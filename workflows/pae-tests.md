---
description: Atomic Execution Step 1 (TDD RED) — classify test level, write failing tests from Acceptance Criteria, observe them fail; --characterize pins existing behaviour for behaviour-preserving work
---

Invocation: `/pae-tests <path-to-atomic-description> [--batch] [--characterize]`
Called by: `/phase-atomic-execution` as Step 1, before `/pae-implement`.

`--batch` suppresses the review pause in `## Report`; it never suppresses the test-level gate,
the RED observation, or the digest written to `notes:`.

`--characterize` selects **characterization mode** for behaviour-preserving work — a
refactor, an extraction, an equivalent-library swap, a performance change. The tests pin what
the system does *now* and must pass before the change instead of failing. The full contract,
including the three conditions that must all hold, is `tdd → ## Characterization mode`; this
workflow's Step 4 branches on it. Everything else — the level gate, the scope rules, the
tests-only rule, the digest — is identical.

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
2b. If the block has `atomic-tests: pinned` → report: "Behaviour already pinned for T-XX.
   Existing characterization tests are reused; re-running re-verifies them against the
   unchanged code." Continue in characterization mode regardless of whether `--characterize`
   was passed — the recorded status is authoritative.
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
   - If present: `WORK_DIR = <resolved absolute path>`, `AI_DIR = WORK_DIR/.ai`.
   - If absent: `WORK_DIR = <current directory>`, `AI_DIR = .ai`.
   Report the resolved `WORK_DIR` before continuing.

1. Load project context — follow `phase-atomic-execution` rules — ## Context Bootstrap.
   Load from `AI_DIR`. If umbrella (`AI_DIR/../.ai/`) exists, load it first.
   Load in order, skip missing files:
   - `AI_DIR/memory/architecture.md` — component boundaries, integration points
   - `AI_DIR/memory/state.md` — current task status, blockers
   - `AI_DIR/principles/architecture.md` — patterns the tests must respect
   - `AI_DIR/principles/coding.md` — style, naming, forbidden patterns
   - `AI_DIR/principles/domain.md` — domain rules and terminology used in test names
   - `AI_DIR/adr/index.md` — decisions that constrain the interface under test
   - `AI_DIR/context/runbook.md` — **required** — the `test:` command
   Report: "TDD context loaded from AI_DIR=<path>: [files read]"

2. **Runbook check.** Read `AI_DIR/context/runbook.md → ## Commands` and extract `test:`.
   - If `test:` is defined → record it; it is the command used to observe RED.
   - If `test:` is missing or still a placeholder → **stop**: "No `test:` command in
     `AI_DIR/context/runbook.md → ## Commands`. TDD cannot observe RED without a way to run
     tests. Add the command, or state explicitly that this subtask is exempt." Wait for the
     user. Do not silently fall through to `none`.

3. Read `T-XX/description.md` — extract `## Goal`, `## Context`, `## Scope`, `## Steps`,
   `## Acceptance Criteria`, and `## Test Plan` if present.
4. Read parent `state.md` — extract `## Solution Design → ### Decision`, `### Invariants`,
   `### Off-limits`.

---

## Step 1 — Test-level gate

Load the `tdd` rule — `## Test-level gate`. Classify this subtask by evaluating the levels
in order (`unit` → `integration` → `contract` → `smoke` → `none`); the first level that
applies wins. A subtask may legitimately need more than one level (e.g. a use case with a
new HTTP route needs `unit` + `contract`) — record all that apply.

Report the classification before writing anything:

```
TDD level: <unit | integration | contract | smoke | none>
Rationale: <one sentence>
Test command: <test: from runbook>
```

**Characterization mode admission check** (only when `--characterize` was passed). Verify all
three conditions from `tdd → ## Characterization mode → ### When it applies`: the Acceptance
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

---

## Step 2 — Derive the test plan

**If `T-XX/description.md` contains `## Test Plan`** (written by `/pd-decompose`): use it as
the authoritative list of scenarios. Verify it covers every Acceptance Criterion — if a
criterion has no scenario, add one and note the gap in `notes:`.

**If `## Test Plan` is absent** (pre-TDD task, or a fix-task): derive the plan now from
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

Follow `testing-standards` for structure and style — this workflow does not restate it.
The non-negotiables it defines: AAA structure, `test_<subject>_<condition>_<expected_outcome>`
naming, InMemory implementations instead of `Mock()` for repository interfaces, no
`time.sleep()`, no order-dependent tests, no `assert True` as the only assertion.

Constraints specific to this step:

1. **Tests only.** Do not create or modify any implementation file. If a test needs a module
   that does not exist yet, the test imports it and fails on that — that is the point.
   Creating an empty stub module solely to make an import resolve is permitted **only** when
   the test runner cannot collect any test otherwise; record it in `notes:`.
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

The digest line keeps its `tdd: red digest` key in this mode too. Three later steps parse
that exact key, and renaming it for one mode would make the pinned set invisible to all of
them; the mode is carried by the `tdd: characterize` line beside it.

Then **skip the remainder of this step** and continue to `## Report`.

---

**On success** (ordinary RED mode), update the leaf `## Subtask Progress` block in the parent
`state.md`:

```
T-XX | <name> | atomic-tests: red | atomic-execution: <current> | atomic-validation: <current>
  last_action: RED reached — <N> failing tests written (<level>)
  target_files: <test files created, appended to any existing list>
  blocker: none
  notes: tdd: <level> — <N> tests, AC coverage <N>/<N>
         tdd: red digest — AC-1 → test_<name>, test_<name>; AC-2 → test_<name>; edge → test_<name>
```

**The RED digest is written in every mode, not only in batch mode.** It is the AC→test-name
mapping from Step 2, recorded verbatim as the `tdd: red digest` line above. It is the only
persisted record of which tests were red and which criterion each one covers, and three later
steps read it: `/pae-implement` Pre-check 2b (to load the set it must satisfy), its Final
Verification (to prove the set is intact — same names, same count), and `/pav-check` (to
detect a weakened or missing test). A digest left only in the chat transcript is not recorded.

---

## Report

```
─── TDD RED COMPLETE — T-XX ─────────────────────────────────
Level:      <unit | integration | contract | smoke | none>
Tests:      <N> written, <N> failing as expected
AC mapping: <N>/<N> Acceptance Criteria covered
Files:      <test file list>
─────────────────────────────────────────────────────────────
```

**Review gate.** The tests are the specification the implementation will be measured
against — reviewing them is more valuable than reviewing the code that follows. Present the
test list and the AC mapping.

- **Batch mode** (`--batch` passed, or called from `/phase-pipeline`): display nothing further
  and continue without waiting — the digest is already in `notes:` from Step 4.
- **Otherwise**: display the digest and continue. Stop and wait only if the AC mapping is
  incomplete, a criterion proved untestable as written, or the test level had to be
  downgraded — these are decisions the user must see.

Next: `/pae-implement <path>` — implement until these tests pass. Do not weaken them.
