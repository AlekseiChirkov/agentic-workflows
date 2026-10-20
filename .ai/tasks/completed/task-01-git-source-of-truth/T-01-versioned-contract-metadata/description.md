## Goal
Add a backward-compatible contract version to new task records and run logs, and warn when workflow rules change without a version update.

## Context
- Dependencies: none.
- Constraints: `VERSION` must contain `0.9.0`; readers must accept state and historical log records without `contract_version`; keep the validator's existing smoke suite passing.
- Reason: version metadata is a shared contract used by task analysis, run logging, and release checks.

Off-limits: do not rename the checkout or change user-facing package files; do not rewrite Git history or update the base branch.

## Scope
- **In scope:** create the contract version file, stamp task and run records, document the field, and implement the stale-rule warning.
- **Out of scope:** changing checkout or log-root environment variables, public documentation, and the physical directory move.
- **Target files:** VERSION, workflows/pd-analyze.md, log-step.sh, rules/run-log.md, validate-contracts.sh.

## Steps
1. Add the root `VERSION` file with the required contract value.
2. Update task analysis to read `VERSION` and write `contract_version:` immediately after `spec_path:` when a version is available.
3. Preserve compatibility with state files created before a version file exists.
4. Add `contract_version` to `log-step.sh run-start` events and document the field in the run-log contract.
5. Add a validator warning when a rules file has a later Git-history change than `VERSION` and the working-tree version remains unchanged.
6. Write smoke checks that fail on the current implementation before changing the implementation paths.
7. Implement the version stamping, logging, and warning behavior without changing unrelated log fields.
8. Run the full contract validator and Bash syntax checks.

## Acceptance Criteria
- `VERSION` exists at the repository root and contains exactly `0.9.0` followed by a newline.
- New task analyses write `contract_version: 0.9.0` immediately after `spec_path:` when `VERSION` is available; older task states without the field remain readable.
- A run-start event records the current contract version when available, and older events without that field remain valid.
- The validator warns when a rule changed after the last version change and the working-tree `VERSION` is unchanged, and emits no warning when the version is updated.
- The complete contract validator passes after implementation.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - `VERSION` contains the required value → a root-file assertion passes only for the exact value.
  - Task analysis with a version file → the generated state places `contract_version` after `spec_path`; without a version file → analysis continues and readers accept the missing field.
  - Run-start with a version file → JSON contains the exact contract version; a legacy event without it remains parseable.
  - A post-version rule commit with unchanged `VERSION` → validator emits a warning; changing `VERSION` in the worktree → warning clears.
  - Full contract validation → exits successfully.
- **Edge cases:** absent version file, empty or malformed version file, unchanged version with newer rules, version changed in the same worktree, legacy records.
