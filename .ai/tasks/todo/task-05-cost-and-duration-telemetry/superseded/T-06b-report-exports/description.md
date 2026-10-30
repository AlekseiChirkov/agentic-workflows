## Goal
Provide versioned retrospective exports with observable, deterministic behavior.

## Context
- Dependencies: T-06a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Export content; AC-18, AC-20; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** versioned retrospective exports, including all applicable requirements and negative cases in Export content; AC-18, AC-20.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-report-exports.py, scripts/usage-telemetry.py.

## Steps
1. Define equivalent versioned report data for JSON, CSV and Markdown renderers.
2. Render exact machine numbers, scope, contributors, exclusions and completeness consistently.
3. Publish complete report artifacts without silently overwriting different prior revisions.

## Acceptance Criteria
- JSON, CSV and Markdown exports represent the same semantic totals and preserve exact numbers in machine output.
- CSV preserves exact decimal values as text and excluded observations are identified consistently across formats.
- Machine exports encode all derived sums as canonical decimal strings, including sums within the safe JSON integer range.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - JSON, CSV and Markdown exports represent the same semantic totals and preserve exact numbers in machine output. → the stated result is observed.
  - CSV preserves exact decimal values as text and excluded observations are identified consistently across formats. → the stated result is observed.
  - Small and large derived sums are exported as canonical decimal strings without rounding.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
