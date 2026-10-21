## Goal
Preserve documented flag telemetry and dash-leading free text, and distinguish unavailable workflow verification from unknown step membership.

## Context
- Sources: two approved important integrated review findings.
- `parse_arguments` currently rejects every operand beginning with `--`, including documented `--flags "--step-by-step"`, spec-run flag text, and unrestricted nonempty flow labels.
- `check_step_name` checks directory readability without search permission; a mode-0400 workflows directory misreports a known step as unknown.
- Grouping: both checks were introduced by this unmerged implementation; fixes touch two files, add no invariant/schema and clear all four quick-flow gates.
- Arbiter interpretation: exact known helper options retain option semantics; other dash-leading operand text is accepted, and unknown tokens in option position are rejected. Shell quoting cannot encode a literal known option differently; no new escape interface is required for existing documented callers.

Off-limits: Do not read or change historical logs, add a new CLI escape syntax, change canonical vocabularies or retrospective/documentation behavior, or weaken existing tests.

## Scope
- **In scope:** Producer operand discrimination and workflow directory searchability, with permanent isolated regression coverage.
- **Out of scope:** New commands, literal-known-option encoding, storage/locking changes and unrelated refactoring.
- **Target files:** `scripts/log-step.sh`, `scripts/validate-contracts.sh`

## Steps
1. Freeze two failing focused regressions before implementation: documented/dash-leading operand preservation and readable-but-unsearchable workflow verification.
2. Distinguish known helper option tokens from ordinary operand text while preserving missing, duplicate, unknown-option and invalid-value rejection behavior.
3. Preserve exact documented workflow flags, unrestricted dash-leading flow inheritance and optional free text.
4. Require directory search permission alongside readability; unavailable verification still writes the valid event unchanged and emits one safe advisory.
5. Execute the isolated acceptance harness, full contract suite and shell syntax checks; preserve all frozen assertions.

## Acceptance Criteria
- Documented workflow flags and ordinary dash-leading free-text/flow values persist exactly, while known option tokens cannot be consumed as missing operands and unknown options remain rejected without side effects.
- A readable but unsearchable workflow directory yields exactly one verification-unavailable warning and persists the valid event unchanged; current, synthetic, unknown and missing-directory behavior remains correct.
- Both regressions run permanently through the isolated harness; the full suite, syntax and whitespace checks pass without real-log access.

## Test Plan
- **Level:** smoke
- **Scenarios:** Exact documented flag strings and dash-leading flow across start/step/end; optional free-text preservation; known-switch/missing/unknown arguments with storage hashes; real directory read/search permission combinations and exact persisted events/advisories.
- **Edge cases:** Same-event and wrong-event known options, multiple workflow flags in one operand, root permission bypass behavior, missing workflow directory, paths containing spaces and unchanged storage after rejected events.
