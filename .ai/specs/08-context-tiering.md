# Compact instructions, explicit loads and concise reports

## Source

ADR-0009 Decision 6 and workstream 3 of the owner's 2026-10-21 optimization request.
The previous unmeasured 40–60k bootstrap-token claim is withdrawn as a baseline.

## Context & Problem

The 2026-10-28 workflow audit removed repeated instructions, clarified child/parent
context ownership, and made standalone bootstrap requirements explicit. The canonical
phase bootstraps remain mandatory; an already loaded compatible parent context can be
reused under `rules/workflow-globals.md` (Context Bootstrap contract). Context packs still use
the current metadata freshness contract (`workflows/context-pack.md → ## Step 1 — Check freshness`).

This is an initial instruction cleanup, not delivery of this spec. The rule/reference
split, machine-readable `loads:`, transitive context measurement, reference deployment,
size targets and quantified baseline gates remain pending. Spec 14 owns stronger project
context manifests/packets and reuse receipts; operative constraints cannot be removed to
meet a size target.

## Goal

Reduce repeated instructional prose and generated narration while retaining operative
contracts, test evidence, findings, stop conditions and readable recovery instructions.

## Scope

Rule/reference split, per-workflow load declarations, context-size tooling, concise
workflow/role report schemas and structural regression checks.

## Out of Scope

Changing contract meaning, task-state storage or project context selection (14),
tool-output truncation (17), cheaper models (04/18), and skipping validation (16).

## Actors & Roles

Maintainers keep one canonical contract; sync deploys on-demand reference; workflow
authors declare loads; executors return concise evidence; validators verify the same
acceptance obligations.

## Terminology

Always-on text is supplied every session. On-demand reference is loaded only when a
condition/citation requires it. A load graph records dependencies and conditional edges;
its unconditional closure is not every reachable reference.

## Requirements

- **REQ-01** THE SYSTEM SHALL keep each top-level rule at most 700 words and the
  always-on set at most 6,000 words; the stricter bootstrap limit from 13 still applies.
  Optional rationale, examples and incidents SHALL move to `rules/reference/<name>.md`
  with stable section links; all operative requirements SHALL stay reachable and
  mandatory conditions SHALL not become optional reference.
- **REQ-02** WHEN syncing, THE SYSTEM SHALL deploy reference files as `ref-<name>`
  on-demand skills with manifest-owned cleanup and preserve references after renames.
- **REQ-03** THE SYSTEM SHALL add `loads:` to workflow front matter, identify mandatory
  and conditional dependencies, and have bootstraps cite the declaration instead of
  duplicating load lists. Missing conditional prerequisites SHALL trigger full relevant
  loading or the original stop, never silent continuation.
- **REQ-04** THE SYSTEM SHALL provide `scripts/measure-context.sh <workflow>`, resolving
  mandatory loads once, detecting missing targets/cycles and reporting words/bytes,
  always-on contribution, and conditional/worst-case closure separately. It SHALL
  not call word counts token counts or assume that every reference is eagerly loaded.
- **REQ-05** WHEN comparing `atomic-execution-implement` and
  `atomic-execution-tests`, THE SYSTEM SHALL record a pre-change baseline with matching
  source/deployed versions and reduce each mandatory instruction-word total to at most
  50 percent of baseline without changing its obligations. If this is infeasible while
  preserving contracts, the task SHALL surface the failed target for owner decision,
  not hide missing requirements or silently weaken the gate.
- **REQ-06** THE SYSTEM SHALL define concise RED, GREEN, review and final-report
  projections carrying result, changed files/diff identity, relevant AC IDs, test
  command/result/evidence reference, blockers, required decisions and next action.
  Repeated step prose, full specs and already recorded histories SHALL not be echoed
  by default; full artifacts SHALL remain accessible. Mandatory warnings and findings
  SHALL never be suppressed to hit a length target.
- **REQ-07** WHEN an output cap or compact schema is used, THE SYSTEM SHALL distinguish
  a complete structured payload from a shortened human summary. It SHALL not truncate
  state deltas, git instructions, errors, test failure details or acceptance evidence
  in transit. Spec 15 owns checkpoint envelopes; 17 owns tool previews.
- **REQ-08** THE SYSTEM SHALL enforce size/reachability/load and required-output-field
  contracts, preserve canonical statuses/protected state and pass offline regression
  assertions from 09. Shared index gates G1–G8 apply. Actual usage/cost comparisons
  SHALL use 05/09 separately from instruction-word targets.

## Data Model

`loads:` references mandatory rules plus explicit conditional references with a
condition. Discovery finalizes a machine-readable encoding compatible with 13's
front matter and 10's renderer. Compact reports reference local full evidence by path,
content hash and scope; no provider-specific report parser is required.

## Contracts & Interfaces

The existing workflow invocations and statuses remain. Removed prose must map to its
new reference home; bootstrap command/prohibition text stays operative and exact.
`measure-context.sh` returns a nonzero status for unresolved mandatory loads/cycles
and emits a machine-readable option for offline gates; it invokes no models.

## Non-Functional Requirements

≤700 words per top-level rule, ≤6,000 always-on words, bootstrap ≤300 words under 13.
Unique dependency traversal terminates on cycles with diagnostics. Output completeness
is schema-based, not a forced prose-word cap that could drop critical findings.

## Edge Cases & Failure Modes

Cover empty/missing load lists, conditional profiles, duplicate/transitive dependencies,
cycles, renamed sections, standalone child calls and long finding lists. A summary
reference without its artifact is incomplete evidence and triggers retrieval/recheck.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Word gates and reference resolution pass; a moved
  prohibition or unmanifested destructive cleanup is rejected.
- [ ] **AC-02** (REQ-03, REQ-04) Every workflow has valid loads; fixtures distinguish
  mandatory and conditional closure, avoid double counting, and reject broken cycles.
- [ ] **AC-03** (REQ-05) Both named workflows meet the recorded 50-percent instruction
  target with a requirement-preservation map, or acceptance explicitly remains failed.
- [ ] **AC-04** (REQ-06, REQ-07) RED/GREEN/review/final fixtures retain required fields
  and full evidence; a large critical-finding payload is preserved despite summary caps.
- [ ] **AC-05** (REQ-08) Offline flat/TDD/state assertions pass, documentation includes
  disable/full-reference recovery, and no savings claim is inferred from word counts.
  An approved release golden, when run, also preserves behavior.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06, REQ-07 | AC-04 |
| REQ-08 | AC-05 |

## Risks

Over-compression can hide a stop or load condition. Keep a before/after obligation map,
test standalone entry points, and preserve access to full reference. A shorter prompt
can have worse cache behavior; only 05/09 can establish a financial result.

## Assumptions

Instruction-word reduction is a structural target, not a promised token/cost reduction.
Optional reference may be expensive on unusual tasks and must be reported honestly.

## Decisions

Retain ADR-0009 size targets, on-demand references and post-rename implementation.
No test-first, validation or protected-section rule is relaxed.

## Clarifications

2026-10-21: expanded to concise generated reports; task context and tool output stay
owned by 14 and 17. Full model-driven goldens remain explicitly approved/release-only.

## Open Questions

No blocking question. Comparative task samples and quality margins are decided before
paid evaluation under 09.

## Notes

Depends on 13 and 09. Suggested slices: baseline/load graph; rule split; deployment;
report contracts; measurement/contract checks; regression and documentation.

## Readiness Checklist

Goal, exclusions, measurable targets, failure behavior and traceability are specified.
Ready for Discovery; conditional loads must not be mistaken for optional correctness.
