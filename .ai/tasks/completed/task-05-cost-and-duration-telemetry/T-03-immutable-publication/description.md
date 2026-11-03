## Goal
Immutable publication and lifecycle projection: deliver and independently validate the complete capability.

## Context
- Dependencies: T-02.
- Constraints: Preserve explicit scope, bounded offline inputs, independently verified provenance, exact arithmetic, immutable accepted evidence and existing nonblocking lifecycle behavior.
- Reason: The user requested fewer work items grouped around integrated capabilities; the original independently testable clusters remain explicit below.
- Previous descriptions and progress are preserved in `../superseded/`.

Off-limits: Paid model calls, implicit historical discovery, automatic model or policy changes, invented evidence, rewriting accepted events or unrelated behavior.

## Scope
- **In scope:** Authorize the selected scope and provenance; publish immutable bundles without changing lifecycle state; integrate first-acceptance projections and exact replay; independently test active and explicitly authorized late imports.
- **Out of scope:** Changes outside the specification and its compatibility requirements.
- **Target files:** Determine from the preserved original descriptions and integrated implementation before modifying code.

## Steps
1. Reconcile existing branches, tests and independently reviewed work with the current main-based stack.
2. Implement the integrated capability and resolve the open defects without discarding existing evidence.
3. Execute the original acceptance scenarios below and independent cross-component review.
4. Integrate reviewed changes in dependency order and update task state.

## Acceptance Criteria

### T-03
- A validated published bundle and a matching self-contained projection retain the same contributing identities and exact values on first acceptance.
- A duplicate bundle or replay does not change lifecycle bytes, while an invalid projection produces neither lifecycle mutation nor a false receipt.

### T-03a
- Shared publication verifies the selected profile, owner scope and authorized provenance of sanitized IDs and evidence; a digest-shaped string alone cannot prove that its content is safe or originates from the selected source.
- Concurrent exact publications yield one content-addressed file and a receipt only after complete installation.
- Corrupt existing content, path substitution and failed installation yield no false receipt or lifecycle mutation.

- Collection is off when the mode is unset or invalid; disabled or unregistered scope produces no publication or acceptance receipt.

### T-03b
- A complete self-contained projection agrees exactly with its cost scalar and preserves the original payload on checkpoint replay.
- Invalid projections and mismatched scalars leave lifecycle bytes, sequence, clock and active state unchanged.

- A self-contained 0.00264 fixture is independently validated against its evidence and cannot be represented by canonical zero.

## Test Plan

### T-03
- **Level:** integration, contract
- **Scenarios:**
  - A validated published bundle and a matching self-contained projection retain the same contributing identities and exact values on first acceptance. → the integrated outputs agree.
  - A duplicate bundle or replay does not change lifecycle bytes, while an invalid projection produces neither lifecycle mutation nor a false receipt. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-03a
- **Level:** unit, integration
- **Scenarios:**
  - Submit a bundle with digest-shaped IDs but absent or unauthorized provenance → reject without publication or a receipt; accept a matching explicitly authorized synthetic bundle.
  - Concurrent exact publications yield one content-addressed file and a receipt only after complete installation. → the stated result is observed.
  - Corrupt existing content, path substitution and failed installation yield no false receipt or lifecycle mutation. → the stated result is observed.
  - Collection is off when the mode is unset or invalid; disabled or unregistered scope produces no publication or acceptance receipt. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-03b
- **Level:** unit, integration
- **Scenarios:**
  - A complete self-contained projection agrees exactly with its cost scalar and preserves the original payload on checkpoint replay. → the stated result is observed.
  - Invalid projections and mismatched scalars leave lifecycle bytes, sequence, clock and active state unchanged. → the stated result is observed.
  - A self-contained 0.00264 fixture is independently validated against its evidence and cannot be represented by canonical zero. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
