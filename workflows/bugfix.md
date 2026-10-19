---
description: Governed entry point for a defect — reproduce, freeze the reproduction as a failing test, fix, verify, record; the light path that is still inside the process
---

Invocation: `/bugfix "<defect description>" [--auto-mode] [--no-repro]`
Examples:
- `/bugfix "forex report shows stale rate after cache expiry"`
- `/bugfix https://sentry.example.com/issues/44821 --auto-mode`
- `/bugfix "typo in the confirmation email subject" --no-repro`

---

## Why this exists

A production defect had exactly two paths before this workflow: write a full spec and run
Discovery — too heavy, so it rarely happened — or fix it outside the pipeline entirely.
The second is what actually occurred (`quick-flow → ## The escalation gate`, the 2026-07-22
case: four behaviour changes to a shipped pipeline with no contract, no `pv-contract`, and
no ADR). This workflow is the third path: lighter than Discovery, and governed unlike an
ad-hoc fix.

**What it does not do.** It does not replace `/phase-discovery` for defects that turn out to
be missing features, and it does not skip the test-first rule. `workflow-globals →
Test-first execution` holds here without exception: the reproduction *is* the RED test.

---

## Run logging

Follow the **`run-log`** rule. Open the run at Step 0 with `--pipeline bugfix`, log one
`step` line per numbered step below, and close with `run-end`. Logging never blocks the fix.

---

## Step 0 — Resolve the defect

1. Classify the input exactly as `spec-draft → ## Step 0` does: URL → fetch and extract;
   file path → read; anything else → treat as the literal defect report. A URL that cannot
   be fetched → **stop** and ask for the description.
2. Load context: `.ai/principles/*`, `.ai/memory/architecture.md`, `.ai/adr/index.md`,
   `.ai/context/runbook.md` (required — the `test:` command), and
   `.ai/context/integrations.md` if the defect involves an external service. Umbrella
   first in multi-repo.
3. Create the task directory `.ai/tasks/todo/fix-<NN>-<slug>/` and write `state.md`:

```
flow: quick
kind: bugfix

## Phases
- discovery: complete
- execution: not-started
- validation: not-started
```

`discovery: complete` is correct and deliberate: Steps 1–2 below *are* the discovery for a
defect, and they finish before any code is touched. `kind: bugfix` marks the task so
`/retro` can separate defect work from feature work.

---

## Step 1 — Reproduce

**No fix is written before the defect is reproduced.** This is the step the ad-hoc path
skips, and it is the reason ad-hoc fixes so often address a symptom.

1. Determine the smallest input that triggers the defect: the failing request, the record
   that renders wrong, the sequence that corrupts state.
2. Reproduce it by running the system — the `test:` or run command from the runbook, a
   targeted script, or a direct call. Observe the wrong behaviour with your own eyes.
3. Record in `state.md`:

```
## Reproduction
trigger: <the smallest input that produces the defect>
observed: <what actually happens>
expected: <what should happen, and what makes that the correct expectation>
verified_by: <the exact command run>
```

**If it does not reproduce → stop.** Report what was tried and what happened instead. A
defect that cannot be reproduced cannot be verified as fixed, and "fixed" would be a guess.
Ask the human for the missing condition — environment, data, timing, version.

`--no-repro` skips this step and is legitimate **only** for a defect with no runtime
behaviour: a typo in a literal, a wrong comment, a stale doc string. It is not legitimate
for "hard to reproduce", "only happens in production", or "I can see the bug in the code".
The first is a finding to report; the last two are exactly the cases where reproduction
matters most. When `--no-repro` is used, write `## Reproduction` with `skipped: <the
justification>` — an unjustified skip is a validation finding.

---

## Step 2 — Diagnose and write the contract

1. Find the cause, not the symptom. Name the file and line where the wrong behaviour
   originates, and explain why the code produces it. A fix at a different layer than the
   cause needs a stated reason.
2. Determine the blast radius: what else calls this code, what else relies on the current
   (wrong) behaviour, whether anything has cached or persisted the wrong result. Persisted
   bad data is its own subtask, not a footnote.
3. Run the four **`quick-flow`** gate conditions and record every result:

```
## Contract (quick)

### Gate
1. files (incl. tests): <N> → <pass|fail>
2. new invariant: <yes|no> → <pass|fail>
3. behaviour change to a shipped pipeline: <yes|no> → <pass|fail>
4. schema change / migration: <yes|no> → <pass|fail>
verdict: quick | full

### Off-limits
### Invariants
### Acceptance Criteria
- [ ] <the reproduction from Step 1 no longer reproduces — stated as Given/When/Then>
- [ ] <no adjacent behaviour changed — name what was checked>
```

**Condition 3 is the one that matters here and it usually fails.** A defect fix *is* a
behaviour change to a shipped pipeline in most cases — that is what a bug fix is. When the
verdict is `full`, this workflow **stops** and hands over:

> "This fix changes shipped behaviour / touches N files / requires a migration. It runs the
> full path. Run: `/spec-draft "<defect>" --auto-mode` then `/phase-discovery <spec>`."

Do not carry on because the fix "feels small". The gate is a checklist, not a judgement
call, and this is the exact failure mode the workflow exists to prevent.

---

## Step 3 — RED: freeze the reproduction as a test

Follow **`tdd`** in full. The test level is classified by the gate in `tdd → ## Test-level
gate`, and for a defect the reproduction dictates it: whatever layer reproduces the bug is
the layer the test belongs to.

1. Write a test that asserts the **expected** behaviour from `## Reproduction`.
2. Run it. It must fail, and it must fail **for the defect's reason** — the observed wrong
   value, not an import error or a typo in the test. A regression test that passes before
   the fix is not testing the defect; find out why and correct the test.
3. Record `atomic-tests: red` and the test file in `state.md`.

The RED test is frozen from this point. It is not edited, skipped, or weakened to make the
fix easier — `tdd` governs, without exception.

`--no-repro` work carries `atomic-tests: n-a` with the justification line required by `tdd`.

---

## Step 4 — GREEN: fix

1. Fix the cause identified in Step 2. Smallest change that makes the RED test pass.
2. Run the full test suite for the affected modules, not only the new test. A fix that
   greens its own test and reds another is not a fix.
3. If the blast radius from Step 2 included persisted bad data, handle it explicitly —
   either a correction step, or a recorded decision that existing bad data is left alone
   and why. Silently leaving corrupted state is the most common incomplete bug fix.
4. Record `atomic-tests: green`, `target_files:`, and what was run.

---

## Step 5 — Verify and record

1. Verify each Acceptance Criterion from Step 2 against the running system, not against the
   diff.
2. Re-run the original reproduction command from `## Reproduction → verified_by`. It must
   now show the expected behaviour. Record the output's verdict in `## Contract Check`.
3. Run lint/build from the runbook if defined.
4. **ADR check.** Apply the same trigger as `pv-finalize → ## Step 3`. A defect fix earns an
   ADR when the *cause* was a design decision rather than a slip — a wrong boundary, a bad
   caching strategy, an error-handling approach that could not work. A typo does not.
   When it triggers → run `/adr-new <task-directory>`.
5. Append a `progress.md` entry: the defect, the cause, the fix, the test that now guards it.
6. Move the task directory to `.ai/tasks/completed/`.

---

## Step 6 — Report

Print: the cause (file:line), the fix, the test that guards it, the gate verdict, whether an
ADR was written, and anything deliberately left alone with its reason.

Then **stop**. Print any follow-up command as plain text. This workflow never commits,
never pushes, and never opens a pull request — use `/suggest-commit-message` and the normal
git flow.

---

## What this workflow never does

- Fix without reproducing (except a justified `--no-repro`).
- Write the fix before the failing test.
- Continue when the quick gate returns `full`.
- Edit, skip, or weaken the RED test to reach green.
- Treat a missing feature as a defect. If Step 2 finds the behaviour was never implemented,
  stop and say so — that is a spec, not a bug.
