spec_path: .ai/specs/07-state-tool.md
contract_version: 0.9.0
flow: full

## Phases
- discovery: complete
- execution: not-started
- validation: not-started

## Task Analysis

→ archived to state-archive.md

### Assumptions
- Spec lists AC-12 and REQ-14 as withdrawn → they are excluded from the task contract; AC-01–AC-11 and AC-13–AC-23 are binding (source: spec `## Requirements` REQ-14, `## Acceptance Criteria` AC-12, D-01).
- Rule file names → the current names apply (`rules/workflow-globals.md`, `rules/workflow-reference.md`, `rules/tdd.md`), because the rule-renaming spec has not landed (source: spec constraint C-4; `rules/` directory listing).
- Acceptance-suite location and registration → a suite under `tests/` with a focused validator mode and a default-run registration, matching every existing suite (source: `scripts/validate-contracts.sh:284-343`; spec implementation hint, nonbinding).
- Test level for this repository → `smoke`/`integration` through executable fixtures; a contract change starts with a failing check (source: `.ai/principles/architecture.md` P7; `.ai/principles/coding.md → Changing a contract`).
- Pinned script digests → every digest in `tests/fixtures/validator-runtime/source_guard_exceptions.json` invalidated by an edit to a pinned script is refreshed in the subtask that makes the edit, by the recorded fixture procedure (source: spec `### Contract-file changes`; ADR-0020 Decision on fixture maintenance).
- Deployment → `scripts/sync.sh` is not changed and not run by this task's subtasks; the tool is addressed through the source root like other helpers (source: spec Out of Scope; ADR-0021 Decision 3).
- Knowledge updates (architecture inventory counts, state registry, progress log) → applied by the orchestrator at finalization, not by subtask workers (source: `rules/orchestration.md → ## Shared-file discipline`).
- flow: full — gate: 1fail 2fail 3pass 4pass (more than three files; a new protected field and new invariants are introduced) (source: `rules/quick-flow.md → ## The escalation gate`).
- Worker model support for selection (the worker tool does not expose a context window) → the documented 1,000,000-token context of the catalog is confirmed as the support observation; selection uses the current catalog without a refresh (source: user, 2026-11-13).

## Open Questions (batch)
None

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10

## Subtask Progress

T-01 | Progress parser and get command | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, scripts/validate-contracts.sh, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/inventory-amendment.json
  blocker: none
  notes:
  branch: feat/state-tool-reader
  base_branch: main
  base_commit: 060ce6dbc7116002ac5e6cd47981cfd3c13d60ff
  commits:
  pr: none

T-02 | Static validation command | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-03 | Set write transaction | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-04 | Note and target-file additions | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-05 | Lifecycle invariants on set | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-06 | Block initialization | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-07 | Idempotent operation receipts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-08 | Lock contention and interruption recovery | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: scripts/state-tool.py, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

T-09 | Receipts grammar contract and validator checks | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: rules/workflow-globals.md, rules/workflow-reference.md, scripts/validate-task.sh, scripts/validate-contracts.sh, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py, tests/fixtures/validator-runtime/inventory-amendment.json
  blocker: none
  notes:

T-10 | Ignore rules and usage documentation | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action:
  target_files: .gitignore, scripts/setup-new-project.sh, docs/USAGE.md, scripts/README.md, tests/state-tool.py, tests/fixtures/validator-runtime/source_guard_exceptions.json, tests/fixtures/validator-runtime/source_guard.py
  blocker: none
  notes:

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Variant 1. The line-preserving model makes REQ-01 and I-8 hold by construction rather
than by careful re-serialization, and the Python suite covers every acceptance criterion,
including the in-process and static-scan cases, in the form the repository already uses
for Python helpers. The per-subtask fixture refresh is the price of keeping every stack
tip fully valid.

Implementation shape (binding for all subtasks):
- One file `scripts/state-tool.py`; the Python-version guard precedes every import other
  than `sys`; vocabulary constants are module-level tuples, one line each.
- Layers as functions: argument parsing → path and file checks → document parse (lines
  with roles, section span, blocks with field groups) → invariant predicates → edit
  operations returning a new line list and changed-field names → receipts → write
  transaction (lock, read, revision, candidate re-parse, temporary file, recheck, rename)
  → JSON result. Parsing, invariants, edits and receipts are callable without the command
  line.
- Errors are a single exception type carrying exit code, error code, message and optional
  line; one top-level handler prints the JSON object on stdout and diagnostics on stderr.
  An unexpected exception is exit 1 `internal-error`.
- Suite `tests/state-tool.py`: fixture builders, a subprocess runner, a directory snapshot
  helper (bytes, mode, mtime), and `runpy` loading for in-process cases; one test class
  per command or concern, extended by each subtask.
- Each subtask that changes a file under `tests/` or `scripts/validate-contracts.sh`
  finishes by refreshing the pinned validator-runtime fixtures by the recorded procedure.
- Subtasks verify with `python3 tests/state-tool.py`,
  `bash scripts/validate-contracts.sh --state-tool-only` and the source-guard suites; the
  complete validator run happens at task-level validation.

adr: `.ai/adr/0022-task-07-state-tool-receipts-and-line-preserving-writes.md` (provisional)

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---|---|---|---|---|---|
| Variant 1 | 4 | 4 | 4 | 5 | 3 | 20 |
| Variant 2 | 3 | 3 | 4 | 3 | 3 | 16 |
| Variant 3 | 4 | 4 | 2 | 4 | 4 | 18 |

**Winner:** Variant 1 — byte preservation by construction and full acceptance coverage in the repository's existing suite pattern.
**Anti-overengineering check:** passed — no abstraction beyond functions in one file; the line model solves the stated byte-preservation requirement.
**Evidence:** spec REQ-01, REQ-03, I-8 and the Determinism target; `.ai/principles/architecture.md` P3 (additive contracts, parsers key on field names) and P7 (test-first, suite under the repository test command); `tests/model-catalog.py` and `scripts/validate-contracts.sh:284-343` (suite pattern); `tests/fixtures/validator-runtime/README.md` (fixture procedure); ADR-0021 (single standard-library file in `scripts/`).

### Scope
#### In
- `scripts/state-tool.py` with `get`, `validate`, `set`, `append-note`, `add-file`,
  `init-block` over the progress section of one task `state.md`.
- Structural parser, canonical invariants, per-task advisory lock, expected revision,
  atomic replace, in-block receipts, recovery reporting, test seam.
- Grammar extension `state_receipts:` in `rules/workflow-globals.md` and
  `rules/workflow-reference.md`, with checks in both validators and a vocabulary drift
  check.
- Ignore rules in `.gitignore` and `scripts/setup-new-project.sh`; "State tool" section and
  entry list in `docs/USAGE.md`; inventory row in `scripts/README.md`.
- Acceptance suite `tests/state-tool.py`, its validator registration, refreshed pinned
  fixtures.

#### Out
- Wiring the tool into any workflow; changing `scripts/sync.sh`.
- Writing git fields, `children:` after creation, or unknown fields; creating or deleting
  the section; deleting, renaming or repairing blocks.
- A transition table beyond the listed invariants; network filesystems, Windows writes,
  multi-host locking; run-log telemetry from the tool.
- Removing the grammar duplication between the two rule files.

### Rejected
→ archived to state-archive.md

### Off-limits
- No file under `workflows/` changes; no deployed copy under the home directory is edited.
- The tool writes only the task `state.md`, `<task>/.state-tool.lock` and its own
  `<task>/.state.md.<owner_token>.tmp`.
- The tool never passes an input value to a shell or interpreter and imports no
  third-party module.
- A held lock is never deleted, truncated or taken over; a temporary file the process did
  not create is never deleted or read as state.
- No existing field, vocabulary value, section name or exit code of an existing script is
  renamed or removed.
- No ignore rule may match a task `state.md`.
- No planning identifier or tool attribution in product code, tests, comments,
  documentation, branch names, commits or pull requests.

### Invariants
- After any refused or failed write, `state.md` is byte-identical and no temporary file of
  that process remains.
- After an applied write, every byte outside the changed and inserted lines of the target
  block is identical.
- Read commands create, modify and delete nothing.
- `atomic-tests` is never removed or moved to a lower rank; `pinned` changes only to
  `green`.
- stdout carries exactly one JSON object; diagnostics go to stderr only.
- The tool's vocabulary constants equal the anchored lines of `rules/workflow-globals.md`.
- Blocks without `state_receipts:` remain valid for every reader.
- `scripts/validate-contracts.sh` passes on the stack tip.

### Acceptance Criteria
The task is accepted when spec criteria AC-01–AC-11 and AC-13–AC-23 hold on the stack tip
(AC-12 is withdrawn). Mapping to subtasks:

| Spec criterion | Subtasks |
|---|---|
| AC-01 | T-01 (reads), T-03 (write refusals) |
| AC-02 | T-03 |
| AC-03 | T-01 (reads), T-03 (structure, version, vocabulary), T-05 (transitions) |
| AC-04 | T-03 |
| AC-05 | T-08 |
| AC-06 | T-02 (stale file listing), T-08 |
| AC-07 | T-07 |
| AC-08 | T-01 (read refusals), T-04 (literal note), T-08 |
| AC-09 | T-03 (exits 4, 6), T-07 (exit 8), T-08 (exit 5), T-10 (manual) |
| AC-10 | T-01, T-02 (reads), T-03 (write) |
| AC-11 | T-01 (reporting), T-05 (writes) |
| AC-13 | T-03 |
| AC-14 | T-01, T-03, T-06 |
| AC-15 | T-06 |
| AC-16 | T-04 |
| AC-17 | T-04 |
| AC-18 | T-09 |
| AC-19 | T-01, T-08 |
| AC-20 | T-05 |
| AC-21 | T-01, T-02, T-03, T-04, T-05 |
| AC-22 | T-01, T-02, T-03, T-07 |
| AC-23 | T-10 |

## Model Selection
selection: complete
active provider: anthropic (`Model (Claude)` column)
catalog: ~/.config/orchestrail/model-catalog.md, refreshed 2026-11-09 (fresh, 4 days old; evidence dated 2026-11-09)
support evidence (2026-11-13): the worker tool of this session accepts the model names haiku, sonnet, opus and fable; the session environment lists the identifiers claude-haiku-5-5, claude-sonnet-5-5 and claude-opus-5-5; worker tools: all; context window 1,000,000 tokens is owner-confirmed on 2026-11-13 (the tool does not expose it), not directly observed.
owner limits: allowed models are the three observed identifiers; the session model claude-fable-5-2 has no catalog evidence and was not a candidate.
cost: no qualified comparable total-cost evidence; the strongest eligible baseline was used, so cost optimality is unverified.
reasoning support (2026-11-13): the worker tool exposes the effort levels low, medium, high, xhigh and max and effort is configurable per worker; support per model is not separately observed.
reasoning rationale: catalog quality is measured at maximum effort and the catalog notes the selected model at high effort still meets band 4, which covers every leaf floor here (2–4); lower levels have no recorded evidence, so `high` is recommended for every leaf.
actual model and actual reasoning: unknown until separately observed execution evidence.

| Leaf | Scores (C/A/V/R/Ver/Crit/RW) | Floor | Recommendation | Confidence | Reasoning | Description sha256 | Plan row sha256 |
|---|---|---|---|---|---|---|---|
| T-01 | 3/1/3/3/4/2/3 | 2 | claude-opus-5-5 | verified | high | 755f9fda5e377da356e5271f54d86807928ff475d013c7e822c9de675510b242 | 6ce2122c5b6fc666ab3cd0dc892bb99247afd573da153c7997f76685c9ec5df7 |
| T-02 | 2/1/2/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | fa91922b91c33ed862b60d5c4430184cc6a91bbf72a5c5e518a3a57e41b7e716 | 3149e5789e84ba01435f26a64bba80331b44ee5b46e9419aa65c3f383d2c8253 |
| T-03 | 4/1/2/5/3/4/4 | 3 | claude-opus-5-5 | verified | high | f3ce69a9533c447ec7776a858ac6a5f2e71fb87fba8e8ab2ce1d52fc5d5fdee9 | 13c641e06e231c95f5b02271554ce164da1cda75b204c36268b1e9daa3062f5e |
| T-04 | 3/1/2/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | 6fa33ccf561757d8029f797be2bba2d16a9bd765414b15bcc0661d2e2a86d9c4 | 3b7ece720cd48c1d52cc677d15417983280a887078fb7ad3b731ff5a6ff80c7f |
| T-05 | 3/2/2/4/4/3/3 | 3 | claude-opus-5-5 | verified | high | 27292ea83d48e89242a8b886c45c9a61ee82bd0e75f8fc36043e98b9ceb4640b | 2f10210fc1497db798b70f2f3162a79a9f70b22535a2e61263d94729aae82656 |
| T-06 | 2/1/2/3/4/2/2 | 2 | claude-opus-5-5 | verified | high | 02ec72a354e4e7a1f0c6433baa7574b2502a77dda465426b1d0936eb2b28e17f | 2191236e1912d5b2f12cb910e6e8f93254bbe17704170f88ebf58a063dcd81ff |
| T-07 | 3/1/2/4/4/3/3 | 3 | claude-opus-5-5 | verified | high | 17c6861db6d21193c7c0c9f549359c521133a5174127bd434a8073cf4a4e09de | 39fcc4f183f13a24852f83dbe7bd8e80e3a306cab40e4eb27bc10cfe8f6206e7 |
| T-08 | 4/2/2/5/3/4/4 | 4 | claude-opus-5-5 | verified | high | 79c5534aed44c47153c789f4e2e104475f8f6923d3d8efda971b0057c6744467 | 0ca245069943e183a68833a951fda9ad183d21f0fa5d1962600c95eb2a1ce387 |
| T-09 | 3/1/4/3/4/3/3 | 3 | claude-opus-5-5 | verified | high | 151c91ad5ebc53a20f741e4fe2eed10b4d5dac79c2540bb28e459dd9d74d569e | a14f65ee21e84747c2d4087199bdda67a6ad9d6e0687d7cebee726e546fca747 |
| T-10 | 2/1/3/2/4/2/2 | 2 | claude-opus-5-5 | verified | high | a7748deed11c23ec26acfdc8a72ca69542015dc4a032b525103933296ff80bb7 | c3402c2761b09b1d9d036b2c08f3fa52c48c0a79d1e82f7ec54d9ae25dad655a |
