---
description: Atomic Execution Step 2 (TDD GREEN) — Execute implementation steps until the RED tests pass, then refactor and verify
---

Invocation: `/pae-implement <path-to-atomic-description>`
Called by: `/phase-atomic-execution` as Step 2, after `/pae-tests`.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

This is the GREEN step. The RED test set produced by `/pae-tests` is a frozen contract —
see the `tdd` rule, `## GREEN — what implementation may and may not do`.

---

## Guard

1. Read parent `state.md` (one level above atomic task directory). Locate the `## Subtask Progress` block for this T-XX.
2. If the block has `atomic-execution: complete` → **stop**: "Atomic execution phase is already complete. Re-running will overwrite the parent `## Subtask Progress` block for this T-XX. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `T-XX/description.md` exists and contains `## Steps` and `## Acceptance Criteria`. If missing → **stop**: "description.md is incomplete. Run `/pd-decompose` + `/pd-finalize` in the parent task."
4. **TDD gate.** Read `atomic-tests:` from the same block:
   - `red` → RED established. Continue.
   - `pinned` → characterization mode: the tests pin existing behaviour and already pass.
     Continue. The GREEN check below becomes a **preservation check** — the pinned set must
     still pass, unchanged, after the work. A pinned test that turns red is a defect in the
     change, never in the test (`tdd → ## Characterization mode — behaviour-preserving work`).
   - `n-a` → test-level gate returned `none` with a justification in `notes:`. Continue; the Final Verification test step degrades to running the existing suite for regressions. If no justification line is present in `notes:` → **stop**: "`atomic-tests: n-a` without a recorded justification. Run `/pae-tests` to classify this subtask."
   - `green` → tests already pass. This is a re-run; confirm before overwriting work.
   - `failed` → **stop**: "RED was never reached for T-XX: <reason from notes>. Resolve before implementing — implementing against a test set that never failed proves nothing."
   - `not-started` → **stop**: "No tests written for T-XX. Run `/pae-tests <path>` first — implementation precedes tests only on pre-TDD tasks."
   - Field absent and execution already `in-progress` → pre-TDD task. Append
     `pre-TDD task, TDD step skipped` once to `notes:` and continue.
   - Field absent on an unstarted task → **stop**: "Run `/pae-tests <path>` first."
5. Otherwise → continue.

---

## Pre-check

0. **Working directory resolution.**
   Read `T-XX/description.md → ## Context`. Check for `working_dir:` field.
   - If `working_dir:` is present: resolve the path relative to the atomic task directory.
     Resolve task-artifact paths absolutely before changing directories.
     All subsequent file reads, writes, and shell commands in this workflow execute
     within that resolved path (the target service repo).
     Set `WORK_DIR = <resolved absolute path>`.
     Set `AI_DIR = WORK_DIR/.ai`.
   - If `working_dir:` is absent: all paths are relative to the current working directory.
     Set `WORK_DIR = <current directory>`.
     Set `AI_DIR = .ai`.
   Report the resolved `WORK_DIR` before continuing.

1. Load the `phase-atomic-execution` rule (`## Context Bootstrap`) from `AI_DIR` before
   reading code or writing tests/implementation. Run the full bootstrap even when
   standalone; the rule owns load order and reporting. Load `WORK_DIR/../.ai` as the
   umbrella when present, then `AI_DIR`.
   Preserve absolute task-artifact paths when running commands in `WORK_DIR`.

2. Read `T-XX/description.md` → `## Scope`.
   Extract:
   - In scope: what this subtask covers
   - Out of scope: what this subtask explicitly does NOT cover
   - Target files: files expected to be created or modified

   If `## Scope` section is absent in description.md → **stop**:
   "T-XX/description.md is missing `## Scope` section. Run `/pd-decompose` to regenerate subtask descriptions." Do not continue.
2b. **Load the RED test set.** Read the test files recorded in the leaf block's
   `target_files:` by `/pae-tests`. These tests define what "done" means for this subtask in
   executable form — read them before writing any implementation code. Note the mapping
   between Acceptance Criteria and test names recorded in `notes:`.
   If `atomic-tests: n-a` or a recorded legacy exemption applies → skip this sub-step.
   Otherwise require the `tdd: red digest`; if missing, stop and recover the frozen test set from evidence before implementing.
3. Read `T-XX/description.md` — extract: `## Goal`, `## Context`, `## Steps`, `## Acceptance Criteria`, and `## Test Plan` if present.
4. Read parent `state.md` — extract `## Solution Design → Decision`, `### Off-limits`, `### Invariants`.
5. Read parent `state.md → ## Subtask Progress` block for this T-XX (if present) — extract `last_action`, `blocker`, `notes`. Determine starting step from `last_action`.
   - If this block is `atomic-execution: blocked` (standalone invocation, without the orchestrator's Step 0) → apply **Blocker Reconciliation** (`phase-atomic-execution` rules) before executing any step. Auto-clear a dependency/status blocker whose prerequisites are all satisfied and continue; for a non-status blocker or an unmet prerequisite, report and wait for confirmation.

Output scope summary before making any changes:
- **Task**: T-XX directory + Goal (from description.md).
- **Context**: from `## Context`.
- **Steps**: identify the next step; do not repeat the whole description.
- **RED tests**: count and names of the failing tests this step must turn green (or `n-a`).
- **Scope In / Out**: from `T-XX/description.md → ## Scope` (extracted in Pre-check step 2). Off-limits: from parent `## Solution Design → ### Off-limits`.
- **Invariants**: constraints that must not be violated.

---

## Execute Steps

For each planned step, starting from recorded `last_action:`:
1. Check Scope Out and parent Off-limits before edits. A conflict → **stop**:
   "Step <N> touches <excluded area>. Choose a scoped alternative, defer it, or explicitly
   amend scope." Wait for the decision unless a declared caller override resolves it;
   never treat that override as permission to violate a binding constraint.
2. Read affected code, perform only the planned action, and follow loaded coding standards.
   Keep `target_files:` as the cumulative union of every changed test/implementation file.
3. Verify the expected effect and applicable scoped tests. Persist
   `last_action: completed step N — <effect and test result>` with `target_files:` after
   every completed step. This pair supplies interruption recovery.
4. A failed step or blocker → set `atomic-execution: blocked`, describe the observed
   failure in `blocker:`, and **stop**: "Resolve <failure> before continuing."

---

## Test Set Discipline (GREEN)

For `red` and `pinned`, enforce `tdd → ## GREEN — what implementation may and may not do`:
**The RED test set may not be weakened.** Do not delete, rename, comment out, or mark
`skip`/`xfail` tests; do not weaken assertions or change expected values to fit the code.
Record a legitimate correction as:

```
tdd: test amended — <test name> — <what changed and why the original was wrong>
```

Changing an Acceptance Criterion is a scope decision: stop before editing the test.
Adding tests is allowed. Re-run scoped tests after each behaviour change; an intermediate
step may leave a test red only when a later planned step supplies its missing behaviour.
Record the result in `last_action:`. Refactor only within scope after GREEN, then rerun tests.

---

## Tripwire Check (composite promotion)

Evaluate at the beginning of execution and again at the midpoint of `## Steps` (after
`ceil(N/2)` of N steps are complete). Load `workflow-reference` for the Autonomous Subtask Classifier (Composite Promotion Protocol) before evaluating.

**Tripwire fires if any of the following conditions are true:**
- Steps balloon: the implementation of this leaf requires substantially more steps than described, and the additional steps constitute a second independently-testable component.
- A second independently-testable component appears that was not anticipated at decomposition time.
- The Acceptance Criteria actually split into two or more independent verifiable clusters during implementation.

**Depth-2 cap constraint:** Determine whether this T-XX is a child of a composite from actual structure — **not** from the ID pattern (Type 3 leaves also have letter suffixes but have no composite parent). Check both of the following:
- In parent `plan.md → ## Subtasks`: does T-XX appear as an indented child row under a composite row?
- In parent `state.md → ## Subtask Progress`: does any `[composite]` block list T-XX in its `children:` field?

If either check is true — this is a depth-2 leaf; do NOT promote it. Stop and report: "Leaf T-XX is oversize but cannot be promoted (depth-2 cap: it is listed as a child of composite T-YY). Re-decompose T-YY by adding more sibling children." Wait for user.

If neither check is true — this is a depth-1 leaf (whether a plain leaf or a Type 3 re-sliced leaf); it MAY be promoted to a composite, within the depth-2 cap.

**If tripwire fires (and this is a depth-1 leaf):** Invoke the Composite Promotion Protocol from `workflow-reference → Autonomous Subtask Classifier → Runtime self-correction`. Do not continue executing the current leaf. Persist the promotion and preserved evidence, then stop/return the replacement children to
the caller. Do not execute the first child until the declared tripwire decision is resolved.

**Tests on promotion.** Preserve every frozen test and its original pre-implementation
observation. Redistribute tests, `target_files:`, AC mapping/digest, and test-mode notes to
matching children. Inherit `red` for an observed RED set or `pinned` for characterization;
never relabel pins as RED or discard tests already passing after partial work. Reuse this
recorded evidence; new uncovered child criteria must pass `/pae-tests` before more code.
A child with no inherited evidence enters `/pae-tests` normally. Composite integration
criteria remain owned by `/phase-composite-validation`.

If no tripwire condition is observed → continue execution normally without any change.

---

## Final Verification

After all planned steps, read `AI_DIR/context/runbook.md → ## Commands` and run
verification in `WORK_DIR`:
1. Require `test:` for testable work. A missing command blocks it; only justified `n-a`
   or a documented pre-TDD task may record its absence and use actual AC/manual
   verification. Missing tooling never changes a testable level to `none`.
2. For `red` / `pinned`, run the whole frozen set and audit it against `tdd: red digest`:
   same original identities/count, no weakened assertion or new skip/xfail without a valid
   `tdd: test amended` record. Added tests are allowed. Under characterization this is a
   **preservation check**: a failing pin means a defect in the change. Fix the code; an
   intended behaviour change requires an approved criterion before changing the pin.
3. Run the affected-module regression suite, including pre-existing tests. `n-a` skips
   the new-test gate, never the regression check when a suite exists.
4. Run configured `lint:`, `typecheck:`, and `build:` commands applicable to the change.
   Note absent optional commands. A command with external deployment/publishing effects
   still requires its normal authorization; do not mistake it for a local build.
5. Verify every Acceptance Criterion with actual evidence (use passing mapped tests),
   parent Invariants/Off-limits, and the allowed scope.

Any failure → preserve the entry test status, set `atomic-execution: blocked` and
`blocker: <command/criterion and observed failure>`, then **stop**: "Resolve verification
failures before finalizing." Keep the frozen tests; do not weaken them. Set GREEN only
when all final checks pass, together with execution completion below.

On success, update the parent `## Subtask Progress` block for this T-XX:

```
T-XX | <name> | atomic-tests: green | atomic-execution: complete | atomic-validation: <current>
  last_action: all steps complete — <one-sentence summary of what was implemented>
  target_files: <comma-separated list of all files modified during this subtask, including test files>
  blocker: none
  notes: <preserve existing notes and all tdd: records; append new observations>
```

When the gate returned `none`, preserve `atomic-tests: n-a` and its justification.
For a documented pre-TDD task with no test field, preserve that absence and its legacy
exemption; do not invent a GREEN status/digest for tests that were never established.

If out-of-scope observations were found during execution, capture them in the `notes:` field (one short line, or a reference to a separate section in parent `state.md`).

Report: "Step 2 (Implementation) complete. Verification: <results>."
This is a progress marker; return to `/pae-finalize` through the active caller.
