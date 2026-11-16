## Goal
A write command given a field value, note, path or block name that is not valid UTF-8 is refused with exit 6 and the matching content error code, instead of ending with an internal error.

## Context
- Dependencies: T-07 (it placed the receipt input digest ahead of the content rules), T-03, T-04, T-06 (the content rules).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`. Contract: the task spec's text-input rule (single-line UTF-8 without CR, LF or NUL), "value and path content rules are exit 6 (`invalid-value`, `invalid-path`)", and the normative write order (argument validation → lock → read → parse → receipt check → revision check → content rules). The receipt check needs the input digest, so the digest must tolerate or pre-screen such input without changing any digest of valid input: receipts already written must keep matching. Every existing refusal order stays as it is (a stale revision is still exit 4 before a content refusal; a matching receipt is still already applied). English only; no planning identifiers or specification labels in code, tests or comments.
- Pinned fixtures: a change to `tests/state-tool.py` or `scripts/state-tool.py` invalidates the suite's pinned resource row in the validator inventory amendment, the amendment digest, the source-guard inventory fingerprint, the tool's dependency digests in the reviewed records and the manifest digest; refresh them once at the end by the fixture maintenance procedure.
- Reason: an important review finding; a regression between two delivered changes.

Off-limits: no change to the digest of any valid input; no change to the order of refusals for valid UTF-8 input; no file under `workflows/` or `rules/`; no change to `scripts/validate-contracts.sh` or the oracle mechanism.

## Scope
- **In scope:** the refusal of non-UTF-8 text in `--field` values, `--note`, `--path`, `--target-file` and `--name` for `set`, `append-note`, `add-file` and `init-block`; where in the write order it is decided; suite cases.
- **Out of scope:** non-UTF-8 bytes in option names, block ids, operation ids or task paths (argument validation already owns them); read commands.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases: each of the four write commands with a text input that is not valid UTF-8, at the current revision and at a stale revision, and a repeat of such a call.
2. Make the write path decide such input by the content rules: exit 6 with `invalid-value` (field value, note, name) or `invalid-path` (path, target file), the no-bypass sentence on stderr, exactly one JSON object on stdout, nothing written and no temporary file.
3. Keep the receipt lookup and the revision check where they are for valid input, and confirm that the digests of valid inputs are byte-identical to before.
4. Refresh the pinned fixtures once and run the suite, the focused validator mode, the inventory oracle suite and the source guard.

## Acceptance Criteria
- `set --field` with a value, `append-note --note`, `add-file --path`, `init-block --name` and `init-block --target-file` given text that is not valid UTF-8 each exit 6 with `invalid-value` or `invalid-path`, print exactly one JSON object and the no-bypass sentence, and leave the task directory unchanged apart from the lock file.
- No such call ends with exit 1 or a traceback, at the current revision or at a stale one; the result at a stale revision follows the normative order and is stated in the tests.
- A valid operation applied before the change is still recognised as already applied afterwards: the receipt entries the suite expects for valid inputs are unchanged.
- The 215 existing tests pass unchanged.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures; arguments passed as bytes).
- **Scenarios:**
  - Invalid UTF-8 in each text input of each write command → exit 6 with the content code, one JSON object, nothing written.
  - The same at a stale revision → the result the normative order gives, never exit 1.
  - Valid inputs → receipts and digests as before.
  - Existing suite → unchanged and passing.
- **Edge cases:** a lone surrogate escape passed by the operating system; invalid bytes in one of several notes; invalid bytes together with a reused operation id.
