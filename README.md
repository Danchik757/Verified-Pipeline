# Verified-Pipeline

Public source for a reproducible mesh-stimulus experiment pipeline. The first target is rendering-parameter ablation using SalFoM predictions; the intended later route reuses the same stimulus, placement and evaluation contracts with mouse observations collected through Toloka.

## Current status

The common-sphere placement feature is under scope correction: it does not
implement the owner's requested independent projection targets. Its local
geometry checks do not establish acceptance as the framing method.

This repository is an **implementation scaffold**. Its stage-identity code is tested locally, and its [common mesh placement geometry](docs/PLACEMENT.md) has bounded diagnostic verification. It cannot yet render a video, run a trained SalFoM model, project predictions, score ground truth, or collect mouse data. See [validation levels](docs/VALIDATION.md) and the [candidate intake ledger](intake/CANDIDATES.md).

`Verified-Pipeline` must become independently runnable. Existing Tools and core code are reference candidates for comparison, not runtime dependencies or automatic sources to copy. A scientific script enters this repository only after its behavior, inputs, outputs and failure cases have been checked against the current contract. This repository does not bundle raw meshes, GT, model weights, videos, or participant data.

## Local contract check

Python 3.10+ and only the standard library are required for the current command:

```bash
PYTHONPATH=src python3 -m verified_pipeline fingerprint examples/stage-spec.synthetic.json
python3 -m unittest discover -s tests -v
```

The fingerprint command validates a *fully resolved* stage specification and returns a deterministic SHA-256 ID. It is an identity check, not a claim that the configuration is scientifically sound. `check-source PATH SHA256` verifies bytes of an external candidate file before intake.

## Boundaries

- [Architecture and ownership](docs/ARCHITECTURE.md)
- [Validation and promotion rules](docs/VALIDATION.md)
- [Candidate code intake](intake/CANDIDATES.md)
- [Local contributor/agent instructions](AGENTS.md)

Code and schemas belong here. Large or private inputs and generated outputs belong outside Git in versioned run directories. The parent `Mesh-Saliency-Projection` repository may pin an exact commit through its root-level `Verified-Pipeline/` submodule link; a standalone clone must not require that parent to run.

No license has been granted for copying third-party sources or pretrained weights into this repository. A repository-wide license and upstream redistribution rights must be settled before such material is published.
