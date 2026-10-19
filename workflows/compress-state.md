---
description: Clean and compress state files — remove stale content, keep only what is current and accurate
---

Invocation: `/compress-state [path]`
Examples:
- `/compress-state` — compress `.ai/memory/state.md` (default)
- `/compress-state .ai/tasks/todo/task-01-add-oauth/state.md` — compress specific file
- `/compress-state --auto .ai/tasks/todo/task-01-add-oauth/state.md` — skip confirmation

---

## Step 0 — Read Input

1. Determine target file:
   - If path provided → use it.
   - Otherwise → `.ai/memory/state.md`.
2. Read target file fully.
3. If target is `.ai/memory/state.md` → also read all `state.md` files in task directories for context.
4. If target file does not exist → report and **stop**.

---

## Step 1 — Audit Content

Classify each section:

1. **Current** — describes active state, decisions, constraints. Keep unchanged.
2. **Stale** — describes what already changed: old decisions, completed phases, removed components. Mark `[STALE]`.
3. **Duplicate** — already present elsewhere in the same file without added value. Mark `[DUPLICATE]`.
4. **Inaccurate** — contradicts actual state. Mark `[INACCURATE]`.
5. **Verbose** — intermediate reasoning where only the conclusion matters. Mark `[VERBOSE]`.

Output list of all findings. If none: "File is current, no compression needed."

---

## Step 2 — Confirm Changes

Output plan: what will be removed, shortened, corrected, or kept.

If `--auto` flag is present → proceed to Step 3 immediately without waiting.
Otherwise → **wait for user confirmation**.

---

## Step 3 — Apply Compression

Load `workflow-reference` for the Protected Sections Contract before applying compression.

1. **Remove** `[STALE]` and `[DUPLICATE]` sections.
2. **Correct** `[INACCURATE]` sections to match actual state.
3. **Shorten** `[VERBOSE]` sections: keep conclusions, remove reasoning path.
4. **Preserve structure**: do not rename section headers used by other workflows.
5. **Do not add** new content — only clean and compress.

Protected sections and fields are defined in `workflow-reference → ## Protected Sections Contract`. Never remove, rename, or summarize any of them. This includes composite-specific protected lines: `[composite]` prefix, `children:`, `rollup:`, and `integration-validation:` fields — never strip these from composite blocks.

Additionally, lines of the form `→ archived to state-archive.md` must never
be removed, compressed, or treated as stale. These are live references to
`state-archive.md` — removing them breaks the archive contract.

The git audit trail in orchestrated mode is protected the same way: the `branch:`,
`base_branch:`, `base_commit:`, `commits:`, and `pr:` fields in leaf blocks, and any `notes:`
line beginning with `arbiter:`. `base_commit` in particular cannot be recomputed once the
parent branch has been squash-merged and deleted — compressing it away makes `/restack`
impossible and strands the branch stack.

The TDD audit trail is likewise protected: the `atomic-tests:` field in leaf blocks, the
`## TDD (quick)` section in quick-tier `state.md` files, and any `notes:` line beginning with
`tdd:` (test level, `none` justification, test amendment records). These record decisions
that `/pav-check` and `/pv-review` audit later — a compressed-away justification reads as an
unjustified skip.

The rationale: these sections are contracts read by orchestrators to determine continuation points. Inside a protected section, stale bullet points may be shortened, but headers and marker lines must remain verbatim.

---

## Step 4 — Verify Result

1. Confirm all sections referenced by workflows are still present.
2. Output statistics: lines before/after, what was removed/shortened/corrected.
3. If reduction < 10% → note: "Minimal compression — file was already in good shape."
