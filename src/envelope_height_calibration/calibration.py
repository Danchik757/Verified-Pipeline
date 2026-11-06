"""Size a sphere or cube by its *full projected height* in a Blender camera.

This module can be imported by a renderer. It deliberately does not reduce a
size to keep the envelope inside the frame: directional overflow is reported.
Run as a Blender script with ``--`` options for a standalone calibration.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from .geometry import measure_blender_envelope, solve_size


def fit_mesh_to_envelope(oriented_vertices, kind, physical_size_m):
    """Return the centered mesh transform for a calibrated sphere or cube.

    Apply the dataset's static orientation before calling this function. The
    returned scale is uniform; source vertices are neither mutated nor saved.
    """
    import numpy as np

    v = np.asarray(oriented_vertices, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or len(v) == 0 or not np.isfinite(v).all():
        raise ValueError("oriented_vertices must be a finite nonempty Nx3 array")
    if kind not in ("sphere", "cube") or physical_size_m <= 0:
        raise ValueError("kind sphere/cube and positive physical size required")
    center = (v.min(axis=0) + v.max(axis=0)) / 2
    centered = v - center
    source_size = (2 * np.linalg.norm(centered, axis=1).max()
                   if kind == "sphere" else 2 * np.abs(centered).max())
    if source_size <= 0:
        raise ValueError("source mesh has zero envelope size")
    return {"source_bbox_center": center.tolist(),
            "uniform_scale": float(physical_size_m / source_size),
            "source_envelope_size": float(source_size),
            "target_envelope_size": float(physical_size_m),
            "kind": kind}


def calibrate_height(scene, camera, kind, target_percent, rotations_world,
                     *, center_world=(0, 0, 0), safe_upper_m=1.0,
                     mode="reference"):
    """Return one physical diameter/edge and projected measurements per view.

    ``rotations_world`` is a nonempty sequence of (angle_label, mathutils
    Matrix) entries. In reference mode the first supplied view controls the
    target; in turn_max mode the largest height over supplied views controls
    it. Keep the returned physical size fixed for all rendered frames.
    """
    views = list(rotations_world)
    if not views or kind not in ("sphere", "cube"):
        raise ValueError("nonempty views and kind sphere/cube required")
    if mode not in ("reference", "turn_max"):
        raise ValueError("mode must be reference or turn_max")
    image_height = round(scene.render.resolution_y * scene.render.resolution_percentage / 100)

    def measured(size, rotation):
        return measure_blender_envelope(scene, camera, kind, center_world,
                                        size, rotation)

    def height(size):
        selected = views[:1] if mode == "reference" else views
        return max(measured(size, rotation)["height_px"] for _, rotation in selected)

    size = solve_size(height, target_percent, image_height, safe_upper_m)
    records = []
    for label, rotation in views:
        records.append({"view": label, "projection": measured(size, rotation)})
    selected = records[:1] if mode == "reference" else records
    achieved = max(r["projection"]["height_percent"] for r in selected)
    if abs(achieved - target_percent) > 1e-5:
        raise AssertionError("calibration did not reach requested height")
    return {
        "kind": kind, "mode": mode, "target_percent": float(target_percent),
        "physical_size_m": size,
        "physical_size_name": "sphere_diameter" if kind == "sphere" else "cube_edge",
        "achieved_percent": achieved,
        "views": records,
        "note": "full projected height before clipping; no frame-fit constraint",
    }


def main():
    import sys
    import bpy
    from mathutils import Matrix, Vector

    argsv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=float, nargs="+", default=[50, 70, 90])
    parser.add_argument("--kind", choices=["sphere", "cube", "both"], default="both")
    parser.add_argument("--mode", choices=["reference", "turn_max"], default="reference")
    parser.add_argument("--distance", type=float, default=1.58)
    parser.add_argument("--elevation", type=float, default=18)
    parser.add_argument("--horizontal-fov", type=float, default=60)
    parser.add_argument("--resolution", type=int, nargs=2, default=[960, 540])
    parser.add_argument("--yaw-step", type=int, default=1)
    parser.add_argument("--safe-upper", type=float, default=1.0)
    parser.add_argument("--output", type=Path)
    a = parser.parse_args(argsv)
    if a.distance <= 0 or not 0 < a.horizontal_fov < 180 or not 0 < a.yaw_step <= 360:
        parser.error("invalid camera distance, FOV or yaw step")
    if any(x <= 0 for x in a.resolution):
        parser.error("resolution must be positive")
    if a.output and a.output.exists():
        parser.error("output already exists; refusing overwrite")

    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = a.resolution
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    data = bpy.data.cameras.new("Envelope calibration camera")
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    elev = math.radians(a.elevation)
    camera.location = (0, -a.distance * math.cos(elev), a.distance * math.sin(elev))
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "PERSP"
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = 36
    data.lens = 36 / (2 * math.tan(math.radians(a.horizontal_fov) / 2))
    scene.camera = camera
    bpy.context.view_layer.update()
    angles = list(range(0, 360, a.yaw_step)) if a.mode == "turn_max" else [0]
    views = [(angle, Matrix.Rotation(math.radians(angle), 3, "Z")) for angle in angles]
    kinds = ["sphere", "cube"] if a.kind == "both" else [a.kind]
    results = [calibrate_height(scene, camera, kind, target, views,
                                safe_upper_m=a.safe_upper, mode=a.mode)
               for kind in kinds for target in a.target]
    payload = {"camera": {"distance_m": a.distance,
                          "elevation_deg": a.elevation,
                          "horizontal_fov_deg": a.horizontal_fov,
                          "resolution_px": a.resolution,
                          "yaw_step_deg": a.yaw_step},
               "blender_version": bpy.app.version_string, "results": results}
    rendered = json.dumps(payload, indent=2) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered)
        print(a.output.resolve())
    else:
        print(rendered)


if __name__ == "__main__":
    main()
