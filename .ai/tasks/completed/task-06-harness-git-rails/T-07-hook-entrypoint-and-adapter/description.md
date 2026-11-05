## Goal
`hooks/git-rails.sh` is the PreToolUse entrypoint (1 MiB stdin read, registry-absent and relevance fast paths, Python ≥3.11 check, `exec python3 -I`), and the core's adapter maps decisions to the Claude Code protocol of spec §6.2 with the §6.3 step-1 permission-mode allowlist, renders the four-line diagnostics of §9 from one next-step table, and enforces the remaining §7.5 limits and §11 failure modes deterministically.

## Context
- Dependencies: T-01 (protocol facts and anchored allowlist line), T-02–T-06 (every reason code the adapter renders)
- Constraints: spec §6.2 (deny = exit 2 + stderr; ask = exit 0 + exact `hookSpecificOutput` JSON + same diagnostic on stderr; allow/not_applicable = exit 0, empty stdout; never emit `"allow"`, D7), §6.3 step 1 (unlisted, missing or unknown modes → `deny owner-approval-unavailable`), §7.1 step 1 (no jq, no Python on the fast path; relevance pattern `(^|[^A-Za-z0-9_.-])(git|gh)([^A-Za-z0-9_.-]|$)`), §7.5 (stdin 1 MiB, command 64 KiB, wall-clock 5 s), §9 (≤1 KiB UTF-8, rule line from the module constant, summary without message text, file contents, environment values, full command or URL user info), §11, I5. The allowlist is a core constant; add a contract check that it equals the anchored `git-rails ask-capable modes:` line in `harness/claude/capabilities.md`.
- Constraints: Bash `set -uo pipefail`, header comment, `bash -n` clean; the 29 reason codes each have a `next` entry and a test. The `registry-error` next step is "fix or remove the invalid line in <registry path>" (owner decision; the setup script refuses to repair an invalid registry).
- Reason: the hook process boundary (stdin → exit status/stdout/stderr) is one component verified end-to-end through the real entrypoint.

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** entrypoint fast paths and runtime check; adapter mapping; permission-mode allowlist and drift check; diagnostics renderer and next-step table; stdin/command/wall-clock limits; `internal-error` catch-all; failure modes of §11; determinism (each case twice, byte-identical); `.ai/tasks/**` and `atomic-tests:` independence; end-to-end execution of the existing case table through the entrypoint.
- **Out of scope:** `hooks.json` registration and installer (T-08), deny fragment (T-09), contract docs (T-10).
- **Target files:** hooks/git-rails.sh, hooks/git_rails.py, tests/git-rails.sh, scripts/validate-contracts.sh

## Steps
1. Add failing end-to-end cases for AC-01 (missing registry exits 0 with no `python3` on `PATH`), AC-02 (no git/gh word exits 0 without starting Python; `git-rails.sh`, `.git/config`, `github.com` do not match), AC-09 (exit/stdout/stderr per decision; no output ever contains `"allow"`; ask-class case under missing, unknown and `bypassPermissions` modes → `deny owner-approval-unavailable`), AC-10 (four-line format, ≤1 KiB, `next` from the table, secrets in message/file/env/URL user info never printed), AC-11 (malformed JSON, unreadable registry, missing Python, injected core exception, git read timeout), AC-12 (byte-identical repeat; `.ai/tasks/**` and `atomic-tests:` changes do not alter decisions), stdin > 1 MiB, command > 64 KiB and wall-clock budget → limit/malformed codes; the allowlist drift check. Run and observe RED.
2. Implement `hooks/git-rails.sh`.
3. Implement the core `main`: bounded stdin, wall-clock budget, catch-all `internal-error`, a test-only fault-injection seam that cannot be triggered by event content alone.
4. Implement the adapter mapping and allowlist.
5. Implement the diagnostics renderer, summary sanitization and next-step table.
6. Run the full existing case table through the entrypoint; run focused and full suites; refactor while green.

## Acceptance Criteria
- Fast paths: with no registry file the entrypoint exits 0 with empty output even when `python3` is absent from `PATH`; a command without a `git`/`gh` word exits 0 without starting Python; `git-rails.sh`, `.git/config` and `github.com` do not trigger the prefilter.
- Protocol: deny → exit 2 with the diagnostic on stderr; ask → exit 0 with stdout exactly `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"<diagnostic>"}}` and the diagnostic on stderr; allow and not_applicable → exit 0 with empty stdout; no case prints `"allow"`; an ask-class case under a missing, unknown or `bypassPermissions` mode gives `deny owner-approval-unavailable`; the core allowlist equals the capability record line.
- Diagnostics: every deny/ask diagnostic has the four lines of §9, is at most 1 KiB, carries the `next` text for its reason code, and a secret placed in a commit message, a `-F` file, an environment value and URL user info never appears on stdout or stderr.
- Failure and determinism: malformed JSON, unreadable registry, missing Python, an injected core exception and a git read timeout give the §11 results; every case run twice gives byte-identical output; adding/removing `.ai/tasks/**` and changing `atomic-tests:` values changes no decision.

## Test Plan
- **Level:** contract (harness protocol fixtures), integration (end-to-end through `hooks/git-rails.sh` in disposable roots), unit (renderer and table completeness)
- **Scenarios:**
  - Each AC → its observable exit status, stdout and stderr.
- **Edge cases:** stdin exactly 1 MiB vs 1 MiB + 1, command exactly 64 KiB, non-UTF-8 input, `python3` 3.10 shim on `PATH`, registry present but empty, `cwd` relative or missing, `tool_name` `Edit`, diagnostic truncation at 1 KiB on a UTF-8 boundary.
