from contextlib import suppress

from trame.widgets import colormaps, dataclass, html
from trame.widgets import vuetify3 as v3

HISTOGRAM_SNAP_PERCENTILES = [1, *range(5, 100, 5)]


class Controls(dataclass.Provider):
    def __init__(self):
        super().__init__(name="controls")
        self.instance = self.ctx.setup._id


class TopLeftFloatControls(html.Div):
    def __init__(self):
        super().__init__(
            style="position:absolute;left:1rem;top:1rem;width:0px;z-index:100;",
            classes="d-flex flex-column ga-2 align-start",
        )


class BottomCenterFloatControls(html.Div):
    def __init__(self):
        super().__init__(
            style="position:absolute;left:1rem;right:1rem;bottom:1rem;z-index:100;",
            classes="d-flex flex-column ga-2 align-center",
        )


class TitledScalarBar(html.Div):
    """Horizontal scalar bar with a title, also shown in its preset editor.

    ``name`` is the provided ColormapConfig name, ``label`` a static text
    (e.g. "Volume") and ``field`` a JS expression of the colored field name.
    """

    def __init__(self, name, field, **kwargs):
        super().__init__(
            classes="d-flex align-center w-100 flex-column overflow-hidden", **kwargs
        )
        title = f"{{{{ {field} }}}}"
        with self:
            html.Div(
                title,
                title=(f"`${{{field}}}`",),
                classes="text-caption font-weight-medium text-white px-2 text-no-wrap text-truncate",
                style="flex-shrink:0;max-width:100%;",
            )
            with colormaps.HorizontalScalarBar(name, has_menu=False) as bar:
                bar.classes += " rounded"
                with v3.VMenu(
                    v_model=f"{name}.menu",
                    activator="parent",
                    location="top",
                    close_on_content_click=False,
                ):
                    with v3.VCard(style="width: fit-content;"):
                        html.Div(
                            title,
                            classes="text-subtitle-2 px-4 pt-2 text-truncate",
                        )
                        colormaps.ColorMapEditor(name, flat=True, style="height: 50vh;")


class TopRightFloatControls(v3.VCard):
    def __init__(self):
        super().__init__(style="position:absolute;right:1rem;top:1rem;z-index:100;")


class CameraFocus(html.Div):
    def __init__(self, reset_camera):
        super().__init__(classes="d-flex flex-column align-center")
        is_earth = "controls.camera_focus === 'earth'"
        with self:
            with v3.VTooltip(text="Reset camera", location="start"):
                with v3.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        icon="mdi-crop-free",
                        classes="rounded",
                        density="comfortable",
                        variant="plain",
                        click=reset_camera,
                    )
            v3.VDivider()
            with v3.VTooltip(
                text=(
                    f"{is_earth} ? 'Earth focus: rotate around earth center' "
                    ": 'Data focus: rotate around data bottom'",
                ),
                location="start",
            ):
                with v3.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        icon=(
                            f"{is_earth} ? 'mdi-earth' "
                            ": 'mdi-image-filter-center-focus'",
                        ),
                        classes="rounded",
                        density="comfortable",
                        variant="plain",
                        click=(
                            f"controls.camera_focus = {is_earth} ? 'data' : 'earth'"
                        ),
                    )


class BaseToolbar(v3.VCard):
    def __init__(self, keys, icon):
        super().__init__(
            classes="d-flex align-center",
            v_if="||".join([f"controls.active_viz.includes('{k}')" for k in keys]),
            style="max-width: 370px",
        )
        with self:
            v3.VBtn(
                icon=icon,
                density="comfortable",
                variant="plain",
                classes="rounded ma-1",
                click=f"controls.{keys[0]}.show = !controls.{keys[0]}.show",
            )


class ZScale(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["zscale"], icon="mdi-arrow-expand-vertical")
        with self:
            v3.VSlider(
                v_show="controls.zscale.show",
                v_model="controls.zscale.scale",
                min=1,
                max=5000,
                step=10,
                style="width: 370px",
                density="compact",
                hide_details=True,
                classes="mr-4",
            )


class Cloud(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["cloud"], icon="mdi-weather-cloudy")
        with self:
            with v3.VCol(
                classes="border-s px-0",
                style="width: 370px",
                v_show="controls.cloud.show",
            ):
                v3.VSelect(
                    v_show="controls.cloud.show",
                    v_model=("controls.cloud.threshold_by", None),
                    items=(
                        "controls.variables_3d.filter(v => v.selected).map(v => v.name)",
                    ),
                    density="compact",
                    hide_details=True,
                    variant="flat",
                )
                v3.VSlider(
                    v_show="controls.cloud.show",
                    v_model="controls.cloud.threshold_value",
                    min=0,
                    max=1,
                    step=0.005,
                    density="compact",
                    hide_details=True,
                    prepend_icon="mdi-water-opacity",
                    classes="pr-2",
                )
                v3.VSlider(
                    v_show="controls.cloud.show",
                    v_model="controls.cloud.opacity",
                    min=0,
                    max=1,
                    step=0.01,
                    density="compact",
                    hide_details=True,
                    prepend_icon="mdi-opacity",
                    classes="pr-2",
                )


class Surface(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["surface"], icon="mdi-layers-outline")
        with self:
            v3.VSelect(
                v_show="controls.surface.show",
                v_model=("controls.surface.color_by", None),
                items=(
                    "controls.variables_2d.filter(v => v.selected).map(v => v.name)",
                ),
                density="compact",
                hide_details=True,
                variant="flat",
                style="width: 370px;",
            )


class Volume(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["volume", "slice"], icon="mdi-cube-outline")
        with self:
            v3.VSelect(
                v_show="controls.volume.show",
                v_model=("controls.volume.color_by", None),
                items=(
                    "controls.variables_3d.filter(v => v.selected).map(v => v.name)",
                ),
                density="compact",
                hide_details=True,
                variant="flat",
                style="width: 370px",
            )
            v3.VBtn(
                v_show="controls.volume.show",
                icon="mdi-chevron-left",
                click=(self._shift_color_by, "[-1]"),
                classes="rounded",
                density="compact",
                variant="flat",
            )
            v3.VBtn(
                v_show="controls.volume.show",
                icon="mdi-chevron-right",
                click=(self._shift_color_by, "[+1]"),
                classes="rounded mx-1",
                density="compact",
                variant="flat",
            )

    def _shift_color_by(self, delta):
        current_field = self.ctx.setup.volume.color_by
        items = [field.name for field in self.ctx.setup.variables_3d if field.selected]
        idx_found = 0

        if len(items) == 0:
            return

        with suppress(ValueError):
            idx_found = items.index(current_field)

        idx_found += delta
        idx_found = min(max(0, idx_found), len(items) - 1)

        self.ctx.setup.volume.color_by = items[idx_found]


class HorizontalSlice(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["hslice"], icon="mdi-altimeter")
        with self:
            v3.VSlider(
                v_show="controls.hslice.show",
                v_model="controls.hslice.altitude",
                step="1",
                min=("controls.column.altitude_range[0]",),
                max=("controls.column.altitude_range[1]",),
                hide_details=True,
                density="comfortable",
                classes="mr-4",
                style="width: 370px",
            )


class VerticalSlice(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["vslice"], icon="mdi-flip-horizontal")
        with self:
            v3.VSlider(
                v_show="controls.vslice.show",
                v_model="controls.vslice.orientation",
                step="1",
                min=[-180],
                max=[180],
                hide_details=True,
                density="comfortable",
                classes="mr-4",
                style="width: 370px",
                # prepend_icon="mdi-compass-outline",
            )
            # v3.VNumberInput(
            #     v_show="controls.slice.show",
            #     v_model="controls.slice.orientation",
            #     step=[1],
            #     min=[-180],
            #     max=[180],
            #     hide_details=True,
            #     density="compact",
            #     prepend_inner_icon="mdi-compass-outline",
            #     control_variant="stacked",
            #     variant="flat",
            #     classes="border-e-thin border-s-thin",
            #     style="width: 370px",
            # )


class FindData(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["find_data"], icon="mdi-magnify-scan")
        with self:
            v3.VTextField(
                v_show="controls.find_data.show",
                v_model="controls.find_data.formula",
                hide_details="auto",
                density="compact",
                append_inner_icon="mdi-view-grid-plus-outline",
                style="width: 370px",
                placeholder="T >= 27",
                variant="flat",
                classes="border-e-thin border-s-thin",
                error_messages=("controls.find_data.error",),
                click_appendInner=self._apply_find_data,
                keydown_enter=self._apply_find_data,
            )

    def _apply_find_data(self):
        self.server.controller.apply_find_data()


class Histogram(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["histogram"], icon="mdi-chart-histogram")
        with self:
            with v3.VCol(
                v_show="controls.histogram.show",
                classes="border-s pa-0",
                style="width: 325px",
            ) as container:
                container.add_child(
                    '<trame-plotly v-if="controls.histogram.figure.data"'
                    ' :data="controls.histogram.figure.data"'
                    ' :layout="controls.histogram.figure.layout"'
                    ' :displayModeBar="false" :displaylogo="false"'
                    ' style="height: 200px;" />'
                )
                v3.VRangeSlider(
                    model_value=("controls.histogram.range",),
                    min=("controls.histogram.data_range[0]",),
                    max=("controls.histogram.data_range[1]",),
                    step=0,
                    density="compact",
                    hide_details=True,
                    classes="px-2",
                    # A dragged bound is no longer snapped
                    update_modelValue=(
                        "if ($event[0] !== controls.histogram.range[0]) "
                        "controls.histogram.snap_min = null;"
                        "if ($event[1] !== controls.histogram.range[1]) "
                        "controls.histogram.snap_max = null;"
                        "controls.histogram.range = $event;"
                    ),
                )
                with html.Div(classes="d-flex align-center px-1 pb-1"):
                    self._snap_menu(0, "min", "max", lambda p: p)
                    v3.VSpacer()
                    self._snap_menu(1, "max", "min", lambda p: 100 - p)

    def _snap_menu(self, idx, bound, other_bound, to_percentile):
        snap = f"controls.histogram.snap_{bound}"
        other = f"controls.histogram.snap_{other_bound}"
        with v3.VMenu(location="top", max_height=300):
            with v3.Template(v_slot_activator="{ props }"):
                v3.VBtn(
                    f"{{{{ controls.histogram.range[{idx}].toPrecision(4) }}}}",
                    v_bind="props",
                    size="small",
                    variant="text",
                    color=(f"{snap} ? 'primary' : undefined",),
                    append_icon="mdi-menu-down",
                    classes="text-none px-1",
                )
            with v3.VList(density="compact"):
                v3.VListItem(
                    title=f"Data {bound}",
                    active=(f"{snap} === 0",),
                    click=f"{snap} = 0",
                )
                for p in HISTOGRAM_SNAP_PERCENTILES:
                    v3.VListItem(
                        title=f"{to_percentile(p)}th percentile",
                        subtitle=f"excluding data {bound}",
                        active=(f"{snap} === {p}",),
                        # Prevent crossing the other snapped bound
                        disabled=(f"{other} > 0 && {p} >= 100 - {other}",),
                        click=f"{snap} = {p}",
                    )


class CropColumn(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["column"], icon="mdi-sort")
        with self:
            v3.VRangeSlider(
                v_if="controls.column.col_max_idx",
                v_show="controls.column.show",
                v_model="controls.column.altitude_range",
                min="0",
                max=("controls.column.col_max_idx",),
                step="1",
                hide_details=True,
                density="compact",
                variant="flat",
                classes="mr-4",
                style="width: 370px;",
            )
