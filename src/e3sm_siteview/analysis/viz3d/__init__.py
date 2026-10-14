from e3sm_siteview.analysis import register_analysis
from e3sm_siteview.analysis.viz3d.constants import NAME
from e3sm_siteview.analysis.viz3d.view import Viz3D

register_analysis(NAME, Viz3D)

__all__ = ["NAME", "Viz3D"]
