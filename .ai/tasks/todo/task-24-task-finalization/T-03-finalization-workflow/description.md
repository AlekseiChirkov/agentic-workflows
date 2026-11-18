## Goal
Connect finalization with shared workflow contracts.

## Context
- working_dir: ../../../../..
- Dependencies: T-02
- Constraints: owner-approved specification and design; test-first; frozen validator inventory.

## Scope
- In scope: Single public phase, canonical state/evidence/authorization contracts, context bootstrap, parent handoffs, protected history and current-pointer exception, scripts guide, manual, reference, templates and generated parity. No additional cleanup or phase flags.
- Out of scope: paused audit, live consumer deployment, product work and PR merging.
- Target files: scripts/phase-finalize.py and finalization support modules for checkpoint/attempt recording, workflows/phase-finalize.md, rules/phase-finalize.md, rules/*.md, workflows/*.md, templates/*.md, docs/*.md, scripts/check-finalization-workflow.py, scripts/validate-task.sh

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
- 2026-11-17: Shared-contract review identified missing supported persistence for failed Git/check attempts and the approved pending/prepared/applied/verified/blocked/preserved operation checkpoints. Include the smallest typed recorder addition with RED behavior tests before implementation. A failed-command recorder must work from an authorized bound journal during remote/network unavailability, preserve exact argv/exit/stdout/stderr/provenance and prior failures, and never treat a caller success flag or exit code as a verified postcondition. Retain source-bound verification and honest recovered teardown/coverage reporting. This implements the approved journal contract; no public flags, children or architectural alternative are added.
- 2026-11-17: Read-only reference inspection confirms recorded repositories use a GitHub SSH host alias. The existing PR resolver accepts only literal github.com remotes. Add safe authoritative resolution for canonical numbered/full-URL PR records with SSH aliases, using existing GitHub tooling evidence and rejecting ambiguous or mismatched hosting identities; do not guess an identity from a repository path. Exercise controlled fixtures only; the completed reference project stays read-only.
- Reference lookup: GitHub CLI remote resolution translates SSH aliases before host filtering (https://github.com/cli/cli/blob/trunk/pkg/cmd/factory/remote_resolver.go). The repo-view manual exposes url/nameWithOwner fields (https://cli.github.com/manual/gh_repo_view). Constrain any fallback to the recorded origin identity; environment overrides, another default remote or mismatched returned identity must not silently select a different repository.
