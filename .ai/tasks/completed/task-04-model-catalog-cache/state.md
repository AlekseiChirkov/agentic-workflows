spec_path: .ai/specs/completed/04-model-catalog-cache.md
flow: full
contract_version: 0.9.0
adr: .ai/adr/0015-task-04-cached-model-selection.md (Accepted)

## Phases
- discovery: complete
- execution: complete
- validation: complete

## Task Analysis

→ archived to state-archive.md

### Assumptions
- flow: full — gate: 1 fail (more than three files), 2 fail (new catalog schema), 3 fail (selector behavior changes), 4 pass (no database migration).
- Run the repository-owned child workflows rather than outdated deployed copies (source: .ai/principles/architecture.md P1).
- Deliver only minimal model-capability input for this selected spec, with unknown availability excluded; do not implement the broader harness migration (source: spec REQ-03/REQ-06; ADR-0013 Decision 2 precedent; user renewed authorization to run this spec).
- Use Python 3.11+ standard-library helpers with no provider client, automatic network access, model spawning, or mandatory runtime (source: architecture existing Python helpers; shared gates G4/G5/G6).
- Catalog Markdown contains one versioned structured payload and the required human-readable tier table; validate derived table drift rather than maintain competing definitions (source: REQ-02/REQ-08; principle P6).
- Refresh research belongs to the explicitly invoked workflow; a helper validates and atomically installs an explicitly supplied candidate. Failed validation or replacement preserves the prior catalog (source: REQ-01; Contracts & Interfaces).
- Cost bands never establish quality. Missing prices/evidence remain unknown, and uncalibrated estimates cannot displace a suitable stronger/session default (source: REQ-02/REQ-05; Risks; shared gate G8).
- No initial real model catalog, new default, paid comparison, or home-directory deployment is part of this run. Model selection for this run retains the session default because no usable catalog is available (source: REQ-01; Open Questions).
- Keep requested, resolved, and actual identities distinct; actual remains unknown without harness execution evidence (source: REQ-06; Data Model; shared gate G1).
- Logging is skipped because ORCHESTRAIL_HOME is unset; optional logging does not block work (source: rules/run-log.md).

## Open Questions (batch)
None.

## Decomposition
- decomposition: complete
- subtasks: T-01, T-05, T-02, T-03, T-04

## Solution Design

### Variants

→ archived to state-archive.md

### Decision
Choose optional local helpers with explicit evidence and conservative fallback. The catalog is user-owned configuration, not a bundled assertion about today's model market. Keep the workflow under 1,500 words and place rationale/schema/examples in on-demand documentation. Cache, selection, and plan resolution are independently testable components; integrate their caller contract last.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Instructions alone | 5 | 5 | 4 | 1 | 4 | 19 |
| Optional local helpers | 4 | 5 | 5 | 5 | 4 | 23 |
| Routing service/migration | 1 | 2 | 1 | 3 | 1 | 8 |

Winner: optional local helpers. Anti-overengineering check: passed; helpers address current deterministic validation/latency/atomicity requirements, not hypothetical routing. Evidence: principles P1/P3/P6/P10/P11, existing Python helper architecture, specification REQ-01 through REQ-08.

### Scope
#### In
Versioned local catalog, refresh validation/atomicity, dated freshness notices, total score mapping, independent quality/availability floors, trait migration, compatible plan columns, visible requested/resolved/default reporting, offline tests and operational documentation.
#### Out
Provider calls, paid comparisons, initial production model defaults, measured savings claims, telemetry price ledger, learned routing, effort/escalation policy, general harness migration, installed global files.

### Rejected

→ archived to state-archive.md

### Off-limits
Do not read historical run logs, change logging schemas or monetary definitions, deploy global configuration, call a provider, silently substitute models, promote a cheaper production default, migrate/rename harnesses, merge PRs, push main, or commit .ai/ files.

### Invariants
- Ordinary lookup and tests never access the network; refresh is explicit and transactional.
- Unknown evidence never becomes an invented model, price, measured capability, or actual execution identity.
- Availability/context/tools/owner limits and quality floors precede economic comparison; worsening task risk cannot reduce the floor.
- Legacy plans and missing optional columns retain explicit session-default behavior.
- Helpers never spawn a model or become a mandatory orchestration runtime.
- RED tests precede implementation and remain frozen; validation is independent; shared files and Git have one writer.

### Acceptance Criteria
- AC-01: Clock-controlled 13/14/30/31-day, missing/malformed/future-date and failed-refresh cases yield specified statuses/notices with no network and unchanged prior bytes on failure.
- AC-02: Unavailable/unsupported and below-floor cheap models are excluded; cost band and capability are independent; unknown economics cannot justify a cheaper default; stronger-first remains eligible.
- AC-03: All score intervals and monotonic risk/uncertainty/verifiability boundaries pass deterministic fixtures.
- AC-04: Legacy/dual/missing columns work; unsupported requests are visible; declared suitable fallback or stop is explicit; actual identity never copies an unavailable planned ID.
- AC-05: Selector is at most 1,500 words; warm isolated lookup is measured below one second; schema/drift/compatibility checks pass; documentation distinguishes targets from measurements and defines ownership/rollback.

## Subtask Progress

T-01 | Local catalog storage | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — all four criteria met; offline schema, freshness, atomic refresh and measured lookup verified
  target_files: tests/model-catalog.py, scripts/validate-contracts.sh, scripts/model-catalog.py
  blocker: none
  notes: tdd: unit primary; integration for real isolated filesystem/CLI, contract for versioned Markdown schema; 15 tests, AC coverage 4/4.
         tdd: red digest — tests/model-catalog.py SHA256 9782913acc8a0488401a55cdaadadb18397c77c97f3359a9efb3adb801fdacbe; 15 unchanged test identities.
         AC-1 → test_catalog_age_boundaries_report_exact_usable_statuses; test_missing_malformed_future_dates_report_selection_unavailable; test_missing_catalog_default_path_preserves_absent_configuration.
         AC-2 → test_strict_schema_identity_and_vocabulary_reject_invalid_payloads; test_markdown_payload_and_derived_tier_table_drift_are_rejected; test_capability_and_price_evidence_validate_dates_types_and_references; test_unknown_price_availability_and_capability_remain_unknown; test_equal_relative_cost_preserves_independently_evidenced_quality.
         AC-3 → test_inspection_is_offline_readonly_and_repeatable; test_valid_refresh_installs_validated_candidate_with_same_directory_replacement; test_invalid_or_missing_refresh_candidate_preserves_previous_bytes; test_failed_replacement_preserves_catalog_and_cleans_temporary_file; test_refresh_creates_missing_directory_only_after_candidate_validation; test_cli_inspection_and_explicit_refresh_report_json_and_exit_status.
         AC-4 → test_repeated_warm_isolated_lookup_measures_less_than_one_second.
         RED command: bash scripts/validate-contracts.sh --model-catalog-only → exit 1, 15 failures/0 errors, each asserts absent intended command before attempting to import/execute it; bash -n and Python syntax checks pass.
         Focused --model-catalog-only executes tests/model-catalog.py; default validation includes the same suite. No implementation, network, real catalog or user configuration writes.
         tdd: test amended — test_strict_schema_identity_and_vocabulary_reject_invalid_payloads — malformed fixtures missing provider/id raised KeyError in the test renderer before validation; authorized renderer-only correction uses get with a missing marker at tests/model-catalog.py lines 59, 62, 63, 68. All 15 test identities, assertions, expected values and rejection cases are unchanged.
         tdd: amendment digests — original SHA256 9782913acc8a0488401a55cdaadadb18397c77c97f3359a9efb3adb801fdacbe; corrected SHA256 4843928a6f1f360ed634de57247372ef898b5ed0db52b34a6452e442a0c5941e.
         GREEN focused: bash scripts/validate-contracts.sh --model-catalog-only → 15/15 pass; 100 warm isolated lookups measured 0.049349 seconds, with no live selection timing or savings claim. Python syntax/mandatory function annotations and modified shell syntax pass.
         Additional regression evidence: test_oversized_price_reports_unavailable_and_preserves_failed_refresh first observed OverflowError; test_windows_newline_candidate_is_inspected_and_installed_consistently first observed rejected CRLF Markdown; test_failed_temporary_cleanup_reports_error_and_preserves_previous_catalog first observed escaping PermissionError. Each was run before its implementation repair; original 15 assertions remain unchanged.
         Final focused acceptance: 18/18 pass; tests/model-catalog.py SHA256 e9d43be5620321577c69091760ac047e80242c0e814311fb0fe7c58a51bcf453; measured 100 warm isolated lookups in 0.063546 seconds. The ordinal capability source contract explicitly excludes uncalibrated judgments; prices remain separate source references.
         Final verification: original 15 frozen test method ASTs exactly match the RED commit; 3 added edge regressions, 18/18 focused acceptance checks pass. Python syntax and mandatory function annotations pass; all repository Bash syntax checks pass. shellcheck unavailable; no standalone type checker configured. Build skipped because it deploys global configuration, explicitly outside scope.
         Broad regression terminal: bash scripts/validate-contracts.sh → exit 1; 590 passed, 1 failed, 2 optional skips. Sole failure is the unchanged public-identity gate requiring docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md, which is absent from main. Catalog acceptance and all hook/workflow groups pass. Output /tmp/model-catalog-full-validation.txt.
         Finalization deltas returned to root: plan status → done; architecture add optional catalog helper purpose/schema/APIs and isolated focused/default acceptance; runbook add focused --model-catalog-only. No architecture, plan, composite or compression edits applied; no composite membership.
         Independent validation: all four leaf Acceptance Criteria are met by focused tests and inspection. bash scripts/validate-contracts.sh --model-catalog-only passed 18/18; 100 warm isolated lookups measured 0.048103 seconds, without a live selection timing or savings claim.
         Independent frozen-test audit: the RED commit SHA256 matches 9782913acc8a0488401a55cdaadadb18397c77c97f3359a9efb3adb801fdacbe; all 15 original test method ASTs are unchanged; three additional regression tests exist; the renderer-only change matches its recorded amendment; current SHA256 e9d43be5620321577c69091760ac047e80242c0e814311fb0fe7c58a51bcf453.
         Independent adversarial evidence: 165 schema/evidence type mutations produced no unexpected exceptions; injected fsync failure and invalid UTF-8 refresh candidates preserved previous catalog bytes and left no staging file. Runbook Bash syntax lint and focused Python syntax/function annotations pass; shellcheck is unavailable; no standalone type checker is configured; deployment remains outside scope. The broad regression result remains owned by root and is not claimed here.
         important: scripts/model-catalog.py:25,41 and tests/model-catalog.py:15,26 use typing.Any without an explicit explanatory comment. principles/python-standards.md requires "No Any without explicit comment explaining why" and forbids unexplained Any. No applicable exemption is recorded. Add the required local justification or replace the dynamic types; preserve frozen test bodies. Verdict NEEDS WORK; do not run pav-propose or pav-close until corrected.

         autonomous repair — dynamic JSON/runpy Any rationale added; executable ASTs and frozen test bodies unchanged; focused 18/18 pass; comments-only test SHA256 041dc4cb96a31bb2f7bc74a80114f7cde92b96efe453a54e358b1f35dca9bfdd.
         Independent revalidation: the required Any rationale is now explicit at both dynamic boundaries. The comments-only repair preserves the complete executable AST of both helper and tests, with all 15 RED test method ASTs unchanged and three additive regressions. Focused acceptance passed 18/18; 100 warm isolated lookups measured 0.045701 seconds. Current test SHA256 041dc4cb96a31bb2f7bc74a80114f7cde92b96efe453a54e358b1f35dca9bfdd. The prior important typing finding is resolved; all four leaf Acceptance Criteria remain met.

  branch: feat/local-model-catalog
  base_branch: main
  base_commit: 21916508a73d45fece9e35c01f78d8ad0ad3bf52
  commits: 5b8794056b1be9f1e249f668d94e51b7c2be0b35 test(catalog): cover freshness and atomic refresh rules, c75bf4acee3cdc395efe61ddd722edadf4cab7a2 feat(catalog): add validated local catalog and atomic refresh, a13668755cb1a842ad6a6faf132a8a81996a0e7f docs(catalog): explain dynamic JSON boundary types
  pr: #31 ready

T-05 | Required archive preservation | atomic-tests: n-a | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — both criteria met; six historical records and exact identity gate preserved
  target_files: docs/analysis/2026-09-16-rules-workflows-naming-review.md, docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md, docs/analysis/2026-09-16-comparative-analysis.ru.md, docs/audits/2026-07-21-logic-audit-fixes.md, docs/audits/2026-10-26-hook-logging-final-review.md, docs/audits/AUDIT-PROMPT.md, docs/README.md
  blocker: none
  notes: tdd: none — restoration/faithful translation of documentation only; no new pure logic (unit), service boundary (integration), runtime API/schema (contract) or infrastructure configuration (smoke). Existing unchanged identity gate was observed failing before repair and is rerun as preservation verification; no gate/ledger relaxation.
  branch: fix/restore-required-archives
  base_branch: feat/local-model-catalog
  base_commit: a13668755cb1a842ad6a6faf132a8a81996a0e7f
  commits: 71c4832df290942d6fdb441f1660aad10c83322a fix(docs): restore referenced historical records
  pr: #32 ready
         Verification: four source blobs preserved; English translations preserve all original physical lines, inline-code spans, exact token tuples/legends and semantic meaning; independent semantic review passed. Original validator unchanged. Clean verification worktree: /tmp/orchestrail-catalog-verify.8cAbXt.
         Independent validation: both Acceptance Criteria met. Four restored English files exactly equal historical source 8c2fa08; all six index links resolve. Translations retain original 81/456 physical lines, every inline-code span, exact identity positions/counts, unchanged legends and numerical values; two TL;DR digit-to-word conversions preserve 4 as four. Independent comparison-table, quantitative and recommendation review found no meaning-changing differences.
         Original pre-removal identity function and ledger section exactly match history. The unchanged focused identity/knowledge preservation function passed with exit 0 in clean commit 71c4832; the clean verification worktree remains unmodified. Documentation diff whitespace and all runbook Bash syntax checks pass; shellcheck unavailable. No broad-suite result claimed. Justified documentation-only n-a retained; no runtime or gate behavior changed.
         Batch improvement review: no proposals; no discretionary changes applied.

T-02 | Conservative model selection | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — all four criteria met; frozen tests, conservative selection and isolated adversarial checks verified
  target_files: tests/model-selection.py, scripts/validate-contracts.sh, scripts/model_selection.py, scripts/model-catalog.py
  blocker: none
  notes: tdd: unit primary for pure floor/filter/economics/traits; CLI contract for JSON recommendation and exit/write boundaries; 19 tests, AC coverage 4/4.
         tdd: red digest — AC-1 → test_floor_every_score_tuple_has_exact_bounded_weighted_result, test_floor_every_worsening_neighbor_never_decreases_requirement, test_floor_invalid_scores_and_unknown_constraints_are_rejected; AC-2 → test_floor_hard_categories_require_five_even_with_easy_creative_work, test_eligibility_actual_availability_is_required_before_economics, test_eligibility_context_tools_owner_and_quality_precede_economics, test_eligibility_unknown_limits_and_empty_allowlist_do_not_admit_candidates, test_identity_same_id_different_providers_is_never_conflated, test_request_invalid_snapshot_requirements_and_owner_shapes_are_rejected, test_selection_is_offline_readonly_repeatable_and_does_not_mutate_inputs; AC-3 → test_economics_price_band_equal_prices_and_unknown_prices_retain_default, test_economics_qualified_comparable_total_cost_can_recommend_cheaper_model, test_economics_incomparable_or_unqualified_evidence_retains_default, test_economics_equal_overlapping_invalid_and_missing_totals_retain_default, test_economics_stronger_first_remains_selectable_with_qualified_lower_total, test_default_missing_or_unsuitable_uses_strongest_eligible_without_invented_identity; AC-4 → test_traits_legacy_mapping_is_explicit_and_unknown_conflicts_are_rejected, test_traits_each_override_filters_support_without_bypassing_quality_floor; CLI/offline edges → test_selection_is_offline_readonly_repeatable_and_does_not_mutate_inputs, test_cli_selection_reports_recommendation_and_refuses_refresh_combination_before_writes
         RED command: bash scripts/validate-contracts.sh --model-selection-only → exit 1, 19 failures/0 errors. Every test reaches the explicit absent-selection-policy assertion before imports or subprocess execution; no fixture/collection/syntax failures. Output /tmp/model-selection-red.txt.
         Frozen test SHA256 675a4c3f63cfaff19eb6727f301a8680c0f1679ad6e314e34ab197d98009228f; Python syntax and mandatory annotations pass for all 26 functions; modified Bash syntax passes. Focused/default validator dispatch included; no implementation file changed.
         Loaded project architecture/state, architecture/coding/domain principles, ADR index, runbook and Python/testing standards; no umbrella context present. Runbook test command scoped to --model-selection-only. No network, provider, model execution, real-home writes or broad suite.
         Intermediate focused result: 18 tests pass; the sole remaining failure was the intentionally not-yet-integrated --select CLI. Canonical integer scoring, hard floors, filters, legacy traits and qualified interval comparisons implemented; no frozen test edits.
         tdd: added red regression — test_request_dated_harness_snapshot_cannot_authorize_current_selection observed 1 test/4 failures (ages 1/14/31/365; expected ValueError not raised) before enforcing current-date harness observations; /tmp/model-selection-snapshot-red.txt. Original 19 test bodies and all original fixture bytes are unchanged; no amendments.
         GREEN final focused: bash scripts/validate-contracts.sh --model-selection-only → 20/20 pass in 5.175 seconds; --model-catalog-only → 18/18 pass. Selection timing is fixture-suite runtime, not live selection latency or savings. Current test SHA256 9713981787edfbe2622515b43de6a41658c86e4d70b3bd83265db003cd6f125f.
         Active support contract: callers observe actual provider/id availability, context and tools afresh on every invocation, supply source reference and harness.date equal to today; any prior/future date is rejected. Catalog TTL and historical economic evaluation dates do not authorize current requestability.
         Bounded adversarial checks passed: 299 JSON type mutations; duplicate estimate identities; contradictory comparable winners; input-order determinism; future snapshot dates; duplicate CLI JSON keys; no unexpected exceptions/writes. No additional tests were added for behavior already passing these probes.
         Final source verification: all functions annotated; dynamic Any has explicit JSON-boundary rationale; new selection functions at most 30 lines/3 parameters; 22 selection functions, 17 catalog functions and 27 test functions pass syntax/annotation checks. All repository Bash syntax and scoped diff whitespace pass. shellcheck unavailable; no standalone type checker configured. Build not run because it deploys globally, outside scope. Broad integration remains root-owned for final clean worktree.
         Interfaces: quality_floor(scores, hard_constraints=()) -> int; normalize_traits(traits) -> list[str]; select_model(validated_catalog_payload, request, today) -> JSON-compatible recommendation. select_catalog(catalog_path, request_path, today) adds offline file/CLI adapter; --select REQUEST.json and --refresh CANDIDATE are mutually exclusive before writes; selected exits 0, stopped/unavailable exits 2. No actual execution identity is claimed and session_action stays preserve.
         Finalization deltas returned to root: plan T-02 → done; architecture add pure selection helper/API, current-date support snapshot, independent ordinal floors and qualified cost intervals; runbook add --model-selection-only. No plan/architecture/shared compression edits applied; no composite membership. Preserve protected notes and git fields; no stale content within this leaf requires compression.
         Independent validation: all four leaf Acceptance Criteria are met by the focused tests and source inspection. Selection acceptance passed 20/20; catalog regression passed 18/18, with 100 isolated catalog lookups measured in 0.040823 seconds. No live model timing or savings is claimed.
         Independent frozen-test audit: the RED commit bytes match SHA256 675a4c3f63cfaff19eb6727f301a8680c0f1679ad6e314e34ab197d98009228f; all 19 original test method ASTs are unchanged; one current-date snapshot regression is additive. Current test SHA256 9713981787edfbe2622515b43de6a41658c86e4d70b3bd83265db003cd6f125f. AC coverage 4/4; no weakening or vacuous assertions found.
         Independent adversarial evidence: 960 request JSON mutations produced no unexpected exceptions; all 216 catalog/harness/estimate order permutations select consistently. Contradictory qualified comparisons preserve the default; all 15 trait/hard-floor combinations stop when frontier evidence is absent; prior/future harness dates reject. Duplicate-key, nonfinite, malformed and non-UTF8 CLI inputs return unavailable/exit 2, preserve catalog bytes and create no configuration files.
         Independent source review: exact identities, current support, owner/context/tools, independently evidenced quality and mandatory floors precede economics; unknown or overlapping economics preserve a suitable baseline; recommendations never execute models or claim actual identity. Dynamic Any rationale is explicit; all 22 selection functions, 17 catalog functions and 27 test functions have mandatory annotations. All production function bodies, including select_catalog (17 lines) and main (23 lines), satisfy the 30-line/3-parameter limits. Scoped diff whitespace and all repository Bash syntax pass; shellcheck unavailable. No standalone type checker configured; deployment and broad regression remain outside this leaf's validation scope.
         Batch improvement review: no proposals; no discretionary changes applied. Protected evidence remains current; no leaf compression required. Orchestrated mode: plan transition T-02 → reviewed returned to root; shared files and broad regression remain root-owned.
  branch: feat/conservative-model-selection
  base_branch: fix/restore-required-archives
  base_commit: 71c4832df290942d6fdb441f1660aad10c83322a
  commits: 758eb1606ca8552e255fbd112ceefc16d0dc8e67 test(selection): cover quality floors and conservative routing, d77c34dd331e3a8bc90a9d73db684cfb386ef3d2 feat(selection): enforce quality floors and qualified cost evidence
  pr: #33 ready

T-03 | Compatible plan model resolution | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation closed DONE — four criteria met; 25 plan, 18 catalog and 20 selection tests pass
  target_files: tests/model-plan.py, scripts/validate-contracts.sh, scripts/model_plan.py, scripts/model-catalog.py
  blocker: none
  notes: tdd: unit primary for header-based parsing, bulk transforms and independent request resolution; contract for JSON CLI/schema; integration for isolated atomic filesystem writes; 22 tests, AC coverage 4/4.
         tdd: red digest — AC-1 → test_legacy_reordered_columns_read_exact_active_provider_requests; test_dual_columns_override_conflicting_legacy_by_active_provider; test_absent_empty_and_placeholder_models_mean_explicit_session_default; test_escaped_pipes_fenced_examples_and_composite_blanks_preserve_rows; test_malformed_and_ambiguous_tables_are_rejected_before_reading.
         AC-2 → test_bulk_additions_preserve_unknown_columns_statuses_and_composite_blanks; test_existing_provider_updates_preserve_every_untouched_byte_and_allow_clear; test_legacy_migration_requires_explicit_values_for_each_added_provider; test_invalid_bulk_updates_leave_original_plan_bytes_unchanged; test_atomic_replace_failure_preserves_plan_and_cleans_staging_file; test_cli_auxiliary_flags_are_validated_before_any_mutation.
         AC-3 → test_exact_requested_identity_resolves_without_economic_substitution; test_identity_uses_provider_and_exact_id_without_provider_switching; test_unsupported_request_stops_visibly_without_undeclared_or_unauthorized_fallback; test_authorized_declared_suitable_fallback_is_visible_and_never_actual; test_fallback_independently_obeys_support_quality_context_tools_owner_and_traits; test_session_default_resolves_only_its_own_suitable_identity_or_stops; test_stale_support_and_malformed_resolution_inputs_fail_explicitly.
         AC-4 → test_actual_requires_fresh_separate_evidence_of_the_authorized_resolved_identity; test_resolution_is_pure_without_network_files_processes_or_input_mutation; test_cli_read_update_and_resolve_are_explicit_json_operations; test_cli_rejects_invalid_updates_and_reports_unavailable_support_without_writes.
         RED command: bash scripts/validate-contracts.sh --model-plan-only → exit 1, 22 failures/0 errors; every test first asserts the missing scripts/model_plan.py behavior before import. Python AST syntax, annotations, 30-line body/3-parameter limits and modified Bash syntax pass. Output /tmp/model-plan-red.txt.
         API contract: read_plan(markdown, provider) returns ordered rows {id,status,source,requested}; update_plan(markdown, updates) returns preserved Markdown; write_plan(path, updates) returns bool changed after atomic replacement. Updates are {row_id:{anthropic:null|exact_id,openai:null|exact_id}}; added columns require explicit values for each nonempty legacy request, preventing accidental default migration.
         Resolution API: resolve_model(catalog, request, today); request has provider, requested:null|{provider,id}, selection (public selection request), fallback:{authorized:bool,model:null|identity}, execution:null|{model:identity,reference,date}. Public selection eligible/excluded output with economics disabled supplies suitability; no arbitrary selected baseline is accepted. Status is resolved/session-default/fallback/stopped; actual is null unless separate current-day execution evidence matches the authorized resolved identity.
         CLI contract: --read-plan PLAN --provider anthropic|openai; --update-plan PLAN --updates JSON; --resolve-plan PLAN --provider anthropic|openai --row ID --resolution JSON [--catalog PATH] [--today DATE]. Resolution JSON has selection/fallback/execution; requested/provider derive from the selected plan row. Invalid auxiliary combinations reject before mutation; runtime/schema failures emit JSON status unavailable and exit 2. Read and update do not require a catalog; resolution never executes a model.
         Frozen test SHA256: 1866d62e268365eaaf6f08cde502989e42193cbc6cc4bbb62ac674d5d9f5c0e6; focused/default dispatch added; no implementation created.
         Additional observed regressions: test_cli_stale_support_preserves_requested_identity_and_error_reason failed with requested null instead of known planned identity; test_unbounded_last_row_is_rejected_before_atomic_updates failed because malformed final row was silently skipped and mutation proceeded. Both repaired after observation; original 22 test method bodies unchanged. Focused 24/24 pass.
         Additional observed regression: test_indented_code_table_is_preserved_and_never_read_as_a_plan first failed with ambiguous-table ValueError because an indented example was parsed as a plan; Markdown indented code is now ignored and preserved. Original 22 frozen method ASTs exactly match the RED commit; 3 additive regressions; 25 current tests pass.
         GREEN verification: bash scripts/validate-contracts.sh --model-plan-only → 25/25; --model-selection-only → 20/20; --model-catalog-only → 18/18. Focused/default plan dispatch remains intact. Current tests/model-plan.py SHA256 eb48b52750f1be30f3720caa07aba5f4a28ef391a076397a3699bc8ccbfb0dc7.
         Bounded adversarial verification: 360 reordered-column/LF/CRLF/CR/no-final-newline/escaped-pipe round trips preserved untouched Markdown and idempotence; injected fsync/chmod/replace failures preserved original bytes and removed staging files; 22 malformed-resolution and both-provider requestability checks pass. Separate read-only review confirmed request-ID error retention and trailing-row repair; auxiliary-flag rejection and matching/mismatched receipt checks pass.
         Quality verification: Python AST syntax and mandatory annotations pass across all affected files; every new/affected function satisfies <=30 body lines and <=3 parameters; explicit Any rationale is present. All runbook Bash syntax checks and scoped diff whitespace pass. shellcheck unavailable; no standalone type checker configured. Build skipped because it deploys global configuration; no full broad suite run, as root owns it.
         Acceptance evidence: AC-1 provider precedence/default/legacy/reordered/composite/escaped/fenced/indented fixtures pass; AC-2 exact untouched-byte/CRLF/no-final-newline/idempotent/malformed/atomic-failure fixtures pass; AC-3 unavailable exact requests stop or use a declared authorized independently suitable fallback, with original ID and reasons preserved; AC-4 actual stays null absent a distinct current-day matching execution receipt, pure resolution reads no files/history and starts no process/network operation.
         Finalization deltas returned to root: plan status → done; architecture add optional scripts/model_plan.py purpose and read_plan/update_plan/write_plan/resolve_model APIs, provider-column precedence, explicit legacy migration and current receipt rule; runbook add --model-plan-only. Root owns shared architecture/plan/compression and final broad validation; no composite membership or rollout changes.
         Independent validation: all four leaf Acceptance Criteria are met. Focused plan acceptance passed 25/25, catalog regression 18/18 and selection regression 20/20. Additional in-memory probes passed reordered dual/legacy exact-byte preservation, CRLF/final-newline preservation, idempotency, unknown/unavailable request/default stops and stopped-request receipt rejection. No product edits, Git mutations, other shared-file edits, network/provider/model calls or telemetry-history reads occurred.
         Independent frozen-test audit: all 22 original test method ASTs at 9f5a4c84ebedac99457f7355bc9e985a47177e7f are unchanged; three regressions are additive; no missing tests, skip/xfail or weakened assertions. Current tests/model-plan.py SHA256 eb48b52750f1be30f3720caa07aba5f4a28ef391a076397a3699bc8ccbfb0dc7. Every criterion retains concrete behavior coverage; no amendment was needed.
         Independent source review: active provider columns override legacy even when empty; absent columns use legacy or explicit session default. Explicit migration protects old requests; malformed/ambiguous tables and updates fail before atomic replacement. Resolution uses independent suitability and exact identities, declares fallback authorization/reasons and otherwise stops. Execution evidence is caller-owned: the helper validates receipt structure, reference, current date and authorized resolved-identity match; it neither authenticates an external observation nor executes a model. Without that separate evidence actual stays unknown.
         Independent quality checks: 26 plan functions, 23 catalog functions and 32 fixture/test functions have mandatory annotations and satisfy 30-line bodies and three-parameter limits; dynamic Any has explicit boundary rationale. Scoped committed diff whitespace and repository Bash syntax pass; shellcheck is unavailable and no standalone type checker is configured. Broad validation and deployment remain root-owned.
         Batch improvement review: no proposals; no discretionary changes applied.
         Orchestrated close: plan transition T-03 → reviewed returned to root. Protected test and Git evidence remains intact; this leaf has no stale validation content to compress. Shared plan, architecture, parent-wide compression and final broad validation remain root-owned.
  branch: feat/compatible-model-resolution
  base_branch: feat/conservative-model-selection
  base_commit: d77c34dd331e3a8bc90a9d73db684cfb386ef3d2
  commits: 9f5a4c84ebedac99457f7355bc9e985a47177e7f test(plans): cover model-column compatibility and resolution, 71238de0beb83de1b6665ec6e2e26ca8d75c1ebc feat(plans): add compatible model columns and visible resolution
  pr: #34 ready

T-04 | Cached selector workflow integration | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all four criteria met; 87 focused tests and unchanged instruction checks pass; installed guidance and role boundaries verified
  target_files: workflows/pd-select-model.md, workflows/spec-run.md, workflows/pe-execute.md, workflows/phase-atomic-execution.md, rules/workflow-reference.md, workflows/pd-decompose.md, workflows/pd-design.md, workflows/pd-finalize.md, docs/MODEL-CATALOG.md, docs/USAGE.md, docs/SPEC-RUN-QUICKSTART.md, docs/README.md, workflows/PIPELINE.md, tests/model-workflow.py, scripts/validate-contracts.sh
  blocker: none
  notes: tdd: contract primary; integration for documented public CLI examples, smoke for canonical/reference drift; 17 new test methods, AC coverage 4/4. Scope matches the expanded reader audit in description.md; no additional readers found. Canonical columns belong in workflow-reference, with no new definition in workflow-globals.
         Bootstrap: WORK_DIR=<repository-root> (local absolute checkout path omitted for publication); AI_DIR=WORK_DIR/.ai; no umbrella context. Loaded memory/architecture.md, memory/state.md, principles/architecture.md, principles/coding.md, principles/domain.md, adr/index.md and context/runbook.md; test command bash scripts/validate-contracts.sh.
         tdd: red digest — AC-1 → test_selector_cached_single_bulk_contract_is_compact_and_reachable, test_selector_explicit_refresh_research_preserves_failed_install, test_selector_unavailable_dependencies_preserve_session_without_eligibility_bypass, test_guide_cli_refresh_success_and_rejection_preserve_prior_bytes, test_guide_cli_default_path_and_missing_dependencies_preserve_session; AC-2 → test_canonical_model_columns_define_empty_precedence_and_explicit_migration, test_canonical_resolution_requires_invocation_support_permissions_and_restrictions, test_canonical_resolution_separates_request_resolution_and_observed_actual, test_execution_readers_resolve_before_request_and_preserve_inline_session, test_discovery_and_quickstart_readers_preserve_optional_columns_and_staleness, test_guide_cli_plan_compatibility_and_migration_are_explicit, test_guide_cli_resolution_surfaces_request_fallback_stop_and_unknown_actual, test_guide_cli_current_support_tools_and_unknown_quality_cannot_be_inferred; AC-3 → test_contract_gate_rejects_broken_helper_canonical_reader_and_guide_links, test_operating_documents_reach_cached_guide_and_drop_retired_contract; AC-4 → test_guide_documents_age_quality_economics_migration_and_ownership, test_guide_timing_labels_measured_fixture_and_unmeasured_live_target.
         Frozen test file SHA256 181ff12ee3918e5b811f6f5917c0bc3df616785a9e75d919733b47df766f7f59; all 17 new methods failed for missing intended caller contracts: absent canonical section/reader references/guide, missing refresh/unavailable policies, and selector 1698 words versus the 1500 maximum. No new test passed and there were no test errors.
         Pre-freeze requirement alignment: root review identified incorrect new expectations for Anthropic Model/OpenAI Model. Corrected only those labels and regex patterns to approved Model (Claude)/Model (Codex), including source=Model (Codex), matching specification REQ-06 and scripts/model_plan.py COLUMNS. No provider/harness rename or product edit. Earlier draft SHA256 ddf8fa937ceb771914689c65cc66e08049b39679642efc42515e5264113bf7f4; corrected digest above. Re-ran the same focused command: all 17 new methods still fail as intended, with 43 assertion reports, zero errors, and the 63 existing helper tests passing.
         RED command: bash scripts/validate-contracts.sh --model-workflow-only → exit 1; 18 catalog, 20 selection and 25 plan existing tests passed; 17 new workflow methods failed with 43 subtest assertion reports; existing workflow-instructions.py passed unchanged. Evidence: /tmp/cached-workflow-red.txt. Default and focused gates register the same five suites. Existing isolated passing tests are not part of the new frozen RED set.
         Test scaffold syntax, mandatory annotations, explicit dynamic Any rationale, at most three arguments and at most 30 function-body lines pass; modified validation shell passes bash -n. Only tests, validation wiring and this leaf block changed. No product implementation, historical store reads, provider/network research, real catalogs, model execution, global deployment, Git writes or logging calls.
         Implementation progress: cached single/bulk selector and explicit refresh/fallback policies now replace live-every-run behavior. Canonical optional column/current-support/receipt rules live only in workflow-reference; six audited workflow readers and four derived operating docs reference the contract/guide. Superseded legacy Model-only validation checks now check explicit compatible provider writes; unrelated assertions remain. Frozen canonical() treats the fenced ## Subtasks example as a section boundary, so the new canonical subsection precedes that example without changing the approved table sample or any frozen test.
         Additive RED regression: test_selector_explicit_refresh_recovers_catalog_before_selection_availability_guard first failed because invalid catalog/current support shared an early return with missing helpers. Proof /tmp/cached-workflow-refresh-recovery-red.txt. The dependency guard now covers only unavailable Python/helpers; explicit refresh can initialize/repair a missing or invalid catalog without selectable current support. Catalog/support failure ends ordinary selection only after an authorized refresh attempt. Original 17 test method ASTs remain unchanged.
         Additive RED regression: test_spec_run_unavailable_model_override_preserves_worker_role_boundaries first failed because the new fallback permitted inline implementation in the Orchestrator. Proof /tmp/cached-workflow-worker-boundary-red.txt. Repaired to retain fresh workers: absent model intent permits ordinary default-worker spawning without claiming selection; an explicit request requires supported model selection or an explicitly authorized independently suitable fallback matching the verified worker default. Unknown default/support cannot satisfy explicit intent. Unavailable worker spawning stops; only standalone executors retain permitted inline execution. Original 17 tests remain unchanged.
         Final GREEN: bash scripts/validate-contracts.sh --model-workflow-only → exit 0; 18 catalog, 20 selection, 25 plan and 19 workflow tests pass (82 total), plus unchanged workflow-instructions.py. Evidence /tmp/cached-workflow-focused-green.txt. All 17 frozen method ASTs exactly match RED commit 539287910d9e3c41a12754bd88ba3b5d962b1184; two additive regressions, no amendments or weakened assertions. Current test file SHA256 74cac960e1fcf94ffd1d17e79ff6dc09745f26422341c350debeebc8809407bf.
         AC verification 4/4: selector/cached refresh/session fallback criteria pass original selector and guide-refresh/dependency tests plus recovery regression; plan-reader criteria pass canonical/reader/plan/resolution/support tests plus worker-role regression; offline drift/reachability and all isolated helper suites pass through shared focused/default registration; ownership/age/traits/quality/economics/provenance/rollback and measured-versus-target guide tests pass. Selector 944 words. Genuine guide CLI operations use only temporary fictional data; missing-dependency reports come from an explicit caller guard, not invented helper success.
         Measurement: executable guide fixture measured 100 warm in-process catalog inspections in 0.044275 seconds; recorded in the guide with date and scope. Final catalog acceptance measured 100 lookups in 0.043616 seconds. Neither result measures live selection or savings; the live 60-second target remains explicitly unmeasured.
         Final checks: all repository Bash syntax passes; test and embedded-guide Python syntax/mandatory annotations/explicit Any rationale/at most three arguments/at most 30 body lines pass; git diff --check passes. Narrow replacement legacy selector gates pass. shellcheck unavailable; no standalone type checker configured. Deployment build excluded; default broad regression remains root-owned and was not run or claimed. No Git mutations, provider/model/network calls, historical-store reads, global deployment or logging calls.
         Orchestrated finalization deltas: plan T-04 Status → done; architecture optional-catalog section should mark workflow integration delivered and describe canonical plan readers, explicit workflow refresh, guide and shared five-suite gate; runbook should add --model-workflow-only as all five offline model/instruction suites. Helper public APIs did not change. No composite membership or rollup. Shared architecture/plan/runbook/compression files were not modified; protected current evidence is retained for root-owned compression.
         Independent validation: NEEDS WORK. AC-1/AC-2/AC-3 are partial because the installed selector/resolver cannot reach the guide schema/rubric through source-relative links, and the derived orchestrated operating procedure contradicts fresh-worker fallback. AC-4 content is otherwise present and exercised by real public CLI examples.
         Important finding: docs/SPEC-RUN-QUICKSTART.md lines 62–64 permits keeping the current session and reporting inline execution when switching is unavailable; workflows/spec-run.md lines 133–139 and 217–220 require a fresh default worker or stop and forbid inline Orchestrator implementation. Reproduce by following the quickstart with workers available but model overrides unavailable. Repair the derived procedure and add contract coverage for that procedure.
         Important finding: ../docs/MODEL-CATALOG.md references in workflows/pd-select-model.md, spec-run.md, pe-execute.md, phase-atomic-execution.md and rules/workflow-reference.md break after scripts/sync.sh copies them into per-skill SKILL.md directories. Temporary layout probes for both supported skill harnesses confirmed all six links point to absent skills/docs paths; no deployment occurred. Explicitly resolve the guide from the configured source root or package it, and add installed-layout reachability coverage.
         Independent focused validation passed: bash scripts/validate-contracts.sh --model-workflow-only; 18 catalog, 20 selection, 25 plan and 19 workflow tests, plus unchanged workflow-instructions.py. No full-suite result is claimed. Frozen SHA256 181ff12ee3918e5b811f6f5917c0bc3df616785a9e75d919733b47df766f7f59 verified against commit 539287910d9e3c41a12754bd88ba3b5d962b1184; all 17 original method ASTs remain identical and two regressions are additive. Unrelated workflow-instructions.py bytes are unchanged.
         Independent quality checks passed: selector 944 words; 24 test functions and five embedded guide functions have mandatory annotations, at most three arguments and at most 30 body lines; scoped committed whitespace and validation-shell syntax pass. Focused fixtures execute documented helpers with fictional isolated data and a network guard. No product edits, Git mutations, real catalog/log reads, provider/model/network calls or deployment occurred. Proposal/close steps are blocked by this NEEDS WORK verdict pending root-owned repair and independent revalidation.
         Authorized review remediation reopens this existing leaf; no established RED tests are regenerated. Contract/smoke/integration classification retained. The source-root recovery is limited to canonical instructions and an executable documentation preflight, with no new runtime script, routing configuration, packaging or deployment. Proposed root resolution uses configured ORCHESTRAIL_HOME or an already-verified invocation-local SOURCE_ROOT; it must never infer a checkout from CWD.
         tdd: red digest — review quickstart authorization (AC-2/AC-4) → test_quickstart_unavailable_override_requires_authorized_default_worker_or_stop; installed guide reachability/source preflight (AC-1/AC-3/AC-4) → test_installed_callers_resolve_guide_from_the_verified_helper_source_root, test_installed_guidance_preflight_uses_configured_or_known_source_not_cwd, test_installed_guidance_missing_root_guide_schema_or_rubric_preserves_inputs; leaf worker intent scope/default roles (AC-2) → test_spec_run_leaf_model_intent_excludes_arbiter_and_independent_validator_defaults.
         Additive review RED: bash scripts/validate-contracts.sh --model-workflow-only → exit 1; all 82 established tests and unchanged workflow-instructions.py pass, while all five new methods fail as expected with 14 assertion reports and zero errors. Evidence /tmp/cached-workflow-review-fixes-red.txt. Failure causes: stale inline quickstart procedure, ten installed caller copies lack helper-root guide paths, executable canonical guidance preflight absent, and broad worker-spawn routing improperly includes roles without leaf model intent.
         Review RED fixtures reproduce actual scripts/sync.sh Claude/Codex per-skill SKILL.md copy destinations and rule- prefix in temporary homes without running sync. Executable-preflight scenarios cover configured versus known verified roots containing spaces, misleading CWD, missing source/guide/schema/rubric and preservation of fictional plan/catalog/session bytes. No product changes or real home/source configuration writes occurred.
         Review frozen preservation: all 19 established test method ASTs exactly match implementation commit a83d8e126fa175c1562263ebe865d951b756b96f, including the original 17 and both existing additions. Five additive methods bring workflow count to 24. Current tests/model-workflow.py SHA256 a1434c87e6dec2b0ee33a367e169dc6d960d532c8fee433cd35a77378dfff546. Python syntax, mandatory annotations, explicit dynamic Any rationale, at most three arguments and at most 30 body lines pass; git diff --check passes. Only the test file and this leaf block changed; product remediation awaits root-owned test commit.
         Review GREEN progress after root checkpoint fe6791e8f186b80a3a9318ffeff8383b81788694: canonical read-only Bash documentation preflight now prefers ORCHESTRAIL_HOME or uses already-verified invocation-local SOURCE_ROOT, checks absolute helper/guide paths and required schema/rubric sections, and returns unavailable without writes or inferred scores/candidates. All installed callers explicitly use the guide under that same helper root rather than CWD or per-skill relative links. Targeted installed-layout/preflight checks pass. No new script, configuration, packaging or deployment was introduced.
         Review role repair: quickstart now mirrors fresh default-worker authorization/stop handling, and spec-run scopes plan rows to leaf Implementers including recreation. Pre-selection Arbiter and independent Validators explicitly retain session-default role workers with fresh capabilities and no inherited implementation model. Targeted quickstart/worker-role checks pass; all 24 frozen test methods and the complete test file remain unchanged.
         Review remediation final GREEN: bash scripts/validate-contracts.sh --model-workflow-only → exit 0; 18 catalog, 20 selection, 25 plan and 24 workflow tests pass (87 total), plus unchanged workflow-instructions.py. Evidence /tmp/cached-workflow-review-fixes-green.txt. All 24 test methods and complete tests/model-workflow.py bytes exactly match root RED checkpoint fe6791e8f186b80a3a9318ffeff8383b81788694; SHA256 remains a1434c87e6dec2b0ee33a367e169dc6d960d532c8fee433cd35a77378dfff546. No test amendments, replacements or weakening.
         Review AC verification: all four criteria pass the preserved and additive focused checks. Installed caller copies resolve guidance under the same verified helper source root; configured roots take precedence, known roots work with spaces, misleading CWD never supplies a root, and missing guide/schema/rubric preserves protected fictional inputs with unavailable status. Quickstart/default-worker authorization and Implementer-only leaf intent now agree with role boundaries. Selector 1017 words. No new script/configuration/deployment or helper interface change.
         Review final quality checks: canonical Bash preflight syntax and all repository Bash syntax pass; frozen tests and embedded guide Python retain mandatory annotations, explicit Any rationale, at most three arguments and at most 30 function-body lines. The new read-only Bash function has no arguments and two body lines. git diff --check passes. shellcheck remains unavailable; no standalone type checker configured. No broad default suite or deployment was run; root owns broad regression and fresh independent revalidation. No Git/shared-file mutations, real home/catalog/log writes or reads, provider/model/network calls or logging calls.
         Review finalization deltas for root: T-04 execution remains done pending fresh validation, not reviewed. Architecture should clarify same-source-root guidance preflight and Implementer-only leaf model intent with explicit default-role workers; helper APIs remain unchanged. Runbook commands need no change; focused gate description may add installed-layout/guidance-absence/role-boundary coverage (87 tests). Shared architecture/plan/runbook/compression were not edited; no composite rollup.
         - validation: fresh independent check at 69898c57650f39c12360556030c45f37c8be5173 is DONE; all four leaf criteria met. Focused gate exited 0 with 18 catalog, 20 selection, 25 plan and 24 workflow tests plus unchanged general instruction checks. Installed Claude/Codex layouts, verified-source read-only guidance, missing-guidance preservation, explicit refresh repair, default-worker stops, role scope and separate actual-identity evidence were inspected against product files. Selector is 1,017 words; scoped shell/Python syntax and diff whitespace pass.
         - validation: frozen evidence independently verified: original 17-test file digest 181ff12ee3918e5b811f6f5917c0bc3df616785a9e75d919733b47df766f7f59 matches 539287910d9e3c41a12754bd88ba3b5d962b1184, and all original method bytes are preserved; full current 24-test file is byte-identical to fe6791e8f186b80a3a9318ffeff8383b81788694 with digest a1434c87e6dec2b0ee33a367e169dc6d960d532c8fee433cd35a77378dfff546. No skips, vacuous tests or weakened assertions found. No provider, model, deployment, network, real-home or history-store operation was performed.
         - validation proposal (optional): tighten the guide example preservation flag to compare exact untouched content; the current prefix comparison can miss appended text. Existing plan-suite exact-byte assertions already protect the product contract. Batch mode records this only; no change is applied.
  branch: feat/cached-selector-workflow
  base_branch: feat/compatible-model-resolution
  base_commit: 71238de0beb83de1b6665ec6e2e26ca8d75c1ebc
  commits: 539287910d9e3c41a12754bd88ba3b5d962b1184 test(selection): cover cached workflow and guide contracts, a83d8e126fa175c1562263ebe865d951b756b96f feat(selection): integrate cached model selection workflows, fe6791e8f186b80a3a9318ffeff8383b81788694 test(selection): cover installed guidance and worker-role boundaries, 69898c57650f39c12360556030c45f37c8be5173 fix(selection): resolve installed guidance and preserve worker roles
  pr: #35 ready

## Execution Report

| Subtask | Outcome | Evidence |
|---|---|---|
| T-01 | reviewed | Independent revalidation; 18 catalog tests; ready PR #31. |
| T-05 | reviewed | Independent semantic/preservation review; unchanged identity gate passes in clean committed stack; ready PR #32. |
| T-02 | reviewed | Independent selection review; 20 selection and 18 catalog tests; ready PR #33. |
| T-03 | reviewed | Independent compatibility review; 25 plan tests and preserved frozen tests; ready PR #34. |
| T-04 | reviewed | Fresh independent revalidation after installed-guidance/role repairs; 87 focused tests plus unchanged instruction contracts; 1,017-word selector; ready PR #35. |
| T-06 | reviewed | Unchanged independent-worker guard repaired without semantic change; fresh independent validation and 87 focused tests pass; all test/validator bytes unchanged. |

Final original integration regression at a83d8e1: 594 passed, zero failures, two optional private-pattern skips; output /tmp/model-catalog-final-validation.txt. Regression on69898c5 returned592/2/2 from the single literal-gate incompatibility and its nested cascade. That approved repair is independently reviewed at 41b627c; the full repaired-tip regression passes594/0/2 at /tmp/model-catalog-final-41b627c-validation.txt, exit0.

## Historical Checkpoints

The unexplained dynamic Any finding was repaired without executable changes and independently revalidated. The pre-existing missing-document identity failure was repaired by the separately reviewed historical-preservation leaf without weakening its ledger or gate. Initial integration review found quickstart role and installed-guide reachability defects; additive RED regressions preceded repair, and a fresh independent validator closed the leaf. Protected per-leaf TDD/Git/review evidence is retained above. No current execution blocker remains. Logging is skipped because ORCHESTRAIL_HOME is unset.

## Autonomous Resume

The owner explicitly requested independent analysis, decisions and high-quality efficient completion. Routine review findings and technical blockers are authorized for repair followed by independent revalidation, without another human stop. Preserve safety rails, frozen tests, evidence and unrelated edits. Resume the existing recorded branch/commits rather than creating a replacement branch. Known dirty files are this run's local knowledge plus unrelated user-edited later specifications; preserve those later specifications byte-for-byte and stage only explicit product paths. Repair the pre-existing documentation blocker from evidence, without weakening the public identity gate.

## Prerequisite Documentation Repair

The current main commit removed six still-linked archive documents without updating the identity ledger or documentation index. Preserve the existing gate/ledger: restore the four English records from verified parent8c2fa08c18115ffcf38a1798742c41e53a2c7461 and translate both historical Russian comparisons faithfully at compatible paths. Keep exact authorized identity-token positions and the redaction legends. This documentation-only repair is authorized by the owner's autonomous-completion instruction; it changes neither selector behavior nor acceptance criteria. Record a separate documentation commit before extending the stack; no new unit tests are required for restoration/translation.

Publication: SSH push with a verified DNS address and existing host-key/identity verification succeeded; catalog ready PR #31 opened. HTTPS credential fallback was not used. Current unrelated user specification edits produce extra legacy-name ledger occurrences; final broad regression will use a clean detached worktree of task commits, leaving those files unchanged.

Current continuation: all original leaves and the validation fix are independently reviewed. The complete final regression at 41b627c passes594/0/2 in a clean worktree. All original leaves and the approved validation fix are reviewed. Preserve user-edited later specifications; only optional future fixture precision remains deferred.

Selection policy refinement: retain the weighted signal formula, clamp adjusted raw to independent ordinal quality1..5; mandatory security/financial/architecture/core-invariant floor is5. Demand labels are display-only and never cost eligibility gates. Comparable expected-total-cost evidence is required to displace a suitable default; token prices/equal ordinal quality alone do not establish equivalent-task cost. Sources: REQ-03/04/05, existing scoring formula, shared G8, Arbiter citation-backed recommendation.

T-06 | Compatible independent-validator wording | atomic-tests: n-a | atomic-execution: complete | atomic-validation: complete
  last_action: DoD complete; independent wording, frozen-byte and focused regression validation passed; T-06 reviewed delta returned to the orchestrator
  target_files: workflows/spec-run.md
  blocker: none
  notes: validation issue #1; restore literal existing independent-worker contract without weakening tests or changing role semantics.
         tdd: none — unit is inapplicable because no pure logic changes; integration because no real boundary changes; contract because no executable interface or shared payload changes; smoke because no declarative infrastructure or configuration changes. Only equivalent instructional wording changes; the existing literal guard is regression evidence, not a new behavior or test exemption based on existing coverage.
         before: unchanged grep from scripts/validate-contracts.sh independent-validator check returned exit 1 before editing workflows/spec-run.md; no new tests written and all frozen test files remain untouched.
         verification: unchanged grep now exits 0; bash scripts/validate-contracts.sh --model-workflow-only exits 0 with catalog18, selection20, plan25, workflow24 and unchanged general instruction checks passing; bash -n scripts/validate-contracts.sh and git diff --check -- workflows/spec-run.md pass.
         frozen bytes: scripts/validate-contracts.sh plus all 11 test files have identical before/after aggregate SHA256 5c04159b4331eb18225f761a58e6bb50410de48c4be41d0fbf54474c6254083f; no test file changed. Full broad regression remains owned by the orchestrator.
         architecture.md: no update needed — no modules, interfaces, role behavior or authorization restrictions changed. Own progress block is current; no compression needed. Orchestrated finalization delta: T-06 plan Status → done; shared files and Git remain owned by the orchestrator.
         validator: independent pav-check DONE at 41b627c — all three criteria met; unchanged literal gate fails at 69898c5 (exit 1) and passes at HEAD (exit 0); all 87 focused model tests and unchanged instruction contracts pass. All 11 test files and both validators are byte-identical at base, HEAD and worktree. Separate session-default spawning, fresh capability/permission/restriction checks, no model override or Implementer inheritance, unknown identity and unavailable-spawn stop remain explicit. The documented none level is justified independently: equivalent wording adds no pure logic, real boundary, interface/payload behavior or declarative configuration; the existing required gate supplies regression evidence. Shell syntax and scoped whitespace pass; shellcheck unavailable; broad regression remains owned by the orchestrator. No critical or important findings.

  branch: fix/independent-validator-wording
  base_branch: feat/cached-selector-workflow
  base_commit: 69898c57650f39c12360556030c45f37c8be5173
  commits: 41b627cb8910570178a32e587bf11d2ba67f84d5 fix(workflows): retain explicit separate validator wording
  pr: #36 ready

## Improvement Proposals (T-04)

### Do Now
None.

### Do Later
None.

### Optional
- Tighten the guide example preservation flag in `docs/MODEL-CATALOG.md` and its workflow assertion: the current `splitlines()` plus `startswith()` check accepts appended text on unrelated lines. Compare exact untouched content so that such a mutation fails. The companion plan suite already checks exact bytes, so this is additional fixture precision rather than an unmet product criterion. No change was applied in batch mode.

## Contract Check

### Invariants
| Invariant | Status |
|---|---|
| Ordinary lookup/tests are offline; refresh is explicit and transactional | PASS — strict catalog validation precedes same-directory atomic replacement; offline/failure fixtures pass. |
| Unknown evidence never becomes invented identity, price, quality or actual execution | PASS — unknown quality is excluded; actual requires separate matching current execution evidence. |
| Availability, capabilities, owner limits and quality precede economics; worsening risk cannot lower the floor | PASS — eligibility precedes qualified comparisons; exhaustive score and worsening-neighbor fixtures pass. |
| Legacy and missing optional columns retain explicit default behavior | PASS — header-based precedence, present-empty defaults and explicit populated-legacy migration are independently tested. |
| Helpers never spawn models or become a mandatory runtime | PASS — optional read/recommend/resolve/update operations and conservative default-worker/stop paths remain explicit. |
| Frozen tests precede implementation; independent validation and one writer remain intact | PASS — commit order and independent AST/byte audits preserve original catalog15, selection19, plan22, workflow17 and final repair24 test methods; workers return shared deltas. |

### Acceptance Criteria
| Criterion | Status |
|---|---|
| AC-01 — Clock-controlled freshness/errors and failed-refresh preservation | PASS — 13/14/30/31-day, invalid-date, offline and unchanged-byte failure fixtures pass in tests/model-catalog.py. |
| AC-02 — Independent quality, availability floors and qualified economics | PASS — unsuitable cheap candidates, unknown/equal prices and unqualified/overlapping comparisons cannot bypass eligibility or displace the suitable baseline; strong-first remains eligible. |
| AC-03 — Total bounded score mapping and monotonicity | PASS — integer/clamped floor and sensitive floor 5 cover all 78,125 score tuples and worsening neighbors. |
| AC-04 — Compatible plans, visible fallback/stop and truthful actual identity | PASS — legacy/dual/default, explicit migration, unsupported identities and independent matching/mismatched receipts pass in tests/model-plan.py. |
| AC-05 — Compact selector, measured lookup, drift/installed reachability and guide | PASS — 1,017 words; 100 isolated lookups below one second; installed-source/missing-guide/worker-role fixtures pass; guide defines ownership, rollback and measured fixture versus unmeasured live target. |

### Off-limits
| Constraint | Status |
|---|---|
| Do not read historical run logs | PASS — only explicit input/evidence and disposable fixtures; no shared-store discovery or direct reads. |
| Do not change logging schemas or monetary definitions | PASS — no logging producer/schema/ledger changes; separate snapshot/comparison ownership. |
| Do not deploy global configuration | PASS — only temporary installed-layout fixtures; no real deployment. |
| Do not call a provider | PASS — no provider client or execution path; no provider/comparative calls during validation. |
| Do not silently substitute models | PASS — exact eligible intent or declared authorized eligible fallback, otherwise stop. |
| Do not promote a cheaper production default | PASS — no real catalog/default bundled; advisory comparison cannot waive authorization. |
| Do not migrate or rename harnesses | PASS — existing names/layouts preserved; current capability inputs only. |
| Do not merge PRs | PASS — all six PRs are open and ready for review after verified promotion. |
| Do not push main | PASS — only recorded feature/fix branches published. |
| Do not commit .ai/ | PASS — combined committed path audit contains no .ai/ paths. |

### Verification Summary
Independent formal contract review: 21 passes, zero failures, zero critical. Current focused gate:87 tests plus unchanged instruction contracts. Prior integration full regression: a83d8e1,594/0/2. Full regression at 69898c5 completed592/2/2 from the single approved wording issue and its nested cascade. Repair at 41b627c is independently reviewed; final complete regression passes594/0/2. Terminal evidence: /tmp/model-catalog-final-41b627c-validation.txt; exit0. No unresolved critical or important findings. Source evidence includes scripts/model-catalog.py:182–250, scripts/model_selection.py:106–124 and211–236, scripts/model_plan.py:183–219 and308–352, rules/workflow-reference.md model contract, and the four model test suites. Shell syntax and scoped whitespace pass; shellcheck unavailable.

## Code Review

### Findings
1. Important — unchanged scripts/validate-contracts.sh:759–760 requires literal `Spawn a **separate** sub-agent`; revised workflows/spec-run.md uses `Spawn a **separate** session-default role worker`. Existing gate fails despite preserved semantics, also causing nested version-history validation failure. Restore compatible explicit wording without changing the gate or role restrictions.
2. Optional — docs/MODEL-CATALOG.md example computes unrelated_bytes_preserved using splitlines/startswith; this flag could accept appended unrelated text or newline changes. The companion plan suite already verifies exact byte preservation; no updater defect exists. Strengthening this demonstration predicate is a future enhancement.

### Summary
Independent formal review: two findings, zero critical, one important repaired and independently revalidated, one optional deferred. Final repaired-commit broad regression exposed the important gate incompatibility; no broad success is claimed at 69898c5. Frozen tests, source quality, pure helper boundaries and exact product preservation pass. The nested version-history failure has the same cause as the direct wording failure, not another defect.

## Issue List

### Approved
1. Restore compatible explicit independent-validator wording. Priority: important. Approved automatically under spec-run validation policy and the owner's autonomous-remediation instruction. Completed by reviewed T-06 at 41b627c; unchanged gate and 87 focused tests pass.

### Deferred
2. Strengthen the guide example's preservation predicate. Priority: optional; no product defect and exact preservation already covered. Deferred under the optional-proposal policy; retain as a nonblocking future fixture improvement.

## Fix-Tasks
fixes-created: complete
fixes-count: 1
Created: T-06-fix-independent-validator-wording

### Fix Classification
| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|---|---|---|---|---|---|---|---|
| #1 independent-validator wording | important | pass: one documentation file | pass: no new invariant | pass: same separate-worker behavior | pass: no schema | shared | T-06-fix-independent-validator-wording |

## Deferred

- [source: issues] Optional guide-example predicate precision: compare untouched example regions byte-for-byte rather than line-prefix matching. The product updater already has exact byte-preservation tests; this is not an unmet requirement or product defect.

## Spec Sync
sync: complete
synced_at: 2026-10-28
deltas: 1 (implemented-differently: 1, not-implemented: 0, implemented-beyond: 0)
spec: .ai/specs/completed/04-model-catalog-cache.md

Only dependency sequencing is clarified: owner-selected delivery uses explicit current-invocation capability input before the broader harness migration. All eight requirements and all five acceptance statements remain unchanged. All five acceptance boxes are marked verified. Source: Task Analysis/Assumptions and Solution Design/Scope; ADR-0015 corroborates. Optional deferred fixture precision is not a requirement divergence.

## Final Validation

- Source tip: 41b627cb8910570178a32e587bf11d2ba67f84d5; all six branches reconcile to protected recorded tips.
- Full clean-checkout regression: 594 passed, 0 failed, 2 optional private-pattern skips; exit0. Output: /tmp/model-catalog-final-41b627c-validation.txt.
- Focused: 87 model tests plus unchanged general instruction checks; all frozen methods/repair bytes preserved.
- Independent contract: 21 pass, 0 fail, 0 critical. Final review: 0 open critical, 0 open important, 1 optional deferred; one approved validation fix completed and independently reviewed.
- Selector: 1,017 words. 100 isolated warm fixture lookups below one second. Live 60-second selection target and model savings remain unmeasured.
- Syntax, annotations/function bounds and scoped whitespace pass. shellcheck unavailable; no standalone type checker configured. Global deployment remains outside scope.
- No .ai/ paths staged or committed. The 17 unrelated user-edited later specs remain byte-identical to their preservation snapshot.
- Logging skipped: ORCHESTRAIL_HOME unset. No historical store/provider/paid comparison/production-default change performed.

## Finalization Decisions

| File | Decision | Reason |
|---|---|---|
| .ai/memory/architecture.md | updated | Optional helper modules, canonical resolution, installed guidance and independent-worker boundaries now exist. |
| .ai/context/runbook.md | updated | Focused offline gates and temporary installed-layout coverage. |
| .ai/principles/architecture.md | skipped | Existing additive/optional-runtime/single-writer principles apply unchanged. |
| .ai/principles/coding.md and domain.md | skipped | No new project-wide standard or domain rule required. |
| .ai/project_state.md | skipped | File absent. |
| .ai/adr/0015-task-04-cached-model-selection.md | accepted in place | Existing provisional record promoted after final verification; no duplicate ADR. |
| .ai/adr/index.md | updated | Existing record status/date accepted. |
| .ai/specs/completed/04-model-catalog-cache.md | completed and reconciled | Completion marker, verified acceptance and attributable dependency clarification only. |
| .ai/specs/README.md | updated | Catalog delivery no longer described as pending. |

All deferred scope is optional example-verification precision; no original subtask or acceptance criterion is deferred. No additional architectural record is owed. Shared state compression preserves phase, contract, TDD, archive and Git audit fields. All six PRs were promoted sequentially to ready for review with verified unchanged head hashes. None was merged.

## Promotion

All six PRs are ready for review; remote head hashes match the recorded branch tips. Merge order: #31 → #32 → #33 → #34 → #35 → #36. Bases form the recorded linear stack. No merge, force push, branch deletion or base push occurred. Commit hashes are pre-merge; use restack after partial squash/rebase integration. Final task artifact validation passes21/0/0.

## Owner-authorized Integration

Date: 2026-10-28.
Authorization: the owner explicitly requested fresh independent validation/review of every PR, autonomous repair of findings and merge after successful revalidation. This later direct instruction authorizes integration despite the earlier skill's no-merge rail. No force push, direct base push, branch deletion, deployment or unrelated-file change is authorized or planned.

Review scope: PRs #31–#36 and combined tip 41b627cb8910570178a32e587bf11d2ba67f84d5. A fresh independent lead and two fresh bounded subreviewers inspect original contracts and current diffs without implementation reports. The lead owns a new full offline regression in a clean detached checkout. Primary workspace state and the17 unrelated later specifications remain preserved.

Integration policy: use merge commits with expected head hashes, in dependency order. After each successful merge, verify the remote merge result/tree and retarget the next stacked PR to main if needed. Never overwrite unexpected concurrent changes. All repair commits require independent verification before integration. No user decision is needed for routine technical remediation already authorized.

Status: fresh independent full regression completed successfully (exit0): 594 passed, 0 failed, 2 optional private-hygiene skips. All six exact reviewed heads receive PASS and a merge recommendation; no repair required. Owner-authorized integration is complete at main 111455ac171c7356d083e00d4d307a7285ed2e35.

Full-run evidence SHA256: cb3fa84d1308c4896c14cd1deb63ba7c2ca1847a8013d0c5d0baabc1008187a1. Terminal result: All required contracts valid. Reviewed source tree: 1c559bb77f26fcfeb4481c586e2ea553086575c2.

Fresh review evidence: 20 independent bounded probes pass across helpers, archives and workflow consumers. Five original RED checkpoints fail for their intended missing behavior and pass with the final product files. Python syntax, shell syntax, frozen-test preservation and whitespace pass. No required repair is identified. The guide preservation flag is accurate for its actual fixture; its weaker future regression oracle and unsupported HTML-commented plan tables are nonblocking limitations, not unmet contract behavior. Full-run output: /tmp/catalog-independent-pr-full.txt. RED evidence: /tmp/catalog-independent-red-probes.txt.

Integration: PR #31 merged into main at f79a4101d2ee7a6f2aecccbfab692613674c3767; exact expected parents and reviewed tree 41f26ef139c7e42f8db393a33348cdabb934c932 verified. Owner specifications preserved.

Integration: PR #32 merged into main at b65f7039e48e6a1a6c9bbd5f39149e2e71c30d85; exact expected parents and reviewed tree b839d8551977a6c35f98dab90468a641da63e0e9 verified. Owner specifications preserved.

Integration: PR #33 merged into main at 2bc6268b160167dede5e189d10ffce1bb452f3de; exact expected parents and reviewed tree 8fda0ea45951557a1720acec3324eac2423e5b78 verified. Owner specifications preserved.

Integration: PR #34 merged into main at 5453f1eaf5ab4536a3266fa66309b2ed18aaa322; exact expected parents and reviewed tree 2015880d20d4184d1076b26310bb70e42f910ccd verified. Owner specifications preserved.

Integration: PR #35 merged into main at 2c986b7544024f7047206876405aef7a7f36efba; exact expected parents and reviewed tree c634d526acbd57cbe0b57329ef8cb670c50bb1f9 verified. Owner specifications preserved.

Integration: PR #36 merged into main at 111455ac171c7356d083e00d4d307a7285ed2e35; exact expected parents and reviewed tree 1c559bb77f26fcfeb4481c586e2ea553086575c2 verified. Owner specifications preserved.

### Integration Completion

All PRs #31–#36 are closed and merged into main, in dependency order with merge commits. The fresh independent post-integration audit confirms every expected pair of parents, every reviewed head retained in ancestry, and final tree 1c559bb77f26fcfeb4481c586e2ea553086575c2 exactly equal to reviewed 41b627c. The 594/0/2 full validation applies to this identical tree; no redundant full rerun is needed. No new repair was required.

Local main and origin/main both equal 111455ac171c7356d083e00d4d307a7285ed2e35. All95 local knowledge files survived the branch switch byte-for-byte; the17 unrelated owner-edited specifications remain identical to their preservation snapshot. No product changes remain unstaged, no paths are staged, and no .ai/ changes were committed. No direct main push, force push, rebase, branch deletion or deployment occurred. The earlier ready/unmerged statements are historical pre-integration evidence; this section records the current merged outcome. Optional future fixture-oracle precision remains nonblocking and is not an unfulfilled acceptance criterion.
