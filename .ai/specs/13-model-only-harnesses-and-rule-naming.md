# 13. Two model harnesses, declared capabilities and one naming scheme

## Source

- **Origin:** the owner's instruction of 2026-09-16 — drop the binding to editors, keep the
  two model harnesses, and remove the structural problems of rules and workflows — as decided
  in ADR-0009 Decisions 2, 3 and 7 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:77-141`,
  `:255-265`; Decision 7 amended by ADR-0017).
- **Previous revision:** 2026-10-28, written in Russian, with the amendments of 2026-10-21 and
  2026-10-28 folded in. Its purpose, translated from Russian (spec 13, revision 2026-10-28,
  §1): "The goal is to make the purpose of every rule and every workflow clear from its name
  and metadata, remove collisions, keep support for two model harnesses, and select
  behaviour by verified capabilities. The target harnesses are `Claude Code` and `Codex`; the
  names `claude` and `codex` are technical adapter identifiers." And: "The document
  describes a future migration. It does not declare it done and does not authorize
  installing changed instructions, running models or rewriting project history." The
  Russian text, with REQ-01–REQ-49 and AC-01–AC-29, is retrievable from the git history of
  this file at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`; every identifier is preserved
  below.
- **Snapshot the previous revision verified (translated from Russian, §2):**
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461`; the facts under Context & Problem were
  re-verified for this revision at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Pinned source:
  [tree at the snapshot](https://github.com/AlekseiChirkov/agentic-workflows/tree/8c2fa08c18115ffcf38a1798742c41e53a2c7461).
- **Roadmap position:** `.ai/specs/README.md` → "Dependency order" — order 2, prerequisites 01 and 13a,
  disposition "Preserve IDs; capability-based behavior and current script paths".
- **This revision:** 2026-11-14, refined in place under `/spec-draft --auto-mode` with the
  owner's authorization to replace the file. No human questions were asked; every resolved
  gap is recorded under Assumptions with its source. Specs 08, 09 and 10 (refined
  2026-11-13) build on this spec; their requests are disposed of under Notes → Peer requests.

### Implementation review — 2026-11-06 (preserved)

- **Disposition:** Planned; capability and registry foundations delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Claude/Codex capability records and project registration/hook ownership exist.
- **Outstanding scope and limits:** Deployment still writes legacy Windsurf paths and setup still creates legacy project rule directories. Data-driven deploy.env, migration ownership for all skills, metadata/naming changes, and coordinated global refresh remain undelivered.
- **Sources:** [`scripts/sync.sh`](../../scripts/sync.sh), [`scripts/setup-new-project.sh`](../../scripts/setup-new-project.sh), [`scripts/install-hooks.py`](../../scripts/install-hooks.py), [`harness/claude/capabilities.md`](../../harness/claude/capabilities.md), [`harness/codex/capabilities.md`](../../harness/codex/capabilities.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

1. **Deployment hard-codes harnesses and still serves the retired editors.**
   `scripts/sync.sh:69-87` copies every workflow, rule and principle to
   `~/.codeium/windsurf/global_workflows/` and `global_rules/`. Claude Code and Codex are two
   literal branches with literal paths (`:89-174`). The per-project pass finds projects with
   `find "$HOME" -maxdepth 6 -type d -name ".devin"` (`:197-282`), copies 13 named rule
   files into `.devin/rules/` and `.windsurf/rules/` (`:206-224`) and deletes workflow copies
   from `.devin/workflows/` and `.windsurf/workflows/` (`:241-265`).
2. **Deployment has no ownership record.** Skills are written with `mkdir -p` and `cp` into
   `~/.claude/skills/<name>/SKILL.md` and `~/.codex/skills/<name>/SKILL.md`
   (`scripts/sync.sh:91-95,123-129,135-139,167-173`); a skill whose source disappeared is
   never removed and a user's edit is overwritten silently.
3. **Project setup creates the retired directories.** `scripts/setup-new-project.sh:85-135`
   creates `.windsurf/rules/` and `.devin/rules/` and copies rule files into them;
   `:138-141` and `:335` instruct the user about Windsurf. `scripts/setup-all-repos.sh:112`
   runs that script in every service directory.
4. **A project registry exists but deployment ignores it.** Setup is its only writer
   (`scripts/setup-new-project.sh:264-321`): `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects`,
   one canonical physical root per line, `projects.lock` with a 5-second wait, atomic
   replacement, refusal of CR/LF/NUL paths. The git-rails hook reads it strictly and picks the
   most specific containing root (`hooks/git_rails.py:277-337`). `scripts/sync.sh` never reads it.
5. **Capability declarations cover logging and git rails only.** `harness/claude/capabilities.md:1-27`
   is a logging record (`hooks: yes`, `profile:`, `verified:`, `runtime:` lines plus prose)
   and `:29-37` a `## git-rails` section whose first lines use the record form `name:` /
   `state:` / `runtime:` / `verified:` / `evidence:`. `harness/codex/capabilities.md:3,12`
   declares `hooks: no` and `git-rails: none (textual rules only)`. No declaration exists for
   `sub-agents`, `concurrent-sub-agents`, `agent-messaging`, `worktrees` or `git`. Neither
   harness directory has `deploy.env` or `always-on.md`; `harness/claude/` also holds
   `hooks.json` and `permissions.json`.
6. **The always-on files live outside the adapters and the Claude one is large.** Bodies are
   `rules/global-claude.md` (985 words, no front matter) and
   `templates/codex-global-AGENTS.md` (484 words); `scripts/sync.sh:58-67,98-101,153-158`
   appends `<!-- Logging capabilities -->`, the whole capability file and a
   `## Current hook installation` record. `harness/claude/capabilities.md` alone has 1,607
   words (`wc -w`), so the deployed Claude file has about 2,600 words.
7. **Metadata is editor-specific and incomplete.** Rules carry `trigger: always_on`
   (`git-flow`, `language`, `orchestration`, `quick-flow`, `run-log`, `tdd`,
   `workflow-globals`) or `trigger: model_decision` (the five `phase-*` rules and
   `workflow-reference`) at line 2 of each file. Every workflow carries only `description:`;
   `workflows/pd-archive.md:2-3` spans two lines. Step designations in descriptions include
   `2.5` (`workflows/pd-select-model.md:2`), `4a` (`workflows/pv-classify-fixes.md:2`) and
   `4b` (`workflows/pd-archive.md:2`).
8. **Names collide and resolution branches per editor.** Five stems exist in both `rules/`
   and `workflows/` (`phase-discovery`, `phase-execution`, `phase-validation`,
   `phase-atomic-execution`, `phase-atomic-validation`). `rules/workflow-globals.md:11-17` is
   a four-column bootstrap table with a Windsurf/Devin column and `:19-27` explains a
   per-environment resolution of rule references.
9. **Several rules mix kinds.** `rules/phase-atomic-execution.md:49` holds
   `## Blocker Reconciliation`, cited by `workflows/phase-atomic-execution.md:52` and
   `workflows/pae-implement.md:76`. `rules/phase-discovery.md:36,43` holds
   `## Codebase Reading Rules` and `## Decision Protocol`. `rules/workflow-reference.md`
   (5,193 words) has 18 top-level `## ` headings outside fenced code plus template headings
   inside fences (`:37-60`, `:192-199`, `:542-550`). Bootstrap rule sizes (`wc -w`):
   `phase-atomic-execution` 683, `phase-discovery` 490, `phase-atomic-validation` 328,
   `phase-execution` 255, `phase-validation` 217.
10. **A reference document is deployed as a skill.** `workflows/PIPELINE.md:2` describes itself
    as "not an executable workflow", yet `scripts/sync.sh:91-95,135-139` deploys every
    `workflows/*.md` as a skill.
11. **The validator's check inventory is frozen.** `tests/fixtures/validator-runtime/oracle.py:162-252`
    pins the description and first expression line of every column-0 `check`, the body of
    each helper called by the 36 acceptance expressions, and one digest over the 94
    non-standard (indented or loop) check lines (`:164-173`).
    `tests/validator-runtime-oracle.py:46-100` accepts only a schema-1 amendment with fields
    `schema`, `paths`, `removed_results`, `resources`, two hard-coded removed results and the
    hard-coded `APPROVED_PATHS` (`:27-43`), pinned by `AMENDMENT_SHA256` (`:26`). The
    validator runs this oracle (`scripts/validate-contracts.sh:5851`). ADR-0019 Decision 3
    (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`) therefore put a
    new contract test outside the validator. Checks pin old names and old contracts, for
    example `grep -q 'trigger: always_on' rules/tdd.md` (`scripts/validate-contracts.sh:858-859`),
    a `trigger: always_on` loop (`:970-972`) and check (`:1853-1854`), setup copying every rule
    (`:1294-1305`) and sync's step 3c/4d structure (`:1311-1316`). Integration tests assert the
    legacy deployment (`tests/hook-install.sh:783-829`); `tests/workflow-instructions.py:38-55`
    reads `rules/workflow-globals.md` and globs `rules/phase-*.md`; the hook core names
    `rules/git-flow.md → ## Safety rails` in its diagnostics (`hooks/git_rails.py:30`,
    `tests/git-rails.sh:36`). Source-guard records bind digests of every shell and Python file
    under `tests/` and are refreshed by `tests/fixtures/validator-runtime/README.md:9-27`.
12. **Step names follow file names.** The run-log helper accepts a step name when a
    `workflows/<name>.md` exists (`scripts/log-step.sh:370-385`); historical names are not
    enforced (`rules/run-log.md:225-229`).

**Consequence:** a third harness would need code edits, deployment leaves stale or
overwritten skills without trace, consumer projects keep receiving editor directories, the
same base name means two different things, behaviour is chosen by harness name instead of a
verified capability, and every rename collides with the frozen validator inventory unless a
reviewed amendment mechanism exists.

## Goal

Maintainers deploy Orchestrail to Claude Code and Codex through one data-driven mechanism that
reads per-harness adapter files, records what it installed, never destroys a file it cannot
prove it owns, refreshes registered projects without touching retired editor directories, and
defers a shared update while a registered project has a task in progress; every rule and
workflow name states its kind, phase and step, behaviour is selected by declared and verified
capabilities, and every reference, check and document follows the new names in one reviewed
migration that the frozen validator inventory accepts through an explicit amendment.

## Scope

1. Retire the Windsurf/Devin deployment and project scaffolding; add a read-only legacy
   reporter `scripts/report-legacy-artifacts.sh` and a `docs/USAGE.md → ## Removed
   integrations` section recording the retirement (REQ-11).
2. Harness adapters: `harness/<name>/deploy.env`, `always-on.md` (moved from
   `rules/global-claude.md` and `templates/codex-global-AGENTS.md`), capability records in
   `capabilities.md`, optional `hooks.json`, `permissions.json`, `reserved-names.txt`.
3. A standard-library Python 3.11+ deployment engine `scripts/deploy-skills.py`, driven by
   `scripts/sync.sh`: deploy manifest, journal, lock, recovery, registry-based project pass,
   active-consumer freeze and `--force`. Its global write path is the state between this
   delivery and spec 11a's; spec 11a then supersedes it (Notes → Relationship to spec 11a).
4. Rule metadata (`description`, `load`) and workflow metadata (`description`, `phase`,
   `step`); one rule-reference resolution rule; the three-column bootstrap table.
5. The capability contract in `rules/contract-phases.md → ## Capabilities` and the
   `/spec-run` capability preflight.
6. Rule renames and splits (DM-10, DM-12), including the `workflow-reference` split and the
   move of `workflows/PIPELINE.md` to `docs/PIPELINE.md`.
7. Command renames (DM-11) as the final naming stage, the canonical name map
   `docs/name-map.json` and its table in `docs/USAGE.md`, and reserved-name collision handling.
8. Re-pointing every active reference: instructions, templates, documents, scripts, hooks,
   tests and validator expressions, with the schema-2 inventory amendment (DM-9) that lets
   the frozen oracle accept them.
9. A standalone checker `scripts/lint-instructions.py` and two standalone suites
   `scripts/check-lint-instructions.py` and `scripts/check-deploy-skills.py`.
10. A migration semantics record under `docs/audits/` (DM-20).
11. Knowledge-base updates and one ADR.

## Out of Scope

- The audit itself (inventory, link graph, duplicate clusters, mixed-kind detection,
  measurements): owned by spec 13a (old REQ-01–REQ-04 moved there). 13a's accepted report is
  an input; see Notes → Ownership between 13 and 13a.
- The generator, generated always-on files, `reads`/`writes`/`called_by` metadata and
  `docs/reference/`: spec 10. `loads` metadata, `rules/reference/`, `ref-<name>` deployment,
  the 700/6,000-word limits and the always-on lines naming `load: always` rules: spec 08.
  The public installer, profiles and backups: spec 11a. Golden runs and `tests/golden/`:
  spec 09. Parallel children and the `--parallel` flag: spec 12. Telemetry (05), git rails
  (06), the state tool (07), specs 14–20.
- Deleting or moving any legacy directory (`~/.codeium/…`, `.windsurf/`, `.devin/`) or any
  installed skill the deploy manifest does not own.
- A third harness; `CODEX_HOME` or any other environment-based path detection.
- Principle files: names, `principle-` namespace and their `trigger:` front matter stay as they
  are (`principles/*.md:1-3`).
- `scripts/link-skills.sh` (a manual, Claude-specific helper; it carries no legacy reference).
- Registering checks in `scripts/validate-contracts.sh`: the inventory accepts no added
  check (Context fact 11); schema 2 (DM-9) changes existing expressions only.
- Rewriting history: `.ai/tasks/completed/`, `.ai/specs/completed/`, ADRs, `docs/audits/`,
  `docs/analysis/`, `.ai/memory/progress.md`, run logs; validator check descriptions (they
  stay frozen, DM-9). Mapping old step names to new ones inside `/retro` (Q-02).
- Running `scripts/sync.sh` against a real home, running models, paid runs.

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Owner | Accepts changes of agreed behaviour; runs `scripts/sync.sh` (with `--force` only by decision); removes legacy directories and leftover skills by hand |
| Implementer | Moves and edits sources, tests and checks under the TDD contract; never runs sync against the real home |
| Independent validator | Reviews the migration semantics record and the inventory amendment entries |
| `scripts/sync.sh` | Validates, installs hooks, runs the legacy reporter and the engine; the only deploy entry point until spec 11a's installer replaces its global-write step (Notes → Relationship to spec 11a) |
| `scripts/deploy-skills.py` | Reads adapters, sources, registry, manifests; writes only owned global targets, its manifests, journal and lock, and owned project links and the `.ai/` ignore line; after spec 11a its `deploy` command is removed and it writes only project links and the ignore line |
| `scripts/setup-new-project.sh` | Sole writer of the registry; creates project files; links skills through the engine |
| `scripts/report-legacy-artifacts.sh` | Reads only; prints legacy objects |
| `scripts/lint-instructions.py` | Reads the repository; prints findings |
| Git-rails hook core | Reads the registry (unchanged) |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Harness | A supported model runtime; in the repository, a directory `harness/<name>/` holding `deploy.env` (DM-5) | ADR-0009 D2; this spec |
| Adapter files | `deploy.env`, `always-on.md`, `capabilities.md` and the optional `hooks.json`, `permissions.json`, `reserved-names.txt` of one harness | This spec; ADR-0017 implications |
| Rule | A top-level `rules/<stem>.md` contract, deployed as skill `rule-<stem>` | `.ai/principles/domain.md:13` (updated by REQ-34) |
| Rule kind | `bootstrap`, `contract`, `protocol` or `procedure`; the file-stem prefix | ADR-0009 D3 |
| Bootstrap rule | `bootstrap-<phase>`: exactly `## Context Bootstrap` and `## Phase Behaviors` | REQ-18, REQ-19 |
| Workflow | An invocable `workflows/<stem>.md` with front matter and one `Invocation:` line | `.ai/principles/coding.md:19-33` |
| Load mode | `always` or `on-demand`: a loading requirement, not proof that the text is in the current context | Previous revision §4 |
| Capability | An operation a harness offers to shipped workflows, declared by a capability record with state, runtime, date and evidence; the session's actual tool permission is checked separately | DM-4 |
| Capability record | A `name:`-started block in `capabilities.md` (DM-4) | `harness/claude/capabilities.md:31-37`; spec 10 A-32 |
| Registry | `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects` | Context fact 4 |
| Active project | A registered root with at least one task phase `in-progress` or an unreadable task state (DM-8) | REQ-59 |
| Active consumer | An active project, counted when a global change is planned; the source checkout counts when it is registered and active, because it uses the same global skills | REQ-43 |
| Deploy manifest | Per-harness ownership record `orchestrail/deploy/<harness>.json` (DM-6). Not spec 10's generator manifest and not spec 11a's installer manifest | This spec |
| Owned object | An installed path whose current bytes equal a digest the deploy manifest or journal records | REQ-10, REQ-42 |
| Plan | The complete list of create/replace/remove actions computed before the first write | REQ-45 |
| Legacy object | One of the paths of DM-13 | REQ-07 |
| Leftover skill | A skill directory under a harness `skills_dir`, not owned, whose name was installed by the previous sync from a DM-1 row: `<old>` of a workflow row, `rule-<old>` of a rule row, `PIPELINE` and `rule-global-claude` of the file rows | REQ-57 |
| Name map | `docs/name-map.json` (DM-1) | REQ-40 |
| Installed name | The skill directory name a source file deploys to (DM-15) | REQ-41, REQ-49 |
| Executable reference | A form of DM-16 in an instruction file | REQ-22, REQ-31 |
| Active reference | Any occurrence of a name in the scan set of DM-17 | REQ-25 |
| Word | A maximal non-empty run of non-whitespace characters (DM-19) | Previous revision §9; spec 08 A-09; spec 10 Terminology |
| Always-on body | The text of `harness/<name>/always-on.md` without an embedded copy of the capability declaration and without the installation record: provenance line, header and core (REQ-54, D-01) | This spec |
| Inventory amendment | `tests/fixtures/validator-runtime/inventory-amendment.json` (DM-9) | Context fact 11 |

Rejected synonyms: "environment" for harness; "capability table" for the declaration (it is
records and prose); "receipt" for the deploy manifest (reserved for the hook installer).

## Requirements

### Withdrawn identifiers

- **REQ-01 — withdrawn, moved to 13a** (inventory of files, kinds, sizes, references, legacy integrations).
- **REQ-02 — withdrawn, moved to 13a** (mixed kinds with section boundaries).
- **REQ-03 — withdrawn, moved to 13a** (ambiguous names, missing target sections).
- **REQ-04 — withdrawn, moved to 13a** (verbatim and semantic duplication).
- **REQ-27 — withdrawn, replaced by REQ-39** (a single legend of short prefixes is not revived).

### Harnesses, deployment and capabilities

- **REQ-05.** THE deployment (`scripts/sync.sh` with `scripts/deploy-skills.py`) SHALL take
  every global target path only from `harness/<name>/deploy.env`, SHALL process every harness
  directory (DM-5) through one code path that compares no value against a harness name, and
  SHALL write nothing under `$HOME/.codeium/`.
- **REQ-06.** WHEN `scripts/setup-new-project.sh` or `scripts/setup-all-repos.sh` runs, THE
  script SHALL NOT create `.windsurf/`, `.devin/` or anything below them.
- **REQ-07.** WHEN sync or project setup runs and a legacy object (DM-13) exists, THE script
  SHALL print exactly one reporter line per object (Contracts → Legacy reporter) and SHALL
  leave the object's bytes, type and contents unchanged.
- **REQ-08.** THE registration step of `scripts/setup-new-project.sh` SHALL keep its current
  behaviour (Context fact 4) unchanged, and the deployment SHALL only read the registry.
- **REQ-09.** WHEN the project pass runs, THE engine SHALL process each distinct registered root
  once in registry order, report a missing root, skip the source checkout, skip an active
  project unless `--force` is given, and refresh owned skill links and the `.ai/` ignore step
  of every other root (Contracts → Project pass).
- **REQ-10.** THE engine SHALL record installed objects in the deploy manifest (DM-6), SHALL
  remove an object only when the manifest or journal records it and its current bytes equal a
  recorded digest, and WHEN no manifest exists for a harness SHALL remove nothing for it.
- **REQ-11.** THE files of scan set L (DM-17) SHALL contain no mention of Windsurf, Devin or
  Codeium; the exceptions are `scripts/report-legacy-artifacts.sh`, which only detects and
  reports, and the section `docs/USAGE.md → ## Removed integrations`, which this delivery
  creates to record the retirement (DM-17 scan set L).
- **REQ-12.** THE front matter of each top-level rule SHALL contain exactly `description` and
  `load` with grammar DM-2 plus only registered extension keys, and SHALL NOT contain `trigger`.
- **REQ-13.** THE front matter of each workflow SHALL contain exactly `description`, `phase`
  and `step` with grammar DM-3 — `step` is a positive integer, an integer with one decimal
  part, an integer with one lowercase letter, or `"-"` — plus only registered extension keys.
- **REQ-14.** THE section `contract-phases → ## Rule references` SHALL contain the anchored
  line ``A reference to rule `<name>` resolves to skill `rule-<name>` on every supported harness.``,
  that line SHALL occur exactly once in scan set R (DM-17), and no file of scan set R SHALL
  contain the phrase `bare basename` or a table header naming a rules-file column.
- **REQ-15.** THE bootstrap table in `contract-phases → ## Context Bootstrap` SHALL have the
  header `| Phase | Skill | Loaded by |` and exactly one row per phase naming one
  `rule-bootstrap-<phase>` skill.
- **REQ-16.** THE rule `contract-phases → ## Capabilities` SHALL list every
  capability-dependent behaviour with its required capability and its path when the
  capability is absent (DM-4 → Behaviour table); IF a required capability is `no`, `unknown`
  or undeclared, or the session does not expose the tool or permission, THEN THE workflow
  SHALL take the listed single-session path or stop before any side effect, and SHALL NOT
  report the unavailable mechanism as used.
- **REQ-35.** EACH harness directory SHALL contain `deploy.env`, `always-on.md` and
  `capabilities.md`, MAY contain `hooks.json`, `permissions.json` and `reserved-names.txt`,
  and THE delivery SHALL extend the existing capability files in place without removing or
  editing any existing line.
- **REQ-36.** WHEN sync deploys an always-on file, THE deployed bytes SHALL equal the assembly
  of DM-14, so the declaration appears exactly once; workflows read capabilities from the
  always-on context, never from per-skill templating or environment variables. Spec 10 later
  replaces the assembly with its generated file without a second append.
- **REQ-37.** WHEN `/spec-run` starts, THE workflow SHALL, before any write, branch, commit or
  spawn, require records `sub-agents`, `agent-messaging` and `git` with `state: yes` and the
  matching session tools, and WHERE `--parallel N` with N > 1 is given (spec 12) also
  `worktrees` and `concurrent-sub-agents`; otherwise it SHALL stop with the message of
  Contracts → `/spec-run` preflight, whose next step is `/pipeline <task-directory>` for a
  missing `sub-agents`, `agent-messaging` or `git`, and a re-run without `--parallel` for a
  missing `worktrees` or `concurrent-sub-agents` (`/pipeline` has no parallel mode); with
  several keys missing, the first in the key order of the preflight contract decides.
  Single-session workflows keep their documented paths.
- **REQ-38.** EACH capability record SHALL state `state`, and for `yes` or `no` also `runtime`,
  `verified` and at least one `evidence`; a capability without collected evidence SHALL be
  `state: unknown`; a `no` record describes the shipped implementation, not a permanent
  platform limit; mechanism support, installation result and checkpoint coverage SHALL remain
  separate statements.

### Names and moved content

- **REQ-17.** THE stems of `rules/*.md` and `workflows/*.md` SHALL be disjoint, and the set
  of installed names of all sources (DM-15) SHALL contain no two names equal under Unicode
  casefolding.
- **REQ-18.** THE five bootstrap rules SHALL be `bootstrap-discovery`, `bootstrap-execution`,
  `bootstrap-validation`, `bootstrap-atomic-execution`, `bootstrap-atomic-validation`.
- **REQ-19.** EACH bootstrap rule SHALL contain, after its front matter and one optional H1,
  exactly the two `## ` sections `## Context Bootstrap` then `## Phase Behaviors` and at most
  300 words (DM-19); IF the moved text exceeds 300 words, THEN the excess `## Phase Behaviors`
  text SHALL move to the overflow rule DM-10 names for that phase, cited from
  `## Phase Behaviors`, and SHALL never be deleted.
- **REQ-20.** THE blocker reconciliation text SHALL live only in
  `rules/procedure-blocker-reconciliation.md` with its three cases (dependency/status blocker,
  non-status blocker, ambiguity rule), and both consumers (`/atomic-execution` Step 0 and
  `/atomic-execution-implement`) SHALL cite that rule.
- **REQ-21.** THE Discovery decision mode and code-reading rules SHALL live only in
  `rules/protocol-discovery-conduct.md`; WHERE 13a's accepted report proves that
  `protocol-autonomous-decision` already covers them completely, they MAY be merged there
  instead, with the proof cited in the semantics record (DM-20).
- **REQ-22.** EXECUTABLE references (DM-16) SHALL name rules and workflows without `.md`;
  invocations stay explicit `/<name>`; documentation paths, examples and history are not
  executable references; every explicit child call an orchestrator makes today SHALL remain an
  explicit call under the new name.
- **REQ-23.** `workflows/PIPELINE.md` SHALL move to `docs/PIPELINE.md` and SHALL NOT be
  deployed; every remaining `workflows/*.md` SHALL contain exactly one line starting
  `Invocation: `.
- **REQ-24.** EVERY top-level rule SHALL be named `<kind>-<subject>` with a kind of DM-2 and
  SHALL follow the rule map DM-10; split rules SHALL follow DM-12.
- **REQ-25.** WHEN a rule, workflow or moved file changes name, THE same change SHALL update
  every active reference in scan set R (DM-17) — including hooks, tests, validator
  expressions, `docs/`, `templates/` and any existing `tests/golden/cases/*/case.json` — so
  that the checker reports zero `stale-name`, `reference-missing` and `heading-missing`.
- **REQ-26.** THE namespaces `rule-<name>` and `principle-<name>` SHALL be kept and documented
  in `contract-phases → ## Rule references`; `ref-<name>` SHALL be reserved for spec 08's
  `rules/reference/` files, which are not top-level rules.
- **REQ-39.** THE command renames of DM-11 SHALL be the last naming stage; entry points and
  utilities keep their names; after it only checks and records follow, not another rename wave.
- **REQ-40.** THE same change that renames a command SHALL update all its calls;
  `docs/USAGE.md → ## Renamed commands and rules` SHALL equal `docs/name-map.json` row for
  row; no alias workflow, alias skill or redirect SHALL be created; history is not rewritten.
- **REQ-41.** IF a new name of DM-1 appears in the `reserved-names.txt` of any harness (DM-18),
  THEN its map entry SHALL be `orchestrail-<name>` for every harness; a collision SHALL be
  established only by such a listing with evidence, never by assumption.
- **REQ-49.** EVERY invocation, document, check and installed directory SHALL use the name of
  `docs/name-map.json`; THE checker SHALL reject a command reference whose name is not an
  installed workflow name, even if a prefixed directory exists.

### Checks and records

- **REQ-28.** THE checker SHALL report `name-collision` for equal rule and workflow stems and
  `installed-name-collision` for installed names equal under casefolding.
- **REQ-29.** THE checker SHALL report each legacy mention in scan set L with path and line
  and honour only the exceptions of REQ-11; an exception grants no right to write to or delete
  a legacy path.
- **REQ-30.** THE checker SHALL reject missing or invalid metadata, `trigger`, repeated keys,
  unregistered keys and a missing or repeated `Invocation:` line; registered extension keys
  are validated by their owning spec's validator, and the checker reports each violation that
  validator finds as `metadata-invalid-value`.
- **REQ-31.** THE checker SHALL reject `.md` after a rule or workflow name in an executable
  reference, an unknown name and a missing heading; repository paths are checked for
  existence only; examples in fenced code and history are not rewritten globally.
- **REQ-32.** THE checker SHALL reject a bootstrap rule over 300 words or with any `## `
  section other than the two of REQ-19, counting words by DM-19 (same rule as specs 08 and 10).
- **REQ-33.** THE delivery SHALL add one accepted ADR that records the migration, supersedes
  ADR-0003 only for its deployment targets (citing ADR-0009), keeps ADR-0003's `rule-` prefix
  and duplicated-essentials decisions, and records the schema-2 inventory amendment as an
  amendment of provisional ADR-0018 and the standalone checker under ADR-0019 Decision 3.
- **REQ-34.** THE delivery SHALL update `.ai/memory/architecture.md`,
  `.ai/context/environment.md`, `.ai/context/integrations.md`, `.ai/context/runbook.md`,
  `.ai/principles/domain.md` and `.ai/principles/coding.md` so that together they name
  `harness/<name>/deploy.env`, the deploy manifest path, `docs/name-map.json`, the
  registry-based project pass and `scripts/lint-instructions.py`; `domain.md` defines every
  term of this spec's Terminology table and the four rule kinds of DM-2;
  `coding.md → ### Rule file shape` states the DM-2
  front matter instead of `trigger:`; and none of the six files contains a legacy mention
  (DM-17 L rule).

### Safety of deployment and migration

- **REQ-42 Ownership.** IF a planned path is a symbolic link, lies outside its resolved target
  root, is recorded with a digest that differs from its current bytes, or the resolved
  `skills_dir` differs from the manifest's, THEN THE engine SHALL write nothing and report the
  conflict (DM-6, Contracts → Engine errors); a foreign file inside a skill directory is never
  removed.
- **REQ-43 Shared skills and active tasks.** WHEN the plan contains at least one global
  action and an active consumer exists, THE engine SHALL write nothing (global targets and
  project links alike), list each active consumer and exit 3, unless `--force` is given;
  `--force` SHALL override only this freeze and the project skip of REQ-09, never ownership,
  input validation or the lock. Active consumers are all active registered roots, the source
  checkout included. THE engine SHALL evaluate active consumers after taking the
  lock and SHALL print the residual-race note, because no current entry point serializes task
  starts with deployment.
- **REQ-44 Inputs as data.** THE engine and the checker SHALL parse `deploy.env`, the
  registry, manifests, the journal, the name map and front matter as data with the grammars of
  the Data Model, SHALL NOT `source`, `eval` or execute them, and SHALL reject unknown keys,
  repeated keys, command substitution and any value outside the grammar.
- **REQ-45 Serialization and recovery.** THE engine SHALL hold an exclusive non-blocking lock
  for the whole run, compute and validate the complete plan before the first write, write the
  journal before the first change, replace each file atomically, write each manifest after
  its objects and delete the journal last; WHEN a journal exists at start, THE engine SHALL
  recover by DM-7 and SHALL NOT lose a user change.
- **REQ-46 Semantic preservation.** EVERY `## ` heading line of a split or renamed rule SHALL
  appear exactly once in the target the section map (DM-12) names, and THE semantics record
  (DM-20) SHALL map every normative statement of a moved section to its single new home and
  consumers; equal heading counts alone are not evidence.
- **REQ-47 Isolated verification.** THE suites SHALL run only in temporary directories with
  `HOME`, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` redirected, SHALL start no model, network or
  paid run, and SHALL never touch the real home; deployment stays a separate owner action.
- **REQ-48 Split.** IF Discovery yields more than eight full subtasks, THEN THE task SHALL be
  split at the boundary of Notes → Split boundary and the split recorded in
  `.ai/specs/README.md` before execution; identifiers are not lost or counted as done by moving.

### Added in this revision

- **REQ-50 Standalone checks.** THE checker `scripts/lint-instructions.py` and the suites
  `scripts/check-lint-instructions.py` and `scripts/check-deploy-skills.py` SHALL be
  standard-library Python 3.11+ programs run directly, SHALL NOT be called from
  `scripts/validate-contracts.sh` or `scripts/sync.sh`, and THE checker SHALL exit 0 on the
  delivered repository.
- **REQ-51 Name-equivalent expression changes.** WHEN a frozen validator expression, helper
  body or non-standard check line changes only by names or paths, THE inventory amendment
  SHALL record it as a `path_changes` entry of DM-9, and THE oracle SHALL accept the current
  validator only if every difference from the frozen inventory is covered by a valid entry.
- **REQ-52 Superseded check contracts.** WHEN this migration supersedes the contract a frozen
  check asserts (for example `trigger: always_on`, setup copying rules into editor
  directories, sync's literal harness steps), THE check SHALL be replaced in place by a check
  of the successor contract and recorded as a `contract_changes` entry of DM-9 naming the
  superseding requirement; no frozen check is deleted, skipped or weakened.
- **REQ-53 Re-pointed tests.** THE delivery SHALL update every test, fixture and hook string
  that names a moved file or renamed name, so that each glob or path it uses matches at least
  one existing file, and `scripts/validate-contracts.sh` SHALL finish with zero failures.
- **REQ-54 Always-on body size.** EACH always-on body SHALL have at most 1,200 words (DM-19).
  The body is the text of `harness/<name>/always-on.md`; when that file contains the exact
  text of the same harness's `capabilities.md` with trailing `\n` characters removed (as spec
  10's generated file will), the first such occurrence is removed before counting. The
  installation record is never part of the file. The counted text is therefore the provenance
  line, the header and the core only (owner decision D-01); the embedded declaration is
  excluded and its size is bounded by spec 08's always-on-set budget, not by this limit.
- **REQ-55 Always-on move.** THE delivery SHALL move `rules/global-claude.md` to
  `harness/claude/always-on.md` and `templates/codex-global-AGENTS.md` to
  `harness/codex/always-on.md` with `git mv`, changing only lines that hold a stale name, a
  legacy mention or the path of the file itself.
- **REQ-56 Runtime guard.** IF `python3` is missing or older than 3.11, THEN `scripts/sync.sh`
  SHALL print `ERROR: Python 3.11 or newer is required for deployment` and exit 1 before the
  hook installation and before any write.
- **REQ-57 Leftover skills.** WHEN the engine finds a leftover skill (Terminology), THE engine
  SHALL print one `leftover` line per directory on every run, SHALL NOT remove it, and SHALL
  never create a directory under an old name.
- **REQ-58 Manifest revision.** THE deploy manifest SHALL carry `source_revision`, the output
  of `git -C <source> rev-parse --verify HEAD`, or `null` when the source is not a git work
  tree or git is unavailable.
- **REQ-59 Active detection.** THE engine SHALL classify a registered root as active exactly by
  DM-8, treating an unreadable task state as active.
- **REQ-61 Semantics record.** THE delivery SHALL add the migration semantics record DM-20
  under `docs/audits/` and index it in `docs/README.md`.
- **REQ-62 Capability records.** EACH `capabilities.md` SHALL contain one record per canonical
  key in `## Capability records` (DM-4), one `always-on-path:` line equal to the
  `always_on_path` value of the same harness's `deploy.env`, and a `hooks` record whose state
  equals the existing `hooks:` line.
- **REQ-63 Validated plan.** IF any input, collision, adapter, ownership or recovery check fails
  for any harness, THEN THE engine SHALL write nothing for any harness or project and exit 1.
- **REQ-64 Contracts unchanged.** THE migration SHALL NOT change any status vocabulary,
  anchored `Status values for` line, TDD rule (`atomic-tests: pinned`, `n-a`, missing
  `atomic-tests:` read as `not-started`, the `pre-TDD task, TDD step skipped` note), protected
  section, stop or authority rule except for name substitutions from DM-1.
- **REQ-65 Installation record per harness.** THE assembly (DM-14) SHALL embed the hook
  installer's result for a harness whose directory has `hooks.json` and
  `{"reason":"no-native-adapter","status":"unavailable"}` for any other harness.

- **REQ-66 Managed always-on file.** THE delivery SHALL replace the advice to edit the global
  always-on file (`rules/language.md:20-21`; the copy in the heredoc at
  `scripts/setup-new-project.sh:115-116` disappears with REQ-06) with the statement that
  `scripts/sync.sh` manages that file and that an edit to it makes the next sync stop with
  `ownership-conflict`, and SHALL add the same statement where `docs/USAGE.md:331` describes
  the global file.

- **REQ-67 Extension keys in the behaviour table.** THE checker SHALL accept in a `Requires`
  cell of the DM-4 behaviour table a canonical key or the `name:` of a capability record that
  every harness's `capabilities.md` declares, and SHALL report
  `capability-behaviour-table-invalid` for any other key.

- **REQ-68 Split targets of mapped rules.** WHEN a spec delivered after this one moves text
  that a frozen check asserts out of a rule that has a `rule` row in `docs/name-map.json` into
  a new top-level rule, THE same delivery SHALL append that rule's stem to the `new` list of
  that row, update the `docs/USAGE.md → ## Renamed commands and rules` row, record the
  re-pointing as `path_changes` entries of DM-9 and refresh `name_map_sha256`, so that the
  moved text stays in the row's mask class and the entry is path-only. A new rule that
  receives no text moved from a mapped rule gets no row, and one `new` value never joins two
  rows, so text asserted by checks of two different rows cannot be moved into one new file.
- **REQ-69 Extending the closed requirement set.** A later spec MAY add values to the closed
  set of `requirement` values accepted in `contract_changes` (DM-9) only in its own delivery,
  together with the change of the oracle test that hard-codes the set and, for each entry that
  names a new value, a verdict row in DM-20 → Superseded checks; no other change extends it.
  A value added by a later spec carries that spec's number, with its letter suffix when the
  spec file name has one, as a prefix, `spec-<NN>[<a-z>] REQ-<MM>` (for example
  `spec-11 REQ-72`, `spec-11a REQ-04`), so it never collides with this spec's bare ids.

REQ-60 is not used.

## Data Model

### DM-1 Name map `docs/name-map.json` (new)

```json
{
  "schema_version": 1,
  "rows": [
    {"kind": "file", "old": "rules/global-claude.md", "new": ["harness/claude/always-on.md"]},
    {"kind": "rule", "old": "phase-discovery", "new": ["bootstrap-discovery", "protocol-discovery-conduct"]},
    {"kind": "workflow", "old": "pd-analyze", "new": ["discovery-analyze"]}
  ]
}
```

- Top-level keys exactly `schema_version` (integer `1`) and `rows`. Row keys exactly `kind`,
  `old`, `new`. `kind` is `rule`, `workflow` or `file`.
- `rule` and `workflow` rows: `old` and each `new` match `^[a-z0-9]+(-[a-z0-9]+)*$`; a
  `workflow` row has exactly one `new`; a `rule` row has one or more. `file` rows: repository
  paths matching `^(rules|workflows|templates|harness|docs)/[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$`,
  exactly one `new`.
- Rows sorted by `kind`, then `old` (Python string order); no `(kind, old)` pair repeated (the
  five `phase-*` stems therefore have one `rule` row and one `workflow` row each); no `new`
  value appears in two rows; no `new` equals any `old`. Rows are exactly: one `rule` row per
  DM-10 source under `rules/` other than `rules/global-claude.md` (listing every overflow rule
  REQ-19 actually created), one `workflow` row per DM-11 rename, and three `file` rows —
  `rules/global-claude.md` and `templates/codex-global-AGENTS.md` (the two DM-10 harness rows)
  and `workflows/PIPELINE.md`; unchanged names are not listed. A later delivery may append a
  split target to the `new` list of an existing `rule` row only as REQ-68 states.
  Parsed with `json.loads`, duplicate keys rejected.
- An absent `docs/name-map.json` reads as a map with no rows (no stale names, no leftovers,
  no name tokens in the DM-9 mask). A current source stem always wins over a map `old`: it is
  deployed normally and never reported as a leftover (the state between metadata work and the
  rename stages).
- `docs/USAGE.md → ## Renamed commands and rules` holds the table `| Kind | Old | New |` with
  one row per map row in map order, `New` joined by `, `, each name in backticks.

### DM-2 Rule front matter (changed; replaces `trigger:`)

```yaml
---
description: Bootstrap context and phase behaviours for Discovery
load: on-demand
---
```

Grammar (shared with DM-3; compatible with spec 10's line grammar): the file starts with a
line `---`; the block ends at the next line `---`. Every non-empty line inside is
`<key>: <value>` at column 0 with `<key>` matching `[a-z_]+`; a value starting with `"` is a
JSON string (`json.loads`, the whole rest of the line); otherwise the value is the rest of the
line with trailing spaces removed, non-empty, not starting with `'`, `[`, `{`, `|`, `>`, `&`,
`*`, `!`, `%`, `@` or `` ` ``. Tabs, comments, repeated keys and continuation lines are errors.
Rule keys: `description` (one non-empty line) and `load` (`always` | `on-demand`).
Registered extension keys: `loads` (owner spec 08; its block grammar and validator are 08's).
Until the owning spec registers its validator in the checker, an extension key is
`metadata-unknown-field`. A column-0 line of a registered extension key whose value is empty
or `[]` opens that key's block, which ends before the next line at column 0 or the closing
`---` (08 DM-1 Extent); the value, comment and continuation-line rules above do not apply inside it,
and the checker passes the block to the owning spec's validator (08 DM-1 for `loads`; spec 10
Data Model → Workflow metadata for `reads`, `writes`, `called_by`). The kind is the stem prefix before the first `-`: `bootstrap`,
`contract`, `protocol`, `procedure`. Their operational meanings are those of spec 13a
(Terminology → Kinds, its A-04): a `bootstrap` rule lists the ordered context sources one
phase loads before acting and that phase's behaviours; a `contract` states formats,
vocabularies, invariants or obligations that hold across workflows regardless of the current
decision point; a `protocol` states how to decide at a named decision point (inputs, criteria,
outcomes); a `procedure` states an ordered sequence of actions triggered by a named condition,
usable from more than one workflow. `.ai/principles/domain.md` becomes their canonical home
(REQ-34). `harness/*/always-on.md` has no front matter.

### DM-3 Workflow front matter (changed)

```yaml
---
description: Discovery Step 2.5 — Recommend models from an optional local catalog
phase: discovery
step: 2.5
---
```

Keys: `description`, `phase`, `step`. `phase` ∈ `discovery | execution | validation |
atomic-execution | atomic-validation | orchestrated | entry | utility`. `step` is a plain
value matching `^[1-9][0-9]*(\.[1-9][0-9]*|[a-z])?$` or the JSON string `"-"`. Sort order of
steps: numeric integer part, then decimal part (absent = 0), then letter (absent first), and
`"-"` before all numbers; this order is binding for every listing of workflows, spec 10's
command reference included (adopted by spec 10, A-44; Notes → Spec 10 alignment). Registered extension keys: `loads` (spec 08), `reads`, `writes`,
`called_by` (spec 10). The values of every workflow are in DM-11.

### DM-4 Capability declaration (extended; record form adopted from spec 10 A-32)

Each `harness/<name>/capabilities.md` keeps all existing lines and gains, at the end of the
file, this section:

```text
## Capability records

always-on-path: $HOME/.claude/CLAUDE.md

name: sub-agents
state: yes
runtime: <runtime and version observed>
verified: <YYYY-MM-DD>
evidence: <URL or repository-relative path>

Limitations: <one paragraph, or "none known">
```

- A record starts at a column-0 line `name: <key>` (`<key>` matching `[a-z0-9-]+`) and ends at
  the first empty line. Allowed keys inside: `state` (required; `yes` | `no` | `unknown`),
  `runtime`, `verified` (a valid `YYYY-MM-DD`), `evidence` (repeatable, non-empty, no
  whitespace). `runtime`, `verified` and at least one `evidence` are required unless
  `state: unknown`. The paragraph after a record starting `Limitations: ` is required for
  every canonical record.
- Canonical keys, in this order: `sub-agents`, `concurrent-sub-agents`, `agent-messaging`,
  `hooks`, `worktrees`, `git`. Each appears exactly once per harness; other record names are
  extensions (`git-rails` is one). An absent canonical key is a checker finding
  (`capability-key-missing`) and reads as `unknown`, which is unavailable.
- `always-on-path:` is a location line, not a record; its value equals `always_on_path` in
  `deploy.env` byte for byte. A record named `always-on-path` is invalid.
- The canonical `hooks` record states whether shipped workflows can use native hooks on that
  harness; its `state` equals the value of the existing `hooks:` line (`yes`/`no`).
- Meanings: `sub-agents` — spawn a separate worker context; `concurrent-sub-agents` — more
  than one worker running at once; `agent-messaging` — send a later message to a worker that
  keeps its context; `hooks` — native hook events the shipped adapter uses; `worktrees` —
  isolated git worktrees for workers; `git` — run git commands in the session.
- Values are filled at implementation time from the installed runtime and its documentation;
  without collected evidence a record is `state: unknown`. This spec asserts no value.
- **Behaviour table** in `rules/contract-phases.md → ## Capabilities`, header
  `| Behaviour | Workflow | Requires | Without it |`, with at least these rows:

| Behaviour | Workflow | Requires | Without it |
|---|---|---|---|
| Orchestrated run with Implementer, Validator and Arbiter workers | `spec-run` | `sub-agents`, `agent-messaging`, `git` | Stop before Step 0; use `/pipeline <task-directory>` |
| Parallel children | `spec-run` | `worktrees`, `concurrent-sub-agents` | Stop before any action; re-run without `--parallel` |
| Devil's Advocate critic | `spec-draft` | `sub-agents`, `agent-messaging` | Inline review, `critic: inline` |
| Model-specific worker for a leaf | `atomic-execution`, `execution-execute` | `sub-agents` | Run inline when no explicit switch is required, otherwise stop |
| Hook-covered step logging | `discovery`, `execution`, `validation`, `pipeline`, `spec-run`, `retro` | `hooks` | Prompt logging with `note: approximate` |

The `Behaviour` texts above are exact; the checker identifies the required rows by them. The
"Parallel children" row is a contract for spec 12, which adds `--parallel` and wires the check
(this spec adds no flag). The six workflows that open a run log today are those containing
`run-start` (`workflows/phase-pipeline.md`, `phase-discovery.md`, `phase-validation.md`,
`phase-execution.md`, `retro.md`, `spec-run.md`).

The same section states: read the records from the always-on context; `no`, `unknown` or an
absent record means unavailable; a declared `yes` still requires the session to expose the
tool and permission at dispatch, checked without network probing; a changed record requires
new evidence.

### DM-5 Harness directory and `deploy.env` (new)

A harness directory is a directory directly under `harness/` whose name matches
`^[a-z0-9]+(-[a-z0-9]+)*$` and that contains `deploy.env`; it must also contain
`always-on.md` and `capabilities.md` (else `adapter-incomplete`). A directory whose name
matches that pattern and that holds `capabilities.md` but no `deploy.env` is also
`adapter-incomplete`, so on a valid tree "has `deploy.env`" and "has `capabilities.md`" select
the same directories; hidden directories and a directory holding only an orphaned
`always-on.md` are ignored. Retiring a harness deletes its `deploy.env` and
`capabilities.md` (and, after spec 10, its header). This is the only harness definition;
spec 10 must align to it (Notes → Spec 10 alignment). Harnesses are processed in
name order. `deploy.env` is UTF-8 with LF endings; each line is empty, a comment starting
`#`, or `<key>=<value>` with no spaces around `=`:

| Key | Required | Value grammar |
|---|---|---|
| `skills_dir` | yes | `$HOME/` followed by one or more segments `[A-Za-z0-9._-]+` joined by `/`; no `.` or `..` segment |
| `always_on_path` | yes | Same grammar |
| `project_skills_link_dir` | no | One or more such segments, relative to a project root, no `$` |

Quotes, `${`, `$(`, backticks, `~`, other variables, trailing spaces, unknown or repeated keys
are `deploy-env-invalid`. Across harnesses, the resolved `skills_dir` values must be pairwise
disjoint (neither equal nor nested) and every `always_on_path` must be distinct and outside
every `skills_dir`; otherwise `adapter-conflict`. `$HOME` expands to the process `HOME`, which must be a non-empty
absolute path (else `home-invalid`). Delivered values:

```text
# harness/claude/deploy.env
skills_dir=$HOME/.claude/skills
always_on_path=$HOME/.claude/CLAUDE.md
project_skills_link_dir=.claude/skills
```

```text
# harness/codex/deploy.env
skills_dir=$HOME/.codex/skills
always_on_path=$HOME/.codex/AGENTS.md
```

### DM-6 Deploy manifest (new)

Path: `<config>/orchestrail/deploy/<harness>.json`, where `<config>` is `XDG_CONFIG_HOME` when
non-empty, else `$HOME/.config` (same rule as `hooks/git_rails.py:277-284`). Serialized as
`json.dumps(obj, indent=2, sort_keys=True) + "\n"`:

```json
{
  "always_on_path": "/home/u/.claude/CLAUDE.md",
  "harness": "claude",
  "install_id": "<sha256 hex of '<harness>\\n<skills_dir_resolved>'>",
  "objects": [
    {"kind": "always-on", "name": null, "path": "/home/u/.claude/CLAUDE.md", "sha256": "<hex>"},
    {"kind": "skill", "name": "rule-contract-tdd", "path": "/home/u/.claude/skills/rule-contract-tdd/SKILL.md", "sha256": "<hex>"}
  ],
  "schema_version": 1,
  "skills_dir": "/home/u/.claude/skills",
  "skills_dir_resolved": "/home/u/.claude/skills",
  "source_revision": "<40 hex> or null"
}
```

- `skills_dir` and `always_on_path` are the expanded `deploy.env` values; `skills_dir_resolved`
  is `os.path.realpath(skills_dir)`. `objects` are sorted by `path`; `path` is
  `<skills_dir_resolved>/<name>/SKILL.md` for skills and the expanded always-on path.
- `install_id` identifies the target installation (the "installation identifier" of the
  previous revision). On every run the engine recomputes it; a stored value that differs is
  `target-moved`, like a differing `skills_dir_resolved`.
- Unknown keys, a `schema_version` other than 1, invalid JSON or duplicate keys are
  `manifest-invalid`. No earlier skill manifest format exists (Context fact 2), so none is
  migrated.
- Lifecycle: created at the first successful deployment of a harness; rewritten only when its
  bytes change; never deleted by the engine.

### DM-7 Journal and lock (new)

- Lock: `<config>/orchestrail/deploy.lock`, created if absent, held with an exclusive
  non-blocking `fcntl.flock` for the whole engine run, released by the kernel at exit, never
  deleted or taken over (ADR-0021 Decision 2 policy).
- Journal: `<config>/orchestrail/deploy/journal.json`, `{"schema_version": 1, "entries":
  [{"path", "old_sha256", "new_sha256"}]}` with one entry per planned change of the run
  (global files, sorted by path); `old_sha256` is `null` for a created file, `new_sha256` is
  `null` for a removed file. Written and `fsync`ed before the first change; deleted after the
  last manifest is written.
- Recovery at start when a journal exists: every entry's current state must equal its
  `old_sha256` or its `new_sha256` (absent counts as `null`); otherwise `journal-mismatch` and
  nothing is written. For the run, both digests of each entry count as owned (REQ-10), the
  plan is recomputed from the sources, executed, the manifests written and the journal
  deleted. An unreadable journal is `journal-invalid`; nothing is written.
- Temporary files: once the plan has passed every check of REQ-63 and the run is not
  deferred, and before the journal is written, the engine deletes each regular file named
  `.<basename>.orchestrail-tmp` directly inside each `skills_dir`, each `<skills_dir>/<name>`
  and each always-on parent directory, visiting only entries that `os.lstat` shows to be real
  directories (links are never followed). They are never owned, and planning ignores them.

### DM-8 Registry (existing, read only) and active detection

The registry format and validation are those of `hooks/git_rails.py:277-327`: UTF-8 lines,
each absolute, canonical (`os.path.realpath(line) == line`), without CR or NUL. Absent file:
empty registry. Unreadable file or invalid line: `registry-invalid`. Duplicate lines are
processed once.

A registered root `R` is **active** when any regular file `R/.ai/tasks/todo/*/state.md`
contains, between the line `## Phases` and the next line starting `## ` (or the end of file),
a line matching `^- (discovery|execution|validation): in-progress[ \t]*$`, or when such a file
cannot be read or decoded as UTF-8. A root that does not exist or is not a directory is
missing, not active.

### DM-9 Inventory amendment schema 2 (new; owned by this spec, reused by spec 08)

`tests/fixtures/validator-runtime/inventory-amendment.json` with `"schema": 2` has exactly the
keys `schema`, `paths`, `removed_results`, `resources`, `name_map_sha256`, `path_changes`,
`contract_changes`. Schema 1 keeps its meaning and four keys. `paths`, `removed_results` and
`resources` keep their schema-1 meaning; each `tests/` file the migration changes is added to
`paths` and to `APPROVED_PATHS` and its digest and observation changes are recorded in
`resources`.

- `path_changes`: list of `{"target", "key", "before", "after"}`. `target` is
  `result` (key = the frozen check description), `body` (key = helper function name) or
  `nonstandard` (key = 0-based index in the 94-line non-standard list before the oracle
  re-inserts its removed loop line). `before` is the exact frozen text and `after` the exact
  current text of the whole expression line, whole function, or whole line.
- `contract_changes`: list of `{"target", "key", "before", "after", "requirement", "reason"}`
  with the same first four fields, `requirement` one of the closed set `REQ-05`, `REQ-06`, `REQ-09`,
  `REQ-10`, `REQ-11`, `REQ-12`, `REQ-14`, `REQ-15`, `REQ-23`, `REQ-36`, `REQ-55`, `REQ-66` (hard-coded in the
  oracle test), `reason` a non-empty single line. `after` must differ from `before`, must not
  be `"pass"` or `"$(echo pass)"`, and must contain the literal `echo pass` and at least one
  repository path or `$(` helper call. Each entry is also a row of DM-20 → Superseded checks
  with the independent validator's verdict; an entry without a `pass` verdict there is not
  delivered. The closed set is extended only by REQ-69.
- **Token classes** for the mask: build one class per group of rows of `docs/name-map.json`
  that share a token (union over shared tokens, so the `rule` and `workflow` rows of each
  `phase-*` stem form one class). A class's name tokens are every `old` and `new` of its
  `rule`/`workflow` rows and, for `rule` rows, `rule-<old>` and `rule-<new>`; its path tokens
  are `rules/<old>.md` and `rules/<new>.md` of rule rows, `workflows/<old>.md` and
  `workflows/<new>.md` of workflow rows, and `old`/`new` of `file` rows.
- **Mask** for `path_changes`: `mask(s)` replaces (1) every whole-token occurrence (not
  preceded or followed by `[A-Za-z0-9_-]`) of a path token of class *k* with `<F k>` when it
  comes from a `file` row (whatever its prefix), otherwise with `<R k>` for a rule-row path
  and `<W k>` for a workflow-row path, then (2)
  every remaining match of `(?:rules|workflows|principles|harness|templates|docs)/[A-Za-z0-9_./-]+`
  with `<PATH>`, then (3) every whole-token occurrence of a name token of class *k* with
  `<N k>`; within each step, alternatives longest first. An entry is valid when
  `before != after` and `mask(before) == mask(after)`. Spec 08's path-only changes between
  paths that are not class tokens satisfy this mask. A change that moves a token or a mapped
  path to another class, or a mapped path between `rules/` and `workflows/` within one class
  (for example `rules/phase-discovery.md` → `workflows/discovery.md`), is rejected; a re-aim between two unmapped paths is accepted and is
  caught only by review (Risks).
- **Pin:** `name_map_sha256` is the SHA-256 of the bytes of `docs/name-map.json`, or `null`
  when the map is absent; a mismatch rejects the amendment.
- **Application:** the oracle reconstructs the frozen form of `scripts/validate-contracts.sh`
  by replacing, in list order (`path_changes` then `contract_changes`), the single occurrence
  of each entry's `after` in the current source with its `before`; zero or several occurrences
  reject the amendment. It verifies each entry against the reconstructed source (`result`: a
  check with description `key` whose expression is `before`; `body`: a function named `key`
  whose text is `before`; `nonstandard`: line `key` of the non-standard list is `before`),
  rejects a repeated `(target, key)` across both lists, then computes the inventory of the
  reconstructed source in a temporary tree laid out like the mutation test
  (`tests/validator-runtime-oracle.py:279-288`) and applies every existing comparison
  unchanged. Any invalid entry raises `ValueError`.
- **Pins and guard:** `AMENDMENT_SHA256` is updated; source-guard records are refreshed by
  `tests/fixtures/validator-runtime/README.md:9-27`.
- Check descriptions never change (they are `key`s); a description that names an old name
  stays as a frozen label.

### DM-10 Rule map (binding unless amended from 13a's accepted report via `/spec-sync`)

| Source | Target(s) | `load` |
|---|---|---|
| `rules/phase-discovery.md` | `rules/bootstrap-discovery.md`; `rules/protocol-discovery-conduct.md` | on-demand; on-demand |
| `rules/phase-execution.md` | `rules/bootstrap-execution.md` | on-demand |
| `rules/phase-validation.md` | `rules/bootstrap-validation.md` | on-demand |
| `rules/phase-atomic-execution.md` | `rules/bootstrap-atomic-execution.md`; `rules/procedure-blocker-reconciliation.md` | on-demand; on-demand |
| `rules/phase-atomic-validation.md` | `rules/bootstrap-atomic-validation.md` | on-demand |
| `rules/workflow-globals.md` | `rules/contract-phases.md` | always |
| `rules/workflow-reference.md` | `rules/contract-state-files.md`; `rules/protocol-autonomous-decision.md`; `rules/protocol-subtask-classifier.md` | on-demand (all three) |
| `rules/tdd.md` | `rules/contract-tdd.md` | always |
| `rules/git-flow.md` | `rules/contract-git-flow.md` | always |
| `rules/orchestration.md` | `rules/contract-orchestration.md` | always |
| `rules/quick-flow.md` | `rules/contract-quick-flow.md` | always |
| `rules/run-log.md` | `rules/contract-run-log.md` | always |
| `rules/language.md` | `rules/contract-language.md` | always |
| `rules/global-claude.md` | `harness/claude/always-on.md` | — (not a rule) |
| `templates/codex-global-AGENTS.md` | `harness/codex/always-on.md` | — (not a rule) |

Load modes follow the current trigger (`always_on` → `always`, `model_decision` →
`on-demand`). A rule file added after this revision is classified by 13a and amended in via
`/spec-sync`; it is never left out.

**Overflow rules (REQ-19).** Measured with DM-19 at the parent snapshot, the text that moves
into `bootstrap-atomic-execution` (front matter, `## Context Bootstrap`, `## Phase Behaviors`)
has about 393 words and `bootstrap-atomic-validation` about 328, so at least these two need
overflow. The only permitted overflow targets, all `load: on-demand`, are
`rules/protocol-execution-conduct.md`, `rules/protocol-validation-conduct.md`,
`rules/protocol-atomic-execution-conduct.md`, `rules/protocol-atomic-validation-conduct.md`
and, for Discovery, the existing target `rules/protocol-discovery-conduct.md`. Each is created
only when its bootstrap rule needs it; each created one is added to the source rule's
`new` list in DM-1 and to DM-20. The bootstrap rule's `## Phase Behaviors` then holds the
obligations that fit and the line "Load the `protocol-<phase>-conduct` rule before acting."

### DM-11 Workflow map, phase and step (binding unless amended from 13a)

| Old | New | `phase` | `step` |
|---|---|---|---|
| `phase-discovery` | `discovery` | discovery | `"-"` |
| `pd-analyze` | `discovery-analyze` | discovery | 1 |
| `pd-decompose` | `discovery-decompose` | discovery | 2 |
| `pd-select-model` | `discovery-select-model` | discovery | 2.5 |
| `pd-design` | `discovery-design` | discovery | 3 |
| `pd-finalize` | `discovery-finalize` | discovery | 4 |
| `pd-archive` | `discovery-archive` | discovery | 4b |
| `phase-execution` | `execution` | execution | `"-"` |
| `pe-execute` | `execution-execute` | execution | 1 |
| `pe-finalize` | `execution-finalize` | execution | 2 |
| `phase-validation` | `validation` | validation | `"-"` |
| `pv-contract` | `validation-contract` | validation | 1 |
| `pv-review` | `validation-review` | validation | 2 |
| `pv-issues` | `validation-issues` | validation | 3 |
| `pv-create-fixes` | `validation-create-fixes` | validation | 4 |
| `pv-classify-fixes` | `validation-classify-fixes` | validation | 4a |
| `pv-execute-fixes` | `validation-execute-fixes` | validation | 5 |
| `pv-finalize` | `validation-finalize` | validation | 6 |
| `phase-atomic-execution` | `atomic-execution` | atomic-execution | `"-"` |
| `pae-tests` | `atomic-execution-tests` | atomic-execution | 1 |
| `pae-implement` | `atomic-execution-implement` | atomic-execution | 2 |
| `pae-finalize` | `atomic-execution-finalize` | atomic-execution | 3 |
| `phase-atomic-validation` | `atomic-validation` | atomic-validation | `"-"` |
| `pav-check` | `atomic-validation-check` | atomic-validation | 1 |
| `pav-propose` | `atomic-validation-propose` | atomic-validation | 2 |
| `pav-close` | `atomic-validation-close` | atomic-validation | 3 |
| `phase-composite-validation` | `composite-validation` | atomic-validation | `"-"` |
| `phase-pipeline` | `pipeline` | orchestrated | `"-"` |

Unchanged names: `spec-run` (orchestrated), `spec-draft`, `spec-sync`, `bugfix`,
`onboard-legacy-project` (entry), `adr-new`, `context-pack`, `retro`, `restack`,
`compress-state`, `suggest-commit-message`, `suggest-commit-pr`, `suggest-pr-description`
(utility); each has `step: "-"`. Descriptions keep their text except stale names; the
`workflows/pd-archive.md` description becomes one line.

### DM-12 Section map for split rules (binding unless amended from 13a)

- `rules/workflow-reference.md`: `## Autonomous Decision Protocol` (`:417-480`) →
  `protocol-autonomous-decision`; `## Autonomous Subtask Classifier` (`:481-553`, with its
  fenced `## Decomposition Decisions` at `:543`) and `## Decomposition Rules` (`:554-577`) →
  `protocol-subtask-classifier`; the text before the first heading and every other line
  starting `## `, inside or outside fences, with its section → `contract-state-files`.
- `rules/phase-discovery.md`: `## Context Bootstrap` → `bootstrap-discovery`;
  `## Codebase Reading Rules`, `## Decision Protocol` → `protocol-discovery-conduct`;
  `bootstrap-discovery` gains `## Phase Behaviors`, which cites the
  `protocol-discovery-conduct` rule.
- `rules/phase-atomic-execution.md`: `## Context Bootstrap`, `## Phase Behaviors` →
  `bootstrap-atomic-execution`; `## Blocker Reconciliation` → `procedure-blocker-reconciliation`.
- For `rules/phase-discovery.md` and `rules/phase-atomic-execution.md`, the text before the first
  `## ` heading (front matter and title) goes to the bootstrap target (13a DM-5 `(preamble)`).
- A moved section keeps its heading text, its `###` subsections and its body; edits are limited
  to DM-1 substitutions and REQ-19 relocations recorded in DM-20.
- The section-level map is recorded in the semantics record (DM-20), one row per source
  `## ` line; `docs/name-map.json` records only file-level renames.

### DM-13 Legacy objects

Global: `$HOME/.codeium/windsurf/global_workflows`, `$HOME/.codeium/windsurf/global_rules`.
Per project root `P`: `P/.windsurf`, `P/.devin`. An object exists when `os.lstat` succeeds
(a symbolic link is reported and not followed).

### DM-14 Always-on assembly (until spec 10 replaces it)

Deployed bytes = bytes of `harness/<name>/always-on.md` + `"\n<!-- Logging capabilities -->\n"`
+ bytes of `harness/<name>/capabilities.md` + `"\n## Current hook installation\n\ninstallation-result: "`
+ result + `"\n"`, the same composition as `scripts/sync.sh:58-67`; result per REQ-65.

### DM-15 Installed names

Per harness: `workflows/<stem>.md` → `<stem>`; `rules/<stem>.md` → `rule-<stem>`;
`principles/<stem>.md` → `principle-<stem>` (spec 08 later adds `ref-<stem>`). Each installed
name `n` is the directory `<skills_dir>/<n>/` with one managed file `SKILL.md` equal to the
source bytes. `docs/PIPELINE.md` is not a source.

### DM-16 Executable references

In scan set E (`rules/*.md`, `workflows/*.md`, `harness/*/always-on.md`), outside fenced code
blocks, a single-backtick span is an executable reference when its content matches:

1. A span not containing ` → ` that matches `^/([a-z0-9][a-z0-9-]*)(\.md)?( .*)?$` — a command
   (a span containing ` → ` is tested against form 2 only); the name must be an installed workflow
   name; a `.md` suffix is `reference-md-suffix`.
2. `^/?([a-z0-9][a-z0-9-]*)(\.md)? → (#{2,3} .+?)( → (#{2,4} .+))*$` — a section reference;
   when the stem is a rule or workflow stem (or `.md` is absent), the target must exist and
   each heading must match a line of the target file, in order; a heading `H` matches a line
   `L` when `L == H` or `L` starts with `H + " — "`; `.md` after a rule
   or workflow stem is `reference-md-suffix`; stems with `.md` that are not rules or
   workflows (`state.md`, `plan.md`) are document references and not checked.
3. `^rule-([a-z0-9-]+)$`, or `^([a-z0-9][a-z0-9-]*)$` immediately followed by ` rule` or
   ` rules` — the rule stem must exist.
4. `^(rules|workflows|harness|templates)/[A-Za-z0-9_./-]+$` — a repository path; it must
   exist unless it contains `*` or `<`. Other prefixes (`principles/`, `docs/`, `scripts/`)
   are not checked because instructions also use them for consumer-project paths (for
   example `principles/coding.md` at `rules/phase-execution.md:28`).

A finding this grammar produces on the parent tree is a pre-existing defect: the delivery
fixes it and lists it in DM-20 → Pre-existing reference defects.

### DM-17 Scan sets and stale-name forms

- **R (references and stale names):** `rules/**`, `workflows/**`, `harness/**`,
  `principles/**`, `templates/**` (dot directories included), `hooks/**`, `scripts/**`,
  `tests/**`, `CLAUDE.md`, the root `README.md`, `docs/*.md` at the docs root (not subdirectories),
  `.ai/principles/*.md`, `.ai/context/*.md`, `.ai/memory/architecture.md`, and
  `tests/golden/cases/*/case.json` if present. Excluded entirely: `docs/name-map.json`,
  `docs/USAGE.md → ## Renamed commands and rules`, `tests/fixtures/validator-runtime/**`
  (frozen data), `scripts/check-lint-instructions.py` and `scripts/check-deploy-skills.py`
  (their fixtures need old names). In `scripts/validate-contracts.sh` the checker skips the
  quoted description of every `check "<description>"` and every line whose first non-blank
  character is `#`. A remaining occurrence that must stay (synthetic fixture data in a test,
  for example) is allowed only when DM-20 → Retained old names lists its path and exact line
  text with a reason. The checker finds the record by the glob
  `docs/audits/*-rule-migration-map.md`: no match means an empty table; more than one is
  `semantics-record-ambiguous`. Known entries: the frozen removed-result names in
  `tests/validator-runtime-oracle.py:54-55` (for example `pd-analyze references
  architecture.md`, a check description) stay as they are.
- **L (legacy mentions):** `rules/**`, `workflows/**`, `harness/**`, `principles/**`,
  `templates/**`, `scripts/sync.sh`, `scripts/setup-new-project.sh`,
  `scripts/setup-all-repos.sh`, `scripts/setup-umbrella.sh`, `scripts/link-skills.sh`,
  `CLAUDE.md`, `docs/USAGE.md` except its section `## Removed integrations`. A mention is a
  case-insensitive match of `windsurf`, `codeium` or `\bdevin\b`.
- **Stale-name forms** for every DM-1 row: workflow rows — `/<old>`, `<old>.md`,
  `workflows/<old>.md`, and the bare whole token `<old>`; rule rows — `rule-<old>`,
  `rules/<old>.md`, `<old>.md`, `` `<old>` `` followed by ` rule`/` rules`, `` `<old> → ``,
  and the bare whole token only for `workflow-globals`, `workflow-reference` and the five
  `phase-*` stems; file rows — the old path and, for `global-claude` and
  `codex-global-AGENTS`, also `<stem>.md` and the bare whole token `<stem>`. An occurrence
  that is part of a `new` path of the same row (such as `PIPELINE.md` inside
  `docs/PIPELINE.md`) is never stale. A whole token is not preceded or
  followed by `[A-Za-z0-9_-]`.

### DM-18 Reserved names `harness/<name>/reserved-names.txt` (optional, new)

```text
runtime: <runtime and version>
verified: <YYYY-MM-DD>
evidence: <URL>

<name>
```

Three header lines, one empty line, then one name per line matching
`^[a-z0-9][a-z0-9-]*$`; `#` lines are comments. Each name is a built-in command or public
skill of that harness taken from the cited listing. An absent file means no listing is
available; the checker prints `info reserved-names-absent <harness>` and finds no collision.

### DM-19 Word count

Decode as strict UTF-8 (failure: `input-encoding`); a file containing U+001C–U+001F is
`input-encoding`; words = `len(text.split())` over the whole text including front matter,
headings and code (spec 08 A-09; spec 10 Terminology).

### DM-20 Migration semantics record (new)

`docs/audits/YYYY-MM-DD-rule-migration-map.md` (date of delivery), indexed in
`docs/README.md`, with a table `| Source | Section | SHA-256 | Target | Target section |
Consumers | Evidence | Reviewed |`: one row per `## ` line of every split or renamed rule (DM-10),
`SHA-256` of the source section text at the parent commit, consumers = files citing it after
migration, evidence = the check or review that shows each condition, exception, writer
authority, stop and resume rule is kept. A relocation forced by REQ-19 and a REQ-21 merge are
rows with their reason. Further sections, each a table:

- `## Superseded checks` — `| Key | Before | After | Requirement | Verdict |`, one row per
  DM-9 `contract_changes` entry; `Verdict` is `pass` or `fail` with one line of reason.
- `## Retained old names` — `| Path | Line text | Reason |` (DM-17).
- `## Pre-existing reference defects` — `| Path:line | Reference | Fix |`: dangling references
  and missing headings the checker finds on the parent tree, fixed by this delivery.

Every row of the first table carries a `Reviewed` column `<role> <YYYY-MM-DD> pass|fail`, and
the record ends with one line `Signed: <reviewer role> <YYYY-MM-DD> <commit sha>` written by
the independent validator.

## Contracts & Interfaces

### `scripts/sync.sh`

`scripts/sync.sh [--from <dir> | --from=<dir>] [--force] [-h | --help]` — `--from` and
`ORCHESTRAIL_HOME` keep their current meaning (`scripts/sync.sh:4-30`); `--force` is passed to
the engine; other arguments keep today's behaviour. Steps in order:

1. Source checks (current `:26-34`, with `harness` added to the required directories).
2. `bash "$ROOT/scripts/validate-contracts.sh"` (unchanged, `:40-45`).
3. Runtime guard (REQ-56).
4. Hook installation (unchanged, `:51-56`).
5. `bash "$ROOT/scripts/report-legacy-artifacts.sh" global`.
6. For each root printed by `python3 -I "$ROOT/scripts/deploy-skills.py" list-projects`
   (NUL-separated, existing directories only, source checkout excluded):
   `bash "$ROOT/scripts/report-legacy-artifacts.sh" project <root>`.
7. `python3 -I "$ROOT/scripts/deploy-skills.py" deploy --from "$ROOT" --hook-result "$HOOK_INSTALL_RESULT" [--force]`.
8. Summary listing the deploy paths read from the adapters (no literal harness paths).

Exit: 0 when step 7 exits 0; 3 when the engine exits 3 (deferred, nothing written); 1 for every
other failure. Removed: steps 1, 2 and 5b of the current script (`:69-87`, `:193-284`) and
every literal `~/.claude` or `~/.codex` path.

### `scripts/deploy-skills.py`

```text
python3 -I scripts/deploy-skills.py deploy --from <root> --hook-result <json-line> [--force]
python3 -I scripts/deploy-skills.py list-projects
python3 -I scripts/deploy-skills.py link-project --from <root> --project <dir>
```

- `deploy`: takes the lock (DM-7), reads adapters (DM-5), sources (DM-15), manifests (DM-6),
  journal (DM-7), registry (DM-8) and name map (DM-1); validates everything (REQ-63); builds
  the plan; evaluates active consumers (REQ-43); writes; runs the project pass.
- Plan per harness: for each installed name and the always-on file — absent: `create`; equal
  bytes: nothing (recorded as owned if not yet); different bytes and owned: `replace`;
  different bytes while the harness has **no** manifest file, path not a symbolic link:
  `adopt` (replace and record; this keeps today's overwrite of Orchestrail-managed paths on
  the first run only, P1; interim behaviour, see Notes → Relationship to spec 11a); different bytes while a manifest exists and the path is either
  unrecorded or recorded with another digest: `ownership-conflict`, printed as
  `ERROR ownership-conflict <path>: changed since the last deployment; save your changes elsewhere, then delete the file or restore its deployed bytes, and rerun`.
  Each manifest entry no longer planned: current bytes equal the
  recorded digest → `remove` the file, then remove its directory if empty (else print
  `keep-nonempty <dir>`); different bytes → print `release-modified <path>` and drop the entry;
  absent → drop the entry. Leftover skills → `leftover` lines (REQ-57).
- Output (standard output, in order): one line per action `create|replace|adopt|remove <path>`,
  `keep-nonempty <dir>`, `release-modified <path>`, `leftover <dir> (not removed; review, then remove it manually)`,
  then `registry absent: …` (when applicable), then project lines and `forced <root>` lines (with `--force`), then
  `note: task starts during deployment are not detected; run sync when no pipeline run is starting`.
  Nothing is written and no action line is printed when the plan is empty and the manifests are
  unchanged.
- Exit codes: 0 done or nothing to do; 1 error (standard error `ERROR <code>: <detail>`); 2
  usage (bad option, `--hook-result` containing CR or LF); 3 deferred (`deferred: active
  consumers` then `active <root> <task-directory>` lines; nothing written).
- Before the first write, the engine also checks that each `skills_dir`, each existing
  `<skills_dir>/<name>` and the parent of each always-on path is absent or a directory, and
  that each always-on path is absent or a regular file; otherwise `unsafe-target`. `io-error`
  means an operating-system error during the write phase. Writes use a temporary file
  `.<basename>.orchestrail-tmp` in the target's directory, flushed and renamed with
  `os.replace`.
- Engine error codes: `deploy-env-invalid`, `home-invalid`, `adapter-incomplete`, `adapter-conflict`,
  `name-collision`, `manifest-invalid`, `journal-invalid`, `journal-mismatch`,
  `ownership-conflict`, `unsafe-target` (symbolic link at a managed path or skill directory,
  path outside `skills_dir_resolved`), `target-moved` (`skills_dir_resolved` differs from the
  manifest), `deploy-locked`, `registry-invalid`, `name-map-invalid`, `io-error`. An `io-error`
  after the journal was written leaves the journal for recovery and never prints a success line.
- `list-projects`: prints existing registered roots except the source root; exit 1 with
  `registry-invalid`; empty output for an absent registry.
- `link-project`: for each harness with `project_skills_link_dir` D, creates `<project>/D` if
  absent and links every skill directory present in `skills_dir` as `<project>/D/<name>` →
  `<skills_dir>/<name>/` when no entry exists at that path; exit 0, or 1 on an error.

### Project pass (inside `deploy`)

For each registry root in order, deduplicated: missing → `project missing <root>`; equal to the
source root → `project skipped (source checkout) <root>`; active and no `--force` →
`project skipped (active task) <root>`; otherwise, for each harness with
`project_skills_link_dir` D where `<root>/D` is a directory and not a symbolic link: remove
symbolic links directly in it that are broken and whose `os.readlink` text starts with the
harness `skills_dir` or `skills_dir_resolved` followed by `/` (owned links); add missing links
as `link-project` does; then apply the current `.ai/` ignore step unchanged
(`scripts/sync.sh:267-276`); print `project updated <root> (linked <n>, unlinked <n>)`. Nested
roots are processed independently. No other project file is written; in particular the
pass never creates, refreshes or removes profile files (spec 11a owns profiles).

### Legacy reporter `scripts/report-legacy-artifacts.sh`

`report-legacy-artifacts.sh global` | `report-legacy-artifacts.sh project <dir>`. For each
existing legacy object (DM-13) it prints
`legacy: <path> — created by an earlier Orchestrail version; review it, then remove it manually if unused: rm -r -- <quoted path>`
with the path quoted by `printf %q`. It writes nothing, follows no link, never recurses, exits 0
after reporting (also when nothing exists) and 2 on a usage error.

### `scripts/setup-new-project.sh`

Steps 2 and 3 (`:85-141`) are removed; it calls
`report-legacy-artifacts.sh project "$PROJECT_DIR"`; step 4 (`:143-164`) is replaced by
`python3 -I deploy-skills.py link-project --from "$WORKFLOWS_SRC" --project "$PROJECT_DIR"`,
and when Python 3.11+ is unavailable it prints `WARNING: skill links unavailable: Python 3.11
or newer is required` and continues; next-step lines name `/discovery` and no editor. The
registration block (`:264-321`) is unchanged.

### `/spec-run` preflight

Added to `workflows/spec-run.md → ## Guard`: read the capability records from the always-on
context. For each required key whose record is absent, `no` or `unknown`, or whose tool is not
exposed in the session: **stop**:
`"spec-run requires capability <key> (declared: <yes|no|unknown|absent>; session tool: <available|unavailable>). <next-step>"`
`<next-step>` is `Use /pipeline <task-directory> for the single-session path.` when `<key>` is
`sub-agents`, `agent-messaging` or `git`, and `Re-run without --parallel.` when `<key>` is
`worktrees` or `concurrent-sub-agents`, because `/pipeline` has no parallel mode (spec 12).
Keys are checked in the order `sub-agents`, `agent-messaging`, `git`, `worktrees`,
`concurrent-sub-agents` and the message names the first failing key, so a run that also lacks a
non-parallel key is directed to `/pipeline`. The Guard holds one `**stop**` line (the template
above) and states the two `<next-step>` texts on lines that do not contain `**stop**`.
The check runs before Step 0 and before any write, branch, commit, spawn or run-log record.

### `scripts/lint-instructions.py`

`python3 -I scripts/lint-instructions.py [--root <dir>]` (default: the parent of `scripts/`).
One finding per line on standard output: `<code> <path>:<line> <message>` (`<line>` 0 when the
finding concerns a whole file); `info …` lines do not affect the exit code. Exit 0 no finding,
1 findings, 2 usage or unreadable root. Codes: `metadata-syntax`, `metadata-missing-field`,
`metadata-unknown-field`, `metadata-duplicate-key`, `metadata-invalid-value`,
`trigger-present`, `invocation-missing`, `invocation-duplicate`, `kind-prefix-invalid`,
`name-collision`, `installed-name-collision`, `bootstrap-sections`, `bootstrap-size`,
`bootstrap-table-invalid`, `resolution-rule-missing`, `always-on-size`, `legacy-mention`,
`reference-md-suffix`, `reference-missing`, `heading-missing`, `stale-name`,
`name-map-invalid`, `usage-map-mismatch`, `reserved-name-collision`, `capability-schema`,
`capability-key-missing`, `capability-behaviour-table-invalid`, `hooks-state-mismatch`,
`always-on-path-mismatch`, `deploy-env-invalid`, `adapter-incomplete`, `input-encoding`,
`semantics-record-ambiguous`.

Triggers not defined elsewhere: `bootstrap-table-invalid` — the header line of REQ-15 is
absent from `contract-phases → ## Context Bootstrap`, the table has other than five rows, or a
`Skill` cell is not `rule-bootstrap-<phase>` of an existing rule; `resolution-rule-missing` —
the REQ-14 anchored line is absent from `contract-phases → ## Rule references`, or occurs more
than once in scan set R; `capability-behaviour-table-invalid` — the DM-4 header is absent, a
required `Behaviour` text is missing, a `Requires` cell names a key that is neither canonical
nor the `name:` of a capability record present in every harness's `capabilities.md` (an
extension key such as spec 18's `sub-agent-effort`, REQ-67), or a
`Workflow` cell names a workflow that does not exist; `usage-map-mismatch` — the DM-1 table is
absent from `docs/USAGE.md` or differs from the map; `name-map-invalid` — any DM-1 rule is
broken; `kind-prefix-invalid` — a top-level rule stem's prefix before the first `-` is not a
DM-2 kind; `input-encoding` — DM-19.

### Suites

`python3 -I scripts/check-lint-instructions.py` and `python3 -I scripts/check-deploy-skills.py`:
`unittest` programs; exit 0 when all cases pass, 1 otherwise. Each case builds a fixture root
in a temporary directory (copying the needed source directories or writing minimal ones),
sets `HOME`, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` to temporary paths, and for sync cases
replaces the validator in the private copy with `#!/bin/bash\nexit 0\n` as
`tests/hook-install.sh:135-138` does. Isolated deployment for other specs (08) is the same
procedure: run `scripts/sync.sh --from <copy>` with those variables redirected.

## Non-Functional Requirements

| Attribute | Target and standard | Verification |
|---|---|---|
| Always-on body | ≤ 1,200 words per harness (REQ-54) | Checker `always-on-size`; AC-34 |
| Bootstrap rule | ≤ 300 words, exactly two sections (REQ-19) | Checker; AC-11 |
| Spec 08 follow-up | ≤ 700 words per top-level rule and ≤ 6,000 words per always-on set are spec 08's acceptance, not a precondition of this spec; they do not replace 300/1,200 | Spec 08 |
| Word counting | DM-19 | Suite cases |
| Checker runtime | Target ≤ 30 s on the repository; the measured time, machine and tool versions are recorded in the ADR's verification; an overrun is reported, not hidden | Timed run at delivery |
| Repeat deployment | A second `deploy` on the same inputs writes no byte, link or manifest | AC-04, AC-05 |
| Reference integrity | Zero `reference-missing`, `heading-missing`, `stale-name` on the delivered tree | Checker exit 0 |
| Preservation | Zero removed or overwritten foreign or modified objects | AC-05, AC-24 |
| Offline checks | Zero model or network calls in the checker and suites | AC-27 |
| Security | Deployment edits user-global files: ownership, path, symbolic-link, lock and recovery rules of REQ-42–REQ-45 apply; inputs are data (REQ-44) | AC-24, AC-26 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | Requirement |
|---|---|---|
| Registry absent | Project pass prints `registry absent: no projects registered; run scripts/setup-new-project.sh in each project`; global deployment proceeds; no search of the home directory | REQ-09 |
| Registry unreadable or an invalid line | `registry-invalid`, exit 1, nothing written (not treated as empty) | REQ-09, REQ-63 |
| Registered root missing | `project missing <root>`; counts neither as active nor as updated | REQ-09 |
| Duplicate registry line | Processed once | REQ-09 |
| Task `state.md` unreadable | Root is active | REQ-59 |
| Plan empty, active project exists | Project pass runs; the active project is skipped and reported | REQ-09, REQ-43 |
| Plan non-empty, active consumer, no `--force` | Exit 3, nothing written, consumers listed | REQ-43 |
| Same with `--force` | Proceeds; each forced consumer printed as `forced <root>` (interim output, Notes → Relationship to spec 11a) | REQ-43 |
| No manifest (first run) | Existing managed paths adopted (interim, Notes → Relationship to spec 11a); nothing removed; leftovers reported | REQ-10, REQ-57 |
| Manifest exists and a new source skill's path already holds other bytes | `ownership-conflict`, nothing written | REQ-42 |
| Owned skill edited by the user | `ownership-conflict` when still planned; `release-modified` when obsolete; never overwritten or removed | REQ-42 |
| User edited the deployed always-on file (as `rules/language.md:20-21` advises today) | `ownership-conflict` with the resolution text; the delivery rewrites both advisories so they no longer direct edits to the managed file (Q-06) | REQ-42 |
| Two harnesses with equal or nested `skills_dir` | `adapter-conflict`, nothing written | REQ-63 |
| Source checkout registered and active, plan non-empty | Counts as an active consumer: exit 3 without `--force` | REQ-43 |
| `docs/name-map.json` absent | Empty map: no stale-name, leftover or mask tokens | REQ-57 |
| Run killed during the write phase leaves `.SKILL.md.orchestrail-tmp` | Ignored by planning; deleted by the next run that passes validation, before its journal (DM-7) | REQ-45 |
| Re-delivery after a rollback with the old sync | Owner deletes `<config>/orchestrail/deploy/` first (Notes → Rollback); otherwise `ownership-conflict` for every overwritten path | REQ-42, REQ-45 |
| Foreign file inside an owned skill directory | Directory kept, `keep-nonempty` | REQ-42 |
| Symbolic link at `SKILL.md` or skill directory | `unsafe-target`, nothing written | REQ-42 |
| `~/.claude/skills` itself a symbolic link | Allowed; resolved path recorded; a later change of the resolved path is `target-moved` | REQ-42 |
| Manifest invalid or of unknown version | `manifest-invalid`, nothing written | REQ-44, REQ-63 |
| Second engine run while one holds the lock | `deploy-locked`, exit 1, nothing written, no takeover | REQ-45 |
| Crash after journal, before manifest | Next run recovers (DM-7) and completes | REQ-45 |
| Target edited between crash and rerun | `journal-mismatch`, nothing written | REQ-45 |
| `deploy.env` with `$(…)`, quotes, unknown or repeated key | `deploy-env-invalid` naming file and line | REQ-44 |
| `HOME` empty or relative | `home-invalid` | REQ-44 |
| Harness directory without `always-on.md` | `adapter-incomplete` | REQ-35 |
| Directory with `capabilities.md` and no `deploy.env` | `adapter-incomplete`; a directory holding only an orphaned `always-on.md` is ignored | REQ-35 |
| Python missing or older than 3.11 | Sync exit 1 before any write; setup continues with a warning | REQ-56 |
| Hook installer fails | Installation record carries its unavailable JSON; deployment continues | REQ-65 |
| Legacy directory is a symbolic link | Reported, not followed | REQ-07 |
| Path with spaces or quotes in a legacy line | Quoted by `printf %q` | REQ-07 |
| Capability record without evidence and `state: yes` | `capability-schema` | REQ-38 |
| Capability `unknown` at `/spec-run` | Stop before any action | REQ-37 |
| Bootstrap over 300 words after the move | Excess moves to the DM-10 overflow rule of that phase, recorded in DM-20 | REQ-19 |
| New rule or workflow file not in DM-10/DM-11 | Discovery stops; amended through `/spec-sync` | REQ-24 |
| Name equal to a reserved name | Prefixed map entry `orchestrail-<name>` | REQ-41 |
| Reserved-name listing unavailable | `info reserved-names-absent`; no prefix | REQ-41 |
| Amendment `after` text occurs twice | Oracle rejects | REQ-51 |
| A frozen check whose asserted contract is superseded | `contract_changes` entry; the check is replaced in place | REQ-52 |
| Glob in a re-pointed test matches nothing | Delivery incomplete (REQ-53) | REQ-53 |
| Old step names in historical run logs | Kept unchanged; lint does not enforce historical names | REQ-64 |
| Concurrency of the git-rails hook | Unaffected: the hook only reads the registry | REQ-08 |
| Authorization | Not applicable: local single-user scripts; ownership and the active-task freeze are the guards | REQ-42, REQ-43 |

## Acceptance Criteria

- **AC-01 — moved to 13a.** The full audit report is accepted as an input and does not count
  as delivery of this migration (REQ-01–REQ-04, withdrawn).
- **AC-02** (REQ-05) — Given an isolated home without `.codeium` and a fixture source copy, when
  `scripts/sync.sh --from <copy>` runs, then no path under `$HOME/.codeium` exists afterwards;
  and given an additional fixture harness `harness/demo/` with its own `deploy.env`,
  `always-on.md` and `capabilities.md`, then its skills and always-on file are deployed to its
  declared paths without any code change, and `scripts/deploy-skills.py` and
  `scripts/sync.sh` contain no string literal `claude`, `codex`, `.claude` or `.codex`.
- **AC-03** (REQ-06, REQ-07) — Given a project with `.windsurf/rules/tdd.md` and `.devin/` of
  known bytes, when setup runs and then sync runs, then those bytes and entries are unchanged,
  each of the two runs prints exactly one `legacy:` line per object, and a fresh project
  directory gets no `.windsurf` or `.devin`.
- **AC-04** (REQ-08, REQ-09, REQ-43) — Given a registry with roots A, B (inactive), M
  (missing), A again and C (active), and a completed earlier deployment, when sync runs with
  unchanged sources, then A and B get missing skill links once each, M is reported missing, C
  is reported skipped, and the registry bytes are unchanged; and when a source skill changes
  and sync runs without `--force`, then it exits 3, lists C, and no global file, manifest or
  project link changes; with `--force` it deploys and prints `forced <C>`; and when the
  source checkout itself is registered and active, with A, B and C inactive, the same changed
  run exits 3 listing the source root.
- **AC-05** (REQ-10) — Given a manifest owning skills `x` and `y`, the source no longer
  providing `x` and `y` but newly providing `w`, `y/SKILL.md` edited by the user, and a
  foreign directory `z`, when sync runs, then `x` is removed, `w` is created, `y` and `z` keep their bytes
  with `release-modified` for `y`; and given no manifest and an obsolete `x`, nothing is
  removed.
- **AC-06** (REQ-11, REQ-29) — Given a fixture rule containing `Windsurf` on line 7, when the
  checker runs, then it prints `legacy-mention rules/<file>:7`; the same text inside
  `scripts/report-legacy-artifacts.sh` or `docs/USAGE.md → ## Removed integrations` yields no
  finding; on the delivered repository the checker prints no `legacy-mention`, and `docs/USAGE.md`
  contains the line `## Removed integrations`.
- **AC-07** (REQ-12, REQ-13, REQ-30) — Given fixture rules and workflows with valid front
  matter (including steps `2.5`, `4b`, `"-"`), when the checker runs, then no metadata finding
  appears; and fixtures with a missing `load`, a `trigger` key, a repeated key, `phase:
  editor`, `step: 0`, `step: 2.5.1`, an unregistered key and a two-line description each yield
  their code.
- **AC-08** (REQ-14, REQ-15) — Given the delivered repository, then the REQ-14 anchored line
  occurs exactly once in scan set R, inside `contract-phases → ## Rule references`; the
  bootstrap table header is `| Phase | Skill | Loaded by |` with five rows naming existing
  `rule-bootstrap-*` skills; no file of scan set R contains `bare basename` or a header cell
  starting `Rules file`; and fixtures removing the anchored line or adding a sixth table row
  yield `resolution-rule-missing` and `bootstrap-table-invalid`.
- **AC-09** (REQ-16) — Given the delivered `contract-phases → ## Capabilities`, then it holds
  the five behaviour rows of DM-4 with their exact `Behaviour` texts and canonical keys only;
  each workflow file named in their `Workflow` cells contains the text
  `` `contract-phases → ## Capabilities` ``; `workflows/spec-draft.md` still contains
  `critic: inline`; and a fixture table with the key `subagents` or a missing required row
  yields `capability-behaviour-table-invalid`.
- **AC-10** (REQ-17, REQ-18, REQ-28) — Given the delivered repository, then the five
  `rules/bootstrap-*.md` exist and the checker reports no collision; and given fixtures with
  `rules/discovery.md` beside `workflows/discovery.md`, and with `rules/tdd.md` beside
  `workflows/rule-tdd.md` (both install as `rule-tdd`), the checker reports `name-collision`
  and `installed-name-collision`; a casefold case (`workflows/Retro.md` beside
  `workflows/retro.md`) also yields `installed-name-collision` and is skipped, with the reason
  printed, when the temporary filesystem is case-insensitive.
- **AC-11** (REQ-19, REQ-32) — Given the delivered bootstrap rules, then each has ≤ 300 words
  and only the two sections; and fixtures with 301 words, or with a third `## ` section, each
  yield one finding.
- **AC-12** (REQ-20) — Given the delivered tree, then `rules/procedure-blocker-reconciliation.md`
  holds the three cases verbatim except DM-1 substitutions, `workflows/atomic-execution.md`
  and `workflows/atomic-execution-implement.md` cite the `procedure-blocker-reconciliation`
  rule, and no other rule contains `## Blocker Reconciliation`.
- **AC-13** (REQ-21) — Given the delivered tree, then exactly one rule holds the code-reading
  budget line and the autonomous/step-by-step mode text from `rules/phase-discovery.md:36-64`,
  and DM-20 names it.
- **AC-14** (REQ-22, REQ-31) — Given fixtures with `` `/discovery.md` ``,
  `` `contract-tdd.md → ## Rules` ``, `` `/nonexistent` `` and
  `` `contract-tdd → ## Missing` ``, when the checker runs, then it reports
  `reference-md-suffix` twice, `reference-missing` and `heading-missing`; a fenced example and
  `` `state.md → ## Phases` `` yield nothing; every explicit child call in
  `workflows/pipeline.md` and the phase orchestrators is a `/<new-name>` command.
- **AC-15** (REQ-23) — Given the delivered tree, then `docs/PIPELINE.md` exists,
  `workflows/PIPELINE.md` does not, a fixture deployment installs no `PIPELINE` skill, and
  every `workflows/*.md` has exactly one `Invocation: ` line.
- **AC-16** (REQ-24, REQ-25, REQ-26) — Given the delivered tree, then every top-level rule stem
  starts with a DM-2 kind, the checker reports no `stale-name`, `reference-missing` or
  `kind-prefix-invalid` (a fixture line naming `docs/PIPELINE.md` yields none, one naming
  `workflows/PIPELINE.md` yields `stale-name`), and `contract-phases → ## Rule references` documents `rule-`,
  `principle-` and the reserved `ref-` namespaces.
- **AC-17** (REQ-24, REQ-46) — Given the parent-commit versions of the split rules, then every
  line starting `## ` in them occurs exactly once in the target DM-12 names, and DM-20 has one
  signed row per such line.
- **AC-18 — withdrawn, replaced by AC-21** (REQ-27).
- **AC-19** (REQ-33) — Given the delivery, then a new accepted ADR and its `index.md` row exist,
  ADR-0003's index status names the supersession of deployment targets only, and ADR-0018's
  status names the schema-2 amendment.
- **AC-20** (REQ-34) — Given the delivery, then the six knowledge files of REQ-34 together
  contain the strings `deploy.env`, `orchestrail/deploy/`, `docs/name-map.json`,
  `scripts/lint-instructions.py` and `registry`; `.ai/principles/domain.md` has a vocabulary
  row for each Terminology term and defines `bootstrap`, `contract`, `protocol` and
  `procedure` with the DM-2 meanings; `.ai/principles/coding.md` no longer contains
  `trigger: always_on`; none of the six has a legacy mention.
- **AC-21** (REQ-39, REQ-40, REQ-41) — Given the delivered tree, then every DM-11 rename is
  applied, `docs/USAGE.md → ## Renamed commands and rules` equals `docs/name-map.json`, no
  workflow or skill exists under an old name; and given a fixture `reserved-names.txt`
  listing `pipeline`, the checker reports `reserved-name-collision` until the map entry
  becomes `orchestrail-pipeline`.
- **AC-22** (REQ-35, REQ-36) — Given a fixture deployment, then each deployed always-on file
  equals the DM-14 assembly with the declaration exactly once, each harness directory holds
  the three required files, and every line of the parent-commit `capabilities.md` files is
  still present in order.
- **AC-23** (REQ-37, REQ-38) — Given `workflows/spec-run.md`, then its `## Guard` holds the
  preflight for `sub-agents`, `agent-messaging` and `git` with the stop message of Contracts →
  `/spec-run` preflight, before Step 0 (the parallel clause is wired by spec 12 through the DM-4
  row), and the Guard states both `<next-step>` texts, the `/pipeline` text for the three
  non-parallel keys and the `Re-run without --parallel.` text for `worktrees` and
  `concurrent-sub-agents`; and given fixture records with a `yes`
  record lacking `evidence`, an invalid date, and a duplicated name, the checker reports
  `capability-schema` for each.
- **AC-24** (REQ-42, REQ-44) — Given fixtures with a symbolic link at a managed `SKILL.md`, a
  manifest with an unknown key, a `deploy.env` value `$HOME/$(id)`, an owned skill edited by
  the user, a deployed always-on file edited by the user, and (with a manifest present) a new
  source skill whose path already holds foreign bytes, when `deploy` runs, then each run exits
  1 with its code (`unsafe-target`, `manifest-invalid`, `deploy-env-invalid`,
  `ownership-conflict` three times, the last two printing the resolution text) and no file in
  the fixture home changes.
- **AC-25** (REQ-43) — Given an active project whose `.claude/skills` links point at the global
  skills and a changed source skill, when sync runs without `--force`, then the global skill
  bytes are unchanged (skipping the project alone is not protection), and every successful
  `deploy` output ends with the residual-race `note:` line.
- **AC-26** (REQ-45) — Given a held lock, then a second `deploy` exits 1 `deploy-locked` without
  writes; given a journal whose entries are half applied, then the next run exits 0 with all
  targets at their new digests and no journal; given a journal entry whose target was edited
  afterwards, then `journal-mismatch` and no write; and after every suite run, successful or
  failed, no `.*.orchestrail-tmp` file remains and every planned target holds either its old
  or its new digest.
- **AC-27** (REQ-46, REQ-47) — Given the suites, then they pass with `HOME`,
  `XDG_CONFIG_HOME` and `XDG_STATE_HOME` redirected; the modification times of the real
  `~/.claude`, `~/.codex` and `<config>/orchestrail` entries are unchanged; a source check in
  each suite parses `scripts/deploy-skills.py`, `scripts/lint-instructions.py` and the suite
  itself with `ast` and finds no import of `socket`, `ssl`, `http`, `urllib` or `ftplib` and no
  subprocess argument list whose program is other than the literal `bash`, `python3`, `git`,
  `sys.executable` or a repository script under test (any other non-literal program fails); and the DM-20 main table has a `pass` row for every source
  `## ` line.
- **AC-28** (REQ-48) — Given a Discovery plan with more than eight subtasks, then the split is
  recorded in `.ai/specs/README.md` before execution and every active REQ belongs to exactly one
  part or to the shared final check.
- **AC-29** (REQ-49) — Given a fixture skill directory `orchestrail-pipeline` and a workflow
  referencing `/pipeline` while the map says `orchestrail-pipeline`, then the checker reports
  `reference-missing`; documentation, checks and deployment use the map name.
- **AC-30** (REQ-50) — Given the delivered tree, then the three Python programs exist, neither
  `scripts/validate-contracts.sh` nor `scripts/sync.sh` names them, both suites exit 0, and
  `python3 -I scripts/lint-instructions.py` exits 0.
- **AC-31** (REQ-51) — Given the oracle suite, then entries changing `/phase-discovery` to
  `/discovery`, `rule-phase-discovery` to `rule-bootstrap-discovery`,
  `rules/tdd.md` to `rules/contract-tdd.md` and `workflows/PIPELINE.md` to `docs/PIPELINE.md`
  are accepted; entries that change a non-name
  token, move `pae-tests` to `atomic-validation-check`, move `rules/tdd.md` to
  `rules/contract-language.md`, have an `after` text occurring twice, or carry a wrong
  `name_map_sha256` are each rejected with `ValueError`.
- **AC-32** (REQ-52) — Given the oracle suite, then a `contract_changes` entry with
  `requirement` `REQ-12` and a well-formed `after` is accepted, and entries without
  `requirement`, with `REQ-99`, with `after` equal to `"pass"`, with an unknown `target`, or
  repeating a `(target, key)` already in `path_changes` are rejected; no frozen check
  description is missing from the reconstructed inventory; and every delivered entry has a
  `pass` row in DM-20 → Superseded checks.
- **AC-33** (REQ-53) — Given the delivered tree, then `scripts/validate-contracts.sh` reports 0
  failed, and every glob or path in `tests/workflow-instructions.py`, `tests/hook-install.sh`
  and `tests/git-rails.sh` that names a rule or workflow matches at least one existing file.
- **AC-34** (REQ-54) — Given fixtures whose `always-on.md` has 1,200 and 1,201 words, with a
  1,607-word `capabilities.md` in the same harness, then only the 1,201-word fixture yields
  `always-on-size`; and a fixture `always-on.md` of 1,000 own words followed by `\n\n` and the
  `capabilities.md` text with trailing `\n` removed yields no finding.
- **AC-35** (REQ-55) — Given the delivery commit, then `git log --follow` shows both always-on
  files moved, and the diff of each against its source changes only lines holding a stale name,
  a legacy mention or its own path.
- **AC-36** (REQ-56) — Given a `PATH` whose `python3` reports 3.10, when sync runs, then it exits
  1 with the REQ-56 message and the fixture home is unchanged.
- **AC-37** (REQ-57) — Given leftover directories `pae-tests` and `rule-tdd` in a fixture
  `skills_dir` without manifest entries, when `deploy` runs twice, then both runs print one
  `leftover` line per directory and the directories are unchanged.
- **AC-38** (REQ-58, REQ-59) — Given a fixture source that is a git work tree, then the manifest
  `source_revision` equals `git rev-parse --verify HEAD`, and `null` for a plain copy; and
  given task states with `- execution: in-progress`, only `complete` values, `in-progress`
  outside `## Phases`, and an unreadable file, the roots are classified active, inactive,
  inactive, active.
- **AC-39** (REQ-61) — Given the delivery, then the DM-20 record exists under `docs/audits/` and
  `docs/README.md` links it.
- **AC-40** (REQ-62) — Given the delivered capability files, then each has `## Capability
  records` with the six canonical records in order, an `always-on-path:` line equal to
  `deploy.env`, and a `hooks` record equal to its `hooks:` line; fixtures breaking each of the
  three yield `capability-key-missing`, `always-on-path-mismatch`, `hooks-state-mismatch`.
- **AC-41** (REQ-63) — Given a fixture where the second harness's `deploy.env` is invalid, when
  `deploy` runs, then it exits 1 and the first harness's targets are also unchanged.
- **AC-42** (REQ-64) — Given the parent and delivered trees, after DM-1 substitutions on the
  parent text, then the multiset of lines across the parent's `rules/*.md`, `workflows/*.md`
  and `templates/codex-global-AGENTS.md` (compared with the delivered `rules/*.md`,
  `workflows/*.md`, `docs/PIPELINE.md` and `harness/*/always-on.md`) that start
  `Status values for`, contain `**stop**`, contain `atomic-tests`, or contain
  `pre-TDD task, TDD step skipped` in the parent is contained in the delivered multiset, the
  only added such line is the REQ-37 preflight stop, and the body of the section
  `## Protected Sections Contract` is byte-identical to the substituted parent body.
- **AC-43** (REQ-65) — Given a fixture deployment, then the Claude always-on file carries the
  installer's JSON and the Codex file carries
  `{"reason":"no-native-adapter","status":"unavailable"}`.
- **AC-44** (REQ-28, REQ-30, REQ-40, REQ-44, REQ-24) — Given one fixture per row, when the
  checker runs, then it prints the listed code:

  | Fixture | Code |
  |---|---|
  | `docs/name-map.json` with a repeated `(kind, old)` | `name-map-invalid` |
  | `docs/USAGE.md` table missing one map row | `usage-map-mismatch` |
  | `rules/rules-tdd.md` (prefix not a kind) | `kind-prefix-invalid` |
  | A rule containing byte `0xff`, or U+001F | `input-encoding` |
  | `deploy.env` with `skills_dir="$HOME/x"` | `deploy-env-invalid` |
  | Harness directory without `always-on.md` | `adapter-incomplete` |
  | Front matter line `description = x` | `metadata-syntax` |

- **AC-45** (REQ-42, REQ-44, REQ-45, REQ-63) — Given one fixture per row, when `deploy` runs,
  then it exits 1 with the listed code and writes nothing:

  | Fixture | Code |
  |---|---|
  | `HOME` set to `relative/home` | `home-invalid` |
  | Harness `demo` with `skills_dir=$HOME/.claude/skills/demo` | `adapter-conflict` |
  | Manifest `skills_dir_resolved` differs from the current resolution | `target-moved` |
  | Registry line `relative/path` | `registry-invalid` |
  | `skills_dir` path occupied by a regular file | `unsafe-target` |
  | Journal that is not JSON | `journal-invalid` |

- **AC-46** (REQ-66) — Given the delivered tree, then neither `rules/contract-language.md` nor
  `docs/USAGE.md` advises editing `~/.claude/CLAUDE.md` or `~/.codex/AGENTS.md`, and both state
  that sync manages the file and stops with `ownership-conflict` after an edit.
- **AC-47** (REQ-67) — Given a fixture behaviour-table row whose `Requires` cell is
  `sub-agent-effort`, when every harness's `capabilities.md` has a record `name:
  sub-agent-effort`, then the checker reports nothing for that row; when one harness lacks the
  record, or the cell is `subagent-effort`, it reports `capability-behaviour-table-invalid`.
- **AC-48** (REQ-68) — Given the oracle suite and a fixture name map whose `rule` row for
  `tdd` lists `contract-tdd` and a split target `contract-tdd-<name>` in `new`, then a
  `path_changes` entry moving `rules/contract-tdd.md` to `rules/contract-tdd-<name>.md` in a
  frozen expression is accepted; with the target absent from the row, or with an entry that
  moves the path to a path of another row's class, it is rejected with `ValueError`; and the delivered
  `docs/USAGE.md` table equals the extended map (`usage-map-mismatch` otherwise).
- **AC-49** (REQ-69) — Given the oracle suite, then a `contract_changes` entry whose
  `requirement` is outside the hard-coded set is rejected with `ValueError`, and given a
  delivery whose amendment contains an entry with a value added to the set, then the oracle
  test names that value in its set and DM-20 → Superseded checks has a `pass` row for that
  entry.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01–REQ-04 (withdrawn) | AC-01 (moved) |
| REQ-05 | AC-02 |
| REQ-06, REQ-07 | AC-03 |
| REQ-08, REQ-09 | AC-04 |
| REQ-10 | AC-05 |
| REQ-11 | AC-06 |
| REQ-12, REQ-13 | AC-07 |
| REQ-14, REQ-15 | AC-08 |
| REQ-16 | AC-09 |
| REQ-17, REQ-18 | AC-10 |
| REQ-19 | AC-11 |
| REQ-20 | AC-12 |
| REQ-21 | AC-13 |
| REQ-22 | AC-14 |
| REQ-23 | AC-15 |
| REQ-24 | AC-16, AC-17, AC-44 |
| REQ-25, REQ-26 | AC-16 |
| REQ-27 (withdrawn) | AC-18 (withdrawn) |
| REQ-28 | AC-10, AC-44 |
| REQ-29 | AC-06 |
| REQ-30 | AC-07, AC-44 |
| REQ-31 | AC-14 |
| REQ-32 | AC-11 |
| REQ-33 | AC-19 |
| REQ-34 | AC-20 |
| REQ-35, REQ-36 | AC-22 |
| REQ-37, REQ-38 | AC-23 |
| REQ-39, REQ-41 | AC-21 |
| REQ-40 | AC-21, AC-44 |
| REQ-42 | AC-24, AC-45 |
| REQ-43 | AC-04, AC-25 |
| REQ-44 | AC-24, AC-44, AC-45 |
| REQ-45 | AC-26, AC-45 |
| REQ-46 | AC-17, AC-27 |
| REQ-47 | AC-27 |
| REQ-48 | AC-28 |
| REQ-49 | AC-29 |
| REQ-50 | AC-30 |
| REQ-51 | AC-31 |
| REQ-52 | AC-32 |
| REQ-53 | AC-33 |
| REQ-54 | AC-34 |
| REQ-55 | AC-35 |
| REQ-56 | AC-36 |
| REQ-57 | AC-37 |
| REQ-58, REQ-59 | AC-38 |
| REQ-61 | AC-39 |
| REQ-62 | AC-40 |
| REQ-63 | AC-41, AC-45 |
| REQ-64 | AC-42 |
| REQ-65 | AC-43 |
| REQ-66 | AC-46 |
| REQ-67 | AC-47 |
| REQ-68 | AC-48 |
| REQ-69 | AC-49 |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Changing many frozen expressions breaks the oracle and source guard (at least 225 of the 465 column-0 check expressions name a migrated path, name, trigger or legacy token at the parent snapshot, plus helper bodies and non-standard lines) | Validator red until re-amended; the amendment is a large share of the work | High | DM-9 entries written with each rename; guard refresh procedure; AC-31–AC-33 |
| A name-only mask hides a semantic edit (a renamed token swapped back) | Weakened check passes | Low | Class-indexed mask rejects cross-class swaps and rule/workflow path swaps; every entry reviewed by the independent validator |
| The first deployment adopts a path the user had edited | User text overwritten once, as sync does today | Medium | Documented in the runbook; the leftover and adopt lines name every path; spec 11a adds backups |
| A task starts during deployment | Instructions change under a running task | Low | Freeze evaluated under the lock; residual note printed; owner runs sync between runs |
| Bootstrap rules exceed 300 words after the move (certain for atomic execution and atomic validation, DM-10) | Obligations could be dropped to fit | High | Named overflow rules (DM-10), recorded in DM-20; nothing deleted |
| Capability evidence for Codex unavailable | Codex records `unknown`; `/spec-run` refuses there | High | Intended conservative path (G4); records updated when evidence exists |
| Specs 08, 10, 11 overlap the deployment and metadata contracts | Divergent formats | Medium | Notes → Peer requests and Follow-ups name the alignment each needs |
| Scope exceeds eight subtasks | Large task | Medium | REQ-48 split boundary |
| The deployed always-on file stays larger than 1,200 words because the embedded declaration is not counted (D-01) | Session context carries the declaration in full | Certain | Intended: the declaration is bounded by spec 08's always-on-set budget; the git-rails residual risks stay in it (ADR-0017); restoring the strict reading is a separate decision |

## Assumptions

- A-01 | Where new checks run | Resolved: standalone checker and suites, not in the validator or sync | Source: ADR-0019 Decision 3; `tests/validator-runtime-oracle.py:46-100`; `tests/fixtures/validator-runtime/oracle.py:244-251` (additive suffix hard-coded) | Reversible: yes
- A-02 | How renamed or superseded frozen checks are accepted | Resolved: schema-2 amendment with `path_changes` (spec 08's record, class-indexed mask) and `contract_changes`, owned here because 13 renames first | Source: ADR-0018 status Provisional (`.ai/adr/index.md:30`); spec 08 A-37; `.ai/specs/README.md` → "Dependency order" | Reversible: yes
- A-03 | 1,200-word limit scope (old §9 said "including the capability table") | Resolved: the limit applies to the always-on body; the declaration's size is governed by spec 08's always-on-set budget | Source: ADR-0009 D2 (declaration embedded) and D6 (6,000-word set budget); ADR-0017 implications (`.ai/adr/0017-task-06-enforced-git-rails-hook.md:202`, residual risks stay in `capabilities.md`); fact: the declaration alone has 1,607 words | Reversible: yes (D-01; Q-01 resolved)
- A-04 | Capability syntax | Resolved: spec 10's record form for every canonical key, in a new trailing section | Source: `harness/claude/capabilities.md:31-37`; spec 10 A-32 | Reversible: yes
- A-05 | `step` values 2.5, 4a, 4b | Resolved: grammar of DM-3 keeps them | Source: current descriptions (Context fact 7); best practice (no renumbering churn) | Reversible: yes
- A-06 | `loads` on rules | Resolved: reserved extension key on rules and workflows, registered by spec 08 | Source: spec 08 REQ-22; ADR-0009 D2 (workflow `loads`) | Reversible: yes
- A-07 | Manifest revision field name | Resolved: `source_revision`, same derivation as spec 08 | Source: spec 08 DM-4 | Reversible: yes
- A-08 | Implementation language of the engine | Resolved: standard-library Python 3.11+ called from bash `sync.sh` | Source: ADR-0009 D6 (bash for sync, Python for tools); precedent `scripts/install-hooks.sh`/`.py`; the validator that sync already runs needs Python (`scripts/validate-contracts.sh:5846`) | Reversible: yes
- A-09 | Location of manifests, journal, lock | Resolved: under `<config>/orchestrail/` beside the registry and hook receipt | Source: `scripts/install-hooks.py:658-659`; Context fact 4 | Reversible: yes
- A-10 | First run without manifest | Resolved for this engine, which is the interim state until spec 11a takes over the write path (A-31): adopt planned managed paths (today's overwrite), remove nothing, report leftovers | Source: REQ-10; P1 (`.ai/principles/architecture.md:11-16`); ADR-0009 D2 (old directories never deleted by scripts) | Reversible: yes
- A-11 | Old-name skills left installed vs "no hidden aliases" | Resolved: never created or kept by the engine; existing ones reported every run for manual removal | Source: REQ-10, REQ-40; ADR-0009 D2 | Reversible: yes
- A-12 | "Maintenance mode" of old REQ-43 | Resolved: an owner-invoked sync is the maintenance action; no unattended global replacement exists; the residual race is printed | Source: previous REQ-43 text; no workflow takes a lock shared with deployment (no `deploy.lock` or registry lock appears in `workflows/`) | Reversible: yes
- A-13 | Deferral exit status | Resolved: 3, distinct from errors | Source: best practice; old §7.4 (non-zero for a deferred mandatory scope) | Reversible: yes
- A-14 | Collision prefix per harness or for all | Resolved: one map name for all harnesses, so instruction text stays single-source | Source: ADR-0009 D1 (prefix only on real collision); D2 (no per-skill templating) | Reversible: yes
- A-15 | Machine-readable rename map | Resolved: `docs/name-map.json`, rendered as a table in `docs/USAGE.md` | Source: REQ-40; P6 (one definition); `.ai/principles/coding.md:71-92` (documents about the project under `docs/`) | Reversible: yes
- A-16 | `deploy.env` prefixes | Resolved: only `$HOME/` | Source: `.ai/principles/coding.md:66-67` (no hard-coded home paths); both harnesses live under `$HOME` | Reversible: yes
- A-17 | Project link directory as data | Resolved: optional `project_skills_link_dir` key | Source: REQ-05 (no provider branch); `scripts/sync.sh:226-239` | Reversible: yes
- A-18 | Phases of utilities and composite validation | Resolved: DM-11 table | Source: `.ai/principles/coding.md:19-21` description prefixes; `scripts/validate-contracts.sh:1451-1455` (composite trigger owned by `pav-close`) | Reversible: yes
- A-19 | Section assignment of the `workflow-reference` split | Resolved: DM-12 defaults, amendable from 13a | Source: ADR-0009 D3 (three targets, frozen headings); heading positions (Context fact 9) | Reversible: yes
- A-20 | Rule load modes | Resolved: from the current trigger | Source: Context fact 7; ADR-0009 D2 | Reversible: yes
- A-21 | Validator check descriptions with old names | Resolved: unchanged frozen labels | Source: oracle pins descriptions (Context fact 11); spec 08 "keeps its description" | Reversible: no (changing them needs a new inventory decision)
- A-22 | Word counter | Resolved: DM-19 | Source: spec 08 A-09; spec 10 Terminology | Reversible: yes
- A-23 | `always-on-path` line kept although it repeats `deploy.env` | Resolved: kept, equality enforced by the checker | Source: previous §7.2; spec 10 relies on it as a plain line | Reversible: yes
- A-24 | Symbolic-link policy for `skills_dir` | Resolved: the directory may resolve elsewhere but must stay stable; managed paths inside must not be links | Source: previous §7.3 ("target substitution stops writing"); best practice for dotfile setups | Reversible: yes
- A-25 | Legacy reporting location | Resolved: dedicated reporter, called by sync and setup | Source: REQ-11 (named exception) | Reversible: yes
- A-26 | `tests/golden/cases/*/case.json` | Resolved: in scan set R if present; spec 09 is ordered after 13 (`.ai/specs/README.md` → "Dependency order"), so they will normally be authored with new names | Source: spec 09 request; roadmap order | Reversible: yes
- A-27 | Principle front matter | Resolved: out of scope | Source: REQ-12 covers rules only | Reversible: yes
- A-28 | Installation record for a future harness with `hooks.json` | Resolved: receives the single hook installer result | Source: `scripts/install-hooks.py` is the only hook installer | Reversible: yes
- A-29 | Source checkout as an active consumer | Resolved: counted when registered and active | Source: REQ-43 intent (shared skills change under any running task); this repository runs its own pipeline (`CLAUDE.md:3-5`) | Reversible: yes
- A-30 | Edited global always-on file | Resolved: protected like every owned object; the advice to edit it is removed (REQ-66); placement of personal preferences left open (Q-06) | Source: REQ-42; current advice at `rules/language.md:20-21` would otherwise lose user text on every sync | Reversible: yes
- A-31 | Who owns global writes after spec 11a | Resolved: spec 11a's installer supersedes the `deploy` write path and migrates DM-6 manifests; this spec's engine is the interim state and its preserved contracts are listed in Notes → Relationship to spec 11a | Source: ADR-0009 Decision 1 Consequences and Decision 6 (installer belongs to spec 11a); former Q-05; spec 11a REQ-42, REQ-43, REQ-71 | Reversible: yes
- A-32 | Names and placement of files and sections created by later specs | Resolved: Notes → Files and sections created after this spec | Source: DM-2, DM-11 naming patterns; DM-12 default target; P6 | Reversible: yes
- A-33 | Extension keys in `Requires` cells | Resolved: admitted when every harness declares the record (REQ-67) | Source: spec 18 REQ-24 and its DM-1; DM-4 extension-record convention | Reversible: yes
- A-34 | 13a acceptance line, root `README.md`, kind definitions | Resolved: Guard checks the `Accepted: owner <date>` line; `README.md` joins scan set R; kinds defined as in spec 13a A-04 | Source: spec 13a DM-8 report layout, A-06 (active class = R plus `README.md`), A-04 | Reversible: yes
- A-35 | Split targets of mapped rules (spec 08 Q-07) | Resolved: option (a) of spec 08's Q-07, as REQ-68: the later spec appends the split target to the `new` list of the existing `rule` row in its own delivery. Grounds: DM-10 (Overflow rules) already adds created split targets to the source row's `new` list, so one mechanism covers both; the DM-9 token classes include every `new` of the row, so the move is path-only and passes the mask unchanged; the row's checks and `name_map_sha256` are the only things that change. Option (b) is rejected: a `contract_changes` entry needs an `after` that is a superseding contract, a split target supersedes none, and extending the closed set by a requirement of this spec would make a name-only move a semantic change reviewed as one (REQ-52). Limit: text asserted by checks of two different rows cannot move into one new file, because a `new` value joins one row only (DM-1); spec 08 stops there, as its own text says | Source: DM-1, DM-9 (token classes, mask), DM-10 (Overflow rules); spec 08 Q-07, A-37, A-39, REQ-22; `tests/validator-runtime-oracle.py:46-100` (current schema-1 oracle, the schema-2 oracle is delivered by this spec); ADR-0018 (inventory frozen, amendments exact) | Reversible: yes
- A-36 | Who may extend the closed `requirement` set | Resolved: only a later spec's own delivery, with the oracle change and a DM-20 row per new entry (REQ-69) | Source: DM-9 (set hard-coded in the oracle test), DM-20 (Superseded checks); spec 11a Part A needs it | Reversible: yes
- A-37 | Stop message for parallel-only capability keys | Resolved: the next step depends on the failing key (REQ-37) | Source: spec 12 REQ-25 (delegates the stop message and its next step to REQ-37); `/pipeline` has no parallel mode | Reversible: yes

## Decisions

- D-01 | The 1,200-word limit counts the always-on body only: the generated always-on file with its provenance line, header and core, without the embedded capability declaration and without the installation record (REQ-54) | Overrides: the original text that counted the capability table in the limit | Rationale: the strict reading is unachievable, because `harness/claude/capabilities.md` alone has about 1,607 words, ADR-0009 requires the declaration to be embedded and ADR-0017 requires the git-rails residual risks to stay in it; the declaration's size is bounded by spec 08's 6,000-word budget, so it cannot grow without limit | Follow-up: none in this spec; restoring the strict reading would require shrinking the declaration under ADR-0017 and is a separate decision

Decisions carried from the previous revision are listed under Notes → Preserved decisions.

## Clarifications

### Session 2026-11-14

No questions were asked (auto mode, owner unavailable by standing instruction). Gaps were
resolved as A-01–A-37; unresolved items are Q-02–Q-04 and Q-06 (Q-05 and Q-01 resolved 2026-11-14).

### Session 2026-11-14 (owner decision)

- Q: How is the 1,200-word limit for the always-on content counted (Q-01)? → A: Keep the
  reading "always-on body only": the generated always-on file with its provenance line,
  header and core, without the embedded capability declaration and without the installation
  record. The strict reading is unachievable (the declaration alone has about 1,607 words;
  ADR-0009 requires it embedded; ADR-0017 keeps the git-rails residual risks in it); the
  declaration is bounded by spec 08's 6,000-word budget. Recorded as D-01; folded into REQ-54,
  the Terminology entry "Always-on body" and A-03.

## Open Questions

- Q-01 | resolved 2026-11-14 | Should the stricter old reading of the 1,200-word limit (whole deployed
  file including the declaration) be restored? It requires moving the git-rails protocol and
  residual-risk text (`harness/claude/capabilities.md:39-90`) out of the deployed
  declaration and re-pointing its validator checks and `tests/git-rails.sh:4456`. Impact: the
  Claude session context stays about 2,600 words until spec 08 or a follow-up acts.
  Resolved 2026-11-14: no; the limit counts the always-on body only, without the embedded
  declaration and the installation record (D-01, REQ-54). Restoring the strict reading would
  be a separate decision under ADR-0017.
- Q-02 | non-blocker | Should `/retro` aggregate historical step names with their new names
  through `docs/name-map.json`? Impact: per-step medians split at the migration date.
- Q-03 | non-blocker | Is an authoritative built-in command listing available for Codex?
  Impact: without it no Codex collision can be established (DM-18).
- Q-04 | non-blocker | When an inventory decision accepts added checks, should the checker run
  inside `scripts/validate-contracts.sh`? Impact: until then it runs only directly.
- Q-05 | resolved 2026-11-14 | Spec 11a owns the installer and migrates the deploy manifests
  of DM-6 (spec 11a REQ-43, REQ-71); see Notes → Relationship to spec 11a and A-31.
- Q-06 | non-blocker | Where should personal, cross-project preferences live once the global
  always-on file is ownership-protected (REQ-66)? Merging user text into that file is out of
  scope for spec 11a too. Impact: until decided, users keep such preferences in project files;
  an edit to the global file stops sync with a resolution message.

## Notes

### Old-to-new section mapping (for citations by specs 08, 09, 10, 11, 12)

| Previous section | Now |
|---|---|
| §1 Purpose and status | Source; Goal |
| §2 Verified initial state | Context & Problem |
| §3 Scope and preserved constraints | Scope; Out of Scope; REQ-64 |
| §4 Terms and owners | Terminology; Actors & Roles |
| §5 Requirements (REQ ids unchanged) | Requirements |
| §6.1 Rule map | Data Model → DM-10 (and DM-12) |
| §6.2 Workflows and commands | Data Model → DM-11 |
| §7.1 Metadata | Data Model → DM-2, DM-3 |
| §7.2 Capability declaration | Data Model → DM-4 |
| §7.3 Placement and ownership | Data Model → DM-5, DM-6, DM-7, DM-8 |
| §7.4 Commands and errors | Contracts & Interfaces; Edge Cases |
| §8 Behaviour preservation | REQ-46, REQ-64; DM-20 |
| §9 Non-functional limits (size table, word counting) | Non-Functional Requirements; DM-19; REQ-54 |
| §10 Acceptance criteria (AC ids unchanged) | Acceptance Criteria |
| §11 Errors, rerun and rollback | Edge Cases; Notes → Rollback |
| §12 Order and split boundary | Notes → Implementation order; Notes → Split boundary |
| §13 Decisions, open questions, readiness | Notes → Preserved decisions; Open Questions; Readiness Checklist |

Content changes peers rely on: REQ-12 now admits registered extension keys (`loads`); REQ-13
admits steps `2.5`, `4a`, `4b`; the 1,200-word limit (old §9) applies to the always-on body;
REQ-30's "future known versions" became the extension-key registry of DM-2/DM-3.

### Ownership between 13 and 13a

13a owns the audit: inventory, link graph, duplicate clusters, mixed-kind detection, word and
byte measurements and its findings, and proposes amendments to this spec. 13 owns every
contract and change listed in Scope, including the final maps DM-10–DM-12, which are binding
defaults; 13a's accepted report may change them only through `/spec-sync` before 13's
Discovery (ADR-0009 D3). 13a should use DM-19 for word counts and DM-2's kinds, and report any
file missing from DM-10/DM-11.

### Prerequisites and Guard for the implementing task

Before any change: spec 01 complete and 13a's report accepted (ADR-0009 D7; roadmap order).
Accepted means: exactly one file matches `docs/audits/*-rules-workflows-audit.md`, and its
`## Acceptance` section holds exactly one line `Accepted: owner <YYYY-MM-DD>` with a valid date
(the line format of spec 13a's report layout, its DM-8); `Accepted: pending`, no match or
several matches stop the task. The report's `## Blockers for spec 13` (13a DM-8) must read
`None.`, or every finding it lists must be cited by an amendment applied to this spec through
`/spec-sync` and recorded in its Change log; otherwise stop. If the report is missing, stop; do
not re-run the audit inside this task. Pin the source
revision, record the active consumers and the installed state of the owner's machine only by
reading.

### Implementation order (hint; Discovery decides the decomposition)

1. RED: the two suites with failing cases for AC-02–AC-07, AC-10, AC-11, AC-14, AC-21–AC-26,
   AC-29–AC-31, AC-34, AC-36–AC-41, AC-43.
2. Checker and name map; metadata on every rule and workflow; PIPELINE move.
3. Adapters: `deploy.env`, always-on moves, capability records; legacy reporter.
4. Engine and the new `sync.sh`/setup; re-point `tests/hook-install.sh`; DM-9 schema 2 in the
   oracle; first amendment entries.
5. Rule renames and splits with DM-20; references, hooks, tests, validator expressions.
6. Command renames (final naming stage) with `docs/USAGE.md` table and collision handling.
7. Full validator, suites, checker, semantics review, knowledge files, ADR.

### Split boundary (REQ-48)

If needed: **13** keeps the retirement of legacy targets, adapters, registry pass, engine,
metadata, capabilities, the checker infrastructure, the `docs/name-map.json` format with its
first rows and the DM-9 machinery (REQ-05–REQ-13, REQ-29–REQ-30, REQ-35, REQ-36, REQ-38,
REQ-42–REQ-45, REQ-50–REQ-52, REQ-54–REQ-59, REQ-62, REQ-63, REQ-65, REQ-66, REQ-68, REQ-69 and
its part of REQ-47); **13b** takes names, content splits, the PIPELINE move, references and final records
(REQ-14–REQ-26, REQ-28, REQ-31–REQ-34, REQ-37, REQ-39–REQ-41, REQ-46, REQ-49, REQ-53, REQ-61,
REQ-64, REQ-67; REQ-14–REQ-16, REQ-37 and REQ-67 name `contract-phases`, `rule-bootstrap-<phase>` skills and
`/pipeline`, which exist only after 13b's renames), adding its rows to the map. REQ-48 and the final REQ-47 check join both. Withdrawn REQ-01–REQ-04 and REQ-27 are
not revived.

### Rollback

Revert the delivery commits with ordinary commits. The reverted tree has the previous
`scripts/sync.sh`, which reads no manifest: it overwrites both always-on files and every skill
it deploys, writes the Windsurf paths again and removes nothing, so new-name skills stay
installed until the owner removes them. After such a rollback the owner deletes
`<config>/orchestrail/deploy/` (manifests and journal); otherwise a later re-delivery finds
digests that no longer match and stops with `ownership-conflict` for every overwritten path.
With the directory deleted, the re-delivered engine runs as a first run (adopt, remove
nothing, report leftovers). The runbook update of REQ-34 carries these two steps. Consumer
task history is not rewritten to restore old names.

### Preserved decisions (from the previous revision)

Two harnesses; capabilities instead of provider names; `rule-`/`principle-` prefixes; four
rule kinds; a separate audit before migration; frozen headings of the split contract; a final
command-rename wave; a registry of physical roots; historical data and old installed
directories preserved. Still rejected: partial support of the retired integration, renaming
only the five colliding rules, moving command renames to spec 11, per-provider workflow logic.

### Rejected alternatives in this revision

- Registering new checks in the validator (blocked by the frozen inventory, A-01).
- Re-freezing the whole inventory after migration (loses the per-check audit trail).
- A regex-only path mask (accepts swaps of different names; replaced by the class-indexed mask).
- Per-harness installed names (forces per-harness instruction text, A-14).
- Deleting leftover old skills on provenance (contradicts REQ-10's first-run rule, A-11).
- Moving the git-rails text out of the declaration now (touches ADR-0017's verified area; D-01 keeps the declaration uncounted).

### Peer requests

- Spec 10 — record form for every canonical key: **adopted** (DM-4, A-04). `step` type:
  **adopted** (DM-3, A-05). `always-on.md` becomes generated after 10: **adopted** (REQ-36;
  REQ-54 counts the body without an embedded declaration). Size 985 + 1,607 + 11 words:
  **adapted** — the limit applies to the body (A-03, D-01); spec 10's REQ-17 should apply its
  1,200 words to provenance line + header + core, not the declaration.
- Spec 08 — optional `loads` on rules: **adopted** as a registered extension key (A-06).
  `source_revision`: **adopted** (A-07, REQ-58). `always-on.md` may name `load: always` rules:
  **confirmed**; the lines count toward the 1,200-word body. Re-pointing frozen checks:
  **13 owns it** (DM-9), with 08's record shape; the mask is widened to `templates/`, `docs/`
  and class-indexed names, which every 08 path-only change between unmapped paths still satisfies.
- Spec 09 — prompts in `tests/golden/cases/*/case.json`: **adopted** in scan set R (A-26).
- Shared finding that the inventory is frozen: **verified** (Context fact 11); new checks are
  standalone (REQ-50).

### Follow-ups for other specs and shared files (not edited here)

- 10: see Notes → Spec 10 alignment.
- 08: reuse DM-9 instead of defining schema 2; register `loads` in the checker (DM-2/DM-3).
  Its Q-07 is settled (A-35): a split target that receives frozen-checked text from a mapped
  rule is appended to that rule's `new` list in 08's own delivery (REQ-68), with the
  `docs/USAGE.md` row, the `path_changes` entries and the refreshed `name_map_sha256`.
- 11a: preserve the contracts listed in Notes → Relationship to spec 11a, including leftover
  reporting (REQ-57) in a command that remains after `deploy` is removed, and refresh its
  quotation of the former Q-05.
- 12: wire `--parallel` into the "Parallel children" row of DM-4 (key names agree, Notes →
  Capability key names). Its REQ-25 delegates the stop and the next step it names to REQ-37, which
  defines them per failing key (Contracts → `/spec-run` preflight): a stop caused by
  `worktrees` or `concurrent-sub-agents` advises re-running without `--parallel`; spec 12
  needs no change.
- 13a: report in DM-19 counts and DM-2 kinds; propose map amendments through `/spec-sync`.

### Relationship to spec 11a (installer)

Ruling of 2026-11-14 (A-31): spec 11a owns the public installer and becomes the only writer of
global files. This spec is delivered first, so its engine, deploy manifests (DM-6), journal and
lock (DM-7), `--force` and `sync.sh` exit code 3 are correct and complete as the state between
the two deliveries. Spec 11a then removes the `deploy` command (its REQ-71), adds
`deployment-set` and `project-pass` on this engine, keeps `list-projects` and `link-project`,
migrates every DM-6 manifest into its own manifest and deletes them (its REQ-43). From that
point REQ-10, REQ-42 and REQ-45 for global targets are met by spec 11a's engine, and the
`deploy` cases of `scripts/check-deploy-skills.py` move as spec 11a states.

Contracts of this spec that spec 11a must preserve: an owned file the user changed is never
overwritten or removed and a conflict writes nothing (REQ-42, REQ-63), except under spec 11a's
explicit `--adopt`, which stores a verified backup before replacing a target (spec 11a REQ-03,
REQ-06) — spec 11a replaces this spec's implicit first-run adoption with that explicit option;
deferral
that writes nothing while an active consumer exists, the source checkout included (REQ-43,
DM-8), with `--force` overriding only that freeze; leftover skills reported, never removed
(REQ-57); the registry read-only (REQ-08); the lock never taken over (DM-7); the project pass
as defined here. The exit code and wording of a deferral become spec 11a's (its REQ-42 uses
exit 1 `active-task`); the deferral itself does not change.

Properties of this engine that exist only until spec 11a takes over the write path, and are
not permanent claims of this spec: the implicit first-run adoption (A-10, the `adopt`
action of Contracts → `scripts/deploy-skills.py`), the `forced <root>` output lines under
`--force`, and the other behaviours that spec 11a changes on purpose. Spec 11a's
`deployment-set` reads the same engine without writing: its per-harness
`leftover_candidates` is carried by the same name-map logic as the REQ-57 leftover
definition (Terminology → Leftover skill), listing existing `<skills_dir>/<name>` directories
for `<old>` of a workflow row, `rule-<old>` of a rule row, `PIPELINE` and `rule-global-claude`
of the file rows, none of them a current installed name (DM-1); the ownership filter is the
consumer's. Only `old` names enter that list, so appending split targets to a `new` list
(REQ-68) never creates a leftover. Spec 11a extends the closed `requirement` set of
`contract_changes` as REQ-69 states, with a DM-20 row per new entry.

### Files and sections created after this spec

DM-10–DM-12 bind only files and sections that exist at this revision. A spec delivered after
13 (08, 14–20) that creates content follows these rules, and its implementer translates the
old names its text uses through `docs/name-map.json`:

- A new top-level rule is `rules/<kind>-<subject>.md` with a DM-2 kind and DM-2 front matter;
  its author chooses `load` (default `on-demand`). Examples already named by their specs:
  `contract-context`, `contract-checkpoints`, `contract-delta-operations`, `contract-output`,
  `contract-verification`, `contract-repair`, `contract-reports`, `contract-loads`. Such files
  get no `docs/name-map.json` row, because they never had an old name; the one exception is a
  split target that receives text moved from a rule that has a `rule` row, whose stem is
  appended to that row's `new` list (REQ-68).
- A new workflow uses the DM-11 pattern directly: a phase child is `<phase>-<step-name>` with
  DM-3 `phase` and `step` (spec 19's `/pae-repair` is created as `atomic-execution-repair`,
  phase `atomic-execution`, step `4`, as its A-01 states); orchestrators, entry points and
  utilities use a name without an old prefix. Old prefixes translate as `pd-` →
  `discovery-`, `pe-` → `execution-`, `pv-` → `validation-`, `pae-` → `atomic-execution-`,
  `pav-` → `atomic-validation-`, `phase-<x>` → `<x>`. No map row is added.
- A section a later spec adds to a file this spec splits or renames lands in that file's
  successor: under an existing parent section, in the target that holds the parent per DM-12
  (spec 20's `### Merge and split` and `### Boundary Alternatives` under
  `## Decomposition Rules` land in `rules/protocol-subtask-classifier.md`); a new `## ` section
  lands in `rules/contract-state-files.md`, the default target of DM-12 (spec 20's
  `## Coverage and Interfaces`, which defines plan sections and their Protected Sections
  entries), unless the authoring spec names another DM-12 target. Citations become
  `<target> → ## <heading>`.
- Every such file and section is subject to the checker (kinds, collisions, references).

### Capability key names (spec 12)

The canonical keys of DM-4 are the only canonical names (extension record names stay
possible under REQ-67): `sub-agents`, `concurrent-sub-agents`, `agent-messaging`,
`worktrees`, `hooks`, `git`. Spec 12's REQ-25 uses the same names in the record form
(`state: yes`); the `worktrees: yes` shorthand in spec 12's source text means the same. This spec asserts no value for any
record; until the Claude records carry evidence and `state: yes`, spec 12 refuses
`--parallel N` with N > 1, which is the intended conservative path (REQ-38). Spec 12 wires the
flag into the "Parallel children" row.

### Spec 10 alignment (this spec's side)

All three items are adopted by spec 10:
- Size: spec 10's always-on limit counts exactly REQ-54's body — the generated file including
  its provenance line, header and core, without the embedded capability declaration and without
  the installation record (10 REQ-17, A-42).
- Steps: spec 10 uses the DM-3 `step` grammar and its sort order (`"-"` first, then integer,
  decimal part, letter) (10 A-44).
- Harness: a non-hidden directory with `deploy.env` (DM-5), which on a valid tree is the same
  set as directories with `capabilities.md`; retiring a harness also deletes its `deploy.env`
  (10 A-43).
- After spec 10, `harness/<name>/always-on.md` is a generated output at the same path; this
  spec's checks keep applying to it (REQ-36, REQ-54).

### Change log

- 2026-11-06 — implementation/state reconciliation: owner-authorized source review at
  `23bded3d96d9c562d16eb7e90285414f4412ac79` (Implementation review above). Requirement and
  acceptance identifiers and historical decisions preserved.
- 2026-11-14 — English refinement: REQ-05–REQ-49 and AC-02–AC-29 restated and made precise;
  REQ-50–REQ-65 (REQ-60 unused) and AC-30–AC-43 added; data model DM-1–DM-20, engine,
  reporter, checker and suites contracts, schema-2 inventory amendment and peer dispositions.
- 2026-11-14 — reconciliation with specs 10–20: installer ownership ruling (Notes →
  Relationship to spec 11, A-31, Q-05 resolved); 13a acceptance line in the Guard, root
  `README.md` in scan set R, kind definitions (A-34); REQ-67 and AC-47 for extension keys in
  `Requires` cells (spec 18); rules for files and sections created by later specs (A-32);
  capability key names (spec 12); spec 10 alignment; DM-5 harness definition and DM-3 sort
  order made binding; project pass writes no profile files.
- 2026-11-14 — second reconciliation pass with specs 08, 11, 12, 14–17, 19, 20: split targets
  of mapped rules append to the row's `new` list (REQ-68, AC-48, A-35; settles spec 08 Q-07);
  the `/spec-run` stop message names the next step by failing key (REQ-37, AC-23, A-37; spec
  12 delegates the wording to REQ-37); the closed `requirement` set is extended only by a later spec's own delivery (REQ-69,
  AC-49, A-36; spec 11); interim properties of the engine marked and the `deployment-set`
  leftover list confirmed (Notes → Relationship to spec 11); the rule names in Notes → Files and
  sections created after this spec checked against the owning specs (14–17, 19) and unchanged.
- 2026-11-14 — independent final review: REQ-69 fixes the prefix form of added values; DM-2 defines extension-key blocks; REQ-30 names `metadata-invalid-value`; split boundary moves REQ-14–REQ-16 and REQ-37 to 13b; REQ-11 and Scope item 1 include `docs/USAGE.md → ## Removed integrations`; DM-12 assigns the preamble; DM-16 form 1 excludes ` → ` spans; Guard requires 13a's blockers list to be cleared; spec 10 alignment marked adopted; line 23 untouched.
- 2026-11-14 — owner decision recorded: D-01 keeps the 1,200-word limit on the always-on body only (without the embedded declaration and the installation record); Q-01 resolved; REQ-54, Terminology, A-03, Risks, Rejected alternatives, Peer requests and the Readiness Checklist aligned.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph describing the outcome | PASS — single Goal paragraph |
| 2 | Out of Scope names concrete exclusions | PASS — owners named per exclusion (13a, 08, 09, 10, 11, 12) |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-05–REQ-69 (REQ-01–04, REQ-27 withdrawn; REQ-60 unused); bundled clauses each have a named AC case |
| 4 | Every REQ maps to ≥1 AC; every AC names ≥1 REQ | PASS — Traceability table |
| 5 | Every AC is binary, observable and can guide a test before implementation | PASS — fixtures and expected codes named |
| 6 | Non-functional targets measurable, standard-referenced or N/A | PASS — NFR table with verification |
| 7 | Data model and contracts specified | PASS — DM-1–DM-20; sync, engine, reporter, setup, preflight, checker, suites |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — Edge Cases table (lock, journal, races, links, absent inputs) |
| 9 | Every ambiguity recorded as resolved or open | PASS — A-01–A-37, Q-01–Q-06 (Q-01 and Q-05 resolved; D-01) |
| 10 | No blocker question remains | PASS — all open questions non-blocking (open: Q-02–Q-04, Q-06) |
| 11 | Every existing-code claim has a verified path:line citation | PASS — citations re-verified by the reviewer |
| 12 | Terminology matches project domain definitions | PASS — Terminology table; REQ-34 adds terms to `domain.md` |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — seven implementation steps (Notes); REQ-48 split boundary if Discovery finds more |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 99/100, critic: sub-agent, open: F-40 (minor; resolved after the final round) |

Reconciliation pass 2026-11-14: targeted edits (REQ-67, AC-47, A-31–A-34, Q-05 resolved) checked by one independent pass on the changed passages; verdict unchanged.

Second reconciliation pass 2026-11-14: REQ-68, REQ-69, AC-48, AC-49, A-35–A-37 and the REQ-37 message text; no open question added; verdict unchanged.

Owner decision pass 2026-11-14: D-01 recorded (Q-01 resolved); changed passages checked by one independent pass; verdict unchanged.

**Verdict: READY FOR DEVELOPMENT** once its prerequisites hold (spec 01 complete, 13a report
accepted; Notes → Prerequisites). Automated readiness is not sign-off.
