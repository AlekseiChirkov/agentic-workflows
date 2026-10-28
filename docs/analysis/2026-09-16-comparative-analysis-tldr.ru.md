# agentic_workflows — analysis TL;DR

Redaction legend: Project A, Project B, and Project C are anonymized labels; the mapping is intentionally not recorded.

Full version: `2026-09-16-comparative-analysis.ru.md`. Date: 2026-09-16.

## What it is

An AI-SDLC specification entirely in markdown (≈76,000 words, 38 workflows, 14 rules), deployed
to Claude Code / Codex / Windsurf. Pipeline: spec → Discovery → Execution (TDD for each
subtask) → Validation (contract, review, fix tasks). All state lives on disk in `.ai/`.

## Strengths

- **Enforced TDD**: RED is observed, the test set is frozen, `pinned` is used for
  refactoring, and `none` requires justification.
- **Independent Validator** without Implementer context; the Arbiter answers only with a citation.
- **Class A/B escalation + batch gate**: one planned stop per task, before the first branch.
- **Git model designed for reviewers**: stacked branches, `test:`+`feat:` commits, `/restack` after
  any merge, safety rails, and no pipeline traces in the repository.
- **Resume contract**, quick tier and `/bugfix` for small changes, multi-repo umbrella.
- **Telemetry + `/retro`** — the only framework that measures itself.
- 534 contract checks and an external audit of its own instructions.

## Weaknesses

- **No runtime** — 123 stopping points and all prohibitions live in text; logs show
  violations (steps logged retrospectively with duration 0, statuses outside the vocabulary).
- **Expensive and slow**: spec-run takes 21–26 h, one subtask up to 15 h, `pd-select-model` 3 h
  (web searches for the model catalog on every run), an agent killed by a spend limit. No budgets.
- **Huge context**: tens of thousands of instruction tokens before the first code file.
- **Strictly sequential** — parallelism is prohibited because there is one state file.
- **127 cross-references**, grep validation, reference tables duplicated in four places.
- **The source of truth is not under git.**
- **Python/FastAPI/GCP focus**; other stacks require rewriting principles.
- High entry barrier, no `examples/`; Windsurf/Codex do not execute the subagent model.

## Comparison

| | agentic_workflows | BMAD | Spec Kit | Kiro | OpenSpec | Superpowers |
|---|---|---|---|---|---|---|
| TDD as a gate | ✅ | ❌ | ❌ | ❌ | ❌ | skill |
| Independent validation + fix tasks | ✅ | partial | ❌ | ❌ | ❌ | partial |
| Git stack / restack | ✅ | ❌ | ❌ | ❌ | ❌ | worktrees |
| Resume contract | ✅ | partial | ❌ | partial | ❌ | ❌ |
| Telemetry | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-repo | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Harness enforcement (hooks) | ❌ | ❌ | ❌ | ✅ | ❌ | partial |
| Parallelism | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Entry barrier | high | medium | low | low | low | low |

Assessment: leads in process depth; falls behind in simplicity, compact context,
harness enforcement, and parallelism.

## Who it fits

**Yes:** long-lived backend/infra projects (Python, Terraform), 1–3 engineers + AI, review
through PRs, multi-repo, legacy onboarding, auditable domains, tasks with 3–8 subtasks.
**With caveats:** other stacks, frontend, teams without an owner for `.ai/`.
**No:** prototypes, single-line changes outside `/bugfix`, ML notebooks, strict
budget/time limits, working only in Windsurf/Codex with `/spec-run`.

## What to improve (in priority order)

1. Put the repository under git and write `contract_version:` in `state.md`.
2. Validate enum fields in `log-step.sh`; log through hooks instead of prompts.
3. Cache the model catalog (TTL) and trim `pd-select-model`.
4. Token/time budgets per subtask; `cost`/`tokens` in the run log.
5. Move prohibitions (`git add -A`, pushing to main, editing RED tests) into hooks/permissions.
6. A state-tool CLI instead of manually editing markdown blocks.
7. Layer rules into contract (always-on) and rationale (on demand); target ≤15k tokens per step.
8. Golden-run workflow tests in headless mode before `sync.sh`.
9. Generate reference tables from front matter instead of four manual copies.
10. Parallel independent subtasks through worktrees (after item 6).
11. Stack profiles for principles (TS, Go, React, Terraform).
12. Given/When/Then or EARS for AC; trace AC → test → commit in the PR body.
13. An honest environment matrix: Claude Code is primary; Codex/Windsurf are limited.
14. `examples/` with a complete run and the “first 15 minutes” in README.

**Main idea:** move existing rules into executable form instead of adding rules —
then reducing context and enabling parallelism will become safe.
