import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from trame.app import TrameComponent
from trame.dataclasses.colormaps import ColormapConfig
from trame.ui.html import DivLayout
from trame.widgets import colormaps, html
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkFiltersCore import vtkFeatureEdges
from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.components import controls
from e3sm_siteview.io import EAMColumnVolume

NAME = "viz"

CAMERA = vtkCamera()


class Viz3D(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._subscriptions = []

        self.columns = column_reader
        self.colormap_config = ColormapConfig(self.server, preset="Viridis")

        self.volume = EAMColumnVolume()
        self.volume.SetInputConnection(0, self.ctx.mesh_algo.GetOutputPort())
        self.volume.SetInputConnection(1, self.columns.GetOutputPort())
        self.volume.Update()
        self.clean_volume = vtkCleanUnstructuredGrid()
        self.volume >> self.clean_volume

        self.horizontal_slice = EAMColumnVolume()
        self.horizontal_slice.SetInputConnection(0, self.ctx.mesh_algo.GetOutputPort())
        self.horizontal_slice.SetInputConnection(1, self.columns.GetOutputPort())
        self.horizontal_slice.Update()

        self._setup_vtk()
        self._build_ui()
        self.bind_reactivity()

    @property
    def name(self):
        return self._id

    def get_data_array(self):
        if "volume" in self.ctx.setup.active_viz:
            self.volume.Update()
            ds = self.volume.GetOutputDataObject(0)
        else:
            self.horizontal_slice.Update()
            ds = self.horizontal_slice.GetOutputDataObject(0)

        return ds.cell_data[self.ctx.setup.volume.color_by]

    def _setup_vtk(self):
        renderer = vtkRenderer(background=(0.5, 0.5, 0.5), active_camera=CAMERA)
        renderWindow = vtkRenderWindow()
        renderWindow.AddRenderer(renderer)
        renderWindow.OffScreenRenderingOn()

        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.render_window = renderWindow
        self.renderer = renderer

        # Volume
        self.volume_mapper = vtkDataSetMapper()
        self.volume_mapper.ScalarVisibilityOn()
        self.volume_mapper.SetColorModeToMapScalars()
        self.volume_mapper.SetScalarModeToUseCellFieldData()
        self.volume_actor = vtkActor(
            mapper=self.volume_mapper, force_opaque=1, scale=(1, 1, 0.1)
        )
        self.renderer.AddActor(self.volume_actor)
        self.clean_volume >> self.volume_mapper
        self.colormap_config.register_mapper(self.volume_mapper)

        # Volume outline
        self.outline_mapper = vtkDataSetMapper()
        self.outline_mapper.ScalarVisibilityOff()
        self.outline_actor = vtkActor(
            mapper=self.outline_mapper, force_opaque=1, scale=(1, 1, 0.1)
        )
        self.renderer.AddActor(self.outline_actor)
        (
            self.clean_volume
            >> vtkGeometryFilter()
            >> vtkFeatureEdges()
            >> self.outline_mapper
        )

        # HSlice
        self.slice_h_mapper = vtkDataSetMapper()
        self.slice_h_mapper.ScalarVisibilityOn()
        self.slice_h_mapper.SetColorModeToMapScalars()
        self.slice_h_mapper.SetScalarModeToUseCellFieldData()
        self.slice_h_actor = vtkActor(
            mapper=self.slice_h_mapper, force_opaque=1, scale=(1, 1, 0.1)
        )
        self.slice_h_actor.property.edge_visibility = 1
        self.renderer.AddActor(self.slice_h_actor)
        self.horizontal_slice >> vtkCleanUnstructuredGrid() >> self.slice_h_mapper
        self.colormap_config.register_mapper(self.slice_h_mapper)

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.volume, ["color_by"], self._on_volume_color_by_change
        )
        self._subscribe(
            self.ctx.setup.column, ["altitude_range"], self._on_column_height_change
        )
        self._subscribe(
            self.ctx.setup.slice, ["altitude"], self._on_column_slice_change, eager=True
        )
        self._subscribe(
            self.ctx.setup, ["active_viz"], self._on_visibility_change, eager=True
        )
        self.ctrl.update_color_range.add(self.colormap_config.update_color_range)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _on_visibility_change(self, active_viz):
        has_volume = "volume" in active_viz
        has_slice = "slice" in active_viz

        self.slice_h_actor.visibility = 0
        self.outline_actor.visibility = 0
        self.volume_actor.visibility = 0

        if has_volume:
            self.volume_actor.visibility = 1
            self.outline_actor.visibility = 0
        if has_slice:
            self.slice_h_actor.visibility = 1
            self.outline_actor.visibility = has_volume
            self.volume_actor.visibility = 0

        self.ctrl.update_color_range.enable_empty()()
        self.html_view.reset_camera()

    def _on_volume_color_by_change(self, color_by):
        if color_by:
            self.colormap_config.set_data_array(color_by, self.get_data_array, "cell")
        self.html_view.update()

    def _on_column_height_change(self, altitude_range):
        self.volume.SetLevelRange(*altitude_range)

        self.ctx.setup.slice.altitude = max(
            self.ctx.setup.slice.altitude, altitude_range[0]
        )
        self.ctx.setup.slice.altitude = min(
            self.ctx.setup.slice.altitude, altitude_range[1]
        )

        self.html_view.reset_camera()

    def _on_column_slice_change(self, level):
        self.horizontal_slice.SetLevelRange(level, level)
        self.ctrl.update_color_range.enable_empty()()
        self.html_view.reset_camera()

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with html.Div(
                style="position:absolute;top:0;left:0;width:100%;height:100%;"
            ):
                self.html_view = vtkw.VtkRemoteView(
                    self.render_window,
                    interactive_ratio=1,
                )
                self.ctrl.render.add(self.html_view.update)
                self.ctrl.reset_camera.add(self.html_view.reset_camera)

                with controls.TopRightFloatControls():
                    v3.VBtn(
                        icon="mdi-crop-free",
                        classes="rounded",
                        density="comfortable",
                        variant="plain",
                        click=self.html_view.reset_camera,
                    )

                with controls.Controls(), controls.TopLeftFloatControls():
                    controls.Cloud()
                    controls.Surface()
                    controls.Volume()
                    controls.HorizontalSlice()
                    # controls.VerticalSlice()
                    controls.FindData()
                    controls.CropColumn()

                with controls.BottomCenterFloatControls():
                    with self.colormap_config.provide_as("colormap"):
                        colormaps.HorizontalScalarBar("colormap", popup_location="top")


register_analysis(NAME, Viz3D)
