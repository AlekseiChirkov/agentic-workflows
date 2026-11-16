# 11. Public materials and first stable release readiness

## Source

- **Split (2026-11-16):** at commit `e3ba41a000c927ac157fd2207df413107ed54cb5` this file
  held Parts A and B of one specification and failed readiness check 13 (feature size). On the
  owner's request of 2026-11-16 (translated from Russian: "they are very large and must be
  split in two if this can be done logically; then run each resulting spec through
  `/spec-draft`") Part A, installer and profiles, moved to
  `.ai/specs/11a-public-installer-and-profiles.md`; Part B, public materials and release
  readiness, stays here. Identifiers keep their numbers and each is defined in exactly one of
  the two files. The Source history below, including the translation of the original request,
  covers both parts and is the canonical copy that spec 11a cites.
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
- **Roadmap position:** `.ai/specs/README.md` → "Dependency order" — order 17 after the split (16 before it), prerequisites 01, 09, 10, 11a,
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

**Public materials are minimal.**
- `README.md` has 26 lines. There is no `LICENSE`, no `CONTRIBUTING.md`, no `.github/`, no
  `docs/examples/`, no optional-feature or release-checklist document, and no git tag
  (`git tag -l` is empty). `VERSION` contains `0.9.0`.
- There is no public installer, no uninstall, no dry run and no profile mechanism;
  spec 11a delivers them, and this spec documents them (11a → Context & Problem).
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
  `tests/fixtures/validator-runtime/README.md:9-27` (ADR-0020 Decision 2).
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
  and spec 11a REQ-04 contradict these expressions, which the current inventory cannot amend; spec 13 introduces a schema-2 inventory amendment (its DM-9) for
  changing existing expressions. REQ-61's new rule file meets the per-rule runtime checks of
  `:1293-1305` by joining the per-rule deployment lists those checks guard, when they still
  exist (REQ-86, Q-07).
- The identity scan compares every occurrence of the former repository name against an
  exact ledger of `(path, line, count)` rows
  (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:184-208`), including
  `docs/USAGE.md:254` (`:204`) and line-pinned rows for both `.ru.md` files (`:200-203`). An
  edit that adds an occurrence or moves a listed line fails the scan until the ledger row is
  updated in the same change.

**Precedent for previews.** `/spec-run --dry-run` reports without project writes, branches,
commits or pull requests, with best-effort telemetry as its only write exception
(`workflows/spec-run.md:10-11`, `:50-51`). `/phase-discovery` and `/bugfix` have no dry run
(`workflows/phase-discovery.md:5`, `workflows/bugfix.md:5`).

**Consequence:** an external user has no getting-started path that explains the installer,
profiles and optional features, no contribution guide and no worked example; agents have no
preview mode for Discovery and defect fixing; and the owner has no verifiable release
candidate to authorize.

## Goal

On top of the installer and profiles of spec 11a, the repository offers the getting-started,
optional-feature, contribution, worked-example and preview (dry-run) materials, an offline CI
workflow and a release checklist with an offline release check, so that the owner can
authorize a first stable release from a fully verified candidate, without this work bumping
the version, tagging, publishing or changing remote settings.

## Scope

Requirements carry the tag **[B]** of the earlier combined specification; every requirement
of this file is a [B] requirement. Scope items 1–7 moved to spec 11a; the numbering of the
remaining items is kept.

8. `README.md` rewrite, `docs/USAGE.md` sections 1, 2, 4, 5, 8 and 9, `docs/OPTIONAL-FEATURES.md`,
   `docs/CONTRIBUTING.md`, `.github/` issue and pull-request templates, translation
   provenance lines in the two `.ru.md` analysis records.
9. `docs/examples/flat-task/` built from spec 09's `flat` reference workspace.
10. The dry-run contract as the new on-demand rule `rules/contract-dry-run.md`, applied by the
    Discovery orchestrator and `/bugfix` and cited by `/spec-run`.
11. `docs/RELEASE-CHECKLIST.md`, `scripts/release-check.sh`, the onboarding measurement record
    and the first release-candidate report. The report and the onboarding record are made after
    this spec's pull requests are merged, on a `main` commit, and land in a follow-up pull
    request that changes only `docs/audits/`; they are release preparation, not part of the
    implementation's acceptance (AC-15 and AC-16 test them on synthetic fixtures; their first
    real instances are release gates).
12. The standalone acceptance suite `scripts/check-public-readiness.py`.
13. The offline CI workflow `.github/workflows/offline-checks.yml` (REQ-81).

**Delivery records:** the generated references regenerated with
`python3 -I scripts/gen-docs.py --write --root .` after the REQ-61 and REQ-62 edits and
committed with them (spec 10 REQ-06; the implementer runs it, this spec's scripts never do);
the root-listing amendment of
`.ai/principles/coding.md → Document placement` (`:83-85`) adding `.github/` (spec 11a adds
`profiles/`), naming its `workflows/` and `ISSUE_TEMPLATE/` subdirectories and the pull-request template, `scripts/README.md` and `docs/README.md` rows,
`.ai/memory/architecture.md`, `.ai/context/environment.md`, `.ai/context/runbook.md`, the
re-pinned source-guard records, the identity-ledger rows of every edited file that holds a
ledger token, and one ADR recording the decisions marked "ADR at delivery" under
Assumptions. The ADR also records the departure from the literal wording of ADR-0009
Decision 6 (originals kept only in history at pinned blobs, D-02) and the CI workflow decision
(D-03); if the ADR process prefers a note appended to ADR-0009 instead, the departure is
recorded there and the ADR cites it. The record also states that the optional CI secret and manual dispatch of ADR-0009 Decision 6 are not used by REQ-81.

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
- The installer, ownership manifest, uninstall, `sync.sh` delegation, neutral core and
  profiles: owned by spec 11a. This spec documents and tests them only through their public
  commands.
- The generator, the always-on composition bytes and `docs/harness-matrix.md`: owned by spec
  10. This spec consumes `--check` and the generated references.
- Registering checks in `scripts/validate-contracts.sh` (frozen inventory).
- Re-creating the Russian originals in the working tree (A-27; owner-confirmed, D-02).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| External user | Reads `README.md`, `docs/USAGE.md` and `docs/OPTIONAL-FEATURES.md`; runs the commands of spec 11a they describe |
| Maintainer | Runs `scripts/check-public-readiness.py` and `scripts/release-check.sh`; prepares release-candidate reports |
| Owner | Supplies the copyright-holder wording, authorizes a specific version, tag, publication, golden runs and any remote-setting change |
| Contributor | Follows `docs/CONTRIBUTING.md`; opens issues and pull requests with the `.github/` templates |
| Generator (`scripts/gen-docs.py`, spec 10) | Answers `--check`; never invoked with `--write` by this spec's scripts |
| Implementer / reviewer | Builds and validates this spec in disposable directories; never deploys into a real home during tests |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Harness | A directory `harness/<name>/` holding spec 13's `deploy.env`; `skills_dir` and `always_on_path` are its deploy paths | Spec 13 REQ-35 |
| Profile | A directory `profiles/<name>/` with `profile.json`, its files and `always-on-fragment.md` | ADR-0009 Decision 6 |
| Optional feature | A capability that works only with an extra prerequisite or explicit enablement (rows of `docs/OPTIONAL-FEATURES.md`) | Original REQ-01 |
| Delivery state | `delivered`, `partial` or `planned` for an optional feature | This spec |
| Cost basis label | `subscription billing`, `API-equivalent`, `unknown`, `measured`, `hypothetical` | Original REQ-02; `.ai/specs/README.md` → "Shared acceptance gates" (G8) |
| Reference workspace | Spec 09's hand-authored correct result of a golden case and its run-log store, built by `golden-eval.py build-reference` from `reference/<workflow>/overlay/` and `history.json` | Spec 09 DM-1 |
| Dry-run contract | The canonical `## Dry-run contract` section defined by REQ-61 | This spec |
| Release candidate | One source commit proposed for release, with its candidate report | This spec |
| Release item | One row `RC-NN` of `docs/RELEASE-CHECKLIST.md` | This spec |
| Candidate report | `docs/audits/<date>-release-candidate-<version>.md` | This spec |
| Onboarding measurement | `docs/audits/<date>-onboarding-measurement.md` | Original §6 |

Installer and profile terms (engine, ownership manifest, installed state, managed fragment and
others) are defined in spec 11a → Terminology.

Rejected synonyms: "stack overlay" for a profile; "golden test" for the example (it is a copy
of a reference workspace, not a test). Spec 11a lists the installer synonyms it rejects.

## Requirements

Identifiers REQ-01–REQ-17 keep their 2026-10-28 subjects; behaviours the earlier text bundled
into one item are split into REQ-18 onward, noted in parentheses. "The engine" is spec 11a's
`scripts/install.py` reached through `scripts/install.sh`; "suite A" is spec 11a's
`scripts/check-install.py` and "suite B" is `scripts/check-public-readiness.py`. Identifiers
are unique across this file and spec 11a: a new identifier takes the next number unused in
either file.

### Identifiers defined in spec 11a

REQ-03–REQ-09, REQ-18, REQ-20–REQ-53, REQ-64–REQ-71 and REQ-73–REQ-80; AC-02–AC-08, AC-17,
AC-19–AC-33 and AC-38–AC-42; A-02–A-23, A-38–A-40 and A-42; Q-04 and Q-06. A citation of one
of them in this file names spec 11a. A-01, A-30 and A-31 apply to both files and are repeated
in each.

### Original requirements, restated

- **REQ-01 [B] Optional-feature documentation.** THE SYSTEM SHALL provide
  `docs/OPTIONAL-FEATURES.md` with one table row per required optional feature (Data Model →
  Optional-feature table) stating its delivery state, prerequisites, how to enable it, how
  work proceeds without it, how to disable and resume it, and evidence paths.
- **REQ-02 [B] Cost labelling.** THE SYSTEM SHALL carry, on every line of `README.md`,
  `docs/*.md` and `docs/examples/**` that contains a money figure (Data Model → Money
  figure), at least one backticked cost basis label.
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
  token (Data Model → Contribution guide) exists.
- **REQ-13 [B] Discovery and bug-fix previews.** WHEN the Discovery orchestrator or `/bugfix`
  is invoked with `--dry-run`, THE SYSTEM SHALL follow the dry-run contract (REQ-61) and
  report the workflow-specific items of REQ-62.
- **REQ-14 [B] Hygiene re-check.** WHEN `scripts/release-check.sh` runs, THE SYSTEM SHALL
  report release item RC-08 as `pass` when the standalone hygiene scan with a resolved local
  pattern file exits 0, `fail` when it exits non-zero, and `not-verified` when no pattern
  file is resolved, when the resolved file is missing or unreadable, or when
  `ORCHESTRAIL_HYGIENE_DENYLIST` is set but empty.
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

### Release check

- **REQ-19 [B] Release check is read-only and offline (split from REQ-03).** WHEN
  `scripts/release-check.sh` runs, THE script SHALL NOT itself invoke `gh`, `claude`,
  `codex`, `curl` or `wget`, SHALL NOT create, move or delete any git ref or tag, and SHALL
  leave every tracked file and every untracked file not matched by `.gitignore` unchanged,
  running every sub-suite with `PYTHONDONTWRITEBYTECODE=1` and every git command with
  `GIT_OPTIONAL_LOCKS=0`. (Test doubles that a sub-suite
  places on its own `PATH` are part of that suite.)

### Public materials and release

- **REQ-54 [B] Links resolve.** THE SYSTEM SHALL resolve every relative Markdown link target
  in `README.md`, `docs/OPTIONAL-FEATURES.md`, `docs/CONTRIBUTING.md`,
  `docs/RELEASE-CHECKLIST.md`, `.github/**/*.md` and `docs/examples/flat-task/*.md` to an
  existing file or directory of the repository, after removing any `#fragment` (fragments
  are not checked).
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
  from the release status vocabulary and evidence, and SHALL state verdict `ready` if and only if
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
  preview, install, adopt and uninstall commands of `scripts/install.sh` and where `--adopt`
  keeps backups (`install-backups` and `adopted-backups` under the user's state directory, spec
  11a → Data Model → Locations) and how `--uninstall` restores them, in section 5 the
  `--profile` option, and in section 8 upgrading by re-running the installer; SHALL state in
  sections 1, 2, 8 and 9 (today `docs/USAGE.md:20-21`, `:111-113`, `:658`, `:759-761`) that the core
  principles are `code-quality.md` and `testing-standards.md` and that Python and
  infrastructure standards come from the `python-fastapi` profile; and SHALL keep the
  statements `test_public_setup_guide_uses_orchestrail_release_instructions` requires.
### Requirements added in the 2026-11-13 and 2026-11-14 reviews

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
- **REQ-86 [B] Validator stays green with the new rule (new 2026-11-16).** WHEN
  `rules/contract-dry-run.md` is added, THE SYSTEM SHALL keep `bash scripts/validate-contracts.sh`
  exiting 0 on the delivering commit: where a still-registered check guards a per-rule
  deployment list (today the project rule copies of `scripts/setup-new-project.sh` and the
  refresh of `scripts/sync.sh`, `scripts/validate-contracts.sh:1293-1305`), THE SYSTEM SHALL add
  the new file to that list so that it is deployed exactly like every other rule, and re-pin
  those scripts' digests; a comment or string that only satisfies the check is not allowed;
  where spec 13 retired that deployment and its check, no edit is made. THE SYSTEM SHALL NOT
  change any check expression for it (Q-07).
- **REQ-81 [B] Offline CI workflow (new 2026-11-14, D-03).** THE SYSTEM SHALL provide
  `.github/workflows/offline-checks.yml` whose `on:` block lists `pull_request`, `push` with
  `branches: [main]` and `schedule` with one weekly cron, with `permissions: contents: read` at
  workflow level, and two jobs: `offline-checks` with `if: github.event_name != 'schedule'`, and
  `full-validator` with `if: github.event_name == 'schedule'`, which runs
  `bash scripts/validate-contracts.sh` (RC-02) alone, so the 34–52 minute full validator never
  blocks a pull request (D-04). The workflow runs offline and starts no paid model run: no step reads a `secrets.` value or invokes
  `claude` or `codex`, and the workflow neither uses `pull_request_target` nor offers a
  credentialed manual dispatch (`.ai/specs/README.md` → "Shared acceptance gates", G6). Each
  job SHALL set up the same environment, from what the repository states: a full-history checkout (the
  translation-blob checks of AC-14 and RC-01's `git diff` need history); `bash`, `git`, `jq`
  and `flock` (`.ai/context/runbook.md → Commands`: native hooks keep Bash/jq/flock
  dependencies, timing needs jq); Python 3.12 as `python3`, because the installer and timing
  engines need 3.11 or newer and the runbook names `MISE_PYTHON_VERSION=3.12.16` as the
  explicit version for isolated-PATH fixtures (the job exports that variable so a mise shim,
  if ever present, resolves instead of failing with `No version is set for shim: python3`);
  and `pytest` (spec 09 REQ-35: without it the golden-run suite exits 3). `offline-checks` SHALL then run,
  in this order and failing the job on any non-zero exit, the commands of RC-03–RC-06 (not RC-02,
  which only `full-validator` and the release checklist run) and,
  as the last step, `python3 -I tests/golden-runs.py` (RC-07) only when `tests/golden-runs.py`
  exists: a shell test `[ -f tests/golden-runs.py ]` guards the step, and when the file is
  absent the step prints a notice that the suite is absent and exits 0, so the workflow does
  not fail before spec 09 is delivered; an absent suite is not a pass of RC-07, which stays
  `not-verified`. When the file exists, every non-zero exit, exit 3 included, fails the job.

## Data Model

All JSON files below are UTF-8, written with sorted keys, two-space indentation and a final
`\n`; readers key on field names and reject unknown keys (the rule of spec 11a REQ-41). Hashes are lowercase hex
SHA-256 of exact bytes. All files and directories below are new unless marked existing.

### Optional-feature table (`docs/OPTIONAL-FEATURES.md`)

Header row exactly `| Feature | State | Prerequisites | Enable | Without it | Disable and resume | Evidence |`.
Required rows (first cell exact): `Native logging hooks`, `Git rails hook`, `Model catalog
and selection`, `Usage telemetry`, `Exact run timing`, `Stack profiles`, `Generated
references`, `Golden runs`, `State tool`. `State` is one of `delivered`, `partial`,
`planned`: `delivered` when the feature's owning specification is under `.ai/specs/completed/`;
`partial` when it is not but at least one implementing file the row names exists; `planned`
when no implementing file exists. `Evidence` names the owning specification first, as the path under `.ai/specs/` or
`.ai/specs/completed/` that exists; an implementing file is any other Evidence path. Owning
specifications: `Native logging hooks` and `Exact run timing` — 03 (hook-based logging);
`Git rails hook` — 06; `Model catalog and selection` — 04; `Usage telemetry` — 05; `Stack
profiles` — 11a; `Generated references` — 10; `Golden runs` — 09; `State tool` — 07. A change
that archives an owning specification to `.ai/specs/completed/` updates the row's `State` and
Evidence path in the same change; suite B failing on a stale row is the intended signal. `Evidence` lists backticked
repository paths; for `delivered` and `partial` every path exists. For `planned`, `Enable`
is exactly `not available`. The document also has `## Cost and usage figures` defining the
five cost basis labels and `## Capability declarations` linking `harness-matrix.md` and
stating that declared support, installation result and checkpoint coverage are distinct, and
`## Platform support` stating that Linux local filesystems are verified and that macOS is a
design target this release does not verify (spec 11a → Non-Functional Requirements,
Portability).

### Money figure

A line matching `\$\s?[0-9]` or `\b[0-9][0-9.,]*\s?USD\b` after fenced code blocks and inline
code spans are removed from it.

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
example's source case can never be a holdout task. The built workspace must hold exactly one
file under `.ai/specs/`; with none or more than one, Discovery stops and reports it, because
spec 09 owns the case content.

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
`## Audit method` (in its own words: an audit is run by a reviewer independent of the change,
its report is `docs/audits/YYYY-MM-DD-<slug>.md` indexed in `docs/README.md`, and actionable
findings become specs; it links `.ai/context/runbook.md` for the commands and states that the
audit-prompt file the runbook names, `docs/audits/AUDIT-PROMPT.md` at
`.ai/context/runbook.md:103`, is not in the tree, so the auditor writes the request; that one
file name is written in plain text, not in backticks, so the path-token rule does not apply to
it), `## Deployment boundary`
(never edit deployed copies; `sync.sh` is the maintainer command; contributors use
`install.sh --dry-run`; tests use disposable homes).

Repository path token (REQ-12, AC-11): inside a backticked span, each whitespace-separated
word whose first `/`-separated segment is a top-level entry of the repository (`.ai`,
`.github`, `docs`, `harness`, `hooks`, `principles`, `profiles`, `rules`, `scripts`,
`templates`, `tests`, `workflows`) or that equals `README.md` or `VERSION`; a word containing
`<`, `>`, `*`, `{` or `~`, or starting with `-` or `$`, is not a path; a trailing `:` and line
suffix (`:12`, `:12-20`) is removed before the check.

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
| RC-03 | `python3 -I scripts/gen-docs.py --check --root .` exits 0 | automated |
| RC-04 | `python3 -I scripts/check-install.py` exits 0 | automated |
| RC-05 | `python3 -I scripts/check-public-readiness.py` exits 0 | automated |
| RC-06 | `bash scripts/check-spec-draft.sh` and `python3 -I scripts/check-gen-docs.py` exit 0 | automated |
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
commit — a commit of the default branch `main`, after any pull request that carries the
candidate's changes is merged (under a squash or rebase merge, the resulting `main` commit) —
intended version, table `| Item | Status | Evidence |` with RC-01–RC-16, verdict line
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

The installer and setup command lines are in spec 11a → Contracts & Interfaces → Command lines.

```text
bash scripts/release-check.sh [--denylist <file>]
python3 scripts/check-public-readiness.py
```

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
3. **Telemetry only.** The only write exception is optional, best-effort run-log telemetry
   under the workflow's own `--pipeline` value when it already logs runs: `run-start`, one
   `--step dry-run --outcome skipped --note approximate`, `run-end --outcome completed`. A dry
   run nested under a parent run logs nothing of its own.
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
`scripts/validate-contracts.sh:350-366` does (`--denylist` overrides); a resolved path that is
missing or unreadable, and a set but empty `ORCHESTRAIL_HYGIENE_DENYLIST`, give RC-08
`not-verified` without a scan; otherwise the file is passed to
`validate-contracts.sh --hygiene-only --denylist <file>`, and its exit 0 or non-zero gives
`pass` or `fail`. It prints
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
- REQ-86 adds `rules/contract-dry-run.md` to the per-rule deployment lists of `scripts/sync.sh`
  and `scripts/setup-new-project.sh` when a still-registered check guards them, then re-pins
  both digests
  (`tests/fixtures/validator-runtime/README.md:9-27`); it changes no check.
- Every edit that moves a ledger-pinned line or adds a ledger token updates the matching
  row of the identity ledger in the same change.

## Non-Functional Requirements

| Attribute | Target / standard | Verification |
|---|---|---|
| Network and models | No network connection, model or harness CLI invocation by `release-check.sh` or suite B | AC-18 (the release check with stubbed suites, and suite B itself under the recording `PATH`) |
| Isolation of tests | Suite B uses disposable `HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, never the real home | AC-18: suite B run under a fake `HOME` leaves the checkout and that `HOME` unchanged outside its temporary directory |
| Performance | N/A — no owner-given target; the 15-minute onboarding figure is a recorded target, not a gate (A-33) | RC-09 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| Release check without a local pattern file | RC-08 `not-verified`, exit 1 | REQ-14 |
| `--denylist` names a missing or unreadable file | RC-08 `not-verified` with evidence `pattern file unreadable: <path>`, exit 1 | REQ-14 |
| `ORCHESTRAIL_HYGIENE_DENYLIST` set but empty | RC-08 `not-verified` (explicitly unset, as the validator's resolver returns 1), exit 1 | REQ-14 |
| `ORCHESTRAIL_HYGIENE_DENYLIST` names a missing file | RC-08 `not-verified` with evidence `pattern file unreadable: <path>` (the scan is not started), exit 1 | REQ-14 |
| Squash or rebase merge of the candidate's pull request | The default-branch commit that results is the candidate; RC-01 and the report are made on it | REQ-59 |
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
  `docs/examples/flat-task/`, When suite B runs, Then the header row is exact, the section
  `## Platform support` contains `Linux` and `macOS`, each of the nine
  required features has exactly one row, every `State` is in the vocabulary and agrees with
  the state rule of Data Model → Optional-feature table, every evidence
  path of a `delivered`/`partial` row exists, every `planned` row's `Enable` is `not
  available`, every money-figure line in scope has a cost basis label, and every `Duration`,
  `Tokens` and `Cost` cell of `run-log-summary.md` is `unknown`; and each mutation — a
  `planned` row with other `Enable` text, an unlabelled `$5` line, a `0` cost cell — makes
  suite B fail naming the file.
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
  appear in order, every repository path token
  (Data Model → Contribution guide) exists, and
  `gen-docs.py --check` exits 0 (the matrix is current and generated).
- **AC-12** (REQ-13, REQ-61, REQ-62, REQ-86) — Given the delivered rules and workflows, When suite B
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
  offline. And on the delivering commit `bash scripts/validate-contracts.sh` exits 0 (REQ-86). And, in a disposable
  fixture project, the surviving setup and sync deployment place `contract-dry-run.md` wherever
  they place `tdd.md` (skipped, with the reason recorded, when spec 13 retired that deployment).
- **AC-13** (REQ-14) — Given fixture checkouts (git repositories with the release-check script)
  where (a) a pattern file is resolved and no tracked file matches, (b) a tracked file matches,
  (c) no pattern file is resolvable, When `release-check.sh` runs with the other suites stubbed
  to exit 0 — the fixture's `scripts/validate-contracts.sh` is a wrapper that, when its first
  argument is `--hygiene-only`, runs the real validator's hygiene mode with `--root` set to the
  fixture checkout and the same remaining arguments, and otherwise exits 0; the other suites
  and `tests/golden-runs.py` are stubs exiting 0 — Then RC-08 is `pass`,
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
  the `not-verified` and `blocked` rules; and suite B, run on a synthetic candidate report
  fixture, accepts it only when each of them has a status in the vocabulary with evidence
  (the first real report is a **release gate**, Scope item 11).
- **AC-16** (REQ-17, REQ-59) — Given each candidate report (synthetic fixtures for implementation
  acceptance; the first real report is a **release gate**, Scope item 11), When suite B runs, Then it lists
  RC-01–RC-16 once each with a vocabulary status and non-empty evidence; RC-16 is
  `owner-decision-pending`; RC-14 is `pass` only when `LICENSE` exists at the report's
  candidate commit and `owner-decision-pending` otherwise; RC-15 is `pass` only when `VERSION`
  at the candidate commit is not `0.9.0` and its evidence matches
  `^owner authorization [0-9]{4}-[0-9]{2}-[0-9]{2}: ".+"$` (the date and the owner's words),
  and `owner-decision-pending` otherwise; and the verdict is `ready` if and only if RC-01–RC-15
  are `pass`. Given synthetic reports for a `0.9.0` candidate and for a release-preparation
  candidate, suite B accepts both and rejects each with one rule broken. And Given the tree that
  delivers this spec (before any REQ-72 commit), the acceptance run finds `VERSION` `0.9.0`, no
  `LICENSE` and no tag `v1.0.0` (a one-time check, not a suite B rule).
- **AC-18** (REQ-19) — Given a fixture checkout with stubbed suites that record their
  environment and a `PATH` whose `gh`, `claude`, `codex`, `curl` and `wget` append to a record
  file, When `release-check.sh` runs, Then the record file is empty, every stub saw
  `PYTHONDONTWRITEBYTECODE=1` and `GIT_OPTIONAL_LOCKS=0`, `git for-each-ref` output and the
  snapshot of every tracked file and every untracked file not matched by `.gitignore` are
  unchanged (`.git/` and ignored paths are outside the snapshot), and the printed table has
  rows RC-01–RC-16; and Given the real suite B run once under the same recording `PATH` and a
  fake `HOME`, Then the record file stays empty and the checkout snapshot and the fake `HOME`
  outside the suite's temporary directory are unchanged.
- **AC-34** (REQ-57) **release gate** — Given a person who performs the onboarding procedure
  of `docs/RELEASE-CHECKLIST.md` in a fresh environment with a stopwatch, When suite B runs
  afterwards, Then one onboarding measurement record exists whose `Candidate commit` is an
  ancestor of `HEAD`, every field is non-empty, and `Target 15 minutes` is `met` or `not met`
  with a cause. The implementation's part is the procedure text in the checklist (AC-15) and
  suite B's validator for the record, tested on a synthetic record fixture.
- **AC-35** (REQ-60) — Given a fixture checkout built as in AC-13 case (a), with every other
  automated item's command stubbed to exit 0 and `tests/golden-runs.py` a stub exiting 0, When `release-check.sh` runs, Then it exits 0 and prints RC-01–RC-08 as `pass`,
  RC-09 and RC-11–RC-13 as `not-verified`, and RC-10 and RC-14–RC-16 as
  `owner-decision-pending`; with RC-03's command stubbed to exit 1, Then RC-03 is `fail`,
  the remaining items still run, and the exit code is 1.
- **AC-36** (REQ-63) — Given `docs/USAGE.md`, When suite B and the existing check
  `test_public_setup_guide_uses_orchestrail_release_instructions` run, Then the check passes,
  section 4 contains `scripts/install.sh --dry-run`, `--adopt`, `--uninstall`, `install-backups`
  and `adopted-backups`, section 5
  contains `--profile`, section 8 contains `scripts/install.sh`, and in sections 1, 2, 8 and 9 every line (prose
  line, table row or tree entry) that contains `python-standards.md` or `infra-standards.md`
  also contains `python-fastapi` or `profiles/`. A section is the text from its `## <n>.`
  heading to the next `## <m>.` heading, fenced blocks included in the text but headings
  inside fences ignored.
- **AC-37** (REQ-17, REQ-72) **release gate** — Given the copyright-holder wording the owner
  supplied at the gate (after confirming that no third party holds rights, D-01) and an
  explicit authorization naming a version, When the release sequence of REQ-72 runs, Then
  the release-preparation commit holds `LICENSE` (Apache License 2.0 with that wording and no
  placeholder token), the
  new `VERSION`, the post-release tag text in `docs/USAGE.md` section 4 and the updated bodies
  of the checks listed in REQ-72, `scripts/validate-contracts.sh` passes on it, a fresh
  `release-check.sh` on it reports RC-01–RC-08 `pass`, and its candidate report shows RC-14 and
  RC-15 `pass`.

- **AC-43** (REQ-81, REQ-16) — Given the delivered tree, When suite B runs, Then
  `.github/workflows/offline-checks.yml` exists with the `on:` triggers `pull_request`, `push`
  and `schedule`, `permissions: contents: read`, the job `offline-checks` with
  `if: github.event_name != 'schedule'`, the job `full-validator` with
  `if: github.event_name == 'schedule'` running the literal RC-02 command, none of the strings
  `secrets.`, `pull_request_target` and `workflow_dispatch`, and no line matching
  `(^|run:|[;&|])\s*(claude|codex)\b`; the steps of `offline-checks` contain, in order, the
  literal commands of RC-03–RC-06 from Data Model → Release items and a `golden-runs.py` step guarded by
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
| REQ-10 | AC-09 |
| REQ-11 | AC-10 |
| REQ-12 | AC-11 |
| REQ-13 | AC-12 |
| REQ-14 | AC-13 |
| REQ-15 | AC-14 |
| REQ-16 | AC-15, AC-43 |
| REQ-17 | AC-16, AC-37 |
| REQ-19 | AC-18 |
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
| REQ-72 | AC-37 |
| REQ-81 | AC-43 |
| REQ-86 | AC-12 |

Every AC names at least one REQ; AC-34 and AC-37 are release gates outside implementation acceptance.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Frozen validator and source guard | Implementation blocked by fingerprint failures | High | Standalone suites; re-pinning procedure; no new `check` lines |
| Identity ledger line pins | Validator fails after USAGE or analysis edits | High | Append-only provenance lines; ledger rows updated in the same change |
| Publishing the `flat` reference result | Later experiments on `flat` may be contaminated | Low | Spec 09 treats `flat` as `tuning` (`published: true`; a holdout task on it is rejected, its REQ-50) |
| Full validator takes 34–52 minutes (`.ai/context/runbook.md:26`) | Slow release check | High | Accepted; release check runs once per candidate |
| Dry-run behaviour of agents is untestable offline | A workflow could still write | Medium | Contract check (AC-12); a golden case can cover it later (spec 09) |

## Assumptions

- A-01 | Language | Resolved: English spec; the Russian text stays in history at `060ce6d`, translated under Source | Source: `rules/language.md`; `.ai/principles/coding.md:11` | Reversible: yes
- A-24 | README length | Resolved: at most 60 lines | Source: `scripts/validate-contracts.sh:4618` (existing, frozen expression) is stricter than and satisfies original REQ-10's 120 | Reversible: yes
- A-25 | Clone URL in README | Resolved: not in README; link to USAGE section 4 | Source: identity ledger (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:184-208`) | Reversible: yes
- A-26 | `CONTRIBUTING.md` location | Resolved: `docs/CONTRIBUTING.md` | Source: `.ai/principles/coding.md:80` (guides in `docs/`), `:83-85` (root holds only listed files) | Reversible: yes
- A-27 | Russian originals (ADR-0009 Decision 6 "kept alongside" vs `rules/language.md`) | Resolved: originals stay byte-exact in history at pinned blobs; each translation names its blob; no Russian text is written to the tree; names keep `.ru.md` | Source: `rules/language.md` and `.ai/principles/coding.md:11` (principles precede ADRs); delivered state `docs/README.md:26`, `:28`; ledger and legend checks pin the names | Reversible: yes (Q-02 resolved 2026-11-14: owner accepted, D-02; ADR at delivery)
- A-28 | CI for required status checks | Resolved 2026-11-14 (supersedes the earlier "not created"): this spec creates one offline workflow, REQ-81; RC-13 is `blocked` only while the workflow or the required-check setting is missing | Source: owner decision D-03 (Q-03); spec 09 Out of Scope and A-24 (that spec creates none); G6 | Reversible: yes
- A-29 | Example source | Resolved: spec 09 `flat` reference workspace for `spec-run`, labelled as not a model run | Source: original REQ-11; spec 09 DM-1; `.ai/specs/README.md` → "Shared acceptance gates" (G6, no paid runs) | Reversible: yes
- A-30 | Test location | Resolved: standalone `scripts/check-install.py` and `scripts/check-public-readiness.py`, not registered in the validator | Source: ADR-0019 Decision 3; spec 10 Scope item 8 | Reversible: yes
- A-31 | Validator edits | Resolved: bodies only, outside the pinned region, expressions untouched, then re-pin | Source: `tests/fixtures/validator-runtime/oracle.py:160-252`; ADR-0020 Decision 2 | Reversible: yes
- A-32 | Remote-setting verification | Resolved: manual items with read-only commands; `release-check.sh` stays offline | Source: original REQ-03, REQ-16; G6 | Reversible: yes
- A-33 | 15-minute onboarding target | Resolved: measured and recorded as `met`/`not met`; not a pass/fail gate of this spec | Source: original §1 ("target") and §6 (record blocking dependencies) | Reversible: yes
- A-34 | Optional-feature document | Resolved: `docs/OPTIONAL-FEATURES.md` with nine required rows | Source: `.ai/principles/coding.md:80`; original §6 paragraph 3 | Reversible: yes
- A-35 | Cost vocabulary | Resolved: five labels | Source: original REQ-02; `.ai/specs/README.md` → "Shared acceptance gates" (G8) | Reversible: yes
- A-36 | Where the dry-run contract lives | Resolved: a new on-demand rule `rules/contract-dry-run.md`, not an always-on rule; telemetry exception as in `/spec-run` | Source: P6 (`.ai/principles/architecture.md`, one canonical statement; finite always-on budget); spec 13 rule kinds (ADR-0009 Decision 3); `workflows/spec-run.md:10-11`, `:50-51` | Reversible: yes
- A-37 | Feature size | Resolved: two parts with an explicit boundary; superseded 2026-11-16 by the split into spec 11a and this spec | Source: readiness check 13; original §8 order | Reversible: yes
- A-41 | Old repository URLs in this spec | Resolved: replaced by repository paths and the pinned commit; the identity-ledger row for this file was removed at `e3ba41a` (done) | Source: precedent of the 2026-11-13 state-tool refinement (`.ai/memory/progress.md:128`) | Reversible: yes
- A-43 | Copyright holder and third-party rights (2026-11-14) | Resolved: the implementer never chooses a holder; the holder line is supplied by the owner at the REQ-72 gate, after the owner confirms no third party holds rights (D-01) | Source: owner decision D-01 (Q-01); ADR-0009 Decision 1 | Reversible: no once published under a licence
- A-44 | What the CI workflow must set up (2026-11-14) | Resolved: REQ-81 lists it from the repository's runbook and spec 09 REQ-35 (the validator is run with bash); no matrix, cache or numeric time limit is specified, and the full validator's long runtime (runbook → Commands) is handled by D-04: it runs in a scheduled job, not in the required check | Source: `.ai/context/runbook.md → Commands`; `scripts/validate-contracts.sh` (run with bash); spec 09 REQ-35 | Reversible: yes

## Decisions

Owner decisions of 2026-11-14 (the refinement itself ran in autonomous mode; these three answered Q-01–Q-03):

- D-01 | The copyright holder is whoever legally owns the code, by default the owner personally under the name in the repository's git authorship; the owner first confirms that no employer or other third party holds rights; the holder line is supplied by the owner at the REQ-72 release gate, never invented by the implementer | Overrides: none | Rationale: a legal question, not a technical one; rights cannot be repaired after publication under a licence | Follow-up: REQ-72, AC-37, A-43; RC-14 stays owner-gated
- D-02 | The Russian originals stay only in git history; each English translation ends with a line naming the original's pinned commit and blob; Russian text does not return to the tree | Overrides: ADR-0009 Decision 6, literal wording ("Russian originals kept with English translations alongside") | Rationale: the language rule forbids non-English text in project files, and a pinned reference keeps the original recoverable | Follow-up: an ADR, or a note appended through the ADR process, records the departure from ADR-0009 Decision 6 (delivery record, Notes); REQ-58 and A-27 unchanged
- D-03 | Spec 11, Part B, creates the CI that required status checks need, as an explicit requirement and not a separate spec; minimum: one offline workflow running the validator and the standalone offline suites, no paid run, no secrets | Overrides: A-28 as first written, and the earlier Out of Scope entry that no spec owns CI (spec 09 keeps its own exclusion) | Rationale: a required status check needs a workflow that produces it, and gate G6 forbids paid runs in default CI | Follow-up: REQ-81, AC-43, RC-13 and REQ-16 updated (the Part B of that date is this spec); spec 09's Out of Scope and A-24 wording should cite REQ-81 (Notes)
- D-04 | The required check `offline-checks` runs the fast offline subset (RC-03–RC-06 and the guarded golden-run suite); the full validator (RC-02) runs in the scheduled job `full-validator` of the same workflow and in the release checklist | Overrides: REQ-81 and A-44 as first written (full validator inside the required check) | Rationale: the full validator takes 34–52 minutes, too slow for every pull request; a weekly full run plus the release gate keeps it enforced | Follow-up: REQ-81, AC-43, A-44 updated; RC-02 stays a release-candidate item

## Clarifications

Autonomous refinement: no questions were asked before 2026-11-14.

### Session 2026-11-14

- Q: What exact copyright-holder wording does the owner want in `LICENSE` (Q-01)? → A: The holder is whoever legally owns the code, by default the owner personally under the name in the repository's git authorship; the owner first confirms that no employer or other third party holds rights (D-01).
- Q: Does the owner accept keeping the Russian originals only in history at pinned blobs (Q-02)? → A: Yes; each translation ends with a line naming the original's commit and blob, and the Russian text does not return to the tree; this departs from the literal wording of ADR-0009 Decision 6 and is recorded by an ADR or an ADR-process note (D-02).
- Q: Which specification creates the CI that required status checks need (Q-03)? → A: This spec, Part B, as REQ-81, with no separate spec; offline only, no paid run, no secrets (D-03).

### Session 2026-11-16

- N/A — autonomous refinement after the split; no question was asked. Resolved gaps are folded
  into REQ-14, REQ-19, REQ-81, REQ-86 (new), Q-07 and the Data Model rules.

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
- Q-05 | resolved 2026-11-16 | Should the roadmap index list Part A and Part B as separate entries
  (11 and 11b)? Impact: Discovery runs two tasks either way. Resolved: the owner split the
  specification; the roadmap lists spec 11a and this spec as separate entries.
- Q-07 | non-blocker (resolved by a Discovery procedure) | REQ-61 adds
  `rules/contract-dry-run.md`. At `e3ba41a` the validator's per-rule loop
  (`scripts/validate-contracts.sh:1293-1305`) runs, for every `rules/*.md` file, runtime checks
  that the file name appears in `scripts/sync.sh` and `scripts/setup-new-project.sh`; a new
  rule file adds no registered check (the oracle pins source text, not names generated at run
  time), but those runtime checks fail unless both scripts name it. Spec 13, a precondition,
  replaces those checks (13 REQ-52). Procedure (REQ-86): Discovery runs the validator on the
  delivered default branch with the new rule file added; when a check fails only because a
  script does not name the new file, the delivery adds it to the deployment list that
  check guards, so it is deployed like every other rule, and re-pins the script's digest; no check expression is changed and no inventory entry is added, because
  naming the file weakens no check and REQ-61 supersedes no contract. Impact: none on the
  specification.

## Notes

- **Preconditions (checked at Discovery):** spec 11a delivered, that is merged into the default
  branch (the installer, profiles and suite A that this spec documents and runs); spec 13's schema-2 inventory mechanism, needed
  only for REQ-72's release-preparation commit; spec 10 (`docs/reference/`, `docs/harness-matrix.md`); spec 09 (`flat` reference
  workspace, offline suite, `docs/GOLDEN-RUNS.md`). Missing → Discovery stops.
- Hint (nonbinding): subtasks — (1) README, USAGE, OPTIONAL-FEATURES, CONTRIBUTING, templates,
  translations; (2) example; (3) dry-run contract; (4) release checklist, release check,
  onboarding measurement and candidate report; (5) offline CI workflow.
- Shared acceptance gates G1–G8 apply (`.ai/specs/README.md` → "Shared acceptance gates"); G6
  is met by the standalone suites; no paid run is needed.
- Rejected alternatives: restoring Russian files in the tree (A-27); a separate spec for CI
  (D-03 puts the one offline workflow in this spec, REQ-81).
- **ADR for D-02.** Delivery adds an ADR (or a note appended through the ADR process)
  recording that ADR-0009 Decision 6's "originals kept alongside" is replaced by originals kept
  only in history at pinned blobs; it is listed with the other delivery records in Scope.
- **Follow-up for other specs (not changed here):** spec 09's offline command
  `python3 -I tests/golden-runs.py` is consumed by REQ-81 only when the file exists; spec 09 marks `flat` as `tuning` with `published: true` (its
  `published` case field, REQ-50, AC-38) because its reference result becomes public.

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

### 2026-11-16 — split into spec 11a and this spec

- Part A (installer and profiles: REQ-03–REQ-09, REQ-18, REQ-20–REQ-53, REQ-64–REQ-71,
  REQ-73–REQ-80; AC-02–AC-08, AC-17, AC-19–AC-33, AC-38–AC-42; A-02–A-23, A-38–A-40, A-42;
  Q-04, Q-06; their Context, Data Model, Contracts, Edge Cases and Risks) moved to
  `.ai/specs/11a-public-installer-and-profiles.md` without renumbering. This file keeps
  Part B, the Source history and this Change Log. Q-05 resolved by the split; Q-07 added for
  the inventory entry REQ-61 needs; A-37 marked superseded.
- Same day, `/spec-draft --auto-mode` review loop with an independent critic (4 rounds: 68, 90,
  94, 99/100): new REQ-86 (the new rule file is deployed like every other rule; no check
  expression changes); Q-07 restated; AC-16 made state-relative; REQ-81's triggers, permissions
  and per-job conditions specified; literal RC commands; the release-check pattern resolution,
  candidate-commit definition, validator wrapper seam, optional-feature state rule with owning
  specifications, repository path-token rule, `## Platform support` and the USAGE backup text
  added; the first real candidate report placed after merge as a release gate.

## Readiness Checklist

Result of 2026-11-16 (first review after the split).

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — public materials, preview, CI and release readiness on top of spec 11a |
| 2 | Out of Scope names concrete exclusions | PASS — owner actions, further CI, paid runs, spec 11a, 13 and 10 ownership named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — 24 requirements; new REQ-86 |
| 4 | Every REQ maps to an AC and every AC names a REQ | PASS — Traceability complete both ways |
| 5 | Every AC is binary and testable before implementation | PASS — fixtures, literals and regexes; AC-34 and AC-37 and the first real candidate report are release gates |
| 6 | Non-functional targets measurable or N/A | PASS — verified by AC-18; performance N/A with reason |
| 7 | Data model and contracts specified | PASS — optional-feature table with state rule, example layout and provenance, contribution guide and templates, release items with literal commands, candidate report, dry-run contract, release check |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — Edge Cases table including pattern resolution and merge strategies |
| 9 | Every ambiguity recorded | PASS — A-01, A-24–A-37, A-41, A-43, A-44; Q-01–Q-03, Q-05 and Q-07 resolved |
| 10 | No blocker question remains | PASS — none open |
| 11 | Every existing-code claim cited and verified | PASS — citations checked by the critic against `e3ba41a` |
| 12 | Terminology matches domain definitions | PASS — installer terms referenced from spec 11a |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — about five subtasks (Notes hint) |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 99/100, critic: sub-agent, open: none (minor F-33 applied after the final round) |

**Verdict: READY FOR DEVELOPMENT.** Release gates AC-34, AC-37 and the first real candidate
report stay open until the owner acts. Automated readiness is not sign-off.
