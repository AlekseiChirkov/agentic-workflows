# Claude logging capabilities

hooks: yes
profile: claude-stop-v1
verified: 2026-10-25
runtime: Claude Code 2.1.309

The native Stop and SubagentStop mechanism is supported by this release. Isolated
native payload, correlation, ownership lifecycle and recovery fixtures provide
verification evidence; they do not demonstrate every workflow step in a live session.

Mechanism support, the current installation result, and accepted checkpoint coverage
are separate facts. A hook alone does not prove step coverage. Named workflow coverage
requires exactly one native Skill invocation, matching dispatch and report markers,
and a producer receipt. An unambiguously correlated session with no Skill invocation
may report `step: unknown`, providing observed coverage without named workflow coverage.
Unknown session coverage cannot suppress a named prompt event. A matching accepted
receipt for a named checkpoint suppresses only its corresponding prompt event.

If capability is unknown or installation is unavailable, retain prompt logging with
`note: approximate`; unobserved boundaries also retain that path. Run start and run
end remain prompt driven. Uncertain delivery retries only its frozen correlated
payload and cannot claim a second logging route.

Installation requires Bash, Python 3.11 or newer, jq and flock. Python is used by the
installer. Native hooks require Bash, jq and flock. Ordinary writes retain their existing
legacy dependencies, including optional jq.

## git-rails

name: git-rails
state: yes
runtime: Claude Code 2.1.317
verified: 2026-11-03
evidence: https://code.claude.com/docs/en/hooks
evidence: https://code.claude.com/docs/en/permissions
evidence: https://code.claude.com/docs/en/permission-modes

event: PreToolUse
tool: Bash
deny: exit 2 with the diagnostic on stderr; the harness blocks the call before permission rules are evaluated and gives Claude the stderr text as the denial reason
ask: exit 0 with the ask-output JSON on stdout and the same diagnostic on stderr; the harness shows the reason to the user in the permission prompt
ask-output: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"<diagnostic>"}}
allow: never emitted; an allowed or ungoverned command exits 0 with empty stdout, which leaves the call to the normal permission flow without approving it
permission-mode values: default, plan, acceptEdits, auto, dontAsk, bypassPermissions (the mode labelled Manual arrives as default)
git-rails ask-capable modes: default, auto
failure-mode: onFailure "block" (Claude Code 2.1.295 or later); a handler that cannot start, exits with a code other than 0 or 2, times out or prints invalid JSON blocks the call as exit 2 does
timeout-unit: seconds; a command handler without a timeout defaults to 600 on PreToolUse
deny-rule exact: Bash(<command>) matches only that whole command text, so Bash(git add .) does not match git add .gitignore
deny-rule prefix: Bash(<command> *) and the equivalent trailing Bash(<command>:*) match the command alone or followed by a space and any text; the space is part of the rule and :* is recognised only at the end of a pattern
deny-rule compound: deny and ask rules apply when any subcommand matches, split on &&, ||, ;, |, |&, & and newlines, including subshells, command substitutions and loop bodies; the timeout, time, nice, nohup, stdbuf, command, builtin, noglob and flag-less xargs wrappers and any leading variable assignment are stripped first
deny-rule precedence: rules are evaluated deny, then ask, then allow; deny and ask rules are evaluated regardless of the hook decision, and a hook exit 2 blocks even when an allow rule matches

An ask is offered only in the listed modes. In default the harness prompts the user. In
auto a hook ask goes to the permission prompt and the classifier does not decide it.
dontAsk denies every call that would prompt. bypassPermissions runs calls without
prompting, and the documentation does not show that a hook ask always reaches a person
there. The documentation does not state how plan and acceptEdits treat a hook ask, so
neither is listed. Any other, missing or unknown mode makes the adapter deny with
`owner-approval-unavailable` instead of asking.

limitations:
- A non-interactive `-p` run reports `default` but has no person to answer the prompt. The harness denies the call unless a permission prompt tool or SDK approval callback answers it, and that program then decides instead of the owner.
- In auto mode a call that the harness's own checks also flag may be denied by the classifier before any prompt.
- Without managed settings or a Team or Enterprise login, an installed mod that handles tool checks can approve a call the hook asked about or blocked.
- Permission rules match command text only. They do not match the same program by path, inside `sh -c`, with global options such as `git -C . push`, or with quoted subcommands. The rules are defence in depth; the hook stays authoritative.
- Exit 2 and the ask JSON are the documented protocol for this runtime. A different runtime version needs this record re-verified.

| ID | Residual risk |
|---|---|
| X1 | Git commands run by scripts or programs that the Bash tool starts (`bash scripts/x.sh`, `make`, Python) are not seen. |
| X2 | A shell alias or function named `git` in the user's shell environment is not seen. |
| X3 | Unlisted destructive operations are not enforced: `checkout -- .`, `restore`, `stash drop`/`clear`, `worktree remove --force`, `filter-branch`, `replace`, local `tag`, `git-receive-pack`, and messages of `merge`/`cherry-pick`/`revert`. |
| X4 | Edits to `.git/` through non-Bash tools are not seen. |
| X5 | Between the decision and execution, refs can move. Only an explicit lease is compare-and-swap. |
| X6 | With `onFailure: "block"` a crash or timeout blocks the call; harness behaviour outside that option, such as a runtime that ignores it or a hook disabled by settings, can still let the call proceed. |
| X7 | An opaque command started outside registered projects that targets a registered project is not caught. |
| X8 | The agent can forge the project registry, the restack journal or git configuration. This is outside the threat model. |
| X9 | Codex and other harnesses have textual rules only. |
| X10 | `--allow-pr`, pull request text and the wider attribution rules remain textual. |
| X11 | The registered entrypoint `hooks/git-rails.sh` lives in the checkout and blocks on failure, so checking out a revision without it blocks every Bash call in every project until uninstall. Uninstall with the current installer before checking out such a revision; earlier installers refuse a receipt that holds PreToolUse or permission state. |
| X12 | The prefilter matches only the literal `git` or `gh` word: JSON-escaped letters and shell spellings that split the word skip the core. That is deliberate evasion, which is outside the threat model. |
| X13 | A registry path the hook cannot stat (an unsearchable directory above the configuration base, a symbolic link loop, a non-directory component) reads as absent, so no project is registered for that call. |
| X14 | With a degraded PATH: without `head` or `tr` there is no prefilter and every Bash command starts Python; with `python3` also missing, every command is denied while a registry exists. |
| X15 | State changed earlier in the same command is not always seen: a group's own write redirection seen by its body, writes in later concurrent pipeline or background elements, data programs that can run commands (`man -P`, `rg --pre`, `file -C`, `less`), configured programs run by read-only git (`diff.external`, `textconv`, `difftool.<tool>.cmd`) and commit hooks. |
| X16 | Unlisted command runners and program options are not enforced: `for-each-repo`, `submodule--helper foreach`, `grep -O`, `archive --exec`, `--upload-pack` on fetch, ls-remote and clone, `submodule update --merge`/`--rebase`. Neither are operations outside the rule matrix: fetch refspecs into local branches, `restore`, `stash drop`, `checkout -f`, `filter-branch` without a command filter. |
| X17 | Restack: `git rebase --continue` is allowed after a non-journal rebase of an unreplayed stack branch; journals record no remote, so a lease push is checked against any remote; the number of journal files is not capped. |
| X18 | The exact permission deny rules apply at user level, in unregistered projects too; here-document body lines can match them because the harness splits commands on newlines; reinstall re-adds an owned rule the user deleted. |
