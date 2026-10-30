## Goal
Integrate retrospective analysis into the complete telemetry contract.

## Context
- type: composite
- children: T-06a, T-06b, T-06e, T-06c, T-06d
- Dependencies: T-05b
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-06a fixed explicit retrospective corpus; T-06b versioned retrospective exports; T-06e comparable group statistics; T-06c independent acceptance and comparison; T-06d measured duration and interval coverage.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-fixed-corpus.py, scripts/usage-telemetry.py, tests/usage-report-exports.py, tests/usage-group-statistics.py, tests/usage-accepted-outcomes.py, tests/usage-duration-analysis.py, scripts/run-log-timing.py.

## Steps
See children: T-06a fixed explicit retrospective corpus; T-06b versioned retrospective exports; T-06e comparable group statistics; T-06c independent acceptance and comparison; T-06d measured duration and interval coverage.

## Acceptance Criteria
- A fixed corpus containing four complete values produces semantically equivalent JSON, CSV and Markdown with median 2.5 and p90 4.
- Independent acceptance and timing evidence remain scoped to the frozen corpus; a late correction or incompatible clocks cannot change the old report or produce an invented exclusive duration.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - A fixed corpus containing four complete values produces semantically equivalent JSON, CSV and Markdown with median 2.5 and p90 4. → the integrated outputs agree.
  - Independent acceptance and timing evidence remain scoped to the frozen corpus; a late correction or incompatible clocks cannot change the old report or produce an invented exclusive duration. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
