## Goal
Integrate usage contract into the complete telemetry contract.

## Context
- type: composite
- children: T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d
- Dependencies: none
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-01a canonical encoding; T-01b typed measurements; T-01e observation and bundle schemas; T-01f source profile schema; T-01h source selection schema; T-01i inventory schema; T-01j attribution schema; T-01k collection segment schema; T-01l diagnostic measurement schema; T-01m price snapshot schema; T-01n pricing scenario schema; T-01o warning policy schema; T-01p analysis corpus schema; T-01q usage receipt schema; T-01r lifecycle projection schema; T-01s current-run snapshot schema; T-01g producer schema export; T-01c source profiles and normalization; T-01d diagnostic metrics.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** scripts/usage_telemetry_contract.py, scripts/validate-contracts.sh, tests/usage-canonical-encoding.py, tests/usage-typed-schema.py, tests/usage-observation-bundle-schema.py, tests/usage-entity-schemas.py, tests/usage-source-selection.py, tests/usage-inventory-schema.py, tests/usage-attribution-schema.py, tests/usage-collection-segment-schema.py, tests/usage-diagnostic-schema.py, tests/usage-price-snapshot-schema.py, tests/usage-pricing-scenario-schema.py, tests/usage-warning-policy-schema.py, tests/usage-analysis-corpus-schema.py, tests/usage-usage-receipt-schema.py, tests/usage-lifecycle-projection-schema.py, tests/usage-current-run-snapshot-schema.py, tests/usage-contract-export.py, scripts/log-step.sh, rules/run-log.md, tests/usage-source-profiles.py, harness/claude/capabilities.md, harness/codex/capabilities.md, tests/usage-diagnostic-registry.py.

## Steps
See children: T-01a canonical encoding; T-01b typed measurements; T-01e observation and bundle schemas; T-01f source profile schema; T-01h source selection schema; T-01i inventory schema; T-01j attribution schema; T-01k collection segment schema; T-01l diagnostic measurement schema; T-01m price snapshot schema; T-01n pricing scenario schema; T-01o warning policy schema; T-01p analysis corpus schema; T-01q usage receipt schema; T-01r lifecycle projection schema; T-01s current-run snapshot schema; T-01g producer schema export; T-01c source profiles and normalization; T-01d diagnostic metrics.

## Acceptance Criteria
- Profile-normalized observations validate against the shared schema and produce the same canonical hash after object-key permutation.
- An independent diagnostic record validates through the registry without becoming an additional paid request, and the unchanged observation retains its original content identity.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - Profile-normalized observations validate against the shared schema and produce the same canonical hash after object-key permutation. → the integrated outputs agree.
  - An independent diagnostic record validates through the registry without becoming an additional paid request, and the unchanged observation retains its original content identity. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
