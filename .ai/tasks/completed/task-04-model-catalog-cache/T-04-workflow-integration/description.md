## Goal
The compact selector and all plan consumers use the cached catalog and visible capability-based resolution, with offline drift checks and an operational guide.

## Context
- Dependencies: T-01 cache, T-02 selection and T-03 plan resolution contracts.
- Constraints: workflow at most 1,500 words; existing single/bulk invocation compatible; --refresh is the only browsing path; use actual helper interfaces and on-demand reference; no deployed configuration changes.
- Reason: the executable instruction interface and its documentation/gates form one verifiable caller contract.
- Coverage clarification: a read-only consumer audit identified decomposition preservation, design staleness, discovery consistency and the quickstart as additional readers. The canonical plan-column definition belongs in workflow-reference; do not duplicate it in workflow-globals.

Off-limits: actual model/provider calls, paid evaluations, initial real catalog, home configuration, deployment, global skill copies, full harness migration, price ledger, guessed measurements, shared files or git writes.

## Scope
- **In scope:** compact pd-select-model with explicit refresh research/validated install and fallback; canonical optional plan columns and legacy compatibility; capability-aware spec-run/pe-execute/phase-atomic-execution readers; current operating docs and fixture gates. Refresh failure retains prior catalog. Clarify ownership, trait migration, calibrated evidence, rollback/disable and timing limits.
- **Out of scope:** full reference generation, helper spawning, global harness deployment, real model list/prices, comparative evaluation.
- **Target files:** workflows/pd-select-model.md, workflows/spec-run.md, workflows/pe-execute.md, workflows/phase-atomic-execution.md, rules/workflow-reference.md, workflows/pd-decompose.md, workflows/pd-design.md, workflows/pd-finalize.md, docs/MODEL-CATALOG.md, docs/USAGE.md, docs/SPEC-RUN-QUICKSTART.md, docs/README.md, workflows/PIPELINE.md, tests/model-workflow.py, tests/workflow-instructions.py, scripts/validate-contracts.sh. Update other existing model-column readers only when targeted search proves necessary and record the scope delta.

## Steps
1. Freeze failing instruction/word-count/reachability/legacy compatibility checks tied to observable caller contracts; preserve unrelated instruction assertions.
2. Replace the live-every-run workflow with cached lookup, dated notices, session-preserving unavailable behavior, explicit --refresh research and atomic install; reference detailed rubric/schema/trait migration on demand.
3. Update canonical optional columns and actual plan consumers to use current support, visible requested/resolved/default/fallback/stop outcomes and unknown actual identity absent execution evidence.
4. Write the on-demand guide and update derived operating/reference docs; integrate all isolated suites into default/focused validation, run appropriate checks and document measured fixture latency versus unmeasured live targets.

## Acceptance Criteria
- Selector contains at most 1,500 words and no routine live lookup/no-cache contract; existing single/bulk invocation works, --refresh alone authorizes research, failures preserve prior catalog, unavailable evidence preserves current/session model visibly.
- All relevant plan readers accept legacy, dual and missing columns, capability-filter before requesting, surface unsupported requests/fallbacks, and never claim planned identity as actual execution.
- Offline default/focused suites validate schema drift, score boundaries, monotonicity, plan compatibility and workflow reachability; no suite calls a provider, reads real user catalogs/logs or runs paid comparisons.
- Guide documents refresh/rollback, age/error policy, independent quality versus price bands, trait migration, uncertainty, requested/resolved/actual identities, telemetry/calibration ownership, shared gates and measured fixture versus live 60-second target without asserting unmeasured savings.

## Test Plan
- **Level:** contract, smoke, integration.
- **Scenarios:** instruction and word-count validation → cache/refresh/fallback branches reachable; all model-plan consumer fixtures → compatibility and visible resolution; broken canonical/schema/reader references → gate failure; actual public helper examples with isolated fictional data → documented output.
- **Edge cases:** missing helper/catalog, legacy columns, unsupported request/fallback, overlong selector, malformed/future date, failed refresh, unavailable price/calibration data and no network/provider tooling.
