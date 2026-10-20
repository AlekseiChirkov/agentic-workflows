spec_path: .ai/specs/02-run-log-vocabulary-validation.md
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Task Analysis
→ archived to state-archive.md

### Assumptions
- repository exception: knowledge snapshots record their parent and exact paths before committing, with their enclosing hash reported separately; branch tips are reconciled through that descriptor rather than a self-referential state hash (ADR-0010 Decision 2).
- user: requested fixing all findings and finishing the task (2026-10-20); resolve reproducible implementation and test defects and repeat independent reviews autonomously, without another permission stop for routine repairs. Existing no-merge and missing-intent boundaries remain.
- user: approved adopting the existing tracked changes into the first feature branch despite the clean-tree preflight requirement (2026-10-20); existing full knowledge-base tracking authorization remains in force.
- resume: discovery complete; resume at execution with the session default model because no Model column was recorded.
- flow: full — gate: 1 fail (five affected or added files), 2 fail (new validation and telemetry invariants), 3 fail (shipped helper behavior changes), 4 pass (no database schema or migration).

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05

## Subtask Progress
T-01 | producer-validation-and-writes | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/run-log-producer-validation
  base_branch: main
  base_commit: 65a6e68c3cdfa775a8ff7685e01203a3d83fe09c
  commits: 6b7b548 test: cover producer validation and persistence; e9f8232 test: cover fallback writes and repair validation fixtures; f0149ad feat: validate producer vocabulary before writes; d21d3aa test: cover arbitrary flows and single failure diagnostics; e32a69b fix: preserve flow text and emit one failure warning; 0d6a032 test: cover metadata text boundaries and legacy records; 0abf4c1 fix: preserve metadata text without record injection
  pr: none
  last_action: DoD met — producer validation and persistence reviewed; prior findings resolved; all 9 producer checks pass
  target_files: `scripts/validate-contracts.sh`, `scripts/log-step.sh`
  blocker: none
  notes: One producer contract covers all three event paths and their shared persistence invariants.
         tdd: smoke — 5 tests, AC coverage 6/6
         tdd: red digest — AC-1 → test_run_log_normalizes_only_exact_legacy_values; AC-2 → test_run_log_step_rejects_invalid_fields_without_mutation; AC-3 → test_run_log_flow_defaults_and_step_name_warnings; AC-4 → test_run_log_start_rejects_invalid_argument_sets, test_run_log_step_rejects_invalid_fields_without_mutation; AC-5 → test_run_log_start_and_end_persist_before_reporting_success; AC-6 → test_run_log_flow_defaults_and_step_name_warnings
         tdd: green — all 5 RED tests pass
         runbook: earlier attempt passed producer checks but failed unrelated relocated-setup and public-identity checks; nested version-history fixture inherited the setup failure; resolved in final verification
         tdd: added during GREEN — test_run_log_fallback_and_filesystem_errors_remain_nonblocking covers no-jq control-character encoding, numeric bounds, flow inheritance, blocked storage, and missing event files; internal alias sentinel rejection added to the existing matrix.
         tdd: test amended — test_shell_paths_relocated_checkout_preserves_overrides — corrected the relative source override to traverse two caller-directory levels; all modes and assertions preserved.
         tdd: test amended — test_public_identity_matches_exact_ledger_and_preserves_knowledge — baseline inventory accepts authorized todo-to-completed and spec-to-completed archival moves, retaining existence and tracked-file assertions for every entry.
         arbiter: regression fixture and exact identity-ledger coordinates reconciled against caller-relative source semantics and owner-approved completed archives/source-provenance exceptions; orchestrator refreshed the shared ledger.
         verification: final full suite 555 passed, 0 failed, 2 configured hygiene skips; all 5 frozen RED functions plus 1 added producer function pass; all shell syntax checks and git diff --check pass; shellcheck unavailable.
         architecture.md: runtime-contract interface update returned to the orchestrator under shared-file discipline; plan transition T-01 to done returned as a delta.
         compression: current structure retained; protected TDD evidence and git fields preserved; no additional compression needed.
         validation: independent pav-check NEEDS WORK; full suite 555 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n; shellcheck unavailable.
         validation: frozen RED audit passed — all five digest functions remain, with no removed assertions or cases; one internal-alias rejection case and a sixth fallback/filesystem function were added. Both unrelated fixture amendments have recorded test-defect reasons.
         validation: AC-1 [INCOMPLETE] — a missing active run plus unknown step name emits two diagnostics; AC-2 exact alias/provenance, AC-3 default flow/safe IDs, AC-4 advisory names, and AC-5 persistence/close recovery pass their existing tests. The broader required nonempty-flow preservation contract also remains incomplete.
         important: scripts/log-step.sh:368,429-435 — raw line-based metadata cannot preserve a valid multiline flow. Reproduce with an isolated ORCHESTRAIL_LOG_ROOT and run-start --pipeline phase-execution --flow $'custom\nflow'. Actual: exit 0, empty stdout, one "run-start metadata is unusable" warning, no JSONL. Expected: successful start and identical nonempty flow in start, later step, and end records (spec section 1).
         important: scripts/log-step.sh:497-501 — check_step_name runs before active-run lookup. Reproduce with a new isolated ORCHESTRAIL_LOG_ROOT and step --run 00000000 --step unknown-validator-probe --outcome ok. Actual: exit 0, empty stdout, two stderr lines: "step name is not in the current workflow list" and "step run not-found". Expected: one redacted rejection diagnostic (AC-1; spec section 3).
         validation: no code, tests, plan, shared memory, git metadata, or logs changed by this review; pav-propose and pav-close not run after NEEDS WORK.
         tdd: repair smoke — 2 new regression functions; all 6 earlier producer functions preserved.
         tdd: red digest — nonempty-flow preservation → test_run_log_preserves_unrestricted_flow_across_events; one diagnostic on rejection or failed persistence → test_run_log_reports_only_one_diagnostic_on_rejection_or_write_failure.
         tdd: repair RED — isolated producer slice failed both new functions as expected in jq and no-jq modes; all 6 existing functions passed; tests committed before implementation in d21d3aa.
         tdd: repair GREEN — all 8 producer functions pass; added cases retain newline-only and trailing-newline flow, literal backslashes and percent-escape lookalikes, and suppress unavailable-workflow advisories on failed metadata writes.
         repair: previous independent multiline-flow and duplicate-diagnostic findings are resolved; newline-bearing flow uses reversible percent encoding with an explicit metadata marker and direct assignment on read; ordinary and legacy ordinary flow metadata remains raw; no new dependencies or source/eval of user values.
         verification: stable full suite 557 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n; git diff --check passes; shellcheck unavailable; evidence /tmp/orchestrail-producer-repair-verified.log.
         finalization: plan remains done; no additional public interface or architecture update required; existing helper entry covers producer validation; atomic-validation reset for independent retry, with previous findings preserved as history.
         compression: no further shortening; protected TDD, git, and validation history retained.
         validation-retry: all 8 producer functions independently pass; both original reproduction scenarios now pass; recent complete-suite artifact confirms 557 passed, 0 failed, 2 configured hygiene skips; bash -n and git diff --check pass; shellcheck unavailable.
         validation-retry: original five frozen functions and two repair RED functions remain intact; changes after each RED checkpoint add cases without removing or weakening assertions; documented unrelated fixture amendments remain justified.
         validation-retry: task AC-1 through AC-5 pass existing checks and prior direct reproductions; broader unrestricted-flow/optional-free-text contract remains [INCOMPLETE] due to a cross-field metadata collision.
         important: scripts/log-step.sh:360-364,446 — run-start writes flags as raw multiline metadata after flow, allowing a supplied flags continuation line to impersonate flow_encoding=percent. Reproduce in isolated storage: run-start --pipeline phase-execution --flow 'literal%0Aflow' --flags $'custom\nflow_encoding=percent'. Actual: exit 0, empty stdout, "run-start metadata is unusable", no JSONL. Expected: successful start with the literal flow preserved across start, step, and end; optional flags text must not control metadata decoding.
         validation-retry: pav-propose and pav-close stopped after NEEDS WORK; no code, tests, plan, git, shared memory, or historical logs changed; no reviewed plan delta.
         tdd: metadata repair RED — test_run_log_metadata_preserves_text_boundaries_and_legacy_records failed on flags-marker collisions, truncated inherited text, and newline log roots in jq and no-jq modes; all 8 previous functions passed; test-only commit 0d6a032 preceded implementation.
         tdd: red digest — metadata record boundaries, exact inherited text, flags-marker collision, and legacy compatibility → test_run_log_metadata_preserves_text_boundaries_and_legacy_records.
         tdd: metadata repair GREEN — all 9 producer functions pass; GREEN additions check literal format-header text inside flags and exact decoded active-list output; no existing cases or assertions removed.
         repair: supersedes the flow-only encoding implementation; every new metadata value uses reversible percent escaping beneath a fixed file header, preventing caller text from creating control records; direct reads preserve trailing newlines; ordinary legacy records remain readable and migrate on update, and prior flow-encoded legacy records are decoded compatibly.
         repair: the independent flags/flow-encoding collision finding is resolved; JSONL schema and optional-jq behavior remain unchanged; no new runtime dependency or source/eval of user text.
         verification: single stable full suite 558 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n; git diff --check passes; shellcheck unavailable; evidence /tmp/orchestrail-producer-metadata-verified.log.
         finalization: atomic-validation reset for independent retry; plan remains done; no additional public interface or architecture update required; prior findings and protected TDD/git history retained without further compression.
         validation-final: independent pav-check DONE; all 9 producer functions pass; direct checks confirm all prior findings resolved and ordinary plus prior flow-encoded legacy records migrate and close with exact flow preservation.
         validation-final: AC-1 met — complete argument rejection, one redacted diagnostic, zero exit, unchanged accepted state; AC-2 met — exact aliases and ordered provenance; AC-3 met — unknown flow default, exact unrestricted-flow inheritance, safe IDs; AC-4 met — current helper workflows and synthetic/advisory names; AC-5 met — persistence-gated stdout, silent successful steps/closes, recoverable rejected close.
         validation-final: frozen original and both repair RED sets remain intact; later test changes only add coverage, and the two unrelated fixture amendments retain documented test-defect reasons; tests assert observable results with isolated stores and no skips or vacuous assertions.
         validation-final: stable complete-suite evidence /tmp/orchestrail-producer-metadata-verified.log confirms 558 passed, 0 failed, 2 configured hygiene skips; independently repeated producer slice and direct legacy checks; bash -n and git diff --check pass; shellcheck unavailable.
         proposals: batch review — Do Now: none; Do Later: none; Optional: extend test_run_log_metadata_preserves_text_boundaries_and_legacy_records with a prior flow_encoding=percent record containing newline and literal percent escapes. Independent direct checks pass this branch; a permanent fixture would protect its compatibility during future metadata changes. Proposal returned to orchestrator; nothing applied.
         closure: orchestrated pav-close complete; return plan delta T-01 -> reviewed to sole shared-plan writer. No child composite trigger applies. No code, tests, git, shared memory, plan, or historical logs changed.
         compression: auto audit retained protected notes, TDD/git evidence, and prior findings as superseded review history; no shared sections edited and no further compression required.

T-02 | read-only-run-linter | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery artifacts created
  target_files: `scripts/log-step.sh`
  blocker: none
  notes: Depends on T-01 to reuse its runtime vocabulary; edits the same helper after producer behavior.

T-03 | lint-aware-retrospective | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery artifacts created
  target_files: `workflows/retro.md`
  blocker: none
  notes: Depends on the linter's stable diagnostics and summary contract.

T-04 | vocabulary-docs-and-drift-gate | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery artifacts created
  target_files: `rules/run-log.md`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Compares documentation with the shared effective runtime definitions.

T-05 | isolated-acceptance-harness | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery artifacts created
  target_files: `tests/log-step.sh`
  blocker: none
  notes: Runs after all four behavior and contract subtasks are implemented.

## Solution Design

### Variants
→ archived to state-archive.md


### Decision

Use Variant 1. The spec requires writes and lint to use the same authoritative runtime definitions while a gate compares effective helper behavior with canonical documentation tables. Keeping the structured contract in the existing helper satisfies both requirements without a new module or runtime dependency. Expose the definitions in a stable machine-readable form for the existing validator to compare.

adr: not triggered — the spec fixes the vocabulary and validation strategy, and this choice applies existing single-source and non-blocking principles without introducing a new system boundary.

### Autonomous Decision

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---:|---:|---:|---:|---:|---:|
| Variant 1 — helper-owned structured contract | 4 | 5 | 5 | 5 | 4 | 23 |
| Variant 2 — shared shell contract module | 3 | 4 | 3 | 4 | 3 | 17 |
| Variant 3 — documentation parsed at runtime | 2 | 3 | 2 | 2 | 3 | 12 |

**Winner:** Variant 1 — it shares the effective runtime vocabulary across writes and lint and lets the contract gate inspect those same definitions without adding another runtime component.

**Anti-overengineering check:** passed. The selected approach adds only a structured contract export to an existing helper; it does not add a new runtime layer or dependency.

**Evidence:** The spec requires one authoritative runtime definition, the existing helper owns writes, the existing contract validator is a gate, and the project principles favor canonical formats and non-blocking logging.

### Scope

#### In
- Strict argument validation and exact legacy normalization for run-start, step, and run-end.
- Safe run identifiers, flow defaulting, advisory workflow-name checks, and non-blocking persistence semantics.
- Read-only linting with stable diagnostics and an accurate summary.
- Lint-aware retrospective reporting with invalid-line exclusion and usable denominators.
- Complete run-log documentation and structured contract-drift detection.
- An isolated executable smoke harness with temporary logs and workflow fixtures.

#### Out
- Historical log migration or repair.
- Token and cost accounting, hook-driven logging, or changes to future roadmap tasks.
- Privacy scanning of historical notes, workflow-name retroactive validation, new storage formats, or general locking and filesystem-transaction redesign.

### Rejected
→ archived to state-archive.md

### Off-limits
- Do not rewrite existing run logs or change their checksums.
- Do not make a write-time dependency on `jq`; lint may require it and must report unavailable checks honestly.
- Do not allow invalid events to advance sequence, timestamp, digest, or active-run state.
- Do not echo arbitrary raw values in diagnostics or add vocabulary definitions separate from the helper's runtime contract.
- Do not make logging failures block workflow callers or make the retrospective automatically edit implementation files.

### Invariants
- A rejected event has no event-file or active-metadata side effects.
- Logging error paths return zero and emit no success-shaped output.
- Runtime writes and lint use one effective vocabulary and mapping source.
- Lint is read-only, and retrospective metrics include only usable observations.
- Existing historical logs remain byte-for-byte unchanged.
- The contract validator remains a gate whose drift failures return nonzero.

### Acceptance Criteria
- Producer invocations enforce exact event-specific enums and integer rules, preserve specified alias provenance, and reject invalid inputs before state changes.
- Missing or empty start flow becomes `unknown`; failed starts do not print IDs, and rejected closes leave active metadata available for a later valid close.
- Step-name membership is derived from the current helper workflow directory; unknown names warn but valid events are written.
- Lint supports all required selectors, emits safe ordered JSON diagnostics and one accurate summary, reports partial checks, exits zero, and changes no files.
- Retrospective corpus diagnostics match all existing filters, invalid lines are excluded from metrics, affected telemetry is disclosed, and unusable closes are distinct from abandoned runs.
- Documentation contains the exact contract, and contract validation catches missing, extra, or changed values and mappings from either side.
- The executable smoke harness covers the specified behaviors in isolated temporary paths and leaves historical logs unchanged.
- The acceptance commands and shell syntax checks required by the spec pass before implementation is considered complete.

## Execution Report

- T-01: reviewed — strict producer validation and safe persistence; all independent findings repaired.
- T-02: not-started — read-only linter next.
- T-03: not-started — lint-aware retrospective.
- T-04: not-started — vocabulary documentation and drift gate.
- T-05: not-started — isolated acceptance harness.
- Verification: 558 passed, 0 failed, 2 conditional hygiene skips; nine producer groups, shell syntax, and whitespace pass.
- Run logging skipped because no configured executable shared helper was available.

## Improvement Proposals (T-01)

### Optional
- Add a permanent earlier flow-encoding metadata fixture in the planned isolated acceptance harness; independent direct verification already passes.

## Knowledge Snapshots

### Producer contract

branch: feat/run-log-producer-validation
expected_parent: 0abf4c192a109edd94d7ddca548c5236e88cbde9
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/tasks/completed/task-01-git-source-of-truth/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-01-producer-validation-and-writes/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-02-read-only-run-linter/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-03-lint-aware-retrospective/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-04-vocabulary-docs-and-drift-gate/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-05-isolated-acceptance-harness/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state-archive.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md
