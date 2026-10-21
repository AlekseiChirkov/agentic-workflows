# Reliable usage telemetry, API-equivalent cost and baseline

## Source

Owner request, 2026-10-21, translated: optimize total cost of a correct result; actual
billing is a fixed subscription, but value every observable task at API prices; do not
invent measurements or launch paid experiments. This expands the existing telemetry
spec without reintroducing production budgets (ADR-0009 Decision 5).

## Context & Problem

The canonical log currently defines event vocabulary and missing-versus-zero semantics
(`rules/run-log.md:116`, `scripts/log-step.sh`). Completed spec 02 protects validation,
non-blocking writes and historical logs. Those guarantees must survive the additive
usage extension. Role, retry, cache, price and coverage information are needed before
any optimization can be evaluated. A total copied from overlapping session histories
or parent/child summaries is not a valid baseline.

## Goal

Make observed usage and total cost of independently accepted results auditable across
both supported harnesses, including cache effects, failed attempts and missing data.

## Scope

Usage adapters, additive telemetry schema, versioned valuation, aggregation, baseline
reporting and anomaly warnings. This owns workstream 1 and the shared metric contract.

## Out of Scope

Production spend/time limits, mandatory new runtime, subscription quota prediction,
automatic routing changes, rewriting historical logs, or automatically running models.

## Actors & Roles

The adapter extracts available measurements; the authorized orchestrator attributes
events and writes shared notes; `/retro` alone reads the shared log store. An optional
normalizer may consume explicitly supplied session exports without reading unrelated
sessions. Evaluation tools consume exported aggregates, not the shared store.

## Terminology

- **API-equivalent cost**: token/tool usage valued using an identified public API price
  snapshot; distinct from subscription payment, provider-reported cost and quotas.
- **Request**: one actual model response, counted once even when present in forked logs.
- **Attempt**: execution or repair on a leaf, with separate verification spans.
- **Coverage**: usable measured observations divided by eligible observed observations,
  with unavailable dimensions reported separately.

## Requirements

- **REQ-01** WHEN measurements are available, THE SYSTEM SHALL record run, project,
  session/agent, parent span, request ID, task/leaf, role, stage, attempt, requested and
  actual model, requested and actual effort if exposed, harness version, source commit,
  deployed contract hash and measurement source; unavailable values SHALL be omitted
  with an explicit coverage reason, not inferred as zero or session defaults.
- **REQ-02** WHEN normalizing provider usage, THE SYSTEM SHALL preserve raw counter names
  and values and produce disjoint buckets: uncached input, cache-read input, cache-write
  input by available TTL, and output including reasoning where the provider includes it.
  `tokens_in` SHALL be the sum of disjoint input buckets, and `tokens_out` the provider's
  total output. Reasoning SHALL be a reported subset where applicable, never added a
  second time. OpenAI-style cached input included in input and Anthropic-style separate
  cache counters SHALL have distinct tested normalization mappings.
- **REQ-03** IF a counter, TTL, model identity or pricing dimension is missing or
  contradictory, THEN THE SYSTEM SHALL retain available measurements, mark coverage
  partial/unavailable and omit unsupported totals; it SHALL NOT estimate tokens from
  characters or equate absence with zero.
- **REQ-04** WHEN ingesting an event again or ingesting forked histories, THE SYSTEM
  SHALL deduplicate by provider response identity plus account/session scope as needed,
  retain attribution provenance, and report unresolvable identity collisions. A response
  SHALL belong to one billing leaf/span; parent summaries SHALL not add its cost again.
- **REQ-05** THE SYSTEM SHALL maintain local versioned price snapshots with model ID,
  currency, effective/retrieval dates, authoritative source URL, token unit, input,
  cached-read, cache-write/TTL, output/reasoning treatment, applicable long-context
  thresholds and tool/service charges. Refresh SHALL be explicit; an absent/inapplicable
  rate SHALL yield an unavailable valuation, not a fallback rate from another model.
- **REQ-06** WHEN valuing usage, THE SYSTEM SHALL use disjoint billed quantities and the
  matching price snapshot. It SHALL label `cost_usd` as API-equivalent USD in every new
  report, retain the price ID and calculation breakdown, and keep any provider-reported
  monetary value separately with its meaning. Subscription cash payment SHALL never be
  described as per-request API spending or inferred quota consumption.
- **REQ-07** THE SYSTEM SHALL extend `scripts/log-step.sh step` with optional
  `--tokens-in N --tokens-out N --cost-usd X` and a documented structured usage input
  for detailed dimensions. Counts SHALL follow the existing integer bound; cost SHALL
  be finite nonnegative decimal USD. Duplicate/conflicting supplied fields SHALL reject
  the entire event before mutation with the existing non-blocking single diagnostic.
  Writing and lint SHALL share schema definitions; old valid events SHALL remain valid.
- **REQ-08** WHEN closing a run, THE SYSTEM SHALL sum nonoverlapping measured events,
  expose per-dimension coverage and any measured subtotal, and publish a complete run
  total only when all eligible contributing events for that dimension are covered.
  Missing request inventory SHALL make coverage unknown, not 100 percent.
- **REQ-09** WHERE a harness exposes reliable usage through hooks, THE SYSTEM SHALL use
  the spec 03 adapter; WHERE an explicitly provided read-only session export exposes it,
  THE SYSTEM SHALL support normalization without hooks. Neither support nor absence
  SHALL be inferred from the harness name. No adapter SHALL read credentials, modify
  transcripts, scan arbitrary projects, or persist prompts/source code in the log.
- **REQ-10** WHEN reporting durations, THE SYSTEM SHALL distinguish run wall time,
  per-span inclusive time, exclusive time where derivable, and sum of worker time.
  Nested or parallel spans SHALL never be presented as additive run wall time.
  Approximate prompt-driven intervals SHALL be labeled as such.
- **REQ-11** WHEN fewer than five usable duration samples exist for a step, THE SYSTEM
  SHALL flag durations over two hours; otherwise it SHALL flag durations over both
  three times the median and two hours. The orchestrator SHALL append the warning to
  the owning notes and final report. The run SHALL continue. `/retro` SHALL export
  threshold summaries for active use; live workflows SHALL NOT read the log store.
- **REQ-12** WHEN `/retro` builds a baseline, THE SYSTEM SHALL report median/p90 and
  sample counts by run, pipeline, role, stage, model, effort, leaf and attempt; cache
  mix; retry/escalation counts; the five most expensive measured leaves; missingness,
  lint exclusions, source/deployed drift and censored/unfinished runs. Small samples
  SHALL be labeled and never treated as reliable model-success estimates.
- **REQ-13** WHEN joining independent acceptance labels from spec 09, THE SYSTEM SHALL
  report both total observed workload cost divided by independently accepted results
  and cost per observed run/attempt. It SHALL include failed/rejected attempts and
  review costs; it SHALL NOT label an LLM's DONE verdict as independently correct.
- **REQ-14** THE SYSTEM SHALL publish a reproducible baseline procedure, anonymized
  synthetic fixtures and the formulas below. Shared gates G1–G8 in the index SHALL apply.
  Paid collection/comparison SHALL require a separately approved experiment manifest.

## Data Model

Additive, schema-versioned usage records associate the identities in REQ-01 with
`usage.raw`, `usage.normalized`, `usage.coverage`, `usage_source`, `price_snapshot_id`,
`cost_basis: api-equivalent`, observed tool charges and span timestamps.
Detailed usage can be supplied by a local JSON sidecar referenced from an additive
event field. Discovery chooses inline versus sidecar storage and records the contract
once; neither option may introduce a second independent event vocabulary.
Legacy `tokens_in`, `tokens_out`, `cost_usd` projections follow REQ-02/06/08.

## Contracts & Interfaces

Existing `step`, `run-end`, `lint`, `contract`, `path` and `active` behavior remains.
New fields must extend the producer, canonical rule, linter, retro reader and contract
validator together. A supplied invalid new field cannot partially append an event.

For each request, cost is the sum of disjoint input/cache/output quantities times their
applicable rates per token, plus separately charged tools. Context transmission is
already in those input quantities: report its attribution, do not add it again.
Reasoning receives a separate charge only when the provider's tariff actually does so.

Total result cost = planning + execution + verification + repair + escalation + tools,
with each request charged once. For repeated independent runs:
cost per independently accepted result = total observed cost / accepted-result count.
A zero denominator is unavailable. This observed ratio is not an unbiased estimate
when missing/censored observations are excluded; disclose that limitation.

## Non-Functional Requirements

Offline fixtures must reproduce expected arithmetic exactly using decimal monetary
arithmetic. No price lookup or model invocation occurs during validation or aggregation.
Telemetry remains best-effort, privacy-preserving, optional and non-blocking.
The same fixture input produces byte-identical normalized records except declared
timestamps; no timing benchmark is claimed without a recorded machine/profile.

## Edge Cases & Failure Modes

Cover absent and zero counters, malformed/negative/oversized integers, NaN/infinite
costs, expired or missing rates, unknown model aliases, TTL mixtures, context-tier
pricing, streaming final versus cumulative counters, duplicate exports, resumed agents,
parent-child summaries, active runs, clock anomalies, corrupt sidecars, missing tools
and unwritable stores. On ambiguity report partial coverage; never repair history.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-09) Synthetic exports from both counter conventions normalize
  without hooks; absent actual-model/effort data is explicit and no unrelated session
  or credential file is accessed.
- [ ] **AC-02** (REQ-02, REQ-03) Fixtures with included versus separate cache counts,
  cache TTLs, reasoning subsets, actual zeros and omissions yield hand-verified disjoint
  totals; missing dimensions cannot silently produce a complete total.
- [ ] **AC-03** (REQ-04, REQ-08, REQ-10) Duplicate/fork/nested/parallel fixtures count each
  request once, show coverage denominators and distinguish wall time from worker time.
- [ ] **AC-04** (REQ-05, REQ-06) Versioned price fixtures exercise ordinary, cached,
  cache-write, long-context and separately charged tool cases; unknown rates yield
  unavailable valuation and API-equivalent labels are present.
- [ ] **AC-05** (REQ-07) Invalid new CLI/JSON inputs leave JSONL, seq, timestamps and
  active metadata untouched; old log tests still pass and producer/doc/lint drift fails.
- [ ] **AC-06** (REQ-11) Four/five-sample, exactly-two-hour and exactly-three-median
  boundary fixtures follow strict greater-than semantics and never stop execution.
- [ ] **AC-07** (REQ-12, REQ-13) A corpus containing rejected, accepted, incomplete and
  duplicate attempts yields expected denominators and accepted-result cost; a reviewer
  verdict alone cannot populate an independent quality label.
- [ ] **AC-08** (REQ-14) Documentation covers local adapters, consent/scope, price refresh,
  baseline export, disable/resume and legacy fields; offline contract/smoke fixtures pass
  and the baseline report distinguishes measurements, simulations and unavailable data.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-09 | AC-01 |
| REQ-02, REQ-03 | AC-02 |
| REQ-04, REQ-08, REQ-10 | AC-03 |
| REQ-05, REQ-06 | AC-04 |
| REQ-07 | AC-05 |
| REQ-11 | AC-06 |
| REQ-12, REQ-13 | AC-07 |
| REQ-14 | AC-08 |

## Risks

Wrong cache semantics or deduplication can dominate apparent savings. Retain raw
counter provenance and auditable per-request calculations. Private transcripts must
stay local; committed fixtures contain synthetic data only.

## Assumptions

Both harnesses may expose different subsets of usage; a comparable complete baseline
is not guaranteed. Missing data can prevent a financial conclusion without blocking
implementation of honest telemetry.

## Decisions

Retain ADR-0009's no-budget policy and ADR-0011's strict, non-blocking log contract.
The owner's current request adds API-equivalent valuation under subscription billing.
Do not silently upgrade a model or infer a current rate from historical prose.

## Clarifications

2026-10-21: the old unconditional "Codex omits cost" becomes "omit unless reliably
measured and valuably priced"; hook availability alone does not determine usage access.
Anomaly history is exported only by retro, preserving its exclusive shared-store role.

## Open Questions

No blocking implementation question. Price/model availability and paid experiment
settings must be verified when explicitly collecting or comparing live runs.

## Notes

Depends on 02 (completed vocabulary), 03 (correlated collection). Consumers: 04 price
references, 09 evaluation, and all nine workstreams. Catalog selection remains spec 04;
this spec owns price snapshots, not model capability ranking.
Suggested slices: schema/fixtures; adapters; pricing; aggregation; retro/baseline;
documentation and compatibility. Smoke/contract tests are deterministic.

## Readiness Checklist

Source and scope recorded; requirements and binary acceptance mapped; legacy and
failure behavior specified; no production budgets or paid-run authorization implied.
Ready for Discovery; live savings remain unmeasured.
