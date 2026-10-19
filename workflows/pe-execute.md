---
description: Execution Step 1 — Execute all pending subtasks via atomic execution → validation cycles
---

Invocation: `/pe-execute <task-directory>`
Called by: `/phase-execution` as Step 1.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory. If `state.md` is not found → **stop**: "state.md not found. Run `/phase-discovery` first."
2. Check `## Phases → discovery`. If not `complete` → **stop**: "Discovery not complete. Run `/phase-discovery` first."
3. Check `## Phases → execution`. If `complete` → **stop**: "Execution phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
4. Otherwise → continue.

---

## Instructions

Read `plan.md` in the task directory. Detect the plan format:
- If `Type` column is absent → flat-only task; use simple sequential iteration (same as before).
- If `Type` column is present → task uses composites or slicing; use DAG-aware iteration below.

**Topological DAG iteration (used when `Type` column is present or when `## Execution Strategy` specifies ordering beyond simple sequence):**

Build a dependency graph from `## Subtasks → Depends On`. Resolve execution order:
1. Respect topological dependency order (a row is ready only when all its `Depends On` entries are `done` or `reviewed`).
2. Within the topological order, also honor the ordering policy from `## Execution Strategy` (e.g. "by capability slice; producer before consumer").
3. Process rows in the resulting order.

For each row in execution order:

1. **Composite rows (`Type: composite`):**
   - Do NOT call atomic-execution on the composite itself.
   - Verify all child rows (listed in `children:` of the composite block in `state.md → ## Subtask Progress`) are present in `plan.md`. If any child row is missing → **stop**: "Composite T-XX children mismatch. Re-run `/pd-decompose` to regenerate."
   - Skip the composite row and continue iterating — children will appear later in topological order.
   - After all children reach `reviewed`, do **not** call `/phase-composite-validation` from
     here — `/pav-close` step 5 owns that trigger and fires it when the last child closes (see
     step 2e). A second invocation hits `phase-composite-validation` Step 0.3
     ("Integration validation already complete. Re-running will overwrite. Confirm? (yes/no)"),
     which stops an unattended `/phase-pipeline` or `/spec-run` run.
   - **Verify the outcome instead.** Read `integration-validation:` in the composite block of
     `state.md → ## Subtask Progress`:
     - `complete` → the composite is `reviewed`; record `composite-reviewed`.
     - `failed` → the integration fix cycle is open; record `composite-blocked` and continue.
     - still `not-started` → the trigger never fired. Record the composite as
       `composite-stalled` in the `## Execution Report` and continue with the remaining rows;
       `/pe-finalize` step 2b reconciles it and tells the user to run
       `/phase-composite-validation` manually.

2. **Leaf rows (`Type: leaf` or no `Type` column — backward compat):**
   a. **Check status**: if `done` / `reviewed` → skip. If `blocked` / `deferred` → skip, record in report.
   b. **Check dependencies**: if any dependency is not `done` or `reviewed` → skip, record: "Skipped T-XX: dependency T-YY not complete."
   c. Verify `T-XX/description.md` contains `## Steps` and `## Acceptance Criteria`. If missing → **stop**: "T-XX/description.md is incomplete. Run `/pd-decompose` + `/pd-finalize` to regenerate."
   d. **Run atomic cycle**:
      - Call `/phase-atomic-execution <path-to-T-XX/description.md>`
      - Call `/phase-atomic-validation <path-to-T-XX/description.md> --batch`
   e. After validation completes, `pav-close` automatically triggers composite rollup and composite validation if this is the last reviewed child (handled inside `pav-close`). No additional action needed here.

3. **Blocked composite (D7):** If a composite's `rollup:` is `blocked`, do NOT attempt its composite validation. Record the composite as `blocked` in the Execution Report. Whether sibling children of the blocked child also halt is determined by whether their `Depends On` chain passes through the blocked child. The existing dependency check (step 2b) enforces this automatically.

Before calling atomic-execution for any leaf, verify `T-XX/description.md` contains `## Steps` and `## Acceptance Criteria`. If missing → **stop** and report: "T-XX/description.md is incomplete. Run `/pd-decompose` + `/pd-finalize` to regenerate."

At any blocker or ambiguous situation in any atomic workflow:
- Stop immediately.
- Describe the problem clearly and concretely.
- Propose 2–3 solution options with trade-offs.
- Wait for user's choice.
- Continue only after receiving an answer.

After each completed leaf subtask (status `reviewed`), run `/compress-state --auto` on the parent task's `state.md` (T-XX directories have no `state.md`).

## Execution Report persistence

After processing each subtask (including skipped, blocked, deferred), append its outcome to the `## Execution Report` section in the task-level `state.md`. Create the section if it does not exist. Format — one line per subtask:

```
## Execution Report
- T-01: done — <one-line summary>
- T-02: reviewed — <one-line summary>
- T-03: blocked — <reason>
- T-04: deferred — deferred by user decision
- T-05: not-reached — execution finished before this subtask
- T-06: composite-reviewed — all children reviewed, integration validation passed
- T-06a: reviewed — <one-line summary>
- T-06b: reviewed — <one-line summary>
```

For composites: record one line for the composite itself (`composite-reviewed` / `composite-blocked` / `composite-stalled` / `not-reached`) AND one line per child. This gives a complete audit trail.

If a T-XX entry for the current subtask already exists in the section (for example on re-run) — overwrite the line in place. Do not keep duplicates.

This file-based record is the source of truth for `/pe-finalize`. Do not rely on session memory.
