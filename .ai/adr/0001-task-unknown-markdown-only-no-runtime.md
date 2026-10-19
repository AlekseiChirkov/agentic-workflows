# ADR-0001: Decisions for Task unknown — The pipeline is markdown instructions with no runtime

## Status

Accepted

## Date

2026-07-01 (reconstructed; the decision predates the first audit)

## Related Task

- Task: none — foundational decision
- Related files: `docs/USAGE.md → ## 1`, `AUDIT-PROMPT.md → ## 1`, `sync.sh`

## Summary

The entire system is plain markdown plus shell scripts that only copy files. Every
behaviour is an instruction the agent reads; nothing executes the pipeline on the agent's
behalf.

## Context

The system had to run inside three different agent harnesses (Windsurf, Claude Code,
Codex) that share no plugin API, and had to be editable by the same agents it governs.
A runtime would have to be written three times or would lock the system to one harness.

## Decisions

### Decision 1: No runtime; instructions only

**What was decided:**
Workflows, rules, and principles are markdown files. Shell scripts copy, validate, and log;
they never execute a workflow step.

**Why:**
Portability across harnesses; zero installation in a consumer project; the agent can read
and reason about the whole process; the process can be audited by reading.

**Alternatives:**
- A CLI orchestrator (Python) driving the agent through an API — rejected: harness-specific,
  a second codebase to maintain, hides the process from the agent.
- Harness plugins per environment — rejected: three implementations, drift.

**Consequences:**
Every defect is a defect of specification, not code. Enforcement rests on the model's
compliance, which the run log shows is imperfect (retroactive logging, non-vocabulary
statuses). Determinism must be recovered incrementally by moving rails into the harness
(hooks, deny-lists, validating scripts) — see ADR-0008 and `specs/`.

**Related files:**
- `validate-contracts.sh` — the only enforcement that runs without an agent

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Any script added to the repository must remain optional for the pipeline to function
(logging never blocks; validation blocks only deploy). A future state-tool
(`specs/07-state-tool.md`) is the first script a workflow would *depend* on at run time,
and needs its own ADR.

## Verification

`sync.sh` performs only `cp`, `mkdir`, `ln`, and `rm` of shadowing copies; no script
invokes an agent.
