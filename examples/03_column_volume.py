"""Example 3 -- both readers + EAMColumnVolume: build a 3D column grid.

The mesh (EAMMeshSource) and the profile table (EAMColumnSource) feed the
two-input EAMColumnVolume filter, which extrudes each column's quad through the
ilev interfaces into a stack of hexahedra. Point z is the ilev pressure; lev
variables become cell data directly and ilev variables are averaged between
interfaces. LevelRange carves out a vertical subset with no re-read.
"""

import json

from common import data_paths, pick_variable
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMColumnSource, EAMColumnVolume, EAMMeshSource


def main():
    data, conn = data_paths()

    mesh = EAMMeshSource()
    mesh.SetFileName(conn)

    col = EAMColumnSource()
    col.SetDataFileName(data)
    col.SetColumnIds(json.dumps([27, 3, 100]))
    col.SetSlicing(json.dumps({"time": 5}))
    var = pick_variable(col.GetProfileVariables())

    vol = EAMColumnVolume()
    vol.SetInputConnection(0, mesh.GetOutputPort())
    vol.SetInputConnection(1, col.GetOutputPort())
    vol.Update()

    ug = vol.GetOutputDataObject(0)
    cell_arrays = [
        ug.GetCellData().GetArrayName(i)
        for i in range(ug.GetCellData().GetNumberOfArrays())
    ]
    zvals = numpy_support.vtk_to_numpy(ug.GetPoints().GetData())[:, 2]
    print(f"variable        : {var}")
    print(
        f"full grid       : {ug.GetNumberOfCells()} hexahedra, {ug.GetNumberOfPoints()} points"
    )
    print(f"z (pressure)    : {zvals.min():.2f} .. {zvals.max():.2f} hPa")
    print(f"cell arrays     : {cell_arrays}")

    vol.SetLevelRange(10, 20)
    vol.Update()
    print(f"LevelRange 10-20: {vol.GetOutputDataObject(0).GetNumberOfCells()} cells")


if __name__ == "__main__":
    main()
