## Goal
Implement evidence, journal and lossless archival mechanics.

## Context
- working_dir: ../../../../..
- Dependencies: —
- Constraints: owner-approved specification and design; test-first; frozen validator inventory.

## Scope
- In scope: Core helper and isolated behavioral fixtures. Explicit Git mutation commands are returned as plans, never executed internally. Include typed read-only git/PR evidence, full and quick prerequisites, root/path resolution, journal locking/CAS, recovery snapshots, no-overwrite task/spec archive, current-link/protected-content verification, independently attested knowledge/test outcomes and completion predicates.
- Out of scope: paused audit, live consumer deployment, product work and PR merging.
- Target files: scripts/phase-finalize.py, scripts/finalization_*.py, scripts/check-phase-finalize.py

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
