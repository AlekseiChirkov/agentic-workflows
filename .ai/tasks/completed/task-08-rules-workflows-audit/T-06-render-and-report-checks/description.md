## Goal
`render` produces the report's generated region deterministically and `verify` checks the report's layout, review line, blockers and generated region.

## Context
- Dependencies: T-05 (complete verifier rules and valid fixture).
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec DM-8 (layout, subsections, columns, row order, escaping) and the report codes of DM-9; `render` contract and exit codes.
- Reason: Rendering and report checking form one component around the report file, with one done-state: the region round-trips and every layout fault has a code.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** the `render` subcommand with `--write`; all eighteen generated subsections; cell escaping; passport values including read coverage and finding counts; validator and test impact counts by context; report layout parsing; review and acceptance line grammar; `git cat-file -e` for the reviewed commit; `report-name-date`; `blocker-unlisted`; `report-generated-mismatch`; the last per-code fixture cases so that every code has one.
- **Out of scope:** writing the hand-written sections of the real report; the real audit run.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing cases for the round trip, the layout faults and the impact fixture.
2. Implement table and bullet rendering helpers with `|` escaped and line breaks replaced by spaces.
3. Render Passport, Inventory, Sections, References (count table and defect edges), Loads, the three candidate tables and Repetition review.
4. Render Legacy mentions, Duplicates, Migration map with computed deviation, and Validator and test impact with edge counts by validator context, other tests, frozen, hooks and other active readers.
5. Render Spec 09 inputs, Findings, Amendments, Read coverage and Installed comparison (or the line `Not verified.`).
6. Add `render --root --report [--write]`: print the region with both marker lines, or replace it in the file atomically; exit 1 with diagnostics when inputs fail a schema rule, exit 2 when markers are missing or repeated under `--write`.
7. Parse the report layout in `verify`: title, section order, single marker pair, one review line and one acceptance line in their grammars (`report-missing`, `report-layout`, `report-name-date`).
8. Check the reviewed commit with the permitted git command (`review-commit-unknown`), the blockers section (`blocker-unlisted`) and the region against fresh render output (`report-generated-mismatch`).
9. Add a completeness case that every diagnostic code has a producing fixture and that the valid fixture exits 0 with empty output.

## Acceptance Criteria
- On a valid fixture, `render --write` changes the report only between the two marker lines, and a second run changes nothing.
- Changing one character inside the generated region yields `report-generated-mismatch`; duplicating a marker yields `report-layout`.
- A fixture report missing the id of a `blocks_09: true` finding under its blockers heading yields `blocker-unlisted`.
- Given a fixture map renaming `rules/a-b.md` and readers naming it once in a `check "…"` description, once in a validator expression, once in `tests/t.py` and once under `tests/fixtures/validator-runtime/`, the impact row shows 1 in each of those four columns.
- With an `unavailable` coverage entry and its finding, the rendered passport says `read_coverage: partial (1 gaps)`.
- A review line naming a commit absent from the fixture repository yields `review-commit-unknown`; a file-name date different from `run_date` yields `report-name-date`.
- `render --write` on a report without markers exits 2 and leaves the file unchanged.
- For every diagnostic code of the verifier a fixture case produces it, and the fully valid fixture produces none and exit 0.
- `python3 -I scripts/check-audit-instructions.py` exits 0.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - round trip → only the region changes; idempotent
  - region edit and duplicated marker → two codes
  - unlisted blocker → `blocker-unlisted`
  - impact fixture → 1 in four columns
  - coverage gap → partial passport line
  - unknown commit and date mismatch → two codes
  - missing markers under `--write` → exit 2, file unchanged
  - per-code completeness; valid fixture silent
  - suite exits 0
- **Edge cases:** cell text containing `|` and line breaks; empty tables; `none` for empty repetition lists; `Reviewed: pending`; malformed review date; role label with invalid characters; `Accepted: owner <date>`; repeated section heading; report without git.
