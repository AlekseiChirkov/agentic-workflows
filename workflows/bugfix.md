---
description: Governed entry point for a defect — reproduce, freeze the reproduction as a failing test, fix, verify, record
---

Invocation: `/bugfix "<defect description, URL, or file>" [--auto-mode] [--no-repro]`
Resolve paths from the current project root. This standalone workflow completes a
quick-eligible defect lifecycle; a full-tier verdict hands over before implementation.

`--auto-mode` resolves unblocked choices through
`workflow-reference → ## Autonomous Decision Protocol` and records the rationale in state.
Without it, ask about unresolved intent. Neither mode overrides the quick gate, test-first
contract, validation stops, or confirmations for overwriting completed work.

## Guard

1. Load the project principles, architecture and current-state memory, ADR index and
   runbook; load integrations only when relevant. Use umbrella before local context.
2. Resolve input through `spec-draft → ## Step 0 — Resolve the input` without running
   specification authoring. If input is unavailable → **stop**: request the missing report.
3. Look for a matching `kind: bugfix` task in `.ai/tasks/todo/` and `.ai/tasks/completed/`
   using its recorded defect
   source and description. Resume its first incomplete step from state; do not allocate a
   duplicate. If several match → **stop**: request the task to resume. A completed matching
   fix is reported; do not redo it without an explicit request.
4. For a new report, create `.ai/tasks/todo/fix-<NN>-<slug>/` with a unique number and domain
   slug. Record the defect source and expected behavior in `state.md`, in English.

## Run logging

Follow `run-log`: open at Step 0 with `--pipeline bugfix`, record completed step boundaries,
then close on completion or a declared stop. Logging failure never blocks work.

## Step 0 — Resolve the defect

For a new task initialize state; for a resumed task preserve existing evidence:

```text
flow: full
kind: bugfix

## Phases
- discovery: in-progress
- execution: not-started
- validation: not-started
```

`full` is the safe initial value; Step 2 sets `quick` only after all gate conditions pass.
Record completed steps in state for resume.

## Step 1 — Reproduce

**No fix is written before the defect is reproduced.** Find the smallest failing input
and run the relevant system/test command. Record:

```text
## Reproduction
trigger: <minimal input or sequence>
observed: <actual behavior>
expected: <correct behavior and its source>
verified_by: <exact command run>
```

If it does not reproduce → **stop**: report attempts and request the missing environment,
data, timing, or version. Do not claim a fix based on an unobserved defect.

`--no-repro` applies only to defects without runtime behavior, such as a wrong comment or
literal copy. Write `skipped: <specific justification>` under `## Reproduction`. It never
licenses skipping because reproduction is difficult or only possible in production.

## Step 2 — Diagnose and write the contract

1. Identify the cause as `path:line`, affected callers and persisted/cached data. If the
   requested behavior never existed, **stop**: report the missing feature and print
   `/spec-draft "<request>"` for the user.
2. Evaluate `quick-flow → ## The escalation gate` against the complete affected surface,
   including tests and any data correction. Record every result:

```text
## Contract (quick)

### Gate
1. files (incl. tests): <N> → <pass|fail>
2. new invariant: <yes|no> → <pass|fail>
3. behaviour change to a shipped pipeline: <yes|no> → <pass|fail>
4. schema change / migration: <yes|no> → <pass|fail>
verdict: quick | full

### Off-limits
<boundaries>
### Invariants
<existing invariants to preserve>
### Acceptance Criteria
- [ ] <expected result, given/when/then>
- [ ] <named adjacent behavior remains correct>
```

A defect fix often changes shipped behavior and therefore fails condition 3. When any
condition fails, set `flow: full`; this workflow **stops** and hands over. Preserve the
reproduction and diagnosis, and print `/spec-draft "<defect>" --auto-mode` followed by
`/phase-discovery <resulting-spec>`. Run neither command automatically.

Only with all four passes, set `flow: quick` and `discovery: complete`, then
`execution: in-progress`. Recheck the gate when scope grows; on breach follow
`quick-flow → ## Mid-flight escalation (quick → full)` and stop this quick lifecycle.

## Step 3 — RED: freeze the reproduction as a test

Follow `tdd` and `quick-flow → ## The quick path — what changes`: the reproduction *is*
the RED test. Classify the test level, assert expected behavior, run it and observe failure
for the defect's reason. Record the canonical `## TDD (quick)` fields, test paths and
command/output summary in state. Preserve the frozen test set through implementation.

`--no-repro` does not choose test level `none`. Evaluate the same test-level gate; use
`none` only with its required written justification. Keep `atomic-tests: red` or `n-a`
when present, consistent with the canonical quick TDD evidence.

## Step 4 — GREEN: fix

Fix the diagnosed cause and run the frozen tests plus affected regression checks. For
justified `level: none`, inspect the corrected artifact and run applicable existing checks;
record that evidence instead of claiming a nonexistent test pass. Handle
persisted bad data explicitly within the accepted gate/scope. Record results and
`target_files:` under `## TDD (quick)`; mark `green-observed` only after an observed pass.
If `atomic-tests:` exists, change `red` to `green`; preserve `n-a` for justified `none` work.
Set `execution: complete` only after verification passes, then `validation: in-progress`.

## Step 5 — Verify and record

1. Re-run the reproduction command unless its skip was justified. Record the observed
   expected outcome; for non-runtime work inspect the corrected artifact instead.
2. Run applicable lint/build commands from the runbook.
3. Run `/pv-contract <task-directory>` and `/pv-review <task-directory>` against the inline
   contract. Honor their stops. Present findings and record repair/defer choices before
   repair; `--auto-mode` may approve in-scope critical/important repairs and defer optional
   items, recording its rationale. Repair approved items inline within the quick gate
   and rerun affected checks. Unresolved failed criteria or critical/important findings prevent
   completion; do not silently treat them as deferred.
4. Apply the ADR trigger in `pv-finalize → ## Instructions`, step 3. If triggered, record
   the explicit decision in state and run `/adr-new <task-directory>`.
5. Set `validation: complete`. Update the project-memory entry using
   `workflow-reference → ## .ai/memory/state.md Entry Format` and append one progress entry
   with the defect, cause, fix and verification evidence. Move the task directory to
   `.ai/tasks/completed/` only after all required checks pass.

## Step 6 — Report

Report cause (`path:line`), fix, test/`none` evidence, gate and validation verdicts, ADR
and unresolved follow-up. Then **stop**. This workflow
never commits, pushes or opens a pull request; print follow-up commands as plain text.
