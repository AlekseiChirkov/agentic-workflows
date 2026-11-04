---
trigger: always_on
---

# Git Flow Contract

Governs every workflow that creates a branch, writes a commit, or opens a pull request.
Owners: `/spec-run` (builds the stack) and `/restack` (repairs it). No other workflow performs
git write operations.

This rule is about *mechanics and safety rails*. Orchestration roles and the escalation
protocol live in `orchestration`; the test-first cycle lives in `tdd`.

---

## Preflight (mandatory, before any branch is created)

Refuse to start unless **all** of these hold. Report which check failed and stop — never
proceed on a partial pass.

1. `WORK_DIR` is a git repository (`git rev-parse --git-dir` succeeds).
2. The working tree is clean — no staged, unstaged, or conflicted **tracked** changes.
   Untracked files are permitted.
3. **Respect repository-owned `.ai/` tracking policy.** Inspect `git ls-files .ai` and
   repository instructions. Tracked knowledge and state are accepted; their presence is
   not a preflight failure. Keep untracked consumer state excluded from commits unless
   the user explicitly authorizes tracking it. Never require removing tracked knowledge
   or changing the repository's ignore policy to start a run.
4. The base branch exists and is checked out or resolvable.
5. No existing branch collides with a branch this run would create — unless this is a resume
   (the branch is recorded in `state.md → branch:` for that T-XX).
6. **`--allow-pr` only:** a remote named `origin` exists, and `gh auth status` succeeds.
   Without the flag, neither `git push` nor any `gh` command is executed at any point.

Single-repo only. A task whose subtasks carry `working_dir:` pointing outside the repository
is out of scope — one spec covers exactly one repository.

---

## Branch model — the stack

Subtask branches chain off one another in dependency order. This is a hard requirement, not a
default.

```
<base>                              (repository default branch)
└── feat/oauth-token-schema         ← branched from <base>
    └── feat/oauth-token-service    ← branched from feat/oauth-token-schema
        └── feat/oauth-login-route  ← branched from feat/oauth-token-service
```

- Branch N is created from the **tip of branch N-1** after N-1 reaches `reviewed`, never from
  `<base>` and never from an unvalidated tip.
- The tip of the stack is the integration point: it holds the whole task. Task-level
  validation (`/pv-contract`, `/pv-review`) runs there.
- No separate integration branch exists — the stack tip is it.
- Independent subtasks still stack. Execution is strictly sequential, so a dependency-free
  subtask gains nothing from branching off `<base>`, and stacking keeps one linear review order.

**Naming:** `<type>/<feature-slug>`.

- `<type>` is the change type — `feat`, `fix`, `refactor`, `perf`, `docs`, `chore` — chosen to
  match what the branch actually delivers.
- `<feature-slug>` names that deliverable in **domain language**, derived from the subtask's
  `## Goal`. It never encodes the subtask identifier, the spec number, or the task directory
  name. See `## Pipeline identifiers stay out of the repository` below.
- Sanitize to `[a-z0-9./-]`, collapse repeats, strip leading and trailing `-`.

**Collisions.** If two subtasks would produce the same slug, extend each with the part of its
Goal that distinguishes it (`feat/oauth-token-schema` and `feat/oauth-token-rotation`), not
with a numeric suffix that mirrors execution order.

**Stack order is not encoded in the branch name.** It lives in `plan.md`, in each subtask's
`base_branch:` field, and in the stack-position line of every pull request. Naming branches
after features rather than after their position is what keeps the repository readable to
someone who has never seen this pipeline.

**Consequence to state plainly, never hide:** because branch N contains branches 1…N-1, a PR
cannot be merged into `<base>` without its predecessors. The human chooses the merge
*strategy* (merge commit / rebase / squash) and *when* to merge; the dependency order is
fixed by the code itself. Any deviation is recoverable with `/restack`.

---

## Commits

**Granularity — at least two commits per subtask**, mirroring the TDD cycle:

| Commit | When | Contents |
|---|---|---|
| `test: <what the tests assert>` | after `/pae-tests` reaches RED | test files only |
| `feat: <what was implemented>` | after `/pae-implement` reaches GREEN | implementation |

Use `fix:` for fix-subtasks, and the type that matches the change (`refactor`, `perf`,
`docs`, `chore`) when neither fits. Additional commits within a subtask are allowed when a
step is independently meaningful; fewer than two are not, because the separate RED commit is
the reviewable evidence that the tests came first.

An optional scope is permitted when it names a **feature or module** in domain language —
`feat(auth): …`, `test(billing): …`. It is never a subtask, spec, or task identifier.

When the test-level gate returned `none` (`atomic-tests: n-a`) there is no RED commit — the
subtask has a single implementation commit, and the justification lives in `state.md`.

**Message format:**

```
<type>[(<feature or module>)]: <imperative summary, <= 72 chars>

<body: what changed and why, wrapped at 72 — omit only when the summary is genuinely complete>
```

**No authorship attribution — absolute.** A commit message must contain only information
describing the change. It must never state, imply, or hint that it was produced by an AI,
an agent, or an assistant. Specifically forbidden anywhere in the message, including
trailers:

- `Co-Authored-By:` lines naming any AI, model, assistant, or tool
- `Generated with …`, `Created by …`, `Written by …` referring to a tool or model
- Emoji or badges used as tool markers (e.g. a robot glyph)
- Model names, agent names, workflow names, or subtask-orchestration jargon
- References to this pipeline's internals (`pae-implement`, `RED`, `sub-agent`, `orchestrator`)

**This overrides any tool default.** Some agent harnesses append an attribution trailer to
commit messages automatically; when this rule is in force, that trailer is not written. If a
harness has already added one, remove it before committing. The same applies to pull request
bodies — see below.

### Pipeline identifiers stay out of the repository

Commit messages, product code, comments, docstrings, test names, configuration, product
documentation, branch names, and pull request text must not reference internal planning
artifacts. Knowledge-base records and workflow definitions may use the identifiers and paths
needed to describe the process. Forbidden in product content and git metadata:

- Subtask identifiers: `T-01`, `T-04b`, `T-09-fix-<slug>`, or any `T-NN` form
- Spec identifiers: `spec-01`, `01-add-oauth`, or the spec file name
- Task directory names: `task-01-add-oauth`
- Decision and memory artifacts: `ADR-0007`, `adr/index.md`, `architecture.md`, `state.md`,
  `plan.md`, `progress.md`, `project_state.md`, or any path under `.ai/`
- Workflow and role names: `pae-implement`, `pav-check`, `spec-run`, `RED`, `Implementer`

**Why this is a correctness rule, not a style preference.** An internal planning reference
can be a dangling reference when the knowledge base is local or no longer contains the
original artifact. Product content must explain the decision itself so readers can understand
it independently of the planning record. This remains true when the repository tracks its
knowledge base.

Permitted instead: feature and module names, the branch name, and a plain description of what
changed and why.

**Traceability:** the mapping from a commit back to its subtask lives in
`state.md → branch:`. Its availability to collaborators follows the repository's tracking
policy; it does not belong in commit or pull request text.

**Staging — never blanket-add.** `git add -A`, `git add .`, `git add --all`, and
`git commit -a` are **forbidden**. Stage an explicit path list, derived from
`## Subtask Progress → target_files:` for the current T-XX, plus reviewed knowledge and state
updates allowed by the repository's tracking policy. A blanket add can publish unrelated
changes or local state that the repository has not chosen to track.

Before each commit, inspect the staged paths and diff. Include `.ai/` paths only when they
are intentional changes to tracked knowledge or state, or the user has explicitly authorized
tracking them. Unstage unrelated or unauthorized paths and record the incident in the
subtask's `notes:`. Preserve untracked consumer state as local-only by default.

---

## Pull requests

PRs are created only when `--allow-pr` was passed.

- **Base** = the previous subtask's branch (the stack parent). For T-01, base = `<base>`.
- **State during the run** = draft. A draft PR cannot be merged, which protects the run from
  the stack shifting underneath it while later subtasks are still being built.
- **Promotion to ready** happens once, as a batch, after `/phase-validation` completes for the
  whole task. Every subtask ends the run with a PR ready for review.
- A subtask whose status is `blocked`, or whose `atomic-validation` is `failed`, gets **no
  PR** — and since the stack is sequential, the run stops there anyway.
- **The orchestrator never merges.** No `gh pr merge`, no local merge into `<base>`, ever.
  Merging is the human's action and the human's alone.

**PR body** — assembled via `/suggest-pr-description`, then extended with:

1. The subtask's `## Goal` and `## Acceptance Criteria`.
2. Test evidence: the test level, the RED commit sha, and the tests that cover each criterion.
3. Its position in the stack and what it is based on, stated explicitly so a reviewer sees the
   dependency before pressing merge:
   `Stack position 3 of 8 — based on feat/oauth-token-service.`
   `Cannot merge into <base> before feat/oauth-token-schema and feat/oauth-token-service.`
   Predecessors are named by branch, never by subtask identifier.

The no-attribution rule above applies verbatim to PR titles and bodies: no tool markers, no
"generated with", no model or agent names.

---

## Safety rails

The Policy column says what an agent may do. The Enforcement column says what the git-rails
hook does when the harness runs it (Claude Code, in a registered project): `hook: deny`
blocks the command, `hook: ask` blocks it until the owner approves that one execution, or
denies it with `owner-approval-unavailable` where no person can be prompted,
`hook: allow with restack journal` lets it through only when the `/restack` recovery
journal verifies it, and `text only` means the hook does not check it. A harness without
the hook applies the whole table as text.

Enforcement values for the safety rails: `hook: deny` | `hook: ask` | `hook: allow with restack journal` | `text only`.

Protected branches for the safety rails: the target remote's default branch, `main`, `master`, `release/*`, and every pattern in `git config orchestrail.protectedBranch`.

A row that names a protected branch means a branch of this protected set. A pattern is a
shell glob in which `*` also matches `/`. For an operation on a local branch the target
remote is `origin`; without `origin`, only the fixed names and configured patterns apply.
When the target remote's default branch is unknown, a rule that needs the protected set denies
with `default-branch-unknown`; set it with `git remote set-head <remote> --auto`.

| Operation | Policy | Enforcement |
|---|---|---|
| `git push` to a subtask branch | Allowed with `--allow-pr` | `text only` |
| `git push` to `main` or any protected branch (protected set above) | **Forbidden, always** | `hook: ask` |
| `git push` to an unprotected `<base>` | **Forbidden, always** | `text only` |
| `git push --force`; a dry run (`--dry-run` or `-n`) of any forced push is allowed | **Forbidden.** Only `--force-with-lease`, only inside `/restack`, only on subtask branches of the current task | `hook: ask` |
| A `--force-with-lease` push whose explicit lease the restack journal verifies for every destination; `/restack` uses `git push --force-with-lease=refs/heads/<b>:<sha> origin <b>` | Only inside `/restack` with `--allow-pr` | `hook: allow with restack journal` |
| A lease push the restack journal does not verify, a `+` refspec, or `--force-if-includes` without a verified lease | **Forbidden** — `/restack` publishes only in the form above | `hook: ask` |
| Bulk, tag or delete push (`--all`, `--mirror`, `--tags`, `--follow-tags`, `--delete`, `:<branch>`) | Owner approval required | `hook: ask` |
| Push whose remote, destination or remote default branch cannot be resolved | **Forbidden** — name the remote and destination explicitly; set a missing default with `git remote set-head <remote> --auto` | `hook: deny` |
| Branch deletion through git (`git branch -d`/`-D`, `git update-ref -d`); gh deletions are listed in the harness capability record | **Owner approval required; a verified temporary child-branch exception is planned.** Deleting a branch on the agent's own initiative is forbidden; branches are deleted by the human when merging | `hook: ask` |
| `gh pr merge`, and the `gh api` pull-request merge endpoints | **Forbidden, always** | `hook: ask` |
| `git add -A` / `.` / `--all`, `git commit -a` | **Forbidden** — explicit paths only | `hook: deny` |
| Staging a directory, a glob, a pathspec-magic or missing path, or staging interactively | **Forbidden** — explicit file paths only | `hook: deny` |
| `git add -f` of an ignored path | Owner approval required — it would publish local state the repository ignores | `hook: ask` |
| A commit message with a `Co-Authored-By:` trailer or a subtask or decision-record identifier, or one the hook cannot read statically | **Forbidden** — see `## Commits`; pass the message with `-m` or `-F <file>` | `hook: deny` |
| A git or gh command governed by a row of this table, in a form the hook cannot verify: `GIT_*` assignments, git aliases, unsupported global options, dynamic arguments | **Forbidden** — write the command in a plain, literal form | `hook: deny` |
| `git rebase` outside `/restack` | **Forbidden** | `hook: ask` |
| `git rebase --onto <new-sha> <old-sha> <branch>` replaying the next branch the restack journal records | Only inside `/restack` | `hook: allow with restack journal` |
| `git reset --hard`, `git clean -xfd` | **Forbidden** — would destroy untracked `.ai/` state | `hook: ask` |
| Moving, renaming, copying or overwriting a protected branch (protected set above) with `branch -f`/`-m`/`-c`, `checkout -B`, `switch -C` or `update-ref` | Owner approval required | `hook: ask` |
| `git merge` or `git pull` into a protected branch (protected set above), except `git pull --ff-only` from the configured upstream, which the hook allows | **Forbidden** — merging is the human's action | `hook: ask` |
| `git commit --amend` of a commit already pushed as part of an open PR | Only inside `/restack` | `hook: ask` |
| Other local rewrites of a pushed branch: `git reset --soft`/`--mixed`/`--keep`/`--merge` on any branch, protected ones included; `git branch -f <b> <rev>`, `git checkout -B <b> <rev>`, `git switch -C` and `git update-ref` of an unprotected branch; `git pull --rebase` on an unprotected branch | Only inside `/restack`; publishing the rewrite needs a forced push, which the rows above gate | `text only` |
| Creating a pull request, its title and body, and attribution beyond the hook's patterns | Only with `--allow-pr`; no attribution | `text only` |

The rules check no read-only or unlisted operation. In a registered project the hook still
denies any git or gh command it cannot verify: opaque forms such as `xargs git …`,
`zsh -c '…'`, `git submodule foreach` and `git bisect run`, and commands over its size limit.
It also denies every relevant command while the project registry or the hook runtime is
unusable. The harness capability record lists these and what the hook does not see.

### Owner approval protocol

A `hook: ask` row grants no right: a Forbidden operation stays forbidden to every workflow,
and the hook's prompt is a second gate for the owner, not a permission. The protocol applies
to a command the owner requested and to one whose Policy allows it with owner approval.

1. Before issuing a command on a `hook: ask` row, explain in chat: the exact command, which
   rail it crosses, why it is needed, what can be lost, and how to undo it.
2. Approval covers that one execution only. A rejection is final for that operation: stop
   and report; do not retry or rephrase the command.
3. When the hook denies with `owner-approval-unavailable` (the session cannot show the prompt
   to a person), stop: give the owner the explanation and the exact command. The owner either
   runs the command outside the agent (in a terminal, or with `! <command>` in Claude Code) or
   gives other instructions.

Never wrap or rephrase a denied command to evade the check. A `hook: deny` names a fixable
form or a command the hook cannot verify: fix the command as the diagnostic says, and do not
retry it unchanged.

**Backward compatibility.** The Policy column keeps its meaning for every workflow; the
Enforcement column only records the hook's result. A reader that knows only the two-column
table reads the Policy cell as before.

---

## Recorded state — required for resume and for restack

Each leaf `## Subtask Progress` block carries these fields (canonical definition in
`workflow-globals → Canonical Status Formats`; protected per
`workflow-reference → Protected Sections Contract`):

```
branch:       feat/oauth-token-service
base_branch:  feat/oauth-token-schema
base_commit:  <sha of the branch point, written when the branch is created>
commits:      <sha> test: cover token refresh rules, <sha> feat: add token refresh service
pr:           #142 draft | #142 ready | none
```

`base_commit` is written at branch-creation time and is **never** recomputed later. It cannot
be derived after the fact: once the parent branch is squash-merged and deleted, the merge base
no longer reflects the true branch point. It is the single input that makes `/restack`
strategy-agnostic — see `restack`.

`commits:` is appended at each commit, not reconstructed at the end. Hashes recorded here are
**pre-merge**: after a squash or rebase merge they will not exist in `<base>`. Any report that
prints them says so.
