---
description: Reference documentation — not an executable workflow. Contains full pipeline reference guide: file structure, phase steps, child workflow table, cycle examples.
---

# AI-Assisted SDLC Pipeline

Three-phase workflow system: Discovery → Execution → Validation.
Each phase is launched manually via slash command. To re-run a specific step, call its child workflow directly (see *Child Workflows* table below).
Global principles are defined in `workflow-globals` (always-on rule).

---

## How to Pass Task Context

| What to pass | Format | Example |
|---|---|---|
| New task (Discovery) | path to spec file | `.ai/specs/01-add-oauth.md` |
| Task directory (Execution / Validation) | path to task directory | `.ai/tasks/todo/task-01-add-oauth/` |
| Atomic subtask | path to T-XX `description.md` | `.ai/tasks/todo/task-01-add-oauth/T-01-slug/description.md` |
| Specific Discovery step | task directory | `/pd-design .ai/tasks/todo/task-01-add-oauth/` |

For phase-discovery: provide the spec path. Task directory is derived automatically.
For all other phase and child workflow commands: provide the task directory.
Atomic child workflow commands (pae-*, pav-*) still receive T-XX/description.md path.
Task directory = provided argument (trailing slash optional).

---

## Task Structure Types

The pipeline supports three task-structure types, selected autonomously by the classifier in `pd-decompose`. The type is **never** a user-facing mode — it is an emergent property of the decomposition.

| Type | Shape | When used |
|------|-------|-----------|
| **1 — Flat** | All T-XX are leaves; executed sequentially per dependency order | Default for most tasks |
| **2 — Nested** | Some T-XX are composites; each has leaf children (T-XXa, T-XXb, …) that execute individually, then the composite runs integration validation | When a subtask is too large for one atomic cycle (≥2 independently-testable components) |
| **3 — Vertical re-sliced** | Two independent tracks dissolved and re-decomposed into per-capability producer→consumer leaf pairs; interleaved for continuous integration | When two cross-repo tracks share a frozen contract and ≥2 capabilities |

Types 2 and 3 compose: a per-capability pair can itself be a composite if each member is large enough. Depth is capped at 2 (composites at depth 1; their children always at depth 2 as leaves).

---

## File Structure

```
.ai/                                      # project memory, principles, decisions, context

.ai/memory/architecture.md                # system architecture snapshot
.ai/memory/state.md                       # task-level context (active tasks, statuses)
.ai/memory/progress.md                    # chronological log of completed work
.ai/principles/                           # architecture / coding / domain principles
.ai/adr/index.md                          # index of architectural decision records
.ai/context/                              # integrations / environment / runbook

.ai/specs/
  <NN>-<slug>.md                          # task specification — immutable after creation
                                          # consumed by phase-discovery; never in task dir

.ai/tasks/
  todo/
    task-<NN>-<slug>/
      state.md                            # task state + spec_path: + all decisions + phase statuses
                                          #   includes: ## Subtask Progress (one block per T-XX)
                                          #   leaf blocks: T-XX | name | atomic-tests | atomic-execution | atomic-validation
                                          #     (+ branch/base_branch/base_commit/commits/pr in orchestrated mode)
                                          #   composite blocks: [composite] T-XX | name | rollup | integration-validation
      plan.md                             # decomposition: T-XX table + dependencies + strategy
                                          #   flat tasks: ID/Name/KeySteps/DependsOn/Status columns
                                          #   nested/sliced tasks: also Type/Slice columns
                                          #   ## Decomposition Decisions: classifier rationale
      T-XX-<slug>/
        description.md                    # leaf subtask spec (## Goal/Context/Scope/Steps/AC/Test Plan)
      T-XX-<slug>/                        # composite subtask container (Type 2)
        description.md                    # composite spec (## Steps = "See children"; ## AC = integration-level)
      T-XXa-<slug>/                       # child of composite T-XX (flat sibling dir — never nested)
        description.md                    # leaf subtask spec
      T-XXb-<slug>/
        description.md
      T-XX-fix-<slug>/
        description.md                    # validation fix-task spec (top-level fixes)
      T-XXc-fix-<slug>/                   # D8: child fix-task (sibling letter + fix suffix)
        description.md
  completed/
    task-<NN>-<slug>/
```

**Directory rules:**
- Children are flat siblings (T-04a/, T-04b/ alongside T-04/) — no nested directories.
- `state.md` and `plan.md` never appear inside T-XX directories.
- All hierarchy lives in the parent task's `plan.md` and `state.md`.

---

## Phase 1 — Discovery

```
/phase-discovery <path>                   # full cycle (steps 0–4), autonomous
/phase-discovery <path> --step-by-step    # pause for review after each step
```

Discovery is **autonomous by default**: Steps 1–4 run back-to-back without
returning control. Ambiguous requirements are resolved by research
(principles → ADRs → memory → codebase patterns → best practice) and recorded in
`## Task Analysis → ### Assumptions`; architectural choices are made via
`workflow-reference → ## Autonomous Decision Protocol` and recorded as
`### Autonomous Decision`. The phase still stops at its end — it never
auto-advances into `/phase-execution`.

`--step-by-step` restores the interactive behavior: clarifying questions in
`pd-analyze`, user-chosen architecture in `pd-design`, and a review pause after
every step. The flag is passed through to all four child workflows.

To run a single step, call its child workflow directly (e.g. `/pd-design <path>`).

| Step | Name | What it does |
|---|---|---|
| 0 | State check | Read state, determine continuation point |
| 1 | Task analysis | Analyze spec + codebase, set `flow:`, record assumptions (asks only with `--step-by-step`) |
| 2 | Decomposition | Break into T-XX subtasks, create directories |
| 3 | Architectural design | Generate 2–3 variants, decide via the Autonomous Decision Protocol (user decides with `--step-by-step`) |
| 4 | Finalization | Update files, compress, mark complete |

**Output:**
- `state.md` — Goal, Affected Parts, Solution Design, Off-limits, Invariants, Acceptance Criteria
- `plan.md` — T-XX table with statuses and dependencies
- `T-XX-<slug>/` directories with `description.md` only (no `state.md` or `plan.md`).
  `description.md` has six sections: `## Goal`, `## Context`, `## Scope`, `## Steps`,
  `## Acceptance Criteria`, `## Test Plan`.

---

## Phase 2 — Execution

```
/phase-execution <path>              # execute all pending subtasks
```

To run a single step, call its child workflow directly (e.g. `/pe-execute <path>`).

| Step | Name | What it does |
|---|---|---|
| 0 | State check | Verify discovery complete, find first incomplete subtask |
| 1 | Subtask execution | For each T-XX: atomic-execution (tests → implement → finalize) → atomic-validation |
| 2 | Finalization | Summary report, update files, compress |

**Output:**
- Implemented functionality
- Task statuses in `plan.md` (`done` / `reviewed` / `blocked` / `deferred`)
- `## Subtask Progress` blocks updated in parent `state.md`

---

## Phase 3 — Validation

```
/phase-validation <path>             # full validation
```

To run a single step, call its child workflow directly (e.g. `/pv-issues <path>`).

| Step | Name | What it does |
|---|---|---|
| 0 | State check | Verify execution complete |
| 1 | Contract verification | Check Invariants, Acceptance Criteria, Off-limits |
| 2 | Code review | Readability, security, edge cases |
| 3 | Issue list | Numbered list with priorities, wait for user |
| 4 | Create fix-tasks | New T-XX subtasks from approved issues |
| 5 | Execute fix-tasks | Atomic cycles for each fix-task |
| 6 | Finalization | Update files, compress, list deferred tasks |

**Output:**
- Fix-tasks created and executed
- Deferred tasks listed
- Clean, compressed state files

---

## Atomic Workflows

For each T-XX subtask. Launched automatically by `/phase-execution` and `/phase-validation`, or manually by user.

```
/phase-atomic-execution <T-XX-path>     # orchestrator: implement (reads T-XX/description.md)
/phase-atomic-validation <T-XX-path>    # orchestrator: validate + close
/phase-composite-validation <T-XX-path> # orchestrator: integration validation for composites
                                        #   called automatically by pav-close when last child closes
```

The atomic execution cycle is **test-first**:

```
/phase-atomic-execution
  1. /pae-tests      RED   — classify test level, write failing tests from ## Acceptance
                             Criteria, run them, observe them fail for the right reason
  2. /pae-implement  GREEN — implement until every RED test passes, then refactor
  3. /pae-finalize           record statuses, roll up composites
```

The RED test set is a frozen contract during GREEN: it may not be deleted, skipped, or
weakened to make the implementation pass. Work with no testable behaviour passes an explicit
test-level gate (`unit` / `integration` / `contract` / `smoke` / `none`) with a recorded
justification — it is never skipped silently. Contract → the `tdd` rule; test style →
`testing-standards`.

All per-subtask implementation detail (`## Steps`, `## Acceptance Criteria`, `## Test Plan`) lives in `T-XX/description.md`, produced during parent `/pd-decompose` + `/pd-finalize`. T-XX directories contain only `description.md` — no `state.md` or `plan.md`. All progress tracking is in the parent `state.md → ## Subtask Progress`.

For composites: `T-XX/description.md` contains `type: composite` in `## Context` and integration-level criteria in `## Acceptance Criteria`. It is never passed to `phase-atomic-execution` — only to `phase-composite-validation`.

---

## Status Glossary

**TDD statuses** (`atomic-tests:` field in leaf `## Subtask Progress` blocks):

| Status | Meaning |
|--------|---------|
| `not-started` | `/pae-tests` has not run. A block with no `atomic-tests:` field is pre-TDD and reads as this |
| `red` | Tests written, run, and observed failing for the expected reason |
| `green` | Implementation complete; the whole RED set passes and is intact |
| `n-a` | Test-level gate returned `none`, with a justification recorded in `notes:` |
| `failed` | RED could not be established — a test passed before implementation, or the suite errored |

**Leaf subtask statuses** (used in `plan.md` Status column and leaf `## Subtask Progress` blocks):

| Status | Meaning |
|--------|---------|
| `not-started` | Subtask has not been touched |
| `in-progress` | Atomic execution is running |
| `done` | Atomic execution complete, atomic validation not yet run |
| `reviewed` | Atomic execution + validation both complete |
| `blocked` | Cannot proceed — external dependency or invariant conflict |
| `deferred` | User chose to defer this subtask |
| `not-reached` | Pipeline did not reach this subtask in the current run |

**Composite subtask statuses** (used in `plan.md` Status column and composite `## Subtask Progress` blocks):

| plan.md Status | rollup field | integration-validation | Meaning |
|----------------|--------------|----------------------|---------|
| `not-started` | `not-started` | `not-started` | No children have started |
| `in-progress` | `in-progress` | `not-started` | At least one child is executing |
| `done` | `done` | `not-started` | All children done; integration validation not yet run |
| `in-progress` | `done` | `in-progress` | Integration validation running |
| `in-progress` | `done` | `failed` | Integration validation failed; fix cycle pending |
| `reviewed` | `done` | `complete` | All children reviewed AND integration validation passed |
| `blocked` | `blocked` | — | At least one child is blocked |

A composite's `plan.md` Status reaches `reviewed` ONLY after `integration-validation: complete`.

**Execution Report composite statuses** (in `## Execution Report`):
- `composite-reviewed` — all children reviewed, integration validation passed
- `composite-blocked` — at least one child blocked
- `composite-stalled` — all children reviewed but integration validation never triggered

Phase statuses used in `state.md → ## Phases`:

| Status | Meaning |
|--------|---------|
| `not-started` | Phase has not been entered |
| `in-progress` | Phase is currently executing |
| `complete` | Phase fully finished |

---

## Child Workflows (Direct Step Access)

Call any step directly without running the full phase.

| Slash command | Phase | Step |
|---|---|---|
| `/pd-analyze` | Discovery | 1 — Task analysis + codebase |
| `/pd-decompose` | Discovery | 2 — Decompose into T-XX |
| `/pd-design` | Discovery | 3 — Architectural design |
| `/pd-finalize` | Discovery | 4 — Finalize + compress |
| `/pd-archive` | Discovery | 4b — Archive verbose Discovery content (called by `/pd-finalize`) |
| `/pd-select-model` | Discovery | 2.5 — Model per subtask (opt-in; called by `/spec-run`, not by `/phase-discovery`) |
| `/pe-execute` | Execution | 1 — Run atomic cycles |
| `/pe-finalize` | Execution | 2 — Summary + finalize |
| `/pv-contract` | Validation | 1 — Contract verification |
| `/pv-review` | Validation | 2 — Code review |
| `/pv-issues` | Validation | 3 — Issue list for user |
| `/pv-create-fixes` | Validation | 4 — Create fix-tasks |
| `/pv-execute-fixes` | Validation | 5 — Execute fix-tasks |
| `/pv-finalize` | Validation | 6 — Finalize |
| `/pae-tests` | Atomic Execution | 1 — TDD RED: test-level gate + failing tests from AC |
| `/pae-implement` | Atomic Execution | 2 — TDD GREEN: execute steps until tests pass (includes tripwire check) |
| `/pae-finalize` | Atomic Execution | 3 — Update statuses + incremental composite rollup |
| `/pav-check` | Atomic Validation | 1 — Final check + verdict |
| `/pav-propose` | Atomic Validation | 2 — Improvement proposals |
| `/pav-close` | Atomic Validation | 3 — Close task + trigger composite integration validation |
| `/phase-composite-validation` | Composite Validation | Integration check after all children reviewed |
| `/pv-classify-fixes` | Validation | 4a — Classify fixes into shared vs dedicated branches |
| `/spec-run` | Orchestrated | Whole spec → stacked branches → review-ready PRs |
| `/restack` | Orchestrated | Replay the branch stack after the human merges part of it |

---

## Orchestrated Mode — one spec to review-ready pull requests

```
/spec-run .ai/specs/01-add-oauth.md              # local only — branches, no PRs
/spec-run .ai/specs/01-add-oauth.md --allow-pr   # also push and open draft PRs
/spec-run .ai/specs/01-add-oauth.md --dry-run    # print the plan, change nothing
```

`/spec-run` carries one spec through Discovery → Execution → Validation using
context-bounded sub-agents, creating one stacked git branch per subtask. Single repository
only — a spec covers exactly one repo.

**Roles** (`orchestration` rule): the Orchestrator owns sequencing, git, and every shared
file; the Arbiter holds full project context for the whole run and answers questions only
with a cited source; the Implementer runs one subtask's `pae-tests` → `pae-implement` →
`pae-finalize`; a **separate** Validator runs `pav-check` → `pav-propose` → `pav-close`
without having seen how the code was written.

Sub-agents exist to bound context, **not** to parallelize. Execution is strictly
sequential — `## Subtask Progress` has no locking.

**The branch stack** (`git-flow` rule): subtask N branches from the tip of subtask N-1. The
stack tip holds the whole task, so task-level validation runs there and no separate
integration branch exists. Consequence, stated plainly: a PR cannot reach the base branch
without its predecessors. The human chooses the merge strategy and the timing; `/restack`
repairs the stack afterwards regardless of which strategy was used.

**The one planned stop** is the Discovery batch gate. `/pd-analyze` splits ambiguities into
class A (answerable from principles / ADRs / codebase — resolved autonomously with a cited
source) and class B (missing product intent — nobody can derive it). Class B is collected
into `## Open Questions (batch)` and presented to the human as a single list *before the
first branch is created*. After it clears, Execution runs unattended.

```
/restack .ai/tasks/todo/task-01-add-oauth/            # replay the stack after a merge
/restack .ai/tasks/todo/task-01-add-oauth/ --allow-pr # and update the open PRs
```

`/restack` replays each remaining branch with `git rebase --onto <new-base> <base_commit>`,
which is why `base_commit` is recorded at branch creation and never recomputed — after a
squash merge the computed merge base is wrong.

---

## Utility

```
/compress-state [path]               # compress specific state file
/compress-state                      # compress .ai/memory/state.md (default)
```

---

## Full Cycle Example

```
# WRITE SPEC
# Create .ai/specs/01-task-foo.md with H1 title and Acceptance Criteria

# PHASE 1 — DISCOVERY
/phase-discovery .ai/specs/01-task-foo.md

# PHASE 2 — EXECUTION
/phase-execution .ai/tasks/todo/task-01-task-foo/

# PHASE 3 — VALIDATION
/phase-validation .ai/tasks/todo/task-01-task-foo/

# MANUAL ATOMIC (single T-XX):
/phase-atomic-execution  .ai/tasks/todo/task-01-task-foo/T-01-slug/description.md
/phase-atomic-validation .ai/tasks/todo/task-01-task-foo/T-01-slug/description.md

# MANUAL TDD STEP ONLY (re-run RED for one subtask):
/pae-tests .ai/tasks/todo/task-01-task-foo/T-01-slug/description.md
```

---

## Quick Start

1. Create `.ai/specs/01-task-foo.md` with at minimum an H1 title.
2. Fill in `test:` under `.ai/context/runbook.md → ## Commands` — the TDD step stops without it.
3. Run `/phase-discovery .ai/specs/01-task-foo.md` — creates task directory automatically.
4. Run `/phase-execution .ai/tasks/todo/task-01-task-foo/`.
5. Run `/phase-validation .ai/tasks/todo/task-01-task-foo/`.

---

## Known Limitations

### Type 3 — no whole-group integration validation

D1 (composite validation: per-child AND whole-series) applies to **composites** (Type 2). Type 3 re-slicing intentionally does NOT create a composite parent — all capability slices are flat leaves. Therefore there is **no automatic whole-group integration validation** across all Type 3 slices.

**Rationale:** Type 3 is designed for tasks where the slices are developed independently per capability, with each capability's producer→consumer pair verified end-to-end. A cross-capability integration concern should be modelled as a separate subtask (e.g. a shared-setup leaf with its own Acceptance Criteria, or a follow-on integration T-XX) rather than by adding a composite wrapper.

**If cross-capability integration validation is required:** model it explicitly as a dedicated leaf subtask with its own `## Acceptance Criteria` that verifies the combined result, added to `plan.md` as a dependency of any downstream work.
