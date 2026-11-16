## Goal
The optional findings left by the independent reviews of the follow-up series are fixed, so no review finding of this task stays open.

## Context
- Origin: owner request of 2026-11-16 to fix every remaining finding.
- Constraints: Python 3.11+, standard library only; no signal handler and no change of the signal disposition at start-up; exit codes 0–8 and the code tables stay closed; English only; no planning identifiers in product content. Do not add or remove lines of `docs/USAGE.md` above line 255.
- Pinned fixtures: refreshed once after the last source edit.

Off-limits: no file under `workflows/` or `rules/`; no new source-guard record; no change to the validator's statements.

## Scope
- **In scope:** start-up interrupt handling of the tool; rendering of control characters in error messages; the manual's signal sentence and fence bullet; last-byte termination of the ignore file in both setup scripts and whole-line comparison in the umbrella setup; one spacing revert in the suite.
- **Out of scope:** a launcher for the tool; escaping of non-ASCII line separators; an interrupt after the result was written.
- **Target files:** scripts/state-tool.py, scripts/setup-new-project.sh, scripts/setup-umbrella.sh, docs/USAGE.md, tests/state-tool.py, tests/fixtures/validator-runtime/inventory-amendment.json, tests/validator-runtime-oracle.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py

## Steps
1. Add failing cases for each finding; amend the two pinned manual sentences that were inaccurate.
2. Guard the tool's imports and body so an interrupt ends it by the signal, only when it runs as the main program.
3. Render control characters in error messages as visible escapes.
4. Compare the last byte of the ignore file as a byte in both setup scripts; compare whole lines in the umbrella setup.
5. Correct the manual sentences; refresh the pinned fixtures; run the suites.

## Acceptance Criteria
- An interrupt after the script's first statement ends the tool by the signal with empty stdout and stderr when it runs as the main program; under another module name the interrupt reaches the loading program and no disposition changes.
- Every stderr diagnostic is one line for arguments holding control characters; stdout stays one JSON object.
- An ignore file whose last byte is not a line feed, NUL included, is terminated before the first append by both setup scripts; the umbrella setup counts only whole lines and leaves a complete file byte-identical.
- The manual states the exact outcome of block creation next to an unclosed fence and the remaining limit of interrupt handling.
- All earlier tests pass; only the two inaccurate pinned sentences were amended.

## Test Plan
- **Level:** integration (subprocess runs and disposable projects), unit for the in-process load, smoke for manual sentences.
- **Scenarios:** interrupt during imports and at the first definition; in-process load interrupted; control characters in five argument positions; ignore files ending in NUL or without a line feed for both scripts.
- **Edge cases:** complete ignore file unchanged; fresh ignore file.
