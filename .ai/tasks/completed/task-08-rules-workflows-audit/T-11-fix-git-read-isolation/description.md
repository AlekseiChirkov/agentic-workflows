## Goal
The audit tool's git reads never open a network connection and never run a program configured by the audited repository or the user's git configuration, or the module states exactly which guarantee it gives.

## Context
- Dependencies: T-10 (the delivered tool, suite and audit outputs).
- Source: task-level code review finding [2] (`## Issue List`). In a partial clone, `git status` rename detection and `git cat-file -e <sha>^{commit}` can fetch missing objects from the promisor remote; `git status` can run clean or process filter drivers selected by `.gitattributes` and defined in repository or global configuration. The module docstring (scripts/audit-instructions.py:59-67) claims that no program named by the repository's configuration runs. Spec REQ-15 and the Contracts → Git use section limit the tool to read-only, offline git reads.
- Constraints: Python 3.11+ standard library only; type annotations on every function; the three permitted git read commands stay the only git commands (`rev-parse --verify HEAD`, `ls-files -z`, `status --porcelain=v1 -z --untracked-files=all`, and in verify `cat-file -e`); options and environment variables may be added to them. A git that does not know a newer option must not turn a clean tree into `unknown` silently on the supported range: prefer environment variables that older git ignores, or detect support. Comments, docstrings and test names state rules in words without requirement, criterion or specification labels.
- Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script, any specification, or the three audit outputs; no registration in the validator or in sync; never read or change installed copies.

## Scope
- **In scope:** the git read environment and options in `scripts/audit-instructions.py`; the module docstring's guarantee; new tests in `scripts/check-audit-instructions.py`.
- **Out of scope:** the audit outputs (the extraction at `8d7e484` stays as delivered; its git state was a clean full clone); any other finding.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing tests: a fixture repository whose attributes select a clean filter, configured in the repository and in a fixture global configuration, that would write a marker file; `extract` and `verify` must not create the marker. If a partial-clone fixture is feasible offline (a local promisor remote via `file://`), add one showing that no object is fetched; otherwise assert the read environment and options directly.
2. Disable lazy fetching for every git read (`GIT_NO_LAZY_FETCH=1`) and rename detection for `status` (`--no-renames`).
3. Keep attribute-selected filters from running: read attributes from the empty tree where the installed git supports it, or otherwise neutralise filter drivers; if a residual case cannot be closed with the permitted commands, narrow the docstring to the exact guarantee and name the residual.
4. Run the full standalone suite and confirm that `extract` on this checkout is byte-identical to the delivered inventory's content model where the tree state allows, and that `verify --root . --report docs/audits/2026-11-17-rules-workflows-audit.md` stays silent.

## Acceptance Criteria
- With a configured clean or process filter selected by attributes, `extract` and `verify` create no marker file and still report the work tree correctly.
- Every git read runs with lazy fetching disabled, and `status` runs without rename detection.
- The module docstring states exactly the guarantee the code gives.
- `python3 -I scripts/check-audit-instructions.py` exits 0 with the earlier 212 tests unchanged, and `verify --root . --report docs/audits/2026-11-17-rules-workflows-audit.md` exits 0 with empty output.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - attribute-selected clean filter in repository configuration → no marker, correct work-tree state
  - attribute-selected filter in a fixture global configuration → no marker
  - read environment and options → lazy fetch disabled, no rename detection
- **Edge cases:** git without the newer options (behaviour stays inside the exit contract and does not silently mark a clean tree unknown on supported versions); a dirty audited file under a filter.
