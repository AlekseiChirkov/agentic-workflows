# Usage test audit: first alphabetical group

Scores reflect necessity of tested behavior, not coverage percentage. A dash means the method was inventoried but its body has not been reviewed; it is not a score of zero.
Only tests with inspected bodies receive scores. Assessing a name or a list of assertion methods alone would not establish what the test actually proves.

| File | Method | Score | Evidence and rationale |
|---|---|---:|---|
| tests/usage-accepted-outcomes.py | `test_resumed_failed_rejected_and_incomplete_attempts` | 90 | Body inspected: resumed failed rejected and incomplete attempts. |
| tests/usage-accepted-outcomes.py | `test_no_independent_acceptance_is_unavailable` | 95 | Body inspected: no independent acceptance is unavailable. |
| tests/usage-accepted-outcomes.py | `test_exact_decimal_arithmetic_and_unknown_cost` | 95 | Body inspected: exact decimal arithmetic and unknown cost. |
| tests/usage-accepted-outcomes.py | `test_experimental_evaluation_is_separate_and_counted_once` | 90 | Body inspected: experimental evaluation is separate and counted once. |
| tests/usage-accepted-outcomes.py | `test_late_revision_applies_only_to_new_report` | 95 | Body inspected: late revision applies only to new report. |
| tests/usage-accepted-outcomes.py | `test_comparison_requires_compatible_evidence_and_scope` | 95 | Body inspected: comparison requires compatible evidence and scope. |
| tests/usage-accepted-outcomes.py | `test_contract_mismatch_and_unrelated_evidence_do_not_accept` | 95 | Body inspected: contract mismatch and unrelated evidence do not accept. |
| tests/usage-accepted-outcomes.py | `test_order_independence_and_output_privacy` | 90 | Body inspected: order independence and output privacy. |
| tests/usage-accepted-outcomes.py | `test_late_work_and_evaluation_do_not_enter_older_corpus` | 95 | Body inspected: late work and evaluation do not enter older corpus. |
| tests/usage-accepted-outcomes.py | `test_revision_conflicts_are_rejected_for_every_input_order` | 90 | Body inspected: revision conflicts are rejected for every input order. |
| tests/usage-accepted-outcomes.py | `test_long_terminating_ratio_preserves_all_digits` | 85 | Body inspected: long terminating ratio preserves all digits. |
| tests/usage-accepted-outcomes.py | `test_nonterminating_ratio_remains_exact_and_comparable` | 90 | Body inspected: nonterminating ratio remains exact and comparable. |
| tests/usage-accepted-outcomes.py | `test_incomplete_experimental_cost_marks_combined_total_incomplete` | 95 | Body inspected: incomplete experimental cost marks combined total incomplete. |
| tests/usage-accepted-outcomes.py | `test_large_exact_results_remain_comparable_after_carry` | 90 | Body inspected: large exact results remain comparable after carry. |
| tests/usage-accepted-outcomes.py | `test_same_attempt_conflicts_cannot_be_silently_double_counted` | 95 | Body inspected: same attempt conflicts cannot be silently double counted. |
| tests/usage-alert-status.py | `test_repeated_status_is_pure_and_has_stable_candidate` | 90 | Body inspected: repeated status is pure and has stable candidate. |
| tests/usage-alert-status.py | `test_strict_boundary_and_lower_bound` | 95 | Body inspected: strict boundary and lower bound. |
| tests/usage-alert-status.py | `test_expiry_scope_and_invalid_completeness` | 90 | Body inspected: expiry scope and invalid completeness. |
| tests/usage-alert-status.py | `test_unknown_does_not_reset_but_observed_below_does` | 95 | Body inspected: unknown does not reset but observed below does. |
| tests/usage-alert-status.py | `test_late_correction_does_not_erase_delivered_warning` | 90 | Body inspected: late correction does not erase delivered warning. |
| tests/usage-alert-status.py | `test_unknown_and_conflicting_values_never_guess_money` | 95 | Body inspected: unknown and conflicting values never guess money. |
| tests/usage-alert-status.py | `test_completeness_strict_boundary_and_unknown_denominator` | 90 | Body inspected: completeness strict boundary and unknown denominator. |
| tests/usage-alert-status.py | `test_invalid_snapshot_fields_cannot_inject_proof_or_leak` | 95 | Body inspected: invalid snapshot fields cannot inject proof or leak. |
| tests/usage-alert-status.py | `test_missing_and_malformed_metrics_keep_pending_episode` | 95 | Body inspected: missing and malformed metrics keep pending episode. |
| tests/usage-alert-status.py | `test_request_and_span_require_trusted_membership_and_preserve_owner` | 95 | Body inspected: request and span require trusted membership and preserve owner. |
| tests/usage-alert-status.py | `test_unknown_completeness_has_own_diagnostic_and_no_invented_percentage` | 90 | Body inspected: unknown completeness has own diagnostic and no invented percentage. |
| tests/usage-alert-status.py | `test_status_returns_verified_current_measurements_and_completeness` | 90 | Body inspected: status returns verified current measurements and completeness. |
| tests/usage-alert-status.py | `test_output_capacity_exhaustion_preserves_old_episode_without_candidate` | 95 | Body inspected: output capacity exhaustion preserves old episode without candidate. |
| tests/usage-alert-status.py | `test_output_byte_exhaustion_does_not_raise_or_drop_prior` | 95 | Body inspected: output byte exhaustion does not raise or drop prior. |
| tests/usage-alert-status.py | `test_prior_scoped_pending_survives_missing_new_measurements` | 95 | Body inspected: prior scoped pending survives missing new measurements. |
| tests/usage-alert-status.py | `test_pending_survives_unavailable_or_foreign_analysis_without_accepting_values` | 95 | Body inspected: pending survives unavailable or foreign analysis without accepting values. |
| tests/usage-analysis-corpus-schema.py | `test_complete_manifest_preserves_inputs_and_explicit_unknowns` | 90 | Body inspected: complete manifest preserves inputs and explicit unknowns. |
| tests/usage-analysis-corpus-schema.py | `test_required_fields_versions_scope_and_closed_shape` | 95 | Body inspected: required fields versions scope and closed shape. |
| tests/usage-analysis-corpus-schema.py | `test_entries_require_explicit_hash_type_path_and_size` | 95 | Body inspected: entries require explicit hash type path and size. |
| tests/usage-analysis-corpus-schema.py | `test_explicit_limits_cover_selected_bytes_and_entry_count` | 95 | Body inspected: explicit limits cover selected bytes and entry count.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-analysis-corpus-schema.py | `test_exclusions_are_explicit_and_private_content_is_not_echoed` | 95 | Body inspected: exclusions are explicit and private content is not echoed. |
| tests/usage-analysis-corpus-schema.py | `test_identifier_mappings_require_explicit_bounded_and_safe_values` | 95 | Body inspected: identifier mappings require explicit bounded and safe values.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-analysis-corpus-schema.py | `test_json_duplicate_keys_and_raw_and_canonical_byte_limits` | 90 | Body inspected: json duplicate keys and raw and canonical byte limits. |
| tests/usage-analysis-corpus-schema.py | `test_manifest_validation_never_reads_or_discovers_history` | 85 | Body inspected: manifest validation never reads or discovers history. |
| tests/usage-analyze-cli-errors.py | `test_failed_analysis_reports_analysis_and_hides_private_paths` | 90 | Body inspected: failed analysis reports analysis and hides private paths. |
| tests/usage-analyze-cli-evidence.py | `test_signed_synthetic_authority_builds_reproducible_report` | 90 | Body inspected: signed synthetic authority builds reproducible report. |
| tests/usage-analyze-cli-evidence.py | `test_regular_file_stdout_is_rejected_without_writes` | 90 | Body inspected: regular file stdout is rejected without writes. |
| tests/usage-analyze-cli-evidence.py | `test_self_signed_user_owned_key_is_rejected_by_real_cli` | 95 | Body inspected: self signed user owned key is rejected by real cli. |
| tests/usage-analyze-cli-evidence.py | `test_signed_rsa_authority_works_without_optional_crypto_module` | 95 | Body inspected: signed rsa authority works without optional crypto module. |
| tests/usage-analyze-cli-evidence.py | `test_optional_ed25519_authority` | 90 | Body inspected: optional ed25519 authority. |
| tests/usage-analyze-cli-evidence.py | `test_signature_and_exact_scope_are_required` | 95 | Body inspected: signature and exact scope are required. |
| tests/usage-analyze-cli-evidence.py | `test_scenario_must_match_explicit_corpus` | 90 | Body inspected: scenario must match explicit corpus. |
| tests/usage-analyze-cli-evidence.py | `test_authority_binds_manifest_cutoff_and_selection` | 95 | Body inspected: authority binds manifest cutoff and selection. |
| tests/usage-attribution-schema.py | `test_full_and_explicit_unknowns_are_preserved` | 90 | Body inspected: full and explicit unknowns are preserved. |
| tests/usage-attribution-schema.py | `test_compact_existing_form_and_valid_kinds` | 85 | Body inspected: compact existing form and valid kinds. |
| tests/usage-attribution-schema.py | `test_invalid_fields_and_untrusted_identifiers` | 95 | Body inspected: invalid fields and untrusted identifiers. |
| tests/usage-attribution-schema.py | `test_candidate_boundary_duplicates_and_types` | 90 | Body inspected: candidate boundary duplicates and types. |
| tests/usage-attribution-schema.py | `test_observation_and_bundle_accept_same_attribution_and_reject_bad` | 90 | Body inspected: observation and bundle accept same attribution and reject bad. |
| tests/usage-attribution-schema.py | `test_canonical_candidates_are_order_independent` | 90 | Body inspected: canonical candidates are order independent. |
| tests/usage-attribution-schema.py | `test_json_rejects_duplicate_fields` | 90 | Body inspected: json rejects duplicate fields. |
| tests/usage-authority-permit.py | `test_valid_independent_permit_accepts_exact_bundle` | 95 | Body inspected: valid independent permit accepts exact bundle. |
| tests/usage-authority-permit.py | `test_unsigned_or_mismatched_permit_cannot_authorize` | 95 | Body inspected: unsigned or mismatched permit cannot authorize. |
| tests/usage-authority-permit.py | `test_different_authority_key_cannot_replace_registered_key` | 95 | Body inspected: different authority key cannot replace registered key. |
| tests/usage-authority-permit.py | `test_missing_crypto_dependency_fails_closed` | 90 | Body inspected: missing crypto dependency fails closed. |
| tests/usage-authority-permit.py | `test_user_owned_anchor_fails_closed_at_real_cli` | 95 | Body inspected: user owned anchor fails closed at real cli. |
| tests/usage-authority-permit.py | `test_self_hmac_without_independent_permit_cannot_authorize` | 95 | Body inspected: self hmac without independent permit cannot authorize. |
| tests/usage-authority-rsa-permit.py | `test_valid_permit_publishes_without_external_libraries` | 95 | Body inspected: valid permit publishes without external libraries. |
| tests/usage-authority-rsa-permit.py | `test_signed_permit_for_another_bundle_scope_or_profile_is_rejected` | 95 | Body inspected: signed permit for another bundle scope or profile is rejected. |
| tests/usage-authority-rsa.py | `test_independently_signed_fixture_is_accepted` | 95 | Body inspected: independently signed fixture is accepted. |
| tests/usage-authority-rsa.py | `test_signature_and_message_are_bound_exactly` | 95 | Body inspected: signature and message are bound exactly. |
| tests/usage-authority-rsa.py | `test_signed_noncanonical_padding_is_rejected` | 95 | Body inspected: signed noncanonical padding is rejected. |
| tests/usage-authority-rsa.py | `test_malformed_key_and_der_trailing_data_are_rejected` | 95 | Body inspected: malformed key and der trailing data are rejected. |
| tests/usage-bounded-source-reads.py | `test_selected_external_file_bytes_and_no_neighbor_access` | 90 | Body inspected: selected external file bytes and no neighbor access. |
| tests/usage-bounded-source-reads.py | `test_invalid_manifest_profile_or_scope_rejected_before_source_access` | 95 | Body inspected: invalid manifest profile or scope rejected before source access. |
| tests/usage-bounded-source-reads.py | `test_size_hash_exact_byte_limits_and_multibyte` | 95 | Body inspected: size hash exact byte limits and multibyte. |
| tests/usage-bounded-source-reads.py | `test_prefix_hash_and_changed_prefix` | 90 | Body inspected: prefix hash and changed prefix. |
| tests/usage-bounded-source-reads.py | `test_symlinks_directories_and_symlinked_ancestors_are_rejected` | 95 | Body inspected: symlinks directories and symlinked ancestors are rejected. |
| tests/usage-bounded-source-reads.py | `test_symlink_swap_during_open_never_reads_target` | 95 | Body inspected: symlink swap during open never reads target. |
| tests/usage-bounded-source-reads.py | `test_json_record_limits_bytes_depth_and_no_partial_success` | 90 | Body inspected: json record limits bytes depth and no partial success. |
| tests/usage-bounded-source-reads.py | `test_all_paths_are_checked_before_reading_any_selected_contents` | 95 | Body inspected: all paths are checked before reading any selected contents. |
| tests/usage-bounded-source-reads.py | `test_concurrent_append_never_reads_beyond_the_selected_extent` | 95 | Body inspected: concurrent append never reads beyond the selected extent. |
| tests/usage-bounded-source-reads.py | `test_selected_reads_do_not_use_network` | 80 | Body inspected: selected reads do not use network. |
| tests/usage-bounded-source-reads.py | `test_opened_source_descriptor_is_closed_when_fstat_fails` | 90 | Body inspected: opened source descriptor is closed when fstat fails. |
| tests/usage-bounded-source-reads.py | `test_unknown_finite_float_does_not_invalidate_raw_record` | 80 | Body inspected: unknown finite float does not invalidate raw record. |
| tests/usage-bounded-source-reads.py | `test_record_limits_apply_across_all_selected_files` | 90 | Body inspected: record limits apply across all selected files. |
| tests/usage-bounded-source-reads.py | `test_invalid_profile_and_owner_are_rejected_before_any_open` | 95 | Body inspected: invalid profile and owner are rejected before any open. |
| tests/usage-canonical-encoding.py | `test_key_and_set_permutations_preserve_bytes_and_hash` | 90 | Body inspected: key and set permutations preserve bytes and hash. |
| tests/usage-canonical-encoding.py | `test_schema_set_key_controls_order_and_identity` | 90 | Body inspected: schema set key controls order and identity. |
| tests/usage-canonical-encoding.py | `test_nested_arrays_keep_order_within_declared_set` | 90 | Body inspected: nested arrays keep order within declared set. |
| tests/usage-canonical-encoding.py | `test_nested_arrays_keep_order_with_key_sorted_set` | 90 | Body inspected: nested arrays keep order with key sorted set. |
| tests/usage-canonical-encoding.py | `test_schema_sets_apply_to_fields_inside_array_members` | 90 | Body inspected: schema sets apply to fields inside array members. |
| tests/usage-canonical-encoding.py | `test_json_array_and_object_discriminators_are_canonical` | 80 | Body inspected: json array and object discriminators are canonical. |
| tests/usage-canonical-encoding.py | `test_envelope_discriminator_preserves_schema_set_ordering` | 90 | Body inspected: envelope discriminator preserves schema set ordering. |
| tests/usage-canonical-encoding.py | `test_stream_order_changes_bytes_and_identity` | 90 | Body inspected: stream order changes bytes and identity. |
| tests/usage-canonical-encoding.py | `test_strict_json_rejects_duplicate_keys_and_special_numbers` | 95 | Body inspected: strict json rejects duplicate keys and special numbers. |
| tests/usage-canonical-encoding.py | `test_counter_rejects_boolean_fraction_negative_and_overflow` | 90 | Body inspected: counter rejects boolean fraction negative and overflow. |
| tests/usage-canonical-encoding.py | `test_decimal_rejects_noncanonical_prices` | 90 | Body inspected: decimal rejects noncanonical prices. |
| tests/usage-canonical-encoding.py | `test_unknown_schema_version_is_rejected` | 80 | Body inspected: unknown schema version is rejected. |
| tests/usage-canonical-encoding.py | `test_fixed_observation_has_stable_documented_utf8_vector` | 90 | Body inspected: fixed observation has stable documented utf8 vector. |
| tests/usage-causal-ownership.py | `test_measurement_evidence_requires_matching_and_authorized_source` | 95 | Body inspected: measurement evidence requires matching and authorized source. |
| tests/usage-causal-ownership.py | `test_authorized_measurement_scope_is_explicit_and_exact` | 95 | Body inspected: authorized measurement scope is explicit and exact. |
| tests/usage-causal-ownership.py | `test_scope_attestation_is_bound_to_record_and_measurement` | 95 | Body inspected: scope attestation is bound to record and measurement. |
| tests/usage-causal-ownership.py | `test_response_identity_includes_provider_and_account_scope` | 95 | Body inspected: response identity includes provider and account scope. |
| tests/usage-causal-ownership.py | `test_shared_pool_is_counted_once_and_leaves_remain_incomplete` | 95 | Body inspected: shared pool is counted once and leaves remain incomplete. |
| tests/usage-causal-ownership.py | `test_unknown_or_unauthorized_ownership_is_not_promoted` | 95 | Body inspected: unknown or unauthorized ownership is not promoted. |
| tests/usage-causal-ownership.py | `test_external_unattributed_pool_is_not_included_in_complete_parent` | 95 | Body inspected: external unattributed pool is not included in complete parent. |
| tests/usage-causal-ownership.py | `test_late_evidence_only_affects_new_report_and_order_is_deterministic` | 90 | Body inspected: late evidence only affects new report and order is deterministic. |
| tests/usage-causal-ownership.py | `test_no_history_read_or_private_payload_leak` | 95 | Body inspected: no history read or private payload leak. |
| tests/usage-collection-segment-schema.py | `test_declared_boundaries_mode_and_explicit_unknown_are_preserved` | 90 | Body inspected: declared boundaries mode and explicit unknown are preserved. |
| tests/usage-collection-segment-schema.py | `test_required_fields_versions_modes_and_private_payload` | 95 | Body inspected: required fields versions modes and private payload. |
| tests/usage-collection-segment-schema.py | `test_times_and_gap_state_do_not_invent_continuity` | 95 | Body inspected: times and gap state do not invent continuity. |
| tests/usage-collection-segment-schema.py | `test_arbitrary_precision_boundary_ordering` | 90 | Body inspected: arbitrary precision boundary ordering. |
| tests/usage-collection-segment-schema.py | `test_size_limit_and_duplicate_json_keys` | 85 | Body inspected: size limit and duplicate json keys. |
| tests/usage-collection-segment-schema.py | `test_bundle_accepts_segment_and_rejects_invalid_or_duplicate_entries` | 90 | Body inspected: bundle accepts segment and rejects invalid or duplicate entries. |
| tests/usage-collection-segments.py | `test_unset_mode_defaults_off_without_creating_a_segment` | 85 | Body inspected: unset mode defaults off without creating a segment. |
| tests/usage-collection-segments.py | `test_enable_disable_and_reenable_preserve_evidence_and_expose_gap` | 95 | Body inspected: enable disable and reenable preserve evidence and expose gap. |
| tests/usage-collection-segments.py | `test_duplicate_transitions_are_idempotent_and_equal_boundary_is_valid` | 90 | Body inspected: duplicate transitions are idempotent and equal boundary is valid. |
| tests/usage-collection-segments.py | `test_invalid_mode_and_missing_authorization_fail_closed` | 95 | Body inspected: invalid mode and missing authorization fail closed. |
| tests/usage-collection-segments.py | `test_invalid_or_backwards_boundary_is_rejected_without_mutation` | 95 | Body inspected: invalid or backwards boundary is rejected without mutation. |
| tests/usage-collection-segments.py | `test_missing_open_segment_cannot_silently_claim_active_collection` | 90 | Body inspected: missing open segment cannot silently claim active collection. |
| tests/usage-collection-segments.py | `test_overlapping_closed_segments_cannot_prove_a_collection_gap` | 90 | Body inspected: overlapping closed segments cannot prove a collection gap. |
| tests/usage-collection-segments.py | `test_explicit_off_segment_keeps_full_gap_since_collection_stopped` | 90 | Body inspected: explicit off segment keeps full gap since collection stopped. |
| tests/usage-collection-segments.py | `test_distinct_segments_cannot_share_an_identity` | 90 | Body inspected: distinct segments cannot share an identity. |
| tests/usage-collection-segments.py | `test_session_owner_is_preserved_and_unrelated_owners_are_rejected` | 95 | Body inspected: session owner is preserved and unrelated owners are rejected. |
| tests/usage-context-evidence-timing.py | `test_only_independently_proven_early_evidence_is_retained` | 95 | Body inspected: only independently proven early evidence is retained. |
| tests/usage-context-evidence-timing.py | `test_invented_member_proofs_fail_closed` | 95 | Body inspected: invented member proofs fail closed. |
| tests/usage-context-evidence-timing.py | `test_nested_members_count_toward_the_record_limit` | 90 | Body inspected: nested members count toward the record limit. |
| tests/usage-contract-export.py | `test_legacy_vocabulary_is_preserved` | 85 | Body inspected: legacy vocabulary is preserved. |
| tests/usage-contract-export.py | `test_export_matches_shared_registry_and_validator_vocabulary` | 95 | Body inspected: export matches shared registry and validator vocabulary. |
| tests/usage-contract-export.py | `test_no_jq_preserves_contract_and_existing_logging` | 90 | Body inspected: no jq preserves contract and existing logging. |
| tests/usage-contract-export.py | `test_missing_python_does_not_claim_usage_is_available` | 95 | Body inspected: missing python does not claim usage is available. |
| tests/usage-contract-export.py | `test_broken_registry_cannot_assert_availability` | 95 | Body inspected: broken registry cannot assert availability. |
| tests/usage-contract-export.py | `test_exported_definitions_validate_without_repository_access` | 95 | Body inspected: exported definitions validate without repository access. |
| tests/usage-contract-export.py | `test_missing_required_kind_disables_export` | 90 | Body inspected: missing required kind disables export. |
| tests/usage-cumulative-epochs.py | `test_single_fully_enclosed_request_has_exact_delta` | 90 | Body inspected: single fully enclosed request has exact delta. |
| tests/usage-cumulative-epochs.py | `test_mid_request_snapshot_is_not_full_request_usage` | 90 | Body inspected: mid request snapshot is not full request usage. |
| tests/usage-cumulative-epochs.py | `test_two_requests_are_not_assigned_individual_usage` | 90 | Body inspected: two requests are not assigned individual usage. |
| tests/usage-cumulative-epochs.py | `test_atomic_completion_profile_can_prove_one_request` | 95 | Body inspected: atomic completion profile can prove one request. |
| tests/usage-cumulative-epochs.py | `test_completion_at_initial_boundary_is_not_attributed_to_interval` | 90 | Body inspected: completion at initial boundary is not attributed to interval. |
| tests/usage-cumulative-epochs.py | `test_completion_just_after_initial_boundary_can_be_attributed` | 90 | Body inspected: completion just after initial boundary can be attributed. |
| tests/usage-cumulative-epochs.py | `test_each_identity_dimension_must_match_and_be_known` | 95 | Body inspected: each identity dimension must match and be known. |
| tests/usage-cumulative-epochs.py | `test_unknown_baseline_reset_gap_and_repeated_prefix_are_unresolved` | 95 | Body inspected: unknown baseline reset gap and repeated prefix are unresolved. |
| tests/usage-cumulative-epochs.py | `test_complete_inventory_is_required_for_interval_delta` | 95 | Body inspected: complete inventory is required for interval delta. |
| tests/usage-cumulative-epochs.py | `test_missing_end_boundary_or_request_extent_never_proves_usage` | 90 | Body inspected: missing end boundary or request extent never proves usage. |
| tests/usage-cumulative-epochs.py | `test_zero_is_evidenced_but_missing_is_not_zero` | 95 | Body inspected: zero is evidenced but missing is not zero. |
| tests/usage-cumulative-epochs.py | `test_disjoint_aggregate_intervals_have_a_separate_total` | 90 | Body inspected: disjoint aggregate intervals have a separate total. |
| tests/usage-cumulative-epochs.py | `test_nonoverlapping_derived_sum_above_safe_integer_remains_exact` | 85 | Body inspected: two nonoverlapping maximum-safe integers verify exact sum beyond the safe-integer boundary; the prior 1025-item workload is no longer exercised. |
| tests/usage-cumulative-epochs.py | `test_overlap_unknown_bounds_or_units_are_only_reconciliation` | 90 | Body inspected: overlap unknown bounds or units are only reconciliation. |
| tests/usage-cumulative-epochs.py | `test_aggregate_permutation_is_deterministic_and_duplicate_is_not_added` | 90 | Body inspected: aggregate permutation is deterministic and duplicate is not added. |
| tests/usage-cumulative-epochs.py | `test_empty_aggregate_set_is_unknown_not_zero` | 90 | Body inspected: empty aggregate set is unknown not zero. |
| tests/usage-cumulative-epochs.py | `test_invalid_numeric_values_are_never_treated_as_valid_usage` | 95 | Body inspected: invalid numeric values are never treated as valid usage. |
| tests/usage-current-run-snapshot-schema.py | `test_complete_snapshot_preserves_receipts_observations_and_unknowns` | 95 | Body inspected: complete snapshot preserves receipts observations and unknowns. |
| tests/usage-current-run-snapshot-schema.py | `test_session_scope_and_time_only_disabled_snapshot` | 85 | Body inspected: session scope and time only disabled snapshot. |
| tests/usage-current-run-snapshot-schema.py | `test_required_fields_closed_shape_and_private_payload` | 95 | Body inspected: required fields closed shape and private payload. |
| tests/usage-current-run-snapshot-schema.py | `test_scope_revision_mode_and_bounds_are_strict` | 95 | Body inspected: scope revision mode and bounds are strict. |
| tests/usage-current-run-snapshot-schema.py | `test_receipt_bundle_and_inventory_evidence_are_self_contained` | 95 | Body inspected: receipt bundle and inventory evidence are self contained. |
| tests/usage-current-run-snapshot-schema.py | `test_bundle_diagnostics_match_snapshot_owner_and_receipt` | 95 | Body inspected: bundle diagnostics match snapshot owner and receipt. |
| tests/usage-current-run-snapshot-schema.py | `test_receipt_bound_quarantine_diagnostic_preserves_source_binding` | 95 | Body inspected: receipt bound quarantine diagnostic preserves source binding. |
| tests/usage-current-run-snapshot-schema.py | `test_delivery_state_is_closed_bounded_and_unique` | 95 | Body inspected: delivery state is closed bounded and unique. |
| tests/usage-current-run-snapshot-schema.py | `test_warning_policy_scope_metric_and_episode_survive_clear_and_recross` | 95 | Body inspected: warning policy scope metric and episode survive clear and recross. |
| tests/usage-current-run-snapshot-schema.py | `test_warning_subscopes_and_multiple_episodes_preserve_independent_delivery` | 95 | Body inspected: warning subscopes and multiple episodes preserve independent delivery. |
| tests/usage-current-run-snapshot-schema.py | `test_json_duplicate_keys_and_declared_limits` | 90 | Body inspected: json duplicate keys and declared limits. |
| tests/usage-current-run-snapshot-schema.py | `test_explicit_private_part_manifest_is_valid_without_opening_files` | 95 | Body inspected: explicit private part manifest is valid without opening files. |
| tests/usage-current-run-snapshot-schema.py | `test_part_manifest_rejects_implicit_or_unbounded_inputs` | 95 | Body inspected: part manifest rejects implicit or unbounded inputs.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-current-run-snapshot-schema.py | `test_part_read_limits_must_be_explicit_and_cover_the_selected_total` | 95 | Body inspected: part read limits must be explicit and cover the selected total. |
| tests/usage-current-run-snapshot-schema.py | `test_snapshot_schema_sets_have_stable_canonical_identity` | 90 | Body inspected: snapshot schema sets have stable canonical identity. |
| tests/usage-diagnostic-registry.py | `test_registered_namespaces_preserve_exact_measurement_and_provenance` | 85 | Body inspected: registered namespaces preserve exact measurement and provenance. |
| tests/usage-diagnostic-registry.py | `test_absent_and_explicit_unknown_do_not_become_measured_zero` | 90 | Body inspected: absent and explicit unknown do not become measured zero. |
| tests/usage-diagnostic-registry.py | `test_scope_source_and_metric_filter_cannot_borrow_other_evidence` | 95 | Body inspected: scope source and metric filter cannot borrow other evidence. |
| tests/usage-diagnostic-registry.py | `test_replayed_event_does_not_double_count_and_conflict_is_rejected` | 90 | Body inspected: replayed event does not double count and conflict is rejected. |
| tests/usage-diagnostic-registry.py | `test_byte_observation_does_not_create_usage_cost_or_quality` | 90 | Body inspected: byte observation does not create usage cost or quality. |
| tests/usage-diagnostic-registry.py | `test_unregistered_names_invalid_records_and_nonopaque_scope_fail_closed` | 95 | Body inspected: unregistered names invalid records and nonopaque scope fail closed. |
| tests/usage-diagnostic-schema.py | `test_registered_metrics_preserve_units_and_scopes` | 90 | Body inspected: registered metrics preserve units and scopes. |
| tests/usage-diagnostic-schema.py | `test_event_attempt_and_context_references_remain_opaque` | 95 | Body inspected: event attempt and context references remain opaque. |
| tests/usage-diagnostic-schema.py | `test_unknown_is_explicit_and_does_not_become_zero` | 95 | Body inspected: unknown is explicit and does not become zero. |
| tests/usage-diagnostic-schema.py | `test_invalid_metric_unit_value_scope_and_source` | 95 | Body inspected: invalid metric unit value scope and source. |
| tests/usage-diagnostic-schema.py | `test_private_fields_are_rejected_without_echo` | 95 | Body inspected: private fields are rejected without echo. |
| tests/usage-diagnostic-schema.py | `test_byte_limit_and_duplicate_keys` | 85 | Body inspected: byte limit and duplicate keys. |
| tests/usage-diagnostic-schema.py | `test_bundle_accepts_valid_and_rejects_malformed_diagnostics` | 90 | Body inspected: bundle accepts valid and rejects malformed diagnostics. |
| tests/usage-duration-analysis.py | `test_overlapping_children_have_distinct_sum_and_union` | 90 | Body inspected: overlapping children have distinct sum and union. |
| tests/usage-duration-analysis.py | `test_grandchildren_are_not_subtracted_again` | 90 | Body inspected: grandchildren are not subtracted again. |
| tests/usage-duration-analysis.py | `test_missing_child_preserves_observed_coverage_but_not_exclusive` | 90 | Body inspected: missing child preserves observed coverage but not exclusive. |
| tests/usage-duration-analysis.py | `test_incompatible_clock_prevents_exclusive` | 90 | Body inspected: incompatible clock prevents exclusive. |
| tests/usage-duration-analysis.py | `test_proven_offset_makes_clocks_comparable` | 90 | Body inspected: proven offset makes clocks comparable. |
| tests/usage-duration-analysis.py | `test_out_of_bounds_child_is_clipped_but_tree_is_inconsistent` | 90 | Body inspected: out of bounds child is clipped but tree is inconsistent. |
| tests/usage-duration-analysis.py | `test_unrelated_overlap_does_not_prove_parentage` | 90 | Body inspected: unrelated overlap does not prove parentage. |
| tests/usage-duration-analysis.py | `test_duplicate_identical_interval_is_not_counted_twice` | 90 | Body inspected: duplicate identical interval is not counted twice. |
| tests/usage-duration-analysis.py | `test_conflicting_duplicate_identity_invalidates_tree` | 90 | Body inspected: conflicting duplicate identity invalidates tree. |
| tests/usage-duration-analysis.py | `test_negative_and_unfinished_intervals_are_not_exact` | 90 | Body inspected: negative and unfinished intervals are not exact. |
| tests/usage-duration-analysis.py | `test_invalid_parent_does_not_report_exact_wall` | 85 | Body inspected: invalid parent does not report exact wall. |
| tests/usage-duration-analysis.py | `test_empty_complete_tree_has_zero_child_work` | 85 | Body inspected: empty complete tree has zero child work. |
| tests/usage-duration-analysis.py | `test_omitted_completeness_does_not_prove_exclusive` | 90 | Body inspected: omitted completeness does not prove exclusive. |
| tests/usage-duration-analysis.py | `test_conflicting_identifiers_are_unknown_independent_of_order` | 90 | Body inspected: conflicting identifiers are unknown independent of order. |
| tests/usage-duration-analysis.py | `test_invalid_child_identity_does_not_claim_zero_work` | 90 | Body inspected: invalid child identity does not claim zero work. |
| tests/usage-duration-analysis.py | `test_explicit_complete_graph_proves_exclusive` | 20 | Same parent, children, explicit complete=True, exclusive result and coverage assertion are already covered by test_overlapping_children_have_distinct_sum_and_union; helper defaults complete=True. Removed; covering test passed. |
| tests/usage-duration-analysis.py | `test_unhashable_parent_identifiers_are_invalid_parentage` | 90 | Body inspected: unhashable parent identifiers are invalid parentage. |
| tests/usage-duration-analysis.py | `test_non_string_parentage_does_not_claim_zero_work` | 90 | Body inspected: non string parentage does not claim zero work. |
| tests/usage-duration-analysis.py | `test_diagnostics_are_stable_under_input_permutation` | 85 | Body inspected: diagnostics are stable under input permutation. |
| tests/usage-duration-analysis.py | `test_approximate_intervals_never_become_exact` | 90 | Body inspected: approximate intervals never become exact. |
| tests/usage-duration-analysis.py | `test_gaps_are_not_invented_as_waiting` | 75 | Body inspected: gaps are not invented as waiting. |
| tests/usage-duration-warnings.py | `test_two_hour_boundary_without_history` | 90 | Body inspected: two hour boundary without history. |
| tests/usage-duration-warnings.py | `test_four_samples_use_fallback` | 85 | Body inspected: four samples use fallback. |
| tests/usage-duration-warnings.py | `test_five_samples_require_both_strict_boundaries` | 90 | Body inspected: five samples require both strict boundaries. |
| tests/usage-duration-warnings.py | `test_candidate_is_excluded_before_sample_count` | 90 | Body inspected: candidate is excluded before sample count. |
| tests/usage-duration-warnings.py | `test_ineligible_samples_do_not_establish_history` | 90 | Body inspected: ineligible samples do not establish history. |
| tests/usage-duration-warnings.py | `test_candidate_only_cannot_supply_history` | 85 | Body inspected: candidate only cannot supply history. |
| tests/usage-duration-warnings.py | `test_expired_and_incompatible_exports_use_fallback` | 90 | Body inspected: expired and incompatible exports use fallback. |
| tests/usage-duration-warnings.py | `test_boolean_version_is_not_version_one` | 85 | Body inspected: boolean version is not version one. |
| tests/usage-duration-warnings.py | `test_missing_required_aggregates_use_fallback` | 90 | Body inspected: missing required aggregates use fallback. |
| tests/usage-duration-warnings.py | `test_forged_aggregate_values_use_fallback` | 90 | Body inspected: forged aggregate values use fallback. |
| tests/usage-duration-warnings.py | `test_excessively_long_median_uses_fallback` | 80 | Body inspected: excessively long median uses fallback. |
| tests/usage-duration-warnings.py | `test_aggregate_values_exclude_candidate_and_ineligible_records` | 90 | Body inspected: aggregate values exclude candidate and ineligible records. |
| tests/usage-duration-warnings.py | `test_malformed_or_future_evidence_uses_fallback` | 90 | Body inspected: malformed or future evidence uses fallback. |
| tests/usage-duration-warnings.py | `test_even_median_uses_two_central_values` | 85 | Body inspected: even median uses two central values. |
| tests/usage-duration-warnings.py | `test_collection_off_still_allows_time_only_warning` | 85 | Body inspected: collection off still allows time only warning. |
| tests/usage-duration-warnings.py | `test_missing_clock_and_unclosed_interval_are_unavailable` | 90 | Body inspected: missing clock and unclosed interval are unavailable. |
| tests/usage-duration-warnings.py | `test_approximate_warning_is_not_measured_anomaly` | 90 | Body inspected: approximate warning is not measured anomaly. |
| tests/usage-empty-retrospective.py | `test_empty_request_coverage_is_not_applicable_and_exportable` | 95 | Body inspected: empty request coverage is not applicable and exportable. |
| tests/usage-empty-retrospective.py | `test_zero_cost_requires_independent_empty_tool_scope` | 95 | Body inspected: zero cost requires independent empty tool scope. |
| tests/usage-entity-schemas.py | `test_complete_profile_preserves_verified_and_unknown_capabilities` | 90 | Body inspected: complete profile preserves verified and unknown capabilities. |
| tests/usage-entity-schemas.py | `test_required_fields_and_unknown_fields_are_rejected_without_exposure` | 95 | Body inspected: required fields and unknown fields are rejected without exposure. |
| tests/usage-entity-schemas.py | `test_versions_types_and_capabilities_are_checked` | 90 | Body inspected: versions types and capabilities are checked. |
| tests/usage-entity-schemas.py | `test_identifiers_and_nested_fields_are_bounded_and_closed` | 95 | Body inspected: identifiers and nested fields are bounded and closed. |
| tests/usage-entity-schemas.py | `test_canonical_and_input_byte_limits` | 85 | Body inspected: canonical and input byte limits. |
| tests/usage-entity-schemas.py | `test_counter_semantics_express_inclusion_and_cache_ttl` | 90 | Body inspected: counter semantics express inclusion and cache ttl. |
| tests/usage-entity-schemas.py | `test_profile_sets_have_stable_canonical_bytes` | 90 | Body inspected: profile sets have stable canonical bytes. |
| tests/usage-entity-schemas.py | `test_semantics_unknown_evidence_and_nested_boundaries` | 95 | Body inspected: semantics unknown evidence and nested boundaries. |
| tests/usage-exact-cost.py | `test_inclusive_cache_and_reasoning_are_not_counted_twice` | 95 | Body inspected: inclusive cache and reasoning are not counted twice. |
| tests/usage-exact-cost.py | `test_separate_cache_write_ttls` | 95 | Body inspected: separate cache write ttls. |
| tests/usage-exact-cost.py | `test_unknown_cache_write_period_is_unpriced_not_zero` | 95 | Body inspected: unknown cache write period is unpriced not zero. |
| tests/usage-exact-cost.py | `test_round_only_the_final_sum` | 95 | Body inspected: round only the final sum. |
| tests/usage-exact-cost.py | `test_half_even_display_and_exact_machine_value` | 95 | Body inspected: half even display and exact machine value. |
| tests/usage-exact-cost.py | `test_unsupported_repeating_unit_does_not_get_rounded` | 90 | Body inspected: unsupported repeating unit does not get rounded. |
| tests/usage-exact-cost.py | `test_large_derived_sum_stays_exact` | 90 | Body inspected: large derived sum stays exact. |
| tests/usage-exact-cost.py | `test_known_empty_model_inventory_still_counts_separate_tool` | 90 | Body inspected: known empty model inventory still counts separate tool. |
| tests/usage-exact-cost.py | `test_empty_unknown_inventory_never_produces_zero_cost` | 95 | Body inspected: empty unknown inventory never produces zero cost. |
| tests/usage-exact-cost.py | `test_proven_empty_billing_scope_is_exactly_zero` | 95 | Body inspected: proven empty billing scope is exactly zero. |
| tests/usage-exact-cost.py | `test_completeness_requires_each_coverage_condition` | 95 | Body inspected: completeness requires each coverage condition. |
| tests/usage-exact-cost.py | `test_conflict_overlap_unknown_sign_or_substitution_forbid_lower_bound` | 95 | Body inspected: conflict overlap unknown sign or substitution forbid lower bound. |
| tests/usage-exact-cost.py | `test_duplicate_contributor_is_not_summed_twice` | 95 | Body inspected: duplicate contributor is not summed twice. |
| tests/usage-exact-cost.py | `test_invalid_numbers_are_rejected` | 90 | Body inspected: invalid numbers are rejected. |
| tests/usage-exact-cost.py | `test_order_does_not_change_exact_total` | 90 | Body inspected: order does not change exact total. |
| tests/usage-exact-cost.py | `test_unpriced_reason_distinguishes_unsupported_unit_from_missing_rate` | 90 | Body inspected: unpriced reason distinguishes unsupported unit from missing rate. |
| tests/usage-exact-cost.py | `test_large_accepted_decimal_and_derived_result_have_no_digit_limit` | 85 | Body inspected: large accepted decimal and derived result have no digit limit. |
| tests/usage-exact-cost.py | `test_private_path_is_never_exported_as_a_contributor_id` | 95 | Body inspected: private path is never exported as a contributor id. |
| tests/usage-fixed-corpus.py | `test_fixed_corpus_contains_only_selected_hash_verified_data` | 95 | Body inspected: fixed corpus contains only selected hash verified data. |
| tests/usage-fixed-corpus.py | `test_selected_byte_tampering_and_invalid_json_fail_closed` | 95 | Body inspected: selected byte tampering and invalid json fail closed. |
| tests/usage-fixed-corpus.py | `test_verification_is_required_and_scope_is_not_a_boolean_claim` | 95 | Body inspected: verification is required and scope is not a boolean claim. |
| tests/usage-fixed-corpus.py | `test_late_observation_is_excluded_by_availability_not_source_time` | 95 | Body inspected: late observation is excluded by availability not source time. |
| tests/usage-fixed-corpus.py | `test_late_verified_input_is_excluded_even_with_early_source_time` | 95 | Body inspected: late verified input is excluded even with early source time. |
| tests/usage-fixed-corpus.py | `test_previous_corpus_is_reproducible_after_explicit_late_selection` | 90 | Body inspected: previous corpus is reproducible after explicit late selection. |
| tests/usage-fixed-corpus.py | `test_selection_order_is_semantically_stable_and_scenario_is_frozen` | 90 | Body inspected: selection order is semantically stable and scenario is frozen. |
| tests/usage-fixed-corpus.py | `test_size_record_and_permission_failures_never_emit_a_corpus` | 95 | Body inspected: size record and permission failures never emit a corpus. |
| tests/usage-fixed-corpus.py | `test_invalid_container_and_scope_are_rejected` | 90 | Body inspected: invalid container and scope are rejected. |
| tests/usage-fixed-corpus.py | `test_verified_decision_changes_are_bound_to_corpus_identity` | 90 | Body inspected: verified decision changes are bound to corpus identity. |
| tests/usage-fixed-corpus.py | `test_declared_exclusion_is_never_included` | 95 | Body inspected: declared exclusion is never included. |
| tests/usage-fixed-corpus.py | `test_late_observation_does_not_leave_associated_evidence` | 95 | Body inspected: late observation does not leave associated evidence. |
| tests/usage-fixed-corpus.py | `test_undated_nested_members_need_independent_first_seen_times` | 95 | Body inspected: undated nested members need independent first seen times. |
| tests/usage-fixed-corpus.py | `test_split_cache_measurement_retains_and_revalidates_evidence` | 90 | Body inspected: split cache measurement retains and revalidates evidence. |
| tests/usage-fixed-corpus.py | `test_derived_measurement_retains_transitive_operands` | 95 | Body inspected: derived measurement retains transitive operands. |
| tests/usage-frozen-context-evidence.py | `test_selected_timed_contexts_survive_and_resolve_real_usage` | 95 | Body inspected: selected timed contexts survive and resolve real usage. |
| tests/usage-frozen-context-evidence.py | `test_unverified_or_late_wrapper_never_becomes_context` | 95 | Body inspected: unverified or late wrapper never becomes context. |
| tests/usage-frozen-context-evidence.py | `test_late_nested_pricing_proof_is_removed_and_bundle_revalidated` | 95 | Body inspected: late nested pricing proof is removed and bundle revalidated. |
| tests/usage-frozen-context-evidence.py | `test_duplicate_context_evidence_set_permutation_is_equivalent` | 90 | Body inspected: duplicate context evidence set permutation is equivalent. |
| tests/usage-frozen-context-evidence.py | `test_untrusted_context_cannot_invent_known_usage` | 95 | Body inspected: untrusted context cannot invent known usage. |
| tests/usage-frozen-context-evidence.py | `test_context_without_its_selected_observation_is_rejected` | 95 | Body inspected: context without its selected observation is rejected. |
| tests/usage-frozen-pricing-inputs.py | `test_each_resolution_input_is_selected_validated_and_frozen` | 95 | Body inspected: each resolution input is selected validated and frozen. |
| tests/usage-frozen-pricing-inputs.py | `test_each_selected_file_is_bound_by_its_digest` | 95 | Body inspected: each selected file is bound by its digest. |
| tests/usage-frozen-pricing-inputs.py | `test_untrusted_selected_input_and_scope_fail_closed` | 95 | Body inspected: untrusted selected input and scope fail closed. |
| tests/usage-frozen-pricing-inputs.py | `test_changed_authority_decisions_change_frozen_identity` | 90 | Body inspected: changed authority decisions change frozen identity. |
| tests/usage-frozen-pricing-inputs.py | `test_late_context_is_excluded_without_rewriting_older_corpus` | 95 | Body inspected: late context is excluded without rewriting older corpus. |
| tests/usage-frozen-pricing-inputs.py | `test_unvalidated_extra_private_fields_are_rejected_even_with_matching_digest` | 95 | Body inspected: unvalidated extra private fields are rejected even with matching digest. |
| tests/usage-group-statistics.py | `test_four_values_produce_exact_even_median_and_nearest_rank_p90` | 85 | Body inspected: four values produce exact even median and nearest rank p90. |
| tests/usage-group-statistics.py | `test_empty_coverage_classes_are_explicitly_unavailable` | 85 | Body inspected: empty coverage classes are explicitly unavailable. |
| tests/usage-group-statistics.py | `test_partial_classes_never_enter_complete_distribution_or_each_other` | 90 | Body inspected: partial classes never enter complete distribution or each other. |
| tests/usage-group-statistics.py | `test_odd_ties_five_samples_and_nearest_rank_boundary` | 85 | Body inspected: odd ties five samples and nearest rank boundary. |
| tests/usage-group-statistics.py | `test_large_and_high_precision_values_remain_exact_decimal_strings` | 90 | Body inspected: large and high precision values remain exact decimal strings. |
| tests/usage-group-statistics.py | `test_permutations_do_not_change_results_and_inputs_are_not_mutated` | 85 | Body inspected: permutations do not change results and inputs are not mutated. |
| tests/usage-group-statistics.py | `test_rejects_invalid_noncanonical_or_inconsistent_values` | 90 | Body inspected: rejects invalid noncanonical or inconsistent values. |
| tests/usage-group-statistics.py | `test_record_limit_is_explicit_and_excess_is_rejected_not_truncated` | 90 | Body inspected: record limit is explicit and excess is rejected not truncated. |
| tests/usage-group-statistics.py | `test_forbidden_fields_and_invalid_values_do_not_echo_private_input` | 90 | Body inspected: forbidden fields and invalid values do not echo private input. |
| tests/usage-group-statistics.py | `test_statistics_perform_no_file_access` | 80 | Body inspected: statistics perform no file access. |
| tests/usage-inventory-completeness.py | `test_tokens_and_pricing_are_separate_coverage_measures` | 95 | Body inspected: tokens and pricing are separate coverage measures. |
| tests/usage-inventory-completeness.py | `test_missing_inventory_has_unknown_denominator` | 95 | Body inspected: missing inventory has unknown denominator. |
| tests/usage-inventory-completeness.py | `test_matching_evidence_hash_without_independent_provenance_is_not_a_denominator` | 95 | Body inspected: matching evidence hash without independent provenance is not a denominator. |
| tests/usage-inventory-completeness.py | `test_wrong_scope_or_evidence_cannot_be_verified` | 95 | Body inspected: wrong scope or evidence cannot be verified. |
| tests/usage-inventory-completeness.py | `test_individually_missing_measurements_are_independent` | 90 | Body inspected: individually missing measurements are independent. |
| tests/usage-inventory-completeness.py | `test_partial_inventory_and_unresolved_branch_have_unknown_denominator` | 95 | Body inspected: partial inventory and unresolved branch have unknown denominator. |
| tests/usage-inventory-completeness.py | `test_duplicate_response_is_not_counted_twice` | 95 | Body inspected: duplicate response is not counted twice. |
| tests/usage-inventory-completeness.py | `test_two_responses_for_one_call_are_two_slots` | 95 | Body inspected: two responses for one call are two slots. |
| tests/usage-inventory-completeness.py | `test_unexpected_response_does_not_produce_fraction_above_one` | 95 | Body inspected: unexpected response does not produce fraction above one. |
| tests/usage-inventory-completeness.py | `test_conflicting_duplicate_never_becomes_full_coverage` | 95 | Body inspected: conflicting duplicate never becomes full coverage. |
| tests/usage-inventory-completeness.py | `test_proven_empty_billable_scope_has_not_applicable_fraction` | 95 | Body inspected: proven empty billable scope has not applicable fraction. |
| tests/usage-inventory-completeness.py | `test_empty_model_inventory_is_not_proof_of_empty_tool_spending` | 95 | Body inspected: empty model inventory is not proof of empty tool spending. |
| tests/usage-inventory-completeness.py | `test_unknown_tool_coverage_cannot_prove_zero` | 95 | Body inspected: unknown tool coverage cannot prove zero. |
| tests/usage-inventory-completeness.py | `test_unknown_model_coverage_cannot_supply_response_denominator` | 95 | Body inspected: unknown model coverage cannot supply response denominator. |
| tests/usage-inventory-completeness.py | `test_unknown_model_coverage_cannot_establish_empty_scope` | 95 | Body inspected: unknown model coverage cannot establish empty scope. |
| tests/usage-inventory-completeness.py | `test_verified_model_coverage_keeps_denominator_with_unknown_tools` | 95 | Body inspected: verified model coverage keeps denominator with unknown tools. |
| tests/usage-inventory-completeness.py | `test_excluded_tools_cannot_prove_empty_billable_scope` | 95 | Body inspected: excluded tools cannot prove empty billable scope. |
| tests/usage-inventory-completeness.py | `test_unfinished_response_does_not_count_as_final` | 90 | Body inspected: unfinished response does not count as final. |
| tests/usage-inventory-schema.py | `test_known_responses_independent_calls_and_unresolved_slots_are_preserved` | 90 | Body inspected: known responses independent calls and unresolved slots are preserved. |
| tests/usage-inventory-schema.py | `test_required_fields_versions_and_private_payload` | 95 | Body inspected: required fields versions and private payload. |
| tests/usage-inventory-schema.py | `test_state_evidence_and_unresolved_slots_are_consistent` | 95 | Body inspected: state evidence and unresolved slots are consistent. |
| tests/usage-inventory-schema.py | `test_scope_window_coverage_and_links_are_closed` | 95 | Body inspected: scope window coverage and links are closed. |
| tests/usage-inventory-schema.py | `test_collection_and_json_bounds` | 90 | Body inspected: collection and json bounds; the real 10001-element arrays are replaced by a synthetic reported length, so large-array processing is no longer exercised. |
| tests/usage-inventory-schema.py | `test_bundle_integration_and_scope` | 90 | Body inspected: bundle integration and scope. |
| tests/usage-inventory-schema.py | `test_complete_inventory_requires_response_or_unresolved_call` | 90 | Body inspected: complete inventory requires response or unresolved call. |
| tests/usage-inventory-schema.py | `test_bundle_requires_linked_inventory_evidence` | 95 | Body inspected: bundle requires linked inventory evidence. |
| tests/usage-inventory-schema.py | `test_missing_inventory_evidence_never_proves_complete` | 95 | Body inspected: missing inventory evidence never proves complete. |
| tests/usage-legacy-recovery.py | `test_legacy_full_lifecycle_without_optional_dependencies` | 95 | Body inspected: legacy full lifecycle without optional dependencies. |
| tests/usage-legacy-recovery.py | `test_invalid_usage_calls_leave_all_lifecycle_bytes_intact` | 95 | Body inspected: invalid usage calls leave all lifecycle bytes intact. |
| tests/usage-legacy-recovery.py | `test_checkpoint_replay_preserves_original_lifecycle_bytes` | 95 | Body inspected: checkpoint replay preserves original lifecycle bytes. |
| tests/usage-legacy-recovery.py | `test_disable_and_resume_preserves_evidence_without_backfill` | 95 | Body inspected: disable and resume preserves evidence without backfill. |
| tests/usage-legacy-recovery.py | `test_signed_cli_disable_resume_replays_installed_bundle` | 95 | Body inspected: signed cli disable resume replays installed bundle. |
| tests/usage-legacy-recovery.py | `test_disable_resume_status_preserves_receipts_and_reports_segment_gap` | 90 | Body inspected: disable resume status preserves receipts and reports segment gap. |
| tests/usage-legacy-recovery.py | `test_permission_disk_and_sync_failures_do_not_create_false_receipts` | 95 | Body inspected: permission disk and sync failures do not create false receipts. |
| tests/usage-legacy-recovery.py | `test_directory_sync_failure_after_install_has_unknown_confirmation` | 95 | Body inspected: directory sync failure after install has unknown confirmation. |
| tests/usage-legacy-recovery.py | `test_kill_before_and_after_atomic_install_requires_exact_retry` | 95 | Body inspected: kill before and after atomic install requires exact retry. |
| tests/usage-lifecycle-authority.py | `test_independent_permit_accepts_only_exact_projection_and_scope` | 95 | Body inspected: independent permit accepts only exact projection and scope. |
| tests/usage-lifecycle-authority.py | `test_bundle_permit_domain_or_unsigned_declaration_cannot_authorize` | 95 | Body inspected: bundle permit domain or unsigned declaration cannot authorize. |
| tests/usage-lifecycle-projection-no-prices.py | `test_proven_empty_scope_needs_no_price_scenario` | 90 | Body inspected: proven empty scope needs no price scenario. |
| tests/usage-lifecycle-projection-no-prices.py | `test_fully_unpriced_work_needs_no_fabricated_snapshot` | 95 | Body inspected: fully unpriced work needs no fabricated snapshot. |
| tests/usage-lifecycle-projection-no-prices.py | `test_all_unpriced_work_cannot_claim_zero_priced_subtotal` | 90 | Body inspected: all unpriced work cannot claim zero priced subtotal. |
| tests/usage-lifecycle-projection-no-prices.py | `test_scenario_and_snapshots_must_be_consistent` | 85 | Body inspected: scenario and snapshots must be consistent. |
| tests/usage-lifecycle-projection-schema.py | `test_complete_projection_is_self_contained` | 90 | Body inspected: complete projection is self contained. |
| tests/usage-lifecycle-projection-schema.py | `test_evidenced_execution_time_controls_historical_price_period` | 95 | Body inspected: evidenced execution time controls historical price period. |
| tests/usage-lifecycle-projection-schema.py | `test_price_period_and_parameter_evidence_are_self_contained_and_match` | 95 | Body inspected: price period and parameter evidence are self contained and match. |
| tests/usage-lifecycle-projection-schema.py | `test_parameter_evidence_must_belong_to_contributor_source_and_profile` | 95 | Body inspected: parameter evidence must belong to contributor source and profile. |
| tests/usage-lifecycle-projection-schema.py | `test_distinct_contributors_cannot_reuse_one_source_record` | 95 | Body inspected: distinct contributors cannot reuse one source record. |
| tests/usage-lifecycle-projection-schema.py | `test_observation_cannot_precede_execution` | 90 | Body inspected: observation cannot precede execution. |
| tests/usage-lifecycle-projection-schema.py | `test_unknown_pricing_cannot_prove_a_lower_bound` | 95 | Body inspected: unknown pricing cannot prove a lower bound. |
| tests/usage-lifecycle-projection-schema.py | `test_uncertain_attribution_or_measurements_cannot_prove_lower_bound` | 95 | Body inspected: uncertain attribution or measurements cannot prove lower bound. |
| tests/usage-lifecycle-projection-schema.py | `test_lower_bound_requires_verified_scope_attribution` | 95 | Body inspected: lower bound requires verified scope attribution. |
| tests/usage-lifecycle-projection-schema.py | `test_invalid_lower_bound_scenario_fails_safely` | 95 | Body inspected: invalid lower bound scenario fails safely. |
| tests/usage-lifecycle-projection-schema.py | `test_reprice_assumptions_must_match_price_applicability` | 90 | Body inspected: reprice assumptions must match price applicability. |
| tests/usage-lifecycle-projection-schema.py | `test_parameter_evidence_is_scoped_to_each_contributor_record` | 95 | Body inspected: parameter evidence is scoped to each contributor record. |
| tests/usage-lifecycle-projection-schema.py | `test_display_amount_is_correct_half_even_rounding` | 90 | Body inspected: display amount is correct half even rounding. |
| tests/usage-lifecycle-projection-schema.py | `test_unresolved_identity_cannot_establish_a_lower_bound` | 95 | Body inspected: unresolved identity cannot establish a lower bound. |
| tests/usage-lifecycle-projection-schema.py | `test_nonterminating_unit_rate_is_unpriced_even_when_quantity_cancels` | 95 | Body inspected: nonterminating unit rate is unpriced even when quantity cancels. |
| tests/usage-lifecycle-projection-schema.py | `test_partial_projection_preserves_explicit_unknowns_without_full_cost` | 95 | Body inspected: partial projection preserves explicit unknowns without full cost. |
| tests/usage-lifecycle-projection-schema.py | `test_required_fields_closed_shape_and_decimal_format` | 95 | Body inspected: required fields closed shape and decimal format. |
| tests/usage-lifecycle-projection-schema.py | `test_contributors_evidence_and_exact_total_must_agree` | 95 | Body inspected: contributors evidence and exact total must agree. |
| tests/usage-lifecycle-projection-schema.py | `test_price_definitions_and_scenario_must_match_hashes` | 95 | Body inspected: price definitions and scenario must match hashes. |
| tests/usage-lifecycle-projection-schema.py | `test_historical_component_requires_one_applicable_snapshot` | 95 | Body inspected: historical component requires one applicable snapshot. |
| tests/usage-lifecycle-projection-schema.py | `test_complete_cost_requires_known_multiplier_applicability` | 95 | Body inspected: complete cost requires known multiplier applicability. |
| tests/usage-lifecycle-projection-schema.py | `test_private_fields_are_rejected_without_echo` | 95 | Body inspected: private fields are rejected without echo. |
| tests/usage-lifecycle-projection-schema.py | `test_canonical_order_and_identity_are_stable` | 90 | Body inspected: canonical order and identity are stable. |
| tests/usage-lifecycle-projection-schema.py | `test_raw_canonical_limits_duplicate_keys_and_count_bounds` | 90 | Body inspected: raw canonical limits duplicate keys and count bounds.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-lifecycle-projection-states.py | `test_verified_empty_inventory_is_self_contained_and_zero` | 95 | Body inspected: verified empty inventory is self contained and zero. |
| tests/usage-lifecycle-projection-states.py | `test_unpriced_response_and_known_subtotal_remain_partial` | 95 | Body inspected: unpriced response and known subtotal remain partial. |
| tests/usage-lifecycle-projection-states.py | `test_ttl_split_write_uses_matching_independent_evidence_and_rate` | 95 | Body inspected: ttl split write uses matching independent evidence and rate. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_split_writes_must_be_included_in_input_scalar` | 95 | Body inspected: split writes must be included in input scalar. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_unsplit_write_counts_as_tokens_even_when_pricing_unknown` | 95 | Body inspected: unsplit write counts as tokens even when pricing unknown. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_nonempty_scope_cannot_claim_inventory_not_applicable` | 95 | Body inspected: nonempty scope cannot claim inventory not applicable. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_nonempty_dimensions_cannot_claim_not_applicable` | 95 | Body inspected: nonempty dimensions cannot claim not applicable. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_not_applicable_is_allowed_for_proven_empty_scope` | 20 | The same fixture and assertion are contained in test_verified_empty_inventory_is_self_contained_and_zero, which also tests invalid variants. Removed; covering test passed. |
| tests/usage-lifecycle-projection-token-scalars.py | `test_split_and_unsplit_same_counter_cannot_be_double_counted` | 95 | Body inspected: split and unsplit same counter cannot be double counted. |
| tests/usage-lifecycle-projection-trust.py | `test_exact_projection_is_checked_before_authorization` | 95 | Body inspected: exact projection is checked before authorization. |
| tests/usage-lifecycle-projection-trust.py | `test_untrusted_evidence_or_scope_and_mismatched_amount_are_rejected` | 95 | Body inspected: untrusted evidence or scope and mismatched amount are rejected. |
| tests/usage-lifecycle-projection-trust.py | `test_verifier_cannot_change_projection_or_owner_and_exceptions_are_sanitized` | 95 | Body inspected: verifier cannot change projection or owner and exceptions are sanitized. |
| tests/usage-lifecycle-projection.py | `test_published_observations_match_first_projection_and_replay` | 95 | Body inspected: published observations match first projection and replay. |
| tests/usage-lifecycle-projection.py | `test_explicit_dash_cost_rejects_without_receipt_or_state_change` | 95 | Body inspected: explicit dash cost rejects without receipt or state change. |
| tests/usage-lifecycle-projection.py | `test_omitted_cost_accepts_projection_and_replay` | 95 | Body inspected: omitted cost accepts projection and replay. |
| tests/usage-lifecycle-projection.py | `test_valid_exact_projection_and_replay_preserve_first_payload` | 95 | Body inspected: valid exact projection and replay preserve first payload. |
| tests/usage-lifecycle-projection.py | `test_signed_foreign_owner_and_unbound_session_cannot_mutate_checkpoint` | 95 | Body inspected: signed foreign owner and unbound session cannot mutate checkpoint. |
| tests/usage-lifecycle-projection.py | `test_registered_project_and_key_must_still_match_current_run` | 95 | Body inspected: registered project and key must still match current run. |
| tests/usage-lifecycle-projection.py | `test_untrusted_complete_projection_cannot_mutate_state` | 95 | Body inspected: untrusted complete projection cannot mutate state. |
| tests/usage-lifecycle-projection.py | `test_invalid_projection_or_scalar_never_mutates_any_state` | 95 | Body inspected: invalid projection or scalar never mutates any state. |
| tests/usage-lifecycle-projection.py | `test_caller_counters_are_recorded_without_verified_cost` | 90 | Body inspected: caller counters are recorded without verified cost. |
| tests/usage-lifecycle-projection.py | `test_unavailable_dependency_preserves_legacy_logging` | 95 | Body inspected: unavailable dependency preserves legacy logging. |

## Duplicates and coverage limits

- Structural comparison of method bodies found one identical pair spanning this group: `usage-authority-permit.py::test_user_owned_anchor_fails_closed_at_real_cli` and `usage-publication-provenance.py::test_genuine_normalization_requires_independent_authority`. Their setup differs: independently registered user-owned key versus missing independent authority. They are not proven duplicates and should not be removed on body identity alone.
- `usage-lifecycle-projection-token-scalars.py::test_not_applicable_is_allowed_for_proven_empty_scope` scores 20: the identical empty projection and assertion are covered by `usage-lifecycle-projection-states.py::test_verified_empty_inventory_is_self_contained_and_zero`.
- `usage-duration-analysis.py::test_explicit_complete_graph_proves_exclusive` scores 20: its same inputs and assertions are a strict subset of `test_overlapping_children_have_distinct_sum_and_union` because the helper defaults to `complete=True`. Removed; the covering test passed after removal. No covered behavior is lost. Unreviewed methods must not be inferred to have passed the audit.
- Shortened record-size boundary checks use a patched small constant and do not exercise physical 16 MiB records.

Inventoried and inspected all 365 original methods; two exact duplicates have since been removed.
