---
description: Reconcile implementation against its spec — record verified delivery and approved divergences without weakening requirements
---

Invocation: `/spec-sync <task-directory> [--auto-mode] [--dry-run]`
Called by: `/pv-finalize` after validation; also runnable standalone.
Resolve task paths from the project root and use that task's `spec_path:`.

`--dry-run` reports only and takes precedence over all write instructions. `--auto-mode`
applies source-backed reconciliation treatments without a prompt; it never supplies
missing authorization or turns a failed criterion into success.

## Guard

1. Read task `state.md`. If absent → **stop**: "No task state at `<path>`."
2. Read `spec_path:` and the referenced spec. If absent → **stop**: "Legacy task has no
   spec to reconcile." If the path is missing → **stop**: name it.
3. Respect `workflow-reference → ## File Responsibility`: task requirements remain
   immutable during implementation. If validation is incomplete, perform a report-only
   pass unless the user explicitly authorized reconciliation at this point, or a calling
   `/pv-finalize` has verified all contract/review/fix prerequisites and is completing its
   finalization steps. Record the authority/evidence; label any incomplete delivery
   accurately. The finalizer need not mark validation complete before this call succeeds.
4. Read any existing `## Spec Sync` and change log to avoid duplicate edits. A `synced_at:`
   date alone cannot prove unchanged inputs; recheck evidence. If no new verified delta
   or metadata change exists, report "Already reconciled; no new changes." and **stop**.

## Step 1 — Build the delta

Read the spec and relevant evidence, loading only decision-bearing portions:

1. Task analysis assumptions and solution-design decisions/scope/rejected alternatives.
2. `plan.md` if present: deferred, blocked or not-reached work is not delivered.
3. Subtask `description.md` amendment records, following archive pointers when needed.
4. Task deferred items, issue decisions, fix-task outcomes and contract-check results.
5. Explicit user-approved scope changes, including a direct request to reconcile current
   reality. Verify resulting behavior against code/tests; code alone cannot authorize a
   requirement change.

A failed criterion is a defect, not a delta. If validation records a failed Acceptance
Criterion → **stop**: report it for repair; neither mode may weaken it in the spec.

Build one row per actual divergence:

| id | Spec says | System does | Source | Class |
|---|---|---|---|---|

| Class | Treatment |
|---|---|
| `implemented-differently` | Revise to the approved implemented behavior, preserving intent and id |
| `not-implemented` | Keep requirement text; annotate verified deferred/blocked/not-delivered status |
| `implemented-beyond` | Add a requirement only for approved delivered scope; flag unapproved scope for a decision |
| `spec-was-right` | Count only; no edit |

Cite the exact artifact/section or explicit decision for each delta. Unattributed
observations become proposed `## Open Questions`, never inferred requirement changes.
Future roadmap requirements remain future requirements; existing functionality may satisfy
part of them without making the rest obsolete.

With `--dry-run`, or report-only mode from the Guard, print the table and proposed open
questions, then **stop** without any file write.

## Step 2 — Decide what the spec should say

With `--auto-mode`, apply the table's treatment to approved deltas. Otherwise present the
table and proposed treatments in one batch and wait for choices not already authorized.
If a choice contradicts a binding source, apply
`spec-draft → ## Step 4B — Resolution, --brain-storm (default)` (Conflict rule).

Never delete or renumber requirements/criteria. Mark withdrawals and deferrals explicitly
with date and source. Distinguish a delivered compromise from an unmet requirement; a
code change does not retroactively approve either.

## Step 3 — Write the spec

1. Apply accepted deltas in place; preserve unrelated text and the document's structure.
   Append stable ids for new requirements when the spec uses ids. Keep existing source
   and clarification records; retain old intent through the change log.
2. Add/update `## Change Log` with date, task, delta id/class, actual edit and source.
   Do not duplicate an unchanged reconciliation entry. Add proposed observations to
   `## Open Questions` only when writes are authorized.
3. If `## Readiness Checklist` exists, rerun
   `spec-draft → ## Step 7 — Readiness gate` and replace only its current result. Do not
   impose the extended authoring format on a minimal or handwritten spec.
4. Preserve completion metadata accurately. Reconciliation is not proof that a pending
   task is complete; do not add `status: done` for incomplete work.

## Step 4 — Record and report

Write task state after the spec edits succeed:

```text
## Spec Sync
sync: complete
synced_at: <ISO-8601 timestamp with timezone>
deltas: <N> (implemented-differently: <a>, not-implemented: <b>, implemented-beyond: <c>)
spec: <spec_path>
```

Append one progress entry for a new reconciliation; a no-op rerun adds none. If new
architecturally significant delivered scope meets the ADR trigger in
`pv-finalize → ## Instructions`, step 3, report the owed ADR and print
`/adr-new <task-directory>`; do not invoke it here.

Report path, delta counts, edits, unresolved observations and validation limitations.
Then **stop**; advance no phase.
