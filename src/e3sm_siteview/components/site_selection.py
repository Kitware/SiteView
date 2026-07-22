import math

from trame.decorators import change
from trame.widgets import client, html
from trame.widgets import vuetify3 as v3

from e3sm_siteview import constants, module


class CoordinatePreview(html.Div):
    def __init__(self, **_):
        super().__init__(classes="coord-preview mt-4")
        self.server.enable_module(module)

        self.state.site_marker_x = 0
        self.state.site_marker_y = 0
        self.state.site_marker_diameter = 0
        self.state.setdefault("data_regions", [])

        with self:
            with client.SizeObserver("site_map_size"):
                html.Div(
                    classes="data-region",
                    v_for="region, i in data_regions",
                    key="i",
                    style=(
                        "`left: ${region[0]}%;top:${region[1]}%;width:${region[2]}%;height:${region[3]}%;`",
                    ),
                )
                html.Div(classes="coord-equator")
                html.Div(classes="coord-meridian")
                html.Div(
                    classes="coord-radius",
                    style=(
                        "{ left: site_marker_x + '%', top: site_marker_y + '%', width: site_marker_diameter + 'px', height: site_marker_diameter + 'px' }",
                    ),
                )
                html.Div(
                    classes="coord-marker",
                    style=("{ left: site_marker_x + '%', top: site_marker_y + '%' }",),
                )

    @change("site_lat", "site_lon")
    def _update_marker(self, site_lat, site_lon, **_):
        self.state.site_marker_x = ((site_lon + 180) / 360) * 100
        self.state.site_marker_y = ((90 - site_lat) / 180) * 100

    @change("site_radius", "site_radius_unit", "site_map_size")
    def _update_radius(self, site_radius, site_radius_unit, site_map_size, **_):
        if not site_radius:
            site_radius = 0
        if site_map_size:
            size_width = site_map_size["size"]["width"]
            deg2px = float(size_width / 360)
            if site_radius_unit == "km":
                site_radius = float(site_radius) / 111.111  # convert to degree

            base = min(float(site_radius) * deg2px, size_width / 4)
            self.state.site_marker_diameter = int(0.5 + max(2 * base, 8))


class SiteSelection(html.Div):
    def __init__(self, next_fn, **_):
        super().__init__(classes="step-pane pa-6")
        self.server.enable_module(module)

        with self:
            with self.ctx.setup.provide_as("config"):
                with v3.VCol():
                    with v3.VSelect(
                        v_model=("site_selected", None),
                        items=("site_all", constants.SITES),
                        item_title="title",
                        item_value="value",
                        label="ARM User Facility",
                        prepend_inner_icon="mdi-domain",
                        variant="outlined",
                        density="comfortable",
                        clearable=True,
                    ):
                        with v3.Template(v_slot_item=" {props, item }"):
                            v3.VListItem(
                                v_bind="props",
                                subtitle=(
                                    "utils?.e3sm?.formatCoords(item?.raw?.lat, item?.raw?.lon)",
                                ),
                            )
                    html.Div(
                        "Coordinates",
                        classes="text-overline text-medium-emphasis mb-1",
                    )
                    with v3.VRow(dense=True):
                        with v3.VCol(cols="6"):
                            v3.VTextField(
                                v_model_number=("site_lat", 70),
                                type="number",
                                step="0.001",
                                label="Latitude",
                                suffix=("site_lat < 0 ? '°S':'°N'",),
                                variant="outlined",
                                density="comfortable",
                                rules=(
                                    "[(v) => (v >= -90 && v <= 90) || 'Latitude must be between -90 and 90']",
                                ),
                            )
                        with v3.VCol(cols="6"):
                            v3.VTextField(
                                v_model_number=("site_lon", 180),
                                type="number",
                                step="0.001",
                                label="Longitude",
                                suffix=("site_lon < 0 ? '°W':'°E'",),
                                variant="outlined",
                                density="comfortable",
                                rules=(
                                    "[(v) => (v >= -180 && v <= 180) || 'Longitude must be between -180 and 180']",
                                ),
                            )

                    html.Div(
                        "Region of Interest",
                        classes="text-overline text-medium-emphasis mb-1",
                    )
                    with v3.VRow(dense=True, align="top"):
                        with v3.VCol():
                            v3.VTextField(
                                v_model_number=("site_radius", 5),
                                type="number",
                                step="0.1",
                                min="0",
                                label="Radius",
                                prepend_inner_icon="mdi-radius-outline",
                                variant="outlined",
                                density="comfortable",
                                classes="pr-4",
                                rules=(
                                    """[
                                    (v) => (v >= 0) || 'Radius must be greater than or equal to 0',
                                    (v) => (v / (site_radius_unit === 'km' ? 111.111 : 1) < 90) || 'Radius must be smaller than 90° or 10 000 Km'
                                ]""",
                                ),
                            )
                        with v3.VBtnToggle(
                            v_model=("site_radius_unit", "deg"),
                            color="primary",
                            variant="outlined",
                            divided=True,
                            mandatory=True,
                            classes="mt-1 pr-4",
                            size="small",
                        ):
                            v3.VBtn("km", value="km", classes="text-none")
                            v3.VBtn("deg", value="deg", classes="text-none")

                        v3.VBtn(
                            "Load {{ config.n_cols }} column{{ config.n_cols > 1 && 's' || '' }}",
                            classes="text-none mt-1",
                            variant="flat",
                            color="primary",
                            size="large",
                            append_icon="mdi-chevron-right",
                            height=48,
                            click=next_fn,
                        )

                    CoordinatePreview()

    @change("site_selected")
    def _on_site_selected(self, site_selected, **_):
        lat_lon = constants.SITES_LAT_LON.get(site_selected)
        if lat_lon:
            self.state.site_lat = lat_lon[0]
            self.state.site_lon = lat_lon[1]

    @change("site_radius", "site_radius_unit")
    def _on_radius(self, site_radius, site_radius_unit, **_):
        if not site_radius:
            site_radius = 1

        self.ctx.setup.radius_deg = site_radius * (
            1.0 if site_radius_unit == "deg" else 111.111
        )

    @change("site_lat", "site_lon")
    def _on_lat_lon(self, site_lat, site_lon, site_selected, **_):
        self.ctx.setup.center = ((360 + float(site_lon)) % 360, float(site_lat), 0)
        if site_selected:
            lat_lon = constants.SITES_LAT_LON.get(site_selected)
            if (
                lat_lon is None
                or math.fabs(float(site_lat) - lat_lon[0]) > 0.001
                or math.fabs(float(site_lon) - lat_lon[1]) > 0.001
            ):
                self.state.site_selected = None
