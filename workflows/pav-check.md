---
description: Atomic Validation Step 1 — Final check against DoD, find bugs, determine verdict
---

Invocation: `/pav-check <path-to-atomic-description>`
Called by: `/phase-atomic-validation` as Step 1.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

---

## Guard

1. Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.
2. If block has `atomic-validation: complete` → **stop**: "Atomic validation already complete. Re-running will overwrite the parent block. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. If `atomic-execution` is not `complete` in the block → **stop**: "Atomic execution must be completed first. Run /phase-atomic-execution <path>."
4. Otherwise → continue.

---

## Context Bootstrap

Load the `phase-atomic-validation` rule (`## Context Bootstrap`) before reading implementation files or
writing project files; run the full bootstrap when invoked standalone. The rule owns
the load order, umbrella precedence, conditional sources, and reporting.

Resolve the description and parent task paths before changing directories. Resolve
`working_dir:` from `description.md → ## Context` relative to the atomic task directory;
if absent, use the invocation directory. Set `WORK_DIR` to that absolute directory
and `AI_DIR = WORK_DIR/.ai`. The umbrella is `WORK_DIR/../.ai`.
Keep task-artifact paths absolute; run code reads, writes, and commands in `WORK_DIR`.

---

## Instructions

1. Read `T-XX/description.md` — extract `## Goal`, `## Acceptance Criteria`.
2. Read parent `state.md` — extract `## Solution Design → Decision`, `### Off-limits`, `### Invariants`.
3. Read parent `state.md → ## Subtask Progress` block for this T-XX — extract `last_action`, `notes` for context on what was implemented.
4. Read changed files from parent `state.md → ## Subtask Progress → T-XX → target_files:`.
   If missing/empty, recover only from a recorded task-specific baseline or reviewed
   commit set, including staged/unstaged changes belonging to this subtask. Never assume
   the latest commit belongs to it. Persist the recovered cumulative list with its source.
   Without reliable ownership evidence → **stop**: "Identify this subtask's changed files before validation."

5. Run the applicable `test:` and `lint:` commands from the resolved runbook in `WORK_DIR`.
   Missing commands, unavailable dependencies, or incomplete runs are reported as evidence
   gaps; do not claim a passing verification that did not run.

**Check completeness:**
- Each Acceptance Criterion from `T-XX/description.md`: met / not met / partial. Mark `[INCOMPLETE]` if not fully met.

**TDD check** (load the `tdd` rule for the contract being enforced):

Read `atomic-tests:` from the leaf block.

- `green` → run the `test:` command over this subtask's tests and confirm they still pass.
  Then audit the test set itself:
  1. **AC coverage** — every Acceptance Criterion maps to at least one test. An uncovered
     criterion is an `important` finding, even when the criterion is met by inspection.
     This test-mapping requirement does not apply to justified `n-a` or legacy exemptions.
  2. **No weakening** — compare the test set against the `tdd: red digest` line in `notes:`
     (written by `/pae-tests`; if it is absent, record an `important` finding; the integrity audit is incomplete). A missing
     test, a reduced test count with no additions, an introduced `skip`/`xfail`, or a
     vacuous assertion is a **`critical`** finding. Every test amendment must have its
     `tdd: test amended — …` line in `notes:` with a reason that blames the test, not the
     implementation.
  3. **Quality** — tests conform to `testing-standards`: AAA structure, behaviour not
     implementation, InMemory over `Mock()` for repositories, no `assert True` as the sole
     assertion, no order dependence. Violations are `important` findings.

- `pinned` reaching validation is itself a finding: characterization tests pin behaviour
  *before* a change and become `green` when `/pae-implement` completes it. A subtask that
  arrives here still `pinned` means the change was never finished or the status was never
  updated — an `important` finding, and the audit below is run regardless. For a subtask that
  went `pinned` → `green`, use `tdd: red digest` for the frozen test identities and the
  `tdd: characterize` note for the preserved behaviour, and a pinned test that was amended must carry
  both its amendment record and the accepted behaviour change (`tdd → ## Characterization
  mode`). An amended pinned test with no recorded behaviour change is a **`critical`**
  finding: it means a refactor changed behaviour and the test was edited to hide it.
- `n-a` → verify the justification line in `notes:` names which of unit/integration/contract/
  smoke was considered and why each is inapplicable. An unjustified or hand-waving `n-a`
  ("hard to test", "small change", "will add later", "existing tests cover it") is an
  **`important`** finding — record it and treat the subtask as untested.
- `red`, `not-started`, or `failed` while `atomic-execution: complete` → **`critical`** finding: the
  implementation was closed without reaching GREEN.
- Field absent → pre-TDD task. Note it, do not raise a finding.

**Find bugs** in changed files:
- **Edge cases**: null values, empty collections, repeated calls.
- **Error handling**: all error paths explicitly handled, no silent swallowing.
- **Interface contracts**: public interfaces in changed files respected.
- **Approach consistency**: implementation matches parent `## Solution Design → Decision`.
- **Invariants**: none violated.

For each bug: file, description, reproducible scenario, severity (`critical` / `important` / `optional`).

**Verdict:**
- **DONE**: all criteria met, no `critical` or `important` bugs.
- **NEEDS WORK**: has `[INCOMPLETE]`, `critical`, or `important` bugs.

Record the verdict in the parent `state.md → ## Subtask Progress` block for this T-XX:

- On **DONE**: do NOT mark `atomic-validation: complete` yet (that happens in `/pav-close`). Update `last_action: pav-check DONE` and preserve `notes`.
- On **NEEDS WORK**: set `atomic-validation: failed`, and in `notes:` list the specific Acceptance Criteria that were not met, plus `critical` / `important` bug summary. Do NOT create fix-tasks automatically — surface findings to the user first.

**If NEEDS WORK** → present the list of unmet criteria and bugs to the user. **Stop.** Do not proceed to Step 2.

Report: "Step 1 (Final Check) complete. Verdict: DONE / NEEDS WORK."
A passing result is a progress marker; return to the caller.
