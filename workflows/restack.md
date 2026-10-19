---
description: Repair a stacked branch series after the human merged part of it — replays each remaining subtask branch onto its new base, works with any merge strategy
---

Invocation: `/restack <task-directory> [--onto <branch>] [--allow-pr]`
Examples:
- `/restack .ai/tasks/todo/task-01-add-oauth/` — replay remaining branches onto the default base
- `/restack .ai/tasks/todo/task-01-add-oauth/ --onto main --allow-pr` — and update the open PRs

Load `git-flow` before running. This is the **only** workflow permitted to rebase or
force-push, and it may do so only on subtask branches of this task.

---

## Why this exists

`/spec-run` builds a stack: each subtask branch is cut from the previous one. When the human
merges the bottom of that stack into the base branch, what happens to the rest depends on the
merge strategy:

| Strategy used by the human | Effect on the remaining stack |
|---|---|
| Merge commit | The parent's commits land in the base unchanged; remaining branches already contain them and stay consistent. Restack is usually a no-op. |
| Rebase merge | The base gets the same changes under new shas. Remaining branches still carry the old shas. |
| Squash merge | The base gets one new commit that appears nowhere in the remaining branches' history. |

This workflow makes all three converge on one operation, so the human is free to merge
however they like:

```
git rebase --onto <new-base> <recorded base_commit> <subtask branch>
```

Because `base_commit` is the recorded branch point, this replays **only that subtask's own
commits**, whatever happened to its predecessor. Git drops patch-equivalent commits by itself,
which covers the rebase-merge case; the squash case is covered because the recorded branch
point is used instead of a computed merge base — after a squash the computed merge base is
wrong, which is exactly why the field is recorded at creation time and never recomputed.

---

## Guard

1. Read `state.md` in the task directory. If absent → **stop**: "No task state found."
2. Verify the working tree is clean (tracked files). If not → **stop**.
3. Collect every subtask block with a `branch:` field, in stack order (the order recorded in
   `plan.md → ## Subtasks`).
4. If any block is missing `base_commit:` → **stop**: "T-XX has no recorded `base_commit`. The
   stack cannot be replayed safely without it — the branch point cannot be recovered after a
   squash merge. Rebase T-XX manually or re-cut the branch."
5. Report the plan before touching anything: which branches are already merged, which will be
   replayed, and onto what.

---

## Step 1 — Classify each branch

For each subtask branch, bottom-up:

- **Merged** — its changes are already contained in the new base. Detect with
  `git cherry <new-base> <branch>`: if every commit is marked `-`, the branch is fully
  applied. Mark merged, skip, and record `notes: restack — already merged into <base>`.
- **Pending** — some commits are not in the base. It will be replayed.
- **Missing** — the branch no longer exists locally (the human deleted it after merging).
  Treat as merged; record it and continue.

The first pending branch's new base is `--onto <branch>` if given, otherwise the repository
default branch. Each subsequent pending branch's new base is the **replayed tip of the
previous pending branch** — the stack is rebuilt in the same shape.

---

## Step 2 — Replay

For each pending branch, in stack order:

1. `git rebase --onto <new-base> <recorded base_commit> <branch>`
2. **On conflict** → **stop immediately**. Do not attempt automatic resolution: the conflict
   means the merged code and this subtask's code disagree, which is a content decision, not a
   mechanical one. Report the conflicting paths, leave the rebase in progress, and tell the
   user they can finish with `git rebase --continue` or abandon with `git rebase --abort`.
   Record the halt in the subtask's `notes:`.
3. On success, update that subtask's block:
   - `base_commit:` → the new branch point (`git rev-parse <new-base>`)
   - `base_branch:` → the new base branch name
   - `commits:` → the new shas, replacing the old ones, with a `notes:` line recording that
     the previous hashes are superseded: `restack <date>: commits replayed, prior hashes void`
4. The replayed tip becomes the base for the next pending branch.

Never rebase the base branch. Never rebase a branch that is not recorded in this task's state.

---

## Step 3 — Publish (only with `--allow-pr`)

For each replayed branch: `git push --force-with-lease origin <branch>`.

- `--force-with-lease`, never `--force`. If the lease fails, the remote moved — **stop** and
  report; someone else pushed to that branch.
- Open PRs update automatically. If a PR's base branch was merged and deleted, the host may
  have already retargeted it — verify the base matches the new stack shape and correct it with
  `gh pr edit <n> --base <branch>` if not.
- Do **not** change any PR's draft/ready state here, and do **not** merge anything.

Without `--allow-pr`, the replay stays local and nothing is pushed.

---

## Step 4 — Report

```
─── RESTACK COMPLETE ────────────────────────────────────────
Task:      <task directory>
New base:  <branch> @ <sha>

  T-01  merged      — already contained in <base>
  T-02  replayed    — 2 commits → <new sha>, <new sha>   PR #142 updated
  T-03  replayed    — 3 commits → <new sha>, …           PR #143 updated
  T-04  halted      — conflict in <paths>

Remaining merge order: #142 → #143 → …
Prior commit hashes for replayed branches are void; state.md updated.
─────────────────────────────────────────────────────────────
```

If any branch halted, say plainly which one and that the rebase is still in progress.
