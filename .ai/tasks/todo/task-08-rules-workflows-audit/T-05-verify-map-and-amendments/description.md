## Goal
`verify` rejects an invalid migration map, an unamended deviation from the migration specification, an invalid amendment and an incomplete statement-coverage record.

## Context
- Dependencies: T-04 (verifier frame and valid-fixture builder).
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec DM-7 (decisions, defaults, deviation, amendment target forms), DM-5 statement units, and the map, amendment and coverage codes of DM-9.
- Reason: Map and amendment checking is the part of the verifier that reads another specification file; it has its own done-state and its own fixtures (a fixture specification file).

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** one `map` row per audited path; decision shapes; split cover with the optional overflow target; shared-target merge reasons; installed-name collisions under casefolding; rule-workflow stem overlap; kind prefixes with the reference-directory exemption; computed deviation with the conduct-rule exception; location of the single `.ai/specs/09-*.md` file; amendment field rules and target forms; affected criterion ids; statement units and the coverage verdict.
- **Out of scope:** deriving the defaults themselves (the auditor writes `spec09_default`; the verifier compares); report checks and rendering.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing cases with a fixture specification file containing `REQ-21`, `AC-05` and a line `### Ownership`.
2. Check one map row per audited path with the row codes, and each decision's target shape (`map-invalid`).
3. Check that a split's section lists cover every source section exactly once, leaving a `sections: null` overflow target out of the cover (`split-sections-incomplete`).
4. Check shared targets for a merge reason on every sharing target (`map-collision`).
5. Compute final installed names and check `installed-name-collision`, `stem-overlap` and `kind-prefix-invalid`.
6. Compute deviation from `spec09_default` and `spec09_optional`, apply the conduct-rule exception when the coverage verdict is `covered`, and require an existing amendment (`deviation-unamended`).
7. Locate the single migration specification file (`spec09-unavailable`) and check amendment fields, target forms and affected ids against its text (`amendment-invalid`, `amendment-target-unknown`).
8. Compute statement units of the two sections of `rules/phase-discovery.md` and check one statement per unit and the verdict (`req21-invalid`).
9. Extend `reference-unknown` to map entries and amendments, and extend the valid fixture so that it passes every rule of this subtask.

## Acceptance Criteria
- Maps that (a) split a file omitting one section, (b) share a target without `merge_reason`, (c) produce `rule-A-b` and `rule-a-b`, (d) give a rule and a workflow the same final stem, (e) target `rules/plain.md` yield `split-sections-incomplete`, `map-collision`, `installed-name-collision`, `stem-overlap` and `kind-prefix-invalid` respectively.
- An amendment targeting `REQ-99` or `Notes:Missing` yields `amendment-target-unknown`; one without evidence yields `amendment-invalid`.
- A map entry whose targets differ from its default, or whose default is null, with `amendment: null` yields `deviation-unamended`; an entry whose targets equal the default plus one optional path yields nothing.
- A root with no file or two files matching `.ai/specs/09-*.md` yields `spec09-unavailable`.
- With two sections holding three statement units, a record listing two of them, listing a line outside them, or stating `covered` with a null `covered_by` yields `req21-invalid`.
- A target under `rules/reference/` without a kind prefix yields no `kind-prefix-invalid`.
- The extended valid fixture yields no diagnostic from the rules of T-04 and T-05.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - five map faults → five codes
  - three amendment faults → two codes as stated
  - deviation with and without amendment; default plus optional → as stated
  - absent or ambiguous specification file → `spec09-unavailable`
  - three coverage faults → `req21-invalid`
  - reference-directory target → no prefix diagnostic
  - valid fixture → silent
- **Edge cases:** split with overflow target; merge of two sources into one target; rename versus move shapes; `keep` with a different target; null default; conduct-rule exception with verdict `not-covered`; amendment `new-REQ` with non-null `current`; `Terminology:` target; statement unit starting at a list item, table row, fence and paragraph.
