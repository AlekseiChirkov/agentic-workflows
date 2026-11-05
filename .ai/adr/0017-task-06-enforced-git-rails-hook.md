# ADR-0017: Decisions for Task 06 — Enforced git rails for agent shell commands

## Status

Accepted (2026-11-05; recorded provisionally on 2026-11-03)

## Date

2026-11-03

## Related Task

- Task: [task-06-harness-git-rails](../tasks/completed/task-06-harness-git-rails/state.md)
- Related pull requests: #64–#75 (one stacked pull request per subtask and fix group)
- Related files: `hooks/git-rails.sh`, `hooks/git_rails.py`, `harness/claude/hooks.json`,
  `harness/claude/permissions.json`, `harness/claude/capabilities.md`,
  `harness/codex/capabilities.md`, `scripts/install-hooks.py`, `rules/git-flow.md`,
  `workflows/restack.md`, `tests/git-rails.sh`, `tests/hook-install.sh`,
  `scripts/validate-contracts.sh`

## Summary

Move the supported subset of the git safety rails from prose into a Claude Code
`PreToolUse` hook for the `Bash` tool. Inside registered projects the hook denies
agent-fixable violations, asks the owner for owner-only operations, allows a verified
`/restack` replay and lease publication, and stays out of the way elsewhere. It is
write-free, offline, deterministic and fail-closed, and it is installed through the
existing owned-hook installer with a deny-only permissions fragment.

## Context

ADR-0008 and principle P10 move enforcement toward the harness. ADR-0009 Decision 5
scoped a git-rails hook. Spec 06 (revision 2026-11-03) turns that scope into an
implementation contract with owner decisions D1–D4 and revision defaults D5–D10.
Spec 13 (final harness layout) was planned first; the owner decided on 2026-11-03 to
implement 06 against the current `harness/claude/` layout so the enforced rails protect
spec 13's mass-rename runs. Discovery confirmed from the official Claude Code
documentation (2.1.317, read 2026-11-03) that hook `ask` decisions reach a human in
`default` and `auto` modes and that `"onFailure": "block"` exists.

## Supersedes

Amends ADR-0009 (effective on acceptance, 2026-11-05):
- Decision 5, git-rails bullet: "detects tracked `.ai/` via `git ls-files .ai` cached per
  session" is replaced by repository ignore rules evaluated per call with no cache (D3).
- Decision 7, execution order: 06 runs before 13a/13 (owner, 2026-11-03).
ADR-0009 stays Accepted for every other decision.

## Decisions

### Decision 1: Bash prefilter entrypoint over a single-file Python core

**What was decided:**
`hooks/git-rails.sh` reads at most 1 MiB, exits 0 when no registry exists or no `git`/`gh`
word is present, checks for Python 3.11+, and `exec`s `python3 -I hooks/git_rails.py`. The
core is one standard-library file: tokenizer, parser, resolver, a per-subcommand rule
dispatch table, I3 combination, adapter and diagnostics renderer, plus one sanitized
git-read function with a 2 s timeout.

**Why:** spec D1 and §7.1; matches the typed single-file stdlib style of
`scripts/install-hooks.py`; unit-testable by import; deterministic.

**Alternatives:** a multi-module package with `sys.path` insertion; a declarative rule
table with a generic engine. Both rejected (see Rejected Options).

**Consequences:** one large file organised by section; later rules extend the dispatch
table rather than adding modules.

### Decision 2: Named verifier interfaces

**What was decided:**
Branch-deletion exceptions (spec §8.7), lease verification (R18) and replay verification
(R26) are named callables. The shipped branch-deletion verifier always returns "no
exception"; the lease and replay verifiers read the `/restack` recovery journal.

**Why:** spec §8.7 requires the extension point for spec 12; the stacked implementation
introduces rules before their journal verification.

**Consequences:** spec 12 adds a verifier without changing the rule matrix.

### Decision 3: Owner authorization through the harness ask decision only

**What was decided:**
No in-band bypass (D2). `ask` is emitted only for permission modes listed in
`harness/claude/capabilities.md` (initially `default`, `auto`); any other, missing or
unknown mode turns `ask` into `deny owner-approval-unavailable`. The harness-native
`allow` is never emitted (D7). The allowlist is a core constant kept equal to the
capability record by a validator check, not parsed at runtime.

**Why:** an approval must reach a human; runtime Markdown parsing would make an
editorial change an enforcement change.

### Decision 4: Fail-closed registration and defense-in-depth deny fragment

**What was decided:**
The `PreToolUse` handler declares `"onFailure": "block"`. `harness/claude/permissions.json`
holds only exact deny patterns for blanket staging and `commit -a` (D8). The installer
validates each manifest group against the handler its event declares, records owned deny
strings in receipt `schema_version: 2` (`owned_permissions`), and migrates version-1
receipts.

**Why:** spec §10.1–§10.3; a deny rule would override an owner's ask approval, so only
deny-class rows go into the fragment.

**Consequences:** a crash or timeout of the git-rails handler blocks the Bash call; the
logging handlers keep `"onFailure": "continue"` (ADR-0013).

### Decision 5: `.ai/` staging follows repository ignore rules per call

**What was decided:**
Staging policy uses `git check-ignore` evaluated per invocation with no cache; force-adding
an ignored path asks the owner (D3). Consumer projects that ignore `.ai/` keep state local;
this repository, which tracks `.ai/` (ADR-0012), can stage its knowledge files.

### Decision 6: Unverifiable forms fail closed inside registered projects

**What was decided:**
The core analyses only a supported subset of shell grammar and resolves every git target it
can verify. Shell option words are read through an allowlist of bash's own grammar, and only
the exact `bash|sh -c '<literal>'` form is parsed for nested commands. Every other spelling
that hands a shell a command string or standard input, every unknown wrapper given a git or
gh word, stdin-fed shells, failed `cd` targets and relative redirects that reach back into a
registered project are opaque and deny `unsupported-form` or `opaque-environment`. Script
operands stay out of scope (residual X1). busybox is read as a wrapper whose next word is the
program.

**Why:** spec invariant I2 (fail closed); repeated independent validations showed that
per-spelling repairs did not converge, while an allowlist checked against real shells did
(generated differential matrices against bash, dash and busybox with a recording fake git:
0 violations).

**Alternatives:** follow each newly found spelling; parse shell strings fully. Rejected:
the first never converges, the second is a shell implementation.

**Consequences:** rare legitimate spellings (dash-only options, single-dash long options,
a script operand held in a variable) deny inside registered projects when the command also
contains a git or gh word.

### Decision 7: Same-command state changes make later state reads unverifiable

**What was decided:**
Once an earlier part of a Bash command may write (any scope; directory changes, plain
assignments, data programs and read-only git exempt), later rules that would read repository
or file state deny instead of reading it. Consequently `git commit … && git push` is denied;
the agent runs the two commands as separate Bash calls.

**Why:** the hook decides before the command runs, so a read after a same-command write
would describe the wrong state.

### Decision 8: Ambiguous option prefixes are evaluated as every candidate

**What was decided:**
A long-option prefix that git would reject as ambiguous is evaluated as each candidate and
the most severe decision wins (`git push --forc` asks as a forced push).

**Why:** the hook must not be weaker than any reading git might take after an upgrade.

### Decision 9: The installer pins each event's failure mode and exact deny rules

**What was decided:**
The installer registers the resolved physical path of a readable entrypoint, accepts only
the failure mode fixed for each event (tool gate `block`, logging handlers `continue`; any
other value or event is `invalid-manifest`), and accepts only exact `Bash(...)` deny rules
with no wildcard and no inner closing parenthesis.

**Why:** spec §10.1–§10.3 and ADR-0013 (nonblocking logging); a wildcard deny rule would
override owner approvals.

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| Spec 13 is not done; implement against the current layout? | Yes (owner, 2026-11-03) | Files placed under current `harness/claude/`; rule path kept in one constant |
| Can hook `ask` reach a human in an interactive mode? | Yes: `default` and `auto` (docs, 2026-11-03) | Spec §14 step-2 stop does not fire; allowlist starts with those modes |
| May tests carry literal `T-NN`/`ADR-NNNN` strings? | Yes, only as commit-message pattern fixtures in `tests/git-rails.sh` (owner, 2026-11-03) | Scoped exception to the pipeline-identifier rule; nowhere else |
| What is a malformed registry? | Strict: the registration writer's validity predicate plus non-UTF-8 or unreadable (owner, 2026-11-03) | Any invalid line denies relevant commands machine-wide; next step tells the owner to fix or remove that line |
| Branch-deletion wording in the rule? | Domain wording without a spec number (owner, 2026-11-03) | Rules copied to consumer projects stay free of dangling references |
| How does task knowledge enter git? | `docs:` commit(s) on the last leaf branch after validation (owner, 2026-11-03) | Feature commits stay code-only |
| Run subtasks in parallel where independent? | No, strictly sequential (owner, 2026-11-03) | One stacked branch per subtask |
| How are ambiguous long-option prefixes read? | As every candidate, most severe wins (owner, 2026-11-03) | Decision 8 |
| Shells other than bash/sh with `-c`? | Opaque, deny (owner, 2026-11-03) | Part of Decision 6 |
| Unlisted wrappers given a git or gh word? | Deny, except a small data-program allowlist (owner, 2026-11-03) | Part of Decision 6 |
| `HOME=`, `XDG_CONFIG_HOME=`, `PATH=` prefixes on governed git? | Deny as opaque environment (owner, 2026-11-03) | Same reason code as `GIT_*` |
| State change earlier in the same command? | Sticky "state may change" mark (owner, 2026-11-03) | Decision 7 |
| Remaining questions during the run? | Decided by the orchestrator under owner delegation (owner, 2026-11-04), each recorded in task state | Fail-closed choices per I2 |
| Shell forms outside the analysed subset found late (busybox shell startup-file options, startup and prompt code, unnormalised stdin paths)? | Record as residual risks, no code change (owner, 2026-11-05) | X1 and X12 wording in the capability record |

## Rejected Options

- Package layout with runtime capability parsing: import seam without codebase precedent;
  documentation formatting would change enforcement.
- Declarative rule table and generic engine: R04/R10/R18/R26 need git reads and
  cross-field logic; hypothetical flexibility.
- Merging leaves to reach eight subtasks: would combine independently testable components.

## Implications for Future Work

- Spec 12 adds the child-branch deletion verifier through Decision 2.
- Spec 13 adds `permissions.json` to its adapter file list and may move the rule-path
  constant.
- Spec 17 must add any output-bounding wrapper to the supported wrapper list with tests.
- Residual risks X1–X20 in `harness/claude/capabilities.md` remain documented
  non-guarantees; X11 is operational: the entrypoint lives in the checkout and blocks on
  failure, so uninstall before checking out a revision without it.
- The scratch differential shell matrix used during validation is worth keeping as an
  opt-in tool for later shell-grammar changes.

## Verification

- `bash scripts/validate-contracts.sh` at the stack tip: 717 passed, 0 failed, 2 skipped
  (private hygiene patterns not configured); `--git-rails-only` 2346/0;
  `--hook-install-only` 79/0.
- Task-level contract check 33/0; every subtask and fix group validated independently,
  test-first commits audited.
- Generated differential shell matrices (real bash, dash and busybox with a recording fake
  git): 348,741 and 122,816 commands, 0 cases where a real shell ran a protected push while
  the hook stayed silent.
- Limitations: the residuals above; live-session behaviour is covered by the capability
  record's documented protocol, not by an end-to-end harness run.

## References

- Specification: `.ai/specs/completed/06-harness-git-rails.md`
- Claude Code documentation: https://code.claude.com/docs/en/hooks,
  https://code.claude.com/docs/en/permissions, https://code.claude.com/docs/en/permission-modes
