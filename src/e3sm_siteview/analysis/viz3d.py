import math

import plotly.colors
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from trame.app import TrameComponent
from trame.dataclasses.colormaps import ColormapConfig
from trame.decorators import controller
from trame.ui.html import DivLayout
from trame.widgets import colormaps, html, rca
from vtkmodules.vtkCommonCore import vtkMath
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkPlane
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import (
    vtk3DLinearGridCrinkleExtractor,
    vtkAppendPolyData,
    vtkFeatureEdges,
    vtkPolyDataToUnstructuredGrid,
    vtkThreshold,
)
from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkFiltersSources import (
    vtkConeSource,
    vtkCylinderSource,
    vtkSphereSource,
    vtkTexturedSphereSource,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkIOImage import vtkJPEGReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkAssembly,
    vtkBillboardTextActor3D,
    vtkCamera,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkTexture,
)

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.components import controls
from e3sm_siteview.io import (
    CONTINENT_PATH,
    EARTH_RADIUS,
    EARTH_TEXTURE_PATH,
    EAMColumnMarkers,
    EAMColumnVolume,
    EAMGridLines,
    EAMLevelCylinder,
    EAMProject,
)

NAME = "viz"

CAMERA = vtkCamera()

EARTH_AXIS = (0, 1, 0)

# Orientation marker site cylinder (textured sphere source has radius 0.5)
SITE_MARKER_EARTH_RADIUS = 0.5
SITE_MARKER_HEIGHT = 0.1
SITE_MARKER_MIN_RADIUS = 0.03

# Selected column markers (line chart colors match its plotly traces)
COLUMN_MARKER_AREA_FRACTION = 0.05
COLUMN_MARKER_SPHERE_SCALE = 2  # sphere radius relative to cylinder radius
COLUMN_MARKER_AMBIENT = 0.5
HEATMAP_COLUMN_COLOR = (255, 255, 255)
LINE_CHART_COLORS = [
    plotly.colors.hex_to_rgb(c) for c in plotly.colors.qualitative.Plotly
]


def _rotate_camera(camera, angle, axis, center):
    """Rotate camera around an axis going through center"""
    transform = vtkTransform()
    transform.Translate(center)
    transform.RotateWXYZ(angle, axis)
    transform.Translate(*(-v for v in center))
    camera.position = transform.TransformPoint(camera.position)
    camera.focal_point = transform.TransformPoint(camera.focal_point)


def create_north_up_interactor_style(get_rotation_center):
    """
    Trackball camera style where left-drag rotates the camera around
    an axis parallel to the earth rotation axis going through
    get_rotation_center() (horizontal motion) and tilts it toward the
    poles (vertical motion) while keeping north up.
    Middle/right buttons and wheel keep their default pan/zoom behavior.
    """
    style = vtkInteractorStyleTrackballCamera()
    state = {"rotating": False}

    def on_left_press(*_):
        interactor = style.GetInteractor()
        style.FindPokedRenderer(*interactor.GetEventPosition())
        if style.GetCurrentRenderer() is None:
            return
        state["rotating"] = True

    def on_left_release(*_):
        state["rotating"] = False

    def on_mouse_move(*_):
        if not state["rotating"]:
            style.OnMouseMove()
            return

        interactor = style.GetInteractor()
        renderer = style.GetCurrentRenderer()
        camera = renderer.active_camera
        x, y = interactor.GetEventPosition()
        last_x, last_y = interactor.GetLastEventPosition()
        width, height = renderer.GetSize()
        center = get_rotation_center()

        # Spin around the earth rotation axis
        azimuth = -180.0 * (x - last_x) / max(width, 1)
        _rotate_camera(camera, azimuth, EARTH_AXIS, center)

        # Tilt toward the poles without going over them
        elevation = 180.0 * (y - last_y) / max(height, 1)
        dop = camera.GetDirectionOfProjection()
        right = [0, 0, 0]
        vtkMath.Cross(dop, EARTH_AXIS, right)
        if vtkMath.Normalize(right) > 0:
            pole_angle = math.degrees(
                math.acos(max(-1.0, min(1.0, vtkMath.Dot(dop, EARTH_AXIS))))
            )
            if 1.0 < pole_angle - elevation < 179.0:
                _rotate_camera(camera, elevation, right, center)

        camera.view_up = EARTH_AXIS
        camera.OrthogonalizeViewUp()
        if style.GetAutoAdjustCameraClippingRange():
            renderer.ResetCameraClippingRange()
        interactor.Render()

    style.AddObserver("LeftButtonPressEvent", on_left_press)
    style.AddObserver("LeftButtonReleaseEvent", on_left_release)
    style.AddObserver("MouseMoveEvent", on_mouse_move)

    return style


class Viz3D(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self.view_handler = None
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

    def refresh_data(self):
        self._need_render()

    def _data_anchor(self):
        """Point on the earth surface at the bottom center of the data"""
        x_rad = math.radians(self.ctx.setup.center[0])
        y_rad = math.radians(self.ctx.setup.center[1])
        cos_y_rad = math.cos(y_rad)
        xs = EARTH_RADIUS * math.sin(x_rad) * cos_y_rad
        ys = EARTH_RADIUS * math.sin(y_rad)
        zs = EARTH_RADIUS * math.cos(x_rad) * cos_y_rad
        return (xs, ys, zs)

    def _rotation_center(self):
        if self.ctx.setup.camera_focus == "earth":
            return (0, 0, 0)
        return self._data_anchor()

    @controller.add("reset_camera")
    def _reset_camera(self):
        xs, ys, zs = self._data_anchor()
        camera = self.renderer.active_camera
        camera.position = (xs * 1000, ys * 1000, zs * 1000)
        camera.view_up = EARTH_AXIS
        if self.ctx.setup.camera_focus == "earth":
            camera.focal_point = (0, 0, 0)
            camera.OrthogonalizeViewUp()
            r = EARTH_RADIUS
            self.renderer.ResetCamera(-r, r, -r, r, -r, r)
        else:
            camera.focal_point = (xs, ys, zs)
            camera.OrthogonalizeViewUp()
            self.renderer.ResetCamera(self.outline_actor.bounds)

        if self.view_handler:
            self.view_handler.update()

    def _setup_vtk(self):
        renderer = vtkRenderer(background=(0.5, 0.5, 0.5), active_camera=CAMERA)
        renderWindow = vtkRenderWindow()
        renderWindow.AddRenderer(renderer)
        renderWindow.OffScreenRenderingOn()

        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        self.interactor_style = create_north_up_interactor_style(self._rotation_center)
        renderWindowInteractor.SetInteractorStyle(self.interactor_style)

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

        # Level cylinder
        self.level_cylinder = EAMLevelCylinder()
        self.level_cylinder.SetCenter(*self.ctx.setup.center[:2])
        self.level_cylinder.SetRadius(self.ctx.setup.radius_deg)
        level_cylinder_mapper = vtkDataSetMapper()
        level_cylinder_mapper.ScalarVisibilityOff()
        self.level_cylinder_actor = vtkActor(mapper=level_cylinder_mapper)
        self.level_cylinder_actor.property.color = (1, 1, 1)
        self.level_cylinder_actor.property.line_width = 2
        self.renderer.AddActor(self.level_cylinder_actor)
        self.level_cylinder_proj = self._proj()
        (
            self.clean_volume
            >> self.level_cylinder
            >> self.level_cylinder_proj
            >> level_cylinder_mapper
        )

        # Level cylinder labels: depth tested billboards (occluded by the
        # scene), synced with the projected cylinder right before each render.
        self.level_label_actors = []
        self._level_labels_mtime = 0
        renderWindow.AddObserver("StartEvent", self._sync_level_labels)

        # Selected column markers: cylinders through the columns used by the
        # heat map / line chart, plus spheres on the line chart cells
        self.column_markers = EAMColumnMarkers()
        self.column_markers.SetAreaFraction(COLUMN_MARKER_AREA_FRACTION)
        self.column_markers.SetInputConnection(self.volume.GetOutputPort())
        column_cylinders_proj = self._proj()
        column_cylinders_proj.SetInputConnection(self.column_markers.GetOutputPort(0))
        column_cylinders_mapper = vtkDataSetMapper()
        column_cylinders_mapper.ScalarVisibilityOn()
        column_cylinders_mapper.SetScalarModeToUseCellFieldData()
        column_cylinders_mapper.SelectColorArray("colors")
        column_cylinders_mapper.SetColorModeToDirectScalars()
        column_cylinders_proj >> column_cylinders_mapper
        column_cylinders_actor = vtkActor(mapper=column_cylinders_mapper)
        # Keep the sides bright when looking down the columns
        column_cylinders_actor.property.ambient = COLUMN_MARKER_AMBIENT
        column_cylinders_actor.property.diffuse = 1 - COLUMN_MARKER_AMBIENT
        self.renderer.AddActor(column_cylinders_actor)

        # Column spheres: synced with the projected centers before each render
        self.column_spheres_proj = self._proj()
        self.column_spheres_proj.SetInputConnection(
            self.column_markers.GetOutputPort(1)
        )
        self.column_sphere_actors = []
        self._column_spheres_mtime = 0
        renderWindow.AddObserver("StartEvent", self._sync_column_spheres)

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

        # Orientation marker: textured earth
        earth_texture = vtkTexture(interpolate=1, mipmap=1)
        vtkJPEGReader(file_name=str(EARTH_TEXTURE_PATH)) >> earth_texture
        earth_marker_mapper = vtkDataSetMapper()
        (
            vtkTexturedSphereSource(theta_resolution=64, phi_resolution=32)
            >> earth_marker_mapper
        )
        earth_marker = vtkActor(mapper=earth_marker_mapper, texture=earth_texture)
        # Mostly ambient lighting so the texture stays bright on all sides
        # while keeping a bit of shading for the 3D feel
        earth_marker.property.ambient = 0.6
        earth_marker.property.diffuse = 0.5
        earth_marker.property.specular = 0
        # Sphere source has poles on Z with lon=-180 on +X; align it with
        # EAMProject (north on +Y, lon=0 on +Z, lon=90 on +X)
        marker_matrix = vtkMatrix4x4()
        marker_matrix.DeepCopy(
            (
                *(0, -1, 0, 0),
                *(0, 0, 1, 0),
                *(-1, 0, 0, 0),
                *(0, 0, 0, 1),
            )
        )
        earth_marker.user_matrix = marker_matrix

        # Rotation axis: south to north (+Y) with a cone at the north tip
        rotation_axis = vtkAppendPolyData()
        vtkCylinderSource(radius=0.02, height=1.4, resolution=24) >> rotation_axis
        (
            vtkConeSource(
                center=(0, 0.7, 0),
                direction=(0, 1, 0),
                height=0.2,
                radius=0.07,
                resolution=24,
            )
            >> rotation_axis
        )
        rotation_axis_mapper = vtkDataSetMapper()
        rotation_axis >> rotation_axis_mapper
        rotation_axis_actor = vtkActor(mapper=rotation_axis_mapper)
        rotation_axis_actor.property.color = (0.9, 0.2, 0.2)

        # Selected site: bright cylinder sticking out of the earth surface,
        # placed by _update_site_marker() (cylinder source is along +Y)
        self.site_marker_source = vtkCylinderSource(
            height=SITE_MARKER_HEIGHT, resolution=24
        )
        site_marker_mapper = vtkDataSetMapper()
        self.site_marker_source >> site_marker_mapper
        self.site_marker_actor = vtkActor(mapper=site_marker_mapper)
        self.site_marker_actor.property.color = (1, 0.9, 0)
        self.site_marker_actor.property.lighting = 0
        self._update_site_marker()

        earth_with_axis = vtkAssembly()
        earth_with_axis.AddPart(earth_marker)
        earth_with_axis.AddPart(rotation_axis_actor)
        earth_with_axis.AddPart(self.site_marker_actor)

        self.orientation_widget = vtkOrientationMarkerWidget(
            orientation_marker=earth_with_axis,
            interactor=renderWindowInteractor,
            viewport=(0.85, 0.85, 1, 1),
        )
        self.orientation_widget.EnabledOn()
        self.orientation_widget.InteractiveOff()

        self._reset_camera()

    def _update_site_marker(self):
        """Place the orientation marker site cylinder at the selected region"""
        lon, lat = self.ctx.setup.center[:2]
        self.site_marker_source.radius = max(
            SITE_MARKER_MIN_RADIUS,
            SITE_MARKER_EARTH_RADIUS * math.radians(self.ctx.setup.radius_deg),
        )
        # Translate along +Y onto the surface, then tilt from the north pole
        # down to the site latitude and spin to its longitude (EAMProject frame)
        transform = vtkTransform()
        transform.RotateY(lon)
        transform.RotateX(90 - lat)
        transform.Translate(0, SITE_MARKER_EARTH_RADIUS, 0)
        self.site_marker_actor.user_transform = transform

    def _sync_level_labels(self, *_):
        self.level_cylinder_proj.Update()
        cylinder = self.level_cylinder_proj.GetOutputDataObject(0)
        if cylinder.GetMTime() == self._level_labels_mtime:
            return
        self._level_labels_mtime = cylinder.GetMTime()

        labels = cylinder.GetPointData().GetAbstractArray("labels")
        entries = []
        if labels is not None:
            for i in range(labels.GetNumberOfValues()):
                if text := labels.GetValue(i):
                    entries.append((text, cylinder.GetPoint(i)))

        while len(self.level_label_actors) < len(entries):
            actor = vtkBillboardTextActor3D()
            actor.text_property.color = (1, 1, 1)
            actor.text_property.font_size = 28
            actor.text_property.justification = 1  # center
            actor.text_property.vertical_justification = 1  # center
            self.renderer.AddActor(actor)
            self.level_label_actors.append(actor)

        for i, actor in enumerate(self.level_label_actors):
            if i < len(entries):
                actor.input, actor.position = entries[i]
                actor.visibility = 1
            else:
                actor.visibility = 0

    def _sync_column_spheres(self, *_):
        self.column_spheres_proj.Update()
        centers = self.column_spheres_proj.GetOutputDataObject(0)
        if centers.GetMTime() == self._column_spheres_mtime:
            return
        self._column_spheres_mtime = centers.GetMTime()

        n_spheres = centers.GetNumberOfPoints()
        while len(self.column_sphere_actors) < n_spheres:
            mapper = vtkDataSetMapper()
            source = vtkSphereSource(theta_resolution=24, phi_resolution=24)
            source >> mapper
            actor = vtkActor(mapper=mapper)
            actor.source = source
            actor.property.ambient = COLUMN_MARKER_AMBIENT
            actor.property.diffuse = 1 - COLUMN_MARKER_AMBIENT
            self.renderer.AddActor(actor)
            self.column_sphere_actors.append(actor)

        point_data = centers.GetPointData()
        for i, actor in enumerate(self.column_sphere_actors):
            if i < n_spheres:
                radius_deg = point_data.GetArray("radius").GetValue(i)
                actor.source.center = centers.GetPoint(i)
                actor.source.radius = (
                    COLUMN_MARKER_SPHERE_SCALE * math.radians(radius_deg) * EARTH_RADIUS
                )
                actor.property.color = [
                    v / 255 for v in point_data.GetArray("colors").GetTuple3(i)
                ]
                actor.visibility = 1
            else:
                actor.visibility = 0

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.volume,
            ["color_by"],
            self._on_volume_color_by_change,
            eager=True,
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
            self.ctx.setup,
            ["center", "radius_deg"],
            self._on_region_change,
            eager=True,
        )
        self._subscribe(
            self.ctx.setup.zscale, ["scale"], self._on_z_scale_change, eager=True
        )
        self._subscribe(self.ctx.setup, ["camera_focus"], self._on_camera_focus_change)
        self._subscribe(
            self.ctx.setup, ["active_analysis"], self._on_column_markers_change
        )
        self._subscribe(
            self.ctx.setup.surface_chart, ["column"], self._on_column_markers_change
        )
        self._subscribe(
            self.ctx.setup.line_chart, ["columns"], self._on_column_markers_change
        )
        self._subscribe(
            self.ctx.setup.hslice,
            ["altitude"],
            self._on_column_markers_change,
            eager=True,
        )
        self._subscribe(self.colormap_config, ["mapper_change"], self._need_render)
        self.ctrl.update_color_range.add(self.colormap_config.update_color_range)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _need_render(self, *_):
        self.view_handler.update()

    def _on_z_scale_change(self, zscale):
        for projection_filter in self._projections:
            projection_filter.SetAltitudeScale(zscale)

        self.view_handler.update()

    def _on_column_markers_change(self, *_):
        active_analysis = self.ctx.setup.active_analysis
        line_entries = []
        if "cellTimeChart" in active_analysis:
            line_entries = [
                (col_id, LINE_CHART_COLORS[i % len(LINE_CHART_COLORS)])
                for i, col_id in enumerate(self.ctx.setup.line_chart.columns)
            ]

        cylinders = list(
            line_entries
        )  # Edit if only want to see sphere for line locations
        heatmap_column = self.ctx.setup.surface_chart.column
        if "columnHeatMap" in active_analysis and heatmap_column is not None:
            cylinders = [e for e in cylinders if e[0] != heatmap_column]
            cylinders.append((heatmap_column, HEATMAP_COLUMN_COLOR))

        self.column_markers.SetCylinders(cylinders)
        self.column_markers.SetSpheres(line_entries)
        self.column_markers.SetLevel(self.ctx.setup.hslice.altitude)
        self.view_handler.update()

    def _on_camera_focus_change(self, *_):
        self._reset_camera()

    def _on_region_change(self, center, radius_deg):
        self.level_cylinder.SetCenter(center[0], center[1])
        self.level_cylinder.SetRadius(radius_deg)
        self._update_site_marker()
        self.view_handler.update()

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
        self.view_handler.update()

    def _on_volume_color_by_change(self, color_by):
        if color_by:
            self.colormap_config.set_data_array(color_by, self.get_data_array, "cell")
        self.view_handler.update()

    def _on_column_height_change(self, altitude_range):
        self.volume.SetLevelRange(*altitude_range)

        self.ctx.setup.hslice.altitude = max(
            self.ctx.setup.hslice.altitude, altitude_range[0]
        )
        self.ctx.setup.hslice.altitude = min(
            self.ctx.setup.hslice.altitude, altitude_range[1]
        )
        self.ctrl.update_color_range()
        self.view_handler.update()

    def _on_column_slice_change(self, level):
        self.horizontal_slice.SetLevelRange(level, level)
        self.ctrl.update_color_range.enable_empty()()
        self.view_handler.update()

    def _on_orientation_slice_change(self, heading):
        nx = math.cos(math.radians(heading))
        ny = math.sin(math.radians(heading))

        self.slice_v_plane.origin = (
            self.ctx.setup.center[0],
            self.ctx.setup.center[1],
            0,
        )
        self.slice_v_plane.normal = (nx, ny, 0)
        self.view_handler.update()

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
        self.view_handler.update()

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with html.Div(
                style="position:absolute;top:0;left:0;width:100%;height:100%;"
            ):
                view = rca.RemoteControlledArea(display="image")
                self.view_handler = view.create_view_handler(
                    self.render_window,
                    encoder="turbo-jpeg",
                )
                self.ctrl.render.add(self.view_handler.update)

                with controls.Controls(), controls.TopRightFloatControls():
                    controls.CameraFocus(reset_camera=self.ctrl.reset_camera)

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
