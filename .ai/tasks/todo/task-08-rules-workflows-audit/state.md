spec_path: .ai/specs/08-rules-workflows-audit.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: not-started
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Specification numbers → the names in force since the renumbering of 2026-11-16 are used everywhere: this specification is 08, the naming migration 09, context tiering 11, and proposal owners are 11, 12, 13, 14, 15 (source: `.ai/specs/README.md → ## Renumbering — 2026-11-16`; ADR-0023).
- Line citations in the specification that have drifted (ledger row cited at `:214`, now `:208`; "docs/audits/ does not exist", now an empty untracked directory; "11 `.sh` and 30 `.py`", now 11 and 31; `docs/README.md:13-20`) → the requirement stands and the subtask that uses a fact re-verifies it at the commit it works on; the extractor reads the live tree and takes no count from a record (source: spec REQ-01; `rule-phase-discovery → ## Codebase Reading Rules`).
- "Run no model" (REQ-04) → it binds the tool and the inventory; the auditor that reads the files and writes the assessment is the pipeline's Implementer role, and the independent reviewer its Validator role (source: spec Actors & Roles; Notes → Prerequisites and Guard).
- Test level → `unit` and `integration` through the standalone `unittest` suite in `scripts/`, never registered in the validator; assessment subtasks take `verify` diagnostics located in their files as RED (source: spec REQ-24, Notes → Implementation order; ADR-0019 Decision 3; `.ai/principles/architecture.md` P7).
- `run_date` → the calendar date of the clean extraction; the three output names and the assessment share it (source: spec DM-7, DM-9 `report-name-date`).
- Extraction order → the tool and suite are committed before extraction; index and knowledge edits come after it, because they are readers and `--strict` is run on a checkout of `source_revision` (source: spec Notes → Prerequisites and Guard).
- One writer of the assessment → reading may be split by file group, but each assessment subtask is sequential and writes the single assessment file (source: P4; spec Edge Cases "Concurrent writers").
- Review line → written after the independent review passes, naming the reviewed commit; the acceptance line stays `Accepted: pending` (source: spec REQ-14, DM-8, AC-10).
- Knowledge entries in `.ai/memory/state.md` and `.ai/memory/progress.md` → written inside the delivery because AC-24 checks them, in the last subtask (source: spec REQ-26, AC-24).
- Installed-copy comparison → not performed; `installed_access: not-verified` (source: spec A-10; owner's rule not to touch deployed copies).
- No ADR → none is required for this delivery; amendments that alter an accepted decision carry `requires_adr` for the later reconciliation of the naming-migration specification (source: spec A-17).
- Branch → Discovery artifacts are written on `docs/discover-rules-workflows-audit`, created from `main` at `cc632f4` (source: repository rule to branch before changing files on the default branch).
- flow: full — gate: 1fail 2fail 3pass 4pass (more than three files; a new tool with a new data contract) (source: `rules/quick-flow.md → ## The escalation gate`).
- Data-contract names that embed specification numbers (`blocks_09`, `in_spec09_grammar`, `spec09_default`, `spec09-unavailable`, `AUD-08-NNN`, `08-extract-1`) → used verbatim in the tool and outputs because the specification fixes them; comments, docstrings and test names state rules in words without requirement, criterion or specification labels (source: spec DM-1, DM-4, DM-7, DM-9; owner ruling of 2026-11-13 on specification labels in product code; P8).

## Open Questions (batch)
None

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10

## Subtask Progress

T-01 | Inventory extractor | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-02 | Reference edges | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-03 | Candidates, legacy mentions and duplicate clusters | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-04 | Verifier: assessment consistency | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-05 | Verifier: map, amendments and statement coverage | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-06 | Renderer and report checks | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: scripts/audit-instructions.py, scripts/check-audit-instructions.py
  blocker: none
  notes:

T-07 | Extraction and assessment of rules and adapters | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.inventory.json, docs/audits/<run_date>-rules-workflows-audit.assessment.json
  blocker: none
  notes:

T-08 | Assessment of workflows | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.assessment.json
  blocker: none
  notes:

T-09 | Map, findings, amendments and report | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/audits/<run_date>-rules-workflows-audit.assessment.json, docs/audits/<run_date>-rules-workflows-audit.md
  blocker: none
  notes:

T-10 | Index, knowledge and review line | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: none
  target_files: docs/README.md, scripts/README.md, .ai/context/runbook.md, .ai/memory/architecture.md, .ai/memory/state.md, .ai/memory/progress.md, docs/audits/<run_date>-rules-workflows-audit.md
  blocker: none
  notes:


## Model Selection
selection: complete
active provider: anthropic (`Model (Claude)` column)
catalog: ~/.config/orchestrail/model-catalog.md, refreshed 2026-11-09 (fresh, 7 days old; evidence dated 2026-11-09)
support evidence (2026-11-16): the worker tool of this session accepts the model names haiku, sonnet, opus and fable; the session environment lists the identifiers claude-haiku-5-5, claude-sonnet-5-5 and claude-opus-5-5; worker tools: all; the tool does not expose a context window, so the 1,000,000-token window is the owner's confirmation of 2026-11-13, not a new observation.
owner limits: allowed models are the three observed identifiers; the session model claude-fable-5-2 has no catalog evidence and was not a candidate. Fallback configuration is valid (openai gpt-6.1-terra, high) and was not needed.
cost: no qualified comparable total-cost evidence; the strongest eligible baseline was used, so cost optimality is unverified.
reasoning support (2026-11-16): the worker tool exposes the effort levels low, medium, high, xhigh and max and effort is configurable per worker; support per model is not separately observed.
reasoning rationale: catalog quality is measured at maximum effort; leaf floors here are 2–4 and lower levels have no recorded evidence, so `high` is recommended for every leaf, as a heuristic.
reselection 2026-11-16: finalization added one test scenario to T-07 (scope, steps and criteria unchanged); T-07 was reselected with unchanged scores and the same result, and its digest was recomputed.
actual model and actual reasoning: unknown until separately observed execution evidence.

| Leaf | Scores (C/A/V/R/Ver/Crit/RW) | Floor | Recommendation | Confidence | Reasoning | Description sha256 | Plan row sha256 |
|---|---|---|---|---|---|---|---|
| T-01 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | 5231849a94d38f25e161099c924d6eecbc278b9301161b4d3510c0a807e9c384 | cf718b61516e0b719764e744605c56461e8e25b41bf825227cc16584ed49963e |
| T-02 | 4/2/3/4/4/2/3 | 3 | claude-opus-5-5 | verified | high | 513549a83a6e6456ee17b4fd2e58c5a5e81a8e7b74bdcc3f54b90c97f800af7e | 78c2fb0e6d243933b109c1a266fabb2c91672a8b40f2d808372b405065bc9218 |
| T-03 | 3/2/3/4/4/2/3 | 3 | claude-opus-5-5 | verified | high | 0b80a7f8f16da9f5d8a96c0ae968134c929597d3ea112599904c9c112e86a25d | 025474779d65d2972e15fc62c08f4f32af1bd2cf0232e70a94170d4b3ed24234 |
| T-04 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | 12e32ba678a199ac338cf3d145fc19efecb4760d825706f50e53eebcf080e7dc | ba945a63453940265cb53e7629f82f0fddc692932b67541446a0bdba1485f66e |
| T-05 | 3/2/3/3/4/2/3 | 3 | claude-opus-5-5 | verified | high | 45446a9330fac1584dd7531ced7a1422f201980a7be2dc6bbcdb4c31f3b29fe3 | e5e278529bcee7306975f76c446a32e225a425ba54af70084e90ea4b7e0c2e5e |
| T-06 | 3/1/3/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | f56026a3cb70bed31b4de7c4e224af1d8aa0c11a8498155eaf511481bd907591 | 680bd30c3a39ec159b3a8e9bd78688d7eb2a8c7bc49391d361beb09284c0cec2 |
| T-07 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | fbf7860f83d1e6eb6d143b9e6acb4ddda0d840743c90bc0384a0558383ae815a | 26325889e65eac13d1a30333f0c82f10d2fc4ad8458b62410bf08b8516826784 |
| T-08 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | ef088cfd3208310cc4ab5665b9f145f5d4ad1c92144783f6be217ab2200bf152 | 8902589702291e8d1541b7ff16f77ad3c054ca7a9eda4311defa0defe9e64b0a |
| T-09 | 4/3/4/4/2/3/4 | 4 | claude-opus-5-5 | verified | high | e745870b9261dcdf96cb54ef3f47c2e4de4eac37f366bc058a9654a9950618e9 | 0f0dd8045dfd8ad9566618435cd1a15dd6193abdc51fb58769ab1b712c58a5c9 |
| T-10 | 2/1/3/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | 25f47f5b8de403951cf30f88645afb5dff12f7000247ab8d103afa489624203e | 420d8807eb3d1fbec973074e772b7d7c8349190916e2cbe4ff8a36258839069d |

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Variant 1. The specification fixes the interface, the data model, the diagnostics and the two permitted files; the remaining choice is internal structure, and layered pure functions in one file satisfy the boundary and keep each subtask's addition local to one layer. Verifier rules and renderer subsections are plain functions collected in ordered lists, not a plug-in mechanism.
adr: not triggered — the specification already fixes the contract and states that no decision record is required; the internal layout of one script is a local choice that a future reader does not need a record to understand.

### Scope
#### In
- The tool with `extract`, `verify` and `render`, and its standalone suite.
- The three audit outputs for the snapshot extracted at a clean commit, with every audited file read in full.
- One index line, two script rows, one commands note, the inventory sentence, and the two memory entries.
- The review line after an independent pass; acceptance left pending.
#### Out
- Any edit to audited files, tests, hooks, principles, templates, the validator, sync or other scripts.
- Applying amendments or fixing findings; reconciliation of the naming-migration specification.
- Registration of the suite or tool in the validator or in sync.
- Installed-copy comparison; token, cost or saving statements.
- Restoring absent historical reports or repairing their links.

### Rejected
→ archived to state-archive.md

### Off-limits
- `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, every other existing script, every specification file.
- `scripts/sync.sh`, installers, workflows and models are never run to produce the inventory.
- Installed copies under the user's home are never read or changed by the tool.
- No absolute path and no former repository name in any output or fixture.

### Invariants
- The tool writes only the `extract --out` file or the generated region under `render --write`, each by atomic replacement.
- Two extractions of the same bytes and git state are byte-identical.
- Symbolic links are recorded and never followed; repository content is never executed or imported by the tool.
- The assessment has one writer at a time, and every audited path has exactly one row in `files`, `coverage` and `map`.
- Nothing obligatory is proposed for deletion; changes to the naming-migration specification exist only as amendments.
- `bash scripts/validate-contracts.sh` stays at zero failures.

### Acceptance Criteria
- `python3 -I scripts/check-audit-instructions.py` exits 0, with at least one case per edge form, per status and per diagnostic code.
- `python3 -I scripts/audit-instructions.py verify --root . --report docs/audits/<run_date>-rules-workflows-audit.md` exits 0 with empty output at the delivery commit.
- A fresh extraction on a checkout of the inventory's `source_revision` equals the delivered inventory byte for byte.
- The report holds `Reviewed: <role> <date> pass <commit>` and `Accepted: pending`, and names every blocking finding under its blockers heading.
- Every changed path of the delivery is in the specification's permitted-changes list, and `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing.
- `bash scripts/validate-contracts.sh` reports zero failures.
- The index, script table, runbook note, inventory sentence and the two memory entries are present as the specification states.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | 4 | 4 | 4 | 4 | 5 | 21 |
| Variant 2 | 3 | 3 | 4 | 4 | 2 | 16 |
| Variant 3 | 4 | 4 | 3 | 2 | 5 | 18 |

**Winner:** Variant 1 — it is the only layout that stays inside the two permitted files and keeps unit-level testability.
**Anti-overengineering check:** passed — ordered lists of plain functions add no abstraction beyond what the per-code and per-subsection criteria need.
**Evidence:** the specification's permitted-changes list and suite contract; P4, P7; ADR-0019 Decision 3 (standalone checks under `scripts/`); `scripts/state-tool.py` as the single-file standard-library precedent.
