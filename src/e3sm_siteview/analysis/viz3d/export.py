"""PNG export of the 3D view with its scalar bars"""

from vtkmodules.util import numpy_support
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter

from e3sm_siteview.analysis.viz3d.constants import EXPORT_SCALE, VIEW_THEMES


class ExportMixin:
    def _export_scalar_bars(self):
        """Scalar bars of the colored layers, like the ones shown in the UI"""
        active_viz = self.ctx.setup.active_viz
        bars = []
        if "surface" in active_viz and self.ctx.setup.surface.color_by:
            bars.append((self.surface_mapper, self.ctx.setup.surface.color_by))
        if self.ctx.setup.volume.color_by and any(
            v in active_viz for v in ("volume", "hslice", "vslice", "find_data")
        ):
            bars.append((self.volume_mapper, self.ctx.setup.volume.color_by))

        color = VIEW_THEMES["dark" if self.ctx.setup.dark else "light"]["lines"]
        actors = []
        width = 0.8 / max(1, len(bars))
        for i, (mapper, title) in enumerate(bars):
            actor = vtkScalarBarActor(
                lookup_table=mapper.GetLookupTable(),
                title=title,
                number_of_labels=5,
                label_format="%.4g",
                bar_ratio=0.5,
                unconstrained_font_size=True,
                maximum_height_in_pixels=60 * EXPORT_SCALE,
            )
            actor.SetOrientationToHorizontal()
            actor.position = (0.1 + i * width + 0.02, 0.02)
            actor.position2 = (width - 0.04, 0.12)
            for prop in (actor.title_text_property, actor.label_text_property):
                prop.color = color
                prop.shadow = False
                prop.italic = False
                prop.font_size = 14
            actor.title_text_property.bold = True
            actors.append(actor)

        return actors

    def export_png(self):
        """Render the 3D view at a higher resolution, with its scalar bars"""
        bars = self._export_scalar_bars()
        for bar in bars:
            self.renderer.AddViewProp(bar)

        # Render once in a bigger window rather than with the tiles of
        # vtkWindowToImageFilter (each tile showed the whole scene).
        # Scaling the DPI keeps the text proportional.
        size = self.render_window.GetSize()
        dpi = self.render_window.GetDPI()
        self.render_window.SetSize(size[0] * EXPORT_SCALE, size[1] * EXPORT_SCALE)
        self.render_window.SetDPI(dpi * EXPORT_SCALE)
        self.render_window.Render()

        window = vtkWindowToImageFilter(
            input=self.render_window, read_front_buffer=False
        )
        writer = vtkPNGWriter(write_to_memory=True)
        window >> writer
        writer.Write()
        data = numpy_support.vtk_to_numpy(writer.GetResult()).tobytes()

        for bar in bars:
            self.renderer.RemoveViewProp(bar)
        self.render_window.SetSize(*size)
        self.render_window.SetDPI(dpi)
        self.render_window.Render()
        self.view_handler.update()

        return self.server.protocol.addAttachment(data)
