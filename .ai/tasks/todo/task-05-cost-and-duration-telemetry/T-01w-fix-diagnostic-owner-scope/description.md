## Goal
Bind snapshot diagnostic records to the owner scope.

## Context
- Owner-authorized fresh validation finding in PR #52.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** bind snapshot diagnostic records to the owner scope and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-current-run-snapshot-schema.py, tests/usage-status-parts-cli.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Same-owner diagnostic records validate and foreign-owner records are rejected in embedded and materialized bundles.
- Receipt binding and legitimate sub-scope rules remain intact.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Same-owner diagnostic records validate and foreign-owner records are rejected in embedded and materialized bundles. Verify the stated result through the relevant public boundary.
  - Receipt binding and legitimate sub-scope rules remain intact. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
