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
- Installer and registry registration use Python 3 standard-library support; jq/flock availability gates install, while saved-state uninstall/recovery requires Python only. Exact settings numbers remain lossless and ownership equality is mathematical (source: full installer specification; Arbiter; installer lifecycle fixtures).
- Offline timing uses an explicit-file Bash CLI and separate source-only Python engine. One file represents one run; distinct files claiming the same run identity are ambiguous. Complete producer lint on unchanged private copies gates all metrics, which use decimal-string durations and exact ratios (source: full timing specification; Arbiter; principles/code-quality.md single responsibility and scripts/install-hooks.sh source-relative delegation).
- The owner requests full autonomous specification and implementation, including routine defect repairs, with analysis delegated for decisions. Full resolved interfaces are documented in the specification before their implementation (source: user, 2026-10-26; Arbiter).
- Resume accepts the recorded implementation tip or verified knowledge-only snapshots above it; each snapshot records its exact parent and changed paths instead of its own hash (source: ADR-0010 Decision 2; completed task-02 Knowledge Snapshots; Arbiter).
- flow: full — gate: 1 fail (more than three files), 2 fail (correlation contract), 3 fail (shipped logging behavior), 4 pass (no database migration).

### Description Amendments
- 2026-10-26: The owner requested a full autonomous specification. Resolved marker/native schema, receipt/fallback ownership, project selection, installation recovery and exact timing contracts were added to the specification before their corresponding components were implemented. Sources: owner instruction, existing roadmap decisions, cited Arbiter analyses and native documentation. No acceptance criterion was weakened.
- 2026-10-26: Independent adapter review exposed Markdown fence eligibility errors; raw-number analysis exposed rounding at explicit receipt/private-state validation boundaries. CommonMark lexical rules and fresh canonical integer encodings clarify the existing invalid-input contract. Separate failing regression commits precede the repair; historical lint compatibility remains unchanged.
- 2026-10-26: Independent installer review found missing Python annotations and oversized product functions. Apply the repository default Python 3.11 minimum, typed stdlib sources and focused helpers; guard unsupported interpreters before engine startup. Add failing version-guard regressions before repair. Annotation-only fixture amendments preserve all executable assertions; any retained CLI-adapter signature exception is named and justified as code-quality permits. Sources: principles/python-standards.md, principles/code-quality.md and Arbiter; no functional acceptance criterion weakened.
- 2026-10-26: Read-only cross-leaf standards audit found 52 newly introduced adapter fixture functions and 9 correlated producer fixture helpers needing annotations. Include annotation-only harmonization and a scoped regression in T-05's complete acceptance harness before its RED freeze; keep original test bodies and generated producer bytes intact. Explicitly justify the single long adapter recovery scenario and necessary CLI helper parameter shapes under code-quality. Baseline Python snippets and setup registry introduce no affected functions and remain outside this repair. Sources: Arbiter main-to-tip AST audit, python-standards and complete-harness acceptance criterion.

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

T-03 | Owned user hook installation | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close complete — all acceptance criteria and Python standards reviewed; isolated 39-test lifecycle and 588-check full gate pass
  target_files: tests/hook-install.sh, scripts/validate-contracts.sh, scripts/install-hooks.sh, scripts/install-hooks.py, harness/claude/hooks.json, harness/claude/capabilities.md, harness/codex/capabilities.md, scripts/setup-new-project.sh, scripts/sync.sh
  blocker: none
  notes: tdd: integration and contract — 32 tests, AC coverage 4/4; disposable HOME, XDG config/state, source and project trees; no real settings/log access
         tdd: red digest — AC-1 → test_hook_install_repeated_lifecycle_preserves_unrelated_settings, test_hook_install_preexisting_identical_entries_remain_unowned, test_hook_uninstall_changed_and_moved_entries_survive, test_hook_uninstall_equal_copies_preserve_unowned_multiplicity_and_empty_groups, test_hook_uninstall_removes_only_created_newly_empty_groups, test_hook_ownership_object_equality_ignores_key_order_and_numeric_spelling, test_hook_ownership_omitted_fields_and_changed_argument_arrays_remain_unowned, test_hook_install_concurrent_operations_are_serialized_and_parseable
         tdd: red digest — AC-2 → test_hook_install_source_precedence_and_quoted_paths_use_literal_arguments, test_hook_setup_registers_canonical_roots_idempotently_and_adapter_gates, test_hook_setup_concurrent_registration_preserves_existing_roots, test_hook_setup_default_config_location_preserves_custom_project_files, test_hook_setup_invalid_registry_or_newline_root_preserves_existing_entries
         tdd: red digest — AC-3 → test_hook_install_invalid_cli_and_manifest_never_mutate_settings, test_hook_install_malformed_settings_preserve_exact_bytes, test_hook_install_malformed_receipt_preserves_both_files, test_hook_install_preserves_exact_json_numbers_and_strings, test_hook_install_missing_dependencies_report_unavailable_without_mutation, test_hook_manifest_and_capabilities_describe_available_mechanism_and_partial_coverage, test_hook_sync_embeds_capabilities_once_and_preserves_all_deployment_targets, test_hook_sync_unavailable_installation_still_refreshes_consumer_projects
         tdd: red digest — AC-4 → test_hook_install_upgrade_preserves_changed_old_handler, test_hook_receipt_control_numbers_cannot_gain_deletion_ownership, test_hook_recovery_before_image_restores_previous_then_recomputes_install, test_hook_recovery_after_image_finalizes_then_recomputes_install, test_hook_recovery_external_edit_preserves_settings_and_prepared_receipt, test_hook_recovery_uninstall_uses_saved_state_after_old_source_disappears, test_hook_recovery_malformed_prepared_receipt_never_replaces_settings, test_hook_transaction_interruption_before_settings_recovers_absent_image, test_hook_transaction_interruption_after_settings_recovers_committed_image, test_hook_transaction_rechecks_before_image_after_preparing_ownership, test_hook_transaction_replacement_failure_preserves_settings_and_allows_retry
         tdd: red evidence — bash scripts/validate-contracts.sh --hook-install-only exits 1; all 32 groups fail with 37 substantive assertions on missing structured lifecycle result, registry, manifest or installation disclosure; zero errors and no fixture/syntax failures
         tdd: frozen test sha256 — 9d431372d11ba0d1cfc8af70cfe05113c85883dfdea63762a7ea39b278fbaaa0
         tdd: baseline coverage — later lifecycle, multiset, raw-control, recovery, dependency and deployment assertions are frozen behind missing first-install behavior and execute during implementation
         decisions: installer-only Python standard-library JSON engine preserves numeric lexemes and exact mathematical equality; sidecar controls remain strict canonical bounded integers; public committed/prepared envelopes include null absence; arbiter reviewed fixture-only destination-aware replacement interruption and external-edit injection
         tdd: review amendment — numeric-preservation fixture now asserts exact raw large/precise/huge/tiny/negative-zero tokens after install and uninstall, allowing surrounding JSON whitespace; all three successful-uninstall receipt assertions allow absent ownership or a structurally valid empty committed receipt; prepared persistence and owned-handler removal assertions remain; no implementation started and remaining assertions retained; repeated canonical scoped run still has 32 failing groups, 37 substantive failures and zero errors
         tdd: test amended — test_hook_setup_registers_canonical_roots_idempotently_and_adapter_gates — supply native event cwd instead of empty payload while preserving quiet inactive and registered warning assertions; specification requires event cwd and existing adapter validates it before registry selection; arbiter confirmed the original process-cwd premise was unsupported
         tdd: added — test_hook_setup_trailing_newline_is_rejected_and_sibling_prefix_stays_inactive — lossless physical cwd registration rejects trailing newline, sibling path prefix stays inactive, and missing native cwd still warns without mutation
         tdd: added — test_hook_uninstall_recovers_without_native_dependencies_but_requires_python; test_hook_receipt_literal_null_is_invalid_and_nullable_next_recovers_absence — missing native runtime does not block saved-state removal, missing Python preserves prepared state, literal null is not an absent receipt, and nullable next ownership recovers actual absence
         decisions: native jq/flock dependencies gate installation only; Python is required for both operations and supplies installer locking; arbiter confirmed saved-state uninstall must survive disappeared adapter dependencies
         verification: individual shell syntax and whitespace review pass; ShellCheck unavailable; no product implementation written; awaiting orchestrator test-only commit and resume
         tdd: green — all 32 committed RED groups retained and passing, plus 3 additive edge groups; 31 frozen test bodies unchanged byte for byte and one approved native-event-cwd fixture correction; no ownership, recovery, numeric or dependency assertion weakened
         tdd: current fixture sha256 — e2c24f0fb9ffa04012991d1bd876ceb1a0cedb4a92dad7a3a6b7a15ce8a01397; original committed RED digest retained above
         acceptance: AC-1 verified by idempotent lifecycle, preexisting identical entries, exact multiset/group quotas, changed/moved entries, array/omitted-field semantics, exact numeric equality and concurrent operations; all unrelated user data retained
         acceptance: AC-2 verified by canonical setup registration, aliases, idempotency, concurrency, custom/default XDG roots, malformed registry, newline/trailing-newline rejection, event-cwd gating, sibling-prefix inactivity and literal source precedence with spaces/quotes
         acceptance: AC-3 verified by malformed settings/ownership/manifest/CLI cases and missing Python/jq/flock no-mutation diagnostics; native manifest and capability declarations distinguish support, current installation and actual checkpoint coverage; isolated sync preserves existing global and consumer deployments after unavailable installation
         acceptance: AC-4 verified by changed/disappeared source upgrades, strict canonical sidecar controls and duplicate claim rejection, before/after/absent/external prepared images, process death after both persisted boundaries, replacement failure/retry and nullable-next recovery through uninstall without native dependencies
         verification: lifecycle 35/35, existing adapter 38/38, producer/lint/retro 35/35, canonical runtime contract, all Bash files individually, in-memory Python syntax and whitespace passed; stable full validator 588 passed, 0 failed, 2 optional hygiene skips; task validator 17 passed, 0 failed, 2 skips; ShellCheck unavailable
         verification logs: /tmp/hook-install-green.txt, /tmp/hook-adapter-regression.txt, /tmp/hook-producer-regression.txt, /tmp/hook-full-contracts.txt, /tmp/hook-task-contracts.txt; no source edits occurred while compatibility/full gates read it
         architecture.md: deltas returned to orchestrator — source-only installer Python engine, native manifest/capabilities, focused/default lifecycle acceptance, serialized setup-only registry and nonblocking sync status embedding; no shared architecture or ADR writes by implementer
         finalization: orchestrated mode; plan delta T-03 → done returned to orchestrator; independent validation remains not-started; protected notes preserved and shared compression remains orchestrator-owned
         limitations: real-home deployment and live/model invocation omitted by instruction; all fixtures use disposable homes/config/state/projects and no real settings or historical logs; individual atomic replacements and recoverable prepared state do not claim cross-file power-loss durability
         validation: independent pav-check NEEDS WORK — all four acceptance criteria met; no functional ownership, settings preservation, recovery, registry or deployment defect found
         validation: important — scripts/install-hooks.py:34 and :50 onward omit mandatory type annotations in all 27 functions/methods; tests/hook-install.sh:24 onward omits return annotations in all 50 Python fixture functions/methods; add typed signatures and class attributes without unexplained Any (principles/python-standards.md:6,10-13)
         validation: important — scripts/install-hooks.py:323 apply has 57 lines and four parameters without an explicit justified deviation; conform to focused functions of at most 30 lines and three parameters (principles/code-quality.md:6-7,82-85)
         arbiter: scripting-specific standards exemption exists? → none found; standard-library requirement overrides external Pydantic dependency only, not annotations or function shape (source: principles/python-standards.md; principles/code-quality.md; .ai/principles/architecture.md; resolved installer specification)
         validation: frozen RED SHA256 matches 9d431372d11ba0d1cfc8af70cfe05113c85883dfdea63762a7ea39b278fbaaa0; all 32 RED tests retained, 31 original bodies identical, one documented native-event-cwd correction, three additive tests, no skips/xfail or vacuous assertions; AC coverage 4/4
         validation: single stable isolated full gate 588 passed, 0 failed, 2 optional hygiene skips; lifecycle and adapter acceptance included; runtime contract pass; task gate 17 passed, 0 failed, 2 skips; all Bash syntax, in-memory Python compile and diff whitespace pass; ShellCheck unavailable
         validation: additional disposable-home probes preserve a near-equal decimal handler and safely retire the maximum canonical quota when fewer occurrences remain; no real settings, deployment or historical log access; full log /tmp/hook-validator-full.txt, runtime /tmp/hook-validator-runtime.txt, task /tmp/hook-validator-task.txt
         validation: pav-propose and pav-close not run because pav-check is NEEDS WORK; no shared-file or product/test/git writes; root owns repair routing and plan/shared deltas
         tdd: repair red digest — Python runtime support → test_hook_install_unsupported_python_preserves_settings_and_ownership, test_hook_uninstall_unsupported_python_preserves_settings_and_ownership, test_hook_unusable_python_reports_unsupported_before_either_operation; mandatory implementation standards → test_hook_installer_functions_follow_public_python_standards
         tdd: repair red evidence — canonical --hook-install-only with four new named groups exits 1 with five substantive assertion failures: old interpreter installs/removes, unusable interpreter reports the wrong reason, and Number lacks its mandatory attribute annotation; zero fixture/syntax errors; unchanged product still passes all 35 previous lifecycle checks after annotation-only fixture amendments
         tdd: repair frozen fixture sha256 — 8a1d2b65c2cd9cc83877eb9d2c2b29e2a79363ae1e6f4f74c3379e7d3eac58a0
         tdd: test amended — add mandatory signature/class-attribute annotations to all existing fixture functions and typed forwarding signatures/prelude to three generated fault adapters; AST audit preserves all 50 previous executable bodies, with only annotation metadata and generated typing prelude normalized; injected destinations, replacement ordering, exits, assertions and existing callsites are unchanged
         standards: narrowly justified parameter exceptions — raw_call exposes command arguments plus environment/source options and call adds expected status; retain their four/five parameters including self to preserve frozen CLI scenario callsites. Generated replacement callbacks retain src/dst plus ParamSpec positional/keyword forwarding because they must substitute for os.replace/os.rename without dropping native arguments. No fixture function exceeds 30 source lines, so no line-length deviation is claimed.
         repair verification: /tmp/hook-standards-repair-red.txt and /tmp/hook-annotation-characterization.txt; fixture Bash syntax, all fixture signature annotations, exact normalized body audit and whitespace pass; no product edits in repair RED; validation remains failed pending independent recheck
         repair implementation: all installer functions and class attributes have standard-library type annotations without Any; Installation/Snapshot/Update dataclasses carry coherent operation/state data; focused load/recover/plan/stage/commit helpers replace the oversized four-parameter function while retaining individual atomic writes, prepared persistence, before-image recheck and replacement ordering
         repair implementation: Bash rejects Python older than 3.11 or unusable interpreters before engine startup with unsupported-python; missing interpreter keeps missing-dependency, native hook/ordinary logging dependencies remain unchanged, capability prerequisites identify Python 3.11 or newer
         repair checkpoint: all 39 frozen groups pass; unchanged repair fixture SHA256 8a1d2b65c2cd9cc83877eb9d2c2b29e2a79363ae1e6f4f74c3379e7d3eac58a0; in-memory syntax and structural annotations/30-line/3-parameter checks pass; source frozen for compatibility and full stable validation
         tdd: repair green — exact 39-test repair RED set unchanged byte for byte from the test-only checkpoint; fixture SHA256 remains 8a1d2b65c2cd9cc83877eb9d2c2b29e2a79363ae1e6f4f74c3379e7d3eac58a0; unsupported install/uninstall, unusable interpreter and public standards regressions pass without weakening previous ownership/recovery assertions
         repair verification: lifecycle/runtime/standards 39 passed, adapter 38 passed, producer/lint/retro 35 passed, canonical runtime contract passed, every Bash file individually and in-memory Python syntax passed; installer annotations resolve at runtime, all source functions have at most 30 lines and three parameters, no unexplained Any; whitespace passed and ShellCheck remains unavailable
         repair verification: ONE unchanged-source full gate completed with 588 passed, 0 failed and 2 optional hygiene skips; /tmp/hook-repair-full.txt; compatibility logs /tmp/hook-repair-adapter.txt, /tmp/hook-repair-producer.txt and /tmp/hook-repair-runtime.txt; focused log /tmp/hook-standards-repair-green.txt; no product source edit during verification
         repair finalization: only scripts/install-hooks.py, scripts/install-hooks.sh and harness/claude/capabilities.md changed during GREEN; shared architecture delta is the explicit Python 3.11 minimum and existing installer phase/type refinement; no new component or dependency; plan completion delta returned to root, no plan/shared-file writes
         repair finalization: atomic execution complete and protected review evidence retained; atomic-validation deliberately remains failed until the independent reviewer rechecks the repaired implementation; no additional product changes or suite runs planned
         validation recheck: pav-check DONE — all four acceptance criteria met; previous important findings resolved by typed source/fixture signatures and coherent typed transaction objects with focused helpers; no remaining critical or important findings
         validation recheck: 37 installer functions have resolved annotations, at most 30 source lines and three non-self parameters; 55 fixture functions are annotated and at most 30 lines; class attributes annotated, no unexplained Any; named fixture forwarding/CLI parameter exceptions carry explicit narrow justification
         validation recheck: repair RED commit 3a3130c1413d0864b30d560e0366067f21f2404e matches the current fixture byte for byte; SHA256 8a1d2b65c2cd9cc83877eb9d2c2b29e2a79363ae1e6f4f74c3379e7d3eac58a0; all 50 previous executable fixture bodies, including three generated fault adapters, match after annotation metadata and generated typing-prelude normalization; original RED and amendment records retained
         validation recheck: independent focused lifecycle/runtime/standards 39 passed; canonical runtime contract pass; task gate 17 passed, 0 failed, 2 skips; all Bash syntax, in-memory compile/annotation resolution and whitespace pass; ShellCheck unavailable
         validation recheck: ONE stable isolated full gate completed with 588 passed, 0 failed and 2 optional hygiene skips; /tmp/hook-validator-recheck-full.txt; focused /tmp/hook-validator-recheck-focused.txt, runtime /tmp/hook-validator-recheck-runtime.txt, task /tmp/hook-validator-recheck-task.txt; reviewed product tip 2ec642806e1700eaa409af44704b291e6f629f53 unchanged throughout
         validation recheck: unsupported Python before engine startup and unusable interpreter preserve settings/ownership and report unsupported-python; missing Python retains missing-dependency; source-independent uninstall/recovery and all ownership/settings/registry/capability assertions pass; all executable fixtures use disposable HOME/XDG/log/project roots
         validation recheck: pav-propose --batch complete — no measurable improvement proposals found; no proposals section or product changes required
         validation recheck: pav-close complete in orchestrated mode; plan delta T-03 → reviewed returned to root; no composite trigger; protected original/repair TDD and git evidence retained; own block requires no compression, shared-state compression remains root-owned
  branch: feat/user-hook-installation
  base_branch: feat/hook-event-adapter
  base_commit: 30f0819e8800f222a59d44211ec01682fa2bfbda
  commits: 94843ed7e3fd5285639f6a0e6074a7af89ba0d4f test(hooks): define owned installation and recovery, f7c673efcb90803b4915cd37deede4ac18383819 feat(hooks): install and recover owned user hooks, 3a3130c1413d0864b30d560e0366067f21f2404e test(hooks): cover interpreter support and Python standards, 2ec642806e1700eaa409af44704b291e6f629f53 fix(hooks): guard Python support and type installer transactions
  pr: #25 draft

T-04 | Coverage-aware workflow logging | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close complete — DoD met; all three acceptance criteria independently verified with no critical or important findings
  target_files: tests/hook-workflow-contract.sh, scripts/validate-contracts.sh, rules/run-log.md, rules/orchestration.md, workflows/spec-run.md, workflows/phase-pipeline.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-validation.md
  blocker: none
  notes: tdd: integration + contract — three aggregate tests, AC coverage 3/3; documentation assertions supply RED; real public adapter/producer fixtures supply existing runtime regression evidence, not live model compliance
         tdd: red digest — AC-1 → test_unavailable_hooks_keep_every_prompt_step_approximate; AC-2 → test_batches_and_absent_red_do_not_claim_named_coverage; AC-3 → test_dispatch_report_status_preserve_one_delivery_route
         initial RED observation: bash scripts/validate-contracts.sh --hook-workflow-only; three tests failed only on missing workflow/rule integration before product edits; isolated native/session/config/state/project/log fixtures
         added paths: tests/hook-workflow-contract.sh; scripts/validate-contracts.sh refined as a test runner target; no product controller
         edge coverage: no envelope and unknown resume; accepted/pending/delivering lost receipt; fallback/fallback-attempted and failed ordinary persistence; wrong/missing status; missing private state; multiple/duplicate/wrapper Skills; none/no-RED; session unknown and missing native session
         tdd: test amended — test_dispatch_report_status_preserve_one_delivery_route — owner-approved additive malformed receipt sequence coverage exposes a test-only controller predicate defect: it matched kind and identity but omitted positive bounded integer seq validation; all original assertions retained
         tdd: receipt red digest — AC-3 → malformed_receipt_status: absent, zero, boolean, negative, fractional, string and over-runtime-maximum sequence on fresh real pending checkpoints; malformed observed zero sequence against accepted private state must not duplicate persistence; eight subcases fail before predicate correction
         tdd: fixture repair — valid_receipt requires kind/tuple and type(seq) is int with 0 < seq <= maximum from public runtime contract; new malformed cases run after the original accepted-route counter baseline; every existing assertion retained
         test fixture hashes: original cd4e34b60b7556dad1b1d08cf40ee0dfb85f64ef044924da632c53499c033945; receipt RED b34b7f7723143dc0ab724c6f8c98661ebc95cc45954e2e8b740b5d86e7517073; receipt GREEN ed29fc5f24fe6b057c5549d3a3d1d644ae9d1b209f736e3930dbc9a94c0eed6c; runner unchanged bd5f1f75765d72216c2316f61522c6ba40745f010c1f6feb2280480c87ef3ead

         verification: three acceptance aggregates green (7.292 s), canonical run-log contract pass, full stable gate 589 passed / 0 failed / 2 configured hygiene skips; Bash syntax and embedded Python compile/annotations/helper limits pass; ShellCheck unavailable; whitespace clean; no deployment or historical-store reads
         regression recovery: first full run canceled after the legacy writer-ownership phrase check failed; restored literal sub-agent never calls in product instructions, then one stable full run passed
         architecture delta returned to Orchestrator: document canonical workflow coverage/routing and isolated workflow acceptance; no new executable product module or schema
         finalization delta returned to Orchestrator: set this subtask plan status to done; validation remains not-started pending independent review; compressed only this leaf block and preserved every tdd digest/hash/git field
         independent validation: AC-1 met by ordinary approximate-note/run-boundary assertions and unavailable-session fixtures; AC-2 met by native batch/duplicate/wrapper/unknown/absent-RED fixtures and retained internal approximate instructions; AC-3 met by concrete native-user dispatch/final report wiring, exact tuple/receipt checks and serialized one-route fixtures
         independent TDD audit: immutable-base RED reproduced with all three aggregate tests failing on missing integration; original 45 assertions retained and seven added; all recorded fixture hashes match; receipt predicate amendment is documented and additive; no skipped, vacuous replacement or weakened frozen assertion found
         independent verification: focused workflow gate 3 passed (7.075 s); canonical run-log contract passed; task gate 17 passed / 0 failed / 2 skips; one stable isolated full gate 589 passed / 0 failed / 2 configured hygiene skips; Bash syntax, in-memory Python compilation, annotations and function limits passed; ShellCheck unavailable; reviewed product remained unchanged
         independent scope audit: explicit native evidence, canonical receipt sequence, missing/unknown resume and private-state handling conform; new heading targets resolve; no executable product controller, fabricated native retry or model timestamp introduced; synthetic composition and documentation assertions establish no live model compliance or live event-firing claim
         batch improvement review: no concrete Do Now, Do Later or Optional proposals found; nothing applied
         close delta returned to Orchestrator: set this subtask plan status to reviewed; compression audit kept the current leaf block and preserved all protected notes, test digests, target files and git fields; no composite trigger applies
  branch: feat/coverage-aware-workflow-logging
  base_branch: feat/user-hook-installation
  base_commit: 4cf5c515d11b5730090923647e1def2d52129095
  commits: 530b7b8a757d250ba42c640b1476fec830c56414 test(logging): define workflow checkpoint routing, 35ed85f53dbc8f9ea52642f8051346cb90c37f08 test(logging): reject malformed workflow acceptance receipts, c6c7f89dd9dbf61c74a6e900819389a8aa27744e feat(logging): route workflow checkpoints by accepted coverage
  pr: #26 draft

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

### Reviewed owned hook installation

branch: feat/user-hook-installation
expected_parent: 2ec642806e1700eaa409af44704b291e6f629f53
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/memory/architecture.md
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/todo/task-03-hook-based-logging/T-05-retrospective-timing/description.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
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

### Reviewed workflow coverage integration

branch: feat/coverage-aware-workflow-logging
expected_parent: c6c7f89dd9dbf61c74a6e900819389a8aa27744e
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/memory/architecture.md
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md
