## Goal
Retrospective reports and duration analysis: deliver and independently validate the complete capability.

## Context
- Dependencies: T-04.
- Constraints: Preserve explicit scope, bounded offline inputs, independently verified provenance, exact arithmetic, immutable accepted evidence and existing nonblocking lifecycle behavior.
- Reason: The user requested fewer work items grouped around integrated capabilities; the original independently testable clusters remain explicit below.
- Previous descriptions and progress are preserved in `../superseded/`.

Off-limits: Paid model calls, implicit historical discovery, automatic model or policy changes, invented evidence, rewriting accepted events or unrelated behavior.

## Scope
- **In scope:** Freeze explicitly selected evidence; calculate comparable groups, accepted outcomes and measured durations; export consistent reports and preserve unknowns.
- **Out of scope:** Changes outside the specification and its compatibility requirements.
- **Target files:** Determine from the preserved original descriptions and integrated implementation before modifying code.

## Steps
1. Reconcile existing branches, tests and independently reviewed work with the current main-based stack.
2. Implement the integrated capability and resolve the open defects without discarding existing evidence.
3. Execute the original acceptance scenarios below and independent cross-component review.
4. Integrate reviewed changes in dependency order and update task state.

## Acceptance Criteria

### T-06
- A fixed corpus containing four complete values produces semantically equivalent JSON, CSV and Markdown with median 2.5 and p90 4.
- Independent acceptance and timing evidence remain scoped to the frozen corpus; a late correction or incompatible clocks cannot change the old report or produce an invented exclusive duration.

### T-06a
- The analyzer consumes only explicitly selected hash-verified inputs and excludes evidence first observed after as_of.
- A late correction cannot change a reproduced older corpus and input permutations preserve semantic results.

### T-06b
- JSON, CSV and Markdown exports represent the same semantic totals and preserve exact numbers in machine output.
- CSV preserves exact decimal values as text and excluded observations are identified consistently across formats.
- Machine exports encode all derived sums as canonical decimal strings, including sums within the safe JSON integer range.

### T-06c
- Failed 0.4, accepted resumed 0.6, rejected 0.3 and incomplete 0.2 produce three opportunities, one accepted and observed 1.5.
- No independent acceptance makes the ratio unavailable, and incomparable tasks or price bases produce no winner.

- Independent experimental evaluation is separate from production verification and included once in an optional combined total; a late defect label changes only a new report revision.

### T-06d
- Parent [0,10] with children [1,7] and [4,9] yields wall 10, worker sum 11, union 8 and exclusive 2.
- Missing children, incompatible clocks or invalid parentage leave exclusive time unknown without subtracting grandchildren twice.

### T-06e
- Values 1, 2, 3, 4 yield n=4, median 2.5, p90=4 and a small-sample marker.
- An empty group has unavailable statistics and partial values do not enter a complete-value distribution.

## Test Plan

### T-06
- **Level:** integration, contract
- **Scenarios:**
  - A fixed corpus containing four complete values produces semantically equivalent JSON, CSV and Markdown with median 2.5 and p90 4. → the integrated outputs agree.
  - Independent acceptance and timing evidence remain scoped to the frozen corpus; a late correction or incompatible clocks cannot change the old report or produce an invented exclusive duration. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-06a
- **Level:** unit, integration
- **Scenarios:**
  - The analyzer consumes only explicitly selected hash-verified inputs and excludes evidence first observed after as_of. → the stated result is observed.
  - A late correction cannot change a reproduced older corpus and input permutations preserve semantic results. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-06b
- **Level:** unit, integration
- **Scenarios:**
  - JSON, CSV and Markdown exports represent the same semantic totals and preserve exact numbers in machine output. → the stated result is observed.
  - CSV preserves exact decimal values as text and excluded observations are identified consistently across formats. → the stated result is observed.
  - Small and large derived sums are exported as canonical decimal strings without rounding.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-06c
- **Level:** unit, integration
- **Scenarios:**
  - Failed 0.4, accepted resumed 0.6, rejected 0.3 and incomplete 0.2 produce three opportunities, one accepted and observed 1.5. → the stated result is observed.
  - No independent acceptance makes the ratio unavailable, and incomparable tasks or price bases produce no winner. → the stated result is observed.
  - Independent experimental evaluation is separate from production verification and included once in an optional combined total; a late defect label changes only a new report revision. → the stated exact result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-06d
- **Level:** unit, integration
- **Scenarios:**
  - Parent [0,10] with children [1,7] and [4,9] yields wall 10, worker sum 11, union 8 and exclusive 2. → the stated result is observed.
  - Missing children, incompatible clocks or invalid parentage leave exclusive time unknown without subtracting grandchildren twice. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-06e
- **Level:** unit
- **Scenarios:**
  - Calculate the four-value group → n=4, median 2.5, p90=4, small-sample marker.
  - Calculate empty and mixed-completeness groups → unavailable empty statistics and separated distributions.
- **Edge cases:** empty groups, ties, even and odd sample sizes, input permutations and exact decimal values.
