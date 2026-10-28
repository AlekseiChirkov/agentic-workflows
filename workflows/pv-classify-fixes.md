---
description: Validation Step 4a — Classify approved fix-tasks into shared or dedicated branches using the quick-flow gate
---

Invocation: `/pv-classify-fixes <task-directory>`
Called by: `/pv-create-fixes` before it creates fix-task directories.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md`. If `## Issue List → ### Approved` is missing → **stop**: "Run `/pv-issues`
   first."
2. If `### Approved` is empty or `None` → report "No approved issues to classify." and return.
3. Reuse existing classification rows/IDs on resume; classify only newly approved issues.
   Append new groups rather than changing completed ones. Ask for explicit confirmation
   before replacing assigned IDs/groups. Load the `phase-validation` rule (`## Context Bootstrap`)
   before project writes on standalone invocation.

---

## Classification

For each approved issue, evaluate the four conditions in
`quick-flow → ## The escalation gate`: **3 or fewer files, counting test files**;
no new invariant; no shipped-pipeline behaviour change; no schema/migration change.
Record each pass/fail with evidence; unknown scope must be resolved before grouping.

All four pass → `shared`; any fail or severity `critical` → `dedicated`.
This reuses the gate per issue; it does not change the task's `flow:` tier.

### Naming — one vocabulary, shared with every downstream reader

Allocate non-colliding fix IDs from `plan.md` and composite membership; `/pv-create-fixes`
reuses them in `## Fix-Tasks → Created:`. The legacy `Branch` table column stores that
**fix-task ID**, not a git branch name; actual branch names follow `git-flow`.
`/pv-execute-fixes` uses the Created list, including sibling IDs:

- **Dedicated** — one fix-task per issue: `T-NN-fix-<slug>`, `<slug>` naming the defect.
- **Shared** — one fix-task per group, covering every issue in it: `T-NN-fix-<group-slug>`,
  `<group-slug>` naming in domain language what the group fixes. One branch and one pull
  request per group.
- **Child of a composite** (D8) — `T-NNx-fix-<slug>`, the sibling letter form defined in
  `/pv-create-fixes` step 2 Case B.

Each distinct ID is one group; `Grouping: shared` alone does not identify a group.
Keep top-level fixes separate from composite-child fixes, and never group children of
separate composites. Composite groups use the next available sibling letter.

### Splitting the shared group

The shared group is capped so it cannot quietly become the thing it was meant to prevent.
Split it into two or more groups when either limit is exceeded:

- more than **5** fixes in one group, or
- more than **10** files touched in total across the group.

A shared group must also stay within one independently testable component and one coherent
criteria set. Split unrelated components/clusters into separate leaves even below these caps.
Split along issue boundaries — never split a single fix across two branches. Each resulting
group gets its own `T-NN-fix-<group-slug>` name from the form above — the split is expressed as
two differently-named groups, never as a letter suffix on one name.

---

## Output

Write to `state.md` under `## Fix-Tasks`, as a classification table `/pv-create-fixes`
consumes. This step runs **before** `/pv-create-fixes` writes that section, so create
`## Fix-Tasks` if it does not exist yet and write only the `### Fix Classification`
subsection into it — `/pv-create-fixes` fills in `fixes-created`, `fixes-count`, and
`Created:` immediately afterwards and must not overwrite this subsection:

```
### Fix Classification

| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|-------|----------|--------|--------|--------|--------|----------|--------|
| #3 <title> | important | pass | pass | pass | pass | shared | T-09-fix-<group-slug> |
| #7 <title> | critical  | pass | pass | fail | pass | dedicated | T-10-fix-<slug> |
```

Every row records all four gate results, so a `dedicated` decision can be audited later —
the same discipline `quick-flow` applies to its own tier decision.

Report: "Fix classification complete. <N> shared across <M> groups, <K> dedicated."
Return to the caller; this is a progress marker.
