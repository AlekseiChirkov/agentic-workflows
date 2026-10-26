# ADR-0013: Decisions for Task 03 — Correlated hook logging

## Status

Provisional

## Date

2026-10-26

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

### Decision 3: Preserve exact user values with recoverable ownership transactions

**What was decided:**
Use a source-only Python standard-library installer behind a Bash entrypoint. Guard
Python 3.11 or newer before loading the engine. Preserve original JSON number tokens
while comparing handler/selector objects by exact mathematical JSON value. Track
inserted handler and created-group multiset quotas separately in an XDG sidecar.
Serialize operations and persist prepared previous/next ownership with settings
before/after digests before replacing settings. Recover only matching images; preserve
external edits and report unavailability otherwise. Project setup alone registers
canonical physical roots under its own lock and atomic replacement.

**Why:**
User configuration is not replaceable generated content. Identical unowned copies,
changed handlers and arbitrary numeric values must survive installation and removal.
A settings write and a separate ownership write cannot form one filesystem transaction.

**Alternatives:**
Whole-file settings replacement, binary-float JSON round trips, deleting all equal
handlers and an in-memory-only receipt lose user data or ownership after interruption.
A persistent service or database adds deployment dependencies without a current need.

**Consequences:**
Installation additionally requires native jq/flock availability; saved-state removal
requires only supported Python and works after the former source disappears. Prepared
recovery is explicit and does not claim cross-file power-loss durability. Registry
mutation remains separate from hook installation and deployment.

**Related files:**
- `scripts/install-hooks.sh`
- `scripts/install-hooks.py`
- `scripts/setup-new-project.sh`
- `harness/claude/hooks.json`
- `tests/hook-install.sh`

### Decision 4: Retain one delivery route and the existing workflow return points

**What was decided:**
After issuing a dispatch envelope, permit only matching receipt-confirmed suppression
or the adapter's serialized fallback/native retry routes. Pending fallback may attempt
once; delivering retains its frozen correlated payload; fallback states permit no
second route. Unknown resume knowledge never proves that no envelope existed.
Provisionally wire only the existing test-definition RED return for named coverage,
requiring a unique native Skill invocation and canonical final report. Keep current
workers, batches, git checkpoints and synthetic summaries intact.

**Why:**
Exit zero is deliberately not persistence acknowledgment. A second ordinary write
after uncertain correlated delivery can duplicate an event. Generic Stop events do
not establish completion of every internal skill.

**Alternatives:**
Unconditional direct fallback, status polling, fabricated native retry events and
restructuring batches to manufacture precision either risk duplicates or change the
workflow for telemetry. These options were rejected.

**Consequences:**
Unobserved boundaries retain prompt logging and exact approximation labels. A
test-level-none path has no RED coverage; GREEN and validation batches remain
approximate. Synthetic fixtures establish routing composition, not live model
compliance or live event firing.

**Related files:**
- `rules/run-log.md`
- `rules/orchestration.md`
- `workflows/spec-run.md`
- `tests/hook-workflow-contract.sh`

### Decision 5: Analyze exact intervals only after verified snapshot eligibility

**What was decided:**
Provide an explicit-file Bash CLI with a typed Python 3.11+ standard-library engine.
Copy selected files privately without changing bytes, run the existing producer lint
once against that snapshot, and verify complete file/physical-line diagnostics before
arithmetic. Read the exported contract instead of copying field vocabulary. Preserve
exact numeric input and use integer half-open intervals, decimal-string totals and
exact ratio pairs. Distinguish inclusive spans, exclusive work, unions, gaps, explicit
waiting and distinct-actor parallel overlap. Reject ambiguous boundaries and run
identity rather than selecting a convenient copy.

**Why:**
Legacy elapsed writes are approximate and overlapping span totals are not wall or
CPU time. Re-serialized floating-point records and unverified lint coverage can
produce plausible but incorrect measurements.

**Alternatives:**
Summing all spans into elapsed time, inferring waiting from gaps, deriving parents
from sequence, merging distinct run files and treating unavailable data as zero were
rejected. A second producer validator would drift from the canonical contract.

**Consequences:**
Graph-invalid components lose exclusive metrics while disconnected valid components
remain usable. Negative-only dependency evidence cannot create measured groups.
Opaque graph coverage and incomplete actor/step totals are null; raw eligible unions
can remain disclosed partial observations. The helper reads explicitly selected
snapshots only and never repairs history. Native hooks and ordinary producer writes
retain their existing Bash dependencies.

**Related files:**
- `scripts/run-log-timing.sh`
- `scripts/run-log-timing.py`
- `workflows/retro.md`
- `tests/hook-timing.sh`

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
