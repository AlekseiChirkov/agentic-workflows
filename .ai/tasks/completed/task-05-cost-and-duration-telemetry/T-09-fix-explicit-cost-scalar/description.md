## Goal
Reject malformed explicit lifecycle cost scalars.

## Context
- Owner-authorized fresh validation finding in PR #59.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** reject malformed explicit lifecycle cost scalars and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/log-step.sh, scripts/usage_telemetry_ingest.py, tests/usage-lifecycle-projection.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Explicit --cost-usd - is rejected without a receipt or changes to lifecycle bytes, sequence, clock or active metadata.
- Omitted cost, valid exact cost, replay behavior and nonblocking legacy operation remain supported.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Explicit --cost-usd - is rejected without a receipt or changes to lifecycle bytes, sequence, clock or active metadata. Verify the stated result through the relevant public boundary.
  - Omitted cost, valid exact cost, replay behavior and nonblocking legacy operation remain supported. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
