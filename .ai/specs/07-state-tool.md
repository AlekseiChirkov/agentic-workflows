# Backlog: a deterministic state tool for `## Subtask Progress`

## Status

**Backlog — not scheduled.** The owner decided (ADR-0009, Decision 5) that agents keep
editing state files directly for now. This file records the agreed shape so the work can
start without a new round of questions when the evidence (hand-edit corruption found by
`validate-task.sh`) justifies it.

## Goal

Every workflow rewrites `## Subtask Progress` blocks by hand. The 2026-07 audit found
blocks never created, duplicated, or truncated; the Protected Sections Contract exists
only because edits are free-form. A small tool that reads and writes the blocks by field
name would make edits atomic and validated.

## Agreed shape (when scheduled)

- Python 3, single file, standard library only; invoked from `ORCHESTRAIL_HOME/bin/`,
  never copied into a consumer project.
- Owns **only** `## Subtask Progress` (leaf and composite blocks). `plan.md` and
  `.ai/memory/state.md` stay under direct agent control.
- Commands: `get`, `set`, `append-note`, `add-file`, `init-block`, `validate`.
- Every write re-serialises the block in canonical order, preserves unknown fields, never
  drops protected fields, refuses illegal status values (non-zero exit), is atomic
  (temp file + rename), and holds a per-task-directory lock; a stale lock older than 10
  minutes is overridden with a warning.
- Optional at run time (ADR-0001): a missing tool means hand editing under the existing
  rules with a `notes:` line; an explicit manual mode exists for emergencies.
- Tests under `tests/` cover leaf and composite blocks, upsert on re-run, protected
  fields, illegal transitions, backward compatibility with a block lacking
  `atomic-tests:`.

## Interim guard (scheduled instead, inside spec 02's chain)

`validate-task.sh` runs warn-only from `/pae-finalize`, `/pav-close`, `/pe-finalize`,
and `/pv-finalize` (their renamed forms after spec 13).

## Notes

- Decisions: ADR-0009 Decision 5.
- Spec 12 was designed without this tool: in parallel mode only the orchestrator writes
  under `.ai/`.
