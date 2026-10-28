# Backlog: a deterministic state tool for `## Subtask Progress`

## Status

**Backlog — not scheduled.** The owner decided (ADR-0009, Decision 5) that agents keep
editing state files directly for now. This file records the agreed shape so the work can
start without a new round of questions when the evidence (hand-edit corruption found by
`validate-task.sh`) justifies it.

## Current implementation baseline — 2026-10-28

No generic state tool has been added. Workflow state updates remain direct edits or
orchestrator-applied worker deltas (`rules/orchestration.md → ## Shared-file discipline`).
The workflow audit clarifies resume/field preservation and adds instruction checks;
these are not a state serializer or locking API. This spec remains unscheduled backlog.

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
  (temp file + rename), and holds a per-task-directory lock; the historical ten-minute
  stale-override policy must be reconciled at Discovery with live-owner/concurrency
  safety before implementation. Age alone must not silently evict an active writer;
  any change to the accepted policy needs a recorded decision.
- Optional at run time (ADR-0001): a missing tool means hand editing under the existing
  rules with a `notes:` line; an explicit manual mode exists for emergencies.
- Tests under `tests/` cover leaf and composite blocks, upsert on re-run, protected
  fields, illegal transitions, backward compatibility with a block lacking
  `atomic-tests:`.

## Interim guard (historical policy; verify current call sites)

ADR-0009 planned warn-only `scripts/validate-task.sh` calls from finalize/close steps.
Completed spec 02 owns log vocabulary, not this guard. When scheduling state work,
inventory actual callers and preserve any already established mandatory stops; do not
weaken a current gate by treating this historical sentence as its implementation.

## Notes

- Decisions: ADR-0009 Decision 5.
- Spec 12 was designed without this tool: in parallel mode only the orchestrator writes
  under `.ai/`.

## Roadmap boundary — 2026-10-21

This remains unscheduled. The nine optimization workstreams do not depend on it.
Spec 14 projects context; spec 15 inspects/renders proposals without mutating state;
the existing orchestrator applies patches. Neither introduces this generic write API.

Future acceptance must cover stale/live lock owners, unknown protected fields,
optimistic source revision checks, duplicate retries, interrupted atomic writes and
manual fallback. Any future serializer should reuse the canonical transition/evidence
contracts rather than create a competing state grammar. No implementation is authorized
by this review.
