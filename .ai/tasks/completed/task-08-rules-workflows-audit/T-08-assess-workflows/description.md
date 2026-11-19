## Goal
The assessment holds complete per-item judgments for every workflow file, including the repetition review of every invocable workflow.

## Context
- Dependencies: T-07 (pinned inventory and assessment skeleton).
- Constraints: The auditor reads every assigned file in full and never edits an audited file; one writer of the assessment; judgments cite current `path:line` evidence; no count, kind or capability is taken from an earlier record or a harness name; no token count or monetary amount in any string; kinds are the eight of the specification's Terminology. Source contract: spec DM-7 and the Edge Cases table.
- Reason: The 42 workflow files are the larger reading group and the only ones with call pairs and repetition review; one done-state: no per-item diagnostic names a workflow.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** for every file under `workflows/`: `files` rows with kinds and evidence, `coverage` entries, `loads` entries, dispositions of `RL`, `FO` and `HN` candidates, legacy roles, the `repetition` record with three finding-id lists for every workflow with an `Invocation:` line and null for the reference document, findings for defect edges and for repeats found by reading, including load repeats deeper than one call step.
- **Out of scope:** rule and adapter files; duplicate groups, map, defaults, amendments, statement coverage; the report.
- **Target files:** `docs/audits/<run_date>-rules-workflows-audit.assessment.json`

## Steps
1. Run `verify` and save the diagnostics located in workflow files as the starting list.
2. Read the orchestrator workflows in full (`phase-*`, `spec-run`, `spec-draft`, `spec-sync`, `bugfix`, `restack`, `retro` and the other entry commands) and write their rows and coverage entries.
3. Read the Discovery, Execution and Validation child workflows (`pd-*`, `pe-*`, `pae-*`, `pav-*`, `pv-*`) in full and write their rows and coverage entries.
4. Read the utility and suggestion workflows and `workflows/PIPELINE.md` in full and write their rows and coverage entries.
5. Classify every load edge whose source is a workflow as `mandatory` or `conditional` with the condition text.
6. Disposition every `RL` candidate and every `FO` and `HN` candidate located in workflows; give legacy mentions their roles.
7. Examine every invocable workflow for repeated reports, repeated checkpoint or status records and repeated review of unchanged inputs; write the three lists and the findings they name with the default proposal owners.
8. Write findings for defect edges sourced in workflows and for load repeats found by reading.
9. Re-run `verify` and confirm that no diagnostic of the per-item rules names a workflow file.

## Acceptance Criteria
- The assessment has exactly one `files` row and one `coverage` entry per workflow path of the inventory.
- `repetition` is non-null exactly for the workflows whose inventory `invocation_lines` is greater than 0.
- Every `RL`, `FO` and `HN` id of the inventory has a `candidates` entry.
- Every proposal finding names its source path and section and exactly one owner from `11`, `12`, `13`, `15`, `14`.
- `verify` prints no `row-missing`, `row-extra`, `row-duplicate`, `load-unclassified`, `candidate-undisposed`, `repetition-invalid`, `legacy-role-missing`, `defect-unrecorded`, `finding-invalid`, `finding-stale`, `assessment-stale` or `coverage-inconsistent` diagnostic for the `files`, `coverage`, `loads`, `candidates`, `legacy` and `findings` keys.
- `git status --porcelain -- rules workflows harness templates tests hooks principles scripts` prints nothing.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - starting `verify` output lists diagnostics for workflow files; final output lists none of the per-item codes
  - row and coverage counts equal the inventory's workflow count
  - repetition present exactly for invocable workflows
  - every candidate id dispositioned
  - proposal owners within the allowed set
  - protected trees unchanged
- **Edge cases:** the reference document without an `Invocation:` line (null repetition, never a caller); call cycle between workflows; candidate inside a quoted stop message; workflow with no load edge; repeat more than one call level apart (finding without an `RL` id).
