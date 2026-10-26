# Honest timing and end-to-end evidence

## Goal
Retrospective analysis separates elapsed coverage from nested worker spans and proves all hook acceptance scenarios using isolated fixtures.

## Context
- Dependencies: T-04.
- Constraints: preserve validated nonblocking logging, explicit attribution and private active correlation; read the parent solution design.
- Reason: one coherent honest timing and end-to-end evidence component with its own independently verifiable acceptance cluster.

## Scope
In scope: Retrospective analysis separates elapsed coverage from nested worker spans and proves all hook acceptance scenarios using isolated fixtures.

Out of scope: cost/token schemas, git protection hooks, broad harness migration, historical telemetry mutation, automatic merges. Other leaves own their named components.

Target files: workflows/retro.md, scripts/run-log-timing.sh, scripts/run-log-timing.py, tests/hook-timing.sh, scripts/validate-contracts.sh, tests/log-step-hook.sh, docs/USAGE.md, scripts/README.md, docs/README.md, harness/claude/capabilities.md, tests/hook-workflow-contract.sh. The Bash launcher delegates to a source-only Python standard-library engine. Add a real partial-append retry regression to the existing correlated producer suite, retaining frozen checks. Harmonize annotations in task-introduced adapter/producer Python fixtures without changing executable bodies, assertions or generated producer bytes; add a scoped standards check. Paths may be refined after inspecting existing patterns; report additions explicitly.

## Steps
1. Freeze deterministic sequential, gapped, waiting, nested and parallel timing fixtures with independent expected denominators and two-run end-to-end scenarios.
2. Implement the specification's half-open interval formulas over explicitly selected validated input, reporting wall time, work/observed union coverage, uncovered gaps, nested/parallel overlap, inclusive/exclusive spans, worker totals and explicit waiting distinctly. Keep unknown session spans out of named-step timing.
3. Integrate approximate-source labeling and partial/unavailable coverage into retrospective instructions without rewriting history.
4. Connect all focused hook fixtures to appropriate contract validation and document installation, correlation, fallback and timing semantics.
5. Run end-to-end fixtures plus existing logging acceptance checks, shell syntax and complete contract validation.

## Acceptance Criteria
- Given a fully covered sequential fixture, nonoverlapping observed intervals sum within five percent of run wall time and all uncovered gaps are labeled.
- Given nested, parallel and waiting spans, inclusive/exclusive/worker durations, union coverage, overlap and waiting use explicit denominators and overlapping span totals are never equated with wall time or actual CPU work.
- Given approximate, legacy, incomplete or invalid data, retrospective labels eligible approximate runs and excludes unusable timing observations with disclosed coverage.
- Given the complete isolated acceptance harness, two-run attribution, duplicate/out-of-order handling, single-session gaps, unavailable hooks and owned user settings lifecycle pass without a model or access to real historical logs.

- Given out-of-run intervals, missing or cyclic parent references, negative/non-finite timestamps, multiple roots, overlaps and successive checkpoints on one agent, timing analysis rejects unusable observations or reports them explicitly without plausible fabricated metrics.

## Test Plan
- Level: integration, contract
- Scenarios:
  - Given a fully covered sequential fixture, nonoverlapping observed intervals sum within five percent of run wall time and all uncovered gaps are labeled. → assert the stated observable result in isolated executable fixtures.
  - Given nested, parallel and waiting spans, inclusive/exclusive/worker durations, union coverage, overlap and waiting use explicit denominators and overlapping span totals are never equated with wall time or actual CPU work. → assert the stated observable result in isolated executable fixtures.
  - Given approximate, legacy, incomplete or invalid data, retrospective labels eligible approximate runs and excludes unusable timing observations with disclosed coverage. → assert the stated observable result in isolated executable fixtures.
  - Given the complete isolated acceptance harness, two-run attribution, duplicate/out-of-order handling, single-session gaps, unavailable hooks and owned user settings lifecycle pass without a model or access to real historical logs. → assert the stated observable result in isolated executable fixtures.
- Edge cases: empty/null inputs, canonical count boundaries, duplicates, invalid transitions, missing dependencies, concurrent delivery, paths with spaces, permission failures, no-mutation on rejection.
- Invalid interval graph scenarios: enforce run bounds and valid parent hierarchy; disclose excluded observations and do not confuse repeated checkpoints on one agent.

### Description Amendments

- 2026-10-26: Apply the two documentation precision proposals before closure: qualify unique native Skill evidence as named-step coverage, retain explicitly correlated unknown-session observations, and state the native flock requirement separately from ordinary logging dependencies. Add two workflow documentation-contract regressions without changing any existing group or helper. Source: independent review, Arbiter analysis and the owner's autonomous implementation authorization. Runtime behavior and acceptance criteria are unchanged.
