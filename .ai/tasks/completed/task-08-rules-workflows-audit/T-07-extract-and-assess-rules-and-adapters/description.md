## Goal
The delivered inventory is extracted at a clean commit, and the assessment holds complete per-item judgments for every rule and adapter file.

## Context
- Dependencies: T-06 (committed tool and suite).
- Constraints: The auditor reads every assigned file in full and never edits an audited file; one writer of the assessment; judgments cite current `path:line` evidence; no count, kind or capability is taken from an earlier record or a harness name; no token count or monetary amount in any string; kinds are the eight of the specification's Terminology. Source contract: spec DM-7 and the Edge Cases table. Extraction requires every audited and reader path to be committed, including this task's own records; the orchestrator owns commits.
- Reason: The first reading group fixes the pinned snapshot and the assessment skeleton that the second group extends; rules and adapters are the files with mixed kinds, load modes for later consumers, and most duplicate sources.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** the clean extraction and `run_date`; the assessment skeleton with every key; for the files under `rules/`, `harness/` and `templates/codex-global-AGENTS.md`: `files` rows with kinds, evidence and section classification (always for `rules/phase-atomic-execution.md` and `rules/phase-discovery.md`), `coverage` entries, `loads` entries for their load edges, dispositions of the candidates located in them, roles of their legacy mentions, and findings for their defect edges and observations; provisional `map` rows are left for T-09.
- **Out of scope:** workflow files; duplicate groups, the migration map, defaults, amendments and the statement-coverage record; the report.
- **Target files:** `docs/audits/<run_date>-rules-workflows-audit.inventory.json`, `docs/audits/<run_date>-rules-workflows-audit.assessment.json`

## Steps
1. Confirm the work tree is clean and the tool and suite are committed; record the commit; run `extract` to the dated inventory path and record the measured time for the report's method section.
2. Create the assessment with every top-level key, `inventory_digest`, `run_date`, role label, environment versions and `installed_access: not-verified`.
3. Run `verify` and save the diagnostics located in rule and adapter files as the starting list.
4. Read each of the 14 rule files in full; write its `files` row (kinds, evidence, sections with kind and proposed home where required) and `coverage` entry with the digest read.
5. Read the four harness files and the Codex always-on template in full; write their rows and coverage entries.
6. Classify every load edge whose source is a rule or adapter file as `mandatory` or `conditional` with the condition text.
7. Disposition every `FO` and `HN` candidate located in these files and give every legacy mention in them one role with a note.
8. Write findings for every defect edge whose source is one of these files and for mixed kinds, naming, legacy and other observations, each with type, severity, owner, closure, evidence and edges; use `accepted-observation` for a defect edge that is correct on reading.
9. Re-run `verify` and confirm that no diagnostic of the per-item rules names a rule or adapter file.

## Acceptance Criteria
- The inventory exists under `docs/audits/` with a date prefix equal to the assessment's `run_date`, its `worktree.state` is `clean`, and its `source_revision` is the commit recorded in step 1.
- A fresh `extract` on a checkout of that `source_revision` equals the inventory byte for byte.
- The assessment has exactly one `files` row and one `coverage` entry for each of the 19 rule and adapter paths, each coverage digest equal to the inventory's.
- The rows of `rules/phase-atomic-execution.md` and `rules/phase-discovery.md` have `sections` covering every section once.
- `verify` prints no `row-missing`, `sections-incomplete`, `load-unclassified`, `candidate-undisposed`, `legacy-role-missing`, `defect-unrecorded`, `finding-invalid`, `finding-stale` or `assessment-stale` diagnostic whose location is a rule or adapter path or an item sourced in one.
- `git status --porcelain -- rules workflows harness templates tests hooks principles scripts` prints nothing.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - inventory file name date, `run_date`, `worktree.state` and `source_revision` → equal to the extraction date, `clean` and the recorded commit
  - starting `verify` output lists diagnostics for these files (observed before the assessment work); final output lists none for them
  - fresh extraction on the pinned revision → byte-identical
  - row and coverage counts for the 19 paths → exact
  - the two always-classified files → full section cover
  - audited and protected trees → unchanged
- **Edge cases:** file with invalid encoding (coverage `unavailable` with a finding); symbolic-link entry (`not-a-file`); a file that changes after extraction (`changed`, re-extract and re-read); candidate that is correct on reading (`guarded` or `not-applicable` with a reason); defect edge correct on reading (`accepted-observation`).
