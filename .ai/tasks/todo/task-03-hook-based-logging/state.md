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
- Hooks remain Bash/jq/flock; offline exact timing uses Python 3 standard library with existing jq-backed lint for eligibility. Unavailable dependencies disclose unavailable coverage without blocking work. No new paid or model-driven tests (source: existing runtime patterns; specification notes and REQ-05; Arbiter).
- The owner requests full autonomous specification and implementation, including routine defect repairs, with analysis delegated for decisions. Full resolved interfaces are documented in the specification before their implementation (source: user, 2026-10-26; Arbiter).
- Resume accepts the recorded implementation tip or verified knowledge-only snapshots above it; each snapshot records its exact parent and changed paths instead of its own hash (source: ADR-0010 Decision 2; completed task-02 Knowledge Snapshots; Arbiter).
- flow: full — gate: 1 fail (more than three files), 2 fail (correlation contract), 3 fail (shipped logging behavior), 4 pass (no database migration).

### Description Amendments
- 2026-10-26: The owner requested a full autonomous specification. Resolved marker/native schema, receipt/fallback ownership, project selection, installation recovery and exact timing contracts were added to the specification before their corresponding components were implemented. Sources: owner instruction, existing roadmap decisions, cited Arbiter analyses and native documentation. No acceptance criterion was weakened.
- 2026-10-26: Independent adapter review exposed Markdown fence eligibility errors; raw-number analysis exposed rounding at explicit receipt/private-state validation boundaries. CommonMark lexical rules and fresh canonical integer encodings clarify the existing invalid-input contract. Separate failing regression commits precede the repair; historical lint compatibility remains unchanged.

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

T-02 | Explicit hook dispatch and completion | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: DoD met — all six acceptance criteria independently verified; fence and exact-token repairs validated; 38 frozen adapter checks and full 587-check contract gate pass
  target_files: hooks/log-step-hook.sh, tests/log-step-hook.sh, rules/run-log.md, scripts/validate-contracts.sh
  blocker: none
  notes: tdd: integration and contract — 15 tests, AC coverage 6/6; isolated HOME, XDG config/state, checkout and log roots
         tdd: red digest — AC-1 → test_hook_interleaved_runs_preserve_exact_identity, test_hook_concurrent_duplicate_deliveries_append_once, test_hook_closed_run_delivery_never_reopens; AC-2 → test_hook_dispatch_private_correlation_is_explicit, test_hook_missing_and_conflicting_native_fields_preserve_pending, test_hook_inactive_project_gates_before_transcript_and_state_reads; AC-3 → test_hook_session_unknown_and_unique_skill_remain_distinct; AC-4 → test_hook_native_schema_and_input_limits_warn_safely, test_hook_bounded_transcript_tail_requires_dispatch_input; AC-5 → test_hook_accepted_status_blocks_fallback_and_returns_receipt, test_hook_fallback_first_owns_route_even_when_legacy_write_fails, test_hook_frozen_retry_requires_matching_receipt; AC-6 → test_hook_marker_canonicality_and_exact_tuple_reject_ambiguity, test_hook_native_evidence_uses_input_and_unique_invocation_ids; shared contract → test_hook_documented_dispatch_marker_and_ownership_contract
         tdd: red evidence — bash scripts/validate-contracts.sh --hook-adapter-only exits 1: 14 explicit canonical dispatch-marker assertions fail; canonical rule test fails on missing ORCHESTRAIL_DISPATCH_V1; no fixture/import/syntax failures
         tdd: frozen test sha256 — a617509fa241ae4e3fd422032a07ee9c35d11817d963e2d11628c98d75d6ab94
         tdd: baseline coverage — later scenario assertions are frozen but cannot execute until missing dispatch is implemented; documentation independently fails against existing rule
         tdd: added — 13 independent edge checks cover nested registry, invalid fallback, route concurrency, dependencies, exact input bytes, native evidence, parent/waiting, missing start, strict receipts, rotated retries, Unicode bounds, skill suffixes and corrupted cached attribution
         tdd: green — all 15 frozen test names and bodies unchanged; 28 adapter checks pass, 35 isolated producer/lint/retro checks pass; full validator 587 passed, 0 failed, 2 optional hygiene skips; canonical runtime gate, individual scripts/hooks/tests shell syntax and whitespace checks pass
         acceptance: all 6 criteria pass through executable isolated fixtures; cached corruption never cross-attributes; durable retries retain native/report binding; process death or lost receipt remains explicitly uncertain
         verification: ShellCheck unavailable; real-home deployment intentionally omitted; full validation includes isolated deployment coverage; real settings and historical logs untouched
         architecture.md: adapter component and new focused validator mode proposed to orchestrator; plan transition T-02 → done and shared compression are orchestrator-owned
         validation: NEEDS WORK — acceptance criteria 2/4/6 incomplete for ineligible fenced report markers; important defect at hooks/log-step-hook.sh:217-223 tracks only delimiter character, ignoring opening length and valid closing syntax
         validation: isolated native delivery with a four-backtick opener, three-backtick line, canonical report and four-backtick closer emits no warning, appends one precise event and reaches accepted while the report remains inside code; same result for four/three tildes and a closing candidate with trailing text
         validation: inverse fence case rejects an eligible marker after the actual four-backtick close; add regressions covering fence lengths, invalid closing suffixes and genuine outside reports before repair
         validation: all 15 frozen RED tests and their fixture methods remain structurally unchanged; initial test digest matches a617509fa241ae4e3fd422032a07ee9c35d11817d963e2d11628c98d75d6ab94; 13 additive checks audited
         validation: focused adapter 28 checks, producer/lint/retro 35 checks, canonical runtime contract, task artifacts 17 checks, shell syntax and committed whitespace pass; ShellCheck unavailable; no real-home deployment; full validator started but not relied on after reproducible rejection failure
         validation: step 1 stopped on NEEDS WORK; no improvement or close step executed; no plan transition or architecture delta
         tdd: repair red digest — AC-2/4/6 → test_hook_report_short_fence_candidates_keep_marker_in_code, test_hook_report_nonclosing_fence_suffixes_and_tabs_keep_marker_in_code, test_hook_report_real_matching_or_longer_closers_allow_outside_marker, test_hook_report_openers_respect_indentation_and_info_string_syntax, test_hook_report_line_separators_preserve_fence_and_marker_boundaries
         tdd: repair red evidence — canonical validator --hook-adapter-only with five named groups exits 1; all five groups fail, with 24 substantive subcase assertion failures across 26 cases: fenced examples append or genuine outside markers remain pending; no fixture/import/syntax errors
         tdd: repair frozen set — all 28 existing test names and bodies unchanged; five additive repair groups; fixture SHA256 8d1cd100b6e7c0fee7b2d39a22ad29336a5901c8a08ada4558027211398ab2fc
         repair decision: bounded top-level CommonMark lexical fences retain character and run length; opening/closing indentation 0–3 ASCII spaces, no leading tab; backtick info excludes backticks, closing suffix only spaces/tabs; LF/CRLF/lone CR are separators without trimming JSON; Arbiter cites CommonMark sections 2.1, 2.2 and 4.5
         tdd: numeric repair red digest — AC-2/4/5/6 → test_hook_raw_fractional_or_exponent_receipt_sequence_leaves_delivery_uncertain, test_hook_raw_noncanonical_cached_receipt_sequence_never_returns_acceptance, test_hook_raw_noncanonical_cached_start_never_forwards_frozen_payload, test_hook_raw_noncanonical_cached_end_never_forwards_frozen_payload, test_hook_fresh_schema_version_requires_exact_integer_token
         tdd: numeric repair red evidence — five named groups through canonical --hook-adapter-only exit 1 with substantive acceptance/status/forwarding failures; raw fractional or exponent encodings round into apparently integral seq/start/end/schema values; no fixture/import/syntax failures
         tdd: numeric repair frozen set — all 33 existing test names and bodies unchanged; five additive numeric groups; fixture SHA256 afd5a5019a207c3c3eb6324eb6b3c331fa6489f8e2b6da186e27032829cf43e5
         repair: fence GREEN — all 33 frozen checks pass; producer 35 checks and full validator 587 passed, 0 failed, 2 optional skips; later exact-token defect requires new RED before completion
         tdd: repair green — all 38 frozen tests unchanged byte for byte from the numeric RED checkpoint; fence and numeric regression groups pass; producer/lint/retro 35 checks pass; stable full validator 587 passed, 0 failed, 2 optional hygiene skips
         verification: repaired source passes canonical runtime contract, per-file scripts/hooks/tests shell syntax and whitespace checks; ShellCheck unavailable; real-home deployment omitted and real settings/logs untouched
         acceptance: repaired AC-2/4/5/6 verified by ten added regression groups; complete original AC mapping retained; fenced examples cannot supply outcomes and raw fractional/exponent numeric encodings cannot authorize cached delivery or acceptance
         finalization: atomic execution complete; validation remains failed until independent recheck; no new component or export; plan transition T-02 → done and shared architecture/decision verification remain orchestrator-owned
         validation: recheck DONE at b17ca232 — all six acceptance criteria met; initial fence finding resolved; no critical or important findings remain
         validation: original 15, expanded 28, fence 33 and numeric 38 frozen test stages retain every test and fixture method byte for byte; final fixture SHA256 afd5a5019a207c3c3eb6324eb6b3c331fa6489f8e2b6da186e27032829cf43e5 matches the numeric RED checkpoint
         validation: independent shorter-fence and invalid-suffix probes now warn and preserve pending state and logs; real outside reports and quote/list container-boundary controls accept correctly
         validation: independent raw receipt probes reject rounded fractions, exponent and underflow forms, negative zero and above-maximum integers; canonical positive integers through the exact maximum accept; quoted numeric text stays a string; malformed private numbers and concatenated records cannot forward or return acceptance
         validation: repaired adapter 38 checks and producer/lint/retro 35 checks pass; stable full gate 587 passed, 0 failed, 2 optional hygiene skips; runtime contract, task artifacts 17 checks, per-file shell syntax and committed whitespace pass
         validation: ShellCheck unavailable; no real-home deployment or historical-log access; documented process-death and lost-receipt uncertainty remains an explicit persistence limitation
         validation: pav-propose batch complete — no proposals; pav-close complete in orchestrated mode; plan delta T-02 → reviewed returned to orchestrator; protected audit retained and shared compression remains orchestrator-owned
  branch: feat/hook-event-adapter
  base_branch: feat/correlated-event-writes
  base_commit: 6695f37ac3c6c3fe979f47fcdf84eadf6c475962
  commits: a40270437130e317d67266809ba1c669fc3ef29d test(hooks): define explicit checkpoint delivery behavior, 3ba0e22e03ad5451e7c3afab206dd0ad047a0694 feat(hooks): correlate native completion checkpoints, cb4cf524489ebf83acaa6e6ac1fd6463c1c71f8f test(hooks): cover fenced report eligibility, 9c0a0102d9dd8c7214522ec0ff049e8bf42cc713 test(hooks): reject noncanonical protocol numbers, b17ca232dbde31705a0b375890348059451be336 fix(hooks): validate report fences and exact protocol numbers
  pr: #24 draft

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

### Reviewed native completion adapter

branch: feat/hook-event-adapter
expected_parent: b17ca232dbde31705a0b375890348059451be336
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/memory/architecture.md
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md
