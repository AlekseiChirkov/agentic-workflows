# ADR-0021: Decisions for Task 07 — Schedule the state tool with a kernel-released lock

## Status

Accepted

## Date

2026-11-13

## Related Task

- Task: owner decision to schedule `.ai/specs/07-state-tool.md` for implementation.
- Related files: `.ai/specs/07-state-tool.md`, `.ai/specs/README.md`,
  `.ai/memory/state.md`, `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md`.

## Summary

The state tool leaves the backlog. This record supersedes the state-tool paragraph of
ADR-0009 Decision 5 in four points: the work is scheduled, the lock is an OS advisory
lock with no stale takeover, the executable lives in `scripts/`, and ignore rules for
the tool's auxiliary files are part of the delivery. Every other part of ADR-0009
Decision 5 stays in force.

## Context

ADR-0009 Decision 5 kept the tool unbuilt and described it as a single standard-library
Python file invoked from `ORCHESTRAIL_HOME/bin/`, with a per-task lock and a ten-minute
stale override. The specification was refined on 2026-11-13 into an implementation-ready
design that deliberately departs from two of those points and deferred the superseding
record to the moment of scheduling. Its constraints required an explicit owner decision
to schedule and asked for real corruption examples first.

Evidence collected on 2026-11-13: `scripts/validate-task.sh` exits 0 on all eight
completed task directories under `.ai/tasks/completed/`. No block corruption is on
record in this repository.

## Decisions

### Decision 1: Schedule the state tool

**What was decided:** The owner schedules spec 07 for implementation on 2026-11-13. The
corruption-evidence precondition is waived; the finding that no corruption is on record
is kept here instead.

**Why:** The design is complete and reviewed, the tool is optional and unwired, and it
touches no existing workflow, so building it carries low risk to current runs.

**Alternatives:** Keep it in the backlog until a validator failure shows corruption —
rejected by the owner. Collect consumer-project examples first — rejected: no such
records are available and the tool refuses rather than guesses on unknown shapes.

**Consequences:** The roadmap lists 07 as scheduled. It remains outside the dependency
chain: no other roadmap item depends on it, and workflows keep editing state by hand
until a separate wiring specification. The value of the tool is unproven by evidence;
adoption is decided after delivery.

### Decision 2: OS advisory lock, no stale takeover

**What was decided:** Writers hold `fcntl.flock` on `<task>/.state-tool.lock`. The kernel
releases it when the holder exits. A lock older than ten minutes is reported as a
suspected hang and is never deleted, truncated or taken over.

**Why:** Lock age never proves that the owner is dead; a takeover of a live owner loses
an update. Kernel release already covers dead owners.

**Alternatives:** The ten-minute stale override of ADR-0009 — rejected for the reason
above. A lock directory with an owner protocol — rejected: more recovery code for the
same guarantee.

**Consequences:** Writes are limited to local filesystems on Linux and macOS. Without
`fcntl` the tool serves reads only. A genuinely hung holder needs a human to stop it.

### Decision 3: The executable is `scripts/state-tool.py`

**What was decided:** One file, `scripts/state-tool.py`, Python 3.11 or newer, standard
library only. No `bin/` directory is introduced.

**Why:** Existing helpers live in `scripts/`, require Python 3.11 and are already covered
by deployment and layout rules.

**Alternatives:** `ORCHESTRAIL_HOME/bin/` as in ADR-0009 — rejected: a new top-level
directory for sync and layout rules with no benefit.

**Consequences:** The script inventory gains one row. Callers address the tool through
the source root like other helpers.

### Decision 4: Ignore the tool's auxiliary files

**What was decided:** The delivery adds ignore rules for `.state-tool.lock` and
`.state.md.*.tmp` to this repository's `.gitignore` and to the entries that
`scripts/setup-new-project.sh` writes into consumer projects.

**Why:** This repository tracks `.ai/` in full, so the files would otherwise appear as
untracked and could be committed by accident. Consumer projects that track `.ai/` have
the same exposure.

**Alternatives:** This repository only — rejected: consumers that track `.ai/` stay
exposed. No rules — rejected: permanent noise in `git status`.

**Consequences:** The task `state.md` itself must never match the rules; the acceptance
criteria check that.

## Verification

Documentation-only decision record. The specification's acceptance criteria verify the
decisions when the tool is built.
