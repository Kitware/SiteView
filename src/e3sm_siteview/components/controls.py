from contextlib import suppress

from trame.widgets import dataclass, html
from trame.widgets import vuetify3 as v3


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


class BottomCenterFloatControls(v3.VCard):
    def __init__(self):
        super().__init__(
            style="position:absolute;left:1rem;right:1rem;bottom:1rem;height:1rem;z-index:100;",
            classes="d-flex flex-column ga-2 align-center",
        )


class TopRightFloatControls(v3.VCard):
    def __init__(self):
        super().__init__(style="position:absolute;right:1rem;top:1rem;z-index:100;")


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


class Cloud(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["cloud"], icon="mdi-weather-cloudy")
        with self:
            v3.VSlider(
                v_show="controls.cloud.show",
                v_model="controls.cloud.opacity",
                min=0,
                max=1,
                step=0.01,
                style="width: 370px",
                density="compact",
                hide_details=True,
                classes="mr-4",
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
        super().__init__(keys=["slice"], icon="mdi-altimeter")
        with self:
            v3.VSlider(
                v_show="controls.slice.show",
                v_model="controls.slice.altitude",
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
        super().__init__(keys=["slice"], icon="mdi-flip-horizontal")
        with self:
            v3.VNumberInput(
                v_show="controls.slice.show",
                v_model="controls.slice.orientation",
                step=[1],
                min=[-90],
                max=[90],
                hide_details=True,
                density="compact",
                prepend_inner_icon="mdi-compass-outline",
                control_variant="stacked",
                variant="flat",
                classes="border-e-thin border-s-thin",
                style="width: 370px",
            )


class FindData(BaseToolbar):
    def __init__(self):
        super().__init__(keys=["find_data"], icon="mdi-magnify-scan")
        with self:
            v3.VTextField(
                v_show="controls.find_data.show",
                v_model="controls.find_data.formula",
                hide_details=True,
                density="compact",
                append_inner_icon="mdi-view-grid-plus-outline",
                style="width: 370px",
                placeholder="T >= 27",
                variant="flat",
                classes="border-e-thin border-s-thin",
                click_appendInner=self._apply_find_data,
            )

    def _apply_find_data(self):
        print("Perform a selection...")


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
