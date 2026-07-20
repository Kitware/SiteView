"""Shared helpers for the SiteView pure-VTK examples.

Set ``EAM_DATA_DIR`` to the directory holding the EAM sample files; it defaults
to ``~/Data/EAM``. All examples use the regional ne30pg2 subset (298 columns).
"""

import os
from pathlib import Path

DATA_FILE = "v2_F20TR_nc00_ndgAllLevs_pd.eam.h1.2008-07-20-00000.nc"
CONN_FILE = "connectivity_ne30pg2_170e_to_230e_55n_to_85n_TEMPEST.nc"


def data_paths():
    """Return ``(data_file, connectivity_file)`` as absolute path strings."""
    root = Path(os.environ.get("EAM_DATA_DIR", Path.home() / "Data" / "EAM"))
    data = root / DATA_FILE
    conn = root / CONN_FILE
    missing = [str(p) for p in (data, conn) if not p.is_file()]
    if missing:
        msg = "Missing EAM data files (set EAM_DATA_DIR):\n  " + "\n  ".join(missing)
        raise SystemExit(msg)
    return str(data), str(conn)


def pick_variable(selection, prefer="T"):
    """Enable and return one lev/ilev variable from a vtkDataArraySelection."""
    names = [selection.GetArrayName(i) for i in range(selection.GetNumberOfArrays())]
    if not names:
        msg = "The column reader exposes no lev/ilev variables."
        raise SystemExit(msg)
    chosen = next((n for n in names if n.split("_", 1)[0] == prefer), names[0])
    selection.DisableAllArrays()
    selection.EnableArray(chosen)
    return chosen
