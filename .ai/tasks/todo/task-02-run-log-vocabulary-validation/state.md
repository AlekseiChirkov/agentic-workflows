spec_path: .ai/specs/02-run-log-vocabulary-validation.md
flow: full

## Phases
- discovery: complete
- execution: complete
- validation: in-progress

## Task Analysis
→ archived to state-archive.md

### Assumptions
- arbiter: exact known helper-option tokens retain option semantics; other dash-leading operand text is preserved, and unknown tokens in option position remain rejected. Existing documented flags and unrestricted flow require this distinction; no new literal-option escape syntax is introduced (rules/run-log.md:81, workflows/spec-run.md:41, spec field-presence rules and missing-operand rule).
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
  pr: #13 draft
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

T-02 | read-only-run-linter | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/run-log-lint
  base_branch: feat/run-log-producer-validation
  base_commit: 872538e2ea3c28faf0f296c9979fa01d6b6d76ae
  commits: 93c985c test: cover read-only lint diagnostics and selection; 610e097 feat: lint historical records without changing files
  pr: #14 draft
  last_action: DoD met — independent read-only lint review complete; selectors, strict JSON, exact numbers, diagnostics, coverage, and preservation pass
  target_files: `scripts/log-step.sh`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Depends on T-01 to reuse its runtime vocabulary; edits the same helper after producer behavior.
         tdd: smoke — 4 tests, AC coverage 4/4; isolated extracted validate-contracts smoke group executed before implementation.
         tdd: red digest — AC-1 → test_run_log_lint_selects_files_and_preserves_storage; AC-2 → test_run_log_lint_emits_ordered_redacted_diagnostics, test_run_log_lint_validates_fields_and_shared_vocabulary; AC-3 → test_run_log_lint_reports_unavailable_and_partial_checks, test_run_log_lint_emits_ordered_redacted_diagnostics; AC-4 → test_run_log_lint_selects_files_and_preserves_storage.
         tdd: RED reason — every function expects the mandatory summary and receives empty stdout with the existing unknown-command warning; no implementation changed. Paused for orchestrator test-only commit.
         implementation: read-only selection and physical-line JSON validation added; field enums/count keys/bound come directly from RUN_LOG_CONTRACT, with no independent vocabulary or producer changes.
         tdd: added during GREEN — wrong-type event values, inaccessible corpus directory, and jq runtime failure after successful startup probe.
         tdd: test amended — test_contract_version_rule_history_warns_until_version_changes — removed an accidental duplicate lint-test insertion inside its Python marker string; the original test logic and all four actual frozen lint functions/assertions remain unchanged.
         verification: first full suite 561 passed, 1 failed, 2 configured skips; failure was the accidental fixture-string insertion above, now repaired. Stable repeat pending after raw-NUL implementation correction.
         tdd: added during GREEN — literal raw NUL inside a JSON string must produce invalid-json; jq raw-line encoding preserves physical line bytes before shell handling and catches file-read failures.
         verification: corrected raw-NUL implementation and fixture passed the complete suite: 562 passed, 0 failed, 2 configured hygiene skips. A subsequent numeric precision correction requires the final stable repeat below.
         tdd: test amended — test_run_log_lint_validates_fields_and_shared_vocabulary — transient GREEN cases expecting mathematically integral 1.0/exponent values to be invalid were corrected per spec sections 1 and 5: strict spelling applies to CLI arguments, while historical JSON checks numeric integrality and bounds. Original frozen matrix unchanged.
         implementation: raw JSON numeric tokens retain precision independently of jq number representation; bounded decimal-scale normalization compares exact integral values to the shared maximum without allocating exponent-sized strings. Equivalent integral forms and negative zero remain valid.
         tdd: added during GREEN — decimal/exponent integral equivalents, exact maximum equivalents, near-bound fractional values, huge positive/negative exponents including zero, and broken selected symlinks.
         tdd: green — all 4 frozen RED functions pass; original names/cases/assertions preserved, with additional raw-byte, numeric-precision, and access-error coverage.
         verification: final stable complete suite 562 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n and git diff --check passes; shellcheck unavailable. Evidence: /tmp/orchestrail-lint-verified.log.
         finalization: orchestrated mode; return plan transition T-02 to done and helper architecture/interface delta to sole shared-file writer. No deployment, git writes, log calls, historical rewrites, or shared-file edits performed.
         architecture.md: interface update returned to orchestrator — helper adds lint selectors, redacted violation records, and ok/partial/unavailable summaries; lint alone requires jq, while producer dependencies and behavior are preserved.
         compression: protected TDD/git evidence retained; corrected prior failures remain historical verification notes; no other sections changed and no further compression needed.
         repair: direct orchestrator check found jq accepts non-JSON numeric extensions (leading-zero, plus-prefixed, incomplete fractional, NaN/Infinity); strict raw token coverage now rejects these as invalid-json anywhere in a record, including unrestricted optional nested fields. Valid integral decimal/exponent spellings remain accepted.
         tdd: added during GREEN — malformed numeric token syntax in nested optional fields, with exact invalid-json diagnostics and counts; all four frozen functions pass.
         verification-final: after strict JSON grammar repair, stable complete suite 562 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n and git diff --check passes; shellcheck unavailable. Evidence: /tmp/orchestrail-lint-verified.log.
         finalization-final: all 4 frozen tests GREEN; no weakened assertions or removed actual test functions; prior accidental fixture duplication removed with amendment record. Return plan T-02 -> done and architecture interface delta to orchestrator; shared files remain under its ownership.
         compression-final: current completion recorded; prior repair history and protected TDD/git evidence retained; no further compression needed within owned block.
         validation: independent pav-check DONE; all four acceptance criteria met: selectors and no-match/empty storage, safe ordered physical-line diagnostics, accurate examined/distinct/violation counts with honest coverage, zero exit and byte-preserving read-only operation.
         validation: all four frozen lint functions independently pass; comparison with test-only commit 93c985c shows original names, cases, and assertions intact and only added coverage. Recorded fixture and numeric expectation amendments identify test defects; no unexplained skips or weakening.
         validation: independent 86-case Decimal differential confirms exact numeric bounds and integrality; a runtime jq failure on the second physical line returns partial with one examined file/line and exactly one summary. Strict JSON, raw NUL, non-object, alias/type/enum/count, access-error, and final-no-newline cases pass.
         validation: stable complete-suite artifact /tmp/orchestrail-lint-verified.log reports 562 passed, 0 failed, 2 configured hygiene skips; all scripts independently pass bash -n; shellcheck unavailable. Exact helper diff preserves producer implementation and optional-jq paths.
         proposals: batch review — Do Now: none; Do Later: add a permanent mid-file jq runtime-failure fixture to the planned isolated acceptance harness, asserting retained examined counts and partial status after one successful line; independent direct check passes. Optional: none. Shared proposal section returned to orchestrator; nothing applied.
         closure: orchestrated pav-close complete; return plan delta T-02 -> reviewed to the sole shared-plan writer. No child composite trigger applies. No implementation, tests, git, shared memory, plan, or historical logs changed.
         compression: auto audit retains protected notes, test/git history, and earlier repair evidence; no further compression needed within owned block and no shared sections edited.

T-03 | lint-aware-retrospective | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/lint-aware-retrospective
  base_branch: feat/run-log-lint
  base_commit: 4e0b7f85b1eb94272caafdccc5afc3eea4062b87
  commits: f096c89 test: cover filtered lint coverage and usable metrics; a799dbc feat: report lint coverage and exclude unusable telemetry
  pr: #15 draft
  last_action: DoD met — independent lint-aware retrospective validation complete; filtered coverage, usable denominators, and physical close classification reviewed
  target_files: `workflows/retro.md`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Depends on the linter's stable diagnostics and summary contract.

         tdd: contract, smoke — 4 functions, AC coverage 4/4; isolated executable loader scenarios use temporary stores, no historical records.
         tdd: red digest — AC-1 → test_retro_filters_intersect_exact_selected_corpus; AC-2 → test_retro_empty_and_invalid_corpora_report_safe_counts, test_retro_incomplete_lint_never_implies_clean_measurements; AC-3 → test_retro_invalid_records_never_enter_metric_observations, test_retro_incomplete_lint_never_implies_clean_measurements; AC-4 → test_retro_invalid_records_never_enter_metric_observations.
         tdd: RED observed — all four report "retro must provide an executable lint-aware corpus loader"; bash -n passes; no workflow edits. Paused for orchestrator test-only commit.
         tdd: test amended — test_retro_empty_and_invalid_corpora_report_safe_counts — malformed JSON diagnostics use the existing helper field name record; original line expectation misunderstood the stable linter interface; corrected before implementation.
         implementation: embedded loader uses lint --all, exact selected-file intersection after all filters and limit, safe grouped diagnostics, invalid-line exclusions, and conservative unverified coverage; snapshots detect changed stores; no helper or producer behavior changed.
         implementation: all metric families specify usable observation/run denominators, optional-field missingness, incomplete subtotal labels, physical abandonment vs unusable/unknown closes, and not-measurable outcomes; report template includes coverage and exclusions; below-five/honesty/recommendation-only behavior preserved.
         tdd: added during GREEN — execute the documented metric aggregation snippet against valid/invalid observations; preserve known diagnostics in partial coverage; active-store changes suppress all unverified metrics.
         verification: all four focused functions pass; frozen names and original assertions preserved, with added coverage only; bash -n passes for the modified validator. Full gate starting.
         tdd: added during GREEN — missing-jq startup still attempts lint --all, reports unavailable without guessed corpus counts or usable observations; no new runtime dependency.
         verification-final: stable complete suite 566 passed, 0 failed, 2 configured hygiene skips; all scripts and embedded Bash snippets pass bash -n; git diff --check passes; shellcheck unavailable. Evidence: /tmp/orchestrail-retro-verified.log.
         verification-final: comparison with test-only commit f096c89 shows 44 added test lines, zero removed lines; all 4 original functions, cases, and assertions preserved. No helper, acceptance-harness, historical log, deployment, or git mutation.
         architecture.md: existing retrospective reader interface updated; return delta to orchestrator for lint-aligned corpus/coverage and usable-observation reporting; no new module.
         finalization: orchestrated pae-finalize complete; return plan transition T-03 -> done, memory status delta, and architecture interface delta to the sole shared-file writer; atomic validation remains not-started for independent review.
         compression: audit limited to owned progress block; protected TDD/git evidence retained; prior pending verification is superseded by final result; no shared sections changed and no further compression needed.
         validation: independent pav-check DONE; AC-1 exact filter/limit diagnostic intersection, AC-2 corpus counts/grouping/safe examples/incomplete status, AC-3 usable-only numerators and denominators plus exclusion effects, and AC-4 absent physical close versus unusable close all met.
         validation: all four focused executable functions independently pass; frozen RED f096c89 audit has zero removed lines/assertions, later coverage is additive, and the pre-implementation invalid-JSON field amendment has its recorded test-defect reason. Tests assert observable results using isolated temporary stores, without skips or vacuous assertions.
         validation: independent targeted checks pass inclusive/combined filtering through the frozen suite, invalid dates/limits, newline-bearing file paths with safe JSON examples, invalid physical close exclusion, unreadable-file unknown closes, unavailable directory coverage, and unselectable-start disclosure; original below-five, honesty, recommendation-only, and raw-context restrictions preserved.
         validation: stable complete-suite evidence /tmp/orchestrail-retro-verified.log confirms 566 passed, 0 failed, 2 conditional hygiene skips; independently repeated focused tests and extra edge checks; all scripts and embedded Bash snippets pass bash -n; git diff --check passes; shellcheck unavailable.
         proposals: pav-propose --batch complete — Do Now: none; Do Later: none; Optional: add permanent executable cases for newline-bearing diagnostic paths and inaccessible runs directories. Independent direct checks pass both; fixtures would protect their safe rendering and unavailable-coverage disclosures. Shared proposal section returned to orchestrator; nothing applied.
         closure: orchestrated pav-close complete; return plan delta T-03 -> reviewed to sole shared-plan writer. No child composite trigger applies. No code, tests, git, shared memory, plan, historical logs, or deployment changes made by this review.
         compression: owned-block auto audit retained protected notes, TDD/git evidence, and all existing fields; no further compression needed; shared sections untouched.

T-04 | vocabulary-docs-and-drift-gate | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/run-log-contract-gate
  base_branch: feat/lint-aware-retrospective
  base_commit: 7531deed32d9187912bbf616d4186925999b4f32
  commits: 75703d6 test: cover contract documentation and bidirectional drift; 9aa0b36 feat: document the contract and reject vocabulary drift
  pr: #16 draft
  last_action: DoD met — independent contract documentation and bidirectional effective-runtime drift validation complete
  target_files: `rules/run-log.md`, `scripts/validate-contracts.sh`, `docs/USAGE.md`
  blocker: none
  notes: Compares documentation with the shared effective runtime definitions.
         tdd: contract/smoke — 3 tests, AC coverage 4/4; isolated validator group executed before implementation, all fail because --run-log-contract-only is not implemented.
         tdd: red digest — AC-1 → test_run_log_contract_documents_effective_runtime_tables; AC-2/AC-4 → test_run_log_contract_checks_shared_definitions_and_prefix_boundary; AC-3 → test_run_log_contract_rejects_bidirectional_vocabulary_drift.
         tdd: RED paused for orchestrator test-only commit; production files untouched.
         implementation: canonical JSON Markdown tables compare bidirectionally with the effective runtime contract export; dedicated focused mode shares the default gate; duplicate/missing rows, values, table headers, types, and prefix boundary semantics fail by field.
         verification: all 3 frozen focused checks pass, including exhaustive both-side mutations and real shared writer/lint enum consumption; no frozen test changes; stable full gate passed.
         verification: final stable full suite 570 passed, 0 failed, 2 configured hygiene skips; all scripts pass bash -n; git diff --check passes; shellcheck unavailable; evidence /tmp/orchestrail-contract-gate-verified.log.
         finalization: all four acceptance criteria pass the 3 frozen contract smoke functions; production helper, historical logs, retrospective behavior, and acceptance harness unchanged; VERSION remains 0.9.0.
         architecture.md: return interface/count delta to orchestrator — validator now includes a structured effective runtime drift gate and --run-log-contract-only; stable count 570 with 2 configured hygiene skips. Shared architecture and plan are not written by implementer.
         compression: own block retains protected TDD/git evidence and no stale progress; plan transition T-04 -> done returned to orchestrator under shared-file discipline.
         validation: independent pav-check DONE; AC-1 complete human enum/alias/count/presence/default/write/lint contract matches specification; AC-2 canonical JSON tables compare with helper export and explicit prefix-boundary probes; AC-3 both-side missing/extra/modified values fail by field with nonzero status; AC-4 writes/lint share effective runtime definitions.
         validation: all 3 frozen focused smoke functions independently pass; entire test block is byte-identical to test-only commit 75703d6, with no removed cases, weakened assertions, introduced skips, or unrecorded amendments. Tests use isolated temporary helpers and stores.
         validation: independent extra probes reject duplicate sections, missing headers/sections/tables, invalid JSON and boolean/null/mixed-array values, empty/duplicate runtime exports, and unexpected focused arguments. Focused real gate passes; all scripts pass bash -n and git diff --check passes.
         validation: stable full evidence /tmp/orchestrail-contract-gate-verified.log confirms 570 passed, 0 failed, 2 configured hygiene skips; default gate invokes the same comparison and preserves failure accounting. Delta contains only rule, validator, and usage wording; no helper, retrospective, historical-log, or acceptance-harness behavior changes.
         proposals: pav-propose --batch complete — Do Now: none; Do Later: none; Optional: none. No improvements with a concrete measurable effect found.
         closure: orchestrated pav-close complete; return plan delta T-04 -> reviewed to sole shared-plan writer. No composite trigger applies. No implementation, tests, git, shared memory, plan, historical logs, or deployment changes made by this review.
         compression: owned-block auto audit retains all protected TDD/git evidence and current fields; no stale content requires compression and no shared sections edited.

T-05 | isolated-acceptance-harness | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: chore/run-log-acceptance
  base_branch: feat/run-log-contract-gate
  base_commit: b1f07863269411eda18b5d43f5eb5a01a4f6110f
  commits: 8d8cf60 test: require isolated executable acceptance runner; 60d315c test: add isolated run-log acceptance harness
  pr: #17 draft
  last_action: DoD met — independent isolated-harness validation complete; all criteria, frozen-test integrity, cleanup, and preservation checks pass
  target_files: `scripts/validate-contracts.sh`, `tests/log-step.sh`
  blocker: none
  notes: Runs after all four behavior and contract subtasks are implemented.
         scope expansion: scripts/validate-contracts.sh test infrastructure is authorized for the harness meta check and permanent acceptance fixtures; production behavior and documentation remain off-limits.
         tdd: smoke — 1 failing meta check, AC coverage 3/3; scoped run returned AssertionError: missing executable isolated run-log harness; bash -n passes.
         tdd: red digest — AC-1 executable and complete coverage -> test_run_log_acceptance_harness_isolated_and_complete; AC-2 temporary isolated roots -> test_run_log_acceptance_harness_isolated_and_complete; AC-3 historical preservation and syntax -> test_run_log_acceptance_harness_isolated_and_complete, focused read-only checks and bash -n.
         checkpoint: paused before harness implementation for the orchestrator test-only commit; implementation resumed after the recorded checkpoint.
         implementation: tests/log-step.sh copies only helper, contract validator, canonical run-log rule, and workflows to a disposable checkout; inherited source/store roots are overridden before helper use; focused functions run in independent errexit-enabled Bash processes; EXIT/INT/TERM cleanup removes all fixtures.
         coverage: existing 20 focused functions and assertions retained; additive required-argument and fixed-clock timing function; empty/case/whitespace rejections, optional omission, all synthetic names, prior percent-flow compatibility, mid-file jq failure, newline diagnostic paths, inaccessible and absent stores, and per-operation SHA-256 preservation checks.
         verification: actual bash tests/log-step.sh passes 21 focused functions; frozen meta check passed relocation, hostile and absent inherited roots, assertion failure propagation, and interrupted cleanup; frozen source block byte-identical to RED commit; bash -n all scripts and harness and git diff --check pass; shellcheck unavailable.
         integration: disposable version-history validator excludes the acceptance-meta group alongside its existing focused-group exclusions to avoid running checks whose definitions were intentionally removed; all original version-history assertions retained.
         tdd: green — frozen acceptance meta check and all 21 focused functions pass; all original assertions retained; the intentional mutation fixture now explicitly requires a changed checksum snapshot while every read-only lint/retro operation requires preservation.
         verification-final: bash tests/log-step.sh passes 21/21; stable bash scripts/validate-contracts.sh passes 572 with 0 failures and 2 configured hygiene skips; evidence /tmp/run-log-acceptance-focused.log and /tmp/orchestrail-acceptance-verified.log; bash -n all scripts and harness, executable mode, and git diff --check pass; shellcheck unavailable.
         acceptance: all 3 criteria met — executable harness runs producer/lint/retro/drift coverage; all helper, workflow, log, and mutation fixtures are temporary; historical checksums are verified around read-only calls and shell syntax passes. Production behavior and documentation unchanged; no real run files read or modified.
         proposals resolved: permanent prior percent-flow metadata fixture with newline/literal escapes; jq failure after an examined physical line with retained partial counts; retro newline diagnostic path and inaccessible runs directory fixtures are covered and passing.
         finalization: orchestrated mode — return plan delta T-05 -> done and architecture entry for tests/log-step.sh to the sole shared-file writer; no direct plan or shared-memory edits.
         compression: own progress block audited; protected TDD/git evidence retained; no further compression or shared-file edits required.

         validation: independent pav-check DONE — all three acceptance criteria met; executable isolated harness passes all 21 focused functions; full suite passes 572 with 0 failures and 2 configured hygiene skips.
         validation: complete branch audit covers producer enums/aliases/counts, recovery and fixed-clock timing, flow/workflow membership, filesystem/no-jq failures, lint selection/diagnostics/availability, retrospective filters/metrics/closes, and bidirectional contract drift.
         validation: frozen RED acceptance meta block is byte-identical to test-only commit 8d8cf60 (SHA-256 5c5401c152d0875e72f84202abdc22f5a0d797038f74b7d7c9560c0786337a1f); original focused cases and assertions remain intact, with additive coverage and no skips, vacuous assertions, or weakening.
         validation: source review confirms every helper/workflow/log fixture is temporary; inherited source/store roots are overridden, copied-checkout relocation and hostile/absent inherited roots pass, and success/failure/TERM cleanup passes. Per-invocation checksums protect lint and retro reads; intentional mutation asserts a changed snapshot. No real run-store paths were opened by this review.
         validation: bash -n passes for all scripts and harness; git diff --check passes; executable mode is 100755; shellcheck unavailable. Independent evidence: /tmp/acceptance-independent-focused.log and /tmp/acceptance-independent-full.log. No critical or important findings.
         proposals: independent batch review — no concrete improvements with sufficient measurable effect found; Do Now, Do Later, and Optional are all none; no proposals applied.
         closure: orchestrated pav-close complete; plan delta T-05 -> reviewed returned to the sole shared-plan writer; no composite trigger applies. Source, tests, git, shared sections, plan, memory, installed skills, deployment, and real logs unchanged by this review.
         compression: auto audit of owned block retains protected TDD/git evidence and current findings; no shortening required. Shared execution-report status remains for the orchestrator to reconcile.

T-06 | fix-redact-unknown-command | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: fix/redact-unknown-command
  base_branch: chore/run-log-acceptance
  base_commit: 1081a29f62aefc79217089105da83695f57281c4
  commits: 8028790 test: cover redacted unknown-command errors; 9827a9d fix: redact unknown-command diagnostics
  pr: #18 draft
  last_action: DoD met — independent unknown-command redaction review complete; all 22 focused checks and 573 full-suite checks pass
  target_files: `scripts/log-step.sh`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Critical contract gate paused; repair authorized by user instruction to fix all findings.
         tdd: smoke — 1 new function, AC coverage 3/3; original producer functions and acceptance meta-test remain unchanged.
         tdd: red digest — AC-1 unknown command redaction, termination, and immutable storage; AC-2 preserved help and valid neighboring commands; AC-3 permanent dynamic harness coverage -> test_run_log_unknown_commands_are_redacted_and_preserve_storage.
         tdd: RED — focused function exits 1 because arbitrary command text and embedded control characters appear in stderr; exact newline reproduction yields two diagnostic lines; zero status, no stdout, help, valid neighboring commands, and temporary-storage hashes otherwise pass. Evidence: /tmp/orchestrail-unknown-command-red.log.
         tdd: GREEN — the single frozen RED function passes; all 28 unknown invocations preserve absent/populated fixture storage, return zero, emit no stdout, and produce the same single safe diagnostic. All help aliases and valid neighboring commands pass.
         implementation: replace only the final unknown-command dispatch diagnostic with constant command invalid-command; no parser, storage, vocabulary, or valid-command changes.
         verification: focused regression exit 0, evidence /tmp/orchestrail-unknown-command-green.log; executable isolated harness 22 passed, exit 0, evidence /tmp/orchestrail-unknown-command-acceptance.log; full suite 573 passed, 0 failed, 2 configured hygiene skips, evidence /tmp/orchestrail-unknown-command-full.log.
         verification: validator remains byte-for-byte equal to test-only commit 8028790; all scripts/*.sh and tests/*.sh pass bash -n; git diff --check passes; shellcheck unavailable. No test amendments or additional tests during GREEN.
         finalization: orchestrated mode; return plan transition T-06 -> done to the sole shared-plan writer. Architecture requires no update because the helper's existing nonblocking interface remains described. No git writes, deployment, historical-log access, shared plan, or memory edits performed.
         compression: owned block audited; protected TDD/git fields and current evidence retained; no shortening needed. Atomic validation remains pending independent review.
         validation: independent pav-check DONE — AC-1 met: 28 unknown invocations across absent/populated fixtures return zero with no stdout, one constant redacted stderr line, timeout protection, and unchanged storage; direct newline reproduction independently passes.
         validation: AC-2 met — missing/empty command and all help aliases retain identical output; valid producer, read-only path/active/contract/lint commands pass the unchanged focused checks; source diff changes only the final unknown-command diagnostic.
         validation: AC-3 met — dynamic executable harness permanently discovers the new regression and passes all 22 focused functions; independently repeated full suite passes 573 with 0 failures and 2 configured hygiene skips. Evidence: /tmp/unknown-command-independent-harness.log and /tmp/unknown-command-independent-full.log.
         validation: frozen RED validator is byte-identical to commit 8028790 (SHA-256 67de96a616ed99874a4da9ff9d1bdeaff0e77446e7d1b994a383a984140cb4cc); base diff adds one behavior-focused regression without changing earlier functions/assertions; no skips, vacuous assertions, or amendments. Independent frozen-helper replay reproduces original two-line disclosure.
         validation: all scripts and harness pass bash -n; git diff --check passes; shellcheck unavailable. Every executed helper uses temporary storage; no real logs accessed. No critical or important findings within this repair scope.
         proposals: independent batch review — no concrete improvements with sufficient measurable effect found; Do Now, Do Later, and Optional are all none; nothing applied.
         closure: orchestrated pav-close complete; return plan delta T-06 -> reviewed to the sole shared-plan writer; no composite trigger applies. No source, tests, git, shared sections, plan, memory, deployment, or real logs changed by this review.
         compression: auto audit of owned block retains protected TDD/git evidence and current validation results; no shortening required. Shared aggregate statuses remain for the orchestrator to reconcile.

T-07 | fix-path-argument-progress | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: fix/path-argument-progress
  base_branch: fix/redact-unknown-command
  base_commit: 6cc6e2bbcbd37371cfb7bb6fb181ef2477462bbd
  commits: 9af9998 test: cover malformed path arguments; 524785d fix: validate path arguments before lookup
  pr: #19 draft
  last_action: DoD met — independent bounded path parsing review complete; malformed calls terminate safely and valid reads preserve output and storage
  target_files: `scripts/log-step.sh`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Missing path operand causes an infinite loop; preserve successful path reads and reject malformed arguments without side effects.
         tdd: smoke — 1 new focused function, AC coverage 3/3; no production changes.
         tdd: red digest — AC-1 malformed argument termination, redaction, and storage hashes; AC-2 exact valid path output and read-only storage; AC-3 permanent producer-group function discovered by the executable harness -> test_run_log_path_arguments_terminate_safely_and_preserve_storage.
         tdd: RED — focused function fails as expected: missing operands time out after 1 second in both absent/populated stores; empty, duplicate and unknown arguments wrongly succeed with path output. Safe existing invalid-ID cases and valid neighboring reads pass. Evidence: /tmp/orchestrail-path-red.log. All fixture helper calls have timeouts; all storage is temporary.
         tdd: GREEN — frozen focused function passes all 42 malformed invocations across absent/populated stores, with zero exits, no stdout, exactly one safe stderr line, unchanged hashes, and exact valid path outputs. Evidence: /tmp/orchestrail-path-green.log.
         implementation: replace only cmd_path argument loop with a bounded zero-argument or --run-plus-ID grammar; validate the complete invocation and safe ID before metadata lookup.
         verification: focused regression exits 0; actual isolated harness passes all 23 focused functions, exit 0, evidence /tmp/orchestrail-path-acceptance.log; full suite passes 574 with 0 failures and 2 configured hygiene skips, exit 0, evidence /tmp/orchestrail-path-full.log.
         verification: validator is byte-identical to test-only commit 9af9998, SHA-256 bfa34d06ebd7f053eaa6013519a46f074131a2eab53ec009f7ba73105102ad7c; no test amendments or new tests during GREEN. All scripts/*.sh and tests/*.sh pass bash -n; git diff --check passes; shellcheck unavailable.
         finalization: orchestrated mode; return plan transition T-07 -> done to the sole shared-plan writer. Architecture requires no update because this restores the helper's existing bounded, nonblocking read interface. No git writes, deployment, historical-log access, shared-plan or memory edits performed.
         compression: auto audit of owned block retains protected TDD/git fields and current evidence; no shortening needed. Atomic validation remains pending independent review.
         validation: independent pav-check DONE — all three acceptance criteria met; the old base path --run times out under a 0.3-second bound, while the fixed invocation returns zero with no stdout, exactly one redacted diagnostic, and no absent-store creation.
         validation: frozen focused regression independently passes all 42 malformed cases across absent/populated storage, exact valid root/run output, complete storage hashes, and bounded calls. The actual disposable acceptance harness independently passes all 23 functions, exit zero.
         validation: frozen RED audit passes — the complete validator is byte-identical to test-only commit 9af9998, SHA-256 bfa34d06ebd7f053eaa6013519a46f074131a2eab53ec009f7ba73105102ad7c; all ACs map to the intact focused test, with behavior assertions, isolated fixtures, no skips and no vacuous assertions. Test-only commit precedes production commit 524785d.
         validation: inspected full-suite evidence /tmp/orchestrail-path-full.log confirms the new path check and 574 passed, 0 failed, 2 configured hygiene skips; full suite not repeated because the relevant source and frozen tests are unchanged. Independently repeated all scripts/tests bash -n and git diff --check; shellcheck unavailable.
         proposals: pav-propose --batch complete — no concrete improvements identified; no proposals section or implementation changes required.
         closure: orchestrated pav-close complete; return plan delta T-07 -> reviewed to sole shared-plan writer. No child composite trigger applies. Only this assigned progress block changed; no source, tests, git, shared-plan, memory, deployment, or historical-log writes.
         compression: auto audit retains protected TDD/git fields and current independent evidence; no stale or duplicate content within the owned block needs removal, and no shared sections edited.

T-08 | fix-run-log-input-boundaries | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: fix/run-log-input-boundaries
  base_branch: fix/path-argument-progress
  base_commit: 30df8979237dbb20728e7f404fcde242c47ba6df
  commits: 8a9c116 test: cover flag text and workflow access boundaries; 4986aee fix: preserve flag text and check workflow access
  pr: none
  last_action: DoD met — independent input and workflow-access boundary review complete; all criteria pass
  target_files: `scripts/log-step.sh`, `scripts/validate-contracts.sh`
  blocker: none
  notes: Two important findings share the quick-flow repair group: two files, no new invariant/schema, and both affected checks were introduced within this unmerged task. Existing fix directories are retained; new approved work is appended rather than recreating completed fixes.
         tdd: smoke — 2 tests; acceptance coverage 3/3, including permanent harness discovery and subsequent full/syntax verification.
         tdd: red digest — AC-1 -> test_run_log_dash_leading_operands_preserve_text_and_reject_known_options; AC-2 -> test_run_log_workflow_directory_permissions_report_verification_availability; AC-3 -> both focused tests registered in producer group for dynamic isolated harness/full-suite execution.
         red evidence: both tests exit 1 against unchanged helper SHA256 ae9749d8469c43c3390b8ce0bfc7d4952173e199d268272d9a42a44993a691ae; operand rejected dash-leading pipeline with missing-operand; real mode-0400 directory returned unknown-name instead of exact unavailable warning. Logs: /tmp/input-boundary-operands-red.log, /tmp/input-boundary-permissions-red.log; focused frozen definitions SHA256 4315e66ec31638d5aba649a3684543f65608d685537cccb7d39459d92617a0f6.
         implementation: existing event-specific option case is factored into event_option_allowed and reused to reject recognized options as operands across all producer events; unknown option-position tokens still reject. Workflow verification requires both read and search permission. No new vocabulary or escape syntax.
         green evidence: both frozen regressions exit 0; actual bash tests/log-step.sh exits 0 with 25/25 focused checks (/tmp/input-boundary-harness-green.log); bash scripts/validate-contracts.sh exits 0 with 576 passed, 0 failed, 2 configured private-hygiene skips (/tmp/input-boundary-full-green.log).
         checks: bash -n passes for every scripts/*.sh and tests/log-step.sh; git diff --check passes. Shellcheck unavailable. Frozen focused-definition SHA256 remains 4315e66ec31638d5aba649a3684543f65608d685537cccb7d39459d92617a0f6; validator SHA256 remains 9552f8889e72d8fe09fe7655dc0013f7f387a2117296cd3631800bcab38f8f12; repaired helper SHA256 b2a2bb34a2bcc6bce996a56754f6686eb8d5d0c91e8ebb9c513f6fb1395fda9c.
         permission evidence: UID 1000 actual Bash read/search probes and producer events pass modes 0700, 0400, 0100, 0000 plus missing directory. The permanent fixture drops groups/GID/UID in a child when root, but root branch was not executed here because sudo -n requires a password (/tmp/input-boundary-root-permissions.log); no claim of privileged validation.
         acceptance: AC-1 proved by frozen operand test; AC-2 by frozen permission test; AC-3 by 25-check actual isolated harness, 576-check full suite and syntax/whitespace gates. Existing rejection/critical repair regressions pass. All fixtures use disposable stores; no real logs, deployment, home, or git writes.
         finalization: architecture.md needs no update — no new module or public interface; existing helper component description remains accurate. Orchestrated shared-plan delta T-08 -> done returned to sole writer; no shared-plan/memory/architecture changes by implementer.
         compression: owned progress block audited; protected TDD/git fields retained and current evidence preserved. No stale or duplicate content requires removal; shared sections left to the orchestrator.
         validation: independent pav-check DONE — AC-1 met: documented flags and ordinary dash-leading flow/free text persist exactly; all 22 known helper options remain reserved across all three event parsers; unknown option-position tokens reject with exact redacted diagnostics and identical storage hashes.
         validation: AC-2 met — real UID 1000 read/search probes and actual event writes pass modes 0700, 0400, 0100, 0000 and missing-directory cases; known, synthetic and unknown names receive exact expected advisories and preserve event fields/sequence. Root-only child privilege-drop code reviewed; not executed in this environment, and no privileged access requested.
         validation: AC-3 met — independent actual isolated harness passes 25/25 (/tmp/input-boundary-independent-harness.log); all scripts and acceptance runner pass bash -n; git diff --check passes; shellcheck unavailable. Fresh supplied full-suite evidence /tmp/input-boundary-full-green.log confirms 576 passed, 0 failed, 2 configured private-hygiene skips and exact current helper/validator hashes.
         validation: frozen RED integrity verified — validator byte-identical to 8a9c116; baseline-to-RED adds 162 lines with zero removals; focused definition SHA256 remains 4315e66ec31638d5aba649a3684543f65608d685537cccb7d39459d92617a0f6. Both frozen functions independently fail baseline for the expected documented-text and mode-0400 warning defects, then pass current helper through the actual harness. No assertions weakened, skipped or amended.
         validation: architecture, coding, domain and TDD contracts respected; tests use isolated real storage and observable events/diagnostics without real historical-log reads. No critical, important or optional findings.
         proposals: batch review complete — no concrete improvements proposed; no changes applied.
         closure: orchestrated pav-close complete; return plan delta T-08 -> reviewed to sole shared-plan writer. No child composite trigger applies; no source, tests, shared plan/memory, git, deployment, home or historical-log changes by validator.
         compression: auto audit of owned progress block found current evidence and protected TDD/git fields intact; no stale or duplicate content removed; shared sections left unchanged.

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
- T-02: reviewed — read-only lint with exact record validation and honest coverage.
- T-03: reviewed — filtered lint coverage, usable metric observations, and honest close classification.
- T-04: reviewed — canonical vocabulary documentation and bidirectional structured drift gate.
- T-05: reviewed — isolated executable acceptance harness; 21 focused checks and cleanup meta check pass.
- T-06: reviewed — unknown-command diagnostics are redacted; 22 focused checks and full suite 573/0/2 pass.
- T-07: reviewed — bounded path parser rejects malformed arguments safely; 23 focused checks and full suite 574/0/2 pass.
- T-08: reviewed — documented dash-leading text persists and unsearchable workflows report verification unavailable; 25 focused checks pass.
- Verification: 576 passed, 0 failed, 2 configured hygiene skips; all 25 focused acceptance checks, shell syntax, and whitespace pass.
- Run logging skipped because no configured executable shared helper was available.

## Improvement Proposals (T-01)

### Optional
- Completed in the isolated acceptance harness: permanent earlier flow-encoding metadata fixture passes.

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

### Read-only lint

branch: feat/run-log-lint
expected_parent: 610e0971decd554a61a658a0f9b8e89c930eee39
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Lint-aware retrospective

branch: feat/lint-aware-retrospective
expected_parent: a799dbc094494ed3bd2a288f71c1ed035ec0d59c
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Canonical contract gate

branch: feat/run-log-contract-gate
expected_parent: 9aa0b360813c4ec2aace663055c1b2127fa2e598
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Isolated acceptance harness

branch: chore/run-log-acceptance
expected_parent: 60d315c11116fb109fd6b94c4b4338e160e769ef
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/architecture.md
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Redacted command errors

branch: fix/redact-unknown-command
expected_parent: 9827a9d98866ca9932e50725d9804d39c8d43363
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-06-fix-redact-unknown-command/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-07-fix-path-argument-progress/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Bounded path arguments

branch: fix/path-argument-progress
expected_parent: 524785d1ab7d608e75de8f7d0da422ffbd564b3c
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

### Preserved flag text and workflow access

branch: fix/run-log-input-boundaries
expected_parent: 4986aee238fd520a8db65f4eff1b245a59d1469e
allowed_scope: listed knowledge-base paths only
recorded_paths:
- .ai/memory/state.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/T-08-fix-run-log-input-boundaries/description.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/plan.md
- .ai/tasks/todo/task-02-run-log-vocabulary-validation/state.md

## Improvement Proposals (T-02)

### Do Later
- Completed in the isolated acceptance harness: mid-file jq failure reports partial status and retains examined counts.

## Improvement Proposals (T-03)

### Optional
- Completed in the isolated acceptance harness: newline-bearing diagnostic paths and inaccessible run directories pass.

## Execution Finalization

- All five leaf subtasks are reviewed; no blocked, deferred or unreached work and no composite reconciliation required.
- Root file decisions: architecture updated for producer/lint/retrospective/drift gate and the isolated acceptance runner; architecture principles unchanged because existing single-source and nonblocking boundaries remain; project_state skipped because absent.
- Compression audit: current progress and final aggregate evidence reconciled; protected git/TDD/arbiter records and archive references retained.
- Task/spec paths remain stable through review readiness; archive relocation follows integration rather than being inferred from completion (pv-finalize completion marker and spec-run no-merge boundary).

## Contract Check

Fresh independent verification of `65a6e68c3cdfa775a8ff7685e01203a3d83fe09c..30df897` on `fix/path-argument-progress`. The parent was validation-in-progress. The earlier critical stop is preserved as history by the sole shared-state writer; both original defects are now resolved.

Validation context loaded: project architecture and memory state, architecture/coding/domain principles, ADR index, runbook, task contract and specification, `rules/tdd.md`, and `principles/testing-standards.md`. Required implementation surfaces read: `scripts/log-step.sh`, relevant added gate/producer/lint/retrospective/harness sections of `scripts/validate-contracts.sh`, `tests/log-step.sh`, `rules/run-log.md`, `workflows/retro.md`, and the `docs/USAGE.md` delta.

Fresh evidence:

- `bash tests/log-step.sh`: exit 0, all 23 isolated checks pass; `/tmp/orchestrail-integrated-focused.log`.
- `bash scripts/validate-contracts.sh --run-log-contract-only`: exit 0, `run-log contract: pass`. The focused harness independently executes bidirectional drift mutations, each of which must return nonzero with a field-specific explanation.
- `bash -n scripts/log-step.sh scripts/validate-contracts.sh tests/log-step.sh`: exit 0.
- Full-suite evidence `/tmp/orchestrail-path-full.log`: 574 passed, 0 failed, 2 configured hygiene skips. Inspected; the complete suite was not repeated in this review because the 23 relevant checks and drift gate were independently executed against unchanged source.
- One extra isolated POSIX directory-access probe reproduced the acceptance gap described below.

All executed helper calls use temporary stores. This review neither read the real historical corpus nor changed project source, tests, shared state, git, installed skills, or deployment. Historical preservation is assessed from changed-file boundaries, operation ordering, and isolated checksum assertions, without claiming a real-corpus checksum audit.

### Invariants

| Invariant | Status |
|-----------|--------|
| A rejected event has no event-file or active-metadata side effects | PASS: complete producer argument validation precedes initialization, lookup-dependent writes, sequence increments and persistence. Producer/required-argument/repair tests compare full temporary-store hashes, including existing digests, and verify the next accepted sequence/duration. |
| Logging error paths return zero and emit no success-shaped output | PASS: producer persistence/fallback tests pass, unknown dispatch uses a constant redacted diagnostic, and the bounded path grammar fixes the former loop. The two repair tests exercise absent/populated stores with timeouts, exact safe stderr and empty failure stdout. |
| Runtime writes and lint use one effective vocabulary and mapping source | PASS: `RUN_LOG_CONTRACT` drives producer normalization, event-specific enums, counts and lint; the effective-definition mutation changes an enum and confirms both producer and lint honor it. |
| Lint is read-only, and retrospective metrics include only usable observations | PASS: lint never initializes storage or writes files; each fixture invocation compares checksums. Retrospective intersects diagnostics with exact selected paths and excludes invalid lines; incomplete coverage conservatively admits no records to metrics. Counter/test denominators and physical unusable closes are tested. |
| Existing historical logs remain byte-for-byte unchanged | PASS within the authorized review boundary: no historical-log path is changed in the aggregate diff; tests isolate stores and assert per-operation checksums; acceptance harness overrides inherited stores before helper calls. No historical repair/migration path was introduced. Real historical checksums were not read. |
| The contract validator remains a gate whose drift failures return nonzero | PASS: canonical gate passes independently; mutation tests independently require nonzero for removed, extra, changed and duplicate documentation/runtime values and mappings, including overbroad prefix semantics. |

### Parent Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| 1. Strict producer enums/counts, exact aliases and provenance, rejection before state changes | PASS: producer enum/count/alias/required-argument tests cover canonical values, exact aliases, ordered existing-note provenance, zero/boundary values, malformed counts, duplicate/unknown/missing arguments, and unchanged storage. |
| 2. Flow default, failed-start output and recoverable rejected closes | PASS: flow/persistence checks cover omitted/empty `unknown`, inherited unrestricted multiline flow, metadata text boundaries and legacy compatibility, failed-start empty stdout, rejected close preservation and later accepted close. |
| 3. Dynamic helper workflow membership and advisory behavior | FAIL (important): `check_step_name` tests directory existence and readability but omits search permission. A readable directory without execute permission causes a current known workflow to receive the unknown-name warning instead of the required verification-unavailable warning. The valid event still persists. See reproduction below. |
| 4. Lint selectors, safe ordered JSON diagnostics, exact summary and partial coverage | PASS: all four lint checks cover selectors, active/closed matching files, no-match/empty corpus, strict physical-line JSON, exact bounded integral forms, safe stable diagnostics and distinct invalid-line counts, missing/broken jq, inaccessible files/directories, broken links and mid-file checker failure; hashes remain unchanged. |
| 5. Filtered retrospective diagnostics and honest usable metrics/close classification | PASS: executable loader tests exercise individual and combined filters plus limit, exact file intersection, invalid-line exclusions, optional-counter/test denominators, unavailable/partial/changing stores, lower bounds and invalid physical closes distinct from abandonment. Prose applies eligibility rules to all metric tables and retains recommendation-only behavior. |
| 6. Exact documentation and bidirectional effective drift gate | PASS: canonical JSON tables match the shared export; all removed/extra/changed/duplicate values and mappings are tested on each side; equivalent overbroad prefix mutations still fail the semantic boundary probe. Presence rules, numeric syntax/bounds and lint contract are documented. |
| 7. Executable isolated acceptance harness and historical preservation | PASS: executable runner copies source into a disposable checkout, sets temporary helper/log/workflow roots before invocation, runs each discovered check in a fresh errexit shell and cleans scratch on exit/signals. The focused 23-check run passes; the full-suite meta-test additionally verifies hostile inherited stores, failure propagation and interrupted cleanup. |
| 8. Required acceptance commands and shell syntax pass | PASS: actual isolated harness and changed-script syntax independently pass; inspected fresh full-suite evidence is 574/0/2. No new source changes intervene. |

### Specification Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| 1. Four outcome and three gate legacy cases with deterministic provenance | PASS: exact normalization tests cover every mapping, both aliases in one event, existing notes, unmapped lookalikes, whitespace/punctuation boundary cases and canonical no-provenance behavior. |
| 2. Exact event-specific enums, pinned tests and bounded integer syntax | PASS: complete producer matrix and lint field matrix cover the prescribed values and rejected spellings; malformed arguments write nothing. |
| 3. Missing/empty start flow becomes inherited `unknown` | PASS: flow tests cover omitted and explicit empty start flow across start, step and close, plus unrestricted nonempty flow preservation. |
| 4. Invalid invocation warns once, exits zero, leaves accepted state unchanged | PASS: producer validation, required arguments and both dedicated repair regressions pass exact stderr/stdout/status and checksum assertions. The old unknown-command disclosure and missing-path loop are resolved. |
| 5. Failed starts print no ID; rejected end can close later; errors do not block | PASS: persistence tests cover blocked/unwritable storage, no-jq fallback, missing event files, rejected then valid end and digest failure after a persisted close. |
| 6. Current/synthetic/advisory step membership and unavailable directory warning | FAIL (important): unavailable membership is misclassified when the workflows directory has read permission but lacks search permission. Ordinary current/synthetic/unknown/missing-directory fixtures pass. |
| 7. Read-only lint selectors, stable diagnostics and accurate summary | PASS: all four lint acceptance functions independently pass, including file/line ordering, distinct-invalid-line counts and coverage failures. |
| 8. Filtered retrospective invalid-row reporting and usable denominators | PASS: all four retrospective executable scenarios independently pass; guidance states excluded/missing observation denominators and physical close rules. |
| 9. Exact rule documentation and enum/mapping drift detection both ways | PASS: independent gate and all contract mutation scenarios pass; no separate lint vocabulary exists. |
| 10. Executable isolated harness with specified behavior/checksum fixtures | PASS: actual 23-check runner passes, covers the enumerated scenario categories, never depends on the actual historical corpus and preserves fixture hashes. Add the unsearchable-directory case when repairing criterion 6. |
| 11. Required harness/full-contract/syntax commands succeed without real-log dependence | PASS: harness and syntax independently pass; full command evidence is 574/0/2. The harness and relevant full-suite fixtures redirect helper/store choices into disposable paths. |

### Off-limits

Five parent bullets are represented as six checks by splitting the combined raw-diagnostics/single-source bullet.

| Constraint | Status |
|------------|--------|
| Do not rewrite historical logs or change checksums | PASS: aggregate file scope excludes logs; read-only operations and temporary fixtures preserve checksum snapshots. No actual historical logs were accessed in this review. |
| Do not make writing depend on jq | PASS: shell-only JSON fallback remains; missing-jq writes persist correctly, while lint reports unavailable honestly. |
| Do not let invalid events advance accepted sequence/timestamp/digest/active state | PASS: validation precedes writes and accepted-event progression; comprehensive full-store hashes and deterministic-clock regression pass. |
| Do not echo arbitrary raw values in diagnostics | PASS: producer/parser messages use fixed field/reason tokens; lint serializes paths/coordinates without field values; unknown-command regression verifies raw control-character text never enters stderr. |
| Do not introduce independent runtime vocabulary definitions | PASS: producer and lint consume `RUN_LOG_CONTRACT`; documentation is canonical comparable data and the gate compares its complete key/value set. |
| Do not block callers or make retro automatically edit implementation | PASS: the two former critical failures are repaired; bounded argument parsing, zero-exit error paths and persistence tests pass. Retro still explicitly recommends and stops without applying changes. |

### Original Critical Failures Recheck

- Unknown command redaction: RESOLVED. The current final dispatch emits `log-step: command invalid-command` regardless of input; the 28-case frozen regression passes.
- Missing path operand loop: RESOLVED. The current parser validates complete argument cardinality before lookup and returns safely on missing operands; the 42-case frozen regression passes.

### Remaining Acceptance Failure Reproduction

**important — unavailable workflow membership is reported as an unknown step**, `scripts/log-step.sh:251`.

Reproduce as an ordinary user in isolated storage:

```python
from pathlib import Path
import os, subprocess, tempfile
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    workflows = root / 'home' / 'workflows'
    workflows.mkdir(parents=True)
    (workflows / 'known.md').write_text('Fixture workflow\n')
    env = dict(os.environ, ORCHESTRAIL_HOME=str(workflows.parent),
               ORCHESTRAIL_LOG_ROOT=str(root / 'store'))
    helper = str(Path('scripts/log-step.sh').resolve())
    run = subprocess.run(['bash', helper, 'run-start', '--pipeline', 'fixture'],
                         env=env, capture_output=True, text=True).stdout.strip()
    workflows.chmod(0o400)
    try:
        result = subprocess.run(['bash', helper, 'step', '--run', run,
                                 '--step', 'known', '--outcome', 'ok'],
                                env=env, capture_output=True, text=True)
        print(result.returncode, repr(result.stdout), repr(result.stderr))
    finally:
        workflows.chmod(0o700)
```

Actual: exit 0, empty stdout, `log-step: step name is not in the current workflow list\n`; event persisted.
Expected: exit 0, event persisted unchanged, exactly one `log-step: step-name verification unavailable\n` advisory because directory entries cannot be searched. Add `-x` to the directory availability condition and a regression fixture for readable-but-unsearchable workflow directories. The existing missing-directory test does not cover this permission combination.

Step 1 (Contract Verification) complete: **29 PASS, 2 FAIL, 0 critical failures**, across 6 invariants, 8 parent criteria, 11 specification criteria and 6 off-limits checks. Both failed entries describe the same important defect. No critical stop is needed. Root must apply this delta and reconcile the historical `pause` field before code review begins.

## Issue List

### Approved
1. critical — fixed and independently reviewed: unknown-command diagnostic included arbitrary caller text and could span multiple physical lines.
2. critical — fixed and independently reviewed: path --run with a missing operand looped forever instead of returning nonblocking diagnostic output.
3. important — fixed and independently reviewed: readable but unsearchable workflow directory now reports verification unavailable.
4. important — fixed and independently reviewed: documented workflow flags and ordinary dash-leading text persist; known helper options remain reserved.

### Deferred
(none)

## Fix-Tasks
fixes-created: complete
fixes-count: 3
Created: T-06-fix-redact-unknown-command, T-07-fix-path-argument-progress, T-08-fix-run-log-input-boundaries

### Fix Classification

| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|---|---|---|---|---|---|---|---|
| #1 unknown-command diagnostic | critical | pass | pass | fail | pass | dedicated | T-06-fix-redact-unknown-command |
| #2 path argument progress | critical | pass | pass | fail | pass | dedicated | T-07-fix-path-argument-progress |
| #3 workflow directory searchability | important | pass | pass | pass | pass | shared | T-08-fix-run-log-input-boundaries |
| #4 dash-leading operand preservation | important | pass | pass | pass | pass | shared | T-08-fix-run-log-input-boundaries |

## Validation History

- The initial integrated contract gate paused on raw unknown-command diagnostics and a missing-path-operand loop. The owner's standing instruction to fix all findings authorized dedicated repairs. Both are independently reviewed and the fresh contract check resolves all critical failures; the historical pause no longer applies to the active check.

## Code Review

Independent whole-change review of `65a6e68c3cdfa775a8ff7685e01203a3d83fe09c..30df897` on `fix/path-argument-progress`.

Guard satisfied: the sole shared-state writer applied the fresh Contract Check, moved the original critical pause into Validation History, and left active invariants/off-limits passing before authorizing this step. Validation remains in progress. The decision remains the helper-owned structured contract, shared by writes and lint and compared with canonical documentation.

Validation context loaded: architecture, memory state, architecture/coding/domain principles, ADR index, runbook, task/spec contracts, `rules/tdd.md` and `principles/testing-standards.md`. Reused the completed bootstrap without redundant rereads, then inspected the current active guard and source. No project writes, git changes, deployment, installed-skill changes or real-log access occurred.

### Findings

1. **important — documented flag telemetry prevents starting a run**, `scripts/log-step.sh:126`; affected documented callers include `rules/run-log.md:81` and `workflows/spec-run.md:41`.

   `parse_arguments` treats every operand beginning with `--` as a missing operand, regardless of which option receives it. The documented `--flags "--step-by-step"` and actual spec-run flag text therefore cause the entire otherwise valid run-start to be rejected. The same check rejects unrestricted nonempty flow labels such as `--custom-flow`, and similarly restricts other free text. This is a regression from the existing free-text interface; it can silently remove complete runs from telemetry for workflows that have flags in force.

   Reproduce with an absent temporary log root:

   ```bash
   scratch=$(mktemp -d)
   ORCHESTRAIL_LOG_ROOT="$scratch/store" bash scripts/log-step.sh run-start \
     --pipeline phase-discovery --flags '--step-by-step'
   rm -rf "$scratch"
   ```

   Actual: exit 0, empty stdout, one `log-step: run-start flags missing-operand` warning and no store/run. Repeated independently with `--flags '--allow-pr --dry-run'` gives the same result. `--flow '--custom-flow'` similarly produces `log-step: run-start flow missing-operand` and no run.

   Expected: documented flag text is retained as supplied and the start persists, with a usable ID; nonempty unrestricted flow labels are preserved through start/step/end. Missing operands must still be rejected without consuming the next helper option. Repair the argument grammar and its documented caller syntax together as needed, preserving supported callers and the rejection safety boundary. Add behavior tests for the exact documented flag examples and dash-leading free text; the existing missing-operand, unknown-argument and no-side-effect assertions must remain intact.

2. **important — inaccessible workflow verification is misreported as unknown membership**, `scripts/log-step.sh:251`; missing regression in `scripts/validate-contracts.sh:2335`.

   The directory check tests existence/read permission without testing search permission. With a readable but unsearchable workflows directory, Bash can list names but `-f` cannot inspect their entries. A current known workflow is then reported as an unknown step. The event is correctly persisted and the message remains safe, but the specified unavailable-verification behavior is violated. This is the same issue already recorded in parent acceptance criterion 3 and specification criterion 6, not an additional distinct contract defect.

   Exact isolated reproduction as an ordinary user:

   ```python
   from pathlib import Path
   import os, subprocess, tempfile
   with tempfile.TemporaryDirectory() as temporary:
       root = Path(temporary)
       workflows = root / 'home' / 'workflows'
       workflows.mkdir(parents=True)
       (workflows / 'known.md').write_text('Fixture workflow\n')
       env = dict(os.environ, ORCHESTRAIL_HOME=str(workflows.parent),
                  ORCHESTRAIL_LOG_ROOT=str(root / 'store'))
       helper = str(Path('scripts/log-step.sh').resolve())
       run = subprocess.run(['bash', helper, 'run-start', '--pipeline', 'fixture'],
                            env=env, capture_output=True, text=True).stdout.strip()
       workflows.chmod(0o400)  # readable directory, no execute/search permission
       try:
           result = subprocess.run(['bash', helper, 'step', '--run', run,
                                    '--step', 'known', '--outcome', 'ok'],
                                   env=env, capture_output=True, text=True)
           print(result.returncode, repr(result.stdout), repr(result.stderr))
       finally:
           workflows.chmod(0o700)
   ```

   Actual: exit 0, empty stdout, `log-step: step name is not in the current workflow list\n`; the step persists. Expected: one `log-step: step-name verification unavailable\n` warning and the same persisted step. Require directory search permission alongside readability and add a mode-0400 fixture; preserve known/synthetic/unknown/missing-directory cases.

### Review Coverage

- **Architecture and clarity:** one readonly `RUN_LOG_CONTRACT` drives normalization, enums and numeric bounds; lint receives those definitions rather than maintaining another vocabulary. Canonical table comparison is field-specific and bidirectional, with explicit prefix-boundary probes. Metadata escaping preserves text boundaries without evaluating caller values. No new runtime module/dependency was added to the producer.
- **Security and errors:** safe eight-hex IDs precede metadata lookup; caller values are not sourced/evaluated; JSON strings escape controls; rejected complete producer arguments precede mutations. New dispatch redaction and bounded path parsing resolve the original critical defects. Lint reports paths through JSON and excludes raw field values. Read/write failures remain nonblocking, and partial OS writes/locking remain outside the requested redesign.
- **Lint edge cases:** reviewed raw-physical-line handling, literal NUL detection, malformed JSON numeric extensions, exact numeric lexeme validation above jq precision, huge exponents, negative zero, final missing newline, empty/no-match corpora, inaccessible/broken selected paths, initial and mid-file tool failures, and distinct line/violation counts. The four executable lint scenarios pass independently with checksum assertions.
- **Retrospective honesty:** reviewed exact selected-path intersection, all filters before filename limit, invalid-row exclusion, conservative exclusion of all unverified observations, known lower bounds, affected-run labels, usable counter/test/duration denominators, physical invalid close versus abandonment, unreadable close status and selection limitations. Guidance retains small-corpus warnings, raw-context restrictions, missing measurements and recommendation-only operation. The four executable scenarios pass independently.
- **Test integrity:** all seven leaves have actual smoke tests; no unjustified `n-a` exemption exists. Independent frozen comparisons retain all original lines of the five producer functions from `6b7b548`, four lint functions from `93c985c`, three contract functions from `75703d6`, and the acceptance meta-test from `8d8cf60`. The retrospective frozen block from `f096c89` removes only `def load(**filters):`, replacing it with `def load(expect_mutation=False, **filters):` to add explicit intentional-mutation verification; no original assertion/case is removed. The current complete validator is byte-identical to the final repair RED commit `9af9998`; the preceding unknown-command regression remains present and unchanged alongside the additive path regression. Recorded unrelated fixture amendments explain actual fixture defects, and transient added numeric expectations were reconciled with mathematical JSON integrality without weakening frozen tests. No vacuous sole assertions, skip/xfail weakening, or repository mocks were found.
- **Acceptance harness integrity:** dynamic test discovery includes the two repairs; fresh Bash processes keep assertion failure meaningful despite callers using conditionals; temporary checkout/store/workflows override inherited roots; cleanup covers success/failure/signals. The full-suite meta-test checks hostile inherited stores and intentionally masked failures. New findings expose missing behavior cases rather than removed tests.

### Verification

- Independently ran the real `bash tests/log-step.sh`: **23 passed, exit 0**, evidence `/tmp/orchestrail-integrated-focused.log`.
- Independently ran the canonical contract gate and changed-script syntax checks: passed.
- Inspected unchanged-source full-suite evidence `/tmp/orchestrail-path-full.log`: **574 passed, 0 failed, 2 configured hygiene skips**. Full repeat was unnecessary after the focused rerun and no source edits.
- Independently reproduced both remaining findings in temporary stores. Original disclosure/hang regressions pass within the actual isolated harness.
- No real historical corpus was read. Preservation conclusions use changed-file scope, isolated full-store checksums and source ordering rather than claiming an actual historical checksum audit.

### Summary

Step 2 (Code Review) complete: **2 findings — 0 critical, 2 important, 0 optional**. Both require repair before review readiness. The fresh Contract Check has one existing acceptance defect represented by two failed rows; finding 1 adds a separate producer compatibility/flow-contract failure discovered during code review. Neither introduces a critical invariant/off-limits failure, so the completed review can proceed to issue consolidation and approved repairs.
