---
description: Suggest a commit message and PR description for the current changes — output is ready to copy
---

Invocation: `/suggest-commit-pr [--staged | --branch <base>]`

## Guard

Step 1 validates flags and context; an unavailable or empty selection stops both outputs.
No file is overwritten.

1. Gather and validate context once using
   `suggest-commit-message → ## Step 0 — Gather Diff Context`.
2. Run the remaining `/suggest-commit-message` steps against that context.
3. Run `/suggest-pr-description` against the same selection and evidence, reusing the
   gathered context. Do not reread git or widen the selection.
4. Output both copy-ready blocks and one combined, deduplicated "Notes for the author"
   section if needed. Then **stop**; do not commit or create a pull request.
