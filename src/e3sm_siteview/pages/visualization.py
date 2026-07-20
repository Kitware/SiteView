from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client, dockview, paraview
from trame.widgets import vuetify3 as v3


class VisualizationPage(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # Deferred UI initialization
        paraview.initialize(self.server)

        self._build_ui()

    def _build_ui(self):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            client.ClientTriggers(mounted=self._load_layout)
            with v3.VLayout():
                with v3.VMain():
                    dockview.DockView(ctx_name="views_container")
                with v3.VFooter(app=True):
                    with self.ctx.setup.provide_as("controls"):
                        with v3.VBtnToggle(
                            v_model="controls.active_viz",
                            color="primary",
                            multiple=True,
                            density="comfortable",
                            border=True,
                            divided=True,
                        ):
                            v3.VBtn(icon="mdi-weather-cloudy", value="cloud")
                            v3.VBtn(icon="mdi-layers-outline", value="surface")
                            v3.VBtn(icon="mdi-cube-outline", value="volume")
                            v3.VBtn(icon="mdi-flip-vertical", value="slice")
                            v3.VBtn(icon="mdi-magnify-scan", value="find-data")
                            v3.VBtn(icon="mdi-sort", value="crop-column")
                            v3.VBtn(icon="mdi-map-marker-plus", value="probes")

                        v3.VDivider(vertical=True, classes="mx-2")

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
                            style="width: 200px;",
                            classes="mx-2",
                        )
                        v3.VSlider(
                            v_model="controls.time_index",
                            min=0,
                            max=("controls.time_index_max",),
                            step=1,
                            density="compact",
                            hide_details=True,
                        )

    def activate(self):
        self._build_ui()

    def _load_layout(self):
        for viewer in self.ctx.viewers.values():
            viewer.add_analysis("viz")


def main():
    from trame.app import get_server  # noqa: PLC0415

    from e3sm_siteview.viewer import create_viewers  # noqa: PLC0415

    server = get_server()
    create_viewers(server)

    app = VisualizationPage(server)
    app.server.start()


if __name__ == "__main__":
    main()
