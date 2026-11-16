## Goal
Reads and writes treat fences inside a block, blank runs, NUL bytes and a swapped-in state file by one defined, fail-closed rule, and the read path parses the text once.

## Context
- Origin: owner request of 2026-11-16 to close every deferred improvement proposal and optional review finding of this task. Each item was verified against the code and decided by an independent analyst; the decisions below are the contract of this subtask and are implemented exactly as worded. Item ids name the proposal section and its ordinal (N = Do Now, L = Do Later, O = Optional; I<n> = issue list entry).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`; exit codes 0–8 and the error-code and warning-code tables stay closed (no decision adds a code). No existing test is deleted, renamed, skipped or weakened; new cases are new test methods or new subtests. English only; no planning identifiers or specification labels (requirement, criterion, invariant, decision, assumption, constraint or question labels) in code, tests, comments, messages or documentation.
- Test-first: every decision marked as a behaviour change has failing tests first, observed failing for the stated reason, committed before the implementation. Guard tests (pass before the change) are allowed when named with their mutation evidence. Refactoring is covered by the existing suite, green before and after.
- Pinned fixtures: a change to `tests/state-tool.py`, `scripts/state-tool.py` or another pinned script invalidates pinned digests (see `tests/fixtures/validator-runtime/README.md`); refresh them once after the last source edit. Do not add or remove lines of `docs/USAGE.md` above line 255: the repository's identity ledger pins that line. Never write the ledger's heading line into any file.
- Specification, ADR and knowledge-base sentences named in the decisions are written by the orchestrator at reconciliation, not in this subtask; manual (`docs/USAGE.md`), rule-file and tool-docstring sentences are in scope where the decision names them.

Off-limits: no file under `workflows/`; no deployed copy under the home directory; no change to the oracle mechanism beyond refreshing pinned values; no new exit, error or warning code; no amendment of an existing test.

## Scope
- **In scope:** the parser's blank-run and fence handling, the NUL refusal, the open flags of `state.md`, the state-missing message, the refactoring items, and the manual's Limits bullets M1 and M2 plus the fenced-text sentence in the existing `set` bullet.
- **Out of scope:** write-rule changes, lock metadata, validators, the setup script.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`, `docs/USAGE.md`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Read every decision below and the code it names; line numbers quoted in the decisions may be stale, locate by function or test name.
2. Add the suite cases the decisions name; for each behaviour change observe the failure and its reason; for each guard case record its mutation evidence.
3. Implement each decision exactly as worded; keep the frozen tests byte-identical.
4. Apply the document sentences that are in scope.
5. Refresh the pinned fixtures once after the last source edit and run the suite, the focused validator mode, the inventory oracle suite and the source-guard suites.

## Acceptance Criteria
- Each decision below marked APPLY holds exactly as its `Decision:` paragraph states (inputs, exit code, error code, result, bytes written, message), within this subtask's scope.
- Every behaviour change has a test that failed before the implementation for the stated reason; every guard case is named with mutation evidence.
- All tests that existed before this subtask pass unchanged.
- The suite, `bash scripts/validate-contracts.sh --state-tool-only`, the inventory oracle suite and the source-guard suites pass with the refreshed pinned values.
- No line of `docs/USAGE.md` above line 255 moved.

## Test Plan
- **Level:** integration (subprocess runs of the tool and the scripts against disposable fixtures), unit where a decision names an in-process case, smoke for manual and rule sentences.
- **Scenarios:** the cases each decision below names, with the expected exit code, error code, result and bytes.
- **Edge cases:** the boundary inputs each decision names; existing tests unchanged.

## Notes for this subtask
For the open-flags item two analysts decided the same flags; use the flag-recording test (no test may wait on a real named pipe) and add the manual sentence given in the second block. Manual bullets to add in section 11 Limits:

M1 — manual, new Limits bullet (must not be merged into the `set` bullet):
"- File shape: `state.md` must be UTF-8 without a byte order mark, carriage returns or NUL bytes (exit 3, `unsupported-encoding`). A blank line is an empty line. Inside a block a line holding only one or two spaces makes the block malformed (exit 3, `malformed-block`) and a line of three or more spaces is a continuation line; `init-block` treats a spaces-only line as the last non-blank line of the section."

M2 — manual, new Limits bullet:
"- Fences inside the section: a fence opened at column 0 ends the block before it. A fence opened at one to three spaces inside a block stays part of that block, together with blank lines directly before it; its lines are never reported, changed or used as an insertion point. An in-block fence that is never closed makes its block malformed (exit 3, `malformed-block`). A column-0 fence that is never closed hides every later block up to the end of the file: `get` and `validate` do not see them and a command that names one exits 3 `block-missing`. In both cases `init-block` exits 1 and writes nothing; close the fence by hand first."

## Decisions

### T-02 L1

T-02 L1 — APPLY — blank lines before an in-block fence do not end the block
Evidence: `continues_after_blanks` requires the line after the blank run to be unfenced, so `parse_blocks` closes the block. Reproduced at fence indents 1, 2 and 3: `  notes: a`, blank, fence pair, `  branch: after` → `get` reports no `branch`, exit 0, no warning. Without the blank line the same block reads `branch` (T-01 L1), so the two shapes disagree.
Decision: behaviour change, failing tests first. Rule: a run of blank lines that is immediately followed by a line opening a fence at 1–3 spaces, while a block is open, is opaque block content like the fence — it does not end the block and is not added to any field group (not listed in `continuation`, not covered by `FieldGroup.end`). Blank lines followed by a column-0 fence, by a field line, by a column-0 line or by the section end still end the block (unchanged). Blank lines followed by a line indented by 3 or more spaces stay continuation lines (unchanged). Exact results: (1) the reproduction above with one and with two blank lines, fence indent 1, 2, 3 → `get` exit 0, fields end with `branch` = `after`, `notes` has `continuation == []`, no warning, `validate` valid; (2) `append-note` on that block → the note line is inserted directly after `  notes: a`, before the blank lines and the fence; the receipts line goes to its canonical position in the now longer block; (3) `  last_action: x`, blank, in-block fence pair, further fields: `set --field last_action=new` → `applied`, only the field line replaced, blank and fenced lines byte-identical; (4) field line, blank, fence pair, blank, `     cont` → the field's `continuation` is `["", "     cont"]` and `set` on it is refused by the existing continuation rule. Bytes written change only for blocks of this shape (the point of the item). Specification: shared text S1. Manual: bullet M2. Files: `scripts/state-tool.py` (`continues_after_blanks` / the blank branch of `parse_blocks`), `tests/state-tool.py`, spec, manual, ADR text D6, fixture refresh. Implement together with I6 (same branch of the parser).
Why: options — (A1) block continues, blanks are opaque like the fence; (A2) block continues, blanks join the preceding field's continuation; (B) keep ending the block and document. (B) keeps a silent loss of fields and contradicts the pinned no-blank shape. (A2) is one line smaller but turns a blank-plus-fence under `last_action`/`blocker` into a `set` refusal while the pinned test `test_fields_without_continuation_lines_are_applied_as_before` requires `applied` for a fence directly under the field — two answers for one idea. (A1) gives one rule ("fenced text and the blank lines before it belong to no field group"), keeps every frozen test (verified by prototype) and matches the pinned insertion rule.

### I6

I6 — APPLY — scan a blank run once
Evidence: `parse_blocks` calls `continues_after_blanks` for every blank line of a run, and each call walks to the end of the run. Timed at the tip with a run of blank lines between `  notes: a` and a continuation line: 2,000 → 0.3 s, 4,000 → 1.2 s, 8,000 → 4.5 s (quadratic). Prototype with one scan per run: 20,000 → 0.06 s, identical output.
Decision: behaviour-preserving change with a failing test first. In the blank branch of `parse_blocks`, find the end of the run once, decide once (continuation line, in-block fence per T-02 L1, or block end), add the whole run to the group when it continues, and move the index to the end of the run. Output must be identical for every input (the `continuation` list still holds one empty string per blank line). Test: 40,000 blank lines between `  notes: a` and a 9-space continuation line; `get --block T-01` must exit 0 within a 10-second limit of its own and report 40,001 continuation entries; a timeout is reported as a test failure. At the tip this takes well over a minute, so the test is red for the right reason. Implement in the same edit as T-02 L1. Files: `scripts/state-tool.py`, `tests/state-tool.py`, fixture refresh.
Why: the branch is being rewritten for T-02 L1 anyway; the margin between the two behaviours is three orders of magnitude, so the time bound is not fragile.

### T-02 L2

T-02 L2 — APPLY — an in-block fence that is never closed makes its block malformed
Evidence: `fence_openers` marks every line to the end of the file as fenced when no closing line exists. Reproduced: leaf `T-01` with a 3-space fence line, then leaf `T-02` with `atomic-execution: complete` under `red` tests → `get` lists only `T-01`, `validate` exit 0 `valid`, `get --block T-02` exit 3 `block-missing`, `set` on `T-01` applied. An unclosed column-0 fence behaves the same for later blocks; `init-block` exits 1 in both shapes (pinned by `test_unclosed_fence_at_the_end_of_the_section_exits_1_and_writes_nothing`). An unclosed fence before the section already fails closed (`section-missing`).
Decision: behaviour change, failing tests first; no new code. A fence opened at 1–3 spaces inside a block that is not closed before the end of the file adds a malformed entry to that block: message `block <id>: fence opened inside the block is not closed`, line = the opening line (1-based). The closing rule is unchanged (a later line starting with the same marker at 0–3 spaces; a closing line that is the last line without a final newline counts as closed). Exact results for the block that holds the fence: `get` without `--block` → exit 3 `rejected`, `malformed-block`, `blocks` omitted; `get --block <it>` → exit 3 `malformed-block`; `get --block <other>` → exit 0 with warning `malformed-block`; `validate` (whole or `--block <it>`) → exit 3 `invalid` `malformed-block`; `set`, `append-note`, `add-file` on it and `init-block` naming its id → exit 3 `malformed-block`, nothing written, no temporary file; writes to other blocks proceed; `init-block` for a new id stays exit 1 `internal-error` with nothing written (frozen test, unchanged). A column-0 fence that is never closed is not attributed to any block and keeps today's behaviour: the lines to the end of the file are foreign, blocks inside are not read (`block-missing` when named), `validate` of the readable blocks is unaffected, `init-block` exits 1; this is stated as a limit (manual M2, spec S1) and gets one guard test pinning `validate` exit 0 and `get --block <hidden>` exit 3 `block-missing`. Tests first: the reproduction with a backtick and with a tilde fence (a backtick line does not close a tilde fence) for `get`, `validate`, `set`; the closed-at-last-line-without-newline case stays valid. Files: `scripts/state-tool.py` (`fence_openers` or a small helper reporting the unclosed opener, `parse_blocks`), `tests/state-tool.py`, spec, manual, ADR text D6, fixture refresh.
Why: options — (1) existing `malformed-block` for the block that holds the fence; (2) a new warning or error code `unclosed-fence` for both shapes; (3) keep and document. (2) opens the closed table and, for the error form, would have to replace the pinned exit 1 of `init-block`. (3) leaves `validate` reporting `valid` for the reproduced damage. (1) covers the reproduced case with an existing code whose meaning fits (the block's extent is damaged), fails closed for reads and writes of that block, and breaks no frozen test (prototype run). No existing code fits a column-0 fence (no block owns it), every write that could be affected already fails closed there, and Markdown defines such a fence as running to the end of the file, so it is documented instead of given a new code.

### T-01 L4

T-01 L4 — APPLY — NUL bytes in state.md are refused as unsupported encoding
Evidence: `decode_state` refuses a byte order mark, CR and invalid UTF-8 only. Reproduced: a NUL in a note value → `get` and `validate` exit 0 and report `"a\u0000b"`; `set` on that block is applied and keeps the byte. Write inputs already refuse NUL (`text_problem`).
Decision: behaviour change, failing tests first. `decode_state` raises `ToolError(3, "unsupported-encoding", "state.md contains NUL bytes")` when the file holds a NUL byte anywhere (inside or outside the progress section), checked next to the CR check. Result: `get` exit 3 `rejected`, `validate` exit 3 `invalid`, every write command exit 3 `rejected` with `state.md` unchanged and no temporary file; `source_revision` is reported (the file was read). No new code, no exit-code change. Tests: add a NUL case to `test_unsupported_encodings_exit_3` as a new subtest or sibling test for `get` and `validate`, and one write case (`set`, file unchanged). Specification: write algorithm step 4 becomes "reject non-UTF-8, BOM, CR or NUL bytes"; edge-case row "CR bytes, BOM, invalid UTF-8" becomes "CR bytes, BOM, invalid UTF-8, NUL bytes"; assumption A-09 becomes "UTF-8 without BOM and without NUL bytes, LF only; otherwise exit 3". Manual: bullet M1. Tool module docstring: no code list change (the code exists). Files: `scripts/state-tool.py`, `tests/state-tool.py`, `.ai/specs/completed/07-state-tool.md`, `docs/USAGE.md`, fixture refresh.
Why: options — (a) refuse with `unsupported-encoding`; (b) keep and document; (c) refuse only when the NUL is inside the section. (a) reuses the existing code whose meaning (the file is not acceptable text) fits, is symmetric with the CR rule and the input rule, is two lines and fails closed; (c) needs the parse before the refusal and gives two answers for one file; (b) leaves control bytes in machine output.

### I9

I9 — APPLY — non-blocking, binary open of state.md
Evidence: `read_state_file` opens with `os.O_RDONLY | O_NOFOLLOW` after an `lstat` check. A named pipe swapped in between the check and the open blocks the tool forever (reads take no lock, and the write path calls the same function while holding the task lock). On Windows, where reads are supported, `os.open` without the binary flag translates line ends, so the CR refusal is bypassed and the revision is not the digest of the file bytes.
Decision: behaviour change, failing test first. The flags become `os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)`. Result for a pipe that passes the first check: the open returns at once and the existing `fstat` check refuses with exit 7 `unsafe-state-file`; regular files read exactly as before. Test (in-process, through the existing `run_in_process` harness): wrap `os.open` to record the flags of every open of `state.md` during a `get` and a `set`; assert `os.O_NONBLOCK` is set in each, and, with `os.O_BINARY` patched in as an attribute (the wrapper strips that bit before delegating), that it is set as well. Do not write a test that waits on a real pipe: it would hang at the tip. The lock file and the temporary file opens are unchanged (a pipe at the lock path is already refused; pinned). Files: `scripts/state-tool.py`, `tests/state-tool.py`, fixture refresh.
Why: two flags, no effect on regular files, removes an unbounded hang under the task lock and makes the documented Windows read path correct.

### I9

I9 — APPLY — open `state.md` non-blocking and, where the platform has it, in binary mode
Evidence: `read_state_file` (lines 412–432) checks `lstat`, then opens with `O_RDONLY | O_NOFOLLOW`, then checks `fstat`. Named-pipe half reproduced: with a named pipe at the path and the first `lstat` answered as a regular file (the swap between the two calls), `get` hangs until killed (timeout exit 124). The same open runs under the task lock in write commands, so a hung writer would hold the lock and every other writer would get exit 5. With `O_NONBLOCK` added (scratch `v3`) the same run returns at once: exit 7, `unsafe-state-file`, "state.md must be a regular file" — the existing `fstat` check and code. Windows half: the tool cannot write without `fcntl` (REQ-24, exit 7 `locking-unavailable`), but the spec and the manual promise that `get` and `validate` still work there; a descriptor opened without `O_BINARY` is in text mode on that platform, so line ends would be translated before the revision is computed and before the CR refusal (`unsupported-encoding`) is applied. Not reproducible here (no Windows host); `O_BINARY` does not exist on this platform, so the flag is a no-op wherever the suite runs.
Decision: In `read_state_file` only, open with `os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)`.
- Named pipe (or other non-regular file) swapped in between the inspection and the open → no hang; reads and the first read of a write: exit 7, `unsafe-state-file`, `source_revision` null, nothing written; at the recheck before the rename: the existing outcome, exit 4 `state-file-changed`, own temporary file removed, `result_revision` null. No new code, no exit-code change. Regular files behave as before.
- The lock-file open and the temporary-file open are not changed (a named pipe at the lock path is already refused without blocking and pinned by `test_lock_path_that_is_a_directory_or_a_named_pipe_is_refused`; neither open is reachable on Windows).
- Files: `scripts/state-tool.py`, `tests/state-tool.py`, `docs/USAGE.md`. Behaviour change → failing tests first: (a) `get` and a write command run with the first `lstat` of `state.md` answered as regular while the path is a named pipe, under a short timeout → exit 7 `unsafe-state-file` (today: the run times out, which is the right failure); (b) with `os.O_BINARY` defined for the run and `os.open` wrapped to record and strip it, the flags used for `state.md` include it (today: absent). No existing test changes.
- Manual sentence (Limits, in the "Without `fcntl`" bullet): "Read commands on such a platform are not covered by the acceptance suite." No spec change needed (REQ-09 already requires the refusal).
Why: Options — both flags [winner]: one expression, no-ops for regular files on this platform, removes an unbounded hang that can hold the task lock, and keeps the stated promise that reads work without `fcntl`; non-blocking only, and withdraw the Windows read promise from the manual and REQ-24: more text change than the flag and a narrowed requirement; reject both: leaves a reproduced hang for the price of one flag. The Windows half stays unverified by execution, which the added manual sentence states instead of assuming.

### T-01 O3

T-01 O3 — APPLY — state-missing message uses the root-relative path
Evidence: `read_state_file` raises `state.md is missing: <absolute path>`; reproduced — the message carries the absolute scratch path while the report's `task` key is root-relative. No test pins the message.
Decision: behaviour change (message text only), failing test first. The `state-missing` message becomes exactly `state.md is missing: <task>/state.md`, where `<task>` is the value of the report's `task` key (root-relative, `/` separators; `.` when the task is the root, giving `./state.md`). Exit 3 and code unchanged; applies to read and write commands. Test: `get` and one write command on a task without `state.md` → message equals `state.md is missing: <TASK_RELATIVE>/state.md` and does not contain the absolute root. Files: `scripts/state-tool.py`, `tests/state-tool.py`, fixture refresh.
Why: stdout then depends only on the inputs (determinism target) and matches the `task` key; cost is one parameter.

### T-02 O2

T-02 O2 — APPLY — split and fence-scan the text once per command (carries T-01 O1)
Evidence: `load_document` and `command_write` run `split_lines` and `fence_flags` for the version check, then `parse_document(text)` repeats `split_lines` and `fence_openers`.
Decision: refactoring, no behaviour change, existing suite as the characterization. Add `parse_lines(lines: list[str], openers: list[int | None]) -> Document` holding the present body of `parse_document`; keep `parse_document(text)` as a two-line wrapper (`split_lines`, `fence_openers`, `parse_lines`) for the two candidate re-parses. `load_document` and `command_write` call `split_lines` and `fence_openers` once, derive the fenced flags from the openers for `task_contract_version`, and call `parse_lines`. `load_document` must still fill `contract_version` before the parse can raise a section refusal. Remove `fence_flags` if it has no caller left. Coordinate with the proposal of another group that extracts a shared version helper for the same two call sites (T-03 Optional 3): apply this one first, or both in one edit. Files: `scripts/state-tool.py`, fixture refresh.
Why: one definition of how text becomes lines and fence state; needed anyway once T-02 L2 adds unclosed-fence knowledge to the scan.

### T-01 O1

T-01 O1 — APPLY — parse the lines once (merged with T-02 O2; one change)
Evidence: the proposal's location is stale — `command_get` no longer splits; the duplication is now in `load_document` and `command_write`, which call `split_lines` and `fence_flags` and then `parse_document(text)`, which splits and computes the fence openers again.
Decision: see T-02 O2; T-01 O1 is delivered by that change and has no separate work.
Why: same defect, one fix.

### T-03 O3

T-03 O3 — APPLY — one helper for the task contract version and its support check
Evidence: `load_document` and `command_write` both run `split_lines`, `task_contract_version(lines, fence_flags(lines))` and `contract_version_supported(...)`.
Decision: extract one function returning the recorded version text (or None) and whether it is supported, used by both; behaviour-preserving refactoring covered by `test_newer_or_uncheckable_contract_version_refuses_writes`, `test_newer_contract_version_warns`, `test_contract_version_without_tool_version_warns` (must stay green unchanged). File: tool only. Do it in the same change as any parser-argument refactoring another analyst approves for the T-01/T-02 duplication items, so the lines are split once.
Why: mechanical, small, and the two copies must never drift on a refusal rule.

### I8

I8 — APPLY — remove the two stored fields that are never read
Evidence: `Document.fenced` is assigned in `parse_document` and read nowhere (no `.fenced` attribute access in the tool or the suite); `TaskPaths.root` is assigned in `resolve_paths` and read nowhere. Every other dataclass field has a reader.
Decision: refactoring, no behaviour change, existing suite as the characterization. Remove `fenced` from `Document` and `root` from `TaskPaths` and adjust the two constructors. If T-02 L2 chooses to store the unclosed opener on the document, that is a new read field and not affected. Files: `scripts/state-tool.py`, fixture refresh.
Why: dead state invites wrong assumptions; two-line removal.

### T-02 O1

T-02 O1 — APPLY — one block-selection helper for get and validate
Evidence: `command_get` and `command_validate` each filter `document.blocks` by `--block`, raise `block-missing`, and split `structure_problems` into the target's and the others'.
Decision: refactoring, no behaviour change, existing suite as the characterization (run it before and after). Add `select_blocks(document: Document, target: str | None) -> tuple[list[Block], list[ToolError], list[ToolError]]` returning the selected blocks, the structure errors of the selection and the structure errors of the other blocks; with no target the selection is every block and the third list is empty; an absent target raises `ToolError(3, "block-missing", f"block {target} not found")`. `command_get` returns exit 3 with the second list when it is non-empty and otherwise adds the codes of the third list to the warnings; `command_validate` uses the second list as its structure errors and ignores the third. Output order of errors and warnings must stay byte-identical. Files: `scripts/state-tool.py`, fixture refresh.
Why: removes about ten duplicated lines in the two read entry points; low risk under the existing 60+ read tests.

### T-01 O2

T-01 O2 — APPLY — section comment above the line helpers
Evidence: the banner `contract version` sits above `split_lines`, `content`, `fence_openers`, `fence_flags`; the version functions start at `task_contract_version`.
Decision: comment-only edit in `scripts/state-tool.py`: insert a banner `lines and fences` (same banner style) above `split_lines` and move the `contract version` banner to directly above `task_contract_version`. No behaviour; test levels considered — unit, integration, contract, smoke: none applies to a comment. Do it in the refactoring change so the fixtures are refreshed once.
Why: free when the file is edited anyway; wrong banner misleads a reader.

### I13

I13 — APPLY — re-wrap the seven lines over 100 characters, inside the refactoring change only
Evidence: exactly seven lines of `scripts/state-tool.py` exceed 100 characters (101–104), in `check_write_arguments`, `resolve_paths`, `task_contract_version`, `structure_problems`, `replace_state`, `write_target` and `main`. The repository has no written line-length rule and sibling scripts hold several hundred such lines; the tool's own style wraps at 100.
Decision: re-wrap those lines (and any new line) to at most 100 characters with no token change, in the same commit as T-01 O2. No standalone change and no new lint check. No test level applies (formatting: unit, integration, contract and smoke considered). Files: `scripts/state-tool.py`.
Why: costs nothing when the file and its pinned digest change anyway; a separate change for it would not be worth a fixture refresh.

### T-13 O1

T-13 O1 — APPLY — manual: fenced text under a field is not covered by the set refusal (ruling: not refused)
Evidence: reproduced: `  last_action: old` directly followed by an in-block fence pair → `set --field last_action=new` applied, field line replaced, fenced lines unchanged. Pinned as `applied` by the frozen case "field line directly followed by an in-block fence" of `SetContinuationTests.test_fields_without_continuation_lines_are_applied_as_before`. A continuation line after the closing fence makes the field continued and `set` is refused (frozen shape "a continuation line after an in-block fence").
Decision: ruling — `set` is not refused for fenced text under the named field; behaviour unchanged. Documentation only: append to the existing Limits bullet about continued values in `docs/USAGE.md` the sentence "Fenced text placed under a field line is not a continuation line: `set` replaces the field line and leaves the fenced lines, and blank lines directly before them, where they are." It must stay inside that one bullet: `test_limits_state_that_set_refuses_a_field_whose_value_continues` requires exactly one Limits item that matches its five patterns. No test level applies (documentation: unit, integration, contract and smoke considered; the manual tests pin other sentences and stay green). File: `docs/USAGE.md`.
Why: options — refuse like continuation lines; keep and document. Refusing contradicts a frozen test and the T-02 L1 rule that fenced text belongs to no field group; the fenced lines are never deleted or changed, which is what the owner ruling of 2026-11-14 protects.
