# SiteView pure-VTK examples

These scripts show how to use the vendored EAM VTK algorithms
(`e3sm_siteview.io`) directly, without ParaView.

## Data

Set `EAM_DATA_DIR` to the folder holding the sample files (defaults to
`~/Data/EAM`):

- `connectivity_ne30pg2_170e_to_230e_55n_to_85n_TEMPEST.nc` — SCRIP mesh, 298
  columns
- `v2_F20TR_nc00_ndgAllLevs_pd.eam.h1.2008-07-20-00000.nc` — field data

## Run

```console
uv run python examples/01_mesh_reader.py
# or, with the venv active:
python examples/01_mesh_reader.py
```

## Examples

| script                            | shows                                                         |
| --------------------------------- | ------------------------------------------------------------ |
| `01_mesh_reader.py`               | `EAMMeshSource`: connectivity → 2D column mesh (vtkPolyData)  |
| `02_column_reader.py`             | `EAMColumnSource`: data → per-column profiles (vtkTable)      |
| `03_column_volume.py`             | both readers + `EAMColumnVolume` → 3D hexahedral column grid  |
| `04_select_columns_in_radius.py`  | pick columns within a radius on the mesh, then load them      |
| `05_time_series_single_column.py` | iterate time for one column via the Slicing JSON              |
