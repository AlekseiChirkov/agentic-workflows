## Goal
The tool's lock and temporary files are ignored by git in this repository and in newly
set-up consumer projects, and the operating manual documents the tool, its exit codes and
the manual fallback.

## Context
- Dependencies: T-08 (final behaviour of the lock and temporary files and of every
  refusal the manual describes), T-09 (the protected field the manual mentions).
- Constraints: contract: task spec REQ-26, REQ-10 (documentation part),
  `### Contract-file changes`. `scripts/setup-new-project.sh` stays idempotent and sets
  `-e`; its digest is pinned in the validator-runtime fixture. Numbers quoted in docs are
  updated in the same change. English only; no planning identifiers in product content.
- Pinned fixtures: edits to `scripts/setup-new-project.sh` and under `tests/` invalidate
  pinned digests; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: ignore rules and the manual are the consumer-facing surface of the tool; the
  manual names the ignore patterns and the step for existing projects, so they are
  verified together.

Off-limits: no task `state.md` may match an ignore rule; `scripts/sync.sh` is not
changed; no workflow is wired to the tool; deployed copies are never edited.

## Scope
- **In scope:** `.gitignore` lines `.state-tool.lock` and `.state.md.*.tmp`; the same two
  patterns in `GITIGNORE_ENTRIES` of `scripts/setup-new-project.sh`; the entry list of the
  setup table in `docs/USAGE.md`; a "State tool" section in `docs/USAGE.md` (commands,
  exit codes, manual fallback, known limits, the rerun-or-by-hand step for an existing
  consumer project that tracks `.ai/`); an inventory row for `state-tool.py` in
  `scripts/README.md`; refreshed pinned digests.
- **Out of scope:** adding ignore entries through `scripts/sync.sh`; changing how
  consumer projects track `.ai/`.
- **Target files:** `.gitignore`, `scripts/setup-new-project.sh`, `docs/USAGE.md`,
  `scripts/README.md`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases: `git check-ignore` on the two auxiliary paths and on a task
   `state.md`; `scripts/setup-new-project.sh` run twice in a disposable git project;
   content checks on `docs/USAGE.md` and `scripts/README.md`.
2. Add the two patterns to `.gitignore` under a comment naming the state tool's auxiliary
   files.
3. Add the two patterns to `GITIGNORE_ENTRIES` in `scripts/setup-new-project.sh`, keeping
   the append loop's once-only behaviour.
4. Update the entry list in the setup table of `docs/USAGE.md` to name both patterns.
5. Write the "State tool" section of `docs/USAGE.md`: purpose and optional status; the six
   command forms; the exit-code table; the manual fallback steps (stop concurrent
   writers, read the whole block, change only the needed fields, review the diff, run
   `scripts/validate-task.sh`, record the reason in `notes:`); the rule that a refusal is
   never bypassed by a manual edit; limits (external editors ignore the lock, local
   filesystems only, reads only without `fcntl`); the step for an existing consumer
   project that tracks `.ai/`: rerun `scripts/setup-new-project.sh` or add the two lines
   by hand.
6. Add the `state-tool.py` row to the inventory table of `scripts/README.md`.
7. Refresh the pinned digests of `scripts/setup-new-project.sh` and the source-guard
   fingerprint, then run the guard suites and the focused state-tool mode.

## Acceptance Criteria
- In this repository `git check-ignore -q` exits 0 on
  `.ai/tasks/todo/task-x/.state-tool.lock` and on
  `.ai/tasks/todo/task-x/.state.md.0123456789abcdef0123456789abcdef.tmp`, and exits 1 on
  `.ai/tasks/todo/task-x/state.md`.
- In a disposable git project where `scripts/setup-new-project.sh` ran twice, `.gitignore`
  contains the lines `.state-tool.lock` and `.state.md.*.tmp` exactly once each.
- The entry list of the setup table in `docs/USAGE.md` names both patterns.
- `docs/USAGE.md` has a "State tool" section that lists the manual fallback steps — stop
  concurrent writers, read the whole block, change only the needed fields, review the
  diff, run `scripts/validate-task.sh`, record the reason in `notes:` — and tells an
  existing consumer project that tracks `.ai/` to rerun `scripts/setup-new-project.sh` or
  add the two lines by hand.
- The section lists the six commands and exit codes 0–8 with their meanings.
- `scripts/README.md` has an inventory row for `state-tool.py`.
- The source-guard suites pass with the refreshed digests.

## Test Plan
- **Level:** integration (git and setup script in disposable projects) and smoke
  (documentation content checks).
- **Scenarios:**
  - Ignore check on lock, temporary file and `state.md` → 0, 0, 1.
  - Setup run twice → each pattern exactly once.
  - Manual content → entry list, section, fallback steps, consumer step, commands, exits.
  - Script inventory → row present.
  - Guard suites → pass.
- **Edge cases:** consumer `.gitignore` absent before setup (created); consumer
  `.gitignore` already holding one of the two patterns (not repeated).
