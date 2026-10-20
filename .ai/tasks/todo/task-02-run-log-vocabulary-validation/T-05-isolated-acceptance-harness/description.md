## Goal
Provide an executable isolated smoke harness that covers the run-log vocabulary contract without reading or changing real run logs.

## Context
- Dependencies: T-01, T-02, T-03, and T-04, because the harness validates their integrated behavior.
- Constraints: Use a temporary log root and workflow fixture; do not read, modify, or depend on the repository's real run store.
- Reason: The task's acceptance contract requires repeatable coverage of failure paths, historical-file preservation, and contract drift.

Off-limits: Do not change runtime or documentation behavior to make a test pass; do not include private data or real log content.

## Scope
- **In scope:** An executable shell smoke harness covering producer validation, lint, retrospective contract, documentation drift, non-blocking errors, and file immutability.
- **Out of scope:** Production implementation, changes to real logs, and tests unrelated to run-log telemetry.
- **Target files:** `tests/log-step.sh`

## Steps
1. Create a temporary fixture tree with an isolated `ORCHESTRAIL_LOG_ROOT` and helper workflow directory.
2. Add cleanup handling and ensure all test commands receive only the temporary paths.
3. Cover canonical enums, every alias, normalization order, explicit empty values, and integer syntax and boundaries.
4. Cover rejected event immutability, invalid-follow-up then valid event behavior, flow defaults, step membership, and filesystem failures.
5. Cover lint selections, malformed and legacy records, no-match and empty stores, active runs, missing `jq`, and read-only checksums.
6. Cover retrospective filter alignment, invalid-row treatment, unusable closes, and documentation/runtime drift in both directions.
7. Make the script executable and assert that the historical fixture checksums remain unchanged after every read-only operation.

## Acceptance Criteria
- `tests/log-step.sh` is executable and exercises every producer, linter, retrospective, and contract-drift branch required by the spec.
- All fixtures use temporary log and workflow paths; the harness never reads, modifies, or depends on the real run store.
- The harness verifies preservation of historical fixture checksums and passes shell syntax validation.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - Execute the harness → it runs every isolated fixture and exits zero only when all expected outputs and state checks pass.
  - Run with the real log root absent or populated → fixture setup still points every helper call at the temporary root and never opens real run files.
  - Compare historical fixture checksums before and after lint and retrospective operations → every checksum is identical.
- **Edge cases:** Interrupted fixture cleanup, paths containing spaces, unavailable workflow directory, missing `jq`, and a failure during simulated writes.
