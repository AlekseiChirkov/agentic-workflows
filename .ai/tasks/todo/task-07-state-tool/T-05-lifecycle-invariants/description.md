## Goal
`set` refuses status changes that break the canonical lifecycle invariants (no downgrade,
`pinned → green`, justified `n-a`, completion preconditions, pre-TDD guard, `green` only
from `red` or `pinned`) and applies a group of fields and notes entirely or not at all.

## Context
- Dependencies: T-03 (write transaction), T-04 (`--note` on `set`, needed for the `n-a`
  justification and the pre-TDD note), T-02 (static predicates).
- Constraints: same runtime limits as the tool. Contract: task spec `### Invariants`
  (I-2, I-3, I-4, I-5, I-9, I-10 and the paragraph after the table), REQ-04, REQ-23.
  Accepted gaps stay open: moves inside rank 1, atomic-validation and composite statuses
  are checked by vocabulary only. English only; no planning identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: transition checks need the previous value and form one rule set, separate from
  serialization and from static validation.

Off-limits: no transition table beyond the listed invariants; the tool never chooses a
test level and never removes `atomic-tests`; no file under `workflows/` or `rules/`.

## Scope
- **In scope:** I-2 rank order, I-3, I-4 on change to `n-a`, I-5 on change to `complete`,
  I-9, I-10; evaluation against changed fields only; `pre-existing-violation` warnings;
  all-or-nothing application of several fields and notes.
- **Out of scope:** new vocabulary values; checks for `rollup` /
  `integration-validation` transitions.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below.
2. Implement the `atomic-tests` rank order (`not-started` 0; `red`, `pinned`, `n-a`,
   `failed` 1; `green` 2; absent segment 0) with `downgrade` (I-2) and `pinned-transition`
   (I-3).
3. Implement `invalid-transition` (I-10): `green` only from `red` or `pinned`.
4. Implement `n-a-unjustified` (I-4) and `completion-without-tests` (I-5) against the
   resulting block, including notes added by the same call and the previous
   `atomic-execution` value for the pre-TDD path.
5. Implement `pre-tdd-not-applicable` (I-9).
6. Evaluate invariants only for fields the operation changes, after the `unchanged`
   shortcut; report a violation in an unchanged field as warning `pre-existing-violation`.
7. Confirm that any refusal leaves `state.md` unchanged and no temporary file, whatever
   the number of valid fields and notes in the same call.
8. Refresh the pinned source-guard fingerprint and run the guard suites and the focused
   state-tool mode.

## Acceptance Criteria
- `pinned → green` is applied; `pinned → red` exits 6 `pinned-transition`; `green → red`
  and `red → not-started` exit 6 `downgrade`.
- `→ n-a` without a `tdd: none — ` note exits 6 `n-a-unjustified`; with
  `--note "tdd: none — smoke considered; no executable surface"` it is applied.
- `n-a → green`, `failed → green` and `not-started → green` exit 6 `invalid-transition`.
- Given a leaf without `atomic-tests:` and `atomic-execution: in-progress`,
  `set --field atomic-execution=complete` exits 6 `completion-without-tests`; with
  `--note "pre-TDD task, TDD step skipped"` it is applied and the header still has no
  `atomic-tests` segment.
- Given `atomic-tests: not-started` or `red`, completion exits 6 `completion-without-tests`.
- Given a leaf without `atomic-tests:` and `atomic-execution: not-started`,
  `set --field atomic-execution=in-progress` exits 6 `pre-tdd-not-applicable`; with
  `--field atomic-tests=red` added it is applied.
- `set --field last_action=x --field atomic-execution=done --note y` exits 6
  `invalid-value` and the fixture is unchanged.
- `set --field atomic-tests=n-a --field last_action=x --note "tdd: none — smoke considered; no executable surface"`
  on `atomic-tests: not-started` is applied with all three changes in one revision.
- Given `atomic-tests: n-a` with notes containing `tdd: none - x` (hyphen),
  `set --field last_action=y` is applied with warning `pre-existing-violation`.
- Every refused fixture is unchanged and holds no temporary file; `failed → red` is
  applied (accepted gap).

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Pinned, downgrade and green-source transitions → applied or the named exit-6 code.
  - `n-a` with and without justification → applied / `n-a-unjustified`.
  - Completion on pre-TDD, `not-started`, `red` blocks → the named results.
  - Pre-TDD start without and with `atomic-tests` → refused / applied.
  - Mixed valid and invalid inputs → exit 6, nothing changed.
  - Three valid changes → one revision.
  - Pre-existing violation in an unchanged field → applied with warning.
- **Edge cases:** justification present only in a later `notes` group; setting a status to
  its current value alongside a real change; composite block status set (vocabulary only).
