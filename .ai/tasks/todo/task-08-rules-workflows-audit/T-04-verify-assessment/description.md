## Goal
`verify` reports every inconsistency between the inventory, the tree and the assessment's per-item judgments, one diagnostic per violation.

## Context
- Dependencies: T-03 (complete inventory and defect predicate).
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec DM-7 (assessment keys, finding types, owners, blocking predicate) and DM-9 codes other than the map, amendment, requirement-coverage and report codes.
- Reason: Assessment consistency is one verifiable component: for each rule there is a fixture that raises exactly its code, and a valid fixture raises none.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** the `verify` subcommand, option parsing, path derivation from `--report`, output order and exit codes; JSON parsing with duplicate keys rejected; schema and enum checks; staleness and work-tree checks including `--strict`; row completeness for `files` and `coverage`; sections, loads, candidates, repetition, legacy, duplicate groups, defect coverage, findings, coverage consistency, installed-copy and economics rules; a fixture builder that produces a fully valid inventory-assessment pair.
- **Out of scope:** map, deviation, amendment and requirement-coverage rules; report layout and the generated region; the `render` subcommand.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write a fixture builder for a valid assessment over a small fixture root, and failing cases that each break one rule.
2. Add `verify --root --report [--strict]`, derive the two JSON paths, and print diagnostics as `<code> <location> <message>` ordered by code then location; exit 0, 1 or 2 as the contract states.
3. Parse both JSON files rejecting duplicate keys; check keys, order-independent presence, types and enum values (`inventory-missing`, `assessment-missing`, `inventory-invalid`, `assessment-invalid`, `digest-mismatch`).
4. Check `inventory-stale` against the tree's audited paths and digests, the byte comparison under `--strict`, and `worktree-dirty`.
5. Check one `files` and one `coverage` row per audited path (`row-missing`, `row-extra`, `row-duplicate`), `assessment-stale`, and `sections-incomplete` for multi-kind rows and the two always-required files.
6. Check `load-unclassified`, `candidate-undisposed`, `repetition-invalid` and `legacy-role-missing`.
7. Check `duplicate-ungrouped`, `duplicate-multigrouped` and `group-invalid`.
8. Check `defect-unrecorded`, `finding-invalid` (owner by type, blocking predicate, severity, status, lines, section, and the rule for findings on edges outside the migration grammar), `finding-stale` and `reference-unknown` for findings, candidates and groups.
9. Check `coverage-inconsistent`, `installed-invalid` and `economics-claim` over every assessment string.
10. Confirm that `verify` creates and changes no file.

## Acceptance Criteria
- A fully valid fixture pair (with a placeholder for the parts checked by later subtasks) yields no diagnostic from the rules of this subtask.
- An assessment with a proposal finding whose owner is `09` yields `finding-invalid`.
- An assessment string `saves 3,000 tokens` or `$5` yields `economics-claim`.
- A two-kind fixture rule with three sections and `sections` covering two yields `sections-incomplete`.
- The control missing-heading edge with no finding naming it yields `defect-unrecorded`.
- A cluster in no group, in two groups, or in a `contradiction` group without a finding yields `duplicate-ungrouped`, `duplicate-multigrouped` or `group-invalid`.
- A load edge without a `loads` entry, a candidate without a disposition, and a legacy mention without a role yield `load-unclassified`, `candidate-undisposed` and `legacy-role-missing`.
- A coverage entry `unavailable` without a `coverage-gap` finding yields `coverage-inconsistent`.
- `installed_access: not-verified` with a non-empty `installed` list, or a location not starting `~/`, yields `installed-invalid`.
- A workflow with an `Invocation:` line and `repetition: null`, or a `repetition.report` id naming a `full-output` finding, yields `repetition-invalid`.
- A `09`-owned `reference-defect` finding on a `missing-path` edge from an active reader without an amendment id in `evidence`, a finding cited by an amendment with `blocks_09: false`, and a `minor` finding with `blocks_09: true` that nothing justifies each yield `finding-invalid`.
- Every code handled here has at least one fixture case that produces it, and `verify` leaves every file digest unchanged.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - valid fixture → no diagnostic of this subtask
  - wrong proposal owner → `finding-invalid`
  - economic strings → `economics-claim`
  - partial sections → `sections-incomplete`
  - unrecorded defect → `defect-unrecorded`
  - three duplicate faults → three codes
  - missing load class, disposition, legacy role → three codes
  - coverage gap without finding → `coverage-inconsistent`
  - installed faults → `installed-invalid`
  - repetition faults → `repetition-invalid`
  - three finding faults → `finding-invalid`
  - per-code cases exist; tree digests unchanged
- **Edge cases:** missing inventory or assessment file; unparseable JSON; duplicate JSON key; unknown and missing key; duplicate id; changed audited file; added and removed audited file; dirty and unknown work tree; symbolic-link entry with status other than `not-a-file`; `not-a-file` on a regular file; unknown id reference.
