# Reusable project context and fresh task-scoped execution packets

## Source

Workstream 2 of the owner's 2026-10-21 request: reduce repeated specification, project
analysis and task-state loading without losing correctness or changing models.

## Context & Problem

Baseline reviewed 2026-10-28.

The workflow audit now distinguishes inherited compatible parent context from full
standalone bootstrap; new workers still load their own required context. The existing
pack includes mutable project state and verifies exact source membership, size and mtime,
including umbrella/absent sources (`workflows/context-pack.md → ## Sources`,
`## Step 1 — Check freshness`). It does not provide content-hash freshness or a stable/dynamic split.

The orchestrator keeps prior leaf transcripts out of new workers and reuses one
Implementer across the test-first handoff (`workflows/spec-run.md → ## Step 4 — Subtask loop`).
Immutable leaf packets, session load receipts, structured extraction and hash-bound
analysis reuse remain pending. Improve these existing mechanisms without adding a new
orchestration engine.

## Goal

Give each role the smallest sufficient, verifiably fresh context, reuse stable
architecture analysis and avoid reloading unchanged material within the same session.

## Scope

Stable project pack, dynamic leaf view, structured task contract, relevant-file
selection, session load receipt, invalidation, conditional retrieval and prefix layout.
This owns workstream 2; instruction text is 08 and controller decisions are 15.

## Out of Scope

Changing canonical state storage, deleting source context, summarizing prohibitions
loosely, mandatory vector databases, mandatory Python runtime, provider cache promises,
or replacing the full-context fallback.

## Actors & Roles

Discovery records the reusable architecture/implementation contract. The orchestrator
materializes immutable packets and dynamic views. Workers read packets and request
additional evidence. Only the authorized writer changes shared artifacts.

## Terminology

A stable pack contains reusable constraints/architecture, not current progress.
A leaf view is a fresh projection of one leaf, relevant ancestor/dependency status
and unresolved blockers. A receipt proves what a particular session loaded; it cannot
prove that another agent remembers the content.

## Requirements

- **REQ-01** THE SYSTEM SHALL split reusable project facts/constraints from mutable
  task progress, preserving umbrella-first/local-override resolution and `working_dir`.
  A completed leaf elsewhere SHALL not invalidate unrelated stable architecture context;
  changed principles, runbook commands or architecture SHALL invalidate affected packs.
- **REQ-02** THE SYSTEM SHALL build a manifest with schema/source version, content
  hashes, source paths, selected sections, umbrella/local provenance and derivation.
  Correctness SHALL not depend solely on mtime/size. A generated summary SHALL retain
  links to originals and preserve every operative rule; commands, prohibitions,
  off-limits lists and relevant invariant/interface clauses SHALL remain exact.
- **REQ-03** WHEN dispatching a leaf, THE SYSTEM SHALL supply its goal, exact AC IDs/
  criteria, scope/off-limits, interfaces, architecture decisions, dependencies with
  readiness evidence, working directory, base revision, test commands and relevant
  integration risks. The dynamic view SHALL exclude unrelated leaf histories while
  retaining ancestors, blockers and cross-cutting constraints that affect this leaf.
- **REQ-04** WHEN reusing within one session, THE SYSTEM SHALL load unchanged material
  once using a session-local receipt tied to hashes and role. A new/forked agent SHALL
  receive its own sufficient context; a receipt alone SHALL not replace the content.
  Changed sources SHALL be reloaded before the next relevant decision.
- **REQ-05** WHEN selecting source files, THE SYSTEM SHALL start with target files,
  referenced interfaces, relevant tests and dependency callers; it SHALL expose omitted
  sources and a retrieval path. Interface/invariant changes, unresolved references,
  ambiguity or failed acceptance SHALL expand context before proceeding. Full-spec and
  full-context loading SHALL remain available.
- **REQ-06** THE SYSTEM SHALL reuse stable architecture analysis across related leaves
  only while its source/interface hashes remain valid. It SHALL retain decision
  provenance, rejected alternatives only when relevant, and an explicit stale status;
  no stale generated summary may override current code or an accepted decision.
- **REQ-07** THE SYSTEM SHALL order unchanged stable instructions before dynamic task
  material where the harness permits, keeping volatile timestamps/progress out of the
  stable prefix. It SHALL report provider cache read/write observations under 05 and
  make no claim that a stable file guarantees cache hits. Missing provider cache controls
  SHALL use ordinary context loading without invented cache settings.
- **REQ-08** THE SYSTEM SHALL support standalone workflow calls and legacy projects
  without a pack by resolving sources and building a scoped packet or loading full
  context. Missing required coding principles/test commands SHALL preserve the original
  warning/stop semantics. Invalid manifests SHALL not silently count as fresh.
- **REQ-09** THE SYSTEM SHALL keep context helpers optional and read-only with respect
  to canonical task state. Only the orchestrator may publish shared generated packets;
  concurrent workers SHALL get immutable snapshots and return context requests/deltas.
  Generated local paths SHALL stay within explicitly resolved project/umbrella roots.
- **REQ-10** THE SYSTEM SHALL apply shared index gates G1–G8, document disable/full-load
  recovery and integrate packet hashes/sizes/loading decisions with 05. Offline fixtures
  SHALL check coverage, invalidation and isolation; live token/cache/cost comparisons
  SHALL remain separate approved evaluations under 09.

## Data Model

A versioned packet manifest records stable-source hashes, dynamic state revision,
task contract digest, relevant source/test hashes, role, base revision and retrieval
references. A session-local receipt records loaded packet/hash and subsequent additions.
Generated packs/views are derived artifacts, never the source of canonical statuses.

## Contracts & Interfaces

Extend existing `/context-pack [--check|--refresh]` rather than add a required service.
Existing packs remain readable as legacy but cannot satisfy the stronger freshness
contract until rebuilt. Discovery chooses an optional deterministic extractor interface;
its absence uses the same documented extraction/full-load procedure.

The role packet consumes 08 load declarations and exposes a contract reference/hash to
15 checkpoints, 16 reviewers, 19 repair attempts and 20 decomposition plans. These
consumers may request expansion; they may not silently redefine packet contents.

## Non-Functional Requirements

A dynamic leaf view contains no unrelated leaf block. Dependency traversal is cycle-
checked and each source is loaded at most once per unchanged session receipt.
Exact commands/prohibitions are byte-preserved. Generated context contains no credentials
or unrelated project paths. No model/network call is necessary to check freshness.

## Edge Cases & Failure Modes

Cover absent/empty pack, same-size same-mtime content change, umbrella/local override,
missing source, renamed interface, active blocker, cross-leaf invariant, role switch,
new agent, manual state edit, symlink outside allowed roots and concurrent worker
requests. On uncertain completeness load the missing originals; stop where the current
contract requires it. Never save tokens by hiding unresolved uncertainty.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Independent-leaf progress changes preserve a stable pack;
  same-size source edits invalidate it. Umbrella overrides and exact forbidden lists/
  runbook commands survive extraction with source provenance.
- [ ] **AC-02** (REQ-03, REQ-05) A many-leaf fixture exposes only the selected leaf and
  required dependency/ancestor context; a changed interface triggers caller/test
  expansion and every AC remains represented or resolvable.
- [ ] **AC-03** (REQ-04, REQ-06) Repeated same-session loading reuses a matching receipt;
  new agents receive actual context, and stale architecture sources force refresh.
- [ ] **AC-04** (REQ-07) Stable-prefix fixtures exclude volatile task progress; reports
  distinguish observed cache hits from merely cache-compatible ordering.
- [ ] **AC-05** (REQ-08, REQ-09) Legacy, standalone, missing-command and concurrent-worker
  fixtures use correct fallback/stops; workers cannot modify shared views and traversal
  cannot escape declared roots.
- [ ] **AC-06** (REQ-10) Offline checks and baseline profiles cover full versus scoped
  loading, complete AC/invariant retention, version/size metadata and disable/resume.
  No measured savings are claimed from fixture byte reductions.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-05 | AC-02 |
| REQ-04, REQ-06 | AC-03 |
| REQ-07 | AC-04 |
| REQ-08, REQ-09 | AC-05 |
| REQ-10 | AC-06 |

## Risks

A relevant-looking file subset can omit a system invariant. Exact constraint coverage,
explicit retrieval, impact-triggered expansion and independent hidden checks mitigate
this; they do not prove that all summaries are lossless.

## Assumptions

Canonical project files stay authoritative and available. A context summary is a
derived convenience, not permission to disregard the full specification.

## Decisions

Extend existing context-pack and bootstrap behavior locally. No required retrieval
service, new state database or provider-specific caching contract.

## Clarifications

2026-10-21: both repeated source input and cache writes must be measured; reducing
uncached characters alone does not establish lower API-equivalent cost.

## Open Questions

None blocking. Paid task samples and tolerances are decided in the 09 manifest.

## Notes

Depends on 05, 08 and 09. Suggested slices: manifest/invalidation; project pack;
leaf contracts/views; session reuse and relevant-file expansion; workflow integration;
offline checks and docs. Context selection does not enable parallelism by itself.

## Readiness Checklist

One owner, explicit source provenance, schema, failure/fallback behavior, binary
acceptance and shared gates are present. Ready for Discovery; savings unmeasured.
