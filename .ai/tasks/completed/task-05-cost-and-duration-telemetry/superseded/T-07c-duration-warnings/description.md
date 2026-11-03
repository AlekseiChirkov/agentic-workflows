## Goal
Provide duration warning eligibility with observable, deterministic behavior.

## Context
- Dependencies: T-07b — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Duration rule; AC-06; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** duration warning eligibility, including all applicable requirements and negative cases in Duration rule; AC-06.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_status.py, tests/usage-duration-warnings.py, scripts/usage-telemetry.py.

## Steps
1. Validate the closed measured interval and explicitly supplied compatible historical threshold export.
2. Exclude the candidate and ineligible observations from historical groups.
3. Apply strict two-hour and three-median boundaries, including the documented fallback.

## Acceptance Criteria
- With fewer than five eligible samples, 7200 seconds does not warn and a larger measured duration does.
- With five eligible samples, a warning requires exceeding both 7200 seconds and three medians; incompatible exports use the fallback.

- A time-only snapshot can warn with collection off; a missing clock is unavailable, and expired exports or candidate-only samples do not establish a historical threshold.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - With fewer than five eligible samples, 7200 seconds does not warn and a larger measured duration does. → the stated result is observed.
  - With five eligible samples, a warning requires exceeding both 7200 seconds and three medians; incompatible exports use the fallback. → the stated result is observed.
  - A time-only snapshot can warn with collection off; a missing clock is unavailable, and expired exports or candidate-only samples do not establish a historical threshold. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
