"""3D view analysis: columns around the site over the earth"""

import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from trame.app import TrameComponent
from trame.dataclasses.colormaps import ColormapConfig
from trame.ui.html import DivLayout
from trame.widgets import html, rca
from vtkmodules.vtkFiltersGeneral import vtkCleanUnstructuredGrid

from e3sm_siteview.analysis import ANALYSIS_ID
from e3sm_siteview.analysis.viz3d.camera import CameraMixin
from e3sm_siteview.analysis.viz3d.export import ExportMixin
from e3sm_siteview.analysis.viz3d.histogram import HistogramMixin
from e3sm_siteview.analysis.viz3d.layers import LayersMixin
from e3sm_siteview.analysis.viz3d.probe import ProbeMixin
from e3sm_siteview.analysis.viz3d.scene import SceneMixin
from e3sm_siteview.components import controls
from e3sm_siteview.data_models import ProbeInfo
from e3sm_siteview.io import EAMColumnSurface, EAMColumnVolume


class Viz3D(
    SceneMixin,
    CameraMixin,
    LayersMixin,
    HistogramMixin,
    ProbeMixin,
    ExportMixin,
    TrameComponent,
):
    def __init__(self, server, column_reader, surface_reader=None):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self.view_handler = None
        self._find_data_valid = False
        self._histogram_key = None
        self._histogram_data_key = None
        self._histogram_snap_key = None
        self._projections = []
        self._subscriptions = []

        self.columns = column_reader
        self.colormap_config = ColormapConfig(self.server, preset="Viridis")
        self.probe = ProbeInfo(self.server)

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

        # Surface (2D fields) on the ground footprint of the columns
        self.surface_reader = surface_reader
        self.surface_colormap_config = ColormapConfig(self.server, preset="Inferno")
        self.surface = EAMColumnSurface()
        self.surface.SetInputConnection(0, self.ctx.mesh_algo.GetOutputPort())
        if surface_reader is not None:
            self.surface.SetInputConnection(1, surface_reader.GetOutputPort())

        self._setup_vtk()
        self._build_ui()
        self.bind_reactivity()

    @property
    def name(self):
        return self._id

    def refresh_data(self):
        self._on_surface_color_by_change(self.ctx.setup.surface.color_by)
        self._update_histogram()
        self._need_render()

    def _need_render(self, *_):
        self.view_handler.update()

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
            self.ctx.setup.surface,
            ["color_by"],
            self._on_surface_color_by_change,
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
            self.ctx.setup.hslice,
            ["edges"],
            self._on_hslice_edges_change,
            eager=True,
        )
        self._subscribe(
            self.ctx.setup.vslice,
            ["edges"],
            self._on_vslice_edges_change,
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
        self._subscribe(self.ctx.setup, ["dark"], self._on_theme_change, eager=True)
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
        self._subscribe(
            self.ctx.setup.histogram,
            ["range", "snap_min", "snap_max"],
            self._update_histogram,
            eager=True,
        )
        self._subscribe(self.colormap_config, ["mapper_change"], self._need_render)
        self._subscribe(
            self.surface_colormap_config, ["mapper_change"], self._need_render
        )
        self._subscribe(
            self.colormap_config,
            ["mapper_change"],
            self._sync_chart_colormap,
            eager=True,
        )
        self.ctrl.update_color_range.add(self.colormap_config.update_color_range)
        self.ctrl.update_color_range.add(self._update_surface_color_range)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with (
                self.ctx.setup.provide_as("global"),
                self.probe.provide_as("probe"),
                html.Div(
                    style="position:absolute;top:0;left:0;width:100%;height:100%;",
                    mouseleave="probe.hover = false",
                ),
            ):
                view = rca.RemoteControlledArea(
                    display="image",
                    send_mouse_move=("global.active_viz.includes('probes')",),
                )
                self.view_handler = view.create_view_handler(
                    self.render_window,
                    encoder="turbo-jpeg",
                )
                self.ctrl.render.add(self.view_handler.update)

                controls.ProbeTooltip()
                controls.ProbeMenu(
                    use_for_heatmap=self.probe_to_heatmap,
                    toggle_line_chart=self.probe_toggle_line_chart,
                )

                with controls.Controls(), controls.LeftFloatControls():
                    controls.VizLayerRail()
                    controls.CameraFocus(
                        reset_camera=self.ctrl.reset_camera,
                        export_image=controls.download_click(
                            self.server, "siteview-3d.png", "image/png", self.export_png
                        ),
                    )

                with controls.Controls(), controls.VizLayersPanel().card:
                    controls.Cloud()
                    controls.ZScale()
                    controls.Surface()
                    controls.Volume()
                    controls.HorizontalSlice()
                    controls.VerticalSlice()
                    controls.FindData()
                    controls.Histogram()
                    controls.CropColumn()
                    controls.Probes()

                with (
                    controls.Controls(),
                    controls.BottomCenterFloatControls(),
                    self.colormap_config.provide_as("colormap"),
                    self.surface_colormap_config.provide_as("surface_colormap"),
                ):
                    controls.TitledScalarBar(
                        "surface_colormap",
                        "controls.surface.color_by",
                        v_if=(
                            "controls.active_viz.includes('surface')"
                            " && controls.surface.color_by"
                        ),
                    )
                    controls.TitledScalarBar(
                        "colormap",
                        "controls.volume.color_by",
                        v_if=(
                            "['volume', 'hslice', 'vslice', 'find_data'].some(v => controls.active_viz.includes(v))"
                        ),
                    )
