# ADR-0018: Decisions for Task 06-1 — Bounded contract validator runtime

## Status

Provisional

## Date

2026-11-05

## Related Task

- Task: [Contract validator runtime](../tasks/todo/task-06-1-test-suite-runtime/state.md)
- Related pull request: not created
- Related files: `scripts/validate-contracts.sh`, additive `tests/validator-runtime*`
  fixtures, `.ai/context/runbook.md`, relevant `docs/USAGE.md` validator text and
  implementation evidence in project memory.

## Summary

Plan a bounded optimization of the existing Bash contract validator: trim the real
warning prefix, match identity tokens once per file, contain and schedule the original
acceptance expressions, and add optional monotonic expression timing. Preserve all
existing checks, diagnostics, focused dispatch and extracted run-log consumers except
the explicitly permitted fixture and scanner error-handling changes. No runtime change
or measured improvement is implemented by this record.

## Context

The current warning fixture copies the whole checkout and executes a nearly complete
validator three times (`scripts/validate-contracts.sh:4526-4591`). Its identity scanner
forks a matching pipeline per source line (`:4786-4804`). The 36 full-run acceptance
expressions have different diagnostic wrappers and precede actual tracked hygiene
(`:4842-5202`). `check` receives an already evaluated result (`:583-597`), so timing its
body cannot measure the check's work.

Worker process groups alone cannot retain all descendants: the existing core creates
new sessions (`hooks/git_rails.py:1630-1634`) and its acceptance fixtures deliberately
launch `setsid sleep 6` (`tests/git-rails.sh:5084-5096`). Run-log extraction preserves
exact section markers and two-line calls (`tests/log-step.sh:30-48`); the existing
PYCORRELATED block has separate inspection constraints (`tests/hook-timing.sh:646-674`).

Discovery inspected HEAD `4d2a9fd1f76eff06ff3aa3a760d683e01c886bac` and validator blob
`9470de8f9bcefcbf89210410c24d371fa741d5ac`. The checkout has unrelated changes and is
not a controlled performance baseline. Execution must freeze a stable integrated
payload, source/resource inventories and fresh complete baseline measurements.

## Decisions

### Decision 1: Guard the real warning prefix instead of running a copied full suite

**What was decided:**
Retain the actual validator through its unique standalone warning call, append
`exit 0`, reject missing/duplicate anchors and any earlier top-level check, and copy
only this script, VERSION and required rule material before the fixture's first commit.
Keep the three history-state warning and exit assertions with isolated git settings.

**Why:**
The fixture's observable purpose is the warning's version/history behavior. Complete
copied-validator execution repeats unrelated acceptance work and amplifies suite growth.

**Alternatives:**
A new warning-only public flag adds forbidden CLI surface. Keeping a complete copied
run retains the dominant unnecessary cost. String stubs do not verify the real warning.

**Consequences:**
The incidental assertion that a complete validator succeeds in the copied checkout is
intentionally removed. Record the exact TDD construction amendment, retain warning
mutations and cut sentinels, and still require real complete implementation acceptance.
Bind the recursion guard's three-call exception to this exact checked construction.

**Related files:**
- `scripts/validate-contracts.sh`
- Additive warning/source-guard verification fixtures.

### Decision 2: Use inline Linux containment for the original acceptance expressions

**What was decided:**
Keep the Bash validator and all 36 original expression/body/diagnostic mappings. Use
an inline standard-library supervisor with Linux subreaper containment and per-worker
ownership boundaries; retain ownership across shell exit, reparenting and new sessions.
Provide private Bash worker prologues containing required definitions/context without
sourcing or reexecuting a full validator. Capture separate channels and explicit
result/status records under one temporary directory, publish complete records and
replay only the contiguous source-order prefix. Parent counters consume validated
records, never PASS-looking test output.

**Why:**
The spec requires both original expression semantics and complete descendant cleanup.
A contained supervisor addresses the actual escaped-session fixture while avoiding a
new framework or external product module.

**Alternatives:**
Group-only signals cannot cover setsid descendants. Focused flags change publication
and model-workflow coverage. A framework migration or external runner module expands
the specified implementation surface.

**Consequences:**
Linux containment must be verified before real workers launch. INT/TERM stops admission,
forwards only to owned processes, grants at most 2 seconds of grace, then kills/reaps
remaining owned processes and removes records within a further 2 seconds in controlled
tests. Preserve exits 130/143 and protect unrelated processes. Infrastructure failure
is abnormal, not a successful zero-FAIL run. Normal and failing groups also drain all
owned descendants before releasing their slot or records. SIGKILL/power-loss cleanup
of all fixture resources is not promised. This is validation infrastructure, not an
agent/workflow runtime; ADR-0001 remains unchanged.

**Related files:**
- `scripts/validate-contracts.sh`
- Additive process-lifecycle and runner-integration verification fixtures.

### Decision 3: Bound admission, measure exclusivity and preserve snapshot barriers

**What was decided:**
Validate full-run jobs as a positive canonical decimal, safely clamp valid values over
36, and default to min(4, positive usable CPU count), falling back to 1. Refill free
slots independently of reporting, count complete worker lifetimes, and isolate groups
whose resources/timing bounds require exclusivity. Finish prefix snapshots before
launches and join every tree before actual tracked hygiene and all later snapshots.

**Why:**
The old partial parallel probe does not establish full-suite resource safety. Current
git-rails timing assertions and source-relative imports require explicit contention
classification and performance evidence under the actual default.

**Alternatives:**
Unbounded workers, a default of eight, batch waits, source snapshots overlapping workers,
or weakening existing timing assertions do not meet the requested runtime contract.

**Consequences:**
Jobs=1 preserves source order. Focused modes bypass all new validation and keep their
existing arguments/exec/exit behavior. Unknown conflict classifications remain exclusive
until evidence supports overlap. Preserve fixed coverage and measured budgets even if
exclusivity limits speedup; a missed target leaves acceptance incomplete.

**Related files:**
- `scripts/validate-contracts.sh`
- Resource inventory and scheduling/barrier verification fixtures.

### Decision 4: Gate monotonic sampling before evaluation and retain literal checks

**What was decided:**
Prefer a full-run-only opt-in DEBUG timing hook that samples Linux `/proc/uptime` with
Bash built-ins before result argument expansion and completes sampling in the renderer.
Document its centisecond (10 ms) quantization and append exactly one indented timing
line after each entire outer result block. Timing off performs no timing-only sampling
or helper startup. Supervisor shutdown clocks are independent.

**Why:**
The selected approach scores 23/25 against 17/25 for repeated explicit per-site sampling:
it avoids widespread edits to literal check calls and extraction-sensitive sections.
Its subtle Bash behavior is a concrete test obligation, not a presumed success.

**Alternatives:**
Gated explicit built-in samples before every check are the in-scope fallback if the
hook fails frozen pre-expansion/conditional/subshell tests; rescore and record the
evidence before switching. Wall clocks, inter-output deltas and one Python startup per
check are unacceptable. Timing only the `check` body misses evaluated work.

**Consequences:**
Preserve two-line harness-parsed calls, exact extraction markers/literal function and
PYCORRELATED. No exception to the literal check-call coding convention is currently
planned; scheduling dispatch does not replace the original check expressions. Any
necessary implementation exception must be explicitly recorded and reconciled before
adoption. Verify queue/report waits are excluded and clock failures fail abnormally.

**Related files:**
- `scripts/validate-contracts.sh`
- Additive timing and unchanged consumer-compatibility fixtures.

### Decision 5: Separate byte equivalence, new error handling and performance evidence

**What was decided:**
Freeze successful scanner rows and existing detected errors before replacing its hot
loop with one per-file matching pass after NUL normalization. Preserve literal path
transport, case-sensitive count keys, locale, ledger validation and knowledge inventory.
Use a separate RED cycle for read-as-EOF correction and new normalization/aggregation
failures. Measure fresh baseline/sequential/default complete runs under the spec's
source/config/cache/variance protocol.

**Why:**
An optimization must not silently change byte/path semantics or call a behavior
correction universal equivalence. Historical counts and timings describe older content.

**Alternatives:**
Raw file grep misses NUL-split matches, awk `-v path` changes backslash bytes, partial
output can conceal failures, and historical-only measurements cannot establish delivery.

**Consequences:**
Keep all samples. Binding medians are S<=B*360/1171.4 and P<=B*240/1171.4; the complete
warning and identity checks each remain <=10 seconds. The old 360/240-second total
goals are stretch goals. Keep budgets out of ordinary-suite wall assertions; any miss
remains incomplete with hotspot evidence. W6/W7 remain outside this scope.

**Related files:**
- `scripts/validate-contracts.sh`
- Additive identity differential/fault fixtures and implementation measurement record.

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| Should the runtime spec be renamed to a later unused prefix after the collision guard? | The owner rejected renaming to 21 and directed continuation under 06. | Retain the existing `06-1` spec/task paths as a task-specific naming exception; do not change the global guard or the git-rails task. |

## Rejected Options

Group-only termination, focused-flag substitution, a framework migration, broad source
guard exemptions, changed suite assertions/timeouts, reduced coverage, historical-only
performance acceptance and W6/W7 expansion. Explicit per-site timing remains a tested,
rescored fallback rather than a rejected requirement.

## Implications for Future Work

Execute the recorded test-first plan on a stable isolated integrated payload. Retain
the frozen result/reference/resource inventories and all new-behavior RED evidence.
Do not promote this ADR until implementation and validation demonstrate its decisions.
Update this same record with delivered details and any explicitly reconciled convention
exception; final validation promotes it in place rather than allocating a duplicate.
Acceptance cannot complete while a binding performance target is missing or failed.

## Verification

Not yet verified — decision recorded before implementation completed.

Discovery inspected the cited source interfaces and created a contract/coverage plan.
No full baseline, optimized benchmark, containment prototype or timing-hook proof has
run in this Discovery invocation. Future evidence must identify the actual tested tree.

## References

- Task: [State](../tasks/todo/task-06-1-test-suite-runtime/state.md) and
  [plan](../tasks/todo/task-06-1-test-suite-runtime/plan.md).
- Pull request: not created.
- Related documents: [Specification](../specs/06-1-test-suite-runtime.md),
  [ADR-0001](0001-task-unknown-markdown-only-no-runtime.md),
  [ADR-0010](0010-task-unknown-public-hygiene-and-local-publication.md),
  [ADR-0012](0012-task-unknown-knowledge-tracking-policy.md).


## Execution Planning Amendment — 2026-11-05

The owner explicitly requested parallel subagent scheduling for this task. The
[plan](../tasks/todo/task-06-1-test-suite-runtime/plan.md) now separates four independent
post-baseline implementation lanes: guard/warning, identity equivalence/error correction,
timing, and lifecycle/admission. Final runner integration and evidence gates remain joins.
This is a task-specific exception to sequential-only execution ordering, not a global
workflow change or a replacement for accepted cross-project orchestration decisions.

Private worker candidates prevent concurrent writes to the same validator. A single
integration writer reconciles patches; the orchestrator alone updates canonical progress,
plan, memory and ADR/git state. Benchmark, full-suite and deadline-sensitive checks require
all other workers to acknowledge idle and drain processes. Test-first, independent
validation, frozen coverage and all original acceptance requirements remain unchanged.
The runtime architecture/status remains Provisional; this amendment starts no execution.
