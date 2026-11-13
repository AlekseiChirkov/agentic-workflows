## Goal
`python3 scripts/state-tool.py validate` reports whether the progress section, or one
block of it, satisfies the structure rules and the static invariants, exiting 0, 3 or 6
without touching any file.

## Context
- Dependencies: T-01 — reuses its parser, path checks and JSON output.
- Constraints: same runtime limits as the tool (Python 3.11+, standard library, single
  file). Contract: task spec `### Invariants`, `### Read outcomes`,
  `### Exit codes and error codes` (the `validate` paragraph), `### New field state_receipts:`.
  English only; no planning identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md` and finish with the
  guard suites passing.
- Reason: static validation is a separate read command with its own exit-code split and
  its own invariant set; later write subtasks reuse the invariant predicates.

Off-limits: no write command behaviour; no file under `workflows/` or `rules/`; no change
to `scripts/validate-task.sh` (its receipts check belongs to the grammar-extension subtask).

## Scope
- **In scope:** the `validate` command with optional `--block`; static checks: structure,
  I-1, I-4, I-5 (static part), I-6, `state_receipts:` format; the 3-before-6 exit rule;
  `result` `valid` / `invalid`; `stale_temp_files` listing.
- **Out of scope:** I-2, I-3, I-7–I-10 (they need a previous value); any repair.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for `validate` covering each static check and the exit split.
2. Implement invariant predicates as functions independent of the command line: header
   values in their vocabulary (I-1), `n-a` justified by notes text containing
   `tdd: none — ` (I-4), static completion rule (I-5), required fields per kind (I-6).
3. Implement the `state_receipts:` format check: 1–20 entries, entry pattern
   `<operation_id>#<16 lowercase hex>`, unique operation ids → `malformed-receipts`.
4. Implement `validate`: without `--block` check every block and list every error; with
   `--block X` check X only; unrecognized prefix and unknown header field are warnings.
5. Apply the exit rule: path and file refusals keep exits 2 and 7; otherwise 3 when any
   structure error exists, else 6 when any invariant error exists, else 0.
6. Refresh the pinned source-guard fingerprint and run the guard suites and the focused
   state-tool mode.

## Acceptance Criteria
- A well-formed fixture exits 0 with `result` `valid`; every file in the task directory is
  unchanged and no file is created.
- A leaf with `atomic-tests: n-a` whose notes contain `tdd: none - x` (hyphen) exits 6 with
  `n-a-unjustified`; with `tdd: none — x` (em dash) it exits 0.
- A leaf without `notes:` and without `target_files:` exits 6 with
  `required-field-missing`; a composite without `children:` exits 6 with the same code.
- A leaf with `atomic-execution: complete` and `atomic-tests: red` exits 6 with
  `completion-without-tests`; with `green` or `n-a` (justified) it exits 0; with
  `atomic-tests` absent and the note `pre-TDD task, TDD step skipped` it exits 0.
- A header status outside its vocabulary exits 6 with `invalid-value`.
- A duplicated `T-02` exits 3 `invalid`; two progress sections exit 3; a `T-01` whose
  `state_receipts:` line holds 21 entries, a malformed entry or a repeated operation id
  exits 3 with `malformed-receipts`.
- A fixture with both a structure error and an invariant error exits 3 and lists both.
- A leftover file `.state.md.0123456789abcdef0123456789abcdef.tmp` in the task directory
  is listed in `stale_temp_files` and still exists afterwards.
- `validate --block T-01` on a file where only `T-02` violates an invariant exits 0.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Well-formed fixture → exit 0, `valid`, snapshot identical.
  - Hyphen versus em-dash justification → exit 6 / exit 0.
  - Missing required fields per kind → exit 6 `required-field-missing`.
  - Completion with `red`, `green`, justified `n-a`, pre-TDD note → 6 / 0 / 0 / 0.
  - Out-of-vocabulary status → exit 6 `invalid-value`.
  - Duplicate block, duplicate section, bad receipts line → exit 3.
  - Mixed structure and invariant errors → exit 3, both listed.
  - Leftover temporary file → listed, not deleted.
  - `--block` scoping → other blocks' invariant errors ignored.
- **Edge cases:** empty section, composite-only section, several `notes` groups carrying
  the justification in a later group, receipts line with exactly 20 entries.
