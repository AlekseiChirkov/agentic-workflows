spec_path: .ai/specs/00-sensitive-data-scrub.md
flow: full
publication: ready for review; the Publication Update below supersedes the original local-only hold

## Phases
- discovery: complete
- execution: complete
- validation: complete

## Task Analysis
→ archived to state-archive.md

### Assumptions
- flow: full — gate: 1 fail (more than three files), 2 fail (new hygiene invariant), 3 fail (validation behavior changes), 4 pass (no schema migration). Source: spec acceptance criteria and repository architecture.
- Keep the public rename outside this change; retain existing environment variable compatibility while removing private default paths. Source: spec Out of Scope.
- Preserve all knowledge-base files and include the full directory in this repository; redact mutable contents rather than delete files. This explicit user exception overrides consumer-repository tracking restrictions. Source: user, 2026-10-19.
- Preserve existing Russian prose; write any new replacement prose in English. Source: global language instructions.

## Open Questions (batch)
None.

### Description Amendments
- 2026-10-19: User chose scan option A. Exclude the denylist, the immutable source spec, git internals, local logs, and machine settings. Preserve every existing local knowledge-base file; redact mutable contents without deleting files. Include the complete knowledge base in this repository, overriding the workflow's consumer-repository tracking prohibition for this run. Source: user.
- 2026-10-19: User chose publication option A. Local failing-test and implementation commits are permitted. Withhold every push and PR pending separately authorized history remediation. Existing history remains unchanged. Source: user.

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03

## Decomposition Decisions
Use three independently verifiable leaves: script path portability, neutral public examples, and the final public-hygiene scanner/corpus sweep. The final leaf owns remaining tracked corpus and local-context redaction so its new whole-tree check can still observe a genuine failing current-tree baseline before that final cleanup. This corrects the initial one-leaf draft after the Arbiter identified separate S2/S5 clusters; no execution artifacts existed or were overwritten.

## Solution Design

### Variants
→ archived to state-archive.md

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Existing Bash validator | 5 | 5 | 5 | 4 | 4 | 23 |
| Separate Python tool | 3 | 4 | 2 | 5 | 3 | 17 |
| Manual cleanup only | 5 | 5 | 3 | 1 | 4 | 18 |

**Winner:** Existing Bash validator — the spec explicitly chooses this integration surface and the repository already uses it for smoke checks.
**Anti-overengineering check:** passed; no new runtime or generalized scanning framework.
**Evidence:** spec Guard criteria; principles/architecture.md P1, P7, P10; context/runbook.md test command; memory/architecture.md scripts.

### Decision
Extend the existing validator, observe a hygiene failure before cleanup, then remove private details from scripts, examples, documents, and local context until both the contract suite and agreed final sweep pass. The user approved explicit scan exceptions and local test-first commits. Preserve and include the full knowledge base; withhold all pushes and PRs.
adr: not triggered — the spec already fixes the validation entry point and no state format, workflow stop, deployment boundary, or runtime architecture is changed. Any new semantics arising from human answers will be recorded before execution.

### Scope
#### In
The forbidden-token contract, root denylist, private path defaults and usages, fictional examples, historical document redactions, local context redactions applied by the Orchestrator, and final scan evidence.
#### Out
History rewriting, the public rename, environment-variable renaming, credential detection, deployment, unrelated roadmap tasks, and remote publication before separate history remediation.

### Rejected
→ archived to state-archive.md

### Off-limits
Do not edit run-log contents or local machine settings. Do not rewrite history, merge, delete branches, force-push, push main, deploy to harnesses, delete knowledge-base files, or alter unrelated workflow behavior. Preserve the source spec; record any approved amendment in this state file.

### Invariants
- Preserve the existing contract checks and workflow semantics while replacing private examples.
- Resolve script defaults from their location or configured overrides, preserving existing override compatibility.
- Preserve document teaching value and the distinction between accepted and rejected quick-gate examples.
- Do not silently suppress hygiene failures or skip unreadable tracked files.
- The denylist is public-hygiene metadata, never a credential store.
- Both batch questions are answered. Local execution and commits are authorized; every push and PR remains withheld.

### Acceptance Criteria
- The agreed full-tree/manual and tracked-file/automated scopes have no private-token matches outside explicitly approved exceptions.
- Scripts contain no private path defaults and retain supported configuration overrides; Bash syntax and relevant path-resolution smoke checks pass.
- Public umbrella and gate examples use fictional names; internal file, project, PR, run, user, and host details are absent in the agreed scope; changed prose is English.
- The existing contract validator includes a configurable forbidden-token group with fail/pass evidence, robust tracked-file enumeration, and a documented public-hygiene denylist.
- Logs and machine-specific settings remain ignored and unmodified; the final sweep command and result are recorded locally.
- The complete existing validator suite passes, tests are intact, and all reviewed branches are eligible for PRs only when the batch-gate publication decision is satisfied.

## Subtask Progress
T-01 | Portable script path defaults | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Atomic validation complete — all acceptance criteria met; relative source propagation repaired; 536 contract checks and Bash syntax pass.
  target_files: validate-contracts.sh, sync.sh, log-step.sh, setup-new-project.sh, setup-umbrella.sh, setup-all-repos.sh, link-skills.sh
  blocker: none
  notes: tdd: smoke — 2 checks, AC coverage 3/3; temporary fixtures only, sync stops at failed preflight and log helper uses read-only path command.
         tdd: red digest — AC-1 → test_shell_paths_public_defaults_pass_syntax; AC-2 → test_shell_paths_relocated_checkout_preserves_overrides; AC-3 → test_shell_paths_public_defaults_pass_syntax, test_shell_paths_relocated_checkout_preserves_overrides; edge → spaces, empty overrides, environment and flag precedence, child source propagation, deployment boundary.
         tdd: green — both RED checks unchanged (SHA-256 verified); 536 passed, 0 failed; AC-1/AC-3 covered by public-default/syntax check and AC-2/AC-3 by relocation/override check.
         verification: configured lint passed; shellcheck unavailable; deployment/build deliberately withheld; no logs, local settings, git state, or shared context modified.
         architecture.md: update proposed to Orchestrator — script defaults derive from script directory, setup scripts accept WORKFLOWS_SOURCE, and sync --from retains highest precedence.
         finalization: orchestrated mode; plan status delta returned as done; own block current with protected RED digest and git fields preserved, no compression needed.
         validation: important — setup-all-repos.sh resolves relative WORKFLOWS_SOURCE against each child directory after cd; with ../source with spaces the umbrella initializes, child setup is not found, child context is absent, and the parent still exits 0. Normalize the selected source before changing directories and add a regression case; AC-2 is partial.
         validation: AC-1 and AC-3 met; independently reproduced both frozen checks failing against baseline scripts and passing unchanged against current scripts; full suite 536 passed, 0 failed; root Bash syntax passes; shellcheck unavailable. No deployment or logs written.
         tdd: supplemental red — AC-2 → test_shell_paths_relocated_checkout_preserves_overrides, added relative setup-source scenario with spaces and child template-marker assertion; 535 passed, 1 expected failure: setup-all-repos.sh (relative): child setup did not use selected source; original atomic-tests green retained.
         tdd: supplemental green — relative source override with spaces initializes the umbrella and child from the same absolute source; full validator unchanged since supplemental test commit (SHA-256 verified), 536 passed, 0 failed.
         repair: setup-all-repos.sh normalizes WORKFLOWS_SRC and exports WORKFLOWS_SOURCE before invoking children; previous validation failure retained pending independent recheck; no shared-file delta beyond the existing completion proposal.
         validation recheck: DONE — AC-1/AC-2/AC-3 met; independently reproduced the relative source child failure before correction and verified it passes after normalization/export. Original test assertions/scenarios preserved; supplemental validator unchanged since RED. Full suite 536 passed, 0 failed; Bash syntax passes; shellcheck unavailable. Earlier finding resolved.
  branch: fix/portable-script-paths
  base_branch: main
  base_commit: fc94fc1f9331d092cd59255ce41fa043c791cd9e
  commits: 34790f153f1a912b4665a6b9fc8b721aed308cf6 test: cover portable script defaults and source overrides, a2c218e266a5e3de8e7d09d78bf33a1a3671eb3b fix: resolve script roots without private checkout paths, 4275345c969ef4f5f516732cbe8f592d775a8d3d test: cover relative source overrides in child setup, 297bda22d5f4c07f7bbf2d73e8fc95fdb6d675bd fix: preserve relative source overrides across child setup
  pr: #2 ready
T-02 | Neutral public examples | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Atomic validation complete — all acceptance criteria met; unchanged RED checks verified; 539 contract checks pass; one pre-existing path-example improvement deferred.
  target_files: validate-contracts.sh, scrub-denylist.txt, docs/USAGE.md, docs/audits/AUDIT-PROMPT.md, docs/audits/2026-07-21-logic-audit-fixes.md, docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md, docs/analysis/2026-09-16-rules-workflows-naming-review.md, docs/analysis/2026-09-16-comparative-analysis.ru.md, templates/.ai-umbrella/README.md, templates/.ai-umbrella/principles/coding.md, templates/.ai/principles/coding.md, templates/.ai/principles/architecture.md, rules/workflow-reference.md, workflows/retro.md, rules/quick-flow.md, workflows/phase-pipeline.md
  blocker: none
  notes: tdd: smoke — 3 checks, AC coverage 3/3; no implementation edits before RED; scoped corpus includes hidden template Markdown and literal case-insensitive substring matches.
         tdd: red digest — AC-1 → test_public_examples_umbrella_uses_neutral_services, test_public_examples_quick_gate_preserves_fictional_outcomes, test_public_examples_scoped_documents_exclude_private_tokens; AC-2 → test_public_examples_umbrella_uses_neutral_services, test_public_examples_quick_gate_preserves_fictional_outcomes; AC-3 → test_public_examples_scoped_documents_exclude_private_tokens; edge → case variants, benign substrings, quoted filename enumeration, scan errors fail closed.
         tdd: test-only privacy correction — replaced a copied client HTTP status with a generic three-digit status matcher before the RED commit and made the known workflow-run identifier independent of surrounding prose; assertions retain the required absence of private payment details.
         tdd: test amended — existing protected-section check only: awk range terminator old multi-phase heading → ^## Multi-Phase Spec Rules, matching the required literal-substring heading redaction; this preserves its original section boundary. All three new RED functions and denylist remain unchanged.
         tdd: red evidence — bash validate-contracts.sh: 536 passed, 3 failed; neutral umbrella names/paths absent, gate examples retain private source details, scoped documents contain forbidden tokens and lack English legends. Denylist added only as shared test input; whole-tree scanner remains outside this leaf.
         tdd: green — all three RED checks pass; 539 passed, 0 failed. New smoke block SHA-256 ec7badea3ecf5f90c46efcbd2928cfdbfd9a3adf57d6b920830b0c7b8f997d04 and denylist SHA-256 a07519f9167d0d197ea6e2e34fe97632f26b9c4f118c28db345ecd6d51f16f06 unchanged. Reversing only the recorded legacy heading-selector amendment restores the exact RED validator SHA-256 415087989c6a3d631811e482fdf0081fc05f5b77e634735170cab5bab63b9971.
         verification: Bash syntax and configured lint pass; shellcheck unavailable. Manual review confirms four-file shipped export change remains full; single-file queue diagnostic INFO-to-DEBUG change remains quick, with its existing invariants and regression step preserved. All files retained; new prose and replacement labels are English.
         architecture.md: no module or interface update needed; public example corpus and validator already documented. The Orchestrator may refresh current validator check counts after the final hygiene leaf.
         finalization: orchestrated mode; own block complete, protected RED digest and git fields preserved; plan status delta returned as done; no shared context, git operations, logging, or deployment performed. No compression needed within the bounded own block.
         validation: DONE — AC-1/AC-2/AC-3 met; all three frozen checks independently fail for the expected reasons against the baseline and pass unchanged in the current tree. Full suite 539 passed, 0 failed; Bash syntax passes; shellcheck unavailable.
         validation: RED audit confirms the new test block and denylist are byte-identical to the test commit; reversing only the documented legacy heading-selector amendment recovers the recorded full RED validator digest. Fictional full/quick outcomes, neutral umbrella names, English legends, historical analysis, and section references preserved.
         proposal: Do Later — pre-existing umbrella working_dir example needs five parent traversals instead of four to reach the service repository; return the shared proposal delta without changing workflow semantics in this privacy leaf.
  branch: docs/neutral-public-examples
  base_branch: fix/portable-script-paths
  base_commit: 297bda22d5f4c07f7bbf2d73e8fc95fdb6d675bd
  commits: ee22ca13443ab86858b85199aea1464a3ad9536a test: cover neutral public examples and privacy redactions, 37f4b2f05516b9f99343eb10c89b22ac083d6493 docs: replace private examples with fictional systems
  pr: #3 ready
T-03 | Public hygiene scanner and final sweep | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: Atomic validation complete — all acceptance criteria met; frozen RED and original checks intact; 542 checks and full-context sweep pass.
  target_files: validate-contracts.sh, .gitignore, README.md, docs/USAGE.md, rules/orchestration.md, rules/phase-discovery.md, rules/run-log.md, workflows/onboard-legacy-project.md, workflows/pd-analyze.md, workflows/pd-decompose.md, workflows/pd-finalize.md, workflows/pe-finalize.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-pipeline.md, workflows/phase-validation.md, workflows/spec-run.md, workflows/suggest-commit-message.md
  blocker: none
  notes: tdd: smoke — 2 checks, AC coverage 4/4; production tracked-tree RED and final sweep are supplementary evidence required before cleanup and completion.
         tdd: red digest — AC-1 → test_public_hygiene_fixture_scans_fail_closed; AC-2 → test_public_hygiene_fixture_scans_fail_closed; AC-3 → test_public_hygiene_repository_preserves_context_and_local_ignores; AC-4 → both checks plus unchanged complete validator.
         tdd: red evidence — corrected complete-source fixture passes clean tree, then contaminated tracked space-containing file unexpectedly exits 0 because hygiene CLI is absent; root ignore policy rejects knowledge-base tracking. Full validator: 539 passed, 2 expected failures.
         tdd: red audit — smoke block SHA-256 8aa8cfd1807ea76cf0e004c0a8f449ceee58108a27f950679835149641e1f537; no implementation or denylist edits. Initial incomplete copied-runner attempt rejected and replaced by complete current HEAD archive before accepting RED; digest now covers complete line-anchored smoke block.
         tdd: test amended — before test commit, empty tracked files accepted, initial fixture paths staged explicitly, ignore assertion limited to approved logs and local settings, and symlink target-text fixtures added; corrected RED remains 539 passed and 2 expected failures.

         tdd: supplemental red — production tracked-tree group observed before any cleanup: standalone scanner exit 1, 15 contaminated tracked files; complete suite 540 passed and 2 expected failures (current ignore policy plus tracked-tree hygiene). Original 539 checks and frozen smoke block preserved.
         implementation: NUL-safe indexed path enumeration, literal case-insensitive matching, exact root metadata/source-spec exemptions, link text scanning, configurable standalone mode, empty-index rejection, and fail-closed missing/unreadable inputs or scan errors; empty ordinary files accepted.
         tdd: green — both frozen RED checks and supplemental production group pass; full validator 542 passed, 0 failed; original 539 checks byte-identical after the scanner prefix is removed; frozen smoke block and denylist SHA-256 unchanged.
         verification: root Bash syntax and configured lint pass; shellcheck unavailable; git diff --check passes. Local logs and machine settings remain ignored, no log/settings content modified, no git mutations or deployment performed.
         manual sweep: bash /tmp/public-hygiene-manual-sweep.sh; exit 0; 152 files scanned, 0 unexpected matches, 0 errors. Command uses find with NUL output, prunes exact root .git and logs directories, skips exact root scrub-denylist.txt, .ai/specs/00-sensitive-data-scrub.md, and .claude/settings.local.json, then grep -Fia -f filtered-patterns on every remaining regular file or symlink text. Includes tracked and untracked knowledge files; all 44 baseline paths remain present.
         acceptance: AC-1 production RED before cleanup plus final scanner pass; AC-2 frozen synthetic fixtures and unchanged public denylist; AC-3 final whole-tree sweep and approved local ignores; AC-4 unchanged prior checks plus full 542-check suite, exact local evidence recorded.
         shared deltas: Orchestrator applied mutable context, narrative, roadmap wording, historical heading spelling, and current check-count redactions; source specification preserved. Host and consumer details are neutral; all knowledge files retained.
         architecture.md: update applied by Orchestrator — validator inventory and standalone hygiene CLI described with 542 checks. Public operating manual current count updated; dated historical counts preserved.
         finalization: orchestrated mode; plan status delta T-03 → done returned to Orchestrator; own block complete and protected TDD/git fields retained. Compression limited to replacing the stale verification checkpoint; no other shared sections changed. Root will stage full knowledge base and re-run indexed hygiene before independent validation; publication remains withheld.

         validation: DONE — AC-1/AC-2/AC-3/AC-4 met; independent complete suite 542 passed, 0 failed with all 45 current knowledge files indexed. All 44 baseline paths preserved; no local logs or settings changed. Bash syntax passes; shellcheck unavailable.
         validation: frozen RED independently reproduced from the test commit: 539 passed, 2 expected failures; historical production scanner independently detects 15 contaminated files. Current fixtures cover literal case-insensitive substrings, punctuation, spaces/newlines, staged context, tracked logs, exact exclusions, link text, empty files, missing/unreadable/empty inputs, and scanner errors. An independent enumeration-only Git failure exits 1 with its specific failure message.
         tdd: validation audit — frozen smoke block and denylist byte-identical to the test commit; removing only additive scanner/smoke/production blocks and their separator recovers the exact original 539-check validator. Recorded digest 8aa8cfd1807ea76cf0e004c0a8f449ceee58108a27f950679835149641e1f537 includes the preceding LF and excludes the closing marker; complete opening-through-closing marker lines hash to 354b08894312b2946b2e06d414e63ad2347e4dac505185fbdd09873162d99a55 in both versions.
         validation sweep: bash /tmp/public-hygiene-manual-sweep.sh independently inspected and run; exit 0; 152 files, 0 unexpected matches, 0 errors. Exact root git/log directories pruned; exact root list, immutable source specification, and local settings excluded; every remaining regular file or symlink text scanned with grep -Fia. Root resolved the optional shared archive EOF whitespace issue; no implementation defect found.

         proposal: Optional — isolate indexed-file enumeration errors in the existing Git failure fixture by delegating root lookup and failing only ls-files; current production behavior independently passes that focused check. Shared proposal section returned to the Orchestrator; no changes applied.

         final validation: orchestrated mode; plan status delta reviewed returned to the Orchestrator. Own block remains current; protected audit/git fields preserved; no compression required within the assigned block.

  branch: fix/public-hygiene-guard
  base_branch: docs/neutral-public-examples
  base_commit: 37f4b2f05516b9f99343eb10c89b22ac083d6493
  commits: a0652f33710906082501ff2fca88ceaa00fc296e test: cover tracked-file hygiene and context preservation, df71192b8299ce89328f4cb6202b523a59e852ec fix: enforce public hygiene and remove private references
  pr: #4 ready

## Arbiter Review
- Scan exceptions require a user decision: the denylist and immutable source spec self-match. Source: spec Guard criteria and domain Spec definition.
- History/publication requires a user decision: the existing initial tree already contains private strings. Source: HEAD:docs/USAGE.md, HEAD:sync.sh, HEAD:log-step.sh; spec Goal and Notes; git-flow Commits.
- Preserve existing configuration names and use safe script-relative defaults. Source: spec Out of Scope and coding Shell scripts.
- Literal case-insensitive substrings also match ordinary words; rewrite those words rather than silently add boundaries. Source: spec first criterion; rules/orchestration.md and docs/USAGE.md matches.
- English replacement labels apply inside existing Russian documents. Source: global language instructions.

## Discovery Finalization
Artifact conformance: 12 passed, 0 failed, 3 not applicable. Six-section descriptions, 3–15 steps, criterion/scenario coverage, dependencies, progress fields, and English output verified. State compression retained all protected sections; verbose analysis and variants were archived.
Root memory state: updated with the ready plan and pending batch gate.
Root architecture: skipped — the selected implementation uses the existing validator; nothing has shipped.
Root architectural principles: skipped — no new architecture principle was decided.
Project state: skipped — no file exists.
Discovery artifacts passed before execution. The user resolved the batch gate; local execution is in progress. Pushes and PRs remain withheld.

## Resume Decisions
- The full knowledge base will be explicitly staged on the final branch after redaction; no file is deleted. The original source spec is an approved scanning exception.
- Model selection uses the session default for all leaves; no verified compatible live model catalog is available in this environment, so no price or capability estimates are invented. Model cells remain blank under the documented default fallback.
- Effective publication mode: local only, overriding the initial --allow-pr flag per the user's latest answer.

## Improvement Proposals (T-02)

### Do Now
None.

### Do Later
A pre-existing umbrella-template relative service path resolves one directory too shallow. Correct it with a focused path-resolution smoke check in a separate change; outside the public-hygiene scope.

### Optional
None.

adr: .ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md (Accepted)

## Improvement Proposals (T-03)

### Do Now
None.

### Do Later
None.

### Optional
Strengthen the Git-error fixture by preserving repository-root lookup and failing only file enumeration. The independent validator already verified the production enumeration failure path; this is a future test-isolation improvement, not a production defect.

## Execution Report
- T-01: reviewed — script-relative defaults and override propagation; supplemental relative-source defect reproduced and fixed; 536 checks passed.
- T-02: reviewed — neutral umbrella and fictional examples, historical redactions, consistent readers; 539 checks passed.
- T-03: reviewed — tracked-file scanner, remaining redactions, complete knowledge-base inclusion; 542 checks passed.
All subtasks complete; none skipped, blocked, deferred, or not reached. No Do Now proposals remain. Publication is withheld by the owner; this is an explicit scope decision rather than an implementation failure.

## Manual Sweep Evidence
Command: grep -rniE -f scrub-denylist.txt -- <all explicitly enumerated regular files under the approved exclusions>; argv supplied directly by Python to preserve filenames.
Exact exclusions: root .git/ and logs/; root scrub-denylist.txt; .ai/specs/00-sensitive-data-scrub.md; .claude/settings.local.json.
Result: 152 files; grep exit 1 (no matches); stdout 0 bytes; stderr 0 bytes. No project symlinks were present. The independently inspected manual helper additionally tests symlink target text: 152 files, 0 unexpected matches, 0 errors.
Preservation: all 44 baseline knowledge-base paths remain; all 45 current knowledge-base files, including the new decision record, are indexed. Standalone tracked-file scanner passes after inclusion.

## Execution Finalization
Project state skipped: file absent. Root memory architecture updated for portable defaults and 542 checks. Domain principles explicitly record the owner-authorized source-repository tracking exception. Architecture principles remain applicable without a new runtime or module. Test-only and implementation commits are recorded separately; main is unchanged. Task artifacts remain at their existing paths so no knowledge-base file is deleted or moved.

## Contract Check

### Invariants

| Requirement | Status |
|---|---|
| Existing checks and workflow semantics | PASS: 542 checks pass; original checks retained with the documented equivalent heading selector. |
| Portable defaults and override compatibility | PASS: Relocation, spaces, empty overrides, flag precedence, and relative child-source propagation pass. |
| Teaching value and quick/full distinction | PASS: Fictional four-file export change remains full; single-file diagnostic log change remains quick. |
| Fail-closed indexed scanning | PASS: Missing/unreadable input, empty list/index, Git/grep errors, staged context, unusual filenames, and symlink text verified. |
| Public-hygiene metadata | PASS: Denylist forbids secret storage and requires same-change cleanup; matching is literal and case-insensitive. |
| Answered owner decisions | PASS: Local commits only; preserve and include full knowledge base; pushes and PRs withheld. |

### Acceptance Criteria

| Requirement | Status |
|---|---|
| Clean approved automated and manual scopes | PASS: All 45 knowledge files indexed; manual sweep 152 files, zero matches/errors, exact approved exclusions. |
| Portable scripts and compatible overrides | PASS: Private defaults removed; Bash syntax and scoped relocation/override scenarios pass. |
| Neutral examples and mutable context | PASS: Fictional umbrella/export/queue examples, English labels/legends, neutral environment and progress context. |
| Configurable guard and genuine RED/GREEN | PASS: Frozen RED reproduced as 539 passes/2 failures; production baseline flags 15 files; current 542/0. |
| Local-store exclusions and sweep evidence | PASS: No log/settings changes; ignore rules and exact zero-match evidence recorded. |
| Intact full suite and publication decision | PASS: All frozen sets intact; documented selector adaptation only; no remote publication. |

### Off-limits

| Requirement | Status |
|---|---|
| Run-log contents | PASS: No log contents changed or committed. |
| Machine settings | PASS: Exact local settings path remains ignored and unmodified. |
| History rewriting | PASS: Only additive local commits; original ancestry unchanged. |
| Merges | PASS: No merge commits introduced. |
| Branch deletion | PASS: No branches deleted; recorded stack exists. |
| Force pushes | PASS: No pushes performed. |
| Main branch writes | PASS: Main remains at the original base. |
| Harness deployment | PASS: No deployment; fixture sync stops at failed preflight. |
| Knowledge-base deletion | PASS: All 44 baseline paths preserved; 45 current files indexed. |
| Unrelated workflow behavior | PASS: Only hygiene, portable resolution, equivalent examples, and owner-approved tracking changes. |
| Source immutability during execution | PASS: Source preserved through validation; approved changes recorded in amendments before post-validation reconciliation. |

## Code Review

### Findings
1. Optional: isolate the Git-error smoke fixture so root lookup delegates normally and only file enumeration fails. Production file-enumeration failure was independently verified to fail closed; no production defect remains.

### Summary
23 contract passes, 0 failures. Code review: 0 critical, 0 important, 1 optional. Frozen tests, the original checks, readability, compatibility, error handling, and architectural fit are acceptable. Bash syntax passes; shellcheck is unavailable. A pre-existing umbrella-template relative service path is separately recorded as an out-of-scope followup.

## Issue List

### Approved
None; no critical or important defects remain.

### Deferred
1. Optional Git-error fixture isolation; deferred under the orchestrated optional-issue policy. Production behavior already verified independently.

## Fix-Tasks
fixes-created: complete
fixes-count: 0
Created: none

## Deferred
- [source: issues] Optional Git-error fixture isolation; no production defect or unmet hygiene criterion.

## Spec Sync
sync: complete
synced_at: 2026-10-19
deltas: 5 (implemented-differently: 4, not-implemented: 0, implemented-beyond: 1)
spec: .ai/specs/00-sensitive-data-scrub.md

## Validation Finalization
All original subtasks reviewed; no required fix-tasks. Existing history and remote publication remain separate owner decisions, as explicitly agreed. Optional fixture refinement and the existing template path followup do not change the passed hygiene contract. Root architecture/current counts and repository-specific tracking principles are updated; no new runtime or deployment target was introduced. Project state skipped because absent. Post-validation spec reconciliation records owner-approved differences; no failed criterion was weakened or reclassified.

## Closure Commit
The final metadata-only inclusion commit intentionally follows the last recorded implementation SHA. Its own hash is reported externally because a tracked file cannot contain the hash of the commit that contains it.
branch: fix/public-hygiene-guard
expected_parent: df71192b8299ce89328f4cb6202b523a59e852ec
allowed_scope: exactly the knowledge-base paths listed below; no source-code changes
Future reconciliation must apply the owner's tracked-knowledge exception, verify the tip first parent equals expected_parent, and verify its changed paths match this list. The generic consumer reconciliation does not recognize this repository-specific closure automatically. All subtask test/implementation SHAs and original branch-point SHAs remain unchanged.
recorded_paths:
- .ai/README.md
- .ai/adr/0001-task-unknown-markdown-only-no-runtime.md
- .ai/adr/0002-task-unknown-state-on-disk-untracked.md
- .ai/adr/0003-task-unknown-rules-as-prefixed-skills.md
- .ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md
- .ai/adr/0005-task-unknown-pipeline-invisible-in-repository.md
- .ai/adr/0006-task-unknown-central-run-log-and-retro.md
- .ai/adr/0007-task-unknown-commit-ai-directory-in-this-repository.md
- .ai/adr/0008-task-unknown-enforcement-moves-to-harness.md
- .ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md
- .ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md
- .ai/adr/index.md
- .ai/context/environment.md
- .ai/context/integrations.md
- .ai/context/runbook.md
- .ai/memory/architecture.md
- .ai/memory/progress.md
- .ai/memory/state.md
- .ai/principles/architecture.md
- .ai/principles/coding.md
- .ai/principles/domain.md
- .ai/specs/00-sensitive-data-scrub.md
- .ai/specs/01-git-source-of-truth.md
- .ai/specs/02-run-log-vocabulary-validation.md
- .ai/specs/03-hook-based-logging.md
- .ai/specs/04-model-catalog-cache.md
- .ai/specs/05-cost-and-duration-telemetry.md
- .ai/specs/06-harness-git-rails.md
- .ai/specs/07-state-tool.md
- .ai/specs/08-context-tiering.md
- .ai/specs/09-golden-run-tests.md
- .ai/specs/10-generated-reference-docs.md
- .ai/specs/11-open-source-readiness.md
- .ai/specs/12-composite-branch-model-and-parallel-children.md
- .ai/specs/13-model-only-harnesses-and-rule-naming.md
- .ai/specs/13a-rules-workflows-audit.md
- .ai/specs/README.md
- .ai/tasks/completed/.gitkeep
- .ai/tasks/todo/.gitkeep
- .ai/tasks/todo/task-00-sensitive-data-scrub/T-01-portable-script-paths/description.md
- .ai/tasks/todo/task-00-sensitive-data-scrub/T-02-neutral-public-examples/description.md
- .ai/tasks/todo/task-00-sensitive-data-scrub/T-03-public-hygiene-guard/description.md
- .ai/tasks/todo/task-00-sensitive-data-scrub/plan.md
- .ai/tasks/todo/task-00-sensitive-data-scrub/state-archive.md
- .ai/tasks/todo/task-00-sensitive-data-scrub/state.md

## Final Verification
- Full contract and smoke suite: 542 passed, 0 failed.
- Final task-artifact validation: 21 passed, 0 failed, 0 skipped.
- Task contract review: 23 passed, 0 failed; no critical or important defects.
- Manual whole-tree sweep: 152 files, 0 unexpected matches, 0 errors; requested regex grep also returns no output.
- Complete knowledge base: 45 current files indexed; all 44 original paths retained; no file deleted or moved.
- Git and publication: original main unchanged; explicit staged scope contains only the recorded knowledge-base paths; no merge, push, pull request, deployment, or history rewrite.
- Optional: Git enumeration-error fixture isolation deferred; an existing template path issue remains an unrelated followup.
- Shell syntax passes; shellcheck is unavailable.

## Publication Update
- 2026-10-19: The owner explicitly authorized publication to AlekseiChirkov/agentic-workflows with existing ancestry and approved scan exceptions retained. This supersedes the earlier local-only hold; history rewriting remains outside scope.
- All three branches were pushed without force. Draft pull requests were created and promoted to ready after the completed validation.
- Merge order: [#2](https://github.com/AlekseiChirkov/agentic-workflows/pull/2) (main) → [#3](https://github.com/AlekseiChirkov/agentic-workflows/pull/3) (fix/portable-script-paths) → [#4](https://github.com/AlekseiChirkov/agentic-workflows/pull/4) (docs/neutral-public-examples).
- Main, existing ancestry, and the first two branch tips remain unchanged. No merge, branch deletion, deployment, or history rewrite occurred.
- The original closure snapshot is 0867afedd2bb343b9326daeef0ef2cbbe9e2bbac. Its descriptor above remains historical; the publication metadata follows it in a separate additive commit.

### Publication Metadata Commit
branch: fix/public-hygiene-guard
expected_parent: 0867afedd2bb343b9326daeef0ef2cbbe9e2bbac
allowed_scope: exactly the three paths below; no source-code changes
Reconciliation must first verify this metadata commit against its parent and path list, then verify the original closure snapshot against the historical descriptor. Its own hash is reported externally because this tracked record cannot contain its enclosing commit hash. Original subtask commits and immutable branch-point hashes remain unchanged.
recorded_paths:
- .ai/tasks/todo/task-00-sensitive-data-scrub/state.md
- .ai/memory/state.md
- .ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md
