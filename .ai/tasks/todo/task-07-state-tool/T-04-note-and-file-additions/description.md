## Goal
Notes are appended and target files are added through `append-note`, `add-file` and
`set --note` without altering existing note text or existing entries.

## Context
- Dependencies: T-03 — reuses the write transaction.
- Constraints: same runtime limits as the tool. Contract: task spec REQ-17, REQ-18,
  REQ-23, `### Commands` (text and path rules, repeated inputs), `## Data Model`
  (insertion of a missing known field). Values are stored literally and never
  interpreted. English only; no planning identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: append-only notes and add-only target files share one serialization concern —
  growing a field group without rewriting it — distinct from replacing a field value.

Off-limits: existing note text and existing `target_files:` entries are never changed or
removed; no lifecycle invariants; no file under `workflows/` or `rules/`.

## Scope
- **In scope:** `append-note --note TEXT …`; `add-file --path P …`; `--note` on `set`,
  applied in the same replace as its fields; note placement rules; path content rules and
  duplicate handling; the `unchanged` result for `add-file`.
- **Out of scope:** `init-block --note` / `--target-file` (block-initialization subtask);
  receipt lookup for repeats.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below.
2. Implement note placement: on the `notes:` line when the block has exactly one `notes:`
   line with an empty value and no continuation lines; as a new `  notes: <note>` line at
   the canonical position when the block has none; otherwise as a continuation line
   indented by 9 spaces after the last line of the last `notes` group; further notes of
   the same call follow as continuation lines.
3. Validate note text (single line, no CR, LF or NUL → exit 6 `invalid-value`) before any
   change, so that one invalid note writes none.
4. Implement `append-note` and `--note` on `set` (fields and notes in one replace).
5. Implement path rules (non-empty, relative, no `..` segment, no leading `./`, no `,`, no
   trailing `/` → exit 6 `invalid-path`) and `add-file`: split the existing value on `, `,
   compare by exact string equality, append new paths with `, `, write a repeated input
   path once at its first position, insert a missing `target_files:` line at its canonical
   position, return `unchanged` when every path is already listed.
6. Refresh the pinned source-guard fingerprint and run the guard suites and the focused
   state-tool mode.

## Acceptance Criteria
- Given empty `notes:`, `append-note --note a --note b` makes the block read `  notes: a`
  followed by `         b`.
- Given non-empty notes with continuation lines, the new line follows the last
  continuation line; given a block with four `notes:` field groups, the new line follows
  the last line of the fourth group; existing note bytes are identical.
- A note containing LF exits 6 and no note from the same call is written.
- The note `$(touch pwned); rm -rf x` is stored literally and no `pwned` file exists.
- Given `target_files: a.sh`, `add-file --path b.sh --path a.sh` gives
  `target_files: a.sh, b.sh`; `add-file --path a.sh` returns `unchanged` and the file is
  unchanged; `add-file --path c.sh --path c.sh` gives `target_files: a.sh, c.sh`.
- `/abs`, `../x`, `a,b` and an empty path each exit 6 `invalid-path`.
- Given a leaf without `notes:` and without `target_files:`, `append-note --note a`
  inserts `  notes: a` after the `blocker:` group and `add-file --path b.sh` inserts
  `  target_files: b.sh` after the `last_action:` group.
- `set --field last_action=x --note y` applies both changes in one revision and lists
  `last_action`, `notes`, `state_receipts` in `changed_fields`.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Empty notes, two notes → first on the field line, second as a 9-space continuation.
  - Existing continuation lines, four `notes` groups → appended after the last line.
  - Note with LF → exit 6, nothing written.
  - Shell metacharacters → literal storage, no side effect.
  - Add, repeat, already-listed paths → expected line / `unchanged`.
  - Invalid paths → exit 6 `invalid-path`.
  - Missing `notes:` / `target_files:` → inserted at canonical positions.
  - `set` with a field and a note → one replace, both changes.
- **Edge cases:** quoted note value, blank lines inside a continuation run, existing
  `target_files:` entries containing spaces or prose, empty `target_files:` value.
