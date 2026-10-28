---
description: One-time knowledge-base initialization for legacy projects — inspect code and fill missing project context without overwriting established knowledge
---

Invocation: `/onboard-legacy-project`
Run from the project root after `scripts/setup-new-project.sh`. Reinvoke to resume.
This workflow writes knowledge and instruction placeholders only; it changes no product
code, git history or runtime environment.

## Guard

1. Require `.ai/{memory,context,principles,adr,specs,tasks}/`, `AGENTS.md` and `CLAUDE.md`.
   If any is absent → **stop**: "Run `bash <workflow-source>/scripts/setup-new-project.sh`
   first, then invoke `/onboard-legacy-project` again."
2. Read available project instructions and `.ai/memory/state.md` before writing. Load
   existing umbrella context before local context when applicable.
3. Read `.ai/onboarding-progress.md` if present. Resume the first incomplete phase/file.
   Checkbox `[x]` and legacy `✓` both mean complete. If quality checks already passed,
   report completion and **stop**, unless a refresh was explicitly requested.
4. Classify target files as `missing`, `stub` or `filled`. A stub contains only template
   placeholders/boilerplate; uncertain content counts as filled. Preserve filled content.
   Ask before replacing it unless the exact replacement is already authorized. Targeted
   instruction-placeholder edits in Phase 2 do not authorize rewriting surrounding text.

## Phase 0 — Pre-flight

Create or extend `.ai/onboarding-progress.md` without discarding prior progress:

```markdown
# Onboarding Progress

## Phases
- [ ] Phase 1 — Codebase Exploration
- [ ] Phase 2 — Write Knowledge Base Files
- [ ] Phase 3 — Quality Check

## Files
<One checkbox per Phase 2 target; record written/skipped and the reason.>

## Evidence
<Concise findings with source paths/lines, sufficient to resume.>

## Notes
Started: <ISO-8601 timestamp>
```

Report classification once. This progress file is the only Phase 1 write target: persist
findings as discovered so interruption does not lose reconnaissance. Do not mark a phase
complete until its outputs exist.

## Phase 1 — Codebase Exploration

Discover paths with `rg --files` (include relevant hidden CI/config paths). Exclude git,
dependencies, caches, build output and generated sources. Use structural search for code
when available, text search for documentation/configuration, and bounded nearby reads.
Do not dump the repository tree, lockfiles, complete migration histories or secret values.

Work through these areas; record evidence, unknowns and affected output targets:

| Area | Inspect and extract |
|---|---|
| Identity/layout | Root and relevant component READMEs; purpose, users, repository type, source roots and component boundaries |
| Stack | Dependency manifests and runtime/tool configs; versions, frameworks, persistence, test/lint/type/build tools; query lockfiles only for a required exact version |
| Entrypoints/interfaces | Server/CLI/worker startup, route/command/event registration and public surfaces |
| Architecture | Representative files per layer; dependency direction, data flow, comparable local patterns and known exceptions |
| Data | Current schemas/models and representative migrations; entities, relationships, tenancy, lifecycle and migration tool |
| Integrations | Client/adapter code and config; service purpose, protocol, auth mechanism and credential variable names |
| Environment | Example config, deployment and infrastructure declarations; variable names/purposes, environment detection, deploy targets and triggers |
| Tests/CI | Runner config, task targets/package scripts and CI steps; exact commands, external prerequisites, test types and coverage configuration |
| Standards | Representative source/tests across layers; naming, errors, logging, injection and test conventions |
| Domain | Model/route/service terminology, validations, enums and observed state transitions |
| Decisions/debt | Explicit design rationale, architectural comments and TODO/FIXME evidence; distinguish observed choice from inferred motive |
| Security | Bounded inspection for hardcoded credentials, unsafe query construction and permissive access/CORS; record verified risk locations without secret values |

An observed pattern is not automatically a binding principle. Separate documented rules,
consistent conventions and known violations. Do not infer reasons or rejected alternatives
from library choice alone. Label hypotheses and unverified security candidates clearly.
After recording adequate evidence for all areas, mark Phase 1 complete.

## Phase 2 — Write Knowledge Base Files

Use the existing project templates/section layout when available. For a missing target,
use the minimum sections below. For each file, recheck classification, write only
project-specific evidence, and update its progress checkbox immediately. Preserve filled
files; report authorized changes separately from skipped files.

Write `unknown — needs manual input` for missing evidence; reserve `not configured` and
`not applicable` for verified absence.
Do not run deploy/migration/seed commands during discovery merely to document them.

| # | Target | Content/sections |
|---|---|---|
| 1 | `.ai/memory/architecture.md` | Overview; Components with responsibility, key paths, interfaces/dependencies; Data Flow; Data Model; External Dependencies |
| 2 | `.ai/context/runbook.md` | Commands; Local Development prerequisites/steps; Environments; known Common Operations |
| 3 | `.ai/context/integrations.md` | Per integration: purpose, protocol, auth mechanism/variable names, key files, verified retry/rate/sandbox constraints; explicitly state if none detected |
| 4 | `.ai/context/environment.md` | Actual environments/deploy triggers/infrastructure; variable table (name, purpose, secret?, safe default); Secrets Management mechanism, never values |
| 5 | `.ai/principles/architecture.md` | Documented boundaries/rationale, observed structure, known exceptions/debt; do not invent prohibitions from inconsistent code |
| 6 | `.ai/principles/coding.md` | Naming, Error Handling, Logging, Dependency Injection, Testing Standards, Forbidden Patterns; distinguish existing rules from recommendations and risk findings |
| 7 | `.ai/principles/domain.md` | Vocabulary table, Invariants and Status / State Machines grounded in code or documentation |
| 8 | `.ai/adr/index.md` and onboarding record | Historical architecture snapshot as described below; preserve existing ADRs/index rows |
| 9 | `.ai/memory/state.md` | Canonical current task sections below; preserve known active work |
| 10 | `.ai/memory/progress.md` | Append actual onboarding outputs, detected stack, integrations and unresolved fields; preserve previous entries |
| 11 | `AGENTS.md` | Fill only existing Project Context and Commands placeholders |
| 12 | `CLAUDE.md` | Append Project Standards only when absent; preserve Context Loading Protocol and existing instructions |

For runbook and instruction command placeholders use these keys:

```text
test:      <verified command or unknown — needs manual input>
lint:      <verified command or unknown — needs manual input>
typecheck: <verified command, not configured, or unknown>
build:     <verified command, not applicable, or unknown>
migrate:   <verified command, not applicable, or unknown>
seed:      <verified command, not applicable, or unknown>
```

`AGENTS.md` needs test/lint/typecheck/build only. Project Context summarizes purpose, stack
and verified constraints. If the expected placeholder does not exist, report it; do not
invent a replacement instruction hierarchy. `CLAUDE.md → ## Project Standards` summarizes
architecture, stack, test/lint commands and established forbidden patterns.

### ADR snapshot

If no onboarding snapshot exists, allocate the next free four-digit ADR number and a
`NNNN-initial-onboarding.md` filename. Do not assume `0001` is available. Record observed
architecture, explicit decisions and evidence, unknown rationale/alternatives, and known
debt. This snapshot does not assert newly approved decisions or fabricated verification.
If a snapshot or filled index exists, preserve it and append only the new record/row.
Use this canonical index order:

```markdown
| Number | Title | Status | Date | Link |
|--------|-------|--------|------|------|
```

### Current task state

Use existing task artifacts to populate active work; never claim no tasks without checking.
For a new state file retain the canonical sections:

```markdown
# state.md — current task-level state and active work

## Active Tasks
<Actual entries using the canonical format, or None.>

## Done
<Known completed entries, or None.>

## Deferred
<Known deferred items, or None.>
```

Use `workflow-reference → ## .ai/memory/state.md Entry Format` for task entries; blocked
work remains in Active Tasks with `status: blocked`. Mark Phase 2 complete only after every
target has a recorded written/skipped outcome.

## Phase 3 — Quality Check

Verify source-backed claims and citations, actual component/domain names, consistent
commands across runbook/instructions, preserved filled content, and unresolved unknowns.
Inspect generated files for unfilled template placeholders and exposed secret values.
Correct only content this run owns; report conflicts with preserved content for review.

Mark Phase 3 complete only when these checks pass. Record completion time, exact output
paths, skipped targets and all remaining unknown fields in onboarding progress. Preserve prior evidence/history.

## Phase 4 — Report

Report written/updated/skipped files, stack, integration/domain/invariant counts, verified
test command, evidence limitations, unknown fields and confirmed security findings. Never
present an unexamined area as zero findings. Give manual next steps:

1. Review generated knowledge and resolve unknowns.
2. Establish `test:` in the runbook before execution if unknown; `/pae-tests` requires it.
3. Review confirmed security findings with the project owner.
4. Create a spec and run `/phase-discovery <spec>` when ready.

Then **stop**; invoke no next phase.
