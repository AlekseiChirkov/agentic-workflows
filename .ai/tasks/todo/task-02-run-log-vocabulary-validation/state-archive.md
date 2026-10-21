# state-archive — task-02-run-log-vocabulary-validation

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Make run-log writes conform to one exact, documented field contract, add read-only validation for stored records, and make retrospective metrics exclude invalid records without changing historical logs or blocking a workflow.

### Affected Parts
- `scripts/log-step.sh` — validate and normalize producer arguments before state changes; preserve non-blocking writes; add a read-only linter using the same runtime vocabulary.
- `workflows/retro.md` — lint the filtered run corpus, disclose incomplete telemetry, and exclude invalid lines from metric calculations.
- `rules/run-log.md` — document field presence, types, enumerations, normalization, validation behavior, and lint output.
- `scripts/validate-contracts.sh` — compare the helper's effective enumerations and mappings with structured documentation tables and fail on drift.
- `tests/log-step.sh` — add an isolated executable smoke harness for producer, linter, reporting, contract-drift, and historical-file guarantees.

### Codebase Analysis
Files read: 4/12 (4 entry-points, 0 deeper).
- `scripts/log-step.sh` — read as the producer entry point. It currently accepts unknown arguments, does not validate field vocabularies, updates sequence metadata before append, has no step-name check or linter, and removes active metadata after attempting a close append without verifying persistence.
- `workflows/retro.md` — read as the sole consumer entry point. It aggregates the filtered corpus directly and currently has no lint step, invalid-line exclusions, or partial-telemetry reporting.
- `rules/run-log.md` — read as the current contract. It permits arbitrary short gate verdicts and does not specify the required closed enums, count bounds, normalization table, or lint contract.
- `scripts/validate-contracts.sh` — read as the contract-gate entry point. It already uses structured checks and retains nonzero failure status; it has no run-log vocabulary drift check.

The project state records ten existing runs and warns that several contain values outside the current vocabulary. The source contract also requires historical logs to remain unchanged. No `tests/` directory exists, so the acceptance harness will be new. The relevant accepted telemetry decisions align with the spec; the spec supplies the binding field-level details for this task.

### Open Questions
None. The spec defines the vocabulary, validation and write semantics, lint diagnostics, retrospective treatment, documentation checks, and smoke-test coverage.

## Archived Solution Design — Variants

**Variant 1 — Keep the structured runtime contract in the helper.** Define field names, enums, integer fields, bounds, and legacy mappings once in `scripts/log-step.sh`. Producer validation and lint consume those definitions; the contract validator reads the helper's structured contract export and compares it with the documented tables.

Advantages: One effective runtime source for both writes and lint; no new runtime dependency or module; the existing contract gate can compare the definitions it actually uses. Disadvantages: The helper needs a stable structured export for contract checks. Risks: If the export does not represent effective runtime values, contract checks could give false confidence.

**Variant 2 — Add a shared shell contract module.** Move structured definitions into a new shell file sourced by the helper and contract validator, with lint using the same functions.

Advantages: Clear separation between contract data and command behavior; one reusable source. Disadvantages: Adds a runtime file and source-path handling. Risks: A missing or incompatible module could break the helper in otherwise valid installations.

**Variant 3 — Parse the documentation tables at runtime.** Make the tables in the run-log rule the source consumed by writes and lint, then validate the parsed tables.

Advantages: Documentation and runtime behavior share the same textual source. Disadvantages: Couples runtime execution to Markdown parsing and document layout. Risks: A formatting edit could break logging, and the validator would have less independent evidence of agreement.

## Archived Solution Design — Rejected

- Variant 2 was rejected because the task needs no separate runtime module, and introducing one increases file and path coupling.
- Variant 3 was rejected because Markdown parsing would make runtime logging depend on document formatting.
- Event-by-event and document-operation subtasks were rejected because they fragment shared contracts and create extra boundaries around one helper and one canonical table set.
