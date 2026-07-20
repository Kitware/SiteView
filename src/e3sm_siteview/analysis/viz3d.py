import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from paraview import simple
from trame.app import TrameComponent
from trame.ui.html import DivLayout
from trame.widgets import html
from trame.widgets import paraview as pvw
from trame.widgets import vuetify3 as v3

from e3sm_siteview.analysis import ANALYSIS_ID, register_analysis

NAME = "viz"


class Viz3D(TrameComponent):
    def __init__(self, server, reader):
        super().__init__(server)
        self._id = next(ANALYSIS_ID)
        self._reader = reader
        self._subscriptions = []
        self._setup_pv(reader)
        self._build_ui()

    @property
    def name(self):
        return self._id

    def _setup_pv(self, reader):
        self.view = simple.CreateRenderView()
        self.view.GetRenderWindow().OffScreenRenderingOn()
        self.representation_surface = simple.Show(
            simple.OutputPort(reader, 0),
            self.view,
        )
        self.representation_volume = simple.Show(
            simple.OutputPort(reader, 1),
            self.view,
            Scale=[1.0, 1.0, 0.1],
            Visibility=0,
        )

        # Attach listeners
        self._subscriptions.append(
            self.ctx.setup.watch(["active_viz"], self._on_volume_change)
        )
        self._subscriptions.append(
            self.ctx.setup.volume.watch(["color_by"], self._on_volume_change)
        )
        self._subscriptions.append(
            self.ctx.setup.watch(["active_viz"], self._on_surface_change)
        )
        self._subscriptions.append(
            self.ctx.setup.surface.watch(["color_by"], self._on_surface_change)
        )

    def _on_surface_change(self, *_):
        self.representation_surface.Visibility = "surface" in self.ctx.setup.active_viz
        self.representation_surface.ColorBy(("CELLS", self.ctx.setup.surface.color_by))
        self.representation_surface.RescaleTransferFunctionToDataRange(False, True)
        self.html_view.update()

    def _on_volume_change(self, *_):
        self.representation_volume.Visibility = "volume" in self.ctx.setup.active_viz
        self.representation_volume.ColorBy(("CELLS", self.ctx.setup.volume.color_by))
        self.representation_volume.RescaleTransferFunctionToDataRange(False, True)
        self.html_view.update()

    def _build_ui(self):
        with DivLayout(self.server, self.name, classes="h-100") as self.ui:
            with html.Div(
                style="position:absolute;top:0;left:0;width:100%;height:100%;"
            ):
                self.html_view = pvw.VtkRemoteView(
                    self.view,
                    interactive_ratio=1,
                )
                self.ctrl.render.add(self.html_view.update)
                self.ctrl.reset_camera.add(self.html_view.reset_camera)
                with v3.VCard(
                    style="position:absolute;right:1rem;top:1rem;z-index:100;"
                ):
                    v3.VBtn(
                        icon="mdi-crop-free",
                        classes="rounded",
                        click=self.html_view.reset_camera,
                    )
                with self.ctx.setup.provide_as("controls"):
                    with html.Div(
                        style="position:absolute;left:1rem;top:1rem;z-index:100;",
                        classes="d-flex flex-column ga-2 align-start",
                    ):
                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('cloud')",
                        ):
                            v3.VBtn(
                                icon="mdi-weather-cloudy",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.cloud.show = !controls.cloud.show",
                            )
                            v3.VSlider(
                                v_show="controls.cloud.show",
                                v_model="controls.cloud.opacity",
                                min=0,
                                max=1,
                                step=0.01,
                                style="width: 300px",
                                density="compact",
                                hide_details=True,
                            )
                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('surface')",
                        ):
                            v3.VBtn(
                                icon="mdi-layers-outline",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.surface.show = !controls.surface.show",
                            )
                            v3.VSelect(
                                v_show="controls.surface.show",
                                v_model=("controls.surface.color_by", None),
                                items=(
                                    "controls.variables_2d.filter(v => v.selected).map(v => v.name)",
                                ),
                                density="compact",
                                hide_details=True,
                                variant="flat",
                                style="width: 300px",
                            )

                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('volume') || controls.active_viz.includes('slice')",
                        ):
                            v3.VBtn(
                                icon="mdi-cube-outline",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.volume.show = !controls.volume.show",
                            )
                            v3.VSelect(
                                v_show="controls.volume.show",
                                v_model=("controls.volume.color_by", None),
                                items=(
                                    "controls.variables_3d.filter(v => v.selected).map(v => v.name)",
                                ),
                                density="compact",
                                hide_details=True,
                                variant="flat",
                                style="width: 300px",
                            )

                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('slice')",
                        ):
                            v3.VBtn(
                                icon="mdi-flip-vertical",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.slice.show = !controls.slice.show",
                            )
                            v3.VNumberInput(
                                v_show="controls.slice.show",
                                v_model="controls.slice.orientation",
                                step=[1],
                                min=[-90],
                                max=[90],
                                hide_details=True,
                                density="compact",
                                prepend_inner_icon="mdi-compass-outline",
                                style="width: 115px",
                                control_variant="stacked",
                                variant="flat",
                                classes="border-e-thin border-s-thin",
                            )
                            v3.VSlider(
                                v_show="controls.slice.show",
                                v_model="controls.slice.altitude",
                                step="0.1",
                                min=("controls.slice.altitude_min",),
                                max=("controls.slice.altitude_max",),
                                hide_details=True,
                                density="comfortable",
                                prepend_icon="mdi-altimeter",
                                style="width: 400px",
                                classes="ml-2",
                            )

                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('find-data')",
                        ):
                            v3.VBtn(
                                icon="mdi-magnify-scan",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.find_data.show = !controls.find_data.show",
                            )
                            v3.VTextField(
                                v_show="controls.find_data.show",
                                v_model="controls.find_data.formula",
                                hide_details=True,
                                density="compact",
                                prepend_inner_icon="mdi-sigma",
                                style="width: 300px",
                                variant="flat",
                                classes="border-e-thin border-s-thin",
                            )

                        with v3.VCard(
                            classes="d-flex align-center",
                            v_if="controls.active_viz.includes('crop-column')",
                        ):
                            v3.VBtn(
                                icon="mdi-sort",
                                density="comfortable",
                                variant="plain",
                                classes="rounded ma-1",
                                click="controls.column.show = !controls.column.show",
                            )
                            v3.VRangeSlider(
                                v_show="controls.column.show",
                                v_model="controls.column.altitude_range",
                                min=("controls.slice.altitude_min",),
                                max=("controls.slice.altitude_max",),
                                step="0.1",
                                hide_details=True,
                                density="compact",
                                style="width: 300px",
                                variant="flat",
                            )


register_analysis(NAME, Viz3D)
