# 19. Reproducible generation of reference documents and always-on instructions

## Source

- **Origin:** owner decision, ADR-0009 Decision 6 (2026-09-17),
  `.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:233-235`: "Generated docs
  (spec 19): separate files under `docs/reference/`, linked from `USAGE.md`; always-on
  files generated from a core body plus per-harness header template; generator in Python."
  The same decision allows Python 3 for optional tools such as generators (`:243-244`).
- **Previous revision:** 2026-10-28, written in Russian. Its goal statement, translated
  from Russian (spec 19, revision 2026-10-28, §1): "The goal is to obtain the references of
  commands, rules and states, and the always-on instructions of both supported harnesses,
  from single canonical sources. Identical input bytes must yield identical output bytes;
  a stale generation must be detected before installation." The Russian text, including
  REQ-01–REQ-15 and AC-01–AC-12, is retrievable from git history of this file at
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Every identifier is preserved below; the
  requirements are restated in English and refined.
- **Roadmap position:** `.ai/specs/README.md` → "Dependency order" — order 15, prerequisites 09 and 11,
  disposition "Render metadata without inlining optional context".
- **This revision:** 2026-11-13, refined in place under `/spec-draft --auto-mode` with the
  owner's authorization to replace the file. No human questions were asked; every
  resolved gap is recorded under Assumptions with its source.

### Implementation review — 2026-11-06 (preserved)

- **Disposition:** Planned; limited assembly already exists.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Sync assembles existing global instruction templates and appends harness capability declarations.
- **Outstanding scope and limits:** The bin/gen-docs.py generator, full workflow metadata schema, generated reference set, reproducible provenance, and stale-output check mode are not delivered.
- **Sources:** [`scripts/sync.sh`](../../scripts/sync.sh), [`templates/codex-global-AGENTS.md`](../../templates/codex-global-AGENTS.md), [`harness/claude/capabilities.md`](../../harness/claude/capabilities.md), [`harness/codex/capabilities.md`](../../harness/codex/capabilities.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

- No generator exists: there is no `bin/` directory and no `scripts/gen-docs.py`
  (`scripts/README.md:8-20` lists every shell helper). Python helpers live in `scripts/`
  (for example `scripts/model-catalog.py`); ADR-0021 Decision 3
  (`.ai/adr/0021-task-07-schedule-state-tool.md:74-86`) rejected a new `bin/` directory for
  the same kind of tool.
- Always-on files are assembled at deploy time. `scripts/sync.sh:58-67` defines
  `append_logging_capabilities`, which appends a marker, the whole
  `harness/<name>/capabilities.md` and a `## Current hook installation` section with the
  installer's JSON result. It is applied to `rules/global-claude.md` → `~/.claude/CLAUDE.md`
  (`scripts/sync.sh:98-101`) and to `templates/codex-global-AGENTS.md` → `~/.codex/AGENTS.md`
  (`scripts/sync.sh:153-158`). `tests/hook-install.sh:783-795` asserts that the deployed file
  starts with the body file and contains the capability declaration exactly once.
- Agents read the installation result from the deployed always-on file:
  `rules/run-log.md:117-121` ("Read the harness capability declaration and current
  installation result").
- Capability declarations are semi-structured text, not a table: `hooks: yes`,
  `profile:`, `verified:`, `runtime:` lines plus prose and a `## git-rails` section
  (`harness/claude/capabilities.md:1-90`); Codex declares `hooks: no` and
  `git-rails: none (textual rules only)` (`harness/codex/capabilities.md:3,12`).
- Sizes today: `rules/global-claude.md` has 985 words and `harness/claude/capabilities.md`
  1,607 words (`wc -w`). Spec 09 REQ-54 limits the always-on body — the always-on file
  without an embedded capability declaration and without the installation record — to
  1,200 words (counted per its DM-19).
- Workflow metadata is only `description:` (every `workflows/*.md` front matter);
  `workflows/pd-archive.md:2-3` spans two lines. Rules still use `trigger:`
  (`rules/tdd.md:2`). Spec 09 REQ-12/REQ-13 introduce `phase`, `step` and `load`; spec 11
  DM-1 introduces `loads`; spec 09 DM-3 registers `reads`, `writes`, `called_by` as this
  spec's extension keys.
- Each of the 41 executable workflows has exactly one line `` Invocation: `/<command> …` ``
  (line 5, `workflows/pd-archive.md:6`). 25 workflows have a prose `Called by:` line, for
  example `workflows/pv-issues.md:6`.
- Status vocabularies are anchored lines inside `## Canonical Status Formats`
  (`rules/workflow-globals.md:156`): `:195` (atomic-execution / atomic-validation), `:197`
  (`atomic-tests`), `:218` (`rollup`), `:219` (`integration-validation`). Phase statuses
  exist only inside a code block (`:165-169`); `plan.md` statuses only as a table
  (`:268-278`). Two of the anchored lines are repeated in `rules/workflow-reference.md:226-227`.
  Anchored vocabulary lines are the project convention (`.ai/principles/coding.md:39-41`).
- `docs/USAGE.md` copies these facts by hand and has drifted: §7 command tables
  (`docs/USAGE.md:501-571`) list a single utility command (`:571`); the `rules/` and
  `workflows/` role tables (`:739-752`, `:763-808`) duplicate file lists; the `atomic-tests`
  vocabulary line omits `pinned` (`:851`, versus `rules/workflow-globals.md:197`); the
  `reviewed` meaning differs (`docs/USAGE.md:829` versus `rules/workflow-globals.md:275`).
  `.ai/principles/coding.md:94-97` records that the derived documents are fixed by hand
  "until `specs/19-generated-reference-docs.md` makes them generated".
- The contract validator's check inventory is frozen. ADR-0019 Decision 3
  (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`) therefore placed a
  new contract test outside it, as the standalone `scripts/check-spec-draft.sh`. The
  inventory oracle accepts only a hard-coded amendment: `tests/validator-runtime-oracle.py:46-57`
  rejects any amendment field other than `schema`, `paths`, `removed_results`, `resources`
  and any removed-result list other than two named checks, so no added check can be
  registered today. `scripts/sync.sh` is pinned by digest in
  `tests/fixtures/validator-runtime/source_guard_exceptions.json:308`; such digests are
  refreshed under the fixture procedure (`tests/fixtures/validator-runtime/README.md:9-28`,
  ADR-0020 Decision 2). The sync fixture replaces the validator with a stub in its
  private copy (`tests/hook-install.sh:135-138`).

**Consequence:** reference material drifts from its canonical sources, the always-on
files are assembled by an append step whose output is never checked against a reviewed
result, and nothing detects a stale or hand-edited derived file before deployment.

## Goal

Maintainers get the command, rule and status references, the harness capability matrix and
the always-on instruction file of each supported harness from one deterministic generator
that reads only canonical sources, so that identical inputs always produce identical bytes,
deployment refuses to proceed while any derived file is stale, missing or hand-edited,
and the operating manual links to the generated references instead of keeping
hand-made copies.

## Scope

1. `scripts/gen-docs.py`: a standard-library Python 3.11+ generator with `--check`,
   `--write [--force]` and `--profile <name>` modes and an optional `--root <dir>`.
2. The workflow metadata fields `reads`, `writes` and `called_by` (schema, validation and
   their population in every `workflows/*.md`).
3. Generated outputs: `docs/reference/commands.md`, `docs/reference/rules.md`,
   `docs/reference/statuses.md`, `docs/harness-matrix.md`, `harness/<name>/always-on.md`
   for every harness directory, and the provenance manifest `docs/reference/manifest.json`.
4. New always-on sources: `templates/always-on-core.md` (shared body) and
   `harness/<name>/always-on-header.md` (harness-specific part), created by splitting
   spec 09's hand-written `harness/<name>/always-on.md` without losing a line.
5. Two new anchored vocabulary lines in the canonical status-formats section (phase
   statuses and `plan.md` statuses) so that every task-state vocabulary is machine-readable.
6. Safe publication: validation before writing, a write lock, atomic per-file replacement,
   a recovery journal, ownership protection of hand-edited outputs.
7. Deployment change in `scripts/sync.sh`: run `--check` after contract validation and
   before any deployment step; deploy generated always-on bytes plus one installation
   record; stop appending the capability declaration. The four fixture consequences under
   Contracts → Deployment contract (copy `docs/` in `tests/hook-install.sh`, new body
   assertion, inventory re-amendment and oracle digest, source-guard refresh) are part of
   this change.
8. A standalone acceptance suite `scripts/check-gen-docs.py`, outside the frozen validator
   inventory (ADR-0019 Decision 3 precedent). `scripts/validate-contracts.sh` is not
   changed.
9. `docs/USAGE.md`: replace the duplicated reference tables and vocabulary lines with links.
10. Delivery records: `.gitignore` lines for auxiliary files, two `scripts/README.md` rows,
    `docs/README.md` index entries, the `.ai/principles/coding.md → ### Documentation`
    update, `.ai/memory/architecture.md`, and one ADR recording the decisions marked
    "ADR at delivery" under Assumptions.
11. In the same change that embeds the capability declaration in `always-on.md` (added
    2026-11-14): spec 11's meter (`scripts/measure-context.sh`) counts
    `harness/<h>/always-on.md` alone as the harness part of its always-on set and no longer
    adds `harness/<h>/capabilities.md`; the "Always-on set" definition that spec 11 places
    in `.ai/principles/domain.md` (its REQ-21) is updated to match, with a meter fixture
    (REQ-50). Spec 11 agrees with this allocation: its A-11 and the always-on composition
    paragraph in its Contracts → Graph resolution state that the meter counts the generated
    `always-on.md` alone "from spec 19's delivery", a change spec 19 makes (19 REQ-50); the
    meter is changed by this delivery, not by spec 11.
12. Registration of `reads`, `writes` and `called_by` as spec 19's extension keys in spec
    09's checker (`scripts/lint-instructions.py`), as spec 09 DM-2/DM-3 require before an
    extension key stops being `metadata-unknown-field` (REQ-51; added 2026-11-14).

## Out of Scope

- Renaming rules and workflows, rule metadata (`description`, `load`), workflow `phase` and
  `step`, the capability declaration format, `harness/<name>/deploy.env`, moving
  `workflows/PIPELINE.md` to `docs/PIPELINE.md`: owned by spec 09.
- The `loads` schema, its condition language, the context-load meter
  `scripts/measure-context.sh` (except the composition change of Scope item 11), the 300/700/6,000-word limits and `ref-<name>` deployment:
  owned by spec 11 (and 09 for the 300-word bootstrap limit).
- Profile files, the managed-fragment markers in project `CLAUDE.md`/`AGENTS.md`, merging
  with user content, `.ai/profile`, the public installer: owned by spec 20.
- Rendering status transitions or a transition engine; the run-log vocabulary
  (`rules/run-log.md`, `scripts/log-step.sh`) and reviewer verdicts in `statuses.md`.
- Deduplicating `docs/PIPELINE.md` and the `principles/` and `templates/` role tables in
  `docs/USAGE.md` (§9 `principles/`, `templates/`).
- A structured JSON diagnostic report, a dry-run plan mode, a diff printer.
- Rewriting historical material: `.ai/tasks/completed/`, `.ai/specs/completed/`,
  `docs/audits/`, `docs/analysis/`, existing ADRs.
- Deploying to a real user home, running models or paid evaluations.
- Registering checks in `scripts/validate-contracts.sh`: blocked by the frozen inventory
  until an inventory change accepts added checks (Q-05).
- Verifying the stop condition of a call cycle (prose; REQ-20).

### Preconditions (checked at Discovery)

Spec 09 is delivered: rules carry DM-2 front matter and kind prefixes, workflows carry
DM-3 `description`/`phase`/`step`, `workflows/PIPELINE.md` has moved to `docs/PIPELINE.md`
(09 REQ-23), every harness directory has `deploy.env` (DM-5) and the DM-4 capability records,
the DM-4 behaviour table exists in `rules/contract-phases.md → ## Capabilities`, and
`harness/<name>/always-on.md` exists for each harness. Spec 11 is delivered: every workflow
carries `loads` (11 DM-1). If any is missing, Discovery stops; the generator itself reports the
missing metadata with exit 2.

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Maintainer | Edits canonical sources; runs `--write` (and `--write --force` after reviewing a conflict); commits sources and outputs together |
| Sync (`scripts/sync.sh`) | Runs the validator (existing step `scripts/sync.sh:41-45`), then `--check`; deploys generated always-on bytes plus one installation record; never runs `--write` |
| Acceptance suite (`scripts/check-gen-docs.py`) | Run directly by maintainers and implementers; builds disposable fixture roots |
| Project installer (spec 20, `scripts/setup-new-project.sh`) | Calls `--profile <name>` and owns what it does with the bytes |
| Generator (`scripts/gen-docs.py`) | Reads inputs; writes only managed outputs, the manifest and its auxiliary files under `--write` |
| Implementer / reviewer | Builds and validates this spec; populates workflow metadata |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Source root | The directory all input and output paths are relative to: `--root` or the parent of the directory holding `gen-docs.py` | This spec |
| Input | A file whose content the generator consumes (table under Data Model → Inputs) | This spec |
| Managed output | A file the generator owns and writes: the four reference documents and every `harness/<name>/always-on.md` | This spec |
| Manifest | `docs/reference/manifest.json`; the last file written in a publication; lists the generator digest, inputs and managed outputs | This spec |
| Generation | The set of managed outputs plus the manifest produced by one `--write` | This spec |
| Publication | The `--write` step that replaces managed outputs on disk | This spec |
| Journal | `docs/reference/.gen-docs.journal.json`; exists only while a publication is incomplete | This spec |
| Owned file | A managed output path whose current bytes equal a digest the generator itself recorded (manifest or journal) | This spec |
| Edited output | A managed output whose bytes differ from both its expected bytes and its recorded digest | This spec |
| Orphaned output | A path listed in the current manifest's outputs that the current inputs no longer produce | This spec |
| Capability declaration | `harness/<name>/capabilities.md`; its facts and record syntax are defined by spec 09 DM-4, which adopted this spec's record form (A-32, A-45). Replaces the earlier phrase "capability table" | Spec 09; this spec |
| Capability record | A `name:`-started block of lines in a capability declaration (Data Model) | This spec |
| Leading caller list | The backticked commands at the start of a `Called by:` line (Data Model) | This spec |
| Retired harness | A former harness directory whose `deploy.env`, `capabilities.md` and header were deleted (spec 09 DM-5) | Spec 09 DM-5; this spec |
| Call cycle | A strongly connected component of the `called_by` graph with more than one workflow or a self-edge; distinct from a load cycle | This spec; spec 11 REQ-11 for load cycles |
| Installation record | The `## Current hook installation` section with `installation-result: <json>` appended by sync at deploy time | `scripts/sync.sh:66` |
| Always-on file | `harness/<name>/always-on.md`, deployed to the harness's `always_on_path` (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) | Spec 09 REQ-35, DM-5; ADR-0009 Decision 2 |
| Always-on body | The always-on file without its embedded capability declaration: provenance line, header and shared core | Spec 09 REQ-54 and Terminology |
| Shared core | `templates/always-on-core.md` | This spec; ADR-0009 Decision 6 |
| Harness header | `harness/<name>/always-on-header.md` | This spec; ADR-0009 Decision 6 |
| Profile fragment | `profiles/<name>/always-on-fragment.md` | Spec 20 |
| Anchored vocabulary line | A line `Status values for <subject>: `v1` \| `v2` …` defining one vocabulary | `.ai/principles/coding.md:39-41` |
| Vocabulary namespace | The subject of one anchored line, with backticks removed | This spec |
| Word | Maximal non-empty run of non-whitespace Unicode characters in the whole UTF-8 text (Python `str.split()` with no argument) | Spec 09 DM-19; spec 11 A-09 |
| Workflow, Rule, Spec | As defined in `.ai/principles/domain.md:12-15` | Domain |

"Template" in this spec means a plain text file concatenated verbatim; it never has
placeholders or expansion.

## Requirements

Identifiers REQ-01–REQ-15 are the 2026-10-28 identifiers, restated in English; behaviours
that the earlier text bundled into one item were split into new identifiers, noted in
parentheses. "The generator" is `scripts/gen-docs.py`.

- **REQ-01 Lazy references.** THE generator SHALL compose each always-on file only from
  its provenance line, its harness header, the shared core and its capability declaration,
  and SHALL NOT insert the content of any other file into it.
- **REQ-02 Provenance.** WHEN `--write` completes successfully, THE generator SHALL leave a
  manifest whose fields match Data Model → Manifest, including the SHA-256 of every managed
  output and the consumed-content digest of every input.
- **REQ-03 Honest availability.** IF a capability declaration lacks a canonical capability
  key, THEN THE generator SHALL render that capability as `unknown` in the harness matrix.
- **REQ-04 Offline operation.** THE generator SHALL complete every mode without opening a
  network connection, invoking a model, or creating a subprocess.
- **REQ-05 Workflow metadata.** IF a workflow's front matter lacks any field listed under
  Data Model → Workflow metadata, THEN THE generator SHALL report `metadata-missing-field`
  once per missing field, naming the file and the field, and SHALL NOT substitute a default.
- **REQ-06 References.** WHEN `--write` runs on valid inputs, THE generator SHALL write
  `docs/reference/commands.md`, `docs/reference/rules.md`, `docs/reference/statuses.md`
  and `docs/harness-matrix.md` with the layouts under Contracts, listing every workflow
  in `commands.md` exactly once and every top-level rule in `rules.md` exactly once.
- **REQ-07 Always-on files.** WHEN `--write` runs on valid inputs, THE generator SHALL
  write `harness/<name>/always-on.md` for every harness directory, laid out as provenance
  line, harness header, shared core, capability declaration, with the capability
  declaration occurring exactly once.
- **REQ-08 Profiles.** WHEN invoked with `--profile <name>`, THE generator SHALL write the
  normalized bytes of `profiles/<name>/always-on-fragment.md` to standard output and SHALL
  NOT create, modify or delete any file.
- **REQ-09 Stale check.** WHEN invoked with `--check`, THE generator SHALL report every
  missing, stale, edited and orphaned managed output and a stale manifest, exit 1 if it
  reported any, and SHALL NOT create, modify or delete any file.
- **REQ-10 Counts.** THE generator SHALL state in `commands.md` the number of workflows and
  in `rules.md` the numbers of rules and reference documents, computed from the enumerated
  inputs, and SHALL NOT publish any count of validator checks.
- **REQ-11 Strict parsing.** IF front matter contains a duplicate key, an unknown key, a
  value of the wrong type, an unsupported `loads` schema version, or a rule file name
  without a kind prefix, THEN THE generator SHALL report the code listed under Contracts →
  Diagnostic codes and exit 2.
- **REQ-12 Validate before writing.** WHILE any input or rendered output fails
  validation, THE generator SHALL leave every managed output, the manifest and the journal
  unchanged.
- **REQ-13 Edit protection.** IF, during `--write` without `--force`, a managed output's
  current bytes differ from its expected bytes and the path is not an owned file, THEN THE
  generator SHALL report `ownership-conflict` for that path, exit 3 and modify no file
  other than creating the lock file.
- **REQ-14 Compatibility.** THE generator SHALL open every input read-only and SHALL NOT
  create, modify or delete any file other than managed outputs, the manifest, the lock
  file, the journal and its own temporary files.
- **REQ-15 Input safety.** IF an input path is a symbolic link, contains a `..` segment,
  resolves outside the source root, or does not exist, THEN THE generator SHALL report
  `unsafe-input-path` or `input-missing` and exit 2.
- **REQ-16 Manual without copies (split from REQ-06).** WHEN `--check` runs, THE generator
  SHALL report `usage-link-missing` for each generated reference that `docs/USAGE.md` does
  not link, and `usage-duplicate` for each duplicated line defined under Contracts →
  Manual duplication rule.
- **REQ-17 Size limit (split from REQ-01; aligned 2026-11-14).** IF the always-on body of a
  rendered always-on file — its provenance line, header and shared core joined as in the
  layout, without the embedded capability declaration — exceeds 1,200 words, THEN THE
  generator SHALL report `size-limit` with the word count and exit 1 (spec 09 REQ-54).
- **REQ-18 Single declaration on deployment (split from REQ-02).** WHEN sync deploys an
  always-on file, THE component that writes the harness's `always_on_path` (Contracts →
  Deployment contract) SHALL write the generated bytes of `harness/<name>/always-on.md`
  followed by exactly one installation record, and SHALL NOT append the capability
  declaration.
- **REQ-19 Core is not deployed (split from REQ-07).** THE deployment SHALL NOT deploy
  `templates/always-on-core.md` or any `harness/<name>/always-on-header.md` as a skill, a
  rule or a standalone file.
- **REQ-20 Structured fields only (split from REQ-03).** THE generator SHALL derive
  reference content only from the fields listed under Data Model and SHALL NOT derive any
  value from prose outside them.
- **REQ-21 Profiles stay out of global outputs (split from REQ-04).** WHILE running
  `--check` or `--write`, THE generator SHALL NOT read any path under `profiles/`.
- **REQ-22 Deployment gate (split from REQ-09; narrowed, A-33).** WHEN `scripts/sync.sh`
  runs, THE sync script SHALL run `python3 -I "$ROOT/scripts/gen-docs.py" --check --root "$ROOT"`
  after contract validation and before its first step that writes outside the source root,
  and SHALL exit non-zero without writing outside the source root if that command exits
  non-zero. After spec 20, the gate's position is spec 20's (its REQ-64, REQ-40; A-48). Spec 20
  keeps spec 11's meter gate (11 REQ-08) next to this one, and the deployment SHALL keep both
  gates, so that load cycles stay checked at deployment.
- **REQ-23 Missing targets (split from REQ-11; narrowed 2026-11-14).** IF a `called_by` name
  does not name an existing workflow, THEN THE generator SHALL report `missing-target` and
  exit 2. Existence of `loads` paths and sections is checked by spec 11's meter only
  (11 REQ-18, REQ-20; A-46).
- **REQ-24 Load cycles (split from REQ-11; restated 2026-11-14).** THE generator SHALL NOT
  traverse the `loads` graph; load-cycle detection over the whole load graph (workflows and
  top-level rules) is owned by spec 11's meter (11 REQ-11), which sync runs as its own gate
  step next to this one (11 REQ-08). The code `load-cycle` is withdrawn from this spec (A-46).
- **REQ-25 Call cycles (split from REQ-11).** WHEN the `called_by` relation contains a
  cycle, including a workflow naming itself, THE generator SHALL accept it and list it
  under `## Call cycles` in `commands.md` (Contracts → Output layouts), separately from
  load cycles.
- **REQ-26 Metadata is data (split from REQ-11).** THE generator SHALL treat metadata
  values and template text as literal data, without evaluating, executing, importing or
  expanding any part of them.
- **REQ-27 Atomic publication (split from REQ-12).** WHEN `--write` publishes, THE
  generator SHALL replace each changed managed output by renaming a fully written and
  flushed temporary file in the same directory, replace the manifest after every other
  output, and delete the journal last.
- **REQ-28 Recovery (split from REQ-12).** WHEN `--write` starts and a journal exists, THE
  generator SHALL treat every path whose current bytes match the journal's old or new
  digest for that path as owned, remove the temporary files the journal lists, and then
  perform a complete publication.
- **REQ-29 Forced regeneration (split from REQ-13).** WHERE `--force` is given with
  `--write`, THE generator SHALL replace edited outputs, delete edited orphaned outputs,
  and resolve a journal per Contracts → Publication algorithm step 4, printing one
  `forced <path>` line to standard error for each path it overrides.
- **REQ-30 Inputs changed during generation (split from REQ-15).** IF, after acquiring
  the write lock, any input's consumed-content digest differs from the digest computed
  during rendering, THEN THE generator SHALL report `input-changed` and exit 3.
- **REQ-31 Deterministic order (split from REQ-15).** THE generator SHALL produce output
  bytes that depend only on input bytes, independent of directory enumeration order,
  locale, time zone, current working directory, `HOME` and `PYTHONHASHSEED`.
- **REQ-32 Single writer.** IF another process holds the write lock, THEN THE generator
  SHALL report `lock-held` and exit 3 without waiting, and SHALL NOT delete or take over the
  lock.
- **REQ-33 Status source.** THE generator SHALL read status vocabularies only from anchored
  vocabulary lines inside the single `## Canonical Status Formats` section of `rules/*.md`,
  and meanings only from a `| Status | Meaning |` table that directly follows such a line.
- **REQ-34 Vocabulary agreement.** IF an anchored vocabulary line in any other
  `rules/*.md` file has the same subject but different values or order, THEN THE generator
  SHALL report `vocabulary-conflict` naming both locations and exit 2.
- **REQ-35 Caller agreement.** IF a workflow has a `Called by:` line and the set of
  workflow names in its leading caller list (Data Model → Leading caller list) differs
  from the workflow names in its `called_by` field, THEN THE generator SHALL report
  `metadata-conflict` and exit 2.
- **REQ-36 Invocation.** IF a workflow does not contain exactly one line matching
  `` ^Invocation: `(.+)`$ `` outside fenced code blocks, THEN THE generator SHALL report
  `invocation-missing` and exit 2.
- **REQ-37 Diagnostics.** THE generator SHALL print every diagnostic of the failing stage
  to standard error in the format under Contracts → Diagnostics, without truncation, and
  exit with that stage's code.
- **REQ-38 Idempotent write.** WHEN `--write` finds every managed output and the manifest
  equal to their expected bytes and no journal exists, THE generator SHALL write no file
  other than creating the lock file if absent, and exit 0.
- **REQ-39 Orphans.** WHEN `--write` finds an orphaned output, THE generator SHALL delete
  it if its bytes equal the digest recorded in the current manifest, and otherwise report
  `ownership-conflict` unless `--force` is given.
- **REQ-40 Adoption.** WHEN `--write` finds a managed output path that exists, has no
  recorded digest and equals its expected bytes, THE generator SHALL treat it as owned.
- **REQ-41 Incomplete publication on check.** IF `--check` finds a journal, THEN THE
  generator SHALL report `publication-incomplete` and exit 3.
- **REQ-42 Line-preserving split.** WHEN the delivery splits spec 09's hand-written
  `harness/<name>/always-on.md` into header and shared core, THE delivery SHALL make the
  multiset of non-empty lines of header plus core equal the multiset of non-empty lines of
  that file at the parent commit, for every harness.
- **REQ-43 Command line.** IF the arguments name zero or several of `--check`, `--write`,
  `--profile`, give `--force` without `--write`, give an unknown option, or give a profile
  name not matching `^[a-z0-9]+(-[a-z0-9]+)*$`, THEN THE generator SHALL report `usage` and
  exit 2.
- **REQ-44 Runtime guard.** IF the interpreter is older than Python 3.11, THEN THE
  generator SHALL report `runtime-unavailable` and exit 3 before importing any module other
  than `sys`. The check is the module-level function
  `runtime_guard(version_info: tuple[int, ...]) -> int | None`, returning `3` after
  printing the diagnostic for versions below `(3, 11)` and `None` otherwise; the entry point
  calls it with `sys.version_info`.
- **REQ-45 Content checks keep passing (restated).** THE generated
  `harness/<name>/always-on.md` SHALL keep the path and the complete text that spec 09's
  hand-written file has, so that the validator's always-on content checks, which spec 09
  points at that path (spec 09 DM-10 maps `rules/global-claude.md` and
  `templates/codex-global-AGENTS.md` to it), pass without a change to
  `scripts/validate-contracts.sh`.
- **REQ-46 Location grammar.** IF a `reads` or `writes` entry does not match Data Model →
  Location grammar, THEN THE generator SHALL report `metadata-invalid-value` naming the
  entry and exit 2.
- **REQ-47 Capability records.** IF a capability record violates Data Model → Capability
  declaration, THEN THE generator SHALL report `capability-schema` naming the file and
  line, and exit 2.
- **REQ-48 Behaviour availability (added 2026-11-14).** WHEN `--write` runs on valid inputs,
  THE generator SHALL render in `docs/harness-matrix.md` a `## Behaviours` section with one
  row per row of the spec 09 DM-4 behaviour table, marking a harness `available` only if
  every key in the row's `Requires` cell (a canonical key or an extension record name,
  spec 09 REQ-67) has a record with `state: yes` in that harness's declaration; a record
  with `state: no` or `state: unknown`, and an absent record, give `unavailable` (for
  example spec 16's `sub-agent-effort` record while its state is `unknown`).
- **REQ-49 Loads on rules (added 2026-11-14).** WHEN a top-level rule's front matter holds a
  `loads` block, THE generator SHALL parse it with the same grammar as a workflow's (spec 11
  DM-1, REQ-22; spec 09 DM-2 registered extension key) and SHALL NOT render it.
- **REQ-50 Declaration counted once (added 2026-11-14).** WHEN spec 11's meter computes a
  harness's always-on set after this delivery, THE meter SHALL count
  `harness/<h>/always-on.md` and SHALL NOT also count `harness/<h>/capabilities.md`, so the
  embedded capability declaration is counted exactly once.
- **REQ-51 Extension keys registered (added 2026-11-14).** THE delivery SHALL register
  `reads`, `writes` and `called_by` in spec 09's checker under its extension-key registry
  (spec 09 DM-2, DM-3), so that the checker reports no `metadata-unknown-field` for them.

## Data Model

### Inputs (new; read-only)

| Input | Consumed content | Hash scope in manifest |
|---|---|---|
| `workflows/*.md` (top level, regular files) | Front matter, the `Invocation:` line, the `Called by:` line if present | `extract` |
| `rules/*.md` (top level) | Front matter; anchored vocabulary lines; in the canonical file, the whole `## Canonical Status Formats` section; in `rules/contract-phases.md`, the rows of the DM-4 behaviour table under `## Capabilities` (spec 09) | `extract` |
| `rules/reference/*.md` (spec 11) | File name only (not opened) | `extract` |
| `harness/<name>/deploy.env` | Existence only (selects harness directories, spec 09 DM-5); not parsed, not listed in the manifest | — |
| `harness/<name>/always-on-header.md` | Whole file | `file` |
| `templates/always-on-core.md` | Whole file | `file` |
| `harness/<name>/capabilities.md` | Whole file | `file` |
| `scripts/gen-docs.py` | Whole file (generator digest, not listed under `inputs`) | `file` |
| `profiles/<name>/always-on-fragment.md` | Whole file; `--profile` only; never in the manifest | — |
| `docs/USAGE.md` | Read by `--check` only for REQ-16; never in the manifest | — |

A harness directory is defined by spec 09 DM-5 (aligned 2026-11-14): a directory directly
under `harness/` whose name matches `^[a-z0-9]+(-[a-z0-9]+)*$` and that contains `deploy.env`.
Each harness directory must also contain `capabilities.md` (otherwise `adapter-incomplete`)
and `always-on-header.md` (otherwise `input-missing`); other files there are ignored. A
directory matching the name pattern that holds `capabilities.md` but no `deploy.env` is
`adapter-incomplete` (exit 2), the code spec 09 uses for the same condition. Hidden
directories, and a directory holding only an orphaned `always-on.md`, are not harnesses
and are not reported; such an `always-on.md` is still an orphan of this generator when the
manifest lists it (REQ-39). At least one harness directory must exist; otherwise
`input-missing` with location `harness/`. Retiring a harness means deleting its
`deploy.env`, `capabilities.md` and `always-on-header.md` (spec 09 DM-5); the next
`--write` deletes its owned `always-on.md`.

Every input whose content is consumed must be valid UTF-8 without a byte-order mark, a
carriage return or any of U+001C–U+001F (as spec 09 DM-19 and spec 11 A-09 require);
otherwise `input-encoding` (exit 2). Inputs are never normalized silently.

`extract` digest: SHA-256 of the UTF-8 bytes of
`json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`, where
`record` holds exactly the values the generator extracted from that file (front matter
mapping, invocation text, cited caller names, anchored lines with values, the status
section text, the behaviour-table rows). An edit that changes none of these values
leaves the digest unchanged. `file` digest: SHA-256 of the file bytes.

### Workflow metadata (fields `reads`, `writes`, `called_by` new; others existing contracts)

| Field | Type | Owner | Rule |
|---|---|---|---|
| `description` | string | Spec 09 REQ-12/13 | Non-empty, single line |
| `phase` | token | Spec 09 REQ-13, DM-3 | One of DM-3's phases: `discovery`, `execution`, `validation`, `atomic-execution`, `atomic-validation`, `orchestrated`, `entry`, `utility` |
| `step` | string | Spec 09 REQ-13, DM-3 | Plain value matching `^[1-9][0-9]*(\.[1-9][0-9]*|[a-z])?$` (for example `1`, `2.5`, `4a`) or the JSON string `"-"` |
| `loads` | mapping | Spec 11 DM-1 | `schema_version` the generator supports: `1` |
| `reads` | list of strings | This spec | Required; `[]` means the workflow reads no canonical file; every entry matches Location grammar; possible reads of conditional branches included |
| `writes` | list of strings | This spec | Same as `reads`, for writes |
| `called_by` | list of strings | This spec | Required; each item is a workflow name (file stem in `workflows/`, no slash) or the literal `user` (direct invocation); no duplicates |

The front matter is delimited by a first line `---` and the next line `---`. Spec 09
DM-2/DM-3 define the top-level scalar grammar (stated compatible with this one) and spec 11
DM-1 the `loads` block grammar; the generator accepts exactly the following line grammar,
which reproduces both.
Every non-empty line inside the delimiters must match one rule; anything else is
`metadata-syntax`. Tabs, comments (`#` starting a value or after a space), anchors and
multi-line scalars are `metadata-syntax`.

- **Top-level scalar:** `<key>: <value>` at column 0, `<key>` matching `[a-z_]+`. A value
  starting with `"` is a JSON string parsed with `json.loads` (it must be the whole rest of
  the line). Otherwise the value is plain: the rest of the line with trailing spaces
  removed, non-empty, not starting with `'`, `[`, `{`, `|`, `>`, `&`, `*`, `!`, `%`, `@`
  or `` ` `` (spec 09 DM-2). `step` must match the DM-3 pattern above as a plain value, or be
  the JSON string `"-"`; any other `step` value is `metadata-invalid-value`.
  Colons inside a plain value are allowed (`description: Step 1 — check: verdict`).
- **`loads` block** (spec 11 DM-1), two-space indentation steps:

  ```yaml
  loads:
    schema_version: 1
    mandatory:
      - path: rules/contract-example.md
        sections: ["## Safety rails"]
    conditional:
      - condition_id: composite_task
        condition: "leaf.type == composite"
        path: rules/reference/example.md
        sections: ["## Integration"]
        on_unknown: load
  ```

  The block grammar and field table are spec 11 DM-1's (aligned 2026-11-14): `loads:`
  alone on its line; at indent 2 only `schema_version` (required, only `1`), `mandatory`
  (required, may be `[]`) and `conditional` (optional, absent equals `[]`); a list is `[]`
  on the key's line or items at indent 4 starting `- <key>: <value>` with further keys of
  the same item at indent 6. Inside the block a plain value matches `[A-Za-z0-9_./-]+`
  (narrower than top-level scalars, as DM-1 requires); a value starting with `"` is a JSON
  string that is the whole rest of the line; `sections`, when present, is a one-line non-empty
  JSON array of strings, rendered verbatim; the generator checks only that form, and
  whether each string is a valid heading path (`["## Safety rails"]`) is spec 11's check
  (11 REQ-18). Item keys, field
  rules other than heading-path validity (`path` grammar, `condition_id` pattern,
  `on_unknown` only `load`) and the
  merging of duplicate paths are DM-1's. The generator maps DM-1 violations to its own
  codes: subset violation → `metadata-syntax`, unknown key → `metadata-unknown-field`,
  repeated key → `metadata-duplicate-key`, absent required key →
  `metadata-missing-field`, field-rule violation → `metadata-invalid-value`,
  `schema_version` other than `1` → `unsupported-schema-version`, all exit 2. The meter
  reports the same defects as findings with exit 1 (11 A-13); the difference is
  intentional, because the generator refuses to render while the meter measures. The
  generator does not resolve paths or sections, evaluate conditions against the 11 DM-2
  registry, or detect cycles (REQ-23, REQ-24).
- **List fields** `reads`, `writes`, `called_by` use exactly one of two forms:

```yaml
reads: []
writes:
  - "<task-dir>/state.md → ## Subtask Progress"
  - "code"
called_by:
  - "atomic-execution"
```

Each block item is two spaces, `- `, and one JSON double-quoted string parsed with
`json.loads`. A list field whose value on its own line is anything other than `[]` or
empty (for example `reads: "x"` or `reads: x`) has the wrong type and is
`metadata-invalid-value`; a malformed item line (flow list with items, unquoted item,
wrong indentation) is `metadata-syntax`. Any key outside the table is
`metadata-unknown-field`; a repeated key is `metadata-duplicate-key`; a wrong type is
`metadata-invalid-value`. Missing keys are `metadata-missing-field`, one diagnostic per key,
so a workflow carrying only 09's fields receives an exact migration list.

### Location grammar (new)

A `reads`/`writes` entry is `<location>` optionally followed by one or more section
segments ` → ## <heading>` or ` → ### <heading>` (cross-reference syntax of
`.ai/principles/coding.md:45-47`; `→` is U+2192 with one space on each side).

`<location>` is one of:

- an area token: `code` (production source of the consumer project), `tests` (its test
  files), `git` (its refs, branches and commits), `run-log` (the central run log written
  through `scripts/log-step.sh`);
- a path relative to the consumer project root, with `/` separators, segments of
  `[A-Za-z0-9._*-]+` or one of the placeholders `<spec>` (the spec file path),
  `<task-dir>` (the task directory), `<subtask-dir>` (a subtask directory),
  `<config>` (`${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail`), `<source>` (the Orchestrail
  source root); a placeholder may only be the first segment; no empty, `.` or `..`
  segment, no leading `/`, no backtick, no `|`.

The generator validates the grammar only; it never resolves these paths on disk.

### Leading caller list (new)

In a line starting `Called by: `, the leading caller list is the longest prefix of the
remaining text matching
`` `/<name>[^`]*`((, | or | and )`/<name>[^`]*`)* `` where `<name>` is `[a-z0-9-]+` — that is,
backticked commands joined only by `, `, ` or ` or ` and `. Names after the first other word are
prose and not compared (for example `` `/phase-atomic-execution` as Step 2, after `/pae-tests` ``
has the leading list `{phase-atomic-execution}`). Only names of existing workflows count.
At `060ce6d` every one of the 25 `Called by:` lines has a one-name leading list
(`workflows/pae-tests.md:6`, `workflows/pd-archive.md:7`,
`workflows/suggest-commit-message.md:6`, `workflows/pd-select-model.md:6` included).

### Rule metadata (existing contract, spec 09)

Top-level `rules/*.md` carry the fields of spec 09 REQ-12 and DM-2 (`description`, `load`)
and may carry the registered extension key `loads` (spec 11 DM-1 and REQ-22; REQ-49), parsed
but not rendered; any other key is `metadata-unknown-field`. The kind is the file-stem prefix before the first `-` and must be one of `bootstrap`,
`contract`, `protocol`, `procedure` (spec 09 REQ-24); otherwise `metadata-invalid-value`.
The deployed skill name is `rule-<stem>`. Reference documents are `rules/reference/*.md`
(spec 11 DM-3, deployed by 11 REQ-02) with skill name `ref-<stem>`; their content is not rendered.

### Anchored vocabulary lines (existing convention; two lines added)

Grammar: `^Status values for (?P<subject>.+?): (?P<values>`[a-z0-9-]+`( \| `[a-z0-9-]+`)*)`
followed by end of line, `.`, or text starting with `.` or ` —`. The namespace is the
subject with backticks removed. The canonical file is the unique `rules/*.md` file with a
line exactly `## Canonical Status Formats` outside fenced code; zero or several such files
is `status-source-missing`. The section extends to the next `## ` heading outside fenced
code or the end of the file (today: `rules/workflow-globals.md:156` to the end). Two
anchored lines with the same namespace in the canonical section is `vocabulary-conflict`.

The delivery adds, inside that section, after the `## Phases` code block:

```text
Status values for `## Phases` entries: `not-started` | `in-progress` | `complete`.
```

and, between the line `**Subtask statuses in `plan.md`:**` and its table:

```text
Status values for `plan.md` Status column: `not-started` | `in-progress` | `done` | `reviewed` | `deferred` | `blocked` | `not-reached`.
```

A meaning table belongs to an anchored line when, after at most one blank line, the next
line is `| Status | Meaning |`. Its first-column values (backticks removed), in order,
must equal the anchored values; otherwise `vocabulary-conflict`.

### Capability declaration (existing; format owned by spec 09 DM-4)

Spec 09 DM-4 adopted the record form below for every canonical key, in a trailing
`## Capability records` section of each declaration (aligned 2026-11-14). The generator
reads only **capability records**, the line form the git-rails section already uses
(`harness/claude/capabilities.md:31-37`):

```text
name: <key>
state: yes | no | unknown
runtime: <text>
verified: <YYYY-MM-DD>
evidence: <URL or root-relative path>
```

A record starts at a line `name: <key>` (`<key>` matching `[a-z0-9-]+`) at column 0 and
ends at the first empty line or end of file. Inside a record only the keys `state`
(required, one of the three values), `runtime`, `verified`, `evidence` (repeatable) are
allowed, each at column 0 as `<key>: <value>`; `runtime`, `verified` and at least one
`evidence` are required unless `state` is `unknown`; `verified` must be a valid calendar
date. A violation, or two records with the same name in one file, is `capability-schema`
(exit 2). Every line outside records — headings, prose, tables, other `key: value`
lines such as `hooks: yes` at `harness/claude/capabilities.md:3` — is ignored (REQ-20).
Limitations stay prose in the declaration (DM-4's `Limitations:` paragraph after a record
lies outside the record) and are not rendered. An `evidence` value must be
non-empty and contain no whitespace; it is rendered verbatim and never fetched or resolved.
`always-on-path` is not a record: spec 09 DM-4 declares it as a plain location line
(`always-on-path: <path>`), which falls outside records and is ignored like other lines; a
record named `always-on-path` is `capability-schema`.

Canonical keys, in spec 09 DM-4's order: `sub-agents`, `concurrent-sub-agents`,
`agent-messaging`, `hooks`, `worktrees`, `git`. Every other record name is an extension
record (for example `git-rails`, or spec 16's `sub-agent-effort`) and is rendered like a
canonical record (REQ-03, REQ-48); the generator needs no list of extension names.
Completeness of canonical records is spec 09's checker finding (`capability-key-missing`);
the generator only renders an absent key as `unknown`.

**Behaviour table (spec 09 DM-4, REQ-67).** In `rules/contract-phases.md`, the first table
after the heading `## Capabilities` (outside fenced code) whose header row is
`| Behaviour | Workflow | Requires | Without it |`. Each data row's `Requires` cell is one or
more backticked keys joined by `, `. A missing file, heading or table is `input-missing`;
a `Requires` cell not of that form is `capability-schema`. Whether a key is a canonical key
or an extension record declared by every harness is spec 09's check
(`capability-behaviour-table-invalid`); the generator treats a key a harness does not
declare as unavailable on that harness.

### Managed outputs (new)

`docs/reference/commands.md`, `docs/reference/rules.md`, `docs/reference/statuses.md`,
`docs/harness-matrix.md`, `harness/<name>/always-on.md` for each harness directory.
All are UTF-8, LF line endings, exactly one trailing `\n`, tracked in git. The manifest is
written with them but is not itself listed among the outputs.

### Manifest `docs/reference/manifest.json` (new)

```json
{
  "generator": {"path": "scripts/gen-docs.py", "sha256": "<64 lowercase hex>"},
  "inputs": [{"hash_scope": "extract", "path": "rules/contract-tdd.md", "sha256": "<hex>"}],
  "metadata_schema": {
    "loads_schema_versions": [1],
    "rule_fields": ["description", "load", "loads"],
    "workflow_fields": ["called_by", "description", "loads", "phase", "reads", "step", "writes"]
  },
  "outputs": [{"path": "docs/harness-matrix.md", "sha256": "<hex>"}],
  "schema_version": 1
}
```

Serialized as `json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"`.
`inputs` and `outputs` are sorted by `path` (Python string order on normalized POSIX
relative paths). No timestamp, absolute path, user name or random value appears. The
manifest never contains its own digest.

### Journal `docs/reference/.gen-docs.journal.json` (new; untracked)

```json
{
  "entries": [{"new_sha256": "<hex or null>", "old_sha256": "<hex or null>",
               "path": "docs/reference/rules.md", "temp": "docs/reference/.rules.md.gen-docs.tmp"}],
  "schema_version": 1
}
```

One entry per path the publication changes, the manifest included, sorted by `path`.
`old_sha256` is null when the path did not exist; `new_sha256` null means deletion of an
orphan (then `temp` is null). Written and flushed before the first replacement; deleted
after the manifest replacement. A journal that is not valid JSON or does not match this
shape is unreadable (Publication algorithm step 4).

### Auxiliary files (new; untracked)

Lock file `docs/reference/.gen-docs.lock` (kept between runs; held with an exclusive
non-blocking `fcntl.flock`, released by the kernel at process exit, never deleted or taken
over — same policy as ADR-0021 Decision 2); temporary files `<dir>/.<basename>.gen-docs.tmp`
next to each target. `.gitignore` gains `/docs/reference/.gen-docs.lock`,
`/docs/reference/.gen-docs.journal.json` and `*.gen-docs.tmp`.

### Lifecycle and migration

No consumer-project data changes. In this repository the delivery (1) adds the three list
fields to every workflow, (2) splits each harness's always-on file into header and shared
core under REQ-42, (3) adds the two anchored lines, (4) runs `--write` and commits sources
and outputs together. Rollback is a revert of the delivery commits, which restores spec
09's hand-written always-on files and the previous sync assembly; a single output file is
never rolled back alone.

## Contracts & Interfaces

### Command line

```text
python3 scripts/gen-docs.py --check [--root <dir>]
python3 scripts/gen-docs.py --write [--force] [--root <dir>]
python3 scripts/gen-docs.py --profile <name> [--root <dir>]
python3 scripts/gen-docs.py -h | --help
```

- `--root <dir>`: an existing directory (missing, not a directory, or no argument →
  `usage`); default is the physical parent of the directory holding the script. `ORCHESTRAIL_HOME` is not consulted; callers address the script
  through it, as with other helpers.
- `-h`/`--help`: usage text on standard output, exit 0.
- Standard output: `--check` prints nothing on success; `--write` prints `written <path>`
  and `removed <path>` lines in publication order and nothing when unchanged; `--profile`
  prints the fragment bytes and nothing else.
- Profile normalization: trailing `\n` characters are stripped and exactly one `\n` is
  appended. A missing `profiles/<name>/always-on-fragment.md` is `profile-not-found`; the
  fragment is subject to the same input safety and encoding rules as every input
  (`unsafe-input-path`, `input-encoding`).

### Stages and exit codes

| Code | Meaning |
|---|---|
| `0` | Check passed, write completed or unchanged, profile printed, or help |
| `1` | Inputs are valid but an output is stale, missing, edited, orphaned, too large, or the manual duplicates reference content |
| `2` | Invalid request, input, metadata, vocabulary or capability declaration |
| `3` | Runtime unavailable, lock held, ownership conflict, inputs changed, incomplete publication, unsafe output path or I/O error |

Stages run in this order; the first stage with a diagnostic ends the run with its code
after printing all of that stage's diagnostics: (1) runtime → 3; (2) arguments → 2;
(3) profile mode only: fragment safety, existence and encoding → 2, print → 0;
(4) input safety and parsing → 2;
(5) rendering and size → 1; then `--check`: (6c) journal present → 3, (7c) comparison and
manual rule → 1; or `--write`: (6w) lock → 3, (7w) input re-read → 3, (8w) recovery and
ownership → 3, (9w) publication → 3.

### Diagnostics

One line per finding on standard error:
`gen-docs: <code>: <location>: <message>`, where `<location>` is the root-relative POSIX
path, optionally `:<line>` (1-based) and `#<field>`, or `-` when no file applies. Lines are
sorted by path, line, then code. `<message>` states the expected condition and the
observed value.

### Diagnostic codes

| Code | Exit | Trigger |
|---|---|---|
| `usage` | 2 | REQ-43 |
| `runtime-unavailable` | 3 | REQ-44 |
| `profile-not-found` | 2 | Fragment file missing |
| `input-missing` | 2 | Required input or harness file absent |
| `unsafe-input-path` | 2 | REQ-15 |
| `input-encoding` | 2 | Invalid UTF-8, BOM, CR or U+001C–U+001F in a consumed input |
| `metadata-syntax` | 2 | Front matter missing or outside the grammar |
| `metadata-duplicate-key` | 2 | Repeated key |
| `metadata-missing-field` | 2 | REQ-05 |
| `metadata-unknown-field` | 2 | Key outside the schema |
| `metadata-invalid-value` | 2 | Wrong type, empty or multi-line description, bad phase or step, bad kind prefix, REQ-46 |
| `unsupported-schema-version` | 2 | `loads.schema_version` not `1` |
| `missing-target` | 2 | REQ-23 |
| `load-cycle` | — | Withdrawn 2026-11-14 (REQ-24; load cycles are spec 11's `cycle` finding) |
| `adapter-incomplete` | 2 | A harness directory without `capabilities.md`, or a `capabilities.md` directory without `deploy.env` (spec 09 DM-5) |
| `invocation-missing` | 2 | REQ-36 |
| `metadata-conflict` | 2 | REQ-35 |
| `status-source-missing` | 2 | Zero or several canonical sections |
| `vocabulary-conflict` | 2 | REQ-34, duplicate namespace, meaning table mismatch |
| `capability-schema` | 2 | REQ-47 |
| `size-limit` | 1 | REQ-17 |
| `output-missing` | 1 | Expected output absent |
| `output-stale` | 1 | Output differs from expected and equals its manifest digest; also the manifest itself differs |
| `output-edited` | 1 | Output differs from expected and from its manifest digest (or has none) |
| `output-orphaned` | 1 | Orphaned output still exists |
| `usage-link-missing` | 1 | REQ-16 |
| `usage-duplicate` | 1 | REQ-16 |
| `publication-incomplete` | 3 | REQ-41 |
| `lock-held` | 3 | REQ-32 |
| `input-changed` | 3 | REQ-30 |
| `ownership-conflict` | 3 | REQ-13, REQ-39, recovery mismatch |
| `unsafe-output-path` | 3 | An output path or its parent is a symbolic link or not a regular file/directory |
| `io-error` | 3 | Any other read or write failure |

### Publication algorithm (`--write`)

1. Parse and validate all inputs; render every output and the manifest in memory;
   enforce the size limit.
2. Create `docs/reference/` if absent; create and acquire the lock (REQ-32). The lock file
   and this directory are the only things created before step 6.
3. Re-read every input and compare consumed-content digests (REQ-30).
4. If a journal exists: when it is readable, apply REQ-28; a listed path whose bytes match
   neither digest is `ownership-conflict` and the journal is kept. When it is unreadable,
   report `publication-incomplete` (exit 3) and keep it. Under `--force`, a mismatching
   path is treated as an edited output and replaced, and an unreadable journal is deleted
   together with every `*.gen-docs.tmp` file next to a managed output path, each printed
   as `forced <path>`; publication then continues.
5. Classify each managed path: equal to expected (skip), owned (replace), adopted
   (REQ-40), edited (`ownership-conflict` unless `--force`); classify orphans (REQ-39).
   If nothing changes and the manifest is equal, exit 0 (REQ-38).
6. Write every temporary file and flush it; then write and flush the journal.
7. Replace outputs in path order, delete owned orphans, replace the manifest, delete the
   journal (REQ-27). Exit 0.

A crash at any point leaves either the previous generation, or a journal that the next
`--write` resolves and `--check` reports. `--check` takes no lock: it cannot report a pass
on a mixed set, because a pass requires every file to equal the bytes the current inputs
produce.

Test seam (documented, inert unless set): `ORCHESTRAIL_GEN_DOCS_TEST_FAULT=<boundary>`
makes `--write` terminate with `os._exit(3)` at `after-temp` (after every temporary file
and the journal are flushed), `after-replace-<k>` (after the k-th replacement, 1-based),
`before-manifest` or `before-journal-delete`; at every boundary a journal exists;
`ORCHESTRAIL_GEN_DOCS_TEST_RESUME=<path>` makes `--write` wait after step 1 until `<path>`
exists, for at most 10 s. Other values are ignored.

### Output layouts

**General byte rules.** Every Markdown output is a sequence of blocks joined by exactly one
empty line, ending with one `\n`. The first block of the four reference documents is the
line `<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->`.
A table block is a header row, a delimiter row of `|` followed by `---|` once per column,
and one row per item, each row written `| c1 | c2 | … |` with single spaces. In cells
`|` is written `\|`. A list cell renders its items in declared order, each in backticks,
joined by `, `; an empty list renders `none`. Scalars render verbatim. The Called by and
Loads rules for `commands.md` below override this list rule for those two columns.

**`docs/reference/commands.md`** — example for one workflow (`<N>` is the workflow count):

```text
<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->

# Command reference

<N> workflows.

## discovery

| Command | Step | Invocation | Description | Called by | Reads | Writes | Loads |
|---|---|---|---|---|---|---|---|
| `/discovery-analyze` | 1 | `/discovery-analyze <task-directory> [--step-by-step]` | Discovery Step 1 — Analyze task | `/discovery`, user | `<spec>`, `<task-dir>/state.md` | `<task-dir>/state.md → ## Task Analysis` | mandatory: `rules/bootstrap-discovery.md`; conditional: `rules/reference/x.md` (## Integration) when `composite_task` |

## Call cycles

none
```

One `## <phase>` section per phase that has workflows, in spec 09's phase order
(`discovery`, `execution`, `validation`, `atomic-execution`, `atomic-validation`,
`orchestrated`, `entry`, `utility`); rows sorted by step in spec 09 DM-3's order (`"-"`
first, then the integer part, then the decimal part with absent read as 0, then the
letter with absent first: `-`, `1`, `2`, `2.5`, `4`, `4a`, `4b`, `5`), then name. The Step
cell shows the parsed value (`-` for `"-"`). Called by (override): workflow names sorted, each as `` `/<name>` ``, then the
unquoted word `user` when present, joined by `, `; `none` when empty. Loads (override):
the side `mandatory: <entries>` and the side `conditional: <entries>`, a side with no
entries omitted, the remaining sides joined by `; `; both empty → `none`. An
entry is the backticked path, then ` (` + sections joined by `; ` + `)` when `sections` is
present, and for conditional entries ` when ` + the backticked `condition_id`. Entries keep
declared order, joined by `, `. `## Call cycles` is always the last section: `none`, or one
line per strongly connected component of the caller graph (edges caller → workflow, `user`
excluded) that has more than one workflow or a self-edge, written as its `` `/<name>` ``
members sorted and joined by `, `, lines sorted by their first member.

**`docs/reference/rules.md`**:

```text
<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->

# Rule reference

<N> rules, <M> reference documents.

## Rules

| Rule | Kind | Load | Skill | Description |
|---|---|---|---|---|
| `contract-tdd` | contract | always | `rule-contract-tdd` | TDD contract |

## Reference documents

| Document | Skill |
|---|---|
| `rules/reference/tdd.md` | `ref-tdd` |
```

Rules sorted by kind (`bootstrap`, `contract`, `protocol`, `procedure`), then name;
reference documents by name. With no reference documents the second table is replaced by
the line `none`.

**`docs/reference/statuses.md`**:

```text
<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->

# Status reference

Source: `rules/<canonical file> → ## Canonical Status Formats`. Transitions and field rules are defined there.

## `atomic-tests`

Values: `not-started` | `red` | `pinned` | `green` | `n-a` | `failed`

## `plan.md` Status column

Values: `not-started` | `in-progress` | `done` | `reviewed` | `deferred` | `blocked` | `not-reached`

| Status | Meaning |
|---|---|
| `not-started` | Not started |
```

One `## <subject as written>` section per anchored line, in document order of the
canonical section; the meaning table is copied cell text verbatim.

**`docs/harness-matrix.md`**:

```text
<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->

# Harness capability matrix

Declared support from `harness/<name>/capabilities.md`. `unknown` means not declared and is treated as unavailable. Limitations, installation results and checkpoint coverage are not shown here; see each declaration and the deployed installation record.

| Capability | claude | codex |
|---|---|---|
| `sub-agents` | yes | unknown |

## claude

| Capability | State | Runtime | Verified | Evidence |
|---|---|---|---|---|
| `git-rails` | yes | Claude Code 2.1.317 | 2026-11-03 | `https://code.claude.com/docs/en/hooks`, `https://code.claude.com/docs/en/permissions` |
```

After the harness sections comes `## Behaviours`: a table with header
`| Behaviour | Requires | <harness 1> | <harness 2> |`, one row per behaviour-table row in
table order, the Behaviour cell verbatim, Requires as backticked keys joined by `, `, and
each harness cell `available` or `unavailable` (REQ-48).

Rows: canonical keys in spec 09 DM-4's order, then extensions sorted by name; harness columns
and `## <harness>` sections sorted by name. The summary table has a row for every canonical
key and every extension declared by any harness; a key a harness does not declare shows
`unknown`. A harness section lists only the records that harness declares; an empty
runtime, verified or evidence cell (state `unknown`) renders `none`.

**`harness/<name>/always-on.md`**: the line
`<!-- Generated by scripts/gen-docs.py; edit the sources, not this file. -->`, then the
header, the shared core and the capability declaration, each with trailing `\n`
characters removed, joined by `\n\n`, followed by one `\n`. The file therefore contains
the capability declaration exactly once, and nothing else besides the body. Its always-on
body (spec 09 REQ-54) is the provenance line, header and core joined the same way; the
provenance line counts 11 words toward the 1,200-word limit (REQ-17). A word counter over
the file (spec 11's meter) must count this file alone and must not add
`harness/<name>/capabilities.md` again, or the declaration is counted twice.

### Manual duplication rule (`docs/USAGE.md`)

`--check` requires the relative link targets `reference/commands.md`,
`reference/rules.md`, `reference/statuses.md` and `harness-matrix.md` (as `](<target>)`).
A missing `docs/USAGE.md` yields `usage-link-missing` for all four. Outside fenced code it
reports `usage-duplicate` (location = the line) for: (a) a table row whose first cell
starts with `` `/ ``; (b) a table row whose first cell contains a backticked token equal
to the file name of a top-level `workflows/*.md` or `rules/*.md`; (c) a table row whose
first cell is exactly one backticked value of a namespace in `statuses.md`; (d) a line
that is not a table row holding two or more backticked tokens joined by ` | ` that all
belong to one namespace. Table delimiter rows are ignored. At `060ce6d`, rows
`docs/USAGE.md:512-571` match (a), `:743-752` and `:767-808` match (b), `:826-832` match
(c), and lines `:836`, `:849`, `:851` match (d); the delivery replaces them with links.

### Deployment contract (`scripts/sync.sh`)

Gate location (aligned 2026-11-14): in spec 09's `scripts/sync.sh` step list, after the
contract validator (step 2) and before hook installation (step 4), the first step that
writes outside the source root; the runtime guard (step 3) precedes it, and spec 11's
`measure-context.sh check` gate follows it (11 Contracts → Deployment). Legacy reporting
precedes it only in spec 20's step list. Once spec 20 is delivered, the gate's position in
`scripts/sync.sh` is owned by spec 20 (its REQ-64), which also runs the same command inside
its installer engine (its REQ-40); this spec then owns only the command and its exit
semantics. Sync runs
`python3 -I "$ROOT/scripts/gen-docs.py" --check --root "$ROOT"`. On exit 1 it prints
`ERROR: generated files are not current. Run: python3 scripts/gen-docs.py --write`; on any
other non-zero exit it prints `ERROR: generated-file check failed (exit <code>); see the
diagnostics above`; in both cases it exits 1 (REQ-22).

Always-on bytes and handover (aligned 2026-11-14): for each harness, the bytes written to
its `always_on_path` are exactly
`<bytes of harness/<name>/always-on.md>` + `"\n## Current hook installation\n\ninstallation-result: " + <result> + "\n"`,
where `<result>` follows spec 09 REQ-65: the hook installer's JSON for a harness whose
directory has `hooks.json`, else `{"reason":"no-native-adapter","status":"unavailable"}`.
This replaces spec 09's DM-14 assembly (09 REQ-36: "Spec 19 later replaces the assembly with
its generated file without a second append"): the component that writes `always_on_path`
— spec 09's `scripts/deploy-skills.py deploy` until spec 20, then spec 20's engine (its
REQ-39, which already states these bytes) — drops DM-14's marker line and appended
declaration. `harness/<name>/always-on.md` keeps its path and becomes a generated output in
the delivery that splits it (REQ-42); spec 09's checks keep applying to it (09 REQ-36,
REQ-54). Paths come from `deploy.env` (09 DM-5) and are not changed by this spec.

Fixture consequences, all in the same change (line numbers are those at `060ce6d`; spec 09
re-points these fixtures first, so the implementer applies the same changes to their
post-09 form): (1) `copy_source` in `tests/hook-install.sh:70-73` also copies `docs/`, so
the private copy holds the current generation, the manifest and `docs/USAGE.md` and the
gate passes; the same holds for any fixture of spec 09's `scripts/check-deploy-skills.py`
that runs sync on a private copy; (2) the sync assertions (`tests/hook-install.sh:790-795`
today) and every spec 09 deploy case asserting the DM-14 assembly expect the generated
`harness/<name>/always-on.md` plus the installation record; (3) because
`tests/hook-install.sh` is an approved path of the frozen inventory, its resource entry in
`tests/fixtures/validator-runtime/inventory-amendment.json` is re-amended in the amendment
schema then in force (spec 09 DM-9 schema 2 once 09 is delivered), and `AMENDMENT_SHA256` in
`tests/validator-runtime-oracle.py` is updated; (4) the source-guard records that pin
`scripts/sync.sh`, `tests/hook-install.sh` and the oracle are refreshed under
`tests/fixtures/validator-runtime/README.md:9-28` (ADR-0020 Decision 2 precedent).

### Acceptance suite (`scripts/check-gen-docs.py`)

A standard-library Python 3.11+ `unittest` program, run as
`python3 scripts/check-gen-docs.py`; exit 0 when every case passes, 1 otherwise. It builds
each fixture source root in a temporary directory with an isolated `HOME` (here and in the
acceptance criteria: `HOME`, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` set to temporary paths,
09 REQ-47), copies
`scripts/gen-docs.py` into it, and runs the generator as a subprocess with `--root`. It
never runs `scripts/validate-contracts.sh`; the sync case (AC-12, AC-15) replaces the
validator in its private copy with `#!/bin/bash\nexit 0\n`, as `tests/hook-install.sh:135-138`
does. It is not registered in `scripts/validate-contracts.sh` (A-33); `scripts/README.md`
lists it as standalone.

## Non-Functional Requirements

| Attribute | Target | Verification |
|---|---|---|
| Determinism | Byte-identical outputs and manifest for identical inputs under different `LC_ALL`, `TZ`, `HOME`, working directory, `PYTHONHASHSEED` and reversed directory enumeration | AC-01, AC-11 |
| Offline | Zero network connections, model calls and subprocesses in every mode | AC-02 (socket and subprocess creation patched to raise) |
| Portability | Python 3.11+, standard library only; writes on Linux and macOS local filesystems (`fcntl`) | AC-19; static import check in `scripts/check-gen-docs.py` |
| Safety | Zero modified or deleted files outside the managed set and auxiliary files; zero lost hand edits without `--force` | AC-09, AC-10 |
| Size | Each always-on body (provenance line, header and core; spec 09 REQ-54) ≤ 1,200 words, counted per spec 09 DM-19 | AC-14 |
| Performance | N/A — the generator and its suite are outside `scripts/validate-contracts.sh` (A-33), so the validator budgets of ADR-0018 do not apply to them, and no owner-approved target exists for sync or the generator. The delivery records the measured wall time of `--check` on this repository and of the suite, with machine and Python version, as evidence only | Delivery record |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| No manifest yet, outputs absent | `--write` creates all; `--check` reports `output-missing` for every output and the manifest | REQ-09, REQ-40 |
| No manifest, an output exists with expected bytes | Adopted | REQ-40 |
| No manifest, an output exists with other bytes | `--write`: `ownership-conflict`; `--check`: `output-edited` | REQ-13 |
| Manifest unreadable or not matching its schema | `--check`: `output-stale` for the manifest; `--write`: treated as absent (no path owned through it) | REQ-09, REQ-13 |
| Hand-edited output | `--check` exit 1 `output-edited`; `--write` exit 3, bytes kept; `--write --force` replaces | REQ-13, REQ-29 |
| Unrelated file inside `docs/reference/` | Never read, listed or deleted | REQ-14 |
| Harness retired (its `deploy.env`, `capabilities.md` and header deleted) | Its `always-on.md` is orphaned: `--check` `output-orphaned`; `--write` deletes it when owned, else `ownership-conflict` | REQ-09, REQ-39 |
| Harness directory with `capabilities.md` but no header | `input-missing` | Data Model |
| Directory with `capabilities.md` but no `deploy.env`, or with `deploy.env` but no `capabilities.md` | `adapter-incomplete` | Data Model |
| Directory holding only an orphaned `always-on.md` | Not reported as a harness; `--check`: `output-orphaned` when the manifest lists it; `--write` deletes it when listed and owned | REQ-09, REQ-39 |
| No harness directory at all; hidden directory under `harness/` | `input-missing` (location `harness/`); hidden directory ignored | Data Model |
| Workflow body edit only | Outputs and manifest unchanged; `--check` exit 0 | REQ-02 |
| Empty `reads`/`writes`/`called_by` | Valid; rendered `none` | REQ-05 |
| Missing field in a workflow with only spec-09 fields | One `metadata-missing-field` per missing field | REQ-05 |
| Two `Invocation:` lines, or one only inside a code fence | `invocation-missing` | REQ-36 |
| `\|` inside an invocation or description | Escaped `\|` in the table | Contracts |
| `Called by:` prose naming a non-caller after the leading list | Not compared | REQ-35 |
| Self-call or mutual callers | Accepted; listed under `## Call cycles` | REQ-25 |
| `loads` cycle, missing `loads` target or section | Not checked by the generator; spec 11's meter reports it in its own sync gate step (11 REQ-08) | REQ-23, REQ-24 |
| Step values `2.5`, `4a`, `4b`, `-` | Sorted `-`, `2.5` after `2`, `4a`, `4b` after `4` | Contracts |
| `Requires` key not declared by a harness | That harness `unavailable` for the behaviour | REQ-48 |
| Top-level rule with a `loads` block | Parsed, not rendered | REQ-49 |
| Duplicate anchored line in another rule with equal values | Accepted; reference cites canonical file only | REQ-34 |
| Status value mentioned only in prose | Not listed | REQ-20, REQ-33 |
| Capability key undeclared | `unknown` | REQ-03 |
| Malformed capability record (bad state, missing evidence, duplicate name, bad date) | `capability-schema` | REQ-47 |
| Symlinked input or profile fragment, `..`, outside root | `unsafe-input-path` | REQ-15 |
| Output path is a symbolic link | `unsafe-output-path`, nothing written | Contracts |
| Input changes after rendering | `input-changed`, nothing written except the lock file | REQ-30 |
| Second concurrent `--write` | `lock-held` | REQ-32 |
| `--check` during a `--write` | Reports drift or `publication-incomplete`; never a false pass | REQ-09, REQ-41 |
| Crash at each publication boundary | Journal left; next `--write` completes; `--check` exit 3 until then | REQ-27, REQ-28 |
| Journal lists a path edited after the crash | `ownership-conflict`, journal kept; `--write --force` replaces the path | REQ-28, REQ-29 |
| Journal unreadable | `--check` and `--write`: `publication-incomplete`, journal kept; `--write --force` deletes it and the temporary files, then publishes | REQ-29, REQ-41 |
| Rendered always-on over 1,200 words | `size-limit`, nothing written | REQ-17 |
| Input with CRLF or BOM | `input-encoding` | Data Model |
| Profile missing or bad name | `profile-not-found` / `usage` | REQ-08, REQ-43 |
| `--root` missing or not a directory | `usage` | REQ-43 |
| `docs/USAGE.md` missing on `--check` | `usage-link-missing` for all four links | REQ-16 |
| Python older than 3.11 | `runtime-unavailable` | REQ-44 |
| Disk full or permission denied during publication | `io-error` exit 3; temporary files and journal left for recovery | REQ-27, REQ-28 |
| Metadata value `$(touch x)` or `{{ x }}` | Rendered literally; no file `x` | REQ-26 |
| Stale outputs when sync runs | Sync exits 1 before installing hooks or copying anything | REQ-22 |

## Acceptance Criteria

All criteria except AC-10's delivery part and AC-21 are implemented first as failing
cases in `scripts/check-gen-docs.py` (disposable source roots in temporary directories,
isolated `HOME`); AC-10's delivery part and AC-21 are verified once on the delivery commit
and recorded as task evidence. "Tree unchanged" means identical bytes, modes and mtimes of
every file under the fixture root, ignoring `docs/reference/.gen-docs.lock` and the
creation of an empty `docs/reference/` directory.

- **AC-01** (REQ-01, REQ-07, REQ-31) — Given a fixture with harnesses `alpha` and `beta`, a
  marker string present only in a rule file, When `--write` runs twice and once more under
  different `LC_ALL`, `TZ`, `HOME`, working directory and `PYTHONHASHSEED`, Then all three
  runs give byte-identical outputs and manifest, each `harness/<h>/always-on.md` equals the
  layout under Contracts, the capability text with trailing `\n` removed occurs exactly
  once, and the marker does not occur in any always-on file.
- **AC-02** (REQ-03, REQ-04, REQ-08, REQ-20, REQ-21) — Given `alpha` declares a record for
  every canonical key and `beta` declares only a `git` record plus a prose sentence naming a
  price and a model, and profile `p1` whose fragment holds a unique marker, When `--write`
  and `--profile p1` run with socket creation and subprocess creation patched to raise,
  Then both succeed, the matrix shows `unknown` for each undeclared `beta` key, neither the
  price nor the model text appears in any output, the marker appears in no managed output
  and no manifest path starts with `profiles/`, `--profile p1` prints exactly the
  normalized fragment, and the tree is unchanged by `--profile`; a symlinked fragment gives
  `unsafe-input-path`.
- **AC-03** (REQ-05, REQ-11, REQ-12) — Given a valid fixture, When separately (a) each
  required workflow field is removed, (b) a key is repeated, (c) `reads: "x"`, (d)
  `loads.schema_version` is `2`, (e) an unknown key is added, (f) a rule is named
  `misc-x.md`, (g) a `reads` item is written unquoted, Then each run exits 2 with exactly
  the code `metadata-missing-field` naming that field, `metadata-duplicate-key`,
  `metadata-invalid-value`, `unsupported-schema-version`, `metadata-unknown-field`,
  `metadata-invalid-value`, `metadata-syntax` respectively, and the tree is unchanged.
- **AC-04** (REQ-06, REQ-10, REQ-16, REQ-36) — Given a fixture with W workflows, R rules
  and M reference documents, one invocation containing `[--a | --b]`, and a
  `docs/USAGE.md` with the four links, When `--write` then `--check` run, Then each
  workflow name appears in exactly one `commands.md` row and each rule in exactly one
  `rules.md` row, the count lines state W, R and M, the invocation cell contains `\|`, and
  `--check` exits 0. Then, separately, each of these USAGE edits makes `--check` exit 1
  with the named code at that line: a row `` | `/x` | y | `` (`usage-duplicate`, a); a row
  whose first cell is the backticked file name of a fixture workflow (`usage-duplicate`,
  b); a row whose first cell is `` `red` `` from a fixture namespace (`usage-duplicate`, c);
  the line `` `red` | `green` `` (`usage-duplicate`, d); one link removed
  (`usage-link-missing`); USAGE deleted (four `usage-link-missing`). A row whose first cell
  is `` `code-quality.md` `` and a line `` `red` | `done` `` mixing two namespaces pass. A
  workflow with two `Invocation:` lines gives `invocation-missing` exit 2.
- **AC-05** (REQ-06, REQ-33, REQ-34) — Given a canonical section with four anchored lines,
  one followed by a meaning table, a status word used only in prose, and a second rule
  file repeating one anchored line, When `--write` runs, Then `statuses.md` lists the four
  namespaces in document order with values in declared order and one meaning table, and the
  prose-only word is absent; changing the repeated line's order gives
  `vocabulary-conflict` naming both files; zero or two `## Canonical Status Formats`
  sections give `status-source-missing`; a meaning table whose rows differ from its line
  gives `vocabulary-conflict`.
- **AC-06** (REQ-09) — Given a fixture after `--write`, When separately the metadata of
  one workflow changes, one byte of the generator changes, one output is deleted, one
  output is hand-edited, and `beta`'s `deploy.env`, `capabilities.md` and header are deleted, Then
  `--check` exits 1 reporting respectively `output-stale` (affected outputs and manifest),
  `output-stale` (manifest), `output-missing`, `output-edited`, `output-orphaned` for
  `harness/beta/always-on.md`; the tree is unchanged in every case; the unmodified fixture
  gives exit 0 and empty output.
- **AC-07** (REQ-10) — Given the outputs of AC-04, When they are searched, Then no output
  contains a match of `\b[0-9]+ (checks?|tests?)\b`, and the stated counts equal the number
  of fixture files of each kind after adding and after removing one workflow.
- **AC-08** (REQ-12, REQ-27, REQ-28, REQ-29) — Given a generation and changed inputs, When
  `--write` is terminated through the fault seam at each boundary in turn, Then after every
  termination `--check` exits 3 (`publication-incomplete`) and never 0, and the next
  `--write` exits 0 leaving outputs byte-equal to an uninterrupted run with no journal or
  temporary file left; a path edited after the termination yields `ownership-conflict`
  with the journal kept, and `--write --force` then exits 0 and prints `forced <path>`; a
  journal replaced by `{` gives `publication-incomplete` on `--write`, and `--write --force`
  deletes it and the temporary files and exits 0.
- **AC-09** (REQ-13, REQ-29, REQ-39, REQ-40) — Given a generation, When (a) an output is
  hand-edited and `--write` runs, (b) `--write --force` runs after (a), (c) a foreign file
  sits in `docs/reference/`, (d) `beta` is retired, (e) `beta` is retired after its output
  was hand-edited, (f) `--write --force` runs after (e), (g) no manifest exists and one
  output already holds the expected bytes, (h) no manifest exists and one output holds
  other bytes, Then (a) exits 3 `ownership-conflict` with the edit preserved, (b) replaces
  it and prints `forced <path>`, (c) leaves the foreign file untouched, (d) deletes
  `harness/beta/always-on.md`, (e) exits 3 `ownership-conflict` with the file kept, (f)
  deletes it and prints `forced <path>`, (g) adopts it and exits 0, (h) exits 3
  `ownership-conflict`.
- **AC-10** (REQ-14, REQ-42) — Given a fixture, When `--write` runs, Then every input and
  every file outside the managed set, the manifest and the auxiliary files is unchanged.
  On the delivery commit: for each harness the multiset of non-empty lines of
  `always-on-header.md` plus `always-on-core.md` equals that of `harness/<name>/always-on.md`
  at the parent commit, and `git diff` against the parent commit shows no change under
  `.ai/tasks/completed/`, `.ai/specs/completed/`, `docs/audits/`, `docs/analysis/` or
  `.ai/adr/` other than the new ADR and its index line.
- **AC-11** (REQ-15, REQ-23, REQ-24, REQ-25, REQ-30, REQ-31) — Given a valid fixture,
  When separately an input is a symlink to a file outside the root, a `loads` path contains
  `..`, a `called_by` names a missing workflow, a `loads` path names a missing rule file and
  another names a missing section, two rules load each other, workflow `a` lists itself and
  workflows `b` and `c` list each other in `called_by`, an input is modified while
  `--write` waits on the resume seam, and directory enumeration is reversed, Then the runs
  give `unsafe-input-path`, `metadata-invalid-value` (11 DM-1 path rule),
  `missing-target`, exit 0 for each of the missing-file, missing-section and mutual-load
  fixtures (no generator diagnostic; those are spec 11's findings), exit 0 with
  `## Call cycles` holding exactly the lines `` `/a` `` and `` `/b`, `/c` ``,
  `input-changed` exit 3 with the tree unchanged, and output identical to the unreversed
  run.
- **AC-12** (REQ-07, REQ-18, REQ-19) — Given an isolated `HOME` and a private checkout copy
  with a current generation and the validator replaced by a stub, When `scripts/sync.sh`
  runs twice, Then each deployed always-on file equals the generated bytes plus exactly
  one installation record per Contracts, the capability text occurs once, the second run
  leaves both files byte-identical, and no deployed skill or file equals the bytes of
  `templates/always-on-core.md` or of any header.
- **AC-13** (REQ-02, REQ-38) — Given a generation, Then the manifest parses with the keys
  and sorting under Data Model, every output digest equals the SHA-256 of the file,
  `generator.sha256` equals the script's digest, and no absolute path or timestamp occurs;
  When a workflow body below its front matter changes, Then `--check` exits 0 and the
  manifest is unchanged; When `--write` runs on an unchanged tree, Then it prints nothing,
  exits 0 and the tree is unchanged.
- **AC-14** (REQ-12, REQ-17) — Given a fixture whose always-on body (provenance line,
  header and core) has 1,200 words and whose capability declaration has 500 words, When
  `--write` runs, Then it succeeds; with a 1,201-word body it exits 1 with `size-limit`
  stating `1201` and the tree is unchanged. Words are counted with Python `str.split()`.
- **AC-15** (REQ-22) — Given a private checkout copy with the validator stubbed and one
  workflow's `reads` changed without regeneration, When `scripts/sync.sh` runs with an
  isolated `HOME`, Then it exits 1, its output contains
  `Run: python3 scripts/gen-docs.py --write`, and nothing exists under the isolated `HOME`
  that did not exist before the run.
- **AC-16** (REQ-26) — Given metadata values `$(touch pwned)`, `__import__('os')` and
  `{{ core }}`, When `--write` runs, Then they appear verbatim in `commands.md` and no file
  `pwned` exists anywhere under the fixture root or the working directory.
- **AC-17** (REQ-32) — Given another process holding the lock, When `--write` runs, Then
  it exits 3 with `lock-held` while the lock is still held, and the lock file still exists
  afterwards.
- **AC-18** (REQ-35) — Given existing workflows `a` and `b` and a workflow whose
  `Called by:` line is `` Called by: `/a` or `/b` as Step 2. `` with `called_by` listing
  only `a`, When `--write` runs, Then it exits 2 with `metadata-conflict`; listing `a`,
  `b` and `user` passes; a line `` Called by: `/a`, `/b`. `` with `called_by` listing `a` and
  `b` passes; a line `` Called by: `/a` as Step 2, after `/b`. `` with `called_by` listing
  only `a` passes.
- **AC-19** (REQ-37, REQ-43, REQ-44) — Given three independent metadata errors in two
  files, When `--write` runs, Then standard error holds exactly three lines matching
  `^gen-docs: [a-z-]+: [^:]+(:[0-9]+)?(#[a-z_]+)?: .+$` sorted by path, line and code;
  invocations with no mode, two modes, `--force` with `--check`, an unknown option,
  `--root` naming a missing directory and `--profile Bad_Name` each exit 2 with `usage`;
  `runtime_guard((3, 10))` returns `3` and prints `runtime-unavailable`,
  `runtime_guard((3, 11))` returns `None`, and the module's top-level statements before the
  guard call import only `sys` (checked with `ast`).
- **AC-20** (REQ-41) — Given a journal file, When `--check` runs, Then it exits 3 with
  `publication-incomplete` and the tree is unchanged.
- **AC-21** (REQ-45) — Given the delivery commit, Then `scripts/validate-contracts.sh` is
  byte-identical to the parent commit and passes; When the no-attribution sentence is
  removed from `templates/always-on-core.md` in a scratch copy and `--write` runs there,
  Then the validator's no-attribution check fails for every `harness/<name>/always-on.md`.
- **AC-22** (REQ-46) — Given entries `../x`, `/abs`, `<unknown>/x`, `code → # Bad`,
  `` a`b ``, `a|b` and `x/<task-dir>`, When `--write` runs on each, Then each exits 2 with
  `metadata-invalid-value` naming the entry; `<task-dir>/state.md → ## Subtask Progress`,
  `code`, `run-log` and `.ai/adr/*.md` pass.
- **AC-23** (REQ-47) — Given a fixture, When separately a record has `state: maybe`, a
  `yes` record lacks `evidence`, a record has `verified: 2026-13-01`, two records share a
  name, a record holds an unknown key, a harness directory lacks its header, and
  `harness/` has no harness directory, Then each run exits 2 with `capability-schema` for
  the first five and `input-missing` for the last two; a hidden directory `harness/.x/`
  holding a `capabilities.md` is ignored; a directory with `capabilities.md` but no
  `deploy.env`, and one with `deploy.env` but no `capabilities.md`, each give
  `adapter-incomplete` exit 2; a directory holding only an `always-on.md` not listed in the
  manifest is ignored.
- **AC-24** (REQ-48) — Given harness `alpha` declaring `sub-agents`, `git` and an extension
  record `sub-agent-effort` with `state: yes`, harness `beta` declaring `sub-agents` with
  `state: yes` only, and a behaviour table with rows requiring `` `sub-agents` ``,
  `` `sub-agents`, `git` `` and `` `sub-agent-effort` ``, When `--write` runs, Then
  `## Behaviours` lists the three rows in table order with `alpha` `available` in all three
  and `beta` `available` only in the first; the extension record `sub-agent-effort` also
  appears as a matrix row (`yes` for `alpha`, `unknown` for `beta`); a harness `gamma` whose
  `sub-agent-effort` record holds only `name:` and `state: unknown` (no `runtime`, `verified`
  or `evidence`, added 2026-11-14) is accepted, shows `unknown` in that matrix row and
  `unavailable` in the third behaviour row; a `Requires` cell
  `sub-agents` without backticks gives `capability-schema`; a fixture without the
  `## Capabilities` table gives `input-missing`.
- **AC-25** (REQ-06, REQ-49) — Given workflows in one phase with steps `5`, `4b`, `"-"`,
  `2.5`, `4a`, `2` and `4`, and a top-level rule carrying a valid `loads` block, When
  `--write` runs, Then the rows appear in the order `-`, `2`, `2.5`, `4`, `4a`, `4b`, `5`
  with the Step cells showing the parsed values (`-` for `"-"`), the rule's row in `rules.md` is unchanged by its `loads`
  block, and the run exits 0; a step `2.0` or `4ab` gives `metadata-invalid-value`; a rule
  `loads` block with `sections: ["Safety rails"]` passes the generator (heading-path rules
  are 11 REQ-18's) and one with `sections: []` gives `metadata-invalid-value`.
- **AC-26** (REQ-50) — Given a fixture harness whose `always-on.md` embeds a 500-word
  capability declaration that its `capabilities.md` also holds, When spec 11's
  `measure-context.sh measure --workflow <id>` runs (11 REQ-04), Then the measurement
  record's `always_on_words` for that harness
  equals the word count of `always-on.md` plus the `load: always` rules and their closure,
  with the 500 declaration words counted once; on the delivery commit the domain
  "Always-on set" row names `always-on.md` and not `capabilities.md`.
- **AC-27** (REQ-51) — Given the delivery commit, When spec 09's checker
  (`python3 -I scripts/lint-instructions.py`) runs, Then it reports no
  `metadata-unknown-field` for `reads`, `writes` or `called_by` in any workflow, and a
  fixture workflow with an unregistered key `foo` still gets `metadata-unknown-field`.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01 |
| REQ-02 | AC-13 |
| REQ-03 | AC-02 |
| REQ-04 | AC-02 |
| REQ-05 | AC-03 |
| REQ-06 | AC-04, AC-05, AC-25 |
| REQ-07 | AC-01, AC-12 |
| REQ-08 | AC-02 |
| REQ-09 | AC-06 |
| REQ-10 | AC-04, AC-07 |
| REQ-11 | AC-03 |
| REQ-12 | AC-03, AC-08, AC-14 |
| REQ-13 | AC-09 |
| REQ-14 | AC-10 |
| REQ-15 | AC-11 |
| REQ-16 | AC-04 |
| REQ-17 | AC-14 |
| REQ-18 | AC-12 |
| REQ-19 | AC-12 |
| REQ-20 | AC-02 |
| REQ-21 | AC-02 |
| REQ-22 | AC-15 |
| REQ-23 | AC-11 |
| REQ-24 | AC-11 |
| REQ-25 | AC-11 |
| REQ-26 | AC-16 |
| REQ-27 | AC-08 |
| REQ-28 | AC-08 |
| REQ-29 | AC-08, AC-09 |
| REQ-30 | AC-11 |
| REQ-31 | AC-01, AC-11 |
| REQ-32 | AC-17 |
| REQ-33 | AC-05 |
| REQ-34 | AC-05 |
| REQ-35 | AC-18 |
| REQ-36 | AC-04 |
| REQ-37 | AC-19 |
| REQ-38 | AC-13 |
| REQ-39 | AC-09 |
| REQ-40 | AC-09 |
| REQ-41 | AC-20 |
| REQ-42 | AC-10 |
| REQ-43 | AC-19 |
| REQ-44 | AC-19 |
| REQ-45 | AC-21 |
| REQ-46 | AC-22 |
| REQ-47 | AC-23 |
| REQ-48 | AC-24 |
| REQ-49 | AC-25 |
| REQ-50 | AC-26 |
| REQ-51 | AC-27 |

Every AC-01–AC-27 names at least one REQ above.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Specs 09 or 11 not delivered, or their formats differ from the sections cited here | Generator built against the wrong schema | Medium | Discovery confirms both are delivered and re-reads 09 DM-2–DM-5 and 11 DM-1 before design; fixtures follow them |
| The Claude always-on body (985 words today, plus 11 provenance words and any lines 11 REQ-31 adds) approaches the 1,200-word limit | `--write` refuses to publish | Low | `size-limit` names the count; the declaration no longer counts (09 REQ-54); content belongs to 09/11 |
| Validator inventory is frozen | The stale-output gate cannot live in the validator; a deploy without sync (manual copying) bypasses it | Medium | Gate in sync, the only deploy path (P1); standalone suite (A-33); Q-05 tracks moving the gate into the validator |
| Editing `scripts/sync.sh` and `tests/hook-install.sh` invalidates source-guard digests and the frozen-inventory amendment for `tests/hook-install.sh` | Validator fails (oracle and guard) until re-amended | High | Apply the four fixture consequences under Contracts → Deployment contract in the same change; if the amendment schema cannot express a needed change, stop and escalate as an ADR-0018 inventory change |
| `tests/hook-install.sh` private copies omit `docs/` | Every sync fixture fails at the gate | High (certain without the fix) | `copy_source` copies `docs/` (fixture consequence 1) |
| Every metadata change requires regeneration; stacked branches touching metadata conflict on generated files | Extra `--write`; restack conflicts | Medium | Extract-scoped input digests limit churn to real metadata changes; resolve a conflict by `--write` |
| `reads`/`writes` populated inaccurately for 41 workflows | Reference misleads | Medium | Grammar and caller checks; reviewer compares each entry with the workflow's numbered steps |
| Auxiliary files committed by accident | Noise in history | Low | `.gitignore` lines; AC-13 tree checks |

## Assumptions

- A-01 | Language of the spec | Resolved: rewrite in English, Russian original kept in git history and summarized with a labelled translation | Source: `rules/language.md`; `.ai/principles/coding.md:11` | Reversible: yes
- A-02 | Generator location (`bin/gen-docs.py` in the old text) | Resolved: `scripts/gen-docs.py`; no `bin/` | Source: ADR-0021 Decision 3 (`.ai/adr/0021-task-07-schedule-state-tool.md:74-86`); `scripts/README.md`; ADR at delivery | Reversible: yes
- A-03 | Runtime | Resolved: Python 3.11+, standard library only | Source: ADR-0009 Decision 6 (`:243-244`); existing helpers (`scripts/README.md` run-log timing) | Reversible: yes
- A-04 | Source root | Resolved: `--root` or the script's own checkout; `ORCHESTRAIL_HOME` not consulted | Source: best practice, smallest choice (a maintainer tool must not write into another checkout implicitly) | Reversible: yes
- A-05 | Machine-readable status format (open decision in old §4.2/§8) | Resolved: existing anchored vocabulary lines plus two added lines; meanings from an adjacent table | Source: `.ai/principles/coding.md:39-41`; spec 07 C-4 rename-following; ADR at delivery | Reversible: yes
- A-06 | Canonical status file after 09's renames | Resolved: located by the `## Canonical Status Formats` heading, not by file name | Source: spec 09 DM-10 moves `workflow-globals` (which holds the section) → `contract-phases`, while the old text of this spec named `contract-state-files`; heading lookup is independent of that outcome | Reversible: yes
- A-07 | Transitions in `statuses.md` | Resolved: not rendered; the reference links to the canonical section | Source: old §4.2 ("not a new transition engine"); spec 07 D-05 (no transition table) | Reversible: yes
- A-08 | Duplicated anchored lines in other rules | Resolved: tolerated only when identical, as a guard against divergence; invariant 11 (`.ai/principles/domain.md:65`) still calls for one definition, and spec 09 keeps the duplicate `rules/workflow-reference.md:226-227` (09 REQ-64, AC-42; it lands in `rules/contract-state-files.md` under 09 DM-12), so REQ-34 tolerates it while identical and its removal is a follow-up outside this spec | Source: current repository state; best practice (fail on divergence rather than on an existing duplicate the generator does not own) | Reversible: yes
- A-09 | Input hashing | Resolved: extract-scoped digests for workflows and rules, whole-file digests for always-on parts | Source: best practice — whole-file digests would stale the manifest on every body edit and conflict across stacked branches (`rules/git-flow.md` stack model); ADR at delivery | Reversible: yes
- A-10 | `generator_version` in the manifest | Resolved: omitted; `generator.sha256` identifies the generator | Source: best practice (a version without a bump rule adds nothing) | Reversible: yes
- A-11 | Lock policy | Resolved: `fcntl.flock`, non-blocking, no stale takeover | Source: ADR-0021 Decision 2 | Reversible: yes
- A-12 | Recovery strategy | Resolved: treat journal-recorded old/new digests as owned and republish from current inputs; no roll-forward from temporary files | Source: best practice, smallest correct choice (generation is deterministic) | Reversible: yes
- A-13 | List-field grammar | Resolved: `[]` or block items of JSON strings | Source: best practice (parseable with the standard library) | Reversible: yes
- A-14 | `reads`/`writes` semantics and grammar | Resolved: Location grammar with four area tokens and five placeholders, no conditions | Source: old §4.1 ("relative paths or named area patterns"); `docs/USAGE.md:510-565` shows the kinds of entries in use | Reversible: yes
- A-15 | External entry point in `called_by` | Resolved: literal `user` | Source: old §4.1 ("external entry point distinguishable from an internal name"); best practice | Reversible: yes
- A-16 | Consistency with prose `Called by:` lines | Resolved: name sets must match when the line exists | Source: `.ai/principles/architecture.md` P6 ("a statement in two places is a defect"); `.ai/principles/coding.md:22` keeps the line | Reversible: yes
- A-17 | Size limits enforced by the generator | Resolved: only 1,200 words per always-on body (A-42); 300/700/6,000 remain with their owners | Source: spec 09 REQ-32 (300) and REQ-54 (1,200); spec 11 REQ-01 (700, 6,000); `.ai/principles/architecture.md` P6 (one owner per statement) | Reversible: yes
- A-18 | Installation record and the 1,200-word limit (superseded by A-42) | Resolved: the limit applies to the generated file; the appended installation record is not counted by the generator | Source: best practice; deployed-file limits belong to 09 | Reversible: yes
- A-19 | Templating | Resolved: plain concatenation, no placeholders | Source: old REQ-11 (template is not code) | Reversible: yes
- A-20 | Where agents find the installation result after the change | Resolved: sync keeps appending the existing record to the deployed file | Source: `rules/run-log.md:117-121`; `scripts/sync.sh:66` | Reversible: yes
- A-21 | Capability declaration in the always-on file | Resolved: embedded verbatim; the matrix is a separate rendered view | Source: old §2 ("exactly one capability table"), `scripts/sync.sh:62` behaviour; old spec 11 text ("without a second interpretation") | Reversible: yes
- A-22 | Harness discovery (superseded by A-43) | Resolved: every non-hidden directory under `harness/` that contains `capabilities.md` (refined by A-40) | Source: ADR-0009 Decision 2 ("`sync.sh` iterates the directory") | Reversible: yes
- A-23 | Reference documents in `rules.md` | Resolved: names and skill names only | Source: spec 11 owns their schema; smallest choice | Reversible: yes
- A-24 | Manual deduplication scope | Resolved: `docs/USAGE.md` command, rule and workflow tables and status vocabulary lines; `docs/PIPELINE.md` excluded | Source: old REQ-06 names `docs/USAGE.md` only | Reversible: yes
- A-25 | Plan mode, JSON report, diff output | Resolved: not delivered | Source: old §5 marks them optional ("may") | Reversible: yes
- A-26 | `--check` and the lock | Resolved: no lock; journal check plus full comparison | Source: best practice (read-only mode creates no file) | Reversible: yes
- A-27 | Input normalization | Resolved: reject invalid UTF-8, BOM and CR | Source: old REQ-05 ("silent filling is forbidden"), best practice | Reversible: yes
- A-28 | Test seams | Resolved: two environment variables, inert unless set | Source: spec 07 precedent (`STATE_TOOL_TEST_RESUME`) | Reversible: yes
- A-29 | Validator registration | Superseded by A-33 (the amendment format cannot add checks) | Source: `tests/validator-runtime-oracle.py:46-57` | Reversible: yes
- A-30 | Content checks after the split | Superseded by A-36 | Source: spec 09 DM-10 already maps both pre-split files to `harness/<name>/always-on.md` | Reversible: yes
- A-31 | Step ordering (superseded by A-44) | Resolved: integers ascending then `-`; follows whatever 09 permits | Source: spec 09 REQ-13 | Reversible: yes
- A-32 | Capability declaration syntax (the previous 09 text listed facts only) | Resolved: `name:`-started capability records as in `harness/claude/capabilities.md:31-37`; other lines ignored; limitations not rendered | Source: existing record form in the repository; best practice, smallest choice; adoption requested from 09 (Q-04) | Reversible: yes
- A-33 | Where the stale-output gate and the suite run (old REQ-09 named `validate-contracts.sh`) | Resolved: `scripts/sync.sh` runs `--check` before deploying; the suite is standalone `scripts/check-gen-docs.py`; the validator is unchanged | Source: ADR-0019 Decision 3 (accepted ADR outranks the old spec text: inventory frozen, standalone checker precedent); `tests/validator-runtime-oracle.py:46-57`; `.ai/principles/architecture.md` P1 (sync is the only deploy path) | Reversible: yes
- A-34 | Bounded call repetition (old REQ-11 and AC-11: "preserved stop condition, checked separately") | Resolved: call cycles are accepted and listed separately under `## Call cycles`; their stop conditions are prose and are not verified by the generator | Source: REQ-20 (no prose parsing); old REQ-11 (metadata is data); narrowing recorded here | Reversible: yes
- A-35 | Which names in a `Called by:` line are callers | Resolved: only the leading caller list | Source: current lines name non-callers after the first name (`workflows/pae-tests.md:6`, `workflows/suggest-commit-message.md:6`); best practice | Reversible: yes
- A-36 | Validator content checks on always-on text | Resolved: no validator change; the generated file keeps spec 09's path and full text | Source: spec 09 DM-10 (`rules/global-claude.md`, `templates/codex-global-AGENTS.md` → `harness/<name>/always-on.md`); ADR-0019 Decision 3 (frozen inventory) | Reversible: yes
- A-37 | Front matter grammar (the previous 09 and 11 texts gave examples only; now 09 DM-2/DM-3 and 11 DM-1, A-51) | Resolved: the line grammar under Data Model → Workflow metadata, covering both examples | Source: best practice (standard-library parser, strict rejection per old REQ-11) | Reversible: yes
- A-38 | Provenance line and the size limit | Resolved: one 11-word provenance line, counted toward 1,200 | Source: best practice (short line); counted as part of the body per spec 09 REQ-54 (A-42) | Reversible: yes
- A-39 | Way out of a stuck journal | Resolved: `--write --force` resolves mismatches and unreadable journals | Source: old REQ-13 (explicit regeneration after review) | Reversible: yes
- A-40 | Retiring a harness (superseded by A-43) | Resolved: delete `capabilities.md` and the header; the owned `always-on.md` becomes an orphan | Source: best practice; makes REQ-39 reachable | Reversible: yes
- A-41 | Python at deploy time (ADR-0009 Decision 6 calls generators optional tools) | Resolved: the sync gate requires Python 3.11+; deployment already depends on Python because sync runs the validator, which runs Python suites by default (`scripts/validate-contracts.sh:5154`) | Source: current deploy dependency; ADR-0009 Decision 6 keeps the generator optional for workflow execution, which this does not change | Reversible: yes
- A-42 | What the 1,200-word limit counts (2026-11-14) | Resolved: the always-on body — provenance line, header and core — without the embedded declaration and without the installation record | Source: spec 09 REQ-54, Terminology (Always-on body) and Notes → Spec 19 alignment | Reversible: yes
- A-43 | Harness definition and retirement (2026-11-14) | Resolved: spec 09 DM-5 — non-hidden pattern-named directory with `deploy.env`; `capabilities.md` without `deploy.env` is `adapter-incomplete`; an orphaned `always-on.md` alone is ignored as a harness; retiring deletes `deploy.env`, `capabilities.md` and the header | Source: spec 09 DM-5 ("the only harness definition") | Reversible: yes
- A-44 | Step grammar and order (2026-11-14) | Resolved: spec 09 DM-3 pattern and sort order (`"-"`, integer, decimal, letter) | Source: spec 09 DM-3 ("binding for every listing of workflows, spec 19's command reference included") | Reversible: yes
- A-45 | Capability records adopted (2026-11-14) | Resolved: the A-32 grammar is now spec 09 DM-4's; extension records render like canonical ones | Source: spec 09 DM-4, A-04, REQ-67 | Reversible: yes
- A-46 | Owner of `loads` graph checks (2026-11-14) | Resolved: spec 11's meter owns target, section and cycle checks over the whole load graph; the generator parses `loads` for rendering only | Source: spec 11 REQ-11, REQ-18, REQ-20, A-04 (workflows are never load targets); single-owner rule, `.ai/principles/architecture.md` P6 | Reversible: yes
- A-47 | Behaviour availability in the matrix (2026-11-14) | Resolved: `## Behaviours` section computed from the DM-4 behaviour table and records; validity of `Requires` keys stays spec 09's check | Source: spec 09 DM-4, REQ-67 and Notes → Spec 19 alignment | Reversible: yes
- A-48 | Gate location after spec 20 (2026-11-14) | Resolved: spec 20 owns the position (its REQ-64) and also gates its engine (its REQ-40); this spec owns the command and exit semantics | Source: spec 20 REQ-39, REQ-40, REQ-64 | Reversible: yes
- A-49 | Rules and workflows added by later specs (12–18) (2026-11-14) | Resolved: no per-spec knowledge — the generator enumerates `workflows/*.md` and top-level `rules/*.md`, takes kinds from the DM-2 prefix and phases/steps from DM-3, so files named under spec 09's Notes → Files and sections created after this spec (for example `atomic-execution-repair`, step `4`) render without change | Source: spec 09 Notes → Files and sections created after this spec; DM-2, DM-3 | Reversible: yes
- A-50 | `loads` on rules (2026-11-14) | Resolved: accepted and parsed, not rendered | Source: spec 11 DM-1, REQ-22; spec 09 DM-2 registered extension key | Reversible: yes
- A-51 | Plain-value grammar (2026-11-14) | Resolved: inside `loads`, 11 DM-1's `[A-Za-z0-9_./-]+`; top-level scalars keep spec 09 DM-2's broader grammar, because 09 owns those fields and descriptions contain spaces and colons | Source: spec 11 DM-1; spec 09 DM-2 | Reversible: yes
- A-52 | Who changes the meter's always-on composition (2026-11-14) | Resolved: this delivery (Scope item 11, REQ-50), in the change that embeds the declaration | Source: spec 11 A-11 and its always-on composition paragraph (Contracts → Graph resolution), which name 19 REQ-50 as the change; spec 11 Notes → "Ownership statements for spec 19"; spec 11 is delivered first (Preconditions). No conflict between the specs | Reversible: yes
- A-53 | Registration of spec 19's front-matter keys in spec 09's checker (2026-11-14) | Resolved: part of this delivery (Scope item 12, REQ-51) | Source: spec 09 DM-2 ("Until the owning spec registers its validator in the checker, an extension key is `metadata-unknown-field`") and DM-3 | Reversible: yes
- A-54 | Metadata of files added by specs 12–17, and the parts of 09, 11, 16 and 20 this spec depends on (2026-11-14) | Resolved: the rule parser (REQ-49) accepts every key those specs prescribe for rules — `description`, `load: on-demand` and an optional `loads` (12 REQ-46, 15 REQ-38, 14 REQ-47, 17 REQ-63; 13 A-02 for `contract-checkpoints` and `contract-delta-operations`); the workflow parser (REQ-23, REQ-51) accepts `description`, `phase` and `step` for the workflow 17 adds (`atomic-execution-repair`, `phase: atomic-execution`, `step: 4`, matching 09 DM-3) and `loads` where 13, 15, 14 and 17 add entries. No prescribed key is rejected. One consequence: those specs do not prescribe `reads`, `writes` or `called_by` for that workflow, which this spec requires of every workflow, so its front matter gets `metadata-missing-field` until the delivery that adds the file also adds the three keys (`called_by` naming `spec-run`, with its `Called by:` line starting with the backticked command, REQ-35); the generator needs no change. Nothing in this design depends on the 13 items under revision in parallel (the stop wording of 09 REQ-37, the rule for extending its closed `requirement` set in 09 REQ-69, a decision on split targets that 09 cites from spec 11); 09 is cited only by the ids already used. Spec 09 itself holds no Q-07 (verified). Spec 16's `sub-agent-effort` record is accepted with `state: unknown` and renders `unavailable` in `## Behaviours` (REQ-48, AC-24). Spec 11 agrees with A-52. Spec 20 keeps both gates (REQ-22) | Source: specs 12, 13, 15, 14, 17 front-matter sections; 09 DM-2, DM-3; 16 DM-1; 11 A-11; 20 REQ-64 | Reversible: yes

## Decisions

N/A — auto mode; no human decision was taken in this revision. Binding earlier decisions
are ADR-0009 Decisions 2 and 6 and ADR-0021 Decisions 2 and 3, cited under Context and
Assumptions.

## Clarifications

### Session 2026-11-13

No questions were asked (auto mode, owner unavailable by standing instruction). Gaps were
resolved as A-01–A-41; unresolved items are Q-01–Q-05.

### Session 2026-11-14

No questions were asked. A reconciliation pass aligned this spec with the final specs 09,
11 and 21 (A-42–A-54); Q-01, Q-02 and Q-04 were resolved by those specs.

## Open Questions

- Q-01 | resolved 2026-11-14 (A-44: spec 09 DM-3 admits these steps and fixes their order) | Spec 09 REQ-13 allowed `step` to be a positive integer or `"-"`,
  but current steps include `2.5` (`workflows/pd-select-model.md:2`), `4a`
  (`workflows/pv-classify-fixes.md:2`) and `4b` (`workflows/pd-archive.md:2`). Impact: the
  sort order of `commands.md` follows whatever 09 finally allows; 09 owns the answer.
- Q-02 | resolved 2026-11-14 (A-42: spec 09 REQ-54 limits only the body; the risk remains in Risks) | The Claude always-on content (985 + 1,607 words today) exceeds the
  1,200-word limit that the previous spec 09 text imposed on that file, and this spec adds an
  11-word provenance line. Impact: if 09 delivers a file within 11 words of the limit,
  `--write` stops with `size-limit` until 09/11 trim it; 09/11 own the content.
- Q-03 | non-blocker | Should `docs/PIPELINE.md` (command index and status glossary,
  `workflows/PIPELINE.md:108-145`) also be replaced by links? Impact: drift there remains
  possible; candidate follow-up spec.
- Q-04 | resolved 2026-11-14 (A-45: adopted as spec 09 DM-4) | Will spec 09 adopt the capability record form (A-32) for its
  canonical keys? Impact: if 09 delivers another syntax, this spec's Data Model →
  Capability declaration is reconciled before Discovery; until 09's declarations contain
  records, every canonical key renders `unknown` (today only `git-rails` is a record).
  `always-on-path` stays a plain line outside records.
- Q-05 | non-blocker | When the validator inventory accepts added checks (an ADR-0018
  inventory change), should `--check` also run inside `scripts/validate-contracts.sh`?
  Impact: until then a stale generation is caught at sync, not at validation.

## Notes

- Dependencies: 09 (names, metadata, capability format, `harness/<name>/always-on.md`,
  PIPELINE move) and 11 (`loads`, reference documents). The generator is a maintainer
  tool; no workflow requires it at run time (old §1; ADR-0009 Decision 6).
- Shared acceptance gates G1–G8 apply (`.ai/specs/README.md` → "Shared acceptance gates"); G6 is met by the
  fixture suite; no paid run is needed.
- Hint (nonbinding): parse, render, compare and publish as separate functions testable
  without the command line. The `loads` parser lives inside `gen-docs.py` (the generator
  digest covers only that file and runs under `python3 -I`).
- Hint (nonbinding): suggested subtasks — (1) metadata schema and parser with fixtures,
  (2) renderers, (3) check/publish/recovery, (4) always-on split and sync change with
  source-guard re-pinning, (5) manual cleanup and delivery records.
- Rejected: a dedicated data block for statuses (a second vocabulary definition beside the
  anchored lines); whole-file input digests (churn); deleting edited outputs without
  `--force`; rendering the installation result into the generated file (it is dynamic).
- Follow-up for other specs: 09 has adopted the record form (DM-4) and the handover (REQ-36,
  Notes → Spec 19 alignment); 21 consumes `--profile`, `docs/harness-matrix.md` and the
  always-on bytes (its REQ-39). Spec 11 already cites spec 09 DM-5 for "Harness" and records the
  composition change as carried out by this delivery (its A-11; 19 REQ-50, Scope item 11);
  nothing further is required of 11. Spec 20 keeps spec 11's meter gate step (11 REQ-08)
  next to the `gen-docs.py --check` step (20 REQ-64 and its `sync.sh` step list). The
  deployment must keep both gates, so that load cycles stay checked at deployment.
- **Identity ledger (follow-up outside this spec):** the ledger row(s) at `.ai/tasks/completed/task-01-git-source-of-truth/state.md` line 208 pins a former-name occurrence at this spec's line 19, which the refined text no longer holds; the change that commits this revision removes them, as spec 21 A-41 does for its own row.

### Change log

- 2026-11-06 — implementation/state reconciliation: Owner-authorized source review at
  `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining
  obligations, and verification limits in the Implementation review above. Preserve
  requirement/acceptance identifiers and historical decisions; repair current local
  references where needed.
- 2026-11-13 — English refinement: REQ-01–REQ-15 and AC-01–AC-12 restated; REQ-16–REQ-47
  and AC-13–AC-23 added; status source, generator path, manifest and publication contracts
  fixed.
- 2026-11-14 — reconciliation with final specs 09, 11 and 21: peer citations by REQ/DM id;
  size limit counts the always-on body (09 REQ-54); step grammar and order (09 DM-3);
  harness definition and retirement (09 DM-5, `adapter-incomplete`); records adopted (09
  DM-4) with extension records and a `## Behaviours` matrix section (REQ-48, 09 REQ-67);
  `loads` grammar, heading-path sections and plain values per 11 DM-1; `loads` accepted on
  rules (REQ-49); `loads` target, section and cycle checks left to 11 (REQ-23 narrowed,
  REQ-24 restated, `load-cycle` withdrawn); deployment handover and gate ownership after
  21 stated; AC-24–AC-27, REQ-48–REQ-51 and A-42–A-53 added; Scope items 11 (meter counts the
  embedded declaration once) and 12 (extension-key registration) added; Q-01, Q-02, Q-04
  resolved.
- 2026-11-14 — second reconciliation pass: A-52 and Scope item 11 cite spec 11's A-11 and its
  always-on composition paragraph (11 agrees that this delivery changes the meter, REQ-50),
  not the withdrawn "11 Q-03 point 1"; REQ-22 and Notes state that the deployment keeps both
  the generator gate and spec 11's meter gate (21 REQ-64 owns their position); REQ-48 and
  AC-24 settle `state: unknown` records (`unavailable`, accepted without runtime, verified or
  evidence); metadata of files added by specs 12–17 checked against REQ-23, REQ-49 and REQ-51,
  no key rejected, missing `reads`/`writes`/`called_by` on `atomic-execution-repair` recorded
  (A-54); spec 09's open decisions do not affect this design; spec 11's `loads` citation
  changed from REQ-03 to DM-1; no line-number citations of specs 10 and 13–18 exist in
  this spec.
- 2026-11-14 — independent final review: A-08 states that spec 09 keeps the duplicate status line; citations of 11 DM-3 and 09 DM-3 corrected; gate order and environment isolation aligned with 11 and 09; examples use delivered names; identity-ledger follow-up; stale citations corrected.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — single paragraph stating the outcome |
| 2 | Out of Scope names concrete exclusions | PASS — owners named per exclusion (09, 11, 21) and preconditions listed |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-51; split items reference their origin |
| 4 | REQ ↔ AC both ways | PASS — Traceability covers REQ-01–REQ-51 and AC-01–AC-27 |
| 5 | ACs binary, observable, testable first | PASS — fixture cases in `scripts/check-gen-docs.py`; AC-10 delivery part and AC-21 verified once on the delivery commit |
| 6 | NFRs measurable or N/A | PASS — performance N/A justified (outside the validator, no approved target) |
| 7 | Data model and contracts specified | PASS — inputs, grammars, manifest, journal, CLI, codes, layouts, sync contract |
| 8 | Error, empty, boundary, concurrency cases | PASS — Edge Cases table, lock and recovery contracts |
| 9 | Every ambiguity resolved or open | PASS — A-01–A-54; Q-01, Q-02, Q-04 resolved; Q-03, Q-05 open |
| 10 | No blocker question remains | PASS — Q-03 and Q-05 are non-blockers |
| 11 | Existing-code claims cited and verified | PASS — path:line citations checked against `060ce6d` |
| 12 | Terminology matches domain definitions | PASS — Terminology table; domain terms reused |
| 13 | Feature-sized (1–8 subtasks) | PASS — about five subtasks (Notes) |
| 14 | Devil's Advocate review | PASS — Review: 3 rounds, score 99/100, critic: sub-agent, open: F-28 (minor, applied after the final round) |

Reconciliation pass 2026-11-14: targeted alignment with final specs 09, 11 and 21; changed
passages checked by one independent critic; verdict unchanged. Second pass 2026-11-14:
points raised by specs 11, 21, 09, 12–17 settled (A-52, A-54); changed passages checked
by one independent critic; verdict unchanged.

Verdict: **READY FOR DEVELOPMENT** — implementation starts only after the preconditions
(specs 09 and 11 delivered) hold. Automated readiness is not sign-off.
