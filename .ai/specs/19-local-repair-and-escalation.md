# 19. Bounded local repair after NEEDS WORK and explicit escalation

## Source

- **Request.** Owner roadmap direction 8 of 2026-10-21, "local repair and escalation": opt-in
  bounded repair, preserved correct code and RED evidence, independent recheck, explicit
  escalation (`.ai/specs/README.md`, roadmap workstream 8). Original language: Russian. The original body is
  preserved below as a labelled faithful English translation; it is historical and
  non-normative. Every requirement and acceptance identifier of the original (REQ-01–REQ-09,
  AC-01–AC-05) is kept with its meaning restated under `## Requirements` and
  `## Acceptance Criteria`; new identifiers are appended. Three narrowings are deliberate and
  recorded: the economic comparison of original REQ-05 and §10 is owned by spec 09's scenario
  calculator, so this spec only reads the owner's start choice (A-09); a lost repair worker is
  never recreated inside the same attempt (A-14); and repair inside spec 12's scheduler is
  wired by spec 12a REQ-54 (N = 1) and spec 12 REQ-63 (N > 1) against this spec's C-5 and C-10 row 12, not by this spec's own files (A-21).
- **Refinement.** Rewritten in English on 2026-11-14 in an autonomous refinement under the
  owner's standing authorization for in-place replacement, against worktree revision
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Specs 14–18 were read in their refined state of
  the same day.

### Implementation review — 2026-11-06 (preserved verbatim)

- **Disposition:** Planned; existing stop/fix workflows delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** The default runner stops on NEEDS WORK and task validation can create and validate explicit fix tasks.
- **Outstanding scope and limits:** The opt-in bounded-local repair policy, persistent episode ledger, attempt reservation/recovery, and qualified escalation protocol are not delivered. Manual fix iterations do not prove the bounded policy.
- **Sources:** [`workflows/spec-run.md`](../../workflows/spec-run.md), [`workflows/pv-create-fixes.md`](../../workflows/pv-create-fixes.md), [`workflows/pv-execute-fixes.md`](../../workflows/pv-execute-fixes.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Change log of the original (preserved verbatim)

- 2026-11-06 — implementation/state reconciliation: Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

### Original text (translated from Russian; historical, non-normative)

**Title.** 19. Bounded local repairs and an explicit transition to a stronger model.

**1. Status and source contract.** Status: a future capability of direction 8 of the request of
2026-10-21. Basis of current behaviour: snapshot `8c2fa08c18115ffcf38a1798742c41e53a2c7461` of
2026-10-28, `workflows/spec-run.md`, `rules/orchestration.md` and the current atomic validation
cycle. Today `NEEDS WORK` keeps the branch, commits and findings and stops the sequential run.
The existing permitted task-level fixes and short bug fixes are separate paths; they do not mean
that the bounded cycle proposed here exists. The separate audit report mentioned by the sources
is absent from the snapshot and does not prove implementation. The new policy is enabled
explicitly and only after the decision to change the stop, recorded at implementation in an
architectural decision. Until then, and whenever the policy is absent, the previous stop applies.
This revision does not enable the new policy automatically.

**2. Goal and scope.** Preserve work that is already correct and repair specific local defects
from independent findings, limiting the number of attempts and checking each one again. On
uncertainty, a critical violation or no progress, move in time to a permitted stronger model or
stop for the owner's decision. In scope: classification, the repair contract, a durable attempt
counter, progress assessment, an availability/effort check, independent recheck and recovery.
Out of scope: widening scope without permission, automatic change of requirements, weakening
frozen tests, endless retries, bypassing external limits, new production money/time limits and
automatic external actions.

**3. Ownership and definitions.**

| Participant | Permitted action |
|---|---|
| Independent reviewer | Stable finding identifiers, reproducible evidence, severity and verdict |
| Orchestrator | Applying the approved policy, reserving attempts, handing over the repair, shared records and repository operations |
| Executor | The minimal sufficient repair within the permitted area, test evidence, returning the result |
| Arbiter/owner | Resolving questions that need interpretation or a change of the accepted contract under existing authority |

A **local repair** does not change the approved goal, AC, interface obligations or the forbidden
area. **Escalation** is execution by an explicitly permitted stronger model chosen by
suitability, or handing the decision to the owner. A higher price alone does not prove greater
suitability. An **episode** links a leaf task, its approved contract and a specific initial
failed check with all later attempts. A resume, a new process, a new file name or a new agent
does not create a new attempt budget. All real requests and responses stay in the shared result
line of 05.

**4. Requirements.**

- **REQ-01.** By default keep the stop on `NEEDS WORK`. An explicit policy, for example
  `--repair-policy bounded-local`, acts only after a recorded contract change. A standalone
  check without this policy still stops and shows the findings.
- **REQ-02.** Distinguish a local implementation defect, an insufficient/wrong test, missing
  context, an infrastructure failure, an architectural/contract divergence and a violation of
  the forbidden area/an invariant. Unclear intent, critical security/data integrity, the
  forbidden area, a weakened RED and an architecture conflict are not part of the autonomous
  cycle; the provided decision is required.
- **REQ-03.** For an eligible repair, issue a contract with finding identifiers, AC,
  reproduction/evidence, expected behaviour, bounded files/interfaces, the hash of the frozen
  tests and the mandatory checks. Preserve correct code; do not recreate the whole task without
  a permitted redesign. A reviewer's finding does not override the source specification.
- **REQ-04.** One episode allows at most one local attempt on the current model and at most one
  explicitly permitted attempt by a stronger model. Each gets an independent verdict. A repeat
  of the same defect, no progress, a new important violation, termination by the provider, or
  doubt about locality forbid further cheap attempts.
- **REQ-05.** Comparing local repair and strong execution relies only on usable 05/09 data on
  full execution, review, success/repair and escalation. Without such data a suitable
  conservative/strong path is kept; probabilities are not invented. A permitted strong model
  may be chosen immediately if the full expected result is preferable.
- **REQ-06.** Before escalation, check availability and the floors of 04, resolve a supported
  setting through 18, and store the requested/resolved/actual model separately. Give the new
  executor the sufficient source contract and unresolved findings. No permitted candidate means
  an explicit stop, not a hidden substitution.
- **REQ-07.** Keep the order of tests before the corresponding implementation, the immutability
  of the frozen RED and the provided procedure for authorizing test amendments. For a new
  behavioural case, add and commit a reproducing test before the fixing code. Repeat the
  affected commands and the independent check of 16 before closing.
- **REQ-08.** Keep the attempt/finding line and the last verified tree through messages of 15
  with a single writer of shared data. A resume does not reset the limit. Dependent leaves are
  blocked until independent acceptance; a final failure keeps branches, commits and findings.
- **REQ-09.** Account all repair, context, review and escalation work under 05, apply G1–G8,
  describe enabling, stop reasons, disabling and recovery. The attempt limit is a governance
  rule, not a money/time limit. A provider limit must not be bypassed by changing accounts.

**5. Eligibility: decision before reserving an attempt.**

| Class | Autonomous action with the policy enabled |
|---|---|
| An unambiguous local implementation defect inside the permitted contract | One local attempt with a specific reproduction is possible |
| Missing context whose answer exists in current sources | First obtain the context through 14/the arbiter; then reclassify, do not repair by guessing |
| An additional test is needed for an unchanged requirement | Allowed only with an existing right to add a test and the order test → commit → implementation |
| An existing frozen test is wrong or needs weakening | Stop for the established agreement on changing the test basis |
| Network/environment/tool failure without a proven code defect | Diagnose the infrastructure; do not rewrite code to hide the failure |
| Architectural divergence, ambiguous AC, change of a shared contract | Arbiter/owner under existing authority; not an autonomous local attempt |
| Critical security/data integrity, leaving the forbidden area, invariant violation | Stop; no new executions start until a decision |
| Provider limit/termination | Keep the state, stop explicitly; do not look for a workaround through accounts |

If a reviewer's finding contradicts the specification, the orchestrator does not declare the
specification wrong and does not repair code blindly. An independent clarification from the
source sources is obtained; changing intent belongs to the owner. If a risk cannot be
confidently classified as local, the stop/strong provided path applies, not an optimistic
classification.

**6. Repair contract and episode record.** The repair contract contains: `episode_id`,
`attempt_id`, `task_id`, `leaf_id`, `task_contract_hash`; the last independently checked tree,
the current actual tree and the 14 packet; the full set of open findings with stable
identifiers, severity, AC and source; the reproduction, expected behaviour and actual failure;
permitted/forbidden files, interfaces and constraints; the frozen test set and its hash, the
required new tests and the grounds for adding them; mandatory deterministic checks and the scope
of the independent check of 16; the permitted model/effort, the source of the permission and the
reasons for the choice; stop conditions, remaining slots and the expected next report. The
durable episode record additionally contains `policy_version`, the initial failed check, the
reservation/dispatch/completion of each attempt, previous and new tree hashes, independent
verdicts, the progress assessment and the terminal reason. These data are protected from
destructive compression. They complement the canonical statuses and introduce no competing task
status vocabulary. A finding identifier does not change merely because its text is reworded.
Equivalent findings are linked by a common basis, otherwise an agent could present a repeat of
an old error as new progress. Withdrawing a wrong finding has a separate independent
justification, not silent removal.

**7. Finite execution order.** (1) Receive an independent `NEEDS WORK`, keep the branch,
evidence and all findings; do not start a dependent task. (2) Check that an approved policy
exists; without it stop under the previous rule. (3) Classify the findings and check locality; a
hard stop condition ends the automatic path before a new execution. (4) Choose a permitted
strategy: use the remaining local attempt, skip it and move to an already permitted strong
model, or stop; cost data do not override quality floors. (5) **Before sending to the
executor**, durably reserve a specific slot with an `attempt_id` through the orchestrator; if
the write fails or the state is ambiguous, do not start the executor. (6) Send the repair
contract; a repeated transport delivery keeps the `attempt_id` and does not create a second
run; if it is unknown whether the run started, the slot counts as used until absence of
execution is confirmed. (7) Receive the actual tree, test evidence and the 15 message; reconcile
the contract, scope and frozen tests; do not accept a result only because the executor says
"fixed". (8) Run the affected checks and an independent recheck under 16; every actually
executed attempt gets its own verdict, even if execution was interrupted or produced no useful
change. (9) If everything is accepted, close the episode and only then permit dependent
progress; on failure determine progress and the next permitted step from the remaining slots.
(10) After a failed strong attempt, stop. A new important finding forbids a further cheap
attempt and requires reclassification: an already permitted escalation is possible only if the
task is still unambiguously local and no hard stop is violated. A critical finding, an unknown
effect or no permitted candidate end the automatic path.

*What counts as an attempt and as progress.* An attempt starts with the real handover of work
to the executor, not with receiving its successful answer. An executor failure/timeout does not
return the slot automatically. A provably unsent request may be marked cancelled with a reason;
this does not erase the reservation record. Paid diagnostic and review requests are accounted
under 05 whether or not they occupy a repair slot. Progress is the independent confirmation that
specific earlier findings are eliminated while the other obligations are kept and no new
important defect appears. Changed line counts, a new commit and an optimistic executor report
are not progress. Partial progress does not allow a second local attempt: the local slot is
still one.

**8. Protection against resetting the limit.** Within the unchanged contract of one leaf task, a
restarted run, process recovery, a change of executor, clearing session context and a new
episode name give no additional slots. The orchestrator looks for the existing line by task,
contract and initial failure and continues it. New work after the limit is exhausted is allowed
only as an explicit owner decision to change the policy, the contract of a new task, or a
permitted replanning. The decision references the earlier episode, explains the new scope and
keeps the earlier costs/failures in the shared result. Creating a technically new identifier
without such a decision is forbidden. Reserving two attempts of one leaf in parallel is not
allowed. In 12, isolated leaves may have their own episodes, but a shared critical defect stops
new dispatches and requires a shared decision. The limit of one leaf is not used to create
uncontrolled copies of the same error.

**9. Test order and preserving correct work.** If existing frozen tests already reproduce the
local defect, no repeated empty test commit is created: the earlier evidence is kept and the
corresponding repair is made with a recheck. If a new test is needed, it first demonstrates the
violation of the unchanged requirement and is committed before the corresponding code. The
executor does not weaken expectations to get a green result. The existing justified exemption
`test-level: none` / `atomic-tests: n-a` is kept for eligible tasks without applicable tests; it
is not assigned retroactively to hide an error, does not create a false RED and does not cancel
the independent content/structural check. The `atomic-tests: pinned` mode and the compatibility
of historical blocks already started without `atomic-tests` are also kept under the canonical
contract. Passing characterization tests are not described as a failing RED and past evidence is
not invented. This does not exempt a new behavioural repair from an applicable reproducing test
before the corresponding code; the basis is chosen by the real kind of repair, not to bypass the
check. Handing over to a stronger model includes the full sufficient source contract, the actual
code, the tests and the unresolved findings. It does not mean rewriting the whole solution.
Already verified correct parts are kept unless the repair is proven to affect them; changing the
overall architecture needs a separate decision.

**10. Economic decision without invented probabilities.** The full comparison is made under
05/09 with the same acceptance criterion. In a simplified scheme: expected chain cost = initial
execution and review + P(local repair) × cost of local repair with review + P(local repair) ×
P(escalation | local repair) × cost of escalation with review + other explicitly accounted
costs. Conditional probabilities are not multiplied as independent without grounds. Real missed
defects, failed final results and accepted results are accounted by the canonical 05/09 method;
this formula does not replace it. A synthetic example only to check the arithmetic: initial
execution and review cost 16 units; local repair with review 16; the probability that it is
needed 0.6; the conditional probability of a later escalation 0.5; escalation with review 30.
Then the chain costs `16 + 0.6 × 16 + 0.6 × 0.5 × 30 = 34.6`, while strong execution right away
costs 30 at the same assumed quality. The example shows that a cheap start can be unprofitable,
but it is not a project measurement or proof of the stated probabilities. Without usable
calibration the probability/cost fields stay unknown. The choice is made by conservative
suitability and risk, not by an invented saving percentage.

**11. Resume and stops.**

| Event | Action |
|---|---|
| Interrupted before dispatch after reservation | Confirm that nothing was sent; keep the cancellation or continue the same slot |
| Unknown whether the run started | Do not send again automatically; recover the facts; the slot counts as used for now |
| A duplicate result arrived | Apply once by `attempt_id/event_id` through 15 |
| The contract or test basis changed | Invalidate the old packet, stop for a permitted amendment |
| An earlier finding repeated | No new local attempt; a possible already permitted escalation or a stop |
| A new important violation | Stop cheap retries, reclassify; escalation only with eligibility kept and a permission already given |
| A new critical violation | Stop the automatic path and hand over the full evidence |
| The strong model is unavailable | Keep the result and stop explicitly; do not substitute the model |
| The policy is disabled during an episode | Start no new attempts; finish collecting the current evidence and keep the previous stop |
| The limit is exhausted | Keep the whole line and return the specific unresolved result to the owner |

**12. Acceptance criteria.**

- AC-01 (`REQ-01`, `REQ-02`). Without the policy and in a standalone check the stop is kept.
  Local defects go through classification; critical, architectural, forbidden and frozen-test
  cases require the provided decision.
- AC-02 (`REQ-03`, `REQ-07`). The minimal sufficient area is repaired; correct code and frozen
  tests are kept. A new test precedes the implementation; an earlier sufficient test does not
  produce an empty test commit. Closing without an independent recheck is impossible.
- AC-03 (`REQ-04`, `REQ-08`). Repeated/non-progressing findings, a restart, a new agent, a
  duplicate event and a new technical episode label do not bypass the limit of one local and one
  permitted escalated attempt. The slot is reserved before dispatch; a dependent task does not
  start on an unaccepted result.
- AC-04 (`REQ-05`, `REQ-06`). Synthetic arithmetic shows choosing immediate strong execution
  when the full chain cost is higher. Without data the conservative path is kept. An unavailable
  model, an unsupported setting and a missing permission stop the escalation explicitly.
- AC-05 (`REQ-09`). Reports keep all executions, context, reviews, escalation, model identity
  and final findings. Disabling, interrupted dispatch and recovery are checked. Offline checks
  start no paid models and introduce no production money/time limit.

Traceability: `REQ-01–02 → AC-01`; `REQ-03,07 → AC-02`; `REQ-04,08 → AC-03`;
`REQ-05–06 → AC-04`; `REQ-09 → AC-05`.

**13. Introduction and readiness.** (1) Record the decision on the exception from the current
stop and leave the policy off by default. (2) Introduce the durable episode/slot line and
synthetic interruption scenarios before any automatic run. (3) Implement classification and the
repair contract, then bounded transitions, the test order and the independent recheck. (4)
Connect 04/18 for the permitted configuration, 14/15 for context/checkpoints and 05 for full
attribution. (5) Check disabling, no available strong model, limit exhaustion and no reset on
resume. Dependencies: 04, 06, 09, 15, 16, 18; the context contracts of 14 are used. G1–G8 are
mandatory, see the [guide](README.md#shared-acceptance-gates). One local retry is a conservative
initial decision, not a proven optimum. Changing the limit, the initial policy or quality needs
an explicit decision and a separate evaluation, not a technical restart.

## Context & Problem

Facts verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

1. **NEEDS WORK stops the orchestrated run.** `/spec-run` step 4.3: "If the verdict is NEEDS
   WORK → the subtask does not close. Record the findings, leave the branch and commits intact,
   and **stop the run**" (`workflows/spec-run.md:297-299`); no leaf N+1 starts before N is
   `reviewed` (`:190`), and the workflow never runs subtasks in parallel (`:378`). Resume
   re-runs the Validator on a `done` leaf (`:190-194`), and a resumed `failed` record "requires
   repaired implementation and a fresh `/pav-check`" (`workflows/phase-atomic-validation.md:80-83`).
2. **The leaf verdict.** `/pav-check` returns NEEDS WORK on `[INCOMPLETE]`, `critical` or
   `important` findings, sets `atomic-validation: failed`, lists unmet criteria in `notes:`,
   creates no fix-task and stops (`workflows/pav-check.md:99-108`). Weakened tests and closing
   without GREEN are `critical` findings (`:63-68`, `:86-87`).
3. **Fix paths exist only at other levels.** Task-level validation creates fix-task leaves from
   approved issues (`workflows/pv-create-fixes.md:50-129`) and executes them through ordinary
   atomic cycles (`workflows/pv-execute-fixes.md:31-49`); a composite integration failure
   creates D8 fix siblings (`workflows/phase-composite-validation.md:89-143`); `/bugfix` repairs
   inline under the quick gate (`workflows/bugfix.md:128-135`). None of them repairs a leaf
   inside the `/spec-run` step 4 loop, limits attempts or escalates.
4. **Roles and stops.** The Orchestrator owns git and every shared file and never writes code
   (`rules/orchestration.md:22-36`); the Validator is a separate agent without the Implementer's
   reasoning (`:80-92`); sub-agents write only their own block, code and tests and return
   deltas (`:96-132`). Class B intent is the human's (`:148-153`); a class-B leak during
   Execution stops the run (`:173-178`). The always-stop list (`:180-187`) does not name NEEDS
   WORK; spec 15 adds one bullet for checkpoint stops
   (`.ai/specs/15-orchestrator-overhead.md` C-6, row `stop`).
5. **Test-first and the frozen set.** RED requires an observed failure for the expected reason
   (`rules/tdd.md:86-100`); the RED set is frozen during GREEN, amendments need a
   `tdd: test amended` record, and adding new tests is always allowed (`:169-189`);
   characterization pins transition only to `green` and a refactor that also fixes a bug must be
   split (`:119-165`); a missing dependency is a blocker, never a downgrade to `none`
   (`:208-210`). `/pae-tests` writes the `tdd: red digest` in every mode (`workflows/pae-tests.md:205-230`).
   Commits: at least `test:` then `feat:` per subtask, `fix:` for fix work, and additional
   commits are allowed when independently meaningful (`rules/git-flow.md:85-96`).
6. **Autonomy is registered.** `/spec-run` is autonomous except at the batch gate, and its
   extra overrides are listed in `rules/workflow-globals.md:62-85`; every stop must be declared
   (`.ai/principles/architecture.md:39-44`, P5) and a format, stop or mode-override change needs
   an ADR (`.ai/principles/coding.md:53-60`).
7. **Model and effort resolution exist and are conservative.** Leaf Implementer models resolve
   through `model-catalog.py --resolve-plan` against a plan row; an unsupported explicit request
   needs an authorized eligible fallback or a stop, and actual identity stays unknown without a
   separate receipt (`rules/workflow-reference.md:156-188`, `workflows/spec-run.md:139-156`).
   The plan reader requires a `## Subtasks` table with `ID` and `Status` columns
   (`scripts/model_plan.py:167-180`). Spec 18 owns effort; its resolver request has an
   `escalation` input and spec 19 owns when to escalate
   (`.ai/specs/18-reasoning-effort-policy.md` REQ-29 and C-6 row 19).
8. **Neighbouring contracts this spec builds on.** Spec 16 records findings `<scope key>/F<n>`
   with `same_as`, severities, per-finding outcomes, verdicts and recheck plans, and makes a
   repair attempt's recheck a review under 16 (`.ai/specs/16-scoped-verification.md` DM-5, DM-7 and its Terminology entry
   "Finding-led recheck"); a defined check exiting non-zero is a finding of at least `important`, and one that
   cannot complete is a blocker (spec 16 REQ-55). Spec 15 offers attempt lineage (`supersedes`),
   `attempt-superseded` and duplicate handling by `event_id` and leaves limits to 19
   (`.ai/specs/15-orchestrator-overhead.md` DM-2 and C-10 row 19). Spec 14 gives a repair attempt a
   fresh implementer packet built with `--predecessor`
   (`.ai/specs/14-task-context-and-reuse.md` C-8 row 19 and C-1 `--predecessor`). Spec 17 separates infrastructure outcomes
   from failing tests (`.ai/specs/17-bounded-tool-output.md` DM-3 and C-7 row 19). Specs 12a and 12 keep a
   failed child unintegrated (`.ai/specs/12a-composite-branch-model.md` REQ-51 and
   `.ai/specs/12-composite-branch-model-and-parallel-children.md` REQ-24) and, only when the policy
   is active, send it into this spec's repair loop (spec 12a REQ-54 and DM-3 `repair_episode`,
   spec 12 REQ-63 and DM-6 stage `repair`).
9. **The validator inventory is frozen.** New checks go into standalone scripts outside
   `scripts/validate-contracts.sh` and outside `tests/`
   (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`). Per-file loops of
   the validator still run on new files: every workflow must appear in `docs/USAGE.md`
   (`scripts/validate-contracts.sh:1354-1358`) and every rule must be named by
   `scripts/setup-new-project.sh` and `scripts/sync.sh` (`:1293-1305`); a write verb before
   `plan.md`, `architecture.md`, `.ai/memory/state.md` or `.ai/project_state.md` in
   `/pav-check` and other sub-agent workflows needs the delta clause (`:1541-1548`).

**Consequence.** One correctable local defect found by the independent Validator stops the whole
stacked run and waits for the owner, even when the defect is reproducible, inside the leaf's
files and fixable without touching its tests. Nothing records repair attempts, so a manual
retry has no limit, no lineage and no defined escalation. The roadmap states that no saving
has been measured (`.ai/specs/README.md`, ownership-map note); this spec makes bounded repair possible and
attributable and leaves every claim about quality or cost to spec 09.

## Goal

Let an owner opt in, per `/spec-run` invocation, to a bounded repair of a leaf that the
independent Validator returned as NEEDS WORK: the Validator classifies each finding, a
read-only helper decides eligibility deterministically and conservatively, the Orchestrator
durably reserves at most one local attempt and, only when the owner authorized it in advance,
at most one escalated attempt per episode, a fresh Implementer repairs only the leaf's own files
test-first without touching any frozen test, and a fresh Validator rechecks the result as a
spec-16 review — so that correct code and RED evidence are preserved, every attempt is recorded
and never reset, every escalation is explicit and goes through the existing model and effort
resolution, and every case the policy does not cover ends at today's NEEDS WORK stop. Without
the opt-in, behaviour is exactly today's.

## Scope

1. An opt-in `/spec-run` flag `--repair-policy bounded-local`, a disable switch and an optional
   owner policy file that authorizes escalation (DM-5).
2. Repair classification of findings by the Validator (DM-6) and a deterministic eligibility
   decision with conservative overrides (DM-7).
3. The repair episode ledger: a protected append-only `## Repair Episodes` section in the task
   `state.md` (DM-3) and write-once records under `<task>/repairs/` (DM-1).
4. The repair contract as the durable reservation of an attempt (DM-8), attempt limits, and
   reset protection.
5. A new atomic workflow for one repair attempt (`/pae-repair`, C-6) and its stage checks (DM-9).
6. Outcome and progress judgement after the independent recheck (DM-10, DM-16) and the next
   permitted step.
7. Escalation resolution through spec 04's model resolution and spec 18's effort escalation
   input (C-8).
8. Resume and recovery (`status`, DM-11), cancellation, owner decisions to reopen or cancel
   (DM-4).
9. A read-only standard-library helper `scripts/repair-episode.py` (C-1), an on-demand rule
   `rules/contract-repair.md` (C-4), edits to `/spec-run`, `/pav-check`, the orchestration,
   TDD, globals and reference rules (C-7), the standalone acceptance suite
   `scripts/check-repair-episode.py` (C-11), documentation, an ignore rule, vocabulary and an ADR.
10. The contracts exposed to specs 05, 09, 12 and 20 and consumed from 04, 14, 15, 16, 17 and 18
    (C-10).

## Out of Scope

- Repair of composite integration failures (D8 fix siblings stay as they are), of task-level
  validation issues (fix-tasks stay as they are), of quick-tier tasks and of `/bugfix`.
- Repair outside `/spec-run`: standalone `/phase-atomic-validation`, `/pav-check`,
  `/phase-execution`, `/pe-execute` and `/phase-pipeline` keep today's NEEDS WORK stop.
- Wiring repair into the scheduler of specs 12a and 12 (N = 1 and N > 1): spec 12a REQ-54 and spec 12 REQ-63 own its journal, its
  handoff stage `repair` and its stops, and calls this spec's C-5 (C-10 row 12).
- Defining review coverage, evidence reuse, finding identity, review records or the recheck
  scope (spec 16); closing a finding (only a spec-16 review gives outcomes).
- The effort policy itself and model eligibility (specs 18 and 04); a model or effort that the
  owner did not declare; any automatic choice of the escalation target.
- Economic modelling, probabilities, savings and comparative evaluation (spec 09's calculator
  and goldens); a production money or time limit; timeouts on workers or checks (ADR-0020).
- Changing the definitions of DONE/NEEDS WORK, severities, status vocabularies, test-first
  order, the RED/pinned/`n-a` rules, git rails, the batch gate or the Arbiter's authority.
- Amending frozen tests inside a repair, recreating a lost repair worker within its attempt,
  more than one local and one escalated attempt per episode, automatic reopening of a closed
  episode.
- Changing `scripts/validate-contracts.sh` or any file under `tests/`; new run-log events,
  fields or markers; spec-05 records.
- The state tool of spec 07.

## Actors & Roles

| Actor | Allowed actions | Forbidden |
|---|---|---|
| Owner | Passes `--repair-policy bounded-local`; sets `ORCHESTRAIL_REPAIR_POLICY=off`; writes the policy file (DM-5); writes reopen and cancel decision lines (DM-4); resolves stops | — |
| Orchestrator (`/spec-run`) | Runs the helper; saves its records; appends ledger lines; resolves model and effort; asks the Arbiter; builds packets; spawns repair Implementers and Validators; commits; writes git fields and plan rows; decides stops | Writing code or tests; editing records; reserving beyond the helper's output; dispatching without a saved reservation |
| Validator | Runs the spec-16 review as today; under an active policy writes the classification draft (DM-6) in `<task>/repairs/drafts/` | Reading the Implementer's reasoning or report; writing ledger lines or records |
| Repair Implementer | Runs `/pae-repair` with one contract; writes new test files, edits allowed paths, writes its own leaf block | Running git; editing frozen tests, the description, `state.md` outside its block, `plan.md`, other leaves; creating non-test files |
| Arbiter | Answers class-A questions of `missing-context` findings with a citation | Deciding eligibility, intent or a test-basis change |
| `scripts/repair-episode.py` | Reads the task directory, the knowledge root, spec-16 records and the repository through read-only git; prints one JSON document | Writing any file; starting a model or a network connection |
| `scripts/check-repair-episode.py` | Acceptance suite in disposable fixtures | Touching the real home or this repository's `.git` |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Repair policy | The opt-in behaviour `bounded-local`, version 1, active for one `/spec-run` invocation (REQ-10) | Original REQ-01 |
| Active policy | The flag is given, the disable switch is not `off`, and the helper's `version` exits 0 | This spec |
| Policy file | The optional owner file DM-5; it authorizes escalation and chooses the start slot | Original REQ-05, REQ-06 |
| Episode | The record of repairing one leaf from one initial NEEDS WORK review record under one contract digest, with all its attempts; id `<leaf_id>.E<n>` (DM-2) | Original §3 |
| Repair attempt | One reserved dispatch of a fresh repair Implementer with one contract; id `<episode_id>.A<m>`. Its `attempt_id` is not a spec-15 `attempt_id` (`<leaf>.<role>.<n>`), but the spawn of the repair Implementer is a spec-15 attempt, recorded as spec 15 specifies (role `implementer`, `supersedes` lineage through its `attempt` number), and it is not a spec-12 attempt (a child execution) | Original §7; `.ai/specs/15-orchestrator-overhead.md` DM-2 |
| Slot | `local` (the model and effort the leaf's Implementer resolves today) or `escalated` (the owner-declared escalation); limit 1 each per episode | Original REQ-04 |
| Reservation | Saving an attempt's repair contract and appending its `reserved` ledger line, both before the spawn | Original §7 step 5 |
| Repair contract | The write-once record DM-8 given to the repair Implementer | Original §6 |
| Classification | The Validator's per-finding repair class and reproduction (DM-6) plus the helper's deterministic overrides (DM-7) | Original REQ-02, §5 |
| Repair class | `local-defect`, `test-missing`, `missing-context`, `test-basis`, `infrastructure`, `contract-divergence`, `hard-stop` (DM-6) | Original §5 |
| Eligible | Every open finding has an eligible class and a valid reproduction, and no episode-level reason applies (DM-7) | Original §5 |
| Repair escalation | A repair attempt in the `escalated` slot, with the owner-declared model and/or effort applied exactly; or, when that is impossible, the stop that hands the decision to the owner | Original §3 |
| Frozen test set | The paths of every `test`-type commit recorded for the leaf, with their current digests (DM-14) | `rules/tdd.md:169-189` |
| Allowed paths | The paths a repair may modify (DM-15) | Original REQ-03 |
| Outcome | The result of one attempt (DM-10) | This spec |
| Progress | `resolved`, `progress`, `no-progress` or `regression` from the recheck record (DM-16) | Original §7 |
| Terminal | The reason an episode closed (DM-3) | Original §6 |
| Recheck | The spec-16 leaf review of the tree an attempt produced | `.ai/specs/16-scoped-verification.md` DM-5 and Terminology "Finding-led recheck" |
| Finding, outcome (`resolved` …), `same_as`, review record, DM-8 notes entry | As spec 16 defines them | `.ai/specs/16-scoped-verification.md` DM-5, DM-7, DM-7a, DM-8 |
| Canonical JSON, self-digest | As spec 15 defines them | `.ai/specs/15-orchestrator-overhead.md` Data Model introduction |
| Leaf, RED, Pinned, `n-a`, Orchestrator, Implementer, Validator, Arbiter, Class A/B | As defined | `.ai/principles/domain.md` vocabulary |

Rejected synonyms: "retry" for a repair attempt (a retry suggests unbounded repetition);
"fix-task" for a repair (fix-tasks are separate leaves); "attempt" alone where a spec-15 or
spec-12 attempt could be meant; "stronger model" as a proven property (the owner declares the
escalation; strength is not established here); "budget" for slots.

## Requirements

Names follow today's files; once spec 13 is delivered (it precedes this spec,
`.ai/specs/README.md` dependency table), every workflow and rule path follows 13's maps (`## Notes → Name
mapping`). Spec 08's `loads:` declarations and its 700-word limit for rules apply to every file
this spec adds or edits when spec 08 is in force. "THE helper" is `scripts/repair-episode.py`.

### Previous identifiers, restated

- **REQ-01 Default stop.** IF `/spec-run` runs without `--repair-policy bounded-local`, or with
  `ORCHESTRAIL_REPAIR_POLICY` disabling it (REQ-11), or the helper's `version` does not exit 0, THEN THE
  Orchestrator SHALL handle a leaf NEEDS WORK exactly as `workflows/spec-run.md:297-299` does
  today and SHALL run no helper subcommand other than `version`, append no ledger line and
  instruct no Validator to classify.
- **REQ-02 Classification.** WHILE the policy is active, WHEN a leaf review publishes a spec-16
  record with verdict NEEDS WORK, THE Validator SHALL write a DM-6 draft that gives every finding
  of that record with status `open` exactly one repair class and one reproduction.
- **REQ-03 Repair contract.** WHEN the Orchestrator reserves an attempt, THE helper SHALL print a
  DM-8 contract containing every DM-8 field, derived only from the ledger, the classification
  record, the review record, the leaf block, the description, the repository and the
  resolution inputs given on the command line.
- **REQ-04 Attempt limits.** IF a reservation would give an episode a second non-cancelled
  attempt in the same slot, or a `local` attempt after a non-cancelled `escalated` attempt, or if
  the episode has an attempt with a `RESERVED` line and neither an `OUTCOME` nor a `CANCELLED`
  line, THEN `reserve` SHALL exit 1 with `slot-exhausted`, `slot-order` or `attempt-pending`.
- **REQ-05 Start without invented numbers.** THE helper SHALL take the first slot of an episode
  from the policy file's `start` value, or `local` when no policy file is given (an invalid file
  stops the run, REQ-13), and SHALL
  hold and print no probability, cost, saving or duration field.
- **REQ-06 Escalation resolution.** WHEN the Orchestrator prepares an `escalated` reservation,
  THE Orchestrator SHALL apply every component the policy file declares for the current harness
  through C-8, and IF any declared component does not resolve or none is effective (C-8 steps 3–4),
  THEN it SHALL close the episode with terminal `escalation-unavailable` and stop without spawning.
- **REQ-07 Test-first inside a repair.** WHEN a repair needs a new test (reproduction `new-test`
  or `coverage`), THE repair Implementer SHALL write it in new files and observe it before any
  change to allowed paths, and THE Orchestrator SHALL commit those files as a `test:` commit
  before the `fix:` commit.
- **REQ-08 Durable lineage.** THE Orchestrator SHALL append each ledger line only after the
  helper printed it and its record (if any) was saved, SHALL derive every limit from the ledger
  alone, and SHALL start no leaf that depends on the repaired leaf before the episode closes
  `accepted` or `resolved-outside`.
- **REQ-09 Attribution and rollback.** WHEN an episode closes, THE Orchestrator SHALL report one
  line per attempt and one line for the episode in the C-5 report form, naming slot, requested
  and resolved model, effort decision key, outcome, progress, review sequence and terminal.

### Activation

- **REQ-10 Flag.** WHEN `/spec-run` is invoked with `--repair-policy <value>` and `<value>` is not
  `bounded-local`, THE Orchestrator SHALL stop in its Guard with the C-9 `repair-policy-unknown`
  message before any write.
- **REQ-11 Disable switch.** WHERE `ORCHESTRAIL_REPAIR_POLICY` is set to a value other than the empty
  string or `on` (documented value `off`; the rule of spec 14 REQ-32), THE Orchestrator SHALL
  treat the policy as inactive for the whole run and report "repair policy disabled by
  ORCHESTRAIL_REPAIR_POLICY=<value>" once.
- **REQ-12 Helper probe.** WHEN Step 0 resolves the task and the flag is given, THE Orchestrator
  SHALL run `version` once; IF it does not exit 0, THEN it SHALL treat the policy as inactive and
  report "repair policy unavailable: <cause>" once.
- **REQ-13 Policy file check.** WHEN the policy would be active and the DM-5 path names an
  existing file, THE Orchestrator SHALL run `check-policy` before any write, and IF it exits 1,
  THEN SHALL stop with the C-9 `repair-policy-invalid` message.
- **REQ-14 Dry run.** WHILE `/spec-run` runs with `--dry-run`, THE Orchestrator SHALL report the
  resolved policy state (active, inactive with cause, or invalid) and SHALL append no ledger line
  and save no record.
- **REQ-15 Scope of application.** WHILE the policy is active, THE Orchestrator SHALL apply the
  repair loop only to a NEEDS WORK verdict of a leaf validated through `/spec-run` step 4.3 —
  including fix-task leaves executed through step 6 and children of composites run in the stack
  — and SHALL keep the existing behaviour for composite integration verdicts.

### Opening and classification

- **REQ-16 Opening.** WHEN a leaf review returns NEEDS WORK under an active policy and `status`
  reports `open`, THE Orchestrator SHALL run `open` with the record named by the leaf's last
  spec-16 DM-8 entry for step `check`, and append the printed `opened` line.
- **REQ-17 Review record required.** IF the leaf's last DM-8 entry for step `check` is a `none`
  entry, is absent, or names a file whose SHA-256 differs from the entry, or the record fails
  DM-7's review checks, THEN `open` SHALL exit 1 with `review-unavailable` or `review-invalid`,
  and THE Orchestrator SHALL stop with today's NEEDS WORK stop and that reason.
- **REQ-18 One open episode.** IF an episode of the leaf is open, THEN `open` SHALL exit 1 with
  `episode-open`.
- **REQ-19 Reopen decision.** IF the leaf's latest closed episode has a terminal other than
  `accepted` or `resolved-outside` and the same contract digest as the new record, THEN `open`
  SHALL exit 1 with `reopen-required` unless a valid DM-4 `repair-reopen` line names that episode.
- **REQ-20 Classification record.** WHEN `classify` runs, THE helper SHALL validate the draft
  against DM-6, apply the DM-7 overrides, print the DM-7 record with `eligible` and `reasons`,
  and print the `classified` line.
- **REQ-21 Draft missing or invalid.** IF the draft is absent, does not parse, names another
  record, omits or repeats an open finding, or uses a value outside DM-6, THEN `classify` SHALL
  print a record with `eligible: false` and reason `draft-invalid` and exit 0.
- **REQ-22 Conservative overrides.** WHEN `classify` evaluates a finding, THE helper SHALL take as
  effective class the more restrictive of the Validator's class and every DM-7 override that
  applies, using the DM-7 restriction order.
- **REQ-23 Unlinked obligations.** IF an obligation of the record has state `failed` or
  `unverified` and no finding with status `open` lists it, THEN `classify` SHALL set
  `eligible: false` with reason `unlinked-obligation`.
- **REQ-24 Owner-decision findings.** IF the record contains a finding with status
  `owner-decision`, THEN `classify` SHALL set `eligible: false` with reason
  `owner-decision-pending`.
- **REQ-25 Reproduction validity.** IF a finding's reproduction kind is not permitted for its
  class and the leaf's test mode by DM-6, or names a frozen test or check that DM-6 requires and
  that does not exist, THEN `classify` SHALL set `eligible: false` with reason
  `reproduction-invalid`.
- **REQ-26 Ineligible close.** WHEN a classification record has `eligible: false`, THE helper
  SHALL print a `close_line` with terminal `ineligible` and the first reason as detail, and THE
  Orchestrator SHALL append it after the `classified` line and stop with today's NEEDS WORK stop.
- **REQ-27 Missing context.** WHEN an eligible classification contains `missing-context`
  findings, THE Orchestrator SHALL send each finding's `question` to the Arbiter before
  reserving, and pass every cited answer to `reserve` in a DM-8 `context_answers` file.
- **REQ-28 Uncited answer.** IF the Arbiter's answer to a `missing-context` question has no
  citation, THEN THE Orchestrator SHALL record the question in `## Open Questions (batch)` under
  `rules/orchestration.md:173-178`, close the episode `ineligible` with detail
  `intent-unresolved`, and stop.

### Reservation and dispatch

- **REQ-29 Resolution before reservation.** WHEN an attempt is to be reserved, THE Orchestrator
  SHALL resolve its model and effort (C-8) and build its spec-14 packet before running `reserve`.
- **REQ-30 Reservation before spawn.** THE Orchestrator SHALL spawn a repair Implementer only
  after the attempt's contract file is saved with result `saved` (or `duplicate` while no
  `RESERVED` line names the attempt) and its `reserved` line is appended.
- **REQ-31 Save failure.** IF saving a helper record ends with `conflict` or `link-failed`, THEN
  THE Orchestrator SHALL append no line for it, spawn nothing, and stop with the C-9
  `repair-save-failed` message.
- **REQ-32 Dispatched line.** WHEN the spawn call for a reserved attempt returns without a harness
  refusal, THE Orchestrator SHALL append the attempt's `dispatched` line before any other action.
- **REQ-33 Refused spawn.** IF the harness refuses the spawn of a reserved attempt for a reason
  other than a provider limit, THEN THE Orchestrator SHALL run `cancel --reason spawn-refused`,
  append its line, and IF the slot then holds two `spawn-refused` cancellations, SHALL run `close`
  (terminal `stopped`, detail `dispatch-refused`) instead of reserving again. WHEN the refusal
  names spec 18's effort parameter or value, THE Orchestrator SHALL also append 18's DM-5
  rejection line, and the spec 18 request of the next reservation SHALL set
  `session.parameter: "absent"` (18 REQ-10).
- **REQ-34 Unknown dispatch.** IF `status` finds an attempt with a `reserved` line and neither a
  `dispatched` nor a `cancelled` line, THEN THE helper SHALL report next action `stop` with detail
  `dispatch-unknown` unless a DM-4 `repair-cancel` line names that attempt, in which case it SHALL
  report next action `cancel`.
- **REQ-35 Plan row.** WHEN an attempt's `reserved` line has been appended and the leaf's plan row
  status is `blocked`, THE Orchestrator SHALL set it to `done` before saving the spec-15 attempt
  record for the repair Implementer and before the spawn.
- **REQ-36 Spawn inputs.** WHEN the Orchestrator spawns a repair Implementer, THE Orchestrator SHALL
  give it exactly the description path, `WORK_DIR`, the branch, the contract path, the packet path
  when one was built, and the instruction of C-5 step 9, and no transcript, report or reasoning of
  any earlier worker.

### The repair attempt

- **REQ-37 Guard.** IF `/pae-repair` is invoked when the leaf block is not
  `atomic-execution: complete` with `atomic-validation: failed`, or the contract is missing, of
  another leaf, or its `description.sha256` differs from the description's current SHA-256, THEN
  THE workflow SHALL stop with blocker `contract-mismatch` and change nothing.
- **REQ-38 Reproduce first.** WHEN `/pae-repair` starts, THE workflow SHALL observe every
  finding's reproduction (C-6 step 2) before editing any allowed path.
- **REQ-39 RED pause.** WHEN `/pae-repair` wrote new test files, THE workflow SHALL report the RED
  form and wait; WHEN it wrote none, THE workflow SHALL continue without a RED report.
- **REQ-40 Stage check.** WHEN a repair Implementer returns a RED or GREEN report, THE Orchestrator
  SHALL run `check --stage red` or `check --stage green` and, only when it exits 0 with no violation,
  commit its `stage_paths` plus the tracked bookkeeping paths inside the task directory or `AI_DIR`
  that the repository's tracking policy allows (`rules/git-flow.md:156-165`), and no other path.
- **REQ-41 Scope.** IF at stage `green` a dirty path lies outside the contract's allowed paths or
  is a new file, or at stage `red` a dirty path is a tracked file or a frozen test path, THEN
  `check` SHALL report violation `scope-exceeded`.
- **REQ-42 Frozen tests.** IF any frozen test path's current SHA-256 differs from the contract, or
  a test file committed at this attempt's stage `red` changed after that commit, THEN `check` and
  `outcome` SHALL report violation `frozen-tests-changed`.
- **REQ-43 Contract change.** IF the description's SHA-256 or the `## Solution Design` section
  digest differs from the contract, or the recheck record's `contract.contract_digest` differs
  from the episode's, THEN `check` and `outcome` SHALL report violation `contract-changed`.
- **REQ-44 Worker blockers.** WHEN the repair Implementer meets a C-6 blocker condition, THE
  workflow SHALL stop, report the blocker code from the `Repair blockers:` line, and leave
  allowed paths as they are.
- **REQ-45 Infrastructure outcomes.** IF a command run by the repair Implementer ends with spec 17
  DM-3 kind `launch-error`, `timeout`, `interrupted` or `signal` (kind `exit` is a failing test or
  check, never an infrastructure blocker), or without a known outcome, THEN THE
  workflow SHALL report blocker `infrastructure` or `evidence-gap` and SHALL change no code to make
  the command pass.
- **REQ-46 Notes entries.** WHEN `/pae-repair` observes its reproduction and when it completes
  verification, THE workflow SHALL append the DM-13 `tdd: repair red` and `tdd: repair green`
  entries to its own leaf block with spec 14's append rule, keeping `atomic-tests:`,
  `atomic-execution: complete` and `atomic-validation: failed` unchanged.

### Recheck, outcome and next step

- **REQ-47 Recheck.** WHEN an attempt's `fix:` commit is made, or `outcome` exits 1
  `review-required` for a lost attempt that left commits, THE Orchestrator SHALL spawn a fresh
  Validator exactly as step 4.3 does, with the repair-active instruction of C-5 step 1, and then
  run `outcome` with the new record. The recheck is an ordinary spec 16 leaf review (spec 16
  C-6 row 19): its prior is the newest valid record of step `check`, which is the record the
  attempt answered, finding-led eligibility and outcomes follow spec 16 DM-5 and R-05, and spec 16
  neither ends nor removes the NEEDS WORK stop that this loop defers (REQ-56).
- **REQ-48 Outcome record.** WHEN `outcome` runs, THE helper SHALL print a DM-10 record, its
  `outcome` line and, when the episode ends, its `closed` line, and SHALL exit 1 with
  `review-required` when the attempt left commits, no DM-10 row before `accepted` matches, and the
  leaf's last spec-16 DM-8 entry for step `check` is still the one of the record the attempt
  answered; a `--review` record that fails DM-7's review checks gives exit 1 `review-invalid`.
- **REQ-49 Foreign change.** IF a commit between the attempt's start head and `HEAD` is absent from
  the leaf's `commits:`, `HEAD` does not descend from the start head, or a commit of the attempt
  has another type than `test` or `fix`, THEN `outcome` SHALL report outcome `foreign-change`.
- **REQ-50 Unchanged tree.** IF a lost or `no-change` attempt left no commit and the tree is clean,
  THEN `outcome` SHALL take the review record the attempt answered as its verdict (source
  `unchanged-tree`) without a new review.
- **REQ-51 Progress.** WHEN `outcome` has a recheck record, THE helper SHALL compute progress by
  DM-16 from that record and the record the attempt answered.
- **REQ-52 Next step after the local slot.** WHEN a `local` attempt ends `rejected`, `no-change` or
  `worker-lost` with a clean tree, THE helper SHALL report next action `classify` (for
  `rejected`) or `reserve-escalated` (otherwise) only if the policy file authorizes escalation
  for the harness and no non-cancelled `escalated` attempt exists, and SHALL otherwise close the
  episode `exhausted` with detail `local` and report next action `stop`.
- **REQ-53 After escalation.** WHEN an `escalated` attempt ends with any outcome other than
  `accepted`, THE helper SHALL close the episode `exhausted` with detail `escalated` and report
  next action `stop`, unless a violation or stop terminal of DM-10 applies first.
- **REQ-54 Stop terminals.** WHEN an attempt ends `scope-exceeded`, `frozen-tests-changed`,
  `foreign-change`, `contract-changed`, `worker-blocked`, `provider-stopped`, `recheck-blocked`,
  `recheck-unrecorded` or `worker-lost` with a dirty tree, THE helper SHALL close the episode with
  the DM-10 terminal and report next action `stop`.
- **REQ-55 Acceptance.** WHEN the recheck record's verdict is `DONE`, THE helper SHALL report
  outcome `accepted`, close the episode `accepted` and report next action `continue`, and THE
  Orchestrator SHALL continue the run at step 4.4.
- **REQ-56 Stop at the end.** WHEN an episode closes with any terminal other than `accepted` or
  `resolved-outside`, THE Orchestrator SHALL stop the run with today's NEEDS WORK stop, keeping the
  branch, commits, findings, ledger and records, and SHALL report the C-5 lines.
- **REQ-57 Provider limits.** IF the harness reports that a dispatched repair worker ended because of
  a usage limit, quota, rate limit or account restriction, THEN THE Orchestrator SHALL run
  `outcome --worker provider-stopped`; IF it refuses the spawn for such a reason, THEN THE
  Orchestrator SHALL run `cancel --reason provider-limit` and `close` (terminal `stopped`, detail
  `provider-stopped`); in neither case SHALL it switch accounts, providers or models to continue.

### Resume and owner decisions

- **REQ-58 Resume first.** WHEN `/spec-run` resumes with an active policy, THE Orchestrator SHALL run
  `status` for each unreviewed leaf before Step 0 item 3's clean-tree decision and follow the C-5
  resume table before any other mutation of that leaf.
- **REQ-59 Resolved outside.** IF an episode is open, the leaf block records
  `atomic-validation: complete`, and every dispatched attempt of the episode has an `OUTCOME`
  line, THEN `status` SHALL report next action `close` with terminal `resolved-outside`; a
  dispatched attempt without an `OUTCOME` line is handled first by `outcome` or `recheck`.
- **REQ-60 Inactive policy with an open episode.** WHILE the policy is inactive, THE Orchestrator
  SHALL leave any open episode and its ledger unchanged and start no attempt; WHEN the policy is
  active again, `status` SHALL continue that episode with its recorded slots.
- **REQ-61 Ledger integrity.** IF a line inside `## Repair Episodes` does not match DM-3, a
  record named by a line is missing for an open episode or has a different SHA-256, or the lines
  violate DM-3's order rules, THEN every helper subcommand except `version` and `check-policy`
  SHALL exit 1 with `ledger-invalid`.
- **REQ-62 Orphan records.** WHEN the helper computes the next attempt or classification number, THE
  helper SHALL use one more than the greatest number among the episode's lines and its record
  files under `classifications/`, `contracts/` and `outcomes/` (not `context/`), so that a record
  saved without its line is never reused.

### Rule, workflows and delivery

- **REQ-63 Rule.** THE rule `rules/contract-repair.md` SHALL have the front matter, sections and
  anchored lines of C-4, and `version` SHALL print the same registries.
- **REQ-64 Workflow edits.** THE files of C-7 SHALL contain the C-7 text, and every phrase that an
  existing frozen check reads in them SHALL stay byte-identical.
- **REQ-65 New workflow.** THE workflow `workflows/pae-repair.md` SHALL implement C-6 and be named
  in `docs/USAGE.md` and the pipeline reference.
- **REQ-66 Protected ledger.** THE `## Repair Episodes` section SHALL be listed in
  `rules/workflow-reference.md → ## Protected Sections Contract` under task-level `state.md`.
- **REQ-67 Ignore rule.** THE repository's `.gitignore` SHALL contain `/.ai/tasks/*/*/repairs/`, and
  the consumer entry list of `scripts/setup-new-project.sh` and `docs/USAGE.md` SHALL contain
  `.ai/tasks/*/*/repairs/`.
- **REQ-68 Frozen validator.** THE delivered change SHALL leave every check expression of
  `scripts/validate-contracts.sh` and every file under `tests/` byte-identical, and the full
  validator SHALL finish with zero failures.
- **REQ-69 Golden regression.** THE delivered change SHALL pass `python3 -I tests/golden-runs.py`
  with no change to its expectations.
- **REQ-70 Standalone suite.** THE acceptance suite SHALL be `scripts/check-repair-episode.py`, run
  directly and called by neither `scripts/validate-contracts.sh` nor `scripts/sync.sh`.
- **REQ-71 Rule deployment.** THE delivered change SHALL register `rules/contract-repair.md` in the
  rule deployment mechanism current at delivery (today `scripts/setup-new-project.sh` and
  `scripts/sync.sh`, `scripts/validate-contracts.sh:1293-1305`).
- **REQ-72 Decision record and knowledge.** THE delivered change SHALL add an Accepted ADR indexed in
  `.ai/adr/index.md` recording the stop change, the ledger, the slots, the classification and
  escalation rules and the opt-in, and SHALL update the files listed in C-12.
- **REQ-73 Vocabulary.** THE delivered change SHALL add the terms Repair episode, Repair attempt,
  Repair contract, Repair classification and Repair escalation to `.ai/principles/domain.md` before
  the rule uses them (Repair escalation is distinct from the class-A/B escalation protocol,
  `rules/orchestration.md:136`).
- **REQ-74 No saving claim.** THE delivered documentation, ADR and reports SHALL state that no
  quality, token, cost or time effect of the repair policy has been measured and that comparison
  belongs to spec 09.
- **REQ-75 Unlisted helper failures.** IF a helper subcommand run by the repair loop exits 1, 2, 3 or
  4 with a reason that C-5 does not map, or `outcome` exits 1 `review-required` a second time for
  one attempt, THEN THE Orchestrator SHALL stop with the C-9 `repair-state` message, leaving the
  episode open and appending no line.

## Data Model

All entities are **new**. JSON is canonical JSON as in spec 15 (UTF-8, sorted keys,
`ensure_ascii=False`, separators `,` and `:`, one trailing LF); a self-digest is computed over
the canonical JSON without its own key; a digest is `sha256:` + 64 lowercase hex. Paths inside
records are POSIX paths relative to the repository top level of `WORK_DIR`, without `..` or a
leading `/`, unless a field says "task-relative".

### DM-1 Locations

| Location | Content | Writer | Lifecycle |
|---|---|---|---|
| `<task>/state.md → ## Repair Episodes` | Ledger lines (DM-3) | Orchestrator | Append-only, protected; created after the last existing section on the first line |
| `<task>/state.md → ## Task Analysis → ### Assumptions` | Owner decision lines (DM-4) | Owner, or the Orchestrator on an explicit owner message | Never removed |
| `<task>/repairs/drafts/<leaf_id>.classification.json` | DM-6 draft | Validator | Overwritable; read only through `classify --draft` |
| `<task>/repairs/classifications/<episode_id>.C<n>.json` | DM-7 record | Orchestrator saves helper output | Write-once |
| `<task>/repairs/contracts/<attempt_id>.json` | DM-8 contract | Orchestrator saves helper output | Write-once |
| `<task>/repairs/context/<attempt_id>.json` | DM-8 `context_answers` input | Orchestrator | Written before `reserve`; replaceable until a `RESERVED` line names the attempt, then never changed; not counted by REQ-62 |
| `<task>/repairs/outcomes/<attempt_id>.json` | DM-10 record | Orchestrator saves helper output | Write-once |

Records are saved with spec 15's `checkpoint_save TMP FINAL no`
(`.ai/specs/15-orchestrator-overhead.md` C-5, `checkpoint_save`): the helper's stdout `record` value is written
to `<final>.tmp`, then linked; `saved` and `duplicate` proceed, `conflict` and `link-failed` stop
(REQ-31). Directories are created with `mkdir -p` on the first save. `<task>/repairs/` is ignored
(REQ-67) and moves with the task directory; `/compress-state` does not touch it. Deleting it while
an episode is open makes the ledger invalid (REQ-61); deleting it after every episode closed loses
only detail, not limits, because limits come from the ledger lines. Migration: none; a task
without the section has no episodes.

### DM-2 Identifiers

| Identifier | Form | Example |
|---|---|---|
| `leaf_id` | Spec 15's pattern `^T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?$` | `T-04d-fix-rounding` |
| `episode_id` | `<leaf_id>.E<n>`, `n` = 1 + number of `opened` lines of the leaf | `T-03.E1` |
| `attempt_id` | `<episode_id>.A<m>`, `m` per REQ-62 | `T-03.E1.A2` |
| Classification number | `C<n>`, `n` per REQ-62 | `C2` |
| Review reference | `#<seq> sha256:<hex>`: the spec-16 record `reviews/<leaf_id>/<seq>.json` and its file SHA-256 | `#3 sha256:9f…` |

`attempt_id` matches spec 18's `reference` pattern (`.ai/specs/18-reasoning-effort-policy.md`
DM-6) and is distinct from spec 15's `<leaf>.<role>.<n>`; the spawn of a repair attempt's Implementer
has its own spec 15 `attempt_id` (REQ-35, C-5 step 8).

### DM-3 Ledger `## Repair Episodes`

Each line is a full-line match of one form (`EP` = episode id, `AT` = attempt id, `HEX` =
64 lowercase hex, `MODEL` = `(anthropic|openai)/[^\s|;]{1,256}|session-default`, `KEY` = a spec-18
DM-5 key or `none`):

```text
OPENED     ^- (EP) \| opened \| contract sha256:(HEX) \| review #([1-9][0-9]*) sha256:(HEX) \| policy bounded-local@1 file (none|[a-z0-9][a-z0-9-]{0,63}@[0-9]+(\.[0-9]+){0,3} sha256:HEX) \| prior (none|EP(,EP)*)$
CLASSIFIED ^- (EP) \| classified \| C([1-9][0-9]*) record sha256:(HEX) \| review #([1-9][0-9]*) \| eligible (yes|no) \| reasons (none|[a-z-]+(,[a-z-]+)*)$
RESERVED   ^- (AT) \| reserved \| slot (local|escalated) \| model (MODEL) \| effort (KEY) \| record sha256:(HEX)$
DISPATCHED ^- (AT) \| dispatched$
CANCELLED  ^- (AT) \| cancelled \| (spawn-refused|provider-limit|owner-confirmed-undispatched)$
OUTCOME    ^- (AT) \| outcome (OUTCOME) \| review (none|#[1-9][0-9]*) \| source (review|unchanged-tree|none) \| progress (resolved|progress|no-progress|regression|not-assessed) \| record sha256:(HEX)$
CLOSED     ^- (EP) \| closed \| (TERMINAL) \| ([a-z-]+)$
```

`OUTCOME` and `TERMINAL` are the registries of C-4. Order rules: an episode's lines follow
`OPENED`, then repeating groups of `CLASSIFIED` and attempts; an attempt has exactly one
`RESERVED`, then at most one of `DISPATCHED`/`CANCELLED`, then (only after `DISPATCHED`) at most one
`OUTCOME`; `CLOSED` is last; at most one episode per leaf is open (no `CLOSED`). Lines of different
leaves may interleave. The `contract` digest of `OPENED` is the record's `contract.contract_digest`.
Every `record sha256:` value is the SHA-256 of the saved record file's bytes (not its
`record_digest`); the `contract sha256:` of `OPENED` is spec 16's `contract_digest`. A line never
contains `; `. Reader tolerance: a task without the section has no episodes; blank
lines inside the section are ignored.

### DM-4 Owner decision lines

In `## Task Analysis → ### Assumptions`, full-line matches:

```text
REOPEN ^- repair-reopen: (EP) — .+ \(source: user\)$
CANCEL ^- repair-cancel: (AT) — not dispatched \(source: user\)$
```

`REOPEN` permits one new episode of the leaf after episode `EP` (REQ-19); it is valid while no
`OPENED` line of a later episode lists `EP` in its `prior` (every later episode lists all earlier
episodes of the leaf, so a reopen is used once). `CANCEL`
permits `cancel --reason owner-confirmed-undispatched` for `AT` (REQ-34). The Orchestrator writes
these lines only when the owner states the decision in the session.

### DM-5 Policy file (owner configuration)

Path: `${XDG_CONFIG_HOME}/orchestrail/repair-policy.json` when `XDG_CONFIG_HOME` is set and
non-empty, otherwise `~/.config/orchestrail/repair-policy.json`. Optional; no workflow creates it.
At most 1,048,576 bytes; duplicate keys, unknown keys, `NaN`/`Infinity` are invalid.

```json
{"schema_version": 1, "policy_id": "owner-repair", "policy_version": "1", "start": "local",
 "escalation": {"claude": {"model": {"provider": "anthropic", "id": "example-strong"}, "effort": null}}}
```

| Field | Rule |
|---|---|
| `schema_version` | `1` |
| `policy_id` | `^[a-z0-9][a-z0-9-]{0,63}$` |
| `policy_version` | `^[0-9]+(\.[0-9]+){0,3}$` |
| `start` | `local` or `escalated` |
| `escalation` | Object with 0–2 keys from `claude`, `codex`; each value `{"model": identity or null, "effort": token or null}` with at least one non-null; `model` = `{"provider", "id"}` with provider `anthropic` for `claude` and `openai` for `codex`, `id` a non-empty string without whitespace, `|` or `;`; `effort` matches `^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$` |

Escalation is authorized for a harness exactly when `escalation` has its key. `start: escalated`
without an entry for the current harness is reported by `reserve` as `escalation-unauthorized`
(terminal `escalation-unavailable`). The file never authorizes a model the owner did not name.

### DM-6 Classification draft (`repair_classification_draft`)

```json
{"schema_version": 1, "kind": "repair_classification_draft", "leaf_id": "T-03",
 "review": {"seq": 2, "file_sha256": "sha256:…"},
 "findings": [{"finding": "T-03/F1", "class": "local-defect",
   "reproduction": {"kind": "failing-check", "test": null, "check": "test"},
   "expected": "parse_amount returns Decimal('1.50') for '1.5'", "question": null}]}
```

| Field | Rule |
|---|---|
| `findings[].finding` | Every id with status `open` in the record, exactly once, in record order |
| `class` | `local-defect`: wrong behaviour inside the leaf's files under an unchanged contract; `test-missing`: an unchanged criterion lacks a test; `missing-context`: the fix depends on a fact that exists in project artifacts but not in the leaf contract; `test-basis`: a frozen test is wrong or would have to change; `infrastructure`: an environment, tool or network failure without a proven code defect; `contract-divergence`: architecture, an ambiguous criterion, an interface or shared contract; `hard-stop`: security, data integrity, Off-limits or an invariant |
| `reproduction.kind` | `frozen-test` (a named frozen test fails; `test` = `<path>::<name>`; it *exists* when `path` is in the frozen set and the file exists; the name is not checked), `failing-check` (the record finding's `check` is non-null and names `check`), `new-test` (a new failing test must precede the fix), `coverage` (a new test closes a coverage gap and may pass), `inspection` (no executable form) |
| `expected` | Non-empty single line: the correct behaviour and its source (criterion or finding) |
| `question` | Non-empty single line iff `class` is `missing-context`, else `null` |

Permitted reproduction kinds by class and test mode (DM-17):

| Class | `ordinary` | `pre-tdd` | `characterize` | `n-a` |
|---|---|---|---|---|
| `local-defect`, `missing-context` | `frozen-test`, `failing-check`, `new-test` | `failing-check`, `new-test` | `frozen-test`, `failing-check` | `failing-check`, `inspection` |
| `test-missing` | `coverage` | `coverage` | none (ineligible) | none (ineligible) |
| any other class | — (ineligible) | — | — | — |

### DM-7 Classification record (`repair_classification`)

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"repair_classification"` |
| `episode_id`, `seq` | Episode and classification number |
| `review` | `{"seq", "file_sha256", "verdict", "contract_digest", "subject_head"}` of the record |
| `test_mode` | DM-17 |
| `findings` | Per open finding: `{"finding", "severity", "draft_class", "overrides", "class", "reproduction", "expected", "question"}`; `overrides` the sorted override codes that applied |
| `unmet_obligations` | Obligation ids with state `failed` or `unverified` |
| `eligible`, `reasons` | Boolean; sorted reason codes |
| `record_digest` | Self-digest |

**Review checks** (`open`, `classify`, `outcome`): the file is `reviews/<leaf_id>/<seq>.json`
under `<task>/verification/`, at most 1,048,576 bytes, parses as JSON with `schema_version` 1,
`kind` `review_record`, `level` `leaf`, `step` `check`, `scope_key` equal to the leaf, a
self-digest `record_digest` that verifies, and a SHA-256 equal to the leaf's last spec-16 DM-8
entry for step `check` (`.ai/specs/16-scoped-verification.md` DM-8).

**Overrides**, per open finding: `critical` severity → `hard-stop` (`critical-severity`); any
obligation id `INV-*` or `OFF-*` → `hard-stop` (`invariant-or-off-limits`); any listed obligation
whose record `risks` contain `security` or `data-integrity` → `hard-stop` (`risk-hard`); `contract`,
`migration`, `shared-dependency` or `uncertain` → `contract-divergence` (`risk-contract`); a
`locations` path equal to a `target_files:` entry of another leaf block (resolved against that
leaf's `working_dir:` as spec 16 DM-5 (7) does) → `contract-divergence` (`cross-leaf`).
**Restriction order** (most restrictive first): `hard-stop`, `contract-divergence`, `test-basis`,
`infrastructure`, `missing-context`, `test-missing`, `local-defect`.

**Eligibility reasons** (all applying, sorted): `draft-invalid`, `class-ineligible` (an effective
class outside `local-defect`, `test-missing`, `missing-context`), `owner-decision-pending`,
`reproduction-invalid`, `unlinked-obligation`, `verdict-not-needs-work`, `frozen-set-unknown`
(test mode `ordinary` or `characterize` and no `test`-type commit recorded), `frozen-location` (an open
finding whose effective class is `local-defect` or `missing-context`, whose `locations` list is
non-empty, and none of whose `locations` paths is in `allowed_paths`, so no repair could change
it; a finding that also lists a frozen test location stays eligible; an empty `locations` list
does not trigger it, because the stage checks still confine every change to `allowed_paths`;
`test-missing` findings are never checked, because their fix is a new test file),
`no-open-finding`.

### DM-8 Repair contract (`repair_contract`)

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"repair_contract"` |
| `episode_id`, `attempt_id`, `slot`, `task_id`, `leaf_id` | Identifiers; `task_id` = base name of the task directory |
| `policy` | `{"name": "bounded-local", "version": 1, "file": null or {"policy_id", "policy_version", "sha256"}}` |
| `contract_digest` | The episode's spec-16 contract digest |
| `description` | `{"path" (task-relative), "sha256"}` |
| `design_sha256` | Digest of the bytes of `## Solution Design` in `state.md` (C-3 extent) |
| `packet` | `{"packet_digest", "task_contract_hash"}`, each from the command line or `null` |
| `review` | `{"seq", "file_sha256", "verdict"}` of the record this attempt answers |
| `classification` | `{"seq", "record_digest"}` |
| `start` | `{"branch", "head", "worktree_id"}` (`worktree_id` as spec 15 defines it); `head` must equal the review record's `subject.head` and the tree must be clean outside the task directory and `AI_DIR` (this spec's definition; spec 16's `subject.clean` is not read because it also counts `AI_DIR` paths), else `reserve` exits 1 `tree-changed` |
| `test_mode`, `frozen_tests`, `frozen_tests_digest` | DM-17; DM-14 list `{"path", "sha256"}`; digest of its canonical JSON |
| `allowed_paths` | DM-15 |
| `required_checks` | Defined checks of the runbook by spec 16 DM-9, in the order `test`, `lint`, `typecheck` |
| `findings` | Per open finding: the record's `findings[].id` (copied as `finding`) and `severity`, `title`, `obligations` (each `{"id", "kind", "state"}`), `locations`, `evidence`, `check`, `same_as`; classification fields `class`, `reproduction`, `expected`; `context_answer` (`null` or `{"question", "answer", "source"}`) |
| `evidence_refs` | `{"tdd_output": [...], "checks": [...]}`. `tdd_output`: the leaf's `tdd: red output` and `tdd: green output` notes lines copied verbatim (spec 17 DM-9; the lines are never reworded or re-derived). `checks`: for each distinct non-null `check` of the open findings, the answered record's `checks[]` entry of that name, as `{"check", "receipt_id", "mode", "stdout_sha256", "stderr_sha256", "reference", "artifact_id", "manifest_sha256"}` read from the referenced spec 16 DM-4 receipt (found as `receipts/*/<hex of receipt_id>.json` under `<git common dir>/orchestrail-verification/`, searching the `<inputs hex>` subdirectories, spec 16 DM-1). By `output.mode`: `direct` fills `stdout_sha256` and `stderr_sha256` from `output.stdout.sha256` and `output.stderr.sha256` (each `null` when capture failed) and leaves `reference`, `artifact_id` and `manifest_sha256` `null`; `capture-output` fills `reference`, `artifact_id` and `manifest_sha256` from `output.reference`, `output.artifact_id` and `output.manifest_sha256` and leaves both stream digests `null`, because spec 16 stores no stream digests in that mode (spec 16 DM-4a, spec 17 helper). A receipt that is missing, unreadable or of another shape gives `mode` `null` and every other field after `receipt_id` `null`: an evidence gap, never an error. The helper copies references only; it does not read captured bytes, run `verify`, or judge them. Empty lists when absent |
| `dispatch` | `{"role": "implementer", "model": {"requested", "resolved", "actual": null, "status"}, "effort": {"decision_key", "outcome", "resolved"} or null, "escalation": null or {"model", "effort"}}` from the command-line inputs |
| `slots` | `{"local": {"used", "limit": 1}, "escalated": {"used", "limit": 1}}` counting non-cancelled attempts including this one |
| `previous_attempts` | `{"attempt_id", "slot", "outcome", "progress", "record_sha256"}` in order |
| `blocker_codes` | The C-4 `Repair blockers:` registry |
| `report_forms` | `["RED", "GREEN"]` when any reproduction is `new-test` or `coverage`, else `["GREEN"]` |
| `record_digest` | Self-digest |

`context_answers` input file: a JSON list of `{"finding", "question", "answer", "source"}`, one per
`missing-context` finding, `question` equal to the classification's, `answer` and `source`
non-empty single lines; else `reserve` exits 1 `context-answer-missing`.

### DM-9 Stage check result (`repair_stage_check`, stdout of `check`)

`{"schema_version": 1, "kind": "repair_stage_check", "attempt_id", "stage", "dirty": [...],
"stage_paths": [...], "violations": [...], "frozen_tests": "intact"|"changed"}`. `dirty` are the
paths `git status --porcelain=v1 -z --untracked-files=all --no-renames` reports, excluding the task
directory and `AI_DIR`; `stage_paths` are `dirty` relative to `WORK_DIR` when `violations` is empty,
else `[]`; `violations` ⊆ `scope-exceeded`, `frozen-tests-changed`, `contract-changed`,
`nothing-to-stage`. Stage `red`: every dirty path must be untracked and none may be in the frozen
set. Stage `green`: every dirty path must be tracked and in `allowed_paths`. An empty `dirty`
reports `nothing-to-stage`.

### DM-10 Outcome record (`repair_outcome`)

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"repair_outcome"` |
| `attempt_id`, `episode_id`, `slot` | Identifiers |
| `worker` | `reported`, `blocked`, `lost` or `provider-stopped`; `blocker` code or `null` |
| `commits` | `{"sha", "type", "paths"}` for every commit from `start.head` (exclusive) to `HEAD` |
| `tree_clean` | Boolean (outside the task directory and `AI_DIR`) |
| `frozen_tests` | `intact` or `changed` |
| `review` | `{"seq", "file_sha256", "verdict", "scope", "minimum_scope"}` or `null` |
| `verdict_source` | `review`, `unchanged-tree` or `none` |
| `outcome` | First matching row below |
| `progress` and its lists | DM-16 |
| `terminal`, `detail` | When the episode ends: the terminal of the row, else `null` |
| `next_action` | `continue` (outcome `accepted`), `classify`, `reserve-escalated`, or `stop` (every other terminal) |
| `record_digest` | Self-digest |

| Outcome (first match) | Condition | Terminal / detail |
|---|---|---|
| `foreign-change` | REQ-49 | `violation` / `foreign-change` |
| `frozen-tests-changed` | REQ-42 | `violation` / `frozen-tests-changed` |
| `scope-exceeded` | A commit of the attempt fails DM-9's stage rule for its type (`test` → stage `red`, `fix` → stage `green`), ignoring bookkeeping paths inside the task directory or `AI_DIR` (`rules/git-flow.md:156-164`); or the tree is dirty with `worker: reported` | `violation` / `scope-exceeded` |
| `contract-changed` | REQ-43 | `contract-changed` / `contract-changed` |
| `provider-stopped` | `worker: provider-stopped` | `stopped` / `provider-stopped` |
| `worker-blocked` | `worker: blocked` | `stopped` / `worker-blocked-<code>` |
| `worker-lost` | `worker: lost` and the tree is dirty | `stopped` / `worker-lost-dirty` |
| `recheck-blocked` | The leaf's last DM-8 entry for step `check` is `none — blocked` written after the answered record's entry, or the leaf block's `blocker:` starts with `verification check ` (spec 16 DM-8 reason `blocked` and REQ-56) | `stopped` / `recheck-blocked` |
| `recheck-unrecorded` | Commits exist and the leaf's last DM-8 entry for step `check` is any other `none` entry written after the answered record's entry | `stopped` / `recheck-unrecorded` |
| `accepted` | Review verdict `DONE` | `accepted` / `recheck-done` |
| `rejected` | Review verdict `NEEDS WORK` | per REQ-52/REQ-53 |
| `no-change` | No commit, clean tree, `worker: reported` | per REQ-52/REQ-53 |
| `worker-lost` | `worker: lost`, clean tree | per REQ-52/REQ-53 |

When the policy file authorizes no escalation, REQ-52 yields terminal `exhausted` / `local`; after an
`escalated` attempt REQ-53 yields `exhausted` / `escalated`.

### DM-11 Status result (`repair_status`, stdout of `status`)

`{"schema_version": 1, "kind": "repair_status", "leaf_id", "episode": null | {"episode_id",
"slots": {...}, "last_line"}, "next_action", "detail", "next_attempt_id"}`. `next_action` (first
matching rule): `none` (no open episode, and either the leaf is not `atomic-validation: failed` or its
newest record has no NEEDS WORK verdict); `open` (no open episode, leaf failed with a NEEDS WORK record); `stop` with detail
`dispatch-unknown` (REQ-34 without a `CANCEL` line); `cancel` (REQ-34 with a `CANCEL` line);
`outcome` (dispatched attempt without outcome and a newer DM-8 entry for step `check`);
`recheck` (dispatched attempt without outcome, attempt commits exist, clean tree, no newer entry);
`dispatched-pending` (dispatched attempt without outcome, no attempt commit); `close` (open episode
whose leaf is `atomic-validation: complete` → `resolved-outside`; a missing `CLOSED` after an
ineligible classification, a terminal outcome or a `provider-limit` cancellation; or a slot holding
two `spawn-refused` cancellations → `stopped` / `dispatch-refused`); `classify` (last line `OPENED`, or last outcome
`rejected` whose review is not yet classified); `reserve-local` /
`reserve-escalated` (eligible classification and no pending attempt, by DM-5 `start` and REQ-04,
REQ-52). `next_attempt_id` is the id `reserve` would assign.

### DM-12 Result line and errors

Every subcommand prints exactly one canonical JSON line on stdout: `{"ok": true|false,
"subcommand", …}`. Subcommands that produce a ledger line add `line` (the exact text to append);
those that produce a record add `record` (the object) and `record_path` (task-relative). `reserve`
adds `dispatch_line`; `classify` and `outcome` add `close_line` (or `null`). Refusals (exit 1) add `reasons` (C-2);
exits 2–4 add `error` and `detail`. stderr carries one line `<code>: <detail>` per reason, without
file contents.

### DM-13 Notes entries

Appended by `/pae-repair` to its own leaf block's notes with spec 14's append rule
(`.ai/specs/14-task-context-and-reuse.md` DM-11); never edited or removed; protected like other
`tdd:` lines:

```text
^tdd: repair red — (AT) — (T-[^ ]+/F[1-9][0-9]*) — (frozen-test|failing-check|new-test|coverage|inspection) → [^;]+( — OUTPUT [^;]+)?$
^tdd: repair green — (AT) — (T-[^ ]+/F[1-9][0-9]*)(,T-[^ ]+/F[1-9][0-9]*)*( — OUTPUT [^;]+)?$
```

The arrow part names the test ids or the check observed and the observed result (`fails`,
`passes`). The optional ` — OUTPUT …` suffix is spec 17's OUTPUT line when the run was captured.
The original `tdd: red digest`, `tdd: red output` and `tdd: green output` lines stay untouched.

### DM-14 Frozen test set

Entries of the leaf's `commits:` value are parsed by DM-18. For each entry whose type is `test`:
the paths of `git diff-tree -r -z --no-commit-id --name-only --no-renames <sha>`, excluding the
task directory and `AI_DIR`. Their union, sorted, each with the SHA-256 of its current bytes
(`null` when deleted), is the frozen set — including a RED test file that a later commit also
touched (an added test or a recorded amendment) and a collection-only stub committed with the
tests (`workflows/pae-tests.md:151-155`), which has no machine-readable marker. Test files that the
implementation commit added are not frozen, as `rules/tdd.md:171` and `:189` define the frozen set; the
recheck judges changes to them. It includes the `test:` commits of earlier repair attempts. A leaf
with test mode `n-a` or `pre-tdd` and no `test` commit has an empty set.

### DM-18 `commits:` parsing

The value is split on `, `; a piece starts a new entry only when it matches
`^[0-9a-f]{7,40} [a-z]+(\([^)]*\))?: `, otherwise it is joined to the previous piece with `, `
(summaries may contain commas, `rules/workflow-reference.md:218`). A leading piece that matches
nothing, or an entry whose sha does not resolve to exactly one commit through
`git rev-parse --verify --quiet <sha>^{commit}`, makes every subcommand that reads the frozen set
or the attempt's commits exit 1 `commits-invalid`. Entries are matched to commits by full object
name after resolution. The type is the word before the optional scope.

### DM-15 Allowed paths

The union, sorted, of the leaf block's `target_files:` entries and the leaf description's
`## Scope` line starting `Target files:` (split on `,`, trimmed), each resolved against the leaf's
`working_dir:` and kept only when inside the work tree of `WORK_DIR`; minus every frozen test path.
New files are never allowed paths; a repair creates new files only as test files at stage `red`.

### DM-16 Progress

Let `P` be the open finding ids of the record the attempt answered and `R` the recheck record.
`resolved` = ids of `P` whose `R` outcome is `resolved`; `remains` = `remains` or `owner-decision`;
`withdrawn` = `withdrawn`; `owner_accepted` = `owner-accepted`; `new` = findings of `R` with status
`open` whose id is not in any earlier record of the episode; `repeats` = members of `new` whose
`same_as` chain (followed through earlier records of the leaf) reaches an id of the episode;
`regressed_obligations` = obligations `verified` or `carried` in the answered record and `failed` or
`unverified` in `R`. Progress: `resolved` when `R` verdict is `DONE`; `regression` when
`regressed_obligations` is non-empty or `new` minus `repeats` contains a `critical` or `important`
finding; `progress` when `resolved` is non-empty; `no-progress` otherwise; `not-assessed` without
`R`. Progress is recorded and reported; it never grants an additional slot.

### DM-17 Leaf test mode

`n-a` when `atomic-tests: n-a`; `pre-tdd` when the field is absent; `characterize` when a notes entry
starts with `tdd: characterize — `; otherwise `ordinary`.

## Contracts & Interfaces

### C-1 Command line

```text
python3 -I "$ORCHESTRAIL_HOME/scripts/repair-episode.py" version
python3 -I … check-policy --policy FILE [--harness claude|codex]
python3 -I … status   --work W --task T --leaf L [--policy FILE | --no-policy] --harness H
python3 -I … open     --work W --task T --leaf L --review R [--policy FILE | --no-policy]
python3 -I … classify --work W --task T --episode E --review R --draft D
python3 -I … reserve  --work W --task T --episode E --slot local|escalated --harness H
                      [--policy FILE | --no-policy] --model MODEL.json [--local-model LOCAL.json]
                      [--effort DECISION.json] [--context-answers A.json] [--packet-digest D]
                      [--task-contract-hash H]
python3 -I … check    --work W --task T --attempt A --stage red|green
python3 -I … outcome  --work W --task T --attempt A [--worker reported|blocked|lost|provider-stopped]
                      [--blocker CODE] [--review R] [--policy FILE | --no-policy] --harness H
python3 -I … cancel   --work W --task T --attempt A --reason spawn-refused|provider-limit|owner-confirmed-undispatched
python3 -I … close    --work W --task T --episode E [--terminal CODE --detail CODE]
```

- Argument forms: `--work` the absolute `WORK_DIR`; `--task` the task directory path; `--leaf` a
  `leaf_id`; `--episode` and `--attempt` DM-2 ids; `--review` and `--draft` file paths (absolute or
  relative to the current directory); `--harness` `claude` or `codex`.
- `MODEL.json` is spec 04's resolution report for the spawn (`status`, `requested`, `resolved`), or
  `{"status": "session-default", "requested": null, "resolved": null}`; `--local-model` (required
  for `--slot escalated`, forbidden otherwise) is the same for the local resolution;
  `DECISION.json` is `{"decision": <spec 18 DM-7 object>, "key": <spec 18 DM-5 key>}`; a file of
  any other shape (extra or missing key, `key` not matching 18 DM-5 `KEY`, `decision.kind` not
  `effort_decision`) → exit 2 `json-invalid`. For `--slot escalated`, `reserve`
  applies C-8 steps 1–4 to these inputs and exits 1 with `escalation-unauthorized`,
  `model-unresolved` (a declared model whose `MODEL.json` status is not `resolved`),
  `effort-not-applied` (a declared effort whose decision does not resolve, or a missing
  `--effort`) or `escalation-identical`. `--worker` defaults to `reported` when the leaf notes hold
  a `tdd: repair green — <attempt_id>` entry and to `lost` otherwise; `--blocker` is required iff
  `--worker blocked`.
- `close` without `--terminal` derives the closing line from the ledger when the last outcome
  record or classification record names a terminal and no `CLOSED` line follows (recovery after an
  interruption), or when REQ-59 applies (`resolved-outside` / `leaf-complete`), or when the second
  `spawn-refused` cancellation of a slot exists (`stopped` / `dispatch-refused`); otherwise it exits
  1 `attempt-state`. Also derivable: a `provider-limit` cancellation → `stopped` /
  `provider-stopped`. `--terminal` with `--detail` is accepted only for the pairs the Orchestrator
  decides: `ineligible` / `intent-unresolved`, `escalation-unavailable` with `escalation-unauthorized`,
  `escalation-identical`, `model-unresolved`, `effort-not-applied` or `resolver-unusable`, and
  `stopped` / `tree-changed`; any other pair → exit 2 `usage`.
- `version` prints `{"ok": true, "subcommand": "version", "schema_version": 1, "record_schemas":
  {...}, "registries": {...}}` with the registries of C-4.
- Git runs with `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `LC_ALL=C`, no pager, using only
  `rev-parse`, `status`, `diff-tree`, `rev-list`, `merge-base --is-ancestor`, `cat-file` and
  `ls-files`. No clock, random value or environment value other than `PATH`, `HOME`,
  `XDG_CONFIG_HOME`, `ORCHESTRAIL_HOME` and `ORCHESTRAIL_REPAIR_POLICY` is read.

### C-2 Exit codes and reason codes

| Exit | Meaning | Codes |
|---|---|---|
| 0 | Completed; the printed result may report `eligible: false`, violations or a terminal | — |
| 1 | Refused | `ledger-invalid`, `commits-invalid`, `episode-open`, `reopen-required`, `review-unavailable`, `review-invalid`, `leaf-state` (`open` or `reserve` while the leaf is not `atomic-execution: complete` with `atomic-validation: failed`), `slot-exhausted`, `slot-order`, `attempt-pending`, `escalation-unauthorized`, `model-unresolved`, `effort-not-applied`, `escalation-identical`, `context-answer-missing`, `tree-changed`, `attempt-unknown` (no such attempt), `attempt-state` (the subcommand does not fit the attempt's or episode's last line), `review-required`, `policy-invalid` (`open`, `status`, `reserve`, `outcome` given an invalid policy file), `cancel-unauthorized` |
| 2 | Invalid invocation | `usage`, `path-invalid`, `input-too-large`, `json-invalid` |
| 3 | Unavailable | `runtime-unavailable` (Python < 3.11; the entry file as a whole uses only syntax older Python 3 interpreters parse and loads 3.11-only code after the check, so this code, not a syntax error, results, as spec 20 A-26), `git-unavailable`, `not-a-repository` |
| 4 | Disabled | `disabled` (`ORCHESTRAIL_REPAIR_POLICY` disabling per REQ-11, e.g. `=off`; every subcommand except `version` and `check-policy`) |

### C-3 Parsing rules

Headings, sections, list items and leaf blocks follow spec 16 C-3
(`.ai/specs/16-scoped-verification.md` C-3); notes entries follow spec 15's note-entry rule
(`.ai/specs/15-orchestrator-overhead.md` Data Model → Note entries). The `## Solution Design` extent for
`design_sha256` runs from its heading line to the line before the next `## ` heading. The ledger
section is the single `## Repair Episodes` heading outside fences; a second one → `ledger-invalid`.

### C-4 `rules/contract-repair.md`

Front matter `description: Repair contract — bounded local repair after NEEDS WORK, escalation and
ledger`, `load: on-demand` (spec 13 DM-2; kind `contract` from the file name, no name-map row, no
`trigger:`). Sections `## Repair loop`, `## Classification`, `## Repair attempt`,
`## Ledger`, `## Stop classes`. Anchored lines, each exactly once:

```text
Repair policies: bounded-local
Repair slots: local 1 | escalated 1
Repair classes: local-defect | test-missing | missing-context | test-basis | infrastructure | contract-divergence | hard-stop
Repair reproductions: frozen-test | failing-check | new-test | coverage | inspection
Repair outcomes: accepted | rejected | no-change | worker-lost | worker-blocked | provider-stopped | scope-exceeded | frozen-tests-changed | foreign-change | contract-changed | recheck-blocked | recheck-unrecorded
Repair terminals: accepted | exhausted | ineligible | escalation-unavailable | violation | contract-changed | stopped | resolved-outside
Repair blockers: contract-mismatch | not-reproduced | infrastructure | evidence-gap | red-not-established | repair-scope | test-basis | contract-question
Repair disable: ORCHESTRAIL_REPAIR_POLICY=off
Repair exit codes: 0 completed | 1 refused | 2 invalid-invocation | 3 unavailable | 4 disabled
```

`## Classification` also holds, verbatim: "Classify conservatively: when you cannot show that a
finding is local, use contract-divergence." `## Repair attempt` holds, verbatim: "Never edit a
frozen test, the description, plan.md or another leaf; create new files only as new test files
before any fix; never run git." The drift check (AC-35) splits each line after `: ` on ` | ` and
compares it with `version`'s registry of the same name. Where spec 08's 700-word limit is in force
and the rule exceeds it, the sections move into `rules/contract-repair-<section>.md` files, each
keeping its heading and anchored lines.

### C-5 Repair loop (`contract-repair → ## Repair loop`, performed by the Orchestrator)

0. **Step 0.** Resolve the policy state per REQ-10–REQ-14. On resume with an active policy, run
   `status` for each unreviewed leaf before Step 0 item 3's clean-tree decision
   (`workflows/spec-run.md:64-69`) and follow it per the resume table below (REQ-58).
1. **Validator spawn (4.3).** With an active policy add to the Validator's instruction: "Repair
   policy active: on NEEDS WORK, write the classification draft per
   `contract-repair → ## Classification` before stopping."
2. **NEEDS WORK.** `status` → `open`: run `open`; append `line`. Refusal → stop (C-9).
3. **Classify.** `classify` with `--draft <task>/repairs/drafts/<leaf_id>.classification.json`;
   save `record`; append `line`. `eligible: false` → append its `close_line` and stop (REQ-26).
4. **Context.** For `missing-context` findings, ask the Arbiter (REQ-27, REQ-28); write
   `<task>/repairs/context/<next_attempt_id>.json`.
5. **Resolve.** Slot from `status`. Always compute the leaf's ordinary model resolution
   (`workflows/spec-run.md:139-156`), called the *local resolution*. Local slot: use it and a
   spec-18 decision with `escalation: null`. Escalated slot: C-8 steps 2–3. A spec-18 `stop`, or a
   local resolution that stops, is that existing stop (no repair ledger line; the episode stays
   open). Spec 18 resolver unusable while an escalation declares `effort` → `close --terminal
   escalation-unavailable --detail resolver-unusable`, append, stop.
6. **Packet.** Spec 14 `packet --role implementer --predecessor <digest of the leaf's latest
   implementer context-packet entry>` with its DM-11 entry.
7. **Reserve.** `reserve`; on exit 0 save `record` (`saved` proceeds; `duplicate` proceeds only when
   no `RESERVED` line names the attempt yet) and append `line` (REQ-30, REQ-31). On exit 1 follow
   the reserve-refusal table below.
8. **Plan row and spec-15 record.** Set the plan row per REQ-35; on the spec-15 helper route run
   `attempt --role implementer` and save it.
9. **Spawn.** A fresh Implementer with the REQ-36 inputs and the instruction: "Run `/pae-repair
   <description> --contract <contract path>`; when it reports RED, stop and wait; one message
   resumes you." Append `dispatch_line` (REQ-32), or on refusal `cancel` per REQ-33 / REQ-57; when the refusal names spec 18's effort parameter or value, also append 18's DM-5 rejection line, and the next reservation's step 5 uses `session.parameter: "absent"`.
10. **RED.** On a RED report: `check --stage red`; no violation → commit `stage_paths` (plus allowed
    bookkeeping, REQ-40) as
    `test: <what the tests assert>` under `git-flow → ## Commits`, append the sha to `commits:`,
    send the same worker one continuation message. Any violation → `outcome --worker reported`.
11. **GREEN.** On a GREEN report: `check --stage green`; no violation → commit `stage_paths` (plus
    allowed bookkeeping) as
    `fix: <what was repaired>`, append the sha. `nothing-to-stage` as the only violation → no
    commit (a `coverage` repair whose new tests pass, or no change at all). Any other violation →
    `outcome --worker reported`. Blocker report → `outcome --worker blocked --blocker <code>`.
    Harness reports the worker finished, failed or unknown without a final response →
    `outcome --worker lost` (REQ-57 for provider limits).
12. **Recheck.** After a GREEN report whose `check` passed or reported only `nothing-to-stage`:
    an attempt with at least one commit → recheck; none → `outcome --worker reported` (outcome
    `no-change`). Also when `outcome` exits 1 `review-required` for the first time for the attempt;
    a second `review-required` for the same attempt → stop with `repair-state`. Steps that already
    ran `outcome` (blocker, lost, violation) do not reach this step. Recheck: set the plan row to `done` if it is `blocked`, build the validator
    packet (spec 14 REQ-41), spawn a fresh Validator exactly as 4.3 with step 1's addition (an ordinary spec 16 leaf review
    whose prior is the record the attempt answered; REQ-47); then
    `outcome --review <record>`.
13. **Outcome.** Save `record`; append `line`, then `close_line` when present. `continue` → step
    4.4. `classify` → step 3 with the new draft. `reserve-escalated` → step 5 (escalated).
    `stop` → stop (REQ-56).
14. **Report.** One line per attempt: `repair <attempt_id> slot <slot> model <requested> resolved
    <resolved|none> actual unknown effort <key|none> outcome <outcome> progress <progress> review
    <#seq|none>`; one line per episode: `repair <episode_id> closed <terminal> (<detail>)`.

Steps 10 and 11 keep the order: no `fix:` commit of an attempt precedes its `test:` commit, and the
repair Implementer edits no allowed path before its RED report (C-6 steps 2–3). No step polls a
running worker (spec 15 C-7 triggers apply). A git command never shares a Bash call with a write
of another step.

**Resume table** (`status` next action → Orchestrator action):

| Next action | Action |
|---|---|
| `none` | Continue the ordinary flow |
| `open` | Step 2 |
| `classify` | Step 3 |
| `reserve-local`, `reserve-escalated` | Step 4 when the classification has `missing-context` findings, else step 5 |
| `cancel` | `cancel --reason owner-confirmed-undispatched`; append; continue with the new `status` |
| `dispatched-pending` | In the session that spawned the worker: wait for a C-7 trigger of spec 15. In any later session (the worker is gone): `outcome --worker lost` |
| `recheck` | Step 12 |
| `outcome` | `outcome --review <newest record>` when the newer DM-8 entry names a record, else `outcome` without `--review` (a `none` entry); worker defaulted by C-1; step 13 |
| `close` | `close --episode E`; append; `resolved-outside` → continue the ordinary flow, else stop (REQ-56) |
| `stop` | Stop with the C-9 message for its detail |

A lost worker's uncommitted changes to tracked files stop the resumed run at Step 0 item 1, whose
git-flow preflight refuses any tracked change before the task is resolved
(`rules/git-flow.md:16-22`); `status` cannot run there, and this spec does not change the
preflight. The owner reconciles the tree; afterwards `status` decides: a commit absent from
`commits:` → `foreign-change`; a clean tree without attempt commits → `dispatched-pending`, then
`outcome --worker lost` (`worker-lost`, `unchanged-tree`); attempt commits and a clean tree →
`recheck`. Untracked leftovers pass the preflight and reach `outcome --worker lost` as
`worker-lost-dirty`. In a repository that tracks `.ai/`, ledger lines and notes written after the
last repair commit are uncommitted tracked changes too; the same preflight stop applies, and the
owner commits or reconciles them before resuming (the Orchestrator commits bookkeeping only with
repair commits, REQ-40).

**Reserve-refusal table** (`reserve` exit 1 reason → action):

| Reason | Action |
|---|---|
| `escalation-unauthorized`, `escalation-identical`, `model-unresolved`, `effort-not-applied` | `close --terminal escalation-unavailable --detail <reason>`; append; stop |
| `tree-changed` | `close --terminal stopped --detail tree-changed`; append; stop |
| `context-answer-missing` | Repeat step 4 once, replacing the context file; a second refusal → stop with the episode open (`repair-state`) |
| `policy-invalid` | Stop with the C-9 `repair-policy-invalid` message (the file changed after Step 0) |
| `slot-exhausted`, `slot-order`, `attempt-pending`, `leaf-state`, `ledger-invalid`, `commits-invalid` | Stop with the episode open (`repair-state`); these mean the ledger, the state or `status` disagree |

**General rule.** Any other helper exit 1, 2, 3 or 4 of any subcommand in this loop, and any refusal
not listed above, stops the run with the episode open and the C-9 `repair-state` message (REQ-75).

**Verbatim lines** of `## Repair loop` (each exactly once):

```text
Scope: the repair loop applies only to a NEEDS WORK verdict of a leaf validated through /spec-run step 4.3, including fix-task leaves and composite children run in the stack, never to a composite integration verdict.
Dependents: start no leaf that depends on the repaired leaf before its episode closes accepted or resolved-outside.
End: when an episode closes with any terminal other than accepted or resolved-outside, stop the run with the step 4.3 NEEDS WORK stop and report the repair lines.
Class B: an Arbiter answer without a citation is a class-B question; record it in ## Open Questions (batch), close the episode ineligible with detail intent-unresolved, and stop.
Saving: if saving a repair record ends with conflict or link-failed, append no line, spawn nothing, and stop with repair-save-failed.
Provider: a provider limit never leads to switching accounts, providers or models.
Dry run: with --dry-run, report the repair policy as active, inactive with its cause, or invalid, and append no ledger line and save no record.
Unlisted: any other helper refusal or failure stops the run with repair-state and leaves the episode open.
```

### C-6 `/pae-repair` (workflow contract)

Front matter `description: Atomic Execution Step 4 (Repair) — apply one bounded repair attempt from
a repair contract, test-first` (after spec 13: file `atomic-execution-repair.md` with `phase:
atomic-execution` and `step: 4`, its DM-3 and DM-11); `Invocation: /pae-repair <path-to-atomic-description> --contract
<path>`.

**Metadata for the generated reference docs (spec 10).** The new workflow also carries the three
keys that spec 10 requires of every workflow (`.ai/specs/10-generated-reference-docs.md` REQ-05 and
Data Model → Workflow metadata; a missing key is `metadata-missing-field`, and spec 10 A-54 records
that no other spec prescribes them for this file): `reads`, `writes` and `called_by`. `called_by` is
`[spec-run]` (spec 10 REQ-23: each item names an existing workflow). The file has a `Called by:` line
whose text begins with the backticked command, the form `Called by: ` followed by the backticked
`/spec-run` and the words `(repair loop)`, so that its leading caller list is `spec-run` and agrees
with `called_by` (spec 10 REQ-35, Data Model → Leading caller list). `reads` and `writes` use spec
10's Location grammar (REQ-46) and list only what steps 1–5 below already read and write; nothing is
added for the generator's sake: `reads` holds the atomic description (`<subtask-dir>/description.md`),
the repair contract (`<task-dir>/repairs/contracts/*.json`), the parent `state.md` sections the
workflow reads (`<task-dir>/state.md → ## Subtask Progress`, `<task-dir>/state.md → ## Solution
Design`), `tests` (the frozen set) and `code`; `writes` holds `<task-dir>/state.md → ## Subtask
Progress` (the leaf block fields of step 4), `tests` (new test files only, step 2) and `code`
(allowed paths only, step 3). The workflow never writes `git`, `plan.md` or any ledger (C-7
constraints). Sections:

1. **Guard** — REQ-37; a `tdd: repair green — <attempt_id>` entry already present → **stop**:
   "Repair attempt <attempt_id> already completed."
2. **Reproduce** — working directory and bootstrap as `/pae-implement` (packet per spec 14 when
   supplied); read the contract, frozen tests, description and Solution Design. Per finding:
   `frozen-test` → run that test, it must fail; `failing-check` → run that check, it must exit
   non-zero (spec 17 kind `exit`); `new-test` → write tests in new files, run them, each must fail
   for the expected reason (`rules/tdd.md:86-100`); `coverage` → write tests in new files and record
   pass or fail; `inspection` → inspect and record. A reproduction that passes → blocker
   `not-reproduced`; a new test that passes before the fix → `red-not-established`; DM-3 kinds
   other than `exit` → `infrastructure`; no known outcome → `evidence-gap`. Append DM-13
   `tdd: repair red` entries. With new test files: report the RED form (`Mode: ordinary`, `Test
   commit: pending — created by the orchestrator`) and wait.
3. **Fix** — change only allowed paths, the minimal sufficient change for the listed findings; never
   create a file; a needed change elsewhere → `repair-scope`; a frozen test that would have to
   change → `test-basis`; a class-A question → the Arbiter as `rules/orchestration.md:140-146`
   states; missing intent → `contract-question`.
4. **Verify** — run the whole frozen set, this attempt's new tests and every required check; each
   finding's reproduction must now show the expected behaviour; iterate within step 3 until all pass
   or a blocker applies. Write `last_action: repair <attempt_id> complete — <summary>`, the union in
   `target_files:`, the DM-13 `tdd: repair green` entry; keep the status fields (REQ-46). Report the
   GREEN form with `Frozen tests: intact`.
5. **Blockers** — report the code in the form's `Blockers` field and stop; write no `blocker:` field
   and revert nothing.

Verbatim lines of `/pae-repair` (each exactly once):

```text
RED wait: report RED and wait only when this attempt wrote new test files; otherwise continue to the fix without a RED report.
Status fields: keep atomic-tests, atomic-execution: complete and atomic-validation: failed unchanged.
Infrastructure: a command that ends with launch-error, timeout, interrupted or signal is blocker infrastructure, and one without a known outcome is blocker evidence-gap; change no code to make it pass.
Order: observe every reproduction before editing any allowed path.
```

### C-7 Workflow and rule edits (additive)

| File | Edit |
|---|---|
| `workflows/spec-run.md` | Invocation gains `[--repair-policy bounded-local]` with one bullet; `## Guard` gains REQ-10; Step 0 gains "Repair policy: resolve per `contract-repair → ## Repair loop` step 0; on resume run its `status` for each unreviewed leaf before item 3's clean-tree decision."; 4.3 keeps verbatim its NEEDS WORK stop paragraph (from "If the verdict is NEEDS WORK" to "failing base.", today `:297-299`) and gains, after it, "With an active repair policy, follow `contract-repair → ## Repair loop` first; the run stops here only when that loop ends without acceptance."; `## What this workflow never does` gains "Never starts a repair attempt without an active repair policy, or beyond the slots `contract-repair` permits."; a `loads:` entry for `contract-repair` (spec 08) |
| `workflows/pav-check.md` | After the NEEDS WORK bullet of the verdict writes and before the paragraph beginning `**If NEEDS WORK**` (today the bullet is `:106` and the paragraph `:108`): "Under `/spec-run` with an active repair policy (the spawn instruction says so), after the NEEDS WORK writes and before stopping, write the repair classification draft per `contract-repair → ## Classification`." No other change |
| `workflows/pae-repair.md` (new) | C-6 |
| `rules/orchestration.md` | `### Conditions that always stop the run` gains "- A repair outcome classified stop by `contract-repair → ## Stop classes`."; `## Shared-file discipline` gains "Repair classification drafts are written by the Validator under `<task>/repairs/drafts/`; repair records and `## Repair Episodes` lines are written only by the Orchestrator."; `### Implementer` gains "A repair attempt is a fresh Implementer running `/pae-repair` under `contract-repair → ## Repair attempt`." |
| `rules/tdd.md` | `## Interaction with existing mechanisms` gains "**Repair attempts.** A repair after NEEDS WORK keeps the frozen set and adds reproducing tests in new files before any fix; see `contract-repair → ## Repair attempt`." |
| `rules/workflow-globals.md` | After the paragraph beginning "`/spec-run` additionally defers the `/pe-finalize` batched proposal decision" (today `:84-85`): "`/spec-run --repair-policy bounded-local` defers the step 4.3 NEEDS WORK stop for the bounded repair loop of `contract-repair`; the stop applies when the loop ends without acceptance." |
| `rules/workflow-reference.md` | `## Protected Sections Contract` lists `## Repair Episodes`; `## Key State-File Markers` gains "`## Repair Episodes` — repair ledger lines, written only by `/spec-run`." |
| `docs/USAGE.md`, `workflows/PIPELINE.md`, `docs/SPEC-RUN-QUICKSTART.md` | The flag, the switch, the policy file, `/pae-repair`, the ignore entry, REQ-74's statement |

Constraints from frozen checks: keep every phrase quoted in Context fact 9 and those of
`scripts/validate-contracts.sh:900-912`, `:1047`, `:1261-1262`, `:1506-1517`; add no line matching
`call ./phase-composite-validation`; in `/pav-check` and `/pae-repair` add no line in which a write
verb precedes `plan.md`, `architecture.md`, `.ai/memory/state.md` or `.ai/project_state.md`.

### C-8 Escalation resolution

1. **Authorization.** The policy file has an `escalation` entry for the harness, else
   `escalation-unauthorized`.
2. **Model.** When `model` is non-null: write a temporary file outside the project containing
   `## Subtasks`, a blank line, the header `| ID | Status | Model (Claude) |` (or `Model (Codex)`),
   the separator `|---|---|---|` and one row `| <leaf_id> | done | <id> |`; run `model-catalog.py --catalog <catalog> --today
   <date> --resolve-plan <temp> --provider <provider> --row <leaf_id> --resolution <input>` with the
   same `selection` the leaf's step 2 resolution uses, `fallback: {"authorized": false, "model":
   null}` and `execution: null` (`rules/workflow-reference.md:166-176`). Status `resolved` → use it;
   any other status → `model-unresolved`. When `model` is null, the leaf's ordinary resolution is
   used.
3. **Effort.** When `effort` is non-null: spec 18 C-4 with `escalation: {"value": <effort>,
   "reference": <next_attempt_id>}`. The component *resolves* iff the decision's `outcome` is
   `requested` and its `reasons` lack `escalation-unverifiable`; it is *effective* iff it resolves
   and the decision's `source` is `escalation` (spec 18 raised the effort to the declared value).
   `not-requested`, or `escalation-unverifiable` (which every harness yields while its
   `## sub-agent-effort` capability is `unknown`) → `effort-not-applied`; resolver unusable (spec 18
   REQ-14) → `resolver-unusable`; `stop` → spec 18's stop. A resolved, non-effective effort (the
   requested effort was already provably at least the declared value) is not a failure. A spec 18
   `stop` stays spec 18's own stop (C-5 step 5), and an `escalation-unverifiable` or `not-requested`
   effort is never replaced by another model, effort or harness setting: the declared component is
   either applied as declared or the episode ends (REQ-06).
4. **Identity.** The model component is *effective* iff its resolved identity differs from the
   local resolution's resolved identity (`session-default` compares equal only to
   `session-default`). If no declared component is effective → `escalation-identical`. The local
   resolution is computed for every escalated attempt, with or without an earlier local attempt.
5. **Record.** Requested, resolved and actual (`null`) identities and the decision key go into the
   contract and the `reserved` line; actual stays unknown without a separate receipt.

No partial escalation: a declared component that is not applied ends the episode.

### C-9 Stops (`contract-repair → ## Stop classes`)

| Code | When | Message |
|---|---|---|
| `repair-policy-unknown` | REQ-10 | "Unknown repair policy <value>. Use --repair-policy bounded-local or omit it." |
| `repair-policy-invalid` | REQ-13 | "Repair policy file <path> is invalid: <errors>. Correct it, move it aside, or set ORCHESTRAIL_REPAIR_POLICY=off, and resume." |
| `repair-save-failed` | REQ-31 | "Repair record <path> could not be saved (<result>). Inspect <task>/repairs/ and resume." |
| `repair-ledger-invalid` | REQ-61 | "Repair ledger of <leaf> is invalid: <reasons>. Restore the section or records and resume." |
| `repair-dispatch-unknown` | REQ-34 | "Repair attempt <attempt_id> may have been dispatched. Confirm with a repair-cancel line if it was not, and resume." |
| `repair-reopen-required` | REQ-19 | "Leaf <leaf> already used episode <episode_id>. Record a repair-reopen decision to allow a new episode." |
| `repair-state` | C-5 general rule (REQ-75) | "Repair helper <subcommand> refused for <leaf>: <exit code> <reasons>. The episode stays open; correct the cause named and resume." |
| NEEDS WORK with repair | REQ-17, REQ-26, REQ-56 | Today's 4.3 stop, followed by the C-5 report lines and the terminal |

### C-10 Contracts exposed to and consumed from other specs

| Spec | Relationship |
|---|---|
| 04 (completed) | Consumed: `--resolve-plan` with its resolution input and statuses (C-8 step 2); no change |
| 05 (completed) | Exposed: `episode_id`, `attempt_id`, slot, terminal and the ledger as plain identifiers; a 05 producer maps them to its `attempt` dimension with its keyed mapping (`scripts/usage_telemetry_adapter.py:20-24`, `scripts/usage_telemetry_contract.py:2911`). No 05 record is written; unknown counts stay unknown |
| 09 | Exposed: ledger and records inside captured task directories; the flag's absence or the switch gives the no-repair arm (variant strategy details `repair_policy`, `escalation_limits`, `.ai/specs/09-golden-run-tests.md` DM-6). The two switches are expressible as spec 09 REQ-52 `switches` (its `Variant switches`): the candidate variant declares `prompt_args: ["--repair-policy", "bounded-local"]`, and a control that must disable repair even where the flag could be inherited declares `env: {"ORCHESTRAIL_REPAIR_POLICY": "off"}` (`ORCHESTRAIL_REPAIR_POLICY` matches spec 09's `ORCHESTRAIL_*` rule and is neither `ORCHESTRAIL_HOME` nor `ORCHESTRAIL_LOG_ROOT`); the control normally omits both. No overlay is needed, but the owner policy file (DM-5) is read from the runner's `HOME` or `XDG_CONFIG_HOME`, which spec 09 passes through to the executor: a comparison run must have no policy file there (then it starts `local` with no escalation, REQ-05), or its candidate arm may escalate; `ORCHESTRAIL_REPAIR_POLICY=off` disables the policy, and so escalation, only in an arm that sets it. Consumed: offline suite (REQ-69). Every quality and cost claim, and the chain arithmetic, belong to 09's calculator (spec 09 REQ-11 and DM-13) |
| 12 | Wired by spec 12a REQ-54 and spec 12 REQ-63 (with 12a DM-3 `repair_episode`, 12 DM-6 stage `repair` and C-6 row 7 of spec 12), which runs C-5 for a failed child while the policy is active, instead of its REQ-24 or REQ-51 stop. What this spec guarantees to it: spec 12's episode key is the `episode_id` (DM-2); an episode is keyed by leaf and, in its `opened` line, the contract digest, and survives serialization, worktree change and new workers, so when spec 12 REQ-14 supersedes an attempt with an open episode, copying that key into the next attempt's `repair_episode` is enough: `status` continues the same episode with its recorded slots, and every limit comes from the ledger alone, never from a spec 12 attempt count. The child keeps spec 12's own concurrency slot, its reservation and its claim on its files while the episode is open; spec 12's slot is unrelated to this spec's `local` and `escalated` slots (DM-8 `slots`). A repair runs only on the leaf's own unmerged branch in its recorded location; a child whose attempt is `merged`, `accepted` or `cleaned` is never repaired here (integration failures use spec 12a's REQ-35 and REQ-45 and the D8 fix siblings); a partially merged composite keeps its merged siblings untouched; an accepted repair (`accepted` outcome, `continue`) leaves spec 12 to set the attempt `validated` and to apply its merge rules, check-merge, abort and serialization unchanged. A spec 12 REQ-04 broad stop is stated by spec 12 itself (12 REQ-04, REQ-54 and C-6 row 8): a repair worker already dispatched is not interrupted and finishes, no further attempt, repair attempt or recheck starts, its result is recorded through this spec's `outcome` step as usual, and the open episode stays open; this spec reserves no new attempt after such a stop and adds nothing to it. At most one attempt per leaf is reserved at any moment. With N > 1 one `/pae-repair` invocation is one workflow invocation performed by one fresh agent that spec 12's root spawns; the agent returns its leaf-block writes as deltas, the root commits the repair checkpoints (REQ-40) and builds a spec 12 DM-6 handoff with stage `repair`, and the repair Validator recheck is a fresh validation phase (this spec's REQ-47; requested under spec 12 C-6 row 6); ledger lines and records are still written only by the Orchestrator, which is spec 12's root in that mode (A-34). A loop that ends without acceptance (REQ-56) returns to spec 12's REQ-24 or REQ-51 stop; without the active policy those stops apply as written (REQ-01) |
| 14 | Consumed: role packets; the repair Implementer gets a fresh `implementer` packet with `--predecessor` (`.ai/specs/14-task-context-and-reuse.md` C-8 row 19 and C-1 `--predecessor`); digests recorded in the contract |
| 15 | Consumed: `checkpoint_save` (C-5), canonical JSON, note-entry parsing, `attempt` lineage through `supersedes`; the spawn of a repair Implementer is a spec-15 attempt (REQ-35, C-5 step 8: role `implementer`, `supersedes` lineage through `attempt`), while this spec's `attempt_id` is not a spec-15 `attempt_id`; repair resume is governed by this spec's `status` alone, repair boundaries are not spec-15 checkpoint kinds, and `compose`, `render` and `receipt` are not used for repair; 15's `reconcile` classifies a repair Implementer's due `green` event as complete (`manual-route`, `none`) from the leaf's original `test:`/`feat:` commits and the `done` plan row even before the repair runs (`.ai/specs/15-orchestrator-overhead.md` DM-9, canonical completion predicates and row `manual-route`); therefore `reconcile`'s entries for repair attempts are ignored. The `blocked` to `done` plan-row rewrite (REQ-35, C-5 steps 8 and 12; A-18) is a manual write that spec 15's helper neither performs nor verifies (15 DM-5 has no such transition; 15 C-10 row 19). No new attempt-record field, so no amendment of 15 |
| 16 | Consumed, under the names of spec 16 C-6 row 19 (the subset read here): the leaf record `reviews/<leaf>/<seq>.json` with `schema_version`, `kind`, `level`, `step`, `scope_key`, `seq`, `record_digest`, `verdict`, `contract.contract_digest`, `subject.head`, `scope`, `minimum_scope`, `findings[]` (`id`, `severity`, `title`, `evidence`, `status`, `obligations`, `locations`, `check`, `same_as`), `obligations[]` (`id`, `kind`, `state`, `risks`), `outcomes[]` (`finding`, `outcome`) and `checks[]` (`check`, `receipt_id`); in the referenced DM-4 receipt the `output` object by mode (DM-8 `evidence_refs`); the DM-8 notes entries including `none — blocked`; the spec 16 REQ-56 `verification check ` blocker prefix; the DM-7a decision sections; the C-3 parsing rules. Spec 16's own `subject.clean` is not read (A-29). The recheck is an ordinary spec 16 leaf review by a fresh Validator whose prior is the record the attempt answered (REQ-47); spec 16 neither ends nor removes the NEEDS WORK stop that this loop defers. 16's decision sections keep `owner-accepted` decisions; this spec never gives outcomes |
| 17 | Consumed, as spec 17 C-7 row 19 states: DM-9 `tdd: red output` and `tdd: green output` lines copied verbatim as `Evidence` items (DM-8 `evidence_refs`; not spec 08 DM-7 evidence references, 08 Q-06); DM-3 kinds `launch-error`, `timeout`, `interrupted` and `signal` separate infrastructure blockers from failing tests (kind `exit`, REQ-45, C-6 step 2); an unknown outcome is an evidence gap; DM-5 records for locating a failure (hint); a command is never re-run by the helper. A spec 16 capture-mode receipt carries no stream digests, only its OUTPUT reference, `artifact_id` and `manifest_sha256` (DM-8) |
| 18 | Consumed: DM-6 `escalation`, C-3 steps 5–7 and their codes (`escalation-raised`, `escalation-unverifiable`), DM-5 keys; C-8 step 3 defines the handling of `escalation-unverifiable` and `not-requested` (`effort-not-applied`, no substitution) and leaves a spec 18 `stop` as spec 18's own stop. While every harness declares the sub-agent effort capability `unknown`, an effort escalation ends `escalation-unavailable` / `effort-not-applied` (A-27) |
| 20 | Exposed: per-leaf `## Repair Episodes` ledger lines (DM-3: `opened`, `reserved` with `slot (local\|escalated)`, `outcome`, `closed`; the section is created on the first line, DM-1, so its absence cannot tell an inactive policy from no repair) as read-only rework evidence for spec 20's per-leaf `repairs` counts (episodes, attempts per slot, closed). Read-only contract: spec 20 may read the section and the records, and never writes, reorders, validates (ledger validity stays `ledger-invalid`, REQ-61) or reinterprets a line, and never changes a slot or a limit |
| 13, 08 | Consumed: rename maps and kind prefixes; `loads:` and rule size |
| 07 | None |

### C-11 Acceptance suite

`python3 -I scripts/check-repair-episode.py` is a standard-library Python 3.11+ `unittest` program.
It builds fixtures under a temporary directory with isolated `HOME`, `XDG_CONFIG_HOME` and
`GIT_CONFIG_NOSYSTEM=1`, runs the helper as a subprocess, reads this repository's rules, workflows
and docs read-only for text cases, never touches the real home or this repository's `.git`, starts
no model and exits 0 only when every case passes.

**Fixture R1.** `git init R`; commit C0 holds `src/a.py` (`def f():\n    return 1\n`), `src/b.py`,
`.gitignore` with `/.ai/tasks/*/*/repairs/` and `/.ai/tasks/*/*/verification/`,
`.ai/context/runbook.md` (`## Commands`, `test: python3 -m unittest`, `lint: (none)`); commit C1
`test: f returns two` adds `tests/test_a.py`; commit C2 `feat: f returns two` changes `src/a.py`.
`.ai/tasks/todo/task-01-demo/state.md` has `## Solution Design` with `### Decision`,
`### Invariants` (`- f is pure`) and `### Off-limits`, a `## Task Analysis → ### Assumptions`
section, and `## Subtask Progress` with:

```text
T-01 | alpha | atomic-tests: green | atomic-execution: complete | atomic-validation: failed
  last_action: pav-check NEEDS WORK
  target_files: src/a.py, tests/test_a.py
  blocker: none
  notes: tdd: red digest — AC-1 → test_f; verification: review T-01 check #1 full-leaf sha256:<digest of record 1>
  branch: feat/alpha
  base_commit: <C0>
  commits: <C1> test: f returns two, <C2> feat: f returns two
T-02 | beta | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: src/b.py
  blocker: none
  notes:
```

`plan.md` has `## Subtasks` with T-01 `done` and T-02 `not-started` (`Depends On` T-01);
`T-01-alpha/description.md` has `## Scope` with `Target files: src/a.py, tests/test_a.py` and two
criteria. `verification/reviews/T-01/1.json` is a synthetic spec-16 record (valid self-digest,
`subject.head` = C2, verdict `NEEDS WORK`, obligations `AC-1` `failed` and `AC-2` `verified` with
empty `risks`, finding `T-01/F1` `important`, `obligations: ["AC-1"]`, `check: "test"`, status
`open`, `locations` `[{"path": "src/a.py", "line": 2}, {"path": "tests/test_a.py", "line":
null}]`). A *valid draft* classifies `T-01/F1` as `local-defect` with `failing-check`. Variants
named in an AC derive from R1. Model inputs are synthetic spec-04 reports; effort inputs are
synthetic spec-18 decisions.

### C-12 Files created or changed

New: `scripts/repair-episode.py`, `scripts/check-repair-episode.py`, `rules/contract-repair.md`,
`workflows/pae-repair.md`, `.ai/adr/<NNNN>-*.md`. Changed: the files of C-7, `.gitignore`,
`scripts/setup-new-project.sh` (rule list, `GITIGNORE_ENTRIES`), `scripts/sync.sh` (rule list) or
13's replacement, `scripts/README.md`, `.ai/principles/domain.md` (REQ-73),
`.ai/memory/architecture.md` (scripts table, inventory counts, workflow list),
`.ai/context/runbook.md` (suite command, switch), `.ai/adr/index.md`.

## Non-Functional Requirements

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-01 | Determinism | Byte-identical stdout for identical files, repository state and arguments (C-1 inputs only) | AC-24 |
| NFR-02 | Read-only, no model, no network | The helper writes no file, imports no network module, starts no process other than `git` | AC-24 (fixture tree identity; static import scan) |
| NFR-03 | Portability | Python 3.11+ standard library; `git`, `bash`, `ln`, `cmp` and `sha256sum` or `shasum` for the save procedure | AC-25 |
| NFR-04 | Bounded input | 1,048,576 bytes per file read (matching spec 15 REQ-43); larger → exit 2 `input-too-large` | AC-25 |
| NFR-05 | Privacy | stderr and ledger lines carry no finding text or file contents; records stay in the ignored task directory | AC-24, AC-30 |
| NFR-06 | Rule size | `rules/contract-repair.md` within spec 08's limit when in force (C-4 split rule) | AC-35 |
| NFR-07 | Performance | N/A — no owner target exists and none is invented; measured effects belong to spec 09 (REQ-74) | — |

## Edge Cases & Failure Modes

| Case | Expected behaviour | Requirement |
|---|---|---|
| Flag absent, switch `off`, or helper missing | Today's stop; no ledger, no classification instruction | REQ-01, REQ-11, REQ-12 |
| Unknown flag value | Guard stop before writes | REQ-10 |
| Invalid policy file | Stop before writes | REQ-13 |
| Policy file absent | Local slot only; after a failed local attempt `exhausted`/`local` | REQ-05, REQ-52 |
| `start: escalated` without an entry for the harness | `escalation-unavailable`/`escalation-unauthorized`; stop | REQ-06, C-8 |
| Spec-16 helper unavailable (DM-8 `none` entry) | `review-unavailable`; today's stop | REQ-17 |
| Record edited after the DM-8 entry | `review-invalid`; stop | REQ-17 |
| Validator wrote no draft or a wrong draft | `ineligible`/`draft-invalid`; stop | REQ-21, REQ-26 |
| Draft classifies a critical finding as `local-defect` | Override `hard-stop`; ineligible | REQ-22 |
| Finding touches another leaf's file | Override `contract-divergence`; ineligible | REQ-22 |
| Unmet obligation without an open finding | `unlinked-obligation`; ineligible | REQ-23 |
| Pending owner-decision finding | `owner-decision-pending`; ineligible | REQ-24 |
| `new-test` reproduction in a characterization or `n-a` leaf | `reproduction-invalid`; ineligible | REQ-25 |
| Ordinary leaf without a recorded `test:` commit | `frozen-set-unknown`; ineligible | DM-7 |
| Arbiter answer without citation | Class B recorded; `ineligible`/`intent-unresolved` | REQ-28 |
| Owner commits on the branch between NEEDS WORK and reservation | `tree-changed`; stop | DM-8 `start` |
| Interruption after record save, before its line | Orphan ignored; next number skips it | REQ-62 |
| Interruption after `reserved`, before `dispatched` | `dispatch-unknown` stop; owner `repair-cancel` line permits cancellation | REQ-34 |
| Harness refuses the spawn | `cancelled`/`spawn-refused`; one new reservation; a second refusal → `stopped`/`dispatch-refused` | REQ-33 |
| Re-running `reserve` after a `reserved` line exists | Exit 1 `attempt-pending`; stop with the episode open | REQ-04 |
| Two Orchestrators on one task at once | Not supported, as in spec 15 (`.ai/specs/15-orchestrator-overhead.md` Out of Scope); no lock is added | — |
| Repair worker edits a frozen test | `frozen-tests-changed`; `violation`; stop | REQ-42 |
| Repair worker edits a path outside allowed paths or creates a non-test file | `scope-exceeded`; stop | REQ-41 |
| A new test passes before the fix | Blocker `red-not-established`; stop | REQ-44 |
| Reproduction no longer fails | Blocker `not-reproduced`; stop | REQ-44 |
| Test command times out or cannot launch | Blocker `infrastructure`; no code change | REQ-45 |
| Repair needs a new implementation file | Blocker `repair-scope`; stop | C-6 step 3 |
| Worker lost with no change | `worker-lost`, verdict `unchanged-tree`; escalation if authorized | REQ-50, REQ-52 |
| Worker lost after the `test:` commit | Recheck, then outcome | REQ-47, REQ-48 |
| Worker lost with uncommitted changes | `stopped`/`worker-lost-dirty`; changes preserved | REQ-54 |
| Provider limit | `stopped`/`provider-stopped`; no account or model switch | REQ-57 |
| Recheck check cannot complete (spec 16 blocker) | `recheck-blocked`; stop | REQ-54 |
| Recheck without a record | `recheck-unrecorded`; stop | REQ-54 |
| Repeat of the same defect after the local attempt | `repeats` recorded; escalation only if authorized and still eligible | DM-16, REQ-52 |
| New critical finding after the local attempt | New classification ineligible (`hard-stop`) | REQ-22, REQ-52 |
| Description amended during the attempt | `contract-changed`; stop | REQ-43 |
| Escalation effort with capability `unknown` | `effort-not-applied`; `escalation-unavailable`; stop | C-8 |
| Escalation model not eligible | `model-unresolved`; stop | C-8 |
| Escalation identical to local | `escalation-identical`; stop | C-8 |
| Policy disabled mid-episode, then re-enabled | Episode untouched while off; continues with its slots | REQ-60 |
| Owner fixes the leaf and the review passes | `resolved-outside` | REQ-59 |
| Closed failed episode, new NEEDS WORK, same contract | `reopen-required` unless a reopen line exists | REQ-19 |
| Contract amended, new NEEDS WORK | New episode allowed; `prior` lists earlier episodes | REQ-19, DM-3 |
| Deleted `repairs/` with an open episode | `ledger-invalid`; stop | REQ-61 |
| Malformed or hand-edited ledger line | `ledger-invalid`; stop | REQ-61 |
| `reserve` refused with an escalation reason | `escalation-unavailable`; stop | C-5 reserve-refusal table |
| `coverage` repair whose new tests pass | `test:` commit, `nothing-to-stage` at GREEN, recheck | C-5 step 11 |
| Interruption after the recheck closed the leaf, before `outcome` | `status` reports `outcome`, not `resolved-outside` | REQ-59 |
| Stub file committed with the tests and implemented later | Frozen; a finding located only there is ineligible (`frozen-location`) | DM-14, DM-7 |
| RED test file also touched by the implementation commit | Stays frozen | DM-14 |
| Commit summary containing commas | Parsed by DM-18 | DM-18 |
| Provider limit at spawn | `cancelled`/`provider-limit`; `stopped`/`provider-stopped` | REQ-57 |
| Duplicate save of an identical record | `duplicate`; proceeds once | DM-1 |
| Dependent leaf | Not started until `accepted` or `resolved-outside` (step 4 order unchanged) | REQ-08 |
| Composite integration NEEDS WORK | Unchanged D8 process | REQ-15 |
| `--dry-run` | Reports state only | REQ-14 |

## Acceptance Criteria

Helper cases run on fixture R1 (C-11); text cases read the delivered files.

- **AC-01** (REQ-01, REQ-02, REQ-11, REQ-12) — Given `workflows/spec-run.md`, then 4.3 still contains
  `:297-299` verbatim, its added sentence conditions the repair loop on an active policy, and C-5
  step 1's Validator instruction is given only with an active policy; given R1 and
  `ORCHESTRAIL_REPAIR_POLICY=off` (and separately `=yes`), every subcommand except `version` and
  `check-policy` exits 4 `disabled` and writes nothing; with it empty or `on`, `status` does not
  exit 4.
- **AC-02** (REQ-03, REQ-07, REQ-40, REQ-41) — Given R1 after `open`, a valid draft, `classify`
  (which reports `eligible: true` although one location is the frozen `tests/test_a.py`) and
  `reserve --slot local`, then the contract has every DM-8 field, `allowed_paths` is `["src/a.py"]`,
  `frozen_tests` is `[tests/test_a.py with its digest]`, `report_forms` is `["GREEN"]`; given a new
  untracked `tests/test_b.py`, `check --stage red` gives `stage_paths: ["tests/test_b.py"]`; given an
  edit to `src/b.py`, `check --stage green` reports `scope-exceeded`; given a clean tree,
  `nothing-to-stage`.
- **AC-03** (REQ-04, REQ-08, REQ-62) — Given an episode with a non-cancelled local attempt, then a
  second `reserve --slot local` exits 1 `slot-exhausted`; after an escalated attempt, `reserve
  --slot local` exits 1 `slot-order`; given a contract file for `A3` without a line, the next
  `next_attempt_id` is `A4`; given the ledger copied to a fresh clone without `repairs/` and every
  episode closed, `status` still counts the slots from the lines.
- **AC-04** (REQ-05, REQ-06) — Given a policy with `start: escalated` and an entry for `claude`,
  then `status` reports `reserve-escalated` first; given no policy file, `reserve-local`; and the
  helper's records contain no key named `probability`, `cost`, `saving` or `duration`.
- **AC-05** (REQ-09, REQ-56) — Given `contract-repair → ## Repair loop`, then it holds both C-5
  step 14 report line forms and the C-5 `End:` verbatim line, each exactly once.
- **AC-06** (REQ-10, REQ-13, REQ-14) — Given `workflows/spec-run.md`, then its Guard names
  `repair-policy-unknown` and Step 0 cites the repair loop step 0; the rule names `check-policy` and
  `repair-policy-invalid` and holds the C-5 `Dry run:` verbatim line; given a policy file with
  an unknown key, `check-policy` exits 1.
- **AC-07** (REQ-15) — Given the rule, then it holds the C-5 `Scope:` verbatim line exactly once,
  and `workflows/phase-composite-validation.md` is byte-identical to its parent revision.
- **AC-08** (REQ-16, REQ-17) — Given R1, `open` exits 0 with an `OPENED` line naming `#1` and the
  record digest; given the DM-8 entry replaced by `verification: review T-01 check none —
  unavailable`, `open` exits 1 `review-unavailable`; given one byte of the record changed, exit 1
  `review-invalid`.
- **AC-09** (REQ-18, REQ-19) — Given an open episode, `open` exits 1 `episode-open`; given a closed
  `exhausted` episode with the same contract digest, `open` exits 1 `reopen-required`, and after a
  DM-4 `repair-reopen: T-01.E1 — owner fixed the test data (source: user)` line it exits 0 with
  `prior T-01.E1`; given a record with a different contract digest, it exits 0 without a decision.
- **AC-10** (REQ-20, REQ-21) — Given a valid draft, `classify` prints `eligible: true`, a
  `CLASSIFIED` line with `eligible yes`; given no draft, a draft naming `#2`, or a draft omitting
  `T-01/F1`, `eligible: false` with reason `draft-invalid` and exit 0.
- **AC-11** (REQ-22) — Given the finding with severity `critical`, or obligation `INV-1`, or an
  obligation with risk `security`, the effective class is `hard-stop`; with risk `uncertain`, or a
  location `src/b.py`, it is `contract-divergence`; each with `eligible: false`, `class-ineligible`
  and the override code listed.
- **AC-12** (REQ-23, REQ-24, REQ-25) — Given `AC-2` changed to `unverified`, reason
  `unlinked-obligation`; given a second finding with status `owner-decision`,
  `owner-decision-pending`; given `atomic-tests: n-a` and `new-test`, or a `tdd: characterize — `
  note and `new-test`, or `frozen-test` naming `tests/test_z.py::test_x` (a path outside the frozen
  set), `reproduction-invalid`.
- **AC-13** (REQ-26, REQ-28) — Given an ineligible classification, `classify` prints `close_line`
  `- T-01.E1 | closed | ineligible | <first reason>`; given the rule, it holds the C-5 `Class B:`
  verbatim line; and `close --terminal ineligible --detail intent-unresolved` exits 0.
- **AC-14** (REQ-27) — Given a `missing-context` finding, `reserve` without `--context-answers`
  exits 1 `context-answer-missing`; with an answer whose `source` is empty, the same; with a cited
  answer, the contract's `context_answer` equals it.
- **AC-15** (REQ-07, REQ-29, REQ-30, REQ-35, REQ-36) — Given the rule's repair loop, then the
  numbered steps titled Resolve, Packet, Reserve, Plan row and spec-15 record, Spawn, RED and GREEN
  appear in that order; Packet names `--predecessor`; Spawn names `description path`, `WORK_DIR`,
  `branch`, `contract path` and `packet path`; the reserve-refusal table names
  `escalation-unauthorized`, `escalation-identical`, `model-unresolved`, `effort-not-applied`,
  `tree-changed`, `context-answer-missing`, `policy-invalid`, `slot-exhausted`, `slot-order`,
  `attempt-pending`, `leaf-state`, `ledger-invalid` and `commits-invalid`; the resume table names
  `none`, `open`, `classify`, `reserve-local`, `reserve-escalated`, `cancel`,
  `dispatched-pending`, `recheck`, `outcome`, `close` and `stop`; given R1 with a dirty `src/a.py`, `reserve` exits 1 `tree-changed`; given a second `reserve`
  after a `RESERVED` line without follow-up, exit 1 `attempt-pending`.
- **AC-16** (REQ-31) — Given the save function of spec 15 run on a contract whose final file exists
  with other bytes, the result is `conflict`; and the rule holds the C-5 `Saving:` verbatim line.
- **AC-17** (REQ-32, REQ-33, REQ-34) — Given a `RESERVED` line without a follow-up, `status`
  reports `stop`/`dispatch-unknown`; with a DM-4 `repair-cancel: T-01.E1.A1 — not dispatched
  (source: user)` line, `status` reports `cancel` and `cancel --reason owner-confirmed-undispatched`
  exits 0 with a `CANCELLED` line; without that line the same `cancel` exits 1 `cancel-unauthorized`;
  given two `spawn-refused` cancellations in the local slot, `status` reports `close` and `close`
  prints `- T-01.E1 | closed | stopped | dispatch-refused`; and the rule's step 9 appends the
  `dispatched` line immediately after a spawn that was not refused and, for an effort refusal,
  states the DM-5 rejection line and `session.parameter: "absent"`.
- **AC-18** (REQ-07, REQ-37, REQ-38, REQ-39, REQ-44, REQ-45) — Given `workflows/pae-repair.md`, then
  its Guard names `contract-mismatch` and the three REQ-37 conditions, its `Reproduce` heading
  precedes its `Fix` heading, it holds the four C-6 verbatim lines, and every code of the
  `Repair blockers:` line appears in it.
- **AC-19** (REQ-42) — Given a reserved attempt and a changed byte in `tests/test_a.py`, `check
  --stage green` reports `frozen-tests-changed`; given an attempt whose `test:` commit added
  `tests/test_b.py` and a later edit to it, `outcome` reports `frozen-tests-changed` with terminal
  `violation`.
- **AC-20** (REQ-43) — Given an edited description after reservation, `check` reports
  `contract-changed`; given a recheck record with another `contract_digest`, `outcome` reports
  outcome `contract-changed`.
- **AC-21** (REQ-46) — Given `workflows/pae-repair.md`, then it contains the literal prefixes
  `tdd: repair red — ` and `tdd: repair green — ` and the C-6 `Status fields:` verbatim line.
- **AC-22** (REQ-47, REQ-48, REQ-50) — Given a dispatched attempt with a `fix:` commit and no newer
  record, `outcome` exits 1 `review-required`; given no commit, a clean tree and `--worker lost`,
  it reports `worker-lost` with `verdict_source: unchanged-tree`.
- **AC-23** (REQ-49) — Given a commit after the start head that is not in `commits:`, `outcome`
  reports `foreign-change`; given a `feat:` commit of the attempt, the same.
- **AC-24** (REQ-51, NFR-01, NFR-02, NFR-05) — Given a recheck record resolving `T-01/F1` and adding
  `T-01/F2` (`important`, no `same_as`), progress is `regression`; with `T-01/F2` `same_as: T-01/F1`
  and `remains` for F1, `no-progress` with `repeats: ["T-01/F2"]`; with F1 resolved and nothing new
  but verdict NEEDS WORK, `progress`; running every subcommand twice gives byte-identical stdout,
  the fixture tree's bytes, modes and mtimes and `.git` are unchanged, no module of `socket`,
  `http`, `urllib`, `ssl` is imported, and stderr lines contain no finding title.
- **AC-25** (REQ-52, NFR-03, NFR-04) — Given a `rejected` local attempt and a policy authorizing
  escalation, `next_action` is `classify`; with `no-change`, `reserve-escalated`; without a policy
  file, `close_line` ends `exhausted | local`; given a 1,048,577-byte draft, exit 2
  `input-too-large`; given Python 3.10 (version guard imported by path), exit 3.
- **AC-26** (REQ-53, REQ-54, REQ-57) — Given a `rejected` escalated attempt, `exhausted | escalated`
  with `next_action: stop`; given `--worker blocked --blocker repair-scope`,
  `stopped | worker-blocked-repair-scope`; given `--worker provider-stopped`,
  `stopped | provider-stopped`; given a lost worker and a dirty tree, `stopped | worker-lost-dirty`;
  given an attempt commit, the leaf note `verification: review T-01 check none — blocked` after the
  answered entry and `blocker: verification check test could not complete — x`, outcome
  `recheck-blocked`; given a `none — helper-error` entry instead, `recheck-unrecorded`; given a
  `provider-limit` cancellation, `close` prints `- T-01.E1 | closed | stopped | provider-stopped`;
  and the rule holds the C-5 `Provider:` verbatim line.
- **AC-27** (REQ-55) — Given a recheck record with verdict `DONE`, `outcome` reports `accepted`,
  progress `resolved` and `close_line` `- T-01.E1 | closed | accepted | recheck-done`.
- **AC-28** (REQ-58, REQ-59, REQ-60) — Given an open episode whose attempts all have `OUTCOME`
  lines and the leaf block changed to `atomic-validation: complete`, `status` reports
  `close`/`resolved-outside`; given instead a dispatched attempt with a `fix:` commit, no `OUTCOME`
  and a newer DONE record, `status` reports `outcome`; given a dispatched attempt without commits,
  `dispatched-pending`; with
  `ORCHESTRAIL_REPAIR_POLICY=off`, `status` exits 4 and the state file is unchanged, and after
  unsetting it `status` reports the same slots as before; the rule's step 0 names Step 0 item 3, and
  the resume table maps `dispatched-pending` in a later session to `outcome --worker lost`.
- **AC-29** (REQ-61) — Given a ledger line with an extra field, two `## Repair Episodes` headings, a
  `DISPATCHED` line before its `RESERVED`, or a contract file whose SHA-256 differs from its line,
  every subcommand except `version` and `check-policy` exits 1 `ledger-invalid`.
- **AC-30** (REQ-63, REQ-67, NFR-05) — Given `rules/contract-repair.md`, then the front matter, the five
  sections and the C-4 anchored lines exist exactly once; given `.gitignore`, it contains
  `/.ai/tasks/*/*/repairs/`; `scripts/setup-new-project.sh` and `docs/USAGE.md` contain
  `.ai/tasks/*/*/repairs/`.
- **AC-31** (REQ-64, REQ-65, REQ-66) — Given the delivered files, each C-7 sentence is present
  verbatim, `## Repair Episodes` appears in the Protected Sections Contract, `pae-repair` appears in
  `docs/USAGE.md` and the pipeline reference, every phrase listed in C-7's constraints is
  unchanged, and the front matter of the workflow file holds `reads`, `writes` and `called_by` with
  `called_by` naming `spec-run`, and its `Called by:` line begins with the backticked `/spec-run`
  (C-6, metadata for the generated reference docs).
- **AC-32** (REQ-68, REQ-69, REQ-71) — Given the delivered tree, `bash scripts/validate-contracts.sh`
  and `python3 -I tests/golden-runs.py` finish with zero failures, no file under `tests/` and no
  check expression differs from the parent revision, and both rule deployment lists name
  `contract-repair.md`.
- **AC-33** (REQ-70) — Given `scripts/validate-contracts.sh` and `scripts/sync.sh`, neither contains
  `check-repair-episode`, and `python3 -I scripts/check-repair-episode.py` exits 0 on the delivered
  tree.
- **AC-34** (REQ-72, REQ-73, REQ-74) — Given `.ai/adr/index.md`, a new Accepted entry names the repair
  policy; the ADR names the stop change, ledger, slots, classification, escalation and opt-in;
  `.ai/principles/domain.md` defines the five REQ-73 terms, including `Repair escalation`; `docs/USAGE.md` and the ADR state that
  no effect has been measured and that comparison belongs to spec 09.
- **AC-35** (REQ-63, NFR-06) — Given the rule and `version`, each anchored registry equals the
  corresponding `version` registry; given a temporary copy with one value changed, the suite fails
  naming that line; where spec 08's meter exists, it reports no `rule-size-exceeded` for the rule
  or its split files.
- **AC-36** (REQ-06, C-8) — Given a policy whose `claude` entry has only `effort: high` and a
  synthetic spec-18 decision with `outcome: not-requested` and reasons containing
  `capability-unknown` and `escalation-unverifiable`, `reserve --slot escalated` exits 1
  `effort-not-applied`, and `close --terminal escalation-unavailable --detail effort-not-applied`
  then exits 0; given a policy declaring a model and a spec-04 report with status `fallback` for
  it, exit 1 `model-unresolved`; given a declared model whose resolved identity equals the
  `--local-model` identity and no effort, exit 1 `escalation-identical`.
- **AC-37** (REQ-08) — Given the rule, then it holds the C-5 `Dependents:` verbatim line, and
  `workflows/spec-run.md` still contains "Never start N+1 before N is `reviewed`".
- **AC-38** (REQ-42, REQ-49) — Given R1 with the `commits:` value
  `<C1> test: f returns two, three and four, <C2> feat: f returns two` (a summary with commas) and
  abbreviated 12-character shas, the frozen set is `[tests/test_a.py]`; given a piece `zz test: x`
  as the first piece, `reserve` exits 1 `commits-invalid`.
- **AC-39** (REQ-41, REQ-42, REQ-25) — Given an R1 variant whose C2 also edits `tests/test_a.py`,
  the frozen set contains `tests/test_a.py` and `allowed_paths` does not; given a variant whose C1
  also adds the stub `src/c.py` that C2 implements and a finding located only in `src/c.py`, the
  frozen set contains `src/c.py` and `classify` reports `eligible: false` with `frozen-location`.
- **AC-40** (REQ-04, REQ-33, REQ-57, C-8) — Given a `spawn-refused` cancellation of the escalated
  attempt `A2`, `reserve --slot escalated` exits 0 with `A3`; given a policy whose `claude` entry
  has only `effort: high` and a decision with `outcome: requested`, `source: recommendation` (no
  raise) and a model equal to the local resolution, `reserve --slot escalated` exits 1
  `escalation-identical`; given the same with `source: escalation`, exit 0.

- **AC-41** (REQ-75, REQ-48) — Given the rule, then C-9 has the `repair-state` row and the rule holds
  the C-5 `Unlisted:` verbatim line and states the second-`review-required` stop in step 12; given a
  `--review` record with one changed byte, `outcome` exits 1 `review-invalid`.
- **AC-42** (REQ-25, REQ-20) — Given R1 with `T-01/F1` reclassified `test-missing` with a `coverage`
  reproduction and located only at `tests/test_a.py`, `classify` reports `eligible: true`; given a
  `local-defect` finding with an empty `locations` list, `eligible: true`; given a `local-defect`
  finding located only at `tests/test_a.py`, `eligible: false` with `frozen-location`.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-01 |
| REQ-03 | AC-02 |
| REQ-04 | AC-03, AC-15, AC-40 |
| REQ-05 | AC-04 |
| REQ-06 | AC-04, AC-36, AC-40 |
| REQ-07 | AC-02, AC-15, AC-18 |
| REQ-08 | AC-03, AC-37 |
| REQ-09 | AC-05 |
| REQ-10 | AC-06 |
| REQ-11 | AC-01 |
| REQ-12 | AC-01 |
| REQ-13 | AC-06 |
| REQ-14 | AC-06 |
| REQ-15 | AC-07 |
| REQ-16 | AC-08 |
| REQ-17 | AC-08 |
| REQ-18 | AC-09 |
| REQ-19 | AC-09 |
| REQ-20 | AC-10, AC-42 |
| REQ-21 | AC-10 |
| REQ-22 | AC-11 |
| REQ-23 | AC-12 |
| REQ-24 | AC-12 |
| REQ-25 | AC-12, AC-39, AC-42 |
| REQ-26 | AC-13 |
| REQ-27 | AC-14 |
| REQ-28 | AC-13 |
| REQ-29 | AC-15 |
| REQ-30 | AC-15 |
| REQ-31 | AC-16 |
| REQ-32 | AC-17 |
| REQ-33 | AC-17, AC-40 |
| REQ-34 | AC-17 |
| REQ-35 | AC-15 |
| REQ-36 | AC-15 |
| REQ-37 | AC-18 |
| REQ-38 | AC-18 |
| REQ-39 | AC-18 |
| REQ-40 | AC-02 |
| REQ-41 | AC-02, AC-39 |
| REQ-42 | AC-19, AC-38, AC-39 |
| REQ-43 | AC-20 |
| REQ-44 | AC-18 |
| REQ-45 | AC-18 |
| REQ-46 | AC-21 |
| REQ-47 | AC-22 |
| REQ-48 | AC-22, AC-41 |
| REQ-49 | AC-23, AC-38 |
| REQ-50 | AC-22 |
| REQ-51 | AC-24 |
| REQ-52 | AC-25 |
| REQ-53 | AC-26 |
| REQ-54 | AC-26 |
| REQ-55 | AC-27 |
| REQ-56 | AC-05 |
| REQ-57 | AC-26, AC-40 |
| REQ-58 | AC-28 |
| REQ-59 | AC-28 |
| REQ-60 | AC-28 |
| REQ-61 | AC-29 |
| REQ-62 | AC-03 |
| REQ-63 | AC-30, AC-35 |
| REQ-64 | AC-31 |
| REQ-65 | AC-31 |
| REQ-66 | AC-31 |
| REQ-67 | AC-30 |
| REQ-68 | AC-32 |
| REQ-69 | AC-32 |
| REQ-70 | AC-33 |
| REQ-71 | AC-32 |
| REQ-72 | AC-34 |
| REQ-73 | AC-34 |
| REQ-74 | AC-34 |
| REQ-75 | AC-41 |

Every AC names at least one REQ above. Shared gates: G1 — REQ-09, C-5 step 14, C-10 row 05
(identities, requested/resolved/actual, unknown stays unknown); G2 — C-10 row 09 (no-repair arm,
comparisons owned by 09); G3 — REQ-07, REQ-22, REQ-38–REQ-47 (test-first, frozen RED intact,
independent recheck, owner stops kept); G4 — REQ-01, REQ-12, REQ-17, REQ-60, C-8 (conservative
paths, no hidden substitution); G5 — Actors, NFR-02, REQ-08 (single writer, read-only helper,
optional); G6 — C-11, REQ-68–REQ-70 (failing fixtures first, no paid run); G7 — REQ-11, REQ-60,
DM-1 (disable, resume, preserved evidence); G8 — REQ-05, REQ-74 (no invented economics, no cap).

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| The Validator classifies a non-local defect as `local-defect` | Wasted attempt or wrong repair | Medium | Overrides from severity, obligations, risks and cross-leaf paths; scope and frozen checks; independent recheck; one attempt per slot |
| The new-file-only rule for tests forces an existing test file to stay incomplete | More `repair-scope` stops | Medium | Conservative by design (A-12); spec 09 can justify relaxing it |
| Effort escalation is never applicable while both harnesses declare `unknown` | Effort-only policies always stop | High | Documented (C-8); owner declares a model escalation or none |
| A forged decision line in `### Assumptions` | Episode reopened without the owner | Low | Text rule (P10 limitation); lines are reviewed with the state file; reopen keeps earlier episodes visible |
| Orphan records accumulate | Clutter in an ignored directory | Low | Never reused (REQ-62); deletion after closure is safe |
| Spec 12a REQ-54 or spec 12 REQ-63 and this spec drift apart | A parallel child repairs under another episode key or limit | Medium | C-10 row 12 and A-34 fix the shared names; limits come from the ledger only |
| Workflow edits break a frozen phrase | Validator red | Low | C-7 constraints; AC-31, AC-32 |

## Assumptions

- A-01 | File names | Resolved: today's names in text; spec 13's maps at implementation, with `/pae-repair` becoming `atomic-execution-repair` (phase `atomic-execution`, step `4`) | Source: `.ai/specs/README.md` (dependency table); `.ai/specs/13-model-only-harnesses-and-rule-naming.md` Notes → Files and sections created after this spec, DM-3, DM-11 | Reversible: yes
- A-02 | Opt-in form | Resolved: per-invocation `/spec-run` flag `--repair-policy bounded-local`; the owner's flag is the per-run authorization, the ADR records the stop change | Source: original REQ-01 and §1; README workstream 8 (`.ai/specs/README.md`, roadmap workstream 8); G3 owner-stop rule | Reversible: yes
- A-03 | Disable switch | Resolved: `ORCHESTRAIL_REPAIR_POLICY=off`; any value other than unset, empty or `on` disables | Source: spec 14 REQ-32 rule, shared by specs 15, 16, 17, 18 | Reversible: yes
- A-04 | Where the tooling lives | Resolved: helper and suite under `scripts/`, outside the validator inventory and `tests/` | Source: ADR-0019 Decision 3 (`.ai/adr/0019-…:68-80`) | Reversible: yes
- A-05 | Who classifies | Resolved: the Validator (independent, already holds the findings) writes a draft; the helper applies deterministic, more restrictive overrides | Source: original §3 roles; G3; spec 16 C-6 leaves classification to 19 | Reversible: yes
- A-06 | Critical findings | Resolved: any `critical` finding makes the episode ineligible | Source: original §7 step 10 and REQ-02; `workflows/pav-check.md:63-68`, `:86-87` (weakened tests and missing GREEN are critical) | Reversible: yes
- A-07 | Repair requires a spec-16 record | Resolved: no record → today's stop | Source: spec 16 C-6 (finding ids, outcomes); G4 conservative path | Reversible: yes
- A-08 | Ledger location | Resolved: protected append-only lines in task `state.md` as the authority on limits, write-once JSON under the ignored `<task>/repairs/` for detail | Source: original §6 (protected from compression); spec 18 DM-5 precedent; spec 15 REQ-37 ignore precedent | Reversible: yes
- A-09 | Economic choice | Resolved: the owner's `start` value; no probability or cost in this spec; arithmetic belongs to spec 09's calculator | Source: original REQ-05 and §10; `.ai/specs/09-golden-run-tests.md` `## Source` (original text, break-even example), REQ-11, DM-13 | Reversible: yes
- A-10 | Escalation authorization | Resolved: only an owner policy file naming a model and/or effort per harness; without it no escalation | Source: original REQ-06 ("no permitted candidate means an explicit stop") | Reversible: yes
- A-11 | Partial escalation | Resolved: every declared component must be applied, else `escalation-unavailable` | Source: G4 no hidden substitution; spec 18 C-6 row 19 leaves the handling to 19 | Reversible: yes
- A-12 | New files in a repair | Resolved: only new test files, only at stage `red`; no edits to existing test files outside allowed paths | Source: `rules/tdd.md:169-189` (frozen set; added tests allowed); best practice, smallest reversible choice for deterministic frozen-file checks | Reversible: yes
- A-13 | Characterization and `n-a` leaves | Resolved: no new tests in either; repairs there rely on frozen pins or failing checks (or inspection for `n-a`) | Source: `rules/tdd.md:119-131` (a fix in a refactor must be split), original §9 | Reversible: yes
- A-14 | Lost repair worker | Resolved: never recreated within the attempt; its commits get a recheck, an unchanged tree keeps the prior verdict | Source: original §7 "a failure/timeout does not return the slot"; spec 15 C-7 | Reversible: yes
- A-15 | Blocked attempts | Resolved: end the episode `stopped` without a further review | Source: `rules/orchestration.md:187` (a blocker stops the run) | Reversible: yes
- A-16 | Missing context | Resolved: the Orchestrator asks the Arbiter; a cited answer enters the contract; an uncited answer is class B and stops | Source: `rules/orchestration.md:47-50`, `:140-153`, `:173-178` | Reversible: yes
- A-17 | Model escalation mechanics | Resolved: a temporary one-row plan resolved through the existing `--resolve-plan` CLI, no fallback | Source: `scripts/model_plan.py:167-180`, `scripts/model-catalog.py:330-345`; `rules/workflow-reference.md:166-176` | Reversible: yes
- A-18 | Plan row during repair | Resolved: the Orchestrator writes `done` over `blocked` at reservation and before the recheck | Source: spec 15 DM-5 validator transitions and DM-9 predicates (`.ai/specs/15-orchestrator-overhead.md` DM-5 and DM-9) | Reversible: yes
- A-19 | Spawn refusal | Resolved: one cancellation per slot, then stop | Source: spec 18 REQ-10 (one new spawn after a refusal); P5 | Reversible: yes
- A-20 | Reopening and unknown dispatch | Resolved: only by owner decision lines in `### Assumptions` | Source: original §8; spec 16 DM-7a decision-section precedent | Reversible: yes
- A-21 | Parallel mode | Resolved: wired by spec 12a REQ-54 and spec 12 REQ-63, which call C-5 (C-10 row 12); this spec's files stay sequential and carry no spec 12 state | Source: `.ai/specs/README.md` (dependency table: spec 12 lists 19 as a prerequisite); spec 12 REQ-54 | Reversible: yes
- A-22 | Policy disabled mid-episode | Resolved: episode paused, not closed; re-enabling continues it with its slots | Source: original §11 row "policy disabled"; reset protection §8 | Reversible: yes
- A-23 | Commit types | Resolved: repair commits are `test:` (new tests) and `fix:` | Source: `rules/git-flow.md:94-96` | Reversible: yes
- A-24 | Run log | Resolved: no new events or fields; `pae-repair` steps logged with existing vocabulary as step names derive from workflow files | Source: `rules/run-log.md:220-229`; spec 15 REQ-31 precedent | Reversible: yes
- A-25 | Timeouts and caps | Resolved: none | Source: ADR-0020; G8 | Reversible: yes
- A-26 | Fix leaves and composite children | Resolved: covered when validated through step 4.3; composite integration excluded | Source: `workflows/spec-run.md:333-340` (step 6 reuses step 4 handoffs); `workflows/phase-composite-validation.md:89-143` | Reversible: yes
- A-27 | Escalation with unknown effort capability | Resolved: `effort-not-applied`, stop | Source: coordinator note (both harnesses declare `unknown`); spec 18 C-3 step 6 | Reversible: yes
- A-28 | Spec 17 evidence lines | Resolved: copied verbatim as `Evidence` items (DM-8 `evidence_refs`; not spec 08 DM-7 evidence references); the repair's own captured runs append OUTPUT lines inside DM-13 entries | Source: `.ai/specs/17-bounded-tool-output.md` DM-9, C-7 row 19 | Reversible: yes
- A-29 | Tree cleanliness at reservation | Resolved: this spec's own definition (outside the task directory and `AI_DIR`); spec 16's `subject.clean` is not read | Source: `.ai/specs/16-scoped-verification.md` DM-3 `clean` (counts `AI_DIR` paths); ADR-0012 (tracked `.ai/` here) | Reversible: yes
- A-30 | Collection stubs and touched test files | Resolved: every path of a `test` commit stays frozen (stubs have no machine-readable marker); findings located in a frozen path are ineligible; test files added by GREEN follow `rules/tdd.md:189` and are not frozen | Source: `workflows/pae-tests.md:151-155`; `rules/tdd.md:179-189`; G3 | Reversible: yes
- A-31 | Effective escalation | Resolved: every declared component must resolve and at least one must change the dispatch (model differs from the local resolution, or spec 18 raised effort with source `escalation`) | Source: G4; spec 18 C-3 step 5 (`.ai/specs/18-reasoning-effort-policy.md` C-3 step 5) | Reversible: yes
- A-34 | Spec 12 naming and writer | Resolved: spec 12's "episode key" is `episode_id` (DM-2); its "slot" is its concurrency slot, never the `local`/`escalated` slots; in parallel mode spec 12's root is the Orchestrator for ledger and record writes (this spec's REQ-08); the spec 12 wiring of REQ-54 is accepted as written, including its statement of the broad-stop case (a dispatched repair worker finishes, no further attempt, repair attempt or recheck starts, the result is recorded through `outcome`, the episode stays open), which spec 12 now states in its own requirements and which this spec only follows | Source: spec 12 REQ-04, REQ-54, C-6 row 8 and A-29; Terminology rows "Episode key" and "Slot"; DM-3 `repair_episode`, DM-6 stage `repair`; spec 12 Notes (follow-up for spec 19: none) | Reversible: yes
- A-33 | Dirty tree on resume | Resolved: the existing git-flow preflight stop stays first; the owner reconciles, then `status` decides | Source: `rules/git-flow.md:16-22`; G4 (ambiguous state stops before mutation) | Reversible: yes
- A-32 | Concurrent Orchestrators | Resolved: unsupported, no lock; sequential re-reservation refused `attempt-pending` | Source: `.ai/specs/15-orchestrator-overhead.md` Out of Scope | Reversible: yes

## Decisions

N/A — auto mode; every resolution is recorded under Assumptions.

## Clarifications

### Session 2026-11-14

- No question was put to the owner (auto mode under standing authorization). A coordinator note
  reported the finished state of specs 17 and 18 (effort capability `unknown` on both harnesses;
  17's notes lines and outcome kinds); folded into C-8, A-27 and A-28.

## Open Questions

- Q-01 | non-blocker | Should this repository track `<task>/repairs/` as knowledge (ADR-0012)
  instead of ignoring it? Impact: detail survives a fresh clone. Recommended: ignore, matching
  specs 15 and 16; limits already survive in the ledger lines.
- Q-02 | non-blocker | Should a repair be allowed to add tests to an existing test file when every
  test named in the RED digest stays byte-identical? Impact: fewer `repair-scope` stops.
  Recommended: no until spec 09 shows misses do not rise.
- Q-03 | non-blocker | Should repair apply in `/phase-pipeline` single-session runs? Impact: a second
  integration point. Recommended: later spec; today's stop kept.

## Notes

### Name mapping (spec 13)

| Today | After 13 |
|---|---|
| `workflows/pav-check.md` | `workflows/atomic-validation-check.md` |
| `workflows/pae-implement.md`; new `workflows/pae-repair.md` | `workflows/atomic-execution-implement.md`; `workflows/atomic-execution-repair.md` |
| `workflows/phase-atomic-validation.md`, `phase-composite-validation.md` | `atomic-validation`, `composite-validation` |
| `rules/orchestration.md`, `rules/tdd.md`, `rules/workflow-globals.md`, `rules/workflow-reference.md` | `contract-orchestration`, `contract-tdd`, `contract-phases`, `contract-state-files` |
| `workflows/spec-run.md` | unchanged |

Name map (spec 13 REQ-68): `rules/contract-repair.md` receives no text moved out of a rule that has a row in `docs/name-map.json`, so it gets no row, no `docs/USAGE.md` row change and no `path_changes` entry, and the edits of existing files in C-7 (the always-stop bullet of `### Conditions that always stop the run`, the `rules/workflow-globals.md` sentence, the `loads:` entry of `workflows/spec-run.md`) are added sentences, section entries or `loads:` entries located by heading or sentence, which survive 13's file renames.

### Implementation hints (nonbinding)

- Hint: order — (1) suite skeleton and fixture R1 with failing cases; (2) ledger parsing, `status`,
  `open`; (3) `classify` and overrides; (4) `reserve`, `check`, `cancel`; (5) `outcome`, progress,
  `close`; (6) rule and workflow text with failing text cases first; (7) docs, ignore rule, ADR.
- Hint: reuse spec 16's C-3 parsing code by copying the rules, not by importing its helper, so that
  each helper stays independently runnable.
- Hint: spec 17's DM-5 records help the repair Implementer locate the first failing test in a
  captured output.

### Change record

- 2026-11-14 — reconciliation with refined peer specs. Targeted edits against specs 09, 12, 13, 14, 15, 16, 17, 18 and 20 in their refined state; no id renumbered, no Q answered. (1) DM-8 `evidence_refs` reads the spec 16 receipt `output` object by mode (`direct`: stream digests; `capture-output`: `reference`, `artifact_id`, `manifest_sha256`) and `findings` come from `findings[].id`. (2) Every spec 16 field this spec reads was checked against spec 16 C-6 row 19; C-10 row 16 now lists them by name. (3) REQ-47, C-5 step 12 and C-10 row 16 state that a recheck is an ordinary spec 16 leaf review whose prior is the answered record and that spec 16 neither ends nor removes the deferred stop. (4) and (5) Every citation of specs 09, 12, 13, 14, 15, 16, 17 and 18 by line number is replaced by a requirement, data-model, contract or section id; REQ-45 and C-10 row 17 follow spec 17 DM-3, DM-9 and C-7 row 19. (6) Spec 12 REQ-54 now wires repair: the Source, Out of Scope, A-21, the spec 12 follow-up and C-10 row 12 state the carry-over of the episode key, the handoff stage `repair` and the no-repair cases; A-34 added. (7) C-4 and C-6 state spec 13's kind, `load`, `phase` and `step`. (8) C-8 step 3 and C-10 row 18 state that an `escalation-unverifiable` effort is never substituted and that a spec 18 stop stays spec 18's own. (9) C-10 row 20 states the read-only contract and the ledger fields spec 20 reads. (10) C-10 row 09 maps the two switches onto spec 09 REQ-52 `switches`.
- 2026-11-14 — second reconciliation pass. Targeted edits against specs 10, 12, 13 and 15; no id renumbered, no Q answered, no requirement or acceptance criterion added (AC-31 gains one clause). (1) Terminology "Repair attempt", DM-2 and C-10 row 15 state that the repair `attempt_id` is not a spec 15 `attempt_id` while the spawn of the repair Implementer is a spec 15 attempt with `supersedes` lineage through `attempt`, that repair resume is governed by `status` alone, that `compose`, `render` and `receipt` are not used for repair, that `reconcile` entries for repair attempts are ignored, and that the `blocked` to `done` plan-row rewrite is a manual write the spec 15 helper neither performs nor verifies. (2) C-6 gains the metadata paragraph: front matter keys `reads`, `writes` and `called_by` (`spec-run`) and a `Called by:` line that begins with the backticked command (spec 10 REQ-05, REQ-23, REQ-35, REQ-46 and A-54); AC-31 asserts it. (3) C-10 row 12 and A-34 say that spec 12 states the broad-stop case itself (12 REQ-04, REQ-54, C-6 row 8, A-29) and its Terminology rows "Episode key" and "Slot" match A-34; the Notes follow-up is updated. (4) A Notes sentence records that `rules/contract-repair.md` moves no text out of a mapped rule, so no name-map row under 13 REQ-68, and the C-7 anchors of the `pav-check`, `spec-run` and `workflow-globals` edits are given by sentence first, with today's line numbers only as a locator. (5) to (7) Checked and unchanged: the spec 16 fields read are those of 16 C-6 row 19 only; C-8 step 3 and C-10 row 18 agree with 18 C-6 row 19, REQ-29 and C-3 step 5; no citation of specs 09, 17 or 20 by line number remains.
- 2026-11-14 — independent final review: spec 17 lines are `Evidence` items, not 08 DM-7 evidence references; REQ-33 sets 18's `session.parameter: "absent"` after an effort refusal; `DECISION.json` shape fixed; disable switch follows spec 14 REQ-32; `/pav-check` insertion anchor corrected; neutral provenance wording; citations corrected.

### Rejected alternatives

- Creating a fix-task leaf for every leaf NEEDS WORK — rejected: new branches, plan rows and full
  cycles redo correct work (original REQ-03).
- Reusing `/pae-implement` with a flag — rejected: its Guard asks before overwriting a completed
  execution, and its GREEN flow assumes the original RED set.
- Classification by the Orchestrator or the Arbiter — rejected: the Orchestrator is context-bounded
  and the Arbiter answers only class A with citations.
- A journal-only ledger — rejected: deleting an ignored directory would reset limits.
- Probability-based strategy selection — rejected: no calibrated data (original §10).
- Recreating a lost repair worker inside its attempt — rejected: a second model run per slot.

### Follow-ups outside this spec (not edited here)

- Specs 12a and 12: none — 12 REQ-04, 12a REQ-54 with 12 REQ-63, 12a DM-3 `repair_episode` and 12 DM-6 stage `repair` already call C-5,
  keep the reservation while an episode is open and state the broad-stop case (C-10 row 12, A-34).
- Spec 18: its C-4 step 2 "Escalation: `null` unless supplied by spec 19" is satisfied by C-8 step 3.
- `.ai/specs/README.md`: no change required; the workstream row already names this spec.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph on opt-in bounded repair, preserved code and RED evidence, recorded attempts and explicit escalation |
| 2 | Out of Scope names concrete exclusions | PASS — D8 and fix-task repair, non-`/spec-run` paths, spec 12 wiring, review contracts (16), effort and models (18, 04), economics (09), frozen-test amendment, validator inventory |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-75; original REQ-01–REQ-09 restated |
| 4 | REQ ↔ AC both ways | PASS — Traceability covers REQ-01–REQ-75 and AC-01–AC-42 |
| 5 | Every AC binary and test-first | PASS — fixture R1 specified; text ACs assert verbatim lines and named tokens |
| 6 | Non-functional targets measurable or N/A | PASS — NFR-01–NFR-06 verifiable; NFR-07 N/A with reason |
| 7 | Data model and contracts specified | PASS — DM-1–DM-18, C-1–C-12 |
| 8 | Error, empty, boundary and concurrency cases | PASS — Edge Cases table; interruption, duplicate save, refused spawn, provider limit, dirty resume; concurrent Orchestrators declared unsupported (A-32) |
| 9 | Every Step 3 ambiguity recorded | PASS — A-01–A-34; Q-01–Q-03 open non-blockers |
| 10 | No blocker question | PASS — none |
| 11 | Existing-code claims cited and verified | PASS — path:line citations checked at `060ce6d`; the critic re-verified them in every round |
| 12 | Terminology matches project definitions | PASS — domain terms reused; new terms defined; rejected synonyms listed; "Repair escalation" distinct from the class-A/B escalation protocol |
| 13 | Feature-sized (1–8 subtasks) | PASS — about seven: ledger and status/open; classification; reserve/check/cancel; outcome/close; rule and workflow text; `/pae-repair`; docs, ignore rule, ADR |
| 14 | Devil's Advocate review | PASS — Review: 5 rounds, score 99/100, critic: sub-agent, open: none critical or major; minor F-41 was applied after round 5 and not re-scored |

Note 2026-11-14 (reconciliation): checks 7, 9 and 11 were re-confirmed against the refined peers after the targeted edits of the Change record; the verdict is unchanged.

Note 2026-11-14 (second reconciliation pass): the points settled with specs 10, 12, 13 and 15 are listed in the Change record; no check result changes and the verdict is unchanged.

Verdict: **READY FOR DEVELOPMENT**, once its roadmap prerequisites (04, 06, 09, 15, 16 and 18; 13
and 08 for names and `loads:`) are delivered. Automated readiness is not owner sign-off.
