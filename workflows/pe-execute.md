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

## Context Bootstrap

Load the `phase-execution` rule (`## Context Bootstrap`) before code reads or writes. When invoked
standalone, perform the full bootstrap, set `execution: in-progress`, and resume recorded work.
`flow: quick` → **stop**: "Quick tasks execute inline in `/phase-execution`; there are no atomic subtasks."

## Instructions

1. Read `plan.md → ## Subtasks`, its `Depends On` column, `## Execution Strategy`,
   and parent `state.md → ## Subtask Progress`. Missing `Type` means leaf.
   Execute strictly sequentially in topological dependency order; break ties using the
   execution strategy, then table order. A dependency is ready when a leaf is `done` or
   `reviewed`; a composite also requires `integration-validation: complete`.
   A dependency cycle or unknown dependency → **stop**: "Invalid dependency graph: <rows>. Repair the plan before executing."

2. For each ready leaf:
   - `reviewed` → record and skip. `blocked` / `deferred` → record the reason and skip;
     do not run dependent rows while their prerequisites remain unmet.
   - Require its description's `## Steps` and `## Acceptance Criteria`; if absent →
     **stop**: "Incomplete subtask description. Run `/pd-decompose` + `/pd-finalize`."
   - Before requesting a model or executing the atomic cycle, apply
     `workflow-reference → ### Model columns and resolution`. Read the active optional
     `Model (Claude)` / `Model (Codex)` column, legacy `Model`, or session default by
     that precedence. Resolve the configured or already-verified source root through
     the canonical read-only guidance preflight; use the same source root for the helper
     and `$SOURCE_ROOT/docs/MODEL-CATALOG.md`, never CWD. Installed skills must read that
     absolute guide; [the repository-relative guide](../docs/MODEL-CATALOG.md) serves
     source readers. Missing guide/schema/rubric makes selection unavailable: preserve
     inputs and session, infer no scores/schema/candidates, and retain explicit-request
     eligibility checks. Run the verified helper's
     `--resolve-plan <plan> --provider <provider> --row <row-id> --resolution <resolution.json>`
     using that guide; keep `execution: null`.
     Supply fresh invocation support from actual permitted tools, permissions and
     restrictions, plus the task requirements and owner limits. Show requested,
     resolved and actual identities and rejection reasons. Unsupported explicit
     requests need an authorized eligible fallback or **stop**. Missing Python 3.11,
     helpers or catalog means selection unavailable: preserve the current session;
     never bypass explicit request eligibility. Without switching capability, run
     inline in the same session only when the verified current identity satisfies
     the request/fallback, or when no explicit request requires a switch, and note it.
     Actual stays unknown without a separate matching current execution receipt
     with caller provenance; a successful spawn alone proves no execution identity.
   - If atomic execution or its finalization is incomplete, call
     `/phase-atomic-execution <description-path>`. Execution complete with plan `done` and
     recorded finalization skips that call and resumes validation; an interrupted
     implementation-to-finalization boundary must finish `/pae-finalize` first.
   - Only after execution succeeds, call `/phase-atomic-validation <description-path> --batch`.
     `--batch` records proposals, prompts for nothing, and applies nothing.
   - On a stopped or failed child, persist its outcome and propagate the stop; do not run
     its successor or finalize the phase. Respect declared autonomous decision overrides;
     they never waive blockers, Guard confirmations, or the TDD gate.
   - After `reviewed`, run `/compress-state --auto` on the parent state.

3. Never execute composite rows atomically. Verify that every `children:` entry has a plan
   row and leaf block; a mismatch → **stop**: "Composite children mismatch. Re-run `/pd-decompose`."
   `/pav-close` step 5 owns the integration-validation trigger after the final child closes.
   Re-read the plan and state after each cycle so newly created fix siblings enter this loop.
   Process new ready leaves before treating the composite as stalled. Do not invoke an
   already-complete composite check a second time.

4. After leaf processing, reconcile each composite:
   - `integration-validation: complete` → `composite-reviewed`.
   - `rollup: blocked` or failed integration with no runnable approved fix → `composite-blocked`.
   - All children reviewed but integration not started → the trigger never fired. Record
     the composite as `composite-stalled`; `/pe-finalize` requires integration validation.
   - Otherwise record why it was not reached. Independent siblings may continue only
     when their dependency chains remain ready.

At an ambiguity, follow `workflow-globals` and the active caller's declared override.
Without such an override, describe the issue, offer 2–3 options with trade-offs, and wait for
user's choice. At a blocker, persist the blocker and stop.

## Execution Report persistence

After every processed, skipped, blocked, or deferred row, upsert one line by subtask ID in
parent `state.md → ## Execution Report`; never append a duplicate on resume:

```
## Execution Report
- T-01: reviewed — <result>
- T-02: blocked — <reason>
- T-03: deferred — <recorded decision>
- T-04: not-reached — <unmet dependency>
- T-05: composite-reviewed — children reviewed, integration passed
- T-05a: reviewed — <result>
```

Use `done`, `reviewed`, `blocked`, `deferred`, `not-reached`, `composite-reviewed`,
`composite-blocked`, or `composite-stalled` as applicable. Include composite rows and children.
This file, not conversation memory, supplies `/pe-finalize`.

Report: "Step 1 (Execute Subtasks) complete. <N> reviewed, <M> skipped."
This is a progress marker; return to the caller without starting another phase.
