## Goal
Duplicate units and statement units recognise table separator rows by the rule decided for extraction again, and the terminology-table check keeps its own stricter pattern under its own name.

## Context
- Dependencies: T-17 and the specification reconciliation after it (the stack tip).
- Source: found by the reconciliation of spec 08 after the proposal follow-ups (spec 08 Q-06 (a)), 2026-11-18. `scripts/audit-instructions.py` binds `TABLE_SEPARATOR_RE` twice: the separator rule decided for the extraction edge cases (`\|[-:|\s]+\|`, matched after trailing whitespace is removed) near the duplicate-unit code, and a stricter terminology-table pattern (`\|(?:\s*:?-+:?\s*\|)+\s*`) added later for `Terminology:` targets. The second binding wins at run time, so duplicate units and statement units now require a `-` in every cell: rows such as `| | |` or `|:|:|` count as content. Nobody approved that change. The delivered inventory is unaffected (the delivery gate passes).
- Decision: give the terminology-table pattern its own name and use it only for the terminology table; duplicate units and statement units use the decided separator rule again.
- Constraints: as the earlier follow-up subtasks (standard library only, annotations, verify writes nothing, no new git command, `METHOD_VERSION` unchanged, no planning identifiers in product content, frozen tests amended only when wrong with a recorded reason).
- Off-limits: every file except the two target files.

## Scope
- **In scope:** the two pattern names and their uses; tests.
- **Out of scope:** any other behaviour.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Failing tests: a separator row of the decided form with an empty or colon-only cell (`| | |`, `|:|:|`) is not a duplicate unit and not a statement unit; the terminology table still needs dashes in its separator row (a table whose second row is `| | |` is not a terminology table).
2. Rename and re-point.
3. Full suite and the delivery gate.

## Acceptance Criteria
- Each behaviour in Step 1 holds and has a test that failed before the change (the terminology case may pass before; record it as a pin).
- No earlier test changes.
- The suite passes and the delivery gate prints `GATE PASS` with `verify --strict` silent.

## Test Plan
- **Level:** integration.
- **Scenarios:** as Step 1.
- **Edge cases:** a separator row with tabs inside; a terminology table whose separator has alignment colons.
