# Focused native and correlated shell delivery

## Goal

Native completion and correlated event delivery use focused shell functions while preserving all existing public outputs, side effects and rejection/retry behavior.

## Context

- Dependencies: T-05 and the complete reviewed feature stack.
- Constraints: principles/code-quality.md limits functions to 30 lines and three parameters unless a specific exception is justified; retain the parent's explicitly enumerated baseline/predicate/fixture exceptions.
- Reason: independent task-level review found oversized new delivery functions and a six-parameter metadata helper. Arbiter structural analysis selected meaningful phase extraction over broad exceptions or compressed lines.

## Scope

In scope: split adapter dispatch, lexical report scanning/canonical validation, bounded transcript/evidence and native completion phases; split producer correlated argument validation, jq/legacy serialization and step parsing/replay/staging/emission/commit. Pass one coherent metadata context rather than six domain parameters. Add a focused source contract and preserve existing runtime fixtures.

Out of scope: new payloads or fields, changed native/profile/marker semantics, new dependency or minimum Bash version, new event ordering or messages, new persistence guarantees, inherited unrelated function rewrites, cost/token changes, deployment and history mutation.

Target files: tests/hook-shell-quality.sh, scripts/validate-contracts.sh, hooks/log-step-hook.sh, scripts/log-step.sh. Test implementation may refine the contract location after inspecting existing fixtures, but additions must be reported before mutation.

## Steps

1. Add a source contract that exposes the unapproved oversized introduced/extended functions and metadata positional API, and pin existing adapter/producer behavior before product edits. Observe the contract fail and preserve a complete test digest.
2. Extract cohesive adapter phases so every fresh or selected repaired shell function fits 30 lines and three domain parameters, except the individually justified cached-record jq predicate. Preserve gating, native/report bindings, state ownership and frozen retries.
3. Extract producer phases and introduce a coherent metadata context so acceptance, append/metadata rollback, duplicate receipts, historical lint, exact raw-number handling and optional-jq behavior remain identical. Preserve original fault-injection surfaces.
4. Audit all task-introduced/task-extended shell functions with structural search and the narrow exception list; run focused and complete isolated acceptance with no weakened tests.

## Acceptance Criteria

- Given the current oversized shell sources, the new focused source contract fails before extraction; after extraction all newly introduced and specifically repaired functions meet 30 lines and three domain parameters, with only the individually justified exceptions retained and no line-compression workaround.
- Given the unchanged adapter fixtures, explicit attribution, lexical/native evidence, private cached validation, unknown sessions, duplicate/retry/fallback ownership and bounded diagnostics remain identical.
- Given the unchanged producer/lint fixtures, legacy and correlated output, exact clocks, no mutation on invalid input, concurrent replay and actual partial-append/metadata rollback remain identical; the metadata staging API takes at most three coherent parameters.
- Given the complete isolated harness, all original frozen tests, installation/workflow/timing composition, canonical contract, shell syntax and task artifacts pass without model calls, real deployment or historical-log access.

## Test Plan

- Level: contract, integration.
- Scenarios: source-size/context contract observes the present defect before product edits; all four acceptance criteria map to source checks and the existing focused adapter/producer/install/workflow/timing fixtures. Add behavior characterization only for a genuine uncovered extraction branch, without changing any existing assertion.
- Edge cases: malformed native/report/private records, nested fences, canonical numeric tokens, ambiguous or missing evidence, zero-length spans, interleaved and duplicate deliveries, frozen retry after transcript rotation, fallback one-attempt ownership, dependency absence, partial event output, metadata replacement failure and paths with spaces.
