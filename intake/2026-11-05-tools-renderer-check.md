# Bounded local check: Tools render pipeline

Date: 2026-11-05. Source: `Mesh-Saliency-Tools` local commit `08e04fe086d1bc422c07a8690f368d3117432c6b`; candidate file hashes are in [CANDIDATES.md](CANDIDATES.md). The three candidate code files were clean in that checkout before testing.

## Commands and observations

1. `python3 -m pytest tests/test_render_config.py tests/test_render_engine.py -q` → 94 passed, 10 skipped. Blender-dependent cases were skipped because `MESH_SALIENCY_BLENDER` was unset.
2. With `MESH_SALIENCY_BLENDER=/Applications/Blender.app/Contents/MacOS/Blender` inside the restricted filesystem sandbox, the same suite reported 94 passed, 10 failed. Each Blender subprocess exited `-11` before executing the scene check; a minimal Blender startup also crashed there.
3. A minimal Blender startup outside that sandbox completed with exit 0. Repeating the suite in that environment → **104 passed, 1 deprecation warning**, in 9.56 seconds. Blender reported version 4.1.1. The test suite includes synthetic box scene, preview, video/placement and validation/error cases.

The sandbox failures are an environment limitation, not evidence of ten renderer defects. Conversely, the 104 passes do not establish the owner's target Blender4.2/Cycles/OptiX path, real dataset materials, D-023 common sphere scale, D-024 full-envelope sizing, complete video timing, SalFoM alignment or metric correctness. The files retain **candidate** status. They have not been copied into Verified-Pipeline or accepted for a scientific release.

Next: inspect the code-to-contract differences, obtain target Blender4.2/OptiX environment, and run a bounded real-mesh render/placement and frame-level comparison. Record actual inputs, outputs, hashes and visual checks before status promotion.
