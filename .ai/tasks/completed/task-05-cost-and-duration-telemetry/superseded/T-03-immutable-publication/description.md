## Goal
Integrate immutable publication into the complete telemetry contract.

## Context
- type: composite
- children: T-03a, T-03b
- Dependencies: T-02b
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-03a immutable usage bundle publication; T-03b validated lifecycle usage projection.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_publication.py, tests/usage-usage-publication.py, scripts/log-step.sh, tests/usage-lifecycle-projection.py.

## Steps
See children: T-03a immutable usage bundle publication; T-03b validated lifecycle usage projection.

## Acceptance Criteria
- A validated published bundle and a matching self-contained projection retain the same contributing identities and exact values on first acceptance.
- A duplicate bundle or replay does not change lifecycle bytes, while an invalid projection produces neither lifecycle mutation nor a false receipt.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - A validated published bundle and a matching self-contained projection retain the same contributing identities and exact values on first acceptance. → the integrated outputs agree.
  - A duplicate bundle or replay does not change lifecycle bytes, while an invalid projection produces neither lifecycle mutation nor a false receipt. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
