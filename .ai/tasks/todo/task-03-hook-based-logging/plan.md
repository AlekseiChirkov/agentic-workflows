# Hook-based logging implementation plan

## Subtasks

| ID | Name | Model | Key Steps (summary) | Depends On | Status |
|---|---|---|---|---|---|
| T-01 | Validated correlated event writes |  | freeze regressions → implement component → verify | — | reviewed |
| T-02 | Explicit hook dispatch and completion |  | freeze regressions → implement component → verify | T-01 | reviewed |
| T-03 | Owned user hook installation |  | freeze regressions → implement component → verify | T-02 | not-started |
| T-04 | Coverage-aware workflow logging | | freeze regressions → implement component → verify | T-03 | not-started |
| T-05 | Honest timing and end-to-end evidence | | freeze regressions → implement component → verify | T-04 | not-started |

## Execution Strategy
Strictly sequential stacked branches, after the separately authorized knowledge tracking policy correction. Each leaf reaches reviewed before its successor starts. Implementer pauses at RED for a test-only commit; a separate Validator reads each diff. No parallel implementation.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One coherent validated correlated event writes component |
| T-02 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One coherent explicit hook dispatch and completion component |
| T-03 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One coherent owned user hook installation component |
| T-04 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One coherent coverage-aware workflow logging component |
| T-05 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One coherent honest timing and end-to-end evidence component |

## Model Selection Evidence
The read-only selection pass refreshed primary provider sources on 2026-10-22. Available verified model ids include gpt-6-astra and gpt-6.1-sol. Correlation/writes and user hook installation have a Frontier quality floor, selecting gpt-6-astra. The remaining two model cells are intentionally blank: equivalent-task RCU and reliable numerical capability/benchmark comparisons were unavailable, so no ECE comparison was invented; use the session default fallback.

| Subtask | C | A | V | R | Ver | Crit | RW | Qmin |
|---|---|---|---|---|---|---|---|---|
| T-01 | 4 | 2 | 3 | 5 | 3 | 4 | 4 | Frontier |
| T-02 | 4 | 3 | 4 | 5 | 3 | 4 | 4 | Frontier |
| T-03 | 3 | 2 | 3 | 4 | 3 | 4 | 3 | Frontier: settings integrity |
| T-04 | 3 | 2 | 4 | 3 | 3 | 3 | 3 | Standard; session fallback |
| T-05 | 4 | 2 | 4 | 4 | 3 | 3 | 3 | Standard; session fallback |

## Resume Model Availability
The selected Frontier model stopped during the first implementation turn because its usage allowance was exhausted. On 2026-10-22 the owner requested continuation. Keep all existing work and frozen tests; resume through fresh context with the session default, leaving model cells blank rather than repeatedly dispatching to the unavailable model. Independent validation remains mandatory.
