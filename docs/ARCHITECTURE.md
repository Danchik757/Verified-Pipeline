# Architecture and code ownership

The parent `Mesh-Saliency-Projection` owns authoritative projection algorithms, metrics and historical benchmark contracts. The existing `Mesh-Saliency-Tools` checkout owns its renderer until a validated transfer or replacement is agreed. Verified-Pipeline owns new experiment contracts, orchestration, dependency adapters, run identity, validation reports and eventual Toloka observation intake.

The intended flow is:

```text
resolved scene + eligible mesh
  -> renderer + frame/placement/video manifest
  -> observation provider (SalFoM map or Toloka mouse events)
  -> core projection adapter -> domain-aware map
  -> core metric adapter + eligible GT -> per-model results
  -> block selector -> frozen next-block reference
```

Every arrow needs a versioned schema, identity check, and failure behavior. The current repository implements only the stage identity contract. No adapter is implemented yet.

One `Observation` contract will identify source kind, frame/time, coordinates, preprocessing, domain and source hashes. The two providers must stay distinguishable in results; a SalFoM prediction must never be mislabeled as human gaze. The Toloka provider will be implemented after the rendering and evaluation route is validated.

The parent submodule is a Git link to a commit and URL, not a filesystem symlink. Code must run if Verified-Pipeline is cloned independently; dependency roots are explicit configuration, never hard-coded relative paths into the parent.
