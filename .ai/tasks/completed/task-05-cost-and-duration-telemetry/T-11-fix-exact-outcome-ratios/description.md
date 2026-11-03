## Goal
Preserve exact accepted-outcome ratios.

## Context
- Owner-authorized fresh validation finding in PR #61.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** preserve exact accepted-outcome ratios and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_outcomes.py, tests/usage-accepted-outcomes.py, tests/usage-outcome-tool-cost.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Long terminating cost ratios retain every exact digit, including the verified-empty experimental inventory report path.
- Nonterminating ratios, zero denominators, incomplete coverage and conditional semantics retain their explicit representations.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Long terminating cost ratios retain every exact digit, including the verified-empty experimental inventory report path. Verify the stated result through the relevant public boundary.
  - Nonterminating ratios, zero denominators, incomplete coverage and conditional semantics retain their explicit representations. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
