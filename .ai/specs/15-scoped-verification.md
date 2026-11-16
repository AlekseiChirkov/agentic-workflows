# 15. Scoped verification: review evidence, reuse for unchanged inputs and finding-led recheck

## Source

- **Request.** Owner roadmap direction 5 of 2026-10-21, "review overhead": independent review,
  evidence reuse for unchanged inputs, finding-led repair review with impact expansion
  (row 5 of `.ai/specs/README.md` → "Nine token optimization workstreams"). Original language: Russian. The original body is preserved below
  as a labelled faithful English translation; it is historical and non-normative. Every
  requirement and acceptance identifier of the original (REQ-01–REQ-08, AC-01–AC-06) is kept
  with its meaning restated in EARS form under `## Requirements` and `## Acceptance Criteria`;
  new identifiers are appended. Two narrowings are deliberate: original REQ-03's three tiers
  become one delivered tier (`standard`), the others needing a later owner decision (A-07); and
  original REQ-08's "later-found defects" are tracked by spec 10 (late defects, spec 10 DM-11
  `late-defect` records), not here.
- **Refinement.** Rewritten in English on 2026-11-14 in an autonomous refinement under the
  owner's standing authorization for in-place replacement, against worktree revision
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`.

### Implementation review — 2026-11-06 (preserved verbatim)

- **Disposition:** Planned; independent review foundations delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Atomic contract checks, an independent Validator, frozen test evidence, and task-level review gates exist.
- **Outstanding scope and limits:** Effective-input test receipts, qualified verification tiers, cross-session evidence reuse, and the formal finding-led incremental review protocol remain undelivered. Existing reviewer passes do not certify the future tiers.
- **Sources:** [`workflows/pav-check.md`](../../workflows/pav-check.md), [`workflows/pv-contract.md`](../../workflows/pv-contract.md), [`workflows/pv-review.md`](../../workflows/pv-review.md), [`workflows/spec-run.md`](../../workflows/spec-run.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Change log of the original (preserved verbatim)

- 2026-11-06 — implementation/state reconciliation: Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

### Original text (translated from Russian; historical, non-normative)

**Title.** 15. Risk-based verification and finding-led recheck of repairs.

**1. Status and grounds.** Status: a future capability of direction 5 of the request of
2026-10-21. Source snapshot: `8c2fa08c18115ffcf38a1798742c41e53a2c7461`, 2026-10-28. The current
`rules/orchestration.md` and `workflows/spec-run.md` require a separate reviewer without the
executor's reasoning; `NEEDS WORK` prevents closure and further sequential execution. The
separate audit report mentioned by the source documents is absent from the snapshot and is not
used as evidence of implementation. Receipts of reproducible checks, qualified cheaper modes
and rechecking only the affected area are not yet declared implemented. This specification
changes evidence preparation and the scope of review. Automatic repair and exemption from the
stop are defined exclusively by [17](17-local-repair-and-escalation.md).

**2. Goal and boundaries.** Repeat only those checks whose inputs or scope have justifiably
changed, while keeping an independent assessment of all criteria and of the behaviour of the
whole affected system. A strong model and passing tests are evidence, not a guarantee of the
absence of defects. In scope: the coverage plan, primary deterministic checks, the permitted
level of semantic review, the reviewer packet, receipts, repair impact analysis and scope
expansion. Out of scope: removing the independent reviewer role, acceptance by tests alone,
automatic specification changes, lowering verification because of model price, model
selection outside the catalog, and a new status vocabulary.

| Responsible | Actions |
|---|---|
| Orchestrator | Collect facts, check freshness, choose the permitted mode by policy, keep stops and evidence |
| Deterministic tools | Execute real commands and keep results; do not decide architectural correctness beyond their checks |
| Independent reviewer | Assess the exact contract, behaviour, interfaces, invariants and findings without the executor's reasoning |
| Independent evaluation 10 | Check which defects the whole strategy misses, including a strong reviewer |

**3. Fixed conditions.** (1) Every criterion and material invariant has a verification owner
or an explicitly open gap. (2) A required failed, missing or unknown check never becomes
successful by default. (3) A receipt is bound to the actual inputs, command and environment;
one commit does not describe a dirty working tree. (4) Partial recheck is admissible only
together with evidence of why the remaining obligations stay covered. (5) An interface change,
a shared invariant change or unknown impact widens the scope; lack of confidence is not read as
lack of impact. (6) The reviewer is independent of producing the implementation; passing it the
executor's reasoning or self-assessment does not replace the source evidence. (7) Test level
`none` is admissible only through the existing justified rule; it creates no false RED or tests
and does not cancel document, contract or result checks that remain applicable. (8) An existing
`atomic-tests: pinned` keeps the evidence of tests passing before the change for unchanged
behaviour; it is not passed off as RED. Old blocks without `atomic-tests` are read under the
canonical compatibility rule without retroactively demanding RED for historical work already
started. The legitimate grounds of the applicable branch are checked, not a fictitious common
template.

**4. Requirements.**
- REQ-01. Create a verification plan from the unchanged AC, risk, criticality, interfaces and
  available commands. State separately what a tool checks, what needs independent
  semantic/architectural review and what stays uncovered.
- REQ-02. Before semantic review, run the applicable compilation, typing, static checks, tests
  and structural checks when running them is safe and permitted. A required error or
  unavailability prevents completion. A failure may be passed to diagnosis but does not turn
  into `DONE`.
- REQ-03. Keep three available tiers: deterministic checks, a qualified cheaper semantic review
  and a strong review of complex/critical/uncertain changes. The current conservative policy
  stays the default until a new one passes independent evaluation 10. A positive result of a
  lower tier does not by itself permit dropping the required semantic review.
- REQ-04. The reviewer packet contains the exact AC, invariants and constraints, the base and
  reviewed revisions, the complete change list, the diff and the needed surrounding behaviour,
  interfaces/callers and test evidence per 14/17. A file diff alone is insufficient when the
  context matters. The executor's reasoning is excluded.
- REQ-05. Reusing a tool result requires all effective inputs to match: sources/tests,
  command/arguments, dependencies, environment, configuration and other declared sources.
  Unknown identity, relevant uncommitted/untracked changes and changed inputs make the receipt
  unusable.
- REQ-06. On repair, pass the previous findings, the previously reviewed and the new tree, the
  repair diff and the open AC. Check each finding, regressions and impact. Changed interfaces,
  shared invariants, scope or unknown dependencies require a wider/full review. A new reviewer
  receives sufficient source content, not one old receipt.
- REQ-07. Keep the current meaning of `DONE`/`NEEDS WORK` and of finding severities. Record the
  reviewed scope, receipts, all material findings, open obligations and expansion reasons.
  Shortening a report does not remove anything important. The specification itself does not
  start repair and does not close a defect.
- REQ-08. Pass to 05/10 information about commands, verification levels, reused inputs,
  rechecks, context expansion and later-found defects. Compare execution and verification on
  the same tasks; do not assume verification is always cheaper. Apply G1–G8.

**5. Coverage plan and level choice.** One row per obligation: `obligation_id` (an existing AC
or a stable invariant/constraint id), `source_ref`/`source_hash` (the canonical exact
requirement), `risk_reason` (contract, security, data integrity, migration, shared dependency,
uncertainty), `deterministic_checks` (exact commands, scope and expected results, or the reason
they do not apply), `semantic_review` (what the reviewer must independently assess),
`integration_owner` (who checks interaction with other changes, and where), `coverage_state`
(covered by fresh evidence, needs execution, not checkable with current means, or unresolved).
An empty test list does not mean absence of risk. A `none/n-a` declaration carries a reference
to the test-level decision; the reviewer does not create it for convenience. Choice rule:
(1) determine required commands and semantic obligations first, cost second; (2) for critical
risk, uncertain impact, architecture/shared-contract change or missing qualification use the
current conservative/strong review; (3) a cheaper semantic review is admissible only for a
pre-qualified task class, an available configuration and a permitted 10/16 policy — a low
price or a model name is not qualification; (4) deterministic checks run before semantic ones
when admissible, and their failure stands even after a positive reviewer text; (5) both
semantic tiers need not run on every task: the sufficient permitted mode is chosen, and the
strong review is reached by risk, a coverage gap or the result of the cheaper review.

**6. Tool result receipt.** Target record version 1: `receipt_id, schema_version;
repository_id, worktree_id, base_revision, head_revision; task_contract_hash, check_id,
check_scope; effective_inputs_manifest, effective_inputs_digest; command_argv_digest,
working_dir; dependency_digest, environment_digest, configuration_digest; tool_versions,
nondeterministic_inputs; command_status, termination_signal, capture_status; artifact_refs,
covered_obligations, created_at`. The effective inputs manifest includes the needed sources,
tests, fixtures, configuration, local data, dependent interfaces, missing expected files and
derived inputs with provenance; a matching commit tree hash is insufficient when the command
reads additional files; a permitted modified working tree may be checked, but its actual
content enters the manifest. The environment digest includes affecting environment versions,
platform and safe configuration identifiers; secrets and raw credentials are not stored. If
external state, the current date, network, randomness or secret-dependent configuration
materially affects the result and cannot be captured, the receipt is marked unusable for reuse
and the check is run again; a random set of known fields must not be hashed and declared the
full environment. Artifacts per 14 hold complete results and hashes; `capture_status !=
complete`, a lost artifact or a byte mismatch excludes its use as evidence of a successful
check; the creation time helps diagnosis but does not prove freshness. Reuse is permitted only
when all hold: schema and command supported; contract and checked obligation match; the full
set of affecting inputs is known and matches; environment, configuration and dependencies
match; artifacts available and intact; no new run is required by the policy of that check
type. A change to an irrelevant file need not invalidate a narrow check **if** the completeness
of its dependencies is proven; without such a dependency model, conservative invalidation over
the whole potentially affecting tree applies; absence of a dependency record does not prove
absence of the dependency.

**7. Independent review packet.** (1) Exact goal, AC, invariants, prohibitions, permitted scope
and accepted decisions. (2) Identity of the base and reviewed states; the complete list of
added/modified/deleted/renamed files. (3) The complete diff or complete verifiable references
with range retrieval; the file list is not cut to the first few. (4) Needed interface
definitions, callers, settings and code before/after. (5) Test level and justification, RED
evidence where applicable, frozen test hashes, actual commands and results. (6) The coverage
plan, open findings, the previously reviewed area and the reasons for the requested mode.
Excluded: the executor's reasoning, its conversation about producing the solution and its
self-assessment; facts from its result are re-verified and moved into neutral form. A reviewer
that finds a missing basis requests expansion through 12/14 and does not accept the result
before receiving the needed context.

**8. Recheck of a repair.** The comparison base is the last independently reviewed tree, not an
arbitrary previous commit. Each finding keeps a stable id, its original evidence, affected AC
and its link to the repair. (1) Check that the contract did not change without permission and
frozen tests were not weakened. (2) Build the repair diff and impact set: files, interfaces,
callers, shared data, configuration, tests and integration boundaries. (3) Give each old
finding its own outcome: fixed with evidence, remains, not confirmed with independent
justification, or needs an owner decision; disappearance of the finding text does not mean it
is fixed. (4) Repeat changed deterministic checks; use unchanged results only per section 6.
(5) Check regressions in the impact set and confirm why the remaining AC are still covered.
(6) On a public/shared interface, architecture, invariant or criteria change, or unknown impact,
widen to the whole affected task; when it cannot be localized, to the whole change.
(7) Produce an independent verdict and a complete scope record; fixing all old findings is not
acceptance when a new important violation appeared. After merging children per 23 the actual
resulting tree is checked; two successful checks of isolated branches do not prove their
compatibility; a recheck may use individual matching receipts but does not carry a common green
verdict over to the merge without analysis.

**9. Errors and stops.**

| Case | Reaction |
|---|---|
| Tests pass but an AC is violated | `NEEDS WORK`; repair only by the provided path |
| Required command missing | Explicit gap, diagnosis/recovery; not counted as run |
| Tests weakened after RED | Stop and the existing procedure for changing the test basis |
| Same code version, different environment | Invalidate dependent receipts and repeat |
| Relevant untracked files appeared | Update the input manifest and repeat dependent checks |
| Artifact deleted or damaged | Restore the evidence or run the check again |
| New reviewer | Pass sufficient original contract, facts and previous findings |
| Repair impact unclear | Full review of the affected task; do not save by assumption |
| Verification tool unavailable | Keep the stop or the documented previous conservative path; do not invent a result |

**10. Acceptance criteria.** AC-01 (REQ-01, REQ-02): plans cover all AC and show gaps; a
required error/unavailability prevents acceptance even with a synthetic positive verdict;
justified `none/n-a`, `pinned` and already-started historical tasks are checked under their own
conditions and create no false RED evidence. AC-02 (REQ-03): table scenarios of criticality,
architectural uncertainty and missing qualification select the conservative/strong review; a
passing tool does not cancel the semantic duty; price does not determine model suitability.
AC-03 (REQ-04): the packet holds all obligations and the complete change manifest; needed
interfaces are available; the executor's reasoning does not reach the independent reviewer's
packet. AC-04 (REQ-05): fully matching inputs permit reuse; a change of source/test/command/
environment/dependency, an unknown external dependency, relevant dirty files and a lost
artifact require a new check; a provably irrelevant change causes no false invalidation of a
narrow result. AC-05 (REQ-06, REQ-07): a local repair checks old findings, regressions and the
remaining AC; an interface/invariant change widens the scope; important findings survive report
shortening; a wrong result is not closed automatically; a merge is checked on the resulting
tree. AC-06 (REQ-08): the scenarios "tests green, behaviour wrong" and a violation the reviewer
missed are detected by the independent checks of 10; reports separate execution, review and
repair, include the full recheck and disabling of the optimization, without unconfirmed promises
of savings. Traceability: REQ-01–02 → AC-01; REQ-03 → AC-02; REQ-04 → AC-03; REQ-05 → AC-04;
REQ-06–07 → AC-05; REQ-08 → AC-06.

**11. Introduction and readiness.** (1) Pin the current meaning of verdicts and test levels; do
not redefine the state vocabulary. (2) Introduce the obligation map and synthetic defects before
optimizing repeats. (3) Implement receipts with a complete input manifest and conservative
invalidation; then the independent review packet. (4) Add repair impact analysis and the
explanation of retained coverage. (5) Connect 12/13/14 and 05 reporting; check the complete
fallback path with the optimization disabled. (6) Keep the cheaper mode off by default until a
separate qualification under 10 with quality tolerances chosen in advance by the owner.
Dependencies: 10, 12, 13, 14. Gates G1–G8 are mandatory. Matching receipts confirm the
repeatability of known inputs, not complete understanding of the system. Checks with unknown or
unstable inputs may be run again — saving is not more important than sufficient evidence.

## Context & Problem

Facts verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

1. **Leaf review runs every check again and has no notion of reuse.** `/pav-check` runs the
   applicable `test:` and `lint:` commands from the runbook and reports missing commands,
   unavailable dependencies or incomplete runs as evidence gaps
   (`workflows/pav-check.md:47-49`). The validation bootstrap rules require running `test:` and
   `lint:` before every verdict (`rules/phase-atomic-validation.md:47`,
   `rules/phase-validation.md:32`). Task-level `/pv-contract` and `/pv-review` run on the same
   stack tip (`workflows/spec-run.md:322-326`) with no record of what an earlier step ran on the
   same tree.
2. **A failed leaf is re-reviewed in full.** A resumed `failed` record "requires repaired
   implementation and a fresh `/pav-check`" (`workflows/phase-atomic-validation.md:80-83`);
   `/pav-check` re-derives every criterion (`workflows/pav-check.md:51-52`). Findings are free
   text in `notes:` (`workflows/pav-check.md:106`) without stable identifiers, so a later review
   cannot say which earlier finding is resolved.
3. **The task-level re-run after fixes is scoped only in prose.** After fix-tasks,
   `/pv-execute-fixes` re-runs `/pv-contract` and `/pv-review` "for the changed surface" and
   records "resolution evidence" (`workflows/pv-execute-fixes.md:46-49`); the quick tier
   re-runs both after inline fixes (`workflows/phase-validation.md:94-99`); `/bugfix` runs both
   against its inline contract (`workflows/bugfix.md:132`). None defines the changed surface,
   the evidence, or when the scope must widen.
4. **Independence is a role boundary.** The Validator is a separate agent that does not receive
   the Implementer's reasoning, intermediate steps or self-assessment
   (`rules/orchestration.md:80-92`); `/spec-run` gives it the description, the test files and
   `git diff <base_commit>..HEAD` and explicitly not the Implementer's reasoning or report
   (`workflows/spec-run.md:284-292`). A NEEDS WORK verdict stops the run
   (`workflows/spec-run.md:297-299`).
5. **The composite integration check reads the union of children's files.**
   (`workflows/phase-composite-validation.md:55-64`); exactly one workflow, `/pav-close`, may
   invoke it (`scripts/validate-contracts.sh:1451-1455`). Spec 22 later moves the invocation to
   `/spec-run` and runs it on a merged composite tip
   (spec 22 REQ-12, REQ-40).
6. **Spec 12 supplies the Validator's context but leaves sufficiency here.** The validator
   packet carries the Task Contract, `base_commit`, the reviewed revision and the
   `--no-renames` name-status list of changed paths; "15 decides sufficiency and may add sources
   by expansion" (spec 12 C-8 row 15, REQ-19, DM-6 item 7).
   Packets are content-addressed and `task_contract_hash` is `sha256:` + the contract part
   digest (12 C-8 row 13); a contract change mid-leaf yields a successor packet and the Validator
   judges against the current contract (12 A-10).
7. **Spec 13 exposes checkpoint facts but keeps Validators away from Implementer reports.**
   Its REQ-30 forbids the Orchestrator to pass "an Implementer report, checkpoint message,
   proposal, receipt or journal path to a Validator"
   (`.ai/specs/13-orchestrator-overhead.md`, REQ-30 and the Validator row of its Actors & Roles table);
   its C-10 row for spec 15 records that this spec does not consume `green` messages or
   `red`/`pinned` receipts, because REQ-30 forbids passing them to a Validator, and keeps
   Validator inputs at `workflows/spec-run.md:284-292` plus the reviewer inputs owned here.
8. **Report forms exist for the Check boundary.** Spec 11's Check form has `Scope`, `Inputs`,
   `Verified obligations`, `Unverified obligations`, `Findings` (every critical and important
   finding) and `Verdict` (`.ai/specs/11-context-tiering.md`, DM-8 Report forms).
9. **The validator inventory is frozen.** New checks go into standalone scripts outside
   `scripts/validate-contracts.sh` and outside `tests/` (ADR-0019 Decision 3,
   `.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`). Several frozen
   checks read the workflows this spec edits: phrases in `/pav-check`
   (`scripts/validate-contracts.sh:900-912`, `:1261-1262`), a write-verb scan of sub-agent
   workflows for shared paths (`:1541-1548`), and the single composite invoker (`:1451-1455`).
   Every rule file must be named in the deployment lists of `scripts/setup-new-project.sh` and
   `scripts/sync.sh` (`scripts/validate-contracts.sh:1293-1305`).
10. **The runbook declares commands as free shell text.** `## Commands` holds `test:`, `lint:`,
    `typecheck:` and `build:` (`templates/.ai/context/runbook.md:10-15`); in this repository
    `build:` deploys to the harness directories (`.ai/context/runbook.md:11`).
11. **Test-first evidence and its exemptions are canonical.** `atomic-tests:` values, the
    pre-TDD compatibility rule and the blocker rule for missing dependencies are defined in
    `rules/tdd.md:34-50`, `:208-210` and `rules/workflow-globals.md:195-208`.

**Consequence.** Every review re-runs every check even when nothing it reads has changed, every
re-review after a repair repeats the whole review without a defined link to the earlier
findings, and nothing records why a narrower re-review would still cover all obligations. The
roadmap states that no saving has been measured (`.ai/specs/README.md` → "Nine token optimization workstreams"); this spec creates
the evidence and the safe scoping, and leaves any claim of saving to spec 10.

## Goal

Give every independent review in the pipeline a recorded, checkable account of what it had to
cover and what it actually covered: a coverage plan of the obligations, deterministic check
receipts bound to the exact content, command and environment they ran against, reuse of a
receipt only when those inputs are provably identical and the project has declared the check
deterministic, and a finding-led recheck after a repair that resolves each earlier finding by
stable identifier, re-reviews every obligation whose evidence changed, and widens to a full
review whenever the contract, an interface, an invariant or the impact is changed or unknown —
all through an optional helper whose absence or failure leaves today's full review in place,
with the single change that defined checks are classified the same way on both paths (REQ-55).

## Scope

1. An optional standard-library helper `scripts/scoped-verification.py` with subcommands
   `version`, `prepare`, `run` and `record` (C-1).
2. The coverage plan, change manifest and recheck plan produced by `prepare` (DM-2, DM-3, DM-5).
3. Check receipts with content-addressed captured output and the reuse decision (DM-4, DM-6).
4. Write-once review records with stable finding identifiers, recheck outcomes, scope and
   expansion reasons, validated by `record` (DM-7).
5. The project declaration of reusable checks in the runbook (DM-9) and the review notes entry
   (DM-8).
6. A new on-demand rule `rules/contract-verification.md` (C-4).
7. Wiring into `/pav-check`, `/pv-contract`, `/pv-review`, `/pv-issues`, `/pv-execute-fixes`,
   `/phase-validation`, `/phase-composite-validation`, `/spec-run` step 4.3 and the
   orchestration rule (C-5).
8. The standalone acceptance suite `scripts/check-scoped-verification.py` (C-7), an ignore rule,
   documentation, knowledge-base updates and an ADR.
9. The contracts exposed to specs 05, 10, 23, 13, 14, 16, 17 and 18 (C-6).

## Out of Scope

- Repair: classification of findings for repair, repair contracts, attempt limits, episodes,
  escalation to a stronger model and any change to the NEEDS WORK stop (spec 17).
- A cheaper or differently configured reviewer, model or effort selection for reviewers
  (specs 04, 16); qualification of any verification strategy and every claim that scoped review
  preserves quality or saves cost (spec 10, strategy E of
  its original §7, REQ-06). The only tier delivered is `standard`.
- Context packets, their freshness and expansion recording (spec 12); checkpoint messages and
  journals (spec 13); output capture, bounded previews, range retrieval and artifact integrity of
  command output (spec 14, used through this spec's DM-4a); usage
  telemetry objects (spec 05); parallel children, worktrees and merges (spec 23).
- Reusing receipts produced outside review workflows, receipts across different worktree roots,
  and any per-check dependency model narrower than the whole non-ignored repository tree.
- Running `build:` commands, timeouts on checks, cleanup of stores, and locks against two
  concurrent reviews of the same scope (the second `record` fails with `record-conflict`).
- Changing the definitions of `DONE`/`NEEDS WORK`, severity values, status vocabularies,
  protected sections, test-first order, the RED/pinned/`n-a` rules, git rails, stops, or the
  invoker of composite validation. The one deliberate change to review behaviour is REQ-55 (how a
  failing or incomplete runbook check is classified), applied with and without the helper; the
  owner approved it on 2026-11-14 (D-01). The
  state tool of spec 07 is not used.
- Changing `scripts/validate-contracts.sh` or any file under `tests/`.

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Maintainer / implementing agent | Delivers this spec test-first in this repository (failing suite cases before helper code and before rule/workflow text); never edits deployed copies (P1) |
| Reviewer (Validator in `/pav-check`; task reviewer in `/pv-contract`, `/pv-review`; composite reviewer in `/phase-composite-validation`) | Runs `prepare`, `run` and `record` (at N = 1; in the cases of REQ-62 the reviewer returns a draft and the root runs `record`); reads sources and git directly; writes drafts under `<task>/verification/drafts/` (at N = 1; in the cases of REQ-62 it returns the draft and the root saves it); appends DM-8 notes entries only where its workflow already writes; never reads the Implementer's reasoning, report or self-assessment |
| Orchestrator (`/spec-run`) | Spawns the Validator as today; applies composite deltas carrying DM-8 entries; never runs the helper for a review it does not perform |
| Implementer | Unchanged; never runs `run` or `record` |
| `scripts/scoped-verification.py` | Reads the task directory, the knowledge root and the repository; runs read-only git subcommands; executes exactly the runbook command of the requested check (through spec 14's helper when available, which also runs its `verify`); writes only the receipt store (`run`) and `<task>/verification/reviews/` (`record`); starts no model, opens no network connection itself |
| `scripts/check-scoped-verification.py` | Acceptance suite; builds and removes disposable fixtures under a temporary directory only |
| Project owner | Declares reusable checks in the runbook; disables the helper with `ORCHESTRAIL_SCOPED_VERIFICATION=off`; decides owner-decision findings and deferrals through existing stops |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Review | One run of `/pav-check` (step `check`), `/pv-contract` (step `contract`), `/pv-review` (step `review`) or `/phase-composite-validation` (step `integration`) | `workflows/pav-check.md:2`, `workflows/pv-contract.md:2`, `workflows/pv-review.md:2`, `workflows/phase-composite-validation.md:2`; this spec |
| Level | `leaf`, `task` or `composite` — what a review covers | This spec |
| Scope key | The leaf or composite id (13's `leaf_id` form) for leaf and composite reviews; `task` for task-level reviews | `.ai/specs/13-orchestrator-overhead.md`, Data Model → Identifiers (`leaf_id`) |
| Obligation | One item a review must judge: `AC-<n>`, `INV-<n>` or `OFF-<n>` (DM-2) | Original §5 "obligation" |
| Coverage plan | The obligations, contract digest and check definitions of one review (DM-2) | Original §5 |
| Change manifest | The changed paths the review must read, with content digests (DM-3) | Original §7 item 2 |
| Check | One of the runbook commands `test`, `lint`, `typecheck` | `templates/.ai/context/runbook.md:12-14` |
| Defined check | A check whose runbook value is non-empty and does not start with `<` or `(` (DM-9) | This spec |
| Receipt | The write-once record of one execution of a check (DM-4) | Original §6 |
| Inputs digest | The digest of everything DM-4 binds a check result to | Original §6 "effective_inputs_digest" |
| Reuse | Accepting an existing receipt instead of executing a check, under DM-6 | Original §6 |
| Review record | The write-once record of one review (DM-7) | Original REQ-07 |
| Scope | `finding-led`, `full-leaf`, `full-task` or `full-integration` | This spec |
| Minimum scope | The narrowest scope `prepare` permits for a review (DM-5) | This spec |
| Finding-led recheck | A review whose scope is `finding-led`: every open prior finding gets an outcome, every changed path and affected obligation is re-reviewed, unaffected obligations are carried | Original §8 |
| Fix diff | The paths changed since the prior record's reviewed head (DM-5) | Original §8 step 2 "repair diff" |
| Carried | An obligation state meaning "verified by a prior record whose evidence paths are unchanged" | Original invariant 4 |
| Finding | One defect in a review record with a stable id `<scope key>/F<n>` (DM-7) | This spec (DM-7); consumed by spec 17 |
| Outcome | `resolved`, `remains`, `withdrawn`, `owner-decision` or `owner-accepted` for a prior open finding | Original §8 step 3 |
| Tier | Verification configuration class; only `standard` exists | Original REQ-03 |
| Helper | `scripts/scoped-verification.py` | This spec |
| Receipt store | `<git common dir>/orchestrail-verification/` (DM-1) | This spec |
| `WORK_DIR`, `AI_DIR`, task directory | As resolved by the calling workflow | `workflows/pav-check.md:28-32`; `rules/phase-atomic-validation.md:16-20` |
| Canonical JSON, self-digest | As spec 13 defines them | `.ai/specs/13-orchestrator-overhead.md`, Data Model preamble |
| Verdict, severity | `DONE`/`NEEDS WORK`; `critical`/`important`/`optional` — unchanged | `workflows/pav-check.md:97-101` |

Rejected synonyms: "cache" or "cache hit" for reuse (no provider cache is involved); "tier" for a
scope; "incremental review" for finding-led recheck; "fixed" for the outcome `resolved`;
"receipt" for a review record or for spec 12's and 13's receipts (those keep their own names in
their specs).

## Requirements

Names follow today's files; once spec 09 is delivered (it precedes this spec,
`.ai/specs/README.md` → "Dependency order"), every workflow and rule path follows 09's maps (`## Notes → Name
mapping`). Spec 11's `loads:` declarations and 700-word limit for rules apply to every file this
spec adds or edits. "THE helper" is `scripts/scoped-verification.py`; a requirement that names a
workflow or rule binds that file.

### Previous identifiers, restated

- **REQ-01 Coverage plan.** WHEN `prepare` runs, THE helper SHALL print a coverage plan that lists
  every obligation of the requested level per DM-2 with its id, kind, source label and text
  digest, together with the defined, undefined and reusable checks.
- **REQ-02 Checks gate the verdict.** IF a review record draft states `DONE` while any defined
  check lacks a referenced receipt for the current inputs with `command_status` exit code 0 and
  `evidence: usable`, THEN `record` SHALL refuse it with reason `verdict-inconsistent` or
  `check-missing` (DM-7 rules R-08, R-11).
- **REQ-03 Single tier.** IF a draft carries a `tier` other than `standard`, THEN `record` SHALL
  refuse it with reason `tier-invalid`.
- **REQ-04 Coverage of changed paths.** IF a draft's `reviewed_paths` omit any path that the
  scope requires (every change-manifest path in a full scope; every fix-diff path in
  `finding-led`), THEN `record` SHALL refuse it with reason `coverage-incomplete`.
- **REQ-05 Reuse only for identical inputs.** WHEN `run --reuse` runs, THE helper SHALL reuse a
  receipt only when every DM-6 condition holds and SHALL otherwise execute the check.
- **REQ-06 Recheck plan.** WHEN `prepare` runs at level `leaf` or `task`, THE helper SHALL compute
  the minimum scope, the fix diff, the open prior findings, the obligations to re-review and
  the carry-eligible obligations per DM-5.
- **REQ-07 Verdict semantics.** WHEN `record` validates a leaf or composite draft, THE helper SHALL
  accept `DONE` only when DM-7 rule R-08 holds and `NEEDS WORK` only when it does not.
- **REQ-08 Attribution facts.** THE review record SHALL contain, per DM-7, the scope, minimum
  scope, expansion reasons, each check's action (`executed` or `reused`) and receipt id, and each
  obligation's final state.

### Preparation

- **REQ-09 Contract digest.** WHEN `prepare` runs, THE helper SHALL compute `contract_digest`
  over the DM-2 contract sources of the level in their fixed order.
- **REQ-10 Change manifest.** WHEN `prepare` runs, THE helper SHALL print the DM-3 change manifest:
  with `--base`, every path changed between the base and the working tree plus untracked
  non-ignored paths, merged with `--listed` paths; without `--base`, the `--listed` paths only;
  in both cases excluding paths inside the task directory.
- **REQ-11 Prior record.** WHEN `prepare` runs, THE helper SHALL select the prior record by the
  DM-5 selection rule and SHALL list every finding of a selected valid prior record with status
  `open` or `owner-decision` in `open_findings`, whether or not the prior is eligible for
  `finding-led`.
- **REQ-12 Latest-review marker.** IF a valid prior record exists and the last DM-8 entry for the
  scope key and step in the DM-8 state location is absent, is a `none` entry, or names a digest
  different from the prior record file's SHA-256, THEN `prepare` SHALL add reason
  `prior-not-latest` and set minimum scope to full.
- **REQ-13 Contract change.** IF the prior record's `contract_digest` differs from the current one,
  or both the prior record and the invocation carry a `task_contract_hash` and they differ, THEN
  `prepare` SHALL set minimum scope to full with reason `contract-changed`.
- **REQ-14 Cross-leaf change.** IF at level `leaf` a fix-diff path equals a `target_files:` entry
  of another leaf block of the task, THEN `prepare` SHALL set minimum scope to `full-leaf` with
  reason `cross-leaf-change`.
- **REQ-15 Composite and accepted reviews.** THE helper SHALL set minimum scope `full-integration`
  for level `composite`, and `full-leaf` with reason `prior-accepted` for a leaf whose prior
  record has verdict `DONE`.
- **REQ-16 Deterministic preparation.** WHEN `prepare` runs twice on identical files, repository
  state and arguments, THE helper SHALL print byte-identical output.

### Receipts

- **REQ-17 Execution.** WHEN `run` executes a check, THE helper SHALL run the argument vector
  `["bash", "-c", <runbook value>]` exactly once in `WORK_DIR` with the helper's own environment,
  capture standard output and standard error as DM-4a states (through spec 14's helper when it is
  available and does not refuse, otherwise to separate files of its own; REQ-58), and publish one
  DM-4 receipt.
- **REQ-18 Non-reusable receipts.** WHEN `run` publishes a receipt, THE helper SHALL set
  `reusable` to false and list every applicable DM-4 reason when the check is not declared
  reusable, capture failed, the command did not exit normally, the inputs digest changed during
  the run, or any input was unknown.
- **REQ-19 Conflicting receipts.** IF two or more DM-6-valid receipts for the current inputs digest
  differ in `command_status`, THEN `run --reuse` SHALL reuse none, report `conflicting-receipts`
  and execute the check.
- **REQ-20 Damaged receipts.** IF a stored receipt fails DM-6 integrity (self-digest, file name,
  schema or output bytes), THEN `run` SHALL skip it, report `receipt-damaged` with its file name,
  and leave it unchanged.
- **REQ-21 Undefined checks.** IF `run` is asked for a check that is not defined, or for any name
  other than `test`, `lint` or `typecheck`, THEN THE helper SHALL exit 2 with error
  `check-undefined` and execute nothing.
- **REQ-22 Unwritable store.** IF the receipt store cannot be created or written, THEN `run` SHALL
  exit 3 with error `store-unwritable` before executing the command.
- **REQ-23 Interruption.** IF the helper receives SIGINT or SIGTERM during `run`, THEN THE helper
  SHALL forward the signal to the process group of the child it started (the command in mode
  `direct`, spec 14's helper in mode `capture-output`, which forwards it on by its own REQ-15),
  wait for that child to exit, publish no receipt, and exit 4 with error `interrupted`.

### Records

- **REQ-24 Write-once publication.** WHEN `record` accepts a draft, THE helper SHALL write the
  DM-7 record exclusively to `<task>/verification/reviews/<scope key>/<n>.json` with `n` one more
  than the highest record name (DM-1) held by a regular file, and SHALL exit 3 with error
  `record-conflict` when any directory entry of that name already exists.
- **REQ-25 Stale preparation.** IF the draft's `preparation_digest` differs from the digest of a
  preparation recomputed by `record` with the same arguments, THEN `record` SHALL refuse with
  reason `preparation-stale`.
- **REQ-26 Obligation completeness.** IF a draft omits a planned obligation, names an unplanned
  one, or leaves any obligation in a state other than `verified`, `carried`, `unverified` or
  `failed`, THEN `record` SHALL refuse with reason `obligations-mismatch`.
- **REQ-27 Valid carrying.** IF a draft marks an obligation `carried` outside scope `finding-led`,
  or for an obligation not in the preparation's `carry_eligible` list, THEN `record` SHALL refuse
  with reason `carry-invalid`.
- **REQ-28 Prior findings answered.** IF a draft lacks exactly one outcome for each open prior
  finding of the preparation, gives `withdrawn` without non-empty evidence, or gives
  `owner-accepted` without a non-empty `decision` reference, THEN `record` SHALL refuse with
  reason `prior-outcome-missing`, `withdrawal-unjustified` or `owner-decision-unreferenced`.
- **REQ-29 Finding identifiers.** IF a draft gives a new finding an id that is not
  `<scope key>/F<n>` with `n` greater than every finding number in earlier records of the scope
  key, reuses an id, or names a `same_as` that no earlier record contains, THEN `record` SHALL
  refuse with reason `finding-id-invalid`.
- **REQ-30 Scope not narrower.** IF a draft's scope is narrower than the preparation's minimum
  scope, or is `finding-led` while any `interface_impact` entry is `interface-change`,
  `invariant-change` or `unknown` or any fix-diff path lacks an entry, THEN `record` SHALL refuse
  with reason `scope-too-narrow`.
- **REQ-31 Failing checks reported.** IF a referenced receipt has a non-zero exit code and no
  finding of severity `critical` or `important` names that check in its `check` field, THEN
  `record` SHALL refuse with reason `check-failure-unreported`.
- **REQ-32 Incomplete checks.** IF a referenced receipt's command did not exit normally or its
  evidence is `unusable`, THEN `record` SHALL refuse with reason `check-incomplete`.
- **REQ-33 TDD audit field.** WHEN `record` validates a leaf draft, THE helper SHALL require
  `tdd_audit.atomic_tests` to equal the leaf block's `atomic-tests:` value (`absent` when the field
  is missing) and `tdd_audit.outcome` to be `performed`, and SHALL require
  `tdd_audit.outcome: not-applicable` for task and composite drafts.

### Helper boundaries

- **REQ-34 Disable switch.** WHILE `ORCHESTRAIL_SCOPED_VERIFICATION` is set to a value other than the
  empty string or `on` (documented value `off`; the rule of spec 12 REQ-32), THE helper SHALL
  exit 4 with error `disabled` for every subcommand except `version`, executing and writing
  nothing.
- **REQ-35 Runtime and repository.** IF the Python runtime is older than 3.11, or `--work` is not
  inside a git work tree, THEN THE helper SHALL exit 4 with error `runtime-unavailable` or
  `not-a-repository` and write nothing.
- **REQ-36 Isolation.** WHILE any subcommand runs, THE helper SHALL write only inside the receipt
  store (`run`) and `<task>/verification/reviews/` (`record`), start no model, and open no network
  connection itself; the only other processes it starts are read-only git subcommands, the check
  command, and spec 14's `capture-output.sh run` (which writes its own store) and `verify`.
- **REQ-37 Result line.** WHEN a subcommand ends, THE helper SHALL print exactly one DM-10 JSON line
  on standard output and nothing else there.

### Rule and workflows

- **REQ-38 Rule.** THE rule `rules/contract-verification.md` SHALL have the front matter and the
  anchored lines of C-4 verbatim and at most 700 words.
- **REQ-39 Leaf review.** THE workflow `/pav-check` SHALL cite `` `contract-verification → ## Review
  procedure` `` and SHALL, when the helper is available, run defined checks through `run --reuse`
  before judging criteria, prepare with `--level leaf`, publish the record before writing the
  verdict, and append the DM-8 entry to its own leaf block after the verdict writes (C-5).
- **REQ-40 Task review.** THE workflows `/pv-contract` and `/pv-review` SHALL cite the same section
  and SHALL, when the helper is available, do the same at level `task` with steps `contract` and
  `review`, writing the DM-8 entry as the last line of `## Contract Check` or `## Code Review`.
- **REQ-41 Issue mapping.** WHEN review records exist for the task, THE workflow `/pv-issues` SHALL
  add to each issue item one line `Findings: <ids>` listing the finding ids it merges.
- **REQ-42 Fix-cycle rechecks.** THE workflows `/pv-execute-fixes` (step 4) and `/phase-validation`
  (quick-tier re-run) SHALL state that the re-run of `/pv-contract` and `/pv-review` follows
  `` `contract-verification → ## Recheck` ``.
- **REQ-43 Composite review.** THE workflow `/phase-composite-validation` SHALL cite the review
  procedure for level `composite` and SHALL return the DM-8 entry as part of the composite block
  delta under `/spec-run`, without adding any invocation of itself.
- **REQ-44 Validator inputs.** THE `/spec-run` step 4.3 and the orchestration rule's `### Validator`
  section SHALL each cite `` `contract-verification → ## Reviewer inputs` `` while keeping their
  existing prohibition on the Implementer's reasoning and report.
- **REQ-45 Fallback.** WHERE the helper is unavailable, disabled, exits 2, 3 or 4, ends the
  record attempts of C-4 `Record:` without publication, or the review's files lie in more than one
  git work tree, THE review workflows SHALL perform the full review without the helper (REQ-55 still
  applying) and append the DM-8 `none` entry with the reason DM-8 maps to that cause.
- **REQ-46 Check report.** WHERE spec 11's Check report form is in force, THE `/pav-check` report
  SHALL fill `Scope`, `Verified obligations`, `Unverified obligations` and `Evidence` from the
  published record per C-5.
- **REQ-47 Runbook declaration.** THE runbook template `templates/.ai/context/runbook.md` SHALL
  contain, under `## Commands`, the DM-9 template line `reusable:` with an empty value.
- **REQ-48 Ignore rule.** THE repository's `.gitignore` SHALL contain the line
  `/.ai/tasks/*/*/verification/`.
- **REQ-55 Check classification.** THE rule `contract-verification` SHALL state, and every review
  workflow SHALL apply with or without the helper, that a defined `test`, `lint` or `typecheck`
  check exiting non-zero is a finding of at least `important` severity naming that check, and that
  a defined check that cannot start, is ended by a signal or loses its captured output is a
  blocker written as C-5 "Blocker writes" states for each level, with no verdict.
- **REQ-56 Blocker reset and resume.** WHEN a review of a scope starts and its block's `blocker:`
  value starts with `verification check `, THE review workflow SHALL reset it to `none` before
  running checks; and IF a task-level step section starts with a `blocked: verification check `
  line, THEN `/phase-validation` SHALL resume that step's writer and `/pv-review` SHALL stop
  (C-5).
- **REQ-57 Capture delegation.** WHERE spec 14's capture helper is available (this spec's DM-4a), WHEN `run`
  executes a check, THE helper SHALL run it through that helper and SHALL record in the receipt
  the DM-4a `output` object of mode `capture-output`, never storing output files of its own,
  except as REQ-58 states.
- **REQ-58 Capture refusal.** IF spec 14's helper refuses before starting the command (DM-4a
  case A), THEN `run` SHALL execute the check directly with its own capture and record the refusal
  code in `output.fallback`, so that the refusal changes no review outcome.
- **REQ-59 Capture loss after start.** IF spec 14's helper may have started the command but
  published no complete, verifiable artifact (DM-4a case B with a non-`complete` status, and case
  C), THEN `run` SHALL NOT execute the command again and SHALL publish a receipt whose evidence is
  `unusable`, so that `record` refuses it (`check-incomplete`) and REQ-55's blocker applies.
- **REQ-60 Single step-5 text.** WHERE specs 14 and 15 are both delivered, THE `/pav-check` step 5
  sentences and the `/phase-composite-validation` check sentence SHALL read exactly as the C-5
  replaced-sentence rows state, superseding spec 14's C-5 rows 3a and 5.
- **REQ-61 Spec 14 suite alignment.** THE delivered change SHALL update the text cases of spec
  14's acceptance suite `scripts/check-capture-output.py` that assert its C-5 rows 3a and 5 so that
  they assert the C-5 resulting sentences of this spec instead, and that suite SHALL pass.
- **REQ-62 Record in parallel mode.** WHERE spec 23's REQ-55 applies (it names the exact cases:
  while N > 1, the child `/pav-check` agent, the Validator of a serialized composite's child and
  the composite validation agent of 22 REQ-12; 23 REQ-01 makes the root orchestrator the only
  writer under `.ai/`), THE reviewing agent SHALL run `prepare` and `run` but never `record`, and
  SHALL return its review draft to the root; THE root orchestrator SHALL save that draft under
  `<task>/verification/drafts/` (DM-1) of the root worktree and run `record --draft` on it with
  the options the agent passed to `prepare`, so that the record is written under the root
  worktree's `<task>/verification/reviews/<scope key>/`. IF the returned draft is unusable
  (missing or not JSON, which `record` reports as `draft-invalid`; 23 REQ-56 also counts a draft naming a different `--work`, `--task` or `--ai-dir` as unusable) or `record` refuses it (exit 1,
  including `check-incomplete`), THEN the root SHALL write no record and apply the `Record:` rule
  of C-4: one correction by a fresh reviewing agent given the refusal reasons, and after a second
  unusable or refused draft, or `record` exiting 2, 3 or 4, a full review without the helper
  (A-33); what the root does when that review also fails (the `record-failed` block) is owned by
  spec 23 (23 REQ-56). WHEN the reviewing agent runs `record` itself (N = 1, the Validator
  running `record` as C-4 states), this requirement does not apply. Dispatch, the verdict and
  notes deltas, the DM-8 entry and the correction reply in parallel mode are owned by spec 23
  (23 REQ-55, REQ-56, C-6 rows 11 and 12).

### Delivery

- **REQ-49 Frozen checks.** THE delivered change SHALL pass the unchanged
  `scripts/validate-contracts.sh`, spec 11's `measure-context.sh check` and spec 09's
  `scripts/lint-instructions.py`, with no change to `scripts/validate-contracts.sh`, to any file
  under `tests/`, or to `tests/fixtures/validator-runtime/inventory-amendment.json`.
- **REQ-50 Golden regression.** THE delivered change SHALL pass spec 10's offline suite
  (`python3 -I tests/golden-runs.py`) with no change to its expected results.
- **REQ-51 Rule deployment.** THE delivered change SHALL register `rules/contract-verification.md`
  in the rule deployment mechanism current at delivery (today the rule lists of
  `scripts/setup-new-project.sh:89`, `:124` and `scripts/sync.sh:208`, `:218`).
- **REQ-52 Knowledge and decision.** THE delivered change SHALL update the files listed in C-8 and
  add an Accepted ADR indexed in `.ai/adr/index.md` recording the content named in C-8.
- **REQ-53 Audit proposals.** WHERE the spec 08 audit assessment exists at delivery, THE ADR of
  REQ-52 SHALL list every proposal it assigns to owner 15 (`review-repeat` by default,
  spec 08 DM-7 default owners, A-07) as implemented — only when the change falls
  within the C-8 files and this spec's requirements — or declined with a reason; WHERE it does not
  exist, THE ADR SHALL state that no audit proposal was available.
- **REQ-54 Standalone suite.** THE acceptance suite SHALL be `scripts/check-scoped-verification.py`,
  run directly, called by neither `scripts/validate-contracts.sh` nor `scripts/sync.sh`.

## Data Model

All entities are **new**. JSON is canonical JSON as in spec 13 (UTF-8, sorted keys,
`ensure_ascii=False`, separators `,` and `:`, one trailing LF). A digest is `sha256:` + 64
lowercase hex. Paths inside records are POSIX paths relative to the repository top-level
directory (`git rev-parse --show-toplevel` of `--work`), without `..` or a leading `/`.

### DM-1 Locations

| Location | Content | Writer | Lifecycle |
|---|---|---|---|
| `<git common dir>/orchestrail-verification/receipts/<inputs hex>/<receipt hex>.json` | DM-4 receipts, mode 0600 | `run` | Write-once; never removed by the helper; shared by all worktrees of the repository |
| `<git common dir>/orchestrail-verification/outputs/<sha256 hex>` | Captured stream bytes, mode 0600 | `run` | Write-once, content-addressed |
| `<task>/verification/reviews/<scope key>/<n>.json` | DM-7 records; a *record name* is a name matching `^[1-9][0-9]*\.json$`; task-level records of both steps share `reviews/task/` | `record` | Write-once |
| `<task>/verification/drafts/` | Reviewer drafts (any name) | Reviewer (N = 1); root (REQ-62) | Overwritable; never read except through `--draft` |

Directories are created with mode 0700 when absent. Temporary files are named `.tmp-<pid>-<16
random hex>` in the target directory and published by `os.link` (fails if the target exists) then
removal of the temporary name; readers ignore `.tmp-` names. `<git common dir>` is the absolute
result of `git rev-parse --path-format=absolute --git-common-dir` in `--work`. Deleting
`orchestrail-verification/` or `<task>/verification/` while no review runs is safe: it only removes
reuse and forces full scope. Migration: none; a task without records is reviewed in full.

**Excluded prefix.** When the task directory lies inside a work tree whose git common directory
equals that of `--work`, the excluded prefix is the task directory's path relative to *its own*
work tree top-level; the prefix is then excluded from `--work`'s tree in DM-3, DM-4 and DM-5 (so a
spec-23 child worktree excludes its copy of the root task directory). Otherwise nothing is
excluded.

### DM-2 Coverage plan (part of the `prepare` result)

Contract sources, in this order (label, then bytes digested; an absent source digests as `null`):

| Level | Sources |
|---|---|
| `leaf` | `task:<description path>` (whole file); `task:state.md → ## Solution Design → ### Decision`; `… → ### Invariants`; `… → ### Off-limits` |
| `task` (`flow: full` or absent) | `spec:<spec_path>` (whole file, `spec_path:` resolved against the parent of `AI_DIR`); `task:state.md → ## Solution Design → ### Decision`; `… → ### Acceptance Criteria`; `… → ### Invariants`; `… → ### Off-limits` |
| `task` (`flow: quick`) | `spec:<spec_path>`; `task:state.md → ## Contract (quick) → ### Acceptance Criteria`; `… → ### Invariants`; `… → ### Off-limits` |
| `composite` | `task:<composite description path>` (whole file); `task:state.md → ## Solution Design → ### Decision`; `… → ### Invariants`; `… → ### Off-limits` |

`contract_digest` = digest of the canonical JSON list `[[label, sha256-or-null], …]`.

Obligations: `AC-<n>` from the description's `## Acceptance Criteria` (leaf, composite) or the
task's `### Acceptance Criteria`; `INV-<n>` from `### Invariants`; `OFF-<n>` from `### Off-limits`;
`n` counts from 1 per kind in source order. Level `task` with step `review` has no obligations
(`[]`): `/pv-review` produces findings, not criterion judgements (`workflows/pv-review.md:35-59`).
Each obligation row:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `AC-1`, `INV-2`, `OFF-1`, … |
| `kind` | `acceptance`, `invariant`, `off-limits` | |
| `source` | string | The source label with heading path |
| `text_sha256` | digest | Of the item's bytes (C-3) |
| `unstructured` | boolean | True when the section had content but no list item (C-3) |

Checks: `defined` (list of `{"check", "reusable"}` in the order `test`, `lint`, `typecheck`),
`undefined` (names), `warnings` (list of strings, sorted: `runbook-missing`,
`reusable-unknown:<name>`, `no-acceptance-criteria`, `section-absent:<label>`).
Leaf only: `atomic_tests` = the leaf block's `atomic-tests:` value or `absent`.

### DM-3 Change manifest (`subject` in the `prepare` result and the record)

| Field | Type | Meaning |
|---|---|---|
| `base` | string or `null` | Full object name of `--base` (`git rev-parse --verify <base>^{commit}`) |
| `head` | string or `null` | `HEAD` object name; `null` on an unborn branch |
| `clean` | boolean | `git status --porcelain=v1 -z --untracked-files=all` lists no path outside the task directory |
| `entries` | list sorted by `path` | `{"status", "path", "sha256"}`; `status` ∈ `A`, `M`, `D`, `T` (from `git diff --no-renames --name-status <base> --`), `A` for an untracked non-ignored path (`git ls-files --others --exclude-standard`), `listed` for a `--listed` path not otherwise changed; `sha256` of the current bytes, or `null` when absent |
| `subject_digest` | digest | Of the canonical JSON of the four fields above |

`--listed` paths are absolute or relative to `--work`; the workflow passes each task-owned file
resolved against its own subtask's `working_dir:` (several `working_dir:` values inside one work
tree are therefore supported). Each must resolve inside the top-level directory of `--work`'s work
tree, else exit 2 `path-invalid`; it is recorded relative to that top-level. A symbolic link is digested as the bytes of its target
string. For a `D` entry, "read in full" (REQ-04) means reading its base content
(`git show <base>:<path>`).

### DM-4 Check receipt (`check_receipt`)

| Field | Type | Meaning |
|---|---|---|
| `schema_version`, `kind` | `1`, `"check_receipt"` | |
| `check` | `test`, `lint`, `typecheck` | |
| `command` | object | `argv` (list of strings), `argv0_path` (real path of `argv[0]` resolved through the helper's `PATH`, or `null`), `argv0_sha256` (digest of that file's bytes, or `null`), `cwd` (`--work` relative to the top-level directory, `.` for the top). When `argv[0]` does not resolve, the command is not started and `command_status` is `start-error` |
| `inputs` | object | `tree_digest`, `worktree_id` (spec 13's Data Model → Identifiers definition), `environment_digest`, `platform` (`system`, `release`, `machine` from Python's `platform` module), `inputs_digest` |
| `inputs_after` | object | `tree_digest` recomputed after the command ended |
| `command_status` | object | `{"kind": "exit", "code": <int>}`, `{"kind": "signal", "signal": <int>}`, `{"kind": "start-error", "detail": <string>}`, or — mode `capture-output` only — `{"kind": "aborted", "label": <spec 14 outcome label, or "unknown">}` (DM-4a mapping) |
| `output` | object | DM-4a. Mode `direct`: `{"mode": "direct", "capture_status": "complete"\|"failed", "stdout": S, "stderr": S, "fallback": <string or null>}` with `S` = `{"sha256", "bytes"}` or `null` when capture failed. Mode `capture-output`: `{"mode": "capture-output", "reference": <spec 14 DM-6 OUTPUT line or null>, "artifact_id": <32 hex or null>, "manifest_sha256": <hex or null>, "manifest": <object or null>}` where `manifest` copies exactly the spec 14 DM-2 keys `capture_status`, `command_status`, `purpose`, `argv_sha256`, `cwd`, `worktree`, `head`, `started_at`, `ended_at` |
| `reusable` | boolean | |
| `not_reusable_reasons` | sorted list | Subset of `not-declared`, `capture-failed`, `abnormal-exit`, `inputs-changed-during-run`, `unknown-input:submodule`, `unknown-input:unreadable`, `unknown-input:unmerged`, `unknown-input:path-encoding`, `unknown-input:nested-repository` |
| `created_at` | string | UTC, `YYYY-MM-DDTHH:MM:SSZ`; diagnostic only |
| `nonce` | string | 16 random lowercase hex characters, so that two runs never share a `receipt_id` |
| `receipt_id` | digest | Self-digest |

`tree_digest`: digest of the canonical JSON list, sorted by path bytes, of `[path, kind, executable,
sha256]` for every path printed by `git ls-files -z --cached --others --exclude-standard` run in the
top-level directory, excluding paths inside the task directory; `kind` is `file`, `symlink` or
`deleted`, `executable` a boolean (`false` unless a regular file with any execute bit), `sha256`
`null` for `deleted`. A gitlink entry, a nested repository (an `--others` entry ending in `/`), an
unreadable path, an unmerged index entry or a path that is not valid UTF-8 contributes
`[path, "unknown", false, null]` and adds the matching `unknown-input:*` reason.
`environment_digest`: digest over the byte string formed by sorting the helper process environment
by name and joining `name=value\0` for every variable except `PWD`, `OLDPWD`, `SHLVL` and `_`. Only the
digest is stored.
`inputs_digest`: digest of the canonical JSON of `check`, `command`, `inputs.tree_digest`,
`inputs.worktree_id`, `inputs.environment_digest` and `inputs.platform`.
`evidence` (derived, never stored): mode `direct` — `usable` when `capture_status` is `complete`,
`command_status.kind` is `exit`, both output files exist and their bytes match `sha256` and
`bytes`; mode `capture-output` — `usable` when `manifest.capture_status` is `complete`,
`command_status.kind` is `exit`, `manifest.argv_sha256` equals the SHA-256 of the canonical JSON
of `command.argv` (spec 14's DM-2 definition), `manifest.cwd` equals the real path of `--work`,
and `bash <capture helper> verify --reference "<reference>" --work <WORK_DIR>` exits 0 when the
evidence is evaluated (at reuse and at `record`); otherwise `unusable`.

### DM-4a Capture delegation (spec 14)

**Availability.** Spec 14's helper is available when `$ORCHESTRAIL_HOME/scripts/capture-output.sh`
is a readable regular file and `ORCHESTRAIL_OUTPUT_CAPTURE` is unset, empty or `on` (spec 14's
switch). Otherwise `run` uses mode `direct` with `fallback: "unavailable"` (file missing or
unreadable) or `"disabled"` (any other switch value).

**Invocation.** The executed child is `["bash", <absolute path of capture-output.sh>, "run",
"--purpose", <test for test, lint for lint and typecheck>, "--", "bash", "-c", <runbook value>]`
in `WORK_DIR` with the helper's environment and no `--timeout-seconds` or `--limit-bytes`
(spec 14's Capture line and defaults). `command` in the receipt stays the check's own vector
`["bash", "-c", <runbook value>]`, so the inputs digest is the same in both modes when the environment is identical; `ORCHESTRAIL_HOME` and `ORCHESTRAIL_OUTPUT_CAPTURE` are part of the environment digest (DM-4), so changing either changes the digest. The capture
helper's standard output and standard error are held in memory only to classify the case; they
are not stored.

**Time limit.** `run` passes no `--timeout-seconds`: the helper cannot know the limit of the shell
call that runs it, and this spec invents no number (A-20, A-35). Spec 14's Capture-line timeout
rule governs a worker's own shell call and does not bind this helper (spec 14 C-7 row 15); the
limit of the worker's outer call applies to the whole `run`. Consequence: when that call is killed,
this spec's `run` process dies with spec 14's helper, so no receipt is published and nothing
classifies case C; the worker sees no `run` result, the check's outcome is unknown, and the
reviewer treats it as a check that lost its output under C-4 `Checks:` (blocker, no rerun in this
review, REQ-59's rule applied by the reviewer). A worker may run the helper's `run` in a background shell call without a
limit, as spec 14's Capture line allows for long commands; no change to the helper is needed.

**Case lettering.** The letters are spec 14's C-7 row 15 mapping, unchanged: a published artifact
is case B whatever the exit status; a non-`complete` published artifact is case B with unusable
evidence; no artifact, or a failing `verify`, is case C; a refusal is case A.

| Case | Recognized by | Receipt |
|---|---|---|
| A — refused before start | Checked after case B. Exit 125, empty standard output, and a standard-error line matching `^capture-output: ([a-z-]+): started=no: `; or exit 126/127 with empty standard output and no `capture-output:` line on standard error (bash could not open the helper) | No receipt for this attempt; `run` executes the check in mode `direct` and records `fallback: <code>` (`unavailable` for the bash case). Codes include `git-command-refused`, `log-step-refused`, `disabled`, `store-unsafe`, `store-unavailable`, `not-a-git-repository`, `platform-unsupported`, `python-unavailable`, `usage`, `limit-too-small` |
| B — artifact published | Checked first, whatever the exit status (spec 14 C-2 passes the child's status through, so a command not found inside `bash -c` exits 127 here and is case B). First line `capture: v1 <id>` and last line a spec 14 DM-6 OUTPUT line for that id | Mode `capture-output` with `reference`, `artifact_id`, `manifest_sha256` and the `manifest` copy read from `<git common dir>/orchestrail-output/<id>/manifest.json`; `command_status` mapped from the manifest: kind `exit` → `exit` with `exit_code`; `signal` → `signal`; `launch-error` → `start-error` with the label as `detail`; `timeout`, `interrupted` → `aborted` with the label. Reasons: `capture-failed` when `capture_status` is not `complete`; `abnormal-exit` when the kind is not `exit` |
| C — anything else | Any other combination (for example `capture: v1 unpublished`, `OUTPUT none — <code>`, no `capture: v1` line, or a `verify` failure right after publication) | Mode `capture-output` with `reference`, `artifact_id`, `manifest_sha256` and `manifest` `null` (or the values read, when only `verify` failed), `command_status` `{"kind": "aborted", "label": "unknown"}`, reasons `capture-failed` and `abnormal-exit`; the command is not run again in this review (spec 14's `Not started:` rule) |

A review never reads spec 14's preview as evidence through this helper; the reviewer reads and
cites the captured output by the `reference` line under spec 14's `## Reading output` and
`## Evidence` rules. Spec 15 keeps the inputs digest, the reuse decision (DM-6) and the review
record. Spec 14's helper refuses every argument holding a git or gh word; case A turns that into
a direct run, exactly as spec 14's rule tells a worker to run such a command directly.

### DM-5 Recheck plan (`recheck` in the `prepare` result)

| Field | Type | Meaning |
|---|---|---|
| `prior` | object or `null` | `{"path", "file_sha256", "record_digest", "seq", "verdict"}` of the selected valid prior record, eligible or not; `null` when none is selected |
| `minimum_scope` | scope | See below |
| `reasons` | sorted list | Closed set below; empty when `finding-led` |
| `fix_diff` | list sorted by path | `{"status", "path", "sha256"}` from `git diff --no-renames --name-status <prior head> --` plus untracked non-ignored paths, excluding the task directory; computed whenever a prior is selected and its head exists, else `[]` |
| `open_findings` | list | Ids of the selected prior record's findings with status `open` or `owner-decision`, at every level and whatever the minimum scope |
| `rereview` | list | `{"id", "why"}` for obligations of the current plan; `why` ∈ `evidence-changed`, `prior-not-met`, `finding-linked`, `no-evidence-paths`, `new-obligation`; computed only when `minimum_scope` is `finding-led`, else `[]` |
| `carry_eligible` | list | Obligation ids not in `rereview` whose prior state was `verified` or `carried` and whose every evidence path has the same current digest as recorded; computed only when `minimum_scope` is `finding-led`, else `[]` |

**Selection.** Scan the record names of `reviews/<scope key>/` in descending `n`. A file that
cannot be read or is not a valid DM-7 record sets reason `prior-record-invalid` and the scan
continues; a valid record of another step is skipped; the first valid record of the requested
step is the prior, which supplies `prior` and `open_findings` even when an invalid file was met
above it. No record name, or no valid record of the step → `prior: null` and, unless
`prior-record-invalid` was set, reason `no-prior-record`.

**Eligibility** for `finding-led` (level `leaf` or `task` only). When `prior-record-invalid` was set
or no prior was selected, `reasons` holds only that reason or `no-prior-record`. Otherwise every
failing
condition among (2)–(7) is listed, sorted: (2) REQ-12 marker matches — else
`prior-not-latest`; (3) for a leaf, prior verdict `NEEDS WORK` — else `prior-accepted`; (4) prior
`subject.clean` is true — else `prior-subject-dirty`; (5) prior `subject.head` exists
(`git cat-file -e <head>^{commit}`) — else `prior-subject-unavailable`; (6) contracts equal per
REQ-13 — else `contract-changed`; (7) for a leaf, no cross-leaf path per REQ-14 — else
`cross-leaf-change`. For (7), each other leaf's `target_files:` entries are resolved against that
leaf's own `working_dir:` (the first `working_dir:` line in `## Context` of the single
`<task>/<id>-*/description.md`, relative to that description's directory; `--work` when absent)
and count only when they resolve inside `--work`'s work tree. When all hold, `minimum_scope` is `finding-led`; otherwise `full-leaf` (leaf)
or `full-task` (task). Level `composite` always yields `full-integration` with reason
`merged-result`. Scope order: `finding-led` < `full-leaf` = `full-task` = `full-integration`; a
full scope must match the level (`full-leaf` for leaf, `full-task` for task,
`full-integration` for composite).

### DM-6 Reuse decision (`run --reuse`)

A stored receipt is reused only when all hold: (1) the receipt directory equals the current
`inputs_digest`; (2) its file name equals its `receipt_id` hex and its self-digest verifies;
(3) `schema_version` is 1 and `kind` is `check_receipt`; (4) `reusable` is true; (5) its evidence is
`usable`; (6) the check is listed in the current runbook `reusable:` line; (7) every other receipt
passing (1)–(5) for the same inputs has an equal `command_status`; (8) the `receipt_id` is
referenced in `checks` by at least one published review record of the same task directory (so
only results that a review has already relied on are reused). Among qualifying receipts the one
with the lexicographically smallest `receipt_id` is reused. A receipt failing (2), (3) or the byte
check or `verify` of (5) is reported `receipt-damaged`; failing (7) reports `conflicting-receipts`; failing
(6) reports `not-declared`; failing (8) reports `not-referenced`; a mode `capture-output` receipt
whose evidence cannot be evaluated because `$ORCHESTRAIL_HOME/scripts/capture-output.sh` is not a
readable regular file (whatever `ORCHESTRAIL_OUTPUT_CAPTURE` says: spec 14 keeps `verify` working
when capture is off) reports `capture-unverifiable` and is not reused; one whose `verify` fails
reports `receipt-damaged`. A reused failing result stays failing.

### DM-7 Review record (`review_record`) and draft

The reviewer writes a draft with the fields marked **draft**; `record` copies them, adds the
others from its own recomputation, and validates.

| Field | Source | Meaning |
|---|---|---|
| `schema_version`, `kind` | helper | `1`, `"review_record"` |
| `level`, `step`, `scope_key` | draft | Must equal the invocation |
| `seq` | helper | The `n` of the file name |
| `preparation_digest` | draft | Self-digest of the `prepare` result the reviewer used |
| `tier` | draft | `standard` |
| `scope` | draft | A scope not narrower than `minimum_scope` |
| `minimum_scope`, `expansion_reasons` | helper | From the recomputed preparation; plus `reviewer-widened` when `scope` is full and `minimum_scope` is `finding-led` |
| `subject`, `contract`, `recheck` | helper | DM-3; `{"contract_digest", "sources", "task_contract_hash", "packet_digest"}`; DM-5 |
| `obligations` | draft + helper | Draft: `{"id", "state", "method", "evidence_paths", "risks", "note"}`; `state` ∈ `verified`, `carried`, `unverified`, `failed`; `method` sorted subset of `inspection`, `check:test`, `check:lint`, `check:typecheck`; `risks` sorted subset of `contract`, `security`, `data-integrity`, `migration`, `shared-dependency`, `uncertain`; helper adds `kind`, `text_sha256`, each evidence path's current `sha256`; for `carried` the draft's `evidence_paths` must be `[]` and the helper copies the prior record's evidence paths with their recorded digests and sets `carried_from` to the prior `seq` |
| `checks` | draft + helper | Draft: `{"check", "receipt_id"}` per defined check; helper adds `command_status` and `evidence` from the receipt and `action`: `reused` when an earlier published record of the same task directory references the same `receipt_id`, else `executed` |
| `reviewed_paths` | draft | Sorted paths the reviewer read in full |
| `interface_impact` | draft | `finding-led` only: one `{"path", "classification"}` per fix-diff path; `classification` ∈ `none`, `interface-change`, `invariant-change`, `unknown` |
| `tdd_audit` | draft | `{"atomic_tests", "outcome"}`; `outcome` ∈ `performed`, `not-applicable` |
| `findings` | draft | `{"id", "severity", "title", "obligations", "locations", "evidence", "status", "same_as", "check", "decision"}`; `status` ∈ `open`, `owner-decision` for a new finding, and additionally `resolved`, `withdrawn`, `owner-accepted` for an id carried from the prior record; `locations` list of `{"path", "line"}` (`line` integer or `null`); `check` a check name or `null`; `decision` (DM-7a) when status is `owner-accepted`, else `null` |
| `outcomes` | draft | One `{"finding", "outcome", "evidence", "decision"}` per id in `open_findings`; `outcome` ∈ `resolved`, `remains`, `withdrawn`, `owner-decision`, `owner-accepted`; `decision` as for findings |
| `verdict` | draft | `DONE` or `NEEDS WORK` for leaf and composite; `null` for task |
| `created_at`, `record_digest` | helper | UTC time (diagnostic); self-digest |

Validation rules applied by `record` (refusal reason in brackets):
- R-01 Draft parses as JSON with exactly the draft fields and valid closed values [`draft-invalid`].
- R-02 Recomputed preparation digest equals `preparation_digest` [`preparation-stale`].
- R-03 Obligations equal the plan's ids, each once, valid states [`obligations-mismatch`].
- R-04 `carried` only in `finding-led` and only for `carry_eligible` ids [`carry-invalid`].
- R-05 Every `open_findings` id has exactly one outcome; `withdrawn` has non-empty evidence
  [`prior-outcome-missing`, `withdrawal-unjustified`]. An outcome `remains` or `owner-decision`
  requires the same id in `findings` with status `open` or `owner-decision`; `resolved`,
  `withdrawn` or `owner-accepted` requires that id absent from `findings` or present with the same
  status; `owner-accepted` requires a `decision` [`owner-decision-unreferenced`].
- R-06 New finding ids follow REQ-29; `same_as` resolves; a new finding has status `open` or
  `owner-decision` [`finding-id-invalid`].
- R-06a Every `owner-accepted` outcome or status carries a DM-7a `decision` that resolves
  [`owner-decision-unreferenced`].

- R-07 Scope rules of REQ-30 and REQ-04 [`scope-too-narrow`, `coverage-incomplete`].
- R-08 Verdict (leaf, composite): `DONE` iff every obligation is `verified` or `carried`, no finding
  of severity `critical` or `important` has status `open` or `owner-decision` (an `owner-accepted`
  finding does not block), and every defined check's receipt has exit code 0
  [`verdict-inconsistent`]. Task drafts carry `null` [`verdict-inconsistent`].
- R-09 Every non-zero receipt is named by a `critical` or `important` finding
  [`check-failure-unreported`].
- R-10 No referenced receipt is abnormal or unusable [`check-incomplete`].
- R-11 Every defined check is referenced by a receipt whose `inputs_digest` equals the current
  inputs digest [`check-missing`].
- R-12 `tier` is `standard` [`tier-invalid`]; `tdd_audit` per REQ-33 [`tdd-audit-invalid`].
**DM-7a Decision reference.** `decision` is `task:state.md:<line>` or `ai:adr/<file>.md:<line>`
(`<file>.md` an ADR file directly under `AI_DIR/adr/`), with `<line>` a 1-based line number. It
resolves only when the file and line exist, the line contains the finding id, and — for
`task:state.md` — the line lies inside one of the decision sections
`## Task Analysis → ### Assumptions`, `## Issue List → ### Deferred` or `## Open Questions (batch)`.
Every other location — drafts, records, `## Subtask Progress`, `## Contract Check`,
`## Code Review`, `## Improvement Proposals (…)`, any other file — does not resolve, because a
reviewing role can write it. A `decision` value outside this grammar is reported
`owner-decision-unreferenced` (not `draft-invalid`).

All failing rules are reported together, sorted; an acceptance criterion that says a draft "is
refused `X`" asserts that `X` is among the reported reasons.

### DM-8 Notes entry

`verification: review <scope key> <step> #<seq> <scope> sha256:<file hex>` after a published record,
where `<file hex>` is the SHA-256 of the record file's bytes; `verification: review <scope key>
<step> none — <reason>` after a review without a record. Reasons:

| Cause | `<reason>` |
|---|---|
| `ORCHESTRAIL_HOME` unset, helper unreadable, `version` not exiting 0, exit 4 `runtime-unavailable` or `not-a-repository` | `unavailable` |
| Exit 4 `disabled` | `disabled` |
| Exit 2, exit 3, exit 4 `interrupted`, or the `Record:` attempts of C-4 end without publication | `helper-error` |
| The review's files lie in more than one git work tree (their `working_dir:` real paths have different `git rev-parse --show-toplevel` results) | `multi-repository` |
| A defined check cannot complete (REQ-55 blocker) | `blocked` |

Location and order: leaf → appended as the last entry of the leaf block's notes, after every
verdict note of the same review, to the end of the last line of the last `notes` field group with
spec 12's append rule (12 DM-11); task → the last line of
`## Contract Check` (step `contract`) or `## Code Review` (step `review`); composite → the
composite block's notes in the same way (a delta under `/spec-run`). Reading uses spec 13's note
entry parsing rule (`.ai/specs/13-orchestrator-overhead.md`, Data Model → Note entries): every `notes` field group and
its continuation lines, split on `; `; the *last DM-8 entry* is the last entry, in file order,
that starts with `verification: review <scope key> <step> `. Pattern:
`^verification: review (T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?|task) (check|contract|review|integration) (#[1-9][0-9]* (finding-led|full-leaf|full-task|full-integration) sha256:[0-9a-f]{64}|none — (unavailable|disabled|helper-error|multi-repository|blocked))$`.
Entries are not protected sections; a removed entry makes the next preparation full
(`prior-not-latest`).

### DM-9 Runbook declaration

Optional line inside the runbook's `## Commands` section: `reusable: <check>[, <check>]…`. Only
the first line of the section starting with `reusable:` counts; its value (the rest of the line)
is split on `,`, each piece trimmed of spaces and tabs, empty pieces and repeats ignored; a piece
other than `test`, `lint` or `typecheck` yields warning `reusable-unknown:<piece>`. An empty value
means no check is reusable. The template line is exactly `reusable:` (empty). A check value is
read from the first line of the section starting with `<name>:`; the value is the rest of the line
with surrounding whitespace removed. A check is defined when the value is non-empty and does not
start with `<` or `(`. The runbook is `AI_DIR/context/runbook.md`; the umbrella runbook is not
read. `build:` is never a check.

### DM-10 Result line and errors

One line of canonical JSON without trailing spaces: `{"ok": true|false, "subcommand": …, …}`.
`prepare` adds `preparation` (the full preparation object: `schema_version` 1,
`kind: "review_preparation"`, `level`, `step`, `scope_key`, `contract`, `obligations`, `checks`,
`atomic_tests`, `subject`, `recheck`, `preparation_digest`). `run` adds `check`, `action`
(`executed` or `reused`), `receipt_id`, `receipt_path`, `command_status`, `evidence`, `reusable`,
`not_reusable_reasons`, `reuse_refused` (sorted reasons: `not-declared`, `no-receipt`,
`not-referenced`, `receipt-damaged:<file>`, `capture-unverifiable`, `conflicting-receipts`, `disabled-by-flag` when
`--reuse` was absent; `[]` when reused),
`stdout_path`, `stderr_path` (mode `direct`; `null` in mode `capture-output`), `output_reference`
(the spec 14 OUTPUT line in mode `capture-output`, else `null`). `record` adds `record_path`, `file_sha256`, `seq`, or on refusal
`reasons`. Failure lines carry `error` (code) and `detail`.

## Contracts & Interfaces

### C-1 Command line

```text
python3 -I "$ORCHESTRAIL_HOME/scripts/scoped-verification.py" version
python3 -I … prepare --level leaf|task|composite --scope-key <key> [--step contract|review]
    --task <task dir> --work <WORK_DIR> [--ai-dir <AI_DIR>] [--description <path>]
    [--base <commit>] [--listed <path>]... [--task-contract-hash <digest>] [--packet-digest <digest>]
python3 -I … run --check test|lint|typecheck --task <task dir> --work <WORK_DIR>
    [--ai-dir <AI_DIR>] [--reuse]
python3 -I … record --draft <path> <the same options as prepare>
```

`--ai-dir` defaults to `<work>/.ai`. `--step` is required for `task` and forbidden otherwise (leaf →
`check`, composite → `integration`). `--description` is required for `leaf` and `composite`.
`--scope-key` must be `task` for level `task` and match 13's `leaf_id` pattern otherwise. Argument
errors exit 2 `usage`. `version` prints `{"ok": true, "subcommand": "version", "schema_version": 1}`.

### C-2 Exit codes and error codes

| Exit | Meaning | Error codes |
|---|---|---|
| 0 | Success: preparation printed; check executed or reused (whatever its own status); record published | — |
| 1 | Draft refused | `record-refused` with `reasons` (DM-7) |
| 2 | Invalid input | `usage`, `path-invalid`, `base-invalid`, `check-undefined`, `contract-ambiguous` (a required heading occurs more than once), `state-unreadable` |
| 3 | Store or record conflict | `store-unwritable`, `record-conflict` |
| 4 | No result | `disabled`, `runtime-unavailable`, `not-a-repository`, `interrupted` |

### C-3 Parsing rules

- **Headings:** ATX headings outside fenced code blocks (fences of three or more backticks or
  tildes). A section extends from its heading line to the line before the next heading of the same
  or a higher level. `### X` under `## Y` means the single `### X` inside `## Y`'s extent; a second
  match → `contract-ambiguous`.
- **List items:** a top-level item starts at column 0 with `- `, `* `, `+ `, `<digits>. ` or
  `<digits>) ` (a `- [ ] `/`- [x] ` checkbox included) and continues over following lines that are
  blank or indented, until the next top-level item or a non-indented non-item line. Item bytes =
  its lines with trailing whitespace removed, joined by `\n`, trailing blank lines dropped. A
  section with non-blank content and no item yields one obligation with `unstructured: true` whose
  bytes are the whole section body under the same normalization.
- **Leaf blocks:** inside `## Subtask Progress`, a block starts at a line beginning with `<id> | `
  or `[composite] <id> | ` and includes the following lines that start with two spaces; fields
  are read by name (`atomic-tests:` from the header line, `target_files:` and `notes:` from the
  indented lines). `target_files:` is split on `,` and trimmed; entries resolve as DM-5 (7) states.
- **Notes entries:** read and appended as DM-8 defines (spec 13's note-entry parsing rule and
  spec 12's append rule).

### C-4 `rules/contract-verification.md`

Front matter: `description: Scoped verification — coverage, checks, reuse, records and recheck`,
`load: on-demand`. Sections and anchored lines, verbatim, one line each:

`## Review procedure`

```text
Availability: use the scoped-verification helper only when ORCHESTRAIL_HOME is set, the helper is readable and its version subcommand exits 0, and only when every file of the review lies in the git work tree of --work; otherwise, or when any subcommand exits 2, 3 or 4, review the full scope without it, run the defined checks directly, and append the verification none entry with its reason.
Order: run every defined check with run --reuse, then prepare, then review, then record, then write the verdict to state, and append the verification entry last; never run build. In the cases of REQ-62 the reviewer stops after review and returns the draft; record and the state writes belong to the root (23 REQ-55).
Obligations: every obligation prepare lists ends verified, carried, unverified or failed; only verified or carried counts as met.
Checks: with or without the helper, a defined test, lint or typecheck check that exits non-zero is a finding of at least important severity naming that check; a defined check that cannot start, is ended by a signal or loses its captured output is a blocker: set blocker:, write no verdict, append the none entry with reason blocked, and stop.
Mutation: when run reports inputs-changed-during-run, run that check once more; if it reports it again, finish without the helper.
Record: at N = 1 the reviewer runs record; in the cases of REQ-62 the reviewer returns a draft and the root runs record. A refused record is not a verdict; correct the draft or widen the scope and record once more; a second refusal in the same review ends the helper path, and the review is then performed in full without it.
Tier: the only verification tier is standard; any other tier needs a recorded owner decision backed by an independent comparison.
```

`## Reviewer inputs`

```text
Reviewer inputs: before a verdict read every obligation, the complete change manifest, every changed path in full, the evidence paths each judged obligation relies on, the test files and tdd notes, and for a recheck the prior review record; never read or request the Implementer's reasoning, report or self-assessment.
```

`## Reuse`

```text
Reuse: only the helper decides reuse, for identical inputs; a refused, damaged or conflicting receipt means the check runs again.
Declaration: list a check in reusable: only when its result depends on nothing but non-ignored repository files outside the task directory, the command and the process environment.
```

`## Recheck`

```text
Recheck: in a finding-led scope give every open prior finding exactly one outcome, review every fix-diff path and every obligation prepare lists for re-review, and carry only carry-eligible obligations.
Expansion: use the full scope when prepare requires it or when any fix-diff path changes an interface or a shared invariant or has unknown impact; you may widen, never narrow.
Merged results: review a composite in full on its current combined tree; a child's verdict never stands for it.
```

### C-5 Workflow and rule edits (additive, except the three replaced sentences listed below)

| File | Edit |
|---|---|
| `workflows/pav-check.md` | One paragraph after `## Context Bootstrap` citing `` `contract-verification → ## Review procedure` `` with the leaf `prepare` arguments (`--scope-key <T-XX>`, `--description`, `--base <base_commit>` when recorded, `--listed` for each `target_files:` entry, `--task-contract-hash`/`--packet-digest` when a spec-12 packet was used); step 5 runs the defined `test`, `lint` and `typecheck` checks "through `run --reuse` when the helper is available" and applies the C-4 `Checks:` line in both cases; before the verdict paragraph, "publish the record"; after the verdict writes, "append the DM-8 entry as the last entry of this leaf's notes", and the NEEDS WORK notes of `workflows/pav-check.md:106` are appended with spec 12's append rule rather than replacing `notes:`; the Check report fills `Scope: <scope> (minimum <minimum_scope>; <reasons>)`, `Verified obligations` (ids `verified` or `carried`), `Unverified obligations` (ids `unverified` or `failed`) and an `Evidence` line for the record file in spec 11's DM-7 form with scope `file` and format `text@1` |
| `workflows/pv-contract.md`, `workflows/pv-review.md` | The same at level `task`, steps `contract`/`review`, `--listed` from the file set each already uses; the DM-8 entry is the last line of the upserted section |
| `/pav-check`, `/pv-contract`, `/pv-review`, `/phase-composite-validation` | Each also contains, verbatim: "Without the helper, or when it exits 2, 3 or 4, perform this review in full, run the defined checks directly, and append the `none` verification entry with its reason." |
| `workflows/pav-check.md:47-49` (replaced) | The first sentence "Run the applicable `test:` and `lint:` commands from the resolved runbook in `WORK_DIR`." becomes "Run the applicable `test:`, `lint:` and `typecheck:` commands from the resolved runbook in `WORK_DIR`." (the three check kinds of Terminology → Check). The sentence "Missing commands, unavailable dependencies, or incomplete runs are reported as evidence gaps; do not claim a passing verification that did not run." — together with spec 14's C-5 row 3a addition to it, when 14 was delivered first (roadmap order 14 then 15, so this edit comes second) — becomes "Run each defined check through the scoped-verification helper's `run --reuse` when it is available (it captures through `contract-output → ## Capture` itself); otherwise run it through `contract-output → ## Capture`, or directly when that helper is absent too. Read results per `contract-output → ## Reading output` and cite them per `contract-output → ## Evidence`, or by the receipt's output files for a direct run. An undefined command is reported as an evidence gap; a defined check is classified by `contract-verification → ## Review procedure` (`Checks:`), so a dependency missing inside the command, which exits non-zero, is a finding; do not claim a passing verification that did not run." Spec 14 is a delivery prerequisite of this spec (roadmap order), so no variant without it is specified |
| `workflows/phase-composite-validation.md:21-22` (replaced) | "Run relevant tests and lint from the corresponding service runbooks; report unavailable checks." — with spec 14's C-5 row 5 addition when present — becomes "Run the defined checks from the corresponding service runbooks through the scoped-verification helper's `run --reuse` when it is available, otherwise through `contract-output → ## Capture`; report undefined checks as evidence gaps and classify defined checks by `contract-verification → ## Review procedure` (`Checks:`)." Spec 14 is a delivery prerequisite, so no variant without it is specified |
| Blocker writes (REQ-55) | `/pav-check`: set the leaf block's `blocker: verification check <name> could not complete — <detail>`, leave `atomic-validation:` unchanged (`in-progress`), write no verdict, append `none — blocked`, and **stop** with that message. `/phase-composite-validation`: the same `blocker:` text in the composite block, `integration-validation:` left `in-progress` (deltas under `/spec-run`), then **stop**. `/pv-contract`, `/pv-review`: upsert the step's section (`## Contract Check` or `## Code Review`) holding only the line `blocked: verification check <name> could not complete — <detail>` followed by the `none — blocked` entry, then **stop**; `/phase-validation` propagates the stop (`workflows/phase-validation.md:101`) |
| Blocker reset and resume (REQ-56) | `/pav-check` and `/phase-composite-validation`: before running checks, when the block's `blocker:` value starts with `verification check `, set it to `none` (a delta under `/spec-run` for the composite). `/phase-validation` resume paragraph (`workflows/phase-validation.md:69-77`): a `## Contract Check` or `## Code Review` section whose first non-blank body line starts with `blocked: verification check ` is partial output and resumes its writer. `/pv-review` Guard: **stop** with "Step 1 (`/pv-contract`) is blocked by a verification check; resolve it and re-run `/pv-contract`." when `## Contract Check` holds such a line |
| `workflows/pv-issues.md` | Item template gains `Findings: <ids>` after `Priority:` when records exist |
| `workflows/pv-execute-fixes.md` step 4, `workflows/phase-validation.md` quick paragraph | One sentence citing `` `contract-verification → ## Recheck` `` |
| `workflows/phase-composite-validation.md` | One paragraph citing the review procedure at level `composite` (`--scope-key` composite id, `--description` composite description, `--listed` the integration surface it already computes); the DM-8 entry goes into the composite block notes, as a delta under `/spec-run` |
| `workflows/spec-run.md` step 4.3; `rules/orchestration.md` `### Validator` | Each gains exactly the sentence "The Validator's inputs follow `contract-verification → ## Reviewer inputs`." (no load or read verb, so spec 11's textual-load detector, `.ai/specs/11-context-tiering.md`, Contracts & Interfaces → Textual load command detection, raises nothing and no `loads:` entry is added to these two files) |
| `rules/orchestration.md` `## Shared-file discipline` | Exactly the sentence "Review records and check receipts are write-once files that the reviewing role creates through the scoped-verification helper; they are not shared files." |
| `loads:` declarations (spec 11) | In spec 11's DM-1 grammar: one entry `- path: rules/contract-verification.md` (no `sections`) appended to the `mandatory` list of each of `/pav-check`, `/pv-contract`, `/pv-review`, `/phase-composite-validation`, `/pv-execute-fixes` and `/phase-validation`; the rule's front matter is `load: on-demand`; the whole file, front matter included, stays within 11 REQ-01's 700 words (this spec's NFR-05). The `contract-output` entries that the replaced sentences' citations need are added by spec 14's delivery (14 REQ-54), not here |

The three replaced sentences (both `workflows/pav-check.md` step 5 sentences and the
`workflows/phase-composite-validation.md` check sentence) are read by no frozen check (checked at
this revision: none matches a pattern in `scripts/validate-contracts.sh`). Every edit above is a section, a quoted sentence, an
anchored line or a `loads:` entry, so it survives spec 09's renames; the `file:line` coordinates are
today's and only locate the text.

Constraints from frozen checks: keep every phrase those checks read (Context fact 9); add no line
matching `call ./phase-composite-validation`; in `/pav-check` and `/phase-composite-validation` add no
line in which a write verb precedes `plan.md`, `architecture.md`, `.ai/memory/state.md` or
`.ai/project_state.md` (`scripts/validate-contracts.sh:1541-1548`).

### C-6 Contracts exposed to and consumed from other specs

| Spec | Relationship |
|---|---|
| 05 | Exposed: review records (DM-7) as facts — scope, expansion reasons, check actions, receipt ids. No 05 object is emitted; any 05 mapping is 05's adapter |
| 10 | Exposed: records inside captured task directories; the switch `ORCHESTRAIL_SCOPED_VERIFICATION=off` gives the full-review arm for strategy comparison. Consumed: the offline suite (REQ-50). Every claim of equal quality or saving belongs to 10 |
| 23 | Exposed: receipts bound to content and worktree, never to branch names or commits. 22 REQ-03 post-merge commands always run and never consult a receipt; this spec does not govern them. A receipt made in a child worktree never stands for the merged tree, because `worktree_id` is an input (A-05, DM-4); only the checks of the 22 REQ-12 composite review, run in the root worktree, may reuse a receipt, and only when REQ-05's conditions hold. That review is always `full-integration` (REQ-15); its DM-1 records are written under `<task>/verification/reviews/<scope key>/` as resolved in the root worktree, where 22 REQ-12 runs that review (the record location is owned here, not by spec 23). Receipt reuse matches 23 A-28. In spec 23's parallel mode (N > 1) the root is the only writer under `.ai/` (23 REQ-01), so the root runs `record` on the draft the reviewing agent returns (the cases are those of 23 REQ-55, stated by REQ-62), which resolves 23 Q-03 (owner decision D-02, REQ-62, A-36); the root's handling is 23 REQ-55 and REQ-56, with the report in 23 C-6 row 11 and the correction reply in 23 C-6 row 12; an unusable or refused draft follows the `Record:` rule (one correction, then a full review without the helper), so no new error code is needed |
| 12 | Consumed: the validator packet as the reviewer's context; `task_contract_hash` and `packet_digest` passed to `prepare` and recorded. Exposed: sufficiency — the reviewer additionally reads the diff content, untracked files, the runbook, evidence paths, tdd notes and the prior record (C-4 `## Reviewer inputs`). Receipts are not bound to packet digests: a check result depends on repository content, not on rendered context |
| 13 | Consumed: the note-entry parsing rule, canonical JSON and `worktree_id` definitions. Not consumed: the `green` messages and `red`/`pinned` receipts 13 C-10 offers — passing any Implementer report, checkpoint message, proposal, receipt or journal path to a Validator would contradict 13 REQ-30, and the reviewer re-derives the same facts (test paths and digests, commits) from git and its own leaf block, which is the more independent source. Validator inputs therefore stay those of `workflows/spec-run.md:284-292` plus C-4 `## Reviewer inputs`; 13 needs no amendment |
| 14 | Consumed: the capture helper `run` and `verify`, the DM-2 manifest keys `capture_status`, `command_status`, `purpose`, `argv_sha256`, `cwd`, `worktree`, `head`, `started_at`, `ended_at`, the DM-6 OUTPUT reference, the C-1 `run`/`verify` command lines, the C-2 refusal form, the DM-1 `manifest.json` location and the DM-4.1 first and last preview lines (DM-4a); 14's C-7 row 15 offers the manifest keys and `verify`, and the rest is cited from those sections. 15 owns the inputs digest, reuse and records; 14 owns capture, previews, retrieval and integrity. 15's C-5 replaced sentences supersede 14's C-5 rows 3a and 5 (REQ-60); 14's row 3b (the `green` TDD check) is unaffected. Settles 14 Q-05 and this spec's former Q-04 |
| 16 | Offered, not consumed: `tier` (only `standard`), per-obligation `risks`, `scope` and `expansion_reasons`; spec 16's policy version 1 reads none of them (16 C-6 row 15), and nothing here depends on 16 using them |
| 17 | Exposed, under these names: the leaf record `reviews/<leaf>/<seq>.json` (DM-1, DM-7) with `schema_version`, `kind`, `level`, `step`, `scope_key`, `seq`, `record_digest`, `verdict`, `contract.contract_digest`, `subject.head`, `scope`, `minimum_scope`, `findings[]` (`id`, `severity`, `title`, `evidence`, `status`, `obligations`, `locations`, `check`, `same_as`, `decision`), `obligations[]` (`id`, `kind`, `state`, `risks`), `outcomes[]` (`finding`, `outcome`), `checks[]` (`check`, `receipt_id`) and, in each referenced DM-4 receipt, the `output` object — `output.stdout`/`output.stderr` `{sha256, bytes}` in mode `direct`, `output.reference`, `output.artifact_id` and `output.manifest_sha256` in mode `capture-output` (no stream digests exist in that mode), the DM-8 entries (including `none — blocked`), the REQ-56 `verification check ` blocker prefix, the DM-7a decision sections and the C-3 parsing rules. Spec 17 overrides its Validator's draft classes from these fields and requires a published record before any repair. While 17's bounded loop defers the NEEDS WORK stop, every recheck is an ordinary leaf review under this spec by a fresh Validator: its prior is the record the attempt answered, finding-led eligibility and outcomes follow DM-5 and R-05, and 15 itself neither ends nor removes that stop. Not owned here: classification for repair, repair contracts, attempts, episodes, progress judgement, escalation and every change to the NEEDS WORK stop |
| 18 | Exposed: per-leaf and per-composite records at `<task>/verification/reviews/<id>/<n>.json` (DM-1 record names, DM-7) — record count, `scope` values (`finding-led`, `full-leaf`, `full-task`, `full-integration`) and `checks[].action` (`executed`, `reused`) — plus the C-3 parsing rules and DM-2 `INV-<n>` numbering |
| 07 | None |

### C-7 Acceptance suite

`python3 -I scripts/check-scoped-verification.py` is a standard-library Python 3.11+ `unittest`
program. It creates fixtures under a temporary directory with isolated `HOME`, `XDG_CONFIG_HOME`
and `GIT_CONFIG_NOSYSTEM=1`, runs the helper as a subprocess (and imports it by path only for the
version guard of AC-24), reads this repository's rules and workflows read-only for text cases,
never touches the real home or this repository's `.git`, and exits 0 only when every case passes.

**Fixture V1.** `git init R`; the first commit contains every file below, `.ai/` included
(tracked, as in this repository):

- `src/a.py` (`def f():\n    return 1\n`), `src/b.py` (`B = 1\n`), `tests/test_a.py`
  (`from src.a import f\n`), `.gitignore` with the lines `/cache/` and
  `/.ai/tasks/*/*/verification/`;
- `.ai/context/runbook.md`: `## Commands` followed by the lines
  `test:      python3 -c "import sys; sys.exit(0)"`, `lint:      python3 -c "print('lint')"`,
  `typecheck: (none)`, `build:     false`, `reusable: test, lint`;
- `.ai/specs/01-demo.md` (`# Demo\n`);
- `.ai/tasks/todo/task-01-demo/state.md`:

```text
spec_path: .ai/specs/01-demo.md
flow: full

## Phases
- discovery: complete
- execution: complete
- validation: not-started

## Solution Design
### Decision
Use f.
### Acceptance Criteria
- f returns 1
- b exists
### Invariants
- f is pure
### Off-limits
- no network

## Subtask Progress
T-01 | alpha | atomic-tests: green | atomic-execution: complete | atomic-validation: in-progress
  last_action: pae-finalize done
  target_files: src/a.py, tests/test_a.py
  blocker: none
  notes: tdd: red digest — AC-1 → test_f
T-02 | beta | atomic-tests: green | atomic-execution: complete | atomic-validation: not-started
  last_action: pae-finalize done
  target_files: src/b.py
  blocker: none
  notes:
```

- `.ai/tasks/todo/task-01-demo/plan.md` with a `## Subtasks` table (`ID | Name | Depends On |
  Type | Status`) holding T-01 and T-02; `T-01-alpha/description.md` with `## Goal`, `## Context`
  (no `working_dir:`), and `## Acceptance Criteria` holding `- AC one`, `- AC two`, `- AC three`;
  `T-02-beta/description.md` of the same shape.

A second commit changes `src/a.py` to `return 2`. Unless an AC says otherwise: `--work` is `R`,
`--task` is `R/.ai/tasks/todo/task-01-demo`, `--base` is the first commit, leaf `prepare` uses
`--scope-key T-01 --description <task>/T-01-alpha/description.md --listed src/a.py --listed
tests/test_a.py`, `ORCHESTRAIL_OUTPUT_CAPTURE=off` (mode `direct`), and an *accepted draft* is a draft built from the current `prepare` result that
satisfies R-01–R-12. Variants named in an AC derive from V1.

### C-8 Files created or changed

New: `scripts/scoped-verification.py`, `scripts/check-scoped-verification.py`,
`rules/contract-verification.md`, `.ai/adr/<NNNN>-*.md`.
Changed: the files of C-5, `scripts/check-capture-output.py` (REQ-61), `templates/.ai/context/runbook.md`, `.gitignore`,
`scripts/setup-new-project.sh` and `scripts/sync.sh` (or 09's replacement, REQ-51),
`scripts/README.md`, `docs/USAGE.md`, the pipeline reference (`workflows/PIPELINE.md`, or
`docs/PIPELINE.md` after spec 09), `.ai/principles/domain.md` (terms: Review record, Check receipt,
Coverage plan, Obligation, Finding-led recheck, Fix diff, Scope), `.ai/memory/architecture.md`
(scripts table, inventory counts), `.ai/context/runbook.md` (suite command, disable switch, store
removal), `.ai/adr/index.md`. The ADR records: content-bound receipts with project opt-in reuse;
review-side receipts only; whole-tree inputs including the worktree root; finding-led recheck
rules and expansion triggers; composite always full; the single `standard` tier; write-once
records outside shared files; the ignore rule; the disable switch; the 08 proposal dispositions.

## Non-Functional Requirements

| Attribute | Target or standard | Verification |
|---|---|---|
| NFR-01 Determinism | `prepare` output byte-identical for identical inputs (REQ-16); records and receipts differ only in `created_at`, the receipt `nonce` and the derived digests for identical drafts and runs | AC-10 |
| NFR-02 No model, no network | The helper imports no network module and starts no harness CLI (REQ-36) | AC-23 (static import scan) |
| NFR-03 Portability | Python 3.11+ standard library; `git` and `bash` on `PATH`; Linux and macOS file semantics | AC-24; review of imports |
| NFR-04 Privacy | Environment values never stored, only one digest; receipts and outputs mode 0600 under the git directory, never committed; records ignored by REQ-48 in this repository and under the untracked `.ai/` of consumer projects | AC-15, AC-22 |
| NFR-05 Rule size | `rules/contract-verification.md` ≤ 700 words (spec 11 REQ-01) | AC-19 |
| NFR-06 Compatibility (G4) | Tasks without records, legacy leaf blocks and disabled helpers follow today's full review plus REQ-55 | AC-20, AC-21, AC-28 |
| NFR-07 Performance | No time target (spec 10 measures review cost with and without the helper; no saving is claimed). Work bound: each `run` reads every non-ignored file outside the excluded prefix twice (before and after the command); `prepare` reads the contract sources, the manifest and evidence paths once and the tree not at all; `record` repeats `prepare` and computes one tree digest per defined check; no step is superlinear in the number of files | Review of the implementation against this bound |

## Edge Cases & Failure Modes

| Case | Expected behaviour | Requirement |
|---|---|---|
| Helper missing, `ORCHESTRAIL_HOME` unset, Python < 3.11 | Full review, `none — unavailable` entry | REQ-35, REQ-45 |
| Switch `off` | Every subcommand but `version` exits 4 `disabled`; full review, `none — disabled` | REQ-34, REQ-45 |
| `--work` outside a git repository | Exit 4 `not-a-repository`; full review | REQ-35 |
| Runbook missing | `defined: []`, `undefined` all three, warning `runbook-missing`; record needs no receipts | REQ-01 |
| `test:` placeholder `<command…>` or `(none …)` | Undefined; not required (today's evidence gap) | REQ-01, DM-9 |
| `reusable:` names `build` or an unknown check | Warning `reusable-unknown:<name>`; ignored | REQ-01 |
| Check not declared reusable | Executed every time; receipt `not-declared` | REQ-18 |
| Same inputs, receipt reused | No execution; `action: reused` | REQ-05 |
| One tracked or untracked non-ignored file changed | New `tree_digest`; executed | REQ-05 |
| Only an ignored file changed | Reuse; covered by the Declaration line's limit | REQ-05, C-4 |
| Different environment variable value | New `environment_digest`; executed | REQ-05 |
| Different worktree of the same repository | New `worktree_id`; executed | REQ-05 |
| Runbook command text changed | New `argv`; executed | REQ-05 |
| Command writes non-ignored files | `inputs-changed-during-run`; not reusable; `record` refuses `check-missing` until a receipt matches the current inputs; the reviewer runs the check once more, and a second mutation ends the helper path (`none — helper-error`) | REQ-18, REQ-02, C-4 `Mutation:` |
| Command killed by a signal or cannot start | Receipt not reusable; `record` refuses `check-incomplete`; reviewer sets `blocker:`, writes no verdict, appends `none — blocked` | REQ-18, REQ-32, REQ-55 |
| Capture write fails (disk full) | `capture_status: failed`, evidence unusable; `check-incomplete` | REQ-18, REQ-32 |
| Output file deleted or altered after the run | Receipt reported `receipt-damaged`, not reused | REQ-20 |
| Two runs on identical inputs with different exit codes (flaky) | `conflicting-receipts`; always executed | REQ-19 |
| Two concurrent runs | Two receipts, distinct names; no partial file visible | REQ-17 |
| Submodule, unreadable or non-UTF-8 path, unmerged index | `unknown-input:*`; not reusable | REQ-18 |
| Helper interrupted | No receipt; exit 4 `interrupted`; temporary files ignored | REQ-23 |
| Store unwritable | Exit 3 before execution; full review | REQ-22, REQ-45 |
| First review of a scope | `minimum_scope` full, reason `no-prior-record` | REQ-11 |
| Prior record JSON damaged or of another step | `prior-record-invalid` / not selected; full | REQ-11 |
| Notes entry missing, `none`, or digest mismatch | `prior-not-latest`; full | REQ-12 |
| Leaf prior verdict `DONE` (re-run after confirmation) | `prior-accepted`; full | REQ-15 |
| Prior subject dirty or its head garbage-collected | `prior-subject-dirty` / `prior-subject-unavailable`; full | DM-5 |
| Description amended, Solution Design edited, spec changed | `contract-changed`; full | REQ-13 |
| Successor packet with a new `task_contract_hash` | `contract-changed`; full | REQ-13 |
| Repair touches another leaf's file | `cross-leaf-change`; `full-leaf` | REQ-14 |
| Reviewer finds an interface or invariant change, or unknown impact | Must record a full scope; finding-led refused | REQ-30 |
| Empty fix diff after NEEDS WORK | Finding-led allowed; every open finding still needs an outcome | REQ-28 |
| Draft omits an outcome, reuses an id, or withdraws without evidence | Refused with the matching reason | REQ-28, REQ-29 |
| Draft `DONE` with an open important finding, a failed obligation or a failing check | `verdict-inconsistent` | REQ-07 |
| Failing lint with no finding naming it | `check-failure-unreported` | REQ-31 |
| Files change between `prepare` and `record` | `preparation-stale`; reviewer prepares again | REQ-25 |
| Two reviewers publish the same `n` | Second gets exit 3 `record-conflict` | REQ-24 |
| Leaf `atomic-tests: n-a`, `pinned` or absent | No RED evidence demanded; `tdd_audit.atomic_tests` mirrors the block; existing `/pav-check` findings apply | REQ-33 |
| Quick tier | Task level reads `## Contract (quick)`; inline fixes rechecked under `## Recheck` | DM-2, REQ-42 |
| Composite after a child merge (spec 22) | `full-integration`; a child-worktree receipt never matches (`worktree_id`), a root-worktree receipt is reused only for identical inputs; 22 REQ-03 post-merge commands are outside this spec and never use receipts | REQ-15, REQ-05 |
| Description without `## Acceptance Criteria` | Warning `no-acceptance-criteria`; the existing Guard stop applies first | REQ-01 |
| Duplicate `### Invariants` under `## Solution Design` | Exit 2 `contract-ambiguous`; full review without the helper, `none — helper-error` | C-3, REQ-45 |
| Review files in more than one git work tree (multi-repository task or composite) | Helper not used; full review, `none — multi-repository` | REQ-45 |
| Record refused twice in one review | Helper path ends; full review without it, `none — helper-error` | REQ-45, C-4 `Record:` |
| Owner accepts a finding as not a defect | The owner records the decision in an allowed DM-7a location; the next review gives `owner-accepted` with that reference; it no longer blocks `DONE` | REQ-28, R-08, DM-7a |
| Blocked check repaired; review re-run | The `verification check …` blocker is reset to `none` first; a blocked task-level section resumes its writer | REQ-56 |
| Receipt never referenced by a published record (for example made outside a review) | Not reused (`not-referenced`) | DM-6 |
| Nested untracked repository | `unknown-input:nested-repository`; not reusable | REQ-18 |
| Spec 14's helper refuses (git or gh word in the runbook value, `store-unavailable`, `store-unsafe`, `disabled`, …) | Command not started by it; run directly with own capture, `fallback: <code>`; review unaffected | REQ-58 |
| Spec 14's helper started the command but published nothing complete or verifiable | Not run again; evidence `unusable`; `check-incomplete`; REQ-55 blocker | REQ-59 |
| Root-run record (cases of REQ-62): the returned draft is unusable or `record` refuses it | No record; one correction by a fresh reviewing agent given the refusal reasons, then a full review without the helper (`none — helper-error`); no new error code; the `record-failed` block if that review also fails is spec 23's | REQ-62, A-33, 23 REQ-56 |
| Spec 14 artifact deleted after a receipt referenced it | Not reused (`receipt-damaged`); executed again | REQ-20, DM-6 |
| Implementer report reachable by the Validator | Not supplied (unchanged `/spec-run` 4.3); rule forbids reading it | REQ-44 |

## Acceptance Criteria

Fixture cases run in `scripts/check-scoped-verification.py`; text cases read the delivered files.

- **AC-01** (REQ-01, REQ-02, REQ-33) — Given V1, when `prepare --level leaf --scope-key T-01
  --description …/T-01-alpha/description.md` runs, then it exits 0 and lists `AC-1`–`AC-3`,
  `INV-1`, `OFF-1`, `defined` = `test` (reusable), `lint` (reusable), `undefined` = `typecheck`, and
  `atomic_tests` equal to the block's value; and given drafts stating `DONE` with (a) the `test`
  receipt exit code 1 and an `important` finding naming `test`, (b) no `lint` receipt, (c) a leaf
  block `atomic-tests: n-a` and `tdd_audit.atomic_tests: n-a`, then (a) is refused
  `verdict-inconsistent`, (b) is refused `check-missing`, and (c) is accepted when all else holds.
- **AC-02** (REQ-03, REQ-15) — Given V1, a draft with `tier: economy` is refused `tier-invalid`; a
  composite preparation has `minimum_scope: full-integration` and reason `merged-result`; and
  `rules/contract-verification.md` contains the `Tier:` line of C-4 verbatim.
- **AC-03** (REQ-04, REQ-44) — Given V1 at the second commit, a full-scope leaf draft whose
  `reviewed_paths` omit `src/a.py` is refused `coverage-incomplete`; and the delivered
  `workflows/spec-run.md` step 4.3 still contains "Do **not** give it the Implementer's reasoning or
  report" and cites `` `contract-verification → ## Reviewer inputs` ``, as does the `### Validator`
  section of `rules/orchestration.md`.
- **AC-04** (REQ-05, REQ-17, REQ-18) — Given V1, `run --check test --reuse` prints
  `action: executed`, `reusable: true` and `reuse_refused` containing `no-receipt`; a second run
  before any record prints `executed` with `not-referenced`; after an accepted T-01 draft
  referencing the first receipt is published (state S), the next run prints `action: reused` with
  the first `receipt_id`. Each of the following starts from state S with every other variant's
  change reverted: after (a) editing `src/b.py`, (b) adding untracked `src/c.py`, (c) setting an
  extra environment variable, (d) changing the runbook `test:` text, (e) running with `--work` set
  to a second `git worktree` of `R`, the run prints `action: executed`; after (f) writing `cache/x`
  (ignored) in `R` it prints `reused`. `run --check typecheck` exits 2 `check-undefined`.
- **AC-05** (REQ-06, REQ-07, REQ-28, REQ-30) — Given a published leaf record with verdict
  `NEEDS WORK`, a clean subject, finding `T-01/F1` (severity `important`, obligations `["AC-2"]`)
  open, `AC-2` verified with evidence path `src/a.py`, every other obligation verified with
  evidence path `tests/test_a.py`, and a later commit changing only `src/a.py`, when `prepare`
  runs, then
  `minimum_scope` is `finding-led`, `fix_diff` lists `src/a.py`, `open_findings` is `["T-01/F1"]`,
  `rereview` contains `AC-2` with `evidence-changed`, and `carry_eligible` contains the other
  verified obligations; a draft without an outcome for `T-01/F1` is refused `prior-outcome-missing`;
  a finding-led draft with `interface_impact` `unknown` for `src/a.py` is refused `scope-too-narrow`;
  the same draft with scope `full-leaf`, no carried obligation and `reviewed_paths` covering the
  change manifest is accepted with `expansion_reasons` containing `reviewer-widened`.
- **AC-06** (REQ-08, REQ-34, REQ-37) — Given an accepted record, it contains `scope`,
  `minimum_scope`, `expansion_reasons`, and per check `action` and `receipt_id`, and per obligation
  `state`; with `ORCHESTRAIL_SCOPED_VERIFICATION=off`, `prepare`, `run` and `record` each exit 4
  `disabled`, the store and `verification/` directories are byte-identical before and after, and
  `version` exits 0; every subcommand prints exactly one line on standard output.
- **AC-07** (REQ-09, REQ-13) — Given V1 and a published finding-led-eligible prior record, editing
  (a) the T-01 description, (b) `### Invariants`, (c) the spec file each make `prepare` report
  `contract-changed`; passing `--task-contract-hash` different from the prior record's does too;
  passing it to only one of the two does not.
- **AC-08** (REQ-10) — Given V1 at the second commit with untracked `src/c.py`, a modified tracked
  file inside the task directory and `--listed src/b.py`, `subject.entries` are
  `M src/a.py`, `listed src/b.py`, `A src/c.py` with digests, and no task-directory path; without
  `--base` only `listed src/b.py` appears; `--listed ../outside` exits 2 `path-invalid`.
- **AC-09** (REQ-11, REQ-12) — Given `reviews/T-01/1.json` valid (step `check`, open finding
  `T-01/F1`) and `2.json` whose JSON is damaged, `prepare` reports reasons exactly
  `["prior-record-invalid"]`, `prior.seq: 1` and `open_findings: ["T-01/F1"]`; given a valid latest
  record and a T-01 notes value whose last `verification: review T-01 check` entry is (a) missing,
  (b) `none — disabled`, (c) a different digest, `prepare` lists `prior-not-latest` in each case,
  and with the matching entry it does not.
- **AC-10** (REQ-16) — Given V1, two `prepare` runs with identical arguments print byte-identical
  lines.
- **AC-11** (REQ-14) — Given a NEEDS WORK record for T-01 and a later commit changing `src/b.py`
  (in T-02's `target_files:`), `prepare` reports `cross-leaf-change` and `minimum_scope:
  full-leaf`.
- **AC-12** (REQ-15) — Given a leaf prior record with verdict `DONE`, `prepare` reports
  `prior-accepted`; given a prior whose subject `clean` is false, `prior-subject-dirty`; given a
  prior whose head object was removed from a cloned fixture, `prior-subject-unavailable`.
- **AC-13** (REQ-19, REQ-20) — Given two stored receipts for the current inputs with exit codes 0
  and 1, `run --reuse` reports `conflicting-receipts` and executes; given one receipt whose stdout
  file was altered, it reports `receipt-damaged:<file>`, executes, and the altered receipt's bytes
  are unchanged.
- **AC-14** (REQ-18, REQ-32) — Given runbook `test:` commands that (a) end via `kill -9 $$`,
  (b) are run with the helper's `PATH` set to a directory holding only a symbolic link `git` to the
  real git (so `bash` does not resolve), (c) create the non-ignored file `src/gen.py`, the receipts
  show (a) `command_status {"kind":"signal","signal":9}` and `abnormal-exit`, (b) `start-error` and
  `abnormal-exit`, (c) an exit status and `inputs-changed-during-run`; and an otherwise accepted draft
  referencing (a) is refused `check-incomplete`.
- **AC-15** (REQ-17, REQ-22, NFR-04) — Given V1 with a command printing `out` to stdout and `err` to
  stderr and exiting 3, the receipt has `command_status {"kind":"exit","code":3}`, two output files
  with the exact bytes and mode 0600, an environment digest but no environment value, and the
  result line contains no output text; with the store directory read-only, `run` exits 3
  `store-unwritable` and the command's marker file is not created.
- **AC-16** (REQ-23) — Given a command `sleep 30` and SIGTERM sent to the helper after the command
  starts, the helper exits 4 `interrupted`, the command's process group is gone, and no receipt
  exists.
- **AC-17** (REQ-24, REQ-25, REQ-26, REQ-27, REQ-29, REQ-31) — Given V1: an accepted draft
  publishes `reviews/T-01/1.json` and the next accepted draft publishes `2.json`; with a dangling
  symbolic link `reviews/T-01/2.json` planted next to `1.json` before `prepare`, an accepted
  full-scope draft makes `record` exit 3 `record-conflict`; editing `src/a.py` after `prepare` makes
  `record` refuse `preparation-stale`; drafts that omit `INV-1`, mark `AC-1` carried in a full
  scope, reuse id `T-01/F1` for a new finding, or leave a failing `lint` receipt unnamed by any
  finding are refused `obligations-mismatch`, `carry-invalid`, `finding-id-invalid` and
  `check-failure-unreported` respectively.
- **AC-18** (REQ-38, REQ-39, REQ-40, REQ-41, REQ-42, REQ-43, REQ-46, REQ-47) — Given the delivered
  tree, `rules/contract-verification.md` has the C-4 front matter and every anchored line verbatim;
  `/pav-check`, `/pv-contract`, `/pv-review` and `/phase-composite-validation` cite
  `` `contract-verification → ## Review procedure` `` and contain `run --reuse`, `prepare` and
  `record`; `/pv-issues` contains `Findings: <ids>`; `/pv-execute-fixes` and `/phase-validation` cite
  `` `contract-verification → ## Recheck` ``; `/pav-check` names `typecheck`, `Verified
  obligations` and `Unverified obligations`; `templates/.ai/context/runbook.md` contains the line
  `reusable:` inside `## Commands`; each of those six workflows lists `rules/contract-verification.md`
  under `loads:` → `mandatory`; and no workflow gains a line matching
  `call ./phase-composite-validation`.
- **AC-19** (REQ-38, NFR-05) — Given the delivered rule, spec 11's `measure-context.sh check`
  reports no `rule-size-exceeded` and no `textual-load-undeclared` finding for any edited file.
- **AC-20** (REQ-45) — Given the delivered tree, `rules/contract-verification.md` contains the
  `Availability:`, `Mutation:` and `Record:` lines of C-4 verbatim, and each of `/pav-check`,
  `/pv-contract`, `/pv-review` and `/phase-composite-validation` contains the C-5 fallback sentence
  verbatim.
- **AC-21** (REQ-33, NFR-06) — Given V1 with T-01's block lacking `atomic-tests:`, `prepare` reports
  `atomic_tests: absent`, and a draft with `tdd_audit {"atomic_tests":"absent","outcome":"performed"}`
  is accepted when all else holds; a task-level draft with `outcome: performed` is refused
  `tdd-audit-invalid`.
- **AC-22** (REQ-48) — Given the delivered `.gitignore`, it contains `/.ai/tasks/*/*/verification/`
  and `git check-ignore` reports `.ai/tasks/todo/task-x/verification/reviews/T-01/1.json` ignored.
- **AC-23** (REQ-36, NFR-02) — Given the helper source, a static scan finds no import of `socket`,
  `http`, `urllib`, `ssl`, `ftplib`, `smtplib` or `asyncio` and no `subprocess` call naming
  `claude`, `codex` or `windsurf`; given snapshots (path, type, bytes) of `R` and of the receipt
  store taken before and after a call, `prepare` changes nothing, an accepted `record` adds exactly
  one file under `<task>/verification/reviews/`, and `run` of the V1 `test:` command adds files only
  under the receipt store.
- **AC-24** (REQ-35) — Given the helper imported by path, its function
  `version_supported(version_info: tuple[int, ...]) -> bool` returns false for `(3, 10, 0)` and true
  for `(3, 11, 0)`, and `main(argv, version_info=(3, 10, 0))` returns 4 after printing error
  `runtime-unavailable`; given `--work` in a directory that is not a git work tree, `prepare` exits
  4 `not-a-repository`.
- **AC-25** (REQ-49, REQ-50, REQ-51, REQ-54) — Given the delivered tree, `bash
  scripts/validate-contracts.sh` passes with no change to that file, to `tests/` or to
  `inventory-amendment.json` (including its `DEPLOY:` checks for `contract-verification.md` when
  today's deployment lists are still the mechanism); `python3 -I tests/golden-runs.py` passes with
  unchanged expectations; `scripts/lint-instructions.py` exits 0; the rule deployment mechanism
  current at delivery deploys `rules/contract-verification.md`; and neither
  `scripts/validate-contracts.sh` nor `scripts/sync.sh` names `check-scoped-verification`.
- **AC-26** (REQ-52, REQ-53) — Given the delivered tree, every file of C-8 is changed as listed,
  `.ai/adr/index.md` has an Accepted row for the new ADR, and the ADR names each item of C-8's ADR
  content and either each 08 proposal assigned to owner 15 with its disposition or the statement
  that no audit proposal was available.
- **AC-27** (REQ-21, REQ-37) — Given V1, `run --check build` exits 2 `check-undefined`, the
  `build:` command is not executed and no receipt is created; every failure line carries `error`
  and `detail`.
- **AC-28** (REQ-55, REQ-45) — Given the delivered tree, `rules/contract-verification.md` contains
  the `Checks:` line of C-4 verbatim, and `/pav-check`, `/pv-contract`, `/pv-review` and
  `/phase-composite-validation` each cite `` `contract-verification → ## Review procedure` `` in
  the same paragraph that names their fallback, so the classification applies with and without the
  helper.
- **AC-29** (REQ-28, REQ-07) — Given a NEEDS WORK T-01 record with open `important` finding
  `T-01/F1`, an empty fix diff, and a `## Task Analysis → ### Assumptions` section (outside every
  DM-2 contract source) added to `state.md` whose line `<n>` reads
  `- owner: T-01/F1 accepted as intended`: a draft giving `owner-accepted` with `decision: null`,
  with `decision: task:state.md:<m>` where line `<m>` is a copy of that text inside
  `## Subtask Progress` or `## Code Review`, or with `decision: task:verification/drafts/d.json:1`
  is refused `owner-decision-unreferenced`; with `decision: task:state.md:<n>`
  and every other DONE condition met, `DONE` is accepted; a new finding `T-01/F2` with status
  `owner-accepted` is refused `finding-id-invalid`; with outcome `owner-decision` (finding kept as
  `owner-decision`), `DONE` is refused `verdict-inconsistent` and `NEEDS WORK` is accepted.
- **AC-30** (REQ-27) — Given the AC-05 situation (so `AC-1` is carry-eligible), a finding-led draft
  marking `AC-1` `carried` with non-empty `evidence_paths` is refused `carry-invalid`; with `[]` it
  is accepted and the record's `AC-1` carries the prior record's evidence paths and digests and
  `carried_from` equal to the prior `seq`.
- **AC-31** (REQ-01) — Given V1, `prepare --level task --scope-key task --step contract` lists
  `AC-1`, `AC-2`, `INV-1`, `OFF-1`; `--step review` lists no obligations; with `flow: quick` and a
  `## Contract (quick)` holding one acceptance item, `--step contract` lists `AC-1` from it; and a
  `### Invariants` section with text but no list item yields one `INV-1` with `unstructured: true`.
- **AC-32** (REQ-10, REQ-18) — Given a second worktree `W` of `R` in which
  `.ai/tasks/todo/task-01-demo/state.md` is modified, `prepare --work W --task
  R/.ai/tasks/todo/task-01-demo` lists no path under `.ai/tasks/todo/task-01-demo/` and reports
  `clean: true`; given an untracked nested repository `R/vendor/x/` (with its own `.git`),
  `run --check test` publishes a receipt with `unknown-input:nested-repository` and
  `reusable: false`.
- **AC-33** (REQ-11, REQ-13, REQ-06) — Given a NEEDS WORK T-01 record with open finding
  `T-01/F1` and an edited T-01 description, `prepare` reports reasons exactly `["contract-changed"]`,
  `minimum_scope: full-leaf` and `open_findings: ["T-01/F1"]`; given no record, reasons are exactly
  `["no-prior-record"]`; given `reviews/task/1.json` (step `contract`) and `2.json` (step `review`),
  `prepare --level task --step contract` selects `1.json`.
- **AC-34** (REQ-12) — Given T-01 notes split over two `notes:` field groups whose last group has a
  continuation line ending with `; verification: review T-01 check #1 full-leaf sha256:<digest of
  1.json>`, `prepare` does not list `prior-not-latest`; when a later entry
  `verification: review T-01 check none — disabled` follows it, `prepare` lists `prior-not-latest`.
- **AC-35** (REQ-55) — Given the delivered tree, `/pav-check` and `/phase-composite-validation`
  contain the C-5 replaced sentences verbatim and, after joining lines and collapsing whitespace,
  no longer contain "reported as evidence gaps;
  do not claim" or "report unavailable checks."; `/pav-check`, `/phase-composite-validation`,
  `/pv-contract` and `/pv-review` each contain the C-5 blocker text for their level, including
  `verification check <name> could not complete`.
- **AC-36** (REQ-10, REQ-45) — Given V1 plus a T-02 description whose `working_dir:` (relative to its own
  directory) resolves to `R/svc`, a directory of the same repository holding `x.py`, and T-02
  `target_files: x.py`, `prepare --level task --step contract
  --listed R/src/a.py --listed R/svc/x.py` (absolute paths) lists both as top-level-relative
  entries, and a cross-leaf check for T-01 resolves T-02's `target_files:` against `R/svc`; a
  `--listed` path inside a different git repository exits 2 `path-invalid`.
- **AC-37** (REQ-56) — Given the delivered tree, `/pav-check` and `/phase-composite-validation`
  contain the blocker-reset instruction with the prefix `verification check `; `/phase-validation`
  names a section starting with `blocked: verification check ` as partial output that resumes its
  writer; and `/pv-review` contains the C-5 stop message verbatim.
- **AC-38** (REQ-57, REQ-17) — Given V1 with `ORCHESTRAIL_OUTPUT_CAPTURE` unset and
  `ORCHESTRAIL_HOME` pointing at a copy of the delivered checkout (spec 14's helper present),
  `run --check test` publishes a receipt with `output.mode: capture-output`, an `artifact_id` that
  names a directory under `<git common dir>/orchestrail-output/`, a `manifest` with exactly the
  nine DM-4 keys, `purpose: test` and `argv_sha256` equal to the SHA-256 of
  `["bash","-c",<test value>]` in spec 14's DM-2 canonical form; nothing is created under the receipt store's `outputs/`; the result
  line's `output_reference` matches spec 14's DM-6 grammar. After an accepted record references
  it: deleting the artifact directory makes the next `run --reuse` report `receipt-damaged:<file>`
  and execute; renaming `scripts/capture-output.sh` inside the same `ORCHESTRAIL_HOME` copy (switch
  still unset, so the environment digest is unchanged) makes it report `capture-unverifiable`,
  execute in mode `direct`, record `fallback: unavailable`, and publish a receipt whose
  `inputs_digest` equals the capture-mode receipt's.
- **AC-39** (REQ-58) — Given V1 with `ORCHESTRAIL_OUTPUT_CAPTURE` unset, spec 14's helper present and the runbook `test:` value
  `touch m; echo git`, `run --check test` publishes a mode-`direct` receipt with
  `fallback: git-command-refused` and the file `m` is created exactly once; with
  `ORCHESTRAIL_OUTPUT_CAPTURE=off` the receipt records `fallback: disabled`; with a regular file at
  `<git common dir>/orchestrail-output` it records `fallback: store-unsafe`.
- **AC-40** (REQ-59) — Given V1 with `ORCHESTRAIL_OUTPUT_CAPTURE` unset and `ORCHESTRAIL_HOME` pointing at a fixture copy whose
  `scripts/capture-output.sh` is a stub that touches a marker, prints `capture: v1 unpublished` and
  `OUTPUT none — publish-failed` on standard output and exits 125, `run --check test` publishes a
  mode-`capture-output` receipt with `command_status {"kind":"aborted","label":"unknown"}` and
  reasons `abnormal-exit` and `capture-failed`, the marker exists once, and an otherwise accepted
  draft referencing it is refused `check-incomplete`; with the switch still unset and a stub that publishes a manifest whose
  `capture_status` is `partial` and whose `verify` exits 0, the receipt lists `capture-failed` and
  evidence `unusable`.
- **AC-41** (REQ-60) — Given the delivered tree after specs 14 and 15, step 5 of
  `workflows/pav-check.md` contains the C-5 resulting first sentence (naming `test:`, `lint:` and
  `typecheck:`) and the C-5 resulting sentence verbatim (with the two
  `contract-output` sentences) and, after joining lines and collapsing whitespace, no longer
  contains "Run them through `contract-output → ## Capture`, read results per"; and
  `workflows/phase-composite-validation.md` contains its C-5 resulting sentence verbatim.
- **AC-42** (REQ-61) — Given the delivered tree, `python3 -I scripts/check-capture-output.py` passes
  and its cases for spec 14's C-5 rows 3a and 5 contain this spec's C-5 resulting sentences.
- **AC-43** (REQ-62) — Given V1, a valid draft produced after `prepare` in one process and saved
  under `.ai/tasks/todo/task-01-demo/verification/drafts/` is published as `reviews/T-01/1.json`
  by `record --draft` run in a separate process with the same options; a file in that directory
  that is not JSON gives exit 1 `record-refused` with reasons `["draft-invalid"]` and publishes
  nothing; a draft that omits a planned obligation is refused as REQ-26 states and publishes
  nothing.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01 | AC-01, AC-31 |
| REQ-02 | AC-01 |
| REQ-03 | AC-02 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-06 | AC-05, AC-33 |
| REQ-07 | AC-05, AC-01, AC-29 |
| REQ-08 | AC-06 |
| REQ-09 | AC-07 |
| REQ-10 | AC-08, AC-32, AC-36 |
| REQ-11 | AC-09, AC-33 |
| REQ-12 | AC-09, AC-34 |
| REQ-13 | AC-07, AC-33 |
| REQ-14 | AC-11 |
| REQ-15 | AC-02, AC-12 |
| REQ-16 | AC-10 |
| REQ-17 | AC-04, AC-15, AC-38 |
| REQ-18 | AC-04, AC-14, AC-32 |
| REQ-19 | AC-13 |
| REQ-20 | AC-13 |
| REQ-21 | AC-04, AC-27 |
| REQ-22 | AC-15 |
| REQ-23 | AC-16 |
| REQ-24 | AC-17 |
| REQ-25 | AC-17 |
| REQ-26 | AC-17 |
| REQ-27 | AC-17, AC-30 |
| REQ-28 | AC-05, AC-29 |
| REQ-29 | AC-17 |
| REQ-30 | AC-05 |
| REQ-31 | AC-17 |
| REQ-32 | AC-14 |
| REQ-33 | AC-01, AC-21 |
| REQ-34 | AC-06 |
| REQ-35 | AC-24 |
| REQ-36 | AC-23 |
| REQ-37 | AC-06, AC-27 |
| REQ-38 | AC-18, AC-19 |
| REQ-39 | AC-18 |
| REQ-40 | AC-18 |
| REQ-41 | AC-18 |
| REQ-42 | AC-18 |
| REQ-43 | AC-18 |
| REQ-44 | AC-03 |
| REQ-45 | AC-20, AC-28, AC-36 |
| REQ-46 | AC-18 |
| REQ-47 | AC-18 |
| REQ-48 | AC-22 |
| REQ-49 | AC-25 |
| REQ-50 | AC-25 |
| REQ-51 | AC-25 |
| REQ-52 | AC-26 |
| REQ-53 | AC-26 |
| REQ-54 | AC-25 |
| REQ-55 | AC-28, AC-35 |
| REQ-56 | AC-37 |
| REQ-57 | AC-38 |
| REQ-58 | AC-39 |
| REQ-59 | AC-40 |
| REQ-60 | AC-41 |
| REQ-61 | AC-42 |
| REQ-62 | AC-43 |

Shared gates: G1 — REQ-08, C-6 (05 attribution facts, no invented counts); G2 — C-6 (10 owns
comparable measurement; switch gives the comparison arm); G3 — REQ-02, REQ-04, REQ-07, REQ-28,
REQ-30, REQ-44 (independent reviewer, frozen RED untouched, integration always full); G4 —
REQ-45, NFR-06; G5 — REQ-36, Actors table (helper writes no shared state, spawns no model, is
optional); G6 — C-7, AC-01–AC-42 (failing fixtures first), REQ-50, no paid run; G7 — REQ-34,
REQ-45, DM-1 deletion safety, ADR; G8 — out of scope here, owned by spec 10 (no saving claimed,
no cost or time cap introduced).

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| A reviewer lists too few `evidence_paths`, so an obligation is carried although code it relied on changed | Missed regression | Medium | Carrying needs non-empty evidence paths (`no-evidence-paths`); all defined checks re-run on current inputs; any interface/invariant/unknown classification forces full; spec 10 measures misses |
| A project declares a check reusable that depends on ignored files, time or network | Stale pass reused | Low–medium | Opt-in only; Declaration line states the condition; conflicting results disable reuse; switch off restores full runs |
| Environment digest makes reuse rare across agents | No saving | High | Acceptable by design (correctness first); spec 10 decides whether to relax with evidence |
| Pre-existing failing checks block `DONE` where today they were evidence gaps | More NEEDS WORK stops | Medium | Owner approved the rule on 2026-11-14 (D-01); the `owner-accepted` outcome (DM-7a) is the only tolerance route |
| Running checks through the helper hides the runbook text from the git-rails hook | A git command in a runbook line is not seen | Low | Same class as residual X1 (scripts run by Bash are unseen); runbook edits are part of reviewed diffs |
| Edits to always-on orchestration rule exceed spec 11 limits | Delivery fails 11's check | Low | One sentence each; detail lives in the on-demand rule |
| Spec 14's helper is absent in one environment and present in another | Receipts of two modes | Low | Same inputs digest in both modes only when the environment, including `ORCHESTRAIL_HOME` and `ORCHESTRAIL_OUTPUT_CAPTURE`, is identical; otherwise the check runs again (correct, no saving); `fallback` records why a run was direct |
| A reviewing agent writes an allowlisted DM-7a decision line itself (decision sections are also written by `/pd-analyze` and, under `/spec-run`, by automatic deferral) | A finding accepted without the owner | Low | The allowlist excludes every section a reviewer is told to write; `rules/orchestration.md:148-153` reserves intent decisions for the human; spec 10 measures missed defects |

## Assumptions

- A-01 | File names | Resolved: today's names in text; spec 09's maps at implementation | Source: `.ai/specs/README.md` → "Dependency order" (09 before 15); spec 13 A-02 precedent | Reversible: yes
- A-02 | Where the new tooling lives | Resolved: helper and suite under `scripts/`, outside the validator inventory and `tests/`; the helper is run with `python3 -I` without a Bash launcher, so the entry file as a whole uses only syntax older Python 3 interpreters parse and loads 3.11-only code after the check, for REQ-35's version check to decide (spec 18 A-26: entry module plus path-loaded engine) | Source: ADR-0019 Decision 3 (`.ai/adr/0019-…:68-80`); spec 12 C-9 | Reversible: yes
- A-03 | Whose receipts may be reused | Resolved: only receipts made by review workflows through the helper; Implementers never run it | Source: G3; `rules/orchestration.md:80-92` | Reversible: yes
- A-04 | Which checks are reusable | Resolved: none unless the project lists them in `reusable:` | Source: original §6 ("unknown → run again"); best practice, smallest reversible choice | Reversible: yes
- A-05 | Effective inputs | Resolved: whole non-ignored repository tree outside the task directory, argv and resolved `argv[0]`, cwd, worktree root, full environment minus four volatile names, platform | Source: original §6; spec 23 cross-worktree correctness (23 A-28: a child-worktree receipt never stands for the merged tree; 22 REQ-03 commands never use receipts); best practice | Reversible: yes
- A-06 | `build:` | Resolved: never run by reviews | Source: `.ai/context/runbook.md:11` (build deploys) | Reversible: yes
- A-07 | Tiers | Resolved: only `standard`; cheaper tiers need an owner decision after comparison | Source: original REQ-03, §11 item 6; `.ai/specs/README.md` → "Review record and remaining decisions" | Reversible: yes
- A-08 | Where finding-led applies | Resolved: leaf after NEEDS WORK and task-level re-runs; composite always full (`full-integration`, REQ-15), run in the root worktree | Source: original §8 last paragraph; spec 22 REQ-12 and A-28 | Reversible: yes
- A-09 | Required-check failures | Resolved: non-zero exit → finding ≥ important → NEEDS WORK; cannot complete → blocker; applied with and without the helper (REQ-55) so the disabled arm stays comparable; approved by the owner on 2026-11-14 (D-01) | Source: original REQ-02; D-01; `rules/tdd.md:208-210` blocker pattern; G2 comparability | Reversible: yes
- A-10 | Storage | Resolved: receipts in the git common directory; records in `<task>/verification/`, ignored here | Source: spec 12 DM-10; spec 13 REQ-37 | Reversible: yes
- A-11 | Obligation ids | Resolved: ordinal per kind, whole-section fallback | Source: `workflows/pae-tests.md:225` (`AC-1 →` digest convention); spec 13 note that descriptions carry no AC ids | Reversible: yes
- A-12 | Relation to spec 12 digests | Resolved: own `contract_digest` always; 12's `task_contract_hash` compared only when both present; receipts independent of packet digests | Source: spec 12 C-8 rows 13 and 15, A-10; coordinator note | Reversible: yes
- A-13 | Reviewer inputs beyond the validator packet | Resolved: diff content, untracked files, runbook, evidence paths, tdd notes, prior record | Source: 12 C-8 ("15 decides sufficiency"); original §7 | Reversible: yes
- A-14 | Spec 13 facts | Resolved: not consumed; reviewer re-derives them | Source: `.ai/specs/13-orchestrator-overhead.md` REQ-30 and C-10 row for spec 15 (both say 15 declines the `green` messages and `red`/`pinned` receipts because REQ-30 forbids passing any Implementer report, checkpoint message, receipt or journal path to a Validator) | Reversible: yes
- A-15 | Output capture | Resolved: through spec 14's helper when available (DM-4a), own capture of complete streams otherwise; no preview | Source: coordinator ruling of the 2026-11-14 reconciliation; spec 14 C-7 row 15 and Q-05; roadmap order 14 before 15 (`.ai/specs/README.md` → "Dependency order") | Reversible: yes
- A-16 | Notes entry | Resolved: `verification:` entry with spec 12's append rule, not protected; `none` marker on fallback | Source: spec 12 DM-11 append rule | Reversible: yes
- A-17 | Finding ids | Resolved: `<scope key>/F<n>`, never reused, `same_as` for recurrences | Source: this spec (DM-7); spec 17 Context item 8 consumes it | Reversible: yes
- A-18 | Prior subject | Resolved: must be clean with an existing head | Source: original invariant 3 | Reversible: yes
- A-19 | Disable switch | Resolved: `ORCHESTRAIL_SCOPED_VERIFICATION=off`; any value other than unset, empty or `on` disables | Source: spec 12 REQ-32 (same rule); spec 13 REQ-33 | Reversible: yes
- A-20 | Timeouts | Resolved: none added | Source: ADR-0020 (timeouts are watchdogs, not budgets); no invented numbers | Reversible: yes
- A-21 | Exit codes | Resolved: 0–4 as C-2; the meaning of each number is this helper's own (spec 12 C-2 assigns 3 and 4 differently) | Source: spec 12 C-2 (range only) | Reversible: yes
- A-22 | Task-level records | Resolved: one per step, verdict `null` | Source: `workflows/pv-contract.md:43-61`, `workflows/pv-review.md:60-70`; decisions belong to `/pv-issues` | Reversible: yes
- A-23 | Path base | Resolved: repository top-level relative | Source: best practice (git output form) | Reversible: yes
- A-24 | Risk classification | Resolved: optional reviewer-set field, decides nothing here; read by spec 17's overrides, offered to (not used by) spec 16 | Source: original §5 `risk_reason`; spec 17 DM-7 overrides; spec 16 C-6 row 15 | Reversible: yes
- A-25 | Check report | Resolved: fields filled from the record | Source: `.ai/specs/11-context-tiering.md`, DM-8 Report forms (`## Check report`) | Reversible: yes
- A-26 | Cross-leaf detection | Resolved: other leaves' `target_files:` resolved against their own `working_dir:` and counted when inside `--work`'s work tree | Source: `workflows/pv-contract.md:35-36` (per-subtask `working_dir:`); best practice | Reversible: yes
- A-27 | Rule name and load | Resolved: `rules/contract-verification.md`, `load: on-demand` | Source: spec 09 kind prefixes (`.ai/specs/09-model-only-harnesses-and-rule-naming.md`, Notes → Files and sections created after this spec); specs 12 and 13 precedent | Reversible: yes
- A-28 | Check ordering | Resolved: checks before `prepare`, record before verdict writes, DM-8 entry last | Source: original REQ-02 (deterministic before semantic); `workflows/pav-check.md:103-108` | Reversible: yes
- A-29 | Pre-existing failing checks | Resolved: no baseline exemption; the owner accepts (`owner-accepted`) or defers through existing routes | Source: conservative reading of G3; former Q-03; owner approval of 2026-11-14 (D-01) | Reversible: yes
- A-30 | Owner decisions on findings | Resolved: outcome/status `owner-accepted` with a decision reference, not blocking `DONE` | Source: `rules/orchestration.md:148-153` (class B is the human's); original §8 step 3 | Reversible: yes
- A-31 | Receipt provenance | Resolved: reuse only receipts already referenced by a published review record of the same task | Source: G3; A-03 enforcement | Reversible: yes
- A-32 | Multi-repository reviews | Resolved: helper not used; `none — multi-repository` | Source: `workflows/phase-composite-validation.md:18-22` (per-child `working_dir:`); best practice | Reversible: yes
- A-33 | Retry bound | Resolved: one re-run after mutation, one re-record after refusal, then full review without the helper | Source: P5 (every stop declared); best practice | Reversible: yes
- A-34 | Task directory exclusion across worktrees | Resolved: excluded prefix relative to the task directory's own work tree | Source: DM-1 excluded-prefix rule; spec 22 REQ-12 and A-28 (the composite review runs in the root worktree) | Reversible: yes
- A-35 | Time limit of a delegated check | Resolved: `run` passes no `--timeout-seconds`; the outer call's limit applies and a killed call leaves no receipt, which the reviewer treats as lost output and does not rerun in that review (DM-4a); no limit source and no number | Source: spec 14 C-7 row 15 and follow-up for 15; A-20; ADR-0020 | Reversible: yes
- A-36 | Who runs `record` in parallel mode | Resolved: the root orchestrator runs `record` on the draft the reviewing agent returns, in the cases of 23 REQ-55 as REQ-62 states them (not only N > 1 children's `/pav-check`: also the Validator of a serialized composite's child at N > 1 and the composite validation agent of 22 REQ-12); at N = 1 the Validator runs `record`; an unusable or refused draft follows the `Record:` rule (REQ-62, A-33; orchestration in 23 REQ-56) | Source: owner decision D-02; 23 D-05, 23 REQ-55, 23 REQ-01 (the root is the only writer under `.ai/`); 23 Q-03 | Reversible: yes

## Decisions

Auto-mode resolutions are recorded under Assumptions. Owner decisions of 2026-11-14:

- D-01 | Accept the strict classification of REQ-55: a defined `test`, `lint` or `typecheck` check exiting non-zero is a finding of at least `important` severity, and a check that cannot start, is killed or loses its captured output is a blocker; no exemption for failures that predate the change; the same rule with and without the helper | Overrides: today's `/pav-check` and composite-validation wording that treats a missing or failing check as an evidence gap | Rationale: an evidence gap lets a validator pass broken code, which undermines gate G3 (independent quality); one rule on both paths keeps the disabled-helper comparison arm comparable | Follow-up: none beyond the delivery already specified (C-5 replaced sentences, AC-28, AC-35); the only tolerance route stays the `owner-accepted` outcome of a finding (DM-7a)
- D-02 | The root orchestrator runs `record` in parallel mode, on the review draft the reviewing agent returns | Overrides: none (resolves 23 Q-03) | Rationale: 23 REQ-01 makes the root the only writer in parallel mode, so records are written by the root from a returned draft, which needs no new mechanism | Follow-up: spec 23 records the same rule and its dispatch; this spec states REQ-62, A-36 and C-6 row 23

## Clarifications

### Session 2026-11-14 (owner decisions)

- Q: Should a defined check that exits non-zero be a finding of at least `important` severity (not an evidence gap), with no exemption for earlier failures, with and without the helper? → A: Yes, accepted (D-01).
- Q: In spec 23's parallel mode (cases per REQ-62), who runs `record` (23 Q-03)? → A: The root orchestrator, on the draft the reviewing agent returns (D-02).

### Session 2026-11-14 (auto mode)

- No question was put to the owner (auto mode under standing authorization). A coordinator note
  confirmed G1–G8 as the gate set and asked that spec 12's final contract be settled here; it is
  folded into A-12, A-13 and C-6.
- Coordinator ruling (reconciliation pass, 2026-11-14): an implementer must not find two capture
  mechanisms; where spec 14's helper is available, checks run through it and the receipt
  references its artifact and manifest, otherwise the existing behaviour applies; spec 15 keeps
  the inputs digest, the reuse decision and the review record. Folded into DM-4a, REQ-57–REQ-61,
  A-15 and C-5.

## Open Questions

- Q-01 | non-blocker | Should location-independent checks be reusable across worktrees? Impact:
  reuse in spec 23's parallel mode. Recommended: no until spec 10 shows misses do not rise.
- Q-02 | non-blocker | Should this repository track review records as knowledge (ADR-0012) instead
  of ignoring them (REQ-48)? Recommended: ignore, matching spec 13 Q-01.
- Q-03 | resolved | Former question on exempting checks that also fail on the base revision —
  resolved by A-29 (no exemption), approved by the owner on 2026-11-14 (D-01).
- Q-04 | resolved | Former question on referencing spec 14 artifacts — resolved by DM-4a and
  REQ-57–REQ-60 (2026-11-14 reconciliation).

## Notes

### Name mapping (spec 09)

| Today | After 09 |
|---|---|
| `workflows/pav-check.md` | `workflows/atomic-validation-check.md` |
| `workflows/pv-contract.md`, `pv-review.md`, `pv-issues.md`, `pv-execute-fixes.md` | `validation-contract`, `validation-review`, `validation-issues`, `validation-execute-fixes` |
| `workflows/phase-validation.md`, `phase-atomic-validation.md`, `phase-composite-validation.md` | `validation`, `atomic-validation`, `composite-validation` |
| `rules/orchestration.md`, `rules/tdd.md`, `rules/quick-flow.md`, `rules/workflow-globals.md` | `contract-orchestration`, `contract-tdd`, `contract-quick-flow`, `contract-phases` |
| `rules/phase-validation.md`, `rules/phase-atomic-validation.md` | `bootstrap-validation`, `bootstrap-atomic-validation` |

### Implementation hints (nonbinding)

- Spec 09 (Notes → Files and sections created after this spec, 09 REQ-68): `rules/contract-verification.md`
  holds only new text. The delivery moves no text out of a rule that has a `rule` row, so it adds no
  name-map row, no `new` entry and no amendment entry; the three replaced sentences live in workflows.

- Hint: order — (1) suite skeleton and V1 fixture with failing cases; (2) `prepare` parsing and
  manifest; (3) receipts and reuse; (4) recheck and `record` validation; (5) rule and workflow
  text with failing text cases first; (6) docs, ignore rule, ADR.
- Hint: compute file digests with streaming reads; hash the tree once before and once after each
  run.
- Hint: keep parsing, digesting, policy and validation in separate functions testable without the
  command line.

### Change log

- 2026-11-14 — reconciliation with finished peer specs: capture delegated to spec 14's helper
  when available (DM-4a, REQ-57–REQ-60, REQ-17 wording, DM-4 `output`/`command_status`, DM-6
  `capture-unverifiable`, DM-10 `output_reference`, C-5 replaced sentences, C-6 row 14, A-15,
  Q-04 resolved, AC-38–AC-42, REQ-61 for spec 14's suite, REQ-23/REQ-36 for the capture child); C-6 rows 17 and 18 name the exact fields and paths those specs
  read and state how rechecks behave while spec 17 defers the NEEDS WORK stop; C-6 row 16 and
  A-24 no longer imply spec 16 consumes anything. Readiness verdict unchanged.
- 2026-11-14 — second reconciliation pass: spec 13, 11 and 23 citations by id instead of line
  number (Terminology, DM-4, DM-8, C-3, C-6 row 13, A-14); A-14 and C-6 row 13 state that 13 REQ-30
  forbids passing any Implementer report, checkpoint message, receipt or journal path to a
  Validator; DM-4a states that `run` passes no `--timeout-seconds` and spells out the case lettering
  (new A-35); C-6 row 23, the Edge Cases composite row, A-05, A-08 and A-34 state 23 A-28 (post-merge
  commands never use receipts, a child-worktree receipt never stands for the merged tree, only the
  root-worktree composite review may reuse one, at `full-integration`); C-5 `loads:` row stated in
  11's grammar and the frozen-check note for the replaced sentences; Notes record that no text moves
  out of a mapped rule (09 REQ-68). Confirmed unchanged: C-6 rows 16, 17, 18, A-19 and A-24 against
  specs 16, 17, 18 and 10 REQ-52. No requirement, acceptance criterion or verdict changed.
- 2026-11-14 — independent final review: C-5 replaces both step 5 sentences of `/pav-check` (`test:`, `lint:`, `typecheck:`), REQ-60 and AC-41 follow; C-6 row 23 states the record location and points to 23 Q-03 (since resolved, see the next entry); disable switch follows spec 12 REQ-32; A-02/A-21 clarified; own ids qualified; Finding source corrected; neutral provenance wording; citations by id.
- 2026-11-14 — owner decisions recorded: D-01 (the REQ-55 classification of failing checks is approved; A-09, A-29, Risks, Scope text and Q-03 now say so) and D-02 (the root orchestrator runs `record` in parallel mode: REQ-62, AC-43, A-36, an Edge Cases row, C-6 row 23 no longer open). Counts updated; verdict unchanged.
- 2026-11-14 — aligned with spec 23 record handling: REQ-62 names the cases by citing 23 REQ-55 (child `/pav-check` agent at N > 1, the Validator of a serialized composite's child at N > 1, the composite validation agent of 23 REQ-12) and cites 23 C-6 rows 11 and 12 and 23 REQ-56 instead of one row; the C-4 `Record:` line, Actors & Roles, C-6 row 23, the Edge Cases row and A-36 state the exception; no id added or renumbered, verdict unchanged.

### Rejected alternatives

- Reusing Implementer-produced check results for the verdict — rejected: weakens G3.
- Commit-hash-based receipts — rejected: one commit does not describe a dirty tree (original §3).
- A per-check dependency model — rejected for now: no reliable, language-neutral source.
- Finding-led composite review — rejected: merged results need a full check (original §8).
- Making the helper mandatory — rejected: G5.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph on recorded coverage, content-bound reuse and finding-led recheck |
| 2 | Out of Scope names concrete exclusions | PASS — repair (17), tiers/models (04, 16, 10), packets (12), journals (13), previews (14), merges (23), build, timeouts, validator inventory |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-62; original REQ-01–REQ-08 restated |
| 4 | REQ ↔ AC both ways | PASS — Traceability table covers REQ-01–REQ-62 and AC-01–AC-43 |
| 5 | Every AC binary and test-first | PASS — fixture V1 fully specified; text ACs quote exact lines |
| 6 | Non-functional targets measurable or N/A | PASS — NFR-01–NFR-06 verifiable; NFR-07 states a work bound and no time target, measurement owned by 10 |
| 7 | Data model and contracts specified | PASS — DM-1–DM-10, DM-4a, DM-7a, C-1–C-8 |
| 8 | Error, empty, boundary and concurrency cases | PASS — Edge Cases table; concurrent runs (nonce), record races (`record-conflict`), interruption |
| 9 | Every Step 3 ambiguity recorded | PASS — A-01–A-36, D-01–D-02; Q-01, Q-02 open non-blockers; Q-03, Q-04 resolved |
| 10 | No blocker question | PASS — none |
| 11 | Existing-code claims cited and verified | PASS — path:line citations checked at `060ce6d`; spec 13 cited after its final revision |
| 12 | Terminology matches project definitions | PASS — domain terms reused; new terms defined; rejected synonyms listed |
| 13 | Feature-sized (1–8 subtasks) | PASS — about six: preparation, receipts, records/recheck, rule and workflow text, docs/ADR |
| 14 | Devil's Advocate review | PASS — Review: 4 rounds, score 97/100, critic: sub-agent, open: none critical or major; minor F-48–F-50 were applied after round 4 and not re-scored |

Owner-decision pass 2026-11-14 (D-01, D-02): REQ-62, AC-43 and A-36 were added after the scored
review and were checked by one independent critic only; the verdict is unchanged.

Second pass 2026-11-14: only peer-citation and delegation wording changed (change log); the verdict
below is unchanged.

Verdict: **READY FOR DEVELOPMENT**, after its roadmap prerequisites (10, 12, 13, 14; 09 and 11 for
names and `loads:`) are delivered. Automated readiness is not owner sign-off.
