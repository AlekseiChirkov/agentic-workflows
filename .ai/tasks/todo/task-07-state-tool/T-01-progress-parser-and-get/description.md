## Goal
`python3 scripts/state-tool.py get` reads the `## Subtask Progress` section of one task
`state.md` through a structural parser and prints one JSON object describing its blocks,
without creating, modifying or deleting any file.

## Context
- Dependencies: none — first subtask; it creates the tool file and its acceptance suite.
- Constraints: Python 3.11+, standard library only, one file `scripts/state-tool.py`; no
  `subprocess`, `os.system`, `os.exec*`, `eval`, `exec` in the tool. The exact contract is
  the task spec (`.ai/specs/07-state-tool.md`): `## Data Model`, `### Commands`,
  `### Read outcomes`, `### Output`, `### Exit codes and error codes`,
  `### Contract version check`. English only; no planning identifiers in code, tests,
  comments or documentation.
- Pinned fixtures: every change under `tests/` or to `scripts/validate-contracts.sh`
  invalidates the source-guard inventory fingerprint and may need reviewed call-site
  records and a validator inventory amendment. Follow
  `tests/fixtures/validator-runtime/README.md`; the guard suites must pass at the end.
- Reason: the parser and the read command are the foundation every later command reuses;
  they are verifiable alone because reads need no lock, revision or write path.

Off-limits: no file under `workflows/`; no change to `scripts/sync.sh`; no write command
behaviour; no change to `rules/` in this subtask.

## Scope
- **In scope:** tool skeleton and command dispatch; Python-version guard; root, task and
  `state.md` path checks for reads; encoding checks; fence-aware section and block parser;
  the four vocabulary constants; contract-version comparison for reads; `get` with
  `--block` and `--field`; the common JSON output keys; the acceptance-suite harness and
  its registration in the validator.
- **Out of scope:** `validate`; every write command; lock, revision, receipts handling
  beyond reporting a malformed `state_receipts:` line as a warning.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `scripts/validate-contracts.sh`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`,
  `tests/fixtures/validator-runtime/inventory-amendment.json`

## Steps
1. Create `tests/state-tool.py`: a `unittest` suite with disposable task-directory
   fixtures, a helper that runs the tool as a subprocess and returns exit code, stdout and
   stderr, and a snapshot helper comparing bytes, mode and mtime of every file in the task
   directory.
2. Create `scripts/state-tool.py` with the Python-version guard placed before every import
   other than `sys` (older than 3.11 → exit 7, `python-too-old`), then command dispatch;
   an unknown command exits 2 with `unknown-command`.
3. Define the vocabulary constants as module-level tuples of string literals, one line
   each, in the order of the anchored lines of `rules/workflow-globals.md`:
   `ATOMIC_STATUS_VALUES`, `ATOMIC_TESTS_VALUES`, `ROLLUP_VALUES`,
   `INTEGRATION_VALIDATION_VALUES`.
4. Implement argument validation for `get` (required `--root`, `--task`; `--block` must
   match the block-id pattern, otherwise exit 2 `invalid-arguments`).
5. Resolve root and task with `realpath`; refuse a task outside root (exit 2,
   `path-outside-root`), a missing `state.md` (exit 3, `state-missing`), and a symlinked or
   non-regular `state.md` (exit 7, `unsafe-state-file`); refuse non-UTF-8, BOM or CR bytes
   (exit 3, `unsupported-encoding`).
6. Implement the fence-aware section locator (`section-missing`, `section-duplicate`) and
   the block parser: header pattern, prefix, header fields, field lines, continuation
   lines, blank-line rule, foreign lines, block end, repeated `notes` groups, malformed
   lines and repeated known fields.
7. Implement the contract-version comparison against `<script dir>/../VERSION`; for reads
   it only adds the warning `unsupported-contract-version`.
8. Implement `get` output: common keys, `contract_version`, `blocks` with `block_id`,
   `block_kind`, `prefix`, `name`, `header_fields`, `fields` (`name`, `value`,
   `continuation`, `known`), `pre_tdd_exception`; the `--field` filter; warnings
   (`unrecognized-prefix`, `unknown-header-field`, `required-field-missing`,
   `malformed-receipts`, problems in other blocks); `stale_temp_files`; `null` for keys
   that cannot be computed; diagnostics on stderr only.
9. Register the suite in `scripts/validate-contracts.sh`: a focused `--state-tool-only`
   mode next to the other focused modes and a `test_state_tool_acceptance` check in the
   default run; then refresh the pinned validator-runtime fixtures by the maintenance
   procedure and run the guard suites.

## Acceptance Criteria
- Given a fixture with leaf `T-01`, composite `[composite] T-02`, and a fenced block
  containing `## Subtask Progress` and a `T-01 | Example | …` header, `get --block T-01`
  and `get --block T-02` exit 0 with `block_kind` `leaf` and `composite`, and the fenced
  lines are not reported.
- For every `get` run, every file in the task directory is unchanged (bytes, mode, mtime)
  and no file, including `.state-tool.lock`, is created; stdout parses as exactly one JSON
  object with `schema_version` 1.
- A leaf without `atomic-tests:` and with `atomic-execution: in-progress` reports
  `pre_tdd_exception` `applicable`; a leaf with `atomic-tests: not-started` and
  `atomic-execution: not-started` reports `not-applicable`.
- An unknown command and `get --block T-1` exit 2; every refusal writes a non-empty stderr.
- `get --block T-03` on a block headed `[x] T-03 | …` exits 0 with `prefix` `[x]` and
  warning `unrecognized-prefix`; a leaf header containing `atomic-foo: x` exits 0 with
  warning `unknown-header-field`; a file with `contract_version: 99.0.0` exits 0 with
  warning `unsupported-contract-version`; with `contract_version: 0.9.0` and the tool's
  `VERSION` file removed, `get` exits 0 with that warning.
- Given duplicated `T-02` and well-formed `T-01`, `get --block T-01` exits 0 with a
  warning and `get` without `--block` exits 3 `rejected` with `block-duplicate` and no
  `blocks` key; with no `state.md`, `get` exits 3 `state-missing`;
  `get --block T-01 --field pr` where `pr` is absent exits 0 with empty `header_fields`
  and `fields`.
- A leaf without `notes:` and `target_files:` makes `get` exit 0 with warning
  `required-field-missing`; a `T-01` whose `state_receipts:` line holds 21 entries makes
  `get --block T-01` exit 0 with warning `malformed-receipts`.
- With `state.md` as a symbolic link, `get` exits 7 `unsafe-state-file`; with the task
  outside root, `get` exits 2 `path-outside-root`.
- A static AST scan of the tool finds only standard-library imports and none of
  `subprocess`, `os.system`, `os.exec*`, `eval`, `exec`, `shell=True`; the version guard
  precedes all imports other than `sys`; with the `fcntl` import blocked, `get` exits 0.
- `bash scripts/validate-contracts.sh --state-tool-only` runs the suite and exits 0, and
  the source-guard suites pass.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures); unit for the AST
  scan.
- **Scenarios:**
  - Leaf, composite and fenced look-alike → kinds reported, fenced lines ignored.
  - Any `get` → task directory snapshot identical, single JSON object on stdout.
  - Pre-TDD shapes → `applicable` / `not-applicable`.
  - Unknown command, malformed block id → exit 2 with stderr text.
  - Unrecognized prefix, unknown header field, newer or uncheckable contract version →
    exit 0 with the named warning.
  - Duplicate block, missing `state.md`, absent `--field` → the listed exits and shapes.
  - Missing required fields, 21 receipt entries → exit 0 with the named warning.
  - Symlinked `state.md`, task outside root → exit 7 / exit 2.
  - AST scan, guard position, blocked `fcntl` → no forbidden construct; `get` still works.
  - Focused validator mode → exit 0.
- **Edge cases:** empty file, section with no blocks, missing final newline, blank lines
  inside continuation runs, quoted note values, column-0 foreign lines, several `notes`
  groups, tab-indented and one-space lines, CR/BOM/invalid UTF-8.
