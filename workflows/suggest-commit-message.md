---
description: Suggest a commit message for the current changes — output is ready to copy
---

Invocation: `/suggest-commit-message [--staged | --branch <base>]`
Called by: `/suggest-commit-pr`; `/suggest-pr-description` reuses Step 0 only.

This workflow suggests text; it performs no git writes. Follow `git-flow → ## Commits`
and `git-flow → ## Commits → ### Pipeline identifiers stay out of the repository` for output hygiene.

## Guard

Validate the selected context and flags using
`suggest-commit-message → ## Step 0 — Gather Diff Context`; an unavailable or empty
selection stops the workflow. No existing file is overwritten.

## Step 0 — Gather Diff Context

Use the following selection for this workflow and the other suggestion workflows.
Reject unknown flags and a combination of `--staged` with `--branch`.

| Invocation | Change set | File list |
|---|---|---|
| No flags | Final changes made in the current conversation; run no git commands | Derive from session context |
| `--staged` | `git diff --cached` | `git diff --cached --name-only` |
| `--branch <base>` | `git diff <base>...HEAD` | `git diff <base>...HEAD --name-only` |

Resolve paths from the current repository root. Validate that `<base>` resolves to a
commit before using it. In branch mode, describe committed branch changes only; staged
and unstaged changes are outside that selection. In git modes, read up to ten recent
commit subjects for style, subordinate to the project's commit rules. An unborn HEAD is
valid for `--staged`; branch mode requires HEAD and a merge base.

If a requested revision or merge base is unavailable → **stop**: name the missing input.
If the selected change set is empty → **stop**: "No changes found in the selected context."
Do not substitute a different selection. Reuse already gathered context when called by
`/suggest-commit-pr`.

## Step 2 — Analyse Changes

Use the selected diff or session context. Read nearby code only where intent or behavior
is unclear. Identify the resulting behavior, the reason supported by evidence, the change
type, and any breaking API, schema, or configuration change. Do not invent motivation.

## Step 3 — Draft Commit Message

Output one copy-ready fenced block using the format in `git-flow → ## Commits`:

```text
<type>[(<feature or module>)]: <imperative summary>

<optional body: what changed and why>
```

Keep the subject and body lines within 72 characters. Omit a redundant body. Describe
behavior and intent; include a product path only when it makes the change clearer and
project rules permit it. Never copy planning identifiers or tool attribution into the text.

## Step 4 — Flag Concerns

After the block, add "Notes for the author" only for evidenced concerns: breaking changes,
missing verification, unfinished changes, exposed secrets, or unintended debug output.
Use one line per concern, without reproducing secret values. Then **stop**.
