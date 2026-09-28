from trame.widgets import html
from trame.widgets import vuetify3 as v3

STEPS = [
    {
        "title": "Select your site location and region size",
        "text": "Pick the site of interest on the map and adjust the radius to define the region of data to extract around it.",
        "icon": "mdi-map-marker-radius",
        "color": "primary",
    },
    {
        "title": "Select the set of fields to load",
        "text": "Browse or search the available variables and choose the ones relevant to your analysis.",
        "icon": "mdi-format-list-checks",
        "color": "teal",
    },
    {
        "title": "Explore the data and gain insight",
        "text": "Use the 3D view, column heatmaps and time charts to investigate how fields evolve in space and time.",
        "icon": "mdi-chart-box-outline",
        "color": "deep-orange",
    },
]


class Welcome(v3.VCard):
    def __init__(self, next_fn, **_):
        super().__init__(rounded="lg")

        with self:
            with v3.VCardItem(classes="pa-6 pb-2"):
                with v3.Template(v_slot_prepend=True):
                    with v3.VAvatar(color="primary", size="48"):
                        v3.VIcon(icon="mdi-map-marker-radius", size="28")
                v3.VCardTitle("Welcome to SiteView", classes="text-h5")
                v3.VCardSubtitle(
                    "Explore E3SM simulation data around a site of interest"
                )
                with v3.Template(v_slot_append=True):
                    v3.VBtn(
                        icon="mdi-close",
                        variant="text",
                        density="comfortable",
                        click=next_fn,
                    )
            with v3.VCardText(classes="px-6"):
                html.P(
                    "Getting started only takes three steps:",
                    classes="text-body-1 mb-4",
                )
                with v3.VList(lines="three", classes="py-0"):
                    for idx, step in enumerate(STEPS):
                        with v3.VListItem(classes="px-0"):
                            with v3.Template(v_slot_prepend=True):
                                with v3.VAvatar(
                                    color=step["color"], variant="tonal", classes="mr-2"
                                ):
                                    html.Span(
                                        f"{idx + 1}",
                                        classes="text-subtitle-1 font-weight-bold",
                                    )
                            with v3.VListItemTitle(classes="font-weight-medium"):
                                v3.VIcon(
                                    icon=step["icon"],
                                    color=step["color"],
                                    size="small",
                                    classes="mr-1",
                                )
                                html.Span(step["title"])
                            v3.VListItemSubtitle(step["text"], classes="text-wrap")

                v3.VDivider()
                with v3.VCardActions(classes="px-6 py-3"):
                    v3.VSpacer()
                    v3.VBtn(
                        "Getting started",
                        color="primary",
                        variant="flat",
                        append_icon="mdi-chevron-right",
                        click=next_fn,
                    )
