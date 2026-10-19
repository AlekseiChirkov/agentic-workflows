---
description: Atomic Validation Step 2 — Propose improvements, categorize; interactive or batch mode
---

Invocation: `/pav-propose <path-to-atomic-description> [--batch]`
Called by: `/phase-atomic-validation` as Step 2. Only runs if verdict is DONE.

**Modes:**
- **Interactive** (default, no flag): prompt user for "Do Now" items before applying.
- **Batch** (`--batch`): record all proposals to `state.md` without prompting or applying. "Do Now" items are tagged for post-execution review by `/pe-finalize`.

`--batch` has exactly one meaning, fixed in `workflow-globals → Workflow-declared mode
overrides`: **record everything, prompt for nothing, apply nothing.** Every caller that passes
it down — `/phase-atomic-validation`, `/pe-execute`, `/pv-execute-fixes`, `/spec-run`,
`/phase-pipeline` — gets that behaviour and no other. A caller that wants the `Do Now` items
applied applies them in a step of its own (`/phase-pipeline` does so at `/pe-finalize` step 5);
it may not reinterpret this flag as apply-without-asking.

Atomic task directory = parent directory of the provided `description.md`.

---

## Guard

1. Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.
2. If block has `atomic-validation: complete` → **stop**: "Atomic validation already complete. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Pre-check

Read parent `state.md → ## Subtask Progress` block for this T-XX.
If `atomic-validation: failed` → **stop**: "Verdict is NEEDS WORK. Fix issues first."
Verify `last_action` was set to `pav-check DONE` by `/pav-check`.

---

## Instructions

1. Read files changed during execution from parent `## Subtask Progress → T-XX → target_files:` with focus on quality.
2. Identify improvements with concrete measurable effect:
   - **Simplification**: unnecessary layers, abstractions.
   - **Duplication**: repeated code worth extracting.
   - **Performance**: with justification (what, where, why slow).
   - **Readability**: renaming, condition simplification.
   - **Robustness**: unhandled edge cases visible from implementation.

3. Categorize:
   - **Do Now**: high effect, low risk, within parent `## Solution Design → ### Scope → #### In`.
   - **Do Later**: high effect but outside `## Solution Design → ### Scope → #### In` or needs separate planning.
   - **Optional**: low effect, discretionary.
   If improvement is outside `## Solution Design → ### Scope → #### In` → automatically **Do Later**, regardless of effect.
   If no improvements found → no proposals section is written.

4. If **Do Now** items exist:
   - **Interactive mode** (no `--batch`): present to user and ask: "Apply improvements now or close task?" **Wait for approval.** Apply only approved Do Now items.
   - **Batch mode** (`--batch`): do NOT prompt and do NOT apply. Record all Do Now items to `state.md` and continue immediately. Print: "Batch mode: N Do Now proposal(s) recorded for T-XX — will surface after execution phase."

5. If proposals are non-empty, append to parent `state.md` a section `## Improvement Proposals (T-XX)`:

```
## Improvement Proposals (T-XX)

### Do Now
<list or "None">

### Do Later
<list or "None">

### Optional
<list or "None">
```

If any `Do Later` / `Optional` items exist, also mirror them as a one-line summary into the `notes:` field of the T-XX `## Subtask Progress` block.

6. Update the parent `state.md → ## Subtask Progress` block for this T-XX: set
   `last_action: pav-propose done`, mirroring the `pav-check DONE` marker `/pav-check` writes.
   Preserve `notes:`, `target_files:`, and `atomic-tests:` unchanged.

   **Write this line in every mode** — interactive and `--batch` alike — and **whether or not
   any proposals were found.** It is the only record that step 2 finished: step 5 writes
   `## Improvement Proposals (T-XX)` only when proposals are non-empty, and
   `atomic-validation: complete` is not set until `/pav-close`. Without this marker,
   `phase-atomic-validation` Step 0 cannot tell a run interrupted before step 2 from one
   interrupted after it, and would silently re-run the wrong step.

7. Report: "Step 2 (Improvements) complete."
