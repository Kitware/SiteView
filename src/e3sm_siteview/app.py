from pathlib import Path
from types import SimpleNamespace

from trame.app import TrameApp

from e3sm_siteview import pages
from e3sm_siteview.analysis import load_all_analysis
from e3sm_siteview.cli import configure_and_parse
from e3sm_siteview.viewer import E3SMAnalyser


class E3smSiteView(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # Tab title
        self.state.trame__title = "E3SM Site View"

        # --hot-reload arg optional logic
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        args = configure_and_parse(self.server.cli)
        load_all_analysis()
        self.ctx.viewers = {}

        # debug
        connectivity_file = Path(args.cf).resolve()
        for data_file in args.df:
            viewer = E3SMAnalyser(
                self.server,
                connectivity_file,
                Path(data_file).resolve(),
            )
            self.ctx.viewers[viewer.name] = viewer

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
