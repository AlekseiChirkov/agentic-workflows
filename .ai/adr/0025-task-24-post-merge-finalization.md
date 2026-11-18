# ADR-0025: Evidence-backed post-merge finalization

## Status
Accepted

## Date
2026-11-17

## Decision
Add a separately invoked finalization phase with mandatory cleanup and only a dry-run flag. Use deterministic safety helpers for evidence, recovery and archival; Git mutations remain explicit and hook-governed. Invocation authorizes only verified resources of the resolved task. Preserve prior validation semantics and original audit records. Extend Git ownership, current-location pointer edits and required local-helper usage narrowly. Staged sync generates provider outputs without live installation or unrelated project changes.

## Context and Alternatives
The owner chose one phase with helpers over instruction-led children. Markdown remains the workflow orchestrator; local mechanics are executable because deletion, interrupted writes and archival need behavioral guarantees. This extends the optional-helper restriction of ADR-0001 only for finalization mutations. The frozen validator inventory remains unchanged; new acceptance suites live in scripts and run from sync preflight.

## Consequences
Missing required evidence or helpers blocks mutation. Ordinary local deletion refusal leaves finalization incomplete. Deployment remains independently unverified unless established by dated evidence. Original Git/TDD/decision records remain unchanged; only current location pointers and mechanical links may be relocated with original snapshots retained. No automatic merge, publication or live consumer deployment is introduced. Before deletion authorization, self-contained recovery packs preserve original Git objects independently of branch reachability and garbage collection; explicit commands create the files, and isolated object-store verification checks their immutable digests, original tips and closure.

The Git-policy exception is a separately anchored canonical section with explicit precedence over fallback deletion/lease rows; the existing four-value Enforcement table vocabulary and restack semantics remain unchanged. This distinguishes delivered post-integration cleanup from the separately planned temporary-child exception without mislabeling enforcement.

## Verification
Verified 2026-11-18 on clean source `9e5b062a22cf919d39d86f1e7c38d62ac9d4fd23`: supported isolated sync completed with the full validator (725 passed, 0 failed, 2 optional private-pattern skips), then all 156 standalone cases (77 core, 23 safety, 56 workflow), and generated 188 provider files. Independent leaf, contract, fixture-integrity and realistic two-repository forward reviews passed. Prior failed runs and repairs remain in task state; no source merge, live installation or deployment is claimed. Actual runtime was Python 3.14.4, Git 2.53.0 and Bash 5.3.9; Python 3.11 compatibility was reviewed statically and ShellCheck was unavailable. See the task Final Verification record for exact source/log provenance and limits.
