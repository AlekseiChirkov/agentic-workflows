## Goal
A write command repeated with the same `operation_id` and the same inputs returns
`already_applied` without writing, a reused id with different inputs is refused, and each
block keeps only its 20 newest receipts.

## Context
- Dependencies: T-03 (receipt append and input digest), T-04 and T-06 (the other write
  commands whose repeats must be idempotent), T-02 (receipts format check).
- Constraints: same runtime limits as the tool. Contract: task spec REQ-08, REQ-19,
  REQ-02 (malformed receipts on a write), `### New field state_receipts:`, write algorithm
  step 6 (receipt check before the revision check). English only; no planning identifiers
  in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: idempotency is one rule set over the receipt field, shared by all four write
  commands and verifiable only once they all exist.

Off-limits: receipts are never stored outside the block; no historical revision is stored;
no file under `workflows/` or `rules/`.

## Scope
- **In scope:** receipt lookup before the revision check; `already_applied` (exit 0, no
  write, regardless of `--expected-revision`); `operation-conflict` (exit 8) with the
  no-bypass sentence; 20-entry cap dropping the oldest; write refusal on a malformed
  `state_receipts:` line (exit 3 `malformed-receipts`); `init-block` repeat on an existing
  id with a matching receipt.
- **Out of scope:** retry after process death (interruption-recovery subtask); any
  receipt storage change.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below.
2. Refuse a write whose target block has a malformed `state_receipts:` line (over 20
   entries, bad entry, repeated id) with exit 3 `malformed-receipts`.
3. Implement the receipt check directly after locating the block and before the revision
   check: same id and digest → `already_applied`, exit 0, `changed_fields` empty,
   `result_revision` equal to the current revision; same id and different digest → exit 8
   `operation-conflict`, stderr carrying the no-bypass sentence.
4. Apply the lookup to `init-block`: an existing id whose block holds a matching receipt
   returns `already_applied`; without one it stays `block-exists`.
5. Enforce the cap on insert: keep the 20 newest entries, oldest first, dropping the
   oldest.
6. Verify that the input digest covers the command, block id and inputs exactly as the
   spec defines (fields sorted by name; notes, paths and children in argument order;
   repeated paths as given).
7. Refresh the pinned source-guard fingerprint and run the guard suites and the focused
   state-tool mode.

## Acceptance Criteria
- For each of `set`, `append-note`, `add-file` and `init-block` applied once with
  `operation_id` X, a repeat with identical inputs and a stale revision exits 0
  `already_applied` and the file is unchanged.
- Reusing X with different inputs exits 8 `operation-conflict`, the file is unchanged, and
  stderr contains `Do not edit state.md by hand to bypass this refusal.`
- After 21 applied operations on one block, its `state_receipts:` line holds the 20 newest
  entries in application order.
- Repeating the first of those 21 operations with a stale revision is treated as new and
  exits 4 `revision-conflict`.
- Given a `T-01` whose `state_receipts:` line holds 21 entries, `set` on `T-01` exits 3
  `malformed-receipts` with the fixture unchanged, while a `set` on another well-formed
  block is applied.
- The same field pairs given in a different argument order produce the same digest
  (`already_applied`); the same notes in a different order produce `operation-conflict`.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Repeat of each write command with a stale revision → `already_applied`, unchanged.
  - Same id, different inputs → exit 8 with the sentence.
  - 21 operations → 20 newest entries in order.
  - Repeat after the receipt was dropped → exit 4.
  - Malformed receipts line → exit 3 on that block only.
  - Field order versus note order → same digest / conflict.
- **Edge cases:** an `unchanged` result records no receipt, so its repeat is `unchanged`
  again; receipts on a composite block; operation id at the 64-character limit.
