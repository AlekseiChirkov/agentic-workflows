## Goal
The state tool's read commands warn, without failing, when the project memory's entry for a task claims a number of reviewed leaves or a pull request range that the task's own leaf records do not support.

## Context
- Dependencies: T-17.
- Source: T-10 Do Later, ordered applied by the owner on 2026-11-18. During the audit run the memory entry claimed "all ten leaves reviewed (#105–#114)" before the last leaf was reviewed; a consistency warning would have caught it. Decision (recommended option of the planning pass, taken under the owner's order): a free-text heuristic in the state tool's read commands, never in the contract validator.
- Facts from the planning pass: `scripts/state-tool.py` (about 1979 lines) already returns warning code strings from `get` and `validate` (`advisory_warnings` near :743, `command_get` near :1786, `command_validate` near :1804). Its suite is `tests/state-tool.py`, run by `bash scripts/validate-contracts.sh --state-tool-only`. The contract validator reads `state-tool.py` by AST: do not change the four status constants.
- Behaviour:
  - Only in the read commands. Read `<root>/.ai/memory/state.md` without following a symbolic link, with a size bound and strict UTF-8; any failure means no warning, never an error.
  - Find the `## Active Tasks` or `## Done` entry line that links to this task's `state.md` (or names the task directory).
  - Parse narrow patterns only: `(all )?<number or number word>( of <n>)? leaves reviewed` and a pull request range `#A–#B` (en dash or hyphen, optional second `#`).
  - Compare with the count of leaf blocks with `atomic-validation: complete` and with the set of their `pr: #N` numbers.
  - On a mismatch, emit the non-blocking warning code `memory-state-mismatch`; exit codes stay unchanged. Document the code in the module docstring and wherever the tool's warning codes are listed (`docs/` manual section, if one lists them).
- Constraints: Python 3.11+ standard library; type annotations; the tool's existing locking, receipts and write paths unchanged; no workflow or rule change; no planning identifiers in product content.
- Off-limits: `scripts/validate-contracts.sh` (no new check), `rules/`, `workflows/`, `harness/`, `templates/`, the audit tool and outputs, specifications.

## Scope
- **In scope:** the warning in `scripts/state-tool.py`, its tests in `tests/state-tool.py`, the warning-code documentation.
- **Out of scope:** structured claim fields written by workflows.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`, and the manual section that lists state-tool warning codes if one exists

## Steps
1. Failing tests: the historical line "all ten leaves reviewed (draft PRs #105–#114 …)" with one leaf not complete → `memory-state-mismatch`; consistent claims → no warning; no memory file, a symbolic-linked memory file or invalid UTF-8 → no warning and unchanged exit; a range whose numbers match the leaves' `pr:` fields → none; exit codes unchanged in every case.
2. Implement.
3. `bash scripts/validate-contracts.sh --state-tool-only`, then the complete validator.

## Acceptance Criteria
- Each behaviour in Step 1 holds and has a test that failed before its implementation.
- No earlier state-tool test changes.
- The state-tool suite and the complete validator report 0 failed.

## Test Plan
- **Level:** integration (temporary project roots).
- **Scenarios:** as Step 1.
- **Edge cases:** a number word ("ten"), "9 of 10 leaves reviewed", a hyphen range, a task with no leaves, a memory line for another task naming a similar directory.
