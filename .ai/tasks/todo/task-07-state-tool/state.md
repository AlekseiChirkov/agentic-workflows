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
- Worker model support for selection (the worker tool does not expose a context window) → the documented 1,000,000-token context of the catalog is confirmed as the support observation; selection uses the current catalog without a refresh (source: user, 2026-11-13).
- Registration of the acceptance suite in `scripts/validate-contracts.sh`, given the frozen validator inventory (raised by T-01 during implementation) → register once in the receipts-grammar subtask (T-09) together with the three contract checks, through one exact, enumerated oracle extension; T-10 refreshes the suite's pinned digest once more; earlier subtasks run the suite directly plus the guard suites; the registration test already in the committed RED set of T-01 is deferred to T-09 (source: user, 2026-11-13; arbiter recommendation with citations: ADR-0018, ADR-0019 Decision 3, ADR-0022 Decision 4, spec REQ-20 / AC-18).

### Description Amendments
- [2026-11-13] Suite registration moved from T-01 to T-09 by owner decision after T-01 found that the frozen validator inventory cannot accept a new check, focused mode or resource row without an oracle extension.
- Original: T-01 step 9 and its last acceptance criterion register the suite (`--state-tool-only` mode and `test_state_tool_acceptance` check) and amend the inventory; T-09 adds only the three contract checks.
- Amended: T-01 leaves `scripts/validate-contracts.sh` unchanged and refreshes only the source-guard fixtures; T-09 registers the suite and performs the one exact oracle extension (targets gain `tests/fixtures/validator-runtime/oracle.py` and `tests/validator-runtime-oracle.py`); T-10 refreshes the suite's resource row and the amendment digest; T-02–T-08 verify with the suite run directly. The spec is unchanged.

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
  pr: none

T-02 | Static validation command | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-03 | Set write transaction | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

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
