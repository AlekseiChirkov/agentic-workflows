# ADR-0005: Decisions for Task unknown — Stacked branches with two commits per subtask; no pipeline identifiers or attribution in the repository

## Status

Accepted — Decision 1 amended by ADR-0009 for composite children (one branch and one PR per composite)

## Date

2026-08-26

## Related Task

- Task: none — design of the git layer
- Related files: `rules/git-flow.md`, `workflows/restack.md`, `rules/global-claude.md → ## Commit Messages`

## Summary

Each subtask gets its own branch cut from the previous subtask's tip, at least a `test:`
and a `feat:` commit, a draft PR promoted to ready after validation; `base_commit` is
recorded once so `/restack` can replay after any merge strategy. Nothing committed may
mention a subtask id, spec, task directory, ADR, `.ai/` path, workflow name, or AI
authorship.

## Context

A finished task landing as one giant diff is unreviewable. `.ai/` is untracked, so any
reference to it in the repository dangles. Harnesses append attribution trailers by
default.

## Decisions

### Decision 1: One stacked branch and PR per subtask

**What was decided:**
`<type>/<feature-slug>` in domain language; branch N from the reviewed tip of N-1; draft
PRs during the run; promotion in stack order after `/phase-validation`; the human merges.

**Why:**
Each PR is reviewable alone; the stack tip is the integration point; drafts protect the
run from the stack shifting underneath it.

**Alternatives:**
- One branch per task — rejected: the giant-diff problem.
- Independent branches from base — rejected: sequential execution gains nothing from it
  and loses linear review order.

**Consequences:**
PR N cannot merge before 1…N-1; squash/rebase merges require `/restack`, which is why
`base_commit` is written at creation and never recomputed.

**Related files:**
- `rules/git-flow.md → ## Branch model`, `## Recorded state`

### Decision 2: Two commits per subtask as TDD evidence

**What was decided:**
`test:` commit after RED, `feat:` after GREEN; a single commit only when the gate returned
`none`.

**Why:**
The separate RED commit is reviewable proof that tests came first.

**Alternatives:**
- One commit per subtask — rejected: no evidence.

**Consequences:**
Requires the Implementer's RED pause (ADR-0004).

### Decision 3: Pipeline identifiers and attribution stay out

**What was decided:**
Forbidden anywhere committed: `T-XX`, spec/task names, ADR numbers, `.ai/` paths,
workflow/role names, `Co-Authored-By` naming a tool, "Generated with", tool emoji, model
names. This overrides harness defaults.

**Why:**
Dangling references for readers without `.ai/`; commit messages describe the change only.

**Alternatives:**
- Allow `T-XX` in commit scopes for traceability — rejected: traceability lives in
  untracked `state.md`, cost accepted and stated.

**Consequences:**
The mapping commit → subtask exists only on the machine that ran the task.

**Related files:**
- `rules/git-flow.md → ## Pipeline identifiers stay out of the repository`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Any PR-body or commit-message generator (`suggest-*`) must be re-checked against Decision 3
when edited. If `.ai/` is ever committed in a consumer project, Decision 3's "dangling
reference" rationale weakens but the attribution rule stands.

## Verification

`rules/git-flow.md → ## Safety rails` table; `validate-contracts.sh` checks the
no-attribution wording exists in `global-claude.md` and `git-flow.md`.
