## Goal
The git-rails decision core closes the push, pull and parser gaps found by task-level review: refspecs split at the last colon, upstream merge values qualified, pull and config-driven program options refused, `pull --rebase` with updateRefs asking, relative repository redirects anchored, the `pipefail` shell form pinned, and a forced push with an otherwise valid journal naming its failed check.

## Context
- Dependencies: T-10 (stack tip; the whole decision core and suite)
- Constraints: spec I2, §7.3, §7.4, §8.1 R12–R18, R26, R28, §8.4, §8.5, §1.2 threat model; Assumptions in task state (ambiguous prefix, state-change mark, owner delegation). Python stays typed stdlib single-file, functions ≤30 lines / ≤3 parameters. Reuse the existing helpers (`full_name`, `state_changed`, `updates_refs`, `read_git`, anchors). Task-level review issues 1, 2, 3, 4, 5, 10, 11, 12 (see `## Code Review`).
- Reason: one component — push/pull/parser decisions of the core — approved as a dedicated fix branch.

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; spec files are not edited; no shared knowledge file is written by the worker — return deltas; never weaken a frozen test.

## Scope
- **In scope:** issue 1 (last-colon refspec split, keeping `:dst` deletion and `:` matching forms); issue 2 (`branch.<cur>.merge` through `full_name`); issue 3 (`git pull --upload-pack` and its prefixes → deny unsupported-form); issue 4 (a pull reading that rebases — `--rebase`/`-r`, `pull.rebase`, `branch.<b>.rebase` — with `rebase.updateRefs` true → ask protected-ref-rewrite); issue 5 (`remote.<r>.receivepack` configured for the target remote and `push.recurseSubmodules=on-demand`/`only` (also `submodule.recurse` true) → deny unsupported-form, including on journal-allowed lease pushes); issue 10 (relative `--git-dir`/`--work-tree` and `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE` values resolved against the effective directory and recorded as anchors, so a redirect into a registered project from outside is denied); issue 11 (pin `bash -o pipefail -c 'git push -f'` → deny unsupported-form); issue 12 (a forced push with an otherwise valid journal carries the verifier failure `forced` in `Decision.failure` on the R17 ask). Update the capability record only if a residual line changes as a result.
- **Out of scope:** installer, deny fragment, rule text, new rule rows beyond the issues.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh, harness/claude/capabilities.md

## Steps
1. Add new failing rows to `tests/git-rails.sh` reproducing each issue with the review's probe commands (and git 2.53 dry-run evidence where the destination matters); add allowed-neighbour guards; observe RED.
2. Split push refspecs at the last colon.
3. Qualify the upstream merge value.
4. Refuse pull program options and config-driven push programs.
5. Ask for rebasing pulls when updateRefs resolves true.
6. Resolve and anchor relative repository redirects.
7. Attach the lease verifier failure to the R17 decision.
8. Run the focused suite, then the full suite alone; refactor while green.

## Acceptance Criteria
- `git push origin 'HEAD^{/fix:}:main'` and `git push origin ':/fix:main'` ask push-protected-target (R16); `git push origin :feat/x` still asks push-delete and `git push origin :` still asks push-bulk-or-tags; with `push.default=upstream` and `branch.feat/y.merge=heads/main`, `git push` asks R16.
- `git pull --upload-pack=x origin`, a push with `remote.origin.receivepack` configured, and a push with `push.recurseSubmodules=on-demand` deny unsupported-form; `git pull --rebase` on an unprotected branch with `rebase.updateRefs=true` asks protected-ref-rewrite, and without updateRefs stays allowed.
- From an unregistered sibling directory, `git --git-dir=../repo/.git push -f` and `GIT_DIR=../repo/.git git push -f` into a registered project are denied (unsupported-form / opaque-environment); `bash -o pipefail -c 'git push -f'` denies unsupported-form; a `--force` lease push with an otherwise valid journal asks push-force with failed check `forced` in the diagnostic.
- Every pre-existing test passes unchanged; the full suite passes with zero failures.

## Test Plan
- **Level:** integration (real disposable repositories, local bare remotes, scratch registries; git 2.53 dry-run evidence), unit (refspec splitting)
- **Scenarios:** each acceptance criterion's commands → the stated decision; allowed neighbours stay allowed.
- **Edge cases:** refspecs with several colons, `+` prefix with a colon in the source, `^{/…}` with no colon, tag sources, bundled pull options, relative `-C` before a relative `--git-dir`, journal push with `+` refspec.
