# Composite tasks: one branch and one PR, children on temporary branches, optional parallelism

## Goal

Today every child of a Type 2 composite is an ordinary leaf in the stack — its own
branch, its own PR — and the composite has no branch; execution is strictly sequential
because `## Subtask Progress` has no locking. The owner decided (ADR-0009, Decision 4)
that a composite is reviewed as one unit and that its children, when proven
independent, may run in parallel. This spec redefines the composite's git shape and
adds capability-gated parallel execution of composite children to `/spec-run`. The
top-level stack model is unchanged.

## Acceptance Criteria

### Composite branch model (sequential and parallel alike)

- [ ] A composite `T-XX` gets exactly one branch, cut from the previous top-level
      subtask's reviewed tip, and exactly one pull request; its children get no PR
- [ ] Each child runs on a temporary branch cut from the composite branch, named
      `<composite-branch>--<child-slug>`, and is merged back with a merge commit
      (`--no-ff`) that preserves the child's `test:` and `feat:` commits; squash is never
      used
- [ ] The orchestrator may delete a temporary child branch only after it merged it back;
      `rules/git-flow.md → ## Safety rails` is amended for exactly that case
- [ ] The composite's PR body carries one stack-position line and a per-child section
      with Goal, Acceptance Criteria, and test evidence (test level, RED commit sha,
      tests per criterion)
- [ ] `/phase-composite-validation` (renamed `composite-validation`) runs on the composite
      branch after the last child is merged back, before the PR is opened

### Independence check

- [ ] `/pd-decompose` writes `Parallel-safe` (`yes | no`) per child of a composite into
      `plan.md`, with evidence in `## Decomposition Decisions`: disjoint target files, no
      shared contract or schema, no dependency edge between the children, no ordering
      constraint in `## Execution Strategy`
- [ ] Before merging a child back, the orchestrator diffs the child's changed files
      against every other in-flight child's `target_files:`; on any overlap it stops
      parallel execution for that composite and serialises the remaining children

### Parallel execution

- [ ] `/spec-run --parallel <N>` (default 2, configurable) runs up to N `parallel-safe`
      children of the current composite concurrently, each in its own worktree with its
      own Implementer and Validator; children marked `no` run sequentially
- [ ] The run refuses `--parallel > 1` unless the harness's `capabilities.md` declares
      `worktrees: yes` and `concurrent-sub-agents: yes`; `sub-agents: yes` alone is not
      sufficient
- [ ] In parallel mode no sub-agent writes under `.ai/`; the orchestrator applies every
      returned delta sequentially, including the child's own `## Subtask Progress` block
- [ ] After an overlap is detected mid-wave, the remaining children are executed
      sequentially, each by a fresh Implementer, on the composite branch
- [ ] The run log records `parallel: <N>` per run and `wave: <k>` per child step;
      `/retro` reports wall-clock vs the sum of child durations
- [ ] Golden-run `composite` passes with `--parallel 1` and `--parallel 2` and produces
      the same normalised artifacts
- [ ] `rules/orchestration.md` and `rules/git-flow.md` are updated; a new ADR supersedes
      ADR-0004 Decision 3 and ADR-0005 Decision 1 on these points

## Out of Scope

- Parallelism between top-level `T-XX` subtasks (stack stays sequential)
- Parallelism in single-session `/execution` runs
- Parallel Discovery; cross-repository parallelism
- A locking state tool (spec 07, backlog)

## Notes

- Decisions: ADR-0009 Decision 4 (composite = one branch + one PR always; merge commit;
  per-child PR sections; deletion of temporary branches; children-only parallelism;
  default 2; double independence check; orchestrator-only writes; fresh Implementer on
  serialisation) and Decision 2 (`worktrees`, `concurrent-sub-agents` capabilities).
- Clarifications 2026-09-17: the spec was renamed from
  `parallel-independent-subtasks`; the wave/integration-branch model was withdrawn.
- Depends on specs 13 (capabilities), 09 (golden `composite` case), 02–03 (log fields).
- Composite children still each pass the full atomic cycle (`atomic-tests: red` before
  GREEN); the two-commit rule applies per child on its temporary branch.
