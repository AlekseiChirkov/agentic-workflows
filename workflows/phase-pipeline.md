---
description: Fully autonomous pipeline — runs Discovery → Execution → Validation in a single session without manual phase transitions
---

Path to spec or task directory: $ARGUMENTS

You are executing the **phase-pipeline** — a fully autonomous pipeline that runs Discovery → Execution → Validation in a single continuous session without manual phase transitions.

---

## Run Logging

This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

At Step 0, open **one** run for the whole pipeline:

Open the run with `log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${WORKFLOWS_SOURCE:+$WORKFLOWS_SOURCE/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-pipeline \
  --project "$(pwd)" --task <task-directory> --spec <spec-path> --flow <quick|full>) || RUN_ID=""
fi
```

Do not open a second run when this pipeline invokes `/phase-discovery`,
`/phase-execution`, or `/phase-validation` — pass `RUN_ID` down and keep every step in one
file, so a pipeline run reads as a single timeline. Log a `step` line for each child
workflow, and additionally one line per **pipeline override actually exercised**
(`--step override:pv-issues --decisions 1`), because the whole point of measuring this
pipeline is learning which overrides fire and what they cost. Close with `run-end
--outcome completed`, or `--outcome stopped` naming the declared stop that ended it.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Pipeline Overrides

These rules override the corresponding rules in `workflow-globals` for this command only. All other global rules remain in full force.

| Overridden rule | Pipeline behavior |
|---|---|
| "Never auto-advance between phases" | **Auto-advance**: after each phase completes, continue to the next immediately. |
| "Architectural choice → present options, wait for user" | **Use Deep Architectural Analysis Protocol** (defined below) to decide independently. |
| "pv-issues → wait for user to approve/defer issues" (`pv-issues` step 4) | **Auto-decide**: fix all `critical` and `important` issues; defer `optional` ones. |
| "pav-propose → wait for user approval of Do Now items" (`pav-propose` step 4) | Not reached: the pipeline always passes `--batch`, which **records and applies nothing**. The proposals are applied later, at `pe-finalize` step 5 below. |
| "pe-finalize step 5 → **Wait for user choice**" on batched `Do Now` items | **Auto-choose option 2** — apply them now, before validation — and record the automatic choice in `state.md`. This is where the pipeline applies what `--batch` deferred. |
| "pe-execute / pv-execute-fixes → at any blocker or ambiguous situation … wait for user's choice" | **Ambiguity**: resolve with the Deep Architectural Analysis Protocol and record it in the subtask's `notes:`. **Blocker**: escalate per the list below — a blocker is not an ambiguity. |
| "pd-analyze step 3 → ask clarifying questions, **wait for answers**" | Not reached: `pd-analyze` asks only under `--step-by-step`, which the pipeline never passes. Ambiguities are resolved by its research order and recorded in `### Assumptions`. |
| "pd-decompose step 2 → >8 subtasks / ambiguous boundary, present options and wait" | Not reached for the same reason: `pd-decompose` pauses only under `--step-by-step`; autonomously it resolves the same options via the Autonomous Decision Protocol and records the choice in `## Decomposition Decisions`. |
| "compress-state step 2 → **wait for user confirmation**" | Not reached: every invocation in this pipeline is `/compress-state --auto`, which proceeds without waiting. Never call it without `--auto` from an autonomous run. |
| "phase-composite-validation step 2 → present integration failures and **wait for the user's decision**" | **Auto-decide**, exactly as for `pv-issues`: approve every `critical` and `important` failure as a fix sibling, defer every `optional` one, and record in `## Integration Issues (T-XX)` that the split was automatic. |

Every override is registered in `workflow-globals → Workflow-declared mode overrides`, which is
the canonical registry; this table is the detail, not a second source of truth.

**Autonomous means no *planned* stops** — the pipeline never stops for a decision it is able to
make. It still stops on the conditions below, and those stops are deliberate.

**Escalate to user (pause and wait) ONLY when:**
- A hard blocker appears that cannot be resolved without external information (missing secret, unavailable external service, missing requirement with no reasonable default).
- A decision would change an external API contract already consumed by clients in a breaking way.
- Two or more variants score identically on all 5 lenses AND have fundamentally different user-visible trade-offs that cannot be resolved by the simplicity tie-breaker.
- A requirement is genuinely ambiguous **and** survives the `pd-analyze` research order (principles → ADRs → memory → codebase patterns → best practice) with no reasonable default (ask — wrong requirements waste all three phases).

All other ambiguities → resolve using the Deep Architectural Analysis Protocol.

### Declared stops — steps this pipeline does NOT override

These are the only places a `/phase-pipeline` run stops. Each is reserved for a human by
contract, so none of them is a defect in the autonomy claim:

| Step that stops | Why it is not overridden |
|---|---|
| `pv-contract` step 7 — critical-failure gate (a `FAIL` Invariant or Off-limits entry) | A violated invariant is reserved for the human by `orchestration → ## Conditions that always stop the run`. |
| `pae-implement` — a step touching `### Scope → #### Out` | Same rule: an Off-limits / out-of-scope breach is never auto-approved. |
| `pae-implement` — composite-promotion tripwire | Reserved for the human; the arbiter has no authority to approve a promotion. |
| `pae-tests` — `atomic-tests: failed` (RED never established) | `tdd` and `workflow-globals → Test-first execution`; no autonomous mode suspends the test-first rule. |
| `pae-implement` / `phase-atomic-execution` — an unresolved blocker | A hard blocker, per the escalation list above. |
| `pe-finalize` step 2b — a composite whose children are all reviewed while `integration-validation: failed` | The integration fix cycle is still open. Reachable autonomously when every integration failure was `optional` and therefore auto-deferred, so it is a declared stop, not an override gap. |
| Any `## Guard` confirmation that would overwrite existing artifacts | `workflow-globals`: Guard confirmations are never suspended by a mode override. |
| `workflow-globals → Never auto-advance between phases`, at the end of the run | The pipeline auto-advances *between its own three phases* only; it never starts a fourth. |

---

## Deep Architectural Analysis Protocol

Canonical definition: `workflow-reference → ## Autonomous Decision Protocol`
(6 steps: generate variants → score on 5 lenses → anti-overengineering filter →
select winner → check escalation threshold → document `### Autonomous Decision`
in `state.md`). Load it and follow it verbatim.

Use it whenever an architectural or design choice is required — it replaces
"present options, wait for user" in `pd-design` and at any ambiguous decision
point during execution.

**Pipeline-specific addition:** at the protocol's Step 5, apply the escalation
conditions from "Pipeline Overrides" above *in addition to* the protocol's own.
When escalation applies → pause, show the scored table, explain the blocker,
wait for the user.

---

## Step 0 — Bootstrap

1. Read `workflow-globals` fully.
   Confirm: "Global rules loaded." before proceeding.
   If file not found: stop and report path error.
2. Verify `$ARGUMENTS` is provided. If not — ask for path to spec
   (`.ai/specs/*.md` for new tasks) or task directory (`.ai/tasks/todo/<task>/`
   for resuming).

   Determine input type from $ARGUMENTS:
   a. If argument ends with `.md` and path starts with `.ai/specs/` →
      treat as spec path (new task). Do **not** derive the task directory here.
      **Run `phase-discovery` Step 0 in full (its steps 1–7) and adopt the task directory it
      produces** — it is the single definition of that name, and it includes the two things a
      simplified derivation drops:
      - **Step 0.4b — multi-phase detection.** A spec with ≥2 `Phase N` markers (or a
        `## Phases` manifest) gets a `-p<N>` directory suffix, `active_phase:`,
        `spec_phase_count:`, and a `## Spec Phases` section
        (`workflow-reference → ## Multi-Phase Spec Rules`). Without it the pipeline
        discovers a whole multi-phase spec as one unphased task and no deferred-phase
        bookkeeping is ever written.
      - **Step 0.5 — the numeric-prefix collision guard**, which stops on two specs sharing a
        numeric prefix.
      Run it in autonomous mode: the pipeline never passes `--step-by-step`, so Step 0.3 does
      not ask about missing Acceptance Criteria. Step 0.6's Guard confirmations are **not**
      overridden — `## Pipeline Overrides` above does not list them, and `workflow-globals`
      forbids suspending them.
   b. If argument is a directory path → treat as task directory (resume or
      post-discovery run).
   c. If argument ends with `.md` and is inside `.ai/tasks/` → legacy mode:
      task directory = parent directory of the argument.
3. Read `state.md` in the task directory (if it exists). Determine pipeline resume point from `## Phases`:
   - `discovery: not-started` or absent → start from Discovery.
   - `discovery: in-progress` → resume Discovery from last completed step.
   - `discovery: complete`, `execution: not-started` → skip to Execution.
   - `execution: in-progress` → resume Execution from first incomplete subtask.
   - `execution: complete`, `validation: not-started` → skip to Validation.
   - `validation: in-progress` → resume Validation from last completed step.
   - All three `complete` → report "Pipeline already complete." Stop.

Output resume point before proceeding:
```
Pipeline resume point: <Phase N — Step M / starting fresh>
```

---

## Phase 1 — Discovery

Read global rules (loaded in Step 0) continue/never-restart rules. Then execute child workflows in order, skipping completed steps as determined in Step 0.

**Child workflow files:**
- `/pd-analyze` → `pd-analyze.md`
- `/pd-decompose` → `pd-decompose.md`
- `/pd-design` → `pd-design.md`
- `/pd-finalize` → `pd-finalize.md`
- `/compress-state` → `compress-state.md`

**Execution:**
1. Read and follow `pd-analyze.md` inline in its default (autonomous) mode —
   ambiguities are resolved by the research order defined there and recorded in
   `## Task Analysis → ### Assumptions`. Ask the user only when an ambiguity
   survives that research and meets the escalation threshold (a requirement with
   no reasonable default that would invalidate all three phases).
2. Read and follow `pd-decompose.md` inline.
3. Read and follow `pd-design.md` inline, **replacing** the "present variants, wait for user choice" step with the **Deep Architectural Analysis Protocol** above.
4. Read and follow `pd-finalize.md` inline.

After Discovery completes, output:
```
─── DISCOVERY COMPLETE ──────────────────────────────────────
Architecture: <one-line summary of chosen approach>
Subtasks: <N> × T-XX
Auto-advancing to Phase 2 — Execution…
─────────────────────────────────────────────────────────────
```

---

## Phase 2 — Execution

Read and follow `phase-execution.md` inline.

**Child workflow files:**
- `/pe-execute` → `pe-execute.md`
- `/pe-finalize` → `pe-finalize.md`
- `/phase-atomic-execution` → `phase-atomic-execution.md`
- `/phase-atomic-validation` → `phase-atomic-validation.md`
- `/pae-tests` → `pae-tests.md`
- `/pae-implement` → `pae-implement.md`
- `/pae-finalize` → `pae-finalize.md`
- `/pav-check` → `pav-check.md`
- `/pav-propose` → `pav-propose.md`
- `/pav-close` → `pav-close.md`
- `/phase-composite-validation` → `phase-composite-validation.md` (reached through `/pav-close` step 5 when the last child of a composite closes — never invoked directly)
- `/compress-state` → `compress-state.md`

**Execution overrides during this phase:**
- At any ambiguous situation that is NOT a hard blocker → apply the **Deep Architectural Analysis Protocol** and decide independently. Document decision in the T-XX `## Subtask Progress → notes` field.
- `pae-tests` review gate → run in batch mode: record the AC→test digest in `notes:` and continue without waiting. **The step itself is never skipped** — the test-level gate is decided by the classifier in the `tdd` rule, not by the Deep Architectural Analysis Protocol, and `none` still requires its justification line. Autonomy licenses unblocked decisions, not untested code.
- Hard blockers (missing external info, invariant conflict with no valid resolution) → escalate per the escalation threshold above.
- `pav-propose` runs with `--batch` (passed down by `pe-execute` step 2d): every proposal is
  **recorded and none is applied**. The `Do Now` items are applied at `pe-finalize` step 5,
  which the pipeline auto-answers with option 2. Do not reinterpret `--batch` as
  apply-without-asking — its meaning is fixed in `workflow-globals`.
- `pe-finalize` step 5 → do not wait: choose option 2 (apply now, before validation) and record
  that the choice was automatic.

After Execution completes, output:
```
─── EXECUTION COMPLETE ──────────────────────────────────────
Completed: <N> subtasks
Blocked / deferred: <M> subtasks
Auto-advancing to Phase 3 — Validation…
─────────────────────────────────────────────────────────────
```

---

## Phase 3 — Validation

Read and follow `phase-validation.md` inline.

**Child workflow files:**
- `/pv-contract` → `pv-contract.md`
- `/pv-review` → `pv-review.md`
- `/pv-issues` → `pv-issues.md`
- `/pv-create-fixes` → `pv-create-fixes.md`
- `/pv-execute-fixes` → `pv-execute-fixes.md`
- `/pv-finalize` → `pv-finalize.md`
- `/phase-atomic-execution` → `phase-atomic-execution.md`
- `/phase-atomic-validation` → `phase-atomic-validation.md`
- `/pae-tests` → `pae-tests.md`
- `/pae-implement` → `pae-implement.md`
- `/pae-finalize` → `pae-finalize.md`
- `/pav-check` → `pav-check.md`
- `/pav-propose` → `pav-propose.md`
- `/pav-close` → `pav-close.md`
- `/compress-state` → `compress-state.md`

**Execution overrides during this phase:**
- `pv-issues` "wait for user" step → **skip the wait**. Instead, automatically approve all `critical` and `important` issues as fix-tasks. Automatically defer all `optional` issues. Write the `## Issue List → Approved / Deferred` sections accordingly.
- `pav-propose` inside the fix cycle → `--batch`, same single meaning: recorded, not applied.
  The Validation phase has no post-phase review step to apply them in, so `Do Now` items raised
  against a fix-task are left recorded in `## Improvement Proposals (T-XX)` and listed in the
  Final Report. This is a declared outcome, not an oversight: an improvement proposed on top of
  a fix is new work, and the pipeline does not silently widen its own scope at the last step.

---

## Final Report

After all three phases complete, output:

```
═══ PIPELINE COMPLETE ═══════════════════════════════════════
Task: <path to description.md>

Discovery:  complete — <architecture one-liner>
Execution:  <N> subtasks complete, <M> blocked/deferred
Validation: <N> issues found → <N_fix> fixed, <N_defer> deferred

State:  <path>/state.md
Plan:   <path>/plan.md
ADR:    .ai/adr/<NNNN-task-ID-short-title>.md (index: .ai/adr/index.md)
═════════════════════════════════════════════════════════════
```

---

## Interruption Recovery

If the pipeline is interrupted mid-run, re-run `/phase-pipeline <same-path>`. Step 0 will read `state.md`, identify the resume point from `## Phases` and `## Subtask Progress`, and continue from exactly where work stopped.
