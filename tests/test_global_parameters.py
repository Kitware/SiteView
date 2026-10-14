import json

import pytest
from conftest import N_TIME
from trame.app import get_server

from e3sm_siteview.data_models import GlobalParameters
from e3sm_siteview.io import EAMColumnSource, EAMMeshSource, EAMSurfaceSource


@pytest.fixture
def setup(request, connectivity_file, data_file):
    server = get_server(request.node.name, client_type="vue3")
    server.controller.update_color_range = lambda: None
    server.controller.render = lambda: None

    mesh = EAMMeshSource()
    mesh.SetFileName(str(connectivity_file))
    mesh.Update()
    server.context.mesh = mesh.GetOutputDataObject(0)

    params = GlobalParameters(server)
    columns = EAMColumnSource()
    columns.SetDataFileName(str(data_file))
    params.register_data_reader(columns)
    surface = EAMSurfaceSource()
    surface.SetDataFileName(str(data_file))
    params.register_surface_reader(surface)
    return params


def test_register_readers(setup):
    assert [v.name for v in setup.variables_3d] == ["T", "Q"]
    assert [v.name for v in setup.variables_2d] == ["PS"]
    assert setup.time_values == list(range(N_TIME))
    assert setup.time_labels == [
        "2008-07-20 00:00",
        "2008-07-20 06:00",
        "2008-07-20 12:00",
    ]


def test_apply_region(setup):
    # Cell centers are at 175E + 10 * i, 55N + 10 * j and col_id = 4 * j + i
    setup.apply_region(7.5, (185, 65, 0))
    col_ids = json.loads(setup.col_ids_str)
    # Neighbors are 10 degrees away
    assert col_ids == [5]
    setup.apply_region(10.5, (185, 65, 0))
    col_ids = json.loads(setup.col_ids_str)
    # Closest column first
    assert col_ids[0] == 5
    assert sorted(col_ids) == [1, 4, 5, 6, 9]
    assert setup.n_cols == 5
    assert setup.col_items[0] == {"title": "65.00°N, 175.00°W", "value": 5}


def test_apply_region_across_antimeridian(setup):
    # 195E expressed as -165 still finds the column
    setup.apply_region(0.1, (-165, 55, 0))
    assert json.loads(setup.col_ids_str) == [2]


def test_load_fields_color_by(setup):
    t, q = setup.variables_3d
    (ps,) = setup.variables_2d
    q.selected = True
    ps.selected = True
    setup.load_fields()
    assert setup.volume.color_by == "Q"
    assert setup.surface.color_by == "PS"

    columns = next(iter(setup.readers))
    selection = columns.GetProfileVariables()
    assert selection.ArrayIsEnabled("Q")
    assert not selection.ArrayIsEnabled("T")

    # color_by keeps a still loaded field
    t.selected = True
    setup.load_fields()
    assert setup.volume.color_by == "Q"


def test_load_fields_without_selection(setup):
    setup.load_fields()
    assert setup.volume.color_by == ""
    assert setup.surface.color_by == ""


def test_time_values_update(setup):
    setup.time_index = 2
    setup.time_values = [0, 1]
    assert setup.time_index_max == 1
    assert setup.time_index == 1
    assert setup.time_value == 1
    setup.time_values = []
    assert setup.time_index_max == 0
    assert setup.time_value == 0
