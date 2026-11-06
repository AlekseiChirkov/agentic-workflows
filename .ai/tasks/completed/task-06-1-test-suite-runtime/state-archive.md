# state-archive — task-06-1-test-suite-runtime

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Reduce the complete contract validator's runtime while retaining its result inventory,
coverage, focused interfaces, diagnostic channels and deployment gate. Implement the
guarded warning prefix, byte-compatible identity scan, bounded acceptance scheduling,
owned-descendant cleanup and optional monotonic timing. Prove the specified relative
and individual-check budgets against a fresh stable implementation baseline; no
implementation or performance acceptance is claimed by Discovery.

### Affected Parts
- `scripts/validate-contracts.sh`: warning fixture, identity hot loop, recursion guard,
  full-run timing, acceptance scheduling and existing counter/reporting boundaries.
- Additive `tests/validator-runtime*.sh` / `tests/validator-runtime*.py` fixtures:
  characterization, guard mutations, scanner faults, deterministic clocks and process
  lifecycle/scheduling tests. Exact filenames are planned, not existing modules.
- `.ai/context/runbook.md`, relevant validator text in `docs/USAGE.md`, an indexed
  provisional ADR, and final measurement/implementation records in project memory.
- Existing suite bodies, product helpers, hooks, CI, installed copies and real settings
  remain outside the implementation surface. W6/W7 remain deferred.

### Codebase Analysis
- Current HEAD: `4d2a9fd1f76eff06ff3aa3a760d683e01c886bac`.
  Current validator blob: `9470de8f9bcefcbf89210410c24d371fa741d5ac`.
  Both differ from the spec's inspected revision; anchors below were relocated in the
  current working tree. This does not constitute a controlled implementation baseline.
- `scripts/validate-contracts.sh:549-597`, read to verify focused dispatch precedes
  the full path, the unique standalone warning call precedes counters, and `check`
  receives an already evaluated string. Existing `set -e` semantics must be pinned.
- `scripts/validate-contracts.sh:4526-4591`, read to verify three complete copied
  executions, whole-tree tar, six-group stripping and the obsolete 31-call assertion.
- `scripts/validate-contracts.sh:4660-4835`, read to verify NUL filename transport,
  ledger discovery/masking, the per-line grep loop, symlink target reads, case-sensitive
  aggregation and knowledge-preservation checks. Preserve everything outside the hot
  loop except explicitly new I/O failure handling.
- `scripts/validate-contracts.sh:4842-5202`, read to verify the 36 acceptance expressions
  and distinct generic/20/35/60-line wrappers. The last installer group appears below
  the tracked-hygiene comment; the barrier belongs before the actual hygiene check,
  not at that comment. The later static suffix remains serial and in place.
- `tests/log-step.sh:30-48`, read to verify three exact extraction marker pairs and
  two-line top-level check removal; extracted functions need no new outer helpers.
- `tests/hook-timing.sh:646-674`, read to verify `PYCORRELATED` extraction and existing
  annotation/size checks; leave this embedded block untouched.
- `scripts/sync.sh:40-45`, read to verify a nonzero real validator stops deployment.
  Future verification uses only disposable source and HOME roots.
- `tests/git-rails.sh:5070-5096`, read to verify real five-second assertions and a
  `setsid sleep 6` descendant. Group-only signals cannot satisfy cleanup coverage.
- `tests/hook-install.sh:45-71,138-145`, read to verify isolated roots, copied source,
  inherited environment handling and the intentionally stubbed validator in sync tests.
- `scripts/validate-task.sh:1-180`, read to verify artifact-check invocation and its
  limited phase checks; manual structural checks must supplement its discovery mode.
- `hooks/git_rails.py:1630-1658`, read one level deeper to verify new-session git
  subprocesses and bounded pipe draining; this product helper must not change.
- `tests/usage-fixed-corpus.py:1-22` and `tests/usage-status-fixtures.py:1-15`, read one
  level deeper to verify source-relative imports and possible bytecode writes.
- Files read: 10/12 (7 entry-points, 3 deeper). Knowledge, spec, runbook, VERSION and
  usage documentation are outside this source-file budget. AST-Grep located Bash
  check syntax; targeted source context confirmed the affected interfaces.
- No prior task directory exists. The spec has one phase and explicit AC-01 through
  AC-17. Unrelated tracked and untracked git-rails/review changes were already present;
  preserve them and select a stable integrated payload only when execution begins.
- Bootstrap: no umbrella `.ai/`; loaded local memory architecture/state, all three
  project principles, ADR index, directly relevant ADRs 0001/0010/0012/0017, and
  environment context. No integration-service context is required.

### Open Questions
None blocking Discovery. Fresh result/reference/resource inventories, Linux containment
verification, and measured exclusivity are required execution evidence, not assumed
completed work. A missed binding budget leaves acceptance incomplete.

## Archived Solution Design — Variants

**A — retain literal checks with an opt-in pre-expansion clock hook.** Keep the Bash
validator, exact full-run expression wrappers and extracted run-log blocks. Place a
standard-library Linux supervisor inline in the validator for the acceptance region;
per-worker subreaper boundaries retain descendant ownership, including setsid children.
Encapsulate the original check expressions in worker functions with private Bash
prologues, record explicit results, and replay the contiguous completed prefix. Gate
Linux uptime sampling behind an opt-in DEBUG hook before expansion and finish timing
in the result renderer. Advantage: few changes to existing check call sites and no
per-check interpreter. Disadvantage: DEBUG behavior is subtle and needs executable
pre-expansion/conditional/subshell proof. Risk: incorrect hook inheritance or ownership
tracking changes semantics; deterministic tests must fail before production integration.

**B — retain literal checks with explicit clock sampling at each check site.** Use the
same contained scheduler and original worker functions, but add gated inline built-in
uptime reads immediately before every check evaluation, including looped call sites.
Extracted blocks retain their two-line calls and self-contained, off-by-default inline
sampling, with no missing helper dependency. Advantage: measurement order is explicit
without DEBUG. Disadvantage: hundreds of repeated timing guards and more changes inside
extracted blocks. Risk: one missed dynamic call site loses a timing record, and broad
instrumentation increases regression review. This remains an in-scope fallback, not a
license to drop timing or alter the extraction contract.

## Archived Solution Design — Rejected
- B loses on repetitive instrumentation and broader extraction-sensitive changes;
  retain it only as the explicitly rescored fallback if A's timing proof fails.
- Group-only signaling is not a viable variant: current fixtures create new sessions,
  so it cannot meet REQ-12 or AC-06. A killed fixture's unittest cleanup is not ownership.
- Replacing expressions with focused flags changes publication/model-workflow coverage
  and wrapper behavior, so it is outside the preserved contract.
- A new framework or external runtime module expands the frozen implementation surface;
  the spec explicitly allows an inline standard-library Linux supervisor instead.
- Fewer checks, altered deadlines, historical baseline reuse and W6/W7 expansion cannot
  make a missing binding performance target acceptable.

