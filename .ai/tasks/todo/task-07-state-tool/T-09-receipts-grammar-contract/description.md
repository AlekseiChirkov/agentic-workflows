## Goal
The canonical state contract defines the tool-managed `state_receipts:` field on one
anchored line, lists it as protected, and both validators check it, including equality
between the tool's vocabulary constants and the anchored vocabulary lines.

## Context
- Dependencies: T-01 (the vocabulary constants in the tool), T-07 (final receipt
  behaviour the definition describes).
- Constraints: a contract change starts with a failing check in
  `scripts/validate-contracts.sh`, then the canonical definition, then every reader.
  Contract: task spec REQ-20 and `### Contract-file changes`. The change is additive:
  blocks without the field stay valid. Every validator check uses the
  `check "<desc>" "$(… && echo pass || echo '<reason>')"` form and is anchored to a
  definition line. Rule file names are the current ones (`rules/workflow-globals.md`,
  `rules/workflow-reference.md`). English only; no planning identifiers in product content.
- Pinned fixtures: `scripts/validate-contracts.sh` is pinned by the validator inventory
  oracle and the source-guard manifest; new checks need an inventory amendment and a
  refreshed fingerprint. Follow `tests/fixtures/validator-runtime/README.md`.
- Reason: the grammar extension is a contract change with its own readers and checks,
  independent of the tool's code paths.

Off-limits: no rename or removal of an existing field, vocabulary or section; no change
to any workflow under `workflows/`; no removal of the grammar duplication between the two
rule files; deployed copies under the home directory are never edited.

## Scope
- **In scope:** the anchored definition line and reader rule in
  `rules/workflow-globals.md`; the protected entry in
  `rules/workflow-reference.md → ## Protected Sections Contract`; the receipts check in
  `scripts/validate-task.sh` and the `pinned` omission in its vocabulary message; the
  three checks in `scripts/validate-contracts.sh`; mutation fixtures proving each check
  fails.
- **Out of scope:** wiring the tool into `scripts/validate-task.sh`; changing
  `/compress-state`'s workflow text.
- **Target files:** `rules/workflow-globals.md`, `rules/workflow-reference.md`,
  `scripts/validate-task.sh`, `scripts/validate-contracts.sh`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`,
  `tests/fixtures/validator-runtime/inventory-amendment.json`

## Steps
1. Add failing checks to `scripts/validate-contracts.sh`: the anchored `state_receipts:`
   line exists in `rules/workflow-globals.md`; the protected list names it; each of the
   four tool constants equals its anchored vocabulary line, in order.
2. Add failing suite cases: mutation copies of the source tree where a constant differs,
   the anchored line is absent, or the protected entry is absent make the validator
   check fail; task fixtures with 21 entries, a malformed entry or a repeated operation id
   make `scripts/validate-task.sh` fail and a well-formed one pass.
3. Add to `rules/workflow-globals.md` the anchored line
   `Tool-managed field state_receipts: <operation_id>#<16-hex digest>, … — at most 20 entries, oldest first; written only by scripts/state-tool.py; never edited or removed by hand or by /compress-state.`
   and the reader rule that blocks without the field are valid.
4. Add `state_receipts:` lines to the protected fields of
   `rules/workflow-reference.md → ## Protected Sections Contract`.
5. Add the receipts check to `scripts/validate-task.sh` (every `state_receipts:` line has
   1–20 well-formed entries and unique operation ids) and include `pinned` in the
   `atomic-tests` vocabulary message.
6. Record the new validator checks in the inventory amendment, refresh the pinned
   source-guard fingerprint, and run the guard suites, the inventory oracle and the
   focused state-tool mode.

## Acceptance Criteria
- `rules/workflow-globals.md` contains the anchored line exactly once and states that
  blocks without the field are valid.
- `rules/workflow-reference.md → ## Protected Sections Contract` lists `state_receipts:`.
- The three new checks in `scripts/validate-contracts.sh` pass on the source tree, and
  each fails on its mutation fixture: a tool vocabulary constant that differs from
  `rules/workflow-globals.md`, the anchored line absent, the protected entry absent.
- `scripts/validate-task.sh` exits 1 on a task fixture whose `state_receipts:` line has
  21 entries, a malformed entry, or a repeated operation id, and exits 0 on a well-formed
  one and on a task without the field.
- The `atomic-tests` vocabulary message of `scripts/validate-task.sh` names all six values.
- `scripts/validate-task.sh` still exits 0 on every directory under
  `.ai/tasks/completed/`; the source-guard suites and the inventory oracle pass.

## Test Plan
- **Level:** smoke (validator checks, RED before the rule edits) and integration
  (mutation fixtures run through the validators).
- **Scenarios:**
  - Source tree → the three validator checks pass.
  - Mutated constant, missing anchored line, missing protected entry → the matching check
    fails.
  - Task fixtures with bad and good receipts lines → exit 1 / exit 0.
  - Vocabulary message → six values.
  - Completed task directories → still exit 0.
- **Edge cases:** a constant with the right values in the wrong order; a
  `state_receipts:` line with exactly 20 entries; a task with no progress section.
