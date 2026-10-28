---
description: Write an architectural decision record at the moment the decision is made, from a task directory or an explicit decision
---

Invocation: `/adr-new <source> [--title "<short title>"] [--provisional]`
`<source>` is a task directory or quoted decision text. Resolve relative paths from the
project root; use that project's `.ai/`. Write decision records, their index and task ADR pointers only.

## Schema — single source

Load the ADR trigger, body template, numbering, filename and index schema from
`pv-finalize → ## Instructions`, step 3. Use that schema unchanged, except for the status
and supersession handling below. Read only its ADR instructions; do not execute finalization.

## Guard

1. If `<source>` is a directory, read its `state.md` and resolve the task's `working_dir:`
   if present. If state is missing → **stop**: "No task state at `<path>`."
2. Find an explicit decision in `## Solution Design`, autonomous-decision records,
   `## Contract (quick)`, or decision-bearing `notes:`. If none → **stop**:
   "No recorded decision. Record the decision first or pass it as text."
3. For text input, use the supplied decision. If a path-like input does not exist, report
   the missing path rather than silently treating it as a decision.
4. Read `.ai/adr/index.md`, related ADRs, and any task `adr:` pointer. Match by the actual
   decision, not only the task number: a task may have several independent decisions.
   - Matching provisional record → update it in place; retain its number.
   - Matching accepted record with no change → report it and **stop**.
   - An accepted decision is being replaced → write a superseding ADR only with explicit
     authorization to change that decision. Otherwise report the proposed replacement
     and wait. Do not overwrite an accepted record's body.

## Step 1 — Gather the decision

Read only relevant portions of task state, `plan.md` when present, project principles,
architecture memory, and related accepted ADRs. Load umbrella context before local context
when the project uses both. Collect the choice, constraints, reason, alternatives,
consequences, and verification evidence. Use `--title` when supplied, otherwise derive a
short title describing the decision.

Cite code claims as `path:line`; label missing rationale/alternatives `not recorded`. Ask only when
missing intent prevents recording what was decided. If the canonical ADR trigger does not
apply, report why no ADR is needed and **stop**.

## Step 2 — Check for contradiction

- Conflicts with an accepted ADR → require an explicitly approved replacement decision.
  Add `## Supersedes` naming the old record and the changed decision. Once the new decision
  is accepted, mark the old record `Superseded by ADR-NNNN` and update both index rows.
  A provisional proposal leaves the accepted record's status intact.
- Conflicts with a principle → **stop**: identify the conflict and request an explicit
  decision about changing the principle. An ADR does not silently amend principles.

## Step 3 — Status

Use `Provisional` with `--provisional` or whenever implementation/verification is incomplete.
Use `Accepted` only for a decided, implemented and verified outcome. A flag never supplies
missing verification. Store status as the content under `## Status`, not in its heading.

`/pv-finalize` promotes a task's provisional ADR in place after validation. Do not reject
or remove abandoned-task records during this workflow unless abandonment was explicitly
recorded; then retain the record with its reason and date.

## Step 4 — Write

1. Allocate or retain the ADR number per the canonical schema. Write the record in English.
2. Fill `## Verification` from checks actually run. For a provisional record write:
   `Not yet verified — decision recorded before implementation completed.`
3. Create or update `.ai/adr/index.md` in its canonical column order. Preserve unrelated
   records and update matching rows rather than appending duplicates.
4. For task input, retain existing task ADR links and add/update an `adr:` pointer to this
   record with its status. A later finalizer must be able to find every provisional record.

## Step 5 — Report

Report path, status, decision, limitations and supersession. For a provisional task ADR,
name `/pv-finalize` as its promotion step. Then **stop**.
