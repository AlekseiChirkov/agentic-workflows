# Validated correlated event writes

## Goal
Add optional hook identity and clock-stamped interval fields to the existing producer, with serialized idempotent acceptance receipts and backward-compatible lint.

## Context
- Dependencies: None.
- Constraints: preserve validated nonblocking logging, explicit attribution and private active correlation; read the parent solution design.
- Reason: one coherent validated correlated event writes component with its own independently verifiable acceptance cluster.

## Scope
In scope: Add optional hook identity and clock-stamped interval fields to the existing producer, with serialized idempotent acceptance receipts and backward-compatible lint.

Out of scope: cost/token schemas, git protection hooks, broad harness migration, historical telemetry mutation, automatic merges. Other leaves own their named components.

Target files: scripts/log-step.sh, rules/run-log.md, tests/log-step.sh, scripts/validate-contracts.sh. Paths may be refined after inspecting existing patterns; report additions explicitly.

## Steps
1. Freeze producer regressions for explicit identity, interval validation, duplicate and out-of-order acceptance, legacy calls, and unchanged state on invalid input.
2. Extend the existing effective producer contract with optional correlation and explicit interval fields, defining the exact CLI and receipt interface for downstream consumers.
3. Serialize writes to each explicitly selected run, validate checkpoint identities before mutation, and persist accepted-delivery metadata without scanning history.
4. Extend read-only lint and canonical contract documentation for additive fields while preserving old events and optional-jq legacy writes.
5. Run focused producer regressions and the canonical contract gate, recording the exact interface and any partial-I/O guarantee limitations; update the bidirectional drift gate in the same leaf.

## Acceptance Criteria
- Given interleaved explicit identities for two runs, each accepted event belongs only to its selected run and duplicate checkpoint delivery appends at most one accepted event.
- Given malformed or incomplete hook metadata or invalid intervals, invocation warns safely, exits zero and leaves accepted sequence/timestamps/correlation state unchanged.
- Given ordinary legacy producer calls and old historical events, current behavior and read-only lint remain compatible; hook acceptance has an explicit receipt rather than relying on exit zero.

- Given a transient producer persistence failure, no accepted receipt is issued and retry can persist exactly one event rather than silently losing the checkpoint.

## Test Plan
- Level: integration, contract
- Scenarios:
  - Given interleaved explicit identities for two runs, each accepted event belongs only to its selected run and duplicate checkpoint delivery appends at most one accepted event. → assert the stated observable result in isolated executable fixtures.
  - Given malformed or incomplete hook metadata or invalid intervals, invocation warns safely, exits zero and leaves accepted sequence/timestamps/correlation state unchanged. → assert the stated observable result in isolated executable fixtures.
  - Given ordinary legacy producer calls and old historical events, current behavior and read-only lint remain compatible; hook acceptance has an explicit receipt rather than relying on exit zero. → assert the stated observable result in isolated executable fixtures.
- Edge cases: empty/null inputs, canonical count boundaries, duplicates, invalid transitions, missing dependencies, concurrent delivery, paths with spaces, permission failures, no-mutation on rejection.
- Receipt retry scenario: fail persistence before acceptance, assert no receipt, restore storage and assert one accepted retry.
