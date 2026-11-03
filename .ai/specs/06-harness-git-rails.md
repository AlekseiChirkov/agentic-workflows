# 06. Enforced git rails for agent shell commands

## 0. Document control

| Field | Value |
|---|---|
| Status | Ready for Discovery. Nothing described here is implemented, installed or enforced yet. |
| Revision | 2026-11-03. Replaces the 2026-10-28 revision; requirement and criterion IDs were renumbered (no other document cites them). |
| Baseline | Owner text was reviewed at `8c2fa08c18115ffcf38a1798742c41e53a2c7461` against the [git-flow contract](https://github.com/AlekseiChirkov/agentic-workflows/blob/8c2fa08c18115ffcf38a1798742c41e53a2c7461/rules/git-flow.md) and the [restack workflow](https://github.com/AlekseiChirkov/agentic-workflows/blob/8c2fa08c18115ffcf38a1798742c41e53a2c7461/workflows/restack.md). Implement against the current local `rules/git-flow.md` and `workflows/restack.md`, not the pinned copies. |
| Authority | ADR-0008 (enforcement moves to the harness); ADR-0009 Decision 5 (git-rails scope); owner decisions of 2026-11-03 recorded in §3. |
| Roadmap prerequisites | 13 and 05 (see §2.3 for what is actually consumed). |
| Normative words | **MUST**, **MUST NOT**, **SHOULD** and **MAY** are binding as in RFC 2119. Everything not marked as an example is normative. |

## 1. Goal and threat model

### 1.1 Goal

Today the git safety rails (`rules/git-flow.md → ## Safety rails`) are prose that an agent
may misread or forget. This spec turns the supported subset into a Claude Code `PreToolUse`
hook that inspects every `Bash` tool command **before it runs** and:

- **denies** commands the agent can fix itself (blanket staging, forbidden commit text,
  unverifiable forms), with a diagnostic that says how to fix them;
- **asks the owner** for commands that only the owner may authorize (protected-branch push,
  force push, branch deletion, rebase outside `/restack`, history destruction, PR merge),
  with an explanation that lets the owner approve or reject that single command;
- **allows** a verified `/restack` replay and its explicit-lease publication without asking;
- **stays out of the way** everywhere else.

### 1.2 Threat model

The hook protects against **mistakes** by an agent acting in good faith: wrong flags,
forgotten rules, wrong target branch, copy-pasted commands. It does **not** protect against
a deliberately evasive agent or a malicious machine owner: the agent can write any file the
hook trusts (registry, restack journal, git config). Every guarantee in this document is
scoped by that model and by the residual risks in §13. Documentation MUST NOT describe the
hook as a sandbox or as protection against arbitrary shell code.

## 2. Scope

### 2.1 In scope

1. `hooks/git-rails.sh` (entrypoint) and `hooks/git_rails.py` (decision core).
2. A `PreToolUse` registration for the `Bash` tool in `harness/claude/hooks.json`.
3. A `permissions.deny` fragment in `harness/claude/permissions.json` (§10.3).
4. Extending `scripts/install-hooks.sh` / `scripts/install-hooks.py` to own the new entries.
5. A documented schema for the `/restack` recovery journal (§8.5), written by
   `workflows/restack.md` and read by the hook.
6. Updated contracts: `rules/git-flow.md`, `workflows/restack.md`,
   `harness/claude/capabilities.md`, `harness/codex/capabilities.md`.
7. Tests `tests/git-rails.sh`, extensions to `tests/hook-install.sh`, and a
   `--git-rails-only` mode in `scripts/validate-contracts.sh`.
8. A new ADR and updates to `.ai/memory/architecture.md`.

### 2.2 Out of scope

- RED-set / GREEN-phase test protection (separate future spec, ADR-0009 Decision 5).
- Reading or enforcing TDD state. The hook never reads `.ai/tasks/**`; its decisions are
  independent of `atomic-tests:` values (`red`, `pinned`, `n-a`, legacy blocks).
- Verifying publication authorization (`--allow-pr`); it remains a textual rule.
- Commit-message rules other than the three patterns of §8.3, and all PR title/body rules;
  they remain textual.
- Git operations outside the rule matrix (§13 lists notable ones).
- Tools other than `Bash` (for example, `Edit`/`Write` touching `.git/`).
- Harnesses without a verified blocking pre-tool hook (Codex today): textual rules only.
- Network access of any kind from the hook.
- The temporary-child-branch deletion exception (owned by spec 12, see §8.7).

### 2.3 Prerequisites and consumers

| Spec | Relationship | What exactly |
|---|---|---|
| 05 (done) | Prerequisite | Installer engine and receipt model (`scripts/install-hooks.py`); coexistence with the Stop/SubagentStop logging hook. |
| 13 | Prerequisite (roadmap order) | Final `harness/<name>/` layout and sync mechanism. 06 MUST place its files where 13 puts adapter files. The project registry it reads already exists (delivered by 03). If 13 is not done when 06 starts, **stop and ask the owner** whether to implement against the current layout. |
| 03 (done) | Consumed | Project registry `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects` and its most-specific-root semantics in `hooks/log-step-hook.sh → project_for`. |
| 12 | Consumer | Adds the child-branch deletion exception through the extension point of §8.7. |
| 17 | Consumer | Any output-bounding wrapper MUST be added to the supported wrapper list (§7.3) with tests, or the wrapped git command is denied. |
| 15, 19, 09 | Consumers | Orchestrator helpers, repairs, escalation and regression runs gain no bypass. |
| 07 | Not related | The hook writes no task state. |

## 3. Resolved decisions

| ID | Decision | Source |
|---|---|---|
| D1 | Bash entrypoint with a cheap prefilter, delegating to a Python 3.11+ standard-library core. | Owner, 2026-11-03 |
| D2 | No in-band bypass (environment variable, marker file, keyword). Owner-authorizable operations use the harness **ask** decision: the owner sees the explanation and approves or rejects one command. Where ask cannot reach a human, the hook denies and the agent asks the owner in chat. | Owner, 2026-11-03 |
| D3 | `.ai/` staging policy is the repository's own ignore rules (`git check-ignore`), evaluated per call, with no cache. Force-adding an ignored path is owner-authorizable. This replaces ADR-0009 Decision 5's "`git ls-files .ai` cached per session"; the new ADR records the change. | Owner, 2026-11-03 |
| D4 | `git add` accepts only literal file paths. Directories, globs, pathspec magic and update-all flags are denied. | Owner, 2026-11-03 |
| D5 | Any `Co-Authored-By:` trailer line is forbidden, whoever it names. A body sentence that mentions the phrase is not a trailer and is allowed. | Revision default (ADR-0009 lists the token) |
| D6 | Task and ADR identifiers are matched with word boundaries and digits (`T-01b`, `ADR-0007`), so `GPT-4` and `T-shirt` pass. | Revision default |
| D7 | The harness-native "allow" decision is never emitted; allowed commands still go through the user's normal permission rules. | Revision default |
| D8 | The `permissions.deny` fragment contains only deny-class patterns. A deny rule would override the owner's ask approval. | Revision default |
| D9 | Unlisted git subcommands are `not_applicable`: the matrix is a closed list, not a default-deny allowlist. | Revision default |
| D10 | Numeric limits are fixed in §7.5 and pinned by tests. | Revision default |

## 4. Terms

| Term | Definition |
|---|---|
| Registered project | A directory equal to or below a root listed in the project registry. When roots are nested, the most specific root wins (same rule as `project_for` in `hooks/log-step-hook.sh`). |
| Invocation | One simple command in the parsed command whose resolved program is `git` or `gh`. |
| Effective directory | The directory an invocation acts on, after literal `cd`/`pushd` steps and every `git -C <path>`. |
| Effective repository | The repository found by `git rev-parse --path-format=absolute --show-toplevel --git-common-dir` run in the effective directory. |
| Governed operation | An invocation matched by a row of the rule matrix (§8.1). |
| Protected ref | A branch ref defined as protected by §8.2. |
| Opaque form | A construct the parser does not support (§7.3). It never counts as safe. |
| Restack journal | The recovery journal written by `/restack` (§8.5). |
| Decision | One of `not_applicable`, `allow`, `deny`, `ask` (§6.1). |

## 5. Invariants

- **I1. Before effects.** The decision is made before the command changes files, the
  index, refs or any remote.
- **I2. Fail closed.** If an invocation in a registered project cannot be verified, the
  result is `deny`, never `allow`.
- **I3. Whole command.** A command is decided as a whole. The most severe result among its
  invocations wins (`deny` > `ask` > `allow` > `not_applicable`). One allowed part never
  allows a denied part.
- **I4. No writes.** The hook writes nothing: no files, no cache, no logs, no git state.
  Its git reads run with `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`,
  `-c core.fsmonitor=false`, with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and
  `GIT_COMMON_DIR` removed from the environment. It never runs network commands
  (`fetch`, `ls-remote`, `gh`).
- **I5. Deterministic.** The same input against the same repository state yields
  byte-identical output.
- **I6. No rewriting.** The hook never edits, corrects or runs the command itself.
- **I7. Model-independent.** The model, role, sub-agent and output-capture method do not
  change any decision.
- **I8. No atomicity claim.** The check and the later command are not atomic. Only an
  explicit `--force-with-lease=<ref>:<sha>` gives compare-and-swap on a remote ref. No other
  form is described as race-free.
- **I9. Diagnostics only on harness channels.** Incidents go to the harness reason channel
  and stderr only (ADR-0009 Decision 5).

## 6. Decision model

### 6.1 Decisions

| Decision | Meaning | Agent's next step |
|---|---|---|
| `not_applicable` | No invocation is in a registered project, or none is governed. Not a safety claim. | Proceed normally. |
| `allow` | All governed invocations were verified as permitted. | Proceed normally. |
| `deny` | A fixable violation, or the command cannot be verified. | Fix the command as the diagnostic says. Do not retry it unchanged, and never wrap or obfuscate it to get past the check. |
| `ask` | The operation needs the owner's authorization. | See §6.3. |

### 6.2 Harness mapping (Claude Code)

The adapter maps the core's decision to the harness protocol. The facts below come from
the Claude Code hooks documentation. Before coding, the implementer MUST confirm them for
the pinned Claude Code version and record the version, source URL and date in
`harness/claude/capabilities.md`. If a fact differs, change only the adapter and the
capability record; the core and the rule matrix stay the same.

| Decision | Adapter output |
|---|---|
| `not_applicable`, `allow` | Exit 0 with empty stdout. MUST NOT emit `permissionDecision: "allow"` (D7). |
| `deny` | Exit 2 with the diagnostic (§9) on stderr. |
| `ask` | Exit 0 with stdout `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"<diagnostic>"}}`, and the same diagnostic on stderr. |
| `ask`, owner approval unavailable | Converted to `deny` with reason `owner-approval-unavailable` (§6.3). |

### 6.3 Owner approval protocol

1. The adapter emits `ask` only when the event's permission mode is on an allowlist in `harness/claude/capabilities.md`. A mode is
   listed only if the documentation shows that, in that mode, the harness shows an ask
   decision to a human and never approves it automatically. For a missing, unknown or
   unlisted mode (for example `bypassPermissions` or non-interactive runs), the adapter
   returns `deny` with reason `owner-approval-unavailable`.
2. **Before** issuing an operation that the matrix marks `ask`, the agent MUST explain in
   chat: the exact command, which rail it crosses, why it is needed, what can be lost, and
   how to undo it.
3. Approval covers that one execution only. A rejection is final for that operation: the
   agent stops and reports. It does not retry or rephrase the command.
4. On `owner-approval-unavailable`, the agent stops. It gives the owner the explanation and
   the exact command. The owner either runs the command outside the agent (in a terminal, or
   with `! <command>` in Claude Code) or gives other instructions.
5. This protocol is added to `rules/git-flow.md` (§10.4).

## 7. Processing pipeline

### 7.1 Order of steps

1. **Entrypoint fast path** (`hooks/git-rails.sh`, Bash only, no jq/Python):
   a. Read stdin up to 1 MiB. If the input is larger, apply step 1c and deny with
      `malformed-input` if it matches. The entrypoint cannot read `cwd` without parsing,
      so this case and step 1d are the only ones that can affect an unregistered
      directory, and only while a registry exists.
   b. If the registry file does not exist, exit 0.
   c. If the raw input does not match the relevance pattern
      `(^|[^A-Za-z0-9_.-])(git|gh)([^A-Za-z0-9_.-]|$)`, exit 0.
   d. If `python3` is missing or older than 3.11, deny with `runtime-unavailable`.
      Otherwise `exec python3 -I <dir>/git_rails.py` with the same stdin. Isolated mode
      does not put the script directory on `sys.path`, so the core is one file or adds
      its own directory explicitly.
2. **Input validation.** The input MUST be one JSON object with `hook_event_name ==
   "PreToolUse"`, `tool_name == "Bash"`, `tool_input.command` as a string, and `cwd` as an
   absolute path. Anything else is `deny malformed-input`. A non-Bash tool is
   `not_applicable`.
3. **Registry read.** Read the registry as one snapshot. If it is unreadable or malformed,
   deny with `registry-error`.
4. **Parse** the command with the supported grammar (§7.3). If parsing fails and `cwd` is
   in a registered project, deny with `unsupported-form`. If parsing fails and `cwd` is not
   in a registered project, the result is `not_applicable` (residual risk X7).
5. **Resolve** each invocation's program, effective directory and effective repository
   (§7.4). Invocations outside registered projects are dropped. If none remain, the result
   is `not_applicable`.
6. **Classify** each remaining invocation against the matrix (§8.1) and evaluate its rule.
7. **Combine** the results per I3 and emit through the adapter (§6.2) with the diagnostic.

### 7.2 Core input and output (internal)

The core works on this logical record. It is not a wire format.

| Field | Content |
|---|---|
| `contract_version` | `1` |
| `tool_name`, `command` | From the event, unmodified. |
| `cwd` | Canonical `realpath` of the event `cwd`. |
| `permission_mode` | From the event if present, else `null`. |
| `registry_snapshot` | List of canonical roots. |

Output: `decision`, `reason_code`, `rule_id`, `summary` (safe operation description),
`next_step`, `checker_version`. `not_applicable` and `allow` carry no reason.

### 7.3 Supported shell grammar

Words are built from unquoted text, single quotes, double quotes without expansion, and
backslash escapes. A word containing `$…`, `${…}`, backticks, `$(…)`, `$'…'`, an unquoted
glob character (`*`, `?`, `[`) or a leading unquoted `~` is **dynamic**.

| Construct | Handling |
|---|---|
| `;`, `&&`, `||`, `&`, `|`, newline | Supported. Every pipeline element is analyzed. |
| Literal `cd <dir>`, `pushd <dir>`, `popd` | Update the effective directory for later commands in the same list. `cd` with a dynamic or missing argument makes later invocations opaque. |
| `( … )`, `{ …; }` | Parsed recursively. A `cd` inside does not leak out of `( … )`. |
| `bash -c '<literal>'`, `sh -c '<literal>'` | The literal is parsed recursively. A dynamic argument is opaque. |
| `$( … )`, backticks | Contents are parsed recursively as a command. The result is a dynamic word. |
| `git commit -m "$(cat <<'D' … D)"` (quoted or unquoted delimiter) | The only dynamic word accepted inside a governed invocation. The heredoc body is the message text. An unquoted-delimiter body MUST NOT contain `$`, backticks or `\`. |
| `<<'D'`, `<<"D"`, `<<D` heredocs; `<<<'literal'` | Literal stdin for `-F -`. Same rule for unquoted delimiters. |
| Redirections `>`, `>>`, `<`, `2>&1`, `n>file` | Ignored for decisions. |
| Leading `NAME=literal` assignments | Allowed, except `GIT_*` names on a governed invocation: deny with `opaque-environment`. |
| Wrappers `command`, `exec`, `env` (assignments only), `time`, `nohup`, `timeout <duration>` | Removed; the wrapped command is analyzed. |
| `eval`, `source`, `.`, `sudo`, `xargs`, `find … -exec`, `parallel`, `watch`, process substitution, `if`/`for`/`while`/`case`, functions, unknown wrappers | Opaque. |
| Program word `git` or `gh`, or an absolute path whose basename is `git` or `gh` | An invocation. A relative path (`./git`) or a dynamic program word is opaque. |

Opaque constructs matter only in registered projects. A command is `unsupported-form` if
an opaque construct sits in a command position, inside a git/gh/wrapper/`cd` argument, or
before an invocation it could affect. A dynamic word in an argument of any other program
(for example `echo "$HOME"`) is fine. A dynamic word in a non-governed git invocation
(`git log "$REF"`) is fine. A dynamic word in a governed invocation is
`unsupported-form`, except for the commit-message form above.

### 7.4 Program, options and target resolution

1. **Git global options** before the subcommand: `-C <path>` is repeatable and resolved
   relative to the previous directory. `--no-pager`, `-P`, `-p`, `--no-optional-locks` and
   `--literal-pathspecs` are accepted. Any other global option (`-c`, `--git-dir`,
   `--work-tree`, `--namespace`, `--exec-path`, `--bare`, …) on a governed subcommand is
   `unsupported-form`.
2. **Aliases.** If the subcommand is not a git builtin and
   `git config --get alias.<name>` exists in the effective repository, the result is
   `unsupported-form`. Git does not let aliases shadow builtins.
3. **Option parsing** follows git's parse-options semantics for governed subcommands:
   bundled short flags (`-Av`, `-am<msg>`), `--opt=value` and `--opt value`, unique
   long-option prefixes (`--forc` is `--force`), `--no-<opt>` negation, the last occurrence
   wins for single-valued options (repeatable `-m` and `--trailer` accumulate), and `--`
   ends options.
4. **Effective repository.** If the effective directory is in a registered project but is
   not inside a git work tree, the invocation is `not_applicable` (git itself will fail).
5. **`gh`.** Only `gh pr merge` and `gh api` are governed (§8.1).

### 7.5 Limits

| Limit | Value | When exceeded |
|---|---|---|
| Hook stdin | 1 MiB | `deny malformed-input` |
| `tool_input.command` | 64 KiB | `deny limit-exceeded` |
| Recursion depth (`-c`, `$( )`, groups) | 3 | `deny limit-exceeded` |
| Tokens per command | 4096 | `deny limit-exceeded` |
| One git read subprocess | 2 s | `deny limit-exceeded` |
| Core wall-clock budget | 5 s | `deny limit-exceeded` |
| Harness timeout in `hooks.json` | 10 s | Harness behavior; see residual risk X6 |
| Commit message file (`-F`) | 1 MiB | `deny commit-message-unverifiable` |

Limits apply only after the relevance prefilter matches and the command is in a registered
project. Python exceptions are caught and reported as `deny internal-error`.

## 8. Rules

### 8.1 Rule matrix

The last column is the result when the condition holds. Each row also covers its
equivalent spellings (§7.4). Rows are checked in order and every matching row applies (I3).

| ID | Invocation | Condition | Result | Reason code |
|---|---|---|---|---|
| R01 | `git add`/`git stage` | `-A`, `--all`, `--no-ignore-removal`, `-u`, `--update`, or a path operand `.` | deny | `blanket-staging` |
| R02 | `git add`/`git stage` | A path operand that is a directory, contains glob characters, starts with `:` (pathspec magic), neither exists nor is tracked, or `--pathspec-from-file` is used | deny | `staging-not-file` |
| R03 | `git add`/`git stage` | `-p`, `-i`, `-e`, `--patch`, `--interactive`, `--edit` | deny | `unsupported-form` |
| R04 | `git add`/`git stage` | `-f`/`--force` with an operand that `git check-ignore` reports as ignored | ask | `staging-ignored-path` |
| R05 | `git add`/`git stage` | Otherwise: every operand is an existing file, a symlink, or a tracked path deleted from the work tree | allow | — |
| R06 | `git commit` | `-a`, `--all`, including bundles such as `-am` | deny | `commit-all` |
| R07 | `git commit` | Path operands, or `-i`/`-o` with paths: each operand checked as in R01–R02 | deny on failure | as R01/R02 |
| R08 | `git commit` | The message cannot be determined statically (§8.3) | deny | `commit-message-unverifiable` |
| R09 | `git commit` | The message matches a forbidden pattern (§8.3) | deny | `commit-message-forbidden` |
| R10 | `git commit --amend` | HEAD is reachable from any `refs/remotes/*` ref | ask | `rewrite-published` |
| R11 | `git push` | `--dry-run`/`-n` | allow (skip R12–R19) | — |
| R12 | `git push` | The target remote or any destination ref cannot be resolved (§8.4) | deny | `push-target-unknown` |
| R13 | `git push` | The protected set cannot be computed (§8.2) | deny | `default-branch-unknown` |
| R14 | `git push` | `--all`, `--branches`, `--mirror`, `--tags`, `--follow-tags`, `push.default=matching`, or any `refs/tags/*` destination | ask | `push-bulk-or-tags` |
| R15 | `git push` | `--delete`/`-d`, or a refspec with an empty source (`:dst`) | ask | `push-delete` |
| R16 | `git push` | Any destination is a protected ref | ask | `push-protected-target` |
| R17 | `git push` | `--force`/`-f`, a `+` refspec, or `--force-if-includes` without an explicit lease | ask | `push-force` |
| R18 | `git push` | `--force-with-lease`: allowed only if every leased ref has an explicit `=<ref>:<sha>` (or `<ref>:` for a ref recorded as absent) **and** the restack verification of §8.5 passes for every destination | allow, else ask | `push-lease-unverified` |
| R19 | `git push` | None of R12–R18 matched | allow | — |
| R20 | `git reset` | `--hard` | ask | `reset-hard` |
| R21 | `git clean` | Without `-n`/`--dry-run` (`-i` is `unsupported-form`) | ask | `clean` |
| R22 | `git branch` | `-d`, `-D`, `--delete` (local or `-r`) | ask (§8.7) | `branch-delete` |
| R23 | `git update-ref` | `-d` on `refs/heads/*`, or `--stdin` | ask | `branch-delete` / `unsupported-form` |
| R24 | `git branch -f`, `-m`, `-M`, `-c`, `-C`; `git checkout -B`; `git switch -C`/`--force-create`; `git update-ref refs/heads/<x>` | The source or destination is a protected ref | ask | `protected-ref-rewrite` |
| R25 | `git rebase` | `--abort` or `--show-current-patch` | allow (skip R26) | — |
| R26 | `git rebase` | A replay matching §8.5, or `--continue`/`--skip` while a rebase of a journal branch is in progress (branch read from `rebase-merge/head-name` or `rebase-apply/head-name`) | allow, else ask | `rebase-outside-restack` |
| R27 | `git merge` | HEAD is a protected ref and the form is not `--abort` | ask | `merge-into-protected` |
| R28 | `git pull` | HEAD is a protected ref, unless the form is `--ff-only` with no repository or refspec operands | ask | `merge-into-protected` |
| R29 | `gh pr merge` | Always | ask | `pr-merge` |
| R30 | `gh api` | The endpoint matches `/pulls/[0-9]+/merge` or `/merges` (ask), or the endpoint is dynamic (deny) | ask / deny | `pr-merge` / `unsupported-form` |
| R31 | Any governed invocation | `GIT_*` assignment, an unsupported global option, an alias, or a dynamic argument | deny | `opaque-environment` / `unsupported-form` |

The matrix grants no new rights and does not narrow any textual rule. Read-only
subcommands (`status`, `diff`, `show`, `log`, `ls-files`, `rev-parse`, `branch --list`, …)
and every unlisted subcommand are `not_applicable` (D9). An ordinary push to an
unprotected branch is `allow`. The `--allow-pr` requirement still applies as a textual rule.

### 8.2 Protected refs

For the effective repository and the target remote `<r>`, protected branch names are:

1. The target of the symbolic ref `refs/remotes/<r>/HEAD`. If it is missing, R13 applies,
   with next step `git remote set-head <r> --auto`.
2. `main`, `master` and `release/*`, always.
3. Every pattern from `git config --get-all orchestrail.protectedBranch` (fnmatch on the
   short branch name).

A destination ref `refs/heads/<name>` is protected if `<name>` matches any entry. Local
protection for R24, R27 and R28 uses the same set with `<r>` = `origin`. If `origin` is
missing, only entries 2 and 3 are used.

### 8.3 Commit message checks

**Sources the hook can read statically** (any other source is R08):

| Source | Text checked |
|---|---|
| `-m <v>`, `-m<v>`, `--message <v>`, `--message=<v>` (repeatable) | Values joined with a blank line, as git does. |
| `-F <path>`, `--file=<path>` with a literal path | File contents. Relative paths resolve against the effective directory. |
| `-F -` | The literal heredoc or here-string attached to that command. |
| `-m "$(cat <<'D' … D)"` | The heredoc body (§7.3). |
| `--trailer <v>`, `--trailer=<v>` | Appended to the checked text. |
| `--amend --no-edit` with no other message source | `git log -1 --format=%B HEAD` plus trailers. |

These sources are R08: no message source (editor), `-e`/`--edit`, `-c`/`-C`,
`--reuse-message`, `--reedit-message`, `--fixup`, `--squash`, `-t`/`--template`, an
unreadable or too-large `-F` file, and any other dynamic text.

**Forbidden patterns** (Python `re` syntax, applied to the full checked text):

| ID | Pattern | Blocks | Does not block |
|---|---|---|---|
| P1 | `(?im)^[ \t]*co-authored-by[ \t]*:` | `Co-Authored-By: Name <mail>`, `co-authored-by:x` | "Remove Co-Authored-By handling" in the body |
| P2 | `(?<![A-Za-z0-9_-])T-[0-9]+[A-Za-z]*(?![A-Za-z0-9_])` | `T-01`, `T-04b`, `T-09-fix-x` | `GPT-4`, `T-shirt`, `IoT-1` |
| P3 | `(?<![A-Za-z0-9_-])ADR-[0-9]+` | `ADR-0007`, `see ADR-12` | `HADR-1`, `ADR-` without digits |

All other no-attribution and no-pipeline-identifier rules in `rules/git-flow.md` remain
textual.

### 8.4 Push target resolution

1. **Remote.** Use the first literal non-option operand if it names a configured remote
   (`remote.<name>.url` exists). A URL or unknown name is R12. Without operands, use, in
   order: `branch.<current>.pushRemote`, `remote.pushDefault`, `branch.<current>.remote`,
   `origin`. If `remote.<r>.push` is configured, the result is R12.
2. **Refspecs.** For each refspec, parse an optional `+`, then `<src>[:<dst>]`.
   - `<src>` alone means `<dst> = <src>`. `HEAD` means the current branch; a detached HEAD
     is R12.
   - A `<dst>` without a `refs/` prefix becomes `refs/heads/<dst>`, unless `<src>` resolves
     only to `refs/tags/*`. In that case the destination is `refs/tags/<dst>` (R14).
   - An empty `<src>` is a deletion (R15).
3. **No refspec.** Use `push.default` (unset means `simple`). `simple` and `current` push
   to `refs/heads/<current>`. `upstream` pushes to `branch.<current>.merge`. `matching` is
   R14. `nothing` is R12. A detached HEAD is R12.
4. Every destination is checked. One permitted destination never allows another (I3).

### 8.5 Restack exception

`/restack` MUST write its recovery journal at
`<git-common-dir>/orchestrail-restack/<sha256-of-canonical-task-path>.json`, using
this minimum schema. Extra fields are allowed. SHAs are 40- or 64-character lowercase hex.

```json
{
  "schema_version": 1,
  "repository_common_dir": "/abs/canonical/.git",
  "task_path": "/abs/canonical/task/dir",
  "target": {"branch": "main", "sha": "<sha>"},
  "publication_authorized": false,
  "order": ["feat/a", "feat/b"],
  "branches": {
    "feat/a": {
      "original_base_commit": "<sha>",
      "original_tip": "<sha>",
      "replayed_tip": null,
      "expected_remote_tip": null
    }
  }
}
```

`expected_remote_tip` is a SHA, the string `"absent"` (the branch was confirmed absent on
the remote), or `null` (not captured). `publication_authorized` is `true` only when
`/restack` runs with `--allow-pr`.

**Rebase verification (R26).** The command MUST be exactly
`git rebase --onto <new-sha> <old-sha> <branch>`, with full SHAs and a literal branch
name. Exactly one journal in the effective repository's common directory MUST satisfy all
of the following:

- `repository_common_dir` equals the canonical effective common directory;
- `<branch>` is in `order`, is not protected, and has `replayed_tip == null`;
- `<old-sha>` equals that branch's `original_base_commit`;
- the current tip of `refs/heads/<branch>` equals `original_tip`;
- `<new-sha>` equals `target.sha` if `<branch>` is the first entry of `order` whose
  `replayed_tip` is `null`, or else the previous branch's `replayed_tip`.

**Push verification (R18).** Each destination `refs/heads/<b>` MUST satisfy all of the
following:

- `<b>` is in `order` and is not protected;
- `publication_authorized` is `true`;
- the local tip of `<b>` equals `replayed_tip`;
- the explicit lease SHA equals `expected_remote_tip`, or the lease is empty and
  `expected_remote_tip` is `"absent"`;
- no `+` refspec and no `--force` is present.

The hook does not check whether the journal is fresh. Any failed or ambiguous
verification (zero or several matching journals, or invalid JSON or schema) gives `ask`
with reason `push-lease-unverified` or `rebase-outside-restack`, plus a diagnostic naming
the failed check. An environment variable, marker file or the word `restack` in the command
is never evidence (D2).

### 8.6 `.ai/` staging policy

R01–R05 apply to `.ai/` like any other path. On top of them, the repository's ignore rules
decide: a tracked path or an unignored untracked path can be staged, and an ignored path
needs `-f`, which is R04 (ask). Consumer projects ignore `.ai/` by default, so their state
stays local unless the owner approves. This repository does not ignore `.ai/` (ADR-0012),
so its knowledge files can be staged. The hook does not inspect staged contents and keeps
no cache (D3).

### 8.7 Branch deletion and the spec 12 extension point

Until spec 12 is implemented, every branch deletion (R22, R23) is `ask`. The core MUST
dispatch R22/R23 through a named exception-verifier interface. For 06 the interface has
one implementation that always returns "no exception". Spec 12 adds a verifier that turns a
proven temporary child-branch deletion into `allow`, preferably through
`git update-ref -d refs/heads/<b> <expected-sha>` (compare-and-swap). 06 MUST NOT
implement that verifier.

## 9. Diagnostics

Each `deny` or `ask` produces one UTF-8 diagnostic of at most 1 KiB:

```
git-rails: <deny|ask> <reason_code> (<rule_id>)
rule: rules/git-flow.md → ## Safety rails
operation: <safe summary, e.g. "git push to refs/heads/main on origin">
next: <one concrete action>
```

- The summary names the subcommand, normalized refs, remote name and path count. It MUST
  NOT include commit-message text, file contents, environment values, the full command or
  URL user info.
- The `next` text for every reason code is defined in one table in the core and is pinned
  by tests.
- Reason codes: `blanket-staging`, `staging-not-file`, `staging-ignored-path`,
  `commit-all`, `commit-message-unverifiable`, `commit-message-forbidden`,
  `rewrite-published`, `push-target-unknown`, `default-branch-unknown`, `push-bulk-or-tags`,
  `push-delete`, `push-protected-target`, `push-force`, `push-lease-unverified`,
  `reset-hard`, `clean`, `branch-delete`, `protected-ref-rewrite`,
  `rebase-outside-restack`, `merge-into-protected`, `pr-merge`, `opaque-environment`,
  `unsupported-form`, `malformed-input`, `registry-error`, `runtime-unavailable`,
  `limit-exceeded`, `internal-error`, `owner-approval-unavailable`. Adding a code requires
  a test.

## 10. Installation and contract updates

### 10.1 Manifest

`harness/claude/hooks.json` gains:

```json
"PreToolUse": [{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash",
    "args": ["@ORCHESTRAIL_HOME@/hooks/git-rails.sh"],
    "timeout": 10
  }]
}]
```

The handler MUST NOT declare a fail-open failure option. If the pinned harness offers a
blocking failure mode, the handler uses it. Otherwise, fail-open on crash or timeout is
recorded as residual risk X6.

### 10.2 Installer

- `scripts/install-hooks.py` stops hard-coding the logging handler. It validates every
  manifest group against the handler that the manifest declares for that event.
- Receipt `schema_version` 2 adds `owned_permissions` (deny strings the installer added).
  Version 1 receipts stay readable and are migrated on the next install.
- The existing guarantees hold for the new entries: idempotent install, preserved foreign
  hooks and settings, exact multiset ownership, serialized locking, atomic replacement,
  recovery of interrupted replacements, and no overwrite of concurrent user edits.
- Removal deletes only owned handlers and owned deny strings.
- `scripts/sync.sh` keeps calling the installer as today. Installation failure does not
  block other deployment targets.

### 10.3 `permissions.deny` fragment

`harness/claude/permissions.json` has the shape `{"permissions":{"deny":[…]}}`. It holds
only patterns for deny-class rows R01 and R06 (D8), for example `Bash(git add -A)`,
`Bash(git add --all)`, `Bash(git add .)`, `Bash(git commit -a)`, `Bash(git commit --all)`.
For each pattern, the exact syntax and its match semantics (exact versus prefix) are
confirmed for the pinned harness and recorded in `harness/claude/capabilities.md`. A
pattern MUST NOT match a legitimate command such as `git add .gitignore`. The fragment is
defense in depth; the hook stays authoritative.

### 10.4 Contract and documentation updates

| File | Change |
|---|---|
| `rules/git-flow.md → ## Safety rails` | Add an `Enforcement` column to every row: `hook: deny`, `hook: ask`, `hook: allow with restack journal`, or `text only`. Replace "Branch deletion: Forbidden" with "owner approval required; spec 12 child exception pending". Add the owner-approval protocol of §6.3 and the agent rule "never wrap or rephrase a denied command to evade the check". |
| `workflows/restack.md` | Document the journal schema of §8.5, including `publication_authorized`, `"absent"` and the exact rebase/push command forms. |
| `harness/claude/capabilities.md` | Add a `git-rails` section: event, tool, pinned version, exit/JSON protocol, ask-capable permission modes, deny-pattern semantics, failure-mode behavior, source URL and date. |
| `harness/codex/capabilities.md` | Add `git-rails: none (textual rules only)`. |
| `scripts/validate-contracts.sh` | Add a `--git-rails-only` mode running `tests/git-rails.sh`. The default run includes it. |
| `.ai/adr/` | New ADR: hook design, D1–D10, and the amendment of ADR-0009 Decision 5 (D3). Index it. |
| `.ai/memory/architecture.md` | Add the new hook, the permissions fragment and the test suite. |

## 11. Error handling

| Situation | Result |
|---|---|
| Registry file absent | Exit 0 (entrypoint fast path). |
| Registry unreadable or malformed, relevant command | `deny registry-error`; next step: repair with `scripts/setup-new-project.sh`. |
| Malformed event or oversized input, relevant command | `deny malformed-input`. |
| Python missing or too old, relevant command | `deny runtime-unavailable`, in any directory while a registry exists (§7.1 step 1d). Irrelevant commands still exit 0. Installation already requires Python 3.11+. |
| Uncaught exception or git read failure | `deny internal-error` or `deny limit-exceeded`. |
| Effective directory not a git work tree | `not_applicable`. |
| Remote HEAD unknown | `deny default-branch-unknown`. |
| Restack journal missing, stale or ambiguous | `ask` with the failed check named. |
| Concurrent settings edit during install | The installer keeps the user's version, reports a conflict and exits non-zero. Nothing is partially written. |
| Output capture truncates the diagnostic | The decision is unchanged. Spec 17 MUST keep the reason line and the exit status. |
| A retry after `deny` | Evaluated from scratch. A previous decision is never reused. |

## 12. Acceptance criteria

All checks run offline in disposable repositories with isolated `HOME`,
`XDG_CONFIG_HOME` and remotes (local bare repositories). They make no network calls and run
no models. `tests/git-rails.sh` is table-driven: each case lists its setup, `cwd`, command,
permission mode, expected decision and expected reason code. Every case also asserts that
the hook leaves `.git/` (refs, index, config), the work tree and `.ai/` byte-identical.

- [ ] **AC-01 Registry gate.** An unregistered `cwd` with no registered target gives exit
  0 with empty stdout. `git -C <registered> push -f` from an unregistered `cwd` gives `ask
  push-force`. With nested registered roots, the innermost root wins. A missing registry
  file gives exit 0 even when `python3` is absent from `PATH`.
- [ ] **AC-02 Fast path.** A command with no `git`/`gh` word exits 0 without starting
  Python (proved with a `PATH` that has no `python3`). `git-rails.sh`, `.git/config` and
  `github.com` do not trigger the prefilter.
- [ ] **AC-03 Grammar.** These are analyzed and get the stated decision: `cd sub && git
  add -A` gives deny; `(cd sub; git add a.txt)` gives allow; `bash -c 'git add .'` gives
  deny; `command git add --all` gives deny; `env X=1 git commit -am x` gives deny;
  `timeout 30 git push -f` gives ask; `git status | head` gives not_applicable. These give
  `deny unsupported-form`: `eval "git push"`, `sh -c "$C"`, `$G push`, `xargs git add`, `for
  f in a; do git add "$f"; done`, `sudo git push`, `./git push`, `git -c x=y push`, and a
  defined alias `git p`. `GIT_DIR=x git commit -m ok` gives `deny opaque-environment`.
  Each limit of §7.5 gives `limit-exceeded`.
- [ ] **AC-04 Staging (R01–R07).** For every row there is a violating case, an allowed
  neighbor and an alternative spelling, including `-Av`, `--al` (prefix), `-u`, `.`,
  `src/`, `'*.py'`, `:/`, `--pathspec-from-file`, `-p`, the forced ignored path
  `.ai/state.md` (ask), the unignored new `.ai/adr/x.md` (allow), and a deleted tracked
  file (allow).
- [ ] **AC-05 Commit messages (R08–R10).** These are denied as `commit-message-forbidden`:
  a `Co-authored-by:` trailer via `-m`, via `$(cat <<'EOF' … EOF)`, via `-F file`, via `-F
  -` with a heredoc, and via `--trailer`; `T-04b` in the subject; `ADR-0007` in the body;
  and `--amend --no-edit` when HEAD's message has a trailer. These are allowed: `fix GPT-4
  parsing`, `Bump T-shirt sizes`, and a body sentence mentioning Co-Authored-By. A bare
  `git commit`, `-c HEAD`, `--fixup` and an unquoted heredoc containing `$X` give
  `commit-message-unverifiable`. `--amend` on a commit contained in `refs/remotes/*` gives
  `ask rewrite-published`; on an unpushed commit it gives allow.
- [ ] **AC-06 Push (R11–R19).** These give `ask push-protected-target`: `origin main`,
  `origin feat/x:main`, `origin HEAD:refs/heads/release/1.2`, `origin HEAD` on `main`, a
  bare `git push` on `main` with `push.default=simple`, and a configured extra protected
  pattern. These give allow: a bare push on `feat/x` and `origin feat/x`. A push of `feat/x
  feat/y:main` gives ask. Force forms give `ask push-force`: `-f`, `--forc`, `+feat/x` and
  `--force-if-includes`. `--force-with-lease` without a journal gives `ask
  push-lease-unverified`. `--delete x` and `:x` give `ask push-delete`. `--tags`,
  `--mirror`, `--all`, a tag destination and `push.default=matching` give `ask
  push-bulk-or-tags`. A URL remote, a detached HEAD and `remote.origin.push` give `deny
  push-target-unknown`. A missing `refs/remotes/origin/HEAD` gives `deny
  default-branch-unknown`. `--dry-run` gives allow.
- [ ] **AC-07 Restack (R18, R26).** A valid journal allows the exact rebase command and
  the exact lease push. Each of these gives ask and names the failed check: wrong
  repository, branch not in `order`, moved local tip, wrong `<old-sha>`/`<new-sha>`, a
  lease SHA different from `expected_remote_tip`, `publication_authorized: false`,
  `--force` together with a valid journal, a protected destination, invalid JSON, and two
  matching journals. A `RESTACK=1` variable and a marker file have no effect.
  `--abort` gives allow.
- [ ] **AC-08 Other operations (R20–R30).** These give ask: `reset --hard`, `clean -fd`,
  `branch -d`/`-D`, `update-ref -d refs/heads/x`, `branch -f main`, `checkout -B main`,
  `merge` on `main`, `pull` on `main` without `--ff-only`, `gh pr merge 1`, and `gh api
  -X PUT repos/o/r/pulls/1/merge`. These give allow or not_applicable: `reset --soft`,
  `clean -n`, `merge` on `feat/x`, `pull --ff-only` on `main`, `gh pr create`, and every
  read-only subcommand.
- [ ] **AC-09 Harness protocol.** Fixtures encode the confirmed protocol from §6.2. deny
  gives exit 2 with the diagnostic on stderr. ask gives exit 0 with the JSON shape. allow
  and not_applicable give exit 0 with empty stdout, and no case ever prints `"allow"`. An
  ask-class case gives `deny owner-approval-unavailable` when the permission mode is
  missing, unknown or `bypassPermissions`.
- [ ] **AC-10 Diagnostics.** Every deny/ask has the four-line format, is at most 1 KiB,
  and has a `next` line from the table. A secret placed in a message, a file, an
  environment value and URL user info never appears in stdout or stderr.
- [ ] **AC-11 Failure modes.** In a registered `cwd`, each of these gives the §11 result:
  malformed JSON, an unreadable registry, missing Python, an injected core exception and a
  git read timeout.
- [ ] **AC-12 Determinism and independence.** Running each case twice gives
  byte-identical output. Adding or removing `.ai/tasks/**` and changing any
  `atomic-tests:` value does not change any decision.
- [ ] **AC-13 Installation.** Installing twice equals installing once. Foreign hooks and
  deny strings are preserved. A version 1 receipt migrates. Removal deletes only owned
  entries. Malformed settings and a concurrent edit cause no partial write. The existing
  `tests/hook-install.sh` and logging suites still pass.
- [ ] **AC-14 Deny fragment.** The fragment contains only R01/R06 patterns. Each pattern
  has a positive and a negative fixture under the recorded match semantics, and none
  matches `git add .gitignore`.
- [ ] **AC-15 Contracts and suite.** Every §10.4 update exists. `bash
  scripts/validate-contracts.sh --git-rails-only` and the full `bash
  scripts/validate-contracts.sh` pass with zero failures.

## 13. Residual risks (documented non-guarantees)

These MUST appear in `harness/claude/capabilities.md` and in the ADR.

| ID | Risk |
|---|---|
| X1 | Git commands run by scripts or programs the Bash tool starts (`bash scripts/x.sh`, `make`, Python) are not seen. |
| X2 | A shell alias or function named `git` in the user's shell environment is not seen. |
| X3 | Unlisted destructive operations are not enforced: `checkout -- .`, `restore`, `stash drop`/`clear`, `worktree remove --force`, `filter-branch`, `replace`, local `tag`, `git-receive-pack`, and messages of `merge`/`cherry-pick`/`revert`. |
| X4 | Edits to `.git/` through non-Bash tools are not seen. |
| X5 | Between the decision and execution, refs can move. Only an explicit lease is compare-and-swap. |
| X6 | If the harness proceeds when the hook crashes or times out, that failure is fail-open. |
| X7 | An opaque command started outside registered projects that targets a registered project is not caught. |
| X8 | The agent can forge the registry, the journal or git config. This is outside the threat model (§1.2). |
| X9 | Codex and other harnesses have textual rules only. |
| X10 | `--allow-pr`, PR text and the wider attribution rules remain textual. |

## 14. Implementation order (test-first)

1. **Read the current sources:** `rules/git-flow.md`, `workflows/restack.md`,
   `harness/claude/*`, `scripts/install-hooks.py`, `hooks/log-step-hook.sh → project_for`,
   `tests/hook-install.sh`. Record the revision you read and any difference from this spec.
   **Stop and ask** if a difference changes a rule.
2. **Confirm the harness facts** of §6.2, §6.3, §10.1 and §10.3 from the official Claude
   Code documentation for the pinned version. Record them in
   `harness/claude/capabilities.md`. **Stop and ask** if ask decisions cannot reach a human
   in any interactive mode.
3. **Write failing tests** for AC-01…AC-14 and watch them fail for the right reason.
4. **Implement the core** (parser, resolver, rules, diagnostics) as pure functions plus a
   thin git-read layer.
5. **Implement the entrypoint and adapter,** then the installer extension and the
   permissions fragment.
6. **Update the contracts and docs** (§10.4), the restack journal writer, the ADR and the
   architecture memory.
7. **Run the full suite** (AC-15). Report changed paths, checks run, the residual-risk
   table and the installation status. Finishing development does not install anything on
   any machine.

Suggested decomposition for `/pd-decompose` (not binding): (a) harness facts and
capability record; (b) shell parser and resolver; (c) staging and commit rules; (d) push
resolution and protected refs; (e) restack journal schema and verification; (f) adapter,
entrypoint and limits; (g) installer and deny fragment; (h) contracts, ADR and validator
mode.
