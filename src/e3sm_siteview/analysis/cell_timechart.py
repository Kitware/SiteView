import json

import numpy as np
import plotly.graph_objects as go
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_client.encoders.numpy import encode
from vtkmodules.util import numpy_support

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.io import EAMColumnSource

NAME = "cellTimeChart"


def min_max(array, min_value, max_value):
    if min_value is None:
        return float(array.min()), float(array.max())

    return float(min(array.min(), min_value)), float(max(array.max(), max_value))


class CellTimeChart(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._subscriptions = []

        self.columns = column_reader
        self.local_data_reader = EAMColumnSource()
        self.local_data_reader.SetDataFileName(self.columns.GetDataFileName())

        self._build_ui()
        self.bind_reactivity()

    @property
    def name(self):
        return self._id

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.line_chart, ["fields", "columns"], self._compute_line_plots
        )
        self._subscribe(self.ctx.setup.slice, ["altitude"], self._compute_line_plots)
        self._subscribe(self.ctx.setup, ["time_index"], self._compute_line_plots)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _compute_line_plots(self, *_):
        fields = self.ctx.setup.line_chart.fields
        col_ids = self.ctx.setup.line_chart.columns
        altitude_idx = self.ctx.setup.slice.altitude
        time_idx = self.ctx.setup.time_index
        self.ctx.setup.line_chart.results = []

        if not fields or not col_ids:
            return

        col = self.local_data_reader
        col.SetColumnIds(json.dumps(col_ids))
        select_arrays = col.GetProfileVariables()
        select_arrays.DisableAllArrays()
        for field in fields:
            select_arrays.EnableArray(field)

        data = {}
        for t in range(self.ctx.setup.time_index_max):
            col.SetSlicing(json.dumps({"time": t}))
            col.Update()
            table = col.GetOutputDataObject(0)
            for field in fields:
                array = table.GetColumnByName(field)
                n_array = numpy_support.vtk_to_numpy(array)
                for idx, col_id in enumerate(col_ids):
                    data.setdefault(field, {}).setdefault(col_id, []).append(
                        n_array[idx][altitude_idx]
                    )

        t_array = np.array(range(self.ctx.setup.time_index_max))
        figs = []
        for field, cols in data.items():
            fig = go.Figure()
            y1 = None
            y0 = None
            for col, values in cols.items():
                array = np.array(values)
                fig.add_trace(
                    go.Scatter(x=t_array, y=array, name=str(col), mode="lines")
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
                with v3.VToolbar(
                    density="compact",
                    classes="px-2 d-flex ga-2 bg-grey-darken-3",
                    theme="dark",
                ):
                    v3.VIcon("mdi-chart-line")
                    with v3.VSelect(
                        v_model="global.line_chart.fields",
                        items=(
                            "global.variables_3d.filter(v => v.selected).map(v => v.name)",
                        ),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        classes="w-100",
                        multiple=True,
                    ):
                        with v3.Template(v_slot_selection="{item, index}"):
                            html.Span(
                                "{{ global.line_chart.fields?.length }} field{{global.line_chart.fields?.length > 1 ? 's' : ''}}",
                                v_if="index == 0",
                            )
                    with v3.VSelect(
                        prepend_inner_icon="mdi-map-marker-outline",
                        v_model="global.line_chart.columns",
                        items=("JSON.parse(global.col_ids_str)",),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        classes="w-100",
                        multiple=True,
                    ):
                        with v3.Template(v_slot_selection="{item, index}"):
                            html.Span(
                                "{{ global.line_chart.columns?.length }} column{{global.line_chart.columns?.length > 1 ? 's' : ''}}",
                                v_if="index == 0",
                            )
                    v3.VSlider(
                        prepend_icon="mdi-altimeter",
                        v_model="global.slice.altitude",
                        step="1",
                        min=("global.column.altitude_range[0]",),
                        max=("global.column.altitude_range[1]",),
                        hide_details=True,
                        density="comfortable",
                        classes="w-100",
                    )

                with html.Div(classes="flex-fill pa-2 border-thin overflow-auto"):
                    # html.Div("{{ global.line_chart }}")
                    with v3.VCard(
                        v_for="v, k in global.line_chart.results",
                        key="k",
                        variant="flat",
                        style=(
                            "`height: max(300px, 100% / ${global.line_chart.results.length})`",
                        ),
                    ) as container:
                        container.add_child(
                            '<trame-plotly :data="v.data" :layout="v.layout" :displayModeBar="false" :displaylogo="false" />'
                        )


register_analysis(NAME, CellTimeChart)
