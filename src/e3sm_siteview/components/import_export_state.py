import json
import os
from datetime import datetime
from pathlib import Path

from trame.app import TrameComponent
from trame.app.file_upload import ClientFile
from trame.decorators import change, trigger
from trame.widgets import vuetify4 as v4

from e3sm_siteview import __version__
from e3sm_siteview.analysis.viz3d.camera import get_camera_state, set_camera_state
from e3sm_siteview.components.footer import TooltipButton
from e3sm_siteview.components.site_selection import SITE_KEYS

# Settings of the 3D view colormaps saved in the state files
COLORMAP_KEYS = (
    "diverging",
    "preset",
    "invert",
    "use_log_scale",
    "discrete_log",
    "n_discrete_colors",
    "override_range",
    "color_value_min",
    "color_value_max",
    "cut_outside_range",
    "nan_color",
    "epsilon",
    "abs_max",
)


class ImportExportState(TrameComponent):
    """Export the analysis to a state file and import it back.

    ``options`` are the parsed command line arguments: their data files are
    saved and their ``state`` (if any) is imported at startup.
    ``load_analyses()`` loads the selected fields as the setup dialog does.
    """

    def __init__(self, server, options, load_analyses):
        super().__init__(server)
        self._load_analyses = load_analyses
        # Absolute paths, so that --state works from any directory
        self._files = {
            "connectivity": str(Path(options.cf).resolve()),
            "data": [str(Path(f).resolve()) for f in options.df],
        }
        if options.state:
            self.ctrl.on_server_ready.add_task(
                lambda **_: self.import_state(options.state)
            )

    @trigger("siteview_export_state")
    def export_state(self):
        """State file content of the current analysis"""
        setup = self.ctx.setup
        return json.dumps(
            {
                "origin": {
                    "version": __version__,
                    "user": os.environ.get("USER", os.environ.get("USERNAME")),
                    "created": datetime.now().isoformat(timespec="seconds"),
                },
                "files": self._files,
                "site": {k: self.state[k] for k in SITE_KEYS},
                "fields": [
                    v.name
                    for v in [*setup.variables_2d, *setup.variables_3d]
                    if v.selected
                ],
                "settings": setup.get_settings(),
                # One entry per data file, in the "files" order
                "colormaps": [
                    {
                        layer: {k: getattr(colormap, k) for k in COLORMAP_KEYS}
                        for layer, colormap in viewer.colormaps.items()
                    }
                    for viewer in self.ctx.viewers.values()
                ],
                "camera": get_camera_state(),
            },
            indent=2,
        )

    @change("siteview_state_file_to_import")
    async def _on_state_file_to_import(self, siteview_state_file_to_import, **_):
        if siteview_state_file_to_import is None:
            return
        # Reset the input so that the same file can be imported again
        with self.state:
            self.state.siteview_state_file_to_import = None
        await self.import_state(
            json.loads(ClientFile(siteview_state_file_to_import).content)
        )

    async def import_state(self, content):
        site = {k: content["site"][k] for k in SITE_KEYS}
        fields = set(content["fields"])
        settings = content["settings"]
        saved_colormaps = content["colormaps"]
        camera = content["camera"]

        setup = self.ctx.setup
        setup.active_page = "viz"
        with self.state:
            self.state.siteview_loading = "Loading state"
        await self.server.network_completion

        try:
            # Site and fields, then load them as the setup dialog does
            with self.state:
                self.state.update(site)
            for v in [*setup.variables_2d, *setup.variables_3d]:
                v.selected = v.name in fields
            await setup.completion()  # wait for the columns of the new region
            with self.state:
                self._load_analyses()

            colormaps = [
                (viewer.colormaps[layer], values)
                for viewer, layers in zip(
                    self.ctx.viewers.values(), saved_colormaps, strict=False
                )
                for layer, values in layers.items()
            ]
            models = [setup, setup.volume, *(colormap for colormap, _ in colormaps)]
            # Apply twice: the watchers reset some values on the first pass
            # (heat map column and field on a new region and volume field,
            # camera on a new focus, colormap range on a new diverging mode)
            for _ in range(2):
                setup.set_settings(settings)
                for colormap, values in colormaps:
                    colormap.update(**values)
                for model in models:
                    await model.completion()

            self.ctrl.apply_find_data()
            set_camera_state(camera)
            self.ctrl.render()
        finally:
            with self.state:
                self.state.siteview_loading = ""


def ImportFile():
    """Hidden input uploading the picked file to "siteview_state_file_to_import".
    Import buttons open it by clicking it."""
    return v4.VFileInput(
        id="siteview-import-file",
        v_model=("siteview_state_file_to_import", None),
        accept=".json,application/json",
        classes="d-none",
    )


class ImportExportMenu(v4.VMenu):
    """Export the analysis to a state file or import one (needs "controls")"""

    def __init__(self):
        super().__init__(location="bottom end")

        with self:
            with v4.Template(v_slot_activator="{ props }"):
                TooltipButton(
                    "'Import / export state'",
                    v_bind="props",
                    icon="mdi-folder-arrow-left-right-outline",
                    variant="text",
                    density="comfortable",
                    classes="mr-2 rounded",
                    disabled=("!!siteview_loading",),
                )
            with v4.VList(density="compact"):
                v4.VListItem(
                    title="Export state",
                    subtitle="Save site, fields and analyses",
                    prepend_icon="mdi-file-download-outline",
                    disabled=("!controls.data_loaded",),
                    click="utils.download('siteview-state.json', trigger('siteview_export_state'), 'application/json')",
                )
                v4.VListItem(
                    title="Import state",
                    subtitle="Restore a saved state file",
                    prepend_icon="mdi-file-upload-outline",
                    click="utils.get('document').getElementById('siteview-import-file').click()",
                )
