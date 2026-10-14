"""North-up camera interaction and camera placement"""

import math

from trame.decorators import controller
from vtkmodules.vtkCommonCore import vtkMath
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from e3sm_siteview.analysis.viz3d.constants import CLICK_TOLERANCE, EARTH_AXIS
from e3sm_siteview.io import EARTH_RADIUS


def _rotate_camera(camera, angle, axis, center):
    """Rotate camera around an axis going through center"""
    transform = vtkTransform()
    transform.Translate(center)
    transform.RotateWXYZ(angle, axis)
    transform.Translate(*(-v for v in center))
    camera.position = transform.TransformPoint(camera.position)
    camera.focal_point = transform.TransformPoint(camera.focal_point)


def create_north_up_interactor_style(get_rotation_center, on_hover=None, on_click=None):
    """
    Trackball camera style where left-drag rotates the camera around
    an axis parallel to the earth rotation axis going through
    get_rotation_center() (horizontal motion) and tilts it toward the
    poles (vertical motion) while keeping north up.
    Middle/right buttons and wheel keep their default pan/zoom behavior.

    on_hover(x, y) is called on mouse move without button pressed and
    on_click(x, y) on a left press/release without dragging.
    """
    style = vtkInteractorStyleTrackballCamera()
    state = {"rotating": False, "press_position": None}

    def on_left_press(*_):
        interactor = style.GetInteractor()
        style.FindPokedRenderer(*interactor.GetEventPosition())
        if style.GetCurrentRenderer() is None:
            return
        state["rotating"] = True
        state["press_position"] = interactor.GetEventPosition()

    def on_left_release(*_):
        state["rotating"] = False
        press_position = state["press_position"]
        state["press_position"] = None
        if on_click is None or press_position is None:
            return
        x, y = style.GetInteractor().GetEventPosition()
        if (
            abs(x - press_position[0]) <= CLICK_TOLERANCE
            and abs(y - press_position[1]) <= CLICK_TOLERANCE
        ):
            on_click(x, y)

    def on_mouse_move(*_):
        if not state["rotating"]:
            style.OnMouseMove()
            if on_hover is not None:
                on_hover(*style.GetInteractor().GetEventPosition())
            return

        interactor = style.GetInteractor()
        renderer = style.GetCurrentRenderer()
        camera = renderer.active_camera
        x, y = interactor.GetEventPosition()
        last_x, last_y = interactor.GetLastEventPosition()
        width, height = renderer.GetSize()
        center = get_rotation_center()

        # Spin around the earth rotation axis
        azimuth = -180.0 * (x - last_x) / max(width, 1)
        _rotate_camera(camera, azimuth, EARTH_AXIS, center)

        # Tilt toward the poles without going over them
        elevation = 180.0 * (y - last_y) / max(height, 1)
        dop = camera.GetDirectionOfProjection()
        right = [0, 0, 0]
        vtkMath.Cross(dop, EARTH_AXIS, right)
        if vtkMath.Normalize(right) > 0:
            pole_angle = math.degrees(
                math.acos(max(-1.0, min(1.0, vtkMath.Dot(dop, EARTH_AXIS))))
            )
            if 1.0 < pole_angle - elevation < 179.0:
                _rotate_camera(camera, elevation, right, center)

        camera.view_up = EARTH_AXIS
        camera.OrthogonalizeViewUp()
        if style.GetAutoAdjustCameraClippingRange():
            renderer.ResetCameraClippingRange()
        interactor.Render()

    style.AddObserver("LeftButtonPressEvent", on_left_press)
    style.AddObserver("LeftButtonReleaseEvent", on_left_release)
    style.AddObserver("MouseMoveEvent", on_mouse_move)

    return style


class CameraMixin:
    """Rotation center and reset of the shared camera"""

    def _data_anchor(self):
        """Point on the earth surface at the bottom center of the data"""
        x_rad = math.radians(self.ctx.setup.center[0])
        y_rad = math.radians(self.ctx.setup.center[1])
        cos_y_rad = math.cos(y_rad)
        xs = EARTH_RADIUS * math.sin(x_rad) * cos_y_rad
        ys = EARTH_RADIUS * math.sin(y_rad)
        zs = EARTH_RADIUS * math.cos(x_rad) * cos_y_rad
        return (xs, ys, zs)

    def _rotation_center(self):
        if self.ctx.setup.camera_focus == "earth":
            return (0, 0, 0)
        return self._data_anchor()

    @controller.add("reset_camera")
    def _reset_camera(self):
        xs, ys, zs = self._data_anchor()
        camera = self.renderer.active_camera
        camera.position = (xs * 1000, ys * 1000, zs * 1000)
        camera.view_up = EARTH_AXIS
        if self.ctx.setup.camera_focus == "earth":
            camera.focal_point = (0, 0, 0)
            camera.OrthogonalizeViewUp()
            r = EARTH_RADIUS
            self.renderer.ResetCamera(-r, r, -r, r, -r, r)
        else:
            camera.focal_point = (xs, ys, zs)
            camera.OrthogonalizeViewUp()
            self.renderer.ResetCamera(self.outline_actor.bounds)

        if self.view_handler:
            self.view_handler.update()

    def _on_camera_focus_change(self, *_):
        self._reset_camera()
