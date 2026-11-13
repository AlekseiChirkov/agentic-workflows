## Goal
`python3 scripts/state-tool.py init-block` inserts a new leaf or composite block with the
canonical initial lines at the end of the existing progress section, and refuses an id
that already exists.

## Context
- Dependencies: T-03 (write transaction), T-04 (note and path content rules).
- Constraints: same runtime limits as the tool. Contract: task spec REQ-16,
  `### Commands` (`init-block` form, canonical initial lines, id and children rules,
  step 1 argument validation), `### Block insertion layout`, `### Output`
  (`changed_fields` for an applied `init-block`, `block_kind` on refusal). English only;
  no planning identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint; follow `tests/fixtures/validator-runtime/README.md`.
- Reason: creating a block is the only operation that adds lines outside an existing
  block; its layout and argument rules are verifiable on their own.

Off-limits: never creates or deletes the `## Subtask Progress` section; never changes an
existing block; `children:` is written at creation only; no file under `workflows/` or
`rules/`.

## Scope
- **In scope:** `init-block` argument validation; canonical leaf and composite lines;
  insertion layout; `block-exists`; receipt on the new block; `changed_fields` listing
  every header field and field line written.
- **Out of scope:** checking that child blocks exist; reordering or renaming blocks.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below.
2. Validate arguments (exit 2 `invalid-arguments`): `--kind leaf|composite`, non-empty
   `--name` without `|`; `--kind composite` without `--children` or without `--note`;
   `--target-file` with `--kind composite`; `--children` with `--kind leaf`; `--children`
   split on `,` with no surrounding spaces, each item matching the block-id pattern, no
   empty item, no repeated item, not the block's own id.
3. Build the canonical lines — leaf: header with the three statuses `not-started`,
   `  last_action:`, `  target_files: <paths joined by ", ">`, `  blocker: none`,
   `  notes: <first note>` plus 9-space continuation lines, `  state_receipts: <entry>`;
   composite: `[composite]` header with `rollup` and `integration-validation`
   `not-started`, `  children: <ids joined by ", ">`, `  blocker: none`, `  notes: …`,
   `  state_receipts: …`; an empty value is written as `  name:` with no trailing space.
4. Implement the insertion layout: find the last non-blank line L of the section; directly
   after the heading when L is the heading, otherwise one blank line and then the block
   after L; blank lines that followed L stay after the new block.
5. Refuse an existing id with exit 6 `block-exists` and a missing section with exit 3
   `section-missing`, leaving the file unchanged.
6. Refresh the pinned source-guard fingerprint and run the guard suites and the suite
   (`python3 tests/state-tool.py`).

## Acceptance Criteria
- Given a section whose last block ends with `  pr: none` followed by one blank line and
  `## Next`, `init-block --block T-05 --kind leaf --name Demo` gives `  pr: none`, a blank
  line, the canonical leaf lines for `T-05`, a blank line, `## Next`.
- Given a section holding only its heading, the block follows the heading directly.
- Given an existing `T-05`, the command exits 6 `block-exists` and the fixture is
  unchanged; given no section, it exits 3 `section-missing`.
- `--kind composite` without `--note`, and `--target-file` with `--kind composite`, exit 2
  `invalid-arguments`.
- `--children T-01a,,T-01b`, `--children T-01a,T-01a` and `--children "T-01a, T-01b"`
  exit 2.
- An applied composite `init-block --children T-06a,T-06b --note "two components"` writes
  the `[composite]` header, `  children: T-06a, T-06b`, `  blocker: none`, the note and a
  `state_receipts:` line; `get --block` on it reports `block_kind` `composite`.
- A leaf created with `--target-file a.sh --target-file a.sh --target-file b.sh` has
  `  target_files: a.sh, b.sh`; without notes its `  notes:` line has no trailing space.
- `changed_fields` of an applied `init-block` lists every header field and field line
  written, with `state_receipts` last; `validate` on the result exits 0.

## Test Plan
- **Level:** integration (subprocess runs against disposable fixtures).
- **Scenarios:**
  - Section ending with a block, a blank line and another heading → exact layout.
  - Heading-only section → block directly after the heading.
  - Existing id, missing section → exit 6 / exit 3, unchanged.
  - Invalid kind combinations and children lists → exit 2.
  - Composite creation → canonical lines and reported kind.
  - Repeated target file, no note → single entry, bare `notes:` line.
  - `changed_fields` and follow-up `validate` → full list, exit 0.
- **Edge cases:** section at end of file without a final newline; section whose last
  non-blank line is a column-0 foreign line; fix-task id form `T-04-fix-some-slug`.
