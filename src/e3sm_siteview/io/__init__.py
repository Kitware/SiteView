"""Vendored EAM VTK algorithms for SiteView (pure VTK).

- ``EAMMeshSource``   : SCRIP connectivity -> 2D column mesh (vtkPolyData)
- ``EAMColumnSource`` : data file -> per-column vertical profiles (vtkTable)
- ``EAMSurfaceSource``: data file -> per-column surface (2D) values (vtkTable)
- ``EAMColumnVolume`` : mesh + profiles -> 3D column grid (vtkUnstructuredGrid)
- ``EAMColumnSurface``: mesh + surface values -> 2D column footprint (vtkUnstructuredGrid)

Copied from QuickView; ParaView-only bits are shimmed in ``_sm_compat`` so the
classes run under pure VTK. Configure via ``Set*`` methods and wire with
``SetInputConnection`` / ``Update``.
"""
from .eam_filters import EAMColumnMarkers, EAMColumnSurface, EAMColumnVolume, EAMLevelCylinder
from .eam_reader import EAMColumnSource, EAMMeshSource, EAMSurfaceSource
from .projection import EAMProject, EARTH_RADIUS
from .earth import CONTINENT_PATH, EARTH_TEXTURE_PATH, EAMGridLines

__all__ = ["EAMColumnMarkers", "EAMColumnSource", "EAMColumnSurface", "EAMColumnVolume", "EAMLevelCylinder", "EAMMeshSource", "EAMSurfaceSource", "EAMProject", "CONTINENT_PATH", "EARTH_TEXTURE_PATH", "EAMGridLines", "EARTH_RADIUS"]
