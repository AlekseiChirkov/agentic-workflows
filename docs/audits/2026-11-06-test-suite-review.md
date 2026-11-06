# Test suite necessity review

Ratings express necessity from 0 to 100, not measured speed. The removal threshold is 25. Child-suite dispatch tests remain necessary because they are the registered route to those suites. Timings of individual cases were not measured.

| File | Line | Test | Score | Decision | Reason |
|---|---:|---|---:|---|---|
| tests/validator-runtime-version-isolation.py | 14 | test_inherited_log_root_is_untouched | 95 | Keep | Prevents a reproduced write into the caller's log store. |
| tests/validator-runtime-oracle.py | — | test_version_fixture_isolates_inherited_log_root | 90 | Keep | Runs the isolated log-root regression in the ordinary validation route. |
| tests/validator-runtime-oracle.py | — | test_amendment_pins_unrelated_fields_order_and_resource_changes | 90 | Keep | Rejects unrelated drift while allowing the reviewed inventory amendment. |
| tests/validator-runtime-oracle.py | — | test_unapproved_nonstandard_check_is_rejected | 85 | Keep | Rejects unapproved changes to nonstandard check syntax. |
| tests/validator-runtime-guard-regressions.py | — | test_shell_focused_dispatch_depends_on_first_argument | 95 | Keep | Prevents a reproduced unbounded shell invocation from passing inspection. |
| tests/validator-runtime-guard-regressions.py | — | test_python_focused_dispatch_depends_on_first_argument | 95 | Keep | Prevents a reproduced unbounded Python subprocess from passing inspection. |
| tests/validator-runtime-guard-regressions.py | — | test_python_executable_override_requires_review | 95 | Keep | Rejects executable overrides that can bypass focused dispatch. |
| tests/validator-runtime-guard-regressions.py | — | test_python_shell_mode_requires_review_unless_false | 95 | Keep | Rejects shell mode when the apparent arguments are not forwarded. |
| tests/validator-runtime-guard-regressions.py | — | test_python_keyword_args_obey_focused_dispatch | 95 | Keep | Inspects subprocess commands supplied through the args keyword. |
| tests/validator-runtime-guard-regressions.py | — | test_python_shell_output_helpers_require_review | 95 | Keep | Rejects unclassified validator runs through shell output helpers. |
| tests/validator-runtime-allowlist-guard.py | 18 | test_wrapper_and_unsupported_checks_fail_closed | 60 | Keep | Inventory mutation contract |
| tests/validator-runtime-allowlist-shell.py | 17 | test_command_lists_do_not_hide_checks | 60 | Keep | Shell syntax mutation contract |
| tests/validator-runtime-allowlist.py | 18 | test_runtime_additions_have_exact_expressions_order_and_positions | 70 | Keep | Inventory placement and mutation contract |
| tests/validator-runtime-characterization.py | 75 | test_counts_lines_case_and_final_line | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 87 | test_independent_sorted_scanner_rows | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 110 | test_sorted_rows_for_binary_paths_and_symlink | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 133 | test_bytes_paths_and_empty_file | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 142 | test_missing_ledger_path_fails | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 148 | test_nul_split_and_symlink_target | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 157 | test_grep_failure_is_not_a_clean_scan | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 169 | test_ledger_mask_preserves_line_numbers | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 178 | test_sort_failure_does_not_report_success | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 189 | test_available_utf8_locale | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 200 | test_run_log_extraction_markers_and_standalone_syntax | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 218 | test_generic_wrapper_suppresses_diagnostics | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 229 | test_wrapper_excerpt_conventions | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 246 | test_conditional_command_substitution_isolated_under_errexit | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 258 | test_result_channels_and_counters | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 267 | test_focused_exec_forwards_arguments_and_exit | 80 | Keep | Behavior characterization |
| tests/validator-runtime-characterization.py | 287 | test_focused_chained_and_bash_dispatch | 80 | Keep | Behavior characterization |
| tests/validator-runtime-guard-dynamic.py | 18 | test_unclassified_dynamic_executable_requires_review | 70 | Keep | Dynamic execution guard |
| tests/validator-runtime-guard-dynamic.py | 23 | test_dynamic_command_positions_require_review | 70 | Keep | Dynamic execution guard |
| tests/validator-runtime-guard-dynamic.py | 29 | test_generated_source_dependency_drift_is_rejected | 70 | Keep | Dynamic execution guard |
| tests/validator-runtime-guard-dynamic.py | 49 | test_exact_classification_rejects_drift_duplicate_and_stale_entry | 70 | Keep | Dynamic execution guard |
| tests/validator-runtime-guard-production.py | 18 | test_exact_context_and_count_and_stale_exceptions | 70 | Keep | Guard exception binding |
| tests/validator-runtime-guard-production.py | 41 | test_new_full_call_is_not_authorized_by_existing_exception | 70 | Keep | Guard exception binding |
| tests/validator-runtime-guard-regressions.py | 18 | test_split_shell_executable_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 22 | test_validator_alias_executed_in_assignment_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 26 | test_split_shell_alias_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 30 | test_shell_alias_split_inside_path_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 34 | test_python_indirect_subprocess_callable_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 38 | test_python_indirect_concatenated_path_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 42 | test_cli_scans_project_with_pinned_classifications | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 48 | test_python_subprocess_callable_assignment_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 52 | test_shell_command_substitution_text_is_not_a_literal_argument | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 56 | test_python_import_alias_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 60 | test_python_command_alias_is_not_silent | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 64 | test_shell_c_tail_is_not_inner_validator_argument | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 68 | test_python_shell_c_tail_is_not_inner_validator_argument | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 72 | test_redirect_target_is_not_a_focused_argument | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 76 | test_only_real_arguments_authorize_focused_dispatch | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 80 | test_inventory_reads_regular_project_sources | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 92 | test_warning_exception_rejects_duplicate_container | 70 | Keep | Guard regression |
| tests/validator-runtime-guard-regressions.py | 96 | test_warning_exception_is_not_portable_to_other_path | 70 | Keep | Guard regression |
| tests/validator-runtime-guard.py | 32 | test_rejects_full_direct_copied_and_alias_calls | 80 | Keep | Nested execution guard |
| tests/validator-runtime-guard.py | 42 | test_accepts_supported_focused_flag_on_actual_argv | 80 | Keep | Nested execution guard |
| tests/validator-runtime-guard.py | 52 | test_inspects_multiline_python_argv_and_comments_as_data | 80 | Keep | Nested execution guard |
| tests/validator-runtime-guard.py | 59 | test_rejects_three_untrimmed_history_calls | 80 | Keep | Nested execution guard |
| tests/validator-runtime-guard.py | 65 | test_stub_exception_is_exact_and_stale_entries_fail | 80 | Keep | Nested execution guard |
| tests/validator-runtime-guard.py | 79 | test_guarded_history_is_bound_to_context_and_exact_count | 80 | Keep | Nested execution guard |
| tests/validator-runtime-identity.py | 93 | test_success_matches_original_loop | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 101 | test_full_ledger_discovery_and_symlink | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 166 | test_registered_check_ignores_external_source_override | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 183 | test_git_fixture_ignores_hostile_environment | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 202 | test_input_read_error_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 209 | test_partial_normalization_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 213 | test_partial_aggregation_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 217 | test_normalized_open_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 220 | test_matches_open_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 223 | test_actual_open_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-identity.py | 226 | test_grep_failure_fails | 90 | Keep | Scanner behavior and error handling |
| tests/validator-runtime-integrated.py | 19 | test_source_guard_wrapper_emits_no_success_text | 75 | Keep | Integrated registration or wrapper behavior |
| tests/validator-runtime-integrated.py | 33 | test_registration_and_wrapper_mutations_are_rejected | 75 | Keep | Integrated registration or wrapper behavior |
| tests/validator-runtime-oracle.py | 33 | test_runtime_security | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 38 | test_runtime_allowlist | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 43 | test_runtime_allowlist_guard | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 48 | test_runtime_shell_guard | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 53 | test_integrated_registrations | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 59 | test_runtime_wrapper_shadow | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 64 | test_sourceguard_allowlist | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 95 | test_runtime_checks_registered_once_after_focused_dispatch | 55 | Keep | Unique relation to focused dispatch; inventory stores dispatch and results separately. |
| tests/validator-runtime-oracle.py | 104 | test_result_extraction_distinguishes_nested_diagnostics | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 111 | test_time_output_fields_are_parsed_and_missing_fields_fail | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 120 | test_nonfinite_sample_values_are_rejected | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 127 | test_evidence_checks_file_bytes_digests_result_inventory_and_median | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 191 | test_frozen_source_detects_actual_name_expression_and_order_changes | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 218 | test_inventory_contains_all_source_contracts | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 228 | test_matching_inventory_is_accepted | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 234 | test_independent_name_expression_and_order_mutations_rejected | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 252 | test_two_consistent_successful_samples_accepted | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 255 | test_incomplete_failed_or_drifted_manifest_rejected | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-oracle.py | 275 | test_high_variance_requires_third_retained_sample | 75 | Keep | Equivalence, evidence, or child-suite dispatch |
| tests/validator-runtime-security.py | 27 | test_git_environment_cannot_redirect_fixture | 75 | Keep | Isolation and integrity |
| tests/validator-runtime-security.py | 48 | test_import_does_not_write_bytecode | 75 | Keep | Isolation and integrity |
| tests/validator-runtime-security.py | 63 | test_inventory_digest_rejects_valid_modified_data | 75 | Keep | Isolation and integrity |
| tests/validator-runtime-sourceguard-allowlist.py | 18 | test_registration_is_required_and_immutable | 65 | Keep | Guard registration integrity |
| tests/validator-runtime-warning-fingerprint.py | 17 | test_approved_prefix_runs_with_pinned_digest | 85 | Keep | Approved prefix integrity and behavior |
| tests/validator-runtime-warning-fingerprint.py | 22 | test_unapproved_prefix_changes_fail_closed | 85 | Keep | Approved prefix integrity and behavior |
| tests/validator-runtime-warning-guard.py | 20 | test_early_compound_checks_are_rejected | 65 | Keep | Prefix safety or bytecode isolation |
| tests/validator-runtime-warning-guard.py | 28 | test_isolation_suite_creates_no_bytecode | 65 | Keep | Prefix safety or bytecode isolation |
| tests/validator-runtime-warning-isolation.py | 20 | test_indented_early_check_is_rejected | 75 | Keep | Fixture isolation |
| tests/validator-runtime-warning-isolation.py | 27 | test_inherited_git_environment_cannot_redirect_fixture | 75 | Keep | Fixture isolation |
| tests/validator-runtime-warning-operators.py | 17 | test_compound_command_operators_are_rejected | 60 | Keep | Prefix command operator handling |
| tests/validator-runtime-warning-strict.py | 17 | test_indirect_early_checks_fail_closed | 65 | Keep | Prefix syntax handling |
| tests/validator-runtime-warning-strict.py | 28 | test_nested_anchor_is_rejected_before_execution | 65 | Keep | Prefix syntax handling |
| tests/validator-runtime-warning.py | 49 | test_missing_duplicate_and_early_check_are_rejected | 85 | Keep | Warning behavior and failure detection |
| tests/validator-runtime-warning.py | 58 | test_post_cut_sentinel_never_runs | 85 | Keep | Warning behavior and failure detection |
| tests/validator-runtime-warning.py | 65 | test_warning_mutations_fail_the_original_assertions | 85 | Keep | Warning behavior and failure detection |
| tests/validator-runtime-wrapper-shadow.py | 17 | test_indented_and_function_definitions_are_rejected | 60 | Keep | Wrapper source integrity |
| tests/validator-runtime-warning.py | — | test_real_prefix_preserves_all_three_states | 25 | Remove | The pinned-digest test executes the same three states and is stronger. |
| tests/validator-runtime-warning-isolation.py | — | test_warning_contract_registered_once | 20 | Remove | The integrated inventory checks warning registration and the pinned wrapper body. |
| tests/validator-runtime-guard-dynamic.py | — | test_dynamic_command_exception_is_context_bound | 10 | Remove | The remaining exact-classification test exercises the same exception matcher and failure states. |
| tests/usage-observation-bundle-schema.py | — | test_observation_json_input_byte_limit | 20 | Remove | The multibyte input test checks the same API and exact byte-limit boundary. |

## Preliminary file-level review

The table below assesses each file as a whole, based on its purpose and scenarios. It is not an individual review of every method or parameter value. Scores are subjective necessity estimates, not measured runtime. Files not listed here have not been individually assessed. Imported fixture modules are not standalone tests.

| File | Score | Decision | Basis |
|---|---:|---|---|
| tests/usage-accepted-outcomes.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-alert-status.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-analysis-corpus-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-analyze-cli-errors.py | 80 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-analyze-cli-evidence.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-attribution-schema.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-authority-permit.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-authority-rsa.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-authority-rsa-permit.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-bounded-source-reads.py | 100 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-canonical-encoding.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-causal-ownership.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-collection-segment-schema.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-collection-segments.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-context-evidence-timing.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-contract-export.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-cumulative-epochs.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-current-run-snapshot-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-diagnostic-registry.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-diagnostic-schema.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-duration-analysis.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-duration-warnings.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-empty-retrospective.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-entity-schemas.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-exact-cost.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-fixed-corpus.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-frozen-context-evidence.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-frozen-pricing-inputs.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-group-statistics.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-inventory-completeness.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-inventory-schema.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-legacy-recovery.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-authority.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection-no-prices.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection-schema.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection-states.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection-token-scalars.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-lifecycle-projection-trust.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-multibundle-report.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-normalize-cli.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-observation-bundle-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-offline-acceptance.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-outcome-tool-cost.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-outcome-unattributed-workload.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-ownership-empty-scope.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-price-applicability.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-price-evidence-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-price-snapshot-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-pricing-scenario-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-epochs.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-epochs-bundle.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-epochs-cli.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-measurement-finality.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-resolution.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-producer-streams.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-publication-cli.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-publication-close-nonblocking.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-publication-late-import.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-publication-provenance.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-publication-run-race.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-consumer.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-dimensions.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-epochs.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-evidence-fields.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-exports.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-multibundle-fields.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-optional-pricing.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-overlap-ownership.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-report-overlap-tools.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-cache-capabilities.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-conditional.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-correction-order.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-coverage.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-empty-scope.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-epochs.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-evidence.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-integration.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-measurement-finality.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-no-prices.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-ownership.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-partial-stream.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-privacy.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-regressions.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-report-evidence.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-response-details.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-revisions.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-token-components.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-tokens.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-tool-ownership.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolution-tools.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-resolved-report-integration.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-response-identity.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-retrospective-integration.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-retrospective-outcome-timing.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-source-normalization.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-source-profiles.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-source-selection.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-canonical-bindings.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-cli-integration.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-coverage-integration.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-delivery-integration.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-duration-integration.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-duration-kinds.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-duration-precision.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-fraction-coverage.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-input-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-integration.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-large-authority.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-large-parts.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-multiple-bundles.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-no-pricing.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-output-relocation.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-owner-scopes.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-parts-cli.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-revision.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-scope-evidence.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-status-scoped-completeness.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-stream-revisions.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-typed-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-unpriced-accepted-outcome.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-unpriced-report.py | 85 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-usage-publication.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-usage-receipt-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-warning-delivery.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-warning-delivery-boundary.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-warning-delivery-durability.py | 95 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-warning-policy-schema.py | 90 | Keep | Domain contract and distinct failure scenarios |
| tests/usage-rsa-fixture.py | n/a | Keep | Shared helper, not a standalone test |
| tests/usage-status-fixtures.py | n/a | Keep | Shared helper, not a standalone test |

## Other reviewed suites

| Suite | Score | Basis |
|---|---:|---|
| tests/git-rails.sh | 95 | Security decisions and fail-closed Git behavior; expensive parameterized cases |
| tests/hook-install.sh | 92 | Installation, recovery, races and permission handling |
| tests/log-step-hook.sh | 90 | Correlation and delivery without duplicates |
| tests/hook-timing.sh | 85 | Timing boundaries and lifecycle |
| tests/hook-workflow-contract.sh | 75 | Workflow contracts and ownership |
| tests/hook-shell-quality.sh | 65 | Static project standards |
| tests/log-step.sh | 88 | Isolated acceptance harness |
| tests/model-catalog.py | 90 | Catalog validation and explicit timing contract |
| tests/model-selection.py | 95 | Eligibility and fail-closed selection |
| tests/model-plan.py | 95 | Plan parsing and model eligibility |
| tests/model-workflow.py | 75 | Workflow instruction contracts |
| tests/workflow-instructions.py | 75 | Instruction reachability and bootstrap contracts |

The individual review of 513 syntactic shell-validator checks is in `2026-11-06-inline-test-review.md`. Individual usage, Git and hook reviews are in the adjacent audit files. Scores for acceptance wrappers assess their registration; loops within a test method are evaluated with their parent rather than as separately named tests. The removed cases are documented in the individual tables. Reduced status fixtures preserve relative size-boundary behavior but no longer prove acceptance above the absolute 1 MiB threshold. A separate small fixture exercises repeated short reads and digest verification. Reduced byte-limit tests assert production constant values and exercise the same branches at small limits, but do not test inputs at the actual byte limits. Collection-count tests use synthetic reported lengths; they do not exercise real arrays of 10,000 elements. Two exact-arithmetic tests now use two large values instead of 1,025 intervals, preserving a sum above the safe integer range but not the large-input exercise. Model selection now exercises pairwise score combinations and global extremes instead of every seven-factor combination. After the audit changes, the ordinary complete run passed in 568.838 seconds with 717 passed, 0 failed and 2 skips; the skips require local private hygiene patterns. The earlier 699.721-second run predates these changes.

## Individual model and workflow checks

Scope: individual executable checks; scores are judgment of behavioral necessity, not coverage percentages.
Scores at or below 30 are candidates for removal. A performance bound may be useful as an optional benchmark, but its wall-clock threshold is sensitive to host load.

| File | Test or check | Score | Distinct behavior or reason |
|---|---|---:|---|
| tests/model-catalog.py | `test_catalog_age_boundaries_report_exact_usable_statuses` | 90 | catalog age boundaries report exact usable statuses. |
| tests/model-catalog.py | `test_missing_malformed_future_dates_report_selection_unavailable` | 90 | missing malformed future dates report selection unavailable. |
| tests/model-catalog.py | `test_missing_catalog_default_path_preserves_absent_configuration` | 85 | missing catalog default path preserves absent configuration. |
| tests/model-catalog.py | `test_strict_schema_identity_and_vocabulary_reject_invalid_payloads` | 95 | strict schema identity and vocabulary reject invalid payloads. |
| tests/model-catalog.py | `test_markdown_payload_and_derived_tier_table_drift_are_rejected` | 85 | markdown payload and derived tier table drift are rejected. |
| tests/model-catalog.py | `test_capability_and_price_evidence_validate_dates_types_and_references` | 90 | capability and price evidence validate dates types and references. |
| tests/model-catalog.py | `test_unknown_price_availability_and_capability_remain_unknown` | 90 | unknown price availability and capability remain unknown. |
| tests/model-catalog.py | `test_oversized_price_reports_unavailable_and_preserves_failed_refresh` | 85 | oversized price reports unavailable and preserves failed refresh. |
| tests/model-catalog.py | `test_equal_relative_cost_preserves_independently_evidenced_quality` | 75 | equal relative cost preserves independently evidenced quality. |
| tests/model-catalog.py | `test_inspection_is_offline_readonly_and_repeatable` | 85 | inspection is offline readonly and repeatable. |
| tests/model-catalog.py | `test_valid_refresh_installs_validated_candidate_with_same_directory_replacement` | 95 | valid refresh installs validated candidate with same directory replacement. |
| tests/model-catalog.py | `test_invalid_or_missing_refresh_candidate_preserves_previous_bytes` | 95 | invalid or missing refresh candidate preserves previous bytes. |
| tests/model-catalog.py | `test_failed_replacement_preserves_catalog_and_cleans_temporary_file` | 95 | failed replacement preserves catalog and cleans temporary file. |
| tests/model-catalog.py | `test_windows_newline_candidate_is_inspected_and_installed_consistently` | 80 | windows newline candidate is inspected and installed consistently. |
| tests/model-catalog.py | `test_failed_temporary_cleanup_reports_error_and_preserves_previous_catalog` | 85 | failed temporary cleanup reports error and preserves previous catalog. |
| tests/model-catalog.py | `test_refresh_creates_missing_directory_only_after_candidate_validation` | 90 | refresh creates missing directory only after candidate validation. |
| tests/model-catalog.py | `test_cli_inspection_and_explicit_refresh_report_json_and_exit_status` | 90 | cli inspection and explicit refresh report json and exit status. |
| tests/model-catalog.py | `test_repeated_warm_isolated_lookup_measures_less_than_one_second` | 70 | The completed catalog contract explicitly requires a measured warm lookup below one second; the threshold remains host-load-sensitive. |
| tests/model-selection.py | `test_floor_pairwise_scores_have_exact_bounded_weighted_result` | 85 | floor pairwise scores have exact bounded weighted result; pairwise sample, not exhaustive. |
| tests/model-selection.py | `test_floor_pairwise_worsening_neighbors_never_decrease_requirement` | 85 | floor pairwise worsening neighbors never decrease requirement; pairwise sample, not exhaustive. |
| tests/model-selection.py | `test_floor_invalid_scores_and_unknown_constraints_are_rejected` | 90 | floor invalid scores and unknown constraints are rejected. |
| tests/model-selection.py | `test_floor_hard_categories_require_five_even_with_easy_creative_work` | 95 | floor hard categories require five even with easy creative work. |
| tests/model-selection.py | `test_eligibility_actual_availability_is_required_before_economics` | 95 | eligibility actual availability is required before economics. |
| tests/model-selection.py | `test_eligibility_context_tools_owner_and_quality_precede_economics` | 95 | eligibility context tools owner and quality precede economics. |
| tests/model-selection.py | `test_eligibility_unknown_limits_and_empty_allowlist_do_not_admit_candidates` | 95 | eligibility unknown limits and empty allowlist do not admit candidates. |
| tests/model-selection.py | `test_economics_price_band_equal_prices_and_unknown_prices_retain_default` | 85 | economics price band equal prices and unknown prices retain default. |
| tests/model-selection.py | `test_economics_qualified_comparable_total_cost_can_recommend_cheaper_model` | 90 | economics qualified comparable total cost can recommend cheaper model. |
| tests/model-selection.py | `test_economics_incomparable_or_unqualified_evidence_retains_default` | 90 | economics incomparable or unqualified evidence retains default. |
| tests/model-selection.py | `test_economics_equal_overlapping_invalid_and_missing_totals_retain_default` | 90 | economics equal overlapping invalid and missing totals retain default. |
| tests/model-selection.py | `test_economics_stronger_first_remains_selectable_with_qualified_lower_total` | 85 | economics stronger first remains selectable with qualified lower total. |
| tests/model-selection.py | `test_default_missing_or_unsuitable_uses_strongest_eligible_without_invented_identity` | 90 | default missing or unsuitable uses strongest eligible without invented identity. |
| tests/model-selection.py | `test_traits_legacy_mapping_is_explicit_and_unknown_conflicts_are_rejected` | 85 | traits legacy mapping is explicit and unknown conflicts are rejected. |
| tests/model-selection.py | `test_traits_each_override_filters_support_without_bypassing_quality_floor` | 90 | traits each override filters support without bypassing quality floor. |
| tests/model-selection.py | `test_identity_same_id_different_providers_is_never_conflated` | 95 | identity same id different providers is never conflated. |
| tests/model-selection.py | `test_request_invalid_snapshot_requirements_and_owner_shapes_are_rejected` | 90 | request invalid snapshot requirements and owner shapes are rejected. |
| tests/model-selection.py | `test_selection_is_offline_readonly_repeatable_and_does_not_mutate_inputs` | 85 | selection is offline readonly repeatable and does not mutate inputs. |
| tests/model-selection.py | `test_cli_selection_reports_recommendation_and_refuses_refresh_combination_before_writes` | 90 | cli selection reports recommendation and refuses refresh combination before writes. |
| tests/model-selection.py | `test_request_dated_harness_snapshot_cannot_authorize_current_selection` | 90 | request dated harness snapshot cannot authorize current selection. |
| tests/model-plan.py | `test_legacy_reordered_columns_read_exact_active_provider_requests` | 85 | legacy reordered columns read exact active provider requests. |
| tests/model-plan.py | `test_dual_columns_override_conflicting_legacy_by_active_provider` | 90 | dual columns override conflicting legacy by active provider. |
| tests/model-plan.py | `test_absent_empty_and_placeholder_models_mean_explicit_session_default` | 90 | absent empty and placeholder models mean explicit session default. |
| tests/model-plan.py | `test_escaped_pipes_fenced_examples_and_composite_blanks_preserve_rows` | 85 | escaped pipes fenced examples and composite blanks preserve rows. |
| tests/model-plan.py | `test_malformed_and_ambiguous_tables_are_rejected_before_reading` | 90 | malformed and ambiguous tables are rejected before reading. |
| tests/model-plan.py | `test_bulk_additions_preserve_unknown_columns_statuses_and_composite_blanks` | 95 | bulk additions preserve unknown columns statuses and composite blanks. |
| tests/model-plan.py | `test_existing_provider_updates_preserve_every_untouched_byte_and_allow_clear` | 95 | existing provider updates preserve every untouched byte and allow clear. |
| tests/model-plan.py | `test_legacy_migration_requires_explicit_values_for_each_added_provider` | 90 | legacy migration requires explicit values for each added provider. |
| tests/model-plan.py | `test_invalid_bulk_updates_leave_original_plan_bytes_unchanged` | 95 | invalid bulk updates leave original plan bytes unchanged. |
| tests/model-plan.py | `test_atomic_replace_failure_preserves_plan_and_cleans_staging_file` | 95 | atomic replace failure preserves plan and cleans staging file. |
| tests/model-plan.py | `test_exact_requested_identity_resolves_without_economic_substitution` | 95 | exact requested identity resolves without economic substitution. |
| tests/model-plan.py | `test_identity_uses_provider_and_exact_id_without_provider_switching` | 95 | identity uses provider and exact id without provider switching. |
| tests/model-plan.py | `test_unsupported_request_stops_visibly_without_undeclared_or_unauthorized_fallback` | 95 | unsupported request stops visibly without undeclared or unauthorized fallback. |
| tests/model-plan.py | `test_authorized_declared_suitable_fallback_is_visible_and_never_actual` | 95 | authorized declared suitable fallback is visible and never actual. |
| tests/model-plan.py | `test_fallback_independently_obeys_support_quality_context_tools_owner_and_traits` | 95 | fallback independently obeys support quality context tools owner and traits. |
| tests/model-plan.py | `test_session_default_resolves_only_its_own_suitable_identity_or_stops` | 90 | session default resolves only its own suitable identity or stops. |
| tests/model-plan.py | `test_stale_support_and_malformed_resolution_inputs_fail_explicitly` | 90 | stale support and malformed resolution inputs fail explicitly. |
| tests/model-plan.py | `test_actual_requires_fresh_separate_evidence_of_the_authorized_resolved_identity` | 95 | actual requires fresh separate evidence of the authorized resolved identity. |
| tests/model-plan.py | `test_resolution_is_pure_without_network_files_processes_or_input_mutation` | 85 | resolution is pure without network files processes or input mutation. |
| tests/model-plan.py | `test_cli_read_update_and_resolve_are_explicit_json_operations` | 90 | cli read update and resolve are explicit json operations. |
| tests/model-plan.py | `test_cli_rejects_invalid_updates_and_reports_unavailable_support_without_writes` | 95 | cli rejects invalid updates and reports unavailable support without writes. |
| tests/model-plan.py | `test_cli_auxiliary_flags_are_validated_before_any_mutation` | 95 | cli auxiliary flags are validated before any mutation. |
| tests/model-plan.py | `test_cli_stale_support_preserves_requested_identity_and_error_reason` | 90 | cli stale support preserves requested identity and error reason. |
| tests/model-plan.py | `test_unbounded_last_row_is_rejected_before_atomic_updates` | 90 | unbounded last row is rejected before atomic updates. |
| tests/model-plan.py | `test_indented_code_table_is_preserved_and_never_read_as_a_plan` | 85 | indented code table is preserved and never read as a plan. |
| tests/model-workflow.py | `test_selector_cached_single_bulk_contract_is_compact_and_reachable` | 70 | selector cached single bulk contract is compact and reachable. |
| tests/model-workflow.py | `test_selector_explicit_refresh_research_preserves_failed_install` | 75 | selector explicit refresh research preserves failed install. |
| tests/model-workflow.py | `test_selector_unavailable_dependencies_preserve_session_without_eligibility_bypass` | 85 | selector unavailable dependencies preserve session without eligibility bypass. |
| tests/model-workflow.py | `test_selector_explicit_refresh_recovers_catalog_before_selection_availability_guard` | 80 | selector explicit refresh recovers catalog before selection availability guard. |
| tests/model-workflow.py | `test_canonical_model_columns_define_empty_precedence_and_explicit_migration` | 80 | canonical model columns define empty precedence and explicit migration. |
| tests/model-workflow.py | `test_canonical_resolution_requires_invocation_support_permissions_and_restrictions` | 90 | canonical resolution requires invocation support permissions and restrictions. |
| tests/model-workflow.py | `test_canonical_resolution_separates_request_resolution_and_observed_actual` | 95 | canonical resolution separates request resolution and observed actual. |
| tests/model-workflow.py | `test_execution_readers_resolve_before_request_and_preserve_inline_session` | 90 | execution readers resolve before request and preserve inline session. |
| tests/model-workflow.py | `test_spec_run_unavailable_model_override_preserves_worker_role_boundaries` | 95 | spec run unavailable model override preserves worker role boundaries. |
| tests/model-workflow.py | `test_quickstart_unavailable_override_requires_authorized_default_worker_or_stop` | 90 | quickstart unavailable override requires authorized default worker or stop. |
| tests/model-workflow.py | `test_installed_callers_resolve_guide_from_the_verified_helper_source_root` | 85 | installed callers resolve guide from the verified helper source root. |
| tests/model-workflow.py | `test_installed_guidance_preflight_uses_configured_or_known_source_not_cwd` | 90 | installed guidance preflight uses configured or known source not cwd. |
| tests/model-workflow.py | `test_installed_guidance_missing_root_guide_schema_or_rubric_preserves_inputs` | 95 | installed guidance missing root guide schema or rubric preserves inputs. |
| tests/model-workflow.py | `test_spec_run_leaf_model_intent_excludes_arbiter_and_independent_validator_defaults` | 95 | spec run leaf model intent excludes arbiter and independent validator defaults. |
| tests/model-workflow.py | `test_discovery_and_quickstart_readers_preserve_optional_columns_and_staleness` | 80 | discovery and quickstart readers preserve optional columns and staleness. |
| tests/model-workflow.py | `test_operating_documents_reach_cached_guide_and_drop_retired_contract` | 70 | operating documents reach cached guide and drop retired contract. |
| tests/model-workflow.py | `test_guide_documents_age_quality_economics_migration_and_ownership` | 70 | guide documents age quality economics migration and ownership. |
| tests/model-workflow.py | `test_guide_cli_refresh_success_and_rejection_preserve_prior_bytes` | 80 | guide cli refresh success and rejection preserve prior bytes. |
| tests/model-workflow.py | `test_guide_cli_plan_compatibility_and_migration_are_explicit` | 80 | guide cli plan compatibility and migration are explicit. |
| tests/model-workflow.py | `test_guide_cli_resolution_surfaces_request_fallback_stop_and_unknown_actual` | 90 | guide cli resolution surfaces request fallback stop and unknown actual. |
| tests/model-workflow.py | `test_guide_cli_default_path_and_missing_dependencies_preserve_session` | 90 | guide cli default path and missing dependencies preserve session. |
| tests/model-workflow.py | `test_guide_cli_current_support_tools_and_unknown_quality_cannot_be_inferred` | 90 | guide cli current support tools and unknown quality cannot be inferred. |
| tests/model-workflow.py | `test_guide_timing_labels_measured_fixture_and_unmeasured_live_target` | 45 | guide timing labels measured fixture and unmeasured live target. |
| tests/model-workflow.py | `test_contract_gate_rejects_broken_helper_canonical_reader_and_guide_links` | 85 | contract gate rejects broken helper canonical reader and guide links. |
| tests/workflow-instructions.py | `entry_errors` (script check) | 75 | Checks required invocation and guard headings across workflow entry points. |
| tests/workflow-instructions.py | `reference_errors` (script check) | 80 | Checks named canonical section references when their source exists. |
| tests/workflow-instructions.py | `bootstrap_errors` (script check) | 85 | Checks phase bootstrap, inherited context and specific known path/classifier regressions. |

## Limits and suggested actions

- The 100-lookup one-second assertion is retained because the catalog specification explicitly requires the measured bound. Its sensitivity to host load remains a limitation.
- The two model-selection floor checks cover every pair of factor values and global extrema, not all 78,125 factor combinations.
- Guide example scenarios remain separate, while one cached example execution per test process supplies independent deep copies of its reports.
- `workflow-instructions.py` contains no `test_*` methods; the rows above describe its three directly invoked check functions.
