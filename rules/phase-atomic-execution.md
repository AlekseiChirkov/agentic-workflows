---
trigger: model_decision
description: Context loading rules for atomic-execution — load when running /phase-atomic-execution, /pae-tests, or /pae-implement standalone (without parent /phase-execution)
---

# Phase: Atomic Execution — Context Rules

## Context Bootstrap

This phase runs inside a parent execution context OR standalone. Always load full context regardless.

**Step 0 — Resolve paths first:**
Read `T-XX/description.md → ## Context → working_dir:` before loading any context.
- If `working_dir:` present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`
- If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`
- Umbrella: if `<AI_DIR>/../.ai/` exists → load umbrella FIRST, then `AI_DIR` (local overrides)

Report before continuing: "WORK_DIR=<path>, AI_DIR=<path>"

**Then load in order** (skip missing files, report what was loaded):

| # | File | What to extract |
|---|------|-----------------|
| 1 | `AI_DIR/memory/architecture.md` | Component boundaries, integration points |
| 2 | `AI_DIR/memory/state.md` | Current task status, active blockers |
| 3 | `AI_DIR/principles/architecture.md` | Patterns to enforce |
| 4 | `AI_DIR/principles/coding.md` | **REQUIRED** — style, naming, error-handling, forbidden patterns |
| 5 | `AI_DIR/principles/domain.md` | Domain rules, terminology |
| 6 | `AI_DIR/adr/index.md` | Decisions that constrain this implementation |
| 7 | `AI_DIR/context/runbook.md` | **REQUIRED** — `test:` for the TDD RED step, test/lint/build for Final Verification |

Report: "Atomic execution context loaded from AI_DIR=<path>: [files read]"

After loading: state which scope constraints apply (from `description.md` + loaded principles).

## Phase Behaviors

- The cycle is test-first: `/pae-tests` (RED) → `/pae-implement` (GREEN) → `/pae-finalize`. See the `tdd` rule.
- `principles/coding.md` must be loaded before writing any code — tests included. If missing → note "No coding principles" in `notes:` and flag it.
- `context/runbook.md` must be available before the TDD step. A missing or placeholder `test:` command **stops** `/pae-tests` — it is not a "skip and note" case, because RED cannot be observed without it. A missing `lint:` before Final Verification is still a "note and continue" case.
- Read target files (from `T-XX/description.md → ## Scope → Target files`) AFTER context is loaded, not before.
- Out-of-scope discovery → stop immediately, report, wait for user decision.
- Update parent `## Subtask Progress` after every step.

## Blocker Reconciliation

Applies whenever a leaf's `atomic-execution: blocked` is encountered on entry (orchestrator Step 0, or a standalone `/pae-implement` that reads the block). Do **not** immediately ask the user "Is it resolved?". First classify the `blocker:` text:

**1. Dependency/status blocker** — the blocker cites only prerequisite subtasks (their approval, preconditions, or completion) and no other condition. Reconcile automatically:

- Determine the prerequisites: this T-XX's declared `Depends On` entries from parent `plan.md → ## Subtasks`, unioned with any `T-YY` explicitly named in the `blocker:` text.
- A prerequisite is **satisfied** when its `plan.md` status is `done` or `reviewed` (the same readiness rule `/pe-execute` uses). A composite prerequisite is satisfied when its block shows `rollup: done` **and** `integration-validation: complete`.
- If **every** prerequisite is satisfied → auto-reconcile without asking:
  - Set `blocker: none`.
  - Set `atomic-execution: in-progress` if `last_action` shows work already began, otherwise `not-started`.
  - Append to `last_action:` — `auto-reconciled blocker: prerequisites <list> satisfied`.
  - Add a `notes:` line recording the automatic reconciliation and the observed prerequisite statuses (e.g. `auto-reconciled 2026-07-17: T-01 reviewed, T-02 done — blocker cleared, no manual confirmation`).
  - Report the reconciliation to the user and **continue** — no confirmation required.
- If **any** prerequisite is NOT satisfied → keep `blocked`, report which prerequisite is outstanding and its current status, ask "Is it resolved? (yes/no)", and **wait**.

**2. Non-status blocker** — anything else: `step N failed`, `test failures`, `lint failures`, a missing external decision, an invariant conflict, or an implementation error. Never auto-reconcile. Report the blocker and ask "Is it resolved? (yes/no)". **Wait.**

**Ambiguity rule:** if the blocker cites a prerequisite **and** any non-status condition, treat it as non-status (manual confirmation). Any doubt → manual. An extra stop is always cheaper than resuming on an unmet blocker.
