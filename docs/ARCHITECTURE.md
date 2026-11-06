# Architecture and code ownership

`Verified-Pipeline` owns its accepted scientific implementation and must run independently of `Mesh-Saliency-Projection` and `Mesh-Saliency-Tools`. Those repositories provide historical implementations and test cases to compare against. Their code is not imported at runtime merely because a submodule or local checkout exists. Any reuse requires a separate source, license and behavior review.

The intended flow is:

```text
resolved scene + eligible mesh
  -> renderer + frame/placement/video manifest
  -> observation provider (SalFoM map or Toloka mouse events)
  -> verified projection implementation -> domain-aware map
  -> verified metric implementation + eligible GT -> per-model results
  -> block selector -> frozen next-block reference
```

Every arrow needs a versioned schema, identity check, and failure behavior. The current repository implements only the stage identity contract. No adapter is implemented yet.

One `Observation` contract will identify source kind, frame/time, coordinates, preprocessing, domain and source hashes. The two providers must stay distinguishable in results; a SalFoM prediction must never be mislabeled as human gaze. The Toloka provider will be implemented after the rendering and evaluation route is validated.

The parent submodule is a Git link to a commit and URL, not a filesystem symlink. A standalone clone is the required execution environment for acceptance. External datasets and checkpoints are explicit, versioned inputs; source code from the parent or Tools is not an implicit dependency.
