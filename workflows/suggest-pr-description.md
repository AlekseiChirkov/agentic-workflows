---
description: Suggest a PR description for the current changes — output is ready to copy
---

Invocation: `/suggest-pr-description [--staged | --branch <base>]`
Called by: `/suggest-commit-pr`.

This workflow suggests text; it creates no pull request and performs no git writes.

## Guard

Validate the selected context and flags using
`suggest-commit-message → ## Step 0 — Gather Diff Context`; an unavailable or empty
selection stops the workflow. No existing file is overwritten.

## Step 0 — Gather Diff Context

Execute only `suggest-commit-message → ## Step 0 — Gather Diff Context`, or reuse the
same selected context supplied by `/suggest-commit-pr`. This defines flag validation,
session/staged/branch selection, empty-selection handling, and targeted reads. Do not
invoke the commit-message workflow merely to collect context.

## Step 2 — Analyse Changes

Identify the problem, resulting behavior, mechanism where non-obvious, breaking changes,
and evidence of verification. Distinguish checks actually run from suggested checks;
never invent commands or passing results. Read relevant code only when context is missing.

## Step 3 — Draft PR Description

Follow `git-flow → ## Pull requests` and
`git-flow → ## Commits → ### Pipeline identifiers stay out of the repository` for text hygiene.
Describe the final change for a reviewer without conversation context. Lead with the
concrete problem and resulting behavior. Scale detail to complexity; preserve a repository
PR template when present. Otherwise use this copy-ready Markdown block:

```markdown
## Summary
<One paragraph or a short list explaining what changed and why.>

## How it works
<Include only for non-obvious logic or an architectural change.>

## Validation
<Checks run and their results, or explicitly state that verification was not run.>
```

Omit inapplicable sections without adding explanations for their omission. Add manual
verification instructions only when useful: give prerequisites, the action, and the
observable expected result. Product paths and test commands are permitted when useful;
planning references and tool attribution are forbidden.

## Step 4 — Flag Concerns

Apply `suggest-commit-message → ## Step 4 — Flag Concerns` to the same change set.
Then **stop**.
