---
description: Discovery Step 3 — Generate 2-3 architectural variants, decide autonomously by default (--step-by-step to choose yourself), record decision
---

Invocation: `/pd-design <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 3.

Resolve artifacts inside the task directory. Default is autonomous;
`--step-by-step` waits for architecture choice. Reuse parent context; standalone
use applies the `phase-discovery` bootstrap.

## Guard

1. Missing task `state.md` / `## Task Analysis` → **stop**: run `/pd-analyze`.
2. `flow: quick` → report that design is skipped; retain `## Contract (quick)`.
3. Require `## Decomposition` / `decomposition: complete`, `plan.md`, and every
   listed subtask description. Missing input → **stop**: complete `/pd-decompose`.
4. `discovery: complete` or an existing `## Solution Design → ### Decision` →
   **stop** for explicit overwrite confirmation unless already confirmed by the
   parent for this exact rerun. Preserve execution/validation progress.

## Instructions

1. Read Task Analysis, `plan.md`, relevant descriptions and binding principles/ADRs.
   Generate 2–3 viable approaches with summary, advantages, disadvantages and risks.
2. Select the winner:
   - Step-by-step: present the variants and **wait** for the user's choice.
   - Autonomous: apply `workflow-reference → ## Autonomous Decision Protocol`:
     score all five lenses, apply its anti-overengineering filter and tie-breaks,
     and escalate only at its threshold. Under `/spec-run`, leave unresolved
     Class B intent for the parent's batch gate rather than inventing an answer.
3. Upsert `## Solution Design` in task `state.md`:

   ```
   ## Solution Design

   ### Variants
   <approaches with advantages, disadvantages and risks>

   ### Decision
   <winner and evidence-based rationale>

   ### Scope
   #### In
   <included outcomes>
   #### Out
   <specific adjacent concerns and exclusions>

   ### Rejected
   <alternatives and reasons>

   ### Off-limits
   <specific boundaries that must not be crossed>

   ### Invariants
   <conditions maintained throughout implementation>

   ### Acceptance Criteria
   <binary observable task-level criteria>
   ```

   Autonomous mode also writes `### Autonomous Decision` inside Solution Design
   using the canonical score table, winner, anti-overengineering check and evidence.
4. Reconcile the chosen Scope, constraints and criteria into affected unstarted
   descriptions and `plan.md` summaries/dependencies. Preserve the six-section
   format, leaf-health constraints, statuses and progress. Record material changes
   in Decomposition Decisions. If the design requires a different decomposition,
   run `/pd-decompose` with this decision as input and its overwrite Guard; then
   recheck alignment. Preserve optional/legacy columns under
   `workflow-reference → ### Model columns and resolution`. A scope change in a
   subtask with any populated provider model cell/column or legacy `Model` cell
   makes its recommendation stale and needs a fresh bulk `/pd-select-model`
   before model-specific execution; report the stale recommendation without
   assigning or silently changing models here. Started
   work that conflicts with the decision is a reconciliation blocker, not permission
   to rewrite progress.
5. Apply `pv-finalize → ## Instructions`'s architecture-decision trigger. If it fires,
   invoke `/adr-new <task-directory> --provisional`; final validation promotes the
   record rather than duplicating it. Otherwise record under `### Decision`:
   `adr: not triggered — <reason>`. Report ADR creation failure and continue;
   preserve the design reasoning in state.
6. Report: `Step 3 (Architectural Design) complete. Decision recorded.` Mention
   reconciliation changes or outstanding batch questions. Under an autonomous
   parent this is a progress marker, not a handoff; standalone use ends here.
