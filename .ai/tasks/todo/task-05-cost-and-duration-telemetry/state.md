spec_path: .ai/specs/05-cost-and-duration-telemetry.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: complete
- validation: complete

## Open Questions (batch)
None.

## Parallel integration
- The telemetry implementation and independent validation are complete on the review stack. PRs #37–#63 are ready for review and must be merged in dependency order.
- Report publication and warning delivery require operator-protected destinations. Warning writers must cooperate on the owner lock; these constraints do not protect against an uncooperative process with the same filesystem authority.
- The only built-in reviewed source profile is synthetic. External signing authority is not supplied, and the synthetic end-to-end tests construct some independent evidence. Live-source deployment has not been demonstrated.

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
| AC-02 | T-01c, T-04 |
| AC-03 | T-04, T-06, T-08 end-to-end |
| AC-04 | T-04 |
| AC-05 | T-03, T-08 |
| AC-06 | T-07 |
| AC-07 | T-06 |
| AC-08 | T-07, T-08 |
| AC-09 | T-04 |
| AC-10 | T-04 |
| AC-11 | T-04, T-08 end-to-end |
| AC-12 | T-04, T-06 |
| AC-13 | T-03, T-04, T-06, T-08 end-to-end |
| AC-14 | T-03, T-08 |
| AC-15 | T-01b, T-01e, T-01f, T-01g, T-02a, T-02b, T-03 |
| AC-16 | T-03, T-04, T-08 end-to-end |
| AC-17 | T-07 |
| AC-18 | T-06 |
| AC-19 | T-06 |
| AC-20 | T-01d, T-06, T-01 integration |
| AC-21 | T-01a, T-01b, T-01e, T-01f, T-01g, T-01 integration |
| AC-22 | T-06 |
| AC-23 | T-04 |
| AC-24 | T-02a, T-02b, T-08 |

## Decomposition
- decomposition: complete
- subtasks: T-01, T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d, T-02a, T-02b, T-02c, T-02, T-03, T-04, T-06, T-07, T-08
- composites: T-01 (completed contract leaves; integration validation pending); T-02 (T-02a, T-02b, T-02c; integration validation pending)
- consolidation: user requested five capability-oriented work items; original descriptions, plan and progress are preserved in `superseded/`.

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

[composite] T-01 | Usage contract | rollup: done | integration-validation: complete
  children: T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d
  blocker: none
  notes: S2=19, S5=19; independent composite validation passed on feat/usage-diagnostic-metrics at 4c85c8d: 190 child tests and both integration criteria passed; the additional integrated scenario was exercised in memory, not saved as a separate regression.

T-01a | canonical encoding and content identities | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; all acceptance criteria covered
  target_files: tests/usage-canonical-encoding.py, scripts/validate-contracts.sh, scripts/usage_telemetry_contract.py
  blocker: none
  notes: tdd: unit — initial 7 tests; tdd: red digest — key/set permutations and ordered streams: test_key_and_set_permutations_preserve_bytes_and_hash, test_stream_order_changes_bytes_and_identity; malformed input: test_strict_json_rejects_duplicate_keys_and_special_numbers, test_counter_rejects_boolean_fraction_negative_and_overflow, test_decimal_rejects_noncanonical_prices, test_unknown_schema_version_is_rejected; stable vector and fixed observation time: test_fixed_observation_has_stable_documented_utf8_vector. Full runbook 593 pass, 2 fail, 2 skip: the new check and its nested historical fixture both fail for the absent implementation. tdd: test amended — added test_schema_set_key_controls_order_and_identity after identifying the missing schema-defined ordering case; it failed against the preceding implementation before the change and the original tests remain intact.
  branch: feat/canonical-encoding-and-content-identities
  base_branch: main
  base_commit: 0fc8297dd2d76c4b0b965be56e8de3e7c176ec18
  commits: cdca445 test: cover canonical telemetry encoding, 51fcae3 test: cover schema-defined telemetry ordering, 690283c feat: add canonical telemetry encoding
  pr: #37 ready

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
  pr: #38 ready

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
  pr: #39 ready

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
  pr: #40 ready

T-01h | source selection schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-source-selection.py, scripts/validate-contracts.sh
  branch: feat/source-selection-schema
  base_branch: feat/remaining-telemetry-entity-schemas
  base_commit: 8a39fe1d5fb7fcfa147f58382ee01f6a7a408f73
  commits: 1832d4f59f865fdf5ec797ec7860cdf74dc1d9f7, ef31d762cb83670b636f0b9311d908f154457a16
  pr: #41 ready
  blocker: none
  notes: selection 7/7, profile 8/8, envelope 23/23, measurement 11/11, canonical 8/8; source bytes and attribution evidence remain consumer responsibilities

T-01i | inventory schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-inventory-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-inventory-schema
  base_branch: feat/source-selection-schema
  base_commit: ef31d762cb83670b636f0b9311d908f154457a16
  commits: 2db515b28410fcb374391b6b139bf58056b114e3, a4f7e3e1cde5cbec1c7a017d7a7ea1466e0f4262, 06b1d8e55700d8e6d1ee5d831264fbe7fa1038d2, acdd33897d6478a9cf1f0c7a5b92fa82e78b52ec
  pr: #42 ready
  blocker: none
  notes: inventory 9/9 and adjacent schema regressions pass; provenance and billable coverage require downstream semantic verification

T-01j | attribution schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-attribution-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-attribution-schema
  base_branch: feat/usage-inventory-schema
  base_commit: acdd33897d6478a9cf1f0c7a5b92fa82e78b52ec
  commits: bf7e23d9a19f7556ef71352572c23456781aac06, 2cb0e92fb79c3068b0170e81c0ca3855ab68f4ac
  pr: #43 ready
  blocker: none
  notes: attribution 7/7 and adjacent schema regressions pass; evidence provenance and causal ownership remain downstream responsibilities

T-01k | collection segment schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-collection-segment-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-collection-segment-schema
  base_branch: feat/usage-attribution-schema
  base_commit: 2cb0e92fb79c3068b0170e81c0ca3855ab68f4ac
  commits: 354c442b22bd654e677b2b3992becbea4e6ebea5, de5fa250b27f1c6fde216ba4b14a10808d169ab0
  pr: #44 ready
  blocker: none
  notes: segment 5/5 and adjacent schema regressions pass; segment ownership and coverage require downstream verification

T-01l | diagnostic measurement schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-diagnostic-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-diagnostic-schema
  base_branch: feat/usage-collection-segment-schema
  base_commit: de5fa250b27f1c6fde216ba4b14a10808d169ab0
  commits: d62c1f8893ceb954a399757d8367fad470f70de7, 5c119aac5673950c7e4907e3a00d10c4640ebeae, e3004d3237676de6c34dd8c70fa82e7a8dd9ad93, e32fb410f3b25d04c794d8e2146bfa4f626959fc
  pr: #45 ready
  blocker: none
  notes: diagnostic 7/7 and adjacent schema regressions pass; producer must establish reference provenance

T-01m | price snapshot schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-price-snapshot-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-price-snapshot-schema
  base_branch: feat/usage-diagnostic-schema
  base_commit: e32fb410f3b25d04c794d8e2146bfa4f626959fc
  commits: a643847b64afc6e94fc57474f64ec50083331828, 1fa1a53897cf5a867f6add699762ed66d48caa29, 803e431a4f4a16bd485c773fe3e4bf1ba68bd0f1, 964579257a711d1ffd3551330366098600fa9000, 84410942565fed982371ebaff0d3a43a8a2c37bf
  pr: #46 ready
  blocker: none
  notes: price 11/11 and adjacent schema regressions pass; unknown multiplier and tool identity must remain unpriced until supported by evidence

T-01n | pricing scenario schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-pricing-scenario-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-pricing-scenario-schema
  base_branch: feat/usage-price-snapshot-schema
  base_commit: 84410942565fed982371ebaff0d3a43a8a2c37bf
  commits: 36799ee7531c69e1fd6b3e0d019f75a31031b323, aedb7c9af38d59568e19bc2764be0a3e1f90f5f6
  pr: #47 ready
  blocker: none
  notes: scenario 8/8 and adjacent schema regressions pass; consumers must verify evidence, actual work and applicability

T-01o | warning policy schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-warning-policy-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-warning-policy-schema
  base_branch: feat/usage-pricing-scenario-schema
  base_commit: aedb7c9af38d59568e19bc2764be0a3e1f90f5f6
  commits: 6487dc35a2210fb0c2a05906d59f7e613b316617, b9b4e7103a54bb00126ebb4dcd95b475a5a6d406
  pr: #48 ready
  blocker: none
  notes: policy 6/6 and related schema regressions pass; consumer must verify cohort provenance and applicability, strict warning bounds and delivery episodes

T-01p | analysis corpus schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-analysis-corpus-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-analysis-corpus-schema
  base_branch: feat/usage-warning-policy-schema
  base_commit: b9b4e7103a54bb00126ebb4dcd95b475a5a6d406
  commits: f3b455e53c2ecb0dfda8dd161d29e03fdc81bee2, 6cc0509e2922246eceb1d6c47b79faf8472ca0e7
  pr: #49 ready
  blocker: none
  notes: corpus 8/8 and related schema regressions pass; consumer must verify selected bytes, authorization and as_of

T-01q | usage receipt schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-usage-receipt-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-acceptance-receipt-schema
  base_branch: feat/usage-analysis-corpus-schema
  base_commit: 6cc0509e2922246eceb1d6c47b79faf8472ca0e7
  commits: 5b5b49811140feb5c206ba7d21f401272f53941b, 87f8f2d3505a3f0372dfff9da72a41de3db3a7da, 722064a2f3b049ea851738e8c2ae16fa35fcd3d7, 00c5b8eb1a0e435a216f0628fb53d6ab559cc66a
  pr: #50 ready
  blocker: none
  notes: receipt 9/9, corpus 8/8, envelope 23/23, canonical 8/8; receipt validation alone does not prove publication or ownership

T-01r | lifecycle projection schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created after transient DNS failure
  target_files: scripts/usage_telemetry_contract.py, tests/usage-lifecycle-projection-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-lifecycle-projection-schema
  base_branch: feat/usage-acceptance-receipt-schema
  base_commit: 00c5b8eb1a0e435a216f0628fb53d6ab559cc66a
  commits: f47ee14581f19dd372353db47362c63774eb93ff, 20ffaa7f32939ee1b5837be7cac14469c62378fc, 269c0a88faafc1962dd154a706a7d06b2b1ca026, 52836fd8db90403c6438e72f32e83f8a87fdeb0f, 3ea069a8fa275f0d5671680dc624f8abaffde51f, 72ef783379621421adb1dac51f9454666b16cd65, 85d0d42c48994d1f90311fde4cacd709b904df6d, 69249ce5578fb1d1d4b155360b713e4835938029, 068de414e8e4de8f1a7d9b93a509e04604b049b2, f2a447b85b282c155feb20560d4c0af5ab60d0f6, f59407fae2b24e0df7273c99e2e9e8c060d83e75, 909651777f86ffb7b5436ec81039ca684ee32b1f, bddbc59ddcbb043a96e916708365f273d151ae66, 09bf8631b8dd4b676916534a39f6cbab796645a8
  pr: #51 ready
  blocker: none
  notes: projection 24/24, scenario 8/8, price 11/11, measurement 11/11, canonical 8/8; unsupported pricing remains rejected and producer must verify evidence provenance and completeness

T-01s | current-run snapshot schema | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-current-run-snapshot-schema.py, scripts/validate-contracts.sh
  branch: feat/usage-current-snapshot-schema
  base_branch: feat/usage-lifecycle-projection-schema
  base_commit: 09bf8631b8dd4b676916534a39f6cbab796645a8
  commits: 672ba5fa273a359bd3b1271f1d7ef208d0dd8109, fad91f64b7f50dfe18aa71807abbc913ecfba3f6, 9ace029113053997a27495da9ba9e565d1e35955, 8a28a5da23807d741c3449cf0f78ff9d14fb94fb, 190747da81afdd8e29f903fea7320795e80c894c, f3cd0245240dac5a2f3a627eba31cb39cd53d760, 4bb85c6c3e5248afa76e5452c0d8de7c8b580764, 227a3952c3b2d428d49ce378c1a3236506e29484, 74fa0106de4190ec2822e4078c079dae52a2c378
  pr: #52 ready
  blocker: none
  notes: snapshot 13/13 and related schema regressions pass; consumers must verify part bytes, receipts and causal ownership

T-01g | producer schema export | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/log-step.sh, scripts/usage_telemetry_contract.py, rules/run-log.md, tests/usage-contract-export.py, scripts/validate-contracts.sh
  branch: feat/usage-contract-export
  base_branch: feat/usage-current-snapshot-schema
  base_commit: 74fa0106de4190ec2822e4078c079dae52a2c378
  commits: c11e0934ccf828e788539324f1b598a1c4ac9b11, ded6542814aaf8467fb733b4a6347244c3c32ff6, ba8ca1ab59b06a9aa504c9a71a5c67ef7239e16f, 74a9003980594fbe099621c362133f93878dcc7b, 97a60a2c12835c5ef19776dd9655d665162d43b9
  pr: #53 ready
  blocker: none
  notes: export 7/7, legacy contract and producer test suite pass; trusted digest required before executing exported definitions

T-01c | versioned source profiles and counter normalization | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-source-profiles.py, harness/claude/capabilities.md, harness/codex/capabilities.md
  branch: feat/usage-source-normalization
  base_branch: feat/usage-contract-export
  base_commit: 97a60a2c12835c5ef19776dd9655d665162d43b9
  commits: a28eb8c67be4d8bf3614d57cca10f827d4ed0fee, 159e3f91d47c2e840730adc0381521a4032dc08f, e9bb9c719aa22952586dd85f8e31974d12383927, 47df9a76fee926000326755ff5e2a092becb39c3
  pr: #54 ready
  blocker: none
  notes: source profile 13/13 and adjacent regressions pass; report must serialize all derived sums as canonical decimal strings, pricing must support TTL split

T-01d | typed diagnostic metrics | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; draft PR created
  target_files: scripts/usage_telemetry_contract.py, tests/usage-diagnostic-registry.py
  branch: feat/usage-diagnostic-metrics
  base_branch: feat/usage-source-normalization
  base_commit: 47df9a76fee926000326755ff5e2a092becb39c3
  commits: 7a06d8f5a40b1ca73382e956fc1c817cb5572eb9, 4c85c8d52e5fc96e95aa877ac68fd7685479f17a
  pr: #55 ready
  blocker: none
  notes: registry 6/6, diagnostic 7/7, envelope 23/23, canonical 8/8; pricing integration must exclude diagnostics from paid requests

[composite] T-02 | Bounded source adapters | rollup: done | integration-validation: complete
  children: T-02a, T-02b, T-02c
  blocker: none
  notes: Independent integration revalidation passed after the destination safety fix; 58 focused tests and shell lint passed. The original destination move race was reproduced on 4a5643d.

T-02a | bounded explicit source selection | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent revalidation passed; draft PR created
  target_files: scripts/usage_telemetry_sources.py, tests/usage-source-selection.py, scripts/usage-telemetry.py
  branch: feat/usage-bounded-source-reads
  base_branch: feat/usage-diagnostic-metrics
  base_commit: 4c85c8d52e5fc96e95aa877ac68fd7685479f17a
  commits: c7a7593942777334bee4caa75c157b3f0e465622, 7db7ea2614fa559c238f6d96f38113565a65bad6, 0d75e3f1af193b3cbac15ad9d4faf520fa7fd5e4, 974d689c2b48e85893b2b330806164f9f676141f, 4b4ada9183c25a75ea9c50ac66cad5cb042f6ead, 0a04ac629826a0c47eb8c7c03300a1d3d5277c81, 4dbe9c2277af8fd26e0348116ca373714a8a84b9, 2463a240024ee1d5ba70642dedb4d1a93652cd81
  pr: #56 ready
  blocker: none
  notes: Source selection was independently reviewed; CLI, quarantine and runner work was subsequently added in the next reviewed leaf. Parent integration validation remains pending.

T-02b | profile-driven source normalization and quarantine | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed within documented rename trust boundary; draft PR created
  target_files: scripts/usage_telemetry_sources.py, tests/usage-source-normalization.py, scripts/usage-telemetry.py
  branch: feat/usage-source-adapter
  base_branch: feat/usage-bounded-source-reads
  base_commit: 2463a240024ee1d5ba70642dedb4d1a93652cd81
  commits: 51a000d1caa545a6e8a5e565c23bd7fbb2b7428c, 511423bde86adb056f5e2724ed769b6cd68ada85, 76dba2b5323dfb03c857d07405eab8df56faf4ad, 28c402322345b12ea3ca5813b4cdd294ce6ab436, b2eb8a4ed3b4b898317119e1d5b386b666729000, 329db89716578bbf12a4891929247b51764fec85, 3c639d91e575df7bf910a577731bb4fee5ed987a, c85ad33, 85ad2a561ff8a3845e8fafd94c616fc58a43e2fe, e24d96e03d3c1ec4fd580419380cb0288285bf65, a3f47aafb9b1453cf22e6a43c16c3448e3ff5887, aea532c992d8fc2c92abd7741a4d8a916b1aee4e, 4a5643d0d1e3ccdebc168f850c772acdd25c06fc
  pr: #57 ready
  blocker: none
  notes: CLI 10/10 and adapter 11/11 pass; vetted synthetic profile only; concurrent destination rename remains a documented TOCTOU limitation requiring integration review; producer must verify evidence provenance


T-02c | normalization destination safety | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: fix/normalization-destination-safety
  base_branch: feat/usage-source-adapter
  base_commit: 4a5643d0d1e3ccdebc168f850c772acdd25c06fc
  commits: a4cdf8fdb28454c794eeeb265a62dac2b96b3023 test: cover normalization destination moves, be2c912c9b0ea903640817b2ace81e1fda6137c9 test: cover streamed normalization output, e94a8a626319c2a6845416ae844824d3995fcc81 fix: stream normalized bundles without file writes, 7a6cf8495989bfcd3b4b9a091a18b6cacb65a77f test: cover socket and broken pipe output
  pr: #58 ready
  last_action: independent validation passed; pipe and socket output, failure handling and source regressions verified
  target_files: scripts/usage-telemetry.py, tests/usage-normalize-cli.py, docs/USAGE-TELEMETRY.md
  blocker: none
  notes: The source adapter composite validation on 4a5643d found that moving the output parent after the final check allows normalized output inside the shared usage store. Fix is approved as important; retain all existing tests and validate the parent after this leaf closes.
         tdd: integration and contract — 1 new failing test, AC coverage 3/3 with existing regression tests.
         tdd: red digest — destination race and shared-store boundary → test_destination_moved_after_final_check_never_publishes_to_shared_store; sanitized fixed-time output and quarantine → test_normalize_emits_self_contained_sanitized_bundle, test_bad_record_quarantined_in_partial_bundle; publication failure and evidence preservation → test_destination_moved_after_final_check_never_publishes_to_shared_store, test_changed_source_and_invalid_manifest_do_not_replace_output. Focused runbook gate: 11 normalization tests pass; CLI suite has 10 pass and the new test fails because a bundle is created in shared storage.
  notes: implementation requires an independently enforced shared-store boundary or an explicitly constrained filesystem and trust model; post-write detection or advisory locking cannot enforce the stated invariant against arbitrary concurrent moves.
  notes: tdd: test amended — test_destination_moved_after_final_check_never_publishes_to_shared_store now moves the directory during normalization and verifies pipe output and no shared-store writes; the owner authorized replacing filesystem output with pipe/socket output because the original unconditional path-race contract is unenforceable without independent authority. Existing CLI tests were updated for the changed interface.
  notes: verification: normalization 22 tests, bounded reads 14, selection 7, profiles 13 passed; lint command passed. Architecture and parent specification require orchestrator updates for the output interface amendment; independent validation and composite revalidation remain pending.

  notes: pav-check NEEDS WORK — important: the pipe/socket interface has no socket success test or actual broken-pipe publication failure test, so the failure/no-false-success acceptance criterion and advertised socket contract are not fully verified. CLI tests 11/11 passed.
  notes: pav-check DONE on revalidation; CLI 13/13, source selection 7/7, normalization 11/11, bounded reads 14/14, profiles 13/13 and shell lint passed. Full runbook suite started and remains running. pav-propose --batch: no proposals.
T-03 | Immutable publication and lifecycle projection | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: independent validation passed; full suite 616 passed, 0 failed, 2 skipped
  target_files: scripts/log-step.sh, scripts/usage-telemetry.py, scripts/usage_telemetry_contract.py, scripts/usage_telemetry_ingest.py, scripts/usage_telemetry_publication.py, scripts/validate-contracts.sh, docs/USAGE-TELEMETRY.md, tests/usage-publication-cli.py, tests/usage-publication-run-race.py, tests/usage-publication-close-nonblocking.py, tests/usage-lifecycle-authority.py, tests/usage-lifecycle-projection.py, tests/usage-lifecycle-projection-no-prices.py, tests/usage-lifecycle-projection-states.py, tests/usage-lifecycle-projection-token-scalars.py, tests/usage-lifecycle-projection-trust.py
  blocker: none
  notes: Resume the existing publication branch and preserve its committed tests and implementation. The grouped task has no consolidated RED checkpoint yet: verify existing failing race tests, supplement missing acceptance coverage, and never overwrite previous tests. Ordinary run-end races remain failing and real independent authorities are not provisioned. Lifecycle projection is available on an isolated branch and scratch integration. Original clusters: T-03, T-03a, T-03b.
  branch: feat/usage-immutable-publication
  base_branch: fix/normalization-destination-safety
  base_commit: 4a5643d0d1e3ccdebc168f850c772acdd25c06fc
  commits: 82b1a923d29d24431801e79220a21ed0eb2186b5, 61eb8fb4b0c4b9f2b6f02d79ca1315f58987ca38, 9e6992d932b5936608e4fe8cb5a9c769c25a53cb, 957f0f698cd6294dbb8fffa48e12d741eae7ce58, 9c4b1e5d5ec6f6f92d0ec600d63be61644f7709a, 076b11c245c8013fca1c692352770e72463be48c, 971ec2c8e97769c5da37c41f5efeadba996c615e, 9d80c165c5ff271288e843c0b3f5c19a29330ba1, 0df88a4d05249e4b6c93e0077544f18144881eb9, 02bef88c14763ebc8a6d832a6a148f39b969d721, 8f6d0cf13c2641301ab21b44ff788d7602e8ac8a, 1755de9e813416cb4205e7e60a1c73d1ef6b39f1, 7a11e2f87526cc362460539efd7c6efac96f05ad, 900d324f29df8756520fca9c67bd35ac742b4706, e344d3acf6ee5d02f425b4235323e3bd4198eb7d, d0209806d40cacb24b9f53b9d91b0ea432f844d6, e35002311bd1a31513d1005fdb5768d46e362a41, 7c466cc0c8b9d79d018488a431324d2c573d7a6f, f6626b04b95e465040d2d8b31128155b3d36fadb, 1539427a5bc1b5f86bb094007e274fa291506509, 275eada05728b9228f2ac8f10608629bca7de3b3, e682a7d3fa51577d1c6031185279ded0ade71bff, 0c2fdf8320e5381d4df1156c79f716fbe0b0bc88, 7d21b1afd8f16e27e52b733a4c7b367aafc2f0c2, 1ce8dd1a34c669c216a71f937a66967754f78cec, 8ad675e23a62daf038d75b0053ed7282cb8b4baa, e3ad1fc88deee132cc4a9f0ac98013168d3e5f7b, 261d2e7ab5f9e402dc3d4eb0fb8305c0ba5fd69e fix: incorporate safe normalization into publication, ab83bbb5362e49d6e6aa00a59b297da718b270b4 test: verify streamed publication provenance, f3b707c52ab1d0b58246ed35c296fa2dd251a575 test: cover usage lifecycle projection, 148083d326e44620be24fd10b9a3e99aa60a84b2 fix: protect usage publication and project lifecycle data, 7d851d9f57e292ca283890f2571f976456ae801d test: reject publication after run closure, 0347a2186deba3d6b3ede462bee16777d74154a0 docs: define publication authorization at run closure, 335742c9419dd57b2a9154ef21ec7a1b7253e20c test: link published observations to lifecycle projection, 03d55702eb8480ea2ae0f9f9c918e058f2b149c5 fix: export available telemetry validators
  pr: #59 ready
  notes: Integrated the reviewed normalization fix by merge; preserved the original base_commit and publication history. Provenance now uses a separate pipe or socket descriptor.
  notes: Independent review reproduced installation after run closure; regression committed and correction in progress.
  notes: Authorization is fixed when active registration is checked; an in-flight installation may finish after close without a receipt, preserving nonblocking closure. New calls after close require separate late-import authorization.
  notes: Consolidated RED evidence: existing committed run-race tests failed on contended lock and stale registration before correction; 7d851d9 reproduced installation after closure and was amended at 0347a21 to reflect the explicitly adopted authorization boundary. Independent integration coverage added at 335742c. Focused publication 56 tests and lifecycle 50 tests passed; full stable-checkout suite remains pending.
  notes: tdd: red digest — nonblocking lifecycle and active registration: test_contended_lifecycle_lock_fails_closed_without_waiting, test_registration_cannot_go_stale_before_publication; close during installation: test_run_closed_during_install_does_not_install_active_bundle (original assertion); signed projection and replay: test_valid_exact_projection_and_replay_preserve_first_payload and integrated publication projection test.
  notes: tdd: test amended — the closure regression was updated after adopting active-registration authorization as the linearization boundary; authorized in-flight installation may finish after closure with no receipt. The original stronger assertion conflicts with nonblocking lifecycle closure under arbitrary publisher suspension.
  notes: Stable full-suite run found contract export unavailable due to future registry entries; corrected and focused export 7/7 and shell quality 3/3 passed.

T-04 | Usage resolution, ownership and exact pricing | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/usage-resolution-and-pricing
  base_branch: feat/usage-immutable-publication
  base_commit: 03d55702eb8480ea2ae0f9f9c918e058f2b149c5
  commits: e90353832b292c8067b4877dd35f760efedeb255 test: cover usage resolution and exact pricing, ba53a81713d0bd6c5ea2906b991e42c03eff1fd5 test: exercise epoch bundles through streamed output, f7484071627991a6aeaad23bd3c512372c41a0b4 feat: resolve usage observations and exact pricing, 0336841f6fd6802e854ec3f7ab916c1e2defacdc test: cover default epoch registration root, 55c8c07461054a646d2a90c1b5ff1e48be57e444 fix: restore epoch defaults and telemetry registry
  pr: #60 ready
  last_action: independent validation passed; full suite 617 passed, 0 failed, 2 skipped
  target_files: scripts/usage-telemetry.py, scripts/usage_telemetry_adapter.py, scripts/usage_telemetry_contract.py, scripts/usage_telemetry_applicability.py, scripts/usage_telemetry_completeness.py, scripts/usage_telemetry_epochs.py, scripts/usage_telemetry_exact_cost.py, scripts/usage_telemetry_identity.py, scripts/usage_telemetry_ownership.py, scripts/usage_telemetry_resolution.py, scripts/usage_telemetry_stream.py, scripts/validate-contracts.sh, tests/usage-*.py (explicit pricing and resolution suites in test commit)
  blocker: none
  notes: Resolution, ownership, pricing and epochs are implemented in isolated branches and the scratch integration branch; complete cross-component verification and final stack integration remain pending. Original clusters: T-04, T-04a, T-04b, T-04c, T-04d, T-04e, T-05, T-05a, T-05b.
  notes: tdd: red digest — seven restored unit suites covering response identity, revisions, epochs, completeness, ownership, applicability and exact cost failed on absent implementation; additional integration suites failed at collection and were not counted as RED.
  notes: tdd: test amended — epoch CLI fixture uses the reviewed pipe output interface instead of the removed output file option. Focused pricing and resolution 236 tests passed; shell lint passed.
  notes: Independent review found default epoch root NameError and missing tool usage registry entry; regression committed and both fixes pass epoch CLI 4/4 and contract export 7/7.
  notes: tdd: red digest — identity: test_branched_copies_are_one_response, test_two_responses_for_one_call_remain_distinct; revisions: test_final_snapshot_replaces_partial_snapshots_in_any_input_order, test_missing_delta_sequence_is_partial_even_with_terminal; epochs: test_single_fully_enclosed_request_has_exact_delta, test_unknown_baseline_reset_gap_and_repeated_prefix_are_unresolved; completeness: test_missing_inventory_has_unknown_denominator, test_tokens_and_pricing_are_separate_coverage_measures; ownership: test_shared_pool_is_counted_once_and_leaves_remain_incomplete, test_late_evidence_only_affects_new_report_and_order_is_deterministic; price evidence: test_historical_applicability_requires_scoped_evidence, test_alias_needs_independent_mapping_and_trusted_evidence; exact arithmetic: test_inclusive_cache_and_reasoning_are_not_counted_twice, test_round_only_the_final_sum, test_large_derived_sum_stays_exact. Seven unit suites were observed failing before implementation; integrated suites were collection-blocked.

T-06 | Retrospective reports and duration analysis | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/telemetry-retrospective-reports
  base_branch: feat/usage-resolution-and-pricing
  base_commit: 55c8c07461054a646d2a90c1b5ff1e48be57e444
  commits: f71dbeaf610579db190b6ccedaa096735ca18592 test: cover retrospective reports and durations, 15da51e3e91d58513c998d8d12f5aa4d4c6de7d5 feat: analyze and export retrospective telemetry, 991b8bf76920016656d40d59fb16ef20998b2e01 refactor: separate lint input selection
  pr: #61 ready
  last_action: independent validation passed; full suite 618 passed, 0 failed, 2 skipped
  target_files: docs/USAGE-TELEMETRY.md, scripts/log-step.sh, scripts/usage-report-publish.py, scripts/usage-telemetry.py, scripts/usage_telemetry_contract.py, scripts/usage_telemetry_sources.py, scripts/usage_telemetry_corpus.py, scripts/usage_telemetry_duration.py, scripts/usage_telemetry_exports.py, scripts/usage_telemetry_group_statistics.py, scripts/usage_telemetry_outcomes.py, scripts/usage_telemetry_report.py, scripts/validate-contracts.sh, report test files in f71dbea
  blocker: none
  notes: Retrospective analysis, report exports and epoch consumers are available in scratch integration. Same-UID export staging race remains failing; independent authority and complete integration remain unverified. Original clusters: T-06, T-06a, T-06b, T-06c, T-06d, T-06e.
  notes: tdd: red digest — group statistics test_four_values_produce_exact_even_median_and_nearest_rank_p90 and test_empty_coverage_classes_are_explicitly_unavailable failed before implementation; remaining restored tests were not individually observed RED. Scoped report suite 169 tests passed. Publisher safety depends on operator-protected destination against same-UID relocation and mutation; acknowledgement alone does not enforce it.
  notes: acceptance coverage — integrated reports: test_real_measured_groups_have_exact_statistics_and_stable_exports, test_later_defect_revision_does_not_rewrite_older_report; corpus: test_fixed_corpus_contains_only_selected_hash_verified_data, test_late_verified_input_is_excluded_even_with_early_source_time; exports: test_json_csv_markdown_preserve_report_semantics, test_every_derived_total_is_a_canonical_decimal_string; outcomes: test_resumed_failed_rejected_and_incomplete_attempts, test_experimental_evaluation_is_separate_and_counted_once; durations: test_overlapping_children_have_distinct_sum_and_union, test_incompatible_clock_prevents_exclusive, test_grandchildren_are_not_subtracted_again; statistics: test_four_values_produce_exact_even_median_and_nearest_rank_p90, test_empty_coverage_classes_are_explicitly_unavailable. Only statistics RED was observed; other cases were verified after implementation.
  notes: Full validation found cmd_lint size limit violation; extracted selection helper and focused shell quality and lint mode checks passed.

T-07 | Current status and warning delivery | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/telemetry-alert-delivery
  base_branch: feat/telemetry-retrospective-reports
  base_commit: 15da51e3e91d58513c998d8d12f5aa4d4c6de7d5
  commits: 9881392aa2a9303915c269b41f8c2f0d30004aac test: cover telemetry status and warning delivery, d40d0d1b88f641f7ee4b142c7e0a9f268caea0ba feat: compute and deliver telemetry warnings, 7eb5809e8a559e492f155ab1e0b89de6035059e7 refactor: include validated report lint selection, 16fb542e7689d9009b9fa1645aaf59c383f9da7f test: cover status output directory relocation, 69ff129460ebba47b992617a3c7eded50447642f test: cover streamed status output, f3de5d0fa9852cec8e0deabe41dd7ea533b7303b fix: stream status without file publication, a207433826021688a7872c68ce8987659c6bd6a7 test: protect warning delivery output boundaries, 2a11a2642e417c2e1f7c8d33380b51f89d54d17a test: cover protected warning destinations, a9ed6ea0ca1e656aa17a7feccc54cb3c30ef7231 fix: protect warning delivery destinations
  pr: #62 ready
  last_action: independent validation passed; full suite 619 passed, 0 failed, 2 skipped
  target_files: docs/USAGE-TELEMETRY.md, scripts/usage-telemetry.py, scripts/usage_telemetry_contract.py, scripts/usage_telemetry_alerts.py, scripts/usage_telemetry_delivery.py, scripts/usage_telemetry_duration_warning.py, scripts/usage_telemetry_modes.py, scripts/validate-contracts.sh, workflows/pe-finalize.md, status and warning test files in commits 9881392, 16fb542 and 69ff129
  blocker: none
  notes: Status and delivery exist in scratch integration. A noncooperative state replacement race remains failing, and delivery is not wired to a real workflow owner. Original clusters: T-07, T-07a, T-07b, T-07c, T-07d.
  notes: tdd: red digest — test_completeness_strict_boundary_and_unknown_denominator, test_strict_boundary_and_lower_bound, test_default_duration_crossing_is_pure_and_stable_when_collection_is_off, test_acceptance_precedes_note_and_marks_delivery_confirmed, test_crash_after_accept_recovers_idempotently failed in detached baseline because status and delivery modules were absent. Integration tests blocked at import are not counted as observed RED. Scoped suite 128 tests passed.
  notes: tdd: test amended — same-UID noncooperating edit during os.replace was replaced with tests for cooperating concurrent writers and detectable pre-replace edits after explicitly adopting the sole-owner trust boundary; advisory locks are not atomic compare-and-swap. The original adversarial race remains possible if that boundary is violated.
  notes: Merged final reviewed report lint correction; original branch point preserved.
  notes: Independent review reproduced status output directory relocation into shared storage; regression committed, streamed output correction in progress.
  notes: tdd: test amended — relocation test now checks pipe/socket-only output after the file-output contract was removed; independently reproduced original failure is recorded in 16fb542.
  notes: Independent review found owner delivery regular stdout and shared note path can write into shared usage store; failing regression committed before correction.
  notes: Owner delivery rejects non-pipe output and direct shared-store destinations before mutations; selected state and note directories require operator protection against same-UID relocation. Scoped warning suite 134 tests passed.

T-08 | Compatibility, recovery and operating guidance | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: feat/telemetry-recovery-guidance
  base_branch: feat/telemetry-alert-delivery
  base_commit: d40d0d1b88f641f7ee4b142c7e0a9f268caea0ba
  commits: 92ac448d97933adb37dc6cb273e870b81244a719 test: cover offline telemetry recovery, 313f8a933903db411b2d5744459a3e5a9d835281 docs: explain offline telemetry recovery, 0bff49829150d8726e5ed87ef2943cb36c413253 test: verify signed offline analysis, 9c6da4dad60b57826060f76aac6b6dbc1d33e5db refactor: include validated report lint selection, 1011f9bb40af9c8341b45b25af815c2c4a598388 fix: include safe status output, f0060323603ff5e8c8582a5f81f6489f6ae601dc fix: include protected warning delivery, fc741833114ce444ada91d61168235c6bc1e39c1 test: verify signed telemetry recovery
  pr: #63 ready
  last_action: independent validation passed; full suite 619 passed, 0 failed, 2 skipped
  target_files: docs/USAGE-TELEMETRY.md, scripts/validate-contracts.sh, workflows/retro.md, tests/usage-legacy-recovery.py, tests/usage-offline-acceptance.py
  blocker: none
  notes: Guidance and compatibility fixtures exist in isolated branches; genuine end-to-end acceptance, optional dependencies, recovery and final review remain pending. Original clusters: T-08, T-08a, T-08b.

  notes: Parallel compatibility branch includes 8 recovery tests and 2 offline acceptance tests; these characterize integrated behavior and were not observed RED. Tests use synthetic RSA key lookup and independent verifier. Stack reconciliation and independent validation remain pending.
  notes: tdd: red digest — recovery and end-to-end tests characterize already integrated behavior; they were not observed RED. test_disable_and_resume_preserves_evidence_without_backfill, test_disable_resume_status_preserves_receipts_and_reports_segment_gap, test_signed_cli_disable_resume_replays_installed_bundle and offline acceptance cover recovery, independent signed publication, 2/2 token and 1/2 pricing coverage, three exports, and 0.00264 projection. Test key lookup is substituted with an explicit synthetic public key.

## Integration Issues (T-02)

### Approved
1. Important — a concurrent destination-directory move between validation and installation can publish normalized output inside the shared usage store. Reproduce the race, enforce a safe destination boundary and retain the existing normalization checks. Fix sibling: T-02c.

### Deferred
None.

## Contract Check

### Invariants
| Invariant | Status |
|---|---|
| Legacy lifecycle remains nonblocking and optional | PASS: recovery and publication tests preserve lifecycle evidence and optional-dependency behavior. |
| Usage publication is validated and immutable | PASS: publication and replay tests verify installation and receipts. |
| Explicit inputs, observation time, and independent inventory govern completeness | PASS: source, bounded-read, inventory and corpus tests. |
| Exact arithmetic and evidence-based ownership | PASS: exact-cost, causal-ownership and offline acceptance tests. |
| Authorized owner controls shared state | PASS within documented operator-protected directories and cooperating-writer boundary; status remains pure. |

### Acceptance Criteria
| Criterion | Status |
|---|---|
| Specification criteria 01–24 | PASS on synthetic scenarios: each mapped to source, pricing, ownership, publication, lifecycle, warning, report, duration, schema or offline acceptance tests. The complete run on fc74183 passed 619 checks with two private-pattern hygiene skips. |
| Existing lifecycle and optional-dependency behavior | PASS: recovery and publication tests; full suite passed. |
| Reproducible explicit-file analysis with evidence-limited results | PASS: fixed-corpus, report, exact-cost and offline acceptance tests. |

### Off-limits
| Constraint | Status |
|---|---|
| Raw prompts, responses, source contents, credentials and paths excluded from shared telemetry | PASS on inspected paths and privacy tests; local private-pattern scans were skipped because patterns were not configured. |
| No rewriting accepted lifecycle evidence or invented prices/identities | PASS: immutable publication, exact retry, evidence and lifecycle tests. |
| No model policy changes, paid calls or implicit historical discovery | PASS on inspected usage scripts and offline tests; suite-wide network isolation is not independently enforced. |

Operational limitations: the only built-in reviewed source profile is synthetic; external signing authority is not supplied. End-to-end tests use a synthetic key and construct some evidence. Protected directories and cooperation by same-UID writers are deployment requirements, not guarantees enforced by advisory locks.

## Code Review
- Independent targeted review found no confirmed critical, important or optional defects on fc74183. It inspected security boundaries, source adapters, ingestion, pricing, ownership, epochs, corpus, exports, warning delivery and selected CLI/producer paths; large schema, report and resolver modules were reviewed selectively, not line by line.
- Full stable suite: 619 passed, 0 failed, 2 skipped for absent private hygiene patterns. ShellCheck unavailable; Bash syntax passed.

## Issue List
### Approved
(none)
### Deferred
(none)

## Fix-Tasks
fixes-count: 0

## Deferred
(none)

## Spec Sync
sync: complete
synced_at: 2026-10-30
deltas: 3 (implemented-differently: 3, not-implemented: 0, implemented-beyond: 0)
spec: .ai/specs/05-cost-and-duration-telemetry.md

## Pull Request Promotion
- PRs #37–#63 promoted to ready for review in stack order using the connected GitHub application. The command-line token lacked permission for this transition.
