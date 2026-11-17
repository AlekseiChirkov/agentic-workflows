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
- Read-only monitoring later observed unrelated audit edits in the original checkout; preserve them without importing or reverting them. The isolated worktree remains based on the pinned dependency.

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
T-01 | Implement evidence, journal and lossless archival mechanics | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: DoD satisfied — independent repair/recovery validation passed
  target_files: scripts/check-phase-finalize.py, scripts/phase-finalize.py, scripts/finalization_support.py, scripts/finalization_evidence.py, scripts/finalization_archive.py, scripts/finalization_recovery.py
  blocker: none
  notes: tdd: integration — real disposable repositories and state/archive boundaries; tdd: red digest — 42 cases in scripts/check-phase-finalize.py, sha256 0b3483d1e1ec0f9ad34049d87130bb4179d911e60454883daff09e24f16bc64b; 42 expected assertion failures, no fixture/import errors; preimplementation test review strengthened supporting validation evidence and allowed current-pointer relocation.
  notes: tdd: test amended — correct protective fixture to canonical orchestrail.protectedBranch and add the missing reviewed multi-repository plan row; assertions and test identities unchanged. Amended set sha256 c054be992a838e99c36c8183ff0ccd745ea30afa67ee3145fcc53dc142c3cb0f; 42 expected failures observed again before the coordinator implementation.
  notes: tdd: test amended — supporting attestations now include executed source assertions, source tips, review provenance and explicit dependency/runtime limitations; six expected attestation-invalid errors exposed the missing fixture provenance. Additional regression cases extend the original frozen set without weakening it. Link regressions were added after their implementation and a temporary link-planning disable produced three expected failures; this replay is recorded separately and is not claimed as original test-first evidence. Original RED outputs and additional regression outputs are retained outside the project in /tmp/finalization-*.txt.
  notes: focused GREEN — 64 tests passed in 16.064s; existing repository-set suite 38 passed in 4.551s; Python syntax and function annotations passed. Final test SHA256 87a0e27682344ef656fc949bd130c38d762ee4bc66e585680d7820ac94bb9ba9. No full validator or staged sync yet.
  notes: independent validation — 64 focused cases passed (22.044s), 38 repository-set cases passed (2.885s); syntax/whitespace passed, ShellCheck unavailable. Critical: ignored-file collision can be overwritten by plain switch. Important: resumed archive trusts stale spec eligibility; canonical pr: none and numbered PR forms are incompatible. Fixes require new observed RED tests before repair.
  notes: recovery audit — original SHA/command text alone does not retain rewritten Git objects after garbage collection. Required repair adds verified self-contained recovery packs before deletion receipts; generation remains explicit and verification uses isolated temporary object storage.
  notes: repair RED — eight independent validation regressions failed as expected in 3.212s, without fixture errors. tdd: test amended — exact checkout argv gains --no-overwrite-ignore because the original plain-switch expectation conflicts with the reproduced unrelated-file preservation invariant; test identity and behavior assertions remain. Recovery-pack regressions are pending before the repair test-only commit.
  notes: combined repair RED — 13 new behavior tests plus the narrowed existing checkout expectation produced 14 expected assertion failures in 5.176s, no errors; implementation unchanged. Test-only commit 24fcc759fea10008ed23b6bce8e01f7906e07e6d; SHA256 2ee13135b0de223f691783cacd1843a03f8ecba5d7bc578bbb8ff1a58972ae24; total 77 cases. tdd: test amended — prepare/adoption fixtures execute real caller recovery-pack plans when required; canonical PR fixtures use controlled gh and local URL-rewritten bare remotes, without network.
  notes: repair GREEN — 77 tests passed in 34.544s; 38 existing repository-set checks passed in 3.283s; syntax and annotations passed for six files. Frozen test digest unchanged. Repair commit 0aa6a9f276338ba5eb12181d2021fc6ceda46a12; independent recheck dispatched.
  notes: independent repair PASS — 77 tests passed in 30.546s; all three prior defects independently rechecked; syntax and whitespace passed; no tests removed and frozen repair digest unchanged. pav-propose --batch: zero proposals. Only this mechanics leaf is reviewed; task-level validation remains pending.
  branch: feat/task-finalization
  base_branch: feat/multi-repository-spec-run
  base_commit: 488edb11b37c3028b720d7de06cfe64cf7fe30c1
  commits: a930fed05cd7d3d06d20e1db94cd24e0fdb78b23, 16589db73254606caeb15bebe81912c462d91131, 5df81f8516c48cbfffe627461e65bd9399212ab0, 36334993beecff0917cbee25839a83f86964eb66, 16a8a7d532c7e5acb57fb6b96c6fab7a0c461db1, 77274994364ed23f7d11106e724f899af1c9cedf, 24fcc759fea10008ed23b6bce8e01f7906e07e6d, 0aa6a9f276338ba5eb12181d2021fc6ceda46a12, 55568223cd7c07b6aa05053d4bb5cae6852e6b49
  pr: none
  notes: implementation commits — 5df81f8516c48cbfffe627461e65bd9399212ab0, 36334993beecff0917cbee25839a83f86964eb66, 16a8a7d532c7e5acb57fb6b96c6fab7a0c461db1; exact local object identities; no publication authorized.

T-02 | Enforce scoped cleanup and stage provider outputs | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: DoD satisfied — independent safety and staging validation passed
  target_files: scripts/check-finalization-safety.py, scripts/finalization_evidence.py, rules/git-flow.md, hooks/git_rails.py, scripts/sync.sh, scripts/setup-new-project.sh
  blocker: none
  branch: feat/task-closure-safety
  notes: sequencing amendment — canonical narrow Git ownership/receipt exception is implemented with hooks in this leaf, preserving definition-before-reader order. Remaining contract readers stay in the next leaf; approved behavior and authorization unchanged.
  notes: interface correction — observed origin transport identity must be journaled and unchanged on resume; name origin and matching SHA alone cannot authorize deletion after a URL/pushurl/rewrite change. Focused regressions precede the evidence-module addition.
  notes: additional coverage — original 15 safety cases passed in 5.622s. Three characterized behaviors passed: actual stale/exact remote lease, denyDeletes failure after local cleanup with safe resume, canonical policy precedence. Five transport tests then produced six expected failures in 2.367s before helper/interface repair; SHA256 bde3ee8786dd845b138855b56d06af775d8d201cf225c5f949f0d554f2a67d62; test-only commit c4c48ac2c7edf2833f07700e35e38d02181cd05d; total 23 cases.
  notes: focused GREEN — 23 safety/staging tests passed in 12.261s; 77 core regressions passed in 37.898s; shell/Python/whitespace checks passed. Existing rails ran 2336 cases in 303.937s with three degraded-PATH Python-shim failures; exact failing method passed all subcases with system Python in 2.609s. Full fresh validator remains pending. Source commit 17d2cede8e3941553dd3535e077a07d9c16256ba; independent review dispatched.
  notes: runtime verification correction — an explicit mise version mistakenly started a Python download; that specific session and descendants were terminated after observed partial progress, no completed installation observed and no global cleanup performed. Use verified system Python for final checks, without further installation.
  notes: tdd: red digest — original 15-case set SHA256 6c93adbe0eafbcb96655b535390ac846ffc5e97777791311ca10849876b45bc3, test-only commit 77a49a35dacd8ae98eac39b491e01ba9471d2b7e; 11 expected assertion failures in 10.171s. Expanded 23-case set SHA256 bde3ee8786dd845b138855b56d06af775d8d201cf225c5f949f0d554f2a67d62, test-only commit c4c48ac2c7edf2833f07700e35e38d02181cd05d; five transport tests produced six expected failures in 2.367s, with three separately passing Git/policy characterizations.
  notes: independent PASS — safety/staging 23 passed in 14.499s; core 77 passed in 36.132s; syntax/annotations/whitespace passed; frozen digests and canonical RED notes verified, no tests weakened. pav-propose --batch: zero proposals. Full fresh validator and actual staged synchronization remain pending.
  base_branch: feat/task-finalization
  base_commit: 55568223cd7c07b6aa05053d4bb5cae6852e6b49
  commits: 77a49a35dacd8ae98eac39b491e01ba9471d2b7e test: cover scoped deletion receipts and isolated staging
  pr: none
  notes: tdd: integration/contract — 15 disposable hook/staging tests observed 11 expected assertion failures in 10.171s, implementation unchanged; SHA256 6c93adbe0eafbcb96655b535390ac846ffc5e97777791311ca10849876b45bc3. Pre-freeze review corrected the protection fixture key and narrowed checkout expectations to preserve generic policy instead of introducing unrelated restrictions. Test-only commit recorded before GREEN.

T-03 | Connect finalization with shared workflow contracts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded; journal recorder/checkpoint gap added to contract integration
  target_files:
  blocker: none
  notes: contract audit — postconditions/action_history exist, but current helper has no supported failed-command recorder; nonzero verification is rejected and blocked responses are not persisted. Implement the approved checkpoint vocabulary and immutable attempt history before claiming full journal conformance; preserve recovered errors and do not hand-edit the journal.
