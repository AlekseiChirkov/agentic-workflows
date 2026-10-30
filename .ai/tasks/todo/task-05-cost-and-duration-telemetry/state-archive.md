# state-archive — task-05-cost-and-duration-telemetry

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Provide reproducible, privacy-preserving usage, cost and duration telemetry for independently accepted outcomes, including explicit coverage and unknowns, without altering existing lifecycle evidence or making paid model calls.

### Affected Parts
The producer and optional helpers, source adapters and profiles, immutable publication and projections, offline calculations, retrospective reporting, local warning proposals, tests, capability declarations, and operating instructions. Public formats require an additive decision before implementation.

### Codebase Analysis
The current revision is 0fc8297dd2d76c4b0b965be56e8de3e7c176ec18. `scripts/log-step.sh` supports lifecycle events and contract/lint commands; usage ingestion is absent. `hooks/log-step-hook.sh` implements bounded native evidence and correlation. `workflows/retro.md` delegates explicit selected timing files to the offline timing helper. `harness/claude/capabilities.md` and `harness/codex/capabilities.md` distinguish demonstrated native coverage from unavailability. The existing runbook specifies `bash scripts/validate-contracts.sh`. Files read: 5/12 (5 entry-points, 0 deeper).

### Open Questions
None identified. Specific source-version capability requires evidence during implementation; absent evidence must remain unknown.

### Decomposition Research
The specification prescribes eight top-level areas, each containing separately testable components. Candidate boundaries require classification and complete acceptance scenarios before a plan is finalized:
1. Strict schemas and typed missing values; canonical serialization and hashing; source profiles and normalization; diagnostic namespaces.
2. Explicit bounded manifests and integrity checks; profile-driven decoding and provenance; quarantine and privacy.
3. Immutable atomic publication and receipts; producer validation; optional lifecycle projection and immutable replay.
4. Identity and deduplication; stream finality and corrections; cumulative epochs and aggregates; independent inventory; causal ownership and scope-relative completeness; late evidence.
5. Price applicability and scenarios; exact arithmetic; complete versus partial cost; final rounding.
6. Fixed corpus and export; statistics; independent acceptance and comparison; measured timing and interval union.
7. Collection modes; pure status and candidate generation; thresholds and episodes; duration warning; owner-applied delivery and recovery.
8. Legacy compatibility; nonblocking failures; recovery and permissions; offline verification and operating instructions.
The specification's acceptance criteria span component boundaries and need integration coverage as well as leaf tests. This is research, not a completed decomposition.

The following cross-cutting requirements must be assigned to both leaf and integration checks during decomposition:
- Canonical output uses UTF-8 compact sorted-key JSON, content hashes, fixed observation time, schema-defined set ordering, ordered stream sequences, strict integer and decimal validation, and no duplicate keys; historical log permissiveness remains unchanged (acceptance criterion 21).
- Source selection fixes explicit file identities, hashes, byte and record limits before reads; bounded parsing, prefix verification, quarantine and opaque diagnostics must not expose source contents or neighboring files (criteria 1, 15, 24).
- Publication validates the entire bundle before mutation, installs content-addressed bytes without overwrite, permits one race verification and issues a receipt only after visibility; lifecycle files and replay state remain byte-identical on negative paths (criteria 5, 13–15).
- Identity, stream revisions, epochs, independently evidenced inventory, causal ownership and late observations must not create duplicate or fabricated request totals (criteria 3, 9–13, 23).
- Pricing must use one applicable scenario, exact decimal arithmetic and separately classified partial subtotals, with no implicit historical price or model substitution (criteria 2, 4, 11, 16, 23).
- Retrospective analysis freezes explicit corpus bytes and observation cutoffs; exports preserve equivalent semantic content, independent acceptance, comparable groups and separately measured time categories (criteria 7, 18, 19, 22).
- Current status is pure and only reads the supplied owner snapshot; explicit thresholds, duration fallback, episode identity and owner-controlled delivery preserve restart and disabled-mode behavior (criteria 6, 17).
- No normal operation calls models or the network; absent optional dependencies and telemetry failures preserve legacy behavior. Synthetic offline tests and operational guidance must cover recovery and source limitations (criteria 5, 8, 14, 15, 24).


## Archived Solution Design — Variants
- A: Add an optional Python standard-library telemetry engine, with separate domain modules and an explicit command entrypoint; extend the existing Bash producer only at its public contract, bounded usage publication and first-acceptance projection boundaries. Reuse existing timing validation. This fits the existing optional-helper architecture and allows exact arithmetic and bounded offline tests; it adds a maintained helper surface.
- B: Implement normalization, publication, pricing, analysis and status directly in the Bash producer and workflow instructions. This avoids a new helper entrypoint but adds complex parsing and exact arithmetic to the legacy path, increases coupling and risks the existing optional-dependency contract.


## Archived Solution Design — Rejected
Putting all parsing, exact arithmetic and reporting into the legacy Bash path risks its compatibility and increases complexity; a hosted service or daemon exceeds the specification.
