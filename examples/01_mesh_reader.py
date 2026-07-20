"""Example 1 -- EAMMeshSource: read the 2D column mesh.

A SCRIP connectivity file becomes a vtkPolyData of quad columns. Cell id equals
column id, a ``col_id`` cell array carries that id explicitly, and coincident
corners are merged into shared points so the mesh has real neighbor topology.
"""

from common import data_paths
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMMeshSource


def main():
    _data, conn = data_paths()

    mesh = EAMMeshSource()
    mesh.SetFileName(conn)
    mesh.Update()

    poly = mesh.GetOutputDataObject(0)
    bounds = poly.GetBounds()
    col_id = numpy_support.vtk_to_numpy(poly.GetCellData().GetArray("col_id"))

    print(f"connectivity : {conn}")
    print(f"columns      : {poly.GetNumberOfCells()} quads")
    print(f"points       : {poly.GetNumberOfPoints()} (shared corners)")
    print(f"lon range    : {bounds[0]:.2f} .. {bounds[1]:.2f}")
    print(f"lat range    : {bounds[2]:.2f} .. {bounds[3]:.2f}")
    print(f"col_id[:5]   : {col_id[:5]}  (cell i == column i)")


if __name__ == "__main__":
    main()
