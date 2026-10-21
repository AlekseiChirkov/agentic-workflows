# Risk-aware verification and finding-led repair review

## Source

Workstream 5 of the owner's 2026-10-21 request: reduce repeated review cost without
hidden quality loss; a strong reviewer is evidence, not an absolute correctness oracle.

## Context & Problem

The current independent Validator receives task description, tests and the base-to-head
diff, without Implementer reasoning (`workflows/spec-run.md:204`). Atomic validation
also reloads full project context (`rules/phase-atomic-validation.md:10`). Findings and
NEEDS WORK currently stop the task (`workflows/pav-check.md:101`). This spec optimizes
verification inputs/evidence; spec 19 alone changes repair control flow.

## Goal

Pay for checks appropriate to actual risk and reuse only evidence that remains valid,
while preserving independent acceptance and adequate whole-change review.

## Scope

Verification plan, deterministic first level, conditional model review, review packet,
evidence identities, repeat-review scope and escalation to broader review.

## Out of Scope

Removing the Validator role, accepting solely because tests pass, automatic repair
policy (19), skipping required architecture/invariant checks, or assuming every strong
review is cheaper than implementation.

## Actors & Roles

Tools provide deterministic evidence. The independent Validator evaluates contract
and semantic/architectural correctness without executor reasoning. The orchestrator
assembles packets and preserves stops. The independent evaluator in 09 checks whether
the entire verification process misses defects.

## Terminology

A verification receipt binds result to actual inputs and environment.
An impact set includes changed code plus affected contracts, callers, tests and
invariants. Finding-led review still checks the remaining acceptance obligations.

## Requirements

- **REQ-01** THE SYSTEM SHALL create a verification plan from the unchanged task ACs,
  risk/criticality, interfaces and available deterministic commands. It SHALL identify
  which obligations tools can check and which need independent semantic/architecture
  review; coverage gaps SHALL remain explicit.
- **REQ-02** THE SYSTEM SHALL run applicable compile/type/lint/tests and structural
  checks before requesting semantic review when execution is safe. Required failing/
  missing checks SHALL not become pass by omission; a failure may be reviewed for
  diagnosis but SHALL not be closed as DONE.
- **REQ-03** THE SYSTEM SHALL keep three available levels: deterministic checks,
  eligible lower-cost semantic review and strong review for complex/critical/uncertain
  changes. The existing conservative review policy SHALL remain the default until
  independently qualified under 09. No level SHALL be skipped solely because a
  lower-level check passed, and a cost-band label SHALL not establish reviewer fitness.
- **REQ-04** WHEN preparing review, THE SYSTEM SHALL provide exact AC/invariant/
  off-limits obligations, base/head identities, full changed-file manifest, diff,
  relevant before/after code, interfaces/callers and test evidence using 14/17.
  A diff-only packet SHALL not be treated as sufficient when surrounding behavior or
  architecture matters. The Implementer's reasoning SHALL remain excluded.
- **REQ-05** WHEN reusing deterministic results, THE SYSTEM SHALL require identical
  effective source/test tree, command/arguments, dependency versions, environment/
  configuration and other declared inputs. Missing identity, dirty/untracked relevant
  changes or changed inputs SHALL invalidate the receipt. Relevant changes SHALL
  rerun the check even if a previous attempt was green.
- **REQ-06** WHEN reviewing a repair, THE SYSTEM SHALL supply prior findings, the
  previous reviewed tree, the new tree, repair diff and unresolved ACs. The Validator
  SHALL verify each finding plus regressions/impact; changed interfaces, shared
  invariants, scope or uncertain dependencies SHALL trigger wider/full review.
  A new reviewer SHALL receive sufficient original context rather than a receipt alone.
- **REQ-07** THE SYSTEM SHALL retain the canonical DONE/NEEDS WORK severity semantics
  and record reviewed scope, evidence receipts, findings, unresolved obligations and
  reasons for expansion. No shortened report may drop critical/important findings.
  Spec 19 consumes the verdict; this spec SHALL NOT auto-close or auto-repair failures.
- **REQ-08** THE SYSTEM SHALL attribute deterministic checks, AI review levels,
  repeated input, reruns, context expansion and missed defects to 05/09. It SHALL
  measure review versus execution cost on the same tasks instead of assuming review
  is always cheaper, and apply shared index gates G1–G8.

## Data Model

Verification plan: AC/invariant-to-check mapping, risk, level eligibility and gaps.
Receipt: tree/input digest, command, dependencies/environment digest, return status,
artifact references and coverage. Review record: base/head, impact scope, findings,
level/model, full-versus-incremental reason and independently evaluated defects.

## Contracts & Interfaces

Extend the atomic validation check and composite/final validation entry points without
changing their canonical status vocabulary. Consume 14 packets, 17 artifacts and 15
envelopes. A receipt is optional derived evidence; full re-execution/review remains the
fallback. Preserve original standalone NEEDS WORK stops until 19 explicitly opts in.

## Non-Functional Requirements

Every task AC has a declared verification owner/check or an explicit unresolved gap.
Receipts are content/environment-bound and cannot survive relevant input changes.
Reviewer independence is mandatory; no executor self-approval path is introduced.

## Edge Cases & Failure Modes

Cover green-but-wrong code, architecture drift, tests weakened after RED, unchanged
tree with different environment, dirty worktree, hidden dependency, lost artifact,
unresolved finding, reviewer switch, large repair and unknown impact. Expand/rerun when
uncertain; record unavailable checks rather than hallucinating results.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Fixture plans map all ACs and gaps; failing or unavailable
  mandatory tools prevent acceptance even if a simulated reviewer returns DONE.
- [ ] **AC-02** (REQ-03) Risk/eligibility fixtures retain strong/conservative review for
  uncertain or critical work; tool pass alone does not authorize skipping semantics.
- [ ] **AC-03** (REQ-04) Packets contain full obligation/change manifests and retrieve
  necessary interfaces; no executor reasoning enters the independent review input.
- [ ] **AC-04** (REQ-05) Identical-input receipts may be reused; source/test/environment/
  command/dependency changes, dirty relevant files or unknown identities force rerun.
- [ ] **AC-05** (REQ-06, REQ-07) Local repairs get finding-led review plus regression/
  impact checks; interface/invariant changes force expansion, all important findings
  survive compaction, and no failure closes automatically.
- [ ] **AC-06** (REQ-08) Seeded green-but-wrong and reviewer-missed defects fail independent
  09 checks; reporting separates execution/review/repair costs and documents full-review
  fallback/disable without claiming unmeasured savings.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03 | AC-02 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-06, REQ-07 | AC-05 |
| REQ-08 | AC-06 |

## Risks

Correlated executor/reviewer errors and incomplete impact analysis can escape review.
Use independent seeded/held-out checks, conservative expansion and later-defect tracking;
a stronger reviewer alone does not eliminate this risk.

## Assumptions

Some checks depend on machine/environment and cannot be reused safely. A full rerun is
acceptable when fingerprinting cost or uncertainty exceeds potential savings.

## Decisions

Keep independent validation, current correctness obligations and stop semantics.
Qualify lower-cost verification policies before promoting them as defaults.

## Clarifications

2026-10-21: incremental review is not just checking the reported fix; it also checks
acceptance coverage and affected behavior. Test receipts never authorize stale GREEN.

## Open Questions

None blocking. Live false-negative tolerances and reviewer arms belong in a 09 manifest.

## Notes

Depends on 09, 14, 15 and 17, including the checkpoint-envelope contract used here.
Suggested slices: coverage plan; receipts; review packets; repair impact expansion;
workflow integration; seeded checks and docs. Composite parallel review extends in 12.

## Readiness Checklist

Scope, independent ownership, reuse preconditions, expansion rules and acceptance are
explicit. Ready for Discovery; review cost advantage remains a hypothesis.
