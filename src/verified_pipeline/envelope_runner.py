"""Independent fixed-envelope runners over the preserved v1.0.0 geometry."""
from pathlib import Path
import hashlib
import json
import sys

PACKAGE = Path(__file__).resolve().parents[1] / "envelope_height_calibration"


def verify_package():
    manifest = json.loads((PACKAGE / "release_manifest.json").read_text())
    if manifest["version"] != "1.0.0":
        raise RuntimeError("Calibration package v1.0.0 required")
    for name, expected in manifest["files"].items():
        if hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Calibration source hash mismatch: {name}")


def calibrate_and_fit(kind, scene, camera, oriented_vertices, target_percent,
                      rotations_world, **options):
    verify_package()
    from envelope_height_calibration import calibrate_height, fit_mesh_to_envelope
    calibration = calibrate_height(scene, camera, kind, target_percent,
                                   rotations_world, **options)
    placement = fit_mesh_to_envelope(oriented_vertices, kind,
                                     calibration["physical_size_m"])
    placement["target_center_world"] = list(options.get("center_world", (0, 0, 0)))
    return {"calibration": calibration, "placement": placement}


def run(kind):
    verify_package()
    from envelope_height_calibration.calibration import main
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if any(x == "--kind" or x.startswith("--kind=") for x in args):
        raise SystemExit("Envelope kind is fixed by the selected script")
    if not any(x == "--mode" or x.startswith("--mode=") for x in args):
        raise SystemExit("Specify --mode reference or --mode turn_max explicitly")
    sys.argv = [sys.argv[0], "--", "--kind", kind, *args]
    main()
