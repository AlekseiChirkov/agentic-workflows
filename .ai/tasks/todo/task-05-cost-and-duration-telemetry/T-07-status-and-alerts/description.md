## Goal
Current status and warning delivery: deliver and independently validate the complete capability.

## Context
- Dependencies: T-04, T-06.
- Constraints: Preserve explicit scope, bounded offline inputs, independently verified provenance, exact arithmetic, immutable accepted evidence and existing nonblocking lifecycle behavior.
- Reason: The user requested fewer work items grouped around integrated capabilities; the original independently testable clusters remain explicit below.
- Previous descriptions and progress are preserved in `../superseded/`.

Off-limits: Paid model calls, implicit historical discovery, automatic model or policy changes, invented evidence, rewriting accepted events or unrelated behavior.

## Scope
- **In scope:** Preserve collection segments; compute pure deterministic status and thresholds; deliver and recover warnings through the authorized owner.
- **Out of scope:** Changes outside the specification and its compatibility requirements.
- **Target files:** Determine from the preserved original descriptions and integrated implementation before modifying code.

## Steps
1. Reconcile existing branches, tests and independently reviewed work with the current main-based stack.
2. Implement the integrated capability and resolve the open defects without discarding existing evidence.
3. Execute the original acceptance scenarios below and independent cross-component review.
4. Integrate reviewed changes in dependency order and update task state.

## Acceptance Criteria

### T-07
- A time-only owner snapshot with collection off produces the eligible duration candidate and the owner delivers it idempotently.
- A repeated threshold crossing retains one episode across restart and an unavailable note destination remains pending without changing the collection segment.

### T-07a
- Unset collection mode is off and re-enabling starts a distinct segment with a visible gap.
- Disabled or invalid mode preserves prior evidence and never publishes usage or invents missing data.

### T-07b
- Repeated status on the same input returns the same pending alert identity and proposed state without writing the input.
- Equality does not cross a threshold; unknown values do not reset an episode and expired policy produces no token or money alert.

- Out-of-range completeness policy is rejected; a proven lower bound can cross a threshold, and only an observed non-crossing resets an episode while corrections preserve prior alerts.

### T-07c
- With fewer than five eligible samples, 7200 seconds does not warn and a larger measured duration does.
- With five eligible samples, a warning requires exceeding both 7200 seconds and three medians; incompatible exports use the fallback.

- A time-only snapshot can warn with collection off; a missing clock is unavailable, and expired exports or candidate-only samples do not establish a historical threshold.

### T-07d
- A pending warning survives interruption and retry applies one idempotent note under the same identifier.
- An unavailable note destination stays pending for the report and collection disablement does not erase delivery state.

- The authorized orchestrator atomically accepts the status-proposed revision, persists pending then confirmed delivery, recovers between those boundaries, and writes the warning only to the matching leaf or run notes and final report.

## Test Plan

### T-07
- **Level:** integration, contract
- **Scenarios:**
  - A time-only owner snapshot with collection off produces the eligible duration candidate and the owner delivers it idempotently. → the integrated outputs agree.
  - A repeated threshold crossing retains one episode across restart and an unavailable note destination remains pending without changing the collection segment. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-07a
- **Level:** unit, integration
- **Scenarios:**
  - Unset collection mode is off and re-enabling starts a distinct segment with a visible gap. → the stated result is observed.
  - Disabled or invalid mode preserves prior evidence and never publishes usage or invents missing data. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-07b
- **Level:** unit, integration
- **Scenarios:**
  - Repeated status on the same input returns the same pending alert identity and proposed state without writing the input. → the stated result is observed.
  - Equality does not cross a threshold; unknown values do not reset an episode and expired policy produces no token or money alert. → the stated result is observed.
  - Out-of-range completeness policy is rejected; a proven lower bound can cross a threshold, and only an observed non-crossing resets an episode while corrections preserve prior alerts. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-07c
- **Level:** unit, integration
- **Scenarios:**
  - With fewer than five eligible samples, 7200 seconds does not warn and a larger measured duration does. → the stated result is observed.
  - With five eligible samples, a warning requires exceeding both 7200 seconds and three medians; incompatible exports use the fallback. → the stated result is observed.
  - A time-only snapshot can warn with collection off; a missing clock is unavailable, and expired exports or candidate-only samples do not establish a historical threshold. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-07d
- **Level:** unit, integration
- **Scenarios:**
  - A pending warning survives interruption and retry applies one idempotent note under the same identifier. → the stated result is observed.
  - An unavailable note destination stays pending for the report and collection disablement does not erase delivery state. → the stated result is observed.
  - The authorized orchestrator atomically accepts the status-proposed revision, persists pending then confirmed delivery, recovers between those boundaries, and writes the warning only to the matching leaf or run notes and final report. → the integrated boundary produces the stated result.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
