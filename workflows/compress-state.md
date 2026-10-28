---
description: Clean and compress state files — remove stale content, keep only what is current and accurate
---

Invocation: `/compress-state [path] [--auto]`
Default target: `.ai/memory/state.md`. Resolve relative paths from the current project root.
`--auto` skips the compression-plan confirmation, not preservation or evidence checks.

## Guard

1. Read the target fully. If missing → **stop**: "No state file at `<path>`."
2. Load `workflow-reference → ## Protected Sections Contract` before classifying content.
   Protected content takes precedence over every compression instruction below.
3. For project memory, inspect active task state referenced by its entries. Read other task
   state only when needed to resolve a specific claim; do not load all completed tasks.

## Step 1 — Audit Content

Classify unprotected content using evidence from current state and referenced artifacts:

| Class | Treatment |
|---|---|
| Current | Keep |
| Stale | Remove only if no longer needed to resume or interpret current state |
| Duplicate | Keep one authoritative occurrence |
| Inaccurate | Correct only when the replacement is verified |
| Verbose | Keep the conclusion, constraints, and unresolved decisions |

Do not treat completion as proof of staleness. Preserve unresolved or conflicting claims
and report their uncertainty. Classification labels are working notes, not edits to disk.
If nothing can be improved → report "File is current; no compression needed." and **stop**.

## Step 2 — Confirm Changes

Report a concise plan of removals, corrections, and reductions. Proceed with `--auto` or
existing explicit authorization; otherwise wait for confirmation before writing.

## Step 3 — Apply Compression

Apply only the audited changes. Keep machine-read headers, marker syntax, field names,
and current phase status. Do not add scope or derive new decisions.

The canonical Protected Sections Contract governs, including archive pointers
(`→ archived to state-archive.md`), `atomic-tests:`, `tdd:` evidence, composite blocks,
and the git fields including `base_commit:`. Never remove, rewrite, or summarize these
as a compression operation. Shorten prose inside a protected section only when that
contract explicitly permits it.

## Step 4 — Verify Result

Compare protected content before/after; it must remain intact. Confirm all continuation
markers and referenced sections still exist. Report line counts before/after and a short
list of changes. If reduction is below 10%, report "Minimal compression; little redundant
content." Then **stop**.
