# Audit of every rule and workflow file before the naming sweep

## Goal

Spec 13 renames every rule and command and splits files by kind. Before touching
anything, the tree must be inventoried so that the renames are decided from evidence:
which files mix kinds, which citations are ambiguous, which statements are duplicated,
and where IDE-specific content lives. This spec produces that audit and nothing else;
spec 13 is amended from its findings via `/spec-sync` (ADR-0009, Decision 3).

## Acceptance Criteria

- [ ] `docs/audits/YYYY-MM-DD-rules-workflows-audit.md` exists with one row per file in
      `rules/` and `workflows/` (derive the inventory from the actual checkout) and the columns: kind (`bootstrap | contract
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

## Optimization review additions — 2026-10-21

- **REQ-01** THE SYSTEM SHALL inventory the actual rules/workflows/harness adapters
  at the reviewed source revision, not enforce a historical file count or assume
  a capability from a provider name.
- **REQ-02** THE SYSTEM SHALL identify repeated bootstrap loads, mandatory versus
  conditional context, duplicated report/checkpoint text and raw tool-output paths,
  with concrete source sections and proposed single ownership in 08/14/15/16/17.
- **REQ-03** THE SYSTEM SHALL distinguish textual/byte/word observations from measured
  tokens/cost, record source-versus-installed drift where evidence is available, and
  reference 05 for monetary baselines rather than infer savings from this audit.
- **REQ-04** THE SYSTEM SHALL check active-spec cross-references and naming/capability
  assumptions, preserve completed historical records and propose explicit 13 amendments.
  It SHALL not rename workflows, deploy files, spawn model tests or implement optimizations.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02) Audit rows match the real source inventory and every
  duplication/load recommendation names source sections and one owning spec.
- [ ] **AC-02** (REQ-03, REQ-04) Cost claims have measurement provenance or are labeled
  unavailable; amendments distinguish active contracts from history and no runtime/
  deployment change is included in the audit delivery.

Depends on 01 as before. The additional inspection stays documentation-only and
precedes 13; the optimization specs consume its findings after the naming sweep.
