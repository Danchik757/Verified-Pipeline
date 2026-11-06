# Envelope height calibration — fixed v1.0.0

This folder is the reusable, versioned implementation of the owner's current sizing definition: **the full perspective projection of a sphere or cube has the requested vertical extent as a percentage of image height**. The measurement uses the complete uncropped projection, including parts outside the image frame. Frame overflow is reported, not used to change the solved size.

## Files

- [`geometry.py`](geometry.py): exact perspective sphere-silhouette bounds, projected cube-corner bounds, image percentages and four edge overflows; mesh-projection helpers are retained for diagnostics.
- [`calibration.py`](calibration.py): `calibrate_height` solves the physical sphere diameter or cube edge; `fit_mesh_to_envelope` returns the uniform transform after dataset-specific static orientation.
- [`run_blender.py`](run_blender.py): standalone Blender entry point; supports target levels, camera settings, `reference` or `turn_max`, yaw step and JSON output.
- [`release_manifest.json`](release_manifest.json): version, source-file SHA256 and validation identities. Verify this before reusing a copied package. New scientific changes require a distinct version and fresh validation; do not silently reinterpret v1 results.

From the workspace root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python Parameters/experiments/envelope_height_calibration/run_blender.py -- \
  --kind both --target 50 70 90 --mode reference \
  --output /path/to/new_calibration.json
```

The script refuses to overwrite its output. For a fixed video scale, use `--mode turn_max --yaw-step 1`; the reported maximum is over those sampled yaw angles only. The returned `physical_size_m` is the sphere diameter or cube edge. For a renderer import:

```python
from envelope_height_calibration import calibrate_height, fit_mesh_to_envelope

result = calibrate_height(scene, camera, "sphere", 70, views,
                          safe_upper_m=1.0, mode="turn_max")
placement = fit_mesh_to_envelope(oriented_vertices, "sphere",
                                 result["physical_size_m"])
```

Keep the same mesh transform for every video frame. Pass the actual Blender camera, final render resolution and any cube rotations. The source mesh must already have the dataset's static orientation before fitting. The package assumes a perspective camera with sphere/cube fully before the eye and does not account for lens distortion, near/far clipping, occlusion or mesh–GT provenance. Height alone does not ensure full frame containment; inspect `overflow_px` separately.

**Scientific scope:** The definition and calculation of full projected envelope height are fixed here. The [six CODE-013 collages](../../../@GPT-job/chats/render-ablation--01a18205/outputs/IMAGE_LIBRARY/08_calibrated_envelope_height/README.md) show 50/70/90% examples. The active D-023 decision sets sphere diameter equal to surrounding-cube edge and uses one sphere-derived mesh transform. Independent sphere/cube sizing in the comparison collages is diagnostic. The eventual experiment must still choose whether the percentage applies in a reference view or to the sampled turn maximum. Production Blender4.2/OptiX integration and full-video checks are separate.

The former import paths one directory above are compatibility wrappers; this folder is the canonical v1 source. Blender4.1.1 reproduced all 12 prior sphere/cube 50/70/90% calibrations exactly in the reference and turn-max modes. The checks are executor checks, not independent review.
