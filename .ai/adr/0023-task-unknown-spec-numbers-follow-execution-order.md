# ADR-0023: Specification numbers follow the execution order

## Status

Accepted

## Date

2026-11-16

## Related Task

- Task: owner decision of 2026-11-16, taken when Discovery of the context-tiering
  specification stopped on its undelivered prerequisites.
- Related files: `.ai/specs/README.md`, every file under `.ai/specs/`,
  `.ai/tasks/completed/task-01-git-source-of-truth/state.md`, `.ai/memory/state.md`.

## Summary

The sixteen open specifications are renumbered 08–23 so that the number in a file name is
its position in the execution order. Every reference in the knowledge base and under
`docs/` is rewritten, historical records included. The knowledge inventory baseline of
the identity ledger moves to the commit that renames the files.

## Context

File numbers recorded the order in which specifications were written, not the order in
which they must be delivered. The roadmap table listed the real order in a separate
column: 13a, 13, 09, 08, 14, 15, 17, 16, 18, 19, 20, 10, 11a, 11, 12a, 12. Starting
Discovery on the file numbered 08 therefore selected a specification whose two
prerequisites, numbered 13 and 09, were not delivered. The numbers 00–07 and 06-1 belong
to delivered work and were already in order.

Two facts constrained the change:

- The specifications cite each other by number about four thousand times (`13 REQ-68`,
  `spec 09`, prerequisite lists, tables keyed by specification).
- The contract validator's identity-ledger check requires every `.ai` path of a recorded
  baseline commit to exist at its path or under `.ai/specs/completed/`. Seven of the
  sixteen files existed at that baseline, which is why the split of 2026-11-16 kept the
  original paths.

## Decisions

### Decision 1 — Contiguous numbers 08–23 in execution order

**What was decided:** The open specifications take the numbers 08–23 in the order of the
roadmap table. Letter suffixes disappear. Completed specifications keep their numbers.
The old-to-new table is `.ai/specs/README.md → ## Renumbering — 2026-11-16`.

**Why:** The owner wants the next specification to deliver to be the lowest open number.

**Alternatives:** A fresh range 21–36, which would never give one number two meanings
(recommended by the implementer, rejected by the owner in favour of contiguous numbers);
keeping the numbers and relying on the order column (rejected: it caused the stop above).

**Consequences:** Every number from 08 to 20 changed meaning on 2026-11-16. Commit
messages, pull request titles and branch names created earlier use the old numbers and
are read through the table.

### Decision 2 — Historical records are rewritten

**What was decided:** Decision records, the progress log, the state registry, completed
specifications, completed task records and documents under `docs/` use the new numbers.
Requirement, acceptance, data-model and assumption identifiers are unchanged.
Identifiers that embedded a specification number were renamed with it (listed under the
table).

**Why:** Owner decision: one numbering everywhere in the tree, so that no record needs a
date to be interpreted.

**Alternatives:** Leave history as written and add only the table (recommended by the
implementer, rejected by the owner).

**Consequences:** Historical statements that named a numeric range now name the
equivalent set, for example "specs 14–20" became "specs 12–18" and "specs 01–13" became
"specs 01–07, 09–11, 19, 21 and 23". ADR-0009 Decision 7 and ADR-0017 read in the new
numbers.

### Decision 3 — The knowledge inventory baseline moves to the renaming commit

**What was decided:** The identity-ledger check reads the last `base_commit:` line of the
ledger file. A dedicated baseline line is appended to that file and names the commit that
renamed the specifications. The recorded base commit of every subtask block stays as it
was. The validator source is unchanged.

**Why:** The check protects knowledge files from deletion. After the renaming every file
still exists under its new name, so a baseline taken after the renaming protects the same
content. The owner chose this over redirect stubs under `.ai/specs/completed/` and over
amending the frozen validator inventory.

**Alternatives:** Seven redirect stubs at the old paths (rejected: they look like
delivered specifications and reuse the numbers 08–13); a rename map in the validator
(rejected: an inventory amendment larger than the change it serves).

**Consequences:** The renaming commit alone fails the full validator; the commit that
follows it restores the check. The branch must reach `main` through a merge commit,
because a squash would make the baseline commit unreachable, as was already true of the
earlier baseline.

## Verification

- Before and after the rewrite, every reference of the forms `spec N`, `N REQ-k`,
  `N's` and `N-<slug>.md` was resolved to a specification file by slug; 3,091 references
  resolve to the same file, apart from the ranges reworded under Decision 2.
- Every `N <id>` reference names an identifier that exists in specification N, before
  and after.
- The complete `bash scripts/validate-contracts.sh` result is recorded in the progress
  log.
