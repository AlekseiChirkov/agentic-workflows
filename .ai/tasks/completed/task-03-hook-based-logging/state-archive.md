# state-archive — task-03-hook-based-logging

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Record reliable workflow completion timestamps through user-level hooks with explicit attribution, safe fallback, and honest timing coverage, preserving the existing logging validation contract.

### Affected Parts
The run-log producer and lint contract, hook adapter, user-level hook installation, minimal capability and project registry scaffold, orchestrator logging instructions, and retrospective timing analysis.

### Codebase Analysis
Files read: 2/12 (2 entry-points, 0 deeper).
- scripts/log-step.sh: read because hook correlation, deduplication and explicit timing interfaces are not described in the current architecture. Existing durations are time since the previous write and cannot represent nested spans.
- scripts/sync.sh: read because manifest-owned user hook merge and registry integration are not described in the current architecture. Existing deployment targets must be preserved.
No hook adapter or harness directory exists. Existing isolated Bash fixtures and the shared runtime vocabulary are the compatibility baseline. Current session exposes sub-agent spawning and messaging; historical harness-name prohibitions are stale.

### Open Questions
None. The Arbiter found the required minimal scaffold determined by existing decisions and the selected specification.


## Archived Solution Design — Variants
1. Prompt-only completion logging: simplest deployment but cannot provide deterministic observation or explicit spans.
2. Additive Bash/jq adapter plus validated producer extension: dispatch captures identity and start time, stop delivery validates a structured marker and invoked skill, the producer serializes accepted checkpoints, and retro computes span coverage.
3. Full event daemon and harness migration: broader automatic instrumentation but introduces a new service and unrelated deployment changes.


## Archived Solution Design — Rejected
Prompt-only cannot meet the requested deterministic boundaries. A daemon and full harness migration add runtime and product scope not needed for this specification.
