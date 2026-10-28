# ADR-0014: Decisions for Task unknown — Clarify workflow execution and context ownership

## Status

Accepted

## Date

2026-10-28

## Related Task

- Task: owner-requested workflow optimization and specification reconciliation.
- Related files: workflow sources, phase rules, global/reference contracts and quick-flow.

## Summary

Keep one operative definition per contract and make parent/child routing explicit.
Reduce repeated instructional prose while preserving prerequisites, evidence, stops,
shared-file ownership and independent validation.

## Context

A source-wide review found contradictory bootstrap and completion instructions,
incomplete resume paths, model-scoring inconsistencies and ambiguous fix-cycle ownership.
The owner authorized corrections followed by a separate instruction-size pass and
reconciliation of specifications. Existing state formats and deployed capabilities remain
compatible; this work does not execute the roadmap's broader harness or tooling changes.

## Decisions

### Decision 1: Reuse current context within its owning session

**What was decided:** Reuse available, unchanged sources for the same resolved project.
Fresh workers and standalone calls perform their own full bootstrap. Resolve umbrella
context from the project directory, and verify cache source membership before reuse.

**Why:** Unconditional child reloads repeat instructions without increasing evidence.

**Alternatives:** Always reload every source; trust a receipt without providing content.
The former repeats context, while the latter cannot establish what a worker knows.

**Consequences:** Mutable sources must be rechecked; stronger hash-bound packets remain
planned. This decision does not provide persistent session receipts or cache guarantees.

**Related files:** Global context contract, atomic phase rules and context-pack workflow.

### Decision 2: Complete only after verified finalization

**What was decided:** Prepare completion metadata, verify contract/review/fix evidence,
record qualifying decisions, reconcile the specification, then write completion status.
Retain future scope and failed criteria honestly. Existing frontmatter is not proof of
completion. Orchestrated proposal batches remain pending without automatic application.

**Why:** Early completion markers hide unfinished reconciliation or unapproved scope.

**Alternatives:** Mark complete first and repair metadata later; rewrite unmet criteria
as delivered behavior. Both misrepresent the accepted outcome.

**Consequences:** Interrupted finalization resumes from evidence. No-op reconciliation
is successful; errors remain outstanding. Direct owner-authorized spec maintenance is
explicitly allowed without using a failed acceptance criterion as an edit justification.

**Related files:** Finalization, specification reconciliation and canonical file contracts.

### Decision 3: Align test gates and promotion stops

**What was decided:** Classify testability before requiring a runner. An independently
justified none level records actual manual verification; absent tooling never implies
none. Composite promotion preserves evidence and stops for the required decision.

**Why:** The old order blocked legitimate non-testable work and contradicted declared stops.

**Alternatives:** Require a test runner for every artifact; continue automatically after
promotion. Neither preserves the existing gate and escalation intent.

**Consequences:** Testable work still requires observed test evidence. Changed topology
must be reconciled before restarting execution; generated fix siblings enter the pending
order and cannot be lost behind an initial printed plan.

**Related files:** TDD workflows, quick-flow, classifier and orchestrated subtask loop.

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

Dropping operative safeguards to meet a size target; treating word counts as measured
usage; declaring planned helper APIs or broader migration complete after prose cleanup.

## Implications for Future Work

Preserve explicit stops, field vocabulary, single-writer state and test-first evidence.
Implement source hashing, model catalog persistence, generated references and policy
changes under their separate specifications; retain current fallback behavior until then.

## Verification

Offline workflow interface/reference checks, 530 static contracts and five hook workflow
fixtures passed. The full suite passed 589 checks with two optional skips; its one existing unstaged
archive condition passed the unchanged strict identity gate in a disposable index.
The real index was preserved. Complete evidence is recorded in the linked audit.
No deployment or paid comparison was performed.

## References

- Related documents: [Workflow clarity and size audit](../../docs/audits/2026-10-28-workflow-clarity-and-size.md).
