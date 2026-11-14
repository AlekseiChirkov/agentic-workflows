# Plan — State tool for safe subtask-progress edits

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status | Model (Claude) | Model (Codex) |
|----|------|---------------------|------------|--------| --- | --- |
| T-01 | Progress parser and get command | suite harness → version guard and dispatch → vocabulary constants → path and encoding checks → section and block parser → get output → pinned source-guard fixtures | — | reviewed | claude-opus-5-5 |  |
| T-02 | Static validation command | invariant predicates → receipts format check → validate with block scope → 3-before-6 exit rule | T-01 | reviewed | claude-opus-5-5 |  |
| T-03 | Set write transaction | write arguments → lock and metadata → read and revision → structure and version refusals → writability and value rules → narrow serialization → receipt append → atomic replace → write output | T-01, T-02 | reviewed | claude-opus-5-5 |  |
| T-04 | Note and target-file additions | note placement → note validation → append-note and set --note → path rules and add-file | T-03 | reviewed | claude-opus-5-5 |  |
| T-05 | Lifecycle invariants on set | rank order and pinned rule → green source rule → n-a and completion rules → pre-TDD guard → changed-field scoping and warnings → all-or-nothing group | T-02, T-03, T-04 | reviewed | claude-opus-5-5 |  |
| T-06 | Block initialization | argument and children validation → canonical leaf and composite lines → insertion layout → block-exists and section-missing refusals | T-03, T-04 | reviewed | claude-opus-5-5 |  |
| T-07 | Idempotent operation receipts | malformed-receipts refusal → receipt lookup before revision → init-block repeat → 20-entry cap → digest coverage | T-02, T-03, T-04, T-06 | reviewed | claude-opus-5-5 |  |
| T-08 | Lock contention and interruption recovery | busy-lock reporting → unsafe path refusals → fault seam → recheck before rename → sync-failure warning and locking-unavailable → stale temporary files | T-03, T-04, T-07 | reviewed | claude-opus-5-5 |  |
| T-09 | Receipts grammar contract and validator checks | failing validator checks → suite registration → mutation fixtures → anchored line and reader rule → protected entry → validate-task receipts check → exact oracle extension | T-01, T-07 | reviewed | claude-opus-5-5 |  |
| T-10 | Ignore rules and usage documentation | failing ignore and doc checks → .gitignore → setup entries → usage entry list → State tool section → script inventory row → pinned digests | T-08, T-09 | reviewed | claude-opus-5-5 |  |

## Execution Strategy

Strictly sequential in ID order, one stacked branch per subtask; the listed order is a
valid topological order of `Depends On`. No subtask runs in parallel.

Shared-file constraints:
- `scripts/state-tool.py` and `tests/state-tool.py` are extended by T-01–T-08 (and the
  suite by T-09 and T-10); each subtask builds on the previous branch tip.
- Every change under `tests/` or to `scripts/validate-contracts.sh` invalidates the pinned
  source-guard inventory fingerprint, so each subtask ends by refreshing the pinned
  source-guard fixtures (`tests/fixtures/validator-runtime/README.md`). Validator edits
  and the one exact extension of the frozen validator inventory are confined to T-09
  (suite registration and contract checks); T-10 refreshes the suite's pinned digest once
  more.
- The complete validator run takes 35–50 minutes; subtasks verify with the suite run
  directly (the focused state-tool mode from T-09 on) and the guard suites, and the complete run happens at task-level
  validation on the stack tip.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | One component: the structural parser exposed through `get`; all criteria observe read results |
| T-02 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One component: static checks behind one command with one exit rule |
| T-03 | leaf | S1=12, S2=1, S3=1, S4=false, S5=1 | One component: the write transaction; lock, revision, receipt append and replace are steps of one operation and cannot be verified apart from an applied write |
| T-04 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One component: growing a field group (notes, target files) without rewriting it |
| T-05 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One component: transition rules that need the previous value |
| T-06 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One component: block creation and its layout |
| T-07 | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | One component: idempotency rules over the receipt field |
| T-08 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | One component: the failure half of the write path (contention, unsafe paths, interruption) |
| T-09 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One component: the grammar extension with its validator checks |
| T-10 | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | One component: the consumer-facing surface; the manual names the ignore patterns, so one criteria cluster |

Size decision — ten leaves against the target of eight (Autonomous Decision Protocol):

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Keep ten coherent leaves | 4 | 4 | 4 | 5 | 4 | 21 |
| Merge to eight (parser+validate, additions+initialization) | 3 | 4 | 3 | 3 | 4 | 17 |
| Split into two tasks (tool; contract and docs) | 2 | 3 | 3 | 4 | 3 | 15 |

**Winner:** keep ten leaves — each merge would put two independently testable components
in one leaf (leaf health requires S2 = 1 and S5 = 1), and a task split would separate the
grammar extension from the tool that writes the field. The target of eight is soft
guidance (`workflow-reference → ## Decomposition Rules`).

Rejected boundaries:
- Receipts inside the write-transaction leaf — rejected: lookup and cap are verifiable
  only once all four write commands exist; the transaction leaf keeps only the append.
- Lifecycle invariants before note additions — rejected: the `n-a` justification and the
  pre-TDD note arrive through `set --note`, so additions come first.
- Suite registration in the first leaf — reversed by owner decision on 2026-11-13 (was
  chosen in Discovery, citing P7): the frozen validator inventory cannot accept a new
  check without an oracle extension, and a registered suite pins its digest, so early
  registration would rewrite the oracle's pinned values in every leaf. The suite is
  registered once in T-09; T-01 and T-09 scopes changed accordingly (T-01: registration
  removed; T-09: registration and oracle extension added; T-10: suite digest refresh).
