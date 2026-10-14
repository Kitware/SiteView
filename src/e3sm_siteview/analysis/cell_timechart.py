import json

import numpy as np
import plotly.colors
import plotly.graph_objects as go
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html
from trame.widgets import vuetify4 as v4
from trame_client.encoders.numpy import encode
from vtkmodules.util import numpy_support

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.components.controls import ChartExportMenu, ChartHint
from e3sm_siteview.io import EAMColumnSource, EAMSurfaceSource

NAME = "cellTimeChart"
COLORS = plotly.colors.qualitative.Plotly


def min_max(array, min_value, max_value):
    if min_value is None:
        return float(array.min()), float(array.max())

    return float(min(array.min(), min_value)), float(max(array.max(), max_value))


class CellTimeChart(TrameComponent):
    def __init__(self, server, column_reader, surface_reader=None):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._subscriptions = []

        self.columns = column_reader
        self.surface_reader = surface_reader
        self.local_data_reader = EAMColumnSource()
        self.local_data_reader.SetDataFileName(self.columns.GetDataFileName())
        self.local_surface_reader = None
        if surface_reader is not None:
            self.local_surface_reader = EAMSurfaceSource()
            self.local_surface_reader.SetDataFileName(surface_reader.GetDataFileName())

        self._build_ui()
        self.bind_reactivity()

    @property
    def name(self):
        return self._id

    def refresh_data(self):
        self._compute_line_plots()

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.line_chart, ["fields", "columns"], self._compute_line_plots
        )
        self._subscribe(self.ctx.setup.hslice, ["altitude"], self._compute_line_plots)
        self._subscribe(self.ctx.setup, ["time_index"], self._compute_line_plots)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _compute_line_plots(self, *_):
        fields = self.ctx.setup.line_chart.fields
        col_ids = self.ctx.setup.line_chart.columns
        altitude_idx = self.ctx.setup.hslice.altitude
        time_idx = self.ctx.setup.time_index
        self.ctx.setup.line_chart.results = []

        if not fields or not col_ids:
            return

        # Split fields between the 3D (column) and 2D (surface) readers
        readers = []
        for reader, has_levels in (
            (self.local_data_reader, True),
            (self.local_surface_reader, False),
        ):
            if reader is None:
                continue
            reader_fields = [f for f in fields if f in reader.GetVariables()]
            if not reader_fields:
                continue
            reader.SetColumnIds(json.dumps(col_ids))
            select_arrays = reader.GetProfileVariables()
            select_arrays.DisableAllArrays()
            for field in reader_fields:
                select_arrays.EnableArray(field)
            readers.append((reader, reader_fields, has_levels))

        data = {field: {} for field in fields}
        for t in range(self.ctx.setup.time_index_max + 1):
            for reader, reader_fields, has_levels in readers:
                reader.SetSlicing(json.dumps({"time": t}))
                reader.Update()
                table = reader.GetOutputDataObject(0)
                for field in reader_fields:
                    array = table.GetColumnByName(field)
                    n_array = numpy_support.vtk_to_numpy(array)
                    for idx, col_id in enumerate(col_ids):
                        value = n_array[idx]
                        if has_levels:
                            value = value[altitude_idx]
                        data[field].setdefault(col_id, []).append(value)

        labels = {item["value"]: item["title"] for item in self.ctx.setup.col_items}
        t_array = np.array(range(self.ctx.setup.time_index_max + 1))
        figs = []
        for field, cols in data.items():
            if not cols:
                continue
            fig = go.Figure()
            y1 = None
            y0 = None
            for idx, (col, values) in enumerate(cols.items()):
                array = np.array(values)
                fig.add_trace(
                    go.Scatter(
                        x=t_array,
                        y=array,
                        name=labels.get(col, str(col)),
                        mode="lines",
                        line={"color": COLORS[idx % len(COLORS)]},
                    )
                )
                y0, y1 = min_max(array, y0, y1)

            # Add time vertical line
            fig.add_shape(
                type="line",
                x0=time_idx,
                y0=y0,
                x1=time_idx,
                y1=y1,
                line={
                    "width": 1,
                    "dash": "dash",
                    "color": "Red",
                },
            )

            fig.update_layout(
                # title={"text": field},
                yaxis={"title": {"text": field}},
                margin={"b": 0, "l": 0, "r": 0, "t": 0},
                plot_bgcolor="white",
                # Plotly hides the legend of single trace charts
                showlegend=True,
            )

            figs.append(encode(fig.to_plotly_json()))

        self.ctx.setup.line_chart.results = figs

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            self.ui.root.classes = "border-thin"
            with (
                self.ctx.setup.provide_as("global"),
                html.Div(
                    style="position:absolute;top:0;left:0;width:100%;height:100%;",
                    classes="d-flex flex-column",
                ),
            ):
                with v4.VToolbar(
                    density="compact", classes="px-2 d-flex ga-2 sv-chart-toolbar"
                ):
                    v4.VIcon("mdi-chart-line", color="primary")
                    with v4.VSelect(
                        v_model="global.line_chart.fields",
                        items=(
                            "[...global.variables_3d, ...global.variables_2d].filter(v => v.selected).map(v => v.name)",
                        ),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        classes="w-100",
                        multiple=True,
                    ):
                        with v4.Template(v_slot_selection="{item, index}"):
                            html.Span(
                                "{{ global.line_chart.fields?.length }} field{{global.line_chart.fields?.length > 1 ? 's' : ''}}",
                                v_if="index == 0",
                            )
                    with v4.VSelect(
                        prepend_inner_icon="mdi-map-marker-outline",
                        v_model="global.line_chart.columns",
                        items=("global.col_items",),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        classes="w-100",
                        multiple=True,
                    ):
                        with v4.Template(v_slot_selection="{item, index}"):
                            html.Span(
                                "{{ global.line_chart.columns?.length }} column{{global.line_chart.columns?.length > 1 ? 's' : ''}}",
                                v_if="index == 0",
                            )
                    v4.VSlider(
                        prepend_icon="mdi-altimeter",
                        v_model="global.hslice.altitude",
                        step="1",
                        min=("global.column.altitude_range[0]",),
                        max=("global.column.altitude_range[1]",),
                        hide_details=True,
                        density="comfortable",
                        classes="w-100",
                    )
                    ChartExportMenu(f"{self.name}_charts")

                with html.Div(
                    id=f"{self.name}_charts",
                    classes="flex-fill border-thin overflow-auto",
                ):
                    ChartHint(
                        "!global.line_chart.fields.length",
                        icon="mdi-chart-line",
                        title="Pick fields to plot",
                        text="Choose one or more fields in the toolbar above.",
                    )
                    ChartHint(
                        "global.line_chart.fields.length && !global.line_chart.columns.length",
                        icon="mdi-cursor-default-click-outline",
                        title="Click a column in the 3D view",
                        text=(
                            "With Probes on, click a column and choose"
                            " “Add to line chart”, or pick columns in the toolbar above."
                        ),
                        action="Turn on probes",
                        click="global.active_viz = [...global.active_viz, 'probes']",
                        action_if="!global.active_viz.includes('probes')",
                    )
                    with v4.VCard(
                        v_for="v, k in global.line_chart.results",
                        key="k",
                        variant="flat",
                        rounded=0,
                        classes="pa-2",
                        style=(
                            "`height: max(300px, 100% / ${global.line_chart.results.length})`",
                        ),
                    ) as container:
                        container.add_child(
                            '<trame-plotly :key="global.dark" :data="v.data" :layout="utils.e3sm.plotlyLayout(v.layout, global.dark)" :displayModeBar="false" :displaylogo="false" />'
                        )


register_analysis(NAME, CellTimeChart)
