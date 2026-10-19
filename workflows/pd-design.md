---
description: Discovery Step 3 — Generate 2-3 architectural variants, decide autonomously by default (--step-by-step to choose yourself), record decision
---

Invocation: `/pd-design <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 3.

Task directory = provided argument (trailing slash optional).

**Mode.** Without `--step-by-step` this workflow decides the architecture itself
via the **Autonomous Decision Protocol** (`workflow-reference`). With
`--step-by-step` it presents the variants and waits for the user's choice.
When invoked standalone, the default is still autonomous.

---

## Guard

1. Read `state.md` in the task directory. If it does not exist or `## Task Analysis` section is missing → **stop**: "Step 1 (Task Analysis) must be completed first. Run `/pd-analyze <path>`." Do not continue.
2. Verify that decomposition has been performed: `## Decomposition` section with `decomposition: complete` must be present in `state.md`, and at least one T-XX subdirectory must exist in the task directory. If either is missing → **stop**: "Step 2 (Decomposition) must be completed first. Run `/pd-decompose <path>`." Do not continue.
3. Check `## Phases → discovery`. If `complete` → **stop**: "Discovery phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
4. Otherwise → continue.

---

## Instructions

1. Read `state.md` in the task directory — use `## Task Analysis` and `### Codebase Analysis` as input.
2. Read `plan.md` — understand the subtask decomposition.
3. Generate 2–3 architectural approach variants for the task.
4. For each variant describe: approach summary, advantages, disadvantages, risks.
5. Select the winning variant:

   **Step-by-step mode** (`--step-by-step`): present all variants to the user.
   **Wait for their choice. Do not choose independently.**

   **Autonomous mode** (default): apply `workflow-reference → ## Autonomous
   Decision Protocol` — score all variants on the 5 lenses, apply the
   anti-overengineering filter, select the winner, check the escalation
   threshold. Escalate only on the Step 5 conditions; otherwise decide and
   continue without pausing.

6. Record the decision in `state.md`. In autonomous mode also write the
   `### Autonomous Decision` block (scoring table, winner, anti-overengineering
   check, evidence) inside `## Solution Design`, per the protocol's Step 6.

Derive `### Scope` from the chosen variant: In = what the chosen approach covers, Out = what was explicitly excluded or is out of bounds for this task. Be specific — vague scope produces no protection.

```
## Solution Design

### Variants
<all variants with pros/cons/risks>

### Decision
<chosen approach and rationale>

### Scope
#### In
<what this task covers — derived from the chosen approach>
#### Out
<what this task explicitly does NOT cover — adjacent concerns, future work,
related systems that will not be touched>

### Rejected
<rejected variants with reasons for rejection>

### Off-limits
<what must not be violated under any circumstances>

### Invariants
<system invariants that must hold throughout implementation>

### Acceptance Criteria
<measurable criteria for the entire task completion>
```

7. **Record the decision as a provisional ADR.** Apply the ADR trigger from
   `pv-finalize → ## Step 3` ("What to record as a decision") to the chosen
   variant. If it fires — the decision is architecturally significant rather
   than an implementation detail — run:

   ```
   /adr-new <task-directory> --provisional
   ```

   This writes the reasoning to `.ai/adr/` **now**, while it exists, instead of
   waiting for the task to validate. A task that later ends blocked, deferred, or
   interrupted therefore keeps its architecture record. `/pv-finalize` promotes
   the provisional ADR to `Accepted` at the end of the task rather than writing a
   second one — see `adr-new → ## Step 3`.

   If the trigger does not fire, write nothing and record why in one line under
   `### Decision`: `adr: not triggered — <reason>`. Do not write an ADR for a
   choice that constrains nothing.

   This step never stops the workflow: `/adr-new` failing or refusing is reported
   and Discovery continues.

8. Report: "Step 3 (Architectural Design) complete. Decision recorded."
   **Autonomous mode:** progress marker, not a handoff — the parent workflow
   proceeds to Step 4 immediately. Do not stop or ask to continue.
