## Goal
Provide stream finality and revisions with observable, deterministic behavior.

## Context
- Dependencies: T-04a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Stream and revision resolution; AC-09; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** stream finality and revisions, including all applicable requirements and negative cases in Stream and revision resolution; AC-09.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-stream-revisions.py.

## Steps
1. Group observations by verified response and deduplicate snapshot and delta evidence.
2. Resolve finality and corrections using proof of sequence continuity and valid revision relationships.
3. Report partial or conflicted measurements without choosing a maximum or received-last value.

## Acceptance Criteria
- Partial outputs 1 and 40 followed by final 100 resolve to 100 in every input order.
- A sequence with increments 1 and 3 but missing 2 remains partial even after a terminal event; incompatible finals conflict.

- Duplicate increments are counted once; correction cycles and incompatible final successors remain conflicted unless a valid correction chain proves the replacement.

- A proven correction successor replaces its final predecessor, while a stream without a final snapshot remains partial at its last ordered evidenced value.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Partial outputs 1 and 40 followed by final 100 resolve to 100 in every input order. → the stated result is observed.
  - A sequence with increments 1 and 3 but missing 2 remains partial even after a terminal event; incompatible finals conflict. → the stated result is observed.
  - Duplicate increments are counted once; correction cycles and incompatible final successors remain conflicted unless a valid correction chain proves the replacement. → the stated result is observed.
  - A proven correction successor replaces its final predecessor, while a stream without a final snapshot remains partial at its last ordered evidenced value. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
