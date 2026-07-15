from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import dockview
from trame.widgets import vuetify3 as v3

from e3sm_siteview import components as sv_ui


class E3smSiteView(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # --hot-reload arg optional logic
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        self._build_ui()

    def _build_ui(self, *_args, **_kwargs):
        self.state.trame__title = "E3SM Site View"
        with VAppLayout(self.server, fill_height=True) as self.ui:
            with v3.VLayout():
                sv_ui.View3DTools()
                with v3.VMain():
                    dockview.DockView(ctx_name="views_container")


def main(server=None, **kwargs):
    app = E3smSiteView(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
