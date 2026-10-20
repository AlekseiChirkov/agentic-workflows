---
status: done
completed_task: task-00-sensitive-data-scrub
completed_at: 2026-10-19
---

# Scrub sensitive data before further publication

## Goal

Clean the current working tree of private client, employer, internal-system, and machine references, and enforce the agreed public-hygiene scope before further publication.

The original pre-initialization premise no longer holds: an initial Git commit already contains private references. The owner explicitly permitted local failing-test and implementation commits and subsequently authorized publication and merging of the reviewed stack with existing ancestry retained (revised 2026-10-19). Cleaning descendants does not clean their ancestors.

## Acceptance Criteria

### Client, employer, and project identifiers

- [x] No occurrence of `vention`, `lattice_lab`, `mariner-gulf`, `dbt_dw`, `invest_ai`,
      `investment_analyst`, or `alterra` (case-insensitive) outside the explicitly approved exceptions: this source specification, Git internals, local logs, and local settings (amended 2026-10-20)
- [x] The checkout keeps living under a parent directory named `alterra` on the
      maintainer's machine (owner's decision, 2026-09-17). That name must therefore never
      be written into a file: scripts resolve their own location, documentation writes
      `<orchestrail>/…` or `~/projects/orchestrail/…`, and `alterra` stays on the denylist
      so a re-introduced absolute path fails the check
- [x] `docs/USAGE.md → ## 3` uses a neutral umbrella example (`acme-platform/` with
      `service-api`, `service-worker`, `service-frontend`, `infra`) and neutral paths
      (`~/projects/acme-platform`)
- [x] `templates/.ai-umbrella/README.md` uses the same neutral example
- [x] `workflows/retro.md` example reads `/retro --project ~/projects/acme-platform`
- [x] `.ai/context/environment.md → ## Environments → Consumer projects` names no real
      project: the list is replaced by "consumer projects are recorded in the local
      registry; none is named here"
- [x] `.ai/memory/progress.md` refers to runs by pipeline, run id, and date only —
      never by project name (e.g. "spec-run 41b4496e (a client service repository)")
- [x] `docs/analysis/2026-09-16-comparative-analysis.ru.md` and its TL;DR replace project
      names with `Project A` / `Project B` / `Project C` and keep a one-line legend saying the
      mapping is intentionally not recorded
- [x] `docs/analysis/2026-09-16-rules-workflows-naming-review.md` and
      `docs/audits/2026-07-21-logic-audit-fixes.md` carry no project name

### Internal system details of client work

- [x] `rules/quick-flow.md` worked examples are rewritten against a fictional system: no
      `nowpayments_service.py`, `report_builder.py`, `MacroTechnical.tsx`, `macro_metrics`,
      `task1_subscription_fix`, invoice/IPN specifics, or HTTP status details taken from
      real code. The examples keep their teaching value: one rejected by the gate (a
      multi-file behaviour change to a shipped pipeline) and one accepted (a log-level
      change in one file)
- [x] The same substitution is applied wherever those names appear elsewhere
      (`rules/tdd.md`, `rules/workflow-reference.md`, `docs/USAGE.md`, `.ai/`)
- [x] `.ai/memory/progress.md` and `.ai/adr/*` contain no pull-request number, workflow-run
      id, or other identifier from a client repository (`PR 732`, `run 33612468450`, …)
- [x] `.ai/principles/architecture.md` and `domain.md` examples use neutral domain terms

### Personal machine and path leakage

- [x] No `Prestige-14Evo`, no user name, and no `$HOME`-absolute path (in particular none
      containing `alterra`, the real parent directory) outside a placeholder: scripts resolve their own location or retain the existing
      `WORKFLOWS_SOURCE` / `AGENTIC_LOG_ROOT` overrides; the public variable rename remains separate (revised 2026-10-19); documentation writes
      `<orchestrail>/…` or `~/.config/orchestrail/…`
- [x] `docs/audits/AUDIT-PROMPT.md` refers to "the repository root", not an absolute path
- [x] `.ai/context/environment.md` records the host as "the maintainer's workstation"

### Guard so it cannot come back

- [x] `validate-contracts.sh` accepts a local forbidden-token pattern file through
      `ORCHESTRAIL_HYGIENE_DENYLIST` or `--denylist`, scanning every indexed
      working-tree path with only this source specification exempt
- [x] The pattern file stays outside the repository; explicit scan inputs fail
      closed when missing, unreadable, empty, or when scanning fails
- [x] The tracked pattern list was removed before publication; maintainers can
      keep their private hygiene patterns in local configuration without
      exposing those identifiers in the repository
- [x] A final manual sweep remains recorded with explicit tree scope, excluding
      Git internals, local logs/settings, and this source specification; current exact
      scans use a local-only pattern input
- [x] `.gitignore` excludes local logs and `.claude/settings.local.json`, while the complete `.ai/` directory is included without deleting any existing file. The source specification remains the only exact scan exception (amended 2026-10-20)

## Out of Scope

- Credentials, tokens, keys — none were found in the tree; the check group added here
  does not attempt secret detection (a separate concern if the repository ever holds one)
- Rewriting the run log store (`logs/` is untracked and stays local)
- `.claude/settings.local.json` (untracked; it keeps machine-specific allow-rules)
- The Orchestrail rename itself (spec 01) — this spec only removes what must never be
  committed; path constants are renamed in 01

## Notes

- Runs before the remaining roadmap work. The owner permitted local test-first commits, then explicitly authorized publication, merging, and completed-record archival with existing ancestry retained (revised 2026-10-19). ADR-0010 records the amended timing clause of ADR-0009 Decision 1.
- Inventory as of 2026-09-17 (file → what): `docs/USAGE.md` (umbrella example, 19 hits),
  `docs/analysis/*` (run table by project), `.ai/context/environment.md` (consumer list,
  host name), `.ai/memory/progress.md` (project names, PR and run ids),
  `rules/quick-flow.md` (two worked examples from client code), `workflows/retro.md`
  (example path), `templates/.ai-umbrella/README.md` (umbrella example), plus
  `~/Documents/projects/alterra/…` literals in six scripts and eleven workflow/rule files.
- The local checkout stays at `~/Documents/projects/alterra/orchestrail/` after spec 01's
  rename; `alterra` is a private path component and is on the denylist precisely because it
  must not appear inside any file. `sync.sh` resolving its own location and
  `ORCHESTRAIL_HOME` make that possible.
- The historical documents under `docs/` are edited rather than deleted: they are the
  record of how the system evolved, and their value does not depend on the project names.
- Test level: `smoke` — the new `validate-contracts.sh` check group is written first and
  observed failing on the current tree, then the tree is cleaned until it passes.

## Change Log

### 2026-10-20 — keep private hygiene patterns local
- Pattern source | implemented-differently | The tracked pattern file remains deleted. The scanner now accepts a local pattern file through `ORCHESTRAIL_HYGIENE_DENYLIST` or user configuration; no pattern contents are committed.
- Missing local configuration | implemented-differently | Contract fixtures continue to exercise fail-closed scanning with synthetic patterns. The full-suite exact scans report `SKIP` when no local private patterns are configured, while an explicit scan still fails closed.

### 2026-10-19 — reconciled after validated working-tree cleanup
- Timing | implemented-differently | Existing Git history is preserved; local test-first commits are permitted and remote publication is withheld. Source: owner answer 2A, task Description Amendments, ADR-0010 Decision 3.
- Scan scope | implemented-differently | Exact source/list exceptions make the literal criterion satisfiable; all other mutable context remains scanned. Source: owner answer 1A, task Description Amendments, ADR-0010 Decision 1.
- Configuration | implemented-differently | Portable defaults preserve current source/log overrides; the public variable rename stays separate. Source: recorded Assumptions and ADR-0010 Decision 4.
- Replacement language | implemented-differently | New historical labels and legends are English while existing Russian prose is preserved. Source: recorded Assumptions and global language instructions.
- Knowledge-base inclusion | implemented-beyond | Every baseline file is retained and the complete knowledge base is tracked. Source: explicit owner clarification, task Contract Check, ADR-0010 Decision 2.

## Optional Followup

The isolated Git enumeration-error fixture can be refined later. Production failure handling is already independently verified; this does not defer any hygiene criterion.

### 2026-10-19 — completed delivery and archival
- Publication and integration | owner-authorized | The earlier hold was superseded by explicit approval to publish existing ancestry, merge the three reviewed pull requests, and close the task. No history rewriting was performed.
- Record location | owner-authorized | The complete task is retained under `.ai/tasks/completed/task-00-sensitive-data-scrub/`; this source is retained under `.ai/specs/completed/`. The exact scanner exception follows this source file; its previous path is no longer exempt.
- Review corrections | verified | Suggested child setup commands preserve absolute source overrides, and unreadability fixtures pass as both the normal user and UID 0. All 542 checks pass.
