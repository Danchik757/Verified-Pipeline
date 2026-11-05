# Validation and promotion

Status applies to a specific code commit, dependency revision, input set and environment. A status on one component does not transfer to the whole pipeline.

| Level | Required evidence |
| --- | --- |
| candidate | Origin, intended role, hash, dependencies, license status and known audit findings recorded. |
| diagnostic verified | Controlled input/output cases, failure cases and an independent reference or geometric/numerical comparison for the claimed behavior. |
| pilot validated | Bounded real-data run in the target environment; source and output hashes, complete manifests, frame/coordinate checks, representative visual review, failures and limitations. |
| release ready | Reproducible fresh-clone setup, fixed dependency bundle, all applicable contract tests and pilot gates, clean/resume/invalidation checks, reviewed release report. |

For each old candidate script, collect source identity, reproduce a minimal baseline, test relevant edge cases and compare to independent expected behavior. Then accept, repair, rewrite or reject it. A historical report or a passing import/unit test is supporting evidence, not release acceptance.

The initial `identity.py` logic is a new local utility. Its tests establish deterministic hashing and rejection of malformed stage specs. It has no scientific validation status and does not make the render-to-metric pipeline runnable.

Before public release, check redistribution rights for any imported code or weights. If the renderer or other dependencies remain private, document the restricted reproduction path explicitly.
