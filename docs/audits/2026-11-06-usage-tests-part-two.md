# Usage test audit: second alphabetical group

A dash means the method was inventoried but its body has not been reviewed; it is not a score of zero.

| File | Method | Score | Evidence and rationale |
|---|---|---:|---|
| tests/usage-multibundle-report.py | `test_two_explicit_partial_bundles_preserve_full_inventory` | 95 | Body inspected: two explicit partial bundles preserve full inventory. |
| tests/usage-multibundle-report.py | `test_duplicate_selected_bundle_does_not_double_count` | 95 | Body inspected: duplicate selected bundle does not double count. |
| tests/usage-multibundle-report.py | `test_two_profiles_combine_only_with_independent_inventory_union` | 95 | Body inspected: two profiles combine only with independent inventory union. |
| tests/usage-multibundle-report.py | `test_cross_profile_same_responses_are_deduplicated_once` | 95 | Body inspected: cross profile same responses are deduplicated once. |
| tests/usage-multibundle-report.py | `test_conflicting_cross_profile_response_is_not_summed_or_selected` | 95 | Body inspected: conflicting cross profile response is not summed or selected. |
| tests/usage-multibundle-report.py | `test_same_response_ids_from_different_providers_are_not_silently_unified` | 95 | Body inspected: same response ids from different providers are not silently unified. |
| tests/usage-multibundle-report.py | `test_missing_selected_profile_does_not_claim_complete_measurements` | 95 | Body inspected: missing selected profile does not claim complete measurements. |
| tests/usage-multibundle-report.py | `test_untrusted_inventory_union_does_not_invent_a_denominator` | 95 | Body inspected: untrusted inventory union does not invent a denominator. |
| tests/usage-normalize-cli.py | `test_nonblocking_pipe_never_reports_success_for_truncated_bundle` | 95 | Body inspected: nonblocking pipe never reports success for truncated bundle. |
| tests/usage-normalize-cli.py | `test_buffered_nonblocking_pipe_reports_sanitized_failure` | 95 | Body inspected: buffered nonblocking pipe reports sanitized failure. |
| tests/usage-normalize-cli.py | `test_all_output_commands_handle_short_and_no_progress_writes` | 95 | Body inspected: all output commands handle short and no progress writes. |
| tests/usage-normalize-cli.py | `test_normalize_emits_self_contained_sanitized_bundle` | 95 | Body inspected: normalize emits self contained sanitized bundle. |
| tests/usage-normalize-cli.py | `test_bad_record_quarantined_in_partial_bundle` | 95 | Body inspected: bad record quarantined in partial bundle. |
| tests/usage-normalize-cli.py | `test_invalid_selection_and_untrusted_profiles_fail_without_result` | 95 | Body inspected: invalid selection and untrusted profiles fail without result. |
| tests/usage-normalize-cli.py | `test_invalid_config_permissions_or_missing_config_fail_without_result` | 95 | Body inspected: invalid config permissions or missing config fail without result. |
| tests/usage-normalize-cli.py | `test_symlinked_config_is_rejected` | 95 | Body inspected: symlinked config is rejected. |
| tests/usage-normalize-cli.py | `test_invalid_run_identifiers_never_produce_output_or_disclose_values` | 95 | Body inspected: invalid run identifiers never produce output or disclose values. |
| tests/usage-normalize-cli.py | `test_changed_source_and_invalid_manifest_do_not_replace_output` | 95 | Body inspected: changed source and invalid manifest do not replace output. |
| tests/usage-normalize-cli.py | `test_file_destination_argument_is_rejected_without_writes` | 95 | Body inspected: file destination argument is rejected without writes. |
| tests/usage-normalize-cli.py | `test_regular_file_stdout_is_rejected_without_writes` | 95 | Body inspected: regular file stdout is rejected without writes. |
| tests/usage-normalize-cli.py | `test_socket_stdout_emits_valid_bundle` | 95 | Body inspected: socket stdout emits valid bundle. |
| tests/usage-normalize-cli.py | `test_closed_pipe_returns_failure_with_sanitized_diagnostics` | 95 | Body inspected: closed pipe returns failure with sanitized diagnostics. |
| tests/usage-normalize-cli.py | `test_destination_moved_after_final_check_never_publishes_to_shared_store` | 95 | Body inspected: destination moved after final check never publishes to shared store. |
| tests/usage-normalize-cli.py | `test_unreviewed_profile_strings_never_appear_in_output` | 95 | Body inspected: unreviewed profile strings never appear in output. |
| tests/usage-observation-bundle-schema.py | `test_observation_and_bundle_accept_and_preserve_identities` | 90 | Body inspected: observation and bundle accept and preserve identities. |
| tests/usage-observation-bundle-schema.py | `test_invalid_versions_and_raw_fields_are_rejected_without_leakage` | 90 | Body inspected: invalid versions and raw fields are rejected without leakage. |
| tests/usage-observation-bundle-schema.py | `test_observation_requires_explicit_metadata` | 90 | Body inspected: observation requires explicit metadata. |
| tests/usage-observation-bundle-schema.py | `test_counter_scope_is_explicit_and_recognized` | 90 | Body inspected: counter scope is explicit and recognized. |
| tests/usage-observation-bundle-schema.py | `test_identifier_character_limit` | 90 | Body inspected: identifier character limit. |
| tests/usage-observation-bundle-schema.py | `test_opaque_identifiers_reject_paths_and_free_text` | 90 | Body inspected: opaque identifiers reject paths and free text. |
| tests/usage-observation-bundle-schema.py | `test_other_identifiers_reject_paths_and_free_text` | 90 | Body inspected: other identifiers reject paths and free text. |
| tests/usage-observation-bundle-schema.py | `test_timestamps_are_not_opaque_identifiers` | 20 | Identical positive fixture and assertion appear at start of test_invalid_timestamps_are_rejected_without_exposure. Removed; covering test passed. |
| tests/usage-observation-bundle-schema.py | `test_invalid_timestamps_are_rejected_without_exposure` | 90 | Body inspected: invalid timestamps are rejected without exposure. |
| tests/usage-observation-bundle-schema.py | `test_candidate_set_is_canonical` | 90 | Body inspected: candidate set is canonical. |
| tests/usage-observation-bundle-schema.py | `test_bundle_sets_are_canonical_and_sequences_remain_ordered` | 90 | Body inspected: bundle sets are canonical and sequences remain ordered. |
| tests/usage-observation-bundle-schema.py | `test_schema_set_order_cannot_be_overridden` | 90 | Body inspected: schema set order cannot be overridden. |
| tests/usage-observation-bundle-schema.py | `test_bundle_rejects_duplicate_set_members` | 90 | Body inspected: bundle rejects duplicate set members. |
| tests/usage-observation-bundle-schema.py | `test_evidence_profile_record_and_bundle_scope_are_checked` | 90 | Body inspected: evidence profile record and bundle scope are checked. |
| tests/usage-observation-bundle-schema.py | `test_exact_canonical_bundle_limit_and_multibyte_input` | 90 | Body inspected: exact canonical bundle limit and multibyte input. |
| tests/usage-observation-bundle-schema.py | `test_canonical_observation_limit_gate` | 90 | Body inspected: canonical observation limit gate. |
| tests/usage-observation-bundle-schema.py | `test_bundle_json_input_byte_limit` | 90 | Body inspected: bundle json input byte limit. |
| tests/usage-observation-bundle-schema.py | `test_bundle_observation_count_limit` | 90 | Body inspected: bundle observation count limit. |
| tests/usage-observation-bundle-schema.py | `test_bundle_canonical_byte_limit` | 90 | Body inspected: bundle canonical byte limit. |
| tests/usage-observation-bundle-schema.py | `test_evidence_association_requires_matching_separate_object` | 90 | Body inspected: evidence association requires matching separate object. |
| tests/usage-observation-bundle-schema.py | `test_rejects_missing_measurements_and_malformed_hash` | 90 | Body inspected: rejects missing measurements and malformed hash. |
| tests/usage-observation-bundle-schema.py | `test_rejects_duplicate_json_keys_before_validation` | 90 | Body inspected: rejects duplicate json keys before validation. |
| tests/usage-offline-acceptance.py | `test_selected_source_to_frozen_exports` | 85 | Body inspected: selected source to frozen exports; broad end-to-end scenario has a long implementation. |
| tests/usage-offline-acceptance.py | `test_complete_resolved_price_is_accepted_as_lifecycle_projection` | 85 | Body inspected: complete resolved price is accepted as lifecycle projection; broad end-to-end scenario has a long implementation. |
| tests/usage-outcome-tool-cost.py | `test_verified_tool_expense_is_included_once_in_observed_workload` | 95 | Body inspected: verified tool expense is included once in observed workload. |
| tests/usage-outcome-tool-cost.py | `test_verified_empty_inventory_preserves_long_exact_ratio` | 95 | Body inspected: verified empty inventory preserves long exact ratio. |
| tests/usage-outcome-tool-cost.py | `test_unverified_tool_inventory_does_not_claim_complete_total` | 95 | Body inspected: unverified tool inventory does not claim complete total. |
| tests/usage-outcome-tool-cost.py | `test_unknown_experimental_scope_does_not_claim_tool_as_workload` | 95 | Body inspected: unknown experimental scope does not claim tool as workload. |
| tests/usage-outcome-tool-cost.py | `test_tool_requires_its_own_experimental_exclusion_proof` | 95 | Body inspected: tool requires its own experimental exclusion proof. |
| tests/usage-outcome-tool-cost.py | `test_missing_tool_scope_does_not_prove_zero_experimental_cost` | 95 | Body inspected: missing tool scope does not prove zero experimental cost. |
| tests/usage-outcome-tool-cost.py | `test_tool_with_late_nested_evidence_is_excluded_from_fixed_corpus` | 95 | Body inspected: tool with late nested evidence is excluded from fixed corpus. |
| tests/usage-outcome-tool-cost.py | `test_model_only_leaf_costs_do_not_hide_selected_tool_expenses` | 95 | Body inspected: model only leaf costs do not hide selected tool expenses. |
| tests/usage-outcome-unattributed-workload.py | `test_unattributed_priced_response_cannot_disappear_from_complete_workload` | 95 | Body inspected: unattributed priced response cannot disappear from complete workload. |
| tests/usage-ownership-empty-scope.py | `test_verified_empty_model_scope_is_zero_even_when_tools_are_unknown` | 95 | Body inspected: verified empty model scope is zero even when tools are unknown. |
| tests/usage-ownership-empty-scope.py | `test_unverified_owner_or_model_inventory_cannot_prove_zero` | 95 | Body inspected: unverified owner or model inventory cannot prove zero. |
| tests/usage-price-applicability.py | `test_historical_applicability_requires_scoped_evidence` | 95 | Body inspected: historical applicability requires scoped evidence. |
| tests/usage-price-applicability.py | `test_period_bounds_and_unknown_historical_period` | 95 | Body inspected: period bounds and unknown historical period. |
| tests/usage-price-applicability.py | `test_missing_or_mismatched_pricing_dimensions_are_unknown` | 95 | Body inspected: missing or mismatched pricing dimensions are unknown. |
| tests/usage-price-applicability.py | `test_alias_needs_independent_mapping_and_trusted_evidence` | 95 | Body inspected: alias needs independent mapping and trusted evidence. |
| tests/usage-price-applicability.py | `test_multiplier_requires_explicit_known_applicability` | 95 | Body inspected: multiplier requires explicit known applicability. |
| tests/usage-price-applicability.py | `test_threshold_is_per_request_strictly_greater` | 95 | Body inspected: threshold is per request strictly greater. |
| tests/usage-price-applicability.py | `test_ttl_tool_identity_and_units_must_match` | 95 | Body inspected: ttl tool identity and units must match. |
| tests/usage-price-applicability.py | `test_conflicting_overlaps_and_possible_unknown_are_never_first_match` | 95 | Body inspected: conflicting overlaps and possible unknown are never first match. |
| tests/usage-price-applicability.py | `test_reprice_is_conditional_and_assumes_only_explicit_dimensions` | 95 | Body inspected: reprice is conditional and assumes only explicit dimensions. |
| tests/usage-price-applicability.py | `test_period_evidence_does_not_attest_a_different_snapshot` | 95 | Body inspected: period evidence does not attest a different snapshot. |
| tests/usage-price-applicability.py | `test_cache_and_tool_identifiers_need_record_scoped_evidence` | 95 | Body inspected: cache and tool identifiers need record scoped evidence. |
| tests/usage-price-applicability.py | `test_multiplier_requires_scoped_positive_or_negative_applicability_evidence` | 95 | Body inspected: multiplier requires scoped positive or negative applicability evidence. |
| tests/usage-price-applicability.py | `test_untrusted_competing_period_is_potential_overlap` | 95 | Body inspected: untrusted competing period is potential overlap. |
| tests/usage-price-evidence-schema.py | `test_pricing_attestations_are_accepted_by_shared_schema` | 90 | Body inspected: pricing attestations are accepted by shared schema. |
| tests/usage-price-evidence-schema.py | `test_multiplier_attestation_is_closed_and_record_scoped` | 90 | Body inspected: multiplier attestation is closed and record scoped. |
| tests/usage-price-snapshot-schema.py | `test_complete_snapshot_preserves_declared_parameters` | 90 | Body inspected: complete snapshot preserves declared parameters. |
| tests/usage-price-snapshot-schema.py | `test_unknown_period_and_explicit_unknown_applicability` | 90 | Body inspected: unknown period and explicit unknown applicability. |
| tests/usage-price-snapshot-schema.py | `test_malformed_rates_and_required_fields_fail` | 90 | Body inspected: malformed rates and required fields fail. |
| tests/usage-price-snapshot-schema.py | `test_effective_period_timestamps_and_verified_aliases` | 90 | Body inspected: effective period timestamps and verified aliases. |
| tests/usage-price-snapshot-schema.py | `test_namespaced_model_and_alias_identifiers` | 90 | Body inspected: namespaced model and alias identifiers. |
| tests/usage-price-snapshot-schema.py | `test_rate_units_cache_and_thresholds_are_typed` | 90 | Body inspected: rate units cache and thresholds are typed. |
| tests/usage-price-snapshot-schema.py | `test_tool_rates_preserve_separate_tool_identities` | 90 | Body inspected: tool rates preserve separate tool identities. |
| tests/usage-price-snapshot-schema.py | `test_multiplier_applicability_is_explicit_and_exact` | 90 | Body inspected: multiplier applicability is explicit and exact. |
| tests/usage-price-snapshot-schema.py | `test_forbidden_fields_and_source_urls_do_not_leak` | 90 | Body inspected: forbidden fields and source urls do not leak. |
| tests/usage-price-snapshot-schema.py | `test_identity_and_set_order` | 90 | Body inspected: identity and set order. |
| tests/usage-price-snapshot-schema.py | `test_raw_and_canonical_byte_limits_and_duplicate_keys` | 90 | Body inspected: raw and canonical byte limits and duplicate keys. |
| tests/usage-pricing-scenario-schema.py | `test_named_scenarios_and_explicit_unknowns` | 90 | Body inspected: named scenarios and explicit unknowns. |
| tests/usage-pricing-scenario-schema.py | `test_version_identity_currency_basis_and_precision_are_strict` | 90 | Body inspected: version identity currency basis and precision are strict. |
| tests/usage-pricing-scenario-schema.py | `test_reprice_assumptions_are_explicit_and_cannot_replace_work` | 90 | Body inspected: reprice assumptions are explicit and cannot replace work. |
| tests/usage-pricing-scenario-schema.py | `test_source_parameters_require_evidence_or_explicit_unknown` | 90 | Body inspected: source parameters require evidence or explicit unknown. |
| tests/usage-pricing-scenario-schema.py | `test_snapshot_references_and_threshold_rules_are_typed` | 90 | Body inspected: snapshot references and threshold rules are typed. |
| tests/usage-pricing-scenario-schema.py | `test_forbidden_fields_do_not_leak` | 90 | Body inspected: forbidden fields do not leak. |
| tests/usage-pricing-scenario-schema.py | `test_identity_uses_schema_sets_and_is_sensitive_to_semantics` | 90 | Body inspected: identity uses schema sets and is sensitive to semantics. |
| tests/usage-pricing-scenario-schema.py | `test_json_limits_duplicates_and_bounded_tree` | 90 | Body inspected: json limits duplicates and bounded tree. |
| tests/usage-producer-epochs-bundle.py | `test_exact_producer_bundle_resolves_its_own_authorized_interval` | 95 | Body inspected: exact producer bundle resolves its own authorized interval. |
| tests/usage-producer-epochs-bundle.py | `test_foreign_or_modified_interval_is_not_authorized_by_another_bundle` | 95 | Body inspected: foreign or modified interval is not authorized by another bundle. |
| tests/usage-producer-epochs-cli.py | `test_real_cli_with_signed_exact_decisions_emits_resolvable_own_bundle` | 95 | Body inspected: real cli with signed exact decisions emits resolvable own bundle. |
| tests/usage-producer-epochs-cli.py | `test_default_log_root_fails_closed_without_registration` | 95 | Body inspected: default log root fails closed without registration. |
| tests/usage-producer-epochs-cli.py | `test_different_root_authority_key_cannot_replace_registered_key` | 95 | Body inspected: different root authority key cannot replace registered key. |
| tests/usage-producer-epochs-cli.py | `test_missing_forged_or_wrong_scope_permit_never_authorizes` | 95 | Body inspected: missing forged or wrong scope permit never authorizes. |
| tests/usage-producer-epochs.py | `test_explicit_source_epochs_survive_bundle_and_resolve_without_double_count` | 95 | Body inspected: explicit source epochs survive bundle and resolve without double count. |
| tests/usage-producer-epochs.py | `test_reset_or_gap_does_not_invent_interval_usage` | 95 | Body inspected: reset or gap does not invent interval usage. |
| tests/usage-producer-epochs.py | `test_epoch_provenance_alone_does_not_authorize_private_model_disclosure` | 95 | Body inspected: epoch provenance alone does not authorize private model disclosure. |
| tests/usage-producer-epochs.py | `test_unverified_source_or_resolver_evidence_remains_unknown` | 95 | Body inspected: unverified source or resolver evidence remains unknown. |
| tests/usage-producer-measurement-finality.py | `test_authorized_exact_measurements_become_final_before_context_binding` | 95 | Body inspected: authorized exact measurements become final before context binding. |
| tests/usage-producer-measurement-finality.py | `test_denied_measurement_remains_partial_despite_final_event` | 95 | Body inspected: denied measurement remains partial despite final event. |
| tests/usage-producer-resolution.py | `test_verified_profile_produces_sanitized_bound_context_usable_by_resolver` | 95 | Body inspected: verified profile produces sanitized bound context usable by resolver. |
| tests/usage-producer-resolution.py | `test_missing_or_unknown_profile_semantics_never_guess_context_or_identity` | 95 | Body inspected: missing or unknown profile semantics never guess context or identity. |
| tests/usage-producer-resolution.py | `test_finality_and_missing_required_source_data_never_become_final_by_guessing` | 95 | Body inspected: finality and missing required source data never become final by guessing. |
| tests/usage-producer-resolution.py | `test_any_unknown_pricing_dimension_preserves_independent_tokens` | 95 | Body inspected: any unknown pricing dimension preserves independent tokens. |
| tests/usage-producer-resolution.py | `test_unknown_execution_time_does_not_hide_tokens_or_assume_a_price` | 95 | Body inspected: unknown execution time does not hide tokens or assume a price. |
| tests/usage-producer-resolution.py | `test_unverified_context_and_secret_parameter_are_never_published` | 95 | Body inspected: unverified context and secret parameter are never published. |
| tests/usage-producer-resolution.py | `test_nonboolean_verification_claims_do_not_authorize_publication` | 95 | Body inspected: nonboolean verification claims do not authorize publication. |
| tests/usage-producer-resolution.py | `test_source_mapping_is_closed_bounded_and_rejects_unverified_guesses` | 95 | Body inspected: source mapping is closed bounded and rejects unverified guesses. |
| tests/usage-producer-streams.py | `test_delta_stream_producer_retains_scoped_evidence_for_resolver` | 95 | Body inspected: delta stream producer retains scoped evidence for resolver. |
| tests/usage-producer-streams.py | `test_producer_explicit_record_correction_requires_separate_revision_authority` | 95 | Body inspected: producer explicit record correction requires separate revision authority. |
| tests/usage-producer-streams.py | `test_unknown_event_mapping_does_not_assume_snapshot_or_finality` | 95 | Body inspected: unknown event mapping does not assume snapshot or finality. |
| tests/usage-publication-cli.py | `test_authorized_bundle_is_visible_before_receipt_and_exact_repeat` | 95 | Body inspected: authorized bundle is visible before receipt and exact repeat. |
| tests/usage-publication-cli.py | `test_disabled_invalid_and_unregistered_scope_do_not_publish` | 95 | Body inspected: disabled invalid and unregistered scope do not publish. |
| tests/usage-publication-cli.py | `test_unsigned_forged_or_changed_bundle_is_rejected` | 95 | Body inspected: unsigned forged or changed bundle is rejected. |
| tests/usage-publication-cli.py | `test_signed_bundle_without_registered_lifecycle_run_is_rejected` | 95 | Body inspected: signed bundle without registered lifecycle run is rejected. |
| tests/usage-publication-cli.py | `test_invalid_private_registration_and_profile_cannot_authorize` | 95 | Body inspected: invalid private registration and profile cannot authorize. |
| tests/usage-publication-cli.py | `test_normalizer_produces_verifiable_private_provenance` | 95 | Body inspected: normalizer produces verifiable private provenance. |
| tests/usage-publication-cli.py | `test_provenance_regular_file_descriptor_is_rejected_without_output` | 95 | Body inspected: provenance regular file descriptor is rejected without output. |
| tests/usage-publication-cli.py | `test_closed_provenance_pipe_fails_without_bundle` | 95 | Body inspected: closed provenance pipe fails without bundle. |
| tests/usage-publication-cli.py | `test_concurrent_publications_create_one_file_and_valid_receipts` | 95 | Body inspected: concurrent publications create one file and valid receipts. |
| tests/usage-publication-cli.py | `test_corrupt_or_symlink_address_and_parent_never_return_receipt` | 95 | Body inspected: corrupt or symlink address and parent never return receipt. |
| tests/usage-publication-cli.py | `test_missing_python_fails_closed_and_lifecycle_logging_remains_usable` | 95 | Body inspected: missing python fails closed and lifecycle logging remains usable. |
| tests/usage-publication-close-nonblocking.py | `test_run_closed_during_install_has_no_receipt_or_lifecycle_mutation` | 95 | Body inspected: run closed during install has no receipt or lifecycle mutation. |
| tests/usage-publication-close-nonblocking.py | `test_paused_install_never_delays_close_or_returns_stale_receipt` | 95 | Body inspected: paused install never delays close or returns stale receipt. |
| tests/usage-publication-late-import.py | `test_explicit_authorized_late_import_is_new_artifact_only` | 95 | Body inspected: explicit authorized late import is new artifact only. |
| tests/usage-publication-late-import.py | `test_late_import_does_not_open_lifecycle_registration_or_history` | 95 | Body inspected: late import does not open lifecycle registration or history. |
| tests/usage-publication-late-import.py | `test_same_key_in_both_registries_cannot_self_certify_registration` | 95 | Body inspected: same key in both registries cannot self certify registration. |
| tests/usage-publication-late-import.py | `test_rewrapped_same_rsa_key_cannot_self_certify_registration` | 95 | Body inspected: rewrapped same rsa key cannot self certify registration. |
| tests/usage-publication-late-import.py | `test_real_registration_key_loader_rejects_caller_owned_key` | 95 | Body inspected: real registration key loader rejects caller owned key. |
| tests/usage-publication-late-import.py | `test_real_cli_requires_explicit_late_certificate` | 95 | Body inspected: real cli requires explicit late certificate. |
| tests/usage-publication-late-import.py | `test_run_authority_cannot_self_certify_its_own_registration` | 95 | Body inspected: run authority cannot self certify its own registration. |
| tests/usage-publication-late-import.py | `test_unsigned_wrong_scope_key_or_bundle_cannot_import_late` | 95 | Body inspected: unsigned wrong scope key or bundle cannot import late. |
| tests/usage-publication-provenance.py | `test_forged_project_with_valid_mac` | 95 | Body inspected: forged project with valid mac. |
| tests/usage-publication-provenance.py | `test_forged_source_with_valid_mac` | 95 | Body inspected: forged source with valid mac. |
| tests/usage-publication-provenance.py | `test_forged_provider_with_valid_mac` | 95 | Body inspected: forged provider with valid mac. |
| tests/usage-publication-provenance.py | `test_forged_measurement_and_consistent_evidence_with_valid_mac` | 95 | Body inspected: forged measurement and consistent evidence with valid mac. |
| tests/usage-publication-provenance.py | `test_forged_evidence_path_with_valid_mac` | 95 | Body inspected: forged evidence path with valid mac. |
| tests/usage-publication-provenance.py | `test_genuine_normalization_requires_independent_authority` | 95 | Body inspected: genuine normalization requires independent authority. |
| tests/usage-publication-run-race.py | `test_contended_lifecycle_lock_fails_closed_without_waiting` | 95 | Body inspected: contended lifecycle lock fails closed without waiting. |
| tests/usage-publication-run-race.py | `test_registration_cannot_go_stale_before_publication` | 95 | Body inspected: registration cannot go stale before publication. |
| tests/usage-publication-run-race.py | `test_uncontended_valid_registration_still_publishes` | 95 | Body inspected: uncontended valid registration still publishes. |
| tests/usage-publication-run-race.py | `test_closed_run_does_not_authorize_active_ingestion` | 95 | Body inspected: closed run does not authorize active ingestion. |
| tests/usage-report-consumer.py | `test_publish_and_exact_retry_refuse_conflicts` | 95 | Body inspected: publish and exact retry refuse conflicts. |
| tests/usage-report-consumer.py | `test_partial_or_inconsistent_archive_never_publishes` | 95 | Body inspected: partial or inconsistent archive never publishes. |
| tests/usage-report-consumer.py | `test_failed_write_and_moved_directory_leave_no_named_staging` | 95 | Body inspected: failed write and moved directory leave no named staging. |
| tests/usage-report-consumer.py | `test_full_archive_followed_by_producer_failure_never_installs` | 95 | Body inspected: full archive followed by producer failure never installs. |
| tests/usage-report-consumer.py | `test_cli_requires_protected_deployment_and_uses_typed_exit_codes` | 95 | Body inspected: cli requires protected deployment and uses typed exit codes. |
| tests/usage-report-consumer.py | `test_shared_storage_rejected` | 95 | Body inspected: shared storage rejected. |
| tests/usage-report-dimensions.py | `test_verified_dimensions_include_actual_component_totals` | 95 | Body inspected: verified dimensions include actual component totals. |
| tests/usage-report-dimensions.py | `test_untrusted_or_private_dimensions_are_unknown` | 95 | Body inspected: untrusted or private dimensions are unknown. |
| tests/usage-report-epochs.py | `test_epoch_requires_all_independently_timed_evidence` | 95 | Body inspected: epoch requires all independently timed evidence. |
| tests/usage-report-evidence-fields.py | `test_revision_requires_exact_independent_authority` | 95 | Body inspected: revision requires exact independent authority. |
| tests/usage-report-evidence-fields.py | `test_model_publication_needs_independent_authority` | 95 | Body inspected: model publication needs independent authority. |
| tests/usage-report-evidence-fields.py | `test_owner_publication_needs_independent_authority` | 95 | Body inspected: owner publication needs independent authority. |
| tests/usage-report-evidence-fields.py | `test_ownership_members_require_independent_cutoff` | 95 | Body inspected: ownership members require independent cutoff. |
| tests/usage-report-evidence-fields.py | `test_six_verified_leaves_are_ranked_by_actual_cost_and_capped_at_five` | 95 | Body inspected: six verified leaves are ranked by actual cost and capped at five. |
| tests/usage-report-evidence-fields.py | `test_repricing_is_conditional_in_all_report_cost_views` | 95 | Body inspected: repricing is conditional in all report cost views. |
| tests/usage-report-evidence-fields.py | `test_selected_revision_and_independently_verified_attribution_are_visible` | 95 | Body inspected: selected revision and independently verified attribution are visible. |
| tests/usage-report-evidence-fields.py | `test_price_terms_come_from_actual_independently_verified_rates` | 95 | Body inspected: price terms come from actual independently verified rates. |
| tests/usage-report-evidence-fields.py | `test_model_breakdown_and_leaf_ranking_require_proven_scope` | 95 | Body inspected: model breakdown and leaf ranking require proven scope. |
| tests/usage-report-evidence-fields.py | `test_unverified_revision_or_ownership_never_becomes_a_claim` | 95 | Body inspected: unverified revision or ownership never becomes a claim. |
| tests/usage-report-evidence-fields.py | `test_unverified_response_identity_never_claims_complete` | 95 | Body inspected: unverified response identity never claims complete. |
| tests/usage-report-evidence-fields.py | `test_unverified_prices_do_not_create_terms_or_ranked_leaves` | 95 | Body inspected: unverified prices do not create terms or ranked leaves. |
| tests/usage-report-evidence-fields.py | `test_selected_input_permutations_preserve_all_export_formats` | 95 | Body inspected: selected input permutations preserve all export formats. |
| tests/usage-report-evidence-fields.py | `test_unpriced_or_unverified_leaves_are_never_ranked_as_complete` | 95 | Body inspected: unpriced or unverified leaves are never ranked as complete. |
| tests/usage-report-exports.py | `test_json_csv_markdown_preserve_report_semantics` | 90 | Body inspected: json csv markdown preserve report semantics. |
| tests/usage-report-exports.py | `test_exact_decimal_strings_and_unknown_are_not_rounded_or_filled` | 90 | Body inspected: exact decimal strings and unknown are not rounded or filled. |
| tests/usage-report-exports.py | `test_input_sets_are_order_independent_without_mutation` | 90 | Body inspected: input sets are order independent without mutation. |
| tests/usage-report-exports.py | `test_csv_rejects_formula_and_private_paths_without_publishing_them` | 95 | Body inspected: csv rejects formula and private paths without publishing them. |
| tests/usage-report-exports.py | `test_closed_report_shape_and_header_reject_private_data` | 95 | Body inspected: closed report shape and header reject private data. |
| tests/usage-report-exports.py | `test_every_derived_total_is_a_canonical_decimal_string` | 90 | Body inspected: every derived total is a canonical decimal string. |
| tests/usage-report-exports.py | `test_all_scalar_values_survive_all_three_formats` | 90 | Body inspected: all scalar values survive all three formats. |
| tests/usage-report-exports.py | `test_fractional_utc_timestamps_and_five_completeness_dimensions` | 90 | Body inspected: fractional utc timestamps and five completeness dimensions. |
| tests/usage-report-exports.py | `test_archive_is_deterministic_and_contains_all_formats` | 90 | Body inspected: archive is deterministic and contains all formats. |
| tests/usage-report-exports.py | `test_contract_identifiers_reach_all_exports_at_boundaries` | 90 | Body inspected: contract identifiers reach all exports at boundaries. |
| tests/usage-report-exports.py | `test_contract_identifier_boundaries_reject_unsafe_values` | 95 | Body inspected: contract identifier boundaries reject unsafe values. |
| tests/usage-report-exports.py | `test_render_does_not_read_history_or_use_network` | 85 | Body inspected: render does not read history or use network. |
| tests/usage-report-multibundle-fields.py | `test_single_profile_exposes_unpriced_components_without_private_paths` | 95 | Body inspected: single profile exposes unpriced components without private paths. |
| tests/usage-report-multibundle-fields.py | `test_two_verified_profiles_retain_identity_terms_and_model_breakdown` | 95 | Body inspected: two verified profiles retain identity terms and model breakdown. |
| tests/usage-report-multibundle-fields.py | `test_unverified_union_or_response_privacy_never_claims_completeness` | 95 | Body inspected: unverified union or response privacy never claims completeness. |
| tests/usage-report-multibundle-fields.py | `test_independently_verified_ownership_and_contributors_are_combined_once` | 95 | Body inspected: independently verified ownership and contributors are combined once. |
| tests/usage-report-multibundle-fields.py | `test_missing_independent_ownership_does_not_gain_full_attribution` | 95 | Body inspected: missing independent ownership does not gain full attribution. |
| tests/usage-report-optional-pricing.py | `test_verified_tokens_survive_absent_price_inputs` | 95 | Body inspected: verified tokens survive absent price inputs. |
| tests/usage-report-optional-pricing.py | `test_foreign_or_unverified_context_never_becomes_known_tokens` | 95 | Body inspected: foreign or unverified context never becomes known tokens. |
| tests/usage-report-overlap-ownership.py | `test_equivalent_verified_ownership_is_deduplicated_once` | 95 | Body inspected: equivalent verified ownership is deduplicated once. |
| tests/usage-report-overlap-ownership.py | `test_conflicting_verified_owners_are_not_silently_selected` | 95 | Body inspected: conflicting verified owners are not silently selected. |
| tests/usage-report-overlap-tools.py | `test_duplicate_tool_identity_across_profiles_never_becomes_a_complete_sum` | 95 | Body inspected: duplicate tool identity across profiles never becomes a complete sum. |
| tests/usage-report-overlap-tools.py | `test_distinct_tool_ids_need_independent_complete_nonoverlap_union` | 95 | Body inspected: distinct tool ids need independent complete nonoverlap union. |
| tests/usage-resolution-cache-capabilities.py | `test_proven_unsupported_cache_does_not_require_inapplicable_components` | 95 | Body inspected: proven unsupported cache does not require inapplicable components. |
| tests/usage-resolution-cache-capabilities.py | `test_unsupported_cache_cannot_declare_cache_measurements` | 95 | Body inspected: unsupported cache cannot declare cache measurements. |
| tests/usage-resolution-cache-capabilities.py | `test_unsplit_write_preserves_tokens_but_its_price_remains_unknown` | 95 | Body inspected: unsplit write preserves tokens but its price remains unknown. |
| tests/usage-resolution-conditional.py | `test_derived_operand_uses_threshold_for_each_response_not_run_total` | 95 | Body inspected: derived operand uses threshold for each response not run total. |
| tests/usage-resolution-conditional.py | `test_unverified_source_operand_does_not_select_threshold_rate` | 95 | Body inspected: unverified source operand does not select threshold rate. |
| tests/usage-resolution-conditional.py | `test_alias_requires_independent_exact_mapping_and_source` | 95 | Body inspected: alias requires independent exact mapping and source. |
| tests/usage-resolution-conditional.py | `test_multiplier_needs_per_record_provenance_not_general_price_authority` | 95 | Body inspected: multiplier needs per record provenance not general price authority. |
| tests/usage-resolution-conditional.py | `test_explicit_reprice_is_conditional_and_never_a_historical_total` | 95 | Body inspected: explicit reprice is conditional and never a historical total. |
| tests/usage-resolution-conditional.py | `test_owned_reprice_is_also_marked_conditional` | 95 | Body inspected: owned reprice is also marked conditional. |
| tests/usage-resolution-conditional.py | `test_reprice_cannot_assume_or_guess_the_actual_model` | 95 | Body inspected: reprice cannot assume or guess the actual model. |
| tests/usage-resolution-correction-order.py | `test_reverse_sequence_correction_cannot_mix_old_final_measurements` | 95 | Body inspected: reverse sequence correction cannot mix old final measurements. |
| tests/usage-resolution-correction-order.py | `test_correctly_ordered_incomplete_correction_does_not_inherit_old_output` | 95 | Body inspected: correctly ordered incomplete correction does not inherit old output. |
| tests/usage-resolution-coverage.py | `test_proven_lower_bound_requires_nonnegative_excluded_scope` | 95 | Body inspected: proven lower bound requires nonnegative excluded scope. |
| tests/usage-resolution-coverage.py | `test_finality_follows_authorized_terminal_event_not_measurement_availability` | 95 | Body inspected: finality follows authorized terminal event not measurement availability. |
| tests/usage-resolution-coverage.py | `test_future_inventory_cannot_establish_historical_denominator` | 95 | Body inspected: future inventory cannot establish historical denominator. |
| tests/usage-resolution-coverage.py | `test_nonboolean_or_untrusted_scope_claim_cannot_prove_lower_bound` | 95 | Body inspected: nonboolean or untrusted scope claim cannot prove lower bound. |
| tests/usage-resolution-empty-scope.py | `test_complete_billable_scope_has_exact_zero_and_not_applicable_fractions` | 95 | Body inspected: complete billable scope has exact zero and not applicable fractions. |
| tests/usage-resolution-empty-scope.py | `test_empty_model_inventory_without_tool_proof_is_not_zero` | 95 | Body inspected: empty model inventory without tool proof is not zero. |
| tests/usage-resolution-empty-scope.py | `test_untrusted_or_late_inventory_never_proves_empty_scope` | 95 | Body inspected: untrusted or late inventory never proves empty scope. |
| tests/usage-resolution-empty-scope.py | `test_tool_proof_cannot_be_inferred_from_an_input_dictionary` | 95 | Body inspected: tool proof cannot be inferred from an input dictionary. |
| tests/usage-resolution-epochs.py | `test_exact_adjacent_delta_is_separate_from_response_accounting` | 95 | Body inspected: exact adjacent delta is separate from response accounting. |
| tests/usage-resolution-epochs.py | `test_partial_interval_is_only_aggregate_and_untrusted_evidence_is_unknown` | 95 | Body inspected: partial interval is only aggregate and untrusted evidence is unknown. |
| tests/usage-resolution-epochs.py | `test_atomic_completion_requires_separate_independent_authority` | 95 | Body inspected: atomic completion requires separate independent authority. |
| tests/usage-resolution-epochs.py | `test_scope_tampering_or_future_evidence_cannot_be_used` | 95 | Body inspected: scope tampering or future evidence cannot be used. |
| tests/usage-resolution-epochs.py | `test_disjoint_epoch_sum_above_safe_integer_is_exported_as_decimal_string` | 95 | Body inspected: two disjoint maximum-safe totals cross the safe-integer boundary; the earlier 1025-interval workload is no longer exercised. |
| tests/usage-resolution-epochs.py | `test_unverified_pack_hash_is_not_exported_as_proof_of_privacy` | 95 | Body inspected: unverified pack hash is not exported as proof of privacy. |
| tests/usage-resolution-epochs.py | `test_duplicate_interval_is_deduplicated_and_not_added_to_response_totals` | 95 | Body inspected: duplicate interval is deduplicated and not added to response totals. |
| tests/usage-resolution-evidence.py | `test_context_has_closed_bounded_schema` | 95 | Body inspected: context has closed bounded schema.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-resolution-evidence.py | `test_operand_provenance_is_independently_authorized` | 95 | Body inspected: operand provenance is independently authorized. |
| tests/usage-resolution-evidence.py | `test_matching_derived_digest_does_not_authorize_untrusted_raw_operand` | 95 | Body inspected: matching derived digest does not authorize untrusted raw operand. |
| tests/usage-resolution-evidence.py | `test_scope_binding_changes_evidence_domain` | 95 | Body inspected: scope binding changes evidence domain. |
| tests/usage-resolution-integration.py | `test_real_bundle_separates_final_tokens_from_historical_price_coverage` | 95 | Body inspected: real bundle separates final tokens from historical price coverage. |
| tests/usage-resolution-integration.py | `test_diagnostic_and_replay_leave_paid_accounting_unchanged` | 95 | Body inspected: diagnostic and replay leave paid accounting unchanged. |
| tests/usage-resolution-integration.py | `test_scoped_response_collisions_preserve_contributions_and_unknown_coverage` | 95 | Body inspected: scoped response collisions preserve contributions and unknown coverage. |
| tests/usage-resolution-integration.py | `test_scoped_collisions_preserve_both_exact_priced_contributions` | 95 | Body inspected: scoped collisions preserve both exact priced contributions. |
| tests/usage-resolution-integration.py | `test_untrusted_inventory_never_proves_denominator_or_complete_cost` | 95 | Body inspected: untrusted inventory never proves denominator or complete cost. |
| tests/usage-resolution-integration.py | `test_forged_scope_or_wrong_record_context_is_not_authorized` | 95 | Body inspected: forged scope or wrong record context is not authorized. |
| tests/usage-resolution-integration.py | `test_one_record_measurement_cannot_authorize_another_record` | 95 | Body inspected: one record measurement cannot authorize another record. |
| tests/usage-resolution-integration.py | `test_call_only_overlap_cannot_create_additive_cost` | 95 | Body inspected: call only overlap cannot create additive cost. |
| tests/usage-resolution-integration.py | `test_set_order_is_deterministic_and_no_network_or_history_is_read` | 95 | Body inspected: set order is deterministic and no network or history is read. |
| tests/usage-resolution-measurement-finality.py | `test_final_snapshot_with_partial_input_cannot_produce_complete_input_or_cost` | 95 | Body inspected: final snapshot with partial input cannot produce complete input or cost. |
| tests/usage-resolution-measurement-finality.py | `test_verified_delta_parts_can_be_finalized_by_terminal` | 20 | Strict assertion subset of usage-resolution-revisions.py::test_contiguous_deltas_and_terminal_are_summed_once, using the identical fixture and resolver. Removed; covering test passed. |
| tests/usage-resolution-no-prices.py | `test_absent_scenario_and_snapshots_preserve_verified_token_totals` | 95 | Body inspected: absent scenario and snapshots preserve verified token totals. |
| tests/usage-resolution-no-prices.py | `test_scenario_without_selected_snapshots_remains_unpriced` | 95 | Body inspected: scenario without selected snapshots remains unpriced. |
| tests/usage-resolution-no-prices.py | `test_unknown_actual_model_does_not_use_scenario_model` | 95 | Body inspected: unknown actual model does not use scenario model. |
| tests/usage-resolution-no-prices.py | `test_price_retrieved_after_cutoff_cannot_price_historical_work` | 95 | Body inspected: price retrieved after cutoff cannot price historical work. |
| tests/usage-resolution-no-prices.py | `test_malformed_nonempty_price_input_is_rejected` | 95 | Body inspected: malformed nonempty price input is rejected. |
| tests/usage-resolution-ownership.py | `test_shared_parent_pool_is_counted_once_without_leaf_allocation` | 95 | Body inspected: shared parent pool is counted once without leaf allocation. |
| tests/usage-resolution-ownership.py | `test_missing_provenance_or_inventory_keeps_scope_incomplete` | 95 | Body inspected: missing provenance or inventory keeps scope incomplete. |
| tests/usage-resolution-ownership.py | `test_forged_record_or_provider_cannot_inherit_other_proof` | 95 | Body inspected: forged record or provider cannot inherit other proof. |
| tests/usage-resolution-ownership.py | `test_late_attribution_changes_only_new_report` | 95 | Body inspected: late attribution changes only new report. |
| tests/usage-resolution-ownership.py | `test_proven_descendant_rolls_up_without_guessed_ancestry` | 95 | Body inspected: proven descendant rolls up without guessed ancestry. |
| tests/usage-resolution-ownership.py | `test_foreign_owner_may_be_excluded_only_by_separate_scope_proof` | 95 | Body inspected: foreign owner may be excluded only by separate scope proof. |
| tests/usage-resolution-ownership.py | `test_unattributed_external_pool_does_not_complete_parent` | 95 | Body inspected: unattributed external pool does not complete parent. |
| tests/usage-resolution-partial-stream.py | `test_latest_snapshot_is_partial_and_never_added_or_finalized` | 95 | Body inspected: latest snapshot is partial and never added or finalized. |
| tests/usage-resolution-partial-stream.py | `test_rejected_latest_measurement_is_not_published` | 95 | Body inspected: rejected latest measurement is not published. |
| tests/usage-resolution-partial-stream.py | `test_deltas_without_terminal_are_preserved_as_partial` | 95 | Body inspected: deltas without terminal are preserved as partial. |
| tests/usage-resolution-partial-stream.py | `test_delta_gap_remains_partial_and_is_not_final` | 95 | Body inspected: delta gap remains partial and is not final. |
| tests/usage-resolution-partial-stream.py | `test_final_snapshot_supersedes_partials_without_addition` | 95 | Body inspected: final snapshot supersedes partials without addition. |
| tests/usage-resolution-privacy.py | `test_rejected_authority_cannot_disclose_identifiers` | 95 | Body inspected: rejected authority cannot disclose identifiers. |
| tests/usage-resolution-privacy.py | `test_privacy_requires_independent_exact_scope_and_record` | 95 | Body inspected: privacy requires independent exact scope and record. |
| tests/usage-resolution-privacy.py | `test_exact_authorization_discloses_verified_records` | 95 | Body inspected: exact authorization discloses verified records. |
| tests/usage-resolution-regressions.py | `test_complete_model_prices_do_not_prove_absence_of_tool_expenses` | 95 | Body inspected: complete model prices do not prove absence of tool expenses. |
| tests/usage-resolution-regressions.py | `test_duplicate_finals_with_different_record_context_are_not_priced_by_arrival` | 95 | Body inspected: duplicate finals with different record context are not priced by arrival. |
| tests/usage-resolution-report-evidence.py | `test_actual_terms_are_exact_unique_and_per_response` | 95 | Body inspected: actual terms are exact unique and per response. |
| tests/usage-resolution-report-evidence.py | `test_missing_prices_remove_terms_without_losing_identity` | 95 | Body inspected: missing prices remove terms without losing identity. |
| tests/usage-resolution-report-evidence.py | `test_missing_measurements_do_not_conflate_identity_and_coverage` | 95 | Body inspected: missing measurements do not conflate identity and coverage. |
| tests/usage-resolution-report-evidence.py | `test_missing_context_or_inventory_does_not_prove_identity` | 95 | Body inspected: missing context or inventory does not prove identity. |
| tests/usage-resolution-report-evidence.py | `test_reprice_terms_are_explicitly_conditional` | 95 | Body inspected: reprice terms are explicitly conditional. |
| tests/usage-resolution-response-details.py | `test_identity_tokens_and_model_cost_are_explicit_per_response` | 95 | Body inspected: identity tokens and model cost are explicit per response. |
| tests/usage-resolution-response-details.py | `test_source_operand_rejection_never_exports_complete_input` | 95 | Body inspected: source operand rejection never exports complete input. |
| tests/usage-resolution-response-details.py | `test_unverified_identity_cannot_export_usable_per_response_cost` | 95 | Body inspected: unverified identity cannot export usable per response cost. |
| tests/usage-resolution-response-details.py | `test_conflicting_final_contexts_are_not_exported_as_one_priced_response` | 95 | Body inspected: conflicting final contexts are not exported as one priced response. |
| tests/usage-resolution-response-details.py | `test_unresolved_call_overlap_never_exports_additive_model_cost` | 95 | Body inspected: unresolved call overlap never exports additive model cost. |
| tests/usage-resolution-revisions.py | `test_mixed_partial_and_final_responses_preserve_price_snapshots` | 95 | Body inspected: mixed partial and final responses preserve price snapshots. |
| tests/usage-resolution-revisions.py | `test_partial_snapshot_replaced_by_final_without_double_count` | 95 | Body inspected: partial snapshot replaced by final without double count. |
| tests/usage-resolution-revisions.py | `test_verified_correction_replaces_old_final_and_untrusted_correction_conflicts` | 95 | Body inspected: verified correction replaces old final and untrusted correction conflicts. |
| tests/usage-resolution-revisions.py | `test_verified_correction_supersedes_conflicted_write_snapshot` | 95 | Body inspected: verified correction supersedes conflicted write snapshot. |
| tests/usage-resolution-revisions.py | `test_final_snapshot_supersedes_conflicted_partial_snapshot` | 95 | Body inspected: final snapshot supersedes conflicted partial snapshot. |
| tests/usage-resolution-revisions.py | `test_contiguous_deltas_and_terminal_are_summed_once` | 95 | Body inspected: contiguous deltas and terminal are summed once. |
| tests/usage-resolution-revisions.py | `test_later_partial_snapshot_does_not_reuse_old_final_cost` | 95 | Body inspected: later partial snapshot does not reuse old final cost. |
| tests/usage-resolution-revisions.py | `test_large_verified_delta_total_stays_exact_and_prices_without_rounding` | 95 | Body inspected: large verified delta total stays exact and prices without rounding. |
| tests/usage-resolution-revisions.py | `test_missing_delta_or_terminal_proof_cannot_be_final` | 95 | Body inspected: missing delta or terminal proof cannot be final. |
| tests/usage-resolution-revisions.py | `test_snapshot_scope_cannot_be_reinterpreted_as_delta` | 95 | Body inspected: snapshot scope cannot be reinterpreted as delta. |
| tests/usage-resolution-revisions.py | `test_delta_scope_cannot_be_reinterpreted_as_snapshot` | 95 | Body inspected: delta scope cannot be reinterpreted as snapshot. |
| tests/usage-resolution-revisions.py | `test_stream_order_is_semantic_not_input_arrival` | 95 | Body inspected: stream order is semantic not input arrival. |
| tests/usage-resolution-token-components.py | `test_verified_final_response_exposes_independent_components` | 95 | Body inspected: verified final response exposes independent components. |
| tests/usage-resolution-token-components.py | `test_conflicting_unsplit_writes_do_not_recreate_input_totals` | 95 | Body inspected: conflicting unsplit writes do not recreate input totals. |
| tests/usage-resolution-token-components.py | `test_partial_component_is_never_reported_complete` | 95 | Body inspected: partial component is never reported complete. |
| tests/usage-resolution-token-components.py | `test_missing_authorization_never_produces_a_value` | 95 | Body inspected: missing authorization never produces a value. |
| tests/usage-resolution-token-components.py | `test_final_delta_parts_use_terminal_without_double_counting` | 95 | Body inspected: final delta parts use terminal without double counting. |
| tests/usage-resolution-tokens.py | `test_complete_input_and_output_have_nonoverlapping_exact_totals` | 95 | Body inspected: complete input and output have nonoverlapping exact totals. |
| tests/usage-resolution-tokens.py | `test_missing_one_source_operand_cannot_complete_input` | 95 | Body inspected: missing one source operand cannot complete input. |
| tests/usage-resolution-tokens.py | `test_unknown_inventory_cannot_justify_complete_token_coverage` | 95 | Body inspected: unknown inventory cannot justify complete token coverage. |
| tests/usage-resolution-tokens.py | `test_large_derived_totals_are_canonical_decimal_strings` | 95 | Body inspected: large derived totals are canonical decimal strings. |
| tests/usage-resolution-tokens.py | `test_unavailable_evidence_is_not_zero` | 95 | Body inspected: unavailable evidence is not zero. |
| tests/usage-resolution-tool-ownership.py | `test_shared_tool_pool_is_counted_once_at_parent_and_not_allocated_to_leaf` | 95 | Body inspected: shared tool pool is counted once at parent and not allocated to leaf. |
| tests/usage-resolution-tool-ownership.py | `test_model_and_tool_contributors_combine_only_after_scope_proof` | 95 | Body inspected: model and tool contributors combine only after scope proof. |
| tests/usage-resolution-tool-ownership.py | `test_untrusted_tool_ownership_or_inventory_never_proves_full_cost` | 95 | Body inspected: untrusted tool ownership or inventory never proves full cost. |
| tests/usage-resolution-tool-ownership.py | `test_late_or_forged_attribution_is_not_inherited_by_scope` | 95 | Body inspected: late or forged attribution is not inherited by scope. |
| tests/usage-resolution-tool-ownership.py | `test_tool_descendant_and_exclusion_require_exact_separate_proof` | 95 | Body inspected: tool descendant and exclusion require exact separate proof. |
| tests/usage-resolution-tool-ownership.py | `test_conditional_tool_reprice_is_marked_at_every_owner_level` | 95 | Body inspected: conditional tool reprice is marked at every owner level. |
| tests/usage-resolution-tools.py | `test_empty_model_inventory_and_known_tool_expense_is_not_zero` | 95 | Body inspected: empty model inventory and known tool expense is not zero. |
| tests/usage-resolution-tools.py | `test_explicit_empty_tool_inputs_preserve_proven_empty_scope` | 95 | Body inspected: explicit empty tool inputs preserve proven empty scope. |
| tests/usage-resolution-tools.py | `test_tool_and_response_model_costs_add_without_overlap` | 95 | Body inspected: tool and response model costs add without overlap. |
| tests/usage-resolution-tools.py | `test_repriced_tools_remain_conditional` | 95 | Body inspected: repriced tools remain conditional. |
| tests/usage-resolution-tools.py | `test_missing_provenance_inventory_or_nonoverlap_prevents_total` | 95 | Body inspected: missing provenance inventory or nonoverlap prevents total. |
| tests/usage-resolution-tools.py | `test_identical_tool_input_is_counted_once_conflicting_id_is_not_added` | 95 | Body inspected: identical tool input is counted once conflicting id is not added. |
| tests/usage-resolution-tools.py | `test_wrong_source_quantity_or_unavailable_price_cannot_be_assumed` | 95 | Body inspected: wrong source quantity or unavailable price cannot be assumed. |
| tests/usage-resolution-tools.py | `test_closed_tool_schema_binds_quantity_and_sanitizes_errors` | 95 | Body inspected: closed tool schema binds quantity and sanitizes errors. |
| tests/usage-resolution-tools.py | `test_late_tool_evidence_is_not_imported_into_an_old_scope` | 95 | Body inspected: late tool evidence is not imported into an old scope. |
| tests/usage-resolution-tools.py | `test_unverified_tool_id_and_private_values_are_not_exposed` | 95 | Body inspected: unverified tool id and private values are not exposed. |
| tests/usage-resolved-report-integration.py | `test_real_selected_work_has_full_token_and_partial_pricing_coverage` | 95 | Body inspected: real selected work has full token and partial pricing coverage. |
| tests/usage-resolved-report-integration.py | `test_changed_independent_assertions_change_identity_and_cannot_forge_coverage` | 95 | Body inspected: changed independent assertions change identity and cannot forge coverage. |
| tests/usage-resolved-report-integration.py | `test_unselected_scenario_or_context_is_never_discovered` | 95 | Body inspected: unselected scenario or context is never discovered. |
| tests/usage-response-identity.py | `test_branched_copies_are_one_response` | 95 | Body inspected: branched copies are one response. |
| tests/usage-response-identity.py | `test_response_identity_is_provider_and_account_scoped` | 95 | Body inspected: response identity is provider and account scoped. |
| tests/usage-response-identity.py | `test_two_responses_for_one_call_remain_distinct` | 95 | Body inspected: two responses for one call remain distinct. |
| tests/usage-response-identity.py | `test_verified_unique_call_alias_merges_with_response` | 95 | Body inspected: verified unique call alias merges with response. |
| tests/usage-response-identity.py | `test_two_responses_and_call_only_record_leave_overlap_unresolved` | 95 | Body inspected: two responses and call only record leave overlap unresolved. |
| tests/usage-response-identity.py | `test_call_alone_requires_verified_stable_unique_alias` | 95 | Body inspected: call alone requires verified stable unique alias. |
| tests/usage-response-identity.py | `test_verified_stable_call_can_identify_response_when_response_id_absent` | 95 | Body inspected: verified stable call can identify response when response id absent. |
| tests/usage-response-identity.py | `test_missing_identity_never_uses_time_or_token_coincidence` | 95 | Body inspected: missing identity never uses time or token coincidence. |
| tests/usage-response-identity.py | `test_unidentified_observation_excludes_same_scope_from_additive_totals` | 95 | Body inspected: unidentified observation excludes same scope from additive totals. |
| tests/usage-response-identity.py | `test_unlinked_call_may_overlap_response_without_call_id` | 95 | Body inspected: unlinked call may overlap response without call id. |
| tests/usage-response-identity.py | `test_conflicting_verified_aliases_do_not_pick_first` | 95 | Body inspected: conflicting verified aliases do not pick first. |
| tests/usage-response-identity.py | `test_input_permutations_and_repeated_observations_are_stable` | 95 | Body inspected: input permutations and repeated observations are stable. |
| tests/usage-response-identity.py | `test_duplicate_observation_id_with_different_content_is_invalid` | 95 | Body inspected: duplicate observation id with different content is invalid. |
| tests/usage-response-identity.py | `test_limits_and_bool_are_checked_before_processing` | 95 | Body inspected: limits and bool are checked before processing. |
| tests/usage-response-identity.py | `test_raw_paths_secrets_and_unknown_fields_are_rejected_without_echo` | 95 | Body inspected: raw paths secrets and unknown fields are rejected without echo. |
| tests/usage-response-identity.py | `test_empty_input_has_no_fabricated_responses` | 95 | Body inspected: empty input has no fabricated responses. |
| tests/usage-retrospective-integration.py | `test_valid_selected_corpus_produces_equivalent_exports_without_history` | 95 | Body inspected: valid selected corpus produces equivalent exports without history. |
| tests/usage-retrospective-integration.py | `test_contract_identifiers_flow_from_corpus_to_archive` | 95 | Body inspected: contract identifiers flow from corpus to archive. |
| tests/usage-retrospective-integration.py | `test_uninventoried_unattributed_record_does_not_create_coverage_or_cost` | 95 | Body inspected: uninventoried unattributed record does not create coverage or cost. |
| tests/usage-retrospective-integration.py | `test_late_observation_does_not_change_an_earlier_selected_report` | 95 | Body inspected: late observation does not change an earlier selected report. |
| tests/usage-retrospective-integration.py | `test_untrusted_or_tampered_selected_input_never_produces_report` | 95 | Body inspected: untrusted or tampered selected input never produces report. |
| tests/usage-retrospective-integration.py | `test_selected_lifecycle_record_uses_existing_event_contract` | 95 | Body inspected: selected lifecycle record uses existing event contract. |
| tests/usage-retrospective-integration.py | `test_command_exposes_offline_explicit_analysis` | 95 | Body inspected: command exposes offline explicit analysis. |
| tests/usage-retrospective-outcome-timing.py | `test_timing_and_acceptance_without_usage_bundle` | 95 | Body inspected: timing and acceptance without usage bundle. |
| tests/usage-retrospective-outcome-timing.py | `test_independently_accepted_outcomes_use_only_actual_resolved_costs` | 95 | Body inspected: independently accepted outcomes use only actual resolved costs. |
| tests/usage-retrospective-outcome-timing.py | `test_unselected_experimental_cost_is_unknown_not_zero` | 95 | Body inspected: unselected experimental cost is unknown not zero. |
| tests/usage-retrospective-outcome-timing.py | `test_empty_experimental_cost_needs_independent_empty_inventory` | 95 | Body inspected: empty experimental cost needs independent empty inventory. |
| tests/usage-retrospective-outcome-timing.py | `test_untrusted_acceptance_does_not_become_a_success` | 95 | Body inspected: untrusted acceptance does not become a success. |
| tests/usage-retrospective-outcome-timing.py | `test_later_defect_revision_does_not_rewrite_older_report` | 95 | Body inspected: later defect revision does not rewrite older report. |
| tests/usage-retrospective-outcome-timing.py | `test_one_response_cannot_be_charged_to_two_attempts` | 95 | Body inspected: one response cannot be charged to two attempts. |
| tests/usage-retrospective-outcome-timing.py | `test_measured_intervals_use_union_and_independent_graph_completeness` | 95 | Body inspected: measured intervals use union and independent graph completeness. |
| tests/usage-retrospective-outcome-timing.py | `test_omitted_child_cannot_inherit_a_complete_graph_attestation` | 95 | Body inspected: omitted child cannot inherit a complete graph attestation. |
| tests/usage-retrospective-outcome-timing.py | `test_conflicting_selected_root_cannot_inherit_graph_attestation` | 95 | Body inspected: conflicting selected root cannot inherit graph attestation. |
| tests/usage-retrospective-outcome-timing.py | `test_real_measured_groups_have_exact_statistics_and_stable_exports` | 95 | Body inspected: real measured groups have exact statistics and stable exports. |
| tests/usage-source-normalization.py | `test_valid_selected_source_produces_private_bounded_bundle_with_evidence` | 95 | Body inspected: valid selected source produces private bounded bundle with evidence. |
| tests/usage-source-normalization.py | `test_duplicate_selected_sources_preserve_distinct_records_and_contexts` | 95 | Body inspected: duplicate selected sources preserve distinct records and contexts. |
| tests/usage-source-normalization.py | `test_keyed_ids_are_deterministic_domain_separated_and_keyed` | 95 | Body inspected: keyed ids are deterministic domain separated and keyed. |
| tests/usage-source-normalization.py | `test_only_explicit_sources_are_opened_and_network_is_unused` | 95 | Body inspected: only explicit sources are opened and network is unused. |
| tests/usage-source-normalization.py | `test_invalid_record_is_quarantined_without_payload_and_valid_siblings_are_partial` | 95 | Body inspected: invalid record is quarantined without payload and valid siblings are partial. |
| tests/usage-source-normalization.py | `test_malformed_record_does_not_discard_valid_siblings` | 95 | Body inspected: malformed record does not discard valid siblings. |
| tests/usage-source-normalization.py | `test_quarantine_diagnostics_survive_bundle_extraction_and_preserve_source_scope` | 95 | Body inspected: quarantine diagnostics survive bundle extraction and preserve source scope. |
| tests/usage-source-normalization.py | `test_prefix_diagnostic_survives_bundle_extraction` | 95 | Body inspected: prefix diagnostic survives bundle extraction. |
| tests/usage-source-normalization.py | `test_record_byte_limit_accepts_boundary_and_quarantines_larger_record` | 95 | Body inspected: record byte limit accepts boundary and quarantines larger record. |
| tests/usage-source-normalization.py | `test_record_tree_limits_report_input_limit_without_leaking_payload` | 95 | Body inspected: record tree limits report input limit without leaking payload. |
| tests/usage-source-normalization.py | `test_invalid_selection_profile_and_changed_file_reject_atomically_without_private_errors` | 95 | Body inspected: invalid selection profile and changed file reject atomically without private errors. |
| tests/usage-source-normalization.py | `test_prefix_and_absent_measurements_never_claim_complete` | 95 | Body inspected: prefix and absent measurements never claim complete. |
| tests/usage-source-profiles.py | `test_included_and_separate_inputs_have_equal_nonoverlapping_totals` | 95 | Body inspected: included and separate inputs have equal nonoverlapping totals. |
| tests/usage-source-profiles.py | `test_matching_split_retains_evidence_and_does_not_double_count` | 95 | Body inspected: matching split retains evidence and does not double count. |
| tests/usage-source-profiles.py | `test_mismatch_and_negative_remainder_preserve_unaffected_output` | 95 | Body inspected: mismatch and negative remainder preserve unaffected output. |
| tests/usage-source-profiles.py | `test_conflicting_unsplit_writes_block_separate_input_total` | 95 | Body inspected: conflicting unsplit writes block separate input total. |
| tests/usage-source-profiles.py | `test_conflicting_unsplit_writes_block_included_input_remainder` | 95 | Body inspected: conflicting unsplit writes block included input remainder. |
| tests/usage-source-profiles.py | `test_reasoning_exceeding_output_is_conflicted` | 95 | Body inspected: reasoning exceeding output is conflicted. |
| tests/usage-source-profiles.py | `test_unsupported_version_and_unknown_cache_are_never_invented_zero` | 95 | Body inspected: unsupported version and unknown cache are never invented zero. |
| tests/usage-source-profiles.py | `test_unverified_counter_semantics_cannot_be_used_to_infer_remainder` | 95 | Body inspected: unverified counter semantics cannot be used to infer remainder. |
| tests/usage-source-profiles.py | `test_observation_and_bundle_validate_per_component_evidence_and_canonical_order` | 95 | Body inspected: observation and bundle validate per component evidence and canonical order. |
| tests/usage-source-profiles.py | `test_duplicate_ttl_mismatched_total_and_wrong_evidence_are_rejected` | 95 | Body inspected: duplicate ttl mismatched total and wrong evidence are rejected. |
| tests/usage-source-profiles.py | `test_large_derived_sum_is_exact_decimal_string_in_observation` | 95 | Body inspected: large derived sum is exact decimal string in observation. |
| tests/usage-source-profiles.py | `test_proven_total_remains_usable_when_one_ttl_is_unknown` | 95 | Body inspected: proven total remains usable when one ttl is unknown. |
| tests/usage-source-profiles.py | `test_known_part_above_total_conflicts_even_with_missing_ttl` | 95 | Body inspected: known part above total conflicts even with missing ttl. |
| tests/usage-source-profiles.py | `test_derived_evidence_references_operands_and_verified_profile` | 95 | Body inspected: derived evidence references operands and verified profile. |
| tests/usage-source-profiles.py | `test_derived_proof_rejects_rehashed_value_scope_and_profile_tampering` | 95 | Body inspected: derived proof rejects rehashed value scope and profile tampering. |
| tests/usage-source-selection.py | `test_complete_selection_and_explicit_unknowns_are_preserved` | 90 | Body inspected: complete selection and explicit unknowns are preserved. |
| tests/usage-source-selection.py | `test_required_fields_versions_and_closed_fields` | 90 | Body inspected: required fields versions and closed fields. |
| tests/usage-source-selection.py | `test_source_entries_require_safe_shape_and_exact_digests` | 90 | Body inspected: source entries require safe shape and exact digests. |
| tests/usage-source-selection.py | `test_limits_are_explicit_integer_and_cover_selected_extent` | 90 | Body inspected: limits are explicit integer and cover selected extent. |
| tests/usage-source-selection.py | `test_entries_and_attribution_are_bounded_and_closed` | 90 | Body inspected: entries and attribution are bounded and closed.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-source-selection.py | `test_json_duplicate_keys_and_input_and_canonical_byte_bounds` | 90 | Body inspected: json duplicate keys and input and canonical byte bounds. |
| tests/usage-source-selection.py | `test_validation_never_reads_selected_path` | 90 | Body inspected: validation never reads selected path. |
| tests/usage-status-canonical-bindings.py | `test_snapshot_analysis_sets_preserve_identity_when_reordered` | 95 | Body inspected: snapshot analysis sets preserve identity when reordered. |
| tests/usage-status-canonical-bindings.py | `test_authority_recognizes_nested_observation_set_permutations` | 95 | Body inspected: authority recognizes nested observation set permutations. |
| tests/usage-status-cli-integration.py | `test_explicit_inputs_and_separate_authority_produce_stable_candidates_offline` | 95 | Body inspected: explicit inputs and separate authority produce stable candidates offline. |
| tests/usage-status-cli-integration.py | `test_repricing_does_not_create_factual_owner_spend_warning` | 95 | Body inspected: repricing does not create factual owner spend warning. |
| tests/usage-status-cli-integration.py | `test_absent_authority_cannot_promote_snapshot_claims_to_proof` | 95 | Body inspected: absent authority cannot promote snapshot claims to proof. |
| tests/usage-status-cli-integration.py | `test_authority_requires_private_permissions` | 95 | Body inspected: authority requires private permissions. |
| tests/usage-status-coverage-integration.py | `test_incomplete_inventory_yields_strict_coverage_warning` | 95 | Body inspected: incomplete inventory yields strict coverage warning. |
| tests/usage-status-coverage-integration.py | `test_missing_inventory_authority_has_unknown_coverage_without_percentage` | 95 | Body inspected: missing inventory authority has unknown coverage without percentage. |
| tests/usage-status-delivery-integration.py | `test_owner_command_rejects_shared_state_or_note_before_mutation` | 95 | Body inspected: owner command rejects shared state or note before mutation. |
| tests/usage-status-delivery-integration.py | `test_owner_command_accepts_socket_output` | 95 | Body inspected: owner command accepts socket output. |
| tests/usage-status-delivery-integration.py | `test_owner_command_rejects_regular_output_before_any_mutation` | 95 | Body inspected: owner command rejects regular output before any mutation. |
| tests/usage-status-delivery-integration.py | `test_owner_command_delivers_and_reports_pending_recovery` | 95 | Body inspected: owner command delivers and reports pending recovery. |
| tests/usage-status-delivery-integration.py | `test_lower_bound_details_survive_pending_delivery_and_retry` | 95 | Body inspected: lower bound details survive pending delivery and retry. |
| tests/usage-status-delivery-integration.py | `test_empty_parts_manifest_survives_status_and_recovery` | 95 | Body inspected: empty parts manifest survives status and recovery. |
| tests/usage-status-delivery-integration.py | `test_selected_segment_and_warning_history_survive_delivery` | 95 | Body inspected: selected segment and warning history survive delivery. |
| tests/usage-status-delivery-integration.py | `test_real_status_proposal_is_accepted_and_repeat_does_not_duplicate` | 95 | Body inspected: real status proposal is accepted and repeat does not duplicate. |
| tests/usage-status-delivery-integration.py | `test_real_proposal_recovers_after_interrupted_acceptance` | 95 | Body inspected: real proposal recovers after interrupted acceptance. |
| tests/usage-status-delivery-integration.py | `test_real_proposal_preserves_pending_report_until_destination_is_available` | 95 | Body inspected: real proposal preserves pending report until destination is available. |
| tests/usage-status-duration-integration.py | `test_default_duration_crossing_is_pure_and_stable_when_collection_is_off` | 90 | Body inspected: default duration crossing is pure and stable when collection is off. |
| tests/usage-status-duration-integration.py | `test_equal_boundary_unverified_open_and_unknown_clocks_do_not_warn` | 90 | Body inspected: equal boundary unverified open and unknown clocks do not warn. |
| tests/usage-status-duration-integration.py | `test_time_only_cli_uses_explicit_owner_authority_without_history` | 90 | Body inspected: time only cli uses explicit owner authority without history. |
| tests/usage-status-duration-kinds.py | `test_one_scope_can_warn_independently_for_work_and_run` | 90 | Body inspected: one scope can warn independently for work and run. |
| tests/usage-status-duration-kinds.py | `test_unknown_clock_source_is_not_a_duration_measurement` | 90 | Body inspected: unknown clock source is not a duration measurement. |
| tests/usage-status-duration-precision.py | `test_fractional_second_crossing_preserves_exact_milliseconds` | 90 | Body inspected: fractional second crossing preserves exact milliseconds. |
| tests/usage-status-duration-precision.py | `test_run_and_closed_span_episodes_are_independent` | 90 | Body inspected: run and closed span episodes are independent. |
| tests/usage-status-duration-precision.py | `test_missing_clock_evidence_has_a_diagnostic` | 90 | Body inspected: missing clock evidence has a diagnostic. |
| tests/usage-status-fraction-coverage.py | `test_fraction_is_exact_and_compared_without_decimal_rounding` | 95 | Body inspected: fraction is exact and compared without decimal rounding. |
| tests/usage-status-input-schema.py | `test_valid_self_contained_inputs_are_offline_and_byte_bounded` | 90 | Body inspected: valid self contained inputs are offline and byte bounded. |
| tests/usage-status-input-schema.py | `test_closed_inputs_reject_unknown_and_missing_fields_without_disclosing_payload` | 90 | Body inspected: closed inputs reject unknown and missing fields without disclosing payload. |
| tests/usage-status-input-schema.py | `test_nested_entries_count_toward_explicit_snapshot_limit` | 90 | Body inspected: nested entries count toward explicit snapshot limit. |
| tests/usage-status-input-schema.py | `test_nested_lists_have_independent_hard_limits_and_no_duplicate_bindings` | 90 | Body inspected: nested lists have independent hard limits and no duplicate bindings.; synthetic reported length checks the count guard, without an actual 10001-element array. |
| tests/usage-status-input-schema.py | `test_context_and_ownership_must_bind_selected_observation` | 90 | Body inspected: context and ownership must bind selected observation. |
| tests/usage-status-input-schema.py | `test_duplicate_argument_must_match_snapshot_or_be_rejected` | 90 | Body inspected: duplicate argument must match snapshot or be rejected. |
| tests/usage-status-input-schema.py | `test_missing_or_untrusted_context_never_produces_owned_values` | 90 | Body inspected: missing or untrusted context never produces owned values. |
| tests/usage-status-integration.py | `test_bounded_snapshot_accepts_explicit_pricing_inputs_without_reading` | 20 | Same inputs, network and file guards, valid and max_bytes=10 rejection as usage-status-input-schema.py::test_valid_self_contained_inputs_are_offline_and_byte_bounded. Removed; covering test passed. |
| tests/usage-status-integration.py | `test_real_receipts_produce_verified_threshold_candidates_and_stable_retry` | 95 | Body inspected: real receipts produce verified threshold candidates and stable retry. |
| tests/usage-status-integration.py | `test_equality_does_not_cross_exact_money_boundary` | 95 | Body inspected: equality does not cross exact money boundary. |
| tests/usage-status-integration.py | `test_untrusted_receipt_or_measurements_cannot_trigger` | 95 | Body inspected: untrusted receipt or measurements cannot trigger. |
| tests/usage-status-integration.py | `test_missing_price_authority_or_inputs_is_unknown_not_zero` | 95 | Body inspected: missing price authority or inputs is unknown not zero. |
| tests/usage-status-integration.py | `test_unproved_nonnegative_scope_cannot_establish_money_lower_bound` | 95 | Body inspected: unproved nonnegative scope cannot establish money lower bound. |
| tests/usage-status-integration.py | `test_exact_token_equality_does_not_cross` | 95 | Body inspected: exact token equality does not cross. |
| tests/usage-status-integration.py | `test_pending_episode_survives_lost_evidence_without_clearing` | 95 | Body inspected: pending episode survives lost evidence without clearing. |
| tests/usage-status-integration.py | `test_absent_scope_evidence_never_creates_request_or_span_warning` | 95 | Body inspected: absent scope evidence never creates request or span warning. |
| tests/usage-status-large-authority.py | `test_explicitly_authorized_large_bundle_produces_real_metrics` | 90 | Body inspected: explicitly authorized large bundle produces real metrics. |
| tests/usage-status-large-authority.py | `test_mismatched_binding_is_not_authorization` | 90 | Body inspected: mismatched binding is not authorization. |
| tests/usage-status-large-parts.py | `test_valid_large_bundle_within_part_and_total_limits_is_not_rejected` | 90 | Body inspected: valid large bundle within part and total limits is not rejected. |
| tests/usage-status-multiple-bundles.py | `test_explicit_receipts_share_one_identity_aware_resolution` | 95 | Body inspected: explicit receipts share one identity aware resolution. |
| tests/usage-status-multiple-bundles.py | `test_same_observations_across_receipts_are_not_counted_twice` | 95 | Body inspected: same observations across receipts are not counted twice. |
| tests/usage-status-multiple-bundles.py | `test_untrusted_receipt_never_joins_the_owner_report` | 95 | Body inspected: untrusted receipt never joins the owner report. |
| tests/usage-status-no-pricing.py | `test_verified_tokens_and_coverage_survive_missing_prices` | 95 | Body inspected: verified tokens and coverage survive missing prices. |
| tests/usage-status-output-relocation.py | `test_relocation_between_check_and_replace_cannot_publish_to_shared_store` | 95 | Body inspected: relocation between check and replace cannot publish to shared store. |
| tests/usage-status-output-relocation.py | `test_status_input_error_is_operation_specific_and_sanitized` | 95 | Body inspected: status input error is operation specific and sanitized. |
| tests/usage-status-output-relocation.py | `test_owner_delivery_errors_are_operation_specific_and_sanitized` | 95 | Body inspected: owner delivery errors are operation specific and sanitized. |
| tests/usage-status-owner-scopes.py | `test_verified_request_and_span_use_only_their_own_resolved_response` | 95 | Body inspected: verified request and span use only their own resolved response. |
| tests/usage-status-parts-cli.py | `test_selected_bundle_is_assembled_from_short_reads_and_digest_checked` | 95 | Body inspected: selected bundle is assembled from short reads and digest checked. |
| tests/usage-status-parts-cli.py | `test_exact_selected_parts_are_loaded_without_touching_neighbor_or_source` | 95 | Body inspected: exact selected parts are loaded without touching neighbor or source. |
| tests/usage-status-parts-cli.py | `test_selected_parts_proposal_delivers_and_preserves_manifest` | 95 | Body inspected: selected parts proposal delivers and preserves manifest. |
| tests/usage-status-parts-cli.py | `test_incorrect_hash_size_and_changed_file_fail_before_output` | 95 | Body inspected: incorrect hash size and changed file fail before output. |
| tests/usage-status-parts-cli.py | `test_invalid_schema_and_foreign_owner_are_rejected` | 95 | Body inspected: invalid schema and foreign owner are rejected. |
| tests/usage-status-parts-cli.py | `test_selected_bundle_diagnostic_must_match_owner` | 95 | Body inspected: selected bundle diagnostic must match owner. |
| tests/usage-status-parts-cli.py | `test_selected_bundle_quarantine_diagnostic_preserves_source_binding` | 95 | Body inspected: selected bundle quarantine diagnostic preserves source binding. |
| tests/usage-status-parts-cli.py | `test_symlink_selected_part_is_not_followed` | 95 | Body inspected: symlink selected part is not followed. |
| tests/usage-status-parts-cli.py | `test_declared_total_bytes_and_record_limit_are_enforced` | 95 | Body inspected: declared total bytes and record limit are enforced. |
| tests/usage-status-parts-cli.py | `test_parts_are_not_authorized_by_hash_or_receipt_alone` | 95 | Body inspected: parts are not authorized by hash or receipt alone. |
| tests/usage-status-revision.py | `test_status_proposal_is_exactly_one_successor_and_input_is_unchanged` | 95 | Body inspected: status proposal is exactly one successor and input is unchanged. |
| tests/usage-status-revision.py | `test_replayed_proposal_is_stale_after_owner_accepts_successor` | 95 | Body inspected: replayed proposal is stale after owner accepts successor. |
| tests/usage-status-revision.py | `test_unavailable_clock_still_proposes_one_revision_without_inventing_warning` | 95 | Body inspected: unavailable clock still proposes one revision without inventing warning. |
| tests/usage-status-scope-evidence.py | `test_scope_money_requires_independent_tool_coverage_and_owner` | 95 | Body inspected: scope money requires independent tool coverage and owner. |
| tests/usage-status-scope-evidence.py | `test_repricing_does_not_create_factual_scoped_spend_warning` | 95 | Body inspected: repricing does not create factual scoped spend warning. |
| tests/usage-status-scope-evidence.py | `test_span_needs_independently_verified_completion_for_token_warning` | 95 | Body inspected: span needs independently verified completion for token warning. |
| tests/usage-status-scoped-completeness.py | `test_distinct_and_unknown_scope_completeness` | 95 | Body inspected: distinct and unknown scope completeness. |
| tests/usage-stream-revisions.py | `test_final_snapshot_replaces_partial_snapshots_in_any_input_order` | 95 | Body inspected: final snapshot replaces partial snapshots in any input order. |
| tests/usage-stream-revisions.py | `test_partial_snapshot_follows_source_order_not_max_or_arrival` | 95 | Body inspected: partial snapshot follows source order not max or arrival. |
| tests/usage-stream-revisions.py | `test_missing_delta_sequence_is_partial_even_with_terminal` | 95 | Body inspected: missing delta sequence is partial even with terminal. |
| tests/usage-stream-revisions.py | `test_contiguous_deltas_count_duplicates_once` | 95 | Body inspected: contiguous deltas count duplicates once. |
| tests/usage-stream-revisions.py | `test_derived_delta_total_may_exceed_source_counter_limit` | 95 | Body inspected: derived delta total may exceed source counter limit. |
| tests/usage-stream-revisions.py | `test_same_observation_or_sequence_with_different_values_conflicts` | 95 | Body inspected: same observation or sequence with different values conflicts. |
| tests/usage-stream-revisions.py | `test_later_partial_event_cannot_preserve_earlier_finality` | 95 | Body inspected: later partial event cannot preserve earlier finality. |
| tests/usage-stream-revisions.py | `test_incompatible_finals_and_unverified_corrections_conflict` | 95 | Body inspected: incompatible finals and unverified corrections conflict. |
| tests/usage-stream-revisions.py | `test_verified_correction_chain_replaces_predecessors` | 95 | Body inspected: verified correction chain replaces predecessors. |
| tests/usage-stream-revisions.py | `test_correction_cycles_and_incompatible_successors_conflict` | 95 | Body inspected: correction cycles and incompatible successors conflict. |
| tests/usage-stream-revisions.py | `test_final_snapshot_and_deltas_do_not_double_count` | 95 | Body inspected: final snapshot and deltas do not double count. |
| tests/usage-stream-revisions.py | `test_partial_snapshots_and_deltas_do_not_prove_compatible_totals` | 95 | Body inspected: partial snapshots and deltas do not prove compatible totals. |
| tests/usage-stream-revisions.py | `test_empty_is_unavailable_and_mixed_responses_are_rejected` | 95 | Body inspected: empty is unavailable and mixed responses are rejected. |
| tests/usage-stream-revisions.py | `test_invalid_input_is_bounded_and_errors_do_not_expose_private_fields` | 95 | Body inspected: invalid input is bounded and errors do not expose private fields; count boundary uses a patched limit of two events and checks the production constant, without exercising a real 10001-event array. |
| tests/usage-typed-schema.py | `test_evidenced_zero_is_a_numeric_value` | 90 | Body inspected: evidenced zero is a numeric value. |
| tests/usage-typed-schema.py | `test_unavailable_measurement_has_reason_and_no_value` | 90 | Body inspected: unavailable measurement has reason and no value. |
| tests/usage-typed-schema.py | `test_all_measurement_states_preserve_supported_evidence` | 90 | Body inspected: all measurement states preserve supported evidence. |
| tests/usage-typed-schema.py | `test_counter_boundaries_and_invalid_values` | 95 | Body inspected: counter boundaries and invalid values. |
| tests/usage-typed-schema.py | `test_unavailable_placeholders_and_missing_reason_are_rejected` | 90 | Body inspected: unavailable placeholders and missing reason are rejected. |
| tests/usage-typed-schema.py | `test_invalid_state_and_unevidenced_zero_are_rejected` | 95 | Body inspected: invalid state and unevidenced zero are rejected. |
| tests/usage-typed-schema.py | `test_specified_reasons_are_typed_and_preserved` | 90 | Body inspected: specified reasons are typed and preserved. |
| tests/usage-typed-schema.py | `test_zero_evidence_rejects_paths_and_unknown_placeholders` | 95 | Body inspected: zero evidence rejects paths and unknown placeholders. |
| tests/usage-typed-schema.py | `test_evidence_requires_a_canonical_sha256_reference` | 95 | Body inspected: evidence requires a canonical sha256 reference. |
| tests/usage-typed-schema.py | `test_final_requires_value_and_conflicted_requires_reason` | 90 | Body inspected: final requires value and conflicted requires reason. |
| tests/usage-typed-schema.py | `test_duplicate_keys_are_rejected_before_measurement_validation` | 90 | Body inspected: duplicate keys are rejected before measurement validation. |
| tests/usage-unpriced-accepted-outcome.py | `test_fully_unpriced_accepted_work_is_unknown_not_zero` | 95 | Body inspected: fully unpriced accepted work is unknown not zero. |
| tests/usage-unpriced-report.py | `test_unselected_price_evidence_cannot_produce_a_zero_subtotal` | 95 | Body inspected: unselected price evidence cannot produce a zero subtotal. |
| tests/usage-unpriced-report.py | `test_untrusted_price_evidence_cannot_produce_a_zero_subtotal` | 95 | Body inspected: untrusted price evidence cannot produce a zero subtotal. |
| tests/usage-usage-publication.py | `test_authorized_bundle_is_installed_and_only_then_receipted` | 95 | Body inspected: authorized bundle is installed and only then receipted. |
| tests/usage-usage-publication.py | `test_disabled_or_unregistered_never_publishes_or_authorizes` | 95 | Body inspected: disabled or unregistered never publishes or authorizes. |
| tests/usage-usage-publication.py | `test_missing_untrusted_or_mismatched_provenance_rejected_before_writes` | 95 | Body inspected: missing untrusted or mismatched provenance rejected before writes. |
| tests/usage-usage-publication.py | `test_schema_size_and_privacy_checks_happen_before_any_write` | 95 | Checks invalid schema, privacy, and actual byte-limit rejection before publication. |
| tests/usage-usage-publication.py | `test_exact_duplicate_and_concurrent_attempts_install_one_file` | 95 | Body inspected: exact duplicate and concurrent attempts install one file. |
| tests/usage-usage-publication.py | `test_corrupt_or_symlink_existing_address_never_overwritten` | 95 | Body inspected: corrupt or symlink existing address never overwritten. |
| tests/usage-usage-publication.py | `test_symlinked_usage_directory_is_rejected` | 95 | Body inspected: symlinked usage directory is rejected. |
| tests/usage-usage-publication.py | `test_authorize_error_does_not_disclose_private_evidence` | 95 | Body inspected: authorize error does not disclose private evidence. |
| tests/usage-usage-publication.py | `test_existing_external_hardlink_is_not_accepted` | 95 | Body inspected: existing external hardlink is not accepted. |
| tests/usage-usage-publication.py | `test_concurrent_duplicate_does_not_conflict_with_writer_cleanup` | 95 | Body inspected: concurrent duplicate does not conflict with writer cleanup. |
| tests/usage-usage-publication.py | `test_substituted_temporary_name_cannot_enter_shared_store` | 95 | Body inspected: substituted temporary name cannot enter shared store. |
| tests/usage-usage-publication.py | `test_foreign_temporary_collision_is_never_deleted_or_modified` | 95 | Body inspected: foreign temporary collision is never deleted or modified. |
| tests/usage-usage-publication.py | `test_atomic_install_unavailable_fails_closed_without_receipt` | 95 | Body inspected: atomic install unavailable fails closed without receipt. |
| tests/usage-usage-publication.py | `test_failed_atomic_install_never_returns_receipt_or_changes_lifecycle` | 20 | Same patched _install OSError and identical no-artifact and lifecycle assertions as test_atomic_install_unavailable_fails_closed_without_receipt. Removed; covering test passed. |
| tests/usage-usage-receipt-schema.py | `test_complete_receipt_preserves_declarations_and_unknown_attribution` | 90 | Body inspected: complete receipt preserves declarations and unknown attribution. |
| tests/usage-usage-receipt-schema.py | `test_required_fields_versions_and_closed_shape` | 90 | Body inspected: required fields versions and closed shape. |
| tests/usage-usage-receipt-schema.py | `test_scope_is_declared_closed_and_has_explicit_quality` | 90 | Body inspected: scope is declared closed and has explicit quality. |
| tests/usage-usage-receipt-schema.py | `test_observation_count_and_duplicate_identifier_bounds` | 90 | Body inspected: observation count and duplicate identifier bounds. |
| tests/usage-usage-receipt-schema.py | `test_private_content_is_not_allowed_or_echoed` | 90 | Body inspected: private content is not allowed or echoed. |
| tests/usage-usage-receipt-schema.py | `test_raw_and_canonical_byte_limits_and_duplicate_json_keys` | 90 | Body inspected: raw and canonical byte limits and duplicate json keys. |
| tests/usage-usage-receipt-schema.py | `test_validation_does_not_infer_acceptance_from_process_status` | 90 | Body inspected: validation does not infer acceptance from process status. |
| tests/usage-usage-receipt-schema.py | `test_observation_identifiers_are_a_canonical_set` | 90 | Body inspected: observation identifiers are a canonical set. |
| tests/usage-usage-receipt-schema.py | `test_callers_cannot_override_receipt_set_order` | 90 | Body inspected: callers cannot override receipt set order. |
| tests/usage-warning-delivery-boundary.py | `test_private_state_owner_and_directory_boundary` | 95 | Body inspected: private state owner and directory boundary. |
| tests/usage-warning-delivery-boundary.py | `test_other_writable_note_is_not_a_valid_destination` | 95 | Body inspected: other writable note is not a valid destination. |
| tests/usage-warning-delivery-boundary.py | `test_detect_state_change_after_accept_before_touching_note` | 95 | Body inspected: detect state change after accept before touching note. |
| tests/usage-warning-delivery-boundary.py | `test_renamed_note_after_append_does_not_confirm_replacement` | 95 | Body inspected: renamed note after append does not confirm replacement. |
| tests/usage-warning-delivery-boundary.py | `test_cooperating_owner_writers_still_have_one_winner` | 20 | Calls test_concurrent_acceptance_has_single_winner directly on the same private temporary fixture; no new assertions. Removed; covering test passed. |
| tests/usage-warning-delivery-durability.py | `test_retry_remains_pending_until_marker_directory_is_synced` | 95 | Body inspected: retry remains pending until marker directory is synced. |
| tests/usage-warning-delivery-durability.py | `test_retry_remains_pending_when_existing_note_cannot_be_synced` | 95 | Body inspected: retry remains pending when existing note cannot be synced. |
| tests/usage-warning-delivery-durability.py | `test_retry_syncs_existing_note_and_directory_before_confirmation` | 95 | Body inspected: retry syncs existing note and directory before confirmation. |
| tests/usage-warning-delivery.py | `test_acceptance_precedes_note_and_marks_delivery_confirmed` | 95 | Body inspected: acceptance precedes note and marks delivery confirmed. |
| tests/usage-warning-delivery.py | `test_crash_after_accept_recovers_idempotently` | 95 | Body inspected: crash after accept recovers idempotently. |
| tests/usage-warning-delivery.py | `test_crash_after_note_before_confirmation_recovers_without_duplicate` | 95 | Body inspected: crash after note before confirmation recovers without duplicate. |
| tests/usage-warning-delivery.py | `test_missing_destination_stays_pending_and_reported_across_disable` | 95 | Body inspected: missing destination stays pending and reported across disable. |
| tests/usage-warning-delivery.py | `test_status_proposal_cannot_change_collection_or_evidence` | 95 | Body inspected: status proposal cannot change collection or evidence. |
| tests/usage-warning-delivery.py | `test_owner_and_scope_are_checked_before_any_side_effect` | 95 | Body inspected: owner and scope are checked before any side effect. |
| tests/usage-warning-delivery.py | `test_leaf_goes_only_to_matching_leaf_not_run_or_other_leaf` | 95 | Body inspected: leaf goes only to matching leaf not run or other leaf. |
| tests/usage-warning-delivery.py | `test_symlink_destination_never_modifies_its_target` | 95 | Body inspected: symlink destination never modifies its target. |
| tests/usage-warning-delivery.py | `test_stale_revision_is_rejected_without_overwriting_other_edit` | 95 | Body inspected: stale revision is rejected without overwriting other edit. |
| tests/usage-warning-delivery.py | `test_concurrent_acceptance_has_single_winner` | 95 | Body inspected: concurrent acceptance has single winner. |
| tests/usage-warning-delivery.py | `test_state_file_cannot_be_used_as_note_destination` | 95 | Body inspected: state file cannot be used as note destination. |
| tests/usage-warning-delivery.py | `test_short_write_keeps_retry_idempotent` | 95 | Body inspected: short write keeps retry idempotent. |
| tests/usage-warning-delivery.py | `test_pending_warning_cannot_be_erased_by_proposal` | 95 | Body inspected: pending warning cannot be erased by proposal. |
| tests/usage-warning-delivery.py | `test_lock_file_cannot_be_used_as_note_destination` | 95 | Body inspected: lock file cannot be used as note destination. |
| tests/usage-warning-delivery.py | `test_detectable_external_state_edit_before_replace_is_rejected` | 95 | Body inspected: detectable external state edit before replace is rejected. |
| tests/usage-warning-delivery.py | `test_note_rename_before_write_does_not_mutate_moved_file_or_confirm` | 95 | Body inspected: note rename before write does not mutate moved file or confirm. |
| tests/usage-warning-delivery.py | `test_private_payload_is_rejected_without_echo_or_write` | 95 | Body inspected: private payload is rejected without echo or write. |
| tests/usage-warning-policy-schema.py | `test_complete_policy_and_explicit_unknowns_are_preserved` | 90 | Body inspected: complete policy and explicit unknowns are preserved. |
| tests/usage-warning-policy-schema.py | `test_complete_fields_version_scope_and_time_are_required` | 90 | Body inspected: complete fields version scope and time are required. |
| tests/usage-warning-policy-schema.py | `test_threshold_types_ranges_units_and_unknown_fields` | 90 | Body inspected: threshold types ranges units and unknown fields. |
| tests/usage-warning-policy-schema.py | `test_historical_evidence_requires_scope_window_and_explicit_statistics` | 90 | Body inspected: historical evidence requires scope window and explicit statistics. |
| tests/usage-warning-policy-schema.py | `test_private_content_is_not_returned_in_validation_errors` | 90 | Body inspected: private content is not returned in validation errors. |
| tests/usage-warning-policy-schema.py | `test_identity_and_json_duplicate_and_size_limits` | 90 | Body inspected: identity and json duplicate and size limits. |

Inventoried and individually assessed all 529 original methods; confirmed exact duplicates are marked as removed.
