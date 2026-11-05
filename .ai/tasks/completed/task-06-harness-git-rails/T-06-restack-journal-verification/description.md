## Goal
The core reads `/restack` recovery journals from `<git-common-dir>/orchestrail-restack/*.json`, validates the spec §8.5 minimum schema, and replaces the no-journal verifiers so the exact replay `git rebase --onto <new-sha> <old-sha> <branch>` (R26) and the exact explicit-lease publication (R18) are allowed only when every §8.5 check passes, otherwise `ask` naming the failed check.

## Context
- Dependencies: T-04 (lease verifier interface), T-05 (replay verifier interface)
- Constraints: spec §8.5 schema (`schema_version: 1`, `repository_common_dir`, `task_path`, `target{branch,sha}`, `publication_authorized`, `order`, `branches.<b>{original_base_commit, original_tip, replayed_tip, expected_remote_tip}`; extra fields allowed; SHAs 40/64 lowercase hex; `expected_remote_tip` SHA | `"absent"` | null). Exactly one matching journal; zero, several, invalid JSON or schema → ask. No freshness check. Environment variables, marker files and the word `restack` are never evidence (D2). The hook writes nothing (I4); journal reads are bounded by the core limits. `--continue`/`--skip` are allowed only while a rebase of a journal branch is in progress.
- Reason: journal verification is one component (schema + two verifiers over the same record) with its own AC cluster (AC-07).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** journal discovery and parsing, schema validation, R26 replay checks (common dir equality, branch in `order` and unprotected with `replayed_tip == null`, `<old-sha>` = `original_base_commit`, current tip = `original_tip`, `<new-sha>` = `target.sha` for the first unreplayed entry else previous `replayed_tip`), `--continue`/`--skip` during a journal-branch rebase, R18 lease checks (in `order`, unprotected, `publication_authorized`, local tip = `replayed_tip`, lease SHA = `expected_remote_tip` or empty lease with `"absent"`, no `+`/`--force`), failed-check naming in the result.
- **Out of scope:** writing journals (documented for `workflows/restack.md` in T-10), diagnostics rendering.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh

## Steps
1. Add failing AC-07 cases: a valid journal allows the exact rebase and the exact lease push; wrong repository, branch not in `order`, moved local tip, wrong `<old-sha>`, wrong `<new-sha>`, lease SHA ≠ `expected_remote_tip`, `publication_authorized: false`, `--force` with a valid journal, protected destination, invalid JSON and two matching journals each give ask naming the failed check; `RESTACK=1` and a marker file have no effect; `--abort` stays allow. Run and observe RED.
2. Implement journal discovery and bounded parsing.
3. Implement schema validation.
4. Implement the replay verifier and in-progress `--continue`/`--skip` handling.
5. Implement the lease verifier.
6. Wire both verifiers in place of the no-journal implementations and run focused and full suites; refactor while green.

## Acceptance Criteria
- With one valid journal, `git rebase --onto <target.sha> <original_base_commit> <first branch>` and `git push --force-with-lease=refs/heads/<b>:<expected_remote_tip> origin <b>` (with `publication_authorized: true` and local tip = `replayed_tip`) give allow; each listed failure gives `ask rebase-outside-restack` or `ask push-lease-unverified` whose result names the failed check; `RESTACK=1` and a marker file change no decision; `rebase --abort` gives allow; the pre-existing T-04/T-05 no-journal cases still give ask.

## Test Plan
- **Level:** integration (real disposable repositories, local bare remotes, journal files in the real common dir), unit (schema validator)
- **Scenarios:**
  - Valid-journal allow cases and each enumerated failure → expected decision and named check.
- **Edge cases:** 64-hex SHAs, uppercase SHA rejected, `expected_remote_tip: "absent"` with empty lease, null `expected_remote_tip`, second branch using previous `replayed_tip`, journal for another repository in the same directory, extra fields, worktree (common dir ≠ git dir).
