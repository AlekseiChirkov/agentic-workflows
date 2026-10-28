# agentic_workflows — full project analysis and comparison with alternatives

Redaction legend: Project A, Project B, and Project C are anonymized labels; the mapping is intentionally not recorded.

Analysis date: 2026-09-16. Analyzed 123 files (≈16,000 lines of Markdown and shell):
38 workflow files, 14 rules, 4 principles, `.ai/` templates, 5 shell scripts,
`validate-contracts.sh` (534 checks, all passing), and 10 real run logs from projects
`Project A`, `Project B`, and `Project C`.

---

## 1. Summary

`agentic_workflows` is not a “collection of prompts,” but an **SDLC process specification for
LLM agents**, implemented entirely in Markdown and deployed to three environments (Claude Code,
Codex, Windsurf/Devin). The system's core: spec → Discovery (analysis, decomposition, design) →
Execution (a TDD cycle for each subtask) → Validation (contract, review, fix tasks), with
all state stored on disk in `.ai/`, rather than in the model's context.

**Main strength:** in the depth of its process engineering, the system surpasses all
known open alternatives: enforced RED→GREEN with a frozen test suite,
Implementer/Validator separation, class A/B escalations with an Arbiter, stacked branches with
recovery after squash merges, a machine-readable run log, and `/retro`, which
analyzes it. None of the compared frameworks covers all these points at once.

**Main weakness:** the cost of this depth. ~76,000 words of instructions, 123 stopping
points, 127 cross-references between files, no runtime: all logic
runs on the LLM's “good faith,” and the logs show regular violations (steps
logged retroactively with zero duration, status vocabulary ignored,
one subtask lasting 15 hours, an agent killed by a spending limit). The system is designed as
a deterministic pipeline but executed by a nondeterministic interpreter.

**Who it is for:** long-lived backend/infra projects (Python/FastAPI/Terraform) with one or two
engineers who value reviewability of every change, decision audits, and a repeatable
process across several AI tools. **Not for:** prototypes, frontend experiments,
teams without the discipline to maintain `.ai/`, or tasks the size of “fix one line.”

---

## 2. What the project is

### 2.1 Architecture

```
Source of truth (this repository)
├── rules/        14 files — always-active contracts (workflow-globals, tdd, git-flow,
│                 orchestration, quick-flow, run-log, language + 5 phase-* bootstrap rules)
├── principles/   4 files — engineering standards (code-quality, python, testing, infra)
├── workflows/    38 files — slash commands: 3 phase orchestrators, 2 atomic orchestrators,
│                 19 child steps (pd-*, pe-*, pv-*, pae-*, pav-*), spec-run/restack,
│                 bugfix, spec-draft, spec-sync, adr-new, context-pack, retro, utilities
├── templates/    .ai/ (project knowledge-base skeleton), .ai-umbrella/ (multi-repo), AGENTS.md
├── sync.sh       validate-contracts.sh → deployment to ~/.claude/skills, ~/.codex/skills,
│                 ~/.codeium/windsurf/global_* + traversal of all projects with .devin/
├── setup-new-project.sh / setup-umbrella.sh — project initialization
├── log-step.sh   append-only JSONL run log with server timestamps
└── logs/runs/    centralized telemetry for every run in every project
```

### 2.2 Key mechanisms

| Mechanism | What it does | Where defined |
|---|---|---|
| **State on disk** | `state.md` / `plan.md` / `T-XX/description.md` are the sole source of progress; “continue, never restart” | `workflow-globals`, `workflow-reference` |
| **Three phases with strict boundaries** | Discovery → Execution → Validation; automatic transitions prohibited except in `/phase-pipeline` | `workflow-globals` |
| **TDD as a contract** | `/pae-tests` writes failing tests from Acceptance Criteria, observes RED, and freezes the suite; `/pae-implement` cannot weaken a test; `pinned` mode for refactoring | `rules/tdd.md` |
| **Test-level gate** | unit → integration → contract → smoke → none, with mandatory justification for `none` | `rules/tdd.md` |
| **Flow tiers** | `quick` (≤3 files, no invariant, no shipped-behavior change, no migration) vs `full`, with promotion during execution | `rules/quick-flow.md` |
| **Autonomous decision protocol** | 2–3 options, 5 lenses (simplicity, reversibility, codebase fit, testability, blast radius), anti-overengineering filter, escalation threshold | `workflow-reference` |
| **Subtask classifier** | signals S1–S5, leaf / composite (Type 2) / vertical re-slice (Type 3), depth-2 cap, runtime tripwire for promotion | `workflow-reference`, `pd-decompose` |
| **`/spec-run` orchestration** | 4 roles (Orchestrator, Arbiter, Implementer, Validator) as context boundaries; class A (Arbiter with a quotation) vs class B (human only, batch gate before the first branch) | `rules/orchestration.md` |
| **Git model** | stacked branches, one per subtask; `test:` + `feat:` commits as TDD evidence; `base_commit` for `/restack` after any merge strategy; `git add -A` prohibited; no pipeline identifiers in the repository | `rules/git-flow.md` |
| **Run log + retro** | pipelines write JSONL through `log-step.sh`; `/retro` aggregates it through `jq` and proposes changes to the workflows themselves | `rules/run-log.md`, `retro.md` |
| **Contract validation** | 534 grep checks for consistency between files before every deployment | `validate-contracts.sh` |
| **Multi-repo** | umbrella `.ai/` + local `.ai/` directories, `working_dir:` in subtasks | `setup-umbrella.sh`, `pd-decompose` |

### 2.3 Real-world operation (from the logs)

| Run | Project | Outcome | Observations |
|---|---|---|---|
| spec-run b905a8a5 | Project A | 9 subtasks, all PASS, PRs opened | **26 h** wall-clock; T-06 — 15.4 h; `pd-select-model` — 3 h (live web search of the model catalog) |
| spec-run 41b4496e | Project A | 10 subtasks, completed | **21.7 h**; T-01 blocked → NEEDS WORK → PASS (3 iterations); T-02 “implementer terminated by spend limit; scratch impl reverted”; T-10 — 10 h |
| spec-run 4029e93a | Project B | stopped at the batch gate | the user's “same-branch” instruction conflicted with 3 gated phases; the gate worked as intended |
| spec-run 4305eda1 | Project B | completed | all 12 steps recorded **in one batch with duration 0** — retroactive logging; 2 subtasks deferred |
| bugfix ×6 | Project B, Project C | all completed, 3–21 min | quick tier works; `resolve` is the longest step (up to 8 min); one run lacked `flow:` and used steps outside the vocabulary (`implement`, `verify-local`, `verify-ci`) |

Conclusions from telemetry: (1) the system really carries large tasks through to PRs without
human involvement except at the batch gate; (2) cost and duration are enormous and uncontrolled;
(3) agents only partly follow the logging contract itself: the `outcome` vocabulary
(`ok|blocked|failed|skipped|deferred`) is violated by `completed`, `implemented`,
`restarted`, and `needs-work`; the `gate` field contains arbitrary text.

---

## 3. Comparison with other solutions

The solutions considered belong to the same class: “a process/methodology on top of a coding agent,” rather than
the agents themselves. Information on external projects is current as of writing; they evolve rapidly.

### 3.1 Brief profiles

| Solution | Essence | Tools | Strengths | Weaknesses |
|---|---|---|---|---|
| **BMAD-METHOD** | Agile personas (Analyst, PM, Architect, SM, Dev, QA); PRD → Architecture → sharded stories; story file as context handoff to the Dev agent | Claude Code, Cursor, Windsurf, Codex, web UI | Large community, expansion packs, strong planning, a story as self-contained context | Heavy ceremony, role “personalities” instead of context boundaries, TDD not enforced, no Git model, no telemetry |
| **GitHub Spec Kit** | `specify` CLI: constitution → specify → plan → tasks → implement; spec-quality checklists | 15+ agents | Easy entry, official GitHub support, tool independence, good spec templates | Stops at tasks.md; no resume state, no TDD gate, no post-implementation validation, no subagent orchestration |
| **Kiro (AWS)** | Spec-driven IDE: requirements.md (EARS), design.md, tasks.md; hooks; steering files | Kiro IDE only | EARS requirements notation, hooks on IDE events, built-in spec UI | Vendor lock-in, no decomposition into dependent subtasks, no Git stack, no cross-project analytics |
| **OpenSpec** | Changes as “change proposals” with delta specs; spec = source of truth; archive after merge | Claude Code, Cursor, and others | Lightweight, works well on brownfield projects, clear “spec after the change” model (analogous to `/spec-sync`) | No execution/validation phases, no TDD, no orchestration |
| **Superpowers (obra)** | Skill library for Claude Code: brainstorming → writing-plans → executing-plans, TDD skill, subagent-driven development, systematic debugging, worktrees | Claude Code (ports exist) | Idiomatic for Claude Code, a real TDD skill, subagents per subtask, low entry barrier | No persistent state between sessions as a contract, no validation phase with fix tasks, no multi-tool support, no telemetry |
| **Agent OS (Builder Methods)** | product/ (mission, roadmap, tech-stack) → specs/ → tasks; standards files | Claude Code, Cursor, others | Simple structure, good “product context,” standards as a separate layer | Planning without gates, no TDD enforcement, no validation, no resume contract |
| **Conductor (Google, Gemini CLI)** | Context-driven: product.md, tech-stack.md, workflow.md, tracks with plan.md; Markdown state | Gemini CLI | “State in Markdown on disk” is close to `.ai/`; treks as tasks | Tied to Gemini CLI, young, no TDD contract, no orchestration |
| **Native Claude Code features** | CLAUDE.md, skills, subagents, hooks, plan mode, worktrees, `/loop`, plugins | Claude Code | Everything executes through the harness: hooks really block commands, subagents really isolate context, worktrees enable parallelism | No methodology out of the box; each team assembles its own |
| **Cline Memory Bank / Cursor Rules / Windsurf Memories** | Memory and rule files loaded into context | respective IDE | Minimal entry barrier | Context only, no process |
| **Aider** | project rules files, architect/editor modes, automatic commits | CLI | Inexpensive, predictable, git-first | No phases, no specs, no validation |

### 3.2 Capability matrix

| Criterion | agentic_workflows | BMAD | Spec Kit | Kiro | OpenSpec | Superpowers | Agent OS | Conductor |
|---|---|---|---|---|---|---|---|---|
| Spec as input, immutable after starting | ✅ (`spec-draft`, immutable, `spec-sync`) | ✅ PRD | ✅ | ✅ | ✅ (delta) | partial | ✅ | ✅ |
| Decomposition with dependencies, composites, limits | ✅ (3–15 steps, ≤8, Type 2/3, depth cap) | ✅ epics/stories | ✅ tasks | ✅ tasks | ❌ | ✅ plans | ✅ | ✅ |
| Architectural options with trade-offs | ✅ (2–3, 5 lenses, ADR) | ✅ Architect | partial (plan) | ✅ design | ❌ | ✅ brainstorming | ❌ | ❌ |
| TDD RED→GREEN as an enforced gate | ✅ (frozen suite, `pinned`, justified `n-a`) | ❌ | ❌ | ❌ | ❌ | ✅ (skill, not a gate) | ❌ | ❌ |
| Independent Validator without Implementer context | ✅ | QA persona (same context) | ❌ | ❌ | ❌ | ✅ (review subagent) | ❌ | ❌ |
| Validation phase with fix tasks | ✅ (contract → review → issues → fixes) | partial | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Persistent state + resume contract | ✅ | partial | ❌ | partial | ❌ | ❌ | ❌ | ✅ |
| Quick tier for small changes | ✅ (4-condition gate) + `/bugfix` | ❌ | ❌ | ❌ | ✅ (in effect) | ❌ | ❌ | ❌ |
| Git model: stacked branches, restack, safety rails | ✅ | ❌ | ❌ | ❌ | ❌ | worktrees | ❌ | ❌ |
| Multi-tool deployment from one source | ✅ (3 environments) | ✅ | ✅ | ❌ | ✅ | partial | ✅ | ❌ |
| Multi-repo / umbrella | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Process telemetry + retro | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Model selection per subtask | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Legacy-code onboarding into a knowledge base | ✅ | ✅ (brownfield) | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Contract validation of the workflows themselves | ✅ (534) | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ |
| Parallel execution of subtasks | ❌ (explicitly prohibited) | ❌ | ❌ | ❌ | ❌ | ✅ worktrees | ❌ | ❌ |
| Harness-level enforcement (hooks, permissions) | ❌ (text only) | ❌ | ❌ | ✅ hooks | ❌ | partial | ❌ | ❌ |
| Entry barrier | high | medium-high | low | low | low | low | low | low |
| Volume of instructions loaded into context | very large | large | small | small | small | medium | small | small |

---

## 4. Strengths of the current project

1. **TDD as a state machine, rather than a wish.** `atomic-tests: not-started → red |
   pinned | n-a → green | failed`; RED requires an *observed* failure for the right reason,
   a test passing before implementation is `failed`, rather than success. The `pinned` mode closes the gap
   through which refactoring usually escapes testing. This is the strongest and rarest part.

2. **Context separation instead of role “personalities.”** The Arbiter must quote its source
   (“an answer without a quotation is not an answer, but a question for the human”); the Validator cannot see the
   Implementer's reasoning. This directly engineers protection against model self-confirmation, rather than theater.

3. **Class A / class B and the batch gate.** Recognizing that in a sequential chain,
   “deferring a subtask = stopping everything,” and moving every question of product intent to one
   point *before the first branch* is a mature design decision absent from every alternative.

4. **A Git model for real work with a reviewer.** A `test:` commit as evidence,
   `base_commit` as the sole input for `/restack`, draft PRs before validation ends, a ban on
   `git add -A` with an explanation of *why* (`.ai/` would enter every branch). The rules read like a
   post-mortem, rather than a checklist.

5. **All state on disk, “continue, never restart.”** An interrupted run resumes
   with the same command; Guard sections prevent overwrites. The logs show that resume actually
   works (Project B: 4029e93a stopped → 4305eda1 continued).

6. **Feedback on the process itself.** A run log with honest rules (“a number written
   by the model is a guess,” “an omitted field ≠ 0”), `/retro` with a mandatory link from each finding to
   a specific file and a “do not invent findings” rule. This is the only framework
   that attempts to measure itself.

7. **Quick tier and `/bugfix` with an explicit gate.** The rules grew from two real incidents
   (23 `fix-NN` directories for single-file edits; an ad hoc fix to a shipped pipeline without
   a contract), both documented as worked examples. The logs show that the bugfix path takes
   3–21 minutes and is actually used.

8. **Project self-discipline.** An independent audit (20 findings, 4 blockers), a fix spec,
   `AUDIT-PROMPT.md` for repeat auditing, 534 contract checks that block deployment.
   The project treats itself as a product.

9. **One source — three environments + multi-repo.** `sync.sh` resolves name collisions
   (the `rule-` prefix), traverses every project, cleans local shadows; umbrella `.ai/` solves
   the question of “where the architecture of service interactions lives.”

10. **No pipeline traces in the repository.** No `T-XX`, ADR numbers, or
    attribution in commits: the repository is readable to someone who has never seen the system.
    The trade-off (traceability only in untracked `state.md`) is stated openly.

---

## 5. Weaknesses of the current project

### 5.1 Structural

1. **No runtime: everything runs on the model's good faith.** 123 `**stop**` points,
   Guard sections, status vocabularies, bans on `git add -A`: all are text. The logs
   show the model violating it: 12 steps with `duration 0` recorded in one batch
   *after* completion (4305eda1), `outcome` takes values outside the enum, `flow:` is empty in
   4 out of 10 runs. `log-step.sh` does not validate the vocabulary; `validate-task.sh` does not
   run automatically. The system *describes* a deterministic pipeline but does not
   *enforce* one.

2. **Context volume.** 17,600 words of rules + 3,500 of principles + up to 4,200 words for a single
   workflow (`pd-select-model`) + a bootstrap from 7 `.ai/` files. A single atomic iteration
   easily starts with 40–60k tokens of instructions before the first code file is read.
   `context-pack` mitigates only the `.ai/` portion. For Windsurf/Codex, where always-on rules
   load in full, it is even heavier. Some “reference” text (rationale, worked examples,
   the history of incidents on 2026-07-22) lives in always-on files despite being needed once a month.

3. **Cost and duration are unbounded.** 26 and 21.7 hours per spec-run; 15 h for one
   subtask; 3 h for `pd-select-model` (a live model-catalog web search on *every* run under
   an explicit ban on caching); an Implementer “terminated by spend limit.” No budget per
   subtask, no timeout, no token accounting in the run log (a `files` field exists, but `tokens`/`cost`
   do not). `/retro` cannot answer the main question: “how much does this cost?”

4. **Strict sequential execution.** Parallelism is prohibited because there is no locking in
   `## Subtask Progress`. This is an honest limitation, but it means that 9 independent
   subtasks take 26 hours while Claude Code already provides worktrees and background subagents.
   The cause is the chosen state format (one Markdown file), rather than the nature of the task.

5. **Fragile cross-references.** 127 references such as “see `workflow-reference → ##
   Autonomous Decision Protocol`” across 56 files. The audit found 10 references to nonexistent
   sections, a `/phase-execution ↔ /phase-validation` deadlock, and a duplicate composite-validation trigger.
   `validate-contracts.sh` is 1,400 lines of substring grep checks; it catches a deleted line but
   not a semantic mismatch. Each new rule adds N checks and M references.

6. **The source of truth is not under Git.** The `agentic_workflows` repository reports `not a git
   repository`. Changes to 76,000 words of contracts cannot be reverted, compared, or bisected;
   `/retro` proposes changing workflows, but there is no history to connect a change with its effect
   in the logs. For a project requiring an ADR for every decision, this is a contradiction.

### 5.2 Product

7. **Python/FastAPI/GCP focus.** `principles/python-standards.md`,
   `infra-standards.md`, the sole stack template `python-fastapi.md`, examples using Alembic and
   Pydantic. For TypeScript/Go/Rust/mobile, principles must be written from scratch; the test-level
   gate and `testing-standards` (InMemory repositories, AAA) implicitly assume clean
   architecture in a backend. Frontend, data science, ML notebooks, and games are barely covered.

8. **Entry barrier and the “second user.”** USAGE.md is 774 lines; understanding why
   `pav-propose --batch` means “record, apply nothing” requires reading three
   files. No `examples/` with a full run of one task (spec → state.md → plan.md →
   description.md → PR). No short “first 15 minutes.” The system is designed for its author.

9. **Unequal environments.** For Windsurf, rules are always-on; for Claude Code, they are skills
   (model-invoked); for Codex, only `AGENTS.md` + skills. The document honestly states that
   trigger semantics change and duplicates “essentials” in `global-claude.md`, but this
   means that in Claude Code the full TDD contract loads only if the model *decides*
   to load it. `/spec-run` subagent orchestration (spawn, keep alive, message)
   is only implementable in Claude Code at all; in Windsurf, it is fictional.

10. **Documentation duplication.** USAGE.md §7–9, PIPELINE.md, `workflow-reference`,
    and descriptions at the top of every workflow: four places describe the same command/status
    tables. The audit has already found drift; it will recur.

11. **The spec is the weakest link without support.** The `templates/spec.md` template is 20 lines;
    `spec-draft` (3,500 words) helps, but there is no requirements notation (EARS, Given/When/Then
    is mandatory only in bugfix), no spec-quality checklist like Spec Kit's, no link
    between Acceptance Criteria ↔ tests ↔ PR as a verifiable artifact outside `notes:`.

12. **`pd-select-model` is overcomplicated.** 4,200 words, a 5-axis evaluation, mandatory live
    web search, special branches for the “creative” trait, and 3 hours in a real run. Yet
    the actual per-subtask price difference between Sonnet/Opus is known in advance.

13. **Hardcoded absolute paths.** `~/projects/agentic_workflows`
    is embedded in rules, workflows, and `log-step.sh`; `--from` is available only in `sync.sh`. Moving to
    another machine/CI requires manual edits.

14. **No tests for the workflows themselves.** Text consistency is checked, but not
    behavior: no “golden run” (spec fixture → expected state.md/plan.md), no
    regression run after rule changes. The audit with 20 findings was performed manually
    through a separate prompt.

---

## 6. Advantages over other solutions

| Advantage | Who falls short |
|---|---|
| The only system with **enforced, auditable TDD** (a frozen RED suite, `pinned`, justified `n-a`, a separate `test:` commit as evidence) | all; Superpowers has a TDD skill, but no gate or status |
| **Independent validation** at three levels: atomic (Validator without context), task (contract + review), integration (composite), with fix-task generation | BMAD (QA in the same context), Spec Kit/Kiro/OpenSpec (no validation) |
| **A Git model for the reviewer**: stacked branches, draft→ready, `/restack` after any merge, safety rails | none of the methodologies describes the Git layer; Superpowers provides worktrees without a stack |
| **Resume contract** with Guards and git↔state reconciliation | Conductor is closest; the others say “reread the files” |
| **Class A/B escalation + Arbiter with quotations + batch gate** — one planned stop for the entire task | all others either ask constantly or never ask at all |
| **Telemetry and `/retro`** — the process improves through data, rather than impressions | none |
| **Quick tier / bugfix** — a governed path for small changes with a formal gate and promotion during execution | OpenSpec is lightweight throughout; the others offer all or nothing |
| **Multi-repo umbrella** and `working_dir:` in subtasks | none |
| **One source → 3 environments** with collision resolution and project traversal | BMAD/Spec Kit/Agent OS are also multi-tool, but without pre-deployment validation |
| **Contract validation and external auditing** of the instructions themselves | none |

It loses to competitors on entry barrier (Spec Kit, OpenSpec, Superpowers),
harness enforcement (Kiro hooks, native Claude Code hooks), parallelism
(Superpowers/worktrees), community and ecosystem size (BMAD, Spec Kit),
requirements notation (Kiro EARS), and context compactness (all).

---

## 7. Which projects the workflows suit

### Good fit

- **Long-lived backend services and data/infra platforms** (Python/FastAPI, SQLAlchemy,
  Terraform, GCP): the principles were written specifically for them; logs show successful runs on
  Terraform/dlt/CI-workflow tasks.
- **Projects with 1–3 engineers where AI writes most code and a human reviews PRs.**
  Stacked branches, `test:` commits, and PR bodies with test evidence are designed for this scenario.
- **Multi-repo systems** with shared architecture (umbrella `.ai/`).
- **Legacy codebases** that first need `/onboard-legacy-project`, then the discipline of
  “do not change shipped behavior without a contract” (quick-flow condition 3).
- **Regulated/auditable domains** (fintech, payments, judging by worked examples about
  NOWPayments and forex) where “why this decision was made” matters (an ADR for every decision,
  `### Autonomous Decision` with scores).
- **Tasks of 3–8 subtasks with 3–15 steps each**: the decomposer is calibrated for these.
- **Teams using several agents** (Claude Code + Codex + Windsurf) that want
  one process for all of them.

### Fit with qualifications

- **TypeScript/Go/another stack**: the process layer is universal, but the principles and
  test-level gate must be rewritten; expect 1–2 days of adaptation.
- **Frontend**: a component-level TDD gate works less well; rules will be needed for visual
  checks and the `smoke` level through e2e.
- **Small teams without a dedicated “process owner”**: `.ai/` becomes stale quickly
  if nobody maintains `architecture.md` and ADRs.

### Poor fit

- **Prototypes, hackathons, experiments**: Discovery with a 5-lens evaluation for a disposable
  script is harmful.
- **Single-line edits unless made through `/bugfix`**: the full path is excessive for these even in
  the quick tier.
- **Data science / ML research** in notebooks: there are no testable Acceptance Criteria in
  the required sense.
- **Tasks with strict time/budget limits**: with budgets currently absent, one
  spec-run can take a day and hit the spending limit.
- **Work only in Windsurf/Codex**, if `/spec-run` is needed: the subagent model does not
  execute there.

---

## 8. What to improve for high-quality, efficient development with these workflows

Sorted by impact/effort ratio. Items 1–5 are quick, 6–10 medium,
11–15 strategic.

### Quick (days)

1. **Put the repository under Git.** Tag contract releases; write `contract_version:`
   in `state.md` so `/retro` can connect rule changes with metric changes. Without this,
   item 6 of `/retro` (“which step worsened”) is unsolvable.

2. **Validate vocabulary in `log-step.sh`.** Reject (or normalize with a
   warning) `outcome`/`tests`/`promoted` outside the enum, require `flow`. Currently, 4 out of 10
   logs are invalid for `/retro`, and their metrics are noise.

3. **Logging through hooks rather than prompts.** In Claude Code, `PostToolUse`/`Stop`
   hooks can invoke `log-step.sh` automatically with real timestamps. Run
   4305eda1 (12 steps at 0 s) shows the model logging after the fact; a hook
   rules this out by design.

4. **Cache the model catalog.** A file with a 7-day TTL instead of a live web search on each
   run; remove 3 hours from `pd-select-model`. Reduce the workflow to a “subtask
   type → tier” table with an override column.

5. **Budgets and timeouts per subtask.** `budget_tokens:` / `max_wall_s:` fields in
   `plan.md`, checked in `/spec-run` Step 4 before spawn; exceeding them → `blocked` with a record,
   rather than silently dying at the spending limit. Record `tokens_in/out` and `cost_usd` in the run log
   (Claude Code exposes them in hooks and `--output-format json`).

### Medium (weeks)

6. **Move enforcement from text into the harness.** For Claude Code: a `PreToolUse` hook
   that blocks `git add -A`, `git push` to the base branch, `git reset --hard`, and staging any
   path under `.ai/`; `deny` rules in `settings.json`. Rule text remains as an explanation,
   but violation becomes impossible, rather than prohibited. Likewise, a hook that
   refuses edits to files in the RED suite during GREEN without a
   `tdd: test amended` entry in `notes:`.

7. **A deterministic state tool.** A small CLI (`state.py`/`state.sh`): `state get
   T-02 atomic-tests`, `state set T-02 last_action "..."`, `state validate`. The model stops
   editing Markdown blocks manually; an entire class of errors disappears (truncated blocks,
   lost `notes:`, duplicates), and `validate-task.sh` runs on every write. This also
   opens the path to locking and parallelism (item 11).

8. **Layer context by access frequency.** Split every rule into *contract* (2–3
   screens, always-on) and *rationale* (worked examples, incident history, example tables,
   on demand). Goal: an atomic step starts with ≤15k instruction tokens. `workflow-reference`
   (4,200 words) and `PIPELINE.md` (2,700) are candidates for “by reference only.” Measure
   the actual bootstrap size and write it to the run log.

9. **Golden-run tests for workflows.** A `tests/fixtures/<case>/` directory with a spec + `.ai/`
   and expected `state.md`/`plan.md`/`description.md`; run through `claude -p` (headless), with
   diffs of normalized artifacts. Run before `sync.sh` alongside
   `validate-contracts.sh`. Three cases cover 80%: flat, composite (Type 2), quick/bugfix.

10. **One source for reference tables.** Generate USAGE.md §7–10 and PIPELINE.md
    from workflow-file front matter through a script (`description:`, `invocation:`, `reads:`,
    `writes:`), rather than manually maintaining four copies. `validate-contracts.sh` would then
    validate front matter instead of grepping prose.

### Strategic (months)

11. **Parallelism for independent subtasks.** After item 7: one state file per
    subtask (`T-XX/progress.md`) + an aggregator, a Git worktree per subtask, a DAG from
    `Depends On`. The stacked model remains for dependent chains; independent branches start from
    base in parallel. Runs lasting 26 hours can become many times shorter without losing contracts.

12. **Stack profiles for principles.** `principles/stacks/{python-fastapi,typescript-node,
    go,terraform,react}.md` with identical sections and an explicit “test-level gate for
    this stack” table (what counts as unit/integration/contract/smoke in a React application).
    `setup-new-project.sh --stack=…` already hints at this, but only one profile is implemented.

13. **Requirements notation and AC tracing.** Mandatory Given/When/Then or EARS for
    Acceptance Criteria in the spec; a spec-quality checklist in `spec-draft` (as in Spec Kit);
    an `AC-N → test name → commit sha` table as a separate `state.md` section, copied into
    the PR body. Currently, the link lives in `notes:` as free text.

14. **An honest environment matrix.** Explicitly declare Claude Code the primary environment (the only place
    where subagents, hooks, and worktrees execute), Codex secondary (AGENTS.md + skills, without
    `/spec-run`), and Windsurf “rules and individual steps.” Remove documentation promises
    that do not hold in an environment, and relieve `sync.sh` of the obligation to support
    always-on semantics where none exist.

15. **Onboarding and examples.** `examples/oauth-task/`: a complete run with a spec, all
    Discovery artifacts, `state.md` after Execution, the final PR body, and run log. “The first 15 minutes”
    in README, in 60 lines. `--dry-run` for `/phase-discovery` and `/bugfix`, rather than only
    `/spec-run`. This lowers the entry barrier, the main disadvantage against Spec Kit/Superpowers.

### Additional (small but useful)

- Make the root path configurable through one variable (`AGENTIC_WORKFLOWS_HOME`),
  substituting it into rules during `sync.sh`.
- Add an explicit secrets/PII diff gate to `pv-review` (currently “security” is one
  list item without a tool).
- Have `/retro` also write a machine-readable report and store a series of metrics by contract
  version (for a “better/worse” chart).
- Deduplicate `rules/global-claude.md` and `templates/codex-global-AGENTS.md`:
  generate both from one source.
- Remove “step 2.5” and other fractional numbers: they already confuse the order (in the logs,
  `model-selection` occurs both before and after the batch gate).

---

## 9. Conclusion

`agentic_workflows` is the most complete known open AI-SDLC specification: where
BMAD provides roles, Spec Kit a spec and tasks, Superpowers a TDD skill and subagents, and Kiro
hooks, this system provides all of them together, plus a Git stack, validation phase, resume contract, and
telemetry. This is its competitive advantage and main risk: a system of 76,000 words
without a runtime is executed by the same probabilistic interpreter it attempts to
discipline, and the logs show that this discipline does not hold everywhere.

The greatest improvement in quality and efficiency will come not from adding new rules, but from
**moving the existing rules into executable form**: Git for the source of truth,
a state tool instead of manual Markdown editing, hooks instead of prohibitions in prose, budgets
and real cost telemetry, golden-run tests instead of grep checks. After that,
it will be safe to reduce context and enable parallelism: two things that
currently make every task expensive and slow.
