from trame.widgets import client

from e3sm_siteview import module
from e3sm_siteview.components.controls import VIZ_LAYER_SHORTCUTS, toggle_layer


class KeyboardShortcuts(client.ClientTriggers):
    """Global keyboard shortcuts of the viz page (needs "controls").

    Space play/pause, Left/Right step time, R reset camera, digits toggle layers.
    Ignored while typing in a field or when a setup dialog is open.
    """

    def __init__(self, reset_camera):
        actions = {
            " ": "controls.time_animating = !controls.time_animating",
            "ArrowLeft": "controls.time_index > 0 && controls.time_index--",
            "ArrowRight": (
                "controls.time_index < controls.time_index_max && controls.time_index++"
            ),
            "r": "trigger('siteview_reset_camera')",
            "R": "trigger('siteview_reset_camera')",
        }
        for key, digit in VIZ_LAYER_SHORTCUTS.items():
            actions[digit] = toggle_layer(key)

        enabled = "controls.active_page === 'viz'"
        js_actions = ", ".join(
            f"'{k}': () => {enabled} && ({v})" for k, v in actions.items()
        )
        super().__init__(
            ref="siteview_shortcuts",
            mounted=f"utils.e3sm.setShortcuts({{ {js_actions} }})",
            before_unmount="utils.e3sm.setShortcuts(null)",
        )
        self.server.enable_module(module)
        self.server.trigger("siteview_reset_camera")(reset_camera)
