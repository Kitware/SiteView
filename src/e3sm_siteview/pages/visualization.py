from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client, dockview, vtk
from trame.widgets import vuetify3 as v3

from e3sm_siteview import components as sv_ui


class VisualizationPage(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # Deferred UI initialization
        vtk.initialize(self.server)

        self._build_ui()

    def _build_ui(self):
        with VAppLayout(self.server, fill_height=True) as self.ui:
            client.ClientTriggers(mounted=self._load_layout)
            with v3.VLayout():
                sv_ui.View3DTools()
                with v3.VMain():
                    dockview.DockView(ctx_name="views_container")

    def activate(self):
        self._build_ui()

    def _load_layout(self):
        for viewer in self.ctx.viewers.values():
            viewer.add_analysis("viz")


def main():
    app = VisualizationPage()
    app.server.start()


if __name__ == "__main__":
    main()
