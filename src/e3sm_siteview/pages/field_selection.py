from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout

from e3sm_siteview.components.field_selection import FieldSelection


class FieldSelectionPage(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._build_ui()

    def _build_ui(self):
        with VAppLayout(self.server) as self.ui:
            FieldSelection(self.next)

    def next(self):
        self.ctx.pages.viz.activate()

    def activate(self):
        self._build_ui()


def main():
    app = FieldSelectionPage()
    app.server.start()


if __name__ == "__main__":
    main()
