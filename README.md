# Orchestrail

Orchestrail is a version-controlled workflow for AI-assisted software development.
It guides changes from a written specification through implementation, validation,
and review while keeping decisions and evidence with the project.

Versions below 1.0.0 are unstable and may change without compatibility guarantees.

## What it provides

- Discovery, test-first implementation, independent validation, and reviewable delivery.
- Reusable project instructions, setup scripts, and persistent project knowledge.
- Workflow and rule deployment across supported coding assistants.

`sync.sh` writes skills under `~/.claude` and `~/.codex`, and overwrites
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` on each run.

Orchestrail provides instructions and scripts rather than a runtime; execution depends
on the coding assistant and project configuration.

## Guides

- [Operating manual](docs/USAGE.md) for installation and daily use.
- [Spec-run quickstart](docs/SPEC-RUN-QUICKSTART.md) for requirements, execution,
  and pull request handling.
- [Specifications index](.ai/specs/README.md) for the planned project improvements.
