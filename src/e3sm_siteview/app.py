from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import colormaps, dockview, plotly, rca
from trame.widgets import vuetify3 as v3

from e3sm_siteview.assets import ASSETS
from e3sm_siteview.components import field_selection, footer, site_selection, welcome
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

        # Deferred UI initialization
        rca.initialize(self.server)
        colormaps.initialize(self.server)
        plotly.initialize(self.server)

        with VAppLayout(self.server, fill_height=True) as self.ui:
            with v3.VLayout():
                with self.ctx.setup.provide_as("controls"):
                    with v3.VDialog(
                        absolute=True,
                        model_value=("controls.active_page === 'welcome'",),
                        persistent=True,
                        scrollable=True,
                        max_width="640",
                    ):
                        welcome.Welcome("controls.active_page = 'site'")

                    with v3.VDialog(
                        absolute=True,
                        model_value=("controls.active_page === 'site'",),
                        persistent=True,
                        scrollable=True,
                    ):
                        with v3.VCard(rounded="lg"):
                            v3.VCardTitle("Select your site location and region size")
                            v3.VDivider()
                            site_selection.SiteSelection(self._select_region)

                    with v3.VDialog(
                        absolute=True,
                        persistent=True,
                        model_value=("controls.active_page === 'fields'",),
                        scrollable=True,
                    ):
                        with v3.VCard(rounded="lg"):
                            v3.VCardTitle("Select fields to load")
                            v3.VDivider()
                            field_selection.FieldSelection(self._load_fields)

                with v3.VMain():
                    dockview.DockView(ctx_name="views_container", theme="Light")
                footer.GeneralControls()

    def _select_region(self):
        if not self.ctx.setup.data_loaded:
            self.ctx.setup.active_page = "fields"
        else:
            self.refresh_analyses_data()
            self.ctx.setup.active_page = "viz"

    def _load_fields(self):
        if not self.ctx.setup.data_loaded:
            self._first_load = False
            list_of_analysis = [a[0] for a in self.ctx.setup.available_analysis]
            for viewer in self.ctx.viewers.values():
                viewer.add_analysis(*list_of_analysis)

            self.ctx.setup.data_loaded = True
        else:
            self.refresh_analyses_data()

        self.ctx.setup.active_page = "viz"

    def refresh_analyses_data(self):
        for viewer in self.ctx.viewers.values():
            for analysis in viewer.analyses:
                analysis.refresh_data()


def main(server=None, **kwargs):
    app = E3smSiteView(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
