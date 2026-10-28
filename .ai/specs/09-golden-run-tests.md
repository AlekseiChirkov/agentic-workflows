# Offline regression checks, release goldens and independent strategy evaluation

## Source

ADR-0009 Decision 6; the owner's 2026-10-21 requirement to compare all execution
strategies and protect quality without treating a strong reviewer as ground truth.

## Context & Problem

Textual contract checks do not demonstrate actual task correctness. The original
golden proposal compared normalized artifacts but removed free-text evidence, and
"no network" did not distinguish offline application fixtures from the model transport.
Evaluation must independently assess behavior, architecture, TDD and cost.

## Current implementation baseline — 2026-10-28

Existing offline suites exercise producer, hook, installation, timing and workflow
instruction contracts (`tests/log-step.sh`, `tests/hook-workflow-contract.sh`,
`tests/hook-timing.sh`, `tests/workflow-instructions.py`). They are deterministic contract
checks, not model-driven task goldens or independent strategy comparisons. The fixture
set, golden runner, evaluation protocol and paid-run qualification specified here remain
pending; source text reductions do not establish model-quality or financial results.

## Goal

Provide deterministic local regression checks plus separately authorized model-driven
runs and fair strategy comparisons with independent quality and total-cost evidence.

## Scope

Synthetic fixtures, semantic/structural assertions, normalization, release-only golden
runner, independent task evaluation protocol, reporting and manual experiment gates.

## Out of Scope

Automatic paid runs during sync/CI, live PR publication, a third harness, a learned
router, or declaring an LLM review verdict a correctness oracle. Core golden execution
remains Claude-based; cross-harness comparisons may use explicitly supplied recorded
runs or separately approved supported adapters, not an assumed Codex CLI contract.

## Actors & Roles

Fixture authors define observable requirements; an evaluator independent of executor
and reviewer owns held-out checks and adjudication. The owner approves paid manifests
and resolves disputed acceptance. CI runs deterministic checks by default.

## Terminology

A golden checks workflow artifacts against a reviewed expectation. A quality evaluation
checks the actual result against independent criteria. A normalized match proves
neither functional correctness nor absence of missed defects.

## Requirements

- **REQ-01** THE SYSTEM SHALL provide ~five-file pure-Python/pytest fixtures
  `flat` (three leaves), `composite` (two children), `quick` and `bugfix`, with filled
  project context and offline application behavior. Fixture/assertion tests SHALL run
  without a provider CLI, credentials or any model/network call.
- **REQ-02** WHEN explicitly approved, `tests/run-golden.sh <case> <workflow>` SHALL copy
  an isolated fixture, invoke `claude -p` with the owner-decided Sonnet 5 baseline,
  allow-listed tools and no application network, and keep raw artifacts/evidence in
  ignored local output. Required provider transport is the sole intended network
  exception; actual sandbox capability SHALL be verified and documented. An unavailable
  pinned model SHALL stop the experiment rather than silently upgrade or substitute.
- **REQ-03** THE SYSTEM SHALL normalize volatile dates/hashes and prose only after
  extracting semantic assertions for statuses, protected fields, notes/findings,
  stop decisions, traceability and TDD evidence. Raw evidence SHALL be retained.
  A normalizer SHALL not erase a failed test, lost critical finding or forbidden edit.
- **REQ-04** THE SYSTEM SHALL compare normalized output with `tests/expected/<case>/`;
  mismatches SHALL return nonzero. `--update` SHALL generate a reviewable expectation
  change and never auto-accept it. Independent assertions SHALL verify task artifacts,
  test-before-implementation history, frozen RED tests, actual fixture behavior and
  architecture constraints, including deliberately seeded defects.
- **REQ-05** THE SYSTEM SHALL keep paid goldens release-only or explicitly approved
  manual experiments. Plain sync/validation/default CI SHALL run offline checks only.
  Manual-dispatch CI SHALL require explicit authorization and separately configured
  credentials; it SHALL not convert a subscription into unapproved API billing.
  Examples for 11 SHALL come only from synthetic fixture output.
- **REQ-06** WHEN evaluating alternatives, THE SYSTEM SHALL support a manifest for
  A strong-first, B cheap execution + strong verification, C strong planning + cheap
  execution, D adaptive model/chain routing, E multilevel verification and F hybrids.
  Every arm SHALL declare exact models/effort, context policy, reviewer policy, retry/
  escalation rules and selection evidence. Unsupported/unimplemented arms SHALL be
  marked unavailable or manually configured, never labeled measured.
- **REQ-07** THE SYSTEM SHALL compare the same initial revision/specification and
  independent acceptance criteria on anonymized owner-selected historical tasks,
  stratified by task type, complexity, risk, context and observability. It SHALL
  separate tuning/calibration tasks from held-out evaluation, record repetitions and
  randomized/counterbalanced order, and label warm/cold cache and cross-run reuse.
  No private code or task transcript SHALL enter committed fixtures.
- **REQ-08** THE SYSTEM SHALL score functional tests, architectural/invariant checks,
  hidden cases, human-adjudicated disagreements and defects found after completion.
  Critical/important seeded defects SHALL be detected by independent checks even if
  the reviewer says DONE. A reviewer cannot establish its own false-negative rate.
- **REQ-09** THE SYSTEM SHALL report independently accepted-result rate, severity of
  escaped defects, first-pass success, calls, iterations, repair/escalation frequency,
  latency and complete/partial API-equivalent cost under 05. It SHALL report sample
  counts and uncertainty, distinguish observed from simulated values, and avoid
  declaring equivalence from a nonsignificant small-sample result.
- **REQ-10** BEFORE a paid run, THE SYSTEM SHALL require an approved manifest naming
  maximum samples/repetitions, spend/time ceilings, maximum retries, critical-defect
  stop conditions, cancellation behavior and a predefined quality/cost decision rule.
  Missing approval/settings SHALL refuse model invocation while allowing offline checks.
  Experiment ceilings SHALL not become production budgets. A critical escaped defect
  SHALL halt the affected candidate arm pending owner review.
- **REQ-11** THE SYSTEM SHALL produce an evaluation template and deterministic scenario
  calculator using supplied probabilities/prices, label every scenario hypothetical,
  include planning/review/rework/escalation/tools, and locate break-even conditions.
  No model-success rates SHALL be invented from model branding or catalog cost bands.
- **REQ-12** THE SYSTEM SHALL apply shared index gates G1–G8 and publish instructions
  for baseline capture, blinding/adjudication, expectation review, safe cancellation,
  artifacts/retention, rollback and promotion. A cheaper default SHALL require the
  predeclared quality rule to pass and independently measured total-cost improvement.

## Data Model

Versioned experiment manifest: approval reference, tasks/base revisions/AC digest,
strata, split, arms/models/effort/policies, ordering/repetitions, cache conditions,
sample/time/spend ceilings and stop rules, evaluator, quality margins and decision rule.
Results join 05 request/span measurements to independent acceptance/failure labels;
raw output remains local, anonymized aggregates may be exported.

## Contracts & Interfaces

Offline fixture/assertion checks are distinct from a command that invokes models.
The runner supports a dry-run manifest showing intended calls and predicted scenario
costs without execution. Prediction is not a charge or a measured result.
Existing Sonnet 5 choice is historical owner policy, not an assertion of current
availability. Changing it requires an explicit approved baseline change.

## Non-Functional Requirements

Offline checks have zero model calls/network access. Repeated normalization of the
same raw corpus is deterministic. Model-driven output is never automatically made an
expectation. Failed/cancelled/partially measured runs remain in the report denominator
or are explicitly accounted for as censored observations.

## Edge Cases & Failure Modes

Cover missing CLI/model/key/approval, insufficient subscription limits, missing hidden
checks, contradictory human/LLM verdicts, duplicate usage, incomplete pricing, stale
context, contaminated holdout, network needed by provider, absent network enforcement,
early cancellation and failed expectation updates. Fail closed for paid execution,
not for ordinary offline validation.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-04) All four fixture/assertion cases run offline; mutation
  fixtures fail for GREEN-before-RED, changed frozen tests and broken invariants.
- [ ] **AC-02** (REQ-02, REQ-05, REQ-10) Mock provider tests prove that default sync/CI,
  missing approval and an unavailable pinned model cause zero model calls; the allowed
  manual path passes the exact approved model/options and enforces experiment stops.
- [ ] **AC-03** (REQ-03, REQ-04) Normalization is stable for harmless prose changes but
  cannot conceal a seeded failed test, dropped finding or prohibited state mutation.
- [ ] **AC-04** (REQ-06, REQ-07) Dry-run A–F manifests show identical task/AC/base inputs,
  separate tuning/holdout and cache conditions; unavailable arms are honestly labeled.
- [ ] **AC-05** (REQ-08, REQ-09) A synthetic reviewer-DONE/hidden-test-failed result is
  rejected independently; reports retain failed/cancelled cases, missing cost coverage,
  denominators and uncertainty.
- [ ] **AC-06** (REQ-11) Hand-calculated scenarios verify cheap-first wins, extra repairs
  erase savings, and strong-first wins; no scenario is described as observed.
- [ ] **AC-07** (REQ-12) Protocol and examples document paid authorization, decision
  rules, rollback and data hygiene. No paid run is necessary to accept the offline
  harness implementation; model-quality/savings claims remain pending actual evaluation.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01 | AC-01 |
| REQ-02, REQ-05, REQ-10 | AC-02 |
| REQ-03 | AC-03 |
| REQ-04 | AC-01, AC-03 |
| REQ-06, REQ-07 | AC-04 |
| REQ-08, REQ-09 | AC-05 |
| REQ-11 | AC-06 |
| REQ-12 | AC-07 |

## Risks

Artifact normalization can hide semantic defects; independent assertions precede it.
Repeated small task sets can overfit; keep a holdout and report uncertainty.
Independent review costs must be accounted for separately from production verifier
costs when comparing deployment economics.

## Assumptions

Historical tasks are available only after owner selection and anonymization.
A live baseline model may be unavailable; changing it is an explicit experiment
decision. No numerical quality margin or experimental budget has yet been approved.

## Decisions

Retain release-only goldens, manual CI authorization and synthetic examples from
ADR-0009. Clarify offline application behavior versus model-service transport.
All A–F strategies are candidates, not a predetermined cheap-first winner.

## Clarifications

2026-10-21: split deterministic harness acceptance from live strategy qualification.
Existing fixed subscriptions do not authorize an API key purchase or API charges.

## Open Questions

Before live evaluation: task sample, repetitions, currently available models, quality
non-inferiority margin, defect observation window and experiment ceilings. None blocks
implementation of the protocol and offline fixtures.

## Notes

Depends on 01, 13, 05 and 06. Suggested slices: fixtures/assertions; normalizer;
manual runner/guards; experiment manifests; reporting/calculator; docs/CI.
Spec 12 extends the composite fixture later; it is not a prerequisite of this harness.

## Readiness Checklist

All requirements have acceptance checks; paid and offline paths are separated;
independent quality, coverage, failure behavior and approval boundaries are explicit.
Ready for Discovery; live experiments remain unapproved.
