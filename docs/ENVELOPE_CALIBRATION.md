# Independent sphere and cube projection height

Current status: owner accepted `turn_max` placement calculation on 2026-11-07. See [the acceptance record](PLACEMENT_ACCEPTANCE.md); prior preference/review wording below describes the historical comparison. Blender4.2/OptiX integration remains separate.

The main branch preserves the checked calibration component and the
explanations needed to recover its behavior. It is not a production renderer
release. Cube turn-maximum sizing is accepted by the owner; the visual comparison is preserved as its rationale. Blender 4.2/OptiX integration is checked separately.

## Files and descriptive names

| Executable | Purpose | Earlier workspace runner name |
| --- | --- | --- |
| `scripts/calibrate_sphere_projection_height.py` | Solve sphere diameter so its full silhouette reaches a requested fraction of image height | `run_sphere.py` |
| `scripts/calibrate_cube_projection_height.py` | Solve cube edge so its full projection reaches that fraction in a reference view or as the sampled turn maximum | `run_cube.py` |

The scripts output calibration JSON and expose a `calibrate_and_fit` function
for a renderer. They do not import or render a mesh from the CLI. The complete
checked v1.0.0 implementation is included under `src/envelope_height_calibration/`;
its Python files and source manifest are byte-identical to the original local
package. `src/verified_pipeline/envelope_runner.py` verifies those hashes and
connects the two named entry points to it. Parent/core/Tools repositories are
not runtime dependencies. Blender provides `bpy`, `mathutils` and NumPy;
outside Blender, the mesh-fit API requires NumPy (`.[geometry]`).

## How the sphere fit works

1. Apply the dataset's fixed orientation to source vertices `v_i`.
2. Find the midpoint `c` of their 3D bounding box, coordinate by coordinate:
   `c_j = (min(v_ij) + max(v_ij))/2`.
3. Find the farthest vertex distance `r = max_i ||v_i-c||`.
   A sphere of radius `r` centered at `c` encloses the source mesh. This is a
   deterministic enclosing sphere, not a minimum enclosing sphere.
4. Solve the target physical sphere radius `R` from its **full projected
   silhouette height** in the actual camera.
5. Use one uniform scale `s = R/r` and transform
   `world_vertex = target_center + s × (v_i-c)`.

Every vertex then has distance at most `R` from the target centre. Uniform
scaling preserves shape and vertex order. Sphere convexity also contains the
faces between those vertices. The source mesh is not edited on disk.

For a camera aimed at the sphere centre with square pixels, the radius can be
explained with a tangent triangle. Let `d` be camera-to-centre distance,
`p` the target fraction (70% means 0.70), `W,H` pixel dimensions and `theta`
horizontal FOV. The pixel focal length is:

```text
f = W / (2 tan(theta/2))
t = (p H) / (2 f)
alpha = atan(t)             # half-angle of the sphere's visible silhouette
R = d sin(alpha)           # tangent triangle, right angle at the sphere surface
  = d t / sqrt(1+t²)
D = 2R
s = R/r
```

The silhouette angle uses tangency to the sphere surface. It is not measured
by projecting the segment between the vertical poles. At 960×540, FOV 60°,
distance 1.58 m and target 70%, the full silhouette height is 378 px and the
physical diameter is about 0.7004954 m. The mesh itself need not reach 70%.

The actual preserved code reads the effective Blender camera projection and
uses bisection over exact sphere silhouette bounds to solve the diameter.
The formula above explains the centered-camera case; it is not a replacement
implementation that ignores the actual Blender camera.

## How the cube fit differs

Use the same source centering convention, but compute the source cube half-edge
`b = max_i,j |v_ij-c_j|`. Solve target cube edge `a` from the full projected
vertical span of all eight corners. The uniform mesh scale is `s=a/(2b)`.
Sphere diameter and cube edge are solved independently; `a=D` is not enforced.
The two fits may therefore give different projected mesh sizes.

For `reference`, the first supplied view controls the height. For `turn_max`,
the maximum over supplied views controls it. One solved size/mesh scale is kept
for the entire turn. With the centered fixed sphere, yaw cannot change its
silhouette; for the cube it can. [Compare the cube rules](CUBE_SIZING_RULES.md).

## Commands from a standalone clone

```bash
blender -b --factory-startup --python scripts/calibrate_sphere_projection_height.py -- \
  --target 50 70 90 --mode reference --output /tmp/sphere_NEW.json

blender -b --factory-startup --python scripts/calibrate_cube_projection_height.py -- \
  --target 50 70 90 --mode turn_max --yaw-step 1 --output /tmp/cube_NEW.json
```

Specify `--mode` explicitly. The named scripts reject kind overrides. Results
include physical size, achieved percentage, all selected view bounds and
optional edge-overflow measurements. Overflow does not silently shrink the
target. A 1° step is a sampled maximum, not a continuous-angle proof. Outputs
are refused if they already exist.

`calibrate_and_fit(scene, camera, oriented_vertices, target_percent,
rotations_world, **options)` in either named script returns `calibration` and
`placement`, including centre translation and uniform scale. Apply that exact
transform to the mesh. Static orientation must precede fitting. Near/far
clipping, renderer import/GT mapping, lens distortion and full video timing
are not accepted by this calibration component.

## Evidence and recovery

- [Original independent sphere/cube visual examples](images/sphere_vs_cube_50_70_90_a380.png).
- [Cube rule comparison](CUBE_SIZING_RULES.md), with new example scripts.
- [Source provenance and checked records](evidence/envelope_calibration/README.md).

Preserve code/input/output identities, the actual measured target, assumptions,
choice rationale, comparisons and pending approvals whenever this method is
changed. A later correction must link to superseded evidence. Do not claim
acceptance solely from copied source or a successful import.
