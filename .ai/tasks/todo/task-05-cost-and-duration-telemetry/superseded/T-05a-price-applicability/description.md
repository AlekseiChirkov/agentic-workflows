## Goal
Provide price snapshot and scenario applicability with observable, deterministic behavior.

## Context
- Dependencies: T-04e — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Price scenarios and applicability; AC-04; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** price snapshot and scenario applicability, including all applicable requirements and negative cases in Price scenarios and applicability; AC-04.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_pricing.py, tests/usage-price-applicability.py.

## Steps
1. Validate immutable price snapshots and named historical or reprice scenarios.
2. Resolve exact model, period, cache TTL, service, region, modality, tool unit and threshold applicability.
3. Reject ambiguous rates and retain unavailable price reasons without substitutions.

## Acceptance Criteria
- Historical prices require proven effective intervals and exact model, service, region, modality and unit applicability.
- Conflicting intervals, unresolved aliases and missing historical prices remain unpriced; explicit reprice remains conditional.
- An absent multiplier declaration means unknown applicability and cannot establish a reliable price without evidence. An absent tool identifier means unknown identity and cannot be matched by guessing.

- A threshold using strict greater-than leaves an input of 1000 at the base rate and applies the multiplier at 1001; cache TTL and separately billed tools require matching rates.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Historical prices require proven effective intervals and exact model, service, region, modality and unit applicability. → the stated result is observed.
  - Conflicting intervals, unresolved aliases and missing historical prices remain unpriced; explicit reprice remains conditional. → the stated result is observed.
  - Missing multiplier declarations and tool identifiers remain unpriced unless separate evidence establishes applicability and identity; no unique-looking rate is selected by inference.
  - A threshold using strict greater-than leaves an input of 1000 at the base rate and applies the multiplier at 1001; cache TTL and separately billed tools require matching rates. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
