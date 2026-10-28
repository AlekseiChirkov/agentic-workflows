---
description: Discovery Step 2 — Decompose task into atomic T-XX subtasks, create directories and files
---

Invocation: `/pd-decompose <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 2.

Resolve artifacts inside the task directory. Default is autonomous;
`--step-by-step` waits for boundary decisions. Reuse parent context; standalone
use applies the `phase-discovery` bootstrap.

## Guard

1. Missing `state.md` or `## Task Analysis` → **stop**: run `/pd-analyze` first.
2. `flow: quick` → report that decomposition is skipped; create no subtasks.
3. `discovery: complete`, `decomposition: complete`, or existing T-XX directories
   → list affected artifacts and **stop** for explicit overwrite confirmation
   unless the parent already obtained it for this exact rerun. Confirmation never
   authorizes resetting progress or deleting an obsolete directory silently.

## Instructions

1. Read `## Task Analysis`; for phased tasks this already defines the active scope.
   Load `workflow-reference → ## Decomposition Rules` and
   `workflow-reference → ## Autonomous Subtask Classifier` once. Do not reread
   the full spec or decompose deferred phases.
2. Draft logical domain/module subtasks T-01, T-02, …, each independently verifiable
   with 3–15 implementation steps. Absorb smaller candidates into related work.
   Target eight top-level subtasks; if more are natural, compare the canonical
   merge/split options without weakening leaf health. For ambiguous boundaries or
   that size decision, step-by-step mode presents options and waits; autonomous
   mode applies the Autonomous Decision Protocol and records choices, rejected
   alternatives and evidence in `plan.md → ## Decomposition Decisions`.
3. Compute S1–S5 and classify every candidate with the canonical classifier.
   Classification itself is autonomous in both modes. Record its decision table
   in `plan.md`. Enforce the depth-2 cap: composite children are leaves; redistribute
   excess work among more siblings rather than nesting a third tier.

   **When Type 3 re-slicing is selected** for T-AA + T-BB, dissolve those candidates.
   Assign cross-cutting work shared by all capabilities to one dependency leaf.
   For each capability, create producer and consumer leaves; derive direction from
   the actual contract and make the consumer depend on the producer. Use
   `base = min(AA, BB)` and capability i → `T-(base+i-1)a` / `T-(base+i-1)b`.
   Check collisions against every retained ID;
   shift base upward by 1 until the complete numeric range is free. Type 3 creates no composite parent.

   **Type 2** keeps T-XX as a composite and creates sibling directories
   T-XXa-<slug>, T-XXb-<slug>, … at task level. Children inherit its constraints,
   Off-limits, external dependencies and repository; each child has one component
   and one coherent Acceptance Criteria cluster.
4. Create exactly `description.md` inside each leaf/composite directory; no local
   `state.md` or `plan.md`. Use all six sections:

   ```
   ## Goal
   <one-sentence measurable outcome>

   ## Context
   - working_dir: <path relative to this T-XX directory; omit for same-repo work>
   - Dependencies: <IDs and reasons, or none>
   - Constraints: <applicable technical/architectural limits>
   - Reason: <why this is a separate unit>

   Off-limits: <specific boundaries inherited from the task>

   ## Scope
   - **In scope:** <included work>
   - **Out of scope:** <specific exclusions>
   - **Target files:** <expected paths>

   ## Steps
   1. <action, location and verifiable outcome>
   2. <...>
   3. <...>

   ## Acceptance Criteria
   - <binary observable condition and exact result>
   - <binary observable condition and exact result>

   ## Test Plan
   - **Level:** <unit | integration | contract | smoke | none; list applicable levels>
   - **Scenarios:**
     - <criterion> → <expected observable outcome>
   - **Edge cases:** <applicable testing-standards checklist categories>
   - **Justification (only when Level is none):** <why each test level is inapplicable>
   ```

   Derive initial Scope from analysis and Steps/Context; align with existing
   `## Solution Design → ### Scope` on rerun. On first run, `/pd-design` reconciles
   descriptions after choosing the architecture.

   Apply the `tdd` test-level gate. Cover every criterion with an observable
   scenario; rewrite untestable criteria. `none` needs reasons for rejecting each
   other level; difficulty, missing framework, size, deferral and existing coverage
   are not reasons. `/pae-tests` may later record Test Plan amendments in state.

   For a composite, use the same six headings with these replacements:
   - Context adds `type: composite` and `children: T-XXa, T-XXb, …`.
   - Target files are the union of children's target files.
   - Steps contains `See children: <IDs and components>` instead of numbered steps.
   - At least two Acceptance Criteria verify integrated output across children.
   - Test Plan uses integration and/or contract scenarios executed by
     `/phase-composite-validation`, rather than `/pae-tests`.
5. Write top-level `plan.md` with `## Subtasks` and `## Execution Strategy`:

   ```
   ## Subtasks

   | ID | Name | Key Steps (summary) | Depends On | Status |
   |----|------|---------------------|------------|--------|
   | T-01 | <name> | <step → step → step> | — | not-started |
   ```

   Extend the table only as required:

   | Shape | Added columns and values |
   |---|---|
   | Cross-repo | `Repo`: repository directory name, or `(umbrella)` without working_dir |
   | Type 2 | `Type`: leaf/composite; place child rows immediately after their parent; composite Key Steps = `(children: <IDs>)` |
   | Type 3 | `Type`, `Slice`, `Repo`; all rows are leaves; Slice is capability name, or `—` for shared setup |

   Record the capability name in the `Slice` **column** of each Type 3 row.
   Combine extensions for a mixed task. Child dependencies include inherited
   external dependencies and actual sibling prerequisites; references must resolve
   and remain acyclic. Outside `/spec-run`, execution follows dependencies; under
   `/spec-run`, preserve strictly sequential stack order.
   `## Execution Strategy` states the ordering policy: Type 3 runs producer before consumer
   within each capability; composites execute their children in listed order.
   Describe any shared-file constraints. Do not claim unsupported parallel execution.

   Include `## Decomposition Decisions` in every plan, even an all-leaf plan:

   ```
   ## Decomposition Decisions

   | Subtask | Decision | Signals | Rationale |
   |---------|----------|---------|-----------|
   | T-XX | leaf | S1=N, S2=1, S3=N, S4=false, S5=1 | <evidence> |
   ```

   Preserve optional model columns and their values, including `Model (Claude)`,
   `Model (Codex)` and legacy `Model`, under
   `workflow-reference → ### Model columns and resolution`; do not assign models
   here or migrate populated legacy cells implicitly. Preserve composite model
   cells as blank. Preserve row Status on a confirmed rerun. Do not remove,
   rename or change the type of a subtask with recorded progress; report a
   reconciliation blocker instead. Reconcile unstarted rows and flag any stale
   model recommendation when their scope changes.
6. Upsert task `state.md → ## Decomposition`:

   ```
   ## Decomposition
   - decomposition: complete
   - subtasks: <all emitted IDs in plan order>
   - composites: <parent and children; omit when absent>
   - sliced-pairs: <original pair → emitted capability leaves; omit when absent>
   ```

7. **Initialise `## Subtask Progress`** in task `state.md` using
   `workflow-globals → ## Canonical Status Formats`. For each leaf, write
   `atomic-tests`, `atomic-execution`, `atomic-validation` as `not-started`, plus
   `last_action:`, `target_files:` from Scope, `blocker: none`, and `notes:` even
   when empty. `/spec-run` adds git fields at branch creation; omit them here.
   For each composite, write:

   ```
   [composite] T-XX | <name> | rollup: not-started | integration-validation: not-started
     children: T-XXa, T-XXb, T-XXc
     blocker: none
     notes: <nonempty classifier rationale>
   ```

   Children match the description and plan order exactly. Type 3 uses leaf blocks only.

   **Upsert semantics:** match blocks by ID and create only missing blocks. Never write a duplicate block.
   Never reset a block whose statuses are beyond `not-started`; preserve existing blocks, including runtime-promoted composites
   from the classifier tripwire. Report any mismatch with regenerated descriptions
   instead of silently changing recorded progress.
8. Verify unique IDs, described dependencies, leaf health, complete test scenarios,
   and matching description/plan/progress inventories. Report:
   `Step 2 (Decomposition) complete. Created <N> leaves and <M> composites.` Under
   an autonomous parent this is a progress marker, not a handoff; standalone use ends here.
