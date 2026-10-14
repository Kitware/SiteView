"""Synthetic EAM files: a 4x4 SCRIP mesh (170E-210E, 50N-90N) and a data
file with 3 time steps and 4 levels, small enough to build on the fly."""

import netCDF4
import numpy as np
import pytest

N_LON, N_LAT = 4, 4
N_COL = N_LON * N_LAT
N_LEV = 4
N_TIME = 3
LEVELS = [100.0, 400.0, 700.0, 1000.0]
FILL = -999.0


def expected_t(time, lev, col):
    return time * 1000 + lev * 100 + col


def expected_ps(time, col):
    return time * 1000 + col


@pytest.fixture(scope="session")
def connectivity_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("eam") / "connectivity.nc"
    lon0 = 170 + 10 * np.arange(N_LON)
    lat0 = 50 + 10 * np.arange(N_LAT)
    corner_lon, corner_lat = [], []
    for lat in lat0:
        for lon in lon0:
            corner_lon.append([lon, lon + 10, lon + 10, lon])
            corner_lat.append([lat, lat, lat + 10, lat + 10])

    with netCDF4.Dataset(path, "w") as ds:
        ds.createDimension("grid_size", N_COL)
        ds.createDimension("grid_corners", 4)
        for name, values in (
            ("grid_corner_lon", corner_lon),
            ("grid_corner_lat", corner_lat),
        ):
            var = ds.createVariable(name, "f8", ("grid_size", "grid_corners"))
            var[:] = values
    return path


def _write_data_file(path, with_lev_variable=True):
    with netCDF4.Dataset(path, "w") as ds:
        ds.createDimension("time", None)
        ds.createDimension("lev", N_LEV)
        ds.createDimension("ncol", N_COL)

        time = ds.createVariable("time", "f8", ("time",))
        time.units = "days since 2008-07-20 00:00:00"
        time.calendar = "noleap"
        time[:] = 0.25 * np.arange(N_TIME)

        if with_lev_variable:
            ds.createVariable("lev", "f8", ("lev",))[:] = LEVELS
        else:
            # Hybrid coefficients only: lev = (hyam * P0 + hybm * PS0) / 100
            ds.createVariable("hyam", "f8", ("lev",))[:] = np.array(LEVELS) / 1000
            ds.createVariable("hybm", "f8", ("lev",))[:] = np.zeros(N_LEV)

        t, lev, col = np.meshgrid(
            np.arange(N_TIME), np.arange(N_LEV), np.arange(N_COL), indexing="ij"
        )
        # Classic EAM order (time, lev, ncol)
        temp = ds.createVariable("T", "f8", ("time", "lev", "ncol"))
        temp[:] = expected_t(t, lev, col)
        # EAMxx order (time, ncol, lev) with a fill value
        q = ds.createVariable("Q", "f8", ("time", "ncol", "lev"), fill_value=FILL)
        values = np.transpose(expected_t(t, lev, col), (0, 2, 1)).astype(float)
        values[:, 0, 0] = FILL
        q[:] = values
        # Surface field
        ps = ds.createVariable("PS", "f8", ("time", "ncol"))
        ps[:] = expected_ps(
            *np.meshgrid(np.arange(N_TIME), np.arange(N_COL), indexing="ij")
        )


@pytest.fixture(scope="session")
def data_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("eam") / "data.eam.h1.nc"
    _write_data_file(path)
    return path


@pytest.fixture(scope="session")
def hybrid_data_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("eam") / "hybrid.eam.h1.nc"
    _write_data_file(path, with_lev_variable=False)
    return path
