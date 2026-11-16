# 12. One branch per composite subtask and isolated execution of its children

## Source

- **Request:** `/spec-draft .ai/specs/12-composite-branch-model-and-parallel-children.md --auto-mode`
  (refinement in place, 2026-11-13). The owner authorized in-place replacement of this file
  and declared that no questions are answered during this run.
- **Input:** the existing specification at commit `c4372f881dd544ffbf8d2374dc66a8e468d61a86`,
  file `.ai/specs/12-composite-branch-model-and-parallel-children.md`; sections 1–16 were
  written in Russian, section 17 in English. Its full original text stays in git history
  (`git show c4372f8:.ai/specs/12-composite-branch-model-and-parallel-children.md`). The
  English text below is a faithful translation of sections 1–16; section 17, the
  Implementation review and the Change Log are reproduced unchanged. Links that pointed to
  the old public repository location at pinned commit
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461` are given as repository-relative paths at that
  commit.
- **Governing decisions:** ADR-0009 Decision 4 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-174`)
  rewrote this spec's scope to "one branch and one PR per composite; parallelism only
  inside a composite"; ADR-0009 Decision 2 (`:77-113`) names the capabilities `/spec-run`
  needs for `--parallel > 1`.

### Implementation review — 2026-11-06

- **Disposition:** Planned; parallel runtime not delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Composite classification, canonical child progress, dependency ordering, and composite validation exist.
- **Outstanding scope and limits:** The branch-per-composite model, temporary child branch lifecycle, admitted parallel leaf scheduler, and per-workflow coordination in section 17 are not implemented by the shipped runner. Detached validator experiments do not deliver this contract.
- **Sources:** [`workflows/spec-run.md`](../../workflows/spec-run.md), [`workflows/pe-execute.md`](../../workflows/pe-execute.md), [`workflows/phase-composite-validation.md`](../../workflows/phase-composite-validation.md), [`rules/workflow-reference.md`](../../rules/workflow-reference.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Original text, sections 1–16 (translated from Russian)

**Title.** 12. One branch for a composite task and isolated execution of its children.

**1. Status and verified initial state.** *Status:* planned contract for isolated parallel
subtask execution. Updated 2026-11-06. This specification does not itself enable parallel
execution or authorize publication.

In snapshot `8c2fa08c` the current execution process (`workflows/spec-run.md` at that commit)
is sequential: leaves form a chain of branches, and no separate branch is created for a
composite task. The integration check (`workflows/phase-composite-validation.md` at that
commit) already distinguishes the children's validation, the combined result and open
integration errors. That is not an implementation of temporary worktrees and parallel
workers.

The current write discipline (`rules/orchestration.md` at that commit) lets a worker change
its own leaf block but returns shared changes to the orchestrator. In this specification, for
the new mode, all writes under `.ai/`, including the children's own blocks, pass to the single
orchestrator. This is a target change, not a description of established behaviour.

Basis: ADR-0009, Decisions 2 and 4. The new decision record written at implementation must
state precisely which provisions of ADR-0004 Decision 3 and ADR-0005 Decision 1 are replaced.
The history of earlier decisions is not rewritten.

**2. Goal, boundaries and important clarifications.** A composite task is validated and
reviewed as one result: it has one permanent working branch and, when publication is
permitted, one pull request. Each child works on a temporary branch owned by the run, passes
the applicable checks and is included in the shared branch by a merge commit without
flattening history.

The goal is to reduce elapsed implementation time for one large task by concurrently running
as many eligible atomic subtasks as can be proven independent. This includes direct atomic
subtasks and atomic descendants of composite subtasks within one repository and task run.
Dependencies, file ownership, integration gates and resource locks remain binding. A
speedup, lower token use or lower cost is not guaranteed. Sequential execution retains the
same quality requirements.

Ambiguities of the original edition resolved:

- *"One request" is conditional on publication permission.* Without `--allow-pr` there are
  no branch pushes and no request-creation calls; with permission exactly one request is
  created per composite task, not one per child.
- *The mode without the flag stays sequential.* `--parallel` without a number means a request
  for two executors; `--parallel N` sets an explicit maximum. The value 2 keeps the original
  choice for the enabled parallel mode.
- *Sequential continuation after an overlap starts from the current composite branch*, but the
  child still gets its own temporary branch. It does not start writing directly into the
  shared branch.
- *The child's current test mode applies.* For a new testable function or a behaviour fix,
  RED before implementation is kept. For a change that does not change behaviour,
  `atomic-tests: pinned` is allowed: the tests pin the earlier behaviour, pass before the
  change and move only to `green`; test evidence is committed before the corresponding change
  without an artificial RED. A justified `none`/`n-a` keeps the permitted single commit. For
  an old block without `atomic-tests:` that already has `atomic-execution: in-progress`, the
  narrow continuation with the note `pre-TDD task, TDD step skipped` is kept, without a
  retroactive RED. A new or not-yet-started task does not get this exception. Grounds: the
  canonical state (`rules/workflow-globals.md`) and the commit rules (`rules/git-flow.md`).

These clarifications set the agreed target text but do not replace the record of the
behaviour change required at implementation.

Out of scope: concurrent independent top-level tasks or specifications; parallel discovery;
multiple repositories; parallel ordinary single-session execution; a separate integration
branch; state tool 07; and automatic merging of owner pull requests. Parallel atomic
descendants within one large task are in scope, including across composite boundaries.

**3. Dependencies and single owners of contracts.** Prerequisites per the current index: 13,
09, completed 02 and 03, 05, 14, 15, 16, 19, 20. Applicable constraints of 06 are used through
the common safety contract; effort and model availability are resolved by 18 and catalog 04,
not anew in this document.

| Document | What 12 receives |
|---|---|
| 13 | Verifiable environment capabilities, process names and the registry |
| 09 | Offline scenarios and a separately authorized comparative evaluation |
| 05 | Identity of requests, attempts, roles and intervals; no double counting |
| 06 | Operation constraints and the narrow exception for deleting a provably included child branch |
| 14 | The child's immutable packet, current dependencies and context hashes |
| 15 | Evidence envelopes, the source-revision check, idempotent application by the orchestrator |
| 16 | Verification scope and validity of confirmations by actual inputs |
| 19 | Bounded repair attempts only for an eligible isolated defect |
| 20 | Full criteria coverage, dependencies, file ownership and independence evidence |

**4. Terms and invariants.** *Composite task* — the existing permitted task type with children
and separate integration criteria. *Wave* — a bounded set of independent children launched
concurrently; a scheduling unit, not an additional branch. *Temporary child branch* — a branch
owned by a specific run with a recorded base and tip. *Inclusion* — a verified merge of the
child's exact tip into the composite branch.

Mandatory invariants:

1. Top-level tasks keep the sequential chain. The next starts only from the verified tip of
   the previous one.
2. A composite task has one branch. A child has no separate public pull request.
3. Each child works in an isolated worktree; the orchestrator owns ref changes, commits and
   shared files.
4. Content under `.ai/` is not written by the workers of the new mode. Context packets are
   read-only snapshots; results are messages and the worker's private artifacts.
5. Before new implementation the applicable test evidence is kept: RED for new or fixed
   behaviour, or `pinned` for pinning unchanged behaviour. A legitimate `none`/`n-a` and the
   narrow compatibility of an already started old task do not produce an invented RED. A
   merge does not delete existing history.
6. A successful child check does not prove successful integration. After the merge the actual
   combined result is checked.
7. A clean textual merge does not prove independence: a change to a shared interface can
   conflict without shared files.
8. Branches and worktrees are deleted only after proven inclusion and preservation of results;
   an inconvenient conflict does not justify deleting work.
9. A repeated message, a late result and an orchestrator restart do not create a second merge
   commit, a second pull request or an additional unaccounted repair attempt.
10. An unknown environment capability and undetermined independence are not treated as
    permission for parallelism.

**5. Normative requirements.** REQ-01–REQ-05 are kept from the original additions; the other
identifiers formalize previously unnumbered criteria.

- **REQ-01. Context and writes.** Each child receives the immutable packet of 14 and a fresh
  bounded projection without its neighbours' conversations. The orchestrator verifies and
  applies sequentially all state-change proposals from the envelopes of 15; workers do not
  publish stale confirmations.
- **REQ-02. Accounting.** Children's requests, retries, checks and cache writes are counted
  once per 05. Total waiting time is shown separately from the sum of worker time. A speedup
  is not declared a cost reduction.
- **REQ-03. History and integration.** The applicable order of tests and implementation is
  kept. Before the merge, overlaps and the child's evidence are checked; the required
  integration checks run on the actual combined tree. A failed merge or check does not create
  a verified composite task.
- **REQ-04. Risk and repairs.** 16 applies to the child and to the shared area; confirmations
  are invalidated after significant changes. Policy 19 is allowed only for an isolated
  eligible defect. A dangerous shared contract or a critical finding stops new dispatch of
  work, preserves results and moves to the existing decision procedure.
- **REQ-05. Independence and capabilities.** Evidence comes from 20 and the applicable
  classifier. Required: no file overlap, no shared mutable contract or schema, no dependency
  edge and no ordering constraint. Role and model permissions are not weakened. An
  unsupported explicit parallel request is rejected; the ordinary mode stays sequential.
- **REQ-06. Branching.** The composite branch is created from the verified tip of the
  previous top-level task; for the first, from the permitted base branch. Each child gets a
  temporary branch from the recorded tip of the composite.
- **REQ-07. Merge and preservation.** Children are included with `--no-ff`, without squashing
  commits. Test and implementation commits are kept; deletion is allowed only with
  confirmation of ownership and exact inclusion per 06.
- **REQ-08. Publication.** When publication is permitted, a composite task has exactly one
  request with one stack-position line and a section per child. Without publication
  permission only a local result is created. Automatic merging of the request is outside the
  agent's authority.
- **REQ-09. Plan description.** Decomposition records `Parallel-safe: yes | no`, exact
  files and interfaces, independence grounds and the integration order in
  `plan.md → ## Decomposition Decisions`. Uncertainty equals `no` until resolved.
- **REQ-10. Parallelism limit.** The number of simultaneously active children does not
  exceed the selected positive integer N. For N > 1 actual `worktrees: yes` and
  `concurrent-sub-agents: yes` are required; `sub-agents: yes` alone is insufficient.
- **REQ-11. Overlap recheck.** Before launch, as actual paths become known, and immediately
  before the merge, overlaps with the planned, running, completed and already included
  children of the wave are checked. A detected overlap disables further parallel execution
  of this composite task and starts safe serialization.
- **REQ-12. Single final check.** After the last child is included, the orchestrator runs
  `/phase-composite-validation` (after the command migration, `composite-validation`) on the
  shared branch. The child's closing signal does not launch a second instance of the check in
  its worktree.
- **REQ-13. Recovery.** The journal links the child, worktree, base, current tip, envelope,
  merge operation and check. After an interruption the orchestrator reconciles against the
  real repository and does not rely only on the last recorded status word.
- **REQ-14. Sequential continuation.** On an overlap: stop new dispatches, preserve active
  work and run the remaining children sequentially by fresh executors from the current shared
  base through temporary branches. Usable evidence is reused only after a currency check; an
  unconfirmed result is not mixed in automatically.
- **REQ-15. Regression and equivalence.** Offline scenarios confirm identical criteria,
  constraints and final behaviour at N = 1 and N = 2; permitted live goldens are compared
  separately per 09. Normalization allows different service identifiers but does not hide
  missing evidence.
- **REQ-16. Migration.** Rules, processes, state, constraints and documentation change
  consistently; an accepted decision record fixes the replaced provisions. Active tasks of
  the previous model are not silently moved to the new one on resume.

**6. Mode interface and preflight.** *6.1 Parameter parsing.*

| Invocation | Meaning |
|---|---|
| `/spec-run ...` | Sequential execution, N = 1 |
| `/spec-run ... --parallel` | Explicit parallel request with the default N = 2 |
| `/spec-run ... --parallel 1` | The sequential path of the new composite model |
| `/spec-run ... --parallel N` | Explicit maximum N; a positive integer |
| Zero, negative, fractional or non-numeric value | Error before any branch is created or worker launched |

A configuration limit may restrict parallelism within an already chosen mode, but must not
silently turn an absent flag into a parallel launch. If an explicit request is not supported,
an explained refusal is returned with the option of choosing the sequential mode. N > 1 must
not be silently replaced by 1 while reporting that the request was fulfilled.

*6.2 Checks before the first change.* The orchestrator checks the repository and the
permitted working directory; the absence of conflicting tracked changes; the `.ai/` knowledge
policy; readiness of the previous top-level task; the plan revision; independence; free branch
and worktree names; sufficient environment capabilities; conformance of models and effort;
publication permission when needed. The presence of a worktree mechanism does not prove the
ability to run independent sub-agents safely. The described capabilities must be confirmed by
the adapter of the installed version. The mechanism limiting the number of workers is also
checked, not derived from the model's strength. Untracked user files are preserved per the
current policy; creating a worktree gives no right to delete them for cleanliness.

**7. Independence plan.** Each child requires a record:

| Field | Content |
|---|---|
| `child_id`, `composite_id` | Canonical local identifiers |
| `target_files` | Concrete expected paths; a rename names both sides |
| `interfaces` | Produced and consumed contracts and schemas, including shared configuration |
| `dependencies` | Exact predecessors with readiness conditions |
| `parallel_safe` | `yes` or `no` |
| `independence_evidence` | Grounds for all four conditions, hash of the plan and sources |
| `integration_order` | Deterministic permitted inclusion order |
| `integration_checks` | Shared criteria, checks and owner |
| `packet_digest` | Reference to the packet of 14; the final packet is formed for the actual base |

Different source files are not enough: two children can change one schema through a generator
and a consumer, one library dependency through different modules, global configuration, or one
error contract. Such changes do not run in parallel without proven independence. The actual
path set is taken from the child's diff against the saved base, not only from the worker's
message; new and deleted files, renames, generated artifacts and dependency metadata count.
Going beyond the agreed set triggers a scope review before the merge. Children with
`parallel_safe: no` run as separate sequential steps; they cannot be inserted into an active
wave just because a slot is free.

**8. Branches, worktrees and roles.** *8.1 Names and ownership.* The composite branch name
follows the current domain format `<type>/<feature-slug>`. The temporary branch is
`<composite-branch>--<child-slug>`. Substrings `T-XX`, spec numbers and task directory names
are not added to names. A collision is resolved by a domain refinement or by verified
resumption of the run's own branch, never by accidentally using someone else's. The ownership
journal records the repository and worktree identifiers, the run, the child, the branch name,
the initial hash, the current known tip and the worktree path. A name match alone is not
enough for changing or deleting a branch.

*8.2 Worker actions.* The executor changes code and tests only in its own worktree and hands
over evidence. The orchestrator makes commits and shared writes. The validator receives the
contract, the necessary tests and the actual diff; it does not inherit the executor's
conversation as its only source of understanding.

In the new parallel mode, test preparation and implementation use distinct workflow agents.
The coordinator transfers the verified test checkpoint, test mode, commands, observed RED or
pinned result and frozen-test restrictions to the implementation agent. This supersedes the
existing same-agent RED-to-GREEN rule for this mode; implementation must record the decision
and update all affected rules. A separate validation agent independently reviews the
resulting revision. Sequential rework uses fresh agents and verified evidence.

A read-only `.ai/` or a separate context packet is not system-protected merely because an
instruction says so: the adapter documentation states separately whether the prohibition is
enforced by environment permissions or by role discipline. A worker is not given shared write
access as a convenience of the parallel mode.

**9. Execution order.** *9.1 Creating the composite task.* (1) Check all preconditions and pin
the plan revision. (2) Create one branch from the verified top-level base, or provably
restore it. (3) Record the initial tip and the branching model in the journal; create no
separate integration branch. (4) Prepare sequential steps and independent waves from the
dependency graph.

*9.2 Dispatching a child.* (1) Recheck dependency readiness and the currency of the
independence grounds. (2) Create a run-owned temporary branch and worktree from the recorded
current shared base; children of one wave usually share a base, and the concrete base is
recorded for each. (3) Form the packet of 14 with the exact base, criteria, prohibitions, test
commands, integration risks and reporting rules. (4) Reserve a leaf slot within N and a task
coordinator identity; dispatch each applicable atomic workflow to a distinct workflow agent
under section 17. (5) Receive only significant envelopes of 15; do not reread the whole state
whenever no new event arrives. (6) Determine the applicable test mode. For a new testable
function or fix, verify RED and make the test commit before implementation is allowed. For a
permitted change without behaviour change, verify `pinned`, commit the passing tests before
the change and then allow only the transition to `green`. Verify the final GREEN and make the
corresponding implementation commit. A legitimate `n-a` and an old, already started block
without `atomic-tests:` follow their separate existing paths: in the second case the exact
note about the old format is kept, but RED is not invented retroactively. Removing the field
or substituting the mode for new work is forbidden. (7) Dispatch atomic validation to a fresh
independent workflow agent. Do not admit the result for integration before validation
succeeds.

*9.3 Including a verified child.* Integration uses a deterministic dependency-compatible order
from the plan, not message arrival order. The plan must not place a dependent before its
prerequisite. Independent ready leaves may refill available slots without waiting for an
entire wave; shared writes and merges remain serialized. (1) Verify the identity of the
worktree, branch, initial base, the child's current tip, the envelope and the independent
confirmation. (2) Compare the actual changes with the plan, the wave's children and the
already included changes; also check shared interfaces and invariants. (3) Check the currency
of the packet and of the confirmation per 14/16; changed inputs require widening the check;
the same branch name or one commit hash is not enough. (4) Record the merge intent with the
expected old tip of the shared branch and the exact tip of the child. (5) Prepare the merge
without flattening history; an intermediate tree used before the commit is a separate actual
input set, not an accepted result. (6) On a conflict, preserve the state and evidence; do not
apply a forced reset, an "always ours/theirs" choice or an automatic retry. (7) On the resulting
combined tree, run the affected deterministic and independent checks per 16; the child's
checks do not replace this step. (8) Commit the merge with `--no-ff`; verify that the commit's
tree equals the checked tree; if content changed, repeat the affected check. (9) Save the
merge hash, its parents, the actual tree, the confirmations and the operation state; only then
is the result considered included. If the chosen safe mechanism creates the commit before the
integration checks, the journal distinguishes "commit created" from "inclusion accepted". A
failed check keeps the commit for recovery but assigns no verified state and permits no
dependent work.

*9.4 Completing the composite task.* After all inclusions are accepted, the orchestrator
invokes the single final integration check on the shared branch. It covers the integration
criteria of the composite description, the union of the actually changed areas, shared
invariants and boundaries. Only a successful confirmation on the current result permits
`integration-validation: complete` and moving the composite row to `reviewed`. Completed
children with a failed integration do not allow closing the composite. The call from the last
child's close becomes a readiness signal to the orchestrator, not an independent rerun inside
the child's worktree; binding the operation to the shared tip and the criteria hash prevents
duplicates.

**10. Overlap and transition to sequential execution.** A detected overlap changes the
original independence assumption; it does not permit choosing file versions automatically.
(1) Mark parallel dispatch of this composite stopped; no new children start. (2) Save the
actual paths, the shared contract and the cause; do not hide it after a successful textual
merge. (3) Send running children a safe stop at the nearest provided checkpoint; do not delete
their worktrees, branches, partial tests or reports. (4) Record all received envelopes as
pending decision; a late report is not applied automatically to the new base. (5) Separate the
results: already included and confirmed; completed but not included; active or partial; not
started. No category implies automatic acceptance. (6) Check whether the already included
result can be kept without changing the contract; on a dangerous shared defect stop further
integration and move to the existing decision procedure. (7) Build a sequential order for the
remaining children; each new or rework-requiring child gets a fresh executor and a new
run-owned branch from the current shared base. (8) A previously completed result can become
evidence and source material; accepting it without rework is permitted only if the
significant inputs match and integration is rechecked; transferring changes does not cancel
the applicable test order. (9) If the reproducing test already passes on the new base, do not
fabricate RED: refine the coverage and the remaining goal through the existing plan-change
procedure; this does not turn a new function or behaviour fix into `pinned`, which stays
permitted only for pinning preserved existing behaviour. (10) Keep earlier branches until
proven inclusion or a separate permitted decision about them; do not rewrite history to make
an interrupted wave look successful. The transition to sequence stays active until the
composite completes, unless separately agreed replanning establishes a new safe contract; it
never starts an endless "parallel — conflict — retry" cycle.

**11. State, envelopes and recovery journal.** Existing canonical statuses are kept; the
technical merge state does not replace `atomic-validation` and `integration-validation`.
Minimal additive journal data: run (`run_id`, branching-model version, repository identifier,
plan hash); composite (identifier, shared branch, top-level base, actual shared tip); child
(identifier, branch and worktree, initial hash, last tip, actual paths); context (hash of the
packet, criteria, tests and significant interfaces); parallelism (requested and actual N, wave
number, reason for sequential continuation); validation (identifiers of envelopes, independent
confirmations and open findings); inclusion (operation identifier, expected parent tips, merge
hash, actual tree, check result); cleanup (evidence of ownership and inclusion, worktree
release and absence of new work); repairs (reference to the episode and counters of 19; a
restart creates no new limit). For one merge the journal distinguishes at least the intent,
the started operation, the created commit, the verified acceptance and the completed cleanup.
These are logical journal stages, not a new task status vocabulary. A state change and a ref
update do not form one file transaction; recovery must reconcile both sides.

Two concurrently dispatched children may carry the same initial hash of shared state.
Applying the first result makes the second's source revision stale even if its own work stays
correct. The orchestrator does not rewrite the old envelope or apply its old patch: it
reconciles the current target fields, contract, tree and evidence and, if the preconditions
hold, forms a new derived proposal against the current revision with a separate `proposal_id`
and a reference `original_event_id`. The original `event_id` and its hash stay unchanged. Such
re-preparation is not a new execution, a new repair attempt or a second billable unit; history
links the original message and the single accepted change. A conflict of significant fields
requires a decision, not a mechanical transfer.

*11.1 Resumption.* If the intent is recorded and nothing changed, repeat the precondition
check before executing. If the merge was interrupted by a conflict, preserve the conflict and
do not start another merge on top of it. If the commit was created but the confirmation not
recorded, check its exact parents, tree and actual evidence; do not create a second commit
automatically. If the state is marked accepted but the shared tip or the verified inputs
changed, treat the confirmation as stale and check the affected area. If a repeated envelope
arrives, compare its identifier and content hash: an identical already applied result is not
repeated; a differing one is rejected as a conflict. If a pull request already exists, check its
repository, source and target branches and its ownership by the run, and update it within the
permission instead of creating a second one. If a worker is unknown after a restart, first
check its existence and worktree; do not launch a replacement over live work.

**12. Errors and repairs.**

| Situation | Action |
|---|---|
| A required environment capability is missing | The explicit parallel request is refused; the sequential path stays available separately |
| Independence is not proven | The child runs sequentially |
| Writes outside the target files or a change to a shared contract | Stop dispatch and inclusion, preserve the evidence, review the scope |
| The child's independent check fails | Keep the default stop; apply 19 only when the permitted policy is explicitly enabled |
| Merge conflict | Keep the branches and the conflict; do not resolve automatically or declare the inclusion successful |
| The combined result violates a criterion | The composite stays unverified; use the existing integration-issue process and fixing children |
| A critical violation of an invariant, security or the agreed architecture | Stop new dispatches and move to the provided decision; do not multiply autonomous attempts |
| An output write or accounting error | Record the uncertainty; do not repeat the change to obtain a clean output |
| A provider limit is exceeded | Keep the work and stop new calls; do not switch accounts to bypass the limit |
| A cleanup failure | Leave the branch or worktree and report the reason; a successful result requires no risky deletion |

Integration fixing children are created under the current decision protocol: in interactive
mode by the user's decision; in an already authorized autonomous mode with the provided
automatic `critical`/`important`/`optional` classification. This does not cancel the special
hard stops for violated intent, architecture or invariants. Creating a fixing child does not
mean silently launching it in the remaining parallel wave. Policy 19 keeps at most one local
and one explicitly authorized stronger attempt per episode; the attempt slot is reserved
before launch. An undetermined, already dispatched launch is not a free retry. Serialization,
a worktree change and a new executor do not reset the history.

**13. Publication and cleanup.** *13.1 One pull request.* After a successful shared check and
with `--allow-pr` in force, the shared branch is published and one request is created or
updated. Its target branch is the previous top-level branch, or the initial base for the first
task. Temporary child branches are not published separately to create requests. The content
includes the domain goal, the combined result, one stack-position line and, per child, its
goal, criteria and test evidence, including the test commit hash where required. Domain names
of children are used, not `T-XX`, spec numbers, links to `.ai/` or internal process names; the
mapping to local identifiers stays in state. The text explains the test order in plain language
without forbidden internal jargon. A draft request is not by itself a technical prohibition on
merging; the user chooses the final merge; the agent keeps the constraints of 06 and does not
run `gh pr merge`.

*13.2 Cleanup of temporary work.* Before deletion, check the exact ownership of the branch,
the match of its saved tip, its inclusion in the accepted shared history, and the absence of an
active worker and of unsaved changes. First release the worktree safely; then delete only the
provably run-owned temporary branch by a permitted method. If the branch pointer moved after
inclusion, deletion is forbidden until a new check. Without evidence the branch is kept. Forced
deletions, `reset --hard` and `clean` are never used for cleanup.

**14. Measurement and mode comparison.** The journal keeps `parallel: N` for the run and
`wave: k` for child steps, plus the actual number of active workers and the reason for reduced
parallelism. Telemetry 05 links each attempt and check to the child without duplicating it in
the composite's sum. The report shows the total elapsed time, the sum of worker durations,
orchestrator and integration time, the number of rechecks, context volumes and observed cache
reads and writes; the sum of durations is never added to the total time as another expense of
the user's time. The parallel mode can be faster and more expensive. Comparison per 09 uses the
same source tasks and independent criteria, including integration defects. Normalized
artifacts at N = 1 and N = 2 must match in semantic obligations, not necessarily in every hash
or write moment.

**15. Acceptance criteria (original).**

- AC-01 (REQ-01, REQ-02): interleaved events of two children do not mix context; shared changes
  are applied sequentially; requests are counted once; the sum of worker time does not become
  waiting time.
- AC-02 (REQ-03, REQ-04): conflicts, changed interfaces and failed checks preserve history,
  invalidate stale confirmations and do not close the composite.
- AC-03 (REQ-05): an unsupported environment, overlapping paths and a shared mutable contract
  do not launch a parallel wave. The semantic obligations of the sequential and parallel
  results match; a paid check is authorized separately.
- AC-04 (REQ-06, REQ-07): the task has one shared branch; each child has a temporary branch
  from the recorded base; the merge keeps the parent links and the applicable test commits.
  Forged ownership or a mismatched tip does not allow deleting the branch.
- AC-05 (REQ-08): without `--allow-pr` there are no pushes and no request-creation commands;
  with permission exactly one request is created; a repeat or resume creates no duplicate;
  internal identifiers do not reach public text.
- AC-06 (REQ-09, REQ-10): the plan contains evidence for every independence condition; the
  number of active children never exceeds N; an invalid N is rejected before any effect; an
  absent flag stays sequential.
- AC-07 (REQ-11, REQ-14): an unexpected overlap before or after one child finishes stops new
  dispatches; partial results are kept; the remaining children get fresh executors and
  temporary branches from the current base.
- AC-08 (REQ-12): the last child's signal triggers exactly one shared check on the composite
  branch; without a successful result on its current tree the `reviewed` status is unreachable.
- AC-09 (REQ-13): interruptions before the merge, during a conflict, after the commit and
  before the confirmation is recorded are recovered without a repeated merge, data loss or
  reset attempt counters.
- AC-10 (REQ-15): offline scenarios at N = 1 and N = 2 check identical criteria, results and
  evidence; differences of time and hashes are normalized without erasing errors.
- AC-11 (REQ-16): rules and calls never contain old and new contradictory closing methods at the
  same time; an active task of the old version does not migrate silently on resume.
- AC-12 (REQ-03, REQ-04, REQ-07): a legitimate `n-a` is kept without fictitious tests;
  `pinned → green` passes without an artificial RED; an already started old block without
  `atomic-tests:` keeps the provided note and requires no retroactive RED. For a new testable
  function or fix the mandatory order holds; a false `pinned` and removing the field to bypass
  it are rejected. A repair does not change frozen tests and does not exceed the limits of 19.

All listed scenarios have offline reproducible variants. A live `composite` golden at N = 1 and
N = 2 is needed for claims about real model behaviour, but its absence does not prevent
accepting the deterministic infrastructure separately; such claims stay unverified until
experience exists.

**16. Implementation and rollout order.** (1) Pin the current rules, plan, interfaces and
environment capabilities; record the differences between the old and new model. (2) Agree the
decision record: composite branch, temporary children, conditional publication, one writer,
single final check and the semantics of the parallelism parameter. (3) Implement the sequential
model N = 1 first, including the journal, recovery, merge and cleanup. (4) Check preservation
of test history, legitimate `pinned`/`n-a`, the narrow compatibility of the old already started
block, publication and composite closing. (5) Add independence evidence and parallel dispatch
with limit N; check mutual isolation and serialization of shared effects. (6) Add overlaps, wave
stop, fresh executors and recovery after interruption; the happy path is not sufficient. (7)
Connect telemetry and reports; update the offline projects of 09 and shared documentation. (8)
Roll out for new or explicitly migrated tasks. When parallelism is disabled, keep the new
branching guarantees and the history of an already started composite; do not return it
automatically to the old chain of separate requests. Readiness means fulfilled offline criteria
and described recovery. It does not mean permitted publication, a parallel mode enabled by
default or measured financial benefit.

### Original section 17 (English, unchanged)

**17. Parallel atomic workflows across the task tree**

*17.1. Source and scope.* The owner clarified on 2026-11-06 (translated from Russian): execute
eligible atomic subtasks of one large task in parallel to shorten implementation time; give
each atomic subtask its own coordinating agent and each atomic workflow a separate agent.
Analysis and test preparation, implementation, and validation are examples of distinct
workflows. The [example task](../tasks/completed/task-06-1-test-suite-runtime/plan.md) is
planning evidence, not authorization to change or run it.

The current runner explicitly executes subtasks sequentially and uses one implementer for
test and implementation checkpoints ([dependency ordering](../../workflows/spec-run.md#L163),
[handoff](../../workflows/spec-run.md#L208), [parallelism prohibition](../../workflows/spec-run.md#L367)).
Atomic execution orders test preparation, implementation and finalization
([execution](../../workflows/phase-atomic-execution.md#L100)); atomic validation orders check,
proposals and close ([validation](../../workflows/phase-atomic-validation.md#L73)). This
section defines a future replacement for those runner rules, not current behavior.

*17.2. Scheduler and ownership requirements.*

- **REQ-17. Task tree.** WHEN an authorized parallel run processes a large task, THE SYSTEM SHALL build one dependency graph of its atomic leaves, including descendants of composite nodes and leaves directly under the task. Composite nodes remain containers and integration gates, not atomic implementation jobs. Independent top-level task runs remain sequential.
- **REQ-18. Admission.** WHEN a leaf is considered for dispatch, THE SYSTEM SHALL admit it only after every declared prerequisite is integrated and reviewed, enclosing gates and other applicable prerequisites permit execution, and its file, interface and resource independence from every active leaf is established. A composite prerequisite is satisfied only after its children and composite integration validation pass.
- **REQ-19. File exclusion.** WHILE a leaf holds its write reservation, THE SYSTEM SHALL prevent another active leaf from writing any of the same normalized repository paths, including test, configuration, generated, deleted and both sides of renamed files. A directory or glob that cannot be resolved to a complete stable set is an overlapping reservation. Distinct worktrees do not waive this exclusion; root-owned shared-state updates remain sequential under REQ-01.
- **REQ-20. Leaf coordination.** WHEN an eligible leaf starts, THE SYSTEM SHALL assign it a dedicated task-coordinator sub-agent that owns its atomic execution and validation sequence and reports to the root orchestrator; it shall not coordinate another leaf concurrently. The root remains the sole writer of shared state and owner of git operations.
- **REQ-21. Workflow agent isolation.** WHEN an applicable atomic workflow is invoked for a leaf, THE SYSTEM SHALL dispatch it to a fresh workflow sub-agent dedicated to that invocation. Atomic execution (/phase-atomic-execution), test analysis/preparation (/pae-tests), implementation (/pae-implement), finalization (/pae-finalize), atomic validation (/phase-atomic-validation), and its applicable child workflows (/pav-check, /pav-propose and /pav-close) each have a distinct fresh agent identity, also distinct from the leaf coordinator and root. Phase agents coordinate their ordered child workflow invocations; the root mediates dispatch if necessary. Finalization and close propose state deltas for the root; neither workflow workers nor leaf coordinators directly write shared .ai/ state or perform root-owned git operations.
- **REQ-22. Verified handoff.** WHEN a workflow completes, THE SYSTEM SHALL pass the next workflow an immutable, minimally scoped handoff containing leaf and attempt identities, base and exact candidate tree/commit, task contract and applicable acceptance criteria, allowed paths, test mode, commands, observed results and artifact digests. The implementation agent receives verified frozen RED or pinned evidence before implementation; the validation agent receives implementation and test evidence independently. A failed, missing, stale or mismatched handoff blocks its dependent stage.
- **REQ-23. Limits and refill.** WHILE parallel mode is active, THE SYSTEM SHALL cap active leaves at N, separately count task coordinators and workflow agents against actual platform agent capacity, and dispatch another ready independent leaf when a slot and all required locks are available. A leaf retains its slot and reservations through atomic validation and until its result is integrated or safely withdrawn. Record requested and effective limits and capacity constraints.
- **REQ-24. Failure isolation.** IF a leaf fails or is blocked, THEN THE SYSTEM SHALL block its descendants and dependent joins, retain its work and evidence, and allow unrelated eligible leaves to continue when no shared safety invariant, resource lock or critical defect requires a broader stop. Existing conflict handling in section 10 applies when asserted independence is disproved.
- **REQ-25. Capability preflight.** BEFORE creating branches or dispatching in this mode, THE SYSTEM SHALL verify worktree isolation, concurrent sub-agents, agent messaging, and the ability to run dedicated coordinators and distinct workflow agents under available delegation permissions. If nested delegation is unavailable, root-mediated flat dispatch is permitted only if it preserves the same identities, sequence, handoffs and ownership; otherwise reject the explicit parallel request with the missing capability and perform no partial dispatch.
- **REQ-26. Completion and measurement.** WHEN all leaves and composite gates complete, THE SYSTEM SHALL verify the integrated task result against the parent contract on the final tree, record the verdict, and report wall time, active-leaf concurrency, worker time, integration/rework time and conflicts separately. Compare sequential and parallel runs only on comparable inputs and quality gates; measured acceleration is evidence, not an unconditional acceptance guarantee.
- **REQ-27. Recovery.** WHEN a run resumes, THE SYSTEM SHALL reconcile each leaf coordinator, workflow invocation, attempt, reservation, candidate tree, handoff, dependency and integration receipt against actual live agents and repository state before redispatch. Never duplicate a live invocation, release a reservation held by a live writer, reuse a stale validation, or lose partial work.

*17.3. Execution and integration contract.* The root expands the task tree into a DAG,
preserves composite joins, checks the versioned plan and reserves file and resource ownership
before dispatch. A ready leaf gets its own isolated branch and worktree, a coordinator, and a
bounded sequence of workflow agents. The coordinator directs phase sequence and returns
evidence; it does not mutate shared state or git. The root may mediate workflow-agent creation
when nested spawning is unavailable. An active leaf runs from reservation through integrated
acceptance or safe withdrawal; N limits leaves, not the total number of agents. Platform
capacity includes the root, coordinators and active workflow agents; report any smaller
effective concurrency.

For testable new behavior, a test agent produces RED evidence; the root verifies and commits
the test checkpoint; a fresh implementation agent receives that checkpoint and produces GREEN;
the root verifies and commits implementation. For permitted characterization, transfer pinned
evidence instead. Documented n-a and legacy in-progress paths remain applicable without
invented RED evidence. A fresh atomic-execution phase agent coordinates test preparation,
implementation and execution finalization, each dispatched to a distinct agent. After
execution finalization, a fresh independent validation phase agent coordinates its ordered
check, proposal and close workflows, each dispatched to a distinct agent when applicable. The
root applies validated state proposals in order. No stage starts until its predecessor has
successfully handed off. Validation failure cannot close the leaf.

A leaf branches from an integrated tree containing all reviewed prerequisites. For nested
composites, the root integrates leaves into their owning composite branch in deterministic
dependency-compatible order and runs that composite single integration gate before integrating
its branch into its parent. Direct leaves integrate into the parent task branch. The parent
final verification is separate from each composite gate. Cross-boundary leaves may run
together only when dependencies and ownership permit it; no dependent leaf starts on an
unintegrated candidate. A dependency outside the owning composite becomes usable only after
its verified result is integrated into an ancestor branch and the owning composite branch
incorporates that exact verified ancestor revision. If the prerequisite is inside another
composite, first complete and integrate that composite gate; do not copy unintegrated leaf
changes across branches. Revalidate affected evidence after incorporating ancestor changes.
Existing no-fast-forward history, single-writer, recovery, publication and conflict rules
remain in force.

If a worker requests or is observed to change a path outside its reservation, stop its writes
and new admissions involving the affected set; preserve candidate trees and compare actual
paths before integration. If overlap or a common-contract conflict invalidates independence,
apply section 10 conservative stop and serialization for the affected task scope. Release a
path only after integration or confirmed worker termination and preservation of its work.
Read-only analysis does not acquire a write reservation and cannot be treated as completed
implementation. Host-exclusive checks, benchmarks and resource locks are separate from file
reservations and apply globally.

*17.4. Example and assumptions.* The example plan identifies the baseline as a prerequisite and
final integration and performance work as joins. It lists four candidate lanes after the
baseline, but the guard, identity, timing and lifecycle leaf descriptions all name
scripts/validate-contracts.sh as a target. These leaves therefore cannot hold concurrent write
reservations under REQ-19, even in separate worktrees. A revised plan may permit concurrency
only after establishing complete, disjoint actual write sets and independent interfaces;
otherwise they run sequentially. This example does not claim that the current task has four
parallel-writable leaves.

Assumptions: the existing explicit --parallel opt-in and N=2 default remain unchanged; the
requested parallelism is inside one task. The coordinator and fresh-workflow-agent model
applies to the new mode and requires a capability-aware adapter. No migration of an active
task is implied. The present same-agent test handoff must be replaced for this mode while
retaining frozen-test guarantees.

*17.5. Additional acceptance criteria.*

- [ ] **AC-13** (REQ-17, REQ-18, REQ-23): Given four ready leaves with pairwise disjoint complete write sets, independent contracts and sufficient capacity, when parallel mode runs with N=4, four dedicated leaf coordinators are active concurrently. A fifth leaf waits; when a slot is safely released, an eligible waiting leaf starts without waiting for an unrelated wave. Dependencies and composite join gates are never bypassed.
- [ ] **AC-14** (REQ-19, REQ-23): Given two ready leaves targeting the same normalized file, including a rename destination or generated output, when N exceeds one, their write intervals do not overlap even across worktrees. Unknown or overlapping directory reservations also prevent concurrent admission.
- [ ] **AC-15** (REQ-20, REQ-21, REQ-22): Given a testable leaf, when its atomic workflows run, its coordinator, execution phase, test, implementation, finalization, validation phase and applicable validation child agents all have distinct identities; RED is verified and committed before the implementation agent starts, GREEN precedes validation, and handoff identities and digests are recorded. Shared state and git changes occur only through the root. Missing or stale handoff evidence blocks the next stage.
- [ ] **AC-16** (REQ-17, REQ-18, REQ-24): Given independent leaves in different composites and a failed leaf with a dependent, when scheduling continues, the unrelated eligible leaf can complete; the failed leaf dependent and its composite join cannot start or close. A critical shared invariant failure invokes the broader stop.
- [ ] **AC-17** (REQ-25, REQ-27): Given unavailable nested delegation, root-mediated dispatch preserves required identities and order when supported; otherwise preflight rejects the request before mutation. After interruption, a live workflow is not redispatched and its write reservation remains held until safe reconciliation.
- [ ] **AC-18** (REQ-18, REQ-19, REQ-26): Given the example guard, identity, timing and lifecycle leaves with the same target file, when their dependency is satisfied, the scheduler never admits them as concurrent writers. The final report separates elapsed time, aggregate worker time, integration/rework and actual concurrency; no speedup is claimed without comparable measurements.
- [ ] **AC-19** (REQ-18, REQ-21, REQ-22, REQ-26): Given nested composites and direct leaves, when all atomic validations and composite joins pass, each composite gate runs once on its integrated tree and the final parent contract is checked on the final integrated tree. Failed or stale validation prevents completion.

The new requirements map to AC-13–AC-19 above. Add deterministic scheduler,
isolated-worktree, workflow-identity, handoff, failure, recovery and integration fixtures
before implementation; retain existing N=1/N=2 equivalence scenarios. No paid benchmark is
required for deterministic acceptance.

## Context & Problem

Verified at worktree revision `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff` (2026-11-13).

**Current branch model.** `/spec-run` treats a composite row as a container that "get[s] no
branch and no agent; their children appear in the order as ordinary leaves"
(`workflows/spec-run.md:162-165`). Every leaf, composite children included, gets its own
stacked branch cut from the previous reviewed leaf's tip (`workflows/spec-run.md:200-206`,
`rules/git-flow.md:52-58`) and, with `--allow-pr`, its own draft pull request whose base is the
previous subtask's branch (`workflows/spec-run.md:305-308`, `rules/git-flow.md:173-180`). When
the last child closes, `/pav-close` step 5 calls `/phase-composite-validation` from inside the
Validator, "on the current branch — the tip already contains every child. Do not create a
branch for the composite" (`workflows/spec-run.md:301-303`, `workflows/pav-close.md:53-66`).
The composite integration check takes "the union of all files changed by any child" from the
children's `target_files:` as its surface (`workflows/phase-composite-validation.md:57`).

**Current execution model.** Execution is strictly sequential: "Never start N+1 before N is
`reviewed`" (`workflows/spec-run.md:190`), "Never runs subtasks in parallel"
(`workflows/spec-run.md:378`), "Sub-agents exist to bound context, not to run work in
parallel" (`rules/orchestration.md:10-14`), and orchestrated mode "is strictly sequential — no
workflow may introduce concurrent subtask execution" (`rules/workflow-globals.md:106-109`).
One Implementer runs `/pae-tests`, pauses at RED, and continues `/pae-implement` →
`/pae-finalize` in the same context (`workflows/spec-run.md:208`, `:264-267`;
`rules/orchestration.md:58-61`); ADR-0004 rejected separate test and implementation agents
(`.ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md:46-47`). A sub-agent
writes its own `## Subtask Progress` block and returns deltas for shared files
(`rules/orchestration.md:26`, `:98-108`). `/spec-run` accepts only `--allow-pr` and
`--dry-run` (`workflows/spec-run.md:5`); no `--parallel` flag exists. `/pd-decompose` tells
the planner "under `/spec-run`, preserve strictly sequential stack order … Do not claim
unsupported parallel execution" (`workflows/pd-decompose.md:124-129`) and its
`## Decomposition Decisions` table has no independence columns (`workflows/pd-decompose.md:131-138`).

**Current state format.** A leaf block carries `branch:`, `base_branch:`, `base_commit:`,
`commits:`, `pr:` in orchestrated mode (`rules/workflow-globals.md:175-186`); a composite block
carries only `children:`, `blocker:`, `notes:` (`rules/workflow-globals.md:210-219`). Composites
are never nested (depth-2 cap, `.ai/principles/domain.md:20`).

**Current git rails.** Branch deletion is "Owner approval required; a verified temporary
child-branch exception is planned" (`rules/git-flow.md:228`), and the contract validator pins
that exact wording (`scripts/validate-contracts.sh:5614`). The hook routes R22 (`git branch
-d/-D`) and R23 (`git update-ref -d`) through a replaceable `DELETION_VERIFIER` whose shipped
implementation `no_exception_verifier` grants nothing (`hooks/git_rails.py:3066-3096`,
`:3284-3290`, `:3336-3354`); the git-rails suite asserts that default
(`tests/git-rails.sh:2801-2802`). Spec 06 reserved this extension point for this spec and
prefers `git update-ref -d refs/heads/<b> <expected-sha>` (completed spec 06 §8.7 "Branch deletion and the spec 12 extension point").
`git merge` is checked only when the current branch is protected (R27,
`hooks/git_rails.py:3385-3387`). `/restack` collects every branch-owning subtask block in plan
order (`workflows/restack.md:21-23`) and uses one recovery-journal pattern that the hook
verifies (`workflows/restack.md:38-107`). `git worktree remove --force` is not enforced by the
hook (`harness/claude/capabilities.md:73`, X3).

**Capabilities.** Neither capability record declares `sub-agents`, `agent-messaging`, `git`,
`worktrees` or `concurrent-sub-agents` today (`harness/claude/capabilities.md`,
`harness/codex/capabilities.md`); spec 13 owns those keys (13 DM-4) and the `/spec-run`
capability preflight (13 REQ-37).

**Decided but not built.** ADR-0009 Decision 4 decided one branch and one PR per composite in
sequential and parallel mode alike, `--no-ff` merge-back of temporary child branches,
orchestrator-only `.ai/` writes in parallel mode, an independence record written by
`/pd-decompose` and re-verified before merge-back, and parallelism "only between children of
one composite" (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-174`). The 2026-11-06
owner clarification (Source, section 17) widens parallelism to atomic leaves across composite
boundaries and directly under the task, which conflicts with that decision; the owner resolved
that conflict on 2026-11-14 in favour of the decision (D-04, Q-01).

**Consequence.** A composite's children are reviewed as separate stacked pull requests although
their integration criteria apply only to their union; every independent child waits for its
predecessor; and the git rails still ask the owner to delete any temporary branch the pipeline
creates. Large tasks pay serial wall-clock time (ADR-0004 records 21–26 h per run,
`.ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md:90`).

## Goal

Give every composite subtask run by `/spec-run` one permanent branch and, when publication is
authorized, one pull request: each child runs on a temporary, run-owned branch, passes its
own atomic cycle, and is merged into the composite branch with a `--no-ff` merge commit that
keeps its test-first commits, after which the run deletes the temporary branch only when the
git-rails hook can verify the deletion. On that model, let an explicitly requested parallel
run (`--parallel [N]`) execute up to N proven-independent children of the same composite
concurrently in isolated worktrees, each through dedicated coordinator and workflow agents,
while the orchestrator stays the single writer of shared state and the only git operator,
serializes the composite on any disproved independence, and recovers from interruption
without duplicate merges, lost work or reset counters. Speed, token use and cost are measured,
not promised.

## Scope

1. The per-composite branch model for new `/spec-run` tasks in sequential mode (N = 1) and
   parallel mode (N > 1): composite branch, temporary child branches, `--no-ff` integration,
   post-merge checks, composite validation on the composite branch, one PR per composite.
2. The `branch_model:` task field and the additive git fields of composite and child blocks,
   with backward compatibility for tasks run under the per-leaf stack.
3. The composite journal (schema, location, stages, atomic write) and resume reconciliation.
4. Cleanup of temporary worktrees and branches, and a git-rails `DELETION_VERIFIER` that
   allows exactly one verified deletion form.
5. The `--parallel [N]` flag, its parsing, dry-run reporting and capability/helper preflight.
6. The `### Parallel Safety` plan record written by `/pd-decompose`.
7. Admission, write reservations, refill, overlap detection and serialization among the
   children of one composite.
8. Leaf coordinators, distinct workflow agents per atomic workflow and verified handoffs in
   parallel mode.
9. The optional helper `scripts/composite_run.py` that makes admission, write-set, merge-check,
   reconciliation and measurement decisions deterministic.
10. `/restack` handling of per-composite tasks.
11. Rule, workflow, principle, vocabulary and documentation updates, the superseding ADR, and
    deterministic contract and fixture checks.

**Delivery gate.** The scope is delivered in two stages that share this specification:
**12A** (items 1–4, 10 and the N = 1 parts of 11; the requirement list is in
`## Notes → ### Delivery stages`) and **12B** (items 5–9 and the rest of 11). 12B starts only
after 12A is accepted. Neither stage starts before the owner schedules it; the roadmap lists
this spec after 13, 09, 05, 14, 15, 16, 19 and 20 (`.ai/specs/README.md` → "Dependency order"), and A-18 states
the conservative behaviour while 14, 15, 16 and 19 are undelivered.

## Out of Scope

- Parallel execution across composite boundaries (children of different composites running
  together) and of leaves directly under the task (top-level leaves), and any change to the
  top-level stack order. The owner deferred it on 2026-11-14 (D-04); parallelism exists only
  between the children of one composite. A possible successor specification is named in
  `## Notes → ### Successor path`.
- Concurrent independent tasks or specifications, parallel Discovery, multi-repository runs,
  and parallel execution outside `/spec-run` (`/phase-execution`, `/phase-pipeline`,
  `/pe-execute` stay sequential).
- A separate integration branch, wave branches, or a task-level branch.
- Pushing or opening pull requests for temporary child branches.
- Merging any pull request, locally or through `gh` (unchanged rail, `rules/git-flow.md:180`).
- The state tool of spec 07 (ADR-0021); the root may use it as its writer when available, but
  nothing here depends on it.
- Defining the capability keys or their declaration format (spec 13), the context packet
  (spec 14), checkpoint envelopes and derived proposals (spec 15), verification scope (spec 16),
  repair attempts (spec 19), independence evidence content (spec 20), telemetry attribution
  (spec 05), effort (spec 18) and golden evaluation (spec 09).
- Changing the run-log vocabulary or adding run-log fields (`rules/run-log.md`, spec 02).
- Migrating a task that already recorded per-leaf branches to the new model.
- Preserving merge commits through `/restack` (Q-02); the exact verified replay form stays.
- Any speedup, token or cost target, and any paid comparison run.
- Changing existing tasks, branches or history in this repository.

## Actors & Roles

| Actor | Allowed actions | Forbidden |
|---|---|---|
| Owner | Invokes `/spec-run` with or without `--parallel`/`--allow-pr`; answers class-B questions; approves or rejects hook asks; merges PRs | — |
| Orchestrator (root) | Sequencing, admission, every git operation, every write under `.ai/` and to the composite journal, spawning agents, applying deltas, running the helper | Writing code or tests; resolving class-B questions; merging PRs; force or rebase outside `/restack` |
| Arbiter | Answers class-A questions with citations (unchanged, `rules/orchestration.md:38-54`) | Writing anything |
| Leaf coordinator (parallel mode) | For one child attempt: requests workflow agents from the root, passes and verifies handoffs, reports stage results and stop acknowledgements to the root | Writing `.ai/`, the journal or code; git operations; coordinating a second child |
| Workflow agent (parallel mode) | Runs exactly one workflow invocation (`/phase-atomic-execution`, `/pae-tests`, `/pae-implement`, `/pae-finalize`, `/phase-atomic-validation`, `/pav-check`, `/pav-propose`, `/pav-close`); edits code and tests only inside its child's worktree and only within its reservation (execution workflows); returns results and deltas | Writing `.ai/` (root or worktree copy), the journal, or files outside the reservation; git write operations |
| Implementer / Validator (effective limit 1) | Unchanged roles (`rules/orchestration.md:56-92`), working in the root worktree on the checked-out child branch | Git operations; shared-file writes beyond the existing own-block carve-out |
| Composite validation agent | A fresh validation sub-agent that runs `/phase-composite-validation` on the composite branch and returns deltas | Writing shared files; git operations |
| git-rails hook | Decides deletion commands through the replaced `DELETION_VERIFIER` | Writing any file |
| `scripts/composite_run.py` | Reads plan, journal and repository; prints decisions | Writing files; git write commands; spawning models |

## Terminology

| Term | Definition | Source |
|---|---|---|
| **Branch model** | Task-level `branch_model:` value: `per-leaf` (every leaf, composite children included, gets a stacked branch; the shipped behaviour) or `per-composite` (this spec). | New; REQ-16 |
| **Composite branch** | The one stacked branch of a composite subtask in a `per-composite` task, cut like any stack branch and named `<type>/<feature-slug>` from the composite's Goal. | ADR-0009 D4; REQ-06 |
| **Child** | A leaf listed in a composite block's `children:`. | `rules/workflow-globals.md:210-219` |
| **Attempt** | One execution of a child on one temporary branch; a rework after serialization is a new attempt. Not a repair attempt of spec 19. | New |
| **Child branch** | The temporary, run-owned, never-pushed branch of one attempt: `<composite-branch>--<child-slug>` for attempt 1, `<composite-branch>--<child-slug>-attempt-<k>` for attempt k ≥ 2. `<child-slug>` follows the branch slug rules of `rules/git-flow.md:60-71` (collisions between children are refined from their Goals); the `--` separator is exempt from repeat-collapsing. | Original §8.1; REQ-30 |
| **Integration** | The verified `--no-ff` merge of a child attempt's exact tip into the composite branch, accepted only after post-merge checks pass and state is recorded. Synonym "inclusion" in the original. | Original §4; REQ-03 |
| **Post-merge check** | Running, on the merged composite tree, the recorded test command of every child accepted so far plus the merged child. A child-branch result, including a spec 16 receipt, never stands for it (A-28). | REQ-03 |
| **Composite journal** | The JSON recovery record `<git-common-dir>/orchestrail-composite/<sha256(task_path)>.json` owned by the root. | REQ-13 |
| **Stage** | A journal-only lifecycle value of an attempt (DM-3). Not a task status. | Original §11 |
| **Parallel limit N** | The positive integer maximum of concurrently active children of one composite; 1 without the flag. | Original §6.1; REQ-10, REQ-29 |
| **Active child** | A child whose latest attempt stage is `branched`, `dispatched`, `validated`, `merge-intent` or `merged`; it occupies one slot of the effective limit. | REQ-10, REQ-23 |
| **Reservation-holding child** | An active child, or one whose latest attempt is `failed`, `blocked`, `check-failed` or `conflict`. | REQ-19, REQ-23 |
| **Write set** | Planned: the explicit file list in `### Parallel Safety`. Actual: the normalized paths of `git diff --name-status -M <base>..<tip>` (both sides of renames) plus uncommitted and untracked changes of the child's worktree. | Original §7; REQ-19 |
| **Reservation** | The planned write set held by a reservation-holding child, from admission until its attempt is `accepted`, `cleaned` or `superseded`. | REQ-19 |
| **Serialized composite** | A composite on which independence was disproved or the worktree probe failed; from then on its effective limit is 1 and new attempts run in the root worktree until it completes. | Original §10; REQ-14, REQ-49 |
| **Wave** | Informal name for the set of children active at the same moment; it has no branch, journal record or status. | Original §4 |
| **Leaf coordinator** | The per-attempt sub-agent of REQ-20. | Original §17 |
| **Workflow agent** | A fresh sub-agent dedicated to exactly one workflow invocation (REQ-21). | Original §17 |
| **Handoff** | The immutable JSON record passed from one workflow stage to the next (DM-6). | REQ-22 |
| **Root** | The Orchestrator of `/spec-run`. | `.ai/principles/domain.md:32` |
| **Episode key** | Spec 19's `episode_id` (19 DM-2). This spec defines no key of its own: DM-3 `repair_episode` holds that value and REQ-14 copies it into the next attempt. | REQ-54; 19 C-10 row 12, A-34 |
| **Slot** | In this spec always a concurrency slot of the effective limit (REQ-10, REQ-23). It is unrelated to spec 19's `local` and `escalated` repair slots (19 DM-8 `slots`), which this spec never names, except in the preserved original text of the Source section, where "attempt slot" is spec 19's sense. | REQ-10; 19 C-10 row 12, A-34 |

Rejected synonyms: "integration branch", "wave branch", "task branch" (no such branches exist);
"sub-PR" (children get no PR); "lock" for a reservation (no file lock is used); "retry" or
"attempt" for a spec 19 repair (a repair is not an attempt).

## Requirements

Component tags name the actor that implements the behaviour. Unless stated, a requirement
applies only to `/spec-run` tasks with `branch_model: per-composite`. Original identifiers keep
their subject; their original text is under Source. REQ-17, REQ-18, REQ-24 and REQ-26 are
restricted to the children of one composite (D-04). "Effective limit" is N, or 1 while
the composite is serialized. Stage names are those of DM-3.

### Shared state and accounting

- **REQ-01 Single writer.** WHILE a parallel run (N > 1) is executing, THE SYSTEM [root] SHALL
  be the only writer of every file under `.ai/` and of the composite journal, applying each
  delta returned by a coordinator or workflow agent sequentially, after re-reading the target
  section; workers' own progress blocks are included. Spec 16 review records
  (`<task>/verification/reviews/`) are files under `.ai/` and follow this rule: REQ-55 and REQ-56 state
  how the root writes them from a returned draft (D-05).
- **REQ-02 Attribution.** WHEN a child attempt reaches an end stage (`accepted`, `failed`,
  `blocked`, `check-failed`, `conflict` or `superseded`) for the first time, THE SYSTEM [root]
  SHALL write exactly one synthetic per-subtask run-log aggregate for that attempt through the
  existing helper path (`workflows/spec-run.md:45-47`), so concurrent attempts never share or
  duplicate an aggregate.
- **REQ-28 Worker context.** WHEN the root dispatches any agent for a child, THE SYSTEM [root]
  SHALL give it only that child's description path, its handoff, its worktree path (parallel
  mode), the absolute path of the root worktree's `.ai/` directory as read-only context and,
  under REQ-53, its context packet, and never another child's transcript, report or handoff.
- **REQ-53 Context packet.** WHERE spec 14's `packet` command is delivered, WHEN the root
  dispatches an execution or validation agent for a child, THE SYSTEM [root] SHALL build the
  agent's packet per 14 C-8 with `--work` set to the attempt's location (its worktree, or the
  root worktree when `worktree` is `null`), `--ai-dir` set to the root worktree's `.ai/`,
  `--base-commit` set to the attempt's `base_commit`, and `--role implementer` for execution
  workflows or `--role validator` for validation workflows, and pass that packet as the
  agent's context in addition to REQ-28's items; when `packet` exits non-zero (including
  14's `working-dir-mismatch`, 14 REQ-50), it dispatches without a packet as 14 REQ-40/REQ-41
  provide.
- **REQ-43 Tracked task records.** WHERE the repository tracks `.ai/` paths, WHEN the root is
  about to switch the root worktree from a child branch to its composite branch, is about to
  merge a child into the composite branch, or has applied the deltas of composite validation
  (before REQ-08 pushes), THE SYSTEM [root] SHALL commit every pending tracked `.ai/` change as
  `chore: update task records` on the branch then checked out, staging explicit paths under
  `rules/git-flow.md:156-165`. The switch that cuts the next stack branch makes no such commit:
  pending records carry over and are staged with the next commit as today, and the next stack
  branch is cut from the composite tip that includes the post-validation record commit, which
  is the tip REQ-08 pushes.

### Branches and integration

- **REQ-06 Composite branch.** WHEN the stack reaches a composite whose block has no
  `branch:` and whose `children:` list is non-empty, THE SYSTEM [root] SHALL create the
  composite branch from the reviewed tip of the previous top-level stack branch (the default
  branch for the first) and record `branch:`, `base_branch:`, `base_commit:`, `commits:`
  (empty) and `pr: none` in the composite block before any child starts.
- **REQ-44 Empty composite.** IF a composite's `children:` list is empty or lists an id with no
  plan row or leaf block, THEN THE SYSTEM [root] SHALL stop before creating its branch with
  `**stop**: "Composite <id> has no runnable children. Re-run /pd-decompose."`.
- **REQ-30 Child branch.** WHEN the root starts a child attempt, THE SYSTEM [root] SHALL create
  the attempt's child branch (Terminology) at the composite branch's current tip SHA and record
  that SHA as the attempt's `base_commit` in the journal and in the child block, using the C-2
  form for the attempt's location: the root worktree when the effective limit is 1, otherwise a
  new worktree at the DM-4 path.
- **REQ-07 Merge form.** WHEN a child attempt is ready to integrate, THE SYSTEM [root] SHALL
  merge it from the root worktree with the composite branch checked out, using exactly
  `git merge --no-ff -m "Merge branch '<child-branch>' into <composite-branch>" <child-branch>`
  as its own Bash call, never squash, rebase or fast-forward.
- **REQ-03 Post-merge checks.** WHEN a merge commit for a child attempt is created, THE SYSTEM
  [root] SHALL run in the root worktree, on that commit's tree, the recorded `test_command`
  (DM-3) of every child already accepted in the composite and of the merged child, in
  `## Subtasks` row order and skipping `null` commands, and accept the integration only if
  every command exits 0.
- **REQ-35 Post-merge failure.** IF a post-merge check fails, THEN THE SYSTEM [root] SHALL keep
  the merge commit, set the attempt stage `check-failed` with the failing command, set the
  composite block `blocker:` to that command and child, admit and integrate no further child
  of that composite, and stop the run after active children of that composite acknowledge a
  stop (REQ-04 procedure).
- **REQ-45 Post-merge recovery.** WHEN a run resumes a composite whose block `blocker:` the
  owner has set back to `none` and whose child is `check-failed`, THE SYSTEM [root] SHALL rerun
  the REQ-03 command list on the current composite tip and set that attempt `accepted` (then
  REQ-39) if every command exits 0, or keep `check-failed` and stop again otherwise.
- **REQ-36 Merge conflict.** IF `git merge` reports a conflict, THEN THE SYSTEM [root] SHALL run
  `git merge --abort`, record the conflicting paths and stage `conflict` in the journal, keep
  the child branch and worktree, and treat the conflict as disproved independence (REQ-14).
- **REQ-39 State recording.** WHEN an integration is accepted, THE SYSTEM [root] SHALL record
  `merge_commit: <sha>` in the child block, append `<sha> merge: <child domain name>` to the
  composite block's `commits:`, and only then set the journal stage `accepted`.
- **REQ-41 Test-first per child.** THE SYSTEM [root] SHALL keep, on every child branch, the
  commit sequence `git-flow → ## Commits` prescribes for the child's `atomic-tests:` mode: a
  `test:` commit before the implementation commit for `red` and `pinned`, a single
  implementation commit for `n-a`, and the `pre-TDD task, TDD step skipped` note without a
  retroactive RED for a legacy in-progress block.
- **REQ-46 Test command record.** WHEN `/pae-tests` reaches `red` or `pinned` for a child, THE
  SYSTEM [`/pae-tests`] SHALL report the exact command that observed the result, and the root
  SHALL record it as the notes line `tdd: command — <command>` in the child block and as the
  attempt's `test_command` in the journal.

### Publication and cleanup

- **REQ-08 One PR per composite.** WHERE `--allow-pr` is given, WHEN a composite reaches
  `reviewed`, THE SYSTEM [root] SHALL push only the composite branch and open one draft PR whose
  base is the previous top-level stack branch (the default branch for the first), or reuse the
  PR already recorded in the composite block's `pr:`, and record it there; child blocks keep
  `pr: none` and child branches are never pushed.
- **REQ-33 PR body.** WHEN the root builds a composite PR body, THE SYSTEM [root] SHALL include
  the composite's Goal and integration Acceptance Criteria, one stack-position line naming
  predecessors by branch, and one section per accepted child with its domain name, Goal,
  Acceptance Criteria, test level and `test:` commit SHA (or the `n-a` justification), with no
  pipeline identifier (`rules/git-flow.md:129-154`).
- **REQ-31 Cleanup.** WHEN an attempt's stage is `accepted` and its `cleanup.failure` is null,
  THE SYSTEM [root] SHALL first run `git worktree remove <path>` (when the attempt has a
  worktree; never `--force`), then `git update-ref -d refs/heads/<child-branch> <attempt tip>`,
  as separate Bash calls, set stage `cleaned` after both succeed, and on any failure, hook ask
  or hook deny keep the branch and worktree, record the reason in `cleanup.failure`, never
  retry or rephrase it in this or a later run, and continue.
- **REQ-32 Deletion verifier.** WHEN the git-rails hook evaluates an R22 or R23 deletion, THE
  SYSTEM [hook] SHALL grant the exception only for `git update-ref -d refs/heads/<b> <sha>`
  whose ref, expected SHA and repository pass every check of `## Contracts & Interfaces →
  ### C-4`, and otherwise keep the shipped `ask` decision.
- **REQ-47 Journal retention.** WHEN the task's Execution phase is complete and every attempt
  is `cleaned` or `superseded`, THE SYSTEM [root] SHALL delete the task's composite journal and
  its handoff directory after the Step 8 report; otherwise it keeps them.

### Composite validation

- **REQ-12 Single composite validation.** WHEN every child of a composite has its latest
  attempt `accepted` or `cleaned` and plan status `reviewed`, THE SYSTEM [root] SHALL check out
  the composite branch in the root worktree and dispatch one fresh validation agent to run
  `/phase-composite-validation` once for that composite tip, whose integration surface is
  `git diff --name-only <composite base_commit>..<composite tip> -- . ':(exclude).ai'` (a full
  review; spec 16 scope `full-integration`, A-28).
- **REQ-40 Close signal.** WHILE a task is `per-composite`, WHEN `/pav-close` finds every
  sibling child complete, THE SYSTEM [`/pav-close`] SHALL return the signal
  `composite-ready: <composite id>` to its caller instead of invoking
  `/phase-composite-validation`.

### Planning and parallel mode

- **REQ-29 Flag parsing.** WHEN `/spec-run` is invoked, THE SYSTEM [root] SHALL resolve N as 1
  without `--parallel`, 2 for `--parallel` not followed by a value, and the value for
  `--parallel <v>` where `<v>` matches `^[1-9][0-9]*$`, and stop with
  `**stop**: "Invalid --parallel value '<v>': use a positive integer."` before preflight writes
  anything for any other value.
- **REQ-48 Per-leaf tasks.** IF N > 1 and the task's `branch_model` is or resolves to
  `per-leaf` (DM-1), THEN THE SYSTEM [root] SHALL stop before any write with
  `**stop**: "Parallel execution requires the per-composite branch model; this task records
  per-leaf branches. Re-run without --parallel."`.
- **REQ-10 Parallel limit.** WHILE a composite is executing, THE SYSTEM [root] SHALL keep the
  number of its active children at or below the effective limit.
- **REQ-25 Capability preflight.** WHEN N > 1, THE SYSTEM [root] SHALL, before Discovery or any
  branch, require the capability records `sub-agents`, `agent-messaging`, `git`, `worktrees`
  and `concurrent-sub-agents` with `state: yes` through spec 13's `/spec-run` preflight, which
  alone defines the stop for a missing or unknown capability, its message and the next step it
  names (13 REQ-37; key names and record form follow 13's capability contract, 13 DM-4),
  and then verify that `ORCHESTRAIL_HOME` is set, that `python3 "$ORCHESTRAIL_HOME/scripts/composite_run.py" --version`
  prints `{"version": "1"}` under Python ≥ 3.11, and that `.ai/context/runbook.md → ## Commands`
  has a non-placeholder `test:` entry (`templates/.ai/context/runbook.md:10-15`), and otherwise
  stop with
  `**stop**: "Parallel execution unavailable: <missing items>. Re-run without --parallel for
  sequential execution."` for these non-capability items, in both cases without any write.
- **REQ-49 Worktree probe.** WHEN the root creates a worktree (N > 1), THE SYSTEM [root] SHALL
  run the runbook `test:` command in that worktree and in the root worktree, both at the
  attempt's `base_commit`, before dispatching any agent, and IF the exit codes differ or the
  probe leaves the worktree with tracked changes, THEN supersede the attempt and mark the
  composite serialized with reason `worktree-probe`.
- **REQ-38 Dry run.** WHERE `--dry-run` is combined with `--parallel`, THE SYSTEM [root] SHALL
  report the resolved N, the preflight result and, for an existing plan, each composite's
  `### Parallel Safety` rows and the children `admit` (with no journal) would start first,
  without creating any branch, worktree, journal or state write.
- **REQ-09 Independence record.** WHEN `/pd-decompose` writes a plan containing a composite,
  THE SYSTEM [`/pd-decompose`] SHALL render one `### Parallel Safety` row per child (DM-5) from
  that child's spec 20 DM-8 object, with `Parallel-safe: no` whenever DM-8 `disqualifiers` is
  non-empty, the write set is not a complete explicit file list, the child needs an exclusive
  resource, an `## Execution Strategy` ordering constraint names it (under spec 20 REQ-13 and
  REQ-35 such ordering is a `Depends On` edge, so this clause matters only for older plans), or
  any independence condition is unproven.
- **REQ-52 Design reconciliation.** WHEN `/pd-design` finishes on a plan containing a composite,
  THE SYSTEM [`/pd-design`] SHALL re-render every `### Parallel Safety` row from the child's
  current spec 20 DM-8 object (whose interface contracts `/pd-design` has just resolved) and
  apply REQ-09's `Parallel-safe` rule again, changing no row of a child that has started in
  the sense of spec 20 REQ-24.
- **REQ-05 Independence predicate.** THE SYSTEM [helper and root] SHALL treat two children of
  one composite as independent only when both rows say `Parallel-safe: yes`, both planned
  write sets are complete and disjoint, neither produces an interface the other produces or
  consumes, and neither depends on the other directly or transitively.
- **REQ-17 Composite graph.** WHEN a parallel run reaches a composite, THE SYSTEM [root] SHALL
  schedule that composite's children from the dependency graph of its `## Subtasks` rows,
  treating the composite as the integration gate and running no child of any other composite
  or top-level leaf concurrently.
- **REQ-51 Sequential children.** WHILE N = 1, THE SYSTEM [root] SHALL run a composite's
  children one at a time in `## Subtasks` row order (the existing dependency-compatible stack
  order), and IF a child's atomic validation returns NEEDS WORK or the child is blocked, THEN stop
  the run as today (`workflows/spec-run.md:297-299`), setting the attempt `failed` or `blocked`
  and the child block `blocker:` as REQ-24 describes.
- **REQ-18 Admission.** WHILE N > 1, WHEN a child is considered for dispatch, THE SYSTEM [root]
  SHALL admit it only under the C-3 `admit` rules: every prerequisite inside the composite has its latest
  attempt `accepted` or `cleaned` and plan status `reviewed`, every prerequisite outside it has
  plan status `reviewed`, it is independent (REQ-05) of every reservation-holding child, or, for
  an exclusive candidate, satisfies admit rule 3, the active count stays within the effective
  limit, and no earlier candidate is a barrier.
- **REQ-19 Reservation.** WHILE a child is reservation-holding (Terminology), THE SYSTEM [root]
  SHALL hold its planned write set as its reservation and admit no other child whose planned
  write set intersects it.
- **REQ-23 Refill and slot retention.** WHEN an attempt leaves the active stages, THE SYSTEM
  [root] SHALL release its slot and rerun admission, and SHALL release its reservation only
  when the attempt is `accepted`, `cleaned` or `superseded`.
- **REQ-11 Overlap detection.** WHILE N > 1, WHEN a workflow agent of a child returns, and
  again immediately before that child's merge, THE SYSTEM [root] SHALL compute the child's
  actual write set (C-3 `check-merge`) and treat any path outside its reservation (including
  any `.ai/` path) or inside another active, `accepted` or `cleaned` child's actual write set as
  disproved independence.
- **REQ-14 Serialization.** WHEN independence is disproved in a composite, THE SYSTEM [root]
  SHALL record `serialized` with the reason and paths in the journal, admit no new child of that
  composite, send every active coordinator a stop and wait until each acknowledges or is
  confirmed gone (REQ-27), then integrate in row order each `validated` attempt whose
  `check-merge` verdict is `ok`, set every other non-accepted attempt of the composite
  `superseded`, and run each remaining child as a new attempt from the current composite tip in
  the root worktree with fresh agents of the effective-limit-1 model (C-1 Step 4: one
  Implementer, one Validator), one at a time, until the composite completes.
- **REQ-04 Broad stop.** IF a critical finding, an Invariant or Off-limits violation, a
  class-B question, a composite-promotion tripwire or any other condition of
  `rules/orchestration.md:180-187` occurs during a parallel run — except `atomic-tests: failed`
  and a worker blocker of one child, which REQ-24 isolates (DM-3 `tests-failed`, `blocker`) —
  THEN THE SYSTEM [root] SHALL
  admit no new child anywhere, send every active coordinator a stop, record each
  acknowledgement with the last verified checkpoint, preserve all branches and worktrees, and
  stop the run. A worker already dispatched, a REQ-54 repair worker included, is not
  interrupted: its running agent finishes (C-6 row 8), no further attempt, repair attempt or
  validation recheck starts, its result is recorded through spec 19's `outcome` step and an
  open episode stays open (19 C-10 row 12), and the attempt keeps the journal stage it had at
  the stop for the resume (REQ-27).
- **REQ-24 Failure isolation.** WHILE N > 1, IF a child's atomic validation returns NEEDS WORK,
  its `/pae-tests` reports `atomic-tests: failed`, or a child is blocked, THEN THE SYSTEM [root] SHALL set its attempt `failed` or `blocked` with
  its `blocked_reason`, write `blocker: <blocked_reason>: <one-line detail>` in the child block,
  keep the attempt unintegrated with its branch, worktree and reservation, keep admitting
  independent children of the same composite, and stop the run with that child reported once no
  child of the composite is active or admissible.
- **REQ-54 Repair policy.** WHERE spec 19's repair policy is active for the run (19
  REQ-01 not applying), IF a child's atomic validation returns NEEDS WORK, THEN THE SYSTEM [root]
  SHALL run 19's repair loop (19 C-5) for that child instead of the REQ-24 or REQ-51 stop: the
  attempt stays `dispatched` with its concurrency slot and reservation and records 19's episode in
  `repair_episode`; a child whose attempt is `merged`, `accepted` or `cleaned` is never repaired
  (integration failures follow REQ-35/REQ-45 and the composite-validation fix siblings of E-31,
  `workflows/phase-composite-validation.md:89-143`); merged siblings are not touched; an accepted
  repair sets the attempt `validated` and then follows REQ-07, REQ-11, REQ-36 and REQ-14
  unchanged; a REQ-04 broad stop starts no further repair attempt or recheck and lets a repair
  worker already dispatched finish, as REQ-04 states; when REQ-14 supersedes an attempt with an
  open episode, the episode key is copied into the next attempt's `repair_episode` (19 C-10:
  an episode survives serialization, worktree change and new workers); and a repair loop that
  ends without acceptance applies the REQ-24 or REQ-51 stop. With N > 1 the `/pae-repair`
  invocation is one workflow invocation: the root spawns one fresh agent for it (REQ-21), the
  agent returns its leaf-block writes as deltas (REQ-01), the root commits 19's checkpoints and
  builds a DM-6 handoff with stage `repair`, and the coordinator then requests a fresh
  validation phase (C-6 row 6). Without the active policy, REQ-24 and REQ-51 apply exactly as
  written.
- **REQ-55 Review records.** WHERE spec 16's `record` command is available (16 C-1), WHILE
  N > 1, WHEN a review agent of the run returns its final report (the `/pav-check` workflow
  agent of a child attempt, REQ-21, the Validator of a child of a serialized composite, which uses
  the effective-limit-1 model and has no coordinator or phase agent, or the composite validation
  agent, REQ-12), THE SYSTEM [root]
  SHALL be the only invoker of `record`: the agent runs `prepare` and `run` but never `record`,
  never writes under `<task>/verification/` and returns its review draft in the report's
  `review` object (C-6 row 11). The root SHALL write the returned DM-7 draft object of spec 16
  to `<task>/verification/drafts/<scope key>-attempt-<k>.json` of the root worktree's task
  directory, and run `record --draft` on it with the options the agent passed to `prepare`, only
  after confirming that `--work` names the attempt's location and `--task` and `--ai-dir` name
  the root worktree's task directory and `.ai/`, before it applies any other delta of that
  report and before the root's checkpoint commit or the next dispatch for the attempt. When
  `record` publishes, the root SHALL apply the report's verdict and notes deltas and then append,
  as the last entry, the 16 DM-8 entry `verification: review <scope key> <step> #<seq> <scope>
  sha256:<file hex>` built from the `record` result (`seq`, `file_sha256`); an agent never writes
  that entry. WHEN the report carries `draft: null` with a `none_reason`, THE SYSTEM [root]
  SHALL append the DM-8 entry `verification: review <scope key> <step> none — <reason>` instead
  and write no record. At N = 1 this requirement does not apply: the Validator runs `record`
  itself as 16 C-4 states.
- **REQ-56 Refused or unusable review draft.** WHERE REQ-55 applies, IF the `review` object is missing, is not JSON of the C-6 row 11 form, or
  names a different `--work`, `--task` or `--ai-dir` (an unusable draft), or `record` exits 1
  (refused), THEN THE SYSTEM [root] SHALL write no record and apply none of that report's
  verdict, `verification:` entry or other review deltas, and SHALL spawn the same review role
  once more as a fresh agent whose message carries the refusal `reasons` (the correction, spec
  16's `Record:` rule), replying to a requesting phase agent per C-6 row 12; IF the correction's
  draft is also unusable or refused, or `record` exits 2, 3 or 4, THEN the root SHALL spawn the
  review role one further time with `"helper": "off"`, whose full review without the helper
  returns `draft: null` with `none_reason: helper-error` (16 DM-8), and when that agent also
  returns no usable report the attempt is `blocked` with reason `record-failed` (REQ-24); for
  the REQ-12 composite validation agent, which has no attempt, the root writes
  `blocker: record-failed: <one-line detail>` in the composite block and stops the run.
- **REQ-50 Owner-cleared resume.** WHEN a run resumes a child whose latest attempt is `failed`
  or `blocked` and whose block `blocker:` the owner has set to `none`, THE SYSTEM [root] SHALL,
  if `reconcile` returns `none` for it, set the attempt back to `dispatched` and restart it with
  fresh agents in its recorded location at the stage the DM-3 resume table gives for its
  `blocked_reason`, counting it as active; while `blocker:` is not `none` the attempt stays as
  it is.

### Agents in parallel mode

- **REQ-20 Leaf coordinator.** WHEN a child attempt is admitted with an effective limit above 1
  (N > 1 and its composite not serialized), THE SYSTEM [root]
  SHALL spawn one fresh leaf coordinator for that attempt only, record its agent identity in
  the journal, and exchange the C-6 messages with it.
- **REQ-21 Workflow agents.** WHEN a phase or workflow agent of a child attempt admitted under
  REQ-20
  requests an invocation (C-6), THE SYSTEM [root] SHALL spawn a fresh agent for that single
  invocation whose identity differs from every other agent of the run and record the identity
  in the journal; the sequence is `/phase-atomic-execution` (requesting `/pae-tests`,
  `/pae-implement`, `/pae-finalize`) then `/phase-atomic-validation` (requesting `/pav-check`,
  `/pav-propose --batch`, `/pav-close`).
- **REQ-22 Verified handoff.** WHEN a workflow agent of a child returns, THE SYSTEM [root] SHALL
  commit the checkpoint its report represents (if any), build the handoff (DM-6) from that
  report and the worktree, record its digest in the journal, run C-3 `check-handoff` on it
  immediately before dispatching the next workflow, and dispatch the next workflow with only that
  handoff when the verdict is `ok`; a missing report, a `stale` verdict or a report whose
  test files differ from the frozen set blocks the next workflow and sets the child `blocked`.
- **REQ-27 Agent recovery.** WHEN a parallel run resumes, THE SYSTEM [root] SHALL, for every
  attempt in stage `dispatched`, send its recorded coordinator a status message and classify the
  outcome as `live` (the coordinator answers with its current stage), `gone` (the harness reports
  the agent identity unknown or finished) or `unknown` (any other outcome); it redispatches only
  a `gone` attempt whose `reconcile` action is `none`, from its last verified checkpoint; for a
  `live` attempt it sends the C-6 stop (row 8), waits for `stopped`, then treats the attempt as
  `gone`; and it sets an `unknown` attempt, or a `gone` one with `inspect-worker`, `blocked` with
  reason `liveness-unknown` or `uncommitted-work`.

### Recovery, migration, measurement

- **REQ-13 Journal and reconciliation.** WHEN `/spec-run` resumes a `per-composite` task, THE
  SYSTEM [root] SHALL validate the composite journal and reconcile every attempt against the
  repository with the C-3 `reconcile` table (running the helper when it is available, otherwise
  applying the same table itself) before any new git operation, acting only on the resulting
  action.
- **REQ-42 Atomic journal write.** WHEN the root changes the journal, THE SYSTEM [root] SHALL
  write the complete new document to `<journal>.tmp` in the same directory and rename it over
  the journal, writing the stage that precedes a git operation before running that operation.
- **REQ-16 Branch model selection.** WHEN `/spec-run` reaches Step 3 for a task whose
  `state.md` has no `branch_model:`, THE SYSTEM [root] SHALL write `branch_model: per-leaf` if
  any block already records `branch:`, otherwise `branch_model: per-composite`, and never change
  an existing value.
- **REQ-34 Restack.** WHEN `/restack` runs on a `per-composite` task, THE SYSTEM [`/restack`]
  SHALL treat only composite blocks and top-level leaf blocks with `branch:` as stack branches,
  skip child blocks, record a replayed composite branch's new own-range commits in its
  `commits:` as for any branch, append to every child block of that composite the note
  `restack <date>: merge history linearized; child commit and merge hashes superseded`, and
  report that the composite's merge commits were linearized.
- **REQ-37 Promotion.** WHEN a leaf with a recorded `branch:` is promoted to a composite by the
  approved Composite Promotion Protocol in a `per-composite` task, THE SYSTEM [root] SHALL keep
  that branch, its `base_branch:`, `base_commit:` and `commits:` as the composite block's git
  fields and start its children from its current tip.
- **REQ-26 Run measurement.** WHEN a run with any composite ends, THE SYSTEM [root] SHALL report,
  per composite, the requested N, serialization events with reasons, and the output of C-3
  `measure`, printing `not measured` for each null value and claiming no speedup.
- **REQ-15 Equivalence.** WHERE an owner-approved spec 09 `composite` golden run exists for
  both `--parallel 1` and `--parallel 2`, THE SYSTEM [`scripts/check-composite-run.py`; spec 09
  defines no comparison between two runs' projections] SHALL compare their normalized
  structural assertions (the two spec 09 expected projections) and treat any difference other than aliased hashes, branch
  names and timestamps as a defect.

## Data Model

### DM-1 Task `state.md` top-of-file field (new)

`branch_model: per-leaf | per-composite`, placed after `flow:`. Written once by `/spec-run`
Step 3 (REQ-16). Reader rule (backward compatibility, P3): absent and any block with `branch:`
→ `per-leaf`; absent and no `branch:` → not yet chosen; ordinary manual runs never write or
require it. Canonical definition goes in `rules/workflow-globals.md → ## Canonical Status
Formats`.

### DM-2 Progress block fields (existing blocks, additive fields)

| Block | Field | Type | Writer | Rule |
|---|---|---|---|---|
| Composite | `branch:` | branch name | root (REQ-06, REQ-37) | Written once; only `/restack` rewrites |
| Composite | `base_branch:` | branch name | root | Previous top-level stack branch or default branch |
| Composite | `base_commit:` | 40/64-hex SHA | root | Written once, never recomputed |
| Composite | `commits:` | `<sha> merge: <child domain name>` and `<sha> chore: update task records`, comma-separated | root (REQ-39, REQ-43) | Appended per commit the root makes on the composite branch |
| Composite | `pr:` | `#N draft \| #N ready \| none` | root (REQ-08) | — |
| Child | `branch:` | child branch of the latest attempt | root (REQ-30) | Updated when a new attempt starts; older attempts stay in the journal |
| Child | `base_branch:` | composite branch | root | — |
| Child | `base_commit:` | SHA | root | The latest attempt's base |
| Child | `commits:` | existing format | root | Commits of the latest attempt, including every commit the root makes on the child branch (a REQ-43 `chore: update task records` commit included, E-43); the last listed commit is the attempt `tip`, which spec 09 SA-10 compares with the merge's second parent |
| Child | `merge_commit:` | SHA or `none` | root (REQ-39) | New field; `none` until accepted |
| Child | `pr:` | always `none` | root | — |
| Child | `notes:` line `tdd: command — <command>` | text | root (REQ-46) | Protected `tdd:` line; absent for `n-a` and legacy |

All new fields are protected like the existing git fields (`rules/workflow-globals.md:233-236`)
and listed in `rules/workflow-reference.md → ## Protected Sections Contract`. Status
vocabularies are unchanged; `rollup` and `integration-validation` keep their meaning.

### DM-3 Composite journal (new)

Lifecycle: the root creates the journal (REQ-42 write) immediately before running the first
REQ-06 command of the task, and deletes it per REQ-47. An absent journal file means "no
composite started": `admit`, `reconcile` and `measure` treat it as empty, `validate` reports
`journal-missing`.

Path `<git-common-dir>/orchestrail-composite/<sha256 hex of UTF-8 canonical task_path>.json`;
regular file ≤ 1 MiB, strict UTF-8 JSON without duplicate keys or NaN/Infinity; extra fields
allowed. Every SHA is a full lowercase 40- or 64-hex object name; every timestamp is
`YYYY-MM-DDTHH:MM:SSZ` copied from `date -u +%Y-%m-%dT%H:%M:%SZ` output or `null`.

```json
{
  "schema_version": 1,
  "repository_common_dir": "/abs/canonical/.git",
  "task_path": "/abs/canonical/.ai/tasks/todo/task-NN-slug",
  "branch_model": "per-composite",
  "requested_parallel": 2,
  "composites": [
    {
      "id": "T-03",
      "branch": "feat/oauth-login",
      "base_branch": "feat/oauth-token-service",
      "base_commit": "<sha>",
      "tip": "<sha>",
      "serialized": null,
      "children": [
        {
          "id": "T-03a",
          "attempts": [
            {
              "attempt": 1,
              "branch": "feat/oauth-login--token-route",
              "worktree": "/abs/.git/orchestrail-worktrees/<task-key>/feat-oauth-login--token-route",
              "base_commit": "<sha>",
              "tip": "<sha>",
              "stage": "dispatched",
              "test_mode": "red",
              "test_command": "python3 -m pytest tests/test_token_route.py",
              "agents": {"coordinator": "<agent id>", "workflows": [{"workflow": "pae-tests", "agent": "<agent id>"}]},
              "handoffs": [{"stage": "tests", "digest": "<sha256 hex>"}],
              "actual_write_set": ["src/token_route.py", "tests/test_token_route.py"],
              "dispatched_at": "2026-11-20T10:00:00Z",
              "ended_at": null,
              "merge": null,
              "cleanup": null,
              "blocked_reason": null
            }
          ]
        }
      ]
    }
  ]
}
```

- `task-key` = the first 16 hex characters of the journal's file-name digest.
- Composite `tip` is the composite branch SHA after the root's last commit or merge on it.
- `worktree` is `null` when the attempt runs in the root worktree (effective limit 1).
- `serialized` is `null` or `{"at": <timestamp>, "reason": "overlap|scope-exceeded|conflict|interface|worktree-probe", "paths": [...], "children": [ids]}`.
- `ended_at` is set when the attempt first reaches `accepted`, `failed`, `blocked`,
  `check-failed`, `conflict` or `superseded`, and cleared when REQ-50 resumes it.
- `unexpected_messages` is an integer count of C-6 messages that matched no expected row;
  optional, absence reads as 0.
- `repair_episode` is `null` or spec 19's episode key (its `episode_id`) while REQ-54 runs a
  repair for the attempt; it is set only when 19's repair policy is active for the run, is
  optional, and absence reads as `null`; without the policy it is never written and REQ-24 and
  REQ-51 apply as written.
- `blocked_reason` is `null` or one of `needs-work`, `tests-failed`, `blocker`,
  `handoff-stale`, `liveness-unknown`, `uncommitted-work`, `worktree-not-writable`,
  `record-failed` (REQ-56).
- `merge` is `null` or `{"expected_target": <composite tip before merge>, "commit": <sha|null>, "tree": <sha|null>, "conflict_paths": [...], "checks": "pass|fail|null", "failed_command": <text|null>, "check_failures": <int>}`; `check_failures` counts failed REQ-03/REQ-45 runs.
- `cleanup` is `null` or `{"worktree_removed": bool, "branch_deleted": bool, "failure": <text|null>}`.
- `test_mode` is `red | pinned | n-a | legacy`; `test_command` is `null` only for `n-a` and `legacy`.
- `requested_parallel` is the N resolved by the latest invocation (REQ-29); a resumed run
  overwrites it. Existing attempts keep their recorded location; no worktree is created while
  the effective limit is 1.

**Stages (journal vocabulary, one anchored line in the workflow):** `branched` | `dispatched` |
`validated` | `merge-intent` | `merged` | `accepted` | `cleaned` | `check-failed` | `conflict` |
`failed` | `blocked` | `superseded`.

| From | To | Trigger |
|---|---|---|
| — | `branched` | REQ-30 branch (and worktree) created; written before the git command per REQ-42 |
| `branched` | `dispatched` | First agent spawned |
| `dispatched` | `validated` | Atomic validation `complete` applied to state |
| `dispatched` | `failed` | NEEDS WORK (`needs-work`) or `atomic-tests: failed` (`tests-failed`) |
| `dispatched` | `blocked` | Worker blocker, stale handoff, liveness unknown, uncommitted work of a gone worker, worktree not writable |
| `failed` / `blocked` | `dispatched` | REQ-50 owner-cleared resume |
| `validated` | `merge-intent` | `merge.expected_target` recorded before `git merge` |
| `merge-intent` | `merged` | Merge commit created; `merge.commit` and `merge.tree` recorded |
| `merge-intent` | `conflict` | REQ-36 after `git merge --abort` |
| `merged` | `accepted` | REQ-03 pass and REQ-39 state recorded |
| `merged` | `check-failed` | REQ-35 |
| `check-failed` | `accepted` | REQ-45 rerun passes |
| `accepted` | `cleaned` | REQ-31 both cleanup steps done |
| `branched`, `dispatched`, `validated`, `conflict`, `failed`, `blocked` | `superseded` | REQ-14 serialization (or REQ-49 probe failure) gives the child a new attempt |

Terminal: `cleaned` and `superseded`. `accepted` with a cleanup failure stays `accepted`.

Resume stage after an owner-cleared `blocker:` (REQ-50):

| `blocked_reason` | Restart at |
|---|---|
| `needs-work`, `record-failed` | Atomic validation, fresh agents, on the current child tip (owner fixes, if any, are commits on the child branch) |
| `tests-failed` | `/pae-tests` |
| `handoff-stale` | Rebuild the handoff from the last root checkpoint commit, then the workflow it blocked |
| `liveness-unknown`, `uncommitted-work`, `blocker` | The first workflow after the last root checkpoint commit (`/pae-tests` when there is none) |
| `worktree-not-writable` | Not resumable; serialization supersedes it |

### DM-4 Worktree location (new)

`<git-common-dir>/orchestrail-worktrees/<task-key>/<child-branch with "/" replaced by "-">`.
Inside the common directory the worktree is invisible to the root worktree's `git status` and is
under the registered project root, so the git-rails hook governs commands run there (the
registry matches by directory prefix, `hooks/git_rails.py:330`) (verified
with git 2.53.0 in a disposable repository on 2026-11-13: `git worktree add` there succeeded,
the root status stayed clean, and git refused `branch -d` while the worktree existed). Tools
that skip `.git` path segments, missing untracked dependencies and edit tools that refuse paths
under `.git` are not verified; REQ-49's probe and E-36 cover them by serializing the composite.

### DM-5 `plan.md → ## Decomposition Decisions → ### Parallel Safety` (new)

```
### Parallel Safety

| Child | Composite | Parallel-safe | Write set | Interfaces | Independence evidence |
|-------|-----------|---------------|-----------|------------|-----------------------|
| T-03a | T-03 | yes | src/token_route.py, tests/test_token_route.py | produces: token-route; consumes: token-schema | disjoint files; no shared schema; no dependency edge; no ordering constraint |
```

- One row per child of every composite; written by `/pd-decompose` (REQ-09), present even when
  every row is `no`. Absent subsection or missing row reads as `no` (backward compatibility).
- `Write set`: comma-separated repository-relative file paths; a rename is `old -> new`; a
  directory, glob or `—` makes the set incomplete and the row must be `no`.
- `Interfaces`: `produces: <names>; consumes: <names>` with domain names; `—` means none.
- A child whose tests or implementation need an exclusive resource (a fixed port, a shared
  database, an external service, a host-exclusive benchmark) is `no`, and the evidence names the
  resource. A child named by an `## Execution Strategy` ordering constraint other than
  `Depends On` is `no`. The Execution Strategy sentence "composites execute their children in
  listed order" (`workflows/pd-decompose.md:127-128`) is replaced by "composite children
  integrate in listed order; `### Parallel Safety` states which may run concurrently".
- `Independence evidence`: one clause for each condition of REQ-05 and for resources.
- Source of every row: the child's spec 20 DM-8 object (one per composite child; 20 DM-8 maps
  each field onto these columns). DM-8 carries no yes/no value: this spec renders the table,
  decides `Parallel-safe` (REQ-09) and owns the REQ-05 predicate. `/pd-design` re-renders the
  rows after resolving interface contracts (REQ-52).
- Integration order is the child row order of `## Subtasks`; dependencies stay in `Depends On`.
- Original fields `packet_digest` and `integration_checks` are not columns: the packet belongs to
  spec 14 and the integration checks are the composite description's Acceptance Criteria.

### DM-6 Handoff (new, parallel mode)

One JSON object per completed workflow stage, built by the root from the returning agent's report
and the worktree after the root's checkpoint commit, carried in the root's message to the next
agent, and stored by the root under `<git-common-dir>/orchestrail-composite/handoffs/<task-key>/<child>-<attempt>-<stage>.json`.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | — |
| `child`, `attempt`, `stage` | text, int, `tests \| implement \| finalize \| check \| propose \| close \| repair` | Identity (`repair`: REQ-54) |
| `worktree`, `branch`, `base_commit` | path, text, SHA | Child attempt |
| `candidate_commit` | SHA | Worktree HEAD after the root's checkpoint commit |
| `description_path` | path | The child's `description.md` |
| `ac_ids` | list of text | Acceptance Criteria covered |
| `allowed_paths` | list of paths | The reservation |
| `test_mode`, `test_command` | as DM-3 | — |
| `observed` | `{"exit_code": int or null, "label": text or null, "failing_tests": [...]}` | RED, pinned or GREEN observation; see the spec 17 mapping below |
| `test_files` | `{path: sha256}` | Frozen test set identity |
| `previous_digest` | sha256 hex or `null` | Chain link |

The digest is SHA-256 over the object serialized with sorted keys, `","`/`":"` separators and
UTF-8. Handoffs pass between child workflows (`/pae-tests` → `/pae-implement` → `/pae-finalize`
→ `/pav-check` → `/pav-propose` → `/pav-close`); phase agents relay them (C-6) and produce none.
Once spec 17 is delivered, test commands run through its output store, one store shared by the
root and every child worktree (17 REQ-07), safe under concurrent use (17 REQ-11, REQ-12); `observed.exit_code` is 17's DM-3 `exit_code`
only when 17's outcome `kind` is `exit`, and `null` otherwise, with `observed.label` set from
17's outcome `label` (kinds `signal`, `interrupted`, `timeout`, `launch-error`). Before 17,
`label` is `null` and `exit_code` is the shell's exit status.

Spec 15 does not carry the DM-6 object: when 15 is delivered, its attempt record carries the
digest of the handoff given to the workflow as `input_handoff_digest`, and its receipt carries
the digest of the handoff the root builds after that checkpoint as `output_handoff_digest`
(15 REQ-41); the object itself exists only in the file above. For stage `repair` (REQ-54) no
receipt exists (15 C-10 row 12), so no `output_handoff_digest` is recorded for it (the field,
where 15's record has it, stays `null`), while `input_handoff_digest` follows 15 REQ-41 as for
every other stage; no rule of this spec requires a receipt for a repair, and the root records
the handoff digest in the journal `handoffs` list as for any stage.

### Migration impact

No existing file is migrated. Tasks with recorded per-leaf branches stay `per-leaf` (REQ-16).
Journals and worktrees live only in the git common directory and are never committed.

## Contracts & Interfaces

### C-1 `/spec-run` invocation (changed)

`/spec-run <path-to-spec> [--allow-pr] [--dry-run] [--parallel [N]]` — N per REQ-29. The run-start
`--flags` value includes `--parallel N` as passed. Stops added: invalid value (REQ-29),
preflight unavailable (REQ-25), per-leaf task with N > 1 (REQ-48). A resumed run uses the N
passed to that invocation and repeats the preflight when N > 1. Step changes:

| Step | Change |
|---|---|
| Step 0 | Parse `--parallel`; N > 1 preflight; for `per-composite` tasks validate the journal and run `reconcile` before any other action (REQ-13) |
| Step 3 | Write `branch_model:` (REQ-16); the stack plan prints a composite as one stack entry with its children indented as temporary branches |
| Step 4 | Composite: REQ-44, REQ-06, then children per REQ-30/REQ-07/REQ-03/REQ-39/REQ-31; at effective limit 1 the existing one-Implementer two-checkpoint handoff runs on the checked-out child branch and the Validator receives `git diff <attempt base_commit>..<child tip>`; an effective limit above 1 (N > 1, composite not serialized) uses REQ-17–REQ-27 and C-6 |
| Step 4.4 | Replaced: composite validation per REQ-12 on `composite-ready` |
| Step 4.5 | PRs only for top-level leaves and composites (REQ-08) |
| Step 8 | Per composite: children, merge commits, child-branch disposition (deleted, or kept with reason), REQ-26 measures |
| Never list | "Never deletes a branch" becomes "Never deletes a branch except the verified temporary child-branch deletion of REQ-31"; "Never runs subtasks in parallel" becomes "Never runs subtasks in parallel except children of one composite under `--parallel N`, N > 1" |

### C-2 Git command forms used by the root (each its own Bash call)

| Purpose | Command |
|---|---|
| Composite branch | `git switch -c <composite-branch> <previous reviewed tip sha>` |
| Child branch in the root worktree (effective limit 1) | `git switch -c <child-branch> <composite tip sha>` |
| Child worktree (N > 1, not serialized) | `git worktree add -b <child-branch> <worktree-path> <composite tip sha>` |
| Child commits in a worktree | `git -C <worktree-path> add <explicit paths>` then `git -C <worktree-path> commit -m "<message>"` |
| Task-record commit (REQ-43) | `git add <explicit .ai paths>` then `git commit -m "chore: update task records"` |
| Return to composite | `git switch <composite-branch>` |
| Integrate | `git merge --no-ff -m "Merge branch '<child-branch>' into <composite-branch>" <child-branch>` |
| Abort conflict | `git merge --abort` |
| Remove worktree | `git worktree remove <worktree-path>` |
| Delete child branch | `git update-ref -d refs/heads/<child-branch> <attempt tip sha>` |

Forbidden in this flow: `git branch -D`, `git worktree remove --force`, `git reset --hard`,
`git clean`, `git stash`, `git rebase`, any push of a child branch. Policy: each git write is its
own Bash call; the hook's same-command state mark denies some, not all, later reads in the same
command (`harness/claude/capabilities.md` X15), so the policy does not rely on it.

### C-3 `scripts/composite_run.py` (new, optional helper)

Invoked as `python3 "$ORCHESTRAIL_HOME/scripts/composite_run.py"`, like the logging helper
(`workflows/spec-run.md:31`); it is run from the source root, not deployed by `scripts/sync.sh`.
Required when N > 1 (REQ-25); optional when N = 1, where the root applies the `reconcile` table
itself if the helper is unavailable. Python ≥ 3.11, standard library only, one file. It never writes a file, never runs a git command
that writes, and never spawns a model. Read-only git it may run: `diff`, `status`,
`rev-parse`, `merge-base --is-ancestor`, `worktree list --porcelain`, `cat-file`. Output: one
JSON object on stdout with sorted keys. Exit 0 = result printed; exit 2 = invalid input or git
read failure, stdout empty, stderr lines `composite-run: <code>: <detail>` with codes
`usage`, `journal-missing`, `journal-invalid`, `plan-invalid`, `unknown-composite`,
`unknown-child`, `git-failed`.

| Subcommand | Arguments | Result |
|---|---|---|
| `--version` | — | `{"version": "1"}` |
| `validate` | `--journal P` | `{"valid": true, "attempts": n}`; any DM-3 violation → exit 2 `journal-invalid` |
| `write-set` | `--repo D --base S --tip S [--include-worktree]` | `{"paths": [...]}`: sorted unique repository-relative POSIX paths from `git diff --name-status -z -M <base> <tip>` (both rename sides) plus, with the flag, every path of `git status --porcelain=v1 -z --untracked-files=all` in D |
| `admit` | `--plan P --journal J --composite ID --limit N` | `{"active": [...], "admit": [...], "waiting": [{"id", "reason"}], "integrate_next": id or null, "done": bool}` |
| `check-merge` | `--plan P --journal J --composite ID --child ID --repo D` | `{"verdict": "ok" \| "scope-exceeded" \| "overlap", "paths": [...], "with": [...]}` |
| `reconcile` | `--journal J --repo D` | `{"attempts": [{"child", "attempt", "stage", "action", "detail"}]}` |
| `check-handoff` | `--handoff P --journal J` | `{"verdict": "ok" \| "stale", "digest": <sha256>, "reasons": [...]}`; `stale` when `candidate_commit` ≠ `git -C <worktree> rev-parse HEAD`, a `test_files` hash differs from the file in the worktree, `previous_digest` ≠ the attempt's last recorded handoff digest, or `child`/`attempt`/`branch` differ from the journal's latest attempt |
| `post-merge-commands` | `--plan P --journal J --composite ID --child ID` | `{"commands": [{"child", "command"}]}`: the REQ-03 list in `## Subtasks` row order |
| `next-attempt` | `--journal J --composite ID --child ID --slug S` | `{"attempt": k, "branch": ..., "worktree": ...}`: k = latest attempt + 1 (1 when none); branch per Terminology; worktree per DM-4 |
| `measure` | `--journal J` | `{"composites": [{"id", "requested_parallel", "elapsed_s", "active_sum_s", "max_concurrency", "merges", "check_failures", "serializations"}]}` |

`measure` formulas per composite, over attempts with both `dispatched_at` and `ended_at`:
`elapsed_s` = latest `ended_at` − earliest `dispatched_at`; `active_sum_s` = Σ(`ended_at` −
`dispatched_at`); `max_concurrency` = the largest number of such intervals
[`dispatched_at`, `ended_at`) containing one instant; `merges` = attempts with non-null
`merge.commit`; `check_failures` = Σ `merge.check_failures`; `serializations` = 1 if `serialized` is set, else 0. With no such attempt
the three time values are `null`.

`admit` rules, evaluated over children in `## Subtasks` row order:
1. Effective limit = 1 if the composite is `serialized`, else `--limit`.
2. A child is a candidate when it has no attempt or its latest attempt is `superseded`, every
   prerequisite inside the composite has its latest attempt `accepted`/`cleaned` and plan
   status `reviewed`, and every prerequisite outside the composite has plan status `reviewed`.
   Otherwise it waits with `prerequisite-failed` when a prerequisite inside the composite is
   `failed`, `blocked`, `check-failed` or `conflict`, else with `dependency-pending` (this
   covers direct and transitive dependencies).
3. A candidate with `Parallel-safe: no`, an incomplete write set, or a serialized composite is
   exclusive: it is admitted only when no child is active, nothing else is admitted in the same
   call, and no reservation-holding child exists whose planned write set is incomplete or
   intersects the candidate's (any reservation-holding child, when the candidate's own set is
   incomplete); while it is active nothing else is admitted. An exclusive candidate that
   cannot be admitted waits with `exclusive-wait` and is a barrier: later candidates wait with
   `barrier`.
4. Other candidates are admitted in order while the active count stays within the limit, each
   independent (REQ-05) of every reservation-holding and already admitted child; otherwise
   `write-set-overlap`, `interface-overlap` or `limit-reached`.
5. `integrate_next` = the first child in row order whose latest attempt is `validated`, when no
   earlier child's latest attempt is `branched`, `dispatched`, `merge-intent` or `merged`.
6. `done` = every child's latest attempt is `accepted` or `cleaned`.

`check-merge`: actual write set of the child's latest attempt (`base_commit..tip`, plus the
worktree when one exists); `scope-exceeded` lists paths not in the planned write set (any
`.ai/` path is always listed); `overlap` lists paths in the actual write set of another child
whose latest attempt is active, `accepted` or `cleaned`, named in `with`; `scope-exceeded`
wins when both apply. The root calls it only when N > 1 (REQ-11).

`reconcile` actions per latest attempt; the first matching row wins (rows marked "any" are
evaluated in table position):

| Journal stage | Observation | Action |
|---|---|---|
| `branched` | branch absent | `redo-branch` |
| `branched`/`dispatched` | branch tip ≠ journal `tip` and the journal tip is an ancestor | `record-tip` |
| `dispatched` | its worktree (or the root worktree when `worktree` is `null`) has uncommitted changes outside `.ai/`, ignoring untracked files the repository ignores | `inspect-worker` |
| `merge-intent` | composite tip = `expected_target`, no `MERGE_HEAD` | `redo-merge-precheck` |
| `merge-intent` | composite tip is a merge commit with parents (`expected_target`, `tip`) | `record-merged` |
| `merge-intent`/`merged` | `MERGE_HEAD` present in the root worktree | `stop-merge-in-progress` |
| `merged` | composite tip contains `merge.commit` | `run-post-merge-checks` |
| `accepted` | `cleanup.failure` is set | `none` |
| `accepted` | worktree or branch still present | `cleanup-pending` |
| any | composite branch tip ≠ journal composite `tip` but descends from it | `record-composite-tip` |
| any | composite branch does not contain an accepted attempt's `merge.commit`, or a recorded ref is at a commit no row above explains | `stop-mismatch` |
| otherwise | — | `none` |


### C-4 git-rails `DELETION_VERIFIER` (changed)

`hooks/git_rails.py` replaces the default `DELETION_VERIFIER` with a composite-journal verifier
of the existing signature `(DeletionRequest, Invocation, Context) → DeletionVerdict`. It returns
`exception=True` only when all hold, checked in this order; otherwise `exception=False` with the
named failure:

| # | Check | Failure text |
|---|---|---|
| 1 | `request.forced` is false, exactly one ref, it starts with `refs/heads/`, and its expected value is a full SHA (the `update-ref -d <ref> <sha>` form) | `unsupported-deletion-form` |
| 2 | `state_changed(invocation)` is false | `state-changed` |
| 3 | Every regular file directly in `<common-dir>/orchestrail-composite/` (subdirectories and `.tmp` files ignored) named 64 hex + `.json` is a usable journal (DM-3 schema, size, encoding, name = SHA-256 of `task_path`, `repository_common_dir` = this common dir), using the restack journal reader rules | `composite-journal-unusable` |
| 4 | Exactly one journal holds exactly one attempt whose `branch` equals the ref's branch name | `no-matching-attempt` |
| 5 | That attempt's stage is `accepted` and `merge.commit` is non-null | `not-accepted` |
| 6 | Expected SHA = attempt `tip` = current value of the ref | `tip-mismatch` |
| 7 | `<merge.commit>^2` = `tip` and `merge.commit` is an ancestor of the current composite branch tip | `not-integrated` |
| 8 | No worktree in `git worktree list --porcelain` has the branch checked out | `checked-out` |

Every git read uses the existing sanitized read layer and budgets. When the verifier refuses, the
decision stays `ask` with the shipped reason code and rule id (R22/R23). `git branch -d`,
`-D` and remote-tracking deletions always refuse at check 1. The test
`test_default_verifier_is_the_no_exception_implementation` (`tests/git-rails.sh:2801-2802`) is
replaced by one asserting the new default, and `no_exception_verifier` stays importable.

### C-5 Contract-file changes (canonical first, then readers)

| File | Change |
|---|---|
| `rules/git-flow.md` | `## Branch model`: per-composite paragraph, child branches and their naming; merge-commit message form; `## Commits`: task-record commit (REQ-43); `## Pull requests`: composite PR and body; `## Safety rails`: keep the existing deletion row for `git branch -d/-D` and unverified forms (`hook: ask`) with its Policy cell changed to "Owner approval required; the verified temporary child-branch deletion is the separate row below", and add a row "`git update-ref -d refs/heads/<child> <sha>` of a temporary child branch the composite journal verifies" with Policy "Only inside `/spec-run` cleanup" and Enforcement `hook: allow with composite journal`, added to the anchored Enforcement vocabulary line; `## Recorded state`: new fields; restack linearization note |
| `rules/orchestration.md` | Opening paragraph: sequential except children of one composite under `--parallel N`; roles Leaf coordinator and Workflow agent; parallel-mode single writer; Implementer split in parallel mode (D-01); the "strictly sequential" sentence keeps that phrase for everything outside one composite; `### Conditions that always stop the run, regardless of class`: in parallel mode (N > 1), `atomic-tests: failed` and a sub-agent blocker of one child stop the run as REQ-24 states (once no child of the composite is active or admissible) |
| `rules/workflow-globals.md` | Orchestrated-mode paragraph; `branch_model:`; composite and child fields; protected fields |
| `rules/workflow-reference.md` | Protected Sections Contract additions; `### Parallel Safety` format |
| `rules/tdd.md` | None; REQ-41 cites it unchanged |
| `workflows/spec-run.md` | C-1, C-2, C-6; Step 4 composite procedure; journal; resume; never list; the "one synthetic aggregate per subtask" sentence (`:45-46`) becomes one per attempt (REQ-02) |
| `workflows/pav-close.md`, `workflows/phase-composite-validation.md` | REQ-40; REQ-12 surface; `/spec-run` becomes the per-composite invoker |
| `workflows/pae-tests.md` | REQ-46 command line in the report and notes |
| `workflows/phase-atomic-execution.md`, `workflows/phase-atomic-validation.md`, `workflows/pae-implement.md`, `workflows/pae-finalize.md`, `workflows/pav-check.md`, `workflows/pav-propose.md` | Parallel-mode clause: run as one dedicated agent, request child invocations from the root (C-6), return every state write (own block included) as a delta, work only inside the given worktree; `workflows/pav-check.md` and `workflows/phase-composite-validation.md` additionally, in parallel mode, never run spec 16's `record` and return the `review` object of C-6 row 11 (REQ-55) |
| `workflows/pd-design.md` | REQ-52 re-render of `### Parallel Safety` after design |
| `workflows/pd-decompose.md` | REQ-09 subsection rendered from 20 DM-8; replace "Do not claim unsupported parallel execution" and the Execution Strategy composite sentence per DM-5 |
| `workflows/restack.md` | REQ-34 |
| `scripts/validate-contracts.sh` | No new check. Each changed check expression below is a spec 13 DM-9 `contract_changes` entry in `tests/fixtures/validator-runtime/inventory-amendment.json` whose `requirement` is a value `spec-12 REQ-NN` this delivery adds under 13 REQ-69, with a DM-20 verdict row per entry. Update the literals of existing checks whose pinned text changes: `:1056` ("strictly sequential" still present), `:1454` (allowed invokers become `workflows/pav-close.md` and `workflows/spec-run.md`), `:1513` (same-agent resume stays true for effective limit 1), `:5456` (vocabulary line), `:5614` (deletion-row wording), `:5617` (old-policy phrases); `:712` stays true |
| `tests/validator-runtime-oracle.py` | Extend the closed `requirement` set with the `spec-12 REQ-NN` values that the `scripts/validate-contracts.sh` row's `contract_changes` entries name (13 REQ-69), update `AMENDMENT_SHA256` and re-pin the source guard |
| `tests/git-rails.sh` | Replace the default-verifier test (C-4); re-pin the source guard per `tests/fixtures/validator-runtime/README.md` |
| `scripts/README.md` | List `composite_run.py`, `check-composite-branch-model.sh` and `check-composite-run.py` |
| `.ai/principles/domain.md` | Terms of `## Terminology`; Composite, Stack, Implementer, Orchestrator rows |
| `.ai/principles/architecture.md` | P4 statement updated to name the root as the single writer of parallel mode |
| `harness/claude/capabilities.md` | State that worker write restrictions are role discipline, not harness permissions (NFR-04) |
| `tests/golden/cases/composite/reference/spec-run/` and `tests/expected/composite/spec-run/projection.json` (spec 09 DM-1; delivery stage 12A) | The change that delivers the composite branch model rebuilds the `composite`/`spec-run` golden reference and its expected projection, because new `/spec-run` tasks then record `per-composite` (REQ-16) and the pair exercises 09's `per-composite` SA-10/SA-11 rules at N = 1 (09 REQ-51) |
| `tests/golden/cases/composite/case.json` (spec 09 DM-1 `workflows`; delivery stage 12B) | The change that delivers parallel children adds a `composite` case workflow entry with `entry: "spec-run"` and `parallel: 2` (its prompt contains `--parallel 2`; the key may differ from `entry`, for example `spec-run-parallel-2`) for REQ-15, with the reference 09 requires for a case workflow |
| `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `workflows/PIPELINE.md` | Composite branch model and `--parallel` |
| `.ai/adr/NNNN-…` | One new ADR superseding ADR-0004 Decision 3 for children of one composite, ADR-0004 Decision 1 for parallel mode (D-01), and recording ADR-0005 Decision 1's amendment as implemented |

File and command names are the current ones. If spec 13's migration lands first, each change
applies to the file spec 13 gives that section: rule files become `<kind>-<subject>`
(`rules/git-flow.md` → `contract-git-flow`; the `workflow-reference` sections → their split
files such as `contract-state-files`; always-on content → `harness/<name>/always-on.md`), and
commands are renamed (ADR-0009 Decision 3, `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:116-130`: `/phase-composite-validation` →
`composite-validation`, `/phase-atomic-execution` → `atomic-execution`,
`/phase-atomic-validation` → `atomic-validation`, child steps such as `/pae-tests` →
`atomic-execution-tests`).

### C-6 Message protocol in parallel mode

The root spawns every agent (A-16); an agent's final report returns to the root; the root,
coordinators and phase agents exchange messages only with the root, never directly between two
non-root agents (`agent-messaging`). Each message is one JSON object.

| # | From → To | Message | Root action |
|---|---|---|---|
| 1 | root → coordinator (spawn) | `{"attempt": {child, attempt, branch, worktree, base_commit}, "description_path", "ai_dir"}` | Journal `dispatched`, `agents.coordinator` |
| 2 | coordinator → root | `{"request": "phase", "workflow": "phase-atomic-execution"}` | Spawn execution phase agent with message 1's fields |
| 3 | phase agent → root | `{"request": "workflow", "workflow": "pae-tests" \| "pae-implement" \| "pae-finalize", "handoff_digest": <sha256 or null>}` | `check-handoff` on the named handoff (none for `pae-tests`); spawn the workflow agent with that handoff |
| 4 | workflow agent → root (final report) | Workflow report: changed paths, test files, observed command and result, deltas | REQ-11, checkpoint commit, REQ-22 handoff, apply deltas; reply to the phase agent `{"stage-done": <workflow>, "handoff_digest", "verdict"}` |
| 5 | phase agent → root (final report) | `{"phase-done": "execution", "result": "complete" \| "blocked" \| "failed", "reason"}` | Forward to the coordinator |
| 6 | coordinator → root | `{"request": "phase", "workflow": "phase-atomic-validation"}` only after a `complete` execution phase or, under REQ-54, after the root reports a finished repair (row 10) | Spawn validation phase agent; it requests `pav-check`, `pav-propose`, `pav-close` as in row 3 |
| 7 | phase agent → root (final report) | `{"phase-done": "validation", "verdict": "DONE" \| "NEEDS WORK", "composite_ready": <id or null>}` | Apply deltas; journal `validated`, or on NEEDS WORK `failed` (or, under REQ-54, keep `dispatched` and run the repair); forward to the coordinator, which ends unless a repair runs, in which case it requests a validation phase again after the repair |
| 8 | root → coordinator and root → its live phase agent | `{"stop": <reason>}` (REQ-04, REQ-14, REQ-27) | The phase agent lets its running workflow agent finish, requests nothing more and sends its final report; the coordinator replies `{"stopped": <last stage-done workflow>}`; a running `repair` workflow agent finishes the same way and starts no recheck (REQ-04, REQ-54) |
| 9 | root → coordinator | `{"status?": true}` (REQ-27) | Reply `{"status": <current workflow or "idle">}` |
| 10 | root → coordinator | `{"repair-done": <episode key>, "handoff_digest": <sha256>}` after the root spawned the `/pae-repair` workflow agent (REQ-21, REQ-54), applied its deltas, committed 19's checkpoints and built the DM-6 handoff with stage `repair` | Journal `agents.workflows` (the repair agent); the coordinator then sends row 6 |
| 11 | review agent → root (final report): the `/pav-check` workflow agent, the Validator of a serialized composite's child (final report only, no phase agent) or the REQ-12 composite validation agent | The row 4 report plus `"review": {"draft": {"level", "step", "scope_key", "options": {the `prepare` options as C-1 of spec 16 names them}, "record": <spec 16 DM-7 draft object>} \| null, "none_reason": null \| "unavailable" \| "disabled" \| "helper-error" \| "multi-repository" \| "blocked"}`; `draft` is null only with a `none_reason` (spec 16 DM-8 reasons) | REQ-55, REQ-56: write the draft file, run `record`, then apply the verdict and notes deltas and append the `verification:` entry from the `record` result; or append the `none` entry |
| 12 | root → phase agent (reply replacing row 4's after a review report that REQ-56 handles) | `{"stage-redo": "pav-check", "record": "refused" \| "unusable" \| "error", "reasons": [<spec 16 refusal reasons, `draft-invalid` for an unusable draft, or the `record` error code for exit 2, 3 or 4>], "helper": "on" \| "off"}` | The phase agent requests `pav-check` again (row 3); the root spawns the fresh agent with `reasons` and `helper`; the composite validation agent and the Validator of a serialized composite's child have no phase agent, so the root respawns them directly with the same fields |

Messages that do not match the expected next row for the attempt are ignored and recorded in the
journal attempt as `unexpected_messages` (count); a second report for the same workflow with the
same handoff digest is a duplicate and ignored (E-33).

## Non-Functional Requirements

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-01 | Determinism | Identical helper inputs produce byte-identical stdout | Fixture runs each subcommand twice and compares bytes |
| NFR-02 | Hook budget | The verifier uses the existing git read layer: 2 s per read and the 5 s event budget (`hooks/git_rails.py` constants `GIT_READ_SECONDS`, main budget) | Fixture with a slow fake git sees `ask`/deny within the existing budget, as the shipped suite does for other verifiers |
| NFR-03 | Non-blocking telemetry | Logging failures never block (P9, `.ai/principles/architecture.md`) | Contract check that the workflow keeps the existing logging clause |
| NFR-04 | Least privilege | Worker write restrictions are role discipline, not enforced by harness permissions; the capability record says so (P11) | Contract check on `rules/orchestration.md` and the capability record |
| NFR-05 | Compatibility | `per-leaf` tasks behave exactly as today (P3; README gate G4) | Contract check plus helper/hook fixtures with legacy blocks |
| NFR-06 | Portability | Helper requires Python ≥ 3.11 and git; Linux is the verified platform; no other platform claim | Preflight message names the missing requirement |
| NFR-07 | Performance | N/A — no speedup, token or cost target (README gate G8; ADR-0009 Decision 5); only measurement per REQ-26 | — |

## Edge Cases & Failure Modes

| # | Case | Expected behaviour | REQ |
|---|---|---|---|
| E-01 | `--parallel 0`, `-1`, `1.5`, `two`, `--parallel=` | Stop before any write | REQ-29 |
| E-02 | `--parallel 1` | Sequential per-composite model, no capability or helper check beyond today's | REQ-29, REQ-25 |
| E-03 | N > 1 on Codex or with any capability key absent/unknown | Stop, name missing keys, no write | REQ-25 |
| E-04 | `ORCHESTRAIL_HOME` unset, helper missing, Python < 3.11 or no runbook test command, with N > 1 | Stop with the missing item; N = 1 needs none of them | REQ-25 |
| E-05 | Composite with one child | One child branch, one merge, composite validation, one PR | REQ-06, REQ-12 |
| E-06 | All children `Parallel-safe: no` or no `### Parallel Safety` | Children run one at a time; effective concurrency 1 recorded | REQ-09, REQ-18 |
| E-07 | Child write set names a directory or glob | Row must be `no`; admitted alone | REQ-09, REQ-19 |
| E-08 | Two children rename to/from the same path | Overlap; not admitted together | REQ-05 |
| E-09 | Child changes a lockfile or generated file not in its write set | `scope-exceeded` → serialization | REQ-11, REQ-14 |
| E-10 | Worker writes under `.ai/` in its worktree | `scope-exceeded` → serialization; the change is never committed | REQ-11 |
| E-11 | Clean merge but post-merge test fails | `check-failed`, composite `blocker:` set, run stops; after the owner fixes the cause (for example by an approved fix child or a commit of their own) and clears `blocker:`, the rerun decides | REQ-35, REQ-45 |
| E-12 | Textual merge conflict | `merge --abort`, `conflict`, serialization, new attempt from current tip | REQ-36, REQ-14 |
| E-13 | Rework attempt's new RED test already passes | `/pae-tests` stops under `tdd` (a new test passing before implementation stops and reports); no fabricated RED | REQ-41 |
| E-14 | Child NEEDS WORK while siblings are independent | Attempt `failed`, reservation kept; siblings continue; dependents wait `prerequisite-failed`; run stops when nothing is active or admissible; resumes per REQ-50 after the owner clears `blocker:` | REQ-24, REQ-50 |
| E-15 | Class-B question or tripwire in one child | Broad stop: no admissions, stop sent to all coordinators | REQ-04 |
| E-16 | Spawn refused for capacity | Child not admitted, `waiting: limit-reached`; effective concurrency recorded; zero active and zero admissible → stop | REQ-23 |
| E-17 | Interruption after `merge-intent`, before `git merge` | `redo-merge-precheck` | REQ-13 |
| E-18 | Interruption after merge commit, before checks | `record-merged` / `run-post-merge-checks`; no second merge | REQ-13 |
| E-19 | Interruption during conflicted merge (`MERGE_HEAD` present) | `stop-merge-in-progress`; owner aborts or resolves | REQ-13 |
| E-20 | Coordinator `gone` after restart (the harness reports the identity unknown), clean worktree | Redispatch from the last verified checkpoint with fresh agents | REQ-27 |
| E-20a | Coordinator status message neither answered nor rejected (`unknown`) | Child `blocked` with `liveness-unknown`, reservation kept; no redispatch | REQ-27 |
| E-21 | Coordinator `gone`, dirty worktree | Child `blocked` with `uncommitted-work`, reservation kept; owner reconciles the paths | REQ-27 |
| E-22 | Journal unreadable or invalid | Resume stops; hook asks for every child deletion | REQ-13, REQ-32 |
| E-23 | Child branch tip moved after acceptance | Verifier `tip-mismatch` → ask; root keeps the branch and reports | REQ-31, REQ-32 |
| E-24 | `git worktree remove` refuses (dirty or locked) | Keep worktree and branch; record; continue | REQ-31 |
| E-25 | Owner rejects a hook ask on deletion | Final for that branch; keep it; report | REQ-31 |
| E-26 | Child branch name collides with an unowned branch | Preflight stops (`rules/git-flow.md:30-31`); resume uses the journal-owned branch only | REQ-30 |
| E-27 | Composite PR already exists on resume | Reuse it; update by pushing the composite branch; no second PR | REQ-08 |
| E-28 | `/restack` after the composite's predecessor is squash-merged | Replay composite branch with the verified form; merges linearized and reported; child blocks skipped | REQ-34 |
| E-29 | Resume of a task started before this change | `branch_model: per-leaf`; old behaviour throughout | REQ-16 |
| E-30 | Leaf promoted to composite mid-run | Its branch becomes the composite branch | REQ-37 |
| E-31 | Composite integration validation NEEDS WORK, fix sibling approved | Fix sibling is a new child: branch from composite tip, normal cycle; admitted under the same rules | REQ-12, REQ-18 |
| E-32 | Two agents return at the same moment | Root applies their deltas one after another; second re-reads the target section first (spec 15 REQ-18 derived proposal when the delta was composed against an older state) | REQ-01 |
| E-33 | Duplicate delivery of a worker result | Same handoff digest → ignored; different content for the same stage → stage blocked | REQ-22 |
| E-34 | Provider limit during a parallel run | Treated as a blocker of that child; no account switch | REQ-24 |
| E-35 | Empty composite (`children:` empty) or a child id without plan row or block | Stop before creating the composite branch | REQ-44 |
| E-36 | Worktree probe exit codes differ, or a workflow agent reports its edit tool refuses the worktree path | Composite serialized (`worktree-probe`), or child `blocked` with `worktree-not-writable` and then serialized; remaining children run in the root worktree | REQ-49, REQ-14 |
| E-37 | `--parallel 3` on a task that recorded per-leaf branches | Stop before any write | REQ-48 |
| E-38 | Resume with a different N than the journal's `requested_parallel` | New N applies to new admissions; existing attempts continue in their recorded location with the agent model they started with (C-6 for worktree attempts, which needs only the sub-agent and messaging support `/spec-run` already requires, `workflows/spec-run.md:16`); N > 1 repeats the preflight | REQ-29, REQ-13 |
| E-39 | A leftover journal of another task records an attempt with the same child-branch name | Verifier check 4 fails → `ask`; root keeps the branch and reports | REQ-32 |
| E-40 | A child depends on a top-level leaf before its composite | Satisfied by that leaf's plan status `reviewed` (it is already in the composite base) | REQ-18 |
| E-41 | Tracked `.ai/` state edited by the root while children run (N > 1) | Committed as `chore: update task records` before each merge; merges never touch `.ai/` because children may not | REQ-43, REQ-11 |
| E-42 | A worker result arrives that does not match the expected next C-6 row | Ignored and counted; the attempt waits for the expected message | REQ-22 |
| E-43 | Effective limit 1: validation deltas pending when the root switches back to the composite branch | Committed on the child branch as `chore: update task records` before `git switch`, so the merge carries them and git never refuses the switch or merge | REQ-43 |
| E-44 | Exclusive candidate while a sibling is `failed` with an intersecting reservation | Waits `exclusive-wait`; the run stops when nothing is active or admissible | REQ-18, REQ-24 |
| E-45 | Root-run test commands (probe, post-merge checks) while an exclusive child that uses a fixed port or shared database is active | Cannot occur: an exclusive child is admitted only when no child is active (so no other child is `validated` or awaiting a probe), nothing is admitted while it is active, its own probe runs before its agents start, and its post-merge checks run after its agents have ended. Children that are not exclusive use no exclusive resource (DM-5) | REQ-18, REQ-49, REQ-03 |
| E-46 | Records pending after a top-level leaf or composite is reviewed and its PR recorded | No record commit on that branch; the records carry over to the next stack branch and go into its first commit, as today | REQ-43 |
| E-47 | The root restarts between a `pav-check` report and the end of its REQ-55 handling | No record or entry was applied before the report was handled; the attempt is still `dispatched` (REQ-27), the validation phase is requested again and the correction budget of REQ-56 starts anew; a record `record` published just before the restart stays, the re-review publishes the next record, and the missing `verification:` entry makes spec 16's next preparation a full scope (`prior-not-latest`, 16 REQ-12) | REQ-55, REQ-27 |

## Acceptance Criteria

Verification vehicles (test-first, written and observed failing before implementation):
**[C]** contract checks in a new standalone `scripts/check-composite-branch-model.sh` (shell
builtins, like `scripts/check-spec-draft.sh`): each [C] criterion names the exact sentence or
anchored line the check matches, and the check fails on the unchanged files; **[H]** helper and
hook fixtures in a new standalone `scripts/check-composite-run.py` (Python standard library,
`unittest`) using disposable git repositories, journals and plans; **[G]** the existing
`tests/git-rails.sh` (one replaced test, C-4); **[L]** an owner-approved live spec 09 run, never
part of ordinary validation. Agent behaviour that only a live run can show (actual concurrency,
agent identities in a real session) is covered by [C] for the instruction and [L] for the
behaviour.

- [ ] **AC-01** (REQ-01, REQ-02, REQ-28) [C] Given the changed `rules/orchestration.md` and
  `workflows/spec-run.md`, when the contract check runs, then it finds the statements that in
  parallel mode the root is the only writer of `.ai/` and of the journal, that each attempt gets
  exactly one per-subtask aggregate when it first reaches an end stage, and that agents receive
  no other child's transcript, report or handoff.
- [ ] **AC-02** (REQ-03, REQ-35, REQ-45) [H] Given a fixture composite with children A and B
  `accepted` (commands `cmdA`, `cmdB`) and C `merged` (command `cmdC`), plus D with `n-a`, when
  `post-merge-commands --child C` runs, then it returns `cmdA`, `cmdB`, `cmdC` in row order and
  no entry for D; given the journal after a failing run (`check-failed`, `merge.check_failures:
  1`), `admit` returns no admission and `integrate_next: null`, and `measure` reports
  `check_failures: 1`; given the same journal after a passing rerun (`accepted`), `admit`
  resumes admissions.
- [ ] **AC-03** (REQ-05) [H] Given fixture plans and an empty journal, when `admit --limit 2`
  runs, then two children with disjoint complete write sets and no interface or dependency
  link are both admitted; and each of these pairs yields exactly one admission with the stated
  reason for the other: a shared path (`write-set-overlap`), a rename touching the other's path
  (`write-set-overlap`), `produces: x` vs `consumes: x` (`interface-overlap`), a direct or
  transitive dependency (`dependency-pending`), `Parallel-safe: no` on the first
  (`barrier` for the second).
- [ ] **AC-04** (REQ-06, REQ-07, REQ-30, REQ-39) [H] Given a disposable repository driven
  through the C-2 command forms for one composite with two sequential children, then the
  composite branch starts at the previous tip, each child branch starts at the composite tip
  recorded as its `base_commit`, each merge commit has first parent = previous composite tip and
  second parent = child tip, every `test:` commit precedes its `feat:` commit in history, and
  `validate` accepts the journal whose child `merge.commit` values equal those merge commits.
- [ ] **AC-05** (REQ-08, REQ-33) [C] Given the changed `rules/git-flow.md` and
  `workflows/spec-run.md`, then they state that only composite and top-level branches are pushed,
  one draft PR per composite whose base is the previous stack branch, a resumed run reuses the PR
  recorded in `pr:`, and the composite body has one stack-position line and one section per child
  with test level and `test:` SHA; and no rule example contains `T-` followed by a digit.
- [ ] **AC-06** (REQ-09, REQ-10, REQ-29) [H][C] Given `admit --limit 2` over four eligible
  independent children, then exactly two are admitted and two wait with `limit-reached`; given a
  serialized composite, then no call admits a child while another is active; and the contract
  check finds the REQ-29 regular expression `^[1-9][0-9]*$` with its stop message in
  `workflows/spec-run.md` and the DM-5 table header in `workflows/pd-decompose.md`.
- [ ] **AC-07** (REQ-11, REQ-14) [H] Given a child whose actual diff touches a path outside its
  reservation, another whose diff touches a path already in an accepted sibling's actual write
  set, and a third that writes `.ai/x.md` in its worktree, when `check-merge` runs, then the
  verdicts are `scope-exceeded`, `overlap` (naming the sibling in `with`) and `scope-exceeded`;
  and given a journal with `serialized` set and one `validated` attempt whose `check-merge` is
  `ok`, `admit` returns it as `integrate_next` and admits nothing while it is active.
- [ ] **AC-08** (REQ-12, REQ-40) [C] Given the changed `workflows/pav-close.md`,
  `workflows/spec-run.md` and `workflows/phase-composite-validation.md`, then `/pav-close`
  returns `composite-ready: <id>` instead of invoking composite validation in `per-composite`
  tasks, the root dispatches one fresh validation agent on the composite branch, and the
  integration surface command is the REQ-12 `git diff --name-only` form excluding `.ai`.
- [ ] **AC-09** (REQ-13, REQ-42) [H][C] Given journals and repositories prepared at each
  interruption point (`branched` without branch, `merge-intent` before the merge, `merge-intent`
  after the merge commit, `MERGE_HEAD` present, `merged` before checks, `accepted` with branch
  present, composite tip advanced by a later commit, recorded merge missing from the composite
  branch), when `reconcile` runs, then it returns `redo-branch`, `redo-merge-precheck`,
  `record-merged`, `stop-merge-in-progress`, `run-post-merge-checks`, `cleanup-pending`,
  `record-composite-tip` and `stop-mismatch` respectively; given an absent journal it returns no
  attempts and `validate` exits 2 with `journal-missing`; a `<journal>.tmp` sibling is ignored by
  `validate` and by the verifier; and the contract check finds in `workflows/spec-run.md` the
  sentence that the stage preceding a git operation is written before that operation.
- [ ] **AC-10** (REQ-15) [L] Given owner-approved spec 09 `composite` golden runs with
  `--parallel 1` and `--parallel 2`, when `scripts/check-composite-run.py` compares the structural
  assertions of the two spec 09 expected projections (normalized by spec 09's rules), then they
  are equal except aliased hashes, branch names and timestamps. Not
  required for deterministic acceptance.
- [ ] **AC-11** (REQ-16) [C] Given the changed `rules/workflow-globals.md` and
  `workflows/spec-run.md`, then the first contains the anchored line
  `branch_model: per-leaf | per-composite` and the sentence "A missing `branch_model:` reads as
  `per-leaf` when any block records `branch:`", and the second contains the REQ-16 rule that an
  existing value is never changed.
- [ ] **AC-12** (REQ-41) [C] Given the changed `workflows/spec-run.md`, then for both the root
  worktree path and the worktree path it names the `test:`-before-implementation commit for `red`
  and `pinned`, the single commit for `n-a` and the unchanged legacy note, and states that a new
  attempt never fabricates RED.
- [ ] **AC-13** (REQ-17, REQ-18, REQ-23) [H] Given five ready independent children of one
  composite and `admit --limit 4`, then four are admitted and the fifth waits `limit-reached`;
  after one admitted child's attempt becomes `accepted`, the next call admits the fifth while the
  other three stay active; after one becomes `failed` instead, the fifth is admitted only if its
  write set is disjoint from the failed child's (reservation kept); and a child whose
  prerequisite is `validated` but not `accepted` waits `dependency-pending`.
- [ ] **AC-14** (REQ-19, REQ-23) [H] Given two candidates whose planned write sets share a
  generated file or a rename destination, or one whose write set contains a directory, then
  `admit` never returns them together and never admits one while the other is
  reservation-holding; after the holder becomes `superseded`, the other is admitted.
- [ ] **AC-15** (REQ-20, REQ-21, REQ-22) [C][H] Given the changed `workflows/spec-run.md`, then
  it contains the C-6 table rows 1–10, requires a fresh coordinator per attempt and a fresh agent
  per phase and workflow invocation, a root checkpoint commit between workflows, and blocking on
  a `stale` handoff; and given a handoff whose `candidate_commit` differs from the worktree HEAD,
  whose test-file hash differs, or whose `previous_digest` breaks the chain, `check-handoff`
  returns `stale` with the matching reason, and `ok` for an unmodified handoff.
- [ ] **AC-16** (REQ-17, REQ-18, REQ-24, REQ-04) [H][C] Given a composite where child A is
  `failed`, B depends on A and C is independent of A, then `admit` admits C, keeps B waiting
  `prerequisite-failed`, and `done` stays false; and the contract check finds the REQ-04 broad
  stop and the REQ-24 rule to stop when nothing is active or admissible; REQ-24's trigger list in
  `workflows/spec-run.md` includes `atomic-tests: failed`; and the changed `rules/orchestration.md
  → ### Conditions that always stop the run, regardless of class` states that in parallel mode
  (N > 1) `atomic-tests: failed` and a sub-agent blocker of one child stop the run as REQ-24
  states.
- [ ] **AC-17** (REQ-25, REQ-27) [C] Given the changed `workflows/spec-run.md`, then it requires
  the five capability keys of REQ-25 for N > 1 through spec 13's preflight, and lists
  `ORCHESTRAIL_HOME`, the helper `--version` output and the runbook test command before any
  write, using the stop of 13 REQ-37 for a missing capability and the REQ-25 stop message for
  the other items, and the three liveness outcomes of
  REQ-27 with redispatch only for `gone` with a clean location.
- [ ] **AC-18** (REQ-18, REQ-19, REQ-26) [H] Given a fixture modelled on the example plan of
  17.4 where four children name `scripts/validate-contracts.sh` in their write sets, then
  `admit` never returns two of them together; and given a journal with three attempts whose
  intervals are [10:00, 10:30), [10:10, 10:40) and [10:50, 11:00), `measure` reports
  `elapsed_s: 3600`, `active_sum_s: 4200`, `max_concurrency: 2`, and `null` time values for a
  composite without a complete interval.
- [ ] **AC-19** (REQ-12) [C] Given the changed workflows, then composite validation runs once per
  composite tip, task-level validation still runs on the stack tip (`workflows/spec-run.md`
  Step 5 unchanged), and a composite cannot reach `reviewed` while any child's latest attempt is
  not `accepted`/`cleaned`.
- [ ] **AC-20** (REQ-28) [C] Given the changed `workflows/spec-run.md`, then the dispatch
  instructions pass the root worktree's absolute `.ai/` path as read-only context and forbid
  edits to the worktree copy of `.ai/`.
- [ ] **AC-21** (REQ-38) [C] Given the changed `workflows/spec-run.md`, then dry run with
  `--parallel` reports N, preflight and the first `admit` result and lists no branch, worktree,
  journal or state write.
- [ ] **AC-22** (REQ-30) [H] Given the C-2 forms in a disposable repository with N = 2, then each
  worktree path equals `next-attempt`'s `worktree`, the root worktree's `git status --porcelain`
  stays empty, and for a child with one `superseded` attempt `next-attempt` returns attempt 2
  and branch `<composite>--<slug>-attempt-2`.
- [ ] **AC-23** (REQ-31, REQ-32) [H][G] Given a disposable registered project and a valid
  journal, when the hook evaluates `git update-ref -d refs/heads/<child> <tip>` for an
  `accepted`, merged, not-checked-out child, then it allows; each single violation of C-4 checks
  1–8 (including `git branch -d`, a wrong expected SHA, a forged attempt in a second journal, an
  unusable journal file, a merge commit not reachable from the composite branch, a checked-out
  branch) yields `ask` with R22/R23; the replaced default-verifier test passes; and `reconcile`
  returns `none` for an `accepted` attempt whose `cleanup.failure` is set.
- [ ] **AC-24** (REQ-34) [C] Given the changed `workflows/restack.md`, then branch collection
  excludes children of composites in `per-composite` tasks, the child-note text of REQ-34 is
  present, and the report states merge-commit linearization for composite branches.
- [ ] **AC-25** (REQ-36) [H] Given two child branches that conflict textually, when the C-2
  merge, abort and journal update are applied, then the composite tip equals
  `merge.expected_target`, no `MERGE_HEAD` exists, the child branch tip is unchanged, and
  `validate` accepts the journal with stage `conflict` and the conflicting path.
- [ ] **AC-26** (REQ-37) [C] Given the changed `workflows/spec-run.md`, then a leaf promoted to a
  composite keeps its recorded branch fields as the composite's.
- [ ] **AC-27** (REQ-43) [C] Given the changed `rules/git-flow.md`, then `## Commits` states, for
  every N, that pending tracked `.ai/` changes are committed as `chore: update task records`
  before switching from a child branch to its composite branch, before each child merge and
  after composite-validation deltas, and that the switch cutting the next stack branch makes no
  record commit.
- [ ] **AC-28** (REQ-44, REQ-48) [C] Given the changed `workflows/spec-run.md`, then it contains
  the REQ-44 and REQ-48 stop messages verbatim, each before any branch creation step.
- [ ] **AC-29** (REQ-46) [C] Given the changed `workflows/pae-tests.md` and
  `workflows/spec-run.md`, then `/pae-tests` reports the observing command and the root records
  `tdd: command — <command>`.
- [ ] **AC-30** (REQ-47) [H] Given a journal where every attempt is `cleaned` or `superseded`,
  `reconcile` returns `none` for all; and the contract check [C] finds the REQ-47 deletion rule
  in Step 8 of `workflows/spec-run.md` with the condition "every attempt is `cleaned` or
  `superseded`".
- [ ] **AC-31** (REQ-49) [C] Given the changed `workflows/spec-run.md`, then it runs the runbook
  `test:` command at the attempt's `base_commit` in the new worktree and in the root worktree
  before dispatch, and when the exit codes differ or the probe leaves tracked changes it
  supersedes the attempt and serializes the composite with `worktree-probe`; it names no setup
  command.
- [ ] **AC-32** (REQ-50, REQ-24) [H][C] Given a journal whose child attempt is `failed` and a
  repository that matches it, `reconcile` returns `none`; given the attempt set back to
  `dispatched`, `admit` counts it as active (it occupies a slot); and the contract check finds in
  `workflows/spec-run.md` the REQ-24 `blocker: <blocked_reason>: <detail>` write, the REQ-50
  precondition that the owner has set `blocker:` to `none`, and the DM-3 resume table rows.
- [ ] **AC-33** (REQ-18) [H] Given child A `failed` with planned write set {x} and exclusive
  candidates B (`Parallel-safe: no`, write set {y}), C (`Parallel-safe: no`, write set {x}) and D
  (write set containing a directory) in that row order, with no active child, when
  `admit --limit 2` runs, then B is admitted alone and C and D wait (`exclusive-wait`,
  `barrier`); in a second fixture without B, C waits `exclusive-wait` and D waits `barrier`; and
  in a third fixture with A `cleaned` and D as the only candidate, D is admitted alone.
- [ ] **AC-34** (REQ-51, REQ-43) [C] Given the changed `workflows/spec-run.md`, then at N = 1 it
  runs children in `## Subtasks` row order and stops the run on NEEDS WORK as in Step 4.3; it
  commits pending tracked task records as `chore: update task records` before switching from a
  child branch to the composite branch, before each child merge and after composite-validation
  deltas; and it states that the switch cutting the next stack branch makes no record commit and
  that the next stack branch starts from the composite tip REQ-08 pushes.
- [ ] **AC-35** (REQ-09, REQ-52) [C] Given the changed `workflows/pd-decompose.md` and
  `workflows/pd-design.md`, then the first renders `### Parallel Safety` from spec 20 DM-8 with
  `Parallel-safe: no` when `disqualifiers` is non-empty, and the second re-renders the rows after
  design without changing rows of children that have started (spec 20 REQ-24).
- [ ] **AC-36** (REQ-53) [C] Given the changed `workflows/spec-run.md`, then, conditioned on spec
  14's `packet` command being available, it builds each child agent's packet with `--work` =
  attempt location, `--ai-dir` = root `.ai/`, `--base-commit` = attempt `base_commit` and the
  role mapping of REQ-53, dispatches without a packet when `packet` exits non-zero, and keeps
  REQ-28's items otherwise.
- [ ] **AC-37** (REQ-54) [C] Given the changed `workflows/spec-run.md`, then it calls 19 C-5 on a
  child NEEDS WORK only when the repair policy is active, keeps the attempt `dispatched` with its
  reservation, never repairs a `merged`, `accepted` or `cleaned` attempt, routes an accepted repair
  to `validated` and the unchanged merge rules, starts no further repair on a REQ-04 broad stop while letting a dispatched repair worker finish (this clause applies to a parallel run, stage 12B), and states
  that without the policy REQ-24 and REQ-51 apply as written.
- [ ] **AC-38** (REQ-55, REQ-56, REQ-01) [C] Given the changed `workflows/spec-run.md`,
  `workflows/pav-check.md`, `workflows/phase-composite-validation.md` and
  `rules/orchestration.md`, then for N > 1 they state that a review agent never runs `record`
  and never writes under `<task>/verification/`; that its report carries the C-6 row 11 `review`
  object; that the root writes the draft under the root worktree's `<task>/verification/drafts/`,
  checks `--work`, `--task` and `--ai-dir`, runs `record` before applying any other delta of the
  report, applies the verdict and notes deltas only after a published record and appends the
  `verification:` entry (16 DM-8) from the `record` result; that `draft: null` with a
  `none_reason` yields the `none` entry; that an unusable draft or exit 1 triggers exactly one
  correction spawn carrying the reasons (C-6 row 12), a second failure or exit 2, 3 or 4 one
  spawn with `"helper": "off"`, and a further failure sets the attempt `blocked` with reason
  `record-failed`; and that at N = 1 the Validator runs `record` itself, while the Validator of a serialized composite's child at N > 1 returns the draft like every other review agent. (Stage 12B; no stage
  12A text depends on it.)

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-38 |
| REQ-02 | AC-01 |
| REQ-03 | AC-02 |
| REQ-04 | AC-16 |
| REQ-05 | AC-03 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04 |
| REQ-08 | AC-05 |
| REQ-09 | AC-06, AC-35 |
| REQ-10 | AC-06 |
| REQ-11 | AC-07 |
| REQ-12 | AC-08, AC-19 |
| REQ-13 | AC-09 |
| REQ-14 | AC-07 |
| REQ-15 | AC-10 |
| REQ-16 | AC-11 |
| REQ-17 | AC-13, AC-16 |
| REQ-18 | AC-13, AC-16, AC-18, AC-33 |
| REQ-19 | AC-14, AC-18 |
| REQ-20 | AC-15 |
| REQ-21 | AC-15 |
| REQ-22 | AC-15 |
| REQ-23 | AC-13, AC-14 |
| REQ-24 | AC-16, AC-32 |
| REQ-25 | AC-17 |
| REQ-26 | AC-18 |
| REQ-27 | AC-17 |
| REQ-28 | AC-01, AC-20 |
| REQ-29 | AC-06 |
| REQ-30 | AC-04, AC-22 |
| REQ-31 | AC-23 |
| REQ-32 | AC-23 |
| REQ-33 | AC-05 |
| REQ-34 | AC-24 |
| REQ-35 | AC-02 |
| REQ-36 | AC-25 |
| REQ-37 | AC-26 |
| REQ-38 | AC-21 |
| REQ-39 | AC-04 |
| REQ-40 | AC-08 |
| REQ-41 | AC-12 |
| REQ-42 | AC-09 |
| REQ-43 | AC-27, AC-34 |
| REQ-44 | AC-28 |
| REQ-45 | AC-02 |
| REQ-46 | AC-29 |
| REQ-47 | AC-30 |
| REQ-48 | AC-28 |
| REQ-49 | AC-31 |
| REQ-50 | AC-32 |
| REQ-51 | AC-34 |
| REQ-52 | AC-35 |
| REQ-53 | AC-36 |
| REQ-54 | AC-37 |
| REQ-55 | AC-38 |
| REQ-56 | AC-38 |

## Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-1 | Agents do not follow role discipline (a worker edits `.ai/` or runs git) | Corrupted shared state or unrecorded commits | Medium | Root-only staging of explicit paths; REQ-11 actual write sets include worktree changes; hook rails; capability record states the limit (NFR-04) |
| R-2 | Hand-written journal drifts from the schema | Resume stops; deletions ask | Medium | `validate` after every write (when the helper is available); atomic rename (REQ-42); hook treats unusable journals as no exception |
| R-3 | The journal is forged or edited to pass the hook | A non-integrated branch could be deleted | Low | Outside the threat model as for the restack journal (`harness/claude/capabilities.md` X8); check 7 still requires reachability of the merge commit, so only fully integrated tips are deletable |
| R-4 | Post-merge checks are too narrow to catch a semantic interface break | Integration defect reaches composite validation | Medium | Composite validation on the final tree (REQ-12); spec 16 may widen the check set later |
| R-5 | `/restack` linearizes composite merge history | Reviewers lose the merge structure after a restack | Medium when predecessors are squash-merged | Reported (REQ-34); per-child test-first order survives (observed 2026-11-13, see Assumptions A-14); Q-02 |
| R-6 | Changing `tests/git-rails.sh` and `scripts/validate-contracts.sh:5614` disturbs the pinned source-guard inventory | Validator fails until re-pinned | High | Follow `tests/fixtures/validator-runtime/README.md` re-pin procedure in the same change; add no new test program under `tests/`; new or changed `.py`/`.sh` files among the spec 09 golden fixtures listed in this spec's C-5 are re-pinned by the same procedure |
| R-7 | Number of agents per child (coordinator plus up to eight workflow agents) exhausts harness capacity | Effective concurrency below N | Medium | Spawn refusal is recorded and the child waits (E-16); REQ-26 reports effective concurrency |
| R-8 | Spec 09 structural assertions SA-10/SA-11 assume per-leaf stacking | Golden cases fail for `per-composite` runs | High once implemented | Adopted by 09 REQ-51 (DM-3 SA-10/SA-11 `per-composite` rules) from the facts in Notes → Follow-up changes |
| R-9 | Parallelism is later widened beyond one composite (D-04 defers it to a possible successor specification) | Scheduler scope widens; branch model for top-level leaves changes | Medium | Scheduler rules are expressed over a dependency graph and reservations, so widening is additive; the branch model for top-level work is left untouched |

## Assumptions

- A-01 | Scope of parallelism | Resolved: only children of one composite run concurrently; top-level leaves and children of different composites keep the sequential stack; the 2026-11-06 owner widening (across composite boundaries and of top-level leaves) was deferred by the owner on 2026-11-14 (D-04, Q-01 resolved) and is out of scope | Source: ADR-0009 Decision 4 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:154-156`); spec 20 REQ-07 keeps the sequential top-level stack; D-04 | Reversible: yes (a successor specification, `## Notes → ### Successor path`)
- A-02 | `--parallel` semantics | Resolved: no flag → N = 1; `--parallel` → 2; `--parallel N` → N; positive integers only | Source: original §2 and §6.1; ADR-0009 Decision 4 "Default `--parallel 2`" read as the flag's default value | Reversible: yes
- A-03 | Does the per-composite model apply at N = 1 | Resolved: yes, for every new `/spec-run` task | Source: ADR-0009 Decision 4 "in sequential and parallel mode alike" | Reversible: yes
- A-04 | How legacy tasks are recognised | Resolved: `branch_model:` field written at Step 3; absent field with any recorded `branch:` reads as `per-leaf` | Source: P3 additive contracts (`.ai/principles/architecture.md`); original REQ-16 | Reversible: yes
- A-05 | Where child work happens at N = 1 | Resolved: on the child branch checked out in the root worktree, no worktree | Source: spec 13 requires `worktrees` only for `--parallel` with N > 1 (13 REQ-37) | Reversible: yes
- A-06 | Worktree location | Resolved: under `<git-common-dir>/orchestrail-worktrees/` | Source: existing pattern of run records under the common directory (`workflows/restack.md:12-15`); disposable-repository verification of 2026-11-13 (DM-4) | Reversible: yes
- A-07 | Merge then check, or check then commit | Resolved: commit-first `--no-ff` merge, then post-merge checks, with distinct `merged` and `accepted` stages | Source: original §9.3 permits this with distinct journal stages; smallest reversible choice (no `--no-commit` intermediate state to recover) | Reversible: yes
- A-08 | Merge commit message | Resolved: `Merge branch '<child-branch>' into <composite-branch>` | Source: git's standard merge message shape; branch names are permitted content (`rules/git-flow.md:149-150`); best practice | Reversible: yes
- A-09 | Which post-merge checks run | Resolved: the recorded test command of every accepted child plus the merged child | Source: original §9.3 step 7 ("affected deterministic checks"); smallest deterministic set until spec 16 | Reversible: yes
- A-28 | Check receipts on merged results | Resolved: the REQ-03 post-merge commands always run and never consult a receipt. Once spec 16 is delivered, its receipts are bound to content and worktree root, never to branch names or commits; a receipt from a child worktree is never reused for the merged composite tree (the worktree root is one of 16's inputs), and only the checks of the REQ-12 composite review, run in the root worktree, may reuse a receipt, when 16's reuse conditions hold (16 REQ-05); that review always runs at scope `full-integration` (16 REQ-15) | Source: spec 16 REQ-05, REQ-15 | Reversible: yes
- A-29 | Repair worker on a broad stop (added 2026-11-14) | Resolved: a REQ-54 repair worker already dispatched when REQ-04 stops the run is not interrupted and not duplicated: it finishes, its result is recorded through spec 19's `outcome` step, no new repair attempt or recheck starts and the episode stays open; this adopts 19 C-10 row 12 and is consistent with C-6 row 8, where a stopped phase agent lets its running workflow agent finish | Source: spec 19 C-10 row 12; REQ-04 and C-6 row 8 of this spec | Reversible: yes
- A-10 | Conflict handling | Resolved: `git merge --abort`, then serialization; the child branch keeps all commits | Source: original §10 (conflict disproves independence; preserve work; no forced reset); `/restack` aborts are already accepted forms (`workflows/restack.md:96-98`) | Reversible: yes
- A-11 | Deletion form | Resolved: only `git update-ref -d refs/heads/<b> <sha>` | Source: completed spec 06 §8.7 | Reversible: yes
- A-12 | Deterministic decisions and their tests | Resolved: an optional stdlib helper `$ORCHESTRAIL_HOME/scripts/composite_run.py`, located like the logging helper; required only for N > 1; at N = 1 the root applies the `reconcile` table itself when the helper is unavailable, so the sequential path needs no helper | Source: README gates G4/G5/G6 (`.ai/specs/README.md` → "Shared acceptance gates"); ADR-0001 implications (a run-time script needs its own ADR) | Reversible: yes
- A-13 | Where new tests live | Resolved: standalone `scripts/check-composite-branch-model.sh` and `scripts/check-composite-run.py`; no new test program under `tests/` (the spec 09 golden reference and case entry listed in this spec's C-5 are fixtures, re-pinned per `tests/fixtures/validator-runtime/README.md` → "Maintaining the nested source guard" (steps 1–5) when they hold `.py`/`.sh` files); one existing test in `tests/git-rails.sh` replaced | Source: ADR-0019 Decision 3 (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`); source-guard README | Reversible: yes
- A-14 | `/restack` and merge commits | Resolved: keep the verified replay form; merge commits are linearized and reported | Source: `workflows/restack.md:91-98` exact form; disposable-repository observation on 2026-11-13 (git 2.53.0): `git rebase --onto` of a branch with two `--no-ff` merges replayed `test: a`, `feat: a`, `test: b`, `feat: b` in order and dropped the merges | Reversible: yes
- A-15 | Separate test and implementation agents | Resolved: in parallel mode only (D-01); N = 1 keeps the one-Implementer two-checkpoint handoff | Source: original §8.2 and REQ-21 explicitly supersede the same-agent rule for the new mode | Reversible: yes
- A-16 | Nested delegation | Resolved: root-mediated dispatch is the specified path: the root spawns every coordinator, phase and workflow agent, and coordinators and phase agents request invocations by message (C-6) | Source: original REQ-25 permits it; smallest choice independent of whether sub-agents can spawn sub-agents | Reversible: yes
- A-17 | Platform agent capacity | Resolved: not declared anywhere; a refused spawn is the observed limit (E-16); no number is invented | Source: original REQ-23; README G1/G4 | Reversible: yes
- A-18 | Dependence on specs 14, 15, 16, 19 not yet delivered | Resolved: before each is delivered, workers bootstrap context themselves (existing rule), deltas use the existing report route, checks are those of REQ-03, and no repair attempt is made (NEEDS WORK stops per REQ-24/REQ-51). Once delivered: 14 → the root builds packets per REQ-53 (14 C-8); 15 → handoff digests per 15 REQ-41; 16 → receipts per A-28; 19 → repair per REQ-54 when its policy is passed; 16 → at N > 1 the root writes review records from returned drafts per REQ-55 and REQ-56 (the receipts rule above is A-28) | Source: README prerequisites row for 12 (`.ai/specs/README.md` → "Dependency order"); G4 conservative path; peer contracts named | Reversible: yes
- A-19 | Telemetry | Resolved: no new run-log fields; one aggregate per attempt; measurements come from the journal through `measure` | Source: spec 02/05 own the run-log contract; P9 (durations never model-written) | Reversible: yes
- A-21 | `/restack` classification of a composite branch | Resolved: unchanged; `git cherry` lists no merge commits, so the own range classifies by its child commits | Source: disposable-repository observation on 2026-11-13 (git 2.53.0): after squash-merging a composite branch with one `--no-ff` merge, `git cherry -v main <tip> <base>` printed only `- … test: a` | Reversible: yes
- A-22 | Liveness of agents after a restart | Resolved: a status message to the recorded identity; the harness's unknown-identity answer means `gone`; anything else that is not a reply means `unknown` and blocks | Source: original REQ-27 ("never duplicate a live invocation"); smallest conservative choice | Reversible: yes
- A-23 | Resource locks and ordering constraints of the original | Resolved: no separate lock mechanism; a child needing an exclusive resource or named by an ordering constraint is `Parallel-safe: no` and runs exclusively | Source: original §17.3 (host-exclusive checks "apply globally") and REQ-05; exclusivity is the smallest rule that needs no new runtime | Reversible: yes
- A-24 | Commits of tracked task records | Resolved: as `chore: update task records` at the three REQ-43 triggers, at every N; otherwise with the root's next commit (existing rule) | Source: `rules/git-flow.md:156-165`; `workflows/spec-run.md:66-69` (dirty tracked bookkeeping stops a resume) | Reversible: yes
- A-25 | Remedy after `check-failed`, NEEDS WORK or a block | Resolved: the run stops; the owner fixes the cause and clears `blocker:`; the resumed run reruns the checks (REQ-45) or continues the attempt (REQ-50) | Source: `workflows/spec-run.md:297-299` (NEEDS WORK stops the run; branch and commits stay) | Reversible: yes
- A-26 | Worktree tooling risk | Resolved: keep DM-4 for hook coverage; a probe (REQ-49) serializes the composite when the worktree behaves differently | Source: hook registry prefix matching (`hooks/git_rails.py:330`); best practice | Reversible: yes
- A-27 | Effort for parallel-mode spawns | Resolved: parallel-mode spawns (leaf coordinators, phase agents and workflow agents) are outside spec 18's policy version 1 and keep today's dispatch behaviour: no resolver call, no effort parameter and no `## Effort Decisions` line for them; the `/pae-tests` and `/pae-implement` agents take the leaf's model resolution of `workflows/spec-run.md` Step 2 like an Implementer, and every other parallel-mode agent uses the session default like the Validator. This delivery adds no effort handling itself. Bringing them under the policy is a later revision of 18 triggered by this delivery (18 A-29): it adds the roles leaf coordinator, phase agent and workflow agent and the stages `tests`, `implement`, `finalize`, `check`, `propose`, `close` to 18 DM-2/DM-6 and names the root as the only writer of `## Effort Decisions` in 18 C-4. The `repair` stage (REQ-54) is not in that list: it stays with spec 19's own route (19 C-8) | Source: spec 18 C-6 row 12 and its A-14, A-29; `workflows/spec-run.md:126-131` | Reversible: yes
- A-20 | Composite validation trigger | Resolved: `/pav-close` returns `composite-ready`; the root dispatches a fresh validation agent | Source: original REQ-12 and §9.4; `rules/orchestration.md:115` already routes its writes through the root | Reversible: yes

## Decisions

- D-02 | A child branch name that collides with an existing branch the journal does not own stops preflight; collisions between two children's slugs are refined from their Goals | Overrides: none (original §8.1 named both remedies; `rules/git-flow.md:30-31`, `:69-71` decide which applies where) | Rationale: an existing unowned branch is never reused | Follow-up: none
- D-03 | After serialization, a validated attempt is integrated only when `check-merge` is `ok`; every other non-accepted attempt is superseded and redone; no partial evidence is carried over | Overrides: none (narrows original §10 step 8, which permitted reuse after a currency check) | Rationale: the currency check of evidence belongs to specs 14/16, which are not delivered; redoing is the smallest safe choice | Follow-up: revisit when 14/16 land
- D-01 | In parallel mode, `/pae-tests` and `/pae-implement` run in distinct fresh agents, with the root committing the test checkpoint and passing a verified handoff | Overrides: ADR-0004 Decision 1 rejected alternative "Tests and implementation in separate agents" (`.ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md:46-47`) and `rules/orchestration.md:58-61`, for parallel mode only | Rationale: authorized by the source (original §8.2 and REQ-21: "This supersedes the existing same-agent RED-to-GREEN rule for this mode; implementation must record the decision") | Follow-up: the superseding ADR of C-5
- D-04 | Parallelism only within one composite: children of one composite may run concurrently (`--parallel N`); children of different composites and top-level leaves never run concurrently and keep the sequential stack | Overrides: the owner's own clarification of 2026-11-06 (Source, §2 and §17) asking for parallel execution across composite boundaries and of leaves directly under the task, which the owner now defers | Rationale: ADR-0009 Decision 4 allows parallelism "only between children of one composite", the stack rule in `rules/git-flow.md` builds top-level branches sequentially from the previous reviewed tip, and widening later is additive because admission works on the dependency graph | Follow-up: deliver stages 12A and 12B, measure on real tasks, and only then consider a separate successor specification for a materialized stack (`## Notes → ### Successor path`), which would supersede ADR-0009 Decision 4 and change the git-flow stack rule; nothing in this spec depends on it
- D-05 | In parallel mode the root orchestrator runs spec 16's `record`, on the review draft the review agent returns in its report (REQ-55, REQ-56, C-6 rows 11 and 12) | Overrides: none (16 assumed the reviewing workflow writes the record; in parallel mode that conflicts with REQ-01, which the owner's choice resolves in favour of REQ-01) | Rationale: in parallel mode the root is the only writer (REQ-01), so verification records are written by the root from a returned draft, which needs no new mechanism | Follow-up: spec 16 is edited separately so that its C-6 row for spec 12 and its parallel-mode review text point at this resolved question; no change to 16's DM-7, DM-4a or record contents is required

## Clarifications

### Session 2026-11-06 (recorded in the original text)

- Q: What parallelism does the owner want? → A: (translated from Russian) Execute eligible
  atomic subtasks of one large task in parallel to shorten implementation time; give each atomic
  subtask its own coordinating agent and each atomic workflow a separate agent; analysis and test
  preparation, implementation and validation are examples of distinct workflows. Folded into
  REQ-20–REQ-22; the cross-composite part was deferred by the owner on 2026-11-14 (D-04, Q-01 resolved).

### Session 2026-11-13

- N/A — auto mode; no question was asked. Every resolved gap is recorded under Assumptions.

### Session 2026-11-14

- Q: Does parallelism go beyond the children of one composite (Q-01)? → A: No. Option (a):
  parallelism only within one composite; across composite boundaries and of top-level leaves it
  is deferred (D-04); a materialized-stack successor specification is considered only after 12A
  and 12B are delivered and measured.
- Q: Who runs the scoped-verification `record` command in parallel mode (Q-03)? → A: The root
  orchestrator, on the review draft that the review agent returns (D-05, REQ-55, REQ-56).

## Open Questions

- **Q-01 (resolved)** | Does parallelism extend beyond the children of one composite? The
  2026-11-06 clarification (Source, §2 and §17: "including across composite boundaries", "leaves
  directly under the task", "Direct leaves integrate into the parent task branch") conflicts with
  accepted ADR-0009 Decision 4 ("Parallel execution is allowed only between children of one
  composite; top-level T-XX remain strictly sequential",
  `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:154-156`), with the stack rule that
  branch N is cut from N-1's reviewed tip (`rules/git-flow.md:52-53`), and with the exclusion of
  a separate integration branch (Source §2). No source defines the branch model for concurrent
  top-level work. Options: **(a) recommended** — children of one composite only, as specified
  here; widening later is additive because admission is graph-based. (b) Materialized stack:
  independent top-level items and children of different composites run concurrently on
  temporary branches from the last reviewed tip; afterwards each stack branch is created in
  plan order from its predecessor's reviewed tip and receives its work by a `--no-ff` merge;
  requires superseding ADR-0009 Decision 4 and changing `rules/git-flow.md → ## Branch model —
  the stack`. (c) One task-level branch for all direct leaves — contradicts ADR-0005 Decision 1,
  the per-subtask PR model and the excluded integration branch. Impact: the scope of REQ-17,
  REQ-18, REQ-24 and REQ-26, and AC-16/AC-19 as originally worded.
  Resolved 2026-11-14: option (a) — parallelism only within one composite (D-04). The
  cross-composite and top-level-leaf parts are out of scope; the materialized-stack option (b) is
  the named successor path (`## Notes → ### Successor path`); option (c) stays rejected. No
  longer a blocker.
- **Q-02 (non-blocker)** | Should `/restack` preserve composite merge commits
  (`--rebase-merges`)? This would change the hook's exact replay form
  (`workflows/restack.md:91-98`) and the replay verifier. Current choice: linearize and report
  (A-14). Impact: review history after restacks only.
- **Q-03 (resolved, non-blocker)** | Who writes spec 16's review records (`<task>/verification/reviews/`,
  16 DM-1, written by its `record` step from `/pav-check` and the review workflows) in parallel
  mode, where REQ-01 makes the root the only writer under `.ai/`? Worker-written `notes:` entries
  (14 DM-11, 16 DM-8, 17 DM-9) are already covered: they are returned as deltas under REQ-01 and
  appended by the root with 14 DM-11's append rule. No source decides the record file write; 16
  assumes the reviewing workflow writes it. Recommended: the workflow agent returns the 16 record
  draft in its report and the root runs 16's `record` against the root worktree's task directory
  in REQ-01's sequential order; workflow agents never invoke `record`. Impact: REQ-01, the C-6
  report fields and A-18; N = 1 is unaffected.
  Resolved 2026-11-14: the recommendation was accepted — the root orchestrator runs `record` on
  the review draft that the agent returns (D-05; REQ-55, REQ-56, C-6 rows 11 and 12, AC-38, E-47).

## Notes

### Constraints

- Every git write is a separate Bash call (policy, C-2).
- No pipeline identifier reaches branch names, commits or PR text (`rules/git-flow.md:129-154`);
  the journal and handoffs live in the git common directory and are never committed.
- `.ai/` tracking policy is unchanged; untracked consumer state is never staged
  (`rules/git-flow.md:156-165`).
- Contract changes follow `.ai/principles/coding.md → Changing a contract`: failing check first,
  canonical definition, readers, ADR.
- The validator's check inventory is not extended: `scripts/validate-contracts.sh` changes only
  the literals of existing checks listed in C-5, each through a 13 DM-9 `contract_changes` entry
  (13 REQ-69); follow the re-pin procedure in
  `tests/fixtures/validator-runtime/README.md`, and run the inventory oracle. Whether the
  replaced `tests/git-rails.sh` test name affects a pinned result inventory was not verified.

### Delivery stages

- **12A — composite branch model (N = 1):** REQ-03, REQ-06, REQ-07, REQ-08, REQ-12, REQ-13,
  REQ-16, REQ-30–REQ-37, REQ-39–REQ-47, REQ-50, REQ-51, REQ-53, REQ-54 (their N = 1 parts) and
  the helper subcommands `validate`,
  `reconcile`, `post-merge-commands` and `next-attempt`; AC-02 (its `post-merge-commands`
  clause), AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-19, AC-23–AC-30, AC-32 (its `reconcile`
  and contract-check clauses), AC-34, AC-36, AC-37 (all but its broad-stop clause); the rebuilt
  `composite`/`spec-run` golden reference and expected projection (C-5).
- **12B — parallel children (N > 1):** the remaining requirements, the helper's `write-set`,
  `admit`, `check-merge`, `check-handoff`, `measure`, and the agent model; the clauses of AC-02
  and AC-32 that run `admit` or `measure`, AC-22 (it uses N = 2), the broad-stop clause of AC-37
  and the remaining acceptance criteria; the `composite` case entry with `parallel: 2` (C-5).
  12B starts after 12A is accepted (Scope → Delivery gate).

### Successor path

Recommended order (D-04): deliver 12A, then 12B, measure on real tasks (REQ-26), and only then
consider a separate successor specification for a "materialized stack": independent top-level
items run concurrently, and the stack branches are built afterwards in plan order. It is not
part of this specification. It would need ADR-0009 Decision 4 superseded and the stack rule in
`rules/git-flow.md → ## Branch model — the stack` changed. Widening is additive for this
spec's scheduler because admission works on the dependency graph (R-9); the branch model for
top-level work stays untouched here.

### Implementation hints (nonbinding)

- Reuse the restack journal reader in `hooks/git_rails.py` (strict JSON, size and name rules,
  `JOURNAL_DIRECTORY` pattern at `:2402`) for the composite journal, with a second directory
  constant; share one fixture set between the hook verifier and `composite_run.py validate`.
- `model_plan.py` already parses `plan.md` tables (`scripts/model_plan.py`); the helper can
  follow its table parsing approach.

### Follow-up changes outside this spec

- Spec 09: adopted — 09 REQ-51 and the DM-3 SA-10/SA-11 `per-composite` rules implement these
  branch-ancestry facts, which a `per-composite` run satisfies (kept here as their source):
  1. *Stack entries.* Top-level leaves and composites (a composite counts as one entry, its
     children do not) form the stack in plan order: the first entry's `base_branch` is the seed
     branch; each later entry's `base_branch` is the previous entry's `branch`, and its
     `base_commit` is that branch's tip when the entry was created (for a composite predecessor,
     the composite tip after composite validation, including the REQ-43 record commit when one
     is made).
  2. *Children.* A child block's `base_branch` is its composite's `branch`. Its `base_commit` is
     the composite tip when its latest attempt started. The first child started has the
     composite's start tip as `base_commit`: that is the composite's own `base_commit` when
     nothing was committed on the composite branch before, as for the `composite`/`spec-run`
     case spec 09 exercises (no promotion), and the promoted leaf's current tip, a descendant
     of the composite's `base_commit`, after a promotion (REQ-37). At N = 1 every later child's
     `base_commit` equals the previous child's `merge_commit` (no record commit is made between
     a merge and the next child branch). With N > 1 the
     `base_commit` of a child is a descendant of, or equal to, the `merge_commit` of each of its
     prerequisites in the same composite.
  3. *Merges.* Each accepted child has `merge_commit` with first parent = the composite tip
     before the merge and second parent = the child attempt's tip; every `merge_commit` is an
     ancestor of the composite branch tip; merge subjects are `Merge branch '<child-branch>'
     into <composite-branch>` and contain no `T-` identifier.
  4. *Chains (SA-11).* For a dependency chain inside one composite, the later child's
     `base_commit` descends from (at N = 1 equals) the earlier child's `merge_commit`; across
     stack entries fact 1 applies.
  Child blocks record `pr: none` and child branches are normally deleted after acceptance, so a
  child's `branch:` may name a branch that no longer exists.
- Spec 13: none — the five capability names of REQ-25 and the `state: yes` record form follow
  13 DM-4, and the preflight and its stop message, including the next step it names for each
  missing key, are those of 13 REQ-37; this spec restates no wording of it.
- Spec 15: none — it carries handoff digests (15 REQ-41) and its derived-proposal rule (15 REQ-18)
  covers E-32.
- Spec 18: none from this delivery, which adds no effort handling (A-27). A later revision of 18 (18 A-29), triggered by this delivery, adds the three parallel-mode roles and the stages `tests`, `implement`, `finalize`, `check`, `propose`, `close` to its DM-2/DM-6, with the root as sole writer of `## Effort Decisions` in its C-4; the `repair` stage stays with 19's route.
- Spec 19: none — its spec-12 row in 19 C-10 is wired by REQ-54.
- Spec 20: none — DM-8 supplies the evidence REQ-09 and REQ-52 render.
- Specs 14, 17: none — wired by REQ-53 and the DM-6 note respectively.
- Spec 16: its C-6 row for spec 12 already records the resolved Q-03 (REQ-62, A-33). Still to change there, separately: REQ-62's citation "C-6 row 12" of this spec reads "C-6 rows 11 and 12" (row 11 holds the report, deltas and entry, row 12 the correction reply), and the C-4 `Record:` line gets a pointer to REQ-62 for N > 1. No change to 16's DM-7, DM-4a or record contents is needed.
- `.ai/specs/README.md`: no change required; row 17 prerequisites stay valid.
- **Identity ledger (follow-up outside this spec):** the ledger row(s) at `.ai/tasks/completed/task-01-git-source-of-truth/state.md` lines 210–212 pin a former-name occurrence at this spec's lines 17, 19 and 34, which the refined text no longer holds; the change that commits this revision removes them, as spec 11 A-41 does for its own row.

### Change Log

#### 2026-11-06 — implementation/state reconciliation

- Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

#### 2026-11-13 — English refinement

- Translated sections 1–16 into Source; rewrote the specification into the `/spec-draft`
  structure; kept REQ-01–REQ-27 and AC-01–AC-19 with their subjects, narrowing REQ-17, REQ-18,
  REQ-24 and REQ-26 and AC-16/AC-19 to one composite pending Q-01; added REQ-28–REQ-42 and
  AC-20–AC-26; review rounds added REQ-43–REQ-51 and AC-27–AC-34.

#### 2026-11-14 — reconciliation with refined peer specs

- Spec 15: handoff digests (15 REQ-41) replace "carried inside its envelope"; E-32 cites 15 REQ-18.
- Spec 20: `### Parallel Safety` rendered from 20 DM-8 (REQ-09); new REQ-52 (`/pd-design`
  re-render); A-01 cites 20 REQ-07.
- Spec 14: new REQ-53 (packet per 14 C-8); A-18 keeps the interim until 14 is delivered.
- Spec 16: A-28 (receipts bound to content and worktree root; composite review
  `full-integration`); notes in Terminology and REQ-12.
- Spec 17: DM-6 `observed` gains `label`; exit-code mapping and shared store.
- Spec 18: A-27 (today's dispatch behaviour until 18 is amended; the amendment stated).
- Spec 19: new REQ-54 and DM-3 `repair_episode`; REQ-24/REQ-51 unchanged without the policy.
- Spec 13: REQ-25 delegates the capability check to 13 REQ-37 and 13 DM-4; citations by id.
- Spec 09: Notes state the branch-ancestry facts of a per-composite run.
- New ids: REQ-52–REQ-54, AC-35–AC-37, A-27, A-28. Readiness verdict unchanged.
- Independent check of the changed passages: 13 findings fixed (A-28 reuse limited; REQ-54
  parallel repair path, episode carry-over and C-6 row 7; REQ-28/REQ-53 packet wording and
  failure path; REQ-52 "started" per 20 REQ-24; DM-3 optional fields; DM-6 `repair` stage;
  citation corrections).

#### 2026-11-14 — second reconciliation pass

- Spec 09: Notes fact 2 now covers a promoted leaf (REQ-37) and the unpromoted `composite`/`spec-run`
  case; C-5 and the delivery stages list the rebuilt golden reference and the `parallel: 2` case entry.
- Spec 19: REQ-04, REQ-54, C-6 row 8, AC-37 and new A-29 state that a dispatched repair worker
  finishes on a broad stop and the episode stays open; Terminology gains "Episode key" and "Slot";
  DM-3 `repair_episode` states the opt-in.
- Spec 15: DM-6 states that no `output_handoff_digest` exists for stage `repair`.
- Spec 18: A-27 and the follow-up list agree with 18 A-29 and C-6 row 12.
- Spec 13: REQ-25 and AC-17 cite 13 REQ-37 for the stop instead of restating it; the follow-up
  entry is closed.
- Spec 17: DM-6 `observed` confirmed against 17 DM-3 and C-7 row 12; no change.
- New id: A-29. Q-01 and the readiness verdict unchanged.

#### 2026-11-14 — owner decisions recorded

- D-04 (Q-01 resolved): parallelism only within one composite; Out of Scope names parallelism across composite boundaries and of top-level leaves; A-01, R-9, the Context paragraph and the Requirements preamble no longer treat it as pending; `### Successor path` added to Notes.
- D-05 (Q-03 resolved): the root runs spec 16's `record` on the returned review draft; REQ-01 amended; new REQ-55, REQ-56, AC-38, E-47, C-6 rows 11 and 12; C-5 workflow row and A-18 extended; spec 16 follow-up added.
- New ids: D-04, D-05, REQ-55, REQ-56, AC-38, E-47. Readiness Checklist re-evaluated; verdict READY WITH RESERVATIONS.

#### 2026-11-14 — independent final review

- REQ-04 leaves `atomic-tests: failed` and worker blockers to REQ-24; stage-specific AC clauses assigned; validator literal changes go through 13 DM-9 under REQ-69; serialized composites use the effective-limit-1 agent model; C-6 row 6 widened and row 10 added for repair; child `commits:` include root record commits; REQ-15 owned by `check-composite-run.py`; new non-blocker Q-03 (writer of peer-spec files in parallel mode); spec 09 follow-up marked adopted; ids reordered; identity-ledger follow-up. Q-01 untouched; verdict NOT READY unchanged.

## Readiness Checklist

Result of 2026-11-14, re-evaluated after the owner decisions D-04 and D-05.

Note (2026-11-14, owner decisions): Q-01 and Q-03 are resolved, so check 10 now passes; REQ-55, REQ-56, AC-38, E-47 and C-6 rows 11 and 12 were added and no earlier requirement or criterion changed its meaning. Check 13 still fails and is the only failure.

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph naming the branch model, parallel children of one composite and measured outcome |
| 2 | Out of Scope names concrete exclusions | PASS — twelve named exclusions, including parallelism across composite boundaries and of top-level leaves (D-04) |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-56, each with one trigger and a response; original ids kept; the review-record behaviour is split into REQ-55 (publication) and REQ-56 (refusal), and, like REQ-54, both carry sub-cases of one behaviour |
| 4 | Every REQ maps to ≥1 AC; every AC names ≥1 REQ | PASS — Traceability covers REQ-01–REQ-56 and AC-01–AC-38 |
| 5 | Every AC is binary, observable and can guide a test first | PASS — [C]/[H]/[G] criteria are deterministic, AC-38 is a [C] contract check; AC-10 [L] is binary but runs only in an owner-approved live run and is not required for deterministic acceptance |
| 6 | Non-functional targets measurable, standard, or N/A | PASS — NFR-01–NFR-06 with verification; NFR-07 N/A with its source |
| 7 | Data model and contracts specified | PASS — DM-1–DM-6, C-1–C-6 (C-6 rows 1–12) |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — E-01–E-47 |
| 9 | Every Step 3 ambiguity recorded as resolved or open | PASS — A-01–A-29, D-01–D-05, Q-01–Q-03 (Q-01 and Q-03 resolved 2026-11-14; Q-02 open, non-blocker) |
| 10 | No blocker question remains | PASS — Q-01 resolved by D-04; Q-02 is a non-blocker |
| 11 | Every existing-code claim has a verified path:line citation | PASS — code citations verified by the author and the critic against revision `060ce6d` and not changed by the owner-decision edits; the new text cites peer-spec ids only (16 C-1, C-4, DM-7, DM-8, REQ-12) |
| 12 | Terminology matches project domain definitions | PASS — new terms defined; `.ai/principles/domain.md` additions listed in C-5 |
| 13 | Scope is feature-sized (1–8 subtasks) | FAIL — 56 requirements exceed one feature; split at the Delivery gate: 12A (composite branch model, N = 1) then 12B (parallel children of one composite) |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 97/100, critic: sub-agent, open: none; the 2026-11-14 owner-decision edits were checked by a scoped independent critic of the changed passages only, whose findings were fixed; this is not a new full review |

**Verdict: READY WITH RESERVATIONS** — check 13 fails (feature size); the Delivery gate already
addresses it by delivering 12A before 12B. No failure in checks 4, 5, 9, 10 or 11 and no open
critical finding. Automated readiness is not sign-off.
