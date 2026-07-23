import json

import numpy as np
import plotly.graph_objects as go
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html, plotly
from trame.widgets import vuetify3 as v3
from vtkmodules.util import numpy_support

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.io import EAMColumnSource

NAME = "time"


class TimeCharts(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._subscriptions = []

        self.columns = column_reader
        self.single_column_reader = EAMColumnSource()
        self.single_column_reader.SetDataFileName(self.columns.GetDataFileName())

        self.ctx.setup.surface_chart.column = self.ctx.setup.col_ids.GetId(0)

        self._build_ui()
        self.bind_reactivity()

    @property
    def name(self):
        return self._id

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.surface_chart, ["color_by", "column"], self._compute_heatmap
        )
        self._subscribe(
            self.ctx.setup.column, ["altitude_range"], self._compute_heatmap
        )
        self._subscribe(self.ctx.setup.volume, ["color_by"], self._sync_color_by)

    def unbind_reactivity(self):
        while self._subscriptions:
            self._subscriptions.pop()()

    def _sync_color_by(self, color_by):
        self.ctx.setup.surface_chart.color_by = color_by

    def _compute_heatmap(self, *_):
        field = self.ctx.setup.surface_chart.color_by
        col_id = self.ctx.setup.surface_chart.column
        altitude_range = self.ctx.setup.column.altitude_range

        if field is None:
            return

        col = self.single_column_reader
        col.SetColumnIds(json.dumps([col_id]))
        select_arrays = col.GetProfileVariables()

        select_arrays.DisableAllArrays()
        select_arrays.EnableArray(field)

        series = []
        levels = None
        for t in range(self.ctx.setup.time_index_max):
            col.SetSlicing(json.dumps({"time": t}))
            col.Update()
            table = col.GetOutputDataObject(0)
            array = table.GetColumnByName(field)
            profile = numpy_support.vtk_to_numpy(array)[0]  # (n_lev,)
            series.append(profile[altitude_range[0] : altitude_range[1]])

            if levels is None:
                levels = table.field_data["lev"][0][
                    altitude_range[0] : altitude_range[1]
                ]

        series = np.array(series)  # (time, level)
        # fig = px.imshow(
        #     series.T,
        #     aspect="auto",
        #     origin="lower",
        #     color_continuous_scale="Viridis",
        # )
        fig = go.Figure(
            data=go.Heatmap(
                z=series.T,
                y=levels,
                colorscale="Viridis",
            )
        )
        fig.update_layout(
            xaxis_title="time",
            yaxis={"title": field, "autorange": "reversed"},
            showlegend=False,
            margin={"b": 0, "l": 0, "r": 0, "t": 0},
        )
        fig.update_xaxes(side="top")

        with self.state:
            self.update_figure(fig)

    def shift_col_id(self, delta):
        all_ids = self.ctx.setup.col_ids
        current_col_id = self.ctx.setup.surface_chart.column
        num_ids = all_ids.GetNumberOfIds()
        for i in range(num_ids):
            local_id = all_ids.GetId(i)
            if current_col_id == local_id:
                target_idx = min(max(0, i + delta), num_ids - 1)
                self.ctx.setup.surface_chart.column = all_ids.GetId(target_idx)
                return

        self.ctx.setup.surface_chart.column = all_ids.GetId(0)

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with (
                self.ctx.setup.provide_as("global"),
                html.Div(
                    style="position:absolute;top:0;left:0;width:100%;height:100%;",
                    classes="d-flex flex-column",
                ),
            ):
                with v3.VToolbar(
                    density="compact", classes="px-2 d-flex ga-2 bg-grey-darken-3"
                ):
                    v3.VIcon("mdi-timeline-clock-outline")
                    v3.VSelect(
                        v_model="global.surface_chart.color_by",
                        items=(
                            "global.variables_3d.filter(v => v.selected).map(v => v.name)",
                        ),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        classes="w-100",
                    )
                    v3.VSpacer()
                    v3.VSelect(
                        prepend_inner_icon="mdi-map-marker-outline",
                        v_model="global.surface_chart.column",
                        items=("JSON.parse(global.col_ids_str)",),
                        density="compact",
                        hide_details=True,
                        variant="flat",
                        style="width:190px;",
                    )
                    v3.VBtn(
                        icon="mdi-chevron-left",
                        click=(self.shift_col_id, "[-1]"),
                        classes="rounded",
                        density="compact",
                    )
                    v3.VBtn(
                        icon="mdi-chevron-right",
                        click=(self.shift_col_id, "[+1]"),
                        classes="rounded",
                        density="compact",
                    )

                with html.Div(classes="flex-fill pa-2 br-red"):
                    self.update_figure = plotly.Figure(
                        display_mode_bar=("false",)
                    ).update

                with self.ctx.setup.provide_as("controls"):
                    with html.Div(
                        style="position:absolute;left:1rem;top:1rem;z-index:100;",
                        classes="d-flex flex-column ga-2 align-start",
                    ):
                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('cloud')",
                        ):
                            v3.VBtn(
                                icon="mdi-weather-cloudy",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.cloud.show = !controls.cloud.show",
                            )
                            v3.VSlider(
                                v_show="controls.cloud.show",
                                v_model="controls.cloud.opacity",
                                min=0,
                                max=1,
                                step=0.01,
                                style="width: 300px",
                                density="compact",
                                hide_details=True,
                                classes="mr-4",
                            )


register_analysis(NAME, TimeCharts)
