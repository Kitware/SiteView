"""Example 2 -- EAMColumnSource: read per-column vertical profiles.

For a list of column ids the reader returns a vtkTable with one row per column.
Each variable is a multi-component column (components = lev/ilev size) holding
that column's profile, and the lev/ilev pressure coordinate is attached as
field data. The time step is chosen through the Slicing JSON.
"""

import json

from common import data_paths, pick_variable
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMColumnSource


def main():
    data, _conn = data_paths()

    col = EAMColumnSource()
    col.SetDataFileName(data)
    col.SetColumnIds(json.dumps([27, 3, 100]))
    col.SetSlicing(json.dumps({"time": 5}))
    var = pick_variable(col.GetProfileVariables())
    col.Update()

    table = col.GetOutputDataObject(0)
    print(f"variable : {var}")
    print(f"rows     : {table.GetNumberOfRows()} (one per column)")
    for i in range(table.GetNumberOfColumns()):
        arr = table.GetColumn(i)
        print(
            f"  column {arr.GetName():40s} "
            f"tuples={arr.GetNumberOfTuples()} comps={arr.GetNumberOfComponents()}"
        )
    field = table.GetFieldData()
    for name in ("lev", "ilev"):
        arr = field.GetAbstractArray(name)
        if arr is not None:
            print(
                f"  field  {name:40s} comps={arr.GetNumberOfComponents()} (pressure hPa)"
            )

    profile = numpy_support.vtk_to_numpy(table.GetColumnByName(var))
    print(f"{var} first-column profile (top 5 levels): {profile[0, :5].round(2)}")


if __name__ == "__main__":
    main()
