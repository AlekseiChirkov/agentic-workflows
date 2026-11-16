# 15. Orchestrator overhead: deterministic checkpoints, inspection and delta rendering

## Source

- **Origin:** workstream 4 ("orchestrator overhead") of the owner's token-optimization
  request of 2026-10-21. Roadmap row 4 of `.ai/specs/README.md` → "Nine token optimization workstreams" — "Fewer status turns,
  bounded history, deterministic inspection and delta rendering; shared state stays
  single-writer" — and order row of `.ai/specs/README.md` → "Dependency order" (order 9, prerequisites 06, 09,
  14, disposition "New workstream 4; no general state engine"). The shared acceptance gates
  G1–G8 (`.ai/specs/README.md` → "Shared acceptance gates") are part of this specification's acceptance contract.
- **Previous revision:** 2026-10-28 (reconciled 2026-11-06), written in Russian. The full
  Russian text, including REQ-01–REQ-08 and AC-01–AC-05, is retrievable from git history of
  this file at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Every identifier is preserved
  below. Faithful English translation of its request (translated from Russian; previous
  revision §2, §3 and §9):
  - Goal (§2): "Leave to the orchestrator the decisions that require judgement, and perform
    repeated checks and the preparation of proposals deterministically. Reduce unnecessary
    loads and polls while keeping the sequence of verifiable actions."
  - Scope (§2): "Checkpoint messages, an optional check of source facts and preparation of
    patches, merging of independent reads, application receipts and recovery after
    interruption." Out of scope: "the general state-changing tool 07, an agent-launch
    service, a change of the ownership model, automatic execution of dependent tasks on an
    unverified base, top-level parallelism and bypassing the rules of 06."
  - Roles (§2): Orchestrator — "verify facts, accept or reject a proposal, change shared
    files sequentially and perform permitted repository operations"; Implementer — "return
    the full result of its boundary and the proposed delta; never present a proposal as
    applied state"; independent Validator — "return a verdict and evidence, keeping
    independence from the Implementer's reasoning"; helper — "only read, compute and print a
    check or a proposal; never change state, the index, branches or commits, never start
    models".
  - REQ-01: "Define complete RED, GREEN, review and completion messages with task/leaf, role,
    event and attempt identifiers, source and checked tree, AC/evidence, exact change/test
    paths, check outcomes, findings and the proposed delta. Short text per 08 does not
    shorten the structured content."
  - REQ-02: "Merge repeated polls and retellings up to the next significant boundary,
    keeping RED before implementation, GREEN before independent review and every
    owner/blocker stop. A worker without a new checkpoint does not force a reread of the
    full state. The legitimate `none/n-a` path is kept without a false RED."
  - REQ-03: "Provide an optional deterministic helper to check branch/base, prepare the list
    of explicit paths for the index, extract the progress block and propose a canonical
    delta. It performs no changes and offers no arbitrary field writes; application belongs
    to the orchestrator."
  - REQ-04: "Before application, check task/leaf, the hash of the source state, the current
    branch/base, permission of the transition and evidence. Protected fields and unrelated
    blocks are preserved. A duplicate is recognized as already applied; a stale or
    contradictory proposal is rejected before change. The helper grants no extra
    permissions."
  - REQ-05: "Limit the active context to the current boundary, the leaf contract/view, open
    findings, short dependency facts and relevant repository evidence. The full history is
    kept with hashes and a retrieval method; a new orchestrator verifies it before using an
    old decision."
  - REQ-06: "Merge independent safe reads into one check with a separate status and
    identity for each result. Dependent changes, approvals, test commits and implementation
    stay sequential. Merging never skips a checkpoint."
  - REQ-07: "Pass to 05 orchestrator requests, tool calls, loaded state bytes and the number
    of boundaries. Compare the full cost and time of the whole chain; moving work into an
    unaccounted child is not a saving."
  - REQ-08: "Keep the manual procedure when the helper is absent, recovery at every boundary
    and G1–G8. New behavioural interfaces are recorded by a decision at implementation; a
    mandatory execution mechanism and the promotion of 07 out of the backlog are not
    authorized."
  - AC-01: "A synthetic chain contains one logical message per actual boundary; redelivery
    creates no new one. Applicable test boundary, test commit, GREEN and independent review
    are ordered. The `none/n-a`, `pinned` and already-started historical paths create no
    false RED. Waiting without an event does not reread the whole history."
  - AC-02: "On identical inputs the helper returns identical proposals. The failure of one
    read is preserved. Files, the index, branches and state are unchanged; no model starts.
    Dependent actions are not merged into one opaque step."
  - AC-03: "Stale state, a wrong branch, another leaf, an invalid transition, a conflicting
    duplicate and damaged evidence change no state. A correct patch preserves protected and
    unrelated bytes; an identical repeat is not applied twice."
  - AC-04: "Interruption before/after each boundary, between files and before the receipt is
    written recovers without invented success or repeated effects. The manual path without
    the helper satisfies the same conditions."
  - AC-05: "Before/after, orchestrator calls, bytes, boundaries and delegated work are
    visible. Enabling, disabling and resuming are described. Synthetic traces are not
    presented as monetary savings of live models."
  - The previous revision also contained a target message schema (§4), a target helper
    interface `scripts/controller-step.sh inspect|render` (§5), an eight-step message
    processing sequence (§6), an interruption table (§7) and read-merging rules (§8). Their
    content is carried into this revision's Data Model, Contracts and Edge Cases; deviations
    are recorded under Assumptions.
- **Implementation review — 2026-11-06 (preserved):**
  - **Disposition:** Planned; textual checkpoint discipline delivered.
  - **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`;
    owner-authorized specification/state reconciliation on 2026-11-06.
  - **Delivered evidence:** RED/GREEN handoffs, separate validation, resume checkpoints, and
    single-writer shared-state rules exist.
  - **Outstanding scope and limits:** The versioned complete checkpoint envelope,
    deterministic inspection/delta helper, input-bound idempotence receipts, and measured
    overhead reduction are not delivered. Native logging markers have a different scope.
  - **Sources:** `workflows/spec-run.md`, `rules/orchestration.md`, `rules/run-log.md`.
  - Existing requirement and acceptance identifiers remain binding. Source inspection and
    historical validation records do not constitute a fresh full-suite or
    deployed-environment certification.
- **This revision:** 2026-11-14, refined in place in an autonomous refinement under the
  owner's standing authorization to replace this file. No question was put to the owner;
  every resolved gap is recorded under Assumptions with its source.

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

1. **Roles and single writer.** `/spec-run` has four roles; the Orchestrator writes
   `state.md`, `plan.md`, shared `.ai/` files and git; the Implementer writes code, tests and
   its own `## Subtask Progress` block; the Validator writes its verdict into its own block
   (`rules/orchestration.md:22-27`). Execution is strictly sequential, one agent at a time
   (`rules/orchestration.md:10-14`). Sub-agents return shared-file changes as a proposed
   delta "in its report" (`rules/orchestration.md:105-108`); the delta cases are listed in
   free prose (`rules/orchestration.md:110-117`). No machine-readable delta syntax exists.
2. **Checkpoints.** The Implementer runs `/pae-tests`, stops and reports the RED digest and
   test files; the Orchestrator commits exactly those paths as `test:`. `target_files:` is
   seeded from the description's Scope at decomposition (`workflows/pd-decompose.md:162`) and
   `/pae-tests` appends test files to it (`workflows/pae-tests.md:207`, `:222`), so at RED it
   can also list planned implementation files that do not yet differ from `HEAD`, although
   `workflows/spec-run.md:248` says it "holds test files only". One message resumes
   the same agent for `/pae-implement` → `/pae-finalize`; the Orchestrator commits the
   implementation as `feat:` (`workflows/spec-run.md:244-272`). `atomic-tests: n-a` has no
   RED report and a single implementation commit (`workflows/spec-run.md:274-277`,
   `rules/git-flow.md:102-103`); `pinned` uses the same test-first commit handoff without
   claiming RED (`workflows/spec-run.md:281-282`). The Validator is a separate agent that
   receives the description path, the test files and `git diff <base_commit>..HEAD`, never the
   Implementer's report (`workflows/spec-run.md:284-292`); NEEDS WORK stops the run
   (`workflows/spec-run.md:297-299`). Workers never run git (`workflows/spec-run.md:245`).
3. **Re-reads after every delta.** After each checkpoint the Orchestrator applies returned
   deltas, then "Re-read[s] the plan and recompute[s] the pending dependency order"
   (`workflows/spec-run.md:194-198`), verifies that the progress block is structurally intact
   after every sub-agent return (`rules/orchestration.md:130-132`) and compresses state
   (`workflows/spec-run.md:312-318`). Each of these is done by reading whole files in the
   Orchestrator's own context; no helper extracts the facts. No script under `scripts/`
   extracts plan, leaf or branch facts for the Orchestrator or renders deltas; `scripts/validate-task.sh`
   checks one task directory's conformance and is not called by `/spec-run` (`scripts/README.md:8-20`).
   Staging takes explicit paths from `target_files:` "plus reviewed knowledge and state updates
   allowed by the repository's tracking policy" (`rules/git-flow.md:155-159`).
4. **Recovery has no application record.** Resume reads `state.md`, reconciles recorded
   branches and commit tips, and resumes "at its existing atomic/git checkpoint"
   (`workflows/spec-run.md:64-79`, `:190-194`, `:380-385`). Nothing records whether a
   returned delta was already applied, partially applied, or applied against a state that
   later changed; a lost worker is recreated from current artifacts
   (`workflows/spec-run.md:193-194`).
5. **Status turns.** The workflow says nothing about how the Orchestrator waits for a worker;
   the only "no polling" sentence concerns telemetry (`workflows/spec-run.md:260`).
6. **Telemetry boundaries.** The run log is write-only during a run and nothing may read it to
   decide (`rules/run-log.md:584-585`). The `/spec-run` RED return is the only named-step
   candidate; GREEN and validation batches stay approximate (`rules/run-log.md:175-180`).
   Spec 05 registers the diagnostics `context.loaded_bytes` and `orchestration.tool_calls`
   (`scripts/usage_telemetry_contract.py:304-313`) whose identifiers must be opaque
   `sha256:` values (`scripts/usage_telemetry_contract.py:350-353`, `:1406-1431`), but no
   producer emits a `diagnostic_measurement` record: the adapter emits only `source_issue`
   diagnostics (`scripts/usage_telemetry_adapter.py:209-214`, `:309-313`).
7. **Report shape.** Spec 08 (order 7, delivered before this spec through 14's prerequisites,
   `.ai/specs/README.md` → "Dependency order") defines four concise report forms with anchored field lists,
   fenced `delta` blocks and a rejection rule for truncated deltas
   (spec 08 DM-8 "Report forms" and its delta rule), and names this spec's checkpoint message
   as the "full structured result" on the helper route only (spec 08 Terminology row "Full
   structured result"). It leaves the inner syntax of a `delta` block and the general envelope
   to this spec (spec 08 DM-8, delta paragraph).
8. **Validator inventory frozen.** New checks cannot be added to
   `scripts/validate-contracts.sh`; standalone checks live in `scripts/`
   (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`); the source guard
   binds every shell and Python file under `tests/` (`tests/fixtures/validator-runtime/source_guard.py:809-813`).
   Many frozen checks grep exact sentences of `workflows/spec-run.md` and
   `rules/orchestration.md` (for example `scripts/validate-contracts.sh:1506-1517`, `:1529`, `:1537-1539`).

Consequence: the Orchestrator spends its own context re-reading whole state and plan files
after every boundary, applies free-text deltas by judgement, and after an interruption cannot
tell an applied delta from an unapplied one except by re-reading and guessing. Duplicate or
late worker results have no identity. None of this is measured, and nothing makes the
checks repeatable.

## Goal

The `/spec-run` Orchestrator keeps the decisions that need judgement and hands every
repeatable check to a deterministic, read-only helper: it inspects task and repository facts
in one bounded call, turns each worker report into one versioned checkpoint message bound to
observed facts, renders the worker's structured deltas into an exact patch whose
preconditions are checked against current bytes, applies that patch itself, and records a
verified receipt — so that each boundary is accepted exactly once, duplicates and late
results have no effect, an interruption at any point resumes without repeated or invented
effects, and the Orchestrator neither polls nor re-reads whole files between boundaries.
Test-first order, independent validation, git rails, owner stops and the single-writer rule
stay as they are; without the helper the existing manual procedure continues unchanged.

## Scope

1. A checkpoint journal per task directory holding write-once attempt records, worker
   reports, checkpoint messages, proposals and receipts.
2. A versioned checkpoint message for the four `/spec-run` boundaries (`red`, `pinned`,
   `green`, `review`), composed deterministically from the worker's spec-08 report and observed
   repository and task facts.
3. A structured syntax for the content of `delta` blocks (five operations) with a closed
   per-checkpoint policy, and its use by the four worker workflows that return deltas under
   `/spec-run`.
4. The optional read-only helper `scripts/controller-step.py` with subcommands `version`,
   `inspect`, `attempt`, `compose`, `render`, `receipt`, `reconcile` and `summary`.
5. The `/spec-run` helper route: attempt records before spawns, report persistence,
   compose → commit → render → apply → receipt per boundary, the acceptance gate, resume
   through `reconcile`, no polling while a worker runs, one progress line per accepted
   boundary.
6. The manual route used when the helper is unavailable or disabled, equal to today's
   procedure.
7. Two on-demand contract rules (`rules/contract-checkpoints.md`,
   `rules/contract-delta-operations.md`), one citation line in the orchestration rule,
   documentation, an ignore rule, a decision record, and the standalone acceptance suite
   `scripts/check-controller-step.py`.
8. The interfaces this spec exposes to specs 05, 08, 09, 12, 14, 16, 17, 18, 19 and 20
   (Contracts → C-10).

## Out of Scope

- A general state-changing tool or arbitrary field writes (spec 07, ADR-0021). The helper
  neither imports nor invokes `scripts/state-tool.py`.
- Parallel execution, worktrees, leaf coordinators and the DM-6 handoff object (spec 12);
  this spec only carries handoff digests (REQ-41).
- Project and task context packets, their freshness and content (spec 14); reviewer packets
  and review scope (spec 16); bounded tool-output capture (spec 17); reasoning effort (spec
  18); repair limits (spec 19); decomposition (spec 20).
- New run-log events, step names, markers or `/phase-pipeline` per-leaf events (spec 09 Q-05); any 05 producer or new 05 metric.
- Changes to `/phase-pipeline`, `/phase-execution`, `/phase-validation`, `/pe-execute` or any
  workflow other than those listed in C-9; Discovery, the Arbiter and the batch gate.
- Changing status vocabularies, protected sections, test-first order, the two-commit rule,
  stop conditions other than the one added by REQ-24, or git rails.
- Structured operations for architecture entries, D8 fix-sibling creation, `children:` lists,
  `## Fix-Tasks` counters and `.ai/memory/*` entries: they stay free-text deltas applied by
  the manual route (REQ-20).
- Measured savings, paid model runs and comparative evaluation (spec 09).
- Locks against a second concurrent Orchestrator on the same task.

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Orchestrator (`/spec-run`) | Runs the helper; writes journal records, worker reports and patches it receives from the helper; applies patches; commits; writes git fields; decides on stops. Sole writer of shared files and of the journal |
| Implementer | Unchanged rights (own progress block, code, tests). Returns its spec-08 report with deltas in DM-4 syntax |
| Validator | Unchanged rights (own block). Returns its spec-08 reports with deltas in DM-4 syntax; never receives Implementer reports, messages or journal paths |
| Arbiter | Unchanged; not part of checkpoints |
| `scripts/controller-step.py` | Reads files and runs read-only git subcommands; prints JSON; writes nothing, starts no model, uses no network |
| `scripts/check-controller-step.py` | Acceptance suite; creates and removes disposable fixture repositories under a temporary directory only |
| Owner | Sets `ORCHESTRAIL_CONTROLLER_STEP=off` to disable the helper route; resolves stops |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Boundary | One of the four points at which a `/spec-run` worker returns: Implementer RED/pinned return, Implementer GREEN return, Validator return | `workflows/spec-run.md:247-299` |
| Checkpoint kind | `red`, `pinned`, `green` or `review` | This spec (A-09) |
| Attempt | One spawned worker instance for one leaf and role; numbered from 1 per leaf and role; a recreated worker is a new attempt | This spec |
| Active attempt | The attempt with the highest number for its leaf and role | This spec |
| Checkpoint report | The worker's final response for a boundary, without run-log marker lines, saved verbatim in the journal | This spec; 08 DM-8 |
| Checkpoint message | The canonical JSON record (DM-3) composed by the helper from one checkpoint report and observed facts; spec 08's "full structured result" for that boundary on the helper route only; on the manual route and outside `/spec-run` the canonical state-file writes plus complete `delta` blocks stay that result | This spec; 08 Terminology row "Full structured result" |
| Delta operation | One JSON line of DM-4 inside a `delta` block | This spec |
| Proposal | The helper's rendering (DM-6) of a message's operations against current file bytes, with an exact patch | This spec |
| Derived proposal | A proposal rendered against bytes that differ from the message's `source_digests` while every operation still holds | Previous revision §6 |
| Receipt | The verified record (DM-7) that a boundary's patch and commit took effect | This spec |
| Checkpoint journal | `<task>/checkpoints/` (DM-1) | This spec |
| Helper route / manual route | Boundary handling with the helper (C-5) / without it (C-8) | This spec |
| Leaf, RED, Pinned, `n-a`, Orchestrator, Implementer, Validator | As defined | `.ai/principles/domain.md:19-35` |
| `WORK_DIR`, task directory | As resolved by `/spec-run` Step 0; 08 DM-7 bases `work:` and `task:` | `workflows/spec-run.md:58-64`; 08 DM-7 |
| `AI_DIR` | `WORK_DIR/.ai` | `rules/phase-atomic-execution.md:18-19` |
| Dirty path | A path that `git status --porcelain=v1 --untracked-files=all` reports as modified, added, deleted or untracked (ignored files excluded) | This spec |
| Canonical completion | A boundary whose effects the canonical state already shows (DM-9 predicates), with or without a journal record | This spec |

Rejected synonyms: "envelope" (spec 12 uses it for the checkpoint message; this spec says
checkpoint message), "transaction" or "commit" for a receipt, "status" for a receipt result,
"close" as a checkpoint kind (folded into `review`, A-09).

## Requirements

Names follow today's files; once spec 13 is delivered (it precedes this spec through spec
09), each path follows 13's rename map (Notes → Name mapping). Requirements REQ-01–REQ-08
keep the previous revision's identifiers and subjects; each is restated as one behaviour,
and the remainder of each previous requirement is split into later identifiers.

### Previous identifiers, restated

- **REQ-01 Checkpoint message.** WHEN the Orchestrator runs `compose` for a saved checkpoint
  report on the helper route, THE SYSTEM SHALL print exactly one checkpoint message containing
  every DM-3 field, derived from that report, the active attempt record and facts observed at
  that moment.
- **REQ-02 No polling.** WHILE a worker of the current boundary is running, THE Orchestrator
  SHALL read no task state, plan, journal or repository fact and send no status query, except
  on one of the triggers of C-7.
- **REQ-03 Read-only helper.** WHEN any `controller-step.py` subcommand runs, THE SYSTEM SHALL
  leave every file, the git index, refs and configuration unchanged, start no model and no
  network connection, and run git only with the subcommands of C-2 and the environment
  `GIT_OPTIONAL_LOCKS=0`.
- **REQ-04 Preconditions before change.** WHEN `render` runs, THE SYSTEM SHALL classify every
  structured operation of the message as `apply`, `already-applied`, `conflict` or `rejected`
  against current bytes (DM-5, DM-6) and print a patch only when no operation is `conflict` or
  `rejected`.
- **REQ-05 Durable history.** THE Orchestrator SHALL store every attempt record, checkpoint
  report, checkpoint message, proposal and receipt of the helper route in the checkpoint
  journal as a write-once file (C-5 save procedure), and SHALL never modify or delete a
  journal file other than its own `*.tmp` files.
- **REQ-06 Independent reads.** WHEN `inspect` runs, THE SYSTEM SHALL perform each read of
  DM-8 independently and report it with its own `status`, `source` and `sha256`, so that a
  failed read neither stops nor hides the others.
- **REQ-07 Journal counts only.** WHEN `summary` runs, THE SYSTEM SHALL print counts derived
  only from journal records (DM-10) and no field for model requests, tool calls, tokens,
  cost, duration or savings.
- **REQ-08 Manual route.** IF the helper route is unavailable or disabled (REQ-33, REQ-34),
  THEN THE Orchestrator SHALL handle every boundary by the manual route (C-8), writing no
  journal record and keeping every existing checkpoint, commit, check and stop.

### Attempts and reports

- **REQ-09 Attempt before spawn.** WHEN the Orchestrator is about to spawn or recreate an
  Implementer or Validator on the helper route, THE Orchestrator SHALL save the attempt record
  printed by `attempt` (DM-2) before the spawn.
- **REQ-10 Report persistence.** WHEN a worker's final response arrives on the helper route,
  THE Orchestrator SHALL save its canonical form (C-5: the response text with lines starting
  with `ORCHESTRAIL_REPORT_V1 ` or `ORCHESTRAIL_DISPATCH_V1 ` removed, line endings converted
  to LF, exactly one trailing LF, written with the harness file-write tool) as
  `reports/<event_id>.md` before running `compose`.
- **REQ-11 Duplicate report.** IF `reports/<event_id>.md` already exists with bytes identical to
  the new report, THEN THE Orchestrator SHALL discard the new copy and produce no new effect.
- **REQ-12 Conflicting report.** IF `reports/<event_id>.md` already exists with different bytes,
  THEN THE Orchestrator SHALL keep the new report as `reports/<event_id>.conflict-<12 hex>.md`
  and stop the run (REQ-24).
- **REQ-13 Superseded attempt.** IF `compose` is given an attempt that is not the active
  attempt of its leaf and role, THEN THE SYSTEM SHALL exit 1 with `attempt-superseded`, and THE
  Orchestrator SHALL change no task state for that report.

### Composition

- **REQ-14 Checkpoint consistency.** IF the leaf block or the report forms contradict the
  requested checkpoint kind (C-4 consistency table), THEN `compose` SHALL exit 1 with
  `checkpoint-mismatch`.
- **REQ-15 Frozen test set.** WHEN `compose` builds a `green` message and a `red` or `pinned`
  receipt exists for the leaf, THE SYSTEM SHALL set `frozen_tests` by comparing the test-path
  digests of that receipt's message with current bytes and its `amendment_notes` count with
  the current one (DM-3).
- **REQ-16 No false RED.** WHERE the leaf block records `atomic-tests: n-a` or is a pre-TDD
  block, THE SYSTEM SHALL accept a `green` message without any `red` or `pinned` receipt or
  `test:` commit, and THE Orchestrator SHALL create no `red` or `pinned` event for that leaf.
- **REQ-17 Explicit staging paths.** WHEN `compose` builds a `red`, `pinned` or `green` message,
  THE SYSTEM SHALL list in `stage_paths` exactly the dirty `target_files:` entries (DM-3) and
  list every other dirty path under `WORK_DIR` (outside the task directory and `AI_DIR`) in
  `unlisted_changes`.
- **REQ-20 Unstructured delta.** IF a `delta` block's first non-blank line does not start with
  `{`, THEN `compose` SHALL record the block in `manual_deltas` with reason
  `delta-unstructured`, and THE Orchestrator SHALL apply it by the manual route after the
  boundary's commit and before running `render` (C-5 step 4).

### Rendering and application

- **REQ-18 Derived proposal.** WHEN a target file's current digest differs from the message's
  `source_digests` entry and every operation is `apply` or `already-applied`, THE SYSTEM SHALL
  print a proposal with `derived: true`, a new `proposal_id`, and the message's `event_id`
  and `payload_digest`, without changing the message.
- **REQ-19 Operation policy.** IF an operation falls outside the DM-5 policy for the message's
  checkpoint kind and role, or would change a protected field, THEN `render` SHALL classify it
  `rejected` with the matching reason code (C-3).
- **REQ-21 Patch application.** WHEN a proposal has a non-empty patch, THE Orchestrator SHALL
  apply it with `git apply --check` followed by `git apply` run from the repository top level,
  in a Bash call that contains no other git command.
- **REQ-22 Receipt verification.** WHEN `receipt` runs, THE SYSTEM SHALL print a receipt only if
  every target file of the event's last proposal has its `after_sha256`, the commit given with
  `--commit` satisfies the C-4 commit rule (required for `red`, `pinned`, `green`; forbidden for
  `review`), and `--manual-applied` is given exactly when `manual_deltas` is non-empty;
  otherwise, or when no proposal of the event is saved, it SHALL exit 1 with `not-applied`,
  `partial`, `diverged`, `commit-mismatch`, `commit-missing`, `manual-unconfirmed` or
  `proposal-missing`.
- **REQ-23 Acceptance gate.** WHILE a boundary is handled on the helper route, THE Orchestrator
  SHALL NOT resume or spawn the next worker step, run the Validator, create the next branch or
  open a pull request for that leaf until the boundary's receipt is saved.
- **REQ-24 Declared stop.** IF a helper subcommand or the save procedure ends with an outcome
  classified `stop` in C-6, THEN THE Orchestrator SHALL stop the run, keep the branch, commits
  and journal, and report the event id, the exit code and every reason code.

### Resume

- **REQ-25 Reconcile first.** WHEN `/spec-run` resumes on the helper route, THE Orchestrator SHALL
  run `reconcile` before Step 0 item 3's clean-tree decision (`workflows/spec-run.md:64-69`),
  include every entry's `next_action` in a stop that item reports, and, when no stop occurs,
  follow each `next_action` (DM-9) before any other mutation.
- **REQ-26 Event classification.** WHEN `reconcile` runs, THE SYSTEM SHALL classify every due
  event (DM-9) into exactly one state, taking the first matching row of DM-9 in table order,
  using only journal records, current file bytes and read-only git facts, and SHALL never
  re-render an event that has a receipt.
- **REQ-27 Commit found.** IF `reconcile` finds that `HEAD` is a commit satisfying the C-4
  commit rule for a received `red`, `pinned` or `green` event without receipt, and its sha is
  absent from the leaf's `commits:`, THEN THE SYSTEM SHALL report state `commit-found` with
  `next_action: "record-commit"` naming that commit, and THE Orchestrator SHALL append it to
  `commits:` and continue at C-5 step 4 instead of committing again.

### Orchestrator conduct

- **REQ-28 Bounded view.** WHEN the Orchestrator needs plan, leaf, branch or dependency facts
  after a boundary on the helper route, THE Orchestrator SHALL obtain them from `inspect`
  instead of reading `state.md` or `plan.md` whole.
- **REQ-29 One progress line.** WHEN a boundary's receipt is saved, THE Orchestrator SHALL report
  it to the user in one line naming the event id, the leaf's resulting statuses and the
  message's `next_gate`, without restating the worker report.
- **REQ-30 Validator isolation.** THE Orchestrator SHALL NOT pass an Implementer report,
  checkpoint message, proposal, receipt or journal path to a Validator.
- **REQ-31 Run log unchanged.** THE delivery SHALL add no run-log event, step name, field or
  marker, and THE Orchestrator SHALL keep every run-log call of `workflows/spec-run.md`; a
  checkpoint message is never a run-log record.
- **REQ-42 Dry run.** WHILE `/spec-run` runs with `--dry-run`, THE Orchestrator SHALL save no
  journal record.

### Route selection

- **REQ-33 Disable switch.** WHERE the environment variable `ORCHESTRAIL_CONTROLLER_STEP` is set
  to a value other than the empty string or `on` (documented value `off`; the rule of spec 14
  REQ-32), THE Orchestrator SHALL use the manual route for the whole run.
- **REQ-34 Availability probe.** WHEN `/spec-run` Step 0 item 2 completes, THE Orchestrator SHALL
  run `python3 -I "$ORCHESTRAIL_HOME/scripts/controller-step.py" version` once and use the
  helper route only on exit 0; IF any later subcommand exits 3, THEN THE Orchestrator SHALL
  switch to the manual route for the rest of the run and report the switch once.
- **REQ-45 Unavailable environment.** IF Python is older than 3.11, `git` cannot be executed,
  or spec 08's report-field lines cannot be read from the source checkout, THEN the helper
  SHALL exit 3 with `unavailable` and a reason code on stderr.

### Canonical contract and delivery

- **REQ-32 Contract drift.** THE contract rules SHALL contain the anchored lines of C-1, and
  `version` SHALL print the same registries; THE acceptance suite SHALL fail when any
  anchored line and the `version` output differ.
- **REQ-35 Frozen validator.** THE delivery SHALL change no expression of
  `scripts/validate-contracts.sh`, SHALL keep every existing check passing, and SHALL place
  its new checks in the standalone `scripts/check-controller-step.py`, which neither
  `scripts/validate-contracts.sh` nor `scripts/sync.sh` calls.
- **REQ-36 Worker delta syntax.** THE workflows `pae-finalize`, `pav-close`, `pav-propose` and
  `phase-composite-validation` SHALL instruct the worker, under `/spec-run`, to return each
  shared-file change that a DM-4 operation expresses as a DM-4 line in a fenced `delta` block,
  and every other shared-file change as a free-text `delta` block. Outside `/spec-run` these
  workflows keep today's behaviour and no consumer applies the rejection rule (08 DM-8).
- **REQ-37 Ignore rule.** THE repository's `.gitignore` SHALL contain the line
  `/.ai/tasks/*/*/checkpoints/`, and THE entry list that `scripts/setup-new-project.sh` appends
  to a consumer's `.gitignore` and the entry list in `docs/USAGE.md` SHALL contain
  `.ai/tasks/*/*/checkpoints/`.
- **REQ-38 Decision record.** THE delivery SHALL add an Accepted ADR recording the checkpoint
  journal, message, delta operations, the stop of REQ-24 and the helper route, indexed in
  `.ai/adr/index.md`.
- **REQ-39 Golden regression.** THE delivered change SHALL pass spec 09's offline suite
  (`python3 -I tests/golden-runs.py`) with no change to its expectations.
- **REQ-40 Audit proposals.** THE delivery SHALL implement, or list as declined with a reason
  in the ADR of REQ-38, every proposal that the spec 13a audit assigns to owner 15
  (13a REQ-02, which names 15 as one of the owners of fixes).
- **REQ-41 Handoff digests.** WHERE a dispatch carries a spec-12 DM-6 handoff, THE attempt
  record SHALL carry its digest in `input_handoff_digest` and the receipt SHALL carry the digest
  of the handoff the root builds after that checkpoint in `output_handoff_digest`; no journal
  record SHALL contain a DM-6 object.
- **REQ-43 Input bound.** IF a report, journal record or patch read by the helper exceeds
  1,048,576 bytes, THEN the helper SHALL exit 2 with `input-too-large`.
- **REQ-44 Determinism.** WHEN a subcommand runs twice on identical file bytes and git state,
  THE SYSTEM SHALL print byte-identical stdout and use no clock, random value or environment
  value other than those C-2 names.
- **REQ-46 Operating documentation.** THE delivery SHALL document in `docs/USAGE.md` and
  `docs/SPEC-RUN-QUICKSTART.md` how to enable, disable and resume the helper route and where
  the journal lives.
- **REQ-47 No savings claim.** THE delivered documentation, ADR and reports SHALL state that no
  token, cost or time saving of the helper route has been measured and that comparisons
  belong to spec 09.
- **REQ-48 Vocabulary entries.** THE delivery SHALL add the terms Checkpoint report,
  Checkpoint message, Checkpoint journal, Proposal, Receipt and Attempt to
  `.ai/principles/domain.md` before the rules use them.
- **REQ-50 Final response composition.** THE `/spec-run` spawn instructions for the
  Implementer's GREEN batch and for the Validator SHALL require a final response that contains,
  in step order, every spec-08 report form the batch produced (GREEN; Check, then Completion
  when `/pav-close` ran), followed by every `delta` block the batch produced.
- **REQ-51 Context packet fields.** WHEN `attempt` or `compose` runs, THE SYSTEM SHALL set
  `packet_digest` to the digest of the leaf's latest Orchestrator `context-packet:` notes
  entry for the role (spec 14 DM-11; a `successor` entry counts) and `task_contract_hash` to
  `sha256:` plus `parts.contract.sha256` of that packet's manifest in the spec-14 store, and
  set both to `null` when the entry is absent or `none`, or the packet file is missing.
- **REQ-49 Rule size.** Each new rule file SHALL be `load: on-demand` and SHALL raise no
  `rule-size-exceeded` finding of spec 08's meter (08 REQ-01: at most 700 words per top-level
  rule, whatever its `load:` mode); WHERE the C-1 sections of
  `rules/contract-checkpoints.md` exceed that limit, they SHALL be split into further
  `rules/contract-checkpoints-<topic>.md` files, each section keeping its heading.

## Data Model

All entities are **new**. JSON records are UTF-8 with sorted keys, `ensure_ascii=False`,
separators `,` and `:` and one trailing LF ("canonical JSON"). A digest is `sha256:` followed
by 64 lowercase hex characters. A record's self-digest (`payload_digest`, `proposal_id`) is
computed over the canonical JSON of the record without that key and without the trailing LF.
A file digest covers the file's raw bytes; an absent file has digest `null`.

### Identifiers

| Identifier | Form | Example |
|---|---|---|
| `leaf_id` | `^T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?$` (header id of `.ai/specs/07-state-tool.md` `## Data Model`; forms from `workflows/pv-create-fixes.md:58,75`) | `T-04d-fix-rounding` |
| `role` | `implementer` or `validator` | |
| `attempt` | integer ≥ 1 without leading zeros | `2` |
| `attempt_id` | `<leaf_id>.<role>.<attempt>` | `T-03.implementer.1` |
| `event_id` | `<attempt_id>.<checkpoint kind>` | `T-03.implementer.1.red` |
| `task_id` | base name of the canonical task directory | `task-12-oauth-login` |
| `repository_id` | digest of the UTF-8 canonical absolute path of `git rev-parse --git-common-dir` | |
| `worktree_id` | digest of the UTF-8 canonical absolute path of `git rev-parse --show-toplevel` | |
| Path reference | 08 DM-7 form `work:<relative POSIX path>` or `task:<relative POSIX path>`; no `..`, no leading `/` | `work:src/token.py` |

### Note entries (parsing rule, new)

The note entries of a leaf block are obtained by taking every `notes` field group (07 grammar),
its field line without the `notes:` label and each of its continuation lines; splitting each
of these lines on `; `, except that a piece which follows a `tdd: red digest —` piece on the same
line, matches `^.+ → test_\w+(, test_\w+)*$` and starts with none of `tdd:`, `context-` or `verification:` is joined to
that digest entry (the digest separates its behaviours with `; `, `workflows/pae-tests.md:225`,
while spec 14 DM-11 appends other entries to the same line); and trimming spaces from each piece. Every non-empty piece is one entry, in file order. This covers separate `notes:` groups, continuation lines
(`workflows/pae-tests.md:209-210`) and `; `-joined entries (spec 14 DM-11, append rule). "A note starting with X" means an entry
starting with X. `amendment_notes`, the C-4 note checks and REQ-51 use this rule.

### DM-1 Checkpoint journal (new; local, ignored)

```text
<task>/checkpoints/
  attempts/<attempt_id>.json
  reports/<event_id>.md
  reports/<event_id>.conflict-<first 12 hex of the report digest>.md
  messages/<event_id>.json
  proposals/<event_id>.<proposal_seq>.json
  proposals/<event_id>.<proposal_seq>.patch      (only when the patch is non-empty)
  receipts/<event_id>.json
```

Created by the Orchestrator on the first helper-route spawn of the task. Files are created
once and never rewritten; readers ignore names ending in `.tmp`. The journal moves with the
task directory and is never committed (REQ-37). `/compress-state` does not touch it. No
cleanup is defined. Migration: none; a task without a journal is a manual-route task.

### DM-2 Attempt record (`checkpoint_attempt`)

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | |
| `kind` | `"checkpoint_attempt"` | |
| `attempt_id`, `leaf_id`, `role`, `attempt` | as Identifiers | `attempt` = 1 + highest existing attempt for leaf and role |
| `supersedes` | `attempt_id` or `null` | The previous attempt of this leaf and role |
| `dispatched` | object | `repository_id`, `worktree_id`, `branch` (string or `null` when detached), `head_revision` (full object name), `state_sha256`, `plan_sha256`, `description_sha256` at the time `attempt` ran |
| `packet_digest`, `task_contract_hash` | digest or `null` | Spec 14 packet in effect at dispatch (REQ-51) |
| `input_handoff_digest` | 64 hex or `null` | Spec 12 DM-6 digest passed with `--input-handoff-digest` |
| `telemetry_ref` | string or `null` | The run-log adapter `checkpoint_id` issued for this spawn (`workflows/spec-run.md:208-230`), passed with `--telemetry-ref`; opaque, never read to decide |

### DM-3 Checkpoint message (`checkpoint_message`)

| Field | Type | Meaning |
|---|---|---|
| `schema_version`, `kind` | `1`, `"checkpoint_message"` | |
| `event_id`, `attempt_id`, `leaf_id`, `role`, `attempt`, `checkpoint` | Identifiers | `checkpoint` ∈ `red`, `pinned`, `green`, `review` |
| `task_id`, `repository_id`, `worktree_id` | Identifiers | Must equal the attempt record's `dispatched` values, else `worktree-changed` |
| `branch`, `head_revision` | observed | Current branch (or `null`) and `HEAD` |
| `base_commit` | string or `null` | The leaf block's `base_commit:` value |
| `block` | object | Observed `atomic_tests`, `atomic_execution`, `atomic_validation` (string or `null` when absent), `blocker` (string), `amendment_notes` (number of note entries starting with `tdd: test amended — `) |
| `test_mode` | `ordinary`, `characterize`, `n-a`, `pre-tdd` or `null` | `red` → `ordinary`; `pinned` → `characterize`; `green` → `n-a` when `atomic-tests: n-a`, `pre-tdd` when the field is absent, else the `test_mode` of the message of the leaf's latest `red`/`pinned` receipt, else `null`; `review` → `null` |
| `verdict` | `"DONE"`, `"NEEDS WORK"` or `null` | Check form `Verdict:` value; `review` only |
| `test_paths` | list of `{"path", "sha256"}` sorted by path (`path` in `work:` form; `sha256` `null` for a deleted path) | `red`/`pinned`: the dirty `target_files:` entries; `green`: the `test_paths` of the message of the leaf's latest `red`/`pinned` receipt, else the changed paths of the leaf's `test:` commit recorded in `commits:`, else (`n-a`, `pre-tdd`) `[]`, each hashed now; `review`: `[]` |
| `changed_paths` | same shape | `green`: the dirty `target_files:` entries (implementation files and any amended test files); otherwise `[]` |
| `stage_paths` | list of strings sorted | Paths relative to `WORK_DIR` for `git add`, run in `WORK_DIR`: `red`/`pinned` → `test_paths`; `green` → `changed_paths`; `review` → `[]`. A deleted path is staged by `git add <path>` like any other. `target_files:` entries that are not dirty are not staged |
| `unlisted_changes` | list of strings sorted | Changed or untracked non-ignored paths under `WORK_DIR`, outside the task directory and `AI_DIR`, not in `target_files:` |
| `frozen_tests` | `intact`, `amended`, `changed-unrecorded`, `not-applicable`, `unknown` | `green` only: `intact` when every `test_paths` digest equals the digest in the receipt's message; `amended` when some differ and `block.amendment_notes` is greater than in that message; `changed-unrecorded` when some differ and it is not; `unknown` when the test paths came from a `test:` commit instead of a receipt; `not-applicable` for `n-a`, `pre-tdd` and the other kinds |
| `source_digests` | object | `task:state.md` and `task:plan.md` (the only DM-4 targets) → file digest at compose time |
| `description_sha256` | digest | The leaf's `description.md` |
| `report_sha256` | digest | `reports/<event_id>.md` |
| `report_forms` | list of strings in report order | Form names detected (C-4): `RED`, `GREEN`, `Check`, `Completion` |
| `acceptance_criteria`, `findings`, `blockers`, `decisions_needed`, `evidence` | lists of strings | Verbatim list items of the corresponding form fields, all forms in report order |
| `empty_reasons` | object | For each of the five lists above that is empty: the verbatim field value (`none`, `unknown — …`, `not applicable — …`) of the first form |
| `next_gate` | string | `Next:` value of the last form |
| `proposed_delta` | list | Structured operations (DM-4) in report order, each with an added `block` (0-based index of its `delta` block) and `line` (1-based line within the block) |
| `manual_deltas` | list of `{"block", "sha256", "reason"}` | Unstructured or empty `delta` blocks; `reason` ∈ `delta-unstructured`, `delta-empty` |
| `packet_digest`, `task_contract_hash` | digest or `null` | Packet in effect when `compose` runs (REQ-51); differs from the attempt record after a spec-14 successor packet at the RED continuation |
| `context_receipt` | string or `null` | The leaf's latest worker `context-receipt:` notes entry for the role, verbatim (spec 14 DM-11) |
| `input_handoff_digest`, `telemetry_ref` | copied | From the attempt record |
| `payload_digest` | digest | Self-digest |

`acceptance_criteria` replaces the previous revision's `ac_ids`: subtask descriptions carry no
criterion identifiers today (`templates/subtask-description.md:32-37`); when a spec-14 contract
supplies identifiers, they appear verbatim in the items.

### DM-4 Delta operations (worker-authored; one JSON object per line)

| `op` | Other keys (all required) | Target and effect |
|---|---|---|
| `plan-status` | `row`, `from`, `to` | `plan.md` `## Subtasks` table row whose `ID` cell equals `row`; the `Status` cell (columns located by header name) changes from `from` to `to`; both in the `plan.md` status vocabulary (`rules/workflow-globals.md:268-278`) |
| `block-field` | `block`, `field`, `from`, `to` | Composite block `block` in `## Subtask Progress`; `field` ∈ `rollup`, `integration-validation` (header segments, vocabularies `rules/workflow-globals.md:218-219`) or `blocker` (field line; `to` non-empty single line) |
| `block-notes-append` | `block`, `text` | Adds the field line `  notes: <text>` after the last `notes` field group of composite block `block` |
| `section-append` | `section`, `lines` | Task `state.md` section whose heading line equals `section`, which must be `## Improvement Proposals (<leaf>)` or `## Integration Issues (<composite>)`; appends `lines` (non-empty list) at the end of the section, or creates the section at the end of the file when absent |
| `request` | `action` | `action` = `compress-state`; produces no patch; satisfied by the existing compression of `workflows/spec-run.md:312-314` |

Every string value is single-line UTF-8 without CR, LF or NUL; unknown or missing keys, a
non-string value or a duplicate key make the line invalid (`delta-invalid`). An operation
whose `from` equals `to` is valid and is classified `already-applied` when the current value
equals it (a routine "unchanged" result of `workflows/pae-finalize.md:53-60`), else
`conflict`. Lines are parsed
in order; later operations see the effects of earlier ones.

Rendering rules: a `Status` cell is rewritten as one space, `to`, and spaces padding the cell to
its previous character length (no padding when `to` is longer, then one trailing space). A
header segment `field: value` keeps its position. `section-append` keeps one blank line before
the next `## ` heading and separates a created section from preceding content by one blank
line. Blocks are parsed with the grammar of `.ai/specs/07-state-tool.md` `## Data Model →
Section and block grammar` (a formalization of `rules/workflow-globals.md:173-222`); unknown
fields, including `state_receipts:`, are preserved byte for byte.

Idempotence: an operation is `already-applied` when its effect already holds — `to` equals the
current value (including `from` = `to`), the exact `notes` text exists in a `notes` group of the
block, or `lines` already occur contiguously in the section; it is `apply` when `from` equals
the current value (or the append target lacks the text); otherwise `conflict`.

### DM-5 Operation policy

"Own leaf" is the message's `leaf_id`; "own composite" is the composite block whose actual
`children:` list contains it (`workflows/pae-finalize.md:53-55`). Any operation not listed is
`rejected` (`op-not-allowed`); an allowed operation with an unlisted transition is `rejected`
(`transition-not-allowed`). The policy check runs first, then the DM-4 idempotence
classification. An operation whose `from` equals `to` passes the transition check whenever its
operation, target row or block and field are allowed for the checkpoint at all, and is then
classified by idempotence.

| Checkpoint / role | Allowed operations and transitions |
|---|---|
| `red`, `pinned` / implementer | none |
| `green` / implementer | `plan-status` own leaf `not-started`/`in-progress` → `done`; `plan-status` own composite from `not-started`, `in-progress`, `done`, `blocked` to `in-progress`, `done` or `blocked`; `block-field` own composite `rollup` (any → any value) and `blocker`; `block-notes-append` own composite; `request` |
| `review` / validator | `plan-status` own leaf `done` → `reviewed` when `verdict` is `DONE`, `done` → `blocked` when `NEEDS WORK`; `plan-status` own composite `done`/`in-progress` → `reviewed` only when its `integration-validation` is `complete` after the preceding operations, and `reviewed`/`done` → `in-progress`; `block-field` own composite `integration-validation` (any value → any other value of its vocabulary, including the D8 revert to `not-started`, `workflows/phase-composite-validation.md:133-134`), `rollup` (any → any value) and `blocker` (any text → any text); `block-notes-append` own composite; `section-append` for `## Improvement Proposals (<own leaf>)` and `## Integration Issues (<own composite>)`; `request` |

Protected (`protected-field`, always `rejected`): any leaf block field; git fields; `children:`;
any block or row other than own leaf and own composite; removal of any line.

### DM-6 Proposal (`checkpoint_proposal`) and patch

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"checkpoint_proposal"` |
| `event_id`, `payload_digest` | Of the message (the "original event" of the previous revision) |
| `proposal_seq` | 1 + number of proposals of this event already in the journal |
| `derived` | `true` when any target's current digest differs from `source_digests` |
| `operations` | One `{"index", "op", "classification", "reason"}` per structured operation; `reason` is `null` for `apply`/`already-applied` |
| `files` | Per changed target, in operation order of first use: `{"target", "before_sha256", "after_sha256"}` |
| `requests` | Actions of `request` operations |
| `manual_deltas` | Copied from the message |
| `patch_sha256` | Digest of the patch bytes, or `null` when no file changes |
| `apply_root` | Absolute repository top level |
| `proposal_id` | Self-digest |

The patch is a unified diff with `a/` and `b/` prefixes, paths relative to the repository top
level, one file section per `files` entry, three context lines, LF endings, and nothing else.
`render --emit json` prints the proposal; `render --emit patch` prints the patch; both read the
same inputs.

### DM-7 Receipt (`checkpoint_receipt`)

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"checkpoint_receipt"` |
| `event_id`, `payload_digest` | Of the message |
| `seq` | 1 + number of receipts already in the journal |
| `proposal_ids` | Every proposal of the event, in `proposal_seq` order |
| `files` | Of the proposal with the highest `proposal_seq`: `{"target", "before_sha256", "after_sha256"}` |
| `manual_deltas` | Of the message, each with `"applied": "asserted"` (`--manual-applied`; applied before `render`, REQ-20) |
| `commit` | `null`, or `{"sha", "parent", "paths": [{"path", "sha256"}], "bookkeeping_paths": [...]}` verified by C-4 (paths top-level relative) |
| `state_sha256`, `plan_sha256` | Current digests when the receipt is printed |
| `output_handoff_digest` | 64 hex or `null` (REQ-41) |

### DM-8 Inspection (`controller_inspection`)

| Field | Meaning |
|---|---|
| `schema_version`, `kind` | `1`, `"controller_inspection"` |
| `reads` | One entry per read, in this fixed order: `git-repository`, `git-head`, `git-status`, `task-state`, `plan`, `leaf-block` (only with `--leaf`), `leaf-description` (only with `--leaf`), `journal`; each `{"name", "status": "ok"\|"error", "source", "sha256", "error_code"}`; `error_code` is `null` or one of `missing`, `unreadable`, `too-large`, `invalid-utf8`, `parse-error`, `git-failed` |
| `repository` | `repository_id`, `worktree_id`, `top_level`, `branch`, `head_revision`, `dirty_paths` (sorted, relative to `WORK_DIR`, ignored files excluded) |
| `task` | `task_id`, `flow`, `phases` (the `## Phases` values) |
| `plan_rows` | `{"id", "type", "status", "depends_on", "dependencies_satisfied"}` per row in table order; `type` `leaf` when the column is absent; `depends_on` `[]` for `—`, `-` or empty; `dependencies_satisfied` by `workflows/pe-execute.md:32-33` (leaf `done`/`reviewed`; composite also `integration-validation: complete`) |
| `leaf` | With `--leaf`: header statuses, `last_action`, `target_files` (split on `,` and trimmed as spec 16 C-3; empty pieces dropped), `blocker`, `notes` (all groups), git fields, unknown field names, `composite_parent`, `description_path` |
| `journal` | With `--leaf`: active attempt per role and the latest event state per checkpoint kind (DM-9 states) |
| `obstacles` | Sorted codes: `branch-mismatch` (current branch ≠ block `branch:`), `base-commit-not-ancestor`, `block-invalid`, `plan-row-missing`, `plan-table-invalid`, `dependency-unknown`, `dependency-cycle`, `description-missing`, `description-ambiguous`, `journal-record-invalid` |
| `sufficient` | `true` only when every read is `ok` |

### DM-9 Reconciliation (`checkpoint_reconciliation`)

Output: `{"schema_version": 1, "kind": "checkpoint_reconciliation", "journal": "present" | "absent",
"events": [...]}`; each entry `{"attempt_id", "event_id", "expected", "state", "next_action",
"details"}`, sorted by `attempt_id` then by kind order (`red`/`pinned`, `green`, `review`).

**Due events.** For each attempt record: a validator attempt is due `review`; an implementer
attempt is due its test boundary (`red` or `pinned`) and `green`, except that no test
boundary is due when the leaf block records `atomic-tests: n-a` or is pre-TDD, or when a
`red`/`pinned` receipt of an earlier attempt of the leaf exists (a recreated Implementer
resumes at `green`, `workflows/spec-run.md:190-194`). Every due event that has a report,
message or receipt gets an entry with its `event_id`. In addition, the first due event of the
active attempt without any record gets one entry with `event_id: null` and `expected` set to
`test-boundary`, `green` or `review`; later due events without records get none.

**Canonical completion predicates** (read from the leaf block, its `commits:` and the plan row):
test boundary — `commits:` has an entry of type `test:`; `green` — `atomic-execution: complete`,
plan row `done` or `reviewed`, and `commits:` has an entry whose type is not `test`
(`rules/git-flow.md:91-95`); `review` —
`atomic-validation` is `complete` or `failed` and the plan row is `reviewed` or `blocked`.

**Commit requirement** (`red`, `pinned`, `green`): a commit satisfying the C-4 commit rule
lies between the attempt's `dispatched.head_revision` (exclusive) and `HEAD` (inclusive) and its
sha is in `commits:`. `review` has no commit requirement.

States, evaluated in table order; the first matching row applies:

| # | `state` | Condition | `next_action` |
|---|---|---|---|
| 1 | `invalid` | A record of the event fails its schema, self-digest or bound | `stop` |
| 2 | `receipt-contradicted` | Receipt whose commit is not an ancestor of `HEAD` or no longer exists | `stop` |
| 3 | `receipted` | Valid receipt | `none` |
| 4 | `superseded` | Attempt is not active | `none` |
| 5 | `conflicted` | A `reports/<event_id>.conflict-*` file exists, or a message exists and `render` would classify an operation `conflict` or `rejected` | `stop` |
| 6 | `manual-route` | A message exists and `render` would exit 1 with a fallback code (C-6); or no message exists and the canonical completion predicate holds; or a report but no message exists and `compose` would exit 1 with a fallback code | `none` when the canonical completion predicate holds, else `manual` |
| 7 | `commit-found` | Message exists; a commit satisfying the commit predicate is `HEAD` but its sha is not in `commits:` | `record-commit` (REQ-27) |
| 8 | `received` | Message exists and the commit requirement is not met | `commit` |
| 9 | `committed` | Message exists, commit requirement met, no proposal saved | `manual-then-render` when `manual_deltas` is non-empty, else `render-and-apply` |
| 10 | `applied-unreceipted` | A proposal is saved and a fresh render classifies no operation `apply` | `receipt` |
| 11 | `partially-applied` | A proposal is saved and a fresh render classifies some operations `already-applied` and others `apply` | `render-and-apply` |
| 12 | `proposed` | A proposal is saved and every operation is still `apply` | `render-and-apply` |
| 13 | `reported` | Report, no message | `compose` |
| 14 | `dispatched` | No record for the due event (`event_id: null`) | `await-or-recreate` (recreate per `workflows/spec-run.md:193-194` when the worker is gone) |

"Would exit" means `reconcile` runs the same checks as that subcommand in-process, read-only,
without printing its output. Every event therefore has at least one saved proposal before its
receipt; an event without structured operations gets a proposal with empty `files`.

An event of kind `review` meets the commit requirement trivially, so it goes from `reported`
to `committed`. Manual deltas applied before an interruption are
re-checked by the manual route, which reads each target before changing it (C-8).

Without a journal, `reconcile` prints `{"events":[],"journal":"absent","kind":"checkpoint_reconciliation","schema_version":1}`
and exits 0; the Orchestrator then uses the manual route's existing reconciliation (C-8).

### DM-10 Summary (`checkpoint_summary`)

`{"schema_version": 1, "kind": "checkpoint_summary", "task_id", "leaves": {<leaf_id>:
{"attempts": {"implementer": n, "validator": n}, "events": {<event_id>: <DM-9 state>}}},
"totals": {"attempts", "reports", "messages", "proposals", "derived_proposals", "receipts",
"operations_applied", "operations_already_applied", "manual_deltas", "conflict_reports",
"unlisted_change_paths"}}`. Every count is an integer ≥ 0 computed from journal records only.

## Contracts & Interfaces

### C-1 Contract rules and anchored lines

`rules/contract-checkpoints.md` (`load: on-demand`; a mandatory entry of `spec-run`'s spec-08
`loads:` declaration) has exactly these sections: `## Helper route` (C-5 including the save
procedure), `## Stop classes` (C-6), `## Waiting` (C-7) and `## Manual route` (C-8).
`rules/contract-delta-operations.md` (`load: on-demand`) has the section `## Delta operations`
(DM-4 and DM-5), declared in the `loads:` of the four workflows of REQ-36.
`rules/orchestration.md → ## Shared-file discipline` gains one sentence citing both as the
canonical definitions. The records of DM-2, DM-3 and DM-6–DM-10 are defined by this spec's Data
Model and produced only by the helper, whose `version` output names their schema versions;
agents never author them.

Anchored lines, each exactly once in the named file:

| File | Line |
|---|---|
| `rules/contract-checkpoints.md` | `Checkpoint kinds: red \| pinned \| green \| review` |
| `rules/contract-checkpoints.md` | `Checkpoint journal: attempts \| reports \| messages \| proposals \| receipts` |
| `rules/contract-checkpoints.md` | `Controller-step exit codes: 0 completed \| 1 rejected \| 2 invalid-invocation \| 3 unavailable` |
| `rules/contract-checkpoints.md` | `Controller-step disable: ORCHESTRAIL_CONTROLLER_STEP=off` |
| `rules/contract-checkpoints.md` | `Checkpoint stop codes: ` followed by the exit 1 and exit 2 codes of the C-6 stop row, separated by ` \| `, in table order |
| `rules/contract-delta-operations.md` | `Delta operations: plan-status \| block-field \| block-notes-append \| section-append \| request` |

The journal line names the subdirectories of `<task>/checkpoints/` (DM-1).

Anchored lines in `workflows/spec-run.md`, each exactly once (Step 0 for the first two, Step 4
for the others):

```text
Checkpoint route: after Step 0 item 2, probe `controller-step.py version` once; use `contract-checkpoints → ## Helper route` only on exit 0 and only while `ORCHESTRAIL_CONTROLLER_STEP` is unset, empty or `on`; otherwise, and after any later exit 3, use `contract-checkpoints → ## Manual route`.
Checkpoint resume: on the helper route, run `controller-step.py reconcile` before item 3's clean-tree decision, name its next actions in any stop, and otherwise follow them before any other mutation.
Checkpoint waiting: while a worker runs, act only on the triggers of `contract-checkpoints → ## Waiting`.
Checkpoint acceptance: on the helper route, a leaf's next worker step, its Validator, the next branch and any pull request wait for the saved receipt of the preceding boundary.
Checkpoint facts: on the helper route, take plan, leaf, branch and dependency facts after a boundary from `controller-step.py inspect`, not from whole-file reads.
Checkpoint progress: report each accepted boundary in one line — event id, resulting statuses, next gate — without restating the worker report.
Checkpoint isolation: never pass an Implementer report, checkpoint message, proposal, receipt or journal path to a Validator.
Checkpoint final response: end the GREEN batch and the validation batch with every report form of the batch in step order, then every delta block.
Checkpoint dry run: `--dry-run` saves no journal record.
```

`version` prints exactly (one line, canonical JSON; shown wrapped here):

```text
{"kind":"controller_version","record_schemas":{"checkpoint_attempt":1,"checkpoint_message":1,
"checkpoint_proposal":1,"checkpoint_receipt":1,"checkpoint_reconciliation":1,"checkpoint_summary":1,
"controller_inspection":1},"registries":{"checkpoint_kinds":["red","pinned","green","review"],
"delta_operations":["plan-status","block-field","block-notes-append","section-append","request"],
"disable":"ORCHESTRAIL_CONTROLLER_STEP=off","exit_codes":{"0":"completed","1":"rejected",
"2":"invalid-invocation","3":"unavailable"},"journal":["attempts","reports","messages","proposals",
"receipts"],"stop_codes":[<stop codes in table order>]},"schema_version":1}
```

The drift check (AC-13) takes the text after the first `: ` of each rule line; a line without
` | ` compares as a string (`disable`); others split on ` | ` into a list, and the exit-code
items split once more on their first space into the `exit_codes` map; the result must equal the
registry of the same name.

### C-2 Command line

```text
python3 -I scripts/controller-step.py version
python3 -I scripts/controller-step.py inspect   --work W --task T [--leaf ID]
python3 -I scripts/controller-step.py attempt   --work W --task T --leaf ID --role R
                                                [--input-handoff-digest H] [--telemetry-ref S]
python3 -I scripts/controller-step.py compose   --work W --task T --attempt-id A --checkpoint K
python3 -I scripts/controller-step.py render    --work W --task T --event E --emit json|patch
python3 -I scripts/controller-step.py receipt   --work W --task T --event E [--commit SHA]
                                                [--manual-applied] [--output-handoff-digest H]
python3 -I scripts/controller-step.py reconcile --work W --task T
python3 -I scripts/controller-step.py summary   --work W --task T
```

- `--work` and `--task` resolve to canonical absolute directories; the task directory and every
  DM-4 target must lie inside `git rev-parse --show-toplevel` of `WORK_DIR`
  (`target-outside-repository`, exit 2).
- `compose` reads `reports/<event_id>.md` and the attempt record; `render` and `receipt` read
  `messages/<event_id>.json` and, for `receipt`, the event's proposals. If
  `messages/<event_id>.json` already exists, `compose` prints it and exits 0 when its bytes
  equal the message it would print, and otherwise exits 1 with `event-exists`.
- `--checkpoint` takes a kind of DM-3; `--role` `implementer` or `validator`; `--emit` `json` or
  `patch`; handoff digests 64 lowercase hex; `--telemetry-ref` matches
  `^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$` (`rules/run-log.md` `hook.identity_pattern`). Any other value, a repeated option or a missing required
  option → exit 2 `invalid-arguments`.
- The source checkout is `ORCHESTRAIL_HOME` when set and non-empty, otherwise the parent of the
  helper's own directory (the existing script convention, `.ai/memory/architecture.md:179`);
  spec 08's `rules/contract-reports.md` is read from it.
- Git subcommands used, always with `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `LC_ALL=C`
  and no pager: `rev-parse`, `status --porcelain=v1 -z --untracked-files=all --no-renames`,
  `merge-base --is-ancestor`, `cat-file`, `diff-tree -r -z --no-commit-id --name-status`,
  `ls-files`. Environment values read: `PATH`, `HOME`, `ORCHESTRAIL_HOME`.
- stdout carries exactly one canonical JSON document (or, for `--emit patch`, the patch) on
  exit 0 and on exit 1; it is empty on exits 2 and 3. stderr carries one line `<code>:
  <detail>` per reason, without file contents.

### C-3 Exit and reason codes

| Exit | Meaning | Reason codes |
|---|---|---|
| 0 | Completed; facts may include obstacles; never a permission to advance | — |
| 1 | Rejected; stdout `{"schema_version":1,"kind":"controller_rejection","command","event_id","reasons":[{"code","detail","index"}]}`; for `inspect`, stdout is the DM-8 document with `sufficient: false` | `attempt-superseded`, `attempt-unknown`, `report-not-canonical`, `commit-missing`, `manual-unconfirmed`, `proposal-missing`, `checkpoint-mismatch`, `worktree-changed`, `block-invalid`, `red-not-established`, `report-form-missing`, `report-form-unexpected`, `report-contains-marker`, `delta-truncated`, `delta-invalid`, `event-exists`, `conflict`, `op-not-allowed`, `transition-not-allowed`, `protected-field`, `target-missing`, `unsupported-line-endings`, `invalid-utf8`, `not-applied`, `partial`, `diverged`, `commit-mismatch`, `journal-record-invalid`; `inspect`: any DM-8 read `error_code` |
| 2 | Invalid invocation | `invalid-arguments`, `unknown-command`, `target-outside-repository`, `input-too-large`, `file-missing` |
| 3 | Unavailable | `unavailable` with `python-unsupported`, `git-unavailable` or `report-contract-unavailable` |

### C-4 Composition rules

**Report forms.** `compose` reads the four `Report fields — <Form>:` lines of spec 08's
`rules/contract-reports.md` from `$ORCHESTRAIL_HOME`. A form is a run of field lines
`<Field>:` or `<Field>: <value>` whose names equal one anchored list in order, starting at
`Boundary:`; list items are the following lines that start with one or more spaces and `- `.
Fenced `delta` blocks are recognized with the fence rules of `rules/run-log.md:408-418`
applied to the info string `delta`. Spec 08's rejection rule for truncated blocks (08 DM-8,
"Delta block" rule) is applied first on the helper route; a block it
cannot bring to a complete report yields `delta-truncated` (C-6).

**Consistency table (REQ-14).**

| Kind | Required forms | Required block state |
|---|---|---|
| `red` | exactly one RED form with `Mode: ordinary`; no GREEN | `atomic-tests: red` (`failed` → `red-not-established`) |
| `pinned` | exactly one RED form with `Mode: characterize`; no GREEN | `atomic-tests: pinned` |
| `green` | exactly one GREEN form; optionally one preceding RED form with `Mode: n-a` | `atomic-execution: complete`, `blocker: none`, and `atomic-tests` `green`, or `n-a` with a `tdd: none — ` note, or absent with a `pre-TDD task, TDD step skipped` note; with `green`, a test-path source of DM-3 (`red`/`pinned` receipt or recorded `test:` commit) must exist |
| `review` | exactly one Check form, optionally followed by one Completion form | `atomic-validation: complete` with `Verdict: DONE`, or `failed` with `Verdict: NEEDS WORK` |

No form at all → `report-form-missing`; any other combination → `report-form-unexpected`.

**Commit rule.** The *commit predicate* holds for a commit when it has exactly one parent, its
parent is the leaf's latest receipted commit or else the attempt's `dispatched.head_revision`,
and its changed paths, as printed by `diff-tree` relative to the
repository top level, equal the message's `stage_paths` each prefixed with `git rev-parse
--show-prefix` of `WORK_DIR`, plus any paths inside the task directory or `AI_DIR`
(bookkeeping allowed by `rules/git-flow.md:157-163`, listed in `bookkeeping_paths`). A path
with status `D` must have digest `null` in the message; for every other path of `stage_paths`
the SHA-256 of the committed blob equals the message digest (bookkeeping paths are not
digest-checked). `receipt --commit` and DM-9 `commit-found` additionally require the commit to
be `HEAD`; the DM-9 commit requirement uses the predicate alone. A `review` event takes no
`--commit`.

**Report canonical form.** LF line endings only, exactly one trailing LF, no line starting with
`ORCHESTRAIL_REPORT_V1 ` or `ORCHESTRAIL_DISPATCH_V1 `; otherwise `report-not-canonical`
(or `report-contains-marker` for a marker line).

### C-5 Helper route in `/spec-run`

**Save procedure.** `## Helper route` contains exactly one fenced block with info string
`sh checkpoint-save`, holding this function (AC-08 extracts and runs it):

```sh
checkpoint_save() {  # checkpoint_save TMP FINAL KEEP_CONFLICT(yes|no); prints the outcome
  if ln "$1" "$2" 2>/dev/null; then rm -f "$1"; echo saved
  elif [ -e "$2" ] && cmp -s "$1" "$2"; then rm -f "$1"; echo duplicate
  elif [ -e "$2" ] && [ "$3" = yes ]; then
    d=$({ sha256sum "$1" 2>/dev/null || shasum -a 256 "$1"; } | cut -c1-12)
    mv "$1" "${2%.md}.conflict-$d.md"; echo conflict
  elif [ -e "$2" ]; then rm -f "$1"; echo conflict
  else rm -f "$1"; echo link-failed; fi
}
```

`KEEP_CONFLICT` is `yes` for reports and `no` for every other record. A report is written to
`<final>.tmp` with the harness file-write tool in canonical form (C-4); helper output is
written as `python3 -I … > <final>.tmp` and saved only when the helper exited 0. The journal
directories are created with `mkdir -p` on the first save.

**Per boundary** (each numbered item a separate Bash call unless stated; a git command never
shares a Bash call with a write of another step, because a same-command write makes the git
rails deny later reads, `.ai/memory/architecture.md:204-205`):

1. Before the spawn, after any spec-14 packet is built and its `context-packet:` entry
   recorded: `attempt …` → save `attempts/<attempt_id>.json` (REQ-09).
2. On the final response: save the report (REQ-10–REQ-12); `compose` → save
   `messages/<event_id>.json`. Outcomes follow C-6.
3. `red`/`pinned`/`green`: commit exactly `stage_paths` (and any bookkeeping paths the
   repository's tracking policy allows) under `git-flow → ## Commits`
   (`workflows/spec-run.md:261-272`), then append the sha to the leaf's `commits:`.
4. Apply `manual_deltas`, if any, by the manual route.
5. `render --emit json` → save `proposals/<event_id>.<proposal_seq>.json`; when its `files` is
   non-empty, `render --emit patch` → save the `.patch` (both renders may share one call).
6. Non-empty patch: `cd <apply_root> && git apply --check <patch> && git apply <patch>`
   (REQ-21). A failed `--check` → repeat step 5 once against current bytes; a second failure →
   stop.
7. `receipt --event E [--commit SHA] [--manual-applied] [--output-handoff-digest H]` → save
   `receipts/<event_id>.json`. Only now is the boundary accepted (REQ-23); report one line
   (REQ-29); continue with the existing flow (resume the same Implementer, build the Validator
   packet and spawn the Validator, pull request, 4.6 compression, which also satisfies
   `request` operations).

Steps 3 and 4 come before rendering so that the receipt's digests include the Orchestrator's
own git-field writes and the manual deltas.

### C-6 Outcome classes

| Class | Outcomes | Orchestrator action |
|---|---|---|
| no-op | exit 1 `attempt-superseded`; save result `duplicate` | Keep the report; no state change |
| fallback (boundary) | exit 1 `report-form-missing`, `attempt-unknown`, `report-not-canonical`, `unsupported-line-endings`, `invalid-utf8` | Manual route for this boundary |
| fallback (facts) | `inspect` exit 1 (`sufficient: false`) | Read the needed files directly for this decision, as the manual route does; no stop |
| fallback (run) | exit 3 (any code); save result `link-failed`; exit 2 `target-outside-repository` | Manual route for the rest of the run, reported once |
| stop | exit 1 `checkpoint-mismatch`, `worktree-changed`, `block-invalid`, `red-not-established`, `report-form-unexpected`, `report-contains-marker`, `delta-truncated`, `delta-invalid`, `event-exists`, `conflict`, `op-not-allowed`, `transition-not-allowed`, `protected-field`, `target-missing`, `not-applied`, `partial`, `diverged`, `commit-mismatch`, `commit-missing`, `manual-unconfirmed`, `proposal-missing`, `journal-record-invalid`; exit 2 `input-too-large`, `file-missing`, `invalid-arguments`, `unknown-command`; save result `conflict`; a second failed `git apply --check` | REQ-24 stop; added to `rules/orchestration.md → ### Conditions that always stop the run` as "a checkpoint outcome classified stop by `contract-checkpoints → ## Stop classes`" |

The `Checkpoint stop codes:` line lists the exit 1 and exit 2 codes of the stop row.

`delta-truncated` follows spec 08's consuming rule first; it stops only when that rule does not
obtain a complete report.

### C-7 Waiting triggers (REQ-02)

While a worker of the current boundary runs, the Orchestrator acts only on: (1) the worker's
final response; (2) the harness reporting the worker finished, failed or unknown without a
final response; (3) a worker message that needs a relay or an answer; (4) an owner message;
(5) a resume. On (2) it runs `reconcile` and follows `await-or-recreate`; it never infers
success from a missing response.

### C-8 Manual route

Today's procedure, with one addition (the rejection rule before DM-5 application, below): `workflows/spec-run.md` Steps 0–8 as delivered before this
spec, including Step 0 reconciliation (`:64-81`), the RED/GREEN commit handoff (`:244-282`),
delta application by the Orchestrator (`:194-198`, `:312-318`) and the structural block check
(`rules/orchestration.md:130-132`). No journal record is written. Structured `delta` blocks
are applied by reading their operations as instructions under DM-5, after spec 08's rejection rule (08 DM-8, "Delta block" rule) has been applied to each received block. A task that switched route
keeps its journal; `reconcile` reports events without receipts, and Step 0 reconciliation
remains the authority for boundaries handled manually.

### C-9 Changed files

| File | Change |
|---|---|
| `scripts/controller-step.py` (new) | The helper; Python 3.11+ standard library only |
| `scripts/check-controller-step.py` (new) | Acceptance suite (C-11) |
| `rules/contract-checkpoints.md`, `rules/contract-delta-operations.md` (new) | C-1 |
| `rules/orchestration.md` | One citation sentence in `## Shared-file discipline`; one bullet in `### Conditions that always stop the run` |
| `workflows/spec-run.md` | `loads:` entry; the nine C-1 anchored lines; the spawn instructions of 4.2 (GREEN batch) and 4.3 gain REQ-50's final-response composition; the sentence "Re-read the plan and recompute the pending dependency order after each delta" (`:195-196`) is prefixed "On the manual route,"; 4.2a's "`target_files:` holds test files only" stays verbatim (a frozen check greps it, `scripts/validate-contracts.sh:1511`) and is followed by "On the helper route the commit takes `stage_paths` from `compose`." Every other sentence existing frozen checks grep stays verbatim |
| `workflows/pae-finalize.md`, `workflows/pav-close.md`, `workflows/pav-propose.md`, `workflows/phase-composite-validation.md` | REQ-36 citation and `loads:` entry |
| `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `scripts/README.md`, `.ai/context/runbook.md` | REQ-46, REQ-47; script row; command for the suite |
| `.gitignore`, `scripts/setup-new-project.sh` (`GITIGNORE_ENTRIES`, `:247-254`) | REQ-37 |
| `.ai/principles/domain.md`, `.ai/adr/` | REQ-48, REQ-38 |

### C-10 Contracts exposed to and consumed from other specs

| Spec | Relationship |
|---|---|
| 05 | Consumed: none required. Exposed: `event_id`, `attempt_id` as plain identifiers; a 05 producer maps them to opaque `sha256:` identifiers with its keyed mapping (`scripts/usage_telemetry_adapter.py:20-24`). No 05 record is written here |
| 08 | Consumed: report forms, `delta` fences and rejection rule, DM-7 path bases, `loads:`. Exposed: the checkpoint message is the "full structured result" on the helper route only (08 Terminology row "Full structured result"); under `/spec-run` the four workflows of REQ-36 return `delta` blocks whose lines are DM-4, 08's rejection rule applies first (helper route: `delta-truncated`; manual route: by the Orchestrator before it applies each block by hand under DM-5); outside `/spec-run` there is no consumer. No evidence format is registered: journal files satisfy `text@1` and are referenced as `task:checkpoints/…` with scope `file` |
| 09 | Consumed: offline suite (REQ-39). Exposed: the journal inside the captured task directory records per-leaf order (`seq`, commits) for `/spec-run` runs; `/phase-pipeline` emissions are unchanged |
| 12 | Exposed: DM-2 `input_handoff_digest` and DM-7 `output_handoff_digest` (REQ-41), the derived-proposal rule (REQ-18) for deltas returned against an older state (12 E-32), `attempt` numbering per leaf and role. A repair of a composite child under 12a REQ-54 and 12 REQ-63 (12 DM-6 stage `repair`) is outside this spec: repair boundaries have no receipt, so no `output_handoff_digest` is recorded for a `repair` handoff (it exists only in 12's handoff file), and a repair Implementer spawned on the helper route is an ordinary further attempt of the leaf. The DM-6 object is not carried: it is built by the root after the checkpoint commit, i.e. after the message it would be inside, and storing it twice would create a second definition |
| 14 | Consumed (spec 14 C-8 row 15 and DM-11): `packet_digest` from the Orchestrator's `context-packet:` notes entry and `task_contract_hash` = `sha256:` + `parts.contract.sha256` of that packet's manifest in `<git-common-dir>/orchestrail-context/packets/` (14 DM-10); `context_receipt` from the worker's `context-receipt:` entry. Adopted as requested by 14: DM-2 holds the packet at dispatch, DM-3 the packet in effect at compose, so a successor packet sent at the RED continuation (14 REQ-42) appears in the `green` message. Packets exist only for Implementers and Validators under `/spec-run`; without one both fields are `null` |
| 16 | Not consumed by 16 (16 C-6, row for 15; 16 A-14): accepted `green` messages and `red`/`pinned` receipts are not offered as fact sources, because REQ-30 forbids passing any Implementer report, checkpoint message, proposal, receipt or journal path to a Validator; the reviewer re-derives test paths, digests and commits from git and its own leaf block. Validator inputs stay `workflows/spec-run.md:284-292` plus 16's reviewer inputs. 15 needs no amendment |
| 17 | Consumed: none; matches 17 C-7 row 15 (OUTPUT lines copied verbatim inside report `Evidence`, no envelope field, no registered 08 evidence format). Report `Evidence:` items referencing 17 artifacts are copied verbatim |
| 18 | Not used: 18 declined DM-2 as its dispatch record (18 C-6, row for 15; 18 A-13), because the attempt record exists only on the helper route and for Implementer and Validator and is written once before the spawn, so it cannot hold a later rejection; 18 keeps per-spawn effort facts in the append-only `## Effort Decisions` section of the task `state.md`. This spec adds no effort field and no schema version for one |
| 19 | Exposed: `checkpoint_save` (C-5), canonical JSON and the note-entry rule, attempt lineage (`supersedes`), `attempt-superseded`, duplicate handling by `event_id`; limits stay 19's. Repair resume is governed by 19's `status` alone: repair boundaries are not checkpoint kinds, so `compose`, `render` and `receipt` are not used for them; `reconcile` may report a repair Implementer's due `green` event as `manual-route` with `none` (DM-9 state row 6: no message, canonical completion predicate holds from the leaf's original commits and a `done` plan row), and its entries for repair attempts are ignored. 19's Orchestrator rewrites a `blocked` plan row as `done` by hand before saving the repair Implementer's attempt record and the spawn (19 REQ-35) and again before the recheck (19 C-5 step 12); DM-5 has no `blocked` → `done` transition for a leaf plan row, and this helper does not perform or verify that write. No change to the helper for ordinary leaves |
| 20 | Exposed: `summary` per-leaf attempt counts (DM-10 `leaves[<leaf_id>].attempts`), which 20 reads as the `attempts` of its overhead report; 20 does not use the event counts |
| 07 | None: the helper does not use `scripts/state-tool.py`; 07's `state_receipts:` field is preserved as an unknown field |

### C-11 Acceptance suite

`python3 -I scripts/check-controller-step.py` builds disposable git repositories in a temporary
directory (tracked and ignored `.ai/` variants, real `state.md`/`plan.md` shapes copied from
`.ai/tasks/completed/task-06-harness-git-rails/`), a scripted spec-08
`rules/contract-reports.md` and synthetic worker reports, runs the helper as a subprocess with
`ORCHESTRAIL_HOME` pointing at a temporary checkout copy, and exits 0 only when every AC case
passes. It reads, never edits, the repository's rules and workflows for the contract cases.

## Non-Functional Requirements

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-01 | Determinism | Byte-identical stdout for identical inputs (REQ-44) | AC-02 |
| NFR-02 | Non-interference | No change to bytes, modes or mtimes of any fixture file, `.git/index`, refs or config (REQ-03) | AC-02 |
| NFR-03 | Portability | Python 3.11+ standard library; Bash, `git`, `ln`, `cmp`, `sha256sum` or `shasum` for the save procedure; no network | AC-16, review of imports |
| NFR-04 | Bounded input | 1,048,576 bytes per read file (REQ-43), matching `rules/run-log.md:455` | AC-16 |
| NFR-05 | Performance | N/A — no owner target exists and none is invented; measured effects belong to spec 09 (REQ-47) | — |
| NFR-06 | Privacy | stderr and summaries carry no file contents; journal files stay in the ignored task directory | AC-05, AC-14 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | Requirement |
|---|---|---|
| Worker response contains the run-log REPORT marker | Saved report omits marker lines; a saved report still containing one → `report-contains-marker` | REQ-10 |
| Same report delivered twice | `duplicate`; no new record | REQ-11 |
| Different report for the same event | Conflict file kept; stop | REQ-12 |
| Late report from a recreated worker's predecessor | `attempt-superseded`; no change | REQ-13 |
| Implementer did not pause (RED and GREEN forms in one return) | `report-form-unexpected`; stop | REQ-14, REQ-24 |
| `atomic-tests: failed` at RED | `red-not-established`; existing stop (`rules/orchestration.md:183`) | REQ-14 |
| Worker reports a blocker | Block state contradicts the kind → `checkpoint-mismatch`; stop (already a stop, `rules/orchestration.md:187`) | REQ-14 |
| `n-a` leaf, pre-TDD block | No red event; `green` accepted without receipt | REQ-16 |
| RED test file changed during GREEN without amendment note | `frozen_tests: changed-unrecorded` recorded; no stop; the Validator's existing test-set audit decides (`rules/orchestration.md:89-91`) | REQ-15 |
| Worker edited a file not in `target_files:` | Listed in `unlisted_changes`; not staged; no stop | REQ-17 |
| `target_files:` seeded from Scope lists files not yet changed at RED | Not dirty → not in `test_paths`/`stage_paths` | REQ-17 |
| RED test amended during GREEN with a `tdd: test amended — ` note | Dirty → in `changed_paths` and staged with the implementation; `frozen_tests: amended` | REQ-15, REQ-17 |
| Implementation deletes a file | Staged by `git add <path>`; commit rule expects status `D` and digest `null` | REQ-17, REQ-22 |
| `WORK_DIR` is a subdirectory of the repository | `stage_paths` relative to `WORK_DIR`; commit rule prefixes them with `--show-prefix` | REQ-22 |
| Tracked `.ai/` bookkeeping included in a commit | Allowed as `bookkeeping_paths`; patches applied after the commit leave tracked bookkeeping dirty, as the Orchestrator's own git-field writes already do; Step 0 item 3 handles it on resume | REQ-22, REQ-25 |
| Resume with tracked uncommitted implementation files | Step 0 item 3 stops as today; its report names `reconcile`'s next actions | REQ-25 |
| Interruption while applying manual deltas | State `committed`, next action `manual-then-render`; the manual route checks each target before changing it | REQ-20, REQ-26 |
| Boundary handled by the manual route, helper available on a later resume | `manual-route` state; `none` when canonical completion holds | REQ-26 |
| Successor spec-14 packet at the RED continuation | `green` message carries the successor's digests; the attempt record keeps the dispatch packet | REQ-51 |
| Worker response with CRLF endings or two trailing newlines | Saved in canonical form; a non-canonical file → `report-not-canonical` fallback | REQ-10 |
| Orchestrator wrote git fields after compose | Proposal `derived: true`; applies normally | REQ-18 |
| Human edited the same plan cell | `conflict`; stop | REQ-04, REQ-24 |
| Worker proposes a write to another leaf's block or to `commits:` | `protected-field`; stop | REQ-19 |
| Free-text delta | `manual_deltas`; manual application after the commit, before `render`; receipt needs `--manual-applied` | REQ-20, REQ-22 |
| `delta` block truncated or with `…` line | 08 consuming rule, else `delta-truncated` stop | REQ-24 |
| CRLF or non-UTF-8 target | Fallback for this boundary | C-6 |
| Task directory outside the repository (umbrella `.ai/`) | Exit 2 `target-outside-repository` at `attempt`; manual route for the run | C-2, REQ-08 |
| Crash between patch and receipt | `applied-unreceipted` → `receipt` | REQ-26 |
| Crash between two files of one patch | `partially-applied` → render remainder | REQ-26 |
| Crash after the test commit, before `commits:` and receipt | `commit-found` → record commit, no second commit | REQ-27 |
| Branch reset by a human after a receipt | `receipt-contradicted`; stop | REQ-26 |
| Worker gone without a response | `dispatched` → recreate as a new attempt; never success | C-7, REQ-26 |
| `git apply --check` fails twice | Stop | C-5 |
| Filesystem without hard links | `link-failed` → manual route for the run | C-5, C-6 |
| Python < 3.11, git missing, 08 field lines missing | Exit 3 → manual route | REQ-34, REQ-45 |
| `ORCHESTRAIL_CONTROLLER_STEP=off` | Manual route; no journal writes | REQ-33 |
| Oversized report or record | Exit 2 `input-too-large`; Orchestrator stops at that boundary | REQ-43 |
| Two Orchestrators on one task | Not supported; write-once saves surface `conflict`/`event-exists`, which stop; no lock | Out of Scope |
| `--dry-run` | No journal write; `inspect` may run | REQ-42 |
| Empty `delta` block | `manual_deltas` with `delta-empty`; nothing to apply | REQ-20 |
| Composite leaf whose parent is unknown | Composite operations `rejected` (`op-not-allowed`) | REQ-19 |
| Unknown plan dependency or cycle | `inspect` obstacle; existing `/pe-execute` stop semantics unchanged | REQ-06 |
| Concurrency inside one run | Not applicable: one Orchestrator applies sequentially (`rules/orchestration.md:10-14`) | — |
| Authorization | Not applicable beyond git rails: the helper runs read-only git outside the Bash hook; mutations stay Orchestrator Bash calls under the hook | REQ-03, REQ-21 |

## Acceptance Criteria

All criteria are checked by `python3 -I scripts/check-controller-step.py` (C-11) unless stated.
Each is written first and observed failing before implementation (G6).

- **AC-01** (REQ-01, REQ-09, REQ-10, REQ-11, REQ-16, REQ-23, REQ-50) — Given a fixture task
  whose leaves have `target_files:` seeded from Scope (planned implementation paths present but
  unchanged at RED): an ordinary leaf (red → green → review), a characterization leaf (pinned →
  green → review), an `n-a` leaf and a pre-TDD leaf (green → review each), with worker
  responses shaped as REQ-50 requires (GREEN responses: GREEN form, finalize text, `delta`
  blocks; validation responses: Check form, Completion form, `delta` blocks), When the suite
  drives `attempt`, report saving, `compose`, scripted commits of `stage_paths`, `render`, patch
  application and `receipt` for every boundary and then re-saves every report a second time,
  Then every `red`/`pinned` message's `stage_paths` lists only the test files written, every
  `compose` exits 0, and `messages/` contains exactly the
  ten expected event files, no `red` or `pinned` event exists for the `n-a` and pre-TDD leaves,
  receipt `seq` values per leaf are increasing in the order test boundary < `green` < `review`,
  every message has all DM-3 keys, and the repeated saves report `duplicate` and add no file.
- **AC-02** (REQ-03, REQ-06, REQ-44) — Given the AC-01 fixture at any point, When each
  subcommand runs twice with identical inputs, Then the two stdouts are byte-identical, every
  fixture file (including `.git/index`, refs and config) keeps its bytes, mode and mtime, a
  recording `PATH` shows only `git` executed; and given `plan.md` made unreadable, `inspect`
  exits 1 with the `plan` read `error` and every other read `ok`.
- **AC-03** (REQ-04, REQ-18, REQ-19) — Given messages whose operations meet, in turn, a changed
  `Status` cell, another leaf's block, a disallowed transition, a git field, an operation not in
  DM-5 and a message journal record with a corrupted `payload_digest`, When `render` runs, Then
  it exits 1 with `conflict`, `protected-field`, `transition-not-allowed`, `protected-field`,
  `op-not-allowed` and `journal-record-invalid` respectively and every file is unchanged; given
  a valid message, the applied patch changes only the targeted lines (every other byte equal);
  given the same message rendered again after application, every operation is
  `already-applied` and the patch is empty; given the state digest changed by an unrelated
  `commits:` edit, the proposal has `derived: true` and a different `proposal_id`; given a
  `review` message of a composite's last child carrying `block-field integration-validation
  in-progress → complete` followed by `plan-status` composite `done → reviewed`, both are
  `apply`, and the D8 sequence `integration-validation complete → not-started` with composite
  `reviewed → in-progress` is also `apply`; given an operation with `from` equal to `to` and to
  the current value, it is `already-applied` and contributes no file change, including a
  `review` `block-field` composite `blocker` `none → none` and a `green` `plan-status` composite
  `reviewed → reviewed`.
- **AC-04** (REQ-05, REQ-25, REQ-26, REQ-27) — Given the `green` boundary of a composite child,
  handled by a recreated Implementer (attempt 2) after attempt 1's `red` receipt, whose message
  carries a `plan-status` and a `block-field` operation (two target files) and one
  free-text `delta` block, interrupted after each of: attempt saved, report saved, message saved,
  implementation commit created, commit appended to `commits:`, proposal saved, `plan.md` alone
  patched, both files patched, receipt saved, When `reconcile` runs, Then the states are
  `dispatched` (`event_id` `null`, `expected` `green` because a `red` receipt exists),
  `reported`, `received`, `commit-found`, `committed` (next action `manual-then-render`),
  `proposed`, `partially-applied`, `applied-unreceipted` and `receipted`; given a `red` event
  interrupted after its commit was appended to `commits:` and before `render`, the state is
  `committed` with `render-and-apply`, and following it yields a proposal with empty `files`
  and a receipt; following each
  `next_action` to the end (manual deltas applied by a scripted step) yields exactly one
  implementation commit and final `state.md`/`plan.md` bytes identical to the uninterrupted
  run; given the later `review` receipt of the same leaf, the `green` event stays `receipted`;
  given a receipt whose commit was reset away, the state is `receipt-contradicted`; given no
  journal, the output is the DM-9 absent document.
- **AC-05** (REQ-07, REQ-33, REQ-46, REQ-47) — Given the completed AC-01 journal, When `summary`
  runs, Then every DM-10 count equals the count of the corresponding records and the output has
  no key containing `token`, `cost`, `duration`, `request`, `tool` or `saving`; and the delivered
  `docs/USAGE.md` contains a section naming `ORCHESTRAIL_CONTROLLER_STEP=off`, the journal path,
  the resume command and the sentence that no saving has been measured.
- **AC-06** (REQ-02, REQ-08, REQ-23, REQ-24, REQ-25, REQ-28, REQ-29, REQ-30, REQ-33, REQ-34,
  REQ-42, REQ-50) — Given the delivered repository, When the suite reads `workflows/spec-run.md`,
  `rules/contract-checkpoints.md`, `rules/contract-delta-operations.md` and
  `rules/orchestration.md`, Then each C-1 anchored line occurs exactly once in its named file,
  `rules/contract-checkpoints.md` has exactly the four C-1 sections and one `sh
  checkpoint-save` block, `spec-run.md` declares `rules/contract-checkpoints.md` in `loads:` and
  contains "On the manual route, Re-read the plan" in place of the unqualified sentence, and
  `### Conditions that always stop the run` contains the C-6 bullet; removing or altering any
  one of these lines in a temporary copy makes the suite fail.
- **AC-07** (REQ-09, REQ-13) — Given two `attempt` records for one leaf and role, When `compose`
  runs for the first, Then it exits 1 with `attempt-superseded`; the second record has
  `attempt: 2` and `supersedes` naming the first.
- **AC-08** (REQ-10, REQ-11, REQ-12) — Given the save procedure extracted from
  `rules/contract-checkpoints.md`, When it saves a report to a free name, to a name with equal
  bytes, and to a name with different bytes, Then it prints `saved`, `duplicate` and `conflict`,
  and the conflict file is named with the first 12 hex digits of the new report's digest; with
  `ln` replaced by a failing stub it prints `link-failed`.
- **AC-09** (REQ-14, REQ-15, REQ-17) — Given each row of the C-4 consistency table violated in
  turn, `compose` exits 1 with `checkpoint-mismatch` (or `red-not-established` for `failed`);
  given a RED test changed without, then with, a new `tdd: test amended — ` note, `frozen_tests`
  is `changed-unrecorded`, then `amended`, and the amended test path is in `changed_paths` and
  `stage_paths`; given an extra modified source file outside `target_files:`, it appears in
  `unlisted_changes` and not in `stage_paths`; given a `target_files:` entry deleted during
  GREEN, it is in `stage_paths` with `sha256: null`; given a `green` report without a RED
  receipt but with a recorded `test:` commit, `frozen_tests` is `unknown` and `test_paths` are
  that commit's paths; given a report with CRLF endings, `compose` exits 1 with
  `report-not-canonical`; given the amendment recorded as a continuation line under `notes:`,
  and separately as a `; `-joined entry on the `notes:` line, `frozen_tests` is `amended` in both.
- **AC-10** (REQ-20, REQ-36) — Given a report with one structured and one free-text `delta`
  block, `compose` puts the second into `manual_deltas` with `delta-unstructured`; and the four
  workflows of REQ-36 each cite `` `contract-delta-operations → ## Delta operations` `` and
  declare it in `loads:`.
- **AC-11** (REQ-21, REQ-22) — Given a rendered patch, When the suite runs `git apply --check` and
  `git apply` from `apply_root` against an ignored untracked `.ai/` and against a tracked one,
  Then both succeed and `receipt` prints a receipt; given one target edited after application,
  `receipt` exits 1 with `diverged`; given nothing applied, `not-applied`; given one of two
  files applied, `partial`; given a commit containing an extra path outside the task directory
  and `AI_DIR`, `commit-mismatch`; given a commit that also contains the tracked task
  `state.md`, a receipt listing it in `bookkeeping_paths`; given `WORK_DIR` a subdirectory of
  the repository, a commit of the `stage_paths` passes; given a deletion, the commit passes with
  status `D`; given a `green` event without `--commit`, `commit-missing`; given manual deltas
  and no `--manual-applied`, `manual-unconfirmed`.
- **AC-12** (REQ-31, REQ-35, REQ-39) — Given the delivered tree, When `bash
  scripts/validate-contracts.sh` and `python3 -I tests/golden-runs.py` (offline) run, Then both
  finish with zero failures; `tests/fixtures/validator-runtime/oracle.py` passes with no new
  `inventory-amendment.json` entry; `scripts/log-step.sh contract` prints the same bytes as at
  the parent revision; and no file under `tests/` is added or changed.
- **AC-13** (REQ-32, REQ-49) — Given the delivered rules, `version` prints exactly the C-1
  document and each registry equals its anchored line split by the C-1 rule; given a temporary copy with one anchored value changed, the suite fails naming that
  line; spec 08's `measure-context.sh check` reports no `rule-size-exceeded` for the two new rules,
  and both declare `load: on-demand`.
- **AC-14** (REQ-37, REQ-38, REQ-40, REQ-48) — Given the delivered tree, `.gitignore` contains
  `/.ai/tasks/*/*/checkpoints/` and `git check-ignore` matches a file in a fixture task's
  journal; `GITIGNORE_ENTRIES` in `scripts/setup-new-project.sh` and the entry list in
  `docs/USAGE.md` contain `.ai/tasks/*/*/checkpoints/`; `.ai/adr/index.md` lists an Accepted ADR that names the journal, the message, the
  delta operations and the REQ-24 stop, and lists every 13a proposal owned by 15 as implemented
  or declined with a reason; `.ai/principles/domain.md` defines the six REQ-48 terms.
- **AC-15** (REQ-41) — Given `attempt --input-handoff-digest H1` and `receipt
  --output-handoff-digest H2`, the attempt record, message and receipt carry `H1`/`H1`/`H2`, and
  no journal file contains a key of spec 12's DM-6 object other than these digests.
- **AC-16** (REQ-43, REQ-45) — Given a 1,048,577-byte report, `compose` exits 2 with
  `input-too-large`; given `PATH` without `git`, `version` exits 3 with `git-unavailable`; given
  the 08 field lines removed from the temporary checkout, `compose` exits 3 with
  `report-contract-unavailable`; given the helper module loaded by path with `importlib` (the
  only in-process seam) and its version-check function `require_python((3, 10, 0))` called, it
  raises the `python-unsupported` exit (status 3) while `(3, 11, 0)` passes.
- **AC-17** (REQ-06, REQ-28) — Given a plan with a composite, its children, a `—` dependency, an
  unknown dependency and a cycle, `inspect` reports `dependencies_satisfied` per
  `workflows/pe-execute.md:32-33`, `type: leaf` for rows without the column, and the obstacles
  `dependency-unknown` and `dependency-cycle`; with `--leaf` and a checked-out branch differing
  from `branch:`, `branch-mismatch` is listed; given `plan.md` unreadable, `plan` has
  `error_code: unreadable` and `sufficient` is `false`.
- **AC-18** (REQ-08, REQ-26) — Given a task whose `red` boundary was handled on the manual
  route (report saved, `compose` exited 1 `report-form-missing`, test commit recorded in
  `commits:`, `atomic-tests: red`) and whose `green` boundary has an attempt record only,
  When `reconcile` runs, Then the `red` event is `manual-route` with `next_action: none` and the
  next entry is `dispatched` with `expected: green`; given the same without the test commit,
  `manual-route` with `next_action: manual` (row 6, `compose` would exit with
  `report-form-missing`).
- **AC-19** (REQ-51) — Given a leaf whose notes hold `context-packet: implementer sha256:P1` and
  then `context-packet: implementer successor sha256:P2 — source-changed` with packet files P1
  and P2 in the store, When `attempt` runs before the second entry and `compose` builds the
  `green` message after it, Then the attempt record carries P1 and P1's contract hash and the
  message carries P2 and P2's `sha256:` + `parts.contract.sha256`; given `context-packet:
  implementer none — disabled`, both fields are `null`; given an entry whose packet file is
  absent, both fields are `null`.

## Traceability

| Requirement | Acceptance criteria |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-06 |
| REQ-03 | AC-02 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-06 | AC-02, AC-17 |
| REQ-07 | AC-05 |
| REQ-08 | AC-06, AC-18 |
| REQ-09 | AC-01, AC-07 |
| REQ-10 | AC-01, AC-08, AC-09 |
| REQ-11 | AC-01, AC-08 |
| REQ-12 | AC-08 |
| REQ-13 | AC-07 |
| REQ-14 | AC-09 |
| REQ-15 | AC-09 |
| REQ-16 | AC-01 |
| REQ-17 | AC-09 |
| REQ-18 | AC-03 |
| REQ-19 | AC-03 |
| REQ-20 | AC-04, AC-10, AC-11 |
| REQ-21 | AC-11 |
| REQ-22 | AC-11 |
| REQ-23 | AC-01, AC-06 |
| REQ-24 | AC-06 |
| REQ-25 | AC-04, AC-06 |
| REQ-26 | AC-04, AC-18 |
| REQ-27 | AC-04 |
| REQ-28 | AC-06, AC-17 |
| REQ-29 | AC-06 |
| REQ-30 | AC-06 |
| REQ-31 | AC-12 |
| REQ-32 | AC-13 |
| REQ-33 | AC-05, AC-06 |
| REQ-34 | AC-06 |
| REQ-35 | AC-12 |
| REQ-36 | AC-10 |
| REQ-37 | AC-14 |
| REQ-38 | AC-14 |
| REQ-39 | AC-12 |
| REQ-40 | AC-14 |
| REQ-41 | AC-15 |
| REQ-42 | AC-06 |
| REQ-43 | AC-16 |
| REQ-44 | AC-02 |
| REQ-45 | AC-16 |
| REQ-46 | AC-05 |
| REQ-47 | AC-05 |
| REQ-48 | AC-14 |
| REQ-49 | AC-13 |
| REQ-50 | AC-01, AC-06 |
| REQ-51 | AC-19 |

Shared gates: G1 — REQ-07, REQ-31, C-10 (05); G2 — REQ-47; G3 — REQ-14–REQ-16, REQ-23, REQ-30,
REQ-35; G4 — REQ-08, REQ-16, REQ-33, REQ-34; G5 — REQ-03, REQ-05, REQ-19; G6 — AC-01–AC-19,
REQ-35, REQ-39; G7 — REQ-33, REQ-46, C-8; G8 — REQ-47, NFR-05.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| The Orchestrator model skips or reorders C-5 steps | Unverified acceptance | Medium | REQ-23 gate, `reconcile` on resume, contract checks (AC-06) |
| More tool calls per boundary than today | Overhead may rise | Medium | No saving claimed (REQ-47); spec 09 measures |
| Spec 08's delivered forms differ from its spec text | `compose` falls back | Medium | Forms read from the delivered anchored lines at run time; fallback is the manual route |
| `git apply` behaviour differs across git versions | Patch rejected | Low | AC-11 on the installed git; failure is a stop, never a silent change |
| Frozen validator checks grep sentences in edited workflows | Validator failures | Medium | REQ-35, AC-12; additive edits only |
| Journals grow without cleanup | Disk use | Low | Small text files; deletion only with the task directory |
| A second Orchestrator on the same task | Interleaved records | Low | Write-once saves surface conflicts as stops; documented as unsupported |

## Assumptions

- A-01 | Language and identifiers | Resolved: English refinement in place; REQ-01–REQ-08 and AC-01–AC-05 keep their ids and subjects; remainders split into new ids | Source: `/spec-draft` Step 5 id rule; owner authorization | Reversible: yes
- A-02 | File names | Resolved: today's names in text; 13's map at implementation; new rules named `contract-checkpoints` and `contract-delta-operations`, `load: on-demand` | Source: `.ai/specs/README.md` → "Dependency order" (13 precedes 09 precedes 15); spec 13 DM-10, DM-11 and Notes → Files and sections created after this spec | Reversible: yes
- A-03 | Helper language and name | Resolved: one Python 3.11+ standard-library file `scripts/controller-step.py`, run with `python3 -I` without a Bash launcher; the previous `.sh` name becomes `.py`. Consequence: the entry file as a whole uses only syntax older Python 3 interpreters parse and loads 3.11-only code after the check, so that REQ-45's version check, not a syntax error, decides (spec 20 A-26: entry module plus path-loaded engine) | Source: ADR-0021 Decision 3 (`scripts/`); `scripts/model-catalog.py` pattern; spec 13 Scope item 3 (standard-library Python 3.11+ engine precedent) | Reversible: yes
- A-04 | Who writes the journal | Resolved: the Orchestrator through Bash redirection and the save procedure; the helper writes nothing | Source: previous revision §2 helper row and AC-02 ("files unchanged") | Reversible: yes
- A-05 | Journal location | Resolved: `<task>/checkpoints/`, ignored in this repository and in the consumer entries of project setup | Source: previous revision §6 ("durable in the task's local data"); spec 07 REQ-26 ignore precedent | Reversible: yes
- A-06 | Who builds the message | Resolved: the helper, run by the Orchestrator, from the worker's spec-08 report and observed facts; worker rights unchanged | Source: previous revision §2 ("new messages do not extend worker rights"); spec 08 Terminology "Full structured result" | Reversible: yes
- A-07 | Event identity | Resolved: deterministic readable `event_id` from attempt and kind; attempts numbered per leaf and role | Source: previous revision §4 (`event_id` stable across redelivery); best practice | Reversible: yes
- A-08 | Acceptance-criterion identity | Resolved: verbatim report items plus `description_sha256` | Source: `templates/subtask-description.md:32-37` (no ids) | Reversible: yes
- A-09 | Checkpoint kinds | Resolved: `red`, `pinned`, `green`, `review`; `close` folded into `review` | Source: `workflows/spec-run.md:291-292` (one Validator return covers check to close) | Reversible: yes
- A-10 | Delta operation set | Resolved: five operations; architecture, D8, children, Fix-Tasks and memory entries stay free text | Source: `rules/orchestration.md:110-117`; smallest reversible set | Reversible: yes
- A-11 | Application tool | Resolved: `git apply --check` then `git apply` from the top level | Source: previous revision §6 step 6 (existing tool with expected-source check); local experiment with git 2.53.0 confirmed application to ignored untracked files | Reversible: yes
- A-12 | Staleness | Resolved: operation-level preconditions decide; file-digest change alone yields a derived proposal | Source: previous revision §6; spec 12 E-32 (derived proposal when a delta was composed against an older state) | Reversible: yes
- A-13 | New stop | Resolved: one declared stop class (C-6) added to the orchestration stop list | Source: P5 (`.ai/principles/architecture.md:39-44`); previous revision §6 steps 2–3 | Reversible: yes
- A-14 | Telemetry | Resolved: no run-log change, no 05 producer, counts from the journal only | Source: `rules/run-log.md:584-585`; `scripts/usage_telemetry_adapter.py:208-214`; P9 | Reversible: yes
- A-15 | Spec 12 handoffs | Resolved: digests only | Source: spec 12 DM-6 Handoff, REQ-22 | Reversible: yes
- A-16 | Evidence format | Resolved: none registered; `text@1` suffices | Source: 08 DM-7 (neither 15 nor 17 registers a format) | Reversible: yes
- A-17 | Input bound | Resolved: 1,048,576 bytes | Source: `rules/run-log.md:455` | Reversible: yes
- A-18 | Timeouts | Resolved: none of its own; harness command timeout applies; the helper is safe to rerun | Source: ADR-0020 (timeouts are watchdogs, not budgets) | Reversible: yes
- A-19 | Disable switch | Resolved: `ORCHESTRAIL_CONTROLLER_STEP=off`; any value other than unset, empty or `on` disables (spec 14 REQ-32 rule); only the Orchestrator reads it | Source: `ORCHESTRAIL_*` variable convention (`.ai/principles/coding.md:66-67`) | Reversible: yes
- A-20 | Test placement | Resolved: standalone `scripts/check-controller-step.py` | Source: ADR-0019 Decision 3 (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`) | Reversible: yes
- A-21 | Spec 07 | Resolved: not used; its grammar cited as the parsing definition | Source: ADR-0021 Decision 1 consequences; gate G5 | Reversible: yes
- A-22 | Spec 14 fields | Resolved: read from the notes entries and packet manifest, never passed by hand; nullable | Source: spec 14 C-8 row 15 ("15's checkpoint message carries them"), DM-11, REQ-42 (successor) | Reversible: yes
- A-23 | Validator inputs | Resolved: unchanged until 16 | Source: `workflows/spec-run.md:284-292`; previous revision §8 | Reversible: yes
- A-24 | Other orchestrators | Resolved: unchanged | Source: spec 09 Q-05 (separate run-log change recommended) | Reversible: yes
- A-25 | Gates | Resolved: G1–G8 | Source: `.ai/specs/README.md` → "Shared acceptance gates"; previous revision §10 | Reversible: no
- A-26 | Line endings | Resolved: LF targets only; CR → fallback | Source: `.ai/specs/07-state-tool.md` grammar ("Line endings are LF") | Reversible: yes
- A-27 | Waiting | Resolved: trigger list without a numeric polling interval | Source: previous revision §8; no owner target | Reversible: yes
- A-28 | Unlisted changes | Resolved: reported, not staged, no stop | Source: `workflows/spec-run.md:261-263` (exact paths only); P5 (no undeclared new stop) | Reversible: yes
- A-29 | Frozen tests | Resolved: recorded, no stop | Source: `rules/orchestration.md:89-91` (Validator audits the test set) | Reversible: yes
- A-30 | Write-once mechanism | Resolved: hard link with `cmp` comparison | Source: best practice (atomic create without overwrite) | Reversible: yes
- A-31 | Duplicate definition | Resolved: identical report bytes | Source: previous revision §6 step 2 | Reversible: yes
- A-32 | Ordering field | Resolved: `seq` from record count; no timestamps | Source: P9 (no model-written time) | Reversible: yes
- A-33 | Plan cell rewrite | Resolved: width-preserving padding | Source: `rules/workflow-reference.md:190-199` table shape; best practice | Reversible: yes
- A-34 | 13a proposals | Resolved: REQ-40 | Source: spec 13a REQ-02 (owner 15); spec 08 precedent (08 Scope item 9) | Reversible: yes
- A-35 | Golden regression | Resolved: REQ-39 | Source: spec 08 REQ-26 precedent; `.ai/specs/README.md` → "Dependency order" (09 prerequisite) | Reversible: yes
- A-36 | Dry run | Resolved: no journal write | Source: `workflows/spec-run.md:10-11` | Reversible: yes
- A-37 | Forms per kind | Resolved: C-4 table; no form → fallback | Source: 08 DM-8 "Report forms"; `workflows/spec-run.md:264-269`, `:291-292` | Reversible: yes
- A-38 | Repository identity | Resolved: path digests of git common dir and top level | Source: previous revision §4 (`repository_id`, `worktree_id`) | Reversible: yes
- A-39 | Staging path form | Resolved: plain paths relative to `WORK_DIR` | Source: `workflows/spec-run.md:261-263` | Reversible: yes
- A-40 | Task outside repository | Resolved: exit 2, manual route | Source: `rules/git-flow.md:35-36` (single repository); smallest choice | Reversible: yes
- A-41 | Test-path source at RED | Resolved: dirty `target_files:` entries, not all entries | Source: `workflows/pd-decompose.md:162` (seeded from Scope); `workflows/pae-tests.md:207`, `:222` (appended) | Reversible: yes
- A-42 | Final response shape | Resolved: every report form of the batch in step order, then every `delta` block (REQ-50) | Source: 08 DM-8, delta paragraph (finalize deltas outside the forms); `workflows/spec-run.md:264-269`, `:291-292` | Reversible: yes
- A-43 | Manual deltas | Resolved: applied after the commit and before `render`, confirmed by `--manual-applied` | Source: previous revision §7 (no step may be lost on resume); smallest change keeping one receipt | Reversible: yes
- A-44 | Resume gate | Resolved: Step 0 item 3's clean-tree stop is kept; `reconcile` runs read-only first and its next actions go into the stop report | Source: `workflows/spec-run.md:64-69`; P5 (no new silent exception) | Reversible: yes
- A-45 | `AI_DIR` | Resolved: `WORK_DIR/.ai` | Source: `rules/phase-atomic-execution.md:18-19` | Reversible: yes
- A-46 | Tracked bookkeeping in commits | Resolved: allowed in the commit rule as `bookkeeping_paths`; commit policy unchanged | Source: `rules/git-flow.md:155-163` | Reversible: yes
- A-47 | Report bytes | Resolved: canonical form (LF, one trailing LF, markers removed) written with the file-write tool | Source: best practice (byte-stable duplicate detection) | Reversible: yes
- A-48 | Manual-route boundaries in the journal | Resolved: no extra record; `reconcile` reads canonical completion predicates | Source: P2 (state on disk is authoritative, `.ai/principles/architecture.md:18-22`) | Reversible: yes
- A-49 | `inspect` failure | Resolved: facts fallback to direct reads, no stop | Source: previous revision §5 ("absence leads to manual execution of the same checks") | Reversible: yes
- A-50 | Version test seam | Resolved: `require_python(version_info)` called in-process after loading the module by path | Source: spec 14 C-9 precedent | Reversible: yes
- A-51 | Peer reconciliation 2026-11-14 | Resolved: C-10 states what each final peer spec consumes; repair resume stays 19's `status` and the helper is unchanged for ordinary leaves; no repair receipt and no `output_handoff_digest` for a 12 `repair` handoff | Source: 19 C-10 row 15, A-18; 12a REQ-54, 12 REQ-63, 12 DM-6; 18 C-6, A-13; 16 C-6, A-14; 17 C-7; 20 DM-9 | Reversible: yes

## Decisions

N/A — auto mode; no choice overrides a principle, accepted ADR or shipped invariant. The added
stop (A-13) extends the declared stop list as P5 requires and is recorded by REQ-38.

## Clarifications

### Session 2026-11-14

- No question was put to the owner (auto mode under standing authorization). Gaps are resolved
  in A-01–A-51.

## Open Questions

- Q-01 | non-blocker | Should this repository track checkpoint journals as knowledge under
  ADR-0012 instead of ignoring them (REQ-37)? Impact: evidence retention versus repository
  noise. Recommended: ignore (A-05) until a consumer needs them.
- Q-02 | non-blocker | Should `/phase-pipeline` adopt `inspect` for its re-reads? Impact: possible
  context reduction in single-session runs. Recommended: a follow-up after spec 09 measures the
  `/spec-run` route.
- Q-03 | withdrawn | Spec 14's final names were confirmed by its refined text (A-22).

## Notes

### Name mapping (spec 13)

| Today | After 13 |
|---|---|
| `rules/orchestration.md` | `rules/contract-orchestration.md` |
| `rules/workflow-globals.md` | `rules/contract-phases.md` |
| `rules/workflow-reference.md` | `rules/contract-state-files.md` |
| `rules/git-flow.md`, `rules/run-log.md`, `rules/tdd.md` | `rules/contract-git-flow.md`, `rules/contract-run-log.md`, `rules/contract-tdd.md` |
| `pae-finalize`, `pav-close`, `pav-propose`, `phase-composite-validation` | 13's workflow map governs |
| `rules/contract-checkpoints.md`, `rules/contract-delta-operations.md` | Created by this spec after 13: named by 13's rule for later files (Notes "Files and sections created after this spec"), `load: on-demand`, no `docs/name-map.json` row |

`workflows/spec-run.md` keeps its name. Every edit of this spec to an existing file is stated as
a section, sentence or `loads:` entry of that file, so an implementer applies it to the file's
successor after 13's renames (13's old-prefix translation: `pae-` → `atomic-execution-`,
`pav-` → `atomic-validation-`, `phase-<x>` → `<x>`), citing `<target> → ## <heading>`.

### Implementation hints (nonbinding)

- Hint: order of work — (1) contract rules and anchored lines with failing drift cases; (2)
  `inspect` and identifiers; (3) `attempt`/`compose` with the C-4 parser; (4) DM-4/DM-5 and
  `render`; (5) `receipt`, `reconcile`, `summary`; (6) workflow edits, docs, ignore rule, ADR.
- Hint: keep parsing, policy, rendering and verification in separate functions testable without
  the command line.
- Hint: fixtures can reuse the disposable-repository pattern of `tests/git-rails.sh` without
  adding files under `tests/`.

### Rejected alternatives

- Workers write their reports or messages to files and return a pointer — rejected: extends
  worker rights (previous revision §2) and moves spec 08's report out of the response.
- Helper applies patches or writes the journal — rejected: previous revision §2 and AC-02.
- Carrying the DM-6 handoff object inside the message — rejected (C-10, 12 row).
- Generic text-replace operations on `state.md` — rejected: protected fields could not be
  checked reliably.
- Using spec 07's state tool for application — rejected: 07 is optional and unwired (ADR-0021).
- Letting `reconcile` bypass Step 0's clean-tree stop — rejected: it would be an undeclared
  exception to an existing stop (A-44).
- A separate journal record for manually handled boundaries — rejected: canonical state already
  shows completion (A-48).

### Follow-ups outside this spec (not edited here)

- Spec 12: done by its 2026-11-14 reconciliation (DM-6 note cites REQ-41; E-32 cites REQ-18).
- Spec 08: done by its 2026-11-14 reconciliation (Terminology row "Full structured result" cites
  DM-3 and DM-4; DM-8 delta paragraph cites REQ-36, REQ-50, REQ-08 and DM-5).
- Specs 16, 17, 18, 19, 20: none; their contract rows agree with this spec's C-10 rows as
  amended on 2026-11-14 (16 declines messages and receipts; 18 declines the attempt record; 19
  owns repair resume; 20 reads DM-10 `attempts`). Their line-number citations into this spec
  drift with edits and should become id citations.

### Change log

- 2026-11-06 — implementation/state reconciliation (preserved in Source).
- 2026-11-14 — English refinement: REQ-01–REQ-08 and AC-01–AC-05 restated; REQ-09–REQ-51 and
  AC-06–AC-19 added; data model (including the note-entry rule and the DM-9 state order),
  contracts and edge cases specified; spec 14's packet fields adopted (REQ-51); the
  Devil's Advocate review findings folded in.
- 2026-11-14 — reconciliation with refined peer specs: 08 citations by id (DM-7, DM-8,
  Terminology row "Full structured result"), the checkpoint message is the full structured
  result on the helper route only, and the delta route statements restated (Terminology, C-4,
  C-8, C-10, REQ-36); C-10 rows 12, 16, 17, 18, 19, 20 aligned with the final peer texts (18 does
  not use DM-2; 16 does not consume messages or receipts; repair resume is 19's `status`; 12
  `repair` handoffs carry no receipt digest); spec 13 file-naming and rename note added; A-51
  appended; Context item 7, the Name mapping row and paragraph, and REQ-49's citation of 08
  REQ-01 added. No requirement id, acceptance criterion or id changed; REQ-36 gained one
  sentence and REQ-49 an explicit citation of 08 REQ-01.
- 2026-11-14 — independent final review: disable switch follows the spec 14 REQ-32 rule; A-03 states the no-launcher consequence; Note entries keep a red digest whole; `target_files` split rule aligned with 16; citations by id (09 Q-05, 12 E-32, 14 C-8/DM-11/REQ-42, 13 Notes).

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph stating problem and outcome |
| 2 | Out of Scope names concrete exclusions | PASS — 07, 12, 14, 16–20, run-log/05 changes, other orchestrators, structured ops not offered, measured savings, locking |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-51, previous ids preserved |
| 4 | Every REQ maps to an AC and back | PASS — Traceability table covers all 51 REQs and 19 ACs |
| 5 | Every AC is binary and can guide a test first | PASS — fixture-based Given/When/Then in `scripts/check-controller-step.py` |
| 6 | Non-functional targets measurable or N/A | PASS — NFR-01–NFR-04, NFR-06 measurable; NFR-05 N/A with reason |
| 7 | Data model and contracts specified | PASS — DM-1–DM-10, note-entry rule, C-1–C-11 |
| 8 | Error, empty, boundary, concurrency cases | PASS — Edge Cases table; concurrency limited to the single Orchestrator and recorded |
| 9 | Every ambiguity resolved or open | PASS — A-01–A-51; Q-01, Q-02 non-blocker; Q-03 withdrawn |
| 10 | No blocker question | PASS |
| 11 | Existing-code claims cited and verified | PASS — verified by author and critic against `060ce6d` and the worktree |
| 12 | Terminology matches the domain | PASS — domain terms reused; new terms added to `domain.md` by REQ-48 |
| 13 | Feature-sized (1–8 subtasks) | PASS — about six subtasks (Notes → Implementation hints) |
| 14 | Devil's Advocate review | PASS — Review: 4 rounds, score 100/100, critic: sub-agent, open: none |

Verdict: **READY FOR DEVELOPMENT**. Automated readiness is not sign-off; review before
implementation.

Note (2026-11-14 reconciliation with refined peer specs): citations to specs 08, 12, 13, 14, 16,
17, 18, 19 and 20 were checked against their final texts and only wording in Context,
Terminology, REQ-36, REQ-49, C-4, C-8, C-10 and Notes changed; the verdict stands and no requirement or acceptance criterion changed.
