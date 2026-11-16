# 12. Parallel children of one composite subtask in isolated worktrees

## Source

- **Split (2026-11-16):** at commit `e3ba41a000c927ac157fd2207df413107ed54cb5` this file held
  both delivery stages of one specification and failed readiness check 13 (56 requirements
  exceed one feature). On the owner's request of 2026-11-16 (translated from Russian: "they are
  very large and must be split in two if this can be done logically; then run each resulting
  spec through `/spec-draft`") stage 12A, the composite branch model at N = 1, moved to
  `.ai/specs/12a-composite-branch-model.md`; stage 12B, parallel children of one composite,
  stays here and starts after spec 12a is delivered (merged). Identifiers keep their numbers and each is
  defined in exactly one of the two files. The Source history below, including the translated
  original text, covers both stages and is the canonical copy that spec 12a cites.

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

**Branch model.** Spec 12a replaces the per-leaf stack for composite children with one
composite branch, temporary child branches merged with `--no-ff`, a composite journal and a
verified deletion; this spec builds on it (12a → Context & Problem for the shipped behaviour
it replaces).

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
creates; spec 12a removes those three problems for sequential runs. Large tasks still pay
serial wall-clock time (ADR-0004 records 21–26 h per run,
`.ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md:90`).

## Goal

On spec 12a's composite branch model, let an explicitly requested parallel
run (`--parallel [N]`) execute up to N proven-independent children of the same composite
concurrently in isolated worktrees, each through dedicated coordinator and workflow agents,
while the orchestrator stays the single writer of shared state and the only git operator,
serializes the composite on any disproved independence, and recovers from interruption
without duplicate merges, lost work or reset counters. Speed, token use and cost are measured,
not promised.

## Scope

Items 1–4 and 10 of the combined specification (the branch model at N = 1, task and block
fields, the composite journal, branch cleanup and the deletion verifier, `/restack`) are spec
12a; the numbering of the remaining items is kept. Item 4 keeps one part here:

4. Removal of temporary worktrees before spec 12a's branch deletion.
5. The `--parallel [N]` flag, its parsing, dry-run reporting and capability/helper preflight.
6. The `### Parallel Safety` plan record written by `/pd-decompose`.
7. Admission, write reservations, refill, overlap detection and serialization among the
   children of one composite.
8. Leaf coordinators, distinct workflow agents per atomic workflow and verified handoffs in
   parallel mode.
9. The subcommands `write-set`, `admit`, `check-merge`, `check-handoff`, `next-attempt` and
   `measure` of spec 12a's helper `scripts/composite_run.py`.
11. Rule, workflow, principle, vocabulary and documentation updates, the superseding ADR, and
    deterministic contract and fixture checks.

**Scheduling.** This spec starts only when the owner schedules it. Hard prerequisites, checked
at Discovery: spec 12a delivered (merged); spec 13 delivered (the capability keys and the
`/spec-run` preflight of 13 DM-4 and REQ-37, REQ-25); spec 20 delivered (the DM-8 object REQ-09
and REQ-52 render); spec 09 delivered (the `composite` case C-10 extends); specs 02, 03 and 05
are completed. Specs 14, 15, 16 and 19 are optional: A-35 states the behaviour before each is
delivered.

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
- Preserving merge commits through `/restack` (spec 12a Q-02); the exact verified replay form stays.
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
| Implementer / Validator (serialized composite in a parallel run) | Spec 12a roles in the root worktree on the checked-out child branch | Git operations; any write under `.ai/` (REQ-01: the own-block carve-out does not apply in a parallel run) |

## Terminology

| Term | Definition | Source |
|---|---|---|
| **Parallel limit N** | The positive integer maximum of concurrently active children of one composite; 1 without the flag. | Original §6.1; REQ-10, REQ-29 |
| **Active child** | A child whose latest attempt stage is `branched` (unless `spawn_refused` is true), `dispatched`, `validated`, `merge-intent` or `merged`; it occupies one slot of the effective limit. | REQ-10, REQ-23 |
| **Reservation-holding child** | An active child, or one whose latest attempt is `failed`, `blocked`, `check-failed` or `conflict`. | REQ-19, REQ-23 |
| **Write set** | Planned: the explicit file list in `### Parallel Safety`. Actual: the normalized paths of `git diff --name-status -M <base>..<tip>` (both sides of renames) plus uncommitted and untracked changes of the child's worktree. | Original §7; REQ-19 |
| **Reservation** | The planned write set held by a reservation-holding child, from admission until its attempt is `accepted`, `cleaned` or `superseded`. | REQ-19 |
| **Serialized composite** | A composite on which independence was disproved or the worktree probe failed; from then on its effective limit is 1 and new attempts run in the root worktree until it completes. | Original §10; REQ-14, REQ-49 |
| **Wave** | Informal name for the set of children active at the same moment; it has no branch, journal record or status. | Original §4 |
| **Leaf coordinator** | The per-attempt sub-agent of REQ-20. | Original §17 |
| **Workflow agent** | A fresh sub-agent dedicated to exactly one workflow invocation (REQ-21). | Original §17 |
| **Handoff** | The immutable JSON record passed from one workflow stage to the next (DM-6). | REQ-22 |
| **Slot** | In this spec always a concurrency slot of the effective limit (REQ-10, REQ-23). It is unrelated to spec 19's `local` and `escalated` repair slots (19 DM-8 `slots`), which this spec never names, except in the preserved original text of the Source section, where "attempt slot" is spec 19's sense. | REQ-10; 19 C-10 row 12, A-34 |

Rejected synonyms: "integration branch", "wave branch", "task branch" (no such branches exist);
"sub-PR" (children get no PR); "lock" for a reservation (no file lock is used); "retry" or
"attempt" for a spec 19 repair (a repair is not an attempt).

## Requirements

Component tags name the actor that implements the behaviour. Unless stated, a requirement
applies only to `/spec-run` tasks with `branch_model: per-composite`. Original identifiers keep
their subject; their original text is under Source. REQ-17, REQ-18, REQ-24 and REQ-26 are
restricted to the children of one composite (D-04). "Parallel run" or "N > 1" is a run whose
resolved N is above 1; "effective limit" is N, or 1 while the composite is serialized. In a
parallel run the attempts of a serialized composite use spec 12a's one-at-a-time agent model
(REQ-14), while REQ-01 (single writer, which overrides the Implementer's own-block carve-out),
REQ-11 (overlap), spec 12a REQ-41's commit sequence, spec 12a REQ-43's record points and REQ-24
(failure isolation) apply to them. Stage names are those of spec 12a DM-3. Identifiers are unique
across this file and spec 12a: a new identifier takes the next number unused in either file.

### Identifiers defined in spec 12a

REQ-03, REQ-06–REQ-08, REQ-12, REQ-13, REQ-16, REQ-30–REQ-37, REQ-39–REQ-47, REQ-50, REQ-51,
REQ-53 and REQ-54; AC-02, AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-19, AC-23–AC-30, AC-32,
AC-34, AC-36, AC-37 and AC-47–AC-50; REQ-64–REQ-67; DM-1–DM-3, C-1–C-5 (this file's C-7–C-10 add
the N > 1 rows to C-1, C-2, C-3 and C-5, and its DM-7 extends DM-3); NFR-01–NFR-03, NFR-05–NFR-07; A-03–A-05,
A-07–A-09, A-11–A-14, A-18–A-21, A-24, A-25, A-28, A-30–A-34; E-05, E-11, E-17–E-19, E-22,
E-23, E-25–E-31, E-35, E-39, E-43, E-46, E-48–E-52, E-54; R-2–R-6, R-8; D-02 and Q-02. A citation of
one of them in this file names spec 12a.

**Clause split.** The clauses of spec 12a REQ-30, spec 12a REQ-31, spec 12a REQ-35, spec 12a REQ-36, spec 12a REQ-47, spec 12a REQ-50 and
spec 12a REQ-54 and spec 12a AC-02, spec 12a AC-12, spec 12a AC-28, spec 12a AC-32 and spec 12a AC-37 that apply only with an effective limit above 1
are this file's REQ-57–REQ-63 and AC-39–AC-43 (each marked "split from 12a …"); AC-44–AC-46
cover REQ-58, REQ-61 and REQ-60. Spec 12a REQ-43 and REQ-53 with AC-34 and AC-36 gave
REQ-68 and REQ-69 with AC-52 and AC-53. The N = 1 behaviour stays in spec 12a under the original
identifier.

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
- **REQ-68 Record commits in a parallel run (split from 12a REQ-43).** WHERE the repository
  tracks `.ai/` paths, WHILE N > 1 and the composite is not serialized, THE SYSTEM [root] SHALL
  keep the root worktree on the composite branch and commit pending tracked `.ai/` changes there as `chore: update task
  records` before each child merge, before dispatching composite validation, after applying its
  deltas, and before the run stops with a `blocker:`, using spec 12a DM-3 `pending_commits` for
  the record commits' SHAs. A serialized composite follows spec 12a REQ-43.
- **REQ-69 Packet location (split from 12a REQ-53).** WHERE spec 14's `packet` command is
  delivered, WHEN the root builds a packet for an agent of an attempt that has a worktree, THE
  SYSTEM [root] SHALL set `--work` to that worktree instead of the root worktree.
- **REQ-28 Worker context.** WHEN the root dispatches any agent for a child, THE SYSTEM [root]
  SHALL give it only that child's description path, its handoff, its worktree path (parallel
  mode), the absolute path of the root worktree's `.ai/` directory as read-only context and,
  under spec 12a REQ-53, its context packet, and never another child's transcript, report or handoff.

### Branches and integration

- **REQ-57 Child worktree (split from 12a REQ-30).** WHILE the effective limit is above 1, WHEN
  the root starts a child attempt, THE SYSTEM [root] SHALL create the attempt's child branch as
  spec 12a REQ-30 states and, in the same step, a new worktree for it at the DM-4 path, using the
  C-8 worktree form, instead of checking the branch out in the root worktree.
- **REQ-59 Post-merge failure with active siblings (split from 12a REQ-35).** WHILE the
  effective limit is above 1, IF a post-merge check fails, THEN THE SYSTEM [root] SHALL, in
  addition to spec 12a REQ-35, admit no further child of that composite (C-9 `admit` rule 0) and stop the run only
  after the active children of that composite acknowledge a stop (REQ-04 procedure).
- **REQ-60 Merge conflict disproves independence (split from 12a REQ-36).** WHILE the effective
  limit is above 1, IF `git merge` reports a conflict, THEN THE SYSTEM [root] SHALL run the abort
  and journal record of spec 12a REQ-36, keep the child's worktree, and treat the conflict as
  disproved independence (REQ-14) instead of spec 12a REQ-36's `blocker:` write and stop.

### Publication and cleanup

- **REQ-58 Worktree removal (split from 12a REQ-31).** WHEN an `accepted` attempt with a
  worktree and a null `cleanup.failure` is cleaned up, THE SYSTEM [root] SHALL run `git worktree
  remove <path>` (never `--force`) as its own Bash call before spec 12a REQ-31's branch deletion,
  and on any failure, hook ask or hook deny keep the worktree and the branch, record the reason
  in `cleanup.failure`, never retry or rephrase it in this or a later run, and continue.
- **REQ-70 Superseded attempts.** WHEN a composite completes, THE SYSTEM [root] SHALL, for each
  `superseded` attempt, run `git worktree remove <path>` (never `--force`) when the attempt has
  a worktree with no tracked change and no untracked, non-ignored path, keep its branch, and
  report the branch and any kept worktree in Step 8; spec 12a REQ-47 deletes the journal only
  when no superseded attempt still has a worktree.
- **REQ-61 Handoff retention (split from 12a REQ-47).** WHEN spec 12a REQ-47 deletes a task's
  composite journal, THE SYSTEM [root] SHALL delete the task's handoff directory (DM-6) in the
  same step; otherwise it keeps it.

### Planning and parallel mode

- **REQ-29 Flag parsing.** WHEN `/spec-run` is invoked, THE SYSTEM [root] SHALL resolve N as 1
  without `--parallel`, 2 for `--parallel` not followed by a value (the next token is absent or
  starts with `--`), and the value for `--parallel <v>` or `--parallel=<v>` where `<v>` matches
  `^[1-9][0-9]*$`, and stop with
  `**stop**: "Invalid --parallel value '<v>': use a positive integer."` before preflight writes
  anything for any other value.
- **REQ-48 Per-leaf tasks.** IF N > 1 and the task's `branch_model` is or resolves to
  `per-leaf` (spec 12a DM-1), THEN THE SYSTEM [root] SHALL stop before any write with
  `**stop**: "Parallel execution requires the per-composite branch model; this task records
  per-leaf branches. Re-run without --parallel."`.
- **REQ-10 Parallel limit.** WHILE a composite is executing, THE SYSTEM [root] SHALL admit no
  child while the number of its active children is at or above the effective limit; attempts
  already active when a resume lowers N continue to completion in their recorded location.
- **REQ-25 Capability preflight.** WHEN N > 1, or on a resume while any attempt has a worktree,
  THE SYSTEM [root] SHALL, before Discovery or any
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
  probe leaves the worktree with tracked changes or new untracked, non-ignored paths outside
  `.ai/`, THEN supersede the attempt and mark the
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
- **REQ-18 Admission.** WHILE N > 1, WHEN a child is considered for dispatch, THE SYSTEM [root]
  SHALL admit it only under the C-9 `admit` rules: every prerequisite inside the composite has its latest
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
- **REQ-11 Overlap detection.** WHILE N > 1 or any attempt of the run has a worktree, WHEN a workflow agent of a child returns, and
  again immediately before that child's merge, THE SYSTEM [root] SHALL compute the child's
  actual write set (C-9 `check-merge`) and treat any path outside its reservation (including
  any `.ai/` path) or inside another active, `accepted` or `cleaned` child's actual write set as
  disproved independence.
- **REQ-14 Serialization.** WHEN independence is disproved in a composite, THE SYSTEM [root]
  SHALL record `serialized` with the reason and paths in the journal, admit no new child of that
  composite, send every active coordinator a stop and wait until each acknowledges or is
  confirmed gone, for at most one further status round (REQ-27), then let an attempt in `merge-intent` or `merged` finish spec 12a REQ-07/REQ-03 (it becomes
  `accepted` or `check-failed`, REQ-59), integrate in row order each `validated` attempt whose
  `check-merge` verdict is `ok`, set `superseded` every other attempt in `branched`,
  `dispatched`, `validated`, `conflict`, `failed` or `blocked` (`accepted` and `cleaned` stay), and run each remaining child as a new attempt from the current composite tip in
  the root worktree with fresh agents of the effective-limit-1 model (spec 12a C-1 Step 4: one
  Implementer, one Validator), one at a time, until the composite completes.
- **REQ-04 Broad stop.** IF a critical finding, an Invariant or Off-limits violation, a
  class-B question, a composite-promotion tripwire or any other condition of
  `rules/orchestration.md:180-187` occurs during a parallel run — except `atomic-tests: failed`
  and a worker blocker of one child, which REQ-24 isolates (spec 12a DM-3 `tests-failed`, `blocker`) —
  THEN THE SYSTEM [root] SHALL
  admit no new child anywhere, send every active coordinator a stop, record each
  acknowledgement with the last verified checkpoint, preserve all branches and worktrees, and
  stop the run. A worker already dispatched, a spec 12a REQ-54 repair worker included, is not
  interrupted: its running agent finishes (C-6 row 8), no further attempt, repair attempt or
  validation recheck starts, its result is recorded through spec 19's `outcome` step and an
  open episode stays open (19 C-10 row 12), and the attempt keeps the journal stage it had at
  the stop for the resume (REQ-27).
- **REQ-24 Failure isolation.** WHILE N > 1, IF a child's atomic validation returns NEEDS WORK
  (unless spec 12a REQ-54 repairs the child, REQ-63),
  its `/pae-tests` reports `atomic-tests: failed`, or a child is blocked, THEN THE SYSTEM [root] SHALL set its attempt `failed` or `blocked` with
  its `blocked_reason`, write `blocker: <blocked_reason>: <one-line detail>` in the child block,
  keep the attempt unintegrated with its branch, worktree and reservation, keep admitting
  independent children of the same composite, and stop the run with that child reported once no
  child of the composite is active or admissible.
- **REQ-63 Repair in a parallel run (split from 12a REQ-54).** WHILE the effective limit is above
  1, WHERE spec 19's repair policy is active for the run, WHEN spec 12a REQ-54 repairs a child,
  THE SYSTEM [root] SHALL run the repair instead of the REQ-24 stop and keep the attempt's
  concurrency slot and reservation; after an accepted
  repair apply REQ-11 and REQ-14 as well as spec 12a REQ-54's merge rules; start no further
  repair attempt or recheck on a REQ-04 broad stop while letting a repair worker already
  dispatched finish, as REQ-04 states; copy the episode key into the next attempt's
  `repair_episode` when REQ-14 supersedes an attempt with an open episode (19 C-10: an episode
  survives serialization, worktree change and new workers); apply the REQ-24 stop when a repair
  loop ends without acceptance (without the active policy, REQ-24 applies exactly as written); and run the `/pae-repair` invocation as one workflow invocation:
  the root spawns one fresh agent for it (REQ-21), the agent returns its leaf-block writes as
  deltas (REQ-01), the root commits 19's checkpoints and builds a DM-6 handoff with stage
  `repair`, and the coordinator then requests a fresh validation phase (C-6 rows 6 and 10).
- **REQ-55 Review records.** WHERE spec 16's `record` command is available (16 C-1), WHILE
  N > 1, WHEN a review agent of the run returns its final report (the `/pav-check` workflow
  agent of a child attempt, REQ-21, the Validator of a child of a serialized composite, which uses
  the effective-limit-1 model and has no coordinator or phase agent, or the composite validation
  agent, spec 12a REQ-12), THE SYSTEM [root]
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
  the spec 12a REQ-12 composite validation agent, which has no attempt, the root writes
  `blocker: record-failed: <one-line detail>` in the composite block and stops the run.
- **REQ-62 Owner-cleared resume with a worktree (split from 12a REQ-50).** WHEN spec 12a REQ-50
  restarts an attempt that has a worktree, THE SYSTEM [root] SHALL restart it in that worktree,
  count it as active (it occupies a slot of the effective limit), and take the restart stage for
  the `blocked_reason` values `handoff-stale`, `liveness-unknown`, `uncommitted-work` and
  `record-failed` from the spec 12a DM-3 resume table.

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
  commit the checkpoint its report represents (if any) in the attempt's worktree in the commit
  sequence of spec 12a REQ-41 (`test:` before the implementation commit for `red` and `pinned`,
  one commit for `n-a`, the legacy note unchanged), build the handoff (DM-6) from that
  report and the worktree, record its digest in the journal, run C-9 `check-handoff` on it
  immediately before dispatching the next workflow, and dispatch the next workflow with only that
  handoff when the verdict is `ok`; a missing report (`blocker`), a `stale` verdict or a report whose test files differ from the
  frozen set (`handoff-stale`) blocks the next workflow and sets the child `blocked` with that
  reason.
- **REQ-71 Spawn refusal.** IF the harness refuses to spawn an agent for a child attempt, THEN
  THE SYSTEM [root] SHALL keep the attempt `branched` with `spawn_refused: true`, record the
  composite's `capacity_limit` as the number of its other active children (DM-7), retry the
  spawn when `admit` lists the attempt in `respawn` after an attempt leaves the active stages
  (clearing `capacity_limit`), and, when no other child of the composite is active, set the attempt `blocked` with
  `blocker` and write `blocker: blocker: spawn refused by the harness`, then stop the run under
  REQ-24 instead of recording a limit (spec 12a's `blocker` resume row applies).
- **REQ-72 Unwritable worktree.** IF a workflow agent's report carries `"worktree_unwritable":
  true` (its edit tool refused a path inside the attempt's worktree), THEN THE SYSTEM [root]
  SHALL set the attempt `blocked` with `worktree-not-writable` and serialize the composite with
  reason `worktree-probe` (REQ-14).
- **REQ-27 Agent recovery.** WHEN a parallel run resumes, THE SYSTEM [root] SHALL, for every
  attempt in stage `dispatched`, send its recorded coordinator and every recorded workflow agent
  not reported finished a status message and classify each outcome as `live` (the coordinator answers with its current stage), `gone` (the harness reports
  the agent identity unknown or finished) or `unknown` (any other outcome); it redispatches only
  a `gone` attempt whose `reconcile` action is `none`, from its last verified checkpoint; an attempt is `live` when any of its agents is `live`; for a
  `live` attempt it sends the C-6 stop (row 8) and waits for `stopped` for at most one further
  status round, then treats the attempt as `gone`, or as `unknown` when an agent is still live; and it sets an `unknown` attempt, or a `gone` one with `inspect-worker`, `blocked` with
  reason `liveness-unknown` or `uncommitted-work`.

### Recovery, migration, measurement

- **REQ-26 Run measurement.** WHEN a run with any composite ends, THE SYSTEM [root] SHALL report,
  per composite, the requested N, serialization events with reasons, and the output of C-9
  `measure`, printing `not measured` for each null value and claiming no speedup.
- **REQ-15 Equivalence.** WHERE an owner-approved spec 09 `composite` golden run exists for
  both `--parallel 1` and `--parallel 2`, THE SYSTEM [`scripts/check-composite-run.py`; spec 09
  defines no comparison between two runs' projections] SHALL compare their normalized
  structural assertions (the two spec 09 expected projections) and treat any difference other than aliased hashes, branch
  names and timestamps as a defect.

## Data Model

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
- Integration order is `## Subtasks` row order among ready children (C-9 `admit` rule 5); dependencies stay in `Depends On`.
- Original fields `packet_digest` and `integration_checks` are not columns: the packet belongs to
  spec 14 and the integration checks are the composite description's Acceptance Criteria.

### DM-6 Handoff (new, parallel mode)

One JSON object per completed workflow stage, built by the root from the returning agent's report
and the worktree after the root's checkpoint commit, carried in the root's message to the next
agent, and stored by the root under `<git-common-dir>/orchestrail-composite/handoffs/<task-key>/<child>-<attempt>-<stage>.json`.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | — |
| `child`, `attempt`, `stage` | text, int, `tests \| implement \| finalize \| check \| propose \| close \| repair` | Identity (`repair`: spec 12a REQ-54) |
| `worktree`, `branch`, `base_commit` | path, text, SHA | Child attempt |
| `candidate_commit` | SHA | Worktree HEAD after the root's checkpoint commit |
| `description_path` | path | The child's `description.md` |
| `ac_ids` | list of text | Acceptance Criteria covered |
| `allowed_paths` | list of paths | The reservation |
| `test_mode`, `test_command` | as spec 12a DM-3 | — |
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
(15 REQ-41); the object itself exists only in the file above. For stage `repair` (spec 12a REQ-54) no
receipt exists (15 C-10 row 12), so no `output_handoff_digest` is recorded for it (the field,
where 15's record has it, stays `null`), while `input_handoff_digest` follows 15 REQ-41 as for
every other stage; no rule of this spec requires a receipt for a repair, and the root records
the handoff digest in the journal `handoffs` list as for any stage.

### DM-7 Journal extension (new, parallel mode)

Spec 12a DM-3 is canonical; this spec writes these optional fields and values, which spec 12a's
`validate` accepts:

| Object | Field or value | Type | Writer | Meaning |
|---|---|---|---|---|
| journal | `requested_parallel` | positive integer | root (REQ-29) | N resolved by the latest invocation; a resumed run overwrites it; absent reads as 1 |
| composite | `serialized` | null or `{"at": <timestamp>, "reason": "overlap\|scope-exceeded\|conflict\|interface\|worktree-probe", "paths": [...], "children": [ids]}` | root (REQ-14, REQ-49) | Absent reads as null |
| attempt | `attempt` ≥ 2 and branch `<composite-branch>--<child-slug>-attempt-<k>` | — | root (REQ-14, `next-attempt`) | A new attempt after serialization |
| attempt | `worktree` | null or absolute path (DM-4) | root (REQ-57) | null when the attempt runs in the root worktree |
| attempt | `agents` | `{"coordinator": <agent id>, "workflows": [{"workflow", "agent"}]}` | root (REQ-20, REQ-21) | Agent identities |
| attempt | `handoffs` | list of `{"stage", "digest"}` | root (REQ-22) | Digests of DM-6 handoffs, in order |
| attempt | `actual_write_set` | sorted list of repository paths | root (REQ-11) | Last `check-merge` paths |
| attempt | `unexpected_messages` | integer | root (C-6) | Count; absent reads as 0 |
| attempt | stage `superseded` | — | root (REQ-14, REQ-49) | Terminal; `ended_at` is set when not already set |
| attempt | `spawn_refused` | bool | root (REQ-71) | true while a refused spawn keeps the attempt `branched`; such an attempt is a waiting candidate, not active |
| composite | `capacity_limit` | null or positive integer | root (REQ-71) | Set on a refused spawn while at least one other child is active; cleared when an attempt leaves the active stages |
| attempt | `blocked_reason` `handoff-stale`, `liveness-unknown`, `worktree-not-writable`, `record-failed` | — | root (REQ-22, REQ-27, REQ-56, E-36) | Resume rows in spec 12a DM-3 |
| attempt | `cleanup.worktree_removed` `true` | — | root (REQ-58) | After `git worktree remove` |

`task-key` (DM-4 worktree path) = the first 16 hex characters of the journal's file-name digest.

## Contracts & Interfaces

### C-7 `/spec-run` invocation (changed; delta to spec 12a C-1)

`/spec-run <path-to-spec> [--allow-pr] [--dry-run] [--parallel [N]]` — N per REQ-29. The
run-start `--flags` value includes `--parallel N` as passed. Stops added: invalid value
(REQ-29), preflight unavailable (REQ-25), per-leaf task with N > 1 (REQ-48). A resumed run uses
the N passed to that invocation and repeats the preflight when N > 1 or any attempt has a
worktree. Rows added to spec 12a's
step changes:

| Step | Change added by this spec |
|---|---|
| Step 0 | Parse `--parallel` (REQ-29); N > 1 preflight (REQ-25, REQ-48); on resume, REQ-27 agent recovery before redispatch |
| Step 4 | An effective limit above 1 (N > 1, composite not serialized) uses REQ-17–REQ-27, REQ-57 and C-6; a serialized composite continues with spec 12a's one-at-a-time procedure (REQ-14) |
| Step 8 | REQ-26 measures per composite |
| Never list | "Never runs subtasks in parallel" becomes "Never runs subtasks in parallel except children of one composite under `--parallel N`, N > 1" |

### C-8 Git command forms added by this spec (each its own Bash call)

Spec 12a C-2 is canonical; this spec adds:

| Purpose | Command |
|---|---|
| Child worktree (N > 1, not serialized) | `git worktree add -b <child-branch> <worktree-path> <composite tip sha>` |
| Child commits in a worktree | `git -C <worktree-path> add <explicit paths>` then `git -C <worktree-path> commit -m "<message>"` |
| Remove worktree | `git worktree remove <worktree-path>` |

### C-9 `scripts/composite_run.py` subcommands added by this spec

The helper, its invocation, exit codes, error codes and the subcommands `--version`,
`validate`, `reconcile` and `post-merge-commands` are defined in spec 12a → C-3. This spec
adds the subcommands below; the helper is required when N > 1 (REQ-25).

| Subcommand | Arguments | Result |
|---|---|---|
| `write-set` | `--repo D --base S --tip S [--include-worktree]` | `{"paths": [...]}`: sorted unique repository-relative POSIX paths from `git diff --name-status -z -M <base> <tip>` (both rename sides) plus, with the flag, every path of `git status --porcelain=v1 -z --untracked-files=all` in D |
| `admit` | `--plan P --journal J --composite ID --limit N` | `{"active": [...], "admit": [...], "respawn": [...], "waiting": [{"id", "reason"}], "integrate_next": id or null, "done": bool}`; an admitted respawn candidate is listed in `respawn` (retry the spawn for its existing attempt) instead of `admit` (start a new attempt) |
| `check-merge` | `--plan P --journal J --composite ID --child ID --repo D` | `{"verdict": "ok" \| "scope-exceeded" \| "overlap", "paths": [...], "with": [...]}` |
| `check-handoff` | `--handoff P --journal J` | `{"verdict": "ok" \| "stale", "digest": <sha256>, "reasons": [...]}`; `stale` when `candidate_commit` ≠ `git -C <worktree> rev-parse HEAD`, a `test_files` hash differs from the file in the worktree, `previous_digest` ≠ the attempt's last recorded handoff digest, or `child`/`attempt`/`branch` differ from the journal's latest attempt |
| `next-attempt` | `--journal J --composite ID --child ID --slug S` | `{"attempt": k, "branch": ..., "worktree": ...}`: k = latest attempt + 1 (1 when none); branch per DM-7; worktree per DM-4, or `null` when the composite is serialized |
| `measure` | `--journal J` | `{"composites": [{"id", "requested_parallel", "elapsed_s", "active_sum_s", "max_concurrency", "merges", "check_failures", "serializations"}]}` |

`measure` formulas per composite, over attempts with both `dispatched_at` and `ended_at`:
`elapsed_s` = latest `ended_at` − earliest `dispatched_at`; `active_sum_s` = Σ(`ended_at` −
`dispatched_at`); `max_concurrency` = the largest number of such intervals
[`dispatched_at`, `ended_at`) containing one instant; `merges` = attempts with non-null
`merge.commit`; `check_failures` = Σ `merge.check_failures`; `serializations` = 1 if `serialized` is set, else 0. With no such attempt
the three time values are `null`.

`admit` rules, evaluated over children in `## Subtasks` row order:
0. While any attempt of the composite is `check-failed`, `admit` admits nothing,
   `integrate_next` is null and every candidate waits with `check-failed` (REQ-59).
1. Effective limit = 1 if the composite is `serialized`, else `min(--limit, capacity_limit)`
   when the composite records `capacity_limit` (REQ-71), else `--limit`.
2. A child is a candidate when it has no attempt, its latest attempt is `superseded`, or its
   latest attempt is `branched` with `spawn_refused: true` (a respawn candidate), every
   prerequisite inside the composite has its latest attempt `accepted`/`cleaned` and plan
   status `reviewed`, and every prerequisite outside the composite has plan status `reviewed`.
   Otherwise it waits with `prerequisite-failed` when a prerequisite inside the composite is
   `failed`, `blocked`, `check-failed` or `conflict`, else with `dependency-pending` (this
   covers direct and transitive dependencies).
3. A candidate with `Parallel-safe: no`, an incomplete write set, or a serialized composite is
   exclusive: it is admitted only when no child is active, nothing else is admitted in the same
   call, and no reservation-holding child exists whose planned write set is incomplete or
   intersects the candidate's (any reservation-holding child, when the candidate's own set is
   incomplete); while it is active or admitted in this call, every other candidate waits with
   `exclusive-active`. An exclusive candidate that
   cannot be admitted waits with `exclusive-wait` and is a barrier: later candidates wait with
   `barrier`.
4. Other candidates are admitted in order while the active count stays within the limit, each
   independent (REQ-05) of every reservation-holding and already admitted child; otherwise
   `write-set-overlap`, `interface-overlap` or `limit-reached`.
5. `integrate_next` = the first child in row order whose latest attempt is `validated`, when no
   earlier child's latest attempt is `branched`, `dispatched`, `merge-intent` or `merged`.
6. `done` = every child's latest attempt is `accepted` or `cleaned`.

`reconcile` rows added for attempts with a non-null `worktree`, evaluated before spec 12a's
rows:

| Journal stage | Observation | Action |
|---|---|---|
| `branched`/`dispatched` | the worktree path is absent | `redo-worktree` |
| `dispatched` | the worktree has tracked changes, or an untracked, non-ignored path outside `.ai/` that is not in `untracked_at_dispatch` (the worktree is not covered by the root's clean-tree gate) | `inspect-worker` |
| `accepted` | the worktree still exists | `cleanup-pending` |

Root actions in a parallel run (replacing spec 12a's for these attempts): `redo-worktree` —
`git worktree add <path> <branch>` when the branch exists, otherwise the C-8 `git worktree add -b`
form from the recorded `base_commit`; `redo-branch` — the C-8 form; `inspect-worker` — `blocked`
with `uncommitted-work`, reservation kept (E-21); `cleanup-pending` — REQ-58, then spec 12a
REQ-31; `none` on `branched` — spawn the leaf coordinator (REQ-20); `none` on `dispatched` —
REQ-27 agent recovery.

`check-merge`: actual write set of the child's latest attempt (`base_commit..tip`, plus the
worktree when one exists); `scope-exceeded` lists paths not in the planned write set (any
`.ai/` path is always listed); `overlap` lists paths in the actual write set of another child
whose latest attempt is active, `accepted` or `cleaned`, named in `with`; `scope-exceeded`
wins when both apply. The root calls it only when N > 1 or any attempt has a worktree (REQ-11).

### C-10 Contract-file changes added by this spec (delta to spec 12a C-5)

| File | Change |
|---|---|
| `rules/orchestration.md` | Opening paragraph: sequential except children of one composite under `--parallel N`; roles Leaf coordinator and Workflow agent; parallel-mode single writer; Implementer split in parallel mode (D-01); the "strictly sequential" sentence keeps that phrase for everything outside one composite; `### Conditions that always stop the run, regardless of class`: in parallel mode (N > 1), `atomic-tests: failed` and a sub-agent blocker of one child stop the run as REQ-24 states (once no child of the composite is active or admissible) |
| `rules/workflow-reference.md` | `### Parallel Safety` format (DM-5) |
| `rules/workflow-globals.md` | The sentence at `:106-109` becomes "Orchestrated mode is strictly sequential — no workflow may introduce concurrent subtask execution, except `/spec-run`'s children of one composite under `--parallel N`, N > 1." |
| `workflows/spec-run.md` | C-7 and C-8 rows of this spec, C-6, worktree attempts, agent recovery; the "one synthetic aggregate per subtask" sentence (`:45-46`) becomes one per attempt (REQ-02) |
| `workflows/phase-atomic-execution.md`, `workflows/phase-atomic-validation.md`, `workflows/pae-tests.md`, `workflows/pae-implement.md`, `workflows/pae-finalize.md`, `workflows/pav-check.md`, `workflows/pav-propose.md`, `workflows/pav-close.md` | Parallel-mode clause: run as one dedicated agent, request child invocations from the root (C-6), return every state write (own block included) as a delta, work only inside the given worktree; `workflows/pav-check.md` and `workflows/phase-composite-validation.md` additionally, in parallel mode, never run spec 16's `record` and return the `review` object of C-6 row 11 (REQ-55) |
| `workflows/pd-design.md` | REQ-52 re-render of `### Parallel Safety` after design |
| `workflows/pd-decompose.md` | REQ-09 subsection rendered from 20 DM-8; replace "Do not claim unsupported parallel execution" and the Execution Strategy composite sentence per DM-5 |
| `scripts/validate-contracts.sh` | No new check and no changed expression: `:1056` stays true (`rules/orchestration.md` keeps "strictly sequential" for everything outside one composite) and `:1513` stays true (`workflows/spec-run.md` keeps the same-agent resume sentence for spec 12a's one-at-a-time model); no `contract_changes` entry and no oracle change. Spec 12a's C-5 owns `:1454`, `:5456`, `:5614` |
| `scripts/README.md` | Note the added subcommands of `composite_run.py` |
| `.ai/principles/domain.md` | Terms of `## Terminology` (Implementer row: split in parallel mode) |
| `.ai/principles/architecture.md` | P4 statement updated to name the root as the single writer of parallel mode |
| `harness/claude/capabilities.md` | State that worker write restrictions are role discipline, not harness permissions (NFR-04) |
| `tests/golden/cases/composite/case.json` (spec 09 DM-1 `workflows`) | Add a `composite` case workflow entry with `entry: "spec-run"` and `parallel: 2` (its prompt contains `--parallel 2`; the key may differ from `entry`, for example `spec-run-parallel-2`) for REQ-15, with the reference 09 requires for a case workflow |
| `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `workflows/PIPELINE.md` | `--parallel` |
| `.ai/adr/NNNN-…` | One new ADR superseding ADR-0004 Decision 3 for children of one composite and ADR-0004 Decision 1 for parallel mode (D-01); spec 12a's ADR records the branch model |

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
| 4 | workflow agent → root (final report) | Workflow report: changed paths, test files, observed command and result, deltas, and `"worktree_unwritable": true` when its edit tool refused a worktree path (REQ-72) | REQ-11, checkpoint commit, REQ-22 handoff, apply deltas; reply to the phase agent `{"stage-done": <workflow>, "handoff_digest", "verdict"}` |
| 5 | phase agent → root (final report) | `{"phase-done": "execution", "result": "complete" \| "blocked" \| "failed", "reason"}` | Forward to the coordinator |
| 6 | coordinator → root | `{"request": "phase", "workflow": "phase-atomic-validation"}` only after a `complete` execution phase or, under spec 12a REQ-54, after the root reports a finished repair (row 10) | Spawn validation phase agent; it requests `pav-check`, `pav-propose`, `pav-close` as in row 3 |
| 7 | phase agent → root (final report) | `{"phase-done": "validation", "verdict": "DONE" \| "NEEDS WORK", "composite_ready": <id or null>}` | Apply deltas; journal `validated`, or on NEEDS WORK `failed` (or, under spec 12a REQ-54, keep `dispatched` and run the repair); forward to the coordinator, which ends unless a repair runs, in which case it requests a validation phase again after the repair |
| 8 | root → coordinator and root → its live phase agent | `{"stop": <reason>}` (REQ-04, REQ-14, REQ-27) | The phase agent lets its running workflow agent finish, requests nothing more and sends its final report; the coordinator replies `{"stopped": <last stage-done workflow>}`; a running `repair` workflow agent finishes the same way and starts no recheck (REQ-04, spec 12a REQ-54) |
| 9 | root → coordinator or workflow agent | `{"status?": true}` (REQ-27) | Reply `{"status": <current workflow or "idle">}`. One status round is one such message to every probed agent followed by one collection of replies after all messages are sent; an agent that has not replied at that collection, and that the harness has not reported unknown or finished, is `unknown` |
| 10 | root → coordinator | `{"repair-done": <episode key>, "handoff_digest": <sha256>}` after the root spawned the `/pae-repair` workflow agent (REQ-21, spec 12a REQ-54), applied its deltas, committed 19's checkpoints and built the DM-6 handoff with stage `repair` | Journal `agents.workflows` (the repair agent); the coordinator then sends row 6 |
| 11 | review agent → root (final report): the `/pav-check` workflow agent, the Validator of a serialized composite's child (final report only, no phase agent) or the spec 12a REQ-12 composite validation agent | The row 4 report plus `"review": {"draft": {"level", "step", "scope_key", "options": {the `prepare` options as C-1 of spec 16 names them}, "record": <spec 16 DM-7 draft object>} \| null, "none_reason": null \| "unavailable" \| "disabled" \| "helper-error" \| "multi-repository" \| "blocked"}`; `draft` is null only with a `none_reason` (spec 16 DM-8 reasons) | REQ-55, REQ-56: write the draft file, run `record`, then apply the verdict and notes deltas and append the `verification:` entry from the `record` result; or append the `none` entry |
| 12 | root → phase agent (reply replacing row 4's after a review report that REQ-56 handles) | `{"stage-redo": "pav-check", "record": "refused" \| "unusable" \| "error", "reasons": [<spec 16 refusal reasons, `draft-invalid` for an unusable draft, or the `record` error code for exit 2, 3 or 4>], "helper": "on" \| "off"}` | The phase agent requests `pav-check` again (row 3); the root spawns the fresh agent with `reasons` and `helper`; the composite validation agent and the Validator of a serialized composite's child have no phase agent, so the root respawns them directly with the same fields |

Messages that do not match the expected next row for the attempt are ignored and recorded in the
journal attempt as `unexpected_messages` (count); a second report for the same workflow with the
same handoff digest is a duplicate and ignored (E-33).

## Non-Functional Requirements

Spec 12a NFR-01 (determinism, also for this spec's subcommands), NFR-02, NFR-03, NFR-05 and
NFR-06 apply unchanged.

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-04 | Least privilege | Worker write restrictions are role discipline, not enforced by harness permissions; the capability record says so (P11) | AC-56 |
| NFR-08 | Performance | N/A — no speedup, token or cost target (README gate G8; ADR-0009 Decision 5); only measurement per REQ-26 (renumbered from NFR-07, which spec 12a keeps) | — |

## Edge Cases & Failure Modes

| # | Case | Expected behaviour | REQ |
|---|---|---|---|
| E-01 | `--parallel 0`, `-1`, `1.5`, `two`, `--parallel=` | Stop before any write | REQ-29 |
| E-02 | `--parallel 1` | Sequential per-composite model, no capability or helper check beyond today's | REQ-29, REQ-25 |
| E-03 | N > 1 on Codex or with any capability key absent/unknown | Stop, name missing keys, no write | REQ-25 |
| E-04 | `ORCHESTRAIL_HOME` unset, helper missing, Python < 3.11 or no runbook test command, with N > 1 | Stop with the missing item; N = 1 needs none of them | REQ-25 |
| E-06 | All children `Parallel-safe: no` or no `### Parallel Safety` | Children run one at a time; effective concurrency 1 recorded | REQ-09, REQ-18 |
| E-07 | Child write set names a directory or glob | Row must be `no`; admitted alone | REQ-09, REQ-19 |
| E-08 | Two children rename to/from the same path | Overlap; not admitted together | REQ-05 |
| E-09 | Child changes a lockfile or generated file not in its write set | `scope-exceeded` → serialization | REQ-11, REQ-14 |
| E-10 | Worker writes under `.ai/` in its worktree | `scope-exceeded` → serialization; the change is never committed | REQ-11 |
| E-12 | Textual merge conflict | `merge --abort`, `conflict`, serialization, new attempt from current tip | spec 12a REQ-36, REQ-14 |
| E-13 | Rework attempt's new RED test already passes | `/pae-tests` stops under `tdd` (a new test passing before implementation stops and reports); no fabricated RED | spec 12a REQ-41 |
| E-14 | Child NEEDS WORK while siblings are independent | Attempt `failed`, reservation kept; siblings continue; dependents wait `prerequisite-failed`; run stops when nothing is active or admissible; resumes per spec 12a REQ-50 after the owner clears `blocker:` | REQ-24, spec 12a REQ-50 |
| E-15 | Class-B question or tripwire in one child | Broad stop: no admissions, stop sent to all coordinators | REQ-04 |
| E-16 | Spawn refused for capacity | Attempt stays `branched` with `spawn_refused`; `capacity_limit` recorded; retried when a slot frees; with no other active child the attempt is `blocked` (`blocker`, detail `spawn refused by the harness`) and the run stops | REQ-71 |
| E-20 | Coordinator `gone` after restart (the harness reports the identity unknown), clean worktree | Redispatch from the last verified checkpoint with fresh agents | REQ-27 |
| E-20a | Coordinator status message neither answered nor rejected (`unknown`) | Child `blocked` with `liveness-unknown`, reservation kept; no redispatch | REQ-27 |
| E-21 | Coordinator `gone`, dirty worktree | Child `blocked` with `uncommitted-work`, reservation kept; owner reconciles the paths | REQ-27 |
| E-53 | Composite integration validation NEEDS WORK, fix sibling approved, N > 1 (split from spec 12a E-31) | The fix sibling is a new child admitted under REQ-18; composite validation runs again on the new tip (spec 12a REQ-67) | REQ-18 |
| E-24 | `git worktree remove` refuses (dirty or locked) | Keep worktree and branch; record; continue | REQ-58 |
| E-55 | The worktree probe leaves untracked build or cache files | Composite serialized with `worktree-probe` | REQ-49 |
| E-56 | A superseded attempt's worktree holds changes at composite completion | Worktree and branch kept and reported in Step 8; the journal is kept | REQ-70 |
| E-57 | Resume with N = 1 while worktree attempts are active | They continue with C-6; helper and preflight still required; no new admission above the limit | REQ-10, REQ-25 |
| E-32 | Two agents return at the same moment | Root applies their deltas one after another; second re-reads the target section first (spec 15 REQ-18 derived proposal when the delta was composed against an older state) | REQ-01 |
| E-33 | Duplicate delivery of a worker result | Same handoff digest → ignored; different content for the same stage → stage blocked | REQ-22 |
| E-34 | Provider limit during a parallel run | Treated as a blocker of that child; no account switch | REQ-24 |
| E-36 | Worktree probe exit codes differ, or a workflow agent reports its edit tool refuses the worktree path | Composite serialized (`worktree-probe`), or child `blocked` with `worktree-not-writable` and then serialized; remaining children run in the root worktree | REQ-49, REQ-72, REQ-14 |
| E-37 | `--parallel 3` on a task that recorded per-leaf branches | Stop before any write | REQ-48 |
| E-38 | Resume with a different N than the journal's `requested_parallel` | New N applies to new admissions; existing attempts continue in their recorded location with the agent model they started with; while any attempt has a worktree, REQ-11, REQ-25's helper and preflight checks and C-6 apply even when the new N is 1 (C-6 for worktree attempts, which needs only the sub-agent and messaging support `/spec-run` already requires, `workflows/spec-run.md:16`); N > 1 repeats the preflight | REQ-29, spec 12a REQ-13 |
| E-40 | A child depends on a top-level leaf before its composite | Satisfied by that leaf's plan status `reviewed` (it is already in the composite base) | REQ-18 |
| E-41 | Tracked `.ai/` state edited by the root while children run (N > 1) | Committed on the composite branch as `chore: update task records` before each merge; merges never touch `.ai/` because children may not | REQ-68, REQ-11 |
| E-42 | A worker result arrives that does not match the expected next C-6 row | Ignored and counted; the attempt waits for the expected message | REQ-22 |
| E-44 | Exclusive candidate while a sibling is `failed` with an intersecting reservation | Waits `exclusive-wait`; the run stops when nothing is active or admissible | REQ-18, REQ-24 |
| E-45 | Root-run test commands (probe, post-merge checks) while an exclusive child that uses a fixed port or shared database is active | Cannot occur: an exclusive child is admitted only when no child is active (so no other child is `validated` or awaiting a probe), nothing is admitted while it is active, its own probe runs before its agents start, and its post-merge checks run after its agents have ended. Children that are not exclusive use no exclusive resource (DM-5) | REQ-18, REQ-49, spec 12a REQ-03 |
| E-47 | The root restarts between a `pav-check` report and the end of its REQ-55 handling | No record or entry was applied before the report was handled; the attempt is still `dispatched` (REQ-27), the validation phase is requested again and the correction budget of REQ-56 starts anew; a record `record` published just before the restart stays, the re-review publishes the next record, and the missing `verification:` entry makes spec 16's next preparation a full scope (`prior-not-latest`, 16 REQ-12) | REQ-55, REQ-27 |

## Acceptance Criteria

Verification vehicles (test-first, written and observed failing before implementation):
**[C]** contract checks in a new standalone `scripts/check-composite-branch-model.sh` (shell
builtins, like `scripts/check-spec-draft.sh`): each [C] criterion names the exact sentence or
anchored line the check matches, and the check fails on the unchanged files; **[H]** helper and
hook fixtures in a new standalone `scripts/check-composite-run.py` (Python standard library,
`unittest`) using disposable git repositories, journals and plans; **[G]** the existing
`tests/git-rails.sh` (one replaced test, spec 12a C-4); **[L]** an owner-approved live spec 09 run, never
part of ordinary validation. Agent behaviour that only a live run can show (actual concurrency,
agent identities in a real session) is covered by [C] for the instruction and [L] for the
behaviour.

- [ ] **AC-01** (REQ-01, REQ-02, REQ-28) [C] Given the changed files, then `rules/orchestration.md`
  contains "In a parallel run the root is the only writer of `.ai/` and of the composite
  journal; agents return every state write as a delta." and `workflows/spec-run.md` contains
  "Write one per-subtask aggregate for each attempt when it first reaches an end stage." and
  "Give an agent only its own child's description, handoff and worktree; never another child's
  transcript, report or handoff."
- [ ] **AC-39** (REQ-59) [H] Given a journal after a failing post-merge check (`check-failed`,
  `merge.check_failures: 1`), when `admit` runs, then it returns no admission and
  `integrate_next: null`, and `measure` reports `check_failures: 1`; given the same journal after
  a passing rerun (`accepted`), `admit` resumes admissions. (Split from 12a AC-02.)
- [ ] **AC-03** (REQ-05) [H] Given fixture plans and an empty journal, when `admit --limit 2`
  runs, then two children with disjoint complete write sets and no interface or dependency
  link are both admitted; and each of these pairs yields exactly one admission with the stated
  reason for the other: a shared path (`write-set-overlap`), a rename touching the other's path
  (`write-set-overlap`), `produces: x` vs `consumes: x` (`interface-overlap`), a direct or
  transitive dependency (`dependency-pending`), `Parallel-safe: no` on the first
  (`exclusive-active` for the second).
- [ ] **AC-06** (REQ-09, REQ-10, REQ-29) [H][C] Given `admit --limit 2` over four eligible
  independent children, then exactly two are admitted and two wait with `limit-reached`; given a
  serialized composite, then no call admits a child while another is active; and [C]
  `workflows/spec-run.md` contains `^[1-9][0-9]*$` and the REQ-29 stop message verbatim, and
  `workflows/pd-decompose.md` contains the DM-5 table header.
- [ ] **AC-07** (REQ-11, REQ-14) [H] Given a child whose actual diff touches a path outside its
  reservation, another whose diff touches a path already in an accepted sibling's actual write
  set, and a third that writes `.ai/x.md` in its worktree, when `check-merge` runs, then the
  verdicts are `scope-exceeded`, `overlap` (naming the sibling in `with`) and `scope-exceeded`;
  and given a journal with `serialized` set and one `validated` attempt whose `check-merge` is
  `ok`, `admit` returns it as `integrate_next` and admits nothing while it is active.
- [ ] **AC-10** (REQ-15) [L] Given owner-approved spec 09 `composite` golden runs with
  `--parallel 1` and `--parallel 2`, when `scripts/check-composite-run.py` compares the structural
  assertions of the two spec 09 expected projections (normalized by spec 09's rules), then they
  are equal except aliased hashes, branch names and timestamps. Not
  required for deterministic acceptance.
- [ ] **AC-43** (REQ-57, REQ-22) [C] Given the changed `workflows/spec-run.md`, then it contains
  "In a worktree, commit `test:` before the implementation commit for `red` and `pinned`, make
  one implementation commit for `n-a`, and keep the legacy note; a new attempt never fabricates
  RED." (Split from 12a AC-12.)
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
  it contains the C-6 table rows 1–12, "Spawn one fresh leaf coordinator per attempt and one
  fresh agent per phase and workflow invocation.", "Commit the checkpoint in the worktree
  before dispatching the next workflow." and "A `stale` handoff blocks the next workflow."; and
  given a handoff whose `candidate_commit` differs from the worktree HEAD, whose test-file hash
  differs, or whose `previous_digest` breaks the chain, `check-handoff` returns `stale` with the
  matching reason, and `ok` for an unmodified handoff.
- [ ] **AC-16** (REQ-17, REQ-18, REQ-24, REQ-04) [H][C] Given a composite where child A is
  `failed`, B depends on A and C is independent of A, then `admit` admits C, keeps B waiting
  `prerequisite-failed`, and `done` stays false; and [C] `workflows/spec-run.md` contains "On a broad stop, admit no new child, send every
  active coordinator a stop and stop the run." and "A failed child keeps its reservation; stop
  the run when no child of the composite is active or admissible." with `atomic-tests: failed`
  in that trigger list; and `rules/orchestration.md → ### Conditions that always stop the run,
  regardless of class` contains "In a parallel run, `atomic-tests: failed` and a sub-agent
  blocker of one child stop the run only when no child of the composite is active or
  admissible."
- [ ] **AC-17** (REQ-25, REQ-27) [C] Given the changed `workflows/spec-run.md`, then it contains
  the five capability keys `sub-agents`, `agent-messaging`, `git`, `worktrees`,
  `concurrent-sub-agents`, the REQ-25 stop message verbatim, "Send a status message to the
  coordinator and to every workflow agent not reported finished." and "Redispatch only a
  `gone` attempt whose `reconcile` action is `none`."
- [ ] **AC-18** (REQ-18, REQ-19, REQ-26) [H] Given a fixture modelled on the example plan of
  17.4 where four children name `scripts/validate-contracts.sh` in their write sets, then
  `admit` never returns two of them together; and given a journal with three attempts whose
  intervals are [10:00, 10:30), [10:10, 10:40) and [10:50, 11:00), `measure` reports
  `elapsed_s: 3600`, `active_sum_s: 4200`, `max_concurrency: 2`, and `null` time values for a
  composite without a complete interval; and an attempt set `superseded` gets `ended_at` and is
  counted.
- [ ] **AC-20** (REQ-28) [C] Given the changed `workflows/spec-run.md`, then it contains "Pass
  the root worktree's absolute `.ai/` path as read-only context; never edit the worktree copy of
  `.ai/`."
- [ ] **AC-21** (REQ-38) [C] Given the changed `workflows/spec-run.md`, then it contains "With
  `--dry-run --parallel`, report the resolved N, the preflight result, each composite's
  `### Parallel Safety` rows and the first `admit` result; create no branch, worktree, journal
  or state write."
- [ ] **AC-22** (REQ-57) [H] Given the C-8 forms in a disposable repository with N = 2, then each
  worktree path equals `next-attempt`'s `worktree`, the root worktree's `git status --porcelain`
  stays empty, and for a child with one `superseded` attempt `next-attempt` returns attempt 2
  and branch `<composite>--<slug>-attempt-2`.
- [ ] **AC-42** (REQ-48) [C] Given the changed `workflows/spec-run.md`, then it contains the
  REQ-48 stop message verbatim before any branch creation step. (Split from 12a AC-28.)
- [ ] **AC-31** (REQ-49) [C] Given the changed `workflows/spec-run.md`, then it contains "Run the
  runbook `test:` command at the attempt's `base_commit` in the new worktree and in the root
  worktree before dispatch; when the exit codes differ or the probe leaves tracked changes or
  new untracked files, supersede the attempt and serialize the composite with `worktree-probe`."
  and names no setup command.
- [ ] **AC-40** (REQ-62, REQ-24) [H][C] Given a journal whose child attempt has a worktree and was
  set back to `dispatched` under spec 12a REQ-50, when `admit` runs, then it counts the attempt
  as active (it occupies a slot); and `workflows/spec-run.md` contains
  `blocker: <blocked_reason>: <one-line detail>` and "Restart an owner-cleared attempt that has
  a worktree in that worktree." (Split from 12a AC-32.)
- [ ] **AC-33** (REQ-18) [H] Given child A `failed` with planned write set {x} and exclusive
  candidates B (`Parallel-safe: no`, write set {y}), C (`Parallel-safe: no`, write set {x}) and D
  (write set containing a directory) in that row order, with no active child, when
  `admit --limit 2` runs, then B is admitted alone and C and D wait `exclusive-active`; in a second fixture without B, C waits `exclusive-wait` and D waits `barrier`; and
  in a third fixture with A `cleaned` and D as the only candidate, D is admitted alone.
- [ ] **AC-35** (REQ-09, REQ-52) [C] Given the changed files, then `workflows/pd-decompose.md`
  contains the DM-5 table header and "Write `Parallel-safe: no` when `disqualifiers` is
  non-empty, the write set is incomplete, an exclusive resource is needed or any independence
  condition is unproven.", and `workflows/pd-design.md` contains "Re-render `### Parallel
  Safety` after design; never change the row of a child that has started."
- [ ] **AC-41** (REQ-63) [C] Given the changed `workflows/spec-run.md`, then it contains "In a
  parallel run, a repaired attempt keeps its slot and reservation; after an accepted repair,
  check overlap again; on a broad stop, start no further repair and let a dispatched repair
  worker finish; copy the episode key on supersession; run `/pae-repair` as one fresh workflow
  agent with a `repair` handoff." (Split from 12a AC-37.)
- [ ] **AC-38** (REQ-55, REQ-56, REQ-01) [C] Given the changed files, then `workflows/pav-check.md`
  and `workflows/phase-composite-validation.md` each contain "In a parallel run, never run
  `record`; return the draft in the report's `review` object.", `workflows/pav-check.md` also
  contains "Outside a parallel run, the Validator runs `record` itself.", `rules/orchestration.md`
  contains "In a parallel run the root runs `record` on a returned review draft.", and
  `workflows/spec-run.md` contains the C-6 rows 11 and 12, "Run `record` on the returned draft
  before applying any other delta of the report.", "Write the draft to
  `<task>/verification/drafts/<scope key>-attempt-<k>.json` of the root worktree after checking
  `--work`, `--task` and `--ai-dir`.", "Apply the verdict and notes deltas only after `record`
  publishes, then append the `verification:` entry from its result.", "A `draft: null` report
  appends the `none` entry." and "An unusable draft or exit 1 gets one correction spawn with the
  reasons; a second failure or exit 2, 3 or 4 gets one spawn with `\"helper\": \"off\"`; a
  further failure blocks the attempt with `record-failed`." (Spec 12a depends on none of it.)
- [ ] **AC-44** (REQ-58) [H][C] Given a journal with an `accepted` attempt whose worktree still
  exists and whose `cleanup.failure` is null, when `reconcile` runs, then it returns
  `cleanup-pending`; and `workflows/spec-run.md` contains the C-8 `Remove worktree` form verbatim
  and "Remove the worktree, never with `--force`, before deleting the child branch; record a
  failure once and never retry it."
- [ ] **AC-45** (REQ-61) [C] Given the changed `workflows/spec-run.md`, then its Step 8 contains
  "Delete the task's handoff directory together with the composite journal."
- [ ] **AC-46** (REQ-60, REQ-14) [H][C] Given two child branches of one composite that conflict
  textually in a disposable repository with N = 2, when the spec 12a C-2 merge and abort are
  applied and the journal is updated, then the composite tip equals `merge.expected_target`, the
  conflicting attempt's stage is `conflict` with its worktree kept, the composite is
  `serialized`, and `admit` admits nothing while another child is active; and
  `workflows/spec-run.md` contains "With an effective limit above 1, a merge conflict serializes
  the composite instead of stopping the run."
- [ ] **AC-51** (REQ-27) [H] Given journals with worktree attempts — `branched` with the worktree
  path absent, `dispatched` with a tracked change in its worktree, `dispatched` with a new
  untracked file in its worktree, `accepted` with its worktree present — when `reconcile` runs,
  then it returns `redo-worktree`, `inspect-worker`, `inspect-worker` and `cleanup-pending`
  respectively.
- [ ] **AC-52** (REQ-68) [C] Given the changed `workflows/spec-run.md`, then it contains "In a
  parallel run, keep the root worktree on the composite branch and commit pending tracked task
  records there before each child merge, before and after composite validation, and before a
  stop." and "A serialized composite commits task records as the one-at-a-time procedure
  does."
- [ ] **AC-53** (REQ-69) [C] Given the changed `workflows/spec-run.md`, then, in the passage
  conditioned on spec 14's `packet`, it contains "For an attempt with a worktree, pass that
  worktree as `--work`."
- [ ] **AC-54** (REQ-71) [H] Given a journal where one child's coordinator spawn was refused
  (`spawn_refused: true`, `capacity_limit: 1`) and one other child is active, when `admit
  --limit 3` runs, then it admits nothing; after the active child becomes `accepted` and
  `capacity_limit` is cleared, it returns the refused child in `respawn` and not in `admit`.
- [ ] **AC-55** (REQ-72) [C] Given the changed `workflows/spec-run.md`, then it contains
  `"worktree_unwritable": true` and "Set the attempt `blocked` with `worktree-not-writable` and
  serialize the composite."
- [ ] **AC-56** (REQ-01) [C] Given the changed files, then `rules/orchestration.md` and
  `harness/claude/capabilities.md` each contain "Worker write restrictions in a parallel run are
  role discipline, not harness permissions." (NFR-04)
- [ ] **AC-57** (REQ-70) [C] Given the changed `workflows/spec-run.md`, then it contains "Remove a
  superseded attempt's clean worktree, never with `--force`, keep its branch and report both in
  Step 8." and "Keep the composite journal while a superseded attempt still has a
  worktree."

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-38, AC-56 |
| REQ-02 | AC-01 |
| REQ-04 | AC-16 |
| REQ-05 | AC-03 |
| REQ-09 | AC-06, AC-35 |
| REQ-10 | AC-06 |
| REQ-11 | AC-07 |
| REQ-14 | AC-07 |
| REQ-15 | AC-10 |
| REQ-17 | AC-13, AC-16 |
| REQ-18 | AC-13, AC-16, AC-18, AC-33 |
| REQ-19 | AC-14, AC-18 |
| REQ-20 | AC-15 |
| REQ-21 | AC-15 |
| REQ-22 | AC-15, AC-43 |
| REQ-23 | AC-13, AC-14 |
| REQ-24 | AC-16, AC-40 |
| REQ-25 | AC-17 |
| REQ-26 | AC-18 |
| REQ-27 | AC-17, AC-51 |
| REQ-28 | AC-01, AC-20 |
| REQ-29 | AC-06 |
| REQ-57 | AC-22, AC-43 |
| REQ-58 | AC-44 |
| REQ-59 | AC-39 |
| REQ-60 | AC-46 |
| REQ-38 | AC-21 |
| REQ-61 | AC-45 |
| REQ-48 | AC-42 |
| REQ-49 | AC-31 |
| REQ-62 | AC-40 |
| REQ-52 | AC-35 |
| REQ-63 | AC-41 |
| REQ-68 | AC-52 |
| REQ-69 | AC-53 |
| REQ-70 | AC-57 |
| REQ-71 | AC-54 |
| REQ-72 | AC-55 |
| REQ-55 | AC-38 |
| REQ-56 | AC-38 |

## Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-1 | Agents do not follow role discipline (a worker edits `.ai/` or runs git) | Corrupted shared state or unrecorded commits | Medium | Root-only staging of explicit paths; REQ-11 actual write sets include worktree changes; hook rails; capability record states the limit (NFR-04) |
| R-7 | Number of agents per child (coordinator plus up to eight workflow agents) exhausts harness capacity | Effective concurrency below N | Medium | Spawn refusal is recorded and the child waits (E-16); REQ-26 reports effective concurrency |
| R-9 | Parallelism is later widened beyond one composite (D-04 defers it to a possible successor specification) | Scheduler scope widens; branch model for top-level leaves changes | Medium | Scheduler rules are expressed over a dependency graph and reservations, so widening is additive; the branch model for top-level work is left untouched |

## Assumptions

- A-01 | Scope of parallelism | Resolved: only children of one composite run concurrently; top-level leaves and children of different composites keep the sequential stack; the 2026-11-06 owner widening (across composite boundaries and of top-level leaves) was deferred by the owner on 2026-11-14 (D-04, Q-01 resolved) and is out of scope | Source: ADR-0009 Decision 4 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:154-156`); spec 20 REQ-07 keeps the sequential top-level stack; D-04 | Reversible: yes (a successor specification, `## Notes → ### Successor path`)
- A-02 | `--parallel` semantics | Resolved: no flag → N = 1; `--parallel` → 2; `--parallel N` → N; positive integers only | Source: original §2 and §6.1; ADR-0009 Decision 4 "Default `--parallel 2`" read as the flag's default value | Reversible: yes
- A-06 | Worktree location | Resolved: under `<git-common-dir>/orchestrail-worktrees/` | Source: existing pattern of run records under the common directory (`workflows/restack.md:12-15`); disposable-repository verification of 2026-11-13 (DM-4) | Reversible: yes
- A-29 | Repair worker on a broad stop (added 2026-11-14) | Resolved: a spec 12a REQ-54 repair worker already dispatched when REQ-04 stops the run is not interrupted and not duplicated: it finishes, its result is recorded through spec 19's `outcome` step, no new repair attempt or recheck starts and the episode stays open; this adopts 19 C-10 row 12 and is consistent with C-6 row 8, where a stopped phase agent lets its running workflow agent finish | Source: spec 19 C-10 row 12; REQ-04 and C-6 row 8 of this spec | Reversible: yes
- A-10 | Conflict handling | Resolved: `git merge --abort`, then serialization; the child branch keeps all commits | Source: original §10 (conflict disproves independence; preserve work; no forced reset); `/restack` aborts are already accepted forms (`workflows/restack.md:96-98`) | Reversible: yes
- A-15 | Separate test and implementation agents | Resolved: in parallel mode only (D-01); N = 1 keeps the one-Implementer two-checkpoint handoff | Source: original §8.2 and REQ-21 explicitly supersede the same-agent rule for the new mode | Reversible: yes
- A-16 | Nested delegation | Resolved: root-mediated dispatch is the specified path: the root spawns every coordinator, phase and workflow agent, and coordinators and phase agents request invocations by message (C-6) | Source: original REQ-25 permits it; smallest choice independent of whether sub-agents can spawn sub-agents | Reversible: yes
- A-17 | Platform agent capacity | Resolved: not declared anywhere; a refused spawn is the observed limit (E-16); no number is invented | Source: original REQ-23; README G1/G4 | Reversible: yes
- A-35 | Dependence on specs 14, 15, 16, 19 not yet delivered, parallel mode (split from spec 12a A-18) | Resolved: before each is delivered, workers bootstrap context themselves (existing rule), deltas use the existing report route, checks are those of spec 12a REQ-03, and no repair attempt is made (NEEDS WORK stops per REQ-24/spec 12a REQ-51). Once delivered: 14 → the root builds packets per spec 12a REQ-53 (14 C-8); 15 → handoff digests per 15 REQ-41; 16 → receipts per spec 12a A-28; 19 → repair per spec 12a REQ-54 when its policy is passed; 16 → at N > 1 the root writes review records from returned drafts per REQ-55 and REQ-56 | Source: README prerequisites row for 12 (`.ai/specs/README.md` → "Dependency order"); G4 conservative path; peer contracts named | Reversible: yes
- A-36 | Telemetry in parallel mode (split from spec 12a A-19) | Resolved: no new run-log fields; one aggregate per attempt; measurements come from the journal through `measure` | Source: spec 02/05 own the run-log contract; P9 (durations never model-written) | Reversible: yes
- A-37 | Bounded waits (2026-11-16) | Resolved: one further status round (C-6 row 9: one message per agent, one collection of replies) after a stop; no reply means `unknown` | Source: original REQ-27 (never duplicate a live invocation); smallest conservative choice without a numeric timeout | Reversible: yes
- A-38 | Disposal of superseded attempts (2026-11-16) | Resolved: clean worktrees removed, branches kept and reported; the journal is kept while a worktree remains | Source: original §10 step 10 (keep earlier branches until proven integrated or decided); 12a REQ-31 deletes only verified integrated branches | Reversible: yes
- A-22 | Liveness of agents after a restart | Resolved: a status message to the recorded identity; the harness's unknown-identity answer means `gone`; anything else that is not a reply means `unknown` and blocks | Source: original REQ-27 ("never duplicate a live invocation"); smallest conservative choice | Reversible: yes
- A-23 | Resource locks and ordering constraints of the original | Resolved: no separate lock mechanism; a child needing an exclusive resource or named by an ordering constraint is `Parallel-safe: no` and runs exclusively | Source: original §17.3 (host-exclusive checks "apply globally") and REQ-05; exclusivity is the smallest rule that needs no new runtime | Reversible: yes
- A-26 | Worktree tooling risk | Resolved: keep DM-4 for hook coverage; a probe (REQ-49) serializes the composite when the worktree behaves differently | Source: hook registry prefix matching (`hooks/git_rails.py:330`); best practice | Reversible: yes
- A-27 | Effort for parallel-mode spawns | Resolved: parallel-mode spawns (leaf coordinators, phase agents and workflow agents) are outside spec 18's policy version 1 and keep today's dispatch behaviour: no resolver call, no effort parameter and no `## Effort Decisions` line for them; the `/pae-tests` and `/pae-implement` agents take the leaf's model resolution of `workflows/spec-run.md` Step 2 like an Implementer, and every other parallel-mode agent uses the session default like the Validator. This delivery adds no effort handling itself. Bringing them under the policy is a later revision of 18 triggered by this delivery (18 A-29): it adds the roles leaf coordinator, phase agent and workflow agent and the stages `tests`, `implement`, `finalize`, `check`, `propose`, `close` to 18 DM-2/DM-6 and names the root as the only writer of `## Effort Decisions` in 18 C-4. The `repair` stage (spec 12a REQ-54) is not in that list: it stays with spec 19's own route (19 C-8) | Source: spec 18 C-6 row 12 and its A-14, A-29; `workflows/spec-run.md:126-131` | Reversible: yes

## Decisions

- D-03 | After serialization, a validated attempt is integrated only when `check-merge` is `ok`; every other non-accepted attempt is superseded and redone; no partial evidence is carried over | Overrides: none (narrows original §10 step 8, which permitted reuse after a currency check) | Rationale: the currency check of evidence belongs to specs 14/16, which are not delivered; redoing is the smallest safe choice | Follow-up: revisit when 14/16 land
- D-01 | In parallel mode, `/pae-tests` and `/pae-implement` run in distinct fresh agents, with the root committing the test checkpoint and passing a verified handoff | Overrides: ADR-0004 Decision 1 rejected alternative "Tests and implementation in separate agents" (`.ai/adr/0004-task-unknown-sequential-orchestration-context-roles.md:46-47`) and `rules/orchestration.md:58-61`, for parallel mode only | Rationale: authorized by the source (original §8.2 and REQ-21: "This supersedes the existing same-agent RED-to-GREEN rule for this mode; implementation must record the decision") | Follow-up: the superseding ADR of C-10
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
  REQ-18, REQ-24 and REQ-26, and AC-16 and the original AC-19 as originally worded.
  Resolved 2026-11-14: option (a) — parallelism only within one composite (D-04). The
  cross-composite and top-level-leaf parts are out of scope; the materialized-stack option (b) is
  the named successor path (`## Notes → ### Successor path`); option (c) stays rejected. No
  longer a blocker.
- **Q-03 (resolved, non-blocker)** | Who writes spec 16's review records (`<task>/verification/reviews/`,
  16 DM-1, written by its `record` step from `/pav-check` and the review workflows) in parallel
  mode, where REQ-01 makes the root the only writer under `.ai/`? Worker-written `notes:` entries
  (14 DM-11, 16 DM-8, 17 DM-9) are already covered: they are returned as deltas under REQ-01 and
  appended by the root with 14 DM-11's append rule. No source decides the record file write; 16
  assumes the reviewing workflow writes it. Recommended: the workflow agent returns the 16 record
  draft in its report and the root runs 16's `record` against the root worktree's task directory
  in REQ-01's sequential order; workflow agents never invoke `record`. Impact: REQ-01, the C-6
  report fields and A-35; N = 1 is unaffected.
  Resolved 2026-11-14: the recommendation was accepted — the root orchestrator runs `record` on
  the review draft that the agent returns (D-05; REQ-55, REQ-56, C-6 rows 11 and 12, AC-38, E-47).

## Notes

### Constraints

- Every git write is a separate Bash call (policy, spec 12a C-2).
- No pipeline identifier reaches branch names, commits or PR text (`rules/git-flow.md:129-154`);
  the journal and handoffs live in the git common directory and are never committed.
- `.ai/` tracking policy is unchanged; untracked consumer state is never staged
  (`rules/git-flow.md:156-165`).
- Contract changes follow `.ai/principles/coding.md → Changing a contract`: failing check first,
  canonical definition, readers, ADR.
- The validator's check inventory is not extended and no check expression changes (C-10); a
  change to `scripts/sync.sh`, `tests/` or the validator body is followed by the re-pin procedure
  of `tests/fixtures/validator-runtime/README.md`.

### Delivery size

Hint (nonbinding): about eight subtasks — (1) helper scheduler subcommands with fixtures;
(2) `### Parallel Safety` record in `/pd-decompose` and `/pd-design`; (3) flag, preflight and
dry run; (4) worktree lifecycle, probe, reconcile rows and serialization; (5) agents, handoffs
and the C-6 protocol; (6) recovery, failure isolation, broad stop and spawn refusal; (7) review
records (REQ-55, REQ-56); (8) rules, documentation, golden case and ADR.

### Successor path

Recommended order (D-04): deliver spec 12a, then this spec, measure on real tasks (REQ-26), and only then
consider a separate successor specification for a "materialized stack": independent top-level
items run concurrently, and the stack branches are built afterwards in plan order. It is not
part of this specification. It would need ADR-0009 Decision 4 superseded and the stack rule in
`rules/git-flow.md → ## Branch model — the stack` changed. Widening is additive for this
spec's scheduler because admission works on the dependency graph (R-9); the branch model for
top-level work stays untouched here.

### Follow-up changes outside this spec

- Spec 09: its branch-ancestry facts for a `per-composite` run are in spec 12a → Notes; with
  N > 1 the `base_commit` of a child is a descendant of, or equal to, the `merge_commit` of each
  of its prerequisites in the same composite.
- Spec 13: none — the five capability names of REQ-25 and the `state: yes` record form follow
  13 DM-4, and the preflight and its stop message, including the next step it names for each
  missing key, are those of 13 REQ-37; this spec restates no wording of it.
- Spec 15: none — it carries handoff digests (15 REQ-41) and its derived-proposal rule (15 REQ-18)
  covers E-32.
- Spec 18: none from this delivery, which adds no effort handling (A-27). A later revision of 18 (18 A-29), triggered by this delivery, adds the three parallel-mode roles and the stages `tests`, `implement`, `finalize`, `check`, `propose`, `close` to its DM-2/DM-6, with the root as sole writer of `## Effort Decisions` in its C-4; the `repair` stage stays with 19's route.
- Spec 19: none — its spec-12 row in 19 C-10 is wired by spec 12a REQ-54.
- Spec 20: none — DM-8 supplies the evidence REQ-09 and REQ-52 render.
- Specs 14, 17: none — wired by spec 12a REQ-53 and the DM-6 note respectively.
- Spec 16: none — its REQ-62 and its C-4 `Record:` line already carry the resolved Q-03 (`.ai/specs/16-scoped-verification.md:601-617`, `:1026`).

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

#### 2026-11-16 — split into spec 12a and this spec

- Stage 12A (REQ-03, REQ-06–REQ-08, REQ-12, REQ-13, REQ-16, REQ-30–REQ-37, REQ-39–REQ-47,
  REQ-50, REQ-51, REQ-53, REQ-54; AC-02, AC-04, AC-05, AC-08, AC-09, AC-11, AC-12, AC-19,
  AC-23–AC-30, AC-32, AC-34, AC-36, AC-37; DM-1–DM-3, C-4, the N = 1 parts of C-1–C-3 and C-5;
  their edge cases, risks and assumptions; D-02, Q-02) moved to
  `.ai/specs/12a-composite-branch-model.md` without renumbering. Their N > 1 clauses became
  REQ-57–REQ-63 and AC-39–AC-46 here, each marked "split from 12a …"; A-30 and E-48 (N = 1
  merge conflict) were added to spec 12a. This file keeps stage 12B, the Source history
  and this Change Log. The verdict "NOT READY unchanged" in the entry above is historical; the
  checklist of `e3ba41a` read READY WITH RESERVATIONS and no longer applies.
- Same day, `/spec-draft --auto-mode` review loop with an independent critic (3 rounds: 59, 87,
  98/100): contract sections renamed C-7–C-10 as deltas to spec 12a; new REQ-68 (record commits),
  REQ-69 (packet location), REQ-70 (superseded attempts), REQ-71 (spawn refusal), REQ-72
  (unwritable worktree) and AC-51–AC-57; `admit` rule 0, `exclusive-active` and `respawn`; reconcile
  rows for worktree attempts; bounded status rounds; DM-7 journal extension; hard prerequisites
  and an eight-subtask delivery hint; every [C] criterion quotes literals.

## Readiness Checklist

Result of 2026-11-16 (first review after the split).

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — concurrent children of one composite on spec 12a's branch model, single writer, serialization and recovery |
| 2 | Out of Scope names concrete exclusions | PASS — cross-composite and top-level parallelism (D-04), other workflows, peer-owned contracts and others named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — 40 requirements, including split REQ-57–REQ-63 and new REQ-68–REQ-72 |
| 4 | Every REQ maps to an AC and every AC names a REQ | PASS — Traceability complete both ways |
| 5 | Every AC is binary and testable before implementation | PASS — [C] literals, [H] helper fixtures; AC-10 [L] is binary but runs only in an owner-approved live run and is not required for deterministic acceptance |
| 6 | Non-functional targets measurable or N/A | PASS — spec 12a NFRs apply; NFR-04 verified by AC-56; NFR-08 N/A with its source |
| 7 | Data model and contracts specified | PASS — DM-4–DM-7, C-6–C-10 |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — this file's E rows, including E-55–E-57 |
| 9 | Every ambiguity recorded | PASS — A-01, A-02, A-06, A-10, A-15–A-17, A-22, A-23, A-26, A-27, A-29, A-35–A-38; D-01, D-03–D-05; Q-01 and Q-03 resolved |
| 10 | No blocker question remains | PASS — none open |
| 11 | Every existing-code claim cited and verified | PASS — verified by the critic against `e3ba41a` |
| 12 | Terminology matches domain definitions | PASS — terms listed for `.ai/principles/domain.md` in C-10 |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — eight subtasks (Notes → Delivery size), at the upper bound |
| 14 | Devil's Advocate review passed | PASS — Review: 3 rounds, score 98/100, critic: sub-agent, open: none (minor F-38 and F-39 applied after the final round) |

**Verdict: READY FOR DEVELOPMENT.** Check 13 sits at the upper bound of eight subtasks; the
review-record requirements REQ-55 and REQ-56 are the natural boundary if Discovery finds more.
Automated readiness is not sign-off.
