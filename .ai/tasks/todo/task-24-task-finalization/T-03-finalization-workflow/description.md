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

- 2026-11-17: Source contract review reproduced interleaved checkout/cleanup and a false-complete pending-refresh inspection outcome. Preserve all tests and repair with separately frozen failing regressions. All recorded-repository checkout refreshes precede remote then local cleanup; pending refresh remains incomplete.
- 2026-11-17: Tracked current knowledge must be reconciled without weakening dirty-tree checks. Add predeclared typed current-record inventory, immutable original snapshots and exact independently attested before/after bindings before allowing only those observed metadata changes on integration checkouts. Keep the index unchanged and exclude source/configuration, task/spec requirements, historical records and recovery/journal artifacts. Untracked umbrella policy remains unchanged; no staging or commits are authorized.
- 2026-11-17: Independent forward evaluation found undocumented final-verification marker coupling. Align the reader with canonical completed-validation evidence and documented source-bound attestations; absent or contradictory evidence still blocks. A newly failed required check must invalidate an older same-source passing attestation until a newer valid pass is established, while preserving both attempts.
- 2026-11-17: Independent cross-file review requires all matching phases' deferred scope to constrain whole-spec archival, canonical hosting-identity bindings shared by helper and hook for rewritten-history SSH aliases, and bounded authoritative journals with immutable digest-bound exact output artifacts. Preserve reader bounds, restack semantics and previous journal revisions on write refusal; never truncate audit evidence. Add observed failing regressions before repair.
- 2026-11-17: Independent consecutive-task fixtures reproduced stale completed receipts vetoing a later valid task. Separate unusable journal/binding validation from ordinary contextual nonmatches, retain exact generation/tip/unique-match protection, and preserve existing restack semantics. Cover distinct and reused branch names with observed RED before repair; any own-receipt retirement must be exact, recoverable and verified before completion.
- 2026-11-17: Whole-skill evaluation requires project-root scope for umbrella checks only; planned Git actions remain repository-exact and arbitrary paths are invalid. Independent new-module review requires current bytes for all captured records to match accepted bindings (or exact journaled archive relocation), explicit positive evidence for previous-phase completion, and clean index-baseline reconciliation tied to freshly verified integration generations. Keep immutable baseline history, invalidated stale attestations, unchanged task branch tips and strict staged/unrelated-work refusal. Add observed RED before repairs.
