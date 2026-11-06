# Calibration source and evidence

The included `src/envelope_height_calibration/` is the complete workspace-local
v1.0.0 implementation authored during CODE-013/014. The five source files are
byte-identical to the original release manifest. No core/Tools code is imported
at runtime. The source is project-local Python geometry; NumPy and Blender are
external runtime dependencies, not vendored third-party implementations.

`UPSTREAM_README_v1.md` is the preserved historical documentation snapshot.
Its earlier common-scale a=D planning language is superseded for current
independent modes by [the active method specification](../../ENVELOPE_CALIBRATION.md).
Keep that snapshot as provenance rather than current operating instructions.

| Record | Meaning |
| --- | --- |
| `calibration_comparison.json` | 12 sphere/cube × 50/70/90% × reference/turn-max cases matching archived v1.0.0 results |
| `real_mesh_fit_checks.json` | 24 A380/Bunny/Spanner/Skull fit checks, with source hashes and differences from earlier render transforms |
| `cube_rule_comparison.json` | Six new A380 frames and 360 sampled angles for each of the two cube policies |
| `provenance.json` | Source identities and included artifact hashes |

Prior bounded checks used Blender 4.1.1. The largest real-mesh scale difference
from archived renders was 4.07113e-8. These records establish diagnostic scope,
not target production-video acceptance. Self-checks are not independent review.

To reproduce the calibration checks using only this checkout and Blender:

```bash
python3 examples/verify_envelope_calibration.py \
  --blender /path/to/blender --out /tmp/envelope_check_NEW
```

Input OBJ files for real-mesh or visual repetition remain external; their
identities are preserved in the records. Do not publish private data or silently
replace a source with a different mesh under the same filename.
