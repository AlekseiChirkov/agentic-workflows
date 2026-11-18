## Goal
Enforce scoped cleanup and stage provider outputs.

## Context
- working_dir: ../../../../..
- Dependencies: T-01
- Constraints: owner-approved specification and design; test-first; frozen validator inventory.

## Scope
- In scope: Finalization receipt verifier and deletion/lease gating without weakening restack or other rails; isolated sync staging with no hooks or project scans, mandatory acceptance preflight and provider parity fixtures.
- Out of scope: paused audit, live consumer deployment, product work and PR merging.
- Target files: scripts/finalization_evidence.py, rules/git-flow.md, hooks/git_rails.py, scripts/sync.sh, scripts/setup-new-project.sh, scripts/check-finalization-safety.py

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

## Description Amendments
- 2026-11-17: Move the narrow canonical Git ownership/receipt exception into this leaf before or together with hook implementation. This changes implementation ordering only; the approved permission scope is unchanged. Remaining shared readers and documentation stay in the following leaf.
- 2026-11-17: Include the narrow evidence-module interface addition that binds configured and effective fetch/push transport identity across prepare, resume and deletion. This closes the existing approved repository-identity guarantee without adding public options or expanding cleanup authorization.
