## Subtasks

| ID   | Name                           | Key Steps (summary)                                      | Depends On | Status      |
|------|--------------------------------|----------------------------------------------------------|------------|-------------|
| T-01 | Producer validation and writes | define contract → validate → normalize → persist safely | —          | reviewed |
| T-02 | Read-only run linter           | select files → validate records → report JSON           | T-01       | reviewed |
| T-03 | Lint-aware retrospective       | filter corpus → exclude invalid lines → report coverage | T-02       | reviewed |
| T-04 | Vocabulary docs and drift gate | document tables → compare runtime contract → fail drift  | T-02       | reviewed |
| T-05 | Isolated acceptance harness    | fixture store → exercise branches → verify immutability | T-01, T-02, T-03, T-04 | reviewed |
| T-06 | Redact unknown command errors | freeze disclosure → redact diagnostic → verify | T-05 | reviewed |
| T-07 | Bound path argument parsing | freeze missing-operand hang → validate path args → verify | T-06 | reviewed |
| T-08 | Repair input boundaries | preserve documented flag text → check workflow search permission → verify | T-07 | reviewed |

## Execution Strategy

Implement T-01 before T-02 because both change the same helper and the linter must reuse the producer's runtime definitions. T-03 and T-04 depend on the linter contract and can be completed in either order; keep them sequential in the task stack. Complete T-05 last so the acceptance harness covers the integrated producer, linter, retrospective contract, and drift gate. All work stays in this repository.

## Decomposition Decisions

### Boundary Decision

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---:|---:|---:|---:|---:|---:|
| One integrated subtask | 5 | 3 | 2 | 2 | 1 | 13 |
| Five capability leaves | 4 | 5 | 5 | 5 | 4 | 23 |
| Split by event command and documentation operation | 2 | 3 | 3 | 4 | 2 | 14 |

**Winner:** Five capability leaves. The producer, linter, retrospective consumer, documentation gate, and acceptance harness have distinct observable outcomes. Splitting by event command or document operation would fragment shared contract work. The shared helper edits are ordered by dependency.

**Anti-overengineering check:** passed. The boundaries follow existing files and independently verifiable capabilities; no new runtime layer or speculative abstraction is introduced.

### Autonomous Subtask Classification

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | One producer contract spanning the three event paths; shared validation and persistence invariants make it one component. |
| T-02 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | One read-only linter interface and its single diagnostic/summary contract. |
| T-03 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One retrospective reporting capability consuming the linter output. |
| T-04 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One cross-check between the runtime contract and its documented canonical tables. |
| T-05 | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | One isolated acceptance harness spanning the completed capabilities. |
