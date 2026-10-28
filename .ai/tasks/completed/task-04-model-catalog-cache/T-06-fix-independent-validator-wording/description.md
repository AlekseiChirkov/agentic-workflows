## Goal
Restore compatibility with the required independent-validator instruction gate while preserving separate default-role workers and all authorization restrictions.

## Context
- The final full regression at commit 69898c5 fails the unchanged ORCH independent-validator gate and consequently its nested version-history fixture.
- The gate requires the literal `Spawn a **separate** sub-agent`; the revised wording inserts session-default role worker before sub-agent.
- Current separate-worker semantics are correct. This repair restores explicit compatible wording only.

## Scope
- **In scope:** minimal wording correction in workflows/spec-run.md, preserving fresh session-default Validator behavior and no inheritance of the Implementer's model.
- **Out of scope:** validator/test changes, helper changes, model/provider calls, deployment, schema/runtime behavior changes, optional example-predicate enhancement.
- **Target files:** workflows/spec-run.md.

## Steps
1. Reproduce the unchanged literal gate failure and classify the documentation-only test level.
2. Restore `Spawn a **separate** sub-agent` while retaining session-default worker, fresh capability checks, no model inheritance and stop behavior.
3. Verify the unchanged gate and focused model/instruction regressions; return finalization deltas.

## Acceptance Criteria
- The unchanged independent-validator gate passes without modifying scripts/validate-contracts.sh.
- The Validator remains a separate fresh session-default role worker; it never inherits the Implementer's model, and unavailable worker spawning still stops.
- All87 current model tests and unchanged general instruction checks remain passing, with all frozen test bytes preserved.

## Test Plan
- **Level:** none for new tests: this is documentation-only wording restoration with no runtime or workflow behavior change. The existing required smoke contract supplies the before/after verification; no new test behavior is introduced.
- **Scenarios:** existing grep gate fails before correction and passes afterward; focused --model-workflow-only remains green.
- **Edge cases:** preserve exact worker-role restrictions and all unrelated text; no global configuration or provider calls.
