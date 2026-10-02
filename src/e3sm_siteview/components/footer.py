from trame.widgets import html
from trame.widgets import vuetify3 as v3


def TooltipButton(tooltip, **kwargs):
    return v3.VBtn(v_tooltip_top=f"{tooltip}", **kwargs)


class GeneralControls(v3.VFooter):
    def __init__(self):
        super().__init__(app=True)

        with self, self.ctx.setup.provide_as("controls"):
            with v3.VBtnToggle(
                v_model="controls.active_page",
                color="primary",
                density="comfortable",
                border=True,
                divided=True,
                classes="mr-4",
                mandatory=True,
            ):
                TooltipButton(
                    "'Site selection'",
                    icon="mdi-map-marker-radius",
                    value="site",
                )
                TooltipButton(
                    "'Fields selection'",
                    icon="mdi-format-list-checks",
                    value="fields",
                )
                TooltipButton(
                    "'Visualization'",
                    icon="mdi-lightbulb-on-outline",
                    value="viz",
                )

            with html.Div(
                v_if="controls.data_loaded", classes="d-flex flex-fill align-center"
            ):
                with v3.VBtnToggle(
                    v_model="controls.active_analysis",
                    color="primary",
                    multiple=True,
                    density="comfortable",
                    border=True,
                    divided=True,
                    classes="mr-4",
                    mandatory=True,
                ):
                    TooltipButton(
                        "v[2]",
                        v_for="v, i in controls.available_analysis",
                        key="i",
                        icon=("v[1]",),
                        value=("v[0]",),
                    )

                with v3.VBtnToggle(
                    v_model="controls.active_viz",
                    color="primary",
                    multiple=True,
                    density="comfortable",
                    border=True,
                    divided=True,
                    classes="mr-4",
                ):
                    TooltipButton("'Clouds'", icon="mdi-weather-cloudy", value="cloud")
                    TooltipButton(
                        "'Vertical scaling'",
                        icon="mdi-arrow-expand-vertical",
                        value="zscale",
                    )
                    # TooltipButton("Surface", icon="mdi-layers-outline", value="surface")
                    TooltipButton(
                        "'Volume rendering'", icon="mdi-cube-outline", value="volume"
                    )
                    TooltipButton(
                        "'Horizontal slice'", icon="mdi-altimeter", value="hslice"
                    )
                    TooltipButton(
                        "'Vertical slice'", icon="mdi-flip-horizontal", value="vslice"
                    )
                    TooltipButton(
                        "'Find data'", icon="mdi-magnify-scan", value="find_data"
                    )
                    TooltipButton(
                        "'Histogram'", icon="mdi-chart-histogram", value="histogram"
                    )
                    TooltipButton("'Column Cropping'", icon="mdi-sort", value="column")
                    TooltipButton(
                        "'Probes'", icon="mdi-map-marker-plus", value="probes"
                    )

                with v3.VBtnToggle(
                    density="comfortable",
                    border=True,
                    divided=True,
                ):
                    TooltipButton(
                        "'First time step'",
                        icon="mdi-step-backward-2",
                        click="controls.time_index = 0",
                    )
                    TooltipButton(
                        "'Previous time step'",
                        icon="mdi-step-backward",
                        click="controls.time_index > 0 && controls.time_index--",
                    )
                    TooltipButton(
                        "'Stop animation'",
                        icon="mdi-stop",
                        v_if="controls.time_animating",
                        click="controls.time_animating = false",
                    )
                    TooltipButton(
                        "'Play animation'",
                        icon="mdi-play",
                        v_else=True,
                        click="controls.time_animating = true",
                    )
                    TooltipButton(
                        "'Next time step'",
                        icon="mdi-step-forward",
                        click="controls.time_index < controls.time_index_max && controls.time_index++",
                    )
                    TooltipButton(
                        "'Last time step'",
                        icon="mdi-step-forward-2",
                        click="controls.time_index = controls.time_index_max",
                    )
                v3.VLabel(
                    "{{controls.time_value}}",
                    style="width: 50px;",
                    classes="mx-2 d-block text-center",
                )
                v3.VSlider(
                    v_model="controls.time_index",
                    min=0,
                    max=("controls.time_index_max",),
                    step=1,
                    density="compact",
                    hide_details=True,
                )
