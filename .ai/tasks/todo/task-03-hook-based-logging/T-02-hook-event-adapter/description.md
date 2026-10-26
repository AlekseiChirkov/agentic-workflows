# Explicit hook dispatch and completion

## Goal
A hook adapter correlates dispatched checkpoints to Stop/SubagentStop observations without guessing runs, interpreting narrative outcomes or scanning history.

## Context
- Dependencies: T-01.
- Constraints: preserve validated nonblocking logging, explicit attribution and private active correlation; read the parent solution design.
- Reason: one coherent explicit hook dispatch and completion component with its own independently verifiable acceptance cluster.

## Scope
In scope: A hook adapter correlates dispatched checkpoints to Stop/SubagentStop observations without guessing runs, interpreting narrative outcomes or scanning history.

Out of scope: cost/token schemas, git protection hooks, broad harness migration, historical telemetry mutation, automatic merges. Other leaves own their named components.

Target files: hooks/log-step-hook.sh, tests/log-step-hook.sh, rules/run-log.md. Paths may be refined after inspecting existing patterns; report additions explicitly.

## Steps
1. Freeze adapter integration fixtures using isolated home, registry, active correlation and log roots.
2. Implement the resolved dispatch/report interface in the specification: executable start time, explicit run/session/dispatch-actor/checkpoint identity, expected skill and optional parent or waiting kind in private metadata. Bind the dispatch line to the native transcript; accept step names only from invocation records.
3. Implement registered-project gating and bounded Stop/SubagentStop JSON handling with exact structured outcome markers and invoked-skill transcript evidence.
4. Forward validated completed intervals through the producer receipt interface, deduplicate duplicate event types and reject late, ambiguous or inconsistent delivery without corrupting either run.
5. Handle single-session skill inference best-effort, permit unknown only with unambiguous correlation, and issue safe coverage warnings for missing dependencies or payloads.
6. Implement status and serialized fallback claims, freeze the first completion payload for identical retries, and prevent late hooks from adding an event after fallback. Run all adapter fixtures and document exact dispatch, marker, native payload and lifecycle contracts.

## Acceptance Criteria
- Given two concurrent runs in one project and interleaved Stop/SubagentStop payloads, explicit dispatch identities keep attribution correct and duplicate or stale deliveries cannot add duplicate events.
- Given missing or conflicting run/session/agent/checkpoint, outcome marker, start time or invoked-skill evidence, hook emits a safe coverage warning and never attributes a different run; inactive projects exit immediately.
- Given a single-session phase with explicit correlation, transcript skill evidence identifies observed skill boundaries best-effort, while genuinely unknown steps are labeled unknown and unobserved transitions remain uncovered.

- Given official native Stop/SubagentStop payload and Skill transcript shapes, executable fixtures consume those shapes; malformed or oversized JSON emits a bounded safe warning and never mutates a run. Unknown step requires a reliable run, outcome and start time.
- Given an accepted checkpoint, status returns its matching receipt and fallback cannot append another event. Given fallback first, a late hook cannot append; failed legacy persistence is never described as accepted.
- Given conflicting or duplicated marker keys, a dispatch line in the wrong transcript, or multiple eligible skill invocations, the adapter emits a coverage warning and preserves both runs.

## Test Plan
- Level: integration, contract
- Scenarios:
  - Given two concurrent runs in one project and interleaved Stop/SubagentStop payloads, explicit dispatch identities keep attribution correct and duplicate or stale deliveries cannot add duplicate events. → assert the stated observable result in isolated executable fixtures.
  - Given missing or conflicting run/session/agent/checkpoint, outcome marker, start time or invoked-skill evidence, hook emits a safe coverage warning and never attributes a different run; inactive projects exit immediately. → assert the stated observable result in isolated executable fixtures.
  - Given a single-session phase with explicit correlation, transcript skill evidence identifies observed skill boundaries best-effort, while genuinely unknown steps are labeled unknown and unobserved transitions remain uncovered. → assert the stated observable result in isolated executable fixtures.
- Edge cases: empty/null inputs, canonical count boundaries, duplicates, invalid transitions, missing dependencies, concurrent delivery, paths with spaces, permission failures, no-mutation on rejection.
- Native schema and bounded input scenarios: representative official payloads pass; malformed/oversized JSON and missing required correlation do not mutate accepted state.
