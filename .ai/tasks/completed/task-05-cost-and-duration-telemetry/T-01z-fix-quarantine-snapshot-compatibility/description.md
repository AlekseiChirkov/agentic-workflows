## Goal
Preserve valid scope-free quarantine diagnostics while enforcing scoped diagnostic ownership.

## Context
- Independent recheck of the snapshot owner repair found a regression for source_issue records, which have source binding but no scope field.
- The owner authorized all necessary corrections and independent rechecks.

## Scope
- **In scope:** snapshot dispatch for diagnostic variants, source binding, receipts and focused regressions.
- **Out of scope:** unrelated warning behavior, schema redesign and historical evidence changes.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-current-run-snapshot-schema.py, tests/usage-status-parts-cli.py.

## Steps
1. Add a behavioral regression for a valid receipt-bound snapshot containing a scope-free source_issue and observe the expected failure.
2. Restrict owner-scope checks to the diagnostic variant that declares scope, retaining source binding checks for quarantined records.
3. Verify valid and invalid quarantine records, foreign scoped diagnostics, selected parts and neighboring suites without weakening earlier tests.

## Acceptance Criteria
- Valid source_issue quarantine records remain accepted with correct source binding and receipt.
- Foreign diagnostic_measurement scopes remain rejected in embedded and selected-part snapshots; invalid quarantine source bindings remain rejected.

## Test Plan
- **Level:** integration, contract
- **Scenarios:** valid source_issue before and after repair; invalid source binding; same and foreign diagnostic owner scopes; selected-part materialization.
- **Edge cases:** absent scope by schema, exact receipt rebinding, empty diagnostics and mixed diagnostic variants.
