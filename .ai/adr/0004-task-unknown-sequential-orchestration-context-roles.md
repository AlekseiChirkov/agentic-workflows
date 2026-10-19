# ADR-0004: Decisions for Task unknown — Orchestrated mode uses context-bounded roles and strictly sequential execution

## Status

Accepted — Decision 3 narrowed by ADR-0009 (parallelism allowed between children of one composite)

## Date

2026-08-26

## Related Task

- Task: none — design of `/spec-run`
- Related files: `rules/orchestration.md`, `workflows/spec-run.md`, `docs/SPEC-RUN-QUICKSTART.md`

## Summary

`/spec-run` splits a run into four roles — Orchestrator, Arbiter, Implementer, Validator —
defined as context boundaries. Sub-agents exist to bound context, not to parallelise;
execution is one subtask at a time.

## Context

A single session running a whole spec ran out of context halfway. Giving each subtask a
fresh, narrow agent solves that, but a narrow agent cannot answer questions that need
project context, and an agent that watched the code being written cannot review it
independently. Meanwhile the state file has no locking.

## Decisions

### Decision 1: Four roles as context boundaries

**What was decided:**
Orchestrator owns sequencing, git, shared files, never writes code. Arbiter lives for the
whole run, answers class-A questions only, always with a citation. Implementer runs one
subtask's atomic execution and pauses once at RED. Validator is a separate agent that
never sees the Implementer's reasoning.

**Why:**
Token economy (narrow agents), independent validation (separate Validator), a cheap
source of project context (Arbiter) without reloading it into every sub-agent.

**Alternatives:**
- Persona-style roles with full context each (BMAD-like) — rejected: no context saving,
  no independence.
- Tests and implementation in separate agents — rejected: GREEN must read the RED set it
  satisfies; splitting pays the bootstrap twice for no isolation gain.

**Consequences:**
Only executable on a harness with sub-agents and message addressing (Claude Code). The
RED pause is what makes the separate `test:` commit possible.

**Related files:**
- `rules/orchestration.md → ## Roles`

### Decision 2: Class A / class B escalation with a single batch gate

**What was decided:**
Missing-context questions go to the Arbiter; missing-intent questions go to the human and
are harvested during Discovery into `## Open Questions (batch)`, presented once before
the first branch. A class-B leak during Execution stops the run.

**Why:**
In a sequential chain, parking a subtask is stopping the run; the cheapest moment to ask
is before any branch exists.

**Alternatives:**
- Ask as questions arise — rejected: invalidates stacked branches.
- Let the Arbiter decide intent — rejected: unsupported claims; the citation rule forbids it.

**Consequences:**
Discovery quality gates the whole run; a missed class-B question costs a stop.

**Related files:**
- `rules/orchestration.md → ## Escalation protocol`

### Decision 3: Strictly sequential

**What was decided:**
No workflow may run subtasks concurrently. Branch N is cut from N-1's reviewed tip.

**Why:**
`## Subtask Progress` is one section in one file with no locking.

**Alternatives:**
- Worktree-per-subtask parallelism — deferred: requires per-subtask state files or a
  locking tool first.

**Consequences:**
Observed wall-clock of 21–26 h per spec-run with independent subtasks serialized.

**Related files:**
- `rules/workflow-globals.md → Orchestrated mode`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Parallelism is the largest available speed-up and is blocked only by Decision 3's premise;
see `specs/07-state-tool.md` and `specs/README.md` for the ordering.

## Verification

`docs/audits/AUDIT-PROMPT.md` was written to audit exactly this design; the run log records the four
spec-run executions.
