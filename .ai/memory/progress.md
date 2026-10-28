# progress.md — chronological log of completed work

## Purpose
Append-only log of completed tasks and notable events for agentic_workflows itself,
newest first. Entries before 2026-09-16 are reconstructed from file contents, run logs,
and the audit spec — dates are those recorded in the sources.

## Log
- **2026-10-26 — Hook logging final review and integration complete.** Seven independent original PR reviews and a separate producer repair review are complete. Three important defects and one advisory regression were fixed with separate regression commits; fresh complete validation passes 594 checks with zero failures and two optional skips. PRs #22–#29 were merged in dependency order with pinned heads and verified complete trees; product delivery is integrated at 8184bfe87a4c696e5c100032ebdf0f5fd8af64ee. History and original branch points are preserved; real settings and historical telemetry remain untouched.

- **2026-10-26 — Hook logging review stack published.** PRs #22–#28 are ready for review in dependency order. All source, specification, accepted decisions and validation evidence are committed; no merge or default-branch update was performed. Integration remains an owner action.

- **2026-10-26 — Hook logging specification reconciled.** All five requirements and ten source acceptance criteria remain fulfilled; zero implemented-differently, not-implemented or implemented-beyond deltas. Completion metadata is recorded without changing requirement intent.

- **2026-10-26 — Hook logging implementation validated.** Explicit identities/receipts, native correlation, owned user settings recovery, coverage-aware fallback and exact offline timing are complete. Six leaves and the tracking-policy prerequisite are independently reviewed; one important shell standards finding was repaired. Final full gate: 591 passed, 0 failed, 2 optional hygiene skips; contract mapping: 32 passes. Existing decision record accepted in place. PRs #22–#28 are published; review promotion follows. No automatic merge or real-home deployment.

- **2026-10-21 — Run-log validation completed.** Producer validation, exact legacy normalization, read-only lint, usable retrospective metrics, structured drift checks and isolated acceptance are reviewed. Four integrated findings were repaired in three fix leaves. Verification: 25 focused checks; full suite 576 passed, 0 failed, 2 configured hygiene skips. Specification reconciled with zero requirement deltas; ADR-0011 accepted. PRs #13–#20 remain stacked for owner review and integration.

- **2026-10-20 — Local hygiene configuration and merge authorization.** The tracked pattern file remains deleted; exact scans now read maintainer-local patterns, and the full suite reports two explicit skips when they are unavailable. Validation: 551 checks passed with local patterns; 549 passed and 2 skipped without them. The owner authorized merging the reviewed changes while preserving existing history.

- **2026-10-20 — Source-of-truth release stack.** Versioned contracts, portable runtime
  paths, public package materials, identity checks, and validation metadata are complete.
  The reviewed stack is published without rewriting existing history; license wording and
  the release tag remain owner-deferred. The reconciled spec records three implemented-
  differently and two not-implemented deltas; the full validator passes 551 checks.

- **2026-10-19 — Public-hygiene delivery completed.** The owner authorized merging PRs #2, #3, and #4 in dependency order. Review corrections preserve source overrides in suggested child setup commands and make readability fixtures deterministic for root. Validation passes 542 checks as the normal user and UID 0. Task records moved to `tasks/completed/task-00-sensitive-data-scrub/`; the source specification moved to `specs/completed/00-sensitive-data-scrub.md`. Its exact scanner exception moved with it; the former path is scanned. Existing history is retained. Optional fixture isolation remains a separate followup.

- **2026-10-19 — Public hygiene and local-only delivery.** Three reviewed local branches remove private references and add an indexed literal-token guard. All 44 baseline knowledge files are preserved; all 45 current files are included. Validation: 542 checks pass, 23 contract requirements pass, manual sweep 152 files with zero matches/errors. Five source differences reconciled (four implemented differently, one additional inclusion requirement); ADR-0010 accepted. Existing history remains unchanged and remote publication is withheld. One optional fixture-isolation improvement is deferred.

- **2026-09-17 — Scrub moved ahead of everything.** The owner required sensitive data to
  be removed before any work starts. `specs/completed/00-sensitive-data-scrub.md` added as the first
  task: client and employer project names, internal source-file references from client
  code, PR and workflow-run identifiers, host name, and `$HOME` paths, plus a
  forbidden-token check group in `validate-contracts.sh` and a `scrub-denylist.txt`.
  ADR-0009 Decision 1 amended; spec 01 now depends on 00; spec 11's scrubbing criterion
  reduced to re-verification.
- **2026-09-17 — Roadmap decisions.** Three rounds of owner questions over specs 01–13
  (76 + 28 + 12) answered in full. ADR-0009 records the decisions: public name
  Orchestrail with SemVer from `0.9.0`; Windsurf/Devin dropped in favour of a
  `harness/<name>/` abstraction with declared capabilities; full `<kind>-<subject>` rule
  naming and command renames inside spec 13, audit split out as 13a; composites get one
  branch + one PR with parallelism only among their children; telemetry instead of
  budgets; state tool deferred to backlog; profiles replace the Python-centric core;
  execution order fixed. Specs 01–13 amended (05 and 12 renamed, 13a added, 07 marked
  backlog); ADR-0008 accepted; ADR-0004/0005 annotated; question files deleted.

- **2026-09-16 — Repository layout for open source.** Owner decisions: `.ai/` is committed
  in full (ADR-0007 accepted); all documents about the system moved from the root into
  `docs/` (`USAGE.md`, `SPEC-RUN-QUICKSTART.md`, `audits/`, `analysis/`); the document
  placement rule added to `principles/coding.md`, `.ai/README.md`, and `CLAUDE.md`;
  `validate-contracts.sh` retargeted to `docs/USAGE.md`. The former root `specs/`
  directory (one audit fix spec) is gone — it lives in `docs/audits/`.
- **2026-09-16 — Comparative analysis and knowledge base.** Full analysis of the system
  against BMAD, Spec Kit, Kiro, OpenSpec, Superpowers, Agent OS, Conductor and native
  Claude Code features (`docs/analysis/2026-09-16-comparative-analysis.ru.md`, `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md`). Findings from the run log:
  spec-run wall-clock 21–26 h, one subtask 15 h, `pd-select-model` 3 h, one implementer
  killed by spend limit, one run logged retroactively (12 steps at 0 s), vocabulary
  violations in 4 of 10 logs. Created `.ai/` for the repository, 8 ADRs reconstructing the
  decisions embedded in the rules, and 11 improvement specs (`specs/README.md`).
- **2026-09-09 — bugfix runs 8a1ffd0d, 0ac36f8f (a consumer repository).** Quick-tier defect path
  used for a CI image-tag race and a documentation consistency fix; 10 and 9.5 min; the
  `--no-repro` path exercised for documentation-only work.
- **2026-09-01 … 09-02 — bugfix runs bd24a6df, a16e6622, 7d3ca8fa, 3da5d689 (consumer repositories).** First production use of `/bugfix`: smoke-level RED tests
  against CI workflows and Terraform; 3–21 min each; `resolve` is consistently the slowest
  step.
- **2026-08-31 — spec-run 4029e93a → 4305eda1 (a consumer repository).** Batch gate stopped the
  first run: a user instruction (`same-branch`) conflicted with three gated rollout phases.
  The second run resumed with an adoption-only scope, delivered a pull request, deferred two
  subtasks behind live evidence gates. All step lines were written at run-end with
  duration 0 — evidence that prompt-driven logging is not real-time.
- **2026-08-31 — spec-run 41b4496e (a consumer repository).** 10 subtasks, 21.7 h. T-01 went
  blocked → NEEDS WORK → PASS; T-02's implementer was terminated by a spend limit and the
  scratch implementation reverted; T-10 took 10 h. Non-vocabulary outcomes (`implemented`,
  `restarted`, `needs-work`) appear in the log.
- **2026-08-27 — spec-run b905a8a5 (a consumer repository).** First full orchestrated run:
  9 subtasks, all PASS, PRs promoted, `--allow-pr`. 26 h wall-clock; `pd-select-model`
  alone 3 h; T-06 15.4 h. Model selection ran between two batch-gate lines.
- **2026-08-26 — Audit prompt and orchestration hardening.** `docs/audits/AUDIT-PROMPT.md` written for
  an independent audit of `/spec-run`; `orchestration.md`, `git-flow.md`, `run-log.md`,
  `spec-run.md`, `restack.md`, `retro.md`, `log-step.sh`, `validate-task.sh` in their
  current form; `sync.sh` gained `--from`.
- **2026-08 (undated) — Orchestrated mode.** `/spec-run` with Arbiter/Implementer/Validator
  roles, class A/B escalation, Discovery batch gate, stacked branches, two-commit TDD
  evidence, `/restack`, run log and `/retro`; `pd-select-model` bulk mode writes the
  `Model` column.
- **2026-07-22 — Incident: out-of-pipeline macro fix.** Four behaviour changes to a
  shipped forex/macro pipeline were made ad hoc with no contract, no `pv-contract`, no ADR.
  Together with the earlier subscription repair case (23 `fix-NN` directories for
  single-file changes) this motivated the quick tier (`rules/quick-flow.md`) and later
  `/bugfix`.
- **2026-07-21 — Independent logic audit.** 20 findings (4 blocker, 9 major, 7 minor):
  `/pd-archive` unreachable, composite progress blocks never created, phase rule files not
  deployed to Claude Code/Codex, composite validation triggered twice, execution ↔
  validation deadlock, inconsistent `--batch`, corrupt ADR index schema, and more. All
  re-verified and fixed per `docs/audits/2026-07-21-logic-audit-fixes.md`; three new check groups added to
  `validate-contracts.sh`.
- **Before 2026-07 — Foundation.** Three-phase pipeline with per-T-XX atomic cycles,
  state on disk, Guard sections, multi-repo umbrella `.ai/`, deployment to Windsurf +
  Claude Code + Codex via `sync.sh`, Python/FastAPI/GCP principles, TDD contract with
  `pinned` characterization mode.

- **2026-10-28 — Workflow clarity and instruction-size maintenance.** Reviewed all 42 workflow files, corrected scope/resume/ownership/test/finalization contradictions, and completed a separate reduction pass: 58,093 to 40,425 words (30.4% fewer). Reconciled eighteen active/backlog specs and the index while preserving four completed records and prior telemetry changes. Offline workflow/reference checks and five hook-workflow fixtures pass; full acceptance: 589 passed, one pre-existing unstaged archive condition, two optional hygiene skips. The unchanged strict archive scan passed with only the eleven byte-identical archive moves staged in a disposable index; the real index hash stayed unchanged. Details: `docs/audits/2026-10-28-workflow-clarity-and-size.md`; decisions recorded in the index. No deployed or model-usage savings are claimed.
