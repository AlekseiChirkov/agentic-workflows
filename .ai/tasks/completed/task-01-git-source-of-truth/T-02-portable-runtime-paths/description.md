## Goal
Make setup and logging scripts resolve from the Orchestrail checkout and use the new public environment-variable names while preserving existing override precedence.

## Context
- Dependencies: T-01 provides the root contract version file used by the relocated checkout.
- Constraints: the script directory is the default root; `ORCHESTRAIL_HOME` overrides it; `sync.sh --from` retains highest precedence; the log default is `<root>/logs` and `ORCHESTRAIL_LOG_ROOT` overrides it.
- Reason: setup must keep working after the checkout moves and across paths containing spaces or relative overrides.

Off-limits: do not change the scrub denylist, rewrite history, update `main`, or deploy harness files.

## Scope
- **In scope:** update root resolution, environment names, child setup propagation, and the documented configuration paths used by script helpers.
- **Out of scope:** README and LICENSE content, the broader remaining-name sweep, and GitHub repository identity.
- **Target files:** sync.sh, log-step.sh, setup-new-project.sh, setup-umbrella.sh, setup-all-repos.sh, link-skills.sh, validate-contracts.sh, rules/run-log.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-pipeline.md, workflows/phase-validation.md, workflows/spec-run.md, workflows/retro.md, workflows/pd-finalize.md, workflows/pe-finalize.md, .ai/context/environment.md, .ai/context/runbook.md.

## Steps
1. Inventory current root, log-store, and child-script override behavior in the six root shell scripts.
2. Change source-root selection to default to the script directory and accept `ORCHESTRAIL_HOME`.
3. Preserve `sync.sh --from` and `--from=...` as the highest-priority source overrides.
4. Change setup scripts to propagate the selected root consistently to child invocations.
5. Change the log-store default to `<root>/logs` and accept `ORCHESTRAIL_LOG_ROOT`.
6. Update workflow helper resolution and environment documentation to use the new variables and `~/.config/orchestrail/` paths.
7. Add smoke scenarios for relocated checkouts, paths with spaces, empty overrides, relative overrides, and precedence.
8. Run the relocated-checkout smoke scenarios, the complete contract validator, and Bash syntax checks.

## Acceptance Criteria
- All six root shell scripts run from a relocated checkout without machine-specific absolute paths.
- `ORCHESTRAIL_HOME` selects the source root for setup helpers; `sync.sh --from` overrides it for both supported option forms.
- `log-step.sh path` returns `<root>/logs` by default and the `ORCHESTRAIL_LOG_ROOT` value when set.
- Child setup invocations use the same resolved root, including when an override is relative and contains spaces.
- Workflow and environment instructions use the new variables and the `~/.config/orchestrail/` configuration root.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - Copy the checkout into a path with spaces and run the scripts from a separate working directory → each uses the relocated checkout by default.
  - Set `ORCHESTRAIL_HOME` and pass `--from` in both forms → the CLI-selected source wins.
  - Set `ORCHESTRAIL_LOG_ROOT` → the read-only path command returns it; omit it → the path is `<root>/logs`.
  - Use a relative source override with spaces and invoke umbrella setup → parent and child initialize from the same resolved source.
  - Inspect workflow and environment instructions → new variable and config paths are present and old defaults are absent.
- **Edge cases:** checkout paths with spaces, empty values, missing override directories, relative paths, CLI precedence, child propagation, read-only path lookup.
