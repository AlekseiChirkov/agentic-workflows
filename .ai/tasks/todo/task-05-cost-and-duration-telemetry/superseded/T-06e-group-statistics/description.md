## Goal
Calculate deterministic statistics for comparable retrospective groups.

## Context
- Dependencies: T-06b — the report representation carries the computed group statistics.
- Constraints: Follow the specification export content and acceptance criterion 18; keep exact values and coverage classes separate.
- Reason: Statistics have an independently testable result separate from format rendering.

Off-limits: Paid calls, implicit history discovery and comparisons of incomplete groups as winners.

## Scope
- **In scope:** Median, nearest-rank p90, sample size and small-sample indication for eligible groups.
- **Out of scope:** Corpus selection, report rendering and acceptance decisions.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-group-statistics.py.

## Steps
1. Select comparable eligible observations and separate complete, partial and unavailable groups.
2. Calculate exact median and nearest-rank p90 without losing decimal precision.
3. Mark groups with fewer than five observations and return unavailable statistics for empty groups.

## Acceptance Criteria
- Values 1, 2, 3, 4 yield n=4, median 2.5, p90=4 and a small-sample marker.
- An empty group has unavailable statistics and partial values do not enter a complete-value distribution.

## Test Plan
- **Level:** unit
- **Scenarios:**
  - Calculate the four-value group → n=4, median 2.5, p90=4, small-sample marker.
  - Calculate empty and mixed-completeness groups → unavailable empty statistics and separated distributions.
- **Edge cases:** empty groups, ties, even and odd sample sizes, input permutations and exact decimal values.
