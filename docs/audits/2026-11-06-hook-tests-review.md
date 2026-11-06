# Hook test review

Static method inventory. Scores are provided only after manual reading; methods marked Not assessed have not been individually evaluated. The descriptive evidence labels are automated navigation aids, not individual findings. No exact AST-body duplicates were detected across these five suites.

| File | Test method | Score | Evidence in test body | Review status |
|---|---|---:|---|---|
| hook-install.sh | test_hook_install_unsupported_python_preserves_settings_and_ownership | 95 | Checks install unsupported python preserves settings and ownership. | Reviewed statically |
| hook-install.sh | test_hook_uninstall_unsupported_python_preserves_settings_and_ownership | 95 | Checks uninstall unsupported python preserves settings and ownership. | Reviewed statically |
| hook-install.sh | test_hook_unusable_python_reports_unsupported_before_either_operation | 95 | Checks unusable python reports unsupported before either operation. | Reviewed statically |
| hook-install.sh | test_hook_installer_functions_follow_public_python_standards | 60 | Source-style constraints; does not exercise behavior. | Reviewed statically |
| hook-install.sh | test_hook_install_repeated_lifecycle_preserves_unrelated_settings | 95 | Checks install repeated lifecycle preserves unrelated settings. | Reviewed statically |
| hook-install.sh | test_hook_install_preexisting_identical_entries_remain_unowned | 95 | Checks install preexisting identical entries remain unowned. | Reviewed statically |
| hook-install.sh | test_hook_uninstall_changed_and_moved_entries_survive | 95 | Checks uninstall changed and moved entries survive. | Reviewed statically |
| hook-install.sh | test_hook_uninstall_equal_copies_preserve_unowned_multiplicity_and_empty_groups | 95 | Checks uninstall equal copies preserve unowned multiplicity and empty groups. | Reviewed statically |
| hook-install.sh | test_hook_uninstall_removes_only_created_newly_empty_groups | 95 | Checks uninstall removes only created newly empty groups. | Reviewed statically |
| hook-install.sh | test_hook_install_source_precedence_and_quoted_paths_use_literal_arguments | 95 | Checks install source precedence and quoted paths use literal arguments. | Reviewed statically |
| hook-install.sh | test_hook_install_invalid_cli_and_manifest_never_mutate_settings | 95 | Checks install invalid cli and manifest never mutate settings. | Reviewed statically |
| hook-install.sh | test_hook_install_upgrade_preserves_changed_old_handler | 95 | Checks install upgrade preserves changed old handler. | Reviewed statically |
| hook-install.sh | test_hook_install_malformed_settings_preserve_exact_bytes | 95 | Checks install malformed settings preserve exact bytes. | Reviewed statically |
| hook-install.sh | test_hook_install_malformed_receipt_preserves_both_files | 95 | Checks install malformed receipt preserves both files. | Reviewed statically |
| hook-install.sh | test_hook_receipt_control_numbers_cannot_gain_deletion_ownership | 95 | Checks receipt control numbers cannot gain deletion ownership. | Reviewed statically |
| hook-install.sh | test_hook_ownership_object_equality_ignores_key_order_and_numeric_spelling | 95 | Checks ownership object equality ignores key order and numeric spelling. | Reviewed statically |
| hook-install.sh | test_hook_ownership_omitted_fields_and_changed_argument_arrays_remain_unowned | 95 | Checks ownership omitted fields and changed argument arrays remain unowned. | Reviewed statically |
| hook-install.sh | test_hook_recovery_before_image_restores_previous_then_recomputes_install | 95 | Checks recovery before image restores previous then recomputes install. | Reviewed statically |
| hook-install.sh | test_hook_recovery_after_image_finalizes_then_recomputes_install | 95 | Checks recovery after image finalizes then recomputes install. | Reviewed statically |
| hook-install.sh | test_hook_recovery_external_edit_preserves_settings_and_prepared_receipt | 95 | Checks recovery external edit preserves settings and prepared receipt. | Reviewed statically |
| hook-install.sh | test_hook_recovery_uninstall_uses_saved_state_after_old_source_disappears | 95 | Checks recovery uninstall uses saved state after old source disappears. | Reviewed statically |
| hook-install.sh | test_hook_recovery_malformed_prepared_receipt_never_replaces_settings | 95 | Checks recovery malformed prepared receipt never replaces settings. | Reviewed statically |
| hook-install.sh | test_hook_transaction_interruption_before_settings_recovers_absent_image | 95 | Checks transaction interruption before settings recovers absent image. | Reviewed statically |
| hook-install.sh | test_hook_transaction_interruption_after_settings_recovers_committed_image | 95 | Checks transaction interruption after settings recovers committed image. | Reviewed statically |
| hook-install.sh | test_hook_transaction_rechecks_before_image_after_preparing_ownership | 95 | Checks transaction rechecks before image after preparing ownership. | Reviewed statically |
| hook-install.sh | test_hook_transaction_replacement_failure_preserves_settings_and_allows_retry | 95 | Checks transaction replacement failure preserves settings and allows retry. | Reviewed statically |
| hook-install.sh | test_hook_install_preserves_exact_json_numbers_and_strings | 95 | Checks install preserves exact json numbers and strings. | Reviewed statically |
| hook-install.sh | test_hook_install_missing_dependencies_report_unavailable_without_mutation | 95 | Checks install missing dependencies report unavailable without mutation. | Reviewed statically |
| hook-install.sh | test_hook_install_concurrent_operations_are_serialized_and_parseable | 95 | Checks install concurrent operations are serialized and parseable. | Reviewed statically |
| hook-install.sh | test_hook_uninstall_recovers_without_native_dependencies_but_requires_python | 85 | Checks uninstall recovers without native dependencies but requires python. | Reviewed statically |
| hook-install.sh | test_hook_receipt_literal_null_is_invalid_and_nullable_next_recovers_absence | 95 | Checks receipt literal null is invalid and nullable next recovers absence. | Reviewed statically |
| hook-install.sh | test_hook_manifest_and_capabilities_describe_available_mechanism_and_partial_coverage | 85 | Checks manifest and capabilities describe available mechanism and partial coverage. | Reviewed statically |
| hook-install.sh | test_hook_setup_registers_canonical_roots_idempotently_and_adapter_gates | 85 | Checks setup registers canonical roots idempotently and adapter gates. | Reviewed statically |
| hook-install.sh | test_hook_setup_trailing_newline_is_rejected_and_sibling_prefix_stays_inactive | 85 | Checks setup trailing newline is rejected and sibling prefix stays inactive. | Reviewed statically |
| hook-install.sh | test_hook_setup_concurrent_registration_preserves_existing_roots | 95 | Checks setup concurrent registration preserves existing roots. | Reviewed statically |
| hook-install.sh | test_hook_setup_default_config_location_preserves_custom_project_files | 95 | Checks setup default config location preserves custom project files. | Reviewed statically |
| hook-install.sh | test_hook_setup_invalid_registry_or_newline_root_preserves_existing_entries | 95 | Checks setup invalid registry or newline root preserves existing entries. | Reviewed statically |
| hook-install.sh | test_hook_sync_embeds_capabilities_once_and_preserves_all_deployment_targets | 95 | Checks sync embeds capabilities once and preserves all deployment targets. | Reviewed statically |
| hook-install.sh | test_hook_sync_unavailable_installation_still_refreshes_consumer_projects | 95 | Checks sync unavailable installation still refreshes consumer projects. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_manifest_registers_blocking_bash_handler_beside_logging | 85 | Checks git rails manifest registers blocking bash handler beside logging. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_fresh_install_adds_one_owned_group_and_repeats_byte_identically | 85 | Checks git rails fresh install adds one owned group and repeats byte identically. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_install_without_hooks_key_creates_every_manifest_event | 85 | Checks git rails install without hooks key creates every manifest event. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_registration_uses_the_physical_entrypoint_beside_its_core | 95 | Checks git rails registration uses the physical entrypoint beside its core. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_symlinked_entrypoint_is_never_registered_alone | 95 | Checks git rails symlinked entrypoint is never registered alone. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_source_without_entrypoint_or_core_is_rejected_without_writes | 95 | Checks git rails source without entrypoint or core is rejected without writes. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_malformed_manifest_variants_are_rejected_without_writes | 95 | Checks git rails malformed manifest variants are rejected without writes. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_malformed_settings_never_receive_a_partial_registration | 95 | Checks git rails malformed settings never receive a partial registration. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_foreign_pretooluse_entries_survive_install_and_removal | 95 | Checks git rails foreign pretooluse entries survive install and removal. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_identical_foreign_handlers_keep_multiset_quotas | 95 | Checks git rails identical foreign handlers keep multiset quotas. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_logging_only_receipt_upgrades_on_reinstall | 95 | Checks git rails logging only receipt upgrades on reinstall. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_registration_preserves_numeric_lexemes | 95 | Checks git rails registration preserves numeric lexemes. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_interrupted_replacements_recover | 95 | Checks git rails interrupted replacements recover. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_concurrent_edit_during_registration_is_not_overwritten | 95 | Checks git rails concurrent edit during registration is not overwritten. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_concurrent_operations_keep_one_owned_registration | 95 | Checks git rails concurrent operations keep one owned registration. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_uninstall_ignores_the_manifest_and_removes_owned_entries | 95 | Checks git rails uninstall ignores the manifest and removes owned entries. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_changed_owned_handler_survives_removal | 95 | Checks git rails changed owned handler survives removal. | Reviewed statically |
| hook-install.sh | test_hook_git_rails_fail_open_pretooluse_handler_is_rejected_without_writes | 25 | Both variants covered by malformed manifest and failure-mode tests. | Removed; retained checks passed |
| hook-install.sh | test_hook_git_rails_pretooluse_group_without_matcher_is_rejected_without_writes | 95 | Checks git rails pretooluse group without matcher is rejected without writes. | Reviewed statically |
| hook-install.sh | test_hook_install_unreadable_entrypoint_is_invalid_source_without_writes | 95 | Checks install unreadable entrypoint is invalid source without writes. | Reviewed statically |
| hook-install.sh | test_hook_install_readable_non_executable_entrypoint_is_registered_and_runs | 95 | Checks install readable non executable entrypoint is registered and runs. | Reviewed statically |
| hook-install.sh | test_hook_install_symlinked_hooks_directory_registers_physical_scripts | 95 | Checks install symlinked hooks directory registers physical scripts. | Reviewed statically |
| hook-install.sh | test_hook_install_blocking_logging_handler_is_invalid_manifest_without_writes | 95 | Checks install blocking logging handler is invalid manifest without writes. | Reviewed statically |
| hook-install.sh | test_hook_install_failure_modes_outside_each_event_mode_are_invalid_manifest | 95 | Checks install failure modes outside each event mode are invalid manifest. | Reviewed statically |
| hook-install.sh | test_hook_permissions_fragment_holds_only_exact_staging_and_commit_all_rules | 95 | Checks permissions fragment holds only exact staging and commit all rules. | Reviewed statically |
| hook-install.sh | test_hook_permissions_fixtures_are_hook_denials_and_negatives_are_not | 95 | Checks permissions fixtures are hook denials and negatives are not. | Reviewed statically |
| hook-install.sh | test_hook_permissions_install_adds_owned_deny_rules_with_version_two_receipt | 95 | Checks permissions install adds owned deny rules with version two receipt. | Reviewed statically |
| hook-install.sh | test_hook_permissions_foreign_rules_and_other_lists_survive_in_order | 95 | Checks permissions foreign rules and other lists survive in order. | Reviewed statically |
| hook-install.sh | test_hook_permissions_quota_keeps_identical_user_copies_and_tolerates_removed_rules | 95 | Checks permissions quota keeps identical user copies and tolerates removed rules. | Reviewed statically |
| hook-install.sh | test_hook_permissions_missing_or_empty_containers_are_restored_exactly | 95 | Checks permissions missing or empty containers are restored exactly. | Reviewed statically |
| hook-install.sh | test_hook_permissions_malformed_settings_are_rejected_without_writes | 95 | Checks permissions malformed settings are rejected without writes. | Reviewed statically |
| hook-install.sh | test_hook_permissions_malformed_fragment_is_rejected_without_writes | 95 | Checks permissions malformed fragment is rejected without writes. | Reviewed statically |
| hook-install.sh | test_hook_permissions_wildcard_and_nested_rules_are_invalid_manifest_without_writes | 95 | Checks permissions wildcard and nested rules are invalid manifest without writes. | Reviewed statically |
| hook-install.sh | test_hook_permissions_receipt_claims_are_validated_before_use | 95 | Checks permissions receipt claims are validated before use. | Reviewed statically |
| hook-install.sh | test_hook_permissions_version_one_receipt_is_read_and_migrated | 95 | Checks permissions version one receipt is read and migrated. | Reviewed statically |
| hook-install.sh | test_hook_permissions_prepared_version_one_receipt_recovers_then_migrates | 95 | Checks permissions prepared version one receipt recovers then migrates. | Reviewed statically |
| hook-install.sh | test_hook_permissions_interrupted_migration_recovers_from_either_image | 95 | Checks permissions interrupted migration recovers from either image. | Reviewed statically |
| hook-install.sh | test_hook_permissions_concurrent_edit_is_not_overwritten | 95 | Checks permissions concurrent edit is not overwritten. | Reviewed statically |
| hook-install.sh | test_hook_permissions_concurrent_operations_keep_one_copy_of_each_rule | 95 | Checks permissions concurrent operations keep one copy of each rule. | Reviewed statically |
| hook-install.sh | test_hook_permissions_uninstall_ignores_the_fragment | 95 | Checks permissions uninstall ignores the fragment. | Reviewed statically |
| hook-timing.sh | test_timing_sequential_complete_uses_exact_wall_denominator | 90 | Complete sequential spans, totals, coverage and worker identity. | Reviewed statically |
| hook-timing.sh | test_timing_successive_actor_spans_preserve_gaps_without_waiting | 90 | Separated spans retain gaps, denominator and worker sum. | Reviewed statically |
| hook-timing.sh | test_timing_nested_reference_subtracts_waiting_from_direct_parent | 90 | Nested waiting and work preserve distinct exclusive totals. | Reviewed statically |
| hook-timing.sh | test_timing_same_actor_overlap_retains_union_and_distinct_actor_parallelism | 90 | Same-actor overlap is not claimed as valid exclusive work. | Reviewed statically |
| hook-timing.sh | test_timing_invalid_component_reference_preserves_disconnected_root | 90 | Invalid tree does not poison independent valid root. | Reviewed statically |
| hook-timing.sh | test_timing_parallel_roots_allow_worker_sum_above_wall | 90 | Parallel actors can have worker totals above wall time. | Reviewed statically |
| hook-timing.sh | test_timing_waiting_sum_and_union_are_independent_of_active_work | 90 | Waiting union and active work remain separate. | Reviewed statically |
| hook-timing.sh | test_timing_unknown_session_span_contributes_only_observed_coverage | 90 | Unnamed session evidence does not invent named steps. | Reviewed statically |
| hook-timing.sh | test_timing_measured_span_approximation_markers_are_exact | 90 | Exact approximation marker and context syntax are classified. | Reviewed statically |
| hook-timing.sh | test_timing_unmarked_legacy_and_missing_interval_remain_unmeasured | 90 | Incomplete legacy data never becomes exact measurement. | Reviewed statically |
| hook-timing.sh | test_timing_invalid_producer_fields_exclude_entire_lines | 90 | Invalid fields reject spans and preserve exact invalid counts. | Reviewed statically |
| hook-timing.sh | test_timing_large_integer_totals_and_ratios_are_lossless_strings | 90 | Totals and ratios remain exact beyond safe integer range. | Reviewed statically |
| hook-timing.sh | test_timing_historical_integral_lexemes_preserve_exact_endpoints | 90 | Historical integral decimal strings retain exact values. | Reviewed statically |
| hook-timing.sh | test_timing_fractional_nonfinite_boolean_or_out_of_bounds_spans_are_excluded | 90 | Invalid numeric forms do not create spans. | Reviewed statically |
| hook-timing.sh | test_timing_out_of_run_or_reversed_spans_do_not_create_groups | 90 | Out-of-window and reversed spans are not counted. | Reviewed statically |
| hook-timing.sh | test_timing_zero_wall_and_endpoint_spans_have_unavailable_ratios | 90 | Zero denominator yields unavailable ratios. | Reviewed statically |
| hook-timing.sh | test_timing_zero_length_children_at_parent_end_remain_valid | 90 | Zero-length child at parent boundary stays valid. | Reviewed statically |
| hook-timing.sh | test_timing_waiting_only_observations_establish_zero_active_work | 90 | Waiting-only data shows observed but zero active work. | Reviewed statically |
| hook-timing.sh | test_timing_zero_length_cycles_still_quarantine_exclusive_metrics | 90 | Zero-duration cycle cannot claim exclusive metrics. | Reviewed statically |
| hook-timing.sh | test_timing_duplicate_checkpoints_collapse_generated_variations | 90 | Duplicate checkpoints ignore generated fields. | Reviewed statically |
| hook-timing.sh | test_timing_conflicting_checkpoint_delivery_fields_exclude_entire_key | 90 | Conflicting checkpoint payloads suppress the key. | Reviewed statically |
| hook-timing.sh | test_timing_duplicate_numeric_equality_uses_exact_mathematical_values | 90 | Equivalent and different numeric lexemes are compared exactly. | Reviewed statically |
| hook-timing.sh | test_timing_boundaries_require_unique_substantive_equality | 90 | Conflicting start/end events invalidate metrics. | Reviewed statically |
| hook-timing.sh | test_timing_identical_boundaries_collapse_only_generated_fields | 90 | Repeated identical boundaries remain measurable. | Reviewed statically |
| hook-timing.sh | test_timing_unusable_or_missing_boundaries_never_invent_denominators | 90 | Missing and invalid boundaries remain unavailable. | Reviewed statically |
| hook-timing.sh | test_timing_metadata_presence_and_exact_strings_control_attribution | 90 | Conflicting attribution labels do not contribute spans. | Reviewed statically |
| hook-timing.sh | test_timing_omitted_optional_metadata_and_start_only_labels_are_supported | 90 | Optional historical metadata absence remains compatible. | Reviewed statically |
| hook-timing.sh | test_timing_parent_cycles_missing_or_cross_session_links_quarantine_components | 90 | Invalid parent graphs quarantine components. | Reviewed statically |
| hook-timing.sh | test_timing_same_actor_and_step_partial_components_keep_totals_unavailable | 90 | Partial graph retains valid spans but rejects misleading totals. | Reviewed statically |
| hook-timing.sh | test_timing_parent_containment_failure_keeps_raw_union_only | 90 | Invalid temporal containment keeps raw union only. | Reviewed statically |
| hook-timing.sh | test_timing_rejected_child_tombstone_excludes_valid_parent_exclusive_time | 90 | Rejected child prevents unsafe parent exclusive claim. | Reviewed statically |
| hook-timing.sh | test_timing_invalid_child_endpoint_quarantines_transitive_siblings | 90 | Bad child endpoint propagates graph uncertainty. | Reviewed statically |
| hook-timing.sh | test_timing_conflicting_parent_declarations_quarantine_every_connected_component | 90 | Conflicting parent claims poison both affected components. | Reviewed statically |
| hook-timing.sh | test_timing_opaque_rejected_evidence_makes_exclusive_graph_unverified | 90 | Opaque malformed evidence blocks exclusive graph claims. | Reviewed statically |
| hook-timing.sh | test_timing_rejected_uncorrelated_legacy_rows_do_not_hide_graph_edges | 90 | Unrelated rejected legacy rows do not poison graph. | Reviewed statically |
| hook-timing.sh | test_timing_explicit_files_deduplicate_paths_without_discovering_store | 90 | Explicit selections deduplicate symlinks without discovery. | Reviewed statically |
| hook-timing.sh | test_timing_cross_file_and_intra_file_run_identity_conflicts_are_unavailable | 90 | Same identity in conflicting files cannot produce metrics. | Reviewed statically |
| hook-timing.sh | test_timing_same_basename_distinct_runs_remain_independent | 90 | Distinct runs with the same basename remain separate. | Reviewed statically |
| hook-timing.sh | test_timing_input_errors_never_look_like_clean_empty_corpus | 95 | Invalid inputs do not become clean empty results. | Reviewed statically |
| hook-timing.sh | test_timing_end_of_options_accepts_literal_dash_path | 90 | Literal dash path works after option terminator. | Reviewed statically |
| hook-timing.sh | test_timing_missing_python_jq_and_unsupported_python_return_null | 90 | Missing or unsupported runtime tools fail closed. | Reviewed statically |
| hook-timing.sh | test_timing_incomplete_or_malformed_lint_never_authorizes_metrics | 95 | Incomplete lint cannot authorize metrics. | Reviewed statically |
| hook-timing.sh | test_timing_invalid_lint_references_and_unique_counts_are_rejected | 90 | Malformed lint locations and counts reject metrics. | Reviewed statically |
| hook-timing.sh | test_timing_known_lint_violations_remain_lower_bounds_when_summary_fails | 90 | Partial lint preserves lower bounds without false exactness. | Reviewed statically |
| hook-timing.sh | test_timing_physical_lf_lines_and_unterminated_final_record_are_exact | 90 | Physical and unterminated line counts remain correct. | Reviewed statically |
| hook-timing.sh | test_timing_snapshot_mutation_or_inventory_change_invalidates_coverage | 95 | Snapshot content and inventory mutation invalidate metrics. | Reviewed statically |
| hook-timing.sh | test_timing_snapshot_is_private_byte_exact_and_cleaned_after_lint | 95 | Private snapshot is byte exact, permissioned, and removed. | Reviewed statically |
| hook-timing.sh | test_timing_contract_export_must_be_usable_and_fetched_once | 90 | Malformed contract fails closed; valid contract fetched once. | Reviewed statically |
| hook-timing.sh | test_timing_retro_docs_preserve_loader_and_describe_honest_measures | 65 | Documentation exposes timing concepts and reachable loader. | Reviewed statically |
| hook-timing.sh | test_timing_python_and_introduced_fixtures_have_complete_annotations | 65 | Checks source function annotations and style limits. | Reviewed statically |
| hook-timing.sh | test_timing_two_run_lifecycle_preserves_attribution_fallback_and_owned_settings | 90 | End-to-end two-run flow preserves attribution and settings. | Reviewed statically |
| hook-shell-quality.sh | test_native_shell_functions_meet_focused_limits | 65 | Checks lexical complexity limits of native adapter functions. | Reviewed statically |
| hook-shell-quality.sh | test_correlated_shell_functions_meet_focused_limits | 65 | Checks function size and arguments with pinned baseline exceptions. | Reviewed statically |
| hook-shell-quality.sh | test_hook_metadata_api_uses_at_most_three_parameters | 25 | Parameter bound is already enforced for every function; extra internal-name requirement is incidental. | Removed; retained check passed |
| hook-workflow-contract.sh | test_unavailable_hooks_keep_every_prompt_step_approximate | 85 | Runs unavailable fixtures and verifies approximate logging instructions. | Reviewed statically |
| hook-workflow-contract.sh | test_batches_and_absent_red_do_not_claim_named_coverage | 90 | Tests ambiguous native skills and absent RED, with workflow contract. | Reviewed statically |
| hook-workflow-contract.sh | test_dispatch_report_status_preserve_one_delivery_route | 95 | Covers accepted, missing, retry, malformed, and failed fallback routes. | Reviewed statically |
| hook-workflow-contract.sh | test_hook_documentation_distinguishes_named_and_unknown_session_coverage | 65 | Checks consistency of user-visible coverage documentation. | Reviewed statically |
| hook-workflow-contract.sh | test_hook_documentation_separates_native_and_legacy_dependencies | 65 | Checks published runtime dependency distinctions. | Reviewed statically |
| log-step-hook.sh | test_hook_dispatch_private_correlation_is_explicit | 95 | Checks private mode, missing session, and no writes. | Reviewed statically |
| log-step-hook.sh | test_hook_interleaved_runs_preserve_exact_identity | 95 | Checks independent identity and timestamps across interleaved runs. | Reviewed statically |
| log-step-hook.sh | test_hook_concurrent_duplicate_deliveries_append_once | 95 | Races duplicate delivery and checks one event. | Reviewed statically |
| log-step-hook.sh | test_hook_closed_run_delivery_never_reopens | 90 | Rejects writes after run closure. | Reviewed statically |
| log-step-hook.sh | test_hook_missing_and_conflicting_native_fields_preserve_pending | 95 | Rejects malformed identity and wrong project without mutation. | Reviewed statically |
| log-step-hook.sh | test_hook_inactive_project_gates_before_transcript_and_state_reads | 95 | FIFO and snapshots prove early project gate and no reads. | Reviewed statically |
| log-step-hook.sh | test_hook_session_unknown_and_unique_skill_remain_distinct | 90 | Distinguishes unknown session, named skill, and missing subagent skill. | Reviewed statically |
| log-step-hook.sh | test_hook_native_schema_and_input_limits_warn_safely | 90 | Rejects malformed and oversized input, then verifies recovery. | Reviewed statically |
| log-step-hook.sh | test_hook_bounded_transcript_tail_requires_dispatch_input | 90 | Rejects dispatch outside simulated bounded tail. | Reviewed statically |
| log-step-hook.sh | test_hook_accepted_status_blocks_fallback_and_returns_receipt | 95 | Accepted receipt blocks a subsequent fallback. | Reviewed statically |
| log-step-hook.sh | test_hook_fallback_first_owns_route_even_when_legacy_write_fails | 95 | Asserts one fallback route and unconfirmed producer handling. | Reviewed statically |
| log-step-hook.sh | test_hook_frozen_retry_requires_matching_receipt | 95 | Proves exact payload retry and receipt matching. | Reviewed statically |
| log-step-hook.sh | test_hook_marker_canonicality_and_exact_tuple_reject_ambiguity | 95 | Rejects duplicate, noncanonical, and mismatched report markers. | Reviewed statically |
| log-step-hook.sh | test_hook_native_evidence_uses_input_and_unique_invocation_ids | 95 | Rejects unrelated input, conflicting invocations, and wrong skills. | Reviewed statically |
| log-step-hook.sh | test_hook_registered_roots_choose_most_specific_and_reject_changed_owner | 95 | Tests nested project ownership and registration changes. | Reviewed statically |
| log-step-hook.sh | test_hook_invalid_fallback_arguments_leave_pending_and_unmutated | 90 | Invalid fallback values preserve pending state. | Reviewed statically |
| log-step-hook.sh | test_hook_fallback_and_native_delivery_concurrently_choose_one_route | 95 | Races routes and verifies exactly one persisted event. | Reviewed statically |
| log-step-hook.sh | test_hook_missing_hook_dependencies_leave_store_unchanged | 90 | Dependency failure keeps event store and pending state. | Reviewed statically |
| log-step-hook.sh | test_hook_byte_limits_and_native_identity_preserve_exact_bytes | 90 | Rejects oversized payload, NUL, and invalid identity. | Reviewed statically |
| log-step-hook.sh | test_hook_predispatch_and_tool_result_evidence_do_not_count | 95 | Distinguishes native input from old or tool-result evidence. | Reviewed statically |
| log-step-hook.sh | test_hook_explicit_waiting_and_parent_survive_out_of_order_delivery | 90 | Checks parent linkage and waiting span under out-of-order delivery. | Reviewed statically |
| log-step-hook.sh | test_hook_missing_start_time_rejects_before_delivery | 90 | Missing timestamp cannot forward event. | Reviewed statically |
| log-step-hook.sh | test_hook_receipt_must_be_one_matching_object_with_integer_sequence | 95 | Rejects malformed and mismatched receipts before acceptance. | Reviewed statically |
| log-step-hook.sh | test_hook_delivering_retries_survive_rotation_and_reject_changed_report_or_actor | 95 | Checks stable retries across transcript rotation and conflicting actors. | Reviewed statically |
| log-step-hook.sh | test_hook_unicode_json_byte_limit_is_not_character_limit | 95 | UTF-8 byte bound cannot be bypassed with multibyte characters. | Reviewed statically |
| log-step-hook.sh | test_hook_skill_name_suffix_is_rejected_without_normalization | 85 | Rejects newline-suffixed skill identity. | Reviewed statically |
| log-step-hook.sh | test_hook_corrupted_frozen_payload_or_receipt_never_changes_run_attribution | 95 | Rejects tampered frozen payload and receipt without writes. | Reviewed statically |
| log-step-hook.sh | test_hook_report_short_fence_candidates_keep_marker_in_code | 90 | Short delimiters cannot close a larger code fence. | Reviewed statically |
| log-step-hook.sh | test_hook_report_nonclosing_fence_suffixes_and_tabs_keep_marker_in_code | 90 | Rejects false fence closers and tab-indented variants. | Reviewed statically |
| log-step-hook.sh | test_hook_report_real_matching_or_longer_closers_allow_outside_marker | 85 | Accepts actual fence closers and outside markers. | Reviewed statically |
| log-step-hook.sh | test_hook_report_openers_respect_indentation_and_info_string_syntax | 90 | Checks real and invalid fence openers. | Reviewed statically |
| log-step-hook.sh | test_hook_report_line_separators_preserve_fence_and_marker_boundaries | 85 | Accepts markers after fences with CR and CRLF. | Reviewed statically |
| log-step-hook.sh | test_hook_raw_fractional_or_exponent_receipt_sequence_leaves_delivery_uncertain | 90 | Rejects noncanonical numeric receipt from producer. | Reviewed statically |
| log-step-hook.sh | test_hook_raw_noncanonical_cached_receipt_sequence_never_returns_acceptance | 90 | Rejects the same number forms in cached receipt. | Reviewed statically |
| log-step-hook.sh | test_hook_raw_noncanonical_cached_start_never_forwards_frozen_payload | 90 | Rejects noncanonical frozen start time without writes. | Reviewed statically |
| log-step-hook.sh | test_hook_raw_noncanonical_cached_end_never_forwards_frozen_payload | 90 | Rejects noncanonical frozen end time without writes. | Reviewed statically |
| log-step-hook.sh | test_hook_fresh_schema_version_requires_exact_integer_token | 90 | Rejects noninteger lexical schema versions at both interfaces. | Reviewed statically |
| log-step-hook.sh | test_hook_documented_dispatch_marker_and_ownership_contract | 65 | Checks published interface tokens, not runtime semantics. | Reviewed statically |

## Limitations

- Method bodies and associated fixture helpers were reviewed statically; scores are judgments, not performance measurements or proof of complete semantic equivalence.
- Exact AST body matches are only a lead: equivalent bodies with different fixtures can test distinct behavior. No exact matches occurred here.
- No method receives a deletion score at or below 30 without demonstrated redundancy and matching fixtures.
