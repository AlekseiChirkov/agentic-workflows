## Subtasks

| ID   | Name                           | Model              | Key Steps (summary)                                               | Depends On | Status      |
|------|--------------------------------|--------------------|-------------------------------------------------------------------|------------|-------------|
| T-01 | Versioned contract metadata    | gpt-6.1-sol        | add VERSION → stamp task state and run logs → warn on stale rules | —          | reviewed |
| T-02 | Portable runtime paths         | gpt-6.1-sol        | rename root overrides → update setup helpers → verify relocation  | T-01       | reviewed |
| T-03 | Public package materials       | gemini-3.8-flash   | add concise README → narrow ignores → update setup guide; defer license and release tag | T-02    | reviewed |
| T-04 | Public identity sweep          | gemini-3.8-flash   | update remaining references → enforce scoped scan → verify hygiene | T-03     | reviewed |

## Execution Strategy

Run the four leaves sequentially as one stack, preserving the scrubbed predecessor branch as the base. Version metadata comes first because later task and run records rely on it. Runtime paths follow, then user-facing package files with the license and release tag deferred, then the scoped identity sweep after all planned names and paths are established. No subtask runs in parallel. The checkout-directory move is an Orchestrator-owned local operation after task validation and PR promotion; it does not change repository contents.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One version-awareness contract shared by task state, run logs, and the validator. |
| T-02 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One runtime configuration behavior across the checkout's scripts and helper instructions. |
| T-03 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One public package surface with a concise README, ignore policy, setup guide, and recorded license deferral. |
| T-04 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One repository identity invariant checked across the remaining mutable content. |
