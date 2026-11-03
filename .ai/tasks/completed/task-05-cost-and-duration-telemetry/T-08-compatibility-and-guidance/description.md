## Goal
Compatibility, recovery and operating guidance: deliver and independently validate the complete capability.

## Context
- Dependencies: T-03, T-04, T-06, T-07.
- Constraints: Preserve explicit scope, bounded offline inputs, independently verified provenance, exact arithmetic, immutable accepted evidence and existing nonblocking lifecycle behavior.
- Reason: The user requested fewer work items grouped around integrated capabilities; the original independently testable clusters remain explicit below.
- Previous descriptions and progress are preserved in `../superseded/`.

Off-limits: Paid model calls, implicit historical discovery, automatic model or policy changes, invented evidence, rewriting accepted events or unrelated behavior.

## Scope
- **In scope:** Verify legacy behavior and offline recovery; run end-to-end acceptance; document real operating and trust boundaries.
- **Out of scope:** Changes outside the specification and its compatibility requirements.
- **Target files:** Determine from the preserved original descriptions and integrated implementation before modifying code.

## Steps
1. Reconcile existing branches, tests and independently reviewed work with the current main-based stack.
2. Implement the integrated capability and resolve the open defects without discarding existing evidence.
3. Execute the original acceptance scenarios below and independent cross-component review.
4. Integrate reviewed changes in dependency order and update task state.

## Acceptance Criteria

### T-08
- The documented disable-and-resume procedure preserves prior evidence while legacy logging and offline validation work without optional usage dependencies.
- Injected installation or publication failure produces no false receipt, and a documented exact retry recognizes a previously installed bundle without invoking a model.

### T-08a
- Legacy logging works without optional usage dependencies and telemetry failures leave accepted lifecycle artifacts unchanged.
- Fault injection at publication and recovery boundaries produces no false receipt and an exact retry recognizes a previously installed bundle.

- The ordinary synthetic validation suite makes no network or paid model calls.

- An explicitly selected synthetic source, duplicate response and independent two-response inventory pass through normalization, publication, resolution, pricing and all three exports: tokens are 2/2 complete, pricing is 1/2, the duplicate is counted once, and a fixed-corpus rerun has identical semantic results.

- A projection built from resolved and priced evidence passes the producer check with the exact computed amount 0.00264; canonical zero is rejected without changing lifecycle evidence.

### T-08b
- Documentation explains explicit sources, supported profiles, price update, exports, disablement and safe recovery.
- The recovery guidance distinguishes an absent receipt from a confirmed rejection and describes exact-byte retry.

- The retrospective workflow explicitly freezes the selected corpus manifest and invokes the analyzer, while active workflows do not discover historical inputs.

## Test Plan

### T-08
- **Level:** integration, contract
- **Scenarios:**
  - The documented disable-and-resume procedure preserves prior evidence while legacy logging and offline validation work without optional usage dependencies. → the integrated outputs agree.
  - Injected installation or publication failure produces no false receipt, and a documented exact retry recognizes a previously installed bundle without invoking a model. → the stated recovery or incompleteness result is observed.
- **Edge cases:** missing dependencies, invalid inputs, partial evidence and repeated delivery.

### T-08a
- **Level:** unit, integration
- **Scenarios:**
  - Legacy logging works without optional usage dependencies and telemetry failures leave accepted lifecycle artifacts unchanged. → the stated result is observed.
  - Fault injection at publication and recovery boundaries produces no false receipt and an exact retry recognizes a previously installed bundle. → the stated result is observed.
  - The ordinary synthetic validation suite makes no network or paid model calls. → the stated result is observed.
  - An explicitly selected synthetic source, duplicate response and independent two-response inventory pass through normalization, publication, resolution, pricing and all three exports: tokens are 2/2 complete, pricing is 1/2, the duplicate is counted once, and a fixed-corpus rerun has identical semantic results. → the integrated boundary produces the stated result.
  - A projection built from resolved and priced evidence passes the producer check with the exact computed amount 0.00264; canonical zero is rejected without changing lifecycle evidence. → the exact result and unchanged evidence are verified.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.

### T-08b
- **Level:** unit, integration
- **Scenarios:**
  - Documentation explains explicit sources, supported profiles, price update, exports, disablement and safe recovery. → the stated result is observed.
  - The recovery guidance distinguishes an absent receipt from a confirmed rejection and describes exact-byte retry. → the stated result is observed.
  - The retrospective workflow explicitly freezes the selected corpus manifest and invokes the analyzer, while active workflows do not discover historical inputs. → the integrated boundary produces the stated result.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
