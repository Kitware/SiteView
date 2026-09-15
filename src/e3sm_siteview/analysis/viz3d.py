import math

import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from trame.app import TrameComponent
from trame.dataclasses.colormaps import ColormapConfig
from trame.ui.html import DivLayout
from trame.widgets import colormaps, html
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkPlane
from vtkmodules.vtkFiltersCore import (
    vtk3DLinearGridCrinkleExtractor,
    vtkFeatureEdges,
    vtkPolyDataToUnstructuredGrid,
    vtkThreshold,
)
from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
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
from e3sm_siteview.io import (
    CONTINENT_PATH,
    EARTH_RADIUS,
    EAMColumnVolume,
    EAMGridLines,
    EAMProject,
)

NAME = "viz"

CAMERA = vtkCamera()


class Viz3D(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self.html_view = None
        self._projections = []
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
        if (
            "hslice" in self.ctx.setup.active_viz
            and "vslice" in self.ctx.setup.active_viz
        ):
            self.volume.Update()
            ds = self.volume.GetOutputDataObject(0)
        elif "hslice" in self.ctx.setup.active_viz:
            self.horizontal_slice.Update()
            ds = self.horizontal_slice.GetOutputDataObject(0)
        elif "vslice" in self.ctx.setup.active_viz:
            self.slice_v_cutter.Update()
            ds = self.slice_v_cutter.GetOutputDataObject(0)
        else:
            self.volume.Update()
            ds = self.volume.GetOutputDataObject(0)

        return ds.cell_data[self.ctx.setup.volume.color_by]

    def _proj(self):
        proj = EAMProject()
        proj.SetProjection(3)  # spherical
        self._projections.append(proj)
        return proj

    def _reset_camera(self):
        x_rad = math.radians(self.ctx.setup.center[0])
        y_rad = math.radians(self.ctx.setup.center[1])
        cos_y_rad = math.cos(y_rad)
        xs = EARTH_RADIUS * math.sin(x_rad) * cos_y_rad
        ys = EARTH_RADIUS * math.sin(y_rad)
        zs = EARTH_RADIUS * math.cos(x_rad) * cos_y_rad
        self.renderer.active_camera.focal_point = (xs, ys, zs)
        self.renderer.active_camera.position = (xs * 1000, ys * 1000, zs * 1000)
        self.renderer.active_camera.view_up = (0, 0, 1)
        self.renderer.ResetCamera(self.outline_actor.bounds)

        if self.html_view:
            self.html_view.update()

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
            mapper=self.volume_mapper,
            force_opaque=1,
        )
        self.renderer.AddActor(self.volume_actor)
        self.clean_volume >> self._proj() >> self.volume_mapper
        self.colormap_config.register_mapper(self.volume_mapper)

        # Volume outline
        self.outline_mapper = vtkDataSetMapper()
        self.outline_mapper.ScalarVisibilityOff()
        self.outline_actor = vtkActor(
            mapper=self.outline_mapper,
            force_opaque=1,
        )
        self.renderer.AddActor(self.outline_actor)
        (
            self.clean_volume
            >> self._proj()
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
            mapper=self.slice_h_mapper,
            force_opaque=1,
        )
        self.slice_h_actor.property.edge_visibility = 1
        self.renderer.AddActor(self.slice_h_actor)
        (
            self.horizontal_slice
            >> vtkCleanUnstructuredGrid()
            >> self._proj()
            >> self.slice_h_mapper
        )
        self.colormap_config.register_mapper(self.slice_h_mapper)

        # VSlice
        self.slice_v_plane = vtkPlane(normal=(1, 0, 0))
        # self.slice_v_cutter = vtkCutter(cut_function=self.slice_v_plane)
        self.slice_v_cutter = vtk3DLinearGridCrinkleExtractor(
            implicit_function=self.slice_v_plane
        )
        self.slice_v_cutter.CopyCellDataOn()
        self.slice_v_mapper = vtkDataSetMapper()
        self.slice_v_mapper.ScalarVisibilityOn()
        self.slice_v_mapper.SetColorModeToMapScalars()
        self.slice_v_mapper.SetScalarModeToUseCellFieldData()
        self.slice_v_actor = vtkActor(
            mapper=self.slice_v_mapper,
            force_opaque=1,
        )
        self.slice_v_actor.property.edge_visibility = 1
        self.renderer.AddActor(self.slice_v_actor)
        (
            self.clean_volume
            >> self.slice_v_cutter
            >> vtkCleanUnstructuredGrid()
            >> self._proj()
            >> self.slice_v_mapper
        )
        self.colormap_config.register_mapper(self.slice_v_mapper)

        # Volume
        self.threshold = vtkThreshold()
        self.threshold_mapper = vtkDataSetMapper()
        self.threshold_actor = vtkActor(
            mapper=self.threshold_mapper,
            visibility=0,
        )
        self.renderer.AddActor(self.threshold_actor)
        (
            self.volume
            >> self._proj()
            >> self.threshold
            >> vtkCleanUnstructuredGrid()
            >> self.threshold_mapper
        )

        # Continents
        reader = vtkXMLPolyDataReader(file_name=str(CONTINENT_PATH))
        mapper = vtkDataSetMapper()
        self.earth_actor = vtkActor(mapper=mapper)
        reader >> vtkPolyDataToUnstructuredGrid() >> self._proj() >> mapper
        self.renderer.AddActor(self.earth_actor)
        mapper.Update()

        self.earth_actor.property.render_lines_as_tubes = 1
        self.earth_actor.property.line_width = 1.0
        self.earth_actor.property.ambient_color = (0, 0, 0)
        self.earth_actor.property.diffuse_color = (0, 0, 0)

        # Earth sphere
        sphere = vtkSphereSource(
            radius=EARTH_RADIUS - 10000, theta_resolution=180, phi_resolution=360
        )
        sphere_mapper = vtkDataSetMapper()
        sphere_actor = vtkActor(mapper=sphere_mapper)
        sphere_actor.property.ambient_color = (0.67, 0.67, 0.67)
        sphere_actor.property.diffuse_color = (0.67, 0.67, 0.67)
        sphere >> sphere_mapper
        self.renderer.AddActor(sphere_actor)

        # Earth grid
        self.grid = EAMGridLines()
        self.grid.SetInterval(10)
        grid_mapper = vtkDataSetMapper()
        grid_actor = vtkActor(mapper=grid_mapper)
        grid_actor.property.ambient_color = (0, 0, 0)
        grid_actor.property.diffuse_color = (0, 0, 0)
        self.grid >> self._proj() >> grid_mapper
        self.renderer.AddActor(grid_actor)

        self._reset_camera()

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
            self.ctx.setup.hslice,
            ["altitude"],
            self._on_column_slice_change,
            eager=True,
        )
        self._subscribe(
            self.ctx.setup.vslice,
            ["orientation"],
            self._on_orientation_slice_change,
            eager=True,
        )

        self._subscribe(
            self.ctx.setup.cloud,
            ["threshold_by", "threshold_value", "opacity"],
            self._on_cloud_change,
            eager=True,
        )

        self._subscribe(
            self.ctx.setup, ["active_viz"], self._on_visibility_change, eager=True
        )
        self._subscribe(
            self.ctx.setup.zscale, ["scale"], self._on_z_scale_change, eager=True
        )
        self._subscribe(self.colormap_config, ["mapper_change"], self._need_render)
        self.ctrl.update_color_range.add(self.colormap_config.update_color_range)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _need_render(self, _):
        self.html_view.update()

    def _on_z_scale_change(self, zscale):
        for projection_filter in self._projections:
            projection_filter.SetAltitudeScale(zscale)

        self.html_view.update()

    def _on_visibility_change(self, active_viz):
        has_volume = "volume" in active_viz
        has_slice = "hslice" in active_viz or "vslice" in active_viz
        has_cloud = "cloud" in active_viz
        has_inside = has_slice or has_cloud

        self.slice_h_actor.visibility = 0
        self.slice_v_actor.visibility = 0
        self.outline_actor.visibility = 0
        self.volume_actor.visibility = 0
        self.threshold_actor.visibility = 1 if has_cloud else 0

        if has_volume:
            self.volume_actor.visibility = 1
            self.outline_actor.visibility = 0

        if has_slice:
            self.slice_h_actor.visibility = "hslice" in active_viz
            self.slice_v_actor.visibility = "vslice" in active_viz

        if has_inside:
            self.outline_actor.visibility = has_volume
            self.volume_actor.visibility = 0

        self.ctrl.update_color_range.enable_empty()()
        self.html_view.update()

    def _on_volume_color_by_change(self, color_by):
        if color_by:
            self.colormap_config.set_data_array(color_by, self.get_data_array, "cell")
        self.html_view.update()

    def _on_column_height_change(self, altitude_range):
        self.volume.SetLevelRange(*altitude_range)

        self.ctx.setup.hslice.altitude = max(
            self.ctx.setup.hslice.altitude, altitude_range[0]
        )
        self.ctx.setup.hslice.altitude = min(
            self.ctx.setup.hslice.altitude, altitude_range[1]
        )
        self.ctrl.update_color_range()
        self.html_view.update()

    def _on_column_slice_change(self, level):
        self.horizontal_slice.SetLevelRange(level, level)
        self.ctrl.update_color_range.enable_empty()()
        self.html_view.update()

    def _on_orientation_slice_change(self, heading):
        nx = math.cos(math.radians(heading))
        ny = math.sin(math.radians(heading))

        self.slice_v_plane.origin = (
            self.ctx.setup.center[0],
            self.ctx.setup.center[1],
            0,
        )
        self.slice_v_plane.normal = (nx, ny, 0)
        self.html_view.update()

    def _on_cloud_change(self, threshold_by, threshold_value, opacity):
        if not threshold_by:
            return
        ds = self.clean_volume.GetOutput()
        array = ds.cell_data[threshold_by]
        min_value, max_value = array.GetRange()
        value = (max_value - min_value) * threshold_value + min_value

        self.threshold.SetInputArrayToProcess(
            0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, threshold_by
        )
        self.threshold.SetThresholdFunction(2)
        self.threshold.SetUpperThreshold(value)
        self.threshold_actor.property.opacity = opacity
        self.html_view.update()

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
                # self.ctrl.reset_camera.add(self.html_view.reset_camera)
                self.ctrl.reset_camera.add(self._reset_camera)

                with controls.TopRightFloatControls():
                    v3.VBtn(
                        icon="mdi-crop-free",
                        classes="rounded",
                        density="comfortable",
                        variant="plain",
                        click=self.ctrl.reset_camera,
                    )

                with controls.Controls(), controls.TopLeftFloatControls():
                    controls.ZScale()
                    controls.Cloud()
                    controls.Surface()
                    controls.Volume()
                    controls.HorizontalSlice()
                    controls.VerticalSlice()
                    controls.FindData()
                    controls.CropColumn()

                with controls.BottomCenterFloatControls():
                    with self.colormap_config.provide_as("colormap"):
                        colormaps.HorizontalScalarBar("colormap", popup_location="top")


register_analysis(NAME, Viz3D)
