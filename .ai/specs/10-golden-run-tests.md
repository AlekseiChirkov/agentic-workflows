# 10. Golden-run regression tests and independent strategy evaluation

## Source

- **Request:** `/spec-draft .ai/specs/10-golden-run-tests.md --auto-mode` (refinement in place,
  2026-11-13). The owner authorized in-place replacement and will not answer questions during
  this run; every gap is resolved under `## Assumptions` with its source.
- **Input:** the existing Russian-language specification at commit `060ce6d` (file last
  changed in `c4372f8`). Its full original text stays in git history. The condensed English
  translation below is faithful in substance; requirement and acceptance identifiers are
  preserved.
- **Governing decisions:** ADR-0009 Decision 6 — golden-run tests run only before a release,
  on a pinned model, against a fixture of about five files in a pure-Python + `pytest` project,
  offline, with a CI secret allowed for manual dispatch only, and `docs/examples/` built from
  the golden fixture (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:236-238`). The
  owner's request of 2026-10-21, recorded in the original text, adds the comparison of all
  suitable strategies without treating a strong reviewer's verdict as proof of correctness.

### Implementation review — 2026-11-06

- **Disposition:** Planned; ordinary offline tests are not the golden framework.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** The repository already has deterministic source, hook, model, telemetry, and runtime tests.
- **Outstanding scope and limits:** The specified four example projects, tests/run-golden.sh, normalized expected-result framework, A-F experiment manifests, held-out evaluation, and comparative promotion evidence are not delivered. No paid experiment is authorized by this review.
- **Sources:** [`tests/workflow-instructions.py`](../../tests/workflow-instructions.py), [`scripts/validate-contracts.sh`](../../scripts/validate-contracts.sh), [`tests/model-selection.py`](../../tests/model-selection.py).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Original text (translated from Russian, condensed; historical, non-normative)

The current requirements are under `## Requirements`; where an identifier below names a
different obligation than its rewritten form, the rewritten form governs and the original
obligation is carried by the requirements in the mapping under `### Change Log`.

**1. Status and purpose.** Implementation draft, ready for reconnaissance and interface
refinement. Ordinary checks must work without models and network. Model runs and claims about
their quality or savings require a separately authorized experiment. Basis: ADR-0009
Decision 6 and the owner's 2026-10-21 request. Verified snapshot `8c2fa08`, 2026-10-28. The
existing contract tests (`tests/log-step.sh`, `tests/hook-workflow-contract.sh`,
`tests/hook-timing.sh`, `tests/workflow-instructions.py`) do not mean the golden task set,
experiment runner or independent evaluation exist. The cited report
`docs/audits/2026-10-28-workflow-clarity-and-size.md` is absent and is not evidence.

**2. Problem and outcome.** Matching file structure does not prove a working result;
normalization can erase a failed test, an unresolved finding or a test-first violation; a
reviewing model can err together with the executor; comparing the price of one answer ignores
preparation, rechecks, repairs and failed tasks. Three distinct outcomes: (1) deterministic
regression — interfaces, formats, limits and synthetic-task behaviour without model calls;
(2) golden run — a model actually runs the process and artifacts are compared with a reviewed
expectation, which does not replace independent behaviour checks; (3) strategy evaluation —
independently accepted results, missed defects, total cost and duration compared on identical
tasks under a pre-registered protocol. No text improvement, word reduction or golden match is
presented as proven token, cost or quality savings.

**3. Scope and dependencies.** In scope: four synthetic projects, semantic checks,
normalization, a manual runner of authorized runs, an experiment manifest, independent
evaluation, a scenario calculator, reports, cancellation and evidence storage. Out of scope:
automatic paid checks on sync or ordinary CI, real pull requests, a third harness, a trained
model router, changes to production budgets. The primary golden executor is the historically
chosen Claude harness; another harness only through an explicitly supported verified adapter
or supplied recorded results. Dependencies: completed 01, 09, 05, 06; 11 and 12–18 consume this
evaluation; 12 later extends the composite example.

**4. Roles.** Fixture author (observable requirements, constraints, open and hidden cases);
task executor (only permitted materials, chosen strategy); working reviewer (normal process
review, one piece of evidence); independent evaluator (separate criteria, hidden checks,
dispute rules, never changed to suit a strategy); experiment owner (authorizes a concrete
manifest, limits, disputed criteria and promotion); experiment runner (isolates runs, checks
authorization, keeps every outcome, stops on set conditions). Independence comes from process,
access to hidden answers and a separate evidence set — not from using a different model. The
executor and working reviewer must not see hidden expected solutions, strategy labels or
evaluator answers before finishing.

**5. Requirements.** REQ-01 self-contained pure-Python `pytest` projects `flat` (three
leaves), `composite` (two children), `quick`, `bugfix`, about five content files, needing no
provider program, keys, network or model. REQ-02 `tests/run-golden.sh <case> <workflow>`
copies an isolated project and calls `claude -p` with the exact authorized model, tool limits
and verified environment; the policy names Sonnet 5 but does not confirm availability or an
exact identifier; a missing pinned variant stops without substitution; application network is
forbidden, model transport is the only network exception, checked against real capabilities.
REQ-03 meaning before normalization: extract and check statuses, protected fields, findings,
stops, traceability and test-first evidence before removing volatile data; keep full raw
material; normalization cannot hide a failure, a lost critical finding or a forbidden edit.
REQ-04 compare with `tests/expected/<case>/`; a mismatch is non-zero; `--update` creates a
reviewable change, never auto-accepted; separately check behaviour, tests-before-code history,
frozen tests, architectural invariants and injected defects. REQ-05 model runs only for a
release or an explicitly authorized manual experiment; sync, ordinary validation and default
jobs run offline checks only; a subscription does not authorize buying API access; examples for
21 come only from synthetic projects. REQ-06 manifest variants A–F with exact models, effort,
context preparation, reviewers, retries, escalation and selection grounds; unsupported variants
are marked unavailable or manual, never measured. REQ-07 same initial revisions, specs and
criteria; historical tasks only owner-selected and anonymized; separate tuning and held-out
evaluation; account for type, complexity, risk, context size, observability, repetitions,
order, cache state and reuse; no private code in published fixtures. REQ-08 independent
quality incl. architecture, invariants, hidden cases, disputes and later defects; critical and
important injected defects detected regardless of the working model's verdict. REQ-09 metrics
with sample sizes, denominators, uncertainty; observations separated from scenarios; no
equivalence claim from a non-significant small sample. REQ-10 an authorized manifest before any
model call with counts, spend/time limits, retries, stop conditions, cancellation and a
pre-registered quality/cost rule; missing settings block only the paid path; a critical missed
defect stops the variant until the owner decides; experimental limits never become production
budgets. REQ-11 scenario calculator from user-given probabilities and prices, always
hypothetical. REQ-12 apply G1–G8; describe baseline collection, variant blinding, dispute
resolution, golden review, cancellation, storage, rollback and promotion; a cheaper variant
becomes default only after the pre-registered quality rule and an independent measurement of
total savings.

**6. Offline suite.** Per-project detection targets: `flat` — missed leaf, dependent work
before the previous review, wrong branch order, incomplete criteria traceability;
`composite` — successful children with a broken shared contract, missing integration check,
wrong final state, later parallel-integration errors after 23; `quick` — missing quick
contract, artificial full decomposition, lost constraints of the short path; `bugfix` — fix
without a reproducing case, changed pinned expected behaviour, regression of a neighbouring
case. Each project has a spec, initial application state, minimal project context, open tests
and a separate directory of independent assertions that is never copied into the executor's
workspace; hiding is not promised when the model can reach their location, so access isolation
is part of preflight. Preparation may use an installed `pytest`; checks never install from the
network. Mandatory corruptions: implementation before the tests commit at a required test
level; frozen tests changed without an authorized amendment; a successful verdict with a failed
hidden case; a high-severity finding removed; a forbidden edit of shared state or out-of-scope
area; incompatible child interfaces with passing child tests; unknown usage reported as zeros;
a capture, normalization or storage error reported as success; a corrupted expectation that
`--update` tries to accept without review. Legitimate modes pass: justified `none/n-a` needs
no fake RED; `pinned` passes before the change and moves only to `green`; a legacy block
without `atomic-tests:` already `atomic-execution: in-progress` continues with the note
`pre-TDD task, TDD step skipped`; new work does not get these exceptions merely because a field
is missing, and claiming `pinned` for new work or deleting a recorded field is rejected.

**7. Strategies A–F.** A strong executor from the start; B cheaper executor plus strong
review; C strong planning plus cheaper execution; D adaptive model or chain selection; E
multiple review levels; F combinations. No code predetermines a winner; D may be described and
calculated hypothetically without a router but not declared measured.

**8. Manifest.** Identity (schema version, experiment id, full-manifest hash, date, owner);
authorization (reference, scope, exact hash of the agreed configuration); sources (application
revision, source and installed instruction revision, spec and criteria hashes); tasks (ids,
risk/complexity classes, tuning or held-out, exclusion rules); variants (exact models, requested
and allowed effort, roles, context, checks, repairs); order (repetitions, randomization or
counterbalancing, seed); cache (cold/warm, reuse, observability); limits (runs, retries, spend,
time, unknown-data handling); quality (primary metrics, tolerated degradation, critical-defect
rule, follow-up window); independent evaluation (owner, hidden checks, blinding, dispute
resolution); environment (adapter and program versions, tools, application network ban and
proof); data (artifact location, retention, anonymization and export); stop (conditions,
cancellation, partial results, resumability); decision (pre-registered accept/reject/
insufficient-data rule and rollback). A safe template may have `approval: null`,
`execution_enabled: false` and unset parameters, never a runnable paid example with invented
prices, models or approvals. An existing approval is reused when it covers the manifest,
volume and repetition; changing models, task count, limits, hidden criteria or selection rules
creates a new configuration that needs updated approval. The runner first does an offline
preflight and prints a reviewable plan; missing approval does not prevent preparing projects,
checks, calculations and an expected-actions report.

**9. Execution, isolation, cancellation.** Preflight: schema, hash, approval scope and variant
exactness; model and parameter availability through permitted means without a paid probe;
pinned sources, criteria, adapters and installed configuration; offline checks and hidden
material available to the evaluator and unavailable to the executor; real tool and network
restrictions — if a declared condition cannot be ensured, stop or agree an explicitly weaker
design before starting, never mark isolation done; a unique workspace, artifact directory and
not-yet-run record, no real pull requests or pushed branches; remaining authorized volume and
limits — unknown spend is not zero and an insufficient limiting mechanism refuses the next paid
run. "No network" means the fixture has no network dependencies; model requests need a
separately authorized transport; a tool-name allowlist is insufficient when a permitted shell
can start any network client; documentation records which mechanism restricts child processes
and what stays unverified. Each attempt gets experiment, task, variant, repetition and attempt
identifiers; a slot in the authorized attempt count is reserved before launch; a missing
response does not mean no call happened; exact usage accounting belongs to 05. Order: save the
raw result, extract semantic assertions, run independent checks, build the normalized
projection, compare the expectation; each step has its own status; an independent failure is
never turned into success by a matching golden. Cancellation stops new work, sends the
termination signal to active processes, saves results and usage, keeps unfinished attempts
visible, never restarts automatically after a lost response or output-save error; resume checks
the journal and the remaining authorization.

**10. Semantics and normalization.** Mandatory order: record raw bytes, commit history,
command results, findings, metadata; extract critical features; check them against independent
assertions (an extraction error is a check error, not an empty success); normalize only
permitted volatile data by versioned rules; check that key relations survive, then compare.
Dates become a date symbol; hashes become stable distinct aliases preserving ancestry;
temporary paths become stable project paths; collapsing all hashes into one value is forbidden.
Free text may be reduced to extracted structure only after a completeness check; findings,
severities, unresolved criteria, forbidden changes and stops are never "noise". `--update`
produces a candidate, a diff and an explanation of changed semantic assertions; a separate
review operation binds the change to a source revision and reason.

**11. Evaluation and statistics.** The unit is task × variant × pre-registered repetition;
internal retries, repairs and model escalation belong to that unit; repetitions of one task may
be dependent. Tuning, thresholds and protocol fixes use a separate data part; held-out results
must not silently become tuning; detected contamination is recorded and the affected sample is
no longer untouched. Mutually exclusive outcomes: independently accepted; rejected by criteria;
stopped by policy; cancelled; technically incomplete; excluded for a pre-defined external reason
(explained, never applied to inconvenient failures). Rates always show numerator and
denominator, planned and started/completed/accepted units; cancelled and partially measured
cases stay in the protocol denominator or are reported as censored with impact analysis. The
owner pre-registers primary metrics, tolerated degradation and the severe-defect rule; no
numeric tolerances are invented here; a critical missed defect stops the affected variant and
is never averaged away. Comparison uses task pairing, pre-registered stratification and
uncertainty intervals, with repetitions as clustered groups; dependence handling, confidence
level and the A–F multiple-comparison policy are fixed before the main sample; after candidate
selection a pre-allocated untouched final sample or a family-wide correction is used. On a small
sample "insufficient data" is a valid result. Example strict promotion rule, made concrete in
the manifest before the experiment: the lower bound of the quality difference (candidate minus
baseline) must be strictly greater than `−Δ`; with `0 < r_max < 1`, the upper bound of the
cost-per-accepted ratio (candidate / baseline) must be strictly less than `r_max`, which needs
a defined denominator, complete comparable cost and all outcomes (zero accepted or incomplete
cost cannot pass); hard constraints are checked separately and never compensated. Workflow
verdict `DONE`, open-test pass and hidden-test pass are shown separately; disputes go to the
independent evaluator, keeping reproducible grounds.

**12. Cost and scenarios.** Telemetry and API-equivalent cost belong to 05; the report links
tasks to its records with measurement completeness, price origin, actual models and missing
components. Total strategy cost includes planning, context, orchestrator, executors, working
review, tools, repairs, escalation and integration; a shared planning pool is included once
when attributable to the cohort and never split evenly without evidence; the independent
experimental evaluation is a separate line. Cost per accepted result = all accounted costs of
all started units (failures included) / number of independently accepted results; undefined
with zero accepted; marked incomplete with incomplete cost. Completion duration and summed
worker time are separate; subscription payment is actual billing, API-equivalent cost a
comparison estimate. Hypothetical break-even: strong path costs 7, cheap path 4 plus a repair
chain of 5 with probability `p`; expected cheap cost `4 + 5p`, break-even `p = 0.6`; at
`p = 0.2` cheap 5 vs strong 7, at `p = 0.6` 7 vs 7, at `p = 0.8` 8 vs 7. The numbers are
synthetic; with differing acceptance probabilities the formula is insufficient; it allows no
unbounded retries and does not change 17's attempt limits. The extended calculator takes
outcome branches with probabilities and planning/review/tool/repair/escalation costs and an
acceptance chance, validates probabilities, keeps unknowns unknown and shows sensitivity.

**13. Gates G1–G8** as defined in `.ai/specs/README.md → ## Shared acceptance gates`, applied
to this spec. **14. Acceptance** AC-01–AC-07 (current text under `## Acceptance Criteria`),
plus mandatory cases: manifest corruption, change after approval, unprotected hidden checks,
unsupported network restriction, interruption after a request was sent, partially measured
result, held-out contamination, a new critical defect, and a human/model evaluation conflict.
**15. Order** projects and negative cases → semantics and normalization → offline plan and
fake adapter → A–F manifest, evaluation form, calculator → manual model adapter disabled by
default, documentation and job separation → hand over against AC-01–AC-07 → a live experiment
only after separate covering approval. Undecided before a paid run: task set, repetitions,
model identifiers, tolerated degradation, follow-up window, limits and dispute owner; they do
not block offline implementation and grant no right to run a model on assumption.

## Context & Problem

Verified facts:

- No golden framework exists: `tests/` holds contract and unit suites only; there is no
  `tests/run-golden.sh`, `tests/golden/` or `tests/expected/` (directory listing of `tests/`
  at `060ce6d`). No CI configuration exists (no `.github/` directory at `060ce6d`).
- The validator's check inventory is frozen. The inventory oracle rejects any change to the
  number of acceptance expressions or focused modes
  (`tests/fixtures/validator-runtime/oracle.py:250`), and the source guard binds reviewed
  exceptions to a digest of every `.sh` and `.py` file under `tests/`
  (`tests/fixtures/validator-runtime/source_guard.py:809-816`). ADR-0019 Decision 3 therefore
  placed a new focused check outside `scripts/validate-contracts.sh`
  (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`). The guard's
  maintenance procedure for new files under `tests/` is documented in
  `tests/fixtures/validator-runtime/README.md:9-28`; ADR-0020 applied it once
  (`.ai/adr/0020-task-unknown-source-guard-watchdog-timeouts.md`, Decision 2).
- Spec 05 already provides the cost-per-accepted calculation over independently verified
  outcomes: `summarize_outcomes(attempts, labels, *, as_of, verify_acceptance, ...)`
  (`scripts/usage_telemetry_outcomes.py:87-88`). An opportunity identity has exactly the keys
  `task_revision`, `input_revision`, `acceptance_contract`, `strategy`, `repetition` (`:13`);
  attempts and labels need a UTC `observed_at` and are ignored after `as_of` (`:110`, `:144`);
  attempt categories are `workload`, `production_verification`, `experimental_evaluation`
  (`:122`); a label whose `acceptance_contract` differs from its identity's is skipped
  (`:147`); label revisions are integers from 1 and two different labels with the same
  identity and revision raise `conflicting acceptance revisions` (`:150-165`); statuses are
  `accepted`, `rejected`, `defect` (`:152`); the latest revision decides (`:167-169`); zero
  accepted yields `accepted_denominator_zero` (`:172`); `compare_outcome_groups` is at
  `:185-206`.
- Pipeline artifacts the golden checks read are canonical: top-level `state.md` fields and
  `## Phases` (`rules/workflow-globals.md:160-169`), leaf blocks and git fields (`:175-186`),
  status vocabularies (`:195`, `:197`), the legacy `atomic-tests:` rule (`:202-208`),
  composite blocks (`:210-219`), `## Fix-Tasks` (`:248-263`), `plan.md` statuses
  (`:268-278`); TDD states and the pre-TDD note (`rules/tdd.md:34-50`); the characterization
  note (`rules/tdd.md:146-147`) and the amendment note (`rules/tdd.md:186`); the leaf `notes:`
  lines `tdd: red digest — <behaviour> → test_<name>, …` written in red and pinned modes and
  `tdd: none — …` for `n-a` (`workflows/pae-tests.md:100-110`, `:205-213`, `:219-225`); the
  two-commit rule (`rules/git-flow.md:85-103`) applied only by `/spec-run` and `/restack`
  (`rules/git-flow.md:7-9`); `## Contract Check` with a free-text Criterion column
  (`workflows/pv-contract.md:46-62`) and its critical stop gate (`:64`); `## Issue List`
  (`workflows/pv-issues.md:46-52`) with severity `critical | important | optional` (`:24`,
  `:28`); the quick gate (`rules/quick-flow.md:28-50`) and quick TDD record
  (`rules/quick-flow.md:90-97`); bugfix task directories `fix-<NN>-<slug>`, `kind: bugfix`,
  `## Reproduction` (`workflows/bugfix.md:25`, `:37-45`, `:52-60`), and the bugfix stop when
  any quick-gate condition fails (`workflows/bugfix.md:97-100`); `/spec-run` stops on
  `flow: quick` (`workflows/spec-run.md:112-114`).
- The run log lives under `$ORCHESTRAIL_LOG_ROOT` when set (`rules/run-log.md:35-45`); step
  events carry `step`, `outcome`, optional `tests`, `gate` and free-text `subtask`
  (`rules/run-log.md:217-222`, `:249-252`). The helper reads step names from
  `$ORCHESTRAIL_HOME/workflows/*.md` (`scripts/log-step.sh:371-378`). Under `/phase-pipeline`
  execution logs one `pe-execute` step per subtask cycle with `--subtask`, `--tests` mirroring
  the final `atomic-tests:` and `--gate` from validation (`workflows/phase-execution.md:36-40`);
  child steps are logged once each (`workflows/phase-pipeline.md:32-35`). Only `/spec-run`
  logs a per-leaf `pae-tests` RED row (`workflows/spec-run.md:255-259`). No emitted event
  orders test writing before implementation for workflows without commits.
- Entry workflows: `/phase-pipeline <spec-path|task-directory>`
  (`workflows/phase-pipeline.md:5`), `/spec-run <path-to-spec> [--allow-pr] [--dry-run]`
  (`workflows/spec-run.md:5`; without `--allow-pr` no push or `gh` command, `:9`),
  `/bugfix "<defect>" [--auto-mode] [--no-repro]` (`workflows/bugfix.md:5`). Both
  `/phase-pipeline` and `/spec-run` are autonomous and pre-answer the issue approve/defer prompt
  (`rules/workflow-globals.md:66`, `:71`, `:79`).
- A non-interactive `claude -p` run has no person to answer permission prompts
  (`harness/claude/capabilities.md:63`). The installed CLI (`claude --version` →
  `2.1.323 (Claude Code)`, observed 2026-11-13 with `claude --help`, no model call) offers
  `-p`, `--model`, `--effort` (`low`, `medium`, `high`, `xhigh`, `max`), `--output-format json`,
  `--max-budget-usd` ("Maximum dollar amount to spend on API calls"), `--permission-mode`,
  `--allowedTools`, `--disallowedTools` and `--no-session-persistence`. Its JSON result field
  names and the enforcement of `--max-budget-usd` were not observed.
- `/output/` is ignored as local generated artifacts (`.gitignore:10`); `ORCHESTRAIL_HOME` and
  `ORCHESTRAIL_LOG_ROOT` select the helper checkout and log store
  (`.ai/memory/architecture.md:179`); the git-rails hook only reads the project registry
  (`.ai/memory/architecture.md:94`) and covers registered projects
  (`harness/claude/capabilities.md:77`). `pytest` is not installed in the repository's pinned
  Python 3.12.16 (`python3 -m pytest --version` → `No module named pytest`, 2026-11-13).

Consequence: optimization specs 11 and 12–18 cannot show that a change preserves behaviour, and
no cheaper strategy can be qualified, because there is neither a deterministic regression of
whole pipeline runs nor a protocol that measures independently accepted results and their
total cost.

## Goal

Give the project a deterministic, model-free regression suite for whole pipeline runs on four
synthetic projects, and a manually triggered, owner-authorized runner that executes those
projects with a model, checks the meaning of the results independently before comparing
normalized artifacts with reviewed expectations, and evaluates strategies A–F under a
pre-registered protocol, so that behaviour preservation can be shown offline and any claim of
equal quality or lower total cost of an accepted result rests on independent, complete,
reproducible evidence rather than on matching files, word counts or a reviewer's verdict.

## Scope

Delivered by this spec (implementation plausibly in eight parts, see `## Notes → Delivery
order`):

1. Four golden cases with seed projects, hidden checks, reference results and a case manifest.
2. Capture, semantic extraction and semantic assertions over pipeline artifacts, git history
   and the run log.
3. Versioned normalization into a semantic projection, golden comparison, `--update`
   candidates and a reviewed acceptance operation for expectations.
4. The experiment manifest, its validation, configuration hashing, approval records and an
   offline preflight with a reviewable plan.
5. The runner: attempt ledger, reservation, adapter invocation (a declared live `claude`
   adapter and a test double), isolation probes, limits, cancellation and resume; import of
   recorded results.
6. Independent evaluation: outcomes, missed defects, blinding, human evaluation records,
   disputes, late defects, held-out reveal and contamination tracking.
7. Reports with denominators, cost per accepted result through spec 05's calculation,
   clustered uncertainty intervals and a pre-registered promotion verdict.
8. The deterministic scenario calculator, the safe manifest template, the operating manual and
   the offline acceptance suite.

## Out of Scope

- Any paid model run, live experiment, or creation of live expected results; this spec ships
  the capability with live execution disabled until an owner approval exists.
- Registering the golden suite in `scripts/validate-contracts.sh` (frozen inventory) or as a
  `scripts/sync.sh` gate (open question Q-01). Creating any CI file: this spec creates none; spec 21
  REQ-81 owns the one offline workflow `.github/workflows/offline-checks.yml`, whose last step runs
  this spec's `python3 -I tests/golden-runs.py` when that file exists. A paid run never starts in
  CI (gate G6).
- Changing pipeline defaults, model plans, effort policy, run-log emission or any production
  budget; adopting a promoted variant is a separate owner decision and spec.
- Building `docs/examples/flat-task/` (owned by spec 21 REQ-11); this spec only makes the
  `flat` case and its runs available as the source.
- Parallel composite execution and its integration errors (spec 23 extends the `composite`
  case later).
- A third harness, a trained router (strategy D is hypothetical unless recorded results are
  supplied), Codex execution (only through recorded results).
- Defining usage telemetry, token accounting, price snapshots or API-equivalent valuation
  (spec 05 owns them); this spec stores what `attach-usage` supplies.
- A shared planning or orchestration pool across units: every unit is an independent pipeline
  run, so no cross-unit pool arises; recorded imports must report per-unit cost.
- Summed worker time: the adapter exposes no per-worker timing; reports carry
  `worker_time_ms: null` with diagnostic `not-observed`.
- Authenticating a human approver or evaluator beyond the interactive-terminal requirement;
  forging records by a process with the owner's file access is outside the threat model.
- Process-level network or file isolation of the live harness itself; the spec defines the
  probe contract and the weaker-design path, not a sandbox implementation.
- Test-before-implementation order evidence for workflows that do not commit; it requires a
  run-log emission change outside this spec (Q-05).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Fixture author | Writes cases under `tests/golden/cases/`: seed project, case manifest, hidden checks, reference results. |
| Task executor | The harness process launched by the adapter; sees only the attempt workspace, the attempt log root and the helper home. |
| Working reviewer | The pipeline's own Validator/review steps inside the executor run; its verdict is one fact among others. |
| Independent evaluator | The runner's evaluation step (hidden checks, assertions) plus a named human recording verdicts from the evaluation queue through `golden-eval.py evaluate`; never edits criteria after seeing results. |
| Dispute resolver | The person named in `evaluation.dispute_resolver`; closes disputes with a final record. |
| Experiment owner | Writes and approves manifests (`approve`, interactive only), accepts expected results, decides promotion outside the tool. |
| Experiment runner | `golden-eval.py run`: validates, preflights, reserves, launches, captures, evaluates, stops and records. Never approves, never changes defaults. |
| Release maintainer | Runs the offline suite and, with an approved regression manifest, the release golden runs. |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Golden case | One synthetic project under `tests/golden/cases/<case>/` with seed, hidden checks, reference results and `case.json`. Ids: `flat`, `composite`, `quick`, `bugfix`. | REQ-01 |
| Case workflow | A key of `case.json → workflows` naming one pipeline entry invocation for the case (initially `spec-run`, `phase-pipeline`, `bugfix`). | DM-1 |
| Catalog pair | One (case, case workflow) pair; the initial catalog has five (DM-1). | DM-1 |
| Seed project | The case's initial project tree copied into a workspace and committed as the seed commit. | DM-1 |
| Branch model | `per-leaf` or `per-composite`, spec 22 DM-1; decides which SA-10/SA-11 rules apply. | Spec 22 DM-1 |
| Stack entry | Under `per-composite`, a top-level leaf or a composite (its children excluded) in plan order. | Spec 22 Notes |
| Variant switch | A spec's opt-in setting a variant applies through `switches` (prompt arguments, environment values, overlay files). | REQ-52 |
| Evaluator-only material | A case's `hidden/` and `reference/`, every artifact root, every `cases_root`, and `blinding.json`; never copied into a workspace or helper home. | REQ-20 |
| Workspace | A fresh temporary git repository holding one attempt's executor-visible project. | REQ-47 |
| Helper home | An attempt-local copy of the pinned source checkout's tracked files without `tests/`, `.ai/` and `docs/`, exported as `ORCHESTRAIL_HOME`. | REQ-20 |
| Capture | The raw, unnormalized record of a finished workspace: files, git history, run log, command results. | REQ-03 |
| Facts | Values extracted from a capture (DM-3). | REQ-03 |
| Semantic assertion (`SA-NN`) | A rule over facts with result `passed`, `failed`, `error` or `not-applicable` (DM-3). | REQ-03 |
| Hidden check (`HC-N`) | An evaluator-only check executed against a copy of the final workspace (DM-3). | REQ-08 |
| Leaf tests | The test functions named after `→` in the leaf's `tdd: red digest` note, resolved in `test_globs` files. | DM-3 |
| Projection | The normalized semantic summary compared with the expected result (DM-4). | REQ-04 |
| Expected result | `tests/expected/<case>/<workflow>/projection.json` plus `review.json`. | REQ-04 |
| Candidate | A directory written by `--update` for review (DM-5); never an expected result by itself. | REQ-16 |
| Manifest | The experiment configuration JSON (DM-6); purpose `regression` (release golden runs) or `comparison` (strategy evaluation). | REQ-10 |
| Configuration hash | `config_sha256`, the canonical-JSON SHA-256 of the manifest without its `approval` key. | REQ-22 |
| Approval record | DM-7; binds an owner's approval to one configuration hash. | REQ-22 |
| Adapter declaration | DM-8; the argument template, result mapping and capability claims of one harness CLI. | REQ-02 |
| Unit | (task, variant, repetition) — the unit of observation. | REQ-29 |
| Attempt | One launch (or one recorded import) for a unit; numbered from 1; addressed by an opaque attempt key. | REQ-24 |
| Finished attempt | An attempt with a `finished` ledger event, whatever its outcome. | REQ-27 |
| Outcome | Exactly one of `independently-accepted`, `rejected-by-criteria`, `stopped-by-policy`, `cancelled`, `technically-incomplete`, `excluded`. | REQ-29 |
| Unit outcome | The outcome of the unit's last finished attempt; `stopped-by-policy` with the refusal reason for a unit refused before any launch; none (`pending`) for a unit not yet reached. | REQ-29 |
| Workflow-claimed success | All three `## Phases` are `complete` in the final task state. | REQ-28 |
| Missed defect | A failed hidden check (or a late defect within the follow-up window) in an attempt with workflow-claimed success; its severity is the defect's `critical`, `important` or `optional`. | REQ-28 |
| Split | `tuning` or `holdout` for each manifest task; the decision split is chosen by `analysis.decision_split`. | REQ-12 |
| Strategy code | `A`–`F` as in the original §7; a variant has exactly one. | REQ-06 |
| Weaker design | A manifest flag in `accepted_weaker_isolation` or `limits.accept_unverified_cost_cap` by which the approving owner accepts a check that cannot be enforced; reports state it. | REQ-21 |
| Severity | `critical`, `important`, `optional` — the pipeline's issue vocabulary (`workflows/pv-issues.md:24`). The original's "high severity" means `critical` or `important`. | — |
| Gates G1–G8 | Canonical definition: `.ai/specs/README.md → ## Shared acceptance gates`. | README |

Rejected synonyms: "golden test" for the offline suite (use *offline suite*); "verdict" for an
outcome (a verdict is the pipeline's `DONE`/`NEEDS WORK`); "`DONE`-claiming" (use
*workflow-claimed success*); "budget" for experiment limits (use *limits*; production budgets
do not exist, ADR-0009 Decision 5).

## Requirements

Original identifiers REQ-01–REQ-12 keep their subject; the translated original text under
`## Source` is historical and non-normative. Each original requirement is rewritten as one EARS
behaviour and its remaining obligations move to REQ-13 onward (2026-11-13).

- **REQ-01 Self-contained cases.** THE SYSTEM SHALL provide the golden cases `flat`,
  `composite`, `quick` and `bugfix` under `tests/golden/cases/<case>/`, each conforming to DM-1
  and the case catalog, whose seed behaviour, open tests, hidden checks and semantic assertions
  execute with the Python standard library, `git` and an already installed `pytest` only,
  without a provider program, credentials, network access or a model.
- **REQ-02 Authorized launch.** WHEN `golden-eval.py run` (or `tests/run-golden.sh`) reaches a
  reserved attempt of an `executable` variant, THE SYSTEM SHALL launch the adapter executable
  once, in the attempt workspace, with the argument list produced by the approved adapter
  declaration from the manifest's exact model id, effort, permission mode and tool lists, and
  with the child environment of `## Contracts & Interfaces → Workspace and child environment`.
- **REQ-03 Meaning before normalization.** THE SYSTEM SHALL process every attempt in the order
  capture → extract → assert → evaluate → normalize → compare and record a separate status
  (`passed`, `failed`, `error`, `skipped`, `not-run`) for each step in the attempt record.
- **REQ-04 Golden comparison.** WHEN the projection of an attempt or `check` differs from the
  expected projection of its catalog pair, or no expected result exists, THE SYSTEM SHALL set
  the compare step to `failed` with reason `golden-mismatch` or `missing-expected`, write a
  unified diff of the two canonical JSON texts (`indent=2`) to `compare/diff.txt`, and exit 1.
- **REQ-05 Paid boundary.** THE SYSTEM SHALL invoke a model adapter only from `golden-eval.py
  run` with an approved runnable manifest.
- **REQ-06 Strategy variants.** THE SYSTEM SHALL accept manifest variants with strategy codes
  `A`–`F` carrying the fields of DM-6, record each variant's `availability` (`executable`,
  `recorded`, `manual`, `unavailable`), and list a variant as measured in a report only when at
  least one of its units has a finished attempt.
- **REQ-07 Comparable recorded results.** IF the tracked files of the seed commit of a workspace
  given to `import-recorded` differ from the task's seed project files outside `.ai/`, THEN THE
  SYSTEM SHALL refuse the import with exit 2 and reason `incomparable`.
- **REQ-08 Independent acceptance.** THE SYSTEM SHALL assign `independently-accepted` only
  through the last row of the DM-10 outcome table or a dispute-resolution record, so that the
  pipeline's own verdict never decides acceptance.
- **REQ-09 Complete metrics.** WHEN `golden-eval.py report` runs, THE SYSTEM SHALL write, per
  variant and split, every DM-12 metric with its numerator and denominator and label the
  report `kind: observed`.
- **REQ-10 Approved manifest required.** IF `run` is invoked without a manifest, with a
  manifest that is not runnable, with `execution_enabled: false`, or with an approval record
  that is missing or unreadable, THEN THE SYSTEM SHALL exit 4 before creating a workspace or
  invoking an adapter.
- **REQ-11 Scenario calculator.** WHEN `golden-eval.py calculate --scenario <file>` runs on a
  valid DM-13 input, THE SYSTEM SHALL write the DM-13 output computed by
  `## Contracts & Interfaces → Calculator`, labelled `kind: hypothetical`.
- **REQ-12 Promotion verdict.** WHEN a report compares a candidate variant with the baseline,
  THE SYSTEM SHALL emit the verdict given by the first matching rule of
  `## Contracts & Interfaces → Promotion rule`.
- **REQ-13 No model substitution.** IF a variant's model id is empty or is one of the adapter
  declaration's `alias_names`, THEN THE SYSTEM SHALL exit 5 before any launch; IF an adapter
  result reports a model identity different from the requested id, THEN THE SYSTEM SHALL mark
  the attempt `stopped-by-policy` with reason `model-mismatch` and launch no further attempt of
  that variant.
- **REQ-14 Normalization rules.** THE SYSTEM SHALL normalize only by the rules NR-1–NR-4 of
  DM-4, map distinct commits to distinct aliases and distinct branches to distinct aliases, and
  record `normalization_version` in every projection.
- **REQ-15 Extraction errors.** IF a required source of DM-3 is missing, unparsable or
  ambiguous, THEN THE SYSTEM SHALL set the extract step to `error` with the source and reason
  and set every assertion that depends on it to `error`.
- **REQ-16 Update writes candidates only.** WHEN `--update` is given to `run` or `check`, THE
  SYSTEM SHALL write a DM-5 candidate directory under `<artifact-root>/candidates/` and SHALL
  NOT write under `tests/expected/`.
- **REQ-17 Reviewed expectation.** WHEN `golden-eval.py accept-expected` runs, THE SYSTEM SHALL
  refuse with exit 1 a candidate whose recorded capture, extract, assert or evaluate status is
  not `passed`, and otherwise write the candidate projection and a DM-5 review record into
  `tests/expected/<case>/<workflow>/`.
- **REQ-18 Applicable TDD contract.** THE SYSTEM SHALL evaluate SA-05 by the TDD evidence table
  of DM-3.
- **REQ-19 Negative catalog.** THE SYSTEM SHALL include in the offline suite every corruption
  N-01–N-12 of `## Edge Cases & Failure Modes` with an assertion that it yields the named check
  result and an outcome other than `independently-accepted`.
- **REQ-20 Evaluator-only material.** THE SYSTEM SHALL build each workspace from the seed
  project only and each helper home from the files listed by `git ls-tree -r --name-only
  <source_revision>` (contents from `git show <source_revision>:<path>`) without the `tests/`,
  `.ai/` and `docs/` trees.
- **REQ-21 Isolation preflight.** IF a live launch is about to start and the isolation probe of
  `## Contracts & Interfaces → Isolation` fails for hidden material or network, and the
  approved manifest does not accept the corresponding weaker design, THEN THE SYSTEM SHALL exit
  5 with reason `isolation-unverified` before any adapter invocation.
- **REQ-22 Approval binding.** IF the manifest's configuration hash differs from the approval
  record's `config_sha256`, THEN THE SYSTEM SHALL exit 4 with reason `approval-mismatch` before
  creating a workspace or invoking an adapter.
- **REQ-23 Interactive approval.** IF `golden-eval.py approve` runs without a terminal on both
  standard input and standard output, or the typed confirmation does not equal the first 12
  hexadecimal characters of the configuration hash, THEN THE SYSTEM SHALL exit 4 without
  writing an approval record.
- **REQ-24 Reservation.** WHEN an attempt is about to launch, THE SYSTEM SHALL first append and
  fsync a `reserved` ledger event, which counts toward `max_attempts` and
  `max_attempts_per_unit` whatever happens afterwards.
- **REQ-25 Spend limits.** IF the next launch would make the spend bound of
  `## Contracts & Interfaces → Limits` exceed `max_cost_usd`, or the bound cannot be computed,
  THEN THE SYSTEM SHALL not launch it and SHALL exit 6 with the reason named there.
- **REQ-26 Cancellation.** WHEN the runner receives SIGINT or SIGTERM, THE SYSTEM SHALL stop
  scheduling, send SIGTERM to the active adapter process group, send SIGKILL after
  `termination_grace_seconds`, capture the workspace, record the attempt as `cancelled`, and
  exit 7.
- **REQ-27 Resume without automatic restart.** WHEN `run --resume <experiment-dir>` runs, THE
  SYSTEM SHALL proceed by `## Contracts & Interfaces → Resume`, launching no new attempt for a
  unit with a finished attempt unless `--retry-incomplete` is given, its last outcome is
  `technically-incomplete`, and `max_attempts_per_unit` allows it.
- **REQ-28 Critical missed defect halts the variant.** WHEN an attempt has a missed defect of
  severity `critical`, THE SYSTEM SHALL record every not-yet-launched unit of that variant as
  `stopped-by-policy` with reason `critical-missed-defect` and launch no further attempt of that
  variant in the experiment.
- **REQ-29 Outcomes.** THE SYSTEM SHALL assign each finished attempt exactly one outcome by the
  first matching row of the DM-10 outcome table and derive unit outcomes as defined in
  `## Terminology`.
- **REQ-30 Blinding.** THE SYSTEM SHALL give human evaluators only the evaluation queue of DM-9,
  addressed by attempt keys and blinded labels, and keep the variant mapping in `blinding.json`
  (mode 0600) and in reports only.
- **REQ-31 Disputes.** WHEN a human `review` record's status differs from the automated outcome
  (`accepted` versus not `independently-accepted`, or `rejected` versus
  `independently-accepted`), THE SYSTEM SHALL open a dispute that only a
  `dispute-resolution` record by the manifest's `evaluation.dispute_resolver` closes.
- **REQ-32 Held-out reveal.** WHEN `report --reveal-holdout` runs, THE SYSTEM SHALL append a
  `holdout-revealed` event with the configuration hash and holdout task ids to the family
  journal and report holdout metrics; without the flag, holdout metrics are `sealed`.
- **REQ-33 Cost per accepted result.** THE SYSTEM SHALL compute workload cost, experimental
  evaluation cost, coverage and cost per accepted result per variant and split by calling spec
  05's `summarize_outcomes` with the mapping of DM-11.
- **REQ-34 Unknown usage stays unknown.** IF an adapter result or recorded metadata lacks a cost,
  call count or token count, THEN THE SYSTEM SHALL store `null` with `cost_source: absent` (for
  cost) and report the affected sums as incomplete, never as `0`.
- **REQ-35 Missing pytest.** IF `pytest` cannot be imported by the interpreter running the
  offline suite or `check`, THEN THE SYSTEM SHALL run every check that does not need it, print
  one diagnostic naming `pytest` and the provisioning command of A-27, install nothing, and exit
  3.
- **REQ-36 No remote effects.** THE SYSTEM SHALL create each workspace with no git remote and
  pass no `--allow-pr` argument in any case prompt.
- **REQ-37 Safe template.** THE SYSTEM SHALL ship `tests/golden/manifest-template.json` with
  `approval: null`, `execution_enabled: false` and every model, price and limit field `null`, for
  which `validate-manifest` reports `valid: true, runnable: false`.
- **REQ-38 Recorded results.** WHEN `golden-eval.py import-recorded` imports a workspace for a
  unit of a `recorded` variant, THE SYSTEM SHALL capture and evaluate it exactly like a live
  attempt and label it `execution_source: recorded`.
- **REQ-39 Source and instruction pinning.** IF the source checkout HEAD differs from
  `sources.source_revision`, its tracked tree is dirty, a case digest differs from the
  manifest, the instructions digest differs from `sources.instructions_digest`, or the adapter
  CLI version differs from the declaration, THEN THE SYSTEM SHALL exit 5 before any adapter
  invocation, naming the mismatch.
- **REQ-40 Documentation.** THE SYSTEM SHALL provide `docs/GOLDEN-RUNS.md` with the sections
  listed in `## Contracts & Interfaces → Documentation`, an index row in `docs/README.md` and an
  inventory row in `scripts/README.md`.
- **REQ-41 Exclusive experiment directory.** IF another process holds the experiment
  directory's lock, THEN THE SYSTEM SHALL exit 9 with reason `busy` without changing any file of
  that directory.
- **REQ-42 Report content.** THE SYSTEM SHALL keep prompts, model output text, conversation
  transcripts and environment variable values out of `report.json` and `report.md`.
- **REQ-43 Retention.** THE SYSTEM SHALL record `retain_until` (experiment start date plus
  `data.retention_days`) in `experiment.json` and every report, and SHALL delete no artifact
  automatically.
- **REQ-44 Count and time limits.** IF launching the next attempt would exceed `max_attempts`,
  `max_attempts_per_unit` or `max_total_wall_seconds` (elapsed run time of the experiment), THEN
  THE SYSTEM SHALL not launch it, record the unit as `stopped-by-policy` with reason
  `attempt-limit`, `unit-attempt-limit` or `total-wall-limit`, and exit 6 after the remaining
  schedule is processed.
- **REQ-45 Attempt timeout.** WHEN an attempt runs longer than `max_wall_seconds_per_attempt`,
  THE SYSTEM SHALL terminate it as in REQ-26, record it `stopped-by-policy` with reason
  `timeout`, and continue with the next unit.
- **REQ-46 Held-out contamination.** IF an experiment's task appears in a family-journal
  `holdout-revealed` event with a different configuration hash, THEN THE SYSTEM SHALL list the
  task under `contamination` and exclude it from holdout metrics and decisions.
- **REQ-47 Workspace location.** IF the workspace path, the attempt log root or the helper home
  lies inside the source checkout, an artifact root, a `cases_root` or a root listed in the
  project registry, or the registry cannot be read when it exists, THEN THE SYSTEM SHALL exit 5
  with reason `workspace-location` before any adapter invocation.
- **REQ-48 Quick-gate expectations.** THE SYSTEM SHALL record for every catalog pair the expected
  flow tier and SHALL fail SA-03 when the run's `flow:` differs from it.
- **REQ-49 Deterministic reference builds.** WHEN `build-reference` runs more than once for the
  same case files, workflow and `--date-base`, THE SYSTEM SHALL produce byte-identical workspace
  files and identical commit and tree ids, as defined under `## Contracts & Interfaces →
  Reference build determinism`.
- **REQ-50 Published cases stay tuning.** IF a manifest task with `split: "holdout"` names a
  case whose `case.json` declares `published: true`, THEN THE SYSTEM SHALL reject the manifest
  with exit 2 and reason `published-case-holdout`.
- **REQ-51 Branch-model-aware structure checks.** WHERE the task's branch model fact is
  `per-composite`, THE SYSTEM SHALL evaluate SA-10 and SA-11 by their `per-composite` rules, and
  by their `per-leaf` rules otherwise.
- **REQ-52 Variant switches.** WHEN a unit of a variant with non-empty `switches` launches, THE
  SYSTEM SHALL apply its prompt arguments, environment entries and overlay as defined under
  `## Contracts & Interfaces → Variant switches`.
- **REQ-53 Role keys.** IF a manifest variant's `roles` does not have exactly the keys
  `orchestrator`, `arbiter`, `implementer` and `validator`, THEN THE SYSTEM SHALL reject the
  manifest with exit 2 naming the variant.
- **REQ-54 Owner policy files in the instructions digest (Q-07, D-01).** THE SYSTEM SHALL list
  in the shipped `claude` declaration's `instruction_paths` the entries
  `$XDG_CONFIG_HOME/orchestrail/effort-policy.json` (spec 16, owner effort policy) and
  `$XDG_CONFIG_HOME/orchestrail/repair-policy.json` (spec 17, owner repair policy) and SHALL
  include each in the instructions digest as defined in `## Data Model`. WHEN such a file does
  not exist, THE SYSTEM SHALL contribute the line `absent  <entry>` for it, so that absence is a
  stable value distinct from every present file. IF a policy entry exists but is not a readable
  regular file or its content is not one valid JSON document under the Data Model rules, THEN
  THE SYSTEM SHALL exit 2 with reason `policy-file-invalid` naming the entry, in the invocation
  and manifest validity stage of `run` (before authorization, lock and preflight) and in
  `validate-manifest --print-current`, and SHALL NOT treat the file as absent.

## Data Model

All entities are new. JSON files are UTF-8, parsed with rejection of duplicate keys, `NaN`,
`Infinity` and non-integer numbers; decimals are strings matching
`(?:0|[1-9][0-9]*)(?:\.[0-9]+)?` (the grammar of `scripts/usage_telemetry_outcomes.py:14`);
timestamps are UTC `YYYY-MM-DDTHH:MM:SS.mmmZ`. Canonical JSON is
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` encoded as UTF-8.
A **tree digest** of a directory is the SHA-256 of the concatenation, in byte order of relative
POSIX path, of the lines `<sha256-of-content>  <relative-path>\n` for every regular file, skipping
only `.git/` and `__pycache__/` directories at any depth; a symbolic link is followed when it
resolves to a regular file inside the root and is an error otherwise; any other file type is an
error. Digests used by this spec:

- **Case digest** (`tasks[].case_digest`): tree digest of the whole case directory
  (`case.json`, `project/`, `hidden/`, `reference/`) under `tests/golden/cases/` or the task's
  `cases_root`.
- **Seed digest**: tree digest of the case's `project/`, including its `.ai/`.
- **Instructions digest** (`sources.instructions_digest`): for each adapter `instruction_paths`
  entry in declaration order, a leading `~` is replaced by the runner's `HOME`; a missing path
  contributes the line `absent  <entry>\n`, a regular file `<sha256>  <entry>\n`, a directory
  `<tree digest skipping every entry whose name starts with ".">  <entry>/\n`; the digest is the
  SHA-256 of the concatenated lines. An entry that starts with `$XDG_CONFIG_HOME/` is an **owner
  policy entry** (REQ-54): the prefix is replaced by the runner's resolved configuration base
  (`XDG_CONFIG_HOME` when set and non-empty in the runner's environment, otherwise
  `$HOME/.config`, with `HOME` as for `~`; the child environment passes both variables through,
  see `Workspace and child environment`, so the digest covers what the executor reads), it must
  name a regular file, and its line keeps the literal entry text, so the digest does not depend
  on the absolute path. The manifest's configuration hash (Terminology) covers `sources.instructions_digest`
  (it is the hash of the manifest without `approval`; REQ-22 binds approval to it), so a change in an owner policy file changes the configuration hash.

Every document carries `schema_version: 1`; an unknown version is rejected with exit 2.

### DM-1 Case layout and `case.json`

```
tests/golden/cases/<case>/
  case.json
  project/                          seed project (copied into workspaces)
  hidden/tests/*.py, hidden/defects.json   evaluator-only
  reference/<workflow>/overlay/     evaluator-only: final files of a correct run
  reference/<workflow>/history.json evaluator-only: steps that build a correct run
```

`case.json` fields:

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | int | `1` |
| `case` | string | Case id; equals the directory name |
| `test_command` | list of strings | Open-test argv run in the workspace: `["python3", "-m", "pytest", "-q", "tests"]` |
| `test_globs` | list of globs | Paths that count as test files: `["tests/**/*.py"]` |
| `workflows` | object | Key = case workflow (names per Notes → Spec 09 coupling); value `{"entry": "spec-run"\|"phase-pipeline"\|"bugfix", "prompt": string, "commits": bool, "expect_flow": "full"\|"quick", "parallel": int}`; `entry` is the pipeline workflow the prompt invokes and the key may differ from it (for example a later `spec-run-parallel-2`); `commits` is true exactly when `entry` is `spec-run`; `parallel` (default 1) is the child concurrency N the prompt requests and SA-10/SA-11 use; a prompt with `parallel` > 1 contains `--parallel <N>` |
| `acceptance_ids` | list of strings | Spec criterion ids (`AC-01`, …) expected `PASS` in `## Contract Check` |
| `allowed_paths` | list of globs | Paths a run may create or change (always including `.ai/**`) |
| `forbidden_paths` | list of globs | Paths a run must not change; take precedence over `allowed_paths` |
| `pinned_tests` | list of `"path::function"` | Seed test functions whose source must stay identical |
| `dependency_chain` | list of paths | Modules whose owning leaves must complete in this order (`flat` only) |
| `max_changed_files` | int or null | Quick-gate file limit (3 for `quick` and `bugfix`, else null) |
| `published` | bool | `true` when the case's reference result is published (`flat`, by spec 21 REQ-11); such a case may only be a `tuning` task (REQ-50) |

`hidden/defects.json`: `{"schema_version":1,"defects":[{"defect_id":"D-1","severity":"critical|important|optional","detected_by":["<file>::<test>"]}]}`;
every hidden test appears in exactly one defect's `detected_by`.

`reference/<workflow>/history.json`: `{"schema_version":1,"date_base":timestamp,"steps":[…]}`
with steps applied in order to a fresh workspace holding the seed commit:

| Step | Fields | Effect |
|---|---|---|
| `branch` | `name`, `from` | `git switch -c <name> <from>` |
| `switch` | `name` | `git switch <name>` |
| `commit` | `type`, `subject`, `paths` | Copy `paths` from `overlay/`, stage exactly them, commit `<type>: <subject>`; author and committer `Golden Reference <reference@example.invalid>`, date `date_base` + n seconds for the n-th commit |
| `merge` | `branch`, `into`, `message` | `git switch <into>` and `git merge --no-ff -m <message> <branch>` with the identity of the `commit` step; a merge commit takes the next number n (and date) in the same sequence as `commit` steps, so `{C<n>}` can name it |
| `log` | `event` (`run-start`, `step`, `run-end`) and the arguments of `scripts/log-step.sh` | Invoke the helper from the helper home with `ORCHESTRAIL_LOG_ROOT` = the reference log root |
| `finalize` | — | Copy every remaining overlay file, replacing `{C<n>}` with the full sha of the n-th commit and `{c<n>}` with its first 7 characters |

Initial catalog (five catalog pairs). Every seed declares in `.ai/memory/architecture.md` that the
package is unreleased and has no consumers, so quick-gate condition 3 holds; flow tiers then
follow from file counts and invariants (`rules/quick-flow.md:28-50`).

| Case | Package and behaviour | Workflows and expected flow | Defects (severity) | Detection targets |
|---|---|---|---|---|
| `flat` | `textstats`, one module per criterion: AC-01 `tokenize.py` `tokenize(text)` returns `re.findall(r"[^\W_]+", text.casefold())`; AC-02 `counts.py` `word_counts(text)` returns a `dict` of token counts; AC-03 `top.py` `top_words(text, n)` returns `(word, count)` pairs sorted by count descending then word ascending, at most `n`, `[]` for `n <= 0`. Three modules plus three test files exceed the quick file limit. `dependency_chain`: the three modules in order. | `spec-run` → `full`; `phase-pipeline` → `full` | D-1 tie order (important), D-2 Unicode casefold (important), D-3 `n` larger than vocabulary (optional) | missed leaf, dependent work before the previous review, wrong branch order, incomplete traceability |
| `composite` | `money`: AC-01 `parse.py` `parse_amount(text) -> int` cents for `^-?\d+(\.\d{1,2})?$`, `ValueError` otherwise; AC-02 `format.py` `format_amount(cents: int) -> str` with exactly two decimals and a leading `-` for negatives; AC-03 (integration) `format_amount(parse_amount(s)) == s` for every canonical `s`. The spec states the shared contract (integer cents) as a cross-module invariant. | `spec-run` → `full` | D-1 interface mismatch (critical), D-2 negative sub-unit amounts such as `-0.05` (important) | successful children with a broken shared contract, missing integration validation, wrong final composite state |
| `quick` | `slug`: existing `slugify(text)`; add `max_length: int \| None = None` — AC-01 unchanged output when `None`; AC-02 truncate at the last hyphen not beyond `max_length`; AC-03 truncate the first word when it alone exceeds `max_length`; AC-04 `ValueError` when `max_length <= 0`. Only `src/slug/__init__.py` and `tests/test_slug.py` may change. | `phase-pipeline` → `quick` | D-1 changed output when `None` (critical), D-2 boundary at exact length (important) | missing quick contract, artificial decomposition, lost off-limits constraint |
| `bugfix` | `pager`: seed `total_pages(n, per_page)` uses floor division; correct is ceiling, `0` for `n == 0`, `ValueError` for `per_page <= 0`; neighbour `page_slice(items, page, per_page)` must not regress; defect report `docs/defect-total-pages.md` numbers its criteria `AC-01`–`AC-03`. Only `src/pager/__init__.py` and `tests/test_pager.py` may change; `pinned_tests` lists the seed's `page_slice` tests and its `total_pages` tests, which use only inputs where floor and ceiling division agree (`n` a multiple of `per_page`, including `n == 0`). | `bugfix` → `quick` (prompt `/bugfix "docs/defect-total-pages.md" --auto-mode`) | D-1 defect not fixed (critical), D-2 `page_slice` regression (important) | fix without a reproducing test, changed pinned expected behaviour, neighbour regression |

Every seed contains a filled minimal `.ai/` (principles, `memory/architecture.md`,
`memory/state.md`, `context/runbook.md` with `test:` equal to `test_command`, `adr/index.md`)
derived from `templates/.ai/`, a `.gitignore` containing `.ai/`, a project `CLAUDE.md`, the spec
or defect report with numbered criteria, the source package and open tests. Seed open tests
pass on the seed.

### DM-2 Capture (`attempts/<attempt_key>/capture/`)

`workspace/` (full copy including `.git`), `git.json` (every commit reachable from any ref: full
sha, parents, subject, changed paths; refs with targets; the seed commit, which is the single
root commit reachable from HEAD), `run-log/` (copy of the attempt log root), `commands.json`
(argv, exit code, duration, stdout/stderr file names of open tests, probes and hidden checks),
`adapter/` (argv, exit code, stdout, stderr, parsed result) and `capture.json` with the tree
digest of `workspace/`, `seed_digest` and the list of capture errors. For live attempts the runner
computes `seed_digest` over the workspace right after the seed commit (excluding `.git/`); it must
equal the case's seed digest. For every capture, the seed commit's tracked files must equal the
seed project's files outside `.ai/`. The capture step is `error` when any of these cannot be
written or either comparison fails. A recorded import has no observable seed `.ai/`; its record
carries `seed_context: "unverified"` and reports list such attempts.

### DM-3 Facts, semantic assertions and hidden checks

Facts are written to `facts.json` (key layout chosen by the implementation, versioned). Required
facts and their sources:

| Fact | Source | Missing/ambiguous → |
|---|---|---|
| Task directory | Exactly one directory under `.ai/tasks/todo/` or `.ai/tasks/completed/` whose `state.md` is new or differs from the seed | error |
| `flow:`, `kind:`, `## Phases` values | Task `state.md` (`rules/workflow-globals.md:160-169`, `workflows/bugfix.md:37-45`) | error |
| Leaf and composite blocks, fields by name | `## Subtask Progress` (`:175-186`, `:210-219`) | error when a block header is unparsable |
| Leaf mode and leaf tests | `notes:` entries — the value and continuation lines of every `notes` field group split at line breaks and at `; ` per spec 13 Data Model → Note entries, which joins to a `tdd: red digest —` entry each following piece on its line that matches `^.+ → test_\w+(, test_\w+)*$` and starts with none of `tdd:`, `context-` or `verification:`, because the digest separates its behaviours with `; ` (`workflows/pae-tests.md:210`, `:225`) — starting with `tdd: characterize —` (pinned), `tdd: none —` (n-a), `tdd: red digest —` (test names: every `test_\w+` after any `→` within that entry only); these three are the only entries read and every other entry, such as `tdd: red output` or `tdd: green output`, is ignored | error when a name matches functions in two files |
| `plan.md` subtask statuses | Status table (`:268-278`) | error for `full` flow; not read for `quick` |
| Contract Check rows | `## Contract Check` tables; a row's criterion id is the first token matching `AC-\d+` in its Criterion cell, else none | error when the section is absent and `validation` is `complete` |
| Issue List entries | `### Approved`, `### Deferred`; an entry is a line matching `^\s*(?:[-*]\s*)?\[?(\d+)\]?[.):]?\s`; `None` means empty | error when a subsection has other non-empty content |
| Quick contract and TDD record | `## Contract (quick)`, `## TDD (quick)` (`tests:` names, `level:`, `red-observed:`, `green-observed:`) | error for `quick` flow |
| Commits, refs | `git.json` | error |
| Branch model | Task `state.md` `branch_model:` resolved by spec 22 DM-1's reader rule: the value when present; absent with any block recording `branch:` → `per-leaf`; otherwise none | error for a value other than `per-leaf` or `per-composite` |
| Changed paths | Final workspace tree versus the baseline (seed project plus the variant's switch overlay, `Variant switches`) by per-file content hash, excluding `.git/` | error |
| Run-log events | JSONL files under the captured log root, ordered by run and `seq` | absent store → empty list |
| Open-test result | `test_command` exit code | error when it cannot start |

Semantic assertions:

| Id | Rule | `not-applicable` when |
|---|---|---|
| SA-01 | Task directory fact exists | never |
| SA-02 | All three phases `complete` | never |
| SA-03 | Flow equals `expect_flow`; every `plan.md` subtask is `reviewed` and has a progress block and vice versa; every composite has `rollup: done` and `integration-validation: complete` | plan and composite parts for `quick` |
| SA-04 | Every leaf block has `target_files:`, `blocker:` and `notes:`; every leaf with `atomic-execution` other than `not-started` has `atomic-tests:` unless SA-14 passes for it; composite blocks have `children:`, `blocker:`, `notes:` | `quick` |
| SA-05 | TDD evidence table below | never |
| SA-06 | Each leaf test function's source at the leaf's `test` commit equals its source at HEAD, unless a `tdd: test amended — <test name>` line names it | workflow `commits: false` |
| SA-07 | No Acceptance Criteria row is `FAIL`; the number of rows is at least the number of `acceptance_ids`; every `acceptance_ids` entry found as a row id is `PASS` | never |
| SA-08 | Number of Contract Check `FAIL` rows ≤ number of Issue List entries (approved + deferred) | never |
| SA-09 | Every changed path matches `allowed_paths` and none matches `forbidden_paths`; changed paths outside `.ai/` ≤ `max_changed_files` when set | never |
| SA-10 | Rules by branch model (DM-3 fact). **`per-leaf` or field absent:** each leaf has `branch:`, `base_branch:`, `base_commit:`, `commits:`; `base_commit` and every listed commit resolve; the first leaf's `base_branch` is the seed branch and each later leaf's `base_branch` is the previous leaf's `branch` in plan order. **`per-composite`** (spec 22 DM-1, DM-2): the stack entries are the top-level leaves and composites in plan order, children excluded; every entry and every child has `branch:`, `base_branch:`, `base_commit:`, `commits:`; `base_commit`, every listed commit and every child `merge_commit` resolve, while a child's `branch:` need not exist; the first entry's `base_branch` is the seed branch, and each later entry's `base_branch` is the previous entry's `branch` with `base_commit` equal to the previous entry's last listed commit; each child's `base_branch` is its composite's `branch`; the composite's start tip is its last listed commit that precedes its first `merge` entry (a promoted leaf's own commits, spec 22 REQ-37) or its `base_commit` when there is none; at N = 1 exactly one child of a composite has the start tip as `base_commit` and every other child's `base_commit` equals another child's `merge_commit` in that composite; at N > 1 each child's `base_commit` equals or descends from the `merge_commit` of each prerequisite child (plan `Depends On`) in the same composite; each child's `merge_commit` has a first parent equal to (N = 1) or descending from (N > 1) the child's `base_commit`, a second parent equal to the child's last listed commit, is an ancestor of the composite's last listed commit, and has a subject matching `^Merge branch '[^']+' into \S+$`. N is the case workflow's `parallel`. **Both models:** no commit subject matches `\bT-\d` | workflow `commits: false` |
| SA-11 | For consecutive modules in `dependency_chain`, take the owning leaf of each (the one leaf listing the module in `target_files:`); zero or two owning leaves → failed `chain-leaf-missing`. With commits and `per-leaf` (or field absent): the later owning leaf's `base_commit` equals the earlier owning leaf's last listed commit. With commits and `per-composite`: when both owning leaves are children of one composite, the later child's `base_commit` equals or descends from the earlier child's `merge_commit`; otherwise the stack entry containing the later leaf (the leaf itself or its composite) has a `base_commit` equal to or descending from the last listed commit of the entry containing the earlier leaf. Without commits, completion order only: the later leaf's `pe-execute` step event has a higher `seq` than the earlier leaf's `pe-execute` event with outcome `ok` in the same run, and when either event is absent the result is `not-applicable` with reason `not-observed` | no `dependency_chain` |
| SA-12 | Open-test command exits 0 | never |
| SA-13 | `## Contract (quick)` has `### Off-limits`, `### Invariants`, `### Acceptance Criteria`; `## TDD (quick)` has `level:` and `red-observed:`; no `T-` subtask directories and no `## Subtask Progress` blocks | flow `full` |
| SA-14 | A leaf whose `notes:` contains `pre-TDD task, TDD step skipped` existed in the seed with `atomic-execution: in-progress` and without `atomic-tests:` | no such note |
| SA-15 | Every `pinned_tests` function exists at HEAD with source text identical to the seed (`ast.get_source_segment`) | empty `pinned_tests` |

TDD evidence table for SA-05 — every applicable row must hold; the first failing row's reason is
reported:

| Applies to | Required evidence | Failure reason |
|---|---|---|
| Every leaf of a completed run | Final `atomic-tests:` is `green` or `n-a`, or the field is absent and SA-14 passes | `tdd-incomplete` (final `red`, `pinned`, `failed`, `not-started`) |
| Leaf in red or pinned mode | A `tdd: red digest` line naming at least one test that resolves in `test_globs` files at HEAD | `digest-tests-missing` |
| Leaf in red mode | HC-2: at least one leaf test fails on the seed | `red-not-reproducible` |
| Leaf in pinned mode | HC-2: every leaf test passes on the seed | `pinned-on-new-behaviour` |
| Leaf in n-a mode | The `tdd: none —` line has non-empty text after the dash | `unjustified-n-a` |
| Leaf in red or pinned mode, workflow `commits: true` | A listed commit of type `test` touching only `test_globs` exists and is an ancestor of every other listed commit of the leaf; at least one other listed commit exists. A commit's type is the `type` group of `^(?P<type>[a-z]+)(?:\([^)]*\))?!?: ` on its subject, else `unknown` | `implementation-before-test` |
| Leaf, workflow `commits: false` | Order is not observable; recorded as `order: not-observed` in facts | — |
| Quick/bugfix task | `## TDD (quick)` has `red-observed: yes` and `green-observed: yes`, or `level: none` with `red-observed: n-a — <non-empty justification>`; unless `level: none`, HC-2 shows at least one `tests:` name fails on the seed | `quick-red-missing` |

Hidden checks, executed on a throwaway copy of the final workspace (never in the executor
workspace), under the isolation prefix when the mechanism is `command-prefix`, with `HOME` set
to an empty temporary directory and the child environment allowlist:

| Id | Check |
|---|---|
| HC-1 | Run `pytest` on `hidden/tests/` copied next to the final project; each failed test maps to its defect id and severity |
| HC-2 | Seed replay: copy the seed project, overlay the final versions of the test files that contain leaf tests (or quick `tests:` names), run those test functions by node id; record pass/fail per test function |
| HC-3 | Defect summary: defect ids whose `detected_by` tests failed; with workflow-claimed success each is a missed defect |

### DM-4 Projection and normalization

`projection.json` fields (canonical JSON, lists sorted as stated):

| Field | Content |
|---|---|
| `schema_version`, `normalization_version` | `1`, `1` |
| `case`, `workflow`, `flow` | Strings |
| `branch_model` | `per-leaf`, `per-composite` or `null` (DM-3 fact) |
| `phases` | Object of the three phase values |
| `leaves` | Sorted by id: `{id, mode: "red"\|"pinned"\|"n-a"\|"pre-tdd", atomic_tests, atomic_execution, atomic_validation, plan_status, tdd_order: "git"\|"not-observed", target_files: sorted normalized paths}` |
| `composites` | Sorted by id: `{id, rollup, integration_validation, children}` |
| `contract_check` | `{acceptance: {<criterion id>: "PASS"\|"FAIL"}, unnumbered: {pass: int, fail: int}, invariants_failed: int, off_limits_failed: int}` |
| `issues` | `{approved: int, deferred: int}`; `fix_tasks: int` |
| `commits` | In alias order: `{id: "<Cn>", parents: [aliases], type, paths: sorted}`; the seed commit has type `seed` |
| `branches` | Object alias-or-seed-branch-name → commit alias |
| `changed_paths` | Sorted normalized paths |
| `open_tests` | `{exit_code: int}` |
| `stops` | Run-log steps with outcome `blocked` or `failed` and `run-end` outcomes, as `{step, outcome}` in log order |
| `quick` | `null` or `{contract_sections: sorted, tdd_level, red_observed: "yes"\|"n-a"\|"absent", decomposed: bool}` |

Free text (notes, subjects, descriptions, issue text) is excluded after extraction succeeds.

Normalization rules, version 1:

- **NR-1 Paths.** An absolute path inside the workspace becomes workspace-relative POSIX; an
  absolute path outside it becomes `<EXTERNAL>/<basename>`.
- **NR-2 Commits.** Commits get aliases `<C1>`, `<C2>`, … in the order of
  `git rev-list --all --topo-order --reverse`; a full or abbreviated (at least 7 hex) id that
  resolves to exactly one captured commit is replaced by its alias.
- **NR-3 Branches.** The seed branch keeps its name; other branches become `<B1>`, `<B2>`, … in
  the alias order of their tip commits, ties by name.
- **NR-4 Volatile values.** Timestamps, run ids, session ids and durations are not part of the
  projection.

### DM-5 Candidates and expected review records

Candidate directory `<artifact-root>/candidates/<case>/<workflow>/<first 12 hex of
projection_sha256>/`: `projection.json`, `diff.txt` (against the current expected projection or
against an empty object), `changed-facts.json` (projection top-level keys whose values differ),
and `candidate.json` `{schema_version:1, case, workflow, projection_sha256, steps: {capture,
extract, assert, evaluate}, origin: "synthetic-reference"|"check"|"attempt:<experiment_id>/<attempt_key>",
source_revision}`.

Review record `tests/expected/<case>/<workflow>/review.json`:
`{"schema_version":1,"projection_sha256":hex,"normalization_version":1,"source_revision":40-hex,"origin":<candidate origin>,"reason":text,"reviewed_by":text,"reviewed_at":timestamp}`.

### DM-6 Manifest

| Field | Type and rule |
|---|---|
| `schema_version` | `1` |
| `experiment_id`, `experiment_family` | `^[a-z0-9][a-z0-9-]{0,63}$` |
| `created` | `YYYY-MM-DD`; `owner` non-empty text |
| `purpose` | `regression` (exactly one variant; `analysis`, `quality`, `baseline_variant` null) or `comparison` (at least two variants, `baseline_variant`, `analysis`, `quality` set) |
| `approval` | `null` or a path relative to the manifest to a DM-7 record; excluded from the configuration hash |
| `execution_enabled` | bool |
| `sources` | `{source_revision: 40-hex, instructions_digest: 64-hex}` |
| `tasks[]` | `{task_id: ^[a-z0-9][a-z0-9-]{0,31}$, case, workflow, split: "tuning"\|"holdout", risk, complexity, context_size: "low"\|"medium"\|"high", observability: text, provenance: "synthetic"\|"owner-selected", cases_root: path\|null, anonymization_record: text\|null, case_digest: 64-hex}`; `risk`/`complexity` are `low`/`medium`/`high`; `owner-selected` requires a `cases_root` outside the repository and a non-empty `anonymization_record`; a task whose case declares `published: true` has `split: "tuning"` |
| `exclusion_rules[]` | `{rule_id, description}` |
| `variants[]` | `{variant_id: ^[A-F][a-z0-9-]{0,15}$, strategy: "A".."F", availability, adapter: "claude"\|null, roles: {orchestrator\|arbiter\|implementer\|validator: {model: string\|null, effort: "low"\|"medium"\|"high"\|"xhigh"\|"max"\|"session-default"\|null}}, permission_mode, allowed_tools[], disallowed_tools[], context_preparation, verification, retries, escalation, selection_rationale, strategy_details, switches}`; `roles` has exactly the four keys `orchestrator`, `arbiter`, `implementer` and `validator` (the roles of the `orchestration` rule; spec 16 DM-3 reads the last three); `switches` is defined under `Variant switches`; `executable` requires one adapter, every role with the same model and effort, and non-null fields; `strategy_details` holds non-empty text keys per strategy: A `planner_and_reviewer`, `same_models_by_role`; B `reviewer_cost`, `repair_policy`, `escalation_limits`; C `handover`, `shared_plan_scope`, `plan_staleness`; D `routing_rules`, `features`, `switch_point`; E `level_order`, `transition_conditions`, `early_stop_risks`; F `composition`, `frozen_rules` |
| `baseline_variant` | A `variant_id` or null |
| `order` | `{repetitions: int ≥ 1, method: "fixed"\|"seeded-hash", seed: int\|null}`; `seeded-hash` requires `seed` |
| `cache` | `{condition: "cold"\|"warm"\|"unspecified", reuse_policy: text}` |
| `limits` | `{max_attempts, max_attempts_per_unit, max_wall_seconds_per_attempt, max_total_wall_seconds, termination_grace_seconds: int ≥ 1; max_cost_usd, max_cost_usd_per_attempt: decimal; unknown_cost_policy: "refuse"\|"count-at-cap"; accept_unverified_cost_cap: bool}` |
| `quality` | `{primary_metric: "independent_acceptance_rate", delta: decimal in [0,1), followup_window_days: int ≥ 0}` or null |
| `analysis` | `{method: "paired-cluster-bootstrap", confidence: decimal in (0,1), resamples: int ≥ 1, seed: int, multiplicity: "bonferroni"\|"holdout", decision_split: "tuning"\|"holdout", selected_candidate: variant_id\|null, denominator: "planned"\|"completed-with-censoring", r_max: decimal in (0,1)}` or null; `holdout` multiplicity requires `decision_split: "holdout"` and `selected_candidate` |
| `evaluation` | `{owner: text, dispute_resolver: text}` |
| `environment` | `{isolation: {mechanism: "none"\|"command-prefix", prefix: [string]\|null, network_probe_target: "host:port"\|null}, accepted_weaker_isolation: null\|{hidden_material: bool, network: bool, reason: text}}`; `network` acceptance also accepts that remote effects with the owner's credentials under `HOME` are not prevented |
| `data` | `{artifact_root: path\|null, retention_days: int ≥ 1, export_policy: text}` |
| `stop` | `{resume_allowed: bool}` |
| `decision` | `{rollback: text}` |

A manifest is **valid** when its shape and types are correct with `null` allowed for every
owner-chosen value; it is **runnable** when it is valid, `execution_enabled` is true, no
required value is `null`, and every referenced case, case workflow and adapter exists. Unknown
fields are an error.

### DM-7 Approval record

`{"schema_version":1,"approval_id":uuid4,"experiment_id":text,"config_sha256":64-hex,"approved_by":text,"approved_at":timestamp,"scope":{"max_attempts":int,"max_cost_usd":decimal},"confirmation":first-12-hex}`.

### DM-8 Adapter declaration (`tests/golden/adapters/<name>.json`)

`{"schema_version":1,"adapter":"claude","executable":"claude","verified_cli_version":"2.1.323","version_argv":["--version"],"argv":[…],"alias_names":["fable","haiku","opus","sonnet"],"effort_values":["low","medium","high","xhigh","max"],"per_attempt_cost_cap":"unverified","instruction_paths":["~/.claude/CLAUDE.md","~/.claude/settings.json","~/.claude/skills","$XDG_CONFIG_HOME/orchestrail/effort-policy.json","$XDG_CONFIG_HOME/orchestrail/repair-policy.json"],"env_passthrough":[],"result":{"format":"json","cost_usd":null,"model":null,"calls":null}}`.

`argv` holds literal strings and the placeholders `{prompt}`, `{model}`, `{effort}`,
`{permission_mode}`, `{allowed_tools}`, `{disallowed_tools}`, `{max_cost_usd_per_attempt}`. The
shipped `claude` declaration is
`["-p","{prompt}","--model","{model}","--effort","{effort}","--output-format","json","--max-budget-usd","{max_cost_usd_per_attempt}","--permission-mode","{permission_mode}","--allowedTools","{allowed_tools}","--disallowedTools","{disallowed_tools}","--no-session-persistence"]`;
the `--effort` pair is omitted for `session-default`; a tool list is joined with `,` and its pair
is omitted when the list is empty. `per_attempt_cost_cap` is `verified`, `unverified` or
`absent`. `result` maps names of top-level fields of the parsed JSON result; `null` means unknown
(Q-02). Changing a declaration changes `adapter.declaration_sha256` in attempt records; the
declaration file belongs to the source revision pinned by the manifest.

### DM-9 Experiment directory, ledger and evaluation queue

```
<artifact-root>/<experiment_id>/
  .lock                       fcntl.flock target
  experiment.json             manifest_sha256, approval_sha256, config_sha256, started_at, retain_until, isolation result
  manifest.json, approval.json  byte copies from the first run
  plan.json                   ordered units with attempt keys
  ledger.jsonl                append-only; each event flushed and fsynced
  blinding.json               mode 0600: variant_id → blinded label
  attempts/<attempt_key>/     attempt.json, capture/, facts.json, assertions.json, hidden/, projection.json, compare/
  evaluation-queue/<attempt_key>/   evaluation input: queue.json, workspace copy, facts.json, assertions.json, hidden results
  evaluations/<attempt_key>/<revision>.json
  reports/<YYYYMMDDTHHMMSSZ>/report.json, report.md
<artifact-root>/candidates/…                 DM-5
<artifact-root>/families/<experiment_family>.jsonl   holdout-revealed events
```

Default `<artifact-root>` is `<source checkout>/output/golden`; `--artifact-root` or
`data.artifact_root` overrides it. Directories are created with mode 0700. `unit_id` is
`<task_id>.<variant_id>.r<repetition>` and appears only in `plan.json`, `attempt.json`, the
ledger and reports. The attempt key is `a-` plus the first 16 hex characters of SHA-256 of
`<config_sha256>:<unit_id>:<attempt_no>`. The blinded label of a variant is `V-` plus the first 8
hex characters of SHA-256 of `<config_sha256>:<variant_id>`. `queue.json` holds only
`{attempt_key, blinded_label, task_id, case, workflow, split}`. The queue's workspace copy omits
`.git/`; in `plan.md` every table cell under a header starting with `Model` is replaced by
`<redacted>`; in the task `state.md` every line of the `## Model Selection` section after its
heading is replaced by `<redacted>`; the queue omits the attempt record, adapter output and commit
bodies. Free text
written by the run elsewhere may still reveal a model; this is a stated limit of blinding. Order `seeded-hash` sorts units by SHA-256 of
`<seed>:<task_id>:<variant_id>:<repetition>`; `fixed` uses manifest order of tasks, then
variants, then repetitions. A ledger event is `{seq: int from 1, ts, event, unit_id|null,
attempt_key|null, details: object}` with `event` in `reserved`, `launched`, `finished`,
`refused`, `resumed`, `evaluation-recorded`, `dispute-opened`, `dispute-resolved`,
`exclusion-recorded`, `usage-attached`.

### DM-10 Attempt record (`attempt.json`) and outcomes

Fields: `attempt_key`, `unit_id`, `experiment_id`, `task_id`, `case`, `workflow`, `variant_id`,
`blinded_label`, `repetition`, `attempt_no`, `split`, `execution_source` (`live`, `recorded`),
`seed_context` (`verified`, `unverified`),
`requested` `{model, effort}`, `actual` `{model: string|null}`, `adapter` `{name, cli_version,
declaration_sha256}`, `isolation` `{hidden_material: "enforced"|"weakened", network:
"enforced"|"weakened", reason|null}`, `started_at`, `ended_at`, `elapsed_ms`, `exit_code`, `steps`
(`launch`, `capture`, `extract`, `assert`, `evaluate`, `normalize`, `compare`, each `{status,
reason}`), `assertions` `{SA-id: status}`, `hidden` `{HC-id: status}`,
`workflow_claimed_success: bool|null`, `missed_defects: [{defect_id, severity, source:
"hidden"|"late"}]`, `outcome`, `outcome_reason`, `usage` `{cost_usd: decimal|null, cost_source:
"adapter-reported"|"attached"|"absent", coverage: "complete"|"incomplete"|"unknown", calls:
int|null, tokens: {input, cached_input, cache_write, output: int|null}}`, `golden` `{status,
expected_sha256|null, projection_sha256|null}`. A record with `cost_source: absent` and a
non-null `cost_usd` is invalid.

Outcome rules, first match wins (records are the experiment's evaluation records for the
attempt):

| # | Condition | Outcome |
|---|---|---|
| 1 | An `exclusion` record names a manifest `rule_id` | `excluded` |
| 2 | Runner received SIGINT/SIGTERM during the attempt | `cancelled` |
| 3 | Timeout, model mismatch, or a refusal recorded against the attempt | `stopped-by-policy` |
| 4 | Launch failed to start, the adapter ended without a parsable result, the attempt was orphaned, or capture, extract or evaluate, or any applicable SA or HC, is `error` | `technically-incomplete` |
| 5 | A `late-defect` record is within `followup_window_days` of `ended_at` | `rejected-by-criteria` (`late-defect`) |
| 6 | A `dispute-resolution` record exists | its status: `accepted` → `independently-accepted`, `rejected` → `rejected-by-criteria` |
| 7 | A dispute is open | `rejected-by-criteria` (`dispute-open`) |
| 8 | Any applicable SA or HC is `failed`, or the latest `review` record is `rejected` | `rejected-by-criteria` |
| 9 | Otherwise | `independently-accepted` |

Normalize and compare statuses never change the outcome (REQ-03). A late defect outside the
window is recorded with `source: "late"` and flagged `outside-window` but changes nothing.

### DM-11 Evaluation records and mapping to spec 05

`evaluations/<attempt_key>/<revision>.json`: `{schema_version:1, attempt_key, revision: int
from 2, evaluator, kind: "review"|"late-defect"|"dispute-resolution"|"exclusion", status:
"accepted"|"rejected"|"defect"|null, defect_id|null, severity|null, rule_id|null, reason,
recorded_at}`. `review` and `dispute-resolution` take `accepted` or `rejected`; `late-defect`
takes `defect` with `defect_id` and `severity`; `exclusion` takes `null` with `rule_id`. Records
are never rewritten; revision 1 is reserved for the automated outcome.

Mapping per unit to `summarize_outcomes` (one call per variant and split):

- `opportunities`: one identity per unit — `task_revision` = `<task_id>:<case_digest>`,
  `input_revision` = `config_sha256`, `acceptance_contract` = tree digest of the case's
  `hidden/`, `strategy` = `variant_id`, `repetition`.
- `attempts`: one entry per attempt — `attempt_id` = attempt key, the unit's identity,
  `observed_at` = `ended_at`, `category` = `workload` (or `experimental_evaluation` for usage
  attached with that category), `cost` = `usage.cost_usd`, `complete` = (`coverage == "complete"`).
- `labels`: exactly one label per unit with a finished attempt, derived from the unit outcome so
  that `summarize_outcomes` and METRICS agree — `revision` = 1 + the number of evaluation records
  of the unit's last attempt, `status` = `accepted` for `independently-accepted`, `defect` for
  reason `late-defect`, `rejected` otherwise, `observed_at` = the latest of `ended_at` and the
  records' `recorded_at`. The label carries `opportunity` and `acceptance_contract` equal to the
  identity's. Late defects outside the window produce no label change.
- `as_of` = the latest `observed_at` among the supplied attempts and labels; `verify_acceptance`
  returns true only for labels built from the experiment's own records.

### DM-12 Report

`report.json`: `{schema_version:1, kind:"observed", experiment_id, config_sha256, generated_at,
retain_until, cost_basis:"api-equivalent-usd", holdout_revealed: bool, blinding: {label:
variant_id}, isolation: object, weaker_designs: [names], variants: [{variant_id, strategy,
availability, measured: bool, splits: {tuning: METRICS, holdout: METRICS|"sealed"}}],
comparisons: [{candidate, baseline, decision_split, quality_diff: {estimate, lower,
upper}|null, cost_ratio: {estimate, lower, upper}|null, confidence_adjusted, hard_constraints:
{name: bool}, verdict, reasons}], contamination: [task_id], disputes_open: [attempt_key],
exclusions: [{attempt_key, rule_id}], diagnostics: []}`. Neither `report.json` nor the DM-6 manifest
carries a size limit of its own; a reader that needs one sets it itself (spec 16 DM-3 applies
1,048,576 bytes and rejects a larger file as `qualification-invalid`).

METRICS: `planned`, `started`, `completed`, `pending`, `unit_outcomes` (count per outcome),
`accepted` `{count, denominator}` (denominator per `analysis.denominator`, `planned` for
regression), `censored` `{count, units}`, `first_attempt_success` `{count, denominator}` (units
whose attempt 1 is accepted / units with an attempt 1), `missed_defects` `{critical, important,
optional}`, `calls` `{sum|null, known_attempts}`, `tokens` `{input, cached_input, cache_write,
output: sum|null, known_attempts}`, `attempts_per_unit` `{max, mean}` (retries), `fix_tasks`
`{sum|null}`, `elapsed_ms` `{sum, median, p90, n, small_sample}` (median, nearest-rank p90 and
`n < 5` marker as in completed spec 05's export-composition section, the Russian-language
frozen record, at its line 478),
`worker_time_ms: null` with diagnostic `not-observed`, `cost` (the `summarize_outcomes` result,
with `combined_cost` requested), `acceptance_interval` `{lower, upper, confidence}|null`.
`acceptance_interval` uses the bootstrap of the promotion rule on the per-task acceptance means
of that variant and split; it is `null` with diagnostic `no-analysis` when `analysis` is null.
`report.md` renders the same values; numbers are exact decimal or reduced `n/d` strings.

### DM-13 Calculator input and output

Input: `{schema_version:1, kind:"hypothetical", unit: text, parameters: {<name>: decimal |
{"low": decimal, "high": decimal}}, strategies: [{id, branches: [{id, probability: decimal |
{"param": name} | {"complement": name}, costs: {planning, execution, tools, verification,
repair, escalation: decimal | {"param": name}}, acceptance: decimal | {"param": name}}]}],
break_even: null | {left: strategy id, right: strategy id, parameter: name}}`. At most 16 range
parameters. A parameter may appear only as probabilities or only as costs/acceptances.

Output: `{schema_version:1, kind:"hypothetical", strategies: [{id, expected_cost,
expected_acceptance, expected_cost_per_accepted|null, range: null | {expected_cost: [min, max],
expected_cost_per_accepted: [min, max]|null}}], break_even: null | {parameter, value|null,
status: "found"|"outside-domain"|"none"|"identical"|"not-applicable"}, diagnostics: []}`.
Values are exact decimal strings, or reduced `n/d` strings when no finite decimal exists.

## Contracts & Interfaces

### Command-line interfaces

All Python entry points run as `python3 -I scripts/golden-eval.py <command> …` with Python
3.11 or newer (older → exit 3). Machine output is one JSON object on stdout; diagnostics go to
stderr.

| Command | Arguments | Effect |
|---|---|---|
| `run` | `--manifest FILE` [`--case C --workflow W`] [`--artifact-root DIR`] [`--update`] [`--dry-run`] [`--resume DIR`] [`--retry-incomplete`] | Validate, authorize, lock, preflight, plan and (unless `--dry-run`) execute units; `--case/--workflow` restricts to matching tasks; `--dry-run` takes no lock and creates or changes no file: it prints the plan, preflight results and planned argv per unit and launches nothing; see `Opening an experiment directory` for existing directories |
| `check` | `--case C --workflow W --workspace DIR` [`--run-log DIR`] [`--out DIR`] [`--update`] | Offline capture → compare of a finished workspace (a git repository whose root commit is the seed) with the run-log store `DIR`; no adapter; default `--out` is a new temporary directory printed in the output |
| `build-reference` | `--case C --workflow W --out DIR` [`--date-base TIMESTAMP`] | Build a reference workspace and run-log store from `reference/<workflow>/` (DM-1) |
| `import-recorded` | `--manifest FILE --unit U --workspace DIR --metadata FILE` [`--run-log DIR`] [`--artifact-root DIR`] | REQ-38 and `## Contracts & Interfaces → Recorded imports`; metadata `{models_by_role, effort_by_role, harness, cost_usd|null, calls|null, tokens|null, started_at, ended_at}` |
| `validate-manifest` | `--manifest FILE` [`--print-current`] | `{valid, runnable, missing: [paths], errors: [..]}`; `--print-current` adds the current source revision, instructions digest and case digests; exit 0 when valid, 2 otherwise |
| `approve` | `--manifest FILE --approved-by NAME --out FILE` | REQ-23; prints the configuration hash and reads the confirmation from the terminal |
| `accept-expected` | `--candidate DIR --reason TEXT --reviewed-by NAME` | REQ-17 |
| `evaluate` | `--experiment DIR --attempt KEY --evaluator NAME` and one of `--verdict accepted\|rejected`, `--late-defect ID --severity S`, `--resolve-dispute accepted\|rejected`, `--exclude RULE_ID`; always `--reason TEXT` | Appends a DM-11 record and the matching ledger event; `--resolve-dispute` requires `NAME` = `dispute_resolver` and an open dispute (else exit 2) |
| `attach-usage` | `--experiment DIR --attempt KEY --usage FILE` | Usage `{category: "workload"\|"experimental_evaluation", cost_usd: decimal, coverage: "complete"\|"incomplete", tokens: {…}\|null, source: text, source_sha256: hex}`; sets `cost_source: attached` |
| `report` | `--experiment DIR` [`--reveal-holdout`] | Writes DM-12 |
| `calculate` | `--scenario FILE` | REQ-11 |

`tests/run-golden.sh <case> <workflow> [options]` is a Bash wrapper (`set -uo pipefail`) that runs
`python3 -I scripts/golden-eval.py run --case <case> --workflow <workflow> [options]` from the
source checkout and returns its exit code; without `--manifest` it exits 4.

Exit codes (all commands):

| Code | Meaning |
|---|---|
| 0 | Success; for `run`/`check`, every attempt `independently-accepted` and every compare `passed` |
| 1 | A check failed: assertion, hidden check, golden mismatch, missing expected, rejected outcome, refused candidate |
| 2 | Invalid invocation or invalid input document |
| 3 | Environment unavailable: Python < 3.11, `git` or `pytest` missing, adapter executable missing |
| 4 | Not authorized: no or non-runnable manifest, execution disabled, approval missing or mismatched, approval command refused |
| 5 | Preflight failed: pinning, isolation, workspace location, model alias |
| 6 | Stopped by policy: count, time or spend limit, timeout, model mismatch, variant halt |
| 7 | Cancelled by signal |
| 8 | I/O error or technically incomplete attempt |
| 9 | Experiment directory busy |

`run` evaluates in this order and returns the first failure: invocation and manifest validity
(2), authorization (4), lock (9), preflight (3, 5). After execution starts it returns the highest
of the codes produced by its attempts and refusals among 1, 6, 7 and 8 (0 when none).

### Run sequence (`run`)

1. Parse and validate the manifest and read the owner policy entries of REQ-54 (exit 2); require runnable and approved (exit 4, REQ-10,
   REQ-22).
2. Open the experiment directory (`Opening an experiment directory`); with `--resume`, also
   apply `Resume`.
3. Preflight (exit 3 or 5): REQ-39 pinning; REQ-13 alias check; REQ-47 locations; REQ-21
   isolation; adapter executable on `PATH` and the first whitespace token of its `version_argv`
   output equal to `verified_cli_version`; `python3 -m pytest --version` succeeds with the
   child `PATH`.
4. For each planned unit in order: skip finished units; apply REQ-28 halts; apply REQ-44 and
   REQ-25 (on refusal append `refused` and record the unit outcome); append `reserved`; create
   the workspace, attempt log root and helper home; launch; append `launched`; wait (REQ-45);
   capture; extract; assert; evaluate; normalize; compare; write `attempt.json` and the
   evaluation-queue entry; append `finished`.
5. Exit per the exit-code table.

### Opening an experiment directory

Shared by `run` (not `--dry-run`), `import-recorded`, `evaluate`, `attach-usage` and `report`:
take the lock (exit 9). When the directory does not exist (`run` and `import-recorded` only;
other commands exit 2): create it, copy manifest and approval, write `experiment.json`,
`plan.json`, `blinding.json`. When it exists: commands given `--manifest` compare the given
manifest and its approval bytes with the stored copies (difference → exit 4); `evaluate`,
`attach-usage` and `report` read the stored copies. `run` without `--resume` on a directory whose ledger
holds a `launched` event exits 2 with `experiment-exists`; a directory holding only imports and
evaluations needs no `--resume`. Imports into an existing directory append no extra event
beyond their own.

### Resume

`run --resume DIR`: open the directory; require `stop.resume_allowed` (else exit 4); append
`resumed`; re-run preflight. An attempt with `reserved` but no `finished` is orphaned: capture its workspace when
the temporary directory still exists, record outcome `technically-incomplete` with reason
`orphaned`, append `finished`; it counts toward limits. Then continue the schedule per REQ-27.

### Recorded imports

`plan.json` lists units of `recorded` variants with `source: recorded`; `run` never launches
them and skips them silently. `import-recorded` performs `run` step 1 and `Opening an experiment
directory` except that `execution_enabled` may be false and
the cost limits may be null when no variant is `executable`; the unit must belong to a
`recorded` variant (else exit 2). Every `models_by_role` value must be non-empty, not an adapter
alias and equal to the variant's role model (else exit 2 `model-mismatch`). The import appends
`reserved` (details `{source: "recorded"}`) and `finished`, counts toward `max_attempts` and
`max_attempts_per_unit` (exit 6 when exceeded), applies no spend limit, copies the workspace and
run log into the capture, and runs extract through compare as for a live attempt.

### Workspace and child environment

Workspace: `tempfile.mkdtemp(prefix="orchestrail-golden-")` under the system temporary
directory; seed project copied without `.git/` and `__pycache__/` directories; `git init -b main`; `git add -A` and one commit `seed: initial
project` with author and committer `Golden Seed <seed@example.invalid>` and date
`2000-01-01T00:00:00Z`; no remote. The attempt log root and the helper home are sibling temporary
directories. After capture the three temporary directories are removed. The registry read for
REQ-47 is `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects` (one path per line), read only.

Child environment, built from an allowlist: `PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `LANG`,
`LC_*`, `TERM`, `TMPDIR`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`,
the adapter's `env_passthrough` names, the variant's `switches.env` entries, `ORCHESTRAIL_HOME` =
helper home and `ORCHESTRAIL_LOG_ROOT` = attempt log root. Every other variable is dropped. Only
variable names are recorded, except that `switches.env` values are part of the manifest.

### Variant switches

`switches` = `{prompt_args: [string], env: {NAME: string}, overlay: path|null, overlay_digest:
64-hex|null}` (empty list, empty object and nulls when unused). A variant that differs from the
baseline only by a spec's opt-in setting is declared with the same roles and the switch here,
for example `prompt_args: ["--repair-policy", "bounded-local"]` on the candidate for spec 17
(the flag's absence is the no-repair arm, spec 17's row for 10 in its C-10), or
`env: {"ORCHESTRAIL_SCOPED_VERIFICATION": "off"}` on the full-review arm for spec 15 (spec 15
REQ-34 and its row for 10). Spec 18 defines no switch (spec 18 A-14); its decomposition-policy
variants differ only in `strategy_details` (spec 18's row for 10). `prompt_args` are appended,
space-separated, to the case workflow's prompt; `--allow-pr` and `--parallel` are rejected
(exit 2), because REQ-36 forbids the first and N comes from the case workflow entry. `env` names
must match `^ORCHESTRAIL_[A-Z0-9_]{1,56}$` and must not be `ORCHESTRAIL_HOME` or
`ORCHESTRAIL_LOG_ROOT` (exit 2), so a switch cannot change the model, the harness configuration
or an allowlisted variable. `overlay` and `overlay_digest` may be `null` in every variant. `overlay` is a directory relative to the manifest whose files are copied into
the workspace after the seed commit and before launch; `overlay_digest` is its tree digest and is
checked in preflight (exit 5 on mismatch); an overlay file that exists in the seed project is
rejected with exit 2 `overlay-conflict`. The seed digest is taken before the overlay; the overlay
files are part of the changed-paths baseline. Switches are part of the configuration hash.

### Reference build determinism

`build-reference` and the seed commit of every workspace run git with every inherited `GIT_*`
variable removed, then `GIT_CONFIG_NOSYSTEM=1`,
`GIT_CONFIG_GLOBAL=/dev/null`, `-c commit.gpgsign=false -c core.hooksPath=/dev/null -c
core.autocrlf=false`, `git init --object-format=sha1`, fixed author and committer identities
and dates, and file modes 100644 or, for files executable in the source, 100755. For the same
case files, workflow and `--date-base` (default: the history's `date_base`), the built workspace
files are byte-identical and every commit and tree id is identical on every run. The run-log
store is not byte-identical, because `scripts/log-step.sh` stamps its own times and run ids
(`rules/run-log.md → ## How a pipeline logs`); its events' `step`, `subtask`, `outcome`, `tests`
and `gate` values and their order are identical. The executor's own git commands use the
user's configuration and are not covered.

### Isolation

Hidden-material probe targets: the case's `hidden/` and `reference/` directories, every
`cases_root`, the artifact root and `blinding.json`. Network probe targets: a loopback listener
opened by the runner, and `network_probe_target` when set. With `mechanism: "command-prefix"`
the runner first connects to each network target itself (control), then runs `prefix +
[python3, -I, <helper home>/scripts/golden_probe.py, --read, <file>…, --connect,
<host:port>…]` in the workspace. The hidden-material probe passes when every read fails; the
network probe passes when every connection the control completed fails inside the prefix and
`network_probe_target` is set; a target the control cannot reach makes the network probe fail.
With `mechanism: "none"` both probes fail. A failed probe is accepted only when
`accepted_weaker_isolation` sets the matching flag; the attempt record and report then state
`weakened` with the reason. Probe results are stored in `experiment.json`.

### Limits

Before each launch: refuse with `attempt-limit` when reserved attempts equal `max_attempts`;
`unit-attempt-limit` when the unit's attempts equal `max_attempts_per_unit`; `total-wall-limit`
when elapsed run time since `started_at` (summed over resumed runs from ledger timestamps)
plus `max_wall_seconds_per_attempt` exceeds `max_total_wall_seconds`. Spend bound = sum of
known `cost_usd` + (number of attempts with unknown cost × `max_cost_usd_per_attempt` when
`unknown_cost_policy` is `count-at-cap`) + `max_cost_usd_per_attempt` for the next attempt;
refusal reasons, checked in this order: `cap-unenforceable` when the declaration says `absent`,
or `unverified` without `accept_unverified_cost_cap: true`; `spend-unknown` when an attempt has
unknown cost and the policy is `refuse`; `spend-limit` when the bound exceeds `max_cost_usd`.
A cost is known when `cost_usd` is not null, whatever its coverage.

### Promotion rule (REQ-12)

Decision tasks: tasks of `analysis.decision_split` not listed under `contamination`; under
`holdout` multiplicity only `selected_candidate` is compared. Per decision task t and variant v,
`a(t,v)` = accepted units / denominator units (all planned units for `planned`; units whose
outcome is not `cancelled`, `technically-incomplete` or `excluded` for
`completed-with-censoring`). `D` = mean over tasks of `a(t,cand) − a(t,base)`. `R` =
(`C_cand`/`N_cand`) / (`C_base`/`N_base`), with `C` the summed known cost of all started units
of the variant on the decision tasks and `N` its accepted units. Bootstrap: for b = 1…`resamples`,
draw `n` decision tasks with replacement, the i-th index being
`int.from_bytes(sha256(f"{seed}:{b}:{i}".encode()).digest()[:8], "big") % n`, and compute `D_b`
and `R_b`. `α` = 1 − `confidence`, divided under `bonferroni` by the number of non-baseline
variants with availability `executable` or `recorded`. Interval bounds: sorted values at 0-based
indices `floor(α/2 · B)` and `ceil((1 − α/2) · B) − 1`. Verdict, first matching rule:

1. `do-not-promote` — the candidate has a critical missed defect on any task of the experiment,
   or a hard constraint fails (an SA-05 failure in any candidate attempt).
2. `insufficient-data` — the decision split is `holdout` and holdout is sealed; fewer than two
   decision tasks have units of both variants; any `R_b` is undefined (zero accepted); a
   decision-split attempt of either variant has cost coverage other than `complete`, an unknown
   actual model, or an open dispute; or `analysis` is null.
3. `promote` — `lower(D) > −delta` and `upper(R) < r_max`.
4. `do-not-promote` — otherwise.

The verdict is advisory; the tool changes no default.

### Calculator

For each strategy and each assignment of fixed parameters: expected cost `E` = Σ probability ×
(sum of branch costs); expected acceptance `A` = Σ probability × acceptance; cost per accepted =
`E/A`, `null` when `A = 0`. Probabilities must lie in [0,1] and sum to exactly 1 per strategy in
`Fraction` arithmetic, else exit 2 naming the strategy. Range parameters: evaluate every corner of
the range box and report min and max (each quantity is affine or linear-fractional in each
parameter, so extremes lie at corners); fixed values are reported at their given value. Break-
even: domain = the parameter's range when it is a range, else [0,1]; when `A_left ≠ A_right` at
any domain end → `not-applicable`; otherwise `E_left − E_right = a + b·x` is affine in x; `b = 0`
→ `identical` when `a = 0`, else `none`; x* = −a/b → `found` inside the domain, else
`outside-domain` with the value.

### Documentation

`docs/GOLDEN-RUNS.md` sections: purpose and the three outcome kinds; running the offline suite
and provisioning `pytest`; case catalog; writing and validating a manifest; approval; release
regression runs; comparison experiments and the promotion rule; isolation limits and weaker
designs; cancellation and resume; human evaluation and disputes; reviewing candidates and
accepting expectations; reports and their limits; calculator; data retention and export;
rollback (stop approving manifests; the tool never changes defaults). `docs/README.md` gets one
index row; `scripts/README.md` one inventory row for `golden-eval.py`.

## Non-Functional Requirements

| Attribute | Target | Verification |
|---|---|---|
| Determinism | Identical inputs produce byte-identical `facts.json`, `projection.json`, reports (apart from `generated_at`) and calculator output | AC-03, AC-06, AC-32 run each twice and compare bytes |
| Offline operation | The offline suite opens no network connection | AC-02; when `unshare --user --net true` succeeds on the host, one suite test re-runs AC-01's `check` calls inside that namespace and passes; otherwise that test is reported skipped |
| Dependencies | Python 3.11+ standard library, `git`, an already installed `pytest`; nothing installed at run time | AC-25 |
| Durability | Ledger events are fsynced before the next action; an interrupted run leaves a ledger whose last line is complete JSON or is ignored when incomplete | AC-16, AC-17, AC-18 |
| Privacy | Reports contain no prompt, model output, transcript or environment value | AC-31 |
| File permissions | Experiment directories 0700, `blinding.json` 0600 | AC-21 |
| Runtime | N/A — no runtime target is set; ADR-0020 places timing outside suite assertions, and the owner set none | — |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| N-01 `flat`/`spec-run`: the leaf's `feat` commit is not preceded by its `test` commit | SA-05 `implementation-before-test` | REQ-18, REQ-19 |
| N-02 `flat`/`spec-run`: a leaf test function changed after its `test` commit without `tdd: test amended` | SA-06 failed | REQ-19 |
| N-03 All phases complete but a hidden test fails | HC-1 failed, missed defect recorded; `rejected-by-criteria` while compare is `passed` | REQ-08, REQ-19 |
| N-04 Issue List entry removed while its Contract Check `FAIL` row remains | SA-08 failed | REQ-19 |
| N-05 Edit of a `forbidden_paths` file or a path outside `allowed_paths` | SA-09 failed | REQ-19 |
| N-06 `composite` children pass their tests but `parse_amount` returns `Decimal` | HC-1 D-1 failed; with claimed success a critical missed defect | REQ-19, REQ-28 |
| N-07 Attempt record with `cost_usd: "0"` and `cost_source: absent` | Record validation fails (exit 8 for the writer, exit 2 for `report` reading it) | REQ-19, REQ-34 |
| N-08 Capture cannot copy the workspace, normalization raises, or a ledger write fails | Step `error`; `technically-incomplete`; exit 8 | REQ-15, REQ-19 |
| N-09 Corrupted projection offered through `--update` and `accept-expected` | `--update` writes only a candidate; `accept-expected` refuses a candidate with a non-`passed` step | REQ-16, REQ-17, REQ-19 |
| N-10 New-feature leaf claims pinned mode | HC-2 shows its tests fail on the seed; SA-05 `pinned-on-new-behaviour` | REQ-18, REQ-19 |
| N-11 Leaf carries the pre-TDD note but was not in flight in the seed | SA-14 failed | REQ-18, REQ-19 |
| N-12 `atomic-tests:` removed from a started leaf | SA-04 failed | REQ-18, REQ-19 |
| `flat` run decides `flow: quick` | SA-03 failed (expected `full`) | REQ-48 |
| `bugfix` run stops at the quick gate | SA-02 and SA-03 failed; `rejected-by-criteria` | REQ-48 |
| Two task directories, or none | SA-01 `error`; `technically-incomplete` | REQ-15 |
| Issue subsection with unrecognized text | Extract `error` | REQ-15 |
| Contract Check criteria without `AC-` ids | SA-07 uses row counts and `FAIL` absence; ids unmatched are reported | REQ-18 |
| Manifest invalid JSON, duplicate key, unknown field, float number, `holdout` without `selected_candidate` | `validate-manifest`/`run` exit 2 | REQ-10 |
| Manifest edited after approval | Exit 4 `approval-mismatch` | REQ-22 |
| `approve` from a pipe or with a wrong confirmation | Exit 4, no file | REQ-23 |
| Model alias `sonnet` or empty model | Exit 5 before launch | REQ-13 |
| Result reports another model | `stopped-by-policy` `model-mismatch`; variant stops | REQ-13 |
| Isolation probe fails, no weaker design accepted | Exit 5, zero launches | REQ-21 |
| Adapter exits after a request may have been sent, printing nothing | Attempt counted; `technically-incomplete`; no automatic relaunch | REQ-24, REQ-27 |
| Runner killed between `reserved` and `finished` | On resume: `technically-incomplete` `orphaned` | REQ-27 |
| Unknown earlier cost with policy `refuse` | Next launch refused, `spend-unknown`, exit 6 | REQ-25 |
| Attempt or total limits reached | Unit `stopped-by-policy` with the limit reason, exit 6 | REQ-44 |
| SIGTERM while the adapter runs | Process group terminated, `cancelled`, exit 7 | REQ-26 |
| Attempt exceeds wall limit | `stopped-by-policy` `timeout`; next unit continues | REQ-45 |
| Second runner on the same experiment | Exit 9, files unchanged | REQ-41 |
| `run` without `--resume` on an experiment directory with a `launched` event | Exit 2 `experiment-exists`; directories with imports only are opened normally | REQ-27 |
| Resume with changed manifest bytes | Exit 4 | REQ-27 |
| Zero accepted units for a variant | `cost_per_accepted: null`, `accepted_denominator_zero`; verdict `insufficient-data` | REQ-33, REQ-12 |
| One decision task only | `insufficient-data` | REQ-12 |
| Critical missed defect and incomplete cost together | `do-not-promote` (hard constraint first) | REQ-12 |
| Human verdict contradicts the automated outcome | Dispute open; outcome `rejected-by-criteria` until resolved | REQ-31 |
| Late defect inside / outside the follow-up window | `rejected-by-criteria` / recorded only | REQ-29 |
| Holdout revealed, then the manifest changed in the same family | Tasks `contaminated`, excluded | REQ-46 |
| `pytest` not importable | Exit 3 after the remaining checks, one diagnostic | REQ-35 |
| Workspace path inside a registered project or the checkout | Exit 5 `workspace-location` | REQ-47 |
| Recorded workspace from another seed | Exit 2 `incomparable` | REQ-07 |
| `per-composite` task whose accepted child branches were deleted | SA-10 passes when the merge commits keep every listed commit reachable | REQ-51 |
| `per-composite` child whose `base_branch` is not its composite's branch, or a merge whose second parent is not the child's last commit | SA-10 failed | REQ-51 |
| Runner's user git configuration signs commits or sets hooks | Ignored by `build-reference` and the seed commit; ids unchanged | REQ-49 |
| `flat` task declared `holdout` | Exit 2 `published-case-holdout` | REQ-50 |
| Switch overlay file already in the seed, `--allow-pr` or `--parallel` in `prompt_args`, or an `env` name outside `ORCHESTRAIL_*` or reserved | Exit 2 | REQ-52 |
| Variant without the `validator` role key or with an extra key | Exit 2 | REQ-53 |
| Calculator probabilities outside [0,1] or not summing to 1 | Exit 2 naming the strategy | REQ-11 |
| Calculator break-even with differing acceptance | `not-applicable` | REQ-11 |
| Concurrency inside one run | Not applicable: attempts run sequentially; the lock prevents a second runner | REQ-41 |

## Acceptance Criteria

Original AC-01–AC-07 keep their subject and are rewritten as binary criteria (2026-11-13); the
mandatory cases of the original §14 are covered from AC-08 onward. All criteria are checked by
`python3 -I tests/golden-runs.py` with a test-double `claude` executable placed first on `PATH`
that appends `{argv, cwd, env_names, ORCHESTRAIL_HOME, ORCHESTRAIL_LOG_ROOT}` to a ledger file
and applies a scripted result (files, commits, log events, JSON output, exit code, sleep).
Reference workspaces come from `build-reference`.

- **AC-01** (REQ-01, REQ-04, REQ-08): Given `pytest` importable, when the suite runs `check`
  on the reference workspace and run-log store of each of the five catalog pairs, then each
  exits 0 with outcome `independently-accepted` and compare `passed`, and the double's ledger is
  empty.
- **AC-02** (REQ-05, REQ-10): Given the double on `PATH`, when the suite runs `run` without
  `--manifest`, with the template, with `execution_enabled: false` and with a missing approval
  file, and runs `check`, `validate-manifest`, `report` and `calculate`, then the double's
  ledger is empty, each `run` call exits 4, and neither `scripts/validate-contracts.sh` nor
  `scripts/sync.sh` contains `golden-eval.py` or `run-golden.sh`.
- **AC-03** (REQ-03, REQ-04, REQ-14, REQ-16): Given the `flat`/`spec-run` reference, when it is
  checked as built, rebuilt with another `--date-base`, with every date in `state.md` replaced,
  and from another absolute path, then the four projections are byte-identical; when one open
  test is made to fail, then SA-12 is `failed`, compare is `failed`, `compare/diff.txt` is
  non-empty and the outcome is `rejected-by-criteria`; when `tests/expected/flat/spec-run/` is
  absent, compare is `failed` with `missing-expected` and exit 1; a projection never gives two
  commits or two branches the same alias, and an absolute path outside the workspace in
  `target_files:` appears as `<EXTERNAL>/<basename>`; and with `--update` the SHA-256 of every
  file under `tests/expected/` is unchanged while the candidate directory holds
  `projection.json`, `diff.txt`, `changed-facts.json` and `candidate.json`.
- **AC-04** (REQ-06, REQ-07): Given an approved comparison manifest with variants A–F where D is
  `unavailable` and C is `recorded`, when `run --dry-run` runs, then the printed plan lists the
  same task ids, case digests and source revision for every variant, C's units with `source:
  recorded`, no unit for D, and no experiment directory is created; after `import-recorded` of
  the `flat`/`spec-run` reference for one C unit and `report`, C has `measured: true` and D
  `measured: false`, and the ledger holds `reserved` and `finished` for that import; an import
  whose seed commit files differ from the case seed exits 2 with `incomparable`; an import whose
  `models_by_role` differ from C's role models exits 2 with `model-mismatch`.
- **AC-05** (REQ-08, REQ-09): Given an experiment with one unit each whose attempt has
  workflow-claimed success and a failed hidden test, is cancelled, is technically incomplete,
  and is accepted with unknown cost, when `report` runs, then the first unit is
  `rejected-by-criteria`, all four outcomes appear in `unit_outcomes`, `accepted` is
  `{count: 1, denominator: 4}` under `planned`, and `cost.coverage` is `incomplete`.
- **AC-06** (REQ-11): Given `tests/golden/calculator-example.json` (strong path cost 7; cheap
  path 4 plus repair 5 with probability `p`), when `calculate` runs with `p` = `0.2`, `0.6` and
  `0.8`, then the cheap expected costs are `5`, `7` and `8`, the strong cost is `7`, break-even
  is `{parameter: "p", value: "0.6", status: "found"}`, every output has `kind: hypothetical`;
  with `p` as range `{low: 0.2, high: 0.8}` the cheap range is `["5", "8"]`; and an input whose
  branch probabilities sum to `0.9` exits 2.
- **AC-07** (REQ-12, REQ-40): Given synthetic attempt sets, when `report` runs, then a set
  meeting every promotion condition yields `promote`; the same set with `lower(D)` equal to
  `−delta`, or with `upper(R)` equal to `r_max`, yields `do-not-promote`; with one critical
  missed defect and an incomplete cost it yields `do-not-promote`; with one decision task, with
  an incomplete cost alone, or with a sealed holdout decision split it yields
  `insufficient-data`; and `docs/GOLDEN-RUNS.md` contains every listed section heading while
  `docs/README.md` and `scripts/README.md` each contain one line naming it.
- **AC-08** (REQ-02): Given an approved regression manifest for `flat`/`spec-run` with model
  `test-model-1`, effort `high`, permission mode `dontAsk`, allowed tools `["Read","Edit"]`, no
  disallowed tools and per-attempt cap `0.5`, when `run` runs, then the double's ledger has
  exactly one entry whose argv equals the DM-8 template expansion with those values and without
  the `--disallowedTools` pair, whose cwd is the workspace, whose `ORCHESTRAIL_HOME` and
  `ORCHESTRAIL_LOG_ROOT` are the attempt's helper home and log root, and whose env names are a
  subset of the allowlist.
- **AC-09** (REQ-13): Given model `sonnet`, when `run` runs, then it exits 5 and the ledger is
  empty; given the double reporting model `other-model` with the declaration's `model` field
  mapped, then the attempt is `stopped-by-policy` with `model-mismatch`, no later unit of that
  variant launches, and `run` exits 6.
- **AC-10** (REQ-15): Given reference workspaces mutated to have two task directories, an
  unparsable leaf header, or unrecognized text under `### Approved`, when `check` runs, then the
  extract step is `error`, the dependent assertions are `error`, the outcome is
  `technically-incomplete` and the exit code is 8.
- **AC-11** (REQ-17): Given a candidate whose `candidate.json` records assert `failed`, when
  `accept-expected` runs, then it exits 1 and `tests/expected/` is unchanged; given a passing
  candidate, then `projection.json` and `review.json` are written with matching
  `projection_sha256` and the candidate's `origin`.
- **AC-12** (REQ-18): Given `flat`/`phase-pipeline` references with (a) a leaf in pinned mode
  whose digest tests pass on the seed, (b) a leaf `n-a` with a non-empty `tdd: none —`
  justification, (c) a seed containing an in-flight leaf without `atomic-tests:` that ends with
  the pre-TDD note, then SA-05, SA-04 and SA-14 pass and the leaf `tdd_order` is `not-observed`;
  given (d) `tdd: none —` with no text, then SA-05 fails with `unjustified-n-a`; given (e) a leaf
  in red mode whose digest tests all pass on the seed, then SA-05 fails with
  `red-not-reproducible`; given (f) a final `atomic-tests: pinned`, then SA-05 fails with
  `tdd-incomplete`; given (g) a red-mode digest line `tdd: red digest — AC-1 → test_a; AC-2 → test_b;
  context-receipt: implementer bootstrap — no-packet epoch 1`, then the leaf tests are `test_a` and
  `test_b` and the `context-receipt:` entry is not part of the digest.
- **AC-13** (REQ-19): Given the references mutated as N-01–N-12, when `check` runs (record
  validation for N-07, the update and accept path for N-09), then each yields exactly the check
  and reason named in `## Edge Cases & Failure Modes` and no outcome `independently-accepted`.
- **AC-14** (REQ-20, REQ-21): Given an approved regression `run` of each catalog pair with a
  double that records the SHA-256 of every file under its cwd and under `ORCHESTRAIL_HOME`,
  then no recorded hash equals a non-empty file of the case's `hidden/` or `reference/` whose
  content does not also occur in the case's `project/`, and the helper
  home has no `tests/`, `.ai/` or `docs/` entry while it holds `scripts/log-step.sh`; given isolation `none` without a weaker design, then `run` exits 5 with
  `isolation-unverified` and the ledger is empty; given a `command-prefix` test prefix that
  denies the probe's reads and connections with a reachable `network_probe_target`, or `none`
  with both weaker-design flags, then the attempt launches and its record states `enforced` or
  `weakened` accordingly.
- **AC-15** (REQ-22, REQ-23): Given an approved manifest, when one limit value is changed after
  approval, then `run` exits 4 with `approval-mismatch` and the ledger is empty; when `approve`
  runs with standard input from a pipe, or through a pseudo-terminal with a wrong 12-character
  confirmation, then it exits 4 and writes no file; with the correct confirmation it writes DM-7
  with the current configuration hash.
- **AC-16** (REQ-24, REQ-25): Given a double that exits 1 with no output, when `run` runs, then
  the ledger shows `reserved` before `launched`, the attempt is `technically-incomplete` and
  counts toward `max_attempts`; separately, given attempts with known costs `0.2` and `0.2`, cap
  `0.5` and `max_cost_usd` `0.8`, the third launch is refused with `spend-limit`; given an
  earlier unknown cost and policy `refuse`, the next launch is refused with `spend-unknown`;
  with policy `count-at-cap` and the same costs it launches when the bound is within
  `max_cost_usd`; given a declaration with `per_attempt_cost_cap: "unverified"` and no
  acceptance, the first launch is refused with `cap-unenforceable`; each refusal exits 6.
- **AC-17** (REQ-26, REQ-45): Given a double that sleeps and ignores SIGTERM, when the runner
  receives SIGTERM, then the double's process group receives SIGTERM and, after the grace
  period, SIGKILL; the attempt is `cancelled`; no further unit launches; `run` exits 7; given a
  wall limit shorter than the double's sleep, the attempt is `stopped-by-policy` `timeout`, the
  next unit launches, and `run` exits 6.
- **AC-18** (REQ-27): Given an experiment with one accepted unit, one `technically-incomplete`
  unit and one orphaned reservation, when `run --resume` runs without `--retry-incomplete`, then
  the orphan is recorded `technically-incomplete` `orphaned` and no adapter call occurs; with
  `--retry-incomplete` exactly two calls occur, each with `attempt_no` 2; with changed manifest
  bytes `--resume` exits 4; and `run` without `--resume` on that directory (which holds a `launched` event) exits 2, while `run` after only an `import-recorded` into a fresh directory proceeds without `--resume`.
- **AC-19** (REQ-28): Given variant B whose first attempt has workflow-claimed success and fails
  a `critical` hidden test, when `run` continues, then B's remaining units are
  `stopped-by-policy` with `critical-missed-defect`, no further B launch occurs, and other
  variants continue.
- **AC-20** (REQ-03, REQ-29): Given attempts matching each row of the DM-10 outcome table,
  including one with both a capture error and a failed assertion and one with an SA `error`,
  then each receives the outcome of its first matching row, and an attempt with compare
  `failed` and everything else `passed` is `independently-accepted`.
- **AC-21** (REQ-30): Given a comparison experiment whose double writes the requested model id
  into a `plan.md` `Model (Claude)` column, a `## Model Selection` line of the task `state.md` and
  a commit trailer, then no file under
  `evaluation-queue/` contains a variant id, that model id or a `unit_id`, `blinding.json` has mode 0600, experiment
  directories have mode 0700, and the report maps every blinded label to its variant.
- **AC-22** (REQ-31): Given an automatically accepted attempt, when `evaluate --verdict
  rejected` is recorded, then a dispute opens and the unit is `rejected-by-criteria`; when a
  person other than the resolver records `--resolve-dispute`, it exits 2; when the resolver
  records `--resolve-dispute accepted`, then the unit is `independently-accepted` and all
  records remain.
- **AC-23** (REQ-32, REQ-46): Given experiment E1 with a holdout task, when `report` runs
  without `--reveal-holdout`, then its holdout metrics are `sealed`; after `--reveal-holdout`,
  the family journal holds the event; and E2 in the same family with a different configuration
  hash lists that task under `contamination` and excludes it from holdout metrics.
- **AC-24** (REQ-33, REQ-34): Given one unit with attempts costing `0.4` and `0.6` whose last
  attempt is accepted, then `cost_per_accepted` is `1` with coverage `complete` when both costs
  are complete; given no accepted unit, it is `null` with `accepted_denominator_zero`; given a
  missing cost, the record stores `null` with `cost_source: absent` and coverage is
  `incomplete`; given usage attached with category `experimental_evaluation`, it appears in
  `experimental_evaluation_cost` and not in `observed_workload_cost`.
- **AC-25** (REQ-01, REQ-35): Given an interpreter where `import pytest` fails, when the suite
  runs, then every non-`pytest` test runs, one diagnostic naming `pytest` is printed, no package
  installer is invoked, and the exit code is 3.
- **AC-26** (REQ-36): Given each catalog pair's reference build and a `run` attempt, then `git
  remote` in the captured workspace prints nothing and no case prompt contains `--allow-pr`.
- **AC-27** (REQ-37): Given `tests/golden/manifest-template.json`, when `validate-manifest`
  runs, then it reports `valid: true, runnable: false`, and `run` with it exits 4.
- **AC-28** (REQ-38): Given the `flat`/`spec-run` reference imported for a `recorded` variant,
  then its attempt record has `execution_source: recorded`, its outcome equals the `check`
  outcome, and the double's ledger is empty.
- **AC-29** (REQ-39): Given a manifest whose `source_revision`, a case digest or the
  instructions digest differs from the values printed by `validate-manifest --print-current`, a
  dirty tracked tree, or a double reporting another version, then `run` exits 5 naming the
  mismatch and the ledger is empty.
- **AC-30** (REQ-41): Given a process holding the experiment lock, when a second `run` on that
  directory starts, then it exits 9 and the directory's file hashes are unchanged.
- **AC-31** (REQ-42, REQ-43): Given a double whose result text and environment contain the
  marker `SECRET-MARKER-7`, then neither `report.json` nor `report.md` contains the marker, both
  contain `retain_until` equal to the start date plus `retention_days`, and every attempt
  directory still exists after `report`.
- **AC-32** (REQ-09): Given a fixed synthetic attempt set and seed, when `report` runs twice,
  then the two `report.json` files are byte-identical apart from `generated_at`, every rate has
  a numerator and denominator, and `acceptance_interval` is non-null for comparison manifests
  and `null` with `no-analysis` for regression manifests.
- **AC-33** (REQ-10): Given manifests with invalid JSON, a duplicate key, an unknown field, a
  float number and a `holdout` multiplicity without `selected_candidate`, when
  `validate-manifest` runs, then each exits 2 naming the offending path.
- **AC-34** (REQ-44): Given `max_attempts` 1 and two planned units, then the second unit is
  `stopped-by-policy` `attempt-limit` and `run` exits 6; given `max_attempts_per_unit` 1 and
  `--retry-incomplete` on an incomplete unit, then it is refused with `unit-attempt-limit`;
  given `max_total_wall_seconds` smaller than `max_wall_seconds_per_attempt`, then the first unit
  is refused with `total-wall-limit`.
- **AC-35** (REQ-47): Given a registry file listing the system temporary directory, or an
  artifact root that contains the system temporary directory, when `run` runs, then it exits 5
  with `workspace-location` and the ledger is empty.
- **AC-36** (REQ-48): Given the `flat`/`phase-pipeline` reference with `flow: quick`, or the
  `bugfix` reference stopped at the gate with `flow: full`, when `check` runs, then SA-03 fails
  and the outcome is `rejected-by-criteria`; and each case's `case.json` declares the expected
  flow listed in the DM-1 catalog.

- **AC-37** (REQ-49): Given a `HOME` whose `.gitconfig` sets `commit.gpgsign=true` with a failing
  signing program and a `core.hooksPath` holding a failing `pre-commit` hook, when
  `build-reference --case flat --workflow spec-run` runs twice with the same `--date-base` into
  two directories, then both succeed, the tree digests of the two workspaces (excluding `.git/`)
  are equal and every ref resolves to the same commit id in both; with another `--date-base` every
  non-seed commit id differs while every commit's tree id is unchanged.
- **AC-38** (REQ-50): Given a comparison manifest with a `flat` task declared `holdout`, when
  `validate-manifest` runs, then it exits 2 with `published-case-holdout`; the same task declared
  `tuning` validates.
- **AC-39** (REQ-51): Given the `composite`/`spec-run` reference (no `branch_model:`) and a
  `per-composite` variant of it built by the suite with `branch`, `merge` and `commit` steps at
  N = 1, when `check` runs, then SA-10 passes for both; after deleting the child branches of the
  `per-composite` variant SA-10 still passes; after changing one child's `base_branch` to the seed
  branch, or rebuilding one merge with another second parent, SA-10 fails; and the projection's
  `branch_model` is `per-leaf` and `per-composite` respectively.
- **AC-40** (REQ-52): Given an approved comparison manifest whose variants A1 and A2 differ only
  in A2's `switches` (`prompt_args` `["--example-switch","on"]`, `env`
  `{"ORCHESTRAIL_EXAMPLE_SWITCH":"on"}`, an overlay holding `.ai/example-policy.json`), when
  `run` runs, then the double's ledger shows the A2 prompt ending with ` --example-switch on`,
  `ORCHESTRAIL_EXAMPLE_SWITCH` among its env names, the
  overlay file present in its cwd, and `.ai/example-policy.json` absent from A2's
  `changed_paths`; A1's entries show none of these; and manifests with `--allow-pr` or
  `--parallel` in `prompt_args`, an `env` name `ANTHROPIC_MODEL` or `ORCHESTRAIL_HOME`, or an
  overlay file that exists in the seed each exit 2.
- **AC-41** (REQ-53): Given comparison manifests whose variant lacks the `validator` role key or
  adds a `planner` key, when `validate-manifest` runs, then each exits 2 naming the variant; and
  given a valid comparison yielding `promote`, `report.json` has `kind: "observed"`, the
  manifest's `experiment_id`, and a `comparisons` element with `candidate`, `baseline` and
  `verdict`, while the manifest's variants carry `adapter` and `roles.<key>.model`/`effort` for
  `arbiter`, `implementer` and `validator`.
- **AC-42** (REQ-54): Given a shipped `claude` declaration, a runner `HOME` with no owner policy
  file and `XDG_CONFIG_HOME` unset, then the instructions digest contains the lines
  `absent  $XDG_CONFIG_HOME/orchestrail/effort-policy.json` and
  `absent  $XDG_CONFIG_HOME/orchestrail/repair-policy.json`, two computations give the same
  digest, and creating `effort-policy.json` under `$HOME/.config/orchestrail/` changes it; given
  `XDG_CONFIG_HOME` set to another directory holding the file, then the file there is read and
  the one under `$HOME/.config` is not.
- **AC-43** (REQ-54, REQ-22): Given an approved manifest and a present `repair-policy.json`,
  when one byte of that file changes, then `validate-manifest --print-current` prints another
  instructions digest and a manifest pinned to the old digest makes `run` exit 5 (REQ-39) with
  the ledger empty; the manifest rewritten with the new digest has another `config_sha256`, so
  its old approval record exits 4 `approval-mismatch`; given two policy files of identical
  content at different absolute paths, then the instructions digests and configuration hashes
  are identical.
- **AC-44** (REQ-54): Given a policy entry that is a directory, an unreadable file, or a file whose
  content is not valid JSON (including one with a duplicate key), then `validate-manifest
  --print-current` and `run` each exit 2 with reason `policy-file-invalid` naming the entry, the
  double's ledger is empty, and the digest is not computed as `absent`.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-25 |
| REQ-02 | AC-08 |
| REQ-03 | AC-03, AC-20 |
| REQ-04 | AC-01, AC-03 |
| REQ-05 | AC-02 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04 |
| REQ-08 | AC-01, AC-05 |
| REQ-09 | AC-05, AC-32 |
| REQ-10 | AC-02, AC-33 |
| REQ-11 | AC-06 |
| REQ-12 | AC-07 |
| REQ-13 | AC-09 |
| REQ-14 | AC-03 |
| REQ-15 | AC-10 |
| REQ-16 | AC-03 |
| REQ-17 | AC-11 |
| REQ-18 | AC-12 |
| REQ-19 | AC-13 |
| REQ-20 | AC-14 |
| REQ-21 | AC-14 |
| REQ-22 | AC-15 |
| REQ-23 | AC-15 |
| REQ-24 | AC-16 |
| REQ-25 | AC-16 |
| REQ-26 | AC-17 |
| REQ-27 | AC-18 |
| REQ-28 | AC-19 |
| REQ-29 | AC-20 |
| REQ-30 | AC-21 |
| REQ-31 | AC-22 |
| REQ-32 | AC-23 |
| REQ-33 | AC-24 |
| REQ-34 | AC-24 |
| REQ-35 | AC-25 |
| REQ-36 | AC-26 |
| REQ-37 | AC-27 |
| REQ-38 | AC-28 |
| REQ-39 | AC-29 |
| REQ-40 | AC-07 |
| REQ-41 | AC-30 |
| REQ-42 | AC-31 |
| REQ-43 | AC-31 |
| REQ-44 | AC-34 |
| REQ-45 | AC-17 |
| REQ-46 | AC-23 |
| REQ-47 | AC-35 |
| REQ-48 | AC-36 |
| REQ-49 | AC-37 |
| REQ-50 | AC-38 |
| REQ-51 | AC-39 |
| REQ-52 | AC-40 |
| REQ-53 | AC-41 |
| REQ-54 | AC-42, AC-43, AC-44 |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Live projections vary between correct runs (leaf split, file names) | Frequent golden mismatches | High | Outcome ignores compare (REQ-03); mismatches become reviewed candidates (REQ-16, REQ-17) |
| A correct live run chooses another flow tier or no composite | Rejection or golden drift | Medium | Seeds fix the gate inputs (DM-1); composites are golden drift, not rejection |
| Hidden material reachable by the live executor | Evaluation not independent | High until an isolation mechanism exists | REQ-21 refuses or labels `weakened`; reports state it (Q-03) |
| Run's code executes on the runner host during open and hidden checks | Host files or artifacts altered | Medium | Throwaway copy, empty `HOME`, environment allowlist, isolation prefix when configured |
| Owner credentials under `HOME` usable by the executor | Remote effects despite no git remote | Medium | Environment allowlist; accepted only with the `network` weaker-design flag |
| Test-before-implementation order unobservable without commits | TDD-order violations under `/phase-pipeline` go undetected | High | Order recorded as `not-observed`; `spec-run` pairs check it; Q-05 |
| Adapter result fields and cost cap unverified | Live cost and model unknown; promotion impossible; launches refused without weaker-design acceptance | High | `null` fields stay unknown (REQ-34); Q-02, Q-06 |
| New files under `tests/` invalidate the source guard inventory | Validator red after the change | Certain | Re-pin per `tests/fixtures/validator-runtime/README.md:9-28` in the same change (Notes) |
| Offline suite not run by `validate-contracts.sh` | Regressions unnoticed between releases | Medium | Manual run before release and in the manual; Q-01 |
| Spec 09 renames workflows | Case prompts stale | Medium | Prompts are data in `case.json`; update with 09 |
| Small samples | Most comparisons `insufficient-data` | High | Valid result by design (REQ-12) |
| Scope size | Long implementation | Medium | Delivery order in eight parts; parts 1–3 are useful alone |

## Assumptions

- A-01 | Language of the spec | Resolved: rewrite in English with a condensed faithful translation under `## Source`, marked non-normative | Source: `rules/language.md`; `.ai/principles/coding.md → Language and tone` | Reversible: yes
- A-02 | Where the suite is registered | Resolved: standalone `python3 -I tests/golden-runs.py`; not added to `scripts/validate-contracts.sh` | Source: ADR-0019 Decision 3 (`.ai/adr/0019-…:68-80`); `tests/fixtures/validator-runtime/oracle.py:250` | Reversible: yes
- A-03 | File placement | Resolved: tooling in `scripts/golden-eval.py` and `scripts/golden_*.py`; owner-named `tests/run-golden.sh` and `tests/expected/`; fixtures under `tests/golden/`; suite `tests/golden-runs.py` | Source: original REQ-02/REQ-04 paths; `scripts/model_selection.py` + `tests/model-selection.py` pattern | Reversible: yes
- A-04 | Runtime | Resolved: Python 3.11+ standard library, run with `python3 -I` | Source: ADR-0009 Decision 6; `.ai/context/runbook.md:41` | Reversible: yes
- A-05 | Expected results per workflow | Resolved: `tests/expected/<case>/<workflow>/` | Source: best practice — one case runs under several workflows | Reversible: yes
- A-06 | Projection content | Resolved: semantic projection without free text (NR-4) | Source: original §10; best practice | Reversible: yes
- A-07 | Initial expected results | Resolved: from reference builds, `origin: synthetic-reference`, reviewed in the implementation change | Source: original §15 (no live run without approval) | Reversible: yes
- A-08 | Live adapter interface | Resolved: DM-8 template from `claude --help` of 2.1.323; strict version equality | Source: observed CLI; original REQ-02 | Reversible: yes
- A-09 | Variants with different models per role | Resolved: `manual` or `recorded`; only single-model variants are `executable` | Source: original REQ-06; the adapter launches one session model | Reversible: yes
- A-10 | Approval authenticity | Resolved: interactive terminal plus typed hash prefix; forging by a same-user process is outside the threat model | Source: git-rails residual risk X8 (`harness/claude/capabilities.md:78`) | Reversible: yes
- A-11 | Spend control | Resolved: per-attempt cap from the adapter plus cumulative known cost; unknown cost refused or counted at cap per manifest; an unverified cap needs owner acceptance | Source: original §9.1 item 7 and §8.1 "Limits … unknown data" | Reversible: yes
- A-12 | Statistical method | Resolved: paired task-cluster percentile bootstrap with a SHA-256 index generator; Bonferroni or holdout | Source: original §11.3; best practice | Reversible: yes
- A-13 | Primary quality metric | Resolved: independent acceptance rate only in version 1 | Source: original §11.3; smallest choice | Reversible: yes
- A-14 | Cost of live attempts | Resolved: adapter-reported cost has coverage `incomplete` unless `attach-usage` supplies spec 05 evidence | Source: G1/G8; spec 05 ownership | Reversible: yes
- A-15 | Isolation mechanisms | Resolved: `none` and `command-prefix` with control-checked probes; weaker design only by approved manifest flag | Source: original §9.1 item 5, §9.2 | Reversible: yes
- A-16 | Workspace location | Resolved: system temporary directory outside the checkout, artifact roots, case roots and registered roots; copied into the capture | Source: REQ-47; `.ai/memory/architecture.md:94`, `harness/claude/capabilities.md:77` | Reversible: yes
- A-17 | Helper home | Resolved: tracked files of the pinned revision without `tests/`, `.ai/`, `docs/` | Source: `scripts/log-step.sh:371-378`; `tests/log-step.sh:15-30` copy pattern | Reversible: yes
- A-18 | Release of a critical-defect halt | Resolved: the variant stays halted; continuing needs a new approved manifest | Source: original REQ-10 ("until owner decision") | Reversible: yes
- A-19 | TDD order evidence | Resolved: git ancestry for committing workflows; `not-observed` otherwise; red/pinned meaning from HC-2 seed replay of digest tests | Source: `rules/git-flow.md:7-9`; `workflows/phase-execution.md:36-40`; `workflows/pae-tests.md:205-225` | Reversible: yes
- A-20 | Case domains, behaviours and gate inputs | Resolved: catalog in DM-1, seeds declaring unreleased packages | Source: original §6.1 targets; `rules/quick-flow.md:28-50`; `workflows/bugfix.md:97-100` | Reversible: yes
- A-21 | Exit codes | Resolved: table under Contracts | Source: best practice; spec 07 style of distinct refusal codes | Reversible: yes
- A-22 | Retention | Resolved: recorded only, no automatic deletion | Source: original §8.1 "Data"; smallest choice | Reversible: yes
- A-23 | Sequential attempts | Resolved: one attempt at a time | Source: P4; ADR-0004 | Reversible: yes
- A-24 | CI | Resolved 2026-11-14 (supersedes "no CI file exists or is created"): this spec creates no CI file; spec 21 REQ-81 owns the one offline workflow, which runs this spec's command when present; paid runs never start in CI (G6) | Source: spec 21 REQ-81, D-03; gate G6; no `.github/` at `060ce6d` | Reversible: yes
- A-25 | Calculator range limit | Resolved: at most 16 range parameters | Source: best practice — bounded enumeration, not a quality target | Reversible: yes
- A-26 | Quick and bugfix test-first evidence | Resolved: `## TDD (quick)` record plus HC-2 seed replay | Source: `rules/quick-flow.md:90-97`; `workflows/bugfix.md:106-112` | Reversible: yes
- A-27 | `pytest` provisioning | Resolved: the owner installs `pytest` once, outside any check run, into the interpreter used for the suite and runs (for example a virtual environment outside the repository: `python3 -m venv <dir> && <dir>/bin/pip install pytest`); the diagnostic prints this command | Source: original §6.1 (install diagnostics outside the check run); ADR-0009 Decision 6 (pytest fixture) | Reversible: yes
- A-28 | Leaf-to-test mapping | Resolved: the `tdd: red digest` note | Source: `workflows/pae-tests.md:205-213`, `:219-225` | Reversible: yes
- A-29 | Composite expectation | Resolved: a missing composite is golden drift, not a rejection; existing composites must reach their final states | Source: classifier decides nesting autonomously (`rules/workflow-reference.md:483-516`) | Reversible: yes
- A-30 | Token and retry metrics | Resolved: tokens only from `attach-usage` or recorded metadata; retries reported as attempts per unit | Source: G2; spec 05 owns token accounting | Reversible: yes

## Decisions

- D-01 | Owner policy files enter the instructions digest through `$XDG_CONFIG_HOME/…` entries of `instruction_paths` (Q-07) | Overrides: none (accepts the Q-07 recommendation; no earlier text excluded these files) | Rationale: otherwise two runs with different effort or repair policy would receive the same configuration hash, which breaks attribution (G1) and comparability (G2) | Follow-up: REQ-54, the digest definition, DM-8, AC-42–AC-44 and Traceability added; spec 17 C-10 row 10 (no repair policy file assumed for a comparison run) becomes checkable through the digest

## Clarifications

N/A for the 2026-11-13 refinement — auto mode with no owner available; gaps were recorded as
A-01–A-30 and Q-01–Q-06.

### Session 2026-11-14

- Q: Do the owner policy files under `XDG_CONFIG_HOME` (`effort-policy.json`, `repair-policy.json`)
  enter the instructions digest? → A: Yes; they are listed as `$XDG_CONFIG_HOME/…` entries of the
  digest inputs (D-01, REQ-54). Rationale: attribution (G1) and comparability (G2).
- Q: Does this spec create a CI file now that spec 21 creates an offline workflow? → A: No; spec 21
  REQ-81 owns the one offline workflow, which runs `python3 -I tests/golden-runs.py` when the file
  exists; paid runs never start in CI (G6).

## Open Questions

- Q-01 | non-blocker | Should the offline suite become a `scripts/sync.sh` gate? (The validator
  inventory stays frozen, ADR-0019 Decision 3.) Impact: until then it runs only by hand.
  Recommended: keep it standalone; a sync gate would be a separate change.
- Q-02 | non-blocker | Which JSON result fields of `claude -p --output-format json` carry cost,
  model identity and call count? Impact: until verified, live cost and model are unknown, every
  live attempt has unknown cost (so the owner must choose `unknown_cost_policy: count-at-cap` or
  accept one attempt per approval), and promotion yields `insufficient-data`. Recommended:
  verify on the first owner-approved regression run and update DM-8 in a reviewed change.
- Q-03 | non-blocker | Which isolation mechanism confines the live executor's tool processes
  while permitting model transport? Impact: live runs are refused or `weakened`. Recommended:
  evaluate the harness's own sandbox settings or a namespace with a transport proxy in a
  separate spec.
- Q-04 | non-blocker | Owner experimental settings (tasks, repetitions, models, `delta`,
  `r_max`, limits, follow-up window, dispute resolver). Impact: no live run until chosen; offline
  implementation unaffected (original §15).
- Q-05 | non-blocker | Should `/phase-pipeline` emit per-leaf `pae-tests` and `pae-implement`
  run-log events so test-first order becomes observable without commits? Impact: order checks
  apply only to `spec-run` pairs. Recommended: a separate run-log change.
- Q-06 | non-blocker | Does `--max-budget-usd` stop an attempt at the cap under subscription and
  API billing? Impact: until verified the declaration says `unverified` and live runs need the
  owner's `accept_unverified_cost_cap`. Recommended: verify in the first approved run.
- Q-07 | non-blocker | Should owner policy files that the executor reads from the passed-through
  `XDG_CONFIG_HOME` — spec 16's `effort-policy.json` and spec 17's `repair-policy.json` under
  `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/` — enter the instructions digest? Today
  `instruction_paths` covers only the adapter's declared paths, so two arms can differ in those
  files unseen, and spec 17's C-10 row 10 assumes no repair policy file exists for a comparison
  run. Impact: comparability of live runs only (G2); offline implementation unaffected.
  Recommended: let DM-8 `instruction_paths` entries start with `$XDG_CONFIG_HOME/` (empty →
  `$HOME/.config`) and list both files in the shipped declaration; an absent file contributes
  `absent  <entry>`.
  Resolved 2026-11-14: yes, include both files (D-01, REQ-54, AC-42–AC-44); otherwise two runs
  with different effort or repair policy would share one configuration hash, breaking
  attribution (G1) and comparability (G2).

## Notes

- **CI consistency (2026-11-14):** REQ-35 (exit 3 without `pytest`) and the exclusion of CI
  configuration are consistent with spec 21 REQ-81, which installs `pytest` and guards the step
  that runs `python3 -I tests/golden-runs.py` with an existence check; this spec has no default
  CI job of its own.
- **Delivery order (eight parts):** (1) cases, seeds, hidden checks, references and
  `build-reference`; (2) capture, facts, assertions; (3) normalization, compare, update,
  accept-expected; (4) manifest, hashing, approval, preflight, dry-run; (5) runner, ledger,
  adapters, limits, cancellation, resume, import; (6) evaluation, queue, disputes, blinding,
  holdout; (7) reports, statistics, promotion; (8) calculator, template, documentation. Parts
  1–3 form a useful regression suite alone; a split into "golden regression" (1–3) and "strategy
  evaluation" (4–8) is the natural boundary if the task proves too large.
- **Test-first:** every part starts with failing cases in `tests/golden-runs.py` (levels `unit`
  and `integration`, offline), per the TDD rule.
- **Guard maintenance (required):** every new `.py`/`.sh` file under `tests/` changes the source
  guard inventory digest; finish all test sources, then follow
  `tests/fixtures/validator-runtime/README.md:9-28` to classify new call sites and re-pin
  `inventory_sha256`, then run the guard, regression and oracle suites.
- **Spec 09 coupling:** workflow and step names in this spec are today's. Spec 09 is a
  prerequisite (README → "Dependency order"), so the delivered values use its names (09 DM-11):
  the DM-1 `entry` value `phase-pipeline` is `pipeline`, SA-11's step `pe-execute` is
  `execution-execute`, and `case.json` prompts use the renamed commands; spec 09's reference
  scan includes `tests/golden/cases/*/case.json`.
- **Specs 22 and 23:** before spec 22 is delivered, `/spec-run` writes no `branch_model:`, so
  the `composite`/`spec-run` pair exercises the `per-leaf` rules of SA-10 and SA-11. After spec
  22's composite branch model is delivered, new `/spec-run` tasks record `per-composite` (spec
  22 REQ-16), so the same pair exercises the `per-composite` rules at N = 1; its reference and
  expected projection must be rebuilt in the change that delivers spec 22, and a `composite`
  workflow entry with `entry: "spec-run"` and `parallel: 2` must be added for spec 23 REQ-15 in
  the change that delivers spec 23's parallel children. Spec 22's C-5 row lists
  `tests/golden/cases/composite/reference/spec-run/` with
  `tests/expected/composite/spec-run/projection.json`, and spec 23's C-5 row lists
  `tests/golden/cases/composite/case.json` (entry `spec-run`, `parallel: 2`); the paths and the
  `entry` and `parallel` fields match DM-1 (the case-workflow key may differ from `entry`, as
  DM-1 allows). Spec 22's Notes also describe the first child's `base_commit` as the
  composite's start tip (the composite's own `base_commit`, or the promoted leaf's tip after a
  promotion, spec 22 REQ-37),
  which agrees with the start-tip rule of SA-10 and SA-11. Old tasks stay `per-leaf` and keep
  today's rules.
- **Spec 14:** its `tdd: red output` and `tdd: green output` notes lines do not affect results:
  the DM-3 fact "Leaf mode and leaf tests" reads only entries starting with `tdd: characterize —`,
  `tdd: none —` or `tdd: red digest —` and ignores every other `notes:` entry (REQ-18, A-28).
- **Specs 15, 16, 17, 18:** their qualification claims use comparison manifests whose candidate
  differs from the baseline by the spec's opt-in setting (`Variant switches`), by
  `strategy_details` (spec 18), or, for spec 16, by role effort; because an `executable` variant
  has one effort for every role, a spec 16 rule that matches only some roles is qualified with
  `recorded` variants (a `manual` variant has no finished attempt and is never measured, REQ-06),
  or with an executable candidate whose uniform effort also changes the other roles; spec 10 defines no experiment for them.
- **Spec 12:** its `context-receipt:` and `context-expansion:` notes entries are free text, which
  the projection excludes, so they do not change expected results.
- **Spec 13:** its checkpoint journal records order for `/spec-run` only and leaves
  `/phase-pipeline` emissions unchanged (spec 13 Out of Scope), so Q-05 stands.
- **Spec 21:** `docs/examples/flat-task/` is built from a `flat` run per spec 21 REQ-11.
- **Spec 17:** the calculator models finite branches only and does not change attempt limits.
- Hint: keep every process launch inside `scripts/golden_*.py` so the test file needs few guard
  classifications.
- Hint: modules `golden_cases`, `golden_capture`, `golden_semantics`, `golden_normalize`,
  `golden_manifest`, `golden_runner`, `golden_evaluation`, `golden_report`,
  `golden_calculator`, `golden_probe`.
- Rejected alternatives: byte-level comparison of normalized markdown (fails on every correct
  run's wording); a single cumulative spend counter without per-attempt cap (cannot stop an
  in-flight overrun); approval embedded in the manifest (circular hash); requiring a composite
  for acceptance (the classifier's nesting choice is legitimate either way).
- **Identity ledger (follow-up outside this spec):** the ledger row(s) at `.ai/tasks/completed/task-01-git-source-of-truth/state.md` line 207 pins a former-name occurrence at this spec's line 19, which the refined text no longer holds; the change that commits this revision removes them, as spec 21 A-41 does for its own row.

### Change Log

#### 2026-11-06 — implementation/state reconciliation

- Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

#### 2026-11-13 — auto-mode refinement

- Rewritten in English in the spec-draft structure; original text translated under `## Source`
  and marked non-normative. REQ-01–REQ-12 and AC-01–AC-07 rewritten as single EARS behaviours
  and binary criteria; REQ-13–REQ-48 and AC-08–AC-36 added; data model DM-1–DM-13, interfaces,
  outcome table, promotion rule and negative catalog N-01–N-12 defined; assumptions A-01–A-30
  and open questions Q-01–Q-06 recorded.
- Mapping of original obligations to current requirements: REQ-01 → REQ-01, REQ-35, REQ-48;
  REQ-02 → REQ-02, REQ-13, REQ-20, REQ-21, REQ-47; REQ-03 → REQ-03, REQ-14, REQ-15; REQ-04 →
  REQ-04, REQ-16–REQ-19; REQ-05 → REQ-05, REQ-36; REQ-06 → REQ-06, REQ-38; REQ-07 → REQ-07,
  REQ-32, REQ-46 and the DM-6 task fields; REQ-08 → REQ-08, REQ-28, REQ-29, REQ-31; REQ-09 →
  REQ-09, REQ-33, REQ-34; REQ-10 → REQ-10, REQ-22–REQ-27, REQ-44, REQ-45; REQ-11 → REQ-11;
  REQ-12 → REQ-12, REQ-30, REQ-39, REQ-40, REQ-42, REQ-43.

#### 2026-11-14 — reconciliation with specs 08, 09, 12–18, 21 and 23

- SA-10 and SA-11 gain `per-composite` rules from spec 23's branch-ancestry facts; the branch
  model fact, projection field, `merge` history step and `parallel` case field are added
  (REQ-51, AC-39).
- `flat` is published and stays `tuning` (`published` case field, REQ-50, AC-38);
  reference-build determinism is specified (REQ-49, AC-37).
- Manifest role keys are fixed to `orchestrator`, `arbiter`, `implementer`, `validator` for
  spec 16 (this spec's REQ-53, AC-41); opt-in variant switches are added for specs 15, 17 and 18
  (REQ-52, AC-40).
- Notes confirm specs 09, 12 and 13; Q-05 stands.
- Independent check of the changed passages: env switches restricted to `ORCHESTRAIL_*`, spec 15
  and spec 18 switch forms corrected, `entry` workflow field for N > 1 pairs, composite start
  tip, merge numbering, inherited `GIT_*` cleared, `notes:` entry splitting.

#### 2026-11-14 — second reconciliation pass

- Spec 23 now lists the rebuilt `composite`/`spec-run` reference and projection (C-5, stage 23A)
  and the `composite` case entry with `entry: "spec-run"` and `parallel: 2` (C-5, stage 23B);
  the Notes cite them and confirm the start-tip rule against spec 23's Notes and REQ-37.
- Spec 16 DM-3 statements confirmed (it reads `arbiter`, `implementer`, `validator` and ignores
  `orchestrator`; `adapter` admits `claude` or `null`; an executable variant has one effort for
  every role); DM-12 now says this spec sets no size limit on `report.json` or the manifest.
- Spec 21's citations of this spec's REQ-49, REQ-50, the `published` field and the run-log fields
  `step`, `subtask`, `outcome`, `tests`, `gate` confirmed; no change.
- Spec 14 cites this spec by line number for its extraction of `tdd:` notes lines. This spec
  states the fact: the DM-3 "Leaf mode and leaf tests" fact reads only three `tdd:` entry kinds
  (REQ-18, A-28) and ignores other `notes:` entries; it is recorded in the Notes and made
  explicit in that fact. Spec 14 now cites it by id (independent final review).

#### 2026-11-14 — independent final review

- DM-3 notes parsing joins the `; `-separated behaviours of a `tdd: red digest` entry per spec 13 Data Model → Note entries and reads every `notes` group (AC-12 case g); spec 09 name coupling stated; `manual` variants are not measured; Q-01 recommendation follows ADR-0019; new non-blocker Q-07 (owner policy files and the instructions digest); change-log attributions and identity-ledger follow-up; stale citations corrected.

#### 2026-11-14 — owner decision recorded

- Q-07 resolved (D-01): REQ-54, AC-42–AC-44, the digest definition, DM-8 `instruction_paths` and
  Traceability record that owner policy files enter the instructions digest. Out of Scope and A-24
  updated for spec 21 REQ-81 (the one offline workflow); Notes record the REQ-35 consistency.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph stating the problem and the outcome |
| 2 | Out of Scope names concrete exclusions | PASS — paid runs, validator registration, CI files (spec 21 REQ-81 owns the one workflow), defaults, 21/23 work, telemetry, isolation implementation and others are named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-54; originals keep their ids, bundled obligations split into REQ-13 onward |
| 4 | Every REQ maps to an AC and every AC names a REQ | PASS — `## Traceability` covers REQ-01–REQ-54 and AC-01–AC-44 |
| 5 | Every AC is binary, observable and test-first | PASS — each AC names inputs, a test double or reference build, and exact outputs or exit codes |
| 6 | Non-functional targets measurable or N/A | PASS — determinism, offline operation, durability, privacy and permissions are verifiable; runtime N/A justified by ADR-0020 and absence of an owner target |
| 7 | Data model and contracts specified | PASS — DM-1–DM-13, CLI, exit codes, run sequence, directory opening, resume, imports, isolation, limits, promotion rule, calculator |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — N-01–N-12 and the failure table; concurrency limited by sequential attempts and the experiment lock |
| 9 | Every ambiguity recorded as resolved or open | PASS — A-01–A-30, Q-01–Q-07 (Q-07 resolved 2026-11-14) |
| 10 | No blocker question remains | PASS — Q-01–Q-06 are open non-blockers that limit the live path only; Q-07 is resolved |
| 11 | Every existing-code claim has a verified path:line citation | PASS — citations verified by the author and independently by the critic |
| 12 | Terminology matches project definitions | PASS — pipeline vocabulary from `.ai/principles/domain.md` and the canonical rules; rejected synonyms listed |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — eight delivery parts, at the upper bound; split boundary named in `## Notes` (parts 1–3 regression, 4–8 evaluation) |
| 14 | Devil's Advocate review passed | PASS — Review: 5 rounds, score 99/100, critic: sub-agent, open: none (minor F-46 applied after round 5 without re-scoring) |

Note (2026-11-14, second reconciliation pass): peer-spec obligations and citations were rechecked
against specs 21, 23, 14 and 16 by id; the verdict is unchanged.

Verdict: **READY FOR DEVELOPMENT**. Live execution remains limited by non-blocking questions
Q-02, Q-03 and Q-06 until the owner approves a first regression run. Automated readiness is
not sign-off; review before implementation.
