---
description: Discovery Step 2 — Decompose task into atomic T-XX subtasks, create directories and files
---

Invocation: `/pd-decompose <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 2.

Task directory = provided argument (trailing slash optional).

**Mode.** Without `--step-by-step` this workflow runs **autonomously**: ambiguous
decomposition boundaries are resolved by the Autonomous Decision Protocol instead
of being handed back to the user. With `--step-by-step` the boundary questions are
presented and awaited. When invoked standalone, the default is still autonomous.

---

## Guard

1. Read `state.md` in the task directory. If it does not exist or `## Task Analysis` section is missing → **stop**: "Step 1 (Task Analysis) must be completed first. Run `/pd-analyze <path>`." Do not continue.
2. Check `## Phases → discovery`:
   - If `complete` → **stop**: "Discovery phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
   - If `in-progress` and `decomposition: complete` marker is present in `state.md`, or any T-XX subdirectories already exist → list the existing T-XX directories and **stop**: "Decomposition already started. Existing subtasks: [list]. Re-running will overwrite their `description.md`. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Instructions

**Multi-phase scope note:** if `state.md` contains `active_phase:`, decomposition
is already scoped to that phase via `## Task Analysis` (narrowed by `pd-analyze`).
Do not re-read the full spec; do not decompose deferred phases.

Load `workflow-reference` for Decomposition Rules before starting step 2.

1. Read `state.md` in the task directory — use `## Task Analysis` as input.
2. Break the task into subtasks (T-01, T-02, ...) following the `## Decomposition Rules` in `workflow-reference`:
   - Each subtask is a logical unit of work (domain/module), not a single file operation.
   - Internal step count per subtask: 3–15.
   - Target 8 subtasks per task (soft guidance). If natural decomposition produces more than 8:
     - *Step-by-step mode* — pause and present options per workflow-reference → ## Decomposition Rules.
     - *Autonomous mode* — apply those same options via the Autonomous Decision Protocol, pick one, and record the choice and its rationale in `## Decomposition Decisions`. Do not pause.
   - If a candidate subtask has < 3 steps — absorb into the closest neighbor.
   - If decomposition boundaries are ambiguous:
     - *Step-by-step mode* — **stop**, describe the ambiguity, propose 2–3 decomposition options with trade-offs, and wait for user decision.
     - *Autonomous mode* — generate the same 2–3 options and resolve them with `workflow-reference → ## Autonomous Decision Protocol`. Record the chosen boundary, the rejected options, and the rationale in `## Decomposition Decisions`. Do not pause.

**2.5 — Autonomous classifier (run after step 2, before creating directories).**

Load `workflow-reference` for the Autonomous Subtask Classifier (signals S1–S5, classification rules, Type 2/3 criteria, Decision record format) before executing this step.

For each candidate subtask, compute signals S1–S5 and apply classification rules in order (default→leaf, leaf-health invariant, Type 2, Type 3). Record every decision in `## Decomposition Decisions` table. The classifier is **fully autonomous** — do not pause to ask the user.

**Depth-2 cap enforcement (mandatory):** A child of a composite (T-XXa, T-XXb, …) may never itself become a composite. If a child candidate still fails the leaf-health invariant after redistribution, add more sibling children to absorb the excess steps — never create a third tier.

**When Type 3 re-slicing is selected for a pair (T-AA + T-BB):**
- Remove both original candidate subtasks from the list.
- **Cross-cutting work first:** before creating capability slices, identify any work shared across ALL capabilities (e.g. shared contract definition, schema setup, shared infrastructure, initialization). Assign it to a single leaf subtask that every capability-pair leaf depends on. Do NOT duplicate this work into individual slices. A capability slice's Acceptance Criteria are declared end-to-end only once its shared-work dependency is satisfied.
- **ID assignment:** let `base = min(AA, BB)` (integer part only). Assign capability index `i` (1-based) the top-level ID `T-(base+i-1)a` (producer role) and `T-(base+i-1)b` (consumer role).
  - **Collision-safety:** before finalizing, verify that none of the IDs T-base through T-(base+N-1) is already in use by any non-dissolved subtask (including children of existing composites). If a collision exists, shift `base` upward by 1 until the full range is free.
- For each capability `i`:
  - Create producer role leaf `T-(base+i-1)a-<capability>-producer/description.md`
  - Create consumer role leaf `T-(base+i-1)b-<capability>-consumer/description.md`
  - Identify which track produces the shared contract and which consumes it — derive this from the task, do not assume a fixed direction. The consumer leaf lists the producer leaf in `Depends On`.
- Record the capability name in the `Slice` **column** of each leaf's `plan.md` row. That
  column is where the grouping is read and where `workflow-reference → ## Protected Sections
  Contract` protects it; `description.md` has no `Slice` field and its six sections are fixed.
- No composite parent is created for Type 3 pairs — the Slice column and ordering policy in `## Execution Strategy` carry the grouping.

**When Type 2 nesting is selected for T-XX:**
- Keep T-XX as the composite directory with a composite `description.md` (see template below).
- Create child directories T-XXa, T-XXb, T-XXc, … each with a leaf `description.md`.
- Children inherit the parent's `working_dir:`, `Constraints`, and `Off-limits`.
- Each child covers one independently-testable component with its own `## Steps` (3–15) and `## Acceptance Criteria`.

**Composite `description.md` template (used for Type 2 composite T-XX):**

```
## Goal
<one-sentence integrated outcome — what this composite achieves end-to-end>

## Context
- working_dir: <same as children, if applicable>
- type: composite
- children: T-XXa, T-XXb, T-XXc
- Dependencies: <T-YY this composite depends on — inherited by all children>
- Constraints: <applies to the composite as a whole>
- Reason: <why Type 2 was selected — which signals fired>

Off-limits: <inherited from parent task>

## Scope
- **In scope:** <what the whole composite covers>
- **Out of scope:** <exclusions>
- **Target files:** (determined by children)

## Steps
See children: T-XXa (<component A>), T-XXb (<component B>), T-XXc (<component C>).

## Acceptance Criteria
(Integration-level — validated after all children are individually reviewed)
- [ ] <end-to-end integration criterion 1>
- [ ] <end-to-end integration criterion 2>
...

## Test Plan
- **Level:** integration | contract
- **Scenarios:** (one per integration criterion — these are executed by
  `/phase-composite-validation`, not by `/pae-tests`)
  - <criterion 1> → <end-to-end scenario that exercises all children together>
  - <criterion 2> → <scenario>
```

The composite's `## Acceptance Criteria` MUST be integration-level (the whole works as a unit), not a restatement of children's individual criteria. Minimum 2 integration criteria required.

3. For each subtask, create directory `T-XX-<slug>/` containing exactly ONE file:

   `T-XX-<slug>/description.md` using this exact six-section template:

   ```
   ## Goal
   <one-sentence outcome this subtask achieves>

   ## Context
   - working_dir: <relative path from this T-XX directory to the target repo, e.g. ../../../../service-api>
     Only include this line if the subtask runs inside a different repository than the task directory.
     Omit entirely for single-repo or umbrella-level work.
   - Dependencies: <which T-XX this subtask depends on and why>
   - Constraints: <technical or architectural limits that apply here>
   - Reason: <why this subtask exists as a separate unit>

   Off-limits: <what must not be touched in this subtask>

   ## Scope
   - **In scope:** <what this subtask covers — derived from ## Steps and parent ### Scope → #### In>
   - **Out of scope:** <what this subtask explicitly does NOT cover — derived from Off-limits and parent ### Scope → #### Out>
   - **Target files:** <files this subtask creates or modifies>

   ## Steps
   1. <step>
   2. <step>
   ...

   ## Acceptance Criteria
   - <verifiable criterion>
   - <verifiable criterion>
   ...

   ## Test Plan
   - **Level:** <unit | integration | contract | smoke | none>
   - **Scenarios:**
     - <AC-1 restated as a test scenario> → <expected observable outcome>
     - <AC-2 restated as a test scenario> → <expected observable outcome>
   - **Edge cases:** <applicable categories from testing-standards → Edge Cases Checklist>
   - **Justification (only when Level is `none`):** <which of unit/integration/contract/smoke
     was considered and why each is inapplicable>
   ```

   Derive `## Scope` content from the subtask's own `## Steps` / `## Context` and the parent `state.md → ## Solution Design → ### Scope`. Do not invent scope — only restate decisions already recorded.

   **`## Test Plan` rules** (executed later by `/pae-tests`; contract defined in the `tdd` rule):
   - Classify `Level` with the test-level gate from the `tdd` rule — evaluate
     `unit` → `integration` → `contract` → `smoke` → `none` in order; first match wins. A
     subtask may need more than one level; list all that apply.
   - **Every** Acceptance Criterion must appear as at least one scenario. A criterion with no
     scenario means the criterion is not testable as written — rewrite the criterion, do not
     drop the scenario.
   - Scenarios are written at the level of observable behaviour, not implementation. They are
     a plan, not code — `/pae-tests` turns them into executable tests.
   - `Level: none` requires the justification line. "Hard to test", "no framework", "small
     change", "will add later", and "existing tests cover it" are not valid justifications.
   - This plan is a Discovery-time artifact and can be revised by `/pae-tests` when
     implementation reveals a gap; the revision is recorded in `state.md`, not here.

   Do NOT create `state.md` or `plan.md` inside the T-XX directory.

4. Create or update top-level `plan.md`:

   **Flat all-leaf task** (no composites, no Type 3 slicing — renders identically to current format; do NOT add Type or Slice columns):
   ```
   ## Subtasks

   | ID   | Name   | Key Steps (summary)                    | Depends On | Status       |
   |------|--------|----------------------------------------|------------|--------------|
   | T-01 | <name> | step1 → step2 → step3                  | —          | not-started  |
   | T-02 | <name> | ...                                    | T-01       | not-started  |

   ## Execution Strategy
   <execution order, parallelism constraints, rationale>
   ```

   **Cross-repo flat task** (at least one T-XX has `working_dir:`, no composites or slicing):
   Add `Repo` column only.
   ```
   ## Subtasks

   | ID   | Name   | Repo              | Key Steps (summary)       | Depends On | Status       |
   |------|--------|-------------------|---------------------------|------------|--------------|
   | T-01 | <name> | (umbrella)        | step1 → step2             | —          | not-started  |
   | T-02 | <name> | service-api       | step1 → step2 → step3     | T-01       | not-started  |

   ## Execution Strategy
   <execution order, parallelism constraints, rationale>
   ```

   **Task with Type 2 composites** (any subtask classified as composite): add `Type` column. Composite rows show `(children: T-XXa, T-XXb, …)` in Key Steps. Child rows are indented by standard. Composite row Depends On = the composite's own dependencies; child row Depends On = either the composite parent's deps or a sibling child.
   ```
   ## Subtasks

   | ID    | Type      | Name              | Key Steps (summary)                   | Depends On    | Status       |
   |-------|-----------|-------------------|---------------------------------------|---------------|--------------|
   | T-01  | leaf      | <name>            | step1 → step2 → step3                 | —             | not-started  |
   | T-02  | composite | <name>            | (children: T-02a, T-02b, T-02c)       | T-01          | not-started  |
   | T-02a | leaf      | <child A name>    | step1 → step2 → step3                 | T-01          | not-started  |
   | T-02b | leaf      | <child B name>    | step1 → step2                         | T-02a         | not-started  |
   | T-02c | leaf      | <child C name>    | step1 → step2 → step3                 | T-02b         | not-started  |
   | T-03  | leaf      | <name>            | step1 → step2                         | T-02          | not-started  |

   ## Execution Strategy
   <execution order; composite rows are containers only — execute children in listed order>

   ## Decomposition Decisions

   | Subtask | Decision | Signals | Rationale |
   |---------|----------|---------|-----------|
   | T-01 | leaf | S1=5, S2=1, S5=1 | Single component; fits one atomic cycle |
   | T-02 | composite (Type 2) | S1=13, S2=3, S5=3 | Three independently-testable components |
   ```

   **Task with Type 3 vertical re-slicing** (cross-repo pair with shared frozen contract and ≥2 capabilities): add `Type`, `Slice`, and `Repo` columns. No composite rows — all leaves, grouped by capability. `## Execution Strategy` states the ordering policy ("process by capability slice; within each slice, producer before consumer").
   ```
   ## Subtasks

   | ID    | Type | Name                  | Key Steps (summary)        | Slice     | Repo   | Depends On | Status      |
   |-------|------|-----------------------|----------------------------|-----------|--------|------------|-------------|
   | T-01  | leaf | shared-setup          | step1 → step2              | —         | (both) | —          | not-started |
   | T-02a | leaf | <cap1>-producer       | <steps>                    | <cap1>    | repo-a | T-01       | not-started |
   | T-02b | leaf | <cap1>-consumer       | <steps>                    | <cap1>    | repo-b | T-02a      | not-started |
   | T-03a | leaf | <cap2>-producer       | <steps>                    | <cap2>    | repo-a | T-01       | not-started |
   | T-03b | leaf | <cap2>-consumer       | <steps>                    | <cap2>    | repo-b | T-03a      | not-started |

   ## Execution Strategy
   Process by capability slice; within each slice, producer before consumer (T-02a before T-02b). This produces continuous integration — <cap1> works end-to-end before <cap2> begins.

   ## Decomposition Decisions

   | Subtask | Decision | Signals | Rationale |
   |---------|----------|---------|-----------|
   | T-02 + T-03 | Type 3 re-slice | S4=true, S3=2, D6 met | Cross-repo pair sharing frozen contract; 2 capabilities; both tracks large |
   ```

   *The leaf names above use abstract role placeholders (`<cap1>-producer`, etc.) and abstract repo names (`repo-a`, `repo-b`). In practice, substitute the actual capability names and the real repo directory names.*

   Use `(umbrella)` when a subtask runs in the umbrella root (no `working_dir:`).
   Use the repo directory name (not full path) for subtasks with `working_dir:`.

`Key Steps` — short inline list (separated by `→`) summarising main steps from `T-XX/description.md → ## Steps`. For composite rows, write `(children: T-XXa, T-XXb, …)` instead.

**Optional `Model` column.** `/pd-select-model` in bulk mode adds a `Model` column after
`Name`, and `/spec-run` reads it to pick the model for each subtask's Implementer agent. Do
not create the column here — `/pd-decompose` never assigns models. If it already exists (a
re-run after model selection), preserve its values.

5. Append to top-level `state.md` an explicit completion marker:

```
## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, ...
- composites: T-02 (children: T-02a, T-02b, T-02c), ...   # omit line if no composites
- sliced-pairs: T-02+T-03 → add/matmul slices, ...        # omit line if no Type 3 re-slicing
```

If the section already exists — overwrite it with the updated list. Omit `composites:` and `sliced-pairs:` lines when none exist (preserves flat-task rendering).

5a. **Initialise `## Subtask Progress` in the top-level `state.md`.** Write one block per
   subtask created in step 3, using the formats in `workflow-reference → ## Parent state.md —
   ## Subtask Progress Format` and `workflow-globals → ## Canonical Status Formats`. Create the
   `## Subtask Progress` section if it does not exist. This section — not `description.md` — is
   where `/pe-execute`, `/pae-*`, `/pav-*`, `/phase-composite-validation`, and `/pe-finalize`
   read and write subtask status, so it must exist before Execution begins.

   - **Leaf subtasks** (including every child of a composite and every Type 3 slice leaf) —
     leaf block with `atomic-tests: not-started`, `atomic-execution: not-started`,
     `atomic-validation: not-started`, and the four field lines `last_action:`,
     `target_files:`, `blocker: none`, `notes:` — all written even when empty, because they
     are protected fields (`workflow-reference → ## Protected Sections Contract`). Do not
     write the five git fields (`branch:`, `base_branch:`, `base_commit:`, `commits:`, `pr:`)
     — `/spec-run` adds them at branch creation.
   - **Type 2 composites** — `[composite]` block:
     ```
     [composite] T-XX | <name> | rollup: not-started | integration-validation: not-started
       children: T-XXa, T-XXb, T-XXc
       blocker: none
       notes: <classifier rationale — which signals fired, why nested>
     ```
     `children:` lists every child ID in execution order and must match the composite's
     `description.md → ## Context → children:` exactly. `notes:` carries the classifier
     rationale recorded in `plan.md → ## Decomposition Decisions` — a composite block with an
     empty `notes:` is incomplete (`workflow-globals → Composite field rules`).
   - **Type 3 re-sliced subtasks** — all leaves; write leaf blocks only. Type 3 produces no
     composite rows, so no `[composite]` block is written for a sliced pair.

   **Upsert semantics (mandatory on any re-run).** Match blocks by T-XX ID: create the blocks
   that are missing, and leave every existing block untouched. Never write a duplicate block
   for an ID that already has one, and never reset a block whose `atomic-tests:`,
   `atomic-execution:`, `atomic-validation:`, `rollup:`, or `integration-validation:` status is
   already beyond `not-started` — a re-run after the Guard confirmation regenerates
   `description.md`, not recorded progress. A leaf block that the Composite Promotion Protocol
   (`workflow-reference → ### Runtime self-correction (tripwire)`) has already converted to
   `[composite]` for the same ID is left as-is.

6. Report: "Step 2 (Decomposition) complete. Created N subtasks."
   **Autonomous mode:** progress marker, not a handoff — the parent workflow
   proceeds to Step 3 immediately. Do not stop or ask to continue.
