spec_path: .ai/specs/06-1-test-suite-runtime.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: not-started
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Naming: retain `.ai/specs/06-1-test-suite-runtime.md` and its derived task basename;
  the owner explicitly directed continuation under 06 after the prefix collision was
  explained. This is a task-specific exception, not a change to the global guard.
- Delivery base: freeze an isolated current integrated checkout when execution starts;
  do not reset this dirty checkout or silently use the older spec inspection commit
  (source: spec A-02 and current source/status inspection).
- Scope: W1-W5 only; keep direct/isolated run-log duplication and vocabulary mutation
  scheduling unchanged (source: spec A-03 and Out of Scope).
- Jobs: default to min(4, positive usable CPUs), fallback 1; permit measured exclusive
  groups without weakening existing timing assertions (source: REQ-10 and A-04).
- Timing: prefer opt-in Linux `/proc/uptime` sampling with centisecond quantization;
  verify a pre-expansion DEBUG hook against pinned Bash semantics before adopting it
  (source: REQ-19 and implementation hints). No timing sampling when disabled.
- Performance: fresh B, S and P medians bind; old 360/240-second totals are stretch
  goals only, and the two individual optimized checks each retain the 10-second
  budget (source: Non-Functional Requirements and A-06).
- Coverage: preserve successful-input scanner behavior in characterization; isolate
  fail-closed read/normalization/aggregation corrections in a separate RED cycle.
  Record W1's intentional fixture amendment before changing its frozen tests
  (source: REQ-03/07/24, AC-17 and rules/tdd.md).
- flow: full — gate: 1 fail (>3 files including fixtures/docs), 2 fail (ownership,
  configuration and timing invariants), 3 fail (shipped validator control flow changes),
  4 pass (no product schema/migration).

- Parallel execution: the owner requested concurrent subagent scheduling on 2026-11-05.
  The task-local plan overrides sequential-only workflow ordering for isolated candidates;
  the orchestrator remains the sole shared-state writer and serializes shared integration.
  Full suites, deadline tests and measurements require a quiet host. Scope, frozen tests,
  canonical status formats and all acceptance gates remain unchanged.

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-07a, T-07b, T-07c, T-08, T-08a, T-08b
- composites: T-07 (T-07a, T-07b, T-07c); T-08 (T-08a, T-08b)

## Subtask Progress

T-01 | Freeze the implementation equivalence oracle | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: tests/validator-runtime-characterization.py, tests/fixtures/validator-runtime/, .ai/memory/progress.md
  blocker: none
  notes: planned TDD mode: characterize: pin existing behavior; baseline measurement is evidence, not a new wall-time assertion.

T-02 | Implement the bounded nested-run source guard | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-guard.py, tests/fixtures/validator-runtime/
  blocker: none
  notes: planned TDD mode: RED.

T-03 | Replace complete warning-fixture runs with the guarded prefix | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-warning.py, .ai/memory/progress.md
  blocker: none
  notes: planned TDD mode: RED.

T-04 | Optimize successful identity scans against the frozen corpus | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-identity.py, tests/fixtures/validator-runtime/
  blocker: none
  notes: planned TDD mode: characterize: behavior-preserving optimization only; new I/O expectations belong to T-05.

T-05 | Reject incomplete identity-scan I/O | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-identity.py
  blocker: none
  notes: planned TDD mode: RED.

T-06 | Add opt-in timing around complete result evaluation | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-timing.py
  blocker: none
  notes: planned TDD mode: RED.

[composite] T-07 | Run acceptance groups with bounded owned concurrency | rollup: not-started | integration-validation: not-started
  children: T-07a, T-07b, T-07c
  blocker: none
  notes: Type 2; S2=S5=3; Lifecycle ownership, admission policy and Bash reporting integration are three independently testable components with three criteria clusters.

T-07a | Contain and reap complete worker process trees | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-processes.py
  blocker: none
  notes: planned TDD mode: RED.

T-07b | Validate jobs and schedule productive bounded slots | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-scheduler.py
  blocker: none
  notes: planned TDD mode: RED.

T-07c | Integrate original expressions and ordered output | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: scripts/validate-contracts.sh, tests/validator-runtime-integration.py, tests/fixtures/validator-runtime/
  blocker: none
  notes: planned TDD mode: RED.

[composite] T-08 | Complete performance acceptance and operating guidance | rollup: not-started | integration-validation: not-started
  children: T-08a, T-08b
  blocker: none
  notes: Type 2; S2=S5=2; Controlled performance acceptance and delivered operating documentation have separate verifiable outcomes; the parent checks their agreement.

T-08a | Measure the complete optimized validator against the baseline | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: .ai/memory/progress.md, .ai/tasks/todo/task-06-1-test-suite-runtime/state.md
  blocker: none
  notes: planned TDD mode: characterize: compare the frozen full-run contract; external performance acceptance is measured evidence, not synthetic RED or a new in-suite threshold.

T-08b | Document the verified validator behavior and decisions | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: Discovery defined scope, acceptance and test scenarios; implementation has not started.
  target_files: .ai/context/runbook.md, docs/USAGE.md, .ai/adr/0018-task-06-1-bounded-validator-runtime.md, .ai/adr/index.md, .ai/memory/architecture.md, .ai/memory/progress.md
  blocker: none
  notes: planned TDD mode: RED.


## Solution Design

### Variants

→ archived to state-archive.md

### Decision

Choose A: preserve original Bash expression/diagnostic semantics and literal checks;
use an inline standard-library Linux ownership supervisor only in the acceptance region
and an opt-in pre-expansion uptime clock adapter for full-run checks. The supervisor is
validator infrastructure, not a workflow/agent runtime, and does not supersede ADR-0001.

The timing adapter is conditional on observed pre-expansion and Bash-semantics tests.
If those tests disprove its safety, keep the tests frozen, rescore A/B using that evidence
and adopt B if it wins; do not weaken coverage or silently ship a hook that fails its
characterization. This is an implementation verification obligation, not an assumed
completed experiment.

adr: .ai/adr/0018-task-06-1-bounded-validator-runtime.md — Provisional; promote in place during pv-finalize after implementation and validation.

### Autonomous Decision

| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---------|------------|---------------|--------------|-------------|--------------|-------|
| A: contained inline supervisor and opt-in pre-expansion hook | 4 | 4 | 5 | 5 | 5 | 23 |
| B: same supervisor and explicit per-site clock instrumentation | 2 | 4 | 3 | 5 | 3 | 17 |

**Winner:** A (23/25) — it preserves current check call sites and extracted consumers
while addressing the actual evaluation and escaped-descendant requirements.
**Anti-overengineering check:** passed. The supervisor solves the current setsid
fixture and bounded cleanup requirement; the clock adapter solves measurement before
argument evaluation. Neither is a general task engine, shell parser, plugin or new test
framework. Unknown runtime safety remains subject to explicit RED/characterization.
**Evidence:** project architecture P1/P3/P4/P7/P8/P9; coding literal check convention;
ADR-0001 validation boundary, ADR-0010 exact hygiene and ADR-0012 complete knowledge
tracking; validator check/warning/scanner/group/hygiene interfaces and unchanged
run-log/PYCORRELATED consumers documented in Task Analysis. Type 2 composites and
separate scanner correction follow rules/tdd.md and the leaf-health classifier.

### Scope

#### In
- W1: unique real-prefix cut, minimal isolated git history, all three warning/exit
  assertions, construction mutations and the explicit incidental-coverage amendment.
- W2: per-file NUL normalization, one matching pass, exact case-sensitive row counts
  and safe path transport; separately tested fail-closed new I/O behavior.
- W3: exactly 36 original expression/body mappings, validated jobs/default/cap,
  productive admission, measured exclusivity, explicit records, bounded descendant
  cleanup and a full join before actual hygiene and all suffix snapshots.
- W4: bounded reference classification, exact checked exceptions and all mutation cases.
- W5: opt-in monotonic expression timing, no timing-only work when off, one indented
  line after each complete outer result and preserved focused/extracted interfaces.
- Additive runtime/guard verification through the ordinary full test command; no new
  public focused CLI. Publish exact added check names once in the frozen inventory delta.
- Stable baseline and optimized evidence, docs, indexed provisional ADR and project memory.

#### Out
Product helper/suite assertion changes, CI/hook/installer changes, framework migration,
module splitting of existing groups, W6/W7 deduplication/mutation parallelism, cached
verdicts, relaxed timeouts, deployment, real-settings/log writes and history rewriting.

### Rejected

→ archived to state-archive.md

### Off-limits
- Preserve unrelated dirty knowledge, installer and git-rails work. Create no branch,
  commit, PR, deployment or installed-copy update during Discovery.
- Do not edit original suite bodies, their internal order, assertions, timeouts or
  product helpers/hooks/installer/CI. All new runtime fixtures are additive.
- Preserve the three exact run-log extraction marker pairs, all their two-line check
  calls, the literal tables function line and PYCORRELATED block; extracted fixtures
  cannot acquire a dependency on supervisor/clock definitions outside their copy.
- Do not edit the spec, broaden the TSV ledger syntax, change locale or redefine the
  baseline knowledge inventory. The owner naming exception is limited to this task.
- No new public focused flags, duplicate-coverage removal, wall-budget assertions in
  ordinary tests, real store/settings writes, historical log changes or hidden skips.

### Invariants
- INV-1: every original outer check remains exactly once in original result position;
  only explicitly named additive checks extend the inventory. Preserve all assertions
  except W1's stated incidental full-copy coverage removal.
- INV-2: successful scanner rows and ordinary jobs=1 output match characterization;
  only REQ-24's explicit behavior exceptions are permitted. New paths need observed RED.
- INV-3: completed failed checks exit 1; clean complete runs exit 0 with existing summary.
  Configuration/infrastructure/interruption exits are abnormal and cannot report success.
- INV-4: no worker tree overlaps prefix or suffix source snapshots; full join precedes
  actual tracked hygiene, including the installer group below its misleading comment.
- INV-5: fixtures retain private HOME/XDG/log isolation and never touch real stores;
  the documented maintainer-local hygiene pattern/skip behavior stays unchanged.
- INV-6: all owned descendants and runner records are reaped/removed on normal, failing
  and handled INT/TERM paths. Handle setsid escape; protect caller and unrelated PIDs.
  No SIGKILL/power-loss universal fixture cleanup guarantee is introduced.
- INV-7: all extraction markers, literal function line, PYCORRELATED annotations/size
  constraints and self-contained extracted helpers remain intact.
- Ordinary off-mode bytes and focused dispatch/forwarding/exec/exit behavior are stable;
  new environment validation and timing are full-run-only.

### Acceptance Criteria
Each criterion is binary; performance criteria require external evidence, not in-suite
wall-time assertions. Characterization uses the pre-change implementation; new behavior
uses observed RED then GREEN under `rules/tdd.md`.

- [ ] **AC-01 (REQ-01–04,24).** Given the optimized real-prefix history fixture, the
  three required states pass and mutations making the warning always present, always
  absent, or blind to work-tree VERSION updates each fail the fixture. No outer copied
  check executes; a scratch sentinel after the cut remains unexecuted. Missing/duplicate
  anchors and a check before the anchor fail construction.
- [ ] **AC-02 (REQ-01–04).** The measured optimized history fixture is <=10 s, contains
  only the necessary source/history material, and runs no complete validator. Preserve
  warning/exit assertion strength and record the construction amendment explicitly.
- [ ] **AC-03 (REQ-06–09,24).** A frozen scanner differential corpus produces identical
  sorted rows and verdicts before/after. Include extra occurrence, reduced ledger count,
  wrong ledger line, final line without newline, repeated tokens, mixed case with both
  correct and merged-case ledgers, colons, spaces/backslashes in paths, NUL-split tokens,
  invalid bytes, empty/no-match files, symlink target text, ledger masking/line offsets,
  missing paths and baseline-detected grep/output errors. New error handling is tested
  separately in AC-17. Cover C and one available
  UTF-8 locale, logging an unavailable locale rather than claiming that case passed.
- [ ] **AC-04 (REQ-06–09).** The complete optimized identity/knowledge check is <=10 s
  in the controlled environment, with no per-line subprocess creation.
- [ ] **AC-05 (REQ-10–15,22–24).** Clean full runs at jobs=1 and default have the same
  complete ordered outer results, counts, warning/summary and status as the frozen
  inventory plus declared new checks. All 36 full-run expression mappings match;
  unrelated post-hygiene checks remain present in order. Compare stable bytes separately
  on stdout and stderr; normalize only fixture paths known to vary, never verdicts,
  diagnostics, counts or relative order within a channel.
- [ ] **AC-06 (REQ-10–14,23).** Deterministic synthetic workers prove ordered reporting
  despite out-of-order completion, multiple failure propagation, later execution after
  failures, and INT/TERM cleanup. Test direct children and grandchildren, including a
  stubborn descendant requiring escalation, plus a child that escapes with `setsid`
  before interruption (matching the existing git-rails fixture). Use handshake/PID
  recording to establish that the escaped child is alive before INT/TERM. Owned PIDs
  and output directory disappear within REQ-12's budget; no pipe remains held open,
  and an unrelated sentinel survives. Invalid jobs values `''`, `0`, `-1`, `+1`, `01`,
  `x`, and whitespace fail before any full-run check; valid huge decimal clamps safely.
- [ ] **AC-07 (REQ-16–17).** The new source guard is observed RED against pre-W1 source
  and GREEN afterwards. Scratch mutations add a direct full call, remove/alter a focused
  flag, split a Python argv across lines, invoke a copied untrimmed validator or `$validator`,
  add unrelated trimming text, and change/delete/duplicate an allowed exception; all
  fail. Classified comments, source-copy data and approved stubs pass. Inventory every
  current reference so unknown candidate forms are review failures, not silent skips.
- [ ] **AC-08 (REQ-18–19).** Timing unset, empty, `0`, and another non-1 value give the
  same ordinary output as the rewritten jobs=1 run with timing off. At `1`, each outer
  result block (PASS/FAIL/SKIP) has exactly one timing line. A controlled monotonic clock
  proves argument evaluation is included, real-time jumps are irrelevant and worker
  queue/report delay is excluded. Document real-clock quantization; timing is nonnegative.
- [ ] **AC-09 (REQ-10,19,20,22).** The reproducible baseline and optimized run records
  meet the proportional S/P budgets and individual-check budgets above, retain all
  samples, and report the old 360/240 s stretch goals separately. Missing a binding
  target leaves this criterion incomplete with hotspot evidence.
- [ ] **AC-10 (REQ-22–24).** If baseline has counts `(pass, fail, skip)` and the named
  new checks total N, clean optimized counts are `(pass+N, 0, skip)` with baseline
  failures zero. Compare check-name inventory, not counts alone. Keep hygiene configuration
  identical; account for its two optional skips explicitly.
- [ ] **AC-11 (REQ-13,15,21,24).** Existing run-log harness and meta-test pass unchanged,
  PYCORRELATED inspection passes, all 37 focused entrypoints retain their source dispatch
  and pass applicable invocation/argument fixtures, and a disposable sync failure test
  proves no deployment writes after validator failure. No actual deployment is run.
- [ ] **AC-12 (REQ-20–21).** Runbook, usage text and indexed ADR describe the delivered
  behavior and actual evidence. Product changes contain no internal planning identifiers.
- [ ] **AC-13 (REQ-10–14,22).** Synthetic barriers/counters demonstrate peak active groups
  never exceeds jobs, is greater than one for jobs>1 with independent workers, refills
  free slots, and remains exactly one with jobs=1. Exercise 0/1/partial-batch inputs;
  do not infer concurrency solely from an elapsed-time threshold.
- [ ] **AC-14 (REQ-11–12,23).** Faulted groups preserve their own existing generic-only,
  20-, 35-, and 60-line failure conventions and separate channels at jobs=1 and jobs>1.
  Include multiline diagnostics, output containing fake PASS text, launch failure,
  partial/missing metadata and unwritable output. Parent cannot convert them to success
  or double-count records; all owned resources are cleaned.
- [ ] **AC-15 (REQ-12–13,22).** A source/resource inventory and synthetic snapshot sentinel
  establish that no worker starts before the preceding snapshot finishes and none is
  alive when tracked hygiene or any later snapshot starts. Existing source hashes are
  unchanged except for allowed bytecode caches; conflicts are serialized explicitly.
- [ ] **AC-16 (REQ-15,18–19).** Focused invocations with invalid jobs and enabled timings
  behave as before; timing-off full runs do not start a timing-only helper. Characterized
  checks retain Bash conditional/errexit/subshell semantics and the extracted harness
  remains executable without scheduler/timing definitions absent from its copy.

- [ ] **AC-17 (REQ-07,24).** Separate observed RED tests inject a read error that the
  original loop treats as EOF, then prove the rewritten scanner rejects it. Inject
  failed normalization/aggregation and partial-output-then-failure independently;
  every case fails closed, even if the partial rows would match the ledger. Freeze
  these new expectations separately from AC-03 and record the intentional behavior
  correction rather than calling it before/after equivalence.

### Implementation Interfaces

1. **Full-run initialization.** Existing 37 focused dispatch blocks stay ahead of new
   configuration/timing/supervisor setup. Validate jobs text before any full result or
   launch; clamp arbitrarily long positive decimals without overflow. CPU detection is
   positive nproc, then positive getconf, else 1; default cap 4. Keep the optional
   history warning before the first ordinary check.
2. **Worker registry and Bash adapter.** Associate each original group ordinal with
   its exact description/expression function, original diagnostic wrapper, required
   definitions/context and resource class. Write private Bash prologues/scripts under
   the one owned temporary directory; pass required values without reparsing shell
   strings. Preserve working directory, applicable environment/descriptors and Bash
   conditional/errexit context, verified against the oracle. Never source/reexecute the
   full validator, and never substitute a focused CLI. Literal check calls stay intact.
3. **Private protocol.** A worker's check renderer preserves complete stdout/stderr
   behavior and publishes the exact description/result plus execution status once.
   Results, channel files and optional start/end timing are keyed by ordinal and
   validated before use; publish complete records atomically. Separate a valid FAIL
   verdict from worker infrastructure failure. PID/ownership metadata stays private.
   Parent counters consume validated records, never printed PASS/FAIL-looking output.
4. **Containment.** An inline standard-library supervisor establishes Linux subreaper
   containment before launches and maintains per-worker ownership boundaries so a
   shell exiting or a descendant using setsid cannot lose ownership. Track process
   identity across reparenting/PID reuse and drain adopted descendants; never signal
   process groups containing caller/unrelated processes. Verify mechanism availability
   before launching; failure is a nonzero runner error. Bash signal forwarding and
   Python teardown cooperate: stop admission, forward INT/TERM, grace <=2 s, KILL
   remaining owned processes, reap and remove records within another <=2 s in synthetic
   controlled tests. Preserve 130/143. Abrupt supervisor errors must also clean owned
   resources; no reliance on killed fixture cleanup or leaked captured pipes.
5. **Admission and output.** Count complete owned group lifetimes against jobs,
   refill a free slot independently of report order, drain before exclusive work and
   flush only the contiguous completed source-order prefix. Preserve byte order within
   each channel, not an invented cross-channel total order. Join all trees before
   hygiene/suffix. Infrastructure errors fail closed; ordinary FAILs do not suppress
   independent later groups. Account for every result once.
6. **Timing.** Enable only for exact ORCHESTRAIL_TEST_TIMINGS=1. Read /proc/uptime with
   Bash built-ins before argument expansion and at completion; document 10 ms source
   quantization and verify nonnegative integer conversion. A gated pre-expansion hook
   must not recurse or inherit into extracted fixtures/substitutions in a way that
   changes semantics. Test controlled monotonic jumps/delays via disposable fixture
   seams, not a new public timing override. Start worker timing at actual execution,
   excluding queue and ordered-output waits. After the entire result block append one
   indented time_ms line. Off means no timing-only samples/helper. Supervisor shutdown
   clocks remain independent of this optional feature.
7. **Scanner.** Retain input discovery/masking/knowledge logic; normalize NULs per
   file, run at most one grep -aEion -- matching invocation, preserve grep 1 versus
   >=2 and aggregate literal bytes with safe path transport (not awk -v escape
   conversion). Check every new read/normalization/aggregation/write status. Freeze
   new fault expectations separately from unchanged successful-input rows.
8. **Source guard.** Inventory new worker/fixture references before registration.
   Match exact container/statement or fingerprint/count/reason exceptions, including
   the three history calls bound to their actual guarded prefix construction.
   Treat supported focused flags on the actual argv as safe; unknown forms fail for
   review. The guard is bounded source regression detection, not a general parser.
9. **Verification registration.** Add callable tests/results for new guard/runtime
   behavior once through the existing full-run route, outside extracted sections.
   Synthetic fixtures extract only required functions/blocks; they cannot recursively
   run the full validator. Maintain a named additive N and stable result positions.
   Existing check call conventions need no planned exception; if implementation needs
   one, record and reconcile that change explicitly before adopting it.
10. **Evidence.** Freeze all original results/36 expressions/37 focused routes and a
    resource manifest before rewriting. Default timing-sensitive/unknown-conflict
    groups to exclusive until inventory and observed concurrency justify overlap.
    Keep bytecode/cache policy equal on all measured modes without overriding cold-cache
    fixture environments. Store live measurement output outside the measured source;
    copy evidence into memory only after each frozen measurement window. Record source
    payload/config and every B/S/P sample. More than 10% spread triggers a third sample;
    S<=B*360/1171.4, P<=B*240/1171.4, warning<=10 s, identity<=10 s bind. Old 360/240 s
    absolute totals are stretch goals. A miss remains incomplete, with hotspots.

### Design Reconciliation
- Eight top-level units, 11 leaves and 2 composites remain unchanged; all statuses
  are not-started. Worker lifecycle/admission/reporting share one inline supervisor
  rather than introducing external product modules.
- T-07c uses original named expression functions and explicit metadata replay. T-06
  carries the pre-expansion proof gate; failed proof requires recorded A/B rescoring.
- T-08b must repeat any full correctness/performance comparison affected by its new
  documentation verification checks before closing, retaining all earlier samples.
- No model recommendation exists or became stale. No requirement is deferred beyond
  the spec's already out-of-scope W6/W7. No timing or performance proof was run here.

## Discovery Verification
- Task artifacts: repository-local `bash scripts/validate-task.sh .ai/tasks/todo/task-06-1-test-suite-runtime --phase discovery` passed 13 checks, failed 0, skipped 3 (execution/validation checks not applicable).
- Supplemental structural audit passed: 13 descriptions, 11 healthy leaves, 2 depth-2 composites; unique IDs; acyclic ordered dependencies; exact description/plan/progress target inventories; one observable scenario per criterion; all 17 spec acceptance criteria retained verbatim.
- `compress-state --auto`: file is current; no stale or duplicate unprotected content needs removal. Use the prescribed Discovery archive for verbose analysis and rejected variants instead of weakening protected sections.
- Optional configured logging/helper routing: ORCHESTRAIL_HOME is unset, so no run log or configured helper was used. The already inspected repository-local artifact validator was executed explicitly as supplemental verification. No native precision is claimed.
- Source verification: validator blob remains `9470de8f9bcefcbf89210410c24d371fa741d5ac`; no implementation, test-suite body, spec, installed copy, settings or real log content was changed.
- Persistent updates: task registry and architecture receive a planned/in-flight entry. Project principles are unchanged because the design adds no new durable rule; .ai/project_state.md is absent and is skipped.
- Execution and validation remain not-started. Performance B/S/P, timing-hook proof, containment proof and runtime acceptance are pending execution; no benchmark improvement is claimed.

## Parallel Execution Amendment
- authorization: Owner requested analysis and plan annotations for parallel subagent execution on 2026-11-05; no implementation was requested by this amendment.
- policy: plan.md -> ## Parallel Execution; task-specific override of sequential-only ordering, private candidates, at most three workers, serial shared integration and orchestrator-only shared-state/git writes.
- independent-lanes: guard (T-02 -> T-03), identity (T-04 -> T-05), timing (T-06), lifecycle (T-07a -> T-07b), all released only after T-01 is reviewed.
- joins: T-07c after all feature/lifecycle prerequisites; composite T-07 before T-08a; T-08a before final T-08b and composite T-08.
- preparation-only: T-01 read-only inventory reports before baseline; T-08b draft guidance after T-01; independent immutable-candidate review when resource locks permit. Preparation never satisfies a task completion dependency.
- resources: benchmark/full-suite/deadline-test host locks require other workers acknowledged idle and process drain. Shared validator writes, corpus additions, state/plan/memory/ADR changes and git mutations remain serial.
- preserved: Discovery complete; execution/validation and every leaf/composite status remain not-started; scope and all 17 acceptance criteria are unchanged. The archived original analysis remains historical and is not rewritten.
- verification: Repository task validation passed 13 checks with 0 failures and 3 phase-inapplicable skips. Supplemental checks passed for the revised acyclic DAG, all 13 descriptions, four independent post-baseline lanes, full join coverage, per-row ownership/resource guidance, unchanged statuses and all 17 retained spec acceptance criteria; artifact whitespace is clean.
