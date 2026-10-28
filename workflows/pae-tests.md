---
description: Atomic Execution Step 1 (TDD RED) — classify test level, write failing tests from Acceptance Criteria, observe them fail; --characterize pins existing behaviour for behaviour-preserving work
---

Invocation: `/pae-tests <path-to-atomic-description> [--batch] [--characterize]`
Called by: `/phase-atomic-execution` as Step 1, before `/pae-implement`.

`--batch` suppresses duplicate digest display, never test classification, observation,
or persistence. It does not authorize applying improvement proposals. `--characterize`
selects `tdd → ## Characterization mode — behaviour-preserving work` when all admission
conditions hold; the tests must pass against unchanged code instead of failing.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

This step produces the RED state. It writes **tests only** — never implementation code.
The governing contract is the `tdd` rule; test style comes from `testing-standards`.

---

## Guard

1. Read parent `state.md` (one level above the atomic task directory). Locate the
   `## Subtask Progress` block for this T-XX.
2. If the block has `atomic-tests: green` → **stop**: "Tests for this subtask are already
   green. Re-running will overwrite the RED test set. Confirm to proceed? (yes/no)" Wait for
   explicit confirmation.
2b. `atomic-tests: pinned` → reuse the recorded characterization mode. If implementation
    has begun, return to `/pae-implement` without rewriting or claiming a new baseline;
    otherwise re-verify existing pins against unchanged code.
3. If the block has `atomic-tests: red` → report: "RED already reached for T-XX. Existing
   failing tests: [list]. Re-running will regenerate them. Confirm to proceed? (yes/no)"
   Wait. On a resume this is normally NOT what you want — continue to `/pae-implement`
   instead.
4. If `atomic-execution: complete` → **stop**: "Atomic execution is already complete.
   Writing tests now would be test-after. Confirm to proceed? (yes/no)" Wait.
5. Check `T-XX/description.md` exists and contains `## Acceptance Criteria`. If missing →
   **stop**: "description.md is incomplete. Run `/pd-decompose` + `/pd-finalize` in the
   parent task."
6. **Composite guard.** If `T-XX/description.md → ## Context` contains `type: composite` →
   **stop**: "T-XX is a composite. Composites are not executed directly; their
   integration-level criteria are verified by `/phase-composite-validation`. Run
   `/pae-tests` on its children (T-XXa, T-XXb, …)."
7. Otherwise → continue.

---

## Pre-check

0. **Working directory resolution** (identical to `/pae-implement`).
   Read `T-XX/description.md → ## Context`. Check for `working_dir:`.
   - If present: resolve relative to the atomic task directory; set absolute `WORK_DIR` and `AI_DIR = WORK_DIR/.ai`.
   - If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`.
   Report the resolved `WORK_DIR` before continuing.

1. Load the `phase-atomic-execution` rule (`## Context Bootstrap`) from `AI_DIR` before
   reading code or writing tests/implementation. Run the full bootstrap even when
   standalone; the rule owns load order and reporting. Load `WORK_DIR/../.ai` as the
   umbrella when present, then `AI_DIR`.
   Preserve absolute task-artifact paths when running commands in `WORK_DIR`.

2. Read `AI_DIR/context/runbook.md → ## Commands` and capture `test:` if available.
   Classify the test level before requiring a command. Missing tooling is never evidence
   for `none`; only the independent gate in Step 1 can justify that exemption.

3. Read `T-XX/description.md` — extract `## Goal`, `## Context`, `## Scope`, `## Steps`,
   `## Acceptance Criteria`, and `## Test Plan` if present.
4. Read parent `state.md` — extract `## Solution Design → ### Decision`, `### Invariants`,
   `### Off-limits`.

---

## Step 1 — Test-level gate

Load `tdd → ## Test-level gate`. Evaluate `unit` → `integration` → `contract` → `smoke` →
`none` in order; the first applicable level is primary. Add other levels only when needed
for criteria the primary level cannot cover, and record their rationale.

Report the classification before writing anything:

```
TDD level: <unit | integration | contract | smoke | none>
Rationale: <one sentence>
Test command: <test: from runbook>
```

**Characterization mode admission check** (when `--characterize` was passed or pins are recorded). Verify all
three conditions from `tdd → ## Characterization mode — behaviour-preserving work → ### When it applies`: the Acceptance
Criteria assert preserved behaviour; that behaviour is observable today; no requirement
changes. Report the verdict:

```
TDD mode: characterize
Conditions: AC preserve behaviour <yes|no> | observable today <yes|no> | no requirement change <yes|no>
```

If any condition is `no` → **stop**: "This subtask is not behaviour-preserving: <which
condition failed>. Run `/pae-tests <path>` without `--characterize`, or split the subtask so
the new behaviour gets its own Acceptance Criterion." Characterization is not a lighter path
for work that is merely hard to specify.

**If the gate returns `none`:**
1. Verify against the `tdd` rule's list of legitimate and illegitimate reasons. "Hard to
   test", "no framework", "small change", "will add later", and "existing tests cover it"
   are **not** valid.
2. Write the justification line to the leaf's `notes:` field:
   `tdd: none — <which of unit/integration/contract/smoke was considered and why each is inapplicable>`
3. Set `atomic-tests: n-a` in the leaf block.
4. Report: "TDD level: none (justified). Next: `/pae-implement <path>`." **Skip Steps 2–4.**

For every testable level, a missing/placeholder/unavailable `test:` command → **stop**:
"Configure a runnable `test:` command before establishing test evidence." Record an
external tooling/dependency blocker; never downgrade the gate to `none` to bypass it.

---

## Step 2 — Derive the test plan

**If `T-XX/description.md` contains `## Test Plan`** (written by `/pd-decompose`): use it as
the authoritative list of scenarios. Verify it covers every Acceptance Criterion — if a
criterion has no scenario, add one and note the gap in `notes:`.

**If `## Test Plan` is absent** (legacy description): derive the plan now from
`## Acceptance Criteria` and record it in the parent `state.md` under the leaf's `notes:` as
a one-line summary. Do not edit `description.md` retroactively.

Map every Acceptance Criterion to at least one test. Then extend the plan with the edge-case
categories from `testing-standards → Edge Cases Checklist` that apply to this subtask —
happy path, empty/null inputs, boundary values, duplicate operations, invalid state
transitions, missing dependencies, concurrency, permission boundaries.

Output the mapping before writing code:

```
AC-1 <criterion text>  → test_<name>, test_<name>
AC-2 <criterion text>  → test_<name>
Edge cases            → test_<name>, test_<name>
```

Every Acceptance Criterion must appear on the left. A criterion with no test is a
decomposition defect — report it and stop.

---

## Step 3 — Write the tests

Follow `testing-standards` for structure, naming, observable assertions, and test doubles.

Constraints specific to this step:

1. **Tests only**, except the collection stub below. An import/collection failure is not RED.
   A minimal collection-only stub is permitted
   **only** when tests otherwise cannot be collected; record the exception in `notes:`
   and `target_files:`. It must implement no behaviour. Observe an executable assertion
   fail for the missing behaviour before proceeding.
2. **Stay in scope.** Test files must be within the subtask's `## Scope → Target files` or
   the project's test directory. Add every test file created to `target_files:` in the leaf
   block.
3. **Test behaviour, not implementation.** Assert observable outcomes through public
   interfaces. A test that would break on a pure refactor is a bad test.
4. **Respect Off-limits.** Tests must not require changes to anything under parent
   `### Off-limits`.

Update the leaf block's `target_files:` as test files are created — not only at the end.

---

## Step 4 — Observe RED

1. Run the `test:` command from the runbook, scoped to the tests just written, from within
   `WORK_DIR`.
2. Record the actual output — which tests failed and with what error.
3. Verify RED per the `tdd` rule — `## RED — what counts`:
   - **Every** new test fails.
   - Each fails for the **expected reason**: missing function, unimplemented branch, wrong
     return value. Not an import error in the test file itself, not a syntax error, not a
     missing fixture, not a typo.

**If a test fails for the wrong reason** → fix the test and re-run. Repeat until every
failure is a genuine one. Do not proceed with a broken test in the set.

**If any new test passes before implementation** → set `atomic-tests: failed`, record which
test passed and the suspected cause (behaviour already exists → subtask scope is wrong; or
the assertion is vacuous → violates `testing-standards → Forbidden in Tests`). **Stop** and
report to the user. Do not continue to `/pae-implement`.

### Characterization mode — Step 4 is inverted

In `--characterize` mode the expectation is reversed and everything else holds:

1. Run the tests against the **unchanged** code. **Every one must pass.** This is the mode's
   equivalent of observing RED and it is equally mandatory — an unrun pin is not a pin.
2. **If a test fails** → the test does not describe current behaviour. Fix the *test* and
   re-run. Never change the code to satisfy a characterization test: the code is the
   specification in this mode.
3. If a test pins behaviour that is visibly wrong, keep it and record
   `tdd: characterize — <test name> pins existing incorrect behaviour: <what is wrong>`,
   then raise it as a finding. A bug fixed inside a refactor is an unrequested behaviour
   change.
4. **Coverage check** — confirm every entry point and branch the change will touch is
   covered, per the rule's step 5. Name any gap; pin it or move it out of scope.
5. On success, write the leaf block with `atomic-tests: pinned`:

```
T-XX | <name> | atomic-tests: pinned | atomic-execution: <current> | atomic-validation: <current>
  last_action: behaviour pinned — <N> characterization tests passing against unchanged code (<level>)
  target_files: <test files created, appended to any existing list>
  blocker: none
  notes: tdd: characterize — <N> tests pin <what behaviour>, verified passing before the change
         tdd: red digest — <behaviour> → test_<name>, test_<name>; <behaviour> → test_<name>
```

Keep the exact `tdd: red digest` key for pins too; later steps read it in both modes.

Then skip the ordinary RED record below and continue to the Report section.

**On success in ordinary mode**, update the parent leaf block, preserving other fields:

```
T-XX | <name> | atomic-tests: red | atomic-execution: <current> | atomic-validation: <current>
  last_action: RED reached — <N> failing tests written (<level>)
  target_files: <cumulative test/stub files, unioned with existing files>
  blocker: none
  notes: tdd: <level> — <N> tests, AC coverage <N>/<N>
         tdd: red digest — AC-1 → test_<name>, test_<name>; AC-2 → test_<name>; edge → test_<name>
```

The RED digest is written in every mode, including characterization; `none` records its
justification instead. Preserve other notes/git fields. `/pae-implement` and `/pav-check`
read the digest to verify frozen test identities and AC coverage.

---

## Report

Report mode/level, test names, AC coverage, files, command, and observed result:
ordinary mode: <N> expected failures; characterization: <N> pins passing before code changes;
`none`: the recorded justification. Do not label passing pins as failing RED tests.

Display the digest unless `--batch` or `/phase-pipeline` suppresses the duplicate output.
A valid gate returns immediately to the caller; this is a progress marker, not a handoff.
Incomplete mapping, an untestable criterion, or a required level downgrade → **stop**:
"Test contract requires a decision: <gap>. Clarify the criterion or scope before implementation."
Batch display suppression never bypasses these gates.

Next: `/pae-implement <path>`. Keep the recorded test set frozen.
