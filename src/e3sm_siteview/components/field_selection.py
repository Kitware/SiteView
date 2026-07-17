from trame.widgets import html
from trame.widgets import vuetify3 as v3

from e3sm_siteview import constants, module


class FieldSelection(html.Div):
    def __init__(self, next_fn, **_):
        super().__init__(classes="step-pane ")
        self.server.enable_module(module)

        self.state.field_surface = [
            {**f, "selected": False} for f in constants.FIELDS_METADATA.values()
        ]
        self.state.field_midpoints = [
            {**f, "selected": False} for f in constants.FIELDS_METADATA.values()
        ]

        with self:
            with html.Div(classes="px-6 pt-6 d-flex align-center ga-2"):
                v3.VTextField(
                    v_model=("fields_filter", ""),
                    placeholder="Search fields (name or description)",
                    prepend_inner_icon="mdi-magnify",
                    variant="outlined",
                    density="comfortable",
                    clearable=True,
                    hide_details=True,
                )
                v3.VBtn(
                    "Load ({{ 5 }} + {{ 6 }})",
                    classes="text-none",
                    variant="flat",
                    color="primary",
                    size="large",
                    append_icon="mdi-chevron-right",
                    height=48,
                    click=next_fn,
                )
            with html.Div(classes="flex-fill px-6 py-3"):
                with v3.VExpansionPanels(
                    v_model=("fields_open_panels", [0, 1]),
                    multiple=True,
                    variant="accordion",
                ):
                    for group in constants.FIELD_GROUPS:
                        with v3.VExpansionPanel():
                            with v3.VExpansionPanelTitle(height="48px", static=True):
                                v3.VIcon(
                                    icon=group.icon, classes="mr-3", color=group.color
                                )
                                html.Span(group.label, classes="font-weight-medium")
                                v3.VChip(
                                    "1 / 10",  # FIXME
                                    size="x-small",
                                    variant="outlined",
                                    color=group.color,
                                    classes="ml-4",
                                )
                                v3.VSpacer()
                                v3.VBtn(
                                    "Select all",
                                    variant="text",
                                    v_on_click_stop_prevent=(
                                        self.updateSelection,
                                        f"['{group.key}', true]",
                                    ),
                                    classes="mr-2 text-none",
                                    density="compact",
                                )
                                v3.VBtn(
                                    "Clear",
                                    variant="text",
                                    v_on_click_stop_prevent=(
                                        self.updateSelection,
                                        f"['{group.key}', false]",
                                    ),
                                    classes="mr-2 text-none",
                                    density="compact",
                                )

                            with v3.VExpansionPanelText(classes="border-t"):
                                with v3.VRow(dense=True):
                                    with v3.VCol(
                                        v_for=f"field in {group.state_name}",
                                        key="field.name",
                                        cols=12,
                                        sm=6,
                                        md=4,
                                        xl=3,
                                        v_show="utils.e3sm.match(field, fields_filter)",
                                    ):
                                        with v3.VCheckbox(
                                            v_model="field.selected",
                                            density="compact",
                                            hide_details=True,
                                        ):
                                            with v3.Template(v_slot_label=True):
                                                with html.Div():
                                                    with html.Div(
                                                        "{{ field.name }}",
                                                        classes="font-weight-medium",
                                                    ):
                                                        html.Span(
                                                            "({{ field.units }})",
                                                            classes="text-caption text-medium-emphasis",
                                                        )
                                                    html.Div(
                                                        "{{ field.description }}",
                                                        classes="text-caption text-medium-emphasis",
                                                        style="line-height:1.2;",
                                                    )

    def updateSelection(self, group_key, select):
        print("toggle selection for", group_key, select)
