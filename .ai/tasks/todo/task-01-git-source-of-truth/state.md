spec_path: .ai/specs/01-git-source-of-truth.md
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

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
  pr: #5
T-02 | Portable runtime paths | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all acceptance criteria met; optional path-scan coverage proposal recorded; draft PR #6 opened.
  target_files: sync.sh, log-step.sh, setup-new-project.sh, setup-umbrella.sh, setup-all-repos.sh, link-skills.sh, validate-contracts.sh, rules/run-log.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-pipeline.md, workflows/phase-validation.md, workflows/spec-run.md, workflows/retro.md, workflows/pd-finalize.md, workflows/pe-finalize.md, .ai/context/environment.md, .ai/context/runbook.md
  blocker: none
  notes: "tdd: smoke — two RED checks, AC coverage 5/5. tdd: test amended — test_shell_paths_relocated_checkout_preserves_overrides — replace obsolete variable expectations with required public names; retain relocation, empty, relative, precedence, child, and link scenarios; add missing-source rejection. tdd: red digest — AC1,AC2,AC3,AC4 → test_shell_paths_relocated_checkout_preserves_overrides; AC5 → test_runtime_instructions_public_configuration_uses_orchestrail. tdd: green — full validator 547 passed, 0 failed; all root shell scripts pass bash -n; git diff --check passes; ShellCheck unavailable. pav-propose: Optional — expand the machine-specific path check beyond `/Documents/projects/` to catch other hard-coded checkout locations."
  branch: feat/portable-runtime-paths
  base_branch: feat/contract-version-metadata
  base_commit: ba008063a0d3cae0a0fe210690646666320fd9e1
  commits: 986c8f9, fc69d1a
  pr: #6 draft
T-03 | Public package materials | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  last_action: pav-close DONE — all acceptance criteria met; optional README destination proposal recorded; draft PR #7 opened.
  target_files: README.md, .gitignore, logs/.gitignore, docs/USAGE.md, validate-contracts.sh
  blocker: none
  notes: "Assigned model `gemini-3.8-flash` is unavailable in this agent runtime; the session default was used. tdd: smoke — three checks, AC coverage 5/5. tdd: test amended — test_public_package_overview_and_release_policy — accept equivalent README wording across line breaks and isolate ignore checks from global excludes. tdd: red digest — AC1, AC2 → test_public_package_overview_and_release_policy; AC3 → test_public_ignore_rules_keep_local_data_ignored_and_knowledge_trackable; AC4 → test_public_setup_guide_uses_orchestrail_release_instructions; AC5 → full validator regression gate; tag inventory unchanged (empty). tdd: green — full validator 550 passed, 0 failed; all root Bash syntax checks pass; git diff --check passes; README 26 lines; LICENSE absent; tag refs unchanged (empty). ShellCheck unavailable. pav-propose: Optional — mention that sync also writes to Windsurf global directories and updates eligible project-local files."
  branch: feat/public-package-materials
  base_branch: feat/portable-runtime-paths
  base_commit: fc69d1ac3718a106d3e8e96f6a11309fbb14a018
  commits: 6e4119d, 3cdf9bc
  pr: #7 draft

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
  commits: daf5fbf, 412206d, 8deba46, 1314aa2, e9221a5, f922b9e, 5d7713f
  pr: #8 draft
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
- Apache-2.0 license | deferred | exact copyright-holder wording is pending from the owner; do not create a placeholder.
- v0.9.0 release tag | deferred | create only after the PR stack is merged and the owner authorizes release.

## Approved Identity Scan Exceptions
- .ai/specs/01-git-source-of-truth.md:17 — preserve only the active source criterion.
- .ai/adr/0007-task-unknown-commit-ai-directory-in-this-repository.md:18 — preserve the historical repository-tracking decision.
- .ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:69 — preserve the historical naming decision.
- .ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md:105,107 — preserve only the publication authorization and historical pull-request links.
- .ai/memory/progress.md:4 — preserve the append-only history heading.
- .ai/tasks/todo/task-00-sensitive-data-scrub/state.md:355,357 — preserve only the completed task's publication authorization and merge-order links.
- docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md:1,40 — preserve the historical comparison record.
- docs/analysis/2026-09-16-comparative-analysis.ru.md:1,14,117,225,263,429,444 — preserve the historical analysis record.
- docs/audits/2026-07-21-logic-audit-fixes.md:1,8,568 — preserve the historical audit record.
- docs/USAGE.md:245 — permit one public-slug token only inside the live clone URL; the clone destination and every other checkout reference use `~/projects/orchestrail`.

### Exact Identity Match Ledger

The final scan compares each `(path, line, token, count)` against this ledger. Each count is per token on that line; any extra token on an approved line fails. T-04 refreshes line numbers after edits and records the resulting scan scope and counts.

| Path | Line | Expected token counts |
|---|---:|---|
| `.ai/specs/01-git-source-of-truth.md` | 17 | `agentic_workflows` × 1; `agentic-workflows` × 1 |
| `.ai/adr/0007-task-unknown-commit-ai-directory-in-this-repository.md` | 18 | `agentic_workflows` × 1 |
| `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md` | 69 | `agentic_workflows` × 1 |
| `.ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md` | 105 | `agentic-workflows` × 1 |
| `.ai/adr/0010-task-unknown-public-hygiene-and-local-publication.md` | 107 | `agentic-workflows` × 3 |
| `.ai/memory/progress.md` | 4 | `agentic_workflows` × 1 |
| `.ai/tasks/todo/task-00-sensitive-data-scrub/state.md` | 355 | `agentic-workflows` × 1 |
| `.ai/tasks/todo/task-00-sensitive-data-scrub/state.md` | 357 | `agentic-workflows` × 3 |
| `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md` | 1 | `agentic_workflows` × 1 |
| `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md` | 40 | `agentic_workflows` × 1 |
| `docs/analysis/2026-09-16-comparative-analysis.ru.md` | 1, 14, 117, 225, 263, 444 | `agentic_workflows` × 1 per line |
| `docs/analysis/2026-09-16-comparative-analysis.ru.md` | 429 | `AGENTIC_WORKFLOWS` × 1 |
| `docs/audits/2026-07-21-logic-audit-fixes.md` | 1, 8, 568 | `agentic_workflows` × 1 per line |
| `docs/USAGE.md` | 245 | `agentic-workflows` × 1 |

### Root File Decisions
- `.ai/memory/architecture.md`: update during Discovery finalization because repository identity, configuration roots, and version metadata are part of the current system snapshot.
- `.ai/principles/architecture.md`: update during T-04 to use the new product identity; do not change the existing architectural principles.
- `.ai/project_state.md`: skip because the file is absent.
- `.ai/memory/state.md`: update during Discovery finalization with the active task entry.

### ADR Decision
`adr: not triggered — the identity and versioning decisions are in ADR-0009; the owner resolved license and release boundaries at the batch gate without a new architectural decision.`

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
