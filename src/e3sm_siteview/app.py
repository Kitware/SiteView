from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import colormaps, dockview, html, plotly, rca
from trame.widgets import vuetify3 as v3

from e3sm_siteview import constants
from e3sm_siteview.assets import ASSETS
from e3sm_siteview.components import (
    field_selection,
    footer,
    header,
    site_selection,
    welcome,
)
from e3sm_siteview.viewer import create_viewers


class DialogTitle(v3.VCardTitle):
    """Setup dialog title, closable once data is loaded (needs "controls")"""

    def __init__(self, title):
        super().__init__(classes="d-flex align-center")
        with self:
            html.Span(title)
            v3.VSpacer()
            v3.VBtn(
                v_if="controls.data_loaded",
                icon="mdi-close",
                variant="text",
                density="comfortable",
                click="controls.active_page = 'viz'",
            )


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

        # Theme shared by vuetify (app) and dockview
        self.ctx.setup.watch(["dark"], self._on_theme_change, eager=True)

        with VAppLayout(
            self.server,
            fill_height=True,
            vuetify_config=constants.VUETIFY_CONFIG,
            theme=("siteview_theme",),
        ) as self.ui:
            with v3.VLayout():
                header.AppHeader()
                with self.ctx.setup.provide_as("controls"):
                    with v3.VDialog(
                        absolute=True,
                        model_value=("controls.active_page === 'welcome'",),
                        persistent=True,
                        scrollable=True,
                        max_width="640",
                    ):
                        welcome.Welcome(
                            "controls.active_page = controls.data_loaded ? 'viz' : 'site'"
                        )

                    with v3.VDialog(
                        absolute=True,
                        model_value=("controls.active_page === 'site'",),
                        persistent=True,
                        scrollable=True,
                    ):
                        with v3.VCard(rounded="lg"):
                            DialogTitle("Select your site location and region size")
                            v3.VDivider()
                            site_selection.SiteSelection(self._select_region)

                    with v3.VDialog(
                        absolute=True,
                        persistent=True,
                        model_value=("controls.active_page === 'fields'",),
                        scrollable=True,
                    ):
                        with v3.VCard(rounded="lg"):
                            DialogTitle("Select fields to load")
                            v3.VDivider()
                            field_selection.FieldSelection(self._load_fields)

                with v3.VMain():
                    dockview.DockView(
                        ctx_name="views_container",
                        theme=("siteview_dockview_theme",),
                    )
                footer.TimeControls()

    def _on_theme_change(self, dark):
        # Async watcher: flush the state explicitly
        with self.state:
            self.state.siteview_theme = "siteviewDark" if dark else "siteviewLight"
            self.state.siteview_dockview_theme = "Dark" if dark else "Light"

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
