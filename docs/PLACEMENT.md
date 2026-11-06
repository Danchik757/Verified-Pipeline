# Common mesh placement and screen size

Scope correction, 2026-11-06: the owner rejected this common-sphere method as
completion of the requested independent projection calibration. This module
does not independently target cube-envelope or mesh silhouette height. Its
bounded geometry evidence is retained for its stated common-scale contract;
it must not be selected as the accepted framing method by default.

Status: diagnostic verified for the centered perspective geometry contract on
2026-11-06. This is a geometry component, not an accepted video renderer.

## Contract

`verified_pipeline.placement` takes mesh vertices **after** the dataset's
static orientation. It computes the midpoint of their axis-aligned bounding
box, then the maximum Euclidean vertex distance from that midpoint. This is a
deterministic enclosing sphere, not the minimum possible sphere. Source vertex
order and values are unchanged. One uniform scale and centre translation fit
the mesh into the sphere, centered at world origin.

The camera optical axis passes through the sphere centre, square pixels are
used, and the supplied FOV is horizontal. The sphere diameter `D` is solved
from the **full uncropped perspective silhouette height** divided by image
height. For target fraction `p`, camera distance `d`, image width `W` and
height `H`, and horizontal FOV `theta`:

```text
f = W / (2 tan(theta/2))
t = p H / (2 f)
D = 2 d t / sqrt(1 + t²)
```

The concentric cube edge is `a=D`; its diagonal is `sqrt(3) D`. Reuse the
same mesh transform for sphere and cube views. Cube screen height is **not**
calibrated to `p`, and can exceed the image. Report uncropped bounds and edge
overflow; do not silently shrink the geometry. With fixed camera and centre,
the sphere's projected height is invariant to mesh yaw, so a reference frame
and a turn maximum give the same `D`. Cube and mesh extents still vary.

The module does not select dataset orientation, import OBJ, create a Blender
scene, establish video frame timing, or render frames. A renderer must supply
its actual effective resolution/FOV and use the returned transform unchanged.
If the camera no longer points at the envelope centre, this centered-camera
formula is inapplicable and the renderer must reject or use a separately
verified general-camera adapter.

## Verification and limits

- Independent dense numeric tangent search reproduced target sphere heights
  at 50/70/90% for 960×540, 60° FOV and 1.58 m camera distance.
- Four real OBJ inputs (SAL3D Spanner, A380, Bunny; 3DVA A380) were checked at
  all three levels. Each transformed vertex lies inside the sphere and cube.
  SAL3D inputs used the documented static +90° X orientation.
- Blender 4.1.1 camera projection of cube corners at eight yaw angles and
  three sizes agreed with this module's projected bounds within 0.000057 px.
- A sampled 360-angle turn at 1° increments found zero mesh overflow for the
  four inputs. The guide cube can overflow at 70/90%; sampled angles are not
  a continuous-turn proof, and these results do not establish target
  Blender 4.2/OptiX renderer integration.

The detailed input hashes and JSON results are held in the SALIENCY workspace
chat artifact `@GPT-job/chats/experiment-pipeline--01a1ab4e/outputs/placement_validation_20261106/`.
