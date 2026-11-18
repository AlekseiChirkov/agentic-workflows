## Goal
Connect finalization with shared workflow contracts.

## Context
- working_dir: ../../../../..
- Dependencies: T-02
- Constraints: owner-approved specification and design; test-first; frozen validator inventory.

## Scope
- In scope: Single public phase, canonical state/evidence/authorization contracts, context bootstrap, parent handoffs, protected history and current-pointer exception, scripts guide, manual, reference, templates and generated parity. No additional cleanup or phase flags.
- Out of scope: paused audit, live consumer deployment, product work and PR merging.
- Target files: workflows/phase-finalize.md, rules/phase-finalize.md, rules/*.md, workflows/*.md, templates/*.md, docs/*.md, scripts/check-finalization-workflow.py, scripts/validate-task.sh

## Steps
1. Load repository bootstrap and relevant contracts.
2. Derive isolated behavior tests from the approved criteria.
3. Run tests and report observed RED before implementation.
4. Implement only the described scope without weakening tests or safety gates.
5. Run focused checks and report actual limitations and shared-file deltas.

## Acceptance Criteria
- The applicable approved requirements and acceptance scenarios pass executable isolated checks.
- Uncertain evidence and unsafe mutations fail closed with recoverable state; unrelated work is unchanged.
- Existing callers retain their contract and new behavior is documented at its canonical source.

## Test Plan
- Level: integration and contract; smoke for instruction contracts.
- Run dedicated scripts/check-*.py acceptance checks against temporary repositories and controlled receipts; run existing focused checks, then required full validation and staged sync at task completion.
