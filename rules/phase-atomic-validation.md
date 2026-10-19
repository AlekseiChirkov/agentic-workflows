---
trigger: model_decision
description: Context loading rules for atomic-validation — load when running /phase-atomic-validation or /pav-check standalone (without parent /phase-validation)
---

# Phase: Atomic Validation — Context Rules

## Context Bootstrap

This phase runs inside a parent validation context OR standalone. Always load full context regardless.

**Step 0 — Resolve paths first:**
Read `T-XX/description.md → ## Context → working_dir:` before loading any context.
- If `working_dir:` present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`
- If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`
- Umbrella: if `<AI_DIR>/../.ai/` exists → load umbrella FIRST, then `AI_DIR` (local overrides)

Report before continuing: "WORK_DIR=<path>, AI_DIR=<path>"

**Then load in order** (skip missing files, report what was loaded):

| # | File | What to extract |
|---|------|-----------------|
| 1 | `AI_DIR/memory/architecture.md` | System invariants, integration contracts |
| 2 | `AI_DIR/memory/state.md` | What was executed, last known state |
| 3 | `AI_DIR/principles/architecture.md` | Patterns the implementation must conform to |
| 4 | `AI_DIR/principles/coding.md` | Code standards — deviations = findings |
| 5 | `AI_DIR/principles/domain.md` | Domain correctness rules |
| 6 | `AI_DIR/adr/index.md` | Past decisions — violations = critical findings |
| 7 | `AI_DIR/context/runbook.md` | Commands to run for verification |

Report: "Atomic validation context loaded from AI_DIR=<path>: [files read]"

After loading: state the validation criteria derived from principles and ADRs before reading any implementation files.

## Phase Behaviors

- Read `target_files` from parent `state.md → ## Subtask Progress → T-XX → target_files:` AFTER context is loaded.
- ADR violations → always `critical` severity.
- Architectural principle violations → `critical` severity.
- Coding principle violations → `important` severity.
- Domain rule violations → `critical` severity.
- Run `runbook.md → test:` and `lint:` if available before issuing verdict.
