---
status: done
completed_task: Git source of truth
completed_at: 2026-10-20
---

# Make Orchestrail the Git source of truth and publish a minimal public slice

## Goal

The repository already has Git history, but its workflow contracts, runtime roots, and
task state need one versioned and portable source of truth. This spec standardizes those
contracts under the public name **Orchestrail**, preserves the existing ancestry, stamps
task state with the contract version, and publishes the minimum a contributor needs to
read the repository.

## Acceptance Criteria

- [ ] The checkout is renamed in place to `orchestrail/` after task validation and PR
      promotion; `git rev-parse --git-dir` succeeds there and no absolute checkout path
      is written into tracked content.
- [ ] No literal `agentic_workflows` or `agentic-workflows` remains in mutable repository
      content except the exact owner-approved source, historical, and live clone-URL
      entries recorded by the identity scan.
- [ ] `sync.sh` resolves its root as the directory containing itself, overridable by
      `ORCHESTRAIL_HOME`; `log-step.sh` resolves `ORCHESTRAIL_LOG_ROOT`, default
      `<root>/logs`; config paths use `~/.config/orchestrail/`
- [ ] `.gitignore` excludes `logs/runs/`, `logs/.active/`, `.claude/settings.local.json`;
      nothing under `.ai/` or `docs/` is ignored (ADR-0007)
- [ ] `bash validate-contracts.sh` passes, including the forbidden-token group from the
      scrubbed predecessor, before task branches are pushed; repository initialization
      and pre-initialization verification occurred in the predecessor.
- [ ] `VERSION` at the root contains `0.9.0`; `/pd-analyze` writes
      `contract_version: <VERSION>` after `spec_path:` in task `state.md`; readers tolerate
      its absence; `log-step.sh run-start` records `contract_version`
- [ ] `validate-contracts.sh` warns (does not fail) when any file under `rules/` is newer
      than `VERSION` in git history and `VERSION` is unchanged in the working tree
- [ ] `LICENSE` is Apache-2.0 with the owner as copyright holder (deferred 2026-10-20)
- [ ] `README.md` (≤ 60 lines): what Orchestrail is, that versions below 1.0.0 are
      unstable, what `sync.sh` writes into `~/.claude` and `~/.codex`, and links to
      `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `.ai/specs/README.md`
- [ ] Existing history is preserved and changes are delivered as an additive stacked PR
      series; the `v0.9.0` release tag is deferred until the stack is merged and the owner
      authorizes release (revised 2026-10-20).
- [ ] `docs/USAGE.md → ## 4` says "clone" and names the tag

## Out of Scope

- Installer, `--dry-run`, `--uninstall`, profiles, examples, scrubbing of client project
  names (spec 11). Until spec 11, the README states that `sync.sh` overwrites
  `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.
- Branch protection (enabled at the public release, spec 11)
- Rewriting or deleting existing history

## Notes

- Decisions: ADR-0009 Decision 1 (name, publication, SemVer, `VERSION`, tracked `.ai/`).
- Clarifications 2026-10-19: preserve existing Git ancestry and publish an additive PR
  stack; rename the local checkout after validation and PR promotion; P3 holds for
  on-disk consumer formats only.
- `sync.sh --from` remains available when a consumer needs a source checkout other than
  the directory containing the script.
- **Depends on `.ai/specs/completed/00-sensitive-data-scrub.md`.** Discovery must stop if the
  scrub's forbidden-token check is absent or failing before a public branch is pushed;
  existing ancestry remains unchanged.

## Change Log

### 2026-10-20 — reconciled from the completed source-of-truth work
- Repository setup | implemented-differently | Preserve existing ancestry and publish an additive stacked PR series instead of creating a single import commit. | Source: Task Analysis → Assumptions and Solution Design → Scope.
- Checkout rename | implemented-differently | Rename the existing checkout after validation and PR promotion because Git history already exists. | Source: Solution Design → Scope and Contract Check.
- Identity scan | implemented-differently | Enforce the exact owner-approved source, history, and clone-URL exceptions. | Source: Solution Design → Scope and Contract Check.
- License | not-implemented | Defer Apache-2.0 license creation until exact copyright-holder wording is supplied. | Source: Task Analysis → Assumptions and Deferred.
- Release tag | not-implemented | Defer the release tag until the stacked PRs are merged and the owner authorizes release. | Source: Task Analysis → Assumptions and Deferred.
