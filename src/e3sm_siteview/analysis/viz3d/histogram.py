"""Histogram of the colored field over the visible cells"""

import numpy as np
import plotly.graph_objects as go
from trame_client.encoders.numpy import encode
from vtkmodules.util import numpy_support

from e3sm_siteview.analysis.viz3d.constants import HISTOGRAM_BINS


def snap_bound(values, mask, percentile, bound):
    """Percentile of the values excluding the extreme one, so a dominant
    bound value (e.g. lots of 0) does not hide the rest of the distribution.
    A 0/100 percentile keeps the data bound."""
    if percentile in (0, 100):
        return bound
    values = values[mask]
    if values.size == 0:
        return bound
    return np.percentile(values, percentile)


class HistogramMixin:
    def _visible_data_array(self):
        """Cell array of the color_by field for what is shown in the 3D view"""
        color_by = self.ctx.setup.volume.color_by
        if not color_by:
            return None

        if self.find_data_actor.visibility:
            self.find_data_threshold.Update()
            ds = self.find_data_threshold.GetOutputDataObject(0)
            return ds.GetCellData().GetArray(color_by)

        return self.get_data_array()

    def _update_histogram(self, *_):
        histogram = self.ctx.setup.histogram
        if "histogram" not in self.ctx.setup.active_viz:
            self._histogram_key = None
            self._histogram_data_key = None
            self._histogram_snap_key = None
            return

        array = self._visible_data_array()
        color_by = self.ctx.setup.volume.color_by
        data_key = (
            color_by,
            None if array is None else (id(array), array.GetMTime()),
        )
        snap_min, snap_max = histogram.snap_min, histogram.snap_max
        snap_key = (data_key, snap_min, snap_max)
        if (
            snap_key == self._histogram_snap_key
            and (data_key, tuple(histogram.range)) == self._histogram_key
        ):
            return

        values = np.array([])
        if array is not None:
            values = numpy_support.vtk_to_numpy(array).ravel()
            values = values[np.isfinite(values)]

        if values.size == 0:
            self._histogram_key = None
            self._histogram_data_key = None
            self._histogram_snap_key = None
            histogram.figure = {}
            return

        # Only (re)apply snapping/clamping when the data or the snap changed
        # so a user defined range is not overridden.
        if snap_key != self._histogram_snap_key:
            data_changed = data_key != self._histogram_data_key
            self._histogram_snap_key = snap_key
            self._histogram_data_key = data_key
            data_min, data_max = float(values.min()), float(values.max())
            histogram.data_range = (data_min, data_max)
            lo, hi = histogram.range
            if data_changed:
                lo, hi = max(lo, data_min), min(hi, data_max)
            if snap_min is not None:
                lo = snap_bound(values, values > data_min, snap_min, data_min)
            if snap_max is not None:
                hi = snap_bound(values, values < data_max, 100 - snap_max, data_max)
            if lo >= hi:
                lo, hi = data_min, data_max
            histogram.range = (float(lo), float(hi))

        lo, hi = (float(v) for v in histogram.range)
        self._histogram_key = (data_key, tuple(histogram.range))

        counts, edges = np.histogram(values, bins=HISTOGRAM_BINS, range=(lo, hi))

        units = next(
            (v.units for v in self.ctx.setup.variables_3d if v.name == color_by),
            None,
        )
        units = f" {units}" if units else ""
        percents = 100 * counts / values.size
        fig = go.Figure(
            data=go.Bar(
                x=(edges[:-1] + edges[1:]) / 2,
                y=counts,
                width=np.diff(edges),
                marker_color="#1f77b4",
                customdata=np.column_stack((edges[:-1], edges[1:], percents)),
                hovertemplate=(
                    f"<b>{color_by}</b>: [%{{customdata[0]:.4g}}, "
                    f"%{{customdata[1]:.4g}}]{units}<br>"
                    "<b>Cells</b>: %{y:,} (%{customdata[2]:.1f}%)"
                    f"<br><b>Total</b>: {values.size:,} cells"
                    "<extra></extra>"
                ),
                hoverlabel={"font": {"size": 11}},
            )
        )
        fig.update_layout(
            title={
                "text": (
                    f"{color_by} ({counts.sum():,} of {values.size:,} cells)"
                    if counts.sum() < values.size
                    else f"{color_by} ({values.size:,} cells)"
                ),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 12},
            },
            bargap=0,
            showlegend=False,
            margin={"b": 30, "l": 40, "r": 10, "t": 30},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"size": 10},
        )
        self.ctx.setup.histogram.figure = encode(fig.to_plotly_json())
