# 18. Economical decomposition with complete acceptance coverage

## Source

- **Origin:** workstream 9 ("economical decomposition") of the owner's token-optimization
  request of 2026-10-21. Roadmap row 9 of `.ai/specs/README.md` → "Nine token optimization workstreams" — "Coherent leaves, measured
  setup/review overhead, architectural boundaries, integration and AC coverage" — and
  dependency row of `.ai/specs/README.md` → "Dependency order" (order 14, prerequisites 04, 05, 10, 12, 13, 15,
  disposition "New workstream 9"). The shared acceptance gates G1–G8
  (`.ai/specs/README.md` → "Shared acceptance gates") are part of this specification's acceptance contract.
- **Previous revision:** 2026-10-28 (reconciled 2026-11-06), written in Russian. The full
  Russian text is retrievable from the git history of this file at
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Every requirement and acceptance identifier is
  kept below; `## Notes → Identifier history` records each change of wording or scope.
- **Faithful English translation of the previous revision** (translated from Russian; every
  section is kept, tables are rendered as lists; historical and non-normative where it
  conflicts with the requirements below):
  - *Implementation review — 2026-11-06* (originally English, quoted): "Disposition: Planned;
    structural decomposition delivered. Verified source scope: main at
    `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state
    reconciliation on 2026-11-06. Delivered evidence: The decomposition workflow already
    distinguishes leaves/composites/vertical re-slices, records Decomposition Decisions, and
    preserves acceptance/dependency boundaries. Outstanding scope and limits: Measured
    leaf/setup/review economics, calibrated split/merge advice, hash-bound shared context, and
    comparable accepted-result evaluation are not delivered. Structural scoring is not an
    economic measurement. Sources: `workflows/pd-decompose.md`, `rules/workflow-reference.md`,
    `workflows/phase-discovery.md`. Existing requirement and acceptance identifiers remain
    binding. Source inspection and historical validation records do not constitute a fresh
    full-suite or deployed-environment certification."
  - *§1 Status and basis:* "Future capability of workstream 9 of the request of 2026-10-21.
    This revision is aligned with source snapshot `8c2fa08c18115ffcf38a1798742c41e53a2c7461`
    of 2026-10-28. The current `workflows/spec-run.md` passes leaf tasks sequentially to an
    implementer and a separate reviewer. The source materials describe the existing
    classifier, dependency order, target files, agreed leaf boundaries and re-splitting of
    tasks that are too large while preserving work already done. At implementation, verify the
    actual decomposition workflow and its name after migration 09. A separate audit report
    named by the sources is absent from the snapshot and does not prove an economic advisor
    exists. A calibrated cost model and comparison of economic variants are not yet considered
    implemented. A small number of leaves is not a goal in itself: leaves that are too small
    repeat preparation and review; leaves that are too large widen the area of uncertainty and
    the cost of repair."
  - *§2 Goal and boundaries:* "Choose coherent, verifiable subtask boundaries by architecture,
    constraints, risk and available measurements, while preserving all acceptance criteria,
    interfaces, dependencies and integration checks. In scope: split/merge signals, a shared
    architectural contract, an obligation map, a dependency graph, comparison of candidates,
    decision rationale and offline scenarios. Out of scope: automatic merging of running or
    accepted tasks, changing the specification for convenience, minimizing the number of leaves
    at any cost, a new branch model, top-level parallelism, and uncalibrated router training.
    Ownership: 18 — task boundaries, coverage, dependencies and the rationale of economic
    advice; 12 — shared architectural package, provenance and freshness; 04 and 16 — suitable
    available models and supported effort; 05 — measurements, cost and missing data; 10 —
    comparable independent evaluation of strategies; 13 and 15 — checkpoints, acceptance and
    integration evidence; 23 — the future composite branch model and separate parallelism
    conditions. 23 and 16 do not become new prerequisites of 20: until they are delivered
    separately, the existing sequential branches and model/effort selection apply. 18's
    contracts give them the signals they need in advance but do not declare the future
    capability enabled."
  - *§3 Terms and invariants:* "A **leaf** is a terminal task with one coherent verifiable
    result, sufficient context and a manageable area of impact. A **composite task** groups
    children and verifies their interaction but does not remove each child's own testing
    obligations. A leaf's **overhead** includes context preparation, handoff, bookkeeping and
    mandatory review, even when little code changes. Invariants: (1) every AC, invariant,
    interface obligation and off-limits area is represented in the plan; savings do not
    justify an omission. (2) A shared architectural question is decided once with a source,
    not again by each executor; a contradiction or staleness of the decision must be resolved
    before dependent execution. (3) Incompatible risks, required approvals and independent
    checkpoints do not disappear when merging. (4) The dependency graph is acyclic; matching
    target files and shared interfaces have an explicit owner and order. (5) Work already
    started is not silently redistributed; history, AC and evidence are not lost in an
    authorized replan. (6) Cost, time, number of calls and quality are separate quantities;
    unknown is not replaced by zero, and a speed-up is not called a monetary saving. (7) Fewer
    leaves, shared analysis and the absence of matching file names do not prove that parallel
    execution is safe."
  - *§4 Requirements:* "REQ-01: link every AC, invariant and interface obligation to one or
    more leaves and an explicit integration check; keep ownership, test level, off-limits area
    and dependency readiness; an uncovered obligation makes the plan unfit for execution.
    REQ-02: store shared architectural/interface decisions once in 12's fresh contract with
    source and version and reference them from the related leaves; an unresolved shared
    decision blocks dependent execution. REQ-03: consider merging tightly related changes that
    are verified together, with compatible files/context and no need for independent
    boundaries; reject merging incompatible risks/quality bars, unrelated results, required
    approvals and excessive context. REQ-04: consider splitting along architectural
    boundaries, independent acceptance results, file/interface conflicts, context sufficiency,
    uncertainty, criticality and expected rework; do not create small leaves only for a cheap
    model or to claim parallelism. REQ-05: with usable 05/10 calibration, compare the full cost
    of planning, of each leaf's context/handoff/execution/review, of integration and of
    expected repair/escalation, and time separately; state the sample, task class, uncertainty
    and quality bars. Without calibration use conservative structural signs without invented
    probabilities or monetary savings. REQ-06: record the chosen and reasonable rejected
    boundaries in `Decomposition Decisions`, exact dependencies, context/quality signals for
    04/16 and the integration owner; distinguish estimated calls/cost from observations.
    REQ-07: keep the canonical atomic/composite kinds and the sequential top-level stack;
    23's future parallelism requires its own independence evidence; a partially executed task
    is not regrouped on resume without an explicit, provided-for decision. REQ-08: evaluate
    variants on comparable tasks per 10, counting re-planning/context/review and late
    integration defects in 05; apply G1–G8; describe the conservative fallback, replan
    authorization and disabling of advice without losing the canonical plan."
  - *§5 Inputs and output contract:* "Before choosing boundaries the following are needed: the
    source specification and its hash, exact AC, architecture/decisions, test level,
    forbidden files, interfaces, the existing plan and its state, available roles/models,
    working roots and, when present, calibration. Unknown inputs are listed explicitly. A
    discrepancy between sources is not resolved by arbitrarily choosing the convenient
    variant. The output is the existing canonical task files with additive decision evidence,
    not a new mandatory database: identity (`schema_version`, `plan_revision`,
    `source_spec_hash`, `task_contract_hash`, `architecture_contract_hash`); coverage (AC /
    invariant / interface → leaf or leaves → check → integration owner); leaf (identifier,
    goal, type, criteria, target and forbidden paths, working directory, test level, risks,
    context); graph (node identifiers and exact directed dependencies with reason/readiness
    condition); ownership (file/interface → responsible leaf, agreed order for joint work);
    candidates (possible groupings, proven constraints, reason for choice/rejection);
    economics (`structural_only` or a reference to calibration, cost/time components,
    uncertainty, unknown fields); execution boundary (what is frozen, what is already started
    or accepted, the next permitted stage). Not every obligation needs a separate leaf or an
    additional test: one scenario may cover several AC; one existing integration stage may
    cover several leaves. But for every obligation it must be visible where and by whom it is
    verified, so that saving rows does not hide a missing check. When an AC spans several
    components, several leaves may be assigned, but responsibility for final acceptance stays
    unambiguous; 'each checks its own part' without an integration owner is insufficient."
  - *§6 Decomposition algorithm:* "(1) Check source completeness: extract all AC and
    constraints without a retelling that changes their meaning; compare with any existing
    plan; keep started/accepted rows. (2) Extract shared decisions: identify interfaces and
    invariants several changes depend on; write or load a fresh 12 contract; pass unresolved
    questions to the current arbiter/owner before dependent execution. (3) Build a structural
    candidate starting from coherent verifiable results, not a given number of leaves or model
    prices; re-split a large task classified by the existing rules as needing it, by those same
    rules. (4) Check coverage and graph: find uncovered AC, missing owners, cycles, unknown
    dependencies, conflicting target areas and violated approval boundaries. (5) Consider close
    alternatives: for adjacent related changes, check a reasonable merge; for a wide/risky leaf,
    a split along an architectural seam; do not enumerate all combinations artificially.
    (6) Discard inadmissible variants: any omitted criterion, violated prohibition, quality,
    approval or context sufficiency excludes a variant before cost is computed. (7) Compare
    admissible variants: with usable calibration use §8; without it apply structural
    rationale and mark the absence of economic certainty. (8) Record the decision: chosen
    boundaries, reasonable rejected variants, reasons, source versions and integration owner;
    state the next permitted stage. (9) Freeze according to the existing process: execution
    uses the agreed plan; a new assumption during work triggers the provided amendment, not a
    hidden rebuild of the graph."
  - *§7 Merge, split and ownership rules:* "A merge is admissible when all of the following
    hold: the changes serve one coherent result and have a joint understandable acceptance;
    target files/interfaces have a compatible owner and order; the context fits a sufficient
    working area with expansion available per 12, without hiding part of the specification;
    there is no required intermediate approval or independently verifiable readiness that the
    merge would destroy; risks and minimum quality bars are compatible, and a critical part is
    not masked among mechanical changes. A split must be considered when: there are
    independent acceptance results or architectural boundaries allowing meaningful
    verification; one leaf needs incompatible roles, approvals or materially different
    execution conditions; the context is too wide, the impact is hard to establish or expected
    rework would touch an excessively large area; several changes compete for a shared schema,
    interface or file and need explicitly ordered stages. Matching target files do not always
    forbid sequential leaves: they require an explicit dependency and integration owner, but
    they do not allow such leaves to be declared independent for 23's parallelism. A shared
    schema/contract can link leaves even with disjoint paths. Children of a composite are not
    merged automatically just because 23 will later give them one shared branch. Each keeps
    its applicable test cycle. A legitimate `none/n-a`, `pinned` capture of preserved
    behaviour and compatibility of started historical blocks apply through existing grounds,
    not economic advice. Regrouping does not create a retroactive RED and does not erase
    collected evidence."
  - *§8 Economics: full cost and uncertainty:* "For a candidate count: C = planning + shared
    reusable context + Σ over leaves (preparation + handoff + execution + mandatory review) +
    integration verification + expected repairs and escalation + other confirmed costs. Shared
    context is counted once only when the data prove such use. Repeated actual loading/cache
    writes do not disappear from the calculation because of an identical hash. Composite totals
    are not added to child units already included. Identity and monetary valuation rules belong
    entirely to 05. Time is estimated separately: in the current sequential mode sequential
    intervals and overhead are counted; hypothetical speed-up through parallelism is marked as
    a scenario not yet available unless 23 is implemented and allowed. The sum of worker
    durations is not declared the parent run's time. Calibration is usable only when a
    comparable task class, source versions, models/environments, acceptance criteria, full
    accounting of attempts and independent quality evaluation are known. An outdated version, a
    small unrepresentative sample or unknown coverage mean limited applicability. Uncertainty
    is given by data or an honest range; statistical precision is not invented. If the
    intervals of comparable estimates overlap substantially or quality is incomparable, no
    economic winner is declared; the understandable conservative variant is preferred and the
    reason for uncertainty is kept. A low estimated cost does not compensate a violated quality
    bar. Synthetic arithmetic check (conditional units, not measured prices or a project
    promise): one excessively wide leaf — planning 2, preparation and mandatory review 4,
    execution 12, integration 2, expected rework 18, total 38; two coherent leaves — 2, 8, 12,
    2, 2, total 26; six leaves that are too small — 2, 24, 12, 2, 1, total 41. The table shows
    why both the minimum and the maximum number of leaves can lose; it does not establish 'two'
    as optimal; other inputs give another result. Without rework data the corresponding cell
    stays unknown, not zero."
  - *§9 Dependency readiness and replanning:* "An edge `A → B` means a concrete readiness
    condition of A before B, for example independent acceptance of the needed interface/tree.
    Completion of A's execution alone does not replace its verification. A changed shared
    contract invalidates packets based on it that have not started and requires checking its
    impact on work already done. On resume, the specification, plan, states and evidence are
    compared first. An accepted leaf is not renamed or dissolved into a new large leaf to
    improve a report. In an authorized replan the following are kept: previous identifiers and
    states as historical evidence; the mapping of old AC/leaves to new ones with reasons; the
    commits, tests and independent verdicts used; the list of evidence that stays valid and
    that is invalidated; a new plan version and the explicit decision that authorized the
    change. Disabling the economic advisor does not rewrite the plan. The next new
    decomposition uses the previous structural rules; active work continues the agreed plan or
    an owner-provided replan."
  - *§10 Failure scenarios:* "One small coherent result — do not create extra leaves for
    formal multi-stage structure. Many similar mechanical changes — consider joint acceptance,
    keeping the scope and verification of each obligation. Shared critical interface — first
    the architectural decision and integration owner; do not hide it in a cheap group. Not
    enough context — split along a semantic boundary or expand per 12; do not exclude AC. No
    calibration — structural advice with unknown cost. Dependency cycle — reject the plan;
    remove the cycle / extract the shared decision before execution. Joint ownership without
    order — establish a single responsible party and a dependency, or change the boundaries.
    AC changed after agreement — provided amendment/replan with a new version, not silent
    editing. Partially executed composite task — keep progress and evidence; regroup only by an
    explicitly authorized path. Different files but a shared schema — do not declare parallel
    safety; apply 23's separate check."
  - *§11 Acceptance criteria:* "AC-01 (REQ-01, REQ-02): the map covers 100% of source AC,
    invariants and interface obligations; each has a check and an integration owner; related
    leaves use one fresh architectural contract; an unresolved shared decision blocks
    dependent execution. AC-02 (REQ-03, REQ-04): scenarios of related small changes and of an
    architectural seam justify a coherent merge/split; a conflict of approvals, quality, risk
    or context sufficiency excludes an inadmissible variant before economic comparison. AC-03
    (REQ-05): manual synthetic sums confirm that fragmentation and excessive size can both
    raise cost; without calibration there are no invented probabilities/monetary savings;
    shared and child costs are not counted twice. AC-04 (REQ-06, REQ-07): the plan contains
    chosen/rejected boundaries, reasons, an acyclic graph and explicit ownership; existing
    types/stack are kept; resuming does not silently change started tasks and does not declare
    parallelism from one grouping. AC-05 (REQ-08): offline scenarios detect a coverage gap and
    an integration defect; comparable reporting includes planning/context/review/rework;
    disabling advice and authorized replanning without loss of history are verified; fewer
    leaves is not presented as proven savings or equal quality. Traceability: REQ-01–02 →
    AC-01; REQ-03–04 → AC-02; REQ-05 → AC-03; REQ-06–07 → AC-04; REQ-08 → AC-05."
  - *§12 Implementation and readiness:* "(1) Verify the current classifier and plan freeze
    after migration 09; keep the single canonical place of the rules. (2) Add the
    coverage/ownership schema and failing scenarios for cycles, omitted AC and conflicting
    boundaries. (3) Implement structural proposals without monetary valuation, then an optional
    comparison by usable calibration. (4) Link the shared contract with 12, checkpoints with
    13, integration verification with 15 and metrics with 05. (5) Verify preservation of
    started tasks, disabling and authorized replanning; evaluate live strategies separately per
    10. Dependencies: 04, 05, 10, 12, 13, 15. G1–G8 are mandatory. Deterministic implementation
    needs no invented calibration. The value of strong shared planning, cheap execution or
    another chain is established by independent data, not by a number of leaves chosen in
    advance."
  - *Change Log, 2026-11-06* (originally English, quoted): "Owner-authorized source review at
    `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations,
    and verification limits in the Implementation review above. Preserve
    requirement/acceptance identifiers and historical decisions; repair current local
    references where needed."
- **Refinement authority:** the repository owner authorized in-place replacement of this file
  and auto-mode resolution (2026-11-14). Names below are today's names
  (`workflows/pd-decompose.md`, `rules/workflow-reference.md`, …); after spec 09 is delivered
  they follow spec 09's rename maps (`.ai/specs/09-model-only-harnesses-and-rule-naming.md`:
  DM-1 name map, DM-10 rule map, DM-12 section map, and Notes "Files and sections created
  after this spec"; see C-5 "Rule-file names after spec 09").

## Context & Problem

Repository citations are verified at `060ce6d`; citations of specs 08–10, 12–17 and 23 are verified
against their working-tree revisions in this worktree on 2026-11-14 (uncommitted at that time).

1. **Decomposition is structural and judgment-based.** `/pd-decompose` drafts "logical
   domain/module subtasks … each independently verifiable with 3–15 implementation steps",
   targets eight top-level subtasks and records choices "in `plan.md → ## Decomposition
   Decisions`" (`workflows/pd-decompose.md:27-33`). The classifier computes S1–S5 and
   enforces the leaf-health invariant "a leaf requires S2 = 1 AND S5 = 1"
   (`rules/workflow-reference.md:485-523`, `:511-512`). The Decomposition Rules forbid splitting
   by operation type and merging independent components "solely to reach the minimum"
   (`rules/workflow-reference.md:554-574`). Nothing records which boundary alternatives were
   considered against which named condition, so a reviewer cannot tell a coherent merge from
   an arbitrary one.
2. **Acceptance coverage is not traced.** Each description carries its own criteria
   (`workflows/pd-decompose.md:76-78`) and `/pd-finalize` checks that every description has
   binary criteria and a scenario per criterion (`workflows/pd-finalize.md:44-63`). No artifact
   maps each criterion of the specification to the subtasks that verify it, and no check
   detects a specification criterion that no subtask covers. Task-level criteria are judged
   only at Validation (`workflows/pv-contract.md:30`), after all leaves are built.
3. **Integration responsibility is implicit.** Composites own "integration-level criteria"
   (`.ai/principles/domain.md:20`); for top-level leaves that jointly satisfy one criterion,
   no artifact names who verifies the combination before task Validation.
4. **Shared interfaces and shared files have no recorded owner or order.** Type 3 makes "the
   consumer depend on the producer" (`workflows/pd-decompose.md:39-45`), but for other
   subtasks the plan only "Describe[s] any shared-file constraints" in prose
   (`workflows/pd-decompose.md:127-129`). Prose ordering cannot be checked and cannot serve as
   independence evidence.
5. **Shared design is written once but not linked.** `/pd-design` writes `### Invariants` and
   `### Decision` (`workflows/pd-design.md:32-60`) after decomposition
   (`workflows/phase-discovery.md:158-164`). Spec 12 delivers these items to every worker as the
   shared architectural contract (spec 12 C-8 row 18, DM-5 items 4–5), but no plan field says which interface agreement an item records.
6. **Per-leaf overhead is real but unmeasured.** Under `/spec-run` every leaf gets its own
   branch, Implementer with two checkpoints and a separate Validator
   (`workflows/spec-run.md:188-199`, `:208`, `:284`), so each extra leaf repeats setup and review.
   Specs 12, 13 and 15 expose per-leaf evidence (packet bytes, attempt counts, review records)
   that nothing combines. Spec 05 values whole runs and ranks fully priced leaves by opaque
   owner identifiers (`scripts/usage_telemetry_report.py:697-714`,
   `scripts/usage_telemetry_adapter.py:20-24`). The roadmap states that no saving has been
   measured (`.ai/specs/README.md` → "Nine token optimization workstreams": "No percentage or dollar saving is established here").
7. **Parallelism evidence is owed to spec 23.** ADR-0009 Decision 4 requires `/pd-decompose` to
   record independence evidence (disjoint target files, no shared contract/schema, no
   dependency edge) for composite children (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:143-162`).
   Spec 23 defines the `### Parallel Safety` table (DM-5) and, since its 2026-11-14
   reconciliation, renders it from this spec's DM-8 in `/pd-decompose` (REQ-09) and re-renders it
   in `/pd-design` (REQ-52); this spec supplies the evidence only.
8. **The validator inventory is frozen.** New checks are standalone programs
   (ADR-0019 Decision 3, `.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`);
   frozen checks already read `workflows/pd-decompose.md`, `workflows/pd-finalize.md` and
   `rules/workflow-reference.md` (`scripts/validate-contracts.sh:604`, `:728-822`).

**Consequence.** A plan can omit a specification criterion, leave a jointly satisfied
criterion without an integration owner, order shared files only in prose and grow or shrink
leaf counts without a recorded reason, and none of this is detected before execution. Leaf
overhead cannot be measured per leaf, so no economic claim about leaf granularity can be
made or tested.

## Goal

Make every full-flow plan carry checkable evidence that each specification criterion and
each shared interface is verified by named subtasks with one integration owner, that every
ordering constraint, shared file and shared interface has an explicit dependency, and that
every chosen merge or split satisfies named conditions — verified deterministically before
Discovery finishes — while keeping today's structural decomposition as the only basis for
boundaries until a spec 10 comparison qualifies another policy, producing the independence
evidence spec 23 needs for composite children, and reporting measured per-leaf setup, review
and repair overhead from the evidence specs 12, 13, 15 and 17 expose, for the owner and for
spec 10 experiments.

## Scope

1. Canonical definitions in `rules/workflow-reference.md`: spec criteria, the `## Coverage`
   and `## Interfaces` plan sections, the covers tag, integration-owner rules, the exclusive
   resources line, merge conditions, split triggers, the `### Boundary Alternatives` record and
   the `economics:` line; entries for the new plan sections in the protected-sections list labelled `` **`plan.md`:** `` (C-5).
2. Workflow edits: `/pd-analyze` (derived criteria ids), `/pd-decompose` (writes the new
   sections, tags and lines; ordering only through `Depends On`), `/pd-design` (interface
   contracts as Invariants items), `/pd-finalize` (runs the verifier), `/spec-run` (reruns the
   verifier after the batch gate); `templates/subtask-description.md`.
3. An optional standard-library helper `scripts/decomposition.py` (entry) with engine
   `scripts/decomposition_engine.py`, subcommands `verify` and `overhead`, read-only, offline.
4. Parallel evidence for composite children (DM-8), the input spec 23 renders into its
   `### Parallel Safety` table.
5. A standalone acceptance suite `scripts/check-decomposition.py`.
6. Vocabulary entries in `.ai/principles/domain.md`, an ADR, `.ai/memory/architecture.md`
   contract-surface update and `docs/USAGE.md` mention.

## Out of Scope

- Any change to the classifier signals S1–S5, the leaf-health invariant, the depth-2 cap,
  Type 2/Type 3 rules or the 3–15 step rule (`rules/workflow-reference.md:485-574`).
- Any cost, token, probability or duration estimate inside plans or descriptions; any
  calibrated or economic split/merge advice; any owner policy file for decomposition; any
  automatic change of granularity.
- Running, scheduling or approving a spec 10 experiment; any paid model run.
- Per-leaf money or token cost in the overhead report (spec 05 owns valuation; its owner
  identifiers are opaque, `scripts/usage_telemetry_adapter.py:20-24`); tool-output bytes
  (spec 14, reachable only through a spec 05 adapter, spec 14 C-7 row 05).
- Writing the `### Parallel Safety` table, the `Parallel-safe` value, the independence
  predicate, admission or any parallel scheduling (spec 23 REQ-09, REQ-05).
- Parallelism across composite boundaries or among top-level leaves (spec 23 Q-01).
- A new subtask kind, branch model, status value or change of the sequential stack.
- A per-leaf complexity classification (spec 16 DM-4 and `/pd-select-model` own it).
- Changes to `scripts/validate-contracts.sh`, `scripts/validate-task.sh`, `scripts/sync.sh` or
  any file under `tests/`.
- Quick-flow tasks (`flow: quick`), their gate and their inline contract.
- Rewriting plans of tasks whose Discovery is already complete.

## Actors & Roles

| Actor | Allowed actions | Forbidden |
|---|---|---|
| Owner | Approves spec 10 experiments; decides any later decomposition policy through a separate spec | — |
| `/pd-analyze` | Labels derived criteria `DC-<n>` in `### Assumptions` | Writing plan sections |
| `/pd-decompose` | Writes `## Coverage`, `## Interfaces`, `### Boundary Alternatives`, the `economics:` line, covers tags, exclusive-resources lines and `Depends On` edges | Writing cost/probability/time estimates; changing rows of started subtasks |
| `/pd-design` | Records interface shapes as `### Invariants` items; fills `Contract` cells; reconciles the new sections when it reruns decomposition | Leaving a contract `pending-design` at its end |
| `/pd-finalize` | Runs `verify`; stops on violations | Rewriting recorded progress to make checks pass |
| Orchestrator (`/spec-run`) | After the batch gate, turns answered `pending:Q<n>` contracts into Invariants items and `INV-<n>` cells; reruns `verify`; stops before the first branch on failure | Starting a branch while `verify` fails |
| `scripts/decomposition.py` | Reads the task directory, the specification and the optional evidence files; prints one JSON line | Writing any file; network; spawning processes or models |
| `scripts/check-decomposition.py` | Builds fixtures in a temporary directory; runs the helper | Being called by `scripts/validate-contracts.sh` or `scripts/sync.sh` |
| Spec 23 `/pd-decompose` extension (future) | Renders DM-8 into `### Parallel Safety` | — |

## Terminology

| Term | Definition | Source |
|---|---|---|
| **Spec criterion** | One acceptance criterion in the task's scope, identified per DM-1 as `AC-<digits>` (its own id), `SPEC-<n>` (ordinal) or `DC-<n>` (derived) | Previous §5 "exact AC"; DM-1 |
| **Coverage** | The `plan.md → ## Coverage` table mapping each spec criterion to the subtasks whose criteria verify it and to one integration owner | Previous §5 "obligation map" |
| **Covers tag** | The text `(covers: <ref>, …)` inside a description's acceptance criterion, naming the spec criteria or interfaces that criterion verifies | DM-4 |
| **Interface** | A named contract one subtask produces and other subtasks consume (signature, file format, schema, command) | Previous §3 invariant 4 |
| **Interface contract** | The single `### Invariants` item of `## Solution Design` that records an interface's agreed shape, referenced as `INV-<n>` | Previous REQ-02; spec 15 DM-2 numbering |
| **Integration owner** | The subtask (or `task`) that verifies the combined result of several subtasks for one criterion or interface | Previous §5 |
| **Dependency path** | A chain of one or more `Depends On` edges from subtask X to subtask Y in `## Subtasks` ("X depends on Y") | `workflows/pd-decompose.md:123-126` |
| **Boundary alternative** | One considered merge or split of candidate units, recorded with outcome and codes | Previous REQ-06 |
| **Merge conditions** | The five codes that must all hold for a chosen merge (DM-6) | Previous §7 |
| **Split triggers** | The codes of which at least one must hold for a chosen split (DM-6) | Previous §7 |
| **Economic basis** | The value of the `economics:` line; this version knows only `structural-only` | Previous §5 "economics" |
| **Write set** | Spec 23's term; here the explicit target-file entries of a leaf | Spec 23 Terminology, "Write set" |
| **Exclusive resource** | A resource a leaf's tests or implementation must use alone (fixed port, shared database, external service, host-exclusive benchmark) | Spec 23 DM-5 |
| **Parallel evidence** | The DM-8 object per composite child | ADR-0009 Decision 4 |
| **Overhead report** | The DM-9 output of `overhead`: per-leaf counts and bytes of setup, review and repair work | Previous §3 "overhead" |

Rejected synonyms: "obligation map" (use Coverage), "economic advisor" or "advice" (not
delivered; see Notes), "parallel-safe" (spec 23's value, never produced here), "complexity"
for anything other than spec 16's input.

## Requirements

Component tags name the implementing actor. Previous identifiers REQ-01–REQ-08 are kept with
refined wording; `## Notes → Identifier history` lists what moved. Every requirement applies
to `flow: full` tasks only (REQ-28).

### Coverage and shared contracts

- **REQ-01 Coverage table.** WHEN `/pd-decompose` writes a full-flow plan, THE workflow SHALL
  write `plan.md → ## Coverage` (DM-2) with exactly one row per spec criterion of DM-1.
- **REQ-02 Interface contract recorded once.** WHEN `/pd-design` writes `## Solution Design`,
  THE workflow SHALL record the agreed shape of each interface listed in `## Interfaces` as one
  item of `### Invariants` and write that item's `INV-<n>` into the interface's `Contract` cell.
- **REQ-09 Pending contracts block finalization.** IF an `## Interfaces` row has `Contract`
  `pending-design`, an `INV-<n>` with no such item, or `pending:Q<n>` without a matching
  `- Q<n>:` entry in `state.md → ## Open Questions (batch)`, THEN `verify` [helper] SHALL report
  the matching C-4 violation.
- **REQ-10 Batch-gate recheck.** WHEN the Orchestrator has written the batch answers and
  reconciled the plan (`workflows/spec-run.md:107-111`), THE Orchestrator SHALL run `verify`
  and treat its exit code as REQ-23 does, stopping before creating any branch on exit 1 or 2.
- **REQ-40 Answered interface questions.** WHEN the batch answers resolve a question named by a
  `pending:Q<n>` contract, THE Orchestrator SHALL, during that reconciliation, add one
  `### Invariants` item recording the answered shape and replace `pending:Q<n>` with its
  `INV-<n>`.
- **REQ-41 Batch entry for interface questions.** WHEN `/pd-design` writes `pending:Q<n>`, THE
  workflow SHALL ensure `## Open Questions (batch)` holds a `- Q<n>:` entry in the format of
  `workflows/pd-analyze.md:92-98`.
- **REQ-15 Criteria identity.** WHEN `verify` runs, THE helper SHALL derive the spec criteria
  exactly as DM-1 defines and report them in DM-7 `criteria`.
- **REQ-16 Criterion completeness.** IF a spec criterion has no `## Coverage` row, a row names
  an id that is not a spec criterion, or two rows name the same id, THEN `verify` SHALL report
  `criterion-uncovered`, `criterion-unknown` or `criterion-duplicate-row` respectively.
- **REQ-17 Tags agree with tables.** IF a subtask listed in a `## Coverage` or `## Interfaces`
  row has no covers tag naming that row's criterion or interface, or a covers tag names a
  criterion or interface whose row neither lists that subtask nor names it as integration owner,
  THEN `verify` SHALL report `tag-missing` or `tag-unlisted` respectively.
- **REQ-18 Integration owner.** IF a row's `Integration owner` violates DM-2 rule O-1–O-4,
  THEN `verify` SHALL report `owner-missing` or `owner-invalid` as C-4 assigns.
- **REQ-39 Well-formed tables.** IF a cell of DM-2, DM-3 or DM-6 violates its grammar, or a
  section of DM-2, DM-3 or DM-6 occurs twice, THEN `verify` SHALL report `cell-invalid` or
  `section-duplicate` (C-4).
- **REQ-19 Withdrawn and deferred criteria.** IF a `## Coverage` row is `withdrawn — amendment`
  without its id in `state.md → ### Description Amendments`, or `deferred — phase <K>` without
  a matching deferred phase line, THEN `verify` SHALL report `withdrawal-unrecorded` or
  `deferral-invalid`.

### Order, files and resources

- **REQ-11 Interface order.** IF a consumer of an interface has no dependency path to its
  producer, THEN `verify` SHALL report `interface-order-missing`.
- **REQ-12 Shared-file order.** IF two leaves in the same repository list the same explicit
  target-file path and neither has a dependency path to the other, THEN `verify` SHALL report
  `shared-file-unordered`.
- **REQ-13 Ordering through dependencies only.** THE `/pd-decompose` workflow SHALL express every
  ordering constraint between two named subtasks, including shared-file and shared-interface
  order, as a `Depends On` edge.
- **REQ-35 No prose ordering.** THE `## Execution Strategy` section SHALL name no ordering between
  two specific subtasks; its task-wide policies stay (Type 3 producer before consumer, and
  composite children integrating in listed order, which is integration order and not a
  readiness constraint; a child that needs another child's output has a `Depends On` edge).
- **REQ-14 Graph validity.** IF a subtask id in `Depends On`, `## Coverage` or `## Interfaces`
  does not resolve to a `## Subtasks` row, a `Depends On` cell holds anything but ids, `,`,
  spaces, `—`, `-` or nothing, or the `Depends On` graph has a cycle, THEN `verify` SHALL report
  `id-unresolved`, `depends-on-malformed` or `graph-cycle`.
- **REQ-20 Exclusive resources line.** IF a leaf description's `## Context` lacks exactly one
  DM-5 line or that line violates DM-5, THEN `verify` SHALL report `resources-line-invalid`.

### Boundaries and economics

- **REQ-03 Merge conditions.** IF a `### Boundary Alternatives` row records `merge` with outcome
  `chosen` and its Codes do not contain all five merge conditions of DM-6, THEN `verify` SHALL
  report `boundary-row-invalid`.
- **REQ-04 Split triggers.** IF a row records `split` with outcome `chosen` and its Codes are
  empty or contain a code outside the split-trigger set of DM-6, THEN `verify` SHALL report
  `boundary-row-invalid`.
- **REQ-06 Boundary record.** WHEN `/pd-decompose` writes `## Decomposition Decisions`, THE
  workflow SHALL include `### Boundary Alternatives` (DM-6) with one row per merge or split it
  considered between candidate units, or the single line `None — <reason>`.
- **REQ-05 Structural economic basis.** WHEN `/pd-decompose` writes `## Decomposition Decisions`,
  THE workflow SHALL write exactly one line `economics: structural-only` as DM-6 places it.
- **REQ-33 No estimates.** THE Discovery workflows SHALL write no cost, token, probability or
  duration estimate into `plan.md` or any description.
- **REQ-31 Canonical rule text.** THE `rules/workflow-reference.md` file (or its successor files, C-5 "Rule-file names after spec 09") SHALL hold the only
  definitions of DM-1–DM-6 (sections of C-5), and every workflow SHALL cite them by
  `file → ## Section` instead of restating them.

### Stack, resume and evaluation

- **REQ-07 Kinds and stack.** THE SYSTEM SHALL keep leaf, composite (Type 2) and Type 3
  re-slice as the only subtask kinds and SHALL keep the sequential top-level stack.
- **REQ-34 No parallel claim from grouping.** THE SYSTEM SHALL derive no parallel-safety value
  from a grouping decision or from boundary evidence; independence of composite children is
  decided only by spec 23's own predicate (spec 23 REQ-05).
- **REQ-24 Resume preservation.** WHEN `/pd-decompose` or `/pd-design` reruns on a plan with a
  started subtask, THE workflow SHALL leave unchanged every `## Coverage` and `## Interfaces` row
  that names a started subtask in any cell, and the covers tags of every started subtask, and
  SHALL report a reconciliation blocker if a change to them is required. A subtask is started
  when its `## Subtasks` `Status` is not `not-started` or any status field of its block in
  `## Subtask Progress` is not `not-started`.
- **REQ-08 Evaluation boundary.** WHERE a decomposition policy other than the current rules is
  to be evaluated, THE evaluation SHALL be a spec 10 comparison, and neither
  `scripts/decomposition.py`, `scripts/check-decomposition.py`, Discovery, validation nor sync
  SHALL start a model run.
- **REQ-28 Quick flow untouched.** WHILE a task has `flow: quick`, THE `verify` subcommand SHALL
  print a DM-7 line with `status: not-applicable` and exit 0, and no Discovery step SHALL write
  the sections of DM-2, DM-3 or DM-6 (quick flow writes no `plan.md`,
  `workflows/phase-discovery.md:166-167`).
- **REQ-29 No second complexity classification.** THE SYSTEM SHALL produce no per-leaf
  complexity value; the per-leaf complexity input of spec 16 remains its DM-4 `effort-input:`
  line written by `/pd-select-model`.

### Helper and finalization

- **REQ-21 Parallel evidence.** WHEN `verify` runs on a plan containing a composite, THE helper
  SHALL include one DM-8 object per child of every composite in DM-7 `parallel_evidence`.
- **REQ-22 Verify interface.** WHEN `verify` is invoked, THE helper SHALL follow C-1 and C-2 and
  print exactly one DM-7 line on exit 0 or 1.
- **REQ-23 Finalization gate.** WHEN `/pd-finalize` runs for full flow and the helper is available
  (C-5), THE workflow SHALL run `verify` and, on exit 1 or 2, stop with the violations and the
  responsible step of C-4, editing no artifact itself, as for its other consistency failures
  (`workflows/pd-finalize.md:62-63`); on exit 3 or when unavailable it SHALL apply the same rules
  manually and report once that the helper was unavailable. Recovery is the existing route: rerun
  the responsible step under its overwrite Guard, then `/pd-select-model` when descriptions
  changed (`workflows/phase-discovery.md:163`).
- **REQ-27 Legacy plans.** THE Execution and Validation workflows SHALL NOT require
  `## Coverage`, `## Interfaces`, `### Boundary Alternatives`, the `economics:` line, covers tags
  or DM-5 lines; IF `verify` runs on a plan without them, THEN it SHALL report `section-missing`
  per absent section.
- **REQ-30 Frozen validator.** THE delivery SHALL change no byte of
  `scripts/validate-contracts.sh`, `scripts/validate-task.sh`, `scripts/sync.sh` or any file
  under `tests/`.
- **REQ-36 Preserved text.** THE delivery SHALL remove or alter no existing line of the edited
  rule, workflow and template files other than the one sentence C-5 replaces in
  `workflows/pd-decompose.md` (C-5 → Preserved anchors).
- **REQ-32 Vocabulary.** THE delivery SHALL add the terms Spec criterion, Coverage, Covers tag,
  Integration owner, Interface contract and Boundary alternative to the vocabulary table of
  `.ai/principles/domain.md`.
- **REQ-37 Decision record.** THE delivery SHALL add an Accepted ADR for the plan contract and
  index it in `.ai/adr/index.md`.
- **REQ-38 Operating documentation.** THE delivery SHALL name `scripts/decomposition.py` in the
  contract surface of `.ai/memory/architecture.md`, list it in `scripts/README.md`, and describe
  in `docs/USAGE.md` how to run `overhead` and how to obtain its two option files (C-6).

### Overhead evidence

- **REQ-25 Overhead report.** WHEN `overhead` runs, THE helper SHALL print one DM-9 line built
  only from the task directory and the files named by its options.
- **REQ-26 Unknown is not zero.** IF a DM-9 value's source is absent, unreadable or does not
  cover a leaf, THEN THE helper SHALL write `null` for that value and add one `unavailable`
  entry with its reason, and SHALL never write `0` for an unobserved count.

## Data Model

All structures are new unless marked existing. Parsing follows spec 15 C-3
(Parsing rules): ATX headings outside fenced code, a section
runs to the next heading of the same or higher level, top-level list items as defined there.
Tables: the first line of the section starting with `|` is the header, the next line the
separator; each following line starting with `|` is a row; the table ends at the first later
line that does not start with `|`. Cells are split on `|` and trimmed. A header other than the
one shown for its section, or a row whose cell count differs from the header, is
`table-malformed`. Fixed headers apply to `## Coverage`, `## Interfaces` and
`### Boundary Alternatives` only. In `## Subtasks` (existing, headers vary,
`rules/workflow-reference.md:132`, `workflows/pd-decompose.md:104-121`) columns are found by header name: `ID` and `Depends On`
are required (absent → `table-malformed` for `## Subtasks`), `Status` and `Type` are read when
present, and other columns are ignored.

### DM-1 Spec criteria (derived, not stored)

1. **Specification text.** `spec_path:` from the top of task `state.md`, resolved against the
   parent of the nearest ancestor directory of the task named `.ai`; absolute paths are used as
   is. Without `spec_path:`, the task's legacy `description.md` (`workflows/pd-analyze.md:20-22`).
2. **Scope.** Without an `active_phase:` line: the whole text. With `active_phase: N`: the text
   before the first phase heading (the preamble) plus the section from the phase heading of N to
   the next phase heading (the boundary of `workflows/pd-analyze.md:23-26`). A phase heading is
   an ATX heading outside fences matching `^#{2,3} Phase ([0-9]+)\b`.
3. **Sections.** Every heading in scope whose text, after removing an optional leading
   `<digits>. `, equals `Acceptance Criteria` compared case-insensitively.
4. **Items.** The top-level list items of those sections in document order (spec 15 C-3). A
   section with non-blank content and no list item contributes one item (its whole body), and
   `criteria.notes` contains `unstructured`; such items always get ordinal ids.
5. **Identifiers.** For each item, strip the list marker, an optional `[ ] `/`[x] ` checkbox and
   leading `*`, `_` and `` ` `` characters. If every item then starts with `AC-<digits>` followed
   by a non-alphanumeric character or end of text, and these ids are unique, each item's id is
   that token (`source: spec-ids`). Otherwise items are `SPEC-1`, `SPEC-2`, … in order
   (`source: spec-ordinals`; `criteria.notes` contains `duplicate-ids` when two leading ids are
   equal).
6. **Derived.** With no item in scope: the distinct tokens `DC-<digits>` in
   `## Task Analysis → ### Assumptions` (`source: derived`). With none of those either:
   `source: none`, no criteria, violation `criteria-absent`.

### DM-2 `plan.md → ## Coverage` (protected)

```
## Coverage

| Criterion | Subtasks | Integration owner |
|-----------|----------|-------------------|
| AC-01 | T-01 | — |
| AC-02 | T-03a, T-03b | T-03 |
| AC-04 | withdrawn — amendment | — |
```

- `Criterion`: one spec criterion id.
- `Subtasks`: comma-separated subtask ids (pattern
  `T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?`), or exactly `withdrawn — amendment`, or
  exactly `deferred — phase <K>`. Deferral applies only to a criterion of the preamble of a
  multi-phase specification (DM-1 item 2) that belongs to a later phase; it is valid when the
  criterion came from the preamble, `state.md` has `active_phase:` other than K and `## Spec Phases` has a line matching
  `^- phase K: deferred( |$)` (`workflows/phase-discovery.md:114-118`). Anything else in the cell
  is `cell-invalid`.
- `Integration owner`: `—`, a subtask id, or `task` (verified at task Validation, O-4).
- Owner rules, where S is the listed subtasks (Interfaces: producer plus consumers):
  - **O-1** `—` is valid only in `## Coverage`, only when S has exactly one member and it is a
    leaf, and is required for withdrawn and deferred rows (another owner there is
    `cell-invalid`).
  - **O-2** When S has two or more members or contains a composite, the owner is not `—`
    (`owner-missing`).
  - **O-3** An id X is valid when (a) X is a composite and every member of S is X or one of X's
    children, or (b) X is in S and X has a dependency path to every other member of S; and X's
    description has a covers tag for the row (`owner-invalid` otherwise).
  - **O-4** `task` is valid in `## Coverage` only when the criterion id occurs as a token
    (regex `(?<![A-Za-z0-9-])<id>(?![A-Za-z0-9-])`, so `AC-1` does not match `AC-10`) in an
    item of `## Solution Design → ### Acceptance Criteria` (so `/pv-contract` judges it,
    `workflows/pv-contract.md:30`), and in `## Interfaces` only when the `Contract` cell is a
    resolving `INV-<n>` (judged as an invariant there); otherwise `owner-invalid`.
- Composite children are read from the `children:` line of the `[composite] <id> |` block in
  `state.md → ## Subtask Progress` (`rules/workflow-globals.md:212-213`); a subtask is a composite
  exactly when such a block exists.
- Body may not be `None`; a task always has at least one criterion or reports `criteria-absent`.

### DM-3 `plan.md → ## Interfaces` (protected)

```
## Interfaces

| Interface | Producer | Consumers | Contract | Integration owner |
|-----------|----------|-----------|----------|-------------------|
| token-schema | T-01 | T-02, T-03a | INV-2 | T-03a |
```

- Body is this table or the single line `None`.
- `Interface`: unique, `^[a-z0-9]+(-[a-z0-9]+)*$`, a domain name (a violation is `cell-invalid`).
- `Producer`: one subtask id. `Consumers`: one or more ids, none equal to the producer
  (`interface-party-invalid`).
- `Contract` (any other value is `cell-invalid`): `INV-<n>` (the n-th item of `## Solution Design → ### Invariants`, numbered as spec
  15 DM-2, obligation `INV-<n>` counted from 1 in source order), `pending-design` (written by
  `/pd-decompose`), or `pending:Q<n>` (an open batch question under `/spec-run`).
- `Integration owner`: rules O-2–O-4 of DM-2.

### DM-4 Covers tag (extends description `## Acceptance Criteria`, existing section)

`(covers: <ref>[, <ref>]…)` anywhere in one top-level item of a description's
`## Acceptance Criteria`, where `<ref>` is a spec criterion id or `interface:<name>`. An item may
carry several tags. Tags elsewhere are ignored. Example item:
`- Given a stored token, the route returns 200 with the token body (covers: AC-02, interface:token-schema)`.
Descriptions resolve as `<task>/<id>-*/description.md` or `<task>/<id>/description.md`; zero or
several matches is `description-unresolved`.

### DM-5 Exclusive resources line (extends description `## Context`, existing section)

Exactly one line in every leaf description's `## Context`:
`- Exclusive resources: none` or `- Exclusive resources: <name>[, <name>]…`, each name non-empty
after trimming, without `,`, and not `none`. Composite descriptions carry no such line.

### DM-6 `## Decomposition Decisions → ### Boundary Alternatives` and the `economics:` line

```
## Decomposition Decisions

economics: structural-only

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-02 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | one module |

### Boundary Alternatives

| Alternative | Kind | Candidates | Outcome | Codes | Evidence |
|-------------|------|------------|---------|-------|----------|
| B-1 | merge | config loader + config validator → T-02 | chosen | one-result, compatible-files, context-fits, no-intermediate-gate, compatible-risk | one module, one AC cluster |
| B-2 | split | T-04 | rejected | one-result | single verifiable output |
```

- The `economics:` line is the first non-blank line after the `## Decomposition Decisions`
  heading, before the existing classifier table (`workflows/pd-decompose.md:131-139`).
- Body of `### Boundary Alternatives` (blank lines ignored) is the table or one line
  `None — <non-empty reason>`; any other non-blank line there is `cell-invalid`.
- `Alternative`: unique `B-<n>`. `Kind`: `merge` | `split`. `Outcome`: `chosen` | `rejected`.
  `Candidates`: free text naming the candidate units or subtask ids. `Evidence`: non-empty text.
- `Codes`: comma-separated, from the set for its kind and outcome:

| Kind / outcome | Allowed codes | Rule |
|---|---|---|
| merge / chosen | `one-result`, `compatible-files`, `context-fits`, `no-intermediate-gate`, `compatible-risk` | All five required (merge conditions) |
| merge / rejected | `separate-results`, `leaf-health`, `incompatible-files`, `context-too-wide`, `intermediate-gate`, `incompatible-risk`, `architectural-boundary` | At least one |
| split / chosen | `separate-acceptance`, `architectural-boundary`, `incompatible-conditions`, `context-too-wide`, `contended-interface`, `uncertainty` | At least one (split triggers) |
| split / rejected | `one-result`, `no-independent-verification`, `leaf-health`, `below-minimum-steps` | At least one |

  Meanings: `one-result` — the units serve one coherent result with joint acceptance;
  `compatible-files` — their target files and interfaces have one owner and order;
  `context-fits` — the merged unit's context needs no hidden part of the specification;
  `no-intermediate-gate` — no required intermediate approval or independently verifiable
  readiness is lost; `compatible-risk` — risks and quality floors are compatible and no
  critical part is masked among mechanical changes; `separate-results`/`separate-acceptance` —
  independent acceptance results; `architectural-boundary` — an architectural seam allowing
  meaningful separate verification; `incompatible-conditions` — different roles, approvals or
  execution conditions; `context-too-wide` — context too wide or impact hard to establish;
  `contended-interface` — several changes compete for one schema, interface or file and need
  ordered stages; `uncertainty` — uncertainty, criticality or expected rework confined to part
  of the unit; `leaf-health` — the result would violate S2 = 1 and S5 = 1;
  `no-independent-verification` — a part would have no verifiable done-state;
  `below-minimum-steps` — a part would have fewer than 3 steps. A cheaper model and parallelism
  are not codes, so neither can justify a chosen split.
- `economics:` line: exactly one line in `## Decomposition Decisions` starting `economics:`; it
  must be `economics: structural-only` in the position above. This version defines no other
  value.

### DM-7 `verify` result (stdout, one canonical JSON line)

Canonical JSON: `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
followed by `\n`.

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | — |
| `kind` | `"decomposition_verification"` | — |
| `status` | `pass` \| `fail` \| `not-applicable` | `not-applicable` for `flow: quick` |
| `criteria` | `{source, scope, ids, notes}` or `null` | `source` ∈ `spec-ids`, `spec-ordinals`, `derived`, `none`; `scope` `whole` or `phase <N>`; `ids` in document order; `notes` a sorted list, subset of `duplicate-ids`, `unstructured`; `null` when `not-applicable` |
| `subtasks` | `{leaves: int, composites: int}` or `null` | From `## Subtasks` and composite blocks; `null` when `not-applicable` |
| `violations` | list of `{code, subject, detail}` | C-4 codes and subjects; `detail` is one human-readable line that tests do not compare; sorted by `code`, then `subject`; `[]` on pass and when `not-applicable` |
| `write_sets` | list of `{subtask, repository, complete, entries}` | One per leaf in plan order; `entries` as written (renames `old -> new`) or `null` when `complete` is false; `[]` when `not-applicable` |
| `parallel_evidence` | list of DM-8 | Plan order; `[]` without composites and when `not-applicable` |

Write-set completeness: the first line of the description's `## Scope` matching
`^\s*-?\s*(\*\*)?Target files:(\*\*)?\s*(.*)$` holds comma-separated entries (backticks
removed). The set is complete when it has at least one entry and every path (both sides of
`old -> new`) is relative, has no `..` segment, contains none of `*?[]{}`, does not end with `/`,
is not `—`, `-` or `none`, and is not an existing directory under the repository root.
`repository` is the description's `working_dir:` resolved from its directory, else the project
root (parent of `.ai`), as an absolute normalized path.

### DM-8 Parallel evidence (one per composite child)

| Field | Type | Meaning | Spec 23 DM-5 column |
|---|---|---|---|
| `child`, `composite` | ids | — | `Child`, `Composite` |
| `write_set` | list of entries or `null` | DM-7 entries; `null` when incomplete | `Write set` |
| `write_set_complete` | bool | DM-7 rule | evidence |
| `produces`, `consumes` | sorted lists of interface names | From DM-3 | `Interfaces` |
| `exclusive_resources` | sorted list or `null` | DM-5; `null` when the line is absent or invalid | evidence |
| `depends_on` | sorted list of sibling ids | Siblings reachable by a dependency path from the child | evidence |
| `disqualifiers` | sorted subset of `write-set-incomplete`, `resources-unknown`, `exclusive-resource`, `interface-unresolved` | `interface-unresolved`: an interface of `produces`/`consumes` whose `Contract` is not a resolving `INV-<n>` | `Parallel-safe` is `no` when non-empty (spec 23 REQ-09) |

DM-8 carries no yes/no parallel-safety value (REQ-07).

### DM-9 Overhead report (stdout of `overhead`, canonical JSON line)

```json
{"schema_version": 1, "kind": "decomposition_overhead",
 "subtasks": {"leaves": 3, "composites": 1},
 "sources": [{"input": "context-records", "sha256": "<hex>"}, {"input": "controller-summary", "sha256": "<hex>"}],
 "leaves": [{"id": "T-01", "composite": null, "atomic_validation": "complete",
   "attempts": {"implementer": 1, "validator": 1},
   "reviews": {"records": 2, "scopes": {"finding-led": 1, "full-leaf": 1},
               "checks_executed": 3, "checks_reused": 1},
   "packets": {"count": 2, "bytes": {"stable": 9100, "contract": 4200, "view": 800}},
   "repairs": {"episodes": 1, "attempts": {"local": 1, "escalated": 0}, "closed": 1}}],
 "composites": [{"id": "T-03", "reviews": null}],
 "unavailable": [{"subject": "T-03", "field": "reviews", "reason": "no-records"}],
 "not_reported": ["cost", "tokens", "tool_output_bytes"]}
```

| Field | Source | Rule |
|---|---|---|
| `atomic_validation` | Leaf block in `## Subtask Progress` | Raw status value; `null` when no block |
| `attempts` | `--controller-summary` (spec 13 DM-10 `checkpoint_summary`): `leaves[<id>].attempts` | `null` with reason `controller-summary-absent` without the option, `not-in-summary` when the leaf is missing |
| `reviews` | `<task>/verification/reviews/<id>/<n>.json` (spec 15 DM-1 Locations, DM-7 review record, C-6 row 18); `<id>` is the leaf id or, for a composite, the composite id (the record's `scope_key`) | `records` = count of record names (`^[1-9][0-9]*\.json$`, spec 15 DM-1; other names, including `.tmp-` names, are ignored) of all steps; `scopes` = count per `scope` value as written, a spec 15 value (`finding-led`, `full-leaf`, `full-task`, `full-integration`; leaf directories hold the first two, composite directories `full-integration`; none is renamed, merged or ranked); `checks_executed`/`checks_reused` = count of `checks[].action` values `executed` and `reused`; `null` with `no-records` when the directory is absent or has no record name, `review-record-invalid:<n>.json` when a record is not a JSON object with `kind: review_record` |
| `packets.count` | `context-packet: <role> sha256:<hex>` and `… successor sha256:<hex> …` entries in the leaf's `notes:` (spec 12 DM-11 notes entries) | `packets: null` with `no-packet-entries` when none |
| `packets.bytes` | `--context-records` (JSON lines of spec 12 DM-8 result records) matched by `digest` | Sum per part of `parts.<part>.bytes`; `null` with `context-records-absent` or `context-record-missing` when any packet digest has no record or a part is `null` |
| `repairs` | `state.md → ## Repair Episodes` (spec 17 DM-3 ledger, DM-2 identifiers; C-10 row 18) | `episodes` = lines matching `^- <id>\.E[0-9]+ \| opened \| `; `attempts.local`/`attempts.escalated` = lines matching `^- <id>\.E[0-9]+\.A[0-9]+ \| reserved \| slot (local\|escalated) \| ` (reservations, including ones later cancelled; spec 17's `slots.<slot>.used`, DM-8 and DM-11, counts only non-cancelled attempts); `closed` = lines matching `^- <id>\.E[0-9]+ \| closed \| `. With the section present, a leaf without lines has zeros, meaning "no ledger line for this leaf"; zeros do not prove the repair policy was active for that leaf. Spec 17 creates the section on its first line (DM-1 Locations), so without the section every leaf is `null` with `no-repair-ledger`, even when the policy was active and nothing was repaired. Ledger validity stays spec 17's (`ledger-invalid`); this count does not validate. Read-only use, as spec 17 C-10 row 18 requires: the helper never writes, reorders or reinterprets a line, never changes a slot or a limit, and counts nothing but the three line forms named above |
| `sources` | Every option file read | SHA-256 of its exact bytes, sorted by `input`; `[]` without options |
| `not_reported` | Constant | Always the three names shown |
| Orders | — | `leaves` and `composites` in `## Subtasks` row order; `unavailable` sorted by that order of `subject`, then `field`; `scopes` keys sorted |
| `unavailable.field` | — | One of `attempts`, `reviews`, `packets`, `packets.bytes`, `repairs` |

Composites carry only `reviews`, read from their own records exactly as for a leaf (spec 15 C-6 row 18 exposes per-leaf and per-composite records; REQ-15 there gives them `full-integration`). Fix-task rows are leaves. No ratio, total, cost or saving is
computed (G8; 05 owns valuation). Producers of the option files: `--controller-summary` is the
stdout of spec 13's `summary` subcommand (spec 13 C-2 command line, DM-10) saved by
whoever runs `overhead`; `--context-records` is the stdout lines of spec 12's
`bash scripts/context-pack.sh verify --packet <store>/<hex>.md` run once per packet digest named
in the leaves' notes (spec 12 C-1 command line), which prints a DM-8 record
with `digest` and `parts`. `overhead` is run by the owner or by a spec 10 experiment on a
captured task directory; no workflow runs it.

**Migration impact:** none. Existing plans are not rewritten; readers ignore the new sections;
the protected-sections list labelled `` **`plan.md`:** `` gains three entries (C-5).

## Contracts & Interfaces

### C-1 Command line

```
python3 -I scripts/decomposition.py verify   --task DIR
python3 -I scripts/decomposition.py overhead --task DIR [--controller-summary FILE] [--context-records FILE]
```

Standard library only, Python 3.11 or newer. `scripts/decomposition.py` is a small entry
module whose source parses under `ast.parse(source, feature_version=(3, 7))`; it checks
`sys.version_info >= (3, 11)` before anything else, then loads the engine
`scripts/decomposition_engine.py` by path with `importlib.util.spec_from_file_location` (with
`-I` the script directory is not on `sys.path`). Any exception escaping the engine exits 2 with
`internal-error: <exception class name>`. Each option at most once; unknown or repeated options
are invalid.

Required inputs (missing, unreadable or non-UTF-8 → exit 2 `input-invalid`): the `--task`
directory; its `state.md`; for `verify` with `flow: full` (or no `flow:` line), `plan.md`, a
`.ai` ancestor directory when `spec_path:` is relative, and the specification file of DM-1
item 1. Description files are not required inputs: a missing or ambiguous one is the violation
`description-unresolved`. For `overhead`, `plan.md` is required and every option file, when
given, is required.

### C-2 Exit codes

| Code | Meaning | Output |
|---|---|---|
| 0 | `verify`: pass or not-applicable; `overhead`: report printed | One DM-7 / DM-9 line |
| 1 | `verify`: at least one violation | One DM-7 line, `status: fail` |
| 2 | Invalid invocation; a required input of C-1 missing, unreadable or non-UTF-8; an internal error; an option file that is not valid JSON / JSON lines, or a summary naming a leaf absent from the plan (`summary-mismatch`) | Nothing on stdout; one stderr line `^(invalid-arguments\|input-invalid\|summary-mismatch\|internal-error): .+$` containing no file content |
| 3 | Python older than 3.11 | One stderr line `unavailable: python` |

### C-3 Check order

`verify` reads every input once, then evaluates all checks and reports every violation found;
it never stops at the first. With `flow: quick` it reads only `state.md`. When `## Coverage`
or `## Interfaces` is absent, only `section-missing` is reported for it, and no row-level check
of that table (criterion completeness, owners, tags naming its rows, interface order) runs;
tags then count as `tag-unlisted` only for a table that is present. Unreadable description files
are `description-unresolved`, not exit 2.

### C-4 Violation codes

| Code | Subject | Raised by | Responsible step |
|---|---|---|---|
| `section-missing` | Section name | REQ-27 | `/pd-decompose` |
| `table-malformed` | Section name | Data Model preamble | `/pd-decompose` |
| `criteria-absent` | `criteria` | DM-1 | `/pd-analyze` |
| `criterion-uncovered`, `criterion-unknown`, `criterion-duplicate-row` | Criterion id | REQ-16 | `/pd-decompose` |
| `withdrawal-unrecorded`, `deferral-invalid` | Criterion id | REQ-19 | `/pd-decompose` |
| `tag-missing`, `tag-unlisted` | `<subtask> <ref>` | REQ-17 | `/pd-decompose` |
| `owner-missing`, `owner-invalid` | Criterion id or `interface:<name>` | REQ-18 | `/pd-decompose` |
| `interface-party-invalid` | `interface:<name>` | DM-3 | `/pd-decompose` |
| `interface-order-missing` | `interface:<name> <consumer>` | REQ-11 | `/pd-decompose` |
| `interface-contract-pending`, `interface-contract-unknown`, `interface-question-unknown` | `interface:<name>` | REQ-09 | `/pd-design` (question: batch reconciliation) |
| `shared-file-unordered` | `<path> <id> <id>` | REQ-12 | `/pd-decompose` |
| `id-unresolved`, `depends-on-malformed`, `graph-cycle` | Id or cycle members | REQ-14 | `/pd-decompose` |
| `description-unresolved` | Subtask id | DM-4 | `/pd-decompose` |
| `resources-line-invalid` | Subtask id | REQ-20 | `/pd-decompose` |
| `boundary-row-invalid` | `B-<n>` or `### Boundary Alternatives` | REQ-03, REQ-04, DM-6 | `/pd-decompose` |
| `economics-line-invalid` | `## Decomposition Decisions` | REQ-05 | `/pd-decompose` |
| `cell-invalid` | `<section> <row key>` (row key = first cell, or `body`) | REQ-39 | `/pd-decompose` (a `Contract` cell: `/pd-design`) |
| `section-duplicate` | Section name | REQ-39 | `/pd-decompose` |

`interface-contract-pending` is `pending-design`; `interface-contract-unknown` is an `INV-<n>`
beyond the item count or with `### Invariants` absent; `interface-question-unknown` is a
`pending:Q<n>` without a batch entry. Subject formats: `graph-cycle` — the ids of one cycle
sorted and joined by one space; `shared-file-unordered` — the path then the two leaf ids sorted;
two-part subjects are joined by one space. One violation is reported per distinct (code,
subject).

### C-5 Rule, workflow and template edits

Rule text is additive; existing sentences stay unless named here.

- **`rules/workflow-reference.md`**: new section `## Coverage and Interfaces` holding DM-1–DM-5,
  the owner rules and the C-4 code table with its responsible steps, with the sentence "Discovery writes no cost, token, probability or
  duration estimate into a plan or description; the economic basis is `economics:
  structural-only`." `## Decomposition Rules` gains `### Merge and split` (merge conditions,
  split triggers, "A cheaper model or a parallelism claim never justifies a split; one coherent
  result is one leaf.") and `### Boundary Alternatives` (DM-6), and the bullets "Every ordering
  constraint between two subtasks is a `Depends On` edge, including shared target files and
  interface producer before consumer." and "Composite children integrate in listed order; that
  order is not a readiness constraint, and a child that needs another child's output has a
  `Depends On` edge." The protected-sections list labelled `` **`plan.md`:** ``
  (`rules/workflow-reference.md:346-350`; at this revision it follows `## Multi-Phase Spec Rules`
  and a `---` rather than lying inside the `## Protected Sections Contract` heading) gains `## Coverage`, `## Interfaces` and
  `## Decomposition Decisions → ### Boundary Alternatives` with the `economics:` line.
- **Rule-file names after spec 09.** This spec names no target other than spec 09's defaults
  (spec 09 DM-12 and Notes "Files and sections created after this spec"). Once spec 09 lands,
  `## Coverage and Interfaces` and the `` **`plan.md`:** `` list entries (C-5) are in
  `rules/contract-state-files.md`, and `### Merge and split`, `### Boundary Alternatives` and the
  two `## Decomposition Rules` bullets are in `rules/protocol-subtask-classifier.md`; every
  citation `workflow-reference → ## Coverage and Interfaces` becomes
  `contract-state-files → ## Coverage and Interfaces`, and `## Decomposition Rules` citations
  become `protocol-subtask-classifier → ## Decomposition Rules`. Before spec 09 lands all of
  them are in `rules/workflow-reference.md`. Every delivery step and every check of this spec
  that names `rules/workflow-reference.md` (REQ-31, AC-03, AC-04, AC-05, AC-16, AC-23, C-7, and
  every other mention in this spec) resolves each heading separately through whichever file
  holds it, so different clauses may resolve to different files, and fails only when none holds
  it; the heading text is identical in both layouts. A clause that says a string occurs "in no
  other file" (AC-23, `no-intermediate-gate`) is read as "in no file outside the resolved rule
  files". Under spec 11, each of the edited
  workflows that cites `## Coverage and Interfaces` as a load (`pd-decompose`, `pd-finalize`)
  lists the resolved file in its `loads:` declaration in spec 11's grammar (DM-1: `mandatory`
  entry with `path: rules/<stem>.md` and `sections: ["## Coverage and Interfaces"]`), and the
  successor file stays within spec 11 REQ-01's 700-word limit (an overflow stops the
  implementer, spec 11 A-38); this spec adds no other requirement for spec 11.
- **`workflows/pd-analyze.md`** step 3 (autonomous): "Label each derived acceptance criterion
  `DC-<n>` in its assumption line."
- **`workflows/pd-decompose.md`**: step 1 also loads `workflow-reference → ## Coverage and
  Interfaces` and reads only the specification's in-scope Acceptance Criteria sections (DM-1);
  the description template's Context gains `- Exclusive resources: <names | none>`; step 4
  requires covers tags; step 5 writes `## Coverage`, `## Interfaces` (contracts
  `pending-design`), `### Boundary Alternatives` and the `economics:` line, and replaces
  "Describe any shared-file constraints." with "Express every shared-file or interface order as
  a `Depends On` edge (`workflow-reference → ## Coverage and Interfaces`)."; step 5's
  preservation paragraph adds REQ-24's text verbatim ("leave unchanged every `## Coverage` and
  `## Interfaces` row that names a started subtask in any cell, and the covers tags of every
  started subtask; report a reconciliation blocker if a change to them is required. A subtask is
  started when its `## Subtasks` `Status` is not `not-started` or any status field of its block in
  `## Subtask Progress` is not `not-started`."); step 8 verifies the new sections.
- **`workflows/pd-design.md`** step 3: "Record each interface of `plan.md → ## Interfaces` as one
  `### Invariants` item stating its agreed shape, and write its `INV-<n>` into the `Contract`
  cell; an interface whose shape depends on a class-B question gets `pending:Q<n>`, and
  `## Open Questions (batch)` gets a `- Q<n>:` entry for it when none exists." Step 3 also: "When
  a `## Coverage` row has owner `task`, keep its criterion id verbatim in one item of
  `### Acceptance Criteria`." Step 4 adds: "`/pd-design` edits no covers tag or exclusive-resources line itself;
  when the design needs other coverage it reruns `/pd-decompose` as already required, which
  rewrites tags under REQ-24 and makes model selection rerun", and "leave unchanged every
  `## Coverage` and `## Interfaces` row that names a started subtask in any cell; report a
  reconciliation blocker if a change to them is required" — so tag changes always precede
  reselection (`workflows/pd-design.md:64-76`). Spec 23 REQ-52 separately has `/pd-design`
  re-render the `### Parallel Safety` rows from the current DM-8 after design; that edit is
  spec 23's, touches no `## Coverage` or `## Interfaces` row, and leaves rows of started
  children unchanged under this spec's REQ-24 definition, so the two edits to the same step
  do not conflict.
- **`workflows/pd-finalize.md`** step 3 adds, after the task-validator block:

  ```bash
  if [ -n "${ORCHESTRAIL_HOME:-}" ] && [ -f "$ORCHESTRAIL_HOME/scripts/decomposition.py" ] && command -v python3 >/dev/null 2>&1; then
    python3 -I "$ORCHESTRAIL_HOME/scripts/decomposition.py" verify --task <task-directory>
  fi
  ```

  "Exit 0 → continue. Exit 1 or 2 → **stop**: report each violation and its responsible step
  from `workflow-reference → ## Coverage and Interfaces`; do not edit recorded progress. Exit 3,
  missing configuration or missing helper → report once and apply the same rules manually."
- **`workflows/spec-run.md`** batch gate (`:107-111`): "When an answer resolves a question named
  by a `pending:Q<n>` contract, add one `### Invariants` item recording the answered shape and
  replace the cell with its `INV-<n>`. After reconciling, run the decomposition verifier as
  `/pd-finalize` does: exit 1 or 2 → **stop** before any branch and report the violations; exit
  3 or helper unavailable → apply the same rules manually."
- **`templates/subtask-description.md`**: Context gains the DM-5 line; Acceptance Criteria gains
  the covers-tag format.
- **Preserved anchors** (frozen checks). REQ-36 keeps every existing line, which keeps every
  frozen check reading these files passing, including those on `workflows/pd-analyze.md`
  (`scripts/validate-contracts.sh:601`, `:655-659`, `:1069`), `workflows/spec-run.md`
  (`:964-1081`, including the flattened "Then **stop and wait**", `:1506-1517`, `:1887`),
  `templates/subtask-description.md` (`:929-930`, `:1242-1247`) and `workflows/pd-finalize.md`
  (`:923-927`, `:1267-1268`). The replaced pd-decompose sentence is read by no frozen check
  (no match for "Describe any" in `scripts/validate-contracts.sh` or `tests/`). Anchors
  specifically near the edited steps: in `workflows/pd-decompose.md` — `decomposition:
  complete`; ``Initialise `## Subtask Progress` ``; the `[composite] T-XX | <name> | rollup:
  not-started | integration-validation: not-started` line; `children: T-XXa`; the Upsert
  paragraph with "Never write a duplicate block", "Never reset a block whose" and "beyond
  `not-started`" before the word "tripwire"; S1–S5; "depth-2"; "When Type 3 re-slicing is
  selected" with "producer" within 20 lines; the line "`## Execution Strategy` states the
  ordering policy: Type 3 runs producer before consumer"; "base = min(AA, BB)"; "collision";
  "upward by 1"; "until the complete numeric range is free"; no "downward"
  (`scripts/validate-contracts.sh:604`, `:728-822`). In `workflows/pd-design.md` —
  `## Solution Design` (`:607`). In `workflows/pd-finalize.md` — `type: composite` (`:774-775`).
  In `rules/workflow-reference.md` — "Autonomous Subtask Classifier" and "Decomposition
  Decisions" (`:759-760`, `:780-781`). Every new `file → ## Section` citation must resolve
  (`tests/workflow-instructions.py:20-35`).

### C-6 Contracts with other specs

| Spec | Relationship |
|---|---|
| 05 (completed) | Consumed: none at run time. Per-leaf money stays in 05's `analyze` report (`scripts/usage-telemetry.py:441-444` `analyze` command; `top_leaves`/`partial_leaves` built in `scripts/usage_telemetry_report.py:712-714`); cost per accepted result stays 05's (completed spec 05 REQ-13 and its section on the cost of an independently accepted result). Exposed: none; DM-9 is not a 05 object |
| 10 | Consumed: comparison manifests, `report.json` verdicts and the hypothetical calculator (spec 10 DM-12 Report, DM-13 Calculator input and output, `Promotion rule (REQ-12)`). A decomposition-policy comparison is a 10 manifest whose variants differ only in decomposition instructions, recorded in `strategy_details` (DM-6 variants); this spec defines no `switches` entry (A-14; 10 `Variant switches`, REQ-52). Another decomposition policy is adopted only after a `promote` verdict and then by a separate owner decision and spec (10 Out of Scope: adopting a promoted variant is a separate owner decision and spec; 10 `Promotion rule (REQ-12)`: the verdict is advisory and changes no default). Exposed: DM-9 may be attached to an attempt's evidence as a diagnostic |
| 23 | Exposed: DM-8 per composite child, mapped field by field onto spec 23 DM-5 (`child`, `composite` → `Child`, `Composite`; `write_set` → `Write set`; `produces`, `consumes` → `Interfaces`; `write_set_complete`, `exclusive_resources`, `depends_on`, `disqualifiers` → `Independence evidence`, with `disqualifiers` non-empty forcing `Parallel-safe: no`); DM-3 interface names; the REQ-13 and REQ-35 rule that all ordering is in `Depends On`; REQ-24's definition of a started subtask, which spec 23 REQ-52 reuses when `/pd-design` re-renders `### Parallel Safety` rows and leaves rows of started children unchanged (this spec edits no such row). 23 owns rendering `### Parallel Safety`, `Parallel-safe` and the REQ-05 predicate. REQ-07 keeps its meaning (sequential top-level stack), as spec 23 A-01 cites |
| 09 | Consumed: rename maps; DM-9 amendment mechanism is not needed because no frozen check changes (REQ-30) |
| 12 | Consumed (spec 12 C-8 row 18): the stable block plus Solution Design items and design-basis status are the shared architectural contract; REQ-02 places interface agreements there as `INV-<n>`, so every packet's Task Contract (DM-5 items 1 and 5) already carries the leaf's covers tags and the referenced invariant; a `design-basis-status: changed` is handled by 12's worker rule (12 C-6, `## Design basis` text). Spec 12 DM-8 `parts.<part>.bytes` (DM-4 `parts`) feed DM-9 `packets.bytes`. No change to 12 |
| 13 | Consumed (spec 13 C-10 row 18): `summary` DM-10 per-leaf attempt counts → DM-9 `attempts`. Event counts are not used |
| 15 | Consumed (spec 15 C-6 row 18): per-leaf and per-composite DM-7 records at `reviews/<id>/<n>.json` (DM-1 record names) → DM-9 `reviews` for leaves and composites alike, with `scope` values `finding-led`, `full-leaf`, `full-task`, `full-integration` and `checks[].action` values `executed`, `reused`; C-3 parsing rules and DM-2 `INV-<n>` numbering. Nothing is written to 15's records or locations |
| 14 | Consumed: none; output bytes reach evidence only through a 05 adapter (spec 14 C-7 row 05); `tool_output_bytes` is listed in `not_reported` |
| 16 | Exposed: nothing new. The complexity input `{quality_floor, hard_constraints}` stays produced by `/pd-select-model` DM-4 (spec 16 DM-4 `effort-input:` line, C-6 row 18; 16's C-6 row 18 records the same: 18 REQ-29 produces no complexity value); boundary codes are not complexity |
| 17 | Consumed (spec 17 C-10 row 18): per-leaf `## Repair Episodes` ledger lines → DM-9 `repairs` counts, read-only; 18 never changes slots or validates the ledger |

### C-7 Acceptance suite

`python3 -I scripts/check-decomposition.py` is a standard-library Python 3.11+ `unittest`
program holding every fixture case of `## Acceptance Criteria`. It builds fixture task
directories under `tempfile.TemporaryDirectory()`, runs the helper as a subprocess with
`python3 -I`, compares stdout JSON and exit codes, checks repository text contracts by reading
files of the source checkout (resolving rule headings as C-5 "Rule-file names after spec 09"
states), and exits 0 only when every case passes. It is never called by
`scripts/validate-contracts.sh`, `scripts/sync.sh` or CI defaults. Fixture **F0**: a spec with
items `AC-01`–`AC-03`; `state.md` with `spec_path:`, `flow: full`, `## Phases`,
`## Task Analysis → ### Assumptions`, `## Solution Design → ### Acceptance Criteria` (three
items beginning `AC-01`, `AC-02`, `AC-03`), `## Solution Design → ### Invariants` (two items) and
`## Subtask Progress` with leaf blocks T-01, T-02, T-03a, T-03b and a composite block T-03
(`children: T-03a, T-03b`); `plan.md` with `## Subtasks` (T-02 depends T-01; T-03, T-03a and
T-03b each depend T-02), `## Coverage` (AC-01 → T-01, owner `—`; AC-02 → T-03a, T-03b, owner
T-03; AC-03 → T-02, owner `—`), `## Interfaces` (`token-schema`, producer T-01, consumers T-02,
T-03a, contract `INV-2`, owner T-03a), `### Boundary Alternatives` with B-1 (chosen merge, five
codes) and the `economics:` line; descriptions whose covers tags match exactly these rows (T-03's
composite criteria carry `(covers: AC-02)`; T-01, T-02 and T-03a carry
`interface:token-schema`), explicit target files with no path shared by two leaves, and
`- Exclusive resources: none` in every leaf. The fixture places the specification and the task
under one temporary root as `<root>/.ai/specs/…` and `<root>/.ai/tasks/todo/task-f0/`.

### C-8 Files created or changed

Created: `scripts/decomposition.py` (entry), `scripts/decomposition_engine.py`,
`scripts/check-decomposition.py`, one ADR. Changed:
`rules/workflow-reference.md`, `workflows/pd-analyze.md`, `workflows/pd-decompose.md`,
`workflows/pd-design.md`, `workflows/pd-finalize.md`, `workflows/spec-run.md`,
`templates/subtask-description.md`, `.ai/principles/domain.md`, `.ai/adr/index.md`,
`.ai/memory/architecture.md`, `docs/USAGE.md`, `scripts/README.md`.

## Non-Functional Requirements

| ID | Attribute | Target | Verification |
|---|---|---|---|
| NFR-01 | Offline, no models | The entry and engine import only standard-library modules and none of `subprocess`, `socket`, `urllib`, `http`, `ssl`, `multiprocessing`; the suite may import `subprocess` to run the helper | AC-05 (source scan) |
| NFR-02 | Read-only | The helper changes no byte, mode or mtime of any file in the fixture tree | AC-15 |
| NFR-03 | Determinism | Two runs on the same inputs print identical bytes | AC-15 |
| NFR-04 | Privacy | Stderr lines contain no input file content; DM-9 contains no notes text other than digests and counts | AC-15, AC-17 |
| NFR-05 | Performance | N/A — no runtime target is set: none is measured, and ADR-0020 treats time limits as watchdogs, not budgets | — |
| NFR-06 | Gates G1–G8 | G1: DM-9 `sources` digests; G2/G8: no cost or saving claim (REQ-05, `not_reported`), comparison only via 10 (REQ-08); G3: coverage never drops and no review step is removed (REQ-16–REQ-18, C-5 adds no skip); G4: legacy plans readable (REQ-27), unknown is `null` (REQ-26); G5: helper read-only, workflows remain writers (NFR-02, P4); G6: suite RED first, no paid run (C-7, REQ-08); G7: rollback in Notes; G8: no production cap | AC-03, AC-05, AC-17–AC-19 |

## Edge Cases & Failure Modes

| ID | Case | Expected behaviour | REQ |
|---|---|---|---|
| E-01 | Spec has no `## Acceptance Criteria`, pd-analyze derived `DC-1`, `DC-2` | Criteria `derived`; rows for DC ids required | REQ-15 |
| E-02 | No criteria and no DC ids | `criteria-absent`; finalization stops, responsible `/pd-analyze` | REQ-15, REQ-23 |
| E-03 | Some spec items have `AC-` ids, others not | Ordinals `SPEC-<n>` for all | REQ-15 |
| E-04 | Duplicate `AC-` ids | Ordinals, `notes` contains `duplicate-ids` | REQ-15 |
| E-05 | `Acceptance Criteria` heading inside a fenced block | Ignored | REQ-15 |
| E-06 | Multi-phase spec, preamble and phase 2 both have criteria, `active_phase: 2` | Both sets in scope; a preamble criterion that belongs to a later phase may be `deferred — phase <K>`; criteria of other phase sections are out of scope and a row for one is `criterion-unknown` | REQ-15, REQ-19 |
| E-07 | Criterion withdrawn by a Description Amendment | `withdrawn — amendment` with id in the amendments section | REQ-19 |
| E-08 | One criterion verified by two top-level leaves, neither depends on the other | Owner must be `task` or a third subtask satisfying O-3; else `owner-invalid` | REQ-18 |
| E-09 | Criterion verified only by a composite | Owner must be that composite (O-2, O-3a) | REQ-18 |
| E-10 | Interface consumer earlier than producer in the graph | `interface-order-missing` | REQ-11 |
| E-11 | Two leaves share `docs/USAGE.md` with no dependency path | `shared-file-unordered` | REQ-12 |
| E-12 | Two leaves share a path but in different repositories (Type 3 `working_dir`) | No violation | REQ-12 |
| E-13 | Target files contain a directory or glob | Write set incomplete; no overlap check for that leaf; DM-8 `write-set-incomplete` | REQ-12, REQ-21 |
| E-14 | Cycle T-02 → T-03 → T-02 | `graph-cycle` naming both | REQ-14 |
| E-15 | `Depends On` cell "T-01 (schema)" | `depends-on-malformed` | REQ-14 |
| E-16 | Description directory missing or two match | `description-unresolved` | REQ-17 |
| E-17 | Interface contract still `pending-design` at finalization | `interface-contract-pending`; stop, responsible `/pd-design` | REQ-09 |
| E-18 | `pending:Q3` under `/spec-run` with batch entry Q3 | Pass at `/pd-finalize`; after the gate clears the batch, the recheck reports `interface-question-unknown` unless reconciled | REQ-09, REQ-10 |
| E-19 | A chosen split with codes `cheaper-model` | `boundary-row-invalid` | REQ-04 |
| E-20 | No alternative was considered | `None — <reason>` passes; empty reason fails | REQ-06 |
| E-21 | Plan written before this delivery | Execution/Validation unaffected; `verify` reports `section-missing` | REQ-27 |
| E-22 | `flow: quick` | `not-applicable`, exit 0 | REQ-28 |
| E-23 | Rerun of decomposition after T-01 started | T-01 cells and tags unchanged; required change is a reconciliation blocker | REQ-24 |
| E-24 | Overhead without options and without `verification/` | All `attempts`, `reviews`, `packets.bytes` null with reasons | REQ-26 |
| E-25 | Controller summary lists `T-09` absent from the plan | Exit 2 `summary-mismatch` | REQ-25 |
| E-26 | A review record is malformed | That leaf's `reviews` null, `review-record-invalid:<n>.json` | REQ-26 |
| E-27 | Non-UTF-8 `plan.md` | Exit 2 `input-invalid` | REQ-22 |
| E-28 | Concurrent writer edits `plan.md` while `verify` reads | Not guarded; Discovery has one sequential writer (P4); each file is read once | REQ-22 |
| E-29 | Fix-task rows present (after Validation) | Treated as leaves; no row requires them in Coverage | REQ-16 |
| E-30 | Python 3.10 | Exit 3; `/pd-finalize` applies manual checks | REQ-23 |
| E-33 | `Acceptance criteria` heading in lower case or numbered | Matched (case-insensitive, optional `<digits>. `) | REQ-15 |
| E-34 | Acceptance Criteria section holds a table or paragraph only | One criterion with ordinal id, `notes` contains `unstructured` | REQ-15 |
| E-35 | Batch answer resolves `pending:Q2` | Orchestrator adds the Invariants item and `INV-<n>`, then reruns `verify` | REQ-40, REQ-10 |
| E-36 | Started subtask shares a Coverage row with an unstarted one and a rerun wants to drop the unstarted one | Row frozen; reconciliation blocker | REQ-24 |
| E-37 | Unexpected exception in the engine | Exit 2 `internal-error: <class>`; `/pd-finalize` stops | REQ-22, REQ-23 |
| E-38 | `## Repair Episodes` present, leaf has no lines | `repairs` zeros | REQ-26 |
| E-31 | `spec_path:` names a missing file | Exit 2 `input-invalid`; `/pd-finalize` stops (exit 2) | REQ-22, REQ-23 |
| E-32 | Legacy task without `spec_path:` and without `description.md` | Exit 2 `input-invalid` | REQ-22 |

## Acceptance Criteria

All fixture cases run in `scripts/check-decomposition.py` (C-7); "violation X" means exit 1
with a DM-7 `violations` entry whose `code` is X and whose `subject` is as stated.

- [ ] **AC-01** (REQ-01, REQ-15, REQ-16, REQ-22) — Given F0, when `verify` runs, then it exits 0
  with `status: pass`, `criteria.source: spec-ids`, `criteria.ids: ["AC-01","AC-02","AC-03"]`
  and `violations: []`; given F0 without the AC-02 row, a row `AC-09`, or a second AC-01 row,
  then violations `criterion-uncovered` (`AC-02`), `criterion-unknown` (`AC-09`) and
  `criterion-duplicate-row` (`AC-01`) respectively.
- [ ] **AC-02** (REQ-03, REQ-04, REQ-06) — Given F0 variants where B-1 (chosen merge) lacks
  `compatible-risk`; a chosen split with codes `uncertainty`; a chosen split with code
  `cheaper-model`; a rejected merge with no codes; the section body `None — single module`; the
  body `None —`; when `verify` runs, then results are violation `boundary-row-invalid` (`B-1`),
  pass, violation, violation, pass and violation (`### Boundary Alternatives`) respectively.
- [ ] **AC-03** (REQ-05, REQ-33) — Given F0 without the `economics:` line, with
  `economics: calibrated`, with the line twice, and with the line placed after the classifier
  table, then each yields violation `economics-line-invalid`; and `rules/workflow-reference.md → ## Coverage and Interfaces`
  contains the sentence "Discovery writes no cost, token, probability or duration estimate into
  a plan or description; the economic basis is `economics: structural-only`."
- [ ] **AC-04** (REQ-07, REQ-13, REQ-34, REQ-35) — Given F0, then no key named `parallel_safe` or
  `Parallel-safe` occurs anywhere in the DM-7 output; `rules/workflow-reference.md →
  ## Autonomous Subtask Classifier` is byte-identical to the base revision (`<base>` as in AC-20;
  this clause is checked at Validation, not by the suite); `workflows/spec-run.md` still contains
  "Never start N+1 before N is `reviewed`" and `workflows/pd-decompose.md` still contains "Do not
  claim unsupported parallel execution"; `workflows/pd-decompose.md` no longer contains "Describe
  any shared-file constraints." and contains the C-5 replacement sentence;
  `rules/workflow-reference.md → ## Decomposition Rules` contains the C-5 `Depends On` bullet and
  the sentence "Composite children integrate in listed order; that order is not a readiness
  constraint, and a child that needs another child's output has a `Depends On` edge."
- [ ] **AC-05** (REQ-08) — Given the delivered tree, then neither `scripts/decomposition.py` nor
  `scripts/decomposition_engine.py` imports (by `ast` scan of `import` and `from` statements) a
  module outside `sys.stdlib_module_names` or any of `subprocess`, `socket`, `urllib`, `http`,
  `ssl`, `multiprocessing`; neither `scripts/validate-contracts.sh` nor `scripts/sync.sh` contains the string
  `decomposition.py`; and `rules/workflow-reference.md → ## Decomposition Rules → ### Merge and
  split` contains "A cheaper model or a parallelism claim never justifies a split; one coherent
  result is one leaf."
- [ ] **AC-06** (REQ-18) — Given F0 variants: AC-02 owner `—`; AC-02 owner `T-01`; AC-02 owner
  `task` with T-03's `AC-02` tag removed; AC-03 listing T-02 and T-01 with owner T-02 (T-01's criteria also tagged `AC-03`);
  AC-02 listing only composite T-03 with owner `—`; the interface owner `T-02` (no dependency
  path from T-02 to T-03a); the interface owner `T-03`; then results are `owner-missing`
  (`AC-02`), `owner-invalid` (`AC-02`), pass, pass, `owner-missing` (`AC-02`), `owner-invalid`
  (`interface:token-schema`) and `owner-invalid` (`interface:token-schema`) respectively.
- [ ] **AC-07** (REQ-17) — Given F0 with the `AC-02` reference removed from T-03a's tag, F0 with
  `(covers: AC-01)` added to a criterion of T-02, and F0 unchanged (T-03 tagged `AC-02` as owner
  only), then the results are violation `tag-missing` (`T-03a AC-02`), violation `tag-unlisted`
  (`T-02 AC-01`) and pass respectively.
- [ ] **AC-08** (REQ-02, REQ-09, REQ-10, REQ-11, REQ-40, REQ-41) — Given F0 variants with contract
  `pending-design`; `INV-3`; `pending:Q1` without a batch section; `pending:Q1` with
  `## Open Questions (batch)` containing `- Q1: …`; T-02 not depending on T-01; Consumers
  `T-01, T-03a` (equal to the producer); then results are `interface-contract-pending`, `interface-contract-unknown`,
  `interface-question-unknown`, pass, `interface-order-missing` (`interface:token-schema T-02`)
  and `interface-party-invalid`; and `workflows/pd-design.md` contains the C-5 step 3 sentences
  (including "gets a `- Q<n>:` entry for it when none exists") and `workflows/spec-run.md`
  contains the C-5 batch-gate sentences (including "replace the cell with its `INV-<n>`" and
  "exit 1 or 2 → **stop** before any branch").
- [ ] **AC-09** (REQ-12) — Given F0 where T-03a and T-03b both list `src/app.py` (same
  repository, no dependency path between them), then violation `shared-file-unordered`
  (`src/app.py T-03a T-03b`); with T-03b depending on T-03a, pass; with T-03b's `working_dir:`
  naming another repository, pass; with T-03b listing `src/` instead of `src/app.py`, pass and
  its `write_sets` entry has `complete: false`, `entries: null`; and with T-01 and T-02 both
  listing `docs/USAGE.md`, pass (T-02 depends T-01).
- [ ] **AC-10** (REQ-14) — Given F0 variants with `Depends On` `T-07`, `T-01 (schema)`, and
  T-02 ⇄ T-03 cycle, then violations `id-unresolved` (`T-07`), `depends-on-malformed` (`T-02`)
  and `graph-cycle` whose subject names T-02 and T-03.
- [ ] **AC-11** (REQ-19) — Given F0 with AC-03 `withdrawn — amendment` (T-02's `AC-03` tag
  removed) and no amendments section, then `withdrawal-unrecorded` (`AC-03`); with
  `### Description Amendments` mentioning AC-03, pass; given a multi-phase F0 whose spec has
  AC-01–AC-03 in the preamble's `## Acceptance Criteria`, a `## Phase 1` and a `## Phase 2`
  section without criteria, `state.md` lines `active_phase: 1` and `## Spec Phases` with
  `- phase 1: in-discovery — Core — <dir>` and `- phase 2: deferred — Later — —`, and AC-03
  `deferred — phase 2` (tag removed), pass; with `deferred — phase 3`, `deferral-invalid`
  (`AC-03`); with `deferred — phase 1`, `deferral-invalid` (`AC-03`).
- [ ] **AC-12** (REQ-15) — Given spec variants: items without ids (three items); mixed ids;
  duplicate `AC-01`; an `Acceptance Criteria` heading only inside a fenced block with
  Assumptions containing `DC-1` and `DC-2`; no criteria and no DC ids; a multi-phase spec with
  criteria in phases 1 and 2 and `active_phase: 2`; a heading `## 12. Acceptance criteria`
  with items `AC-01`, `AC-02`; a heading `## Acceptance Criteria` whose body is one paragraph;
  then `criteria` is `spec-ordinals` `["SPEC-1","SPEC-2","SPEC-3"]`; `spec-ordinals`;
  `spec-ordinals` with `notes: ["duplicate-ids"]`; `derived` `["DC-1","DC-2"]`; `none` with violation
  `criteria-absent`; scope `phase 2` with only preamble and phase-2 items; `spec-ids`
  `["AC-01","AC-02"]`; and `spec-ordinals` `["SPEC-1"]` with `notes: ["unstructured"]`; every
  other case has `notes: []`.
- [ ] **AC-13** (REQ-20) — Given F0 with T-02's resources line removed, duplicated, or
  `- Exclusive resources: none, port 8080`, then `resources-line-invalid` (`T-02`) each time; with
  `- Exclusive resources: port 8080`, pass.
- [ ] **AC-14** (REQ-21) — Given F0 with T-03b's resources `port 8080` and T-03a's target files
  containing `src/`, then `parallel_evidence` has two objects in plan order: T-03a with
  `write_set: null`, `write_set_complete: false`, `produces: []`, `consumes: ["token-schema"]`,
  `depends_on: []`, `disqualifiers: ["write-set-incomplete"]`; T-03b with `depends_on: []`,
  `exclusive_resources: ["port 8080"]`, `disqualifiers: ["exclusive-resource"]`; with T-03b
  depending on T-03a, T-03b's `depends_on` is `["T-03a"]`; with T-03b's resources line removed,
  its `exclusive_resources` is `null` and its disqualifiers contain `resources-unknown`; with
  contract `pending-design`, T-03a's disqualifiers also contain `interface-unresolved`.
- [ ] **AC-15** (REQ-22, NFR-02–NFR-04) — Given F0, two `verify` runs print identical bytes and
  leave every fixture file's bytes, mode and mtime unchanged; an unknown option, a repeated
  `--task`, a missing `plan.md` and a non-UTF-8 `plan.md` each exit 2 with empty stdout and one
  stderr line matching C-2 that contains no fixture text; `ast.parse` of
  `scripts/decomposition.py` with `feature_version=(3, 7)` succeeds; running the entry
  in-process with `sys.version_info` patched to `(3, 10, 0)` exits 3 with `unavailable: python`
  before the engine is loaded; and an engine replaced (in a temporary copy) by one raising
  `RuntimeError` exits 2 with `internal-error: RuntimeError`.
- [ ] **AC-16** (REQ-23) — Given the delivered `workflows/pd-finalize.md`, then step 3 contains the
  C-5 command block and the sentences "Exit 1 or 2 → **stop**", "do not edit recorded progress"
  and "apply the same rules manually"; and every row of C-4 appears in `rules/workflow-reference.md → ## Coverage and
  Interfaces` with its responsible step.
- [ ] **AC-17** (REQ-25, REQ-26) — Given F0 after execution with a DM-10 summary file
  (T-01 attempts 1/1), `verification/reviews/T-01/1.json` (a valid `review_record` object, `scope: full-leaf`, two
  checks `executed`) and `2.json` (likewise valid, `scope: finding-led`, one `executed`, one `reused`), T-01 notes with two
  `context-packet:` entries, a records file with both digests, and `## Repair Episodes` holding
  `- T-01.E1 | opened | …`, `- T-01.E1.A1 | reserved | slot local | …` and
  `- T-01.E1 | closed | …` lines, when `overhead` runs with both options, then T-01 shows
  `attempts {"implementer":1,"validator":1}`, `reviews {"records":2,
  "scopes":{"finding-led":1,"full-leaf":1},"checks_executed":3,"checks_reused":1}`, `packets.count`
  2 with per-part byte sums equal to the records, `repairs {"episodes":1,"attempts":{"local":1,
  "escalated":0},"closed":1}`, T-02 shows `repairs` with all zeros, `sources` lists both files
  with their SHA-256 sorted by `input`, and `not_reported` is
  `["cost","tokens","tool_output_bytes"]`.
- [ ] **AC-18** (REQ-26) — Given the same task without options, without `verification/`, with
  no `context-packet:` entries and without `## Repair Episodes`, then every leaf has `attempts`,
  `reviews`, `packets` and `repairs` `null`, `unavailable` holds one entry per leaf and field
  with reasons `controller-summary-absent`, `no-records`, `no-packet-entries` and
  `no-repair-ledger`, `sources` is `[]`, and no count in the output is `0`; given a records file
  missing one digest, `packets.bytes` is `null` with `context-record-missing`; given a summary
  naming `T-09`, exit 2 `summary-mismatch`.
- [ ] **AC-19** (REQ-27) — Given a copy of `.ai/tasks/completed/task-06-harness-git-rails/`
  and of its specification `.ai/specs/completed/06-harness-git-rails.md` under one temporary
  root with the same relative layout (plan without the new sections), `verify` exits 1 and its
  violations include `section-missing` for `## Coverage`, `## Interfaces` and
  `### Boundary Alternatives` and `economics-line-invalid`, and include no
  `criterion-uncovered`; and no file under `workflows/` other than `pd-analyze.md`,
  `pd-decompose.md`, `pd-design.md`, `pd-finalize.md` and `spec-run.md` names `## Coverage` or
  `## Interfaces`.
- [ ] **AC-20** (REQ-28) — Given a task with `flow: quick` and no `plan.md`, `verify` exits 0 with
  `status: not-applicable` and `violations: []`; and `rules/quick-flow.md` is unchanged by the
  delivery (`git diff <base> -- rules/quick-flow.md` empty, where `<base>` is
  `git merge-base HEAD main` of the delivery branch; this part is checked at Validation, not by
  the suite).
- [ ] **AC-21** (REQ-29) — Given the delivered tree, then `workflows/pd-decompose.md`,
  `workflows/pd-design.md`, `scripts/decomposition.py` and `scripts/decomposition_engine.py`
  contain neither `effort-input` nor
  `quality_floor`, and no DM-7 or DM-9 key contains `complexity`.
- [ ] **AC-22** (REQ-30, REQ-36) — Given the delivered branch (`<base>` as in AC-20, checked at
  Validation), then `git diff <base> -- scripts/validate-contracts.sh scripts/validate-task.sh
  scripts/sync.sh tests/` is empty, `git diff <base> --` of each file edited under C-5 shows no
  removed line except the replaced pd-decompose sentence, every preserved anchor of C-5 is
  present, `python3 tests/workflow-instructions.py` exits 0, and
  `bash scripts/validate-contracts.sh` exits 0.
- [ ] **AC-23** (REQ-31, REQ-01, REQ-06, REQ-20) — Given the delivered rule and workflows, then
  `rules/workflow-reference.md` has exactly one heading `## Coverage and Interfaces` and the
  subsections `### Merge and split` and `### Boundary Alternatives` under
  `## Decomposition Rules`; its protected-sections list labelled `` **`plan.md`:** `` (wherever that
  label stands, C-5) lists `## Coverage`, `## Interfaces` and `### Boundary Alternatives`; `workflows/pd-decompose.md` cites
  `` `workflow-reference → ## Coverage and Interfaces` `` and its template contains
  `- Exclusive resources:`; `workflows/pd-analyze.md` contains "Label each derived acceptance
  criterion `DC-<n>`"; `templates/subtask-description.md` contains `Exclusive resources:` and
  `(covers:`; and the string `no-intermediate-gate` occurs in `rules/workflow-reference.md` and
  in no file under `rules/` or `workflows/` outside the resolved rule files.
- [ ] **AC-24** (REQ-24) — Given the delivered workflows, then `workflows/pd-decompose.md` step 5
  contains "leave unchanged every `## Coverage` and `## Interfaces` row that names a started
  subtask in any cell, and the covers tags of every started subtask", the sentence defining
  started ("A subtask is started when its `## Subtasks` `Status` is not `not-started` or any
  status field of its block in `## Subtask Progress` is not `not-started`.") and
  "reconciliation blocker"; and `workflows/pd-design.md` step 4 contains "leave unchanged every
  `## Coverage` and `## Interfaces` row that names a started subtask in any cell" and
  "reconciliation blocker".
- [ ] **AC-25** (REQ-32, REQ-37, REQ-38) — Given the delivered tree, then
  `.ai/principles/domain.md` has vocabulary rows (lines starting `| **<term>** |`) for Spec
  criterion, Coverage, Covers tag, Integration owner, Interface contract and Boundary
  alternative; `.ai/adr/index.md` has a row with status `Accepted` whose title contains
  "decomposition"; `.ai/memory/architecture.md` and `scripts/README.md` contain
  `scripts/decomposition.py`; and `docs/USAGE.md` contains `decomposition.py overhead`,
  `--controller-summary` and `--context-records`.
- [ ] **AC-26** (REQ-39, REQ-18) — Given F0 variants: an `## Interfaces` name `Token_Schema`;
  two rows named `token-schema`; `Contract` `TBD`; a `## Coverage` `Subtasks` cell `T-01 and
  T-02`; owner `T-01` on a withdrawn row; a second `## Coverage` heading; a `## Coverage` header
  `| Criterion | Leaves | Owner |`; owner `task` for AC-01 with the `AC-01` item removed from
  the Solution Design criteria; owner `task` for AC-01 with F0's Solution Design criteria; then results are `cell-invalid` (`## Interfaces Token_Schema`),
  `cell-invalid`, `cell-invalid`, `cell-invalid`, `cell-invalid`, `section-duplicate`
  (`## Coverage`), `table-malformed` (`## Coverage`), `owner-invalid` (`AC-01`) and pass
  respectively.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-23 |
| REQ-02 | AC-08 |
| REQ-03 | AC-02 |
| REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06 | AC-02, AC-23 |
| REQ-07 | AC-04 |
| REQ-08 | AC-05 |
| REQ-09 | AC-08 |
| REQ-10 | AC-08 |
| REQ-11 | AC-08 |
| REQ-12 | AC-09 |
| REQ-13 | AC-04 |
| REQ-14 | AC-10 |
| REQ-15 | AC-01, AC-12 |
| REQ-16 | AC-01 |
| REQ-17 | AC-07 |
| REQ-18 | AC-06, AC-26 |
| REQ-19 | AC-11 |
| REQ-20 | AC-13, AC-23 |
| REQ-21 | AC-14 |
| REQ-22 | AC-01, AC-15 |
| REQ-23 | AC-16 |
| REQ-24 | AC-24 |
| REQ-25 | AC-17 |
| REQ-26 | AC-17, AC-18 |
| REQ-27 | AC-19 |
| REQ-28 | AC-20 |
| REQ-29 | AC-21 |
| REQ-30 | AC-22 |
| REQ-31 | AC-23 |
| REQ-32 | AC-25 |
| REQ-33 | AC-03 |
| REQ-34 | AC-04 |
| REQ-35 | AC-04 |
| REQ-36 | AC-22 |
| REQ-37 | AC-25 |
| REQ-38 | AC-25 |
| REQ-39 | AC-26 |
| REQ-40 | AC-08 |
| REQ-41 | AC-08 |

Every AC names at least one REQ above; AC-01–AC-26 all appear.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| New tables add Discovery output and packet bytes, against the token-saving goal | Medium | Medium | Compact tables; descriptions grow only by tags and one line; spec 12 bytes and DM-9 make the cost visible; no saving is claimed |
| `Depends On` edges added for shared files reduce future parallelism | Low | Medium | Correct by design (ADR-0009 Decision 4); sequential mode is unaffected |
| Spec 15 C-3 parsing rules implemented twice (15's helper and this one) drift | Medium | Low | One definition (15 C-3), cited; suite fixtures mirror 15's cases for headings and items |
| Ordinal ids `SPEC-<n>` shift when a spec without ids is amended | Low | Low | Specs are immutable after Discovery; amendments are recorded and decomposition reruns |
| Spec 09/11 move or rename the sections cited here | Low | Medium | Names follow 09's maps; citations are checked by `tests/workflow-instructions.py` |
| Forcing reselection: description edits change the `/pd-select-model` digests (`workflows/pd-select-model.md:241`) | Medium | Low | Tags and DM-5 lines are written only by `/pd-decompose`, before selection; `/pd-design` writes only `Contract` cells, Invariants and criteria; a design-driven rerun of `/pd-decompose` reruns selection as today |

## Assumptions

- A-01 | What "cost-aware" decides without measurement | Resolved: boundaries stay structural (`economics: structural-only`); no run-time economic advice, policy file or estimate | Source: `.ai/specs/README.md` → "Nine token optimization workstreams" (no saving measured), G8; P9 (`.ai/principles/architecture.md:70`); brief default "today's behaviour" | Reversible: yes
- A-02 | Adoption of another decomposition policy | Resolved: only after a spec 10 `promote` verdict and a separate owner decision and spec | Source: spec 10 Out of Scope, `Promotion rule (REQ-12)`, `Variant switches` | Reversible: yes
- A-03 | Coverage obligations | Resolved: specification criteria (DM-1) and interfaces; Solution Design invariants are judged by every leaf review (spec 15 DM-2 includes `### Invariants` for each leaf) and by `/pv-contract` | Source: spec 15 DM-2; `workflows/pv-contract.md:30` | Reversible: yes
- A-04 | When coverage is written | Resolved: `/pd-decompose`, before `/pd-select-model`, so tags do not stale model selection; `/pd-design` writes only `Contract` cells, Invariants items and carried criterion ids in its own Solution Design, never tags | Source: `workflows/phase-discovery.md:158-164`; `workflows/pd-select-model.md:241` | Reversible: yes
- A-05 | Where `/pd-decompose` gets the criteria | Resolved: targeted read of the in-scope Acceptance Criteria sections only | Source: `workflows/pd-decompose.md:23-26` (no full reread) | Reversible: yes
- A-06 | Specs without criteria | Resolved: derived criteria labelled `DC-<n>` by `/pd-analyze` | Source: `workflows/pd-analyze.md:35-37`; `workflows/phase-discovery.md:63-64` | Reversible: yes
- A-07 | Obligation id numbering for invariants | Resolved: spec 15 DM-2 `INV-<n>` | Source: spec 15 DM-2 | Reversible: yes
- A-08 | Interface agreements location | Resolved: one `### Invariants` item each, delivered by spec 12's Task Contract | Source: spec 12 DM-5, C-8 row 18 | Reversible: yes
- A-09 | Ordering expression | Resolved: only `Depends On` edges; prose ordering removed for shared files | Source: ADR-0009 Decision 4 (`:157-160`); spec 23 DM-5 treats prose ordering constraints as `no` | Reversible: yes
- A-10 | Owner of a jointly satisfied criterion | Resolved: rules O-1–O-4; `task` only under O-4 (A-29) | Source: previous §5 ("integration owner"); `workflows/pv-contract.md:30` | Reversible: yes
- A-11 | Tool form | Resolved: standalone `scripts/decomposition.py` + `scripts/check-decomposition.py`, not in the validator | Source: ADR-0019 Decision 3 (`:68-80`); spec 12 A-20, spec 13 C-11 pattern | Reversible: yes
- A-12 | Finalization integration | Resolved: optional helper, manual fallback like `validate-task.sh` | Source: `workflows/pd-finalize.md:64-74` | Reversible: yes
- A-13 | Legacy plans | Resolved: no reader outside Discovery requires the sections; `/pd-finalize` stops with recovery | Source: P3 (`.ai/principles/architecture.md:24`); G4 | Reversible: yes
- A-14 | Rollback switch | Resolved: none; rollback is reverting the delivery (Notes → Rollback) because no advice exists to disable | Source: G7; A-01 | Reversible: yes
- A-15 | Complexity classification | Resolved: none here; spec 16 DM-4 via `/pd-select-model` | Source: spec 16 DM-4, C-6 row 18 | Reversible: yes
- A-16 | Per-leaf money in the overhead report | Resolved: not reported; 05 owner ids are opaque and need the owner's key | Source: `scripts/usage_telemetry_adapter.py:20-24`; `scripts/usage_telemetry_report.py:697-714` | Reversible: yes
- A-17 | Review evidence access | Resolved: read spec 15 records from the task directory | Source: spec 15 DM-1, C-6 row 18 | Reversible: yes
- A-18 | Attempt evidence access | Resolved: caller passes spec 13 `summary` output as a file | Source: spec 13 DM-10, C-10 row 18 | Reversible: yes
- A-19 | Context bytes access | Resolved: caller passes spec 12 DM-8 records; counts from notes entries | Source: spec 12 DM-8, DM-11 | Reversible: yes
- A-20 | Parallel evidence scope | Resolved: composite children only | Source: ADR-0009 Decision 4 (`:154-156`); spec 23 A-01 | Reversible: yes
- A-21 | Who renders `### Parallel Safety` | Resolved: spec 23 REQ-09; this spec supplies DM-8 | Source: spec 23 REQ-09, REQ-52, DM-5 | Reversible: yes
- A-22 | Frozen checks | Resolved: no change to any checked file; preserve anchors | Source: ADR-0019 Decision 3; `scripts/validate-contracts.sh:604-822` | Reversible: yes
- A-23 | Composite children source | Resolved: `children:` of the composite block in `state.md` | Source: `rules/workflow-globals.md:213`; spec 15 C-3 leaf blocks | Reversible: yes
- A-24 | Boundary vocabulary | Resolved: closed code sets derived from previous §7 conditions | Source: previous §7; best practice (closed vocabularies are checkable, `.ai/principles/coding.md:39-41`) | Reversible: yes
- A-25 | Synthetic cost arithmetic (previous AC-03) | Resolved: hypothetical comparisons use spec 10's calculator; this spec ships no formula | Source: spec 10 DM-13 | Reversible: yes
- A-26 | Python requirement | Resolved: 3.11+, `-I`, exit 3 below, through an entry module parseable by older interpreters and a path-loaded engine | Source: spec 10, 12, 16 helpers; spec 12's launcher precedent (spec 12 Scope, optional helper); `python3 -I` drops the script directory from `sys.path` (Python documentation of `-I`) | Reversible: yes
- A-27 | Delivery order against undelivered specs 10, 12, 13, 15, 17 | Resolved: follow the roadmap order (`.ai/specs/README.md` → "Dependency order"); `verify` depends on none of them; `overhead` reads their specified formats, its fixtures synthesize those inputs, and each input is optional with `null` when absent | Source: roadmap; REQ-26 | Reversible: yes
- A-28 | Recovery after a verifier stop | Resolved: the existing consistency-failure route of `/pd-finalize` (stop, return to the responsible step, rerun selection when descriptions change); no in-place repair | Source: `workflows/pd-finalize.md:62-63`; `workflows/phase-discovery.md:163`; `workflows/pd-decompose.md:16-19` | Reversible: yes
- A-29 | Meaning of a `task` owner | Resolved: allowed only when task Validation judges it (criterion carried into Solution Design criteria, or interface contract as an invariant) | Source: `workflows/pv-contract.md:30` | Reversible: yes
- A-30 | Zero repair counts | Resolved: zeros only when `## Repair Episodes` exists, and they mean "no ledger line", not "policy active and nothing repaired"; a missing section is `null` because its absence cannot distinguish an inactive policy from no repair | Source: spec 17 lazy creation and reader tolerance (spec 17 DM-1 Locations, DM-3 reader tolerance); P9 | Reversible: yes
- A-31 | Listed order of composite children | Resolved: integration order, not a readiness constraint; readiness is `Depends On` | Source: spec 23 DM-5 replacement sentence for the Execution Strategy | Reversible: yes

## Decisions

N/A — auto mode; no choice overrides a principle, accepted ADR or shipped invariant. The
replacement of the "Describe any shared-file constraints" sentence is recorded by REQ-13 and
C-5.

## Clarifications

### Session 2026-11-14

- No question was put to the owner (auto mode under standing authorization). Gaps are resolved
  in A-01–A-31.

## Open Questions

- Q-01 | withdrawn | Spec 17's per-leaf repair record was unknown while its file was being
  rewritten; its current text exposes `## Repair Episodes` ledger lines to spec 18
  (spec 17 C-10 row 18), consumed by DM-9 `repairs`.
- Q-02 | non-blocker | Spec 23 holds its own blocker Q-01 on parallelism across composite
  boundaries (spec 23 Open Questions, A-01). Impact: DM-8 covers
  composite children only; if the owner widens parallelism, DM-8 must also cover top-level
  leaves. Recommended: keep within-composite scope (ADR-0009 Decision 4); nothing here depends
  on the wider reading.

## Notes

### Implementation hints (nonbinding)

Plausible subtasks: (1) helper parsing, criteria (DM-1) and coverage/tag/owner checks;
(2) graph, interfaces, files, resources, boundary and economics checks with DM-8; (3) the
`overhead` subcommand; (4) rule text, template and domain vocabulary; (5) workflow edits for
pd-analyze, pd-decompose, pd-design, pd-finalize and spec-run; (6) ADR, architecture and docs.
Each starts with failing cases in `scripts/check-decomposition.py` (smoke level for text
contracts, unit level for the helper).

### Rollback

Revert the delivery commits and run `scripts/sync.sh`. Plans written under this contract stay
readable: old workflows ignore unknown sections, although an older `/compress-state` does not
protect them. Tasks in Discovery rerun from `/pd-decompose`; tasks in Execution continue
unchanged because no execution reader uses the new sections.

### Rejected alternatives

- An owner decomposition policy file with granularity preferences (like spec 16 DM-2): no
  qualified evidence exists to fill it; adoption belongs to a later spec after 10 (A-02).
- Coverage keyed by Solution Design criteria, written by `/pd-design`: tags in descriptions
  would change the selection digests after model selection and force reselection (A-04).
- Including invariants in coverage: duplicated by spec 15's per-leaf review of all invariants
  (A-03).
- Adding the checks to `scripts/validate-contracts.sh` or `scripts/validate-task.sh`: frozen
  inventory (A-11, A-22).
- Per-leaf cost through an owner-supplied map of opaque 05 ids: adds key handling for no current
  consumer (A-16).

### Identifier history

- REQ-01: was "link every AC, invariant and interface obligation to leaves and an integration
  check"; now the Coverage table for spec criteria; invariants are covered per A-03; interfaces
  by DM-3 (REQ-02, REQ-11).
- REQ-02: was "shared decisions stored once in 12's contract"; now the interface contract as
  one Invariants item, delivered by 12 C-8; the blocking clause moved to REQ-09 and REQ-10.
- REQ-03, REQ-04: merge and split rules kept; now checkable code sets (DM-6).
- REQ-05: was "calibrated comparison when available, else structural"; calibrated comparison
  moved to spec 10 (REQ-08, A-02); this spec records `structural-only`.
- REQ-06: decision record kept; the "signals for 04/16" clause is satisfied by
  `/pd-select-model` (REQ-29); integration owner moved into DM-2/DM-3.
- REQ-07: meaning kept (canonical kinds, sequential top-level stack); its "no parallelism from
  grouping" clause is REQ-34 and its resume clause REQ-24. Spec 23 A-01 cites REQ-07 for the sequential
  top-level stack, which is unchanged.
- REQ-08: evaluation kept under spec 10; the "disable advice" clause is moot (A-14).
- AC-01–AC-05 keep their subjects with fixture-level wording; the synthetic sums of previous
  AC-03 moved to spec 10's calculator (A-25). REQ-09–REQ-41 and AC-06–AC-26 are new. Split out
  of compound statements in this refinement: REQ-33 from REQ-05, REQ-34 from REQ-07, REQ-35
  from REQ-13, REQ-36 from REQ-30, REQ-37 and REQ-38 from REQ-32.

### Follow-ups for other specs and shared files (not edited here)

- Spec 23: satisfied on 2026-11-14 (DM-5 renders from DM-8, REQ-52 re-renders in
  `/pd-design`, A-01 cites REQ-07); no further change.
- Spec 16: no change; spec 18 cites DM-4 and C-6 row 18.
- Spec 17: no change; DM-9 consumes its C-10 row 18 ledger exposure read-only.
- Spec 09: satisfied by its Notes "Files and sections created after this spec", which already
  names this spec's three sections and targets; no change.
- `.ai/specs/README.md`: no change required.

### Change log

- 2026-11-06 — implementation/state reconciliation (see Source).
- 2026-11-14 — auto-mode refinement into English: requirements made checkable, coverage and
  interface tables, boundary vocabulary, parallel evidence for spec 23, overhead report,
  standalone helper and suite.
- 2026-11-14 — reconciliation with refined peer specs. Spec 15: DM-9 example, AC-17 and the
  `reviews` mapping use the real scope values (`finding-led`, `full-leaf`, `full-task`,
  `full-integration`), cover per-composite records, and cite DM-1, DM-2, DM-7, C-3 and C-6 by id.
  Spec 17: `repairs` cites DM-1 to DM-3 and C-10 and states the read-only use. Spec 23: C-6
  row maps DM-8 onto DM-5 columns and notes REQ-52 reuses REQ-24's definition of a started
  subtask. Spec 09: C-5 "Rule-file names after spec 09" records the successor files and
  resolving checks. Spec 10: C-6 row restates that no switch exists and the `promote` precondition.
  Spec 11: one-line `loads:` statement in C-5. All peer-spec line-number citations replaced by
  section, requirement, data-model or contract ids. No requirement, acceptance criterion or
  assumption id was added, renumbered or removed; no verdict changed.
- 2026-11-14 — independent final review: README and completed-spec 05 citations by heading or id; C-5 and AC-23 name the protected list labelled `**plan.md:**`; DM-9 `repairs` attempt counts include cancelled reservations; repository citations corrected.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph: checkable coverage, order and boundary evidence, structural basis, parallel evidence, measured overhead |
| 2 | Out of Scope names concrete exclusions | PASS — classifier rules, estimates and economic advice, paid runs, per-leaf money, Parallel Safety rendering, cross-composite parallelism, new kinds, complexity, frozen files, quick flow, completed plans |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-41; previous REQ-01–REQ-08 kept, compound statements split (Identifier history) |
| 4 | Every REQ maps to an AC and back | PASS — Traceability covers 41 REQs and 26 ACs |
| 5 | Every AC is binary and can guide a test first | PASS — fixture cases in `scripts/check-decomposition.py` (C-7); `<base>` diffs marked for Validation |
| 6 | Non-functional targets measurable or N/A | PASS — NFR-01–NFR-04 and NFR-06 verified by ACs; NFR-05 N/A with reason (ADR-0020) |
| 7 | Data model and contracts specified | PASS — DM-1–DM-9, C-1–C-8 |
| 8 | Error, empty, boundary, concurrency cases | PASS — E-01–E-38; concurrency excluded by the single sequential Discovery writer (P4, E-28) |
| 9 | Every ambiguity resolved or open | PASS — A-01–A-31; Q-01 withdrawn, Q-02 non-blocker |
| 10 | No blocker question | PASS |
| 11 | Existing-code claims cited and verified | PASS — repository at `060ce6d`; specs 08–10, 12–17 and 23 in the working tree on 2026-11-14; verified by author and critic |
| 12 | Terminology matches the domain | PASS — domain terms reused; new terms added to `domain.md` by REQ-32 |
| 13 | Feature-sized (1–8 subtasks) | PASS — about six subtasks (Notes → Implementation hints) |
| 14 | Devil's Advocate review | PASS — Review: 3 rounds, score 100/100, critic: sub-agent, open: none |

Verdict: **READY FOR DEVELOPMENT**. Automated readiness is not sign-off; review before
implementation.

Reconciliation note (2026-11-14): peer specs 11, 10, 23, 09, 12, 13, 15, 14, 16 and 17 were re-read and
the changed passages align with them; the checks above and the verdict are unchanged.
