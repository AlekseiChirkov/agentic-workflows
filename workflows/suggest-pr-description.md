---
description: Suggest a PR description for the current changes — output is ready to copy
---

Invocation: `/suggest-pr-description`
Examples:
- `/suggest-pr-description` — use current session context (changes made in this conversation)
- `/suggest-pr-description --staged` — only staged changes (reads git)
- `/suggest-pr-description --branch main` — diff against a different base branch (reads git, default: main)

---

## Step 0 — Gather Diff Context

**Mode selection:**

- If invoked **with no arguments** (clean command) → **Session-context mode**: skip git commands entirely. Reconstruct the change set from the current conversation — every file the assistant wrote, edited, or deleted during this session. Proceed directly to Step 2 using that context. If no edits were made in this session, report "No changes found in current session." and **stop**.

- If invoked **with any flag** (`--staged`, `--branch`, etc.) → **Git mode**: run the steps below.

**Git mode only:**

1. Determine base branch:
   - If `--branch <name>` provided → use it.
   - Otherwise → `main`.

2. Collect diff:
   - If `--staged` → run `git diff --cached`.
   - Otherwise → run `git diff HEAD` (staged + unstaged). If HEAD does not exist, run `git diff --cached`.

3. Also run:
   - `git diff --name-only HEAD` (or `--cached` if `--staged`) — file list.
   - `git log --oneline -10` — recent commit style reference.
   - `git diff <base-branch>...HEAD --stat` — cumulative branch delta (omit if no commits yet).

4. If the diff is empty → report "No changes detected." and **stop**.

---

## Step 2 — Analyse Changes

Read each changed file fully only when the diff alone is insufficient to understand intent (e.g. context around a moved block, interface contract). Otherwise work from the diff.

Identify:
- **What changed** — the concrete code-level delta (files, functions, data structures).
- **Why it changed** — the intent or problem being solved, inferred from diff + file names + recent commits.
- **Scope** — new feature / bug fix / refactor / chore / docs / test / infra.
- **Breaking changes** — public API, DB schema, config keys, env vars altered in a non-backwards-compatible way.
- **Testing surface** — how an engineer could verify this works (from the diff, not invented).

---

## Step 3 — Draft PR Description

Sections to include (omit a section only if it is genuinely not applicable — say why):

**Summary**
Bullet list of what changed and why. 2–5 bullets. No filler sentences. Never mention file names, paths, or directory names — describe behaviour and intent only.

**How it works** *(include only if the change introduces non-obvious logic, a new flow, or architectural change)*
1–3 sentences or a short numbered list. Focus on the mechanism, not the motivation. No file names or paths.

**How to test**
Numbered checklist. Each step must be concrete and reproducible by someone unfamiliar with the change. Include:
- Environment setup if non-trivial.
- The specific action to perform.
- The expected observable outcome.

If there are automated tests that cover this: mention them and how to run them.

Output format — present inside a fenced Markdown block so it is copy-ready:

```markdown
## Summary
- …

## How it works
…

## How to test
1. …
2. …
```

---

## Step 4 — Flag Concerns

After the copy-ready block, add a short **"Notes for the author"** section (omit entirely if nothing to flag):

- Breaking changes that need a migration guide or version bump.
- Missing test coverage inferred from the diff.
- TODOs or commented-out code left in.
- Secrets, debug flags, or `print()` / `console.log()` left in.
- Anything that looks unfinished or inconsistent with the rest of the diff.

Keep this section brief — one line per concern.
