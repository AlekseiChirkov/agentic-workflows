spec_path: .ai/specs/completed/01-git-source-of-truth.md
flow: full

## Phases
- discovery: complete
- execution: complete
- validation: complete

## Task Analysis
→ archived to state-archive.md

### Assumptions
- `flow: full` — gate: 1 fail (more than three files), 2 fail (new version and state invariants), 3 fail (shipped script and workflow behavior changes), 4 pass (no schema migration). Source: specification and repository architecture.
- Keep `.ai/` tracked in full, including this task directory. Source: user clarification, ADR-0007, and ADR-0010.
- Start the new task stack from `fix/public-hygiene-guard`, because the task depends on the completed scrub and `main` does not contain it. Source: spec 01, `.ai/memory/state.md`, and task 00's execution plan.
- Preserve the existing Git history. Publish additive task branches and PRs under the explicit `--allow-pr` flag, but do not merge, update `main`, or rewrite history. Source: user invocation and ADR-0010 amendment.
- New task state created before `VERSION` exists may omit `contract_version`; readers must accept that legacy shape, while future task analyses stamp the current version. Source: specification.
- Preserve the current public GitHub slug and historical links; scan exceptions are limited to the active source specification, exact historical records, and that slug inside the live clone URL. Replace other mutable names and all old checkout paths. Source: user batch-gate answer.
- Defer the Apache-2.0 license until the owner supplies exact copyright-holder wording; do not add a placeholder. Source: user batch-gate answer.
- Deliver the versioned PR stack on the existing ancestry; defer the v0.9.0 tag until the stack is merged and the owner authorizes release. Source: user batch-gate answer.

### Owner Deferrals
- Apache-2.0 license | deferred | exact copyright-holder wording is pending from the owner; do not create a placeholder.
- v0.9.0 release tag | deferred | create only after the PR stack is merged and the owner authorizes release.

## Open Questions (batch)
None.

## Decomposition
- decomposition: complete
- subtasks: T-01, T-02, T-03, T-04

## Subtask Progress
T-01 | Versioned contract metadata | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — acceptance criteria met; PR #5 opened; optional staged-update coverage proposal returned.
  target_files: VERSION, workflows/pd-analyze.md, log-step.sh, rules/run-log.md, validate-contracts.sh
  blocker: none
  notes: "tdd: smoke — four frozen RED checks now pass; full validator 546/546; root Bash syntax passes; shellcheck unavailable. tdd: red digest — AC1 test_contract_version_root_has_exact_release_value; AC2 test_contract_version_analysis_stamps_state_and_accepts_legacy; AC3 test_contract_version_run_start_stamps_current_and_reads_legacy; AC4 test_contract_version_rule_history_warns_until_version_changes; AC5 full validator regression gate. RED result: 542 passed, 4 failed. pav-propose: Optional — cover staged VERSION updates in the stale-rule fixture; current coverage exercises only an unstaged update."
  branch: feat/contract-version-metadata
  base_branch: fix/public-hygiene-guard
  base_commit: 3ae483eb5efe5d45288da166728fb6902e615efb
  commits: cd58b7b, 4f7e70a, ba00806
  pr: #5 merged into main
T-02 | Portable runtime paths | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all acceptance criteria met; optional path-scan coverage proposal recorded; draft PR #6 opened.
  target_files: sync.sh, log-step.sh, setup-new-project.sh, setup-umbrella.sh, setup-all-repos.sh, link-skills.sh, validate-contracts.sh, rules/run-log.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-pipeline.md, workflows/phase-validation.md, workflows/spec-run.md, workflows/retro.md, workflows/pd-finalize.md, workflows/pe-finalize.md, .ai/context/environment.md, .ai/context/runbook.md
  blocker: none
  notes: "tdd: smoke — two RED checks, AC coverage 5/5. tdd: test amended — test_shell_paths_relocated_checkout_preserves_overrides — replace obsolete variable expectations with required public names; retain relocation, empty, relative, precedence, child, and link scenarios; add missing-source rejection. tdd: red digest — AC1,AC2,AC3,AC4 → test_shell_paths_relocated_checkout_preserves_overrides; AC5 → test_runtime_instructions_public_configuration_uses_orchestrail. tdd: green — full validator 547 passed, 0 failed; all root shell scripts pass bash -n; git diff --check passes; ShellCheck unavailable. pav-propose: Optional — expand the machine-specific path check beyond `/Documents/projects/` to catch other hard-coded checkout locations."
  branch: feat/portable-runtime-paths
  base_branch: feat/contract-version-metadata
  base_commit: ba008063a0d3cae0a0fe210690646666320fd9e1
  commits: 986c8f9, fc69d1a
  pr: #6 merged into main
T-03 | Public package materials | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all acceptance criteria met; optional README destination proposal recorded; draft PR #7 opened.
  target_files: README.md, .gitignore, logs/.gitignore, docs/USAGE.md, validate-contracts.sh
  blocker: none
  notes: "Assigned model `gemini-3.8-flash` is unavailable in this agent runtime; the session default was used. tdd: smoke — three checks, AC coverage 5/5. tdd: test amended — test_public_package_overview_and_release_policy — accept equivalent README wording across line breaks and isolate ignore checks from global excludes. tdd: red digest — AC1, AC2 → test_public_package_overview_and_release_policy; AC3 → test_public_ignore_rules_keep_local_data_ignored_and_knowledge_trackable; AC4 → test_public_setup_guide_uses_orchestrail_release_instructions; AC5 → full validator regression gate; tag inventory unchanged (empty). tdd: green — full validator 550 passed, 0 failed; all root Bash syntax checks pass; git diff --check passes; README 26 lines; LICENSE absent; tag refs unchanged (empty). ShellCheck unavailable. pav-propose: Optional — mention that sync also writes to Windsurf global directories and updates eligible project-local files."
  branch: feat/public-package-materials
  base_branch: feat/portable-runtime-paths
  base_commit: fc69d1ac3718a106d3e8e96f6a11309fbb14a018
  commits: 6e4119d, 3cdf9bc
  pr: #7 merged into main

## Improvement Proposals (T-03)

### Do Now
None

### Do Later
None

### Optional
- Mention that `sync.sh` also writes to Windsurf global directories and updates eligible project-local files.
T-04 | Public identity sweep | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — independent validation passed all acceptance criteria; no important findings or useful proposals.
  target_files: CLAUDE.md, README.md, docs/README.md, docs/USAGE.md, link-skills.sh, setup-all-repos.sh, setup-new-project.sh, setup-umbrella.sh, sync.sh, validate-contracts.sh, templates/.ai/principles/architecture.md, templates/codex-global-AGENTS.md, workflows/pv-create-fixes.md, .ai/README.md, .ai/adr/index.md, .ai/context/runbook.md, .ai/memory/architecture.md, .ai/memory/state.md, .ai/principles/architecture.md, .ai/specs/README.md, .ai/specs/13-model-only-harnesses-and-rule-naming.md
  blocker: none
  notes: Assigned model `gemini-3.8-flash` is unavailable in this agent runtime; the session default was used. tdd: smoke — one exact identity-ledger check, AC coverage 4/4. tdd: red digest — AC1,AC2,AC4 → test_public_identity_matches_exact_ledger_and_preserves_knowledge; AC3 → identity check and test_public_hygiene_tracked_tree_excludes_private_tokens. tdd: green — full validator 551/551; hygiene-only pass; all root scripts pass bash -n; git diff --check passes; ShellCheck unavailable. Final scan scope: all 163 tracked and non-ignored untracked worktree files, with no directory exclusions; only the 14 self-referential ledger data rows are masked while all other state content is scanned. The exact ledger records 22 `(path, line, token, count)` tuples across 21 line locations, 26 total occurrences in 10 files. The only current-content match is the single public-slug token in `docs/USAGE.md:245`; all other retained matches are source or historical lines listed below. pav-check NEEDS WORK: AC1 — `.ai/principles/coding.md` still names obsolete root variables; AC3 test gap — the knowledge inventory reads current HEAD instead of the pre-branch base, so it cannot detect a file removed in this branch. Review confirms the current base and HEAD both contain the same 45 knowledge paths. Independent revalidation 2026-10-20: pav-check NEEDS WORK. AC1 remains unmet (important): docs/USAGE.md:637 says --from takes precedence over $WORKFLOWS_SOURCE, but sync.sh reads ORCHESTRAIL_HOME; setting the documented variable has no effect. TDD audit (important): test changes were committed after RED in 1314aa2, but the required amendment record was absent. Checks: full validator 551/551; hygiene-only, shell syntax, and git diff --check passed; all 45 base .ai paths are present and tracked in HEAD; ShellCheck unavailable. tdd: test amended — 1314aa2: compare the knowledge inventory against the recorded base commit and require every baseline file to remain present and tracked. tdd: test amended — test_runtime_instructions_public_configuration_uses_orchestrail: include docs/USAGE.md so published setup examples must use the public source-root variable and reject its obsolete name.
  amendment: tdd test changes were recorded before the separate test commits; both independent validation findings have been corrected and the full validator is GREEN at 551/551.
  branch: feat/public-identity-sweep
  base_branch: feat/public-package-materials
  base_commit: 3cdf9bc93dbde32ee57223df4a0c14b092d0b976
  commits: daf5fbf, 412206d, 8deba46, 1314aa2, e9221a5, f922b9e, 5d7713f, 42d960d, 0c7e46f
  pr: #8 merged into main
T-05-fix-validation-metadata | Synchronize validation metadata | atomic-tests: n-a | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all acceptance criteria passed; draft PR #9 opened; no useful improvements proposed.
  target_files: docs/USAGE.md, .ai/memory/architecture.md, .ai/tasks/completed/task-01-git-source-of-truth/state.md
  blocker: none
  notes: tdd: none — unit, integration, and contract tests do not apply because no executable behavior or public interface changes; smoke checks do not observe the documentation count or recorded commit list. The full validator remains the regression check.
  branch: fix/validation-metadata
  base_branch: feat/public-identity-sweep
  base_commit: 0c7e46f1965e317429cd2b730578e61a95b27000
  commits: 260185e, d1e3125, 364b83e, de3d5c7
  pr: #9 merged into main

## Execution Report
- T-01: reviewed — version metadata, legacy record compatibility, and stale-rule warning implemented and atomically validated.
- T-02: reviewed — portable runtime roots, override precedence, and setup propagation implemented and atomically validated.
- T-03: reviewed — public package materials, ignore policy, and release setup guidance implemented and atomically validated; license and release tag deferred by owner decision.
- T-04: reviewed — public identity sweep and exact knowledge inventory guard implemented; both independent validation findings corrected and the full validator passes.

## Solution Design

### Variants
→ archived to state-archive.md

### Decision
Use the sequential feature stack. It keeps each independently verifiable outcome reviewable and follows the existing task 00 stack, which already has a ready pull request and contains the required scrub. The version contract comes first because subsequent task and run records depend on it.

### Autonomous Decision
| Variant | Simplicity | Reversibility | Codebase fit | Testability | Blast radius | Total |
|---|---:|---:|---:|---:|---:|---:|
| Single broad release branch | 4 | 2 | 1 | 2 | 2 | 11 |
| Sequential feature stack | 4 | 4 | 5 | 5 | 4 | 22 |
| Separate versioning task | 3 | 3 | 3 | 3 | 3 | 15 |

**Winner:** Sequential feature stack — it matches the repository's reviewed predecessor stack and gives each contract a focused smoke test.
**Anti-overengineering check:** passed; this uses the existing branch and validation model without adding a new workflow abstraction.
**Evidence:** `.ai/principles/architecture.md` P1, P4, and P7; ADR-0005; `.ai/tasks/todo/task-00-sensitive-data-scrub/plan.md`; the active stack and ready PRs recorded in `.ai/memory/state.md`.

### Scope

#### In
- Add contract version metadata and the stale-rule warning.
- Update runtime roots, environment variables, and setup instructions for Orchestrail.
- Create the concise public README, update ignore rules, and describe the planned setup tag; defer the license and release tag as recorded below.
- Sweep remaining mutable repository content for the new identity using the batch-gate decision for source and historical records.
- After task validation and PR promotion, rename the local checkout and verify that Git and scripts still resolve there.

#### Out
- Rewriting existing Git history, merging PRs, updating `main`, or deploying to a harness.
- Deleting any tracked `.ai/` knowledge or `docs/` content.
- Changing the configuration contract of consumer repositories beyond the variables and paths named by the specification.
- Renaming the public GitHub repository; preserve its current public slug.
- Creating a release tag before the PR stack is merged and the owner authorizes release.

### Rejected
→ archived to state-archive.md

### Off-limits
- Do not rewrite or delete existing commits, merge pull requests, update `main`, force-push, or delete branches.
- Do not remove `.ai/` or `docs/` from the repository, or ignore either directory.
- Do not copy private absolute paths or denylisted personal identifiers into tracked files.
- Do not broaden source/history scan exceptions beyond the user's batch-gate decision.
- Do not promote draft PRs until task-level validation passes.

### Invariants
- The Git repository and its existing ancestry remain intact.
- The full `.ai/` knowledge base and `docs/` remain tracked.
- Script defaults resolve from the checkout; supported overrides keep the specified precedence.
- State and run-log readers accept legacy records without `contract_version`.
- The public-hygiene guard and complete contract validator pass before publishing task branches.
- New task branches include the scrubbed predecessor and stack in dependency order.

### Acceptance Criteria
- [ ] The checkout is named orchestrail/, and git rev-parse --git-dir succeeds there; no absolute checkout path is written into tracked content.
- [ ] The former project name is absent from mutable source and documentation scopes, except exact approved scan locations recorded below.
- [ ] sync.sh, log-step.sh, and configuration examples use the specified Orchestrail roots and environment-variable names.
- [ ] .gitignore excludes the requested local logs and machine settings while leaving .ai/ and docs/ trackable.
- [ ] The complete contract validator and the scrub check pass before any task branch is pushed.
- [ ] VERSION contains 0.9.0; new task state and run-start events record contract_version; readers accept its absence in older records.
- [ ] The validator warns when rules have later Git history than an unchanged VERSION.
- [ ] README.md is at most 60 lines and contains all required statements and links. LICENSE creation is deferred until the owner supplies exact holder wording; no placeholder license is created.
- [ ] Existing history is preserved and the task delivers an additive PR stack. The v0.9.0 tag is deferred until the stack is merged and the owner authorizes release; this run does not create or move tags.
- [ ] docs/USAGE.md section 4 says to clone and identifies v0.9.0 as the tag to use after release.

## Deferred
(none)

## Approved Identity Scan Exceptions
- .ai/specs/02-run-log-vocabulary-validation.md:9 — preserve only the unchanged issue link in the current active source specification, within the existing owner-approved source category.
- .ai/specs/completed/01-git-source-of-truth.md:22 — preserve only the active source criterion.
- .ai/adr/0007-task-unknown-commit-ai-directory-in-this-repository.md:18 — preserve the historical repository-tracking decision.
- .ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:69 — preserve the historical naming decision.
- .ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md:105,107 — preserve only the publication authorization and historical pull-request links.
- .ai/memory/progress.md:4 — preserve the append-only history heading.
- .ai/tasks/completed/task-00-sensitive-data-scrub/state.md:357,359 — preserve only the completed task's publication authorization and merge-order links.
- docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md:1,40 — preserve the historical comparison record.
- docs/analysis/2026-09-16-comparative-analysis.ru.md:1,14,117,225,263,429,444 — preserve the historical analysis record.
- docs/audits/2026-07-21-logic-audit-fixes.md:1,8,568 — preserve the historical audit record.
- docs/USAGE.md:251 — permit one public-slug token only inside the live clone URL; the clone destination and every other checkout reference use `~/projects/orchestrail`.

### Exact Identity Match Ledger

The final scan compares each `(path, line, token, count)` against this ledger. Each count is per token on that line; any extra token on an approved line fails. T-04 refreshes line numbers after edits and records the resulting scan scope and counts.

| Path | Line | Expected token counts |
|---|---:|---|
| `.ai/specs/02-run-log-vocabulary-validation.md` | 9 | `agentic-workflows` × 1 |
| `.ai/specs/completed/01-git-source-of-truth.md` | 22 | `agentic_workflows` × 1; `agentic-workflows` × 1 |
| `.ai/adr/0007-task-unknown-commit-ai-directory-in-this-repository.md` | 18 | `agentic_workflows` × 1 |
| `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md` | 69 | `agentic_workflows` × 1 |
| `.ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md` | 105 | `agentic-workflows` × 1 |
| `.ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md` | 107 | `agentic-workflows` × 3 |
| `.ai/memory/progress.md` | 4 | `agentic_workflows` × 1 |
| `.ai/tasks/completed/task-00-sensitive-data-scrub/state.md` | 357 | `agentic-workflows` × 1 |
| `.ai/tasks/completed/task-00-sensitive-data-scrub/state.md` | 359 | `agentic-workflows` × 3 |
| `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md` | 1 | `agentic_workflows` × 1 |
| `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md` | 40 | `agentic_workflows` × 1 |
| `docs/analysis/2026-09-16-comparative-analysis.ru.md` | 1, 14, 117, 225, 263, 444 | `agentic_workflows` × 1 per line |
| `docs/analysis/2026-09-16-comparative-analysis.ru.md` | 429 | `AGENTIC_WORKFLOWS` × 1 |
| `docs/audits/2026-07-21-logic-audit-fixes.md` | 1, 8, 568 | `agentic_workflows` × 1 per line |
| `docs/USAGE.md` | 251 | `agentic-workflows` × 1 |

### Root File Decisions
- `.ai/memory/architecture.md`: updated during Discovery for repository identity, configuration roots, and version metadata; the validator count was synchronized during validation.
- `.ai/principles/architecture.md`: updated during the identity sweep; no further update was needed because architectural principles did not change.
- `.ai/project_state.md`: skip because the file is absent.
- `.ai/memory/state.md`: updated at phase transitions; the completed task is now recorded under Done.

### ADR Decision
`adr: existing decisions verified — the accepted identity, versioning, and publication records cover the choices made; validation introduced no new architectural decision.`

## Improvement Proposals (T-01)

### Do Now
None

### Do Later
None

### Optional
- Extend the stale-rule warning fixture to test a staged `VERSION` update; current coverage exercises only an unstaged update.

## Improvement Proposals (T-02)

### Do Now
None

### Do Later
None

### Optional
- Expand the machine-specific path check beyond `/Documents/projects/` to catch other hard-coded checkout locations.

## Contract Check

### Invariants
| Invariant | Status |
|-----------|--------|
| Git history and existing ancestry remain intact | PASS — the current branch descends from the recorded stack base with additive commits; no rewrite, merge, or main update is present. |
| The complete `.ai/` knowledge base and `docs/` remain tracked | PASS — all 45 baseline `.ai/` paths remain present and tracked; the current tree tracks 52 `.ai/` paths and 8 documentation paths. |
| Script defaults resolve from the checkout and supported overrides retain their precedence | PASS — shell path and configuration smoke checks pass, including relative roots, empty overrides, missing sources, and `sync.sh --from` precedence. |
| State and run-log readers accept legacy records without `contract_version` | PASS — compatibility checks pass for both task state and run-start records. |
| Public hygiene and the complete contract validator pass before publication | PASS — the full validator reports 551 passed and 0 failed; the hygiene-only check passes, and the published task branches were pushed after their green gates. |
| The task branches preserve the scrubbed predecessor and dependency order | PASS — the recorded base commits and additive history form the required T-01 → T-02 → T-03 → T-04 stack. |

### Acceptance Criteria
| Criterion | Status |
|-----------|--------|
| Checkout name, Git metadata, and tracked-path privacy | PASS — the checkout is named `orchestrail`; `git rev-parse --git-dir` succeeds after the move, and the hygiene validator finds no absolute checkout path in tracked content. |
| Former project name absent from mutable scopes except exact approved scan locations | PASS — the full identity-ledger and tracked-tree checks pass with no unexpected matches. |
| Runtime scripts and configuration examples use the public roots and variables | PASS — contract checks cover `ORCHESTRAIL_HOME`, `ORCHESTRAIL_LOG_ROOT`, documented paths, and `--from` precedence. |
| Ignore rules exclude local logs and machine settings while keeping `.ai/` and `docs/` trackable | PASS — ignore-policy checks pass; both trees are tracked. |
| Full validator and scrub check pass before task branches are pushed | PASS — each task branch passed its green validation gate before push; the final full validator and hygiene-only check also pass. |
| Version metadata, state stamping, legacy readers, and stale-rule warning | PASS — `VERSION` is `0.9.0`; version metadata and legacy compatibility checks pass, and the validator emits the expected stale-version warning. |
| README length and required package content; license deferral recorded without a placeholder | PASS — package-material checks pass; README is 26 lines, no placeholder license exists, and the owner's deferral is recorded. |
| Additive PR stack preserves history; release tag remains deferred and unchanged | PASS — the stack is additive, no `v0.9.0` tag exists, and no tag was created or moved. |
| `docs/USAGE.md` section 4 instructs cloning and names the post-release tag | PASS — the section documents the clone command and `v0.9.0` checkout after release. |

### Off-limits
| Constraint | Status |
|------------|--------|
| Do not rewrite or delete commits, merge PRs, update `main`, force-push, or delete branches | PASS — current history is additive on the task branch; no prohibited Git operation occurred. |
| Do not remove or ignore `.ai/` or `docs/` | PASS — both directories remain tracked and are not ignored. |
| Do not copy private absolute paths or denylisted identifiers into tracked files | PASS — the tracked-tree hygiene validator passes. |
| Do not broaden source/history scan exceptions | PASS — the exact approved identity ledger remains enforced and passes. |
| Do not promote draft PRs before task-level validation passes | PASS — draft PRs were withheld until task-level validation passed; all remain unmerged. |

## Code Review

### Findings
1. `docs/USAGE.md:636` and `.ai/memory/architecture.md:22,78` still state that the validator has 542 checks, while the current suite reports 551. The coding standard requires quoted check counts to be updated with the change. Severity: important.
2. The T-04 `commits:` audit trail ends at `5d7713f`, but the recorded branch head is `0c7e46f` and includes the later state commits `42d960d` and `0c7e46f`. Spec-run resume reconciliation compares the branch tip with the final recorded SHA, so this task cannot safely resume from its current state. Severity: important.

### Summary
2 findings: 0 critical, 2 important, 0 optional. Test coverage and TDD amendment records were reviewed; no test-set weakening or unsupported test exemption was found.

## Issue List

### Approved
1. Synchronize the published validator check counts. Update the usage guide and current architecture snapshot from 542 to the verified count so repository documentation matches the 551-check validator.
2. Repair the T-04 commit audit trail. Record the missing state commits so the final SHA matches the `feat/public-identity-sweep` branch tip and spec-run can resume safely.

### Deferred
(none)

## Fix-Tasks

### Fix Classification

| Issue | Severity | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Grouping | Branch |
|-------|----------|--------|--------|--------|--------|----------|--------|
| #1 Synchronize validator check counts | important | pass | pass | pass | pass | shared | T-05-fix-validation-metadata |
| #2 Repair T-04 commit audit trail | important | pass | pass | pass | pass | shared | T-05-fix-validation-metadata |

fixes-created: complete
fixes-count: 1
Created: T-05-fix-validation-metadata

## Spec Sync
sync: complete
synced_at: 2026-10-20
deltas: 5 (implemented-differently: 3, not-implemented: 2, implemented-beyond: 0)
spec: .ai/specs/completed/01-git-source-of-truth.md
