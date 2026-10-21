# Enforce the git safety rails with harness hooks and permission rules

## Goal

`rules/git-flow.md` forbids `git add -A`, pushing to protected branches, force-push
outside `/restack`, `reset --hard`, `clean`, branch deletion, `gh pr merge`, and staging
anything under `.ai/`. All of it is prose. A `PreToolUse` hook and a permission deny-list
make the operations fail in the harness, to enforce the covered command forms and reduce reliance on
prompt compliance (ADR-0009, Decision 5).

## Acceptance Criteria

- [ ] `hooks/git-rails.sh` (`PreToolUse` for `Bash`) blocks, quoting the rule:
      `git add -A|.|--all`, `git commit -a`, `git push` to the default branch or any
      `release/*` branch, `git push --force` (allowing `--force-with-lease` only when the
      `/restack` marker is present), `git reset --hard`, `git clean`, `git branch -D|-d`
      (except a temporary composite child branch the orchestrator created and already
      merged — ADR-0009 Decision 4), `gh pr merge`, `git rebase` outside `/restack`
- [ ] The hook blocks `git commit` when the message contains `Co-Authored-By`, a
      `T-[0-9A-Za-z]+` identifier, or `ADR-[0-9]+`
- [ ] The hook blocks staging any path under `.ai/` unless `git ls-files .ai` is
      non-empty (tracked `.ai/`, as in this repository); the result is cached per session
- [ ] Installed at **user level** by `sync.sh` from `harness/claude/hooks.json`,
      idempotently; the hook exits immediately unless the current directory is a
      registered project
- [ ] A `permissions.deny` fragment with the equivalent patterns ships in
      `harness/claude/` and is merged into `~/.claude/settings.json` by `sync.sh`
- [ ] Blocked operations are reported on stderr only (no `notes:` edit) until a state
      tool exists
- [ ] `rules/git-flow.md → ## Safety rails` gains an "enforced by" column: the hook name
      on `hooks: yes` harnesses, "prose only" otherwise
- [ ] `tests/git-rails.sh` feeds every forbidden form and the allowed forms
      (`git add <path>`, `git push origin feat/x`, `--force-with-lease` under `/restack`)
      to the hook and asserts the verdicts

## Out of Scope

- RED-set protection (refusing test-file edits during GREEN) — a separate future spec
- Hook enforcement where the installed harness lacks the required capability

## Notes

- Decisions: ADR-0009 Decision 5 (user-level, registered projects only, protected
  branches, message patterns, `git ls-files` detection, stderr-only) and Decision 4
  (temporary child branch deletion).
- Depends on spec 13 (`harness/`, registry) and follows spec 05 in the chain.
- Parsing is conservative: inspect the actual executable/arguments and supported shell
  forms; ambiguous or opaque commands must not receive a success-shaped allow verdict.

## Optimization integration — 2026-10-21

- **REQ-01** THE SYSTEM SHALL keep protected commands visible to hooks through optional
  helpers, nested shells and tool-output capture. If equivalent inspection cannot be
  guaranteed, the helper SHALL refuse wrapping the mutation and use direct native
  execution subject to existing approvals.
- **REQ-02** THE SYSTEM SHALL preserve stderr deny reasons and the nonzero deny status
  through compact output. Repair/escalation SHALL not bypass git/commit-message rails,
  explicit-path staging or the test-before-implementation commit order.
- **REQ-03** THE SYSTEM SHALL distinguish a tracked source knowledge base from untracked
  consumer metadata using the resolved repository/worktree identity; a cached result
  from another repository SHALL not authorize staging here.
- **REQ-04** THE SYSTEM SHALL test quoted/alternate command forms, wrappers and negative
  cases offline. Claims about enforcement SHALL name actual harness capability and
  limits; mere deny-pattern presence SHALL not be described as universal shell safety.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02) Direct, wrapped and nested fixture commands preserve
  the same deny outcome or the wrapper refuses; truncation never changes deny to allow.
- [ ] **AC-02** (REQ-03, REQ-04) Switching repository/worktree invalidates inappropriate
  metadata caches; tracked-source exceptions cannot leak to consumers, and command/
  quoted-form fixtures document the actual supported enforcement surface.

Dependencies stay 13 and 05. Specs 15/17/19 consume these rails and must not redefine
or weaken them. Temporary-child deletion is permitted only under the ownership and
already-merged proof required by 12, not an untrusted marker alone.
