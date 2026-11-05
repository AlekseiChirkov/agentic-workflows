## Goal
`harness/claude/capabilities.md` carries a verified `git-rails` capability section and `harness/codex/capabilities.md` declares `git-rails: none (textual rules only)`, both pinned by contract checks in `scripts/validate-contracts.sh`.

## Context
- Dependencies: none
- Constraints: spec 06 §6.2, §6.3 step 1, §10.1, §10.3, §10.4 (capabilities rows), §13; section fields follow spec 13 §7.2 (name, state `yes|no|unknown`, verified runtime version, date, evidence URL, limitations). Facts must come from the official Claude Code documentation for the locally pinned version (`claude --version`); Discovery read https://code.claude.com/docs/en/hooks, /permissions and /permission-modes on 2026-11-03 for 2.1.317 — re-confirm, do not copy blindly. The existing logging record above the new section is preserved byte-for-byte.
- Constraints: the ask-capable permission-mode allowlist is one anchored line (`git-rails ask-capable modes: <comma-separated>`) so the core constant can be drift-checked later. List only modes the docs show prompting a human and never auto-approving (Discovery found: `default`, `auto`).
- Reason: spec §14 step 2 requires the harness facts to be recorded before any adapter code is written; every later leaf depends on these facts.

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** confirm and record: event `PreToolUse`, tool `Bash`, pinned version and date, source URLs; exit/JSON protocol (deny = exit 2 + stderr; ask = exit 0 + `hookSpecificOutput` JSON; allow never emitted); `permission_mode` values and the ask-capable allowlist; deny-rule match semantics (exact `Bash(x)` vs prefix `Bash(x *)`/`Bash(x:*)`, compound-command handling, precedence over hook output); failure-mode behaviour (`onFailure: "block"`, timeout units); residual risks X1–X10. Codex declaration line. Contract checks for both files.
- **Out of scope:** hook code, manifest, installer, `rules/git-flow.md`.
- **Target files:** harness/claude/capabilities.md, harness/codex/capabilities.md, scripts/validate-contracts.sh

## Steps
1. Run `claude --version`; read the official hooks, permissions and permission-modes pages; note every fact listed in Scope with its URL. If ask decisions cannot reach a human in any interactive mode → stop and report (spec §14 step 2).
2. Add failing contract checks to `scripts/validate-contracts.sh` (`check "<desc>" "$(… && echo pass || echo '<reason>')"` form, anchored to definition lines) for every required field of the Claude section, the anchored allowlist line, each residual-risk ID X1–X10, and the exact Codex line. Run them and observe failure.
3. Append a `## git-rails` section to `harness/claude/capabilities.md` with the spec 13 §7.2 fields and every Scope fact; keep the existing logging text unchanged.
4. Add `git-rails: none (textual rules only)` to `harness/codex/capabilities.md`.
5. Run the new checks and the full `bash scripts/validate-contracts.sh`.

## Acceptance Criteria
- The new checks fail on the pre-change files and pass after: the Claude section states state `yes`, the pinned runtime version, a verification date, at least one official evidence URL, deny = exit 2 with stderr, the ask JSON shape with `permissionDecision`/`permissionDecisionReason`, "allow is never emitted", the anchored ask-capable modes line, Bash deny-rule match semantics (exact vs prefix), the failure-mode option and timeout unit, and residual risks X1–X10 each by ID.
- `harness/codex/capabilities.md` contains the exact line `git-rails: none (textual rules only)` and its check passes.
- The pre-existing logging capability text in both files is unchanged (diff shows additions only) and every pre-existing check still passes.

## Test Plan
- **Level:** smoke (contract checks in `scripts/validate-contracts.sh`, the repository's validating tool)
- **Scenarios:**
  - Claude section fields → each named check passes after, fails before.
  - Codex line → exact-line check passes after, fails before.
  - Preservation → `git diff` of both files shows only added lines; full suite has zero failures.
- **Edge cases:** missing single field (each check is independent), duplicate section (check counts exactly one), allowlist line with unknown mode names.
