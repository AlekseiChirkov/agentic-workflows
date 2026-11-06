# 06-1. Contract validator runtime

## Source

- Original owner request, 2026-11-03: optimize the excessively slow test suite.
- Refinement request, 2026-11-05 (translated from Russian): study this specification
  and the current tests, correct errors and contradictions, and repeat independent
  validation after every revision until the specification scores at least 9.5/10.
- This document specifies future implementation. The review changes no test or runtime
  implementation and does not authorize deployment, publication or history rewriting.

## Context & Problem

### Document control and evidence boundaries

| Field | Value |
|---|---|
| Status | Revised for development; implementation and performance acceptance remain outstanding. |
| Revision | 2026-11-05, revision 4; supersedes the first revision's unresolved alternatives and historical-only acceptance assumptions. |
| Inspected source | HEAD `672cd514ade50e0207b839ba424222701771a5fa`; validator blob `d64c4a413e7be1114df51bdbc67ffd0b6ad75709`, 5,796 lines. References below use this blob; relocate by symbol before editing. |
| Historical timing source | `.ai/memory/progress.md:9`, measured commit `a6cdaf1e450dde18bcdc6855c01bc091e86b6f81`, validator blob `0bb1a01e7be903a1d45bd3696f509235ded4f1be`, 5,390 lines. |
| Current runtime evidence | Owner reports runs of 50 minutes or longer; `.ai/context/runbook.md:28` records approximately 34–52 minutes and memory-pressure failures. These are reports, not a fresh controlled baseline. |
| Dependencies | No dependency on token optimization. Implementation must use the current integrated test content, including git-rails, rather than reverting to the historical measured tree. |
| Normative language | Requirements, acceptance criteria and invariants bind implementation. Historical measurements, estimates, probes and explicitly labelled hints are evidence, not guarantees. |

### How the current tests execute

The runbook's `test:` command is `bash scripts/validate-contracts.sh`
(`.ai/context/runbook.md:9`). `scripts/sync.sh:40–45` runs the same command and aborts
before deployment if it fails. The validator is a Bash program using `set -e`, not a
pytest or unittest discovery runner (`scripts/validate-contracts.sh:1–10`).

1. It defines shared usage-suite functions and dispatches **37 focused flags** before
   the full-run path (`scripts/validate-contracts.sh:12–553`). Some flags use `exec`,
   others loops or chained commands; forwarded arguments and failure behavior differ.
2. A no-argument invocation changes to the physical repository root and emits the
   optional git-history warning before the first check (`:554–577`).
3. `check(description, result)` interprets the already evaluated string: exact `pass`
   increments PASS, `skip:*` increments SKIP, anything else increments FAIL and prints
   its diagnostic (`:583–597`). Work usually executes in `$(...)` **before** `check`
   starts. Instrumenting only the function body does not measure the test.
4. Contract groups mix grep/awk assertions, real shell and Python fixtures, isolated
   git repositories, mutation checks and executable harness tests (`:600–4840`).
   The run-log checks execute directly and again through the isolated harness;
   preserving this duplicate coverage is intentional in this scope (`:2378–4474`).
5. **36 acceptance result records** follow: 35 `test_*_acceptance` checks and
   `test_workflow_instruction_contracts` (`:4842–5198`). These are result groups,
   not 36 files or 36 individual Python test cases. The inspected `tests/` contains
   135 Python files and 7 shell files, including reusable fixture modules.
6. The tracked-tree hygiene check follows those suites (`:5200–5214`), then **80
   additional static check call sites** follow (`:5216–5781`). Loops mean static
   call-site counts are not runtime result counts. The summary and completed-run
   failure status are produced at `:5783–5796`.

The shell acceptance scripts embed Python unittest programs. Git-rails builds real
fixture repositories per case, checks byte/mode/mtime preservation, executes table
cases in process and through the hook, and includes deliberately slow subprocess and
wall-budget scenarios (`tests/git-rails.sh:67–83,121–206,4518–4524,5050–5096`).
Hook installation and timing copy source folders into private fixtures and isolate
HOME/XDG/log roots (`tests/hook-install.sh:45–71`, `tests/hook-timing.sh:43–65`).
Usage suites exercise schemas, normalization, provenance, lifecycle, pricing,
reporting and warnings with synthetic evidence and fixture modules; imports can write
bytecode next to source (`tests/usage-fixed-corpus.py:12–22`,
`tests/usage-status-fixtures.py:7–15`). AST inspection parsed all 142 test files (including embedded Python where applicable);
no direct mutation expression rooted at SOURCE/ROOT was found. This is a bounded static
observation, not proof of dynamic isolation. A unique temporary fixture does not by
itself prove there are no shared source writes or timing-sensitive interactions.

### Existing costs and why they grow

| Work | Verified implementation | Historical measured cost |
|---|---|---|
| Contract-version history fixture | `test_contract_version_rule_history_warns_until_version_changes`, `:4526–4593`, copies the whole tree, strips six check groups and executes the remaining validator **three times** just to inspect one warning. | 709.9 s, 60.6% |
| Identity/knowledge check | `test_public_identity_matches_exact_ledger_and_preserves_knowledge`, `:4660–4840`, discovers the ledger, scans tracked and non-ignored untracked paths plus ledger paths, masks ledger rows, scans symlink target text, then verifies tracked knowledge preservation. Its inner Bash loop forks grep for every line (`:4786–4804`). | 138.4 s, 11.8%; 315 s in a separate loaded run |
| Run-log checks | Direct checks and the complete isolated harness, `:2378–4474`; vocabulary mutations repeatedly invoke the focused contract gate (`:2393–2430`). | About 58 s directly and 59 s through the meta-test |
| Acceptance groups | Original full-run expressions at `:4842–5198`; wrappers retain distinct failure behavior. | About 202 s across 36 groups |
| Other work | Fast definition checks, plus groups subsequently added after the old tail. | About 6 s in the historical tree; not a current measurement |

Historical full run: **1,171.4 s wall**, 877.8 s user, 339.0 s system, approximately
186 MB peak RSS, 653 passed / 0 failed / 2 skipped. Recorded environment: 8 CPUs,
Linux 7.0.0, Python 3.14.4, GNU Bash/grep, `en_US.UTF-8`. User + system time is close
to wall time, consistent with mostly sequential execution. A historical 13-group
focused-mode probe at 8 jobs took 86.2 s; this is neither a full-tail equivalence test
nor evidence that the current default should use 8 workers.

The inspected git-rails suite grew by 4,159 lines and hook-install by 834 lines since
that measured commit. A slower suite included in the copied validator is paid for
**four times** in a full run: three warning fixtures and once normally. This causal
explanation is an inference from the invocation graph, not a current per-check timing.
Recent task records report 716/0/2 and a substantially expanded git-rails case count
(`.ai/tasks/todo/task-06-harness-git-rails/state.md:572,753`); neither historical count
is a fixed acceptance oracle for the implementation checkout.

### Review probes, not implementation acceptance

- A scratch copy containing the real current prefix through the warning call,
  `VERSION`, and a rule file produced no warning / warning / no warning for the
  three required git states; each exited 0 without a result line. Individual
  invocations took about 0.01–0.02 s. This demonstrates feasibility; it is not a
  before/after execution of the expensive original fixture.
- On the same small byte fixture, the old line loop detected an identity split by
  a NUL byte; raw file-level grep missed it. Removing NUL bytes before grep restored
  the exact matches, case and line numbers. The optimized scanner must preserve this.
- The old W2 prototype's 3.3 s ledger match supports the optimization direction but
  does not establish equivalence for binary data, filenames or I/O failures.
- Fresh focused execution on 2026-11-05 passed **2,346 git-rails tests**: 287.877 s
  reported by unittest, **288.15 s wall**, 194.31 s user, 84.53 s system, 65,920 KiB
  peak RSS, exit 0. Command: `PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -v bash
  scripts/validate-contracts.sh --git-rails-only`. Environment: 8 usable CPUs, Linux
  7.0.0-42-generic, Python 3.14.4, Bash 5.3.9, grep 3.12; LANG=en_US.UTF-8,
  LC_CTYPE=C.UTF-8; approximately 15 GiB RAM, no other validator. CPU/memory cgroup
  limits were not exposed at the inspected standard paths. This single sample is
  not a current full baseline B. One existing group already exceeds the old 240 s
  whole-run stretch goal; it must be measured again under the selected scheduler.
- The baseline loop can mistake a failed Bash `read` for EOF (`:4787–4804`); an
  independently executed read-error probe confirmed successful loop termination.
  Fail-closed handling of that fault is explicitly new behavior below.

## Goal

Reduce full-validator runtime by removing three unnecessary complete fixture runs,
replacing per-line process creation in the identity scan, and scheduling the existing
acceptance groups with bounded concurrency, while preserving their required checks,
assertions, diagnostics, isolation and deployment gate. Demonstrate the improvement
against a fresh baseline on the implementation checkout, with an unchanged sequential
fallback and no wall-time pass/fail assertions in the ordinary suite.

## Scope

| ID | Work |
|---|---|
| W1 | Replace the warning fixture's complete copied-validator executions with a guarded real-prefix fixture. |
| W2 | Scan each file with one matching pass, preserving Bash's existing byte normalization and the exact identity ledger. |
| W3 | Schedule the 36 existing full-run acceptance expressions concurrently, retain source-order reporting, and join before hygiene. |
| W4 | Add a bounded source guard against accidental nested full runs, with explicit checked exceptions. |
| W5 | Add opt-in monotonic per-check timing that includes result-expression evaluation. |
| W6 | Deferred: deduplicate the direct and isolated run-log executions. |
| W7 | Deferred: parallelize the run-log vocabulary mutation cases. |

Implementation files: `scripts/validate-contracts.sh`, additive runtime-runner/guard
verification fixtures under `tests/`, the runbook, relevant validator usage text in
`docs/USAGE.md`, an indexed decision record, and implementation evidence in project
memory. Existing acceptance suite bodies and product helpers remain unchanged.

## Out of Scope

- Porting the validator, introducing a test framework, splitting its existing groups
  into modules, or changing product scripts, hooks or CI configuration.
- Removing duplicate run-log execution, reducing mutation/table coverage, changing
  internal test order, skipping checks, caching verdicts, or weakening timeouts/assertions.
- Adding new focused public CLI flags; performance work on individual acceptance suites.
- Updating deployment, user settings, historical logs or installed copies.
- Implementing the optimizations during this specification review.

## Actors & Roles

Maintainers run the full suite or focused modes. `sync.sh` consumes its exit status.
Implementation authors preserve the frozen characterization set and add RED coverage
for new behavior. Independent validators inspect both source and observed evidence;
only the primary writer updates shared specification and memory files.

## Terminology

- **Check:** one outer validator result record counted by `check`; captured fixture
  output can contain other text that resembles result lines.
- **Acceptance group:** one of the 36 existing full-run expressions at `:4842–5198`,
  including all of its current sequencing, redirection, failure text and truncation.
- **Full run:** no focused flag, from warning through the final summary.
- **Baseline B:** median wall seconds of controlled unchanged full runs on the source
  checkout being optimized, under the measurement protocol below.
- **Snapshot check:** a check that reads/enumerates source-tree contents; identity,
  warning-fixture construction and tracked hygiene are known examples.
- **Seeded violation:** minimal corruption of a disposable fixture, never the real tree.
- **Worker:** an owned acceptance-group process tree; the job limit counts groups,
  not every nested Python, shell or test-internal concurrent process.

## Requirements

### W1 — warning fixture

- **REQ-01.** THE warning fixture SHALL invoke no `check` in its copied validator.
- **REQ-02.** WHEN evaluating real git history, THE fixture SHALL retain all three
  assertions: no warning at the version commit, the exact existing warning after a
  later committed `rules/` change, and no warning after an unstaged `VERSION` update;
  each invocation must exit 0.
- **REQ-03.** WHEN constructing the fixture, THE fixture SHALL retain the real validator
  prefix through the unique standalone `warn_stale_contract_version` call, append
  `exit 0`, and reject a missing/duplicate anchor or any top-level check before it.
  The trim precedes the fixture's initial commit. The obsolete six-group stripping
  and `removed == 31` assertion are replaced with this construction guard.
- **REQ-04.** THE fixture SHALL copy only the trimmed validator, `VERSION` and the rule
  material needed for the history scenario, into its private git repository. It must
  not archive the whole working tree or depend on real HOME/XDG/git hooks/config;
  use isolated git identity/config and prevent inherited signing/hooks from interfering.
- **REQ-05.** Withdrawn: the first revision's alternative warning-only public flag.
  REQ-03 is the selected implementation; no extra CLI surface is introduced.

The narrowly accepted behavior change is removal of the incidental assertion that a
complete validator succeeds in a history-less copied checkout. All three warning
assertions and their exit-status assertions remain. This exception is explicit; W1
is not labelled universal behavior equivalence. Record the fixture-construction
amendment and reason under the repository's TDD rules. A full run in the real
checkout remains mandatory implementation acceptance.

### W2 — identity scan

- **REQ-06.** THE identity scanner SHALL replace its per-line matching subprocesses
  with at most one `grep -aEion -- "$identity_pattern"` matching invocation per scanned
  file, aggregating exact `(path, line, matched token, count)` rows as before.
- **REQ-07.** THE optimized scan SHALL produce identical sorted rows and verdicts to
  the original loop on successfully read inputs, including these existing semantics:
  - Preserve file discovery, NUL-delimited filename transport, ledger masking without
    shifting lines, symlink **target text** via `readlink`, and knowledge preservation.
  - Remove embedded NUL bytes as Bash `read` currently does, before token matching;
    retain line breaks, CR bytes, case, repeated matches and an unterminated final line.
  - Preserve literal path bytes supported by the existing TSV ledger, including
    spaces, colons and backslashes. Do not use an awk `-v path=...` conversion that
    interprets backslash escapes. Do not broaden the ledger's path syntax here.
  - Split grep's line prefix only at its first colon. Counts are case-sensitive
    keys even though matching is case-insensitive. Preserve the inherited locale
    and the existing `LC_ALL=C` final sorts; no new LANG/LC_ALL override.
  - Treat grep 1 as no match and retain grep >=2 failure. Normalization, read,
    aggregation and write failures must also fail closed, never become empty success.
    Read errors that the old Bash loop mistakes for EOF, and failures of newly
    introduced normalization/aggregation steps, are explicit new error-handling
    behavior requiring RED tests, separate from successful-input characterization.
    The existing
    `Identity scan failed on <path>:<line>` diagnostic may omit the line number for
    a per-file grep error. Other diagnostics remain unchanged.
- **REQ-08.** THE rewrite SHALL leave ledger discovery, ledger row validation, expected
  rows and baseline knowledge inventory logic unchanged.
- **REQ-09.** THE rewrite MAY retain the ledger-discovery grep per candidate file;
  this is outside the per-line hot loop and does not require optimization.

### W3 — bounded scheduling and ordered results

- **REQ-10.** WHEN running the full suite, THE validator SHALL limit simultaneous
  acceptance groups to the validated job count. Unset `ORCHESTRAIL_TEST_JOBS` defaults
  to `min(4, usable CPU count)`, with fallback 1 if detection fails. Usable count means
  a positive result from `nproc`, otherwise `getconf _NPROCESSORS_ONLN`; the default
  cap limits unproven contention. A set value must match `[1-9][0-9]*`; reject empty,
  zero, negative, signed, leading-zero, whitespace or non-decimal values before any
  full-run check/worker, naming the variable and exiting nonzero. Values greater
  than 36 have effective concurrency 36 and must be clamped without integer overflow.
- **REQ-11.** THE scheduler SHALL execute every existing full-run expression exactly
  once and report its complete result in original source order, preserving its
  result text, stdout/stderr behavior and counters. Preserve each wrapper: the first
  three groups suppress their subprocess output; model workflow uses 60-line excerpts;
  native adapter, diagnostic registry and hook installation use 20; most others use
  35 (`:4842–5198`). Do not replace these expressions with focused flags: publication's
  focused mode additionally runs legacy recovery (`:140–152`), and model-workflow's
  focused mode aggregates other suites (`:279–289`).
- **REQ-12.** WHILE groups run, THE runner SHALL own private per-group stdout, stderr,
  result/status and, when enabled, timing records under one `mktemp -d` directory, with no child
  writing directly to parent output. On completion or runner failure it must reap
  children before removing its directory. On INT/TERM it must stop launching work,
  forward the signal to owned process trees, wait up to 2 s for graceful termination,
  escalate remaining owned processes to KILL, and complete reaping/output cleanup
  within a further 2 s in the controlled test environment, exiting 130/143.
  Ownership/containment must include descendants that start a new process group or
  session. Ordinary group-only killing is insufficient: the existing core starts
  git subprocess sessions (`hooks/git_rails.py:1634`), and a git-rails fixture starts
  `setsid sleep 6` (`tests/git-rails.sh:5084–5096`). Use a supervisor with Linux
  subreaper containment or an equivalently verified ownership mechanism; do not
  depend on a killed fixture's Python addCleanup running. A Linux-specific inline
  standard-library supervisor is within scope and is not a test-framework migration.
  The finite cleanup budget applies to synthetic runnable/stubborn processes,
  not uninterruptible kernel tasks or power failure. It must never signal the caller's process group or unrelated processes. Capture
  errors, missing/malformed worker records and launch failures must fail closed.
- **REQ-13.** THE runner SHALL finish preceding snapshot checks before launching
  acceptance groups and join **all** group trees before executing tracked hygiene at
  its existing output position. Retain all checks after hygiene and their order.
  No later snapshot may overlap workers. Bytecode writes are not permission for
  suites to mutate shared source content; resource conflicts require serialization.
- **REQ-14.** WHEN `ORCHESTRAIL_TEST_JOBS=1`, THE runner SHALL execute the same groups,
  one at a time, in their existing order with the same ordinary result output.
- **REQ-15.** WHEN a focused flag is used, THE validator SHALL preserve existing dispatch,
  argument forwarding, exec/exit behavior and internal sequential execution. The
  new jobs/timings variables apply only to full runs, even if set to invalid values.

A failed check must not prevent independent later groups from running. Parent counters
are based on explicit owned records, never inferred by grepping arbitrary test stdout.
Results are flushed only as a contiguous completed prefix, so a fast later suite cannot
report before an unfinished earlier suite. Completion order may differ from report order.
Scheduling must keep free slots productive rather than waiting for an entire batch.
Timing-sensitive groups may run exclusively when the resource inventory requires it;
this must preserve output order and must be included in performance evidence. Retain
all current timing assertions, including git-rails' five-second-budget scenarios.

### W4 — bounded recursion guard

- **REQ-16.** THE validator SHALL add a source check that rejects accidental nested
  full-validator calls in its own source and regular shell/Python sources under
  `tests/`. The check must inventory the existing forms before implementing its
  bounded scanner: direct Bash commands, the local `$validator` alias, multiline
  Python subprocess argv, copied paths, fixture-generated scripts and source text
  used as data. An allowed focused call must have a real supported focused flag on
  that same argv, not merely a `--*-only` string nearby.
  Exceptions must identify a stable file/container, exact statement or fingerprint,
  expected occurrence count and reason. Baseline examples include a stub validator
  used by the relocated-source/deploy fixtures (`:2027`, `tests/hook-install.sh:138`),
  and W1's three calls **only when** its exact guarded trimming construction is
  present. Changes in call count/context, stale allowances, or newly encountered
  unclassified validator references/alias invocations must fail for review. Comments,
  headers and literal source-copy paths are classified data, not executable calls.
  This is a regression guard for inventoried forms, not a general shell parser or
  an adversarial security boundary. Do not use a broad whole-file exemption or
  treat an unrelated occurrence of trimming code as proof of a safe fixture.
- **REQ-17.** WHEN the guard is applied to unchanged pre-W1 source, IT SHALL fail for
  the three complete history-fixture invocations. It must pass only after the guarded
  prefix construction is present and all other references are accounted for.

### W5 — timing

- **REQ-18.** WHEN `ORCHESTRAIL_TEST_TIMINGS=1` on a full run, THE validator SHALL append
  exactly one indented `time_ms=<nonnegative integer>` line after each complete outer
  PASS/FAIL/SKIP result block, including multiline diagnostics. Unset, empty or any
  other value adds no timing output. Existing non-timing result bytes remain unchanged.
- **REQ-19.** THE timing mechanism SHALL measure with a genuine monotonic clock from
  **before result-expression evaluation** until completion, with explicit source and
  resolution documented. Worker timing excludes queue wait and ordered-report wait.
  Bash `EPOCHREALTIME`, `date`, and inter-output deltas are not acceptable check clocks.
  A cheap Linux `/proc/uptime` read with documented centisecond quantization, or a
  persistent standard-library monotonic clock helper, is acceptable; starting a Python
  interpreter per check is not. Timing must not introduce timing-only sampling or a
  timing-only helper dependency when off, change errexit/subshell behavior, or break
  two-line harness extraction. A scheduler supervisor needed for process ownership
  may still use its own shutdown clock independently of W5.

### Documentation and additional contracts

- **REQ-20.** THE implementation SHALL document jobs validation/default/cap, sequential
  fallback, exclusive scheduling, timing scope/resolution and measured runtime in
  `.ai/context/runbook.md` and relevant `docs/USAGE.md` validator text; update quoted
  counts to verified results, not to a historical constant.
- **REQ-21.** THE implementation SHALL record the fixture-coverage exception, concurrency
  and cleanup decision in an indexed ADR, including any exception to the current
  literal check-call coding convention. The exception must not affect harness-parsed
  groups; preserve their two-line `check` calls.
- **REQ-22.** BEFORE rewriting checks, THE implementation SHALL freeze an ordered outer
  result inventory and the 36 full-run expression/body/diagnostic mappings from its
  own checkout, plus a resource inventory of source writes, fixed paths, locks, ports,
  inherited stores and timing bounds. Treat any source change during benchmarking
  as invalidating the affected comparison. Classify serialization needs explicitly.
- **REQ-23.** WHEN completed validation has any failed check, THE validator SHALL exit 1;
  otherwise it exits 0 with the existing summary. Configuration/internal runner errors
  and interruption are nonzero abnormal exits, not successful zero-FAIL runs.
- **REQ-24.** THE implementation SHALL preserve every baseline check name, assertion and
  result position, subject only to the stated W1 fixture exception, W2 I/O-error
  line-number exception, and new fail-closed W2 read/normalization/aggregation handling
  under REQ-07. New runtime/guard checks are additive, named explicitly in
  the implementation's frozen inventory, and counted exactly once. No fixed 654-pass
  acceptance count applies across changing source revisions.

## Data Model

No product schema, persisted user data or migration changes. Existing ledger rows and
result strings retain their formats. New runner records are private ephemeral internal
data, keyed by original group ordinal and carrying the exact result string, process
status, separated output channels and, when W5 is enabled, monotonic start/end timestamps. A worker record
must distinguish successful execution from a successfully written failure verdict.
Workers publish complete records before the parent consumes them; missing or partial
records are errors. Internal files are removed after reaping on normal/failing and
handled signal exits. Existing fixtures retain ownership of their own temporary stores.

## Contracts & Interfaces

### Consumer compatibility

| Consumer | Contract retained |
|---|---|
| `scripts/sync.sh:40–45` | Nonzero validation aborts before deployment. Test in a disposable HOME/source with a failure sentinel; never deploy to the real home. |
| Runbook and TDD callers | No-argument command, ordered outer results, existing diagnostic routing, final summary and completed-run exit rule. Warning remains before first ordinary check. |
| All 37 focused flags | Existing bodies/arguments/exec semantics; no scheduler or new environment validation in focused mode. |
| `tests/log-step.sh:30–48` | Exact Run-log contract/producer/Retrospective section marker pairs and two-line top-level `check` shapes; helpers inside those extracted sections remain self-contained. |
| Harness meta-test, `:4403–4474` | Literal `test_run_log_contract_documents_effective_runtime_tables() { run_log_contract_smoke tables; }`; complete required-name coverage and four failure/isolation scenarios. |
| `tests/hook-timing.sh:646–674` | `PYCORRELATED` heredoc label and annotation/size constraints. |
| Existing fixture construction | W1's six stripped sections and 31-producer-call guard are intentionally replaced by REQ-03; they are not permanent consumers. |

### Invariants

- **INV-1.** All existing outer checks remain exactly once, plus explicitly inventoried
  new checks; no skipped/xfail workaround or reduced test input set.
- **INV-2.** W2 and ordinary sequential results preserve baseline behavior, with the
  only permitted existing-behavior exceptions explicitly named in REQ-24. New scheduler,
  configuration, guard and diagnostics behavior follows RED coverage.
- **INV-3.** Completed-run status follows REQ-23; interruption/internal failure can never
  print a successful completion summary.
- **INV-4.** No source snapshot check overlaps a worker process tree.
- **INV-5.** Fixtures do not access real user settings/stores or real `logs/`; no weakening
  of existing HOME/XDG/log-root isolation. Maintainer-local hygiene pattern reading
  retains its documented exception and skip behavior.
- **INV-6.** Runner-owned processes and temporary output directory do not survive normal,
  failed or handled INT/TERM exits. Existing fixture cleanup is not silently replaced
  with a new universal signal guarantee. SIGKILL/power-loss cleanup is not promised.
- **INV-7.** Preserve the exact markers, literal function line and heredoc named above;
  do not introduce helper dependencies missing from extracted run-log fixtures.

## Non-Functional Requirements

### Reproducible performance acceptance

The old absolute targets (360 s sequential, 240 s parallel) describe the old workload;
retain them as **stretch goals**, not unsupported current-machine guarantees. The
binding comparison carries forward their proportional improvement on current content:

- Sequential median S must be at most `B × 360 / 1171.4` (about 30.7% of baseline).
- Default-concurrency median P must be at most `B × 240 / 1171.4` (about 20.5% of baseline).
- The isolated optimized warning fixture and identity check must each finish within
  the original 10 s budget on the controlled reference environment.

Measure at least two unchanged baseline full runs, two optimized jobs=1 full runs and
two optimized default full runs, sequentially with no other validator or heavy task.
For two values use their arithmetic mean as the median. Record every run, not just the
best. If values within a mode differ by more than 10% of their median, investigate load
and obtain a third run for that mode; retain all samples and use the three-value median.
Record source commit/blob and dirty-path inventory, machine/CPU quota, RAM, Python,
Bash/grep, locale, hygiene-pattern availability, job count, cache policy, wall/user/system,
peak RSS, exit and exact outer result counts. Use the same source payload except the
intended changes and the same locale/config for before/after; keep concurrent work and
uncommitted source changes out of the measurement window. Use a consistent warm-cache
policy for all modes, recording whether bytecode existed; do not charge cold startup
only to one side. Test harness fixtures must not inherit a benchmarking override that
invalidates their cold-cache or runtime scenarios.

Use `/usr/bin/time -v` around the real full command; timestamped output is hotspot
attribution evidence only, not an exact check clock. W5 supplies optimized per-check
measurements and actual worker durations. Record the serial prefix, concurrent-region
makespan, exclusive groups and residual suffix separately. Estimates must account for
the critical path and contention, not just add historical savings.

If any binding target is missed, record the result and the dominant costs; acceptance
remains incomplete. Do not hide misses, lower targets, remove checks or expand into
product/test-assertion changes automatically. A later scope/target amendment must be
explicit and independently revalidated. Performance budgets belong in the measurement
record, never ordinary suite timing assertions.

## Edge Cases & Failure Modes

| Case | Required outcome |
|---|---|
| No work / last partial worker batch | Finish and join without deadlock; each registered group reports once. Synthetic runner verification covers 0, 1 and more-than-jobs groups. |
| Slow first group, fast later failure | Later workers may finish and slots refill; source-order report and complete failure block are retained. |
| Several failures / a group killed externally | Continue independent work; report failed groups once and exit nonzero. Missing result metadata is an internal failure, never PASS. |
| Invalid or extremely large jobs value | Validate textual grammar before arithmetic; reject malformed values or safely clamp valid huge decimals. |
| INT/TERM while spawning, waiting or reporting | Stop launching, terminate/reap owned descendant groups, clean output records, preserve 130/143; do not kill caller/sentinel. |
| Full disk, unreadable output, failed clock/launch | Nonzero infrastructure diagnostic and owned-resource cleanup. No invented successful verdict/timing. |
| Empty/no-match file, unterminated final line, NUL, invalid UTF-8 | Preserve characterized identity rows and grep status under C and available UTF-8 locale. |
| Missing/unreadable scanned file or symlink | Preserve failure, using deterministic fault injection when permissions are ineffective for root. |
| Timing off on a full run | No timing-only sampling/helper; the W3 process supervisor may still be required. Ordinary output is preserved. |
| Focused mode, including jobs/timings variables set | Existing dispatch, output and dependencies; no W3 supervisor or W5 timing helper is introduced. |
| Resource contention or time-bound suite | Serialize conflicting groups or reduce scheduling; keep current assertions and timeouts. |

## Acceptance Criteria

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

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01,02,03,04 | AC-01,02 |
| REQ-05 | Withdrawn; replaced by REQ-03, no implementation obligation |
| REQ-06,08,09 | AC-03,04 |
| REQ-07 | AC-03,04,17 |
| REQ-10 | AC-05,06,09,13 |
| REQ-11 | AC-05,14 |
| REQ-12 | AC-06,14,15 |
| REQ-13 | AC-05,06,15 |
| REQ-14 | AC-05,06,13 |
| REQ-15 | AC-05,11,16 |
| REQ-16,17 | AC-07 |
| REQ-18 | AC-08,16 |
| REQ-19 | AC-08,09,16 |
| REQ-20 | AC-09,12 |
| REQ-21 | AC-11,12 |
| REQ-22 | AC-05,09,10,13,15 |
| REQ-23 | AC-05,06,10,14 |
| REQ-24 | AC-01,03,05,10,11,17 |

## Risks

| Risk | Impact / likelihood | Mitigation |
|---|---|---|
| Historical targets and counts hide current workload growth | High / observed | Pin fresh source and median baseline; freeze actual names/mappings and report stretch goals separately. |
| Shared paths, bytecode or test-internal threads multiply contention | High / plausible | Resource inventory, default cap 4, per-group ownership, snapshot barrier and measured exclusive scheduling. Jobs=1 is the fallback. |
| Git-rails and hook fixtures have existing real-time bounds | High / observed | Do not raise bounds; classify exclusive work and validate the real default, not a 13-group historical probe. |
| Killing only a worker shell leaks grandchildren or captured pipes | High / observed escaped-session fixture | Verified subtree ownership beyond process groups, bounded escalation/reaping and synthetic stubborn/setsid descendant cases. |
| W2 changes binary, locale or path handling | High / demonstrated | NUL normalization, exact rows, safe path transport, injected I/O errors and locale differential corpus. |
| Guard is mistaken for a complete parser | Medium / plausible | State supported forms and candidate-review limit; fingerprint/count allowances; pair static construction recognition with executable cut-sentinel coverage. |
| Timing mode changes Bash control flow or adds fork overhead | Medium / plausible | Freeze execution semantics; cheap monotonic sampling, include argument evaluation, no helper when off. |
| Existing unrelated dirty knowledge files are overwritten or contaminate measurements | High / present | Preserve unrelated changes; isolate implementation and freeze exact measurement payload/config. |

## Assumptions

- A-01 | Fixture strategy | Resolved: guarded prefix (former D-1 A) with the stated
  incidental full-copy assertion removed | Source: owner's optimization/refinement
  request and the fixture's warning-specific purpose at `:4526–4593` | Reversible: yes.
- A-02 | Delivery base | Resolved: select an isolated implementation checkout from the
  current integrated base when implementation begins; do not reset/branch this dirty
  review checkout | Source: current in-flight git-rails work and reversible isolation
  | Reversible: yes. No branch operation is performed by this specification review.
- A-03 | Duplicate run-log work | Resolved: W6/W7 deferred (former D-3/D-4 A)
  | Source: minimum coverage-preserving scope | Reversible: yes.
- A-04 | Default job count | Resolved: cap at 4 and usable CPUs, with measured exclusivity
  where necessary | Source: unproven full-tail contention and current timing assertions
  | Reversible: yes. This is a specification choice, not an owner quotation.
- A-05 | Timing platform | Resolved: implementation may use Linux's cheap monotonic
  uptime source; document any helper/dependency instead | Source: current supported
  reference environment and no per-line/per-check interpreter startup | Reversible: yes.
- A-06 | Performance criterion | Resolved: preserve original proportional improvement
  against current B; keep old absolute budgets as stretch goals | Source: demonstrated
  source growth makes historical absolute predictions unsupported | Reversible: yes.

## Decisions

Former open D-1 is resolved by A-01; D-2 is a deferred implementation checkout choice
under A-02, not a requirement to branch from stale main; D-3/D-4 are out of scope under
A-03. Superseded alternatives (public warning-only flag, retaining a complete copied run,
run-log deduplication or parallel mutations) are not simultaneous binding requirements.
No owner response is needed for the authorized specification refinement. The future
indexed ADR records delivered implementation decisions; no runtime architecture is
claimed implemented by this review.

## Clarifications

### Session 2026-11-05

- Q: What outcome did the owner authorize? → A: Correct and improve this specification,
  with an independent validator after each revision, until a score of at least 9.5/10;
  the owner reports test runs of 50 minutes or longer (translated from Russian).
- Specification defaults A-01–A-06 were inferred autonomously and are not represented
  as separately answered owner questions.

## Open Questions

None blocking specification development. Implementation must measure B, complete the
resource/exception inventories and verify the chosen scheduling strategy. Those are
specified implementation tasks with failure criteria, not missing owner decisions.

## Notes

### Implementation and verification order

1. Freeze the current checkout, result/group/resource inventories and controlled
   baseline measurements. Characterize existing scanner rows, wrapper diagnostics,
   focused dispatch and Bash execution semantics before changes.
2. Add W4 with observed RED on existing full history calls. Treat W4 as new behavior.
3. Implement W1; record its narrow fixture amendment and demonstrate cut guard,
   warning-state mutations and W4 GREEN. Do not repeatedly run full baseline fixtures
   for every warning mutation; bounded extracted real-warning probes may supplement
   the once-recorded unchanged full baseline, with that distinction explicit.
4. Implement W2 against frozen byte/path/ledger characterization. Match rows as well
   as negative verdicts and preserve existing detected failures. Handle the explicit
   read-error correction/new helper errors as separate RED behavior under AC-17.
5. Add RED coverage for new timing and scheduler contracts using deterministic small
   synthetic workers, then implement W5/W3. Preserve extracted sections unchanged.
6. Run focused consumer checks and failure/interruption/snapshot scenarios. Complete
   docs/ADR and full before/after performance acceptance on stable content. Report
   any remaining failure honestly; do not deploy as part of verification.

A practical decomposition is seven units: inventories/characterization; recursion guard;
warning fixture; identity scan; timing; worker scheduling/cleanup; docs and measurements.
W1 and W2 are independent after characterization. W6/W7 are separate future scopes.

### Implementation hints (nonbinding)

- Normalize NULs once per input, explicitly inspect grep status, and aggregate only
  successful matching output. Preserve literal paths through safe byte transport,
  such as a dedicated environment value read by awk, rather than escaped `-v` text.
- Reuse the actual full-run result expressions inside workers. Do not reconstruct
  them by guessing a focused flag or applying one common excerpt length.
- A DEBUG-based clock hook is acceptable only if executable characterization proves
  it fires before argument expansion, does not recurse or leak into extracted
  fixtures, and preserves conditional/errexit behavior. It is not prescribed here.
- There is no reason to run the unchanged 50-minute suite repeatedly during a prose
  review. Fresh complete performance runs are mandatory for implementation acceptance,
  and this document does not claim they already happened.

## Readiness Checklist

| Check | Result and reason |
|---|---|
| Goal | PASS — bounded optimization with preserved checks and measurable improvement. |
| Out of scope | PASS — explicit exclusions, including existing assertion/timeout changes. |
| Requirements | PASS — stable ids retained; withdrawn REQ-05 explicit; observable behavior. |
| Traceability | PASS — all active requirements map to acceptance and every AC names requirements. |
| Testability | PASS — existing behavior characterized; new paths have deterministic RED cases. |
| Non-functional | PASS — controlled medians, proportional budgets, exact measurement fields. |
| Data/contracts | PASS — ephemeral worker records, existing output/CLI and consumer boundaries. |
| Failure/edge cases | PASS — invalid jobs, I/O failure, descendant signals, bytes and barriers covered. |
| Ambiguities | PASS — resolved assumptions labelled; measurement/inventory work has explicit gates. |
| Blockers | PASS — no missing owner decision prevents implementation. |
| Evidence | PASS — current source anchors and historical/current/probe distinctions recorded. |
| Terminology | PASS — outer check, group, worker and baseline are distinguished. |
| Scope size | PASS — seven implementation units; duplicate run-log optimizations deferred. |

Automated readiness: **READY FOR DEVELOPMENT**. This is specification readiness only;
implementation correctness, runtime targets and independent review scores are separate
evidence and must not be inferred from this checklist.
