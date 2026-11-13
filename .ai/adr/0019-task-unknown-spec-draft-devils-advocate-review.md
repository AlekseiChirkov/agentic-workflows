# ADR-0019: Decisions for Task unknown — Independent bounded review in specification authoring

## Status

Accepted

## Date

2026-11-13

## Related Task

- Task: owner-requested improvement of standalone specification authoring.
- Related files: `workflows/spec-draft.md`, `scripts/check-spec-draft.sh`,
  `.ai/principles/domain.md`.

## Summary

`/spec-draft` replaces its two-pass author self-review with a bounded loop between the
author and a separate read-only Devil's Advocate critic, scored on a fixed 100-point rubric.
A specification is ready for development only at 95/100 or more with no open critical or
major finding.

## Context

The former self-review was run by the agent that wrote the draft and still held the
conversation, so gaps it filled from memory stayed invisible. The readiness gate had no
quality measure, and nothing bounded iterative correction. No contract check covered the
workflow.

## Decisions

### Decision 1: An independent critic reviews the draft

**What was decided:** Spawn one Devil's Advocate sub-agent per review loop. It sees the
spec, project sources and code, never the conversation or the author's reasoning, and never
edits the spec. Later rounds go to the same critic by message.

**Why:** Hiding the conversation tests whether the spec stands alone. A persistent critic
verifies its own earlier findings instead of rediscovering the document each round.

**Alternatives:** A fresh critic every round — rejected: it re-raises closed or new minor
findings and contradicts earlier rounds, which defeats convergence. Author self-review —
rejected: it is the defect being fixed.

**Consequences:** One writer per file is preserved; the author applies every change.
Harnesses without sub-agents run an inline pass labelled `critic: inline`, which cannot
pass readiness check 14.

### Decision 2: Bounded loop with severity caps

**What was decided:** At most 10 rounds. The loop ends at pass (score ≥ 95, no open
critical or major), at the round limit, or on stagnation (two consecutive rounds without a
new critical or major finding and without a score increase). An open critical finding caps
the score at 80 and an open major one at 94; minor findings together deduct at most 5 points
and never start a round.

**Why:** The caps make the 95 threshold equivalent to "no material defect remains", so the
score cannot be gamed by polishing wording, and minor findings cannot keep the loop alive.

**Alternatives:** Unbounded rounds until a perfect score; a score without caps. Both allow
endless minor correction or a passing score over a material defect.

**Consequences:** Rejecting a finding requires a citation; a finding the critic maintains
becomes a dispute for the human in interactive mode, or an open question in auto mode.
Only a compact review result is written to the spec; the round log goes to the report.

### Decision 3: A standalone focused contract test

**What was decided:** `scripts/check-spec-draft.sh` pins the review contract with one
fast builtin-only check and runs on its own, outside `scripts/validate-contracts.sh`.

**Why:** The validator's check inventory is frozen by the bounded validator runtime
decision; adding a check requires amending that inventory. Its nested source guard also
binds reviewed exceptions to the digest of every shell and Python file under `tests/`, so
any new file there fails the guard. `scripts/` already holds the standalone
`validate-task.sh` checker and is outside that inventory.

**Consequences:** A full validator run does not execute this test; run it directly after
changing the workflow until the validator inventory accepts new checks.

## Verification

The new test failed on the unchanged workflow with 15 named failures, passes after the
change in about 30 ms, and rejects mutations of the score cap, a rubric weight and a
removed rubric criterion.
