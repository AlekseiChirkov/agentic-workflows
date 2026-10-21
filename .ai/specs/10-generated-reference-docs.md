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
- [ ] `gen-docs.py` renders each `harness/<name>/always-on.md` from `templates/always-on-core.md`
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
- Depends on 13 (front matter/harness layout) and 08 (load declarations/reference tiers).

## Optimization integration — 2026-10-21

- **REQ-01** THE SYSTEM SHALL render mandatory/conditional load metadata without
  eagerly inlining reference bodies, task context, examples or mutable run state into
  always-on files. Generated instruction size SHALL satisfy 08 and 13.
- **REQ-02** THE SYSTEM SHALL distinguish source fragments from deployed rendered
  artifacts, include reproducible source hashes and generate the capability table once.
  Sync SHALL not append a second copy after rendering.
- **REQ-03** THE SYSTEM SHALL render the available context/tool/review/effort/repair
  interfaces from canonical metadata when present and mark absent optional features
  honestly. It SHALL NOT invent supported model IDs, prices or savings from prose.
- **REQ-04** THE SYSTEM SHALL fail stale-reference/size checks offline, avoid network
  or model calls and preserve profile fragments only in project-local files.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02) Two renders are identical, contain one capability table,
  keep conditional reference bodies out of global instructions and satisfy word gates.
- [ ] **AC-02** (REQ-03, REQ-04) Minimal/full optional-feature metadata renders accurate
  docs; stale or broken targets fail without provider calls or global profile leakage.

The shared core is a non-deployed template, not another always-on rule skill.
Keep its single home consistent with 13/08. Optional tools stay optional at
execution time; a maintainer documentation generator need not be a workflow runtime.
