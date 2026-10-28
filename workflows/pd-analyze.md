---
description: Discovery Step 1 — Analyze task and codebase; resolve ambiguities autonomously by default, ask clarifying questions with --step-by-step
---

Invocation: `/pd-analyze <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 1.

Resolve paths inside the task directory (trailing slash optional). Default is
autonomous; `--step-by-step` waits for requirement clarification. Reuse parent context.

## Guard

1. Read task `state.md`. Missing/unreadable state → **stop** and request the task
   directory created by `/phase-discovery`.
2. `discovery: complete` → **stop** for explicit overwrite confirmation unless
   that exact rerun is already confirmed by the parent. Preserve unrelated state.

## Instructions

1. Resolve the task statement from `spec_path:` in `state.md`; otherwise use the
   legacy task-level `description.md`. Missing/unreadable selected input → **stop**
   and report its path; do not silently switch from a broken `spec_path:`.
   For `active_phase: N`, include the shared preamble before the first phase heading
   and the selected phase section up to the next recognized phase heading,
   regardless of its number or heading level. Exclude other phases. Validate the selected
   boundary; lead the Goal with `Phase <N> of <M> —`.
2. Apply the `phase-discovery` rule's Context Bootstrap unless the parent already
   supplied it. This includes `.ai/memory/architecture.md`, `.ai/memory/state.md`,
   `.ai/principles/architecture.md`, coding/domain principles and the ADR index;
   progress and integration/environment context are conditional as defined there.
   Report loaded files and constraints once per context.
3. Resolve ambiguities:
   - Step-by-step: ask only unresolved questions and **wait** for answers.
   - Autonomous: follow the research order in `phase-discovery` and the
     `workflow-reference → ## Autonomous Decision Protocol`. Record each resolution
     and evidence in `### Assumptions`. Derive missing Acceptance Criteria from the
     goal; escalate only on the protocol's threshold or a hard blocker.
   - Under `/spec-run`, apply `orchestration → ## Escalation protocol`: resolve
     Class A (missing context) with evidence; collect Class B (missing intent) in
     `## Open Questions (batch)`. Never guess Class B answers. Continue analysis
     that does not depend on them; mark dependent conclusions provisional. The
     parent presents the entire batch to the human before creating branches and
     reconciles affected analysis/design before execution.
4. Inspect only the affected codebase using the rule's reading budget: at most
   8 entry-point and 4 one-level-deeper files, 12 total. Use architecture context
   to scope reading; verify affected interfaces and freshness in source, beginning
   with entry points; read deeper only when needed. Record paths, reasons and
   `Files read: N/12 (X entry-points, Y deeper)` in `### Codebase Analysis`.
   Stop reading once interfaces are understood. If the budget is exhausted, record
   `Insufficient architecture.md coverage for: <modules>` under `### Open Questions`.
   Do not invent conclusions; an unresolved implementation-critical gap remains
   a blocker for dependent work. Knowledge/spec files are outside this source-file budget.
5. On first analysis, read `VERSION` from the workflow source checkout root.
   A single numeric `major.minor.patch` value may
   be recorded as `contract_version:` immediately after `spec_path:`. Missing,
   unreadable or malformed VERSION is omitted without blocking. Preserve any
   recorded version on resume and never stamp an old analysis retroactively.
   Older readers/states without `contract_version` remain valid. Output header:

```
spec_path: <existing resolved specification path>
contract_version: <valid source VERSION; omit when unavailable>
```

   Preserve an existing source path; legacy tasks without a spec keep their
   description source without inventing a `spec_path:`.
6. Upsert `## Task Analysis` in task `state.md`; preserve other sections and phase
   statuses. Set only `discovery: in-progress`:

   ```
   ## Task Analysis

   ### Goal
   <one paragraph; phase prefix when applicable>

   ### Affected Parts
   <components, expected file surface and effects>

   ### Codebase Analysis
   <findings; source paths/reasons; budget count, or no additional files needed>

   ### Open Questions
   <remaining gaps and their effect on further work, or None>

   ### Assumptions
   - <ambiguity> → <resolution> (source: <principle, ADR, code path, best practice or user>)
   ```

   Always retain `### Assumptions`; write `None` when empty. User answers use the
   same format. Under `/spec-run` only, also upsert:

   ```
   ## Open Questions (batch)
   - Q<N>: <self-contained question>
     why unanswerable: <evidence searched and remaining intent gap>
     options: (a) <answer and consequence> (b) <answer and consequence>
     affects: <design or work dependent on the answer>
   ```

   Write `None` when no Class B question remains; omit this section outside
   orchestrated mode. Preserve previously answered questions as assumptions.
7. Evaluate `quick-flow → ## The escalation gate` against the established file
   count and impact (3 or fewer files, counting test files). Require all conditions;
   uncertainty means full. Write top-level `flow:` and an assumption line:
   `flow: quick|full — gate: 1<pass/fail> 2<pass/fail> 3<pass/fail> 4<pass/fail>`.
   For quick flow, write `## Contract (quick)` with `### Off-limits`,
   `### Invariants` (existing only), and binary, observable `### Acceptance Criteria`
   before implementation. Create no T-XX directories. Existing full-flow artifacts
   are not silently discarded or downgraded on a rerun; preserve full flow or
   report the conflicting artifacts for reconciliation.
8. Report: `Step 1 (Task Analysis) complete. flow: <quick|full>.` Mention remaining
   gaps/batch questions. Under an autonomous parent this is a progress marker,
   not a handoff; the parent runs its next applicable child. Standalone use ends here.
