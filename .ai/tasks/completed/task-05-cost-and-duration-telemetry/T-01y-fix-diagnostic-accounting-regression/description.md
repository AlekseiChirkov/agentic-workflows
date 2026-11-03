## Goal
Pin diagnostic isolation from paid accounting.

## Context
- Owner-authorized fresh validation finding in PR #55.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** pin diagnostic isolation from paid accounting and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** tests/usage-resolution-integration.py.

## Steps
1. Add an integrated characterization regression for the already correct accounting behavior.
2. Run the regression before any production edit and retain the passing behavioral baseline.
3. Verify the test observes identities and exact accounting through the resolver; commit only the test coverage.

## Acceptance Criteria
- Adding a valid independent diagnostic preserves observation content identities, paid response identities/counts, token totals and exact costs.
- A repeated diagnostic event remains nonbillable and the test observes integrated resolver behavior.

## Test Plan
- **Level:** integration (characterization; no production behavior change)
- **Scenarios:**
  - Adding a valid independent diagnostic preserves observation content identities, paid response identities/counts, token totals and exact costs. Verify the stated result through the relevant public boundary.
  - A repeated diagnostic event remains nonbillable and the test observes integrated resolver behavior. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
