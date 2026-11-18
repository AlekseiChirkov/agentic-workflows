## Goal
`verify` checks the blockers section in both directions and resolves every `path:line` evidence item against the inventory, and the runbook and module state when a silent `verify` is guaranteed.

## Context
- Dependencies: T-11 (the tool and suite with git read isolation).
- Source: task-level code review findings [4], [5] and [7] (`## Issue List`), deferred as optional and approved by the owner on 2026-11-18 ("fix all findings"). Finding [6] is already closed by `/spec-sync` (REQ-03 verbatim-copy clarification, D-03) and needs no change here.
  - [4] `.ai/context/runbook.md:41-43` says `verify … must print nothing for a delivered audit`, but spec 08 (Contracts, report layout paragraph) guarantees exit 0 only in the delivery repository at the delivery commit; on a later tree `inventory-stale`, `spec09-unavailable` (spec 09 archived) or `req21-invalid` (the discovery rule renamed) are expected. The one-off constants `ALWAYS_SECTIONED` (scripts/audit-instructions.py:2070) and `DISCOVERY_RULE` (:2507) are specific to this audit and are not marked as such.
  - [5] `blocker_rules` (scripts/audit-instructions.py:3613) checks only that every `blocks_09: true` finding id occurs under `## Blockers for spec 09`. DM-8 says the section "names every finding with `blocks_09: true`, or `None.`". A listed finding id that names no finding or a finding with `blocks_09: false`, and a section that is not `None.` when nothing blocks (or `None.` when something blocks), go unreported.
  - [7] `path:line` evidence (in `files[].evidence`, finding, amendment, group and map evidence) is checked only for form. Checked by the orchestrator on 2026-11-18: all 632 evidence items of the delivered assessment resolve — every path is an inventory `files` or `readers` path and every line or range lies within that entry's `lines`; the 40 id items name existing findings or amendments.
- Design (owner-approved scope; spec 08 DM-9 gains the two codes through `/spec-sync` after this subtask, as implemented-beyond with owner approval):
  - new code `blocker-extra`: an `AUD-…` finding id under `## Blockers for spec 09` that names no finding, or a finding whose `blocks_09` is false; location is the report line.
  - the `None.` rule is a `report-layout` diagnostic: when no finding blocks, the section body must be exactly `None.`; when a finding blocks, `None.` must not appear.
  - new code `evidence-unresolved`: an evidence item of the form `path:line` or `path:start-end` whose path is neither an inventory `files` nor `readers` path, whose entry has no line count, or whose line or range is outside `1..lines` (or reversed); a bare `path` item that names no inventory path. Location is `<json file>#<id or index>` as for other assessment diagnostics. Line counts come from the inventory, so a later tree causes no new diagnostic.
  - the runbook line says that `verify` must print nothing at the delivery commit and names the diagnostics a later tree may print; the module marks the two constants as specific to this audit's rule set.
- Constraints: Python 3.11+ standard library only; type annotations on every function; verify writes nothing and runs no new git command; diagnostics keep the `<code> <location> <message>` form and the code-then-location order; comments, docstrings and test names state rules in words without requirement, criterion, finding or specification labels.
- Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script, any specification, or the three audit outputs under `docs/audits/`; no registration in the validator or in sync; never read or change installed copies.

## Scope
- **In scope:** `blocker_rules` and the report-layout check of the blockers section; evidence resolution in `verify`; the two new codes in the module's diagnostic list and docstring; the comments on the two audit-specific constants; the runbook command note; new tests and the suite's list of diagnostic codes.
- **Out of scope:** the audit outputs (they must stay silent under the new checks); spec 08 (reconciled afterwards by `/spec-sync`); any other finding or proposal.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`, `.ai/context/runbook.md`

## Steps
1. Write failing tests: a blockers section listing a non-blocking finding id and an unknown id (`blocker-extra`); a section without `None.` when nothing blocks and one with `None.` beside a blocking finding (`report-layout`); evidence with an unknown path, a line past the entry's count, a reversed range, a line on an entry without a line count, and a bare unknown path (`evidence-unresolved`); valid evidence on audited and reader paths stays silent. Add both codes to the suite's list of diagnostic codes so the every-code fixture test covers them.
2. Implement the reverse blockers check and the `None.` rule.
3. Implement evidence resolution against the inventory's `files` and `readers` line counts for every evidence list of the assessment.
4. Mark the audit-specific constants; correct the runbook note.
5. Run the full standalone suite and `verify --root . --report docs/audits/2026-11-17-rules-workflows-audit.md`.

## Acceptance Criteria
- A listed finding id that is unknown or not blocking yields `blocker-extra` at its report line; a blockers section that breaks the `None.` rule yields `report-layout`; the delivered report yields neither.
- An evidence item that does not resolve against the inventory's paths and line counts yields `evidence-unresolved`; every evidence item of the delivered assessment resolves.
- The runbook note limits the silent-`verify` guarantee to the delivery commit and names the diagnostics a later tree may print; the module marks the two audit-specific constants.
- `python3 -I scripts/check-audit-instructions.py` exits 0 with the earlier 228 tests unchanged except the list of diagnostic codes, which gains exactly the two new codes, and `verify --root . --report docs/audits/2026-11-17-rules-workflows-audit.md` exits 0 with empty output.

## Test Plan
- **Level:** integration
- **Scenarios:**
  - listed non-blocking id, listed unknown id → `blocker-extra`
  - empty section with no blocking finding, `None.` beside a blocking finding → `report-layout`
  - unknown evidence path, line past the count, reversed range, entry without a line count, unknown bare path → `evidence-unresolved`
  - delivered audit → silent
- **Edge cases:** an amendment id (`AMD-…`) in the blockers section is not a finding id and is ignored; a finding id mentioned twice is reported once per line; evidence on a reader that is not decoded; a range whose end equals the line count.
