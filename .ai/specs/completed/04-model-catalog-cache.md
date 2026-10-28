---
status: done
completed_task: task-04-model-catalog-cache
completed_at: 2026-10-28
---

# Cached model catalog and consistent, availability-aware selection

## Source

ADR-0009 Decision 6 and the owner's 2026-10-21 request to prefer the least expected
total cost of a correct result, including the possibility that strong-first is cheaper.

## Context & Problem

The selector still rebuilds its catalog through live web search on every invocation
(`workflows/pd-select-model.md → ### Step 0 — Build the model catalog via live web search (every run, no file)`).
The 2026-10-28 workflow audit corrected verifiability to 1 = difficult and 5 = immediate,
made task/capability scales explicit, completed boundary rules, and retained conservative
risk/availability floors (`## Scoring Rubric`, `### Step 2 — Derive the minimum quality tier (Qmin)`,
`### Step 4 — Step up through remaining tiers using expected cost of error`). These textual
corrections are the baseline, not unresolved defects to reproduce.

Persisted catalog/TTL/refresh, dual optional harness columns, deterministic catalog fixtures
and qualified economic selection remain pending. Bulk mode currently writes the single
`Model` column; single mode remains chat-only (`### Step 5 — Present the recommendation`).

## Goal

Remove routine catalog searches and make model choice reproducible, available on the
actual harness, and conservative about correctness and unknown evidence.

## Scope

Local catalog, freshness, cost bands, task-signal rubric, capability/availability
filtering, plan columns and requested-versus-resolved model reporting.

## Out of Scope

Learned routing without calibration, automatic mid-task switching (spec 19), effort
policy (18), or defining a second token-price ledger (05).

## Actors & Roles

The maintainer explicitly refreshes the catalog. The selector records candidates.
The orchestrator resolves supported choices before spawning; it never silently
substitutes another model. Either harness can orchestrate if its capabilities permit.

## Terminology

A cost band (`light | standard | frontier`) is a relative price grouping, not a claim
of equal quality across models/providers. A session default is an explicit unresolved
choice whose actual execution model must still be recorded by telemetry.

## Requirements

- **REQ-01** THE SYSTEM SHALL use `~/.config/orchestrail/model-catalog.md`, with a
  schema version and `refreshed:` date. Age below 14 days is fresh; 14 through 30 days
  is usable with a dated notice; over 30 days is usable only with a stale warning.
  Missing, malformed or future dates SHALL be reported. Only `--refresh` may browse.
  Without a usable catalog, preserve the current/session model and report selection
  unavailable; do not invent a model, price or capability score.
- **REQ-02** THE SYSTEM SHALL retain a table `tier | anthropic model id | openai model id |
  relative cost`, with `light | standard | frontier`, and explicit availability,
  supported traits/context/tools and evidence dates. Relative cost SHALL reference
  spec 05 price snapshots where available; a missing price is unknown, not free.
- **REQ-03** WHEN selecting, THE SYSTEM SHALL first filter for actual harness/model
  availability, context/tool support, owner constraints and mandatory quality floors.
  Only eligible candidates may be compared by cost. Security, financial, core invariant
  and architecture-sensitive tasks SHALL retain explicit conservative floors.
- **REQ-04** THE SYSTEM SHALL define every task factor once on a consistent scale.
  Verifiability SHALL use 1 = difficult/late detection and 5 = cheap/immediate detection
  everywhere. Any task-to-capability mapping SHALL be explicit, bounded and total;
  no uncovered intervals or raw 1–5 versus 1–10 comparison is allowed. The old inverted
  rubric is already corrected in the current workflow; retain it under regression checks.
  Replace the current no-persistence catalog contract only when implementing this spec.
- **REQ-05** THE SYSTEM SHALL support optional trait overrides
  `creative | heavy-reasoning | mechanical`, document migration from current trait
  labels and prevent trait overrides from bypassing quality/availability floors.
  Model capability evidence SHALL be distinguished from price tier and uncalibrated
  judgment. Strong-first SHALL remain selectable when repair risk dominates.
- **REQ-06** WHEN bulk selection runs, THE SYSTEM SHALL add optional
  `Model (Claude)` and `Model (Codex)` columns; absent/empty cells mean session default.
  Readers SHALL accept legacy single-model plans and missing new columns. If the
  chosen model cannot actually be requested, the orchestrator SHALL surface the
  resolution and use the declared conservative fallback or stop if no authorized model
  is suitable; it SHALL NOT label the unavailable model as executed.
- **REQ-07** THE SYSTEM SHALL keep the selector at most 1,500 words, move optional
  rationale to on-demand reference, and perform no web lookup with a usable catalog
  unless explicitly refreshed. Warm deterministic catalog lookup SHALL complete within
  one second in an isolated fixture; a live Step 2 target of 60 seconds SHALL be reported
  only from measured runs, not asserted from the fixture.
- **REQ-08** THE SYSTEM SHALL validate catalog schema, tier/trait vocabulary, plan
  compatibility, score boundaries and monotonic quality floors with offline fixtures.
  Shared index gates G1–G8 apply. Historical success inputs, if later used, SHALL come
  only from a versioned curated retro export, never direct shared-store reads.

## Data Model

Additive catalog fields: schema version, refresh/evidence dates, exact provider model
IDs, price snapshot references, availability, context/tool limits and supported traits.
Plan columns remain optional. Requested/resolved/actual model identities are distinct
in spec 05. No speculative success probabilities are stored as measured facts.

## Contracts & Interfaces

Existing standalone and bulk selector invocations remain; `--refresh` explicitly opts
into catalog research. Refresh failure preserves the last valid catalog. Invalid new
content never partially replaces it. No test invokes a provider or refreshes the web.

## Non-Functional Requirements

No routine network calls; bounded deterministic selection; ≤1,500 workflow words.
Catalog refresh is atomic and preserves the previous usable file on failure.

## Edge Cases & Failure Modes

Cover ages 13/14/30/31 days, absent/future dates, no eligible model, unavailable defaults,
missing prices, trait conflicts, context overflow, old plans and exact score boundaries.
When unsure about quality, retain the suitable stronger/default choice and record
uncertainty rather than asserting an unmeasured cheap-model success rate.

## Acceptance Criteria

- [x] **AC-01** (REQ-01) Clock-controlled age/error fixtures produce the specified notices
  and no network access; failed refresh leaves the prior catalog unchanged.
- [x] **AC-02** (REQ-02, REQ-03, REQ-05) An unavailable cheap candidate and a cheap
  candidate below a financial/security floor are excluded; equally priced models are
  not assigned equal capability without evidence.
- [x] **AC-03** (REQ-04) Boundary/monotonicity fixtures cover every score and interval;
  worsening uncertainty, risk or verifiability cannot lower the quality floor.
- [x] **AC-04** (REQ-06) Legacy/dual-column plans work; unsupported requests are visible,
  and actual model reporting cannot retain an unavailable planned ID.
- [x] **AC-05** (REQ-07, REQ-08) Workflow length, fixture latency, schema/drift checks
  pass; documentation separates measured timings from targets and defines fallback,
  refresh and calibration-export ownership.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01 | AC-01 |
| REQ-02, REQ-03, REQ-05 | AC-02 |
| REQ-04 | AC-03 |
| REQ-06 | AC-04 |
| REQ-07, REQ-08 | AC-05 |

## Risks

Cost-band selection can disguise quality differences. Independent quality evaluation
under 09 is required before replacing conservative defaults; catalog labels are not
measured task-success probabilities.

## Assumptions

Catalog content may become stale without permission to refresh; honest fallback is
preferable to automatic model shopping. Supported IDs must be checked at implementation.

## Decisions

Keep ADR-0009's local TTL catalog and two optional columns. Correct contradictory
selection logic without introducing a learned router or mandatory live evaluation.

## Clarifications

2026-10-21: remove harness-name-based orchestration exclusions; spec 13 capabilities
control eligibility. Public API-equivalent price and actual subscription charge differ.

## Open Questions

None blocking. A new default model or paid routing comparison requires explicit approval.

## Notes

Deterministic catalog selection and plan resolution use explicit current-invocation
capability evidence. The owner selected implementation before the broader harness
migration; unknown support remains unavailable. Spec 13 retains ownership of the full
deployed harness capability contract and naming migration.

Consumers: 18 effort, 19 escalation, 20 decomposition. Spec 05 owns
monetary definitions; 09 owns comparative evidence. Suggested slices: catalog/TTL,
consistent scoring, availability/plan resolution, checks and documentation.

## Readiness Checklist

Scope, compatibility, failure cases and acceptance remain explicit and consistent.
Implementation and independent validation are complete; all original acceptance criteria
pass. No live model-quality or savings measurement is claimed.

## Change Log

### 2026-10-28 — reconciled from task-04-model-catalog-cache
- dependency-sequencing | implemented-differently | Clarified owner-selected delivery using explicit current capability inputs before the broader harness migration; no requirement or acceptance statement weakened. | Source: task state Task Analysis/Assumptions and Solution Design/Scope; ADR-0015.
