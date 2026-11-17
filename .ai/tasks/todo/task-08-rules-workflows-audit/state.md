spec_path: .ai/specs/08-rules-workflows-audit.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Specification numbers → the names in force since the renumbering of 2026-11-16 are used everywhere: this specification is 08, the naming migration 09, context tiering 11, and proposal owners are 11, 12, 13, 14, 15 (source: `.ai/specs/README.md → ## Renumbering — 2026-11-16`; ADR-0023).
- Line citations in the specification that have drifted (ledger row cited at `:214`, now `:208`; "docs/audits/ does not exist", now an empty untracked directory; "11 `.sh` and 30 `.py`", now 11 and 31; `docs/README.md:13-20`) → the requirement stands and the subtask that uses a fact re-verifies it at the commit it works on; the extractor reads the live tree and takes no count from a record (source: spec REQ-01; `rule-phase-discovery → ## Codebase Reading Rules`).
- "Run no model" (REQ-04) → it binds the tool and the inventory; the auditor that reads the files and writes the assessment is the pipeline's Implementer role, and the independent reviewer its Validator role (source: spec Actors & Roles; Notes → Prerequisites and Guard).
- Test level → `unit` and `integration` through the standalone `unittest` suite in `scripts/`, never registered in the validator; assessment subtasks take `verify` diagnostics located in their files as RED (source: spec REQ-24, Notes → Implementation order; ADR-0019 Decision 3; `.ai/principles/architecture.md` P7).
- `run_date` → the calendar date of the clean extraction; the three output names and the assessment share it (source: spec DM-7, DM-9 `report-name-date`).
- Extraction order → the tool and suite are committed before extraction; index and knowledge edits come after it, because they are readers and `--strict` is run on a checkout of `source_revision` (source: spec Notes → Prerequisites and Guard).
- One writer of the assessment → reading may be split by file group, but each assessment subtask is sequential and writes the single assessment file (source: P4; spec Edge Cases "Concurrent writers").
- Review line → written after the independent review passes, naming the reviewed commit; the acceptance line stays `Accepted: pending` (source: spec REQ-14, DM-8, AC-10).
- Knowledge entries in `.ai/memory/state.md` and `.ai/memory/progress.md` → written inside the delivery because AC-24 checks them, in the last subtask (source: spec REQ-26, AC-24).
- Installed-copy comparison → not performed; `installed_access: not-verified` (source: spec A-10; owner's rule not to touch deployed copies).
- No ADR → none is required for this delivery; amendments that alter an accepted decision carry `requires_adr` for the later reconciliation of the naming-migration specification (source: spec A-17).
- Branch → Discovery artifacts are written on `docs/discover-rules-workflows-audit`, created from `main` at `cc632f4` (source: repository rule to branch before changing files on the default branch).
- flow: full — gate: 1fail 2fail 3pass 4pass (more than three files; a new tool with a new data contract) (source: `rules/quick-flow.md → ## The escalation gate`).
- Data-contract names that embed specification numbers (`blocks_09`, `in_spec09_grammar`, `spec09_default`, `spec09-unavailable`, `AUD-08-NNN`, `08-extract-1`) → used verbatim in the tool and outputs because the specification fixes them; comments, docstrings and test names state rules in words without requirement, criterion or specification labels (source: spec DM-1, DM-4, DM-7, DM-9; owner ruling of 2026-11-13 on specification labels in product code; P8).
- Stack base → the stack is built on `feat/multi-repository-spec-run` (draft PR #104 into `main`, tip `488edb1`), not on `main`, so the audit covers the multi-repository changes to rules and workflows; that PR merges first. The permitted-changes check of the delivery is computed against `488edb1`, not `main` (source: user, 2026-11-17).
- Absolute home paths in copied text → the tool rewrites `/home/<name>/` and `/Users/<name>/` to `~/` in every text it copies from audited files (full-output, harness-name and legacy `text`, duplicate unit text) before hashing, so outputs satisfy REQ-25/AC-22 and clusters stay intact; `method_version` stays `08-extract-1` because no output was ever produced under the unamended rule; DM-6 is amended by `/spec-sync` in Validation; the assessment records an `other` finding owned by `owner` for the absolute paths in `rules/global-claude.md` and `templates/codex-global-AGENTS.md` (source: user, 2026-11-17, question raised by T-03 during Execution).

## Open Questions (batch)
None

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10

## Subtask Progress

T-01 | Inventory extractor | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — DoD met (8/8 acceptance criteria, 43/43 tests, RED set intact), V1–V3 and V5 resolved, three optional findings V8–V10 recorded; plan.md `reviewed` returned as a delta; previous: pav-propose done — batch: 2 Do Now, 2 Do Later, 2 Optional recorded, none applied; previous: pav-check DONE — re-validation after rework: V1, V2, V3 reproduced as fixed, V5 fixed for fsmonitor; no critical or important finding; previous: rework GREEN — V1, V2, V3, V5 fixed and V4 documented; 43/43 tests pass; previous: rework RED reached — 4 added tests fail for V1, V2, V3, V5; previous: pav-check NEEDS WORK — three important error-path defects (exit contract broken or inventory silently incomplete); all eight acceptance criteria met; previous: pae-finalize done — read-only `extract` writes the deterministic inventory (audited set with digests, encoding, words, front matter, invocation lines and sections; classified readers; git revision, tracked and work-tree state; inventory digest; empty later lists) by atomic replacement, with exit 2 and one ERROR line for usage, root-invalid, out-unwritable and the runtime guard
  target_files: scripts/check-audit-instructions.py, scripts/audit-instructions.py
  blocker: none
  notes: tdd: unit, integration — 39 tests (42 with subtests), AC coverage 8/8; test command `MISE_PYTHON_VERSION=3.12.16 python3 -I scripts/check-audit-instructions.py` (standalone suite per task Assumptions; runbook `test:` is the frozen validator, which must not register it); every case fails because scripts/audit-instructions.py does not exist yet
         tdd: red digest — four-path root → test_extract_lists_exactly_the_audited_entries_of_a_four_file_root, test_codex_global_template_is_the_only_audited_template, test_inventory_has_the_documented_keys_in_order_and_empty_later_lists, test_default_root_is_the_parent_of_the_scripts_directory; determinism and digest → test_two_extractions_are_byte_identical_and_digest_is_independently_reproducible, test_inventory_text_is_canonical_json_with_relative_paths_only, test_digest_of_a_root_with_no_entries_is_the_digest_of_empty_text; symbolic links → test_symbolic_links_are_rows_with_null_digests_and_are_never_followed, test_other_entry_is_recorded_without_being_opened; reader classes and exclusions → test_each_reader_gets_the_first_matching_class, test_audit_outputs_own_scripts_skipped_and_unclassed_files_are_not_readers, test_reader_that_is_not_utf8_is_recorded_as_not_decoded; read-only → test_extract_changes_nothing_but_the_out_file, test_existing_out_file_is_replaced_without_leftover_temporary_files; runtime guard and source shape → test_interpreter_older_than_three_eleven_gets_the_guard_message_and_exit_two, test_tool_starts_with_docstring_future_import_sys_import_and_version_guard, test_tool_imports_only_standard_library_modules, test_every_tool_function_is_fully_annotated; text model → test_front_matter_fences_crlf_and_preamble_give_documented_sections; standalone → test_tool_exists_and_neither_validator_nor_sync_names_it (its no-mention half already holds as an off-limits invariant; the case fails on the missing tool); edge → test_file_starting_with_a_level_two_heading_has_no_preamble, test_empty_file_has_zero_words_and_no_sections, test_final_line_without_newline_is_counted, test_unclosed_front_matter_leaves_the_whole_file_as_body, test_unclosed_fence_runs_to_the_end_of_the_file, test_indented_tilde_fence_closes_only_on_a_run_at_least_as_long, test_byte_order_mark_is_kept_and_front_matter_reads_absent, test_invalid_utf8_audited_file_has_digests_but_no_text_model, test_control_character_audited_file_has_no_word_count, test_decodable_non_markdown_file_has_words_but_no_markdown_fields, test_clean_commit_records_revision_and_tracked_files_ignoring_excluded_changes, test_dirty_tree_lists_changed_audited_and_reader_paths_in_path_order, test_root_that_git_cannot_read_yields_null_revision_and_unknown_worktree, test_missing_git_program_yields_null_revision_and_unknown_worktree, test_root_without_rules_directory_is_invalid, test_missing_root_is_invalid, test_out_in_a_missing_directory_is_unwritable, test_out_naming_a_directory_is_unwritable_and_leaves_no_temporary_file, test_usage_errors_print_one_error_line_and_exit_two
         interpretations frozen by the tests: an unclosed front matter reports keys [], trigger and description null, continuation_lines 0; a level-2 heading is `## ` at column 0; a root lacking either rules/ or workflows/ is root-invalid
         arbiter: unclosed front matter → status `unclosed`, keys [], trigger/description null, whole file is body (source: spec DM-5 Front matter; Edge Cases "Front matter without closing"; DM-2 front_matter enum)
         arbiter: only column-0 `## ` outside fences and front matter starts a section (source: spec DM-5 Headings and Sections; DM-4 G1 form 2; rules/workflow-globals.md wrapped `  ## Mid-flight escalation` line)
         arbiter: root-invalid when either rules/ or workflows/ is missing or the root does not exist (source: spec Contracts & Interfaces extract row; Terminology → Primary set; DM-4 node names)
         tdd: green — 39/39 frozen tests pass unchanged (test file identical to ed5def1); no test amended, none added
         verification 2026-11-17: suite 39 OK in ~1.8 s; `MISE_PYTHON_VERSION=3.12.16 bash scripts/validate-contracts.sh` 721 passed / 0 failed / 2 skipped; `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing; lint: runbook command covers shell only (not applicable to the two Python files), py_compile clean; typecheck: none configured (annotation case in the suite passes); build: not run (sync is off-limits for this task)
         implementation choices not fixed by tests: `.git`, `logs`, `output`, `__pycache__` pruned by directory name at any depth; a status path counts toward `worktree.paths` when it is a listed audited or reader path, or when it is gone from disk and classifies as audited or reader by location (deletions make the tree dirty); git runs without inherited GIT_* variables; root assumed to be the git top level; an unreadable entry yields exit 2 `root-unreadable`
         smoke on this checkout: 61 audited files (56 primary, 5 adapter), 519 readers, two runs byte-identical, no absolute path in the output
         architecture: no update proposed — the specification permits only the inventory sentence of `.ai/memory/architecture.md`, owned by the index-and-knowledge subtask
         validation 2026-11-17 (pav-check): verdict NEEDS WORK. Acceptance criteria 8/8 met; RED digest intact (39 names in suite equal the 39 digest names; `git diff ed5def1 HEAD -- scripts/check-audit-instructions.py` empty; no skip/xfail added — the one `skipTest` is the pre-existing git-missing guard); suite 39 OK in 1.8 s; grep of validator and sync prints nothing; diff touches only the two target files; commits carry no attribution or planning ids; smoke on this checkout 61 files / 519 readers, two runs byte-identical, no absolute path, section word and byte sums equal file totals for every audited file
         validation finding (important) V1: `validate_root` runs outside the OSError handler and `is_real_directory` catches only FileNotFoundError/NotADirectoryError, so a root that cannot be searched (mode 000) ends in a PermissionError traceback, exit 1, with the absolute path on stderr — outside the documented 0/2 exit contract; repro: `mkdir -p R/rules R/workflows; chmod 000 R; extract --root R --out O` → rc 1
         validation finding (important) V2: `reader_paths` uses `os.walk` without `onerror`, so an unreadable directory among readers is skipped silently and extract exits 0 with an incomplete `readers` list, while the same condition under an audited directory exits 2 `root-unreadable`; repro: `docs/sub` mode 000 holding `a.md`, `docs/b.md` readable → rc 0, readers ['docs/b.md']
         validation finding (important) V3: a file name that is not valid UTF-8 (surrogate-escaped by scandir/os.walk) reaches `inventory_digest`/`json` writing and raises UnicodeEncodeError, traceback exit 1; repro: `rules/bad-\xff.md` → rc 1; the spec requires UTF-8 JSON paths but defines no behaviour, so the tool should refuse with exit 2 and one ERROR line
         validation finding (optional) V4: porcelain v1 status paths are relative to the repository top level while `ls-files` paths are relative to `-C <root>`; a root below the top level of an enclosing repository gets mismatched `worktree.paths` (recorded choice "root assumed to be the git top level"; reasoned from git documentation, not reproduced — git writes are not allowed in validation)
         validation finding (optional) V5: `git status` runs a repository-configured `core.fsmonitor` program; passing `-c core.fsmonitor=false` keeps the permitted command while honouring "never execute repository content"
         validation finding (optional) V6: front-matter `continuation_lines` skips whitespace-only lines (`text.strip()`), while DM-5 says "any other non-empty line"; no test pins either reading
         validation finding (optional) V7: `root-unreadable` as an extract exit-2 code is an extension of the spec's extract row (listed there only for verify); keep it documented or record it via spec-sync
         tdd: rework red 2026-11-17 — added (original 39 byte-for-byte unchanged): V1 → test_root_that_cannot_be_searched_is_reported_as_unreadable (PermissionError traceback, exit 1); V2 → test_unreadable_directory_among_readers_is_reported_instead_of_skipped (exit 0, silent skip); V3 → test_file_name_that_is_not_utf8_is_refused_without_writing, subtests rules and docs (UnicodeEncodeError, exit 1); V5 → test_repository_configured_fsmonitor_program_is_never_run (marker written by the fsmonitor program); suite 43 run, exactly these 4 fail (5 failures with subtests)
         tdd: rework green 2026-11-17 — 43/43 pass (39 original + 4 added, test file identical to 1f47f4e); no test amended. Fixes: V1 root validation runs inside the read-error handling and a permission error now propagates from the directory check → exit 2 `root-unreadable` with strerror only; V2 the reader walk raises on an unreadable directory; V3 audited, reader and work-tree paths are checked for UTF-8 before any digest or write → exit 2 `root-unreadable: a file name is not valid UTF-8: <escaped relative path>`; V5 every git call adds `-c core.fsmonitor=false -c core.hooksPath=/dev/null`; V4 docstring states the root is taken as the git top level; V6 and V7 unchanged as instructed
         verification 2026-11-17 (rework): standalone suite 43 OK in ~2.0 s; smoke on this checkout 61 files / 519 readers, two runs byte-identical, no absolute path; full validator not rerun (only the two target files changed)
         re-validation 2026-11-17 (pav-check): verdict DONE. Acceptance criteria 8/8 met. Test integrity: the 39 digest names equal the 39 test names of ed5def1; lines 1–791 of the suite at HEAD are byte-identical to ed5def1 and 1f47f4e only appends two classes (80 insertions, 0 deletions); `git diff 1f47f4e HEAD -- scripts/check-audit-instructions.py` is empty; the 4 rework tests carry a RED record; skips are environment guards only (git missing, superuser). Suite 43 OK in 2.3 s; `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing; diff 488edb1..HEAD touches only the two target files; four commits carry no attribution or planning identifier; smoke on this checkout 61 files / 519 readers, default and `--root .` runs byte-identical, no `/home/` in the output, section word and byte sums equal file totals for every audited file; py_compile clean; lint: runbook lint is shell-only (not applicable); full validator not run (instructed)
         re-validation reproductions: V1 root mode 000 and root mode 0644 → exit 2 `root-unreadable: cannot read the root (Permission denied)`, no out file, no path on stderr — resolved; V2 `docs/sub` mode 000 → exit 2, no out file — resolved; V3 `rules/bad-\xff.md` and `docs/d\xfe/a.md` → exit 2 `root-unreadable: a file name is not valid UTF-8: <relative escaped path>`, no out file, while a non-UTF-8 name at an unclassified or skipped location (`VERSION\xff`, `logs/\xff`) is ignored with exit 0 — resolved; V5 a repository-configured `core.fsmonitor` program is not run and the tree reads dirty correctly — resolved for fsmonitor (see V9); V4 documented in the docstring; V6, V7 unchanged as instructed
         re-validation finding (optional) V8: `audited_paths` tests `templates/codex-global-AGENTS.md` with `os.path.lexists`, which swallows a permission error; with `templates/` readable but not searchable (mode 0644) and holding no other reader file, extract exits 0 and the adapter file is silently missing from `files` (repro: fixture with only that file under `templates/`, `chmod 644 templates` → rc 0, files lack it; mode 000 → rc 2). Graded optional, not important like V2, because any other file under `templates/` is a reader whose `lstat` raises and turns the run into exit 2, so a realistic root cannot reach the silent path; fix is `os.lstat` with only FileNotFoundError/NotADirectoryError treated as absent
         re-validation finding (optional) V9: `git status` still runs a repository-configured clean filter driver (`filter.<name>.clean` selected by `.gitattributes`) when it rehashes a file whose stat data changed (repro: filter writes a marker; `touch` an audited file; extract → marker written, rc 0); the docstring's "so no program named by the repository's configuration runs" overclaims — correct the sentence, or neutralise attributes for the status call
         re-validation finding (optional) V10: the reader walk prunes only `.git`, `logs`, `output` and `__pycache__`, so an unreadable directory that can hold no reader (repro: root-level `misc/` mode 000) makes extract exit 2 `root-unreadable` although nothing in it would be read; the specification defines no behaviour for this, and refusal is the conservative reading
         proposals (batch, recorded, none applied; section returned to the orchestrator as a delta): Do Now — P1 adapter-file presence via `os.lstat` so a permission error surfaces (V8), P2 correct the docstring's read-only sentence about configured programs (V9); Do Later — P3 roots below the git top level (V4, needs a specification decision), P4 record `root-unreadable` for extract by spec-sync (V7); Optional — P5 prune the reader walk to classifiable prefixes (V10), P6 settle whitespace-only front-matter lines (V6)
         re-validation process note: the V5 and V9 reproductions created and committed to two throwaway git repositories under the session scratchpad (fixture writes, as the suite itself does); no git write touched this repository
  branch: feat/instruction-audit-inventory
  base_branch: feat/multi-repository-spec-run
  base_commit: 488edb11b37c3028b720d7de06cfe64cf7fe30c1
  commits: ed5def1 test(audit): cover the deterministic inventory of instruction files, a95fc36 feat(audit): extract a deterministic inventory of instruction files, 1f47f4e test(audit): cover unreadable roots, undecodable names and git isolation, d2dcc6c fix(audit): refuse unreadable roots and undecodable file names
  pr: #105 draft

T-02 | Reference edges | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — DoD met (7/7 acceptance criteria, 65/65 tests, RED set intact), no critical or important finding, seven optional findings V1–V7 recorded; plan.md `reviewed` and state compression returned as deltas; previous: pav-propose done — batch: 1 Do Now, 2 Do Later, 3 Optional recorded, none applied; previous: pav-check DONE — all seven acceptance criteria met, RED digest intact, grammar corner cases, arbiter resolutions and exit contract checked; previous: pae-finalize done — `extract` records every reference edge to audited files with form, context, status, flags and targets, ordered by source, line and column, and exposes the defect predicate `is_defect_edge`; plan.md `done` and state compression returned as deltas; previous: all steps complete — `extract` now records every reference edge (span grammar, heading resolution through extents, token grammar with masking, statuses, contexts, load flag, grammar flag) ordered by source, line and column, and exposes `is_defect_edge`; previous: completed steps 2–10 — node names, span grammar, heading resolution, token grammar, statuses, contexts, load flag and defect predicate implemented; suite 65/65 pass; previous: RED reached — 22 failing tests written (unit, integration); the 43 existing tests pass unchanged
  target_files: scripts/check-audit-instructions.py, scripts/audit-instructions.py
  blocker: none
  notes: tdd: unit, integration — 22 tests (26 failures with subtests), AC coverage 7/7; test command `MISE_PYTHON_VERSION=3.12.16 python3 -I scripts/check-audit-instructions.py` (standalone suite per task Assumptions); every new case fails on an empty `edges` list or on the missing `is_defect_edge` function, 0 errors; the 43 existing tests are byte-for-byte unchanged and pass (suite diff: two docstring lines reworded for the module load of the predicate, two imports, one appended block)
         tdd: red digest — control example → test_section_reference_to_a_heading_the_rule_lacks_is_a_missing_heading_defect; every form and status → test_command_spans_resolve_workflow_stems_and_report_unknown_commands, test_section_reference_candidates_follow_the_head, test_heading_components_resolve_inside_the_current_extent, test_rule_name_spans_resolve_only_rules, test_path_spans_resolve_audited_paths_globs_and_skip_placeholders, test_bare_name_spans_match_any_stem_and_report_shared_stems, test_token_forms_in_text_resolve_in_order_with_masking, test_span_that_no_span_form_matches_is_scanned_by_tokens, test_non_markdown_sources_use_only_the_token_grammar, test_defect_predicate_follows_class_context_form_status_and_suffix; slash section reference and suffix flags → test_slash_prefixed_section_reference_is_a_section_ref_never_a_command; grammar flag and document reference → test_grammar_flag_holds_only_for_span_forms_in_top_level_instruction_files, test_token_found_inside_an_unmatched_span_is_never_in_the_grammar, test_section_reference_candidates_follow_the_head; validator contexts → test_validator_check_descriptions_and_comments_get_their_contexts; fence, planning and history → test_front_matter_and_fence_references_get_their_contexts, test_planning_history_and_frozen_references_are_recorded_but_never_defects; load line → test_span_edges_on_load_lines_of_audited_markdown_are_load_edges; edge → test_tokens_need_whole_token_boundaries_and_hyphenated_stems, test_crlf_lines_match_without_the_carriage_return, test_undecodable_sources_add_no_edges_and_undecodable_candidates_have_no_headings, test_edges_have_documented_keys_and_are_ordered_by_source_line_and_column
         interpretations frozen by the tests: (1) a span containing ` → ` whose head has the section-ref shape but names no candidate and is not a bare token before a `#`-marked component is consumed with no edge and is not rescanned by the token grammar (`rules/zz-gone.md → ## X`, `state.md → ## X`); (2) a `check ` line may be indented, and the first double-quoted string honours backslash escapes; (3) an unmarked first component that matches a heading makes that heading's extent current for later marked components; (4) a candidate without a text model (symlink, invalid UTF-8, control characters) has no headings, so a marked component is `missing-heading`; a symbolic link under rules/ still names a stem; (5) the defect predicate is the function `is_defect_edge(edge)`, called by loading the tool's source as a module
         arbiter: (1) confirmed — a section-ref-shaped span with no candidate and no bare-token-plus-marked head is consumed with no edge (source: spec DM-4 G1 form 1 → form 2 and "first match wins"; "any other head is a document reference and yields no edge")
         arbiter: (2) confirmed — indented `check ` lines count and the first quoted string honours backslash escapes (source: spec DM-4 "line-initial `check `", read through spec 09 DM-17 "every `check "<description>"`"; escape pattern in tests/fixtures/validator-runtime/oracle.py)
         arbiter: (3) confirmed — the matched heading's extent becomes current after an unmarked first component; when several headings match, the first in line order is used, because resolution runs from the start of the file (source: spec DM-4 "the matched heading's extent becomes the current extent"; first in line order is an inference)
         arbiter: (4) confirmed — a candidate without a text model has no headings; a symbolic link names a stem but is never read (source: spec DM-5 headings come only from decoded text; DM-2 non-decodable files have no sections; REQ-15 no symlink reads)
         arbiter: grammar flag — token-grammar edges found inside a span that matched no span form keep context `span` but always have `in_spec09_grammar: false`; the flag is true only for span-grammar command, section-ref with a spec 09 form-2 head, rule-name and non-glob path edges in top-level instruction files (source: spec REQ-29; DM-4 `in_spec09_grammar` "the pre-existing defects spec 09 fixes … Otherwise false"; spec 09 DM-16 anchored forms; change-log entry "narrowed to spec 09 DM-16 form 2 heads"); pinned by test_token_found_inside_an_unmatched_span_is_never_in_the_grammar
         tdd: green — 65/65 pass (43 earlier + 22 RED, suite identical to f304c35); no test amended, none added
         verification 2026-11-17: standalone suite 65 OK in ~3.6 s; py_compile clean; `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing; lint: runbook lint is shell-only (not applicable); typecheck: none configured; build and full validator not run (only the two script files changed; sync is off-limits); fuzz of 40 random fixture roots with backticks, arrows, fences, CR, BOM and quotes → exit 0 every time; unreadable reader file → exit 2 `root-unreadable`, no out file
         smoke on this checkout: 61 files, 519 readers, 6887 edges (resolved 6076, ambiguous-stem 199, missing-path 299, missing-target 191, unknown-command 71, missing-heading 23, glob-empty 12, heading-unmarked 11, resolved-prefix 5); 487 defect edges, 65 load edges, 857 grammar-flag edges; default and `--root .` runs byte-identical; no `/home/` in the output; extract ~2.9 s
         implementation choices not fixed by tests: the audited-tree walk also records real directories, so the existing-directory check never stats through a link; a component split is on every ` → `, so a heading whose text itself contains ` → ` (`rules/quick-flow.md:137` `## Mid-flight escalation (quick → full)`, cited from `workflows/bugfix.md:104` and `workflows/phase-execution.md:97`) yields `missing-heading` and an in-grammar defect — correct on reading, left to the assessment as an accepted observation; for load lines each span with its backticks is replaced by one space; ` rule`/` rules` after a span must end at a word boundary; globs match every audited path, symlinks included; reader bytes are read once and reused for digests and edges
         architecture: no update proposed — `.ai/memory/architecture.md` does not name the tool, and the specification permits only its inventory sentence, owned by the index-and-knowledge subtask
         validation 2026-11-17 (pav-check): verdict DONE. Acceptance criteria 7/7 met (control example, every form and status, slash section reference and suffix flags, grammar flag by source and document reference, validator contexts, fence/planning/history never defects, load lines). Test integrity: `git diff f304c35 HEAD -- scripts/check-audit-instructions.py` is empty; `git diff f867e18 f304c35` touches only the module docstring (two lines), two imports and one appended block, so the 43 earlier test bodies are unchanged; the 22 test names after the appended marker equal the 22 RED-digest names; no skip/xfail added (the three `skipTest` calls are the pre-existing git-missing and superuser guards). RED reproduced independently: the suite of f304c35 against the tool of f867e18 (exported with `git archive`) fails exactly the 22 digest tests (26 failures with subtests), 0 errors, the 43 earlier tests pass. Suite at HEAD 65 OK in 4.6 s; `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing; diff f867e18..HEAD touches only the two target files; both commits carry no attribution or planning identifier; no unused import; every function annotated (suite case passes); lint: runbook lint is shell-only (not applicable); full validator not run (instructed)
         validation evidence: smoke on this checkout 61 files, 519 readers, 6891 edges (the 4 more than the execution record come from the uncommitted task state and plan edits, both planning readers), 487 defect edges; default and `--root .` runs byte-identical; no `/home/` in the output; ~4.9 s. Spot checks: the 7 active `missing-heading` edges cite bold paragraph labels or the arrow-in-heading case, never a real heading; the 8 in-grammar defects are 6 `ambiguous-stem` section references with a `phase-atomic-execution`/`phase-discovery` head and the 2 recorded arrow-in-heading cases. Own fuzz: 60 random roots (backticks, arrows, fences, CR, BOM, quotes, control characters, tabs, non-ASCII) → exit 0, two runs byte-identical, edges strictly ordered and unique, `raw` found at `column` in every edge. Exit contract: no new read path (outlines reuse the bytes already read); unreadable reader or audited file → exit 2 one ERROR line, no out file, no traceback; dangling symbolic link under rules/ names a stem and resolves `missing-heading` without being read. Arbiter resolutions (1)–(4) and the grammar-flag ruling reproduced as recorded
         validation finding (optional) V1: the token literal `templates/codex-global-AGENTS.md` has a left boundary but no right one, so `templates/codex-global-AGENTS.md.bak` in text resolves to the adapter file, while `rules/x.md.bak` is taken whole and reads `missing-path`; the specification gives the literal no boundary (repro: line `A templates/codex-global-AGENTS.md.bak` in a reader with the adapter present → path edge `resolved`)
         validation finding (optional) V2: with two equal headings, a marked component resolves to the first in line order and never tries the next, so `dup → ## A → ### Y` is `missing-heading` when `### Y` sits under the second `## A`; the specification does not define duplicate headings (arbiter (3) covers only unmarked components)
         validation finding (optional) V3: components are not trimmed and may be empty: `` `r-one → ## Step 1 ` `` (trailing space) and `` `r-one → ` `` read `missing-heading`; the specification trims only the heading line
         validation finding (optional) V4: a run of three or more backticks inside a line is paired tick by tick (`` ```w-one``` `` gives the span `w-one`); the specification defines only single and double backticks
         validation finding (optional) V5: a `check "` string without a closing quote runs to the end of the line as `check-description`, and any non-quote text may stand between `check ` and the quote; the specification does not define either case
         validation finding (optional) V6: the fixture heading `## Codebase Reading Rules` repeats a real heading of this repository; stems are synthetic as required, but the heading text is not; changing it is a test amendment that needs a recorded reason
         validation finding (optional) V7: headings whose text contains ` → ` cannot be cited (already recorded as an implementation choice; two in-grammar defect edges on this checkout); left to the assessment as an accepted observation or to the naming-migration grammar
         proposals (batch, recorded, none applied; section returned to the orchestrator as a delta): Do Now — P1 give the adapter literal the same right boundary as the other path tokens (V1); Do Later — P2 settle duplicate headings, untrimmed and empty components by spec-sync (V2, V3), P3 headings containing ` → ` (V7, needs a decision with the naming-migration grammar); Optional — P4 synthetic fixture heading with a recorded test amendment (V6), P5 runs of three or more backticks (V4), P6 unclosed check strings (V5)
         validation process note: fixtures, the RED reproduction tree and outputs live under the session scratchpad `val-t02`; no git write touched this repository; permissions changed on fixtures were restored
  branch: feat/instruction-audit-reference-edges
  base_branch: feat/instruction-audit-inventory
  base_commit: f867e186967167dfa1a965b8958daa023441e365
  commits: f304c35 test(audit): cover reference edges between instruction files, 200098f feat(audit): record reference edges between instruction files
  pr: #106 draft

T-03 | Candidates, legacy mentions and duplicate clusters | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close done — DoD met (6/6 acceptance criteria, 81/81 tests, RED set intact and reproduced), no critical or important finding, six optional findings V1–V6 recorded; plan.md `reviewed` returned as a delta; previous: pav-propose done — batch: 1 Do Now, 2 Do Later, 2 Optional recorded, none applied; previous: pav-check DONE; previous: pae-finalize done — `extract` records repeated loads of call pairs, full-output and harness-name lines, legacy mentions and verbatim duplicate clusters, with home directory prefixes in copied text written as `~/`; plan.md `done` and state compression returned as deltas; previous: all steps complete — `extract` fills repeat_loads, full_output, harness_names, legacy_mentions and duplicate_clusters by the call-clause, line-candidate, legacy and text-unit rules, with home directory prefixes in copied text written as `~/`; suite 81/81; previous: completed steps 2–9 — `extract` now fills repeat_loads, full_output, harness_names, legacy_mentions and duplicate_clusters; suite 79/79 pass (RED set unchanged); final verification stopped on the output-hygiene check; previous: RED reached — 14 failing tests written (unit, integration); the 65 existing tests pass unchanged
  target_files: scripts/check-audit-instructions.py, scripts/audit-instructions.py
  blocker: none
  notes: tdd: unit, integration — 14 tests (35 failures with subtests), AC coverage 6/6; test command `MISE_PYTHON_VERSION=3.12.16 python3 -I scripts/check-audit-instructions.py` (standalone suite per task Assumptions); every new case fails on an empty candidate list (assertion, 0 errors); the 65 existing tests are byte-for-byte unchanged and pass (suite diff: one appended block of 411 lines after the last test class)
         tdd: red digest — call fixture → test_calls_between_invocable_workflows_that_share_a_load_are_repeat_loads; negation, stop marker, verb-less mention and negation outside the verb clause → test_only_a_call_verb_without_earlier_negation_or_stop_marker_makes_a_call; candidate lines → test_full_output_and_harness_name_lines_of_audited_markdown_are_candidates; legacy terms → test_legacy_terms_in_a_rule_yield_two_mentions_and_not_a_longer_devin_word; shared sentence at and below the threshold → test_sentence_of_eight_words_shared_by_two_rules_is_one_cluster_and_seven_none; repeat run → test_candidate_lists_have_documented_keys_and_repeat_runs_are_byte_identical; edge → test_each_shared_single_target_load_of_a_call_pair_is_one_candidate, test_commands_that_are_not_workflow_calls_add_no_candidates, test_candidate_lines_are_numbered_by_source_and_line_with_collapsed_and_cut_text, test_legacy_mentions_cover_whole_audited_markdown_and_json_files_only, test_quote_indentation_and_list_markers_are_stripped_and_lines_joined, test_paragraphs_split_into_sentences_after_terminal_punctuation, test_unit_repeated_in_one_file_and_cluster_order_follow_first_member, test_headings_separators_fences_front_matter_and_other_files_give_no_units
         interpretations frozen by the tests: (1) `caller` and `callee` are repository-relative workflow paths (`workflows/w-a.md`), like `target`; (2) a clause with several call verbs is a call when no negation precedes its first verb, so a negation after the verb ("Run it and never skip `/x`") does not block; (3) spans, matched or not, are blanked before the clause delimiters are searched; (4) FO/HN ids run in source path then line order, and a line matching both is in both lists; (5) legacy mentions are taken from the whole decoded audited `.md`/`.json` file, front matter and fences included, ordered by source, line, column; (6) a DUP member's `line_start`/`line_end` are the lines of the unit's first and last word; `sha256` is over the unit text's UTF-8 bytes and `words` is `len(text.split())`; (7) a table row is one unit and is never split at sentence punctuation; (8) list markers `[-*+] ` and `\d+[.)] ` are stripped after an optional `>` and indentation
         implementation choices not fixed by tests: callers are top-level `workflows/<stem>.md` files only; the `**stop**` marker is searched in the line before the edge's column; FO/HN/legacy text is collapsed with its ends stripped before the cut to 160 code points; a table row's text is whitespace-collapsed; heading, fence, front-matter and table lines end a paragraph; pipes count as words in a table row; members and clusters that tie on path and lines keep reading order; legacy, FO and HN use files whose `encoding` is `utf-8`
         arbiter: (1) confirmed by inference — `caller`/`callee` are repository-relative workflow paths: calls are command edges whose `source` and `targets[].path` are paths, and AC-17 uses stems only as prose labels (source: spec DM-6 Repeated loads; DM-4 edge entry; Data Model preamble "Paths are repository-relative POSIX strings"; AC-17)
         arbiter: (2), (3) confirmed — negation counts only before the first verb of the clause, and every span is blanked before delimiters are searched (source: spec DM-6 clause definition "With spans replaced by spaces (positions kept)"; Edge Cases row "A negation elsewhere on a calling line")
         arbiter: (5) confirmed; order and column by inference — legacy mentions cover the whole file including fences and front matter, ordered by source, line, column, with column as in DM-4 (0-based code points, trailing CR removed); only files whose `encoding` is `utf-8` (source: spec REQ-18 "every case-insensitive match"; DM-6 Legacy mention; DM-4 `column`; DM-2 `encoding`). Correction: duplicate units and repeated-load calls also exclude fences and front matter, not only FO/HN (source: DM-6 Duplicate clusters "outside front matter and fences"; DM-6 calls take contexts `span` or `text` only)
         arbiter: (6) confirmed; member line bounds by inference — `line_start`/`line_end` are the lines of the unit's first and last word (source: spec DM-6 Duplicate clusters member shape)
         arbiter: (4) by inference — FO/HN ids follow source path then line order, and a line matching both patterns is in both lists (source: Data Model preamble path-order convention; NFR Determinism)
         arbiter: (7) confirmed; table-row whitespace is not settled by the specification — one choice (whitespace runs collapsed, ends stripped) is applied to every row on both sides of the comparison (source: spec DM-6 "A table row … is one unit")
         tdd: green set — 79/79 pass (65 earlier + 14 RED, suite identical to f375b8d); no test amended, none added; atomic-tests stays `red` because final verification is blocked
         verification 2026-11-17: standalone suite 79 OK in ~5.6 s; py_compile clean; no line over 100 characters; spec examples reproduced on this checkout — `workflows/pd-finalize.md:113` and `workflows/pd-decompose.md:14` are not calls, `workflows/phase-pipeline.md:105` and `workflows/pav-close.md:64` are
         smoke on this checkout: 61 files, 519 readers, 6907 edges; repeat_loads 21, full_output 9, harness_names 38, legacy_mentions 8, duplicate_clusters 64; default and `--root .` runs byte-identical; no former repository name, no `/Users/`; one `/home/` occurrence (DUP-021, see blocker); extract ~2.2 s
         decision 2026-11-17 (owner, option A): every text copied from audited files — FO, HN and legacy `text` and duplicate unit text — rewrites `/home/<name>/` and `/Users/<name>/` to `~/` before cutting, comparing and hashing; `method_version` stays `08-extract-1`; the DM-6 amendment is left to spec-sync during validation
         tdd: rework red 2026-11-17 — added (79 committed tests byte-for-byte unchanged, one appended class of 45 lines): home prefixes in copied text → test_home_directory_prefixes_in_copied_text_become_tilde_paths (cluster across different user names, sha256 over rewritten text, FO/HN/legacy text, no `/home/` or `/Users/` in the output); rewrite precision → test_home_rewrite_needs_a_home_directory_and_a_name_segment (`/homestead/x`, `/home/ alone`, `/Users/ too`, `~/kept/y` unchanged, `/home/someone/z` → `~/z`); suite 81 run, exactly these 2 fail on verbatim home paths (assertion, 0 errors)
         orchestrator: the home-path rewrite tests use synthetic placeholder prefixes (`/home/someone/`, `/Users/someone/`) as fixture input; accepted as the only way to exercise the rewrite — they name no real machine path, and the outputs the tests check contain none
         tdd: green — 81/81 pass (65 earlier + 14 RED + 2 rework RED; suite identical to 1990c41); no test amended, none added; blocker cleared by the owner's option A
         verification 2026-11-17 (rework): standalone suite 81 OK in ~6.0 s; py_compile clean; no line over 100 characters; lint: runbook lint is shell-only (not applicable); typecheck: none configured; full validator not run (only the two script files changed; sync is off-limits)
         smoke on this checkout (rework): 61 files, 519 readers, 6917 edges (the 10 more than before come from this block's own planning-reader edits); repeat_loads 21, full_output 9, harness_names 38, legacy_mentions 8, duplicate_clusters 64; default and `--root .` runs byte-identical; zero `/home/` or `/Users/` occurrences and no former repository name; DUP-021 now reads `~/Documents/projects/.tools/…`; extract ~2.3 s
         implementation choice not fixed by tests: the home prefix is rewritten only where it starts a path (`(?<![\w./~-])/(home|Users)/<name>/`), so `/srv/home/<name>/x` stays as written
         architecture: no update proposed — `.ai/memory/architecture.md` does not name the tool, and the specification permits only its inventory sentence, owned by the index-and-knowledge subtask
         validation 2026-11-17 (pav-check): verdict DONE. Acceptance criteria 6/6 met (each maps to a named test). Test integrity: `git diff 6847e51 HEAD -- scripts/check-audit-instructions.py` is append-only (456 insertions after the last earlier class, 0 deletions), so the 65 earlier tests are unchanged; `git diff 1990c41 HEAD` of the suite is empty, so the 16 RED-digest tests are unchanged since their test commits; no skip or xfail added (the three `skipTest` calls are the earlier git-missing and superuser guards). RED reproduced in the scratchpad: f375b8d's suite and 1990c41's suite each paired with the 6847e51 tool fail exactly the 14 and 16 new tests by assertion (one extra ERROR is the archive copy lacking scripts/validate-contracts.sh); seven single-line mutations of the HEAD tool (no home rewrite, no stop check, negation over the whole clause, self-call allowed, separators kept, multi-target loads, threshold 7) are each caught. Suite 81 OK in 5.9 s; py_compile clean; every function annotated, none over 30 lines, no line over 100 characters; no requirement, criterion or planning label in the diff; `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing; the subtask diff touches only the two target files; commit messages carry no attribution or planning ids. Full validator not run (caller instruction; only the two standalone scripts changed); runbook lint is shell-only, not applicable
         validation smoke on this checkout: 61 files, 519 readers, 6916 edges; repeat_loads 21, full_output 9, harness_names 38, legacy_mentions 8, duplicate_clusters 64; default and `--root .` runs byte-identical; zero `/home/`, `/Users/` or former repository name; spec examples reproduced (`workflows/pd-finalize.md:113`, `workflows/pd-decompose.md:14` not calls; `workflows/phase-pipeline.md:105`, `workflows/pav-close.md:64` calls); exit contract probes (non-UTF-8 and control-character workflows, symlinked workflow, missing out directory, missing root) give exit 0 or exit 2 with one ERROR line, no traceback
         validation finding (optional) V1: the home rewrite needs a slash after the name, so a bare home directory stays absolute — `Keep the full output in /home/alice and also /Users/bob.` and `` `/home/carol` `` reach FO/HN text unchanged and would fail the AC-22 grep; latent (no such text in the tree); the frozen rework test also keeps `/home/ alone` and `/Users/ too`, which hold `/home/`/`/Users/` and would fail the same grep if they occurred in an audited file
         validation finding (optional) V2: REQ-25 says outputs hold only repository-relative or `~/`-relative paths, but copied text keeps system paths verbatim — DUP-021 text holds `/usr/bin/sg` (and T-02 edge `raw` holds `/tmp`); AC-22's grep passes; copied text cannot be rewritten without falsifying it, so the requirement wording needs spec-sync (machine-specific home paths only)
         validation finding (optional) V3: the separator pattern is matched against the line with trailing spaces kept, so `| --- | --- | --- | --- | ` (trailing space) is a 9-word unit and two such rows form a cluster (repro: two rules with that separator → DUP of the separator text); literal to DM-6's `^\|[-:| ]+\|$`; no such row in the tree
         validation finding (optional) V4: the stop marker is matched case-sensitively in the raw line, so `**Stop**: run `/w-q` first.` is a call while a span `` `**stop**` `` before the command blocks one; DM-6 names only `**stop**`; no such line in the tree
         validation finding (optional) V5: audited files with `encoding: control-character` give no FO, HN, legacy or call entries, although DM-6 limits only duplicate units to `utf-8` (the arbiter settled legacy; FO/HN/calls follow the edge rule that only `utf-8` audited files have edges)
         validation finding (optional) V6: the rework tests feed `/home/someone/`, `/Users/someone/` placeholders as fixture input; the orchestrator accepted it, but the task's off-limits line says no absolute path in any fixture — record the exception when spec-sync amends DM-6
         validation observation: the call heuristic counts a quoted stop message without a `**stop**` marker as a call (`workflows/pae-implement.md:66` → RL-001 `pae-implement` → `pd-decompose`); DM-6-conformant, left to the auditor's disposition
         proposals (batch, recorded, none applied; section returned to the orchestrator as a delta): Do Now — P1 rewrite a bare home directory at a path end (`/home/<name>` or `/Users/<name>` followed by end of text, whitespace, a backtick or punctuation) to `~`, with a test (V1; confirm it stays within the owner's home-path decision); Do Later — P2 spec-sync: amend DM-6 for the home rewrite, narrow REQ-25 to machine-specific home paths, and record the fixture-input exception (V2, V6); P3 spec-sync: decide whether separator rows are matched after trailing whitespace is removed (V3); Optional — P4 match the stop marker case-insensitively outside spans (V4); P5 state the encoding rule for FO, HN, legacy and calls in DM-6 (V5)
         validation process note: fixtures and archived test commits live under the session scratchpad `val-t03`; no git write touched this repository; no permission changed
  branch: feat/instruction-audit-candidates
  base_branch: feat/instruction-audit-reference-edges
  base_commit: 6847e512de31d56d8ed6a05eefe7db8300f6ae2f
  commits: f375b8d test(audit): cover repeat-load, output, naming and duplicate candidates, 1990c41 test(audit): require home directory paths in copied text as tilde paths, 6595ff1 feat(audit): list repeat-load, output, naming and duplicate candidates
  pr: none

T-04 | Verifier: assessment consistency | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-05 | Verifier: map, amendments and statement coverage | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-06 | Renderer and report checks | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-07 | Extraction and assessment of rules and adapters | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.inventory.json, docs/audits/<run_date>-rules-workflows-audit.assessment.json
  blocker: none
  notes:

T-08 | Assessment of workflows | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.assessment.json
  blocker: none
  notes:

T-09 | Map, findings, amendments and report | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.assessment.json, docs/audits/<run_date>-rules-workflows-audit.md
  blocker: none
  notes:

T-10 | Index, knowledge and review line | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/README.md, scripts/README.md, .ai/context/runbook.md, .ai/memory/architecture.md, .ai/memory/state.md, .ai/memory/progress.md, docs/audits/<run_date>-rules-workflows-audit.md
  blocker: none
  notes:


## Model Selection
selection: complete
active provider: anthropic (`Model (Claude)` column)
catalog: ~/.config/orchestrail/model-catalog.md, refreshed 2026-11-09 (fresh, 7 days old; evidence dated 2026-11-09)
support evidence (2026-11-16): the worker tool of this session accepts the model names haiku, sonnet, opus and fable; the session environment lists the identifiers claude-haiku-5-5, claude-sonnet-5-5 and claude-opus-5-5; worker tools: all; the tool does not expose a context window, so the 1,000,000-token window is the owner's confirmation of 2026-11-13, not a new observation.
owner limits: allowed models are the three observed identifiers; the session model claude-fable-5-2 has no catalog evidence and was not a candidate. Fallback configuration is valid (openai gpt-6.1-terra, high) and was not needed.
cost: no qualified comparable total-cost evidence; the strongest eligible baseline was used, so cost optimality is unverified.
reasoning support (2026-11-16): the worker tool exposes the effort levels low, medium, high, xhigh and max and effort is configurable per worker; support per model is not separately observed.
reasoning rationale: catalog quality is measured at maximum effort; leaf floors here are 2–4 and lower levels have no recorded evidence, so `high` is recommended for every leaf, as a heuristic.
reselection 2026-11-16: finalization added one test scenario to T-07 (scope, steps and criteria unchanged); T-07 was reselected with unchanged scores and the same result, and its digest was recomputed.
actual model and actual reasoning: unknown until separately observed execution evidence.

| Leaf | Scores (C/A/V/R/Ver/Crit/RW) | Floor | Recommendation | Confidence | Reasoning | Description sha256 | Plan row sha256 |
|---|---|---|---|---|---|---|---|
| T-01 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | 5231849a94d38f25e161099c924d6eecbc278b9301161b4d3510c0a807e9c384 | cf718b61516e0b719764e744605c56461e8e25b41bf825227cc16584ed49963e |
| T-02 | 4/2/3/4/4/2/3 | 3 | claude-opus-5-5 | verified | high | 513549a83a6e6456ee17b4fd2e58c5a5e81a8e7b74bdcc3f54b90c97f800af7e | 78c2fb0e6d243933b109c1a266fabb2c91672a8b40f2d808372b405065bc9218 |
| T-03 | 3/2/3/4/4/2/3 | 3 | claude-opus-5-5 | verified | high | 0b80a7f8f16da9f5d8a96c0ae968134c929597d3ea112599904c9c112e86a25d | 025474779d65d2972e15fc62c08f4f32af1bd2cf0232e70a94170d4b3ed24234 |
| T-04 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | 12e32ba678a199ac338cf3d145fc19efecb4760d825706f50e53eebcf080e7dc | ba945a63453940265cb53e7629f82f0fddc692932b67541446a0bdba1485f66e |
| T-05 | 3/2/3/3/4/2/3 | 3 | claude-opus-5-5 | verified | high | 45446a9330fac1584dd7531ced7a1422f201980a7be2dc6bbcdb4c31f3b29fe3 | e5e278529bcee7306975f76c446a32e225a425ba54af70084e90ea4b7e0c2e5e |
| T-06 | 3/1/3/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | f56026a3cb70bed31b4de7c4e224af1d8aa0c11a8498155eaf511481bd907591 | 680bd30c3a39ec159b3a8e9bd78688d7eb2a8c7bc49391d361beb09284c0cec2 |
| T-07 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | fbf7860f83d1e6eb6d143b9e6acb4ddda0d840743c90bc0384a0558383ae815a | 26325889e65eac13d1a30333f0c82f10d2fc4ad8458b62410bf08b8516826784 |
| T-08 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | ef088cfd3208310cc4ab5665b9f145f5d4ad1c92144783f6be217ab2200bf152 | 8902589702291e8d1541b7ff16f77ad3c054ca7a9eda4311defa0defe9e64b0a |
| T-09 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | e745870b9261dcdf96cb54ef3f47c2e4de4eac37f366bc058a9654a9950618e9 | 0f0dd8045dfd8ad9566618435cd1a15dd6193abdc51fb58769ab1b712c58a5c9 |
| T-10 | 2/1/3/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | 25f47f5b8de403951cf30f88645afb5dff12f7000247ab8d103afa489624203e | 420d8807eb3d1fbec973074e772b7d7c8349190916e2cbe4ff8a36258839069d |

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Variant 1. The specification fixes the interface, the data model, the diagnostics and the two permitted files; the remaining choice is internal structure, and layered pure functions in one file satisfy the boundary and keep each subtask's addition local to one layer. Verifier rules and renderer subsections are plain functions collected in ordered lists, not a plug-in mechanism.
adr: not triggered — the specification already fixes the contract and states that no decision record is required; the internal layout of one script is a local choice that a future reader does not need a record to understand.

### Scope
#### In
- The tool with `extract`, `verify` and `render`, and its standalone suite.
- The three audit outputs for the snapshot extracted at a clean commit, with every audited file read in full.
- One index line, two script rows, one commands note, the inventory sentence, and the two memory entries.
- The review line after an independent pass; acceptance left pending.
#### Out
- Any edit to audited files, tests, hooks, principles, templates, the validator, sync or other scripts.
- Applying amendments or fixing findings; reconciliation of the naming-migration specification.
- Registration of the suite or tool in the validator or in sync.
- Installed-copy comparison; token, cost or saving statements.
- Restoring absent historical reports or repairing their links.

### Rejected
→ archived to state-archive.md

### Off-limits
- `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, every other existing script, every specification file.
- `scripts/sync.sh`, installers, workflows and models are never run to produce the inventory.
- Installed copies under the user's home are never read or changed by the tool.
- No absolute path and no former repository name in any output or fixture.

### Invariants
- The tool writes only the `extract --out` file or the generated region under `render --write`, each by atomic replacement.
- Two extractions of the same bytes and git state are byte-identical.
- Symbolic links are recorded and never followed; repository content is never executed or imported by the tool.
- The assessment has one writer at a time, and every audited path has exactly one row in `files`, `coverage` and `map`.
- Nothing obligatory is proposed for deletion; changes to the naming-migration specification exist only as amendments.
- `bash scripts/validate-contracts.sh` stays at zero failures.

### Acceptance Criteria
- `python3 -I scripts/check-audit-instructions.py` exits 0, with at least one case per edge form, per status and per diagnostic code.
- `python3 -I scripts/audit-instructions.py verify --root . --report docs/audits/<run_date>-rules-workflows-audit.md` exits 0 with empty output at the delivery commit.
- A fresh extraction on a checkout of the inventory's `source_revision` equals the delivered inventory byte for byte.
- The report holds `Reviewed: <role> <date> pass <commit>` and `Accepted: pending`, and names every blocking finding under its blockers heading.
- Every changed path of the delivery is in the specification's permitted-changes list, and `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing.
- `bash scripts/validate-contracts.sh` reports zero failures.
- The index, script table, runbook note, inventory sentence and the two memory entries are present as the specification states.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | 4 | 4 | 4 | 4 | 5 | 21 |
| Variant 2 | 3 | 3 | 4 | 4 | 2 | 16 |
| Variant 3 | 4 | 4 | 3 | 2 | 5 | 18 |

**Winner:** Variant 1 — it is the only layout that stays inside the two permitted files and keeps unit-level testability.
**Anti-overengineering check:** passed — ordered lists of plain functions add no abstraction beyond what the per-code and per-subsection criteria need.
**Evidence:** the specification's permitted-changes list and suite contract; P4, P7; ADR-0019 Decision 3 (standalone checks under `scripts/`); `scripts/state-tool.py` as the single-file standard-library precedent.

## Improvement Proposals (T-01)

### Do Now
- P1: adapter-file presence via `os.lstat` so a permission error surfaces instead of omitting `templates/codex-global-AGENTS.md` (V8); add a test
- P2: correct the docstring sentence claiming no repository-configured program runs; clean filter drivers can run under `git status` (V9)

### Do Later
- P3: roots below the git top level — `worktree.paths` mismatch (V4); needs a specification decision within the three permitted git commands
- P4: record `root-unreadable` as an extract exit-2 code via `/spec-sync` (V7)

### Optional
- P5: prune the reader walk to classifiable prefixes so an unreadable unclassified directory does not refuse the root (V10)
- P6: settle whether whitespace-only front-matter lines count as continuation lines (V6)

## Improvement Proposals (T-02)

### Do Now
- P1: give the token literal `templates/codex-global-AGENTS.md` the same right boundary as the other path tokens, so `templates/codex-global-AGENTS.md.bak` no longer resolves to the adapter file (V1); add a test

### Do Later
- P2: settle by `/spec-sync` how duplicate headings, untrimmed components and empty components resolve (V2, V3)
- P3: headings whose text contains ` → ` cannot be cited (V7); decide with the naming-migration grammar or record as an accepted observation

### Optional
- P4: replace the fixture heading text that repeats a real repository heading, with a recorded test amendment (V6)
- P5: define runs of three or more backticks inside a line (V4)
- P6: define an unclosed `check "` string and text between `check ` and the first quote (V5)

## Improvement Proposals (T-03)

### Do Now
- P1: rewrite a bare home directory at a path end (`/home/<name>` or `/Users/<name>` followed by end of text, whitespace, a backtick or punctuation) to `~`, with a test, so copied text cannot fail the output grep for `/home/` and `/Users/` (V1); confirm it stays within the owner's home-path decision

### Do Later
- P2: spec-sync — amend DM-6 for the home rewrite, narrow REQ-25 to machine-specific home paths (system paths such as `/usr/bin/sg` stay verbatim in copied text), and record the accepted fixture-input exception for placeholder home prefixes (V2, V6)
- P3: spec-sync — decide whether table separator rows are matched after trailing whitespace is removed (V3)

### Optional
- P4: match the stop marker case-insensitively and outside spans (V4)
- P5: state in DM-6 that full-output, harness-name, legacy and call detection read only `utf-8` audited files (V5)
