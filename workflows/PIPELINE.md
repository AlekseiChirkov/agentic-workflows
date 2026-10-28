---
description: Reference documentation — pipeline map and command index; not an executable workflow
---

# AI-Assisted SDLC Pipeline

Discovery → Execution → Validation. Run phases manually, or authorize automatic
transitions with `/phase-pipeline` or `/spec-run`. This file is a navigation reference;
workflow headers own invocations, rules own contracts. Do not load the entire reference
as a prerequisite for an individual child.

## How to Pass Task Context

| Operation | Argument |
|---|---|
| New Discovery | Spec path, e.g. `.ai/specs/01-add-oauth.md` |
| Parent phases and children | Task directory, e.g. `.ai/tasks/todo/task-01-add-oauth/` |
| Atomic execution/validation and their children | Leaf `description.md` path |
| Composite validation | Composite `description.md` path |

`phase-discovery` owns task naming, multi-phase selection and prefix collision checks.
Resolve `working_dir:` before file operations; umbrella context is relative to the
resolved project. See each command for supported flags.

## Task Structure Types

Canonical classifier: `workflow-reference → ## Autonomous Subtask Classifier`.

| Type | Shape and execution |
|---|---|
| **1 — Flat** | Dependency-ordered leaves, one atomic cycle per leaf. |
| **2 — Nested** | Composite container with leaf children; integrate after every child is reviewed. |
| **3 — Vertical re-sliced** | Shared-contract tracks become capability producer→consumer leaf pairs; extract common setup once. |

Only Type 2 creates a composite parent. Depth is capped at two: children are always
leaves. Classifier decisions and dependencies are explicit in the plan.

## File Structure

```text
.ai/
  specs/<NN>-<slug>.md                 original task statement
  memory/{architecture,state,progress}.md
  principles/                         constraints and domain language
  adr/index.md                        decision index
  context/                            runbook, integrations, environment
  tasks/todo/task-<NN>-<slug>/         multi-phase tasks add -p<N>
    state.md                          phase markers, decisions, progress blocks
    plan.md                           subtasks, dependencies, strategy
    state-archive.md                  archived verbose Discovery evidence
    T-XX-<slug>/description.md         leaf or composite contract
    T-XXa-<slug>/description.md        composite child: sibling directory
    T-XX-fix-<slug>/description.md     top-level validation fix
    T-XXc-fix-<slug>/description.md    composite fix sibling
  tasks/completed/                    completed task records
```

There is no state or plan inside subtask directories. Progress lives in parent state.
Leaf descriptions have six sections: `## Goal`, `## Context`, `## Scope`, `## Steps`,
`## Acceptance Criteria`, `## Test Plan`. Composite descriptions declare `type: composite` and integration criteria;
pass them to composite validation, never atomic execution. Specification changes after
Discovery follow the authorized reconciliation/completion exceptions; implementation
never rewrites requirements to hide a failure.

## Phase 1 — Discovery

`/phase-discovery <spec-path> [--step-by-step] [--phase N]`

Autonomous by default, with research-backed assumptions and scored design decisions.
`--step-by-step` enables review pauses. Orchestrated mode reserves class-B intent
questions for the batch gate. The phase resolves task state, then runs analysis →
decomposition → design → finalization; quick tasks skip decomposition/design/archive.
Outputs: contract and phase markers in state, plus plan and descriptions for full tasks.

## Phase 2 — Execution

`/phase-execution <task-directory>`

Require Discovery complete. For each ready leaf run atomic execution, then independent
atomic validation; resume `done` leaves at validation. Composite containers run no
implementation cycle. Finalize the execution report and proposal decisions before
marking the phase complete. Quick tasks use inline TDD against their quick contract.

## Phase 3 — Validation

`/phase-validation <task-directory>`

Require Execution complete. Verify contract → review code → decide issues → create and
execute approved fixes → finalize, record qualifying decisions and reconcile the spec.
Quick tasks retain contract/review/approval but use inline repairs. Failed invariants or
Off-limits always stop. A deferred item remains visible; it is never reported as delivered.

## Atomic Workflows

```text
/phase-atomic-execution <leaf-description>
  /pae-tests → /pae-implement → /pae-finalize
/phase-atomic-validation <leaf-description>
  /pav-check → /pav-propose → /pav-close
```

Test-first execution: establish RED before GREEN, or admitted characterization (`pinned`)
before preservation work. `none` needs the recorded gate justification. The frozen test
set cannot be deleted, skipped or weakened to pass. Canonical process: `tdd`.
The last reviewed composite child triggers integration validation exactly once; approved
integration fixes are new sibling leaves and keep the composite open until rechecked.

## Status Glossary

Canonical fields and vocabulary: `workflow-globals`; translations and protection:
`workflow-reference`. Distinguish plan status from atomic fields:

| Record | Meaning |
|---|---|
| `atomic-tests: red / pinned / green / n-a / failed` | Observed test evidence, characterization baseline, success, justified absence, or failure to establish valid evidence. Missing field reads `not-started`. |
| Plan `done` | Execution complete; validation still pending. |
| Plan `reviewed` | Execution and validation complete. |
| Composite `reviewed` | All children reviewed and `integration-validation: complete`. |
| `composite-reviewed` | Execution-report summary: children and integration passed. |
| `composite-blocked` | Execution-report summary: a child is blocked. |
| `composite-stalled` | Execution-report summary: reviewed children lack completed integration validation. |

Never copy a plan `done` value into an atomic-status field. Field names, protected lines,
status transitions and backward compatibility come from the canonical rules.

## Child Workflows (Direct Step Access)

Children are callable independently and perform their phase bootstrap when no parent
has loaded context. Their Guards detect completed work before overwrite.

| Group | Commands in execution order |
|---|---|
| Discovery | `/pd-analyze`, `/pd-decompose`, `/pd-design`, `/pd-finalize`, `/pd-archive` |
| Optional model choice | `/pd-select-model` (bulk writes Model; called by `/spec-run`) |
| Execution | `/pe-execute`, `/pe-finalize` |
| Atomic execution | `/pae-tests`, `/pae-implement`, `/pae-finalize` |
| Atomic validation | `/pav-check`, `/pav-propose`, `/pav-close` |
| Composite integration | `/phase-composite-validation` |
| Validation | `/pv-contract`, `/pv-review`, `/pv-issues`, `/pv-create-fixes`, `/pv-execute-fixes`, `/pv-finalize` |
| Fix branch grouping | `/pv-classify-fixes` (called by fix creation in orchestrated mode) |
| Automatic phases | `/phase-pipeline` |
| Context-bounded delivery | `/spec-run`, `/restack` |
| Entry points | `/spec-draft`, `/bugfix`, `/onboard-legacy-project` |
| Knowledge utilities | `/context-pack`, `/compress-state`, `/adr-new`, `/spec-sync`, `/retro` |
| Suggested delivery text | `/suggest-commit-message`, `/suggest-pr-description`, `/suggest-commit-pr` |

## Orchestrated Mode — one spec to review-ready pull requests

`/spec-run <spec-path> [--allow-pr] [--dry-run]`

`orchestration` defines Orchestrator, Arbiter, Implementer and independent Validator.
Workers run sequentially and return shared-file deltas; the Orchestrator owns shared
state and git. Class-B questions are answered before the first branch, and leaks stop.

`git-flow` defines the stack: each leaf branches from its reviewed predecessor. RED
gets a test-only commit before the same Implementer continues to GREEN; justified
`n-a` gets one implementation commit. Composites are containers without branches in the
current model. Later PRs contain their predecessors and depend on them. PRs require
`--allow-pr`, start as drafts and become ready after successful task validation.
The workflow never merges; the human chooses integration timing and strategy.

`/restack <task-directory> [--allow-pr]` repairs the remaining stack using recorded
branch points after integration. Missing branches alone do not prove a merge.

## Utility

`/compress-state [path] [--auto]` preserves protected markers and current decisions.
`/context-pack` verifies its source manifest before cache reuse. `/retro` is the only
run-log reader and recommends workflow changes without applying them.

## Full Cycle Example

```text
/phase-discovery .ai/specs/01-add-oauth.md
/phase-execution .ai/tasks/todo/task-01-add-oauth/
/phase-validation .ai/tasks/todo/task-01-add-oauth/
```

## Quick Start

Create a spec with H1 and acceptance criteria. Configure real verification commands in
the runbook before testable execution. Run the manual cycle above or authorize the
three phases with `/phase-pipeline <spec-path>`. Quick eligibility and promotion are
owned by `quick-flow`; a small diff alone does not qualify.

## Known Limitations

### Type 3 — no whole-group integration validation

Flat capability pairs have **no automatic whole-group integration validation**. When
cross-capability behavior needs checking, add a dedicated integration leaf with its own
criteria and dependency edges; do not assume a composite trigger exists.
