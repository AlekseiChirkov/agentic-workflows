# state.md — current task-level state and active work

## Purpose
The agent writes here the current state of all active tasks: which tasks are
in progress, their phase status, and any deferred or blocked items. This is
the canonical task-level context loaded at the start of every session.
Answers "what is the current work in flight?" Updated after every phase
transition.

## Structure

## Active Tasks
One entry per task: name, link to task directory, current phase, status.
Entry format: `workflow-reference → ## .ai/memory/state.md Entry Format`.
A task waiting on an external dependency stays here with `status: blocked` — there is no
separate blocked section.

## Done
Completed tasks. `/pv-finalize` moves an entry here from `## Active Tasks` when validation
completes with no deferred items.

## Deferred
Tasks or items explicitly postponed, with reason.

Later phases of a multi-phase spec are recorded here by `/pd-finalize` in this format:
`- <basename> phase <K>/<M> | deferred | reason: later phase of <basename>, starts after phase <N> validation complete`
