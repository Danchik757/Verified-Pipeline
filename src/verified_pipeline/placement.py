"""Common sphere-derived mesh placement (D-023/D-024).

Inputs are already in the dataset's static orientation. The camera optical
axis passes through the envelope centre, pixels are square, and FOV is
horizontal. Geometry is returned without mutating the source mesh.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class Placement:
    source_center: tuple[float, float, float]
    source_radius: float
    scale: float
    sphere_diameter_m: float
    cube_edge_m: float
    target_height_percent: float
    projected_sphere_height_px: float

    def transform(self, vertex: Iterable[float]) -> tuple[float, float, float]:
        """Map an oriented source vertex to world coordinates about (0,0,0)."""
        v = tuple(vertex)
        if len(v) != 3 or not all(math.isfinite(x) for x in v):
            raise ValueError("vertex must contain three finite coordinates")
        return tuple((v[i] - self.source_center[i]) * self.scale for i in range(3))


def projected_sphere_height_px(diameter_m: float, distance_m: float,
                               horizontal_fov_deg: float, width_px: int) -> float:
    """Exact vertical tangent-to-tangent extent of a centered sphere."""
    if not (math.isfinite(diameter_m) and math.isfinite(distance_m)
            and math.isfinite(horizontal_fov_deg) and width_px > 0
            and 0 < diameter_m < 2 * distance_m
            and 0 < horizontal_fov_deg < 180):
        raise ValueError("invalid sphere or centered perspective camera")
    focal_px = width_px / (2 * math.tan(math.radians(horizontal_fov_deg) / 2))
    radius = diameter_m / 2
    return 2 * focal_px * radius / math.sqrt(distance_m**2 - radius**2)


def diameter_for_height(target_percent: float, distance_m: float,
                        horizontal_fov_deg: float, width_px: int,
                        height_px: int) -> float:
    """Solve D from the full uncropped perspective silhouette height / H."""
    if not (math.isfinite(target_percent) and 0 < target_percent <= 100
            and math.isfinite(distance_m) and distance_m > 0
            and math.isfinite(horizontal_fov_deg) and 0 < horizontal_fov_deg < 180
            and isinstance(width_px, int) and width_px > 0
            and isinstance(height_px, int) and height_px > 0):
        raise ValueError("invalid target or centered perspective camera")
    focal_px = width_px / (2 * math.tan(math.radians(horizontal_fov_deg) / 2))
    tangent = target_percent * height_px / (200 * focal_px)
    return 2 * distance_m * tangent / math.sqrt(1 + tangent**2)


def place_in_sphere_and_cube(oriented_vertices: Iterable[Iterable[float]],
                             target_percent: float, distance_m: float,
                             horizontal_fov_deg: float, width_px: int,
                             height_px: int) -> Placement:
    """Fit once to a sphere; the concentric cube has edge equal to diameter.

    The source centre is the midpoint of the oriented mesh's axis-aligned
    bounding box. The radius is the largest Euclidean vertex distance from
    that centre. This is a deterministic enclosing sphere, not a minimum
    enclosing sphere. Keep the same returned transform for both guides.
    """
    vertices = [tuple(v) for v in oriented_vertices]
    if not vertices or any(len(v) != 3 or not all(math.isfinite(x) for x in v)
                           for v in vertices):
        raise ValueError("oriented mesh must have finite Nx3 vertices")
    center = tuple((min(v[i] for v in vertices) + max(v[i] for v in vertices)) / 2
                   for i in range(3))
    radius = max(math.dist(v, center) for v in vertices)
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("mesh must have positive enclosing radius")
    diameter = diameter_for_height(target_percent, distance_m,
                                   horizontal_fov_deg, width_px, height_px)
    return Placement(center, radius, diameter / (2 * radius), diameter,
                     diameter, target_percent,
                     projected_sphere_height_px(diameter, distance_m,
                                                horizontal_fov_deg, width_px))


def projected_cube_bounds_px(edge_m: float, distance_m: float,
                             horizontal_fov_deg: float, width_px: int,
                             height_px: int,
                             cube_to_camera: Iterable[Iterable[float]]) -> tuple[float, float, float, float]:
    """Full (left, right, top, bottom) projection of cube corners before crop.

    Camera coordinates: X right, Y down, Z forward. The supplied 3x3 matrix
    rotates cube-local axes into that camera basis. The centre is (0,0,d).
    """
    matrix = [tuple(row) for row in cube_to_camera]
    if (len(matrix) != 3 or any(len(row) != 3 or not all(math.isfinite(x) for x in row)
                                for row in matrix) or not math.isfinite(edge_m)
            or edge_m <= 0 or not math.isfinite(distance_m) or distance_m <= 0
            or not 0 < horizontal_fov_deg < 180 or width_px <= 0 or height_px <= 0):
        raise ValueError("invalid cube or camera")
    for i in range(3):
        for j in range(3):
            dot = sum(matrix[i][k] * matrix[j][k] for k in range(3))
            if abs(dot - (1.0 if i == j else 0.0)) > 1e-5:
                raise ValueError("cube_to_camera must be an orthonormal rotation")
    determinant = (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
                   - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
                   + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))
    if abs(determinant - 1.0) > 1e-5:
        raise ValueError("cube_to_camera must be a proper rotation")
    focal_px = width_px / (2 * math.tan(math.radians(horizontal_fov_deg) / 2))
    xy = []
    for x in (-edge_m / 2, edge_m / 2):
        for y in (-edge_m / 2, edge_m / 2):
            for z in (-edge_m / 2, edge_m / 2):
                point = (x, y, z)
                transformed = [sum(matrix[i][j] * point[j] for j in range(3))
                               for i in range(3)]
                depth = distance_m + transformed[2]
                if depth <= 0:
                    raise ValueError("cube intersects or crosses camera plane")
                xy.append((width_px / 2 + focal_px * transformed[0] / depth,
                           height_px / 2 + focal_px * transformed[1] / depth))
    return (min(x for x, _ in xy), max(x for x, _ in xy),
            min(y for _, y in xy), max(y for _, y in xy))


def bounds_report(bounds: tuple[float, float, float, float],
                  width_px: int, height_px: int) -> dict:
    """Report uncropped occupancy and overflow; never resize to hide overflow."""
    left, right, top, bottom = bounds
    if (width_px <= 0 or height_px <= 0 or not all(math.isfinite(x) for x in bounds)
            or left > right or top > bottom):
        raise ValueError("invalid bounds or frame")
    return {"height_percent": 100 * (bottom - top) / height_px,
            "overflow_px": {"left": max(0., -left),
                            "right": max(0., right - width_px),
                            "top": max(0., -top),
                            "bottom": max(0., bottom - height_px)}}
