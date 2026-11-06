"""Measure and solve full perspective screen bounds for spherical/cubic envelopes.

Camera coordinates are x right, y down, z forward; pixels have origin top left.
The caller supplies effective Blender intrinsics and envelope-to-camera rotation.
This module does not clip bounds to the image or resize between video frames.
"""
from __future__ import annotations

import math
from itertools import product


def sphere_bounds(center, radius, fx, fy, cx, cy):
    """Exact pixel bounds of a perspective sphere fully in front of the eye."""
    x, y, z = center
    if radius <= 0 or z <= radius:
        raise ValueError("sphere must be positive and fully in front of camera")

    def tangent_limits(t, f, c):
        denominator = z * z - radius * radius
        q = radius * math.sqrt(t * t + denominator)
        return c + f * (t * z - q) / denominator, c + f * (t * z + q) / denominator

    xmin, xmax = tangent_limits(x, fx, cx)
    ymin, ymax = tangent_limits(y, fy, cy)
    return xmin, xmax, ymin, ymax


def cube_corners(center, edge, rotation):
    """Eight camera-coordinate corners, with columns of rotation as cube axes."""
    if edge <= 0:
        raise ValueError("cube edge must be positive")
    return [tuple(center[i] + sum(rotation[i][j] * v[j] for j in range(3))
                  for i in range(3))
            for v in product((-edge / 2, edge / 2), repeat=3)]


def cube_bounds(center, edge, rotation, fx, fy, cx, cy):
    """Exact bounds of a projected convex cube entirely before camera plane."""
    corners = cube_corners(center, edge, rotation)
    if any(v[2] <= 0 for v in corners):
        raise ValueError("cube crosses camera plane")
    projected = [(cx + fx * v[0] / v[2], cy + fy * v[1] / v[2]) for v in corners]
    return (min(v[0] for v in projected), max(v[0] for v in projected),
            min(v[1] for v in projected), max(v[1] for v in projected))


def mesh_vertex_bounds_camera(vertices_camera, fx, fy, cx, cy):
    """Full projected bounds of supplied Nx3 camera-coordinate mesh vertices.

    This measures geometric silhouette extent, including off-frame vertices.
    Vertices must be in front of the eye. It does not perform visibility or
    near-plane clipping; a rasterized boundary may differ by about a pixel.
    """
    import numpy as np

    v = np.asarray(vertices_camera, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or len(v) == 0:
        raise ValueError("vertices_camera must be a nonempty Nx3 array")
    if not np.isfinite(v).all() or np.any(v[:, 2] <= 0):
        raise ValueError("mesh vertices must be finite and in front of camera")
    x = cx + fx * v[:, 0] / v[:, 2]
    y = cy + fy * v[:, 1] / v[:, 2]
    return float(x.min()), float(x.max()), float(y.min()), float(y.max())


def measurement(bounds, width, height):
    """Full bounds and four edge overflows, without cropping to the frame."""
    if width <= 0 or height <= 0:
        raise ValueError("resolution must be positive")
    xmin, xmax, ymin, ymax = bounds
    if not all(math.isfinite(v) for v in bounds) or xmin > xmax or ymin > ymax:
        raise ValueError("invalid projection bounds")
    return {
        "bounds_px": list(bounds),
        "width_px": xmax - xmin, "height_px": ymax - ymin,
        "width_percent": 100 * (xmax - xmin) / width,
        "height_percent": 100 * (ymax - ymin) / height,
        "overflow_px": {"left": max(0, -xmin), "right": max(0, xmax - width),
                        "top": max(0, -ymin), "bottom": max(0, ymax - height)},
    }


def solve_size(height_at_size, target_percent, image_height, safe_upper,
               iterations=72):
    """Find one physical size for target projected height by bisection.

    The caller must keep geometry before the camera and verify monotonicity over
    its bracket. The solved size is held constant across video frames.
    """
    if not 0 < target_percent <= 100 or image_height <= 0 or safe_upper <= 0:
        raise ValueError("invalid target or size bracket")
    target = target_percent * image_height / 100
    if height_at_size(safe_upper) < target:
        raise ValueError("target not reached within safe bracket")
    lo, hi = 0., safe_upper
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if height_at_size(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def max_height_for_views(size, bounds_for_views):
    """Maximum across supplied views; sampling alone is no continuous proof."""
    values = [bounds(size)[3] - bounds(size)[2] for bounds in bounds_for_views]
    if not values:
        raise ValueError("at least one view is required")
    return max(values)


def max_safe_size_for_views(bounds_for_views, width, height, safe_upper,
                            margin_px=0, iterations=72):
    """Largest sampled-view size fitting all four image edges with a margin.

    Requires that the supplied bounds functions stay valid and that increasing
    size cannot make an already overflowing view fit again within the bracket.
    This is a sampled-view check, not a continuous-turn guarantee.
    """
    if not bounds_for_views or width <= 0 or height <= 0 or safe_upper <= 0:
        raise ValueError("invalid views, frame or size bracket")
    if margin_px < 0 or margin_px * 2 >= min(width, height):
        raise ValueError("invalid image margin")

    def fits(size):
        for bounds in bounds_for_views:
            xmin, xmax, ymin, ymax = bounds(size)
            if (xmin < margin_px or xmax > width - margin_px or
                    ymin < margin_px or ymax > height - margin_px):
                return False
        return True

    if fits(safe_upper):
        return safe_upper
    lo, hi = safe_upper * 1e-12, safe_upper
    if not fits(lo):
        raise ValueError("envelope center is outside safe image area")
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if fits(mid):
            lo = mid
        else:
            hi = mid
    return lo


def measure_blender_envelope(scene, camera, kind, center_world, physical_size,
                             rotation_world=None):
    """Blender adapter: measure actual render-camera geometry in pixels.

    ``physical_size`` is sphere diameter or cube edge. ``rotation_world`` is a
    3x3 Blender mathutils Matrix of cube-local axes in world coordinates;
    omitted means world-aligned cube. Actual resolution, pixel aspect, sensor
    fit and lens shift are read through Blender's camera projection.
    """
    from mathutils import Matrix, Vector
    from bpy_extras.object_utils import world_to_camera_view

    if camera.data.type != "PERSP":
        raise ValueError("only perspective Blender cameras are supported")
    width = round(scene.render.resolution_x * scene.render.resolution_percentage / 100)
    height = round(scene.render.resolution_y * scene.render.resolution_percentage / 100)
    camera_axes = camera.matrix_world.to_3x3()
    front = camera.location + camera_axes @ Vector((0, 0, -1))

    def screen(point):
        uv = world_to_camera_view(scene, camera, point)
        return uv.x * width, (1 - uv.y) * height

    cx, cy = screen(front)
    fx = screen(front + camera_axes @ Vector((1, 0, 0)))[0] - cx
    fy = screen(front + camera_axes @ Vector((0, -1, 0)))[1] - cy
    local = camera.matrix_world.inverted() @ Vector(center_world)
    center_camera = (local.x, -local.y, -local.z)
    if kind == "sphere":
        bounds = sphere_bounds(center_camera, physical_size / 2,
                               fx, fy, cx, cy)
    elif kind == "cube":
        rot = camera_axes.inverted() @ (
            rotation_world if rotation_world is not None else Matrix.Identity(3))
        rows = (tuple(rot[0]), tuple(-v for v in rot[1]),
                tuple(-v for v in rot[2]))
        bounds = cube_bounds(center_camera, physical_size, rows,
                             fx, fy, cx, cy)
    else:
        raise ValueError("kind must be 'sphere' or 'cube'")
    result = measurement(bounds, width, height)
    result.update({"physical_size": physical_size,
                   "physical_measure": "sphere_diameter" if kind == "sphere" else "cube_edge",
                   "resolution_px": [width, height],
                   "camera_intrinsics_px": [fx, fy, cx, cy]})
    return result


def measure_blender_mesh(scene, camera, vertices_world):
    """Measure uncropped projection of supplied Blender-world mesh vertices.

    Supply evaluated, statically oriented vertices for the exact renderer pose.
    The function returns the same width/height/overflow schema as envelope
    measurement; it does not alter the source mesh or object transform.
    """
    import numpy as np
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    if camera.data.type != "PERSP":
        raise ValueError("only perspective Blender cameras are supported")
    width = round(scene.render.resolution_x * scene.render.resolution_percentage / 100)
    height = round(scene.render.resolution_y * scene.render.resolution_percentage / 100)
    axes = camera.matrix_world.to_3x3()
    front = camera.location + axes @ Vector((0, 0, -1))

    def screen(point):
        uv = world_to_camera_view(scene, camera, point)
        return uv.x * width, (1 - uv.y) * height

    cx, cy = screen(front)
    fx = screen(front + axes @ Vector((1, 0, 0)))[0] - cx
    fy = screen(front + axes @ Vector((0, -1, 0)))[1] - cy
    v = np.asarray(vertices_world, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or len(v) == 0:
        raise ValueError("vertices_world must be a nonempty Nx3 array")
    inv = np.asarray(camera.matrix_world.inverted(), dtype=float)
    local = np.column_stack((v, np.ones(len(v)))) @ inv.T
    camera_vertices = np.column_stack((local[:, 0], -local[:, 1], -local[:, 2]))
    result = measurement(mesh_vertex_bounds_camera(camera_vertices, fx, fy, cx, cy),
                         width, height)
    result.update({"resolution_px": [width, height],
                   "camera_intrinsics_px": [fx, fy, cx, cy],
                   "vertex_count": len(v)})
    return result
