from trame.widgets import html
from trame.widgets import vuetify4 as v4

from e3sm_siteview.components import field_selection, site_selection
from e3sm_siteview.components.header import N_FIELDS

IS_SITE = "controls.active_page === 'site'"
IS_FIELDS = "controls.active_page === 'fields'"
FIRST_RUN = "!controls.data_loaded"
CAN_APPLY = f"({IS_SITE} && controls.n_cols > 0) || ({IS_FIELDS} && ({N_FIELDS}) > 0)"


class SetupDialog(v4.VDialog):
    """Site and fields selection (needs the "controls" provider)

    First run: stepper (site -> fields) with Back / Next / Load.
    Once data is loaded: edit a single setting with Cancel / Apply.
    """

    def __init__(self, apply_fn, cancel_fn):
        super().__init__(
            absolute=True,
            persistent=True,
            scrollable=True,
            model_value=(f"{IS_SITE} || {IS_FIELDS}",),
        )

        with self, v4.VCard(rounded="lg"):
            # First run: progress
            with v4.VStepper(
                v_if=FIRST_RUN,
                model_value=("controls.active_page",),
                update_modelValue="controls.active_page = $event",
                flat=True,
                bg_color="transparent",
            ):
                with v4.VStepperHeader(classes="elevation-0 justify-center"):
                    v4.VStepperItem(
                        value="site",
                        title="Site & region",
                        subtitle=(
                            "`${controls.n_cols} column${controls.n_cols > 1 ? 's' : ''}`",
                        ),
                        icon="mdi-map-marker-radius",
                        complete=(IS_FIELDS,),
                        editable=True,
                        color="primary",
                    )
                    # Keep the steps close together on wide screens
                    v4.VDivider(style="max-width: 240px;")
                    v4.VStepperItem(
                        value="fields",
                        title="Fields",
                        subtitle=(f"`${{{N_FIELDS}}} selected`",),
                        icon="mdi-format-list-checks",
                        editable=("controls.n_cols > 0",),
                        color="primary",
                    )

            # Edit: single setting
            with v4.VCardTitle(v_else=True, classes="d-flex align-center"):
                v4.VIcon(
                    icon=(
                        f"{IS_SITE} ? 'mdi-map-marker-radius' : 'mdi-format-list-checks'",
                    ),
                    color="primary",
                    classes="mr-2",
                )
                html.Span(
                    f"{{{{ {IS_SITE} ? 'Site location and region' : 'Fields to load' }}}}"
                )
                v4.VSpacer()
                v4.VBtn(
                    icon="mdi-close",
                    variant="text",
                    density="comfortable",
                    click=cancel_fn,
                )

            v4.VDivider()
            with v4.Template(v_if=IS_SITE):
                site_selection.SiteSelection()
            with v4.Template(v_if=IS_FIELDS):
                field_selection.FieldSelection()
            v4.VDivider()

            with v4.VCardActions(classes="px-6 py-3"):
                v4.VBtn(
                    "Back",
                    v_if=f"{FIRST_RUN} && {IS_FIELDS}",
                    prepend_icon="mdi-chevron-left",
                    variant="text",
                    classes="text-none",
                    click="controls.active_page = 'site'",
                )
                v4.VBtn(
                    "Cancel",
                    v_if="controls.data_loaded",
                    variant="text",
                    classes="text-none",
                    click=cancel_fn,
                )
                v4.VSpacer()
                v4.VBtn(
                    (
                        "{{ controls.data_loaded ? 'Apply'"
                        f" : {IS_SITE} ? 'Select fields' : 'Load ' + ({N_FIELDS}) + ' field' + (({N_FIELDS}) > 1 ? 's' : '') }}}}"
                    ),
                    color="primary",
                    variant="flat",
                    classes="text-none px-4",
                    append_icon=(
                        "controls.data_loaded ? 'mdi-check' : 'mdi-chevron-right'",
                    ),
                    disabled=(f"!({CAN_APPLY})",),
                    click=apply_fn,
                )
