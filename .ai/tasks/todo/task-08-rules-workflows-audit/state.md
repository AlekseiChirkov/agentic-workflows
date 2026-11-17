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
  pr: none

T-02 | Reference edges | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-03 | Candidates, legacy mentions and duplicate clusters | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

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
