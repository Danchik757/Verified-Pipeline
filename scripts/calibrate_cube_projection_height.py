"""Solve cube edge for a requested full projected image-height percentage."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from verified_pipeline.envelope_runner import calibrate_and_fit as _fit, run


def calibrate_and_fit(scene, camera, oriented_vertices, target_percent,
                      rotations_world, **options):
    return _fit("cube", scene, camera, oriented_vertices, target_percent,
                rotations_world, **options)


if __name__ == "__main__":
    run("cube")
