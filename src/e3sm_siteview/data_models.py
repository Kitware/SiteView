import asyncio

from paraview import simple
from trame.app import asynchronous, dataclass

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
    altitude = dataclass.Sync(float, 0)
    altitude_min = dataclass.Sync(float, 0)
    altitude_max = dataclass.Sync(float, 100)


class FindDataControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    formula = dataclass.Sync(str, "")


class ColumnControls(dataclass.StateDataModel):
    show = dataclass.Sync(bool, True)
    altitude_range = dataclass.Sync(tuple[float, float], (0, 100))


class GlobalParameters(dataclass.StateDataModel):
    readers = dataclass.ServerOnly(set, set)
    variables_2d = dataclass.Sync(list[Variable], list, has_dataclass=True)
    variables_3d = dataclass.Sync(list[Variable], list, has_dataclass=True)
    time_values = dataclass.Sync(list[float], list)
    time_index = dataclass.Sync(int, 0)
    time_index_max = dataclass.Sync(int, 0)
    time_value = dataclass.Sync(float, 0.0)
    # Visualization
    active_viz = dataclass.Sync(list[str], ["surface"])
    time_animating = dataclass.Sync(bool, False)
    # Viz controls
    cloud = dataclass.Sync(CloudControls, has_dataclass=True)
    surface = dataclass.Sync(ColorByControls, has_dataclass=True)
    volume = dataclass.Sync(ColorByControls, has_dataclass=True)
    slice = dataclass.Sync(SliceControls, has_dataclass=True)
    find_data = dataclass.Sync(FindDataControls, has_dataclass=True)
    column = dataclass.Sync(ColumnControls, has_dataclass=True)

    def __init__(self, server, **defaults):
        super().__init__(server, **defaults)
        self.cloud = CloudControls(server)
        self.surface = ColorByControls(server)
        self.volume = ColorByControls(server)
        self.slice = SliceControls(server)
        self.find_data = FindDataControls(server)
        self.column = ColumnControls(server)

        self.ctrl.load_fields = self.load_fields
        self.animation_scene = simple.GetAnimationScene()

    @property
    def ctrl(self):
        return self.server.controller

    @dataclass.watch("time_values", sync=True)
    def _on_time_values(self, values):
        self.time_index_max = len(values) - 1
        self.time_value = values[self.time_index]

    @dataclass.watch("time_index", sync=True)
    def _on_time_index(self, time_index):
        self.time_value = self.time_values[time_index]
        self.animation_scene.AnimationTime = self.time_value
        self.ctrl.render()

    @dataclass.watch("time_animating")
    def _on_animation(self, time_animating):
        if time_animating:
            asynchronous.create_task(self._animate())

    async def _animate(self):
        while self.time_animating:
            await asyncio.sleep(0.1)
            if self.time_index < self.time_index_max:
                self.time_index += 1
            else:
                self.time_index = 0
            self.ctrl.render()

    def register_reader(self, reader):
        if len(self.readers) == 0:
            reader.UpdatePipelineInformation()
            self.time_values = [float(t) for t in reader.TimestepValues]
            self.variables_2d = [
                Variable(self.server, name=str(n))
                for n in reader.SurfaceVariables.Available
            ]
            self.variables_3d = [
                Variable(self.server, name=str(n))
                for n in reader.MiddleLayerVariables.Available
            ]

        self.readers.add(reader)

    def load_fields(self):
        for reader in self.readers:
            reader.SurfaceVariables = [f.name for f in self.variables_2d if f.selected]
            reader.MiddleLayerVariables = [
                f.name for f in self.variables_3d if f.selected
            ]
