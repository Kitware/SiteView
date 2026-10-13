"""Example 6 -- EAMSurfaceSource: read per-column surface (2D) fields.

Companion of EAMColumnSource for the variables without a vertical axis, e.g.
``(time, ncol)`` fields such as TS or PRECT. For a list of column ids the reader
returns a vtkTable with one row per column and one single-component column per
enabled variable. The time step is chosen through the Slicing JSON.
"""

import json

from common import data_paths
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMSurfaceSource


def main():
    data, _conn = data_paths()

    surface = EAMSurfaceSource()
    surface.SetDataFileName(data)
    surface.SetColumnIds(json.dumps([27, 3, 100]))
    surface.SetSlicing(json.dumps({"time": 5}))

    selection = surface.GetProfileVariables()
    names = [selection.GetArrayName(i) for i in range(selection.GetNumberOfArrays())]
    print(f"surface variables ({len(names)}): {', '.join(names)}")
    for name in names:
        selection.EnableArray(name)
    surface.Update()

    table = surface.GetOutputDataObject(0)
    print(f"rows : {table.GetNumberOfRows()} (one per column)")
    col_ids = numpy_support.vtk_to_numpy(table.GetColumnByName("col_id"))
    for name in names:
        values = numpy_support.vtk_to_numpy(table.GetColumnByName(name))
        print(
            f"  {name:40s} {dict(zip(col_ids.tolist(), values.round(3).tolist(), strict=True))}"
        )


if __name__ == "__main__":
    main()
