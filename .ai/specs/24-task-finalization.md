---
status: done
completed_task: task-24-task-finalization
completed_at: 2026-11-18
---

# Post-merge task finalization

## Goal
Close one validated development task after delivery to its intended integration branches, preserving evidence and unfinished product scope.

## Requirements
- REQ-01: Provide `/phase-finalize <task-directory|spec-path> [--dry-run]`; ordinary invocation authorizes mandatory task-scoped cleanup. No phase, cleanup or resume flag.
- REQ-02: Resolve single-repository and recorded umbrella repository sets, archived paths and validation prerequisites without guessing or initializing Git.
- REQ-03: Establish current integration of every recorded branch/stack from original full SHAs, ancestry and authoritative PR receipts; missing refs and closed PRs prove nothing.
- REQ-04: Preserve independent validation, integration, checkout, cleanup, knowledge, archival, audit and deployment outcomes. Deployment is unverified unless dated revision/environment evidence exists.
- REQ-05: Show exact candidate refs, expected tips, protection/worktree checks, commands and recovery; use normal local deletion and expected-SHA remote deletion. Preserve unrelated work and block unsafe operations.
- REQ-06: Keep Git mutations explicit and extend source policy/hooks narrowly; never merge, publish metadata, force-update branches, reset, clean, stash or remove worktrees.
- REQ-07: Persist atomic, locked, revision-checked checkpoints outside moving artifacts; reconcile mutable facts and partial failures on every rerun.
- REQ-08: Reconcile current knowledge, preserving historical decisions, requirements, source/test evidence, original refs, unfinished work and tracking policy.
- REQ-09: Archive task then eligible whole spec without overwrite; preserve manifests, backups, link correctness and old-path resolution across interruptions.
- REQ-10: Dry-run changes no project/Git state or telemetry. Missing required evidence/helpers block mutation; optional tools and telemetry have explicit nonblocking treatment.
- REQ-11: Fit context bootstrap, logging and independent review; existing delivery commands stop before merges and only suggest finalization.
- REQ-12: Support staged synchronization of every provider output without live installation or unrelated project updates.

## Acceptance Criteria
- AC-01: Isolated behavioral tests exercise merge/stack/multi-repository and rewritten-history evidence, including refusal of uncertain delivery.
- AC-02: Changed refs, dirty/diverged trees, protection, worktrees, absent authorization and stale remote leases cannot produce unsafe deletion or successful closure.
- AC-03: Partial cleanup, interrupted journal/archive, destination collisions, old paths and repeat invocation retain recovery evidence and resume safely.
- AC-04: Archive/reference checks preserve requirements, protected Git/TDD fields and all original files; partial multi-phase delivery retains the spec.
- AC-05: Untracked umbrella state remains local; deployment unknown, unavailable optional tooling, logging failures and prior-test limitations are reported accurately.
- AC-06: Scoped hook tests retain existing rails; staged sync checks provider parity and no live writes; required existing checks pass.

## Approved Design
Owner approved the implementation plan on 2026-11-17. One phase with deterministic safety helpers; mandatory cleanup; only --dry-run. Source base is multi-repository support 488edb11b37c3028b720d7de06cfe64cf7fe30c1. No paused audit changes, live destructive tests, PR merging or consumer deployment.

## Change Log

- 2026-11-18: Metadata-only completion after independent implementation review and successful final staged preflight. No requirement or criterion text changed; zero implementation deltas. Merge, task finalization and deployment remain separate outcomes.
