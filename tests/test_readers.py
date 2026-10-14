import json

import numpy as np
import pytest
from conftest import FILL, LEVELS, N_COL, N_LEV, N_TIME, expected_ps, expected_t
from vtkmodules.util import numpy_support

from e3sm_siteview.io import EAMColumnSource, EAMMeshSource, EAMSurfaceSource


def _column(table, name):
    return numpy_support.vtk_to_numpy(table.GetColumnByName(name))


def _reader(cls, path, arrays, col_ids, time=0):
    reader = cls()
    reader.SetDataFileName(str(path))
    selection = reader.GetProfileVariables()
    for name in arrays:
        selection.EnableArray(name)
    reader.SetColumnIds(json.dumps(col_ids))
    reader.SetSlicing(json.dumps({"time": time}))
    reader.Update()
    return reader, reader.GetOutputDataObject(0)


def test_mesh_reader(connectivity_file):
    reader = EAMMeshSource()
    reader.SetFileName(str(connectivity_file))
    reader.Update()
    mesh = reader.GetOutputDataObject(0)

    assert mesh.GetNumberOfCells() == N_COL
    # Shared corners are merged: (4 + 1) x (4 + 1) grid points
    assert mesh.GetNumberOfPoints() == 25
    col_id = numpy_support.vtk_to_numpy(mesh.GetCellData().GetArray("col_id"))
    np.testing.assert_array_equal(col_id, np.arange(N_COL))
    assert mesh.GetBounds()[:4] == (170, 210, 50, 90)


def test_column_reader_metadata(data_file):
    reader = EAMColumnSource()
    reader.SetDataFileName(str(data_file))
    selection = reader.GetProfileVariables()
    names = {selection.GetArrayName(i) for i in range(selection.GetNumberOfArrays())}
    # Only fields with a vertical axis
    assert names == {"T", "Q"}
    tdim = reader.GetDimensions()["time"]
    assert tdim.size == N_TIME
    assert tdim.calendar == "noleap"


@pytest.mark.parametrize("time", [0, 2])
def test_column_reader_values(data_file, time):
    col_ids = [7, 2, 11]
    _, table = _reader(EAMColumnSource, data_file, ["T", "Q"], col_ids, time)

    assert table.GetNumberOfRows() == len(col_ids)
    # Rows keep the requested order
    np.testing.assert_array_equal(_column(table, "col_id"), col_ids)
    lev = np.arange(N_LEV)
    expected = np.array([expected_t(time, lev, c) for c in col_ids])
    # (time, lev, ncol) and (time, ncol, lev) both end up as (column, level)
    np.testing.assert_array_equal(_column(table, "T"), expected)
    np.testing.assert_array_equal(_column(table, "Q"), expected)
    np.testing.assert_array_equal(
        numpy_support.vtk_to_numpy(table.GetFieldData().GetArray("lev")).ravel(),
        LEVELS,
    )


def test_column_reader_fill_value_is_nan(data_file):
    _, table = _reader(EAMColumnSource, data_file, ["Q"], [0, 1])
    q = _column(table, "Q")
    assert np.isnan(q[0, 0])
    assert not np.isnan(q[0, 1:]).any()
    assert FILL not in q


def test_column_reader_empty_selection(data_file):
    _, table = _reader(EAMColumnSource, data_file, [], [0, 1])
    assert table.GetNumberOfColumns() == 0
    _, table = _reader(EAMColumnSource, data_file, ["T"], [])
    assert table.GetNumberOfColumns() == 0


def test_column_reader_hybrid_levels(hybrid_data_file):
    # No lev variable: levels are derived from the hybrid coefficients
    _, table = _reader(EAMColumnSource, hybrid_data_file, ["T"], [0])
    lev = numpy_support.vtk_to_numpy(table.GetFieldData().GetArray("lev")).ravel()
    np.testing.assert_allclose(lev, LEVELS)


def test_surface_reader(data_file):
    reader = EAMSurfaceSource()
    reader.SetDataFileName(str(data_file))
    selection = reader.GetProfileVariables()
    names = {selection.GetArrayName(i) for i in range(selection.GetNumberOfArrays())}
    assert names == {"PS"}

    col_ids = [3, 9]
    _, table = _reader(EAMSurfaceSource, data_file, ["PS"], col_ids, time=1)
    np.testing.assert_array_equal(
        _column(table, "PS").ravel(), [expected_ps(1, c) for c in col_ids]
    )
