## Goal
Provide offline telemetry operating guidance with observable, deterministic behavior.

## Context
- Dependencies: T-08a — sequential execution order for the shared telemetry contract.
- Constraints: Follow the specification sections Requirements and acceptance; AC-08; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** offline telemetry operating guidance, including all applicable requirements and negative cases in Requirements and acceptance; AC-08.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** docs/USAGE.md, tests/usage-telemetry-guidance.py, scripts/validate-contracts.sh, tests/log-step.sh, rules/run-log.md, workflows/retro.md.

## Steps
1. Document explicit selected sources, supported profiles, pricing scenarios and offline export.
2. Describe enablement, disablement, preserved gaps and owner-controlled alert delivery.
3. Describe recovery, receipt uncertainty and exact-byte retry without rewriting prior evidence.

## Acceptance Criteria
- Documentation explains explicit sources, supported profiles, price update, exports, disablement and safe recovery.
- The recovery guidance distinguishes an absent receipt from a confirmed rejection and describes exact-byte retry.

- The retrospective workflow explicitly freezes the selected corpus manifest and invokes the analyzer, while active workflows do not discover historical inputs.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Documentation explains explicit sources, supported profiles, price update, exports, disablement and safe recovery. → the stated result is observed.
  - The recovery guidance distinguishes an absent receipt from a confirmed rejection and describes exact-byte retry. → the stated result is observed.
  - The retrospective workflow explicitly freezes the selected corpus manifest and invokes the analyzer, while active workflows do not discover historical inputs. → the integrated boundary produces the stated result.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
