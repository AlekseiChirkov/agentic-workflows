# 08. Audit of rules, workflows and harness adapters before the naming migration

## Source

- **Origin:** ADR-0009 Decision 3 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:130-131`):
  "The audit of all rule and workflow files is its own spec, **08**, executed before 09; spec
  09 is amended via `/spec-sync` from its findings." Order: ADR-0009 Decision 7 as amended by
  ADR-0017 (06 before 08 and 09); roadmap order 1 in `.ai/specs/README.md` → "Dependency order".
- **Previous revision:** 2026-10-28 in Russian, plus the 2026-11-06 review (preserved below);
  its text with REQ-01–REQ-14 and AC-01–AC-10 is in this file's git history at `060ce6d…`.
- **Request, translated from Russian (08 revision 2026-10-28, §1 "Purpose and status"):**
  "Revision: 2026-10-28. This is a specification of an audit, not a statement that the audit
  is already complete. It defines a verifiable result for the next executor. Executing the
  specification does not rename rules, install skills or run models. The goal is to obtain a
  complete map of the active instructions, references, loads, mixed responsibilities and
  duplication on one pinned snapshot of the sources. From this map specification 09 receives
  exact changes to its requirements before the migration starts. The criteria of this document
  are checked by the completeness of the inventory and the reproducibility of the observations,
  not by the size of the report. Main decisions: ADR-0009, decisions 2, 3 and 7. Mandatory
  prerequisite: completed specification 01. The full 08 audit precedes 09; a partial review of
  the workflows does not replace it."
- **Snapshot the previous revision verified (translated from Russian, §2):**
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461`; [source tree](https://github.com/AlekseiChirkov/agentic-workflows/tree/8c2fa08c18115ffcf38a1798742c41e53a2c7461).
  The facts under Context & Problem were re-verified for this revision at
  `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`. Every earlier identifier keeps its meaning; Notes →
  Identifier history lists the changes.
- **This revision:** 2026-11-14, refined in place under `/spec-draft --auto-mode` with the
  owner's authorization to replace the file. No human questions were asked; every resolved gap
  is recorded under Assumptions with its source. Spec 09 (refined the same day) withdrew its
  REQ-01–REQ-04 and AC-01 into this spec; their content is covered here (Notes → Identifier
  history).

### Implementation review — 2026-11-06 (preserved)

- **Disposition:** Planned; required full audit not delivered.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Instruction-contract tests and narrower test-suite audits exist.
- **Outstanding scope and limits:** There is no delivered full rules/workflows audit with all required file rows, read-coverage evidence, link graph, duplicate clusters, and accepted migration map. This specification-delivery review is not that full audit. The historical workflow-clarity report remains unavailable.
- **Sources:** [`tests/workflow-instructions.py`](../../tests/workflow-instructions.py), `docs/audits/2026-11-06-test-suite-review.md` (absent from the current tree; link removed in this revision), [`rules/workflow-reference.md`](../../rules/workflow-reference.md).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

## Context & Problem

Verified at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff`:

1. **The audited set.** `rules/` holds 14 Markdown files, `workflows/` 42 (41 workflows and
   `workflows/PIPELINE.md`), `harness/` four (`harness/claude/capabilities.md`, `hooks.json`,
   `permissions.json`, `harness/codex/capabilities.md`); none has subdirectories. The Codex
   always-on body lives outside them in `templates/codex-global-AGENTS.md`, and spec 09 moves it
   to `harness/codex/always-on.md` (spec 09 REQ-55). `.ai/memory/architecture.md:22-23` states "42
   workflows, 14 rules, 4 principles, 10 shell scripts and 30 Python helpers"; `scripts/` holds
   11 `.sh` and 30 `.py` files.
2. **Five stems name both a rule and a workflow:** `phase-discovery`, `phase-execution`,
   `phase-validation`, `phase-atomic-execution`, `phase-atomic-validation`. Resolution is
   explained per editor in `rules/workflow-globals.md:19-27`.
3. **Known mixed-kind candidates.** `rules/phase-atomic-execution.md:49` holds
   `## Blocker Reconciliation` beside its bootstrap sections (`:8`, `:40`);
   `rules/phase-discovery.md:36,43` hold `## Codebase Reading Rules` and `## Decision Protocol`;
   `rules/quick-flow.md:156,176` hold two worked examples inside a rule;
   `rules/workflow-reference.md` (5,193 words, `wc -w`) has top-level headings from `:10` to
   `:613`, several of them template headings inside fenced blocks (for example `:38-56`).
4. **Reference syntax varies.** Section references appear with heading markers
   (`` `git-flow → ## Safety rails` ``) and without them (`` `workflow-globals → Canonical Status Formats` ``
   at `rules/tdd.md:35` and `rules/git-flow.md:278`); load lines name rules by bare stem
   (`` Load `orchestration` and `git-flow` before Step 0 `` at `workflows/spec-run.md:6`;
   `` load `workflow-reference` `` at `workflows/pav-close.md:32`) or with the word "rule"
   (`` Load the `phase-atomic-validation` rule `` at `workflows/pav-close.md:26`).
5. **The existing reference check is partial.** `tests/workflow-instructions.py:20-35` reads only
   `workflows/*.md`, only spans with `##`–`####`-marked headings (`:23`), skips a head that resolves to no file
   (`:29`), and accepts a citation when any of the two same-stem candidates holds the heading
   (`:31`). It does not see rules, unmarked headings, load lines, scripts, tests or documents.
6. **Historical audit evidence is missing.** `docs/audits/` does not exist in the tree;
   `docs/README.md:13-20` still links five files under it, ADR-0014 cites
   `docs/audits/2026-10-28-workflow-clarity-and-size.md` (`.ai/adr/0014-task-unknown-workflow-contract-clarity.md:108`),
   which `.ai/specs/README.md` → "Delivered source cleanup" records as absent, and the preserved review above cited
   `docs/audits/2026-11-06-test-suite-review.md`, also absent. The only earlier review in the tree
   is the partial naming review `docs/analysis/2026-09-16-rules-workflows-naming-review.md`
   (14 rules and 38 workflows at its date); its example of an ambiguous `phase-execution.md`
   citation in `workflows/phase-pipeline.md` no longer occurs in that file.
7. **Some duplication is intentional.** ADR-0003 Decision 2 duplicates the always-on essentials
   into `rules/global-claude.md` and `templates/codex-global-AGENTS.md`, restated at
   `rules/workflow-globals.md:29-33`.
8. **Spec 09 depends on this audit.** Spec 09 withdrew its REQ-01–REQ-04 and AC-01 into 08;
   its Notes → Ownership between 09 and 08 give 08 the inventory, link graph, duplicate
   clusters, mixed-kind detection and measurements, ask 08 to count words with spec 09's word
   count (DM-19, used by REQ-32) and to use the rule kinds of spec 09 DM-2, and ask 08 to report
   files missing from spec 09's maps. The maps DM-10, DM-11 and DM-12 are "binding unless amended
   from 08's accepted report via `/spec-sync`"; REQ-21 lets Discovery conduct merge into
   `protocol-autonomous-decision` only WHERE 08's accepted report proves complete coverage; its
   implementing task stops when 08's report is missing or not accepted (Notes → Prerequisites
   and Guard). Spec 11 consumes the proposals 08 assigns to owner 11
   (spec 11 Scope item 9).
9. **The validator's check inventory is frozen.** ADR-0019 Decision 3
   (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:68-80`) puts new contract
   tests outside `scripts/validate-contracts.sh`; the nested source guard binds the validator
   and every `.sh`/`.py` file under `tests/` (`tests/fixtures/validator-runtime/source_guard.py:809-822`),
   so `scripts/` is outside it. Precedent: the standalone `scripts/check-spec-draft.sh`
   (`scripts/README.md:20`). Re-pointing frozen checks after renames is spec 09's amendment
   mechanism (REQ-51, REQ-52; schema 2 of `tests/fixtures/validator-runtime/inventory-amendment.json`).
10. **Every tracked file is scanned for the former repository name.** The validator assembles a
    case-insensitive pattern (`scripts/validate-contracts.sh:4682-4685,4801`) and compares every
    match with the exact ledger `.ai/tasks/completed/task-01-git-source-of-truth/state.md:184-214`;
    a public-hygiene scanner also checks tracked files against local patterns
    (`scripts/validate-contracts.sh:371-427`). New audit outputs must therefore not contain the
    former name.

**Consequence:** without a complete, reproducible audit spec 09 renames and splits files on
defaults that nobody has checked against the full set of references, loads and duplicates;
spec 09's Discovery has no accepted report to start from (its Guard stops); spec 11 receives no
proposals; and dangling or ambiguous references found only after the migration are mixed with
defects the migration itself introduced.

## Goal

Maintainers obtain one pinned, reproducible audit of every rule, workflow and harness adapter
file — its kinds, sections, sizes, references in both directions, loads, legacy mentions,
verbatim and semantic duplication — produced by a read-only deterministic extractor and a
complete, machine-verified assessment, so that spec 09 receives a checked migration map and
exact amendments with their evidence, spec 11 and specs 12–15 receive owned proposals, and no
instruction, adapter or installed copy changes in the process.

## Scope

1. A read-only, standard-library Python 3.11+ tool `scripts/audit-instructions.py` with three
   subcommands: `extract` (writes the inventory), `verify` (checks inventory, assessment and
   report) and `render` (prints or writes the report's generated region).
2. A standalone `unittest` suite `scripts/check-audit-instructions.py` with fixture trees,
   including the control example of a reference to a missing section.
3. The audit outputs under `docs/audits/`: the report `YYYY-MM-DD-rules-workflows-audit.md`,
   the inventory `YYYY-MM-DD-rules-workflows-audit.inventory.json` and the assessment
   `YYYY-MM-DD-rules-workflows-audit.assessment.json`, indexed in `docs/README.md`.
4. The auditor's full reading of the primary and adapter sets and the assessment: kinds,
   mixed-kind sections, load modes, candidate dispositions, legacy roles, duplicate groups,
   migration map, spec 09 inputs, findings and proposed amendments to spec 09.
5. Index and knowledge updates: `scripts/README.md`, `.ai/context/runbook.md`,
   `.ai/memory/architecture.md` (inventory counts), `.ai/memory/state.md`,
   `.ai/memory/progress.md`.

## Out of Scope

- Any change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`,
  `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh` or another existing script, and
  fixing any defect the audit finds (REQ-04, REQ-14).
- Applying amendments to spec 09 or any other spec; `/spec-sync` of spec 09 and the owner's
  acceptance happen after this delivery (Notes → Handoff).
- Spec 09's contracts: the checker `scripts/lint-instructions.py` and its executable-reference
  grammar (spec 09 REQ-22, REQ-31), the name map, the binding maps (DM-10–DM-12), the semantics
  record, re-pointing references (REQ-25, REQ-53) and the schema-2 inventory amendment (REQ-51,
  REQ-52). 08 reuses some of their definitions without enforcing them.
- Spec 11's load metadata, tiering, size limits and measurement tool; specs 12–15's
  mechanisms; spec 19's generated documents; spec 10's golden runs.
- Token counts, cost, cached input, model or paid runs, and any economic conclusion (REQ-03).
- Reading or changing installed copies under `~/.claude`, `~/.codex` or `~/.codeium` by the
  tool; an optional manual comparison is recorded only as REQ-03 describes.
- Restoring the missing historical reports (Q-01) and repairing the dangling `audits/` links in
  `docs/README.md:13-20` (reported, not fixed).
- Registering any check in `scripts/validate-contracts.sh` or `scripts/sync.sh`.

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Owner | Accepts or rejects the report and each amendment; runs `/spec-sync` on spec 09; decides contradictions |
| Auditor (Implementer role) | Builds the tool test-first; runs `extract`; reads every primary and adapter file in full; writes the assessment and the hand-written report sections; never edits an audited file |
| Independent reviewer (Validator role) | Re-checks completeness, disputed classifications and evidence; its verdict is written to the report's review line by the single writer of the task's files |
| `scripts/audit-instructions.py extract` | Reads the root and git metadata; writes only the `--out` file |
| `scripts/audit-instructions.py verify` | Reads; prints diagnostics; writes nothing |
| `scripts/audit-instructions.py render` | Reads; prints the generated region, or with `--write` replaces only that region of the report |
| `scripts/check-audit-instructions.py` | Builds fixture trees in temporary directories; writes nothing else |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Audit | The delivery of this spec: tool, suite, inventory, assessment, report | This spec |
| Root | The repository directory the tool reads (`--root`, default the parent of `scripts/`) | Convention of `scripts/model-catalog.py` and spec 09 |
| Primary set | Every directory entry under `rules/` and `workflows/`, recursively | Previous revision §3 |
| Adapter set | Every directory entry under `harness/`, recursively, plus `templates/codex-global-AGENTS.md` | Previous revision §3; spec 09 REQ-55 (A-03) |
| Audited file | A member of the primary or adapter set | This spec |
| Reader | A file outside the audited set that the tool scans for references to audited files; it has one reader class (DM-3) | Previous revision §3 |
| Reader class | `active`, `frozen`, `planning` or `history` (DM-3) | This spec |
| Inventory | The extractor's JSON output (DM-1) | Previous revision §5.1 |
| Assessment | The auditor's JSON judgments (DM-7) | This spec |
| Report | The Markdown document (DM-8) | Previous REQ-11 |
| Edge | One occurrence of a reference from a source file to one or more audited files (DM-4) | Previous REQ-07 |
| Defect edge | An edge for which DM-4 → Defect predicate holds | This spec |
| Load edge | An edge on a load line (DM-5 → Load lines) | Spec 11 → Textual load command detection |
| Candidate | A tool-detected item the auditor must disposition: repeated load (`RL-NNN`), full-output line (`FO-NNN`) or harness-name line (`HN-NNN`) | This spec |
| Duplicate cluster | Verbatim-equal text units in two or more places (`DUP-NNN`, DM-6) | Previous REQ-08 |
| Duplicate group | The auditor's grouping of clusters and read-detected repeats with one disposition (`DG-NNN`) | Previous REQ-08 |
| Finding | `AUD-08-NNN`, one observed problem or observation with owner and closure criterion (DM-7) | Previous §5.3 |
| Proposal | A finding of a proposal type (DM-7) owned by spec 11, 12, 13, 15 or 14 | Previous REQ-02 |
| Migration map | One decision per audited file: keep, move, rename, split or merge (DM-7) | Previous REQ-09 |
| Amendment | `AMD-08-NN`, a proposed change to one identifier of spec 09 (DM-7) | Previous REQ-10 |
| Spec 09 default | The target(s) spec 09's maps give an audited file at audit time; `null` when the file is absent from them | Spec 09 DM-10, DM-11, DM-12 |
| Word | Spec 09's word count (DM-19, used by REQ-32): strict UTF-8, U+001C–U+001F rejected, `len(text.split())` over the whole text | Spec 09; equal to spec 11 counter version 1 |
| Audit complete | `verify` exits 0 and the report's review line records `pass` (REQ-14) | Previous REQ-14 |
| Report accepted | The report's acceptance line records the owner and a date | Spec 09 Notes → Prerequisites and Guard |
| Defects fixed | A later state reached by other specs; never claimed by this audit | Previous REQ-14 |

**Kinds** (classification of the report; the first four are spec 09 DM-2's rule-stem kinds,
named by ADR-0009 Decision 3; their operational definitions are this audit's, A-04):

| Kind | A file or section of this kind |
|---|---|
| `bootstrap` | Lists the ordered context sources one phase loads before acting, and that phase's behaviours (spec 09 REQ-19 shape) |
| `contract` | States formats, vocabularies, invariants or obligations that hold across workflows regardless of the current decision point |
| `protocol` | States how to decide at a named decision point: inputs, criteria and outcomes |
| `procedure` | States an ordered sequence of actions triggered by a named condition, usable from more than one workflow |
| `always-on` | Is the harness-wide essentials body delivered into every session |
| `workflow` | Is an invocable command: front-matter `description`, an `Invocation:` line, steps |
| `reference` | Explains: rationale, worked examples, incident history or lookup tables not needed to act (P6) |
| `adapter-config` | Is harness data or a capability declaration rather than an instruction |

Rejected synonyms: "category" or "type" for kind; "link" for edge (a link is one form of edge);
"issue" for finding; "receipt" for the inventory.

## Requirements

### Preserved identifiers (meaning kept, wording made precise)

- **REQ-01 Pinned inventory.** WHEN `extract` runs, THE extractor SHALL list every non-directory
  entry (regular file, symbolic link or other) of the primary and adapter sets found in the root's
  file system at that moment, with the fields of DM-2, and SHALL NOT take a file count, file kind
  or capability from any record, earlier report or harness name.
- **REQ-02 Owned proposals.** EACH finding of a proposal type (DM-7 → Finding types) SHALL name
  its source path and section and exactly one owner from `11`, `12`, `13`, `15`, `14`.
- **REQ-03 Separate measurements.** THE inventory, assessment and report SHALL state words,
  bytes, edge counts and load counts as separate fields, SHALL contain no token count and no
  monetary amount (DM-9 → `economics-claim`), and WHERE the auditor compares an installed copy,
  THE assessment SHALL record the source digest, the installed digest and the installed location
  in `~/`-relative form, with conclusions limited to that installation. A path or file name
  copied verbatim from a scanned file (for example the edge `raw` `rules/reference/12ktokens.md`)
  is not a token count, even where it matches the DM-9 token pattern; the verbatim-copy rule of
  REQ-25 covers it. *(Clarified 2026-11-18 by `/spec-sync`; Decisions → D-03.)*
- **REQ-04 Audit boundary.** THE audit delivery SHALL change no file outside the list of REQ-11,
  SHALL run neither `scripts/sync.sh`, an installer, a workflow nor a model, and SHALL record
  every change it proposes to spec 09 only as an amendment (DM-7).
- **REQ-05 Row completeness.** THE assessment SHALL contain exactly one `files` row per audited
  path of the inventory, including symbolic links and other non-regular entries, each with a
  non-empty `kinds` list.
- **REQ-06 Mixed kinds.** WHEN a row has more than one kind, and always for
  `rules/phase-atomic-execution.md` and `rules/phase-discovery.md`, THE row SHALL classify every
  section of that file (DM-5 → Sections) exactly once with a kind and a proposed home, and SHALL
  cite current `path:line` evidence.
- **REQ-07 References.** THE extractor SHALL resolve every edge by DM-4, distinguishing the
  statuses `ambiguous-stem`, `missing-target`, `missing-heading`, `missing-path`,
  `unknown-command`, `glob-empty` and the `md_suffix` flag, and SHALL label a repository-path
  mention with form `path`, never as an invocation; and EVERY defect edge SHALL appear in at
  least one finding.
- **REQ-08 Duplication.** EVERY duplicate cluster SHALL belong to exactly one duplicate group,
  and EACH group SHALL name its members, normative source, condition differences, disposition
  and owner; a group whose members contradict each other SHALL have disposition `contradiction`
  and a finding.
- **REQ-09 Migration map.** THE assessment SHALL hold exactly one map entry per audited path,
  and THE verifier SHALL reject a map in which a split does not cover every section of its source
  exactly once, a target path is shared without a merge reason on every sharing target, two
  installed names are equal under Unicode casefolding, a rule stem equals a workflow stem, or a
  top-level rule target lacks a kind prefix (DM-9 → map codes).
- **REQ-10 Amendments.** EACH amendment SHALL name one existing target in spec 09 (DM-7 →
  Amendment target forms) or a new requirement or criterion, the change type (`semantic`,
  `editorial` or `relocation`), the current and proposed text, the reason, the evidence, the
  affected acceptance criteria, its dependencies and whether it requires an ADR; EVERY map entry
  that deviates from its spec 09 default (DM-7 → Spec 09 defaults) SHALL cite an amendment.
- **REQ-11 Output files and permitted changes.** THE delivery SHALL create or change only:
  `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`, the three
  `docs/audits/<run_date>-rules-workflows-audit.*` files (DM-1, DM-7, DM-8), one index line in
  `docs/README.md`, one table row per new script in `scripts/README.md`, the commands note in
  `.ai/context/runbook.md`, the inventory sentence `.ai/memory/architecture.md:22-23`,
  `.ai/memory/state.md` and `.ai/memory/progress.md`, plus the records the pipeline itself
  writes for this task: `.ai/tasks/todo/task-*-rules-workflows-audit/**` and its archived copy
  under `.ai/tasks/completed/`, the 08 row of `.ai/specs/README.md`, this spec file
  (`/spec-sync` only), and, only when the pipeline archives this spec to
  `.ai/specs/completed/08-rules-workflows-audit.md`, the path cell of identity-ledger row
  `.ai/tasks/completed/task-01-git-source-of-truth/state.md:214` (the precedent of the archived
  rows above it).
- **REQ-12 Read coverage.** THE assessment SHALL hold exactly one coverage entry per audited path
  with status `read`, `unavailable`, `changed` or `not-a-file` (only for `symlink` and `other`
  entries) and the digest that was read; WHEN any entry is `unavailable` or `changed`, THE report
  passport SHALL state `read_coverage: partial` with the gap count and each gap SHALL have a
  `coverage-gap` finding.
- **REQ-13 Reproducibility.** WHEN `extract` runs twice on the same root bytes and git state,
  THE two outputs SHALL be byte-identical, and THE inventory SHALL record `source_revision`,
  `worktree`, `inventory_digest` and `method_version` (DM-1); the passport adds the run date,
  tool versions, scope, exclusions and installed-copy access (DM-8).
- **REQ-14 Closure states.** THE report SHALL distinguish audit complete, report accepted and
  defects fixed: THE delivery SHALL NOT claim audit complete unless `verify` exits 0 and the
  review line records `pass`, SHALL leave the acceptance line `Accepted: pending`, and MAY
  deliver open findings, each with `blocks_09` set by DM-7 → Blocking predicate and listed under
  `## Blockers for spec 09` when true.

### Added in this revision

- **REQ-15 Read-only offline extraction.** THE tool SHALL write only the file named by
  `extract --out` or, for `render --write`, the generated region of the named report, each by
  atomic replacement; SHALL NOT follow symbolic links, execute or import repository content, or
  open a network connection; and SHALL call only `git` read commands (Contracts → Git use).
- **REQ-16 Reader classes.** THE extractor SHALL scan the readers of DM-3 with their class, SHALL
  exclude every `docs/audits/*-rules-workflows-audit.md`, `.inventory.json` and
  `.assessment.json` and its own two files `scripts/audit-instructions.py` and
  `scripts/check-audit-instructions.py`, and SHALL record a reader that is not valid UTF-8 with `decoded: false` and
  no edges.
- **REQ-17 Reference grammar.** THE extractor SHALL produce edges exactly by DM-4 and DM-5,
  including the context, form, `load` flag, status and per-candidate heading status of each.
- **REQ-18 Legacy mentions.** THE extractor SHALL record every case-insensitive match of
  `windsurf`, `codeium` or `\bdevin\b` (spec 09 DM-17 → L pattern) in audited Markdown and JSON
  files, and THE assessment SHALL give each such mention exactly one role: `active-behavior`,
  `legacy-detection`, `historical` or `example`.
- **REQ-19 Loads and candidates.** THE extractor SHALL list repeated-load, full-output and
  harness-name candidates by DM-6, and THE assessment SHALL classify every load edge whose source
  is an audited file as `mandatory` or `conditional` (with the condition text) and SHALL give
  every candidate a disposition (`finding` with a finding id, `guarded` or `not-applicable` with
  a reason).
- **REQ-20 Spec 09 inputs.** THE assessment SHALL record, for spec 09: the spec 09 default of
  every map entry derived by DM-7 → Spec 09 defaults, the REQ-21 coverage verdict with exactly one
  mapping per statement unit (DM-5 → Statement units) of
  `rules/phase-discovery.md → ## Codebase Reading Rules` and `## Decision Protocol`, and THE
  report SHALL render the word counts of every section of every audited file.
- **REQ-21 Validator impact counts.** FOR every map entry whose decision is not `keep`, THE
  report SHALL render the number of edges that target the source, grouped as DM-8 → Validator and
  test impact lists, so that spec 09 can size its re-pointing and schema-2 amendment work.
- **REQ-22 Verification.** WHEN `verify` runs, THE verifier SHALL check the inventory, assessment
  and report by every rule of DM-9, print one diagnostic per violation in the form
  `<code> <location> <message>`, and exit 0 only when it prints none.
- **REQ-23 Generated region.** THE report SHALL contain exactly one generated region, and THE
  verifier SHALL require it to equal byte for byte what `render` produces from the same inventory
  and assessment.
- **REQ-24 Standalone suite.** THE suite `scripts/check-audit-instructions.py` SHALL be a
  standard-library `unittest` program run directly, SHALL NOT be called from
  `scripts/validate-contracts.sh` or `scripts/sync.sh`, SHALL build every fixture under a
  temporary directory, and SHALL contain at least one case per edge form, per status, per
  diagnostic code of DM-9 and per edge case listed with this requirement.
- **REQ-25 Public hygiene.** THE audit outputs SHALL contain no machine-specific home path
  (`/home/<name>/` or `/Users/<name>/`) and no occurrence of the former repository name, SHALL
  state every path of their own (entry paths, locations, evidence) in repository-relative or
  `~/`-relative form, and WHEN the delivery is complete, `bash scripts/validate-contracts.sh`
  SHALL finish with zero failures. Other absolute paths, such as system paths (`/usr/bin/sg`,
  `/tmp`), are allowed only inside text copied verbatim from a scanned file: the DM-6 text of
  audited files, after its home rewrite, and edge `raw` values (DM-4). The suite's fixtures may
  use placeholder absolute paths (`/home/someone/…`, `/opt/skills/SKILL.md`), because AC-27
  needs a location that does not start `~/`; no fixture names a real home directory.
  *(Narrowed 2026-11-18 by `/spec-sync` from "only repository-relative or `~/`-relative
  paths"; Decisions → D-03.)*
- **REQ-26 Index and knowledge.** THE delivery SHALL add the report to `docs/README.md` under
  ``## Audits (`audits/`)``, both scripts to the `scripts/README.md` table, the two commands to
  `.ai/context/runbook.md → ## Commands` notes, the updated script counts to
  `.ai/memory/architecture.md:22-23`, and a completed entry to `.ai/memory/state.md` and
  `.ai/memory/progress.md`.
- **REQ-27 Runtime guard.** IF the running Python is older than 3.11, THEN THE tool SHALL print
  `ERROR: Python 3.11 or newer is required` to standard error and exit 2 before reading anything;
  the module's first statements SHALL be its docstring, `from __future__ import annotations`,
  `import sys` and the guard, before any other import or definition, so that the guard runs on
  older interpreters that can parse the file.
- **REQ-28 Repetition review per workflow.** THE assessment SHALL record, for every audited
  workflow with at least one `Invocation:` line, the result of examining it for repeated reports,
  repeated checkpoint or status records and repeated review of unchanged inputs, as three lists of
  finding ids of types `report-repeat`, `checkpoint-repeat` and `review-repeat` (an empty list
  meaning examined, none found).
- **REQ-29 Owned fixes for references outside spec 09's grammar.** IF a finding owned by `09`
  names a defect edge that spec 09's executable-reference grammar does not cover (DM-4 →
  `in_spec09_grammar` false), THEN THE finding's `evidence` SHALL cite an amendment that gives
  spec 09 the obligation to fix it.

## Data Model

All JSON files are UTF-8, written with `json.dumps(value, ensure_ascii=False, indent=2)` plus
one trailing `\n`, keys in the order listed here, parsed with duplicate keys rejected. Paths are
repository-relative POSIX strings. Digests are lowercase hexadecimal SHA-256. Lists are sorted as
stated; "path order" means Python string order of the path.

### DM-1 Inventory (new) — `docs/audits/<run_date>-rules-workflows-audit.inventory.json`

| Key | Type | Content |
|---|---|---|
| `schema_version` | integer | `1` |
| `method_version` | string | `"08-extract-1"`; any change to DM-2–DM-6 behaviour changes it |
| `source_revision` | string or null | `git rev-parse --verify HEAD` of the root; null when git or the work tree is unavailable |
| `worktree` | object | `{"state": "clean" | "dirty" | "unknown", "paths": [...]}`; `paths` lists, in path order, every audited or reader path (after the DM-3 exclusions) that `git status --porcelain=v1 -z --untracked-files=all` reports; `state` is `dirty` exactly when `paths` is non-empty, otherwise `clean`; changes to excluded or unread files (the audit outputs, `VERSION`) do not count; `unknown` with `[]` when git is unavailable |
| `inventory_digest` | string | SHA-256 of the UTF-8 text formed by one line `<path>\t<set or class>\t<sha256 or ->\n` per entry of `files` and `readers` merged into one list sorted in path order |
| `files` | list | DM-2 entries, path order |
| `readers` | list | DM-3 entries, path order |
| `edges` | list | DM-4 entries, ordered by source path, line, column |
| `repeat_loads` | list | DM-6 `RL` entries |
| `full_output` | list | DM-6 `FO` entries |
| `harness_names` | list | DM-6 `HN` entries |
| `legacy_mentions` | list | DM-6 legacy entries |
| `duplicate_clusters` | list | DM-6 `DUP` entries |

### DM-2 File entry (audited set)

| Key | Type | Content |
|---|---|---|
| `path` | string | Repository-relative path |
| `set` | string | `primary` or `adapter` |
| `entry` | string | `file`, `symlink` (never followed) or `other` (from `os.lstat`) |
| `tracked` | boolean or null | Listed by `git ls-files -z`; null without git |
| `sha256`, `bytes`, `lines` | string, integer, integer or null | Of the raw bytes; `lines` = number of LF-separated lines (a final line without LF counts); null for non-files |
| `encoding` | string or null | `utf-8`, `invalid` (strict decode fails) or `control-character` (contains U+001C–U+001F); null for non-files |
| `words` | integer or null | Word count (Terminology); null unless `encoding` is `utf-8` |
| `front_matter` | object or null | For decodable `.md` files: `{"status": "present" | "absent" | "unclosed", "keys": [...], "trigger": str|null, "description": str|null, "continuation_lines": int}` (DM-5); null otherwise |
| `invocation_lines` | integer or null | Lines starting `Invocation: ` outside fences, for decodable `.md` files |
| `sections` | list | DM-5 sections of a decodable `.md` file, in line order; `[]` otherwise |

### DM-3 Readers and classes

A reader entry is `{"path", "class", "sha256", "lines", "decoded"}`. The extractor walks the root
with `os.walk(followlinks=False)`, takes regular files only, skips `.git/`, `logs/`, `output/`,
`__pycache__/` and `*.pyc`, skips audited files, applies the exclusions of REQ-16 (the three
audit output patterns and the tool's own two scripts, whose fixture literals would otherwise be
edges), and assigns the
first matching class:

| Class | Paths |
|---|---|
| `frozen` | `tests/fixtures/validator-runtime/**` |
| `active` | `CLAUDE.md`, `README.md`; `principles/**`, `templates/**` (dot directories included), `hooks/**`, `scripts/**`, `tests/**`; files directly in `docs/`; `.ai/principles/*.md`, `.ai/context/*.md`, `.ai/memory/architecture.md` |
| `planning` | `.ai/README.md`, `.ai/memory/state.md`, files directly in `.ai/specs/`, `.ai/tasks/todo/**` |
| `history` | `.ai/adr/**`, `.ai/specs/completed/**`, `.ai/tasks/completed/**`, `.ai/memory/progress.md`, `docs/**` below a subdirectory |

Any other file is not read (for example `VERSION`, `.gitignore`). Audited files are edge sources
of class `active`. The `active` class equals spec 09's scan set R (DM-17) plus `README.md`, minus
the paths R excludes that do not exist yet.

### DM-4 Edge, grammar and statuses

Edge entry: `{"source", "class", "line", "column", "context", "form", "raw", "load", "md_suffix", "in_spec09_grammar", "status", "targets"}`.
`line` is 1-based; `raw` is the matched text without enclosing backticks (for G1, the whole span
content); `column` is the 0-based code-point offset of the first character of `raw` in the line
with a trailing CR removed. `context` is `front-matter`, `fence`, `span` (inside a single-backtick span), `text`,
and, in `scripts/validate-contracts.sh` only, `check-description` (inside the first double-quoted
string after a line-initial `check `) or `comment` (first non-blank character `#`). `targets` is a
list of `{"path", "heading_status"}` in path order; `heading_status` is null unless the form is
`section-ref`.

**Node names.** Rule stems: `rules/<stem>.md` at the top level of `rules/`. Workflow stems:
`workflows/<stem>.md`. Audited paths: every DM-2 path.

**Span grammar G1** (Markdown sources, spans outside fences and front matter; first match wins):

1. `command` — a span not containing ` → ` that matches `^/([a-z0-9][a-z0-9-]*)(\.md)?( .*)?$`: a
   workflow stem → `resolved`; otherwise `unknown-command` (spec 09 DM-16 form 1). Spans
   containing ` → `, such as `` `/spec-run → ## Step 4 → 4.2` `` (`rules/orchestration.md:67`),
   go to form 2.
2. `section-ref` — the span contains ` → `; the head (text before the first ` → `), after removing
   one leading `/`, is `rule-<stem>`, a path `rules/<stem>.md` or `workflows/<stem>.md`, or
   `<stem>` with an optional `.md`. Candidates: the rule and workflow files with that stem (a
   `rule-` head or `rules/` path: the rule only; a `workflows/` path: the workflow only). With no
   candidate: a head that is a bare `[a-z0-9-]+` token followed by a `#`-marked component →
   `missing-target`; any other head is a document reference and yields no edge. Components after
   the head, per candidate, from the start of the file: a marked component `#{n} T` resolves when
   a heading line inside the current extent equals `#{n} T` after trailing whitespace is removed
   (`resolved`), else when one starts with `#{n} T — ` (`resolved-prefix`, accepted by spec 09
   DM-16), else `missing-heading` and resolution stops; the matched heading's extent becomes the
   current extent (DM-5 → Extent). An unmarked first component resolves against any heading of level 2 or deeper whose
   text equals `T` or starts with `T — `, `T (` or `T:` (`heading-unmarked`), else
   `missing-heading`; unmarked components after a resolved heading are sub-items and are not
   checked. A candidate's `heading_status` is its worst component (`missing-heading` worst, then
   `heading-unmarked`, `resolved-prefix`, `resolved`).
3. `rule-name` — `^rule-([a-z0-9-]+)$`, or `^([a-z0-9][a-z0-9-]*)$` with the span immediately
   followed by ` rule` or ` rules`: the rule stem exists → `resolved` (the word "rule"
   disambiguates a shared stem); otherwise `missing-target`.
4. `path` — `^(rules|workflows|harness|templates)/[A-Za-z0-9_./*<>-]+$`: containing `<` → no edge;
   containing `*` → form `glob`, matched against audited paths with `fnmatch` semantics where `*`
   does not cross `/`; matches → `resolved`, none → `glob-empty`; an audited path → `resolved`; an
   existing directory → no edge; a `templates/` path that is not audited → no edge; otherwise
   `missing-path`.
5. `bare-name` — `^([a-z0-9][a-z0-9-]*)$` equal to a rule or workflow stem → `resolved` for one
   candidate, `ambiguous-stem` for two.

`md_suffix` is true only for a G1 `command` whose name ends in `.md`, a G1
`section-ref` whose head is `<stem>.md` (not a `rules/` or `workflows/` path), and every G2
`md-name`; it is false for `path`, `glob`, `skill-name` and `bare-name`. A span no form matches is
scanned with G2.

**Edge status.** For forms with a single possible target the status is as stated per form. For
`section-ref`, `md-name` and `bare-name`: no candidate → `missing-target`; two candidates →
`ambiguous-stem` regardless of heading results (each candidate keeps its `heading_status`); one
candidate → `resolved` for `md-name` and `bare-name`, and that candidate's `heading_status` for
`section-ref`.

**Token grammar G2** (all other text of every source, including spans G1 did not match, fences
and front matter; applied form by form in this order, each match masking its characters from
later forms; a whole token is not preceded or followed by `[A-Za-z0-9_-]`):

1. `path`/`glob` — `(?<![A-Za-z0-9_./-])(rules|workflows|harness)/[A-Za-z0-9_*./-]*[A-Za-z0-9_*]`
   and the literal `templates/codex-global-AGENTS.md`, resolved as G1 form 4.
2. `md-name` — whole token `<stem>.md` for a rule or workflow stem: one candidate → `resolved`,
   two → `ambiguous-stem`; `md_suffix: true`.
3. `skill-name` — whole token `rule-<stem>` with `<stem>` matching `[a-z0-9]+(-[a-z0-9]+)*`: rule
   exists → `resolved`, else `missing-target`.
4. `command` — `/<stem>` for a workflow stem, not preceded by `[A-Za-z0-9_./-]` and not followed
   by `[A-Za-z0-9_/-]` → `resolved`; G2 never yields `unknown-command`.
5. `bare-name` — whole token equal to a rule or workflow stem that contains a hyphen: one
   candidate → `resolved`, two → `ambiguous-stem`. Stems without a hyphen are matched only by the
   other forms.

Non-Markdown sources use G2 only, with context `text` (or the two validator contexts).

**Defect predicate.** An edge is a defect edge when its class is `active`, its context is not
`fence`, its form is not `bare-name`, and either its status is not `resolved` or
`resolved-prefix`, or its `md_suffix` is true. `resolved-prefix` is counted but is not a defect,
because spec 09 DM-16 accepts it; `heading-unmarked` is a defect, because it does not follow the
cross-reference syntax of `.ai/principles/coding.md:45-51` and spec 09's grammar does not read
it.

**`in_spec09_grammar`** is true when the source is a top-level `rules/*.md`, `workflows/*.md` or
`harness/*/always-on.md` file, the context is `span`, the form is `command`, `section-ref` whose
head, after one optional leading `/`, matches `[a-z0-9][a-z0-9-]*` with an optional `.md` and
whose first component is marked `##` or `###` (spec 09 DM-16 form 2), `rule-name` or `path` (not `glob`: spec 09 DM-16 form 4 skips paths containing `*`), and the
status is not `heading-unmarked`; such defects are the
pre-existing defects spec 09 fixes (spec 09 DM-16, last paragraph). Otherwise false (REQ-29).

### DM-5 Text model

- **Lines** split on LF; a trailing CR is ignored for matching and counted in bytes.
- **Front matter**: present when line 1 is exactly `---`, ending at the next line that is exactly
  `---` (`unclosed` when there is none: then no front matter is removed from the body). Inside it,
  a line `^([a-z_]+):( .*)?$` is a key (repeated keys are listed again in `keys`); `trigger` and
  `description` record the value after `: ` with trailing whitespace removed (first occurrence);
  any other non-empty line is a continuation line.
- **Fences** (spec 11 → Section resolution, generalised to the indentation found in the sources):
  a line whose text after leading spaces starts with three or more backticks or tildes opens a
  fence; it closes at the next line whose text after leading spaces is a run of the same
  character at least as long, followed only by whitespace. An unclosed fence runs to the end of
  the file.
- **Headings**: ATX lines (`#` to `######` followed by a space) outside fences and front matter.
- **Extent** (spec 11 → Section resolution): a heading's extent runs from its line to the line
  before the next heading of the same or a higher level, or to the end of the file; the whole
  file is the extent before the first component.
- **Spans**: maximal single-backtick pairs on one line outside fences; double-backtick spans are
  treated as two empty spans.
- **Sections**: the file is partitioned at each level-2 heading outside fences. Entry
  `{"heading", "line", "words", "bytes"}`: `heading` is the heading line with trailing whitespace
  removed, or `(preamble)` for the lines before the first level-2 heading (omitted when there are
  none); words and bytes cover the section's lines, so their sums equal the file's. A `## ` line
  inside a fence (the template headings of `rules/workflow-reference.md:37-60`) is not a section
  and travels with its enclosing section; spec 09 DM-12 and REQ-46 also count such lines, so a
  split proposal states in its amendment or map `sections` where they go when that differs.
- **Statement units** (for REQ-20): inside a section, outside fences, excluding its heading line,
  a unit starts at a list-item line (`^\s*([-*+]|\d+[.)])\s`), at a table row other than the
  separator, at a fence opening line (the whole fenced block is one unit), or at the first
  non-blank line after a blank line or after the heading; following non-blank lines that start no
  unit belong to it. A unit is identified by its first line number.
- **Load lines** (spec 11 → Textual load command detection, extended to workflow targets): a line
  of an audited `.md` file outside fences and front matter whose text with spans removed matches,
  case-insensitively, `\b(load|loads|loaded|loading|read|reads|reading)\b`; every edge with
  context `span` on that line gets `load: true`.

### DM-6 Candidates, legacy mentions and duplicate clusters

- **Repeated loads `RL-NNN`.** Calls: `command` edges with status `resolved` and context `span` or
  `text`, whose source is a workflow with at least one `Invocation:` line (so the reference
  document `workflows/PIPELINE.md` is never a caller), whose target is another workflow, and whose
  clause (below) contains a case-insensitive match of
  `\b(run|runs|invoke|invokes|call|calls|execute|executes|delegate|delegates|spawn|spawns)\b`
  With spans replaced by spaces (positions kept), the clause is the text
  from just after the last of `.`, `;`, `:`, `,`, `—`, `→`, `(`, `)` that precedes the edge's
  column, up to that column. The edge is a call when its clause contains a call verb, no
  negation (`\b(not|never|no)\b` or `n't\b`) occurs in the clause before that verb, and no
  `**stop**` marker occurs earlier on the line (a quoted stop message names a prerequisite, not a
  call). So "Do not run `/phase-execution` automatically" (`workflows/pd-finalize.md:113`) and
  "**stop**: … run `/pd-analyze` first" (`workflows/pd-decompose.md:14`) are not calls, while
  "Run `/phase-discovery` in autonomous mode. Read-only resolution did not …"
  (`workflows/phase-pipeline.md:105`) and "… is not already complete → call
  `/phase-composite-validation`" (`workflows/pav-close.md:64`) are. For every
  distinct call pair (caller `W`, callee `C`) and every target `T` that both `W` and `C` load
  through load edges with exactly one target, emit `{"id", "caller", "callee", "target"}`. This
  is a repeat within one parent-child invocation, the reuse case of ADR-0014 Decision 1; no roots
  or transitive reach are computed, so cycles need no special handling. Order: caller, callee,
  target; ids from `RL-001`. A graph without calls yields no candidates.
- **Harness names `HN-NNN`.** A line of an audited `.md` file outside fences and front matter
  that matches case-insensitively `\b(claude code|claude|codex)\b`: `{"id", "source", "line",
  "text"}` (text as for `FO`); the auditor checks whether behaviour branches on a harness name
  instead of a capability (ADR-0009 Decision 2; previous REQ-04).
- **Full output `FO-NNN`.** A line of an audited `.md` file outside fences and front matter that
  matches, case-insensitively, `\b(full|entire|complete|whole|verbatim|raw|unabridged)\b` and also
  `\b(outputs?|logs?|diffs?|transcripts?|stdout|stderr)\b`: `{"id", "source", "line", "text"}`,
  `text` being the line with whitespace runs collapsed and cut to 160 code points.
- **Legacy mention**: `{"source", "line", "column", "term", "text"}` for each REQ-18 match in an
  audited file; `term` is the lowercased match, `text` as for `FO`.
- **Duplicate clusters `DUP-NNN`.** Units are taken from audited `.md` files with `utf-8`
  encoding, outside front matter and fences, skipping heading lines and table separator lines
  (`^\|[-:| ]+\|$`). A table row (a line starting with `|`) is one unit. Other non-blank lines
  are grouped into paragraphs (maximal runs of non-blank, non-table lines); each line loses a
  leading `>`, leading whitespace and a leading list marker (`[-*+] ` or `\d+[.)] `); the
  paragraph's lines are joined with one space, whitespace runs are collapsed, and the text is
  split after `.`, `!` or `?` followed by whitespace. Units with fewer than 8 words are dropped.
  Units whose text is equal in two or more places form a cluster
  `{"id", "sha256", "words", "text", "members": [{"path", "line_start", "line_end"}]}`, members
  in path then line order; clusters ordered by their first member; ids from `DUP-001`.
- **Home-directory prefixes in copied text.** In every text copied from an audited file — the
  `text` of `FO`, `HN` and legacy mentions and each line that enters a duplicate unit — each
  home-directory prefix `/home/<name>/` or `/Users/<name>/` (not preceded by a word character,
  `.`, `/`, `~` or `-`; `<name>` one path component without whitespace) is written as `~/`
  before whitespace is collapsed and the text is cut, and before units are joined, split,
  counted, compared and hashed (`scripts/audit-instructions.py:1206-1217`, `:1296-1310`).
  Candidate matching and `line`/`column` values use the original line. Other absolute paths are
  copied verbatim (REQ-25). `method_version` stays `08-extract-1`, because no output was produced
  under the rule before this amendment. *(Amended 2026-11-18 by `/spec-sync`; Decisions → D-01.)*

### DM-7 Assessment (new) — `docs/audits/<run_date>-rules-workflows-audit.assessment.json`

Written by the auditor. Keys, in order; an unknown or missing key is `assessment-invalid`:

| Key | Content |
|---|---|
| `schema_version` | `1` |
| `inventory_digest` | Equal to the inventory's |
| `run_date` | `YYYY-MM-DD`; equal to the date prefix of the three file names |
| `auditor`, `environment` | Role label; `{"python": "<python3 --version>", "git": "<git --version>"}` |
| `installed_access` | `not-verified` or `verified` |
| `files` | One per audited path: `{"path", "sha256", "kinds", "sections", "evidence", "repetition"}`; `sha256` null for non-files; `kinds` a non-empty, duplicate-free list of the eight kinds; `sections` null or a list of `{"heading", "kind", "proposed_home"}` covering every DM-5 section of the file once (`proposed_home` a repository path); `evidence` a non-empty list of `path:line` strings; `repetition` (REQ-28) `{"report": [ids], "checkpoint": [ids], "review": [ids]}` for every workflow with an `Invocation:` line, null for every other file |
| `coverage` | One per audited path: `{"path", "sha256", "status", "reader"}` (REQ-12); `reader` a role label matching `^[A-Za-z][A-Za-z0-9-]*$` |
| `loads` | One per load edge whose source is audited: `{"source", "line", "column", "mode", "condition"}`; `condition` non-empty when `mode` is `conditional`, else null |
| `candidates` | One per `RL`, `FO` and `HN` id: `{"id", "disposition", "finding", "reason"}`; `disposition` `finding`, `guarded` or `not-applicable`; `finding` required for `finding`, `reason` non-empty otherwise; an `RL` or `FO` finding has a proposal type, an `HN` finding type `naming` |
| `legacy` | One per legacy mention: `{"source", "line", "column", "role", "note"}` |
| `duplicate_groups` | `{"id": "DG-NNN", "clusters", "locations", "normative_source", "condition_differences", "disposition", "owner", "finding", "rationale"}`: `clusters` DUP ids; `locations` read-detected `{"path", "line_start", "line_end"}`; a group has at least two locations in total; `normative_source` `{"path", "section"}`; `disposition` `consolidate`, `intentional`, `condition-specific` or `contradiction`; `owner` `11` or `09` for `consolidate`, `owner` for `contradiction`, `none` otherwise; `finding` required for `consolidate` and `contradiction`; `rationale` non-empty |
| `map` | One per audited path: `{"source", "decision", "targets", "spec09_default", "spec09_optional", "amendment"}`; `targets` a list of `{"path", "sections", "merge_reason"}` (`sections` null or headings of the source; `merge_reason` null or non-empty); `spec09_default` null or a list of `{"path", "sections"}`; `spec09_optional` a list of paths (possibly empty); `amendment` null or an `AMD-08-NN` id |
| `req21` | `{"verdict": "covered" | "not-covered", "statements": [{"source": "rules/phase-discovery.md:<line>", "text", "covered_by"}]}`; exactly one statement per statement unit (DM-5) of the two sections, `source` naming the unit's first line; `covered_by` null or `path:line`; `covered` exactly when no `covered_by` is null |
| `findings` | DM-7 → Finding |
| `amendments` | DM-7 → Amendment |
| `installed` | List of `{"path", "location", "source_sha256", "installed_sha256"}`; empty when `installed_access` is `not-verified` |

**Decisions.** `keep`: one target equal to the source. `rename`: one target in the same directory
with another name. `move`: one target in another directory. `split`: two or more targets whose
`sections` lists together hold every section of the source exactly once; an optional overflow
target (`spec09_optional`, spec 09 REQ-19) carries `sections: null`, holds no whole section and
is left out of that cover. `merge`: one target
shared with another entry. Top-level `rules/*.md` targets need a stem prefix `bootstrap-`,
`contract-`, `protocol-` or `procedure-` (ADR-0009 Decision 3); `rules/reference/` targets (spec
11) are exempt. Installed names: top-level `rules/<stem>.md` → `rule-<stem>`, `workflows/<stem>.md`
→ `<stem>`; other paths are not deployed.

**Spec 09 defaults.** The auditor derives `spec09_default` from spec 09 as it stands at the
audited revision; the reviewer re-derives it by the same table:

| Source | `spec09_default` | `spec09_optional` |
|---|---|---|
| A `rules/` file named in spec 09 DM-10 | DM-10's targets in order; for split rules each target's `sections` from DM-12 (DM-12's catch-all "every other line … → `contract-state-files`" expanded to explicit headings) | The overflow rule DM-10 permits for that phase, if any |
| `rules/global-claude.md`, `templates/codex-global-AGENTS.md` | The DM-10 / REQ-55 target (`harness/claude/always-on.md`, `harness/codex/always-on.md`) | `[]` |
| `workflows/PIPELINE.md` | `docs/PIPELINE.md` (spec 09 REQ-23) | `[]` |
| A workflow whose stem is a DM-11 `Old` value | `workflows/<New>.md` | `[]` |
| A workflow named in DM-11's "Unchanged names" list | The same path | `[]` |
| A `harness/` file | The same path (spec 09 REQ-35 extends existing adapter files in place) | `[]` |
| Any other audited file | null | `[]` |

**Deviation** is computed, not written: an entry deviates when `spec09_default` is null, or when
the set of target paths is neither the default's set nor the default's set plus some members of
`spec09_optional`, or when a default target with non-null `sections` and the same-path target
list different section sets. Exception (spec 09 REQ-21): for `rules/phase-discovery.md`, replacing
`rules/protocol-discovery-conduct.md` by `rules/protocol-autonomous-decision.md` with the same
sections is not a deviation when `req21.verdict` is `covered`. Every deviating entry needs a
non-null `amendment`.

**Blocking predicate.** `blocks_09` is true exactly when an amendment cites the finding in its
`evidence`, or the finding's type is `contradiction`, or its type is `coverage-gap` and its source
is audited. Severity `blocker` is allowed only when `blocks_09` is true.

**Finding** `{"id", "type", "severity", "source", "section", "sha256", "lines", "observation", "consequence", "owner", "closure", "blocks_09", "status", "evidence", "edges"}`:
`id` `AUD-08-NNN` (unique); `source` a DM-2 or DM-3 path; `sha256` that entry's digest;
`section` a DM-5 section heading of an audited source, `(file)`, or free text for a reader;
`lines` 1-based line numbers within the source; `severity` `blocker`, `major` or `minor`;
`status` `open` or `historical-fixed` (an earlier recorded defect confirmed absent in the current
source; no new work is created); `evidence` a non-empty list of `path:line` or `path`; `edges` a
list of `{"source", "line", "column"}` naming defect edges. Types and their owners:

| Type | Allowed owners |
|---|---|
| `load-repeat`, `conditional-context`, `report-repeat`, `checkpoint-repeat`, `review-repeat`, `full-output` (proposal types) | `11`, `12`, `13`, `15`, `14` |
| `reference-defect`, `ambiguous-name`, `mixed-kind`, `naming`, `legacy-mention`, `duplicate` | `09`, `11`; a `09`-owned finding naming an edge with `in_spec09_grammar` false cites an amendment in `evidence` (REQ-29) |
| `contradiction` | `owner` |
| `coverage-gap`, `other` | `09`, `11`, `12`, `13`, `15`, `14`, `owner` |
| `accepted-observation` (a defect edge or candidate that is correct on reading, with the reason in `observation`) | `none`; `severity` `minor`, `blocks_09` false |

Default owners for proposals (A-07): `load-repeat` 12, `conditional-context` 11, `report-repeat`
11, `checkpoint-repeat` 13, `review-repeat` 15, `full-output` 14.

**Amendment** `{"id", "target", "change", "current", "proposed", "reason", "evidence", "affected", "depends_on", "requires_adr", "disposition"}`:
`id` `AMD-08-NN`; `target` in one of the **amendment target forms**: an identifier `REQ-NN`,
`AC-NN`, `DM-NN`, `A-NN` or `Q-NN` occurring as a whole token in spec 09; `Notes:<heading>` where
spec 09 has a line `### <heading>`; `Terminology:<term>` where spec 09 has a table row starting
`| <term> |`; or `new-REQ` / `new-AC`; `change` `semantic`, `editorial` or `relocation`; `current`
the exact current text (null for `new-*`); `proposed` non-empty; `evidence` non-empty, each item a
finding id or `path:line`; `affected` AC ids occurring in spec 09; `depends_on` amendment ids;
`requires_adr` true when the change alters a decision of ADR-0009 Decision 3 (kind prefixes, the
three-way `workflow-reference` split, frozen `##` headings) or merges sections; `disposition`
`proposed`.

### DM-8 Report (new) — `docs/audits/<run_date>-rules-workflows-audit.md`

Exact top-level layout, in this order: `# Rules and workflows audit — <run_date>`; `## Summary`
(hand-written); `## Method` (hand-written: commands run, deviations from the plan, time taken);
one line `<!-- audit:generated:begin -->`; the generated region; one line
`<!-- audit:generated:end -->`; `## Blockers for spec 09` (hand-written; names every finding with
`blocks_09: true` and no other finding, or is exactly `None.` when no finding blocks; amendment
ids and other text beside the listed ids are allowed); `## Independent review` with exactly one line
`Reviewed: pending` or `Reviewed: <role> <YYYY-MM-DD> pass|fail <40-hex commit>` (`<role>` matches
`^[A-Za-z][A-Za-z0-9-]*$`, the date is a valid calendar date, and the commit must exist:
`git -C <root> cat-file -e <sha>^{commit}`); `## Acceptance` with exactly one line
`Accepted: pending` or `Accepted: owner <YYYY-MM-DD>`. `verify` is guaranteed to exit 0 in the
delivery repository at the delivery commit; on a later tree or a clone without the reviewed
commit (for example after a squash merge) it may print `review-commit-unknown` or
`inventory-stale`, which does not reopen the audit (A-28).

The generated region holds, in order, `###` subsections with these fixed column sets (rows in the
order stated; cell text with `|` escaped and line breaks replaced by spaces; formatting otherwise
the renderer's own and deterministic):

| Subsection | Columns and rows |
|---|---|
| Passport | Bullet lines `source_revision`, `worktree`, `inventory_digest`, `method_version`, `scope` (sets, reader classes, exclusions), `installed_access`, `read_coverage` (`complete` or `partial (<n> gaps)`), `findings` (`<n> total, <m> open, <b> blocking spec 09`), `run_date`, `environment` |
| Inventory | Path, Set, Entry, Tracked, Words, Bytes, Kinds, Coverage, Decision, Findings — audited paths in path order |
| Sections | Path, Section, Line, Words, Bytes, Kind, Proposed home — every section of every audited file |
| References | A count table class × status; then every defect edge: Source:line:column, Raw, Form, Context, Status, Candidates, Findings |
| Loads | Source:line, Targets, Mode, Condition |
| Repeated loads | ID, Caller, Callee, Target, Disposition, Finding |
| Full-output candidates | ID, Source:line, Text, Disposition, Finding |
| Harness-name candidates | ID, Source:line, Text, Disposition, Finding |
| Repetition review | Workflow, Report findings, Checkpoint findings, Review findings (`none` for an empty list) |
| Legacy mentions | Source:line, Term, Role, Note |
| Duplicates | Group, Clusters, Locations, Normative source, Condition differences, Disposition, Owner, Finding |
| Migration map | Source, Decision, Targets (with sections), Spec 09 default, Deviation, Amendment |
| Validator and test impact | Per non-`keep` map entry: Source, Decision, and edge counts for `scripts/validate-contracts.sh` by context (`text`, `check-description`, `comment`), other `tests/**`, `frozen`, `hooks/**`, other `active` |
| Spec 09 inputs | Map entries with a null default; the REQ-21 verdict and statement table |
| Findings | ID, Type, Severity, Source, Section, Owner, Blocks 09, Status, Observation, Closure |
| Amendments to spec 09 | ID, Target, Change, Proposed, Reason, Evidence, Affected, Depends on, Requires ADR, Disposition |
| Read coverage | Path, Status, SHA-256, Reader |
| Installed comparison | Path, Location, Source SHA-256, Installed SHA-256, Match — or the line `Not verified.` |

### DM-9 Verifier rules and diagnostic codes

Location is `<path>:<line>` (`0` for a whole file) or `<json file>#<id or index>`.

| Code | Raised when |
|---|---|
| `inventory-missing`, `assessment-missing`, `report-missing` | The file derived from `--report` is absent |
| `inventory-invalid`, `assessment-invalid` | Not parseable, schema violated, unknown or missing key, enum value outside its set, or duplicate id |
| `report-name-date` | A file name date differs from `run_date` |
| `inventory-stale` | An audited path is added, removed or has another digest in the root than in the inventory; with `--strict`, any byte difference between a fresh extraction and the inventory |
| `worktree-dirty` | `worktree.state` is not `clean` |
| `digest-mismatch` | `inventory_digest` differs between the two JSON files |
| `row-missing`, `row-extra`, `row-duplicate` | `files`, `coverage` or `map` does not hold exactly one entry per audited path |
| `assessment-stale` | An entry's `sha256` differs from the inventory's |
| `sections-incomplete` | A required `sections` list (REQ-06) is null or does not cover each section once |
| `load-unclassified` | A load edge with an audited source lacks a `loads` entry, or an entry names no load edge |
| `candidate-undisposed` | An `RL`/`FO`/`HN` id lacks a `candidates` entry, a required finding or reason, or names a finding of the wrong type |
| `repetition-invalid` | A workflow with an `Invocation:` line has null `repetition`, another file has a non-null one, or a listed id is not a finding of the matching type |
| `legacy-role-missing` | A legacy mention lacks a `legacy` entry |
| `duplicate-ungrouped`, `duplicate-multigrouped`, `group-invalid` | A cluster in no group, in two groups, or a group breaking DM-7 rules |
| `defect-unrecorded` | A defect edge is named in no finding's `edges` |
| `finding-invalid` | A finding breaks DM-7: owner not allowed for its type, `blocks_09` unequal to the blocking predicate, severity `blocker` with `blocks_09` false, bad `status`, `lines` or `section`, or a `09`-owned finding naming an edge with `in_spec09_grammar` false without an amendment id in `evidence` (REQ-29) |
| `finding-stale` | A finding's `sha256` differs from its source's |
| `evidence-unresolved` | A well-formed evidence item of a `files` row, finding or amendment does not resolve against the inventory: a `path:line`, `path:start-end` or bare path names no `files` or `readers` path, the entry has no line count, the range is reversed, or a line lies outside `1..lines` (a number of more than nine significant digits counts as outside); a finding id cited as finding evidence names no path. Line counts come from the inventory, so a later tree adds none. *(Added 2026-11-18 by `/spec-sync`; Decisions → D-04.)* |
| `reference-unknown` | A finding, candidate, group or map entry cites an id that does not exist |
| `map-invalid` | A decision's target shape is wrong (DM-7 → Decisions) |
| `split-sections-incomplete` | A split does not cover every section of its source exactly once |
| `map-collision` | A target path is shared and a sharing target has no `merge_reason` |
| `installed-name-collision` | Two final installed names are equal under `str.casefold` |
| `stem-overlap` | A final top-level rule stem equals a final workflow stem |
| `kind-prefix-invalid` | A top-level rule target lacks a kind prefix |
| `deviation-unamended` | An entry deviates (DM-7 → Deviation) and its `amendment` is null or names no existing amendment |
| `spec09-unavailable` | No single file matches `.ai/specs/09-*.md` under the root |
| `amendment-invalid`, `amendment-target-unknown` | An amendment breaks DM-7, or its `target` does not satisfy DM-7 → Amendment target forms against spec 09, or an `affected` id is not a whole token of spec 09 |
| `req21-invalid` | The statements are not exactly one per statement unit of `## Codebase Reading Rules` and `## Decision Protocol` of `rules/phase-discovery.md` (missing, extra, repeated or outside them), or the verdict contradicts the `covered_by` values |
| `coverage-inconsistent` | An `unavailable` or `changed` entry has no `coverage-gap` finding, `not-a-file` is used for a regular file, or a non-file has another status |
| `report-layout` | DM-8 headings, markers or the review/acceptance line are missing, repeated or malformed; or `## Blockers for spec 09` is not exactly `None.` when no finding blocks, or holds a `None.` line beside blocking findings |
| `review-commit-unknown` | The commit of a `Reviewed:` line does not exist in the root's repository |
| `report-generated-mismatch` | The generated region differs from `render` output |
| `blocker-unlisted` | A `blocks_09: true` finding id does not occur in `## Blockers for spec 09` |
| `blocker-extra` | A whole finding id under `## Blockers for spec 09` names no finding, or a finding whose `blocks_09` is false; reported once per id per line *(added 2026-11-18 by `/spec-sync`; Decisions → D-04)* |
| `economics-claim` | The report or any assessment string matches `(?i)\b\d[\d,.]*\s*k?\s*tokens?\b`, `[$€£]\s?\d` or `\b(USD|EUR)\b` |
| `installed-invalid` | `installed` breaks REQ-03 (non-empty with `not-verified`, a location not starting `~/`, or a `source_sha256` unequal to the inventory) |

## Contracts & Interfaces

### `scripts/audit-instructions.py`

`python3 -I scripts/audit-instructions.py <subcommand> [options]`; standard library only;
`#!/usr/bin/env python3`; a header docstring stating purpose, CLI, exit codes and that it is
read-only; type annotations on every function (`principle-python-standards → ## Type Hints — Mandatory`).

| Subcommand | Options | Output | Exit |
|---|---|---|---|
| `extract` | `--root DIR` (default: parent of `scripts/`), `--out FILE` (required) | DM-1 to `FILE`, written to a temporary file in the same directory and moved into place | 0 written; 2 `root-invalid` (no `rules/` or `workflows/` directory), unwritable `--out`, runtime guard |
| `verify` | `--root DIR`, `--report FILE` (required), `--strict` | Diagnostics on standard output, one per line, ordered by code then location | 0 none; 1 any diagnostic; 2 usage error, unreadable root, runtime guard |
| `render` | `--root DIR`, `--report FILE` (required), `--write` | The generated region including both marker lines on standard output, or with `--write` that region replaced in `FILE` atomically | 0 rendered; 1 the inputs fail a schema rule (diagnostics printed); 2 usage error, markers missing or repeated (`--write`), runtime guard |

The inventory and assessment paths are derived from `--report` by replacing `.md` with
`.inventory.json` and `.assessment.json`. Usage errors print one `ERROR: …` line to standard error.

**Git use.** Only `git -C <root> rev-parse --verify HEAD`, `git -C <root> ls-files -z`,
`git -C <root> status --porcelain=v1 -z --untracked-files=all` and, in `verify`,
`git -C <root> cat-file -e <sha>^{commit}`, run with `LC_ALL=C`,
`GIT_OPTIONAL_LOCKS=0` and no pager; a failing or missing git yields the null/`unknown` values of
DM-1 and DM-2, never an error.

### `scripts/check-audit-instructions.py`

`python3 -I scripts/check-audit-instructions.py`: a `unittest` program; exit 0 when every case
passes, 1 otherwise. Fixture roots are built under `tempfile.TemporaryDirectory()` with minimal
`rules/`, `workflows/`, `harness/`, reader files and, where needed, an initialised git
repository with `HOME` and `XDG_CONFIG_HOME` set to temporary paths for the git calls. Fixtures
use synthetic stems (for example `alpha-flow`, `beta-step`), never the repository's names, and
may use placeholder absolute paths, never a real home directory (REQ-25).

## Non-Functional Requirements

| Attribute | Target and standard | Verification |
|---|---|---|
| Determinism | Two `extract` runs on unchanged bytes produce byte-identical files (REQ-13) | AC-12; AC-03 with `--strict` |
| Read-only | Only the `--out` file, or the report region under `--write`, changes | AC-11 (tree digest before and after) |
| Offline | No network, model or paid run; only the git read commands of Contracts | AC-11; source inspection by the reviewer |
| Dependencies | Python 3.11+ standard library and git; no package installation | AC-26 |
| Runtime | No target is set (A-12); the measured `extract` and `verify` times are recorded under `## Method` | Report review |
| Public hygiene | Zero identity-ledger or hygiene failures | AC-22 |
| Security | Symbolic links are recorded, never followed or read through; repository content is never executed or imported | AC-13 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | Requirement |
|---|---|---|
| A new file appears under `rules/reference/` or any nested directory | Listed with its path; needs assessment, coverage and map rows | REQ-01, REQ-05 |
| Symbolic link or other entry under an audited directory | Row with `entry` `symlink`/`other`, null digests; not followed; still assessed and mapped; coverage `not-a-file` | REQ-05, REQ-12, REQ-15 |
| Directory under an audited directory | Not an entry; its files are listed | REQ-01 |
| A reference document names every command (`workflows/PIPELINE.md`) | It has no `Invocation:` line, so its edges are never calls | REQ-19 |
| Workflows call each other in a cycle | Each call pair is evaluated on its own; a cycle yields at most one candidate per pair and target | REQ-19 |
| A line forbids running a command ("Do not run `/x`") or names it in a stop message | Not a call (clause negation and stop-marker rules) | REQ-19 |
| A negation elsewhere on a calling line ("If no X remains, run `/x`") | Still a call: negation counts only in the verb's clause before the verb | REQ-19 |
| A load repeated deeper than one parent-child step in one session | Not a candidate; the auditor records it as a `load-repeat` finding found by reading | REQ-19 |
| Mentions of a command without a call verb ("see `/x`") | Not a call | REQ-19 |
| Slash-prefixed section reference (`` `/spec-run → ## Step 4 → 4.2` ``) | Form `section-ref`, never `command` | REQ-17 |
| The tool's or suite's own fixture literals | Not scanned (REQ-16 exclusion) | REQ-16 |
| An interpreter that cannot parse the file's syntax | Fails with a syntax error before the guard; accepted limit | REQ-27 |
| Audited file not valid UTF-8, or containing U+001C–U+001F | Row kept with `encoding` set, `words` null, no sections or edges; coverage `unavailable` with a `coverage-gap` finding | REQ-12 |
| Empty audited file | `words` 0, no sections; still assessed | REQ-05 |
| Front matter without closing `---` | `status: unclosed`; whole file treated as body | REQ-17 |
| Unclosed fence | Runs to end of file; its references are `fence` context | REQ-17 |
| CRLF line endings | CR ignored for matching, counted in bytes | REQ-13 |
| UTF-8 byte-order mark | Not stripped; front matter then reads `absent` | REQ-17 |
| Stem shared by a rule and a workflow | `ambiguous-stem` with both candidates and their heading statuses, unless the form is `rule-name`, a `rule-` head or a directory path | REQ-07 |
| Section reference to a missing heading (control example) | `missing-heading` defect edge | REQ-07 |
| Unmarked heading in a section reference | `heading-unmarked` defect edge, or `missing-heading` | REQ-07 |
| Glob path matching nothing | `glob-empty` defect edge in `active` readers | REQ-07 |
| Reference in a planning or history reader to a missing name | Edge recorded, never a defect | REQ-16 |
| Reference inside a fenced example | `fence` context; never a defect | REQ-07 |
| Defect edge that is correct on reading (for example a harness built-in command) | Named by an `accepted-observation` finding | REQ-07 |
| Reader not valid UTF-8 (for example `.gz` fixtures) | `decoded: false`, no edges | REQ-16 |
| A source file changes after extraction | `verify` reports `inventory-stale` and every `assessment-stale` entry; the auditor re-extracts and re-reads the changed files | REQ-13 |
| Extraction on a dirty work tree | Allowed for drafts; `verify` reports `worktree-dirty`, so delivery needs a clean extraction | REQ-13 |
| Git unavailable or the root is not a work tree | `source_revision` null, `worktree` `unknown`, `tracked` null; `verify` reports `worktree-dirty` | REQ-13 |
| Earlier audit outputs under `docs/audits/` | Excluded from readers by name pattern | REQ-16 |
| Historical defect already fixed (the naming review's `phase-execution.md` example) | Finding with `status: historical-fixed` and current evidence; no new task | REQ-14 |
| Two equal sentences valid under different conditions | Group disposition `condition-specific` with the conditions; never mechanically removed | REQ-08 |
| Two fragments contradict each other | Group `contradiction`, owner `owner`, finding | REQ-08 |
| A section mixes a rule and its example | The section row records the boundary; moving the example to reference requires `evidence` that the rule stays reachable before the action | REQ-06 |
| A size target of another spec conflicts with obligatory content | Finding recording the failed target and an addressed amendment or proposal; nothing is proposed for deletion | REQ-02, REQ-10 |
| Different skill names on different harnesses | Classified from the capability records and deployment code, never by harness name | REQ-01 |
| Installed copy differs from its source | Both digests recorded under `installed`; conclusion limited to that installation | REQ-03 |
| No access to installed copies | `installed_access: not-verified`, empty `installed`, passport says so | REQ-03 |
| Spec 09 file absent or ambiguous | `spec09-unavailable`; amendments cannot pass | REQ-10 |
| Spec 09 renumbers an identifier after the audit | The amendment target no longer exists; `verify` on a later tree fails `amendment-target-unknown`; the audit stays valid at its own revision | REQ-10 |
| Large volume for one reader | Parallel readers are allowed; `coverage.reader` names each; exactly one entry per path; the assessment has one writer | REQ-12 |
| Concurrent writers of the assessment | Not supported: one writer (P4) | REQ-11 |
| Python older than 3.11 | Exit 2 with the guard message | REQ-27 |
| `render --write` on a report without markers | Exit 2, file unchanged | REQ-23 |
| Authorization | Not applicable: local read-only tool on a single-user checkout | — |

## Acceptance Criteria

Fixture criteria (AC-11 onward, and the fixture parts of AC-01–AC-10) are cases of
`scripts/check-audit-instructions.py`; delivery criteria run on the delivered repository.

- **AC-01** (REQ-01, REQ-02, REQ-05) — Given a fixture root with `rules/a-b.md`,
  `rules/reference/c.md`, `workflows/d-e.md` and `harness/x/y.json`, when `extract` runs, then
  `files` holds exactly those four paths; and given an assessment with a proposal finding whose
  owner is `09`, when `verify` runs, then it prints `finding-invalid`; and given the delivered
  report, when `verify --root . --report <report>` runs at the delivery commit, then it exits 0
  with empty output.
- **AC-02** (REQ-03, REQ-04) — Given an assessment string `saves 3,000 tokens` or `$5`, when
  `verify` runs, then it prints `economics-claim`; and given the delivery's last commit `<tip>`,
  when `git diff --name-only "$(git merge-base main <tip>)" <tip>` runs, then every listed path is
  in the REQ-11 list. *(Delivery 2026-11-18: the delivery stack is built on
  `feat/multi-repository-spec-run`, draft PR #104 with tip `488edb1`, so that the audit covers its
  rule and workflow changes; by the owner's decision D-02 the list was computed with base
  `488edb1` in place of `merge-base main`, and every listed path is in the REQ-11 list. The
  criterion's `merge-base main` form applies unchanged once PR #104 is in `main`.)*
- **AC-03** (REQ-05, REQ-12, REQ-13) — Given a checkout of the inventory's `source_revision` in
  a temporary work tree, when `extract` writes a fresh inventory, then it equals the delivered
  inventory byte for byte; and the delivered assessment has one `coverage` entry per audited path
  whose digest equals the inventory's.
- **AC-04** (REQ-06) — Given a fixture rule with two kinds and three sections, when `verify` runs
  with `sections` covering two of them, then it prints `sections-incomplete`; and in the delivered
  assessment the rows of `rules/phase-atomic-execution.md` and `rules/phase-discovery.md` have
  `sections` covering every section.
- **AC-05** (REQ-07) — Given the control example `` `alpha-flow → ## Missing` `` in a fixture
  workflow where `rules/alpha-flow.md` has no such heading, when `extract` runs, then the edge has
  status `missing-heading`; and when `verify` runs with no finding naming it, then it prints
  `defect-unrecorded`.
- **AC-06** (REQ-08) — Given two fixture rules sharing a sentence of eight or more words, when
  `extract` runs, then one `DUP-001` cluster lists both; and when the assessment groups it in no
  group, in two groups, or as `contradiction` without a finding, then `verify` prints
  `duplicate-ungrouped`, `duplicate-multigrouped` or `group-invalid` respectively.
- **AC-07** (REQ-09) — Given fixture maps that (a) split a file omitting one section, (b) share a
  target without `merge_reason`, (c) produce `rule-A-b` and `rule-a-b`, (d) give a rule and a
  workflow the same final stem, (e) target `rules/plain.md`, when `verify` runs, then it prints
  `split-sections-incomplete`, `map-collision`, `installed-name-collision`, `stem-overlap` and
  `kind-prefix-invalid` respectively.
- **AC-08** (REQ-10) — Given a fixture spec 09 file containing `REQ-21`, `AC-05` and a line
  `### Ownership`, when an amendment targets `REQ-99` or `Notes:Missing`, lacks evidence, or a map
  entry's targets differ from its `spec09_default` (or the default is null) with `amendment: null`,
  then `verify` prints `amendment-target-unknown`, `amendment-target-unknown`,
  `amendment-invalid` and `deviation-unamended` respectively; and an entry whose targets equal the
  default plus one `spec09_optional` path prints nothing.
- **AC-09** (REQ-11, REQ-26) — Given the delivery, then the three output files exist under
  `docs/audits/` with the same `run_date` prefix, the section ``## Audits (`audits/`)`` of
  `docs/README.md` links the report, `scripts/README.md` has one row per new script, and the
  inventory sentence of `.ai/memory/architecture.md` (`:22-23` before the change) states the
  counts `ls scripts/*.sh | wc -l` and `ls scripts/*.py | wc -l` give at the delivery commit.
- **AC-10** (REQ-14) — Given the delivered report, then `## Independent review` holds
  `Reviewed: <role> <date> pass <sha>`, `## Acceptance` holds `Accepted: pending`, and every
  finding with `blocks_09: true` is named under `## Blockers for spec 09`; and given a fixture
  report missing one such id, `verify` prints `blocker-unlisted`; given one listing a finding that
  does not block, `blocker-extra`. *(Extended 2026-11-18 by `/spec-sync`; Decisions → D-04.)*
- **AC-11** (REQ-15) — Given a fixture root and the SHA-256 of every file in it, when `extract`
  and `verify` run, then only the `--out` file is new or changed; and when `render --write` runs,
  then the report differs only between the two marker lines.
- **AC-12** (REQ-13) — Given a fixture root, when `extract` runs twice to two files, then they are
  byte-identical; and `inventory_digest` equals the SHA-256 of the DM-1 line text computed by the
  case independently.
- **AC-13** (REQ-15, REQ-01) — Given `rules/link.md` as a symbolic link to a file outside the root
  and `workflows/sub` as a symbolic link to a directory, when `extract` runs, then both are rows
  with `entry: symlink` and null digests, and no file behind them contributes edges.
- **AC-14** (REQ-16) — Given readers in each class, a non-UTF-8 reader, and a file
  `docs/audits/2020-01-01-rules-workflows-audit.md` naming an audited file, when `extract` runs,
  then each reader has the DM-3 class, the non-UTF-8 reader has `decoded: false`, and the excluded
  file appears in neither `readers` nor `edges`; and fixture files `scripts/audit-instructions.py`
  and `scripts/check-audit-instructions.py` containing `rules/zz-missing.md` produce no reader
  entry and no edge.
- **AC-15** (REQ-17) — Given fixture spans for every G1 form and text for every G2 form, when
  `extract` runs, then each edge has the form, context, status, `md_suffix` and targets DM-4
  defines, including `ambiguous-stem` for a shared stem, `resolved` for the same stem with
  ` rule`, `resolved-prefix` (not a defect), `heading-unmarked` (a defect), `unknown-command`,
  `missing-target`, `missing-path`, `glob-empty`, `section-ref` (not `command`) for
  `` `/w-one → ## Step 1` ``, `md_suffix: false` for `` `rules/r-one.md` `` and `true` for
  `` `w-one.md → ## Step 1` ``, `in_spec09_grammar` true for a span in `rules/r-one.md` and false
  for the same text in `docs/G.md`, no edge for `` `state.md → ## X` ``, and `check-description`
  and `comment` contexts in a fixture `scripts/validate-contracts.sh`.
- **AC-16** (REQ-18) — Given a fixture rule containing `Windsurf`, `.devin/` and `devinly`, when
  `extract` runs, then exactly two legacy mentions are recorded; and when one lacks a `legacy`
  entry, `verify` prints `legacy-role-missing`.
- **AC-17** (REQ-19) — Given fixture workflows with `Invocation:` lines, `w-root` whose line "Run
  `/w-child`." calls `w-child`, both loading `` the `r-one` rule ``, plus `workflows/HUB.md`
  without an `Invocation:` line that runs both commands, and `w-a` and `w-b` that run each other
  and both load `r-one`, when `extract` runs, then the candidates are exactly `RL-001`
  (`w-a` → `w-b`), `RL-002` (`w-b` → `w-a`) and `RL-003` (`w-root` → `w-child`), each with target
  `rules/r-one.md`; `HUB.md` is never a caller; lines "see `/w-child`", "Do not run
  `/w-child`" and "**stop**: run `/w-child` first" in `w-root` add no call, while "If no file
  remains, run `/w-child`." and "Run `/w-child`. It does not ask." are calls; a line "paste the full test output" yields `FO-001`, and a line naming "Codex"
  yields `HN-001`; and when a load edge has no `loads` entry or a candidate has no disposition,
  `verify` prints `load-unclassified` or `candidate-undisposed`.
- **AC-18** (REQ-20) — Given a fixture `rules/phase-discovery.md` whose two sections hold three
  statement units, when `req21` lists two of them, lists a line outside them, or has verdict
  `covered` with a null `covered_by`, then `verify` prints `req21-invalid`; and in the delivered
  report the Spec 09 inputs subsection lists every map entry with a null default and the REQ-21
  verdict.
- **AC-19** (REQ-21) — Given a fixture map renaming `rules/a-b.md` and readers naming it once in a
  `check "…"` description, once in a validator expression, once in `tests/t.py` and once under
  `tests/fixtures/validator-runtime/`, when `render` runs, then the Validator and test impact row
  shows 1 in each of those four columns.
- **AC-20** (REQ-22) — For every code of DM-9, a fixture case produces that code, and a fully valid
  fixture produces none and exit 0.
- **AC-21** (REQ-23) — Given a valid fixture report, when one character inside the generated region
  changes, then `verify` prints `report-generated-mismatch`; when a marker is duplicated, it prints
  `report-layout`.
- **AC-22** (REQ-25) — Given the delivered tree, when `bash scripts/validate-contracts.sh` runs
  (with `MISE_PYTHON_VERSION` set where the runbook says so), then it reports zero failures, and
  `grep -rn '/home/\|/Users/' docs/audits/*-rules-workflows-audit.*` prints nothing.
- **AC-23** (REQ-24) — Given the repository, when `python3 -I scripts/check-audit-instructions.py`
  runs, then it exits 0; and `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh`
  prints nothing.
- **AC-24** (REQ-26) — Given the delivery, then `.ai/context/runbook.md → ## Commands` names both
  commands, and `.ai/memory/state.md` and `.ai/memory/progress.md` each hold an entry for this audit
  linking the report.
- **AC-25** (REQ-12) — Given a fixture coverage entry `unavailable` without a `coverage-gap`
  finding, when `verify` runs, then it prints `coverage-inconsistent`; with the finding, the
  rendered passport says `read_coverage: partial (1 gaps)`.
- **AC-26** (REQ-27) — Given the tool run under an interpreter whose `sys.version_info` is patched
  below 3.11 by the case, then it prints the guard message and exits 2; the tool's imports are
  standard-library modules only (checked against `sys.stdlib_module_names`); and
  `ast.parse` of the tool's source shows, after the docstring, exactly `from __future__ import
  annotations`, `import sys` and an `if` statement comparing `sys.version_info` with `(3, 11)` as
  the first three statements.
- **AC-27** (REQ-03) — Given `installed_access: not-verified` with a non-empty `installed` list, or
  a location not starting `~/`, when `verify` runs, then it prints `installed-invalid`.
- **AC-28** (REQ-28) — Given a fixture workflow with an `Invocation:` line and `repetition: null`,
  or a `repetition.report` id naming a finding of type `full-output`, when `verify` runs, then it
  prints `repetition-invalid`; and the delivered assessment has a non-null `repetition` exactly for
  the audited workflows whose inventory `invocation_lines` is greater than 0.
- **AC-29** (REQ-29, REQ-14) — Given a `09`-owned `reference-defect` finding naming a
  `missing-path` edge from an `active` reader (so `in_spec09_grammar` is false) with no amendment
  id in `evidence`, when `verify` runs, then it prints `finding-invalid`; and given a finding cited
  by an amendment but with `blocks_09: false`, or a `minor` finding with `blocks_09: true` that no
  amendment cites and whose type is not `contradiction` or `coverage-gap`, it prints
  `finding-invalid`.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-13 |
| REQ-02 | AC-01 |
| REQ-03 | AC-02, AC-27 |
| REQ-04 | AC-02 |
| REQ-05 | AC-01, AC-03 |
| REQ-06 | AC-04 |
| REQ-07 | AC-05 |
| REQ-08 | AC-06 |
| REQ-09 | AC-07 |
| REQ-10 | AC-08 |
| REQ-11 | AC-09 |
| REQ-12 | AC-03, AC-25 |
| REQ-13 | AC-03, AC-12 |
| REQ-14 | AC-10, AC-29 |
| REQ-15 | AC-11, AC-13 |
| REQ-16 | AC-14 |
| REQ-17 | AC-15 |
| REQ-18 | AC-16 |
| REQ-19 | AC-17 |
| REQ-20 | AC-18 |
| REQ-21 | AC-19 |
| REQ-22 | AC-20 |
| REQ-23 | AC-21 |
| REQ-24 | AC-23 |
| REQ-25 | AC-22 |
| REQ-26 | AC-09, AC-24 |
| REQ-27 | AC-26 |
| REQ-28 | AC-28 |
| REQ-29 | AC-29 |

Every AC names at least one REQ above; no AC is unmapped.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Heuristic forms (bare names, full-output words, sentence split) produce noise | Auditor time; false defects | High | Fixed method version; `accepted-observation` findings; candidates need only a disposition |
| Verbatim detection misses reworded repetition | Semantic duplicates unreported | Medium | Groups take read-detected `locations`; the reviewer checks them |
| Spec 09 changes its identifiers or maps after the audit | Amendments point at moved text | Medium | Amendments cite identifiers and exact current text; `verify` re-checks targets at the audited revision |
| Readers evolve after extraction (knowledge files, index) | `--strict` fails on later commits | High | `--strict` is run on a checkout of `source_revision` (AC-03); plain `verify` checks only audited digests |
| The full validator takes 34–52 minutes (`.ai/context/runbook.md` notes) | Slow final gate | High | Run once at the end; standalone suite for iteration |
| Assessment volume (60+ rows, every load edge, every cluster) | Long reading work | High | Discovery may split reading by file group; one writer of the assessment |
| Kind definitions differ from the ones spec 09 later adopts | Reclassification | Low | Definitions recorded here (A-04) and proposed to 09 as an amendment if they are to become canonical |

## Assumptions

- A-01 | Whether a tool is part of this spec (the previous §8 put new tool behaviour in "a separate change with tests") | Resolved: the tool and its suite are delivered by this spec as their own test-first subtasks; REQ-11 lists them | Source: previous §8 last paragraph; REQ-13 and AC-05 need a deterministic method with a control example; global test-first rule (`.ai/principles/architecture.md` P7) | Reversible: yes
- A-02 | Where the tool and suite live | Resolved: `scripts/`, run directly, never from the validator or sync | Source: ADR-0019 Decision 3; `tests/fixtures/validator-runtime/source_guard.py:809-822`; spec 09 REQ-50 precedent | Reversible: yes
- A-03 | Whether `templates/codex-global-AGENTS.md` is audited | Resolved: yes, in the adapter set | Source: spec 09 REQ-55 moves it into `harness/codex/`; ADR-0003 Decision 2 | Reversible: yes
- A-04 | Operational definitions of the rule kinds | Resolved: Terminology → Kinds; proposed to spec 09 only through an amendment | Source: ADR-0009 Decision 3 names kinds without defining them; spec 09 Terminology ("Rule kind … the file-stem prefix"); P6; naming review §2 | Reversible: yes
- A-05 | Reference grammar | Resolved: spec 09 DM-16 forms on current names, extended with unmarked headings, load lines, bare names, reader token forms and statuses | Source: spec 09 REQ-22, REQ-31; spec 11 → Section resolution and Textual load command detection; Context facts 4–5 | Reversible: yes
- A-06 | Reader classes | Resolved: DM-3; `active` = spec 09 scan set R plus `README.md` | Source: spec 09 DM-17; previous §3 (history counted separately) | Reversible: yes
- A-07 | Proposal default owners | Resolved: DM-7 table | Source: `.ai/specs/README.md` → "Nine token optimization workstreams" (workstream boundaries) | Reversible: yes
- A-08 | Legacy scope | Resolved: audited files only; readers are spec 09's scan set L | Source: previous §5.2 (column of the inventory row); spec 09 REQ-11, REQ-29 | Reversible: yes
- A-09 | Economic statements | Resolved: none allowed in the outputs | Source: previous REQ-03; `.ai/specs/README.md` ("Word/byte reductions are diagnostics"); ADR-0014 rejected options | Reversible: yes
- A-10 | Installed-copy comparison | Resolved: optional, manual, recorded with both digests; the tool never reads installed copies | Source: previous §3 and §7; owner's rule not to touch deployed copies | Reversible: yes
- A-11 | Clean tree for delivery | Resolved: `worktree-dirty` blocks `verify`; dirty extraction only for drafts | Source: previous REQ-13 (same bytes, same output); best practice: the smallest reproducible choice | Reversible: yes
- A-12 | Runtime target | Resolved: none set; measured time recorded | Source: no project source states one; the skill forbids inventing numeric targets | Reversible: yes
- A-13 | Minimum duplicate unit of 8 words; 160-code-point context cut | Resolved: method parameters of `08-extract-1` | Source: best practice (shorter units are mostly list fragments); reversible by a new method version | Reversible: yes
- A-14 | How acceptance is recorded | Resolved: the report's `Accepted:` line, written by the owner after delivery | Source: spec 09 Notes → Prerequisites and Guard ("08's report accepted"); previous §9 | Reversible: yes
- A-15 | Per-occurrence classification of validator lines | Resolved: not done here; counts only (REQ-21); classification into `path_changes`/`contract_changes` is spec 09's delivery | Source: spec 09 REQ-51, REQ-52, DM-9; spec 09 Notes → Ownership | Reversible: yes
- A-16 | Which audit-time decision owners exist | Resolved: specs 11, 09, 12–15 and `owner`; 19, 21, 23 receive no findings from this audit | Source: previous REQ-02; spec 09 Out of Scope | Reversible: yes
- A-17 | ADR | Resolved: none required; amendments that alter ADR-0009 Decision 3 carry `requires_adr` for spec 09's `/spec-sync` | Source: `.ai/principles/coding.md` → Changing a contract (formats, stops, mode overrides); previous §6 step 8 | Reversible: yes
- A-18 | Boundary with spec 09 for pre-existing reference defects | Resolved: 08 records them as findings with owner 09; spec 09 fixes them | Source: spec 09 DM-16 last paragraph; previous REQ-04 | Reversible: yes
- A-19 | Where unmarked headings, `resolved-prefix` and bare names stand | Resolved: unmarked headings are defects (coding syntax); `resolved-prefix` and bare names are counted but never defects (A-27) | Source: `.ai/principles/coding.md:45-51`; spec 09 DM-17 stale-name forms | Reversible: yes
- A-20 | Duplicate consolidation owner | Resolved: 09 when a map rename, split or move performs it, otherwise 11; contradictions go to the owner | Source: spec 09 REQ-46; spec 11 Scope item 6; previous §3 (owner accepts changes of agreed behaviour) | Reversible: yes
- A-21 | How deviation from spec 09 is decided | Resolved: computed by `verify` from the auditor's `spec09_default`, derived by the DM-7 table; the reviewer re-derives defaults | Source: spec 09 DM-10, DM-11 (including "Unchanged names"), DM-12, REQ-23, REQ-35, REQ-55; spec 09 Notes → Ownership | Reversible: yes
- A-22 | What a "normative statement" is for REQ-21 coverage | Resolved: DM-5 statement units (list items, table rows, fenced blocks, paragraphs) | Source: spec 09 REQ-21 ("proves … covers them completely"); best practice: the smallest unit `verify` can enumerate | Reversible: yes
- A-23 | What counts as a workflow call and a repeated load | Resolved: resolved command edges from invocable workflows whose clause holds a call verb without a preceding negation and no earlier stop marker; candidates per caller-callee pair only. This narrows ADR-0014 Decision 1, which speaks of reuse "within its owning session": repeats more than one call level apart in one session are found by reading and recorded as `load-repeat` findings without an `RL` id. A transitive version merged most workflows into one component on the current tree | Source: ADR-0014 Decision 1; `workflows/pd-finalize.md:113`, `workflows/pd-decompose.md:14`, `workflows/phase-pipeline.md:105`, `workflows/pav-close.md:64`; `workflows/PIPELINE.md` names every command without calling it (no `Invocation:` line; `tests/workflow-instructions.py:11-12` skips it too); best practice | Reversible: yes
- A-24 | How capability assumptions are examined | Resolved: `HN` candidate lines naming a harness, each dispositioned | Source: previous REQ-04 ("names and capability assumptions"); ADR-0009 Decision 2 (branch on capabilities, never on harness name) | Reversible: yes
- A-25 | Cross-specification references (previous REQ-04) | Resolved: narrowed to edges from specifications (`planning` readers) into audited files; references between specifications are not audited | Source: previous §3 (specifications read only "if they contain references to this set"); `.ai/specs/README.md` owns spec-to-spec ownership | Reversible: yes
- A-26 | When a finding blocks spec 09 | Resolved: DM-7 → Blocking predicate | Source: spec 09 Notes → Prerequisites and Guard; previous REQ-14 ("blocking influence on 09 known") | Reversible: yes
- A-27 | `resolved-prefix` | Resolved: counted, not a defect | Source: spec 09 DM-16 form 2 accepts the ` — ` prefix | Reversible: yes
- A-28 | Where `verify` must pass | Resolved: in the delivery repository at the delivery commit; later trees may legitimately fail staleness or commit checks | Source: the audit is a snapshot (previous §1 "one pinned snapshot"); `.ai/memory/state.md` records merge-commit integration, but squash merges cannot be excluded | Reversible: yes

## Decisions

N/A — auto mode; no human decision was taken in the 2026-11-14 revision.

Owner decisions taken during the delivery (task 08, recorded by `/spec-sync` on 2026-11-18;
source: `.ai/tasks/todo/task-08-rules-workflows-audit/state.md → ### Assumptions`, source user):

- D-01 | 2026-11-17 | Home-directory prefixes in copied text | Decision: the tool writes
  `/home/<name>/` and `/Users/<name>/` as `~/` in every text it copies from audited files, before
  comparing and hashing, so the outputs meet REQ-25 and AC-22 and clusters stay intact;
  `method_version` stays `08-extract-1`. Applied to DM-6. Raised by the duplicate-cluster
  subtask during Execution.
- D-02 | 2026-11-17 | Stack base | Decision: the delivery stack is built on
  `feat/multi-repository-spec-run` (draft PR #104, tip `488edb1`), not on `main`, so the audit
  covers the multi-repository changes to rules and workflows; that PR merges first, and the
  permitted-changes check is computed against `488edb1`. Recorded at AC-02.
- D-03 | 2026-11-18 | Absolute paths other than home paths | Decision: REQ-25 and the
  delivery's derived Off-limits line "No absolute path … in any output or fixture" are narrowed
  to machine-specific home paths; system paths copied verbatim (DM-6, edge `raw` values) and
  placeholder absolute paths in test fixtures (AC-27 needs one) are allowed; no code or output
  change. Taken at the contract-check critical-failure gate (`### Critical Failures Decision:
  continue`). The token-pattern exemption for a copied file name (review finding 6, Issue List
  [6], recorded with [1]) belongs to the same verbatim-copy rule. Applied to REQ-25, REQ-03 and
  the suite contract.
- D-04 | 2026-11-18 | Review follow-ups | Decision: the owner approved fixing the deferred
  optional review findings 4, 5 and 7 ("fix all findings") after the first finalization.
  `verify` checks the blockers section in both directions (`blocker-extra`; the `None.` rule as
  `report-layout`) and resolves well-formed evidence against the inventory's paths and line
  counts (`evidence-unresolved`); the runbook limits the silent `verify` to the delivery commit.
  The delivered outputs are unchanged and verify silently. Applied to DM-8, DM-9 and AC-10.

## Clarifications

### Session 2026-11-14

No questions were asked (auto mode; the owner is unavailable by standing instruction). Gaps were
resolved as A-01–A-28; open items are Q-01 and Q-02.

## Open Questions

- Q-01 | non-blocker | Can the historical reports `docs/audits/2026-10-28-workflow-clarity-and-size.md`
  and `docs/audits/2026-11-06-test-suite-review.md` be restored? Impact: claims about earlier
  reviews stay unverifiable; the new audit of the available snapshot is not blocked (previous §10).
- Q-02 | non-blocker | Should `scripts/audit-instructions.py` stay after spec 09 lands, or be
  retired once spec 09's checker exists? Impact: maintenance of a second reference parser.
- Q-03 | non-blocker | Should these delivered and verified behaviours, which go beyond the
  Contracts table and have no owner approval, be added to it? (a) `extract` exits 2 with
  `root-unreadable` for an unreadable directory or file or a file name that is not valid UTF-8
  (the table lists an unreadable root only for `verify`); (b) `render --write` refuses with exit 2
  and `report-unreadable` (absent, not a regular file, a symbolic link, over 64 MiB or not
  UTF-8), `report-markers` or `report-unwritable`, and checks the report before its inputs;
  (c) the report is read up to 64 MiB (67108864 bytes), and `verify` reports an unreadable report
  as `report-layout` at `:0` (`scripts/audit-instructions.py:46-57`, `:3379-3420`, `:3648-3653`). Source: delivery
  proposals T-01 P4, T-06 P2 and T-06 P5 (task 08). Impact: until then, the Contracts table
  understates the exit-2 cases.
- Q-04 | non-blocker | Should Contracts → Git use and REQ-15 record the git isolation the
  delivery added (lazy fetching off, rename detection off, the user's and the system's attributes
  files not read, attributes read from the empty tree of the object format, filter drivers named
  by `info/attributes` blanked, file-system monitor off, hooks pointed at an empty location), and
  the git versions the guarantee needs? From the module docstring
  (`scripts/audit-instructions.py:59-96`): with git older than 2.45, `status` or `cat-file` in a
  partial clone can still fetch a missing object; older than 2.41, a tree attribute can still
  select a filter; older than 2.31, an `info/attributes` filter can still run; a submodule's own
  `info/attributes` and a root without its own `.git` are not covered. Source: the review
  finding of task 08 fixed in its git-read fix subtask (PR #115); only git 2.53.0 was run.
  Impact: REQ-15's offline and no-program statement holds as tested on current git only.
- Q-05 | non-blocker | Other behaviour the delivery's validators proposed to settle in this spec,
  pending an owner decision (task 08 proposals, not applied): T-01 P3 (roots below the git top
  level); T-02 P2 (duplicate headings, untrimmed and empty components); T-03 P3 (table separator
  rows with trailing whitespace); T-04 P3–P11 (output character set and escaping; relative
  `--report`; assessment-only checks with an invalid inventory; plain `verify` on a changed
  non-file kind; linked inventory and assessment files; evidence paths that are not repository
  paths; recursion depth of the reader walk; `--help`; exit on a failing standard output);
  T-05 P3–P6 (non-blank `reason`; `Terminology:` targets and whole-token ids in examples;
  amendment self-dependency and cycles; `merge` for every shared target); T-06 P3 (report line
  endings); T-12 Do Later (ASCII-only digits in evidence forms; escaping bidirectional control
  characters in diagnostic messages). T-03 P2 is resolved by D-01 and D-03.

## Notes

### Ownership between 09 and 08

08 owns the audit: tool, inventory, link graph, duplicate clusters, mixed-kind detection,
measurements, findings, proposals and proposed amendments. Spec 09 owns every contract and change
in its Scope, including its maps (DM-10–DM-12), which 08 amends only through the owner's
`/spec-sync` of spec 09. 08 counts words with spec 09's word count (DM-19), classifies with spec
09 DM-2's rule kinds, and reports files missing from DM-10/DM-11 (spec09_default null). Places
where 08 chose the narrower reading are A-08, A-15, A-18 and A-25.

### How proposed moves interact with the frozen validator

The audit moves, renames, merges and deletes nothing. Each non-`keep` map entry, when spec 09
executes it, touches frozen validator expressions and tests that name the source; spec 09 records
name-only changes as schema-2 `path_changes` and superseded contracts as `contract_changes`
(REQ-51, REQ-52), keeps check descriptions as frozen labels, and re-points tests and hooks
(REQ-53; for example `tests/workflow-instructions.py:38-54` and `hooks/git_rails.py:30`). The
report's Validator and test impact table gives the counts per entry so spec 09's Discovery can size
that work; its own frozen `tests/fixtures/validator-runtime/**` occurrences are listed separately.

### Handoff

The report path, `source_revision`, migration map, amendments, findings with `blocks_09` and open
questions go to spec 09. The owner accepts the report (`Accepted:` line) and runs `/spec-sync` on
spec 09 with the accepted amendments; disputed behaviour changes are never accepted
automatically (previous §9). Proposals owned by 11 are handled by spec 11 Scope item 9; those of
12–15 by their specs.

### Prerequisites and Guard for the implementing task

Spec 01 is complete (`.ai/specs/completed/01-git-source-of-truth.md`). Before extraction, commit
the tool and suite so the extraction runs on a clean tree; do the index and knowledge edits after
extraction (they are readers, so `--strict` is run on a checkout of `source_revision`). Never run
`scripts/sync.sh`, an installer, a workflow or a model for the inventory.

### Implementation order (hint; Discovery decides the decomposition)

1. RED: suite cases for `extract` (AC-01, AC-05, AC-06, AC-11–AC-17, AC-26); then the extractor.
2. RED: suite cases for `verify` and `render` (AC-04, AC-07, AC-08, AC-10, AC-18–AC-21, AC-25,
   AC-27–AC-29); then both subcommands.
3. Extract at a clean commit; read and assess by file group (rules, workflows, adapters), each
   leaf's RED being the `verify` diagnostics located in its files; then map, spec 09 inputs,
   findings and amendments; render; hand-written sections.
4. Index and knowledge updates; full validator; independent review; review line.

### Rejected alternatives

- A Markdown-only report with hand-made tables (not reproducible; no binary completeness check).
- New checks in `scripts/validate-contracts.sh` or a suite under `tests/` (frozen inventory and
  source guard, ADR-0019 Decision 3).
- Waiting for spec 09's checker (it is delivered after this audit).
- Classifying every validator occurrence here (spec 09's DM-9 work; A-15).

### Identifier history

- REQ-01–REQ-14 and AC-01–AC-10 keep their previous meaning, with these recorded changes:
  AC-01–AC-10 now also name fixture cases; REQ-11 now lists the tool, suite and knowledge files
  (A-01); previous REQ-02's "repeated reports and checkpoint records" is now the explicit REQ-28;
  previous REQ-03's "monetary conclusions only from spec 05 measurements" is narrowed to no
  monetary or token statement at all (A-09); previous REQ-04's "active references between
  specifications, names and capability assumptions" is covered by planning-reader edges (A-25)
  and `HN` candidates (A-24). REQ-15–REQ-29 and AC-11–AC-29 are new.
- Spec 09's withdrawn REQ-01 (inventory of files, kinds, sizes, references, legacy integrations)
  is covered by 08 REQ-01, REQ-05, REQ-17, REQ-18 and REQ-20; its REQ-02 (mixed kinds with section
  boundaries) by REQ-06; its REQ-03 (ambiguous names, missing target sections) by REQ-07; its
  REQ-04 (verbatim and semantic duplication) by REQ-08; its AC-01 (the full report accepted as an
  input) by AC-10 and the `Accepted:` line.
- The previous §9 sentence preserving "the decision on unscheduled 07" is superseded by ADR-0021
  (07 scheduled 2026-11-13).

### Follow-ups for other specs and shared files (not edited here)

- Spec 09: name the report's `Accepted:` line as the acceptance its Guard checks; consider adding
  root `README.md` to scan set R; adopt or replace the kind definitions of A-04 in `domain.md`
  (REQ-34).
- Spec 11: Scope item 9 consumes findings of proposal types with owner `11` by `AUD-08-NNN` id.
- `docs/README.md:13-20` links five absent audit files (Context fact 6); an owner decision.
- The identity ledger row `.ai/tasks/completed/task-01-git-source-of-truth/state.md:214`
  expects the former name once on line 23 of this file; this revision keeps that line.

### Change log

- 2026-11-06 — implementation/state reconciliation (preserved above).
- 2026-11-14 — English refinement: request translated under Source; REQ-01–REQ-14 and
  AC-01–AC-10 restated in EARS and binary form; tool, data model, verifier codes, report layout,
  edge cases, REQ-15–REQ-29 and AC-11–AC-29 added; the absent test-suite review link removed.
- 2026-11-14 — independent final review: optional overflow targets carry `sections: null` and stay out of the exactly-once cover; `in_spec09_grammar` narrowed to spec 09 DM-16 form 2 heads; README and spec citations by heading or id; line 23 untouched.
- 2026-11-18 — `/spec-sync` of task 08 (`.ai/tasks/todo/task-08-rules-workflows-audit`), called
  by validation finalization after the contract check (16 of 17 passed; the failed Off-limits
  line decided by the owner), the review and the one fix were complete; `verify` silent and the
  suite at 228/228 on the delivery stack. Deltas: (1) DM-6, implemented-differently — home
  prefixes in copied text written as `~/` before comparing and hashing, `method_version`
  unchanged; edit: new DM-6 bullet; source D-01. (2) REQ-25, implemented-differently (approved
  narrowing) — from "only repository-relative or `~/`-relative paths" to no machine-specific home
  path, with system paths in verbatim-copied text and placeholder fixture paths allowed; edit:
  REQ-25 restated, one sentence added to the suite contract; source D-03. (3) REQ-03,
  implemented-differently (clarification under the same rule) — a copied file name that matches
  the token pattern is not a token count; edit: one sentence; source D-03, Issue List [6].
  (4) AC-02, implemented-differently (verification base) — the permitted-changes list computed
  from `488edb1` instead of `merge-base main`; edit: delivery annotation, criterion text kept;
  source D-02. Owner decisions recorded under Decisions; behaviour beyond the spec without owner
  approval and the validators' pending proposals listed as Q-03–Q-05; no requirement or
  criterion removed or renumbered; REQ-15 and every other requirement unchanged.
- 2026-11-18 — `/spec-sync` of task 08 after fix-task T-12 (owner-approved review follow-ups,
  D-04): suite 237/237, `verify` silent. Deltas, all implemented-beyond with owner approval:
  (1) DM-8 blockers rule stated in both directions; (2) DM-9 gains `blocker-extra` and
  `evidence-unresolved`, and `report-layout` covers the `None.` rule; (3) AC-10 extended for
  `blocker-extra` (AC-20 covers both codes through its every-code fixture). Q-05 lists the T-12
  Do Later proposals. No requirement or criterion removed or renumbered; line 23 untouched.

## Readiness Checklist

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph describing the outcome | PASS — one paragraph: pinned reproducible audit, verified assessment, outputs for 09 and 11/12–15, no instruction change |
| 2 | Out of Scope names concrete exclusions | PASS — audited trees, spec 09 contracts, spec 11/19/10 work, economics, installed copies, validator registration, historical report restoration |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-29; preserved ids keep their meaning (Notes → Identifier history) |
| 4 | Every REQ maps to ≥1 AC; every AC names ≥1 REQ | PASS — Traceability table covers REQ-01–REQ-29 and AC-01–AC-29 |
| 5 | Every AC is binary, observable and can guide a test before implementation | PASS — fixture cases with named inputs and expected codes; delivery checks with exact commands |
| 6 | Non-functional targets measurable, standard-referenced or N/A | PASS — determinism, read-only, offline, dependencies, hygiene, security; runtime has no target by recorded decision (A-12) |
| 7 | Data model and contracts specified | PASS — DM-1–DM-9; CLI, exit codes, git use, suite contract; delivered exit-2 refusals and git isolation beyond the Contracts table are open as Q-03 and Q-04 |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — Edge Cases table (encodings, links, empty files, stale trees, cycles, negations, single writer) |
| 9 | Every ambiguity recorded as resolved or open | PASS — A-01–A-28; delivery decisions D-01–D-03; Q-01–Q-05 |
| 10 | No blocker question remains | PASS — all five open questions are non-blocking |
| 11 | Every existing-code claim has a verified path:line citation | PASS — citations re-verified by the reviewer in every round; the `scripts/audit-instructions.py` citations added on 2026-11-18 verified at `df3aa06` |
| 12 | Terminology matches project domain definitions | PASS — Terminology table; kinds from ADR-0009 Decision 3 with operational definitions (A-04); word count from spec 09 |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — four implementation steps (Notes), reading split by file group |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 99/100, critic: sub-agent, open: F-33 (minor; applied after the final round) |

**Verdict: READY FOR DEVELOPMENT** (re-run 2026-11-18 by `/spec-sync` after the delivery
reconciliation; check 14 is the authoring review and was not repeated). Automated readiness is
not sign-off; review before implementation.
