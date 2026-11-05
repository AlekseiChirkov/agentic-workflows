## Goal
`rules/git-flow.md → ## Safety rails` carries an `Enforcement` column on every row, the owner-approval protocol of spec §6.3 and the never-evade rule; `workflows/restack.md` documents the §8.5 journal schema and exact command forms; contract checks pin both, and the full suite passes (AC-15).

## Context
- Dependencies: T-01–T-09 (the enforcement values must describe shipped behaviour)
- Constraints: spec §10.4 rows for `rules/git-flow.md`, `workflows/restack.md`, `scripts/validate-contracts.sh`; `.ai/principles/coding.md → Changing a contract` (failing check first, canonical definition, every reader). Enforcement values: `hook: deny`, `hook: ask`, `hook: allow with restack journal`, `text only`. Replace "Branch deletion: Forbidden" with "owner approval required; a verified temporary child-branch exception is planned" (owner decision: domain wording, no spec number in rule text). Keep each row's existing Policy meaning for workflows otherwise (the matrix narrows no textual rule). No pipeline identifiers (`T-NN`, `ADR-NNNN`, `.ai/` paths) in the rule or workflow text; validator Group 26 must stay green. Readers: grep `workflows/`, `rules/`, `docs/USAGE.md`, `workflows/PIPELINE.md`, `templates/` for the reworded branch-deletion policy and update consistently.
- Constraints: the ADR, its index, `.ai/memory/architecture.md` and `.ai/specs/README.md` are written by the orchestrator — return their deltas (hook, permissions fragment, test suite, `--git-rails-only`; ADR content: hook design, D1–D10, amendment of ADR-0009 Decision 5 by D3, roadmap order 06 before 13a/13, residual risks X1–X10).
- Reason: the textual contract update is one documentation component pinned by one check cluster.

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** Safety rails table Enforcement column; branch-deletion rewording; owner-approval protocol (§6.3 steps 2–4) and "never wrap or rephrase a denied command to evade the check"; restack journal schema (`schema_version`, `repository_common_dir`, `task_path`, `target`, `publication_authorized` true only with `--allow-pr`, `order`, `branches.*`, `"absent"`) and the exact rebase/push forms; reader updates; contract checks; full-suite run.
- **Out of scope:** hook code, installer, capability records (T-01), knowledge files (orchestrator).
- **Target files:** rules/git-flow.md, workflows/restack.md, scripts/validate-contracts.sh, plus any reader file whose branch-deletion wording must change

## Steps
1. Add failing contract checks: every Safety rails row has an Enforcement value from the four-value vocabulary (anchored vocabulary line); the branch-deletion row has the new wording; the owner-approval protocol and never-evade sentence exist; `workflows/restack.md` names every §8.5 schema field, `publication_authorized`, `"absent"` and both exact command forms. Run and observe RED.
2. Update `rules/git-flow.md`.
3. Update `workflows/restack.md` so the journal it writes carries the schema and `publication_authorized` reflects `--allow-pr`.
4. Grep readers and update consistent wording.
5. Run `bash scripts/validate-contracts.sh --git-rails-only` and the full `bash scripts/validate-contracts.sh`; return knowledge deltas.

## Acceptance Criteria
- The new checks fail before and pass after: every Safety rails row has exactly one Enforcement value from the vocabulary; branch deletion reads "owner approval required; a verified temporary child-branch exception is planned" and no rule file gains a spec number; the owner-approval protocol and the never-evade rule are present; `workflows/restack.md` documents every §8.5 field, the `"absent"` value, `publication_authorized` tied to `--allow-pr`, and the exact `git rebase --onto <new-sha> <old-sha> <branch>` and `git push --force-with-lease=refs/heads/<b>:<sha> origin <b>` forms.
- `bash scripts/validate-contracts.sh --git-rails-only` and the full `bash scripts/validate-contracts.sh` pass with zero failures (optional configured skips allowed and reported).

## Test Plan
- **Level:** smoke (contract checks in `scripts/validate-contracts.sh`)
- **Scenarios:**
  - Each documented element → its anchored check passes after, fails before.
  - Full suite → zero failures.
- **Edge cases:** a row with two Enforcement values, an Enforcement value outside the vocabulary, leftover "Forbidden" branch-deletion wording in a reader, Group 26 commit-scope scan of the edited files.

## Scope extension (decided before execution)

The earlier subtasks assigned these items here; they are in scope:
- **Recovery journal documentation detail:** `order` lists only the branches to replay, in replay order — the first entry is replayed onto `target.sha`, each later one onto the previous entry's `replayed_tip`; `publication_authorized` is true only with `--allow-pr`; `expected_remote_tip` is a SHA, `"absent"` or null.
- **Residual-risk lines in `harness/claude/capabilities.md`** (extend the `## git-rails` residual table or its limitations list; the existing X1–X10 checks stay; add checks for the new lines):
  - the registered entrypoint lives in the checkout and blocks on failure, so checking out a revision without `hooks/git-rails.sh` blocks every Bash call in every project until uninstall; uninstall with the current installer before checking out such a revision; earlier installers refuse receipts that hold PreToolUse or permission state;
  - the prefilter matches only the literal git/gh word (JSON-escaped letters and shell spellings that split the word skip the core — evasion under the threat model);
  - a registry path the hook cannot stat (an unsearchable directory above the config base, a symlink loop, a non-directory component) reads as absent;
  - degraded PATH: without head or tr there is no prefilter and every Bash command starts Python; with python3 also missing every command is denied while a registry exists;
  - same-command state change: a group's own write redirection seen by its body, writes in later concurrent pipeline or background elements, data programs that can run commands (`man -P`, `rg --pre`, `file -C`, `less`), configured programs run by read-only git (`diff.external`, `textconv`, `difftool.<tool>.cmd`), commit hooks;
  - unlisted command runners and program options (`for-each-repo`, `grep -O`, `archive --exec`, `--upload-pack`, `submodule update --merge/--rebase`) and operations outside the matrix (fetch refspecs into local branches, `restore`, `stash drop`, `checkout -f`, `filter-branch` without a command filter);
  - restack: `--continue` after a non-journal rebase of an unreplayed stack branch; journals record no remote; no cap on the number of journal files;
  - the exact deny rules apply at user level in unregistered projects too; here-document body lines can match them under the harness's newline splitting; reinstall re-adds an owned rule the user deleted.
- **Runbook delta (returned, not written):** the uninstall-before-old-checkout step, and the new focused suite timings.
- **Target files:** add `harness/claude/capabilities.md`.
