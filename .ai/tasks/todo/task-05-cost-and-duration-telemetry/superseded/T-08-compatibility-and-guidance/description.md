## Goal
Integrate compatibility and guidance into the complete telemetry contract.

## Context
- type: composite
- children: T-08a, T-08b
- Dependencies: T-07d
- Constraints: Preserve explicit scope, immutable evidence and unknown values throughout.
- Reason: The components are separately testable and require integrated verification.

Off-limits: Paid model calls, automatic model or policy changes, unsolicited history discovery and changes to existing evidence.

## Scope
- **In scope:** T-08a legacy compatibility and recovery; T-08b offline telemetry operating guidance.
- **Out of scope:** Other telemetry components and unrelated workflow behavior.
- **Target files:** docs/USAGE.md, tests/usage-compatibility-recovery.py, scripts/validate-contracts.sh, tests/log-step.sh, tests/usage-telemetry-guidance.py, rules/run-log.md, workflows/retro.md.

## Steps
See children: T-08a legacy compatibility and recovery; T-08b offline telemetry operating guidance.

## Acceptance Criteria
- The documented disable-and-resume procedure preserves prior evidence while legacy logging and offline validation work without optional usage dependencies.
- Injected installation or publication failure produces no false receipt, and a documented exact retry recognizes a previously installed bundle without invoking a model.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - The documented disable-and-resume procedure preserves prior evidence while legacy logging and offline validation work without optional usage dependencies. → the integrated outputs agree.
  - Injected installation or publication failure produces no false receipt, and a documented exact retry recognizes a previously installed bundle without invoking a model. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.
