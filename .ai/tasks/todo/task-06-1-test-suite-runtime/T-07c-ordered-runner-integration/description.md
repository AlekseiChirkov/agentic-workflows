## Goal
Integrate original expressions and ordered output with the observable outcomes below.

## Context
- Dependencies: T-01, T-02, T-03, T-04, T-05, T-06, T-07a, T-07b
- Constraints: Preserve INV-1 through INV-7 and the frozen oracle. Keep all existing suite bodies, assertions, timeouts, focused dispatch and extracted run-log contracts. Use isolated fixtures; no real HOME/XDG/log stores or installed-copy writes. All new Python is standard-library-only; preserve applicable annotation/size contracts.
- Reason: One Bash adapter maps the frozen acceptance expressions onto the scheduler without changing their externally observed result stream.
- TDD mode: RED

- Parallel execution: lane `serial integration`; use `plan.md -> ## Parallel Execution` for release conditions, private-candidate ownership and host locks. Return all shared-state/knowledge changes as deltas to the orchestrator; do not write canonical progress blocks.

Off-limits: Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.

## Scope
- **In scope:** Integrate exactly 36 original full-run expressions, original wrappers and explicit record-based parent accounting, with snapshot/consumer boundaries.
- **Out of scope:** Product helpers, hooks, installer, CI, public focused flags, W6/W7, coverage reductions, historical log changes, deployment and history rewriting.
- **Target files:** `scripts/validate-contracts.sh`, `tests/validator-runtime-integration.py`, `tests/fixtures/validator-runtime/`

## Steps
1. Add RED synthetic reporting/counter/channel/barrier fixtures around the existing 36-expression map; preserve ordinary failure wrappers and command-substitution context.
2. Encapsulate the original check expressions in named worker functions and provide their exact required Bash definitions/context to private worker scripts. Do not call public focused flags or source a full validator to execute a group.
3. Capture child stdout/stderr and exact result/status on owned records. Replay only a contiguous completed source-order prefix within each channel; update parent PASS/FAIL/SKIP from validated metadata, never printed PASS-looking text.
4. Continue independent later groups after check failures and keep slots productive. Missing records/launch faults remain abnormal; completed failed checks produce exit 1 and unchanged ordinary summary.
5. Launch only after prefix snapshots; join every group tree before the actual tracked-hygiene result, preserving all suffix checks and output positions. Record original-to-new expression/body/diagnostic equivalence.
6. Wire worker timing without queue/report delay, register runtime verification checks additively and classify all new source references in the bounded guard.
7. Run unchanged isolated run-log/meta-test and PYCORRELATED consumers, all applicable focused dispatch/argument fixtures, fake PASS/multiline/excerpt faults and a disposable sync failure sentinel.

## Acceptance Criteria
- C1 (AC-05/10/14): all 36 original expression mappings and generic/20/35/60-line failure conventions match at jobs=1 and jobs>1; complete blocks and separate channel order are preserved, counters derive from one valid owned record per result and later independent work executes after failures.
- C2 (AC-11/15/16): all workers start after prefix snapshots and none survives into actual hygiene/suffix snapshots; 37 focused interfaces, extraction markers/literal function/PYCORRELATED remain compatible and a disposable failed validation causes zero deployment writes.
- C3 (AC-05/08; REQ-23): timing excludes queue/report waits, ordinary timing-off bytes remain stable, completed failures exit 1, and infrastructure/interruption cannot emit a successful completion summary.

## Test Plan
- **Level:** integration, contract
- **Scenarios:**
  - C1: delay the first worker and fail later workers; compare stdout/stderr separately against frozen wrappers, including fake PASS text and 20/35/60-line truncation, exact result order/count and execution sentinels.
  - C2: snapshot handshakes and live PID checks prove barriers; rerun unchanged consumer extraction and focused fixtures under invalid new variables, then execute sync only in a disposable source/HOME with a failure sentinel.
  - C3: controlled clocks hold queue/report release independently of execution, compare timing-off bytes, and exercise completed-check failure versus infrastructure/signal exits.
- **Edge cases:** channel ordering, multiline diagnostics, stdout spoofing, wrapper excerpts, snapshot order, extracted helper independence.
- Test fixtures are additive; original acceptance-suite bodies remain unchanged. New runtime checks must be registered once in the ordinary test command without recursively running the complete validator. Performance thresholds live only in the external measurement record.
