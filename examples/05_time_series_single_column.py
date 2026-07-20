"""Example 5 -- iterate over time, loading one column each step.

The column stays fixed while the Slicing time index advances, assembling a
(time, level) array for a single column. Time is a sliced dimension (Slicing
JSON), so there is no VTK time pipeline to drive -- just re-set and re-update.
"""

import json

import numpy as np
from common import data_paths, pick_variable
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMColumnSource


def main():
    data, _conn = data_paths()
    column_id = 100

    col = EAMColumnSource()
    col.SetDataFileName(data)
    col.SetColumnIds(json.dumps([column_id]))
    var = pick_variable(col.GetProfileVariables())

    tdim = col.GetDimensions().get("time")
    n_time = tdim.size if tdim is not None else 1

    series = []
    for t in range(n_time):
        col.SetSlicing(json.dumps({"time": t}))
        col.Update()
        table = col.GetOutputDataObject(0)
        profile = numpy_support.vtk_to_numpy(table.GetColumnByName(var))[0]  # (n_lev,)
        series.append(profile)

    series = np.array(series)  # (time, level)
    print(f"variable   : {var}")
    print(f"column id  : {column_id}")
    print(f"time steps : {n_time}")
    print(f"series shape (time, level): {series.shape}")
    surface = series[:, -1]  # bottom level over time
    print(f"surface-level range over time: {surface.min():.2f} .. {surface.max():.2f}")


if __name__ == "__main__":
    main()
