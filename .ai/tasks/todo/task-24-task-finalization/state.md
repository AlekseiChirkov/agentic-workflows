spec_path: .ai/specs/24-task-finalization.md
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Task Analysis
Owner supplied and approved the complete design; requirements are retained in the source specification.

### Assumptions
- Source dependency remains unmerged; implementation starts at its pinned tip without paused audit changes.
- No --allow-pr authorization: all delivery stays local; no push or GitHub mutation.

## Decomposition
decomposition: complete

## Model Selection
selection: complete
Session-default workers; no model or effort override requested. Actual model identity and effort are not independently observed. Preliminary provider recommendations are inapplicable to this explicit default-worker request.

## Solution Design
### Decision
One phase, deterministic evidence/journal/archive helper, explicit Git commands, narrow hook authorization, staged sync. Owner-approved plan of 2026-11-17.
### Scope
One validated development task, all recorded repositories, mandatory cleanup.
### Invariants
No uncertain deletion, no lost protected history, no implicit deployment, no live test mutations.
### Off-limits
Paused audit, consumer installations, PR merging and protected/base publication.
### Acceptance Criteria
The source specification AC-01 through AC-06 apply.

## Subtask Progress
T-01 | Implement evidence, journal and lossless archival mechanics | atomic-tests: green | atomic-execution: complete | atomic-validation: not-started
  last_action: pae-finalize done — implemented evidence-backed finalization, recoverable journal and lossless archival; independent validation pending
  target_files: scripts/check-phase-finalize.py, scripts/phase-finalize.py, scripts/finalization_support.py, scripts/finalization_evidence.py, scripts/finalization_archive.py
  blocker: none
  notes: tdd: integration — real disposable repositories and state/archive boundaries; tdd: red digest — 42 cases in scripts/check-phase-finalize.py, sha256 0b3483d1e1ec0f9ad34049d87130bb4179d911e60454883daff09e24f16bc64b; 42 expected assertion failures, no fixture/import errors; preimplementation test review strengthened supporting validation evidence and allowed current-pointer relocation.
  notes: tdd: test amended — correct protective fixture to canonical orchestrail.protectedBranch and add the missing reviewed multi-repository plan row; assertions and test identities unchanged. Amended set sha256 c054be992a838e99c36c8183ff0ccd745ea30afa67ee3145fcc53dc142c3cb0f; 42 expected failures observed again before the coordinator implementation.
  notes: tdd: test amended — supporting attestations now include executed source assertions, source tips, review provenance and explicit dependency/runtime limitations; six expected attestation-invalid errors exposed the missing fixture provenance. Additional regression cases extend the original frozen set without weakening it. Link regressions were added after their implementation and a temporary link-planning disable produced three expected failures; this replay is recorded separately and is not claimed as original test-first evidence. Original RED outputs and additional regression outputs are retained outside the project in /tmp/finalization-*.txt.
  notes: focused GREEN — 64 tests passed in 16.064s; existing repository-set suite 38 passed in 4.551s; Python syntax and function annotations passed. Final test SHA256 87a0e27682344ef656fc949bd130c38d762ee4bc66e585680d7820ac94bb9ba9. No full validator or staged sync yet.
  branch: feat/task-finalization
  base_branch: feat/multi-repository-spec-run
  base_commit: 488edb11b37c3028b720d7de06cfe64cf7fe30c1
  commits: 16589db73254606caeb15bebe81912c462d91131 test: cover evidence-backed task closure and archive recovery
  pr: none
  notes: implementation commits — 5df81f8516c48cbfffe627461e65bd9399212ab0, 36334993beecff0917cbee25839a83f86964eb66, 16a8a7d532c7e5acb57fb6b96c6fab7a0c461db1; exact local object identities; no publication authorized.

T-02 | Enforce scoped cleanup and stage provider outputs | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded
  target_files:
  blocker: none
  notes:

T-03 | Connect finalization with shared workflow contracts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded
  target_files:
  blocker: none
  notes:
