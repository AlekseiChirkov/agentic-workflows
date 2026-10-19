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
     change, never in the test (`tdd → ## Characterization mode`).
   - `n-a` → test-level gate returned `none` with a justification in `notes:`. Continue; the Final Verification test step degrades to running the existing suite for regressions. If no justification line is present in `notes:` → **stop**: "`atomic-tests: n-a` without a recorded justification. Run `/pae-tests` to classify this subtask."
   - `green` → tests already pass. This is a re-run; confirm before overwriting work.
   - `failed` → **stop**: "RED was never reached for T-XX: <reason from notes>. Resolve before implementing — implementing against a test set that never failed proves nothing."
   - `not-started` → **stop**: "No tests written for T-XX. Run `/pae-tests <path>` first — implementation precedes tests only on pre-TDD tasks."
   - Field absent → pre-TDD task. Append `pre-TDD task, TDD step skipped` to `notes:` and continue.
5. Otherwise → continue.

---

## Pre-check

0. **Working directory resolution.**
   Read `T-XX/description.md → ## Context`. Check for `working_dir:` field.
   - If `working_dir:` is present: resolve the path relative to the atomic task directory.
     All subsequent file reads, writes, and shell commands in this workflow execute
     within that resolved path (the target service repo).
     Set `WORK_DIR = <resolved absolute path>`.
     Set `AI_DIR = WORK_DIR/.ai`.
   - If `working_dir:` is absent: all paths are relative to the current working directory.
     Set `WORK_DIR = <current directory>`.
     Set `AI_DIR = .ai`.
   Report the resolved `WORK_DIR` before continuing.

1. Load project context — follow `phase-atomic-execution` rules — ## Context Bootstrap.
   Load from `AI_DIR` resolved in step 0 above. If umbrella (`AI_DIR/../.ai/`) exists, load it first.
   Load in order, skip missing files:
   - `AI_DIR/memory/architecture.md` — component boundaries, integration points
   - `AI_DIR/memory/state.md` — current task status, blockers
   - `AI_DIR/principles/architecture.md` — patterns to enforce during implementation
   - `AI_DIR/principles/coding.md` — **required** — style, naming, error-handling, forbidden patterns
   - `AI_DIR/principles/domain.md` — domain rules, terminology
   - `AI_DIR/adr/index.md` — past decisions that constrain this implementation
   - `AI_DIR/context/runbook.md` — **required for Final Verification** — test/lint/build commands
   Report: "Atomic execution context loaded from AI_DIR=<path>: [files read]"
   If `principles/coding.md` not found → note "No coding principles" in task `notes:` and proceed cautiously.
2. Read `T-XX/description.md` → `## Scope`.
   Extract:
   - In scope: what this subtask covers
   - Out of scope: what this subtask explicitly does NOT cover
   - Target files: files expected to be created or modified

   Write a scope summary block before making any changes:
     Scope In:    <in scope summary>
     Scope Out:   <out of scope list>
     Target files: <file list>

   If `## Scope` section is absent in description.md → **stop**:
   "T-XX/description.md is missing `## Scope` section. Run `/pd-decompose` to regenerate subtask descriptions." Do not continue.
2b. **Load the RED test set.** Read the test files recorded in the leaf block's
   `target_files:` by `/pae-tests`. These tests define what "done" means for this subtask in
   executable form — read them before writing any implementation code. Note the mapping
   between Acceptance Criteria and test names recorded in `notes:`.
   If `atomic-tests: n-a` → skip this sub-step.
3. Read `T-XX/description.md` — extract: `## Goal`, `## Context`, `## Steps`, `## Acceptance Criteria`, and `## Test Plan` if present.
4. Read parent `state.md` — extract `## Solution Design → Decision`, `### Off-limits`, `### Invariants`.
5. Read parent `state.md → ## Subtask Progress` block for this T-XX (if present) — extract `last_action`, `blocker`, `notes`. Determine starting step from `last_action`.
   - If this block is `atomic-execution: blocked` (standalone invocation, without the orchestrator's Step 0) → apply **Blocker Reconciliation** (`phase-atomic-execution` rules) before executing any step. Auto-clear a dependency/status blocker whose prerequisites are all satisfied and continue; for a non-status blocker or an unmet prerequisite, report and wait for confirmation.

Output scope summary before making any changes:
- **Task**: T-XX directory + Goal (from description.md).
- **Context**: from `## Context`.
- **Steps**: full list from `## Steps`. Mark starting point if continuing.
- **RED tests**: count and names of the failing tests this step must turn green (or `n-a`).
- **Scope In / Out**: from `T-XX/description.md → ## Scope` (extracted in Pre-check step 2). Off-limits: from parent `## Solution Design → ### Off-limits`.
- **Invariants**: constraints that must not be violated.

---

## Execute Steps

For each step from `## Steps` in `T-XX/description.md` (starting from determined point):

Before executing this step:
1. Check if this step touches anything listed in Scope Out.
   If yes: STOP immediately. Report:
   "Step N touches out-of-scope area: <specific item from Scope Out>.
   This step should not be executed as written.
   Options:
   1. Modify the step to stay within scope
   2. Defer this change to the appropriate subtask
   3. Confirm explicitly that scope should be extended"
   Wait for user decision. Do not proceed.
2. Add any files modified in this step to `target_files:` in
   `## Subtask Progress` block in parent `state.md`.
   Update after every step, not only at the end.

1. Read target file or check target directory before making changes.
2. Execute the action described by the step.
   - Do not refactor beyond what the step specifies.
   - Do not add functionality beyond parent `## Solution Design → ### Scope → #### In`.
   - Follow existing code style.
3. Verify the step produced the expected effect (each step must be independently observable).
   - If verification passes → update parent `state.md → ## Subtask Progress` block for this T-XX: set `last_action: completed step N — <short description>` and `target_files: <comma-separated list of files modified in this step>`. Next step.
   - If verification fails → **stop immediately**. Update parent block: `blocker: step N failed — <what was observed>`. Report to user and wait.
4. If a blocker is discovered (unknown dependency, invariant conflict) → **stop**. Update parent block `blocker:` field. Describe and wait.

**Important**: Update the parent `## Subtask Progress` block after EVERY completed step, not just at the end. Write both `last_action:` and `target_files:` together. This ensures correct continuation if interrupted.

---

## Test Set Discipline (GREEN)

Applies whenever `atomic-tests: red` or `atomic-tests: pinned`. Load the `tdd` rule — `## GREEN — what implementation
may and may not do` — for the full contract. Enforced here:

**The RED test set may not be weakened.** Do not delete, rename, comment out, or mark
`skip`/`xfail` any test from it. Do not narrow an assertion, replace an exact expected value
with a truthiness check, or drop a case from a parametrized set. Do not change an expected
value to match what the implementation happens to produce.

**Making the code fit the test is the job. Making the test fit the code is the failure mode.**

**Legitimate test amendment.** A RED test may be corrected when the *test* is wrong — it
encoded a misunderstanding of the Acceptance Criterion, used a wrong fixture, or asserted an
implementation detail instead of behaviour. It may never be corrected because the
implementation is inconvenient. Record every amendment in the leaf's `notes:`:

```
tdd: test amended — <test name> — <what changed and why the original was wrong>
```

If an amendment would change what an Acceptance Criterion means, that is a scope question,
not a test question: **stop** and report before touching the test.

**Adding tests during GREEN is always allowed** and needs no amendment record — an
uncovered branch discovered while implementing should get a test.

**Run the tests as you go.** After each step that touches behaviour under test, re-run the
scoped `test:` command. A step is not "verified" (Execute Steps, item 3) while a test that
covers it is still red — unless the step is an intermediate one whose test is expected to go
green later. Record which tests turned green in `last_action:`.

**Refactor.** Once every RED test passes, refactoring is permitted while the suite stays
green and the changes stay within `## Scope`. Re-run the tests after refactoring. Refactoring
never widens scope.

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

**If tripwire fires (and this is a depth-1 leaf):** Invoke the Composite Promotion Protocol from `workflow-reference → Autonomous Subtask Classifier → Runtime self-correction`. Do not continue executing the current leaf. After promotion, restart execution with the first child (T-XXa).

**Tests on promotion.** The RED tests already written are never discarded. Redistribute each
one to the child whose Acceptance Criteria it covers, add it to that child's `target_files:`,
and set that child's `atomic-tests: red`. A child that inherits no test enters the cycle at
`/pae-tests` normally. The promoted composite's own integration-level criteria are covered by
`/phase-composite-validation`, not by `/pae-tests`.

If no tripwire condition is observed → continue execution normally without any change.

---

## Final Verification

After all steps from `## Steps` are done:

Pre-verification:
1. Read `AI_DIR/context/runbook.md` → `## Commands` (uses `AI_DIR` resolved in Pre-check step 0).
   Run all commands from within `WORK_DIR`.
2. **GREEN check** (when `atomic-tests: red` or `pinned`). Under `pinned` this is a
   preservation check: the whole pinned set must still pass and must be intact — same test
   names, same count as the `tdd: red digest` line. Any pinned test that now fails means the
   change altered behaviour: fix the code, or, if the behaviour change is intended, stop —
   the work is no longer behaviour-preserving and needs its own Acceptance Criterion and
   very likely an ADR. Run the `test:` command over the RED test set
   for this subtask. **Every test from that set must pass.**
   - If any RED test still fails: set `blocker: test failures — <which tests, summary>`,
     stop, report to user. Do not weaken the test to get past this gate.
   - Then verify the set is intact: the tests that pass are the same tests that were red —
     same names, same count (plus any added during GREEN), no `skip`/`xfail` markers
     introduced. If the set shrank or an assertion was weakened without an amendment record
     in `notes:` → set `blocker: RED test set was weakened — <detail>`, stop, report.
   - On success: set `atomic-tests: green` in the leaf block.

2b. **Regression check.** Run the full `test:` command for modules affected by this subtask —
   not just the new tests. A subtask that turns its own tests green while breaking a
   neighbouring test is not done. If pre-existing tests fail: set
   `blocker: regression — <summary>`, stop, report to user.

   When `atomic-tests: n-a`, step 2 does not apply and this step is the only test gate: run
   the affected-module suite for regressions.

3. If `lint:` command is defined:
   Run the lint command.
   If lint fails: set `blocker: lint failures — <summary>`, stop, report to user.
4. If no `test:` command is defined:
   This can only occur on a pre-TDD task — `/pae-tests` stops when `test:` is missing.
   Write to `notes:`: "No test command found in AI_DIR/context/runbook.md → ## Commands"
   Continue to Acceptance Criteria check.
   If no `lint:` command is defined: note it the same way and continue.

5. Check each Acceptance Criterion from `T-XX/description.md → ## Acceptance Criteria`: pass/fail.
   For criteria backed by a test (per the AC→test mapping in `notes:`), the passing test **is**
   the evidence — state which test proves it rather than re-asserting it by inspection.
6. Verify no parent `### Invariants` are violated.
7. Verify changes don't touch files outside parent `## Solution Design → ### Scope → #### In`.

If any check fails → **stop**. Update parent `## Subtask Progress` block `blocker:` field. Report to user. Do not proceed to finalization.

On success, update the parent `## Subtask Progress` block for this T-XX:

```
T-XX | <name> | atomic-tests: green | atomic-execution: complete | atomic-validation: <current>
  last_action: all steps complete — <one-sentence summary of what was implemented>
  target_files: <comma-separated list of all files modified during this subtask, including test files>
  blocker: none
  notes: <optional — deviations, test amendments, or out-of-scope observations>
```

When the gate returned `none`, the first field stays `atomic-tests: n-a` and its
justification line is preserved in `notes:`.

If out-of-scope observations were found during execution, capture them in the `notes:` field (one short line, or a reference to a separate section in parent `state.md`).
