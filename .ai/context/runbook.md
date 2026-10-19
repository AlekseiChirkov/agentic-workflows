# runbook.md — operational procedures for agentic_workflows

## Purpose
How to validate, deploy, audit, and recover the workflow system. The `## Commands` keys
are read by `/pae-implement` and `/bugfix` for the automated verification step.

## Commands
test:      bash validate-contracts.sh
lint:      for f in *.sh; do bash -n "$f" || exit 1; done; command -v shellcheck >/dev/null && shellcheck -S warning *.sh || true
typecheck: (none — markdown and bash only)
build:     bash sync.sh --from "$(pwd)"

Notes:
- `test:` is the `smoke`-level validating tool for this repository. A new contract check
  that fails before a change and passes after it is the RED test (`rules/tdd.md`).
- `build:` deploys to the current machine's harness directories; there is no build
  artifact. Use `sync.sh --from <dir>` when working on a copy outside the canonical path.
- `validate-task.sh <task-dir>` checks one task's artifacts; run it manually when working
  on a task under `.ai/tasks/`.

## Procedures

### Deploy a change
1. `bash validate-contracts.sh` — must report 0 failed.
2. `bash sync.sh` (or `sync.sh --from <dir>`). It re-runs validation, copies to Windsurf,
   Claude Code, Codex, then walks every project containing `.devin/`.
3. Verify: `ls ~/.claude/skills/ | wc -l`, `head ~/.claude/CLAUDE.md`, and in a harness
   type `/phase-discovery` to confirm autocomplete.
4. Restart open agent sessions — skills are read at invocation, `CLAUDE.md` at session start.

### Add a workflow
1. Create `workflows/<name>.md` following `.ai/principles/coding.md → Workflow file shape`.
2. Ensure the basename does not collide with a file in `rules/` (if it must, the rule
   deploys as `rule-<name>` automatically — but avoid it).
3. Add its row to `docs/USAGE.md → ## 7` and `## 9`, and to `PIPELINE.md` if it is a pipeline step.
4. If it writes a `state.md` section, add a "has writer" check to `validate-contracts.sh`
   group 1 and list the section in the Protected Sections Contract if `/compress-state`
   must preserve it.
5. If it is an orchestrator, add run-log calls per `rules/run-log.md`.
6. Deploy.

### Add or change a rule
1. Write the check in `validate-contracts.sh` first; run it; it must fail.
2. Edit the rule. Keep vocabulary on anchored definition lines.
3. Grep `workflows/ rules/ docs/ templates/` for every reader of the
   changed text; update them.
4. If it is always-on essential for Claude Code/Codex, update the summary in
   `rules/global-claude.md` and `templates/codex-global-AGENTS.md` (both are deployed
   verbatim).
5. `setup-new-project.sh` copies a fixed list of rule files into `.windsurf/rules/` and
   `.devin/rules/` — add a new rule to that list, and to the count in `docs/USAGE.md → ## 5`.
6. Record an ADR if a format, stop, or mode override changed. Deploy.

### Change a canonical status format
Follow `.ai/principles/coding.md → Changing a contract`. Additionally:
- Add the backward-compatibility sentence for readers in `workflow-globals`.
- Update `validate-task.sh` so existing task directories in other repositories still pass
  (or are reported as legacy, not failed).
- Update `compress-state.md` if the field is protected.

### Run the independent audit
1. Open a fresh agent session in this directory.
2. Paste `docs/audits/AUDIT-PROMPT.md` (everything below its first rule).
3. The auditor writes a report file only; it must not edit anything or run `sync.sh`.
4. Turn findings into a spec in `.ai/specs/` (the 2026-07 example is `docs/audits/2026-07-21-logic-audit-fixes.md`).

### Run a retro
1. `ls logs/runs/*.jsonl | wc -l` — below 5 the findings are anecdotes.
2. `/retro [--since <date>] [--pipeline <name>]` in an agent session. Requires `jq`.
3. The report lands in `logs/retro-<date>.md`. Findings that name a file become specs.
4. `bash log-step.sh active` lists runs never closed with `run-end`.

### Initialize a consumer project
1. `cd <project>`; `bash <orchestrail>/setup-new-project.sh`.
2. Fill `.ai/context/runbook.md → ## Commands` (`test:` is required — `/pae-tests` stops
   without it), `CLAUDE.md → ## Standards`, `AGENTS.md → ## Project Context` and `## Commands`.
3. For an existing codebase run `/onboard-legacy-project` once.
4. Multi-repo: `setup-umbrella.sh` at the root first, then `setup-all-repos.sh` or
   `setup-new-project.sh` per service.
5. Confirm `.ai/` is in `.gitignore` and untracked: `git ls-files .ai | head -1` is empty.

### Recover from a bad deploy
- Deployed copies are disposable. Fix the source here, re-run `sync.sh`.
- If a workflow skill shadows a rule skill (or vice versa), check that `rule-` prefixes
  are present: `ls -d ~/.claude/skills/rule-* | wc -l` must equal the count of `rules/*.md`.
- Project-local `.claude/skills/<name>` that are real directories (not symlinks) shadow
  the global skill; `sync.sh` deletes such copies for projects with `.devin/`, otherwise
  remove them by hand and re-run `link-skills.sh`.

### Recover a task whose state is corrupt
1. `bash validate-task.sh <task-dir>` — read every `[FAIL]`.
2. Repair the `## Subtask Progress` block by hand to the canonical format
   (`workflow-globals → Canonical Status Formats`); never delete `base_commit`, `commits`,
   `notes:`, or `tdd:` lines.
3. Re-run the same phase command; Guards will find the resume point.
4. Under `/spec-run`, Step 0 reconciles recorded branches against git; if a branch tip
   moved, decide by hand whether to reset the recorded `commits:` or the branch.
