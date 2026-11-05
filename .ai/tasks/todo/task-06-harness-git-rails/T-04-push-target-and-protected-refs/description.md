## Goal
The core resolves every `git push` target remote and destination ref per spec §8.4, computes the protected-ref set per §8.2, and decides pushes per rules R11–R17 and R19, routing `--force-with-lease` (R18) to a lease-verification interface that, until the restack verifier exists, reports "no journal" so R18 gives `ask push-lease-unverified`.

## Context
- Dependencies: T-02
- Constraints: spec §8.1 R11–R19, §8.2, §8.4, I3 (every destination checked), I4 (no network: never `fetch`/`ls-remote`), I8. Protected set = target of `refs/remotes/<r>/HEAD` (missing → R13 with next step `git remote set-head <r> --auto`), `main`, `master`, `release/*`, and every `git config --get-all orchestrail.protectedBranch` pattern (fnmatch on the short name). Local protection for later rules uses `<r>` = `origin` (only entries 2–3 when `origin` is missing) — expose this as a function for T-05.
- Constraints: the lease verifier is an interface (callable) so T-06 replaces only its implementation; T-04 ships the "no journal found" implementation.
- Reason: push resolution and protected refs are one component with its own AC cluster (AC-06).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** remote resolution (literal configured remote; URL/unknown → R12; defaults `branch.<cur>.pushRemote`, `remote.pushDefault`, `branch.<cur>.remote`, `origin`; configured `remote.<r>.push` → R12); refspec parsing (`+`, `<src>[:<dst>]`, `HEAD`, detached HEAD → R12, `refs/` prefixing, tag-only sources → `refs/tags/<dst>`, empty src = delete); `push.default` (`simple`/`current`/`upstream`/`matching`/`nothing`); R11 `--dry-run`/`-n` allow; R13–R17, R19; R18 detection and lease parsing (`=<ref>:<sha>`, `<ref>:`), calling the verifier; protected-set function shared with T-05.
- **Out of scope:** journal reading/verification (T-06), other subcommands, diagnostics rendering.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh

## Steps
1. Add failing AC-06 cases with local bare remotes: every `ask push-protected-target`, allow, `ask push-force`, `ask push-lease-unverified`, `ask push-delete`, `ask push-bulk-or-tags`, `deny push-target-unknown`, `deny default-branch-unknown` and `--dry-run` case of the criterion, plus AC-03 `timeout 30 git push -f` → ask. Run and observe RED.
2. Implement remote resolution and its config reads.
3. Implement refspec and `push.default` destination resolution.
4. Implement the protected-ref set and the shared local-protection function.
5. Implement R11–R17 and R19 with I3 across destinations.
6. Implement R18 detection, lease parsing and the verifier interface with the no-journal implementation.
7. Run focused and full suites; refactor while green.

## Acceptance Criteria
- `origin main`, `origin feat/x:main`, `origin HEAD:refs/heads/release/1.2`, `origin HEAD` on `main`, bare `git push` on `main` with `push.default=simple`, a configured extra protected pattern, and `feat/x feat/y:main` each give `ask push-protected-target`; bare push on `feat/x` and `origin feat/x` give allow; `-f`, `--forc`, `+feat/x`, `--force-if-includes` and `timeout 30 git push -f` give `ask push-force`; `--force-with-lease` without a journal gives `ask push-lease-unverified`; `--delete x` and `:x` give `ask push-delete`; `--tags`, `--mirror`, `--all`, a tag destination and `push.default=matching` give `ask push-bulk-or-tags`; a URL remote, detached HEAD and `remote.origin.push` give `deny push-target-unknown`; a missing `refs/remotes/origin/HEAD` gives `deny default-branch-unknown`; `--dry-run` gives allow; no case performs a network operation.

## Test Plan
- **Level:** integration (real disposable repositories with local bare remotes and real config)
- **Scenarios:**
  - Each AC example → expected decision and reason code.
- **Edge cases:** `--force-with-lease` bare vs `=ref` vs `=ref:sha`, `--no-force` negation, `--repo=`, multiple refspecs mixing protected and unprotected, `refs/heads/` explicit dst, `origin/HEAD` pointing to a non-main branch, protected pattern with `*`, `origin` absent.
