## Goal
Usage resolution, ownership and exact pricing: deliver and independently validate the complete capability.

## Context
- Dependencies: T-03.
- Constraints: Preserve explicit scope, bounded offline inputs, independently verified provenance, exact arithmetic, immutable accepted evidence and existing nonblocking lifecycle behavior.
- Reason: The user requested fewer work items grouped around integrated capabilities; the original independently testable clusters remain explicit below.
- Previous descriptions and progress are preserved in `../superseded/`.

Off-limits: Paid model calls, implicit historical discovery, automatic model or policy changes, invented evidence, rewriting accepted events or unrelated behavior.

## Scope
- **In scope:** Resolve identity, streams and cumulative epochs; prove completeness and causal ownership; select applicable prices and compute exact totals; integrate producer evidence with analysis.
- **Out of scope:** Changes outside the specification and its compatibility requirements.
- **Target files:** Determine from the preserved original descriptions and integrated implementation before modifying code.

## Steps
1. Reconcile existing branches, tests and independently reviewed work with the current main-based stack.
2. Implement the integrated capability and resolve the open defects without discarding existing evidence.
3. Execute the original acceptance scenarios below and independent cross-component review.
4. Integrate reviewed changes in dependency order and update task state.

## Acceptance Criteria

### T-04
- Duplicate and revised observations resolve once against the independent inventory and assign a proven shared pool to its parent.
- An unresolved identity prevents an unjustified complete scope total; proven late evidence changes only a new report, which can become complete when all completeness conditions hold.

### T-04a
- The same response across branched sessions counts once, while two distinct responses from one call count twice.
- Ambiguous identity is retained as unresolved and is excluded from overlapping additive totals.

### T-04b
- Partial outputs 1 and 40 followed by final 100 resolve to 100 in every input order.
- A sequence with increments 1 and 3 but missing 2 remains partial even after a terminal event; incompatible finals conflict.

- Duplicate increments are counted once; correction cycles and incompatible final successors remain conflicted unless a valid correction chain proves the replacement.

- A proven correction successor replaces its final predecessor, while a stream without a final snapshot remains partial at its last ordered evidenced value.

### T-04c
- Two adjacent snapshots with one fully enclosed request produce its exact evidenced delta.
- A mid-request snapshot, unknown epoch, reset or gap does not invent full request usage or double-count an overlapping aggregate.

### T-04d
- Two independently inventoried final requests with one unknown price report token completeness 2/2 and priced coverage 1/2.
- Unknown inventory has an unknown denominator; proven empty billable scope alone permits exact zero.

### T-04e
- A measurement is not treated as independently evidenced unless its explicitly supplied sanitized evidence matches the reference, source, scope and measured value; absent or unauthorized evidence remains unverified without discovering history.
- A shared 0.1 expense with two candidate leaves is counted once in the proven parent pool and is not split into 0.05 shares.
- A late observation changes only a newly produced report and an external unattributed pool is not included in a complete parent total.

- A 0.1 shared pool included once in a complete proven parent remains unattributed to both leaves, so neither leaf is declared complete.

### T-05
- Applicable price snapshots and exact arithmetic price the complete synthetic request at 0.00264.
- The specified unknown-cache-TTL fixture retains its priced 0.00224 subtotal without complete cost; a conflicting applicable rate leaves its affected component unpriced.

### T-05a
- Historical prices require proven effective intervals and exact model, service, region, modality and unit applicability.
- Conflicting intervals, unresolved aliases and missing historical prices remain unpriced; explicit reprice remains conditional.
- An absent multiplier declaration means unknown applicability and cannot establish a reliable price without evidence. An absent tool identifier means unknown identity and cannot be matched by guessing.

- A threshold using strict greater-than leaves an input of 1000 at the base rate and applies the multiplier at 1001; cache TTL and separately billed tools require matching rates.

### T-05b
- The supplied synthetic examples yield exact 0.00264, 0.00289 and partial subtotal 0.00224.
- Two 0.015 components sum to 0.03 before half-even display rounding; a partial subtotal never populates complete cost.

- An unsupported nonterminating rate unit remains unpriced; two 0.005 amounts total exactly 0.01 before display rounding.

- Derived sums above 9007199254740991 remain exact decimal strings; zero model responses plus a proven 0.02 separately billed tool produce a 0.02 total when inventory is complete.

## Test Plan

### T-04
- **Level:** integration, contract
- **Scenarios:**
  - Duplicate and revised observations resolve once against the independent inventory and assign a proven shared pool to its parent. → the integrated outputs agree.
  - An unresolved identity prevents an unjustified complete scope total; proven late evidence changes only a new report, which can become complete when all completeness conditions hold. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-04a
- **Level:** unit, integration
- **Scenarios:**
  - The same response across branched sessions counts once, while two distinct responses from one call count twice. → the stated result is observed.
  - Ambiguous identity is retained as unresolved and is excluded from overlapping additive totals. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-04b
- **Level:** unit, integration
- **Scenarios:**
  - Partial outputs 1 and 40 followed by final 100 resolve to 100 in every input order. → the stated result is observed.
  - A sequence with increments 1 and 3 but missing 2 remains partial even after a terminal event; incompatible finals conflict. → the stated result is observed.
  - Duplicate increments are counted once; correction cycles and incompatible final successors remain conflicted unless a valid correction chain proves the replacement. → the stated result is observed.
  - A proven correction successor replaces its final predecessor, while a stream without a final snapshot remains partial at its last ordered evidenced value. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-04c
- **Level:** unit, integration
- **Scenarios:**
  - Two adjacent snapshots with one fully enclosed request produce its exact evidenced delta. → the stated result is observed.
  - A mid-request snapshot, unknown epoch, reset or gap does not invent full request usage or double-count an overlapping aggregate. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-04d
- **Level:** unit, integration
- **Scenarios:**
  - Two independently inventoried final requests with one unknown price report token completeness 2/2 and priced coverage 1/2. → the stated result is observed.
  - Unknown inventory has an unknown denominator; proven empty billable scope alone permits exact zero. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-04e
- **Level:** unit, integration
- **Scenarios:**
  - Resolve matching, mismatched, absent and unauthorized evidence → only a proven matching association is verified.
  - A shared 0.1 expense with two candidate leaves is counted once in the proven parent pool and is not split into 0.05 shares. → the stated result is observed.
  - A late observation changes only a newly produced report and an external unattributed pool is not included in a complete parent total. → the stated result is observed.
  - A 0.1 shared pool included once in a complete proven parent remains unattributed to both leaves, so neither leaf is declared complete. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-05
- **Level:** integration, contract
- **Scenarios:**
  - Applicable price snapshots and exact arithmetic price the complete synthetic request at 0.00264. → the integrated outputs agree.
  - The specified unknown-cache-TTL fixture retains its priced 0.00224 subtotal without complete cost; a conflicting applicable rate leaves its affected component unpriced. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-05a
- **Level:** unit, integration
- **Scenarios:**
  - Historical prices require proven effective intervals and exact model, service, region, modality and unit applicability. → the stated result is observed.
  - Conflicting intervals, unresolved aliases and missing historical prices remain unpriced; explicit reprice remains conditional. → the stated result is observed.
  - Missing multiplier declarations and tool identifiers remain unpriced unless separate evidence establishes applicability and identity; no unique-looking rate is selected by inference.
  - A threshold using strict greater-than leaves an input of 1000 at the base rate and applies the multiplier at 1001; cache TTL and separately billed tools require matching rates. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-05b
- **Level:** unit, integration
- **Scenarios:**
  - The supplied synthetic examples yield exact 0.00264, 0.00289 and partial subtotal 0.00224. → the stated result is observed.
  - Two 0.015 components sum to 0.03 before half-even display rounding; a partial subtotal never populates complete cost. → the stated result is observed.
  - An unsupported nonterminating rate unit remains unpriced; two 0.005 amounts total exactly 0.01 before display rounding. → the stated result is observed.
  - Derived sums above 9007199254740991 remain exact decimal strings; zero model responses plus a proven 0.02 separately billed tool produce a 0.02 total when inventory is complete. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
