## Goal
Detect incomplete telemetry stream output.

## Context
- Owner-authorized fresh validation finding in PR #58.
- Independent review evidence: the final PR review report and parent Issue List.
- Preserve existing evidence, legacy lifecycle behavior and explicitly unknown measurements.

## Scope
- **In scope:** detect incomplete telemetry stream output and its behavioral regression coverage.
- **Out of scope:** unrelated telemetry behavior, real deployments, network or paid model calls, and historical evidence rewriting.
- **Target files:** scripts/usage-telemetry.py, tests/usage-normalize-cli.py.

## Steps
1. Add focused behavioral regressions and observe the expected failures before changing production code.
2. Repair the implementation without weakening the frozen tests or broadening the public contract.
3. Run focused and neighboring acceptance checks, inspect the changes, and retain separate test and fix commits.

## Acceptance Criteria
- Normalization, analysis, status and owner delivery never report success after partial or non-progress stdout writes.
- Real nonblocking pipe/socket regressions establish complete successful output or a sanitized I/O failure, while ordinary and provenance output remain correct.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - Normalization, analysis, status and owner delivery never report success after partial or non-progress stdout writes. Verify the stated result through the relevant public boundary.
  - Real nonblocking pipe/socket regressions establish complete successful output or a sanitized I/O failure, while ordinary and provenance output remain correct. Verify the stated result through the relevant public boundary.
- **Edge cases:** valid and invalid boundaries, missing or partial evidence, repeated delivery, scope isolation and failure preservation where applicable.
