# `/spec-run` — quickstart

One spec → stacked branches → review-ready pull requests, run by context-bounded sub-agents.
Full contracts: `rules/orchestration.md` (roles, escalation) and `rules/git-flow.md` (branches,
commits, safety rails). This page is the operating procedure only.

Use it when a task is big enough that one session would run out of context. For a small change,
use the quick tier instead (`rules/quick-flow.md`).

---

## Before you start

| Check | How |
|---|---|
| Clean working tree (tracked files) | `git status` — untracked files are permitted |
| Repository-owned `.ai/` policy | Inspect `git ls-files .ai` and repository instructions; tracked knowledge and state are accepted |
| Local consumer state stays local | Keep untracked `.ai/` excluded from commits unless the user explicitly authorizes tracking it |
| `test:` command is filled in | `.ai/context/runbook.md → ## Commands` — the TDD step stops without it |
| Spec exists | `.ai/specs/<NN>-<slug>.md`, H1 title required, `## Acceptance Criteria` strongly recommended |
| Only for `--allow-pr` | remote `origin` exists and `gh auth status` succeeds |

One spec covers **one repository**. Cross-repo work is split into separate specs.

---

## Run it

```bash
/spec-run .ai/specs/01-add-oauth.md --dry-run     # print preflight + branch stack, change nothing
/spec-run .ai/specs/01-add-oauth.md               # full run, everything stays local
/spec-run .ai/specs/01-add-oauth.md --allow-pr    # also push branches and open draft PRs
```

Start with `--dry-run` on a repository you have not used it in before: it prints the preflight
result and the stack it would build, and creates nothing.

Without `--allow-pr`, no `git push` and no `gh` command runs at any point.

---

## What it does, in order

| Step | What happens |
|---|---|
| 0 | Preflight; if the task directory exists, work out the resume point and reconcile recorded branches against the actual repository |
| 1 | Discovery (`pd-analyze` → `pd-decompose` → `pd-design` → `pd-finalize`), autonomous. The Arbiter is spawned here and kept alive for the whole run. **→ the batch gate, see below** |
| 2 | `/pd-select-model` in bulk mode fills the `Model` column in `plan.md` |
| 3 | Resolve execution order and print the branch stack before touching anything |
| 4 | Per subtask: cut the branch → Implementer writes RED tests → **orchestrator commits `test:`** → same agent implements GREEN → orchestrator commits `feat:` → a **separate** Validator reviews → draft PR |
| 5 | Task-level validation on the stack tip (`/phase-validation`) |
| 6 | Fix-tasks, if the review produced any — grouped into shared or dedicated branches |
| 7 | All draft PRs promoted to ready for review, in stack order |
| 8 | Final report: branches, commits, tests, PRs, merge order |

Execution is strictly sequential — one subtask at a time. Sub-agents exist to bound context,
not to parallelise.

---

## The one planned stop

After Discovery, `/spec-run` presents **`## Open Questions (batch)`** — the ambiguities no
agent may resolve, because the answer is product intent that is not in the spec, the codebase,
or the principles. Each comes with 2–3 options and the Arbiter's recommendation.

Answer them, and the run continues unattended.

This gate is deliberately placed **before the first branch is created**: at that point an
answer that changes the design costs one re-run of decomposition, while the same answer during
Execution would invalidate every branch already stacked on top of the wrong assumption.

---

## Everything else that can stop it

Not planned stops — each means something needs your decision:

- A violated invariant or an Off-limits breach (`/pv-contract` critical-failure gate).
- `atomic-tests: failed` — RED was never established.
- A validator verdict of NEEDS WORK: the subtask does not close and the run stops there,
  because nothing above it can be built on a failing base.
- A composite-promotion tripwire.
- Any `## Guard` that would overwrite existing artifacts.
- A preflight or git-rail violation.
- A class-B question discovered during Execution (Discovery missed it) — branches and commits
  are left intact, and the question is recorded.

---

## What you get

A stack, each branch cut from the tip of the previous one:

```
main
└── feat/oauth-token-schema      PR #141 ready
    └── feat/oauth-token-service PR #142 ready
        └── feat/oauth-login-route  PR #143 ready
```

Per subtask, at least two commits: `test:` with the failing tests, then `feat:` with the
implementation. The separate RED commit is the reviewable evidence that the tests came first.
When the test-level gate returned `none`, there is one implementation commit and the
justification lives in `state.md`.

Branch names and commit messages carry **no** pipeline identifiers and no authorship
attribution — no subtask id, no spec or task directory name, no ADR or `.ai/` path. The mapping
back to a subtask lives in `state.md`; its visibility follows repository tracking policy.
Stage explicit paths, including intentional tracked knowledge updates when applicable.

---

## Merging, and `/restack`

**You merge. The orchestrator never does** — it never merges a PR, never pushes to the base
branch, never deletes a branch, never force-pushes outside `/restack`.

Because branch N contains branches 1…N-1, merge them bottom-up. Any strategy is fine —
merge commit, rebase, or squash. After a rebase or squash merge, replay what is left:

```bash
/restack .ai/tasks/todo/task-01-add-oauth/              # local only
/restack .ai/tasks/todo/task-01-add-oauth/ --allow-pr   # and update the open PRs
```

`/restack` works with any strategy because each branch's `base_commit` was recorded when the
branch was created and is never recomputed. On a conflict it stops and hands the rebase to you —
a conflict is a content decision, not a mechanical one.

Commit hashes in the final report are pre-merge and will not survive a squash or rebase merge.

---

## If it is interrupted

Re-run the same command with the same flags:

```bash
/spec-run .ai/specs/01-add-oauth.md --allow-pr
```

Step 0 reads `state.md`, checks each recorded branch still matches its recorded commits, and
resumes at the first incomplete subtask. If a branch moved underneath the recorded state —
someone worked on it by hand — it stops and says so rather than building on an unknown base.

---

## Where to look while it runs

Everything is in the task-level `state.md → ## Subtask Progress`:

```
T-02 | token service | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch:       feat/oauth-token-service
  base_branch:  feat/oauth-token-schema
  base_commit:  <sha of the branch point>
  commits:      <sha> test: cover token refresh rules, <sha> feat: add token refresh service
  pr:           #142 draft
```

`base_commit` is the one field that cannot be recovered after a squash merge — never remove it.
`notes:` lines beginning with `tdd:` and `arbiter:` are the audit trail: test level, `none`
justifications, test amendments, and every class-A resolution with its cited source.
