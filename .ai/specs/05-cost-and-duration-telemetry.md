# Reliable usage telemetry, API-equivalent cost and baseline

## Source

Owner request, 2026-10-21, translated: optimize total cost of a correct result; actual
billing is a fixed subscription, but value every observable task at API prices; do not
invent measurements or launch paid experiments. This expands the existing telemetry
spec without reintroducing production budgets (ADR-0009 Decision 5).

## Context & Problem

The lifecycle producer advances step sequence and timing on accepted writes
(`scripts/log-step.sh:736`, `scripts/log-step.sh:845`), deletes active metadata on
close (`scripts/log-step.sh:944`), and recognizes only three lifecycle event types
(`scripts/log-step.sh:1171`). Correlated replay freezes the accepted payload
(`rules/run-log.md → ## Correlated hook intervals`, `rules/run-log.md → ## Native hook adapter → ### Project activation and private ownership`). Consequently, logging a model request
as another step, or enriching an accepted checkpoint with late usage, would change
existing process semantics. The hook currently forwards timing and result fields,
not usage counters (`hooks/log-step-hook.sh:355`, `hooks/log-step-hook.sh:443`).

The privacy contract forbids conversation content and external source paths in the
shared store (`rules/run-log.md → ## What must never enter the log`); retrospective analysis owns historical reads
(`rules/run-log.md → ## Relationship to the existing state files`, `workflows/retro.md → ## Step 1 — Load`). Usage needs its own additive
observation contract and explicit completeness evidence. Otherwise partial streams,
forked histories, internal review calls, resumed work and nested summaries can produce
apparently precise but incomplete or duplicated costs. This document specifies planned
behavior; none of the additional interfaces below is claimed to be implemented.

## Current implementation baseline — 2026-10-28

Completed correlated logging supplies executable intervals, explicit attribution and
exact retrospective timing. The workflow audit preserves that protocol and its loader
(`workflows/retro.md → ## Step 1 — Load`, `### Measured hook intervals`), while shortening
workflow text. Usage observations, prices, cost projections, advisory policies and the
interfaces in this spec remain unimplemented. Word/byte changes are diagnostics, not
measured tokens or money. The owner's expanded 2026-10-27 requirements remain intact.

## Goal

Make model usage and the cost of independently accepted results auditable across both
supported harnesses, so the owner can identify expensive work and evaluate savings
without hiding missing data, failed attempts, verification or subscription semantics.

## Scope

- Versioned source profiles, scoped collection and immutable request observations.
- Streaming finalization, deduplication, causal attribution and coverage accounting.
- Reproducible API-equivalent valuation, including cache, tools and unknown prices.
- Local usage summaries, advisory thresholds and retrospective exports for optimization.
- Compatibility with lifecycle logging and the shared metric contract consumed by
  catalog selection, evaluation, context, orchestration, review, effort and repair work.

## Out of Scope

Production spend/time caps; quota prediction; automatic model or policy changes; paid
experiments; external notifications; a dashboard, daemon or hosted monitoring service;
provider billing/admin API integration; a general log-retention manager; rewriting
historical logs; and making Python, jq or telemetry mandatory for legacy logging.
No collection of prompts, responses, source code, tool arguments or credentials is added.

## Actors & Roles

| Actor | Responsibility and permitted inputs |
|---|---|
| Source adapter | Read explicitly selected exports or owned hook payloads using a declared source profile; emit sanitized observations and inventory evidence. |
| Telemetry producer | Validate complete ingestion invocations and publish immutable artifacts; return separate usage receipts. It does not query historical usage for routing or totals. |
| Authorized orchestrator | Supply correlation, consume its own current-run receipts and private accumulator, and write shared notes as the existing single writer. |
| Retro | Select historical lifecycle and usage inputs, freeze a private corpus manifest, invoke pure analysis helpers and publish versioned reports. |
| Maintainer | Explicitly refresh price snapshots and configure advisory policies or adapter profiles. |
| Evaluation and optimization consumers | Read explicitly exported aggregates and independent acceptance labels, never discover or scan the shared history themselves. |

Reading a producer's exact existing content-addressed publication to verify an
idempotent retry is bookkeeping, not permission for historical queries. Pure helpers
read only explicit input manifests. An active workflow cannot use them to select a
historical corpus. Export ingestion does not grant permission to inspect unrelated
sessions or accounts.

## Terminology

| Term | Definition |
|---|---|
| API-equivalent cost | Usage valued using a named public API price scenario; distinct from subscription payment, provider-reported money and quota consumption. |
| Result opportunity | One declared task/input/acceptance-contract/strategy/repetition combination; resumed runs and repairs do not create new opportunities. |
| Run | One lifecycle invocation; process completion and usage finalization are separate. |
| Attempt | One execution, repair or verification episode belonging to a result opportunity. |
| Request | One actual model response, counted once across copied histories; a retry producing a different response is another request. |
| Observation | An immutable source measurement of a request, counter interval, inventory or monetary aggregate; several observations may describe the same request. |
| Accounting owner | The narrowest evidenced task/span or explicit shared/unattributed pool charged once; parent rollups are non-additive views. |
| Coverage | Separately evidenced inventory, finalization, token-dimension, valuation and attribution completeness for a declared scope and as-of time. |
| Priced subtotal | The sum of valid, disjoint, priceable components; it is not automatically a complete total or a proven lower bound. |

Existing project meanings of workflow, phase, atomic cycle, leaf, orchestrator, run log
and retro are retained. New telemetry terms are definitions proposed for the canonical
run-log contract during implementation, not additional workflow status vocabularies.

## Requirements

- **REQ-01** WHEN a usage observation is available, THE SYSTEM SHALL associate the
  identities and provenance in the Data Model with it, leaving unavailable actual
  model/effort or ownership dimensions explicitly unknown rather than substituting
  planned values, session defaults or timestamp guesses.
- **REQ-02** WHEN normalizing a supported counter convention, THE SYSTEM SHALL produce
  the disjoint quantities defined below while retaining only allowlisted numeric raw
  counters; included reasoning and tool tokens SHALL NOT be charged again.
- **REQ-03** IF a measurement is missing, partial, contradictory or unsupported, THEN
  THE SYSTEM SHALL retain valid available dimensions with typed coverage reasons and
  withhold unsupported complete totals; text length SHALL NOT estimate token usage.
- **REQ-04** WHEN observations refer to the same response, THE SYSTEM SHALL resolve
  them exactly once under the identity and revision rules below, preserving provenance
  and quarantining unresolved conflicts instead of using ingestion order as authority.
- **REQ-05** THE SYSTEM SHALL maintain immutable, explicitly refreshed price snapshots
  with exact model applicability, effective evidence, unit prices, cache lifetimes,
  context predicates, service/region dimensions and separately billed tool units.
- **REQ-06** WHEN valuing usage, THE SYSTEM SHALL apply one identified valuation
  scenario and publish its calculation breakdown, retaining provider-reported money
  separately; subscription payments SHALL NOT become per-request charges or quotas.
- **REQ-07** WHEN optional token/cost projections or structured usage references are
  supplied to the lifecycle producer, THE SYSTEM SHALL validate the whole invocation
  before mutation under the projection rules below, preserving its existing safe,
  non-blocking failure and legacy optional-dependency behavior.
- **REQ-08** WHEN reporting a run, THE SYSTEM SHALL expose the completeness dimensions
  defined below and distinguish a provisional close-time projection from a complete
  as-of retrospective total; unknown request inventory SHALL NOT become 100% coverage.
- **REQ-09** WHERE a verified source profile exposes usage, THE SYSTEM SHALL support
  its owned hook payload or explicitly selected read-only export; a timing hook alone
  SHALL NOT establish usage support, inventory completeness or native model access.
- **REQ-10** WHEN reporting durations, THE SYSTEM SHALL distinguish lifecycle wall
  time, inclusive span time, derivable exclusive time and sum of worker time, retaining
  clock/source quality and never adding overlapping spans into run wall time.
- **REQ-11** WHEN an eligible completed duration crosses the declared advisory rule,
  THE SYSTEM SHALL deliver the duration warning to the owning notes and final report
  using an explicit threshold export or the fixed two-hour fallback, without stopping
  the run or reading history.
- **REQ-12** WHEN building a baseline, THE SYSTEM SHALL publish the cohort statistics,
  expensive-work ranking, usage mix, failures and exclusions defined below, separating
  complete observations, partial subtotals and censored work.
- **REQ-13** WHEN joining independent acceptance labels, THE SYSTEM SHALL report
  opportunity-level observed cost per accepted result under the cohort rules below,
  including failed/rejected attempts and production review costs; an LLM completion
  verdict SHALL NOT supply an independent acceptance label.
- **REQ-14** THE SYSTEM SHALL publish reproducible offline fixtures, formulas, adapter
  coverage and operational documentation; shared index gates G1-G8 apply, and paid
  collection/comparison still requires a separately authorized experiment manifest.
- **REQ-15** WHEN selecting an adapter, THE SYSTEM SHALL require a versioned source
  profile declaring format, counter scope, identity, finality and inventory capabilities;
  unsupported versions SHALL produce unavailable coverage rather than guessed mappings.
- **REQ-16** WHEN partial, final or corrected response usage arrives, THE SYSTEM SHALL
  select authoritative quantities using the stream lifecycle rules below; summing
  cumulative snapshots or treating the largest partial value as final is prohibited.
- **REQ-17** WHEN only cumulative or aggregate counters are exposed, THE SYSTEM SHALL
  apply the verified-epoch and aggregate rules below without inventing per-request
  usage, distributing costs by text size or adding covered aggregate and request totals.
- **REQ-18** WHEN attributing a response, THE SYSTEM SHALL use explicit causal evidence
  and assign one evidenced accounting owner or shared/unattributed pool, without equal
  splits or fabricated leaf assignments.
- **REQ-19** WHEN usage or acceptance evidence arrives after process closure, THE
  SYSTEM SHALL publish a new immutable observation or derived report revision without
  reopening the run or modifying its accepted lifecycle event or checkpoint payload.
- **REQ-20** WHEN publishing usage, THE SYSTEM SHALL use the bounded immutable artifact
  and snapshot contracts below, leaving lifecycle files, sequence, timing and checkpoint
  state unchanged by usage-only ingestion.
- **REQ-21** WHEN calculating or presenting monetary values, THE SYSTEM SHALL use exact
  integer/decimal arithmetic and the subtotal, lower-bound and rounding rules below.
- **REQ-22** WHEN a configured usage advisory threshold is crossed, THE SYSTEM SHALL
  emit a local, deduplicated warning with scope and coverage, without enforcing a budget,
  changing a model, invoking another model or sending external messages.
- **REQ-23** WHERE consumers supply optimization diagnostics, THE SYSTEM SHALL retain
  the typed, namespaced metadata dimensions below without treating bytes, words or
  inferred roles as measured tokens, actual model settings or independent quality.
- **REQ-24** WHEN exporting telemetry analysis, THE SYSTEM SHALL produce versioned
  machine-readable and human-readable artifacts with a frozen corpus, calculation
  scenario and inclusion/exclusion audit trail; equal inputs SHALL reproduce equal
  semantic output and canonical serialized bytes except declared creation timestamps.
- **REQ-25** IF collection is disabled, a dependency is unavailable or a bounded source
  fails validation, THEN THE SYSTEM SHALL preserve existing evidence and workflow
  behavior while reporting the affected coverage gap under the failure contract below.
- **REQ-26** WHEN comparing strategies or models, THE SYSTEM SHALL distinguish
  descriptive observations from qualified comparisons and refuse cheapest/effectiveness
  conclusions from incomparable scope, partial lower bounds or self-reported quality.

## Data Model

All entities below are **new** additive metadata except the existing lifecycle events
(`rules/run-log.md → ## Field vocabulary`) and timing/correlation fields (`rules/run-log.md → ## Correlated hook intervals`).
Wire schemas have integer `schema_version: 1`, no duplicate JSON keys, finite numeric
values, and a canonical contract export. Unknown schema versions are unsupported;
unknown fields in normalized envelopes are rejected. A provider payload is never copied
wholesale into any entity.

| Entity | Required fields, types and identity |
|---|---|
| Source profile | Stable profile ID/version; provider, harness and supported format/version evidence; counter paths and semantics; response identity/account scope; finality signal; inventory capability; optional cache/effort/tool dimensions; known omissions; reviewed date and official evidence URL. |
| Collection scope | Opaque project/task/opportunity/run/session/agent IDs as available; selected-source IDs/digests; profile version; collection interval; receipt/as-of time; authorized source selection. Project rename aliases require explicit mapping. |
| Observation | Content-derived ID; kind `request_usage`, `inventory` or `reported_aggregate`; profile and source digest/record ordinal; counter scope; provider identity scope; response/client-call ID where exposed; provider timestamp and timestamp quality; observed-at time; sanitized raw counters; normalized dimensions; measurement state; outcome; attribution evidence and optional superseded observation reference. |
| Request view | Derived canonical provider/account/response key; contributing observation IDs; requested/resolved/actual model and effort with evidence; selected final/partial dimensions; accounting owner; coverage reasons; no mutable stored request total. |
| Inventory | Scope and observation window; independently supplied eligible client-call/response identities and one-to-many linkage; unresolved issued-call slots; explicit `complete`, `partial` or `unknown` state and evidence; known child/internal-review/tool membership, collection segments/gaps and declared exclusions. |
| Attribution | Root entrypoint, nested workflow/stage, role, full/quick flow, attempt, parent span and opportunity ID where supplied; owner kind `span`, `task`, `shared_pool` or `unattributed`; candidate owners, evidence source and asserted/verified/inferred quality. |
| Price snapshot | Content-derived ID; USD currency and decimal-string rates per declared unit; retrieval date; effective interval or explicitly unknown history; exact model/verified alias mapping; API modality, service tier, region, cache/threshold/tool applicability and source URLs. |
| Valuation scenario | Stable ID and basis `at_execution` or `reprice`; selected snapshot IDs; explicit service/region/modality assumptions or original execution dimensions; threshold rules; currency and presentation precision. It is not an invoice. |
| Advisory policy | Schema/version, explicit token/USD/coverage thresholds; scope and units; generated-at/valid-until; optional compatible historical cohort digest/sample count/median; warning deduplication state stays private to the owning run. |
| Analysis manifest | Explicit immutable lifecycle/usage/inventory/price/acceptance inputs with digests and versions; normalized aliases; scope; as-of time; exclusions; selected scenario; output schema/normalizer version. External source paths remain in the local manifest, never shared telemetry. |

### Counter and lifecycle semantics

- `measurement_state`: `partial | final | unavailable | conflicted` per applicable
  dimension; request outcome is separately `succeeded | failed | cancelled | timed_out |
  unknown`. Failure or cancellation does not imply free usage.
- `counter_scope`: `response_total | incremental_delta | cumulative_epoch |
  provider_aggregate | caller_aggregate`. Session/request counters cannot be interchanged.
- Normalized quantities: `input_uncached`, `input_cache_read`, cache-write entries
  `{ttl, tokens}`, optional `input_cache_write_unsplit`, `output_total` and optional
  `reasoning_subset`. `tokens_in` is known only when its exhaustive input sum is known.
  Each reported observation count is an integer from zero through 9007199254740991;
  derived aggregate counts use exact integers even above that per-observation limit.
- Included-input profiles subtract both cache reads and cache writes from total input
  only when the profile documents that inclusion. Separate-input profiles add their
  disjoint ordinary/cache buckets. A missing write field means zero only when that
  profile proves it inapplicable, not because a serializer omitted it. TTL components
  must equal a reported write total; negative residuals and overlaps are conflicts.
- A final provider snapshot replaces earlier partial totals for that response. It is
  not added to them. A final correction replaces a prior final only with explicit
  provider revision/ordering evidence; otherwise contradictory finals are conflicted.
  Arrival order, file modification time and component-wise maximum are not authority.
  Documented unique incremental deltas may be summed once; finality additionally
  requires a proven start-to-terminal contiguous sequence or equivalent provider
  completeness evidence. A terminal marker with missing deltas is not enough. Their
  authoritative final snapshot is a consistency check or replacement, never another
  charge. A truncated stream remains
  partial even when its counters are monotonic or its process exits successfully.
- Cumulative differencing requires the same provider/account/model/unit dimensions,
  a documented epoch, ordered adjacent snapshots and a complete interval inventory.
  Per-request attribution additionally requires exactly one evidenced contributing
  request fully bracketed by the snapshots with no in-flight usage crossing either
  endpoint, or documented counters updated atomically at request completion. A
  mid-request predecessor measures only an interval, not the entire request. Resets,
  replayed prefixes, gaps, multiple requests and unknown initial values
  must not create request-level deltas. A valid interval aggregate may remain a separate
  aggregate-only observation. Aggregate monetary/counter snapshots are non-additive
  corroboration when their covered request set overlaps or is unknown.

### Identity, ownership and late data

Provider/account identity scopes deduplicate the same response across forked sessions;
session IDs are provenance, not an extra identity component that duplicates a response.
Without response IDs, a profile may use a proven stable client-call identity and its
response linkage; timestamp-plus-token fingerprints alone cannot prove equivalence.
Unresolvable identity leaves completeness unavailable and excludes potentially
overlapping values from an additive subtotal. Transport/export replay of one response
counts once; retries producing different responses count separately.

Ownership evidence is dispatch/correlation metadata or an explicit reviewed import
mapping. Requested model, prompt-inferred role or a coincident timestamp is not an
actual execution setting or proof of ownership. Root controller, planning, integration
and review spans are legitimate owners without a leaf. A proven common ancestor may
own a shared pool once; candidate leaves keep incomplete attribution. If no common
scope is evidenced, the pool stays unattributed. No equal or proportional split is made.
Top-level approach and nested stages are separate labels, never additive competing runs.

Stable ownership includes linked final responses, children and tool observations that
arrive after `run-end`. A process outcome is unchanged. Reports use immutable as-of
revisions, retain earlier reports and list late arrivals/exclusions. Replayed or invalid
timestamps may support identity evidence only; duration and time-window membership stay
unknown unless another measured clock establishes them.

### Completeness and cost states

Every report declares scope/as-of and records inventory state, eligible request count
when known, finalized request count, per-dimension usable numerator/denominator,
priceable count, verified-owner count, unknown-model count, unknown-rate count and
exclusion reasons. An independently evidenced inventory includes retries, cancelled
and failed requests, orchestration, workers and internal review where the source can
enumerate them. An end marker without such capability does not prove inventory closure.
Client-call and linked response identities are aliases of one contributing response;
one call yielding two actual responses expands to two distinct requests. An unresolved
issued call remains an unknown-usage slot, not a zero-cost response. Unresolved fan-out
keeps the response denominator unknown; report known responses and unresolved slots
separately, never a ratio greater than one or a guessed complete denominator.
Parsed record count is never the request inventory denominator. Missing inventory makes
request coverage unknown even if all parsed records contain final counters. Known empty
inventory reports zero eligible requests, exact zero billable cost when the whole
billable scope is evidenced empty, and coverage `not_applicable`, not 0/0 or fabricated
100%. An empty export with unknown inventory still has unavailable cost.

A token dimension may be complete while valuation or attribution is incomplete.
Unknown internal model aliases, including guardian/review calls, retain measured tokens
and request counts with unpriced cost; no public-model substitution is made. Complete
scope cost requires independently complete inventory, final applicable quantities,
resolved identity/ownership, applicable prices/tool units and no conflicting overlap.
Otherwise `cost_usd` complete total is absent and a separately named priced subtotal
may be shown. `lower_bound` is permitted only when all included components are valid,
nonnegative, disjoint and priceable, and exclusions cannot reduce them. Contradictions,
unresolved overlap, assumed historical prices or unresolved signed components within
the selected valuation forbid that claim. Separately excluded provider account credits
do not change an API-list-price subtotal's mathematical bound. Priceable components
with unknown write TTL can contribute a subtotal while
write cost remains unavailable. Provider-reported money keeps original currency, scope
and possible credits separately; no implicit FX conversion or aggregate addition occurs.

## Contracts & Interfaces

### Additive ingress and publication

Proposed interfaces, to be implemented without changing existing invocation behavior:

```text
python3 scripts/usage-telemetry.py normalize --profile ID --input-manifest FILE --output FILE
bash scripts/log-step.sh usage-ingest --manifest FILE
python3 scripts/usage-telemetry.py analyze --corpus-manifest FILE --scenario ID --output-dir DIR
python3 scripts/usage-telemetry.py status --receipt-snapshot FILE [--policy FILE] --output FILE
```

`normalize` reads only explicitly enumerated regular source files and an explicit
attribution scope in its manifest; no recursive session discovery or implicit backfill.
It emits a sanitized bundle and structured coverage diagnostics. Valid but unavailable
dimensions are not invalid producer arguments. An invalid individual source observation
is quarantined by opaque source ID/ordinal/reason while other usable observations are
retained; a malformed container/profile/manifest fails the invocation with no output
publication. Unknown raw payload fields are not persisted. A changing selected input is
excluded or frozen at an explicitly verified prefix with a partial-source reason.

The proposed wire envelopes are fixed as follows; physical JSON schemas are exported
with the canonical contract during implementation, not guessed independently by each
consumer. Identifier counts and envelope sizes use the limits below.

| Envelope | Required contract |
|---|---|
| Input manifest | `schema_version: 1`, `kind: source_selection`, profile ID/version, declared owner scope, explicit attribution mapping, and source entries `{source_id, local_path, sha256, optional verified_prefix_bytes}`. A source entry is a selected regular file, never a directory/glob; source IDs and digests replace local paths in output. |
| Ingestion manifest | The self-contained sanitized `usage_bundle`: schema/profile versions, opaque declared run/project scope, source IDs/digests, observations, inventories/collection segments and bounded typed diagnostics. It has no external data references or external source paths. Declared ownership remains asserted until its causal evidence is verified; schema acceptance does not prove it. |
| Usage receipt | `kind: usage_accepted`, receipt schema version, bundle SHA-256, observation IDs, declared owner scope, `duplicate` boolean and schema-validation version. This acknowledges publication only, not inventory completeness, provider truth, verified attribution or financial finality. |
| Lifecycle usage projection | Self-contained sanitized contributor quantities/IDs and profile evidence, included price definitions/digests/scenario, exact projected amounts and coverage. It is submitted through `--usage-file`; no contributor discovery or shared-history read is needed. Missing independent evidence leaves the projection unverified/non-additive. |
| Receipt snapshot | `kind: current_run_snapshot`, schema version, owner run/session scope, private revision ID, collection mode/segments, accepted receipt identities, reconciled request views/inventory and advisory crossing/delivery state. Optional duration observations carry measured endpoints/duration, duration kind, source quality and cohort key; historical threshold exports carry explicit bytes/digest/expiry. It carries data needed for calculation, not just shared-store file names. Multiple private parts require explicit digested entries in a bounded manifest. |

Input, corpus and private snapshot manifests are at most 1 MiB and 10,000 entries;
referenced normalized bundle/private data parts are at most 32 MiB each. Policy and
receipt envelopes are bounded by the same 1 MiB limit. Reject duplicate keys, nonfinite
values, unsupported versions and a manifest above its limit before following entries.
An analysis manifest freezes all chosen bytes/digests before calculation. Output bundles
and private data parts use the normalized observation limits. Explicit helper outputs
must be outside the canonical shared usage namespace; only the producer publishes there.

`usage-ingest` is the sole usage-store writer and uses the same canonical definitions
exported by `log-step.sh contract`; normalized envelopes are not a second lifecycle event
vocabulary. It validates the entire sanitized bundle before publication and writes
exactly one immutable canonical bundle file per invocation below the resolved log
root's `usage/v1/`. Its basename is producer-generated SHA-256 of the full canonical
bundle bytes plus `.json`; the bundle has no embedded self-digest. Observation IDs hash
their canonical bytes excluding their own ID. Exact concurrent replay publishes one
identical bundle; different observations of one request are retained for retrospective
revision/conflict resolution. Publication uses exclusive no-follow temporary creation
in the same directory and atomic no-overwrite install. There is at most one install
attempt per invocation; no lock/poll/retry loop or global history lock is introduced.
A partial file is never eligible for analysis or referenced by success.
A prior artifact is never replaced or silently repaired. Usage-only ingestion cannot
change `runs/`, lifecycle `seq`, `last_epoch`, duration, active run metadata or checkpoint
replay state, including when its declared run is closed or unverified.

Stored references are only producer-generated digest basenames, not caller-selected
paths: no separators, `..`, absolute path or symlink component is accepted. Resolve
the canonical usage root once and use regular files confined beneath it, with no-follow
operations or equivalent descriptor-relative checks to prevent path-swap escape.
Idempotent replay verifies the exact existing bundle digest/bytes and returns a duplicate
receipt; a corrupt existing target is diagnosed, never overwritten. Unknown temporary
files are ineligible, not interpreted as committed bundles.

The usage producer follows the legacy zero-exit, at-most-one bounded safe-diagnostic
contract; success requires an explicit typed receipt with the bundle digest and
observation identities. No receipt means acceptance is unacknowledged/unknown, not proof
that publication failed: death or lost stdout after install can leave the whole bundle
persisted. Retry only the exact canonical bundle and verify its content-addressed target
to obtain a duplicate receipt. Do not infer rejection, emit a synthetic receipt or claim
crash-proof exactly-once delivery.
Usage receipts and lifecycle checkpoint receipts have separate types. Pure helper CLI
exit codes are 0 for successful processing (including explicitly partial output), 2 for
invalid/unsupported invocation, 3 for source or output I/O failure; diagnostics contain
reason codes and opaque IDs, not source content. Validation failure publishes no report
claimed complete. Collection/analysis failure does not stop the owning workflow.

### Projections, immutability and read ownership

`step` optionally accepts `--tokens-in N --tokens-out N --cost-usd X` and
`--usage-file FILE` containing verified contributor references and their coverage.
Token-only scalars without source/profile evidence are caller-supplied unverified
aggregates; they cannot establish cache semantics, complete request coverage or an
additional additive cost. A supplied `--cost-usd` requires the self-contained structured
snapshot, scenario and calculation breakdown, and must equal the canonical exact
decimal amount, not its rounded display value; otherwise reject the whole lifecycle
invocation before any mutation. The scalar is permitted only for an independently
complete stated projection scope; partial priced components use a separately named
subtotal inside `--usage-file`, never a complete `cost_usd` scalar. Display-only amounts
have a separate non-additive field.
The writer validates only this explicit supplied snapshot and canonical schema, not
historical contributor artifacts or run summaries. Accepted projections remain derived
non-additive views and never prove native provider evidence by their presence alone.
Duplicate flags, mismatched contributor projections and invalid decimal/count inputs
also reject atomically. New canonical `cost_usd` projections mean API-equivalent USD;
historical values without a basis remain legacy/unverified, not retroactively relabeled.

References/projections may be supplied only on the first accepted lifecycle write.
Accepted checkpoint retries keep their original normalized payload exactly. Late usage
or repricing creates a separate artifact/report, never enriches or reopens that event.
Close-time summaries may use only the owner's receipt-derived private accumulator and
are provisional unless full inventory/finality is independently established; failure
or absence of that accumulator leaves them unavailable, not reconstructed from history.

Only retro selects lifecycle and usage history for analysis. Its pure `analyze` helper
receives a frozen explicit corpus manifest, including applicable inventories, price
snapshots and acceptance revisions; it never discovers the store. Inputs must pass
their schema/lint and digest checks before inclusion. Unknown runs or invalid lifecycle
records remain quarantined/unverified attribution, not silently joined by directory or
time. Existing timing-source eligibility and lint exclusions remain in force.

### Valuation and arithmetic

An `at_execution` scenario needs prices whose effective interval covers execution and
all original required service/region/model dimensions. A retrieval date alone cannot
prove historical applicability. A `reprice` scenario intentionally applies named fixed
snapshots and explicit dimensions to the same workload; its amounts are labeled
counterfactual API-equivalent values. Unknown original dimensions may be explicitly
assumed only in `reprice`, with those assumptions visible and no historical-bill claim.
Only tariff-scenario service tier, region and API pricing modality may be assumed for
repricing, with explicit labels. Actual model identity, usage quantities, cache lifetime,
threshold operands, inventory and ownership must remain evidenced; cross-model
simulation is outside this contract. Conflicting/overlapping snapshot applicability is
unavailable, never first-match-wins.
Price refresh is a separate explicit operation, preserves old snapshots on failure and
never occurs during normalization, aggregation, validation or ordinary collection.

For each request, sum disjoint quantity times applicable rate divided by the rate unit,
plus separately billed tool quantities. Context transmission is already included in
input. Snapshot predicates state their operand, exact boundary (`>` versus `>=`) and
affected components; a request-level context multiplier applies to the whole request
when its tariff says so, never to a run's cumulative input. Unsupported modalities or
tool units remain unpriced. Included reasoning is a subset; an independently priced
reasoning dimension is allowed only where an evidenced tariff and source define it.

Use exact arbitrary-precision aggregate integers and decimal monetary arithmetic.
No per-request cent rounding occurs before summation. Machine exports retain exact
decimal strings and explicit rate units; human USD values round once to two decimals
using half-even and disclose when displayed rows differ from the displayed total.
Prices, subtotals, lower bounds, caller-reported money and provider money have distinct
fields and status labels. A complete USD field is never filled with a partial sum.

### Advisory monitoring

Automatic collection and `usage-ingest` use `ORCHESTRAIL_USAGE_MODE=on|off`, scoped to
the invoking process and inherited hook execution; unset defaults to `off`. Invalid
values disable collection with a safe reason. Off produces no shared usage publication
or accepted receipt; legacy timing/logging is unaffected. Explicit read-only normalize,
analyze and status operations still work while collection is off. Enabling requires a
registered/authorized owner scope and verified profile; it never grants wider source
access. No settings file is changed automatically by this feature.

The owning process keeps a private collection segment boundary when mode changes;
re-enabling starts a new segment and declares the intervening gap. Missing prior private
state makes continuity unknown. No usage count is invented while off and no historical
backfill is performed implicitly. Existing evidence and delivered-warning state survive
disable/resume. An explicitly authorized later export can supply additional observations
without erasing the earlier gap or changing accepted lifecycle events.

`status` is a pure calculation over the current owner's explicit receipt snapshot;
it does not read historical artifacts. The authorized owner is the single writer of
that private state, reconciles request revisions by the same rules as retro, and never
adds receipt totals together. `status` returns current usage/cost and coverage, advisory
candidates with stable IDs, and proposed next private state; it does not deliver notes
or mutate its inputs. Unknown or missing accumulator state is unavailable, not a prompt
to recover history. Its snapshot also supports the normal completion report; there is
no background poller or mid-step alarm.

Duration observations come only from the current owner's timing receipts or executable
clock evidence and explicit threshold-export inputs, never a historical lookup. Usage
collection off does not disable duration advisories. A duration-only private snapshot
is valid without usage receipts; unavailable timing evidence yields an explicit reason.

The owner atomically accepts the next private state and performs idempotent note/report
updates keyed by warning ID. The ID includes run, policy version, scope, metric and
crossing episode. Repeated status calls return the same pending ID; retries/resume do
not add another warning. Crash between state persistence and note delivery leaves a
pending/recoverable delivery state, not a claim of exactly-once notification. Leaf
warnings belong in the leaf notes; run-only warnings belong in run notes. All warnings
appear in the final report. If a notes destination is unavailable, retain a pending
reason for the final report rather than writing an unrelated file or blocking execution.

Token and USD thresholds are optional explicit nonnegative policy values with a scope
(`request`, completed `span`, or current `run`) and units. There are no default USD or
token budgets. Token thresholds are bounded integers; USD thresholds are exact decimal
strings; coverage minima are exact decimals in [0,1]. Invalid policies are unavailable,
not partially applied. Expired or scope/version-incompatible token/USD/coverage policies
produce a policy-unavailable diagnostic and no crossing warning; only duration uses the
fixed fallback below. A warning fires on strict `measured_value > threshold` at an accepted
measurement/checkpoint; equality does not fire. A valid partial lower bound may warn
that the observed subtotal crossed, explicitly stating partial coverage; conflicted or
unpriced values cannot assert a monetary crossing. Coverage policies may warn on
`known_finalized_fraction < minimum_fraction`; unknown denominator yields a separate
unknown-coverage diagnostic, never a manufactured percentage. Return one candidate per
crossing episode and retain delivery state across owner restart and mode changes; only
a known noncrossing measurement resets the episode. Unknown values do not reset it.
A new policy version has its own identity. A late correction may establish a known
noncrossing state but never deletes an earlier warning; a later status explains its
revised evidence. Only the authorized shared-file writer adds notes and final reports.

Duration warnings evaluate completed measured work spans or closed run wall intervals
separately. Cohort key: canonical step, duration kind, timing-source quality and declared
compatible harness/profile/contract/configuration. Exclude waiting-only spans, synthetic
rollups, invalid timestamps, unfinished spans and the candidate observation. Do not mix
approximate intervals with measured work. An explicit retro threshold export supplies
corpus digest, sample window, eligible count, median, generated-at and valid-until;
expired, incompatible or missing exports use the fixed rule, not invented history.
With fewer than five usable cohort samples or unavailable history, warn iff duration
is greater than 7200 seconds; with at least five, warn iff it is greater than both
7200 seconds and three times the median. Approximate intervals may show a labeled
duration notice, not a measured historical anomaly. Policies never stop, retry, reroute
or change workflow/model execution.

### Retrospective output and comparison

Export canonical versioned JSON plus Markdown and CSV summaries. Include corpus and
scenario IDs, as-of, versions, source/deployed hashes where exposed, inventory and all
coverage dimensions, exclusions, late observations, conflicted identities, unpriced
model/tool counts, contributor IDs and calculation terms. Stable sort keys make row and
input-order permutations semantically identical. Raw source manifests remain local;
public fixtures/exports contain synthetic or explicitly sanitized metadata only.

Report per run/opportunity/root approach/nested stage/role/model/effort/attempt with
sample counts; input/cache/output/reasoning mix; requests, retries and escalation;
duration kinds; and five most expensive completely valued leaves. Partial priced leaves
have a separate partial-subtotal list with `proven_lower_bound` or `subtotal_only`
labels according to the proof rules; conflicted/unresolved overlap is unrankable, and
no partial list establishes the cheapest. Median sorts usable
values and averages the two middle values for even n; p90 is nearest-rank at
`ceil(0.9*n)`. Empty cohorts are unavailable; n below five is labeled small-sample.
Complete cost distributions and partial-subtotal distributions never share a percentile.
Unfinished, rejected, missing and censored opportunities remain visible with their costs.

Opportunity identity includes task/input revision, acceptance contract, strategy arm
and independent repetition. Resumed invocations and repairs stay inside that identity.
Independent acceptance labels carry evaluator/source, contract, observed-at and revision;
an escaped-defect correction produces an as-of label revision, not an edited history.
Observed cost per accepted result = all observed workload cost in that declared cohort
divided by independently accepted opportunities. Include rejected/failed work, repairs,
orchestration and production verification in the numerator; zero accepted results is
unavailable. Missing cost/censoring makes the ratio partial/descriptive, not unbiased
expected success cost. Additional independent experimental evaluation overhead is
reported separately, with an optional all-in total, never counted twice as production
verification.

Qualified comparisons require the same task set/initial revision/acceptance criteria,
declared repetitions and quality policy, compatible measurement coverage, and one
valuation basis. Root approaches are compared at root scope; nested phase and atomic
costs are exclusive stage breakdowns inside a root rollup, not independent competitors.
Partial or unmatched cohorts cannot establish cheapest or most effective. Model choice,
effort, task size and quality floors remain owned by their consumer specs; this feature
only provides evidence and never applies an optimization automatically.

Optional diagnostics use a canonical namespaced registry of numeric value, unit,
scope/contributor IDs, source and measurement quality. Initial supported namespaces
cover context loads/bytes/cache observations, controller/tool calls/checkpoints,
review scope/reuse, tool preview/full/retrieved bytes, repair/escalation and
decomposition/setup/integration. Consumers own producing these values. The registry
does not make their instrumentation mandatory or convert bytes/words to tokens.

## Non-Functional Requirements

| Attribute | Target | Verification |
|---|---|---|
| Nonblocking compatibility | Zero changes to legacy invocation behavior; usage producer exit 0 on all paths; zero workflow stops caused by telemetry failure. | Isolated acceptance fixtures with missing dependencies and failed writes. |
| Exactness | No binary-floating monetary summation; no aggregate integer overflow at the per-event bound. | Decimal/integer golden arithmetic and permutation fixtures. |
| Offline operation | Zero model calls, price lookups or network calls during capture, normalization, analysis or ordinary checks. | Network/model stubs fail if invoked. Explicit price refresh is tested separately offline with snapshots. |
| Input bounds | At most 16 MiB per selected source record, 1 MiB per normalized observation, 10,000 observations and 32 MiB per ingestion bundle; at most 256 characters per opaque identifier and 64 candidate owners per observation. | Exact-boundary and one-over fixtures; oversize data produces a declared exclusion/failure, never silent truncation. Larger imports require explicit bounded bundles. |
| Persistence | New private directories 0700 and metadata files 0600; immutable no-overwrite publication; no success receipt before full artifact visibility. | Permission, process interruption and concurrent-publication fixtures. Existing unrelated directories are not chmod'ed. |
| Scope and privacy | Zero credential reads, arbitrary project scans, persisted conversation bodies or external absolute source paths. | Forbidden-field/path/symlink and instrumented file-access fixtures. |
| Diagnostics | Usage-producer diagnostics are at most one line and 512 UTF-8 bytes per invocation; structured helper diagnostics use bounded opaque IDs/reason codes only. | Oversize/error fixtures verify bounds and no payload echoes. |
| Determinism | Equal inputs/profile/scenario yield identical sorted canonical output except declared creation timestamps. | Byte comparison and input permutation fixtures. |
| Runtime dependencies | Legacy producer retains its existing optional-jq path; Python 3.10+ standard library is optional for the new usage helper only. | Missing Python/jq fixtures show explicit usage unavailability and working legacy logging. |
| Performance claims | No wall-time/RSS claim without a declared machine, corpus, selected record count and profile. Processing is bounded by the declared input/bundle limits and never rereads history per request. | Fixture access trace and bounded-bundle checks; any later benchmark reports its profile. |

## Edge Cases & Failure Modes

| Case | Required behavior |
|---|---|
| Empty export or no eligible requests | Known empty inventory differs from unknown inventory; no 0/0, invented 100%, or fabricated zero cost for absent data. |
| Initial stream usage only; interrupted stream | Keep partial state and valid components; no final cost solely from output size, process exit or maximum counter. |
| Out-of-order replay, corrected final, conflicting finals | Use declared identity/revision semantics; duplicates count once; unsupported conflicts remain excluded. |
| Missing IDs; reset cumulative counters; inherited history | No fingerprint-based exactness or invented per-request deltas; report aggregate-only/unknown identity and gaps. |
| Shared request, root-only controller, after-close usage | Preserve one supported pool/owner; no leaf split; append late observations without lifecycle mutation. |
| Unknown model, internal review, rate/TTL/context operand missing | Keep measured tokens and unpriced components; no substitution, TTL default or complete-dollar total. |
| Failed, cancelled, rejected or timed-out work | Retain known billable usage/outcome; unknown usage is not zero. |
| Malformed producer arguments, duplicate keys, unsupported normalized schema | Reject the full invocation before any mutation; one safe producer diagnostic and no success receipt. |
| Invalid record within an otherwise usable explicit export | Quarantine sanitized identity/reason and exclude affected dimensions; preserve other usable records and disclose denominator impact. |
| Unauthorized source, path traversal, symlink escape, forbidden payload field | Reject or exclude without exposing content or reading outside the explicit scope. |
| Concurrent identical publication or interruption | One immutable visible artifact; no partial success. Retry is idempotent. Conflicting observation revisions resolve during analysis, not overwrite. |
| Corrupt/missing/changed referenced artifact or selected input | Disclose exclusion or fail the dependent report's completeness; do not repair historical data. |
| Disk full, permissions or concurrent publication contention | Return a diagnostic and no acknowledgment on failure; a completed install may persist with unknown acknowledgment. Exact retry checks the target. No lock/wait loop or global history lock. |
| Disabled/missing adapter or dependency | Legacy workflow continues; status explains gap; re-enable starts a new collection checkpoint with no silent history scan. |
| Stale policy, noncomparable cohort, equality at threshold | Use documented fixed duration fallback; do not invent cost/token thresholds or fire on equality. |
| Cleanup or retention | No automatic deletion of accepted evidence. Removing producer-owned unpublished temporary files is permitted; source transcripts stay source-owned. Future evidence cleanup requires a scoped dry-run and referenced-evidence safeguards. |

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-09, REQ-15) Both included-input and separate-input synthetic
  exports normalize without hooks; absent actual-model/effort and unsupported profile
  versions produce explicit unavailable states. A timing-only receipt cannot establish
  usage or inventory completeness; access probes confirm only selected sources are read.
- [ ] **AC-02** (REQ-02, REQ-03, REQ-21) Synthetic rates and quantities in the arithmetic
  fixtures below produce exact $0.00264, $0.00289 and unknown-TTL priced subtotal
  $0.00224, with reasoning included once and missing dimensions never treated as zero.
- [ ] **AC-03** (REQ-04, REQ-08, REQ-10, REQ-18) Duplicate/fork/nested/parallel fixtures
  count each evidenced request once, retain shared pools, distinguish timing kinds and
  show separate known/unknown coverage denominators without additive parent charges.
- [ ] **AC-04** (REQ-05, REQ-06, REQ-21) Versioned fixtures cover cache TTL, threshold
  equality/one-over, service/region applicability, separate tool charges, conflicting
  rate intervals, explicit repricing and missing historical rates. Unknown internal
  model pricing leaves its request/tokens visible and cost unavailable.
- [ ] **AC-05** (REQ-07, REQ-20) Invalid scalar/structured projections and unsupported
  `--cost-usd` leave lifecycle bytes, sequence, clocks and active metadata unchanged;
  accepted correlated replay stays byte-equivalent and legacy optional-jq checks pass.
- [ ] **AC-06** (REQ-11, REQ-22) Four/five-sample duration fixtures, strict 7200-second and
  three-median boundaries, candidate exclusion, and expired/incompatible threshold
  exports yield the declared warning behavior without a stop or historical store read.
  A valid current-owner duration-only snapshot still produces its warning when usage
  collection is off, while missing timing evidence remains unavailable.
- [ ] **AC-07** (REQ-12, REQ-13, REQ-26) Accepted/rejected/resumed/censored fixtures yield
  the declared opportunity counts and $1.50 observed workload cost; zero accepted
  results is unavailable. LLM DONE alone cannot supply acceptance or a savings claim.
- [ ] **AC-08** (REQ-14, REQ-24, REQ-25) Documentation and isolated offline smoke/contract
  checks cover scope consent, profiles, price refresh, baseline export, disable/resume,
  dependency absence, legacy values and recovery without history rewriting or paid calls.
- [ ] **AC-09** (REQ-04, REQ-16) Partial output snapshots 1, 40 and final 100 resolve to
  output 100 and $0.00264 regardless of order/replay; summing them to 141 fails. Without
  a final, output 40 remains partial. Deltas 10 at sequence 1 and 30 at sequence 3 with
  missing sequence 2 and terminal 4 remain partial 40. Delta replay counts once;
  conflicting same-ID deltas/finals require explicit correction evidence or quarantine.
- [ ] **AC-10** (REQ-17) Adjacent cumulative snapshots with one inventoried request
  fully bracketed by those snapshots permit its exact delta. If the request started at
  counter 90 but available snapshots are mid-request 100 and final 110, delta 10 cannot
  establish full request usage 20. Reset, gap, multiple-request and unknown-epoch cases
  never fabricate a per-request delta or add overlapping provider aggregates.
- [ ] **AC-11** (REQ-08, REQ-15) Two independently inventoried final requests with one
  unknown tariff yield token coverage 2/2 and valuation coverage 1/2. The same parsed
  rows without inventory yield unknown coverage; a known empty billable scope has exact
  zero cost and not_applicable coverage. Call/response aliases count once, one call with
  two responses yields two request slots, and unresolved fan-out prevents a known
  denominator rather than producing coverage greater than one or a free missing call.
- [ ] **AC-12** (REQ-18, REQ-19) A $0.10 request shared by two candidate leaves remains
  one $0.10 common pool, not $0.05 per leaf; explicitly linked after-close usage changes
  only a new as-of report, and replayed timestamps cannot create measured durations.
- [ ] **AC-13** (REQ-19, REQ-20) Many requests for one step, a late final, and a new price
  scenario publish usage/report revisions while checksums of all accepted lifecycle
  events and checkpoint metadata remain unchanged. Prior reports stay reproducible.
- [ ] **AC-14** (REQ-20, REQ-25) Concurrent exact bundle replay yields one visible artifact;
  interrupted/full-disk/permission-failed publication returns no success receipt and
  no partial referenced file. Death/lost stdout after full install leaves acknowledgment
  unknown; exact retry returns a duplicate receipt. No crash-proof delivery claim is made,
  and retry neither duplicates cost nor advances lifecycle timing.
- [ ] **AC-15** (REQ-09, REQ-20, REQ-25) Duplicate-key, oversized, forbidden-field,
  traversal, symlink, digest-mismatch and changing-input fixtures disclose exclusions or
  fail as specified, without credentials, conversation bodies or external paths in logs.
- [ ] **AC-16** (REQ-06, REQ-21) Exact totals above the per-observation integer bound are
  preserved. Two $0.005 request costs sum to $0.010 and display $0.01; two $0.015 costs
  sum to $0.030 and display $0.03 rather than per-item rounded $0.04. Exact $0.00264
  cannot be supplied as canonical $0.00; unverified scalars cannot populate verified cost.
- [ ] **AC-17** (REQ-22, REQ-25) Explicit token/USD/coverage policies test equality,
  crossing, replay, late correction and known reset; each crossing emits once and labels
  partial/unknown coverage. Repeated pure status calls return the same candidate ID;
  owner restart and collection disable/resume preserve delivery state and idempotent
  notes/final-report updates. Expired policies and coverage minima outside [0,1] yield
  no crossing warning. No policy means no invented threshold, stop or model call.
- [ ] **AC-18** (REQ-12, REQ-24) Values {1,2,3,4} produce n=4, median 2.5 and p90 4 with
  a small-sample label. Empty, partial and complete cohorts remain separate; repeated
  input permutations produce matching canonical JSON, Markdown and CSV semantics.
- [ ] **AC-19** (REQ-13, REQ-26) Resumed repairs count as one result opportunity;
  acceptance/escaped-defect revisions change only new as-of reports. Independent
  experiment evaluation cost remains separate from production review and an all-in
  report adds it once. Incomparable task or valuation arms cannot name a cost winner.
- [ ] **AC-20** (REQ-23, REQ-24) Synthetic metadata from each diagnostic namespace keeps
  units, scope, source and inferred/measured quality. Missing diagnostics are unavailable,
  and byte reductions alone cannot populate tokens, dollars or quality conclusions.

### Synthetic arithmetic fixtures

All prices here are invented test data per 1,000,000 tokens: ordinary input $2,
cache read $0.20, short write $2.50, long write $4 and output $10. They are not current
provider prices. Input/output totals and reasoning are interpreted by the chosen profile.

| Fixture | Expected exact result |
|---|---|
| Included input 1000, read subset 200, no applicable writes, output 100, reasoning subset 40; or separate ordinary 800 + read 200 + output 100. | Ordinary 800, input 1000, output 100; $0.00264. |
| Ordinary 600 + read 200 + short write 100 + long write 100 + output 100. | Input 1000; $0.00289. |
| Same total write 200, TTL unknown; ordinary 600 + read 200 + output 100 known. | Known priced subtotal $0.00224; no complete cost or guessed TTL. |
| Synthetic context predicate input > 1000, multiplying all input prices by 2 and output by 1.5. | At input 1000 use $0.00264; at ordinary 801 + read 200 + output 100 use $0.004784. |
| Failed execution $0.40 + resumed accepted repair $0.60; separate rejected opportunity $0.30; separate censored opportunity $0.20. | Three opportunities, one accepted; total observed $1.50; descriptive ratio $1.50 with censoring disclosed. |
| Two independently inventoried requests, second an internal unknown-price model with input 500 and output 50. | Both retain known tokens; valuation 1/2; second cost unknown, never zero. |

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-02 |
| REQ-03 | AC-02 |
| REQ-04 | AC-03, AC-09 |
| REQ-05 | AC-04 |
| REQ-06 | AC-04, AC-16 |
| REQ-07 | AC-05 |
| REQ-08 | AC-03, AC-11 |
| REQ-09 | AC-01, AC-15 |
| REQ-10 | AC-03 |
| REQ-11 | AC-06 |
| REQ-12 | AC-07, AC-18 |
| REQ-13 | AC-07, AC-19 |
| REQ-14 | AC-08 |
| REQ-15 | AC-01, AC-11 |
| REQ-16 | AC-09 |
| REQ-17 | AC-10 |
| REQ-18 | AC-03, AC-12 |
| REQ-19 | AC-12, AC-13 |
| REQ-20 | AC-05, AC-13, AC-14, AC-15 |
| REQ-21 | AC-02, AC-04, AC-16 |
| REQ-22 | AC-06, AC-17 |
| REQ-23 | AC-20 |
| REQ-24 | AC-08, AC-18, AC-20 |
| REQ-25 | AC-08, AC-14, AC-15, AC-17 |
| REQ-26 | AC-07, AC-19 |

## Risks

| Risk | Consequence | Mitigation |
|---|---|---|
| Harness exposes only partial counters or no request inventory | Complete dollars cannot be established. | Source capability evidence and per-dimension unknown states; no promise to recover hidden counters. |
| Wrong finality, counter scope or alias mapping | False savings, duplication or incorrect prices. | Versioned profiles, explicit revisions, exact fixtures and unknown/conflict states. |
| Optional telemetry affects the workflow clock or replay | Broken process/timing evidence. | Separate immutable publication, checksum acceptance and no late lifecycle enrichment. |
| Private source content leaks through provenance or errors | Sensitive metadata is exposed. | Numeric allowlists, opaque source IDs, confined artifacts and safe diagnostics. |
| Advisories become implicit budgets or routing | Changes accepted workflow behavior. | Explicit warning-only policy, no execution effects and unchanged no-budget decision. |
| Feature grows into a state engine or monitoring service | Implementation becomes a new platform. | Eight bounded implementation slices; no daemon, dashboard, mandatory runtime or generalized retention. |

## Assumptions

Both harnesses may expose different subsets of usage; a comparable complete baseline
is not guaranteed. Missing data can prevent a financial conclusion without blocking
implementation of honest telemetry.

- A-01 | Scope of this refinement | Resolved: improve the existing telemetry specification autonomously; implementation remains unstarted. | Source: owner's 2026-10-27 request. | Reversible: yes.
- A-02 | Request observations versus lifecycle events | Resolved: separate immutable usage artifacts and first-write-only lifecycle references. | Source: existing timing/replay contracts at `scripts/log-step.sh:845` and `rules/run-log.md → ## Correlated hook intervals`. | Reversible: yes, before implementation contract approval.
- A-03 | Missing live counter capability | Resolved: explicit selected-export support or unavailable profile; no speculative native hooks. | Source: current hook forwarding at `hooks/log-step-hook.sh:355`. | Reversible: yes.
- A-04 | Advisory scope | Resolved: local explicit token/USD/coverage warnings with no enforced production budgets or external messages. | Source: existing no-budget decision and owner's transparency goal. | Reversible: yes.
- A-05 | Historical/current price ambiguity | Resolved: separate at_execution and reprice scenarios; unknown historical dimensions remain unknown. | Source: existing API-equivalent definition and best practice. | Reversible: yes.
- A-06 | Unknown request ownership | Resolved: common-scope shared/unattributed pools, never arbitrary leaf splits. | Source: prior retrospective evidence and best practice. | Reversible: yes.
- A-07 | Publication limits/runtime | Resolved: explicit bounded bundles and an optional standard-library helper; legacy producer dependency behavior unchanged. | Source: existing non-blocking producer contract and best practice. | Reversible: yes.
- A-08 | Coverage proof | Resolved: independent inventory/finality evidence; source limitations can make complete accounting impossible. | Source: prior retrospective evidence and official provider observability semantics. | Reversible: yes.
- A-09 | Statistical and presentation conventions | Resolved: nearest-rank p90, n<5 notice, exact decimals and final half-even cents. | Source: best practice, chosen for deterministic offline acceptance. | Reversible: yes.
- A-10 | Consumer diagnostic scope | Resolved: accept optional typed metadata now; consumer instrumentation and optimization policy stay with their owning specs. | Source: existing shared metric ownership in the roadmap. | Reversible: yes.
- A-11 | Collection enablement | Resolved: process-scoped explicit on/off with default off; read-only analysis remains available and duration advisories retain their existing obligation. | Source: optional collection/privacy constraints and best practice. | Reversible: yes.
- A-12 | Lost acknowledgment | Resolved: one immutable bundle can persist without a receipt; exact replay verifies it instead of inferring rejection. | Source: uncertain-persistence contract at `rules/run-log.md → ## Correlated hook intervals`. | Reversible: yes.
- A-13 | Advisory delivery state | Resolved: pure status returns stable candidates/next state; the authorized owner performs private-state and idempotent notes/report updates. | Source: project single-writer invariant and best practice. | Reversible: yes.

## Decisions

Retain ADR-0009's no-budget policy and ADR-0011's strict, non-blocking log contract.
The owner's current request adds API-equivalent valuation under subscription billing.
Do not silently upgrade a model or infer a current rate from historical prose.

2026-10-27: the additions above are proposed specification contracts, not a change to
deployed behavior or an approval of experiments. Record the concrete additive runtime
contract decision before implementation changes public producer/reader formats. Existing
timing and correlation decisions remain effective.

## Clarifications

2026-10-21: the old unconditional "Codex omits cost" becomes "omit unless reliably
measured and valuably priced"; hook availability alone does not determine usage access.
Anomaly history is exported only by retro, preserving its exclusive shared-store role.

### Session 2026-10-27

Owner request, translated: perform a full additional analysis and improve this
specification to close gaps, inaccuracies, problems and ambiguities. Existing edits are
authorized. Source text and requirement/acceptance IDs are preserved; new requirements
and acceptance cases are appended. No clarification questions or paid experiments were
needed. Full audit considered all nine authoring categories: scope, data model, flow,
non-functional behavior, integrations, failures, constraints, terminology and acceptance.

## Open Questions

None blocking. A source profile that cannot prove usage finality, complete inventory,
actual model identity or prices must expose that limitation; implementing honest partial
coverage does not require those unavailable measurements. Live source-version capability
verification and any paid experiment settings remain execution-time evidence/authorization,
not permission to guess missing data or start an experiment during this task.

## Notes

Depends on completed vocabulary and correlated timing foundations. Spec 04 owns catalog
selection, this spec owns monetary snapshots/usage, and spec 09 owns qualified quality
comparison. Existing optimization consumers remain 08 and 14-20. Source profiles use
capabilities and current helper paths; the wider harness naming migration is not a
prerequisite for deterministic telemetry fixtures. Do not repeat completed hook work.

Suggested maximum eight implementation slices: canonical schema/profiles and fixtures;
scoped adapters; immutable ingress and lifecycle projections; reconciliation/inventory/
ownership; price scenarios and arithmetic; retrospective exports and acceptance cohorts;
current-run status/advisories; compatibility, recovery and documentation. No task
directories or implementation subtasks are created by this authoring pass.

Rejected alternatives: one step per request changes timing; enriching old checkpoints
breaks replay; max partial usage fabricates finality; assigning unknown review models a
public price fabricates money; forced leaf splits fabricate precision; a global session
scan violates scope; dashboard/budget enforcement adds an unrelated operational system.

Implementation-time primary references, verified 2026-10-27; revalidate adapter versions
before claiming support. These sources establish semantics, not a pinned production rate:

- [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [OpenAI observability and usage](https://developers.openai.com/api/docs/guides/agents-api/observability)
- [Anthropic streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)
- [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

## Readiness Checklist

| Check | Result |
|---|---|
| Goal is one paragraph in domain language | PASS |
| Concrete scope and exclusions are defined | PASS |
| Requirements retain stable IDs and EARS triggers | PASS |
| Every requirement and acceptance case is traced | PASS |
| Acceptance outcomes are binary and observable offline | PASS |
| Non-functional targets are numeric or explicitly bounded | PASS |
| Data model, proposed interfaces and errors are defined | PASS |
| Empty/error/boundary/concurrency cases are covered | PASS |
| Authoring ambiguities are resolved and recorded | PASS |
| No blocking open question remains | PASS |
| Existing-code claims carry verified path/line evidence | PASS |
| Existing project terminology is retained | PASS |
| Feature is bounded to at most eight implementation slices | PASS |

Verdict: READY FOR DEVELOPMENT following document validation and independent adversarial
review. This is an automated readiness assessment, not human sign-off or evidence of
implementation. Review the proposed contracts before implementation; live savings remain
unmeasured.
