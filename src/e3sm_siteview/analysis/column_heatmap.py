import json

import netCDF4
import numpy as np
import plotly.graph_objects as go
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html, plotly
from trame.widgets import vuetify3 as v3
from trame_client.encoders.numpy import encode
from vtkmodules.util import numpy_support

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis
from e3sm_siteview.io import EAMColumnSource

NAME = "columnHeatMap"


class ColumnHeatMap(TrameComponent):
    def __init__(self, server, column_reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._subscriptions = []

        self.columns = column_reader
        self.single_column_reader = EAMColumnSource()
        self.single_column_reader.SetDataFileName(self.columns.GetDataFileName())

        col_ids = json.loads(self.ctx.setup.col_ids_str)
        self.ctx.setup.surface_chart.column = col_ids[0] if col_ids else None

        self._build_ui()
        self.bind_reactivity()
        self._compute_heatmap()

    @property
    def name(self):
        return self._id

    def _subscribe(self, obj, watch, callback, eager=False, sync=False):
        self._subscriptions.append(obj.watch(watch, callback, eager=eager, sync=sync))

    def bind_reactivity(self):
        self._subscribe(
            self.ctx.setup.surface_chart,
            ["color_by", "column", "extra_fields"],
            self._compute_heatmap,
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

    def _time_labels(self):
        tdim = self.single_column_reader.GetDimensions().get("time")
        if tdim is None:
            return [0]

        if tdim.data is not None and tdim.units:
            try:
                dates = netCDF4.num2date(
                    tdim.data, tdim.units, calendar=tdim.calendar or "standard"
                )
                return [d.strftime("%Y-%m-%d %H:%M") for d in dates]
            except (ValueError, TypeError):
                pass

        return list(range(tdim.size))

    def refresh_data(self):
        self._compute_heatmap()

    def _compute_heatmap(self, *_):
        primary = self.ctx.setup.surface_chart.color_by
        col_id = self.ctx.setup.surface_chart.column
        altitude_range = self.ctx.setup.column.altitude_range

        fields = [primary] if primary else []
        for field in self.ctx.setup.surface_chart.extra_fields:
            if field not in fields:
                fields.append(field)

        if not fields or col_id is None:
            self.ctx.setup.surface_chart.results = []
            return

        col = self.single_column_reader
        col.SetColumnIds(json.dumps([col_id]))
        select_arrays = col.GetProfileVariables()

        select_arrays.DisableAllArrays()
        for field in fields:
            select_arrays.EnableArray(field)

        time_labels = self._time_labels()
        series = {field: [] for field in fields}
        levels = None
        for t in range(len(time_labels)):
            col.SetSlicing(json.dumps({"time": t}))
            col.Update()
            table = col.GetOutputDataObject(0)
            for field in fields:
                array = table.GetColumnByName(field)
                profile = numpy_support.vtk_to_numpy(array)[0]  # (n_lev,)
                series[field].append(profile[altitude_range[0] : altitude_range[1]])

            if levels is None:
                levels = table.field_data["lev"][0][
                    altitude_range[0] : altitude_range[1]
                ]

        # Only label a handful of time steps to keep the axis readable
        tick_step = max(1, len(time_labels) // 6)
        tick_vals = time_labels[::tick_step]
        tick_text = [str(v).replace(" ", "<br>") for v in tick_vals]

        col_label = next(
            (
                item["title"]
                for item in self.ctx.setup.col_items
                if item["value"] == col_id
            ),
            str(col_id),
        )

        results = []
        for field in fields:
            fig = go.Figure(
                data=go.Heatmap(
                    z=np.array(series[field]).T,  # (level, time)
                    x=time_labels,
                    y=levels,
                    colorscale="Viridis",
                    hovertemplate=(
                        f"time: %{{x}}<br>lev: %{{y}}<br>{field}: %{{z}}<extra></extra>"
                    ),
                )
            )
            fig.update_layout(
                title={"text": f"{field} ({col_label})", "x": 0.5, "xanchor": "center"},
                xaxis={
                    "title": "time",
                    "side": "bottom",
                    "type": "category",
                    "tickmode": "array",
                    "tickvals": tick_vals,
                    "ticktext": tick_text,
                    "tickangle": 0,
                },
                yaxis={"autorange": "reversed"},
                showlegend=False,
                margin={"b": 60, "l": 0, "r": 0, "t": 30},
            )
            results.append(
                {
                    "field": field,
                    "removable": field != primary,
                    **encode(fig.to_plotly_json()),
                }
            )

        self.ctx.setup.surface_chart.results = results

    def add_field(self, field):
        extra_fields = self.ctx.setup.surface_chart.extra_fields
        if field != self.ctx.setup.surface_chart.color_by and field not in extra_fields:
            self.ctx.setup.surface_chart.extra_fields = [*extra_fields, field]

    def remove_field(self, field):
        self.ctx.setup.surface_chart.extra_fields = [
            f for f in self.ctx.setup.surface_chart.extra_fields if f != field
        ]

    def shift_col_id(self, delta):
        all_ids = json.loads(self.ctx.setup.col_ids_str)
        if not all_ids:
            return

        current_col_id = self.ctx.setup.surface_chart.column
        if current_col_id in all_ids:
            i = all_ids.index(current_col_id)
            target_idx = min(max(0, i + delta), len(all_ids) - 1)
            self.ctx.setup.surface_chart.column = all_ids[target_idx]
            return

        self.ctx.setup.surface_chart.column = all_ids[0]

    def _build_ui(self):
        plotly.initialize(self.server)
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
                    with html.Div(classes="d-flex ga-2"):
                        with v3.VMenu(location="bottom end"):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VBtn(
                                    v_bind="props",
                                    icon="mdi-plus",
                                    classes="rounded",
                                    density="compact",
                                )
                            with v3.VList(density="compact", max_height="50vh"):
                                v3.VListItem(
                                    v_for=(
                                        "name in global.variables_3d.filter(v => v.selected).map(v => v.name)"
                                        ".filter(n => n !== global.surface_chart.color_by"
                                        " && !global.surface_chart.extra_fields.includes(n))"
                                    ),
                                    key="name",
                                    title=("name",),
                                    click=(self.add_field, "[name]"),
                                )

                        with v3.VMenu(location="bottom end"):
                            with v3.Template(v_slot_activator="{ props }"):
                                v3.VBtn(
                                    v_bind="props",
                                    icon="mdi-map-marker-outline",
                                    classes="rounded",
                                    density="compact",
                                )
                            with v3.VList(density="compact", max_height="50vh"):
                                v3.VListItem(
                                    v_for="item in global.col_items",
                                    key="item.value",
                                    title=("item.title",),
                                    active=(
                                        "item.value === global.surface_chart.column",
                                    ),
                                    click="global.surface_chart.column = item.value",
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

                with html.Div(classes="flex-fill pa-2 border-thin overflow-auto"):
                    with v3.VCard(
                        v_for="(v, i) in global.surface_chart.results",
                        key="v.field",
                        variant="flat",
                        rounded=0,
                        classes="position-relative",
                        style=(
                            "`height: max(300px, (100% - ${5 * (global.surface_chart.results.length - 1)}px) / ${global.surface_chart.results.length});`"
                            " + (i > 0 ? 'border-top: 1px solid rgba(0, 0, 0, 0.25);margin-top: 5px;padding-top: 5px;' : '')",
                        ),
                    ) as container:
                        container.add_child(
                            '<trame-plotly :data="v.data" :layout="v.layout" :displayModeBar="false" :displaylogo="false" />'
                        )
                        v3.VBtn(
                            v_if="v.removable",
                            icon="mdi-close",
                            size="small",
                            variant="outlined",
                            classes="rounded",
                            density="compact",
                            style="position:absolute;top:6px;right:6px;z-index:1;",
                            click=(self.remove_field, "[v.field]"),
                        )


register_analysis(NAME, ColumnHeatMap)
