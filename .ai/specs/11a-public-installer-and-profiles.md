# 11a. Public installer with ownership records, and technology-neutral profiles

## Source

- **Split from:** `.ai/specs/11-open-source-readiness.md` at commit
  `e3ba41a000c927ac157fd2207df413107ed54cb5` (2026-11-16). That revision failed readiness
  check 13 (feature size) and recorded a split boundary (its Notes → Split boundary): Part A,
  installer and profiles, became this specification; Part B, public materials and release
  readiness, stays in spec 11. Requirement, acceptance, assumption and question identifiers
  keep their numbers; an identifier is defined in exactly one of the two files.
- **Origin of the requirements:** owner decisions in ADR-0009 Decision 1 and Decision 6
  (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:47-75`, `:215-253`): "`sync.sh`
  replaced for external users by an installer with `--dry-run`, `CLAUDE.md` backup, and
  `--uninstall`" (`:240-242`); "Technology-neutral core … `setup-new-project.sh --profile
  <name>` … the selection is recorded in `.ai/profile` (name + source version)" (`:223-229`).
- **Original request text:** the 2026-10-28 Russian specification and its English translation
  of §1–§3 and §7 are preserved in spec 11 → Source → "Translation of the 2026-10-28 request";
  "original REQ-NN" and "original §1–§3, §7" refer to that translation. The installation and
  profile sections §4, §5 and §8 were never translated there; this file cites them from the
  Russian text at `060ce6d` (`git show 060ce6dbc7116002ac5e6cd47981cfd3c13d60ff:.ai/specs/11-open-source-readiness.md`)
  by line, translated below (translated from Russian).

### Translation of original §4, §5 and §8 (lines of the `060ce6d` text)

§4.1 Mandatory preliminary check (`:53-57`): "The source version, target environments,
applicable dependencies and rights on exactly named paths are checked. … Do not install system
packages and do not change account settings automatically. The installer uses only permitted
roots. `deploy.env` is parsed as data per 13 and is not executed by a shell. A symbolic link
leading outside, an unexpected change of owner or a mismatch of the source hash stops the
corresponding write before data is lost. The absence of a previous manifest does not prove
ownership of a file found."

§4.2 Ownership manifest (`:59-65`): "A versioned manifest contains the installation identifier,
the version and hash of the source, the environment, the absolute normalized target path, the
object type, the hash of the installed bytes, the previous type/hash if any, a reference to the
backup and the operation status. Backup paths are local and not published. For a symbolic
link its text target is stored … For each path an immutable base before the first installation
(`original_backup`, or proven initial absence) and copies of individual generations for
rolling back updates (`generation_backups`) are distinguished. Updating version one to version
two does not replace the original user copy with a copy of version one. Removal restores the
state before the first installation when there are no later conflicts; rollback of a failed
update returns the previous installed generation. … A damaged base is not restored by guessing.
Hook settings use the existing contract of ownership of individual entries; the whole
`settings.json` must not be captured because one own hook is present. … Unknown manifest
versions are not migrated by guessing."

§4.3 Life cycle (`:67-77`): "1. Build the complete plan without writing and single out
conflicts. 2. Apply the existing installation permission; if it does not cover replacing
someone else's file, show the concrete difference before obtaining a decision. 3. Take the lock
of the whole installation, re-check sources and target hashes. 4. Write backups and the
operation journal to a private area. 5. Prepare new files in a temporary area, check them,
replace each owned object atomically. 6. Publish the manifest of the completed generation last.
On an intermediate failure keep the journal and explicitly report a partial installation.
7. On a repeated run first recover or safely cancel the incomplete operation; do not start an
independent installation on top of it. … The presence of a flag or a manifest does not permit
destroying a user edit. `--force`, if it exists in a compatible interface, does not cancel
ownership protection and the limits of authority."

§4.4 Removal and restore (`:79-91`): a table of target states and actions (remove an unchanged
owned file; restore a verified previous copy; keep a user-modified file and name the conflict
and the backup location; keep a directory that holds user files; do not restore over a
vanished or link-replaced target without a check; do not guess ownership by name when the
manifest is missing or damaged; keep the target when the backup is damaged). "Removal does not
touch consumer tasks, `.ai/`, source history and previously deployed directories of retired
environments. … Removing global skills does not mean removing the project."

§5 Profiles and project instructions (`:93-106`): the map of
`profiles/python-fastapi/principles/python-standards.md` and `infra-standards.md` to
`.ai/principles/`, the moved stack context to a path under `.ai/context/` "defined by the
profile manifest", and `always-on-fragment.md` to a managed fragment of `CLAUDE.md` and
`AGENTS.md` obtained through 10. "The name of the target context file is fixed in the manifest
before implementation; the installer does not copy one file into two folders 'just in case'.
`.ai/profile` contains at least `name` and the source `VERSION` … The project's own content
outside the managed fragment is kept byte for byte. The neutral core does not prescribe an
application language, cloud, infrastructure service or framework. Stack examples are allowed
in an explicitly chosen profile, and Python in maintenance tools."

§8 Execution plan and recovery (`:139-143`): "After an unsuccessful update restore the last
consistent generation from the journal, re-checking user edits. If safe automatic recovery is
impossible, keep both versions and give concrete paths/differences for a decision. Do not use a
general recursive removal to clean an unknown state."
- **Request for the split:** owner request of 2026-11-16 (translated from Russian): "review
  specs 11 and 12 in `.ai/specs`; they are very large and must be split in two if this can be
  done logically; then run each resulting spec through `/spec-draft`". The owner chose the
  file names (`11a` for the first part, the original path for the second) and autonomous
  refinement (`--auto-mode`).

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

**Deployment has no ownership, preview or removal.**
- `scripts/sync.sh` recognizes only `--from` and `--help`; other arguments are collected and
  ignored (`scripts/sync.sh:9-24`). It copies workflows, rules and principles into the
  Windsurf directories under `~/.codeium/windsurf/` (`:69-87`; spec 13 retires those targets),
  and it copies every
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
  (`tests/fixtures/validator-runtime/source_guard_exceptions.json:308`, `:332`, `:358`,
  `:3569`, `:3591`). Changing
  any of them requires the re-pinning procedure of
  `tests/fixtures/validator-runtime/README.md:9-27` (ADR-0020 Decision 2).
- Frozen checks also pin today's deployment shape: `tdd.md` named in `scripts/sync.sh` and
  `scripts/setup-new-project.sh` (`scripts/validate-contracts.sh:953-957`); `git-flow.md` and
  `orchestration.md` named in both (`:1166-1169`); sync's per-project `# 5.` block extracted
  by `test_sync_preserves_repository_knowledge_policy` (`:1174-1179`); every `rules/*.md`
  name in both scripts (`:1293-1305`); literal `cp "$file" ~/.claude/skills/…` and
  `~/.codex/skills/…` loops in sync's sections 3c and 4d (`:1308-1316`); literal
  `mkdir -p ~/.<root>/skills/$skill_name` (`:1317-1320`). Spec 13 (data-driven sync, no project rule copies)
  and REQ-04 of this spec and REQ-61 of spec 11 contradict these expressions, which the current inventory
  cannot amend; spec 13 introduces a schema-2 inventory amendment (its DM-9) for changing
  existing expressions (see Q-06 for what this spec still needs from it).
- Spec 13 (final, not yet delivered) specifies `scripts/deploy-skills.py` as the
  deployment engine behind `sync.sh`, with per-harness deploy manifests
  `C/deploy/<harness>.json` (its DM-6), journal and lock `C/deploy.lock` (its DM-7). Its
  Q-05 is resolved: this spec's installer supersedes the `deploy` write path and migrates
  those manifests (spec 13 A-31 and Notes → Relationship to spec 11a); the mapping and the
  preserved contracts are under Contracts → Relationship to spec 13's deployment engine.
- `tests/hook-install.sh` feeds `2\n` to the setup prompt (`:129-133`), copies only
  `scripts hooks harness rules workflows principles templates` into its fixture source
  (`:70-73`) and asserts the sync deployment layout byte for byte (`:783-806`); it is an
  approved path of the frozen inventory amendment (`tests/validator-runtime-oracle.py:27-40`).

**Consequence:** an external user cannot install without losing their own global
instruction file, cannot preview or undo an installation, receives Python/FastAPI/GCP
standards as global rules for every project; spec 11 cannot document an installation or a
profile choice that does not exist.

## Goal

An external user can preview, install, upgrade and remove Orchestrail's global files with a
plan that names every write, an ownership record that never deletes or overwrites their own
bytes without a backup, and a maintainer deployment that runs the same engine; projects get
technology standards only through an explicitly selected, upgradable profile on top of a
technology-neutral core. The public materials, worked example and release readiness that
build on this installer belong to spec 11.

## Scope

Requirements carry the tag **[A]** of the earlier combined specification; every requirement
of this file is an [A] requirement.

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
8. Changes to files spec 13 delivers: the subcommands of `scripts/deploy-skills.py` (REQ-71),
   `scripts/check-deploy-skills.py` (Contracts → Relationship to spec 13's deployment
   engine), and the inventory files `tests/validator-runtime-oracle.py`,
   `tests/fixtures/validator-runtime/inventory-amendment.json` and spec 13's DM-20 record
   (Q-06).

**Delivery records:** the root-listing amendment of
`.ai/principles/coding.md → Document placement` (`:83-85`) adding `profiles/` (spec 11 adds
`.github/`), `scripts/README.md` rows, `.ai/memory/architecture.md`,
`.ai/context/environment.md`, `.ai/context/runbook.md`, the re-pinned source-guard records,
the identity-ledger rows of every edited file that holds a ledger token, and one ADR
recording the decisions marked "ADR at delivery" under Assumptions.

## Out of Scope

- Everything spec 11 owns: `README.md`, `docs/USAGE.md` and the other public documents,
  `docs/OPTIONAL-FEATURES.md` (spec 11 documents this spec's commands and profiles there),
  `docs/CONTRIBUTING.md`, `.github/`, the worked example, the dry-run contract for
  `/phase-discovery` and `/bugfix`, the release checklist, `scripts/release-check.sh`, the
  onboarding measurement, the release-candidate report and the offline CI workflow.
- Creating `LICENSE`, setting `VERSION`, creating a tag, publishing a release or changing
  remote repository settings: owner actions recorded by spec 11.
- Paid or live model runs of any kind, including spec 09 release golden runs.
- A documentation site, a third harness, renaming the project or commands (spec 13),
  rewriting history (ADR-0010), packaging (pip, Homebrew, npm), a `curl | sh` bootstrap,
  Windows support.
- Deploy paths (`harness/<name>/deploy.env`), the installed-name map, the registry, the
  per-project pass, `list-projects`/`link-project`, legacy reporting and the active-consumer
  rule: owned by spec 13 (`scripts/deploy-skills.py`). This spec consumes them and only
  replaces the global-write part of that engine (Scope item 8) (Contracts → Relationship to spec 13's
  deployment engine).
- The generator, the always-on composition bytes and `docs/harness-matrix.md`: owned by spec
  10. This spec consumes `--check`, `--profile` and the deployment contract.
- Merging user text into the global instruction files (a managed region inside
  `~/.claude/CLAUDE.md`); removing a profile from a project without selecting another;
  automatic profile upgrades by `sync.sh` or `install.sh`; migrating stack content that the
  old setup already pasted into a project's `AGENTS.md`; `--profile` in
  `scripts/setup-all-repos.sh` and `scripts/setup-umbrella.sh`.
- Registering checks in `scripts/validate-contracts.sh` (frozen inventory).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| External user | Runs `scripts/install.sh` (with `--dry-run`, `--adopt`, `--uninstall`, `--harness`), `scripts/setup-new-project.sh [--profile <name>] [--adopt]`; never runs `sync.sh` |
| Maintainer | Runs `scripts/sync.sh [--from <dir>] [--adopt] [--force]` and `scripts/check-install.py` |
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
| Target | One path in the deployment set, or one path recorded in the ownership manifest | This spec |
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

Rejected synonyms: "receipt" for the ownership manifest (reserved for the hook installer's
receipt); "generation" for the installed state (spec 10 uses "generation" for a generator
publication); "lock file" for the manifest; "stack overlay" for a profile.

## Requirements

Identifiers REQ-01–REQ-17 keep their 2026-10-28 subjects; behaviours the earlier text bundled
into one item are split into REQ-18 onward, noted in parentheses. Identifiers are unique across
this file and spec 11: a new identifier takes the next number unused in either file.

### Identifiers defined in spec 11

REQ-01, REQ-02, REQ-10–REQ-17, REQ-19, REQ-54–REQ-63, REQ-72 and REQ-81; AC-01, AC-09–AC-16,
AC-18, AC-34–AC-37 and AC-43; A-24–A-29, A-32–A-37, A-41, A-43 and A-44; D-01–D-04; Q-01–Q-03
and Q-05. A citation of one of them in this file names spec 11. A-01, A-30 and A-31 apply to
both files and are repeated in each. "The engine" is `scripts/install.py` reached through
`scripts/install.sh`; "suite A" is `scripts/check-install.py` (spec 11's suite B is
`scripts/check-public-readiness.py`).

### Original requirements, restated

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

### Installer

- **REQ-18 [A] Preview writes nothing (split from REQ-03).** WHEN the engine runs with
  `--dry-run`, THE engine SHALL print the plan and SHALL NOT create, modify, rename or
  delete any file or directory, including the lock, journal, manifest and backup
  directories.
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
  and then replacing the target (a modified orphaned entry is released instead, REQ-73), and SHALL leave every other conflict code unresolved.
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
  with the path of its original backup or `none`, and keep its entry in the ownership manifest.
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
- **REQ-34 [A] Missing manifest.** IF `--uninstall` finds no ownership manifest and no spec 13
  deploy manifest (REQ-43), THEN THE engine SHALL remove nothing, report `no-manifest` and exit 0.
- **REQ-35 [A] Uninstall boundary.** WHEN `--uninstall` runs, THE engine SHALL NOT modify any
  consumer project, the project registry, the run-log store, legacy harness directories or
  any path that is neither recorded in the ownership manifest nor a bookkeeping path, except the
  hook settings, receipt and hook lock that `install-hooks.sh uninstall` changes (REQ-38).
- **REQ-36 [A] Symbolic-link target.** IF a target is a symbolic link, THEN THE engine SHALL
  report `symlink-target` unless `--adopt` applies, and SHALL never write through the link.
- **REQ-37 [A] Foreign owner.** IF an existing target or its parent directory is owned by a
  user ID other than the engine's effective user ID, THEN THE engine SHALL report
  `foreign-owner`.
- **REQ-38 [A] Delegated hook settings.** WHEN a targeted harness directory contains
  `hooks.json`, THE engine SHALL obtain a predicted result from `install-hooks.sh plan`
  while planning and SHALL apply hook settings only by running `install-hooks.sh install`
  (or, at uninstall, `uninstall` for each `delegated` hook record of the ownership manifest),
  never by writing `settings.json` or the hook receipt itself.
- **REQ-39 [A] Always-on bytes.** THE engine SHALL install, at each targeted harness's
  `always_on_path`, exactly the bytes spec 10's deployment contract defines: the generated
  `harness/<name>/always-on.md` followed by the installation record built from the hook
  installer's result, or `{"reason":"no-native-adapter","status":"unavailable"}` when the
  harness has no `hooks.json`.
- **REQ-40 [A] Generated files must be current.** WHEN an install (dry-run included) starts,
  THE engine SHALL run `python3 -I <root>/scripts/gen-docs.py --check --root <root>` and, if
  it exits non-zero, SHALL exit 3 with `generated-files-stale` before reading any target.
- **REQ-41 [A] Inputs as data.** THE engine SHALL parse `deploy.env`, spec 13 deploy manifests
  (`C/deploy/<harness>.json`; invalid → exit 2 `deploy-manifest-invalid`), the ownership
  manifest, the installer journal, profile manifests and profile records only as data (spec 13
  REQ-44 for `deploy.env`; strict JSON for the rest: duplicate keys, `NaN`/`Infinity`,
  unknown keys and unknown `schema_version` rejected) and SHALL NOT migrate an unknown
  version by guessing.
- **REQ-42 [A] Active consumers.** WHEN an install or uninstall plan has at least one entry
  whose action is not `unchanged` or `keep`, or a `delegated` record whose predicted settings
  hash differs from the current one, and `deployment-set` reports an active consumer (spec 13 REQ-43) without `--force`,
  THE engine SHALL write nothing and exit 1 with `active-task`; `--force` SHALL carry only
  the meaning spec 13 gives it.
- **REQ-43 [A] Migration of spec 13 deploy manifests.** WHEN an install or uninstall starts
  without an ownership manifest and one or more spec 13 deploy manifests
  (`C/deploy/<harness>.json`, spec 13 DM-6) exist, THE engine SHALL treat each of their
  objects as an entry by the mapping under Contracts → Relationship to spec 13's
  deployment engine, and SHALL delete those deploy manifests when its own operation commits
  (Apply order step 11 for an install or an uninstall).
- **REQ-44 [A] Exit codes and diagnostics.** THE launcher and the engine SHALL exit with the
  codes and print diagnostics in the format under Contracts → Exit codes and Diagnostics.
- **REQ-45 [A] Inputs changed during apply.** IF a source file's SHA-256 or a target's
  content identity differs, at the moment of its write, from the value in the plan, THEN THE
  engine SHALL stop before that write, keep the journal and exit 4 with `source-changed` or
  `target-changed`.

### Profiles

- **REQ-46 [A] Profile manifest validation.** IF `profiles/<name>/profile.json` violates Data
  Model → Profile manifest, THEN THE engine SHALL exit 2 with `profile-invalid` before any
  project write.
- **REQ-47 [A] Managed fragment.** WHEN the engine writes a managed fragment into a project
  instruction file, THE engine SHALL place the profile fragment between the markers under
  Data Model → Managed fragment and SHALL keep every byte outside the begin line, region
  content and end line unchanged.
- **REQ-48 [A] Malformed markers.** IF a project instruction file contains a begin marker
  without exactly one following end marker, more than one begin marker, an end marker
  before the begin marker, or a begin marker naming a profile other than the profile record's
  `name` (or, without a profile record, other than the profile being applied), THEN THE engine SHALL report `fragment-markers-invalid` for that
  file and write nothing.
- **REQ-49 [A] Profile file conflicts.** IF a profile target exists without a profile-record
  entry and differs from the new content, or its current content differs from its recorded
  content while the new content differs from both the recorded and the current content, THEN THE engine SHALL report `foreign-target` or
  `user-modified` and, unless `--adopt` is given, write nothing.
- **REQ-50 [A] Profile switch and upgrade.** WHEN a profile operation runs against an existing
  profile record and REQ-09 does not apply (another profile, another version, or changed source
  content of a profile file or fragment), THE engine SHALL decide every target by the
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

### Maintainer gates

- **REQ-64 [A] Maintainer gates.** WHEN `scripts/sync.sh` runs, THE SYSTEM SHALL run the
  contract validator and `gen-docs.py --check` before invoking the installer, and SHALL NOT
  invoke the installer or the per-project pass when either fails or when the installer exits
  non-zero. Where spec 08 is delivered, sync also runs its `measure-context.sh check` there
  (spec 08 REQ-08) under the same rule. When the installer exits non-zero, sync SHALL print
  `ERROR: installation stopped (exit <n>); see the diagnostics above` and exit with that code.
### Requirements added in the 2026-11-13 and 2026-11-14 reviews (REQ-79 and REQ-80 on 2026-11-14)

- **REQ-65 [A] Retired targets (new 2026-11-13).** WHEN an install targets a harness whose
  skills directory holds a path listed in `scripts/install-retired.json` (Data Model →
  Retired targets) without an ownership-manifest entry, THE engine SHALL report info `legacy-target`
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
- **REQ-73 [A] Modified orphans (split from REQ-28).** IF an orphaned entry of a targeted
  harness is modified, THEN THE engine SHALL report `user-modified` and, under `--adopt`,
  drop the entry, keep the file and report `released`.
- **REQ-74 [A] Other harnesses (split from REQ-28).** WHEN an install targets a subset of the
  harnesses that have entries, THE engine SHALL carry the entries of the other harnesses into
  the new ownership manifest unchanged and SHALL NOT touch their targets.
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
- **REQ-80 [A] Registry stays read-only.** THE engine and `project-pass` SHALL NOT write the
  project registry (spec 13 REQ-08 preserved).
- **REQ-84 [A] Locks are never taken over (split from REQ-80).** THE engine and `project-pass`
  SHALL NOT delete either lock file (`C/install.lock`, `C/deploy.lock`) or take one over from a
  process that holds it (spec 13 DM-7 preserved).
- **REQ-85 [A] Project pass leaves profiles alone (split from REQ-80).** THE `project-pass`
  subcommand SHALL NOT create, refresh or remove any profile file or profile record in a
  project (spec 13 Contracts → Project pass preserved).
- **REQ-82 [A] Runtime guard for profiles.** IF `scripts/setup-new-project.sh --profile` runs
  while `python3` is missing or older than 3.11, THEN THE SYSTEM SHALL exit 3 with
  `runtime-unavailable` before writing any file.
- **REQ-83 [A] Writable parents.** IF the parent directory of a target that the plan creates,
  replaces or removes, or its first existing ancestor when the parent is to be created, is not
  writable by the engine's effective user, THEN THE engine SHALL exit 3 with
  `target-not-writable` during planning and write nothing.

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
| `installation_id` | string | 32 lowercase hex characters (`uuid4().hex`); Apply order step 2 fixes it after taking the locks and before planning, so the plan names real backup paths: the manifest's id, else the journal's id (an interrupted first install), else a new one; reused while a manifest exists; a new one after an uninstall that leaves no entry. A dry run without a manifest generates none and uses `00000000000000000000000000000000` in planned backup paths |
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
| `retained` | string \| null | Conflict or info code that kept the entry after an uninstall (`user-modified`, `type-changed`, `backup-corrupt`, `directory-kept`), else null; a later install sets it to null for every entry it records as owned |
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
| `installation_id` | The manifest's id, the id generated in step 2, or null in a dry run without a manifest (planned backup paths then use the all-zero placeholder) |
| `source` | As in the ownership manifest; null for uninstall |
| `recovery` | null, or `{"journal": path, "operation": …, "steps": [{"path", "action": "restore" \| "remove" \| "apply" \| "none" \| "delete-temporary" \| "hooks-uninstall" \| "conflict", "current": identity, "after": identity, "conflict": null \| "target-changed"}]}` in the order Contracts → Recovery runs them |
| `entries` | Sorted by `path`: `{"path", "harness" (null for profile), "type", "action", "source", "previous", "next", "ownership", "conflict", "backup"}`; `backup` is null or `{"kind": "original" \| "previous" \| "adopted" \| "profile", "path": abs path}` naming the backup the action will write |
| `delegated` | `[{"kind":"hooks","harness","operation","predicted_result","settings_path","settings_sha256_before","settings_sha256_after","receipt_path","receipt_sha256_before","receipt_sha256_after","lock_path"}]`; from `install-hooks.sh plan`: `predicted_result` is its `result` when `status` is `planned`, otherwise its whole output object; the path and hash fields are copied, or null when the output is unavailable; `lock_path` is `C/hooks-installed.lock` |
| `bookkeeping` | Sorted `{"path","action"}` for the ownership manifest, journal, both locks (`C/install.lock`, `C/deploy.lock`), backup files and directories, each migrated spec 13 deploy manifest (`remove`), profile record; action `create`, `replace` or `remove`, except that a lock file appears only with `create` (or not at all when it exists) and is never removed (REQ-80) |
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
`:166`, `:213`. Discovery lists every match with its disposition; this spec's reviewer
confirms that no obligation was dropped.

### Stack terms

Case-insensitive, whole word (`\b…\b`): `python`, `fastapi`, `sqlalchemy`, `pydantic`,
`pytest`, `postgres`, `postgresql`, `asyncpg`, `gcp`, `google cloud`, `cloud run`, `terraform`,
`mypy`, `ruff`, `alembic`, `structlog`. Checked in `principles/*.md` only, code blocks
included.

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
python3 scripts/check-install.py
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
  → exit 2. With `--profile`, setup first runs the launcher's runtime probe (same probe as
  `scripts/install-hooks.sh:45`; missing `python3` or a version below 3.11 → exit 3
  `runtime-unavailable`, REQ-82), then validates the profile name, `profile.json` and the
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
Relationship to spec 11a, A-31; its Q-05 is resolved). This spec changes it as follows:

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
- `scripts/check-deploy-skills.py` (spec 13's suite) is updated by this spec: its `deploy` cases
  move to suite A as installer cases or are rewritten against `deployment-set` and
  `project-pass`, and its other cases stay unchanged.

**Leftover skills (spec 13 REQ-57).** Leftover reporting lives in the installer, which stays
after `deploy` is removed: `install` (not `uninstall`) takes each harness's
`leftover_candidates` from `deployment-set`, drops every candidate that is, or lies inside,
the path of an ownership-manifest entry (an owned object is not a leftover), and reports the rest as
`leftover <dir> (not removed; review, then remove it manually)` lines and in the plan's
`leftover` field (REQ-79). Spec 13's detection knowledge (name map, adapters) stays in
`deployment-set`; the ownership knowledge stays in the installer.

**Preserved contracts of spec 13** (spec 13 Notes → Relationship to spec 11a), each met by a
requirement of this spec or changed on purpose:

| Spec 13 contract | Met here by |
|---|---|
| An owned file the user changed is never overwritten or removed; a conflict writes nothing (13 REQ-42, REQ-63) | REQ-03, Install classification (`user-modified`, exit 1, nothing written); the exception is `--adopt` with a verified backup (REQ-06), which replaces 13's implicit first-run adoption (see below) |
| A deferral writes nothing while any active consumer exists, the source checkout included; `--force` overrides only that freeze (13 REQ-43, DM-8) | REQ-42 and `deployment-set`'s `active` list |
| Leftover skills are reported and never removed (13 REQ-57) | REQ-79 |
| The registry stays read-only (13 REQ-08) | REQ-80 (REQ-35 for uninstall) |
| The lock is never taken over (13 DM-7) | REQ-84, REQ-24 |
| The project pass stays as 13 defines it and never touches profile files (13 Contracts → Project pass) | REQ-71 (`project-pass` unchanged), REQ-85, A-21 |

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
| 2 | Invalid request or input: `usage`, `source-invalid` (a required source file — `scripts/install.py`, `scripts/deploy-skills.py`, a harness's `deploy.env` or generated `always-on.md` — missing or unreadable), `legacy-journal-present`, `deploy-config-invalid`, `deploy-manifest-invalid`, `manifest-invalid`, `journal-invalid`, `profile-invalid`, `profile-record-invalid`, `profile-not-found` |
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
| directory entry, `created: true` | — | removed with `rmdir` after its files when empty; otherwise `keep` with info `directory-kept` and the entry kept with `retained: "directory-kept"` |
| directory entry, `created: false` | — | entry dropped; the directory is never removed |

The hook delegate runs `install-hooks.sh uninstall`; its result is reported, never retried.
After applying, the ownership manifest keeps exactly the entries whose `retained` is set:
every `retain` entry and every `keep` entry with `directory-kept`; when none remain, the ownership manifest, journal and `S/install-backups/<installation_id>/` are deleted.

### Apply order (install)

1. Resolve paths; run REQ-40's check; run `deploy-skills.py deployment-set --from <root>
   [--force]` (its failure → exit 2 `deploy-config-invalid`); select targeted harnesses
   (none → exit 3 `no-harness`).
2. Non-dry-run only: create `C` with mode 0700 and acquire `C/install.lock`, then
   `C/deploy.lock` (`fcntl.flock`, non-blocking, retry every 25 ms for 5 s →
   `installer-busy`). Then fix the `installation_id`: the ownership manifest's id when a
   manifest exists; otherwise the installer journal's id when a journal exists; otherwise a
   new `uuid4().hex`.
3. Recovery when a journal exists. A dry run plans it only, and step 5 then classifies every
   target as if the planned recovery had run: a target named by a recovery step has that step's
   `after` identity. A planned recovery conflict makes the dry run exit 1 (a dry run never
   exits 4).
4. `install-hooks.sh plan install --from <root>` for each harness with `hooks.json`.
5. Build the deployment set, classify every target and build the plan.
6. When the plan meets REQ-42's trigger (an entry whose action is not `unchanged` or `keep`,
   or a `delegated` record whose `settings_sha256_after` differs from
   `settings_sha256_before`): spec 13's active-consumer rule (REQ-42). In a non-dry run, `deployment-set` is run again now, while both locks are
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
11. Record the SHA-256 of the ownership manifest about to be written as `commit` in the journal; write the ownership manifest (temporary file, `fsync`, `os.replace`); delete the journal,
    the operation's previous-state backups and the directory
    `S/install-backups/<installation_id>/previous/`; release the lock; print the summary.

Uninstall follows steps 1–4 (without the generated-file check and harness selection: its
targets come from the ownership manifest; step 4 runs `install-hooks.sh plan uninstall` once
for each `delegated` record of kind `hooks` in the ownership manifest, and only those records
lead to a hook uninstall and appear in the plan's `delegated` list; it uses `deployment-set` only for `active`; a failing `deployment-set` is exit 2
`deploy-config-invalid` because active consumers cannot be evaluated — `--force` does not
bypass it, and the user runs the uninstall from a checkout whose configuration is valid), classifies by Uninstall classification, applies step 6, and
in step 7 stops only for `active-task` (exit 1, nothing written); `retain` entries do not
stop it (REQ-70). It journals each `remove`/`restore` with a previous-state backup of the
removed bytes, journals and then runs `install-hooks.sh uninstall` after the target steps
(REQ-78), and finishes with
step 11 (or deletes the ownership manifest when no entry is retained), exiting 1 when any
entry was classified `retain` and 0 otherwise; an entry kept only with `directory-kept` does
not change the exit code (Diagnostics: info).

`ORCHESTRAIL_INSTALL_TEST_FAULT=after-write:<n>` (test-only) makes the engine exit 4
immediately after the n-th applied step, without cleanup, to simulate an interruption; it
can only stop a run. `ORCHESTRAIL_INSTALL_TEST_FOREIGN_UID=<path>` (test-only) makes the
engine treat that path as owned by another user ID; it can only add a `foreign-owner`
conflict. `ORCHESTRAIL_INSTALL_TEST_PAUSE=before-write:<n>:<path>` (test-only) makes the
engine, immediately before step 9's re-verification of the n-th step, wait until `<path>`
exists (polling every 25 ms, for at most 30 s, then continuing); the suite changes a source or
target during the wait and then creates `<path>`; it can only delay a run. All three are read
only by the engine and documented as test seams in `scripts/README.md` (A-16).

### Recovery

First, every step's `temporary` file that still exists is deleted. A journal with
`operation: install` is rolled back: steps marked applied, in reverse order — current
identity equals `next` → restore `previous` from its previous-state backup (or remove when
`previous` is absent); equals `previous` → nothing; anything else → conflict
`target-changed`, both versions kept and reported. A journal with `operation: uninstall` is
rolled forward from its own steps, in order: current identity equals `next` → done; equals
`previous` → apply the step; anything else → conflict `target-changed`; a hook step not
marked applied is executed by running `install-hooks.sh uninstall` (REQ-78); afterwards the
ownership manifest is rewritten as step 11 of that uninstall would have written it. Hook settings are not rolled
back (the hook installer is idempotent and recovers its own transactions; info
`hooks-unavailable` is reported only when its result is unavailable). A recovery without
conflicts deletes the journal and continues with the requested operation; with conflicts it
exits 4 and keeps the journal. Rolling back an install that had no ownership manifest before it
(an interrupted first install) restores every original backup it took and then deletes
`S/install-backups/<installation_id>/`; the requested install continues under the same id and
takes its backups afresh. A conflict keeps that directory. Before any of this, the current manifest's hash (null when
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

### Existing-check obligations

- Except in spec 11 REQ-72's release-preparation commit (which changes check expressions only through
  spec 13's schema-2 inventory amendment, followed by re-pinning), edits to
  `scripts/validate-contracts.sh` are allowed only inside function bodies outside the
  pinned-body region, never in a `check` line or failure message, and never add or
  remove a line matching `\bcheck\b`; any edit is followed by the source-guard re-pinning
  procedure. This spec needs none; spec 11 needs one only if its REQ-63 forces a body change.
- Changing `scripts/sync.sh` or `scripts/setup-new-project.sh` is followed by re-pinning their
  digests under `tests/fixtures/validator-runtime/README.md:9-27`. `tests/hook-install.sh` is not
  edited; if a change is unavoidable, its inventory resource entry is re-amended and the
  oracle digest updated as spec 10 describes.

## Non-Functional Requirements

| Attribute | Target / standard | Verification |
|---|---|---|
| Portability | Bash and Python 3.11+ standard library only; no package installation, no account-setting change; Linux local filesystems verified; macOS is a design target (`fcntl` is available there) that this delivery does not verify | Suite A static import check (standard-library modules only) and its Linux run; spec 11 states the macOS limit in `docs/OPTIONAL-FEATURES.md` |
| Network and models | No network connection, model or harness CLI invocation by the engine, the launcher or suite A | Suite A runs the engine with `PATH` fakes for `gh`, `claude`, `codex`, `curl`, `wget` that record calls |
| Data safety | Byte-exact backups verified by SHA-256; atomic per-file replacement with `fsync`; no write through a symbolic link | AC-05, AC-24, AC-25 |
| Privacy | Backups, manifest and journal stay under the user's XDG directories with modes 0600/0700; nothing from them is committed | Suite A asserts the modes and that no manifest, journal, lock or backup path lies under the source root |
| Determinism | Identical inputs give byte-identical installed bytes and plan JSON apart from paths containing `installation_id`; manifests differ only in `installation_id` | AC-03 (installed bytes, manifests); suite A compares two dry-run plans of one home byte for byte |
| Isolation of tests | Suites use disposable `HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, never the real home | Suite A asserts every write is under its temporary root |
| Compatibility | Hook receipt versions 1 and 2 and the `install`/`uninstall` output of `install-hooks.sh` unchanged; deployed always-on bytes equal spec 10's contract | `tests/hook-install.sh` passing (its `copy_source` lacks `VERSION`, which is why `VERSION` is optional for the engine; any unavoidable fixture edit follows Existing-check obligations); AC-26 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| Empty `HOME` without `~/.claude` or `~/.codex`, no `--harness` | Exit 3 `no-harness`, nothing written | REQ-20 |
| Maintainer machine deployed by the old sync (no manifest) | Every differing target is `foreign-target`; install exits 1; rerun with `--adopt` backs up and replaces; identical files become `preexisting-identical` | REQ-22, REQ-23 |
| User keeps `~/.claude/CLAUDE.md` as a symbolic link into a dotfiles repository | `symlink-target`; `--adopt` stores the link text and writes a regular file; uninstall restores the link | REQ-36, REQ-29 |
| `~/.claude` itself is a symbolic link | Allowed: deploy roots are resolved once; links below the resolved root → `symlink-in-path` | REQ-69 |
| User edits the installed `CLAUDE.md`, then upgrades | `user-modified`, exit 1; `--adopt` keeps the edited bytes as an adopted-edit backup under `S/adopted-backups/` (reported, never deleted) and replaces | REQ-22, REQ-23 |
| User adds a file inside an installed skill directory | Uninstall removes `SKILL.md` only, keeps the directory, `directory-kept` | REQ-31 |
| Interruption after k writes | Rerun rolls back from the journal to the previous installed state, then installs | REQ-25, REQ-26 |
| A target changed by the user between interruption and rerun | Recovery keeps both versions, exit 4, journal kept | REQ-26 |
| Two installers start together | The second exits 3 `installer-busy` after 5 s | REQ-24 |
| Interruption during uninstall | Rerun rolls forward from the journal steps and completes | REQ-26, REQ-70 |
| `install.sh --harness claude` after a claude+codex install | Codex entries carried over unchanged | REQ-74 |
| Home deployed by an older release still holds `principle-python-standards` | `legacy-target`; removed with backup under `--adopt` when bytes match a released hash | REQ-65 |
| Crash between temporary-file creation and rename | Recovery deletes the journalled temporary file | REQ-26 |
| Profile switch with a begin marker naming another profile than the record | `fragment-markers-invalid`, nothing written | REQ-48 |
| Source file edited during apply | Exit 4 `source-changed` before that write; rerun rolls back | REQ-45 |
| Manifest deleted by the user, no spec 13 deploy manifest | Uninstall removes nothing (`no-manifest`); install treats targets as foreign | REQ-34 |
| Uninstall in a home deployed by spec 13's engine (deploy manifests, no ownership manifest) | Objects migrate as owned entries and are removed as `migrated` (`no-original` for always-on files); deploy manifests deleted at commit | REQ-43, REQ-34 |
| Spec 13 deploy manifest malformed or of an unknown version | Exit 2 `deploy-manifest-invalid`, nothing written | REQ-41 |
| `setup-new-project.sh --profile` with `python3` missing or older than 3.11 | Exit 3 `runtime-unavailable` before any write | REQ-82 |
| Manifest with `schema_version` 2 or duplicate keys | Exit 2 `manifest-invalid`, nothing written | REQ-41 |
| Original backup file deleted or altered | `backup-corrupt`, target kept, entry retained | REQ-33 |
| Target owned by another user (shared machine) | `foreign-owner`, not resolvable by `--adopt` | REQ-37 |
| Parent directory not writable | Exit 3 `target-not-writable` at planning | REQ-83 |
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

## Acceptance Criteria

All suites build fixtures in temporary directories with isolated `HOME` and XDG variables
and copy the needed source subset; "tree snapshot" means the sorted list of every path under
the temporary root with type, mode, size, mtime and content hash. Criteria marked
**release gate** depend on an owner action; they are not part of the implementation's
acceptance and stay open until the owner acts.

- **AC-02** (REQ-03, REQ-30, REQ-70) — Given an install into an empty fixture home with
  `--harness claude --harness codex`, after which the user edits one installed `SKILL.md` and
  the installed `~/.codex/AGENTS.md`, When `install.sh --uninstall` runs, Then both edited
  files are byte-identical to the edits, standard error has two `user-modified` lines, the
  exit code is 1, every other installed file target is gone, and the ownership manifest retains exactly
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
  `install.sh --dry-run --adopt` prints a plan and then `install.sh --adopt` runs, Then every
  path whose existence or content identity differs between the snapshots before and after the
  run (directory mtimes are not compared) is named by the plan — an entry with action other
  than `unchanged` and `keep`, a `bookkeeping` path, or a `delegated` settings, receipt or lock
  path; every such entry, and every `bookkeeping` path except the transient ones (the installer
  journal, the previous-state backups and their `previous/` directory, which the run creates
  and deletes), differs between
  the two snapshots; and the dry run left the snapshot identical.
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
  previous-only targets are removed, an edited previous-only target is kept and reported, the
  shared target (unedited by the user, with new bytes in `p2`) is replaced (row "cur = base,
  new ≠ base"), and `.ai/profile` names `p2`.
- **AC-17** (REQ-18) — Given fixture homes (a) empty with `~/.claude`, (b) installed, (c) with an
  interrupted journal, When `install.sh --dry-run`, `install.sh --uninstall --dry-run` and the
  profile operation with `--dry-run` run, Then each prints valid plan JSON and the tree
  snapshot of the temporary root (homes, XDG directories, project) is identical before and
  after, including the absence of `C/install.lock`.
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
- **AC-22** (REQ-21, REQ-41, REQ-68) — Given a committed install, When suite A validates the ownership manifest,
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
  unchanged and the ownership manifest's `harnesses` still lists both.
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
  exits 1 with `active-task` and writes nothing; and with `--force`, Then no `active-task`
  diagnostic is printed, the changed target is written and the exit code is 0.
- **AC-29** (REQ-43, REQ-71) — Given a fixture home deployed by spec 13's engine (deploy
  manifests for claude and codex, each skill and always-on object at its recorded digest
  except one skill the user edited), When `install.sh` runs, Then every unchanged object is
  classified `owned` with `original.state` `migrated`, the edited skill gives `user-modified`
  and exit 1, and nothing is written; When it runs with `--adopt`, Then the ownership manifest holds an
  entry per object and `C/deploy/claude.json` and `C/deploy/codex.json` no longer exist; and
  `scripts/deploy-skills.py deploy` exits 2 (unknown subcommand) while `deployment-set`
  prints the documented JSON and leaves the snapshot unchanged; and Given a second spec 13 home
  without user edits, When `install.sh --uninstall` runs, Then every migrated object is removed,
  each always-on file reports `no-original`, the created skill directories are removed when
  empty, both deploy manifests are deleted and the run exits 0.
- **AC-30** (REQ-44, REQ-45, REQ-83) — Given one fixture per code, produced as listed, When the
  engine runs, Then the exit code and diagnostic code match the exit-code table and every
  diagnostic line matches `^install: [a-z-]+: (-|/.+): .+$`. Exit 2: `usage` (an unknown
  option), `source-invalid` (the source's `harness/claude/always-on.md` removed),
  `legacy-journal-present` (a `C/deploy/journal.json`), `deploy-config-invalid` (a malformed
  `harness/claude/deploy.env`), `deploy-manifest-invalid` (a `C/deploy/claude.json` with a
  duplicate key), `manifest-invalid` (AC-22), `journal-invalid` (a journal whose
  `manifest_sha256` matches neither the current manifest nor its `commit`), `profile-invalid`,
  `profile-not-found` (AC-31) and `profile-record-invalid` (a `.ai/profile` with an unknown
  key). Exit 3: `runtime-unavailable` (a `PATH` whose `python3` stub reports 3.10),
  `generated-files-stale` (AC-27), `no-harness` (AC-19), `installer-busy` (AC-21),
  `target-not-writable` (a skills directory with mode 0555; skipped with a recorded reason
  when the suite runs as user ID 0), `project-not-initialized` (a project without `.ai/`) and
  `profile-fragment-unavailable` (a fixture `gen-docs.py` stub exiting 1). `io-error` and
  `internal-error` have no reliable fixture and are excluded; suite A instead calls the
  engine's vocabulary guard directly with an unknown action and asserts `internal-error`.
  And Given `ORCHESTRAIL_INSTALL_TEST_PAUSE` set before the first write step and the step's
  source file modified during the pause, Then the run
  exits 4 with `source-changed`, the journal remains, and a re-run restores the previous
  installed state; and Given the step's target modified the same way instead, Then the run exits 4 with
  `target-changed` and the modified bytes are kept.
- **AC-31** (REQ-46, REQ-52, REQ-82) — Given profile manifests violating each rule of Data Model →
  Profile manifest, and `--profile Bad_Name` and `--profile missing`, When setup runs, Then
  each exits 2 (`profile-invalid`, `usage`, `profile-not-found`) and the project snapshot is
  unchanged; and Given a `PATH` whose `python3` stub reports version 3.10, When setup runs with
  `--profile python-fastapi`, Then it exits 3 with `runtime-unavailable` and the project
  snapshot is unchanged.
- **AC-32** (REQ-47, REQ-48) — Given `AGENTS.md` with user text before and after an existing
  region, When the profile is re-applied with a new fragment, Then only the region content
  changes and all bytes outside it are identical; and Given files with two begin markers, a
  begin without end, an end before begin, and a begin marker naming `other` while the profile
  record names `python-fastapi`, Then each gives `fragment-markers-invalid` and
  the file is unchanged.
- **AC-33** (REQ-51) — Given a project with `.ai/profile` for `python-fastapi`, When setup runs
  without `--profile` and with empty standard input, Then it exits 0, the profile files,
  regions and record are unchanged, and its standard output contains no stack question.

- **AC-44** (REQ-64) — Given a fixture source whose validator stub exits 0 and whose
  `gen-docs.py --check` stub exits 1, and stubs for the installer and `deploy-skills.py
  project-pass` that record their calls, When `sync.sh --from <source>` runs, Then it prints
  spec 10's REQ-22 message, exits 1, calls neither the installer nor `project-pass` and creates
  no file under the fixture home; Given a meter stub exiting 1 in a source where spec 08's
  `measure-context.sh` exists, Then the same holds; and Given passing gates and an installer
  stub exiting 1, Then sync prints `ERROR: installation stopped (exit 1); see the diagnostics
  above`, exits 1 and does not call `project-pass`.

- **AC-38** (REQ-26, REQ-67, REQ-70, REQ-78) — Given an installation with a `backup`-origin target,
  an `absent`-origin target and a third owned file, When `--uninstall` runs with
  `ORCHESTRAIL_INSTALL_TEST_FAULT=after-write:1` and exits 4, and `--uninstall` is re-run
  without the variable, Then the `backup`-origin target holds its original bytes, the other
  two are removed, the ownership manifest and journal are gone, and the re-run exits 0; Given the fault
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
  `leftover` field; and Given a candidate that equals an ownership-manifest entry's path, Then it is not
  reported.
- **AC-42** (REQ-80, REQ-84, REQ-85) — Given a fixture home, a registry and held locks, When `install.sh`,
  `install.sh --uninstall` and `deploy-skills.py project-pass` run, Then the registry bytes are
  unchanged, neither `C/install.lock` nor `C/deploy.lock` is deleted or replaced while another
  process holds an `flock` on it (the installer exits 3 `installer-busy`; `project-pass`
  exits 1 with spec 13's `deploy-locked`), and in a registered
  project holding `.ai/profile` and a managed fragment `project-pass` leaves every profile
  file and record byte-identical.

## Traceability

| REQ | AC |
|---|---|
| REQ-03 | AC-02, AC-20 |
| REQ-04 | AC-03 |
| REQ-05 | AC-04 |
| REQ-06 | AC-05 |
| REQ-07 | AC-06 |
| REQ-08 | AC-07 |
| REQ-09 | AC-08 |
| REQ-18 | AC-17 |
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
| REQ-64 | AC-03, AC-44 |
| REQ-65 | AC-39 |
| REQ-66 | AC-19, AC-40 |
| REQ-67 | AC-24, AC-38 |
| REQ-68 | AC-22 |
| REQ-69 | AC-25 |
| REQ-70 | AC-02, AC-38 |
| REQ-71 | AC-29 |
| REQ-73 | AC-23 |
| REQ-74 | AC-23 |
| REQ-75 | AC-39 |
| REQ-76 | AC-39 |
| REQ-77 | AC-39 |
| REQ-78 | AC-38 |
| REQ-79 | AC-41 |
| REQ-80 | AC-42 |
| REQ-82 | AC-31 |
| REQ-83 | AC-30 |
| REQ-84 | AC-42 |
| REQ-85 | AC-42 |

Every AC names at least one REQ. No criterion of this spec is a release gate; the release gates AC-34 and AC-37 are in spec 11.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Users' personal global instruction files are replaced (with backup) | Lost personal instructions in sessions until restored | Medium | Conflict without `--adopt`; spec 11's README and USAGE explain the backup and uninstall |
| Homes deployed before spec 13's engine have no manifest | First sync stops with `foreign-target` conflicts | Medium | Documented one-time `sync.sh --adopt`; identical files adopted without backup; homes deployed by spec 13 migrate without conflicts (REQ-43) |
| Spec 13's delivered engine differs from its spec text | The `deployment-set` contract or DM-6 mapping needs adjustment | Medium | Discovery of this spec verifies DM-6 and the engine at the delivered revision; changes are recorded in this spec's delivery ADR |
| Migrated always-on files have no original backup | Uninstall removes `CLAUDE.md`/`AGENTS.md` without restoring earlier user content | Medium | Info `no-original`; the earlier content was already overwritten by sync and spec 13's adopt |
| Frozen validator and source guard | Implementation blocked by fingerprint failures | High | Standalone suites; re-pinning procedure; no new `check` lines |
| `flock` binary absent on macOS | Hook installation unavailable there | Medium | Recorded in the installation record and OPTIONAL-FEATURES; engine uses `fcntl` |

## Assumptions

- A-01 | Language | Resolved: English spec; the Russian text stays in history at `060ce6d`, translated under Source | Source: `rules/language.md`; `.ai/principles/coding.md:11` | Reversible: yes
- A-02 | Location of `install.sh` | Resolved: `scripts/install.sh`, not the repository root | Source: `scripts/README.md:3` ("All executable shell helpers live in this directory"); `.ai/principles/coding.md:83-85` | Reversible: yes
- A-03 | Engine language | Resolved: Python 3.11+ standard library, run as `python3 -I`, Bash launcher with a version guard | Source: `scripts/install-hooks.sh:45-51` and `.ai/memory/architecture.md:87` (Python installer engine precedent); `.ai/context/runbook.md:41-43`. ADR-0009 Decision 6 (`:243-244`) names bash for `sync.sh`/`setup-*` and Python for optional tools; the launcher and `sync.sh` stay Bash, and the Python engine follows the delivered hook installer's precedent — a deviation recorded in this spec's delivery ADR | Reversible: yes
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
- A-14 | Overlap with spec 13's `deploy-skills.py` (DM-6 manifests, DM-7 journal and lock, global writes) | Resolved: `install.py` becomes the only global writer; `deploy-skills.py deploy` is removed and replaced by read-only `deployment-set` and `project-pass`; DM-6 manifests are migrated and deleted (REQ-43, REQ-71) | Source: ADR-0009 Decision 1 Consequences and Decision 6 (installer belongs to 11); spec 13 A-31 and Notes → Relationship to spec 11a (its Q-05 is resolved; its list of preserved contracts is mapped to requirements under Contracts → Relationship to spec 13's deployment engine) | Reversible: yes (ADR at delivery)
- A-15 | Exit codes | Resolved: 0/1/2/3 aligned with spec 10's family, plus 4 for incomplete | Source: spec 10 Contracts → Stages and exit codes; best practice | Reversible: yes
- A-16 | Interruption testing | Resolved: test-only fault variable that can only stop a run, and (2026-11-16) a pause variable that can only delay one, so the suite can change an input between planning and a write | Source: `.ai/memory/architecture.md:88` (git-rails test-only seam that can only deny) | Reversible: yes
- A-17 | Profile layout and target names | Resolved: `profile.json`; targets under `.ai/principles/` and `.ai/context/stack-python-fastapi.md` | Source: ADR-0009 Decision 6 (`:225-229`); original §5 (name fixed in the manifest) | Reversible: yes
- A-18 | Profile name grammar | Resolved: `^[a-z0-9]+(-[a-z0-9]+)*$` | Source: spec 10 REQ-43 | Reversible: yes
- A-19 | Marker wording | Resolved: neutral `BEGIN/END MANAGED PROFILE` markers without the product name | Source: `.ai/principles/architecture.md` P8 | Reversible: yes
- A-20 | Profile conflict handling | Resolved: all-or-nothing with `--adopt`; deleted files stay deleted | Source: A-06 consistency; best practice (respect a user's deletion) | Reversible: yes
- A-21 | Profile upgrades in registered projects | Resolved: only by re-running setup with `--profile`; sync and install never touch project profiles | Source: ADR-0009 Decision 6 (setup copies profiles); smallest choice | Reversible: yes
- A-22 | Interactive stack prompt | Resolved: removed | Source: original REQ-08 (explicit `--profile`); ADR-0009 Decision 6 | Reversible: yes
- A-23 | What "neutral" means for the two core files | Resolved: no stack term anywhere in `principles/*.md`; stack-specific examples rewritten as language-neutral `text` pseudocode, originals moved verbatim to `profiles/python-fastapi/principles/code-examples.md` | Source: original §5 ("stack examples are allowed in an explicitly chosen profile"); REQ-07 | Reversible: yes
- A-30 | Test location | Resolved: standalone `scripts/check-install.py` (suite A; spec 11 adds `scripts/check-public-readiness.py`), not registered in the validator | Source: ADR-0019 Decision 3; spec 10 Scope item 8 | Reversible: yes
- A-31 | Validator edits | Resolved: bodies only, outside the pinned region, expressions untouched, then re-pin | Source: `tests/fixtures/validator-runtime/oracle.py:160-252`; ADR-0020 Decision 2 | Reversible: yes
- A-38 | Project skill links after uninstall | Resolved: left untouched (they belong to projects; spec 13's pass removes broken links) | Source: REQ-35; `scripts/sync.sh:226-239` | Reversible: yes
- A-39 | Platform | Resolved: Linux and macOS local filesystems | Source: `scripts/install-hooks.py:16` (`fcntl`); spec 10 Non-Functional Requirements | Reversible: yes
- A-40 | Installed and backup modes | Resolved: installed files 0644; bookkeeping 0600/0700; restore uses the recorded mode | Source: best practice | Reversible: yes
- A-45 | How a later spec's rows enter spec 13's signed DM-20 record (2026-11-16) | Resolved: this delivery appends its `## Superseded checks` rows and one further `Signed:` line by its own independent validator below the existing one; earlier rows and signatures are not changed | Source: spec 13 REQ-69 (a later spec adds verdict rows in its own delivery) and DM-20 (record ends with a `Signed:` line); smallest additive choice | Reversible: yes
- A-42 | Which command reports leftover skills after `deploy` is removed (2026-11-14) | Resolved: the installer, on `install` and `--dry-run` (REQ-79), fed by `deployment-set`'s `leftover_candidates`; not an additional `deploy-skills.py` subcommand, so that REQ-71's subcommand set and the public installer's output stay the single place a user sees the lines | Source: spec 13 REQ-57 and Notes → Relationship to spec 11a (leftover reporting must survive `deploy`); spec 13 Terminology → Leftover skill | Reversible: yes

## Decisions

N/A — the owner decisions D-01–D-04 of 2026-11-14 concern licensing, translations and CI and
are recorded in spec 11; no decision was taken for this part.

## Clarifications

N/A — no questions were asked for this part; the 2026-11-14 session is recorded in spec 11.

### Session 2026-11-16

- N/A — autonomous refinement after the split; no question was asked. Resolved gaps are
  recorded as A-16 (amended) and A-45, the new requirements REQ-82–REQ-85 and AC-44.

## Open Questions

- Q-04 | resolved 2026-11-13 | Spec 13 now specifies `scripts/deploy-skills.py`, DM-6 deploy
  manifests and DM-7 journal and lock; the mapping is under Contracts → Relationship to spec
  13's deployment engine. Discovery of this spec re-verifies it against the delivered spec 13.
- Q-06 | non-blocker (external precondition owned by spec 13) | The frozen checks that pin
  the text of `scripts/sync.sh` and `scripts/setup-new-project.sh`
  (`scripts/validate-contracts.sh:953-957`, `:1166-1179`, `:1293-1320`, as spec 13 re-points
  them for its own sync and setup) must be re-pointed before REQ-04 can pass.
  Spec 13 is final and defines the mechanism: `tests/fixtures/validator-runtime/inventory-amendment.json`
  with `"schema": 2` and the lists `path_changes` and `contract_changes` (its DM-9; REQ-51
  and REQ-52; A-02). What this spec needs amended is exactly the checks that, once spec 13
  is delivered, assert text this spec changes: in `sync.sh`, the separate hook-installation
  step and the `deploy-skills.py deploy --hook-result` step (replaced by the launcher call and
  `project-pass`, REQ-04, REQ-64, REQ-71); in `setup-new-project.sh`, the interactive stack
  prompt and standards injection (replaced by `--profile`, REQ-08, REQ-51); and any check
  that names a rule file literally in either script if spec 13's delivery still leaves one
  (spec 11's REQ-61 rule file is spec 11's own `contract_changes` entry, `spec-11 REQ-61`, in its delivery; this spec adds none for it). This spec's Discovery lists them by running the
  oracle against the delivered spec 13. These changes are semantic, so they are
  `contract_changes` entries, not `path_changes` (which spec 13's mask accepts only for
  name-only differences). The precondition is met by spec 13's text for the mechanism but
  not for these entries: the closed set of `requirement` values (spec 13's own REQ-05, REQ-06,
  REQ-09, REQ-10, REQ-11, REQ-12, REQ-14, REQ-15, REQ-23, REQ-36, REQ-55, REQ-66) is
  hard-coded in the oracle test and cannot name a requirement of this spec, and each entry also needs a
  verdict row in the `## Superseded checks` table of spec 13's DM-20 record. Impact: this spec
  extends the closed set under spec 13 REQ-69 with values of the form `spec-11a REQ-NN` in
  `tests/validator-runtime-oracle.py` (updating `AMENDMENT_SHA256` and the source-guard records), appends its entries and their DM-20 rows, and states it in
  this spec's delivery ADR; if spec 13 is delivered without DM-9 schema 2, Discovery stops.
  The value `spec-11a` needs spec 13 REQ-69's prefix grammar to accept a letter after the
  number; that grammar change is made to spec 13's text in the change that splits this spec
  out, so it is not a blocker. DM-20 rows are appended as A-45 states.

## Notes

- **Preconditions (checked at Discovery):** spec 13 (`deploy.env`, installed-name map,
  active-task rule, retired Windsurf targets; the active-task rule is delivered in
  `deploy-skills.py` (spec 13 REQ-43, DM-8) and consumed through `deployment-set`; and the
  checks listed under Context → Constraints that pin sync and setup text have been retired or
  rewritten through an accepted inventory change, Q-06; spec 13 DM-9) and spec 10
  (`gen-docs.py --check`, `--profile`, generated `harness/<name>/always-on.md`, sync deployment
  contract). Missing → Discovery stops.
- **Relationship to spec 11:** spec 11 starts after this spec is reviewed. It documents this
  spec's command lines, profiles and optional features, its release check runs
  `scripts/check-install.py`. Spec 11 adds its own inventory entry, `spec-11 REQ-61`, for its
  rule file (spec 11 Q-07); this spec adds none for it.
- Hint (nonbinding): subtasks — (1) manifest, plan and classification with suite A fixtures;
  (2) apply, journal, recovery and fault seam; (3) uninstall; (4) hook plan operation,
  launcher and sync delegation with source-guard re-pinning; (5) neutral core and profiles.
- Ownership of the sync gates: this spec owns the position of the validator, generator and
  meter gates in `scripts/sync.sh` after its delivery (REQ-64); spec 10 owns the generator
  command and its exit semantics and spec 08 the meter command (spec 10 REQ-22, A-48).
- Hint (nonbinding): keep classification, planning and applying as separate functions of the
  engine so suite A can test classification tables without subprocesses.
- Shared acceptance gates G1–G8 apply (`.ai/specs/README.md` → "Shared acceptance gates"); G6
  is met by the standalone suite; no paid run is needed.
- Rejected alternatives: a managed region inside the global instruction files (spec 10 and
  ADR-0009 define whole-file always-on deployment); partial installs on conflict; a second
  ownership mechanism for hook settings; `install.sh` at the repository root (A-02);
  interactive profile prompts; automatic profile upgrades during sync.
- **Follow-up for other specs (not changed here):** spec 13 records that its REQ-10, REQ-42
  and REQ-45 for global targets are delivered by this engine and that its project pass never
  refreshes profiles (its Notes → Relationship to spec 11a; A-21).
- **Changed with the split (same change):** spec 13 REQ-69's `requirement` grammar accepts a
  letter after the spec number (`spec-11a REQ-NN`, Q-06); `.ai/specs/README.md` lists this spec
  as its own roadmap row before spec 11; citations in specs 08, 10 and 13 of identifiers that
  moved here name spec 11a.

## Change Log

### 2026-11-16 — split from spec 11

- Created from Part A of `.ai/specs/11-open-source-readiness.md` at `e3ba41a`: Context,
  Scope items 1–7, the installer and profile requirements, Data Model, Contracts, Edge Cases,
  acceptance criteria, Traceability rows, Risks, Assumptions and Q-04/Q-06 moved without
  renumbering. The history of these texts before the split is the Change Log of spec 11.
- Q-06 now names `spec-11a REQ-NN` as the closed-set value; spec 11 keeps its own entry for
  its REQ-61 (spec 11 Q-07).
- Same day, `/spec-draft --auto-mode` review loop with an independent critic (3 rounds: 56, 92,
  99/100): REQ-49, REQ-50, REQ-34 and REQ-43 corrected; REQ-80 split into REQ-80, REQ-84 and
  REQ-85; new REQ-82 (setup runtime guard) and REQ-83 (writable parents); new AC-44 (sync
  gates); AC-04, AC-08, AC-28, AC-29, AC-30, AC-31 and AC-32 sharpened; the pause test seam,
  the dry-run `installation_id`, the recovery step object, the uninstall hook plan and the
  `directory-kept` exit rule defined; Scope item 8 and the translation of original §4, §5 and §8
  added; A-45 added and A-16 amended.

## Readiness Checklist

Result of 2026-11-16 (first review after the split).

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — installer, ownership record, maintainer deployment and profiles in one paragraph |
| 2 | Out of Scope names concrete exclusions | PASS — spec 11's materials, owner actions, paid runs, spec 13 and 10 ownership and others named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — 62 requirements; REQ-80 split into REQ-80, REQ-84, REQ-85; new REQ-82, REQ-83 |
| 4 | Every REQ maps to an AC and every AC names a REQ | PASS — Traceability covers every requirement and all 29 criteria |
| 5 | Every AC is binary and testable before implementation | PASS — fixture-based Given/When/Then with the fault, pause and foreign-user test seams |
| 6 | Non-functional targets measurable or N/A | PASS — each NFR row names its suite A verification |
| 7 | Data model and contracts specified | PASS — locations, manifest, journal, plan, profile manifest and record, markers, CLIs, exit codes, diagnostics, classification, apply order, recovery |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — Edge Cases table and classification tables, including uninstall migration and the interrupted first install |
| 9 | Every ambiguity recorded | PASS — A-01–A-23, A-30, A-31, A-38–A-40, A-42, A-45; Q-04 resolved, Q-06 open |
| 10 | No blocker question remains | PASS — Q-06 is a non-blocker; the spec 13 grammar it needs is in spec 13's text |
| 11 | Every existing-code claim cited and verified | PASS — citations checked by the critic against `e3ba41a` (code unchanged since `060ce6d`) |
| 12 | Terminology matches domain definitions | PASS — "ownership manifest" qualified throughout next to spec 13's deploy manifests |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — about five to six subtasks (Notes hint) |
| 14 | Devil's Advocate review passed | PASS — Review: 3 rounds, score 99/100, critic: sub-agent, open: none (minor F-21 applied after the final round) |

**Verdict: READY FOR DEVELOPMENT.** Automated readiness is not sign-off.

