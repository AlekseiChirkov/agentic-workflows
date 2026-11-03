## Goal
Retain conditional pricing semantics in warnings.

## Context
- Owner-authorized fresh validation finding in PR #62.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** retain conditional pricing semantics in warnings and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_alerts.py, tests/usage-status-cli-integration.py, tests/usage-status-scope-evidence.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Conditional repricing cannot become a factual owner or scoped spend threshold or lower bound.
- Historical supported amounts still warn correctly; hypothetical-only crossings remain excluded or explicitly conditional through delivery.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Conditional repricing cannot become a factual owner or scoped spend threshold or lower bound. Verify the stated result through the relevant public boundary.
  - Historical supported amounts still warn correctly; hypothetical-only crossings remain excluded or explicitly conditional through delivery. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
