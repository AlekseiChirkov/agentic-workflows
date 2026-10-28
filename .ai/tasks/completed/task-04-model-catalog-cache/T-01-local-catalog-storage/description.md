## Goal
The optional local catalog helper validates versioned Markdown configuration, reports freshness deterministically, and replaces the catalog atomically only on explicit refresh.

## Context
- Dependencies: none.
- Constraints: Python 3.11+ standard library; no automatic network, provider APIs, model spawning or production defaults. Default path is ~/.config/orchestrail/model-catalog.md; allow explicit fixture paths and clock inputs.
- Reason: catalog persistence is one independently testable boundary.

Off-limits: shared knowledge, logs, user configuration outside isolated tests, real refresh research, deployment, monetary ledger, git writes.

## Scope
- **In scope:** one canonical structured payload with schema version/refreshed/evidence dates, required tier table (tier | anthropic model id | openai model id | relative cost), exact IDs, availability/context/tools/traits, separate capability evidence and price snapshot references; strict drift/vocabulary validation; inspect output; atomic refresh from an explicitly supplied candidate.
- **Out of scope:** candidate ranking, plan mutation, workflow rewrite, current real model list or prices.
- **Target files:** scripts/model-catalog.py, tests/model-catalog.py, scripts/validate-contracts.sh. Add a focused catalog mode to the validator and default-suite inclusion so tests are runnable through the runbook test command. Test dispatch wiring may accompany the RED test-only commit as executable test infrastructure.

## Steps
1. Define and test the observable helper/schema contract, using fictional clearly isolated fixtures with no provider calls.
2. Implement strict schema, dates, tiers/traits/identities and derived-table validation, preserving unknown prices/capabilities rather than making them zero/equal.
3. Implement clock-controlled inspection: below 14 days fresh, 14–30 dated notice, over 30 stale warning; missing/malformed/future dates and missing catalog report selection unavailable with session preservation.
4. Implement explicit --refresh candidate installation with same-directory atomic replacement, full validation before mutation and preservation of prior bytes on every rejected candidate or failed replacement; measure warm isolated lookup and wire focused/default checks.

## Acceptance Criteria
- Valid fixtures at ages 13, 14, 30 and 31 yield respectively fresh, dated usable, dated usable and stale usable; malformed/missing/future dates and missing catalog report unavailable with no network access or implicit creation.
- Missing/duplicate/unknown schema, tiers, traits, inconsistent tier table and invalid evidence are rejected; missing price remains unknown, not free; cost tiers do not assert equal quality.
- Without --refresh, inspection cannot write; explicit invalid/failed refresh preserves the previous catalog byte-for-byte; valid refresh atomically installs the fully validated candidate.
- A measured repeated warm deterministic lookup completes in under one second in an isolated fixture, without claiming live selection timing or savings.

## Test Plan
- **Level:** unit, integration, contract.
- **Scenarios:** freshness boundaries and invalid dates → exact statuses; schema and table drift → rejection; missing evidence → unknown/unavailable; explicit refresh success/failure → byte comparisons; lookup with network disabled → identical outcome; measured fixture → below one second.
- **Edge cases:** empty/invalid payloads, booleans as numeric values, duplicates, unknown version, missing dependencies, replacement failure, future dates, absent directories, repeated operations and isolated home/config roots.
