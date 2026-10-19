---
trigger: always_on
---

# Orchestration Contract

Governs `/spec-run` — the orchestrated mode in which one spec is carried from Discovery to
finished pull requests by a set of agents with deliberately narrow context.

**Sub-agents exist to bound context, not to run work in parallel.** Execution is strictly
sequential: one subtask at a time, one agent at a time. Nothing in this rule licenses
concurrent execution, and no workflow may introduce it — the pipeline's single
`## Subtask Progress` block in the parent `state.md` has no locking and would be corrupted by
concurrent writers.

---

## Roles

Four roles. A role is a context boundary, not a personality.

| Role | Lifetime | Sees | Writes |
|---|---|---|---|
| **Orchestrator** | whole run | task-level state, `plan.md`, branch/PR state, agent reports | `state.md`, `plan.md`, shared `.ai/` files, git operations |
| **Arbiter** | whole run | spec, `state.md`, all `.ai/` principles + ADRs + architecture, `plan.md` | nothing — answers only |
| **Implementer** | one subtask | that `T-XX/description.md`, `.ai/` context, its own RED tests | code, tests, its own `## Subtask Progress` block |
| **Validator** | one subtask | that `T-XX/description.md`, the tests, the diff | verdict into its own block |

### Orchestrator

Owns sequencing, git, and every shared file. Runs Discovery itself (Discovery is cheap in
context and produces the artifacts every later agent depends on). For each T-XX in
topological order: creates the branch, spawns the Implementer, spawns the Validator, commits,
opens the draft PR, updates task-level state, moves on.

Never writes code. Never writes tests. Never merges.

### Arbiter — the context holder

Spawned once, kept alive for the whole run, addressed by message rather than re-spawned so
its context persists. It exists because Implementer and Validator are given narrow context on
purpose; without it, every ambiguity would force a full context reload into a sub-agent and
the token economy this design exists for would evaporate.

**Answers exactly one class of question** — see the escalation protocol below.

**Citation rule (hard):** every answer must cite its source — a named principle, `ADR-NNNN`,
`architecture.md`, or a concrete file and pattern in the repository.
*An answer without a citation is not an answer.*
It is reclassified as a question for the human. This is the single mechanism preventing the
arbiter from becoming a well-formatted source of unsupported claims.

The arbiter has no authority to: clear a violated invariant, approve a composite promotion,
override a Guard, or decide that a test-level gate returns `none`.

### Implementer

One agent per subtask, running the full atomic execution cycle for that subtask:
`/pae-tests` → `/pae-implement` → `/pae-finalize`. Tests and implementation live in the same
agent because the GREEN step must read the RED set it is satisfying, and splitting them would
pay the `.ai/` context bootstrap twice for no isolation gain.

It **pauses once, at RED**: after `/pae-tests` it reports the RED digest and the test files it
wrote, and waits. That pause exists so the orchestrator can create the test-only commit
`git-flow → ## Commits` requires — the Implementer never runs `git` itself. One message resumes
it, in the same context, for `/pae-implement` → `/pae-finalize`. Sequence:
`/spec-run → ## Step 4 → 4.2`.

Receives: the path to one `T-XX/description.md`, the resolved `WORK_DIR`, and the branch it
is on. Loads `.ai/` context itself per the standalone-invocation rule. Receives **no**
transcript from previous subtasks — the parent `state.md` is the handoff.

### Validator

A **separate agent** with no memory of how the implementation was produced. Runs
`/pav-check` → `/pav-propose --batch` → `/pav-close`.

Receives: the path to the same `T-XX/description.md`, the test files, and the diff for the
subtask. Does **not** receive the Implementer's reasoning, its intermediate steps, or its
self-assessment. The point is an independent reading of whether the code satisfies the
criteria — an agent that watched the code being written cannot supply that.

This separation is what makes the TDD test-set audit in `/pav-check` meaningful: the
Validator compares the tests against the RED digest without having been present when either
was written.

---

## Shared-file discipline

Sub-agents write **only** their own `## Subtask Progress` block and their own code and test
files. They must not write to:

- `.ai/memory/architecture.md`, `.ai/memory/state.md`, `.ai/memory/progress.md`
- `.ai/project_state.md`
- `.ai/adr/` and `.ai/adr/index.md`
- `plan.md`, or another subtask's progress block

Where a workflow instructs a sub-agent to update one of these, the sub-agent instead
**returns the proposed delta in its report**, and the orchestrator applies it. One writer per
shared file, always. Every such case in the pipeline today:

| Shared file | Instructed by | What the sub-agent returns instead |
|---|---|---|
| `.ai/memory/architecture.md` | `/pae-finalize` step 1b (Implementer) | the module entries to add or update |
| `.ai/memory/state.md`, `.ai/project_state.md` | the finalize workflows | the entry line, in the format `workflow-reference` defines |
| `plan.md` | `/pae-finalize` step 2 (Implementer: `Status` → `done`) and `/pav-close` step 2 (Validator: `Status` → `reviewed`) | the T-XX row and its new `Status` value |
| `plan.md`, the `[composite]` block, `## Integration Issues (T-XX)`, and any D8 fix-sibling directory + row | `/phase-composite-validation` steps 2 and 3, reached from `/pav-close` step 5 inside the **Validator** | the composite row's new `Status`, the composite block's new field values, the approve/defer list, and — for a D8 sibling — the directory to create with its `description.md`, its `plan.md` row, and its leaf block |

`plan.md` is named here explicitly, not left to inference: setting the subtask's `Status` is the
whole job of `/pae-finalize` step 2 and `/pav-close` step 2, so without the delta-return route a
sub-agent would be instructed to do the thing this section forbids. The carve-out for "its own
`## Subtask Progress` block" does **not** extend to `plan.md` — a composite's rollup row is not
any single sub-agent's own row.

`/phase-composite-validation` is the third row for the same reason, and it is the widest case:
the Validator reaches it through `/pav-close` step 5 when the last child of a composite closes,
and every artifact it produces is shared — the composite's own block, `plan.md`, a task-level
section, and, on a NEEDS WORK verdict, a whole new sibling subtask. None of that is the
Validator's own row, so none of it is written by the Validator. It returns the deltas; the
orchestrator applies them, creates the directory, and writes the rows.

After each sub-agent returns, the orchestrator verifies that the subtask's progress block is
structurally intact (required fields present, status vocabulary valid). An agent that died
mid-write leaves a truncated block; repair it or re-run the step before continuing.

---

## Escalation protocol

Every ambiguity is one of two classes. Route by class — never by how important it feels.

**Class A — missing context.** The answer exists in the project's artifacts but not in the
asking agent's window. Examples: which layer owns validation, what error shape the API
returns, which naming standard applies, whether a pattern already exists.

→ Ask the **Arbiter**. It answers with a citation. The resolution is recorded in the
subtask's `notes:` in the form `arbiter: <question> → <answer> (source: <citation>)`.
The run does not stop.

**Class B — missing intent.** The spec does not determine it, the codebase does not imply it,
and two reasonable answers produce a materially different product. Examples: should an
expired token refresh or force re-login; is a partial import an error or a warning; which of
two behaviours is the product actually meant to have.

→ **The human decides.** No agent may resolve it, the arbiter included.

**The decisive design consequence:** in a strictly sequential dependency chain, parking a
subtask does not let the others proceed — parking is stopping. Therefore class B must be
harvested *before* execution begins, not discovered during it.

### Where class B is harvested — the Discovery batch gate

During Discovery, `/pd-analyze` collects every class-B ambiguity into
`state.md → ## Open Questions (batch)` instead of resolving it. Class A ambiguities continue
to be resolved autonomously and recorded in `### Assumptions` with their source, unchanged.

Before creating the first branch, the orchestrator presents the batch to the human as one
list — each question with 2–3 options and the arbiter's recommendation — and **waits**. The
answers are written into `### Assumptions` and become part of the task contract.

The human is asked **once**, at the point where answering is cheapest: before any branch,
any test, any line of code. This is also a review of the spec itself, which is where a
spec-driven flow wants its quality gate.

### Class B discovered during Execution

A leak means Discovery missed something. The run **stops**: record the question in
`## Open Questions (batch)` with the subtask that hit it, leave the branch and its commits
intact, report, and wait. Do not guess. A wrong requirement invalidates every phase built on
top of it, and in a stack it invalidates every branch above it too.

### Conditions that always stop the run, regardless of class

- A violated invariant or Off-limits breach (`/pv-contract` critical-failure gate).
- `atomic-tests: failed` — RED was never established (see `tdd`).
- A composite-promotion tripwire firing in `/pae-implement`.
- Any `## Guard` that would overwrite existing artifacts.
- A preflight or git-rail violation (see `git-flow`).
- A sub-agent reporting a blocker it could not resolve.

Autonomy in this mode licenses *unblocked* decisions, never *unrecorded* ones, and never
decisions the pipeline has deliberately reserved for a human.
