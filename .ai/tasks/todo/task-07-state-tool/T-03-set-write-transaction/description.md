## Goal
`python3 scripts/state-tool.py set` changes the named fields of one block under the
per-task lock and the expected-revision check, records a receipt, and replaces `state.md`
with one rename so that only the changed lines differ.

## Context
- Dependencies: T-01 (parser, path checks, output), T-02 (invariant predicates for
  vocabulary values).
- Constraints: same runtime limits as the tool. Contract: task spec
  `### Write algorithm (normative order)`, `### Field writability`,
  `### New field state_receipts:` (entry and input-digest format), `### Commands`,
  `### Output`, REQ-01, REQ-03, REQ-05, REQ-06, REQ-07, REQ-11, REQ-13, REQ-15, REQ-19.
  Input values are never passed to a shell or interpreter. English only; no planning
  identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: the write transaction (lock, revision, narrow serialization, receipt, atomic
  replace) is the single mechanism every mutating command shares; `set` on plain fields
  exercises it end to end.

Off-limits: no `--note` handling, lifecycle invariants (I-2–I-5, I-9, I-10), receipt
lookup for repeated operations, or lock-contention reporting — later subtasks own them;
no file other than `state.md`, `.state-tool.lock` and the tool's own temporary file is
written by the tool; no file under `workflows/` or `rules/`.

## Scope
- **In scope:** write-argument validation; `fcntl` availability check; lock acquisition
  with the wait bound and owner metadata; full read with identity and revision;
  write-side structure and version refusals; I-1 and I-7 checks and value content rules;
  header and field-line serialization including insertion of a missing known field and of
  the `atomic-tests` header segment; the `unchanged` shortcut; receipt append with the
  input digest; candidate re-parse with the I-8 check; temporary file, sync, identity
  recheck, rename, directory sync; write output keys; the no-bypass sentence on stderr for
  exits 4 and 6.
- **Out of scope:** `--note`; `append-note`, `add-file`, `init-block`; `already_applied`
  and `operation-conflict`; receipt cap; lock-busy details; fault seam.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below.
2. Validate write arguments: required `--block`, `--expected-revision`
   (`^sha256:[0-9a-f]{64}$`, else `malformed-revision`), `--operation-id` (pattern, else
   `invalid-operation-id`), `--field NAME=VALUE` split at the first `=`, a repeated field
   name, `--lock-wait-seconds` 0–600 → exit 2; then check `fcntl`.
3. Open `<task>/.state-tool.lock` with `O_NOFOLLOW` (mode 0600), acquire
   `flock(LOCK_EX | LOCK_NB)` with 25 ms retries until the wait bound, then truncate and
   write `{"owner_token", "pid", "host", "started_at"}`.
4. Read the full bytes; record device, inode and revision; apply the encoding and
   contract-version checks (write: exit 3 `unsupported-contract-version`).
5. Parse and locate the block; refuse a duplicated or malformed target, an unrecognized
   prefix or an unknown header field with exit 3.
6. Compare `--expected-revision` with the current revision → exit 4 `revision-conflict`.
7. Check I-7 (`read-only-field`, `field-not-applicable`) and value content rules
   (single-line text, non-empty `last_action` / `blocker`, I-1 vocabulary); return
   `unchanged` without writing when no value changes.
8. Build the candidate: replace changed header segments and field lines in place, insert a
   missing known field at its canonical position, insert `atomic-tests: <value> | ` before
   `atomic-execution:` when the segment is absent.
9. Append `<operation_id>#<input digest>` as the last `state_receipts:` entry (line
   inserted at its canonical position or replaced in place); re-parse the candidate and
   confirm bytes outside the block and every unchanged line are identical.
10. Create `.state.md.<owner_token>.tmp` with `O_CREAT | O_EXCL | O_NOFOLLOW` and the
    original permission bits, write, `fsync`; re-check identity and revision of `state.md`
    (mismatch → remove own temporary file, exit 4 `state-file-changed`); `os.replace`;
    `fsync` the directory; I/O failure → exit 7 with `state.md` unchanged.
11. Print the write result (`operation_id`, `block_id`, `block_kind`, `source_revision`,
    `result_revision`, `changed_fields`); print the sentence
    `Do not edit state.md by hand to bypass this refusal.` on stderr for exits 4 and 6.
12. Refresh the pinned source-guard fingerprint and run the guard suites and the focused
    state-tool mode.

## Acceptance Criteria
- Given a leaf `T-01` with, in order, `last_action:`, an empty `target_files:`,
  `blocker: none`, a quoted `notes:` value with 9-space continuation lines including an
  inner blank line, and `  verification: x`, plus a column-0 foreign line after the block
  and text in other sections, `set --block T-01 --field last_action=done` applied on two
  identical copies gives a diff of exactly the changed `last_action` line plus one
  `state_receipts:` line directly after the last `notes` continuation line and before
  `verification: x`; both results are byte-identical.
- `set --field last_action=x` returns `applied` with `changed_fields`
  `["last_action", "state_receipts"]` and every header status unchanged.
- Given a leaf missing `blocker:` and without `atomic-tests:`,
  `set --field blocker=none --field atomic-tests=red` inserts `  blocker: none` directly
  after `target_files:` and `atomic-tests: red | ` directly before `atomic-execution:`;
  no other line moves.
- Given revision R0, after writer A applies with R0, writer B with R0 exits 4
  `revision-conflict` and the file equals A's result; after another section changes,
  a `set` with R0 exits 4 and the other section's new text is retained.
- With two progress sections, two `T-01` headers, or a tab-indented line in `T-01`, a
  `set` on `T-01` exits 3 with `section-duplicate`, `block-duplicate` or `malformed-block`
  and `state.md` is unchanged with no temporary file left.
- `set --field atomic-execution=done` exits 6 `invalid-value`; a block with `atomic-foo: x`
  in the header exits 3 `unknown-header-field`; a block headed `[x] T-03 | …` exits 3
  `unrecognized-prefix`; `contract_version: 99.0.0`, or `contract_version: 0.9.0` with the
  tool's `VERSION` removed, exits 3 `unsupported-contract-version`; `state.md` is
  unchanged in each case.
- `set --field pr=<its current value>` exits 6 `read-only-field`; `set` with values equal
  to the current ones returns `unchanged`, writes nothing and adds no receipt.
- A write without `--operation-id`, a malformed `--expected-revision`, an invalid
  operation id, or one field named twice exits 2; stdout is one JSON object each time.
- Refusals with exit 4 and exit 6 print `Do not edit state.md by hand to bypass this
  refusal.` on stderr.
- A file without a final newline keeps that state after an applied `set`.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Rich block, one field changed on two copies → two-line diff, identical results.
  - Plain field change → `changed_fields` and untouched header.
  - Missing field and missing header segment → canonical insertion positions.
  - Two writers, foreign-section change → exit 4, expected content retained.
  - Damaged structure → exit 3, no change, no temporary file.
  - Bad value, unknown header field, unrecognized prefix, newer or uncheckable version →
    exit 6 / 3 with the named code.
  - Read-only field, unchanged values → exit 6 / `unchanged`.
  - Invalid invocations → exit 2 with one JSON object.
  - Refusal text → sentence present on stderr.
  - Missing final newline → preserved.
- **Edge cases:** field insertion when no earlier known field exists (directly after the
  header), out-of-order known fields, unknown repeated fields, value containing `=` or
  `|`-free punctuation, empty value refusal, values with CR/LF/NUL.
