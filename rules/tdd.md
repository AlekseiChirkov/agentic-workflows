---
trigger: always_on
---

# TDD Contract

Test-Driven Development is a **mandatory, additive step** in the atomic execution cycle.
It does not replace any existing step — it precedes implementation and constrains it.

The canonical cycle is defined here; the executable step lives in `/pae-tests`.
Test *style* (AAA, InMemory repositories, naming, coverage targets, forbidden practices)
lives in `testing-standards` — this rule governs *process and enforcement*, not style.

---

## Where the step sits

```
/phase-atomic-execution
  1. /pae-tests      ← RED   — write failing tests from ## Acceptance Criteria
  2. /pae-implement  ← GREEN — write code until those tests pass, then REFACTOR
  3. /pae-finalize   ← record statuses
/phase-atomic-validation
  1. /pav-check      ← verifies the tests are still green and were not weakened
```

The step is per-leaf. Composites (Type 2) own integration-level Acceptance Criteria and
are covered by `/phase-composite-validation`, not by `/pae-tests`.

---

## The three states

`atomic-tests:` is a field in the leaf `## Subtask Progress` block (see
`workflow-globals → Canonical Status Formats`). Values:

| Value | Meaning | Set by |
|---|---|---|
| `not-started` | `/pae-tests` has not run for this subtask | default; absent field is read as this |
| `red` | Tests written, executed, and **observed failing for the expected reason** | `/pae-tests` |
| `green` | Implementation complete; every test from the RED set passes | `/pae-implement` |
| `n-a` | Test-level gate returned `none` — justification recorded | `/pae-tests` |
| `pinned` | Characterization tests written and observed **passing against the unchanged code** — behaviour-preserving work only | `/pae-tests --characterize` |
| `failed` | RED could not be reached (tests passed before implementation, or the suite errored) | `/pae-tests` |

**Backward compatibility:** a leaf block with no `atomic-tests:` field is a pre-TDD task.
Readers treat the missing field as `not-started` and must not fail on it. Workflows that
encounter an in-flight task (`atomic-execution: in-progress`) without the field continue
without retroactively demanding RED — record `notes: pre-TDD task, TDD step skipped` and
proceed.

---

## Test-level gate

Not all work is unit-testable. `/pae-tests` classifies every leaf before writing anything.
This is a checklist evaluated in order — the **first** level that applies wins.

| Level | Applies when | Executable form |
|---|---|---|
| `unit` | Pure logic: domain entities, use cases, transforms, validators, calculations | Test function asserting behaviour with InMemory fakes |
| `integration` | Crosses a real boundary: DB queries, migrations, external client, message bus | Test against a real (test) dependency |
| `contract` | Produces or consumes an interface another component depends on: HTTP route, event schema, shared payload | Test asserting status codes / response schema / payload shape |
| `smoke` | Declarative infrastructure or configuration with a validating tool: Terraform, k8s manifests, CI config, JSON/YAML schemas | `terraform validate` / `plan` assertion, schema validation, config lint — anything that fails before the change and passes after |
| `none` | **Only** when all four levels above are genuinely inapplicable | No test — justification required |

`none` is legitimate for: documentation-only changes, comment/docstring edits, dependency
pin bumps with no code change, pure file moves with no behaviour change, and formatting.

`none` is **not** legitimate for: "hard to test", "no test framework here", "will add tests
later", "the change is small", or "existing tests cover it". The first two are findings to
report, not exemptions; the last three are test-after in disguise.

**Justification record (mandatory when `none`).** `/pae-tests` writes one line to the leaf's
`notes:` field:

```
tdd: none — <which of unit/integration/contract/smoke was considered and why each is inapplicable>
```

An unjustified `n-a` is a validation finding in `/pav-check` and a code-review finding in
`/pv-review`.

---

## RED — what counts

A test is RED only when **all three** hold:

1. It exists as an executable artifact, runnable by the `test:` command from
   `.ai/context/runbook.md → ## Commands`.
2. It has been **actually run** and observed to fail. A test assumed to fail is not RED.
3. It fails **for the expected reason** — a missing function, an unimplemented branch, a
   wrong return value. A test that fails on an import error, a syntax error, a missing
   fixture, or a typo in the test itself is a broken test, not a RED test. Fix it and re-run.

If a newly written test **passes** before any implementation, that is a signal, not a
success. Either the behaviour already exists (then the subtask's scope is wrong — report it)
or the test asserts nothing meaningful (then it violates `testing-standards → Forbidden in
Tests`). Set `atomic-tests: failed`, record which test passed prematurely, and stop.

---

## Characterization mode — behaviour-preserving work

Some legitimate work changes no behaviour by definition: extracting a module, renaming
across a boundary, replacing a library with an equivalent, or optimising a hot path. Its
Acceptance Criterion is "the system does exactly what it did before", and no failing test can
be derived from that — the behaviour already exists, so any test of it passes immediately.

Before this mode, such work fell into the `none` exemption, which is wrong twice over: it is
not untestable, and it is precisely the work where a regression is hardest to notice.

**The inversion.** Ordinary TDD pins the *requirement* with a test that fails until the code
is written. Characterization pins the *current behaviour* with a test that passes before the
change and must keep passing through it. The safety property is the same — the test is
written before the code is touched, and the code may not edit the test to succeed.

### When it applies

Run `/pae-tests --characterize` when **all three** hold:

1. The subtask's Acceptance Criteria assert preserved behaviour, not new behaviour.
2. The behaviour being preserved is observable today — it can be executed and asserted now.
3. No requirement changes. A refactor that also fixes a bug or adds a field is not
   behaviour-preserving; split it, and the new behaviour goes through ordinary RED.

If any one fails, this is ordinary work: use the standard gate. Characterization is **not** a
softer option for work that is merely hard to specify — that reasoning is how the `none`
exemption was abused, and it is no more valid here.

### The procedure

1. **Classify the level** with the ordinary test-level gate. Characterization is a mode, not
   a level; the tests are still unit, integration, contract, or smoke.
2. **Capture current behaviour.** Write tests asserting what the system does *now*, including
   behaviour that looks wrong. A characterization test records reality; a bug preserved
   through a refactor is a correct outcome, and a bug fixed by accident is an unrequested
   behaviour change. Where current behaviour is genuinely wrong, record it:
   `tdd: characterize — <test name> pins existing incorrect behaviour: <what is wrong>`
   and raise it as a finding. Do not fix it inside a refactor.
3. **Run them against the unchanged code. They must pass.** This is the mode's equivalent of
   observing RED, and it is just as mandatory: a characterization test that *fails* before
   the change means it does not describe current behaviour. Fix the test — never the code —
   and re-run.
4. **Set `atomic-tests: pinned`** and write one note:
   `tdd: characterize — <N> tests pin <what behaviour>, verified passing before the change`
5. **Coverage check before proceeding.** Every entry point and branch the change will touch
   must be covered. Refactoring code whose behaviour is unpinned is exactly the ordinary
   untested change this rule exists to prevent — name any gap, and either pin it or move it
   out of scope.

### During the change

The pinned set is frozen exactly as a RED set is — the prohibitions in `## GREEN` apply
without modification. One addition, and it is the important one:

**A pinned test that goes red during the change is a defect in the change, never a defect in
the test.** The correct response is to fix the code. Amending a pinned test requires the same
recorded justification as amending a RED test *and* an explicit statement of the behaviour
change being accepted — at which point the work is no longer behaviour-preserving and needs a
requirement, an Acceptance Criterion, and very likely an ADR.

`/pae-implement` sets `atomic-tests: green` when the change is complete and the whole pinned
set still passes. `pinned` → `green` is the mode's only legal transition.

---

## GREEN — what implementation may and may not do

During `/pae-implement`, the RED test set is a **frozen contract**.

**Forbidden without an explicit, recorded amendment:**
- Deleting, renaming, commenting out, or `skip`/`xfail`-marking any test from the RED set.
- Weakening an assertion (narrowing a range, replacing an exact value with a truthiness
  check, removing a case from a parametrized set).
- Changing an expected value in a test to match what the implementation happens to produce.

**Permitted amendments** — a RED test may be corrected when the *test itself* is wrong, not
when the implementation is inconvenient. Legitimate causes: the test encoded a
misunderstanding of the Acceptance Criterion, used a wrong fixture, or asserted an
implementation detail rather than behaviour (`testing-standards → Test Behavior, Not
Implementation`). Every amendment is recorded in the leaf's `notes:`:

```
tdd: test amended — <test name> — <what changed and why the original was wrong>
```

Adding *new* tests during GREEN is always allowed and never needs an amendment record.

**Refactor.** Once every RED test passes, refactoring is permitted only while the whole
suite stays green, and only within the subtask's `## Scope`. Rerun the tests after
refactoring. Refactoring is not an excuse to widen scope.

---

## Interaction with existing mechanisms

**Flow tiers.** `flow: full` runs `/pae-tests` per leaf. `flow: quick` has no T-XX subtasks,
so it runs the TDD step inline against `## Contract (quick) → ### Acceptance Criteria` —
see `quick-flow → The quick path`. The gate and the RED definition are identical in both
tiers; only the location of the Acceptance Criteria differs.

**Tripwire.** If the composite-promotion tripwire fires in `/pae-implement`, the RED tests
already written are redistributed to the children whose Acceptance Criteria they cover, and
each child re-enters the cycle at `/pae-tests`. Tests are never discarded on promotion.

**Blockers.** A test that cannot reach RED because of a missing external dependency is a
blocker like any other: set `blocker:`, stop, report. Do not downgrade the gate to `none`
to get unblocked — that converts an external problem into a permanent hole in coverage.

**Autonomous modes.** `/phase-pipeline` and autonomous Discovery do not suspend this rule.
The test-level gate is decided by the classifier above, not by the Autonomous Decision
Protocol, and `none` still requires its justification line. An autonomous run may not
choose `none` to save time.

---

## Why the order matters

Correct tests + wrong code → the tests catch the bug.
Wrong tests + correct code → the wrong thing was built and nobody knows.

Tests written after the implementation are shaped by the code that already exists: they
document what was built, not what was required. Writing them first is what makes them a
check on the requirement rather than a description of the outcome.
