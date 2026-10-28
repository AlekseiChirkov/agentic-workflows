---
description: Atomic Validation Step 2 — Propose improvements, categorize; interactive or batch mode
---

Invocation: `/pav-propose <path-to-atomic-description> [--batch]`
Called by: `/phase-atomic-validation` as Step 2. Only runs if verdict is DONE.

**Modes:**
- **Interactive** (default, no flag): prompt user for "Do Now" items before applying.
- **Batch** (`--batch`): record all proposals to `state.md` without prompting or applying. "Do Now" items are tagged for post-execution review by `/pe-finalize`.

Canonical proposal semantics: `workflow-globals → Workflow-declared mode overrides`.
`--batch` means record every proposal, prompt for nothing, apply nothing. `/pe-finalize`
step 5 owns later application when selected; no caller may reinterpret the flag.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.
Load the `phase-atomic-validation` rule (`## Context Bootstrap`) before code reads or writes, including standalone invocation.

---

## Guard

1. Read parent `state.md`. Locate the `## Subtask Progress` block for this T-XX.
2. If block has `atomic-validation: complete` → **stop**: "Atomic validation already complete. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Otherwise → continue.

---

## Pre-check

Read parent `state.md → ## Subtask Progress` block for this T-XX.
If `atomic-validation: failed` → **stop**: "Verdict is NEEDS WORK. Fix issues first."
If `last_action` is not `pav-check DONE` → **stop**: "Run `/pav-check` successfully before proposing improvements."

---

## Instructions

Under `/spec-run`, return the shared proposal section as a delta; only the orchestrator
writes it. Your own leaf block remains writable.

1. Read files changed during execution from parent `## Subtask Progress → T-XX → target_files:` with focus on quality.
2. Identify improvements with concrete measurable effect:
   - **Simplification**: unnecessary layers, abstractions.
   - **Duplication**: repeated code worth extracting.
   - **Performance**: with justification (what, where, why slow).
   - **Readability**: renaming, condition simplification.
   - **Robustness**: opportunities beyond the satisfied contract.
   A newly discovered correctness defect returns to `/pav-check` as NEEDS WORK; do not
   disguise it as a discretionary improvement.

3. Categorize:
   - **Do Now**: high effect, low risk, within parent `## Solution Design → ### Scope → #### In`.
   - **Do Later**: high effect but outside `## Solution Design → ### Scope → #### In` or needs separate planning.
   - **Optional**: low effect, discretionary.
   If improvement is outside `## Solution Design → ### Scope → #### In` → automatically **Do Later**, regardless of effect.
   If no improvements found → no proposals section is written.

4. Before prompting/applying, upsert one `## Improvement Proposals (T-XX)` section
   when proposals exist; preserve existing decisions and mark applied/declined items so a
   resume cannot apply them twice:

```
## Improvement Proposals (T-XX)

### Do Now
<items or "None">

### Do Later
<items or "None">

### Optional
<items or "None">
```

   No proposals → no section. Mirror Do Later / Optional summaries in leaf `notes:`.

5. Handle unresolved Do Now items:
   - **Interactive:** present the persisted list, ask which to apply, and wait for approval.
     Apply only approved items within scope, follow the TDD gate for changed behaviour,
     preserve frozen tests, update `target_files:`, and rerun tests/lint and AC verification.
     A failed check → record `atomic-validation: failed` and stop; do not close.
   - **Batch:** do NOT prompt and do NOT apply. Report the count recorded for later review.

6. Update the parent `state.md → ## Subtask Progress` block for this T-XX: set
   `last_action: pav-propose done`, mirroring the `pav-check DONE` marker `/pav-check` writes.
   Preserve the cumulative `target_files:`, `atomic-tests:`, and all existing/TDD notes.

   **Write this line in every mode**, including zero proposals, only after all approved
   work and checks finish. It is the resume marker `/phase-atomic-validation` reads.

7. Report: "Step 2 (Improvements) complete." This is a progress marker for `/pav-close`.
