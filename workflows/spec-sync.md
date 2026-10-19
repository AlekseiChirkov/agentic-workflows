---
description: Reconcile a shipped implementation against its spec — record what was actually built, so the spec stays the source of truth instead of a historical artifact
---

Invocation: `/spec-sync <task-directory> [--auto-mode] [--dry-run]`
Examples:
- `/spec-sync .ai/tasks/completed/task-01-add-oauth/` — reconcile after validation
- `/spec-sync .ai/tasks/todo/task-04-billing/ --auto-mode` — no questions, record deltas
- `/spec-sync .ai/tasks/completed/task-01-add-oauth/ --dry-run` — report the delta, change nothing

Called by `/pv-finalize` as its last step, and runnable standalone at any time.

---

## Why this exists

`.ai/specs/<NN>-<slug>.md` is **immutable during a task** (`workflow-reference → ## File
Responsibility`) — that rule is what stops an agent from quietly rewriting the requirement
it failed to meet, and this workflow does not weaken it. But immutable-forever turns the
spec into a historical artifact: implementation legitimately diverges through Description
Amendments, deferred items, accepted compromises, and validation fixes, and none of that
ever reaches the spec. From the second task onward, the spec describes a system that no
longer exists.

This workflow closes that loop **after** the task is done, at one controlled moment, with
every change attributed to a recorded source. It is the only workflow permitted to write to
a spec after Discovery has started.

---

## Guard

1. Read `state.md` in the task directory. If absent → **stop**: "No `state.md` at
   `<path>`. Nothing to reconcile."
2. Read `spec_path:`. If absent → **stop**: "No `spec_path:` in `state.md` — legacy task,
   nothing to reconcile." If present but the file does not exist → **stop** and name the
   missing path.
3. Check `## Phases → validation`. If not `complete` → **warn**, do not stop: "Validation is
   `<status>`. Reconciling before validation records deltas that may still change." Continue.
4. Read `## Spec Sync` in `state.md`. If it exists with `sync: complete` and no file has
   changed since (compare against the recorded `synced_at:`), report "Already reconciled at
   `<timestamp>`; no new deltas." and **stop**.

---

## Step 1 — Build the delta

Collect every recorded divergence between what the spec asked for and what exists. Read,
in this order:

1. `state.md → ## Task Analysis → ### Assumptions` — what was assumed rather than specified.
2. `state.md → ## Solution Design → ### Decision`, `### Scope`, `### Rejected` — the shape
   that was actually chosen, and what was explicitly excluded.
3. `plan.md → ## Subtasks` — any subtask ending `deferred`, `blocked`, or `not-reached`.
   Whatever it covered is in the spec but not in the system.
4. Every `T-XX/description.md → ### Description Amendments` — the amendment procedure
   records intent changes at subtask level and nowhere else.
5. `state.md → ## Deferred` — items the human accepted as not-now.
6. `state.md → ## Issue List` and `## Fix-Tasks` — behaviour that changed during validation.
7. `state.md → ## Contract Check` — any Acceptance Criterion recorded as met by different
   means than the spec described.

For each divergence produce one delta row:

| id | Spec says | System does | Source | Class |
|---|---|---|---|---|

`Class` is one of:

- **`implemented-differently`** — the requirement is met, by other means than the spec
  described. The spec text is now wrong and must be corrected.
- **`not-implemented`** — deferred, blocked, or dropped. The spec is right and the system
  is behind; the spec must say so rather than silently over-promise.
- **`implemented-beyond`** — behaviour exists that no requirement asked for. Either a
  missing requirement or unrequested scope; both need recording.
- **`spec-was-right`** — no divergence. Not written anywhere; counted only.

A divergence you cannot attribute to one of the seven sources above is **not** a delta —
it is an observation, and it goes to `## Open Questions` in the spec instead. Never infer a
requirement change from code alone: the whole value of this step is that every spec edit
carries a citation.

If `--dry-run` → print the delta table and **stop**. Nothing is written.

---

## Step 2 — Decide what the spec should say

**`--auto-mode`:** resolve each delta yourself. `implemented-differently` → rewrite the
requirement to describe the built behaviour, keeping the original id and appending
`(revised <date>)`. `not-implemented` → mark the requirement `(deferred <date>)` and leave
its text intact. `implemented-beyond` → append a new requirement with the next free id.
Never delete a requirement, and never renumber one.

**Interactive (default):** present the delta table, then ask per class — not per row —
which of the three treatments applies, offering the auto-mode treatment as the
recommendation. A human answer that contradicts a binding source is handled exactly as in
`spec-draft → ## Step 4B → Conflict rule`.

**The one thing neither mode may do:** silently weaken an Acceptance Criterion that
validation recorded as *failed*. A failed criterion is a defect, not a delta. If Step 1
surfaces one, stop and report it — the fix belongs in a fix-task, not in a spec edit.

---

## Step 3 — Write the spec

Edit `spec_path:` in place. Apply, in order:

1. Append a `## Change Log` section if absent, and add one entry:

```
### <YYYY-MM-DD> — reconciled from task-<NN>-<slug>
- <id> | <class> | <what changed in the spec> | Source: <the state file section cited>
```

2. Apply each accepted treatment from Step 2 to the body. Requirement ids are stable:
   revise text in place, never renumber; append new ids at the end; mark withdrawn ones
   rather than deleting them.
3. If the spec has a `## Readiness Checklist` (written by `/spec-draft`), re-run the gate
   from `spec-draft → ## Step 7` against the revised text and replace the checklist with
   the new result. A spec that is now internally inconsistent must say so.
4. If the spec has no `## Change Log` and no `## Readiness Checklist` — a hand-written spec
   from the minimal template — add only the change log. Do not restructure a spec the human
   wrote; reconcile it and leave its shape alone.

Preserve everything the spec already says that no delta contradicts. This workflow edits
what diverged; it does not rewrite prose it merely disagrees with stylistically.

---

## Step 4 — Record and report

1. Write to `state.md`:

```
## Spec Sync
sync: complete
synced_at: <YYYY-MM-DD>
deltas: <N> (implemented-differently: <a>, not-implemented: <b>, implemented-beyond: <c>)
spec: <spec_path>
```

2. Append one line to `.ai/memory/progress.md` naming the spec reconciled and the delta
   counts.
3. If any delta was classed `implemented-beyond` **and** the behaviour is architecturally
   significant by the criteria in `pv-finalize → ## Step 3`, report that an ADR is owed and
   print `/adr-new <task-directory>` as plain text. Do not write the ADR here.
4. Report: the spec path, the delta counts, what was changed, and anything sent to
   `## Open Questions`.

Then **stop**. This workflow never advances a phase and never edits code.
