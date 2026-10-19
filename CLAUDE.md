# Project Claude Rules — agentic_workflows

This repository is the source of truth for the AI-SDLC pipeline and is developed with
that same pipeline. Its own knowledge base lives in `.ai/` (not to be confused with
`templates/.ai/`, the skeleton seeded into consumer projects).

## Context Loading Protocol

At the start of every session, read in this order:
1. `.ai/README.md`                 — how this knowledge base is organised
2. `.ai/memory/architecture.md`    — layers, deployment matrix, data flow, contract surface
3. `.ai/memory/state.md`           — active work and known conditions
4. `.ai/principles/`               — architecture (P1–P12), coding (file-shape standards), domain (vocabulary, invariants)
5. `.ai/adr/index.md`              — decisions embedded in the rules; read the full ADR before changing its area

On demand:
- `.ai/context/runbook.md`         — commands, deploy, audit, retro, recovery procedures
- `.ai/context/environment.md`     — harness paths, variables, hard-coded paths
- `.ai/context/integrations.md`    — harnesses and tools the workflows depend on
- `.ai/specs/README.md`            — the improvement roadmap
- `.ai/memory/progress.md`         — history (audits, incidents, runs)

After every completed task, update `.ai/memory/state.md` and append to
`.ai/memory/progress.md`. After every design decision, add an ADR and index it.

## Commands

See `.ai/context/runbook.md → ## Commands`. In short: `bash validate-contracts.sh` is the
test suite; `bash sync.sh` deploys; never edit deployed copies under `~/.claude`,
`~/.codex`, `~/.codeium`.

## Document placement

Analysis, audit, comparison, review, and similar documents are created under `docs/`
(`docs/analysis/`, `docs/audits/`, dated names) and indexed in `docs/README.md` — never
in the repository root. Actionable changes become specs in `.ai/specs/`. Full rule:
`.ai/principles/coding.md → Document placement`.

## Standards

- `.ai/principles/coding.md` — how workflow, rule, principle, and script files are written.
- A contract change starts with a failing check in `validate-contracts.sh` (TDD at the
  `smoke` level), then the canonical definition, then every reader, then the ADR.
- English in every file. No pipeline identifiers or tool attribution in commits.
