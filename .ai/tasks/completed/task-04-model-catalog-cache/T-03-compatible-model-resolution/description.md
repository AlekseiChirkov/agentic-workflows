## Goal
Plan model readers and the optional helper preserve legacy plans and resolve requested models visibly against explicit active-session support without inventing actual execution identities.

## Context
- Dependencies: T-01 catalog interface and T-02 suitability policy.
- Constraints: Model (Claude)/Model (Codex) are optional; absent/empty means session default; legacy Model remains readable. Preserve unrelated Markdown, status, row order and columns. Helpers never spawn models.
- Reason: plan/request resolution is one interface independent of selection economics.

Off-limits: git/shared files, executing models, actual identity guessed from a plan, hidden substitution, complete harness migration, telemetry schema/price ledger.

## Scope
- **In scope:** robust header-based legacy/dual-column reading and optional bulk updates, empty cells, composite rows, active-provider precedence, explicit requested/resolved/unavailable/default/fallback/stop outcomes; actual identity is unknown unless supplied separately by execution evidence.
- **Out of scope:** workflow prose changes, provider switching, deployment and model spawning.
- **Target files:** scripts/model_plan.py, scripts/model-catalog.py, tests/model-plan.py, scripts/validate-contracts.sh.

## Steps
1. Freeze legacy/dual/empty/composite round-trip and unsupported-request fixtures as failing contract tests.
2. Implement column-name-based plan reading with a clear legacy/dual precedence rule; empty present provider cell means session default, not an old-column hidden override.
3. Implement optional dual-column writes preserving unrelated content, statuses and composite blanks, with malformed/ambiguous input rejected before any mutation.
4. Implement visible resolution using current actual request capability plus suitability; authorized declared conservative fallback or stop; report requested/resolved/actual separately and never execute anything.

## Acceptance Criteria
- Legacy Model-only, dual-column and absent/empty-model plans parse with documented precedence and explicit session default; reordered columns and composite rows preserve meaning.
- Bulk updates add optional Model (Claude)/Model (Codex) without changing unrelated sections, columns, row order or statuses; malformed/ambiguous plans remain byte-identical.
- Unsupported requests are surfaced with requested ID/reason and a suitable declared authorized fallback, otherwise stop; no unavailable planned ID is reported as resolved or actual execution.
- Without execution evidence actual remains unknown, even after successful requested-model resolution; the helper never spawns a model or reads telemetry history.

## Test Plan
- **Level:** unit, contract, integration.
- **Scenarios:** legacy/dual/empty plans → exact requests; unknown columns and composite rows → stable round-trip; unsupported planned candidate → visible suitable authorized fallback or stop; no execution evidence → actual unknown; invalid table/update → no mutation.
- **Edge cases:** duplicate IDs/columns, escaped pipes, malformed separator, missing columns, conflicting legacy/provider cells, unavailable default, stale availability, incompatible fallback, explicit empty provider cell and repeated writes.
