## Goal
Export the additive telemetry schema through the existing producer contract.

## Context
- Dependencies: T-01s completes the shared schema registry before export.
- Constraints: Keep existing lifecycle vocabulary and producer exit-zero behavior; preserve operation without optional Python and jq where previously supported.
- Reason: Producer-facing export and compatibility are independently testable from individual schemas.

Off-limits: Usage publication, lifecycle event mutation and independent duplicate schema definitions.

## Scope
- **In scope:** Export of the canonical telemetry schema and reasons from the existing producer contract with backwards compatibility.
- **Out of scope:** Source adapters, publication and telemetry calculations.
- **Target files:** scripts/log-step.sh, scripts/usage_telemetry_contract.py, rules/run-log.md, tests/usage-contract-export.py, scripts/validate-contracts.sh.

## Steps
1. Connect the existing contract command to the shared versioned telemetry schema without changing lifecycle event meanings.
2. Define a conservative unavailable path when optional dependencies are absent and retain existing producer behavior.
3. Check parity between exported definitions and validators and verify legacy contract consumers and no-jq operation.

## Acceptance Criteria
- Producer contract output exposes the shared versioned telemetry definitions and reason vocabulary without changing existing lifecycle entries.
- With optional dependencies unavailable, existing producer operations retain their prior nonblocking behavior and telemetry availability is not falsely asserted.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - Compare producer export against the shared registry and previous lifecycle contract → telemetry matches and legacy entries remain unchanged.
  - Run existing operations without optional dependencies → old behavior remains available without a false usage receipt.
- **Edge cases:** missing Python, missing jq, malformed registry, unknown versions and older consumers.
