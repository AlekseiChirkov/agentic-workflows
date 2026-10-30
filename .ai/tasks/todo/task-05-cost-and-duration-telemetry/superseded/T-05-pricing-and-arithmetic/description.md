## Goal
Integrate pricing and arithmetic into the complete telemetry contract.

## Context
- type: composite
- children: T-05a, T-05b
- Dependencies: T-04e
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-05a price snapshot and scenario applicability; T-05b exact cost computation and completeness.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_pricing.py, tests/usage-price-applicability.py, tests/usage-exact-cost.py.

## Steps
See children: T-05a price snapshot and scenario applicability; T-05b exact cost computation and completeness.

## Acceptance Criteria
- Applicable price snapshots and exact arithmetic price the complete synthetic request at 0.00264.
- The specified unknown-cache-TTL fixture retains its priced 0.00224 subtotal without complete cost; a conflicting applicable rate leaves its affected component unpriced.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - Applicable price snapshots and exact arithmetic price the complete synthetic request at 0.00264. → the integrated outputs agree.
  - The specified unknown-cache-TTL fixture retains its priced 0.00224 subtotal without complete cost; a conflicting applicable rate leaves its affected component unpriced. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
