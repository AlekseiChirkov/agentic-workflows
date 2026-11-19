# runbook.md — operational procedures for Orchestrail

## Purpose
How to validate, deploy, audit, and recover the workflow system. The `## Commands` keys
are read by `/pae-implement` and `/bugfix` for the automated verification step.

## Commands
test:      bash scripts/validate-contracts.sh
lint:      for f in scripts/*.sh hooks/*.sh tests/*.sh; do bash -n "$f" || exit 1; done; command -v shellcheck >/dev/null && shellcheck -S warning scripts/*.sh hooks/*.sh tests/*.sh || true
typecheck: (none — no standalone checker configured; focused acceptance checks mandatory Python annotations)
build:     bash scripts/sync.sh --from "$(pwd)"

Notes:
- `test:` is the `smoke`-level validating tool for this repository. A new contract check
  that fails before a change and passes after it is the RED test (`rules/tdd.md`).
- `build:` deploys to the current machine's harness directories. To produce reviewable
  provider artifacts without installing them, use
  `scripts/sync.sh --from <source-tree> --stage <empty-directory>`.
  Staging runs the required preflight and never refreshes consumer projects.
- `scripts/validate-task.sh <task-dir>` checks one task's artifacts; run it manually when working
  on a task under `.ai/tasks/`.
- Focused hook suites use `scripts/validate-contracts.sh --hook-adapter-only`,
  `--hook-install-only`, `--hook-workflow-only`, `--hook-timing-only` and
  `--hook-shell-quality-only`. Runtime scenarios use disposable
  home/config/state/project/log roots rather than real user settings. The shell
  source contract uses syntax-only inspection, bounded named exceptions and
  fingerprinted unchanged baseline functions; it has no AST-Grep runtime dependency.
- `--git-rails-only` runs `tests/git-rails.sh`: the decision core and the hook entrypoint `hooks/git-rails.sh` end to end, in disposable repositories with isolated HOME/XDG and a Python-free PATH for the fast-path cases; about 3.5 min. The full validator takes about 34–52 min (longer under memory pressure); run it with nothing else in parallel, since under memory pressure a concurrent run can be killed because a contract-version fixture re-runs it on a copy (the separate validator-runtime specification addresses this). The git-rails hook uses bash; head, tr and sed only for its fast path (without them the core decides alone); Python 3.11+ for relevant commands.
- The registered git-rails entrypoint runs from this checkout and blocks on failure. Before checking out a revision without `hooks/git-rails.sh`, or before an earlier installer touches the receipt, run `bash scripts/install-hooks.sh uninstall` from the current checkout; otherwise every Bash call in every project is blocked until uninstall. Earlier installers refuse a receipt that holds PreToolUse or permission state.
- When `python3` resolves to a mise shim without a configured installed version,
  isolated-PATH fixtures cannot start Python and several suites fail. Use a
  verified system interpreter, e.g. `PATH=/usr/bin:/bin bash scripts/sync.sh
  --from <source-tree> --stage <empty-directory>`. Selecting an unknown mise
  version can start an installation; it is not required for verification.
- `bash scripts/check-spec-draft.sh` pins the `/spec-draft` review contract (critic, round
  limit, rubric and threshold) in about 30 ms. It runs standalone, outside the frozen validator
  inventory, so run it after every change to `workflows/spec-draft.md`.
- `python3 scripts/check-repo-set.py` runs the multi-repository `/spec-run` acceptance suite
  (the read-only `scripts/repo-set.py` helper against disposable git repositories, plus the
  instruction contract) in a few seconds. It is standalone, outside the frozen validator
  inventory, so run it after every change to `scripts/repo-set.py`, `workflows/spec-run.md`,
  `rules/git-flow.md → ## Multi-repository runs` or the `## Repositories` state format.
- `python3 -I scripts/audit-instructions.py extract|verify|render` is the read-only audit tool
  for rules, workflows and harness adapters;
  `python3 -I scripts/audit-instructions.py verify --root . --report docs/audits/<date>-rules-workflows-audit.md`
  must print nothing in the delivery repository at the delivery commit of an audit. On a later
  tree or a clone it may print `inventory-stale` (audited files changed),
  `review-commit-unknown` (the reviewed commit is absent, for example after a squash merge),
  `spec09-unavailable` (no single `.ai/specs/09-*.md`, for example once spec 09 is archived),
  `amendment-invalid` or `amendment-target-unknown` (spec 09 edited) and `req21-invalid` (the
  discovery rule renamed or changed); these do not reopen the audit. `render --write`
  regenerates the report's generated region. `python3 -I scripts/check-audit-instructions.py` runs its acceptance suite
  against disposable fixture roots. Both are standalone, outside the frozen validator
  inventory; run the suite after every change to `scripts/audit-instructions.py`, with
  `MISE_PYTHON_VERSION` set as above.
- Run `git update-index --refresh` in the root before
  `python3 -I scripts/audit-instructions.py extract`. The tool's git reads apply neither
  the attributes of the tree nor the user's or the system's attributes file, so a Git LFS,
  `ident` or eol-converted file whose index stat data is stale can read as changed; the
  refresh records it as unchanged first. The refresh is an ordinary git command with the
  repository's own attributes and filters, so run it only in a repository you trust.
- `--state-tool-only` runs `tests/state-tool.py` (the state tool's acceptance suite, about 30 s) through `scripts/validate-contracts.sh`; the default run includes it as `test_state_tool_acceptance`.
- Optional model helpers use offline focused suites `--model-catalog-only`,
  `--model-selection-only` and `--model-plan-only` through `scripts/validate-contracts.sh`.
  `--model-workflow-only` runs catalog, selection, plan, workflow and unchanged general
  instruction suites together, including temporary installed-skill guidance fixtures and
  worker-role authorization. They use fictional disposable catalogs and never execute
  a model or refresh the web. The complete isolated CLI example is in docs/MODEL-CATALOG.md.
- Installer and offline timing engines require Python 3.11 or newer, using only the
  standard library. Timing also requires jq-backed producer lint. Native hooks retain
  Bash/jq/flock dependencies; saved-state uninstall does not require jq/flock.

## Local configuration

Keep machine settings under `~/.config/orchestrail/`. Export `ORCHESTRAIL_HOME`
to select the shared checkout for setup helpers and workflow helper resolution.
Setup and sync scripts default to the repository root (the parent of `scripts/`) when the source override is unset or empty;
`scripts/sync.sh --from <dir>` and `--from=<dir>` take precedence over the environment.
Export `ORCHESTRAIL_LOG_ROOT` to select a shared log store; unset or empty values
use the helper checkout's `logs/` directory. Inspect it without creating files with
`bash "$ORCHESTRAIL_HOME/scripts/log-step.sh" path`.
Keep private hygiene patterns outside the repository and set
`ORCHESTRAIL_HYGIENE_DENYLIST` to their local file. The default is
`$XDG_CONFIG_HOME/orchestrail/hygiene-patterns.txt` or
`~/.config/orchestrail/hygiene-patterns.txt`. The full suite reports exact scans as
`SKIP` when no local pattern file exists; `bash scripts/validate-contracts.sh --hygiene-only`
requires a configured file and fails closed.

## Procedures

### Deploy a change
1. `bash scripts/validate-contracts.sh` — must report 0 failed.
2. `bash scripts/sync.sh` (or `scripts/sync.sh --from <dir>`). It re-runs validation, copies to Windsurf,
   Claude Code, Codex, then walks every project containing `.devin/`.
3. Verify: `ls ~/.claude/skills/ | wc -l`, `head ~/.claude/CLAUDE.md`, and in a harness
   type `/phase-discovery` to confirm autocomplete.
4. Restart open agent sessions — skills are read at invocation, `CLAUDE.md` at session start.

### Add a workflow
1. Create `workflows/<name>.md` following `.ai/principles/coding.md → Workflow file shape`.
2. Ensure the basename does not collide with a file in `rules/` (if it must, the rule
   deploys as `rule-<name>` automatically — but avoid it).
3. Add its row to `docs/USAGE.md → ## 7` and `## 9`, and to `PIPELINE.md` if it is a pipeline step.
4. If it writes a `state.md` section, add a "has writer" check to `scripts/validate-contracts.sh`
   group 1 and list the section in the Protected Sections Contract if `/compress-state`
   must preserve it.
5. If it is an orchestrator, add run-log calls per `rules/run-log.md`.
6. Deploy.

### Add or change a rule
1. Write the check in `scripts/validate-contracts.sh` first; run it; it must fail.
2. Edit the rule. Keep vocabulary on anchored definition lines.
3. Grep `workflows/ rules/ docs/ templates/` for every reader of the
   changed text; update them.
4. If it is always-on essential for Claude Code/Codex, update the summary in
   `rules/global-claude.md` and `templates/codex-global-AGENTS.md` (both are deployed
   verbatim).
5. `scripts/setup-new-project.sh` copies a fixed list of rule files into `.windsurf/rules/` and
   `.devin/rules/` — add a new rule to that list, and to the count in `docs/USAGE.md → ## 5`.
6. Record an ADR if a format, stop, or mode override changed. Deploy.

### Change a canonical status format
Follow `.ai/principles/coding.md → Changing a contract`. Additionally:
- Add the backward-compatibility sentence for readers in `workflow-globals`.
- Update `scripts/validate-task.sh` so existing task directories in other repositories still pass
  (or are reported as legacy, not failed).
- Update `compress-state.md` if the field is protected.

### Run the independent audit
1. Open a fresh agent session in this directory.
2. Paste `docs/audits/AUDIT-PROMPT.md` (everything below its first rule).
3. The auditor writes a report file only; it must not edit anything or run `scripts/sync.sh`.
4. Turn findings into a spec in `.ai/specs/` (the 2026-07 example is `docs/audits/2026-07-21-logic-audit-fixes.md`).

### Run a retro
1. `ls logs/runs/*.jsonl | wc -l` — below 5 the findings are anecdotes.
2. `/retro [--since <date>] [--pipeline <name>]` in an agent session. Requires `jq`;
   exact interval analysis additionally uses Python 3.11+. The offline timing helper
   accepts only explicitly selected files and never discovers or repairs history.
3. The report lands in `logs/retro-<date>.md`. Findings that name a file become specs.
4. `bash scripts/log-step.sh active` lists runs never closed with `run-end`.

### Initialize a consumer project
1. `cd <project>`; `bash <orchestrail>/scripts/setup-new-project.sh`.
2. Fill `.ai/context/runbook.md → ## Commands` (`test:` is required — `/pae-tests` stops
   without it), `CLAUDE.md → ## Standards`, `AGENTS.md → ## Project Context` and `## Commands`.
3. For an existing codebase run `/onboard-legacy-project` once.
4. Multi-repo: `scripts/setup-umbrella.sh` at the root first, then `scripts/setup-all-repos.sh` or
   `scripts/setup-new-project.sh` per service.
   One shared spec in a root that is not a git repository runs across its repositories with
   `/spec-run .ai/specs/<spec>.md --repo <directory>=<base-branch> …` from that root
   (`rules/git-flow.md → ## Multi-repository runs`); start with `--dry-run`.
5. Respect repository-owned tracking policy. New consumers keep `.ai/` ignored by default; existing tracked knowledge is preserved and is not a preflight failure.
6. A consumer that tracks `.ai/` gets the two state-tool ignore entries by adding `.state-tool.lock` and `.state.md.*.tmp` to its `.gitignore` by hand, or by rerunning `scripts/setup-new-project.sh`, which appends both and skips its `.ai/` entry where files under `.ai/` are tracked.

### Recover from a bad deploy
- Deployed copies are disposable. Fix the source here, re-run `scripts/sync.sh`.
- If a workflow skill shadows a rule skill (or vice versa), check that `rule-` prefixes
  are present: `ls -d ~/.claude/skills/rule-* | wc -l` must equal the count of `rules/*.md`.
- Project-local `.claude/skills/<name>` that are real directories (not symlinks) shadow
  the global skill; `scripts/sync.sh` deletes such copies for projects with `.devin/`, otherwise
  remove them by hand and re-run `scripts/link-skills.sh`.

### Recover a task whose state is corrupt
1. `bash scripts/validate-task.sh <task-dir>` — read every `[FAIL]`.
2. Repair the `## Subtask Progress` block by hand to the canonical format
   (`workflow-globals → Canonical Status Formats`); never delete `base_commit`, `commits`,
   `notes:`, or `tdd:` lines.
3. Re-run the same phase command; Guards will find the resume point.
4. Under `/spec-run`, Step 0 reconciles recorded branches against git; if a branch tip
   moved, decide by hand whether to reset the recorded `commits:` or the branch.

### Verify finalization changes without deploying
1. Run `/usr/bin/python3 scripts/check-phase-finalize.py`,
   `/usr/bin/python3 scripts/check-finalization-safety.py` and
   `/usr/bin/python3 scripts/check-finalization-workflow.py` sequentially.
   These standalone suites remain outside the frozen validator inventory; sync
   requires all three in addition to its complete existing preflight.
2. Complete independent scenario and cross-file contract review. Preserve actual
   failed attempts and recovered errors; a later pass does not erase them.
3. Follow the nested source-guard maintenance procedure in
   `tests/fixtures/validator-runtime/README.md` when reviewed dependencies change.
   Never expand its exceptions without inspecting the affected callsites.
4. Run `PATH=/usr/bin:/bin bash scripts/sync.sh --from <source-tree>
   --stage <empty-directory>` with no competing heavy checks. This performs the
   mandatory full validator and generates all provider artifacts.
5. Compare staged workflows, prefixed rules, principles and capability-appended
   global instructions with their canonical source. Retain the source revision,
   actual results and optional-tool limitations in task evidence.

### Close a merged consumer task
Use `/phase-finalize <task-directory|spec-path> --dry-run` for a read-only plan,
then the same invocation without `--dry-run` for the entire finalization.
Cleanup is mandatory and the ordinary invocation authorizes only the resolved
task's proven resources. Rerun the same command after resolving a blocker; the
versioned journal resumes unfinished work, including an original path after
archival. Finalization never merges PRs, commits knowledge or authorizes deployment.
Keep untracked umbrella knowledge local; never stage it in a participating child
repository. Missing required deployment evidence leaves task closure incomplete.
