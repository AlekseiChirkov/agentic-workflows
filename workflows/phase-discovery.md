---
description: Phase 1 — Discovery orchestrator: analyze task, decompose, design architecture, finalize plan
---

Invocation: `/phase-discovery <path-to-spec> [--phase N] [--step-by-step]`
Example: `/phase-discovery .ai/specs/01-add-oauth.md --phase 2`

The spec must be a file in `.ai/specs/`. Child workflows take the task directory,
not the spec path. `/pd-select-model` is optional here; `/spec-run` invokes it separately.

## Execution Modes

State the selected mode before Step 1 and pass `--step-by-step` to children only
when that flag was supplied.

| Mode | Behavior |
|---|---|
| Autonomous (default) | Run all remaining children in this turn. Completion reports are progress markers, not handoffs. |
| Step-by-step | Resolve questions interactively; after each child, report artifacts, key decisions and the next step, then **stop** and wait for review. No extra review pause after the final report. |

### Autonomous mode overrides

For this phase, resolve ambiguity using `workflow-reference → ## Autonomous Decision
Protocol` instead of the global wait-for-decision and doubt-stop rules. Research
principles → relevant ADRs → memory → codebase patterns → best practice. Record
requirement resolutions in `## Task Analysis → ### Assumptions`, decomposition
choices in `plan.md → ## Decomposition Decisions`, and architecture scoring in
`## Solution Design → ### Autonomous Decision`. Derive missing Acceptance Criteria
from the spec and record that assumption.

Escalate only on the protocol's threshold, a hard blocker, or an overwrite Guard.
Under `/spec-run`, its Class A/B escalation and Discovery batch gate take precedence.
Overwrite Guards still apply. Only an encompassing workflow such as
`/phase-pipeline` may advance phases.

### Step-by-step mode behavior

After a nonfinal child completes, output `Step <N> complete — review requested`,
the artifacts written, key decisions, and next child. Continue only after explicit
go-ahead. A skipped child requires no review pause.

## Context Bootstrap

Apply the `phase-discovery` rule's Context Bootstrap once per context. Children
reuse that context; standalone children bootstrap it themselves. Skip missing files,
load umbrella before local context, and report the files loaded and applicable constraints.

## Guard

Run the read-only checks in Step 0 before creating or replacing artifacts.
Missing/invalid input, conflicting task locations, ambiguous phase boundaries, and
an overwrite requiring confirmation all **stop** the workflow. A confirmation
already given for this exact rerun applies to its children; do not ask repeatedly.
An encompassing parent may request **resolution-only Step 0** to locate artifacts
for resume. That read-only operation accepts completed Discovery without an
overwrite confirmation and returns before state changes, logging or child execution.

## Step 0 — Bootstrap

1. Parse arguments; if the spec path is missing, **stop** and request it. Verify
   the file exists under `.ai/specs/` and its first heading is H1. Otherwise
   **stop** with the invalid path or missing-title reason.
2. Read the spec. Without `## Acceptance Criteria`, derive criteria in autonomous
   mode; in step-by-step mode, ask whether to continue with interactive clarification.
3. Resolve phase scope using `workflow-reference → ## Multi-Phase Spec Rules`:
   - Use a `## Phases` manifest when present; every listed phase must map to one
     `## Phase N` or `### Phase N` section. Otherwise detect distinct phase numbers
     from those headings. Two or more phases means multi-phase.
   - Ambiguous, duplicate or unmapped boundaries → **stop** and report them.
   - `--phase N` must name an existing phase; reject it for a single-phase spec.
   - Resolution-only parent resume without `--phase`: first select the unique
     existing phase task whose validation is incomplete. Multiple unfinished tasks
     → **stop** and request an explicit phase. Otherwise use the default below.
   - Default without `--phase`: select the lowest phase with no task directory
     anywhere under `.ai/tasks/`, including completed tasks. If none remains,
     report all phases discovered; a resolution-only parent may inspect the last
     completed phase, while standalone discovery **stops** and requests an explicit phase.
   - Derive `.ai/tasks/todo/task-<spec-basename>/` for a single phase, or
     `.ai/tasks/todo/task-<spec-basename>-p<N>/` for a multi-phase spec.
4. If the filename has a numeric prefix, check other active `.ai/specs/` files for
   that exact prefix (digits before the first `-`). A collision → **stop**: `Spec prefix collision: <paths>`;
   request renaming. Do not treat a filename without such a prefix as a collision.
5. Locate any existing directory with the derived task basename under `.ai/tasks/`.
   Multiple locations → **stop** and report them. A completed location may be
   adopted only for resolution-only parent inspection; otherwise **stop** and report
   its path. Never create a duplicate in `todo/`.
6. For an existing task, read its `state.md`; missing or malformed phase state →
   **stop** and report what must be repaired. For `discovery: complete`, require
   overwrite confirmation only when rerunning Discovery; resolution-only inspection
   adopts existing artifacts without mutation. Preserve all existing
   fields, execution/validation statuses, and progress. For `in-progress`, resume
   using Step 0.5. For `not-started`, begin analysis.
7. **Resolution-only parent call:** return the resolved spec/task paths, phase and
   existing phase statuses now. Do not create files, set `discovery: in-progress`,
   bootstrap/log a Discovery run, or invoke children. Otherwise create the task
   directory after checks pass and initialize a new `state.md`:

   ```
   spec_path: <spec-path>
   flow: full

   ## Phases
   - discovery: in-progress
   - execution: not-started
   - validation: not-started
   ```

   On resume, preserve `spec_path:` and `flow:`; add a missing source path or
   default flow only when absent, and set only `discovery: in-progress`.
   Multi-phase tasks also carry `active_phase: N` and `spec_phase_count: M`
   alongside `spec_path:`, plus `## Spec Phases`:

   ```
   ## Spec Phases
   - phase <N>: in-discovery — <title> — <task-directory>
   - phase <K>: deferred — <title> — —
   - phase <J>: complete — <title> — <existing-task-directory>
   ```

   Mark the active phase `in-discovery`, undiscovered phases `deferred`, and
   prior phases `complete` only when their task validation is complete. If another
   discovered phase is incomplete, **stop** and report it before claiming completion
   or proceeding to a later phase. Single-phase tasks omit these phase-specific fields.
8. Bootstrap context and open the run log before the first child.

## Run Logging

Follow `run-log → ## Workflow coverage and routing`. Resolve the helper from
`ORCHESTRAIL_HOME` and issue `scripts/log-step.sh run-start --pipeline phase-discovery`
with project, resolved task, spec, current flow and flags. Keep `LOG_HELPER` and
`RUN_ID`; on a later-session resume start a new run. A parent-owned run uses the
parent's routing rather than opening an independent child run.

Log each child actually executed (`pd-analyze`, `pd-decompose`, optional
`pd-select-model`, `pd-design`, `pd-finalize`, `pd-archive`); account for nested
archive once. Add `--note approximate` to ordinary prompt steps. Carry observed
questions, stops, decisions, escalations and quick-to-full promotion counts.
Close with `run-end --outcome completed` after finalization, or `stopped` on an
early stop. Missing/failed logging never delays work; mention it once in the final report.

## Step 0.5 — Resume Check (if state.md existed)

Use explicit markers in order:

- `## Task Analysis` → Step 1 complete.
- Above plus `## Decomposition` / `decomposition: complete` → Step 2 complete.
- Above plus `## Solution Design` / `### Decision` → Step 3 complete.
- `flow: quick` plus `## Contract (quick)` → Steps 2–3 intentionally skipped.

A marker whose required artifact is missing or contradictory → **stop** and
report the inconsistency. Partial T-XX artifacts without a completion marker
still enter `/pd-decompose`'s overwrite Guard. A confirmed rerun starts at Step 1; otherwise resume at the first incomplete step.
Report the resume point.

## Execution

Run the remaining children in order, passing the task directory and selected mode:

1. `/pd-analyze <task-directory>` — analysis and flow selection.
2. `/pd-decompose <task-directory>` — full flow only.
3. `/pd-design <task-directory>` — full flow only.
4. `/pd-finalize <task-directory>` — consistency, archive and final report.

Read `flow:` after Step 1: for `flow: quick`, skip Steps 2 and 3; create no T-XX or
`plan.md`; full flow runs all steps. Apply `quick-flow` if scope requires promotion.
A child Guard or hard blocker stops the phase in either mode. In autonomous mode,
immediately invoke the next child when the previous one succeeds.

Let `/pd-finalize` supply the single final report: artifact paths, chosen approach,
autonomous assumptions and scores when available, and the next command as text.
For quick flow, report the inline contract.

**STOP. Do not run `/phase-execution` automatically.**
