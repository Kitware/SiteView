import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html
from trame.widgets import vtk as vtk_widgets

# VTK factory initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis

NAME = "viz"


class Viz3D(TrameComponent):
    def __init__(self, server, reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._reader = reader
        self._setup_vtk(reader)
        self._build_ui()

    @property
    def name(self):
        return self._id

    def _setup_vtk(self, reader):
        mapper = vtkDataSetMapper()
        actor = vtkActor(mapper=mapper)
        reader >> mapper

        renderer = vtkRenderer()
        render_window = vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.OffScreenRenderingOn()

        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(render_window)
        renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        renderer.AddActor(actor)
        renderer.ResetCamera()

        self.actor = actor
        self.mapper = mapper
        self.renderer = renderer
        self.render_window = render_window

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with html.Div(
                style="position:absolute;top:0;left:0;width:100%;height:100%;"
            ):
                self.view = vtk_widgets.VtkRemoteView(
                    self.render_window,
                    interactive_ratio=1,
                )


register_analysis(NAME, Viz3D)
