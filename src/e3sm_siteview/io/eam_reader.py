"""EAM column-profile and 2D-mesh VTK sources.

Vendored from QuickView for SiteView (pure VTK, no ParaView). ParaView-only
decorators/prints are supplied by the paraview-optional shim in ``_sm_compat``,
so in a pure-VTK app the classes are configured directly via their ``Set*``
methods and wired with ``SetInputConnection`` / ``Update``.
"""
import json

import netCDF4
import numpy as np
from vtkmodules.util import numpy_support, vtkConstants
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkDataArraySelection, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkTable

from ._perf import perf as _perf
from ._sm_compat import print_error, print_warning, smproperty, smproxy

_has_deps = True


class EAMConstants:
    LEV = "lev"
    HYAM = "hyam"
    HYBM = "hybm"
    ILEV = "ilev"
    HYAI = "hyai"
    HYBI = "hybi"
    P0 = float(1e5)
    PS0 = float(1e5)


class DimMeta:
    """Simple class to store dimension metadata."""

    def __init__(self, name, size, data=None):
        self.name = name
        self.size = size
        self.long_name = None
        self.units = None
        self.data = data  # Store the actual dimension coordinate values

    def __getitem__(self, key):
        """Dict-like access to attributes."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Dict-like setting of attributes."""
        setattr(self, key, value)

    def update_from_variable(self, var_info):
        """Update metadata from netCDF variable info - only long_name and units."""
        try:
            self.long_name = var_info.getncattr("long_name")
        except AttributeError:
            pass

        try:
            self.units = var_info.getncattr("units")
        except AttributeError:
            pass

    def __repr__(self):
        return f"DimMeta(name='{self.name}', size={self.size}, long_name='{self.long_name}')"


class VarMeta:
    """Simple class to store variable metadata."""

    def __init__(self, name, info, horizontal_dim=None):
        self.name = name
        self.dimensions = info.dimensions  # Store dimensions for slicing
        self.fillval = np.nan
        self.long_name = None

        # Extract metadata from info
        self._extract_metadata(info)

    def _extract_metadata(self, info):
        """Helper to extract metadata attributes from netCDF variable."""
        # Try to get fill value from either _FillValue or missing_value
        for fillattr in ["_FillValue", "missing_value"]:
            value = self._get_attr(info, fillattr)
            if value is not None:
                self.fillval = value
                break

        # Get long_name if available
        long_name = self._get_attr(info, "long_name")
        if long_name is not None:
            self.long_name = long_name

    def _get_attr(self, info, attr_name):
        """Safely get an attribute from netCDF variable info."""
        try:
            return info.getncattr(attr_name)
        except (AttributeError, KeyError):
            return None

    def __getitem__(self, key):
        """Dict-like access to attributes."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Dict-like setting of attributes."""
        setattr(self, key, value)

    def __repr__(self):
        return f"VarMeta(name='{self.name}', dimensions={self.dimensions})"


def compare(data, arrays, dim):
    ref = data[arrays[0]][:].flatten()
    if len(ref) != dim:
        raise Exception(
            "Length of hya_/hyb_ variable does not match the corresponding dimension"
        )
    for array in arrays[1:]:
        comp = data[array][:].flatten()
        if not np.array_equal(ref, comp):
            return None
    return ref


def FindSpecialVariable(data, lev, hya, hyb):
    dim = data.dimensions.get(lev, None)
    if dim is None:
        raise Exception(f"{lev} not found in dimensions")
    dim = dim.size
    var = np.array(list(data.variables.keys()))

    if lev in var:
        lev = data[lev][:].flatten()
        return lev

    _hyai = [v for v in var if hya in v]
    _hybi = [v for v in var if hyb in v]
    if len(_hyai) != len(_hybi):
        raise Exception("Unmatched pair of hya and hyb variables found")

    p0 = data["P0"][:].item() if "P0" in var else EAMConstants.P0
    ps0 = EAMConstants.PS0

    if len(_hyai) == 1:
        hyai = data[_hyai[0]][:].flatten()
        hybi = data[_hyai[1]][:].flatten()
        if not (len(hyai) == dim and len(hybi) == dim):
            raise Exception(
                "Lengths of arrays for hya_ and hyb_ variables do not match"
            )
        ldata = ((hyai * p0) + (hybi * ps0)) / 100.0
        return ldata
    else:
        hyai = compare(data, _hyai, dim)
        hybi = compare(data, _hybi, dim)
        if hyai is None or hybi is None:
            raise Exception("Values within hya_ and hyb_ arrays do not match")
        else:
            ldata = ((hyai * p0) + (hybi * ps0)) / 100.0
            return ldata


# ------------------------------------------------------------------------------
# A reader example.
# ------------------------------------------------------------------------------
def createModifiedCallback(anobject):
    import weakref

    weakref_obj = weakref.ref(anobject)
    anobject = None

    def _markmodified(*args, **kwars):
        o = weakref_obj()
        if o is not None:
            o.Modified()

    return _markmodified


@smproxy.source(name="EAMColumnSource", label="EAM Column Profile Reader")
@smproperty.xml(
    """
                <StringVectorProperty command="SetDataFileName"
                      name="FileName1"
                      label="Data File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF data file name.</Documentation>
                </StringVectorProperty>
                """
)
@smproperty.xml(
    """
                <StringVectorProperty command="SetColumnIds"
                      name="ColumnIds"
                      label="Column Ids"
                      number_of_elements="1"
                      animateable="0"
                      default_values="">
                    <Documentation>JSON list of horizontal column (cell) ids to
                    extract full vertical profiles for, e.g. [12, 13, 27].</Documentation>
                </StringVectorProperty>
                """
)
@smproperty.xml(
    """
                <StringVectorProperty command="SetSlicing"
                      name="Slicing"
                      label="Slicing"
                      number_of_elements="1"
                      animateable="0"
                      default_values="">
                    <Documentation>JSON of index slices for non-vertical,
                    non-horizontal dimensions (e.g. {"time": 3}). The vertical
                    dimension (lev/ilev) is always fully expanded.</Documentation>
                </StringVectorProperty>
                """
)
class EAMColumnSource(VTKPythonAlgorithmBase):
    """Extract full vertical profiles for a list of horizontal columns.

    This is the transpose of EAMSliceSource: instead of fixing the vertical
    level and returning every column (a horizontal map), it fixes a set of
    columns and returns every vertical level (a stack of profiles).

    The output is a vtkTable with one row per selected column. Each field
    variable becomes a single multi-component column whose component count is
    that variable's vertical size (``lev`` or ``ilev``), so row j of the
    variable column holds the full vertical profile of column j::

        rows   = selected columns
        col_id : 1 component               (the column id per row)
        <var>  : n_lev | n_ilev comps      (profile per row)

    The shared vertical pressure coordinate is attached as field data (a
    vtkTable column must match the row count, so it cannot live as a column):

        FieldData["lev"]  : 1 tuple x n_lev comps
        FieldData["ilev"] : 1 tuple x n_ilev comps

    Only the data file is needed; no geometry/connectivity is read here.
    """

    def __init__(self):
        super().__init__(nInputPorts=0, nOutputPorts=1, outputType="vtkTable")
        self._DataFileName = None
        self._column_ids = []
        self._slices = {}
        self._variables = {}  # VarMeta by name (vars with a vertical axis)
        self._dimensions = {}  # sliceable non-vertical dims (e.g. time)

        self._variable_selection = vtkDataArraySelection()
        self._variable_selection.AddObserver(
            "ModifiedEvent", createModifiedCallback(self)
        )

        self._var_dataset = None
        self._cached_var_filename = None
        self._horizontal_dim = None

    def __del__(self):
        self._close_dataset()

    # -- dataset caching ------------------------------------------------------
    def _close_dataset(self):
        if self._var_dataset is not None:
            try:
                self._var_dataset.close()
            except Exception:
                pass
            self._var_dataset = None

    def _get_var_dataset(self):
        if self._DataFileName != self._cached_var_filename or self._var_dataset is None:
            if self._var_dataset is not None:
                try:
                    self._var_dataset.close()
                except Exception:
                    pass
            self._var_dataset = netCDF4.Dataset(self._DataFileName, "r")
            self._cached_var_filename = self._DataFileName
        return self._var_dataset

    # -- metadata -------------------------------------------------------------
    @staticmethod
    def _vertical_dim(dimensions):
        """Return the lev/ilev dimension name in ``dimensions``, or None."""
        for d in dimensions:
            if d in (EAMConstants.LEV, EAMConstants.ILEV):
                return d
        return None

    def _detect_horizontal_dim(self, vardata):
        """Detect the horizontal (column) dimension from the data file alone.

        Chosen semantically rather than positionally, because the dimension
        order differs across models: classic EAM writes ``(time, lev, ncol)``
        (ncol innermost) while EAMxx writes ``(time, ncol, lev)`` (lev
        innermost). Among the non-vertical, non-record dimensions of field
        variables, the horizontal axis the ColumnIds index into is the one
        used by the most variables (a file may also carry a second grid such
        as a dynamics ``ncol_d``; the physics grid the bulk of fields live on
        is the intended target). Ties break toward the larger dimension. No
        connectivity file is required.
        """
        counts = {}
        for info in vardata.variables.values():
            dims = info.dimensions
            if self._vertical_dim(dims) is None:
                continue
            for d in dims:
                if d in (EAMConstants.LEV, EAMConstants.ILEV):
                    continue
                dim_obj = vardata.dimensions.get(d)
                if dim_obj is None or dim_obj.isunlimited() or d == "time":
                    continue  # skip the record/time axis
                counts[d] = counts.get(d, 0) + 1
        # Primary horizontal grid = most-used candidate, larger size wins ties.
        self._horizontal_dim = max(
            counts,
            key=lambda d: (counts[d], vardata.dimensions[d].size),
            default=None,
        )

    def _populate_variable_metadata(self):
        if self._DataFileName is None:
            return
        vardata = self._get_var_dataset()
        self._detect_horizontal_dim(vardata)
        if not self._horizontal_dim:
            print_error(
                "EAMColumnSource: could not detect the horizontal (column) dimension"
            )
            return

        self._variable_selection.RemoveAllArrays()
        self._variables.clear()
        self._dimensions.clear()

        for name, info in vardata.variables.items():
            dims = info.dimensions
            # Only variables on the horizontal grid that also have a vertical
            # (lev/ilev) axis can yield a profile.
            if self._horizontal_dim not in dims or self._vertical_dim(dims) is None:
                continue
            self._variables[name] = VarMeta(name, info, self._horizontal_dim)
            self._variable_selection.AddArray(name)

            # Remaining sliceable dims (e.g. time): neither horizontal nor
            # vertical, arity > 1.
            for d in dims:
                if d == self._horizontal_dim or d in (
                    EAMConstants.LEV,
                    EAMConstants.ILEV,
                ):
                    continue
                if d in self._dimensions:
                    continue
                dim_obj = vardata.dimensions.get(d)
                if dim_obj is not None and dim_obj.size > 1:
                    dim_meta = DimMeta(d, dim_obj.size)
                    if d in vardata.variables:
                        try:
                            dim_meta.data = vardata[d][:].data
                        except Exception:
                            pass
                        dim_meta.update_from_variable(vardata.variables[d])
                    self._dimensions[d] = dim_meta

        for d in self._dimensions:
            self._slices.setdefault(d, 0)
        self._variable_selection.DisableAllArrays()

    # -- properties -----------------------------------------------------------
    def SetDataFileName(self, fname):
        if fname is not None and fname != "None" and fname != self._DataFileName:
            self._DataFileName = fname
            self._populate_variable_metadata()
            self.Modified()

    def GetDataFileName(self):
        return self._DataFileName

    def SetColumnIds(self, id_str):
        try:
            ids = json.loads(id_str) if id_str and id_str.strip() else []
        except (json.JSONDecodeError, ValueError) as e:
            print_error(f"EAMColumnSource: invalid ColumnIds JSON: {e}")
            return
        try:
            ids = [int(i) for i in ids]
        except (TypeError, ValueError) as e:
            print_error(f"EAMColumnSource: ColumnIds must be integers: {e}")
            return
        if ids != self._column_ids:
            self._column_ids = ids
            self.Modified()

    def SetSlicing(self, slice_str):
        if not (slice_str and slice_str.strip()):
            return
        try:
            slice_dict = json.loads(slice_str)
        except (json.JSONDecodeError, ValueError) as e:
            print_error(f"EAMColumnSource: invalid Slicing JSON: {e}")
            return
        changed = False
        for dim, val in slice_dict.items():
            if isinstance(val, int) and self._slices.get(dim) != val:
                self._slices[dim] = val
                changed = True
        if changed:
            self.Modified()

    def GetVariables(self):
        return self._variables

    def GetDimensions(self):
        return self._dimensions

    @smproperty.dataarrayselection(name="Variables")
    def GetProfileVariables(self):
        return self._variable_selection

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def _add_column(table, name, np_arr, vtk_type):
        vtk_arr = numpy_support.numpy_to_vtk(
            np.ascontiguousarray(np_arr), deep=True, array_type=vtk_type
        )
        vtk_arr.SetName(name)
        table.AddColumn(vtk_arr)

    @staticmethod
    def _add_field_array(table, name, np_arr):
        # A vtkTable column must match the row count, so the shared vertical
        # coordinate (a single tuple with n_lev|n_ilev components) is attached
        # as field data instead of as a row column.
        vtk_arr = numpy_support.numpy_to_vtk(
            np.ascontiguousarray(np_arr), deep=True, array_type=vtkConstants.VTK_DOUBLE
        )
        vtk_arr.SetName(name)
        table.GetFieldData().AddArray(vtk_arr)

    # -- execution ------------------------------------------------------------
    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("column_reader.RequestData"):
            return self._RequestDataImpl(outInfo)

    def _RequestDataImpl(self, outInfo):
        output = vtkTable.GetData(outInfo, 0)
        output.Initialize()

        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0
        if not self._DataFileName:
            print_error("EAMColumnSource: a data file is required")
            return 0

        vardata = self._get_var_dataset()
        if not self._horizontal_dim:
            self._detect_horizontal_dim(vardata)
        if not self._horizontal_dim:
            print_error(
                "EAMColumnSource: could not detect the horizontal (column) dimension"
            )
            return 0

        # Dedupe while preserving requested order (the table's row order).
        ids = list(dict.fromkeys(self._column_ids))
        enabled = [
            vm
            for vm in self._variables.values()
            if self._variable_selection.ArrayIsEnabled(vm.name)
        ]
        if not ids or not enabled:
            # Valid but empty result (nothing selected yet).
            return 1

        n = len(ids)
        # netCDF advanced indexing wants ascending indices; read sorted, then
        # permute rows back to the requested order.
        order = np.argsort(ids, kind="stable")
        sorted_ids = np.asarray(ids, dtype=np.int64)[order]
        inv = np.empty(n, dtype=np.int64)
        inv[order] = np.arange(n)

        # One row per column; col_id is a single-component column.
        self._add_column(
            output, "col_id", np.asarray(ids, dtype=np.int32), vtkConstants.VTK_INT
        )

        # One multi-component column per variable: n rows x (n_lev|n_ilev) comps.
        for vm in enabled:
            vdim = self._vertical_dim(vm.dimensions)
            n_d = vardata.dimensions[vdim].size

            slice_tuple = []
            for d in vm.dimensions:
                if d == self._horizontal_dim:
                    slice_tuple.append(sorted_ids)
                elif d == vdim:
                    slice_tuple.append(slice(None))
                else:
                    slice_tuple.append(int(self._slices.get(d, 0)))

            with _perf.timed(f"column_reader.netcdf_read.{vm.name}"):
                arr = np.asarray(vardata[vm.name][tuple(slice_tuple)])

            # Orient to (column, level): rows = columns, components = levels,
            # regardless of the file's dimension order.
            remaining = [
                d
                for d, s in zip(vm.dimensions, slice_tuple)
                if not isinstance(s, int)
            ]
            if remaining.index(vdim) < remaining.index(self._horizontal_dim):
                arr = arr.T  # (level, column) -> (column, level)
            arr = arr.reshape(n, n_d)[inv]  # restore requested row order

            if not np.isnan(vm.fillval):
                arr = np.where(arr == vm.fillval, np.nan, arr)

            self._add_column(
                output,
                vm.name,
                np.ascontiguousarray(arr, dtype=np.float64),
                vtkConstants.VTK_DOUBLE,
            )

        # Vertical coordinate arrays (single tuple, n_lev|n_ilev comps), attached
        # as field data. Emit whichever axes exist in the file regardless of which
        # variables are selected, so a downstream volume filter can build geometry
        # from the ilev interfaces even when only lev variables were loaded.
        for axis, hya, hyb in (
            (EAMConstants.LEV, EAMConstants.HYAM, EAMConstants.HYBM),
            (EAMConstants.ILEV, EAMConstants.HYAI, EAMConstants.HYBI),
        ):
            if axis in vardata.dimensions:
                try:
                    coord = np.asarray(
                        FindSpecialVariable(vardata, axis, hya, hyb), dtype=np.float64
                    ).reshape(1, -1)
                except Exception as e:
                    print_error(f"EAMColumnSource: could not read {axis} coordinate: {e}")
                    continue
                self._add_field_array(output, axis, coord)

        return 1


@smproxy.source(name="EAMMeshSource", label="EAM Mesh Reader")
@smproperty.xml(
    """
                <StringVectorProperty command="SetFileName"
                      name="FileName"
                      label="Connectivity File"
                      number_of_elements="1">
                    <FileListDomain name="files" />
                    <Documentation>Specify the NetCDF (SCRIP) connectivity file.
                    </Documentation>
                </StringVectorProperty>
                """
)
class EAMMeshSource(VTKPythonAlgorithmBase):
    """Read the 2D column mesh from a SCRIP connectivity file as vtkPolyData.

    This is the picking surface: the application selects a point on it, maps
    that to a cell, grows a neighborhood, and feeds the resulting column ids to
    EAMColumnSource. Only the connectivity file is read (no data file, no
    variables).

    Each SCRIP cell (``grid_size`` quads defined by ``grid_corner_lat`` /
    ``grid_corner_lon``) becomes one polygon, in file order, so cell id == the
    column id. A ``col_id`` cell-data array carries that id explicitly so it
    survives any downstream filtering/reordering. Coincident corners are merged
    into shared points, giving the mesh real edge/point topology for
    neighbor-based region growing.
    """

    def __init__(self):
        super().__init__(nInputPorts=0, nOutputPorts=1, outputType="vtkPolyData")
        self._FileName = None
        self._cached_output = None
        self._cached_filename = None

    def SetFileName(self, fname):
        if fname is not None and fname != "None" and fname != self._FileName:
            self._FileName = fname
            self.Modified()

    def _build_polydata(self):
        ds = netCDF4.Dataset(self._FileName, "r")
        try:
            mvars = list(ds.variables.keys())
            lat_name = next(v for v in mvars if "corner_lat" in v)
            lon_name = next(v for v in mvars if "corner_lon" in v)
            lat = np.asarray(ds.variables[lat_name][:]).astype(np.float64)
            lon = np.asarray(ds.variables[lon_name][:]).astype(np.float64)
        finally:
            ds.close()

        ncell, ncorner = lat.shape
        lon_flat = lon.reshape(-1)
        lat_flat = lat.reshape(-1)

        # Corner coordinates (lon, lat, 0); SCRIP corners are in degrees.
        coords = np.empty((lon_flat.size, 3), dtype=np.float32)
        coords[:, 0] = lon_flat
        coords[:, 1] = lat_flat
        coords[:, 2] = 0.0

        # Merge coincident corners so adjacent cells share points/edges (needed
        # for topological region growing). Round to absorb float noise; keep the
        # original coordinate of each merged point's first occurrence.
        key = np.round(np.column_stack([lon_flat, lat_flat]), 8)
        _, first_idx, inverse = np.unique(
            key, axis=0, return_index=True, return_inverse=True
        )
        inverse = np.asarray(inverse).reshape(-1)
        points = coords[first_idx]
        conn = inverse.reshape(ncell, ncorner).astype(np.int64)

        poly = vtkPolyData()
        vtk_points = vtkPoints()
        vtk_points.SetData(
            numpy_support.numpy_to_vtk(
                np.ascontiguousarray(points), deep=True, array_type=vtkConstants.VTK_FLOAT
            )
        )
        poly.SetPoints(vtk_points)

        offsets = np.arange(0, ncell * ncorner + 1, ncorner, dtype=np.int64)
        cells = vtkCellArray()
        cells.SetData(
            numpy_support.numpy_to_vtk(
                offsets, deep=True, array_type=vtkConstants.VTK_ID_TYPE
            ),
            numpy_support.numpy_to_vtk(
                np.ascontiguousarray(conn.reshape(-1)),
                deep=True,
                array_type=vtkConstants.VTK_ID_TYPE,
            ),
        )
        poly.SetPolys(cells)

        # Explicit column id per cell (cell id == column id, but carry it so it
        # survives downstream reordering/extraction).
        col_id = numpy_support.numpy_to_vtk(
            np.arange(ncell, dtype=np.int32), deep=True, array_type=vtkConstants.VTK_INT
        )
        col_id.SetName("col_id")
        poly.GetCellData().AddArray(col_id)
        return poly

    def RequestData(self, request, inInfo, outInfo):
        output = vtkPolyData.GetData(outInfo, 0)

        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0
        if not self._FileName or self._FileName == "None":
            print_error("EAMMeshSource: a connectivity file is required")
            return 0

        if self._cached_output is None or self._cached_filename != self._FileName:
            with _perf.timed("mesh_reader.build"):
                self._cached_output = self._build_polydata()
            self._cached_filename = self._FileName

        output.ShallowCopy(self._cached_output)
        return 1
