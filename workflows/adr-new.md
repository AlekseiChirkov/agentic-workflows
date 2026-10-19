---
description: Write an architectural decision record at the moment the decision is made, from any source — a task directory, a design step, or a decision the human just took
---

Invocation: `/adr-new <source> [--title "<short title>"] [--provisional]`
Examples:
- `/adr-new .ai/tasks/todo/task-04-billing/` — from a task's recorded decisions
- `/adr-new .ai/tasks/todo/task-04-billing/ --provisional` — decision taken, work not finished
- `/adr-new "chose Redis over in-process cache for session state"` — from a bare decision

---

## Why this exists

`/pv-finalize` is the only workflow that writes an ADR, and it runs at the very end of
Validation. A decision taken in `/pd-design` therefore reaches `.ai/adr/` only if the whole
task validates successfully. Every task that ends `blocked`, `deferred`, or interrupted
loses its architectural reasoning permanently — the decision survives in `state.md`, inside
a task directory nobody reads again.

This workflow decouples *recording a decision* from *finishing a task*. It writes the same
artifact, in the same schema, at whatever moment the decision actually exists.

**It does not replace `/pv-finalize` step 3.** That step remains the end-of-task ADR and
keeps its trigger. This workflow is for decisions that need recording earlier, or outside a
task entirely.

---

## Schema — single source

The ADR body template, the quality requirements, and the index schema are defined **once**,
in `pv-finalize → ## Step 3` (sub-steps 3.3 through 3.7). Read them and follow them exactly.
Do not restate them here and do not invent a variant: two ADR schemas in one repository
silently corrupt the index, because an appended row in a different column order shifts every
value.

The two rules that are easiest to get wrong, repeated because they are load-bearing:

- File name: `NNNN-task-<ID>-<short-title>.md`, `NNNN` = highest existing + 1, zero-padded
  to four digits, `unknown` for `<ID>` when there is no task.
- Index row, in the header's column order:
  `| NNNN | <ADR title — the decision in a few words> | Accepted | YYYY-MM-DD | [<adr-file-name>.md](<adr-file-name>.md) |`

**Language:** the ADR file and the index are project files. English only, whatever language
the conversation is in (`language` rule).

---

## Guard

1. Resolve `<source>`:
   - **A directory** → a task directory. Read `state.md`; it must exist.
   - **Anything else** → the literal text of a decision, recorded standalone.
2. For a task directory, read `## Solution Design → ### Decision` and `### Autonomous
   Decision`. If neither exists → **stop**: "No recorded decision at `<path>`. Run
   `/pd-design <path>` first, or pass the decision as text."
3. Check whether an ADR for this task already exists — scan `.ai/adr/*.md` for
   `NNNN-task-<ID>-*`. If one does:
   - and it is `## Status: Provisional` → this run **supersedes** it in place: keep the
     number, replace the body, set the status per Step 3.
   - and it is `## Status: Accepted` → **stop**: "ADR `<file>` already records task `<ID>`.
     Amending an accepted ADR needs a new ADR that supersedes it. Confirm to write a
     superseding record? (yes/no)". Wait.

---

## Step 1 — Gather the decision

For a **task directory**, read in this order and take only what bears on the decision:

1. `state.md → ## Solution Design` — `### Decision`, `### Variants`, `### Rejected`,
   `### Autonomous Decision` (the scoring table is the reasoning; carry its conclusion, not
   the table).
2. `state.md → ## Task Analysis → ### Assumptions` — assumptions the decision rests on.
3. `state.md → ## Contract (quick)` for a quick-tier or `/bugfix` task.
4. `plan.md` — the shape the decision produced.
5. `.ai/adr/index.md` — any existing ADR this decision changes or contradicts. A new ADR
   that silently contradicts an accepted one is the defect this step exists to catch.

For a **bare decision**, the text is the decision; gather its context from
`.ai/memory/architecture.md` and `.ai/principles/*`, and ask the human for the alternatives
considered if none are stated. An ADR without rejected alternatives records a preference,
not a decision.

**The evidence rule.** Every claim about existing code carries a `path:line`. A decision's
consequences are only credible if the current state it changes is cited.

---

## Step 2 — Check for contradiction

Compare the decision against `.ai/adr/index.md` and `.ai/principles/*`.

- Contradicts an **accepted ADR** → the new ADR must say so explicitly: add a
  `## Supersedes` section naming the ADR number and what specifically no longer holds, and
  set the superseded ADR's `## Status` to `Superseded by ADR-NNNN`. Update both index rows.
- Contradicts a **principle** → **stop**. A principle is changed by editing
  `.ai/principles/*` deliberately, never by an ADR quietly ruling the other way. Report the
  conflict and ask whether the principle is being changed.

---

## Step 3 — Status

| Status | When | Written by |
|---|---|---|
| `Accepted` | The decision is made and the work implementing it is complete or already shipped | default |
| `Provisional` | The decision is made, the work is not finished — the common case when called from Discovery | `--provisional` |

`Provisional` exists so a decision from `/pd-design` can be recorded immediately without
claiming an outcome it has not yet earned. `/pv-finalize` promotes it: when it finds a
provisional ADR for the task it is closing, it updates that ADR in place — status
`Accepted`, `## Verification` filled from the validation results — instead of writing a
second record. The index row's `Status` column is updated to match.

An abandoned task's provisional ADR is **left in place**, its status set to
`Rejected — task abandoned <date>` with one line of reason. A recorded decision that was
not taken is still worth more than a lost one: it stops the next person re-deriving it.

---

## Step 4 — Write

1. Write the ADR file per `pv-finalize → ## Step 3.4`, with the status from Step 3.
2. Fill `## Verification` honestly. For a provisional ADR write exactly:
   `Not yet verified — decision recorded before implementation completed.`
   Never describe checks that have not run.
3. Update `.ai/adr/index.md` per `pv-finalize → ## Step 3.7`, creating it with the canonical
   header if absent:
   ```
   | Number | Title | Status | Date | Link |
   |--------|-------|--------|------|------|
   ```
4. When the source was a task directory, add one line to `state.md`:
   `adr: .ai/adr/NNNN-task-<ID>-<short-title>.md (<status>)` — so `/pv-finalize` finds the
   provisional record instead of writing a duplicate.

---

## Step 5 — Report

Print the ADR path, its status, the decisions recorded (one line each), anything superseded,
and — for a provisional ADR — the reminder that `/pv-finalize` will promote it.

Then **stop**. This workflow writes no code, changes no phase status, and starts nothing.
