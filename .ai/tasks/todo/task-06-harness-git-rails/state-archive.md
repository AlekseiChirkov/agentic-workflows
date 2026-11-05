# state-archive — task-06-harness-git-rails

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Turn the supported subset of `rules/git-flow.md → ## Safety rails` into a Claude Code
`PreToolUse` hook for the `Bash` tool that, inside registered projects only, denies
agent-fixable git violations with a fix-it diagnostic, asks the owner for owner-only
operations, allows a verified `/restack` replay and lease publication, and is
`not_applicable` everywhere else — deterministic, write-free, offline and fail-closed —
installed through the existing owned-hook installer with a deny-only permissions fragment,
documented in the contracts, and covered by an offline table-driven suite wired into
`scripts/validate-contracts.sh`.

### Affected Parts
- New: `hooks/git-rails.sh` (Bash entrypoint, prefilter, runtime check, `exec python3 -I`),
  `hooks/git_rails.py` (single-file stdlib core: input validation, registry, parser,
  resolver, rule matrix R01–R31, restack journal verifier, diagnostics, adapter mapping),
  `harness/claude/permissions.json`, `tests/git-rails.sh` (+ optional data/harness files
  under `tests/`).
- Changed: `harness/claude/hooks.json` (PreToolUse group), `scripts/install-hooks.py`
  (per-event manifest validation, receipt v2 `owned_permissions`, v1 migration),
  `scripts/install-hooks.sh` (only if the source check needs the new entrypoint),
  `tests/hook-install.sh`, `scripts/validate-contracts.sh` (`--git-rails-only`, default
  inclusion, contract checks), `rules/git-flow.md`, `workflows/restack.md`,
  `harness/claude/capabilities.md`, `harness/codex/capabilities.md`.
- Knowledge (orchestrator-written): new ADR + index, `.ai/memory/architecture.md`,
  `.ai/specs/README.md` roadmap order note.
- Effects: once `scripts/sync.sh` runs after merge, the hook is installed at user level for
  every Claude Code session, active only below roots in the XDG project registry. This
  machine has no registry file today, so installation alone changes no decision here.

### Codebase Analysis
Source revision read: `main` @ 196a022 (2026-11-03). Spec baseline `8c2fa08` is older; the spec
directs implementation against current local sources.

1. `rules/git-flow.md` — read to verify current Safety rails rows and preflight check 3.
   Rails table has 9 rows, `Policy` column only; "Branch deletion: Forbidden". Preflight 3
   already accepts tracked knowledge (ADR-0012). No difference that changes a rule.
2. `workflows/restack.md` — read to verify journal path and replay/publish command forms.
   Journal already lives at `<common-dir>/orchestrail-restack/<sha256-of-canonical-task-path>.json`
   with identity, branch points/tips, replayed tips, target, order, expected remote tips; replay
   is `git rebase --onto <new-base-sha> <base_commit> <branch>`, publish is
   `git push --force-with-lease=refs/heads/<b>:<expected-tip> origin <b>`. Matches §8.5 forms;
   schema (`schema_version`, `publication_authorized`, `"absent"`) is not yet documented.
3. `harness/claude/capabilities.md` — read to verify record shape. Logging-only record,
   `runtime: Claude Code 2.1.309`, `verified: 2026-10-25`; no git-rails section.
4. `harness/claude/hooks.json` — read to verify manifest shape. Stop/SubagentStop groups,
   handler `{"type":"command","command":"bash","args":["@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh"],"timeout":10,"onFailure":"continue"}`.
5. `harness/codex/capabilities.md` — read to verify Codex declaration (`hooks: no`).
6. `scripts/install-hooks.py` — read to verify installer coupling. `EVENTS = ('Stop','SubagentStop')`
   hard-coded; `load_manifest` requires exactly those events and one fixed expected handler
   (lines 316–336); receipts are `schema_version: 1` with `owned`/`created_groups`; source check
   requires `hooks/log-step-hook.sh` and `scripts/log-step.sh`. No `permissions` handling.
7. `scripts/install-hooks.sh` — read to verify lifecycle entry: Python 3.11 guard, jq/flock for
   install, exits 0 with an unavailable JSON on recoverable failure.
8. `scripts/validate-contracts.sh` — read to verify focused-mode wiring (lines 313–340:
   `if [ "${1:-}" = --x-only ]; then shift; exec bash tests/x.sh "$@"; fi`) and default
   inclusion (lines 5142–5180 run each suite and report). Group 26 scans only named rule/workflow
   files for `type(T-…)` scopes; no check scans tests or hooks for `T-NN`/`ADR-NNNN` strings.
9. `hooks/log-step-hook.sh → project_for` (deeper) — read to verify registry semantics:
   `$HOOK_CONFIG` lines, absolute, existing, already-canonical roots only; `/` matches all;
   longest matching root wins; non-canonical entries are skipped, not errors.
10. `tests/hook-install.sh` (deeper) — read to verify suite conventions: disposable roots,
    `[test-name ...]` selection, never deploys to the real home.
11. `tests/hook-shell-quality.sh` (deeper) — read to verify whether new hooks are auto-inspected:
    it inspects only named files (`hooks/log-step-hook.sh`, `scripts/log-step.sh`).

Files read: 11/12 (8 entry-points, 3 deeper).

Harness facts (spec §6.2/§6.3/§10.1/§10.3), checked during Discovery from the official docs
(https://code.claude.com/docs/en/hooks, /permissions, /permission-modes, read 2026-11-03;
local runtime Claude Code 2.1.317): PreToolUse exit 2 blocks and stderr is the reason Claude
receives; JSON `hookSpecificOutput.permissionDecision` ∈ allow/deny/ask/defer with
`permissionDecisionReason` (ask reason shown to the user); input carries `permission_mode` ∈
default, plan, acceptEdits, auto, dontAsk, bypassPermissions; in `auto` a hook `ask` goes to the
human prompt; `-p` with nobody to answer denies; hook `ask` behaviour in plan, acceptEdits,
dontAsk and bypassPermissions is not documented; `onFailure: "block"` exists (v2.1.295+) and
blocks the tool call on start failure, other exit codes, timeout or invalid output; `timeout`
is seconds; `command` + `args` spawns without a shell; `matcher: "Bash"` is exact; `Bash(x)`
permission rules are exact, `Bash(x *)`/`Bash(x:*)` are prefix; deny rules are evaluated
regardless of hook output. T-01 re-confirms and records these with version and date.

### Open Questions
None. The spec §14 step-2 stop condition ("ask decisions cannot reach a human in any
interactive mode") does not fire: `default` and `auto` deliver hook `ask` to a human.

## Archived Solution Design — Variants
- **V1 — Single-file core with a rule dispatch table and injectable verifiers.** `hooks/git_rails.py`
  holds pure functions (tokenizer → parser → resolver → per-subcommand rule functions → I3
  combination → adapter/renderer) over one frozen event record, plus one sanitized git-read
  function with the 2 s timeout. Rules register per governed subcommand in a dispatch table that
  each leaf extends. Branch-deletion exceptions, lease verification and replay verification are
  named callables with shipped default implementations (spec §8.7 interface; T-04/T-05 defaults,
  T-06 journal implementation). The ask-capable mode allowlist and the diagnostic rule path are
  module constants; a validator check keeps the allowlist equal to the anchored capability line.
  `hooks/git-rails.sh` is a dependency-free prefilter that `exec`s `python3 -I`.
  *Advantages:* matches spec D1/§7.1 1d (`-I`, one file), the typed stdlib style of
  `scripts/install-hooks.py`, deterministic, unit-testable by import, no runtime file parsing
  beyond registry/journal. *Disadvantages:* one large file (estimated 1,500–2,500 lines).
  *Risks:* file size; mitigated by sectioned layout and the dispatch table.
- **V2 — Package `hooks/git_rails/` (parser, rules, adapter modules) with explicit `sys.path`
  insertion; allowlist parsed from `harness/claude/capabilities.md` at runtime.**
  *Advantages:* smaller modules; capability record is the single runtime source.
  *Disadvantages:* `-I` requires manual path insertion (spec permits but adds an import seam);
  runtime Markdown parsing adds a failure mode on every relevant command and couples hook
  behaviour to documentation formatting; no existing multi-module Python package in the repo.
  *Risks:* an editorial change to the capability record silently changes enforcement.
- **V3 — Rules encoded as declarative data (JSON/YAML table) interpreted by a generic engine.**
  *Advantages:* matrix readable as data. *Disadvantages:* R04/R10/R18/R26 need git reads and
  cross-field logic the data form cannot express without an embedded mini-language; adds an
  abstraction absent from the codebase. *Risks:* overengineering.

## Archived Solution Design — Rejected
V2 (runtime Markdown coupling, import seam without a codebase precedent); V3 (generic engine
for logic that needs git reads; hypothetical flexibility). Ten-into-eight leaf merge (see
`plan.md → ## Decomposition Decisions`).
