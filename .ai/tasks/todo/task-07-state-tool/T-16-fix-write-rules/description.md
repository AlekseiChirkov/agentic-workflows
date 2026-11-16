## Goal
Write commands refuse whitespace-only text, continued target files, a tests-status change that breaks a completed leaf and a state file that is not writable, never end in an internal error for input the grammar allows, and report messages that are valid Unicode.

## Context
- Origin: owner request of 2026-11-16 to close every deferred improvement proposal and optional review finding of this task. Each item was verified against the code and decided by an independent analyst; the decisions below are the contract of this subtask and are implemented exactly as worded. Item ids name the proposal section and its ordinal (N = Do Now, L = Do Later, O = Optional; I<n> = issue list entry).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`; exit codes 0–8 and the error-code and warning-code tables stay closed (no decision adds a code). No existing test is deleted, renamed, skipped or weakened; new cases are new test methods or new subtests. English only; no planning identifiers or specification labels (requirement, criterion, invariant, decision, assumption, constraint or question labels) in code, tests, comments, messages or documentation.
- Test-first: every decision marked as a behaviour change has failing tests first, observed failing for the stated reason, committed before the implementation. Guard tests (pass before the change) are allowed when named with their mutation evidence. Refactoring is covered by the existing suite, green before and after.
- Pinned fixtures: a change to `tests/state-tool.py`, `scripts/state-tool.py` or another pinned script invalidates pinned digests (see `tests/fixtures/validator-runtime/README.md`); refresh them once after the last source edit. Do not add or remove lines of `docs/USAGE.md` above line 255: the repository's identity ledger pins that line. Never write the ledger's heading line into any file.
- Specification, ADR and knowledge-base sentences named in the decisions are written by the orchestrator at reconciliation, not in this subtask; manual (`docs/USAGE.md`), rule-file and tool-docstring sentences are in scope where the decision names them.

Off-limits: no file under `workflows/`; no deployed copy under the home directory; no change to the oracle mechanism beyond refreshing pinned values; no new exit, error or warning code; no amendment of an existing test.

## Scope
- **In scope:** the write rules and messages named in the decisions, their suite cases, and the manual sentences the decisions give (including the Limits sentence of item T-05 L4: "A hand-edited `atomic-tests` value outside the vocabulary counts as `not-started`: `set` replaces it with any vocabulary value except `green`.").
- **Out of scope:** parser and fence rules, lock metadata and signals, validators, the setup script.
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
The `add-file` sentence goes inside the existing Limits bullet about continued values, not into a new bullet: one manual test requires exactly one Limits item matching its patterns.

## Decisions

### T-03 N2

T-03 N2 — APPLY — bound --lock-wait-seconds to one to three digits
Evidence: `lock_wait_seconds` / `LOCK_WAIT = [0-9]+`; reproduced `--lock-wait-seconds` with 5000 nines → exit 1 `internal-error` (`ValueError: Exceeds the limit (4300 digits)`). `0600` and `0000` are accepted today.
Decision: `LOCK_WAIT = re.compile(r"[0-9]{1,3}")`. Result: any value that is not one to three ASCII digits, or is above 600 → exit 2 `invalid-arguments`, nothing read or written, `source_revision` null. This includes `0600`, `0000` and 5000 nines. `0`, `5`, `005`, `600` stay accepted. Behaviour change: failing test first (5000 nines → exit 2; `0600` → exit 2), added to `test_invalid_write_invocations_exit_2_with_one_json_object` or beside it. Files: `scripts/state-tool.py`, `tests/state-tool.py`. Spec sentence (`### Commands`, first bullet): "`--lock-wait-seconds` is written as one to three ASCII digits with a value from 0 to 600; anything else is exit 2 `invalid-arguments`."
Why: the spec already puts an out-of-range wait under exit 2; the fixed-width pattern is the smallest change that removes the internal error.

### T-03 O1

T-03 O1 — APPLY — keep the separator space when a header status with an empty value is set
Evidence: `edit_header`; reproduced: header `T-01 | Leaf | atomic-tests: | atomic-execution: in-progress | …`, `set --field atomic-tests=red` → applied, header becomes `atomic-tests: red| atomic-execution: …` (no space before `|`). It re-parses, but it is not the canonical ` | ` form the line-grep validator and hand readers expect.
Decision: in `edit_header`, when the existing segment's value is empty after stripping, write the segment as ` <name>: <value> ` when it is not the last segment and ` <name>: <value>` when it is the last one; a segment with a non-empty value keeps today's in-place replacement. Result for the reproduction: `T-01 | Leaf | atomic-tests: red | atomic-execution: in-progress | …`, exit 0 `applied`, `changed_fields` `["atomic-tests", "state_receipts"]`. Behaviour change (bytes written): failing test first, with an empty first segment, an empty middle segment and an empty last segment. Files: tool, suite. No spec text.
Why: the tool should never write a non-canonical header; three lines.

### T-04 L1

T-04 L1 — APPLY — add-file refuses a target_files value that continues
Evidence: `target_files_change` reads `groups[0].value` only. Reproduced: `  target_files: a.sh,` + continuation `     b.sh`, `add-file --path b.sh` → exit 0 `applied`, line becomes `  target_files: a.sh,, b.sh`, continuation line kept.
Decision (ruling). Options: (a) read continuation lines as further entries — guesses a list grammar the contract does not define (separator at line ends, indentation), low simplicity, medium blast radius; (b) refuse — one check, mirrors the owner ruling for `set` (ADR-0022 Decision 5, REQ-27), fails closed, fully testable; (c) keep and document — keeps writing a duplicated entry and a doubled comma. Winner: (b).
Exact behaviour: `add-file` on a leaf whose `target_files` field group has at least one continuation line (a blank line followed by a continuation line included; lines of an in-block fence are not continuation lines, as for REQ-27) → exit 6, error `invalid-value`, result `rejected`, no warning, `state.md` unchanged, no temporary file; also when every named path is already listed on the field line (checked before the `unchanged` shortcut). Order: target lookup (exit 3) → matching receipt (`already_applied`) / reused id (exit 8) → stale revision (exit 4) → `field-not-applicable` on a composite → note and path content rules (`invalid-path` wins) → this refusal → `unchanged` shortcut. `set`, `append-note` and `init-block` are not affected; `add-file` on a block where another field continues stays applied (`test_notes_and_target_files_still_grow_in_a_block_with_a_continued_field` unchanged). Message: `block <id>: target_files has continuation lines, which add-file does not read; edit the block by the manual procedure`.
Files: tool (`check_additions`), suite (failing tests first: refusal, current-path case, order against receipt, revision and `invalid-path`), spec, manual, ADR. No new code. Spec: add "**REQ-next Continued target files.** WHEN `add-file` names a block whose `target_files` field group has continuation lines, THE SYSTEM SHALL refuse with exit 6 (`invalid-value`) and leave `state.md` unchanged and create no temporary file, also when every path is already listed; `add-file` reads and writes the field line only." plus one AC, one edge-case row and one traceability row. Manual: append to the existing Limits bullet about `set` (same bullet, so `test_limits_state_that_set_refuses_a_field_whose_value_continues` still finds exactly one item): "`add-file` likewise refuses a `target_files:` value that continues on following lines (exit 6, `invalid-value`), because it reads entries from the field line only."
Why: same rule as the owner's `set` ruling — refuse rather than guess or delete.

### T-04 L2

T-04 L2 — APPLY — whitespace rules for target paths
Evidence: `path_problem`; reproduced: `--path "   "` → applied, `  target_files: a.sh,    `; `--path "c.sh "` and `--path " d.sh"` → applied, `a.sh, c.sh ,  d.sh`; existing value of one space + `--path c.sh` → `  target_files:  , c.sh`.
Decision (ruling, shared with T-04 L3 and T-06 L3). Options: (a) one rule — a text input that must be non-empty must hold a non-whitespace character; (b) also refuse leading or trailing whitespace on every text input; (c) keep and document. Winner: (a) for all inputs, plus the surrounding-whitespace refusal for paths only, because a path is a list entry compared by exact string equality and split on `, `, while notes and names are opaque text stored literally.
Exact behaviour, all `invalid-path`, exit 6, nothing written, for `add-file --path` and `init-block --target-file`: (1) a whitespace-only path (the empty path included) → message `must not be empty or only whitespace`; (2) a path with leading or trailing whitespace (`path != path.strip()`) → message `must not start or end with whitespace`. Inner whitespace stays valid (`docs/my guide.md`). Check order inside `path_problem`: single-line/UTF-8 rule, then (1), then (2), then the existing lexical rules. (3) In `target_files_change`, an existing value that is whitespace-only has no entries and the written value is the new paths joined by `, ` (the reproduction then gives `  target_files: c.sh`).
Files: tool, suite (failing tests first: spaces-only path, tab-only path, leading space, trailing space, whitespace-only existing value; guard: inner space still applied), spec, manual. Spec `### Commands`: replace "non-empty" in the paths bullet by "holding at least one non-whitespace character, with no leading or trailing whitespace", and add to the text-input bullet: "A value, note, name or path made only of whitespace counts as empty." REQ-18: "an empty value has no entries" becomes "an empty or whitespace-only value has no entries". Manual `add-file` row: add "A path that is empty, only whitespace, or has leading or trailing whitespace is refused."
Why: the tool already treats a whitespace-only `last_action`/`blocker` as empty; one rule for every text input, and paths must not write trailing whitespace or near-duplicate entries.

### T-04 L3

T-04 L3 — APPLY — a whitespace-only note is refused like the empty note
Evidence: `note_problem` refuses only `""`; reproduced: `append-note --note "   "` and `--note "\t"` → applied, whitespace-only continuation lines; on an empty `notes:` line the note is stored as `  notes:   `.
Decision: the shared rule of T-04 L2: a note with `note.strip() == ""` → exit 6 `invalid-value`, message `note must not be empty or only whitespace`, the whole call refused, nothing written; applies to `append-note --note`, `set --note`, `init-block --note`. Leading or trailing whitespace around visible text stays accepted and stored literally. An existing whitespace-only `notes:` value is still kept and followed by the note (frozen test `test_notes_line_with_a_whitespace_value_is_kept_and_followed_by_the_note` unchanged: existing note text is never altered). Behaviour change: failing tests first (spaces, tab, for all three commands). Files: tool, suite, manual (`append-note` row: "An empty note is refused." becomes "A note that is empty or only whitespace is refused.").
Why: a whitespace-only continuation line becomes a blank line under any trimming editor and silently changes the notes group.

### T-04 O3

T-04 O3 — APPLY — quote an invalid path unambiguously in the message
Evidence: `check_note_and_path_content` formats `path '{path}'`; reproduced: a path with LF puts a raw line break inside the stderr diagnostic line.
Decision: format the path with `!r` (`f"block {block_id}: path {path!r} {reason}"`). Message text only; exit, code and result unchanged. Failing test first: the `invalid-path` message for `a\nb.sh` contains the two characters `\n`, not a line break, and stderr holds the diagnostic on one line. Files: tool, suite. Do it in the same change as T-12 L2.
Why: one token, and a diagnostic line must stay one line.

### T-12 L2

T-12 L2 — APPLY — error messages never carry lone surrogates
Evidence: reproduced: `add-file --path` with bytes `src/\xff.py` → message `…path 'src/\udcff.py'…` as a JSON escape; the parsed string cannot be encoded as strict UTF-8. Same for `invalid block id: T-\udcff` (exit 2).
Decision (ruling). Options: (a) in one place before the report is emitted, pass every `errors[].message` through `message.encode("utf-8", "backslashreplace").decode("utf-8")` — total, one line, shows the byte as the six ASCII characters `\udcff`; (b) render the original byte as `\xff` through a surrogate-escape round trip — prettier, needs a fallback for surrogates that are not escaped bytes; (c) keep. Winner: (a).
Exact behaviour: for every command and every exit code, each error message in stdout and stderr is valid Unicode; a byte of an argument that is not valid UTF-8 appears as backslash, `u`, `dc` and the byte's two hex digits; valid text is unchanged; exit codes and error codes are unchanged. Failing test first: for the `invalid-path`, `invalid-value` and exit-2 block-id refusals with the byte `\xff`, the parsed message encodes with strict UTF-8 and contains the literal text `\udcff`. Files: tool (`main`), suite. Out of scope and unchanged: the `task` key, `stale_temp_files` and `lock_owner` (the last belongs to the lock-metadata proposals).
Why: one place, cannot raise, no new code.

### T-05 L1

T-05 L1 — APPLY — a tests-status change may not break completion on a completed leaf
Evidence: `check_write_invariants` evaluates the completion rule only when `atomic-execution` changes. Reproduced on `atomic-execution: complete`: justified `n-a` → `red` and → `failed` applied; `not-started`, `red`, `pinned`, `failed` inserted on a completed pre-TDD block applied; each with warning `pre-existing-violation`, and `validate` then exits 6 `completion-without-tests`.
Decision (ruling). Options: (a) refuse with `completion-without-tests` — existing code, fails closed, one condition, testable; (b) keep and add a distinct warning — needs a new warning code and still writes a block the tool's own `validate` rejects; (c) keep and document — the warning name stays false for a violation the write created. Winner: (a).
Exact behaviour: a `set` that changes `atomic-tests` (its value differs from the current one, or the segment is inserted) to a value other than `green` or `n-a`, does not change `atomic-execution`, and targets a leaf whose `atomic-execution` is `complete` → exit 6, error `completion-without-tests` with the header line number, result `rejected`, nothing written, no temporary file. It is evaluated after the tests-transition rules, so `downgrade`, `pinned-transition`, `invalid-transition` and `n-a-unjustified` keep precedence (for example `n-a` → `not-started` stays `downgrade`). Unaffected: the same change together with `atomic-execution` set to another value in the same `set` (for example `atomic-tests=red` with `atomic-execution=in-progress` → applied); `red` → `green` on a completed block (repair, applied); naming the current tests value (not a change; `test_status_named_with_its_current_value_is_not_a_transition` stays as is); writes that change neither field (warning `pre-existing-violation` as today). A block that already violates the rule (complete with `red`) cannot move to another non-passing value either.
Files: tool, suite (failing tests first: the six reproduced moves refused; the three unaffected cases), spec, manual, ADR. Spec `### Invariants`: I-5 scope cell becomes "write (when `atomic-execution` changes to `complete`, or when `atomic-tests` changes while an unchanged `atomic-execution` is `complete`), validate (static part)"; accepted-gaps sentence becomes "`failed → red`, `red → n-a` and other moves inside rank 1 are allowed unless I-5 refuses them on a completed leaf; atomic-validation and composite statuses are checked by vocabulary only." Manual `set` row: add "A tests status cannot be changed to a value other than `green` or `n-a` while execution is `complete`." ADR-0022: a dated decision stating this narrowing of the accepted gap of Decision 2.
Why: the tool must not report as applied a write that creates a violation its own `validate` reports; afterwards `pre-existing-violation` means what its name says.

### T-05 O1

T-05 O1 — APPLY — one condition for the pre-existing-violation warning
Evidence: three `warnings.append("pre-existing-violation")` branches in `check_write_invariants`, de-duplicated by `unique`.
Decision: join the three conditions with `or` and append once; behaviour-preserving, covered by `PreExistingViolationTests`. Same change as T-05 L1 (same function).
Why: the function is being edited anyway.

### T-05 O2

T-05 O2 — APPLY — drop the redundant value parameter of execution_transition_error
Evidence: `value` always equals `result["atomic-execution"]`.
Decision: remove the parameter and read the value from `result`. Behaviour-preserving, same change as T-05 L1.
Why: one source for one value.

### T-05 O3

T-05 O3 — APPLY — rename the local unchanged in check_write_invariants
Evidence: local `unchanged` (header fields the write does not change) sits beside the `unchanged` result.
Decision: rename to `kept`. Same change as T-05 L1.
Why: removes a real near-collision at no cost.

### T-05 O4

T-05 O4 — APPLY — comment the rule order of tests_transition_error
Evidence: the order (downgrade, pinned, green source, justification) is decided by statement order only; tests pin it (`justification does not allow a downgrade`, `pinned to justified n-a`).
Decision: add one comment line: "The first broken rule in this order is the one reported." Same change as T-05 L1. Exempt from test-first: a comment has no testable behaviour (unit level considered; the order itself is already pinned).
Why: makes a pinned order a visible decision.

### T-06 L3

T-06 L3 — APPLY — a block name must hold a non-whitespace character
Evidence: `name_problem` refuses only `""`; reproduced: `--name "   "` → applied, header `T-02 |     | atomic-tests: …`; `--name " Demo "` → applied, read back as `' Demo '`.
Decision: the shared rule of T-04 L2: a name with `name.strip() == ""` → exit 6 `invalid-value`, message `name must not be empty or only whitespace`, nothing written (after the revision check, as today for the empty name; a missing `--name` stays exit 2). Leading or trailing spaces around visible text stay accepted and are written as given. Behaviour change: failing tests first (one space, several spaces, a tab; guard: ` Demo ` applied and read back unchanged), added to `test_invalid_name_content_is_invalid_value_and_nothing_changes`. Files: tool, suite; the spec sentence is the one given in T-04 L2 ("A value, note, name or path made only of whitespace counts as empty.").
Why: an empty-looking name segment is as useless as an empty one; surrounding spaces are harmless opaque text and refusing them would be a second rule.

### T-06 O1

T-06 O1 — APPLY — docstrings for check_revision and new_block_input
Evidence: both still have none.
Decision: one line each ("Refuse a write whose expected revision is not the revision of the file read under the lock." / "Collect the init-block inputs from the options, in argument order."). Exempt from test-first: docstrings have no behaviour (unit level considered). Fold into the next tool change.
Why: trivial consistency.

### T-06 O3

T-06 O3 — APPLY — verify_new_block compares the lines outside the inserted block
Evidence: `verify_new_block` compares block shapes only. Reproduced in process: a candidate in which a column-0 foreign line of the section and a line of a later section were altered is accepted by `verify_new_block`. The write algorithm step 9 requires confirming that bytes outside the block are identical.
Decision: add one check to `verify_new_block`: the candidate lines with the inserted window removed (the separator lines and the `count` block lines, that is the lines from the insertion anchor + 1 up to `start + count`) must equal the source lines exactly; a difference → exit 1 `internal-error` "candidate check failed: lines outside the new block changed", nothing written. Unreachable from the command line today, so no caller-visible behaviour changes. Failing test first at unit level: load the tool in process and call `verify_new_block` with such an altered text → expect the internal error (today it returns). Files: tool, suite.
Why: makes a normative step an explicit check instead of a property of the construction.

### T-07 L2

T-07 L2 — APPLY — state that an unchanged result reserves no operation id
Evidence: reproduced: `unchanged` under id `U`, then `U` with other inputs → applied; pinned for the repeat by `test_unchanged_result_records_no_receipt_so_its_repeat_is_unchanged_again`.
Decision: intended; keep. Manual, after the receipts paragraph of "Write protocol": "An `unchanged` result writes nothing and records no receipt, so its operation id is not reserved: the same id may later be applied to that block with any inputs, and the receipts line lists only applied operations." Add the phrase check to `ManualTests` first (failing), then the sentence. Files: manual, suite.
Why: a receipt can only be recorded by writing, and `unchanged` must write nothing (REQ-11).

### T-07 L3

T-07 L3 — APPLY — operation-conflict reports the line of the receipts line
Evidence: `receipt_matches` raises without a line; reproduced: `errors[0]` has no `line`.
Decision: pass the 1-based line of the block's `state_receipts:` line as `line` of the `operation-conflict` error (all four write commands). Additive output; exit 8 and message unchanged. Failing test first (assert `line` equals the receipts line number) in `ReceiptRepeatTests`. Files: tool, suite.
Why: points the reader at the recorded entry; `line` is already an optional error key.

### T-07 O1

T-07 O1 — APPLY — one separator constant for receipts
Evidence: `receipts_problem` splits on the literal `", "`; `receipt_entries` and `build_candidate` use `RECEIPT_SEPARATOR`.
Decision: use `RECEIPT_SEPARATOR` in `receipts_problem`. Behaviour-preserving; covered by the receipts tests. Fold into the next tool change.
Why: reader and writer of one format must share its constant.

### T-12 O1

T-12 O1 — APPLY — blank line after the summary of the input_digest docstring
Evidence: the summary line runs straight into the explanation.
Decision: insert the blank line; fold into the next tool change. Exempt from test-first: docstring layout (unit level considered, no behaviour).
Why: trivial.

### T-13 L1

T-13 L1 — APPLY — a field line named like a header status is an ordinary unknown field
Evidence: reproduced: a leaf with the field line `  atomic-execution: weird`: `get` reports it under `fields` with `known: false` and `validate` is `valid`; `set --field atomic-execution=complete --field atomic-tests=green` → exit 1 `internal-error` "a written value does not read back", with or without continuation lines under that line; also with the header segment absent and a field line `  atomic-tests: weird`. Cause: the candidate is correct; `verify_candidate` merges header values and field-line values into one dictionary, so the field line shadows the header value in the read-back check.
Decision (ruling). Options: (a) treat the line as the unknown field the reader already reports and fix the read-back check — no new code, matches "unknown fields are preserved", smallest blast radius; (b) make such a block malformed (exit 3) — turns blocks that `validate` accepts today into structure errors for every command. Winner: (a).
Exact behaviour: `set` on a header status of such a block changes the header segment only → exit 0 `applied`, `changed_fields` the header field(s) and `state_receipts`, the status-named field line and its continuation lines byte-identical; naming the current header value → `unchanged` (the continuation refusal never applies to a status name; REQ-27 covers `last_action` and `blocker` only). In `verify_candidate` compare header statuses with the re-parsed header fields and field lines with the re-parsed field groups separately. Failing tests first: the three reproduced cases applied with the field line unchanged; guard: current value named with continuation lines under the status-named line → `unchanged` (pins the exclusion in `continued_field`; mutation: removing the exclusion turns it into exit 6). Files: tool, suite, spec (`## Data Model`, Repeated field row or below the table): "A field line whose name is a header field name is an unknown field: it is preserved and never read or written as the header status."
Why: an internal error for input the grammar allows is a tool fault; the reader already defines what the line is.

### T-13 O2

T-13 O2 — APPLY — refusal message names both ways out
Evidence: `check_field_changes` message ends "append a note instead"; the manual names the manual procedure or a note.
Decision: message becomes `block <id>: <name> has continuation lines, which set does not replace; edit the block by the manual procedure or append a note`. The frozen assertions (`continuation line`, the field name) still hold. Same change as T-04 L1 (sibling message).
Why: one wording for tool and manual.

### I7

I7 — APPLY — a state file the caller cannot write is not replaced
Evidence: reproduced: `state.md` with mode 0444 (and 0400), `set` → exit 0 `applied`, new inode, mode kept; the rename needs only directory permission. The spec edge-case table already lists "permission denied → exit 7, `state.md` unchanged".
Decision (ruling). Options: (a) refuse with the existing `io-error` — honours the read-only marker, fails closed, one system call, testable; (b) document only — the tool keeps overwriting a file its owner marked read-only; (c) refuse on any ownership difference too — needs policy for group-writable shared files. Winner: (a), plus one manual sentence for ownership.
Exact behaviour: when a write has built and verified its candidate (write step 10), the tool first opens `state.md` for writing without truncation and without following links (`O_WRONLY | O_NOFOLLOW`) and closes it at once; if that open fails → exit 7, error `io-error`, message `state.md is not writable: <reason>`, result `rejected`, `source_revision` and `result_revision` both the revision read, `state.md` unchanged (same inode, mode, mtime), no temporary file created; the lock file may exist. Results decided earlier are unchanged on a read-only file: `already_applied`, `unchanged`, and exits 2, 3, 4, 5, 6, 8. Failing test first (skipped for the superuser, like `test_unwritable_task_directory_exits_7_with_the_file_unchanged`): mode 0444 → exit 7 `io-error`, snapshot unchanged, no temporary file; a repeat of an applied operation on the now read-only file → `already_applied`. Files: tool (`replace_state`), suite, spec, manual. Spec write step 10, prepend: "Open `state.md` for writing without truncation; failure is exit 7 `io-error` before any temporary file exists." Edge-case row: "`state.md` not writable by the caller | Exit 7 `io-error`, `state.md` unchanged, no temporary file | REQ-07". Manual Limits: "A `state.md` the caller cannot open for writing is never replaced (exit 7, `io-error`). An applied write replaces the file by rename, so the new file belongs to the user who ran the tool; its permission bits are kept, its owner and group are not."
Why: a read-only bit is an explicit instruction not to modify the file; the code and the edge-case row already exist.
