## Goal
Provide independent acceptance and comparison with observable, deterministic behavior.

## Context
- Dependencies: T-06e — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Cost of independently accepted outcomes; AC-07, AC-19; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** independent acceptance and comparison, including all applicable requirements and negative cases in Cost of independently accepted outcomes; AC-07, AC-19.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-accepted-outcomes.py, scripts/usage-telemetry.py.

## Steps
1. Group resumed attempts by stable outcome opportunity and validate independent acceptance revisions.
2. Calculate observed workload per accepted opportunity with explicit incomplete coverage.
3. Guard comparison conclusions on task, quality, coverage and pricing comparability.

## Acceptance Criteria
- Failed 0.4, accepted resumed 0.6, rejected 0.3 and incomplete 0.2 produce three opportunities, one accepted and observed 1.5.
- No independent acceptance makes the ratio unavailable, and incomparable tasks or price bases produce no winner.

- Independent experimental evaluation is separate from production verification and included once in an optional combined total; a late defect label changes only a new report revision.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Failed 0.4, accepted resumed 0.6, rejected 0.3 and incomplete 0.2 produce three opportunities, one accepted and observed 1.5. → the stated result is observed.
  - No independent acceptance makes the ratio unavailable, and incomparable tasks or price bases produce no winner. → the stated result is observed.
  - Independent experimental evaluation is separate from production verification and included once in an optional combined total; a late defect label changes only a new report revision. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
