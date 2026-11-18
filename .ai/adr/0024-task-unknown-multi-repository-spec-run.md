# ADR-0024: One shared specification across several git repositories in `/spec-run`

## Status

Accepted

## Date

2026-11-17

## Related Task

- Task: owner request of 2026-11-17 to run one shared specification of a project whose root
  holds the knowledge base but is not a git repository, with code in two nested repositories
  (`backend/`, `frontend/`, base branch `dev`), in one `/spec-run`.
- Related files: `workflows/spec-run.md`, `rules/git-flow.md`, `rules/workflow-globals.md`,
  `rules/workflow-reference.md`, `rules/orchestration.md`, `workflows/phase-discovery.md`,
  `workflows/pd-decompose.md`, `workflows/pv-classify-fixes.md`, `workflows/pv-create-fixes.md`,
  `workflows/restack.md`, `workflows/compress-state.md`, `scripts/repo-set.py`,
  `scripts/check-repo-set.py`.

## Summary

`/spec-run` gains a multi-repository mode. Participating repositories and their base
branches are declared with `--repo <directory>=<base-branch>` and recorded in task
`state.md → ## Repositories`. One plan and one strictly sequential topological order drive
one independent branch stack per repository. A read-only standard-library helper,
`scripts/repo-set.py`, supplies the per-repository preflight, the routing of leaves to
repositories and stacks, and the reconciliation of recorded checkpoints. Single-repository
runs are unchanged and do not use the helper.

## Context

`git-flow` stated "Single-repo only", and `/spec-run` told the user to split cross-repository
work into separate specifications. Discovery already modelled cross-repository work
(`working_dir:` per subtask, the `Repo` plan column, Type 3 producer/consumer re-slicing),
but every later step assumed one `WORK_DIR`, one preflight, one stack, one stack tip and one
git checkpoint per run. Splitting a feature such as a user dashboard into two specifications
loses the shared requirement set and the dependency order between the API and its consumer.

Constraints: the project root must not become a git repository and no file may move; the
repositories share no git history; execution stays sequential with one writer per shared
file (ADR-0004); `--dry-run` writes nothing; no push or `gh` without `--allow-pr`; the
contract validator inventory is frozen (ADR-0018), so new checks are standalone
(ADR-0019 Decision 3).

## Decisions

### Decision 1: Explicit repository set

**What was decided:** the run is multi-repository when the project root is not inside a git
work tree and `--repo <directory>=<base-branch>` flags (or, on resume, the recorded
`## Repositories` section) declare the participants. Each name is a direct child directory
of the root that is a repository root. The base branch is mandatory and must be a local
branch. Different flags on resume stop the run.

**Why:** auto-detection would include unrelated nested repositories, and inferring the base
from the checked-out branch or the remote default is wrong for projects whose working base is
`dev`. Direct children keep `<repository>/../.ai` equal to the shared knowledge base, so the
existing umbrella-first Context Bootstrap of workers loads it unchanged.

**Alternatives:** a manifest file in the shared `.ai/` (writes into the user's project);
auto-detection with the checked-out branch as base (silent wrong base).

### Decision 2: A read-only helper for the git facts

**What was decided:** `scripts/repo-set.py` (`mode`, `preflight`, `route`, `reconcile`) prints
one JSON object per call, exits 1 on any failed check and 2 on invalid input, runs git with
`GIT_OPTIONAL_LOCKS=0` and without inherited `GIT_*` variables, never writes, never contacts
a remote, and runs `gh auth status` only with `--allow-pr`. `/spec-run` calls it only in
multi-repository mode.

**Why:** per-repository preflight, topological routing and checkpoint reconciliation are
deterministic and testable against disposable repositories; prose alone cannot be tested
behaviourally (P10). Keeping single-repository runs off the helper preserves their existing,
Python-free behaviour exactly.

**Alternatives:** prose-only changes with text checks.

### Decision 3: One stack per repository, one shared order

**What was decided:** every leaf, composite and fix belongs to exactly one repository
(`Repo` cell plus a `working_dir:` that resolves to it). Work touching several repositories
is split into one leaf per repository that keeps the same spec requirement identifiers, the
consumer depending on the producer. Leaves run strictly sequentially in the plan's shared
topological order; within a repository the existing stack rule applies (first leaf from the
base branch, each later leaf from the previous reviewed leaf of that repository). A leaf
starts only when every dependency in any repository is `reviewed`.

**Why:** it keeps the shared requirement trace and the dependency order while respecting that
each repository has its own history. Sequential execution keeps the single-writer rule.

### Decision 4: Cross-repository dependencies are ordering facts, never git bases

**What was decided:** dependencies between repositories are recorded in
`plan.md → ## Execution Strategy` (`Cross-repository dependencies:`), in
`state.md → ## Repositories → cross_repo_dependencies:` and in pull request bodies. No branch,
commit or pull request names another repository's branch as its base. Draft PRs are promoted
only after validation of the whole run, per repository in stack order. The final report gives
one stack per repository and one integration order.

### Decision 5: Additive state format

**What was decided:** a `repo:` field before the git fields of an orchestrated leaf block and
a task-level `## Repositories` section, both protected. A task without the section is a
single-repository task for every reader (P3).

## Consequences

- `/restack` takes `--repo <directory>` on a multi-repository task and repairs one
  repository's stack at a time; journals already live in each repository's git directory.
- A missing branch, an unexpected tip, a recorded commit off its branch or a checkpoint
  without `repo:` stops a resume for explicit resolution; absence never proves a merge.
- `working_dir:` is resolved relative to the T-XX directory, as `/pd-decompose` defines; the
  subtask template and the umbrella README example were corrected to that depth.
- The new acceptance suite `scripts/check-repo-set.py` runs standalone, outside the frozen
  validator inventory; a full validator run does not execute it.
- Python 3.9+ is required for multi-repository runs only.
- Atomic workers resolve `AI_DIR = <repository>/.ai`; when a repository has no local
  runbook they use the umbrella runbook and run its commands from the umbrella root, where
  such commands are written (`phase-atomic-execution → ## Context Bootstrap`). Projects with a
  local runbook are unaffected.

## Verification

The suite failed on the unchanged source (helper missing, contract text missing) and passes
after the change: single-repository classification, two-repository preflight, a dirty tree
in one repository, a missing base branch, an unfinished operation, branch collisions,
independent stacks, cross-repository dependencies, resume selection, missing branch,
unexpected tip, base not an ancestor, read-only behaviour and publication gating.
