## Goal
`harness/claude/permissions.json` holds only R01/R06 deny-class Bash patterns, and the installer merges them into `permissions.deny` with receipt `schema_version: 2` `owned_permissions`, migrates version-1 receipts on the next install, and removes only owned deny strings.

## Context
- Dependencies: T-01 (recorded deny-pattern match semantics), T-08 (generic manifest validation)
- Constraints: spec §10.2 (receipt v2, v1 readable and migrated, owned-only removal, all existing guarantees), §10.3 (shape `{"permissions":{"deny":[…]}}`; R01/R06 only, D8; none matches a legitimate command such as `git add .gitignore`), AC-13, AC-14. The fragment is defense in depth; the hook stays authoritative. Fixtures test patterns under the semantics recorded in `harness/claude/capabilities.md` (exact `Bash(x)`, prefix only for `Bash(x *)`/`Bash(x:*)`); use exact forms only unless a prefix form is proven never to match a legitimate command.
- Reason: permission ownership is a second, independently testable installer component with its own AC cluster (AC-14 + the deny part of AC-13).

Off-limits: no writes to the real `~/.claude`, `~/.codex`, `~/.config/orchestrail` or any project registry; no network access in the hook or its tests; the hook never reads `.ai/tasks/**`; no spec-12 child-branch deletion verifier; no RED-set/GREEN protection; no Codex hook; no edits to deployed copies; nothing is installed on this machine; Stop/SubagentStop logging behaviour and its `"onFailure": "continue"` stay unchanged; the spec files under `.ai/specs/` are not edited; no shared knowledge file (`.ai/memory/*`, `.ai/adr/*`, `plan.md`) is written by the worker — return deltas.

## Scope
- **In scope:** the fragment file; an offline matcher in the tests implementing the recorded semantics; positive/negative fixtures per pattern; installer read/validate of the fragment; `permissions.deny` merge preserving foreign strings and order; receipt v2 with `owned_permissions` (exact multiset, like handlers); v1 receipt read and migration; removal; malformed fragment/settings and concurrent edit → no partial write.
- **Out of scope:** hook behaviour; manifest handlers (T-08).
- **Target files:** harness/claude/permissions.json, scripts/install-hooks.py, tests/hook-install.sh

## Steps
1. Add failing cases: fragment contains only R01/R06 patterns (`Bash(git add -A)`, `Bash(git add --all)`, `Bash(git add .)`, `Bash(git commit -a)`, `Bash(git commit --all)` or the confirmed set); each pattern has a matching positive and a non-matching negative fixture; none matches `git add .gitignore`; install adds owned deny strings and writes a v2 receipt; a foreign deny string identical to an owned one is preserved by quota; a v1 receipt migrates; removal leaves foreign strings; malformed fragment/settings and concurrent edit cause no write. Run and observe RED.
2. Create the fragment.
3. Implement fragment loading and validation.
4. Implement deny merge and `owned_permissions` ownership with v2 receipts.
5. Implement v1 → v2 migration and owned-only removal.
6. Run `--hook-install-only` and the full suite; refactor while green.

## Acceptance Criteria
- The fragment parses as `{"permissions":{"deny":[…]}}`, every entry is an R01/R06 pattern, each has a positive and a negative fixture under the recorded semantics, and no entry matches `git add .gitignore`; installing twice equals installing once; foreign deny strings are preserved; the receipt is `schema_version: 2` with `owned_permissions`; a version-1 receipt is read and migrated on the next install; removal deletes only owned deny strings and handlers; a malformed fragment, malformed settings and a concurrent edit cause no partial write; all pre-existing installer and logging suites pass.

## Test Plan
- **Level:** integration (installer against disposable homes), unit (offline matcher fixtures)
- **Scenarios:**
  - AC examples → settings bytes, receipt contents and fixture outcomes as stated.
- **Edge cases:** `permissions` key absent / `deny` absent / `deny` not a list, user `allow` list untouched, duplicate owned strings across reinstall, prepared-state receipt from v1 during recovery.
