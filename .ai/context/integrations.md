# integrations.md — harnesses and external tools the workflows depend on

## Purpose
Everything outside this repository that a workflow talks to, and the assumptions it
makes about each. Consult before changing a workflow that spawns agents, calls a CLI, or
searches the web.

## Integrations

### Claude Code (Anthropic) — agent harness
- Purpose: primary execution environment; skills, `CLAUDE.md`, sub-agents, hooks.
- Interface: `~/.claude/skills/<name>/SKILL.md` with front-matter `description:`;
  `~/.claude/CLAUDE.md` global instructions; per-project `CLAUDE.md`.
- Used by: every workflow; `/spec-run` relies on spawning sub-agents, keeping the Arbiter
  alive and addressing it by message, and pausing the Implementer mid-run.
- Assumptions: skills are model-invoked (not always-on) — hence `global-claude.md`
  duplicates the essentials; a project-local `.claude/skills/` hides global skills
  (`scripts/link-skills.sh`). Hooks and permission deny-lists are available but **not used yet**
  (`specs/03`, `specs/06`).
- Docs: https://docs.claude.com/en/docs/claude-code

### OpenAI Codex — agent harness
- Interface: `~/.codex/AGENTS.md`, `~/.codex/skills/<name>/SKILL.md`, per-project `AGENTS.md`.
- Used by: all workflows as skills; no orchestration.
- Assumptions: reads `AGENTS.md → ## Commands` directly; template changes do not propagate
  to existing projects.

### Windsurf / Devin Desktop (Codeium) — agent harness
- Interface: `~/.codeium/windsurf/global_workflows/*.md`, `global_rules/*.md` with
  `trigger: always_on`; per-project `.windsurf/rules/`, `.devin/rules/`.
- Assumptions: rules are truly always-on here; no sub-agents.

### git — version control of consumer repositories
- Used by: `/spec-run`, `/restack` (the only workflows allowed to write), preflight checks,
  `suggest-*` utilities (read-only).
- Rails: no `git add -A`, no push to base, no force-push outside `/restack`
  (`--force-with-lease` only), no `reset --hard`/`clean`, no branch deletion, no merge.

### GitHub CLI (`gh`) — pull requests
- Used by: `/spec-run --allow-pr` (draft PR creation, promotion to ready), `/restack --allow-pr`.
- Assumptions: remote `origin` exists and `gh auth status` succeeds; PR bodies follow
  `git-flow → ## Pull requests` and carry no attribution.

### `jq` — JSON processing
- Used by: `scripts/log-step.sh` (digest generation; degrades to a stub without it), `/retro`
  (all aggregation).

### Web search — model catalog
- Used by: `/pd-select-model` Step 0, every run, by explicit rule (no cached catalog).
- Cost observed: up to 3 h in run b905a8a5. See `specs/completed/04-model-catalog-cache.md`.

### Web fetch — spec and defect sources
- Used by: `/spec-draft` and `/bugfix` when given a URL (issue tracker, Sentry, docs).
- Assumption: a URL that cannot be fetched stops the workflow and asks for text.

### Consumer project `.ai/` — the knowledge base contract
- Every phase performs the Context Bootstrap from `rules/phase-*.md`: `principles/*`,
  `memory/architecture.md`, `memory/state.md`, `adr/index.md`, `context/runbook.md`,
  conditionally `context/integrations.md`, `context/environment.md`.
- `context/runbook.md → ## Commands` keys `test:`, `lint:`, `typecheck:`, `build:` drive
  automated verification; `test:` is mandatory for the TDD step.
