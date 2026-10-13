from trame.widgets import html
from trame.widgets import vuetify3 as v3

from e3sm_siteview.assets import ASSETS
from e3sm_siteview.components.footer import TooltipButton

N_FIELDS = (
    "controls.variables_2d.filter(v => v.selected).length"
    " + "
    "controls.variables_3d.filter(v => v.selected).length"
)


class StepChip(v3.VChip):
    """Summary of a setup step, click to open it (needs the "controls" provider)"""

    def __init__(self, text, icon, page, tooltip):
        super().__init__(
            text,
            v_tooltip_bottom=tooltip,
            prepend_icon=icon,
            variant=(f"controls.active_page === '{page}' ? 'flat' : 'tonal'",),
            color="primary",
            classes="text-none px-5",
            click=f"controls.active_page = '{page}'",
        )


class AppHeader(v3.VAppBar):
    """Logo, setup summary, analysis selection and app settings"""

    def __init__(self):
        super().__init__(density="compact", flat=True, border="b")

        with self, self.ctx.setup.provide_as("controls"):
            v3.VAvatar(image=ASSETS.icon, size=28, classes="ml-4")
            v3.VAppBarTitle(
                "SiteView",
                classes="flex-0-0 font-weight-medium mx-2",
            )

            with html.Div(classes="d-flex ga-2 ml-2 align-center"):
                StepChip(
                    (
                        "{{ site_selected || utils.e3sm.formatCoords(site_lat, site_lon) }}"
                        " · {{ site_radius }}{{ site_radius_unit === 'deg' ? '°' : ' km' }}"
                        " · {{ controls.n_cols }} column{{ controls.n_cols > 1 ? 's' : '' }}"
                    ),
                    icon="mdi-map-marker-radius",
                    page="site",
                    tooltip="'Change site location and region size'",
                )
                StepChip(
                    f"{{{{ {N_FIELDS} }}}} field{{{{ ({N_FIELDS}) > 1 ? 's' : '' }}}}",
                    icon="mdi-format-list-checks",
                    page="fields",
                    tooltip="'Change the loaded fields'",
                )

                TooltipButton(
                    "'Getting started'",
                    icon="mdi-help-circle-outline",
                    variant="text",
                    density="comfortable",
                    click="controls.active_page = 'welcome'",
                )

            v3.VSpacer()

            with v3.VBtnToggle(
                v_if="controls.data_loaded",
                v_model="controls.active_analysis",
                color="primary",
                multiple=True,
                mandatory=True,
                density="comfortable",
                variant="outlined",
                divided=True,
                classes="mr-2",
            ):
                TooltipButton(
                    "v[2]",
                    v_for="v, i in controls.available_analysis",
                    key="i",
                    icon=("v[1]",),
                    value=("v[0]",),
                )

            v3.VSpacer()

            v3.VDivider(vertical=True, classes="mx-2")

            TooltipButton(
                "controls.dark ? 'Light theme' : 'Dark theme'",
                icon=("controls.dark ? 'mdi-weather-sunny' : 'mdi-weather-night'",),
                variant="text",
                density="comfortable",
                classes="mr-2 rounded",
                click="controls.dark = !controls.dark",
            )

            v3.VProgressLinear(
                active=("trame__busy",),
                indeterminate=True,
                absolute=True,
                location="bottom",
                color="primary",
            )
