# Bounded local repairs and explicit model escalation

## Source

Workstream 8 of the owner's 2026-10-21 request: preserve correct work, use concrete
review feedback, and prefer strong execution immediately where its expected total
cost is lower than cheap execution plus repair.

## Context & Problem

Baseline reviewed 2026-10-28.

NEEDS WORK still stops the atomic/run path and preserves branch/commit evidence
(`workflows/spec-run.md → ## Step 4 — Subtask loop`,
`workflows/pav-check.md → ## Instructions`). Task-level approved validation fixes and
quick bugfix repairs are separate existing paths; neither implements this proposed
per-leaf bounded retry policy. The workflow audit improved resume and evidence handling
without enabling automatic model escalation or resetting failure stops.

## Goal

Offer an opt-in, bounded repair path for clearly local defects, with independent
revalidation, preserved evidence and prompt escalation or owner stop when appropriate.

## Scope

Repair eligibility/classification, correction contract, retry state, progress checks,
model/effort resolution, escalation, independent recheck and interruption recovery.

## Out of Scope

Automatic scope expansion, hiding critical findings, weakening frozen RED tests,
unlimited retries, routine production spend/time caps, automatic approval of external
actions, or default activation of cheap-first execution without qualification.

## Actors & Roles

The independent Validator produces findings. The orchestrator determines policy/
eligibility and owns shared state/git. The Implementer applies the smallest sufficient
repair. The Arbiter/owner resolves architecture, invariant and intent ambiguity.

## Terminology

A local repair changes code within the existing approved task contract.
Escalation selects an explicitly authorized stronger execution configuration or hands
the decision to the owner; it never means silently accepting a failed task.

## Requirements

- **REQ-01** THE SYSTEM SHALL retain the current stop-on-NEEDS-WORK behavior by default.
  An explicit run policy such as `--repair-policy bounded-local` SHALL opt in only after
  the changed stop contract is recorded in an implementation ADR. Standalone validation
  without that policy SHALL still stop and surface findings.
- **REQ-02** WHEN classifying failure, THE SYSTEM SHALL distinguish local implementation
  defects, missing/incorrect tests, missing context, infrastructure/tool failure,
  architecture/contract disagreement and forbidden-scope/invariant violations.
  Ambiguous intent, security/data-integrity critical findings, off-limits changes,
  weakened RED evidence and conflicting architecture SHALL stop for the existing
  Arbiter/owner decision; they SHALL NOT enter an autonomous cheap repair loop.
- **REQ-03** WHEN repair is eligible, THE SYSTEM SHALL provide a correction contract
  with finding IDs, affected ACs, reproduction/evidence, expected behavior, constrained
  files/interfaces, frozen test digest and required checks. It SHALL preserve verified
  correct code and avoid whole-task regeneration unless an explicit redesign is approved.
  Reviewer feedback SHALL not override the original specification.
- **REQ-04** THE SYSTEM SHALL allow at most one local repair attempt on the current
  model and at most one explicitly authorized stronger-model attempt per leaf within
  one bounded-local policy episode. Each attempt SHALL get an independent verdict.
  Repeated findings, no progress, new important defects, budget-provider termination
  or uncertainty about repair feasibility SHALL skip further cheap attempts.
- **REQ-05** WHEN considering repair versus immediate strong execution, THE SYSTEM
  SHALL use available qualified task-class evidence for execution, verification,
  success/repair and escalation cost under 05/09. If that evidence is absent, it SHALL
  retain the suitable conservative/strong path rather than invent probabilities.
  An authorized stronger candidate may be chosen immediately when expected total
  correct-result cost is lower. A high API price alone SHALL not force cheap execution.
- **REQ-06** WHEN escalating, THE SYSTEM SHALL verify availability/quality floors in 04,
  resolve supported effort in 18, record requested/resolved/actual model separately
  and give a new executor sufficient original contract/context plus unresolved findings.
  Missing authorized strong models SHALL stop visibly; no silent substitution.
- **REQ-07** WHEN repair changes behavior or adds a regression case, THE SYSTEM SHALL
  preserve test-first order, keep frozen RED tests immutable unless the established
  amendment/owner process authorizes correction, and commit tests before corresponding
  implementation. It SHALL rerun affected deterministic checks and apply independent
  scoped/full re-review under 16 before closure.
- **REQ-08** THE SYSTEM SHALL persist attempt/finding lineage and last verified tree
  through 15 envelopes with one shared-state writer. Resuming SHALL not reset counters
  to bypass the bound. Dependent leaves SHALL remain blocked until the current leaf
  is reviewed; terminal failure SHALL preserve all branches, commits and findings.
- **REQ-09** THE SYSTEM SHALL attribute repair/context/review/escalation costs and
  progress to 05, apply shared index gates G1–G8, and document opt-in, stop reasons,
  disable/resume and rollback. Attempt bounds are control-flow safeguards, not
  production USD/time caps; a provider limit SHALL not be evaded by account switching.

## Data Model

Additive policy/attempt record: episode ID, leaf/base/contract hash, executor/model/
effort request, finding IDs, classification, attempt counter, prior/next tree,
frozen-test hash, progress, verification receipt and outcome. Existing statuses stay
canonical; additional attempt data must be protected from destructive compression.

## Contracts & Interfaces

Extend `spec-run` and atomic validation handoff only for explicitly enabled policy.
Canonical NEEDS WORK remains a failure verdict. No dependent task starts above it.
Use 14 correction packets, 15 envelopes, 16 verification and 18 effort resolution.
Only the orchestrator applies state/git effects; worker retries do not own shared state.

## Non-Functional Requirements

At most two model repair attempts per bounded-local episode: one local plus one
authorized stronger attempt; either can be skipped. No active attempt can alter
frozen evidence silently. A process restart cannot create an uncounted third attempt.

## Edge Cases & Failure Modes

Cover duplicate findings/reports, same finding after repair, infrastructure failures,
stale contracts, no actual model control, unavailable escalation, changed test oracle,
new important bug, interrupted commit and provider termination. Preserve work and
surface the reason instead of restarting the entire task or suppressing a failure.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Default/standalone validation still stops. Opt-in fixtures
  permit local defects but route critical, off-limits, architecture and frozen-test
  problems to the required decision path.
- [ ] **AC-02** (REQ-03, REQ-07) A correction fixture changes only necessary code, retains
  correct files and frozen tests, adds new reproduction tests before implementation,
  and cannot close without independent revalidation.
- [ ] **AC-03** (REQ-04, REQ-08) Repeated/no-progress findings skip cheap retries; restart,
  duplicate events and changed worker sessions cannot exceed the persisted bound or
  start a dependent task on an unreviewed result.
- [ ] **AC-04** (REQ-05, REQ-06) Hand-calculated policy scenarios select immediate strong
  execution when repair erases savings; unknown evidence keeps conservative behavior,
  and unavailable/unsupported stronger requests stop visibly.
- [ ] **AC-05** (REQ-09) Reports include every attempt/review/context/escalation cost,
  terminal findings and model identities. Offline traces cover disable/resume and do
  not launch paid models or impose a production spend/time cap.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-07 | AC-02 |
| REQ-04, REQ-08 | AC-03 |
| REQ-05, REQ-06 | AC-04 |
| REQ-09 | AC-05 |

## Risks

A reviewer may be wrong, a cheap model may misunderstand its instructions, and changing
tests can disguise failure. Keep original acceptance authoritative, evaluate independently
under 09 and stop rather than auto-amend the contract.

## Assumptions

One local attempt is a conservative initial policy choice, not an empirically optimal
retry count. Changing the bound or default requires an explicit policy decision and
quality evidence, not a continuation that silently resets the episode.

## Decisions

Introduce an opt-in exception to current failure stops only after a recorded ADR.
Retain hard intent/invariant stops, single-writer state, test-first order and independent
validation. Strong-first and early strong escalation remain valid choices.

## Clarifications

2026-10-21: the owner prioritizes minimal corrected errors and lowest total correct-result
cost. A low-cost model is not preferred when expected rework makes it more expensive.

## Open Questions

None blocking for implementing the disabled-by-default path. Paid qualification and any
default activation need a 09 manifest and owner-approved tolerances.

## Notes

Depends on 04, 06, 09, 15, 16 and 18. Suggested slices: policy/lineage; eligibility;
correction packet; bounded controller flow; test/review integration; recovery/docs.
Parallel repair behavior is integrated separately in 12.

## Readiness Checklist

Existing behavior, opt-in change, hard stops, finite attempts, quality gates and
acceptance are explicit. Ready for Discovery; paid qualification remains unapproved.
