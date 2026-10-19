## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status |
|---|---|---|---|---|
| T-01 | Portable script path defaults | scoped failing smoke checks → relative defaults → relocated checkout checks | — | reviewed |
| T-02 | Neutral public examples | scoped failing checks → fictional examples → document semantics verification | T-01 | reviewed |
| T-03 | Public hygiene scanner and final sweep | global hygiene RED → remaining corpus cleanup and local deltas → final sweep | T-02 | reviewed |

## Execution Strategy
Strict sequential local stack from main: fix/portable-script-paths → docs/neutral-public-examples → fix/public-hygiene-guard. Each leaf uses scoped smoke criteria; the final leaf owns the full-tree guard, remaining redactions, and inclusion of the complete preserved knowledge base. Both batch questions are resolved. Local test-first commits are authorized; all pushes and PRs are withheld pending separate history remediation. No parallel execution. Shared context deltas are applied only by the Orchestrator. Model column absent: use the session default as the workflow permits.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One script path-resolution behavior; isolated relocation/override smoke criteria. |
| T-02 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One public-example corpus with scoped editorial/semantic checks. |
| T-03 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One final full-tree scanner contract with its remaining corpus cleanup. |
