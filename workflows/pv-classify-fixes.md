---
description: Validation Step 4a — Classify approved fix-tasks into shared or dedicated branches using the quick-flow gate
---

Invocation: `/pv-classify-fixes <task-directory>`
Called by: `/pv-create-fixes` before it creates fix-task directories.

Task directory = provided argument (trailing slash optional).

---

## Purpose

A validation pass can produce anything from one typo fix to a structural rework. Giving every
fix its own branch and pull request buries the reviewer; putting them all in one buries the
review. This step decides the split with a checkable rule instead of a judgement call.

The rule reuses the project's existing definition of "small change" — the `quick-flow` gate —
rather than inventing a second one.

---

## Guard

1. Read `state.md`. If `## Issue List → ### Approved` is missing → **stop**: "Run `/pv-issues`
   first."
2. If `### Approved` is empty → report "No approved issues to classify." and **stop**.

---

## Classification

For each approved issue, evaluate the four `quick-flow` gate conditions against the fix it
would require:

1. **Small surface** — the fix touches **3 or fewer files, counting test files**.
2. **No new invariant** — it introduces nothing that would become a new line under
   `### Invariants`, `domain.md`, or `principles/*`.
3. **No behaviour change to an already-shipped pipeline** — using the definition in
   `quick-flow`, applied to code that shipped before this task.
4. **No schema change** — no DB schema change and no migration.

- **All four hold → `shared`.** The fix joins the common fix branch.
- **Any one fails → `dedicated`.** The fix gets its own branch and its own pull request.

A `critical` severity issue is `dedicated` regardless of the gate: a critical finding deserves
review in isolation, not folded into a batch.

### Naming — one vocabulary, shared with every downstream reader

Fix-tasks have exactly one naming form, the one `/pv-create-fixes` writes into
`## Fix-Tasks → Created:` and `/pv-execute-fixes` discovers by the glob `T-XX-fix-*`
(`workflow-globals → ## Fix-Tasks format`):

- **Dedicated** — one fix-task per issue: `T-NN-fix-<slug>`, `<slug>` naming the defect.
- **Shared** — one fix-task per group, covering every issue in it: `T-NN-fix-<group-slug>`,
  `<group-slug>` naming in domain language what the group fixes. One branch and one pull
  request per group.
- **Child of a composite** (D8) — `T-NNx-fix-<slug>`, the sibling letter form defined in
  `/pv-create-fixes` step 2 Case B.

Never emit a group name that is not itself a valid fix-task ID — a `fixes` / letter-suffix form
matches no downstream reader, so a group named that way is created and then never executed.

### Splitting the shared group

The shared group is capped so it cannot quietly become the thing it was meant to prevent.
Split it into two or more groups when either limit is exceeded:

- more than **5** fixes in one group, or
- more than **10** files touched in total across the group.

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

Report: "Fix classification complete. <N> shared across <M> branch(es), <K> dedicated."
