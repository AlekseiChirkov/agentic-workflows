# 11. Public installation, technology-neutral profiles and first stable release readiness

## Source

- **Origin:** owner decisions in ADR-0009 Decision 1 and Decision 6
  (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:47-75`, `:215-253`): spec 11 keeps
  the installer, profiles, examples and the re-verification of the scrub; "`sync.sh` replaced
  for external users by an installer with `--dry-run`, `CLAUDE.md` backup, and `--uninstall`"
  (`:240-242`); "Technology-neutral core … `setup-new-project.sh --profile <name>` … the
  selection is recorded in `.ai/profile` (name + source version)" (`:223-229`); "Russian
  originals kept with English translations alongside" (`:240-241`).
- **Previous revision:** 2026-10-28, written in Russian, verified against
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461`. The complete Russian text is retrievable with
  `git show 060ce6dbc7116002ac5e6cd47981cfd3c13d60ff:.ai/specs/11-open-source-readiness.md`.
  Its pinned source links pointed at `scripts/sync.sh`, `scripts/install-hooks.py` and
  `scripts/setup-new-project.sh` at that commit; they are cited below as repository paths.
- **Roadmap position:** `.ai/specs/README.md` → "Dependency order" — order 16, prerequisites 01, 09, 10, 13,
  disposition "Accurate docs; license/release remain explicit owner actions".
- **This revision:** 2026-11-13, refined in place in autonomous specification-authoring mode
  with the owner's authorization to replace the file. No human questions were asked; every
  resolved gap is recorded under Assumptions with its source.

### Translation of the 2026-10-28 request (translated from Russian, spec 11 §1–§3 and §7)

§1 Goal and status: "Revision: 2026-10-28. The goal is to give a new user a reproducible
installation, a technology-neutral core, an explicit choice of profile, safe update and
removal, sufficient examples and a verifiable release procedure. The first-contact target is
15 minutes from a ready environment to a prepared project and a clear next action. Verified
source snapshot: `8c2fa08…`. The repository is already public; minimal materials, the
version, portable roots and the tracked knowledge base exist. `scripts/install-hooks.py`
provides ownership and recovery of individual hook settings but is not a general installer.
`scripts/sync.sh` still copies the global instructions directly. Profiles, the full
installer, generated references and the full release process remain planned. Actual user
installations were not checked. Branch protection state is a mutable service setting and is
re-checked before release. Dependencies: completed 01, then 09, 10 and 13. Basis of the
decisions: ADR-0009, decisions 1 and 6; public-history constraints are refined by ADR-0010.
The completed cleanup and project rename are not repeated."

§2 Scope: "In scope: the common installation mechanism, the external `install.sh`, a
compatible call from `scripts/sync.sh`, profiles, project preparation, examples, a
contribution guide, issue and change templates, a public hygiene check and release
readiness. Existing consumers keep their tasks, local content and their decisions about
which `.ai/` files are tracked. Out of scope: a documentation site, a third runtime
environment, renaming the project again, changing publication history and migrating
commands again. Renaming commands belongs to 13. Preparing a release does not mean
permission to bump the version, create a tag, publish a release or change remote
repository settings."

§3 Requirements (each translated faithfully; restated as EARS below):

- REQ-01 Capability documentation. Describe installed optional tools, ways of working
  without them, actual capability declarations, disabling and resuming. Do not present a
  plan as a delivered function. Examples with model calls are subject to separate
  authorization under 09.
- REQ-02 Economics and privacy of examples. Distinguish subscription payment, the notional
  cost of an equivalent API, unknown counters and measured or hypothetical savings. Publish
  only synthetic anonymized examples; do not carry over real sessions, client context,
  secrets or private check patterns.
- REQ-03 Preservation of user changes. Installation, update and removal preserve files
  changed by the user. A restore conflict is shown explicitly. The preview writes nothing.
  The readiness check does not run paid models and does not publish tags.
- REQ-04 Common installer. `install.sh` serves external users and supports `--dry-run` and
  `--uninstall`. `scripts/sync.sh` remains the maintainer's command and uses the same
  ownership, planning, backup and restore operations, without a separate unsafe
  implementation.
- REQ-05 Complete write plan. Before changes, compute all affected paths: global
  instructions, skill directories, hook settings, manifests, backups and project fragments.
  The plan contains the action, source, previous and new hash, ownership basis and
  conflict. Unknown actions are not performed.
- REQ-06 Ownership and reversibility. Before an authorized replacement of an existing global
  instruction, keep a byte-for-byte backup. Remove only unchanged objects from the own
  manifest. Restoring a backup does not overwrite later content. For directories, every
  element belonging to the installer is checked; a foreign added file prevents removal of
  the directory.
- REQ-07 Neutral core. Technology standards and the stack template move to
  `profiles/python-fastapi/`. The root `principles/` keeps `code-quality.md` and
  `testing-standards.md` as universal standards. Maintenance tools may be written in
  Python; this does not make the language a mandatory stack of a consumer project.
- REQ-08 Explicit profile. `setup-new-project.sh --profile <name>` selects an existing
  profile, transfers its files per the manifest, adds a managed fragment only to project
  instructions and records the name and source version in `.ai/profile`. Without a profile
  the neutral core is used. Profiles are not installed as global skills.
- REQ-09 Profile update. Re-applying the same profile is idempotent. Changing the version
  or the profile compares the original, the previously installed and the current content;
  user changes are preserved. Removing the old profile does not delete files that the new
  profile or the user still use.
- REQ-10 Getting-started documentation. `README.md` does not exceed 120 lines and explains
  purpose, audience, environment preparation, installation, project creation, profile
  choice and starting task discovery. Links lead to `docs/USAGE.md`,
  `docs/SPEC-RUN-QUICKSTART.md`, `docs/reference/` and `.ai/specs/README.md`.
- REQ-11 Example of a completed task. `docs/examples/flat-task/` contains a synthetic
  specification, discovery results, the state after execution, a proposed merge
  description and a log summary from the verified `flat` example of spec 09. Provenance
  and version of the example are mandatory. A manually composed example is not called an
  actual model run.
- REQ-12 Contribution and harness matrix. Create `CONTRIBUTING.md` with the change
  procedure, file shapes, commit rules, offline checks, audit method and deployment
  boundary. The matrix `docs/harness-matrix.md` is generated by 10 from actual
  declarations, distinguishing support, installation and coverage.
- REQ-13 Procedure preview. For task discovery and bug fixing, define `--dry-run`: reading
  inputs and producing a plan without changing the project, state, branches, commits,
  registration and pushes. It runs no tests with unknown side effects and starts no
  additional models. A step that cannot be determined without execution is shown as an
  uncertainty.
- REQ-14 Hygiene re-check. Pass the forbidden-data check from 00 with the local private
  pattern source. Do not copy the patterns into the repository. Distinguish a skipped check
  from a successful result. The check does not authorize rewriting published history.
- REQ-15 Contribution materials and languages. Prepare issue and proposed-change templates
  in `.github/`. For Russian analytical documents under `docs/analysis/`, keep the
  originals and place English translations alongside with an unambiguous version
  correspondence. Translation does not change normative decisions.
- REQ-16 Remote repository readiness. Before release, verify mandatory review of changes,
  the prohibition of direct pushes to the protected branch and the offline checks of 09. If
  a setting cannot be read or changed, it is an incomplete release item, not an assumed
  success. It may be changed only within permission the owner has already given.
- REQ-17 Release. The checklist contains all criteria, the exact source version, the
  license decisions and the deferred Apache-2.0 copyright-holder wording from 01.
  `VERSION = 1.0.0`, the tag and publication happen only after the owner's explicit
  permission for the specific release. Absence of permission does not block preparing a
  fully verifiable candidate.

§7 Acceptance criteria (translated): AC-01 documentation of minimal and full configuration
honestly describes availability and the provenance of economic data; examples are
synthetic (REQ-01, REQ-02). AC-02 later user edits are preserved at removal; the preview
changes no file; the release check calls no model and creates no tag (REQ-03). AC-03 the
external installation and the maintainer command use the same ownership logic; the same
plan gives the same result (REQ-04). AC-04 the plan lists all real writes including
settings and backups; no hidden additional paths (REQ-05). AC-05 temporary scenarios of
clean install, update, removal, conflict, damaged backup and interruption preserve user
bytes and give an exact outcome; the chain "user original → version 1 → version 2 →
removal" returns the original; rollback of a failed update returns version 1 without
replacing the original backup (REQ-06). AC-06 a search for active prescriptions in the
core finds no mandatory application stack; the profile holds all moved technology
standards (REQ-07). AC-07 an explicit profile creates only the intended local files and
the `.ai/profile` record; a run without a profile leaves the neutral core (REQ-08). AC-08
re-application does not duplicate fragments; a version or profile change does not delete
user edits and reveals conflicts (REQ-09). AC-09 `README.md` ≤120 lines, all links
resolve; the getting-started procedure is performed with time and constraints recorded
(REQ-10). AC-10 the example has all five artifact kinds, verifiable provenance and an
authorized source; no real client data (REQ-11). AC-11 `CONTRIBUTING.md` allows
reproducing the offline checks; the harness matrix matches generator 10 and claims no
planned capability (REQ-12). AC-12 the preview of discovery and bug fixing preserves a
snapshot of all mutable areas, starts no side execution and marks uncertainties (REQ-13).
AC-13 the local hygiene check is performed and its source is not published; missing
private configuration yields "not verified", not success (REQ-14). AC-14 templates are
present; each Russian analytical document has a current translation with the same
normative meaning (REQ-15). AC-15 the state of mandatory review, branch protection and
checks is confirmed by available current information or named as an explicit release
blocker (REQ-16). AC-16 a complete release checklist is prepared, the deferred license
decision is resolved, the version bump and publication are separated from verification
and require specific permission (REQ-17).

§4–§6 (installation contract, profiles, documentation and release) and §8–§9 (execution
order, recovery, remaining decisions) are incorporated into Requirements, Data Model,
Contracts and Notes below; nothing in them is dropped without an Assumption.

### Implementation review — 2026-11-06 (preserved)

- **Disposition:** Planned; public-source foundations delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** The public README, version, operating manuals, portable source-root helpers, and hook-specific ownership installer exist.
- **Outstanding scope and limits:** The common install.sh lifecycle, neutral/profile split, profile manifests, generated references, measured onboarding, and complete release gate are not delivered. Hook ownership does not establish ownership for all deployed files; license/tag decisions remain deferred.
- **Sources:** [`README.md`](../../README.md), [`VERSION`](../../VERSION), [`scripts/setup-new-project.sh`](../../scripts/setup-new-project.sh), [`scripts/install-hooks.py`](../../scripts/install-hooks.py), [`principles/python-standards.md`](../../principles/python-standards.md), [`templates/stacks/python-fastapi.md`](../../templates/stacks/python-fastapi.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

**Deployment has no ownership, preview or removal.**
- `scripts/sync.sh` recognizes only `--from` and `--help`; other arguments are collected and
  ignored (`scripts/sync.sh:9-24`). It copies every
  workflow, rule and principle into `~/.claude/skills/` and `~/.codex/skills/` with `cp`
  (`:89-96`, `:104-112`, `:122-130`, `:132-140`, `:142-151`, `:166-174`) and overwrites
  `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` without a backup (`:98-101`, `:155-159`). It
  records nothing about what it wrote, so nothing can be removed or restored safely.
- `README.md:15-16` warns that sync overwrites both global instruction files. There is no
  `install.sh`, no uninstall and no dry run (`scripts/README.md:8-20` lists every shell helper).
- The only ownership-aware writer is the hook installer: `scripts/install-hooks.sh`
  (`install|uninstall`, `:13-17`; dependency and Python 3.11 guards `:35-49`) and its engine
  `scripts/install-hooks.py`, which owns individual entries of `~/.claude/settings.json`
  through a receipt at `$XDG_CONFIG_HOME/orchestrail/hooks-installed.json` (`:656-659`),
  serializes with a non-blocking `flock` and a 5-second deadline (`:528-544`), recovers a
  prepared transaction (`:564-579`, `:626-641`) and prints one JSON result (`:660-671`). Sync
  runs it and embeds its result in the deployed Claude instruction file (`scripts/sync.sh:51-67`).

**The core is not technology-neutral.**
- `principles/` holds `python-standards.md` ("Applies to all Python code", `:6`) and
  `infra-standards.md` (Terraform, CDK, Docker, `:6`) beside the universal files; sync deploys
  all four as global `principle-*` skills (`scripts/sync.sh:104-112`).
- The universal files contain stack-specific prescriptions and examples:
  `principles/code-quality.md:26` (SQLAlchemy), `:45` ("In Python"), `:89` (Pydantic), `python`
  fences at `:101`, `:121`, `:143`, `SQLAlchemyError` at `:111`;
  `principles/testing-standards.md:168`, `:216-220` (pytest, SQLAlchemy, PostgreSQL).
- Project setup asks interactively for a stack overlay (`scripts/setup-new-project.sh:195-230`,
  `read -r stack_choice` at `:201`) and pastes `templates/stacks/python-fastapi.md` into the
  `## Standards` injection block of `AGENTS.md` (`templates/AGENTS.md:78-82`). There is no
  `profiles/` directory and no `.ai/profile` record.

**Public materials are minimal.**
- `README.md` has 26 lines. There is no `LICENSE`, no `CONTRIBUTING.md`, no `.github/`, no
  `docs/examples/`, no optional-feature or release-checklist document, and no git tag
  (`git tag -l` is empty). `VERSION` contains `0.9.0`.
- The Russian analysis records were replaced in place by English translations that keep the
  `.ru.md` names (`docs/README.md:26`, `:28`); the Russian originals exist only in history:
  `docs/analysis/2026-09-16-comparative-analysis.ru.md` as blob
  `a260b0048a2639f0cd2f2e6cbc34953bba1a7742` and
  `docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md` as blob
  `522a8a5c7659ca13a94f529554ba5ab384ebd9b7`, both at commit
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461`. Heading and fence line counts of each translation
  equal those of its original (24/24 and 7/7 headings; 2/2 fences in the full analysis).
- The public-hygiene scanner exists: pattern resolution (`scripts/validate-contracts.sh:350-366`),
  fail-closed tracked-file scan (`:371-426`) and the standalone `--hygiene-only` mode, which
  exits 1 when no pattern file is configured (`:428-455`).

**Constraints the delivery must respect.**
- The validator's check inventory is frozen: names, expressions and order of every
  registered check are pinned, and check-function bodies are pinned only for checks between
  the markers `# ── End public identity smoke checks` and `hygiene_tracked_tree_result() {`
  (`tests/fixtures/validator-runtime/oracle.py:160-252`, markers at `:187-188`; markers at
  `scripts/validate-contracts.sh:4871` and `:5231`). New checks cannot be registered; ADR-0019
  Decision 3 (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`) places
  new contract tests in standalone scripts under `scripts/`.
- The nested source guard fingerprints `scripts/validate-contracts.sh` and every `.sh`/`.py`
  file under `tests/` (`tests/fixtures/validator-runtime/source_guard.py:809-822`) and pins the
  digests of `scripts/sync.sh` and `scripts/setup-new-project.sh`
  (`tests/fixtures/validator-runtime/source_guard_exceptions.json:308`, `:332`, `:358`). Changing
  any of them requires the re-pinning procedure of
  `tests/fixtures/validator-runtime/README.md:9-28` (ADR-0020 Decision 2).
- Existing checks bind the delivery: `README.md` at most 60 lines with fixed statements and
  links, no `LICENSE` file, and the two deferral lines in the task-01 record
  (`scripts/validate-contracts.sh:4615-4633`); `docs/USAGE.md` section 4 keeps the live clone
  URL, the checkout path and `v0.9.0` (`:4649-4660`); `VERSION` is exactly `0.9.0`
  (`:4469-4471`); the `.ru.md` files keep the English redaction legend (`:2222-2226`).
- Frozen checks also pin today's deployment shape: `tdd.md` named in `scripts/sync.sh` and
  `scripts/setup-new-project.sh` (`scripts/validate-contracts.sh:953-957`); `git-flow.md` and
  `orchestration.md` named in both (`:1166-1169`); sync's per-project `# 5.` block extracted
  by `test_sync_preserves_repository_knowledge_policy` (`:1174-1179`); every `rules/*.md`
  name in both scripts (`:1293-1305`); literal `cp "$file" ~/.claude/skills/…` and
  `~/.codex/skills/…` loops in sync's sections 3c and 4d (`:1308-1316`); literal
  `mkdir -p ~/.<root>/skills/$skill_name` (`:1317-1320`). Spec 13 (data-driven sync, no project rule copies)
  and REQ-04/REQ-61 of this spec contradict these expressions, which the current inventory
  cannot amend; spec 13 introduces a schema-2 inventory amendment (its DM-9) for changing
  existing expressions (see Q-06 for what this spec still needs from it).
- Spec 13 (final, not yet delivered) specifies `scripts/deploy-skills.py` as the
  deployment engine behind `sync.sh`, with per-harness deploy manifests
  `C/deploy/<harness>.json` (its DM-6), journal and lock `C/deploy.lock` (its DM-7). Its
  Q-05 is resolved: this spec's installer supersedes the `deploy` write path and migrates
  those manifests (spec 13 A-31 and Notes → Relationship to spec 11); the mapping and the
  preserved contracts are under Contracts → Relationship to spec 13's deployment engine.
- The identity scan compares every occurrence of the former repository name against an
  exact ledger of `(path, line, count)` rows
  (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:184-214`), including
  `docs/USAGE.md:254` (`:204`) and line-pinned rows for both `.ru.md` files (`:200-203`). An
  edit that adds an occurrence or moves a listed line fails the scan until the ledger row is
  updated in the same change.
- `tests/hook-install.sh` feeds `2\n` to the setup prompt (`:129-133`), copies only
  `scripts hooks harness rules workflows principles templates` into its fixture source
  (`:70-73`) and asserts the sync deployment layout byte for byte (`:783-806`); it is an
  approved path of the frozen inventory amendment (`tests/validator-runtime-oracle.py:27-40`).

**Precedent for previews.** `/spec-run --dry-run` reports without project writes, branches,
commits or pull requests, with best-effort telemetry as its only write exception
(`workflows/spec-run.md:10-11`, `:50-51`). `/phase-discovery` and `/bugfix` have no dry run
(`workflows/phase-discovery.md:5`, `workflows/bugfix.md:5`).

**Consequence:** an external user cannot install without losing their own global
instruction file, cannot preview or undo an installation, receives Python/FastAPI/GCP
standards as global rules for every project, and has no contribution guide, worked example
or release procedure; the owner has no verifiable candidate to authorize.

## Goal

An external user can preview, install, upgrade and remove Orchestrail's global files with a
plan that names every write, an ownership record that never deletes or overwrites their own
bytes without a backup, and a maintainer deployment that runs the same engine; projects get
technology standards only through an explicitly selected, upgradable profile on top of a
technology-neutral core; and the repository offers the getting-started, contribution,
example and release materials that let the owner authorize a first stable release from a
fully verified candidate, without this work bumping the version, tagging, publishing or
changing remote settings.

## Scope

The work is split into two feature-sized parts with an explicit boundary (see Notes →
Split boundary). Every requirement is tagged **[A]** or **[B]**.

**Part A — installer and profiles**

1. `scripts/install.sh` (public launcher) and `scripts/install.py` (standard-library Python
   3.11+ engine) with install, `--dry-run`, `--uninstall`, `--adopt`, `--harness`, `--from`
   and `--force` (pass-through to spec 13's active-task rule).
2. The ownership manifest, installer journal, original, previous-state and adopted-edit
   backups, lock, plan, recovery and uninstall behaviour defined under Data Model and
   Contracts, and the retired-target list `scripts/install-retired.json`.
3. A read-only `plan` operation of `scripts/install-hooks.sh`/`scripts/install-hooks.py`; the
   existing `install` and `uninstall` operations are unchanged.
4. `scripts/sync.sh` delegating every global write to `scripts/install.sh`.
5. The neutral core: moving the stack standards and stack template into
   `profiles/python-fastapi/`, rewriting stack-specific examples in the two core principle
   files, removing `templates/stacks/`.
6. Profiles: `profiles/<name>/profile.json`, `setup-new-project.sh --profile <name> [--adopt]`,
   the managed fragment in project `CLAUDE.md` and `AGENTS.md`, `.ai/profile`, three-way
   profile upgrade and switch; removal of the interactive stack prompt.
7. The standalone acceptance suite `scripts/check-install.py`.

**Part B — public materials and release readiness**

8. `README.md` rewrite, `docs/USAGE.md` sections 1, 2, 4, 5, 8 and 9, `docs/OPTIONAL-FEATURES.md`,
   `docs/CONTRIBUTING.md`, `.github/` issue and pull-request templates, translation
   provenance lines in the two `.ru.md` analysis records.
9. `docs/examples/flat-task/` built from spec 09's `flat` reference workspace.
10. The dry-run contract as the new on-demand rule `rules/contract-dry-run.md`, applied by the
    Discovery orchestrator and `/bugfix` and cited by `/spec-run`.
11. `docs/RELEASE-CHECKLIST.md`, `scripts/release-check.sh`, the onboarding measurement record
    and the first release-candidate report.
12. The standalone acceptance suite `scripts/check-public-readiness.py`.
13. The offline CI workflow `.github/workflows/offline-checks.yml` (REQ-81).

**Both parts — delivery records:** the root-listing amendment of
`.ai/principles/coding.md → Document placement` (`:83-85`) adding `profiles/` (Part A) and
`.github/` (Part B), naming its `workflows/` and `ISSUE_TEMPLATE/` subdirectories and the pull-request template, `scripts/README.md` and `docs/README.md` rows,
`.ai/memory/architecture.md`, `.ai/context/environment.md`, `.ai/context/runbook.md`, the
re-pinned source-guard records, the identity-ledger rows of every edited file that holds a
ledger token, and one ADR per part recording the decisions marked "ADR at delivery" under
Assumptions. The Part B ADR also records the departure from the literal wording of ADR-0009
Decision 6 (originals kept only in history at pinned blobs, D-02) and the CI workflow decision
(D-03); if the ADR process prefers a note appended to ADR-0009 instead, the departure is
recorded there and the Part B ADR cites it. The record also states that the optional CI secret and manual dispatch of ADR-0009 Decision 6 are not used by REQ-81.

## Out of Scope

- Creating `LICENSE`, supplying the copyright-holder wording (D-01), setting `VERSION` to `1.0.0`,
  creating any tag, publishing a release, changing remote repository settings or branch
  protection: owner actions (REQ-17, REQ-16). The release checklist records them.
- CI configuration beyond the one offline workflow of REQ-81 (`.github/workflows/`; D-03):
  no further workflow, no job that holds a secret, no manual-dispatch paid run. Enabling the
  workflow's job as a required status check in the remote repository is an owner action
  (RC-13).
- Paid or live model runs of any kind, including spec 09 release golden runs.
- A documentation site, a third harness, renaming the project or commands (spec 13),
  rewriting history (ADR-0010), packaging (pip, Homebrew, npm), a `curl | sh` bootstrap,
  Windows support.
- Deploy paths (`harness/<name>/deploy.env`), the installed-name map, the registry, the
  per-project pass, `list-projects`/`link-project`, legacy reporting and the active-consumer
  rule: owned by spec 13 (`scripts/deploy-skills.py`). This spec consumes them and only
  replaces the global-write part of that engine (Contracts → Relationship to spec 13's
  deployment engine).
- The generator, the always-on composition bytes and `docs/harness-matrix.md`: owned by spec
  10. This spec consumes `--check`, `--profile` and the deployment contract.
- Merging user text into the global instruction files (a managed region inside
  `~/.claude/CLAUDE.md`); removing a profile from a project without selecting another;
  automatic profile upgrades by `sync.sh` or `install.sh`; migrating stack content that the
  old setup already pasted into a project's `AGENTS.md`; `--profile` in
  `scripts/setup-all-repos.sh` and `scripts/setup-umbrella.sh`.
- Registering checks in `scripts/validate-contracts.sh` (frozen inventory).
- Re-creating the Russian originals in the working tree (A-27; owner-confirmed, D-02).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| External user | Runs `scripts/install.sh` (with `--dry-run`, `--adopt`, `--uninstall`, `--harness`), `scripts/setup-new-project.sh [--profile <name>] [--adopt]`; never runs `sync.sh` |
| Maintainer | Runs `scripts/sync.sh [--from <dir>] [--adopt] [--force]`, the acceptance suites and `scripts/release-check.sh`; prepares release-candidate reports |
| Owner | Supplies the copyright-holder wording, authorizes a specific version, tag, publication, golden runs and any remote-setting change |
| Contributor | Follows `docs/CONTRIBUTING.md`; opens issues and pull requests with the `.github/` templates |
| Engine (`scripts/install.py`) | Reads sources and targets; writes only targets in the deployment set, its manifest, journal, lock and backups; delegates hook settings |
| Hook installer (`scripts/install-hooks.sh`) | Sole writer of `~/.claude/settings.json` hook and permission entries and of its receipt |
| Generator (`scripts/gen-docs.py`, spec 10) | Answers `--check` and `--profile <name>`; never invoked with `--write` by this spec's scripts |
| Implementer / reviewer | Builds and validates this spec in disposable homes; never deploys into a real home during tests |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Launcher | `scripts/install.sh`: argument parsing, source-root resolution, runtime guard, then `python3 -I scripts/install.py` | This spec |
| Engine | `scripts/install.py` | This spec |
| Source root | The Orchestrail checkout being installed: `--from`, else `ORCHESTRAIL_HOME` when non-empty, else the parent of the launcher's directory (physical path) | `scripts/sync.sh:4-7`, `.ai/context/environment.md:43` |
| Harness | A directory `harness/<name>/` holding spec 13's `deploy.env`; `skills_dir` and `always_on_path` are its deploy paths | Spec 13 REQ-35 |
| Targeted harness | A harness the engine deploys to in one run (REQ-20) | This spec |
| Deployment set | Every `(harness, target path, type, source)` the engine installs in one run (Data Model → Deployment set) | This spec |
| Target | One path in the deployment set, or one path recorded in the manifest | This spec |
| Retired target | A skill path a released version deployed that is no longer in the deployment set, listed in `scripts/install-retired.json` | REQ-65 |
| Ownership manifest | `$XDG_CONFIG_HOME/orchestrail/install-manifest.json`; records the installed state. Always qualified ("ownership manifest") to avoid spec 10's generator manifest | This spec |
| Installed state | The set of entries the ownership manifest records after the last successful operation, numbered by `revision` | This spec |
| Entry | One record of the ownership manifest for one target | This spec |
| Owned target | A target with an entry whose recorded installed content equals its current content | This spec |
| Modified target | A target with an entry whose current content differs from the recorded installed content | This spec |
| Foreign target | An existing target without an entry | This spec |
| Orphaned entry | An entry whose target is not in the current deployment set | This spec |
| Original backup | A byte-exact copy (or link text) of a foreign target, taken before the engine first replaces it; kept until uninstall restores it | Original §4.2 `original_backup` |
| Previous-state backup | A byte-exact copy of an owned target taken before an operation replaces or removes it; kept only until the operation commits | Original §4.2 `generation_backups` |
| Adopted-edit backup | A byte-exact copy of a user-modified target replaced under `--adopt`; never deleted by the engine | REQ-23 |
| Installer journal | `$XDG_CONFIG_HOME/orchestrail/install-journal.json`; exists only while an operation is incomplete. Always qualified to avoid spec 10's generator journal | This spec |
| Plan | The engine's complete list of intended actions (Data Model → Plan), computed before any write and printed by `--dry-run` | Original REQ-05 |
| Conflict | A plan entry the engine refuses to act on without a decision; codes under Contracts | This spec |
| Adopt | The `--adopt` decision: back up, then replace, a foreign, modified or symbolic-link target | This spec |
| Delegated entry | A plan or manifest record for state another installer owns (hook settings) | Original §4.2 |
| Installation record | The `## Current hook installation` section appended to a deployed always-on file | Spec 10 Terminology |
| Neutral core | The core principle files `principles/code-quality.md` and `principles/testing-standards.md` after this spec | REQ-07 |
| Stack term | One of the words listed under Data Model → Stack terms | This spec |
| Profile | A directory `profiles/<name>/` with `profile.json`, its files and `always-on-fragment.md` | ADR-0009 Decision 6 |
| Profile manifest | `profiles/<name>/profile.json` | Original §5 |
| Profile record | `<project>/.ai/profile` | ADR-0009 Decision 6 |
| Managed fragment | The marker-delimited region a profile owns in a project's `CLAUDE.md` and `AGENTS.md` | Original REQ-08 |
| Profile fragment | `profiles/<name>/always-on-fragment.md`, read through `gen-docs.py --profile` | Spec 10 Terminology |
| Optional feature | A capability that works only with an extra prerequisite or explicit enablement (rows of `docs/OPTIONAL-FEATURES.md`) | Original REQ-01 |
| Delivery state | `delivered`, `partial` or `planned` for an optional feature | This spec |
| Cost basis label | `subscription billing`, `API-equivalent`, `unknown`, `measured`, `hypothetical` | Original REQ-02; `.ai/specs/README.md` → "Shared acceptance gates" (G8) |
| Reference workspace | Spec 09's hand-authored correct result of a golden case and its run-log store, built by `golden-eval.py build-reference` from `reference/<workflow>/overlay/` and `history.json` | Spec 09 DM-1 |
| Dry-run contract | The canonical `## Dry-run contract` section defined by REQ-61 | This spec |
| Release candidate | One source commit proposed for release, with its candidate report | This spec |
| Release item | One row `RC-NN` of `docs/RELEASE-CHECKLIST.md` | This spec |
| Candidate report | `docs/audits/<date>-release-candidate-<version>.md` | This spec |
| Onboarding measurement | `docs/audits/<date>-onboarding-measurement.md` | Original §6 |

Rejected synonyms: "receipt" for the ownership manifest (reserved for the hook installer's
receipt); "generation" for the installed state (spec 10 uses "generation" for a generator
publication); "lock file" for the manifest; "stack overlay" for a profile; "golden test"
for the example (it is a copy of a reference workspace, not a test).

## Requirements

Identifiers REQ-01–REQ-17 keep their 2026-10-28 subjects; behaviours the earlier text bundled
into one item are split into REQ-18 onward, noted in parentheses. "The engine" is
`scripts/install.py` reached through `scripts/install.sh`; "the suite A/B" are
`scripts/check-install.py` and `scripts/check-public-readiness.py`.

### Original requirements, restated

- **REQ-01 [B] Optional-feature documentation.** THE SYSTEM SHALL provide
  `docs/OPTIONAL-FEATURES.md` with one table row per required optional feature (Data Model →
  Optional-feature table) stating its delivery state, prerequisites, how to enable it, how
  work proceeds without it, how to disable and resume it, and evidence paths.
- **REQ-02 [B] Cost labelling.** THE SYSTEM SHALL carry, on every line of `README.md`,
  `docs/*.md` and `docs/examples/**` that contains a money figure (Data Model → Money
  figure), at least one backticked cost basis label.
- **REQ-03 [A] Preservation of user bytes.** THE engine SHALL NOT overwrite, remove or
  rename a modified, foreign or symbolic-link target unless `--adopt` is given, and SHALL
  then store its bytes or link text as a verified backup before the replacement.
- **REQ-04 [A] One engine for both commands.** WHEN `scripts/sync.sh` deploys, THE SYSTEM
  SHALL perform every write under a harness deploy path, the hook settings and the always-on
  files only by running `scripts/install.sh --from <root>` with one `--harness` option per
  harness directory, and SHALL NOT copy, link or remove files under those paths itself.
- **REQ-05 [A] Complete plan before writing.** WHEN an install, uninstall or profile
  operation starts, THE engine SHALL compute the complete plan — every target, delegated
  entry and bookkeeping path (ownership manifest, installer journal, lock, backups, profile
  record) it may write or remove, with action, source, previous and next content identity,
  ownership and conflict — before its first write, and SHALL write no path absent from that
  plan.
- **REQ-06 [A] Original backup.** WHEN the engine replaces a foreign or symbolic-link target
  under `--adopt`, THE engine SHALL first store the target's bytes (or link text) and mode as
  an original backup, verify the stored copy's SHA-256, and record it in the entry's
  `original` field.
- **REQ-07 [A] Neutral core.** THE SYSTEM SHALL keep exactly `code-quality.md` and
  `testing-standards.md` in `principles/`, neither containing any stack term, and SHALL hold
  `python-standards.md`, `infra-standards.md`, the former stack template and the removed
  stack-specific examples under `profiles/python-fastapi/`.
- **REQ-08 [A] Explicit profile.** WHEN `scripts/setup-new-project.sh --profile <name>` runs
  in a project, THE SYSTEM SHALL copy the files listed by `profiles/<name>/profile.json` to
  their targets, write the managed fragment into the project's `CLAUDE.md` and `AGENTS.md`,
  and write `.ai/profile`, and SHALL write no other project file for the profile.
- **REQ-09 [A] Idempotent re-application.** WHEN the same profile at the same source content
  is applied again to a project whose profile files and fragments are unchanged since the
  last application, THE SYSTEM SHALL leave every project file byte-identical, including
  `.ai/profile`, `CLAUDE.md` and `AGENTS.md`.
- **REQ-10 [B] Getting-started README.** THE SYSTEM SHALL provide a `README.md` of at most 60
  lines that passes the existing check `test_public_package_overview_and_release_policy` and
  states purpose, audience, prerequisites, installation, project creation, profile choice and
  the first Discovery command, linking `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`,
  `docs/reference/commands.md`, `.ai/specs/README.md`, `docs/OPTIONAL-FEATURES.md`,
  `docs/CONTRIBUTING.md` and `docs/harness-matrix.md`.
- **REQ-11 [B] Worked example.** THE SYSTEM SHALL provide `docs/examples/flat-task/` with the
  files listed under Data Model → Example layout, built from spec 09's `flat` reference
  workspace for the `spec-run` workflow, whose `README.md` states that the content is a
  hand-authored reference result and not a model run.
- **REQ-12 [B] Contribution guide.** THE SYSTEM SHALL provide `docs/CONTRIBUTING.md` with the
  six sections under Data Model → Contribution guide, in which every repository path
  written in backticks exists.
- **REQ-13 [B] Discovery and bug-fix previews.** WHEN the Discovery orchestrator or `/bugfix`
  is invoked with `--dry-run`, THE SYSTEM SHALL follow the dry-run contract (REQ-61) and
  report the workflow-specific items of REQ-62.
- **REQ-14 [B] Hygiene re-check.** WHEN `scripts/release-check.sh` runs, THE SYSTEM SHALL
  report release item RC-08 as `pass` when the standalone hygiene scan with a resolved local
  pattern file exits 0, `fail` when it exits non-zero, and `not-verified` when no pattern
  file is resolved.
- **REQ-15 [B] Contribution templates.** THE SYSTEM SHALL provide
  `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/change_request.md` and
  `.github/PULL_REQUEST_TEMPLATE.md` with the content under Data Model → Contribution
  templates.
- **REQ-16 [B] Remote-setting items.** THE SYSTEM SHALL list in `docs/RELEASE-CHECKLIST.md`
  release items RC-11 (required review), RC-12 (no direct push to the protected branch) and
  RC-13 (required status checks), each with a read-only verification command and the rule
  that an unreadable setting is `not-verified` and a missing one is `blocked`; spec 09's
  offline checks are verified locally as RC-07 (`python3 -I tests/golden-runs.py`). RC-13 is
  satisfiable by REQ-81: it is `pass` when the default branch requires the status check
  `offline-checks` (the job of the workflow REQ-81 creates), `blocked` while that setting is
  missing or the workflow file is absent, and `not-verified` when the setting cannot be read.
  Local verification of RC-02–RC-07 stays the fallback evidence for the checks themselves and
  does not by itself turn RC-13 into `pass`.
- **REQ-17 [B] Owner-gated release.** THE SYSTEM SHALL list in `docs/RELEASE-CHECKLIST.md`
  release items RC-14 (license and copyright-holder wording), RC-15 (version and tag
  authorization) and RC-16 (publication), each stating that only the owner's explicit
  authorization of the specific version changes it from `owner-decision-pending`.

### Installer — Part A

- **REQ-18 [A] Preview writes nothing (split from REQ-03).** WHEN the engine runs with
  `--dry-run`, THE engine SHALL print the plan and SHALL NOT create, modify, rename or
  delete any file or directory, including the lock, journal, manifest and backup
  directories.
- **REQ-19 [B] Release check is read-only and offline (split from REQ-03).** WHEN
  `scripts/release-check.sh` runs, THE script SHALL NOT itself invoke `gh`, `claude`,
  `codex`, `curl` or `wget`, SHALL NOT create, move or delete any git ref or tag, and SHALL
  leave every tracked file and every untracked file not matched by `.gitignore` unchanged,
  running every sub-suite with `PYTHONDONTWRITEBYTECODE=1`. (Test doubles that a sub-suite
  places on its own `PATH` are part of that suite.)
- **REQ-20 [A] Harness detection.** WHEN an install runs without `--harness`, THE engine
  SHALL target exactly the harnesses whose `always_on_path` parent directory exists.
- **REQ-21 [A] Manifest content.** WHEN an install commits, THE engine SHALL write an
  ownership manifest that conforms to Data Model → Ownership manifest and records every
  target it created, replaced or adopted.
- **REQ-22 [A] Stop on conflict.** IF the plan of an install contains at least one conflict,
  THEN THE engine SHALL print one diagnostic per conflict, write nothing and exit 1.
- **REQ-23 [A] Adopt.** WHERE `--adopt` is given, THE engine SHALL resolve the conflicts
  `foreign-target`, `user-modified` and `symlink-target` by storing a verified backup that it
  never deletes itself (an original backup, or an adopted-edit backup for `user-modified`)
  and then replacing the target, and SHALL leave every other conflict code unresolved.
- **REQ-24 [A] Single writer.** IF the installer lock is held by another process for 5
  seconds, THEN THE engine SHALL exit 3 with `installer-busy` without writing.
- **REQ-25 [A] Journalled atomic writes.** WHEN an install or uninstall applies its plan, THE
  engine SHALL write the installer journal before the first target write, replace each file
  target atomically through a temporary file in the same directory, mark each step applied
  in the journal, write the ownership manifest last, and delete the journal after the
  manifest is written.
- **REQ-26 [A] Recovery first.** WHEN the engine starts an install or uninstall and an
  installer journal exists, THE engine SHALL complete recovery (Contracts → Recovery: an
  install journal is rolled back, an uninstall journal is rolled forward from its own steps)
  before planning the requested operation, and SHALL exit 4 without planning when recovery
  leaves a conflict.
- **REQ-27 [A] Upgrade keeps the original backup (split from REQ-06).** WHEN an install
  replaces an owned target whose entry holds an original backup, THE engine SHALL keep that
  entry's `original` field and backup file unchanged.
- **REQ-28 [A] Owned orphans.** WHEN an install plans an owned orphaned entry of a targeted
  harness, THE engine SHALL remove the target, restoring its original backup if one exists.
  Entries with `installed: {"removed": true}` are never orphans (REQ-65).
- **REQ-29 [A] Uninstall of owned targets (split from REQ-06).** WHEN `--uninstall` runs, THE
  engine SHALL, for each owned target, restore its verified original backup when one exists,
  keep it when its original state is `preexisting-identical`, and remove it otherwise.
- **REQ-30 [A] Uninstall keeps modified targets (split from REQ-03).** IF `--uninstall` finds
  a modified target, THEN THE engine SHALL leave it byte-identical, report `user-modified`
  with the path of its original backup or `none`, and keep its entry in the manifest.
- **REQ-31 [A] Directories with foreign content (split from REQ-06).** WHEN `--uninstall` or
  an orphan removal empties an owned skill file from a directory the engine created, THE
  engine SHALL remove that directory only if it is then empty, and otherwise leave it and
  report `directory-kept`.
- **REQ-32 [A] Changed object type.** IF a target recorded as a file is found as a directory,
  symbolic link or other non-regular object, THEN THE engine SHALL leave it untouched and
  report `type-changed`.
- **REQ-33 [A] Corrupt backup.** IF a backup's content SHA-256 differs from the value recorded
  for it, THEN THE engine SHALL leave the current target untouched, report `backup-corrupt`
  and keep the entry.
- **REQ-34 [A] Missing manifest.** IF `--uninstall` finds no ownership manifest, THEN THE
  engine SHALL remove nothing, report `no-manifest` and exit 0.
- **REQ-35 [A] Uninstall boundary.** WHEN `--uninstall` runs, THE engine SHALL NOT modify any
  consumer project, the project registry, the run-log store, legacy harness directories or
  any path that is neither recorded in the manifest nor a bookkeeping path.
- **REQ-36 [A] Symbolic-link target.** IF a target is a symbolic link, THEN THE engine SHALL
  report `symlink-target` unless `--adopt` applies, and SHALL never write through the link.
- **REQ-37 [A] Foreign owner.** IF an existing target or its parent directory is owned by a
  user ID other than the engine's effective user ID, THEN THE engine SHALL report
  `foreign-owner`.
- **REQ-38 [A] Delegated hook settings.** WHEN a targeted harness directory contains
  `hooks.json`, THE engine SHALL obtain a predicted result from `install-hooks.sh plan`
  while planning and SHALL apply hook settings only by running `install-hooks.sh install`
  (or `uninstall` at uninstall), never by writing `settings.json` or the hook receipt
  itself.
- **REQ-39 [A] Always-on bytes.** THE engine SHALL install, at each targeted harness's
  `always_on_path`, exactly the bytes spec 10's deployment contract defines: the generated
  `harness/<name>/always-on.md` followed by the installation record built from the hook
  installer's result, or `{"reason":"no-native-adapter","status":"unavailable"}` when the
  harness has no `hooks.json`.
- **REQ-40 [A] Generated files must be current.** WHEN an install (dry-run included) starts,
  THE engine SHALL run `python3 -I <root>/scripts/gen-docs.py --check --root <root>` and, if
  it exits non-zero, SHALL exit 3 with `generated-files-stale` before reading any target.
- **REQ-41 [A] Inputs as data.** THE engine SHALL parse `deploy.env`, the ownership manifest,
  the installer journal, profile manifests and profile records only as data (spec 13
  REQ-44 for `deploy.env`; strict JSON for the rest: duplicate keys, `NaN`/`Infinity`,
  unknown keys and unknown `schema_version` rejected) and SHALL NOT migrate an unknown
  version by guessing.
- **REQ-42 [A] Active consumers.** WHEN an install or uninstall plan changes at least one
  target and `deployment-set` reports an active consumer (spec 13 REQ-43) without `--force`,
  THE engine SHALL write nothing and exit 1 with `active-task`; `--force` SHALL carry only
  the meaning spec 13 gives it.
- **REQ-43 [A] Migration of spec 13 deploy manifests.** WHEN an install or uninstall starts
  without an ownership manifest and one or more spec 13 deploy manifests
  (`C/deploy/<harness>.json`, spec 13 DM-6) exist, THE engine SHALL treat each of their
  objects as an entry by the mapping under Contracts → Relationship to spec 13's
  deployment engine, and SHALL delete those deploy manifests when its own manifest commits.
- **REQ-44 [A] Exit codes and diagnostics.** THE launcher and the engine SHALL exit with the
  codes and print diagnostics in the format under Contracts → Exit codes and Diagnostics.
- **REQ-45 [A] Inputs changed during apply.** IF a source file's SHA-256 or a target's
  content identity differs, at the moment of its write, from the value in the plan, THEN THE
  engine SHALL stop before that write, keep the journal and exit 4 with `source-changed` or
  `target-changed`.

### Profiles — Part A

- **REQ-46 [A] Profile manifest validation.** IF `profiles/<name>/profile.json` violates Data
  Model → Profile manifest, THEN THE engine SHALL exit 2 with `profile-invalid` before any
  project write.
- **REQ-47 [A] Managed fragment.** WHEN the engine writes a managed fragment into a project
  instruction file, THE engine SHALL place the profile fragment between the markers under
  Data Model → Managed fragment and SHALL keep every byte outside the begin line, region
  content and end line unchanged.
- **REQ-48 [A] Malformed markers.** IF a project instruction file contains a begin marker
  without exactly one following end marker, more than one begin marker, or an end marker
  before the begin marker, THEN THE engine SHALL report `fragment-markers-invalid` for that
  file and write nothing.
- **REQ-49 [A] Profile file conflicts.** IF a profile target exists without a profile-record
  entry and differs from the new content, or its current content differs from both its
  recorded content and the new content, THEN THE engine SHALL report `foreign-target` or
  `user-modified` and, unless `--adopt` is given, write nothing.
- **REQ-50 [A] Profile switch and upgrade.** WHEN a profile operation runs against a profile
  record of a different profile or version, THE engine SHALL decide every target by the
  three-way table under Contracts → Profile three-way rules, removing a previous-profile-only
  target only when its current content equals its recorded content.
- **REQ-51 [A] No profile.** WHEN `scripts/setup-new-project.sh` runs without `--profile`, THE
  SYSTEM SHALL ask no stack question, write no profile file, fragment or profile record, and
  leave an existing `.ai/profile` and its files unchanged.
- **REQ-52 [A] Unknown profile.** IF `--profile` names a value that does not match
  `^[a-z0-9]+(-[a-z0-9]+)*$` or a profile without `profiles/<name>/profile.json`, THEN
  `scripts/setup-new-project.sh` SHALL exit 2 before writing any file.
- **REQ-53 [A] Profiles are project-only.** THE engine SHALL NOT include any path under
  `profiles/` in the deployment set of an install.

### Public materials and release — Part B

- **REQ-54 [B] Links resolve.** THE SYSTEM SHALL resolve every relative Markdown link target
  in `README.md`, `docs/OPTIONAL-FEATURES.md`, `docs/CONTRIBUTING.md`,
  `docs/RELEASE-CHECKLIST.md`, `.github/**/*.md` and `docs/examples/flat-task/*.md` to an
  existing file or directory of the repository.
- **REQ-55 [B] Example provenance.** THE SYSTEM SHALL record in
  `docs/examples/flat-task/provenance.json` (Data Model → Example provenance) every example
  file, and every copied file's bytes SHALL equal the bytes at its `built_path` in a fresh
  `build-reference` output made with the recorded `date_base` from the current tree. The
  comparison covers workspace files only; spec 09 REQ-49 makes those byte-identical, whereas the
  run-log store of the build is not (Data Model → Example layout).
- **REQ-56 [B] Example privacy.** THE SYSTEM SHALL keep `docs/examples/**` free of the
  patterns under Data Model → Example privacy patterns.
- **REQ-57 [B] Onboarding measurement.** THE SYSTEM SHALL provide one onboarding measurement
  record per release candidate with every field under Data Model → Onboarding measurement.
- **REQ-58 [B] Translation provenance.** THE SYSTEM SHALL end each `docs/analysis/*.ru.md`
  file with one line naming its Russian original's commit and blob (Data Model →
  Translation provenance line).
- **REQ-59 [B] Candidate report.** WHEN a release candidate is prepared, THE SYSTEM SHALL
  provide a candidate report listing every release item RC-01–RC-16 with exactly one status
  from the release status vocabulary and evidence, and SHALL state verdict `ready` only when
  every item RC-01–RC-15 is `pass` (RC-16, publication, follows the verdict).
- **REQ-60 [B] Release check output.** WHEN `scripts/release-check.sh` completes, THE SYSTEM
  SHALL print the table under Contracts → Release check and exit 0 only if RC-01–RC-08 are
  all `pass`.
- **REQ-61 [B] Dry-run contract.** THE SYSTEM SHALL define the dry-run contract once, as the
  section `## Dry-run contract` with the seven numbered clauses under Contracts → Dry-run
  contract, in the new on-demand rule `rules/contract-dry-run.md`, and SHALL cite it from the
  Discovery orchestrator, `/bugfix` and `/spec-run`.
- **REQ-62 [B] Workflow-specific dry-run items.** WHEN the Discovery orchestrator or `/bugfix`
  runs with `--dry-run`, THE workflow SHALL report the items listed for it under Contracts →
  Dry-run contract → Workflow items.
- **REQ-63 [B] Operating manual.** THE SYSTEM SHALL describe in `docs/USAGE.md` section 4 the
  preview, install, adopt and uninstall commands of `scripts/install.sh`, in section 5 the
  `--profile` option, and in section 8 upgrading by re-running the installer; SHALL state in
  sections 1, 2 and 9 (today `docs/USAGE.md:20-21`, `:111-113`, `:759-761`) that the core
  principles are `code-quality.md` and `testing-standards.md` and that Python and
  infrastructure standards come from the `python-fastapi` profile; and SHALL keep the
  statements `test_public_setup_guide_uses_orchestrail_release_instructions` requires.
- **REQ-64 [A] Maintainer gates.** WHEN `scripts/sync.sh` runs, THE SYSTEM SHALL run the
  contract validator and `gen-docs.py --check` before invoking the installer, and SHALL NOT
  invoke the installer or the per-project pass when either fails or when the installer exits
  non-zero. Where spec 08 is delivered, sync also runs its `measure-context.sh check` there
  (spec 08 REQ-08) under the same rule. This spec owns the position of these gates in
  `scripts/sync.sh` after its delivery; spec 10 owns the generator command and its exit
  semantics and spec 08 the meter command (spec 10 REQ-22, A-48).
### Requirements added in the 2026-11-13 and 2026-11-14 reviews (tagged by part; REQ-79 and REQ-80 on 2026-11-14)

- **REQ-65 [A] Retired targets (new 2026-11-13).** WHEN an install targets a harness whose
  skills directory holds a path listed in `scripts/install-retired.json` (Data Model →
  Retired targets) without a manifest entry, THE engine SHALL report info `legacy-target`
  (ownership `legacy`) and leave it unchanged unless `--adopt` is given.
- **REQ-66 [A] Explicit harnesses (split from REQ-20).** WHEN one or more `--harness <name>`
  options are given, THE engine SHALL target exactly those harnesses and create their
  missing deploy directories, each recorded as a `directory` entry with `created: true`.
- **REQ-67 [A] Absent target at uninstall (split from REQ-32).** IF a target is absent at
  uninstall, THEN THE engine SHALL restore its original backup when one exists and
  otherwise drop the entry.
- **REQ-68 [A] Invalid manifest (split from REQ-34).** IF the ownership manifest is
  unreadable, malformed or of an unknown `schema_version`, THEN THE engine SHALL write
  nothing and exit 2 with `manifest-invalid`.
- **REQ-69 [A] Symbolic link in the path (split from REQ-36).** IF any path component
  between a resolved deploy root and a target is a symbolic link, THEN THE engine SHALL
  report `symlink-in-path`.
- **REQ-70 [A] Uninstall continues past entry conflicts.** WHILE `--uninstall` applies its
  plan, WHEN an entry is classified `retain`, THE engine SHALL continue with the remaining
  entries and exit 1 at the end; only an `active-task` deferral or a recovery conflict stops
  an uninstall before its first write.
- **REQ-71 [A] One global writer.** THE SYSTEM SHALL remove the `deploy` subcommand of
  `scripts/deploy-skills.py` and SHALL provide in its place the read-only subcommand
  `deployment-set` and the subcommand `project-pass`, both under Contracts → Relationship
  to spec 13's deployment engine, keeping `list-projects` and `link-project` unchanged.
- **REQ-72 [B] Release sequence.** WHEN the owner authorizes a specific version and supplies
  the copyright-holder line of `LICENSE` (D-01), THE SYSTEM SHALL prepare one release-preparation commit that sets `VERSION`, adds `LICENSE`, updates
  the post-release tag text of `docs/USAGE.md` section 4 and updates, through spec 13's
  schema-2 inventory amendment where an expression changes, the checks that pin the previous
  state (`scripts/validate-contracts.sh:4469-4471` and `:4604-4605` for `VERSION`, `:4615-4633`
  for `LICENSE` and the task-01 deferral lines, `:4649-4667` for the tag text; each
  `contract_changes` entry names the value `spec-11 REQ-72`, which this commit adds under spec 13
  REQ-69 with its DM-20 rows), and SHALL
  treat that commit as a new release candidate verified by a fresh `release-check.sh` and
  candidate report before any tag. The holder is whoever legally owns the code; by default
  the owner personally, under the name in the repository's git authorship. Before supplying
  the line the owner confirms that no employer or other third party holds rights to the code
  (a precondition the owner alone can meet and that cannot be repaired after publication under
  a licence). The implementer SHALL NOT choose or invent a holder and SHALL NOT commit a
  `LICENSE` file, or any file with a placeholder holder line, to a published branch before
  that gate; a draft with a clearly marked placeholder may exist only outside any committed
  tree.
- **REQ-73 [A] Modified orphans (split from REQ-28).** IF an orphaned entry of a targeted
  harness is modified, THEN THE engine SHALL report `user-modified` and, under `--adopt`,
  drop the entry, keep the file and report `released`.
- **REQ-74 [A] Other harnesses (split from REQ-28).** WHEN an install targets a subset of the
  harnesses that have entries, THE engine SHALL carry the entries of the other harnesses into
  the new manifest unchanged and SHALL NOT touch their targets.
- **REQ-75 [A] Retiring under adopt (split from REQ-65).** WHERE `--adopt` is given and a
  retired path's SHA-256 is one of its listed released hashes, THE engine SHALL store an
  original backup, remove the path (and its directory when then empty) and record an entry
  with `installed: {"removed": true}` (ownership `retired` on later runs).
- **REQ-76 [A] Modified retired paths (split from REQ-65).** IF a retired path without an
  entry has a SHA-256 not listed for it, THEN THE engine SHALL report info
  `legacy-target-modified` and leave it unchanged, also under `--adopt`.
- **REQ-77 [A] Retired entries on later installs.** WHEN an install finds an entry with
  `installed: {"removed": true}`, THE engine SHALL leave the entry and the path unchanged
  (action `unchanged` when the path is absent; info `legacy-target` when the user re-created
  it).
- **REQ-78 [A] Hook removal is journalled.** WHEN an uninstall removes hook settings, THE
  engine SHALL record the hook uninstall as the last journal step before running it, and
  recovery SHALL re-run `install-hooks.sh uninstall` when that step is not marked applied.
- **REQ-79 [A] Leftover skills.** WHEN an install (dry-run included) finds a directory named
  in a harness's `leftover_candidates` (`deployment-set`) that is neither an entry's path nor
  inside one, THE engine SHALL list it in the plan's `leftover` field, SHALL print it in a
  non-dry run once per run as `leftover <dir> (not removed; review,
  then remove it manually)`, SHALL NOT remove,
  modify or create any directory under such a name, and SHALL NOT change the exit code
  (spec 13 REQ-57 preserved; Contracts → Relationship to spec 13's deployment engine).
- **REQ-80 [A] Preserved registry, lock and project-pass boundaries.** THE engine and
  `project-pass` SHALL NOT write the project registry, SHALL NOT delete either lock file
  (`C/install.lock`, `C/deploy.lock`) or take one over from a process that holds it, and
  `project-pass` SHALL NOT create, refresh or remove any profile file or record in a project
  (spec 13 REQ-08, DM-7 and Contracts → Project pass preserved).
- **REQ-81 [B] Offline CI workflow (new 2026-11-14, D-03).** THE SYSTEM SHALL provide
  `.github/workflows/offline-checks.yml` with two jobs. The job `offline-checks` is triggered by
  `pull_request` and by `push` to the default branch; the job `full-validator` is triggered only
  by `schedule` (a weekly cron) and runs `bash scripts/validate-contracts.sh` (RC-02) alone, so
  the 34–52 minute full validator never blocks a pull request (D-04). Both jobs run with read-only repository permissions,
  that runs offline and starts no paid model run: no step reads a `secrets.` value or invokes
  `claude` or `codex`, and the workflow neither uses `pull_request_target` nor offers a
  credentialed manual dispatch (`.ai/specs/README.md` → "Shared acceptance gates", G6). The
  job SHALL set up, from what the repository states: a full-history checkout (the
  translation-blob checks of AC-14 and RC-01's `git diff` need history); `bash`, `git`, `jq`
  and `flock` (`.ai/context/runbook.md → Commands`: native hooks keep Bash/jq/flock
  dependencies, timing needs jq); Python 3.12 as `python3`, because the installer and timing
  engines need 3.11 or newer and the runbook names `MISE_PYTHON_VERSION=3.12.16` as the
  explicit version for isolated-PATH fixtures (the job exports that variable so a mise shim,
  if ever present, resolves instead of failing with `No version is set for shim: python3`);
  and `pytest` (spec 09 REQ-35: without it the golden-run suite exits 3). It SHALL then run,
  in this order and failing the job on any non-zero exit, the commands of RC-03–RC-06 (not RC-02,
  which only `full-validator` and the release checklist run) and,
  as the last step, `python3 -I tests/golden-runs.py` (RC-07) only when `tests/golden-runs.py`
  exists: a shell test `[ -f tests/golden-runs.py ]` guards the step, and when the file is
  absent the step prints a notice that the suite is absent and exits 0, so the workflow does
  not fail before spec 09 is delivered; an absent suite is not a pass of RC-07, which stays
  `not-verified`. When the file exists, every non-zero exit, exit 3 included, fails the job.

## Data Model

All JSON files below are UTF-8, written with sorted keys, two-space indentation and a final
`\n`; readers key on field names and reject unknown keys (REQ-41). Hashes are lowercase hex
SHA-256 of exact bytes. Paths in engine records are absolute and normalized (no `.`/`..`,
no trailing slash). All files and directories below are new unless marked existing.

### Locations (new)

| Path | Mode | Purpose |
|---|---|---|
| `C/install-manifest.json` | 0600 | Ownership manifest |
| `C/install-journal.json` | 0600 | Installer journal (only while incomplete) |
| `C/install.lock` | 0600 | `flock` target |
| `S/install-backups/<installation_id>/original/<sha256>` | 0600 | Original backups, content-addressed |
| `S/install-backups/<installation_id>/previous/<sha256>` | 0600 | Previous-state backups |
| `S/adopted-backups/<sha256>` | 0600 | Adopted-edit backups: bytes of a `user-modified` target replaced under `--adopt`; never deleted by the engine |
| `S/profile-backups/<sha256>` | 0600 | Profile `--adopt` backups; never deleted by the engine |

`C` is `Path(XDG_CONFIG_HOME or HOME/.config).absolute() / 'orchestrail'` and `S` is
`Path(XDG_STATE_HOME or HOME/.local/state).absolute() / 'orchestrail'` (resolution of
`scripts/install-hooks.py:656` and `hooks/log-step-hook.sh:16`). Directories the engine
creates under `C` and `S` get mode 0700. An empty variable counts as unset.

### Deployment set

Harnesses, deploy paths, skill names and sources come from `deployment-set` (Contracts →
Relationship to spec 13's deployment engine), which applies spec 13's adapters, sources and
name map and spec 08's `ref-` namespace (its REQ-02, DM-3). For orientation, today's equivalent
(`scripts/sync.sh:89-174`):

| Source | Target | Type |
|---|---|---|
| `workflows/<n>.md` | `<skills_dir>/<installed name>/SKILL.md` | file |
| `rules/<n>.md` (top level) | `<skills_dir>/rule-<n>/SKILL.md` | file |
| `rules/reference/<n>.md` (only when spec 08 delivered it; spec 08 REQ-02) | `<skills_dir>/ref-<n>/SKILL.md` | file |
| `principles/<n>.md` | `<skills_dir>/principle-<n>/SKILL.md` | file |
| each skill directory above | `<skills_dir>/<name>/` | directory |
| `<skills_dir>` and, under `--harness`, every missing ancestor of `<skills_dir>` and of `always_on_path` up to the first existing directory | each such directory | directory (`created: true`) |
| `harness/<h>/always-on.md` + installation record (REQ-39) | `<always_on_path>` | file |

Nothing under `profiles/`, `docs/`, `tests/` or `.ai/` is a source (REQ-53). Installed files
get mode 0644. `VERSION` is optional for the engine: when absent, `source.version` and the
profile record's `version` are null.

### Retired targets (`scripts/install-retired.json`, new, `schema_version` 1)

`{"schema_version":1, "targets":[{"name": skill directory name, "file": "SKILL.md",
"sha256": [hex, …]}]}`. Initial content: `principle-python-standards` and
`principle-infra-standards`, each with the SHA-256 of every blob of
`principles/python-standards.md` and `principles/infra-standards.md` in the repository's
history (`git log --format=%H -- <path>` then `git rev-parse <commit>:<path>` content
hashes), computed once at delivery. The path checked is `<skills_dir>/<name>/<file>`; a
removed retired file's directory is removed when empty. An entry for a removed retired target
has `installed: {"removed": true}` and `original` `backup`; uninstall restores it.

### Ownership manifest (`install-manifest.json`, `schema_version` 1)

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | int | `1` |
| `installation_id` | string | 32 lowercase hex characters (`uuid4().hex`), created when the first non-dry-run plan is applied (before its journal and backups are written) and reused while a manifest exists; a new one after an uninstall that leaves no entry |
| `revision` | int ≥ 1 | Incremented at each committed install |
| `source` | object | `{"root": abs path, "version": VERSION content without trailing whitespace, "commit": 40-hex or null}`; `commit` is `git -C <root> rev-parse HEAD` when it succeeds |
| `harnesses` | list of strings | Harnesses with at least one entry, sorted |
| `entries` | list | Sorted by `path` |
| `delegated` | list | `[{"kind": "hooks", "harness": h, "result": object}]`, the hook installer's last result |

Entry:

| Field | Type | Meaning |
|---|---|---|
| `path` | string | Target path |
| `harness` | string | Harness name |
| `type` | `"file"` \| `"directory"` | Installed object type |
| `source` | string \| null | Source-root-relative path of the source file; for the always-on file, `harness/<h>/always-on.md`; null for directories |
| `installed` | object | `{"sha256": hex}` for files (for the always-on file, the hash of the composed bytes actually written); `{"removed": true}` for a removed retired target (REQ-65); `{}` for directories |
| `created` | bool | For directories, true when the engine created it; always false for files |
| `original` | object | `{"state": "absent"}`, `{"state": "migrated"}` (adopted from a spec 13 deploy manifest, REQ-43), `{"state": "preexisting-identical"}`, `{"state": "backup", "type": "file", "sha256": hex, "mode": "0644", "backup": abs path}` or `{"state": "backup", "type": "symlink", "target": link text}` |
| `retained` | string \| null | Conflict or info code that kept the entry after an uninstall (`user-modified`, `type-changed`, `backup-corrupt`, `directory-kept`), else null |
| `adopted_backups` | list | `[{"sha256": hex, "backup": abs path}]` of adopted-edit backups taken for this target, oldest first; reported at uninstall, never deleted |

`original.state` meanings: `absent` — nothing existed before the first install;
`preexisting-identical` — a foreign file already held exactly the bytes installed (no backup;
uninstall keeps it); `backup` — replaced under `--adopt` after an original backup. A
directory entry has `absent` when `created` is true and `preexisting-identical` otherwise.

### Installer journal (`install-journal.json`, `schema_version` 1)

`{"schema_version":1, "operation":"install"|"uninstall", "installation_id":…,
"manifest_sha256": hex|null, "commit": null|{"manifest_sha256": hex|null}, "steps":[step…]}`
where `manifest_sha256` is the hash of the ownership manifest when the operation started
(null when absent), `commit` stays null until Apply order step 11 sets it to the hash of the
manifest being committed (null inside the object when that step deletes the manifest), and
each step is
`{"path", "action", "previous", "next", "previous_backup": abs path|null, "temporary": abs
path|null, "applied": bool}`; `temporary` is the `.<basename>.tmp-<16 hex>` name chosen for a
file write, recorded before the temporary file is created. The hook step of an uninstall
(REQ-78) is `{"path": settings path, "action": "hooks-uninstall", "previous": null, "next":
null, "previous_backup": null, "temporary": null, "applied": bool}`.
`previous`/`next` are content identities (below). Steps are in apply order. The journal is
rewritten atomically (temporary file, `fsync`, `os.replace`) after each applied step.

### Content identity

`{"type":"absent"}`, `{"type":"file","sha256":hex}`, `{"type":"symlink","target":text}`,
`{"type":"directory"}`, or `{"type":"other"}` (FIFO, socket, device). Determined with
`lstat`; links are never followed.

### Plan (`schema_version` 1; printed by `--dry-run`)

| Field | Meaning |
|---|---|
| `schema_version` | `1` |
| `operation` | `install`, `uninstall` or `profile` |
| `source` | As in the manifest; null for uninstall |
| `recovery` | null, or `{"journal": path, "operation": …, "steps": [planned recovery actions]}` |
| `entries` | Sorted by `path`: `{"path", "harness" (null for profile), "type", "action", "source", "previous", "next", "ownership", "conflict", "backup"}`; `backup` is null or `{"kind": "original" \| "previous" \| "adopted" \| "profile", "path": abs path}` naming the backup the action will write |
| `delegated` | `[{"kind":"hooks","harness","operation","predicted_result","settings_path","settings_sha256_before","settings_sha256_after","receipt_path","receipt_sha256_before","receipt_sha256_after","lock_path"}]`; from `install-hooks.sh plan`: `predicted_result` is its `result` when `status` is `planned`, otherwise its whole output object; the path and hash fields are copied, or null when the output is unavailable; `lock_path` is `C/hooks-installed.lock` |
| `bookkeeping` | Sorted `{"path","action"}` for the manifest, journal, both locks (`C/install.lock`, `C/deploy.lock`), backup files and directories, each migrated spec 13 deploy manifest (`remove`), profile record; action `create`, `replace` or `remove`, except that a lock file appears only with `create` (or not at all when it exists) and is never removed (REQ-80) |
| `leftover` | Sorted list of absolute paths reported as leftover skills (REQ-79); empty for uninstall and profile |
| `summary` | Object with integer keys `create`, `replace`, `unchanged`, `remove`, `restore`, `keep`, `retain`, `conflict` |

`action` vocabulary: `create`, `replace`, `unchanged`, `remove`, `restore`, `keep`, `retain`.
`ownership` vocabulary: `absent`, `owned`, `owned-missing`, `modified`, `foreign`,
`foreign-identical`, `orphaned`, `legacy`, `retired`. `conflict` is null or a code from Contracts → Diagnostics.
Any action or ownership value outside these vocabularies is an internal error: exit 3
`internal-error`, nothing written (original REQ-05 "unknown actions are not performed").

### Profile manifest (`profiles/<name>/profile.json`, `schema_version` 1)

```json
{
  "schema_version": 1,
  "name": "python-fastapi",
  "description": "Python, FastAPI and infrastructure-as-code standards",
  "files": [
    {"source": "principles/python-standards.md", "target": ".ai/principles/python-standards.md"},
    {"source": "principles/infra-standards.md", "target": ".ai/principles/infra-standards.md"},
    {"source": "principles/code-examples.md", "target": ".ai/principles/code-examples.md"},
    {"source": "context/stack.md", "target": ".ai/context/stack-python-fastapi.md"}
  ]
}
```

Rules: exactly these four keys; `name` equals the directory name and matches
`^[a-z0-9]+(-[a-z0-9]+)*$`; `files` non-empty; each `source` is a relative path inside
`profiles/<name>/` naming a regular, non-symlink, UTF-8 file; each `target` is a relative
path starting with `.ai/principles/` or `.ai/context/`, without `..`, unique within the
list; `profiles/<name>/always-on-fragment.md` exists (spec 10 reads it).

The first profile's layout (new): `profiles/python-fastapi/principles/python-standards.md`
and `infra-standards.md` (moved byte-identical from `principles/`),
`principles/code-examples.md` (every matching prose line and every whole fenced block
containing a match, verbatim, one
`##` heading per origin file and section),
`context/stack.md` (moved byte-identical from `templates/stacks/python-fastapi.md`),
`always-on-fragment.md` (a pointer naming the four target files and stating they apply to
the project), `profile.json`.

### Profile record (`<project>/.ai/profile`, `schema_version` 1)

`{"schema_version":1, "name":…, "version": source VERSION, "files":[{"target", "sha256",
"source"}] sorted by target, "fragments": {"AGENTS.md": hex, "CLAUDE.md": hex}}`. `sha256` is
the content written; `fragments` holds the hash of each managed region's content.

### Managed fragment

```
<!-- BEGIN MANAGED PROFILE: <name> -->
<profile fragment bytes, as printed by gen-docs.py --profile, ending in \n>
<!-- END MANAGED PROFILE -->
```

The begin line matches `^<!-- BEGIN MANAGED PROFILE: ([a-z0-9]+(-[a-z0-9]+)*) -->$`, the end
line `^<!-- END MANAGED PROFILE -->$`. The two marker lines belong to the managed region:
replacing a region rewrites the begin line with the new profile name. A begin-line name that
differs from the profile record's `name` (or that exists while no profile record exists and
differs from the profile being applied) is `fragment-markers-invalid`. The region content is the bytes after the begin
line's `\n` up to the start of the end line. When no region exists, the engine appends
`\n` if the file is non-empty and does not end with `\n`, then `\n<begin>\n<fragment><end>\n`;
a missing instruction file is created with `<begin>\n<fragment><end>\n`.

### Neutral-core rewrite rule

For each line of `principles/code-quality.md` and `principles/testing-standards.md` that
matches a stack term: a fenced code block containing the line is moved verbatim to
`profiles/python-fastapi/principles/code-examples.md` and replaced in the core by a ```` ```text ````
block expressing the same point in language-neutral pseudocode; a prose line is copied
verbatim to that file and rewritten in the core without the term, keeping its obligation
(for example "In Python: if using ABC or Protocol" → "If using an interface"; "Dataclasses /
Pydantic models for data containers" → "Plain data-container types for data"). Known matches
at `060ce6d`: `principles/code-quality.md:26`, `:45`, `:89`, fences starting at `:101` (holding `:111`),
`:121`, `:143`; `principles/testing-standards.md` fences at `:13`, `:77`, `:116`, `:148`,
`:166`, `:213`. Discovery lists every match with its disposition; the Part A reviewer
confirms that no obligation was dropped.

### Stack terms

Case-insensitive, whole word (`\b…\b`): `python`, `fastapi`, `sqlalchemy`, `pydantic`,
`pytest`, `postgres`, `postgresql`, `asyncpg`, `gcp`, `google cloud`, `cloud run`, `terraform`,
`mypy`, `ruff`, `alembic`, `structlog`. Checked in `principles/*.md` only, code blocks
included.

### Optional-feature table (`docs/OPTIONAL-FEATURES.md`)

Header row exactly `| Feature | State | Prerequisites | Enable | Without it | Disable and resume | Evidence |`.
Required rows (first cell exact): `Native logging hooks`, `Git rails hook`, `Model catalog
and selection`, `Usage telemetry`, `Exact run timing`, `Stack profiles`, `Generated
references`, `Golden runs`, `State tool`. `State` is one of `delivered`, `partial`,
`planned`, set from the source at implementation time. `Evidence` lists backticked
repository paths; for `delivered` and `partial` every path exists. For `planned`, `Enable`
is exactly `not available`. The document also has `## Cost and usage figures` defining the
five cost basis labels and `## Capability declarations` linking `harness-matrix.md` and
stating that declared support, installation result and checkpoint coverage are distinct.

### Money figure

A line matching `\$\s?[0-9]` or `\b[0-9][0-9.,]*\s?USD\b`, outside fenced code blocks.

### Example layout (`docs/examples/flat-task/`)

| File | Kind | Content |
|---|---|---|
| `README.md` | authored | Provenance summary, artifact index, statement "hand-authored reference result of a correct run; not produced by a model run", synthetic-data statement, independent checks applied |
| `spec.md` | copied | The specification file under `.ai/specs/` of the built reference workspace (from the seed project or the overlay) |
| `discovery/plan.md` and `discovery/<subtask>/description.md` | copied | The task's `plan.md` and subtask `description.md` files of the built workspace |
| `state-after-execution.md` | copied | The task's final `state.md` of the built workspace |
| `pull-request.md` | authored | Pull-request description for the reference commits in the `/spec-run` body format |
| `run-log-summary.md` | authored | Table `| Step | Subtask | Outcome | Tests | Duration | Tokens | Cost |`, one row per run-log step event in the built store's order; `Step`, `Subtask`, `Outcome` and `Tests` are the events' `step`, `subtask`, `outcome` and `tests` values (the `gate` value, when present, is not shown); `Duration`, `Tokens`, `Cost` are `unknown` |
| `provenance.json` | authored | Example provenance |

The example is produced by spec 09's
`python3 -I scripts/golden-eval.py build-reference --case flat --workflow spec-run --out <dir> --date-base <timestamp>`.
Copied files are the built bytes (after spec 09's `finalize` has replaced the `{C<n>}`/`{c<n>}`
placeholders), never the raw overlay; `run-log-summary.md` is derived from the run-log store
the command builds, taking only the deterministic event fields of spec 09 → Reference build
determinism (`step`, `subtask`, `outcome`, `tests`, `gate` and their order); the store's bytes,
times and run ids are never copied, because `scripts/log-step.sh` stamps them anew on every build.
Spec 09 marks `flat` as `tuning` with `published: true` in its `case.json` (its case field table; REQ-50 rejects a holdout task on it), so the
example's source case can never be a holdout task. When the built workspace holds no file or more than one file under
`.ai/specs/`, Discovery records the chosen path in `provenance.json` and states why.

### Example provenance (`provenance.json`, `schema_version` 1)

`{"schema_version":1, "source_kind":"reference workspace", "case":"flat",
"workflow":"spec-run", "source_commit":40-hex, "version": VERSION or null, "date_base":
timestamp passed to build-reference, "files":[{"path": example path, "built_path": path
relative to the build output|null, "sha256": hex, "authored": bool}]}`; `built_path` is null
exactly when `authored` is true; `files` lists every file in the directory except
`provenance.json` itself.

### Example privacy patterns

Regular expressions, any match fails: `/home/`, `/Users/`, `[A-Za-z]:\\`, `\bsk-[A-Za-z0-9]{16,}`,
`\bghp_[A-Za-z0-9]{20,}`, `\bAKIA[0-9A-Z]{16}\b`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`,
`hygiene-patterns`, `settings\.local\.json`. The tracked-file hygiene scan (RC-08) covers the
private patterns.

### Contribution guide (`docs/CONTRIBUTING.md`)

Sections, in order: `## Change procedure` (spec → Discovery → test-first execution →
validation; link `.ai/README.md`), `## File shapes` (link `.ai/principles/coding.md`),
`## Commits` (format, no attribution trailers, no planning identifiers; link the git-flow
rule file under the name spec 13 gives it, `rules/git-flow.md` today), `## Offline checks` (each command in backticks: the contract validator,
`--hygiene-only` with a local pattern file, `gen-docs.py --check`, `check-spec-draft.sh`,
`check-gen-docs.py`, `check-install.py`, `check-public-readiness.py`, and spec 09's offline
suite `python3 -I tests/golden-runs.py`, which `scripts/validate-contracts.sh` does not run),
`## Audit method` (link `.ai/context/runbook.md` and describe the independent-audit procedure
there; `docs/audits/AUDIT-PROMPT.md`, which that procedure names at `.ai/context/runbook.md:103`,
is absent from the tree and is not linked), `## Deployment boundary`
(never edit deployed copies; `sync.sh` is the maintainer command; contributors use
`install.sh --dry-run`; tests use disposable homes).

### Contribution templates

- `bug_report.md`: front matter `name`, `about`, `labels: bug`; headings `## Version`,
  `## Harness`, `## Steps to reproduce`, `## Expected`, `## Actual`; the line
  `Do not paste secrets, private code or real session logs.`
- `change_request.md`: front matter `name`, `about`; headings `## Problem`,
  `## Proposed change`, `## Affected files`.
- `PULL_REQUEST_TEMPLATE.md`: headings `## Summary`, `## Checks run`, `## Documentation`; a
  checklist line stating that commits follow the git-flow rule (linked under its name at
  delivery) with no attribution trailers and no planning identifiers.

### Translation provenance line

`Translation of the Russian original <path> at commit 8c2fa08c18115ffcf38a1798742c41e53a2c7461 (blob <40-hex>); the translation does not change normative content.`
appended as the last line, preceded by one blank line. Appending keeps every ledger-pinned
line number unchanged.

### Onboarding measurement (`docs/audits/<YYYY-MM-DD>-onboarding-measurement.md`)

Fields as a two-column table: `Candidate commit`, `Operating system`, `Shell`, `Python`,
`Git`, `Harness and version`, `Environment` (fresh `HOME` and XDG directories, fresh clone),
`Prerequisites ready (minutes)`, `Install (minutes)`, `Project setup (minutes)`, `Waiting for
external access (minutes)`, `Total to first Discovery command (minutes)`, `Blocking
dependencies`, `Target 15 minutes` (`met` or `not met`, with the cause when not met). Times
are wall-clock minutes from a stopwatch; no field is left empty (`none` is allowed for
`Blocking dependencies`).

### Release items and statuses

Status vocabulary: `pass`, `fail`, `not-verified`, `blocked`, `owner-decision-pending`.
`docs/RELEASE-CHECKLIST.md` holds the item table below, the verification command and status
rules of each item, `## Onboarding procedure` (fresh `HOME` and XDG directories, fresh clone,
the README steps up to the first Discovery command, a stopwatch, and the record fields of Data
Model → Onboarding measurement) and `## Release sequence` (Contracts → Release check and
REQ-72).

| Item | Subject | Kind |
|---|---|---|
| RC-01 | Clean working tree; candidate commit recorded | automated |
| RC-02 | `bash scripts/validate-contracts.sh` exits 0 | automated |
| RC-03 | `gen-docs.py --check` exits 0 | automated |
| RC-04 | `scripts/check-install.py` exits 0 | automated |
| RC-05 | `scripts/check-public-readiness.py` exits 0 | automated |
| RC-06 | `scripts/check-spec-draft.sh` and `scripts/check-gen-docs.py` exit 0 | automated |
| RC-07 | Spec 09 offline suite `python3 -I tests/golden-runs.py` exits 0 (`not-verified` when `tests/golden-runs.py` is absent or the suite exits 3 because `pytest` is unavailable, 09 REQ-35) | automated |
| RC-08 | Public hygiene (REQ-14) | automated |
| RC-09 | Onboarding measurement for this candidate | manual |
| RC-10 | Release golden runs under an owner-approved manifest (spec 09) | owner |
| RC-11 | Required pull-request review on the default branch | manual |
| RC-12 | No direct push to the default branch | manual |
| RC-13 | Required status check `offline-checks` (REQ-81, REQ-16) | manual |
| RC-14 | `LICENSE` Apache-2.0 with the owner's holder wording | owner |
| RC-15 | Authorization of the specific version and tag | owner |
| RC-16 | Publication | owner |

Candidate report (`docs/audits/<YYYY-MM-DD>-release-candidate-<version>.md`): candidate
commit, intended version, table `| Item | Status | Evidence |` with RC-01–RC-16, verdict line
`Verdict: ready` or `Verdict: not ready`, and the list of items that block `ready`. Order:
(1) `release-check.sh` and the manual items run on the candidate commit; (2) the report is
added in a following commit that changes only files under `docs/audits/`; (3) for a version
the owner authorizes, the release-preparation commit of REQ-72 becomes a new candidate and
steps 1–2 repeat for it; (4) the tag, when authorized, goes on that last report commit. RC-01 passes on a later commit only when
`git diff --name-only <candidate commit> HEAD` lists only `docs/audits/` paths. Suite B
validates candidate reports and onboarding records only when at least one exists, so it can
pass on the candidate commit itself.

## Contracts & Interfaces

### Command lines

```text
bash scripts/install.sh [--dry-run] [--adopt] [--force] [--harness <name>]... [--from <dir>]
bash scripts/install.sh --uninstall [--dry-run] [--force] [--from <dir>]
bash scripts/install.sh -h | --help
python3 -I scripts/install.py install   --source <root> [--dry-run] [--adopt] [--force] [--harness <name>]...
python3 -I scripts/install.py uninstall --source <root> [--dry-run] [--force]
python3 -I scripts/install.py profile   --source <root> --project <dir> --name <name> [--dry-run] [--adopt]
python3 -I scripts/install.py profile-check --source <root> --name <name>
bash scripts/install-hooks.sh plan install [--from <dir>] | plan uninstall
bash scripts/sync.sh [--from <dir>] [--adopt] [--force]
bash scripts/setup-new-project.sh [--profile <name>] [--adopt]
bash scripts/release-check.sh [--denylist <file>]
python3 scripts/check-install.py
python3 scripts/check-public-readiness.py
```

- Launcher: `#!/usr/bin/env bash`, `set -uo pipefail`, header comment per
  `.ai/principles/coding.md → Shell scripts`. Source root precedence `--from` >
  non-empty `ORCHESTRAIL_HOME` > parent of `scripts/`; a missing directory → exit 2 `usage`.
  Python older than 3.11 or missing → exit 3 `runtime-unavailable` (same probe as
  `scripts/install-hooks.sh:45`). `--uninstall` with `--adopt` or `--harness`, an unknown
  option, a repeated `--from`, or a `--harness` name without `harness/<name>/deploy.env` →
  exit 2 `usage`.
- `--force` is passed only to spec 13's active-task rule and, for `project-pass`, to its project skip (REQ-42).
- `install-hooks.sh plan <op>`: same dependency and runtime guards as `install`/`uninstall`
  (a missing dependency prints the existing unavailable JSON); prints one JSON line
  `{"status":"planned","operation":…,"result":<object install|uninstall would print>,
  "settings_path":…,"settings_sha256_before":hex|null,"settings_sha256_after":hex|null,
  "receipt_path":…,"receipt_sha256_before":hex|null,"receipt_sha256_after":hex|null}`; it
  simulates `recover_snapshot` and `plan_update` (`scripts/install-hooks.py:564-599`) in
  memory, takes no lock and writes nothing; exit 0.
- `sync.sh` (spec 13's step list, changed here): source checks, validator, runtime guard and
  legacy reporting as spec 13 defines them → `gen-docs.py --check` (spec 10; on its failure sync
  prints spec 10's REQ-22 message and exits 1) → where spec 08 is delivered,
  `measure-context.sh check --root "$ROOT"` (spec 08 REQ-08, its message, exit 1), kept next to
  the generator check → launcher with
  `--from "$ROOT"` and `--harness <name>` for every `harness/*/deploy.env`, passing `--adopt`
  and `--force` through → `deploy-skills.py project-pass --from "$ROOT" [--force]` only after
  exit 0. Spec 13's separate hook-installation step and its `deploy-skills.py deploy` step are
  removed (the engine runs the hook installer). Any non-zero installer exit makes sync print
  `ERROR: installation stopped (exit <n>); see the diagnostics above` and exit with that code.
- `setup-new-project.sh`: options are parsed before any write; `--adopt` without `--profile`
  → exit 2. With `--profile`, setup first validates the profile name, `profile.json` and the
  fragment (`install.py profile-check`, which reads only the source tree: name grammar, `profile.json`
rules, source files and `gen-docs.py --profile`; exit 0, 2 or 3) and stops with
  the engine's exit code before its first write when validation fails. The profile step then
  runs after `CLAUDE.md`, `.ai/` and `AGENTS.md` exist and before the `.gitignore` and registry
  steps, as
  `python3 -I "$WORKFLOWS_SRC/scripts/install.py" profile --source "$WORKFLOWS_SRC" --project "$PROJECT_DIR" --name <name> [--adopt]`;
  a non-zero exit stops setup with that exit code. The interactive stack prompt
  (`:195-230`) is removed; `templates/AGENTS.md:80-82` is replaced by the comment
  `<!-- Project-specific standards go here; a selected profile adds a managed block at the end of this file. -->`.
- The profile operation obtains fragment bytes from
  `python3 -I <source>/scripts/gen-docs.py --profile <name> --root <source>`; a non-zero exit →
  exit 3 `profile-fragment-unavailable`.

### Relationship to spec 13's deployment engine

Spec 13 delivers `scripts/deploy-skills.py` (adapters, sources, name map, registry, deploy
manifests DM-6, journal and lock DM-7, active consumers, project pass). Its engine, deploy
manifests, journal and lock, `--force` and `sync.sh` exit code 3 are correct and complete as
the state between the two deliveries; this spec supersedes the write path (spec 13 Notes →
Relationship to spec 11, A-31; its Q-05 is resolved). This spec changes it as follows:

- `deploy` is removed (REQ-71); `install.py` is the only global writer.
- `deployment-set --from <root> [--force]` (new, read-only, takes no lock): prints one JSON
  object `{"schema_version":1, "harnesses":[{"name", "skills_dir", "skills_dir_resolved",
  "always_on_path", "has_hooks": bool, "skills":[{"name", "source"}],
  "leftover_candidates":[path]}], "active":[{"root", "task"}]}` built by spec 13's adapter, source, name-map and active-consumer logic; exit 0,
  or spec 13's error codes with exit 1. `active` lists every active registered root, the
  source checkout included (spec 13 REQ-43, DM-8), and is empty under `--force`, which
  overrides only that freeze. A harness's `leftover_candidates` holds the
  sorted absolute paths of existing directories `<skills_dir>/<name>` for the spec 13
  leftover names (spec 13 Terminology → Leftover skill: `<old>` of a workflow row,
  `rule-<old>` of a rule row, `PIPELINE` and `rule-global-claude` of the file rows, none of
  them a current installed name). The engine builds its deployment set from it (Data Model →
  Deployment set) and adds the always-on composition (REQ-39).
- `project-pass --from <root> [--force]` (new): runs spec 13's project pass unchanged and
  prints its project lines; it takes spec 13's lock `C/deploy.lock`.
- `list-projects` and `link-project` are unchanged; `scripts/setup-new-project.sh` keeps
  calling `link-project`.
- Locks: the engine holds `C/install.lock` and then `C/deploy.lock` (non-blocking, the same
  5-second retry) for a non-dry run, so a spec 13 engine from another checkout cannot write
  concurrently.
- Migration (REQ-43): each DM-6 object becomes an entry with `path` = object `path`,
  `harness` = manifest `harness`, `type` `file`, `source` from `deployment-set` (null when the
  object is no longer planned), `installed.sha256` = object `sha256`, `created` false,
  `original` `{"state": "migrated"}`; directories of migrated skills become `directory`
  entries with `created` true (spec 13's engine created them), so uninstall removes them when
  empty. A spec 13 journal (`C/deploy/journal.json`) present at start
  → exit 2 `legacy-journal-present` with the instruction to complete spec 13's recovery from
  the checkout that wrote it; nothing written.
- `scripts/check-deploy-skills.py` (spec 13's suite) is updated in Part A: its `deploy` cases
  move to suite A as installer cases or are rewritten against `deployment-set` and
  `project-pass`, and its other cases stay unchanged.

**Leftover skills (spec 13 REQ-57).** Leftover reporting lives in the installer, which stays
after `deploy` is removed: `install` (not `uninstall`) takes each harness's
`leftover_candidates` from `deployment-set`, drops every candidate that is, or lies inside,
the path of a manifest entry (an owned object is not a leftover), and reports the rest as
`leftover <dir> (not removed; review, then remove it manually)` lines and in the plan's
`leftover` field (REQ-79). Spec 13's detection knowledge (name map, adapters) stays in
`deployment-set`; the ownership knowledge stays in the installer.

**Preserved contracts of spec 13** (spec 13 Notes → Relationship to spec 11), each met by a
requirement of this spec or changed on purpose:

| Spec 13 contract | Met here by |
|---|---|
| An owned file the user changed is never overwritten or removed; a conflict writes nothing (13 REQ-42, REQ-63) | REQ-03, Install classification (`user-modified`, exit 1, nothing written); the exception is `--adopt` with a verified backup (REQ-06), which replaces 13's implicit first-run adoption (see below) |
| A deferral writes nothing while any active consumer exists, the source checkout included; `--force` overrides only that freeze (13 REQ-43, DM-8) | REQ-42 and `deployment-set`'s `active` list |
| Leftover skills are reported and never removed (13 REQ-57) | REQ-79 |
| The registry stays read-only (13 REQ-08) | REQ-80 (REQ-35 for uninstall) |
| The lock is never taken over (13 DM-7) | REQ-80, REQ-24 |
| The project pass stays as 13 defines it and never touches profile files (13 Contracts → Project pass) | REQ-71 (`project-pass` unchanged), REQ-80, A-21 |

Explicit changes from spec 13, each with its reason:

- Implicit first-run adoption of unrecorded managed paths (13 A-10) becomes the `foreign-target`
  conflict with `--adopt` as the explicit remedy, because the owner's request requires that user
  bytes are never replaced without a verified backup (REQ-03, REQ-06); homes deployed by spec
  13's engine are migrated as owned objects (REQ-43), and the Risks table records the one-time
  `sync.sh --adopt` for older homes.
- A modified owned orphan: 13 prints `release-modified` and drops the entry in the same run;
  here it is a `user-modified` conflict that writes nothing and, under `--adopt`, is released
  with `released` (REQ-73), because a conflict writes nothing. Likewise 13's `keep-nonempty`
  line becomes the `directory-kept` info.
- The deferral's exit code and wording are this spec's: exit 1 with `active-task` (REQ-42), and
  `sync.sh` passes the installer's exit code through instead of spec 13's exit 3.
- Spec 13's `forced <root>` lines under `--force` are not printed: `deployment-set` returns an
  empty `active` list under `--force`, so the installer does not know the forced roots; the
  override itself is unchanged.
- `target-moved` and the deploy manifest's `install_id` are not carried over: manifest entries
  hold absolute target paths, so a changed `skills_dir` yields orphaned entries and path
  checks (REQ-69, REQ-37) instead of a stored identifier comparison.

### Standard output

- `--dry-run`: the plan JSON only.
- Other runs: one line `<action> <path>` per entry whose action is not `unchanged`, in plan
  order, then one `leftover <dir> (not removed; review, then remove it manually)` line per
  leftover skill (install only, REQ-79), then `summary: create=<n> replace=<n> unchanged=<n> remove=<n> restore=<n> keep=<n> retain=<n> conflict=<n>`,
  then, only when the run wrote a target, spec 13's residual-race `note:` line as the last
  line (Apply order step 6).

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Completed; or dry-run plan without conflicts; or uninstall with `no-manifest` |
| 1 | Conflicts or `active-task` deferral; install and profile wrote nothing; uninstall applied safe entries and retained the rest |
| 2 | Invalid request or input: `usage`, `source-invalid` (a required source file — `scripts/install.py`, `scripts/deploy-skills.py`, a harness's `deploy.env` or generated `always-on.md` — missing or unreadable), `legacy-journal-present`, `deploy-config-invalid`, `manifest-invalid`, `journal-invalid`, `profile-invalid`, `profile-record-invalid`, `profile-not-found` |
| 3 | Unavailable before the first write: `runtime-unavailable`, `generated-files-stale`, `no-harness`, `installer-busy`, `target-not-writable`, `project-not-initialized`, `profile-fragment-unavailable`, `io-error`, `internal-error` |
| 4 | Incomplete: a failure after the first target write, `source-changed`, `target-changed`, or recovery that left a conflict; the journal is retained |

A dry-run exits 0 or 1 by the same rule and never 4.

### Diagnostics

One line per finding on standard error: `install: <code>: <path or ->: <message>`, sorted by
path then code. Codes and severities:

| Code | Kind | Trigger |
|---|---|---|
| `foreign-target` | conflict | Existing target without entry, content differs from next |
| `user-modified` | conflict | Modified target |
| `symlink-target` | conflict | Target is a symbolic link |
| `symlink-in-path` | conflict | REQ-69 |
| `foreign-owner` | conflict | REQ-37 |
| `type-changed` | conflict | REQ-32 |
| `backup-corrupt` | conflict | REQ-33 |
| `fragment-markers-invalid` | conflict | REQ-48 |
| `active-task` | conflict | REQ-42 |
| exit-2 and exit-3/4 codes above | error | Exit-code table |
| `no-manifest`, `no-original`, `directory-kept`, `kept-preexisting`, `kept-deleted`, `released`, `legacy-target`, `legacy-target-modified`, `hooks-unavailable`, `hook-result-differs` | info | Reported, never change the exit code |

### Install classification (per file target)

| Current (lstat) | Entry | Next equals current | Result |
|---|---|---|---|
| absent | none | — | `create`, ownership `absent` |
| absent | present | — | `create`, ownership `owned-missing` |
| file = entry's installed hash | present | yes / no | `unchanged` / `replace` (owned) |
| file ≠ installed hash | present | yes | `unchanged`; entry updated to the current hash |
| file ≠ installed hash | present | no | conflict `user-modified`; with `--adopt`: adopted-edit backup under `S/adopted-backups/` and `replace` (REQ-23) |
| file | none | yes | `unchanged`, ownership `foreign-identical`, `original.state` `preexisting-identical` |
| file | none | no | conflict `foreign-target`; with `--adopt`: original backup and `replace` |
| symbolic link | any | — | conflict `symlink-target`; with `--adopt`: original backup of the link text and `replace` with a regular file |
| directory or other | any | — | conflict `type-changed` |

A `user-modified` target adopted under `--adopt` keeps its existing `original` field; its
modified bytes are stored as an adopted-edit backup under `S/adopted-backups/`, appended to
the entry's `adopted_backups` and reported; the engine never deletes that file. For directory targets: absent → `create` (`created:
true`); existing directory → `unchanged` (`created: false` unless an entry says true); any
other type → `type-changed`. Ownership checks (REQ-37) and writability of every parent
(`target-not-writable`) are evaluated during planning.

### Uninstall classification (per entry)

| Current | Entry `original` | Result |
|---|---|---|
| file = installed hash | `absent` | `remove` |
| file = installed hash | `preexisting-identical` | `keep` (info `kept-preexisting`); entry dropped |
| file = installed hash | `backup` | verify backup hash → `restore` (bytes and mode, or link text); mismatch → `backup-corrupt`, `retain` |
| file ≠ installed hash | any | `retain`, conflict `user-modified`, message names the backup path or `none` |
| absent | `backup` | `restore` |
| absent | other | entry dropped |
| file = installed hash | `migrated` | `remove` (info `no-original` for an always-on file: its pre-install content was never backed up) |
| absent | entry with `installed: {"removed": true}` (retired) | `restore` from the original backup, first recreating its parent directory with mode 0755 when absent |
| present | entry with `installed: {"removed": true}` | `retain`, conflict `user-modified` (the user re-created the retired file); original backup path reported |
| directory, symbolic link or other | any | `retain`, conflict `type-changed` |
| directory entry, `created: true` | — | removed with `rmdir` after its files when empty; otherwise `keep` with info `directory-kept` |

The hook delegate runs `install-hooks.sh uninstall`; its result is reported, never retried.
After applying, the manifest keeps exactly the retained entries (with `retained` set); when
none remain, the manifest, journal and `S/install-backups/<installation_id>/` are deleted.

### Apply order (install)

1. Resolve paths; run REQ-40's check; run `deploy-skills.py deployment-set --from <root>
   [--force]` (its failure → exit 2 `deploy-config-invalid`); select targeted harnesses
   (none → exit 3 `no-harness`).
2. Non-dry-run only: create `C` with mode 0700 and acquire `C/install.lock`, then
   `C/deploy.lock` (`fcntl.flock`, non-blocking, retry every 25 ms for 5 s →
   `installer-busy`).
3. Recovery when a journal exists (dry-run: plan it only).
4. `install-hooks.sh plan install --from <root>` for each harness with `hooks.json`.
5. Build the deployment set, classify every target and build the plan.
6. When at least one entry's action is not `unchanged` or `keep`: spec 13's active-consumer
   rule (REQ-42). In a non-dry run, `deployment-set` is run again now, while both locks are
   held (spec 13 REQ-43 evaluates after taking the lock), and its `active` list decides; a
   dry run uses the list from step 1. A deferral adds `active-task` to the plan. A run that
   writes prints spec 13's residual-race note
   `note: task starts during deployment are not detected; run sync when no pipeline run is starting`
   as the last line of its standard output.
7. Dry-run: print the plan and exit 0, or 1 when it has a conflict. Otherwise, conflicts →
   diagnostics, exit 1.
8. Write the journal; take every backup (`fsync` file and directory); run
   `install-hooks.sh install --from <root>`; if its result differs from the predicted one,
   rebuild the always-on targets' next content with the actual result, record it in the
   journal and report `hook-result-differs`.
9. For each step: re-verify the source hash and the target's content identity (REQ-45);
   write `.<basename>.tmp-<16 hex>` in the target directory, `fsync`, `os.replace`, `fsync` the
   directory; mark the step applied.
10. Remove orphaned owned targets and empty created directories (also journalled steps).
11. Record the SHA-256 of the manifest about to be written as `commit` in the journal; write the manifest (temporary file, `fsync`, `os.replace`); delete the journal
    and the operation's previous-state backups; release the lock; print the summary.

Uninstall follows steps 1–3 (without the generated-file check and harness selection: its
targets come from the manifest; it uses `deployment-set` only for `active`; a failing `deployment-set` is exit 2
`deploy-config-invalid` because active consumers cannot be evaluated — `--force` does not
bypass it, and the user runs the uninstall from a checkout whose configuration is valid), classifies by Uninstall classification, applies step 6, and
in step 7 stops only for `active-task` (exit 1, nothing written); `retain` entries do not
stop it (REQ-70). It journals each `remove`/`restore` with a previous-state backup of the
removed bytes, journals and then runs `install-hooks.sh uninstall` after the target steps
(REQ-78), and finishes with
step 11 (or deletes the manifest when no entry is retained), exiting 1 when any entry was
retained and 0 otherwise.

`ORCHESTRAIL_INSTALL_TEST_FAULT=after-write:<n>` (test-only) makes the engine exit 4
immediately after the n-th applied step, without cleanup, to simulate an interruption; it
can only stop a run. `ORCHESTRAIL_INSTALL_TEST_FOREIGN_UID=<path>` (test-only) makes the
engine treat that path as owned by another user ID; it can only add a `foreign-owner`
conflict. Both are read only by the engine and documented as test seams in
`scripts/README.md`.

### Recovery

First, every step's `temporary` file that still exists is deleted. A journal with
`operation: install` is rolled back: steps marked applied, in reverse order — current
identity equals `next` → restore `previous` from its previous-state backup (or remove when
`previous` is absent); equals `previous` → nothing; anything else → conflict
`target-changed`, both versions kept and reported. A journal with `operation: uninstall` is
rolled forward from its own steps, in order: current identity equals `next` → done; equals
`previous` → apply the step; anything else → conflict `target-changed`; a hook step not
marked applied is executed by running `install-hooks.sh uninstall` (REQ-78); afterwards the
manifest is rewritten as step 11 of that uninstall would have written it. Hook settings are not rolled
back (the hook installer is idempotent and recovers its own transactions; info
`hooks-unavailable` is reported only when its result is unavailable). A recovery without
conflicts deletes the journal and continues with the requested operation; with conflicts it
exits 4 and keeps the journal. Before any of this, the current manifest's hash (null when
absent) is compared with the journal: `commit` is not null and the hash equals
`commit.manifest_sha256` → the operation had committed; only the journal and the previous-state backups are deleted; equal to
`manifest_sha256` → roll back or forward as above; anything else → `journal-invalid` (exit 2,
nothing written).

### Profile three-way rules (per target; base = profile-record hash, cur = current, new = next)

| State | Result |
|---|---|
| no record, target absent | `create` |
| no record, cur = new | `unchanged`; recorded |
| no record, cur ≠ new | conflict `foreign-target` |
| record, target absent | `keep` with info `kept-deleted` (not recreated); with `--adopt`: `create` |
| cur = base, new = base | `unchanged` |
| cur = base, new ≠ base | `replace` |
| cur ≠ base, cur = new | `unchanged`; record updated |
| cur ≠ base, new = base | `keep` (user edit, nothing to upgrade) |
| cur ≠ base, new ≠ base, cur ≠ new | conflict `user-modified` |
| target only in the previous profile, cur = base | `remove` |
| target only in the previous profile, cur ≠ base | `keep`, reported |

Fragments follow the same table with the region content as cur and the region's recorded
hash as base; a missing region with a record is re-inserted. Under `--adopt`, a conflicting
target's current bytes are copied to `S/profile-backups/<sha256>` (verified) before
replacement and the path is reported. The profile operation locks the project by
`fcntl.flock` on an open descriptor of `<project>/.ai/` (5 s, `installer-busy`), writes every
file atomically and writes `.ai/profile` last. Any conflict → nothing written, exit 1.

### Dry-run contract

`rules/contract-dry-run.md` is a new rule that follows spec 13's Notes → Files and sections
created after this spec: stem `<kind>-<subject>` with kind `contract` (it states obligations
that hold across workflows, spec 13 DM-2), front matter of exactly `description:` and
`load: on-demand` (no `loads:` of its own), and no `docs/name-map.json` row, because it never
had an old name. It is deployed like every rule. Spec 08 applies to it in full: the whole file
stays within the 700-word limit of every top-level rule (spec 08 REQ-01), so the seven clauses
are kept short. Its section
`## Dry-run contract` holds exactly these numbered clauses:

1. **Reads.** Any project file and read-only git commands (`status`, `log`, `diff`, `show`,
   `rev-parse`, `ls-files`, `for-each-ref`) are allowed.
2. **No writes.** Project files, `.ai/`, task state, the index, branches, tags, stashes,
   commits, the project registry, deployed files and the model catalog stay unchanged;
   nothing is pushed and no pull request is created.
3. **Telemetry only.** The only write exception is best-effort run-log telemetry:
   `run-start`, one `--step dry-run --outcome skipped --note approximate`, and
   `run-end --outcome completed`.
4. **No execution.** No test, build, lint or project command runs; no sub-agent or
   additional model is started; no web request is made.
5. **Report.** The report has the headings `Inputs read`, `Would write`, `Would run`,
   `Uncertain`, `Next command`.
6. **Uncertain.** A step whose outcome needs execution, an unanswered question or an
   unavailable input is listed under `Uncertain` with its reason; questions are not asked.
7. **No resume state.** A dry run leaves nothing that a later resume reads.

Workflow items: each of the two workflows gains a `## Dry-run` section citing
`contract-dry-run → ## Dry-run contract` and naming its items by these labels. Discovery
orchestrator: `Resolved spec`; `Task directory` (to create, or the resume point of an
existing one); `Children` (it would run); `Derived analysis` (what it can derive without
writing). `/bugfix`: `Task directory` (matching or new); `Quick-gate verdict` (when
determinable, else under `Uncertain`); `Reproduction test` (path and assertion it would
write); `Reproduction result` (always under `Uncertain`).
Both Invocation lines gain `[--dry-run]`. `/spec-run`'s `--dry-run` bullet keeps its own
items and adds the citation. Where spec 08's `loads` metadata exists, the three workflows
declare the rule in it using spec 08's grammar (DM-1), because spec 08's check reports a
textual load command with an undeclared target (`textual-load-undeclared`, REQ-12) and an on-demand rule that
no workflow's loads reach (`rule-unreachable`, REQ-19) and its deployment gate then stops
sync. Spec 08's condition registry has no `--dry-run` feature, so the declaration is a
`mandatory` entry with `sections: ["## Dry-run contract"]`; adding a conditional feature is
spec 08's additive change, not made here.

### Release check (`scripts/release-check.sh`)

Runs RC-01–RC-08 in order, continuing after failures, with the pattern file resolved as
`scripts/validate-contracts.sh:350-366` does (`--denylist` overrides) and passed to
`validate-contracts.sh --hygiene-only --denylist <file>`. It prints
`| Item | Status | Evidence |` with RC-01–RC-16; RC-09, RC-11, RC-12 and RC-13 print
`not-verified` with evidence `manual item; record in the candidate report`, and RC-10 and
RC-14–RC-16 print `owner-decision-pending` with evidence `owner item`. Evidence for RC-01 is the commit
hash; for others the command and its exit code. Exit 0 when RC-01–RC-08 are all `pass`, 1
otherwise, 3 when `git` or Python 3.11 is unavailable. It writes no file (temporary files
only under `mktemp -d`, removed by an exit trap).

### Existing-check obligations

- `README.md` keeps the statements and links that `scripts/validate-contracts.sh:4615-4633`
  requires: 60 lines or fewer; "Orchestrail"; purpose; the pre-1.0 instability sentence; a
  sentence naming `sync.sh` before `~/.claude` and `~/.codex`; links `](docs/USAGE.md)`,
  `](docs/SPEC-RUN-QUICKSTART.md)`, `](.ai/specs/README.md)`. It does not contain the clone
  URL (identity ledger); it links `docs/USAGE.md#4-initial-setup-new-machine--standalone-project`
  for cloning.
- Except in REQ-72's release-preparation commit (which changes check expressions only through
  spec 13's schema-2 inventory amendment, followed by re-pinning), edits to
  `scripts/validate-contracts.sh` are allowed only inside function bodies outside the
  pinned-body region, never in a `check` line or failure message, and never add or
  remove a line matching `\bcheck\b`; any edit is followed by the source-guard re-pinning
  procedure. This spec needs none unless REQ-63 forces a body change.
- Changing `scripts/sync.sh` or `scripts/setup-new-project.sh` is followed by re-pinning their
  digests under `tests/fixtures/validator-runtime/README.md:9-28`. `tests/hook-install.sh` is not
  edited; if a change is unavoidable, its inventory resource entry is re-amended and the
  oracle digest updated as spec 10 describes.
- Every edit that moves a ledger-pinned line or adds a ledger token updates the matching
  row of the identity ledger in the same change.

## Non-Functional Requirements

| Attribute | Target / standard | Verification |
|---|---|---|
| Portability | Bash and Python 3.11+ standard library only; no package installation, no account-setting change; Linux local filesystems verified; macOS is a design target (`fcntl` is available there) that this delivery does not verify, stated as such in `docs/OPTIONAL-FEATURES.md` | Suite A static import check (standard-library modules only) and its Linux run |
| Network and models | No network connection, model or harness CLI invocation by the engine, the launcher, `release-check.sh` or the suites | AC-18; suite A runs the engine with `PATH` fakes for `gh`, `claude`, `codex`, `curl`, `wget` that record calls |
| Data safety | Byte-exact backups verified by SHA-256; atomic per-file replacement with `fsync`; no write through a symbolic link | AC-05, AC-24, AC-25 |
| Privacy | Backups, manifest and journal stay under the user's XDG directories with modes 0600/0700; nothing from them is committed | Suite A mode assertions; RC-08 |
| Determinism | Identical inputs give byte-identical installed bytes and plan JSON apart from paths containing `installation_id`; manifests differ only in `installation_id` | AC-03 (installed bytes, manifests); suite A compares two dry-run plans of one home byte for byte |
| Isolation of tests | Suites use disposable `HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, never the real home | Suite A asserts every write is under its temporary root |
| Performance | N/A — no owner-given target; the 15-minute onboarding figure is a recorded target, not a gate (A-33) | RC-09 |
| Compatibility | Hook receipt versions 1 and 2 and the `install`/`uninstall` output of `install-hooks.sh` unchanged; deployed always-on bytes equal spec 10's contract | `tests/hook-install.sh` passing (its `copy_source` lacks `VERSION`, which is why `VERSION` is optional for the engine; any unavoidable fixture edit follows Existing-check obligations); AC-26 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| Empty `HOME` without `~/.claude` or `~/.codex`, no `--harness` | Exit 3 `no-harness`, nothing written | REQ-20 |
| Maintainer machine deployed by the old sync (no manifest) | Every differing target is `foreign-target`; install exits 1; rerun with `--adopt` backs up and replaces; identical files become `preexisting-identical` | REQ-22, REQ-23 |
| User keeps `~/.claude/CLAUDE.md` as a symbolic link into a dotfiles repository | `symlink-target`; `--adopt` stores the link text and writes a regular file; uninstall restores the link | REQ-36, REQ-29 |
| `~/.claude` itself is a symbolic link | Allowed: deploy roots are resolved once; links below the resolved root → `symlink-in-path` | REQ-36 |
| User edits the installed `CLAUDE.md`, then upgrades | `user-modified`, exit 1; `--adopt` keeps the edited bytes as an adopted-edit backup under `S/adopted-backups/` (reported, never deleted) and replaces | REQ-22, REQ-23 |
| User adds a file inside an installed skill directory | Uninstall removes `SKILL.md` only, keeps the directory, `directory-kept` | REQ-31 |
| Interruption after k writes | Rerun rolls back from the journal to the previous installed state, then installs | REQ-25, REQ-26 |
| A target changed by the user between interruption and rerun | Recovery keeps both versions, exit 4, journal kept | REQ-26 |
| Two installers start together | The second exits 3 `installer-busy` after 5 s | REQ-24 |
| Interruption during uninstall | Rerun rolls forward from the journal steps and completes | REQ-26, REQ-70 |
| `install.sh --harness claude` after a claude+codex install | Codex entries carried over unchanged | REQ-28 |
| Home deployed by an older release still holds `principle-python-standards` | `legacy-target`; removed with backup under `--adopt` when bytes match a released hash | REQ-65 |
| Crash between temporary-file creation and rename | Recovery deletes the journalled temporary file | REQ-26 |
| Profile switch with a begin marker naming another profile than the record | `fragment-markers-invalid`, nothing written | REQ-48 |
| Source file edited during apply | Exit 4 `source-changed` before that write; rerun rolls back | REQ-45 |
| Manifest deleted by the user | Uninstall removes nothing (`no-manifest`); install treats targets as foreign | REQ-34 |
| Manifest with `schema_version` 2 or duplicate keys | Exit 2 `manifest-invalid`, nothing written | REQ-41 |
| Original backup file deleted or altered | `backup-corrupt`, target kept, entry retained | REQ-33 |
| Target owned by another user (shared machine) | `foreign-owner`, not resolvable by `--adopt` | REQ-37 |
| Parent directory not writable | Exit 3 `target-not-writable` at planning | REQ-05 |
| Disk full during backup or write | Before the first target write: exit 3 `io-error`; after: exit 4, journal kept | REQ-25 |
| `jq` or `flock` missing | Hook result `missing-dependency` is recorded in the installation record; install continues | REQ-38, REQ-39 |
| Hook result differs between plan and apply | Always-on content rebuilt with the actual result; info `hook-result-differs` | REQ-38 |
| Generated files stale in the checkout | Exit 3 `generated-files-stale` | REQ-40 |
| Registered project has an in-progress task | Spec 13 rule defers; exit 1 `active-task` unless spec 13's `--force` applies | REQ-42 |
| Profile principle file deleted by the user | `kept-deleted`, not recreated without `--adopt` | REQ-50 |
| Project `AGENTS.md` already holds stack text from the old setup | Left as is; the fragment is appended; duplication is accepted | REQ-47 |
| `CLAUDE.md` with two begin markers | `fragment-markers-invalid`, nothing written | REQ-48 |
| `--profile Bad_Name` or a missing profile | Exit 2 before any write | REQ-52 |
| Project without `.ai/` passed to the profile operation | Exit 3 `project-not-initialized` | REQ-08 |
| Downgrade (older checkout installs over newer) | Same rules as an upgrade | REQ-21 |
| `--dry-run` while a journal exists | Plan includes the recovery steps; nothing written | REQ-18 |
| Release check without a local pattern file | RC-08 `not-verified`, exit 1 | REQ-14 |
| `tests/golden-runs.py` absent (spec 09 not delivered), or the suite exits 3 (09 REQ-35) | RC-07 `not-verified` | REQ-60 |
| Remote setting unreadable (token lacks permission) | Candidate report item `not-verified`; verdict `not ready` | REQ-16, REQ-59 |
| Concurrency of Discovery dry-run with a real run | Dry run reads only; no lock and no state change | REQ-61 |

## Acceptance Criteria

All suites build fixtures in temporary directories with isolated `HOME` and XDG variables
and copy the needed source subset; "tree snapshot" means the sorted list of every path under
the temporary root with type, mode, size, mtime and content hash. Criteria marked
**release gate** depend on an owner action; they are not part of the implementation's
acceptance and stay open until the owner acts.

- **AC-01** (REQ-01, REQ-02) — Given `docs/OPTIONAL-FEATURES.md` and
  `docs/examples/flat-task/`, When suite B runs, Then the header row is exact, each of the nine
  required features has exactly one row, every `State` is in the vocabulary, every evidence
  path of a `delivered`/`partial` row exists, every `planned` row's `Enable` is `not
  available`, every money-figure line in scope has a cost basis label, and every `Duration`,
  `Tokens` and `Cost` cell of `run-log-summary.md` is `unknown`; and each mutation — a
  `planned` row with other `Enable` text, an unlabelled `$5` line, a `0` cost cell — makes
  suite B fail naming the file.
- **AC-02** (REQ-03, REQ-30, REQ-70) — Given an install into an empty fixture home with
  `--harness claude --harness codex`, after which the user edits one installed `SKILL.md` and
  the installed `~/.codex/AGENTS.md`, When `install.sh --uninstall` runs, Then both edited
  files are byte-identical to the edits, standard error has two `user-modified` lines, the
  exit code is 1, every other installed file target is gone, and the manifest retains exactly
  the two edited files (`retained: "user-modified"`) plus the created directories that still
  contain them (`retained: "directory-kept"`).
- **AC-03** (REQ-04, REQ-64) — Given two identical empty fixture homes A and B and one fixture
  source with a stubbed validator, When `install.sh --harness claude --harness codex` runs in
  A and `sync.sh --from <source>` in B, Then the trees under both homes are identical in
  relative paths, types, modes and bytes, the two manifests are equal after replacing
  `installation_id` and the home prefix, a second run of each changes no byte, and a stubbed
  validator exiting 1 makes `sync.sh` exit non-zero with no file under B's home created.
- **AC-04** (REQ-05) — Given a fixture home with a foreign `~/.claude/CLAUDE.md`, an owned
  modified skill file, one orphaned owned entry and a hook settings file, When
  `install.sh --dry-run --adopt` prints a plan and then `install.sh --adopt` runs, Then the set
  of non-directory paths whose existence or content identity changed, plus the directories
  created or removed, equals the plan's entries with action other than `unchanged` and `keep`,
  its `bookkeeping` paths (including both locks) and its `delegated` settings, receipt and
  lock paths (directory mtimes are not compared); and the dry run left the snapshot identical.
- **AC-05** (REQ-06, REQ-25, REQ-26, REQ-27) — Given a user `CLAUDE.md` with mode 0640, When
  version 1 is installed with `--adopt`, version 2 (a fixture source in which three existing
  workflow files have new bytes, so its plan has at least four `replace` steps including the
  always-on file) is installed, and `--uninstall` runs, Then `CLAUDE.md` equals the user bytes
  with mode 0640; and Given version 1 installed and
  `ORCHESTRAIL_INSTALL_TEST_FAULT=after-write:2` on the version-2 install, When the install
  exits 4 and is re-run without the variable against version 1's source, Then every target
  equals its version-1 bytes, no `.tmp-` file remains, the journal is gone, and the original
  backup file and the entry's `original` field are unchanged from before the version-2
  attempt. "Applied step" counts every journalled target write, removal or restore.
- **AC-06** (REQ-07, REQ-53) — Given the delivered tree, When suite A runs, Then `principles/`
  holds exactly `code-quality.md` and `testing-standards.md`, a stack-term search over them
  has zero matches, `profiles/python-fastapi/principles/python-standards.md`,
  `infra-standards.md` and `context/stack.md` equal the bytes of `principles/python-standards.md`,
  `principles/infra-standards.md` and `templates/stacks/python-fastapi.md` at the parent of the
  moving commit, `templates/stacks/` does not exist, and an install deploys no
  `principle-python-standards` or `principle-infra-standards` skill and no path from
  `profiles/`.
- **AC-07** (REQ-08) — Given a fresh fixture project, When `setup-new-project.sh --profile
  python-fastapi` runs, Then the files created by the profile step are exactly the four
  targets of `profile.json`, `.ai/profile` and one managed region in each of `CLAUDE.md` and
  `AGENTS.md` whose content equals `gen-docs.py --profile python-fastapi` output; and Given a
  second fresh project, When setup runs without `--profile` and with empty standard input,
  Then none of those files or regions exists and the run exits 0.
- **AC-08** (REQ-09, REQ-49, REQ-50) — Given a project with `python-fastapi` applied, When it
  is applied again, Then the project tree snapshot is unchanged except mtimes are not
  compared; When the source changes one profile file and the user edited that file, Then
  the operation exits 1 with `user-modified` and the tree is unchanged; When a fixture profile
  `p2` sharing one target is applied over `python-fastapi`, Then unchanged
  previous-only targets are removed, an edited previous-only target is kept, the shared
  target follows the three-way table, and `.ai/profile` names `p2`.
- **AC-09** (REQ-10, REQ-54) — Given the delivered tree, When the existing validator check
  `test_public_package_overview_and_release_policy` and suite B run, Then the check passes,
  `README.md` has at most 60 lines and the seven links of REQ-10, every relative link target
  of REQ-54's files exists, and `README.md` contains no occurrence of the former repository
  name.
- **AC-10** (REQ-11, REQ-55, REQ-56) — Given `docs/examples/flat-task/`, When suite B runs,
  Then every file of the Example layout exists, `provenance.json` lists every other file once
  with matching SHA-256, every copied file equals its `built_path` in a `build-reference`
  output that suite B builds in a temporary directory with the recorded `date_base` (the
  comparison reads workspace files only, never the run-log store), `run-log-summary.md` rows
  equal the `step`, `subtask`, `outcome` and `tests` values and order of that build's store
  events, `README.md` contains the not-a-model-run statement, no privacy pattern matches, and
  changing one byte of a copied file makes suite B fail naming it.
- **AC-11** (REQ-12) — Given `docs/CONTRIBUTING.md`, When suite B runs, Then the six headings
  appear in order, every backticked path naming a repository file exists, and
  `gen-docs.py --check` exits 0 (the matrix is current and generated).
- **AC-12** (REQ-13, REQ-61, REQ-62) — Given the delivered rules and workflows, When suite B
  runs, Then exactly one file under `rules/` has a `## Dry-run contract` heading, namely
  `rules/contract-dry-run.md` with `load: on-demand`, kind `contract`, no `docs/name-map.json`
  row and at most 700 words, whose seven numbered clauses begin, in
  order, with the bold labels `**Reads.**`, `**No writes.**`, `**Telemetry only.**`,
  `**No execution.**`, `**Report.**`, `**Uncertain.**`, `**No resume state.**`; the Discovery
  orchestrator's and `/bugfix`'s Invocation lines contain `[--dry-run]`; each of those two
  workflows and `workflows/spec-run.md` contain the citation `contract-dry-run → ## Dry-run
  contract`; the Discovery orchestrator's `## Dry-run` section contains the labels
  `Resolved spec`, `Task directory`, `Children`, `Derived analysis`, and `/bugfix`'s contains
  `Task directory`, `Quick-gate verdict`, `Reproduction test`, `Reproduction result`. This
  criterion is a contract check; agent behaviour under a real dry run is not verified
  offline.
- **AC-13** (REQ-14) — Given fixture checkouts where (a) a pattern file is resolved and no
  tracked file matches, (b) a tracked file matches, (c) no pattern file is resolvable, When
  `release-check.sh` runs with the other suites stubbed to exit 0, Then RC-08 is `pass`,
  `fail` and `not-verified` respectively, the exit code is 0, 1 and 1, and in the real tree no
  tracked path's basename is `hygiene-patterns.txt`.
- **AC-14** (REQ-15, REQ-58) — Given the delivered tree, When suite B runs, Then the three
  template files have the front matter, headings and lines of Data Model → Contribution
  templates, and each `docs/analysis/*.ru.md` ends with a provenance line whose blob exists
  (`git cat-file -e`), contains Cyrillic text, and has the same counts of heading lines
  (`^#{1,6} `) and fence lines (`^```) as the translation.
- **AC-15** (REQ-16, REQ-57) — Given `docs/RELEASE-CHECKLIST.md`, When suite B runs, Then it
  has a section `## Onboarding procedure` naming every field of Data Model → Onboarding
  measurement, and RC-11, RC-12
  and RC-13 each have a verification command that uses `gh api` with the `{owner}/{repo}`
  placeholders and none of `-X`, `--method`, `-f`, `-F`, `--input`, and the document states
  the `not-verified` and `blocked` rules; and the first candidate report gives each of them a
  status in the vocabulary with evidence.
- **AC-16** (REQ-17, REQ-59) — Given the first candidate report, When suite B runs, Then it
  lists RC-01–RC-16 once each with a vocabulary status and non-empty evidence, RC-14–RC-16
  are `owner-decision-pending`, the verdict is `ready` exactly when RC-01–RC-15 are `pass`,
  `VERSION` is `0.9.0`, `LICENSE` does not exist, and no tag `v1.0.0` exists.
- **AC-17** (REQ-18) — Given fixture homes (a) empty with `~/.claude`, (b) installed, (c) with an
  interrupted journal, When `install.sh --dry-run`, `install.sh --uninstall --dry-run` and the
  profile operation with `--dry-run` run, Then each prints valid plan JSON and the tree
  snapshot of the temporary root (homes, XDG directories, project) is identical before and
  after, including the absence of `C/install.lock`.
- **AC-18** (REQ-19) — Given a fixture checkout with stubbed suites that record their
  environment and a `PATH` whose `gh`, `claude`, `codex`, `curl` and `wget` append to a record
  file, When `release-check.sh` runs, Then the record file is empty, every stub saw
  `PYTHONDONTWRITEBYTECODE=1`, `git for-each-ref` output and the tree snapshot of the
  checkout are unchanged, and the printed table has rows RC-01–RC-16.
- **AC-19** (REQ-20, REQ-66) — Given an empty fixture home, When `install.sh` runs, Then it exits 3
  with `no-harness` and writes nothing; Given a home with only `~/.claude`, Then only the
  claude targets are created; Given `--harness codex` on that home, Then `~/.codex` and its
  targets are created and no claude target.
- **AC-20** (REQ-22, REQ-23, REQ-03) — Given a home holding a foreign `CLAUDE.md`, When
  `install.sh` runs without `--adopt`, Then it exits 1, prints `foreign-target` for that path
  and the tree snapshot is unchanged; When it runs with `--adopt`, Then `CLAUDE.md` holds the
  always-on bytes, the original backup file's hash equals the user bytes, and the entry's
  `original.state` is `backup`; and a `type-changed` target (a directory at a `SKILL.md` path)
  still exits 1 under `--adopt`.
- **AC-21** (REQ-24) — Given a process holding `flock` on `C/install.lock`, When `install.sh`
  runs, Then it exits 3 with `installer-busy` after the 5-second deadline (the suite allows
  2 further seconds for process start-up) and the tree snapshot is unchanged except the lock
  file's existence.
- **AC-22** (REQ-21, REQ-41, REQ-68) — Given a committed install, When suite A validates the manifest,
  Then it has exactly the documented fields and every entry's installed hash equals its
  target; and Given manifests with a duplicate key, `NaN`, an unknown key and
  `schema_version: 2`, When `install.sh` and `--uninstall` run, Then each exits 2 with
  `manifest-invalid` and writes nothing.
- **AC-23** (REQ-28, REQ-73, REQ-74) — Given an installed fixture source from which one workflow is then
  deleted, When `install.sh` runs, Then that skill's `SKILL.md` and its created directory are
  removed and its entry is gone; Given instead that the user had edited it, Then the install
  exits 1 with `user-modified` and nothing changes, and with `--adopt` the file is kept
  byte-identical, its entry is dropped and `released` is reported; Given an orphaned entry
  with an original backup, Then the original bytes are restored; and Given a claude+codex
  installation, When `install.sh --harness claude` runs, Then every codex entry and target is
  unchanged and the manifest's `harnesses` still lists both.
- **AC-24** (REQ-29, REQ-31, REQ-32, REQ-33, REQ-34, REQ-35, REQ-67) — Given an installed fixture with
  (a) an `absent`-origin file, (b) a `backup`-origin file, (c) a `preexisting-identical` file,
  (d) a skill directory with an added user file, (e) a deleted `backup`-origin target, (f) a
  target replaced by a directory, (g) an altered original backup, and a registered fixture
  project and log store, When `--uninstall` runs, Then (a) is removed, (b) and (e) are
  restored with original bytes and mode, (c) is kept, (d) keeps the directory and the user
  file with `directory-kept`, (f) and (g) are retained with `type-changed` and
  `backup-corrupt`, the exit code is 1, and the project tree, registry and log store
  snapshots are unchanged; and with no manifest the run exits 0 with `no-manifest` and
  changes nothing.
- **AC-25** (REQ-36, REQ-37, REQ-69) — Given (a) a symbolic link at a `SKILL.md` target,
  (b) a symbolic link as a skill directory below the resolved skills root, When `install.sh`
  runs, Then (a) gives `symlink-target` and (b) `symlink-in-path`, exit 1, and the link
  targets' contents are unchanged; with `--adopt`, (a) becomes a regular file and its link
  text is recorded; and Given `ORCHESTRAIL_INSTALL_TEST_FOREIGN_UID=<target path>` (a
  test-only variable that makes the engine treat that path as owned by another user ID and
  can only add conflicts), Then the run exits 1 with `foreign-owner` even under `--adopt`.
- **AC-26** (REQ-38, REQ-39) — Given a fixture with `hooks.json` for claude only, When
  `install.sh --dry-run` runs, Then the plan's `delegated` record equals the mapping (Data
  Model → Plan) of the output of `install-hooks.sh plan install`, also when `jq` is absent
  from `PATH` (unavailable output), and that command left the snapshot unchanged; When the
  install runs, Then `~/.claude/CLAUDE.md` equals the bytes of `harness/claude/always-on.md`
  followed by `\n## Current hook installation\n\ninstallation-result: ` + the hook result +
  `\n`, `~/.codex/AGENTS.md` uses `{"reason":"no-native-adapter","status":"unavailable"}`, and
  `settings.json` and the hook receipt are byte-identical to those produced in a twin home by
  `install-hooks.sh install --from <source>` alone.
- **AC-27** (REQ-40) — Given a fixture source whose generated file differs from the generator's
  output, When `install.sh` and `install.sh --dry-run` run, Then both exit 3 with
  `generated-files-stale` and write nothing.
- **AC-28** (REQ-42) — Given a registered fixture project with a task phase `in-progress` as
  spec 13 defines it, When `install.sh` runs on a home where a target would change, Then it
  exits 1 with `active-task` and writes nothing; and with `--force`, Then the outcome is the
  one spec 13 prescribes for `--force`.
- **AC-29** (REQ-43, REQ-71) — Given a fixture home deployed by spec 13's engine (deploy
  manifests for claude and codex, each skill and always-on object at its recorded digest
  except one skill the user edited), When `install.sh` runs, Then every unchanged object is
  classified `owned` with `original.state` `migrated`, the edited skill gives `user-modified`
  and exit 1, and nothing is written; When it runs with `--adopt`, Then the manifest holds an
  entry per object and `C/deploy/claude.json` and `C/deploy/codex.json` no longer exist; and
  `scripts/deploy-skills.py deploy` exits 2 (unknown subcommand) while `deployment-set`
  prints the documented JSON and leaves the snapshot unchanged.
- **AC-30** (REQ-44, REQ-45) — Given each exit-2 and exit-3 condition of the exit-code table
  reproducible in a fixture, When the engine runs, Then the exit code and diagnostic code
  match the table and every diagnostic line matches `^install: [a-z-]+: (-|/.+): .+$`; and
  Given a source file modified by a test hook between planning and its write, Then the run
  exits 4 with `source-changed`, the journal remains, and a re-run restores the previous
  installed state; and Given a target modified the same way, Then the run exits 4 with
  `target-changed` and the modified bytes are kept.
- **AC-31** (REQ-46, REQ-52) — Given profile manifests violating each rule of Data Model →
  Profile manifest, and `--profile Bad_Name` and `--profile missing`, When setup runs, Then
  each exits 2 (`profile-invalid`, `usage`, `profile-not-found`) and the project snapshot is
  unchanged.
- **AC-32** (REQ-47, REQ-48) — Given `AGENTS.md` with user text before and after an existing
  region, When the profile is re-applied with a new fragment, Then only the region content
  changes and all bytes outside it are identical; and Given files with two begin markers, a
  begin without end, and an end before begin, Then each gives `fragment-markers-invalid` and
  the file is unchanged.
- **AC-33** (REQ-51) — Given a project with `.ai/profile` for `python-fastapi`, When setup runs
  without `--profile` and with empty standard input, Then it exits 0, the profile files,
  regions and record are unchanged, and its standard output contains no stack question.
- **AC-34** (REQ-57) **release gate** — Given a person who performs the onboarding procedure
  of `docs/RELEASE-CHECKLIST.md` in a fresh environment with a stopwatch, When suite B runs
  afterwards, Then one onboarding measurement record exists whose `Candidate commit` is an
  ancestor of `HEAD`, every field is non-empty, and `Target 15 minutes` is `met` or `not met`
  with a cause. The implementation's part is the procedure text in the checklist (AC-15) and
  suite B's validator for the record, tested on a synthetic record fixture.
- **AC-35** (REQ-60) — Given a fixture checkout where every automated item's command is stubbed
  to exit 0, When `release-check.sh` runs, Then it exits 0 and prints RC-01–RC-08 as `pass`,
  RC-09 and RC-11–RC-13 as `not-verified`, and RC-10 and RC-14–RC-16 as
  `owner-decision-pending`; with RC-03's command stubbed to exit 1, Then RC-03 is `fail`,
  the remaining items still run, and the exit code is 1.
- **AC-36** (REQ-63) — Given `docs/USAGE.md`, When suite B and the existing check
  `test_public_setup_guide_uses_orchestrail_release_instructions` run, Then the check passes,
  section 4 contains `scripts/install.sh --dry-run`, `--adopt` and `--uninstall`, section 5
  contains `--profile`, section 8 contains `scripts/install.sh`, and sections 1, 2 and 9 do
  not name `python-standards.md` or `infra-standards.md` outside a sentence that also names
  the `python-fastapi` profile.
- **AC-37** (REQ-17, REQ-72) **release gate** — Given the copyright-holder wording the owner
  supplied at the gate (after confirming that no third party holds rights, D-01) and an
  explicit authorization naming a version, When the release sequence of REQ-72 runs, Then
  the release-preparation commit holds `LICENSE` (Apache License 2.0 with that wording and no
  placeholder token), the
  new `VERSION`, the post-release tag text in `docs/USAGE.md` section 4 and the updated bodies
  of the checks listed in REQ-72, `scripts/validate-contracts.sh` passes on it, a fresh
  `release-check.sh` on it reports RC-01–RC-08 `pass`, and its candidate report shows RC-14 and
  RC-15 `pass`.

- **AC-38** (REQ-26, REQ-67, REQ-70, REQ-78) — Given an installation with a `backup`-origin target,
  an `absent`-origin target and a third owned file, When `--uninstall` runs with
  `ORCHESTRAIL_INSTALL_TEST_FAULT=after-write:1` and exits 4, and `--uninstall` is re-run
  without the variable, Then the `backup`-origin target holds its original bytes, the other
  two are removed, the manifest and journal are gone, and the re-run exits 0; Given the fault
  placed after the last target step (before the journalled hook step), Then the re-run runs
  `install-hooks.sh uninstall` and the owned hook entries are gone from `settings.json`; and
  Given a `backup`-origin target deleted by the user before uninstall, Then it is restored.
- **AC-39** (REQ-65, REQ-75, REQ-76, REQ-77) — Given a fixture home holding `principle-python-standards/SKILL.md` with
  bytes of a listed released hash and `principle-infra-standards/SKILL.md` with other bytes,
  and no manifest, When `install.sh` runs, Then both are reported (`legacy-target`,
  `legacy-target-modified`) and unchanged; When `install.sh --adopt` runs, Then the first is
  removed with an original backup and an entry `installed: {"removed": true}`, the second is
  unchanged; When `install.sh` runs again, Then the removed path stays absent and its entry
  unchanged; and When `--uninstall` runs, Then the first is restored byte-identical.
- **AC-40** (REQ-66, REQ-20) — Given a home with only `~/.claude`, When
  `install.sh --harness codex` runs, Then `~/.codex` and its skills directory are created and
  recorded as `directory` entries with `created: true`, no claude target is written, and
  `--uninstall` afterwards removes `~/.codex` when it is empty.
- **AC-41** (REQ-79) — Given a fixture home whose `skills_dir` holds the directories
  `pae-tests` and `rule-tdd` (names spec 13's name map lists as leftovers) with no manifest
  entry, and a fixture source whose `deployment-set` reports them as `leftover_candidates`,
  When `install.sh` runs twice, Then each run prints one `leftover <dir> (not removed; review,
  then remove it manually)` line per directory, the directories are byte-for-byte unchanged,
  the exit code is not changed by them, and `install.sh --dry-run` lists both in the plan's
  `leftover` field; and Given a candidate that equals a manifest entry's path, Then it is not
  reported.
- **AC-42** (REQ-80) — Given a fixture home, a registry and held locks, When `install.sh`,
  `install.sh --uninstall` and `deploy-skills.py project-pass` run, Then the registry bytes are
  unchanged, neither `C/install.lock` nor `C/deploy.lock` is deleted or replaced while another
  process holds an `flock` on it (the installer exits 3 `installer-busy`; `project-pass`
  exits 1 with spec 13's `deploy-locked`), and in a registered
  project holding `.ai/profile` and a managed fragment `project-pass` leaves every profile
  file and record byte-identical.

- **AC-43** (REQ-81, REQ-16) — Given the delivered tree, When suite B runs, Then
  `.github/workflows/offline-checks.yml` exists with one job `offline-checks`, the jobs
  `offline-checks` (triggers `pull_request` and `push`) and `full-validator` (trigger `schedule`
  only, running the command of RC-02), read-only permissions, and none of the strings `secrets.`,
  `pull_request_target`, `workflow_dispatch`, `claude ` and `codex ` as a command; the steps of `offline-checks`
  contain, in order, the commands of RC-03–RC-06 and a `golden-runs.py` step guarded by
  `[ -f tests/golden-runs.py ]`, a full-history checkout, `MISE_PYTHON_VERSION=3.12.16` and a
  `pytest` install; and `docs/RELEASE-CHECKLIST.md` states the RC-13 rule of REQ-16 naming the
  check `offline-checks`. Given a fixture checkout without `tests/golden-runs.py`, When the
  guarded step's shell text runs, Then it exits 0 and prints the notice; Given a fixture whose
  stubbed suite exits 3, Then the step exits non-zero. The checks are textual (the standard
  library has no YAML parser); a hosted run of the workflow is not required for acceptance.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-01 |
| REQ-03 | AC-02, AC-20 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-06 | AC-05 |
| REQ-07 | AC-06 |
| REQ-08 | AC-07 |
| REQ-09 | AC-08 |
| REQ-10 | AC-09 |
| REQ-11 | AC-10 |
| REQ-12 | AC-11 |
| REQ-13 | AC-12 |
| REQ-14 | AC-13 |
| REQ-15 | AC-14 |
| REQ-16 | AC-15, AC-43 |
| REQ-17 | AC-16, AC-37 |
| REQ-18 | AC-17 |
| REQ-19 | AC-18 |
| REQ-20 | AC-19, AC-40 |
| REQ-21 | AC-22 |
| REQ-22 | AC-20 |
| REQ-23 | AC-20 |
| REQ-24 | AC-21 |
| REQ-25 | AC-05 |
| REQ-26 | AC-05, AC-38 |
| REQ-27 | AC-05 |
| REQ-28 | AC-23 |
| REQ-29 | AC-24 |
| REQ-30 | AC-02 |
| REQ-31 | AC-24 |
| REQ-32 | AC-24 |
| REQ-33 | AC-24 |
| REQ-34 | AC-24 |
| REQ-35 | AC-24 |
| REQ-36 | AC-25 |
| REQ-37 | AC-25 |
| REQ-38 | AC-26 |
| REQ-39 | AC-26 |
| REQ-40 | AC-27 |
| REQ-41 | AC-22 |
| REQ-42 | AC-28 |
| REQ-43 | AC-29 |
| REQ-44 | AC-30 |
| REQ-45 | AC-30 |
| REQ-46 | AC-31 |
| REQ-47 | AC-32 |
| REQ-48 | AC-32 |
| REQ-49 | AC-08 |
| REQ-50 | AC-08 |
| REQ-51 | AC-33 |
| REQ-52 | AC-31 |
| REQ-53 | AC-06 |
| REQ-54 | AC-09 |
| REQ-55 | AC-10 |
| REQ-56 | AC-10 |
| REQ-57 | AC-15, AC-34 |
| REQ-58 | AC-14 |
| REQ-59 | AC-16 |
| REQ-60 | AC-35 |
| REQ-61 | AC-12 |
| REQ-62 | AC-12 |
| REQ-63 | AC-36 |
| REQ-64 | AC-03 |
| REQ-65 | AC-39 |
| REQ-66 | AC-19, AC-40 |
| REQ-67 | AC-24, AC-38 |
| REQ-68 | AC-22 |
| REQ-69 | AC-25 |
| REQ-70 | AC-02, AC-38 |
| REQ-71 | AC-29 |
| REQ-72 | AC-37 |
| REQ-73 | AC-23 |
| REQ-74 | AC-23 |
| REQ-75 | AC-39 |
| REQ-76 | AC-39 |
| REQ-77 | AC-39 |
| REQ-78 | AC-38 |
| REQ-79 | AC-41 |
| REQ-80 | AC-42 |
| REQ-81 | AC-43 |

Every AC names at least one REQ; AC-34 and AC-37 are release gates outside implementation acceptance.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Users' personal global instruction files are replaced (with backup) | Lost personal instructions in sessions until restored | Medium | Conflict without `--adopt`; README and USAGE explain the backup and uninstall |
| Homes deployed before spec 13's engine have no manifest | First sync stops with `foreign-target` conflicts | Medium | Documented one-time `sync.sh --adopt`; identical files adopted without backup; homes deployed by spec 13 migrate without conflicts (REQ-43) |
| Spec 13's delivered engine differs from its spec text | The `deployment-set` contract or DM-6 mapping needs adjustment | Medium | Discovery of Part A verifies DM-6 and the engine at the delivered revision; changes are recorded in the Part A ADR |
| Migrated always-on files have no original backup | Uninstall removes `CLAUDE.md`/`AGENTS.md` without restoring earlier user content | Medium | Info `no-original`; the earlier content was already overwritten by sync and spec 13's adopt |
| Frozen validator and source guard | Implementation blocked by fingerprint failures | High | Standalone suites; re-pinning procedure; no new `check` lines |
| Identity ledger line pins | Validator fails after USAGE or analysis edits | High | Append-only provenance lines; ledger rows updated in the same change |
| Publishing the `flat` reference result | Later experiments on `flat` may be contaminated | Low | Spec 09 treats `flat` as `tuning` (`published: true`; a holdout task on it is rejected, its REQ-50) |
| Full validator takes 34–52 minutes (`.ai/context/runbook.md:26`) | Slow release check | High | Accepted; release check runs once per candidate |
| `flock` binary absent on macOS | Hook installation unavailable there | Medium | Recorded in the installation record and OPTIONAL-FEATURES; engine uses `fcntl` |
| Scope larger than eight subtasks | One task overruns review capacity | High | Split boundary A/B (Notes) |
| Dry-run behaviour of agents is untestable offline | A workflow could still write | Medium | Contract check (AC-12); a golden case can cover it later (spec 09) |

## Assumptions

- A-01 | Language | Resolved: English spec; the Russian text stays in history at `060ce6d`, translated under Source | Source: `rules/language.md`; `.ai/principles/coding.md:11` | Reversible: yes
- A-02 | Location of `install.sh` | Resolved: `scripts/install.sh`, not the repository root | Source: `scripts/README.md:3` ("All executable shell helpers live in this directory"); `.ai/principles/coding.md:83-85` | Reversible: yes
- A-03 | Engine language | Resolved: Python 3.11+ standard library, run as `python3 -I`, Bash launcher with a version guard | Source: `scripts/install-hooks.sh:45-51` and `.ai/memory/architecture.md:87` (Python installer engine precedent); `.ai/context/runbook.md:41-43`. ADR-0009 Decision 6 (`:243-244`) names bash for `sync.sh`/`setup-*` and Python for optional tools; the launcher and `sync.sh` stay Bash, and the Python engine follows the delivered hook installer's precedent — a deviation recorded in the Part A ADR | Reversible: yes
- A-04 | Bookkeeping locations | Resolved: manifest, journal and lock under `C`; backups under `S` | Source: `scripts/install-hooks.py:656-659`; `hooks/log-step-hook.sh:16`; `.ai/context/environment.md:49` | Reversible: yes (ADR at delivery)
- A-05 | Which harnesses an install targets | Resolved: auto-detect by parent of `always_on_path`; `--harness` explicit; sync passes every harness | Source: best practice (no unrequested directories in a user's home); `scripts/sync.sh:71`, `:134` create directories today | Reversible: yes
- A-06 | Partial installs | Resolved: any conflict stops the whole install before writing | Source: original §4.3 step 2 (show the difference before a decision); best practice (a partial skill set is a broken install) | Reversible: yes
- A-07 | Decision mechanism for foreign or modified targets | Resolved: one `--adopt` flag; it never resolves `type-changed`, `foreign-owner`, `symlink-in-path`, `backup-corrupt` | Source: original §4.3 last paragraph (`--force` does not cancel ownership protection); ADR-0009 Decision 6 (`CLAUDE.md` backup) | Reversible: yes (ADR at delivery)
- A-08 | Foreign files identical to the installed bytes | Resolved: adopted without backup, kept at uninstall | Source: original §4.1 (absence of a manifest does not prove ownership) | Reversible: yes
- A-09 | Lifetime of previous-state backups | Resolved: only until the operation commits | Source: original §4.2 (rollback of a failed update); best practice (smallest retained data) | Reversible: yes
- A-10 | Recovery direction | Resolved: install rolls back, uninstall rolls forward | Source: original §4.3 step 7 and §8 | Reversible: yes
- A-11 | Hook settings in the plan | Resolved: new read-only `plan` operation of the hook installer; hooks are not rolled back | Source: original §4.2 last paragraph; `scripts/install-hooks.py:582-599` already computes the update without writing | Reversible: yes
- A-12 | Stale generated files | Resolved: the engine runs `gen-docs.py --check` itself | Source: spec 10 Goal ("deployment refuses to proceed while any derived file is stale") | Reversible: yes
- A-13 | Active tasks | Resolved: consume spec 13 REQ-43 through `deployment-set`'s `active` list; `--force` has only its meaning | Source: spec 13 REQ-09, REQ-43 | Reversible: yes
- A-14 | Overlap with spec 13's `deploy-skills.py` (DM-6 manifests, DM-7 journal and lock, global writes) | Resolved: `install.py` becomes the only global writer; `deploy-skills.py deploy` is removed and replaced by read-only `deployment-set` and `project-pass`; DM-6 manifests are migrated and deleted (REQ-43, REQ-71) | Source: ADR-0009 Decision 1 Consequences and Decision 6 (installer belongs to 11); spec 13 A-31 and Notes → Relationship to spec 11 (its Q-05 is resolved; its list of preserved contracts is mapped to requirements under Contracts → Relationship to spec 13's deployment engine) | Reversible: yes (ADR at delivery)
- A-15 | Exit codes | Resolved: 0/1/2/3 aligned with spec 10's family, plus 4 for incomplete | Source: spec 10 Contracts → Stages and exit codes; best practice | Reversible: yes
- A-16 | Interruption testing | Resolved: test-only fault variable that can only stop a run | Source: `.ai/memory/architecture.md:88` (git-rails test-only seam that can only deny) | Reversible: yes
- A-17 | Profile layout and target names | Resolved: `profile.json`; targets under `.ai/principles/` and `.ai/context/stack-python-fastapi.md` | Source: ADR-0009 Decision 6 (`:225-229`); original §5 (name fixed in the manifest) | Reversible: yes
- A-18 | Profile name grammar | Resolved: `^[a-z0-9]+(-[a-z0-9]+)*$` | Source: spec 10 REQ-43 | Reversible: yes
- A-19 | Marker wording | Resolved: neutral `BEGIN/END MANAGED PROFILE` markers without the product name | Source: `.ai/principles/architecture.md` P8 | Reversible: yes
- A-20 | Profile conflict handling | Resolved: all-or-nothing with `--adopt`; deleted files stay deleted | Source: A-06 consistency; best practice (respect a user's deletion) | Reversible: yes
- A-21 | Profile upgrades in registered projects | Resolved: only by re-running setup with `--profile`; sync and install never touch project profiles | Source: ADR-0009 Decision 6 (setup copies profiles); smallest choice | Reversible: yes
- A-22 | Interactive stack prompt | Resolved: removed | Source: original REQ-08 (explicit `--profile`); ADR-0009 Decision 6 | Reversible: yes
- A-23 | What "neutral" means for the two core files | Resolved: no stack term anywhere in `principles/*.md`; stack-specific examples rewritten as language-neutral `text` pseudocode, originals moved verbatim to `profiles/python-fastapi/principles/code-examples.md` | Source: original §5 ("stack examples are allowed in an explicitly chosen profile"); REQ-07 | Reversible: yes
- A-24 | README length | Resolved: at most 60 lines | Source: `scripts/validate-contracts.sh:4618` (existing, frozen expression) is stricter than and satisfies original REQ-10's 120 | Reversible: yes
- A-25 | Clone URL in README | Resolved: not in README; link to USAGE section 4 | Source: identity ledger (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:184-214`) | Reversible: yes
- A-26 | `CONTRIBUTING.md` location | Resolved: `docs/CONTRIBUTING.md` | Source: `.ai/principles/coding.md:80` (guides in `docs/`), `:83-85` (root holds only listed files) | Reversible: yes
- A-27 | Russian originals (ADR-0009 Decision 6 "kept alongside" vs `rules/language.md`) | Resolved: originals stay byte-exact in history at pinned blobs; each translation names its blob; no Russian text is written to the tree; names keep `.ru.md` | Source: `rules/language.md` and `.ai/principles/coding.md:11` (principles precede ADRs); delivered state `docs/README.md:26`, `:28`; ledger and legend checks pin the names | Reversible: yes (Q-02 resolved 2026-11-14: owner accepted, D-02; ADR at delivery)
- A-28 | CI for required status checks | Resolved 2026-11-14 (supersedes the earlier "not created"): this spec creates one offline workflow, REQ-81, Part B; RC-13 is `blocked` only while the workflow or the required-check setting is missing | Source: owner decision D-03 (Q-03); spec 09 Out of Scope and A-24 (that spec creates none); G6 | Reversible: yes
- A-29 | Example source | Resolved: spec 09 `flat` reference workspace for `spec-run`, labelled as not a model run | Source: original REQ-11; spec 09 DM-1; `.ai/specs/README.md` → "Shared acceptance gates" (G6, no paid runs) | Reversible: yes
- A-30 | Test location | Resolved: standalone `scripts/check-install.py` and `scripts/check-public-readiness.py`, not registered in the validator | Source: ADR-0019 Decision 3; spec 10 Scope item 8 | Reversible: yes
- A-31 | Validator edits | Resolved: bodies only, outside the pinned region, expressions untouched, then re-pin | Source: `tests/fixtures/validator-runtime/oracle.py:160-252`; ADR-0020 Decision 2 | Reversible: yes
- A-32 | Remote-setting verification | Resolved: manual items with read-only commands; `release-check.sh` stays offline | Source: original REQ-03, REQ-16; G6 | Reversible: yes
- A-33 | 15-minute onboarding target | Resolved: measured and recorded as `met`/`not met`; not a pass/fail gate of this spec | Source: original §1 ("target") and §6 (record blocking dependencies) | Reversible: yes
- A-34 | Optional-feature document | Resolved: `docs/OPTIONAL-FEATURES.md` with nine required rows | Source: `.ai/principles/coding.md:80`; original §6 paragraph 3 | Reversible: yes
- A-35 | Cost vocabulary | Resolved: five labels | Source: original REQ-02; `.ai/specs/README.md` → "Shared acceptance gates" (G8) | Reversible: yes
- A-36 | Where the dry-run contract lives | Resolved: a new on-demand rule `rules/contract-dry-run.md`, not an always-on rule; telemetry exception as in `/spec-run` | Source: P6 (`.ai/principles/architecture.md`, one canonical statement; finite always-on budget); spec 13 rule kinds (ADR-0009 Decision 3); `workflows/spec-run.md:10-11`, `:50-51` | Reversible: yes
- A-37 | Feature size | Resolved: two parts with an explicit boundary | Source: readiness check 13; original §8 order | Reversible: yes
- A-38 | Project skill links after uninstall | Resolved: left untouched (they belong to projects; spec 13's pass removes broken links) | Source: REQ-35; `scripts/sync.sh:226-239` | Reversible: yes
- A-39 | Platform | Resolved: Linux and macOS local filesystems | Source: `scripts/install-hooks.py:16` (`fcntl`); spec 10 Non-Functional Requirements | Reversible: yes
- A-40 | Installed and backup modes | Resolved: installed files 0644; bookkeeping 0600/0700; restore uses the recorded mode | Source: best practice | Reversible: yes
- A-41 | Old repository URLs in this spec | Resolved: replaced by repository paths and the pinned commit; the identity-ledger row for this file (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:209`) must be removed in the change that commits this revision — a shared-file edit outside this refinement, listed under Notes → Follow-up | Source: precedent of the 2026-11-13 state-tool refinement (`.ai/memory/progress.md:128`) | Reversible: yes
- A-42 | Which command reports leftover skills after `deploy` is removed (2026-11-14) | Resolved: the installer, on `install` and `--dry-run` (REQ-79), fed by `deployment-set`'s `leftover_candidates`; not an additional `deploy-skills.py` subcommand, so that REQ-71's subcommand set and the public installer's output stay the single place a user sees the lines | Source: spec 13 REQ-57 and Notes → Relationship to spec 11 (leftover reporting must survive `deploy`); spec 13 Terminology → Leftover skill | Reversible: yes
- A-43 | Copyright holder and third-party rights (2026-11-14) | Resolved: the implementer never chooses a holder; the holder line is supplied by the owner at the REQ-72 gate, after the owner confirms no third party holds rights (D-01) | Source: owner decision D-01 (Q-01); ADR-0009 Decision 1 | Reversible: no once published under a licence
- A-44 | What the CI workflow must set up (2026-11-14) | Resolved: REQ-81 lists it from the repository's runbook and spec 09 REQ-35 (the validator is run with bash); no matrix, cache or numeric time limit is specified, and the full validator's long runtime (runbook → Commands) is handled by D-04: it runs in a scheduled job, not in the required check | Source: `.ai/context/runbook.md → Commands`; `scripts/validate-contracts.sh` (run with bash); spec 09 REQ-35 | Reversible: yes

## Decisions

Owner decisions of 2026-11-14 (the refinement itself ran in autonomous mode; these three answered Q-01–Q-03):

- D-01 | The copyright holder is whoever legally owns the code, by default the owner personally under the name in the repository's git authorship; the owner first confirms that no employer or other third party holds rights; the holder line is supplied by the owner at the REQ-72 release gate, never invented by the implementer | Overrides: none | Rationale: a legal question, not a technical one; rights cannot be repaired after publication under a licence | Follow-up: REQ-72, AC-37, A-43; RC-14 stays owner-gated
- D-02 | The Russian originals stay only in git history; each English translation ends with a line naming the original's pinned commit and blob; Russian text does not return to the tree | Overrides: ADR-0009 Decision 6, literal wording ("Russian originals kept with English translations alongside") | Rationale: the language rule forbids non-English text in project files, and a pinned reference keeps the original recoverable | Follow-up: an ADR, or a note appended through the ADR process, records the departure from ADR-0009 Decision 6 (Part B delivery record, Notes); REQ-58 and A-27 unchanged
- D-03 | Spec 11, Part B, creates the CI that required status checks need, as an explicit requirement and not a separate spec; minimum: one offline workflow running the validator and the standalone offline suites, no paid run, no secrets | Overrides: A-28 as first written, and the earlier Out of Scope entry that no spec owns CI (spec 09 keeps its own exclusion) | Rationale: a required status check needs a workflow that produces it, and gate G6 forbids paid runs in default CI | Follow-up: REQ-81, AC-43, RC-13 and REQ-16 updated; spec 09's Out of Scope and A-24 wording should cite REQ-81 (Notes)
- D-04 | The required check `offline-checks` runs the fast offline subset (RC-03–RC-06 and the guarded golden-run suite); the full validator (RC-02) runs in the scheduled job `full-validator` of the same workflow and in the release checklist | Overrides: REQ-81 and A-44 as first written (full validator inside the required check) | Rationale: the full validator takes 34–52 minutes, too slow for every pull request; a weekly full run plus the release gate keeps it enforced | Follow-up: REQ-81, AC-43, A-44 updated; RC-02 stays a release-candidate item

## Clarifications

Autonomous refinement: no questions were asked before 2026-11-14.

### Session 2026-11-14

- Q: What exact copyright-holder wording does the owner want in `LICENSE` (Q-01)? → A: The holder is whoever legally owns the code, by default the owner personally under the name in the repository's git authorship; the owner first confirms that no employer or other third party holds rights (D-01).
- Q: Does the owner accept keeping the Russian originals only in history at pinned blobs (Q-02)? → A: Yes; each translation ends with a line naming the original's commit and blob, and the Russian text does not return to the tree; this departs from the literal wording of ADR-0009 Decision 6 and is recorded by an ADR or an ADR-process note (D-02).
- Q: Which specification creates the CI that required status checks need (Q-03)? → A: This spec, Part B, as REQ-81, with no separate spec; offline only, no paid run, no secrets (D-03).

## Open Questions

- Q-01 | non-blocker | What exact copyright-holder wording does the owner want in `LICENSE`?
  Impact: RC-14 and AC-37 stay open; implementation proceeds (ADR-0009 Decision 1; spec 01
  Change Log). Resolved 2026-11-14: the holder is whoever legally owns the code, by default
  the owner personally under the name in the repository's git authorship, after the owner
  confirms that no third party holds rights; the owner supplies the holder line at the
  REQ-72 gate (D-01). RC-14 and AC-37 remain owner gates.
- Q-02 | non-blocker | Does the owner accept keeping the Russian originals in history at
  pinned blobs (A-27) instead of restoring them beside the translations? Impact: if not,
  two files are restored and the identity ledger, legend check and language rule need an
  exception. Resolved 2026-11-14: accepted; originals stay only in history, each translation
  names the pinned commit and blob; an ADR or ADR-process note records the departure from
  ADR-0009 Decision 6 (D-02).
- Q-03 | non-blocker | Which specification owns CI configuration for required status checks?
  Impact: RC-13 is `blocked` until one exists. Resolved 2026-11-14: this spec, Part B, REQ-81
  (D-03); RC-13 becomes satisfiable once the owner requires the `offline-checks` status check.
- Q-04 | resolved 2026-11-13 | Spec 13 now specifies `scripts/deploy-skills.py`, DM-6 deploy
  manifests and DM-7 journal and lock; the mapping is under Contracts → Relationship to spec
  13's deployment engine. Discovery of Part A re-verifies it against the delivered spec 13.
- Q-05 | non-blocker | Should the roadmap index list Part A and Part B as separate entries
  (11 and 11b)? Impact: Discovery runs two tasks either way.
- Q-06 | non-blocker (external precondition owned by spec 13) | The frozen checks that pin
  the text of `scripts/sync.sh` and `scripts/setup-new-project.sh`
  (`scripts/validate-contracts.sh:953-957`, `:1166-1179`, `:1293-1320`, as spec 13 re-points
  them for its own sync and setup) must be re-pointed before REQ-04 and REQ-61 can pass.
  Spec 13 is final and defines the mechanism: `tests/fixtures/validator-runtime/inventory-amendment.json`
  with `"schema": 2` and the lists `path_changes` and `contract_changes` (its DM-9; REQ-51
  and REQ-52; A-02). What this spec needs amended is exactly the checks that, once spec 13
  is delivered, assert text this spec changes: in `sync.sh`, the separate hook-installation
  step and the `deploy-skills.py deploy --hook-result` step (replaced by the launcher call and
  `project-pass`, REQ-04, REQ-64, REQ-71); in `setup-new-project.sh`, the interactive stack
  prompt and standards injection (replaced by `--profile`, REQ-08, REQ-51); and any check
  that names a rule file literally in either script if spec 13's delivery still leaves one
  (REQ-61 adds `rules/contract-dry-run.md`). Part A's Discovery lists them by running the
  oracle against the delivered spec 13. These changes are semantic, so they are
  `contract_changes` entries, not `path_changes` (which spec 13's mask accepts only for
  name-only differences). The precondition is met by spec 13's text for the mechanism but
  not for these entries: the closed set of `requirement` values (spec 13's own REQ-05, REQ-06,
  REQ-09, REQ-10, REQ-11, REQ-12, REQ-14, REQ-15, REQ-23, REQ-36, REQ-55, REQ-66) is
  hard-coded in the oracle test and cannot name a requirement of this spec, and each entry also needs a
  verdict row in the `## Superseded checks` table of spec 13's DM-20 record. Impact: Part A
  extends the closed set under spec 13 REQ-69 with values of the form `spec-11 REQ-NN` in
  `tests/validator-runtime-oracle.py` (updating `AMENDMENT_SHA256` and the source-guard records), appends its entries and their DM-20 rows, and states it in
  the Part A ADR; if spec 13 is delivered without DM-9 schema 2, Discovery stops.

## Notes

- **Preconditions (checked at Discovery):** Part A needs spec 13 (`deploy.env`, installed-name
  map, active-task rule, retired Windsurf targets; the active-task rule is delivered in `deploy-skills.py`
  (spec 13 REQ-43, DM-8) and consumed through `deployment-set`;
  and the checks listed under Context → Constraints that pin sync and setup text have been
  retired or rewritten through an accepted inventory change, Q-06; spec 13 DM-9) and spec 10 (`gen-docs.py --check`,
  `--profile`, generated `harness/<name>/always-on.md`, sync deployment contract). Part B
  needs Part A, spec 10 (`docs/reference/`, `docs/harness-matrix.md`) and spec 09 (`flat`
  reference workspace, offline suite, `docs/GOLDEN-RUNS.md`). Missing → Discovery stops.
- **Split boundary.** Part A = REQ-03–REQ-09, REQ-18, REQ-20–REQ-53, REQ-64–REQ-71,
  REQ-73–REQ-80 (AC-02–AC-08, AC-17, AC-19–AC-33, AC-38–AC-42). Part B = REQ-01, REQ-02, REQ-10–REQ-17, REQ-19,
  REQ-54–REQ-63, REQ-72, REQ-81 (AC-01, AC-09–AC-16, AC-18, AC-34–AC-37, AC-43). Part B starts after Part A is
  reviewed.
- Hint (nonbinding): Part A subtasks — (1) manifest, plan and classification with suite A
  fixtures; (2) apply, journal, recovery and fault seam; (3) uninstall; (4) hook plan
  operation, launcher and sync delegation with source-guard re-pinning; (5) neutral core and
  profiles. Part B — (1) README, USAGE, OPTIONAL-FEATURES, CONTRIBUTING, templates,
  translations; (2) example; (3) dry-run contract; (4) release checklist, release check,
  onboarding measurement and candidate report.
- Hint (nonbinding): keep classification, planning and applying as separate functions of the
  engine so suite A can test classification tables without subprocesses.
- Shared acceptance gates G1–G8 apply (`.ai/specs/README.md` → "Shared acceptance gates"); G6 is met by the
  standalone suites; no paid run is needed.
- Rejected alternatives: a managed region inside the global instruction files (spec 10 and
  ADR-0009 define whole-file always-on deployment); partial installs on conflict; a second
  ownership mechanism for hook settings; restoring Russian files in the tree (A-27);
  `install.sh` at the repository root (A-02); interactive profile prompts; automatic profile
  upgrades during sync; a separate spec for CI (D-03 puts the one offline workflow in this spec, REQ-81).
- **ADR for D-02.** Part B delivery adds an ADR (or a note appended through the ADR process)
  recording that ADR-0009 Decision 6's "originals kept alongside" is replaced by originals kept
  only in history at pinned blobs; it is listed with the other delivery records in Scope.
- **Follow-up for other specs and shared files (not changed here):** spec 09's Out of Scope and
  A-24 say no spec creates CI; they should cite this spec's REQ-81 as the owner of the one
  offline workflow, and spec 09's offline command `python3 -I tests/golden-runs.py` is
  consumed by it only when the file exists; spec 13 records that its
  REQ-10, REQ-42 and REQ-45 for global targets are delivered by this engine and that its project
  pass never refreshes profiles (its Notes → Relationship to spec 11; A-21); spec 09 marks `flat` as `tuning` with `published: true` (its
  `published` case field, REQ-50, AC-38) because its reference result becomes public; the identity ledger
  (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:209`) loses the row for this file;
  `.ai/specs/README.md` may list Part A/B (Q-05).

## Change Log

### 2026-11-06 — implementation/state reconciliation

- Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

### 2026-11-13 — English refinement

- Rewritten in English. REQ-01–REQ-17 and AC-01–AC-16 keep their subjects; bundled
  behaviours split into REQ-18–REQ-64 and AC-17–AC-37. Original §4–§6 contracts made
  concrete (manifest, journal, plan, classification, recovery, profile three-way rules,
  markers). README limit aligned with the existing 60-line check; `CONTRIBUTING.md` placed
  under `docs/`; old repository URLs replaced by repository paths.
- Same day, review loop: an independent Devil's Advocate review (4 rounds: 54, 83, 92,
  99/100) added REQ-65–REQ-78 and AC-38–AC-40, defined the relationship to spec 13's
  `deploy-skills.py`, the release sequence, retired targets, adopted-edit backups and
  uninstall roll-forward; spec 09's offline suite is referenced as
  `python3 -I tests/golden-runs.py`.

### 2026-11-14 — reconciliation with refined peer specs

- Spec 13: Q-05 recorded as resolved; the relationship section now states 13's engine as the
  interim state, maps each preserved contract of 13's Notes → Relationship to spec 11 to a
  requirement, and lists the explicit changes with reasons. Added REQ-79 (leftover skills,
  reported by the installer through `deployment-set`'s `leftover_candidates`; A-42) and REQ-80
  (registry, lock and project-pass boundaries), AC-41, AC-42 and the plan field `leftover`.
  Q-06 now cites 13's DM-9, REQ-51, REQ-52 and A-02 and records that the precondition is met
  by 13's text for the mechanism only; the closed `requirement` set must be extended by Part A.
  The dry-run rule's name, kind, load value, absence of a name-map row and the 700-word limit
  of spec 08 REQ-01 are stated; its declaration in the workflows' `loads` is a `mandatory`
  section entry. Spec 13's REQ-57 is the leftover requirement; this spec's REQ-57 is the
  onboarding measurement and is unchanged.
- Spec 09: the example's run-log summary takes only the deterministic event fields; REQ-55's
  comparison covers workspace files only; `flat` is `tuning` with `published: true`
  (09 REQ-49, REQ-50). The offline check stays `python3 -I tests/golden-runs.py` (REQ-16, RC-07).
- Spec 10: the gate command and `--profile` output are 10's; the gate's position in `sync.sh`
  after this spec is this spec's (REQ-64; 10 REQ-22, A-48). Spec 08's meter gate is kept next
  to it.
- Spec 08: citations updated to REQ-02, DM-1, DM-3, REQ-12, REQ-19. No tiering interaction with
  the 60-line `README.md` limit (the meter covers rules, workflows and always-on bodies).
- Open questions Q-01, Q-02 and Q-03 are unchanged.
- 2026-11-14 — independent final review: `--adopt` of a `user-modified` target uses the adopted-edit backup (REQ-23); closed-set values `spec-11 REQ-NN` under 13 REQ-69 (Q-06, REQ-72); RC-07 maps a missing-pytest exit 3 to `not-verified`; README and repository citations corrected.

### 2026-11-14 — owner decisions recorded

- D-01–D-03 recorded under Decisions with a Clarifications session; Q-01, Q-02 and Q-03
  marked resolved (ids and text kept). REQ-72 and AC-37 carry the holder rule (owner supplies
  the line at the release gate after confirming third-party rights). A-27 resolved, A-28
  superseded, A-43 and A-44 appended. Added REQ-81 (offline CI workflow, Part B), AC-43,
  Traceability row, Scope item 13, split-boundary membership; REQ-16, RC-13, Out of Scope and
  Notes updated; the Part B ADR also records the departure from ADR-0009 Decision 6.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph stating the user, maintainer and owner outcomes |
| 2 | Out of Scope names concrete exclusions | PASS — owner actions, further CI, paid runs, spec 13/10 ownership, global merging and others named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-81; bundled behaviours split with "split from" notes |
| 4 | Every REQ maps to an AC and every AC names a REQ | PASS — Traceability table complete both ways |
| 5 | Every AC is binary and testable before implementation | PASS — fixture-based Given/When/Then; AC-34 and AC-37 are marked release gates owned by the owner |
| 6 | Non-functional targets measurable or N/A | PASS — performance N/A with reason; others have a verification method |
| 7 | Data model and contracts specified | PASS — manifest, journal, plan, profile manifest and record, markers, example provenance, release items, CLIs, exit codes, diagnostics |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — Edge Cases table and classification tables |
| 9 | Every ambiguity recorded | PASS — A-01–A-44 and Q-01–Q-06 (Q-01–Q-04 resolved) |
| 10 | No blocker question remains | PASS — Q-05 and Q-06 are open non-blockers (Q-06 an external precondition owned by spec 13); Q-01–Q-04 resolved |
| 11 | Every existing-code claim cited and verified | PASS — citations checked against `060ce6d` and the current texts of specs 09, 10 and 13 |
| 12 | Terminology matches domain definitions | PASS — collisions with spec 10 and 13 terms qualified ("ownership manifest", "installer journal", "installed state") |
| 13 | Scope is feature-sized (1–8 subtasks) | FAIL — about nine to ten subtasks in total; split recorded (Notes → Split boundary): Part A (installer and profiles, about five) and Part B (public materials, release and the REQ-81 workflow, about four to five), Part B after Part A |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 99/100, critic: sub-agent, open: none; REQ-79, REQ-80, AC-41, AC-42 and A-42 had only the targeted 2026-11-14 pass (minor F-60 and F-61 applied after the final round); REQ-81, AC-43, A-43, A-44 and D-01–D-03 had only a targeted check of the changed passages |

Verdict: **READY WITH RESERVATIONS** — check 13 fails alone: run Discovery as two tasks along
the recorded split boundary. Release gates AC-34 and AC-37 stay open until the owner acts.
Automated readiness is not sign-off.
Note 2026-11-14: reconciliation with the refined specs 08, 09, 10 and 13 added REQ-79, REQ-80,
AC-41, AC-42 and A-42 inside Part A; the verdict and the split are unchanged.
Note 2026-11-14 (owner decisions): REQ-81, AC-43, A-43, A-44 and D-01–D-03 added; Q-01–Q-03 resolved; the verdict and the split are unchanged.
