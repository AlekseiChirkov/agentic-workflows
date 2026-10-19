# Audit of every rule and workflow file before the naming sweep

## Goal

Spec 13 renames every rule and command and splits files by kind. Before touching
anything, the tree must be inventoried so that the renames are decided from evidence:
which files mix kinds, which citations are ambiguous, which statements are duplicated,
and where IDE-specific content lives. This spec produces that audit and nothing else;
spec 13 is amended from its findings via `/spec-sync` (ADR-0009, Decision 3).

## Acceptance Criteria

- [ ] `docs/audits/YYYY-MM-DD-rules-workflows-audit.md` exists with one row per file in
      `rules/` and `workflows/` (52 today) and the columns: kind (`bootstrap | contract
      | protocol | procedure | always-on | workflow | reference`), load mode, word count,
      files it cites, files that cite it, lines mentioning Windsurf / Devin / Codeium
- [ ] A "mixed-kind files" table names every rule whose content spans more than one kind
      with the section boundaries — at least `phase-atomic-execution` (Blocker
      Reconciliation) and `phase-discovery` (Decision Protocol, Codebase Reading Rules)
- [ ] An "ambiguous citations" table lists every citation with a `.md` suffix on a
      colliding basename or a section name that does not exist in the cited file — at
      least `workflows/phase-pipeline.md:185` and `:225`
- [ ] A "duplicated statements" table lists every statement appearing verbatim or
      near-verbatim in two or more of `rules/`, `workflows/`, `docs/USAGE.md`,
      `workflows/PIPELINE.md`, with the proposed single home
- [ ] A "proposed rename map" table gives, for every file, its target name under the
      `<kind>-<subject>` scheme and the command rename map of ADR-0009 Decision 3, with
      any deviation from the decided scheme justified
- [ ] A list of amendments spec 13 needs, each phrased as a change to a `REQ-NN` or a
      new requirement
- [ ] `docs/README.md` links the audit; nothing outside `docs/` and `.ai/` is modified

## Out of Scope

- Any rename, move, or edit of `rules/`, `workflows/`, or scripts
- Running `sync.sh`

## Notes

- Decisions: ADR-0009 Decision 3 (audit as its own spec, run before 13) and Decision 7
  (order 01 → 13a → 13).
- Test level: `none` — documentation-only; unit/integration/contract/smoke have no
  behaviour to assert; the deliverable is checked by review against the criteria above.
- Reuse the method of `docs/audits/AUDIT-PROMPT.md` (read the whole surface before
  judging any part; defects are relational).
