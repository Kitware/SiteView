from trame.app import TrameApp, asynchronous
from trame.ui.vuetify4 import VAppLayout
from trame.widgets import colormaps, dockview, html, plotly, rca
from trame.widgets import vuetify4 as v4

from e3sm_siteview import constants
from e3sm_siteview.assets import ASSETS
from e3sm_siteview.components import footer, header, setup, shortcuts, welcome
from e3sm_siteview.viewer import create_viewers

SITE_KEYS = ("site_selected", "site_lat", "site_lon", "site_radius", "site_radius_unit")


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

        # Values to restore when canceling a setup edit
        self._setup_snapshot = None
        # Message of the overlay shown while (re)loading data, hidden when empty
        self.state.siteview_loading = ""
        self.ctx.setup.watch(["active_page"], self._on_page_change)

        with VAppLayout(
            self.server,
            fill_height=True,
            vuetify_config=constants.VUETIFY_CONFIG,
            theme=("siteview_theme",),
        ) as self.ui:
            with v4.VLayout():
                header.AppHeader()
                with self.ctx.setup.provide_as("controls"):
                    shortcuts.KeyboardShortcuts(self.ctrl.reset_camera)
                    with v4.VDialog(
                        absolute=True,
                        model_value=("controls.active_page === 'welcome'",),
                        persistent=True,
                        scrollable=True,
                        max_width="640",
                    ):
                        welcome.Welcome(
                            "controls.active_page = controls.data_loaded ? 'viz' : 'site'"
                        )

                    setup.SetupDialog(self._apply_setup, self._cancel_setup)

                with v4.VMain(classes="position-relative"):
                    dockview.DockView(
                        ctx_name="views_container",
                        theme=("siteview_dockview_theme",),
                    )
                    LoadingOverlay()
                footer.TimeControls()

    def _on_theme_change(self, dark):
        # Async watcher: flush the state explicitly
        with self.state:
            self.state.siteview_theme = "siteviewDark" if dark else "siteviewLight"
            self.state.siteview_dockview_theme = "Dark" if dark else "Light"

    def _on_page_change(self, active_page):
        if (
            active_page in ("site", "fields")
            and self.ctx.setup.data_loaded
            and self._setup_snapshot is None
        ):
            self._setup_snapshot = {
                "site": {k: self.state[k] for k in SITE_KEYS},
                "fields": {v.name: v.selected for v in self._variables()},
            }

    def _variables(self):
        return [*self.ctx.setup.variables_2d, *self.ctx.setup.variables_3d]

    def _apply_setup(self):
        self._setup_snapshot = None
        setup = self.ctx.setup
        if setup.active_page == "site" and not setup.data_loaded:
            setup.active_page = "fields"
            return

        if setup.active_page == "site":
            self.state.siteview_loading = "Updating region"
        else:
            n_fields = sum(v.selected for v in self._variables())
            self.state.siteview_loading = (
                f"Loading {n_fields} field{'s' if n_fields > 1 else ''}"
            )
        setup.active_page = "viz"
        asynchronous.create_task(self._load_data())

    def _cancel_setup(self):
        snapshot, self._setup_snapshot = self._setup_snapshot, None
        if snapshot:
            self.state.update(snapshot["site"])
            for v in self._variables():
                selected = snapshot["fields"].get(v.name, v.selected)
                if v.selected != selected:
                    v.selected = selected
        self.ctx.setup.active_page = "viz"

    async def _load_data(self):
        # Let the client show the overlay before blocking on IO
        await self.server.network_completion
        with self.state:
            try:
                if not self.ctx.setup.data_loaded:
                    list_of_analysis = [a[0] for a in self.ctx.setup.available_analysis]
                    for viewer in self.ctx.viewers.values():
                        viewer.add_analysis(*list_of_analysis)
                    self.ctx.setup.data_loaded = True
                else:
                    self.refresh_analyses_data()
            finally:
                self.state.siteview_loading = ""

    def refresh_analyses_data(self):
        for viewer in self.ctx.viewers.values():
            for analysis in viewer.analyses:
                analysis.refresh_data()


class LoadingOverlay(v4.VOverlay):
    """Blocks the analyses while data is (re)loaded"""

    def __init__(self):
        super().__init__(
            model_value=("!!siteview_loading",),
            contained=True,
            persistent=True,
            no_click_animation=True,
            classes="align-center justify-center",
        )
        with self, v4.VCard(classes="sv-float d-flex align-center ga-3 px-5 py-3"):
            v4.VProgressCircular(indeterminate=True, color="primary", size=24, width=3)
            html.Span("{{ siteview_loading }}…", classes="text-body-medium")


def main(server=None, **kwargs):
    app = E3smSiteView(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
