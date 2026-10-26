# ADR-0013: Decisions for Task 03 — Correlated hook logging

## Status

Provisional

## Date

2026-10-22

## Related Task

- Task: [Hook-based logging](../tasks/todo/task-03-hook-based-logging/state.md).
- Related files: `scripts/log-step.sh:554`, `workflows/spec-run.md:169`, `scripts/sync.sh:70`.

## Summary

Add an explicitly correlated hook adapter and interval-aware producer contract while preserving approximate prompt logging for unobserved boundaries.

## Context

The producer currently measures time since the previous accepted write. Batched sub-agent checkpoints do not coincide with every workflow step. The selected specification requires deterministic attribution, duplicate handling, user-owned settings preservation and honest nested timing without reading history during production.

## Decisions

### Decision 1: Extend the producer and isolate active correlation

**What was decided:**
Use executable clock stamps and explicit run/session/agent/checkpoint identity, optional parent/waiting semantics, serialized accepted-event metadata and an acceptance receipt. Keep correlation state separate from historical logs. Extend the existing Bash producer and shared validation contract additively.

**Why:**
Forwarding ordinary completion calls cannot distinguish concurrent or overlapping work, and exit zero intentionally does not imply persistence.

**Alternatives:**
Newest-active-run selection can cross-attribute concurrent runs. Narrative outcome inference fabricates results. A separate service adds deployment and runtime complexity without solving a further current requirement.

**Consequences:**
Hook-only dependencies may be unavailable without blocking work. Legacy prompt calls retain their existing behavior. Ordinary duplicate delivery is serialized; partial filesystem write limitations are disclosed rather than claiming crash-proof exactly-once behavior.

**Related files:**
- `scripts/log-step.sh`
- `hooks/log-step-hook.sh`
- `rules/run-log.md`

### Decision 2: Gate by demonstrated coverage and install only owned entries

**What was decided:**
Install user-level Stop/SubagentStop hooks only through manifest-owned merges, activate registered projects, declare hook capabilities independently of coverage, and retain approximate prompt logging for unobserved skill boundaries. Add only the minimal harness scaffold required by this selected task; preserve current deployment targets.

**Why:**
Stop is an answer boundary, not a universal step boundary. The full harness migration is a separate task; the selected specification and existing decisions already determine the narrow prerequisite interfaces.

**Alternatives:**
Removing every prompt after detecting hooks loses internal steps. Project-level installation leaks user configuration into consumer repositories. Completing the full harness migration here exceeds the selected specification.

**Consequences:**
This run makes a narrow roadmap-order exception to ADR-0009 Decision 7 without claiming the wider migration complete. Run boundaries stay prompt-driven. Retrospective timing distinguishes wall coverage, gaps, overlap, waiting and inclusive/exclusive worker spans rather than CPU work.

**Related files:**
- `harness/claude/hooks.json`
- `scripts/sync.sh`
- `workflows/spec-run.md`
- `workflows/retro.md`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

Newest-run inference, narrative outcomes, wholesale prompt removal, project-level hooks, a persistent event daemon and broad harness retirement.

## Implications for Future Work

The full harness migration and usage/cost normalization remain separate. Keep explicit identity, receipt and denominator contracts compatible with old logs and unavailable hook dependencies.

## Verification

Not yet verified — decision recorded before implementation completed.

## References

- Task: hook-based logging.
- Pull request: pending.
- Related documents: run-log contract, current logging decisions, roadmap decisions on user hooks and capabilities.
