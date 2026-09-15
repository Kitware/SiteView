from pathlib import Path
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCellArray

from vtkmodules.util import numpy_support, vtkConstants
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
import numpy as np

POINTS_PER_LINE = 100

CONTINENT_PATH = Path(__file__).with_name("continents.vtp").resolve()


class EAMGridLines(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self, nInputPorts=0, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.llat = -90.0
        self.hlat = 90.0
        self.llon = -180.0
        self.hlon = 180.0
        self.interval = 30

    def SetLongRange(self, llon, hlon):
        if self.llon != llon or self.hlon != hlon:
            self.llon = llon
            self.hlon = hlon
            self.Modified()

    def SetLatRange(self, llat, hlat):
        if self.llat != llat or self.hlat != hlat:
            self.llat = llat
            self.hlat = hlat
            self.Modified()

    def SetInterval(self, interval):
        if self.interval != interval:
            self.interval = interval
            self.Modified()

    def RequestInformation(self, request, inInfo, outInfo):
        return super().RequestInformation(request, inInfo, outInfo)

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        return super().RequestUpdateExtent(request, inInfo, outInfo)

    def RequestData(self, request, inInfo, outInfo):
        interval = self.interval
        llon = self.llon
        hlon = self.hlon
        llat = self.llat
        hlat = self.hlat

        import math

        llon = math.floor(llon / interval) * interval
        hlon = math.ceil(hlon / interval) * interval
        xextent = hlon - llon
        llat = math.floor(llat / interval) * interval
        hlat = math.ceil(hlat / interval) * interval
        yextent = hlat - llat

        output = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(outInfo, 0))

        # Getting Longitude lines
        longs = int(xextent / interval) + 1
        lonpoints = POINTS_PER_LINE * longs

        # Getting Latitude lines
        lats = int(yextent / interval) + 1
        latpoints = POINTS_PER_LINE * lats

        shape = (lonpoints + latpoints, 3)
        coords = np.empty(shape, dtype=np.float64)

        # Generate longitude line x-coordinates (longitude values)
        lonx = np.linspace(llon, hlon, longs)
        lonx = np.repeat(lonx, POINTS_PER_LINE)

        # Generate longitude line y-coordinates (latitude values)
        lony = np.linspace(llat, hlat, POINTS_PER_LINE)
        lony = np.tile(lony, longs)  # Repeat for each longitude line

        # Generate latitude line x-coordinates (longitude values)
        latx = np.linspace(llon, hlon, POINTS_PER_LINE)
        latx = np.tile(latx, lats)  # Repeat for each latitude line

        # Generate latitude line y-coordinates (latitude values)
        laty = np.linspace(llat, hlat, lats)
        laty = np.repeat(laty, POINTS_PER_LINE)

        # Verify array sizes before assignment
        assert len(lonx) == lonpoints, f"lonx size {len(lonx)} != expected {lonpoints}"
        assert len(lony) == lonpoints, f"lony size {len(lony)} != expected {lonpoints}"
        assert len(latx) == latpoints, f"latx size {len(latx)} != expected {latpoints}"
        assert len(laty) == latpoints, f"laty size {len(laty)} != expected {latpoints}"

        coords[:lonpoints, 0] = lonx
        coords[:lonpoints, 1] = lony
        coords[:lonpoints, 2] = 1.0
        coords[lonpoints:, 0] = latx
        coords[lonpoints:, 1] = laty
        coords[lonpoints:, 2] = 1.0
        _coords = dsa.numpyTovtkDataArray(coords)

        vtk_coords = vtkPoints()
        vtk_coords.SetData(_coords)
        output.SetPoints(vtk_coords)
        ncells = longs + lats
        cellTypes = np.empty(ncells, dtype=np.uint8)

        # Build cell offsets array
        offsets = np.empty(ncells + 1, dtype=np.int64)

        # Longitude line offsets
        for i in range(longs):
            offsets[i] = i * POINTS_PER_LINE

        # Latitude line offsets
        for i in range(lats):
            offsets[longs + i] = lonpoints + i * POINTS_PER_LINE

        # Final offset
        offsets[-1] = lonpoints + latpoints

        # Build connectivity array for polylines
        cells = np.arange(lonpoints + latpoints, dtype=np.int64)

        cellTypes.fill(vtkConstants.VTK_POLY_LINE)
        cellTypes = numpy_support.numpy_to_vtk(
            num_array=cellTypes.ravel(),
            deep=True,
            array_type=vtkConstants.VTK_UNSIGNED_CHAR,
        )
        offsets = numpy_support.numpy_to_vtk(
            num_array=offsets.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cells = numpy_support.numpy_to_vtk(
            num_array=cells.ravel(), deep=True, array_type=vtkConstants.VTK_ID_TYPE
        )
        cellArray = vtkCellArray()
        cellArray.SetData(offsets, cells)
        output.VTKObject.SetCells(cellTypes, cellArray)
        return 1
