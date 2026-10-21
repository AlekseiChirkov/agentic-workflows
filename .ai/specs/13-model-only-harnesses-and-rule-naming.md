# Model-only harnesses (Claude Code + Codex), a harness abstraction, and a self-describing `rules/` ↔ `workflows/` layout

<!-- SDD spec. Authored from the 2026-09-16 naming review, brain-storm mode, on 2026-09-16. Amended 2026-09-17 per ADR-0009. -->

## Source

Owner instruction, 2026-09-16 (translated from Russian):

> Write a spec for this problem. The goal of the spec is a full analysis of these files,
> finding the problems, and moving away from Windsurf so that only Claude and Codex remain.
> Workflows must work only with models, not with IDEs. Within this spec we keep support for
> Codex and Claude only. The spec must follow all SDD standards and solve the problems you
> found between rules and workflows.

Input analysis: `docs/analysis/2026-09-16-rules-workflows-naming-review.md`.

## Context & Problem

Historical snapshot: the following analysis was written on 2026-09-16. Script paths
are normalized to their current `scripts/` location, but old line numbers/counts are
historical evidence, not a current inventory. Spec 13a must refresh findings and the
heading map from the actual checkout before any rename. Runtime capabilities must be
verified against installed versions; old harness-name assumptions are superseded below.


The repository deploys to three harnesses. Windsurf / Devin Desktop is an IDE with two
namespaces (`global_workflows/`, `global_rules/`) addressed by bare basename
(`scripts/sync.sh:51-67`); Claude Code and Codex are model harnesses with one namespace, skills
(`scripts/sync.sh:72-140`). That difference shaped the source tree:

- Five basenames exist in both `rules/` and `workflows/` — `phase-discovery`,
  `phase-execution`, `phase-validation`, `phase-atomic-execution`,
  `phase-atomic-validation`. On Windsurf the namespaces keep them apart; on Claude Code and
  Codex they collided, the 2026-07 audit found the rule side undeployed (finding B-3,
  `docs/audits/2026-07-21-logic-audit-fixes.md:41-52`), and the fix was a deploy-time
  `rule-` prefix plus a prose resolution rule every reader must know
  (`rules/workflow-globals.md:19-27`).
- The rule side of each pair is not "the rules of that phase" but a **context bootstrap**
  (load list + behaviours, `rules/phase-execution.md:8-26`), and two of them carry
  unrelated procedures: Blocker Reconciliation (`rules/phase-atomic-execution.md:45-63`,
  ≈350 of 644 words) and the Discovery Decision Protocol
  (`rules/phase-discovery.md:36-64`).
- Windsurf's `trigger: always_on | model_decision` front matter is on every rule
  (`rules/tdd.md:2`, `rules/workflow-reference.md:2`) although it means nothing to Claude
  Code or Codex, where a skill is model-invoked regardless
  (`rules/workflow-globals.md:29-33`).
- Citations are ambiguous where names collide: `workflows/phase-pipeline.md:185` reads
  "follow `phase-execution.md` inline" — the workflow is meant, the rule is equally
  plausible.
- `workflows/PIPELINE.md` is documentation (`docs/USAGE.md:108`) but is deployed as a
  skill because it sits in the copied directory (`scripts/sync.sh:54`, `scripts/sync.sh:75`).
- The Windsurf/Devin path adds a per-project pass that discovers projects by a `.devin`
  marker directory (`scripts/sync.sh:177-230`) and a setup step that writes `.windsurf/rules/`
  and `.devin/rules/` copies into every consumer project (`scripts/setup-new-project.sh:80-135`).
  Fifty lines across `rules/`, scripts, and `scripts/validate-contracts.sh` mention Windsurf,
  Devin, or Codeium.
- Rule names follow four different styles (subject: `tdd`; location: `workflow-globals`;
  deploy target: `global-claude`; phase: `phase-*`), and `workflow-reference.md` holds
  26 top-level sections of five different kinds in 514 lines.

Consequence of doing nothing: every new rule inherits the collision workaround and a
harness it no longer targets; a contributor cannot tell a file's kind from its name; the
prose resolution rule and the Windsurf-only front matter are always-on context spent on
a harness the owner has dropped.

## Goal

A contributor or an agent can tell from a file's name and front matter what it is
(bootstrap, contract, protocol, procedure, always-on summary, workflow) and where it is
loaded, without a legend and without a per-harness resolution rule; the system targets
exactly two model harnesses, Claude Code and Codex, and nothing in the source tree,
scripts, or contract checks refers to an IDE.

## Scope

- Removal of Windsurf / Devin Desktop from `scripts/sync.sh`, `scripts/setup-new-project.sh`,
  `scripts/setup-all-repos.sh`, `scripts/validate-contracts.sh`, rule front matter, `workflow-globals`,
  templates, and `docs/USAGE.md`.
- A harness-neutral front-matter schema for rules and workflows.
- A consumer-project registry replacing the `.devin` marker for `scripts/sync.sh`'s per-project pass.
- Cleanup of stale skill directories previously deployed by this system.
- Renaming the five colliding rules to `bootstrap-<phase>` and extracting the two
  embedded procedures into their own rule files.
- Renaming the remaining rules to a `<kind>-<subject>` scheme and splitting
  `workflow-reference` by kind.
- A `harness/<name>/` abstraction (Claude Code, Codex) with a declared capability
  contract that `scripts/sync.sh` iterates and workflows branch on.
- Renaming the slash commands to the `discovery-*` / `execution-*` / `validation-*` /
  `atomic-execution-*` / `atomic-validation-*` scheme, as the final subtask.
- Moving `PIPELINE.md` to `docs/`.
- Contract checks that prevent each class of problem from recurring.
- An ADR recording the harness decision and the naming scheme.

## Out of Scope

- The audit itself — it is `.ai/specs/13a-rules-workflows-audit.md`, executed first; this
  spec is amended from its findings before any rename starts.
- Generating `docs/USAGE.md` tables from front matter (`.ai/specs/10-generated-reference-docs.md`).
- Deleting `~/.codeium/windsurf/global_workflows/` and `global_rules/` on the owner's
  machine, or `.windsurf/` / `.devin/` directories in consumer projects — reported, not
  removed.
- Changing the content of any contract (status vocabularies, TDD rule, git rails,
  orchestration roles). Text moves; meaning does not.
- Hooks, budgets, state tool, context tiering (specs 03, 05, 06, 07, 08).
- Any support for a third harness (Cursor, Gemini CLI, Aider).

## Actors & Roles

| Actor | Description | What they can do in this feature |
|---|---|---|
| Owner / maintainer | Edits the source tree, runs `scripts/sync.sh` | Runs the audit, applies renames, accepts the ADR |
| Contributor | Reads the tree to change one rule or workflow | Identifies a file's kind and load mode from its name and front matter |
| Claude Code agent | Executes workflows as skills; reads `~/.claude/CLAUDE.md` | Resolves any rule citation to `rule-<name>` with no per-harness branch |
| Codex agent | Executes workflows as skills; reads `~/.codex/AGENTS.md` | Same capability-gated workflow behavior; orchestration only when required capabilities are declared and available |
| `scripts/sync.sh` | Deploys the tree | Deploys to two harnesses only; cleans stale skills; refreshes registered projects |
| `scripts/setup-new-project.sh` | Seeds a consumer project | Writes Claude Code and Codex artifacts only; registers the project |
| `scripts/validate-contracts.sh` | Gate before deploy | Fails on any regression this spec forbids |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Harness | The agent runtime a workflow executes in: Claude Code or Codex after this spec | `.ai/principles/domain.md` (new entry required) |
| Rule | An always-on or on-demand contract in `rules/`, deployed as a `rule-<name>` skill | `.ai/principles/domain.md → Rule` |
| Workflow | A slash-command definition in `workflows/`, deployed as a skill | `.ai/principles/domain.md → Workflow` |
| Bootstrap | A rule whose content is a phase's `.ai/` load list and phase behaviours; file name `bootstrap-<phase>` | this spec |
| Contract | A rule defining canonical formats or vocabularies other files consume | this spec |
| Protocol | A rule defining a decision or classification procedure invoked by workflows | this spec |
| Procedure | A rule defining a mechanical repair or reconciliation sequence | this spec |
| Always-on file | `harness/<name>/always-on.md`, deployed as the harness's global instruction (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`), carrying the capability table | ADR-0009 Decision 2 |
| Load mode | `always` (in the harness global instruction) or `on-demand` (a skill loaded when cited) | this spec, replaces Windsurf `trigger:` |
| Consumer project | A repository seeded by `scripts/setup-new-project.sh` | `.ai/context/environment.md` |
| Project registry | `~/.config/orchestrail/projects`, one absolute path per line | this spec |
| Kind | The classification of a rule file: bootstrap, contract, protocol, procedure | ADR-0009 Decision 3 |
| Harness directory | `harness/<name>/` holding `always-on.md`, `capabilities.md`, `deploy.env`, optional `hooks.json` | ADR-0009 Decision 2 |
| Capability | A declared harness ability workflows may branch on: `sub-agents`, `concurrent-sub-agents`, `agent-messaging`, `hooks`, `worktrees`, `git`, `always-on-path` | ADR-0009 Decision 2 |

Synonyms not to be used: "IDE" for a harness (the targets are model harnesses); "trigger"
for load mode; "global rule" for a rule.

## Requirements

### Audit (withdrawn — moved to spec 13a on 2026-09-17)

- **REQ-01** (withdrawn → 13a) | WHEN the task starts, THE SYSTEM SHALL write
  `docs/audits/YYYY-MM-DD-rules-workflows-audit.md` listing every file in `rules/` and
  `workflows/` with: kind, load mode, word count, files it cites, files that cite it, and
  every line mentioning Windsurf, Devin, or Codeium.
- **REQ-02** (withdrawn → 13a) | THE SYSTEM SHALL flag in the audit every rule file whose content spans more
  than one kind, naming the section boundaries.
- **REQ-03** (withdrawn → 13a) | THE SYSTEM SHALL flag in the audit every citation that is ambiguous
  (carries a `.md` suffix for a colliding basename, or names a section that does not
  exist in the cited file).
- **REQ-04** (withdrawn → 13a) | THE SYSTEM SHALL flag in the audit every statement that appears verbatim
  or near-verbatim in two or more of `rules/`, `workflows/`, `docs/USAGE.md`, and
  `workflows/PIPELINE.md`.

### Harness reduction

- **REQ-05** | THE SYSTEM SHALL deploy, via `scripts/sync.sh`, by iterating `harness/*/deploy.env`
  (initially `claude`, `codex`) with no provider-specific branch in the script, and SHALL
  NOT create or write any path under `~/.codeium/`.
- **REQ-06** | THE SYSTEM SHALL NOT create `.windsurf/` or `.devin/` directories or files
  in a consumer project from `scripts/setup-new-project.sh` or `scripts/setup-all-repos.sh`.
- **REQ-07** | IF `scripts/setup-new-project.sh` finds an existing `.windsurf/` or `.devin/`
  directory in the project, THEN THE SYSTEM SHALL print one line naming it as a legacy
  artifact safe to delete, and SHALL leave it unchanged.
- **REQ-08** | WHEN `scripts/setup-new-project.sh` completes, THE SYSTEM SHALL append the
  project's absolute path to `~/.config/orchestrail/projects` unless it is already present.
- **REQ-09** | WHEN `scripts/sync.sh` runs its per-project pass, THE SYSTEM SHALL iterate the
  project registry, skip entries whose path no longer exists (reporting each), skip — with
  a report line — any project in which a task `state.md → ## Phases` has a phase
  `in-progress` unless `--force` is passed, and refresh `.claude/skills/` symlinks and
  `CLAUDE.md`/`AGENTS.md`-adjacent artifacts for each remaining entry.
- **REQ-10** | WHEN `scripts/sync.sh` deploys skills, THE SYSTEM SHALL write a manifest of every
  skill directory it created and SHALL remove, under `~/.claude/skills/` and
  `~/.codex/skills/`, any directory listed in the previous manifest that no longer
  corresponds to a source file.
- **REQ-11** | THE SYSTEM SHALL remove operational references to dropped harnesses from
  `rules/`, `workflows/`, `harness/`, `principles/`, `templates/`, `scripts/*.sh`, `CLAUDE.md`
  and `docs/USAGE.md`. The sole production-code exception is the dedicated read-only
  `scripts/report-legacy-artifacts.sh` that detects/reports the paths required by REQ-07
  and never writes/deletes them. Its synthetic tests and historical documents
  (`docs/audits/`, `docs/analysis/`, `.ai/memory/progress.md`, `.ai/adr/`, completed
  task/spec records and verbatim source quotations) are exempt. Contract checks SHALL
  enforce the reporter's read-only behavior and reject new unreviewed exceptions.
- **REQ-12** | THE SYSTEM SHALL carry, in every `rules/*.md` front matter, exactly the keys
  `description:` (one line) and `load: always | on-demand`, and no `trigger:` key.
- **REQ-13** | THE SYSTEM SHALL carry, in every `workflows/*.md` front matter, the keys
  `description:`, `phase:` (one of `discovery | execution | validation |
  atomic-execution | atomic-validation | orchestrated | entry | utility`) and `step:`
  (an integer or `-`).
- **REQ-14** | THE SYSTEM SHALL resolve a rule citation `` `name` `` to the skill
  `rule-name` on both harnesses, and `rules/contract-phases.md` (renamed per REQ-24)
  SHALL state that in one sentence with no per-harness branch.
- **REQ-15** | THE SYSTEM SHALL present the Context Bootstrap table with one skill column
  per phase (no "rules file" column).
- **REQ-16** | WHERE a mechanism requires a capability (sub-agent spawning → `sub-agents`;
  Arbiter kept alive and Implementer resumed → `agent-messaging`; hooks → `hooks`;
  parallel children → `worktrees` + `concurrent-sub-agents`), THE SYSTEM SHALL name the
  capability in the rule that defines the mechanism and SHALL state the behaviour when the
  capability is absent (single-session execution of the same steps, or refusal to start
  for `/spec-run`); no rule or workflow SHALL branch on a harness name. If declared
  capabilities are not exposed/authorized in the active session, it SHALL stop naming
  the unavailable prerequisite or use the declared single-session fallback, never
  silently claim that a restricted tool was used.
- **REQ-35** | THE SYSTEM SHALL hold, for each supported harness, a directory
  `harness/<name>/` containing `always-on.md`, `capabilities.md`, `deploy.env`
  (`skills_dir`, `always_on_path`), and optionally `hooks.json`.
- **REQ-36** | WHEN `scripts/sync.sh` deploys a harness's always-on file, THE SYSTEM SHALL embed
  that harness's capability table from `capabilities.md` into the deployed copy, and every
  workflow that needs a capability SHALL read it from the always-on contract (no per-skill
  templating, no environment-variable detection).
- **REQ-37** | IF `/spec-run` starts on a harness whose capability table lacks
  `sub-agents`, `agent-messaging`, or `git`, THEN THE SYSTEM SHALL refuse to start naming
  the missing capability; WITH `--parallel > 1` the same applies to `worktrees` and
  `concurrent-sub-agents`.
- **REQ-38** | THE SYSTEM SHALL declare each harness's verified capabilities independently,
  with tested runtime/version, verification date and evidence. Both support the full
  single-session workflow where prerequisites are available. Sub-agents, messaging,
  hooks and concurrency SHALL be declared from actual supported tools and permissions,
  not inferred from a harness name or a historical table. Unknown capabilities SHALL
  be unavailable with an explicit note; workflows still read the deployed declaration
  rather than perform per-skill environment detection.

### Naming and layout

- **REQ-17** | THE SYSTEM SHALL have no basename that exists in both `rules/` and
  `workflows/`.
- **REQ-18** | THE SYSTEM SHALL name the five phase bootstrap rules `bootstrap-discovery`,
  `bootstrap-execution`, `bootstrap-validation`, `bootstrap-atomic-execution`,
  `bootstrap-atomic-validation`.
- **REQ-19** | THE SYSTEM SHALL contain each bootstrap rule as exactly two sections,
  `## Context Bootstrap` and `## Phase Behaviors`, of at most 300 words in total.
- **REQ-20** | THE SYSTEM SHALL hold the Blocker Reconciliation procedure in
  `rules/procedure-blocker-reconciliation.md`, cited from `workflows/phase-atomic-execution.md`
  and `workflows/pae-implement.md` by that name.
- **REQ-21** | THE SYSTEM SHALL hold the Discovery decision-mode text (autonomous vs
  step-by-step) and the codebase reading rules in `rules/protocol-discovery-conduct.md`,
  or — if Discovery finds the Autonomous Decision Protocol already covers the decision
  text — merged into it with a recorded justification.
- **REQ-22** | THE SYSTEM SHALL contain no citation of a rule or workflow that carries a
  `.md` suffix; `workflows/phase-pipeline.md:185` and `:225` SHALL read "run the
  `/phase-execution` (`/phase-validation`) workflow's steps inline".
- **REQ-23** | THE SYSTEM SHALL hold `PIPELINE.md` at `docs/PIPELINE.md`, and every file in
  `workflows/` SHALL contain an `Invocation:` line.
- **REQ-24** | THE SYSTEM SHALL name rules as `<kind>-<subject>` where kind ∈
  {`bootstrap`, `contract`, `protocol`, `procedure`}, with these mappings:
  `workflow-globals` → `contract-phases`; `workflow-reference` → `contract-state-files`
  (file responsibilities, formats, protected sections, multi-phase, entry formats),
  `protocol-autonomous-decision`, `protocol-subtask-classifier` (classifier, tripwire,
  decomposition rules); `global-claude` → `harness/claude/always-on.md`;
  `templates/codex-global-AGENTS.md` → `harness/codex/always-on.md`. Subject-named rules
  (`tdd`, `git-flow`, `orchestration`, `quick-flow`, `run-log`, `language`) become
  `contract-tdd`, `contract-git-flow`, `contract-orchestration`, `contract-quick-flow`,
  `contract-run-log`, `contract-language`.
- **REQ-25** | WHEN a rule is renamed, THE SYSTEM SHALL update every citation in
  `workflows/`, `rules/`, `templates/`, live `docs/`, `scripts/*.sh`, live `.ai/`, and the deployed skill
  name, so that `scripts/validate-contracts.sh` reports zero unresolved citations.
- **REQ-26** | THE SYSTEM SHALL keep the deployed skill names `rule-<name>` and
  `principle-<name>` and document them as a namespace standard.
- **REQ-27** (withdrawn — superseded by REQ-39) | THE SYSTEM SHALL list the workflow
  prefix legend once, in `docs/USAGE.md`.
- **REQ-39** | THE SYSTEM SHALL, as the final subtask of this spec, rename the workflows:
  orchestrators `phase-discovery` → `discovery`, `phase-execution` → `execution`,
  `phase-validation` → `validation`, `phase-pipeline` → `pipeline`,
  `phase-atomic-execution` → `atomic-execution`, `phase-atomic-validation` →
  `atomic-validation`, `phase-composite-validation` → `composite-validation`; children
  `pd-<step>` → `discovery-<step>`, `pe-<step>` → `execution-<step>`, `pv-<step>` →
  `validation-<step>`, `pae-<step>` → `atomic-execution-<step>`, `pav-<step>` →
  `atomic-validation-<step>`; entry points and utilities unchanged.
- **REQ-40** | WHEN a workflow is renamed, THE SYSTEM SHALL update every invocation and
  citation in `workflows/`, `rules/`, `harness/`, `templates/`, live `docs/`, `scripts/*.sh`, live `.ai/`,
  and the deployed skill name, and SHALL list the old → new map in `docs/USAGE.md` for
  users of consumer projects.
- **REQ-41** | IF a renamed workflow name equals the name of a known public skill of a
  supported harness, THEN THE SYSTEM SHALL prefix that one skill directory with
  `orchestrail-` and record the collision in `docs/USAGE.md`.

### Contract checks and records

- **REQ-28** | IF any basename exists in both `rules/` and `workflows/`, THEN
  `scripts/validate-contracts.sh` SHALL fail.
- **REQ-29** | IF any file listed in REQ-11 contains a forbidden token outside its
  explicit exception, THEN `scripts/validate-contracts.sh` SHALL fail naming the file
  and line. Exception membership alone SHALL NOT allow a write to a legacy path.
- **REQ-30** | IF any `rules/*.md` lacks `description:` or `load:`, carries `trigger:`,
  or any `workflows/*.md` lacks `description:`, `phase:`, `step:`, or `Invocation:`, THEN
  `scripts/validate-contracts.sh` SHALL fail.
- **REQ-31** | IF any citation of a rule or workflow carries a `.md` suffix, or names a
  file that does not exist, THEN `scripts/validate-contracts.sh` SHALL fail.
- **REQ-32** | IF a bootstrap rule exceeds 300 words or contains a section other than the
  two named in REQ-19, THEN `scripts/validate-contracts.sh` SHALL fail.
- **REQ-33** | THE SYSTEM SHALL record an ADR that supersedes the deploy-target part of
  ADR-0003 and cites ADR-0009 Decisions 2 and 3 as the source of the harness abstraction,
  the `<kind>-<subject>` scheme, the `load:` front matter, and the command rename map.
- **REQ-34** | THE SYSTEM SHALL update `.ai/memory/architecture.md`,
  `.ai/context/environment.md`, `.ai/context/integrations.md`, `.ai/principles/domain.md`
  (new terms: harness, harness directory, capability, bootstrap, kind, load mode, project registry) and
  `.ai/principles/coding.md → Rule file shape` to the post-change state.

## Data Model

**Rule front matter** — `existing (rules/tdd.md:1-3)`, changed:

```yaml
---
description: <one line>          # required, existing
load: always | on-demand         # new, replaces trigger:
---
```

**Workflow front matter** — `existing (workflows/pd-analyze.md:1-3)`, extended:

```yaml
---
description: <one line>          # existing
phase: discovery | execution | validation | atomic-execution | atomic-validation | orchestrated | entry | utility   # new
step: <int> | -                  # new
---
```

**Project registry** — `new`: `~/.config/orchestrail/projects`, plain text, one
absolute path per line, no duplicates, created by `scripts/setup-new-project.sh`, read by
`scripts/sync.sh`. Lifecycle: append on setup; entries whose path is missing are reported by
`scripts/sync.sh` and left for the owner to prune.

**Skill manifest** — `new`: `~/.claude/skills/.orchestrail-manifest` and
`~/.codex/skills/.orchestrail-manifest`, one skill directory name per line, rewritten
on every `scripts/sync.sh`; the previous content drives stale-directory removal (REQ-10).

**Harness directory** — `new`: `harness/<name>/always-on.md` (core body; rendered with the
capability table at deploy), `capabilities.md` (table `capability | yes/no | note`),
`deploy.env` (`skills_dir=`, `always_on_path=`), optional `hooks.json`.

**Rule file kinds** — `new` classification, encoded in the file name prefix; no
persisted enum beyond the names themselves and the check in `scripts/validate-contracts.sh`.

No automatic migration of consumer-project task history is authorized. Structured
live references must be inventoried by 13a; old command names in historical free text,
completed records and verbatim Source quotations remain unchanged. In-progress projects
retain the REQ-09 deployment freeze and are not rewritten by the citation sweep.

## Contracts & Interfaces

**`scripts/sync.sh`** — same invocation (`scripts/sync.sh [--from <dir>]`); output is one section per
harness directory (`[claude] skills`, `[claude] always-on`, `[codex] …`) followed by
`[projects] registered projects`; new flag `--force` (ignore the in-progress freeze); exit 1 on validation failure (unchanged); new stderr lines
`stale skill removed: <name>` and `registry entry missing: <path>`.

**`scripts/setup-new-project.sh`** — same invocation; steps `[2/7] .windsurf/rules/` and
`[3/7] .windsurf/workflows/` removed; new final line `registered: <path>` or
`already registered`; legacy notice per REQ-07.

**`scripts/validate-contracts.sh`** — five new check groups (REQ-28 … REQ-32); existing checks
that reference `~/.codeium`, `.windsurf`, `.devin`, `trigger:` removed or retargeted; the
reported pass count changes and `docs/USAGE.md` quotes the new number.

**Skill names** (deployed): `rule-<new-name>` for every rule, e.g.
`rule-bootstrap-discovery`, `rule-contract-phases`, `rule-protocol-autonomous-decision`;
`principle-<name>` unchanged; workflow skills renamed per REQ-39 (`discovery`,
`discovery-analyze`, `atomic-execution-tests`, …); `PIPELINE` skill removed.

**Rule citation syntax** (unchanged form, new names): `` `contract-tdd` `` for the whole
rule, `` `contract-phases → ## Canonical Status Formats` `` for a section. Resolution:
prepend `rule-`.

**Failure responses:** `scripts/sync.sh` refuses to run when the manifest exists but is
unreadable (exit 1, message); `scripts/setup-new-project.sh` continues without registry when
`~/.config` is not writable and says so.

## Non-Functional Requirements

| Attribute | Target | How it is verified |
|---|---|---|
| Always-on context size | Each rendered `harness/<name>/always-on.md` ≤ 1,200 words; historical line counts are not a current baseline | `wc -w` in `scripts/validate-contracts.sh` |
| Bootstrap size | each `bootstrap-*` ≤ 300 words | REQ-32 check |
| Contract-check runtime | `scripts/validate-contracts.sh` completes in ≤ 30 s on the owner's machine | `time bash scripts/validate-contracts.sh` |
| Deploy idempotence | two consecutive `scripts/sync.sh` runs produce identical `~/.claude/skills` and `~/.codex/skills` trees | `diff -r` of a listing before/after the second run |
| Reference integrity | 0 unresolved citations, 0 `.md`-suffixed citations | REQ-31 check |
| Harness leakage | 0 forbidden tokens in source layers | REQ-29 check |
| Availability / performance / security | N/A — no runtime component; scripts run locally with the owner's permissions | — |

## Edge Cases & Failure Modes

| # | Case | Expected behaviour | Requirement |
|---|---|---|---|
| 1 | Consumer project has `.windsurf/rules/` from an earlier setup | Reported as legacy, untouched; project otherwise set up normally | REQ-07 |
| 2 | Registry file absent on first `scripts/sync.sh` after the change | Per-project pass reports "no registry — run scripts/setup-new-project.sh in each project" and exits 0 | REQ-09 |
| 3 | Registry contains a path that no longer exists | Skipped with one report line; other entries processed | REQ-09 |
| 4 | Registry contains the same path twice (hand-edited) | Processed once; duplicate reported | REQ-08, REQ-09 |
| 5 | Previous manifest lists `rule-phase-discovery` (old name) | Directory removed; new `rule-bootstrap-discovery` created | REQ-10 |
| 6 | Previous manifest absent (first run after the change) | Nothing removed; manifest written; a one-time notice lists old-name directories that look stale for manual review | REQ-10 |
| 7 | A skill directory under `~/.claude/skills/` was created by the user, not by sync | Never removed (not in manifest) | REQ-10 |
| 8 | A workflow cites a rule by its old name after the rename | `scripts/validate-contracts.sh` fails; deploy blocked | REQ-25, REQ-31 |
| 9 | Two rule files would map to the same `<kind>-<subject>` | Discovery resolves by subject qualifier; check for duplicate basenames within `rules/` fails otherwise | REQ-17 (extended to intra-directory) |
| 10 | An in-flight consumer task references a rule in `notes:` free text | Not an error; free text is not a citation | Data Model note |
| 11 | `~/.config` unwritable | Setup completes; registry step reports failure; `scripts/sync.sh` per-project pass has nothing to do | REQ-08 |
| 12 | Two `scripts/sync.sh` runs concurrently | Out of scope — single-user tool; documented in `docs/USAGE.md` as not supported | — |
| 13 | A contributor adds a rule with `trigger:` from habit | `scripts/validate-contracts.sh` fails naming the key | REQ-30 |
| 14 | A workflow file without `Invocation:` (documentation placed in `workflows/`) | `scripts/validate-contracts.sh` fails | REQ-23, REQ-30 |
| 15 | Empty `rules/` front matter block | Check fails (missing `description:`) | REQ-30 |
| 16 | A registered project has a task with a phase `in-progress` | Skipped by `scripts/sync.sh` with a report line; `--force` overrides | REQ-09 |
| 17 | `/spec-run` invoked with required capabilities missing or unavailable in the session | Refuses before effects naming the actual missing prerequisite, regardless of harness name | REQ-16, REQ-37, REQ-38 |
| 18 | A renamed workflow (`execution`) collides with a public skill | That skill directory deployed as `orchestrail-execution`; recorded | REQ-41 |
| 19 | A consumer project's in-flight `state.md` mentions an old command name in `last_action:` free text | Not an error; free text is not a citation | Data Model note |

## Acceptance Criteria

- [ ] **AC-01** (withdrawn → spec 13a) (REQ-01, REQ-02, REQ-03, REQ-04) — Given the current tree, when the audit
      is written, then `docs/audits/<date>-rules-workflows-audit.md` has one row per file
      in `rules/` and `workflows/` (52 rows) with the six columns named in REQ-01, a
      "mixed-kind" table naming at least `phase-atomic-execution` and `phase-discovery`
      with section boundaries, an "ambiguous citations" table containing
      `phase-pipeline.md:185` and `:225`, and a "duplicated statements" table.
- [ ] **AC-02** (REQ-05) — Given a clean `~/.codeium/` snapshot, when `scripts/sync.sh` runs, then
      no file under `~/.codeium/` is created or modified, and `grep -n 'claude\|codex' scripts/sync.sh`
      matches no branching construct — only the harness-directory loop.
- [ ] **AC-03** (REQ-06, REQ-07) — Given a temp project with a pre-existing
      `.windsurf/rules/x.md`, when `scripts/setup-new-project.sh` runs, then no `.devin/` is
      created, `.windsurf/rules/x.md` is byte-identical, and the output contains one line
      naming `.windsurf/` as legacy.
- [ ] **AC-04** (REQ-08, REQ-09) — Given two temp projects set up with the script, a
      third path in the registry that does not exist, and a fourth project whose task
      `state.md` has `execution: in-progress`, when `scripts/sync.sh` runs, then the two projects'
      `.claude/skills/` symlinks are refreshed, the output contains exactly one
      `registry entry missing:` line and one `skipped (in-progress):` line, and with
      `--force` the fourth project is refreshed too.
- [ ] **AC-05** (REQ-10) — Given `~/.claude/skills/rule-phase-discovery/` present and
      listed in the manifest, when `scripts/sync.sh` runs after the rename, then that directory
      is gone, `rule-bootstrap-discovery/SKILL.md` exists, and a user-created
      `~/.claude/skills/my-own/` is untouched.
- [ ] **AC-06** (REQ-11, REQ-29) — Given the post-change tree, when
      `grep -rniE 'windsurf|devin|codeium' rules workflows harness principles templates scripts/*.sh CLAUDE.md docs/USAGE.md`
      runs, then every match belongs only to the explicit read-only legacy reporter
      exception; an execution/deployment reference outside that exception fails. When
      the word `Windsurf` is inserted into
      `rules/contract-tdd.md`, then `scripts/validate-contracts.sh` fails naming that file.
- [ ] **AC-07** (REQ-12, REQ-13, REQ-30) — Given the post-change tree, when
      `scripts/validate-contracts.sh` runs, then it passes; and when `trigger: always_on` is added
      to one rule, or `phase:` is removed from one workflow, then it fails naming the file.
- [ ] **AC-08** (REQ-14, REQ-15) — Given `rules/contract-phases.md`, when read, then the
      Context Bootstrap table has columns `Phase | Skill | Loaded by` only, and the
      resolution sentence contains no harness name.
- [ ] **AC-09** (REQ-16) — Given `rules/contract-orchestration.md` and `docs/USAGE.md`,
      when searched, then no harness name appears next to a mechanism; each mechanism
      names its capability and the behaviour when it is absent.
- [ ] **AC-10** (REQ-17, REQ-18, REQ-28) — Given the post-change tree, when
      `comm -12 <(ls rules) <(ls workflows)` runs, then it is empty; the five
      `bootstrap-*.md` files exist; and when a file `rules/pd-analyze.md` is created, then
      `scripts/validate-contracts.sh` fails.
- [ ] **AC-11** (REQ-19, REQ-32) — Given each `bootstrap-*.md`, when `wc -w` runs, then
      the count is ≤ 300 and the only `##` headings are `Context Bootstrap` and
      `Phase Behaviors`; and when a third heading is added, then `scripts/validate-contracts.sh`
      fails.
- [ ] **AC-12** (REQ-20) — Given `rules/procedure-blocker-reconciliation.md`, when read,
      then it contains the three classification cases (dependency/status, non-status,
      ambiguity) verbatim from today's `rules/phase-atomic-execution.md:45-63`, and
      `workflows/pae-implement.md` and `workflows/phase-atomic-execution.md` cite it by
      that name and cite nothing else for reconciliation.
- [ ] **AC-13** (REQ-21) — Given the post-change tree, when searched, then the Discovery
      decision-mode text exists in exactly one rule file and `bootstrap-discovery.md`
      cites it.
- [ ] **AC-14** (REQ-22, REQ-31) — Given the post-change tree, when
      `grep -rnE '\`[a-z-]+\.md\`' workflows rules` is filtered to rule/workflow names,
      then it is empty; `workflows/phase-pipeline.md` lines formerly 185 and 225 read as
      specified; and when a `.md`-suffixed citation is inserted, then
      `scripts/validate-contracts.sh` fails.
- [ ] **AC-15** (REQ-23) — Given the post-change tree, when checked, then
      `docs/PIPELINE.md` exists, `workflows/PIPELINE.md` does not, no `PIPELINE` skill
      directory is deployed, and every file in `workflows/` contains a line starting with
      `Invocation:`.
- [ ] **AC-16** (REQ-24, REQ-25, REQ-26) — Given the post-change tree, when
      `ls rules/` runs, then every name starts with `bootstrap-`, `contract-`,
      `protocol-`, or `procedure-`; `harness/codex/always-on.md` exists and
      `templates/codex-global-AGENTS.md` and `rules/global-claude.md` do not; `scripts/validate-contracts.sh` passes; and
      `ls ~/.claude/skills/` after `scripts/sync.sh` shows `rule-<name>` for every rule.
- [ ] **AC-17** (REQ-24) — Given `rules/contract-state-files.md`,
      `rules/protocol-autonomous-decision.md`, `rules/protocol-subtask-classifier.md`,
      when their `##` headings are concatenated, then they equal the source-revision
      heading inventory recorded by 13a, each appearing exactly once. Do not enforce a
      historical count against a changed checkout.
- [ ] **AC-18** (withdrawn — superseded by AC-21) (REQ-27).
- [ ] **AC-19** (REQ-33) — Given `.ai/adr/`, when listed, then a new Accepted ADR exists
      covering the three points of REQ-33 and `adr/index.md` has its row; ADR-0003's
      status reads `Superseded by ADR-NNNN` for the deploy-target decision.
- [ ] **AC-21** (REQ-39, REQ-40, REQ-41) — Given the post-change tree, when `ls workflows/`
      runs, then no name starts with `pd-`, `pe-`, `pv-`, `pae-`, `pav-`, or `phase-`;
      `discovery.md`, `discovery-analyze.md`, `atomic-execution-tests.md`,
      `composite-validation.md` exist; `grep -rn 'pd-\|pae-\|/phase-' workflows rules harness templates docs scripts/*.sh .ai`
      returns only the old → new map in `docs/USAGE.md` and historical documents;
      `scripts/validate-contracts.sh` passes; any collision is recorded with an `orchestrail-`
      prefixed skill directory.
- [ ] **AC-22** (REQ-35, REQ-36) — Given `harness/claude/` and `harness/codex/`, when
      `scripts/sync.sh` runs, then `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` each contain the
      capability table of their harness, and the rendered tables differ exactly where
      `capabilities.md` differs.
- [ ] **AC-23** (REQ-37, REQ-38) — Given a temp always-on file whose table lacks
      `sub-agents`, when `/spec-run` is started, then it stops before Step 0 naming
      `sub-agents`; given a verified table and active tools satisfying all prerequisites, it proceeds
      on either harness; given `--parallel 2` and a table
      with `worktrees: no`, it stops naming `worktrees`.
      A declared capability whose tool is unavailable in the active session also
      stops before effects; unknown/unverified declarations carry evidence notes
      rather than fabricated support.
- [ ] **AC-20** (REQ-34) — Given the five `.ai/` files named in REQ-34, when searched for
      `Windsurf`, `.devin`, `trigger:`, or an old rule name, then nothing is found, and
      `domain.md` defines all terms named by REQ-34.

## Traceability

| REQ | Acceptance Criteria | Notes |
|---|---|---|
| REQ-01 | AC-01 | withdrawn → 13a |
| REQ-02 | AC-01 | withdrawn → 13a |
| REQ-03 | AC-01 | withdrawn → 13a |
| REQ-04 | AC-01 | withdrawn → 13a |
| REQ-05 | AC-02 | |
| REQ-06 | AC-03 | |
| REQ-07 | AC-03 | |
| REQ-08 | AC-04 | |
| REQ-09 | AC-04 | |
| REQ-10 | AC-05 | |
| REQ-11 | AC-06 | |
| REQ-12 | AC-07 | |
| REQ-13 | AC-07 | |
| REQ-14 | AC-08 | |
| REQ-15 | AC-08 | |
| REQ-16 | AC-09 | |
| REQ-17 | AC-10 | |
| REQ-18 | AC-10 | |
| REQ-19 | AC-11 | |
| REQ-20 | AC-12 | |
| REQ-21 | AC-13 | |
| REQ-22 | AC-14 | |
| REQ-23 | AC-15 | |
| REQ-24 | AC-16, AC-17 | |
| REQ-25 | AC-16 | |
| REQ-26 | AC-16 | |
| REQ-27 | AC-18 | withdrawn → REQ-39 |
| REQ-28 | AC-10 | |
| REQ-29 | AC-06 | |
| REQ-30 | AC-07 | |
| REQ-31 | AC-14 | |
| REQ-32 | AC-11 | |
| REQ-33 | AC-19 | |
| REQ-34 | AC-20 | |
| REQ-35 | AC-22 | |
| REQ-36 | AC-22 | |
| REQ-37 | AC-23 | |
| REQ-38 | AC-23 | |
| REQ-39 | AC-21 | |
| REQ-40 | AC-21 | |
| REQ-41 | AC-21 | |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| A rename misses a citation in a file the sweep did not cover (e.g. `templates/AGENTS.md`, `.ai/`) | Agent loads nothing for a cited rule; silent behaviour change | medium | REQ-25 sweep list is explicit; REQ-31 check fails on any unresolved name; do the sweep with one `sed` script committed with the change |
| Splitting `workflow-reference` changes a section heading | 42 citations in `workflows/`+`rules/` break | medium | AC-17 requires the heading set to be preserved exactly; rename only files, not headings, in this spec |
| Stale-skill removal deletes something the owner made by hand | Data loss in `~/.claude/skills` | low | REQ-10 removes only manifest-listed names; first run removes nothing (edge case 6) |
| Required Git history is unavailable when this runs | Rename sweep is unreviewable and unrevertable | conditional; source-of-truth work is completed | Hard dependency on completed 01; verify actual repository availability |
| Contract-check count changes invalidate numbers in docs | Docs drift | high | AC-07 implies re-running; `docs/USAGE.md` count updated in the same task |
| The owner still opens Windsurf occasionally | Old copies in `~/.codeium` go stale silently | low | Out of scope by decision; legacy deletion guidance stays in the read-only CLI reporter/historical migration report, not prohibited operational docs |
| Too many subtasks for one task (check 13) | Discovery produces > 8 subtasks | high — command renames were added | Audit is already spec 13a; if Discovery still exceeds 8, split into 13 (harness removal + `harness/` + front matter, REQ-05…16, 29, 30, 35…38) and 13b (all renames, REQ-17…28, 31…34, 39…41) |
| A consumer project runs an old command name after the rename | Skill not found | medium | Old → new map in `docs/USAGE.md`; `scripts/sync.sh` prints it once after the rename deploy |

## Assumptions

- `harness set` — Claude Code and Codex are the only targets; no third harness is planned
  → source: owner instruction (Source section).
- `windsurf cleanup` — files already deployed under `~/.codeium/` and `.windsurf/`/`.devin/`
  in consumer projects are reported, never deleted by scripts → source: safety rail
  "before deleting, look at the target" and the low cost of manual deletion.
- `project discovery` — a registry file replaces the `.devin` marker because no other
  marker distinguishes a consumer project from any directory with `.claude/`
  → source: `scripts/sync.sh:177-182` (marker-based discovery), decision recorded in Decisions.
- `skill prefix kept` — `rule-`/`principle-` deploy prefixes stay because they group
  skills in listings and cost nothing once the collision is gone → source: naming review
  R4.
- `headings frozen` — the split of `workflow-reference` keeps every `##` heading text so
  that all 42 section citations survive with only the file part changed → source: risk
  table.
- `in-flight tasks preserved` — deployment skips in-progress projects and citation
  rewrites exclude completed/free-text historical records; actual live references
  are inventoried by 13a rather than assumed absent.

## Decisions

- All decisions below are recorded in ADR-0009 (Decisions 2, 3, 7), which is the source
  of truth; this list is the summary.
- Drop Windsurf / Devin Desktop entirely; keep Claude Code and Codex — owner, 2026-09-16.
- `harness/<name>/` abstraction with a declared capability contract embedded into the
  deployed always-on file; workflows branch on capabilities only — owner, 2026-09-17.
- Both harnesses execute the full single-session pipeline; `/spec-run` is universal and
  capability-gated — owner, 2026-09-17. The historical claim that only one harness
  qualifies is not a current capability declaration.
- Kind vocabulary `bootstrap | contract | protocol | procedure`; full `<kind>-<subject>`
  scheme with no exceptions; `workflow-reference` split now with frozen headings; always-on
  files move to `harness/` — owner, 2026-09-17.
- Slash commands renamed inside this spec as the final subtask (map in REQ-39) — owner,
  2026-09-17.
- Audit is its own spec 13a, executed first; this spec is amended via `/spec-sync` —
  owner, 2026-09-17.
- Registry at `~/.config/orchestrail/projects`; freeze on `in-progress` with `--force`;
  no automatic deletion of Windsurf directories — owner, 2026-09-17.
- Workflows target models, not IDEs: any IDE-specific concept (`trigger:` front matter,
  IDE rule directories) is removed rather than made optional — owner, 2026-09-16.
- Project registry file over marker-directory discovery — author, confirmed by owner.

## Clarifications

### Session 2026-09-16

- Q: Keep Windsurf as a "degraded" target with a warning, or remove it? → A: Remove; only
  Claude and Codex remain (owner).
- Q: Should the spec also rename the slash commands (`pd-analyze` → `discovery-analyze`)?
  → A: Deferred to spec 11 at first.

### Session 2026-09-17

- Q: Command renames in spec 13 or 11? → A: In 13, as the final subtask.
- Q: Orchestrator names? → A: `discovery`, `execution`, `validation`, `pipeline`,
  `atomic-execution`, `atomic-validation`, `composite-validation`; children keep the step
  suffix; utilities unchanged.
- Q: Keep `/spec-run` Claude-only? → A: Universal, gated by declared capabilities
  (`sub-agents`, `agent-messaging`, `git`; `worktrees` + `concurrent-sub-agents` for
  parallel).
- Q: How does a skill know its harness? → A: `scripts/sync.sh` embeds the capability table into
  the harness's always-on file; no per-skill templating, no environment variables.
- Q: `always-on` in `rules/` or a `harness/` directory? → A: `harness/<name>/` with
  `always-on.md`, `capabilities.md`, `deploy.env`, optional `hooks.json`.
- Q: Delete `~/.codeium` copies? → A: No; print the command.
- Q: Audit as first subtask or own spec? → A: Own spec 13a.

## Open Questions

| # | Question | Severity | Impact if answered differently |
|---|---|---|---|
| — | None. The three questions of 2026-09-16 were answered on 2026-09-17 (ADR-0009). | | |

## Notes

- **Depends on** `.ai/specs/completed/01-git-source-of-truth.md` (git, Orchestrail name) and
  `.ai/specs/13a-rules-workflows-audit.md` (findings folded in via `/spec-sync`).
  Discovery must stop if either is not complete.
- **Related:** `.ai/specs/10-generated-reference-docs.md` (front-matter keys added here
  are what it renders), `.ai/specs/11-open-source-readiness.md` (public command names),
  ADR-0003 (partly superseded), ADR-0008 (this spec is the "make names self-describing"
  part of the enforcement-first direction: four new check groups).
- **Split boundary if Discovery exceeds 8 subtasks:** see Risks — harness work stays in
  13, every rename goes to 13b.
- **Suggested order inside the task:** audit → `.md`-suffix citation fix (REQ-22) →
  PIPELINE move (REQ-23) → harness removal in scripts (REQ-05…REQ-10) → front matter
  (REQ-12, REQ-13) → bootstrap rename + extraction (REQ-18…REQ-21) → remaining renames
  and `workflow-reference` split (REQ-24, REQ-25) → `harness/` and capabilities
  (REQ-35…REQ-38) → checks (REQ-28…REQ-32) → command renames (REQ-39…REQ-41, last) →
  docs and records (REQ-16, REQ-33, REQ-34). Each rename is `git mv` + one committed
  `sed` script + green `scripts/validate-contracts.sh`.
- **Implementation hint (not a requirement):** the registry and manifest paths can share
  `~/.config/orchestrail/`; the manifest could live there too, keyed by harness,
  if writing dotfiles into `~/.claude/skills/` proves undesirable.
- **Rejected alternative:** keeping Windsurf as a "best effort" target with the
  `rule-` workaround — rejected by the owner; it is the source of the collision.
- **Rejected alternative:** renaming only the five colliding rules and leaving the rest —
  rejected because it leaves four naming styles in one directory; the cost of the extra
  renames is one `sed` sweep under the same checks.
- **TDD level for the task:** `smoke` — each new `scripts/validate-contracts.sh` group is written
  first and observed failing on fixtures/current defects identified by 13a (historical
  counts are not fixed expectations), then the tree is changed
  until green.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one paragraph in domain language | PASS |
| 2 | `## Out of Scope` names concrete exclusions | PASS |
| 3 | Every requirement has a `REQ-NN` id and matches one EARS pattern | PASS |
| 4 | Every REQ has ≥1 AC; every AC names ≥1 REQ | PASS — active and withdrawn IDs retained; traceability checked by identifier, not a historical count |
| 5 | Every AC is binary and observable | PASS |
| 6 | Non-functional targets are numeric or explicitly N/A with a reason | PASS |
| 7 | Data model and contracts are present or explicitly N/A with a reason | PASS |
| 8 | Edge cases cover at least error, empty, boundary, and concurrency | PASS — concurrency declared unsupported (case 12) |
| 9 | Every ambiguity is either resolved in `## Assumptions` or listed in `## Open Questions` | PASS |
| 10 | No `blocker`-severity open question remains | PASS |
| 11 | Every codebase claim carries a `path:line` citation | PASS |
| 12 | Terminology matches `principles/domain.md` where it defines a term | PASS — all new terms flagged for addition (REQ-34) |
| 13 | The spec is feature-sized — plausibly 1–8 implementation subtasks | FAIL (recommendation only) — estimated 9–11 after the command renames were added; split boundary given in Risks |

**Verdict: READY WITH RESERVATIONS** — every blocking check passes; check 13 recommends
splitting into 13 and 13b at decomposition. Amended 2026-09-17 per ADR-0009; the audit
(13a) runs first and may amend this spec again via `/spec-sync`.

## Review amendments — 2026-10-21

- REQ-38 and AC-23 now use verified capabilities, not a permanent Codex prohibition.
  This follows ADR-0009's capability principle; current declarations must carry evidence.
- REQ-11/AC-06 now permit exactly the read-only legacy reporter required by REQ-07.
  A blanket string ban cannot coexist with code that detects and reports those strings.
- Live citation sweeps preserve completed history and Source quotations. Script
  interfaces now point to `scripts/`; historical line references must be refreshed
  by 13a rather than treated as current measurements.
- AC-17 uses the actual audited heading set. Reference/core splits must preserve its
  meaning and the 08 word budget. Spec 10's shared source body is a non-deployed
  template, not a second rule skill or a duplicate capability table.
- Capabilities/front matter are prerequisites, not authorization to enable cheaper
  policies, automatic retries or paid evaluations. Specs 05/09/14–20 own those changes.
- The feature-size reservation remains: Discovery must use the documented 13/13b
  split boundary if necessary; no ninth optimization workstream is expanded merely
  to absorb naming work. Record such a split in the index before execution.
