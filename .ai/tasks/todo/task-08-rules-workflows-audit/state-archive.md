# state-archive — task-08-rules-workflows-audit

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Deliver one pinned, reproducible audit of every rule, workflow and harness adapter file: a read-only standard-library tool `scripts/audit-instructions.py` (`extract`, `verify`, `render`) with its standalone suite `scripts/check-audit-instructions.py`, and the three audit outputs under `docs/audits/` (inventory, assessment, report) produced by reading every audited file in full, so that the naming-migration specification receives a machine-verified migration map, amendments and findings, the optimization specifications receive owned proposals, and no instruction, adapter, test, validator or installed copy changes.

### Affected Parts
- New: `scripts/audit-instructions.py` (extractor, verifier, renderer; Python 3.11+ standard library; git read commands only), `scripts/check-audit-instructions.py` (`unittest`, temporary fixture roots, synthetic stems).
- New: `docs/audits/<run_date>-rules-workflows-audit.md`, `.inventory.json`, `.assessment.json`.
- Changed (one line or row each): `docs/README.md` (audits index), `scripts/README.md` (two table rows), `.ai/context/runbook.md` (commands note), `.ai/memory/architecture.md` (inventory sentence), `.ai/memory/state.md`, `.ai/memory/progress.md`.
- Read-only inputs: 14 files in `rules/`, 42 in `workflows/`, 4 in `harness/`, `templates/codex-global-AGENTS.md` (61 audited paths at this revision), every reader of DM-3, and `.ai/specs/09-model-only-harnesses-and-rule-naming.md` for defaults and amendment targets.
- Unchanged by contract: `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, every other existing script, and every other specification.

### Codebase Analysis
- `tests/workflow-instructions.py` — read to verify the limits of the existing reference check: it reads only `workflows/*.md`, only `##`–`####`-marked citations, skips unresolved heads and accepts either same-stem candidate (lines 20-35), as the spec states. The new tool does not replace or edit it.
- `scripts/state-tool.py` (header) — read to verify the house pattern for a standard-library tool: `#!/usr/bin/env python3`, a usage docstring, one JSON result, read commands that write nothing. The runtime-guard shape required here (docstring, `from __future__ import annotations`, `import sys`, guard) is checked by the suite, not copied.
- `scripts/README.md` — read to verify the table the two new rows join; `check-spec-draft.sh` is the standalone-check precedent row.
- `docs/README.md` — read to verify the ``## Audits (`audits/`)`` section exists and receives the report link. It lists six entries, five of them links to files that are not in the tree.
- `tests/fixtures/validator-runtime/source_guard.py` (lines 801-834) — read to verify that the source guard binds `.sh`/`.py` files under `tests/` only, so new files under `scripts/` are outside it.
- Tree facts verified by listing: 14 rules, 42 workflows, 4 harness files, no nested directories; `scripts/` holds 11 `.sh` and 31 `.py` files; `docs/audits/` exists as an empty, untracked directory; the identity-ledger row for this specification is at `.ai/tasks/completed/task-01-git-source-of-truth/state.md:208` and pins line 23 of the specification.
- Files read: 5/12 (5 entry-points, 0 deeper). Knowledge and specification files are outside the budget.

### Open Questions
- Whether the historical reports can be restored (spec Q-01) and whether the tool stays after the naming migration (spec Q-02): both non-blocking; neither changes this delivery.

## Archived Solution Design — Variants
- **Variant 1 — one tool file in layers of pure functions.** `scripts/audit-instructions.py` holds, in order: runtime guard and CLI; text model; inventory; reference grammar; candidates and clusters; verifier as a list of check functions that each take the loaded inventory, assessment and report and return diagnostics; renderer as one function per subsection. The suite drives the CLI as a subprocess for behaviour and loads the file by path for the version-guard and small unit cases. Advantages: exactly the two files the specification permits; one read-only entry point; every layer is testable on fixture trees; a new diagnostic is one function. Disadvantages: a large single file. Risks: the file grows past comfortable review size; mitigated by fixed layer order and small functions.
- **Variant 2 — a package of sibling modules with a thin CLI** (the pattern of the telemetry helpers). Advantages: smaller files. Disadvantages: creates files outside the permitted-changes list, so the delivery fails its own boundary criterion; changes the script counts the knowledge base records; more import plumbing under `python3 -I`. Risks: needs a specification amendment before it can be accepted.
- **Variant 3 — one tool file tested only as a black box.** Advantages: the suite never loads repository code. Disadvantages: the version-guard criterion needs `sys.version_info` patched by the case, which a pure subprocess cannot do without a wrapper; unit-level edge cases of the text model become slow end-to-end fixtures. Risks: weaker coverage of grammar edge cases.

## Archived Solution Design — Rejected
- Variant 2: breaks the permitted-changes list and the recorded script counts.
- Variant 3: cannot meet the version-guard criterion cleanly and weakens edge-case coverage.
- A general plug-in or rule-configuration layer for the verifier: no current requirement needs rules to be configured or extended at run time.
