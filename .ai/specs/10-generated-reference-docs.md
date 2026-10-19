# Generate reference documentation and always-on files from source

## Goal

The command tables in `docs/USAGE.md`, `docs/PIPELINE.md`, and the child-workflow table
in the state-files contract restate the same facts by hand, and the two always-on files
are maintained separately. Make workflow front matter the source of the reference
tables and a shared core body the source of every harness's always-on file (ADR-0009,
Decision 6).

## Acceptance Criteria

- [ ] Every `workflows/*.md` front matter carries `description:`, `phase:`, `step:`,
      `loads:` (spec 08), `reads:`, `writes:`, `called_by:`
- [ ] `bin/gen-docs.py` renders `docs/reference/commands.md` (all workflows by phase and
      step), `docs/reference/rules.md` (all rules by kind with `load:` mode), and
      `docs/reference/statuses.md` (from the state-files contract); `docs/USAGE.md` links
      to them and contains no hand-written copy of those tables
- [ ] `gen-docs.py` renders each `harness/<name>/always-on.md` from `rules/always-on-core.md`
      plus `harness/<name>/always-on-header.md` plus the harness's `capabilities.md`
      table; `sync.sh` deploys the rendered file
- [ ] Profile fragments (spec 11) are **not** rendered into the global always-on files;
      the generator exposes a `--profile <name>` mode used by `setup-new-project.sh` for
      the project-local `CLAUDE.md` / `AGENTS.md`
- [ ] `validate-contracts.sh` fails if any generated file is stale (renders to a temp
      file and diffs)
- [ ] Counts quoted in docs ("N workflows", "N checks") are rendered, not typed

## Out of Scope

- Generating workflows or rules themselves
- A documentation site (later)

## Notes

- Decisions: ADR-0009 Decision 6 (separate `docs/reference/` files; always-on = core body
  + per-harness header; Python generator; profile fragment project-local only —
  Decision 6 and round-3 R3-05).
- Runs after spec 13 (front-matter keys, `harness/` layout).
