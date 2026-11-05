# architecture.md — current snapshot of the workflow system

## Purpose
Describes Orchestrail as it exists now: the layers of markdown, how they are
deployed into agent harnesses, how a task flows through them, and the contracts that
hold the files together. Updated only when a layer, a deployment target, or a contract
surface changes.

## Overview

Orchestrail is a **file-based specification of an AI-assisted SDLC**. Core workflow
behaviour lives in instructions that an LLM agent (Claude Code, Codex, or
Windsurf/Devin) reads and follows. Small local helpers provide validation, deployment
and telemetry, including the Python installer engine. The repository is the single source of truth;
`scripts/sync.sh` copies it into each harness's global configuration, and
`scripts/setup-new-project.sh` seeds a target project with a `CLAUDE.md`/`AGENTS.md`, rule
copies, skill symlinks, and a `.ai/` knowledge base. A task then moves through three
phases — Discovery, Execution, Validation — with all progress persisted in the target
project's `.ai/tasks/…/state.md`, and every orchestrated run appends telemetry to a
central log store that `/retro` reads.

Current inventory: 42 workflows, 14 rules, 4 principles, 10 shell scripts and 30 Python
helpers under `scripts/`, with automated consistency and smoke checks.

## Components

### Layer 1 — `rules/` (always-on contracts, 14 files)
Policies every workflow obeys. Deployed as Windsurf/Devin global rules, and — because
Claude Code and Codex have no rules directory — as skills under the mandatory `rule-`
prefix (five basenames collide with workflows). Key files:

| File | Owns |
|---|---|
| `workflow-globals.md` | phase contract, never-auto-advance, mode overrides registry, `--batch` semantics, flow tiers summary, **Canonical Status Formats** (`state.md`, `## Subtask Progress` leaf/composite blocks, `## Fix-Tasks`, `plan.md` statuses) |
| `workflow-reference.md` | file responsibilities, Description Amendment, Protected Sections Contract, multi-phase rules, `.ai/memory/state.md` entry format, **Autonomous Decision Protocol**, **Autonomous Subtask Classifier** (S1–S5, Type 2/3, tripwire), Decomposition Rules |
| `tdd.md` | RED/GREEN/pinned/n-a/failed states, test-level gate, frozen RED set, characterization mode |
| `git-flow.md` | preflight, stacked branch model, two-commit rule, no-attribution rule, pipeline identifiers out of the repo, safety rails with an Enforcement column (`hook: deny` / `hook: ask` / `hook: allow with restack journal` / `text only`), owner-approval protocol and never-evade rule, recorded git fields |
| `orchestration.md` | four roles (Orchestrator, Arbiter, Implementer, Validator), shared-file discipline (one writer per shared file), class A/B escalation, Discovery batch gate |
| `quick-flow.md` | four-condition gate, what quick skips and still mandates, mid-flight promotion |
| `run-log.md` | log store, three `scripts/log-step.sh` calls, field vocabulary, never-block rule, canonical per-boundary capability/evidence routing and receipt-confirmed suppression; unobserved prompt boundaries remain approximate |
| `language.md` | English in every project file |
| `phase-*.md` (5) | per-phase Context Bootstrap (which `.ai/` files to load and in what order), Blocker Reconciliation |
| `global-claude.md` | the content of `~/.claude/CLAUDE.md` — always-on essentials for Claude Code |

### Layer 2 — `principles/` (engineering standards, 4 files)
`code-quality.md`, `python-standards.md`, `testing-standards.md`, `infra-standards.md`.
Domain-quality rules, Python/FastAPI/GCP-centric. Deployed as Windsurf global rules and
as `principle-*` skills. `testing-standards` owns test *style*; `rules/tdd.md` owns test
*process*.

### Layer 3 — `workflows/` (slash commands, 42 files)

```
Orchestrators        phase-discovery  phase-execution  phase-validation  phase-pipeline
Atomic orchestrators phase-atomic-execution  phase-atomic-validation  phase-composite-validation
Discovery children   pd-analyze → pd-decompose → (pd-select-model) → pd-design → pd-finalize → pd-archive
Execution children   pe-execute → pe-finalize
Atomic children      pae-tests → pae-implement → pae-finalize ; pav-check → pav-propose → pav-close
Validation children  pv-contract → pv-review → pv-issues → pv-create-fixes (→ pv-classify-fixes) → pv-execute-fixes → pv-finalize
Orchestrated mode    spec-run, restack
Entry points         spec-draft, bugfix, onboard-legacy-project, adr-new, spec-sync
Utilities            context-pack, compress-state, retro, suggest-commit-message, suggest-pr-description, suggest-commit-pr
Reference            PIPELINE.md (not executable)
```

Every executable workflow has: a front-matter `description:`, an `Invocation:` line, a
`## Guard` section (detects completed work, asks before overwriting), numbered steps,
explicit `**stop**` points, and a report line. Children are callable standalone and must
run the full Context Bootstrap when they are.

### Layer 4 — `templates/`
`.ai/` skeleton (seeded into projects, never overwrites), `.ai-umbrella/` (multi-repo
root), `AGENTS.md` (Codex, per project), `codex-global-AGENTS.md` (→ `~/.codex/AGENTS.md`),
`subtask-description.md` and `spec.md` (reference skeletons), `stacks/python-fastapi.md`.

### Layer 5 — scripts
| Script | Role |
|---|---|
| `scripts/validate-contracts.sh` | Consistency and smoke checks across layers 1–3, including bidirectional canonical JSON-table/runtime contract comparison (`--run-log-contract-only`); includes an optional tracked-file public-hygiene scanner using local patterns (`--hygiene-only`, `--root`, `--denylist`); run by `scripts/sync.sh`; any failure blocks deploy |
| `scripts/validate-task.sh` | applies the same contracts to one task directory's artifacts; run by `/pd-finalize` and `/pe-finalize` |
| `scripts/sync.sh` | validate → copy to Windsurf, Claude Code, Codex → walk every project with `.devin/` and refresh its rule copies and skill symlinks |
| `scripts/setup-new-project.sh` | seed a project (auto-detects umbrella `../.ai/`) |
| `scripts/setup-umbrella.sh`, `scripts/setup-all-repos.sh` | multi-repo initialization |
| `scripts/link-skills.sh` | workaround: symlink global skills into a project's `.claude/skills/` |
| `scripts/log-step.sh` | validates complete producer arguments and exact legacy aliases before append-only JSONL writes; optional-jq legacy fallback; sorted runtime `contract` export and read-only `lint` diagnostics/summary; executable integer `ts_ms` boundaries; optional correlated identities and spans use bounded per-run flock, private active-only deduplication and matching JSON acceptance receipts; jq is required for lint and correlated writes, with flock/truncate additionally required for correlated writes; exits 0 on every error |
| `hooks/log-step-hook.sh` | Bash/jq/flock dispatch, status and serialized fallback; native Stop/SubagentStop adapter gates the most-specific registered project before private/transcript/log reads, validates canonical markers and native Skill evidence, freezes native/report-bound delivery for receipt-confirmed retries, and retains exclusive fallback ownership; private records under the XDG state directory contain no conversation text |
| `scripts/install-hooks.sh`, `scripts/install-hooks.py` | Bash lifecycle entrypoint guards Python 3.11+ before a typed source-only standard-library engine loads; the engine takes the event set from the manifest and validates each event's single group against its own declared handler (exact field set, `bash` command, one `@ORCHESTRAIL_HOME@/hooks/<name>.sh` argument substituted to the resolved physical path of a readable non-symlink script (unreadable → `invalid-source`); each event's handler declares the one failure mode fixed per event (`PreToolUse` block, `Stop`/`SubagentStop` continue; any other event is `invalid-manifest`); a `PreToolUse` group needs a matcher), requires `hooks/git_rails.py` and `scripts/log-step.sh` in the source, reads `harness/claude/permissions.json` (exact deny-only `Bash(...)` rules with no `*` and no inner `)`) on install only and merges them into `permissions.deny`, keeping user rules and their order, with exact `owned_permissions` counts and `created_permissions` containers; receipt `schema_version` 2 when it holds permission state and version 1 form otherwise, so an earlier installer can still read the receipt after uninstall; version 1 receipts are read and migrated; accepts event-shaped receipt claims so removal never reads the manifest or the fragment; the engine preserves user settings numeric lexemes, tracks exact inserted handler/group multiset quotas, serializes installation and recovers prepared before/after settings replacements without overwriting external edits; Python is required for installation/removal, while jq/flock gate installation only |
| `hooks/git_rails.py` | Typed single-file standard-library git-rails decision core: event validation, strict registry snapshot (writer predicate → registry-error), small shell grammar parser (recursion depth 3, 4096 tokens, quote-aware expansion skipping), a walker tracking a logical working directory with uncertain states for failed cd, stack rotation, CDPATH and shopt, plus anchors (every directory the command names) that decide when an unverifiable form matters; basename-matched wrappers; a DATA_PROGRAMS allowlist for programs given a git/gh word; stdin-fed shells opaque; sanitized read-only git layer (2 s per read, process-group kill); effective-repository and alias resolution; git parse-options helper with ambiguity candidates; the opaque-invocation rule (R31, including GIT_*, HOME, XDG_CONFIG_HOME and PATH prefixes, statements and exports) ahead of a per-subcommand rule table: staging rules (blanket flags, literal-file operands checked with `ls-files`, interactive forms, forced ignored paths checked with `check-ignore` → ask) and commit rules (commit-all, path operands, static message sources from -m, -F file up to 1 MiB, -F - heredoc or here-string on fd 0, the commit-message heredoc, --trailer, and --amend --no-edit; forbidden co-author trailer, task and decision-record identifier patterns; amend of a commit contained in refs/remotes → ask); ambiguous option prefixes are evaluated as every candidate; the parser records fd-0 input redirections so only the effective stdin heredoc counts; a sticky state-may-change mark: once any earlier command in the same Bash command may write (in any scope; directory changes, assignments, exports, data programs and read-only git without a file-writing redirection or option are exempt), rules consult a shared helper before reading repository or file state and deny that read (message file, HEAD message and trailer configuration → commit-message-unverifiable; operands, remote-tracking reachability, alias and work-tree lookups → unsupported-form); push rules: a push parse-options table, R11 dry-run allow unless the readable configuration runs a program; unsupported receive-pack/exec/on-demand submodule options and the target remote's configured receivepack, on-demand submodule recursion or submodule.recurse, the target remote from the operand, --repo or branch.<current>.pushRemote → remote.pushDefault → branch.<current>.remote → origin (configured remotes only; URL, path, unknown name or remote.<r>.push → push-target-unknown), destinations from refspecs split at the last colon (short names under heads/ or tags/ read as refs/<name>, failing closed) or push.default read from one config snapshot, the current branch and one for-each-ref; R13–R18 in matrix order over every destination; a shared protected-set API (DEFAULT_PROTECTED, protected_branches, local_protected_branches, is_protected); and a replaceable LEASE_VERIFIER(LeaseRequest, Invocation, Context) → LeaseVerdict interface (LeaseRequest carries each destination's source); a destination named by more than one lease is not explicit (git applies the first lease), so the push asks explicit-lease; destructive and merge rules: parse-options tables for reset, clean, branch, update-ref, checkout, switch, rebase, merge and pull, R20 reset --hard, R21 clean without -n (-i unsupported-form), R22/R23 branch and ref deletion (symbolic refs followed unless --no-deref; --stdin unsupported-form) through a replaceable DELETION_VERIFIER whose shipped implementation grants no exception, R24 protected-ref rewrites against the local protected set (forced creation and update-ref follow symbolic branch refs to their target; move and copy act on the literal names) (unknown origin default → default-branch-unknown), R25 rebase --abort/--show-current-patch allow, R26 every other rebase through a replaceable REPLAY_VERIFIER, R27/R28 merge and pull on a protected current branch; pull --upload-pack and the fetched remote's configured uploadpack → unsupported-form; a rebasing pull with rebase.updateRefs → ask protected-ref-rewrite (R28), R29 gh pr merge, R30 gh api merge endpoints and GraphQL merge and merge-queue mutations (mergePullRequest, enablePullRequestAutoMerge, mergeBranch, enqueuePullRequest) (file-sourced bodies unsupported-form); current-branch, protected-set, symbolic-ref and rebase-state reads deny after a same-command state change; git command runners (submodule foreach, bisect run, filter-branch --setup and command filters, difftool -x/--extcmd) are opaque → unsupported-form; restack journal verification: `<git-common-dir>/orchestrail-restack/<64-hex>.json` only (non-blocking, no symlinks, regular files ≤1 MiB, strict UTF-8 JSON without duplicate keys or NaN/Infinity constants, schema_version 1, file name = sha256(task_path)); any unusable journal asks; exactly one journal passing every check verifies; the replay verifier checks the exact `--onto <new> <old> <branch>` form (first order entry onto target.sha, later ones onto the previous replayed_tip) and one-word --continue/--skip on a stack branch (a configured rebase.updateRefs, read with `git config --type=bool`, invalid values counted as set, makes them ask with failure update-refs because git would also move other branches, as does stored rebase-merge/update-refs state at --continue/--skip), the lease verifier checks every destination (order, protection, publication authorization, replayed tip, source naming the branch, explicit lease = expected_remote_tip or empty for "absent", not forced); asks carry the failed check in Decision.failure (an R16 ask with an unverified lease names branch-protected; an R17 ask names forced when the lease fails on that ground; an allowlist shell-option scanner following bash's grammar (known -/+ letters, every o/O taking a word; the GNU long options only before the first short option, --rcfile/--init-file taking a word; -- ending options); a single-dash spelling of a long option, an unknown option word, or a script operand naming standard input (/dev/stdin, /dev/fd/N, /proc/<self|pid>/fd/N) is opaque; only `bash|sh -c '<literal>'` is parsed; busybox is a wrapper whose next word is the program; repository redirects are anchored after a failed cd as well); environment variables, marker files and the word restack are never evidence; most-severe combination; never writes, never runs gh or network git; entry point and adapter: main reads stdin up to 1 MiB under a 5 s wall-clock budget, commands over 64 KiB of UTF-8 → limit-exceeded in a registered cwd, a test-only fault seam that can only deny, catch-all internal-error; respond(decision, event, environ) maps to the Claude Code protocol (deny exit 2 + stderr, ask exit 0 + the exact hookSpecificOutput JSON + stderr, allow/not_applicable exit 0 silently, never "allow"); an ask outside ASK_CAPABLE_MODES (default, auto; drift-checked against the capability record) becomes deny owner-approval-unavailable keeping its rule id; four-line diagnostics of at most 1 KiB from RULE_PATH, Decision.summary, the failed check and the NEXT_STEPS table of all 29 reason codes, with control characters replaced and UTF-8-safe truncation; the registry is opened non-blocking and must be a regular file; a killed read drains for at most 0.5 s; main catches the budget signal around run, so a signal inside the failure handlers still denies limit-exceeded |
| `hooks/git-rails.sh` | Bash PreToolUse entrypoint for the Bash tool: resolves its own directory CDPATH-safe; with head and tr available it reads at most 1 MiB + 1 byte of the event and exits 0 without Python when the registry file is absent or the raw event has no git/gh word (the relevance pattern, with a JSON escape also counted as a boundary); without head or tr it skips the read and the prefilter and hands the unchanged stdin to the core; a registry behind an existing directory without search permission counts as present, so the core answers registry-error; a missing or older python3 denies runtime-unavailable with the rule line and next step read from the core, or a fixed wording without sed; otherwise execs `python3 -I` on the core; writes no file |
| `scripts/run-log-timing.sh`, `scripts/run-log-timing.py` | Explicit-file offline Bash launcher and typed Python 3.11+ standard-library engine; private unchanged snapshots and complete canonical producer lint gate exact integer interval/graph analysis, decimal-string totals and exact ratios; jq is required for eligibility, unavailable inputs/dependencies never become measured zeros |

`harness/claude/hooks.json` contains the portable native hook fragment: the git-rails `PreToolUse` group for `Bash` (`onFailure: block`) and the Stop/SubagentStop logging groups (`onFailure: continue`). `harness/claude/permissions.json` is the deny-only permission fragment `{"permissions":{"deny":[…]}}`: five exact rules for blanket staging and commit-all, defence in depth beside the hook, each with a positive and a negative fixture under the recorded match semantics. Claude and Codex capability declarations under `harness/` distinguish mechanism support, current installation status and demonstrated checkpoint coverage. Sync rebuilds the existing global instruction bodies and appends each capability block and installation result once; installation unavailability does not interrupt the other deployment targets or consumer refresh. The Claude capability record also carries a verified `git-rails` section (PreToolUse/Bash exit and JSON protocol, the anchored `git-rails ask-capable modes:` allowlist, permission-rule match semantics, the blocking failure option, limitations and residual risks X1–X10); the Codex record declares `git-rails: none (textual rules only)`. Contract checks in `scripts/validate-contracts.sh` pin each field.

Project setup is the sole writer of the XDG configuration project registry. It registers physical canonical roots idempotently under a dedicated lock with atomic replacement, preserves existing entries and rejects newline paths. The hook adapter only reads this registry; sync does not register or prune project roots.

### Executable acceptance checks

`tests/log-step.sh` copies the helper, canonical contract and workflows into a disposable checkout and runs the focused producer, lint, retrospective and drift checks in separate Bash processes. Explicit temporary log/workflow roots and per-operation checksums isolate fixtures from real logs; exit and signal traps clean up the temporary tree.

`tests/log-step-hook.sh` exercises native input, explicit dispatch correlation, exact report markers, bounded transcript evidence, private state and competing delivery routes in disposable home/config/state/project/log roots. Run it through `bash scripts/validate-contracts.sh --hook-adapter-only`; the default validator includes the same acceptance suite.

`tests/hook-install.sh` covers owned installation/removal, lossless numeric settings, multiset quotas, malformed inputs, concurrent registration, interrupted replacement recovery and isolated multi-harness sync. The focused `--hook-install-only` mode and default validator run the same lifecycle acceptance suite without real-home deployment.

`tests/hook-workflow-contract.sh` combines instruction-contract assertions with isolated public adapter/producer composition. The focused `--hook-workflow-only` mode and default validator check one-route delivery, canonical receipts, approximate unobserved boundaries and the existing test-definition return's dispatch/report handoff. These are synthetic fixtures; they do not claim live model compliance or event firing. The same worker, return points and GREEN/validation batches remain intact.

`tests/hook-timing.sh` checks exact interval arithmetic, graph quarantine, historical/approximate exclusions, strict snapshot/lint completeness and a two-run installation-to-removal lifecycle. The focused `--hook-timing-only` mode and default validator run the same isolated acceptance suite. The correlated producer fixture also proves actual partial output is rolled back before one accepted retry. Existing adapter/producer fixture bodies retain their behavior after mandatory annotation harmonization.

`tests/hook-shell-quality.sh` uses syntax-only Bash and standard-library inspection to enforce focused native/producer function size and positional APIs. Named predicate/lifecycle exceptions have measured ceilings; unchanged baseline exclusions are fingerprinted. The focused `--hook-shell-quality-only` mode and default validator run the same contract without executing inspected source or requiring AST-Grep.

`tests/git-rails.sh` is the table-driven git-rails suite (decision and resolution tables plus unit cases for options, combination and module surface). It uses disposable repositories, registries and fake slow or recording git with isolated HOME/XDG, and asserts byte, mode and mtime identity of every fixture tree around each call. Every decision table also runs end to end through `hooks/git-rails.sh` (one hook run per case, compared byte for byte with the in-process adapter), plus entrypoint fast-path, protocol, diagnostics, failure-mode, limit and independence classes using a Python-free PATH. The focused `--git-rails-only` mode and default validator run it.

### Layer 6 — `logs/` (central telemetry store)
`logs/runs/<ts>-<pipeline>-<id>.jsonl` + `.md` digest, `.active/` for open runs.
Cross-project by design; gitignored; read only by `/retro`.

### Layer 7 — `docs/` (documents about the system)
`docs/USAGE.md` (operating manual), `docs/SPEC-RUN-QUICKSTART.md`, `docs/audits/`
(`AUDIT-PROMPT.md`, `2026-07-21-logic-audit-fixes.md`), `docs/analysis/`
(`2026-09-16-comparative-analysis.ru.md` and its TL;DR), `docs/README.md` (index).
Placement rule: `.ai/principles/coding.md → Document placement`. The root holds only
`CLAUDE.md`, scripts, and source directories.

## Data Flow

```
author edits rules/ workflows/ principles/ templates/
        │
        ▼
scripts/validate-contracts.sh ──fail──▶ deploy blocked
        │ pass
        ▼
scripts/sync.sh ──▶ ~/.codeium/windsurf/global_{workflows,rules}/
        ├─▶ ~/.claude/skills/{<wf>,rule-<r>,principle-<p>}/SKILL.md + ~/.claude/CLAUDE.md
        ├─▶ ~/.codex/skills/… + ~/.codex/AGENTS.md
        └─▶ every project with .devin/: refresh .devin/rules, .windsurf/rules, .claude/skills symlinks
        │
        ▼
scripts/setup-new-project.sh (per project) ──▶ CLAUDE.md, AGENTS.md, .ai/ skeleton, .gitignore (.ai/ untracked)
        │
        ▼
spec in .ai/specs/NN-slug.md
  ──▶ /phase-discovery  ──▶ .ai/tasks/todo/task-NN-slug/{state.md, plan.md, T-XX/description.md}
  ──▶ /phase-execution  ──▶ per T-XX: pae-tests (RED) → pae-implement (GREEN) → pae-finalize → pav-*
  ──▶ /phase-validation ──▶ contract → review → issues → fix-tasks → finalize → ADR, progress.md, spec-sync
  (or /spec-run: same, plus Arbiter, stacked branches, test:/feat: commits, draft→ready PRs)
        │
        ▼
scripts/log-step.sh ──▶ logs/runs/*.jsonl ──▶ read-only lint ──▶ /retro usable observations ──▶ recommended edits to this repository
```

## Contract surface (what must stay consistent across files)

- **Canonical Status Formats** (`workflow-globals`) — every reader/writer of `state.md`
  and `plan.md`; readers key on field names, never on position; missing `atomic-tests:`
  is read as `not-started`.
- **Protected Sections Contract** (`workflow-reference`) — what `/compress-state` may never
  remove (`notes:`, `target_files:`, git fields, `tdd:` lines, composite blocks,
  `## Improvement Proposals`, `### Fix Classification`).
- **Cross-reference syntax** — `<file> → ## <Section>`; offline instruction checks
  validate canonical workflow/rule section targets, alongside the existing contract checks.
- **Mode overrides registry** (`workflow-globals → Workflow-declared mode overrides`) —
  the only place a workflow may declare autonomy; `phase-pipeline → ## Pipeline
  Overrides` is the detail.
- **`--batch`** — proposal callers record, prompt for nothing, apply nothing.
  `/pae-tests --batch` only suppresses duplicate digest display; it grants no authority.
- **Rule-name resolution** — bare basename on Windsurf/Devin, `rule-<name>` skill on
  Claude Code/Codex.
- **Active-run metadata** — a fixed format header and escaped values preserve multiline caller text without interpreting it as records; ordinary legacy metadata remains readable. JSONL events retain their existing schema.
- **Run-log vocabulary** — the helper enforces event-specific enums, bounded counts, exact legacy aliases, and safe run identifiers through one runtime contract exposed by `contract`; rejected arguments leave accepted event state unchanged.

## External Dependencies

- Agent harnesses: Claude Code (skills, `CLAUDE.md`, sub-agents), OpenAI Codex
  (`AGENTS.md`, skills), Windsurf / Devin Desktop (global workflows and rules).
  Model and worker requestability must be observed from the active session; harness
  names and logging declarations alone do not establish support.
- Tools invoked by workflows: `git`, `gh` (PRs, only with `--allow-pr`), `jq`
  (`scripts/log-step.sh` digests, `/retro`), `bash`, a web search capability (explicit model-catalog refresh only).
- Script source defaults resolve to the repository root, the parent of `scripts/`. `ORCHESTRAIL_HOME` overrides source selection; `scripts/sync.sh --from` takes precedence. Setup helpers normalize and propagate the selected root to children. `ORCHESTRAIL_LOG_ROOT` overrides the repository-root `logs/` directory. Documentation paths are placeholders.

## Workflow maintenance baseline — 2026-10-28

Workflow entry points now expose explicit Guards and invocation forms. Parent/child
context reuse requires available, current sources for the same resolved project; fresh
workers and standalone children bootstrap independently. Context packs still verify
metadata, not content hashes. Canonical phase rules own loading, and canonical protocol
rules own the classifier, promotion stops and permitted specification writes.

Finalization records completion after evidence, qualifying ADRs and authorized spec
reconciliation. Source cleanup does not implement the planned naming/harness migration,
packet tooling or parallel composite execution. The optional catalog
helpers below are a separate additive feature.

## Enforced git rails

Task 06 delivers a Claude Code `PreToolUse` hook for `Bash` (`hooks/git-rails.sh` prefilter +
single-file stdlib core `hooks/git_rails.py`), a deny-only `harness/claude/permissions.json`,
per-event installer validation with receipt `schema_version: 2`, `tests/git-rails.sh` with a
`--git-rails-only` validator mode, and an `Enforcement` column in the git-flow Safety rails.
Delivered as stacked PRs #64–#75 (merge pending). Shell strings are analysed only in the exact
`bash|sh -c '<literal>'` form, with option words read through an allowlist of bash's grammar;
every other command-string or stdin spelling is opaque and denies inside registered projects.
Operational hazard: the registered entrypoint runs from this checkout and blocks on failure,
so uninstall before checking out a revision without it (runbook). `git commit … && git push`
in one Bash call is denied by the same-command state-change mark; run them separately.
The decision core `hooks/git_rails.py` (parser, resolver, R31, staging, commit, push, destructive, ref-rewrite, rebase and merge rules, protected-ref set, lease-, deletion- and replay-verifier interfaces, restack journal verification) , the hook entrypoint `hooks/git-rails.sh` with the core's adapter and diagnostics, and `tests/git-rails.sh` with `--git-rails-only` exist; the PreToolUse registration (`harness/claude/hooks.json`, per-event validation in `scripts/install-hooks.py`) exists; the deny fragment `harness/claude/permissions.json` with receipt version 2 and version 1 migration exist; the safety-rails contract exists: an Enforcement value on all 21 Safety-rails rows, the owner-approval protocol, the recovery journal documented in `workflows/restack.md → ## Recovery journal` with the forms the recovery workflow uses (the hook allows any forced push or replay that exactly one journal verifies for every destination; a set rebase.updateRefs stops the replay), the statement that the hook still denies unverifiable forms and every relevant command while the registry or runtime is unusable, only an amend of a published commit is a hook-ask rewrite row while other local rewrites of a pushed unprotected branch are textual (only the later forced push asks), the protected set defined once on an anchored line (target remote default branch, main, master, release/*, orchestrail.protectedBranch globs; origin for local operations; unknown default → default-branch-unknown), git reset other than --hard unchecked on every branch, pull --ff-only from the upstream allowed, one unusable journal file making every journal check ask, and capability residuals X1–X20 (X20: gh aliases, gh pr close --delete-branch and gh api ref writes are not enforced). Decision record ADR-0017 (Accepted).

## Usage telemetry

The current source provides optional explicit-input telemetry normalization, immutable usage
publication, evidence-based resolution and exact pricing, retrospective reports, and
owner-controlled warnings. Normalization, analysis and status emit to pipes or sockets.
Report publication and warning delivery require operator-protected directories; warning
state has one authorized cooperative writer. The only built-in reviewed source profile is
synthetic, and an independent signing authority is an external deployment requirement.
Existing lifecycle logging remains nonblocking and optional telemetry failures preserve
accepted evidence.

## Optional model catalog helpers

`scripts/model-catalog.py` validates a versioned Markdown payload and its derived tier table,
inspects freshness, and atomically installs an explicitly supplied validated candidate. Public
APIs include validate_catalog, inspect_catalog, refresh_catalog, tier_rows and default_catalog_path.
The helper never browses; explicit workflow refresh owns source research. Catalog ages below
14 days are fresh, 14–30 dated, and over 30 stale but usable with notice. Invalid evidence
preserves the session and reports selection unavailable.

`scripts/model_selection.py` exposes quality_floor, normalize_traits and select_model.
Independent ordinal quality floors and current-invocation support/context/tools/owner limits
precede economics. A suitable default is displaced only by qualified comparable total-cost
intervals; price bands and snapshots do not establish equivalent quality or expected cost.
Unknown evidence remains unknown. The recommendation is advisory and never executes models.

`scripts/model_plan.py` exposes read_plan, update_plan, write_plan and resolve_model.
Optional provider columns take precedence over legacy Model, including explicit empty cells.
Bulk writes preserve unrelated bytes and require explicit legacy migration decisions.
Resolution reports requested/resolved/actual separately; unsupported requests require an
independently suitable declared authorized fallback or stop. Actual identity remains unknown
without separate current-day matching execution evidence.

Focused offline gates are --model-catalog-only, --model-selection-only and --model-plan-only;
the same suites are included in default validation. All three helpers have passed focused
acceptance and independent review. Workflow integration has passed fresh independent revalidation.
The canonical model-column and resolution contract is owned by workflow-reference. The selector
uses cached lookup, explicit research/atomic refresh and session-preserving unavailable behavior;
all execution and discovery readers reference the same additive contract. Installed skills resolve
the guide from the same configured or already-verified source root as the helper, never CWD.
A read-only canonical preflight verifies helper siblings and guide schema/rubric sections; missing
guidance preserves inputs and reports selection unavailable. Leaf model intent applies to
Implementers; Arbiter and independent Validator workers retain separate session-default roles.
The on-demand catalog
guide contains the rubric, evidence ownership, rollback and executable fictional CLI examples.
The --model-workflow-only gate runs all four model suites plus unchanged instruction contracts;
default validation includes the same suites. The selector is 1,017 words. Fixture lookup timing
is measured separately from the unmeasured live 60-second target.
No real initial catalog, model execution, new production default, paid comparison, global
deployment, price ledger or full harness migration is introduced.

