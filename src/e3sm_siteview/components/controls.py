from contextlib import suppress

from trame.widgets import colormaps, dataclass, html
from trame.widgets import vuetify4 as v4

HISTOGRAM_SNAP_PERCENTILES = [1, *range(5, 100, 5)]


class Controls(dataclass.Provider):
    def __init__(self):
        super().__init__(name="controls")
        self.instance = self.ctx.setup._id


# (key, icon, title) of the 3D view layers/tools
VIZ_LAYERS = [
    ("cloud", "mdi-weather-cloudy", "Clouds"),
    ("zscale", "mdi-arrow-expand-vertical", "Vertical scaling"),
    ("surface", "mdi-layers-outline", "Surface"),
    ("volume", "mdi-cube-outline", "Volume"),
    ("hslice", "mdi-altimeter", "Horizontal slice"),
    ("vslice", "mdi-flip-horizontal", "Vertical slice"),
    ("find_data", "mdi-magnify-scan", "Find data"),
    ("histogram", "mdi-chart-histogram", "Histogram"),
    ("column", "mdi-sort", "Column cropping"),
    ("probes", "mdi-map-marker-plus", "Probes"),
]
VIZ_LAYER_INFO = {key: (icon, title) for key, icon, title in VIZ_LAYERS}
# Keyboard shortcut toggling each layer, in the VIZ_LAYERS order
VIZ_LAYER_SHORTCUTS = dict(zip([k for k, *_ in VIZ_LAYERS], "1234567890", strict=False))


def toggle_layer(key):
    """JS expression adding/removing a VIZ_LAYERS key of controls.active_viz"""
    active = f"controls.active_viz.includes('{key}')"
    return (
        f"controls.active_viz = {active}"
        f" ? controls.active_viz.filter(v => v !== '{key}')"
        f" : [...controls.active_viz, '{key}']"
    )


# Shared props so every input of the floating cards looks the same
FIELD_PROPS = {"density": "compact", "hide_details": True, "variant": "outlined"}
SLIDER_PROPS = {"density": "compact", "hide_details": True}


def IconBtn(icon, tooltip=None, size="small", location="top", **kwargs):
    """Icon button with the density/variant shared by all the floating cards"""
    if tooltip is not None:
        kwargs[f"v_tooltip_{location}"] = (
            tooltip if isinstance(tooltip, tuple) else f"'{tooltip}'"
        )
    kwargs.setdefault("variant", "text")
    return v4.VBtn(
        icon=icon,
        size=size,
        density="comfortable",
        classes=f"rounded {kwargs.pop('classes', '')}",
        **kwargs,
    )


class LeftFloatControls(html.Div):
    """Left column of the 3D view: layer rail and camera controls"""

    def __init__(self):
        super().__init__(
            style="position:absolute;left:1rem;top:1rem;z-index:100;",
            classes="d-flex flex-column ga-2",
        )


class VizLayerRail(v4.VCard):
    """Vertical toggles of the 3D view layers/tools"""

    def __init__(self):
        show = "controls.show_tools"
        super().__init__(classes="sv-float d-flex flex-column pa-1 ga-1")
        with self:
            # Hide all the tools to focus on the visualization
            IconBtn(
                (f"{show} ? 'mdi-menu-open' : 'mdi-menu'",),
                (f"{show} ? 'Hide tools' : 'Show tools'",),
                size="default",
                location="end",
                click=f"{show} = !{show}",
            )
        with self, html.Div(v_show=show, classes="d-flex flex-column ga-1"):
            v4.VDivider()
            for key, icon, title in VIZ_LAYERS:
                active = f"controls.active_viz.includes('{key}')"
                shortcut = VIZ_LAYER_SHORTCUTS.get(key)
                IconBtn(
                    icon,
                    f"{title} ({shortcut})" if shortcut else title,
                    size="default",
                    location="end",
                    color=(f"{active} ? 'primary' : undefined",),
                    variant=(f"{active} ? 'tonal' : 'text'",),
                    click=toggle_layer(key),
                )


class VizLayersPanel(html.Div):
    """Settings of the active layers, right of the VizLayerRail.

    The container lets the mouse events go to the 3D view, only the card
    catches them. Add the layer sections inside the ``card``.
    """

    def __init__(self):
        super().__init__(
            # Leave room for the scalar bars at the bottom
            style=(
                "position:absolute;left:4.75rem;top:1rem;bottom:6rem;width:340px;"
                "z-index:100;pointer-events:none;"
            ),
        )
        with self:
            self.card = v4.VCard(
                v_show=(
                    "controls.show_tools && controls.active_viz.some(v => "
                    f"{[k for k, *_ in VIZ_LAYERS]}.includes(v))"
                ),
                classes="sv-float sv-layers overflow-y-auto",
                style="pointer-events:auto;max-height:100%;",
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
                classes="text-body-small font-weight-medium text-high-emphasis px-2 text-no-wrap text-truncate",
                style="flex-shrink:0;max-width:100%;",
            )
            with colormaps.HorizontalScalarBar(name, has_menu=False) as bar:
                bar.classes += " rounded"
                with v4.VMenu(
                    v_model=f"{name}.menu",
                    activator="parent",
                    location="top",
                    close_on_content_click=False,
                ):
                    with v4.VCard(classes="sv-float", style="width: fit-content;"):
                        html.Div(
                            title,
                            classes="text-title-small px-4 pt-2 text-truncate",
                        )
                        colormaps.ColorMapEditor(name, flat=True, style="height: 50vh;")


class CameraFocus(v4.VCard):
    def __init__(self, reset_camera):
        super().__init__(
            v_show="controls.show_tools",
            classes="sv-float d-flex flex-column align-center pa-1 ga-1",
        )
        is_earth = "controls.camera_focus === 'earth'"
        with self:
            IconBtn(
                "mdi-crop-free",
                "Reset camera (R)",
                size="default",
                location="end",
                click=reset_camera,
            )
            v4.VDivider(classes="align-self-stretch")
            IconBtn(
                (f"{is_earth} ? 'mdi-earth' : 'mdi-image-filter-center-focus'",),
                (
                    f"{is_earth} ? 'Earth focus: rotate around earth center' "
                    ": 'Data focus: rotate around data bottom'",
                ),
                size="default",
                location="end",
                click=f"controls.camera_focus = {is_earth} ? 'data' : 'earth'",
            )


def SliderValue(text, min_width="3.5rem"):
    """Current value (with units) of a slider, to use in its append slot"""
    with v4.Template(v_slot_append=True):
        html.Div(
            text,
            classes="text-body-small text-medium-emphasis text-no-wrap text-right",
            style=f"min-width: {min_width};",
        )


class LayerSection(html.Div):
    """Row of an active layer in the VizLayersPanel.

    The header shows the layer name with a summary of its settings while
    collapsed (``controls.<key>.show``). Add the settings in ``body`` and
    extra header buttons in ``actions``.
    """

    def __init__(self, key, summary=None, expandable=True):
        icon, title = VIZ_LAYER_INFO[key]
        show = f"controls.{key}.show" if expandable else "false"
        super().__init__(
            v_if=f"controls.active_viz.includes('{key}')",
            classes="sv-layer",
        )
        toggle = {"click": f"{show} = !{show}", "style": "cursor:pointer;"}
        with self:
            with html.Div(classes="d-flex align-center pa-1 ga-1"):
                with html.Div(
                    classes="d-flex align-center flex-fill ga-2 pl-2 overflow-hidden",
                    **(toggle if expandable else {}),
                ):
                    v4.VIcon(icon, size="small", color="primary")
                    html.Div(
                        title,
                        classes="text-body-medium font-weight-medium text-no-wrap",
                    )
                    if summary:
                        html.Div(
                            summary,
                            v_show=f"!{show}",
                            classes="text-body-small text-medium-emphasis text-truncate",
                        )
                self.actions = html.Div(classes="d-flex align-center")
                if expandable:
                    IconBtn(
                        (f"{show} ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                        (f"{show} ? 'Collapse' : 'Expand'",),
                        click=f"{show} = !{show}",
                    )
                IconBtn(
                    "mdi-close",
                    "Hide layer",
                    click=(
                        f"controls.active_viz = controls.active_viz.filter(v => v !== '{key}')"
                    ),
                )
            self.body = html.Div(v_if=show, classes="d-flex flex-column ga-2 px-3 pb-3")


class ZScale(LayerSection):
    def __init__(self):
        super().__init__("zscale", summary="&times;{{ controls.zscale.scale }}")
        with self.body:
            with v4.VSlider(
                v_model="controls.zscale.scale",
                min=1,
                max=5000,
                step=10,
                **SLIDER_PROPS,
            ):
                SliderValue("&times;{{ controls.zscale.scale }}")


class Cloud(LayerSection):
    def __init__(self):
        super().__init__("cloud", summary="{{ controls.cloud.threshold_by }}")
        with self.body:
            v4.VSelect(
                v_model=("controls.cloud.threshold_by", None),
                items=(
                    "controls.variables_3d.filter(v => v.selected).map(v => v.name)",
                ),
                **FIELD_PROPS,
            )
            with v4.VSlider(
                v_model="controls.cloud.threshold_value",
                min=0,
                max=1,
                step=0.005,
                prepend_icon="mdi-water-opacity",
                v_tooltip_top="'Threshold (fraction of the field range)'",
                **SLIDER_PROPS,
            ):
                # Threshold is relative to the field range of each file
                SliderValue(
                    "≥ {{ (100 * controls.cloud.threshold_value).toFixed(1) }}%"
                )
            with v4.VSlider(
                v_model="controls.cloud.opacity",
                min=0,
                max=1,
                step=0.01,
                prepend_icon="mdi-opacity",
                v_tooltip_top="'Opacity'",
                **SLIDER_PROPS,
            ):
                SliderValue("{{ Math.round(100 * controls.cloud.opacity) }}%")


class ColorBySection(LayerSection):
    """Layer colored by one of the selected controls.<variables> fields"""

    def __init__(self, key, variables):
        super().__init__(key, summary=f"{{{{ controls.{key}.color_by }}}}")
        self._key = key
        self._variables = variables
        with self.body, html.Div(classes="d-flex align-center ga-1"):
            v4.VSelect(
                v_model=(f"controls.{key}.color_by", None),
                items=(
                    f"controls.{variables}.filter(v => v.selected).map(v => v.name)",
                ),
                classes="flex-fill",
                **FIELD_PROPS,
            )
            IconBtn(
                "mdi-chevron-left",
                "Previous field",
                click=(self._shift_color_by, "[-1]"),
            )
            IconBtn(
                "mdi-chevron-right",
                "Next field",
                click=(self._shift_color_by, "[+1]"),
            )

    def _shift_color_by(self, delta):
        controls = getattr(self.ctx.setup, self._key)
        variables = getattr(self.ctx.setup, self._variables)
        items = [field.name for field in variables if field.selected]
        idx_found = 0

        if len(items) == 0:
            return

        with suppress(ValueError):
            idx_found = items.index(controls.color_by)

        idx_found += delta
        idx_found = min(max(0, idx_found), len(items) - 1)

        controls.color_by = items[idx_found]


class Surface(ColorBySection):
    def __init__(self):
        super().__init__("surface", "variables_2d")


class Volume(ColorBySection):
    def __init__(self):
        super().__init__("volume", "variables_3d")


def EdgeToggle(key):
    """Toggle the cell edges of the controls.<key> slice"""
    edges = f"controls.{key}.edges"
    return IconBtn(
        (f"{edges} ? 'mdi-grid' : 'mdi-grid-off'",),
        (f"{edges} ? 'Hide edges' : 'Show edges'",),
        click=f"{edges} = !{edges}",
    )


class HorizontalSlice(LayerSection):
    def __init__(self):
        level = "{{ utils.e3sm.formatLevel(controls.column.levels, controls.hslice.altitude) }}"
        super().__init__("hslice", summary=level)
        with self.actions:
            EdgeToggle("hslice")
        with self.body:
            with v4.VSlider(
                v_model="controls.hslice.altitude",
                step="1",
                min=("controls.column.altitude_range[0]",),
                max=("controls.column.altitude_range[1]",),
                **SLIDER_PROPS,
            ):
                SliderValue(level, min_width="4.5rem")


class VerticalSlice(LayerSection):
    def __init__(self):
        angle = "{{ controls.vslice.orientation }}°"
        super().__init__("vslice", summary=angle)
        with self.actions:
            EdgeToggle("vslice")
        with self.body:
            with v4.VSlider(
                v_model="controls.vslice.orientation",
                step="1",
                min=[-180],
                max=[180],
                **SLIDER_PROPS,
            ):
                SliderValue(angle)


class FindData(LayerSection):
    def __init__(self):
        formula = "controls.find_data.formula"
        super().__init__("find_data", summary=f"{{{{ {formula} }}}}")
        with self.body:
            with v4.VTextField(
                v_model=formula,
                density="compact",
                variant="outlined",
                hide_details="auto",
                append_inner_icon="mdi-view-grid-plus-outline",
                placeholder="T >= 27",
                error_messages=("controls.find_data.error",),
                click_appendInner=self._apply_find_data,
                v_on_keydown_enter=self._apply_find_data,
                focus="utils.e3sm.trackFormulaInput($event)",
            ):
                # Variables menu: insert a field name at the cursor
                with (
                    v4.Template(v_slot_prepend_inner=True),
                    v4.VMenu(location="bottom start", max_height=300),
                ):
                    with v4.Template(v_slot_activator="{ props }"):
                        v4.VIcon(
                            "mdi-function-variant",
                            v_bind="props",
                            v_tooltip_top="'Insert a variable'",
                        )
                    with v4.VList(density="compact"):
                        v4.VListItem(
                            v_for="f in controls.variables_3d.filter(v => v.selected)",
                            key="f.name",
                            title=("f.name",),
                            click=(
                                f"{formula} = utils.e3sm.insertInFormula({formula}, f.name)"
                            ),
                        )

    def _apply_find_data(self):
        self.server.controller.apply_find_data()


class Histogram(LayerSection):
    def __init__(self):
        super().__init__(
            "histogram",
            summary=(
                "{{ controls.histogram.range[0].toPrecision(4) }}"
                " &ndash; {{ controls.histogram.range[1].toPrecision(4) }}"
            ),
        )
        with self.body as container:
            container.classes = "d-flex flex-column px-3 pb-3"  # remove gap
            container.add_child(
                '<trame-plotly :key="controls.dark" v-if="controls.histogram.figure.data"'
                ' :data="controls.histogram.figure.data"'
                ' :layout="utils.e3sm.plotlyLayout(controls.histogram.figure.layout, controls.dark)"'
                ' :displayModeBar="false" :displaylogo="false"'
                ' style="height: 200px;" />'
            )
            v4.VRangeSlider(
                model_value=("controls.histogram.range",),
                min=("controls.histogram.data_range[0]",),
                max=("controls.histogram.data_range[1]",),
                step=0,
                # A dragged bound is no longer snapped
                update_modelValue=(
                    "if ($event[0] !== controls.histogram.range[0]) "
                    "controls.histogram.snap_min = null;"
                    "if ($event[1] !== controls.histogram.range[1]) "
                    "controls.histogram.snap_max = null;"
                    "controls.histogram.range = $event;"
                ),
                **SLIDER_PROPS,
            )
            with html.Div(classes="d-flex align-center"):
                self._snap_menu(0, "min", "max", lambda p: p)
                v4.VSpacer()
                self._snap_menu(1, "max", "min", lambda p: 100 - p)

    def _snap_menu(self, idx, bound, other_bound, to_percentile):
        snap = f"controls.histogram.snap_{bound}"
        other = f"controls.histogram.snap_{other_bound}"
        with v4.VMenu(location="top", max_height=300):
            with v4.Template(v_slot_activator="{ props }"):
                v4.VBtn(
                    f"{{{{ controls.histogram.range[{idx}].toPrecision(4) }}}}",
                    v_bind="props",
                    size="small",
                    variant="text",
                    color=(f"{snap} ? 'primary' : undefined",),
                    append_icon="mdi-menu-down",
                    classes="text-none px-1",
                )
            with v4.VList(density="compact"):
                v4.VListItem(
                    title=f"Data {bound}",
                    active=(f"{snap} === 0",),
                    click=f"{snap} = 0",
                )
                for p in HISTOGRAM_SNAP_PERCENTILES:
                    v4.VListItem(
                        title=f"{to_percentile(p)}th percentile",
                        subtitle=f"excluding data {bound}",
                        active=(f"{snap} === {p}",),
                        # Prevent crossing the other snapped bound
                        disabled=(f"{other} > 0 && {p} >= 100 - {other}",),
                        click=f"{snap} = {p}",
                    )


class CropColumn(LayerSection):
    def __init__(self):
        # Level 0 is the top of the atmosphere
        levels = (
            "{{ utils.e3sm.formatLevel(controls.column.levels, controls.column.altitude_range[0]) }}"
            " &ndash; {{ utils.e3sm.formatLevel(controls.column.levels, controls.column.altitude_range[1]) }}"
        )
        super().__init__("column", summary=levels)
        with self.body:
            v4.VRangeSlider(
                v_if="controls.column.col_max_idx",
                v_model="controls.column.altitude_range",
                min="0",
                max=("controls.column.col_max_idx",),
                step="1",
                **SLIDER_PROPS,
            )
            html.Div(levels, classes="text-body-small text-medium-emphasis text-center")


class Probes(LayerSection):
    def __init__(self):
        super().__init__(
            "probes", summary="Click a column to chart it", expandable=False
        )


def _probe_anchor_style(x, y, offset, extra=""):
    """Absolute position at (x, y) view fractions, flipped to stay in view"""
    return (
        f"`position:absolute;z-index:200;left:${{100 * {x}}}%;top:${{100 * {y}}}%;"
        f"transform:translate(${{{x} > 0.5 ? 'calc(-100% - {offset}px)' : '{offset}px'}},"
        f" ${{{y} > 0.5 ? 'calc(-100% - {offset}px)' : '{offset}px'}});{extra}`"
    )


class ProbeTooltip(html.Div):
    """Lat/lon and value of the hovered column (needs the "probe" provider)"""

    def __init__(self):
        super().__init__(
            v_if="probe.hover",
            classes="text-body-small text-white bg-grey-darken-3 rounded px-2 py-1 text-no-wrap elevation-2",
            # Keep the mouse events for the 3D view
            style=(
                _probe_anchor_style(
                    "probe.hover_x", "probe.hover_y", 12, "pointer-events:none;"
                ),
            ),
        )
        with self:
            html.Div("{{ probe.hover_title }}")
            html.Div(
                "{{ probe.hover_value }}",
                v_if="probe.hover_value",
                classes="font-weight-medium",
            )


class ProbeMenu(v4.VCard):
    """Use the clicked column in the charts (needs the "probe" and "global" providers)"""

    def __init__(self, use_for_heatmap, toggle_line_chart):
        in_line_chart = "global.line_chart.columns.includes(probe.menu_col_id)"
        super().__init__(
            v_if="probe.menu",
            density="compact",
            classes="sv-float",
            style=(_probe_anchor_style("probe.menu_x", "probe.menu_y", 4),),
        )
        with self:
            with v4.VCardItem(
                prepend_icon="mdi-map-marker-outline", classes="py-1 pr-1"
            ):
                html.Div("{{ probe.menu_title }}", classes="text-title-small")
                with v4.Template(v_slot_append=True):
                    v4.VBtn(
                        icon="mdi-close",
                        size="small",
                        variant="plain",
                        density="comfortable",
                        click="probe.menu = false",
                    )
            v4.VDivider()
            with v4.VList(density="compact", classes="py-0"):
                v4.VListItem(
                    prepend_icon="mdi-view-grid-compact",
                    title="Use for column heat map",
                    active=("global.surface_chart.column === probe.menu_col_id",),
                    click=use_for_heatmap,
                )
                v4.VListItem(
                    prepend_icon=(
                        f"{in_line_chart} ? 'mdi-chart-line-variant' : 'mdi-chart-line'",
                    ),
                    title=(
                        f"{in_line_chart} ? 'Remove from line chart' : 'Add to line chart'",
                    ),
                    click=toggle_line_chart,
                )
