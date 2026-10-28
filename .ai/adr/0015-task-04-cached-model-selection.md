# ADR-0015: Decisions for Task 04 — Cached model selection

## Status

Accepted

## Date

2026-10-28

## Related Task

- Task: .ai/tasks/completed/task-04-model-catalog-cache
- Related pull requests: #31, #32, #33, #34, #35, #36
- Related files: scripts/model-catalog.py, scripts/model_selection.py, scripts/model_plan.py, workflows/pd-select-model.md

## Summary

Use optional deterministic local helpers for a versioned catalog, conservative selection and compatible plan resolution. Keep refresh explicit and model execution outside the helpers.

## Context

At base revision 2191650 the selector required live research on every call and forbade persistence. Logging declarations do not establish model-request support (harness/codex/capabilities.md:1; harness/claude/capabilities.md:1). The owner explicitly selected this spec before the wider harness migration; ADR-0013 Decision 2 provides a narrow-scaffold precedent without claiming that migration complete.

## Decisions

### Decision 1: Optional cache and explicit evidence

**What was decided:** Keep a user-owned versioned catalog and checked derived tier table. Explicit refresh validates a complete candidate before atomic replacement. Filter declared availability, tools, context, owner constraints and independent quality before economics. Missing evidence preserves a suitable stronger/session model or stops an explicit unsuitable request. Requested, resolved and actual identities remain distinct.

**Why:** Offline fixtures can prove schema, exact score boundaries, compatibility, atomicity and lookup latency. Names and price bands do not prove capability or availability.

**Alternatives:** Instructions alone cannot enforce these contracts. A routing service adds a mandatory runtime and exceeds the approved scope.

**Consequences:** Standard-library helpers never browse or spawn models. The explicitly refreshed workflow owns research. No real initial catalog, new production default, paid comparison, global deployment or broader harness migration is included. Current caller-supplied capability evidence supports this narrow feature. Price snapshots and curated evaluation exports keep their separate owners.

**Related files:**
- scripts/model-catalog.py
- scripts/model_selection.py
- scripts/model_plan.py
- workflows/pd-select-model.md
- docs/MODEL-CATALOG.md

### Decision 2: Quality evidence precedes qualified economic comparison

**What was decided:** Map all seven integer task signals to a bounded ordinal quality floor from 1 to 5. Sensitive categories require floor 5. Filter current support, context, tools, owner limits and traits before economics. A suitable default changes only when qualified comparable expected-total-cost intervals establish a cheaper correct-result option. Price snapshots never establish capability or equivalent-task cost.

**Why:** Cost bands and token prices do not establish task success. Missing or conflicting evidence must not silently downgrade a suitable baseline.

**Alternatives:** Price-first routing and uncalibrated success probabilities were rejected. A learned router and paid comparisons remain outside this delivery.

**Consequences:** Capability remains unknown without source-supported evidence. Current requestability must be observed for every invocation, independently of catalog age. Comparative evidence and monetary definitions keep their existing separate owners.

**Related files:**
- scripts/model_selection.py
- docs/MODEL-CATALOG.md
- tests/model-selection.py

### Decision 3: Additive plan intent and observed execution identity

**What was decided:** Read optional provider columns by header, falling back to legacy Model only when the active provider column is absent. Present-empty cells request the session default. Adding columns to populated legacy rows requires explicit migration values. Resolve exact requested identities or a declared authorized independently suitable fallback; otherwise stop. Actual identity requires separate current-day matching execution evidence with caller-owned provenance.

**Why:** An unavailable planned ID must never be reported as executed, and an additive format must not silently erase legacy intent or change unrelated Markdown.

**Alternatives:** Positional columns, implicit cross-provider migration and hidden substitution were rejected. Receipt authentication and telemetry schema changes belong to their existing owners.

**Consequences:** Helpers remain pure or explicitly atomic and never spawn models. Leaf recommendations govern Implementers; task-wide Arbiter and independent Validator workers retain distinct session-default roles. Model override limitations never authorize inline Orchestrator implementation.

**Related files:**
- scripts/model_plan.py
- rules/workflow-reference.md
- workflows/spec-run.md
- tests/model-plan.py

### Decision 4: Resolve installed guidance from the verified source checkout

**What was decided:** Installed callers use the same configured or already-verified source root for helper siblings and the on-demand guide. A small read-only canonical preflight checks helper and guide schema/rubric availability. Never infer that root from CWD or installed relative links. Missing guidance reports selection unavailable and preserves inputs.

**Why:** Sync installs each workflow as a separate SKILL.md without packaging the source docs beside it. Repository-relative links alone were unreachable from that layout.

**Alternatives:** Copying a second documentation package into global skills or adding a mandatory runtime was rejected as unnecessary deployment scope. Source-relative links remain conveniences for source readers.

**Consequences:** ORCHESTRAIL_HOME remains the configured source selector; SOURCE_ROOT is only an invocation-local resolved path. Temporary installed-layout fixtures cover both supported skill layouts, decoy working directories, paths with spaces and missing guide sections.

**Related files:**
- rules/workflow-reference.md
- workflows/pd-select-model.md
- docs/MODEL-CATALOG.md
- tests/model-workflow.py

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

Instructions alone and a mandatory routing service, for the reasons above.

## Implications for Future Work

Preserve legacy plans and optional columns. Future harness declarations may supply explicit availability evidence; unknown remains unavailable. Cheaper-default promotion requires separately approved independent comparison. Do not introduce another price ledger or direct shared-log reader.

## Verification

All original leaves and the final equivalent-wording validation fix passed separate independent validation. Final committed tip 41b627cb8910570178a32e587bf11d2ba67f84d5 passes the complete offline regression: 594 checks, 0 failures, 2 optional private-pattern skips. The focused gate passes 87 model tests plus unchanged general instruction contracts. Frozen test methods and final repair test bytes remain intact. Independent formal contract review passes 21/21; no critical or important finding remains open. One optional guide example-verification improvement is deferred, with exact product preservation already covered.

The selector is 1,017 words. 100 warm isolated fixture lookups remain below one second. The live 60-second selection target, model quality and savings remain unmeasured. Syntax, mandatory annotations/function bounds and whitespace checks pass; shellcheck is unavailable. No deployment, real initial catalog, provider/paid comparison or production-default change occurred. Execution and pre-final task artifacts passed 17 and 20 checks respectively; final reconciliation artifacts pass 21 checks with zero failures or skips. All six related PRs are ready for review.

## References

- Task: .ai/tasks/completed/task-04-model-catalog-cache/state.md
- Related documents: .ai/specs/completed/04-model-catalog-cache.md; .ai/specs/README.md; ADR-0009 Decision 6; ADR-0013 Decision 2
