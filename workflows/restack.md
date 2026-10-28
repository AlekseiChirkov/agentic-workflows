---
description: Repair a stacked branch series after part was merged — replay each remaining branch onto its new base using recorded branch points
---

Invocation: `/restack <task-directory> [--onto <branch>] [--allow-pr]`
Load `git-flow`. Only this workflow may rebase or force-push, and only branches recorded
for this task. Resolve task paths from the project root; operate in its single repository.

## Guard

1. Read task `state.md` and `plan.md`. If either is missing → **stop**: name it.
2. Resolve the absolute git common directory with
   `git rev-parse --path-format=absolute --git-common-dir`. Use the recovery journal
   `<common-dir>/orchestrail-restack/<sha256-of-canonical-task-path>.json`, keyed by
   canonical repository and task paths. Inspect it before clean-tree/replay checks.
3. Apply `git-flow → ## Preflight (mandatory, before any branch is created)` as relevant
   to replay: require a clean tracked tree, no unresolved git operation, and a resolvable
   target base. Resolve `--onto` or the repository's configured default branch; do not
   guess `main` or silently fetch a different revision.
4. Collect branch-owning subtask blocks in plan order. Verify each branch belongs to this
   task and is not the target/default base. If none → report "No task branches to restack."
   and **stop**.
5. If a block is missing `base_commit:` → **stop**: "No recorded branch point for `<branch>`.
   The stack cannot be replayed safely; recover the original point from evidence first."
6. Verify each recorded branch point and tip exists as a commit and the point is an
   ancestor of that tip. Recover a missing local branch's tip from its recorded commits
   or existing remote-tracking ref only when they agree; absence never proves merger.
7. Reconcile an existing journal only when repository/task identity and actual tips
   match its original or confirmed replayed tips. Mismatch → **stop**: report the changed
   branch. An interrupted rebase requires the user to continue or abort it, then rerun
   for evidence-based journal reconciliation; never infer success from journal presence.
8. With `--allow-pr`, verify remote/authentication and capture the remote tip of each
   publishable branch for an explicit force-with-lease. Without it, execute no push or
   `gh` command. Report the classification and replay plan before mutation.

## Step 1 — Classify each branch

Classify against the resolved target base, using only each branch's own range
`<recorded base_commit>..<recorded tip>`:

- **Merged:** the tip is an ancestor of the target, or every commit in a nonempty own
  range is patch-equivalent there (`git cherry <target> <tip> <base_commit>` gives only
  `-` entries). An empty own range is already contained.
- **Squash-merged:** patch comparison alone cannot establish this. Require a recorded
  merged PR whose head matches the recorded tip and whose merge commit is in the target,
  verified through the host only with `--allow-pr`, or equivalent explicit owner evidence.
- **Pending:** the branch is known to be unmerged and contains work to replay.
- **Uncertain/missing:** unavailable tip or ambiguous merger evidence → **stop**: report
  what must be established. A deleted local branch is not evidence that its work landed.

Do not classify squash candidates as definitely pending merely because commit hashes or
individual patch IDs differ. Record the evidence for every skipped branch.
The first pending branch uses the target base; later pending branches use the successfully
replayed tip of the previous pending branch. Restore an absent pending local branch only
from the verified recorded tip.

## Step 2 — Replay

Before mutation, persist the Guard's recovery journal with repository/task identity,
original branch points/tips, confirmed replayed tips, chosen target, planned order and
expected remote tips.
Update it after each successful replay. Keep state deltas there until no further replay
requires a clean tree; then apply them to task state. This also supports tracked task state
without making subsequent replays fail on this workflow's own edits.

For each pending branch, in stack order:

1. Capture `<new-base>` as an immutable SHA, then run:
   `git rebase --onto <new-base-sha> <recorded base_commit> <branch>`.
2. **On conflict** → **stop immediately**. Do not attempt automatic resolution. Preserve
   the journal, apply completed-branch state deltas, record the halt and conflicting paths,
   and leave the rebase in progress. Tell the user to finish with `git rebase --continue`
   or abandon with `git rebase --abort`. Do not publish a partial stack.
3. On success, record new `base_commit:` (the captured new base SHA), `base_branch:`, and
   `commits:` for the replayed own range. Preserve the old values in the recovery journal;
   add `notes: restack <date>: prior hashes superseded` without removing existing notes.
4. Use this branch's new tip as the next pending branch's base.

Never replay the target/default branch or an unrecorded branch. Apply final state deltas
before publishing, and verify the recorded new tips match git. Retain the journal until
state and any requested publication are complete; remove only this workflow's journal.

## Step 3 — Publish (only with `--allow-pr`)

For each changed branch, push using its captured expected remote tip:
`git push --force-with-lease=refs/heads/<branch>:<expected-tip> origin <branch>`.
Use an empty expected tip only for a branch confirmed absent remotely.

If a lease fails → **stop**: report remote movement; never replace the expected tip and
retry automatically. Verify open PR bases match the rebuilt stack and correct them with
`gh pr edit <n> --base <new-base-branch>`. Preserve draft/ready state. Never merge a PR.
Without `--allow-pr`, keep all replay results local.

## Step 4 — Report

Report the task, target branch/SHA, each branch's classification and evidence, replayed
commit counts, state changes, publication/PR results, and remaining merge order. On a
halt, identify the branch, recovery journal and whether a rebase remains in progress.
Then **stop**.
