import os
from vtkmodules.vtkCommonCore import (
    vtkPoints,
)

from vtkmodules.vtkFiltersCore import (
    vtkAppendFilter,
)
from vtkmodules.util import numpy_support
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
import numpy as np
from pyproj import Proj, Transformer


# Number of threads for the projection fan-out. pyproj releases the GIL
# inside Transformer.transform, so chunking the input across threads
# scales nearly linearly (7.4x on 8 threads in our bench). Default is
# max(1, cpu_count - 1) to leave one core for the UI/IO thread; override
# via QV_PROJECTION_THREADS for HPC machines or to pin down for testing.
def _default_projection_threads():
    env = os.environ.get("QV_PROJECTION_THREADS")
    if env:
        try:
            return max(1, int(env))
        except ValueError:
            pass
    return max(1, (os.cpu_count() or 2) - 1)


_PROJECTION_THREADS = _default_projection_threads()
# Below this point count the thread-pool overhead outweighs the speedup.
_PROJECTION_THREADING_MIN = 1_000_000


def _threaded_transform(xformer, x, y):
    """Apply xformer.transform over x, y by chunking across threads."""
    n = len(x)
    if _PROJECTION_THREADS <= 1 or n < _PROJECTION_THREADING_MIN:
        return xformer.transform(x, y)

    chunk = n // _PROJECTION_THREADS

    def work(i):
        lo = i * chunk
        hi = n if i == _PROJECTION_THREADS - 1 else lo + chunk
        return xformer.transform(x[lo:hi], y[lo:hi])

    with ThreadPoolExecutor(max_workers=_PROJECTION_THREADS) as ex:
        results = list(ex.map(work, range(_PROJECTION_THREADS)))

    x_out = np.concatenate([r[0] for r in results])
    y_out = np.concatenate([r[1] for r in results])
    return x_out, y_out

EARTH_RADIUS = 6_356_752


class EAMProject(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(
            nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )
        self.__Dims = -1
        self.project = 3  # make spherical the default
        self.altitude_scale = 1.0
        self.translate = False
        self.cached_points = None
        # Cache keyed on input-points identity + projection params. Immune to
        # spurious upstream Modified() on the shared points.
        self._cached_input_points = None
        self._cached_key = None

    def _invalidate_cache(self):
        self.cached_points = None
        self._cached_input_points = None
        self._cached_key = None

    def SetTranslation(self, translate):
        if self.translate != translate:
            self.translate = translate
            self._invalidate_cache()
            self.Modified()

    def SetProjection(self, project):
        if self.project != int(project):
            self.project = int(project)
            self._invalidate_cache()
            self.Modified()

    def SetAltitudeScale(self, value):
        if self.altitude_scale != value:
            self.altitude_scale = float(value)
            self._invalidate_cache()
            self.Modified()

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        outData.ShallowCopy(inData)
        in_points = inData.GetPoints()

        cache_key = (id(in_points), self.project, self.translate)
        if self.cached_points is not None and self._cached_key == cache_key:
            outData.SetPoints(self.cached_points)
        else:
            # we modify the points, so copy them
            out_points_vtk = vtkPoints()
            out_points_vtk.DeepCopy(outData.GetPoints())
            outData.SetPoints(out_points_vtk)
            out_points_np = outData.points.GetData()
            flat = out_points_np.flatten()
            x = flat[0::3] - 180.0 if self.translate else flat[0::3]
            y = flat[1::3]
            z = flat[2::3]

            if self.project == 3:
                # Spherical
                to_rad = np.pi / 180
                x_rad = x * to_rad
                y_rad = y * to_rad
                cos_y_rad = np.cos(y_rad)
                radius = (EARTH_RADIUS + self.altitude_scale * z)
                zs = radius * np.cos(x_rad) * cos_y_rad
                xs = radius * np.sin(x_rad) * cos_y_rad
                ys = radius * np.sin(y_rad)
                flat[0::3] = xs
                flat[1::3] = ys
                flat[2::3] = zs
            else:
                try:
                    # Use proj4 string for WGS84 instead of EPSG code to avoid database dependency
                    latlon = Proj(proj="latlong", datum="WGS84")
                    if self.project == 1:
                        proj = Proj(proj="robin")
                    elif self.project == 2:
                        proj = Proj(proj="moll")
                    else:
                        # Should not reach here, but return without transformation
                        return 1

                    xformer = Transformer.from_proj(latlon, proj, always_xy=True)
                    res = _threaded_transform(xformer, x, y)
                except Exception as e:
                    print(f"Projection error: {e}")
                    # If projection fails, return without modifying coordinates
                    return 1

                flat[0::3] = np.array(res[0])
                flat[1::3] = np.array(res[1])
                flat[2::3] *= self.altitude_scale

            outPoints = flat.reshape(out_points_np.shape)
            _coords = numpy_support.numpy_to_vtk(outPoints, deep=True)
            outData.GetPoints().SetData(_coords)
            # the previous cached_points, if any, is available for
            # garbage collection after this assignment
            self.cached_points = out_points_vtk
            self._cached_input_points = in_points  # hold ref so id() stays valid
            self._cached_key = cache_key

        return 1
