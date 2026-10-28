# index.md — index of architectural decision records

## Purpose
Lists all ADRs for Orchestrail itself with number, title, status, and date.
ADR-0001 … 0006 are reconstructions of decisions already embedded in the rules, written
so that a contributor can find the *why* without reading every rule. ADR-0007 and 0009 record owner decisions of September 2026; ADR-0008 is provisional.

## Structure

## Records
| Number | Title | Status | Date | Link |
|--------|-------|--------|------|------|
| 0001 | The pipeline is markdown instructions with no runtime | Accepted | 2026-07-01 | [0001-task-unknown-markdown-only-no-runtime.md](0001-task-unknown-markdown-only-no-runtime.md) |
| 0002 | All pipeline state lives on disk in `.ai/` and is never committed in consumer projects | Accepted | 2026-07-01 | [0002-task-unknown-state-on-disk-untracked.md](0002-task-unknown-state-on-disk-untracked.md) |
| 0003 | Rules deploy to Claude Code and Codex as `rule-<name>` skills; essentials duplicated | Accepted | 2026-07-21 | [0003-task-unknown-rules-as-prefixed-skills.md](0003-task-unknown-rules-as-prefixed-skills.md) |
| 0004 | Orchestrated mode uses context-bounded roles and strictly sequential execution | Accepted | 2026-08-26 | [0004-task-unknown-sequential-orchestration-context-roles.md](0004-task-unknown-sequential-orchestration-context-roles.md) |
| 0005 | Stacked branches, two commits per subtask, no pipeline identifiers or attribution in the repository | Accepted | 2026-08-26 | [0005-task-unknown-pipeline-invisible-in-repository.md](0005-task-unknown-pipeline-invisible-in-repository.md) |
| 0006 | Central cross-project run log written by a helper and read only by `/retro` | Accepted | 2026-08-26 | [0006-task-unknown-central-run-log-and-retro.md](0006-task-unknown-central-run-log-and-retro.md) |
| 0007 | This repository commits its own `.ai/` knowledge base in full | Superseded by ADR-0012 | 2026-09-16 | [0007-task-unknown-commit-ai-directory-in-this-repository.md](0007-task-unknown-commit-ai-directory-in-this-repository.md) |
| 0008 | Roadmap direction: move enforcement from prose into the harness before adding rules | Accepted | 2026-09-16 | [0008-task-unknown-enforcement-moves-to-harness.md](0008-task-unknown-enforcement-moves-to-harness.md) |
| 0009 | Roadmap decisions of September 2026 (identity, harness abstraction, naming, composites, telemetry, profiles, order) | Accepted | 2026-09-17 | [0009-task-unknown-roadmap-decisions-2026-09.md](0009-task-unknown-roadmap-decisions-2026-09.md) |
| 0010 | Public hygiene, complete knowledge-base preservation, and local publication | Accepted | 2026-10-19 | [0010-task-unknown-public-hygiene-and-local-publication.md](0010-task-unknown-public-hygiene-and-local-publication.md) |
| 0011 | Run-log contract validation and usable retrospective evidence | Accepted | 2026-10-21 | [0011-task-02-run-log-contract.md](0011-task-02-run-log-contract.md) |
| 0012 | Respect repository-owned knowledge tracking policy | Accepted | 2026-10-22 | [0012-task-unknown-knowledge-tracking-policy.md](0012-task-unknown-knowledge-tracking-policy.md) |
| 0013 | Explicitly correlated hooks and coverage-aware timing | Accepted | 2026-10-26 | [0013-task-03-correlated-hook-logging.md](0013-task-03-correlated-hook-logging.md) |
| 0014 | Clarify workflow execution and context ownership | Accepted | 2026-10-28 | [0014-task-unknown-workflow-contract-clarity.md](0014-task-unknown-workflow-contract-clarity.md) |
| 0015 | Optional cached catalog and conservative model resolution | Accepted | 2026-10-28 | [0015-task-04-cached-model-selection.md](0015-task-04-cached-model-selection.md) |
