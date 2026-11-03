## Goal
Prevent normalized outputs from entering the shared usage store through concurrent destination replacement.

## Context
- Dependencies: T-02b; continue from the reviewed source adapter branch.
- Constraints: Preserve the explicit source selection, bounded reads, sanitized outputs and nonblocking legacy behavior. The test and implementation must protect the complete output operation, including concurrent directory moves.
- Reason: Independent source-adapter integration validation reproduced a violation of the sole-writer invariant.

Off-limits: Paid calls, implicit history discovery, rewriting accepted evidence or changing unrelated lifecycle behavior.

## Scope
- **In scope:** Destination validation and atomic publication of normalized output under adversarial path replacement, including the shared usage store boundary.
- **Out of scope:** Unrelated pricing, reporting and alert behavior.
- **Target files:** scripts/usage-telemetry.py, tests/usage-normalize-cli.py and any narrowly required supporting tests or documentation.

## Steps
1. Preserve the reviewed branch and reproduce the destination move after the final path check as a failing test.
2. Implement and document an enforceable destination boundary without claiming protection from a post-write check alone.
3. Verify normal and invalid source behavior, concurrent destination moves, path safety and the sole-writer invariant.
4. Run independent validation, then rerun the source adapter composite integration validation.

## Acceptance Criteria
- A concurrent move of the output directory into the shared usage store cannot cause normalized output or temporary output to be published there.
- Explicit digest-verified source selection still produces sanitized, fixed-time output; invalid records are quarantined without losing valid siblings.
- Failed or unsafe output publication produces no false success and does not mutate existing lifecycle evidence.

## Test Plan
- **Level:** integration and contract.
- **Scenarios:**
  - Move the output parent after the last path check and before installation; verify no output is created in the shared usage store.
  - Exercise valid selection, malformed records, changed inputs and destination failures without weakening existing tests.
  - Re-run source-selection, bounded-read, normalization and CLI suites and the parent integration criteria.

## Description Amendment
The owner authorized resolving the infeasible arbitrary-rename contract by removing filesystem output from the normalizer. Normalize emits a complete canonical bundle to a pipe or socket after validation; it rejects `--output` and regular-file stdout. Consumers own persistence and its safety boundary. The earlier destination criterion is superseded: directory moves cannot make the normalizer create either temporary or final output in the shared store because it creates neither. A caller or consumer may independently write there and is outside the helper's enforcement boundary. Existing command examples requiring `--output` need a task-level specification amendment.
