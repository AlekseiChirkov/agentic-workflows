---
trigger: model_decision
description: Context loading rules for discovery phase — load when running /phase-discovery, /pd-analyze, /pd-decompose, /pd-design, /pd-finalize
---

# Phase: Discovery — Context Rules

## Context Bootstrap

Run before analyzing any codebase file. Skip missing files without error.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.
Report at end: "Discovery context loaded: [files read]"

| # | File | What to extract |
|---|------|-----------------|
| 1 | `.ai/memory/architecture.md` | System components, service boundaries, constraints |
| 2 | `.ai/memory/state.md` | Active tasks, blockers, in-flight work |
| 3 | `.ai/principles/architecture.md` | Architectural patterns, boundaries, what NOT to build |
| 4 | `.ai/principles/coding.md` | Naming standards, forbidden patterns — shapes decomposition |
| 5 | `.ai/principles/domain.md` | Domain rules, ubiquitous language, business constraints |
| 6 | `.ai/adr/index.md` | Past decisions index — read full ADR only if directly relevant |
| 7 | `.ai/memory/progress.md` | Previous session context — only if resuming interrupted work |

**Conditional — load only if the task statement mentions external services, third-party
APIs, or environment-specific setup:**

| # | File | Load when |
|---|------|-----------|
| 8 | `.ai/context/integrations.md` | Task touches external services / third-party APIs / cross-service contracts |
| 9 | `.ai/context/environment.md` | Task depends on environment-specific config (envs, secrets, infra topology) |

Skip both without error if not applicable or file missing.

After loading: state which architectural constraints apply to the current task before touching code.

## Codebase Reading Rules

- Use `.ai/memory/architecture.md` to scope source reads. Read affected source when verifying behavior, freshness, or a concrete pattern; an inventory description alone is not implementation evidence.
- Budget: max 12 files (8 entry-points + 4 one-level-deeper). Hard limit.
- Document every file read with reason: "read to verify <specific behavior or gap>."
- Stop reading when affected parts are understood.

## Decision Protocol

Discovery runs **autonomously by default**; `--step-by-step` switches it to
manual review. See `/phase-discovery → ## Execution Modes` (the workflow, not this rules file).

**Autonomous mode (default):**
- Task requirements unclear → resolve by research in this order: `.ai/principles/*`
  → `.ai/adr/` → `.ai/memory/*` → existing codebase patterns → general best
  practice. Record the resolution in `## Task Analysis → ### Assumptions`.
  Never infer intent silently — inferring is allowed, hiding it is not.
- Decomposition boundary or architectural choice ambiguous → generate 2–3 options
  and resolve them with `workflow-reference → ## Autonomous Decision Protocol`.
  Record the scoring and rationale.
- Steps 1→4 run back-to-back. A step's completion report is not a handoff.
- Stop only on the Autonomous Decision Protocol's escalation conditions or a
  Guard confirmation that would overwrite existing artifacts.

**Step-by-step mode (`--step-by-step`):**
- Task requirements unclear → ask before proceeding. Never infer intent silently.
- Decomposition boundary ambiguous → present 2–3 options with trade-offs, wait for decision.
- Architectural variants → present, wait for the user's choice.
- After each of Steps 1–4 → stop and wait for review.
