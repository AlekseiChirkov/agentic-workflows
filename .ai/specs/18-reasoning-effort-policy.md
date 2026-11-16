# 18. Reasoning effort policy by role, stage, complexity and harness capability

## Source

- **Origin:** workstream 7 ("reasoning effort") of the owner's token-optimization request of
  2026-10-21. Roadmap row 7 of `.ai/specs/README.md` → "Nine token optimization workstreams" — "Role/stage/complexity-based effort,
  capability checks, conservative fallback, measured quality" — and dependency row
  `.ai/specs/README.md` → "Dependency order" (order 12, prerequisites 04, 05, 09, 15, 16, disposition "New
  workstream 7"). The shared acceptance gates G1–G8 (`.ai/specs/README.md` → "Shared acceptance gates") are part of
  this specification's acceptance contract.
- **Previous revision:** 2026-10-28 (reconciled 2026-11-06), written in Russian. The full
  Russian text is retrievable from the git history of this file at
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Every requirement and acceptance identifier is
  preserved below. Faithful English translation of its request (translated from Russian;
  previous revision §1–§3, §4 and §10; the remaining sections §5–§9 and §11 are summarized in
  one line each):
  - Implementation review of 2026-11-06 (originally English, quoted): "Disposition: Planned;
    model-resolution foundations delivered. … Delivered evidence: Selection supports an
    explicit recommendation fallback with a reasoning_effort field and keeps
    unsupported/unknown capability states explicit. Outstanding scope and limits: The
    versioned role/stage/risk effort policy, verified setting application, and independent
    quality/economic qualification are not delivered. A fallback field alone is not this
    policy."
  - Status (§1): "Future capability of workstream 7 of the request of 2026-10-21. … Current
    model selection uses the existing catalog and suitability rules; the orchestrator
    separates the executor from the independent reviewer and keeps the executor between its
    checkpoints. A versioned effort policy by role/stage and qualified cheaper values are not
    considered implemented. … Settings of a specific installed harness and the exact syntax
    are verified at implementation against its version and authoritative information; the
    fields below are not a claim about current provider parameters."
  - Goal (§2): "Use only actually supported effort settings, choose them by role, stage,
    complexity and risk, and honestly record what was requested, permitted by the harness and
    observed. Mechanical work is performed by a deterministic tool when that suffices. Complex
    and critical work keeps a conservative configuration until alternatives are
    independently qualified."
  - Ownership (§2): "18 owns the resolution of a supported setting. The model catalog and
    availability belong to 04, harness capabilities to 13, measurement to 05, qualification to
    09, verification to 16, the escalation decision to 19. 19 is a later consumer of setting
    resolution, not a prerequisite of 18. Until 19's repair policy is enabled, the existing
    stops and owner-authorized assignments apply; no autonomous escalation arises from this
    specification."
  - Out of scope (§2): "invented parameters, transferring level names between providers, a
    learned router, automatic change of model/provider, production cost limits and a promise
    of visibility of hidden reasoning tokens."
  - Terms (§3): requested effort — "the intent of the owner, the task or the policy"; resolved
    setting — "the exact value the current verified capability allows to be passed to the
    selected model"; confirmation of application — "only an acceptance of the parameter
    explicitly returned by the harness; absent confirmation is not invented"; observed effort
    — "the execution characteristic actually disclosed by the harness; may remain unknown";
    policy intent class — "a local notion of complexity/risk, not a universal numeric
    provider scale"; minimum quality floor — "an approved suitability constraint of a
    configuration for a task class".
  - Invariants (§3): "1. The same level name on different models does not mean the same
    computation, quality or cost. 2. A sent parameter does not prove its application, let
    alone the actual amount of reasoning. 3. Unknown measures are not recorded as zero. 4. An
    unsupported parameter is not sent at random. The model is not silently substituted. 5. A
    cheaper setting does not become the default without qualification of the full result under
    09. 6. A stage switch resolves the setting anew; a cheap mechanical action does not lower
    the next complex check."
  - REQ-01: "Define an optional versioned policy by role (`orchestrator`, `Arbiter`,
    `Implementer`, `Validator`), stage, complexity, risk, ambiguity and task kind. For
    sufficient mechanical actions prefer deterministic tools. Planning, uncertain
    architecture, critical invariants and complex verification keep conservative minimum
    floors."
  - REQ-02: "Supported model/harness settings are described in a single 04/13 registry: exact
    syntax, allowed values, scope, date/version of confirmation and states of
    unknown/unsupported. Cross-provider equating of names and invented token budgets are
    forbidden."
  - REQ-03: "Priority: an explicit approved owner/run override, an approved task override, a
    qualified role/stage policy, the previous suitable conservative harness value. All
    options are checked against quality floors. A conflict with a floor is shown for decision;
    it is not hidden by lowering or by ignoring the request."
  - REQ-04: "If effort control is absent or application cannot be confirmed, use the
    documented suitable value without unsupported parameters and separately record requested,
    resolved and observed. Observed remains unknown when data is absent. Substituting the
    model for the sake of a setting without permission is forbidden."
  - REQ-05: "On stage change, recovery and retry keep the policy's provenance and determine
    suitability anew. Inheriting the cheap effort of a mechanical stage into a complex fix or
    review is not allowed. The decision to escalate belongs to 19; here only the supported
    setting is checked."
  - REQ-06: "Until an independent evaluation of the quality and full cost of the accepted
    result under 09, keep the previous defaults. An offline check of setting resolution proves
    the correctness of the parameter choice, not the quality of the model."
  - REQ-07: "Account under 05 for full input/output, the available part of reasoning, cache,
    time, failures, retries, verification and escalation. Reasoning tokens already included in
    output are not paid twice. The absence of a separate counter does not equal absence of
    reasoning."
  - REQ-08: "Old plans remain valid; describe disable/rollback and satisfy G1–G8. Ordinary
    setting resolution and checks do not call the provider and do not start a paid
    experiment."
  - AC-01 (REQ-01, REQ-03): "Tabulated roles/stages/risks yield the expected rule and source.
    Architectural/critical uncertainty keeps the floor; an incompatible override and a rule
    conflict are explicitly detected."
  - AC-02 (REQ-02, REQ-04): "Supported values are passed exactly. An unknown model/version and
    an unsupported value produce no invented argument or model change. Requested, resolved,
    confirmed and observed are distinguished."
  - AC-03 (REQ-05): "Stage change, recovery and 19's escalation use one registry and recheck
    the floors. A mechanical stage's setting is not inappropriately inherited; the
    session-scope limitation is respected."
  - AC-04 (REQ-06, REQ-07): "An unqualified economical entry does not become the default. A
    synthetic report accounts for verification/repair, unknown measures and the part of
    reasoning included in output without double counting. An offline scenario is not
    presented as an evaluation of live model quality."
  - AC-05 (REQ-08): "An old plan, absent policy, viewing a decision without a run, disable and
    resume keep the current behaviour. No network/paid calls occur during resolution and
    offline checks."
  - Summarized: §5 sketched a capability registry keyed by exact harness/model version and a
    declarative policy record with `require_exact`; §6 an eight-step deterministic resolution
    algorithm; §7 stage change and recovery (no claimed switch inside a live worker; RED and
    GREEN stay in one Implementer); §8 qualification only through a separate 09 plan; §9 an
    error/fallback table; §11 an implementation order (verify capabilities, schema, offline
    scenarios, wiring to 15/05, rollback documentation).

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. File names in this section are the
current (pre-spec-13) names; see Notes → Name mapping for the names the implementation edits.

1. **An effort contract already exists, but only for leaf Implementers and only as prose.**
   `/pd-select-model` recommends a reasoning effort per leaf from demand and risk scores
   ("1–2 favor low, 3 medium, 4 high, 5 the highest justified supported level; hard
   constraints favor high or higher", `workflows/pd-select-model.md:212-221`), reports
   `not configurable` or a preliminary owner-configured fallback level when support is
   unknown (`:223-229`), and records the recommendation with its support observation in the
   task's `## Model Selection` checkpoint (`:238-245`). The owner-configured fallback carries a
   `reasoning_effort` string (`workflows/pd-select-model.md:89-101`;
   `scripts/model_selection.py:320-322`, `:431-433`). Before dispatch, the canonical rule
   requests the recommended level "only if currently supported and configurable" as observed
   from the current tool, otherwise reports the mismatch and "stop[s] that explicit effort
   request; never silently substitute a level"; legacy tasks keep their behaviour; inline
   execution cannot switch its own setting; recommended, requested and actual are reported
   separately and actual stays unknown (`rules/workflow-reference.md:144-154`). The offline
   helper does not compute or validate effort, and effort is recommended "separately from model
   identity" (`docs/MODEL-CATALOG.md:82-89`).
2. **Arbiter and Validator always run at the session default.** `/spec-run` spawns the
   Arbiter "without a model override" (`workflows/spec-run.md:90-93`) and the Validator "as a
   session-default role worker without a model override" (`:284-288`); plan model intent
   applies only to Implementers (`:126-130`; ADR-0015 Decision 3, "Leaf recommendations govern
   Implementers; task-wide Arbiter and independent Validator workers retain distinct
   session-default roles"). No text sets or records effort for these roles.
3. **Support is judged from the session only.** The rule asks the dispatcher to "observe the
   current tool's supported effort levels" (`rules/workflow-reference.md:145-146`). No
   harness declaration states whether a worker-spawn mechanism accepts an effort setting:
   `harness/claude/capabilities.md` declares logging (`:1-27`) and a `git-rails` record
   (`:29-90`: record `:31-37`, anchored lines `:39-52`, prose `:54-60`, `limitations:` `:62-67`,
   residual-risk table `:69-90`); `harness/codex/capabilities.md` declares `hooks: no` (`:3`) and
   `git-rails: none (textual rules only)` (`:12`). `rg -i effort harness/` returns nothing.
   The only effort values observed in the repository concern the separate CLI process
   (`claude --effort`, values `low`, `medium`, `high`, `xhigh`, `max`, observed with
   `claude --help` on 2026-11-13, spec 09 Context & Problem, installed-CLI observation), not a sub-agent
   spawn.
4. **Nothing records what was actually requested per spawn.** The recommendation lives in
   `## Model Selection`; the dispatch-time request, its source and the reason it was or was
   not sent are reported in chat only. Spec 05's telemetry has an `effort` capability flag in
   source profiles (`scripts/usage_telemetry_contract.py:536-545`, values `unknown`,
   `supported`, `unsupported`) and an `effort` report dimension carried by opaque
   `dimension_evidence` records (`scripts/usage_telemetry_contract.py:2900-2916`;
   `scripts/usage_telemetry_report.py:48`), but no source-profile parameter for observed
   effort (`resolution.parameters` admits only `model`, `service_tier`, `region`, `modality`,
   `scripts/usage_telemetry_contract.py:500-502`).
5. **A cheaper default needs approved comparative evidence.** The roadmap requires an
   explicitly approved spec-09 comparison before promoting a cheaper default
   (`.ai/specs/README.md` → "Shared acceptance gates", introductory paragraph); ADR-0015 repeats it ("Cheaper-default promotion requires
   separately approved independent comparison"). Spec 09 emits an advisory per-comparison
   `verdict` (`promote`, `do-not-promote`, `insufficient-data`) in `report.json`
   (spec 09 DM-12 Report and `Promotion rule (REQ-12)`); its manifest variants carry
   `roles: {<role>: {model, effort}}` with `effort` one of `low`, `medium`, `high`, `xhigh`,
   `max`, `session-default` (spec 09 DM-6 Manifest); it leaves "changing … effort policy" and adoption of a
   promoted variant to a separate owner decision (spec 09 Out of Scope).
6. **Constraints on delivery.** The validator's check inventory is frozen; new checks are
   standalone scripts outside `scripts/validate-contracts.sh`, and a new shell or Python file
   under `tests/` invalidates the nested source guard (ADR-0019 Decision 3,
   `.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-76`). Frozen checks
   read `workflows/spec-run.md`, `rules/orchestration.md` (`scripts/validate-contracts.sh:1041`,
   `:1508-1529`) and the `## git-rails` section of `harness/claude/capabilities.md`, which ends
   at the next `## ` heading (`scripts/validate-contracts.sh:5257-5265`). The model workflow
   suite reads `rules/workflow-reference.md` from `### Model columns and resolution` to the end
   of its `##` section and requires `reasoning.*(?:recommendation|level)` and
   `reasoning.*(?:actual|observed)` there (`tests/model-workflow.py:89-96`, `:161-169`). Spec
   13's inventory amendment admits `contract_changes` only for a closed set of 13's own
   requirement ids (spec 13 DM-9 `contract_changes`, extended only by 13 REQ-69).
7. **Spec 13 lands first.** The dependency order puts 13 (order 2) before 09 (order 6) and 09
   before 18 (order 12) (`.ai/specs/README.md` → "Dependency order"). 13 renames the workflows and rules this
   spec edits and splits `rules/workflow-reference.md`, sending `### Model columns and
   resolution` and `## Protected Sections Contract` to `rules/contract-state-files.md`
   (spec 13 DM-10 row `rules/workflow-reference.md` and DM-12), and
   appends a `## Capability records` section at the end of each capability file (spec 13 DM-4).

Consequence: effort is chosen for one role by a prose heuristic, judged supported from the
session's own perception, never declared per harness, and not persisted per spawn. The other
roles cannot be configured at all, an owner cannot state a policy, a lowering cannot be tied
to evidence, and telemetry cannot attribute usage to the effort actually requested.

## Goal

Give every worker spawn of the sequential orchestrated and single-session execution paths one
deterministic, offline effort decision: an optional owner-written, versioned policy maps
role, stage and recorded complexity to an exact harness-specific value; a policy-chosen value
is sent only when the harness declares the setting with evidence and the session exposes it,
while today's session-observed Implementer recommendation keeps working until a declaration
exists; otherwise the spawn uses the harness default visibly. No rule may lower effort below
today's behaviour without an approved spec-09 comparison, every decision is persisted with its
model, requested, resolved and actual (unknown) values, and with no policy and no escalation
the request sent equals today's, also when the resolver itself is unusable (REQ-39).

## Scope

1. A per-harness capability section `## sub-agent-effort` (DM-1) in the record form of spec
   13 DM-4, with anchored value, order, default and parameter lines; shipped as `unknown`
   unless evidence is collected at implementation.
2. An optional owner policy file (DM-2) with `target` and `minimum` rules matched on role,
   stage, quality floor, hard constraints and leaf kind, an optional spec-09 qualification
   reference (DM-3) and a bounded owner raise.
3. A standard-library helper `scripts/effort-policy.py` with `resolve` and `check-policy`
   commands (C-1–C-3): pure, offline, deterministic.
4. A per-leaf complexity and recommendation line written by the model-selection workflow
   (DM-4).
5. A task-level, protected, append-only `## Effort Decisions` section (DM-5) written by the
   dispatcher.
6. Dispatcher integration for the `/spec-run` Arbiter, Implementer and Validator spawns and the
   leaf worker spawn of the single-session executors; harness rejection; resolver
   unavailability; the disable switch (C-4).
7. The effort dimension source string offered to spec 05 (C-5) and the contracts exposed to or
   consumed from specs 04, 05, 09, 12, 13, 15, 16, 19 and 20 (C-6); G1–G8 conformance (C-8).
8. A companion guide `docs/EFFORT-POLICY.md`, domain vocabulary entries, an ADR and a
   standalone acceptance suite `scripts/check-effort-policy.py` (C-7).

## Out of Scope

- Choosing or substituting a model or provider; model eligibility stays with
  `### Model columns and resolution` and spec 04.
- The Orchestrator's own session effort, inline execution (it cannot switch its own setting,
  `rules/workflow-reference.md:152`), Discovery children run inline, the quick tier, the
  `/spec-draft` Devil's Advocate critic and `/bugfix`.
- Spec 12's parallel-mode spawns (leaf coordinators, phase agents and per-workflow agents):
  they are outside policy version 1 and keep today's dispatch behaviour until a later change to
  this spec brings them in (C-6 row 12, A-29).
- Changing the existing model-selection heuristic that maps scores to a recommended level
  (`workflows/pd-select-model.md:216-221`), including its low recommendations for low-demand
  leaves.
- Any shipped policy file, shipped default level, numeric target, token budget or claimed
  saving; any cross-harness equivalence of level names.
- Running, scheduling or approving a spec-09 experiment; paid model runs of any kind.
- Deciding when a failed attempt escalates (spec 19) and producing new complexity evidence
  (spec 20).
- Writing spec-05 telemetry records or extending 05's schema, including the previous REQ-07
  accounting of reasoning, cache, retries and escalation and the previous AC-04 synthetic
  report: 05 already owns that accounting; this spec only supplies the C-5 label.
- A harness acknowledgement ("confirmation of application", previous §3): no documented
  acknowledgement mechanism exists; only an explicit spawn rejection is recorded (REQ-10).
- A dispatch-record field in spec 15's `checkpoint_attempt` (C-6 explains why none is needed).
- Changing effort inside a live worker; per-message effort.
- Preferring deterministic tools for mechanical actions (previous REQ-01 sentence): that is a
  property of decomposition and tool design (specs 17 and 20), not of a spawn parameter.

## Actors & Roles

| Actor | Allowed actions | Forbidden |
|---|---|---|
| Owner | Writes, versions, disables or removes the policy file; adds qualification references after adopting a spec-09 `promote` verdict; sets `owner_raise`; collects capability evidence | — |
| Dispatcher — the `/spec-run` Orchestrator, or the single-session executor (`execution-execute`, `atomic-execution`) when it spawns a leaf worker | Builds the request, runs the resolver, appends `## Effort Decisions` lines, passes the effort parameter only on `outcome: requested`, stops on `outcome: stop` | Editing or deleting decision lines; choosing a value the decision did not resolve; retrying another value after a rejection |
| Resolver `scripts/effort-policy.py` | Reads the capability file, the policy file, the qualification files the policy names and the request; prints one decision | Writing any file; network access; starting processes; reading other paths |
| Model-selection workflow | Writes `effort-input:` lines into `## Model Selection` during bulk selection | Running the resolver |
| Worker (Arbiter, Implementer, Validator) | Runs at the effort it was spawned with | Writing `## Effort Decisions` |
| Spec 19 policy (future) | Supplies an `escalation` value in the request | Bypassing the capability gate |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Reasoning effort | A harness-specific setting, chosen when a worker is spawned, that the harness documents as controlling how much the model reasons. Values are exact strings of one harness; equal strings on different harnesses are unrelated. | Previous §3 invariant 1 |
| Effort value | One exact token from a harness's declared `sub-agent-effort values:` line (DM-1), or a token the session exposes. | New |
| Harness default | Spawning without any effort parameter. Its level is unknown unless DM-1 declares `default:`. Written `harness-default` in records. | New; `rules/workflow-reference.md:150` |
| Recommended effort | The per-leaf level from the model-selection workflow (existing). | `workflows/pd-select-model.md:212-229` |
| Requested effort | The effort the precedence of C-3 settles on before the capability gate: an effort value or `harness-default`. Only DM-5's unavailable line writes `unknown`, because no decision exists. | Previous §3; model analogue `.ai/memory/architecture.md:237` |
| Resolved effort | The effort value actually passed in the spawn, or `none`. | Previous §3 |
| Actual effort | The effort the execution used, from separate execution evidence. Always `unknown` in this spec. | Previous §3 "observed"; `rules/workflow-reference.md:153-154` |
| Baseline | Today's behaviour for a spawn: the recommended effort for an Implementer whose recommendation applies (C-3 step 2), otherwise `harness-default`. | New; G4/G7 |
| Effort policy | The optional owner file DM-2. | Previous REQ-01 |
| Target rule / minimum rule | A policy rule that sets the requested effort when no recommendation applies / that raises a lower requested effort. | New |
| Owner raise | `owner_raise: true` on a target rule whose value is the highest declared value: the owner's explicit acceptance that the top value is not a lowering (C-3 step 3). | Previous REQ-03 "explicit approved owner override" |
| Provably at least / provably lower | The C-3 comparisons on a declared ascending order. | New |
| Qualification | A DM-3 reference to a spec-09 comparison whose verdict is `promote` and whose variants differ in exactly the rule's effort. | spec 09 DM-6 Manifest, `Promotion rule (REQ-12)` |
| Spawn (dispatch) | One start of a worker, including recreation after interruption or rejection. A message to a live worker is not a spawn. Not the run-log `dispatch` marker (`rules/run-log.md:383`). | `rules/orchestration.md:40-41`, `:63-67` |
| Decision | The resolver's output DM-7 for one spawn. | New |
| Quality floor | The ordinal 1–5 demand floor computed by `quality_floor` (`scripts/model_selection.py:106`). Used here as the complexity signal. | Spec 04 |

Rejected synonyms: "reasoning level" for an effort value outside quotations of existing text;
"applied effort" (use resolved for what was sent and actual for what ran); "budget" for
effort.

## Requirements

### Preserved identifiers, restated

- **REQ-01 Policy matching.** WHEN the resolver evaluates a spawn with a valid policy, THE
  resolver SHALL treat as matching exactly the rules whose every `match` condition holds for
  the request under DM-2 → Matching and whose `levels` object has a key equal to the
  request's `harness`.
- **REQ-02 Capability declaration.** EACH of `harness/claude/capabilities.md` and
  `harness/codex/capabilities.md` SHALL contain exactly one `## sub-agent-effort` section in
  the DM-1 form and position, and a section without cited evidence for the harness's
  installed runtime SHALL declare `state: unknown`, `values: none`, `order: unknown`,
  `default: unknown` and `parameter: unknown`.
- **REQ-03 Precedence.** WHEN the resolver computes the requested effort, THE resolver SHALL
  apply the steps of C-3 in their listed order: policy, baseline, target rule, minimum rule,
  escalation, gate, enforcement.
- **REQ-04 Capability gate.** IF the requested effort is an effort value and any C-3 step 6
  check fails, THEN THE resolver SHALL set `resolved` to `null` and `outcome` to
  `not-requested` (or `stop` under REQ-13) with the first failing check's reason code, and
  SHALL NOT resolve any other value.
- **REQ-05 One decision per spawn.** WHEN a dispatcher is about to spawn or recreate a worker,
  THE dispatcher SHALL run the resolver for that spawn and pass the effort parameter to the
  spawn only when the decision's `outcome` is `requested`, using exactly its `resolved` value;
  a message to a live worker (the RED continuation, an Arbiter question) SHALL carry no effort
  parameter and produce no decision.
- **REQ-06 Qualified lowering.** IF a matching target rule's value is not provably at least the
  baseline and the rule has no valid `owner_raise`, THEN THE resolver SHALL apply that rule
  only when a matching rule's `qualification` verifies under DM-3, and otherwise SHALL keep
  the baseline with reason `rule-unqualified` (no qualification) or `qualification-invalid`
  (verification failed).
- **REQ-07 No invented measurement.** THE decision SHALL carry `actual: "unknown"` and a
  `dimension_source` string (C-5), and SHALL contain no token count, cost, duration or other
  numeric measure of reasoning.
- **REQ-08 Unchanged without a policy.** IF no policy is used (file absent, `--no-policy`, or
  the disable switch) and the request's `escalation` is `null`, THEN THE resolver's
  `requested` value SHALL equal the baseline.

### Persistence and reporting

- **REQ-09 Decision line before spawn.** WHEN the resolver prints a decision for a spawn, THE
  dispatcher SHALL append exactly one DM-5 decision line to the task `state.md`
  `## Effort Decisions` section before it spawns the worker or stops.
- **REQ-10 Harness rejection.** IF the harness refuses a spawn and its error message names the
  DM-1 `parameter` or the resolved value, THEN THE dispatcher SHALL append a DM-5 rejection
  line for that key, SHALL NOT retry with another effort value, and SHALL run the resolver
  again for a new spawn whose request has `session.parameter: "absent"`.
- **REQ-33 Report line.** WHEN a DM-5 line is appended, THE dispatcher SHALL report one line
  `effort: <key> model <model> requested <requested> resolved <resolved|none> actual unknown
  (<reasons|none>)` in its run output (`rejected-by-harness` in place of the values for a
  rejection line).

### Stops and degraded paths

- **REQ-11 Invalid policy.** IF the policy file exists and fails DM-2 validation, THEN THE
  resolver SHALL print a decision with `outcome: "stop"` and reason `policy-invalid` and exit
  1.
- **REQ-12 Policy conflict.** IF two matching rules of the same `kind` name different values
  for the request's harness, THEN THE resolver SHALL print a decision with `outcome: "stop"`
  and reason `policy-conflict` and exit 1.
- **REQ-13 Enforced minimum.** IF a matching minimum rule has `enforce: true` and the
  effective effort of the decision (the resolved value, or `harness-default` when nothing is
  resolved) is not provably at least that rule's value, THEN THE resolver SHALL set
  `outcome: "stop"`, add reason `minimum-unsatisfied` and exit 1.
- **REQ-34 Stop before spawn.** WHEN a decision has `outcome: "stop"`, THE dispatcher SHALL
  NOT spawn the worker and SHALL stop with the C-4 stop message.
- **REQ-14 Resolver unusable.** IF the resolver cannot be run or does not return a usable
  result (C-4 step 4: Python 3.11+ or the helper missing, exit 2 or 3, any other exit code, or
  stdout that is not a DM-7 document, including a crash or a kill by the tool's own command time
  limit), THEN THE dispatcher SHALL stop before the spawn when the policy file exists and the
  disable switch (REQ-21) is not in effect, and otherwise SHALL apply REQ-39. A policy file that
  exists counts whatever its content: without the resolver the dispatcher cannot tell a malformed
  file from a valid one, so a malformed file with an unusable resolver stops as well (a
  malformed file with a working resolver stops under REQ-11).
- **REQ-39 Today's rule without a usable resolver.** IF REQ-14 applies and either no policy file
  exists or the disable switch (REQ-21) is in effect, THEN THE dispatcher SHALL decide the effort
  parameter itself by today's rule, as C-3 step 2 and step 6c do with the capability treated as
  `unknown` (REQ-37, A-26): for an Implementer spawn whose DM-4 recommendation is a level token
  (not `none` and not `not-configurable`) made for the spawn's own model identity (REQ-17,
  REQ-18, REQ-36), THE dispatcher SHALL send that level as the effort parameter only when the
  REQ-35 observation shows the parameter exposed with that level among its enumerated values; in
  every other case (Arbiter, Validator, no usable recommendation, parameter absent, unknown or
  without enumeration, level not enumerated) it SHALL spawn without an effort parameter. It SHALL
  send no value other than that recommendation, SHALL apply no policy rule, and SHALL NOT apply
  a non-null escalation (REQ-29), recording `escalation-unverifiable` instead. Where it can read
  the harness capability record and the record declares `state: no`, it SHALL send no parameter.
- **REQ-40 No fallback for an owner policy.** WHILE a policy file exists and the disable switch
  (REQ-21) is not in effect, THE dispatcher SHALL NOT apply REQ-39: a policy that cannot be
  evaluated is a stop (REQ-14, REQ-11, REQ-12, REQ-13), never today's rule. A value chosen by a
  policy rule (`policy-target`, `policy-minimum`), and any lowering of the baseline, therefore
  reaches a spawn only through a usable resolver; REQ-39 can send only the leaf's own
  recommendation, which is today's request.
- **REQ-41 Unavailable line.** WHEN REQ-39 applies, THE dispatcher SHALL append one DM-5
  UNAVAILABLE line before it spawns (REQ-09) and report it (REQ-33): outcome `requested` with
  `requested` and `resolved` both the level sent, or outcome `not-requested` with `requested
  unknown` and `resolved none`; reasons in C-2 order holding the codes that C-3 steps 2, 5
  (`escalation-unverifiable` only) and 6 would add for that decision, then `resolver-unavailable`,
  then the cause code of C-2 (Unusable-resolver output). For a harness other than `claude` or
  `codex` (C-4 step 2) no DM-5 line can be written (DM-5 admits only those two); the dispatcher
  applies REQ-39 and reports the decision (REQ-33) without a line.
- **REQ-31 Unusable capability section.** IF the capability file is unreadable or its
  `## sub-agent-effort` section is absent or violates DM-1, THEN THE resolver SHALL treat the
  capability as `invalid` with reason `capability-invalid` and continue C-3 (exit 0 unless
  REQ-11, REQ-12 or REQ-13 applies).
- **REQ-21 Disable switch.** WHERE the environment variable `ORCHESTRAIL_EFFORT_POLICY`
  is set to a value other than the empty string or `on` (documented value `off`; the rule of
  spec 14 REQ-32), THE dispatcher SHALL invoke the resolver with `--no-policy` for every spawn of
  the run.

### Inputs

- **REQ-15 Complexity line.** WHEN the model-selection workflow records `selection: complete`
  in bulk mode, THE workflow SHALL write one DM-4 `effort-input:` line per current leaf in
  `## Model Selection`.
- **REQ-16 Unknown complexity.** IF a leaf has no `effort-input:` line, or the spawn is an
  Arbiter, THEN THE dispatcher SHALL send `complexity.quality_floor: null` and
  `complexity.hard_constraints: null`.
- **REQ-17 Recommendation for another model.** IF the recommendation's `for` identity differs
  from the request's `model`, THEN THE resolver SHALL use `harness-default` as the baseline
  with reason `recommendation-model-mismatch`.
- **REQ-18 Not-configurable recommendation.** IF the recommendation value is
  `not-configurable`, THEN THE resolver SHALL use `harness-default` as the baseline with
  reason `recommendation-not-configurable`.
- **REQ-29 Escalation input.** WHEN the request carries an `escalation` value, THE resolver
  SHALL apply C-3 step 5: raise the requested effort to it when the requested effort is
  provably lower, leave it unchanged when the requested effort is provably at least it, and
  otherwise leave it unchanged and add `escalation-unverifiable`.
- **REQ-30 Request validation.** IF the arguments violate C-1 or the request violates DM-6,
  THEN THE resolver SHALL exit 2 with one `<code>: <detail>` line on stderr (C-2) and print
  nothing on stdout.
- **REQ-35 Session observation.** WHEN the dispatcher builds a request, THE dispatcher SHALL
  set `session` from the spawn tool schema visible in its own session: `exposed` with the
  enumerated values when the tool shows a parameter named as DM-1's `parameter:` line (or,
  while that line is `unknown`, a parameter whose name contains `effort`) with an enumerated
  value set; `exposed` with `values: null` when such a parameter shows no enumeration;
  `absent` when the tool shows no such parameter; and `unknown` when no tool schema is visible.
- **REQ-36 Legacy recommendation.** IF an Implementer's leaf has no DM-4 line, THEN THE
  dispatcher SHALL send `recommendation: null`.
- **REQ-38 Missing recommendation.** IF an Implementer request has `recommendation: null`,
  THEN THE resolver SHALL use `harness-default` as the baseline with reason
  `recommendation-unavailable`.
- **REQ-37 Session-only recommendation.** IF the requested effort's source is
  `recommendation` and the capability is `unknown` or `invalid`, THEN THE resolver SHALL
  apply the session checks of C-3 step 6 instead of failing, adding
  `session-only-recommendation`.

### Helper properties

- **REQ-19 Determinism and isolation.** THE resolver SHALL print byte-identical stdout for
  identical argument values and file bytes, SHALL open no network connection, start no
  process and write no file, and SHALL read only the files named by its arguments and the
  qualification files named inside the policy.
- **REQ-20 Policy check.** WHEN `check-policy` runs, THE resolver SHALL validate the policy
  (and, with `--capabilities`, each rule value against that harness's declared values) and
  print the C-1 summary, exiting 0 when valid and 1 otherwise.

### Delivery

- **REQ-22 Dispatcher text.** THE delivery SHALL add the C-4 procedure as the subsection
  `### Reasoning effort resolution` of the state-files contract (Notes → Name mapping),
  placed in the same `##` section directly after `### Model columns and resolution`; SHALL
  replace that section's existing effort paragraph (the one beginning "For each leaf, read its
  reasoning effort recommendation", `rules/workflow-reference.md:144-154` before spec 13) by
  one sentence citing the new subsection; and SHALL cite the new subsection from
  `workflows/spec-run.md` (Arbiter spawn in Step 1, 4.2 and 4.3) and from the two
  single-session executors' model-resolution steps.
- **REQ-23 Protected section.** THE delivery SHALL list `## Effort Decisions` under task-level
  `state.md` in the state-files contract's `## Protected Sections Contract`.
- **REQ-24 Capability record and behaviour row.** THE delivery SHALL declare the
  `## sub-agent-effort` record (DM-1) in each harness's `capabilities.md`, with `state: unknown`
  where no evidence exists. WHERE the phases contract has `## Capabilities` (spec 13
  delivered), THE delivery SHALL also add the behaviour row of C-4 → Capability row; spec 13
  REQ-67 admits in a `Requires` cell the `name:` of a capability record that every harness's
  `capabilities.md` declares.
- **REQ-25 Guide.** THE delivery SHALL add `docs/EFFORT-POLICY.md` with the DM-1, DM-2, DM-3
  schemas, one runnable fictional example per command and the disable and rollback procedure;
  an entry for it in `docs/README.md`; one sentence citing it in `docs/MODEL-CATALOG.md →
  ## Reasoning effort`; and table rows for `effort-policy.py` and `check-effort-policy.py` in
  `scripts/README.md`.
- **REQ-26 Standalone suite.** THE delivery SHALL add `scripts/check-effort-policy.py`
  (C-7), SHALL NOT register it in `scripts/validate-contracts.sh` or `scripts/sync.sh`, and
  SHALL add no file under `tests/`.
- **REQ-27 Decision record.** THE delivery SHALL add an Accepted ADR recording DM-1, DM-2, the
  C-3 precedence, the session-only recommendation path, the owner raise, the qualification
  rule, the `## Effort Decisions` section and the new stops, indexed in `.ai/adr/index.md`.
- **REQ-28 Frozen suite intact.** THE delivery SHALL leave every check expression of
  `scripts/validate-contracts.sh` and every file under `tests/` byte-identical, and the full
  validator SHALL pass on the delivered tree.
- **REQ-32 Vocabulary.** THE delivery SHALL add the terms Reasoning effort, Harness default,
  Effort policy and Effort decision to `.ai/principles/domain.md → ## Vocabulary`.

## Data Model

All entities are **new** unless marked. JSON is UTF-8; files over 1,048,576 bytes are
rejected; duplicate object keys, `NaN`/`Infinity` and unknown keys are invalid everywhere.
"Token" means a string matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$`. "Model identity" means
`<provider>/<id>` matching `^(anthropic|openai)/[^\s|;]{1,256}$` or the literal
`session-default` (a spawn without a model override).

### DM-1 Capability section `## sub-agent-effort` (extends `harness/<id>/capabilities.md`)

Position: immediately before the line `## Capability records` when the file has one (spec 13
DM-4 keeps that section last), otherwise after the file's last line. Either way the section
starts after the `## git-rails` section, so the frozen `git_rails_section` reader stops at its
heading (`scripts/validate-contracts.sh:5257-5259`).

```text
## sub-agent-effort

name: sub-agent-effort
state: yes
runtime: <runtime name and version>
verified: <YYYY-MM-DD>
evidence: <URL or repository-relative path>

Limitations: <one paragraph>

sub-agent-effort values: <token>, <token>, …
sub-agent-effort order: ascending
sub-agent-effort default: <token>
sub-agent-effort parameter: <token>
```

| Line | Rule (validated by the resolver unless marked) |
|---|---|
| Heading | Exactly one line `## sub-agent-effort` in the file; the section runs to the next line starting `## ` or the end of file |
| Record (`name:` … first empty line) | Spec 13 DM-4 grammar: keys `name`, `state` (`yes`/`no`/`unknown`), `runtime`, `verified` (valid `YYYY-MM-DD`), `evidence` (repeatable, no whitespace); `runtime`, `verified` and ≥1 `evidence` required unless `state: unknown`. Extension record name `sub-agent-effort` |
| `Limitations:` paragraph | A line starting `Limitations: ` must follow the record. Its content is not validated by the resolver; AC-16 checks that it says resolved is not actual |
| `sub-agent-effort values:` | Exactly once in the section. `none` iff `state` is not `yes`; otherwise ≥1 unique tokens joined by `, ` |
| `sub-agent-effort order:` | Exactly once. `ascending` (values listed lowest to highest, with evidence) requires `state: yes` and ≥2 values; otherwise `unknown` |
| `sub-agent-effort default:` | Exactly once. A token from `values` (the level used when no parameter is sent, with evidence) or `unknown` |
| `sub-agent-effort parameter:` | Exactly once. The token naming the spawn tool's effort parameter, or `unknown` (required when `state` is not `yes`) |

Meaning of `state: yes`: the harness's worker-spawn mechanism used by the shipped workflows
accepts an effort setting at spawn with the listed values, per the cited evidence for the
named runtime. `no`: the documented mechanism has no such setting for that runtime. The
section contains no `.ai/` path, `T-NN` id or `ADR-NNNN` (it is deployed into the always-on
context, `scripts/sync.sh:61-62`). The resolver reads the source checkout's file
(`$SOURCE_ROOT/harness/<id>/capabilities.md`), which is authoritative; the deployed always-on
copy is refreshed by sync and is not read by the resolver.

### DM-2 Policy file (owner configuration)

Path: `${XDG_CONFIG_HOME}/orchestrail/effort-policy.json` when `XDG_CONFIG_HOME` is set and
non-empty, otherwise `~/.config/orchestrail/effort-policy.json` (the pattern of
`workflows/pd-select-model.md:89-90`). Optional; never created by any workflow.

```json
{
  "schema_version": 1,
  "policy_id": "owner-policy",
  "policy_version": "1",
  "rules": [
    {
      "rule_id": "validators-at-least-high",
      "kind": "minimum",
      "enforce": false,
      "match": {"roles": ["validator"], "stages": null, "quality_floors": [4, 5],
                "hard_constraints": "any", "leaf_kinds": null},
      "levels": {"claude": "high"}
    }
  ]
}
```

| Field | Rule |
|---|---|
| `schema_version` | `1` |
| `policy_id`, `rule_id` | `^[a-z0-9][a-z0-9-]{0,63}$`; `rule_id` unique in the file |
| `policy_version` | `^[0-9]+(\.[0-9]+){0,3}$` |
| `rules` | Array of 0–256 rules; an empty array is valid |
| `kind` | `target` or `minimum` |
| `enforce` | Boolean; required for `minimum`; forbidden for `target` |
| `owner_raise` | Optional boolean, `target` only; default `false` |
| `qualification` | Optional DM-3 object, `target` only; default absent |
| `match.roles` | Non-empty unique subset of `arbiter`, `implementer`, `validator` |
| `match.stages` | `null` (any) or non-empty unique subset of `context`, `execution`, `validation` |
| `match.quality_floors` | `null` (any, including unknown) or non-empty unique integers 1–5 |
| `match.hard_constraints` | `any`, `present` (known non-empty list) or `absent` (known empty list) |
| `match.leaf_kinds` | `null` (any) or non-empty unique subset of `ordinary`, `fix` |
| `levels` | Object with 1–2 keys, each `claude` or `codex`, each value a token |

All `match` keys are required. **Matching.** A rule matches a request when:
`request.dispatch.role ∈ roles`; `stages` is `null` or contains `request.dispatch.stage`;
`quality_floors` is `null` or contains a non-null `request.complexity.quality_floor`;
`hard_constraints` is `any`, or `present` with a known non-empty list, or `absent` with a known
empty list (a `null` list matches only `any`); `leaf_kinds` is `null` or contains a non-null
`request.dispatch.leaf_kind`; and `levels` has the key `request.harness`. A rule's value is
`levels[request.harness]`.

### DM-3 Qualification reference

```json
{"report": "/abs/report.json", "report_sha256": "<64 hex>",
 "manifest": "/abs/manifest.json", "manifest_sha256": "<64 hex>",
 "candidate": "B", "baseline": "A"}
```

Paths are absolute; digests 64 lowercase hex; variant ids match `^[A-F][a-z0-9-]{0,15}$`
(spec 09 DM-6). The 1,048,576-byte limit of check 1 is this spec's own: spec 09 sets no size
limit on `report.json`. A report or manifest above it is rejected as unreadable evidence
(`qualification-invalid`) and the rule applies no lowering; this is a documented limit, not a
defect, and the conservative reading. For a rule with value `v` evaluated for request harness `h`, the reference
verifies when all hold:

1. Both files are regular files of at most 1,048,576 bytes whose SHA-256 equals the given
   digest, and both parse as JSON with `schema_version` `1`.
2. The report has `kind` `"observed"`, its `experiment_id` equals the manifest's, and its
   `comparisons` contains an element with equal `candidate` and `baseline` and `verdict`
   `"promote"` (spec 09 DM-12 and Promotion rule).
3. The manifest's `variants` contains the candidate and the baseline, both with `adapter`
   equal to `h`; for every role `r` in the rule's `match.roles`, the candidate's
   `roles[r].effort` equals `v` and the baseline's `roles[r].effort` equals
   `"session-default"` (spec 09's value for a run whose CLI invocation omits `--effort`, 09 DM-8;
   the counterpart of this spec's `harness-default`), and both variants have the same `roles[r].model`.

Any other result is `qualification-invalid`. The reference records the owner's adoption of a
promoted variant; it relies on spec 09 REQ-53 and its manifest definition, whose `roles` has
exactly the keys `orchestrator`, `arbiter`, `implementer` and `validator`, each with `model`
and `effort`, and whose `adapter` is `claude` or `null` (C-6). This check reads only the keys
named in the rule's `match.roles` (a subset of `arbiter`, `implementer`, `validator`); the
`orchestrator` key is required by spec 09 but ignored here, and its effort is never compared.
**Uniform-effort limitation.** Spec 09 gives an `executable` variant one effort for every role
(the orchestrator included), so an executable candidate changes the roles outside the rule's
`match.roles` as well. A rule that matches only some roles is therefore qualified with a
`recorded` variant (a `manual` variant is never measured, so it never reaches `promote`; 09
REQ-06), or with an executable candidate whose uniform effort is the
rule's value `v`; check 3 still compares only the matched roles. Since 09's `adapter` admits
only `claude` or `null`, a `codex` rule has no verifying reference of any availability, and a
recorded or manual variant verifies only when its manifest sets `adapter` to the request
harness.

### DM-4 `effort-input:` line (extends `## Model Selection`)

Written by the model-selection workflow, one line per current leaf, after the leaf's existing
checkpoint lines:

```text
effort-input: <leaf_id> floor <1-5> hard <none|c1,c2> recommended <token|not-configurable|none> for <model identity>
```

Pattern: `^effort-input: (T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?) floor [1-5] hard (none|[a-z-]+(,[a-z-]+)*) recommended ([A-Za-z0-9][A-Za-z0-9._-]{0,31}|not-configurable|none) for ((anthropic|openai)/[^\s|;]{1,256}|session-default)$`.
`floor` is the helper's `quality_floor` (`scripts/model_selection.py:106`, reported at
`:366`); `hard` lists the leaf's hard constraints in `HARD_CONSTRAINTS` order
(`scripts/model_selection.py:29`); `recommended` is the reasoning recommendation already
recorded for that leaf (`none` when the record holds no single level); `for` is the identity
the recommendation was made for. Existing checkpoint lines are unchanged. Legacy checkpoints
without these lines remain valid (REQ-16, REQ-36).

### DM-5 `## Effort Decisions` (task `state.md`, protected, append-only)

Created by the dispatcher on the first DM-5 line of the task, after the last existing section.
Lines are appended and never edited, reordered or removed. Exactly three line forms, each a
full-line match:

```text
DECISION    ^- (?P<key>KEY) \| (claude|codex) \| (arbiter/context|implementer/execution|validator/validation) \| model (MODEL) \| outcome (requested|not-requested|stop) \| requested (TOKEN|harness-default) \| resolved (TOKEN|none) \| source (baseline|recommendation|policy-target|policy-minimum|escalation) \| policy ([a-z0-9][a-z0-9-]{0,63}@[0-9]+(\.[0-9]+){0,3}|none) \| reasons ([a-z-]+(,[a-z-]+)*|none)$
REJECTION   ^- (?P<key>KEY) \| rejected-by-harness$
UNAVAILABLE ^- (?P<key>KEY) \| (claude|codex) \| (arbiter/context|implementer/execution|validator/validation) \| model (MODEL) \| outcome (requested|not-requested) \| requested (TOKEN|unknown) \| resolved (TOKEN|none) \| source none \| policy none \| reasons ([a-z-]+,)*resolver-unavailable(,[a-z-]+)*$
```

with `KEY` = `(T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?|task)\.(arbiter|implementer|validator)\.[1-9][0-9]*`,
`MODEL` = `(anthropic|openai)/[^\s|;]{1,256}|session-default`, `TOKEN` =
`[A-Za-z0-9][A-Za-z0-9._-]{0,31}`.

- Key: `<scope>.<role>.<n>`; `<scope>` is the leaf id or `task` for the Arbiter; `<n>` = 1 +
  the number of existing DECISION and UNAVAILABLE lines with the same scope and role.
- DECISION mapping from DM-7: harness ← `harness`; `<role>/<stage>` ← `dispatch.role` and
  `dispatch.stage`; model ← `model`; outcome ← `outcome`; requested ← `requested`; resolved ←
  `resolved` or `none`; source ← `source`; policy ← `policy.policy_id@policy.policy_version`
  or `none`; reasons ← `reasons` joined by `,` in DM-7 order, or `none` when empty.
- UNAVAILABLE mapping (REQ-39, REQ-41): the dispatcher writes it without a DM-7 document.
  Outcome `requested` goes with `requested` equal to `resolved`, both the level sent; outcome
  `not-requested` goes with `requested unknown` and `resolved none`. `source` and `policy` are
  always `none`. `reasons` lists the C-3 codes of the decision, `resolver-unavailable`, and the
  cause code, in C-2 order. The grammar is a backward-compatible widening of the earlier form: a
  line `outcome not-requested | requested unknown | resolved none | ... | reasons
  resolver-unavailable` still matches, and readers treat the cause code as optional on such
  earlier lines; lines written under REQ-41 always carry it.
- A REJECTION line follows the DECISION line it refers to and repeats its key.

### DM-6 Resolver request (`--request FILE`)

```json
{"schema_version": 1, "harness": "claude", "model": "anthropic/example-model",
 "dispatch": {"role": "implementer", "stage": "execution", "scope": "T-03", "leaf_kind": "ordinary"},
 "complexity": {"quality_floor": 4, "hard_constraints": []},
 "recommendation": {"value": "high", "for": "anthropic/example-model"},
 "escalation": null,
 "session": {"parameter": "exposed", "values": ["low", "medium", "high"]}}
```

| Field | Rule |
|---|---|
| `harness` | `claude` or `codex`; must equal the `--capabilities` file's parent directory name |
| `model` | Model identity of the spawn: the identity resolved under `### Model columns and resolution`, or `session-default` when no model override is passed |
| `dispatch.role` / `stage` | Exactly `arbiter`/`context`, `implementer`/`execution`, or `validator`/`validation` |
| `dispatch.scope` | `task` iff role `arbiter`; otherwise a leaf id (DM-4 leaf pattern) |
| `dispatch.leaf_kind` | `null` iff role `arbiter`; otherwise `fix` when the scope contains `-fix-`, else `ordinary` (a mismatch is invalid) |
| `complexity.quality_floor` | Integer 1–5 or `null`; must be `null` for the Arbiter |
| `complexity.hard_constraints` | `null` or unique names from `HARD_CONSTRAINTS`; must be `null` for the Arbiter |
| `recommendation` | `null`, or `{"value": token or "not-configurable", "for": model identity}`; must be `null` unless role `implementer` |
| `escalation` | `null` or `{"value": token, "reference": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"}` |
| `session.parameter` | `exposed`, `absent` or `unknown`; `values` is a non-empty unique token array or `null`, and must be `null` unless `exposed` |

### DM-7 Decision (stdout of `resolve`)

Canonical JSON: sorted keys, `ensure_ascii=False`, separators `,` `:`, one trailing LF.

| Field | Value |
|---|---|
| `schema_version`, `kind` | `1`, `"effort_decision"` |
| `harness`, `model`, `dispatch` | Copied from the request |
| `baseline` | Token or `"harness-default"` (step 2) |
| `requested` | Token or `"harness-default"` |
| `source` | Source of `requested` (C-2) |
| `resolved` | Token or `null` |
| `actual` | `"unknown"` |
| `outcome` | `requested`, `not-requested` or `stop` |
| `reasons` | Unique C-2 codes sorted by their C-2 table order |
| `rules` | Sorted `rule_id`s per C-3 → Rule listing |
| `policy` | `null` when the policy is absent, not used or invalid; otherwise `{"policy_id", "policy_version", "sha256"}` (SHA-256 of the file bytes) |
| `capability` | `{"state": "yes"|"no"|"unknown"|"invalid", "runtime": string|null, "verified": string|null}` |
| `dimension_source` | C-5 string |

No path, file content or qualification file path appears in the decision.

## Contracts & Interfaces

### C-1 Command line

```text
python3 -I scripts/effort-policy.py resolve --capabilities FILE (--policy FILE | --no-policy) --request FILE
python3 -I scripts/effort-policy.py check-policy --policy FILE [--capabilities FILE]
```

- A `--policy FILE` path that does not exist means "policy absent" (reason `policy-absent`);
  `--no-policy` adds reason `policy-not-used`. Repeated, missing or unknown options, or both
  `--policy` and `--no-policy` → exit 2.
- `check-policy` prints one canonical JSON document `{"schema_version":1,"kind":
  "effort_policy_check","valid":bool,"policy":{"policy_id","policy_version","sha256","rules":
  <count>}|null,"errors":[{"code","detail","rule_id"}]}`. Error codes: `policy-absent` (file
  missing), `policy-invalid` (any DM-2 violation; `detail` names the JSON path), and, with
  `--capabilities`, `value-not-declared` (a rule value for that harness absent from its
  declared values, or the section not `state: yes`). `rule_id` is the rule's id or `null`.
  `errors` is sorted by code, then by `rule_id` with `null` first, then by `detail`.
- The helper checks `sys.version_info >= (3, 11)` before any other work and exits 3 otherwise;
  so that this check, not a syntax error, decides on an older interpreter, the entry file as a
  whole uses only syntax older Python 3 interpreters parse and loads any 3.11-only code after the
  check (spec 20 A-26: entry module plus path-loaded engine).

### C-2 Exit codes, sources and reason codes

| Exit | Meaning |
|---|---|
| 0 | `resolve`: decision with outcome `requested` or `not-requested`. `check-policy`: valid |
| 1 | `resolve`: decision with outcome `stop`. `check-policy`: not valid |
| 2 | Invalid arguments or request; stdout empty; stderr one line `invalid-arguments: <detail>` or `invalid-request: <JSON path>` without file contents |
| 3 | Python older than 3.11; stderr `unavailable: python` |

Sources: `baseline`, `recommendation`, `policy-target`, `policy-minimum`, `escalation`.

Reason codes, in this order: `policy-absent`, `policy-not-used`, `policy-invalid`,
`policy-conflict`, `recommendation-unavailable`, `recommendation-model-mismatch`,
`recommendation-not-configurable`, `recommendation-precedes-target`, `owner-raise`,
`rule-qualified`, `rule-unqualified`, `qualification-invalid`, `minimum-raised`,
`minimum-unverifiable`, `minimum-unsatisfied`, `escalation-raised`,
`escalation-unverifiable`, `harness-default`, `capability-invalid`, `capability-unknown`,
`capability-unsupported`, `value-not-declared`, `session-only-recommendation`,
`session-unknown`, `session-parameter-absent`, `session-value-absent`, `resolver-unavailable`,
`resolver-python`, `resolver-missing`, `resolver-failed` (the last four DM-5 UNAVAILABLE only).

**Unusable-resolver output.** An unusable resolver prints no DM-7 document; the only
machine-readable signal is exit 3 with stderr `unavailable: python` (above). The dispatcher
derives the cause code of the DM-5 UNAVAILABLE line from what it observed: `resolver-python`
(exit 3 with that stderr line), `resolver-missing` (the interpreter or `scripts/effort-policy.py`
cannot be started or found), `resolver-failed` (anything else: exit 2, any other exit code, a
crash, a kill by the tool's own command time limit, or stdout that is not a DM-7 document). The
UNAVAILABLE line is therefore this contract's output for an unusable resolver, and carries what
the dispatcher needs: the decision it took under REQ-39 and the cause.

### C-3 Resolution algorithm

Let `cap` be `invalid` (REQ-31), or the section's `state`. Let `V` be the declared values when
`cap` is `yes`, else empty. `rank(x)` is the index of `x` in `V` when `order: ascending` and
`x ∈ V`; `rank("harness-default")` is `rank(default)` when `default` is a token, else
undefined; every other rank is undefined. `a` is **provably at least** `b` when `a == b`, or
both ranks are defined and `rank(a) ≥ rank(b)`. `a` is **provably lower** than `b` when both
ranks are defined and `rank(a) < rank(b)`.

1. **Policy.** Load the policy unless absent or `--no-policy` (adding `policy-absent` or
   `policy-not-used`). Invalid → mark stop with `policy-invalid` and treat the rule set as
   empty. Otherwise compute the matching rules (DM-2); if two matching rules of the same kind
   have different values → mark stop with `policy-conflict` and treat the rule set as empty.
   Continue with step 2 in every case.
2. **Baseline.** For an Implementer: `recommendation: null` → `harness-default`, source
   `baseline`, add `recommendation-unavailable`; `for` ≠ `model` → `harness-default`, source
   `baseline`, add `recommendation-model-mismatch`; value `not-configurable` →
   `harness-default`, source `baseline`, add `recommendation-not-configurable`; otherwise the
   recommended token, source `recommendation`. Arbiter and Validator: `harness-default`, source
   `baseline`. Set `baseline` and `requested` to this value.
3. **Target.** Let `T` be the matching target rules (all have one value `v`). If `T` is
   non-empty: when the source is `recommendation`, keep it and add
   `recommendation-precedes-target`. Otherwise:
   a. `v` provably at least `requested` → set `requested = v`, source `policy-target`;
   b. else if some rule in `T` has `owner_raise: true`, `order: ascending` holds and `v` is the
      last element of `V` → set `requested = v`, source `policy-target`, add `owner-raise`;
   c. else if some rule in `T` has a `qualification` that verifies (DM-3) → set
      `requested = v`, source `policy-target`, add `rule-qualified`;
   d. else keep `requested`; add `qualification-invalid` when some rule in `T` has a
      `qualification`, otherwise `rule-unqualified`.
4. **Minimum.** Let `M` be the matching minimum rules (one value `m`). If non-empty:
   `requested` provably lower than `m` → `requested = m`, source `policy-minimum`, add
   `minimum-raised`; `requested` provably at least `m` → no change; otherwise no change and add
   `minimum-unverifiable`.
5. **Escalation.** If `escalation` is non-null with value `e`: the same three branches as step
   4 with source `escalation` and codes `escalation-raised` / `escalation-unverifiable`.
6. **Gate.** If a stop is marked, set `resolved: null` and skip to step 7. If
   `requested == "harness-default"` → `resolved: null`, `not-requested`, add
   `harness-default`. Otherwise evaluate in order; the first failing check adds its code and
   gives `resolved: null`, `not-requested`:
   a. capability: `cap` = `no` fails (`capability-unsupported`). `cap` = `invalid` or
      `unknown` adds `capability-invalid` / `capability-unknown`; it fails unless `source` is
      `recommendation`, in which case add `session-only-recommendation` and go to c.
   b. declaration (`cap` = `yes`): `requested ∉ V` fails (`value-not-declared`).
   c. session: `parameter` `unknown`, or `exposed` with `values: null`, fails
      (`session-unknown`); `absent` fails (`session-parameter-absent`); `requested ∉ values`
      fails (`session-value-absent`).
   All pass → `resolved = requested`, `outcome: requested`.
7. **Enforcement and output.** If a stop is marked → `outcome: stop`. Otherwise, for every
   matching minimum rule with `enforce: true`, if the effective effort (`resolved`, or
   `harness-default` when `resolved` is `null`) is not provably at least `m` → `outcome: stop`,
   `resolved: null`, add `minimum-unsatisfied`. Print DM-7; exit per C-2.

**Rule listing (`rules`).** The ids of: every rule in `T` when step 3 set `requested`
(branches a–c); every rule in `M` when step 4 raised; the two or more conflicting rules on
`policy-conflict`; every enforced minimum rule that caused `minimum-unsatisfied`. Empty
otherwise, and always empty on `policy-invalid`.

### C-4 Dispatcher procedure (state-files contract → `### Reasoning effort resolution`)

1. **When.** Immediately before each spawn or recreation of an Arbiter (`/spec-run` Step 1), an
   Implementer (4.2, after model resolution), a Validator (4.3), or the leaf worker spawned by
   the single-session executor (`execution-execute`, or `atomic-execution` when invoked
   directly), always with role `implementer` and stage `execution`. Only the process that
   performs the spawn resolves: a worker that itself runs `atomic-execution` inline makes no
   decision. Not for messages to a live worker, inline execution or `/spec-run --dry-run`.
2. **Request.** Harness: `claude` under Claude Code, `codex` under Codex (the `harness/`
   directory names); any other harness takes the REQ-14 path. Model: the identity resolved
   for the spawn, or `session-default`. Complexity: the leaf's DM-4 line for Implementer and
   Validator spawns; without it, and for the Arbiter, `null` (REQ-16). Recommendation
   (Implementer only, `null` otherwise): from the DM-4 line — `recommended none` gives `null`,
   otherwise `{"value": <recommended>, "for": <for>}`; without a DM-4 line, `null` (REQ-36).
   Session: REQ-35. Escalation: `null` unless supplied by spec 19.
3. **Run.** With the verified `SOURCE_ROOT` of `### Model columns and resolution`:
   `python3 -I "$SOURCE_ROOT/scripts/effort-policy.py" resolve --capabilities
   "$SOURCE_ROOT/harness/<harness>/capabilities.md" --policy <DM-2 path> --request <file>`
   (`--no-policy` when `ORCHESTRAIL_EFFORT_POLICY` is set to a value other than empty or `on`). The request file is a temporary file outside the project,
   removed afterwards.
4. **Interpret.** Exit 0 or 1 with stdout that parses as a DM-7 document → step 5. Anything
   else (interpreter or helper missing, exit 2, exit 3, other exit codes, unparsable stdout) →
   REQ-14.
5. **Record and report.** Append the DM-5 DECISION line (REQ-09) and report (REQ-33).
6. **Act.** `requested` → pass `resolved` as the spawn tool's effort parameter (DM-1
   `parameter`, or the parameter observed under REQ-35). `not-requested` → spawn without an
   effort parameter. `stop` → **stop**: "Effort decision <key> stopped the spawn: <reasons>.
   Correct or disable the policy (set ORCHESTRAIL_EFFORT_POLICY=off, or move <policy path>
   aside) and resume."
7. **Rejection.** REQ-10. Spawn failures that do not name the effort parameter or value follow
   the existing spawn-failure handling and add no DM-5 line.
8. **Unusable resolver.** REQ-14; stop message: "Effort policy present but the effort resolver
   is unusable: <cause>. Restore Python 3.11+ and the helper, or disable the policy, and
   resume." (REQ-40: no fallback, and no DM-5 line.) With no policy file, or with the disable
   switch in effect, apply today's rule (REQ-39), append the UNAVAILABLE line (REQ-41), report it
   and spawn with the level that rule sends or without an effort parameter. A harness rejection
   of that level (REQ-10) appends the rejection line and the next spawn re-runs this step with
   `session.parameter: "absent"`, which sends no parameter.

The subsection also states that adding effort to Arbiter and Validator spawns leaves them
session-default *model* roles: ADR-0015 Decision 3 concerns model identity, and effort is
recommended separately from model identity (`docs/MODEL-CATALOG.md:84`).

**Capability row** (REQ-24), in the header of spec 13 DM-4's behaviour table:

```text
| Policy- or escalation-chosen reasoning effort for a spawned worker | `spec-run`, `atomic-execution`, `execution-execute` | `sub-agent-effort` | While the record is `unknown` or absent, send only a session-observed leaf recommendation; otherwise, including `state: no`, spawn without an effort parameter and record outcome not-requested |
```

The narrowed Behaviour cell keeps 13 REQ-16 (a `no`, `unknown` or undeclared capability takes the
"Without it" path) consistent with REQ-37, under which a session-observed recommendation is still
sent while the record is `unknown` (C-3 step 6a refuses it for `state: no`).

### C-5 Effort dimension source (exposed to spec 05)

`dimension_source` = `requested:<harness>:<resolved token>` when `outcome` is `requested`,
otherwise `requested:<harness>:none`. It labels the requested configuration, never the actual
one. A spec-05 producer that attributes a spawn's usage maps this string to the opaque
`effort` dimension value through its keyed mapping (`scripts/usage_telemetry_adapter.py:20-24`;
values must be `sha256:` identifiers, `scripts/usage_telemetry_contract.py:350-353`,
`:2911-2915`; ADR-0016 Decision 3, last paragraph). This spec writes no telemetry record.

### C-6 Contracts with other specs

| Spec | Relationship |
|---|---|
| 04 (completed) | Consumed: `quality_floor`, `HARD_CONSTRAINTS`, the reasoning recommendation and model resolution, unchanged. Extended additively: DM-4 lines in the model-selection workflow |
| 05 (completed) | Consumed: none required. Exposed: C-5. Needed for actual effort (not required here): a source-profile parameter for observed effort in a new schema version of 05's contract; until then actual stays `unknown` |
| 09 | Consumed: DM-12 `report.json` fields `kind`, `experiment_id` and `comparisons[].candidate`, `baseline`, `verdict`, and DM-6 manifest `variants[].roles[].effort`/`model`/`adapter` (DM-3). Aligned with 09 REQ-53: `roles` has exactly `orchestrator`, `arbiter`, `implementer`, `validator`; 18 reads the last three and ignores `orchestrator`. The uniform-effort limitation of executable variants is stated in DM-3. 09 sets no `report.json` size limit; DM-3's limit is 18's own |
| 12 | Exposed: DM-6 and C-3. Parallel-mode spawns (leaf coordinators, phase agents, per-workflow agents with 12's stages `tests`, `implement`, `finalize`, `check`, `propose`, `close`) are outside policy version 1 (12 A-27 says the same): they keep today's dispatch behaviour, with no effort parameter and no `## Effort Decisions` line, and policy version 1 and its DM-2/DM-6 enums stay as written. The amendment 12 requires (the three roles and the stages added to DM-2/DM-6, the root named as the only writer of `## Effort Decisions` in C-4) is a later change to this spec, made by a revision of 18 triggered by 12's delivery; see A-29 for who makes it |
| 13 | Consumed: DM-4 record grammar and extension-record convention; file and section names (Notes → Name mapping and Files and sections created after this spec); the behaviour table; REQ-67, which admits a declared capability record name such as `sub-agent-effort` in a `Requires` cell (Q-01 resolved) |
| 15 | Consumed: none. DM-2 `checkpoint_attempt` is not amended: it exists only on the helper route and for Implementer and Validator, is written once before the spawn, and cannot carry a later rejection; DM-5 covers every route and role. 15's C-10 row 18 records that DM-2 is not used |
| 16 | Consumed: none in policy version 1. 16's C-6 row for 18 offers `tier`, `risks`, `scope` and `expansion_reasons`; policy version 1 reads none of them, and a later policy version may add a match key |
| 19 | Exposed: the DM-6 `escalation` input, C-3 steps 5–7 and the codes `escalation-raised` and `escalation-unverifiable`, and outcome `not-requested`; agreed with 19 C-8 step 3 and C-10 row 18. 19 owns when to escalate and what to do with an `escalation-unverifiable` or `not-requested` result (no substitution of another model or effort); a spec 18 `stop` stays 18's own. Without 19 the request's `escalation` is `null` (C-4 step 2) |
| 20 | Exposed: nothing new. 20 REQ-29 produces no complexity value; the complexity input `{quality_floor, hard_constraints}` stays produced by `/pd-select-model` through DM-4's `effort-input:` line |

### C-7 Acceptance suite

`python3 -I scripts/check-effort-policy.py` builds a temporary directory with fixture
capability files, policy files, spec-09-shaped reports and manifests and requests; runs
`scripts/effort-policy.py` as a subprocess (`python3 -I`) and, for AC-05 and AC-15, also
in-process with `runpy.run_path` and patched standard-library functions; reads, never edits,
the repository's workflows, rules, harness files, guide, `scripts/README.md` and ADR index for
the contract cases; prints one line per AC case and exits 0 only when every case passes. It
implements the DM-5 mapping and regexes itself. It is not referenced by
`scripts/validate-contracts.sh` or `scripts/sync.sh`.

### C-8 Shared acceptance gates

| Gate | How this spec meets it |
|---|---|
| G1 Attribution | DM-5 records harness, model identity, role/stage and a per-scope spawn number; C-5 labels usage for 05; actual stays `unknown` |
| G2 Comparable measurement | No measurement claim is made; comparisons belong to 09 (DM-3) |
| G3 Independent quality | No change to test-first order, RED/GREEN in one Implementer, Validator independence, git rails or owner stops (C-4 step 1) |
| G4 Compatibility | Legacy plans and checkpoints readable (REQ-16, REQ-36); unknown capability uses the harness default or the session-only recommendation (REQ-37); invalid policy stops before mutation (REQ-11); no model substitution (Out of Scope; REQ-04) |
| G5 Ownership | The resolver writes nothing and spawns nothing; only the dispatcher writes `## Effort Decisions` |
| G6 Testing | AC fixtures written first; no paid run in resolution, checks, sync or validation (NFR-07) |
| G7 Rollback | Notes → Rollback; disable switch (REQ-21); recorded lines kept |
| G8 Economics | No cheaper default without a qualified comparison (REQ-06); no cost or time cap introduced |

## Non-Functional Requirements

| Id | Attribute | Target or standard | Verification |
|---|---|---|---|
| NFR-01 | Determinism | Byte-identical stdout for identical inputs (REQ-19) | AC-05 |
| NFR-02 | Isolation | No socket, subprocess or file write by the resolver (REQ-19) | AC-05 |
| NFR-03 | Portability | Python 3.11+ standard library only, `-I` mode; exit 3 below 3.11 | AC-15 (exit 3 case), review of imports |
| NFR-04 | Bounded input | 1,048,576 bytes per read file; 256 rules | AC-06 |
| NFR-05 | Performance | N/A — no owner target exists and none is invented | — |
| NFR-06 | Privacy | Decisions and stderr carry no file contents or paths | AC-04, AC-15 |
| NFR-07 | Cost | No provider call or paid run in resolution, checks, sync or validation (G6) | AC-05 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| No policy file | Baseline; `policy-absent` | REQ-08 |
| Empty `rules` array | Valid; baseline | REQ-08 |
| Policy not UTF-8 JSON, duplicate key, unknown key, missing `match` key, >1 MiB, >256 rules | Stop `policy-invalid` | REQ-11 |
| Two target rules match with equal values | No conflict; both listed when applied | REQ-12, C-3 |
| Two minimum rules match with different values | Stop `policy-conflict`; both listed | REQ-12 |
| Rule for `codex` only, spawn on `claude` | Rule does not match | REQ-01 |
| Unknown floor, rule `quality_floors: [1,2]` | No match | REQ-01, REQ-16 |
| Target value lower than recommendation | Recommendation kept; `recommendation-precedes-target` | REQ-03 |
| Target over `harness-default` with `default: unknown`, no owner raise, no qualification | Baseline kept; `rule-unqualified` | REQ-06 |
| Owner raise on a value that is not the top value, or with `order: unknown` | No raise; falls to qualification or `rule-unqualified` | REQ-06 |
| Qualification report changed after referencing | Hash mismatch; `qualification-invalid` | REQ-06 |
| Qualification verdict `insufficient-data`, or variants differ in model | `qualification-invalid` | REQ-06 |
| Minimum over `harness-default` with unknown default | `minimum-unverifiable`; with `enforce: true` stop | REQ-03, REQ-13 |
| `order: unknown`, two different tokens | Only equality is provable | REQ-03 |
| Section `state: yes` but value not declared | `value-not-declared` | REQ-04 |
| Capability `unknown`, recommendation exposed by the session | Requested (today's behaviour); `capability-unknown`, `session-only-recommendation` | REQ-37 |
| Capability `unknown`, target rule with a verifying qualification | `capability-unknown`, not-requested | REQ-04 |
| Capability `unknown`, target rule without qualification over `harness-default` | `rule-unqualified`, `harness-default`, not-requested | REQ-06 |
| Session shows parameter without enumeration | `session-unknown` | REQ-04, REQ-35 |
| Capability file missing or malformed | `capability-invalid` | REQ-31 |
| Recommendation made for another model | Baseline `harness-default` | REQ-17 |
| Recommendation `not-configurable` | Baseline `harness-default` | REQ-18 |
| Legacy leaf without DM-4 line | Recommendation `null`; `recommendation-unavailable`; rerun bulk selection restores it | REQ-36, REQ-38 |
| Harness refuses the spawn because of the parameter | Rejection line; new spawn with `absent`; no other value tried | REQ-10 |
| Harness refuses the spawn for another reason | Existing spawn-failure handling; no DM-5 line | REQ-10 |
| Interrupted between decision line and spawn | On resume the next spawn is a new spawn `<n+1>`; the earlier line is kept | REQ-09 |
| RED continuation, Arbiter question | No decision | REQ-05 |
| Recreated Implementer after resume | New decision; the RED/GREEN rule of the orchestration contract is unchanged | REQ-05 |
| Resolver exits 2, 3, other code, or prints non-JSON | REQ-14 path | REQ-14 |
| Same, no policy file (or disable switch in effect), Implementer with a recommendation the session exposes | Today's rule: level sent; UNAVAILABLE line `requested`/`resolved` the level | REQ-39, REQ-41 |
| Same, no policy file, any other spawn or session state | Today's rule: no parameter; UNAVAILABLE line `not-requested` | REQ-39, REQ-41 |
| Same, policy file exists (valid or malformed), switch not in effect | Stop; no fallback; no DM-5 line | REQ-14, REQ-40 |
| Same, no policy file, non-null escalation | Escalation not applied; `escalation-unverifiable` in the UNAVAILABLE line | REQ-39 |
| `ORCHESTRAIL_EFFORT_POLICY=off` | `--no-policy`; gate still applies | REQ-21 |
| Escalation with no policy | Applied by step 5; REQ-08 does not apply | REQ-29 |
| Malformed request (Validator with recommendation, unknown stage) | Exit 2 | REQ-30 |
| Concurrent writers to `## Effort Decisions` | Not possible: only the single dispatcher of a run writes (P4) | REQ-09 |
| Legacy task without `## Effort Decisions` | Readers tolerate absence; first line creates the section | REQ-09 |
| Escalation value not declared | `escalation-unverifiable`, then the gate decides | REQ-29 |

## Acceptance Criteria

Each case runs inside `scripts/check-effort-policy.py` against fixtures. Unless stated, the
capability fixture is `state: yes`, values `e1, e2, e3`, `order: ascending`, `default: e2`,
`parameter: effort`, and the session is `exposed` with `["e1","e2","e3"]`.

- **AC-01** (REQ-01, REQ-03) — Given the fixture capability and the requests below, when
  `resolve` runs, then each decision's `requested`, `source`, `outcome` and `rules` equal the
  row and its `reasons` contain the listed codes (plus `policy-absent`/`policy-not-used` only
  where the row says no policy):

  | # | Request and policy | requested | source | outcome | rules | reasons include |
  |---|---|---|---|---|---|---|
  | 1 | Implementer, recommendation `e1` for its model; target rule `t1` (implementer, value `e3`) | `e1` | recommendation | requested | — | `recommendation-precedes-target` |
  | 2 | Validator; target `t1` (validator, `e3`) | `e3` | policy-target | requested | `t1` | — |
  | 3 | Validator; capability `default: unknown`; target `t1` (validator, `e3`) | `harness-default` | baseline | not-requested | — | `rule-unqualified`, `harness-default` |
  | 4 | As 3 with `owner_raise: true` | `e3` | policy-target | requested | `t1` | `owner-raise` |
  | 5 | Validator; target `t1` (validator, `e1`) with a verifying qualification | `e1` | policy-target | requested | `t1` | `rule-qualified` |
  | 6 | Implementer, recommendation `e1`; minimum `m1` (implementer, `e2`, `enforce: false`) | `e2` | policy-minimum | requested | `m1` | `minimum-raised` |
  | 7 | Validator; `default: unknown`; minimum `m1` (validator, `e2`) | `harness-default` | baseline | not-requested | — | `minimum-unverifiable` |
  | 8 | Arbiter; target `t1` (roles `["arbiter"]`, value `e3`, `quality_floors: [4]`) | `harness-default` | baseline | not-requested | — | `harness-default` |
  | 9 | Implementer floor 5, hard `["security"]`; minimum `m1` (`quality_floors: [5]`, `hard_constraints: "present"`, `e3`), recommendation `e2` | `e3` | policy-minimum | requested | `m1` | `minimum-raised` |
  | 10 | Fix leaf `T-04-fix-x`; target `t1` with `leaf_kinds: ["ordinary"]`, validator | `harness-default` | baseline | not-requested | — | `harness-default` |

- **AC-02** (REQ-02, REQ-04, REQ-31, REQ-35, REQ-37) — Given these requests, when `resolve`
  runs, then each has the listed `outcome`, `resolved` and gate code, and every non-null
  `resolved` equals its `requested`:

  | # | Request, capability and session | outcome | resolved | gate code (exactly one) |
  |---|---|---|---|---|
  | 1 | Validator, target `t1` (validator, `e3`); fixture | requested | `e3` | — |
  | 2 | As 1; session values `["e1","e2"]` | not-requested | `null` | `session-value-absent` |
  | 3 | As 1; session `absent` | not-requested | `null` | `session-parameter-absent` |
  | 4 | As 1; session `unknown` | not-requested | `null` | `session-unknown` |
  | 5 | As 1; session `exposed`, `values: null` | not-requested | `null` | `session-unknown` |
  | 6 | Implementer, recommendation `e3` for its model; capability values `e1, e2` (`default: e2`) | not-requested | `null` | `value-not-declared` |
  | 7 | As 6 with capability `state: no` (values `none`) | not-requested | `null` | `capability-unsupported` |
  | 8 | Validator, target `t1` (validator, `e3`) with a verifying DM-3 qualification; capability `state: unknown` | not-requested | `null` | `capability-unknown` |
  | 9 | As 8 with a malformed section (`order: ascending` with one value) | not-requested | `null` | `capability-invalid` |
  | 10 | As 8 with no `## sub-agent-effort` section | not-requested | `null` | `capability-invalid` |
  | 11 | Implementer, recommendation `e3` for its model; capability `state: unknown`; session exposes `e3` | requested | `e3` | — (reasons include `capability-unknown`, `session-only-recommendation`) |

- **AC-03** (REQ-05, REQ-09, REQ-10, REQ-16, REQ-33, REQ-35, REQ-36) — Given the delivered
  `### Reasoning effort resolution`, then it states: one resolver run per spawn or recreation;
  no decision for messages to a live worker; the request sources of C-4 step 2 including the
  `null` complexity and recommendation cases and the REQ-35 session observation; appending the
  DM-5 line before spawning; the REQ-33 report line; passing only `resolved`; and the rejection
  procedure with `session.parameter: "absent"`. And given each DM-7 fixture decision of AC-01,
  AC-02, AC-06 and AC-07, the suite's DM-5 mapping produces a line matching the DECISION regex,
  and a fixture rejection line matches the REJECTION regex.
- **AC-04** (REQ-06, REQ-07) — Given a Validator target `e1` under the fixture capability, when
  `resolve` runs with no qualification, with a report whose digest differs, with verdict
  `insufficient-data`, with a manifest whose candidate's validator effort is `e2`, with a
  manifest whose variants differ in validator model, and with a verifying reference, then the
  first keeps the baseline with `rule-unqualified`, the next four keep it with
  `qualification-invalid`, and the last applies the rule with `rule-qualified`; every decision
  has `actual: "unknown"`, a C-5 `dimension_source`, no numeric value other than
  `schema_version`, and no fixture path.
- **AC-05** (REQ-08, REQ-19, REQ-21) — Given a missing policy path and, separately,
  `--no-policy`, when `resolve` runs for an Implementer with recommendation `e2` for its model
  and for a Validator, then `requested` equals `e2` and `harness-default`, and `resolved` equals
  `e2` and `null`, respectively; the same holds with `state: unknown` and the session exposing
  `e2` (Implementer `resolved: "e2"`); running each request twice yields byte-identical stdout;
  in-process runs with `socket.socket`, `subprocess.Popen`, `os.system` and `open` in a write
  mode patched to raise complete with exit 0; and the delivered C-4 text states that
  any `ORCHESTRAIL_EFFORT_POLICY` value other than empty or `on` (documented `off`) selects
  `--no-policy`.
- **AC-06** (REQ-11, REQ-12) — Given policy files that are invalid UTF-8, contain a duplicate
  key, an unknown key, 257 rules, 1,048,577 bytes, or a `target` with `enforce`, and a policy
  with two matching minimum rules `m1` `e1` and `m2` `e3`, when `resolve` runs, then each exits
  1 with `outcome: "stop"`, `resolved: null`, a `baseline` computed by step 2, and reason
  `policy-invalid` with `rules: []` (the first six) or `policy-conflict` with
  `rules: ["m1","m2"]` (the last).
- **AC-07** (REQ-13, REQ-34) — Given an enforced minimum `e3` for validators and (a) the
  fixture, (b) session values `["e1","e2"]`, (c) `order: unknown`, (d) `default: unknown`
  with no other rule, when `resolve` runs, then (a) exits 0 with `outcome: requested`,
  `resolved: "e3"`, and (b)–(d) exit 1 with `outcome: stop`, `resolved: null` and
  `minimum-unsatisfied`; and the delivered C-4 text contains the stop message and forbids the
  spawn on `stop`.
- **AC-08** (REQ-14, REQ-40) — Given the delivered C-4 text, then it maps every non-DM-7 result
  to the REQ-14 path, stops when an enabled policy file exists (valid or malformed) without a
  fallback and without a DM-5 line, and otherwise applies REQ-39 (amended 2026-11-14: it
  formerly spawned without a parameter); and a fixture earlier-form UNAVAILABLE line (`outcome
  not-requested`, `requested unknown`, `resolved none`, `reasons resolver-unavailable`) matches
  its DM-5 regex.
- **AC-09** (REQ-15, REQ-16) — Given the delivered model-selection workflow, then its selection
  checkpoint text requires one DM-4 line per current leaf and contains the DM-4 pattern; and
  given a request with `quality_floor: null` and `hard_constraints: null`, then a rule with
  `quality_floors: null` and `hard_constraints: "any"` matches and rules with
  `quality_floors: [1]`, `hard_constraints: "present"` or `hard_constraints: "absent"` do not.
- **AC-10** (REQ-17, REQ-18, REQ-38) — Given an Implementer recommendation `e3` for another
  model, a recommendation `not-configurable`, and `recommendation: null`, when `resolve` runs
  without a policy, then each has `baseline: "harness-default"` with
  `recommendation-model-mismatch`, `recommendation-not-configurable` and
  `recommendation-unavailable` respectively.
- **AC-11** (REQ-20) — Given a valid policy, an invalid one, an absent path and a valid policy
  with a value missing from `--capabilities`, when `check-policy` runs, then the exits are 0, 1,
  1, 1, `valid` is `true`, `false`, `false`, `false`, and the `errors` arrays of the last three
  contain the codes `policy-invalid`, `policy-absent` and `value-not-declared` respectively.
- **AC-12** (REQ-22, REQ-23, REQ-24, REQ-25, REQ-32) — Given the delivered tree, then the
  state-files contract has `### Reasoning effort resolution` directly after
  `### Model columns and resolution` in the same `##` section, and the former effort paragraph
  is one sentence citing it; `workflows/spec-run.md` cites it in Step 1, 4.2 and 4.3; both
  single-session executors cite it; `## Protected Sections Contract` lists
  `## Effort Decisions`; the C-4 capability row is present where the phases contract has `## Capabilities`,
  and every harness's `capabilities.md` holds a `## sub-agent-effort` record; `docs/EFFORT-POLICY.md` exists and is listed in `docs/README.md`, cited from
  `docs/MODEL-CATALOG.md → ## Reasoning effort` and both helpers are listed in
  `scripts/README.md`; and `.ai/principles/domain.md` defines the four REQ-32 terms.
- **AC-13** (REQ-26, REQ-27, REQ-28) — Given the delivered tree and its base commit (the
  merge-base with `main` at delivery), then `scripts/check-effort-policy.py` exists, neither
  `scripts/validate-contracts.sh` nor `scripts/sync.sh` names it, `git diff --name-only
  <base> -- tests/` is empty, `git diff <base> -- scripts/validate-contracts.sh` is empty,
  `.ai/adr/index.md` lists an Accepted ADR whose title names the effort policy, and
  `bash scripts/validate-contracts.sh` exits 0.
- **AC-14** (REQ-29) — Given, without a policy, an Implementer with recommendation `e1` and
  escalation `e3`; an Implementer with recommendation `e3` and escalation `e1`; and an
  Implementer with recommendation `e2` and escalation `zz` (undeclared), when `resolve` runs,
  then the results are `requested: "e3"` with source `escalation` and `escalation-raised`;
  `requested: "e3"` with source `recommendation` and neither escalation code; and
  `requested: "e2"` with `escalation-unverifiable` respectively; and with no policy, a Validator with escalation `e3`
  has `requested: "e3"`.
- **AC-15** (REQ-30, C-1 exit 3) — Given requests with a Validator recommendation, role/stage
  `validator`/`execution`, scope `task` for an Implementer, `leaf_kind` contradicting the scope,
  `values` with `parameter: "absent"`, an unknown key, a repeated option, an unknown option, and
  both `--policy` and `--no-policy`, when `resolve` runs, then each exits 2 with empty stdout
  and one stderr line matching `^(invalid-arguments|invalid-request): ` that contains no
  fixture content; and an in-process run with `sys.version_info` patched to `(3, 10, 0)` exits
  3 with `unavailable: python`.
- **AC-16** (REQ-02) — Given the delivered harness files, then each contains exactly one
  `## sub-agent-effort` heading positioned per DM-1, one record named `sub-agent-effort` valid
  under DM-1, a `Limitations:` paragraph containing the words "resolved" and "actual", each of
  the four anchored lines exactly once and consistent with DM-1 (a `state: unknown` section has
  `none`/`unknown` values), no `.ai/`, `T-NN` or `ADR-NNNN` text, and the bytes of
  `harness/claude/capabilities.md → ## git-rails` and the Codex line
  `git-rails: none (textual rules only)` are unchanged from the AC-13 base commit (the frozen
  git-rails checks read them; AC-13 runs the validator).
- **AC-17** (REQ-33) — Given the delivered C-4 text, then it contains the REQ-33 report line
  format with `actual unknown` and the `rejected-by-harness` variant.
- **AC-18** (REQ-39, REQ-40, REQ-41) — Given the delivered C-4 text and C-2, then C-4 step 8
  states REQ-39's rule and the REQ-40 boundary, and each fixture below yields the listed
  parameter and a DM-5 UNAVAILABLE line that matches its regex, with outcome, `requested`,
  `resolved` and reasons exactly as listed (the suite builds the line with its own copy of the
  DM-5 mapping; the Implementer has recommendation `e3` for its own model unless stated):

  | # | No policy file unless stated; resolver state; spawn and session | parameter sent | outcome / requested / resolved | reasons |
  |---|---|---|---|---|
  | 1 | Helper missing; Implementer; session exposes `e1,e2,e3` | `e3` | requested / `e3` / `e3` | `capability-unknown,session-only-recommendation,resolver-unavailable,resolver-missing` |
  | 2 | Python 3.10 (exit 3); Implementer; session `absent` | none | not-requested / `unknown` / `none` | `capability-unknown,session-only-recommendation,session-parameter-absent,resolver-unavailable,resolver-python` |
  | 3 | Crash or time-limit kill; Validator | none | not-requested / `unknown` / `none` | `harness-default,resolver-unavailable,resolver-failed` |
  | 4 | Exit 2; Implementer with recommendation for another model | none | not-requested / `unknown` / `none` | `recommendation-model-mismatch,harness-default,resolver-unavailable,resolver-failed` |
  | 5 | Helper missing; Implementer; session exposes `e1,e2` only | none | not-requested / `unknown` / `none` | `capability-unknown,session-only-recommendation,session-value-absent,resolver-unavailable,resolver-missing` |
  | 6 | Policy file exists and `ORCHESTRAIL_EFFORT_POLICY=off`; as row 1 | `e3` | as row 1 | as row 1 |
  | 7 | Valid policy file; helper missing, or crash, or time-limit kill | none (stop) | no DM-5 line | — |
  | 8 | Malformed policy file (invalid UTF-8); helper missing | none (stop) | no DM-5 line | — |
  | 9 | Malformed policy file; resolver working | none (stop, REQ-11) | DECISION line `stop` | `policy-invalid` (AC-06) |
  | 10 | Helper missing; Implementer; non-null escalation; session exposes `e3` | `e3` | requested / `e3` / `e3` | `escalation-unverifiable,capability-unknown,session-only-recommendation,resolver-unavailable,resolver-missing` |
  | 11 | As row 1 with the capability record `state: no` | none | not-requested / `unknown` / `none` | `capability-unsupported,resolver-unavailable,resolver-missing` |

  and in no row is a value sent that differs from the leaf's recommendation.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-02, AC-16 |
| REQ-03 | AC-01 |
| REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04 |
| REQ-08 | AC-05 |
| REQ-09 | AC-03 |
| REQ-10 | AC-03 |
| REQ-11 | AC-06 |
| REQ-12 | AC-06 |
| REQ-13 | AC-07 |
| REQ-14 | AC-08, AC-18 |
| REQ-15 | AC-09 |
| REQ-16 | AC-03, AC-09 |
| REQ-17 | AC-10 |
| REQ-18 | AC-10 |
| REQ-19 | AC-05 |
| REQ-20 | AC-11 |
| REQ-21 | AC-05 |
| REQ-22 | AC-12 |
| REQ-23 | AC-12 |
| REQ-24 | AC-12 |
| REQ-25 | AC-12 |
| REQ-26 | AC-13 |
| REQ-27 | AC-13 |
| REQ-28 | AC-13 |
| REQ-29 | AC-14 |
| REQ-30 | AC-15 |
| REQ-31 | AC-02 |
| REQ-32 | AC-12 |
| REQ-33 | AC-03, AC-17 |
| REQ-34 | AC-07 |
| REQ-35 | AC-02, AC-03 |
| REQ-36 | AC-03 |
| REQ-37 | AC-02, AC-05 |
| REQ-38 | AC-10 |
| REQ-39 | AC-18 |
| REQ-40 | AC-08, AC-18 |
| REQ-41 | AC-18 |

Every AC names at least one REQ; AC-01–AC-18 are all covered above.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Both capability sections ship `unknown` | Policy- and escalation-chosen values are never sent | High until evidence is collected | Today's recommendation path stays (REQ-37); reasons are visible; Q-02 |
| The session observation is the dispatcher's own reading of its tool schema | A wrong reading sends or withholds a value | Medium | Declared and session values must agree when declared; `values: null` is `session-unknown` |
| Harness accepts a value but the model ignores or remaps it | Resolved ≠ actual | Unknown | `actual: unknown`; `Limitations:` paragraph; no claim of application |
| Existing heuristic already recommends low effort for low-demand leaves | Lower effort without a spec-09 comparison continues | Existing | Out of scope to change; owners can add minimum rules |
| Minimum rules and target raises are inert while `default:` is unknown | Floors over the harness default cannot be proved | High | `minimum-unverifiable` visible; `enforce: true` stops; owner raise for the top value |
| Owner raise when the real default lies outside the declared values | Requesting the top value could still be lower | Low | Only the top declared value; the owner explicitly accepts it; recorded as `owner-raise` |
| Spec-09 experiments run through the CLI flag, not a spawned worker | Qualification measures a proxy | Medium | Owner adoption is explicit; DM-3 pins model, role and effort correspondence |
| Frozen checks read edited files | A frozen check fails | Low (edits are additive) | REQ-28; stop and report rather than change a check |
| Delivery omits a harness's `sub-agent-effort` record | Spec 13's checker rejects the REQ-24 row (`capability-behaviour-table-invalid`) | Low | REQ-24 requires both records, `unknown` allowed; Q-01 resolved by 13 REQ-67 |

## Assumptions

- A-01 | Where effort support is declared | Resolved: an extension record `sub-agent-effort` in the spec-13 DM-4 form, in its own `## ` section placed before 13's `## Capability records`, plus four anchored lines modelled on `git-rails ask-capable modes:` | Source: spec 13 DM-4; `harness/claude/capabilities.md:31-46`; `scripts/validate-contracts.sh:5257-5259` | Reversible: yes
- A-02 | Values asserted for Claude Code and Codex | Resolved: none; both ship `unknown` unless the implementing task cites evidence for the installed runtime | Source: 13 DM-4 "This spec asserts no value"; `.ai/memory/architecture.md:175-176` | Reversible: yes
- A-03 | Policy location and ownership | Resolved: optional owner file under the XDG configuration directory; never created by workflows | Source: `workflows/pd-select-model.md:89-101` pattern; ADR-0015 Decision 1 | Reversible: yes
- A-04 | Default when no evidence establishes one | Resolved: today's behaviour (baseline, including the session-observed recommendation) | Source: owner standing decision; G4, G7; previous REQ-06 | Reversible: yes
- A-05 | What counts as lowering | Resolved: any target value not provably at least the baseline; unknown order or default makes values incomparable | Source: previous invariants 1, 5; `.ai/specs/README.md` → "Shared acceptance gates" | Reversible: yes
- A-06 | Qualification evidence | Resolved: hash-pinned spec-09 report and manifest; verdict `promote`; variants equal in model and differing only in the rule's role effort from `session-default` | Source: 09 DM-6 Manifest, DM-12 Report, `Promotion rule (REQ-12)`; 09 Out of Scope | Reversible: yes
- A-07 | Precedence between a leaf recommendation and a target rule | Resolved: recommendation wins; target rules only fill spawns without one; minimum rules apply to both | Source: ADR-0015 Decision 3; previous REQ-03 order (task override before role policy) | Reversible: yes
- A-08 | Behaviour on unsupported value | Resolved: do not send, do not substitute another value, continue at harness default unless an enforced minimum stops | Source: `rules/workflow-reference.md:148-150` | Reversible: yes
- A-09 | Floors stopping the run | Resolved: only when the owner sets `enforce: true` | Source: P5; previous §9 row "override conflicts with floor → owner" | Reversible: yes
- A-10 | Invalid or conflicting policy | Resolved: stop before the spawn | Source: G4 ("unsafe or ambiguous state stops before mutation"); previous §9 | Reversible: yes
- A-11 | Complexity signal | Resolved: spec 04's quality floor and hard constraints, persisted by DM-4 | Source: `scripts/model_selection.py:29`, `:106`, `:366`; `workflows/pd-select-model.md:117-121` | Reversible: yes
- A-12 | Ambiguity and risk dimensions of the previous REQ-01 | Resolved: covered through the quality floor, which weights ambiguity A and risk R and forces floor 5 for hard constraints | Source: `workflows/pd-select-model.md:117-119` | Reversible: yes
- A-13 | Where per-spawn facts are recorded | Resolved: protected append-only `## Effort Decisions` in task `state.md`, not 15's DM-2 | Source: P2, P4; 15 DM-1/DM-2; C-6 | Reversible: yes
- A-14 | Roles in scope | Resolved: Arbiter, Implementer, Validator of the sequential paths; not the Orchestrator itself, the critic, inline work or spec 12's parallel spawns | Source: `rules/orchestration.md:18-27`; `rules/workflow-reference.md:152` | Reversible: yes
- A-15 | Stage vocabulary | Resolved: `context` (Arbiter, the "context holder"), `execution` (one Implementer for the whole atomic execution cycle), `validation` (Validator) | Source: `rules/orchestration.md:38`, `:56-67`, `:80-83` | Reversible: yes
- A-16 | Effort inside a live worker | Resolved: never changed; set only at spawn | Source: previous §7; `rules/orchestration.md:63-67` | Reversible: no (harness limitation unknown)
- A-17 | Recording actual effort | Resolved: always `unknown`; no source in 05's profile parameters | Source: `scripts/usage_telemetry_contract.py:500-502`; `rules/workflow-reference.md:153-154` | Reversible: yes
- A-18 | Telemetry attribution | Resolved: offer a dimension source string; 05's producer maps it | Source: `scripts/usage_telemetry_contract.py:2900-2916`; ADR-0016 Decision 3 (keyed opaque identifiers) | Reversible: yes
- A-19 | Test placement | Resolved: `scripts/check-effort-policy.py`, standalone | Source: ADR-0019 Decision 3; precedent `scripts/check-spec-draft.sh` (`scripts/README.md:20`) | Reversible: yes
- A-20 | Helper form | Resolved: one stdlib CLI, `-I`, exit codes 0–3 | Source: `.ai/principles/coding.md`; `scripts/model-catalog.py` precedent | Reversible: yes
- A-21 | Resolver unusable | Resolved: stop only when an enabled policy exists; otherwise today's rule (REQ-39) with an UNAVAILABLE line (amended 2026-11-14 by D-01; formerly a spawn without parameter) | Source: G4; `workflows/spec-run.md:147-153` analogue; owner decision D-01 | Reversible: yes
- A-22 | Disable switch | Resolved: `ORCHESTRAIL_EFFORT_POLICY=off`; any value other than unset, empty or `on` disables (spec 14 REQ-32 rule) | Source: the `ORCHESTRAIL_*` variable convention (`.ai/memory/architecture.md:179`); smallest reversible choice | Reversible: yes
- A-23 | Legacy checkpoints without DM-4 lines | Resolved: complexity and recommendation `null`; rerunning bulk selection restores them | Source: P3; free text is not parseable deterministically | Reversible: yes
- A-24 | Previous REQ-01 "prefer deterministic tools for mechanical actions" | Resolved: out of scope here | Source: roadmap ownership `.ai/specs/README.md` → "Nine token optimization workstreams" | Reversible: yes
- A-25 | Previous "explicit owner/run override" | Resolved: expressed through the owner's policy file, including `owner_raise` for the top declared value; no new command flag | Source: previous REQ-03; P5/P6 | Reversible: yes
- A-26 | Today's session-observed recommendation while no declaration exists | Resolved: kept (REQ-37); policy-chosen values still need `state: yes` | Source: owner standing decision (default is today's behaviour); `rules/workflow-reference.md:144-147`; 13 REQ-16 governs new capability-dependent behaviour | Reversible: yes
- A-27 | Arbiter and Validator as "session-default roles" | Resolved: the phrase concerns model identity; effort is a separate setting | Source: ADR-0015 Decision 3; `docs/MODEL-CATALOG.md:84` | Reversible: yes
- A-28 | Target tree | Resolved: the tree after spec 13; pre-13 names apply only if 13 is not delivered | Source: `.ai/specs/README.md` → "Dependency order" | Reversible: yes
- A-29 | Spec 12's parallel-mode spawns (added 2026-11-14) | Resolved: outside policy version 1; behaviour stays exactly as today (no effort parameter, no resolver call, no `## Effort Decisions` line for them) and DM-2/DM-6 enums and C-4 stay as written. 12's A-27 states the same. To bring them under the policy, 12's implementer, or the owner after 12's delivery, makes a revision of this spec that adds the roles leaf coordinator, phase agent and workflow agent and the stages `tests`, `implement`, `finalize`, `check`, `propose`, `close` to DM-2/DM-6 (with DM-2 `match` and DM-5 grammar updates and acceptance rows), names the root as the only writer of `## Effort Decisions` in C-4, and re-checks the additive resolver; 12's delivery adds no effort handling itself | The `repair` stage of 12 (REQ-54) is not in the amendment list: it stays with spec 19's own route (19 C-5 step 5 and C-8 step 3) | Source: spec 12 A-27 and its follow-up list; this spec's A-14 | Reversible: yes

## Decisions

Auto mode made no choice that overrides a principle, accepted ADR or shipped invariant (A-26,
A-27); the replacement of the prose effort paragraph and the new stops are recorded by REQ-22
and REQ-27. One owner decision is recorded:

- D-01 | With no policy file and an unusable resolver, the dispatcher applies today's rule (REQ-39) instead of spawning without an effort parameter; the DM-5 UNAVAILABLE grammar is widened to carry the decision and a cause code | Overrides: none (replaces the earlier REQ-14 / C-4 step 8 / A-21 wording, which departed from the Goal) | Rationale: the Goal and gate G4 say nothing changes without an owner policy; reusing the existing rule for the failure case is more conservative than a new "spawn without effort" variant | Follow-up: REQ-14, REQ-39–REQ-41, DM-5, C-2, C-4 step 8, AC-08 and AC-18 amended; with a policy file present the stop stays (REQ-40); no change in other specs required

## Clarifications

### Session 2026-11-14

- No question was put to the owner (auto mode under standing authorization). Gaps are resolved
  in A-01–A-29.

### Session 2026-11-14 (owner decision)

- Q: With no enabled policy and an unusable resolver, should the spawn carry no effort
  parameter (earlier text) or follow today's rule, as the Goal requires? → A: Follow today's
  rule (REQ-39); extend the DM-5 UNAVAILABLE grammar accordingly (D-01).
- Q: Does the same fallback apply when an owner policy file exists but cannot be evaluated? →
  A: No. That stays a stop (REQ-14, REQ-40); only the no-policy case changes.

## Open Questions

- Q-01 | resolved | Spec 13 admits registered extension keys in the `Requires` cell: resolved
  by spec 13 REQ-67 (a canonical key or the `name:` of a capability record that every harness's
  `capabilities.md` declares). REQ-24 is unconditional; the delivery declares the record for
  each harness (REQ-24). Kept for its id.
- Q-02 | non-blocker | Can the Claude Code worker-spawn mechanism's effort setting be evidenced
  for the installed runtime? Impact: until it is, only session-observed recommendations are
  sent. Recommended: collect evidence at implementation; otherwise ship `unknown`.
- Q-03 | resolved | With no enabled policy and an unusable resolver (Python older than 3.11
  or the helper missing), REQ-14, C-4 step 8 and A-21 spawned without an effort parameter, while
  the Goal requires that with no policy and no escalation the request sent equals today's, and
  today's rule (`rules/workflow-reference.md`, effort paragraph of the dispatch section,
  replaced by REQ-22) sends the leaf's recommendation when the session exposes the setting.
  Resolved 2026-11-14: apply today's rule in that case (REQ-39: send the DM-4 recommendation only
  when REQ-35 observes it exposed, otherwise no parameter) and widen the DM-5 UNAVAILABLE grammar
  (DM-5; AC-08, AC-18). Owner decision D-01. An existing policy file still stops (REQ-40).

## Notes

### Name mapping (spec 13)

The implementation edits the tree after spec 13. Names below are post-13, with the current
name in parentheses for use only if 13 is not delivered (`docs/name-map.json` absent):
state-files contract `rules/contract-state-files.md` (`rules/workflow-reference.md`); phases
contract `rules/contract-phases.md` (none before 13; the behaviour-row half of REQ-24 then does not apply, A-28);
orchestration contract `rules/contract-orchestration.md` (`rules/orchestration.md`);
model-selection workflow `workflows/discovery-select-model.md` (`workflows/pd-select-model.md`);
single-session executors `workflows/execution-execute.md` (`workflows/pe-execute.md`) and
`workflows/atomic-execution.md` (`workflows/phase-atomic-execution.md`); `workflows/spec-run.md`
unchanged. Anchors are headings, never line numbers.
This spec creates no top-level rule file (its new files are two scripts, a guide and an ADR), so
13's rule `rules/<kind>-<subject>.md` naming for later files and spec 08's 700-word limit
(REQ-01) apply only if a later change adds one; it would be `load: on-demand` with no name-map
row.

### Implementation hints (nonbinding)

1. Subtask order: capability sections and guide; `effort-policy.py` with the suite (RED first:
   AC-01, AC-02, AC-04–AC-07, AC-09–AC-11, AC-14, AC-15 fixtures); DM-4 in the model-selection
   workflow; dispatcher text, protected section and vocabulary; ADR and capability row.
2. Evidence for DM-1 can come from the runtime's official documentation of its sub-agent or
   task tool and the installed version string. The CLI flag observed by spec 09 concerns
   `claude -p`, not a spawned sub-agent, and is not evidence for this section.

### Rollback

New runs: set `ORCHESTRAIL_EFFORT_POLICY=off` or move the policy file aside; the gate keeps
working with the baseline. Full rollback: revert the delivery; `## Effort Decisions` and
`effort-input:` lines then remain as inert, readable history. No recorded line is rewritten.

### Rejected alternatives

- Embedding effort in spec 15's `checkpoint_attempt`: covers one route and two roles, and is
  written before the outcome is known (C-6).
- A per-model capability registry keyed by model version (previous §5): no evidence source
  exists per model; the session and harness declaration are the only checkable facts.
- Stopping on every unsupported value: changes today's behaviour of
  `rules/workflow-reference.md:148-150`.
- Treating the top declared value as at least an unknown default without an owner statement:
  assumes the default is one of the declared values, which no evidence states.
- Dropping today's session-only recommendation until a declaration exists: would change the
  request sent for every Implementer without a policy (A-26).

### Identifier history

REQ-01–REQ-08 and AC-01–AC-05 keep their previous subjects, restated as single behaviours, with
these narrowings: previous REQ-07's accounting and previous AC-04's synthetic report belong to
spec 05 (Out of Scope); previous AC-02's "confirmed" state is reduced to the rejection line
because no acknowledgement mechanism exists. REQ-09–REQ-41 and AC-06–AC-18 are new (REQ-39–REQ-41 and AC-18 appended 2026-11-14 by D-01).

### Follow-ups for other specs and shared files (not edited here)

- 13: none — REQ-67 admits the `sub-agent-effort` record name in `Requires` (Q-01 resolved).
- 09: none — REQ-53 and the manifest definition already carry the role keys (C-6).
- 05: a later schema version may add an observed-effort source-profile parameter (C-6).
- 12: no change to 12 now; parallel-mode spawns stay outside the policy (A-29). Bringing them
  in is the revision of 18 triggered by 12's delivery, as 12's follow-up list also states.
- 15: none — its C-10 row for 18 already says its attempt record is not used by 18.
- 19: none — C-8 step 3 and C-10 row 18 agree with REQ-29 and C-3 step 5.
- 20: none — REQ-29 produces no complexity value; DM-4 stays the producer.

### Change log

- 2026-11-14 — reconciliation with refined peer specs: parallel-mode spawns kept outside policy
  version 1 with the later amendment stated (C-6 row 12, A-29; agrees with spec 12 A-27);
  qualification attachment aligned with spec 09 REQ-53 and DM-12 (ignored `orchestrator` key,
  uniform-effort limitation, size limit of DM-3 documented as 18's own, rejected as
  `qualification-invalid`); spec 16 row lists all four offered fields; spec 19, 15, 20 rows
  confirmed; Q-01 resolved by spec 13 REQ-67 and REQ-24 made unconditional with the record
  declaration required in each harness; spec 10's `## Behaviours` rendering confirmed (while both
  records are `state: unknown` the row shows `unavailable` for both harnesses). Ids preserved; A-29 added.
- 2026-11-14 — Refined in English: capability section, owner policy, offline resolver,
  decision persistence and integration; identifiers preserved.
- 2026-11-06 — Implementation/state reconciliation (previous revision; preserved under Source).
- 2026-11-14 — independent final review: capability row narrowed so 13 REQ-16 agrees with REQ-37; new non-blocker Q-03 (unusable resolver without a policy versus the Goal); disable switch follows spec 14 REQ-32; version check needs a parseable top level; 09 `session-default` mapped to `harness-default`; AC-16 made checkable in the suite; citations by id or heading.
- 2026-11-14 — owner decision recorded: D-01 resolves Q-03; with no policy file (or the disable
  switch) and an unusable resolver the dispatcher applies today's rule (REQ-39–REQ-41, AC-18);
  DM-5 UNAVAILABLE widened backward-compatibly (outcome `requested`, `requested`/`resolved`
  tokens, optional extra reasons, cause codes `resolver-python`, `resolver-missing`,
  `resolver-failed` in C-2); the Goal's exception wording removed; REQ-14, C-4 step 8, A-21, AC-08
  and the edge-case rows amended; an existing policy file still stops (REQ-40).

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph stating the problem and the outcome |
| 2 | Out of Scope names concrete exclusions | PASS — model choice, inline/Orchestrator effort, spec 12 parallel spawns, heuristic change, shipped defaults, paid runs, 05/15 schema changes, live-worker changes |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-41; previous REQ-01–REQ-08 preserved and restated |
| 4 | Every REQ maps to an AC and back | PASS — Traceability covers 41 REQs and 18 ACs |
| 5 | Every AC is binary and can guide a test first | PASS — fixture tables and text checks in `scripts/check-effort-policy.py` |
| 6 | Non-functional targets measurable or N/A | PASS — NFR-01–NFR-04, NFR-06, NFR-07 measurable; NFR-05 N/A with reason |
| 7 | Data model and contracts specified | PASS — DM-1–DM-7, C-1–C-8 |
| 8 | Error, empty, boundary, concurrency cases | PASS — Edge Cases table; concurrency excluded by the single dispatcher (P4) |
| 9 | Every ambiguity resolved or open | PASS — A-01–A-29; Q-01 and Q-03 resolved, Q-02 non-blocker |
| 10 | No blocker question | PASS |
| 11 | Existing-code claims cited and verified | PASS — verified by author and critic at `060ce6d` and in the worktree |
| 12 | Terminology matches the domain | PASS — domain roles reused; new terms added to `domain.md` by REQ-32 |
| 13 | Feature-sized (1–8 subtasks) | PASS — about five subtasks (Notes → Implementation hints) |
| 14 | Devil's Advocate review | PASS — Review: 3 rounds, score 100/100, critic: sub-agent, open: none |

Note (2026-11-14 reconciliation): peer-spec alignment edits only (see Change log); no change to
requirements beyond REQ-24 losing its precondition; the verdict is unchanged.

Verdict: **READY FOR DEVELOPMENT**. Automated readiness is not sign-off; review before
implementation.
