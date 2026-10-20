# ADR-0007: Decisions for Task unknown — This repository commits its own `.ai/` knowledge base

## Status

Accepted

## Date

2026-09-16

## Related Task

- Task: none — decision taken while creating `.ai/` for the repository itself
- Related files: `.ai/`, `templates/.ai/`, `rules/git-flow.md → ## Preflight` (check 3), `setup-new-project.sh` (`.gitignore` step)

## Summary

Unlike consumer projects, agentic_workflows tracks `.ai/` in git **in full** — every
directory and file, including in-flight task directories under `.ai/tasks/todo/` —
because for an open-source project the knowledge base *is* the contributor
documentation, and the task directories are the record of how each change was made.

## Context

ADR-0002 keeps `.ai/` out of consumer repositories to avoid divergent state on stacked
branches and dangling references. This repository is different: its "code" is the
process itself, contributors need `architecture.md`, the ADRs, and the roadmap in
`specs/` to work on it, and there is no stacked-branch flow for the repository's own
changes yet.

## Decisions

### Decision 1: Track `.ai/` in full

**What was decided:**
Commit everything under `.ai/` — `README.md`, `memory/`, `principles/`, `context/`,
`adr/`, `specs/`, `tasks/todo/`, `tasks/completed/`, and a generated `context-pack.md`
if one exists. No `.gitignore` entry mentions `.ai/`. Confirmed by the owner on
2026-09-16.

**Why:**
Contributors and agents start from context instead of re-reading 16 000 lines.
Completed task directories are the audit trail of how a change was made — valuable for
a project whose product is the process.

**Alternatives:**
- Keep `.ai/` untracked (the default) — rejected: knowledge would live on one machine.
- Move the content to `docs/` in a different shape — rejected: the pipeline's own
  workflows expect `.ai/` and would not load `docs/`.
- Track everything except `tasks/todo/` — rejected by the owner: in-flight state is
  part of the record; the history noise is accepted, and a task's commits can be squashed
  when it completes.

**Consequences:**
`/spec-run` preflight check 3 would refuse to run on this repository. Until a
repository-level override exists, changes here run through `/phase-*` manually or
`/bugfix`, not `/spec-run`. ADR-0005's "dangling reference" rationale does not apply
here, but the no-attribution and no-identifier commit rules still do.

**Related files:**
- `.gitignore` (to be created with `specs/completed/01-git-source-of-truth.md`)

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| Should `.ai/tasks/todo/` be tracked too? | Yes — the owner wants `.ai/` committed in full | No `.gitignore` entry for `.ai/`; `specs/01` updated |
| Should `/spec-run` gain a flag to allow a tracked `.ai/`? | Open | If yes, a spec is needed; if no, this repository never uses `/spec-run` on itself |

## Rejected Options

See Alternatives.

## Implications for Future Work

When `specs/01` puts the repository under git, the first commit includes `.ai/` in full.
A future ADR may revisit `tasks/todo/` if history noise becomes a problem.

## Verification

None yet — the repository is not under git.
