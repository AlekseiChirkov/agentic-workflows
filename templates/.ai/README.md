# README.md — entry point for agents working inside .ai/

## Purpose
This file orients an AI agent to the `.ai/` knowledge base of the project. It
defines what must be loaded on every session, what is loaded on demand, and
how the agent is expected to keep these files in sync with reality. Read this
file first, every time. It changes only when the structure of `.ai/` changes.

## Structure

### Loading Order

**Always load (every session):**
- `memory/state.md` — current task-level state and active work
- `memory/architecture.md` — system architecture snapshot
- `principles/architecture.md`, `principles/coding.md`, `principles/domain.md`

**Load on demand (when relevant to the current task):**
- `memory/progress.md` — historical progress log
- `adr/index.md` — index of architectural decision records; load specific ADRs as needed
- `context/integrations.md` — external systems and integration points
- `context/environment.md` — runtime environments and configuration
- `context/runbook.md` — operational procedures
- `specs/<NN>-<slug>.md` — the original task statement; accessed via `spec_path:` in task state.md
- `tasks/todo/<task>/` — when working on a specific task
- `tasks/completed/<task>/` — for historical reference only

### Update Protocol

- After each task: update `memory/state.md` (current state) and append to `memory/progress.md`
- After each architectural decision: add an ADR under `adr/` and link it from `adr/index.md`; update `memory/architecture.md` if the snapshot is affected
- After each principle clarification: update the relevant `principles/*.md`
- After each integration or environment change: update the relevant `context/*.md`

### File Map

- `specs/` — task spec files (one per task; consumed by phase-discovery)
- `memory/state.md` — current task-level state, active tasks, statuses
- `memory/architecture.md` — system architecture snapshot
- `memory/progress.md` — chronological progress log
- `tasks/todo/` — task directories for pending work
- `tasks/completed/` — task directories for finished work
- `adr/index.md` — index of architectural decision records
- `principles/architecture.md` — architectural principles
- `principles/coding.md` — coding standards
- `principles/domain.md` — domain-specific principles
- `context/integrations.md` — external systems and integration points
- `context/environment.md` — runtime environments and configuration
- `context/runbook.md` — operational procedures and recovery steps
