## Goal
Accept general JSON discriminator values in canonical primitives.

## Context
- Owner-authorized fresh validation finding in PR #39.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** accept general json discriminator values in canonical primitives and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-canonical-encoding.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Array and object kind values canonicalize and hash as ordinary valid JSON without TypeError.
- Valid envelope schema ordering and invalid envelope validation retain their behavior.

## Test Plan
- **Level:** unit, contract
- **Scenarios:**
  - Array and object kind values canonicalize and hash as ordinary valid JSON without TypeError. Verify the stated result through the relevant public boundary.
  - Valid envelope schema ordering and invalid envelope validation retain their behavior. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
