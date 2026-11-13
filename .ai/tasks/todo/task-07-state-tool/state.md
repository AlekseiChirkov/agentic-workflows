spec_path: .ai/specs/07-state-tool.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: not-started
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Spec lists AC-12 and REQ-14 as withdrawn → they are excluded from the task contract; AC-01–AC-11 and AC-13–AC-23 are binding (source: spec `## Requirements` REQ-14, `## Acceptance Criteria` AC-12, D-01).
- Rule file names → the current names apply (`rules/workflow-globals.md`, `rules/workflow-reference.md`, `rules/tdd.md`), because the rule-renaming spec has not landed (source: spec constraint C-4; `rules/` directory listing).
- Acceptance-suite location and registration → a suite under `tests/` with a focused validator mode and a default-run registration, matching every existing suite (source: `scripts/validate-contracts.sh:284-343`; spec implementation hint, nonbinding).
- Test level for this repository → `smoke`/`integration` through executable fixtures; a contract change starts with a failing check (source: `.ai/principles/architecture.md` P7; `.ai/principles/coding.md → Changing a contract`).
- Pinned script digests → every digest in `tests/fixtures/validator-runtime/source_guard_exceptions.json` invalidated by an edit to a pinned script is refreshed in the subtask that makes the edit, by the recorded fixture procedure (source: spec `### Contract-file changes`; ADR-0020 Decision on fixture maintenance).
- Deployment → `scripts/sync.sh` is not changed and not run by this task's subtasks; the tool is addressed through the source root like other helpers (source: spec Out of Scope; ADR-0021 Decision 3).
- Knowledge updates (architecture inventory counts, state registry, progress log) → applied by the orchestrator at finalization, not by subtask workers (source: `rules/orchestration.md → ## Shared-file discipline`).
- flow: full — gate: 1fail 2fail 3pass 4pass (more than three files; a new protected field and new invariants are introduced) (source: `rules/quick-flow.md → ## The escalation gate`).
- Specification labels in product code (raised by the T-02 validation: four docstrings named invariants as `I-1`, `I-4`, `I-5`, `I-6`) → requirement, criterion, invariant, decision and assumption labels of the spec are planning identifiers; product code, tests, comments and docs state the rule in words. T-02 is corrected by its Implementer and re-validated by a new independent Validator, then the run continues (source: user, 2026-11-13).
- Worker model support for selection (the worker tool does not expose a context window) → the documented 1,000,000-token context of the catalog is confirmed as the support observation; selection uses the current catalog without a refresh (source: user, 2026-11-13).
- Registration of the acceptance suite in `scripts/validate-contracts.sh`, given the frozen validator inventory (raised by T-01 during implementation) → register once in the receipts-grammar subtask (T-09) together with the three contract checks, through one exact, enumerated oracle extension; T-10 refreshes the suite's pinned digest once more; earlier subtasks run the suite directly plus the guard suites; the registration test already in the committed RED set of T-01 is deferred to T-09 (source: user, 2026-11-13; arbiter recommendation with citations: ADR-0018, ADR-0019 Decision 3, ADR-0022 Decision 4, spec REQ-20 / AC-18).

### Description Amendments
- [2026-11-13] Suite registration moved from T-01 to T-09 by owner decision after T-01 found that the frozen validator inventory cannot accept a new check, focused mode or resource row without an oracle extension.
- Original: T-01 step 9 and its last acceptance criterion register the suite (`--state-tool-only` mode and `test_state_tool_acceptance` check) and amend the inventory; T-09 adds only the three contract checks.
- Amended: T-01 leaves `scripts/validate-contracts.sh` unchanged and refreshes only the source-guard fixtures; T-09 registers the suite and performs the one exact oracle extension (targets gain `tests/fixtures/validator-runtime/oracle.py` and `tests/validator-runtime-oracle.py`); T-10 refreshes the suite's resource row and the amendment digest; T-02–T-08 verify with the suite run directly. The spec is unchanged.
- [2026-11-13] T-02 scope extended with two parser corrections raised by the T-01 validation and resolved by the Arbiter from the spec grammar (class A).
- Original: T-02 covers the `validate` command only.
- Amended: T-02 also makes an indented fence inside a block opaque block content (spec `## Data Model` Block end row and fence rule, REQ-02, AC-01) and makes a repeated header status segment a malformed block for reads and writes (spec repeated-field rule, original §4(5), `### Read outcomes`). Two acceptance criteria and two scenarios added to its description.

## Open Questions (batch)
None

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10

## Subtask Progress

T-01 | Progress parser and get command | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — reviewed: 10/10 acceptance criteria met, suite 43/43, source guard and guard/oracle suites pass, validator unchanged; no critical or important finding; 8 proposals recorded in batch mode, none applied
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: tdd: integration — 44 tests (62 failures counting subtests), AC coverage 10/10; unit-level AST scans; smoke-level static check of the validator registration (running the focused mode from inside the suite would recurse; the mode itself is run at GREEN)
         tdd: red digest — AC-1 → test_leaf_and_composite_kinds_reported_and_fenced_lines_ignored; AC-2 → test_reads_leave_every_file_unchanged_and_create_none, test_stale_temporary_files_are_listed_but_never_read_or_deleted, every test via the one-JSON-object/schema_version check; AC-3 → test_leaf_without_atomic_tests_in_progress_is_applicable, test_leaf_with_atomic_tests_not_started_is_not_applicable; AC-4 → test_unknown_command_exits_2, test_malformed_block_id_exits_2; AC-5 → test_unrecognized_prefix_is_read_as_leaf_with_warning, test_unknown_header_field_is_reported_with_warning, test_newer_contract_version_warns, test_contract_version_without_tool_version_warns; AC-6 → test_duplicate_block_warns_on_other_block_and_rejects_whole_read, test_missing_state_file_exits_3, test_absent_field_gives_empty_header_fields_and_fields; AC-7 → test_missing_required_fields_warn, test_malformed_receipts_line_warns; AC-8 → test_symbolic_link_state_file_exits_7, test_task_outside_root_exits_2; AC-9 → test_imports_are_standard_library_only_and_no_dynamic_execution, test_version_guard_precedes_every_import_other_than_sys, test_get_works_without_fcntl; AC-10 → test_focused_mode_and_default_check_run_this_suite; edge → test_fields_report_values_continuations_and_known_flags, test_repeated_notes_groups_are_separate_entries_in_file_order, test_field_filter_selects_a_header_field, test_column_zero_foreign_line_ends_block, test_section_without_blocks_reads_empty_list, test_missing_final_newline_is_read, test_fix_task_block_id_is_accepted, test_report_names_task_relative_to_root_and_revision_of_bytes, test_repeated_read_gives_identical_output, test_leaf_without_atomic_tests_not_started_is_not_applicable, test_missing_required_option_exits_2, test_supported_or_absent_contract_version_does_not_warn, test_twenty_well_formed_receipts_do_not_warn, test_well_formed_block_has_no_warnings, test_missing_block_exits_3, test_missing_or_duplicated_section_exits_3, test_malformed_lines_make_block_malformed, test_repeated_unknown_field_is_preserved_not_malformed, test_unsupported_encodings_exit_3, test_non_regular_state_file_exits_7, test_old_python_exits_7_before_file_access, test_vocabulary_constants_equal_anchored_rule_lines
         RED observed: 61 failures report the tool file absent (no JSON on stdout, or the explicit existence assertion for in-process and AST cases); 1 reports the focused validator mode missing; 0 errors, 0 passes
         output shape chosen where the contract is silent: header_fields is a list of {name, value} in header order (parallel to fields); a problem in another block is listed in warnings by its error code (block-duplicate, malformed-block)
         source guard at RED: the new suite file changes the inventory fingerprint (133 stale classified records, 112 unclassified sites incl. the suite's one runner call); pinned fixtures are refreshed once at the end of GREEN
         blocked 2026-11-13 at the validator registration (frozen validator inventory cannot accept a new check or focused mode); resolved by owner decision 2026-11-13 — registration moved to the receipts-grammar subtask; validator edit reverted (diff empty)
         tdd: test amended — test_focused_mode_and_default_check_run_this_suite — removed: the registration obligation moved to a later subtask by owner decision of 2026-11-13, because the frozen validator inventory cannot accept the check without an oracle extension; its now-unused VALIDATOR_SCRIPT constant went with it; no other test was deleted, renamed, skipped or weakened (RED set 44 → 43; amended AC-10 is verified by the direct suite run, the guard suites and an empty validator diff)
         fixture refresh: digest of the inventory without the new suite equals the recorded 314b1e91…, so the suite is the only changed input; 133 inventory_sha256 fields → e1ba94f9…; one reviewed record appended for the run_tool subprocess call (dependency scripts/state-tool.py f92e566f…); manifest digest in source_guard.py → 6a78ae7b…; no other record changed
         GREEN: suite 43/43; source guard pass; validator-runtime guard, regressions, production, dynamic, external-source, oracle (22), integrated, allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist, wrapper-shadow, identity, security, version-isolation and warning isolation/operators/strict/fingerprint suites pass; complete validator not run (orchestrator runs it at task validation)
         finalize: architecture.md update proposed as a delta (orchestrated mode, not applied); plan.md T-01 → done returned as a delta; no composite membership; compression requested from the orchestrator
         pav-check 2026-11-13: DONE. Test-set audit — the diff between the test commit and the implementation commit removes only test_focused_mode_and_default_check_run_this_suite and its VALIDATOR_SCRIPT constant (recorded amendment, owner decision); the other 43 digest names are present, no skip/xfail, no weakened assertion. Amended AC-10 has no in-suite test by that decision; it was verified by running the suite, the source guard, the guard/oracle suites and an empty validator diff. Manual runs against a disposable task directory confirmed kinds, fenced look-alikes, warnings, refusals (exit 2/3/7), null keys and an unchanged directory. Optional findings only: an indented fence inside a block ends the block and later field lines are silently foreign; a repeated header field is accepted without a warning; a whitespace-only line of one or two spaces makes the block malformed; NUL bytes are accepted; the suite has no case for a malformed tool VERSION or for io-error; command_get splits lines and computes fence flags twice
         pav-propose 2026-11-13 (batch, nothing applied): Do Now — tests for a malformed tool VERSION and for an unreadable state file; Do Later — fence inside a block, repeated header field, whitespace-only short lines, NUL bytes; Optional — double line split in get, misplaced section comment, absolute path in the state-missing message
  branch: feat/state-tool-reader
  base_branch: main
  base_commit: 060ce6dbc7116002ac5e6cd47981cfd3c13d60ff
  commits: b4d1309 test(state-tool): cover structural reads of the progress section, 19989c0 feat(state-tool): read the progress section with a structural parser
  pr: #80 draft

T-02 | Static validation command | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — reviewed: 11/11 acceptance criteria met, suite 73/73, source guard and guard/oracle suites pass, validators unchanged, specification labels removed with no behaviour change; no critical or important finding; 8 proposals recorded in batch mode, none applied
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: tdd: integration — 29 tests (57 failures counting subtests), AC coverage 11/11; subprocess runs of get and validate against disposable task fixtures through the existing runner helper (no new subprocess call site)
         tdd: red digest — AC-1 (indented fence) → test_indented_fence_inside_a_block_is_opaque_block_content, test_continuation_after_a_closing_fence_belongs_to_the_preceding_field, test_column_zero_fence_ends_the_block; AC-2 (repeated header segment) → test_repeated_header_status_segment_makes_the_block_malformed; AC-3 → test_well_formed_fixture_is_valid_and_leaves_every_file_unchanged, test_every_outcome_creates_modifies_and_deletes_nothing; AC-4 → test_n_a_requires_em_dash_justification; AC-5 → test_missing_required_fields_per_kind_exit_6; AC-6 → test_completion_requires_green_or_justified_n_a_or_pre_tdd_note; AC-7 → test_header_status_outside_vocabulary_is_invalid_value; AC-8 → test_duplicated_block_exits_3, test_two_progress_sections_exit_3, test_malformed_receipts_line_exits_3; AC-9 → test_structure_and_invariant_errors_are_both_listed_with_exit_3; AC-10 → test_leftover_temporary_file_is_listed_and_kept; AC-11 → test_block_option_ignores_invariant_errors_of_other_blocks; edge → test_repeated_validation_gives_identical_output, test_newer_contract_version_is_a_warning_only, test_empty_and_composite_only_sections_are_valid, test_justification_in_a_later_notes_group_or_continuation_line_counts, test_unknown_header_field_and_unrecognized_prefix_are_warnings_only, test_every_invariant_error_of_every_block_is_listed, test_missing_state_or_section_exits_3, test_malformed_block_exits_3, test_twenty_well_formed_receipts_are_valid, test_path_and_file_refusals_keep_exits_2_and_7, test_invalid_arguments_exit_2, test_block_option_ignores_structure_errors_of_other_blocks, test_block_option_refuses_missing_or_structurally_broken_block
         RED observed: 57 failures, 0 errors; 45 show exit 2 unknown-command where 0, 3 or 6 is expected and 5 show command null where validate is expected (the command does not exist yet); 3 show get reading notes only where branch after an indented fence is expected; 1 shows an empty notes continuation where the line after a closing fence is expected; 3 show get exit 0 where malformed-block exit 3 is expected for a repeated header segment; the 43 earlier tests pass
         test_column_zero_fence_ends_the_block: its get assertions already hold (a column-0 fence ends the block today); it fails RED only on the validate assertion — the column-0 rule is kept as a guard against the fence fix over-reaching
         arbiter: an indented fence (1-3 spaces) inside a block does not end it; delimiter and inner lines are opaque block content, never field, continuation or malformed lines; a continuation after the closing fence belongs to the preceding field; a column-0 fence still ends the block; an unclosed fence runs to end of file (source: spec Data Model, Section and block grammar, fence rule and Block end row, .ai/specs/07-state-tool.md:367-368,377; REQ-02; AC-01; Edge Cases "Block-like lines inside a fence")
         arbiter: a repeated header status segment makes the block malformed — get --block and validate on it exit 3 malformed-block, reads of other blocks warn, writes refuse (source: spec repeated-known-field rule .ai/specs/07-state-tool.md:380; original section 4(5) on ambiguously recognized structure; Read outcomes rows for a malformed block; closed error-code table)
         no separate test for an unclosed fence: get output is identical before and after the fix (everything after the opener is fenced and the section runs to end of file), so such a test could not fail first
         implementation choices where the contract is silent: validate checks invariants of every selected block, malformed or duplicated ones included, and lists structure errors before invariant errors; one required-field-missing error per block names every missing field; errors carry the header line (receipts errors the receipts line); with --block, validate reports no warnings for other blocks; a blank line followed by an indented fence still ends the block (only a fence with no blank line before it is block content); repeated unknown header fields stay allowed, like repeated unknown field lines
         fixture refresh: inventory digest with the previous suite equals the recorded e1ba94f9…, so the suite is the only changed inventory input; 134 inventory_sha256 fields (133 plus the suite's runner record) → 2b1e88a2…; that record's dependency scripts/state-tool.py f92e566f… → 6d29bceb…, its context unchanged; no record added or removed; manifest digest in source_guard.py → a27962cf…
         GREEN: suite 72/72 (43 earlier + 29 RED, unchanged since the test commit, no removed lines); source guard pass; validator-runtime guard (6), regressions (25), production (2), dynamic (4), external-source (5), oracle (22), integrated (2), allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist, wrapper-shadow, identity (11), security (3), version-isolation, warning isolation/operators/strict/fingerprint pass; validate on all nine repository task state files exits 0 valid; lint not applicable (no shell file changed); complete validator and build not run (orchestrator runs them)
         finalize: architecture.md update proposed as a delta (orchestrated mode, not applied); plan.md T-02 → done returned as a delta; no composite membership; compression requested from the orchestrator
         output shape chosen where the contract is silent: validate reports result invalid for every non-zero exit, including exits 2 and 7 (the read-outcomes table names invalid for those; the output table allows only valid / invalid); --field is not an option of validate (exit 2 invalid-arguments)
         source guard at RED: fails with stale classified references because the suite changed; pinned fixtures are refreshed once at the end of GREEN
         pav-check 2026-11-13: NEEDS WORK. Acceptance criteria 11/11 met (suite 72/72; each criterion also reproduced by hand against disposable task directories; validate on copies of the nine repository task state files exits 0 valid and get output is byte-identical to the previous tool). Test-set audit clean: the test commit only adds lines (406 added, 0 removed), the implementation commit does not touch the suite, the 29 digest names and the 43 earlier names are present, no skip or expected-failure marker, no weakened assertion. Source guard and the guard, oracle, integrated, allowlist and external-source suites pass; both validators and the oracle files are unchanged against the base commit; the fixture diff changes 134 inventory digests, one dependency digest and the manifest digest only (134 records before and after)
         pav-check important (blocks closing): scripts/state-tool.py:501, 506, 511 and 529 — four docstrings name the invariants by their specification labels (`I-1`, `I-4`, `I-5`, `I-6`); the labels exist only in the planning record, so product code points at it (Off-limits: no planning identifier in product code or comments; the pipeline-identifier rule of the git-flow contract); line 501 says nothing else. Fix: state the rule in words; then refresh the pinned tool digest and the manifest digest
         pav-check optional: a blank line before an indented fence ends the block, so field lines after the closing fence become unreported foreign lines and validate reports valid (recorded implementation choice, no test pins it); an unclosed indented fence hides every later block and validate still reports valid with no warning; a continuation line that follows a fence placed directly under the header is now malformed-block where the previous tool read it as foreign; group end indexes exclude a trailing in-block fence, which matters to later field insertion; no test for an empty receipts line or a receipts line with a continuation line (both exit 3 by hand)
         tdd: unit — rework for the specification-label finding: a static scan is feasible and proportionate (same form as the existing source-contract checks), so the gate returns unit; 1 test, test_sources_state_rules_without_specification_labels, scans the tool and the suite for REQ-, AC-, I-, D- and A- labels followed by a number
         rework RED observed 2026-11-13: suite 73 tests, 1 failure, 0 errors — the new test lists the labels at state-tool.py:501, 506, 511 and 529; the suite itself has none; the 72 earlier tests pass
         rework GREEN 2026-11-13: suite 73/73 (72 earlier + the wording test, suite unchanged since its test commit); AST of the tool with docstrings removed equals the previous commit (no behaviour change); source guard pass; validator-runtime guard (6), regressions (25), production (2), dynamic (4), external-source (5), oracle (22), integrated (2), allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist, wrapper-shadow, identity (11), security (3), version-isolation and warning isolation/operators/strict/fingerprint pass
         rework fixture refresh: inventory digest with the pre-rework suite equals the recorded 2b1e88a2…, so the suite is the only changed inventory input; 134 inventory_sha256 fields → 5c76be5a…; the runner record's dependency scripts/state-tool.py 6d29bceb… → 59ab21eb…, context unchanged; no record added or removed; manifest digest in source_guard.py → eb3e7b40…
         pav-check 2026-11-13 (re-validation by a new independent validator): DONE. Acceptance criteria 11/11 met — suite 73/73, and each criterion reproduced by hand with about 90 runs against disposable task directories (every run: one JSON object, directory snapshot identical). Exit rule confirmed: path and file refusals keep exit 2 (outside root, invalid arguments) and exit 7 (symbolic link, directory, named pipe) with result invalid; otherwise 3 with any structure error, else 6, else 0; a mixed fixture lists structure errors and invariant errors together. Receipts format confirmed at the boundaries (1 and 20 entries valid; 0 or 21 entries, upper-case or 15/17-digit digest, 65-character id, id starting with a hyphen, repeated id, separator without a space, trailing space, continuation line → exit 3 malformed-receipts; get only warns). validate on copies of the nine repository task state files exits 0 valid, leaves each copy unchanged, and get output is byte-identical to the base-commit tool
         pav-check earlier finding resolved: no requirement, criterion, invariant, decision or assumption label in scripts/state-tool.py or tests/state-tool.py (scan also covers constraint labels and planning paths; the only block ids and task paths are fixture data); the correction commit changes four docstrings only — the tool's syntax tree with docstrings removed equals the previous commit, and the suite is untouched by it
         pav-check test-set audit clean: both test commits only add lines to tests/state-tool.py (406 and 15 added, 0 removed) and touch nothing else; the implementation and correction commits do not touch the suite; the 29 digest names, the 43 earlier names and the wording test are present (73); no skip or expected-failure marker, no vacuous assertion; every criterion maps to at least one test
         pav-check environment: source guard pass; validator-runtime guard (6), guard-executable (90), guard-regressions (25), guard-production (2), guard-dynamic (4), oracle (22), integrated (2), allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist and external-source-guard (5) pass; scripts/validate-contracts.sh, scripts/validate-task.sh, the oracle files, workflows/ and rules/ are unchanged against the base commit; the fixture diff against the base commit changes 134 inventory digests, one dependency digest and the manifest digest only (336 records before and after, identical apart from digests); tool imports are standard library only, with no subprocess, os.system, exec or eval and no write call other than stdout and stderr; lint not applicable (no shell file changed); the complete validator was not run (evidence gap by owner decision — the orchestrator runs it at task validation)
         pav-check optional (carried over, still reproducible, none blocks closing): a blank line before an indented fence ends the block, so field lines after the closing fence are unreported foreign lines and validate reports valid; an unclosed indented fence hides every later block and validate reports valid with no warning; a continuation line after a fence placed directly under the header is malformed-block; group end indexes exclude a trailing in-block fence; no suite case for an empty receipts line or a receipts line with a continuation line (both exit 3 by hand). New optional: the wording test covers five label families in two files only (constraint labels and other product files are outside it) and its pattern would also flag ordinary text such as a paper size written with a hyphen; no suite case pins exit 7 for a state file that is a directory or a named pipe under validate, or the order of structure errors before invariant errors
         pav-propose 2026-11-13 (batch, nothing applied): Do Now — 1 (suite cases for an empty receipts line, a receipts line with a continuation line, a directory or named pipe as the state file under validate, and the order of structure errors before invariant errors); Do Later — 4 (blank line before an indented fence, unclosed indented fence hiding later blocks, field-group end index excluding a trailing in-block fence, continuation line after a fence directly under the header); Optional — 3 (shared block selection of get and validate, double line split in the loader, breadth and precision of the wording test)
  branch: feat/state-tool-validate
  base_branch: feat/state-tool-reader
  base_commit: a02a8861f7537531bfefbcb78e07f33bb0e92ee4
  commits: bbbc32b test(state-tool): cover static validation and block grammar corrections, 7dcf8b9 feat(state-tool): validate the progress section statically, 51fee56 test(state-tool): require rules to be stated without specification labels, 8a3b9a9 fix(state-tool): state invariant rules in words in docstrings
  pr: #81 draft

T-03 | Set write transaction | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — reviewed: 10/10 acceptance criteria met, suite 103/103, source guard and guard/oracle suites pass, validators unchanged; no critical or important finding; 8 proposals recorded in batch mode, none applied
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes: tdd: integration — 30 tests (67 failures counting subtests), AC coverage 10/10; subprocess runs of set and get against disposable task fixtures through the existing runner helper (no new subprocess call site); a NUL value and blocked fcntl run in process through the existing in-process helper
         tdd: red digest — AC-1 → test_rich_block_change_touches_only_the_changed_line_and_the_receipt_line; AC-2 → test_plain_field_change_reports_changed_fields_and_keeps_header_statuses; AC-3 → test_missing_field_and_header_segment_are_inserted_at_canonical_positions; AC-4 → test_second_writer_with_the_same_revision_is_refused, test_change_in_another_section_after_the_revision_is_kept_and_refused; AC-5 → test_damaged_structure_refuses_the_write_without_any_change; AC-6 → test_value_outside_vocabulary_or_content_rules_is_invalid_value, test_unknown_header_field_and_unrecognized_prefix_refuse_writes, test_newer_or_uncheckable_contract_version_refuses_writes; AC-7 → test_read_only_and_inapplicable_fields_are_refused, test_values_equal_to_current_are_unchanged_without_write_or_receipt; AC-8 → test_invalid_write_invocations_exit_2_with_one_json_object; AC-9 → test_refusals_with_exit_4_and_6_print_the_no_bypass_sentence; AC-10 → test_missing_final_newline_is_preserved; edge → test_several_fields_change_in_one_replace_and_are_listed_in_order, test_composite_status_change_applies_with_the_receipt_after_notes, test_missing_field_without_an_earlier_known_field_goes_directly_after_the_header, test_out_of_order_known_fields_and_repeated_unknown_fields_keep_their_places, test_existing_receipts_line_is_extended_in_place, test_in_block_fence_is_kept_in_place_and_never_an_insertion_point, test_receipt_digest_depends_on_inputs_and_not_on_field_order, test_values_are_stored_literally, test_other_duplicated_block_or_pre_existing_invalid_value_does_not_block, test_missing_state_file_exits_3, test_value_with_nul_is_invalid_value, test_lock_wait_bounds_are_accepted, test_lock_file_holds_owner_metadata_with_private_mode, test_original_permission_bits_are_kept, test_symbolic_link_lock_path_exits_7, test_set_without_fcntl_exits_7_and_touches_nothing
         RED observed 2026-11-13: suite 103 tests, 67 failures counting subtests, 0 errors; every failure shows exit 2 unknown-command for set (23 where 0 is expected, 12 where 3, 2 where 4, 15 where 6, 2 where 7; 13 exit-2 cases name unknown-command instead of invalid-arguments, malformed-revision or invalid-operation-id); the 73 earlier tests pass
         test plan additions (scope items without a description criterion): lock owner metadata and mode 0600, symbolic-link lock path, original permission bits, fcntl unavailable, the lock-wait bound, a malformed receipts line, a missing block, section or state file, an existing receipts line extended in place, a duplicated other block that does not block the write
         arbiter: in-block fences and writes — a block with an indented fence is not malformed and writes proceed; fenced lines are preserved byte for byte and never moved; insertion positions come from field groups only, so a fence never counts as the last line of a field group; a continuation line after a closing fence belongs to the preceding field line (source: spec Data Model, Block end row, field group and insertion rules .ai/specs/07-state-tool.md:376-379,397-399; REQ-01, REQ-03, REQ-17; the invariant that unchanged lines stay byte-identical) — pinned by test_in_block_fence_is_kept_in_place_and_never_an_insertion_point
         arbiter: repeated header status segment — the block is malformed; writes refuse with exit 3 and leave state.md unchanged (source: spec original section 4(5) on ambiguously recognized structure; Read outcomes) — pinned by test_damaged_structure_refuses_the_write_without_any_change
         test choices where the contract is silent: the receipt digest is checked for 16 lowercase hex characters, determinism and independence of field order, not for the exact JSON shape of the inputs; out-of-order fixtures are chosen so that file order and canonical order give the same insertion point
         source guard at RED: fails with 134 stale classified references because the suite changed; pinned fixtures are refreshed once at the end of GREEN
         coordinator ruling 2026-11-13: the receipt input digest follows the spec exactly — SHA-256 over UTF-8 JSON of command, block_id and inputs with sorted keys and separators , and : — and its shape stays stable for later commands; implemented inputs for set are fields (name/value pairs sorted by name) and notes (argument order, empty until note support lands); JSON keeps non-ASCII text as UTF-8
         assumption (coordinator, 2026-11-13): a missing known field goes after the last line of the last matching field group in file order, planned insertions of the same write included; pinned only where file order and canonical order agree
         implementation choices where the contract is silent: a field set is not-applicable when it belongs only to the other block kind and read-only otherwise (git, unknown, state_receipts, notes, target_files, children); an absent header segment other than atomic-tests also goes before the first present segment that follows it in canonical order, or last; replacing a field line keeps its continuation lines; whitespace-only last_action or blocker is empty; the no-bypass sentence is printed for write commands only (validate exit 6 is not a refusal of a write); state.md is checked before the lock is taken, so state-missing and unsafe-state-file create no lock file; lock-busy reports only its code until lock details land
         out of scope, left for later subtasks: a 21st receipt makes the candidate re-check fail with internal-error until the receipt cap drops the oldest entry; no pre-existing-violation or required-field-missing warning on writes yet
         tdd: no test amended; tests/state-tool.py is unchanged since the test commit (30 RED tests and 73 earlier tests intact, no skip or expected-failure marker)
         fixture refresh: inventory digest with the base-commit suite equals the recorded 5c76be5a…, so the suite is the only changed inventory input; 134 inventory_sha256 fields → ee98fc26…; the runner record's dependency scripts/state-tool.py 59ab21eb… → 37795065…, its context unchanged; no record added or removed; manifest digest in source_guard.py → 4e4a2a04…
         GREEN 2026-11-13: suite 103/103; source guard pass; validator-runtime guard (6), guard-executable (90), guard-regressions (25), guard-production (2), guard-dynamic (4), oracle (22), integrated (2), allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist, external-source-guard (5), wrapper-shadow, identity (11), security (3), version-isolation and warning isolation/operators/strict/fingerprint pass; manual set on a copy of this task directory changes exactly the named lines plus one receipts line and validate-task.sh still passes; lint not applicable (no shell file changed); typecheck not configured; build (deploy) and the complete validator not run by direction
         finalize: architecture.md update proposed as a delta (orchestrated mode, not applied); plan.md T-03 → done returned as a delta; no composite membership; compression requested from the orchestrator
         pae-finalize summary (kept from the previous last_action): set changes the named fields of one block under the task lock and the expected-revision check, inserts missing fields and the atomic-tests segment at canonical positions, appends a receipt, re-parses the candidate and replaces state.md with one rename
         pav-check 2026-11-13 (independent validator): DONE. Acceptance criteria 10/10 met — suite 103/103, and each criterion reproduced by hand with about 190 runs against disposable task directories (every run: one JSON object on stdout; after every refusal state.md byte-identical with the same mode, mtime and inode and no temporary file). The rich block on two identical copies differs from the original by the changed last_action line plus one receipts line after the last notes continuation line and before the unknown field, with byte-identical results and identical output; the receipt entry equals the operation id, a hash sign and the first 16 hex digits of SHA-256 over the sorted-key compact UTF-8 JSON of command, block id and inputs, recomputed independently
         pav-check write order confirmed by a system-call trace of one applied write and by ordering probes: arguments (exit 2) before the fcntl check, fcntl before paths, state.md inspected before the lock, lock file opened with no-follow, create and mode 0600, non-blocking exclusive lock, truncate and owner metadata, read, encoding and contract version, structure refusals (exit 3) before the revision check (exit 4), revision before writability, writability before value rules, unchanged shortcut without receipt, temporary file opened exclusively with no-follow and the original permission bits, file sync, identity and revision recheck, one rename, directory sync; a single process, no child process
         pav-check file safety confirmed in process by wrapping single calls: bytes rewritten before the recheck, the same bytes under a new inode, and a removed state.md each exit 4 state-file-changed with the other writer's bytes kept and the tool's temporary file removed; a failing candidate write, permission change, file sync, rename or lock metadata write exits 7 with state.md unchanged and no temporary file; a failing directory sync after the rename reports applied with the directory-sync warning; an existing file with the chosen temporary name is neither overwritten nor removed (exit 7); a held lock gives exit 5 after the wait bound with the no-bypass sentence and the holder's metadata untouched; a lock path that is a symbolic link, a dangling link, a directory or a named pipe exits 7 unsafe-lock-path without hanging; permission bits 0640, 0604, 0444, 0600 and 0664 survive under a restrictive umask; twelve concurrent writers with one revision give exactly one applied and eleven revision conflicts
         pav-check test-set audit clean: the test commit only adds lines to tests/state-tool.py (592 added, 0 removed) and touches nothing else; the implementation commit does not touch the suite and the working tree equals it; the 30 digest names and the 73 earlier names are present (103); no skip or expected-failure marker, no vacuous assertion; every criterion maps to at least one test
         pav-check environment: source guard pass; validator-runtime guard (6), guard-executable (90), guard-regressions (25), guard-production (2), guard-dynamic (4), oracle (22), integrated (2), allowlist, allowlist-guard, allowlist-shell, sourceguard-allowlist and external-source-guard (5) pass; scripts/validate-contracts.sh, scripts/validate-task.sh, the oracle files, workflows/ and rules/ are unchanged against the base commit; the fixture diff changes 134 inventory digests, one dependency digest and the manifest digest only (134 records before and after, no other leaf changed); imports are standard library only, no subprocess, system, exec or eval call; no specification label or planning path in the tool or the suite (block ids are fixture data); get and validate output on copies of the nine repository task state files is byte-identical to the base-commit tool and the copies are untouched; a set on a copy of this task's state file changes the header line, the last_action line and one inserted receipts line and still validates; lint not applicable (no shell file changed); the complete validator was not run (evidence gap by owner decision — the orchestrator runs it at task validation)
         pav-check boundaries owned by later subtasks, judged safe: a write to a block that already holds 20 receipt entries, and a reused operation id with other inputs, are refused with exit 1 internal-error (candidate re-check) before any temporary file exists, state.md unchanged — safe, but the message does not name the cause until the receipt cap and the operation-conflict refusal land; writes report no required-field-missing warning yet; an interrupt while waiting for the lock ends with a traceback and no JSON object, state.md unchanged
         pav-check optional (none blocks closing): scripts/state-tool.py:269 — a wait bound of more than 4300 digits exits 1 internal-error instead of exit 2 (integer conversion limit); scripts/state-tool.py:771 — changing a header status whose current value is empty writes the value without the space before the next separator (the header still parses); scripts/state-tool.py:969-971 — when state.md cannot be read at the recheck the reported result revision falls back to the earlier source revision instead of null; scripts/state-tool.py:1117 — the check before the lock reads the whole file where an inspection would do; no suite case pins the exact JSON shape of the receipt digest, an encoding refusal on a write, an I/O failure with exit 7, or a lock path that is a directory or a named pipe
         pav-propose 2026-11-13 (batch, nothing applied): Do Now — 2 (suite cases for the exact receipt digest input, an encoding refusal on a write, an I/O failure with exit 7 and a directory or named pipe as the lock path; a wait bound with thousands of digits refused with exit 2); Do Later — 3 (named refusals for a full receipts line and a reused operation id once the receipt subtask lands, one JSON object on an interrupt, a null result revision when state.md is unreadable at the recheck); Optional — 3 (spacing after an empty header status value, inspection instead of a full read before the lock, one shared contract-version check for reads and writes)
  branch: feat/state-tool-set
  base_branch: feat/state-tool-validate
  base_commit: 5e49da3c248031a4415bfb5e6b08706e39733530
  commits: 04d8f9c test(state-tool): cover field updates through the write transaction, b558e3e feat(state-tool): update block fields through a locked atomic write
  pr: none

T-04 | Note and target-file additions | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-05 | Lifecycle invariants on set | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-06 | Block initialization | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-07 | Idempotent operation receipts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-08 | Lock contention and interruption recovery | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-09 | Receipts grammar contract and validator checks | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: rules/workflow-globals.md, rules/workflow-reference.md, scripts/validate-task.sh, scripts/validate-contracts.sh, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/inventory-amendment.json, tests/fixtures/validator-runtime/oracle.py, tests/validator-runtime-oracle.py
  blocker: none
  notes:

T-10 | Ignore rules and usage documentation | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: .gitignore, scripts/setup-new-project.sh, docs/USAGE.md, scripts/README.md, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/inventory-amendment.json, tests/validator-runtime-oracle.py
  blocker: none
  notes:

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Variant 1. The line-preserving model makes REQ-01 and I-8 hold by construction rather
than by careful re-serialization, and the Python suite covers every acceptance criterion,
including the in-process and static-scan cases, in the form the repository already uses
for Python helpers. The per-subtask fixture refresh is the price of keeping every stack
tip fully valid.

Implementation shape (binding for all subtasks):
- One file `scripts/state-tool.py`; the Python-version guard precedes every import other
  than `sys`; vocabulary constants are module-level tuples, one line each.
- Layers as functions: argument parsing → path and file checks → document parse (lines
  with roles, section span, blocks with field groups) → invariant predicates → edit
  operations returning a new line list and changed-field names → receipts → write
  transaction (lock, read, revision, candidate re-parse, temporary file, recheck, rename)
  → JSON result. Parsing, invariants, edits and receipts are callable without the command
  line.
- Errors are a single exception type carrying exit code, error code, message and optional
  line; one top-level handler prints the JSON object on stdout and diagnostics on stderr.
  An unexpected exception is exit 1 `internal-error`.
- Suite `tests/state-tool.py`: fixture builders, a subprocess runner, a directory snapshot
  helper (bytes, mode, mtime), and `runpy` loading for in-process cases; one test class
  per command or concern, extended by each subtask.
- Each subtask that changes a file under `tests/` finishes by refreshing the pinned
  source-guard fixtures by the recorded procedure.
- Amended 2026-11-13 (owner decision): the suite is registered in
  `scripts/validate-contracts.sh` once, in T-09, through one exact, enumerated extension
  of the frozen validator inventory; T-10 refreshes the suite's pinned digest. T-01–T-08
  do not edit the validator.
- Subtasks verify with `python3 tests/state-tool.py` and the source-guard suites
  (`bash scripts/validate-contracts.sh --state-tool-only` from T-09 on); the complete
  validator run happens at task-level validation.

adr: `.ai/adr/0022-task-07-state-tool-receipts-and-line-preserving-writes.md` (provisional)

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | 4 | 4 | 4 | 5 | 3 | 20 |
| Variant 2 | 3 | 3 | 4 | 3 | 3 | 16 |
| Variant 3 | 4 | 4 | 2 | 4 | 4 | 18 |

**Winner:** Variant 1 — byte preservation by construction and full acceptance coverage in the repository's existing suite pattern.
**Anti-overengineering check:** passed — no abstraction beyond functions in one file; the line model solves the stated byte-preservation requirement.
**Evidence:** spec REQ-01, REQ-03, I-8 and the Determinism target; `.ai/principles/architecture.md` P3 (additive contracts, parsers key on field names) and P7 (test-first, suite under the repository test command); `tests/model-catalog.py` and `scripts/validate-contracts.sh:284-343` (suite pattern); `tests/fixtures/validator-runtime/README.md` (fixture procedure); ADR-0021 (single standard-library file in `scripts/`).

### Scope
#### In
- `scripts/state-tool.py` with `get`, `validate`, `set`, `append-note`, `add-file`,
  `init-block` over the progress section of one task `state.md`.
- Structural parser, canonical invariants, per-task advisory lock, expected revision,
  atomic replace, in-block receipts, recovery reporting, test seam.
- Grammar extension `state_receipts:` in `rules/workflow-globals.md` and
  `rules/workflow-reference.md`, with checks in both validators and a vocabulary drift
  check.
- Ignore rules in `.gitignore` and `scripts/setup-new-project.sh`; "State tool" section and
  entry list in `docs/USAGE.md`; inventory row in `scripts/README.md`.
- Acceptance suite `tests/state-tool.py`, its validator registration, refreshed pinned
  fixtures.

#### Out
- Wiring the tool into any workflow; changing `scripts/sync.sh`.
- Writing git fields, `children:` after creation, or unknown fields; creating or deleting
  the section; deleting, renaming or repairing blocks.
- A transition table beyond the listed invariants; network filesystems, Windows writes,
  multi-host locking; run-log telemetry from the tool.
- Removing the grammar duplication between the two rule files.

### Rejected
→ archived to state-archive.md

### Off-limits
- No file under `workflows/` changes; no deployed copy under the home directory is edited.
- The tool writes only the task `state.md`, `<task>/.state-tool.lock` and its own
  `<task>/.state.md.<owner_token>.tmp`.
- The tool never passes an input value to a shell or interpreter and imports no
  third-party module.
- A held lock is never deleted, truncated or taken over; a temporary file the process did
  not create is never deleted or read as state.
- No existing field, vocabulary value, section name or exit code of an existing script is
  renamed or removed.
- No ignore rule may match a task `state.md`.
- No planning identifier or tool attribution in product code, tests, comments,
  documentation, branch names, commits or pull requests.

### Invariants
- After any refused or failed write, `state.md` is byte-identical and no temporary file of
  that process remains.
- After an applied write, every byte outside the changed and inserted lines of the target
  block is identical.
- Read commands create, modify and delete nothing.
- `atomic-tests` is never removed or moved to a lower rank; `pinned` changes only to
  `green`.
- stdout carries exactly one JSON object; diagnostics go to stderr only.
- The tool's vocabulary constants equal the anchored lines of `rules/workflow-globals.md`.
- Blocks without `state_receipts:` remain valid for every reader.
- `scripts/validate-contracts.sh` passes on the stack tip.

### Acceptance Criteria
The task is accepted when spec criteria AC-01–AC-11 and AC-13–AC-23 hold on the stack tip
(AC-12 is withdrawn). Mapping to subtasks:

| Spec criterion | Subtasks |
|---|---|
| AC-01 | T-01 (reads), T-03 (write refusals) |
| AC-02 | T-03 |
| AC-03 | T-01 (reads), T-03 (structure, version, vocabulary), T-05 (transitions) |
| AC-04 | T-03 |
| AC-05 | T-08 |
| AC-06 | T-02 (stale file listing), T-08 |
| AC-07 | T-07 |
| AC-08 | T-01 (read refusals), T-04 (literal note), T-08 |
| AC-09 | T-03 (exits 4, 6), T-07 (exit 8), T-08 (exit 5), T-10 (manual) |
| AC-10 | T-01, T-02 (reads), T-03 (write) |
| AC-11 | T-01 (reporting), T-05 (writes) |
| AC-13 | T-03 |
| AC-14 | T-01, T-03, T-06 |
| AC-15 | T-06 |
| AC-16 | T-04 |
| AC-17 | T-04 |
| AC-18 | T-09 |
| AC-19 | T-01, T-08 |
| AC-20 | T-05 |
| AC-21 | T-01, T-02, T-03, T-04, T-05 |
| AC-22 | T-01, T-02, T-03, T-07 |
| AC-23 | T-10 |

## Model Selection
selection: complete
active provider: anthropic (`Model (Claude)` column)
catalog: ~/.config/orchestrail/model-catalog.md, refreshed 2026-11-09 (fresh, 4 days old; evidence dated 2026-11-09)
support evidence (2026-11-13): the worker tool of this session accepts the model names haiku, sonnet, opus and fable; the session environment lists the identifiers claude-haiku-5-5, claude-sonnet-5-5 and claude-opus-5-5; worker tools: all; context window 1,000,000 tokens is owner-confirmed on 2026-11-13 (the tool does not expose it), not directly observed.
owner limits: allowed models are the three observed identifiers; the session model claude-fable-5-2 has no catalog evidence and was not a candidate.
cost: no qualified comparable total-cost evidence; the strongest eligible baseline was used, so cost optimality is unverified.
reasoning support (2026-11-13): the worker tool exposes the effort levels low, medium, high, xhigh and max and effort is configurable per worker; support per model is not separately observed.
reasoning rationale: catalog quality is measured at maximum effort and the catalog notes the selected model at high effort still meets band 4, which covers every leaf floor here (2–4); lower levels have no recorded evidence, so `high` is recommended for every leaf.
actual model and actual reasoning: unknown until separately observed execution evidence.

| Leaf | Scores (C/A/V/R/Ver/Crit/RW) | Floor | Recommendation | Confidence | Reasoning | Description sha256 | Plan row sha256 |
|---|---|---|---|---|---|---|---|
| T-01 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | f096f32d875af4167ed8cd213514f99a9ebb5ad9d201d1d6e5fb67d6978a83f8 | 6ce2122c5b6fc666ab3cd0dc892bb99247afd573da153c7997f76685c9ec5df7 |
| T-02 | 2/1/2/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | 39453f6c1b616ed11bfc060e2702503537152c50da591edd949848e99b343f9c | 3149e5789e84ba01435f26a64bba80331b44ee5b46e9419aa65c3f383d2c8253 |
| T-03 | 4/1/2/5/3/4/4 | 3 | claude-opus-5-5 | verified | high | 823ec3dbb2ec06092d14b79d3b34f7ec2f18dc36efc0729ee035f660c308c0b2 | 13c641e06e231c95f5b02271554ce164da1cda75b204c36268b1e9daa3062f5e |
| T-04 | 3/1/2/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | ef54102f753ab7ae758a5b0591afc960cd51f8b20012594859567469351fde3f | 3b7ece720cd48c1d52cc677d15417983280a887078fb7ad3b731ff5a6ff80c7f |
| T-05 | 3/2/2/4/4/3/3 | 3 | claude-opus-5-5 | verified | high | ab26d195f031d9e106b783647b17f4c5e76583d3eba1ee0015b3d0dbce3d0c45 | 2f10210fc1497db798b70f2f3162a79a9f70b22535a2e61263d94729aae82656 |
| T-06 | 2/1/2/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | 14fa76136cd4d7ea44e0eadb89b7450c51be2a3199b384f3e6f539c1a2eddcd2 | 2191236e1912d5b2f12cb910e6e8f93254bbe17704170f88ebf58a063dcd81ff |
| T-07 | 3/1/2/4/4/3/3 | 3 | claude-opus-5-5 | verified | high | 3e2c013be7b35058a1f3f713570691ec26afdfa07875e9fca6aa1e6131a22282 | 39fcc4f183f13a24852f83dbe7bd8e80e3a306cab40e4eb27bc10cfe8f6206e7 |
| T-08 | 4/2/2/5/3/4/4 | 4 | claude-opus-5-5 | verified | high | 192dfc1e797b67ced34fef704c3f316cde3d586428159e592ac65aba4936d05e | 0ca245069943e183a68833a951fda9ad183d21f0fa5d1962600c95eb2a1ce387 |
| T-09 | 3/1/4/3/4/3/3 | 3 | claude-opus-5-5 | verified | high | ae19f8108c81d29af4a114900c988ffeb3f3ebe4813d1d23e5dbb813e7b4fb14 | a14f65ee21e84747c2d4087199bdda67a6ad9d6e0687d7cebee726e546fca747 |
| T-10 | 2/1/3/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | 5c316822e2f2ad429c7905a9e5e2d241b9dac1727242e78027e8069a4e61b2ea | c3402c2761b09b1d9d036b2c08f3fa52c48c0a79d1e82f7ec54d9ae25dad655a |

## Improvement Proposals (T-01)

### Do Now
- [batch, not applied] Robustness (tests): add two read cases to `tests/state-tool.py` — a tool tree whose `VERSION` is malformed (for example `1.0`) with a task `contract_version: 0.9.0` must warn `unsupported-contract-version`, and an unreadable `state.md` (mode 000) must exit 7 `io-error` with `source_revision` null. Both behaviours exist in `scripts/state-tool.py` (`tool_contract_version`, `read_state`) and are stated by the spec (`### Contract version check`, `### Exit codes and error codes`) but no test pins them. New tests only; no amendment needed.

### Do Later
- Robustness (grammar decision, before the first write command): a fence opened at 1–3 spaces inside a block ends the block (`parse_blocks`, the `fenced[index]` branch), so field lines after the closing fence become unreported foreign lines. The grammar lists no fence among the block-end conditions; decide whether such a fence is opaque content of the block or a block end, state it in the grammar, and pin it with a test. Reproduction: a leaf with `  notes: a`, then `   ```` / `  pr: hidden` / `   ````, then `  branch: after` — `get` reports neither `pr` nor `branch` and exits 0 with no warning.
- Robustness (grammar decision, before `set`): a header that repeats a known status segment (`atomic-tests: red | atomic-tests: green | …`) is read without any warning, and `pre_tdd_exception` reads the last occurrence through a dictionary. Decide whether a repeated header field is malformed or a warning before a write command has to choose which segment to change.
- Robustness: a whitespace-only line of one or two spaces inside a block makes the block `malformed-block` (literal reading of the malformed-line rule). Editors leave such lines; decide whether they count as blank lines.
- Robustness: NUL bytes in `state.md` are accepted by reads and reported inside names and values; the encoding refusal could cover them once the write commands define their text rules.

### Optional
- Duplication: `command_get` splits the text and computes fence flags, then `parse_document` does both again; pass the line list and flags into the parser (the contract version must still be reported before a section refusal).
- Readability: the `contract version` section comment in `scripts/state-tool.py` sits above the line helpers (`split_lines`, `content`, `fence_flags`); move the helpers under their own heading.
- Readability: the `state-missing` message prints the absolute path while the report's `task` key is root-relative; use the relative form in the message.

## Improvement Proposals (T-02)

### Do Now
- [batch, not applied] Robustness (tests): add four cases to `tests/state-tool.py` for behaviour that `scripts/state-tool.py` already has and the contract states but no test pins — `validate` on a leaf whose `state_receipts:` line is empty, and on one whose receipts line has a continuation line, exits 3 `malformed-receipts` (`receipts_problem`); `validate` with a directory or a named pipe as `state.md` exits 7 `unsafe-state-file` with `source_revision` null (only the symbolic link is covered for `validate`); a fixture with a structure error and an invariant error lists the structure error first (`command_validate`). New tests only; no amendment of an existing test.

### Do Later
- Robustness (grammar decision, before the first write command): a blank line directly before a fence indented by 1–3 spaces ends the block (`parse_blocks`, the blank-line branch through `continues_after_blanks`), so field lines after the closing fence become unreported foreign lines and `validate` reports `valid`. Reproduction: a leaf with `  notes: a`, a blank line, a fence pair indented by 3 spaces, then `  branch: after` — `get` lists no `branch` and exits 0 with no warning. Decide whether such a fence continues the block, state it in the grammar, and pin it with a test.
- Robustness (needs a contract decision): an indented fence that is never closed makes every later line opaque, so later blocks disappear and `validate` exits 0 `valid` with no warning. Reproduction: leaf `T-01` with `  notes: a` followed by one fence line indented by 3 spaces, then a leaf `T-02` with `atomic-tests: red | execution status `complete`` — `validate` exits 0. A warning or a structure error for a fence that reaches the end of the file needs a code, and the error-code table is closed.
- Robustness (for the write subtasks): `FieldGroup.end` does not cover an in-block fence that follows the group, so "directly after the last line of the last field group" places a new field line before that fence. Decide in the first subtask that inserts a field line whether the fence travels with the preceding group, and pin it with a test.
- Robustness: a continuation line that follows a fence placed directly under the block header is reported as `malformed-block` (no preceding field line); the previous reader treated it as foreign. Confirm this is the intended reading when the grammar text for in-block fences is written down.

### Optional
- Duplication: `command_get` and `command_validate` both select the target block, raise `block-missing` and split structure problems into own and other; extract one selection helper.
- Duplication: `load_document` splits the text and computes fence flags, then `parse_document` does both again; pass the line list and fence openers into the parser.
- Robustness (test): the wording test scans two files for five label families; constraint labels and other product files are outside it, and its pattern would also flag ordinary hyphenated text such as a paper size. Either widen it deliberately to the other families or restrict it to comments and docstrings.

## Improvement Proposals (T-03)

### Do Now
- [batch, not applied] Robustness (tests): add four cases to `tests/state-tool.py` for behaviour that `scripts/state-tool.py` already has and the contract states but no test pins — the receipt entry of a `set` equals the operation id, `#` and the first 16 hex digits of SHA-256 over the compact sorted-key UTF-8 JSON of command, block id and inputs (`input_digest`, `set_inputs`; the later idempotency subtask compares against this value, so its shape must not drift); a `set` on a file with CR bytes, a byte order mark or invalid UTF-8 exits 3 `unsupported-encoding` with the file unchanged; an in-process case where the candidate write, the file sync or the rename raises exits 7 `io-error` with `state.md` unchanged and no temporary file (`replace_state`); a lock path that is a directory or a named pipe exits 7 `unsafe-lock-path` (`acquire_lock`; only the symbolic link is covered). New tests only; no amendment of an existing test.
- [batch, not applied] Robustness: `lock_wait_seconds` (`scripts/state-tool.py:267-272`) converts any run of digits, so a value of more than 4300 digits raises the interpreter's integer-conversion error and the command exits 1 `internal-error` instead of exit 2 `invalid-arguments`. Reproduction: `set … --lock-wait-seconds` followed by 5000 nines. Bound the pattern to one to three digits. Behaviour change — needs a failing case first.

### Do Later
- Robustness (for the receipt subtask): until the 20-entry cap and the operation-conflict refusal exist, a write to a block whose receipts line already holds 20 entries, and a reused operation id with other inputs, are stopped by the candidate re-check with exit 1 `internal-error` and the message "target block does not read back". Nothing is written and no temporary file is created, so this is safe, but the message hides the cause. The receipt subtask should cover both with tests that expect the named outcomes (oldest entry dropped; exit 8), so the internal-error path is no longer reachable from valid input.
- Robustness (for the interruption subtask): an interrupt signal while the command waits for the lock, or between the temporary file and the rename, ends with a traceback and no JSON object on stdout (`main` catches `Exception` only); in the second case the temporary file stays behind. Decide whether an interrupt reports one JSON object and removes the process's own temporary file.
- Robustness: when `state.md` cannot be read at the identity recheck (`scripts/state-tool.py:969-971`, for example removed by another process), the reported result revision falls back to the earlier source revision, although the output contract defines it as the current file revision or null. Report null there.

### Optional
- Readability: changing a header status whose current value is empty (`T-01 | Leaf | atomic-tests: | …`) writes the new value without a space before the next separator (`edit_header`, `scripts/state-tool.py:768-771`); the header still parses and reads back. Insert the space when the old value was empty.
- Performance: `command_set` reads the whole of `state.md` before taking the lock only to refuse a missing or unsafe file (`scripts/state-tool.py:1117`), then reads it again under the lock; an inspection without reading would do.
- Duplication: `load_document` and `command_set` both split the text, find the task contract version and call `contract_version_supported`; extract one helper that returns the version and whether it is supported.
