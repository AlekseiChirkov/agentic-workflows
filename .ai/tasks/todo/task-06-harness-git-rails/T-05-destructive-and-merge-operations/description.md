## Goal
The core decides reset, clean, branch deletion and protected-ref rewrites, rebase, merge, pull and PR-merge invocations per rules R20–R25 and R27–R30, routes branch deletion through the named exception-verifier interface of spec §8.7 (single implementation: "no exception"), and routes non-abort rebases (R26) to a replay-verification interface that, until the restack verifier exists, gives `ask rebase-outside-restack`.

## Context
- Dependencies: T-02, T-04 (shared local protected-ref function)
- Constraints: spec §8.1 R20–R30, §8.7 (06 MUST NOT implement the spec-12 verifier), I4 (`gh` is parsed, never run). `gh api` endpoint matching: `/pulls/[0-9]+/merge` or `/merges` → ask; dynamic endpoint → `deny unsupported-form`. Rebase-in-progress branch is read from `rebase-merge/head-name` or `rebase-apply/head-name` under the git dir.
- Reason: owner-authorizable non-push operations form one rule family with one AC cluster (AC-08).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** R20 `reset --hard`; R21 `clean` without `-n`/`--dry-run` (`-i` unsupported); R22 `branch -d/-D/--delete` (local or `-r`) and R23 `update-ref -d refs/heads/*` / `--stdin` via the exception-verifier interface; R24 `branch -f/-m/-M/-c/-C`, `checkout -B`, `switch -C/--force-create`, `update-ref refs/heads/<x>` on protected source/destination; R25 `rebase --abort`/`--show-current-patch` allow; R26 detection with the replay-verifier interface (no-journal implementation); R27 `merge` on protected HEAD (not `--abort`); R28 `pull` on protected HEAD unless `--ff-only` without operands; R29 `gh pr merge`; R30 `gh api`.
- **Out of scope:** journal reading/verification (T-06), push rules, diagnostics rendering.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh

## Steps
1. Add failing AC-08 cases (every ask and every allow/not_applicable example of the criterion) plus `git rebase main` without a journal → `ask rebase-outside-restack` and `rebase --abort` → allow. Run and observe RED.
2. Implement R20, R21.
3. Implement the exception-verifier interface and R22/R23.
4. Implement R24 using the shared protected-ref function.
5. Implement R25 and R26 detection with the replay-verifier interface.
6. Implement R27, R28 with HEAD resolution.
7. Implement R29 and R30 endpoint matching.
8. Run focused and full suites; refactor while green.

## Acceptance Criteria
- `reset --hard`, `clean -fd`, `branch -d`, `branch -D`, `update-ref -d refs/heads/x`, `branch -f main`, `checkout -B main`, `merge` on `main`, `pull` on `main` without `--ff-only`, `gh pr merge 1`, `gh api -X PUT repos/o/r/pulls/1/merge` and `git rebase main` without a journal each give ask with their reason codes (`reset-hard`, `clean`, `branch-delete`, `protected-ref-rewrite`, `merge-into-protected`, `pr-merge`, `rebase-outside-restack`); `reset --soft`, `clean -n`, `merge` on `feat/x`, `pull --ff-only` on `main`, `gh pr create`, `rebase --abort` and every read-only subcommand give allow or not_applicable; a dynamic `gh api` endpoint gives `deny unsupported-form`; the branch-deletion path calls the exception-verifier interface, whose only implementation returns "no exception".

## Test Plan
- **Level:** integration (real disposable repositories, protected config, an in-progress rebase fixture), unit (endpoint matcher and verifier interface)
- **Scenarios:**
  - Each AC example → expected decision and reason code.
  - Verifier interface → a test-injected verifier is consulted for R22/R23 (proves the extension point) while the shipped one returns no exception.
- **Edge cases:** `branch --delete -r origin/x`, `clean -nfd` vs `clean -fdn`, `switch --force-create main`, `pull --ff-only origin main` (operands → ask), `merge --abort` on main, detached HEAD, `gh api` with `--method` and with `-XPUT`.
