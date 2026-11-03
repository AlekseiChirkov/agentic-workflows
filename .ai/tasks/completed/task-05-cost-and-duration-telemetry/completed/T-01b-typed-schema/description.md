## Goal
Validate typed usage measurements without conflating unknown values with zero.

## Context
- Dependencies: T-01a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections on missing values and counter normalization; preserve evidenced values and typed reasons.
- Reason: Measurement validation has a distinct independently testable output.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** Measurement states, numeric values, typed reasons and evidence of zero.
- **Out of scope:** Observation and bundle envelopes, other entity schemas and producer contract export.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-typed-schema.py, scripts/validate-contracts.sh.

## Steps
1. Define measurement states and their allowed values in accordance with the specification.
2. Validate numeric values, typed reasons and evidence without manufacturing a zero.
3. Test positive controls and invalid state, type and boundary combinations through the offline test command.

## Acceptance Criteria
- A known, evidenced zero remains numeric zero; an unavailable value has an explicit reason and no numeric field.
- Boolean, negative, fractional and above-limit counters and unavailable values represented by zero, an empty string or a placeholder are rejected.

## Test Plan
- **Level:** unit
- **Scenarios:**
  - Validate evidenced zero and unavailable measurement → preserve the former and omit the latter value with its reason.
  - Validate invalid numeric types and unavailable placeholders → reject each without accepting an invalid measurement.
- **Edge cases:** all four states, empty reasons, boundary counters, duplicate keys and valid positive controls.
