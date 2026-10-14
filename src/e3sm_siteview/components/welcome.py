from trame.widgets import html
from trame.widgets import vuetify4 as v4

from e3sm_siteview import __version__ as app_version

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


class Welcome(v4.VCard):
    def __init__(self, next_fn, **_):
        super().__init__(rounded="lg")

        with self:
            with v4.VCardItem(classes="pa-6 pb-2"):
                with v4.Template(v_slot_prepend=True):
                    with v4.VAvatar(color="primary", size="48"):
                        v4.VIcon(icon="mdi-map-marker-radius", size="28")
                v4.VCardTitle(
                    f"Welcome to SiteView v{app_version}", classes="text-headline-small"
                )
                v4.VCardSubtitle(
                    "Explore E3SM simulation data around a site of interest"
                )
                with v4.Template(v_slot_append=True):
                    v4.VBtn(
                        icon="mdi-close",
                        variant="text",
                        density="comfortable",
                        click=next_fn,
                    )
            with v4.VCardText(classes="px-6"):
                html.P(
                    "Getting started only takes three steps:",
                    classes="text-body-large mb-4",
                )
                with v4.VList(lines="three", classes="py-0"):
                    for idx, step in enumerate(STEPS):
                        with v4.VListItem(classes="px-0"):
                            with v4.Template(v_slot_prepend=True):
                                with v4.VAvatar(
                                    color=step["color"], variant="tonal", classes="mr-2"
                                ):
                                    html.Span(
                                        f"{idx + 1}",
                                        classes="text-body-large font-weight-bold",
                                    )
                            with v4.VListItemTitle(classes="font-weight-medium"):
                                v4.VIcon(
                                    icon=step["icon"],
                                    color=step["color"],
                                    size="small",
                                    classes="mr-1",
                                )
                                html.Span(step["title"])
                            v4.VListItemSubtitle(step["text"], classes="text-wrap")

                v4.VDivider()
                with v4.VCardActions(classes="px-6 py-3"):
                    v4.VSpacer()
                    v4.VBtn(
                        "Getting started",
                        color="primary",
                        variant="flat",
                        append_icon="mdi-chevron-right",
                        click=next_fn,
                    )
