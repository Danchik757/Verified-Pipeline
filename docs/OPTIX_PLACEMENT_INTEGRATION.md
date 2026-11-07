# Placement connection to Blender 4.2 / OptiX

Bounded integration check passed on 2026-11-07. The accepted independent
sphere/cube placement calculation was connected to a diagnostic Blender
scene, rendered on OptiX, encoded to short videos and verified after decoding.
This establishes this component connection, not the entire ablation pipeline.

## Exact scope and result

- Source snapshot: `120e19f50e8affe90620f4075176cfe89f483d35`, retained by
  annotated tag `placement-geometry-v1.0.0`; calibration core 1.0.0 unchanged.
- Blender 4.2.15 LTS on one NVIDIA RTX 3090, driver 580.159.03. Cycles GPU,
  OptiX enabled; CPU and CUDA render devices disabled. Other GPUs were not used.
- SAL3D A380, Spanner and Bunny; source SHA-256 identities preserved.
  Static +90° X orientation, both independent envelope fits, target 70%.
- 6 cases × 12 poses = 72 new 640×360 RGBA renders. Angles 0–330° at 30°
  steps, one fixed scale per case. Calibration used the accepted 360-angle
  turn-max sampling at 1° steps. Diagnostic clip schedule: 6 fps, 2 s, no
  duplicated 360° endpoint. This does not finalize the SalFoM frame schedule.
- Effective camera: distance 1.580000047 m, horizontal FOV 60.00000167°,
  elevation 18°. Maximum vertex-position difference between the actual
  Blender object matrix and the expected transform: **8.96e-8 m**.
- 12 additional 50/70/90% calibration regressions at the standard 960×540
  calibration resolution passed with **zero physical-size difference** from
  the saved Blender4.1.1 reference values.
- Six FFV1 lossless videos decoded to exactly the original frame pixels in
  the original order. Both lossless and H.264 preview videos have 12 frames,
  640×360 resolution and 6 fps. Retrieved frame/video file hashes also match.

The [machine-readable summary](evidence/optix_placement/summary.json) includes
device selection, camera values, per-video hashes and decoded-frame hashes.
Full frames, videos, logs, calibration records, launch PID, GPU preflight/after
state and input identities are in the SALIENCY workspace evidence package:
`@GPT-job/chats/experiment-pipeline--01a1ab4e/outputs/blender42_optix_integration_20261107/`.
The original remote run and logs remain preserved; large videos are not in Git.

## Reproduce with explicit inputs

Create a new code snapshot and output directory, using external identified
OBJ inputs. The input directory must contain `A380.obj`, `spanner.obj`,
`bunny.obj`, and `inputs.json` mapping those three stem names to their SHA-256.
Source identities are recorded in the summary.

```bash
mkdir -p /tmp/placement_repeat_NEW/code
git archive placement-geometry-v1.0.0 | tar -x -C /tmp/placement_repeat_NEW/code
git rev-parse placement-geometry-v1.0.0^{} > /tmp/placement_repeat_NEW/code/SOURCE_COMMIT

CUDA_VISIBLE_DEVICES=CHOSEN_FREE_GPU blender -b --factory-startup --threads 4 \
  --python examples/check_placement_optix.py -- \
  --code /tmp/placement_repeat_NEW/code --inputs /path/to/identified_inputs \
  --out /tmp/placement_repeat_NEW/results

python3 examples/verify_placement_videos.py --out /tmp/placement_repeat_NEW/results
```

Check current allocation before selecting a device. The scene check rejects
anything except Blender4.2 and exactly one enabled OptiX device. It fails on
pose, size, containment or output mismatches. The video checker requires
ffmpeg/ffprobe with FFV1 and libx264; it checks frame count/rate/resolution and
lossless decoded pixels. Existing files are not a resume signal.

## Limits and next work

The render test uses 8 samples without denoising and diagnostic material/light
settings. These are not the final experiment appearance settings. Targets
50/90% were numerically checked here; the new GPU renders used 70%. There is
no claim of textured-dataset ingestion, full production camera variants,
SalFoM alignment, metrics, AO/light acceptance or a complete ablation run.
The next scientific discussion is Q06 lamp geometry. Further rendering
coverage is needed when those production scene settings are finalized.
