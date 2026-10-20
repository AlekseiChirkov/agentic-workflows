# README.md — entry point for agents working inside .ai/

## Purpose
This is the knowledge base for **Orchestrail itself** — the repository that
defines the AI-SDLC pipeline. It is a meta-project: the product is a set of markdown
workflows, rules, principles, templates, and shell scripts, and "the codebase" is those
files. Do not confuse this directory with `templates/.ai/`, which is the skeleton the
pipeline seeds into *other* projects.

Read this file first, every time. It changes only when the structure of `.ai/` changes.

## Structure

### Loading Order

**Always load (every session):**
- `memory/state.md` — active work, roadmap status, known blockers
- `memory/architecture.md` — how the workflow system is built and deployed
- `principles/architecture.md`, `principles/coding.md`, `principles/domain.md`

**Load on demand (when relevant to the current task):**
- `memory/progress.md` — history of the project (audits, incidents, runs)
- `adr/index.md` — design decisions already embedded in the rules; load a full ADR before
  changing the area it governs
- `context/runbook.md` — how to validate, deploy, audit, and recover
- `context/environment.md` — the three target environments and every hard-coded path
- `context/integrations.md` — the agent harnesses and tools the workflows depend on
- `specs/README.md` — the improvement roadmap, one spec per change, in priority order
- `specs/completed/` — completed source specifications retained for historical reference
- `tasks/todo/<task>/` — when working on a specific task
- `tasks/completed/<task>/` — for historical reference only

### Update Protocol

- After each task: update `memory/state.md` and append to `memory/progress.md`
- After each design decision about the pipeline: add an ADR under `adr/`, link it from
  `adr/index.md`, and update `memory/architecture.md` if the deployment shape or the
  contract surface changed
- After each principle clarification: update the relevant `principles/*.md`
- After a change to `sync.sh`, `setup-*.sh`, or a deployment path: update
  `context/environment.md` and `context/runbook.md`
- After a change to any always-on rule or canonical status format: add or update the
  matching check in `validate-contracts.sh` **in the same change**

### Where documents go

Analysis, audits, comparisons, and any similar write-up about the system are created
under `docs/` (`docs/analysis/`, `docs/audits/`, dated file names) and indexed in
`docs/README.md` — never in the repository root or in `.ai/`. Actionable improvements are
specs in `specs/`. Full rule: `principles/coding.md → Document placement`.

### This repository is its own consumer

Changes here are made with the same pipeline the repository defines. A change to a rule
or workflow is a task: it starts from a spec in `specs/`, runs through Discovery, and ends
with `validate-contracts.sh` green and `sync.sh` deployed. The TDD rule applies with the
test level `smoke` — `validate-contracts.sh` is the validating tool, and a new contract
check that fails before the change and passes after it is the RED test.

### File Map

- `specs/` — improvement specs (one per change; `specs/README.md` is the ordered roadmap)
- `memory/state.md` — active tasks and roadmap status
- `memory/architecture.md` — system snapshot: layers, deployment, data flow, contracts
- `memory/progress.md` — chronological log
- `tasks/todo/`, `tasks/completed/` — task directories produced by Discovery
- `adr/index.md` — decision index; `adr/NNNN-*.md` — decision records
- `principles/architecture.md` — design principles of the workflow system
- `principles/coding.md` — how workflow, rule, and script files are written
- `principles/domain.md` — vocabulary and invariants of the pipeline
- `context/runbook.md` — commands and procedures
- `context/environment.md` — environments, paths, variables
- `context/integrations.md` — harnesses and external tools
- `../docs/` — manuals, analyses, audits (see `principles/coding.md → Document placement`)
