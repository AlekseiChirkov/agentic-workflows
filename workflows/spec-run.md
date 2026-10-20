---
description: Orchestrator — carry one spec from Discovery to review-ready pull requests, one stacked branch per subtask, using context-bounded sub-agents
---

Invocation: `/spec-run <path-to-spec> [--allow-pr] [--dry-run]`
Examples:
- `/spec-run .ai/specs/01-add-oauth.md` — full run, all work stays local
- `/spec-run .ai/specs/01-add-oauth.md --allow-pr` — also push branches and open draft PRs
- `/spec-run .ai/specs/01-add-oauth.md --dry-run` — print the plan, change nothing

You are the **Orchestrator**. Load `orchestration` and `git-flow` in full before Step 0 —
they define the roles, the escalation protocol, and every git rail this workflow obeys.

**Flags:**
- `--allow-pr` — authorizes pushing branches and opening draft pull requests. Without it, no
  `git push` and no `gh` command runs at any point; the stack exists only locally.
- `--dry-run` — prints preflight results, the resolved subtask order, and the branch stack
  that would be created. Creates no branch, writes no commit, opens no PR. Discovery is not
  run; if Discovery has not happened yet, the plan is reported as "unknown until Discovery".

Single repository only. A spec covers exactly one repo — cross-repo work is split into
separate specs.

---

## Run Logging

This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

At Step 0, after preflight passes and the resume point is known, open the run:

Open the run with `log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline spec-run \
  --project "$(pwd)" --task <task-directory> --spec <spec-path> \
  --flags "<--allow-pr / --dry-run as passed>") || RUN_ID=""
fi
```

The Orchestrator owns every log call, exactly as it owns every shared file — a sub-agent
never calls `log-step.sh`. This keeps the shared-file discipline in `orchestration` intact
and keeps `seq` monotonic.

Log a `step` line after each of Steps 1–8, plus one per subtask inside the Step 4 loop
(`--step subtask --subtask T-XX --tests <atomic-tests value> --gate <validator verdict>`).
The batch gate gets its own line — `--step batch-gate --stops 1 --questions N` — because
the number of class-B questions per run is the single most useful number this pipeline
produces. On `--dry-run`, log `run-start`, one `--step dry-run --outcome skipped` line, and
`run-end --outcome completed`; write nothing else. Close with `run-end --outcome
completed`, `stopped`, or `failed`.

Logging is best-effort: if `$LOG_HELPER` is missing or a call fails,
continue unchanged and mention it once in the final report. Never stop, retry, or ask the
user because of a log write.

---

## Step 0 — Preflight and resume

1. Run the full preflight checklist from `git-flow → ## Preflight`. Any failure → report
   which check failed and **stop**.
2. Resolve the task directory from the spec path exactly as `/phase-discovery` does
   (`task-` + spec basename, plus `-p<N>` for multi-phase specs).
3. If the task directory exists, read `state.md` and determine the resume point:
   - `## Phases → discovery` not `complete` → resume at Step 1.
   - discovery complete, some subtasks not `reviewed` → resume at Step 4, at the first
     subtask that is not `reviewed`.
   - all subtasks `reviewed`, `validation` not complete → resume at Step 5.
   - everything complete → report and stop.
4. **Reconcile git against state.** For each subtask with a recorded `branch:`, verify the
   branch still exists and its tip matches the last sha in `commits:`. Report any divergence
   and **stop** — a branch that moved underneath the recorded state means someone worked on it
   manually, and continuing would silently build on an unknown base.
5. Report the resume point, the flags in force, and whether PRs will be opened.

If `--dry-run` → print preflight result and the plan from Step 3 (or "unknown until
Discovery"), then **stop**.

---

## Step 1 — Discovery, with the batch gate

Run Discovery in its autonomous mode by invoking the child workflows in order —
`/pd-analyze`, `/pd-decompose`, `/pd-design`, `/pd-finalize` — passing the task directory.
Do not pass `--step-by-step`.

Two orchestrated-mode differences, both defined in `orchestration → ## Escalation protocol`:

- **Class A** ambiguities are resolved as usual and recorded in
  `## Task Analysis → ### Assumptions` with their source.
- **Class B** ambiguities are **not** resolved. `/pd-analyze` collects them into
  `state.md → ## Open Questions (batch)`.

Spawn the **Arbiter** before Discovery finishes and keep it alive for the whole run. Give it
the spec, `state.md`, `plan.md`, and the full `.ai/` context. Address it by message for the
rest of the run rather than re-spawning it.

### The batch gate — the only planned human stop

After `/pd-finalize`, read `## Open Questions (batch)`.

- **Empty** → report "No open questions. Proceeding to execution." and continue.
- **Non-empty** → present every question as one list. For each: the question, why it is not
  answerable from the artifacts, 2–3 options with consequences, and the Arbiter's
  recommendation. Then **stop and wait**.

Write the human's answers into `### Assumptions` (one line each, source: `user`), clear
`## Open Questions (batch)`, and only then continue.

This gate runs before any branch is created — that is the whole point of harvesting class-B
ambiguities during Discovery. Nothing has been built yet, so an answer that changes the
design costs nothing but a re-run of decomposition. The same answer arriving during Execution
would invalidate every branch already stacked on top of the wrong assumption.

---

## Step 2 — Model selection

Run `/pd-select-model <task-directory>` in bulk mode. It writes the `Model` column into
`plan.md → ## Subtasks`. Use that column when spawning the Implementer for each subtask.

If the column is absent or a row is blank, spawn with the session default and note it.

---

## Step 3 — Resolve the stack

Read `plan.md → ## Subtasks`. Build the execution order exactly as `/pe-execute` does:
topological order over `Depends On`, honouring any ordering policy in `## Execution Strategy`.
Composite rows are containers — they get no branch and no agent; their children appear in the
order as ordinary leaves.

Derive the branch stack per `git-flow → ## Branch model`: subtask N branches from the tip of
subtask N-1, with subtask 1 branching from the repository default branch.

Print the plan before executing:

```
Stack plan — <spec title>
  <base>
  └── feat/oauth-token-schema      model: <model>   (T-01)
      └── feat/oauth-token-service model: <model>   (T-02, depends T-01)
          └── feat/oauth-login-route  model: <model>   (T-03a, child of composite T-03)
PRs: draft on creation, promoted to ready after validation | not created (no --allow-pr)
```

Subtask identifiers appear in this plan and in `state.md` because both are local and
untracked. They never reach a branch name, a commit, or pull request text — see
`git-flow → ## Pipeline identifiers stay out of the repository`.

---

## Step 4 — Subtask loop

For each subtask in order. Never start N+1 before N is `reviewed`.

**4.1 Branch.** Derive the branch name from the subtask's `## Goal` as `<type>/<feature-slug>`
in domain language — never from its identifier (`git-flow → ## Branch model`). Create it from
the current tip and check it out.
Immediately record in the subtask's `## Subtask Progress` block: `branch:`, `base_branch:`,
and `base_commit:` (the sha of the branch point — `git rev-parse HEAD` before any work).
`base_commit` is written once and never recomputed.

**4.2 Implementer — one agent, two checkpoints.** Spawn a fresh sub-agent with the model from
Step 2. Give it: the path to `T-XX/description.md`, the resolved `WORK_DIR`, the branch name,
and the instruction to run `/pae-tests` → **report RED and wait** → `/pae-implement` →
`/pae-finalize`. It loads `.ai/` context itself. Do **not** pass it the transcript of any
previous subtask.

**The RED checkpoint is what makes the two-commit rule achievable.** `git-flow → ## Commits`
requires a test-only `test:` commit, and that commit can only be created while no
implementation file has been written yet. An agent that reports once, after GREEN, has already
put implementation and tests in the working tree together. So the Implementer stops in the
middle, and the orchestrator — which owns git (`orchestration → ## Roles`) — commits between
the halves:

a. The agent runs `/pae-tests`, then **stops and reports**: the RED digest and the test files
   it wrote. At this point `target_files:` holds test files only.
b. The orchestrator commits exactly those paths as `test: <what the tests assert>`. Stage
   explicit paths — never `git add -A`. Verify nothing under `.ai/` is staged. Append the sha
   to `commits:`.
c. The orchestrator sends the **same** agent one message to continue. It runs
   `/pae-implement` → `/pae-finalize` in the context it already holds, so the GREEN step still
   reads the RED set it is satisfying — the reason tests and implementation share one agent
   (`orchestration → ### Implementer`).
d. On the GREEN report, the orchestrator commits the implementation paths added to
   `target_files:` as `feat: <what was implemented>`, under the same staging rules, and appends
   that sha to `commits:`.

When the test-level gate returned `none` (`atomic-tests: n-a`) there is no RED checkpoint and
no `test:` commit — the agent runs straight through and the subtask gets a single
implementation commit, exactly as `git-flow → ## Commits` specifies for that case.

Commit messages carry no authorship attribution of any kind, and no pipeline identifier —
no `T-XX`, no spec or task directory name, no ADR or `.ai/` path. See
`git-flow → ## Commits` and `## Pipeline identifiers stay out of the repository`. The
attribution rule overrides any harness default that would append a trailer.

**4.3 Validator.** Spawn a **separate** sub-agent. Give it: the path to the same
`T-XX/description.md`, the test files, and the subtask diff (`git diff <base_commit>..HEAD`).
Do **not** give it the Implementer's reasoning or report. Instruct it to run `/pav-check` →
`/pav-propose --batch` → `/pav-close`.

If the verdict is NEEDS WORK → the subtask does not close. Record the findings, leave the
branch and commits intact, and **stop the run**: the stack is sequential and nothing above
this subtask can be built on a failing base.

**4.4 Composite rollup.** When the closed subtask is the last child of a composite,
`/pav-close` triggers `/phase-composite-validation` automatically. It runs on the current
branch — the tip already contains every child. Do not create a branch for the composite.

**4.5 Pull request** (only with `--allow-pr`, only when the subtask is `reviewed`). Push the
branch, then open a **draft** PR with base = the previous subtask's branch (for T-01, base =
the repository default branch). Build the body per `git-flow → ## Pull requests`, including
the stack position and the dependency warning. Record `pr:` in the block.

A subtask that is `blocked` or whose validation `failed` gets no PR.

**4.6 Shared state.** Apply any deltas the sub-agents returned for `architecture.md`,
`.ai/memory/state.md`, or `.ai/project_state.md` — the sub-agents do not write these
themselves (`orchestration → ## Shared-file discipline`). Verify the subtask's progress block
is structurally intact. Run `/compress-state --auto` on the task `state.md`.

---

## Step 5 — Task-level validation

Runs on the stack tip, which holds the whole task. Invoke `/phase-validation <task-directory>`
and let it run its children in order.

Orchestrated-mode behaviour for its two interactive steps:
- `/pv-issues` — do not wait. Approve every `critical` and `important` issue as a fix-task;
  defer every `optional` one. Record the split in `## Issue List`.
- `/pav-propose` — runs with `--batch` inside the fix cycle.

`/pv-contract`'s critical-failure gate is **not** overridden: a violated invariant or an
Off-limits breach stops the run and waits, per `orchestration`.

---

## Step 6 — Fix-tasks

`/pv-create-fixes` calls `/pv-classify-fixes` to decide branch grouping: fixes that clear the
`quick-flow` gate share one fix branch and one PR; fixes that breach it get their own.

Fix branches extend the stack from its tip and follow the same loop as Step 4 — Implementer,
Validator, commits, draft PR. Their commit type is `fix:` and their branch is named after the
defect being fixed, in domain language.

---

## Step 7 — Promote pull requests

Only with `--allow-pr`, only after `/phase-validation` completes with no unresolved critical
findings. Convert every draft PR in the stack to **ready for review**, in stack order.

This is the one moment PRs become mergeable — during the run they are drafts precisely so the
stack cannot shift while later subtasks are still being built.

---

## Step 8 — Final report

```
═══ SPEC RUN COMPLETE ═══════════════════════════════════════
Spec:  <spec path>
Task:  <task directory>
Repo:  <repo>            Base: <base branch>

Subtasks
  T-01 <name>            reviewed
    branch:  feat/oauth-token-schema
    base:    <base branch> @ <base_commit>
    commits: <sha> test: cover token schema validation rules
             <sha> feat: add token schema with expiry validation
    tests:   unit — 7 tests, AC 4/4
    PR:      #141 ready — base <base branch>
  T-02 <name>            reviewed
    branch:  feat/oauth-token-service
    base:    feat/oauth-token-schema @ <base_commit>
    ...

Merge order (fixed by code dependencies)
  1. #141  feat/oauth-token-schema   → <base branch>
  2. #142  feat/oauth-token-service  → retargets to <base branch> once #141 merges
  3. #143  feat/oauth-login-route    …
  Each PR contains its predecessors' commits and cannot reach <base branch>
  without them. Merge strategy is yours — merge commit, rebase, or squash all
  work. After a squash or rebase merge, run `/restack <task-directory>` to
  replay the remaining branches onto the new base.

  Commit hashes above are pre-merge and will not survive a squash or rebase merge.

Validation
  Contract:  <N> pass, <M> fail
  Review:    <N> findings — <N_fix> fixed, <N_defer> deferred
  Deferred:  <list or none>

Open questions (unresolved)
  <list, or "none">

Summary
  <what the task delivered, in prose>
═════════════════════════════════════════════════════════════
```

---

## What this workflow never does

- Never merges a pull request, locally or via `gh`.
- Never pushes to the base branch.
- Never force-pushes — that lives only in `/restack`.
- Never deletes a branch.
- Never commits anything under `.ai/`.
- Never runs `git add -A`, `git reset --hard`, or `git clean`.
- Never writes a pipeline identifier into a branch name, a commit, or pull request text.
- Never resolves a class-B ambiguity on the human's behalf.
- Never runs subtasks in parallel.

## Interruption recovery

Re-run `/spec-run <same-spec>` with the same flags. Step 0 reads `state.md`, reconciles the
recorded branches and commit hashes against the actual repository, and resumes at the first
incomplete subtask. Branch and commit state is recorded as it happens precisely so this is
possible — nothing is reconstructed after the fact.
