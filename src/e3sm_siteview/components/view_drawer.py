from trame.widgets import html
from trame.widgets import vuetify3 as v3

from e3sm_siteview import __version__ as app_version
from e3sm_siteview.components import css, tools


class View3DTools(v3.VNavigationDrawer):
    def __init__(self, reset_camera=None):
        super().__init__(
            permanent=True,
            rail=("compact_drawer", True),
            width=253,
            style="transform: none;",
        )

        with self:
            with html.Div(style=css.NAV_BAR_TOP):
                with v3.VList(
                    density="compact",
                    nav=True,
                    select_strategy="independent",
                    v_model_selected=(
                        "active_tools",
                        ["load-data", "select-slice-time", "animation-controls"],
                    ),
                ):
                    tools.AppLogo()
                    tools.ResetCamera(click=reset_camera)

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.StateImportExport()
                    tools.OpenFile()

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.FieldSelection()
                    tools.DataSelection()
                    tools.Animation()

                    v3.VDivider(classes="my-1")  # ---------------------

                    tools.LayoutManagement()
                    tools.MapProjection()
                    tools.Cropping()

                    v3.VDivider(classes="my-1")  # ---------------------

                    # dev add-on ui reload
                    if self.server.hot_reload:
                        v3.VDivider(classes="my-1")  # ---------------------
                        tools.ActionButton(
                            compact="compact_drawer",
                            title="Refresh UI",
                            icon="mdi-database-refresh-outline",
                            click=self.ctrl.on_server_reload,
                        )

            with html.Div(style=css.NAV_BAR_BOTTOM):
                v3.VDivider()
                v3.VLabel(
                    f"{app_version}",
                    classes="text-center text-caption d-block text-wrap",
                )
