# Orchestrail — USAGE

Source of truth for an AI-assisted SDLC pipeline deployed to three environments:
Windsurf, Claude Code, and Codex. Everything in this repository is plain markdown;
shell scripts only copy files around. There is no runtime.

---

## 1. System Overview

### What this is

A file-based system that turns "do task X" into a deterministic sequence of phases
with explicit state on disk. The AI assistant is constrained by:

- **Workflows** — slash-command definitions (`/phase-discovery`, `/pae-implement`, …)
  that describe step-by-step what the AI must do.
- **Rules** — always-on policies (`workflow-globals.md`, `language.md`) loaded into
  every conversation.
- **Principles** — domain-quality standards (`code-quality.md`, `python-standards.md`,
  `testing-standards.md`, `infra-standards.md`) loaded into every conversation.
- **Templates** — boilerplate. `AGENTS.md` and the `.ai/` skeleton are copied into a
  project by `setup-new-project.sh`; `subtask-description.md` and `spec.md` stay in this
  repository as reference skeletons the workflows reproduce inline.

### What problems it solves

| Problem                                              | Mechanism                                         |
|------------------------------------------------------|---------------------------------------------------|
| AI silently invents architecture                     | `/pd-design` forces 2–3 variants + user decision  |
| Long tasks lose context across sessions              | All progress in `state.md` / `plan.md` on disk    |
| Phase boundaries get blurred                         | Each phase is a separate slash command, stops at end |
| Inconsistent quality across projects                 | Always-on principles + per-project `CLAUDE.md`    |
| Three AI tools, three different config formats       | `sync.sh` deploys one source to all three         |
| Re-running a single step requires guesswork          | Child workflows callable directly; `## Guard` checks |
| Tests get written after the code, describing what was built instead of what was required | `/pae-tests` writes failing tests from Acceptance Criteria before `/pae-implement`; the RED set is frozen during implementation |
| One long session runs out of context halfway through a task    | `/spec-run` gives each subtask a fresh, narrowly-scoped agent; a long-lived Arbiter holds the project context the sub-agents deliberately lack |
| A finished task lands as one giant unreviewable diff            | One stacked branch and one pull request per subtask, each reviewable on its own |
| Tasks that should be split into pieces get done as one big mess | `/pd-decompose` enforces 3–15 steps, ≤8 subtasks  |

### How the pieces fit together

```
          ┌──────────────────────────────────────────────────┐
          │  ~/projects/orchestrail/                     │ ← source of truth (edit here)
          │                                                  │
          │  workflows/   rules/                             │
          │  principles/  templates/                         │
          └────────────────────────┬─────────────────────────┘
                                   │
                              sync.sh
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐
  │ Windsurf         │  │ Claude Code      │  │ Codex              │
  │ ~/.codeium/      │  │ ~/.claude/       │  │ (per-project       │
  │   windsurf/      │  │   skills/        │  │   AGENTS.md only — │
  │   global_*       │  │ ~/.claude/       │  │   no global store) │
  │                  │  │   CLAUDE.md      │  │                    │
  └──────────────────┘  └──────────────────┘  └────────────────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │
                          setup-new-project.sh
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  <project>/                  │
                    │    CLAUDE.md   (Claude)      │
                    │    AGENTS.md   (Codex)       │
                    │    .windsurf/rules/          │
                    │    .claude/skills/ (symlinks)│
                    │    tasks/                    │
                    └──────────────────────────────┘
```

---

## 2. Directory Structure

```
~/projects/orchestrail/
├── docs/USAGE.md                    this file
│
├── sync.sh                          deploy source → Windsurf + Claude + ~/.claude/CLAUDE.md
├── setup-new-project.sh             initialize a project (CLAUDE.md, AGENTS.md, rules, skills)
├── link-skills.sh                   workaround: symlink ~/.claude/skills/ into project
│
├── rules/                           always-on rules (deployed globally to Windsurf + Claude)
│   ├── workflow-globals.md          phase contract, canonical status formats, flow tiers
│   ├── workflow-reference.md        extended rationale + examples (model_decision trigger)
│   ├── tdd.md                       TDD contract: RED→GREEN, test-level gate, frozen test set
│   ├── git-flow.md                  branch stack, commits, PR policy, git safety rails
│   ├── orchestration.md             agent roles, context boundaries, class A/B escalation
│   ├── quick-flow.md                quick vs full tier, escalation gate
│   ├── language.md                  English in every project file (chat language is user-specific)
│   └── global-claude.md             contents written to ~/.claude/CLAUDE.md by sync.sh
│
├── principles/                      always-on engineering standards (Windsurf global_rules)
│   ├── code-quality.md              clean architecture, SOLID, naming, error handling, DI
│   ├── python-standards.md          types, Pydantic, async, FastAPI, SQLAlchemy, structlog
│   ├── testing-standards.md         test style: AAA, InMemory repos, coverage targets
│   └── infra-standards.md           IaC, Terraform layout, IAM, Docker, observability
│
├── workflows/                       slash-command definitions (deployed as Windsurf workflows
│   │                                  and Claude Code skills)
│   ├── PIPELINE.md                  reference doc (not executable)
│   ├── phase-pipeline.md            autonomous Discovery→Execution→Validation
│   ├── phase-discovery.md           Phase 1 orchestrator
│   ├── phase-execution.md           Phase 2 orchestrator
│   ├── phase-validation.md          Phase 3 orchestrator
│   ├── phase-atomic-execution.md    per-T-XX execution orchestrator
│   ├── phase-atomic-validation.md   per-T-XX validation orchestrator
│   ├── pd-analyze.md                Discovery step 1
│   ├── pd-decompose.md              Discovery step 2
│   ├── pd-design.md                 Discovery step 3
│   ├── pd-finalize.md               Discovery step 4
│   ├── pd-archive.md                Discovery step 4b — called by pd-finalize
│   ├── pd-select-model.md           Discovery step 2.5 — opt-in model selection
│   ├── pe-execute.md                Execution step 1
│   ├── pe-finalize.md               Execution step 2
│   ├── pv-contract.md               Validation step 1
│   ├── pv-review.md                 Validation step 2
│   ├── pv-issues.md                 Validation step 3
│   ├── pv-create-fixes.md           Validation step 4
│   ├── pv-execute-fixes.md          Validation step 5
│   ├── pv-finalize.md               Validation step 6
│   ├── pae-tests.md                 atomic-execution step 1 — TDD RED
│   ├── pae-implement.md             atomic-execution step 2 — TDD GREEN
│   ├── pae-finalize.md              atomic-execution step 3
│   ├── pav-check.md                 atomic-validation step 1
│   ├── pav-propose.md               atomic-validation step 2
│   ├── pav-close.md                 atomic-validation step 3
│   ├── spec-draft.md                standalone — raw task → development-ready SDD spec
│   ├── spec-sync.md                 reconcile a shipped implementation back into its spec
│   ├── bugfix.md                    governed defect path — reproduce → RED → fix → record
│   ├── adr-new.md                   write an ADR when the decision is made, not at task end
│   ├── context-pack.md              build one verified context pack from .ai/
│   ├── retro.md                     analyse the run log; report what to change in the workflows
│   ├── spec-run.md                  orchestrator — spec → stacked branches → PRs
│   ├── restack.md                   replay the stack after a merge
│   ├── pv-classify-fixes.md         validation step 4a — fix branch grouping
│   ├── phase-composite-validation.md integration check for a Type 2 composite
│   ├── onboard-legacy-project.md    one-time .ai/ initialization for a legacy project
│   ├── suggest-commit-message.md    utility — copy-ready commit message
│   ├── suggest-pr-description.md    utility — copy-ready PR description
│   ├── suggest-commit-pr.md         utility — both of the above in one call
│   └── compress-state.md            utility — compress a state file
│
└── templates/
    ├── AGENTS.md                    Codex template — copied to project root by setup script
    ├── subtask-description.md       T-XX/description.md skeleton
    ├── spec.md                      task spec template — copy to .ai/specs/<NN>-<slug>.md
    ├── .ai/                         project knowledge-base skeleton (memory/, principles/,
    │                                  context/, adr/, specs/, tasks/) seeded into a project
    │                                  by setup-new-project.sh — existing files are never touched
    └── .ai-umbrella/                umbrella-root skeleton, seeded by setup-umbrella.sh
```

### How each category is deployed

| Source                | Deployed to (Windsurf)                    | Deployed to (Claude Code)            | Deployed to (Codex)       |
|-----------------------|-------------------------------------------|--------------------------------------|---------------------------|
| `workflows/*.md`      | `~/.codeium/windsurf/global_workflows/`   | `~/.claude/skills/<name>/SKILL.md`   | `~/.codex/skills/<name>/SKILL.md` |
| `rules/*.md`          | `~/.codeium/windsurf/global_rules/`       | `~/.claude/skills/rule-<name>/SKILL.md`, plus `~/.claude/CLAUDE.md` from `global-claude` | `~/.codex/skills/rule-<name>/SKILL.md`, plus `~/.codex/AGENTS.md` |
| `principles/*.md`     | `~/.codeium/windsurf/global_rules/`       | `~/.claude/skills/principle-*/SKILL.md`   | `~/.codex/skills/principle-*/SKILL.md` |
| `templates/AGENTS.md` | —                                         | —                                    | `<project>/AGENTS.md`     |

| `templates/.ai-umbrella/` | —                                        | —                                    | —                         |

---

## 3. Multi-Repo Projects

For projects that contain multiple service repositories under one umbrella directory
(e.g., `~/projects/acme-platform/`), use two-level `.ai/`:

```
acme-platform/              ← umbrella root
├── .ai/                  ← shared context (architecture, principles, domain)
├── CLAUDE.md             ← umbrella context loading protocol
├── service-api/
│   ├── .ai/              ← service-specific context (state, tasks, overrides)
│   └── CLAUDE.md         ← two-level loading protocol (auto-generated)
├── service-worker/
│   ├── .ai/
│   └── CLAUDE.md
├── service-frontend/
│   ├── .ai/
│   └── CLAUDE.md
└── infra/
    ├── .ai/
    └── CLAUDE.md
```

### Setup sequence

```bash
# 1. Initialize the umbrella root
cd ~/projects/acme-platform
bash ~/projects/orchestrail/setup-umbrella.sh

# 2. Fill in the umbrella knowledge base
$EDITOR .ai/memory/architecture.md   # describe all services and how they interact
$EDITOR .ai/principles/coding.md     # shared coding standards
$EDITOR .ai/principles/domain.md     # ubiquitous language

# 3. Initialize each service repo (auto-detects ../.ai/)
cd service-api
bash ~/projects/orchestrail/setup-new-project.sh

cd ../service-worker
bash ~/projects/orchestrail/setup-new-project.sh
# ... repeat for each service
```

`setup-new-project.sh` detects `../.ai/` automatically and generates a `CLAUDE.md`
with two-level loading (umbrella first, local overrides second).

### What lives where

| Information | Umbrella `.ai/` | Service `.ai/` |
|---|---|---|
| How services interact | `memory/architecture.md` | — |
| This service's internals | — | `memory/architecture.md` |
| Active tasks | — | `memory/state.md` |
| Cross-service tasks | `memory/state.md` | — |
| Shared principles (all services) | `principles/` | — |
| Stack/domain overrides | — | `principles/` |
| Shared external systems | `context/integrations.md` | — |
| Service-specific integrations | — | `context/integrations.md` |
| How to run/deploy | — | `context/runbook.md` |
| Cross-cutting ADRs | `adr/index.md` | — |
| Service-specific ADRs | — | `adr/index.md` |
| Specs and tasks | — | `specs/`, `tasks/` |

---

## 4. Initial Setup (new machine / standalone project)

Clone the public repository to the Orchestrail checkout path:

```bash
git clone https://github.com/AlekseiChirkov/agentic-workflows.git ~/projects/orchestrail
bash ~/projects/orchestrail/sync.sh
```

The `v0.9.0` tag is intended for use after release. Once it is published, check it out
with `git -C ~/projects/orchestrail checkout v0.9.0`. Until then, use the default branch.

`sync.sh` runs `validate-contracts.sh` first and refuses to deploy if any check fails.
It then performs:

1. Copy `workflows/*.md` → `~/.codeium/windsurf/global_workflows/`
2. Copy `rules/*.md` and `principles/*.md` → `~/.codeium/windsurf/global_rules/`
3. For each `workflows/<name>.md` → `~/.claude/skills/<name>/SKILL.md`, each
   `principles/<name>.md` → `~/.claude/skills/principle-<name>/SKILL.md`, and each
   `rules/<name>.md` → `~/.claude/skills/rule-<name>/SKILL.md`.
   Also write/refresh `~/.claude/CLAUDE.md` from `rules/global-claude.md`.
   The `rule-` prefix is required: five basenames exist in both `workflows/` and `rules/`, so
   an unprefixed rule skill would overwrite the workflow skill of the same name.
4. The same three skill layouts under `~/.codex/skills/`, plus `~/.codex/AGENTS.md` from
   `templates/codex-global-AGENTS.md`.
5. Walk every project containing a `.devin/` directory: refresh its `.devin/rules/` and
   `.windsurf/rules/` copies, refresh `.claude/skills/` symlinks, delete local workflow
   copies that shadow the global ones, and ensure `.ai/` is in `.gitignore`.

Verify deployment:

```bash
ls ~/.codeium/windsurf/global_workflows/  | head
ls ~/.codeium/windsurf/global_rules/      | head
ls ~/.claude/skills/                      | head
ls -d ~/.claude/skills/rule-*             | head
ls -d ~/.codex/skills/rule-*              | head
cat ~/.claude/CLAUDE.md                   | head
```

In Windsurf or Claude Code, typing `/phase-discovery` should now autocomplete.

---

## 5. Adding the System to a Project

```bash
cd <project-root>
bash ~/projects/orchestrail/setup-new-project.sh
```

The script (idempotent — safe to re-run):

| Step | What it creates / modifies                                                                  |
|------|---------------------------------------------------------------------------------------------|
| 1    | `CLAUDE.md` — pointer form, or the two-level protocol when an umbrella `../.ai/` is detected |
| 2    | `.windsurf/rules/` **and** `.devin/rules/`: all twelve rule files — `workflow-globals`, `workflow-reference`, `language`, `quick-flow`, `tdd`, `git-flow`, `orchestration`, and the five `phase-*` context rules |
| 3    | Notes about `.windsurf/workflows/` — uses global workflows unless local override exists     |
| 4    | `.claude/skills/<name>` symlinks pointing at `~/.claude/skills/<name>` (Claude Code workaround) |
| 5    | `.ai/` knowledge base seeded from `templates/.ai/` (never overwrites existing files), then `AGENTS.md` for Codex from `templates/AGENTS.md` |
| 6    | `.gitignore` entries: `.ai/` (pipeline state is never committed), `.claude/skills/`, `.env`, `*.pyc`, `__pycache__/` |

### Manual steps required after the script runs

These cannot be auto-detected — fill them in by hand:

**`.ai/context/runbook.md → ## Commands`** — actual shell commands for this project:

```markdown
## Commands
test:      pytest tests/ -v
lint:      ruff check src/
typecheck: mypy src/
build:     docker build -t app .
```

Workflows (e.g. `pae-implement`) look up these by key in
`.ai/context/runbook.md → ## Commands` — not in `CLAUDE.md`. Missing keys are
tolerated, but lint/test automation will be skipped for whatever is missing.

**`CLAUDE.md → ## Standards`** — project-specific overrides only.
Global standards live in `~/.claude/CLAUDE.md`. Add overrides such as:

```markdown
## Standards
architecture:   repository pattern, no business logic in routers
naming:         snake_case files, PascalCase classes
error-handling: typed exceptions, no silent fallbacks
forbidden:      no global state, no print() in committed code
```

**`AGENTS.md → ## Project Context`** — what this project is, for Codex:

```markdown
## Project Context
What this project does:  Order management API with async event processing.
Primary stack:           Python 3.12, FastAPI, PostgreSQL, GCP Cloud Run, Terraform.
Key constraints:         Multi-tenant, GDPR, latency < 200ms p95.
```

**`AGENTS.md → ## Commands`** — same `test:` / `lint:` / `typecheck:` / `build:`
values as in `CLAUDE.md`. Codex reads them from `AGENTS.md` directly.

---

## 6. Daily Workflow — Task to Merged Code

### Step 0 — Write the spec

```bash
$EDITOR .ai/specs/01-task-jwt-auth.md
```

Spec filename standard: `<NN>-<kebab-name>.md` (NN = two-digit zero-padded
number, unique across all files in `.ai/specs/`).

Minimum required content:
- `# H1 title` — required. Used as task title in state.md and ADR.
- `## Acceptance Criteria` — strongly recommended. If absent, phase-discovery
  derives them in Step 1 and records them under `### Assumptions` (with
  `--step-by-step` it asks for confirmation instead).

The spec is immutable after Discovery starts. Write it carefully: goal, constraints,
acceptance criteria, out-of-scope. A template is available at `templates/spec.md`.

### Step 1 — Discovery

```
/phase-discovery .ai/specs/01-task-jwt-auth.md                  # autonomous (default)
/phase-discovery .ai/specs/01-task-jwt-auth.md --step-by-step   # review each step
```

By default the whole phase runs end-to-end without stopping: ambiguities are
resolved by research and logged in `### Assumptions`, and the architecture is
chosen by the Autonomous Decision Protocol and logged as `### Autonomous
Decision`. The final report includes a digest of everything decided without you.
Pass `--step-by-step` when you want to be asked — clarifying questions, a choice
between architectural variants, and a review pause after each of the four steps.

Discovery never auto-advances into Execution in either mode.

Sequence inside the phase (each is a callable child workflow):

1. `/pd-analyze` — reads root state files (`.ai/memory/architecture.md`,
   `.ai/memory/state.md`, `.ai/principles/architecture.md`), reads only the codebase parts that are
   not already described in those, resolves ambiguities by research and records each one in
   `### Assumptions` (asks clarifying questions only with `--step-by-step`), sets the `flow:`
   tier, and writes `## Task Analysis` to `state.md`.
2. `/pd-decompose` — splits the task into 1–8 T-XX subtasks (each with 3–15
   steps), creates `.ai/tasks/todo/task-01-task-jwt-auth/T-XX-<slug>/description.md` using
   the six-section template defined in the workflow itself (mirrored by
   `templates/subtask-description.md`), and writes the `## Subtasks` table to `plan.md`.
3. `/pd-design` — generates 2–3 architectural variants with trade-offs and selects one
   via the Autonomous Decision Protocol, recording `### Autonomous Decision` alongside
   `## Solution Design → ### Decision` in `state.md`. With `--step-by-step` it presents the
   variants and **waits for the user's choice** instead.
4. `/pd-finalize` — sanity-checks artifacts, runs `/compress-state`, marks
   `discovery: complete`.

**Phase output:**
- `state.md` — phases, task analysis, decision, subtask progress block per T-XX
- `plan.md` — T-XX table with statuses, dependencies, key-steps summary
- `T-XX-<slug>/description.md` for each subtask (only this file — no per-T-XX state)

**The phase STOPS here.** Print the next command for the user.

### Step 2 — Execution

```
/phase-execution .ai/tasks/todo/task-01-task-jwt-auth/
```

For each T-XX in `plan.md` (in dependency order):

1. `/phase-atomic-execution T-XX/description.md`
   - `/pae-tests` — **TDD RED.** Classifies the test level (`unit` / `integration` /
     `contract` / `smoke` / `none`), writes tests from `## Acceptance Criteria` following
     `T-XX/description.md → ## Test Plan`, runs them, and verifies each fails for the
     expected reason. Sets `atomic-tests: red`. Writes tests only — no implementation.
   - `/pae-implement` — **TDD GREEN.** Runs the `## Steps` from `T-XX/description.md` until
     every RED test passes, then refactors while green. The RED set is frozen: no deleting,
     skipping, or weakening tests to reach green. Updates `## Subtask Progress` in parent
     `state.md`. Stops on ambiguity per the trust mechanism in `workflow-globals.md`.
   - `/pae-finalize` — sets atomic-execution status to `complete`, updates `plan.md` to
     `done`, rolls up a composite parent if this subtask is one of its children, and
     compresses state. The lint/test run happens earlier, in `/pae-implement → Final
     Verification`, using the commands from `.ai/context/runbook.md → ## Commands`.
2. `/phase-atomic-validation T-XX/description.md`
   - `/pav-check` — verifies the implementation against `## Acceptance Criteria`, audits the
     RED test set, and issues a verdict: `DONE` or `NEEDS WORK`.
   - `/pav-propose` — proposes optional improvements categorized `Do Now` / `Do Later` /
     `Optional`. Called from the execution loop it runs with `--batch`: proposals are
     recorded and nothing is applied, and `/pe-finalize` surfaces the `Do Now` items at the
     end of the phase. Invoked standalone it **stops and waits for approval**.
   - `/pav-close` — marks atomic-validation `complete`, parent `plan.md` status `reviewed`.

After all T-XX done: `/pe-finalize` writes `## Execution Report`, marks
`execution: complete`. **Phase stops.**

### Step 3 — Validation

```
/phase-validation .ai/tasks/todo/task-01-task-jwt-auth/
```

1. `/pv-contract` — checks every `Invariant`, `Acceptance Criterion`, `Off-limits`
   item from `state.md`. Critical failures block validation.
2. `/pv-review` — code review: readability, architecture consistency vs.
   `principles/code-quality.md`, security, edge cases.
3. `/pv-issues` — compiles numbered issue list with priorities
   (`critical` / `important` / `optional`). **Stops, waits for user approve/defer.**
4. `/pv-create-fixes` — converts approved issues into `T-XX-fix-<slug>/description.md`
   subtasks. Updates `## Fix-Tasks` in `state.md`.
5. `/pv-execute-fixes` — runs atomic-execution + atomic-validation for each
   fix-task (same loop as Execution phase).
6. `/pv-finalize` — writes `## Deferred`, compresses state, marks
   `validation: complete`.

**Phase output:** clean code, all critical/important issues fixed, deferred
list documented, ADR optionally written.

### Step 4 — Ship

Once `validation: complete` — commit, push, open PR. The state files
(`state.md`, `plan.md`, per-T-XX descriptions) double as PR description material.

### Alternative — Fully autonomous pipeline

```
/phase-pipeline .ai/tasks/todo/task-01-task-jwt-auth/
```

Runs all three phases without phase boundaries. Architectural choices use the
**Deep Architectural Analysis Protocol** (5-lens scoring + anti-overengineering
filter, recorded as `### Autonomous Decision` in `state.md`). Pauses only for:

- Hard blockers (missing secret, unreachable service, missing requirement with
  no reasonable default)
- Breaking external-API-contract changes
- Genuinely ambiguous requirements in `pd-analyze`

All other ambiguity is resolved autonomously and documented in `notes:`.

### Interruption recovery

Re-run the same command. Every workflow reads `state.md → ## Phases` and
`## Subtask Progress`, finds the resume point, and continues. No flags. Never
restart.

---

## 7. Slash Commands Reference

Path argument syntax:
- `/phase-discovery`: `<path>` = path to spec file in `.ai/specs/`
- All other phase and child workflow commands: `<path>` = task directory (`.ai/tasks/todo/task-<NN>-<slug>/`)
- Atomic child workflows (`pae-*`, `pav-*`, `phase-atomic-*`): `<path>` = `T-XX/description.md`

### Phase orchestrators

| Command                       | What it does                                          | Reads                                          | Writes                                                          |
|-------------------------------|-------------------------------------------------------|------------------------------------------------|-----------------------------------------------------------------|
| `/phase-discovery <path> [--step-by-step]` | Runs Discovery steps 1–4; autonomous by default, `--step-by-step` pauses for review after each step | `spec (.ai/specs/*.md)`, root state files; creates `state.md` with `spec_path:` | `state.md`, `plan.md`, `T-XX/description.md`                    |
| `/phase-execution <path>`     | Runs atomic-execution + atomic-validation per T-XX    | `state.md`, `plan.md`, all `T-XX/description.md`| `state.md → ## Subtask Progress`, code changes                  |
| `/phase-validation <path>`    | Runs Validation steps 1–6                             | `state.md`, `plan.md`, codebase                | `## Contract Check`, `## Code Review`, `## Issue List`, `## Fix-Tasks`, `## Deferred`, fix-task code |
| `/phase-pipeline <path>`      | All three phases autonomously                         | same as above                                  | same as above + `### Autonomous Decision` blocks                |
| `/phase-atomic-execution <T>` | Implement one T-XX                                    | `T-XX/description.md`, parent `state.md`       | parent `state.md → ## Subtask Progress`, code                   |
| `/phase-atomic-validation <T>`| Validate one T-XX                                     | parent `state.md`, code                        | parent `state.md → ## Subtask Progress`, `plan.md` status       |

### Discovery children

| Command             | Step | What it does                                                                  | Writes                                                |
|---------------------|------|-------------------------------------------------------------------------------|-------------------------------------------------------|
| `/pd-analyze <p>`   | 1    | Read spec + root state, minimal code reading, record assumptions, set `flow:` (asks only with `--step-by-step`) | `state.md → ## Task Analysis`, `flow:`  |
| `/pd-decompose <p>` | 2    | Split into T-XX subtasks (3–15 steps each, ≤8 subtasks total)                 | `plan.md → ## Subtasks`, `T-XX/description.md` files  |
| `/pd-design <p>`    | 3    | 2–3 variants + trade-offs, decided by the Autonomous Decision Protocol (`--step-by-step` stops for the user) | `state.md → ## Solution Design → ### Decision` |
| `/pd-finalize <p>`  | 4    | Sanity check, compress, mark `discovery: complete`                            | `state.md → ## Phases`                                |

### Execution children

| Command            | Step | What it does                                              | Writes                                                  |
|--------------------|------|-----------------------------------------------------------|---------------------------------------------------------|
| `/pe-execute <p>`  | 1    | Loop atomic-execution + atomic-validation per T-XX        | code, `## Subtask Progress`                             |
| `/pe-finalize <p>` | 2    | Summary report, compress                                  | `state.md → ## Execution Report`, `## Phases`           |

### Validation children

| Command                  | Step | What it does                                                      | Writes                                                |
|--------------------------|------|-------------------------------------------------------------------|-------------------------------------------------------|
| `/pv-contract <p>`       | 1    | Check Invariants, Acceptance Criteria, Off-limits                 | `state.md → ## Contract Check`                        |
| `/pv-review <p>`         | 2    | Code review: readability, architecture, security, edge cases      | `state.md → ## Code Review`                           |
| `/pv-issues <p>`         | 3    | Numbered issue list with priorities; stop for user approve/defer  | `state.md → ## Issue List`                            |
| `/pv-create-fixes <p>`   | 4    | Generate `T-XX-fix-<slug>/description.md` subtasks                | `state.md → ## Fix-Tasks`, fix-task directories       |
| `/pv-execute-fixes <p>`  | 5    | Atomic-execute + atomic-validate each fix-task                    | code, `## Subtask Progress`                           |
| `/pv-finalize <p>`       | 6    | Compress, list deferred, mark `validation: complete`              | `state.md → ## Deferred`, `## Phases`                 |

### Atomic children

| Command               | Step | What it does                                                       | Writes                                                |
|-----------------------|------|--------------------------------------------------------------------|-------------------------------------------------------|
| `/pae-tests <T>`      | 1    | **TDD RED** — test-level gate, write failing tests from `## Acceptance Criteria`, observe them fail | test files, `## Subtask Progress → atomic-tests: red` |
| `/pae-implement <T>`  | 2    | **TDD GREEN** — execute the `## Steps` until the RED tests pass, then refactor | code, parent `state.md → ## Subtask Progress`         |
| `/pae-finalize <T>`   | 3    | Set atomic-execution status, update `plan.md`, roll up a composite parent | `## Subtask Progress`, `plan.md` status         |
| `/pav-check <T>`      | 1    | Verify against `## Acceptance Criteria`, issue verdict             | `## Subtask Progress → notes`                         |
| `/pav-propose <T>`    | 2    | Propose improvements (Do Now / Do Later / Optional); wait for user | `## Subtask Progress → notes`                         |
| `/pav-close <T>`      | 3    | Mark atomic-validation complete, `plan.md` status `reviewed`       | `## Subtask Progress`, `plan.md` status               |

### Utility

| Command                  | What it does                                                                |
|--------------------------|-----------------------------------------------------------------------------|
| `/compress-state [path]` | Compress a state file. Default target: `.ai/memory/state.md`. Preserves required-empty fields (`notes:`, `target_files:`) and everything in the Protected Sections Contract. |

### Rules every workflow obeys

(Defined in `rules/workflow-globals.md` — loaded into every conversation.)

- **Never auto-advance between phases** — except `/phase-pipeline`.
- **Test-first execution** — every leaf subtask goes through `/pae-tests` (RED) before
  `/pae-implement` (GREEN). The failing tests are a frozen contract, not a draft. Non-testable
  work passes an explicit, recorded gate. Contract: `rules/tdd.md`. Not suspended by
  `/phase-pipeline`.
- **Orchestrated mode** — `/spec-run` runs a whole spec with context-bounded sub-agents, one
  stacked branch per subtask, strictly sequential. Contracts: `rules/orchestration.md`,
  `rules/git-flow.md`. It never merges a PR, never pushes to the base branch, never commits
  `.ai/`.
- **Continue, never restart** — read `state.md` first, resume from last completed step.
- **Wait for user on ambiguity** — present 2–3 options with trade-offs.
- **Trust mechanism** — trivial → execute autonomously; non-trivial → stop and ask.
- **Strict adherence to artifacts** — implement exactly what Discovery produced.
- **Direct child-workflow invocation for re-runs** — no `--step=N` flag; each child has a `## Guard` that checks for already-completed work.

---

## 8. Updating the System

Edit only in `~/projects/orchestrail/`. Then re-sync.

```bash
$EDITOR ~/projects/orchestrail/principles/python-standards.md   # or any other file
bash ~/projects/orchestrail/sync.sh
```

`sync.sh` is idempotent. It re-copies everything; whatever was edited propagates
to all three environments on the next slash-command invocation:

- Windsurf reads from `~/.codeium/windsurf/global_workflows/` and `global_rules/`
- Claude Code reads from `~/.claude/skills/<name>/SKILL.md` and `~/.claude/CLAUDE.md`
- Codex reads `AGENTS.md` per project — the template is at
  `~/projects/orchestrail/templates/AGENTS.md`. To propagate template changes to
  *existing* projects, re-run `setup-new-project.sh` in each project (it does
  NOT overwrite an existing `AGENTS.md`; you must update each project's
  `AGENTS.md` manually or `rm AGENTS.md` first).

### What NOT to do

- Do **not** edit files in `~/.codeium/windsurf/global_workflows/`,
  `~/.codeium/windsurf/global_rules/`, `~/.claude/skills/`, or `~/.claude/CLAUDE.md`
  directly — they are overwritten by the next `sync.sh`.
- Do **not** edit `templates/AGENTS.md` and expect existing projects to update.
  Existing projects keep their own copy.

### Where each edit lands

| You edit                                    | Effect after `sync.sh`                                              |
|---------------------------------------------|---------------------------------------------------------------------|
| `workflows/<x>.md`                          | Windsurf workflow `/x` updated, Claude skill `x/SKILL.md` updated   |
| `rules/global-claude.md`                    | `~/.claude/CLAUDE.md` rewritten / appended; also redeployed as skill `rule-global-claude` |
| `rules/workflow-globals.md`                 | Windsurf rule updated; Claude Code and Codex skill `rule-workflow-globals` updated; project copies in `.windsurf/rules/` and `.devin/rules/` refreshed by the per-project pass |
| `rules/<x>.md` (any other rule)             | Windsurf global rule updated; Claude Code and Codex skill `rule-<x>` updated                |
| `principles/<x>.md`                         | Windsurf global rule updated; Claude Code and Codex skill `principle-<x>` updated           |
| `templates/AGENTS.md`                       | New projects get the new template; existing projects unaffected      |
| `setup-new-project.sh` / `sync.sh`          | Effective on next invocation                                        |

### Propagating rule changes to existing projects

Rules under `.windsurf/rules/` are *copies* (not symlinks). After editing
`rules/workflow-globals.md`:

```bash
cd <existing-project>
cp ~/projects/orchestrail/rules/workflow-globals.md .windsurf/rules/workflow-globals.md
```

Or re-run `setup-new-project.sh` after deleting the affected file.

---

## 9. File Roles Quick Reference

### Repository root

| File                       | Role                                                                              |
|----------------------------|-----------------------------------------------------------------------------------|
| `docs/USAGE.md`            | This document.                                                                    |
| `docs/SPEC-RUN-QUICKSTART.md` | Operating procedure for `/spec-run`: preflight, the batch gate, what stops the run, the branch stack you get, merging and `/restack`, interruption recovery. |
| `validate-contracts.sh`    | 551 contract checks across the three layers, including optional tracked-file public hygiene. Run by `sync.sh` before every deploy; any failure blocks deployment. |
| `sync.sh`                  | Deploy source → Windsurf workflows + rules, Claude skills, `~/.claude/CLAUDE.md`. Source tree defaults to the script directory; `--from <dir>` takes precedence over `ORCHESTRAIL_HOME`. |
| `validate-task.sh`         | Applies the canonical contracts to ONE task directory's artifacts (`state.md`, `plan.md`, `description.md`) rather than to the workflow definitions. Run by `/pd-finalize` and `/pe-finalize`; exit 1 blocks the phase. |
| `log-step.sh`              | Append-only run log writer. Stamps its own timestamps and derives durations, so no duration is ever model-guessed. Exits 0 on every error path — logging never blocks a pipeline. |
| `setup-new-project.sh`     | Initialize a project: `CLAUDE.md`, `AGENTS.md`, `.windsurf/rules/`, skill symlinks, `.gitignore`. |
| `link-skills.sh`           | Workaround for Claude bug: symlink `~/.claude/skills/` into project `.claude/skills/`. |

Keep private hygiene patterns in a local file outside the repository. Set
`ORCHESTRAIL_HYGIENE_DENYLIST` to its path, or place it at
`$XDG_CONFIG_HOME/orchestrail/hygiene-patterns.txt` (default:
`~/.config/orchestrail/hygiene-patterns.txt`). Never commit this file. Patterns are
literal case-insensitive substrings; comments and blank lines are ignored.

Run `bash validate-contracts.sh --hygiene-only` for the tracked-file scan alone. Use
`--root <repository>` and `--denylist <file>` to select a checkout or override the local
pattern file. Explicit scans fail closed when inputs are missing or unreadable, the
pattern file is empty, scanning fails, or the index is empty. The full contract suite
reports its two private-pattern scans as `SKIP` when no local patterns are configured;
its synthetic scanner fixtures always run. The scanner reads every indexed path,
including newly staged knowledge files and tracked logs, and scans symlink target text
without following it. Only the original source specification is exempt. Empty tracked
files are clean. Logs and local machine settings stay ignored in this repository.

### `rules/`

| File                       | Role                                                                              |
|----------------------------|-----------------------------------------------------------------------------------|
| `workflow-globals.md`      | Always-on. Phase contract, never-auto-advance, canonical status formats, flow tiers, fix-task format. Decomposition limits and the reference tables live in `workflow-reference.md`. |
| `workflow-reference.md`    | Model-decision trigger. Extended file-role reference, state-file marker list, status lifecycle. |
| `language.md`              | Always-on. Every project file in English. Chat language is deliberately NOT set here — it belongs in the user's personal `~/.claude/CLAUDE.md`. |
| `git-flow.md`              | Always-on. Branch stack, commit granularity, the no-attribution commit rule, PR policy (draft → ready), preflight, and every git safety rail. |
| `orchestration.md`         | Always-on. Roles (Orchestrator / Arbiter / Implementer / Validator), context boundaries, shared-file discipline, class A/B escalation, the Discovery batch gate. |
| `tdd.md`                   | Always-on. TDD contract: RED→GREEN cycle, test-level gate (unit/integration/contract/smoke/none), what counts as RED, frozen-test-set rule during GREEN, characterization mode (`pinned`) for behaviour-preserving work, `atomic-tests:` status vocabulary. |
| `run-log.md`               | Always-on. Run log contract: the central store, the three `log-step.sh` calls, the field vocabulary, what must never be logged, and the rule that logging never blocks a run. |
| `quick-flow.md`            | Always-on. Quick vs full tier: four-condition escalation gate, what the quick path skips and still mandates (inline contract + inline TDD step), mid-flight promotion to full. |
| `phase-discovery.md`, `phase-execution.md`, `phase-validation.md`, `phase-atomic-execution.md`, `phase-atomic-validation.md` | Model-decision trigger. Per-phase Context Bootstrap (which `.ai/` files to load, in what order), phase behaviours, and — for atomic execution — the Blocker Reconciliation procedure. Every phase workflow cites these by name. |
| `global-claude.md`         | Content for `~/.claude/CLAUDE.md`. Architecture principles + Python/testing/infra/naming/forbidden summaries. |

### `principles/`

| File                       | Role                                                                              |
|----------------------------|-----------------------------------------------------------------------------------|
| `code-quality.md`          | Always-on. Clean layered architecture, SOLID, naming, functions/classes, error handling, Repository pattern, DI, forbidden list. |
| `python-standards.md`      | Always-on. Type hints, Pydantic v2, async rules, FastAPI patterns, SQLAlchemy 2.0 async, structlog, project structure, Python forbidden list. |
| `testing-standards.md`     | Always-on. Test *style*: behavior-not-implementation, AAA, InMemory repos, layer coverage targets, naming, edge cases. Maps the TDD sequence onto the workflows that execute it (`rules/tdd.md` owns the *process*). |
| `infra-standards.md`       | Always-on. IaC general rules, Terraform layout, IAM least privilege, Docker, observability, config.|

### `workflows/`

| File                            | Role                                                                              |
|---------------------------------|-----------------------------------------------------------------------------------|
| `PIPELINE.md`                   | Reference doc (not executable). Full pipeline overview, status glossary, child-workflow table. |
| `phase-pipeline.md`             | Autonomous Discovery → Execution → Validation. Includes Deep Architectural Analysis Protocol. |
| `phase-discovery.md`            | Discovery orchestrator. Sequentially calls `pd-analyze`, `pd-decompose`, `pd-design`, `pd-finalize`. |
| `phase-execution.md`            | Execution orchestrator. Loops atomic-execution + atomic-validation per T-XX, then `pe-finalize`. |
| `phase-validation.md`           | Validation orchestrator. Sequentially calls `pv-contract` … `pv-finalize`.        |
| `phase-atomic-execution.md`     | Single T-XX execution: `pae-tests` → `pae-implement` → `pae-finalize`.            |
| `phase-atomic-validation.md`    | Single T-XX validation: `pav-check` → `pav-propose` → `pav-close`.                |
| `pd-analyze.md`                 | Discovery step 1: read spec + root state + minimal code, record assumptions, set the `flow:` tier, write `## Task Analysis`. |
| `pd-decompose.md`               | Discovery step 2: split into 1–8 T-XX subtasks, create `T-XX/description.md` (six sections, incl. `## Test Plan`), write `plan.md → ## Subtasks`. |
| `pd-design.md`                  | Discovery step 3: generate 2–3 architectural variants and decide via the Autonomous Decision Protocol (`--step-by-step` waits for the user). |
| `pd-finalize.md`                | Discovery step 4: sanity check, compress, set `discovery: complete`, invoke `pd-archive`, update root files. |
| `pd-archive.md`                 | Discovery step 4b: move `## Task Analysis` (except `### Assumptions`), `### Variants` and `### Rejected` into `state-archive.md`, leaving pointer lines. Called by `pd-finalize` — never before `discovery: complete`. |
| `pd-select-model.md`            | Discovery step 2.5 (opt-in): score each subtask and recommend a model per subtask. Bulk mode writes the `Model` column in `plan.md`; `/spec-run` calls it, `/phase-discovery` does not. |
| `pe-execute.md`                 | Execution step 1: per-T-XX atomic-execution → atomic-validation loop.             |
| `pe-finalize.md`                | Execution step 2: write `## Execution Report`, mark `execution: complete`.        |
| `pv-contract.md`                | Validation step 1: verify Invariants, Acceptance Criteria, Off-limits.            |
| `pv-review.md`                  | Validation step 2: code review (readability, architecture, security, edge cases). |
| `pv-issues.md`                  | Validation step 3: numbered issue list with priorities, wait for user decision.   |
| `pv-create-fixes.md`            | Validation step 4: create fix-task directories from approved issues.              |
| `pv-execute-fixes.md`           | Validation step 5: run atomic cycles for each fix-task.                           |
| `pv-finalize.md`                | Validation step 6: compress, list deferred, mark `validation: complete`.          |
| `pae-tests.md`                  | Atomic-execution step 1 (TDD RED): classify test level, write failing tests from `## Acceptance Criteria`, run them, verify they fail for the expected reason. |
| `pae-implement.md`              | Atomic-execution step 2 (TDD GREEN): run the `## Steps` from `T-XX/description.md` until the RED tests pass, then refactor. |
| `pae-finalize.md`               | Atomic-execution step 3: update statuses in parent `state.md` + `plan.md`, roll up a composite parent, compress. |
| `pav-check.md`                  | Atomic-validation step 1: check against Acceptance Criteria, find bugs, issue verdict. |
| `pav-propose.md`                | Atomic-validation step 2: propose Do Now / Do Later / Optional improvements; wait for user. |
| `pav-close.md`                  | Atomic-validation step 3: mark complete, parent `plan.md` status `reviewed`.      |
| `spec-draft.md`                 | Standalone SDD authoring: a raw task (link, text, or file) → one development-ready spec in `.ai/specs/`. Interactive by default, autonomous with `--auto-mode`. Isolated — creates no task directory and starts no pipeline. |
| `spec-sync.md`                  | Reconcile a finished task's implementation back into its spec. The only workflow permitted to write a spec after Discovery starts; every edit carries a citation to the state file that recorded the divergence. Called by `/pv-finalize`, runnable standalone. |
| `bugfix.md`                     | Governed entry point for a defect: reproduce → freeze the reproduction as a failing test → fix → verify → record. Runs the quick tier; hands over to the full path when the quick gate returns `full`. |
| `adr-new.md`                    | Write an ADR at the moment the decision exists, from a task directory or a bare decision. `--provisional` records a Discovery decision before the task finishes; `/pv-finalize` promotes it instead of writing a second record. |
| `context-pack.md`               | Assemble bootstrap sources 1–7 into one manifest-verified `.ai/context-pack.md`. A step may read it instead of the seven files, only after confirming freshness. |
| `retro.md`                      | The only reader of the run log. Aggregates runs across projects and reports what to change in the workflows, with the evidence each finding rests on. |
| `spec-run.md`                   | Orchestrator: one spec → stacked branch per subtask → review-ready PRs, via context-bounded sub-agents. |
| `restack.md`                    | Replay the branch stack after the human merges part of it — works with merge, rebase, or squash. |
| `pv-classify-fixes.md`          | Validation step 4a: classify fixes into shared vs dedicated branches using the quick-flow gate. |
| `phase-composite-validation.md` | Integration validation for a Type 2 composite, after every child is individually reviewed. Triggered by `pav-close` when the last child closes. |
| `onboard-legacy-project.md`     | One-time: analyze an existing codebase and fill every `.ai/` file so later phases start from context instead of re-reading the code. Run after `setup-new-project.sh`. |
| `suggest-commit-message.md`     | Utility: copy-ready commit message for the current changes (session context by default, git with a flag). |
| `suggest-pr-description.md`     | Utility: copy-ready PR description — summary, how it works, how to test. |
| `suggest-commit-pr.md`          | Utility: runs both of the above with the same arguments. |
| `compress-state.md`             | Utility: remove stale state-file content while preserving required-empty fields and the Protected Sections Contract. |

### `templates/`

| File                       | Role                                                                              |
|----------------------------|-----------------------------------------------------------------------------------|
| `AGENTS.md`                | Codex template copied to project root. Contains Role, Project Context (TODO), Commands (TODO), Workflow, full set of standards. |
| `subtask-description.md`   | T-XX subtask description skeleton — all six sections: Goal, Context, Scope, Steps (3–15), Acceptance Criteria, Test Plan. Reference skeleton only; it is not copied into projects. |
| `spec.md`                  | Task spec template: H1 title, Goal, Acceptance Criteria, Out of Scope, Notes. Copy to `.ai/specs/<NN>-<slug>.md`. |

---

## 10. Status & Contract Quick Reference

### Subtask statuses in `plan.md`

| Status        | Meaning                                                  |
|---------------|----------------------------------------------------------|
| `not-started` | Not touched                                              |
| `in-progress` | Atomic execution running                                 |
| `done`        | Execution complete, validation not run                   |
| `reviewed`    | Execution + atomic validation both passed                |
| `blocked`     | External dependency / invariant conflict                 |
| `deferred`    | User chose to postpone                                   |
| `not-reached` | Session ended before this subtask was reached            |

### Phase statuses in `state.md → ## Phases`

`not-started` | `in-progress` | `complete`

### `## Subtask Progress` block (one per T-XX)

```
T-XX | <name> | atomic-tests: <status> | atomic-execution: <status> | atomic-validation: <status>
  last_action: <one line>
  target_files: <comma-separated, write even when empty>
  blocker: <none | description>
  notes: <decisions or deviations, write even when empty>
```

Atomic statuses (`atomic-execution` / `atomic-validation`):
`not-started` | `in-progress` | `complete` | `blocked` | `skipped` | `failed`.

`atomic-tests` statuses: `not-started` | `red` | `green` | `n-a` | `failed`.
A block written before the TDD step existed has no `atomic-tests:` line; read it as
`not-started` and do not error.

Under `/spec-run` the block also carries `branch:`, `base_branch:`, `base_commit:`,
`commits:`, and `pr:`. Composite subtasks use a `[composite]` block with
`rollup:` / `integration-validation:` / `children:` instead of the three atomic status fields.

### `## Fix-Tasks` block

```
## Fix-Tasks
fixes-created: complete
fixes-count: <N>
Created: T-XX-fix-<slug>, ...
```

When none: `fixes-count: 0` and `Created: none`.

Full canonical formats: `rules/workflow-globals.md`.
Extended rationale + examples: `rules/workflow-reference.md`.
