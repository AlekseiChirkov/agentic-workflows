## Goal
The assessment is complete with duplicate groups, the migration map, the migration-specification inputs and amendments, and the report renders and verifies with the review pending.

## Context
- Dependencies: T-08 (all per-file judgments).
- Constraints: The auditor reads every assigned file in full and never edits an audited file; one writer of the assessment; judgments cite current `path:line` evidence; no count, kind or capability is taken from an earlier record or a harness name; no token count or monetary amount in any string; kinds are the eight of the specification's Terminology. Source contract: spec DM-7 and the Edge Cases table. Defaults are derived from the migration specification as it stands at the audited revision by the table of DM-7; nothing is proposed for deletion; amendments are proposals only and the specification file is not edited.
- Reason: Cross-file synthesis needs every per-file row first and produces the artefacts the migration consumes; one done-state: `verify` exits 0 on the report with `Reviewed: pending`.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** duplicate groups over every cluster and read-detected repeats; one map entry per audited path with decision, targets, `spec09_default`, `spec09_optional` and amendment; the statement-coverage record for the two sections of `rules/phase-discovery.md`; amendments with exact current text; remaining findings and `blocks_09` values; the report file with summary, method, generated region, blockers, review and acceptance lines.
- **Out of scope:** index and knowledge edits; the review line; applying any amendment; fixing any finding.
- **Target files:** `docs/audits/<run_date>-rules-workflows-audit.assessment.json`, `docs/audits/<run_date>-rules-workflows-audit.md`

## Steps
1. Run `verify` and save the remaining diagnostics as the starting list.
2. Assign every duplicate cluster to exactly one group with members, normative source, condition differences, disposition, owner and rationale; add read-detected locations; write findings for `consolidate` and `contradiction` groups.
3. Read the migration specification's rule map, workflow map, section map and the requirements the default table names; write `spec09_default` and `spec09_optional` for every audited path.
4. Decide each map entry (keep, rename, move, split, merge) from the per-file kinds and sections; give targets, section lists and merge reasons.
5. Enumerate the statement units of `## Codebase Reading Rules` and `## Decision Protocol`; record where each is covered and the verdict.
6. Write one amendment per deviation and per obligation the migration specification lacks, with target, change type, exact current and proposed text, reason, evidence, affected criteria, dependencies and the decision-record flag.
7. Set `blocks_09` on every finding by the blocking predicate and add any finding the synthesis reveals, including historical defects confirmed fixed.
8. Create the report with the title, summary, method (commands, deviations, measured times), the marker pair, the blockers section naming every blocking finding or `None.`, `Reviewed: pending` and `Accepted: pending`; run `render --write`.
9. Run `verify --root . --report <report>` until it prints nothing, then confirm the outputs hold no absolute path and no economic statement.

## Acceptance Criteria
- `verify --root . --report <report>` exits 0 with empty output on the committed tree.
- The assessment has exactly one `map` entry per audited path, and every entry that deviates from its default cites an existing amendment.
- Every duplicate cluster of the inventory belongs to exactly one group.
- The `req21` record has one statement per statement unit of the two sections and a verdict consistent with them.
- The report's Spec 09 inputs subsection lists every map entry with a null default and the coverage verdict; the Sections subsection shows word counts for every section of every audited file; the impact subsection has one row per non-`keep` entry.
- Every finding with `blocks_09: true` is named under `## Blockers for spec 09`; the acceptance line is `Accepted: pending`.
- `grep -rn '/home/\|/Users/' docs/audits/*-rules-workflows-audit.*` prints nothing, and `.ai/specs/09-model-only-harnesses-and-rule-naming.md` is unchanged.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - starting `verify` output lists map, group, coverage-record and report diagnostics; final output is empty with exit 0
  - map row count and amendment citations → exact
  - cluster membership → one group each
  - coverage record → one statement per unit
  - report subsections → present with the stated content
  - blockers listed; acceptance pending
  - no absolute path; migration specification unchanged
- **Edge cases:** audited path absent from the migration maps (null default, amendment required); split whose fenced template headings travel with their section; shared merge target; equal sentences valid under different conditions (`condition-specific`); contradicting fragments (owner decision); a size target that conflicts with obligatory content (finding, nothing deleted).
