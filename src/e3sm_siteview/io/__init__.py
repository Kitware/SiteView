"""Vendored EAM VTK algorithms for SiteView (pure VTK).

- ``EAMMeshSource``   : SCRIP connectivity -> 2D column mesh (vtkPolyData)
- ``EAMColumnSource`` : data file -> per-column vertical profiles (vtkTable)
- ``EAMColumnVolume`` : mesh + profiles -> 3D column grid (vtkUnstructuredGrid)

Copied from QuickView; ParaView-only bits are shimmed in ``_sm_compat`` so the
classes run under pure VTK. Configure via ``Set*`` methods and wire with
``SetInputConnection`` / ``Update``.
"""
from .eam_filters import EAMColumnVolume
from .eam_reader import EAMColumnSource, EAMMeshSource

__all__ = ["EAMColumnSource", "EAMColumnVolume", "EAMMeshSource"]
