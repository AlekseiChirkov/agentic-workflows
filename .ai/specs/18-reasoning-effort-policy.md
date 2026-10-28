# Capability-aware reasoning effort by role and task

## Source

Workstream 7 of the owner's 2026-10-21 request: avoid unnecessary reasoning for
mechanical stages while preferring strong-first where expected rework makes it cheaper.

## Context & Problem

Baseline reviewed 2026-10-28.

Selection now has consistent scoring/availability guidance, but still recommends an
Implementer model through the existing live catalog (`workflows/pd-select-model.md → ## Instructions`).
The orchestrator spawns a separate Validator and preserves same-worker execution
checkpoints (`workflows/spec-run.md → ## Step 4 — Subtask loop`). No versioned role/stage
effort policy, supported-setting resolver or qualified cheaper default has been added.
Requested settings never prove applied effort or measured reasoning-token reduction.

## Goal

Choose supported effort conservatively by role, stage, complexity and risk, record the
actual configuration and allow evidence-based reduction without hidden quality loss.

## Scope

Effort policy, supported-setting registry integration, precedence/fallback, role-stage
overrides, conservative risk floors, telemetry and qualification.

## Out of Scope

Inventing unsupported flags, equating providers' effort labels, a learned model router,
automatic model migration, production cost/time caps, or promising reasoning-token
visibility when a harness does not expose it.

## Actors & Roles

The owner may explicitly pin effort. Discovery records task risk and defaults.
The orchestrator resolves supported settings before dispatch. Workers report execution
configuration where exposed. The evaluator qualifies reductions under 09.

## Terminology

Requested effort is an intended supported value. Effective effort is what the harness
accepts; observed actual effort is recorded only if exposed. A semantic policy class
is local intent, not a provider-independent numerical reasoning scale.

## Requirements

- **REQ-01** THE SYSTEM SHALL define an optional versioned policy keyed by role
  (orchestrator/Arbiter/Implementer/Validator), stage, complexity, risk, ambiguity and
  task kind. Mechanical inspections SHALL prefer deterministic helpers where sufficient;
  planning, uncertain architecture, critical invariants and complex review SHALL retain
  conservative model/effort floors.
- **REQ-02** THE SYSTEM SHALL declare model/harness-supported effort controls in one
  capability registry integrated with 04/13, with exact invocation syntax, evidence
  date and unknown/unsupported states. Different provider labels SHALL not be treated
  as equivalent or converted into fabricated reasoning-token budgets.
- **REQ-03** WHEN resolving effort, THE SYSTEM SHALL apply explicit approved owner/run
  override, approved task override, qualified role/stage policy, then the existing
  conservative harness default, subject to declared quality floors. A conflicting
  unsafe override SHALL be surfaced for decision, not silently lowered.
- **REQ-04** IF effort cannot be requested or verified, THEN THE SYSTEM SHALL use the
  documented suitable default without unsupported flags, record requested/resolved/
  observed values separately under 05 and mark unknown actual effort. The helper SHALL
  not substitute a different model to satisfy an effort setting without authorization.
- **REQ-05** WHEN switching stages or retrying, THE SYSTEM SHALL retain explicit
  policy provenance and avoid inheriting a cheap mechanical-stage effort into complex
  repair/review. Spec 19 owns any escalation decision; this spec resolves only its
  supported effort request.
- **REQ-06** THE SYSTEM SHALL preserve existing defaults until a cheaper effort profile
  passes the predeclared independent quality and accepted-result cost rule under 09.
  Deterministic policy tests may establish correct resolution but SHALL NOT be presented
  as model-quality evidence.
- **REQ-07** THE SYSTEM SHALL record total input/output, reasoning subset where exposed,
  cache effects, latency, failures, retries, review/escalation and API-equivalent total
  cost under 05. Reasoning tokens already in output SHALL never be double-charged;
  missing reasoning data SHALL not be equated to zero.
- **REQ-08** THE SYSTEM SHALL keep legacy plans valid, document policy disable/rollback
  and apply shared index gates G1–G8. No provider/harness network probe or paid model
  experiment SHALL run from ordinary validation or policy lookup.

## Data Model

Versioned policy entries: role/stage/task signals, semantic intent, exact supported
setting per model/harness, conservative floor, evidence/calibration reference and
fallback. Optional plan/task effort metadata must be additive; unspecified values
retain previous behavior. Per-request requested/resolved/actual values use 05.

## Contracts & Interfaces

Add optional effort fields to the existing selection/dispatch contracts and a
read-only resolver. Capability declarations own valid controls; policy entries reference
them. A dry-run resolution shows chosen model/effort, evidence and fallback with no
model invocation. It never claims a setting was applied before execution.

## Non-Functional Requirements

Offline resolution is deterministic for identical catalog/policy/capability inputs.
Zero provider calls occur during lookup/tests. Unsupported parameters are never sent.
All default changes are reversible without modifying canonical status history.

## Edge Cases & Failure Modes

Cover absent policy, unknown model version, unsupported effort, unavailable actual
effort, conflict with owner pin, higher-risk task, stage change, resumed worker,
catalog staleness and a cheap setting that increases retries. Preserve the suitable
conservative model/default when qualification is missing.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-03) Table-driven role/stage/risk fixtures choose the declared
  policy; critical/architecture cases retain floors and unsafe overrides are surfaced.
- [ ] **AC-02** (REQ-02, REQ-04) Supported controls are passed exactly; unsupported or
  unknown models receive no invented flag, no silent model change and honest metadata.
- [ ] **AC-03** (REQ-05) Stage/repair fixtures do not inherit inappropriate cheap effort;
  explicit escalation from 19 resolves through the same capability contract.
- [ ] **AC-04** (REQ-06, REQ-07) Unqualified profiles cannot become defaults. Synthetic
  reports include repair/review cost, reasoning subsets and missingness without
  double counting or claiming observed model-quality savings.
- [ ] **AC-05** (REQ-08) Legacy/no-policy behavior, dry-run and disable/rollback work,
  deterministic checks pass and zero paid calls occur during lookup/validation.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-03 | AC-01 |
| REQ-02, REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06, REQ-07 | AC-04 |
| REQ-08 | AC-05 |

## Risks

Lower effort can increase rework or latent defects; effort names may change.
Pin capability evidence and evaluate whole-result cost/quality rather than isolated
reasoning-token reductions.

## Assumptions

Some harnesses expose no effort control or actual setting. Honest defaults are a
supported result, not a failure requiring a different provider.

## Decisions

Retain current conservative defaults until qualification. Models and price snapshots
remain owned by 04/05; this feature does not duplicate those catalogs.

## Clarifications

2026-10-21: use every actually supported effort/model alternative in approved comparison;
no hard-coded preference for cheap-first or high effort across all roles.

## Open Questions

None blocking. Exact current control syntax is verified during implementation using
the installed harness and authoritative documentation; live margins need owner approval.

## Notes

Depends on 04, 05, 09, 15 and 16. Suggested slices: capability/schema; resolver;
dispatch/metadata; qualification guards; stage/fallback fixtures; docs.

## Readiness Checklist

Supported-value ownership, precedence, risk floors, truthful telemetry and acceptance
are explicit. Ready for Discovery; no default reduction is authorized by this spec.
