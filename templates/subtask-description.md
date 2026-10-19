# Subtask Description Template

## Goal
One sentence: what exists and works when this subtask is done.
Format: "<Subject> can/does <action> <measurable condition>."
Example: "Users can authenticate with email/password and receive a JWT token valid for 24h."

## Context
- working_dir: <relative path from the task directory to the repo where this subtask runs, e.g. ../../../../service-api — omit entirely for single-repo tasks>
- Dependencies: which T-XX this subtask depends on and why.
- Constraints: technical or architectural limits that apply here.
- Reason: why this subtask exists as a separate unit.

## Scope
In scope: what this subtask explicitly covers.

Out of scope: list specific things that could be confused as part of this
subtask but are NOT included. Be explicit — name actual features, files,
or behaviours, not vague categories.
Example: "Frontend changes, error logging setup, unrelated database migrations."

Target files: list of files expected to be created or modified.
Example: "src/auth/service.py, src/auth/router.py, tests/test_auth.py"

## Steps
Numbered steps (3–15).
Each step must be:
- Scoped to one domain or module (not one file operation)
- Verifiable independently — end with a checkable result
- Written as: "<action> in <location> so that <verifiable outcome>"

## Acceptance Criteria
Each criterion must be:
- Binary: passes or fails — no "works correctly" or "functions as expected"
- Testable without author context
- Mapped to a specific behaviour or step outcome
Format: "Given <condition>, <subject> <does/returns/produces> <exact result>."

## Test Plan
Consumed by `/pae-tests` to write the failing tests before implementation begins.
Contract: the `tdd` rule. Style: `testing-standards`.

- **Level:** unit | integration | contract | smoke | none
  Classify with the test-level gate — evaluate unit → integration → contract → smoke → none
  in order, first match wins. List more than one when the subtask needs more than one.
- **Scenarios:** one line per Acceptance Criterion — every criterion must appear here.
  Format: "<criterion restated as a scenario> → <expected observable outcome>"
- **Edge cases:** applicable categories from testing-standards → Edge Cases Checklist
  (happy path, empty/null, boundary values, duplicate operations, invalid state transitions,
  missing dependencies, concurrency, permission boundaries).
- **Justification:** required only when Level is `none` — which of unit/integration/contract/
  smoke was considered and why each is inapplicable. "Hard to test", "no framework", "small
  change", "will add later", and "existing tests cover it" are not valid justifications.
