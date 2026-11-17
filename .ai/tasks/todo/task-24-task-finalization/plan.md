# Finalization implementation

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status |
|----|------|---------------------|------------|--------|
| T-01 | Implement evidence, journal and lossless archival mechanics | tests → implement → review | — | reviewed |
| T-02 | Enforce scoped cleanup and stage provider outputs | tests → implement → review | T-01 | reviewed |
| T-03 | Connect finalization with shared workflow contracts | tests → implement → review | T-02 | in-progress |

## Decomposition Decisions

Three sequential leaves separate evidence/archive mechanics, enforced cleanup/deployment mechanics and instruction contracts. No concurrent shared-file writers.
