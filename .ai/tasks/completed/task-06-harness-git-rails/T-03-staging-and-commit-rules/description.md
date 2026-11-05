## Goal
The core decides `git add`/`git stage` and `git commit` invocations per rules R01–R10, the static commit-message sources and forbidden patterns P1–P3 of spec §8.3, and the `.ai/` staging policy of §8.6.

## Context
- Dependencies: T-02 (parser, resolver, parse-options helper, rule dispatch table, suite)
- Constraints: spec §8.1 rows R01–R10, §8.3, §8.6, D3 (ignore rules via `git check-ignore`, per call, no cache), D4 (literal file paths only), D5 (any `Co-Authored-By:` trailer line), D6 (word-boundary identifier matching). Patterns P1–P3 are used exactly as written in §8.3. The `-F` file limit is 1 MiB (§7.5). Commit-message text never appears in any decision output.
- Constraints: owner exception (batch gate 2026-11-03): literal `T-NN`/`ADR-NNNN` strings are allowed only as commit-message pattern fixtures inside `tests/git-rails.sh` or its table data — never in test names, comments, the core or any other file. `.ai/state.md` / `.ai/adr/x.md` are disposable-repository fixture paths.
- Reason: staging and commit rules share path-operand checks (R07 reuses R01–R02) and form one verifiable rule family.

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** R01 blanket staging (`-A`, `--all`, `--no-ignore-removal`, `-u`, `--update`, `.`), R02 non-file operands (directory, glob, `:` magic, missing-and-untracked, `--pathspec-from-file`), R03 interactive forms, R04 forced ignored path → ask, R05 allow (file, symlink, tracked deleted path); R06 `-a`/`--all`/bundles, R07 commit path operands and `-i`/`-o`, R08 unverifiable message sources, R09 forbidden patterns, R10 `--amend` on a commit reachable from `refs/remotes/*` → ask; message sources `-m`/`--message` (joined with blank lines), `-F <path>`/`--file=`, `-F -` with attached heredoc/here-string, `-m "$(cat <<'D' … D)"`, `--trailer`, `--amend --no-edit` (HEAD message plus trailers); unquoted-delimiter heredoc bodies containing `$`, backticks or `\` → R08.
- **Out of scope:** push, other operations, restack, diagnostics rendering, entrypoint.
- **Target files:** hooks/git_rails.py, tests/git-rails.sh

## Steps
1. Add failing cases for AC-04: for every row R01–R07 a violating case, an allowed neighbour and an alternative spelling, including `-Av`, `--al`, `-u`, `.`, `src/`, `'*.py'`, `:/`, `--pathspec-from-file`, `-p`, forced ignored `.ai/state.md` (ask), unignored new `.ai/adr/x.md` (allow), deleted tracked file (allow); plus the AC-03 decisions `cd sub && git add -A` deny, `(cd sub; git add a.txt)` allow, `bash -c 'git add .'` deny, `command git add --all` deny, `env X=1 git commit -am x` deny.
2. Add failing cases for AC-05 (every forbidden, allowed and unverifiable example of the criterion, `--amend` published vs unpublished). Run and observe RED.
3. Implement operand classification with `git check-ignore` and `ls-files` reads.
4. Implement R01–R05 and R07 reuse.
5. Implement static message extraction for every §8.3 source and the R08 list.
6. Implement P1–P3 matching and R09.
7. Implement R10 reachability via `git for-each-ref refs/remotes`/`merge-base --is-ancestor` (read-only).
8. Run focused and full suites; refactor while green.

## Acceptance Criteria
- Staging: every R01–R07 violating case gives its stated reason code (`blanket-staging`, `staging-not-file`, `unsupported-form`, `commit-all`), forced ignored `.ai/state.md` gives `ask staging-ignored-path`, and every allowed neighbour (including unignored new `.ai/adr/x.md`, a symlink and a deleted tracked file) gives allow; the five AC-03 staging/commit grammar commands give their stated decisions.
- Commit messages: a `Co-authored-by:` trailer via `-m`, `$(cat <<'EOF' … EOF)`, `-F file`, `-F -` heredoc and `--trailer`, `T-04b` in the subject, `ADR-0007` in the body and `--amend --no-edit` on a trailer-bearing HEAD each give `deny commit-message-forbidden`; `fix GPT-4 parsing`, `Bump T-shirt sizes` and a body sentence mentioning Co-Authored-By give allow; bare `git commit`, `-c HEAD`, `--fixup` and an unquoted heredoc containing `$X` give `deny commit-message-unverifiable`; `--amend` on a commit contained in `refs/remotes/*` gives `ask rewrite-published` and on an unpushed commit gives allow.

## Test Plan
- **Level:** integration (rules evaluated against real disposable repositories with real ignore rules, tracked/deleted files and remote-tracking refs), unit (pattern functions P1–P3 and message joining)
- **Scenarios:**
  - AC 1 staging cases → expected decision and reason code.
  - AC 2 message cases → expected decision and reason code.
- **Edge cases:** `--` separator before paths, operand with spaces, unique-prefix ambiguity (`--a` ambiguous → unsupported or as git), repeated `-m`, `-F` file over 1 MiB, unreadable `-F` file, relative `-F` path resolved from effective directory, CRLF messages, trailer with leading whitespace.
