---
trigger: model_decision
description: Context loading rules for validation phase — load when running /phase-validation, /pv-contract, /pv-review, /pv-issues
---

# Phase: Validation — Context Rules

## Context Bootstrap

Run before reviewing any implementation file. Skip missing files without error.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.
Report at end: "Validation context loaded: [files read]"

| # | File | What to extract |
|---|------|-----------------|
| 1 | `.ai/memory/architecture.md` | System-level invariants, integration contracts |
| 2 | `.ai/memory/state.md` | What was executed, task progress |
| 3 | `.ai/principles/architecture.md` | Patterns the implementation must conform to |
| 4 | `.ai/principles/coding.md` | Code standards — deviations are findings |
| 5 | `.ai/principles/domain.md` | Domain correctness rules |
| 6 | `.ai/adr/index.md` | Past decisions — violations are critical findings |
| 7 | `.ai/context/runbook.md` | Commands to run tests/lint during validation |

After loading: state the validation criteria derived from principles and ADRs before reviewing code.

## Phase Behaviors

- ADR violations → always `critical` severity.
- Architectural principle violations → `critical` severity.
- Coding principle violations → `important` severity.
- Domain rule violations → `critical` severity.
- Run `runbook.md → test:` and `lint:` commands before issuing any verdict.
- Read implementation files (from `target_files:`) AFTER context is fully loaded.
