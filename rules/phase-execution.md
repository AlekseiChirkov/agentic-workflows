---
trigger: model_decision
description: Context loading rules for execution phase — load when running /phase-execution, /pe-execute, /pae-implement, /pae-finalize
---

# Phase: Execution — Context Rules

## Context Bootstrap

Run before modifying any project file. Skip missing files without error.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.
Report at end: "Execution context loaded: [files read]"

| # | File | What to extract |
|---|------|-----------------|
| 1 | `.ai/memory/architecture.md` | Component boundaries, integration points, service contracts |
| 2 | `.ai/memory/state.md` | Current task status, active blockers |
| 3 | `.ai/principles/architecture.md` | Patterns to enforce, boundaries not to cross |
| 4 | `.ai/principles/coding.md` | **REQUIRED** — code style, naming, error-handling, forbidden patterns |
| 5 | `.ai/principles/domain.md` | Domain rules, terminology, business constraints |
| 6 | `.ai/adr/index.md` | Past decisions that constrain current implementation |
| 7 | `.ai/context/runbook.md` | test/lint/build commands — required for Final Verification step |

After loading: state which principles and constraints apply to the current subtask before writing code.

## Phase Behaviors

- `principles/coding.md` must be loaded before writing any code. If missing → note in `notes:` and proceed cautiously.
- `context/runbook.md` is required for Final Verification in `pae-implement`. If missing → write "No runbook — test/lint skipped" to `notes:`.
- Scope adherence: never implement beyond `T-XX/description.md → ## Scope → In scope`.
- Update parent `## Subtask Progress` after EVERY completed step — not only at the end.
- Out-of-scope discovery during a step → stop, report, wait for user decision.
