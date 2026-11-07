# Review handoff for Verified-Pipeline changes

The owner designated a workspace chat for verification of contributions from
other task executors. The SALIENCY chat registry identifies its location.
Use this handoff for a review of an exact revision; it does not create an
automatic watcher or send messages to other agents.

Supply the task/problem, base and proposed head commit (or PR), intended
behavior and scientific scope, reproduction command, and test results. For
scientific changes include the input/config/environment identities, expected
and observed outputs, evidence location and known limits. Identify any files
or decisions intentionally left to another task.

The reviewer checks the proposed diff against the accepted baseline, verifies
the claimed fix and consequential failure paths, and reproduces relevant
behavior at that revision. For changed stage boundaries, check frame/time,
coordinate/domain and source/manifest consistency with adjacent stages. Use
bounded real inputs and the target environment when the claim requires them.
Record checks actually rerun separately from inherited/producer evidence.

Review records state the exact head and one verdict: verified for stated
scope, changes required, or not verified with the missing check. Record
findings with locations and verify fixes again at their new revision. Do not
declare release readiness from a successful import, an executor self-check or
a diagnostic test of an unrelated component. Follow [validation levels](VALIDATION.md).

Preserve checkpoint commits and existing human attribution. Review is scoped
to the submitted task and does not by itself authorize merging, unrelated scientific
runs, server allocation changes or replacing accepted outputs.
