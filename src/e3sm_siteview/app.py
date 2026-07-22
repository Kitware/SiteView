from types import SimpleNamespace

from trame.app import TrameApp

from e3sm_siteview import pages
from e3sm_siteview.assets import ASSETS
from e3sm_siteview.viewer import create_viewers


class E3smSiteView(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # Tab title
        self.state.trame__title = "E3SM Site View"
        self.state.trame__favicon = ASSETS.icon

        # --hot-reload arg optional logic
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        create_viewers(self.server)

        self.ctx.pages = SimpleNamespace(
            fields=pages.FieldSelectionPage(self.server),
            viz=pages.VisualizationPage(self.server),
            site=pages.SiteSelectionPage(self.server),
        )


def main(server=None, **kwargs):
    app = E3smSiteView(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
