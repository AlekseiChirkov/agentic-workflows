## Goal
The audit is indexed, recorded in the knowledge base and closed with the independent review line, with the full contract validator at zero failures.

## Context
- Dependencies: T-09 (report verified with review pending, and its independent validation verdict and commit).
- Constraints: Edits are limited to one index line, two table rows, one commands note, the inventory sentence and the two memory entries; knowledge edits come after extraction because these files are readers; the review line records the verdict of the independent validation of T-09 and the commit it reviewed, written by the single writer of the task's files; the acceptance line stays pending. Source contract: spec DM-8 review line grammar and the permitted-changes list.
- Reason: Closure is separate because it depends on a review verdict that exists only after the report is validated, and because its edits would make a strict re-extraction differ.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** the report link in `docs/README.md`; rows for both scripts in `scripts/README.md`; the two commands in the runbook's command notes; the script counts in the architecture inventory sentence; completed entries in the state registry and progress log linking the report; the `Reviewed:` line; the final checks.
- **Out of scope:** any change to the inventory or assessment; acceptance by the owner; reconciliation of the migration specification; repair of the absent audit links already in the index.
- **Target files:** `docs/README.md`, `scripts/README.md`, `.ai/context/runbook.md`, `.ai/memory/architecture.md`, `.ai/memory/state.md`, `.ai/memory/progress.md`, `docs/audits/<run_date>-rules-workflows-audit.md`

## Steps
1. Add one line linking the report under ``## Audits (`audits/`)`` in `docs/README.md`.
2. Add one table row per new script to `scripts/README.md`, each stating purpose, standalone use and that it is outside the validator inventory.
3. Add a note naming both commands to `.ai/context/runbook.md → ## Commands`.
4. Update the inventory sentence of `.ai/memory/architecture.md` to the counts `ls scripts/*.sh | wc -l` and `ls scripts/*.py | wc -l` give.
5. Add a completed entry linking the report to `.ai/memory/state.md` and append one to `.ai/memory/progress.md`, at the end so that pinned line numbers above do not move.
6. Replace `Reviewed: pending` with `Reviewed: <role> <date> pass <commit>` using the recorded verdict and reviewed commit of T-09; if that verdict is not a pass, stop and report instead.
7. Run `verify --root . --report <report>`, the suite, and `bash scripts/validate-contracts.sh` with the Python version setting the runbook names.
8. List the delivery's changed paths against the permitted-changes list and report any path outside it.

## Acceptance Criteria
- `## Independent review` holds exactly one line `Reviewed: <role> <date> pass <40-hex commit>` whose commit exists, and `## Acceptance` holds `Accepted: pending`.
- `verify --root . --report <report>` exits 0 with empty output at the final commit.
- The three output files exist under `docs/audits/` with one date prefix, and ``## Audits (`audits/`)`` of `docs/README.md` links the report.
- `scripts/README.md` has one row for each of the two scripts, and the architecture inventory sentence states the counts the two `ls … | wc -l` commands give.
- `.ai/context/runbook.md → ## Commands` names both commands, and the state registry and progress log each hold an entry linking the report.
- `bash scripts/validate-contracts.sh` reports zero failures, and `python3 -I scripts/check-audit-instructions.py` exits 0.
- Every path in `git diff --name-only "$(git merge-base main HEAD)" HEAD` is in the permitted-changes list of the specification.

## Test Plan
- **Level:** smoke, integration
- **Scenarios:**
  - review and acceptance lines → exact grammar; commit exists
  - `verify` at the final commit → exit 0, empty
  - index link and three files → present
  - script rows and counts → exact
  - runbook and memory entries → present
  - validator → zero failures; suite → exit 0
  - changed paths → all permitted
- **Edge cases:** review verdict not a pass (stop, no line written); review commit missing after a history rewrite (`review-commit-unknown`); identity-ledger line pins in the files edited (append, never insert above a pinned line); validator failure caused by a former-name occurrence in an output.
