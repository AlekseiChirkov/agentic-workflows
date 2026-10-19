# ADR-0008: Decisions for Task unknown — Roadmap direction: move enforcement from prose into the harness before adding rules

## Status

Accepted — confirmed by the owner's answers recorded in ADR-0009 (order of work, telemetry before limits, harness abstraction)

## Date

2026-09-16

## Related Task

- Task: none — conclusion of the 2026-09 comparative analysis (`ANALYSIS.ru.md → §8`)
- Related files: `.ai/specs/README.md`, `.ai/principles/architecture.md → P10`

## Summary

The next improvements to the system prioritise making existing rules executable — git
for the source, vocabulary validation in `log-step.sh`, hook-driven logging, budgets,
harness-level git rails, a state tool, golden-run tests — over adding new instructional
text. Context reduction and parallelism follow once those exist.

## Context

The run log shows text rules being violated by the interpreter they rely on: steps logged
retroactively with zero duration, `outcome` values outside the enum, missing `flow:`,
a sub-agent killed by a spend limit, 26-hour runs. The instruction corpus is ≈76 000
words with 123 stop points; every added rule increases context cost and cross-reference
fragility without increasing compliance.

## Decisions

### Decision 1: Enforcement before elaboration

**What was decided:**
No new always-on rule is added until `specs/01`–`specs/06` are done, except to fix a
defect found by audit or retro. New behaviour is expressed first as a check, a hook, a
script, or a schema; prose explains it.

**Why:**
Compliance is the bottleneck, not specification.

**Alternatives:**
- Continue refining prose (more examples, stronger wording) — rejected: the log shows
  diminishing returns.
- Rewrite as a runtime (CLI orchestrator) — rejected: reverses ADR-0001 wholesale; the
  incremental path keeps portability.

**Consequences:**
Claude Code becomes the primary harness explicitly (hooks, deny-lists, sub-agents);
Codex and Windsurf receive the same prose but not the rails, and the documentation says
so.

**Related files:**
- `.ai/specs/README.md`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Order of the roadmap in `specs/README.md` is derived from this decision; reordering it
is a change to this ADR.

## Verification

None yet.
