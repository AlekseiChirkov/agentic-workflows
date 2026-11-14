## Goal
`set` refuses to change a field whose existing value has continuation lines, so that old continuation text can never remain under a new value.

## Context
- Dependencies: T-03 (field replacement), T-05 (the order of write rules), T-12 (same files; stacked after it).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`. Owner ruling of 2026-11-14, recorded in the task assumptions: `set` on a field whose existing value has continuation lines is refused with exit 6 and nothing changes; `set` never deletes existing text. The refusal is a value rule of the write order: it is decided with the other field rules, after the receipt and revision checks and before the unchanged shortcut, so that naming such a field with its current first-line value is refused too. Fields that `set` may change on a field line are `last_action` and `blocker`; notes and target files are not changed by `set --field`. A blank line followed by a continuation line belongs to the field group, as the grammar defines. English only; no planning identifiers or specification labels in code, tests, comments or documentation.
- Pinned fixtures: a change to `tests/state-tool.py` or `scripts/state-tool.py` invalidates the suite's pinned resource row, the amendment digest, the source-guard inventory fingerprint, the tool's dependency digests and the manifest digest; refresh them once at the end. Do not insert lines in `docs/USAGE.md` above its section 11: the repository's identity ledger pins a line number earlier in that file.
- Reason: an important review finding with an owner ruling on behaviour the specification does not define.

Off-limits: no deletion or rewriting of existing continuation lines; no change to how notes or target files grow; no file under `workflows/` or `rules/`; no change to `scripts/validate-contracts.sh` or the oracle mechanism.

## Scope
- **In scope:** the refusal in `set` for `last_action` and `blocker` when the field group has continuation lines; its error code and message; one sentence in the Limits of the manual's State Tool section; suite cases.
- **Out of scope:** replacing a whole field group; header status changes (they have no continuation lines); `append-note`, `add-file`, `init-block`.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`, `docs/USAGE.md`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases: `set` on `blocker` and on `last_action` whose group has one continuation line, several, and a blank line followed by one; the same with the current first-line value; a field without continuation lines next to another field that has them.
2. Refuse such a `set` with exit 6 and the existing content error code for values (`invalid-value`), a message naming the field and the reason, the no-bypass sentence, one JSON object, nothing written and no receipt; decide it with the field rules, before the unchanged shortcut.
3. Confirm that a `set` naming several fields is refused as a whole when one of them has continuation lines, and that fields without continuation lines behave as before.
4. Add one sentence to the Limits of the manual's State Tool section: `set` does not change a field whose value continues on following lines; edit such a block by the manual procedure or append a note.
5. Refresh the pinned fixtures once and run the suite, the focused validator mode, the inventory oracle suite and the source guard.

## Acceptance Criteria
- Given `  blocker: waiting for review` followed by a continuation line, `set --field blocker=none` exits 6 with `invalid-value`, prints one JSON object and the no-bypass sentence, and the task directory is unchanged apart from the lock file; the same holds for `last_action`, for several continuation lines, and for a blank line followed by a continuation line.
- `set --field blocker=<its current first-line value>` on such a field is refused the same way, not reported as unchanged.
- `set --field last_action=x --field blocker=none` where only `blocker` has continuation lines changes nothing.
- A `set` on a field without continuation lines in a block where another field has them is applied as before.
- The manual's Limits state the rule, and no line above section 11 of the manual moved.
- All existing tests pass unchanged.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures); smoke for the manual sentence.
- **Scenarios:**
  - Field with one, several, or blank-then-one continuation lines → exit 6, nothing written.
  - Current value named on such a field → exit 6.
  - Several fields, one with continuation lines → nothing written.
  - Neighbouring field without continuation lines → applied.
  - Manual → sentence present; earlier lines unmoved.
- **Edge cases:** continuation lines under `last_action` at the top of a block; an in-block fence directly after the field line (fenced lines are not continuation lines); a stale revision together with such a field (revision conflict first).
