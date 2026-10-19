# state.md — current task-level state and active work

## Purpose
Canonical task-level context for work on agentic_workflows itself. Loaded at the start
of every session. Updated after every phase transition.

## Active Tasks
- [task-00-sensitive-data-scrub] | phase: validation | status: blocked | note: validation complete, all subtasks reviewed, 542 checks pass; only optional fixture isolation deferred; full knowledge base preserved; publication withheld

 Execution order fixed by ADR-0009 Decision 7 (amended 2026-09-17): **00 (scrub) first** → 01 → 13a → 13 → 04 → 02 → 03 → 05 → 06 → 09 → 08 → 10 → 11 → 12; 07 is backlog. The roadmap is in `specs/README.md`; each spec becomes a task via
`/phase-discovery .ai/specs/<NN>-<slug>.md`.

## Done
- [roadmap-decisions-2026-09] | completed | note: three clarification rounds (116 questions) answered by the owner; ADR-0009 records every decision; all 14 specs amended; question files removed
- [analysis-2026-09] | completed | note: full comparative analysis written to `docs/analysis/2026-09-16-comparative-analysis.ru.md` and `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md`; `.ai/` knowledge base created for the repository itself
- [logic-audit-fixes-2026-07] | completed | note: 20 audit findings (4 blocker, 9 major, 7 minor) applied per `docs/audits/2026-07-21-logic-audit-fixes.md`; `validate-contracts.sh` extended; deployment matrix fixed

## Deferred
None.

## Known conditions (read before starting any task)
- The repository has local Git history. The initial commit contains private references; remote publication is withheld until a separately authorized history-remediation decision.
- `.ai/` in this repository is **committed in full**, including `tasks/todo/` — the
  opposite of the pipeline's default for consumer projects (ADR-0007, accepted 2026-09-16).
- The owner permits local test-first and implementation commits. Current mutable content is scrubbed; the root denylist and source requirement are intentional exceptions. No pushes, pull requests, or history rewrites are authorized by the current run.
- The public name is **Orchestrail**; the rename (directory, `ORCHESTRAIL_HOME`,
  `~/.config/orchestrail/`, `ORCHESTRAIL_LOG_ROOT`) happens in spec 01, not before.
  Until then paths in this knowledge base still say `agentic_workflows`.
- All analysis, audit, and similar documents live under `docs/` (`principles/coding.md →
  Document placement`). The repository root holds only `CLAUDE.md`, scripts, and the
  source directories.
- `validate-contracts.sh` passes 542/542 with the complete indexed knowledge base (2026-10-19); the manual sweep has zero unexpected matches/errors.
- Run log contains 10 runs (4 spec-run, 6 bugfix). Four of them carry values outside the
  `run-log` vocabulary; `/retro` results over this corpus are unreliable until
  `specs/02-run-log-vocabulary-validation.md` lands.
