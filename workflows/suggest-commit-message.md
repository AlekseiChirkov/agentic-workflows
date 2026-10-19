---
description: Suggest a commit message for the current changes — output is ready to copy
---

Invocation: `/suggest-commit-message`
Examples:
- `/suggest-commit-message` — use current session context (changes made in this conversation)
- `/suggest-commit-message --staged` — only staged changes (reads git)
- `/suggest-commit-message --branch main` — diff against a different base branch (reads git, default: main)

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

---

## Step 3 — Draft Commit Message

Rules:
- Subject line: imperative mood, ≤ 72 characters, no period, no issue number unless obvious from the diff.
- Blank line after subject.
- Body (only if needed): explain *why*, not *what*. Wrap at 72 characters. Omit entirely if the subject is self-explanatory.
- Standard commit prefix when the project uses it (infer from `git log`). Common prefixes: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `ci`.
- **Never mention file names, file paths, or directory names** — describe what changed conceptually, not where it lives in the repository.

Output format — present inside a fenced code block so it is copy-ready:

```
<type>(<scope>): <subject>

<body — omit if not needed>
```

---

## Step 4 — Flag Concerns

After the copy-ready block, add a short **"Notes for the author"** section (omit entirely if nothing to flag):

- Breaking changes that need a migration guide or version bump.
- TODOs or commented-out code left in.
- Secrets, debug flags, or `print()` / `console.log()` left in.
- Anything that looks unfinished or inconsistent with the rest of the diff.

Keep this section brief — one line per concern.
