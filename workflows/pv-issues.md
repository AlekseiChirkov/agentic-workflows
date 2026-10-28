---
description: Validation Step 3 — Compile numbered issue list with priorities, present to user, wait for decision
---

Invocation: `/pv-issues <task-directory>`
Called by: `/phase-validation` as Step 3.

Task directory = provided argument (trailing slash optional).

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → validation`. If `complete` → **stop**: "Validation phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Code Review` present in `state.md`. If missing → **stop**: "Step 2 (/pv-review) must be completed first. Run /pv-review <path>."
4. Otherwise → continue.

---

## Instructions

Load the `phase-validation` rule (`## Context Bootstrap`) before writes when standalone.
Code-review severity maps directly to issue priority: `critical`, `important`, `optional`.

1. Read `state.md` — extract `## Contract Check` and `## Code Review`.
2. Deduplicate the contract/review findings into one stable numbered list; preserve issue
   numbers and decisions on resume. Invariant/Off-limits failures are `critical`;
   unmet Acceptance Criteria are at least `important`. For each item:

```
[N]. <Task name>
     Problem: <what is wrong or can be improved>
     Solution: <what specifically to do>
     Priority: critical | important | optional
```

3. Present the full list to the user.
4. **Wait for user's response**: which tasks to fix now, which to defer.
   Under `/phase-pipeline` or `/spec-run`, use their declared override: approve critical /
   important, defer optional, and record that the split was automatic. An empty issue list
   needs no decision: write `None` to both subsections and continue.
5. Upsert in `state.md`, preserving prior resolved decisions:

```
## Issue List

### Approved
<list of approved issue numbers with descriptions>

### Deferred
<list of deferred issue numbers with reasons>
```

6. Report: "Step 3 (Issue List) complete. N approved for fix, M deferred."
Return to the caller; this is a progress marker.
