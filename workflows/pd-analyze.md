---
description: Discovery Step 1 — Analyze task and codebase; resolve ambiguities autonomously by default, ask clarifying questions with --step-by-step
---

Invocation: `/pd-analyze <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 1.

Task directory = provided argument (trailing slash optional).

**Mode.** Without `--step-by-step` this workflow runs **autonomously**: it does
not ask clarifying questions and does not hand control back mid-step. With
`--step-by-step` it uses the interactive behavior described in step 3.
When invoked standalone (not via `/phase-discovery`), the default is still
autonomous — pass `--step-by-step` to be asked.

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → discovery`. If `complete` → **stop**: "Discovery phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Instructions

1. Resolve task statement:
   a. Read `state.md` from task directory.
   b. If `spec_path:` field is present at the top of `state.md` → read the file
      at that path as the task statement.
   c. Else (legacy fallback) → read `description.md` from task directory.
   d. If neither exists → **stop**: "Cannot resolve task statement. No spec_path
      in state.md and no description.md in task directory."
   e. If `active_phase:` is present in `state.md` (multi-phase spec):
      - Read `active_phase: N` and `spec_phase_count: M`.
      - Task statement = any spec content **before** the first Phase heading
        (treat as shared preamble / common context) PLUS the content starting
        from the `Phase N` heading through the start of the next `Phase <N+1>`
        heading (or end of file if N is the last phase).
      - Do NOT include content from other phases.
      - Record in `## Task Analysis → ### Goal`: lead with "Phase <N> of <M> — ".
   f. If `active_phase:` is absent → unchanged (whole spec is the task statement).
2. Build context from persistent state files — follow `phase-discovery` rules — ## Context Bootstrap.
   Load in order (skip missing files; in multi-repo, load umbrella `../.ai/` first, then `.ai/`):
   - `.ai/memory/architecture.md` — system architecture, components, constraints
   - `.ai/memory/state.md` — current phase, active tasks, blockers
   - `.ai/principles/architecture.md` — architectural decisions and constraints
   - `.ai/principles/coding.md` — naming standards, forbidden patterns (shapes decomposition)
   - `.ai/principles/domain.md` — domain rules, ubiquitous language, business constraints
   - `.ai/adr/index.md` — past decisions index (read full ADR only if directly relevant)
   - `.ai/memory/progress.md` — only if resuming interrupted work
   Report: "Discovery context loaded: [files read]"

   **Conditional load:** if the task statement (from step 1) mentions external
   services, third-party APIs, or cross-service contracts → also read
   `.ai/context/integrations.md`. If it mentions environment-specific setup
   (envs, secrets, infra topology) → also read `.ai/context/environment.md`.
   Skip either without error if not applicable or the file is missing. Note
   which of the two were loaded in the same report line.
3. Resolve ambiguities and unclear requirements.

   **Step-by-step mode** (`--step-by-step`): ask clarifying questions.
   **Wait for answers before continuing.**

   **Autonomous mode** (default): do NOT ask. Resolve each ambiguity by research,
   in this priority order — stop at the first level that answers it:
   1. `.ai/principles/*` — an explicit rule settles the question outright.
   2. `.ai/adr/` — a past decision on the same subject is binding unless the
      task statement explicitly supersedes it. Read the full ADR when the index
      line is not conclusive.
   3. `.ai/memory/architecture.md` + `.ai/memory/state.md` — current system
      shape, in-flight work, existing constraints.
   4. Existing codebase patterns — how comparable cases are already solved here.
      Consistency with the repo outranks a theoretically better alternative.
   5. General best practice — only when levels 1–4 are silent. Prefer the
      smallest, most reversible option.

   Record every resolution in `## Task Analysis → ### Assumptions` using the
   format in step 6. One line per ambiguity — no silent resolutions.

   Escalate to the user only per `workflow-reference → Autonomous Decision
   Protocol → Step 5` (hard blocker with no reasonable default, breaking change
   to an externally consumed contract). Missing Acceptance Criteria is NOT an
   escalation: derive them from the spec's goal and record them as assumptions.

   **Orchestrated mode** (invoked by `/spec-run`): split ambiguities by class per
   `orchestration → ## Escalation protocol` instead of resolving all of them.
   - **Class A — missing context.** The answer exists in the artifacts (principles, ADRs,
     `architecture.md`, codebase patterns). Resolve it exactly as in autonomous mode and
     record it in `### Assumptions` with its source. Unchanged behaviour.
   - **Class B — missing intent.** The spec does not determine it, the codebase does not
     imply it, and two reasonable answers produce a materially different product. Do **not**
     resolve it and do **not** guess a default. Append it to `## Open Questions (batch)` in
     the format below, and carry on analysing — collect every one of them in this pass.

   The test for class B: could a competent engineer with full access to this repository
   still reasonably choose either answer? If yes, it is class B. A resolution you can only
   justify with "seems reasonable" — with no principle, ADR, or existing pattern to cite —
   is class B by definition.

   `/spec-run` presents the whole batch to the human once, before any branch is created, and
   writes the answers back into `### Assumptions`. Collecting them here is what allows the
   rest of the run to proceed without stopping.
4. **Minimal repository reading — decision tree:**
   1. Read the 4 root state files first (done in step 2 above).
   2. For each module/component mentioned in the task description:
      a. If root state files contain a description of that module → do NOT read its files.
      b. If root state files have no mention of that module → read its entry point file only.
      c. If entry point is insufficient to understand the interface → read one level deeper.
   3. Document every file read with reason: "read because X not described in root files."
   4. Stop reading when the affected parts are understood — do not explore beyond that.

**Code reading budget (hard limit):**
- Maximum entry-point files (branch 2b): 8
- Maximum one-level-deeper files (branch 2c): 4
- Total maximum files read: 12
- If budget exhausted before full understanding: stop reading, document the gap
  in `## Task Analysis → ### Open Questions` as "Insufficient architecture.md coverage for: <modules>",
  and continue with available context. Do NOT exceed the budget.
- Budget tracking: maintain a running count in `## Task Analysis → ### Codebase Analysis`:
  `Files read: N/12 (X entry-points, Y deeper)`

   In `state.md → ## Task Analysis → ### Codebase Analysis`, explicitly list every file you read and why — if none were needed beyond step 2, write "No additional files read — state files provided sufficient context."
5. Analyze only the codebase parts relevant to the task that were not covered by step 2.
6. Read `VERSION` from the workflow source checkout (the checkout containing this workflow,
   not the consumer project's root). Accept a single nonempty `major.minor.patch` value
   with numeric components. If VERSION is missing, empty, unreadable, or malformed,
   omit `contract_version:` and continue analysis. Readers accept older state files
   without `contract_version`; its absence never blocks analysis or resume.
   When a valid version is available, write `contract_version:` immediately after
   the existing `spec_path:` line, preserving that path. If no `spec_path:` exists,
   resolve and write the source specification path first. Preserve an already recorded
   contract version when resuming an existing analysis; do not stamp it retroactively.
   Write to `state.md` in the task directory:

```
spec_path: <resolved specification path>
contract_version: <valid VERSION value; omit when unavailable>
flow: quick | full

## Phases
- discovery: in-progress
- execution: not-started
- validation: not-started

## Task Analysis

### Goal
<one paragraph: what needs to be achieved>

### Affected Parts
<list: which parts of the system are affected and how>

### Codebase Analysis
<key findings from the codebase relevant to the task>

### Open Questions
<resolved questions and answers, or "None">

### Assumptions
<one line per autonomously resolved ambiguity — required section, write "None"
when nothing had to be assumed:>
- <ambiguity> → <decision taken> (source: principles | ADR-NNNN | architecture.md | codebase: <file> | best practice | user)

## Open Questions (batch)
<orchestrated mode only — class-B ambiguities awaiting a human decision. Omit the
section entirely in ordinary runs. Write "None" when the pass found no class-B
ambiguity:>
- Q<N>: <the question, stated so it can be answered without reading the codebase>
  why unanswerable: <what was searched and why the artifacts do not settle it>
  options: (a) <option — consequence> (b) <option — consequence> (c) <option — consequence>
  affects: <which T-XX or which part of the design hangs on this>
```

`### Assumptions` is ALWAYS written, even when empty (`None`) — downstream
workflows and the Discovery review digest read it. In step-by-step mode it holds
whatever the user answered, phrased the same way.

Note: do NOT overwrite `spec_path:` if it already exists at the top of `state.md`.
Only set `discovery: in-progress` and append `## Task Analysis` section.

6b. **Set the flow tier** (see the `quick-flow` rule for the full gate). Using the file
   surface and codebase impact just established, evaluate all four gate conditions:
   (1) 3 or fewer files, counting test files — a count, not an estimate; (2) no new
   invariant; (3) no behaviour change to an already-shipped
   pipeline; (4) no DB schema change / no migration. If **all** hold → `flow: quick`;
   if **any** fails → `flow: full`. Default and tie-break is `full`.
   - Write the top-of-file `flow:` field in `state.md`.
   - Record the decision in `### Assumptions` as one line:
     `flow: quick|full — gate: 1<pass/fail> 2<..> 3<..> 4<..>`.
   - If `flow: quick`: write a `## Contract (quick)` section now — `### Off-limits`,
     `### Invariants` (existing invariants the change must not break — never a new one),
     `### Acceptance Criteria` — before any code is touched. `/phase-discovery` will then
     skip `/pd-decompose` and `/pd-design`. Do NOT create T-XX subtasks.
   - If `flow: full`: unchanged — proceed to decomposition.
7. Report: "Step 1 (Task Analysis) complete." — include the chosen `flow:` tier.
   **Autonomous mode:** this report is a progress marker, not a handoff — the
   parent workflow proceeds to Step 2 immediately. Do not stop or ask to continue.
