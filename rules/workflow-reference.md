---
trigger: model_decision
description: Workflow process reference — load when using any /phase-* or child workflow slash command.
---

# Workflow Process Reference

Canonical status formats (`## Phases`, subtask statuses) live in `workflow-globals` (always-on). This file owns file responsibilities, protection, amendments and decision protocols; it also provides extended examples.

## File Responsibility

**Parent task directory (`.ai/tasks/todo/task-<NN>-<slug>/`):**
- `state.md` — current state, all decisions (including architectural), phase statuses,
  execution report, fix-tasks marker, `## Subtask Progress` (per-T-XX atomic execution/
  validation status). Contains `spec_path:` field pointing to the original spec.
- `plan.md` — decomposition only: subtask table (with `Key Steps` column), dependencies,
  execution strategy. No architectural decisions.

Task specification lives in `.ai/specs/<NN>-<slug>.md` — immutable after creation.
The task directory contains no top-level `description.md`. To read the original task
statement, follow `spec_path:` in `state.md`.

**Controlled exceptions:** `/pv-finalize` prepares `status: done`, `completed_task:`
and `completed_at:` in step 2.5 and merges them into existing frontmatter only after
successful final checks and reconciliation. This is a completion marker, not a change to the task statement. Preserve unrelated frontmatter fields;
existing frontmatter alone does not mean completion. `/spec-sync` may reconcile content
at verified finalization, after Validation, or under explicit user authorization.
Failed acceptance criteria remain defects and must never be weakened by reconciliation.
During implementation, requirement changes use the Description Amendment procedure on
subtask descriptions; they do not silently alter the source spec.

**Subtask directory (`T-XX-<slug>/`):**

Each T-XX directory contains exactly ONE file: `description.md`.

`description.md` structure (T-XX level):
```
## Goal
One sentence describing the done-state of this subtask.

## Context
Why this subtask exists, dependencies on other T-XX, constraints.

## Scope
In scope, out of scope, and the target files this subtask creates or modifies.
Read by `/pae-implement` before any code is written — a missing `## Scope` stops it.

## Steps
Numbered implementation steps (3–15 items).
Each step must be atomic enough to verify but grouped by domain, not by file operation.

## Acceptance Criteria
Explicit, checkable conditions that define completion.
These are used verbatim during atomic-validation.

## Test Plan
Test level (unit | integration | contract | smoke | none), one scenario per Acceptance
Criterion, applicable edge-case categories, and — when the level is `none` — the
justification. Consumed by `/pae-tests` to write the failing tests before implementation.
```

`plan.md` and `state.md` are NOT created at the T-XX level.
All progress tracking lives in the parent task's `state.md → ## Subtask Progress`.
All step listings live in the parent task's `plan.md` table (summary) and in `T-XX/description.md → ## Steps` (full).

## Description Amendment

The spec file (`.ai/specs/<NN>-<slug>.md`) may be amended after creation only when:
- A requirement turns out to be technically impossible as stated.
- Discovery reveals a fundamental misunderstanding of the task scope.
- User explicitly decides to change the task definition mid-execution.

**Amendment procedure:**

Do NOT edit the spec file directly. (The completion frontmatter written by `/pv-finalize`
step 2.5 is not an amendment and is not covered by this prohibition.) Post-validation
`/spec-sync` and explicit owner-authorized reconciliation are controlled content-edit
exceptions under File Responsibility; neither may weaken a failed criterion.
Add a `### Description Amendments` section to the task-level `state.md`:

```
### Description Amendments
- [date if known] <what changed and why>
- Original: <original statement>
- Amended: <new statement>
```

Treat the amended version as authoritative for all subsequent workflow steps.
If decomposition (T-XX subtasks) is affected — re-run `/pd-decompose` after recording the amendment.

Amendments are a permanent record — never delete them from `state.md`.

---

## Parent `plan.md` Table Format

### Model columns and resolution

Optional model columns: `Model (Claude)` maps to provider `anthropic`; `Model (Codex)`
maps to `openai`. Read columns by header, never position. A legacy `Model` cell applies
to the active provider only when its provider column is absent. A present empty provider
cell overrides legacy and requests the session default. Missing model columns also use
the session default visibly. Preserve unknown columns, statuses, row order, unrelated
Markdown and composite blank cells.

Bulk updates use `--update-plan PLAN --updates UPDATES.json`. When adding columns to a
populated legacy table, supply an explicit value or intentional `null` for every newly
added provider on every populated legacy row. Never infer that one legacy ID works for
both providers or silently clear an existing request. A changed scope makes any populated
model cell stale; rerun bulk selection before requesting a model for that scope.

Before any model-specific request, resolve the leaf through this contract:

1. Observe fresh support for this invocation from the actual exposed model-selection
   tool, its accepted identifiers, context limits, tool permissions and restrictions,
   plus current owner constraints. Set `harness.date` to today and retain an observation
   reference. A same-day date alone does not establish invocation-specific provenance.
   Catalog TTL is not proof of support. Provider names are not proof of support.
   Logging capability files are not proof of support. Unknown availability, context or
   tools cannot authorize a request; filter support, context, tools, owner limits,
   independent quality and traits before considering economics.
2. Read the active provider with `--read-plan PLAN --provider PROVIDER`. Resolve with
   `--catalog CATALOG --today YYYY-MM-DD --resolve-plan PLAN --provider PROVIDER
   --row ID --resolution REQUEST.json`. The resolution input contains `selection`,
   `fallback` and `execution`; the helper derives the requested ID from the plan.
   Use `execution: null` during recommendation and resolution. The complete schemas
   and runnable fictional examples are in [the catalog guide](../docs/MODEL-CATALOG.md).
3. Display requested, resolved and actual identities, status and reasons separately.
   An unsupported explicit request requires an independently eligible declared fallback
   that is authorized, or a visible stop. The helper never substitutes an undeclared
   model or executes one. Missing helper/Python/catalog/support reports selection
   unavailable and preserves session configuration. Never bypass explicit-request
   eligibility because selection is unavailable: independently establish eligibility
   and an authorized fallback, or stop before model-specific execution. With no explicit
   request, ordinary work may remain in the same session without claiming selection.
4. Request only the authorized resolved identity when the current tool can select it.
   An inline executor cannot switch its own model by editing a plan; retain the current
   session visibly. Actual remains unknown (`null`) without a separate current execution
   receipt matching the authorized resolved provider/ID and this execution context.
   The caller owns receipt provenance; helper checks of date/reference/identity do not
   authenticate an observation. Successful spawn alone is insufficient, as are plan
   cells, recommendations, tool arguments and dispatch acceptance. Never create a receipt
   from those inputs. A later observed receipt may be supplied separately; do not read
   historical stores directly to infer actual identity or calibrate estimates.

### Base table example

```
## Subtasks

| ID   | Name | Key Steps (summary)                              | Depends On | Status       |
|------|------|--------------------------------------------------|------------|--------------|
| T-01 | ...  | create variables.tf → terraform fmt → validate   | —          | not-started  |
| T-02 | ...  | ...                                              | T-01       | not-started  |
```

`Key Steps` — short inline list (separated by `→`) of the main steps of the subtask.
Example: `create variables.tf → terraform fmt → validate outputs`.
Detailed steps live in `T-XX/description.md → ## Steps`.

## Parent `state.md` — `## Subtask Progress` Format

One block per T-XX:

```
T-XX | <name> | atomic-tests: <status> | atomic-execution: <status> | atomic-validation: <status>
  last_action: <one line — what was done last>
  target_files: <comma-separated list of files modified, test files included — write even when empty>
  blocker: <none | description of blocker>
  notes: <key decisions or deviations — write even when empty>
  branch: <branch name — orchestrated mode only>
  base_branch: <branch this one was cut from — orchestrated mode only>
  base_commit: <sha of the branch point — orchestrated mode only>
  commits: <sha <type>: <summary>, ... — orchestrated mode only; the commit scope is a feature or module name, never a subtask identifier (see `git-flow`)>
  pr: <#N draft | #N ready | none — orchestrated mode only>
```

The five git fields appear only under `/spec-run`; ordinary manual runs omit them and no
reader may require them. See `git-flow` for how they are produced and `orchestration` for the
role that writes them.

Status values for atomic-execution / atomic-validation: `not-started` | `in-progress` | `complete` | `blocked` | `skipped` | `failed`.
Status values for `atomic-tests`: `not-started` | `red` | `pinned` | `green` | `n-a` | `failed` — semantics in the `tdd` rule. `pinned` is characterization mode: tests that pin existing behaviour and pass before a behaviour-preserving change; it transitions only to `green`. A block without the field is a pre-TDD task; read it as `not-started` and never error on its absence.

## Status Lifecycle Notes

- `not-started` → `red` when `/pae-tests` writes failing tests and observes them fail
  (`n-a` when the test-level gate returns `none` with a recorded justification).
- `red` → `green` when `/pae-implement` reaches Final Verification with the whole RED set
  passing and intact.
- `not-started` → `in-progress` when atomic-execution begins.
- `in-progress` → `done` when atomic-execution completes.
- `done` → `reviewed` when atomic-validation passes.
- `blocked` vs `deferred`: `blocked` is an external dependency issue (data, infra, upstream team); `deferred` is an explicit user decision to postpone.
- `not-reached` is set by `/pe-finalize` for subtasks present in `plan.md` but absent from `## Execution Report` (usually due to session interruption or earlier blocker).

## Key State-File Markers

Markers are read by orchestrators to determine continuation points:

- `## Task Analysis` — written by `/pd-analyze`.
- `## Subtask Progress` — written and updated by `/pae-tests`, `/pae-implement`, `/pae-finalize`, `/pav-check`, `/pav-propose` (`notes:` only), `/pav-close`; git fields by `/spec-run` and `/restack`.
- `## Improvement Proposals (T-XX)` — written by `/pav-propose`, read by `/pe-finalize` step 5.
- `## Open Questions (batch)` — class-B ambiguities collected by `/pd-analyze` in orchestrated mode, cleared by `/spec-run` after the human answers.
- `## Decomposition` with `decomposition: complete` — written by `/pd-decompose`.
- `## Solution Design` with `### Decision` — written by `/pd-design`.
- `## Execution Report` — written by `/pe-execute`, finalized by `/pe-finalize`.
- `## Contract Check` with optional `### Critical Failures Decision` — written by `/pv-contract`.
- `## Code Review`, `## Issue List` — written by `/pv-review`, `/pv-issues`.
- `## Fix-Tasks` with `fixes-created: complete` + `fixes-count: <N>` — written by `/pv-create-fixes`.
- `## Deferred` — written by `/pv-finalize`.

---

## Reference Tables (moved from workflow-globals)

## Status Translation Table

When updating `plan.md` after atomic-execution or atomic-validation completes,
use this table to translate atomic status → plan.md Status column:

| Atomic status (## Subtask Progress) | plan.md Status column | When |
|--------------------------------------|-----------------------|------|
| `red` / `pinned` / `n-a` (atomic-tests) | `in-progress`      | After pae-tests — the subtask is underway, not done |
| `complete` (atomic-execution)        | `done`                | After pae-finalize |
| `complete` (atomic-validation)       | `reviewed`            | After pav-close |
| `blocked`                            | `blocked`             | Direct match |
| `skipped`                            | `not-reached`         | No atomic run occurred |
| `failed`                             | `blocked`             | Validation failed, needs fix-task |

Rule: `failed` has no direct plan.md equivalent — treat as `blocked` in plan.md
and record the failure reason in the `## Execution Report`.

---

## Protected Sections Contract

The following sections are contracts read by orchestrators and must never be removed, renamed, or summarized by `/compress-state` or any other workflow.

**Task-level `state.md`:**
- `## Phases` (top-level and atomic)
- `## Task Analysis`
- `## Task Analysis → ### Assumptions` (decisions taken autonomously — never removed, never archived by `/pd-archive`)
- `## Decomposition` (including `decomposition: complete` marker)
- `## Solution Design` (Invariants, Off-limits, Acceptance Criteria, Decision, Scope)
- `## Subtask Progress`
- `## Execution Report`
- `## Contract Check` (including `### Critical Failures Decision`)
- `## Code Review`
- `## Issue List`
- `## Fix-Tasks` (including `fixes-created` marker and `fixes-count` field)
- `## Deferred`
- `## Spec Phases` (multi-phase specs only — phase roadmap; never remove)
- `### Description Amendments` (if present — permanent record, never remove)
- `## Contract (quick)` (quick tier only — the whole contract for the task lives here;
  including `### Off-limits` / `### Invariants` / `### Acceptance Criteria`. Read by
  `/pv-contract` and `/pv-review`)
- `## TDD (quick)` (quick tier only — the RED/GREEN record `/pv-review` audits)
- `## Flow Escalation` (if present — the recorded `quick → full` promotion; never remove)
- `## Improvement Proposals (T-XX)` (written by `/pav-propose`, read by `/pe-finalize` after
  the execution phase — removing it loses the batched `Do Now` items before they are surfaced)
- `## Integration Issues (T-XX)` (written by `/phase-composite-validation` step 2d — the
  recorded approve/defer decision for integration failures; read by its own step 3 when creating
  D8 fix siblings and on every re-run, so it must survive compression)
- `## Open Questions (batch)` (orchestrated mode only — class-B ambiguities awaiting a human
  decision. The header and its entries may be cleared only by `/spec-run`, after the human has
  answered; no other workflow may remove or summarize them)
- Top-of-file lines that must never be removed or modified:
  - `spec_path:` — pointer to the original spec file
  - `flow:` — the tier selector (`quick` | `full`) set during Discovery
  - `active_phase:` — active spec phase number (multi-phase only)
  - `spec_phase_count:` — total number of spec phases (multi-phase only)

## Multi-Phase Spec Rules

When a spec defines ≥2 phase markers (`## Phase N` or `### Phase N` headings),
`/phase-discovery` enters multi-phase mode:

**Invocation argument `--phase N`**
Pass `--phase N` to target a specific phase. If omitted, the lowest phase number
with no existing task directory is selected automatically.

**Task directory naming**
- Single-phase (0–1 phase markers): `task-<spec-basename>/`
- Multi-phase: `task-<spec-basename>-p<N>/` where N is the active phase number.
  Example: spec `client-issue-13.md`, phase 2 → `task-client-issue-13-p2/`

Each phase gets its own task directory and runs through a full Discovery →
Execution → Validation cycle independently. Subsequent phases are started with
`/phase-discovery <spec_path> --phase <N+1>` after the previous phase completes
validation.

---

**Composite-specific protected lines (within `## Subtask Progress`):**
- `[composite]` prefix line — identifies the block as a composite; must not be removed or relabeled
- `children:` line — list of leaf IDs; must not be removed
- `rollup:` field — derived execution status; must not be removed
- `integration-validation:` field — must not be removed

**`plan.md`:**
- `## Subtasks` table and all `Status` column values
- `Type` column values — must not be removed when present
- `Slice` column values — must not be removed when present
- `## Decomposition Decisions` section — must not be removed or summarized (classifier rationale record)

**Protected fields — never remove even when empty:**
- `notes:` — required field in `## Subtask Progress` (both leaf and composite blocks)
- `target_files:` — required field in leaf `## Subtask Progress` blocks
- `blocker:` — required field in composite `## Subtask Progress` blocks
- `atomic-tests:` — required field in leaf `## Subtask Progress` blocks once `/pae-tests` has
  run; never removed, never downgraded to an earlier state by a later workflow
- `notes:` lines beginning with `tdd:` — the TDD audit trail (test level, `none`
  justification, test amendments). Never removed or summarized.
- `branch:`, `base_branch:`, `base_commit:`, `commits:`, `pr:` — the git audit trail in
  orchestrated mode. Only `/restack` may rewrite `base_commit` and `commits`; no workflow may
  remove them. `base_commit` cannot be recovered once the parent branch is squash-merged and
  deleted, so losing it makes the branch stack unrepairable.
- `notes:` lines beginning with `arbiter:` — recorded class-A resolutions with their source
  citation (`orchestration`). Never removed or summarized.

Inside a protected section, stale bullet points may be shortened, but headers and marker lines must remain verbatim.

---

## .ai/memory/state.md Entry Format

When any workflow updates `.ai/memory/state.md`, use this exact format for task status entries under `## Active Tasks`:

```
[task-id / task-name] | phase: <discovery|execution|validation> | status: <in-progress|complete|blocked|reviewed> | note: <one line — what changed>
```

Examples:
```
task4b_integration_test | phase: validation | status: complete | note: all subtasks reviewed, no deferred items
task5_auth_layer | phase: execution | status: blocked | note: waiting for client GCP credentials
task6_billing | phase: discovery | status: in-progress | note: decomposition complete, design pending
```

When a task reaches `validation: complete` with no deferred items:
- Move its entry from `## Active Tasks` to `## Done` (create section if absent).
- Format: `- [task-id] | completed | note: <one line summary of what was delivered>`

**Sections and where each status lives.** The file carries exactly three task sections, and each
one has a writer: `## Active Tasks` (every task in flight, written by the phase finalize
workflows), `## Done` (written by `/pv-finalize`), and `## Deferred` (written by `/pd-finalize`
for later phases of a multi-phase spec, and by `/pv-finalize` for deferred items). There is no
`## Blocked` section: `blocked` is a `status:` value **inside** an `## Active Tasks` entry, which
keeps a blocked task in the list a reader actually scans. Do not add a section no workflow
writes — `/compress-state` cannot distinguish an empty section from a stale one.

**Upsert rule:** if the task entry already exists — update it in place. If it does not exist — append to the relevant section. Never create duplicate entries for the same task.

---

## .ai/project_state.md Update Rules

`project_state.md` answers "what exists in the codebase right now?" — technical inventory, not task progress.
Update it surgically at each phase boundary. If the file does not exist — skip without error.

| Phase complete | Section(s) to update | What to write |
|---|---|---|
| discovery | `## In-flight work` | Add entry for this task: planned modules, endpoints, architecture changes. Code does not yet exist. |
| execution | `## Module inventory`, `## HTTP surface`, `## In-flight work` | Add/update implemented modules with key exports; add/update new endpoints; remove the in-flight entry for this task. |
| validation | `## Module inventory`, `## What doesn't exist` | If deferred items affect the system boundary — add them to `## What doesn't exist` with `planned but deferred` note. If no deferred items — no update required. |

**Update principle:** surgical edits only — never rewrite unrelated sections. Describe system state factually: what exists, what it exports, what it exposes. Do not write task IDs, phase statuses, or progress information in `project_state.md` — that belongs in `.ai/memory/state.md`.

---

## Autonomous Decision Protocol

Canonical definition. Used by any workflow running in autonomous mode
(`/phase-pipeline` at all times; `/phase-discovery` unless `--step-by-step`
is passed) whenever an architectural or design choice is required. It replaces
"present options, wait for user" at that decision point.

### Step 1 — Generate variants (2–3)
Describe each variant with approach summary, advantages, disadvantages, risks.

### Step 2 — Score on 5 lenses (1–5, higher = better)

| Lens | Question to answer |
|---|---|
| **Simplicity** | How much new code, concepts, or abstractions does this add? Fewer = better. |
| **Reversibility** | How hard is it to change this decision later without breaking things? Easier = better. |
| **Codebase fit** | How well does it align with patterns, standards, and abstractions already present in the repo? |
| **Testability** | How easy is it to write fast, deterministic, isolated tests for this? |
| **Blast radius** | How many existing files / modules need to change? Fewer = better. |

Scoring inputs, in priority order: `.ai/principles/*`, `.ai/adr/` (past decisions
on the same subject are binding unless the task explicitly supersedes them),
`.ai/memory/architecture.md`, patterns already present in the codebase, and
only then general best practice.

### Step 3 — Apply anti-overengineering filter
If the highest-scoring variant introduces an abstraction or pattern NOT already
present in the codebase, verify it solves a *current, concrete* problem stated in
the task description — not a hypothetical future one. If it only addresses a
hypothetical, reduce its Simplicity score by 2 before totalling.

### Step 4 — Select winner
Highest total score wins. On a tie → the simpler variant wins (lowest
Simplicity-score variant is eliminated). If still tied → the variant with best
Codebase fit wins.

### Step 5 — Check escalation threshold
Escalate to the user (pause and wait) ONLY when:
- A hard blocker appears that cannot be resolved without external information
  (missing secret, unavailable external service, requirement with no reasonable default).
- The decision would break an external API contract already consumed by clients.
- Two or more variants score identically on all 5 lenses AND have fundamentally
  different user-visible trade-offs that the simplicity tie-breaker cannot resolve.

Anything else → decide and continue. Do not escalate merely because a choice
feels significant.

### Step 6 — Document decision
Write the standard `## Solution Design` sections, and add inside it:

```
### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | N | N | N | N | N | N |
| Variant 2 | N | N | N | N | N | N |

**Winner:** Variant X — <one-sentence rationale>
**Anti-overengineering check:** passed / adjusted (reason)
**Evidence:** <principles / ADRs / codebase patterns that drove the scores>
```

---

## Autonomous Subtask Classifier

Called by `pd-decompose` after producing the initial candidate list. The AI decides whether each candidate becomes a leaf, a composite (Type 2), or part of a vertical re-slice (Type 3). **No user prompt is issued for this decision.** The rationale is recorded in `plan.md → ## Decomposition Decisions`.

### Signals (compute per candidate subtask)

| Signal | Definition |
|--------|-----------|
| S1 | Number of implementation steps in `## Steps` |
| S2 | Count of independently-testable components — groups of work that each have their own verifiable done-state and could be validated in isolation |
| S3 | Count of distinct capabilities or domain areas covered (each with its own meaning to the system) |
| S4 | Boolean — does the subtask span cross-repo work or reference a shared frozen external contract? |
| S5 | Count of separable Acceptance Criteria clusters — groups of AC items that test distinct components, where each cluster can pass/fail independently |

### Classification rules (evaluated in order)

S1, S2, S3 and S5 are nonnegative integer counts; S4 is boolean. Resolve uncertain
component/criteria groupings before classification. Apply these steps in order:

1. **Type 3 — vertical re-slice pairs first.** Consider pairs whose S4 is true and
   that reference the same shared frozen contract. Re-slice only when each track has
   S1 > 8 or S2 ≥ 2, the contract defines their interface, and S3 ≥ 2 shared capabilities
   provide a split. This takes priority over Type 2 nesting.
   - Extract work shared across ALL capabilities into one prerequisite leaf; never
     duplicate contract/schema/common infrastructure work into each capability.
   - When Type 3 applies, emit a producer leaf and consumer leaf per capability; derive those roles
     from the contract, not client/server labels. Consumer Depends On producer.
   - Let `base = min(AA, BB)`. Capability i gets `T-(base+i-1)a` (producer) and
     `T-(base+i-1)b` (consumer). Shift `base` upward by 1 until the full range is free
     of colliding IDs belonging to non-dissolved subtasks. Record capability names in plan Slice.
2. **Leaf-health invariant.** Classify remaining candidates, including generated slices:
   a leaf requires S2 = 1 AND S5 = 1. Size uncertainty alone does not force nesting.
3. **Type 2 — nest into composite** when S2 ≥ 2 AND S5 ≥ 2. Create sibling child
   directories T-XXa, T-XXb, …, each with one component and one coherent AC cluster;
   the parent owns integration-level criteria.
4. **Mismatched clusters.** If only S2 or S5 exceeds 1, align criteria with testable
   components and recount. Merge genuinely inseparable work; otherwise split criteria
   and steps into coherent siblings. Never retain an unhealthy leaf.
5. **Depth-2 cap.** A composite's children are leaves. Redistribute an unhealthy child
   across more sibling children rather than nesting a third tier. Merge undersized work
   only when it remains one testable component; preserve acceptance coverage and the
   Decomposition Rules below.

### Runtime self-correction (tripwire)

During atomic execution of a leaf (`pae-implement`), if any of these conditions arise:
- Steps balloon: more implementation steps are discovered than originally listed, crossing the leaf-health boundary.
- A second independently-testable component appears that was not anticipated during decomposition.
- Acceptance Criteria actually split into two or more independent verifiable clusters.

Then invoke the **Composite Promotion Protocol**:
1. Stop current atomic execution immediately.
2. Re-classify the current leaf as a composite. Update its `description.md → ## Context` to add `type: composite`.
3. Redistribute the leaf's steps into sibling children: create T-XXa, T-XXb, … directories with `description.md` files containing the redistributed steps and scoped AC.
4. Update `plan.md`: change the T-XX row `Type` to `composite`; add child rows (T-XXa, T-XXb, …) with `Type: leaf`.
5. Update `state.md → ## Subtask Progress`: replace the leaf block with a composite block; add leaf blocks for each child.
6. Depth-2 cap holds — do not promote a child of a composite.
7. Stop after recording the promotion and preserve existing test evidence. In orchestrated mode, return shared-artifact deltas instead of writing them. Report the proposed first child (T-XXa) and wait for the required promotion decision; do not start it automatically.

### Decision record format (written to `plan.md → ## Decomposition Decisions`)

```
## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-XX | leaf | S1=N, S2=1, S5=1 | Single coherent component; fits one atomic cycle |
| T-YY | composite (Type 2) | S1=N, S2=3, S5=3 | Three independently-testable components, three AC clusters |
| T-YY + T-ZZ | Type 3 re-slice | S4=true, S3=3 | Cross-repo pair sharing frozen contract with 3 capabilities; D6 conditions met |
```

---

## Decomposition Rules

A subtask (T-XX) must represent a logical unit of work, not an individual operation.

Criteria for a valid subtask:
- Groups related operations around a single domain or module
  (e.g., "Terraform staging module" — NOT "create variables.tf" + "create outputs.tf" as separate tasks)
- Contains between 3 and 15 implementation steps internally
- Is independently verifiable (has a clear done-state)
- Is NOT split by operation type (create / configure / validate must live together inside one subtask)

Decomposition limits:
- Target 8 subtasks per task (soft guidance, not a hard limit)
- If natural decomposition produces more than 8, compare coherent merges with splitting the task. In `--step-by-step` mode, present both options and wait for explicit user decision. In autonomous Discovery, use the Autonomous Decision Protocol and record the choice; do not merge unrelated components merely to reach 8.
- If a candidate has fewer than 3 steps, merge it only with a coherent neighbor that
  preserves one testable component and one AC cluster. If no such merge exists, re-slice
  the boundaries through the Autonomous Decision Protocol. If the minimum and leaf-health
  constraints cannot both hold, stop and report that conflict for an explicit decision.
  Never pad steps or merge independent components solely to reach the minimum.

These rules apply strictly during `/pd-decompose` and must be enforced before `/pd-finalize` runs.

---

## Legacy tasks

Legacy tasks (`temp_docs/task2_*`, `temp_docs/task3_*`) follow the pre-refactor structure (with `T-XX/state.md` and `T-XX/plan.md`) and are exempt from these rules.

---

## Project .ai/ Contract

All projects using these workflows MUST define the following in `.ai/`:

### .ai/specs/ — spec files (required for new workflow)
- `<NN>-<kebab-name>.md` — one file per task. H1 required. Numeric prefix must be unique.
- Immutable during implementation except for explicit owner-authorized edits. Post-validation reconciliation and completion metadata follow `## File Responsibility`.
- Consumed by `phase-discovery` to create the task directory.
- Naming standard: `<NN>-<kebab-name>.md` where NN is zero-padded two digits (01, 02...).

### .ai/context/runbook.md — ## Commands (required for test/lint automation)
- `test:` — command to run full test suite
- `lint:` — command to run linter
- `typecheck:` — command for type checking (optional)
- `build:` — command to build (optional)

`test:` is **required** for testable work: `/pae-tests` stops when it is missing or still a
placeholder, because RED cannot be observed without a runner. Classify the level first;
independently justified `none` retains its manual evidence and needs no runner. Never
select `none` because a command is missing.

### .ai/principles/coding.md — ## Standards (optional but recommended)
- `architecture:` — key patterns, e.g. "repository pattern, no business logic in routers"
- `naming:` — standards
- `error-handling:` — approach
- `forbidden:` — what never to do

Workflows read these sections by key — never by hardcoded command strings.

## File Location Reference

| File | Path | Purpose |
|------|------|---------|
| Task state | `.ai/tasks/todo/task-NN-slug/state.md` | Per-task progress, decisions, phase markers |
| Task plan | `.ai/tasks/todo/task-NN-slug/plan.md` | Subtask decomposition table |
| Task registry | `.ai/memory/state.md` | Cross-task registry (Active Tasks / Done) |
| Architecture | `.ai/memory/architecture.md` | System-level architecture description |
| Project inventory | `.ai/project_state.md` | What exists in the codebase right now |
| Principles | `.ai/principles/coding.md` | Project-specific coding standards |
| Runbook | `.ai/context/runbook.md` | Commands for test/lint/build/deploy |
| ADR index | `.ai/adr/index.md` | Index of all architectural decisions |

Note: `.ai/memory/state.md` and `.ai/project_state.md` are at different nesting levels
by design — `memory/` groups session-context files, `project_state.md` is a technical
inventory updated more frequently. Do not move either without updating all finalize workflows.
