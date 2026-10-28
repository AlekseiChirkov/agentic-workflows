# Owned user hook installation

## Goal
Sync installs and uninstalls only manifest-owned user hooks and exposes the minimal registry/capability scaffold without replacing existing deployment behavior.

## Context
- Dependencies: T-02.
- Constraints: preserve validated nonblocking logging, explicit attribution and private active correlation; read the parent solution design.
- Reason: one coherent owned user hook installation component with its own independently verifiable acceptance cluster.

## Scope
In scope: Sync installs and uninstalls only manifest-owned user hooks and exposes the minimal registry/capability scaffold without replacing existing deployment behavior.

Out of scope: cost/token schemas, git protection hooks, broad harness migration, historical telemetry mutation, automatic merges. Other leaves own their named components.

Target files: harness/claude/hooks.json, harness/claude/capabilities.md, harness/codex/capabilities.md, scripts/sync.sh, scripts/setup-new-project.sh, scripts/install-hooks.sh, tests/hook-install.sh. Paths may be refined after inspecting existing patterns; report additions explicitly.

## Steps
1. Freeze temporary-home lifecycle fixtures for installation, repetition, uninstall, unrelated settings, malformed settings, source paths with spaces and project registry gating.
2. Add minimal hook manifest and evidence-based capability declarations with verification date/runtime evidence and explicit unknown/unavailable semantics; hook support and workflow-step coverage remain separate declarations.
3. Implement manifest-owned settings merge and uninstall with exact handler/selector ownership receipts, serialized safe writes and preservation of all unowned settings and hook entries. A preexisting identical entry remains unowned; manually changed entries survive uninstall.
4. Wire user-level lifecycle into sync, embed capability declarations in deployed always-on instructions, and maintain a canonical absolute-path consumer registry from project setup.
5. Preserve all currently shipped harness deployment targets and document unavailable-dependency fallback without claiming the wider migration complete.
6. Run lifecycle fixtures and existing sync/setup validation.
7. Exercise the prepared ownership transaction before/after settings replacement,
   uninstall recovery, changed source paths and external settings edits. Preserve
   unmatched external edits and report unavailable coverage.

## Acceptance Criteria
- Given user settings with unrelated hook entries and settings, install twice and uninstall remove only entries owned by this manifest and preserve user data.
- Given registered and unregistered directories, only registered projects activate logging; setup records canonical project paths idempotently and source paths with spaces remain functional.
- Given absent dependencies or malformed user settings, installation preserves original settings and reports unavailable hook coverage; capabilities distinguish hook availability from observed step coverage.
- Given a source path change, malformed ownership receipt or user-modified installed entry, upgrade/uninstall follows the resolved ownership contract without deleting unowned data.

## Test Plan
- Level: integration, contract
- Scenarios:
  - Given user settings with unrelated hook entries and settings, install twice and uninstall remove only entries owned by this manifest and preserve user data. → assert the stated observable result in isolated executable fixtures.
  - Given registered and unregistered directories, only registered projects activate logging; setup records canonical project paths idempotently and source paths with spaces remain functional. → assert the stated observable result in isolated executable fixtures.
  - Given absent dependencies or malformed user settings, installation preserves original settings and reports unavailable hook coverage; capabilities distinguish hook availability from observed step coverage. → assert the stated observable result in isolated executable fixtures.
- Edge cases: empty/null inputs, canonical count boundaries, duplicates, invalid transitions, missing dependencies, concurrent delivery, paths with spaces, permission failures, no-mutation on rejection.
