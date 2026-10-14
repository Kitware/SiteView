from trame.widgets import html
from trame.widgets import vuetify3 as v3


def TooltipButton(tooltip, **kwargs):
    return v3.VBtn(v_tooltip_top=f"{tooltip}", **kwargs)


class TimeControls(v3.VFooter):
    """Media player like time navigation"""

    def __init__(self):
        super().__init__(app=True, border="t", classes="py-1")

        with self, self.ctx.setup.provide_as("controls"):
            with html.Div(classes="d-flex align-center ga-1"):
                TooltipButton(
                    "'First time step'",
                    icon="mdi-skip-previous",
                    variant="text",
                    density="comfortable",
                    classes="rounded",
                    click="controls.time_index = 0",
                )
                TooltipButton(
                    "'Previous time step (←)'",
                    icon="mdi-step-backward",
                    variant="text",
                    density="comfortable",
                    classes="rounded",
                    click="controls.time_index > 0 && controls.time_index--",
                )
                TooltipButton(
                    "controls.time_animating ? 'Pause animation (Space)' : 'Play animation (Space)'",
                    icon=("controls.time_animating ? 'mdi-pause' : 'mdi-play'",),
                    color="primary",
                    variant="flat",
                    density="comfortable",
                    classes="rounded",
                    click="controls.time_animating = !controls.time_animating",
                )
                TooltipButton(
                    "'Next time step (→)'",
                    icon="mdi-step-forward",
                    variant="text",
                    density="comfortable",
                    classes="rounded",
                    click="controls.time_index < controls.time_index_max && controls.time_index++",
                )
                TooltipButton(
                    "'Last time step'",
                    icon="mdi-skip-next",
                    variant="text",
                    density="comfortable",
                    classes="rounded",
                    click="controls.time_index = controls.time_index_max",
                )

            html.Div(
                "Step {{ controls.time_index + 1 }} / {{ controls.time_index_max + 1 }}",
                classes="text-body-2 text-medium-emphasis text-no-wrap mx-4",
                style="min-width: 7rem;",
            )
            v3.VSlider(
                v_model="controls.time_index",
                min=0,
                max=("controls.time_index_max",),
                step=1,
                density="compact",
                hide_details=True,
                color="primary",
                classes="mr-2",
            )
