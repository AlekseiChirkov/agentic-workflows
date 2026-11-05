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
   canonical repository and task paths (schema: `## Recovery journal`). Inspect it before
   clean-tree/replay checks.
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
   publishable branch as its `expected_remote_tip` for an explicit force-with-lease.
   Without it, execute no push or `gh` command. Report the classification and replay plan
   before mutation.

## Recovery journal

The journal is this workflow's recovery record and the only evidence the git-rails hook
accepts for a replay rebase or a lease push; without exactly one matching journal the hook
asks the owner, or denies a form or target it cannot resolve (`git-flow → ## Safety rails`).
The file name is the SHA-256 hex digest of the UTF-8 `task_path`. Every file in the journal
directory whose name is 64 hex digits followed by `.json` must be a usable journal: one that
is unreadable, invalid or misnamed makes every replay and lease push ask, as an unreadable
journal directory does. Minimum schema; extra fields are allowed:

```json
{
  "schema_version": 1,
  "repository_common_dir": "/abs/canonical/.git",
  "task_path": "/abs/canonical/task/dir",
  "target": {"branch": "main", "sha": "<sha>"},
  "publication_authorized": false,
  "order": ["feat/oauth-token-service", "feat/oauth-login-route"],
  "branches": {
    "feat/oauth-token-service": {
      "original_base_commit": "<sha>",
      "original_tip": "<sha>",
      "replayed_tip": null,
      "expected_remote_tip": null
    },
    "feat/oauth-login-route": {
      "original_base_commit": "<sha>",
      "original_tip": "<sha>",
      "replayed_tip": null,
      "expected_remote_tip": null
    }
  }
}
```

- Every SHA is a full 40- or 64-character lowercase hex object name. `repository_common_dir`
  and `task_path` are the canonical absolute paths resolved in the Guard. `target` is the
  resolved target branch and its SHA, captured once before the first replay.
- `publication_authorized` is `true` only when `/restack` runs with `--allow-pr`.
- `order` lists only the branches to replay, in replay order: the first entry is replayed
  onto `target.sha`, each later entry onto the previous entry's `replayed_tip`. Record
  merged and skipped branches with their evidence in an extra field, never in `order`.
- `branches.<b>` exists for every entry of `order`. `original_base_commit` is the
  recorded `base_commit:`; `original_tip` is the branch tip before replay; `replayed_tip`
  is `null` until that branch's replay succeeds, then its new tip.
  `expected_remote_tip` is a SHA, `"absent"` (the branch was confirmed absent on the
  remote) or `null` (not captured).

This workflow uses exactly these command forms, with full SHAs and literal branch names.
The hook allows a replay or a forced push only when exactly one journal verifies it (a push:
every destination), and otherwise asks the owner, or denies a form or target it cannot
resolve:

- Replay: `git rebase --onto <new-sha> <old-sha> <branch>`. `<branch>` is the first entry of
  `order` whose `replayed_tip` is `null` and is at its `original_tip`; `<old-sha>` is its
  `original_base_commit`; `<new-sha>` is its replay base from `order`. Before the first
  replay, read `git config --type=bool --get rebase.updateRefs`. When `rebase.updateRefs`
  is true, or the hook asks about a replay → **stop**: "The replay of `<branch>` cannot be
  verified: <reason>." Report it; never retry the replay in another form. After a
  conflict, `git rebase --continue`, `--skip` and `--abort` of that replay are accepted as
  well.
- Publication: `git push --force-with-lease=refs/heads/<b>:<sha> origin <b>`, one branch per
  push, where `<sha>` is the branch's `expected_remote_tip` and the local branch is at its
  `replayed_tip`. For a branch recorded as `"absent"`, use
  `git push --force-with-lease=refs/heads/<b>: origin <b>`. Never add `--force` or a `+`
  refspec. A dry-run push (`--dry-run` or `-n`) is allowed.

The journal records only what this workflow observed. Never edit it to make a command pass
the hook; a command the hook asks about follows the owner-approval protocol in
`git-flow → ## Safety rails`.

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

Before mutation, persist the Guard's recovery journal (`## Recovery journal`) with
repository/task identity, the chosen target, `publication_authorized`, the replay `order`,
original branch points and tips, `replayed_tip: null` for every branch still to replay and
the expected remote tips.
After each successful replay, write that branch's `replayed_tip` before the next replay.
Keep state deltas there until no further replay requires a clean tree; then apply them to
task state. This also supports tracked task state
without making subsequent replays fail on this workflow's own edits.

For each pending branch, in stack order:

1. Take `<new-sha>`, the branch's replay base from `order`, as an immutable SHA, and
   `<old-sha>`, its recorded `base_commit`, then run:
   `git rebase --onto <new-sha> <old-sha> <branch>`.
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

For each changed branch, push using its captured `expected_remote_tip` as `<sha>`:
`git push --force-with-lease=refs/heads/<b>:<sha> origin <b>`.
Use the empty lease `git push --force-with-lease=refs/heads/<b>: origin <b>` only for a
branch whose `expected_remote_tip` is `"absent"`.

If a lease fails → **stop**: report remote movement; never replace the expected tip and
retry automatically. Verify open PR bases match the rebuilt stack and correct them with
`gh pr edit <n> --base <new-base-branch>`. Preserve draft/ready state. Never merge a PR.
Without `--allow-pr`, keep all replay results local.

## Step 4 — Report

Report the task, target branch/SHA, each branch's classification and evidence, replayed
commit counts, state changes, publication/PR results, and remaining merge order. On a
halt, identify the branch, recovery journal and whether a rebase remains in progress.
Then **stop**.
