---
description: Orchestrator — carry one spec from Discovery to review-ready pull requests, one stacked branch per subtask, using context-bounded sub-agents
---

Invocation: `/spec-run <path-to-spec> [--allow-pr] [--dry-run]`
You are the **Orchestrator**. Load `orchestration` and `git-flow` before Step 0.
They own roles, shared-file discipline, escalation and git rails.

- `--allow-pr` authorizes pushes and draft PRs; without it run no push or `gh` command.
- `--dry-run` reports preflight, existing plan and proposed stack without project writes,
  branches, commits, PRs or Discovery. Best-effort telemetry is its only write exception.
- One repository per invocation; split cross-repository work into separate specs.

## Guard

Require an existing spec, supported worker messaging, and passing git preflight. Read
state before mutation. Resume completed checkpoints rather than recreating their branches
or commits. Existing class-B questions must be answered before execution; an overwrite
still needs explicit authorization. A completed run with no remaining PR promotion stops.

---

## Run Logging

This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the
store, the field vocabulary, and the rule that logging never blocks a run.

After Step 0 resolves the task and resume point, open the run with `scripts/log-step.sh run-start` through the configured helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
RUN_ID=""
if [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline spec-run \
  --project "$WORK_DIR" --task <task-directory> --spec <spec-path> \
  --flags "<--allow-pr / --dry-run as passed>") || RUN_ID=""
fi
```

The Orchestrator owns prompt log calls and adapter dispatch/status/fallback calls.
Native hooks deliver their own correlated writes; a sub-agent never calls
`scripts/log-step.sh` and returns its report marker. Follow `run-log → ## Workflow coverage and routing`
for every boundary, including uncertain resumes and unavailable status.

Log each executed numbered step once, plus one synthetic aggregate per subtask
(`--step subtask --subtask T-XX --tests <atomic-tests> --gate <verdict> --note approximate`).
This aggregate is distinct from the named RED row in Step 4.2. Ordinary prompt steps use
`--note approximate`. Log an actual batch stop as
`--step batch-gate --stops 1 --questions N --note approximate`; do not count an empty gate as a stop.
Dry-run logs only `run-start`, `--step dry-run --outcome skipped --note approximate`,
and `run-end --outcome completed`. Close other runs as `completed`, `stopped` or `failed`.
Missing helpers or log failures never block work; mention unavailable logging once.

---

## Step 0 — Preflight and resume

1. Resolve the project `WORK_DIR` and run `git-flow → ## Preflight (mandatory, before any branch is created)`. Report any failure
   and **stop**. Dry-run performs read-only checks and reads an existing plan if available;
   otherwise report "unknown until Discovery" and stop after closing telemetry.
2. Run `phase-discovery` Step 0 in full for resolution only, adopting its working directory, task path,
   multi-phase selection and collision guards. Resolution itself writes nothing; let
   Discovery initialize a fresh task once.
3. If resolution found a new task without state, start at Step 1. Otherwise read
   `state.md` and reconcile recorded branches and commit tips. A missing branch or
   unexpected tip requires explicit reconciliation; never infer that missing means merged.
   Clean-tree preflight also applies on resume. Uncommitted tracked work, including
   tracked task bookkeeping, stops before mutation: report exact paths and the pending
   checkpoint for user reconciliation. Never stash or commit it merely to clear this gate.
4. Resolve pending `## Open Questions (batch)` before resuming any execution. Preserve
   answered assumptions, and reconsider unstarted design/decomposition if answers change
   them. Conflicts with already built work stop for a recorded decision.
5. Resume the earliest unfinished checkpoint:
   - Discovery incomplete: Step 1.
   - Discovery complete, model/stack setup missing: Steps 2–3.
   - Unreviewed leaves: Step 4 at the first one, at its existing atomic/git checkpoint.
   - Leaves reviewed, execution finalization missing: `/pe-finalize` before Step 5.
   - Execution complete, Validation incomplete: Step 5, including its pending fixes.
   - Validation complete: Step 7 if authorized PR promotion is outstanding; otherwise report.
6. Report the resume point and flags. Restore the Arbiter from current artifacts on a new
   session; do not assume a previous worker or its in-memory dispatch envelope survived.

---

## Step 1 — Discovery, with the batch gate

Pass the resolved `--phase N` for multi-phase specs so the child keeps the selected
phase. Run `/phase-discovery` in autonomous **orchestrated** mode, allowing normal initialization
for a fresh task and resuming existing Discovery artifacts otherwise. It owns child sequencing and quick/full routing; never pass `--step-by-step`.
Spawn the **Arbiter** after task artifacts exist, before execution; give it current spec,
state, plan and relevant project context. Retain it by message for this session.

`orchestration → ## Escalation protocol` governs Discovery: resolve class A with cited
sources; collect class B in `## Open Questions (batch)`. No worker may infer missing intent.

### The batch gate — the only planned human stop

After `/pd-finalize`, read `## Open Questions (batch)`.

- **Empty** → report "No open questions. Proceeding to execution." and continue.
- **Non-empty** → present every question as one list. For each: the question, why it is not
  answerable from the artifacts, 2–3 options with consequences, and the Arbiter's
  recommendation. Then **stop and wait**.

Write the human's answers into `### Assumptions` (one line each, source: `user`), clear
`## Open Questions (batch)`, and only then continue.

The batch gate runs before any branch is created. After answers, reconcile any affected
unstarted plan, descriptions and design before continuing; skip no unresolved questions
on resume. If `flow: quick`, this branch-per-leaf workflow has no leaf plan: **stop** and
report `/phase-pipeline <task-directory>` as the supported inline route. Do not invent a
leaf, silently promote the tier or implement code in the Orchestrator.

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

Derive the branch stack per `git-flow → ## Branch model — the stack`: subtask N branches from the tip of
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

Subtask identifiers appear in this plan and in `state.md`; whether those records are tracked
follows repository policy. They never reach a branch name, a commit message, or pull request
text — see
`git-flow → ### Pipeline identifiers stay out of the repository`.

---

## Step 4 — Subtask loop

For each pending leaf in order. Never start N+1 before N is `reviewed`. On resume,
reuse its branch and skip completed checkpoints: existing RED resumes at its test commit,
GREEN with execution complete resumes at finalization/implementation commit, and `done`
resumes at Validator. Recreate a lost worker from current artifacts; never rewrite RED to
recover conversation memory. Apply returned shared-file deltas after each checkpoint,
before another worker or composite check depends on them. Re-read the plan and recompute
the pending dependency order after each delta: approved integration siblings are runnable
work, not entries to leave behind in the originally printed stack. Update remaining stack
positions and PR totals; preserve already created branch points.

**4.1 Branch.** Derive the branch name from the subtask's `## Goal` as `<type>/<feature-slug>`
in domain language — never from its identifier (`git-flow → ## Branch model — the stack`). For a new leaf, create it from
the previous reviewed leaf's tip (default branch for the first) and check it out.
For a resumed leaf, check out its reconciled existing branch.
Immediately record in the subtask's `## Subtask Progress` block: `branch:`, `base_branch:`,
and `base_commit:` (the sha of the branch point — `git rev-parse HEAD` before any work).
`base_commit` is written once and never recomputed. Do not rewrite it on resume.

**4.2 Implementer — one agent, two checkpoints.** Before the existing spawn, check native
capability, current installation and native session identity as required by
`run-log → ## Workflow coverage and routing`. Only when the profile/payload is supported,
installation is available, `RUN_ID` is usable and `CLAUDE_CODE_SESSION_ID` is present,
provisionally dispatch the expected `pae-tests` boundary. Assign one stable logical
`actor_id` to this worker, retain it for the checkpoint, and invoke the readable adapter
through Bash:

```bash
HOOK_ADAPTER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/hooks/log-step-hook.sh}"
DISPATCH_LINE=""
if [ -r "$HOOK_ADAPTER" ]; then
  DISPATCH_LINE=$(bash "$HOOK_ADAPTER" dispatch --run "$RUN_ID" \
    --agent-id "$actor_id" --boundary subagent --expected-skill pae-tests) || DISPATCH_LINE=""
fi
```

Retain the original `ORCHESTRAIL_DISPATCH_V1` line unchanged in the native user input
of the fresh sub-agent, together with the complete returned tuple in the current run
context. Validate the returned envelope against the adapter contract before treating
it as issued; if issuance is uncertain, use the canonical unknown-resume route. Never
reconstruct or quote the line as assistant/tool output. A known unavailable dispatch
that issued no envelope uses the canonical ordinary approximate path.

Spawn the fresh sub-agent with the model from Step 2. Give it: the path to
`T-XX/description.md`, the resolved `WORK_DIR`, the branch name,
and the instruction to run `/pae-tests` → **report RED and wait** → `/pae-implement` →
`/pae-finalize`. It loads `.ai/` context itself. Do **not** pass it the transcript of any
previous subtask.

The Implementer reports before implementation so the Orchestrator can create the
required test-only commit. Workers never run git:

a. The agent runs `/pae-tests`, then **stops and reports**: the RED digest and the test files
   it wrote. At this point `target_files:` holds test files only.
   When a provisional envelope was supplied and RED was actually established, append
   one unindented canonical `ORCHESTRAIL_REPORT_V1` line outside code fences to this
   final response. Use the exact retained tuple with `"outcome":"ok","tests":"red"`,
   compact key-sorted JSON and no step or timestamp fields. Marker construction and
   native evidence follow `run-log → ## Native hook adapter → ### Dispatch and native evidence`. A genuine unique
   native `Skill` invocation of `pae-tests` remains required; the expected-skill flag
   alone, a wrapper invocation, or reading the workflow file cannot establish coverage.
   The orchestrator resolves status or serialized fallback before the git checkpoint,
   using `run-log → ## Workflow coverage and routing`. Match the retained tuple and
   acceptance receipt; suppress only this named RED row after acceptance. If no envelope
   was ever issued, log `--step pae-tests --outcome ok --tests red --note approximate`.
   Do not fabricate native events, poll, or delay the git handoff for telemetry.
b. The orchestrator commits exactly those paths as `test: <what the tests assert>`. Stage
   explicit paths — never `git add -A`. Verify staged paths follow the repository-owned
   tracking policy in `git-flow → ## Commits`. Append the sha to `commits:`.
c. The orchestrator sends the **same** agent one message to continue. It runs
   `/pae-implement` → `/pae-finalize` in the context it already holds, so the GREEN step still
   reads the RED set it is satisfying — the reason tests and implementation share one agent
   (`orchestration → ### Implementer`).
   The GREEN batch must never reuse the RED marker or envelope for its return; retain
   approximate logging for `pae-implement`, `pae-finalize` and the existing aggregate.
d. On the GREEN report, the orchestrator commits the implementation paths added to
   `target_files:` as `feat: <what was implemented>`, under the same staging rules, and appends
   that sha to `commits:`.

When the test-level gate returned `none` (`atomic-tests: n-a`), emit no RED report and
no RED timing row. Leave any provisional checkpoint uncovered: there is no RED checkpoint
and no `test:` commit — the agent runs straight through and the subtask gets a single
implementation commit, exactly as `git-flow → ## Commits` specifies for that case.

Follow `git-flow → ## Commits` for explicit staging, repository tracking policy and
messages. Verify the recorded digest/commits before skipping an interrupted checkpoint.
A characterization (`pinned`) checkpoint uses the same test-first commit handoff without
claiming RED or emitting a named RED marker; follow `tdd` for its evidence.

**4.3 Validator.** Spawn a **separate** sub-agent. Give it: the path to the same
`T-XX/description.md`, the test files, and the subtask diff (`git diff <base_commit>..HEAD`).
Do **not** give it the Implementer's reasoning or report. Instruct it to run `/pav-check` →
`/pav-propose --batch` → `/pav-close`.

Keep the three-skill validation batch and its internal prompt steps approximate under
`run-log → ## Workflow coverage and routing`.

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

**4.6 Shared state.** Apply returned plan, composite and knowledge deltas per
`orchestration → ## Shared-file discipline`; verify each progress block is intact.
Compress task state with `/compress-state --auto`. After all leaves are reviewed, run
`/pe-finalize` once to record Execution completion and collect batched proposals before
Task-level Validation. In this mode, retain batched proposals pending and report them
at delivery; apply none and request no new proposal choice. This named override is
registered in `workflow-globals`. The Orchestrator delegates approved code work to an Implementer.

---

## Step 5 — Task-level validation

Run `/phase-validation <task-directory>` on the stack tip. Its children own issue
collection, fix creation/classification, fix execution and finalization; do not rerun those
steps separately afterward. Inside this invocation:

- `/pv-issues`: approve `critical`/`important`, defer `optional`, and record the split.
- `/pav-propose`: pass `--batch`; record proposals and apply nothing.
- `/pv-contract`: preserve the critical-failure gate; failed Invariant/Off-limits stops.
- `/spec-sync`: pass `--auto-mode` after validation checks; failed criteria remain defects.

## Step 6 — Fix-tasks

This is a callback **during Step 5**, not a second fix pass. `/pv-create-fixes` calls
`/pv-classify-fixes`: gate-qualified fixes share a branch/PR; others get dedicated branches.
The Orchestrator applies shared deltas and runs Step 4's Implementer/Validator/commit
handoffs for each group before `/pv-finalize`. Shared groups execute leaves sequentially
on their recorded branch; only dedicated groups create another branch. Use domain-named
`fix:` branches/messages and test-first commits under `git-flow`.

---

## Step 7 — Promote pull requests

Only with `--allow-pr`, only after `/phase-validation` completes with no unresolved critical
findings. Convert every draft PR in the stack to **ready for review**, in stack order.

This is the one moment PRs become mergeable — during the run they are drafts precisely so the
stack cannot shift while later subtasks are still being built.

---

## Step 8 — Final report

Report the spec/task/repo/base, final outcomes and delivered behavior. For each leaf or
fix group include status, branch, base and `base_commit`, commit hashes, tests and PR URL
(or local-only). Include contract/review results, deferred findings, proposals and open
questions. Mark hashes as pre-merge. List the required merge order and the dependency
warning: later PRs include predecessors. After squash/rebase integration, `/restack`
repairs remaining branches; the human chooses merge timing and strategy.

If blocked, report the exact checkpoint and resume command; never label it complete.

---

## What this workflow never does

- Never merges a pull request, locally or via `gh`.
- Never pushes to the base branch.
- Never force-pushes — that lives only in `/restack`.
- Never deletes a branch.
- Never commits untracked consumer state without explicit user authorization; tracked `.ai/`
  knowledge and state follow repository policy.
- Never runs `git add -A`, `git reset --hard`, or `git clean`.
- Never writes a pipeline identifier into a branch name, a commit, or pull request text.
- Never resolves a class-B ambiguity on the human's behalf.
- Never runs subtasks in parallel.

## Interruption recovery

Re-run `/spec-run <same-spec>` with the same flags. Step 0 reads `state.md`, reconciles the
recorded branches and commit hashes against the actual repository, and resumes at the first
incomplete subtask. Branch and commit state is recorded as it happens precisely so this is
possible — nothing is reconstructed after the fact.
