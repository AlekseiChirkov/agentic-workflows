## Goal
Provide collection mode and evidence segments with observable, deterministic behavior.

## Context
- Dependencies: T-06d — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Enablement and disablement; AC-08, AC-17; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** collection mode and evidence segments, including all applicable requirements and negative cases in Enablement and disablement; AC-08, AC-17.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_status.py, tests/usage-collection-segments.py, scripts/usage-telemetry.py.

## Steps
1. Record collection enablement and disablement as owner-scoped segment boundaries.
2. Preserve previous evidence and delivery state when collection is disabled.
3. Represent discontinuity and re-enablement gaps without scanning historical storage.

## Acceptance Criteria
- Unset collection mode is off and re-enabling starts a distinct segment with a visible gap.
- Disabled or invalid mode preserves prior evidence and never publishes usage or invents missing data.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Unset collection mode is off and re-enabling starts a distinct segment with a visible gap. → the stated result is observed.
  - Disabled or invalid mode preserves prior evidence and never publishes usage or invents missing data. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
