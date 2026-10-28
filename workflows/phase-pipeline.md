---
description: Fully autonomous pipeline — run Discovery, Execution and Validation with explicit decision overrides and resumable state
---

Invocation: `/phase-pipeline <spec-path|task-directory>`

Run one task through three phases. Load `workflow-globals`; use the phase rules for
context bootstrap and resolve rule names as that contract specifies. Children reuse
context already loaded by this invocation; standalone children bootstrap themselves.

## Guard

Require an existing spec or task path. Read existing task state before writes. Resume
completed steps; never reset them. Guard confirmations that overwrite artifacts remain
mandatory in every mode. If all three phases are complete, report and **stop**.

## Run Logging

Follow `run-log → ## Workflow coverage and routing`. After Step 0 resolves the task,
open one run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-pipeline \
    --project "$WORK_DIR" --task <task-directory> --spec <spec-path> \
    --flow <quick|full>) || RUN_ID=""
fi
```

Do not open a second run in child phases; pass `RUN_ID` and let the outermost caller
close it. Log each executed child once and each exercised override as
`--step override:<child> --decisions 1 --note approximate`. Ordinary prompt steps
always carry `--note approximate`. Close with `run-end --outcome completed|stopped|failed`.
Missing helpers or logging errors never block work; mention unavailable logging once.

## Pipeline Overrides

The registry is `workflow-globals`; this table specifies this command's behavior.
Overrides apply only inside this invocation and never cross into a later spec phase.

| Decision point | Action |
|---|---|
| End of Discovery or Execution | Continue to the next phase after its completion marker is verified. |
| `pd-analyze`, `pd-decompose`, `pd-design` | Use autonomous defaults; never pass `--step-by-step`. Resolve design choices through the protocol below. |
| `pae-tests` output formatting | Pass `--batch` to suppress duplicate digest display; preserve every evidence/blocker gate. RED establishment is never skipped. |
| `pv-issues` approval | Approve `critical` and `important`; defer `optional`; record the automatic split. |
| `phase-composite-validation` integration approval | Apply the same split in `## Integration Issues (T-XX)`. |
| `pav-propose` | Pass `--batch`: record every proposal, apply nothing. |
| `pe-finalize` step 5, batched `Do Now` choice | Choose option 2: apply now before Validation, and record the automatic choice. |
| `pe-execute`, `pv-execute-fixes` ambiguity | Resolve through the protocol; external blockers still stop. |
| `compress-state` confirmation | Pass `--auto`; protected sections remain intact. |
| `spec-sync` reconciliation | Pass `--auto-mode` after Validation, retaining its failed-criterion guard. |

`Do Now` proposals against validation fix-tasks remain recorded and appear in the final
report; there is no later execution review stage to apply them automatically.

### Declared stops — steps this pipeline does NOT override

Escalate only for unresolved external inputs, breaking changes to consumed external
APIs, or unresolved user-visible trade-offs under the Autonomous Decision Protocol.
A requirement without a reasonable default after the research order is such a stop.
The following gates also stop and wait:

| Gate | Action |
|---|---|
| `pv-contract` critical-failure gate: failed Invariant or Off-limits | Record the failure; ask the human. |
| `pae-implement` out-of-scope work or composite-promotion tripwire | Preserve evidence; request the recorded decision. |
| `pae-tests`: `atomic-tests: failed` | Establish valid test evidence before continuing. |
| `phase-atomic-execution`, `pae-implement`: unresolved blocker | Preserve the stopping point and report the needed input. |
| `pe-finalize`: `integration-validation: failed` with all children reviewed | Keep the integration cycle open; do not mark Execution complete. |
| Any Guard confirmation that overwrites existing artifacts | Wait for explicit authorization. |
| Failed artifact validation or inconsistent phase markers | Repair the artifact or report the blocker before advancing. |

Completion of Validation ends this command; never launch the next spec phase.

## Deep Architectural Analysis Protocol

Canonical definition: `workflow-reference → ## Autonomous Decision Protocol`.
Use its variants, scoring, tie-breakers and decision record for substantive design
choices. Apply the additional stops above. Routine choices already determined by an
artifact need only that citation, not another scoring table.

## Step 0 — Bootstrap

1. Resolve `WORK_DIR` from `working_dir:` when present; otherwise use the project root
   owning the input and its `.ai/`. Resolve relative arguments from the caller's directory.
2. For a spec, **Run `phase-discovery` Step 0 in full**, once, for resolution only, and adopt its resolved task
   directory. This preserves multi-phase `-p<N>` naming and the numeric-prefix collision
   guard. This is read-only resolution: a fresh task is initialized by Discovery,
   not by the parent.
3. For a task directory, require and read its `state.md`. A legacy task-file argument resolves to its
   parent directory. Reject other input forms with the supported invocation.
4. For a newly resolved spec without task state, start Discovery. Otherwise read
   `## Phases`: resume the earliest incomplete phase and its first incomplete child.
   A later completed phase with an incomplete predecessor is inconsistent: **stop** and
   report the conflicting markers. Missing/invalid state on a resume is a prerequisite
   failure; do not manufacture a new task.
5. Report the task, flow tier and resume point. Open logging after resolution succeeds.

## Phase 1 — Discovery

Pass the resolved `--phase N` for multi-phase specs so the child keeps the selected
phase. Run `/phase-discovery` in autonomous mode. Read-only resolution did not initialize a
fresh task: let the child perform its normal initialization once. For an in-progress
Discovery, resume its recorded step; skip completed Discovery entirely.
It owns the quick/full branch, child sequencing, `/pd-archive` and completion checks.
Do not separately replay its children:

- `/pd-analyze` → `pd-analyze.md`
- `/pd-decompose` → `pd-decompose.md` (full only)
- `/pd-design` → `pd-design.md` (full only)
- `/pd-finalize` → `pd-finalize.md`

After `discovery: complete`, report the chosen approach and advance to Execution.

## Phase 2 — Execution

Run `/phase-execution <task-directory>` with the overrides above. It owns inline quick
execution or leaf cycles and the post-execution proposal review:

- `/pe-execute` → `pe-execute.md`
- `/pe-finalize` → `pe-finalize.md`
- `/phase-atomic-execution` → `phase-atomic-execution.md`
- `/pae-tests` → `pae-tests.md`
- `/pae-implement` → `pae-implement.md`
- `/pae-finalize` → `pae-finalize.md`
- `/phase-atomic-validation` → `phase-atomic-validation.md`
- `/pav-check` → `pav-check.md`
- `/pav-propose` → `pav-propose.md`
- `/pav-close` → `pav-close.md`
- `/phase-composite-validation` → `phase-composite-validation.md` (triggered by the last child's close)

Advance only after `execution: complete` and successful artifact checks.

## Phase 3 — Validation

Run `/phase-validation <task-directory>` with the overrides above:

- `/pv-contract` → `pv-contract.md`
- `/pv-review` → `pv-review.md`
- `/pv-issues` → `pv-issues.md`
- `/pv-create-fixes` → `pv-create-fixes.md` (full only)
- `/pv-execute-fixes` → `pv-execute-fixes.md` (full only)
- `/pv-finalize` → `pv-finalize.md`
- `/compress-state` → `compress-state.md`

Do not rerun fix creation or execution separately after this phase; its children own them.

## Final Report

Report the resolved task path, phase outcomes, implemented behavior, verification and
coverage, fixed/deferred issues, unprocessed proposals, state/plan paths and ADR paths
(or the recorded reason none was needed). Report completion only after
`validation: complete`; otherwise name the blocker and exact resume command.

## Interruption Recovery

Re-run the same invocation. Read current files, reconcile pending decisions, and resume
from the earliest incomplete checkpoint. Never infer completion from the last chat reply.
