---
description: Phase 1 — Discovery orchestrator: analyze task, decompose, design architecture, finalize plan
---

Invocation: `/phase-discovery <path-to-spec> [--phase N] [--step-by-step]`
Example: `/phase-discovery .ai/specs/01-add-oauth.md`
         `/phase-discovery .ai/specs/01-add-oauth.md --phase 2`
         `/phase-discovery .ai/specs/01-add-oauth.md --step-by-step`

`--phase N` selects which phase of a multi-phase spec to discover. If omitted
on a multi-phase spec, the lowest phase with no existing task directory is chosen.

`--step-by-step` switches to manual review mode — see `## Execution Modes`.

The spec file must be in `.ai/specs/`. Task directory is derived automatically:
- Single-phase: `task-` + spec filename without extension.
- Multi-phase: `task-` + spec filename without extension + `-p<N>`.
Example: `.ai/specs/01-add-oauth.md` → `.ai/tasks/todo/task-01-add-oauth/` (single-phase)
                                     → `.ai/tasks/todo/task-01-add-oauth-p1/` (multi-phase, phase 1)

If path is not provided — ask the user and do not continue.

To run a single step directly, call the child workflow:
`/pd-analyze`, `/pd-decompose`, `/pd-design`, `/pd-finalize`.
Pass the task directory as the argument to child workflows (not the spec path).

---

## Execution Modes

Determine the mode in Step 0 and state it explicitly before Step 1. Pass the
mode to every child workflow as an argument (`--step-by-step` when in manual
review mode; nothing when autonomous).

| Mode | Trigger | Behavior |
|---|---|---|
| **Autonomous** | default — no `--step-by-step` | Run Steps 1→4 back-to-back in a single uninterrupted session. Never return control to the user between steps. |
| **Step-by-step** | `--step-by-step` passed | After each step, stop, present what was produced, and wait for the user's review before starting the next step. |

### Autonomous mode overrides

These override the corresponding rules in `workflow-globals` **for the duration
of this phase only**. Every other global rule stays in full force — in
particular, `Never auto-advance between phases` still applies: Discovery ends
at `/pd-finalize` and never invokes `/phase-execution`.

| Overridden rule | Autonomous behavior |
|---|---|
| "Wait for user decisions" (`workflow-globals`) | Decide independently via the **Autonomous Decision Protocol** (`workflow-reference`). |
| "Any doubt → stop and ask" (`workflow-globals` → Trust mechanism) | Resolve doubt by research: `.ai/principles/*`, `.ai/adr/`, `.ai/memory/*`, then existing codebase patterns, then general best practice. Record what was assumed. |
| `pd-analyze` → "ask clarifying questions, wait for answers" | Do not ask. Resolve each ambiguity by the research order above and record every resolution in `## Task Analysis → ### Assumptions`. |
| `pd-decompose` → "ambiguous boundary → propose options, wait" | Choose the boundary via the Autonomous Decision Protocol; record the rationale in `## Decomposition Decisions`. |
| `pd-design` → "present variants, wait for user choice" | Apply the Autonomous Decision Protocol and record `### Autonomous Decision` in `state.md`. |
| Step 0.3 → "no Acceptance Criteria, continue? (yes/no)" | Do not ask. Note the gap and let `/pd-analyze` derive criteria from the spec. |

**Escalate (pause and wait) only** on the conditions listed in
`workflow-reference → Autonomous Decision Protocol → Step 5`, or on a Guard
failure that would overwrite existing artifacts. A significant-feeling decision
is not by itself grounds to stop.

Guard confirmations that protect existing work (`discovery: complete`,
existing T-XX directories, existing `state-archive.md`) are **not** overridden
in either mode — they always stop and wait.

### Step-by-step mode behavior

After each of Steps 1–4 completes, output:

```
─── STEP <N> COMPLETE — REVIEW REQUESTED ────────────────────
Produced: <artifacts written / sections added>
Key decisions: <one line each, or "none">
Next: Step <N+1> — <child workflow>
─────────────────────────────────────────────────────────────
```

Then **stop and wait**. Continue only on explicit user go-ahead. In this mode
`pd-analyze` asks its clarifying questions and `pd-design` presents variants for
the user to choose — i.e. the original interactive behavior is preserved.

---

## Run Logging

This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

At Step 0, before reading anything, open the run:

Open the run with `log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${WORKFLOWS_SOURCE:+$WORKFLOWS_SOURCE/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-discovery \
  --project "$(pwd)" --task <task-directory> --spec <spec-path> \
  --flow <quick|full, once known> --flags "<flags in force>") || RUN_ID=""
fi
```

Log one `step` line after each of `pd-analyze`, `pd-decompose`, `pd-select-model` (when
run), `pd-design`, `pd-finalize`, and `pd-archive`. Carry `--questions` and `--stops` from
`--step-by-step` interactions, `--decisions` from the `### Assumptions` and
`### Autonomous Decision` records written by the step, `--escalations` when the Autonomous
Decision Protocol hit its threshold, and `--promoted yes` when `pd-analyze` set
`flow: quick` and a later step promoted it. Close with `run-end --outcome completed` when
Step 4 finishes, or `--outcome stopped` with the reason when the phase stops early.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Context Bootstrap

Follow `phase-discovery` rules — ## Context Bootstrap. Load in order, skip missing files.
In multi-repo projects: load umbrella (`../.ai/`) first, then local (`.ai/`) — local overrides.

1. `.ai/memory/architecture.md` — components, constraints, service boundaries
2. `.ai/memory/state.md` — active tasks, blockers, in-flight work
3. `.ai/principles/architecture.md` — architectural patterns, boundaries
4. `.ai/principles/coding.md` — naming, forbidden patterns
5. `.ai/principles/domain.md` — domain rules, ubiquitous language
6. `.ai/adr/index.md` — past decisions index
7. `.ai/memory/progress.md` — only if resuming interrupted work

Conditional (only if task touches external services or environment-specific
setup): `.ai/context/integrations.md`, `.ai/context/environment.md`.

Report: "Discovery context loaded: [files read]"

---

## Step 0 — Bootstrap

0. Parse arguments. Determine execution mode per `## Execution Modes`:
   `--step-by-step` present → step-by-step; otherwise → autonomous.
   Output: `Discovery mode: autonomous — running Steps 1–4 without stopping.`
   or `Discovery mode: step-by-step — pausing for review after each step.`
1. Verify spec file exists. If not — **stop**: "Spec file not found: <path>"
2. Read spec file. Verify H1 heading is present. If missing — **stop**:
   "Spec must have an H1 title. Add `# <Task Title>` as the first heading."
3. Check for `## Acceptance Criteria` section. If absent:
   - **Step-by-step mode** — warn and ask: "No `## Acceptance Criteria` found in
     spec. `pd-analyze` will clarify them interactively. Continue? (yes/no)"
     Wait for answer. Stop if no.
   - **Autonomous mode** — do not ask. Report: "No `## Acceptance Criteria` in
     spec — will be derived in Step 1 and recorded in `### Assumptions`."
     Continue.
4. Derive task directory: `task-` + basename of spec file without extension.
   Example: `01-add-oauth.md` → task directory = `.ai/tasks/todo/task-01-add-oauth/`
   (Multi-phase specs: step 4b may append a `-p<N>` suffix after phase detection.)

4b. **Multi-phase detection** (run after step 4, before step 5):
    a. Look for a `## Phases` manifest section in the spec. If present, treat its
       listed entries as the authoritative phase list.
    b. Else scan the spec for headings matching `^#{2,3}\s+Phase\s+\d+\b`. Count
       distinct matches.
       - **≥2 matches → multi-phase.** Proceed with steps c–f below.
       - 0–1 matches → single-phase: skip the rest of 4b, keep directory name from step 4.
    c. If a manifest lists phases that do not map to corresponding spec sections,
       or if phase boundaries are otherwise ambiguous → **STOP**: "Multi-phase spec
       detected but phase boundaries are ambiguous: <detail>. Clarify before continuing."
    d. Determine target phase N:
       - If `--phase` arg given → use that N.
       - Else → lowest phase number with no existing `task-<basename>-p<N>/` directory
         under `.ai/tasks/todo/` (check all subdirectories, not just `todo/`).
       - If all phases already have task directories → **STOP**: "All phases of <spec>
         already discovered."
    e. Revise task directory to: `.ai/tasks/todo/task-<spec-basename>-p<N>/`
    f. Record spec_phase_count = M (total number of phases detected).

5. Guard — numeric prefix uniqueness check:
   Extract the numeric prefix (digits before first `-`) from the spec filename.
   Scan all files in `.ai/specs/`. If another file has the same prefix → **stop**:
   "Spec prefix collision: <existing-file> and <new-file> share the same numeric
   prefix. Rename one of them to avoid duplicate task directories."
6. Check if task directory already exists:
   - If exists, read `state.md` inside it. Check `## Phases`:
     - `discovery: complete` → "Discovery already complete. Re-running will
       overwrite existing artifacts. Confirm to proceed? (yes/no)" Wait.
     - `discovery: in-progress` → determine resume point (same logic as below),
       output: "Task directory exists. Resuming from Step N."
     - `discovery: not-started` → continue to Step 0.7
   - If does not exist → create it: `mkdir -p <task-directory>`
7. Create or update `state.md` in task directory. At minimum write:

```
spec_path: <path-to-spec>
flow: full

## Phases
- discovery: in-progress
- execution: not-started
- validation: not-started
```

`flow: full` is written here as the default; `/pd-analyze` re-evaluates it against the
`quick-flow` gate in its Step 6b and may set `flow: quick`.

If `state.md` already exists (resume case) — add `spec_path:` line at top if
not already present; update `discovery: in-progress` in `## Phases`.

**Multi-phase only** (detected in step 4b): additionally write `active_phase:`
and `spec_phase_count:` immediately after `spec_path:`, and add a `## Spec Phases`
section. The full top-of-file block becomes:

```
spec_path: <path-to-spec>
active_phase: <N>
spec_phase_count: <M>

## Spec Phases
- phase 1: <complete|deferred|in-discovery> — <title> — <task-dir or "—">
- phase 2: <complete|deferred|in-discovery> — <title> — <task-dir or "—">
- phase M: ...

## Phases
- discovery: in-progress
- execution: not-started
- validation: not-started
```

Status values for `## Spec Phases` lines:
- Active phase N → `in-discovery`
- Phases with no existing task directory → `deferred`
- Phases whose task directory already exists and is complete → `complete`

Single-phase: write only `spec_path:` — do NOT write `active_phase:`,
`spec_phase_count:`, or `## Spec Phases`.

---

## Step 0.5 — Resume Check (if state.md existed)

Read `state.md`. Determine last completed step from explicit markers:
- `## Task Analysis` present → Step 1 done.
- Above + `## Decomposition` with `decomposition: complete` → Steps 1–2 done.
- Above + `## Solution Design` with `### Decision` → Steps 1–3 done.
Output: `Discovery partially complete. Completed: Steps [list]. Continuing from Step N.`

---

## Execution

Run child workflows in order, skipping already completed steps.
**Pass task directory (not spec path) as the argument to all child workflows.**
**Append `--step-by-step` to every child invocation when in step-by-step mode.**

1. Call `/pd-analyze <task-directory>` — Task analysis + codebase examination. This step
   sets `flow:` (see the `quick-flow` rule).
2. Call `/pd-decompose <task-directory>` — Decomposition into T-XX subtasks
3. Call `/pd-design <task-directory>` — Architectural design (2–3 variants)
4. Call `/pd-finalize <task-directory>` — Finalization + compress

**Flow-tier branch (read `flow:` from `state.md` after Step 1).** If `flow: quick`,
**skip Steps 2 and 3** — a quick task has no T-XX decomposition and no variant design; its
`## Contract (quick)` was written by `/pd-analyze`. Go straight to Step 4 (`/pd-finalize`,
which also skips `/pd-archive` when there is nothing verbose to archive). If `flow: full`,
run Steps 2–4 unchanged. The gate and the quick contract requirements are defined in the
`quick-flow` rule.

**Autonomous mode — continuation rule (this is the default and it is mandatory):**
A child workflow's closing `Report: "Step N complete."` is a progress marker, not
a handoff. The moment a child reports completion, immediately invoke the next
child in the same turn. Do not summarize and wait, do not ask "shall I continue?",
do not return control to the user for any reason other than a genuine escalation
(see `## Execution Modes`). The phase is one continuous run from Step 1 through
Step 4; the only planned stop is the final report below.

**Step-by-step mode:** after each child completes, emit the review block from
`## Execution Modes → Step-by-step mode behavior` and wait for go-ahead.

If any child workflow encounters a hard blocker or a Guard confirmation — stop
and report to the user before continuing, in either mode.

After all steps complete, report to the user (display as text — do NOT invoke):
- Path to `state.md` — full analysis and chosen solution.
- Path to `plan.md` — subtask list with dependencies.
- **Autonomous mode only** — a review digest so the user can audit what was
  decided without them: chosen architecture in one line, the `### Autonomous
  Decision` winner and score, and every entry from `### Assumptions`. Follow it
  with: "Decisions were made autonomously. Re-run with `--step-by-step` to
  review each step interactively."
- "Discovery complete. Run `/phase-execution <task-directory>` to start execution."

**STOP. Do not run `/phase-execution` automatically.**
