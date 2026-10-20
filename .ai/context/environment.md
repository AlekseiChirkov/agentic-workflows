# environment.md — environments, paths, and configuration

## Purpose
Where the workflow system runs and what it assumes about the host. Read before any
change to `sync.sh`, `setup-*.sh`, `log-step.sh`, or to a path mentioned in a rule.

## Environments

There are no staging/production tiers; there are three **agent harnesses** the source is
deployed into, plus consumer projects.

### Claude Code (primary)
- Workflows → `~/.claude/skills/<name>/SKILL.md`
- Rules → `~/.claude/skills/rule-<name>/SKILL.md`; principles → `principle-<name>`
- `rules/global-claude.md` → `~/.claude/CLAUDE.md` (overwritten on every sync)
- Per project: `CLAUDE.md` (pointer or two-level protocol), `.claude/skills/<name>` symlinks
  to the global skills (workaround: a project-local `.claude/skills/` hides global skills)
- Only harness where `/spec-run`'s sub-agent model (Arbiter kept alive, Implementer paused
  at RED, separate Validator) is executable. Skills are model-invoked, not always-on.

### OpenAI Codex
- Same three skill layouts under `~/.codex/skills/`
- `templates/codex-global-AGENTS.md` → `~/.codex/AGENTS.md`
- Per project: `AGENTS.md` from `templates/AGENTS.md` (never overwritten; manual updates)
- No sub-agent orchestration; `/spec-run` is not executable here.

### Windsurf / Devin Desktop
- Workflows → `~/.codeium/windsurf/global_workflows/`
- Rules and principles → `~/.codeium/windsurf/global_rules/` (always-on by front matter)
- Per project: copies (not symlinks) of a fixed list of rule files in `.windsurf/rules/`
  and `.devin/rules/`; refreshed by `sync.sh` for every project that has `.devin/`.
- No sub-agents; the Orchestrator role degrades to a single session.

### Consumer projects
- Seeded by `setup-new-project.sh`: `CLAUDE.md`, `AGENTS.md`, `.ai/` (from
  `templates/.ai/`, never overwrites), `.gitignore` entries (`.ai/`, `.claude/skills/`).
- Consumer projects are recorded in the local registry; none is named here.

## Configuration

| Variable / path | Used by | Default | Notes |
|---|---|---|---|
| `ORCHESTRAIL_HOME` | `sync.sh`, `setup-*.sh` | the script directory | Empty values use the default; `sync.sh --from <dir>` and `--from=<dir>` override it; relative paths resolve from the caller directory |
| `ORCHESTRAIL_LOG_ROOT` | `log-step.sh`, `/retro` | `<repo>/logs` | store is gitignored |
| `ORCHESTRAIL_HOME` helper resolution | `rules/run-log.md`, orchestrator workflows, artifact checks | unset: skip optional logging | Configure one shared checkout; required artifact checks need a configured source |
| `$HOME/.claude`, `$HOME/.codex`, `$HOME/.codeium/windsurf` | `sync.sh`, `setup-new-project.sh` | — | harness locations |
| `.ai/context/runbook.md → ## Commands` (per consumer project) | `pae-implement`, `pae-tests`, `bugfix` | — | `test:` required for TDD |

Local configuration belongs under `~/.config/orchestrail/`. Keep machine settings
outside the checkout; configure `ORCHESTRAIL_HOME` with the checkout location and
`ORCHESTRAIL_LOG_ROOT` when selecting a different shared log store. These variables
are read from the environment; scripts do not automatically source configuration files.
Setup helpers normalize the selected source before invoking children. A missing
source directory fails before project initialization. `log-step.sh path` only prints
the selected path and never creates the store; an empty log override uses `<root>/logs`.

## Host
- Linux, bash, `jq` (required for run-log digests and `/retro`), `git`, `gh` (only for
  `--allow-pr`), `shellcheck` optional.
- Development host: the maintainer's workstation.
- Local Git history exists; remote publication remains withheld pending separate history remediation.

## Scrub note (2026-09-17)

Mutable repository content uses neutral placeholders and configured helper paths.
The public-hygiene validator scans all tracked files except its root pattern list and
the immutable source specification. Local logs, machine settings, and Git internals
are outside the manual sweep. The local checkout location remains private.
