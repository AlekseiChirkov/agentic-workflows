# README.md — entry point for agents working inside this umbrella .ai/

## Purpose
This is the system-level knowledge base for a multi-repository project.
Describes how all services interact, shared principles, and cross-cutting decisions.
Individual service repos have their own .ai/ — they inherit shared principles from
here and add service-specific overrides.

This file changes only when the structure of .ai/ changes.

## Loading Order

**At umbrella level (cross-service work):**
1. `memory/architecture.md` — system topology: all services, boundaries, data flows
2. `memory/state.md`        — cross-service tasks in flight
3. `principles/architecture.md`, `principles/coding.md`, `principles/domain.md`
4. `adr/index.md`           — cross-cutting decisions

On demand:
- `context/integrations.md` — external systems shared across services
- `context/environment.md`  — shared environments (GCP project IDs, staging, prod)

**Inside a SERVICE repository (two-level loading):**
Load umbrella first, then local — local overrides umbrella:
1. `../.ai/memory/architecture.md` — system topology
2. `.ai/memory/architecture.md`    — this service's internal architecture
3. `.ai/memory/state.md`           — active tasks in this service
4. `../.ai/principles/`            — shared principles (all three files)
5. `.ai/principles/`               — local overrides for this service
6. `.ai/adr/index.md`              — decisions specific to this service

On demand:
- `.ai/context/runbook.md`          — how to run/deploy this service
- `.ai/context/integrations.md`     — this service's specific integration details
- `../.ai/context/integrations.md`  — shared external systems

## Cross-Repo Tasks

A cross-repo task lives in `tasks/todo/<task-slug>/` at the umbrella level.
Its subtasks (T-XX) each declare `working_dir:` pointing to the target service repo.

**Workflow:**
```
cd lattice_lab/
/phase-discovery .ai/specs/01-auth-feature.md
# → creates .ai/tasks/todo/task-01-auth-feature/ with T-XX dirs
# → each T-XX/description.md has working_dir: ../../../../service-api (or similar)
# → plan.md shows Repo column: service-api | service-worker | (umbrella)

/phase-execution .ai/tasks/todo/task-01-auth-feature/
# → for each T-XX: resolves working_dir, executes inside that service repo
# → reads principles from that service's .ai/principles/ (+ umbrella override chain)
# → runs lint/test from that service's .ai/context/runbook.md
```

**working_dir path convention:**
Path is relative from the T-XX directory to the target service repo.
Example: task at `.ai/tasks/todo/task-01/T-01/description.md`
→ `working_dir: ../../../../service-api` resolves to `lattice_lab/service-api/`

**Single-service tasks** still run inside the service repo directly:
```
cd lattice_lab/service-api/
/phase-discovery .ai/specs/02-local-feature.md
```
Prefer this when a feature is entirely contained within one service.

## File Map

- `memory/architecture.md`  — system topology: services, boundaries, communication patterns
- `memory/state.md`         — cross-service tasks in flight (single-service tasks → service .ai/)
- `memory/progress.md`      — project-level history of significant milestones
- `principles/architecture.md` — shared architectural principles all services must follow
- `principles/coding.md`    — shared coding standards (stack defaults; services override per stack)
- `principles/domain.md`    — ubiquitous language and cross-service domain model
- `context/integrations.md` — external systems used by multiple services
- `context/environment.md`  — shared environments, infrastructure identifiers
- `adr/index.md`            — cross-cutting architectural decisions
- `specs/`                  — specs for tasks that span multiple services
- `tasks/todo/`             — active cross-repo task directories
- `tasks/completed/`        — finished cross-repo task directories
