from pathlib import Path

from trame.app import TrameComponent, asynchronous

from e3sm_siteview.analysis import create_analysis
from e3sm_siteview.plugins.reader import EAMSliceSource


class E3SMAnalyser(TrameComponent):
    def __init__(self, server, connectivity_file, data_file):
        super().__init__(server)
        self._name = Path(data_file).name
        self.reader = EAMSliceSource()
        self.reader.SetDataFileName(str(data_file))
        self.reader.SetConnFileName(str(connectivity_file))
        self._analysis = {}

    @property
    def name(self):
        return self._name

    def add_analysis(self, type="viz"):
        analysis = create_analysis(type, self.server, self.reader)
        if analysis is None:
            msg = f"Invalid analysis type: {type}"
            raise ValueError(msg)
        self._analysis[type] = analysis
        asynchronous.create_task(
            self._add_panel(analysis.name, self.name, analysis.name)
        )

    async def _add_panel(self, panel_id, label, template_name):
        self.ctx.views_container.add_panel(panel_id, label, template_name)
