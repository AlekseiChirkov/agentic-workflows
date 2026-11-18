---
trigger: model_decision
description: Context loading rules for separately invoked post-merge finalization — load when running /phase-finalize
---

# Phase: Finalization — Context Rules

## Context Bootstrap

Before file or Git operations, resolve the selected task/spec and its project working
root. Load umbrella context before local context; local overrides apply only to its
repository. Reuse unchanged sources only within this invocation. Read missing conditional
sources as unavailable; missing required delivery/recovery evidence blocks mutation.

| Order | Source | Extract |
|---|---|---|
| 1 | `.ai/memory/architecture.md`, `.ai/memory/state.md` | Current system, task state and unfinished scope |
| 2 | `.ai/principles/architecture.md`, `coding.md`, `domain.md` | Knowledge ownership, tracking policy and invariants |
| 3 | `.ai/adr/index.md` and relevant full ADRs | Binding decisions and protected historical intent |
| 4 | `.ai/context/runbook.md` | Verification, operations, recovery and required deployment contracts |
| 5 | `.ai/context/environment.md`, `.ai/context/integrations.md` | Intended environments/revisions and repository identities |
| 6 | Current progress, ADR statuses, roadmap/scope indexes, delivery notes, top-level guidance | Current claims, historical intent and other unfinished work; explicitly skip absent optional records |
| 7 | Selected task state/plan/descriptions, source spec, supporting review records | Original full Git fields, independent validation, TDD and remaining phases |
| 8 | Existing stable finalization journal and immutable snapshots | Original scope, attempts, checkpoints, recovery, old paths and archive intent |

Read original delivery records and each recorded repository's relevant local sources after the umbrella sources.
Do not inspect unrelated repositories or use historical progress as current proof.
Load `workflow-globals`, `workflow-reference`, `git-flow`, `orchestration` and `run-log`;
on Claude Code/Codex resolve these to the `rule-` skill names. Read required helper
schemas from the configured or independently verified source checkout before writes.
Report: "Finalization context loaded: [sources read; required missing evidence]."

## Phase Behaviors

Canonical state, checkpoints and authorization: `workflow-globals → ## Finalization`.
Git authority: `git-flow → ## Finalization Git ownership`. Preservation and relocation:
`workflow-reference → ## Protected Sections Contract`. Logging remains best effort;
its failure cannot become a successful test or deployment measurement.

Run the single `phase-finalize` workflow through its own Guard; no automatic entry from
Validation or its parents. Ordinary invocation already authorizes mandatory proven cleanup.
Retain independent review and shared-file ownership. Reconcile every rerun against current
facts; report prior validation, integration, cleanup, archival and deployment separately.
