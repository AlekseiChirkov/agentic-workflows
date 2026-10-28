---
description: Atomic Execution Step 3 — Update statuses in atomic and parent state files, compress
---

Invocation: `/pae-finalize <path-to-atomic-description>`
Called by: `/phase-atomic-execution` as Step 3.

Atomic task directory = parent directory of the provided `description.md`.
Parent task directory = one level above.

---

## Guard

Read the description and parent progress block before writing. `atomic-execution: complete`
is the expected successful input from `/pae-implement`, not evidence that finalization ran.
Missing state, execution not complete, or `blocker:` other than `none` → **stop**:
"Complete `/pae-implement` successfully before finalizing."

`atomic-tests:` must be `green` or justified `n-a`; absent is allowed only with the recorded
pre-TDD exemption. Any other value → **stop**: "Implementation has not reached GREEN."
If the plan is already `done`/`reviewed` and the finalization result is recorded, ask for
explicit confirmation before replacing it. Do not prompt on the first successful call.

---

## Context Bootstrap

Resolve `working_dir:` relative to the atomic task directory (absent → invocation directory),
set absolute `WORK_DIR` / `AI_DIR`, and load `phase-atomic-execution → ## Context Bootstrap`
before project writes. Keep description/state/plan paths absolute.

## Instructions

Use the Status Translation Table in workflow-reference before changing plan statuses.
Under `/spec-run`, write only this leaf's progress block; return all plan, architecture,
composite, and compression changes as deltas under `orchestration → ## Shared-file discipline`.

1. Preserve the successful leaf block: `atomic-execution: complete`, `blocker: none`.
   Preserve `atomic-tests:` as set by `/pae-tests` / `/pae-implement` (`green` or `n-a`).
   Never remove or downgrade it. Preserve cumulative `target_files:` and all `notes:` /
   `tdd:` evidence and git fields. Never create atomic `state.md` or `plan.md` files.

2. Check `AI_DIR/memory/architecture.md` for modules/interfaces in `target_files:`.
   Add a missing module's purpose, key exports, and layer; update a changed interface in
   place. No interface change or missing architecture file → skip. Append the outcome
   to `notes:`; in orchestrated mode distinguish a proposed delta from an applied update.

3. Update parent `plan.md`: this leaf's `Status` becomes `done`.
   **Orchestrated mode (`/spec-run`) — do not write the file.** Return `T-XX → done`
   as a delta for the orchestrator instead.

4. **Incremental composite rollup.** Find actual membership in a composite block's
   `children:` list; a letter-suffixed ID alone is not proof (Type 3 leaves share that form).
   No membership → skip. Otherwise inspect every sibling's atomic execution:
   any blocked → `rollup: blocked`; all complete → `rollup: done`; otherwise `in-progress`.
   Update the composite plan row to the matching status (`done`, `blocked`, `in-progress`),
   preserving `reviewed` when integration already passed and no child has reopened.
   Copy a blocking child's reason into `blocker:`; otherwise set `none`.
   In `/spec-run`, return these composite/plan updates as deltas.

5. Run `/compress-state --auto` on parent state (or request the shared edit from the
   orchestrator). After all finalization actions, set
   `last_action: pae-finalize done — <implementation summary>` in this leaf's block.

6. Report execution, TDD mode/level, verification, and which updates were applied or
   returned as deltas. Display `/phase-atomic-validation <path>` as the next atomic step.
   This is a progress marker for an active caller, not a handoff.
