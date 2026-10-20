# state-archive — task-01-git-source-of-truth

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Prepare the repository for the Orchestrail identity by making its scripts and documentation resolve from the checkout rather than its former name, adding version metadata to task and run records, publishing concise project materials, and moving the local checkout to the new directory name. Preserve the existing Git history and the repository's complete tracked knowledge base.

### Affected Parts
- Root shell scripts and helper workflows: replace the former checkout and environment defaults with portable Orchestrail settings while preserving documented command-line overrides.
- Task and run metadata: add the root contract version, stamp new task state, record it in run-start events, and warn when rules change without a version update.
- Public package materials: create the Apache-2.0 license and a short README, narrow ignore patterns to local logs and machine settings, and update the setup guide for the public checkout path and tag.
- Tracked project documentation: update current references across rules, workflows, principles, templates, and the knowledge base while preserving approved historical records.
- Repository operations: retain the already initialized history, build on the scrubbed predecessor stack, and move the local checkout after repository work is complete.

### Codebase Analysis
- This checkout is already a Git repository. The current branch is `fix/public-hygiene-guard` at `a4602e1`; `main` remains at `fc94fc1` and does not contain the completed scrub work required by this spec. The current public repository has PRs #2–#4 ready for review. The task depends on spec 00, so the new stack must inherit the current predecessor branch to include the hygiene guard.
- `.ai/` is intentionally tracked in full, including task records. The owner reaffirmed this in the current conversation; ADR-0007 and ADR-0010 document the repository-specific exception to consumer-project defaults.
- The required prerequisite `bash validate-contracts.sh --hygiene-only` exits 0. The completed scrub task records the full-tree scan and validation results.
- Root `README.md` has 127 lines; `LICENSE` and `VERSION` are absent. `.gitignore` currently ignores all of `logs/` and `.claude/settings.local.json`; the spec requires narrower log exclusions and allows `.ai/` and `docs/` to remain tracked.
- `sync.sh` resolves its checkout from its own directory but currently uses `WORKFLOWS_SOURCE`; `log-step.sh` resolves its log store from its own directory but currently uses `AGENTIC_LOG_ROOT`. Setup scripts and workflow helpers use those existing variable names. `pd-analyze` does not currently stamp a contract version, and `run-start` does not record one.
- The old checkout name appears in six shell scripts and in current documentation, templates, workflows, rules, and tracked knowledge files. Matches also occur in the active source spec itself, future specs, and historical pull-request links. The source spec's literal scan criterion therefore needs an explicit policy for its own source text and preserved records.
- No module-specific code reading beyond the entry points was needed. Files read: `sync.sh` (root resolution and command override), `log-step.sh` (log root and run-start fields), and `validate-contracts.sh` (existing path-portability smoke checks and the scrub prerequisite). Also inspected `.gitignore`, the README introduction, and setup-guide section 4 for the requested documentation changes.

### Open Questions
- The existing Git history and completed scrub work are retained. The public repository is already live, and the owner has authorized additive branch publication and pull requests; no merge, main update, or history rewrite is authorized. Source: ADR-0010's 2026-10-19 amendment and `.ai/memory/state.md`.
- The current source spec and preserved historical links contain the former repository name, while its scan criterion does not exempt them. The treatment is collected in the batch gate below.
- The exact copyright-holder wording is not specified in the repository artifacts. The desired public wording is collected in the batch gate below.
- The single-import-commit and tag criterion predates the existing Git history and conflicts with the no-main-update rule for this run. Its delivery boundary is collected in the batch gate below.

## Archived Solution Design — Variants

1. **Single broad release branch:** combine version contracts, runtime path changes, public materials, and the final identity sweep in one large change. This reduces branch coordination but produces a broad review and weakens the independent RED evidence for each contract.
2. **Sequential feature stack:** deliver version metadata, runtime path configuration, public package files, and the remaining identity sweep as four dependent branches. Each branch has its own smoke-level RED and implementation evidence, and the stack begins at the scrubbed predecessor.
3. **Separate versioning from identity work:** create one task for version metadata and a later task for all naming and packaging changes. This reduces the first task's scope but delays the public identity and creates a second discovery and validation cycle for changes that share the same release surface.

## Archived Solution Design — Rejected
- **Single broad release branch:** rejected because it combines several independent contracts into one review and does not match the existing reviewed stack.
- **Separate versioning task:** rejected because version metadata and public identity are parts of the same release contract and share the validator and run-log surfaces.
