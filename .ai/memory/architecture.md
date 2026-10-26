# architecture.md — current snapshot of the workflow system

## Purpose
Describes Orchestrail as it exists now: the layers of markdown, how they are
deployed into agent harnesses, how a task flows through them, and the contracts that
hold the files together. Updated only when a layer, a deployment target, or a contract
surface changes.

## Overview

Orchestrail is a **file-based specification of an AI-assisted SDLC**. There is no
runtime: every behaviour is an instruction that an LLM agent (Claude Code, Codex, or
Windsurf/Devin) reads and follows. The repository is the single source of truth;
`scripts/sync.sh` copies it into each harness's global configuration, and
`scripts/setup-new-project.sh` seeds a target project with a `CLAUDE.md`/`AGENTS.md`, rule
copies, skill symlinks, and a `.ai/` knowledge base. A task then moves through three
phases — Discovery, Execution, Validation — with all progress persisted in the target
project's `.ai/tasks/…/state.md`, and every orchestrated run appends telemetry to a
central log store that `/retro` reads.

Size at the time of writing: 38 workflows, 14 rules, 4 principles, and 8 shell scripts under `scripts/`,
≈76 000 words of instructions with automated consistency and smoke checks.

## Components

### Layer 1 — `rules/` (always-on contracts, 14 files)
Policies every workflow obeys. Deployed as Windsurf/Devin global rules, and — because
Claude Code and Codex have no rules directory — as skills under the mandatory `rule-`
prefix (five basenames collide with workflows). Key files:

| File | Owns |
|---|---|
| `workflow-globals.md` | phase contract, never-auto-advance, mode overrides registry, `--batch` semantics, flow tiers summary, **Canonical Status Formats** (`state.md`, `## Subtask Progress` leaf/composite blocks, `## Fix-Tasks`, `plan.md` statuses) |
| `workflow-reference.md` | file responsibilities, Description Amendment, Protected Sections Contract, multi-phase rules, `.ai/memory/state.md` entry format, **Autonomous Decision Protocol**, **Autonomous Subtask Classifier** (S1–S5, Type 2/3, tripwire), Decomposition Rules |
| `tdd.md` | RED/GREEN/pinned/n-a/failed states, test-level gate, frozen RED set, characterization mode |
| `git-flow.md` | preflight, stacked branch model, two-commit rule, no-attribution rule, pipeline identifiers out of the repo, safety rails, recorded git fields |
| `orchestration.md` | four roles (Orchestrator, Arbiter, Implementer, Validator), shared-file discipline (one writer per shared file), class A/B escalation, Discovery batch gate |
| `quick-flow.md` | four-condition gate, what quick skips and still mandates, mid-flight promotion |
| `run-log.md` | log store, three `scripts/log-step.sh` calls, field vocabulary, never-block rule |
| `language.md` | English in every project file |
| `phase-*.md` (5) | per-phase Context Bootstrap (which `.ai/` files to load and in what order), Blocker Reconciliation |
| `global-claude.md` | the content of `~/.claude/CLAUDE.md` — always-on essentials for Claude Code |

### Layer 2 — `principles/` (engineering standards, 4 files)
`code-quality.md`, `python-standards.md`, `testing-standards.md`, `infra-standards.md`.
Domain-quality rules, Python/FastAPI/GCP-centric. Deployed as Windsurf global rules and
as `principle-*` skills. `testing-standards` owns test *style*; `rules/tdd.md` owns test
*process*.

### Layer 3 — `workflows/` (slash commands, 38 files)

```
Orchestrators        phase-discovery  phase-execution  phase-validation  phase-pipeline
Atomic orchestrators phase-atomic-execution  phase-atomic-validation  phase-composite-validation
Discovery children   pd-analyze → pd-decompose → (pd-select-model) → pd-design → pd-finalize → pd-archive
Execution children   pe-execute → pe-finalize
Atomic children      pae-tests → pae-implement → pae-finalize ; pav-check → pav-propose → pav-close
Validation children  pv-contract → pv-review → pv-issues → pv-create-fixes (→ pv-classify-fixes) → pv-execute-fixes → pv-finalize
Orchestrated mode    spec-run, restack
Entry points         spec-draft, bugfix, onboard-legacy-project, adr-new, spec-sync
Utilities            context-pack, compress-state, retro, suggest-commit-message, suggest-pr-description, suggest-commit-pr
Reference            PIPELINE.md (not executable)
```

Every executable workflow has: a front-matter `description:`, an `Invocation:` line, a
`## Guard` section (detects completed work, asks before overwriting), numbered steps,
explicit `**stop**` points, and a report line. Children are callable standalone and must
run the full Context Bootstrap when they are.

### Layer 4 — `templates/`
`.ai/` skeleton (seeded into projects, never overwrites), `.ai-umbrella/` (multi-repo
root), `AGENTS.md` (Codex, per project), `codex-global-AGENTS.md` (→ `~/.codex/AGENTS.md`),
`subtask-description.md` and `spec.md` (reference skeletons), `stacks/python-fastapi.md`.

### Layer 5 — scripts
| Script | Role |
|---|---|
| `scripts/validate-contracts.sh` | Consistency and smoke checks across layers 1–3, including bidirectional canonical JSON-table/runtime contract comparison (`--run-log-contract-only`); includes an optional tracked-file public-hygiene scanner using local patterns (`--hygiene-only`, `--root`, `--denylist`); run by `scripts/sync.sh`; any failure blocks deploy |
| `scripts/validate-task.sh` | applies the same contracts to one task directory's artifacts; run by `/pd-finalize` and `/pe-finalize` |
| `scripts/sync.sh` | validate → copy to Windsurf, Claude Code, Codex → walk every project with `.devin/` and refresh its rule copies and skill symlinks |
| `scripts/setup-new-project.sh` | seed a project (auto-detects umbrella `../.ai/`) |
| `scripts/setup-umbrella.sh`, `scripts/setup-all-repos.sh` | multi-repo initialization |
| `scripts/link-skills.sh` | workaround: symlink global skills into a project's `.claude/skills/` |
| `scripts/log-step.sh` | validates complete producer arguments and exact legacy aliases before append-only JSONL writes; optional-jq legacy fallback; sorted runtime `contract` export and read-only `lint` diagnostics/summary; executable integer `ts_ms` boundaries; optional correlated identities and spans use bounded per-run flock, private active-only deduplication and matching JSON acceptance receipts; jq is required for lint and correlated writes, with flock/truncate additionally required for correlated writes; exits 0 on every error |
| `hooks/log-step-hook.sh` | Bash/jq/flock dispatch, status and serialized fallback; native Stop/SubagentStop adapter gates the most-specific registered project before private/transcript/log reads, validates canonical markers and native Skill evidence, freezes native/report-bound delivery for receipt-confirmed retries, and retains exclusive fallback ownership; private records under the XDG state directory contain no conversation text |

### Executable acceptance checks

`tests/log-step.sh` copies the helper, canonical contract and workflows into a disposable checkout and runs the focused producer, lint, retrospective and drift checks in separate Bash processes. Explicit temporary log/workflow roots and per-operation checksums isolate fixtures from real logs; exit and signal traps clean up the temporary tree.

`tests/log-step-hook.sh` exercises native input, explicit dispatch correlation, exact report markers, bounded transcript evidence, private state and competing delivery routes in disposable home/config/state/project/log roots. Run it through `bash scripts/validate-contracts.sh --hook-adapter-only`; the default validator includes the same acceptance suite.

### Layer 6 — `logs/` (central telemetry store)
`logs/runs/<ts>-<pipeline>-<id>.jsonl` + `.md` digest, `.active/` for open runs.
Cross-project by design; gitignored; read only by `/retro`.

### Layer 7 — `docs/` (documents about the system)
`docs/USAGE.md` (operating manual), `docs/SPEC-RUN-QUICKSTART.md`, `docs/audits/`
(`AUDIT-PROMPT.md`, `2026-07-21-logic-audit-fixes.md`), `docs/analysis/`
(`2026-09-16-comparative-analysis.ru.md` and its TL;DR), `docs/README.md` (index).
Placement rule: `.ai/principles/coding.md → Document placement`. The root holds only
`CLAUDE.md`, scripts, and source directories.

## Data Flow

```
author edits rules/ workflows/ principles/ templates/
        │
        ▼
scripts/validate-contracts.sh ──fail──▶ deploy blocked
        │ pass
        ▼
scripts/sync.sh ──▶ ~/.codeium/windsurf/global_{workflows,rules}/
        ├─▶ ~/.claude/skills/{<wf>,rule-<r>,principle-<p>}/SKILL.md + ~/.claude/CLAUDE.md
        ├─▶ ~/.codex/skills/… + ~/.codex/AGENTS.md
        └─▶ every project with .devin/: refresh .devin/rules, .windsurf/rules, .claude/skills symlinks
        │
        ▼
scripts/setup-new-project.sh (per project) ──▶ CLAUDE.md, AGENTS.md, .ai/ skeleton, .gitignore (.ai/ untracked)
        │
        ▼
spec in .ai/specs/NN-slug.md
  ──▶ /phase-discovery  ──▶ .ai/tasks/todo/task-NN-slug/{state.md, plan.md, T-XX/description.md}
  ──▶ /phase-execution  ──▶ per T-XX: pae-tests (RED) → pae-implement (GREEN) → pae-finalize → pav-*
  ──▶ /phase-validation ──▶ contract → review → issues → fix-tasks → finalize → ADR, progress.md, spec-sync
  (or /spec-run: same, plus Arbiter, stacked branches, test:/feat: commits, draft→ready PRs)
        │
        ▼
scripts/log-step.sh ──▶ logs/runs/*.jsonl ──▶ read-only lint ──▶ /retro usable observations ──▶ recommended edits to this repository
```

## Contract surface (what must stay consistent across files)

- **Canonical Status Formats** (`workflow-globals`) — every reader/writer of `state.md`
  and `plan.md`; readers key on field names, never on position; missing `atomic-tests:`
  is read as `not-started`.
- **Protected Sections Contract** (`workflow-reference`) — what `/compress-state` may never
  remove (`notes:`, `target_files:`, git fields, `tdd:` lines, composite blocks,
  `## Improvement Proposals`, `### Fix Classification`).
- **Cross-reference syntax** — `<file> → ## <Section>`; 127 such references exist and
  `scripts/validate-contracts.sh` checks that named sections exist.
- **Mode overrides registry** (`workflow-globals → Workflow-declared mode overrides`) —
  the only place a workflow may declare autonomy; `phase-pipeline → ## Pipeline
  Overrides` is the detail.
- **`--batch`** — one meaning everywhere: record, prompt for nothing, apply nothing.
- **Rule-name resolution** — bare basename on Windsurf/Devin, `rule-<name>` skill on
  Claude Code/Codex.
- **Active-run metadata** — a fixed format header and escaped values preserve multiline caller text without interpreting it as records; ordinary legacy metadata remains readable. JSONL events retain their existing schema.
- **Run-log vocabulary** — the helper enforces event-specific enums, bounded counts, exact legacy aliases, and safe run identifiers through one runtime contract exposed by `contract`; rejected arguments leave accepted event state unchanged.

## External Dependencies

- Agent harnesses: Claude Code (skills, `CLAUDE.md`, sub-agents — the only harness where
  `/spec-run`'s Arbiter/Implementer/Validator model is executable), OpenAI Codex
  (`AGENTS.md`, skills), Windsurf / Devin Desktop (global workflows and rules).
- Tools invoked by workflows: `git`, `gh` (PRs, only with `--allow-pr`), `jq`
  (`scripts/log-step.sh` digests, `/retro`), `bash`, a web search capability (`pd-select-model`
  rebuilds its model catalog live).
- Script source defaults resolve to the repository root, the parent of `scripts/`. `ORCHESTRAIL_HOME` overrides source selection; `scripts/sync.sh --from` takes precedence. Setup helpers normalize and propagate the selected root to children. `ORCHESTRAIL_LOG_ROOT` overrides the repository-root `logs/` directory. Documentation paths are placeholders.
