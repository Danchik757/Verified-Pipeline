# Accepted placement calculation — 2026-11-07

The owner accepts independent sphere/cube calibration using the maximum full projected envelope height over the turn (`turn_max`). One mesh scale is held fixed across frames. The accepted code revision is `5d675f418f6e8b866071ddd92504dc7115f3efe3`; calibration core version is 1.0.0. Exact source hashes are pinned in [ACCEPTED_PLACEMENT.json](ACCEPTED_PLACEMENT.json). Use the descriptive sphere/cube scripts with explicit `--mode turn_max --yaw-step 1`.

The currently checked turn sampling is yaw 0–359 degrees at 1-degree steps; this is a sampled maximum. Final frame-angle scheduling must use its actual angle list or explicitly revalidate sampling. Sphere yaw invariance holds for the fixed centered camera.

Acceptance checked current source/evidence hashes, all six comparison-frame hashes, and all 12 saved exact calibration comparisons. No additional render was needed for this policy-only acceptance.

Placement calculation is accepted. Production Blender4.2/OptiX renderer connection remains a separate stage. Main merge, parent pointer updates and target-engine execution are not implied by this record. The next scientific discussion can proceed to lamp geometry (Q06).

Git integration completed on 2026-11-07: PR2 fast-forwarded into main, all intermediate commits preserved. Annotated tag `placement-geometry-v1.0.0` pins the accepted implementation; rejected common-scale history is retained under `archive/common-sphere-diagnostic-2026-11-07`. Both finished feature branches were removed after remote tags were verified.
