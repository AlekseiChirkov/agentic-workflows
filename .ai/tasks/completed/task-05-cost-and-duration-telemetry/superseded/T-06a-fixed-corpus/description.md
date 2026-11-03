## Goal
Provide fixed explicit retrospective corpus with observable, deterministic behavior.

## Context
- Dependencies: T-05b — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Corpus selection and freezing; AC-13, AC-18; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** fixed explicit retrospective corpus, including all applicable requirements and negative cases in Corpus selection and freezing; AC-13, AC-18.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_report.py, tests/usage-fixed-corpus.py, scripts/usage-telemetry.py.

## Steps
1. Validate a bounded explicit corpus manifest, selected files, digests and access scope.
2. Freeze as_of, scenario, versions, inclusions and exclusions before analysis.
3. Filter late evidence by observation time and preserve reproducible corpus identity.

## Acceptance Criteria
- The analyzer consumes only explicitly selected hash-verified inputs and excludes evidence first observed after as_of.
- A late correction cannot change a reproduced older corpus and input permutations preserve semantic results.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - The analyzer consumes only explicitly selected hash-verified inputs and excludes evidence first observed after as_of. → the stated result is observed.
  - A late correction cannot change a reproduced older corpus and input permutations preserve semantic results. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
