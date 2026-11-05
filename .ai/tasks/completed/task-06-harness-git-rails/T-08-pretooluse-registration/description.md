## Goal
`harness/claude/hooks.json` registers the git-rails PreToolUse handler for `Bash` with `"onFailure": "block"`, and `scripts/install-hooks.py` validates every manifest group against the handler that event declares, so installation, idempotence, foreign-hook preservation, ownership quotas, recovery and removal hold for the new entry exactly as for the logging handlers.

## Context
- Dependencies: T-01 (failure-mode fact), T-07 (entrypoint path)
- Constraints: spec §10.1 manifest (`matcher: "Bash"`, `type: command`, `command: bash`, `args: ["@ORCHESTRAIL_HOME@/hooks/git-rails.sh"]`, `timeout: 10`) plus `"onFailure": "block"` (the pinned harness offers a blocking failure mode — spec §10.1 requires it); §10.2 first bullet and the guarantee list. The installer stops hard-coding the logging handler and the `EVENTS` pair; the source check also requires `hooks/git-rails.sh` and `hooks/git_rails.py`. Logging groups stay exactly as today. Receipt schema changes belong to T-09 — this leaf keeps receipt `schema_version: 1` semantics for hook ownership. `scripts/sync.sh` keeps calling the installer unchanged.
- Reason: hook-manifest ownership is one component (manifest + per-event validation) with one AC cluster (AC-13, hook part).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** manifest entry; per-event expected-handler validation derived from the manifest itself with the existing strictness (one group per event, one handler, exact handler shape, placeholder substitution); event set from the manifest; source check; insertion, idempotence, foreign-hook preservation, exact multiset ownership, locking, atomic replacement, interrupted-replacement recovery, concurrent-edit protection and owned-only removal for the PreToolUse entry; `tests/hook-install.sh` extensions.
- **Out of scope:** `permissions.deny` handling and receipt v2 (T-09); hook behaviour.
- **Target files:** harness/claude/hooks.json, scripts/install-hooks.py, scripts/install-hooks.sh, tests/hook-install.sh

## Steps
1. Add failing `tests/hook-install.sh` cases: fresh install creates the PreToolUse `Bash` group with the resolved absolute entrypoint and `onFailure: block`; installing twice equals once; a foreign PreToolUse handler and foreign Bash group are preserved; removal deletes only the owned handler/group; malformed manifest variants (wrong handler, extra group, missing entrypoint in source) are rejected without writes; interrupted replacement recovers; concurrent user edit is not overwritten. Run and observe RED.
2. Add the manifest entry.
3. Replace the hard-coded expected handler and `EVENTS` with per-event validation from the manifest.
4. Extend the source check.
5. Run `bash scripts/validate-contracts.sh --hook-install-only`, the logging suites and the full suite; refactor while green.

## Acceptance Criteria
- Installing from a disposable source into a disposable home adds exactly one owned PreToolUse group `{"matcher":"Bash","hooks":[{"type":"command","command":"bash","args":["<source>/hooks/git-rails.sh"],"timeout":10,"onFailure":"block"}]}` alongside unchanged Stop/SubagentStop entries; a second install is byte-identical; foreign hooks and settings survive install and removal; removal deletes only owned entries; malformed manifests, malformed settings and a concurrent edit cause no partial write; every pre-existing `tests/hook-install.sh`, `tests/log-step-hook.sh` and `tests/hook-timing.sh` case still passes.

## Test Plan
- **Level:** integration (installer run against disposable homes and source trees)
- **Scenarios:**
  - AC examples → settings bytes and receipt contents as stated.
- **Edge cases:** existing user PreToolUse group with the same matcher, duplicate identical foreign handler (multiset quotas), numeric lexeme preservation in settings, missing `hooks` key, receipt from the logging-only install upgraded by re-install.
