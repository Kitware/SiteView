import json
import math
from pathlib import Path

from trame.app import TrameComponent, asynchronous
from trame.ui.html import DivLayout
from trame.widgets import client
from trame.widgets import vuetify3 as v3

from e3sm_siteview.analysis import create_analysis, load_all_analysis
from e3sm_siteview.cli import configure_and_parse
from e3sm_siteview.data_models import GlobalParameters, VisualizationAnalysis
from e3sm_siteview.io import EAMColumnSource, EAMMeshSource


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

    # Compute data region
    lon_min, lon_max, lat_min, lat_max, *_ = server.context.mesh.GetBounds()
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
        o = (lon_min - 180) / 360
        w = (lon_max - lon_min) / 360
        x_percent.append((0.5 + o, w))

    server.state.data_regions = [
        (lon_o * 100, lat_o, lon_w * 100, lat_h) for lon_o, lon_w in x_percent
    ]

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

        # max_col_id = int(self.ctx.mesh.GetCellData().GetArray("col_id").GetRange()[1])
        # print("n_cols", max_col_id)

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

        self.ctx.setup.register_data_reader(self.columns)
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
            with v3.VContainer(classes="h-100 pa-0", fluid=True):
                with (
                    v3.VRow(dense=True, classes="h-100"),
                    self.config.provide_as("conf"),
                    self.ctx.setup.provide_as("global"),
                ):
                    with v3.VCol(
                        v_for="tempate_name, viz_name in conf.panels",
                        key="viz_name",
                        classes="position-relative",
                        v_show="global.active_analysis.includes(viz_name)",
                    ):
                        client.ServerTemplate(name=("tempate_name",))

    def add_analysis(self, *analysis_types):
        panels = {}
        for type in analysis_types:
            analysis = create_analysis(type, self.server, self.columns)
            if analysis is None:
                msg = f"Invalid analysis type: {type}"
                raise ValueError(msg)
            self._analysis[type] = analysis
            panels[type] = analysis.name

        self.config.panels = panels
        asynchronous.create_task(
            self._add_panel(self.template_name, self.name, self.template_name)
        )

    async def _add_panel(self, panel_id, label, template_name):
        # print("_add_panel", panel_id, label, template_name)
        self.ctx.views_container.add_panel(panel_id, label, template_name)
