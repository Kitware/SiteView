"""Reaction of the 3D layers to the UI controls"""

import math

from trame.decorators import controller
from vtkmodules.vtkCommonDataModel import vtkDataObject

from e3sm_siteview.analysis.viz3d.constants import (
    FIND_DATA_ARRAY,
    HEATMAP_COLUMN_COLOR,
    LINE_CHART_COLORS,
)


class LayersMixin:
    def _sync_chart_colormap(self, *_):
        lut = self.volume_mapper.GetLookupTable()
        n_colors = lut.GetNumberOfTableValues() if lut else 0
        if n_colors < 2:
            return

        colorscale = []
        for i in range(n_colors):
            r, g, b, _ = lut.GetTableValue(i)
            colorscale.append(
                [
                    i / (n_colors - 1),
                    f"rgb({round(r * 255)},{round(g * 255)},{round(b * 255)})",
                ]
            )

        self.ctx.setup.surface_chart.colorscale = colorscale
        self.ctx.setup.surface_chart.color_range = list(
            self.colormap_config.color_range
        )

    def _on_z_scale_change(self, zscale):
        for projection_filter in self._projections:
            projection_filter.SetAltitudeScale(zscale)

        self.view_handler.update()

    def _on_column_markers_change(self, *_):
        active_analysis = self.ctx.setup.active_analysis
        line_entries = []
        if "cellTimeChart" in active_analysis:
            line_entries = [
                (col_id, LINE_CHART_COLORS[i % len(LINE_CHART_COLORS)])
                for i, col_id in enumerate(self.ctx.setup.line_chart.columns)
            ]

        cylinders = list(
            line_entries
        )  # Edit if only want to see sphere for line locations
        heatmap_column = self.ctx.setup.surface_chart.column
        if "columnHeatMap" in active_analysis and heatmap_column is not None:
            cylinders = [e for e in cylinders if e[0] != heatmap_column]
            cylinders.append((heatmap_column, HEATMAP_COLUMN_COLOR))

        self.column_markers.SetCylinders(cylinders)
        self.column_markers.SetSpheres(line_entries)
        self.column_markers.SetLevel(self.ctx.setup.hslice.altitude)
        self.view_handler.update()

    def _on_region_change(self, center, radius_deg):
        self.level_cylinder.SetCenter(center[0], center[1])
        self.level_cylinder.SetRadius(radius_deg)
        self._update_site_marker()
        self.view_handler.update()

    def _on_visibility_change(self, active_viz):
        has_volume = "volume" in active_viz
        has_slice = "hslice" in active_viz or "vslice" in active_viz
        has_cloud = "cloud" in active_viz
        has_find = "find_data" in active_viz and self._find_data_valid
        has_inside = has_slice or has_cloud or has_find

        self.slice_h_actor.visibility = 0
        self.slice_v_actor.visibility = 0
        self.outline_actor.visibility = 0
        self.volume_actor.visibility = 0
        self.threshold_actor.visibility = 1 if has_cloud else 0
        self.find_data_actor.visibility = 1 if has_find else 0
        self.surface_actor.visibility = 1 if "surface" in active_viz else 0

        if "probes" not in active_viz:
            self.probe.hover = False
            self.probe.menu = False

        if has_volume:
            self.volume_actor.visibility = 1
            self.outline_actor.visibility = 0

        if has_slice:
            self.slice_h_actor.visibility = "hslice" in active_viz
            self.slice_v_actor.visibility = "vslice" in active_viz

        if has_inside:
            self.outline_actor.visibility = has_volume
            self.volume_actor.visibility = 0

        self.ctrl.update_color_range.enable_empty()()
        self._update_histogram()
        self.view_handler.update()

    def _on_volume_color_by_change(self, color_by):
        if color_by:
            self.colormap_config.set_data_array(color_by, self.get_data_array, "cell")
        self._update_histogram()
        self.view_handler.update()

    def _on_surface_color_by_change(self, color_by):
        if color_by and self.surface_reader is not None:
            self.surface_colormap_config.set_data_array(
                color_by, self.get_surface_data_array, "cell"
            )
        self.view_handler.update()

    def _update_surface_color_range(self):
        if self.ctx.setup.surface.color_by and self.surface_reader is not None:
            self.surface_colormap_config.update_color_range()

    def _on_column_height_change(self, altitude_range):
        self.volume.SetLevelRange(*altitude_range)

        self.ctx.setup.hslice.altitude = max(
            self.ctx.setup.hslice.altitude, altitude_range[0]
        )
        self.ctx.setup.hslice.altitude = min(
            self.ctx.setup.hslice.altitude, altitude_range[1]
        )
        self.ctrl.update_color_range()
        self._update_histogram()
        self.view_handler.update()

    def _on_column_slice_change(self, level):
        self.horizontal_slice.SetLevelRange(level, level)
        self.ctrl.update_color_range.enable_empty()()
        self._update_histogram()
        self.view_handler.update()

    def _on_hslice_edges_change(self, edges):
        self.slice_h_actor.property.edge_visibility = edges
        self.view_handler.update()

    def _on_vslice_edges_change(self, edges):
        self.slice_v_actor.property.edge_visibility = edges
        self.view_handler.update()

    def _on_orientation_slice_change(self, heading):
        nx = math.cos(math.radians(heading))
        ny = math.sin(math.radians(heading))

        self.slice_v_plane.origin = (
            self.ctx.setup.center[0],
            self.ctx.setup.center[1],
            0,
        )
        self.slice_v_plane.normal = (nx, ny, 0)
        self._update_histogram()
        self.view_handler.update()

    def _on_cloud_change(self, threshold_by, threshold_value, opacity):
        if not threshold_by:
            return
        ds = self.clean_volume.GetOutput()
        array = ds.cell_data[threshold_by]
        min_value, max_value = array.GetRange()
        value = (max_value - min_value) * threshold_value + min_value

        self.threshold.SetInputArrayToProcess(
            0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, threshold_by
        )
        self.threshold.SetThresholdFunction(2)
        self.threshold.SetUpperThreshold(value)
        self.threshold_actor.property.opacity = opacity
        self.view_handler.update()

    @controller.add("apply_find_data")
    def _apply_find_data(self):
        formula = self.ctx.setup.find_data.formula.strip()
        self._find_data_valid = False

        if formula:
            self.clean_volume.Update()
            calculator = self.find_data_calculator
            calculator.RemoveAllVariables()
            for name in self.clean_volume.GetOutputDataObject(0).cell_data:
                calculator.AddScalarArrayName(name)
            calculator.function = formula
            calculator.Update()
            ds = calculator.GetOutputDataObject(0)
            if ds.GetCellData().GetArray(FIND_DATA_ARRAY) is None:
                self.ctx.setup.find_data.error = "Invalid formula"
            else:
                self._find_data_valid = True

        self._on_visibility_change(self.ctx.setup.active_viz)
