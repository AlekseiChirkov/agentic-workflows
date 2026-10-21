# Reduce orchestrator turns and deterministic bookkeeping overhead

## Source

Workstream 4 of the owner's 2026-10-21 request: reduce controller context/turns while
preserving checkpoints, single-writer state and correctness.

## Context & Problem

The orchestrator performs branch/state bookkeeping, RED/GREEN commits, independent
review, composite rollup and reporting (`workflows/spec-run.md:158`). RED and GREEN are
separate checkpoints with the same Implementer (`workflows/spec-run.md:169`); removing
that checkpoint would break test-first commit evidence. Optimize work around those
gates, not the gates themselves.

## Goal

Keep the controller focused on decisions requiring judgment and use bounded,
deterministic inspections and patch proposals for repeated mechanical work.

## Scope

Checkpoint envelope, read-only inspection/delta rendering, batched safe reads, resume
receipts, compact controller context and selective history retrieval.

## Out of Scope

General state CLI (07 remains backlog), a runtime that launches agents, changing writer
ownership, skipping RED/GREEN commits or independent review, top-level parallelism,
or automatically starting dependent work before its prerequisite is reviewed.

## Actors & Roles

The orchestrator owns git and shared state. Implementer/Validator return evidence and
proposed deltas. Optional helpers inspect/render deterministic results and never spawn
models, commit, or mutate canonical task state.

## Terminology

A checkpoint envelope is one complete structured report for a logical boundary.
A delta is a proposal against an identified state revision; it is not self-authorizing.

## Requirements

- **REQ-01** THE SYSTEM SHALL define RED, GREEN, review and close envelopes carrying
  task/leaf identity, base/tree revision, event/attempt identity, AC/evidence references,
  exact changed/test paths, test outcome, findings and proposed state delta. Required
  fields SHALL remain complete even when human narration is compact under 08.
- **REQ-02** THE SYSTEM SHALL consolidate redundant status polls and repeated reports
  into the next meaningful checkpoint, while preserving RED-before-implementation,
  GREEN-before-review, independent validation and every existing owner/blocker stop.
  A running agent without a new checkpoint SHALL not trigger repeated full-state reads.
- **REQ-03** THE SYSTEM SHALL provide an optional deterministic inspection/rendering
  helper for branch/base verification, exact-path staging plans, progress-block
  extraction and canonical delta proposals. It SHALL be read-only for project state/
  git; the orchestrator applies reviewed patches and executes git commands. This is
  not the generic arbitrary-field state mutation API deferred in 07.
- **REQ-04** WHEN applying a proposed delta, THE SYSTEM SHALL verify task/leaf, source
  hash, current branch/base, allowed transition and evidence preconditions, preserve
  protected fields and unrelated blocks, and apply it once. Stale, duplicate or
  contradictory proposals SHALL be rejected or recognized as already applied before
  any mutation. Helpers SHALL not grant permission for an otherwise forbidden action.
- **REQ-05** THE SYSTEM SHALL keep the active controller packet bounded to the current
  checkpoint, leaf contract/view, unresolved findings, prerequisite summaries and
  relevant git evidence. Full history SHALL stay on disk with hashes/retrieval paths;
  a resume/new agent SHALL verify it before relying on a prior decision.
- **REQ-06** WHEN safe independent reads are needed, THE SYSTEM SHALL batch them into
  one inspection operation, preserving each command's status and output identity.
  Dependent mutations, commits, approvals and state transitions SHALL stay ordered;
  batching SHALL not combine RED and GREEN across their required checkpoint.
- **REQ-07** THE SYSTEM SHALL attribute controller requests, tool calls, state bytes
  loaded and checkpoint counts to 05. It SHALL compare complete controller cost and
  latency, not reduce turns by moving the same work to uncounted children.
- **REQ-08** THE SYSTEM SHALL retain manual instructions when helpers are absent,
  recover from interruption at any checkpoint, and apply shared index gates G1–G8.
  New behavioral interfaces SHALL be recorded during implementation; no mandatory
  runtime dependency or state-tool promotion is authorized by this specification.

## Data Model

Envelope version, event ID, task/leaf, role, attempt, state hash, branch/base/tree,
evidence references, required next gate and proposed patch. Session-local receipts
record accepted envelope IDs; durable canonical statuses remain unchanged.

## Contracts & Interfaces

Proposed optional interface:
`scripts/controller-step.sh inspect --task <dir> --leaf <id>` and
`... render --event <file>`, producing versioned JSON plus an exact patch proposal.
Missing dependencies use manual inspection and the same transition checks.
No `apply`, agent-spawn or arbitrary field-write subcommand is included.

The orchestrator may submit the validated patch through existing editing tools as one
operation, with its existing authorization. Spec 06 enforcement still applies to all
subsequent git commands. Spec 07 may later reuse the renderer if separately scheduled.

## Non-Functional Requirements

Helpers perform zero model calls, state writes or git mutations. Duplicate events
are idempotent at the orchestration layer. Unrelated/protected text is byte-preserved.
Safety checks precede effects; controller turn reduction is measured under 05/09.

## Edge Cases & Failure Modes

Cover missing/duplicated reports, stale hashes, manually edited state, branch movement,
RED without committed tests, GREEN without successful verification, late child result,
partially applied patch, missing helper and controller restart. On ambiguity inspect
the real tree/evidence; never synthesize a completed gate.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Trace fixtures have one meaningful envelope per boundary,
  no redundant polling turns, and retain separate RED, GREEN and independent review.
- [ ] **AC-02** (REQ-03, REQ-06) Helper fixtures return deterministic inspection/patch
  proposals, retain per-command failures, make zero mutations/calls and preserve
  sequential dependent actions.
- [ ] **AC-03** (REQ-04) Stale/duplicate/wrong-branch/invalid-transition fixtures cannot
  overwrite state; correct patches preserve unrelated blocks and protected evidence.
- [ ] **AC-04** (REQ-05, REQ-08) Interrupt/restart at every checkpoint and helper-absent
  runs resume through the same gates with full-history retrieval available.
- [ ] **AC-05** (REQ-07, REQ-08) Before/after fixture traces expose controller calls,
  bytes and delegated work; documentation includes rollout/disable and does not claim
  measured model savings without a separately approved run.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-06 | AC-02 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-07 | AC-05 |
| REQ-08 | AC-04, AC-05 |

## Risks

Over-batching can remove a necessary decision or hide an error. Preserve checkpoint
semantics and individual read statuses; never batch dependencies or approvals blindly.

## Assumptions

The existing editor and git interfaces suffice for applying a rendered proposal.
No state lock service is required while the orchestrator remains the only writer.

## Decisions

Retain ADR-0001's Markdown orchestration and optional helpers, ADR-0009's deferred
state engine, and current test-first two-checkpoint execution.

## Clarifications

2026-10-21: deterministic bookkeeping means inspections/rendered proposals plus the
existing authorized writer, not a mandatory autonomous state-mutating daemon.

## Open Questions

None blocking. Actual turn/cost improvement needs evaluation under 09.

## Notes

Depends on 06, 09 and 14. Suggested slices: envelope; inspection/render helper;
transition guards; controller history/polling; recovery fixtures and documentation.
Spec 12 later supplies concurrent child results; this feature remains sequential.

## Readiness Checklist

Checkpoint ownership, optional interface, failure cases and acceptance are explicit.
Ready for Discovery; no claim that fewer turns necessarily reduce total cost.
