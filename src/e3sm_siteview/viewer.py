import json
import math
from pathlib import Path

from trame.app import TrameComponent, asynchronous
from trame.ui.html import DivLayout
from trame.widgets import client
from trame.widgets import vuetify4 as v4

from e3sm_siteview.analysis import create_analysis, load_all_analysis
from e3sm_siteview.cli import configure_and_parse
from e3sm_siteview.data_models import GlobalParameters, VisualizationAnalysis
from e3sm_siteview.io import EAMColumnSource, EAMMeshSource, EAMSurfaceSource


def compute_data_regions(lon_min, lon_max, lat_min, lat_max):
    """Data extent as [(left, top, width, height), ...] in percent of an
    equirectangular map centered on lon 0, split in two when crossing the
    antimeridian. Empty when the data covers the whole globe."""
    x_percent = []  # [(origin, width), ...]
    lat_o = ((90 - lat_max) / 180) * 100
    lat_h = math.fabs(((90 - lat_min) / 180) * 100 - lat_o)

    if lon_min < 180 and lon_max > 180:
        o1 = 0.5 + lon_min / 360
        x_percent.append((o1, 1 - o1))
        x_percent.append((0, (lon_max - 180) / 360))
    elif lon_min > 180:
        o = (lon_min - 180) / 360
        w = (lon_max - lon_min) / 360
        x_percent.append((o, w))
    else:
        o = 0.5 + lon_min / 360
        w = (lon_max - lon_min) / 360
        x_percent.append((o, w))

    # make sure we go left to right
    x_percent.sort()
    if len(x_percent) == 2 and x_percent[0][0] + x_percent[0][1] == x_percent[1][0]:
        # remove split, just make 1 region
        x_percent = [(x_percent[0][0], x_percent[0][1] + x_percent[1][1])]

    if len(x_percent) == 1 and x_percent[0][1] == 1:
        # Full region => no highlight
        x_percent = []

    return [(lon_o * 100, lat_o, lon_w * 100, lat_h) for lon_o, lon_w in x_percent]


def create_viewers(server):
    load_all_analysis()
    options = configure_and_parse(server.cli)

    mesh_algo = EAMMeshSource()
    mesh_algo.SetFileName(str(Path(options.cf).resolve()))
    mesh_algo.Update()
    server.context.mesh_algo = mesh_algo
    server.context.mesh = mesh_algo.GetOutputDataObject(0)
    server.context.setup = GlobalParameters(server)
    viewers = server.context.viewers = {}

    # Highlight of the data region on the site selection map
    server.state.data_regions = compute_data_regions(
        *server.context.mesh.GetBounds()[:4]
    )

    # Load fields
    for data_file in options.df:
        viewer = E3SMAnalyser(
            server,
            Path(data_file).resolve(),
        )
        viewers[viewer.name] = viewer


class E3SMAnalyser(TrameComponent):
    def __init__(self, server, data_file):
        super().__init__(server)
        self._name = Path(data_file).name
        self.config = VisualizationAnalysis(self.server)

        self.columns = EAMColumnSource()
        self.columns.SetDataFileName(data_file)
        self.columns.SetColumnIds(json.dumps([0]))
        self.columns.SetSlicing(json.dumps({"time": 0}))

        # Extract column height
        if self.ctx.setup.column.col_max_idx == 0:
            array_select = self.columns.GetProfileVariables()
            array_name = array_select.GetArrayName(0)
            array_select.EnableArray(array_name)
            self.columns.Update()
            table = self.columns.GetOutputDataObject(0)
            self.ctx.setup.column.col_max_idx = (
                table.GetColumnByName(array_name).number_of_components - 1
            )
            self.ctx.setup.column.altitude_range = (
                0,
                self.ctx.setup.column.col_max_idx,
            )
            if table.GetFieldData().HasArray("lev"):
                self.ctx.setup.column.levels = [
                    float(v) for v in table.field_data["lev"].ravel()
                ]

        self.ctx.setup.register_data_reader(self.columns)

        self.surface = EAMSurfaceSource()
        self.surface.SetDataFileName(data_file)
        self.ctx.setup.register_surface_reader(self.surface)

        self._analysis = {}
        self._build_ui()

    @property
    def name(self):
        return self._name

    @property
    def template_name(self):
        return self.name.replace(".", "_").replace("-", "_")

    def _build_ui(self):
        with DivLayout(self.server, self.template_name, classes="h-100") as self.ui:
            # Dock panels live outside of v-app, so provide the app theme
            with (
                v4.VThemeProvider(
                    theme=("siteview_theme",), with_background=True, classes="h-100"
                ),
                v4.VContainer(classes="h-100 pa-0", fluid=True),
            ):
                with (
                    v4.VRow(no_gutters=True, classes="h-100 sv-analysis-row"),
                    self.config.provide_as("conf"),
                    self.ctx.setup.provide_as("global"),
                ):
                    with v4.VCol(
                        v_for="template_name, viz_name in conf.panels",
                        key="viz_name",
                        classes="position-relative",
                        v_show="global.active_analysis.includes(viz_name)",
                    ):
                        client.ServerTemplate(name=("template_name",))

    def add_analysis(self, *analysis_types):
        panels = {}
        for type in analysis_types:
            analysis = create_analysis(type, self.server, self.columns, self.surface)
            if analysis is None:
                msg = f"Invalid analysis type: {type}"
                raise ValueError(msg)
            self._analysis[type] = analysis
            panels[type] = analysis.name

        self.config.panels = panels
        asynchronous.create_task(self._add_panel())

    async def _add_panel(self):
        self.show_panel()

    def show_panel(self):
        """Add the dock panel of this file (no-op on clients that have it)"""
        self.ctx.views_container.add_panel(
            self.template_name, self.name, self.template_name
        )

    @property
    def analyses(self):
        return self._analysis.values()
