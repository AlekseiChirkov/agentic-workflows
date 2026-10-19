# ADR-0009: Decisions for Task unknown — Roadmap decisions of September 2026 (three clarification rounds)

## Status

Accepted

## Date

2026-09-17

## Related Task

- Task: none — decisions taken by the owner in three question rounds over the roadmap
  specs 01–13 (2026-09-16 … 2026-09-17)
- Related files: `.ai/specs/*.md`, `.ai/adr/0003`, `0004`, `0005`, `0007`, `0008`

## Summary

The owner answered 116 questions across three rounds. This record collects every
decision that changes a spec's premise, a contract, or the repository's shape, so that
the specs can cite one source. Decisions are grouped by subject; each names the specs it
binds.

## Context

The roadmap (`.ai/specs/README.md`) was drafted from the 2026-09-16 comparative analysis
with assumptions where the owner's intent was unknown. Round 1 (76 questions) settled
defaults; round 2 (28) resolved the consequences of nine answers that changed a spec's
premise; round 3 (12) closed the remaining design consequences. Specs are amended to
match this record.

## Decisions

### Decision 1: Identity, publication, versioning

**Timing amended 2026-10-19 (owner):** the repository already has Git history. Local test-first commits are permitted; pushes and pull requests are withheld pending separate history remediation. ADR-0010 replaces only the original pre-initialization timing clause; all other roadmap decisions remain accepted.

**Amended 2026-09-17 (owner):** sensitive data is scrubbed **before** `git init`, not at
the public release. Client and employer project names, internal source-file references
taken from client code, pull-request and workflow-run identifiers, the machine host name,
and `$HOME`-absolute paths are removed in `.ai/specs/00-sensitive-data-scrub.md`, which
also adds a forbidden-token check group to `validate-contracts.sh`. Rationale: git
history cannot be edited after publication; a later scrub would require a rewrite that
invalidates every published hash. Spec 11 only re-verifies the check.

**What was decided:**
- Public name **Orchestrail**. Rename in spec 01: repository directory `orchestrail/`,
  environment `ORCHESTRAIL_HOME`, config `~/.config/orchestrail/`, log root
  `ORCHESTRAIL_LOG_ROOT`; every hard-coded literal updated in the same commit.
- Public GitHub repository under the owner's personal account, published after a minimal
  public slice inside spec 01: `LICENSE` (Apache-2.0, holder = the owner), a short
  `README.md`, `.gitignore`, the name. Everything else stays in spec 11.
- SemVer; first tag `v0.9.0` on the single import commit; `1.0.0` = first stable public
  contract. Versions below 1.0.0 are unstable.
- `VERSION` file at the repository root holds the contract version; `/pd-analyze` writes
  `contract_version:` into task `state.md`; a rule change without a bump is a warning, not
  a failure.
- Default branch `main`; branch protection at the public release.
- P3 (additive contracts) holds for formats consumer projects already have on disk; new
  formats may change freely until 1.0.
- `.ai/` is tracked in full including `tasks/todo/`; `docs/` and `logs/.gitignore` are
  tracked; `logs/runs/` is ignored.
- Skill names keep `rule-*` / `principle-*`; a brand prefix is added to a generic
  workflow name only on a real collision with a known public skill.

**Why:** early feedback on a pre-1.0 contract; one rename sweep instead of two.

**Alternatives:** publish only at spec 11 (rejected: delays feedback); keep
`agentic_workflows` (rejected: generic and already used).

**Consequences:** spec 01 grows the rename and the minimal public slice; spec 11 keeps
installer, profiles, examples, scrubbing.

**Related files:** `.ai/specs/01`, `11`

### Decision 2: Harness abstraction — Claude Code and Codex now, others later

**What was decided:**
- Windsurf / Devin Desktop are dropped (spec 13). Old directories under `~/.codeium` and
  consumer `.windsurf/` / `.devin/` are never deleted by scripts; the removal command is
  printed for the owner.
- A `harness/<name>/` directory per supported harness, starting with `claude/` and
  `codex/`, each containing `always-on.md` (core body), `capabilities.md`, `deploy.env`
  (target paths), and an optional `hooks.json` fragment. `sync.sh` iterates the directory;
  no hard-coded provider branches.
- Workflows branch on **capabilities**, never on harness name. `sync.sh` embeds the
  harness's capability table into the always-on file it deploys for that harness; skills
  read the contract from there. No per-skill templating, no environment-variable
  detection.
- Both Claude Code and Codex are full executors of the single-session pipeline.
  `/spec-run` is a universal orchestrator that requires the capabilities `sub-agents`,
  `agent-messaging`, `git`, and — with `--parallel > 1` — `worktrees` plus an explicit
  `concurrent-sub-agents` declaration; a harness lacking any of them cannot run it. Today
  only Claude Code declares them.
- Consumer project registry at `~/.config/orchestrail/projects`, appended by
  `setup-new-project.sh`, iterated by `sync.sh`. A registered project with any task whose
  `state.md → ## Phases` has a phase `in-progress` is skipped by `sync.sh` with a report
  line; `--force` overrides.
- Rule front matter: `description:` + `load: always | on-demand`, no `trigger:`.
  Workflow front matter: `description:`, `phase:`, `step:`, and (spec 08) `loads:`.

**Why:** the owner's instruction "workflows work with models, not IDEs"; a third
provider must be a directory, not a rewrite.

**Alternatives:** two hard-coded branches in `sync.sh` (rejected); per-skill harness
templating (rejected: fragile, duplicates every skill).

**Consequences:** spec 13 gains the `harness/` layout and capability contract; ADR-0003's
deploy-target decision is superseded when spec 13 lands.

**Related files:** `.ai/specs/13`, `13a`

### Decision 3: Naming scheme for rules and workflows

**What was decided:**
- Rule kinds: `bootstrap`, `contract`, `protocol`, `procedure`. Every rule file is
  `<kind>-<subject>` with no exceptions (`contract-tdd`, `contract-git-flow`,
  `bootstrap-discovery`, `procedure-blocker-reconciliation`, …).
- `workflow-reference` is split now into `contract-state-files`,
  `protocol-autonomous-decision`, `protocol-subtask-classifier`; `##` headings are frozen.
- The always-on files leave `rules/` for `harness/<name>/always-on.md`.
- Slash commands are renamed inside spec 13 as its final subtask: orchestrators
  `discovery`, `execution`, `validation`, `pipeline`, `atomic-execution`,
  `atomic-validation`, `composite-validation`; children keep the step suffix
  (`discovery-analyze`, `execution-finalize`, `validation-issues`,
  `atomic-execution-tests`, `atomic-validation-check`). Entry points and utilities are
  unchanged (`spec-run`, `spec-draft`, `spec-sync`, `bugfix`, `adr-new`, `context-pack`,
  `retro`, `restack`, `compress-state`, `onboard-legacy-project`, `suggest-*`).
- The audit of all rule and workflow files is its own spec, **13a**, executed before 13;
  spec 13 is amended via `/spec-sync` from its findings.

**Why:** a name must state the file's kind; one rename sweep.

**Alternatives:** prefix only the five colliding names (rejected: four naming styles
remain); rename commands at spec 11 (rejected: second full-tree sweep).

**Consequences:** every citation in `workflows/`, `rules/`, `docs/`, `templates/`,
`.ai/`, and scripts changes once, under `validate-contracts.sh` checks.

**Related files:** `.ai/specs/13`, `13a`

### Decision 4: Composite tasks — one branch, one PR; parallelism only inside a composite

**What was decided:**
- A Type 2 composite always has **one branch and one pull request**, in sequential and
  parallel mode alike. Its children run on temporary branches cut from the composite
  branch and are merged back with a **merge commit** (`--no-ff`), preserving each child's
  `test:` / `feat:` commits as TDD evidence. No squash.
- The composite's PR body carries one stack-position line and a per-child section (Goal,
  Acceptance Criteria, test evidence).
- The orchestrator may delete a temporary child branch only if it created it and it is
  already merged back; the branch-deletion rail is amended for that case only.
- Parallel execution is allowed **only between children of one composite**; top-level
  `T-XX` remain strictly sequential in the stacked model (branch N cut from N-1's reviewed
  tip; PR base = previous branch). Default `--parallel 2`, configurable; `/spec-run` only.
- Independence is checked twice: `/pd-decompose` writes `parallel-safe: yes|no` with
  evidence (disjoint target files, no shared contract/schema, no dependency edge) to
  `plan.md`; the orchestrator re-verifies the actual diff before merge-back and, on
  overlap, serialises: remaining children run sequentially, each by a fresh Implementer on
  the composite branch.
- In parallel mode only the orchestrator writes under `.ai/`; sub-agents return deltas.

**Why:** narrow, reviewable scope for parallelism; the stack model and its evidence stay
intact.

**Alternatives:** waves of independent top-level subtasks with an integration branch
(rejected: changes the stack contract); squash merge-back (rejected: loses RED commit).

**Consequences:** ADR-0005 Decision 1 is amended for composite children (no separate PR
per child); ADR-0004 Decision 3 is narrowed (sequential *between* top-level subtasks).
Spec 12 is rewritten to this scope.

**Related files:** `.ai/specs/12`, `rules/git-flow.md`, `rules/orchestration.md`

### Decision 5: Telemetry instead of budgets; state tool deferred

**What was decided:**
- No wall-clock or cost limits on subtasks or runs. Spec 05 becomes telemetry-only:
  `tokens_in`, `tokens_out`, `cost_usd`, `duration_s` per step and per run; cost metrics
  in `/retro`; Codex `cost_usd` omitted until reliable.
- Anomalous-duration warning, written to the subtask's `notes:` and the final report:
  duration > 2 h while fewer than 5 samples exist for that step; afterwards > 3× the
  step's median with an absolute floor of 2 h. Never stops a run.
- Run-log vocabulary is enforced in `log-step.sh` with a normalisation map
  (`completed`→`ok`, `implemented`→`ok`, `restarted`→`failed`, `needs-work`→`failed`,
  `PASS`→`pass`, `NEEDS WORK — …`→`needs-work`, `escalated`→`fail`), original kept in
  `note`; any other value is rejected; unknown `--step` names warn (list derived from
  `workflows/*.md`); historical runs are left as-is and reported as rejected.
- Hooks (specs 03, 06) are installed at **user level** and activate only inside a
  registered project. Step logging moves to `SubagentStop` and `Stop` hooks;
  `run-start`/`run-end` stay prompt-driven; Codex durations stay prompt-driven and are
  labelled approximate.
- Git-rails hook: protects the default branch and `release/*`; blocks commits whose
  message contains `Co-Authored-By`, `T-XX`, or `ADR-`; detects tracked `.ai/` via
  `git ls-files .ai` cached per session; writes incidents to stderr only. RED-set
  protection is a separate future spec.
- The state tool (spec 07) is **not** built now; agents keep editing state files
  directly. It stays in the backlog as: Python 3, single file, stdlib only, invoked from
  `ORCHESTRAIL_HOME/bin/`, owning `## Subtask Progress` only, per-task lock with 10-minute
  stale override. Interim guard: `validate-task.sh` runs warn-only from every finalize /
  close workflow.

**Why:** visibility first, limits from evidence later; avoid a runtime dependency before
its value is measured.

**Alternatives:** hard budgets (rejected by owner); mandatory state tool (rejected for
now).

**Consequences:** spec 05 rewritten; spec 07 moved to backlog; spec 12 designed without a
lock (orchestrator-only writes).

**Related files:** `.ai/specs/02`, `03`, `05`, `06`, `07`

### Decision 6: Models, profiles, documentation, tests

**What was decided:**
- Model catalog: hand-maintained at `~/.config/orchestrail/model-catalog.md`, TTL 14
  days, staleness warning after 30 days, web refresh only on `--refresh`. Selection by
  cost tier with optional trait override. `plan.md` carries two columns, `Model (Claude)`
  and `Model (Codex)`, filled from the same tier table by cost-band equivalence; an empty
  cell means the session default.
- Technology-neutral core: `code-quality` and `testing-standards` stay core;
  Python/FastAPI/infra material becomes an optional profile (`profiles/python-fastapi/`).
  `setup-new-project.sh --profile <name>` copies profile principles into the consumer
  project's `.ai/principles/` and `.ai/context/` and writes the profile fragment into the
  **project-local** `CLAUDE.md` / `AGENTS.md`; global always-on files stay core-only;
  profiles are never global skills; the selection is recorded in `.ai/profile` (name +
  source version).
- Context tiering (spec 08) after spec 13: ≤ 700 words per always-on rule, ≤ 6 000 words
  total; worked examples and incident narratives in `rules/reference/` deployed as
  `ref-*` skills.
- Generated docs (spec 10): separate files under `docs/reference/`, linked from
  `USAGE.md`; always-on files generated from a core body plus per-harness header
  template; generator in Python.
- Golden-run tests (spec 09): run only before a release; pinned Sonnet 5; fixture a
  ~5-file pure-Python + pytest project; offline; CI secret allowed for manual dispatch
  only. `docs/examples/` is built from the golden fixture, never from a client project.
- Before publication: client and internal project names scrubbed; `settings.local.json`
  and run logs never published; Russian originals kept with English translations
  alongside; `sync.sh` replaced for external users by an installer with `--dry-run`,
  `CLAUDE.md` backup, and `--uninstall`; documentation site later.
- Python 3 allowed for optional tools (state tool, generators, normaliser); bash for
  `sync.sh`, `setup-*`, `log-step.sh`.
- Pull requests are reviewed by the owner; agent review is advisory.

**Why:** owner's answers, rounds 1–3.

**Alternatives:** recorded per item in the specs' `## Notes`.

**Consequences:** specs 04, 08, 09, 10, 11 amended.

**Related files:** `.ai/specs/04`, `08`, `09`, `10`, `11`

### Decision 7: Execution order

**What was decided:**
spec 00 (scrub) → 01 → 13a → 13; then 04 independently; then 02 → 03 → 05 → 06 (log
contract, then automatic recording, then telemetry, then protection hooks); then 09, 08,
10, 11, 12. Spec 07 is backlog.

**Why:** nothing may be committed before the scrub; spec 13 touches every file, so doing
others first means editing rules twice.

**Related files:** `.ai/specs/README.md`

## Questions and Answers

The three rounds (116 questions) were answered by the owner on 2026-09-17; the answers
are folded into this record and into each spec's `## Clarifications`. The question files
were removed after folding.

## Rejected Options

Listed per decision above.

## Implications for Future Work

- When spec 13 lands: ADR-0003 status → superseded (deploy targets); write the harness
  capability contract into `.ai/principles/domain.md`.
- When spec 12 lands: amend ADR-0004 (Decision 3) and ADR-0005 (Decision 1) formally with
  a superseding ADR.
- A future spec for RED-set protection (hook refusing test-file edits during GREEN).
- A future spec for `/spec-run` on a second orchestrating harness once one declares the
  required capabilities.

## Verification

Each amended spec cites this ADR in `## Decisions`; `.ai/specs/README.md` order matches
Decision 7.
