"""EAMColumnVolume filter (3D column grid from mesh + profile table).

Vendored from QuickView for SiteView (pure VTK). See ``_sm_compat`` for the
paraview-optional decorator shim.
"""
import numpy as np
from vtkmodules.util import numpy_support, vtkConstants
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkPolyData,
    vtkTable,
    vtkUnstructuredGrid,
)

from ._perf import perf as _perf
from ._sm_compat import print_error, smdomain, smproperty, smproxy

_has_deps = True


@smproxy.filter(name="EAMColumnVolume", label="EAM Column Volume")
@smproperty.input(name="Profiles", port_index=1)
@smdomain.datatype(dataTypes=["vtkTable"], composite_data_supported=False)
@smproperty.input(name="Mesh", port_index=0)
@smdomain.datatype(dataTypes=["vtkPolyData"], composite_data_supported=False)
@smproperty.xml(
    """
                <IntVectorProperty command="SetLevelRange"
                      name="LevelRange"
                      label="Level Range"
                      number_of_elements="2"
                      default_values="0 2147483647">
                    <Documentation>Inclusive [min, max] range of vertical level
                    (cell) indices to keep. Clamped to the available levels; the
                    default keeps them all.</Documentation>
                </IntVectorProperty>
                """
)
class EAMColumnVolume(VTKPythonAlgorithmBase):
    """Build a 3D hexahedral grid of columns from the 2D mesh + profile table.

    Inputs:
      * port 0 (Mesh):     EAMMeshReader vtkPolyData (2D column quads + col_id)
      * port 1 (Profiles): EAMColumnProfileReader vtkTable (per-column profiles,
                           with lev/ilev pressure coordinate field data)

    Each selected column's quad is extruded through the vertical ilev interfaces
    into a stack of hexahedra (one per lev layer). Point z is the ilev pressure
    (pressure-as-z, matching the EAMProject spherical convention, so this grid
    drops into the same projection path). lev variables map directly to cells;
    ilev variables are averaged between adjacent interfaces. LevelRange extracts
    a contiguous subset of layers.
    """

    LEV = "lev"
    ILEV = "ilev"

    def __init__(self):
        super().__init__(
            nInputPorts=2, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self._lev_range = [0, 2**31 - 1]

    def FillInputPortInformation(self, port, info):
        # Port 0 is the 2D mesh (vtkPolyData); port 1 is the profile table
        # (vtkTable, which is NOT a vtkDataSet, so the default requirement
        # would reject it and the filter would never execute).
        info.Set(
            self.INPUT_REQUIRED_DATA_TYPE(),
            "vtkPolyData" if port == 0 else "vtkTable",
        )
        return 1

    def SetLevelRange(self, vmin, vmax):
        if [vmin, vmax] != self._lev_range:
            self._lev_range = [vmin, vmax]
            self.Modified()

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def _add_cell_array(cell_data, name, np_arr, vtk_type):
        vtk_arr = numpy_support.numpy_to_vtk(
            np.ascontiguousarray(np_arr), deep=True, array_type=vtk_type
        )
        vtk_arr.SetName(name)
        cell_data.AddArray(vtk_arr)

    @classmethod
    def _lev_pressures(cls, table):
        lev = table.GetFieldData().GetAbstractArray(cls.LEV)
        if lev is not None:
            return numpy_support.vtk_to_numpy(lev).reshape(-1).astype(np.float64)
        return None

    @classmethod
    def _interface_pressures(cls, table):
        """Interface (ilev) pressures for the vertical geometry.

        Prefers the ilev field array; if only lev is present, derives interfaces
        by averaging adjacent midpoints and extrapolating the top/bottom.
        """
        fd = table.GetFieldData()
        ilev = fd.GetAbstractArray(cls.ILEV)
        if ilev is not None:
            return numpy_support.vtk_to_numpy(ilev).reshape(-1).astype(np.float64)
        lev = fd.GetAbstractArray(cls.LEV)
        if lev is not None:
            levp = numpy_support.vtk_to_numpy(lev).reshape(-1).astype(np.float64)
            mids = 0.5 * (levp[:-1] + levp[1:])
            top = levp[0] - (mids[0] - levp[0])
            bot = levp[-1] + (levp[-1] - mids[-1])
            return np.concatenate([[top], mids, [bot]])
        return None

    # -- execution ------------------------------------------------------------
    def RequestData(self, request, inInfo, outInfo):
        with _perf.timed("column_volume.RequestData"):
            return self._RequestDataImpl(inInfo, outInfo)

    def _RequestDataImpl(self, inInfo, outInfo):
        mesh = vtkPolyData.GetData(inInfo[0], 0)
        table = vtkTable.GetData(inInfo[1], 0)
        output = vtkUnstructuredGrid.GetData(outInfo, 0)
        output.Initialize()

        global _has_deps
        if not _has_deps:
            print_error("Required Python module 'netCDF4' or 'numpy' missing!")
            return 0
        if mesh is None or table is None:
            print_error("EAMColumnVolume: requires both Mesh and Profiles inputs")
            return 0

        n = table.GetNumberOfRows()
        if n == 0:
            return 1  # nothing selected yet

        colid_col = table.GetColumnByName("col_id")
        if colid_col is None:
            print_error("EAMColumnVolume: Profiles table has no 'col_id' column")
            return 0
        col_ids = numpy_support.vtk_to_numpy(colid_col).reshape(-1)

        # Vertical coordinate: ilev interfaces bound the cells, lev at centers.
        iface_z_all = self._interface_pressures(table)
        if iface_z_all is None:
            print_error("EAMColumnVolume: Profiles table lacks a lev/ilev coordinate")
            return 0
        lev_p = self._lev_pressures(table)
        n_ilev = len(iface_z_all)
        n_lev = len(lev_p) if lev_p is not None else n_ilev - 1

        # Clamp the requested level range to what exists.
        lmin = max(0, int(self._lev_range[0]))
        lmax = min(n_lev - 1, int(self._lev_range[1]))
        if lmax < lmin:
            print_error(
                f"EAMColumnVolume: empty LevelRange after clamp [{lmin}, {lmax}]"
            )
            return 0
        n_layers = lmax - lmin + 1
        n_iface = n_layers + 1
        iface_z = iface_z_all[lmin : lmin + n_iface]

        # Map each column id to its cell in the mesh, then gather the 4 corners.
        mesh_colid = mesh.GetCellData().GetArray("col_id")
        if mesh_colid is not None:
            mc = numpy_support.vtk_to_numpy(mesh_colid).reshape(-1)
            colid_to_cell = {int(c): i for i, c in enumerate(mc)}
        else:
            colid_to_cell = {i: i for i in range(mesh.GetNumberOfCells())}

        corner_lon = np.empty((n, 4), dtype=np.float64)
        corner_lat = np.empty((n, 4), dtype=np.float64)
        for j in range(n):
            cell_id = colid_to_cell.get(int(col_ids[j]))
            if cell_id is None:
                print_error(
                    f"EAMColumnVolume: col_id {int(col_ids[j])} not present in mesh"
                )
                return 0
            pts = mesh.GetCell(cell_id).GetPoints()
            for c in range(4):
                px, py, _ = pts.GetPoint(c)
                corner_lon[j, c] = px
                corner_lat[j, c] = py

        # Points: (column, interface, corner) -> (lon, lat, pressure).
        lonb = np.broadcast_to(corner_lon[:, None, :], (n, n_iface, 4))
        latb = np.broadcast_to(corner_lat[:, None, :], (n, n_iface, 4))
        zb = np.broadcast_to(iface_z[None, :, None], (n, n_iface, 4))
        pts_np = np.stack([lonb, latb, zb], axis=-1).reshape(-1, 3).astype(np.float32)

        vpoints = vtkPoints()
        vpoints.SetData(
            numpy_support.numpy_to_vtk(
                np.ascontiguousarray(pts_np), deep=True, array_type=vtkConstants.VTK_FLOAT
            )
        )
        output.SetPoints(vpoints)

        # Hexahedra: bottom quad at interface l, top quad at interface l+1.
        n_cells = n * n_layers
        j_idx = np.repeat(np.arange(n), n_layers)
        l_idx = np.tile(np.arange(n_layers), n)
        corners = np.arange(4)
        base_b = ((j_idx * n_iface + l_idx) * 4)[:, None] + corners[None, :]
        base_t = ((j_idx * n_iface + (l_idx + 1)) * 4)[:, None] + corners[None, :]
        conn = np.hstack([base_b, base_t]).astype(np.int64)

        offsets = np.arange(0, n_cells * 8 + 1, 8, dtype=np.int64)
        cell_types = np.full(n_cells, vtkConstants.VTK_HEXAHEDRON, dtype=np.uint8)
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
        output.SetCells(
            numpy_support.numpy_to_vtk(
                cell_types, deep=True, array_type=vtkConstants.VTK_UNSIGNED_CHAR
            ),
            cells,
        )

        # Cell data: identity arrays plus the mapped variables.
        cd = output.GetCellData()
        self._add_cell_array(
            cd, "col_id", np.repeat(col_ids.astype(np.int32), n_layers),
            vtkConstants.VTK_INT,
        )
        self._add_cell_array(
            cd, "level", np.tile(np.arange(lmin, lmax + 1, dtype=np.int32), n),
            vtkConstants.VTK_INT,
        )

        for i in range(table.GetNumberOfColumns()):
            name = table.GetColumnName(i)
            if name == "col_id":
                continue
            arr = table.GetColumn(i)
            ncomp = arr.GetNumberOfComponents()
            prof = numpy_support.vtk_to_numpy(arr)
            if prof.ndim == 1:
                prof = prof.reshape(n, ncomp)
            if ncomp == n_lev:
                # lev variable -> cell value directly
                cellvals = prof[:, lmin : lmax + 1]
            elif ncomp == n_ilev:
                # ilev variable -> average the two bounding interfaces
                seg = prof[:, lmin : lmax + 2]
                cellvals = 0.5 * (seg[:, :-1] + seg[:, 1:])
            else:
                continue  # not a lev/ilev profile column
            self._add_cell_array(
                cd, name,
                np.ascontiguousarray(cellvals.reshape(-1), dtype=np.float64),
                vtkConstants.VTK_DOUBLE,
            )

        return 1

