## Goal
Provide bounded explicit source selection with observable, deterministic behavior.

## Context
- Dependencies: T-01d — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Interfaces and envelopes; limits; AC-15, AC-24; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** bounded explicit source selection, including all applicable requirements and negative cases in Interfaces and envelopes; limits; AC-15, AC-24.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_sources.py, tests/usage-source-selection.py, scripts/usage-telemetry.py.

## Steps
1. Validate the manifest, selection scope, explicit limits and fixed source metadata before reads.
2. Open selected regular files without following forbidden paths and verify full or preselected prefix hashes.
3. Enforce per-file, aggregate, record and nesting limits without silent truncation.

## Acceptance Criteria
- A selected regular file at the declared size and digest is accepted; a changed source and a missing mandatory limit are rejected.
- An explicitly authorized external regular file may be selected without reading its neighbors; symlinks, scope violations and excess size, depth or records are rejected.

- An exact declared byte boundary is accepted, one byte beyond is rejected, multibyte text is measured in bytes, and a changed preverified prefix fails integrity verification.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - A selected regular file at the declared size and digest is accepted; a changed source and a missing mandatory limit are rejected. → the stated result is observed.
  - An explicitly authorized external regular file may be selected without reading its neighbors; symlinks, scope violations and excess size, depth or records are rejected. → the stated result is observed.
  - An exact declared byte boundary is accepted, one byte beyond is rejected, multibyte text is measured in bytes, and a changed preverified prefix fails integrity verification. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
