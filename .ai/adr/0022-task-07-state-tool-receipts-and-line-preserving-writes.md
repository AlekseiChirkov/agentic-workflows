# ADR-0022: Decisions for Task 07 — State tool receipts, invariant checks and line-preserving writes

## Status

Provisional

## Date

2026-11-13

## Related Task

- Task: `.ai/tasks/todo/task-07-state-tool/` (spec `.ai/specs/07-state-tool.md`)
- Related pull request: not yet created
- Related files: `scripts/state-tool.py`, `tests/state-tool.py`,
  `rules/workflow-globals.md`, `rules/workflow-reference.md`, `scripts/validate-task.sh`,
  `scripts/validate-contracts.sh`

## Summary

ADR-0021 scheduled the state tool and fixed its lock, location and ignore rules. This
record covers the remaining design decisions that shape the canonical state format and
the tool's internals: operation receipts stored in an additive in-block field,
invariant-only lifecycle checks, a line-preserving write model, and the placement of the
acceptance suite under the pinned test inventory.

## Context

The tool edits one block of `## Subtask Progress` in a task `state.md`. Real blocks carry
quoted note values, blank lines inside continuation runs, unknown fields and foreign
lines, all of which must survive a write byte for byte. Idempotent retries need durable
evidence that an operation was applied. Status transitions are defined by the execution
and validation workflows, not by one table. Every file under `tests/` and the contract
validator are bound by a pinned source-guard inventory fingerprint
(`tests/fixtures/validator-runtime/README.md`).

## Decisions

### Decision 1: Operation receipts live in an additive in-block field

**What was decided:** Each applied write records `<operation_id>#<16-hex input digest>` as
the last entry of a tool-managed `state_receipts:` field line of the target block, capped
at the 20 newest entries. The field is defined on one anchored line of
`rules/workflow-globals.md`, listed as protected, and checked by both validators. Blocks
without the field stay valid; readers that do not know it treat it as an unknown field.

**Why:** The receipt is written in the same atomic replace as the block change, so a
retry after an interruption can tell applied from not applied without a second file.

**Alternatives:** A sidecar receipt journal — rejected: two files need crash
reconciliation. No receipts — rejected: identical intended notes would collapse or
duplicate on retry. Storing the resulting revision — rejected: a file cannot contain its
own hash.

**Consequences:** The canonical block grammar gains one protected field (additive under
P3). A retry after 20 later writes on the same block is treated as a new operation.

**Related files:**
- `rules/workflow-globals.md`, `rules/workflow-reference.md`
- `scripts/validate-task.sh`, `scripts/validate-contracts.sh`

### Decision 2: Lifecycle checks are canonical invariants, not a transition table

**What was decided:** Writes enforce only invariants taken from canonical sources:
vocabulary membership, no downgrade of `atomic-tests` by rank, `pinned` only to `green`,
`green` only from `red` or `pinned`, justified `n-a`, completion preconditions and the
pre-TDD guard. Moves inside one rank, atomic-validation and composite statuses are
checked by vocabulary only. Invariants apply to the fields an operation changes;
pre-existing violations elsewhere become warnings.

**Why:** One source of truth: the workflows define transitions, and the tool must never
certify test results or refuse an unrelated write on legacy data.

**Alternatives:** A full transition table — rejected: a contract change every workflow
must follow, and it could reject legitimate recovery paths. Vocabulary-only checks —
rejected: `pinned → red` and an unjustified `n-a` would pass.

**Consequences:** Some illegitimate moves remain possible (accepted gaps). The tool's
vocabulary constants are pinned to the anchored lines by a drift check.

**Related files:**
- `scripts/state-tool.py`

### Decision 3: Writes use a line-preserving document model

**What was decided:** The tool keeps `state.md` as its original list of lines, classifies
each line, and applies a write as whole-line replacements and insertions by index. The
candidate is re-parsed before the replace to confirm that bytes outside the changed lines
are identical.

**Why:** Byte preservation of untouched text holds by construction instead of depending
on a faithful re-serializer for quoting, blank continuation lines and unknown fields.

**Alternatives:** Parsing the block into an object and re-serializing it — rejected: risk
of silent normalization in legacy blocks.

**Consequences:** Edit operations work on line indexes; a missing known field is inserted
at its canonical position without moving existing lines.

**Related files:**
- `scripts/state-tool.py`

### Decision 4: The acceptance suite lives under `tests/` and each change refreshes the pinned fixtures

**What was decided:** The suite is `tests/state-tool.py` (`unittest`), with a focused
`--state-tool-only` validator mode and a registration in the default validator run. Every
subtask that changes a file under `tests/` or the validator refreshes the pinned
validator-runtime fixtures by the recorded maintenance procedure.

**Why:** The tool is under the repository test command from its first branch, in the same
form as the existing Python helper suites, and every stack tip stays fully valid.

**Alternatives:** A shell suite — rejected: it cannot run the in-process directory-sync
case or the static scan without embedded Python. A standalone suite outside the pinned
inventory with one final refresh — rejected: the tool would sit outside the test command
for most of the stack and break the suite-registration pattern.

**Consequences:** Each subtask pays a fixture refresh; validator edits are confined to the
suite registration and the grammar-extension checks.

**Related files:**
- `tests/state-tool.py`, `scripts/validate-contracts.sh`
- `tests/fixtures/validator-runtime/`

## Verification

Not yet verified — decision recorded before implementation completed.
