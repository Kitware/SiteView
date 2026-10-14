import pytest

from e3sm_siteview.viewer import compute_data_regions


def _x_percent(lon):
    # Same mapping as the site selection map (script.js): lon 0 at the center
    return ((lon + 180) % 360) / 360 * 100


def test_global_mesh_has_no_highlight():
    assert compute_data_regions(0, 360, -90, 90) == []


def test_eastern_hemisphere_region():
    ((left, top, width, height),) = compute_data_regions(0, 40, 30, 60)
    assert left == pytest.approx(_x_percent(0))
    assert width == pytest.approx(40 / 360 * 100)
    assert top == pytest.approx((90 - 60) / 180 * 100)
    assert height == pytest.approx(30 / 180 * 100)


def test_western_hemisphere_region():
    ((left, _, width, _),) = compute_data_regions(250, 290, 30, 60)
    assert left == pytest.approx(_x_percent(250))
    assert width == pytest.approx(40 / 360 * 100)


def test_region_crossing_the_antimeridian_is_split():
    # Regional ne30pg2 sample: 170E to 230E
    left_part, right_part = compute_data_regions(170, 230, 55, 85)
    assert left_part[0] == pytest.approx(0)
    assert left_part[2] == pytest.approx(50 / 360 * 100)
    assert right_part[0] == pytest.approx(_x_percent(170))
    assert right_part[0] + right_part[2] == pytest.approx(100)
