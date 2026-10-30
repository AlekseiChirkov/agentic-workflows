# ADR-0016: Decisions for Task 05 — Additive usage telemetry

## Status

Accepted

## Date

2026-10-30

## Related Task

- Task: [Cost and duration telemetry](../tasks/todo/task-05-cost-and-duration-telemetry/state.md).
- Related files: `scripts/log-step.sh`, `scripts/usage-telemetry.py`, `scripts/run-log-timing.py`, `rules/run-log.md`, `workflows/retro.md`.

## Summary

Introduce optional offline usage telemetry and an additive, evidence-bearing producer interface while preserving existing lifecycle records and nonblocking behavior.

## Context

The existing producer exports its contract in `scripts/log-step.sh:1031` and owns lifecycle operations in `scripts/log-step.sh:572`, `scripts/log-step.sh:866`, and `scripts/log-step.sh:885`. The retrospective workflow explicitly selects timing inputs in `workflows/retro.md:274`. Usage, cost, identity, inventory, and late evidence require a separate contract and must not change accepted lifecycle events. Normal operation must not invoke models or fetch prices.

## Decisions

### Decision 1: Separate bounded usage evidence from lifecycle events

**What was decided:**
Use an optional Python 3.10+ standard-library engine for explicit-input normalization, exact calculations, reporting and pure status. Extend the existing Bash producer additively with a versioned telemetry contract export, a separate content-addressed usage publication and optional self-contained first-acceptance projections. The producer remains the sole writer of the shared usage store. New envelopes use the specification's versioned kinds, typed unknowns, canonical UTF-8 JSON and SHA-256 identities; schema definitions and validation are shared among producers and readers. Existing lifecycle event types, accepted replays and historical interpretations remain unchanged.

**Why:**
The existing helper pattern supports isolated offline computations and exact arithmetic while keeping optional dependencies and historical access out of the ordinary producer path. A separate immutable artifact permits late evidence without changing accepted lifecycle bytes.

**Alternatives:**
Implementing all parsing, computation and export in the legacy Bash producer increases coupling and threatens optional-dependency compatibility. A hosted service or background process exceeds the requested scope.

**Consequences:**
Telemetry can be unavailable or partial without blocking the workflow. A publication receipt proves installation only, not source truth or measurement completeness. Schema and byte vectors must be concretely defined before dependent adapters and producers are implemented. Owner-controlled warning delivery remains separate from pure status computation.

### Decision 2: Address measurement evidence by content

**What was decided:**
The measurement `evidence` field is an opaque SHA-256 reference to a separate sanitized evidence object, using the shared canonical encoding. The evidence object cannot include its own identifier or a reference back to the measurement containing that identifier. Adapters may derive the identifier from explicitly selected, permitted source evidence; they must not invent an evidence object when none exists. This format applies to this field, not to all opaque identifiers. The schema and consumers must define and validate the evidence object's permitted provenance, source identity and measured field/value before accepting the association.

**Why:**
A free-form reference can carry paths or sensitive text, while a fixed content-addressed field supports deterministic matching of a separately validated object.

**Alternatives:**
Accepting arbitrary strings would permit raw paths or free text to enter normalized data. Treating a hash-shaped string alone as proof of an actual measurement would invent provenance.

**Consequences:**
The identifier's format and byte match do not prove that a source is genuine, authorized, relevant, complete or free of secrets. Downstream consumers verify the actual selected evidence and its scope; absent or unverified evidence remains unknown or partial. No unselected history is read.

**Related files:**
- `scripts/usage_telemetry_contract.py`
- `scripts/usage_telemetry_sources.py`
- `scripts/usage_telemetry_resolution.py`

### Decision 3: Express unavailable observation metadata explicitly

**What was decided:**
Versioned observation envelopes represent unavailable source time as `source_time: null` with `source_time_quality: unknown`, unknown outcome as `outcome: unknown`, and unassigned attribution as an explicit unattributed owner with its declared quality and candidate list. The physical format does not infer actual model, ownership or clock quality from a plan or ingestion time. Counter scopes use the enumerated source semantics, including `response_total`.

The initial physical schema uses explicit UTC RFC 3339 timestamps for observed and known source times. Attribution candidates, measurement reason sets and the bundle's sources, observations, evidence objects, inventories, segments and diagnostics are sets ordered by their canonical element bytes; ordered source streams retain their order. Invalid times cannot be passed through as arbitrary text, and permutations of a set cannot create new semantic identities.

**Why:**
Required metadata must remain explicit when a selected source does not prove it; an absent source time cannot be replaced with the observation time.

**Alternatives:**
Filling unavailable metadata from session configuration or treating it as a zero would misstate source evidence.

**Consequences:**
Validators and readers must distinguish unknowns from measured values and must enforce limits on both input bytes and canonical output. Schema and evidence association remain versioned and subject to independent validation.

Opaque project, selected-source, provider-account scope and owner-candidate IDs in the versioned usage envelope use `sha256:` followed by 64 lowercase hexadecimal characters. Adapters must generate these from authorized inputs using an appropriately keyed domain-separated mapping or independent random identifiers, and retain any identifying mapping only in the authorized local scope. The string shape alone cannot prove safe generation or absence of secrets, and hashes of low-entropy names can be guessed. Shared publication must verify provenance and privacy under the selected profile and owner scope rather than relying on the shape alone. Other identifiers, such as a registered profile name and existing run ID, retain their own separately validated contracts.

**Related files:**
- `scripts/usage_telemetry_contract.py`

**Related files:**
- `scripts/log-step.sh`
- `scripts/usage-telemetry.py`
- `scripts/run-log-timing.py`
- `rules/run-log.md`
- `workflows/retro.md`

### Decision 4: Separate streaming computation from protected publication

**What was decided:**
Normalization, analysis and status emit complete results through pipes or sockets. Report publication waits for successful analysis and installs a validated immutable archive in an operator-protected directory. Warning state and notes use a sole authorized cooperative writer in protected directories. Active publication authorization is fixed at the registration check; an already authorized installation may complete after run closure without issuing a receipt.

**Why:**
Same-user directory relocation and uncooperative state writes cannot be excluded by pathname checks or advisory locks. Streaming removes helper-owned output files, while explicit protected-directory and writer constraints state the remaining deployment authority honestly.

**Alternatives:**
Post-write cleanup, check-then-act path validation and advisory locks as a claim of unconditional protection were rejected. Holding a publisher lock through installation was rejected because a suspended publisher could delay lifecycle closure.

**Consequences:**
Operators must enforce protection against relocation and mutation, including same-UID actors. A missing receipt does not prove that installation failed. Synthetic test profiles and test signing keys do not establish a live deployment.

**Related files:**
- `scripts/usage-telemetry.py`
- `scripts/usage-report-publish.py`
- `scripts/usage_telemetry_delivery.py`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

Use the existing Bash lifecycle path for all telemetry or introduce an external service.

## Implications for Future Work

Do not infer finality, ownership, completeness, prices or model identity from absent evidence. Preserve exact input scope, immutable prior artifacts and the distinction between estimated API-equivalent cost and actual subscription payment.

## Verification

All 27 PRs received isolated reviews, sequential repairs and fresh independent rechecks. Full combined source verification at 524367a446c2456ac2c81ddfa143cd2da47bd51e: 619 passed, 0 failed and 2 optional private-pattern hygiene skips. Focused regressions cover canonical ordering, exact times and ratios, scoped accounting, complete stdout, lifecycle rejection, contract-valid exports, private selected-part delivery and conditional pricing. Historical knowledge and patch context are retained. Real source profiles and external signing infrastructure were not demonstrated.

## References

- Task: [Cost and duration telemetry](../tasks/todo/task-05-cost-and-duration-telemetry/state.md).
- Pull requests: #37–#63; corrections and the combined validation record are included in #63.
- Related documents: existing correlated hook logging decision and telemetry specification.
