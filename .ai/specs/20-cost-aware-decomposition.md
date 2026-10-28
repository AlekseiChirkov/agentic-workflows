# Cost-aware decomposition with complete acceptance coverage

## Source

Workstream 9 of the owner's 2026-10-21 request: reduce redundant leaf setup, planning
and review while retaining coherent scopes, architectural boundaries and low error rates.

## Context & Problem

Baseline reviewed 2026-10-28.

Each leaf uses its own Implementer and independent Validator
(`workflows/spec-run.md → ## Step 4 — Subtask loop`). The current decomposition workflow
already records classifier signals, dependency order, target ownership and coherent leaf
criteria (`workflows/pd-decompose.md → ## Instructions`); the workflow audit clarified
Type 3 re-slicing, inherited constraints and preservation of progressed subtasks.

No calibrated cost model or economic grouping adviser has been implemented. Tiny leaves
can repeat setup/review, while oversized leaves can increase rework; leaf count alone
remains neither a cost nor a quality metric.

## Goal

Choose coherent task boundaries using measured overhead and risk, with complete AC/
dependency/integration coverage and reusable architecture decisions.

## Scope

Decomposition signals, shared analysis contract, grouping/splitting criteria, dependency
DAG, overhead-aware candidate comparison, decomposition rationale and regression fixtures.

## Out of Scope

Automatically merging active reviewed tasks, changing a specification to make it easier,
minimizing leaf count irrespective of risk, top-level parallelism, new branch semantics
or a learned task-sizing model without calibration.

## Actors & Roles

Discovery identifies boundaries and creates the plan. An Arbiter resolves architectural
ambiguity. The model selector applies quality/availability floors. The orchestrator
executes the existing sequential stack; independent validation checks integration.

## Terminology

Fixed leaf overhead includes bootstrap, dispatch, bookkeeping and required review.
A coherent leaf has one verifiable outcome and a manageable impact scope.
A composite coordinates children but does not remove each child's TDD obligations.

## Requirements

- **REQ-01** THE SYSTEM SHALL map every specification AC, invariant and interface
  obligation to one or more leaves and an explicit integration check. It SHALL preserve
  ownership, required test levels, off-limits constraints and dependency readiness;
  no saving may be achieved by leaving an obligation unmapped.
- **REQ-02** THE SYSTEM SHALL identify shared architecture/interface decisions once,
  store their source/version in the reusable contract under 14 and reference them from
  related leaves instead of asking each executor to redesign the same interface.
  Unresolved cross-cutting decisions SHALL be resolved before dependent execution.
- **REQ-03** WHEN considering grouping, THE SYSTEM SHALL favor closely related,
  jointly verifiable changes with compatible target ownership/context and no need for
  independent checkpoints. It SHALL reject grouping across incompatible risk/quality
  floors, unrelated outcomes, mandatory approval boundaries or excessive context.
- **REQ-04** WHEN considering splitting, THE SYSTEM SHALL use architectural seams,
  independent acceptance outcomes, target-file/interface conflicts, context sufficiency,
  ambiguity, criticality and expected rework. It SHALL not create tiny leaves solely to
  assign a cheaper model or claim parallelism.
- **REQ-05** WHEN sufficiently reliable 05/09 calibration exists, THE SYSTEM SHALL
  compare candidate decompositions by total planning + per-leaf context/dispatch/
  execution/review + integration + expected repair/escalation cost and wall time.
  It SHALL report the calibration sample/cohort, uncertainty and quality floors.
  Unknown probabilities/costs SHALL stay unknown; an uncalibrated plan SHALL use
  conservative structural heuristics, not fabricated USD savings.
- **REQ-06** THE SYSTEM SHALL record chosen grouping/splitting rationale and plausible
  rejected boundaries in `Decomposition Decisions`, exact dependencies in an acyclic
  plan, context/quality signals for 04/18 and integration ownership. The plan SHALL
  distinguish estimated calls/cost from observed usage.
- **REQ-07** THE SYSTEM SHALL preserve canonical atomic/composite types and the existing
  top-level stack. Parallel safety, when later enabled by 12, SHALL require its separate
  independence checks; fewer leaves or shared analysis SHALL not imply parallel safety.
  No partially executed task SHALL be regrouped silently on resume.
- **REQ-08** THE SYSTEM SHALL evaluate decomposition on matched tasks under 09, include
  repeated planning/context/review and later integration defects in 05, and apply shared
  index gates G1–G8. It SHALL document conservative fallback, replan authorization and
  how to disable cost-aware advice without losing the canonical task plan.

## Data Model

Additive decomposition rationale: AC-to-leaf/integration mapping, target/interface
ownership, shared architecture contract hash, dependency edges, risk/context signals,
candidate boundaries, structural estimate or calibration reference and uncertainty.
Existing task/plan formats remain readable; advisory economic fields are optional.

## Contracts & Interfaces

Extend the existing decomposition workflow and subtask classifier at their single
canonical homes after 13 renames. Model/effort resolution remains 04/18; pricing is 05.
The plan is frozen according to the existing Discovery contract. A changed assumption
during execution uses the established amendment/replan process, not automatic regrouping.

## Non-Functional Requirements

One hundred percent of declared AC IDs are mapped; dependency cycles and duplicate/
conflicting target ownership are detected. No compulsory leaf-count target is added.
Deterministic checks require no model calls or shared-log reads.

## Edge Cases & Failure Modes

Cover one tiny task, many related mechanical edits, a high-risk shared interface,
large context, missing calibration, conflicting ownership, cyclic dependencies,
changed acceptance after Discovery and partially completed composite. Prefer a
reviewable conservative plan when financial evidence is weak.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Fixture AC/interface maps are complete; several related
  leaves reference one fresh architecture contract and cannot execute while a shared
  decision remains unresolved.
- [ ] **AC-02** (REQ-03, REQ-04) Tiny-related-change and architecture-seam fixtures choose
  coherent grouping/splitting; approval/risk/context conflicts prevent unsafe grouping.
- [ ] **AC-03** (REQ-05) Synthetic calculations show both excessive fragmentation and
  oversized rework can be more expensive; absent calibration produces explicit
  structural advice with no invented success rate or monetary saving.
- [ ] **AC-04** (REQ-06, REQ-07) Plans have complete rationale, an acyclic dependency map
  and preserved stack/types; a resumed partially executed task cannot silently change
  leaf ownership or declare parallel-safe.
- [ ] **AC-05** (REQ-08) Offline integration-defect/coverage fixtures pass, matched-run
  reporting includes setup/review/rework, and documentation provides disable/replan
  paths without claiming that fewer leaves guarantee lower cost or equal quality.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06, REQ-07 | AC-04 |
| REQ-08 | AC-05 |

## Risks

Grouping may hide integration failures; splitting may multiply bootstrap and reviews.
Measure whole-result economics and independently verify acceptance/invariants rather
than choosing a global minimum or maximum leaf size.

## Assumptions

Historical calibration may be unavailable or too small; structural heuristics remain
valid advisory behavior. Feature-sized specs can decompose into the existing allowed
task types without forcing a single atomic implementation.

## Decisions

Preserve architectural boundaries, traceability and explicit integration checks.
Optimize decomposition locally; do not replace the task hierarchy or stack model.

## Clarifications

2026-10-21: reuse architecture analysis, not mutable progress or executor transcripts.
If strong planning amortized across leaves wins, it is a valid strategy C result.

## Open Questions

None blocking. Useful calibration strata and live task sample require later evaluation.

## Notes

Depends on 04, 05, 09, 14, 15 and 16. Suggested slices: coverage/decision schema;
group/split heuristics; optional calibrated comparison; workflow/classifier integration;
dependency fixtures; evaluation/docs. Spec 12 adds parallel execution later.

## Readiness Checklist

Scope, coherent boundary criteria, complete coverage, calibration limits, compatibility
and acceptance are explicit. Ready for Discovery; no fixed savings target is invented.
