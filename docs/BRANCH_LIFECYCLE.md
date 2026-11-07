# Branch lifecycle and recoverable versions

Owner instruction, 2026-11-07: keep branches purposeful and few, while preserving previous versions.

1. Keep main as the clear entry point for integrated accepted work. State explicitly when accepted code remains only in a feature branch.
2. Inspect existing branches, task ownership and dirty state before creating a branch. Reuse a suitable active task branch. Normally keep one active implementation branch per task/repository. Use commits for progress, corrections and renames; do not create a branch per conversation turn or as a backup.
3. Create a branch for meaningful isolation: unverified scientific code, a coherent change needing review, an incompatible experiment or separate authorized work. Record its purpose, owner, base and intended destination.
4. Record accepted versions with exact commits, evidence and limitations. Use descriptive annotated tags for durable milestones, naming the actual accepted scope. Keep tags immutable and push them when remote recovery is required.
5. After authorized integration, verify that the intended changes are integrated and no unique work remains, then close the PR and remove its finished branch. Reconcile main documentation. Branches are not version archives.
6. Before removing rejected or abandoned work, preserve needed unique versions in a durable tagged commit and record the rejection reason and successor. A bare hash can become unreachable after branch deletion; a Markdown reference alone does not retain Git objects.
7. Cleanup respects task ownership and current authorization. Do not delete other workers' branches, discard dirty work, merge unreviewed changes, force-push or rewrite shared history as routine cleanup. A request to document this rule is not permission to merge or delete existing branches.
8. Recover from a recorded commit/tag in a detached checkout or temporary recovery branch; use a separate worktree when the active checkout is dirty. Compare before restoring and prefer revert/fix commits on shared history. Close temporary recovery branches after preserving their purpose and unique work.

Git preserves source history, not external meshes, weights, outputs or environments. Preserve their identities and recovery instructions with evidence records.
