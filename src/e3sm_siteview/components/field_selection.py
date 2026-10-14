from trame.widgets import html
from trame.widgets import vuetify4 as v4

from e3sm_siteview import constants, module


class FieldSelection(html.Div):
    def __init__(self, **_):
        super().__init__(classes="step-pane ")
        self.server.enable_module(module)

        with self, self.ctx.setup.provide_as("fields"):
            with html.Div(classes="px-6 pt-6"):
                v4.VTextField(
                    v_model=("fields_filter", ""),
                    placeholder="Search fields (name or description)",
                    prepend_inner_icon="mdi-magnify",
                    variant="outlined",
                    density="comfortable",
                    clearable=True,
                    hide_details=True,
                )

            with html.Div(classes="flex-fill px-6 py-3"):
                with v4.VExpansionPanels(
                    v_model=("fields_open_panels", [0, 1]),
                    multiple=True,
                    variant="accordion",
                ):
                    for group in constants.FIELD_GROUPS:
                        with v4.VExpansionPanel():
                            with v4.VExpansionPanelTitle(height="48px", static=True):
                                v4.VIcon(
                                    icon=group.icon,
                                    classes="mr-3",
                                    color=group.color,
                                )
                                html.Span(group.label, classes="font-weight-medium")
                                v4.VChip(
                                    f"{{{{fields.{group.state_name}.filter(v=>v.selected).length}}}} / {{{{ fields.{group.state_name}.length }}}}",  # FIXME
                                    size="x-small",
                                    variant="outlined",
                                    color=group.color,
                                    classes="ml-4",
                                )
                                v4.VSpacer()
                                v4.VBtn(
                                    "Select all",
                                    variant="text",
                                    v_on_click_stop_prevent=(
                                        self.updateSelection,
                                        f"['{group.state_name}', true, fields_filter]",
                                    ),
                                    classes="mr-2 text-none",
                                    density="compact",
                                )
                                v4.VBtn(
                                    "Clear",
                                    variant="text",
                                    v_on_click_stop_prevent=(
                                        self.updateSelection,
                                        f"['{group.state_name}', false, fields_filter]",
                                    ),
                                    classes="mr-2 text-none",
                                    density="compact",
                                )

                            with v4.VExpansionPanelText(classes="border-t"):
                                with v4.VRow(density="compact"):
                                    with v4.VCol(
                                        v_for=f"field in fields.{group.state_name}",
                                        key="field.name",
                                        cols=12,
                                        sm=6,
                                        md=4,
                                        xl=3,
                                        v_show="utils.e3sm.match(field, fields_filter)",
                                    ):
                                        with v4.VCheckbox(
                                            v_model="field.selected",
                                            density="compact",
                                            hide_details=True,
                                        ):
                                            with v4.Template(v_slot_label=True):
                                                with html.Div():
                                                    with html.Div(
                                                        "{{ field.name }}",
                                                        classes="font-weight-medium",
                                                    ):
                                                        html.Span(
                                                            "({{ field.units }})",
                                                            classes="text-body-small text-medium-emphasis",
                                                        )
                                                    html.Div(
                                                        "{{ field.description }}",
                                                        classes="text-body-small text-medium-emphasis",
                                                        style="line-height:1.2;",
                                                    )

    def updateSelection(self, group_key, select, query):
        listing = getattr(self.ctx.setup, group_key)
        for item in listing:
            if query:
                if query.lower() in item.name.lower():
                    item.selected = select
            else:
                item.selected = select
