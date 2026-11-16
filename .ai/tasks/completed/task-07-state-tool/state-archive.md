# state-archive — task-07-state-tool

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Deliver an optional, deterministic, standard-library Python tool, `scripts/state-tool.py`,
that reads and validates the `## Subtask Progress` section of one task `state.md`
structurally and changes one block's agreed fields under a per-task OS advisory lock, an
expected-revision check and durable idempotency receipts, replacing the file atomically or
not at all. The delivery also adds the additive `state_receipts:` grammar extension with
its validator checks, ignore rules for the tool's auxiliary files, and usage
documentation. The tool stays unwired: no workflow calls it.

### Affected Parts
- New: `scripts/state-tool.py` (commands `get`, `validate`, `set`, `append-note`,
  `add-file`, `init-block`), its acceptance suite under `tests/`, and a focused validator
  mode in `scripts/validate-contracts.sh`.
- Contract files: `rules/workflow-globals.md` (one anchored `state_receipts:` line plus a
  reader rule), `rules/workflow-reference.md → ## Protected Sections Contract`.
- Validators: `scripts/validate-task.sh` (receipts check; the message at line 141 omits
  `pinned`), `scripts/validate-contracts.sh` (anchored line, protected entry, vocabulary
  drift check between the tool constants and `rules/workflow-globals.md`).
- Ignore rules: `.gitignore`, `GITIGNORE_ENTRIES` in `scripts/setup-new-project.sh`,
  entry list in `docs/USAGE.md` section 5.
- Documentation: `docs/USAGE.md` "State tool" section, `scripts/README.md` inventory row.
- Fixture: `tests/fixtures/validator-runtime/source_guard_exceptions.json` — digests of
  every pinned script the task edits are refreshed by the recorded maintenance procedure.
- Knowledge (orchestrator-applied at finalization): `.ai/memory/architecture.md` script
  inventory and contract surface, `.ai/memory/state.md`, `.ai/memory/progress.md`.
- No workflow file under `workflows/` changes (spec Out of Scope, D-07).

### Codebase Analysis
- `scripts/validate-task.sh` — read to verify the existing section checks: line greps over
  the whole file (Group 5, lines 133–170) and the TDD trail (Group 6); exits 0/1/2; the
  vocabulary message at line 141 lists five `atomic-tests` values while the pattern accepts
  six. A receipts check fits as a new check inside Group 5.
- `scripts/validate-contracts.sh` — read (targeted) to verify registration patterns: each
  acceptance suite has a focused `--<name>-only` mode near the top (lines 45–343) and a
  `check "test_<name>_acceptance"` registration in the default run; checks use the
  `check "<desc>" "$(… && echo pass || echo '<reason>')"` form.
- `scripts/setup-new-project.sh` — read to verify `GITIGNORE_ENTRIES` (lines 247–254): a
  fixed-string `grep -qF` append loop, already idempotent; a missing `.gitignore` is created.
- `.gitignore` — read to verify no existing pattern covers the lock or temporary files and
  that `.ai/` is not ignored here.
- `docs/USAGE.md` — read to verify the entry list (line 310, step 6 of the setup table) and
  the section layout (numbered sections 1–10); a "State tool" section is new.
- `scripts/README.md` — read to verify the inventory table lists shell helpers only today;
  the spec requires a row for `state-tool.py`.
- `tests/` — listed to verify suite naming: shell suites (`git-rails.sh`, `hook-*.sh`) and
  Python suites (`model-*.py`, `usage-*.py`) both exist and are each registered in the
  validator.
- `rules/workflow-globals.md`, `rules/workflow-reference.md` — canonical grammar and
  protected list verified against the spec's citations (knowledge files, outside the budget).

Files read: 7/12 (7 entry-points, 0 deeper).

### Open Questions
None. The spec records no open question; the remaining choices (suite file name and
language, internal module structure, subtask boundaries) are design decisions resolved in
decomposition and design.

## Archived Solution Design — Variants
1. **Line-preserving document model, Python suite under `tests/`.** The tool keeps
   `state.md` as its original list of lines and classifies each line (section heading,
   block header, field line, continuation, foreign). A write replaces or inserts whole
   lines by index and joins the list back, so untouched bytes are identical by
   construction; the post-serialization re-parse confirms it. Pure functions for parsing,
   invariants, receipts and edits are separate from the command line. The acceptance suite
   is `tests/state-tool.py` (`unittest`, subprocess runs on disposable fixtures plus
   in-process cases through `runpy`), registered as `--state-tool-only` and in the default
   validator run; each subtask refreshes the pinned validator-runtime fixtures.
   Advantages: byte preservation is structural; in-process fault cases and the AST scan are
   natural in Python; follows the existing `tests/model-*.py` suites. Disadvantages: every
   subtask pays the fixture refresh. Risks: reviewed call-site records for subprocess use.
2. **Parsed block objects with canonical re-serialization, shell suite.** The target block
   is parsed into an object and written back from it; the suite is `tests/state-tool.sh`.
   Advantages: simpler edit code. Disadvantages: re-serialization must reproduce quoting,
   blank continuation lines and unknown fields exactly — the normalization risk the spec
   forbids; shell cannot run the in-process directory-sync case or the AST scan without
   embedded Python. Risks: silent byte drift in legacy blocks.
3. **Line-preserving model, suite kept outside the pinned test inventory.** Same tool
   design, with the suite as a standalone script that the validator does not register,
   and one fixture refresh at the end. Advantages: no per-subtask refresh. Disadvantages:
   the tool would sit outside the repository test command until the last subtask;
   breaks the pattern that every suite has a focused mode and a default registration;
   validator checks for the grammar extension still need the refresh.

## Archived Solution Design — Rejected
- Variant 2 — re-serialization risks byte drift in legacy blocks; a shell suite cannot run
  the in-process cases.
- Variant 3 — leaves the tool outside the repository test command for most of the stack.
- Spec-level rejections stay rejected: full transition table, vocabulary-only checks,
  lock directory with an owner protocol, revision-only optimistic writes, sidecar receipt
  journal, no receipts, a `bin/` location.
