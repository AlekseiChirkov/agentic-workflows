# state-archive — task-04-model-catalog-cache

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Implement an optional, deterministic local model catalog and conservative selector with explicit refresh, compatible plan columns, and honest model resolution. Preserve the current execution model when usable evidence is absent.

### Affected Parts
Catalog and selection helpers, selector workflow, plan readers, canonical optional columns, focused offline validation, and operating documentation.

### Codebase Analysis
Discovery context loaded: .ai/memory/architecture.md, .ai/memory/state.md, .ai/principles/architecture.md, .ai/principles/coding.md, .ai/principles/domain.md, .ai/adr/index.md, .ai/context/runbook.md, .ai/context/integrations.md, .ai/context/environment.md. Architecture describes the existing helpers and deployment: do not reread their implementations during Discovery.

Files read: 6/12 (6 entry-points, 0 deeper): workflows/pd-select-model.md because detailed selection formulas are absent from architecture; harness/codex/capabilities.md and harness/claude/capabilities.md because model-request evidence must be distinguished from logging capabilities; templates/subtask-description.md because concrete leaf shape matters; targeted scripts/validate-contracts.sh and scripts/validate-task.sh entry sections because focused-mode and artifact-check interfaces are not documented in architecture. Workflow definitions and rules loaded for process are not product exploration.

The selector currently builds a live, nonpersistent catalog and writes a legacy Model column. Harness files declare logging support, not model request support. The current session exposes sub-agent and messaging tools, but no resolved execution identity telemetry. The repository tracks knowledge; this invoked skill prohibits committing knowledge, so all run state remains local during this run. No deployment or paid comparison is authorized by this task.

### Open Questions
None blocking.


## Archived Solution Design — Variants
1. Markdown instructions alone: smallest surface, but schema validation, atomic replacement and exhaustive numerical boundaries cannot be established reproducibly.
2. Optional standard-library local helpers plus a compact workflow: explicit inputs, no network/provider dependencies, deterministic fixtures and conservative fallback; adds a small schema and command interface.
3. Full routing service or harness migration: broad integration and deployment work, new runtime and speculative calibration beyond the authorized scope.


## Archived Solution Design — Rejected
Reject instructions-only validation because it cannot prove exact boundaries or atomic writes. Reject a routing service because it adds a mandatory runtime and crosses ownership/scope boundaries.
