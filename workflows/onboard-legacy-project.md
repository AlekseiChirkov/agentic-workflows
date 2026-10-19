---
description: One-time knowledge-base initialization for legacy projects — analyze codebase, fill all .ai/ files so AI agents can start from context instead of re-reading the code
---

Invocation: `/onboard-legacy-project`
No arguments required. Run from the project root after `setup-new-project.sh`.

To resume a partially completed onboarding, invoke again — the workflow detects progress and skips completed phases.

---

## Phase 0 — Pre-flight

### 0.1 — Infrastructure check

Verify `setup-new-project.sh` was already run:

```bash
ls .ai/memory/ .ai/context/ .ai/principles/ .ai/adr/ .ai/specs/ .ai/tasks/ 2>/dev/null
ls CLAUDE.md AGENTS.md 2>/dev/null
```

If any directory is missing → **stop**:
"Run `bash <workflow-source>/setup-new-project.sh` first, then invoke `/onboard-legacy-project` again."

### 0.2 — Resume detection

Check for `.ai/onboarding-progress.md`:
- If absent → this is a fresh run. Create it with the content below and proceed to Phase 1.
- If present → read it. Determine the last completed phase (marked `✓`). Skip completed phases and resume from the next incomplete one.

Create `.ai/onboarding-progress.md`:

```markdown
# Onboarding Progress

## Phases
- [ ] Phase 1 — Codebase Exploration
- [ ] Phase 2 — Write Knowledge Base Files
- [ ] Phase 3 — Quality Check

## Notes
Started: <today's date and time>
```

### 0.3 — Stub detection

For each `.ai/` file that already exists, classify it:
- **Stub** — body contains only `## Purpose` / `## Structure` boilerplate with no real content. Will be filled.
- **Filled** — has real project-specific content. Will be **skipped** (do not overwrite).
- **Missing** — file does not exist. Will be created.

List your classification before proceeding. Ask the user before overwriting any filled file.

---

## Phase 1 — Codebase Exploration

**Rule: explore first, write nothing until Phase 2.**
For every step below, record findings in working memory (do not write to `.ai/` yet).

### 1.1 — Project identity

Read `README.md` (root and all immediate subdirectory READMEs):

```bash
find . -maxdepth 2 -name "README.md" -not -path './.git/*' | sort
```

Extract:
- What the system does — one clear paragraph
- Who uses it (end users, other systems, developers)
- Any stated architectural goals or constraints

### 1.2 — Repository structure

```bash
find . -maxdepth 4 \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './__pycache__/*' \
  -not -path './.ai/*' \
  -not -path './.claude/*' \
  -not -path './venv/*' \
  -not -path './.venv/*' \
  -not -path './dist/*' \
  -not -path './build/*' \
  -not -path './.tox/*' \
  -not -path './target/*' \
  | sort
```

From this output, determine:
- Repository type: single service / monorepo / library / CLI tool / data pipeline
- Top-level layout: identify each root directory and its purpose
- Source roots: `src/`, `app/`, `lib/`, `packages/`, `services/`, `internal/`, `cmd/`, or equivalent

### 1.3 — Stack and dependencies

Read every dependency manifest you find:

| Language | Files to read |
|----------|---------------|
| Python | `requirements*.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile` |
| Node/TS | `package.json`, `yarn.lock`, `pnpm-lock.yaml` |
| Go | `go.mod` |
| Ruby | `Gemfile` |
| Rust | `Cargo.toml` |
| Java/Kotlin | `pom.xml`, `build.gradle`, `build.gradle.kts` |
| PHP | `composer.json` |

From dependencies, identify:
- **Language and runtime version** (look for `python_requires`, `engines.node`, `go`, `rust-edition`)
- **Web framework**: FastAPI, Django, Flask, Express, NestJS, Gin, Echo, Rails, Spring Boot, Laravel, …
- **Database / ORM**: SQLAlchemy, Django ORM, Prisma, GORM, ActiveRecord, Hibernate, TypeORM, …
- **Testing framework**: pytest, jest, vitest, go test, rspec, JUnit, PHPUnit, …
- **Linting / formatting**: ruff, flake8, black, eslint, prettier, golangci-lint, rubocop, …
- **Type checking**: mypy, tsc, pyright, …
- **Task runners / build tools**: make, just, gradle, tox, nx, turborepo, …
- **Async model**: sync, async/await, goroutines, threads

### 1.4 — Entry points and application boundaries

Look for:
```bash
find . -maxdepth 4 -not -path './.git/*' -not -path './node_modules/*' \
  \( -name "main.py" -o -name "main.go" -o -name "main.ts" -o -name "index.ts" \
     -o -name "app.py" -o -name "server.py" -o -name "wsgi.py" -o -name "asgi.py" \
     -o -name "manage.py" -o -name "cli.py" -o -name "__main__.py" \) | sort
```

Also search for `cmd/`, `bin/`, `scripts/` directories.

Read the main entry point(s). Identify:
- How the HTTP server / message consumer / CLI starts
- Top-level interfaces exposed: HTTP routes, CLI commands, queue consumers, cron jobs, gRPC services

### 1.5 — Architecture layers

Identify which layers exist and how they are separated.
Scan directory names and a few representative files per layer:

| Pattern to look for | Common directory names |
|---------------------|----------------------|
| API / transport | `routers/`, `controllers/`, `handlers/`, `views/`, `api/`, `endpoints/` |
| Application / service | `services/`, `use_cases/`, `commands/`, `queries/`, `application/` |
| Domain / business | `models/`, `domain/`, `entities/`, `core/` |
| Infrastructure | `repositories/`, `adapters/`, `clients/`, `gateways/`, `infrastructure/` |
| Cross-cutting | `middleware/`, `auth/`, `logging/`, `config/`, `errors/`, `utils/` |

Determine which architectural pattern is followed (or absence of one):
- Clean Architecture / Hexagonal
- MVC / MVT
- Flat (all in one layer)
- Feature-based modules

Note any violations: business logic in routers? DB queries in controllers? Mixed concerns?

### 1.6 — Data layer

Find schema definitions:
```bash
find . -maxdepth 6 -not -path './.git/*' \
  \( -name "*.sql" -o -name "*.prisma" -o -path "*/migrations/*" -o -path "*/alembic/*" \
     -o -name "schema.rb" -o -name "*.dbml" \) | sort
```

Also find ORM model files by reading directories identified in 1.5 as domain/models layer.

Extract:
- Database type: PostgreSQL, MySQL, SQLite, MongoDB, Redis, DynamoDB, …
- Schema management tool: Alembic, Django migrations, Flyway, golang-migrate, Prisma, ActiveRecord, …
- Main entities/tables — for each: what it represents, key fields, relationships
- Is there a multi-tenant pattern? Soft deletes? Audit timestamps?

### 1.7 — External integrations

Search for client and adapter patterns:
```bash
# HTTP clients
grep -rn "requests\.\|httpx\.\|axios\.\|fetch(\|urllib\.\|http\.get\|http\.post" \
  --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rb" \
  -l . 2>/dev/null | grep -v test | grep -v spec | head -20

# Message brokers
grep -rn "kafka\|rabbitmq\|pika\|celery\|kombu\|sqs\|pubsub\|nats\|redis.*queue\|rq\." \
  --include="*.py" --include="*.ts" --include="*.js" --include="*.go" -l . 2>/dev/null | head -10

# Common providers
grep -rn "stripe\|twilio\|sendgrid\|mailgun\|ses\|s3\|gcs\|azure\|sentry\|datadog\|opentelemetry\|auth0\|cognito\|firebase" \
  --include="*.py" --include="*.ts" --include="*.js" --include="*.go" -il . 2>/dev/null | head -20
```

For each integration found: which files use it, what it does, what credentials it needs.

### 1.8 — Configuration and environments

```bash
find . -maxdepth 4 -not -path './.git/*' \
  \( -name ".env.example" -o -name ".env.template" -o -name ".env.sample" \
     -o -name "settings.py" -o -name "config.py" -o -name "config.go" \
     -o -name "application.yml" -o -name "application.yaml" \
     -o -name "config.yaml" -o -name "config.yml" \
     -o -name "appsettings.json" -o -name "fly.toml" -o -name "railway.toml" \
     -o -name "render.yaml" -o -name "Procfile" \) | sort
```

Also find deployment config:
```bash
find . -maxdepth 4 -not -path './.git/*' \
  \( -name "Dockerfile" -o -name "docker-compose*.yml" -o -name "docker-compose*.yaml" \
     -o -path "*/k8s/*" -o -path "*/kubernetes/*" -o -path "*/helm/*" \
     -o -path "*/terraform/*" -o -path "*/infra/*" \) | sort
```

Extract:
- All required environment variables (name + purpose + secret/non-secret)
- Distinct environments (local / dev / staging / production)
- How the app detects its environment
- Infrastructure type: bare VM, Docker, K8s, Cloud Run, Lambda, Heroku, Fly.io, …

### 1.9 — Test suite

```bash
find . -maxdepth 5 -not -path './.git/*' \
  \( -path "*/tests/*" -o -path "*/test/*" -o -path "*/spec/*" -o -path "*/__tests__/*" \) \
  -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.go" -o -name "*.rb" \
  2>/dev/null | sort | head -30
```

Also check:
```bash
# Find test runner configuration
find . -maxdepth 2 -not -path './.git/*' \
  \( -name "pytest.ini" -o -name "setup.cfg" -o -name "pyproject.toml" \
     -o -name "jest.config.*" -o -name "vitest.config.*" \
     -o -name ".mocharc*" -o -name "Makefile" -o -name "justfile" \) | sort
```

Read `Makefile` or `justfile` if present — extract all `test:`, `lint:`, `build:`, `migrate:` targets.
Read `package.json → scripts` section if present.

Identify:
- Test types present: unit, integration, e2e, contract
- Test runner command (with flags)
- Coverage configuration (any coverage threshold?)
- Whether test suite can run without external services (mocked vs real)

### 1.10 — CI/CD pipeline

```bash
find . -maxdepth 4 -not -path './.git/*' \
  \( -path "*/.github/workflows/*.yml" -o -path "*/.github/workflows/*.yaml" \
     -o -name ".gitlab-ci.yml" -o -name "Jenkinsfile" \
     -o -path "*/.circleci/config.yml" -o -name ".drone.yml" \
     -o -name "azure-pipelines.yml" \) | sort
```

Read each CI file. Extract:
- What runs on every PR (lint, typecheck, test, build, deploy-to-staging)
- What triggers a production deploy
- Branch naming standards, protected branches
- Any secrets required by CI (names only — values are secrets)

### 1.11 — Standards and patterns

Scan 5–10 representative source files across different layers. Look for:

**Naming**:
```bash
# Get a sample of source filenames to detect naming standard
find . -maxdepth 5 -not -path './.git/*' -not -path './node_modules/*' \
  \( -name "*.py" -o -name "*.ts" -o -name "*.go" \) | \
  grep -v test | grep -v spec | grep -v migration | head -30
```

**Error handling** — grep for exception/error patterns:
```bash
grep -rn "raise\|except\|throw\|catch\|Result<\|error.wrap" \
  --include="*.py" --include="*.ts" --include="*.go" \
  -l . 2>/dev/null | grep -v test | head -10
```
Read 2–3 of these files to see the error handling pattern.

**Logging** — grep for logger usage:
```bash
grep -rn "logger\.\|logging\.\|log\.\|console\.log\|fmt\.Printf\|slog\." \
  --include="*.py" --include="*.ts" --include="*.go" \
  . 2>/dev/null | grep -v test | head -10
```

**Dependency injection** — look for DI container or constructor injection patterns.

**Forbidden patterns already present** — collect evidence of known anti-patterns:
```bash
grep -rn "print(" --include="*.py" . 2>/dev/null | grep -v test | grep -v "#" | head -10
grep -rn "TODO\|FIXME\|HACK\|XXX" \
  --include="*.py" --include="*.ts" --include="*.go" --include="*.rb" \
  . 2>/dev/null | head -30
```

### 1.12 — Domain language

From README, model names, route names, and function names — extract domain vocabulary:
- Key domain nouns with precise project-specific meanings
- Terms used ambiguously or differently from their common meaning
- Business rules enforced in code: validations, status transition guards, conditional invariants

Search for status/state enumerations:
```bash
grep -rn "class.*Status\|class.*State\|class.*Type\|Enum\|enum\|IntEnum" \
  --include="*.py" --include="*.ts" --include="*.go" \
  . 2>/dev/null | grep -v test | head -20
```

### 1.13 — Architectural decisions in code

Look for evidence of deliberate choices:
- Framework / ORM / database choice (why not the obvious alternative — any comments?)
- Async vs sync choice
- Monolith vs services split (if split: what was the boundary criterion?)
- Auth approach: JWT, sessions, API keys — find the implementation
- Any HACK/FIXME comments that indicate known architectural debt (collected in 1.11)

### 1.14 — Surface-level security scan

Run these quick checks. Flag findings — do not fix, just record for principles/coding.md:

```bash
# Hardcoded secrets candidates
grep -rn "password\s*=\s*['\"].\|api_key\s*=\s*['\"].\|secret\s*=\s*['\"].\|token\s*=\s*['\"]." \
  --include="*.py" --include="*.ts" --include="*.go" --include="*.js" \
  . 2>/dev/null | grep -v test | grep -v ".env" | grep -v "example" | head -10

# SQL string formatting (injection risk)
grep -rn "f['\"].*SELECT\|f['\"].*INSERT\|f['\"].*UPDATE\|f['\"].*DELETE\|% .*cursor\|format.*query" \
  --include="*.py" . 2>/dev/null | grep -v test | head -10

# CORS wildcard
grep -rn "allow_origins.*\[\"\*\"\]\|Access-Control-Allow-Origin.*\*" \
  --include="*.py" --include="*.ts" --include="*.go" . 2>/dev/null | head -5
```

Record any hits as `Known Risk` entries — these go into `principles/coding.md → ## Forbidden Patterns` as warnings.

---

## Phase 2 — Write Knowledge Base Files

Write each file in the order below. For each:
- If already **filled** (detected in Phase 0.3) → skip it: output "already filled — skipped."
- Write real content derived solely from Phase 1 findings.
- Use `unknown — needs manual input` for any field where you found no evidence.
- Do not pad with guesses. Accurate and incomplete beats complete and wrong.

After writing each file, mark its phase in `.ai/onboarding-progress.md` so the session can resume.

---

### File 1 — `.ai/memory/architecture.md`

```markdown
# architecture.md — current snapshot of the system's architecture

## Overview
<One paragraph: what the system does, who uses it, how the major parts fit together.
Derived from README + entry-point files.>

## Components

### <Layer or Component Name>
**Responsibility:** <what it does>
**Key files / directories:** <list>
**Interfaces:** <what it exposes to other layers>
**Dependencies:** <what it depends on>

<Repeat for each major layer found in Phase 1.5>

## Data Flow
<Narrative: how a request/event enters the system, passes through layers,
reaches persistence, and returns a response. Use the layer names from ## Components.>

## Data Model
<List main entities/tables with one-line descriptions.>
<e.g. — User: registered account; Order: confirmed purchase with line items>

## External Dependencies
<One entry per integration found in Phase 1.7:>
<- ServiceName: purpose, which files use it>
```

---

### File 2 — `.ai/context/runbook.md`

```markdown
# runbook.md — operational procedures

## Commands
test:      <exact command>
lint:      <exact command>
typecheck: <exact command or "not configured">
build:     <exact command or "not applicable">
migrate:   <exact command or "not applicable">
seed:      <exact command or "not applicable">

## Local Development
<Step-by-step: fresh checkout → running app.
e.g. copy .env.example → .env, fill required vars, docker compose up, migrate, start server.>

## Environments
| Environment | URL/Host | Deploy trigger | Notes |
|-------------|----------|----------------|-------|
| local       | ...      | manual         | ...   |
| staging     | ...      | ...            | ...   |
| production  | ...      | ...            | ...   |

## Common Operations
<Subsections for known operational procedures: deploy, rollback, DB restore, etc.
Leave blank if none found.>
```

---

### File 3 — `.ai/context/integrations.md`

```markdown
# integrations.md — external systems this project integrates with

## Integrations

### <Integration Name>
- **Purpose:** <what it does for this system>
- **Protocol:** <HTTP REST / GraphQL / gRPC / SDK / message queue>
- **Auth:** <API key / OAuth2 / IAM role / …> — env var: `<VAR_NAME>`
- **Key files:** <where the client / adapter lives>
- **Notes:** <rate limits, retry policy, sandbox vs prod, anything non-obvious>

<Repeat for each integration found in Phase 1.7.
If none found — write "No external integrations detected.">
```

---

### File 4 — `.ai/context/environment.md`

```markdown
# environment.md — runtime environments and configuration

## Environments

### Local
- **Purpose:** development
- **Start:** <how to start locally>
- **Notes:** <any local-only quirks>

### <Staging / Dev / Preview>
- **URL:** <if known>
- **Deploy trigger:** <merge to X branch / manual / CI>

### Production
- **URL:** <if found in CI or README>
- **Deploy trigger:** <if found>
- **Infra:** <Dockerized? Cloud Run? EC2? Kubernetes? Heroku? Fly.io?>

## Required Environment Variables

| Variable | Purpose | Secret? | Default |
|----------|---------|---------|---------|
| <VAR>    | <what>  | yes/no  | <value or "none"> |

<Populate from .env.example / settings files found in Phase 1.8.>

## Secrets Management
<Where secrets live: .env file / GCP Secret Manager / AWS Secrets Manager / Vault / CI secrets / …>
```

---

### File 5 — `.ai/principles/architecture.md`

```markdown
# architecture.md — architectural principles for this project

## Principles

### Layering
**Rule:** <layer boundary rule — e.g. "routers may not import repositories directly">
**Rationale:** <why — from observed pattern or README>
**Observed structure:** <actual directory → directory dependency flow>

### <Any other principle found — one subsection per principle>
<e.g. Repository Pattern, CQRS, Event-driven, Async-first, Hexagonal, …>
**Rule:** <rule>
**Rationale:** <rationale>

### Known Violations / Technical Debt
<List architectural violations visible in the codebase.
These are things future AI agents must know exist but must NOT replicate.>
<e.g. "UserService directly imports db session — bypasses repository layer.
Do not replicate this pattern; fix it when touching user flows.">
```

---

### File 6 — `.ai/principles/coding.md`

```markdown
# coding.md — coding standards specific to this project

## Standards

### Naming
<File naming standard, class naming, function naming, variable naming.
e.g. snake_case files, PascalCase classes, snake_case functions and variables>

### Error Handling
<Pattern observed: typed exceptions / generic Exception / error-tuple / Result type.
Where errors are caught. What is logged vs re-raised.>

### Logging
<Library used, log levels, structured fields present in log calls.>

### Dependency Injection
<Pattern: constructor injection / DI container / module-level singletons. Examples.>

### Testing Standards
<Test file naming, fixture approach, mock vs real implementations, test structure.>

### Forbidden Patterns
<Patterns to never replicate — based on HACK/FIXME inventory and Phase 1.14 security scan.
e.g.:
- No print() in committed non-test code (use logger)
- No hardcoded credentials (use env vars)
- No direct DB queries in route handlers (use repository layer)
- No raw string formatting in SQL queries (use parameterized queries)
>
```

---

### File 7 — `.ai/principles/domain.md`

```markdown
# domain.md — domain-specific principles and vocabulary

## Vocabulary

| Term | Precise meaning in this project |
|------|---------------------------------|
| <term> | <definition from models, routes, README> |

<Add every domain noun found in Phase 1.12.
If no domain language detected — write:
"Domain vocabulary not yet documented — add terms as they are discovered.">

## Invariants

<Business rules enforced in code. One per bullet.>
<e.g.:>
<- An Order may not be cancelled after it reaches status "shipped".>
<- A User must have a verified email before placing an Order.>
<Derive from model validations, status guards, service-layer conditions.>
<If none found — write "No explicit invariants detected — add as discovered.">

## Status / State Machines
<If any domain objects have a status field with defined transitions, document them here.
e.g. Order: draft → confirmed → shipped → delivered | cancelled>
```

---

### File 8 — `.ai/adr/index.md` + `0001-initial-onboarding.md`

Update `.ai/adr/index.md`:

```markdown
# index.md — index of architectural decision records

## Records

| Number | Title | Status | Date | Link |
|--------|-------|--------|------|------|
| 0001   | Initial architecture onboarding | Accepted | <today's date> | [0001-initial-onboarding.md](0001-initial-onboarding.md) |
```

Create `.ai/adr/0001-initial-onboarding.md`:

```markdown
# ADR 0001 — Initial Architecture Onboarding

**Date:** <today>
**Status:** Accepted

## Context
Legacy project onboarded into AI-assisted SDLC pipeline.
No prior ADRs existed. This record captures the architectural snapshot at onboarding time.

## Decisions Recorded

<For each deliberate architectural choice found in Phase 1.13 — one subsection:>

### <Decision name>
**Choice:** <what was chosen>
**Alternatives not chosen:** <if detectable>
**Rationale:** <as best inferred from code, comments, or README>

## Known Debt
<HACK / FIXME / TODO items that indicate architectural debt — from Phase 1.11 and 1.14.>
```

---

### File 9 — `.ai/memory/state.md`

```markdown
# state.md — current task-level state and active work

## Active Tasks
None — project freshly onboarded. No tasks in flight.
A task waiting on an external dependency stays here with `status: blocked`.

## Done
None.

## Deferred
None.
```

---

### File 10 — `.ai/memory/progress.md`

```markdown
# progress.md — chronological log of completed work

## Log

- **<today's date>** — Initial AI knowledge-base onboarding via `/onboard-legacy-project`.
  Analyzed codebase and filled:
  architecture.md, runbook.md, integrations.md, environment.md,
  principles/architecture.md, principles/coding.md, principles/domain.md,
  adr/index.md + 0001-initial-onboarding.md, state.md, AGENTS.md, CLAUDE.md.
  Stack: <detected stack>.
  Integrations: <count and names>.
  Unknown fields requiring manual input: <list or "none">.
```

---

### File 11 — `AGENTS.md` (targeted edits only)

Do NOT rewrite the whole file. Find and replace only the placeholder sections:

**`## Project Context`** — replace the `# TODO` comment with:
```
What this project does:  <one paragraph from Phase 1.1>
Primary stack:           <language + framework + DB + infra from Phase 1.3>
Key constraints:         <multi-tenant? GDPR? latency targets? from README or Phase 1.8>
```

**`## Commands`** — replace the `# TODO` comments with the exact commands from runbook.md:
```bash
test:      <exact test command from Phase 1.9>
lint:      <exact lint command from Phase 1.3>
typecheck: <exact typecheck command or "not configured">
build:     <exact build command or "not applicable">
```

---

### File 12 — `CLAUDE.md` (append only)

Read the existing `CLAUDE.md`.
Check if it has a `## Project Standards` section already. If not — append:

```markdown
## Project Standards

architecture:   <one-line summary of the main layering rule from principles/architecture.md>
stack:          <language + framework + DB>
test command:   <exact test command>
lint command:   <exact lint command>
forbidden:      <top 3 forbidden patterns from principles/coding.md>
```

Do NOT modify the `## Context Loading Protocol` section. Append only.

---

## Phase 3 — Quality Check

After writing all files, verify:

1. **No invented content** — every claim traces to a file read in Phase 1. List any field where you wrote `unknown — needs manual input`.

2. **Commands are real** — the commands in `runbook.md → ## Commands` and `AGENTS.md → ## Commands` are actual commands found in the project (Makefile target, script, `package.json scripts`, or direct CLI). Do not guess.

3. **Architecture matches reality** — layer names in `architecture.md → ## Components` match actual directory names in the repo.

4. **Domain terms are real** — every term in `domain.md → ## Vocabulary` appears in the codebase (model names, route names, or README).

5. **No filled files were overwritten** — confirm every file classified as "filled" in Phase 0.3 was skipped.

Update `.ai/onboarding-progress.md`:

```markdown
## Phases
- [x] Phase 1 — Codebase Exploration
- [x] Phase 2 — Write Knowledge Base Files
- [x] Phase 3 — Quality Check

## Notes
Completed: <today's date>
Stack detected: <stack>
Unknown fields: <list or "none">
```

---

## Phase 4 — Report

Output the following summary:

```
=== Knowledge Base Onboarding Complete ===

Files written:
  ✓ .ai/memory/architecture.md
  ✓ .ai/context/runbook.md
  ✓ .ai/context/integrations.md
  ✓ .ai/context/environment.md
  ✓ .ai/principles/architecture.md
  ✓ .ai/principles/coding.md
  ✓ .ai/principles/domain.md
  ✓ .ai/adr/index.md + 0001-initial-onboarding.md
  ✓ .ai/memory/state.md
  ✓ .ai/memory/progress.md
  ✓ AGENTS.md (## Project Context + ## Commands)
  ✓ CLAUDE.md (appended ## Project Standards)

Skipped (already filled):
  <list any files skipped>

Needs manual input:
  <list every "unknown — needs manual input" field with file and field name>
  <or "None — all fields populated from code evidence">

Stack detected:      <language + framework + DB>
Integrations found:  <count> (<names>)
Domain terms:        <count>
Invariants:          <count>
Test command:        <command or "NOT FOUND — required before /phase-execution">
Security findings:   <count of Phase 1.14 hits, or "none">

Next steps:
  1. Review the files above, fill any "unknown" fields manually.
  2. **Set `test:` in `.ai/context/runbook.md → ## Commands` if it is still unknown.**
     The pipeline's TDD step (`/pae-tests`) stops without it — RED cannot be observed
     when there is no way to run tests. A legacy project with no test command needs one
     added before `/phase-execution` will run.
  3. If security findings were noted — run /codebase-audit for a full security review.
  4. Create your first spec: .ai/specs/01-<first-task>.md
  5. Then run: /phase-discovery .ai/specs/01-<first-task>.md
```
