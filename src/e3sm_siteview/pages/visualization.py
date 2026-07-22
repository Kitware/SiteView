from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client, colormaps, dockview, plotly, vtk
from trame.widgets import vuetify3 as v3

from e3sm_siteview.components import footer


class VisualizationPage(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # Deferred UI initialization
        vtk.initialize(self.server)
        colormaps.initialize(self.server)
        plotly.initialize(self.server)

        self._build_ui()

    def _build_ui(self):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            client.ClientTriggers(mounted=self._load_layout)
            with v3.VLayout():
                with v3.VMain():
                    dockview.DockView(ctx_name="views_container", theme="Light")
                footer.GeneralControls()

    def activate(self):
        self._build_ui()

    def _load_layout(self):
        for viewer in self.ctx.viewers.values():
            viewer.add_analysis("viz", "time")


def main():
    from trame.app import get_server  # noqa: PLC0415

    from e3sm_siteview.viewer import create_viewers  # noqa: PLC0415

    server = get_server()
    create_viewers(server)

    app = VisualizationPage(server)
    app.server.start()


if __name__ == "__main__":
    main()
