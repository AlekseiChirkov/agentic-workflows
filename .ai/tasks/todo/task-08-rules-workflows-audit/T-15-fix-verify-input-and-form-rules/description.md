## Goal
`verify` reads its JSON inputs as strictly as it reads the report, reports a changed entry kind without `--strict`, accepts only ASCII digits in identifiers and line numbers, and checks the remaining amendment rules: blank current text, `Notes:` targets after trailing whitespace, `Terminology:` targets against table body rows only, and self-dependencies and dependency cycles.

## Context
- Dependencies: T-14.
- Source: improvement proposals of T-04 (P6, P7), T-05 (P1, P2, P4, P5, P7, P9) and T-12 (Do Later 2, Optional 1, 2, 4), ordered applied by the owner on 2026-11-18. Verified by a read-only planning pass:
  - T-04 P6, decision: plain `verify` compares an audited entry's kind as well as its digest and reports `inventory-stale <path>:0 changed kind in the root` (today only `--strict` notices a link that becomes another kind).
  - T-04 P7, decision: read the inventory and the assessment as the report is read — no-follow, regular file only. A symbolic link is `<inventory|assessment>-invalid` with the message "is a symbolic link and is not followed"; the display name comes from the link name. Today `load_document` follows links with `read_bytes()` (scripts/audit-instructions.py:1722-1724).
  - T-05 P1: `current_faults` accepts `""` because `"" in text` is true (:2863). Reject a blank `current` for an existing target as `amendment-invalid` ("current is blank").
  - T-05 P2: `Notes:` targets are matched against `### ` lines without removing trailing whitespace (:2536). Build them from `line[4:].rstrip()`. Spec 09 has three `### ` lines with trailing whitespace; no delivered amendment uses `Notes:`.
  - T-05 P4 + P9, decision: a `Terminology:` target resolves only against body rows of the table under spec 09's `## Terminology` (no header or separator rows); build that index once. Identifier targets stay literal whole tokens anywhere; the `REQ-99` example stays an accepted observation. No delivered amendment uses `Terminology:`.
  - T-05 P5, decision: a self-dependency and any `depends_on` cycle are `amendment-invalid`. `change` and `requires_adr` are auditor judgments checked only by the schema (to be documented by the spec sync). The delivered graph has no cycle.
  - T-05 P7: rename `test_deeply_nested_assessment_values_are_scanned_without_a_traceback` and `test_deeply_nested_values_without_amounts_are_silent` (around suite :3119, :3136) so that the names say what they assert (`assessment-invalid`). Recorded amendment: the names contradict the assertions.
  - T-12 Do Later 2: use `[0-9]` instead of `\d` in every verifier form pattern: the evidence line and span patterns (:1749, :2914, :2980), `AUDIT_ID` (:1840), `AMENDMENT_ID_RE` (:1750), the finding, criterion and identifier patterns (:2837-2839) and `LISTED_FINDING_RE` (:3464). Today `rules/git-flow.md:٣` passes its form rule and resolves as line 3, and `AUD-08-٠٠١` matches `AUDIT_ID`. Leave `ECONOMICS_PATTERNS` as they are (Unicode digits are the stricter reading there) and the extraction patterns as they are (they would change inventory bytes). Dates already reject non-ASCII digits.
  - T-12 Optional 1: remove the redundant `resolvable_assessment` helper of the evidence resolution tests (recorded amendment: the amended `files_row` already makes the link cite its target).
  - T-12 Optional 2: in `cited_line` (:2984-2989), a line number with more significant digits than the entry's line count has digits is outside; add the boundary test.
  - T-12 Optional 4: three blank lines before `def evidence_fault`; one blank line before `OVERLONG_DIGITS` in the suite.
- Constraints: as T-13. Off-limits: as T-13.

## Scope
- **In scope:** the items above.
- **Out of scope:** output escaping and render; audit output content; spec 08 text.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Failing tests: a link that becomes another non-file kind is reported by plain `verify`; a symbolic-linked inventory and assessment are `-invalid` and not followed; `current: ""` and `current: " "` are `amendment-invalid`; a `Notes:` target resolves against a `### X ` line with a trailing space; a `Terminology:` target matches only a body row; a self-dependency and a two-amendment cycle are `amendment-invalid`; `rules/x.md:٣` in a files row is rejected by its form rule and in a finding is `evidence-unresolved`; `AUD-08-٠٠١` is rejected by the schema; a ten-digit line on a ten-line entry is outside.
2. Apply the two recorded amendments (renames, helper removal).
3. Implement.
4. Suite, delivery gate.

## Acceptance Criteria
- Each behaviour in Steps 1 holds and has a test that failed before its implementation.
- Only the two recorded amendments change earlier tests.
- Suite exits 0; the delivery gate prints `GATE PASS`; spec 09 at the current tree still matches every delivered amendment target under the new rules.

## Test Plan
- **Level:** integration.
- **Scenarios:** as Steps 1.
- **Edge cases:** a three-amendment cycle; a `Terminology:` target equal to a header cell; a `### ` line with a trailing tab; a symbolic link inside the inventory's parent directory path (only the final component is checked, as for the report).
