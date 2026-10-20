---
description: Discovery Step 4 — Finalize discovery, verify consistency, compress state
---

Invocation: `/pd-finalize <task-directory> [--step-by-step]`
Called by: `/phase-discovery` as Step 4.

Task directory = provided argument (trailing slash optional).

**Mode.** `--step-by-step` is accepted for symmetry with the other Discovery
steps; it does not change this workflow's behavior, since Step 4 ends the phase
and already stops at the final report. Consistency failures in step 1 stop in
both modes — they mean an earlier step must be re-run.

---

## Guard

1. Read `state.md` in the task directory.
2. Check `## Phases → discovery`. If `complete` → **stop**: "Discovery phase is already complete. Re-running will overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait for explicit confirmation.
3. Check `## Solution Design` with `### Decision` present in `state.md`. If missing → **stop**: "Step 3 (/pd-design) must be completed first. Run /pd-design <path>."
   **Exception — `flow: quick`.** The quick tier skips `/pd-decompose` and `/pd-design` by
   design (`quick-flow → The quick path`), so `## Solution Design` is never written and its
   absence is not a failure. When the top-of-file `flow:` field reads `quick`, skip this check
   and verify `## Contract (quick)` with `### Off-limits` / `### Invariants` /
   `### Acceptance Criteria` is present instead — if *that* is missing → **stop**: "Quick task
   has no `## Contract (quick)`. Run `/pd-analyze <path>` to write it."
4. Otherwise → continue.

---

## Instructions

Load `workflow-reference` for the Protected Sections Contract and .ai/memory/state.md Entry Format
before starting steps 5 and 6.

**Flow-tier branch (read `flow:` from `state.md`).** If `flow: quick`, there is no `plan.md`,
no T-XX directory, and no `## Solution Design`: **skip steps 1, 2 and 4b entirely** and verify
instead that `state.md` carries `## Contract (quick)` with all three sub-sections and that its
`### Acceptance Criteria` entries are binary and observable (the same testability standard
step 2 item 7 applies to a subtask criterion). A criterion that cannot be turned into a
pass/fail assertion fails the check — **stop** and return to `/pd-analyze`. Steps 3, 4, 4a, 5,
6, 7 and 8 run unchanged, reading `## Contract (quick)` wherever they would read
`## Solution Design`. If `flow: full`, run every step below unchanged.

1. Review all artifacts in the task directory for consistency:
   - `state.md` has sections: `## Task Analysis`, `## Solution Design` with `### Decision`.
   - `plan.md` has `## Subtasks` table with columns: `ID`, `Name`, `Key Steps (summary)`, `Depends On`, `Status`, with correct dependencies.
   - Each `T-XX-*/description.md` is consistent with the chosen architecture from `## Solution Design`.

2. **Per-subtask verification.** Before marking `discovery: complete`, verify for each T-XX listed in `plan.md`:
   1. `T-XX-*/description.md` exists.
   2. It contains all six sections: `## Goal`, `## Context`, `## Scope`, `## Steps`, `## Acceptance Criteria`, `## Test Plan`.
   3. `## Scope` contains both `In scope:` and `Out of scope:` entries (not blank).
   4. `## Steps` check — **two variants:**
      - **Leaf** (no `type: composite` in `## Context`): `## Steps` must have between 3 and 15 numbered implementation steps.
      - **Composite** (`## Context` contains `type: composite`): `## Steps` may contain only child references (e.g. "See children: T-04a, T-04b, T-04c.") — the step-count rule does NOT apply. Verify instead that `## Context` contains `children:` listing at least 2 children.
   5. `## Acceptance Criteria` has at least 2 checkable conditions.
      - For composites: these MUST be integration-level criteria (verifiable across the combined output of all children), not a restatement of individual children's criteria.
   6. `## Test Plan` check — verify all four:
      a. `Level:` is present and holds one of `unit` / `integration` / `contract` / `smoke` /
         `none` (or a combination). An empty or missing `Level:` fails the check.
      b. Every Acceptance Criterion from item 5 appears as at least one scenario. An
         uncovered criterion fails the check — the criterion is not testable as written.
      c. When `Level: none` — the justification line is present and names which of
         unit/integration/contract/smoke was considered and why each is inapplicable.
         Reject "hard to test", "no framework", "small change", "will add later", and
         "existing tests cover it": these are not justifications.
      d. For composites — `Level:` is `integration` or `contract`, and scenarios exercise the
         children together rather than restating individual children's tests.
   7. **Acceptance Criteria testability.** Each criterion is binary and observable — it states
      a condition and an exact expected result, not "works correctly" / "functions as
      expected". A criterion that cannot be turned into a pass/fail assertion fails the check.
   8. No extra files (`state.md`, `plan.md`) exist in the T-XX directory.

   If any T-XX fails this check — **stop** and return to `/pd-decompose` for that specific subtask before proceeding. Report the failing T-XX and which check did not pass.

   Additionally, for any composite T-XX: verify each child listed in `children:` has its own directory and `description.md` that passes all leaf checks (1–8 above). If a child fails → stop and return to `/pd-decompose`.

3. **Artifact conformance check.** Run the contract validator against the task
   directory:

   ```bash
   bash "${ORCHESTRAIL_HOME:?Set ORCHESTRAIL_HOME}/validate-task.sh" <task-directory> --phase discovery
   ```

   It applies the canonical contracts — `## Phases` vocabulary, the `flow:` tier, the
   six-section `description.md`, the `## Subtask Progress` block format, the required-even-
   when-empty fields, and the TDD audit trail — to the artifacts this phase produced, rather
   than to the workflow definitions. The manual review above says what to look for; this says
   whether it is actually there.

   - **Exit 0** → continue.
   - **Exit 1** → fix every reported failure, then re-run until it passes. A malformed
     artifact is cheap to fix now and expensive later: the next phase parses these files and
     will either misread them or stop.
   - **Script missing or not executable** → report that in one line and continue. The
     validator is a check, not a gate that can block work on its own absence.

4. Run `/compress-state --auto` on `state.md` in the task directory.

4a. Update `## Phases` in `state.md`: set `discovery: complete`.
    This is written **before** step 4b, not at the end: `/pd-archive`'s Guard stops unless
    `discovery: complete` is already present, so archiving is unreachable if the marker is
    written later. Steps 5–6 below do not depend on the phase status.

4b. Run `/pd-archive <task-directory>` to archive verbose Discovery content
    and reduce Execution-phase context load.
    If `state-archive.md` already exists in the task directory (resume case)
    — skip without error.
    **`flow: quick` — skip this step.** A quick task has no `### Variants` and no
    `### Rejected` to archive, and `quick-flow → The quick path` lists `/pd-archive` among the
    steps the tier skips.

5. Update state files — mandatory:

   **`.ai/memory/state.md`** — upsert task entry using the format from `workflow-reference → ## .ai/memory/state.md Entry Format`:
   `[task-id] | phase: discovery | status: complete | note: plan ready, <N> subtasks`
   When `active_phase:` is present, task-id = the phased directory name
   (`task-<basename>-p<N>`), per the entry format in `rules/workflow-reference.md`.

   **Multi-phase only** — when `active_phase: N` is present in `state.md`:
   - In `.ai/memory/state.md → ## Deferred`, add one line per phase K where K > N
     (upsert — do not duplicate if the line already exists):
     `- <basename> phase <K>/<M> | deferred | reason: later phase of <basename>, starts after phase <N> validation complete`
   - In `plan.md` (task-level), prepend the following banner as the very first line:
     `> Scope: Phase <N> of <M>. Phases <N+1>–<M> deferred (see state.md → ## Spec Phases).`

   **`.ai/project_state.md`** — update per rules in `workflow-reference → ## .ai/project_state.md Update Rules`:
   - Add entry to `## In-flight work`: planned modules, endpoints, architecture changes from `## Solution Design → ### Decision`. Code does not yet exist.
   - If file does not exist — skip without error.

6. Update root files — for each file, explicitly state your decision (update / skip) and the reason:

   | File | Update when | Surgical edit: only |
   |------|-------------|---------------------|
   | `.ai/memory/architecture.md` | Chosen architecture introduces new modules, components, or changes to existing structure | affected architecture sections |
   | `.ai/principles/architecture.md` | New architectural decisions, constraints, or off-limits were established that are not already documented | corresponding decision/constraint sections |

   **Update principle:** surgical edits only — change only what Discovery directly determined. Do not rewrite unrelated sections. If a file does not exist — skip without error.

7. Verify `## Phases → discovery: complete` is present in `state.md` (written in step 4a).
   If a later step overwrote it, restore it.
8. Report to user (display as text — do NOT invoke):
   - Path to `state.md` — full analysis and chosen solution.
   - Path to `plan.md` — subtask list with dependencies (omit on `flow: quick`, which has no
     `plan.md`; report the path to `## Contract (quick)` in `state.md` instead).
   - "Discovery complete. Run `/phase-execution <task-directory>` to start execution."
   - **If Discovery ran autonomously** (no `--step-by-step`) — a review digest:
     chosen architecture in one line, the `### Autonomous Decision` winner and
     total score, and every entry from `## Task Analysis → ### Assumptions`.
     Close with: "Decisions were made autonomously. Re-run with `--step-by-step`
     to review each step interactively."
   - **Multi-phase only** — if `active_phase: N` is present and N < spec_phase_count:
     "Phase <N> discovery complete. After Phase <N> validation completes, run
     `/phase-discovery <spec_path> --phase <N+1>` to begin the next phase."

**STOP. Do not run `/phase-execution` automatically.**
