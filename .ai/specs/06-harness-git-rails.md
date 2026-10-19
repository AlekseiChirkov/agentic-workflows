# Enforce the git safety rails with harness hooks and permission rules

## Goal

`rules/git-flow.md` forbids `git add -A`, pushing to protected branches, force-push
outside `/restack`, `reset --hard`, `clean`, branch deletion, `gh pr merge`, and staging
anything under `.ai/`. All of it is prose. A `PreToolUse` hook and a permission deny-list
make the operations fail in the harness, so a lapse in compliance cannot damage a
repository (ADR-0009, Decision 5).

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
- Enforcement on harnesses without hooks (Codex today)

## Notes

- Decisions: ADR-0009 Decision 5 (user-level, registered projects only, protected
  branches, message patterns, `git ls-files` detection, stderr-only) and Decision 4
  (temporary child branch deletion).
- Depends on spec 13 (`harness/`, registry) and follows spec 05 in the chain.
- Parsing is conservative: block on match; never reason about quoting.
