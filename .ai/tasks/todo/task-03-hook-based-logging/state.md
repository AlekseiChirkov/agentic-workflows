spec_path: .ai/specs/03-hook-based-logging.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Tracked knowledge files are permitted and the blanket prohibition must be removed (source: user, 2026-10-22).
- Keep explicit staging and repository-owned tracking policy; preserve ignored state for consumer repositories that choose it (source: user; ADR-0012).
- Implement only the hook-focused harness/capability/registry scaffold needed here; preserve existing deployment targets and leave the larger harness migration outstanding. Selecting this specification is a narrow roadmap-order exception (source: user invocation; ADR-0009 Decisions 2, 5 and 7; spec 13 REQ-35/36/38; Arbiter).
- Hook availability is distinct from boundary coverage. Batched sub-agent skills and single-session internal transitions retain prompt logging unless explicitly observable (source: specification REQ-04; workflows/spec-run.md dispatch shape; Arbiter).
- Extend the existing producer additively; never replace its validated vocabularies, optional-jq legacy path or read-only lint guarantees (source: ADR-0011).
- Correlation state is private active metadata outside historical logs; explicit run/session/agent/checkpoint identity and an accepted-write receipt govern attribution and retries (source: specification REQ-01/03; Arbiter).
- Runtime remains Bash with jq for hooks and flock for serialization; unavailable hook dependencies select nonblocking approximate fallback. No new paid or model-driven tests (source: existing Bash/jq runtime; specification notes and REQ-05).
- The owner requests full autonomous specification and implementation, including routine defect repairs, with analysis delegated for decisions. Full resolved interfaces are documented in the specification before their implementation (source: user, 2026-10-26; Arbiter).
- Resume accepts the recorded implementation tip or verified knowledge-only snapshots above it; each snapshot records its exact parent and changed paths instead of its own hash (source: ADR-0010 Decision 2; completed task-02 Knowledge Snapshots; Arbiter).
- flow: full — gate: 1 fail (more than three files), 2 fail (correlation contract), 3 fail (shipped logging behavior), 4 pass (no database migration).

## Open Questions (batch)
None.

## Authorized Prerequisite
- branch: fix/knowledge-base-tracking-policy
- base_branch: main
- base_commit: 7477bacce34b58d3c683a4329b82778b0d330a7e
- commits: be14570c80ad82db6ddd77b86e90e13f0e7aeb5d test(sync): preserve repository knowledge tracking policy, 9bb1358be2ee9d09f83520239ff30baa29c05906 fix: respect repository knowledge tracking policy
- status: reviewed
- tests: RED then GREEN for repository tracking policy; independent review PASS. Full validation: 575 pass, stale archived-spec ledger path corrected and focused recheck PASS, two optional hygiene skips.
- pr: #22 draft; origin verified and branch published after destination checks

## Decomposition
decomposition: complete
Five sequential leaves. Every leaf owns one coherent component and frozen behavior tests; none is a composite.

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Choose the additive adapter. Dispatch and completion are clock-stamped by executable tooling. Correlation is explicit and separate from historical logs. Preserve old producer behavior for ordinary calls; new optional identity/interval fields and acceptance receipts support safe hook delivery. Missing dependencies or incomplete boundaries retain approximate prompt logging. Deduplication promises cover ordinary repeated deliveries under serialization; partial operating-system writes are disclosed rather than claiming crash-proof exactly-once persistence.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Prompt-only | 5 | 5 | 5 | 3 | 5 | 23 |
| Additive adapter | 4 | 5 | 5 | 5 | 4 | 23 |
| Event daemon | 1 | 2 | 1 | 3 | 1 | 8 |
Winner: Additive adapter. Prompt-only is ineligible because it fails explicit hook and timing requirements; the adapter is the highest-scoring eligible variant.
Anti-overengineering check: passed; private correlation state and serialization solve current attribution/deduplication requirements.
Evidence: architecture P3/P4/P9/P10; ADR-0011; specification REQ-01 through REQ-05.

### Scope
#### In
Additive producer identity/span contract; dispatch and stop adapter; user-level owned hook lifecycle; minimal capability and project registry integration; coverage-aware prompt fallback; retrospective interval metrics and isolated fixtures.
#### Out
Cost/token normalization, git enforcement hooks, broad harness retirement/renaming, model-paid tests, historical log rewrites, automatic merges, and completion of the wider harness migration.

### Rejected
→ archived to state-archive.md

### Off-limits
- Do not read historical logs for event attribution or rewrite historical telemetry.
- Do not attach an event to a guessed or newest active run.
- Do not overwrite unowned user hooks or settings.
- Do not push to the default branch, merge, force-push, or delete branches.
- Do not change cost/token schemas or implement git rails.

### Invariants
- Invalid input is rejected completely before sequence, timestamps, accepted identity or metadata change; failures are safe diagnostics and exit zero.
- The shared effective runtime vocabulary and canonical rule remain synchronized; legacy events and prompt calls remain valid.
- Every accepted hook event has a unique explicit correlation identity and executable clock-stamped interval; unknown skill is allowed only for unambiguous single-session attribution.
- A structured marker supplies only canonical outcome, never narrative inference or model-written duration.
- Only manifest-owned settings entries may be merged or removed.
- Hooks availability never substitutes for demonstrated workflow boundary coverage.

### Acceptance Criteria
- Hook manifest declares SubagentStop and Stop, derives skills from invocation records, requires explicit dispatch correlation and exact report markers, and gates registered projects.
- Two interleaved runs, duplicate/out-of-order deliveries and malformed or ambiguous events do not cross-attribute or duplicate accepted events.
- User-level install/uninstall is idempotent, preserves unrelated settings, and supports paths containing spaces.
- Uncovered and hooks-unavailable steps retain prompt-driven approximate notes; retrospective reports label those runs.
- Fully covered sequential spans account for wall time within five percent; nested and parallel reports separate inclusive/exclusive/worker time, gaps, overlap and waiting without claiming CPU work.
- Existing producer/lint tests, full contract validation and isolated hook fixtures pass without changing real logs.

## Subtask Progress

T-01 | Validated correlated event writes | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: DoD met — four acceptance criteria verified independently; serialized receipts, retry rollback and legacy compatibility validated; one optional regression proposal recorded
  target_files: scripts/validate-contracts.sh, scripts/log-step.sh, rules/run-log.md
  blocker: none
  notes: tdd: integration and contract — eight tests, AC coverage 4/4; scoped runbook validator fixtures executed against unchanged producer
         tdd: red digest — AC-1 → test_run_log_correlated_concurrent_runs_preserve_identity, test_run_log_correlated_duplicates_and_out_of_order_are_idempotent; AC-2 → test_run_log_correlated_invalid_fields_preserve_accepted_state; AC-3 → test_run_log_correlated_lint_accepts_legacy_and_rejects_invalid_spans, test_run_log_correlated_contract_detects_bidirectional_drift, test_run_log_correlated_clock_boundaries_preserve_milliseconds; AC-4 → test_run_log_correlated_append_failure_allows_retry, test_run_log_correlated_metadata_failure_allows_retry
         tdd: test amended — test_run_log_correlated_clock_boundaries_preserve_milliseconds — cache the public run path before run-end because close intentionally removes active lookup metadata; assertions unchanged
         tdd: added — test_run_log_correlated_waiting_and_parent_identity_are_explicit — explicit waiting/work spans and same-run/session parent scope requested during implementation
         tdd: added — historical identities ending in a newline are rejected by read-only lint, matching producer validation
         tdd: added — test_run_log_correlated_clock_fraction_preserves_leading_zeros — deterministic executable date at .006500000 seconds failed with 650 milliseconds; full nanosecond conversion preserves 006 milliseconds on affected coreutils versions; original real-clock assertions unchanged
         tdd: green — all eight frozen RED checks retained; 10 correlated checks and 35 focused producer/lint/retro checks pass; full validator 586 passed, 0 failed, 2 optional hygiene skips; canonical contract gate and shell syntax pass; ShellCheck unavailable
         architecture.md: existing producer interface update proposed to orchestrator; plan transition T-01 → done and shared-file compression remain orchestrator-owned
         acceptance: all 4 criteria pass; recoverable append/metadata failures issue no receipt and retry once; process death and failed rollback remain outside the documented deduplication guarantee
         validation: independent base-to-HEAD review; all four acceptance criteria met; eight frozen RED checks retained without weakening; one documented boundary-fixture correction and additive tests audited
         validation: 35 isolated acceptance checks, full validator 586 passed/0 failed/2 optional hygiene skips, task validator 17 passed/0 failed, canonical contract gate, shell syntax and committed whitespace checks passed
         validation: independent injected partial append restored the exact store with no receipt; retry accepted sequence 1 once; mixed legacy/correlated concurrency, bounded identities, private metadata and closed-run rejection passed
         validation: ShellCheck unavailable; deployment-only runbook build intentionally omitted to preserve the real home; full contract suite includes isolated sync coverage
         proposals: Optional — strengthen the append-failure regression to inject failure during event output; independent partial-write rollback probe already passed; shared proposal section returned to orchestrator
  branch: feat/correlated-event-writes
  base_branch: fix/knowledge-base-tracking-policy
  base_commit: 9bb1358be2ee9d09f83520239ff30baa29c05906
  commits: be65b3dc956a3e156ad95d4b3535765ea41b6746 test(logging): cover correlated events and precise intervals, a10aeb3e42d2c74448e11939186b82cb8e205794 feat(logging): accept correlated checkpoint intervals
  pr: #23 draft

T-02 | Explicit hook dispatch and completion | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: discovery complete
  target_files:
  blocker: none
  notes: tdd: integration and contract fixtures required before implementation

T-03 | Owned user hook installation | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: discovery complete
  target_files:
  blocker: none
  notes: tdd: integration and contract fixtures required before implementation

T-04 | Coverage-aware workflow logging | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: discovery complete
  target_files:
  blocker: none
  notes: tdd: integration and contract fixtures required before implementation

T-05 | Honest timing and end-to-end evidence | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: discovery complete
  target_files:
  blocker: none
  notes: tdd: integration and contract fixtures required before implementation

adr: .ai/adr/0013-task-03-correlated-hook-logging.md (Provisional)

## Improvement Proposals (T-01)

### Do Now
None.

### Do Later
None.

### Optional
- Strengthen the append-failure regression to inject failure during event output. Its current directory fixture rejects before append. Independent partial-append fault injection already verified rollback and exactly one accepted retry. Deferred as optional; all acceptance criteria are verified.

## Knowledge Snapshots

### Reviewed correlated event contract and full specification

branch: feat/correlated-event-writes
expected_parent: a10aeb3e42d2c74448e11939186b82cb8e205794
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/adr/0012-task-unknown-knowledge-tracking-policy.md
- .ai/adr/0013-task-03-correlated-hook-logging.md
- .ai/adr/index.md
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/completed/task-01-git-source-of-truth/state.md
- .ai/tasks/todo/task-03-hook-based-logging/T-01-correlated-event-contract/description.md
- .ai/tasks/todo/task-03-hook-based-logging/T-02-hook-event-adapter/description.md
- .ai/tasks/todo/task-03-hook-based-logging/T-03-user-hook-installation/description.md
- .ai/tasks/todo/task-03-hook-based-logging/T-04-workflow-logging-coverage/description.md
- .ai/tasks/todo/task-03-hook-based-logging/T-05-retrospective-timing/description.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state-archive.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md
