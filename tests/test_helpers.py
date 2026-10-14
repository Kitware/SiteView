from types import SimpleNamespace

import numpy as np
import pytest

from e3sm_siteview.analysis.viz3d.histogram import snap_bound
from e3sm_siteview.data_models import format_lat_lon, normalize_lon, time_dates


@pytest.mark.parametrize(
    ("lon", "expected"),
    [(0, 0), (179, 179), (180, -180), (190, -170), (360, 0), (-190, 170)],
)
def test_normalize_lon(lon, expected):
    assert normalize_lon(lon) == pytest.approx(expected)


def test_format_lat_lon():
    assert format_lat_lon(200, 36.6) == "36.60°N, 160.00°W"
    assert format_lat_lon(10.5, -5) == "5.00°S, 10.50°E"


def _tdim(data, units, calendar=None):
    return SimpleNamespace(data=np.asarray(data), units=units, calendar=calendar)


def test_time_dates():
    tdim = _tdim([0, 0.5, 1], "days since 2008-07-20 00:00:00", "noleap")
    assert time_dates(tdim) == [
        "2008-07-20 00:00",
        "2008-07-20 12:00",
        "2008-07-21 00:00",
    ]


@pytest.mark.parametrize(
    "tdim",
    [
        None,
        _tdim([0, 1], None),
        _tdim([0, 1], "not a time unit"),
        SimpleNamespace(data=None, units="days since 2000-01-01", calendar=None),
    ],
)
def test_time_dates_not_decodable(tdim):
    assert time_dates(tdim) is None


def testsnap_bound():
    values = np.array([0, 0, 0, 0, 1, 2, 3, 4], dtype=float)
    mask = values > 0
    # 0/100 keep the data bound
    assert snap_bound(values, mask, 0, -1.0) == -1.0
    assert snap_bound(values, mask, 100, 9.0) == 9.0
    # Percentile computed without the dominant extreme value
    assert snap_bound(values, mask, 50, 0.0) == pytest.approx(2.5)
    # Nothing left after masking
    assert snap_bound(values, np.zeros_like(mask), 50, 0.0) == 0.0
