# Working rules for Verified-Pipeline

Read `README.md`, `docs/ARCHITECTURE.md`, `docs/VALIDATION.md`, and `intake/CANDIDATES.md` before changing scientific code. When working inside the SALIENCY workspace, also follow its root `AGENTS.md` and `@GPT-job` task/chat rules.

- Preserve source data, historical results and other workers' changes. Use scoped branches and one owner per editing scope.
- Record source commit/hash and evidence before reusing an older script. Do not mark a wrapper or copied file validated solely because tests import it.
- Keep accepted runtime code self-contained in this repository. Existing Tools/core scripts may be inspected as candidates, but must not become implicit runtime dependencies. Add each scientific component only after its contract and bounded real-input behavior are verified.
- Separate SalFoM predictions, Toloka mouse observations and author GT by type and provenance. Reject implicit modality conversion.
- Resolve configuration fully before hashing or running. Record code/input/checkpoint identities, frame schedule, coordinate domain, preprocessing and metric/projection versions.
- Reject missing, nonfinite, mismatched or partial results. Resume only after checking content identities; do not overwrite accepted outputs.
- Keep large data, weights, videos, maps, credentials and participant records out of Git. Review licenses before adding upstream source or weights to this public repository.
- Promotion from diagnostic to pilot or release needs recorded evidence for the exact code and environment. Never call an executor self-check independent review.
