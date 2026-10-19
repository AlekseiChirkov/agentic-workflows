---
description: Suggest a commit message and PR description for the current changes — output is ready to copy
---

Invocation: `/suggest-commit-pr`
Examples:
- `/suggest-commit-pr` — use current session context (changes made in this conversation)
- `/suggest-commit-pr --staged` — only staged changes (reads git)
- `/suggest-commit-pr --branch main` — diff against a different base branch (reads git, default: main)

---

This skill runs two sub-skills in sequence, passing the same arguments to each:

1. Invoke `/suggest-commit-message` (with all args as received) — produces a copy-ready commit message.
2. Invoke `/suggest-pr-description` (with all args as received) — produces a copy-ready PR description.

Both outputs appear together so the author has everything needed to open a PR in one step.
