"""Example 4 -- pick columns within a radius, then load them.

The EAMMeshSource polydata is the selection surface: build a point locator on
the column centers, find every column whose center lies within a radius of a
target (lon, lat), and feed those column ids to EAMColumnSource.

The radius is in degrees on the flat lon/lat mesh (not geodesic) -- fine for a
small region; project to a cartesian mesh for global correctness.
"""

import json

from common import data_paths, pick_variable
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkStaticPointLocator
from vtkmodules.vtkFiltersCore import vtkCellCenters

from e3sm_siteview.io import EAMColumnSource, EAMMeshSource


def columns_within_radius(poly, center, radius):
    """Return the col_ids whose cell centers fall within radius of center."""
    centers = vtkCellCenters()
    centers.SetInputData(poly)
    centers.Update()

    locator = vtkStaticPointLocator()
    locator.SetDataSet(centers.GetOutput())
    locator.BuildLocator()

    found = vtkIdList()
    locator.FindPointsWithinRadius(radius, center, found)

    col_id = numpy_support.vtk_to_numpy(poly.GetCellData().GetArray("col_id"))
    return sorted(int(col_id[found.GetId(i)]) for i in range(found.GetNumberOfIds()))


def main():
    data, conn = data_paths()

    mesh = EAMMeshSource()
    mesh.SetFileName(conn)
    mesh.Update()
    poly = mesh.GetOutputDataObject(0)

    center = (200.0, 70.0, 0.0)  # lon, lat inside the 170-230E / 55-85N region
    radius = 5.0  # degrees
    ids = columns_within_radius(poly, center, radius)
    print(f"center {center[:2]}  radius {radius} deg  ->  {len(ids)} columns")
    print(f"col_ids: {ids}")
    if not ids:
        return

    col = EAMColumnSource()
    col.SetDataFileName(data)
    col.SetColumnIds(json.dumps(ids))
    col.SetSlicing(json.dumps({"time": 0}))
    var = pick_variable(col.GetProfileVariables())
    col.Update()

    table = col.GetOutputDataObject(0)
    n_lev = table.GetColumnByName(var).GetNumberOfComponents()
    print(
        f"loaded profiles: {table.GetNumberOfRows()} columns x {n_lev} levels of {var}"
    )


if __name__ == "__main__":
    main()
