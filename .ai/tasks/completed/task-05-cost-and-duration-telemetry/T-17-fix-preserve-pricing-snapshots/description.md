## Goal
Preserve selected price snapshots while evaluating partial and complete response groups.

## Context
- Independent recheck found a local observation snapshot list overwrites the pricing input parameter.
- A mixed partial and final response corpus must remain analyzable.

## Scope
- **In scope:** the colliding local binding and mixed-response regression coverage.
- **Out of scope:** pricing formula, schema, ownership and revision policy changes.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-resolution-revisions.py.

## Steps
1. Reproduce the price lookup failure with mixed partial and final response groups.
2. Rename the observation-local binding without changing selection or price inputs.
3. Verify the mixed case, corrections, active conflicts and neighboring resolution suites.

## Acceptance Criteria
- A partial response followed by a complete response resolves without overwriting selected price inputs.
- Partial and complete response accounting, active conflicts, verified corrections and exact pricing retain their semantics.

## Test Plan
- **Level:** integration
- **Scenarios:** partial then final and relevant order permutations; preserved valid correction; unresolved conflict.
- **Edge cases:** multiple response groups, partial finality and exact price evidence.
