import asyncio
import json

from trame.app import asynchronous, dataclass
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkStaticPointLocator
from vtkmodules.vtkFiltersCore import vtkCellCenters

from e3sm_siteview.constants import FIELDS_METADATA


class Variable(dataclass.StateDataModel):
    name = dataclass.Sync(str)
    selected = dataclass.Sync(bool, False)
    units = dataclass.Sync(str)
    description = dataclass.Sync(str)

    @dataclass.watch("name", sync=True, eager=True)
    def _on_name_change(self, name):
        tokens = name.split("_")
        for i in range(1, len(tokens) + 1):
            base_name = "_".join(tokens[:i])
            entry = FIELDS_METADATA.get(base_name)
            if entry:
                self.units = entry.get("units")
                self.description = entry.get("description")
                return

        print(f"No matching field name for {name}")

    @dataclass.watch("selected", sync=True)
    def _on_selected(self, _):
        self.server.controller.load_fields()


class CloudControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    opacity = dataclass.Sync(float, 0.5)


class ColorByControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    color_by = dataclass.Sync(str)


class SliceControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    orientation = dataclass.Sync(int, 0)
    altitude = dataclass.Sync(int, 0)


class FindDataControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    formula = dataclass.Sync(str, "")


class ColumnControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    altitude_range = dataclass.Sync(tuple[int, int], (0, 100))
    col_max_idx = dataclass.Sync(int, 0)


class VisualizationAnalysis(dataclass.StateDataModel):
    panels = dataclass.Sync(dict[str, str], dict)


class DrappedChart(dataclass.StateDataModel):
    color_by = dataclass.Sync(str)
    column = dataclass.Sync(int, 0)


class CellTimeCharts(dataclass.StateDataModel):
    fields = dataclass.Sync(list[str], list)
    columns = dataclass.Sync(list[int], list)
    results = dataclass.Sync(list, list)


class GlobalParameters(dataclass.StateDataModel):
    # Data handling
    readers = dataclass.ServerOnly(set, set)
    variables_2d = dataclass.Sync(list[Variable], list, has_dataclass=True)
    variables_3d = dataclass.Sync(list[Variable], list, has_dataclass=True)
    # Time
    time_values = dataclass.Sync(list[int], list)
    time_index = dataclass.Sync(int, 0)
    time_index_max = dataclass.Sync(int, 0)
    time_value = dataclass.Sync(int, 0.0)
    time_animating = dataclass.Sync(bool, False)
    # Columns selection
    radius_deg = dataclass.Sync(float, 1.0)
    center = dataclass.Sync(tuple[float, float, float], (0, 0, 0))
    col_ids_str = dataclass.Sync(str, "[]")
    n_cols = dataclass.Sync(int, 0)
    # 3D Viz controls
    active_viz = dataclass.Sync(list[str], ["volume"])
    cloud = dataclass.Sync(CloudControls, has_dataclass=True)
    surface = dataclass.Sync(ColorByControls, has_dataclass=True)
    volume = dataclass.Sync(ColorByControls, has_dataclass=True)
    slice = dataclass.Sync(SliceControls, has_dataclass=True)
    find_data = dataclass.Sync(FindDataControls, has_dataclass=True)
    column = dataclass.Sync(ColumnControls, has_dataclass=True)
    # Heatmap Chart controls
    surface_chart = dataclass.Sync(DrappedChart, has_dataclass=True)
    # Line chart controls
    line_chart = dataclass.Sync(CellTimeCharts, has_dataclass=True)
    # Analysis
    active_analysis = dataclass.Sync(list[str], ["viz"])
    available_analysis = dataclass.Sync(
        list,
        [
            ("viz", "mdi-earth"),
            ("columnHeatMap", "mdi-view-grid-compact"),
            ("cellTimeChart", "mdi-chart-line"),
        ],
    )

    def __init__(self, server, **defaults):
        super().__init__(server, **defaults)
        self.cloud = CloudControls(server)
        self.surface = ColorByControls(server)
        self.volume = ColorByControls(server)
        self.slice = SliceControls(server)
        self.find_data = FindDataControls(server)
        self.column = ColumnControls(server)
        self.surface_chart = DrappedChart(server)
        self.line_chart = CellTimeCharts(server)

        self.ctrl.load_fields = self.load_fields

        # VTK pipeline to compute col_ids
        centers = vtkCellCenters()
        centers.SetInputData(self.ctx.mesh)
        centers.Update()

        self.col_ids = vtkIdList()
        self.locator = vtkStaticPointLocator()
        self.locator.SetDataSet(centers.GetOutput())
        self.locator.BuildLocator()

    @property
    def ctrl(self):
        return self.server.controller

    @property
    def ctx(self):
        return self.server.context

    @dataclass.watch("time_values", sync=True)
    def _on_time_values(self, values):
        self.time_index_max = len(values) - 1
        self.time_value = values[self.time_index]

    @dataclass.watch("time_index", sync=True)
    def _on_time_index(self, time_index):
        self.time_value = self.time_values[time_index]

    @dataclass.watch("time_animating")
    def _on_animation(self, time_animating):
        if time_animating:
            asynchronous.create_task(self._animate())

    @dataclass.watch("radius_deg", "center")
    def apply_region(self, radius_deg, center):
        self.locator.FindPointsWithinRadius(radius_deg, center, self.col_ids)
        self.col_ids.Sort()
        col_id = numpy_support.vtk_to_numpy(
            self.ctx.mesh.GetCellData().GetArray("col_id")
        )
        selected_ids = [
            int(col_id[self.col_ids.GetId(i)])
            for i in range(self.col_ids.GetNumberOfIds())
        ]
        self.col_ids_str = json.dumps(selected_ids)
        self.n_cols = len(selected_ids)

    async def _animate(self):
        while self.time_animating:
            await asyncio.sleep(0.1)
            if self.time_index < self.time_index_max:
                self.time_index += 1
            else:
                self.time_index = 0

    def register_data_reader(self, reader):
        if len(self.readers) == 0:
            selection = reader.GetProfileVariables()
            names = [
                selection.GetArrayName(i) for i in range(selection.GetNumberOfArrays())
            ]
            # HOW do I split 2d/3d arrays?
            self.variables_3d = [Variable(self.server, name=str(n)) for n in names]
            tdim = reader.GetDimensions().get("time")
            n_time = tdim.size if tdim is not None else 1
            self.time_values = list(range(n_time))

        self.readers.add(reader)

    def load_fields(self):
        for reader in self.readers:
            array_selection = reader.GetProfileVariables()
            array_selection.DisableAllArrays()
            for name in (f.name for f in self.variables_2d if f.selected):
                # print(f"+(2d) {name}")
                array_selection.EnableArray(name)
            for name in (f.name for f in self.variables_3d if f.selected):
                # print(f"+(3d) {name}")
                array_selection.EnableArray(name)

    @dataclass.watch("time_value", sync=True)
    def update_reader_time(self, time_value):
        slice_desc = json.dumps({"time": time_value})
        for reader in self.readers:
            reader.SetSlicing(slice_desc)
        self.ctrl.update_color_range()
        self.ctrl.render()

    @dataclass.watch("col_ids_str")
    def update_reader_col_ids(self, col_ids_str):
        for reader in self.readers:
            reader.SetColumnIds(col_ids_str)
