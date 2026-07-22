from trame.widgets import vuetify3 as v3


class GeneralControls(v3.VFooter):
    def __init__(self):
        super().__init__(app=True)

        with self, self.ctx.setup.provide_as("controls"):
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
                v3.VBtn(
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
                v3.VBtn(icon="mdi-weather-cloudy", value="cloud")
                # v3.VBtn(icon="mdi-layers-outline", value="surface")
                v3.VBtn(icon="mdi-cube-outline", value="volume")
                v3.VBtn(icon="mdi-altimeter", value="slice")  # mdi-flip-vertical
                v3.VBtn(icon="mdi-magnify-scan", value="find_data")
                v3.VBtn(icon="mdi-sort", value="column")
                v3.VBtn(icon="mdi-map-marker-plus", value="probes")

            with v3.VBtnToggle(
                density="comfortable",
                border=True,
                divided=True,
            ):
                v3.VBtn(
                    icon="mdi-step-backward-2",
                    click="controls.time_index = 0",
                )
                v3.VBtn(
                    icon="mdi-step-backward",
                    click="controls.time_index > 0 && controls.time_index--",
                )
                v3.VBtn(
                    icon="mdi-stop",
                    v_if="controls.time_animating",
                    click="controls.time_animating = false",
                )
                v3.VBtn(
                    icon="mdi-play",
                    v_else=True,
                    click="controls.time_animating = true",
                )
                v3.VBtn(
                    icon="mdi-step-forward",
                    click="controls.time_index < controls.time_index_max && controls.time_index++",
                )
                v3.VBtn(
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
