from pathlib import Path

from paraview import simple
from trame.app import TrameComponent, asynchronous

from e3sm_siteview.analysis import create_analysis, load_all_analysis
from e3sm_siteview.cli import configure_and_parse
from e3sm_siteview.data_models import GlobalParameters


def create_viewers(server):
    load_all_analysis()
    options = configure_and_parse(server.cli)

    server.context.setup = GlobalParameters(server)
    viewers = server.context.viewers = {}

    connectivity_file = Path(options.cf).resolve()
    for data_file in options.df:
        viewer = E3SMAnalyser(
            server,
            connectivity_file,
            Path(data_file).resolve(),
        )
        viewers[viewer.name] = viewer


class E3SMAnalyser(TrameComponent):
    def __init__(self, server, connectivity_file, data_file):
        super().__init__(server)
        self._name = Path(data_file).name
        self.reader = simple.EAMDataReader(
            DataFile=str(data_file),
            ConnectivityFile=str(connectivity_file),
        )
        self.ctx.setup.register_reader(self.reader)
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
