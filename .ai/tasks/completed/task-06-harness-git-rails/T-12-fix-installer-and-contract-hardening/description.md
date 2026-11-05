## Goal
The installer refuses unreadable or non-physical entrypoints, blocking logging handlers and wildcard deny rules, and the git-flow protected-push row records that dry-run pushes are allowed, each pinned by a failing case first.

## Context
- Dependencies: T-11-fix-push-and-pull-resolution-gaps (stack order)
- Constraints: spec §10.1–§10.3, AC-13, AC-14; nonblocking logging (logging handlers must keep `onFailure: continue`); installer guarantees unchanged; contract-change order (failing check first). Task-level review issues 6, 7, 8, 9.
- Reason: shared fix group — each issue clears the quick-flow gate (two files, existing invariants, no schema change).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; spec files are not edited; no shared knowledge file is written by the worker — return deltas; never weaken a frozen test.

## Scope
- **In scope:** issue 6 (the source check requires a readable entrypoint and registers its resolved physical path; a mode-000 entrypoint or a symlinked `hooks/` component is `invalid-source` or is registered by its physical path, with no write on refusal); issue 7 (a per-event failure-mode constant pins Stop/SubagentStop to `continue` and PreToolUse to `block`; any other value is `invalid-manifest`); issue 8 (`PERMISSION_RULE` rejects `*` and any `)` before the closing parenthesis → `invalid-manifest`, no write); issue 9 (the protected-push row in `rules/git-flow.md` notes that a non-forced dry run is allowed, pinned by a new contract check).
- **Out of scope:** decision core, other rule rows, receipt schema.
- **Target files:** scripts/install-hooks.py, tests/hook-install.sh, rules/git-flow.md, scripts/validate-contracts.sh

## Steps
1. Add failing installer cases for issues 6–8 and a failing contract check for issue 9; observe RED.
2. Require a readable physical entrypoint and register the resolved path.
3. Pin per-event failure modes.
4. Reject wildcard and malformed deny rules.
5. Add the dry-run note to the protected-push row.
6. Run the installer suite, then the full suite alone.

## Acceptance Criteria
- Installing from a scratch source with a mode-000 `hooks/git-rails.sh` reports `invalid-source` and writes nothing; with a symlinked `hooks/` the registered argument is the physical path; a manifest whose Stop or SubagentStop handler declares `onFailure: block`, or whose PreToolUse handler declares `continue`, is `invalid-manifest` with no write; a fragment holding `Bash(*)` or `Bash(git add *)` is `invalid-manifest` with no write.
- The protected-push row of `rules/git-flow.md` says a non-forced dry run (`--dry-run` or `-n`) is allowed, and its new contract check passes; every pre-existing installer case and check passes unchanged; the full suite passes with zero failures.

## Test Plan
- **Level:** integration (installer against scratch homes and sources), smoke (contract check)
- **Scenarios:** each acceptance criterion → the stated status, receipt and settings bytes.
- **Edge cases:** readable but non-executable entrypoint (bash runs it), symlinked source root vs symlinked `hooks/`, `Bash()` empty rule, rule with a nested parenthesis, foreign groups untouched on refusal.
