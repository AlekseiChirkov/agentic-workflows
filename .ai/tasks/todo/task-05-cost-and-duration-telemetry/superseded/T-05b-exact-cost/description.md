## Goal
Provide exact cost computation and completeness with observable, deterministic behavior.

## Context
- Dependencies: T-05a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Formula and precision; AC-02, AC-16, AC-23; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** exact cost computation and completeness, including all applicable requirements and negative cases in Formula and precision; AC-02, AC-16, AC-23.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_pricing.py, tests/usage-exact-cost.py.

## Steps
1. Compute independent priced components using exact integers and finite decimal arithmetic.
2. Classify complete cost, proven lower bound and subtotal-only amounts from evidenced coverage.
3. Sum before half-even display rounding and preserve exact machine-readable decimal values.

## Acceptance Criteria
- The supplied synthetic examples yield exact 0.00264, 0.00289 and partial subtotal 0.00224.
- Two 0.015 components sum to 0.03 before half-even display rounding; a partial subtotal never populates complete cost.

- An unsupported nonterminating rate unit remains unpriced; two 0.005 amounts total exactly 0.01 before display rounding.

- Derived sums above 9007199254740991 remain exact decimal strings; zero model responses plus a proven 0.02 separately billed tool produce a 0.02 total when inventory is complete.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - The supplied synthetic examples yield exact 0.00264, 0.00289 and partial subtotal 0.00224. → the stated result is observed.
  - Two 0.015 components sum to 0.03 before half-even display rounding; a partial subtotal never populates complete cost. → the stated result is observed.
  - An unsupported nonterminating rate unit remains unpriced; two 0.005 amounts total exactly 0.01 before display rounding. → the stated result is observed.
  - Derived sums above 9007199254740991 remain exact decimal strings; zero model responses plus a proven 0.02 separately billed tool produce a 0.02 total when inventory is complete. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
