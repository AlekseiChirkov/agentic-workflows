## Goal
Export every permitted input identifier.

## Context
- Owner-authorized fresh validation finding in PR #61.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** export every permitted input identifier and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage_telemetry_exports.py, tests/usage-report-exports.py, tests/usage-retrospective-integration.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Contract-valid colon and 256-character identifiers reach deterministic JSON, CSV, Markdown and archive exports.
- Input-derived identifiers match their source contracts while unsafe or over-limit values remain rejected.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Contract-valid colon and 256-character identifiers reach deterministic JSON, CSV, Markdown and archive exports. Verify the stated result through the relevant public boundary.
  - Input-derived identifiers match their source contracts while unsafe or over-limit values remain rejected. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
