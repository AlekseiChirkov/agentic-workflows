# Put Orchestrail under git, rename it, and publish a minimal public slice

## Goal

The repository that defines the pipeline is not a git repository: ≈76 000 words of
contracts cannot be diffed, reverted, bisected, or reviewed, and `/retro` cannot relate a
workflow change to a change in the metrics. This spec initialises version control under
the public name **Orchestrail**, fixes every hard-coded path in the same commit, stamps
task state with the contract version, and publishes the minimum a stranger needs to
read the repository (ADR-0009, Decision 1).

## Acceptance Criteria

- [ ] The checkout is renamed in place to `orchestrail/` under its existing parent
      directory and `git rev-parse --git-dir` succeeds there; the absolute path is never
      written into any file (spec 00's denylist enforces it)
- [ ] No literal `agentic_workflows` or `agentic-workflows` remains in `rules/`,
      `workflows/`, `principles/`, `templates/`, `docs/USAGE.md`, `CLAUDE.md`, `.ai/`, or
      any `*.sh` except in historical documents (`docs/audits/`, `docs/analysis/`,
      `.ai/memory/progress.md`, `.ai/adr/`)
- [ ] `sync.sh` resolves its root as the directory containing itself, overridable by
      `ORCHESTRAIL_HOME`; `log-step.sh` resolves `ORCHESTRAIL_LOG_ROOT`, default
      `<root>/logs`; config paths use `~/.config/orchestrail/`
- [ ] `.gitignore` excludes `logs/runs/`, `logs/.active/`, `.claude/settings.local.json`;
      nothing under `.ai/` or `docs/` is ignored (ADR-0007)
- [ ] `bash validate-contracts.sh` passes, including the forbidden-token group from spec
      00, immediately before `git init` and again immediately before the first push
- [ ] `VERSION` at the root contains `0.9.0`; `/pd-analyze` writes
      `contract_version: <VERSION>` after `spec_path:` in task `state.md`; readers tolerate
      its absence; `log-step.sh run-start` records `contract_version`
- [ ] `validate-contracts.sh` warns (does not fail) when any file under `rules/` is newer
      than `VERSION` in git history and `VERSION` is unchanged in the working tree
- [ ] `LICENSE` is Apache-2.0 with the owner as copyright holder
- [ ] `README.md` (≤ 60 lines): what Orchestrail is, that versions below 1.0.0 are
      unstable, what `sync.sh` writes into `~/.claude` and `~/.codex`, and links to
      `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `.ai/specs/README.md`
- [ ] One import commit on `main`, tagged `v0.9.0`, message per `rules/git-flow.md → ##
      Commits`; remote `origin` is the owner's public GitHub repository
- [ ] `docs/USAGE.md → ## 4` says "clone" and names the tag

## Out of Scope

- Installer, `--dry-run`, `--uninstall`, profiles, examples, scrubbing of client project
  names (spec 11). Until spec 11, the README states that `sync.sh` overwrites
  `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.
- Branch protection (enabled at the public release, spec 11)
- Reconstructing history before the import commit

## Notes

- Decisions: ADR-0009 Decision 1 (name, publication, SemVer, `VERSION`, tracked `.ai/`).
- Clarifications 2026-09-17: single import commit; rename now, not at spec 11; P3 holds
  for on-disk consumer formats only.
- The rename of the local directory happens before `git init`; `sync.sh --from` is not
  needed afterwards.
- **Depends on `.ai/specs/completed/00-sensitive-data-scrub.md`.** Discovery must stop if the
  scrub's forbidden-token check is absent or failing: nothing sensitive may enter the
  first commit, because git history cannot be edited after publication.
