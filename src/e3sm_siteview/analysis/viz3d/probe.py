"""Probe: hover tooltip and click menu on the columns"""


class ProbeMixin:
    def _probe_active(self):
        return "probes" in self.ctx.setup.active_viz

    def _pick_column(self, x, y):
        """(col_id, lat/lon label) of the column at the display position"""
        if not self.probe_picker.Pick(x, y, 0, self.renderer):
            return None
        ds = self.probe_picker.GetDataSet()
        cell_id = self.probe_picker.GetCellId()
        col_ids = ds.GetCellData().GetArray("col_id") if ds is not None else None
        if col_ids is None or cell_id < 0:
            return None
        col_id = int(col_ids.GetTuple1(cell_id))
        title = next(
            (
                item["title"]
                for item in self.ctx.setup.col_items
                if item["value"] == col_id
            ),
            str(col_id),
        )
        return col_id, title

    def _picked_value(self):
        """'field: value units' of the colored field on the last picked cell"""
        if self.probe_picker.GetActor() is self.surface_actor:
            field, variables = (
                self.ctx.setup.surface.color_by,
                self.ctx.setup.variables_2d,
            )
        else:
            field, variables = (
                self.ctx.setup.volume.color_by,
                self.ctx.setup.variables_3d,
            )
        array = self.probe_picker.GetDataSet().GetCellData().GetArray(field or "")
        if array is None:
            return ""
        value = array.GetTuple1(self.probe_picker.GetCellId())
        units = next((v.units for v in variables if v.name == field), None)
        return f"{field}: {value:.4g}{f' {units}' if units else ''}"

    def _view_fractions(self, x, y):
        """Display position to fractions of the view size from the top left"""
        width, height = self.render_window.GetSize()
        return x / max(width, 1), 1 - y / max(height, 1)

    def _on_probe_hover(self, x, y):
        if not self._probe_active():
            return
        picked = self._pick_column(x, y)
        if picked is None:
            self.probe.hover = False
            return
        self.probe.hover_x, self.probe.hover_y = self._view_fractions(x, y)
        self.probe.hover_title = picked[1]
        self.probe.hover_value = self._picked_value()
        self.probe.hover = True

    def _on_probe_click(self, x, y):
        if not self._probe_active():
            return
        picked = self._pick_column(x, y)
        if picked is None:
            self.probe.menu = False
            return
        self.probe.menu_x, self.probe.menu_y = self._view_fractions(x, y)
        self.probe.menu_col_id, self.probe.menu_title = picked
        self.probe.menu = True

    def _show_analysis(self, name):
        active_analysis = self.ctx.setup.active_analysis
        if name not in active_analysis:
            self.ctx.setup.active_analysis = [*active_analysis, name]

    def probe_to_heatmap(self):
        self.ctx.setup.surface_chart.column = self.probe.menu_col_id
        self._show_analysis("columnHeatMap")
        self.probe.menu = False

    def probe_toggle_line_chart(self):
        col_id = self.probe.menu_col_id
        columns = list(self.ctx.setup.line_chart.columns)
        if col_id in columns:
            columns.remove(col_id)
        else:
            columns.append(col_id)
            self._show_analysis("cellTimeChart")
        self.ctx.setup.line_chart.columns = columns
        self.probe.menu = False
