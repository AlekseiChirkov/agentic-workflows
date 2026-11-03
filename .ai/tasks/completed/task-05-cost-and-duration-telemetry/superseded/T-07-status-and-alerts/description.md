## Goal
Integrate status and alerts into the complete telemetry contract.

## Context
- type: composite
- children: T-07a, T-07b, T-07c, T-07d
- Dependencies: T-06d
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-07a collection mode and evidence segments; T-07b pure status and threshold episodes; T-07c duration warning eligibility; T-07d owner-controlled warning delivery.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_status.py, tests/usage-collection-segments.py, scripts/usage-telemetry.py, tests/usage-alert-status.py, tests/usage-duration-warnings.py, tests/usage-warning-delivery.py.

## Steps
See children: T-07a collection mode and evidence segments; T-07b pure status and threshold episodes; T-07c duration warning eligibility; T-07d owner-controlled warning delivery.

## Acceptance Criteria
- A time-only owner snapshot with collection off produces the eligible duration candidate and the owner delivers it idempotently.
- A repeated threshold crossing retains one episode across restart and an unavailable note destination remains pending without changing the collection segment.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - A time-only owner snapshot with collection off produces the eligible duration candidate and the owner delivers it idempotently. → the integrated outputs agree.
  - A repeated threshold crossing retains one episode across restart and an unavailable note destination remains pending without changing the collection segment. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
