spec_path: .ai/specs/05-cost-and-duration-telemetry.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Open Questions (batch)
None.

## Parallel integration
- Reviewed leaf directories are stored in `completed/`; unfinished leaves and composites remain at the task root. The scratch integration branch is `integration/usage-telemetry` at `/tmp/orchestrail-combined-integration` (HEAD `f167903`); it is not merged or fully validated.
- Outstanding work includes ordinary publication races with run-end, same-UID report staging and warning-state races, real workflow owner delivery, independent authority provisioning, complete cross-component validation, and integration of the reviewed work into the pull request stack. The full validation run was stopped at the user request before completion; observed failures included warning delivery and pre-refactor shell/contract checks.
- Scratch integration branch `integration/usage-telemetry` at `/tmp/orchestrail-combined-integration` combines publication and lifecycle projection; targeted publication and projection suites passed. It is not a reviewed stack branch or pull request.
- Resolution and pricing modules are assembled in `/tmp/orchestrail-resolution-pricing-integration` on branch `parallel/resolution-pricing-integration`; real evidence-aware integration tests are in progress. This branch is not yet part of the pull request stack.
- Retrospective modules are assembled in `/tmp/orchestrail-report-integration` on branch `parallel/report-integration`; CLI and report integration are in progress. The branch includes failing regressions for missing token components and same-UID staging relocation. It is not part of the pull request stack.
- Collection mode and alert modules are assembled in `/tmp/orchestrail-status-integration` on branch `parallel/status-integration`; real snapshot analysis tests are in progress. Delivery remains separate with one failing noncooperative state replacement race; the other race and additional owner-boundary tests now pass.
- Integration review found gaps in duration alerts and streaming corrections; fixes are committed on their parallel branches. Duration alert fixes passed independent targeted re-review; stream fixes still require independent review. Both require stack integration. Conditional repricing and multi-bundle deduplication have targeted tests and parallel-branch implementations, but require independent review and integration. Nonzero tool costs and adapter epoch production remain incomplete. Independent report review found missing multi-profile details, missing unpriced response lists, incomplete outcome workload accounting, and missing tool-input integration. CLI analysis and report fields now exist on the parallel branch but have not passed final review. Same-UID staging relocation remains an open failing security regression.
- Publication remains blocked by the absence of an independently provisioned authority and a run-end race (failing regression committed as 7a11e2f). A standard-library RSA verification path is implemented at d020980 and independently reviewed, but its end-to-end test substitutes the trust-anchor loader; no real signer or protected registry is installed. Holding the lifecycle lock across publication was rejected because it can block run-end. No end-to-end positive publication through a real independently provisioned registry has been demonstrated. Lifecycle projection integration on `parallel/lifecycle-projection` passed targeted independent re-review at c3780c0 after fixing owner scope, cache writes, unknown prices, and completeness; session ownership remains fail-closed. It is not yet part of the pull request stack.

## Task Analysis
→ archived to state-archive.md

### Assumptions
- Preserve tracked knowledge and state according to the repository policy (source: `.ai/principles/domain.md`, invariant 9).
- Preserve existing lifecycle event semantics; usage observations use a separate additive contract (source: specification, publication and recovery).
- Unknown finality, coverage, identity or applicable prices must remain unknown or partial (source: specification, completeness and monetary states).
- No paid model calls, production budgets, automatic model changes or historical discovery by active workflows (source: specification, scope and participants).
- flow: full — gate: 1 fail 2 fail 3 fail 4 fail; the change spans multiple components, new invariants, behavior and public formats (source: specification, implementation order).

## Acceptance Trace

| Criterion | Component and integration evidence |
|---|---|
| AC-01 | T-01c, T-02a, T-02b, T-02 integration |
| AC-02 | T-01c, T-05b, T-05 integration |
| AC-03 | T-04a, T-04e, T-06d, T-08a end-to-end |
| AC-04 | T-05a, T-05b, T-05 integration |
| AC-05 | T-03b, T-08a |
| AC-06 | T-07c, T-07d, T-07 integration |
| AC-07 | T-06c |
| AC-08 | T-07a, T-08a, T-08b, T-08 integration |
| AC-09 | T-04b |
| AC-10 | T-04c |
| AC-11 | T-04a, T-04d, T-05a, T-08a end-to-end |
| AC-12 | T-04e, T-06a |
| AC-13 | T-03a, T-04e, T-06a, T-08a end-to-end |
| AC-14 | T-03a, T-08a |
| AC-15 | T-01b, T-01e, T-01f, T-01g, T-02a, T-02b, T-03a |
| AC-16 | T-03b, T-05b, T-08a end-to-end |
| AC-17 | T-07a, T-07b, T-07d, T-07 integration |
| AC-18 | T-06a, T-06b, T-06e, T-06 integration |
| AC-19 | T-06c |
| AC-20 | T-01d, T-06b, T-01 integration |
| AC-21 | T-01a, T-01b, T-01e, T-01f, T-01g, T-01 integration |
| AC-22 | T-06d |
| AC-23 | T-04d, T-04e, T-05b |
| AC-24 | T-02a, T-02b, T-08a |

## Decomposition
- decomposition: complete
- subtasks: T-01, T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d, T-02, T-02a, T-02b, T-03, T-03a, T-03b, T-04, T-04a, T-04b, T-04c, T-04d, T-04e, T-05, T-05a, T-05b, T-06, T-06a, T-06b, T-06e, T-06c, T-06d, T-07, T-07a, T-07b, T-07c, T-07d, T-08, T-08a, T-08b
- composites: T-01 (T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d); T-02 (T-02a, T-02b); T-03 (T-03a, T-03b); T-04 (T-04a, T-04b, T-04c, T-04d, T-04e); T-05 (T-05a, T-05b); T-06 (T-06a, T-06b, T-06e, T-06c, T-06d); T-07 (T-07a, T-07b, T-07c, T-07d); T-08 (T-08a, T-08b)

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Choose A. The Python 3.10+ standard-library helper is optional, explicitly invoked and works only on selected inputs. The existing producer remains the sole shared usage-store writer, exits zero on every path and preserves legacy operation without Python or jq. The source modules identified by leaf descriptions are initial boundaries, subject to adjustment when independently validated; no service or background process is introduced.

adr: .ai/adr/0016-task-05-additive-usage-telemetry.md (Provisional)

The public format change is additive: export a telemetry schema section from the existing producer contract, retaining the existing lifecycle event vocabulary. Version 1 telemetry envelopes use the specification's named kinds, fields, measurement states, fixed observation time, bounds and canonical UTF-8 JSON/SHA-256 rules. Usage bundles are self-contained and content-addressed under `usage/v1/`; receipt identity proves publication only. Optional first-acceptance projections carry their own evidence and never enrich an accepted replay. Unknown data remains absent or explicitly typed rather than zero. Existing historical records retain their original interpretation. Schema definitions, serialization and validation are shared by normalization, producer publication and offline analysis; no reader may invent a second incompatible schema. Exact field definitions and test vectors must be established in the contract component before an adapter or producer is published.

Measurement evidence references use SHA-256 of separate canonical sanitized evidence objects, without cyclic self-reference. This field-specific format prevents arbitrary free-form references; it does not prove that the object is safe, authentic, authorized or applicable. Explicit downstream evidence verification is required and absent evidence remains unknown.

### Scope
#### In
The eight areas and acceptance trace above, with offline synthetic validation and explicit owner-controlled warning delivery.
#### Out
Paid experiments, automatic price fetching during normal work, production budgets, automatic model changes, external notifications, dashboards, background services, unselected historical discovery and changes to existing accepted evidence.

### Rejected
→ archived to state-archive.md

### Off-limits
No prompts, responses, source contents, credentials or source paths enter shared telemetry. Do not rewrite lifecycle events or accepted checkpoints, silently substitute prices or model identities, alter existing model policies, or make paid calls.

### Invariants
- Legacy lifecycle operations remain nonblocking and work without the optional telemetry dependencies.
- Every shared usage publication is completely validated and immutable; a receipt confirms only verified installation.
- Explicit input scope, fixed observation time and independent inventory control all derived completeness claims.
- Exact arithmetic and evidence-based ownership prevent invented amounts and duplicate contributions.
- Shared state is changed only by its authorized owner, never by the pure status computation.

### Acceptance Criteria
- All 24 specification acceptance criteria pass on synthetic offline inputs, including the mapped leaf and cross-component scenarios.
- Existing lifecycle byte-level negative-path, optional-dependency and replay tests pass without network or model calls.
- Explicit-file analysis is reproducible and publishes no complete cost, exclusive time or comparison winner without the required evidence.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| A: optional Python engine and narrow producer integration | 4 | 4 | 5 | 5 | 4 | 22 |
| B: all logic in legacy Bash and workflow instructions | 2 | 2 | 2 | 2 | 2 | 10 |

**Winner:** Variant A — it fits the existing optional offline-helper pattern and isolates the legacy path.
**Anti-overengineering check:** passed; the helper and separate shared publication are required by the bounded, exact and independently testable contract.
**Evidence:** specification interfaces, publication and nonfunctional requirements; existing `scripts/run-log-timing.py`, `scripts/log-step.sh`, and project architecture and coding principles.

## Subtask Progress

[composite] T-01 | Usage contract | rollup: in-progress | integration-validation: not-started
  children: T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d
  blocker: none
  notes: S2=19, S5=19; independently testable entity schemas were redistributed into sibling leaves under the owner-approved autonomous process.

T-01a | canonical encoding and content identities | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; all acceptance criteria covered
  target_files: tests/usage-canonical-encoding.py, scripts/validate-contracts.sh, scripts/usage_telemetry_contract.py
  blocker: none
  notes: tdd: unit — initial 7 tests; tdd: red digest — key/set permutations and ordered streams: test_key_and_set_permutations_preserve_bytes_and_hash, test_stream_order_changes_bytes_and_identity; malformed input: test_strict_json_rejects_duplicate_keys_and_special_numbers, test_counter_rejects_boolean_fraction_negative_and_overflow, test_decimal_rejects_noncanonical_prices, test_unknown_schema_version_is_rejected; stable vector and fixed observation time: test_fixed_observation_has_stable_documented_utf8_vector. Full runbook 593 pass, 2 fail, 2 skip: the new check and its nested historical fixture both fail for the absent implementation. tdd: test amended — added test_schema_set_key_controls_order_and_identity after identifying the missing schema-defined ordering case; it failed against the preceding implementation before the change and the original tests remain intact.
  branch: feat/canonical-encoding-and-content-identities
  base_branch: main
  base_commit: 0fc8297dd2d76c4b0b965be56e8de3e7c176ec18
  commits: cdca445 test: cover canonical telemetry encoding, 51fcae3 test: cover schema-defined telemetry ordering, 690283c feat: add canonical telemetry encoding
  pr: #37 draft

T-01b | typed usage measurements | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; all acceptance criteria covered
  target_files: tests/usage-typed-schema.py, scripts/validate-contracts.sh, scripts/usage_telemetry_contract.py
  blocker: none
  notes: Draft originals are preserved in draft-schema-tests.py and draft-schema-runner.patch. tdd: unit — initial 7 tests, 2/2 acceptance criteria; tdd: red digest — known zero and unavailable reason: test_evidenced_zero_is_a_numeric_value, test_unavailable_measurement_has_reason_and_no_value; numeric boundaries and placeholders: test_counter_boundaries_and_invalid_values, test_unavailable_placeholders_and_missing_reason_are_rejected; additional states and duplicate keys: test_all_measurement_states_preserve_supported_evidence, test_invalid_state_and_unevidenced_zero_are_rejected, test_duplicate_keys_are_rejected_before_measurement_validation. Focused runbook: 7 tests, 10 failures due to absent measurement validator. tdd: test amended — test_specified_reasons_are_typed_and_preserved added because the initial test set omitted the specification's reason vocabulary; it failed against the initial implementation and original tests remain intact. Verification: measurement and canonical regression sets 8/8 each; lint passed. Full run before state correction: 595 passed, 1 failed, 2 skipped; the sole failed identity-ledger check passed separately after correction; full suite was not repeated. Independent validation: NEEDS WORK — arbitrary evidence strings accept source paths and unknown placeholders as proof of zero; final without a value and conflicted with a value and no reason are accepted. Focused measurement and canonical tests each 8/8; Bash syntax passed, ShellCheck unavailable; full suite not repeated by validator.
  notes: tdd: test amended — independent validation identified missing unsafe evidence and contradictory state cases; test_zero_evidence_rejects_paths_and_unknown_placeholders and test_final_requires_value_and_conflicted_requires_reason produced five expected failures against the preceding implementation.
  notes: tdd: test amended — synthetic evidence fixtures now use the schema-defined canonical SHA-256 of a sanitized object; test_evidence_requires_a_canonical_sha256_reference reproduced six expected failures before implementation. Existing behavioral assertions remain intact.
  notes: Independent revalidation passed: measurement 11/11, canonical 8/8, Bash syntax passed; ShellCheck unavailable. Evidence digest validates structure only; downstream must verify the sanitized object, scope and linkage. No improvement proposals.
  branch: feat/versioned-schema-and-typed-missing-measurements
  base_branch: feat/canonical-encoding-and-content-identities
  base_commit: 690283cbe4d500a0de9f544d13fdc788c2592e42
  commits: c98c458 test: cover typed usage measurements, 4215041 test: cover telemetry measurement reasons, 1ae17cd feat: validate typed usage measurements, c8634e1 test: cover unsafe measurement evidence, 2f63c84 fix: validate measurement evidence and states, eba25d1 test: require content-addressed measurement evidence, 154492e fix: constrain measurement evidence references
  pr: #38 draft

T-01e | observation and bundle schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; all leaf acceptance criteria covered
  target_files: tests/usage-observation-bundle-schema.py, scripts/validate-contracts.sh, scripts/usage_telemetry_contract.py
  blocker: none
  notes: tdd: unit and integration — 12 tests, 19 expected failures on missing schema validators; tdd: red digest — test_observation_and_bundle_accept_and_preserve_identities, test_invalid_versions_and_raw_fields_are_rejected_without_leakage, test_observation_requires_explicit_metadata, test_counter_scope_is_explicit_and_recognized, test_identifier_character_limit, test_observation_json_input_byte_limit, test_bundle_json_input_byte_limit, test_bundle_observation_count_limit, test_bundle_canonical_byte_limit, test_evidence_association_requires_matching_separate_object, test_rejects_missing_measurements_and_malformed_hash, test_rejects_duplicate_json_keys_before_validation. Canonical observation byte limit still needs a valid boundary fixture in implementation or validation.
  notes: tdd: test amended — synthetic opaque identifiers now use the field-specific digest format because the initial fixtures allowed privacy-unsafe raw strings; test_opaque_identifiers_reject_paths_and_free_text produced 20 expected failures on the preceding implementation. Canonical bundle limit fixture still straddles the specified boundary.
  notes: tdd: test amended — added test_other_identifiers_reject_paths_and_free_text and test_timestamps_are_not_opaque_identifiers after finding paths and free text were accepted in other identifier fields; scoped RED showed 24 failures on the preceding implementation.
  notes: Verification: envelope 15/15, measurement 11/11, canonical 8/8; Bash syntax passed, ShellCheck unavailable. Inventories, segments, diagnostics and split cache writes are presently unsupported and must be integrated before final delivery. Structural identifier checks do not establish safe provenance.
  notes: tdd: test amended — independent review found invalid timestamps and order-sensitive schema sets; six regression tests added, with 10 expected failures on the prior implementation. Canonical size gates are checked at exact reduced thresholds using valid fixtures; a separate bundle fixture straddles the actual 32 MiB limit. The current observation schema has a conservative canonical maximum below 34,072 bytes, so a valid 1 MiB observation fixture is unreachable under its other limits.
  notes: tdd: test amended — independent revalidation found caller overrides of schema-defined ordering and duplicate set members; test_schema_set_order_cannot_be_overridden and test_bundle_rejects_duplicate_set_members produced six expected failures.
  notes: Independent validation DONE; envelope 23/23, measurement 11/11, canonical 8/8; Bash syntax passed. Deferred integration obligations remain assigned to later components. No improvement proposals.
  branch: feat/observation-and-bundle-schema
  base_branch: feat/versioned-schema-and-typed-missing-measurements
  base_commit: 154492e42d9de61e36e95451d5475ee49b1e6d79
  commits: 6c85abc test: cover usage observation envelopes, e86b72b test: protect telemetry identifier privacy, c49a575 test: reject unsafe telemetry identifiers, a6015c7 feat: validate usage observation envelopes, 3583e8d test: cover envelope identity and time boundaries, ef6ddee fix: canonicalize envelope sets and timestamps, a0266c6 test: prevent ambiguous envelope identities, 9c92b4b fix: enforce canonical envelope identities
  pr: #39 draft

T-01f | source profile schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; all acceptance criteria covered
  target_files: tests/usage-entity-schemas.py, scripts/validate-contracts.sh, scripts/usage_telemetry_contract.py
  blocker: none
  notes: tdd: unit and contract — 5 tests; tdd: red digest — test_complete_profile_preserves_verified_and_unknown_capabilities, test_required_fields_and_unknown_fields_are_rejected_without_exposure, test_versions_types_and_capabilities_are_checked, test_identifiers_and_nested_fields_are_bounded_and_closed, test_canonical_and_input_byte_limits. Scoped RED: five expected failures because validator is absent.
  notes: Verification: profile 5/5, envelope 23/23, measurement 11/11 and canonical 8/8; Bash syntax and py_compile passed. Structural evidence references do not establish source authenticity.
  notes: tdd: test amended — independent review found missing input inclusion, cache TTL, reasoning inclusion and schema set ordering; three new tests reproduced two validator errors and one canonical ordering failure on the preceding implementation.
  notes: Independent revalidation DONE: profile 8/8, envelope 23/23, measurements 11/11, canonical 8/8; bash syntax passed; ShellCheck unavailable. Source authenticity, safe provenance and normalized cache reconciliation remain explicit downstream obligations. No improvement proposals.
  branch: feat/remaining-telemetry-entity-schemas
  base_branch: feat/observation-and-bundle-schema
  base_commit: 9c92b4bdb86c9a59c3b77df3c4f57a78fdc90a21
  commits: 5678daf test: cover source profile schema, c662856 feat: validate source profile schema, 2f27356 test: cover source profile counter semantics, 8a39fe1 fix: preserve source counter semantics
  pr: #40 draft

T-01h | source selection schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-source-selection.py, scripts/validate-contracts.sh
  branch: feat/source-selection-schema
  base_branch: feat/remaining-telemetry-entity-schemas
  base_commit: 8a39fe1d5fb7fcfa147f58382ee01f6a7a408f73
  commits: 1832d4f59f865fdf5ec797ec7860cdf74dc1d9f7, ef31d762cb83670b636f0b9311d908f154457a16
  pr: #41 draft
  blocker: none
  notes: selection 7/7, profile 8/8, envelope 23/23, measurement 11/11, canonical 8/8; source bytes and attribution evidence remain consumer responsibilities

T-01i | inventory schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-inventory-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-inventory-schema
  base_branch: feat/source-selection-schema
  base_commit: ef31d762cb83670b636f0b9311d908f154457a16
  commits: 2db515b28410fcb374391b6b139bf58056b114e3, a4f7e3e1cde5cbec1c7a017d7a7ea1466e0f4262, 06b1d8e55700d8e6d1ee5d831264fbe7fa1038d2, acdd33897d6478a9cf1f0c7a5b92fa82e78b52ec
  pr: #42 draft
  blocker: none
  notes: inventory 9/9 and adjacent schema regressions pass; provenance and billable coverage require downstream semantic verification

T-01j | attribution schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-attribution-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-attribution-schema
  base_branch: feat/usage-inventory-schema
  base_commit: acdd33897d6478a9cf1f0c7a5b92fa82e78b52ec
  commits: bf7e23d9a19f7556ef71352572c23456781aac06, 2cb0e92fb79c3068b0170e81c0ca3855ab68f4ac
  pr: #43 draft
  blocker: none
  notes: attribution 7/7 and adjacent schema regressions pass; evidence provenance and causal ownership remain downstream responsibilities

T-01k | collection segment schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-collection-segment-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-collection-segment-schema
  base_branch: feat/usage-attribution-schema
  base_commit: 2cb0e92fb79c3068b0170e81c0ca3855ab68f4ac
  commits: 354c442b22bd654e677b2b3992becbea4e6ebea5, de5fa250b27f1c6fde216ba4b14a10808d169ab0
  pr: #44 draft
  blocker: none
  notes: segment 5/5 and adjacent schema regressions pass; segment ownership and coverage require downstream verification

T-01l | diagnostic measurement schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-diagnostic-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-diagnostic-schema
  base_branch: feat/usage-collection-segment-schema
  base_commit: de5fa250b27f1c6fde216ba4b14a10808d169ab0
  commits: d62c1f8893ceb954a399757d8367fad470f70de7, 5c119aac5673950c7e4907e3a00d10c4640ebeae, e3004d3237676de6c34dd8c70fa82e7a8dd9ad93, e32fb410f3b25d04c794d8e2146bfa4f626959fc
  pr: #45 draft
  blocker: none
  notes: diagnostic 7/7 and adjacent schema regressions pass; producer must establish reference provenance

T-01m | price snapshot schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-price-snapshot-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-price-snapshot-schema
  base_branch: feat/usage-diagnostic-schema
  base_commit: e32fb410f3b25d04c794d8e2146bfa4f626959fc
  commits: a643847b64afc6e94fc57474f64ec50083331828, 1fa1a53897cf5a867f6add699762ed66d48caa29, 803e431a4f4a16bd485c773fe3e4bf1ba68bd0f1, 964579257a711d1ffd3551330366098600fa9000, 84410942565fed982371ebaff0d3a43a8a2c37bf
  pr: #46 draft
  blocker: none
  notes: price 11/11 and adjacent schema regressions pass; unknown multiplier and tool identity must remain unpriced until supported by evidence

T-01n | pricing scenario schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-pricing-scenario-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-pricing-scenario-schema
  base_branch: feat/usage-price-snapshot-schema
  base_commit: 84410942565fed982371ebaff0d3a43a8a2c37bf
  commits: 36799ee7531c69e1fd6b3e0d019f75a31031b323, aedb7c9af38d59568e19bc2764be0a3e1f90f5f6
  pr: #47 draft
  blocker: none
  notes: scenario 8/8 and adjacent schema regressions pass; consumers must verify evidence, actual work and applicability

T-01o | warning policy schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-warning-policy-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-warning-policy-schema
  base_branch: feat/usage-pricing-scenario-schema
  base_commit: aedb7c9af38d59568e19bc2764be0a3e1f90f5f6
  commits: 6487dc35a2210fb0c2a05906d59f7e613b316617, b9b4e7103a54bb00126ebb4dcd95b475a5a6d406
  pr: #48 draft
  blocker: none
  notes: policy 6/6 and related schema regressions pass; consumer must verify cohort provenance and applicability, strict warning bounds and delivery episodes

T-01p | analysis corpus schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-analysis-corpus-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-analysis-corpus-schema
  base_branch: feat/usage-warning-policy-schema
  base_commit: b9b4e7103a54bb00126ebb4dcd95b475a5a6d406
  commits: f3b455e53c2ecb0dfda8dd161d29e03fdc81bee2, 6cc0509e2922246eceb1d6c47b79faf8472ca0e7
  pr: #49 draft
  blocker: none
  notes: corpus 8/8 and related schema regressions pass; consumer must verify selected bytes, authorization and as_of

T-01q | usage receipt schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-usage-receipt-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-acceptance-receipt-schema
  base_branch: feat/usage-analysis-corpus-schema
  base_commit: 6cc0509e2922246eceb1d6c47b79faf8472ca0e7
  commits: 5b5b49811140feb5c206ba7d21f401272f53941b, 87f8f2d3505a3f0372dfff9da72a41de3db3a7da, 722064a2f3b049ea851738e8c2ae16fa35fcd3d7, 00c5b8eb1a0e435a216f0628fb53d6ab559cc66a
  pr: #50 draft
  blocker: none
  notes: receipt 9/9, corpus 8/8, envelope 23/23, canonical 8/8; receipt validation alone does not prove publication or ownership

T-01r | lifecycle projection schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created after transient DNS failure
  target_files: scripts/usage_telemetry_contract.py, tests/usage-lifecycle-projection-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-lifecycle-projection-schema
  base_branch: feat/usage-acceptance-receipt-schema
  base_commit: 00c5b8eb1a0e435a216f0628fb53d6ab559cc66a
  commits: f47ee14581f19dd372353db47362c63774eb93ff, 20ffaa7f32939ee1b5837be7cac14469c62378fc, 269c0a88faafc1962dd154a706a7d06b2b1ca026, 52836fd8db90403c6438e72f32e83f8a87fdeb0f, 3ea069a8fa275f0d5671680dc624f8abaffde51f, 72ef783379621421adb1dac51f9454666b16cd65, 85d0d42c48994d1f90311fde4cacd709b904df6d, 69249ce5578fb1d1d4b155360b713e4835938029, 068de414e8e4de8f1a7d9b93a509e04604b049b2, f2a447b85b282c155feb20560d4c0af5ab60d0f6, f59407fae2b24e0df7273c99e2e9e8c060d83e75, 909651777f86ffb7b5436ec81039ca684ee32b1f, bddbc59ddcbb043a96e916708365f273d151ae66, 09bf8631b8dd4b676916534a39f6cbab796645a8
  pr: #51 draft
  blocker: none
  notes: projection 24/24, scenario 8/8, price 11/11, measurement 11/11, canonical 8/8; unsupported pricing remains rejected and producer must verify evidence provenance and completeness

T-01s | current-run snapshot schema | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-current-run-snapshot-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-current-snapshot-schema
  base_branch: feat/usage-lifecycle-projection-schema
  base_commit: 09bf8631b8dd4b676916534a39f6cbab796645a8
  commits: 672ba5fa273a359bd3b1271f1d7ef208d0dd8109, fad91f64b7f50dfe18aa71807abbc913ecfba3f6, 9ace029113053997a27495da9ba9e565d1e35955, 8a28a5da23807d741c3449cf0f78ff9d14fb94fb, 190747da81afdd8e29f903fea7320795e80c894c, f3cd0245240dac5a2f3a627eba31cb39cd53d760, 4bb85c6c3e5248afa76e5452c0d8de7c8b580764, 227a3952c3b2d428d49ce378c1a3236506e29484, 74fa0106de4190ec2822e4078c079dae52a2c378
  pr: #52 draft
  blocker: none
  notes: snapshot 13/13 and related schema regressions pass; consumers must verify part bytes, receipts and causal ownership

T-01g | producer schema export | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/log-step.sh, scripts/usage_telemetry_contract.py, rules/run-log.md, tests/usage-contract-export.py, scripts/validate-contracts.sh
  branch: feat/usage-contract-export
  base_branch: feat/usage-current-snapshot-schema
  base_commit: 74fa0106de4190ec2822e4078c079dae52a2c378
  commits: c11e0934ccf828e788539324f1b598a1c4ac9b11, ded6542814aaf8467fb733b4a6347244c3c32ff6, ba8ca1ab59b06a9aa504c9a71a5c67ef7239e16f, 74a9003980594fbe099621c362133f93878dcc7b, 97a60a2c12835c5ef19776dd9655d665162d43b9
  pr: #53 draft
  blocker: none
  notes: export 7/7, legacy contract and producer test suite pass; trusted digest required before executing exported definitions

T-01c | versioned source profiles and counter normalization | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-source-profiles.py, harness/claude/capabilities.md, harness/codex/capabilities.md
  branch: feat/usage-source-normalization
  base_branch: feat/usage-contract-export
  base_commit: 97a60a2c12835c5ef19776dd9655d665162d43b9
  commits: a28eb8c67be4d8bf3614d57cca10f827d4ed0fee, 159e3f91d47c2e840730adc0381521a4032dc08f, e9bb9c719aa22952586dd85f8e31974d12383927, 47df9a76fee926000326755ff5e2a092becb39c3
  pr: #54 draft
  blocker: none
  notes: source profile 13/13 and adjacent regressions pass; report must serialize all derived sums as canonical decimal strings, pricing must support TTL split

T-01d | typed diagnostic metrics | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-diagnostic-registry.py
  branch: feat/usage-diagnostic-metrics
  base_branch: feat/usage-source-normalization
  base_commit: 47df9a76fee926000326755ff5e2a092becb39c3
  commits: 7a06d8f5a40b1ca73382e956fc1c817cb5572eb9, 4c85c8d52e5fc96e95aa877ac68fd7685479f17a
  pr: #55 draft
  blocker: none
  notes: registry 6/6, diagnostic 7/7, envelope 23/23, canonical 8/8; pricing integration must exclude diagnostics from paid requests

[composite] T-02 | Bounded source adapters | rollup: not-started | integration-validation: not-started
  children: T-02a, T-02b
  blocker: none
  notes: S2=2, S5=2; independent components require integration.

T-02a | bounded explicit source selection | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_sources.py, tests/usage-source-selection.py, scripts/usage-telemetry.py
  branch: feat/usage-bounded-source-reads
  base_branch: feat/usage-diagnostic-metrics
  base_commit: 4c85c8d52e5fc96e95aa877ac68fd7685479f17a
  commits: c7a7593942777334bee4caa75c157b3f0e465622, 7db7ea2614fa559c238f6d96f38113565a65bad6, 0d75e3f1af193b3cbac15ad9d4faf520fa7fd5e4, 974d689c2b48e85893b2b330806164f9f676141f, 4b4ada9183c25a75ea9c50ac66cad5cb042f6ead, 0a04ac629826a0c47eb8c7c03300a1d3d5277c81, 4dbe9c2277af8fd26e0348116ca373714a8a84b9, 2463a240024ee1d5ba70642dedb4d1a93652cd81
  pr: #56 draft
  blocker: none
  notes: isolated commits 802025233392c24631178c7b1b049940e2f4643f through 85cfa01cecdb2c38336b7deac988b69a199a2a13; 10/10 tests pass; CLI, quarantine and runner integration pending

T-02b | profile-driven source normalization and quarantine | atomic-tests: complete | atomic-execution: complete | atomic-validation: reviewed
  last_action: independent validation passed within documented rename trust boundary; draft PR created
  target_files: scripts/usage_telemetry_sources.py, tests/usage-source-normalization.py, scripts/usage-telemetry.py
  branch: feat/usage-source-adapter
  base_branch: feat/usage-bounded-source-reads
  base_commit: 2463a240024ee1d5ba70642dedb4d1a93652cd81
  commits: 51a000d1caa545a6e8a5e565c23bd7fbb2b7428c, 511423bde86adb056f5e2724ed769b6cd68ada85, 76dba2b5323dfb03c857d07405eab8df56faf4ad, 28c402322345b12ea3ca5813b4cdd294ce6ab436, b2eb8a4ed3b4b898317119e1d5b386b666729000, 329db89716578bbf12a4891929247b51764fec85, 3c639d91e575df7bf910a577731bb4fee5ed987a, c85ad33, 85ad2a561ff8a3845e8fafd94c616fc58a43e2fe, e24d96e03d3c1ec4fd580419380cb0288285bf65, a3f47aafb9b1453cf22e6a43c16c3448e3ff5887
  pr: #57 draft
  blocker: none
  notes: CLI 10/10 and adapter 11/11 pass; vetted synthetic profile only; concurrent destination rename remains a documented TOCTOU limitation requiring integration review; producer must verify evidence provenance

[composite] T-03 | Immutable publication | rollup: not-started | integration-validation: not-started
  children: T-03a, T-03b
  blocker: none
  notes: S2=2, S5=2; independent components require integration.

T-03a | immutable usage bundle publication | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: independent re-review passed for late-import authority identity; ordinary run-end publication races remain failing
  target_files: scripts/usage_telemetry_publication.py, tests/usage-usage-publication.py, scripts/log-step.sh
  branch: feat/usage-immutable-publication
  base_branch: feat/usage-source-adapter
  base_commit: 4a5643d0d1e3ccdebc168f850c772acdd25c06fc
  commits: 82b1a923d29d24431801e79220a21ed0eb2186b5, 61eb8fb4b0c4b9f2b6f02d79ca1315f58987ca38, 9e6992d932b5936608e4fe8cb5a9c769c25a53cb, 957f0f698cd6294dbb8fffa48e12d741eae7ce58, 9c4b1e5d5ec6f6f92d0ec600d63be61644f7709a, 076b11c245c8013fca1c692352770e72463be48c, 971ec2c8e97769c5da37c41f5efeadba996c615e, 9d80c165c5ff271288e843c0b3f5c19a29330ba1, 0df88a4d05249e4b6c93e0077544f18144881eb9, 02bef88c14763ebc8a6d832a6a148f39b969d721, 8f6d0cf13c2641301ab21b44ff788d7602e8ac8a, 1755de9e813416cb4205e7e60a1c73d1ef6b39f1, 7a11e2f87526cc362460539efd7c6efac96f05ad, 900d324f29df8756520fca9c67bd35ac742b4706, e344d3acf6ee5d02f425b4235323e3bd4198eb7d, d0209806d40cacb24b9f53b9d91b0ea432f844d6, e35002311bd1a31513d1005fdb5768d46e362a41, 7c466cc0c8b9d79d018488a431324d2c573d7a6f, f6626b04b95e465040d2d8b31128155b3d36fadb, 1539427a5bc1b5f86bb094007e274fa291506509, 275eada05728b9228f2ac8f10608629bca7de3b3, e682a7d3fa51577d1c6031185279ded0ade71bff, 0c2fdf8320e5381d4df1156c79f716fbe0b0bc88, 7d21b1afd8f16e27e52b733a4c7b367aafc2f0c2, 1ce8dd1a34c669c216a71f937a66967754f78cec, 8ad675e23a62daf038d75b0053ed7282cb8b4baa, e3ad1fc88deee132cc4a9f0ac98013168d3e5f7b
  pr: none
  blocker: Independent authorities are not provisioned in this environment; ordinary publication races with run-end remain reproducibly failing. Do not treat publication as complete.
  notes: Late import uses distinct independently controlled registration and usage authorities. Positive tests replace trust-anchor loaders; no real provisioned authority or complete live publication path is demonstrated.

T-03b | validated lifecycle usage projection | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated lifecycle RED tests and trusted-check helper committed; actual log-step integration still failing
  target_files: scripts/usage_telemetry_publication.py, tests/usage-lifecycle-projection.py, scripts/log-step.sh
  blocker: none
  notes: isolated commits 3fb09b721deaf974305364be58bc531805ea2d2b through f794dc9705fc2dea11e69ae3bdd5e26d4f82e8e9; external provenance authority and producer integration unresolved

[composite] T-04 | Resolution and completeness | rollup: not-started | integration-validation: not-started
  children: T-04a, T-04b, T-04c, T-04d, T-04e
  blocker: none
  notes: S2=5, S5=5; independent components require integration.

T-04a | response identity and deduplication | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated identity component independently reviewed; evidence and runner integration pending
  target_files: scripts/usage_telemetry_resolution.py, tests/usage-response-identity.py
  blocker: none
  notes: isolated commits ef8af7c5716d658d6c52c493a18ab66f2d89ae05 through c152774e5241363981a962e55114307a77004649; 16/16 tests pass; proof and runner integration pending

T-04b | stream finality and revisions | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated stream component independently reviewed; identity, evidence and runner integration pending
  target_files: scripts/usage_telemetry_resolution.py, tests/usage-stream-revisions.py
  blocker: none
  notes: isolated commits 7cea39a55cc15ee7e96cd61bf3db6d36b1f16702 through fd501ee3228a05db27f22168e8e94b17aebeed33; 12/12 tests pass; integration requires verified response identity and correction evidence

T-04c | cumulative epochs and aggregate coverage | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated cumulative epoch component independently reviewed; runner and evidence integration pending
  target_files: scripts/usage_telemetry_resolution.py, tests/usage-cumulative-epochs.py
  blocker: none
  notes: isolated commits 223e7dc30c4abff60677755a18d5e77b0d8dc605 through a3d03e9d27f72638b5e345d5f5c5e10a617aac67; 16/16 tests pass; proof, runner and overlapping response integration pending

T-04d | inventory and measurement completeness | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated completeness component independently reviewed; runner and evidence integration pending
  target_files: scripts/usage_telemetry_resolution.py, tests/usage-inventory-completeness.py
  blocker: none
  notes: isolated commits 25513fdbcdbb8a564961f5914aa4ceb17a2cbba8 through 0cf84b895361213409ed10070415ae9c82c22c68; 18/18 tests pass; verify independent inventory provenance and billable coverage at integration

T-04e | causal ownership and late evidence | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated ownership component independently reviewed; shared evidence and report integration pending
  target_files: scripts/usage_telemetry_resolution.py, tests/usage-causal-ownership.py
  blocker: none
  notes: isolated commits f50baccdc15dbbbbdd76ba51c6e261cf2fa3dd2b through 466a7d1667361727567c079f764c5c6470c76dff; 9/9 tests pass; integrate trusted record-specific scope attestations and report

[composite] T-05 | Pricing and arithmetic | rollup: not-started | integration-validation: not-started
  children: T-05a, T-05b
  blocker: none
  notes: S2=2, S5=2; independent components require integration.

T-05a | price snapshot and scenario applicability | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated applicability evidence fixes independently reviewed; shared evidence and pricing integration pending
  target_files: scripts/usage_telemetry_pricing.py, tests/usage-price-applicability.py
  blocker: none
  notes: isolated commits e569c3dad46a34450cda9b7966d240d8608924b2 through b8e47445e1951272bce96fe6b12e86f82ff4d9f9; 13/13 tests pass; new evidence types require shared validator and trusted provenance integration

T-05b | exact cost computation and completeness | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated exact cost component independently reviewed; applicability, evidence and runner integration pending
  target_files: scripts/usage_telemetry_pricing.py, tests/usage-exact-cost.py
  blocker: none
  notes: isolated commits 8c49cf136f55971c3f3354469af61358eee314b0 through 9af6dd078d274e73db067acbb22d47011258eb73; 18/18 tests and 10000 arithmetic comparisons pass; applicability and evidence integration pending

[composite] T-06 | Retrospective analysis | rollup: not-started | integration-validation: not-started
  children: T-06a, T-06b, T-06e, T-06c, T-06d
  blocker: none
  notes: S2=5, S5=5; independent components require integration.

T-06a | fixed explicit retrospective corpus | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated fixed corpus independently reviewed; lifecycle, CLI and runner integration pending
  target_files: scripts/usage_telemetry_report.py, tests/usage-fixed-corpus.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits cfbfc16a79d98dac573d5da8cd0ab628929999ec through 2c7d9161f1bd2ed6c8ed8e64a96c865cd2b24fbd; 15/15 tests pass; lifecycle validator, CLI and trusted evidence integration pending

T-06b | versioned retrospective exports | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated report export independently reviewed; corpus and CLI integration pending
  target_files: scripts/usage_telemetry_report.py, tests/usage-report-exports.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits 55b03218d6ea511bd743fd9c0613fa4e2be29246 through 4acfb06aecb0bd0b735218ce313a101942c1ae37; 12/12 tests pass; actual corpus and CLI integration pending

T-06e | comparable group statistics | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated statistics component independently reviewed; runner and report integration pending
  target_files: scripts/usage_telemetry_report.py, tests/usage-group-statistics.py
  blocker: none
  notes: isolated commits 481a8f917747291710f1cc0254e6f46aa6bf92ca, aa8b70289123f8bce2902530d5365bc0b670969f; 10/10 unit tests pass; connect runner during integration

T-06c | independent acceptance and comparison | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated accepted outcome component independently reviewed; provenance, report and CLI integration pending
  target_files: scripts/usage_telemetry_report.py, tests/usage-accepted-outcomes.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits e1fa20f53b616ee9b79173bc5e3c519c5cb75ecd through a1a25afc7a1a6559cd3fbbe22439d6582a742c40; 14/14 tests pass; independent evidence and CLI integration pending

T-06d | measured duration and interval coverage | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated interval component independently reviewed at 4287233; report integration pending
  target_files: scripts/usage_telemetry_report.py, tests/usage-duration-analysis.py, scripts/usage-telemetry.py, scripts/run-log-timing.py
  blocker: none
  notes: isolated commits eea77b28a251b1ff1821f0ae48ca2cd297b43428 through 42872337fee23c3ee70874fe954531223f190218; 21/21 unit tests pass

[composite] T-07 | Status and alerts | rollup: not-started | integration-validation: not-started
  children: T-07a, T-07b, T-07c, T-07d
  blocker: none
  notes: S2=4, S5=4; independent components require integration.

T-07a | collection mode and evidence segments | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated collection mode component independently reviewed; owner and runner integration pending
  target_files: scripts/usage_telemetry_status.py, tests/usage-collection-segments.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits 91e2c41bdec22baab43e7c051f45b8019cadbe83 through e31f62f2a2b32a9722c36db5f514ac89f7d345d7; 10/10 tests pass; status and runner integration pending

T-07b | pure status and threshold episodes | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated episode state machine independently reviewed; actual analyzer and runner integration pending
  target_files: scripts/usage_telemetry_status.py, tests/usage-alert-status.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits ee1e625763b48f0ff74fdb74a1a81870a4bac28d through 907d521e00d768f86eace9a6f752b890cb494d8c; 16/16 mocked tests pass; real analyzer and runner integration are not implemented

T-07c | duration warning eligibility | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated duration warning component independently reviewed; runner and export integration pending
  target_files: scripts/usage_telemetry_status.py, tests/usage-duration-warnings.py, scripts/usage-telemetry.py
  blocker: none
  notes: isolated commits cf7855de5aeb4e427f242a9f6456a3cd94394285 through afc53915f5938dbeb5d89eb046cf0c1a6098394f; 17/17 tests pass; verify corpus provenance, runner and real historical export at integration

T-07d | owner-controlled warning delivery | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated delivery review found file races; lock alias fixed but two regression tests remain failing
  target_files: scripts/usage_telemetry_status.py, tests/usage-warning-delivery.py, scripts/usage-telemetry.py
  blocker: Noncooperative state and note replacement races can overwrite edits or cause false delivery; protected single-owner execution must be enforced before completion.
  notes: isolated commits c19efe4c89fa2f428c56a7df1cfb5bce096733da through 3e913c278389410d5b522a4116e241fb63360fa6; 14/16 tests pass; two race regressions remain RED

[composite] T-08 | Compatibility and guidance | rollup: not-started | integration-validation: not-started
  children: T-08a, T-08b
  blocker: none
  notes: S2=2, S5=2; independent components require integration.

T-08a | legacy compatibility and recovery | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: isolated compatibility test suite committed; end-to-end and runner integration pending
  target_files: docs/USAGE.md, tests/usage-compatibility-recovery.py, scripts/validate-contracts.sh, tests/log-step.sh
  blocker: none
  notes: isolated commit fef2fa6cf6f06544ecc5f8d4510ad32a5f8c8826; 6 tests pass with a trusted verifier fixture; full CLI with real independent authority, lifecycle projection replay and runner integration remain unverified.

T-08b | offline telemetry operating guidance | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: planned
  target_files: docs/USAGE.md, tests/usage-telemetry-guidance.py, scripts/validate-contracts.sh, tests/log-step.sh, rules/run-log.md, workflows/retro.md
  blocker: none
  notes:
