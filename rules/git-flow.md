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

| Operation | Policy |
|---|---|
| `git push` to a subtask branch | Allowed with `--allow-pr` |
| `git push` to `<base>` / `main` / any protected branch | **Forbidden, always** |
| `git push --force` | **Forbidden.** Only `--force-with-lease`, only inside `/restack`, only on subtask branches of the current task |
| Branch deletion | **Forbidden.** Branches are deleted by the human when merging |
| `gh pr merge` | **Forbidden, always** |
| `git add -A` / `.` / `--all`, `git commit -a` | **Forbidden** — explicit paths only |
| `git rebase` outside `/restack` | **Forbidden** |
| `git reset --hard`, `git clean -xfd` | **Forbidden** — would destroy untracked `.ai/` state |
| Rewriting a commit already pushed as part of an open PR | Only inside `/restack` |

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
