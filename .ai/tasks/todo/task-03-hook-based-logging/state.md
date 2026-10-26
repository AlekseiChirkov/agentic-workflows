spec_path: .ai/specs/03-hook-based-logging.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: complete
- validation: complete

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
- The owner requests full autonomous specification and implementation, including routine defect repairs, with analysis delegated for decisions. Resolved interfaces and later implementation-driven clarifications are documented in the specification; the explicit amendment and TDD records preserve their chronology (source: user, 2026-10-26; Arbiter).
- Resume accepts the recorded implementation tip or verified knowledge-only snapshots above it; each snapshot records its exact parent and changed paths instead of its own hash (source: ADR-0010 Decision 2; completed task-02 Knowledge Snapshots; Arbiter).
- flow: full — gate: 1 fail (more than three files), 2 fail (correlation contract), 3 fail (shipped logging behavior), 4 pass (no database migration).

### Description Amendments
- 2026-10-26: The owner requested a full autonomous specification. Resolved marker/native schema, receipt/fallback ownership, project selection, installation recovery and exact timing contracts were documented in the specification. Parent/waiting semantics, fence and raw-number validation, and Python support/standards refinements also have explicit implementation-time or review-time records below. Sources: owner instruction, existing roadmap decisions, cited Arbiter analyses and native documentation. No acceptance criterion was weakened.
- 2026-10-26: Independent adapter review exposed Markdown fence eligibility errors; raw-number analysis exposed rounding at explicit receipt/private-state validation boundaries. CommonMark lexical rules and fresh canonical integer encodings clarify the existing invalid-input contract. Separate failing regression commits precede the repair; historical lint compatibility remains unchanged.
- 2026-10-26: Independent installer review found missing Python annotations and oversized product functions. Apply the repository default Python 3.11 minimum, typed stdlib sources and focused helpers; guard unsupported interpreters before engine startup. Add failing version-guard regressions before repair. Annotation-only fixture amendments preserve all executable assertions; any retained CLI-adapter signature exception is named and justified as code-quality permits. Sources: principles/python-standards.md, principles/code-quality.md and Arbiter; no functional acceptance criterion weakened.
- 2026-10-26: Read-only cross-leaf standards audit found 52 newly introduced adapter fixture functions and 9 correlated producer fixture helpers needing annotations. Include annotation-only harmonization and a scoped regression in T-05's complete acceptance harness before its RED freeze; keep original test bodies and generated producer bytes intact. Explicitly justify the single long adapter recovery scenario and necessary CLI helper parameter shapes under code-quality. Baseline Python snippets and setup registry introduce no affected functions and remain outside this repair. Sources: Arbiter main-to-tip AST audit, python-standards and complete-harness acceptance criterion.

- 2026-10-26: Independent timing review proposed two documentation precision corrections. Apply both under the owner's autonomous authorization: distinguish named Skill coverage from explicitly correlated session unknown, and document the native flock dependency. Expand T-05 to the capability declaration and additive workflow documentation tests. Existing runtime semantics and frozen assertions remain unchanged (sources: independent Validator and Arbiter).

## Open Questions (batch)
None.

## Authorized Prerequisite
- branch: fix/knowledge-base-tracking-policy
- base_branch: main
- base_commit: 7477bacce34b58d3c683a4329b82778b0d330a7e
- commits: be14570c80ad82db6ddd77b86e90e13f0e7aeb5d test(sync): preserve repository knowledge tracking policy, 9bb1358be2ee9d09f83520239ff30baa29c05906 fix: respect repository knowledge tracking policy
- status: reviewed
- tests: RED then GREEN for repository tracking policy; independent review PASS. Full validation: 575 pass, stale archived-spec ledger path corrected and focused recheck PASS, two optional hygiene skips.
- pr: #22 ready; origin verified and branch published after destination checks

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
  commits: be65b3dc956a3e156ad95d4b3535765ea41b6746 test(logging): cover correlated events and precise intervals, a10aeb3e42d2c74448e11939186b82cb8e205794 feat(logging): accept correlated checkpoint intervals, d804b01b2b1cd6e82f1890fee3128ebd0655fd5f chore(logging): Reconcile specification ancestry
  pr: #23 ready

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
  pr: #24 ready

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
  pr: #25 ready

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
  pr: #26 ready

T-05 | Honest timing and end-to-end evidence | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close complete — all five criteria independently verified; stable full gate 590/0/2 and final workflow 5/timing 51 pass; documentation proposals addressed; reviewed plan delta returned to root
  target_files: tests/hook-timing.sh, tests/log-step-hook.sh, scripts/validate-contracts.sh, scripts/run-log-timing.sh, scripts/run-log-timing.py, workflows/retro.md, docs/USAGE.md, scripts/README.md, docs/README.md, harness/claude/capabilities.md, tests/hook-workflow-contract.sh
  blocker: none
  notes: tdd: integration and contract fixtures required before implementation
         tdd: integration and contract — 51 groups, AC coverage 5/5; public explicit-file CLI, exact independent reference arithmetic, private lint snapshots, complete isolated two-run lifecycle
         tdd: red digest — AC-1 → test_timing_sequential_complete_uses_exact_wall_denominator, test_timing_successive_actor_spans_preserve_gaps_without_waiting; AC-2 → test_timing_nested_reference_subtracts_waiting_from_direct_parent, test_timing_same_actor_overlap_retains_union_and_distinct_actor_parallelism, test_timing_invalid_component_reference_preserves_disconnected_root, test_timing_parallel_roots_allow_worker_sum_above_wall, test_timing_waiting_sum_and_union_are_independent_of_active_work, test_timing_unknown_session_span_contributes_only_observed_coverage, test_timing_large_integer_totals_and_ratios_are_lossless_strings, test_timing_historical_integral_lexemes_preserve_exact_endpoints, test_timing_zero_wall_and_endpoint_spans_have_unavailable_ratios, test_timing_zero_length_children_at_parent_end_remain_valid, test_timing_waiting_only_observations_establish_zero_active_work; AC-3 → test_timing_measured_span_approximation_markers_are_exact, test_timing_unmarked_legacy_and_missing_interval_remain_unmeasured, test_timing_invalid_producer_fields_exclude_entire_lines, test_timing_fractional_nonfinite_boolean_or_out_of_bounds_spans_are_excluded, test_timing_out_of_run_or_reversed_spans_do_not_create_groups, test_timing_duplicate_checkpoints_collapse_generated_variations, test_timing_conflicting_checkpoint_delivery_fields_exclude_entire_key, test_timing_duplicate_numeric_equality_uses_exact_mathematical_values, test_timing_boundaries_require_unique_substantive_equality, test_timing_identical_boundaries_collapse_only_generated_fields, test_timing_unusable_or_missing_boundaries_never_invent_denominators, test_timing_metadata_presence_and_exact_strings_control_attribution, test_timing_omitted_optional_metadata_and_start_only_labels_are_supported, test_timing_retro_docs_preserve_loader_and_describe_honest_measures; AC-4 → test_timing_python_and_introduced_fixtures_have_complete_annotations, test_timing_two_run_lifecycle_preserves_attribution_fallback_and_owned_settings; AC-5 → test_timing_zero_length_cycles_still_quarantine_exclusive_metrics, test_timing_parent_cycles_missing_or_cross_session_links_quarantine_components, test_timing_same_actor_and_step_partial_components_keep_totals_unavailable, test_timing_parent_containment_failure_keeps_raw_union_only, test_timing_rejected_child_tombstone_excludes_valid_parent_exclusive_time, test_timing_invalid_child_endpoint_quarantines_transitive_siblings, test_timing_conflicting_parent_declarations_quarantine_every_connected_component, test_timing_opaque_rejected_evidence_makes_exclusive_graph_unverified, test_timing_rejected_uncorrelated_legacy_rows_do_not_hide_graph_edges, test_timing_cross_file_and_intra_file_run_identity_conflicts_are_unavailable; edge → test_timing_explicit_files_deduplicate_paths_without_discovering_store, test_timing_same_basename_distinct_runs_remain_independent, test_timing_input_errors_never_look_like_clean_empty_corpus, test_timing_end_of_options_accepts_literal_dash_path, test_timing_missing_python_jq_and_unsupported_python_return_null, test_timing_incomplete_or_malformed_lint_never_authorizes_metrics, test_timing_invalid_lint_references_and_unique_counts_are_rejected, test_timing_known_lint_violations_remain_lower_bounds_when_summary_fails, test_timing_physical_lf_lines_and_unterminated_final_record_are_exact, test_timing_snapshot_mutation_or_inventory_change_invalidates_coverage, test_timing_snapshot_is_private_byte_exact_and_cleaned_after_lint, test_timing_contract_export_must_be_usable_and_fetched_once
         tdd: red evidence — bash scripts/validate-contracts.sh --hook-timing-only exits 1; all 51 named groups fail with 125 expected missing timing CLI/engine/documentation assertions, zero errors; no product or documentation edits before RED
         tdd: frozen test-name SHA256 — e7e45803e97eb102366912ea0317c65fccf95c1de483762b2794c902f798f4af
         tdd: frozen test files SHA256 — tests/hook-timing.sh 53a34dde3c4e15523d174519453d64ada59050df5fb1bf4f20cefbbb55472850; tests/log-step-hook.sh f20e7ee99077d5ec7b12f57e70104d8204d70919b8b7f48bb65f65a7f95b4bfc; scripts/validate-contracts.sh 5ace1c74a127af5686381d36d0c77cbaa26486f7e70a6d371f73992babbd8d01
         tdd: explicit annotation-only frozen-source amendment — adapter 52 functions and 11 class attributes plus correlated producer fixture 9 functions now have complete annotations; executable bodies, defaults, assertions and generated producer literal preserved; only future/type imports, type aliases, return/argument annotations and no-value class annotations added
         tdd: annotation preservation evidence — narrow normalized full AST comparisons before the separately authorized partial-append addition: adapter 8edeb87064e4f8bb00239efd614947c42ee3a1a937229d4c1804e8b8ee66543d; correlated fixture 4b6902e7fc7e2e4f0dd4acfe305590450a8f2ef04bea52e9b9569e514bcffd5c; generated producer literal unchanged SHA256 da199fd99b9aa012cee5ab7212fe1656ee45b21e2f915342ae22e83af2822e91
         code-quality exceptions — retained adapter call (4 parameters), dispatch (6), transcript (4) and payload (6) preserve frozen native fixture boundary shapes; correlated accepted (4) preserves exact receipt tuple and replay flag; contiguous corrupted-frozen-payload fixture (36 lines) retains the complete corruption matrix; no blanket waiver and every fresh timing function is at most 30 lines and 3 parameters including self
         verification: amended adapter 38 checks pass; authorized correlated append regression passes after actual partial JSON bytes reach the event inode, live size exceeds original, snapshot rollback restores exact bytes, then sequence 1 accepts once and replay is duplicate; original pre-append failure assertions retained
         verification: scripts/validate-contracts.sh, tests/log-step-hook.sh and tests/hook-timing.sh pass Bash syntax; Python fixture compilation stays in memory; no real HOME deployment, model invocation or historical-log reads; complete suite deferred until GREEN
         tdd: first full gate — 588 passed, 2 failed, 2 optional skips; outer timing 51 passed. Nested history copied validator erased producer source required by the scoped annotation audit (IndexError in python_block); inserted usage documentation shifted the unchanged permitted clone token from line 251 to 254. No engine timing defect found; root refreshed the exact identity ledger line only.
         tdd: test amended — test_contract_version_rule_history_warns_until_version_changes — root-approved fixture packaging correction preserves the copied producer definitions and PYCORRELATED heredoc byte-for-byte, suppressing only its 28 complete column-zero check/continuation invocation pairs with exact syntax/count/no-residual assertions; other five section removals and every original assertion remain unchanged
         tdd: approved amendment SHA256 — scripts/validate-contracts.sh ce5dc8ac9fa65b7bb2f165bb38e0cf8f40766e91ce638c56d308ab340acf3329; original timing and adapter file hashes, all 51 timing test bodies and generated producer literal remain byte-identical
         verification: copied-history packaging proof retains the exact producer source and excludes its nested execution; amended fixture compiles in memory, Bash syntax and whitespace pass; canonical contract and 17-check task validation pass; timing 51 and producer/lint/retro 35 pass; paused before the separate test-only commit and new stable full gate
         tdd: green — all 51 frozen timing groups pass with unchanged names, count, bodies and assertions; timing/adapter file hashes match the original RED checkpoint and validator differs only by the separately approved, committed history-copy packaging amendment
         verification: stable full validator after the fixture correction exits 0 — 590 passed, 0 failed, 2 configured hygiene skips; all three nested rule-history validators, public identity ledger and final hook aggregates pass; final evidence /tmp/timing-full-validation-final.txt
         verification: scoped timing 51, producer/lint/retro 35, adapter 38, installation 39 and workflow 3 pass; canonical runtime contract passes; task metadata 17 passed, 0 failed, 2 skips; all scripts/hooks/tests pass per-file Bash syntax and introduced Python compiles in memory with mandatory hints, no Any, functions at most 30 lines and 3 parameters except individually recorded prior fixture cases; ShellCheck unavailable
         verification: original retrospective corpus loader remains byte-identical SHA256 9d9153e6fa0ec1bcb775c52adde3a0df41aa9db3c8400fbe5dfc84954be326d4; snapshot privacy, LF counts, exact arithmetic, negative-only graph evidence and complete isolated registration/install/two-run/dedup/fallback/close/uninstall lifecycle pass without model invocation or real home/history access
         acceptance: all five criteria verified through the frozen mapping — exact sequential coverage/gaps, independent nested/parallel/waiting arithmetic, honest approximate/incomplete exclusions, complete two-run lifecycle and invalid interval/parent graph handling; elapsed spans are never CPU claims
         finalization: execution complete, validation not-started; root already updated architecture inventory/dataflow, provisional decision record and runbook dependencies/commands; plan remains in-progress until independent review as explicitly directed; no additional shared-file edits requested
         tdd: documentation repair contract — two additive typed checks cover named versus unknown-session evidence/suppression in the capability profile and bounded usage section, plus native Bash/jq/flock dependencies versus ordinary optional-jq logging; all runtime behavior and the original 51 timing criteria remain unchanged
         tdd: documentation repair red digest — AC-3/4 and approved documentation amendment → test_hook_documentation_distinguishes_named_and_unknown_session_coverage, test_hook_documentation_separates_native_and_legacy_dependencies
         tdd: documentation repair red evidence — bash scripts/validate-contracts.sh --hook-workflow-only runs 5 groups: all original 3 pass, new 2 fail with 3 substantive missing-doc assertions and zero errors; no documentation or implementation edits before RED; source /tmp/workflow-documentation-red.txt
         tdd: documentation repair freeze — tests/hook-workflow-contract.sh SHA256 952a5ab0204c6a11e0bee9b77f6f78cf2eecff6496c9377accf396d46b16f829; every preexisting workflow function and helper source is byte-identical to the previous 3-group harness; tests/hook-timing.sh remains SHA256 53a34dde3c4e15523d174519453d64ada59050df5fb1bf4f20cefbbb55472850
         verification: both additive documentation methods have return annotations, at most 30 lines and 3 parameters; workflow Bash syntax and in-memory Python compilation pass; source work paused for separate test-only commit
         tdd: documentation repair green — all 5 workflow groups pass (original 3 plus the 2 frozen additive checks); all 51 timing groups pass; canonical runtime contract passes. Supplemental test commit 30aa5fedc3fa53715a0709b2017f752e4b97202d is preserved; workflow test SHA256 remains 952a5ab0204c6a11e0bee9b77f6f78cf2eecff6496c9377accf396d46b16f829
         verification: documentation-only implementation changes harness/claude/capabilities.md and the bounded hook coverage section in docs/USAGE.md — named coverage and receipt suppression require the matching named observation; fully correlated no-invocation session unknown remains observed without named coverage/suppression; native Bash/jq/flock dependencies are separated from ordinary optional-jq logging
         verification: per-file Bash syntax, in-memory script and fixture Python compilation, documentation whitespace and frozen source hashes pass; timing engine, all original 51 timing tests, adapter source, approved validator and every workflow test remain unchanged. No second leaf full gate run, as directed; the final integrated task-wide gate and independent delta review follow the documentation commit
         finalization: documentation repair execution complete; original full 590/0/2 evidence remains recorded and the supplemental RED/commit/GREEN trail is intact; plan and shared decision records remain root-owned; no additional shared deltas
         validation: independent pav-check DONE — all five acceptance criteria met; no critical or important findings; exact boundary/metadata equality, integer interval arithmetic, negative-only graph evidence, partial actor/step null totals and private complete lint snapshots reviewed
         validation: independent stable full isolated gate exited 0 — 590 passed, 0 failed, 2 configured hygiene skips; evidence /tmp/timing-independent-validation.txt; focused timing 51, producer/lint/retro 35, adapter 38, installation 39, workflow 3, canonical contract and task metadata 17/0/2 passed
         validation: frozen timing/adapter hashes and approved validator amendment hash match; annotation-normalized executable AST digests independently reproduced, generated producer literals and original retrospective loader preserved; actual partial-append rollback plus one accepted retry and duplicate replay verified; Bash syntax and whitespace clean; ShellCheck unavailable
         validation: supplementary documentation regressions independently RED at their test-only commit (2 tests, 3 expected assertion failures, no errors); final documentation-only delta passes workflow 5 and timing 51 plus canonical gate; original workflow fixture AST and all frozen source hashes preserved; no model invocation, real-home deployment or historical-log reads
         validation proposals: both optional documentation precision proposals addressed by the separately reviewed documentation repair; no Do Now, Do Later or Optional proposals remain; the earlier actual-partial-append proposal is fulfilled by the preserved executable regression
  branch: feat/run-log-timing
  base_branch: feat/coverage-aware-workflow-logging
  base_commit: 2ad00eda9d4371673c719ea4d40b1c8fdf74f03c
  commits: 18513f7b1615c9d542653ad8c59bfde2e0a9ea28 test(timing): define exact interval and lifecycle analysis, fd81d62a5699315c13cfe3ba17bcf583f752a34f test(contracts): preserve audited sources in history fixtures, 571620dd5fe1ab50c3e775660b7fe9a9905611b0, 30aa5fedc3fa53715a0709b2017f752e4b97202d, 44d16576fe265755a21670fc57a6f348e16c8899 docs(hooks): clarify named coverage and native dependencies
  pr: #27 ready

T-06 | Focused shell delivery functions | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: reviewed — all four acceptance criteria met; independent quality 3 and runtime 168 pass; worker full gate 591/0/2 verified against exact committed blobs
  target_files: tests/hook-shell-quality.sh, scripts/validate-contracts.sh, hooks/log-step-hook.sh, scripts/log-step.sh
  blocker: none
  notes: tdd: contract and integration tests must precede behavior-preserving extraction; preserve every prior frozen assertion and output/effect ordering
         decision: split adapter dispatch, report scan/validation, transcript read/evidence and completion phases; split producer correlation validation, serializers, step context/replay/staging/emission/commit; replace six metadata arguments with a coherent context of at most three parameters (source: independent task review and Arbiter structural audit)
         code-quality exception: hooks/log-step-hook.sh record_valid is a 40-line single jq cross-field cached-record predicate; preserve tuple, frozen-payload and accepted-receipt consistency in one invocation rather than scatter the authoritative predicate or add deployed query dependencies
         code-quality exception: scripts/log-step.sh cmd_run_start is 92 lines (baseline 91) and cmd_run_end is 64 (baseline 62); preserve the established CLI persistence lifecycles and effect/output ordering, whose task additions are limited to executable clocks and serialization
         code-quality exception: scripts/log-step.sh cmd_lint is 186 lines (baseline 155); additions are correlated declarative predicates in the existing raw-number-aware jq filter, preserving one authoritative eligibility and line-diagnostic transaction
         code-quality exception: scripts/validate-contracts.sh validate_run_log_contract (79) and run_log_contract_smoke (96) preserve same-sized baseline single Python heredocs with contract-key additions; run_correlated_event_smoke (223) hosts separately typed audited scenario functions in one frozen Python program
         code-quality exception: scripts/validate-contracts.sh test_sync_preserves_repository_knowledge_policy (32) preserves one disposable tracked/untracked lifecycle, cleanup and idempotence assertions; test_contract_version_rule_history_warns_until_version_changes (66, baseline 59) preserves the three VERSION states, audited copied producer source and frozen assertions
         code-quality exception: adapter main/options and existing producer cmd_* accept the public CLI argv vector; retain that interface rather than reinterpret option tokens as domain parameters. No general shell, jq, test or parameter-limit waiver is granted
         tdd: contract + integration — three new aggregate tests failing as expected, AC coverage 4/4; test command bash scripts/validate-contracts.sh --hook-shell-quality-only; unchanged sources pinned with adapter 38, producer 35, installer 39, workflow 5 and timing 51 passing tests
         tdd: red digest — AC-1 → test_native_shell_functions_meet_focused_limits, test_correlated_shell_functions_meet_focused_limits; AC-2 → test_native_hook_adapter_acceptance (38 unchanged fixture tests); AC-3 → test_hook_metadata_api_uses_at_most_three_parameters, producer acceptance (35 unchanged fixture tests); AC-4 → test_user_hook_installation_acceptance (39), test_workflow_hook_coverage_acceptance (5), test_hook_timing_acceptance (51), canonical run-log contract and shell syntax checks
         tdd: observed RED — adapter dispatch 31, parse_report 47, transcript_skill 33 and completion 77 physical lines; producer validate_hook_args 38, emit_json 33 and cmd_step 143 physical lines; stage_hook_metadata has six positional parameters; all exceed the explicit 30-line/three-parameter limits
         tdd: source guard — standard-library lexical masking excludes comments, quoted strings and heredoc data; Bash syntax-only endpoint probes retain physical LOC and nested declarations; numeric expansions include braced/default forms; duplicates, missing declarations and unparseable syntax fail closed. Predicate/lifecycle ceilings remain exactly record_valid 40, cmd_run_start 92, cmd_run_end 64 and cmd_lint 186 with arity checks retained. Three independently verified unchanged baseline exclusions are function-fingerprinted.
         tdd: frozen test digest — tests/hook-shell-quality.sh SHA256 2f932dd99619b6ddfbc46bec67d006100a24c2885f89e4a909dbbc64fbeaf4ff; 3 test methods and 16 fully annotated Python functions, each at most 30 lines and three parameters including self; new validator acceptance wrapper is 7 lines with no positional parameters
         tdd: preserved fixture hashes — tests/log-step-hook.sh f20e7ee99077d5ec7b12f57e70104d8204d70919b8b7f48bb65f65a7f95b4bfc; tests/log-step.sh 0c0a2911a61c15e1cc734bc2abd220359dda62a3a81b4d68529823097ad2a40d; tests/hook-install.sh 8a1d2b65c2cd9cc83877eb9d2c2b29e2a79363ae1e6f4f74c3379e7d3eac58a0; tests/hook-workflow-contract.sh 952a5ab0204c6a11e0bee9b77f6f78cf2eecff6496c9377accf396d46b16f829; tests/hook-timing.sh 53a34dde3c4e15523d174519453d64ada59050df5fb1bf4f20cefbbb55472850
         tdd: product sources untouched at RED — hooks/log-step-hook.sh SHA256 7c1daa03d48f7d973ee5a6daa5ce722bc5d531b9f7a06ec52ca78be4eeb840e1; scripts/log-step.sh eb8fe3d58840c632ca4f49e8b508e3ad757e0f9941d824ab0db72171763cf0a6; validator changes add only the focused test route and default acceptance wrapper, preserving every existing fixture body
         arbiter: coherent private step state without a newer Bash requirement → cmd_step owns one invocation-local associative step_context with fixed descriptive keys; extracted helpers mutate it only by direct current-shell calls, never subshells. No global context, nameref or eval (source: scripts/log-step.sh baseline associative arrays and meta_read printf-v output-variable contract; principles/code-quality.md; full specification Shell implementation constraints).
         arbiter: correlated metadata transport → stage_hook_metadata(run,path,context_json) carries STRING fields last_epoch,seq,delivery_key,delivery; delivery retains its exact existing compact JSON bytes as a string. Build only after existing correlated jq validation and never persist the internal transport object (source: scripts/log-step.sh stage_hook_metadata and meta_encode; resolved specification Shell implementation constraints).
         tdd: verification boundary — focused RED, all five unchanged runtime suites and Bash syntax observed; a redundant full validator begun before extraction was stopped at the orchestrator's request, with the complete integrated gate reserved for stable GREEN. No model calls, real-home deployment or historical telemetry reads.
         arbiter: adapter phase state → scan_report owns local fence/fence_length updated directly by update_report_fence(run,suffix); completion owns its existing local native scalars, mutated by documented direct helpers. No new adapter globals or context framework; fallback/accepted terminate and delivering checks frozen evidence without transcript scans (source: hooks/log-step-hook.sh existing parse_report/completion local ownership; principles/code-quality.md; Arbiter review).
         implementation: cohesive adapter dispatch/report/fence/transcript/native binding/frozen retry phases and producer validation/serialization/replay/clock/labels/staging/append/commit phases complete. All source checks and unchanged 38/35/39/5/51 runtime suites pass; the diagnostic fixture caught a private commit failure escaping the public exit-zero boundary, corrected without changing any fixture. Midpoint tripwire passed: one existing delivery component and unchanged acceptance scope.
         tdd: green digest — same three RED test names pass, without amendment, deletion, renaming or weakened assertions: test_native_shell_functions_meet_focused_limits; test_correlated_shell_functions_meet_focused_limits; test_hook_metadata_api_uses_at_most_three_parameters. All original fixture files and validator wiring remain byte-identical to their RED hashes.
         acceptance: AC-1 source checks pass, independently audited with AST-Grep across 91 product function definitions; repaired adapter dispatch/parse_report/transcript_skill/completion measure 23/18/9/18 physical lines and producer validate_hook_args/emit_json/cmd_step measure 9/8/17. Metadata staging uses three parameters and 25 lines; fresh functions satisfy 30 lines and three parameters. Named exception ceilings remain 40/92/64/186 and all three fingerprinted baseline bodies remain unchanged; no line compression or blanket waiver.
         acceptance: AC-2 adapter 38/38 and AC-3 producer 35/35 frozen runtime tests pass after final extraction, including lexical/native attribution, cached raw numeric rejection, unknown-session rules, frozen retries, fallback ownership, optional-jq legacy output, exact clock formatting, replay serialization, actual partial append rollback and metadata replacement failure. The public producer continues to return zero on rejection and persistence errors.
         acceptance: AC-4 installer 39/39, workflow 5/5 and timing 51/51 pass; canonical run-log contract passes; Bash syntax passes for every scripts/hooks/tests shell file; all 32 embedded Python programs compile; all 16 focused guard functions are annotated and within 30 lines/three parameters. Shellcheck is unavailable on this host. Task artifacts pass 20 checks with no failures and one expected incomplete-spec-reconciliation skip.
         verification: one stable complete bash scripts/validate-contracts.sh invocation passed 591 checks, failed 0 and skipped 2 unavailable local private-pattern scans. Output /tmp/hooks-shell-final-validation.txt SHA256 3d57a61e8eb3d5f99f2958fba0b09f53f7e0807dd5c91f88ec4c36b16588fc16; exit status 0 in /tmp/hooks-shell-final-validation.status. Its existing copied-history fixture passed all three VERSION states without Git or AST-Grep dependencies in the source guard.
         verification: exact nine-blob product/test manifest /tmp/hooks-shell-final-source-manifest.sha256 SHA256 bdcb046aba36c71f01e77aba7d040b02b87e920952d70118617db2910074e5a7; every entry verified before/after the complete gate. Adapter final SHA256 82d62af33ffef9b11f4c55244d77e1ea5bf800988754f4d37e9baaf003fd6586; producer final SHA256 92c28d4bd2b5094a67e7477de310322a479162795fb36f7f199c44041568f684; validator remains 990ee27a47a9bca852fa857c42501cf2b253c8fbe877b8aff7d552657d460060 and quality test remains 2f932dd99619b6ddfbc46bec67d006100a24c2885f89e4a909dbbc64fbeaf4ff. No product/test file changed during or after this gate.
         implementation contract: direct completion phases read/gate stdin into owner-local raw/path plus existing PROJECT; bind_native_fields reads raw and writes owner-local kind/session/path/message/native_agent; bind_completion_record reads message/session/kind and writes owner-local state plus existing REPORT/RECORD. Frozen validation reads existing records/report/native actor; skill resolution reads native path/boundary/session and updates existing SKILL; freeze updates only existing RECORD and its private persisted record. Producer phases use only cmd_step-owned step_context and existing validated PARSED_ARGS; mutating phases remain direct current-shell calls.
         finalize: implementation and tests are complete; atomic validation remains not-started for independent review. Orchestrated mode applies: plan status remains in-progress as directed, and shared memory/progress files are returned as proposed deltas rather than modified. No model invocation, real-home deployment, historical telemetry access, new runtime dependency, newer Bash minimum, changed schema or changed persistence claim.
         architecture.md: proposed orchestrator delta — document tests/hook-shell-quality.sh under executable acceptance checks: syntax-only Bash/standard-library inspection enforces focused function size and argument limits, bounded named exceptions and fingerprinted unchanged baseline exclusions; focused --hook-shell-quality-only and default validator run the same contract. Existing adapter/producer public interfaces and deployment descriptions require no change.
         implementation paths: GREEN product edits are limited to hooks/log-step-hook.sh and scripts/log-step.sh; tests/hook-shell-quality.sh and scripts/validate-contracts.sh were committed at RED and remain frozen. The two product blobs remain unchanged after the passing integrated gate.
         independent validation: pav-check DONE; all four acceptance criteria met with no critical or important findings. Source review confirms cohesive phase extraction without line compression, invocation-local associative producer state and direct caller-owned adapter state, no shadowing of output variables, unchanged Bash minimum and ordinary optional-jq serialization, exact four-string metadata transport, native project gating before private/transcript access, terminal-state and frozen-retry ordering, append rollback and receipt-after-commit semantics.
         independent validation: real Bash AST audit covers 91 product function definitions; all selected functions satisfy 30 physical lines and three domain parameters, with only the recorded 40/92/64/186 ceilings and unchanged fingerprinted baseline bodies excluded. The new seven-line validator wrapper has no positional parameters; the source inspector executes only Bash syntax probes and standard-library Python, without sourcing product code or requiring Git/AST-Grep at runtime.
         independent validation: frozen source contract independently reproduces all three expected RED failures against the exact base sources, and passes all three methods against the committed product. Test-only commit precedes product commit; the new guard and validator wiring are byte-identical to RED, all five original runtime fixture files are byte-identical to the base, and no amendment, skip, weakened assertion or frozen digest mismatch exists.
         independent validation: reviewer independently ran quality 3/3, adapter 38/38, producer 35/35, installer 39/39, workflow 5/5 and timing 51/51; canonical contract, all scripts/hooks/tests Bash syntax, changed-source whitespace and task metadata 20/0/1 pass. All 32 embedded programs in the validator and fixtures compile in memory; the additional setup program also compiles. All 16 quality-inspector Python functions are annotated and within 30 lines/three parameters. Shellcheck is unavailable.
         independent validation: reviewer verified the worker's complete gate artifact, rather than executing a duplicate full gate: exact recorded output/status/manifest hashes match, all nine manifest entries match committed tip a1774f5dc9d5f5b3fd0a1ac67159523289a78453 and current files, and output contains 591 unique passes, zero failures, two configured hygiene skips and terminal success with exit status zero. No source/evidence mismatch, incomplete coverage or runtime finding requires another full run.
         independent validation: initial redirected invocations failed before assertions with transient host quota errors; plain reruns of every scoped suite completed successfully. No unrelated temporary files were deleted. Verification used disposable fixture roots, with no model calls, live deployment, user settings access or historical telemetry reads.
         independent improvements: pav-propose --batch complete; no concrete Do Now, Do Later or Optional proposals identified.
         independent close: pav-close complete in orchestrated mode; return plan transition T-06 to reviewed for the orchestrator. No composite trigger applies. Own-block compression audit retained all existing protected notes, digests and git fields; shared-file compression and task-level status updates belong to the orchestrator.
  branch: fix/hook-function-boundaries
  base_branch: feat/run-log-timing
  base_commit: a9936d21f42aaf555dbcd67d70f334a1df38cb51
  commits: 4bc1d000d6d3767353e8ea6af833fd6b81f5da06, a1774f5dc9d5f5b3fd0a1ac67159523289a78453
  pr: #28 ready

adr: .ai/adr/0013-task-03-correlated-hook-logging.md (Accepted)

T-07 | Private producer replay and metadata | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: DoD met — four acceptance criteria verified; independent repair PASS and fresh complete gate 594/0/2; metadata review and integration follow.
  target_files: scripts/validate-contracts.sh, scripts/log-step.sh
  blocker: none
  notes: Arbiter selected raw canonical positive cached sequences, private creation before redirection, and advisories only for newly accepted arbitrary unknown names; preserve intentional session unknown and optional-jq ordinary logging.
         tdd: red — cache accepts zero, exponent and string sequences; mixed ordinary writes widen metadata and temporary replacements under umasks 002/000; correlated arbitrary names and unavailable definitions lack advisory. All three new checks exit one for these assertions; original focused 35 checks pass and product source is unchanged.
         fixture exception: run_private_producer_smoke has an exact 187-line ceiling and arity one. It hosts one frozen typed Python heredoc corpus with shared disposable public-command, receipt and byte/mode snapshot support. Each Python helper meets 30 lines and three parameters. Retaining complete cache/privacy/advisory lifecycles avoids arbitrary heredoc splitting; no fixture-wide exception is granted. Arbiter approved under code-quality's individually justified exception rule.
         fixture amendment: the history-copy extraction count changes 28 to 31 solely because three check pairs were added. Exact pair shape and no-residual-check assertions remain intact; no original assertion changed.
         tdd: green — producer 38/38, adapter 38/38, source quality 3/3, canonical, Bash syntax and whitespace checks pass. Raw cache validation includes a single fixed-schema object, duplicate/escaped duplicate-key rejection and unchanged conflicting-payload behavior. Historical exponent-form sequence lint remains compatible. Permission probes cover initial/ordinary/correlated metadata and temporary replacements under 002/000 with jq and no-jq, without event-mode changes. The frozen test commit remains unchanged.
         validation: NEEDS_WORK at c42a663 — the three original repairs pass independent producer 38, adapter 38, quality 3, canonical, 37 malformed-cache probes, 24 private temporary replacements and rollback/concurrency/history probes. Literal NUL inside a raw sequence or after the JSON object is discarded by Bash before validation and still yields acceptance. All file bytes and modes remain unchanged, but malformed raw state must not establish acceptance.
         decision: Arbiter confirms the fresh-cache invariant applies before line decoding. Reject the entire NUL-bearing active file before header/key parsing, so initial explicit file lookup stops safely rather than treating a corrupt cache entry as absent. Preserve literal percent text and legacy decoding; distinguish failed opening from normal EOF, and do not claim Bash EOF status proves error-free I/O. Extend this unpublished leaf with another separate regression commit then implementation commit.
         tdd: added/red — four literal-NUL positions (after object, inside sequence, key and string value) independently yield duplicate acceptance on c42a663 with unchanged bytes/modes. Additive positive escaped-key, percent text, quote/backslash and newline replay controls pass. Commit cfa4f6f contains only these 17 test lines, before product repair; no existing assertion changes. The specifically named heredoc fixture ceiling is now 204 lines (187 plus 17), arity one, retaining the same single-corpus rationale and typed 30-line/three-parameter Python helpers.
         tdd: NUL green — metadata_has_no_nul is eight lines/one parameter; meta_read is 24 lines/three parameters. Guard raw bytes before line parsing and reject a failed descriptor open; preserve existing percent decoding and avoid stronger OS read-error guarantees. Producer 38, adapter 38, quality 3, canonical, syntax, whitespace and 15 independent NUL/legacy probes pass. One existing adapter timeout under CPU contention passed unchanged both alone and on the full adapter rerun; no timeout or assertion was changed.
         validation: PASS at da4e027 — independent producer 38, adapter 38, source quality 3 and canonical checks; 37 malformed-cache cases, 40 NUL-route checks, failed descriptor opening/exhaustion, 24 private replacements, mixed concurrency, historical lint and actual append/metadata rollback all pass. Exact original three RED cases and four NUL RED positions independently reproduced; all original assertions and 17 additive follow-up lines audited. The unchanged bounded-transcript timeout case and full adapter rerun pass; source remains immutable.
         final validation: fresh complete isolated validator at da4e027 exits zero: 594 passed, 0 failed, 2 optional private-pattern skips. All original source/behavior assertions remain intact. This completes the cumulative criterion; no product issue remains. The clean detached checkout and 125-file non-knowledge manifest pin the validated source.
  branch: fix/private-event-replay
  base_branch: fix/hook-function-boundaries
  base_commit: fa865f4363a9f2420984ee3b1249deed2f1fc4ec
  commits: f8c85c478bfc84f6821d170bc1a3574212b690c5 test(logging): cover private replay and metadata permissions, c42a6632e680fddcef6810ff0be95aa857206814 fix(logging): validate private replay and preserve metadata modes, cfa4f6f45c492f1c746559f09b0b0515b4f7bc51 test(logging): reject NUL bytes before metadata decoding, da4e027b708d42cb6ae858d032c84ceb71b8fd5f fix(logging): reject NUL bytes before reading active metadata
  pr: #29; branch published, promotion after the final knowledge delta review


## Improvement Proposals (T-01)

### Do Now
None.

### Do Later
None.

### Optional
- Addressed during the complete acceptance harness: retained the original early-failure scenario and added actual partial-output injection, proving event inode growth, byte-exact rollback, one accepted retry and duplicate replay. Independently verified during timing validation; no outstanding proposal remains.

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

### Reviewed exact timing and completed execution

branch: feat/run-log-timing
expected_parent: 44d16576fe265755a21670fc57a6f348e16c8899
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/adr/0013-task-03-correlated-hook-logging.md
- .ai/adr/index.md
- .ai/context/runbook.md
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/completed/task-01-git-source-of-truth/state.md
- .ai/tasks/todo/task-03-hook-based-logging/T-05-retrospective-timing/description.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md

### Validated correlated hooks and exact timing

branch: fix/hook-function-boundaries
expected_parent: a1774f5dc9d5f5b3fd0a1ac67159523289a78453
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/adr/0013-task-03-correlated-hook-logging.md
- .ai/adr/index.md
- .ai/context/runbook.md
- .ai/memory/architecture.md
- .ai/memory/progress.md
- .ai/memory/state.md
- .ai/specs/03-hook-based-logging.md
- .ai/specs/README.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md
- .ai/tasks/todo/task-03-hook-based-logging/T-06-fix-hook-function-boundaries/description.md

### Published review-ready hook logging stack

branch: fix/hook-function-boundaries
expected_parent: 04e97a015ec2517ca84766bc900da397bf80ea5b
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/memory/progress.md
- .ai/memory/state.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md

### Independently verified private producer acceptance

branch: fix/private-event-replay
expected_parent: da4e027b708d42cb6ae858d032c84ceb71b8fd5f
allowed_scope: exactly the listed knowledge-base paths
recorded_paths:
- .ai/specs/03-hook-based-logging.md
- .ai/tasks/todo/task-03-hook-based-logging/plan.md
- .ai/tasks/todo/task-03-hook-based-logging/state.md
- .ai/tasks/todo/task-03-hook-based-logging/T-07-fix-private-event-replay/description.md

## Execution Report

| Subtask | Outcome | Evidence |
|---|---|---|
| T-01 | reviewed | Explicit producer identity, serialized receipts, rollback/retry and historical compatibility; independent review passed. |
| T-02 | reviewed | Native dispatch/evidence, bounded diagnostics, frozen delivery, fallback and exact protocol validation; independent review passed. |
| T-03 | reviewed | Lossless owned settings, prepared recovery, registration, capability/sync and Python guards; independent review passed. |
| T-04 | reviewed | Coverage-aware routing at existing returns, approximate uncovered boundaries and receipt suppression; independent review passed. |
| T-05 | reviewed | Exact snapshot-gated interval analysis, full isolated lifecycle, standards harmonization and documentation precision; independent review passed. |
| T-06 | reviewed | Approved validation repair: focused shell phases, coherent metadata context and bounded source contract; independent review passed. |

Skipped, blocked, deferred and not-reached subtasks: none. No composite rows exist.
All recorded improvement proposals have been addressed; no Do Now work remains.

Root file decisions: update architecture inventory/dataflow and runbook runtime/check commands; retain existing architectural principles because the implementation follows their additive-contract, explicit-state and honest-measurement decisions. Project inventory is absent, so skip it. Preserve the provisional decision record until task-level validation accepts it.

Compression audit: corrected the blanket pre-implementation chronology and completed optional proposal status; preserved all protected sections, archive pointers, branch points, commits, frozen digests and amendment records. Remaining chronological verification lines are audit evidence, not active blockers.

## Contract Check

### Invariants

| Invariant | Status |
|---|---|
| Invalid input is rejected before sequence, timestamps, accepted identity or metadata change; diagnostics remain safe and exit zero. | PASS: complete producer validation and native/raw-marker checks precede mutation; rejection fixtures preserve accepted state. |
| Runtime vocabulary and canonical rule remain synchronized; legacy events and prompt calls remain valid. | PASS: additive exported hook fields match canonical tables; bidirectional gate, historical lint and optional-jq compatibility pass. |
| Accepted hooks have explicit unique correlation and executable intervals; unknown is restricted to unambiguous sessions. | PASS: exact tuples, executable clocks, serialized ownership and matching receipts govern delivery; unknown requires a session boundary and session actor. |
| Structured markers provide canonical outcome, never narrative inference or model duration. | PASS: canonical unfenced report parsing supplies outcome/optional tests/gate; native Skill evidence supplies the step and executable clocks supply times. |
| Only manifest-owned settings entries may be merged or removed. | PASS: exact occurrence and created-group quotas preserve unowned copies and changed handlers; numeric tokens and unmatched recovery images survive. |
| Hook availability never substitutes for demonstrated boundary coverage. | PASS: mechanism, installation and accepted coverage remain distinct; named suppression requires matching native evidence and receipt. |

### Acceptance Criteria

| Criterion | Status |
|---|---|
| Stop/SubagentStop manifest, invoked skills, exact reports, explicit dispatch and registered projects. | PASS: both handlers call the adapter; the most-specific registered root gates access; native user dispatch and unique Skill evidence establish attribution. |
| Interleaved runs, duplicate/out-of-order delivery and malformed/ambiguous inputs preserve attribution and uniqueness. | PASS: fixtures cover explicit two-run identities, concurrent replay, out-of-order parents, rejection, frozen retry and one-route fallback. |
| User installation/removal is idempotent, preserves unrelated settings and supports spaced paths. | PASS: sync invokes the user installer; ownership, argument vectors, concurrent lifecycle and interrupted recovery fixtures cover these cases. |
| Uncovered/unavailable steps retain approximate prompts and retrospective labels. | PASS: all five orchestrators use canonical approximate routing; internal batches remain approximate; timing and retrospective label eligible approximate sources. |
| Sequential coverage meets five percent tolerance; nested/parallel timing separates spans, wall coverage, gaps, overlap and waiting. | PASS: exact 10000/10000 sequential reference and independent integer half-open formulas distinguish sums, unions, exclusive work and waiting; invalid graph totals are disclosed. |
| Existing producer/lint, complete contract and isolated hook fixtures pass without real-log changes. | PASS: final stable complete gate reports 591 passed, 0 failed and 2 optional hygiene skips. A fresh reviewer verified its exact committed source manifest/artifact and independently ran quality 3 plus all runtime 168 checks; disposable roots preserve real settings/history. |

### Off-limits

| Constraint | Status |
|---|---|
| No historical-log attribution or telemetry rewriting. | PASS: adapter uses explicit native/private evidence and producer active metadata; offline consumers and fixtures remain read-only/disposable. |
| No guessed or newest active run. | PASS: no newest-run selection exists; explicit dispatch identity survives receipt/fallback selection. |
| No unowned settings overwrite. | PASS: exact owned occurrence quotas preserve user entries, changed handlers and unmatched prepared images. |
| No default-branch push, merge, force-push or branch deletion. | PASS: only additive feature-branch pushes and draft creation were performed; independent validation made no git mutations. |
| No cost/token schema or git-rail implementation. | PASS: additions concern correlation/timing only; the separately authorized tracking prerequisite preserves existing staging and git prohibitions. |

### Specification coverage

| Source requirement | Status / evidence |
|---|---|
| Original AC: native manifest, invoked skill, canonical outcome and explicit attribution | PASS: native transcript/report parser, dispatch and receipt tuple validation. |
| Original AC: idempotent user sync installation and registered activation | PASS: installer/registry/lifecycle fixtures preserve user settings. |
| Original AC: best-effort session skill and explicitly correlated unknown | PASS: unique invocation evidence, session-only unknown and bounded diagnostics. |
| Original AC: prompt run boundaries and evidence-based suppression | PASS: all five orchestrators preserve internal prompts; only a matching named receipt suppresses its row. |
| Original AC: hooks-no approximate path and retrospective labels | PASS: Codex hooks:no and exact approximation marker/prefix routing are explicit. |
| Original AC: sequential/nested/parallel denominators | PASS: exact independent reference fixtures separate inclusive/exclusive/worker and wall measures. |
| Original AC: both canonical paths and capability selection | PASS: canonical workflow routing, native adapter and correlated interval sections define the selection. |
| Added AC-01 | PASS: interleaved/concurrent identity, replay, ambiguity and no-mutation assertions. |
| Added AC-02 | PASS: owned installation/recovery and unavailable/missing evidence routing. |
| Added AC-03 | PASS: wall denominators, exclusive graph eligibility, worker totals and overlap fixtures. |
| REQ-01 | PASS: explicit identity, bounded serialization, accepted receipts and additive validation/lint. |
| REQ-02 | PASS: no prose outcome or guessed attribution; missing evidence warns/omits; uncertainty never proves acceptance. |
| REQ-03 | PASS: private active correlation is separate from history; lint/timing remain read-only consumers. |
| REQ-04 | PASS: manifest ownership, canonical registry and capability/installation/coverage distinctions. |
| REQ-05 | PASS: deterministic no-model concurrency, duplicate/out-of-order, missing/unknown/unavailable and exact interval fixtures. |

Independent contract validation: 32 mapped checks PASS, 0 FAIL, no pending execution evidence and no critical failures. The 17 parent-contract checks and 15 source-specification checks are all verified. Current native profile fields were additionally checked against official command-hook, SubagentStop and environment documentation. Evidence remains documentation plus synthetic fixtures, not live firing or model compliance.

## Code Review

### Findings

1. Important — shell function standards. Adapter dispatch (31 lines), parse_report (47), transcript_skill (33), completion (77), and producer validate_hook_args (38), emit_json (33), cmd_step (143) require real decomposition. stage_hook_metadata takes six positional arguments and needs a coherent context. Named cohesive predicate, minimally extended baseline lifecycle and frozen-fixture exceptions require explicit notes.

### Summary

Independent whole-stack review: 0 critical, 1 important, 0 optional findings. No functional, architectural, security, edge-case, interface or test-integrity finding. Initial integrated full gate: 590 passed, 0 failed, 2 optional hygiene skips. The sole important finding is resolved by reviewed T-06; final full gate: 591 passed, 0 failed, 2 optional hygiene skips. A fresh reviewer independently ran quality 3 and all runtime 168 checks, inspected the actual Bash AST and frozen sources, and verified the worker full-gate artifact against identical committed blobs. No unresolved findings remain.

## Issue List

### Approved

1. Decompose native and correlated shell delivery into focused functions and replace the six-parameter metadata API with a coherent context; record only individually justified existing predicate/lifecycle/fixture exceptions. Priority: important. Automatically approved under spec-run and the owner's autonomous implementation instruction. Resolved by independently reviewed T-06; both repair commits and the unchanged behavior evidence are recorded above.
2. Reject nonpositive or noncanonical cached acceptance sequences before JSON normalization. Priority: important. Approved by the owner's additional final-review/repair instruction; T-07.
3. Preserve private active metadata and temporary replacement permissions across ordinary writes. Priority: important. Approved by the owner's additional final-review/repair instruction; T-07.
4. Restore the canonical advisory for newly accepted arbitrary unrecognized correlated step names. Priority: optional. Included under the owner's autonomous repair authorization; T-07.
5. Reject literal NUL before Bash metadata reads can normalize malformed cache. Priority: important. Found by independent repair validation and approved under the same repair instruction; T-07.

### Deferred

(none)

## Fix-Tasks
fixes-created: complete
fixes-count: 2
Created: T-06-fix-hook-function-boundaries, T-07-fix-private-event-replay

### Fix Classification

| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|---|---|---|---|---|---|---|---|
| #1 Focused shell delivery functions | important | fail: four product/test files | pass: no new invariant | pass: behavior preserved | pass: no schema/migration | dedicated | T-06-fix-hook-function-boundaries |
| #2–#5 Private producer replay and metadata | important and optional | pass: two product/test files | pass: enforce existing invariants | fail: correct shipped behavior | pass: no schema/migration | dedicated | T-07-fix-private-event-replay |

## Deferred

(none)

## Spec Sync
sync: complete
synced_at: 2026-10-26
deltas: 0 (implemented-differently: 0, not-implemented: 0, implemented-beyond: 0)
spec: .ai/specs/03-hook-based-logging.md

All five source requirements and ten original/additional acceptance criteria retain their intent. The resolved interfaces and explicitly recorded implementation/review refinements are already in the specification. The standards repair changes private structure only; no failed criterion was weakened or reclassified as a delta. Sources: Task Analysis assumptions/amendments, T-06 decision and TDD notes, approved issue #1, Contract Check, final Code Review and reviewed plan.

## Finalization

All six leaves are reviewed; the separately authorized prerequisite is reviewed. One important task-review finding was fixed and independently verified; no critical, optional, deferred or open question remains. Parent contract verification is 17/17 and original specification mapping is 15/15. Final cumulative behavior is supported by quality 3, runtime 168, canonical/syntax/annotation/whitespace checks and the verified 591/0/2 complete gate. The fresh repair reviewer ran scoped suites and verified the worker full artifact; it did not repeat the default full invocation.

Root-file decisions: architecture and runbook updated for delivered modules, runtime requirements, coverage routing, exact timing and source acceptance. Existing architectural principles remain valid and are retained; this implementation enforces their explicit-state, additive-contract and honest-measurement rules. Project inventory is absent and skipped. Existing provisional decision record accepted in place, with its index updated; no new ADR was allocated.

Compression audit: all protected sections, archive pointers, assumption/amendment chronology, branch points, commit records, named exceptions and TDD digests are retained. Intermediate verification notes identify their original checkpoints. No required audit evidence was removed; minimal compression was appropriate.

Final artifact checks: task validator 21 passed, 0 failed, 0 skipped; the existing exact public identity ledger passed after final knowledge edits. The nine product/test blobs remain identical to the verified full gate.

## Delivery Report

status: ready-for-review
repository: Orchestrail
base: main at immutable branch point 7477bacce34b58d3c683a4329b82778b0d330a7e

| Order | PR | Branch | Base | Status |
|---|---|---|---|---|
| 1 | #22 | fix/knowledge-base-tracking-policy | main | ready |
| 2 | #23 | feat/correlated-event-writes | fix/knowledge-base-tracking-policy | ready |
| 3 | #24 | feat/hook-event-adapter | feat/correlated-event-writes | ready |
| 4 | #25 | feat/user-hook-installation | feat/hook-event-adapter | ready |
| 5 | #26 | feat/coverage-aware-workflow-logging | feat/user-hook-installation | ready |
| 6 | #27 | feat/run-log-timing | feat/coverage-aware-workflow-logging | ready |
| 7 | #28 | fix/hook-function-boundaries | feat/run-log-timing | ready |

Merge order is the table order. No merge, default-branch push, force push or branch deletion was performed. After a squash or rebase merge, use restack before integrating remaining branches. Recorded hashes are pre-merge. Remote main advanced independently to 6fbaf42cca979f132280b1b04698d41306331626 by adding the original specification; feature branch points remain unchanged.

Verification limits: ShellCheck unavailable; two private-pattern scans explicitly skip because maintainer-local configuration is absent. Synthetic fixtures and official native documentation establish the supported profile; no live model invocation, event firing, real user-settings deployment or historical-corpus access is claimed.

## Additional Final Review and Integration

status: validated-awaiting-integration
authorization: On 2026-10-26 the owner explicitly requested a fresh independent validator for every pull request, subagent repairs for findings, and merging all completed pull requests. This narrowly supersedes the earlier no-merge constraint for this delivery. Default-branch direct pushes, force pushes, branch deletion, deployment and historical attribution remain prohibited. The preceding completed validation remains an immutable checkpoint; this section records the additional review.

Review isolation: one fresh validator per PR, detached cumulative source at fa865f4363a9f2420984ee3b1249deed2f1fc4ec, synthetic home/settings/log roots and independent reports outside the repository. Root owns shared records and git. Implementation remains sequential; read-only reviews use separate worktrees.

| PR | New review status | Evidence |
|---|---|---|
| #22 | PASS | 69 focused assertions; two isolated sync runs; historical spaced-path behavior already fixed later. |
| #23 | NEEDS_WORK, resolved by #29 | Original 35 producer checks and canonical gate passed; independent cache/privacy/advisory findings repaired and independently rechecked at da4e027. |
| #24 | PASS | 38 adapter cases and 23 independent boundary probes; no remaining adapter finding. |
| #25 | PASS | 39 installer, two native registry and eight independent edge groups; syntax, compile and whitespace checks. |
| #26 | PASS | Five workflow acceptance groups and 15 independent CLI scenarios; all 45 original assertions retained. |
| #27 | PASS | 51 timing groups, canonical gate, two documentation checks and 14 independent probes; frozen fixture and actual partial-output assurance verified. |
| #28 | PASS | Source quality 3, producer 35 and adapter 38; actual 91-function Bash AST, exact RED, metadata bytes, frozen fixtures and task artifacts verified. |
| #29 | PASS on fixed source | Separate repair validator; producer 38, adapter 38, quality 3, canonical and adversarial raw cache/NUL/privacy/rollback checks. Final cumulative validation 594/0/2. |

Approved repair: T-07 addresses important malformed cached acceptance and private metadata mode regressions, plus the optional correlated step-name advisory. The owner's autonomous repair authorization includes all three. Source: independent PR23 report and Arbiter analysis citing specification fresh-number rules, canonical positive receipt contract and the universal step-name advisory. No acceptance criterion is weakened.

The independent repair validator additionally found literal-NUL normalization before raw JSON validation. A separate failing regression commit precedes that repair. Its final PASS report resolves the preserved NEEDS_WORK checkpoint without overwriting it. All four additional final-review findings are addressed; a suggestion to clarify aggregate/internal row counts is an optional test readability improvement, not an established product defect.

Final cumulative validation: completed with exit zero in a detached clean checkout at da4e027b708d42cb6ae858d032c84ceb71b8fd5f, after all scoped runtime suites finished: 594 passed, 0 failed, 2 optional private-pattern skips. The earlier in-progress c42a663 run was stopped and superseded after the NUL finding; it is not completion evidence. A 125-file non-knowledge source manifest pins the final gate input. Knowledge updates are reviewed and checked separately; no model, live hook firing, real settings or historical-corpus access is claimed.

Ancestry repair: remote main 6fbaf42cca979f132280b1b04698d41306331626 differs from the original branch point only by the initial specification. PR23 conflicted only on that specification. Append merge d804b01b2b1cd6e82f1890fee3128ebd0655fd5f, with parents original producer head 6695f37ac3c6c3fe979f47fcdf84eadf6c475962 and remote main, retains the producer head's complete tree 4f27c0e23ea26106ff1863b8f709d56d3034115a unchanged. Ordinary fast-forward branch push only; no published commit was replaced. Independent PR23 review verified both parents and tree equality. Historical base_commit records remain unchanged. Root simulated all seven sequential merges before any remote merge: every merge is clean, each post-producer tree equals its original reviewed head, final tree ebebe6ef7689712cbd367e97d0976c77960e92a2 equals the reviewed cumulative tip. Actual merge trees must be checked against these predictions.
