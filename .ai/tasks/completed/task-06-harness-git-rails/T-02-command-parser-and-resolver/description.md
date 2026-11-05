## Goal
`hooks/git_rails.py` exposes a pure decision frame that validates the event, reads the project registry, parses the Bash command under the spec §7.3 grammar and resolves every git/gh invocation's program, effective directory and effective repository, yielding `not_applicable`, `unsupported-form`, `opaque-environment`, `registry-error`, `malformed-input` or `limit-exceeded` per spec §7.1 steps 2–5, §7.3, §7.4 and the parser limits of §7.5, combined per I3.

## Context
- Dependencies: none (first code leaf)
- Constraints: Python 3.11+ standard library only, one file, typed with mandatory annotations, runnable under `python3 -I` (spec D1, §7.1 1d). Pure functions plus a thin git-read layer that sets `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `-c core.fsmonitor=false`, removes `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`/`GIT_COMMON_DIR`, and enforces the 2 s per-read timeout (I4). Registry path `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects`; matching mirrors `hooks/log-step-hook.sh → project_for` (`/` matches all, the longest matching root wins). Validity is strict (owner decision): the whole registry is `deny registry-error` when it is unreadable, not UTF-8, or has any line that is empty or contains CR/NUL, is relative, or is not already canonical (`os.path.realpath(line) != line`) — the same predicate as `scripts/setup-new-project.sh` registration.
- Constraints: the closed governed-subcommand list (D9) is data in the core: `add`, `stage`, `commit`, `push`, `reset`, `clean`, `branch`, `update-ref`, `checkout`, `switch`, `rebase`, `merge`, `pull`; `gh pr merge`, `gh api`. Rule evaluation is a dispatch table filled by later leaves; this leaf ships it with only R31 (GIT_* assignment, unsupported global option, alias, dynamic argument on a governed invocation). The diagnostic rule-path string lives in one module constant that tests read.
- Constraints: create `tests/git-rails.sh` (table-driven entry; may embed or delegate to a stdlib Python runner as `tests/hook-shell-quality.sh` embeds Python) and add `--git-rails-only` to `scripts/validate-contracts.sh` plus default-run inclusion, following the existing focused-mode block and default-run reporting pattern. Every case uses disposable repositories with isolated `HOME`/`XDG_CONFIG_HOME` and asserts `.git/`, the work tree and `.ai/` are byte-identical afterwards.
- Reason: the parser/resolver is the shared substrate of every rule; it has its own verifiable output (resolved invocation records and parser-level decisions).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** event validation (§7.1 step 2), registry snapshot read (step 3), grammar (§7.3: separators, literal `cd`/`pushd`/`popd`, subshell scoping, `bash -c`/`sh -c` literals, `$( )`/backticks, the commit-message heredoc form, heredocs and here-strings, redirections, leading assignments, wrappers `command`/`exec`/`env`/`time`/`nohup`/`timeout`, opaque constructs), program resolution (`git`/`gh`/absolute basename; relative or dynamic → opaque), git global options (`-C` chain, accepted flags, others unsupported), alias detection via `git config --get alias.<name>` for non-builtins, git parse-options semantics helper (bundles, `--opt=value`, unique long prefixes, `--no-`, last-wins, `--`) usable by rule leaves, effective repository via `rev-parse --path-format=absolute --show-toplevel --git-common-dir`, non-work-tree → `not_applicable`, recursion depth 3 and 4096-token limits, git read 2 s timeout, I3 combination.
- **Out of scope:** rules R01–R30, restack journal, entrypoint, adapter output, diagnostics rendering, stdin/command-size/wall-clock limits.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh, scripts/validate-contracts.sh

## Steps
1. Write `tests/git-rails.sh` with a case table and fixtures (disposable repos, isolated HOME/XDG, registry files, nested roots) and the byte-identity assertion; add `--git-rails-only` and default inclusion to `scripts/validate-contracts.sh`.
2. Add failing cases: registry gate (unregistered cwd, `git -C <registered>` from unregistered cwd resolves into the project, nested roots innermost wins, unreadable registry, non-UTF-8 registry and each invalid-line kind (empty, CR, NUL, relative, non-canonical/symlinked) → registry-error), malformed events, non-Bash tool → not_applicable.
3. Add failing grammar cases asserting resolved invocation records for the AC-03 commands, and `unsupported-form` for `eval "git push"`, `sh -c "$C"`, `$G push`, `xargs git add`, `for … done`, `sudo git push`, `./git push`, `git -c x=y push`, defined alias `git p`; `GIT_DIR=x git commit -m ok` → opaque-environment; recursion and token limits → limit-exceeded; a hanging git read → limit-exceeded. Run and observe RED.
4. Implement the tokenizer/word model with dynamic-word detection.
5. Implement the list/pipeline/group/`-c`/substitution parser with recursion accounting.
6. Implement effective-directory tracking, wrapper stripping and program resolution.
7. Implement the sanitized git-read layer with timeout, effective-repository resolution and alias detection.
8. Implement the registry snapshot and most-specific-root gate.
9. Implement governed classification, R31, the parse-options helper and I3 combination.
10. Run the focused and full suites; refactor while green.

## Acceptance Criteria
- Registry gate: unregistered cwd with no registered target → not_applicable; `git -C <registered> …` from an unregistered cwd is resolved into the registered project; nested roots → innermost root; missing registry file → not_applicable; an unreadable or non-UTF-8 registry, or one with any empty, CR/NUL, relative or non-canonical line, with a relevant command → `deny registry-error`; a registered root that no longer exists but is otherwise valid is not malformed.
- Grammar: each AC-03 command resolves to the expected invocation list (program, subcommand, argv, effective directory, repository); every listed opaque form → `deny unsupported-form`; `GIT_DIR=x git commit -m ok` → `deny opaque-environment`; recursion depth > 3 and > 4096 tokens → `deny limit-exceeded`; a git read exceeding 2 s → `deny limit-exceeded`; `git status | head` → not_applicable.
- `bash scripts/validate-contracts.sh --git-rails-only` runs the suite; the default validator includes it; every case leaves `.git/`, the work tree and `.ai/` byte-identical.

## Test Plan
- **Level:** unit (parser and resolver functions imported from `hooks/git_rails.py`), integration (real disposable git repositories and registry files for resolution, aliases and timeouts)
- **Scenarios:**
  - Registry gate cases → expected decision per AC 1.
  - Grammar and opaque cases → expected invocation records / reason codes per AC 2.
  - Suite wiring and byte identity → AC 3.
- **Edge cases:** empty command, whitespace-only, unterminated quotes, `cd` inside `( )` not leaking, `cd` with dynamic arg making later invocations opaque, `env` with options vs assignments, `timeout` with and without duration, absolute `/usr/bin/git`, non-work-tree directory, symlinked registry root (non-canonical → `registry-error`), registry with trailing newline vs none, nonexistent but canonical root.
