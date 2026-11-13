# state.md — current task-level state and active work

## Purpose
Canonical task-level context for work on Orchestrail itself. Loaded at the start
of every session. Updated after every phase transition.

## Active Tasks


Execution order fixed by ADR-0009 Decision 7 (amended 2026-09-17; ADR-0017 moves 06 before 13a/13): **00 (scrub) first** → 01 → 13a → 13 → 04 → 02 → 03 → 05 → 06 → 09 → 08 → 10 → 11 → 12; 07 is scheduled outside this order (ADR-0021). The roadmap is in `specs/README.md`; each spec becomes a task via
`/phase-discovery .ai/specs/<NN>-<slug>.md`.

- [State tool](../specs/07-state-tool.md) | phase: not started | status: scheduled 2026-11-13 by owner decision (ADR-0021) | note: next step `/spec-run .ai/specs/07-state-tool.md`; no task directory yet.

Runtime work was closed by owner decision; remaining roadmap scope is not automatically scheduled.

## Done
- [State tool specification](../specs/07-state-tool.md) | completed: 2026-11-13 | note: backlog spec refined in English; design ready (4 review rounds, 100/100; amended spec re-reviewed in 2 rounds, 98/100); scheduled the same day (ADR-0021 records the schedule, lock and executable-path amendments); Q-01 resolved by adding ignore rules to the scope (REQ-26, AC-23).
- [Contract suite repair](../adr/0020-task-unknown-source-guard-watchdog-timeouts.md) | completed: 2026-11-13 | note: six failures fixed — identity ledger re-lined after the owner's audit deletions and spec edits (token totals unchanged); guard watchdog timeouts raised and exceptions re-pinned by the fixture procedure; mise shim failures resolved per run with `MISE_PYTHON_VERSION`.
- [Specification review loop](../adr/0019-task-unknown-spec-draft-devils-advocate-review.md) | completed: 2026-11-13 | note: `/spec-draft` self-review replaced by a separate read-only Devil's Advocate critic, at most 10 rounds, 100-point rubric with severity caps, pass at 95 with no open critical or major finding; standalone `scripts/check-spec-draft.sh` (about 30 ms) outside the frozen validator inventory.
- [Validator runtime](../tasks/completed/task-06-1-test-suite-runtime/state.md) | status: completed | closure: owner-directed, 2026-11-06 | note: #77–#79 integrated, archival commit 23bded3; partial implementation only. Concurrent acceptance execution, opt-in timing, the additional scanner I/O correction and comparative targets remain undelivered; phase/AC evidence was not promoted to passing.
- [Specification delivery review](../../docs/audits/2026-11-06-specification-delivery-review.md) | completed: 2026-11-06 | note: all 23 specifications reviewed against current source, tests and task evidence; seven completed foundations retained, runtime closure distinguished from acceptance, fifteen roadmap/backlog specifications remain unimplemented as complete contracts.
- [Enforced git rails](../tasks/completed/task-06-harness-git-rails/state.md) | phase: validation | status: reviewed | note: 10 subtasks + 2 fix groups independently validated; all 12 branches merged into main in stack order as merge commits e9c7216…a17e8a8 (#64 shows merged; #65–#75 closed with the merge commit noted, because GitHub cannot record a merge whose base is a stack branch); full checks 717/0/2 at the tested tip, whose tree main matches exactly; residual risks X1–X20; owner chose 06 before 13a/13 (ADR-0017 Accepted)
- [Validator runtime specification review](../../docs/analysis/2026-11-05-validator-runtime-review.md) | completed: 2026-11-05 | note: current test architecture inspected; independent scores 7.0 → 9.3 → 9.6 → 9.7/10; revised specification ready for development; 2,346 git-rails tests passed in 288.15 s wall; optimizations remain unimplemented
- [Cost and duration telemetry](../tasks/completed/task-05-cost-and-duration-telemetry/state.md) | phase: validation | status: reviewed | note: 27 PRs independently reviewed, 18 repairs independently verified, all knowledge included; full checks 619/0/2; synthetic source and external authority deployment limits remain
- [Cached model catalog](../tasks/completed/task-04-model-catalog-cache/state.md) | phase: validation | status: reviewed | note: owner-authorized independent review and integration complete; all six PRs #31–#36 merged; full validation 594/0/2, no required repairs; main 111455ac171c7356d083e00d4d307a7285ed2e35 exactly matches the tested tree
- [Workflow instruction maintenance] | completed | note: all 42 workflows clarified and reduced in two passes; 18 active specs reconciled, four completed records preserved; 589 full-suite checks pass with two optional skips; the pre-existing unstaged archive condition passes the unchanged strict gate in a disposable index
- [Hook-based logging](../tasks/completed/task-03-hook-based-logging/state.md) | phase: validation | status: reviewed | note: seven leaves and prerequisite reviewed; separate final PR reviews and producer hardening complete; PRs #22–#29 merged in order; final validation 594/0/2
- [Run-log vocabulary validation](../tasks/completed/task-02-run-log-vocabulary-validation/state.md) | phase: validation | status: reviewed | note: strict producer, read-only lint, usable retrospective metrics, drift gate and isolated acceptance complete; PRs #13–#20 integrated; source specification and task archived
- [task-00-sensitive-data-scrub](../tasks/completed/task-00-sensitive-data-scrub/state.md) | completed | note: PRs #2, #3, and #4 integrated in order; review fixes included; 542 checks pass as normal user and UID 0; source specification archived under specs/completed
- [Git source of truth] | completed | note: versioned contracts, portable runtime paths, public materials, identity checks, and validation metadata are complete; checkout is renamed; PRs #5–#9 were merged into main; owner deferrals remain documented
- [roadmap-decisions-2026-09] | completed | note: three clarification rounds (116 questions) answered by the owner; ADR-0009 records every decision; all 14 specs amended; question files removed
- [analysis-2026-09] | completed | note: full comparative analysis written to `docs/analysis/2026-09-16-comparative-analysis.ru.md` and `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md`; `.ai/` knowledge base created for the repository itself
- [logic-audit-fixes-2026-07] | completed | note: 20 audit findings (4 blocker, 9 major, 7 minor) applied per `docs/audits/2026-07-21-logic-audit-fixes.md`; `validate-contracts.sh` extended; deployment matrix fixed

## Deferred
None.

## Known conditions (read before starting any task)
- On 2026-11-06 the owner requested deleting all remaining runtime branches. Only `main` remains locally and remotely after cleanup. Detached temporary worktrees preserve experimental commits and uncommitted runner/guard changes; these are not integrated source or active work. The older 2026-11-03 branch inventory is superseded. Any future reuse requires fresh inspection and validation.
- On 2026-10-28 the owner explicitly authorized committing all pending knowledge and roadmap edits and pushing main directly. This supersedes the earlier feature-run exclusions for this publication only. The personal checkout path is omitted from the new completed record; pinned source links and the owner's specification text are preserved. The exact source-URL ledger inventory is updated under this later authorization, with its checker unchanged.
- On 2026-10-28 the owner authorized fresh independent catalog review, autonomous repair and integration. PRs #31–#36 are merged; main 111455ac171c7356d083e00d4d307a7285ed2e35 exactly matches the clean independently validated tree (594/0/2). All17 unrelated later-specification edits are preserved. Optional example-oracle precision is a nonblocking future enhancement; the actual guide fixture preserves exact unrelated bytes.
- On 2026-10-26 the owner explicitly authorized final per-PR validation, autonomous repairs and integration of the hook-logging delivery. PRs #22–#29 were merged with verified trees and merge commits; no direct main push, force push, rebase, branch deletion or real-settings deployment was used.
- The initial commit contains private references. On 2026-10-19 the owner explicitly authorized publishing the reviewed stack with existing ancestry and approved scan exceptions retained; the earlier publication hold is superseded. History rewriting remains outside scope.
- `.ai/` in this repository is **committed in full**, including `tasks/todo/` — the
  repository-owned policy for this source checkout; consumer defaults remain local (ADR-0012).
- The owner permits local test-first and implementation commits. Current mutable content is scrubbed; private scan patterns remain in local configuration. The owner authorized merging PRs #2–#9 after validation; they were integrated in dependency order using merge commits. Existing ancestry remains unchanged; history rewriting is outside scope.
- The public name is **Orchestrail**. Local checkout references use `~/projects/orchestrail`;
  machine settings use `~/.config/orchestrail/`, with `ORCHESTRAIL_HOME` and
  `ORCHESTRAIL_LOG_ROOT` selecting shared checkouts and logs.
- All analysis, audit, and similar documents live under `docs/` (`principles/coding.md →
  Document placement`). The repository root holds only `CLAUDE.md`, scripts, and the
  source directories.
- Historical full-suite evidence includes 594/0/2 on 2026-10-26 and the runtime task's later recorded 717/0/2 tested parent; these are not current-tree certification or comparative performance acceptance. The complete knowledge base remains tracked.
- Earlier inventory recorded 10 runs, four carrying noncanonical values. The integrated helper can lint these without rewriting them; retrospective metrics exclude unusable observations. Existing historical logs were not read or changed by this review.
