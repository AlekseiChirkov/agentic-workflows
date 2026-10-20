## Goal
Document the exact run-log contract and make the repository contract gate detect any drift between its runtime definitions and canonical tables.

## Context
- Dependencies: T-02, because the check must compare the completed helper definitions used by both writes and lint.
- Constraints: Keep runtime definitions authoritative and shared; use structured machine-comparable data rather than mention-only text searches.
- Reason: A contract that is documented but not mechanically checked will drift again.

Off-limits: Do not introduce a second vocabulary in lint or the validator, loosen the validator's failure status, or edit historical logs.

## Scope
- **In scope:** Complete field and normalization tables, presence and count semantics, lint contract, invalid-event state guarantees, and bidirectional drift checks.
- **Out of scope:** Producer or linter behavior changes, retrospective reporting, and acceptance-harness implementation.
- **Target files:** `rules/run-log.md`, `scripts/validate-contracts.sh`

## Steps
1. Update the field table with exact enum sets, count names and bounds, required fields, and absent-versus-empty behavior.
2. Document exact legacy mappings, match boundaries, raw-note provenance, and the `unknown` flow default.
3. Document invalid-event immutability, non-blocking warnings, and the complete read-only lint interface and summary contract.
4. Represent the canonical documentation tables as structured machine-comparable values.
5. Read the helper's effective runtime definitions through its structured contract interface and compare all values and mappings with documentation.
6. Verify the `NEEDS WORK` prefix boundary explicitly, including rejection of lookalikes.
7. Report field-specific drift failures and preserve nonzero status for any missing, extra, or changed value on either side.
8. Include contract mutations of both runtime definitions and documentation in the isolated acceptance coverage.

## Acceptance Criteria
- The rule documents every enum, mapping, count bound, presence rule, flow default, write guarantee, and lint reporting rule from the spec.
- Contract validation compares structured effective helper data and canonical documentation tables, including exact `NEEDS WORK` prefix semantics.
- Removing, adding, or changing a value or mapping on either side causes a field-specific contract failure with nonzero exit status.
- The writer and linter consume one runtime vocabulary source; the validator reads those effective definitions instead of maintaining another copy.

## Test Plan
- **Level:** contract, smoke
- **Scenarios:**
  - Inspect the run-log tables and compare unmodified helper definitions → every enum, mapping, integer bound, presence rule, default, and lint contract is documented and validation passes.
  - Remove or change each enum/mapping on the runtime side → validation fails with a field-specific message.
  - Remove or change each enum/mapping in documentation → validation fails with a field-specific message.
  - Change the `NEEDS WORK` boundary to accept a lookalike → validation detects mapping drift.
  - Compare producer and lint contract consumers with the contract export → both use the same runtime definitions and the validator reads that export.
- **Edge cases:** Missing tables, duplicate values, extra aliases, changed count maximum, and case-sensitive aliases.
