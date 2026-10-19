# ADR-0002: Decisions for Task unknown — All pipeline state lives on disk in `.ai/` and is never committed

## Status

Accepted

## Date

2026-07-01 (reconstructed)

## Related Task

- Task: none — foundational decision
- Related files: `rules/workflow-globals.md → Canonical Status Formats`, `rules/git-flow.md → ## Preflight`, `setup-new-project.sh`, `templates/.ai/`

## Summary

Progress is persisted in `state.md` / `plan.md` / `T-XX/description.md` under the consumer
project's `.ai/`, resumed by re-running the same command, and `.ai/` is gitignored.

## Context

Long tasks outlive a context window; sessions crash; agents are swapped. A phase must be
resumable from artifacts alone. At the same time a stacked-branch model would put a
divergent `state.md` on every branch if `.ai/` were tracked.

## Decisions

### Decision 1: State on disk, "continue, never restart"

**What was decided:**
Every workflow reads `state.md` before acting; every step writes `last_action:` and
`target_files:` immediately; Guards find the resume point.

**Why:**
Resumability without flags; an operator can watch progress in one file.

**Alternatives:**
- Conversation memory / summaries — rejected: lost on session end.
- A database or JSON store — rejected: not human-readable in a harness, needs tooling.

**Consequences:**
Markdown has no locking, so one writer per shared file (ADR-0004) and strictly sequential
execution. Model-edited markdown blocks get truncated or drift; `validate-task.sh` exists
to catch that after the fact.

**Related files:**
- `rules/workflow-globals.md`, `rules/workflow-reference.md → ## Protected Sections Contract`

### Decision 2: `.ai/` is untracked in consumer projects

**What was decided:**
`setup-new-project.sh` adds `.ai/` to `.gitignore`; `/spec-run` preflight refuses if
`git ls-files .ai` returns anything; `git add -A` is forbidden.

**Why:**
Pipeline state must not appear in the repository history or on stacked branches;
identifiers in `.ai/` must not become dangling references for readers (ADR-0005).

**Alternatives:**
- Commit `.ai/` as project documentation — rejected for consumer projects: every branch in
  a stack would carry a different `state.md`; merge conflicts on state.

**Consequences:**
Traceability from a commit back to its subtask exists only on the machine that ran the
task. Knowledge (`architecture.md`, ADRs) is not shared with teammates through git unless a
project decides otherwise. For **this** repository the opposite choice is proposed in
ADR-0007.

**Related files:**
- `rules/git-flow.md → ## Preflight`, `## Commits → Staging`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Parallel execution requires a state format with one file per subtask or a locking tool
(`specs/07-state-tool.md`, `specs/10` ordering in `specs/README.md`).

## Verification

`git-flow` preflight check 3; `validate-contracts.sh` groups covering canonical formats.
