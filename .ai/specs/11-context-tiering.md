# 11. Instruction tiers, explicit loads and concise reports without losing obligations

## Source

- **Request.** Owner roadmap direction 3 of 2026-10-21 ("shorter instructions and
  outputs"), bound by ADR-0009 Decision 6 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:230-232`:
  "≤ 700 words per always-on rule, ≤ 6 000 words total; worked examples and incident
  narratives in `rules/reference/` deployed as `ref-*` skills") and Decision 2
  (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:100-101`: rule front matter
  `description:` + `load: always | on-demand`; workflow front matter `description:`,
  `phase:`, `step:` and "(spec 11) `loads:`"). Workstream 3 of the roadmap index
  (`.ai/specs/README.md`, "Nine token optimization workstreams").
- **Previous revision.** Russian text of 2026-10-28 with the 2026-11-06 review block, last
  committed in `c4372f881dd544ffbf8d2374dc66a8e468d61a86`. English translation of its core
  statements (translated from Russian, sections 1–3 of that revision):
  - "Reduce repeated instructions and the retelling of data already available, while
    preserving every prohibition, mandatory load, stop condition, acceptance criterion,
    test evidence and recovery information."
  - "This specification owns the structure of rules, load declarations, the counting of
    instruction volume and the form of the concise report. It does not change the meaning
    of workflows, task statuses, the billing model, model selection or the conditions for
    accepting a result."
  - "Text reduction by itself does not mean this specification is fulfilled. The historical
    estimate of 40–60 thousand tokens at initial load is withdrawn and must not be used as a
    baseline. The report `docs/audits/2026-10-28-workflow-clarity-and-size.md` is absent
    from the verified tree and is not evidence."
  - Invariants of that revision: every obligation has one canonical place and a verifiable
    load path before it is needed; a conditional load means "mandatory when the condition
    holds", not "at the agent's discretion"; a concise view never replaces the full
    structured result; word and byte counts are never called token counts and never imply
    money saved or cache hits; the meter, the reference checker and the generator never run
    models and never change task state.
- **This revision.** 2026-11-13, refined in place under the owner's standing authorization
  for in-place replacement, in autonomous mode: no questions were put to the owner; every
  resolved gap is recorded under `## Assumptions`. Requirement ids REQ-01–REQ-08 and
  acceptance ids AC-01–AC-05 keep their meaning; new ids are appended.

### Implementation review — 2026-11-06

- **Disposition:** Planned; existing instruction foundations only.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** Parent/standalone loading rules and explicit canonical references exist.
- **Outstanding scope and limits:** Reference tiers, loads metadata, ref-skill deployment, the context-load graph meter, and the required measured reduction are not delivered. Text cleanup is not proof of the numerical acceptance target.
- **Sources:** [`rules/phase-discovery.md`](../../rules/phase-discovery.md), [`rules/phase-atomic-execution.md`](../../rules/phase-atomic-execution.md), [`tests/workflow-instructions.py`](../../tests/workflow-instructions.py), [`scripts/sync.sh`](../../scripts/sync.sh).
- Existing requirement and acceptance identifiers remain binding. Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

## Context & Problem

Facts verified on 2026-11-13 at `060ce6dbc7116002ac5e6cd47981cfd3c13d60ff` (word counts are
whitespace-separated runs over the whole UTF-8 file; for these files the result equals
the counter defined in `## Contracts & Interfaces → Word and byte counting`):

1. Rules carry Windsurf front matter, not the ADR-0009 schema: `trigger: always_on`
   (`rules/tdd.md:1-3`) or `trigger: model_decision` (`rules/phase-atomic-execution.md:1-4`).
   No file under `workflows/`, `rules/` or `principles/` contains a `loads:` key (ripgrep
   `^loads:` returns nothing). There is no `rules/reference/` directory and no
   `scripts/measure-context.*`.
2. The seven `trigger: always_on` rules total **15,345 words**: `git-flow` 2,870,
   `language` 122, `orchestration` 1,646, `quick-flow` 1,681, `run-log` 4,547, `tdd` 1,845,
   `workflow-globals` 2,634. Eight files directly under `rules/` exceed 700 words: the six
   above other than `language`, `workflow-reference` (5,193) and `global-claude` (985),
   which spec 09 moves out of `rules/` to `harness/claude/always-on.md` (09 DM-10, REQ-55).
   `rules/global-claude.md` is copied to `~/.claude/CLAUDE.md` and followed by the whole of
   `harness/claude/capabilities.md` (1,607 words) and an installation-result line
   (`scripts/sync.sh:58-67`, `scripts/sync.sh:99-101`); Codex receives
   `templates/codex-global-AGENTS.md` (484 words) plus `harness/codex/capabilities.md`
   (91 words) the same way (`scripts/sync.sh:155-158`).
   On Claude Code only that global file is loaded automatically; rules are model-invoked
   `rule-*` skills, not always-on (`.ai/context/environment.md:19`; P11,
   `.ai/principles/architecture.md:84-88`). The `trigger: always_on` marker takes effect
   automatically only on Windsurf, which spec 09 retires.
3. Instruction loading is hand-written prose in each workflow, for example "Load the
   `phase-atomic-execution` rule (`## Context Bootstrap`) …" (`workflows/pae-tests.md:56-59`,
   `workflows/pae-implement.md:53-57`), "Load `tdd → ## Test-level gate`"
   (`workflows/pae-tests.md:75`) and "Load the `phase-atomic-validation` rule …"
   (`workflows/pav-check.md:24-26`). Nothing checks that a list is complete or that a cited
   source is reachable before it is needed; `tests/workflow-instructions.py:20-35` only
   checks that cited `file → ## Section` targets exist.
4. Deployment copies only `rules/*.md` (a non-recursive glob) into `rule-<name>` skills for
   both harnesses (`scripts/sync.sh:123-129`, `scripts/sync.sh:167-173`); a nested
   `rules/reference/` file would not be deployed today. No deploy manifest exists in the
   current tree; spec 09 introduces it (09 REQ-10, REQ-42, REQ-45).
5. Step reports are free text with no fixed fields: `workflows/pae-tests.md:234-246`,
   `workflows/pae-implement.md:197`, `workflows/pav-check.md:110`,
   `workflows/pae-finalize.md:66-68`, `workflows/pav-close.md:70`. In orchestrated mode
   workers never run git (`workflows/spec-run.md:245`).
6. The default validator runs `tests/workflow-instructions.py`
   (`scripts/validate-contracts.sh:5153-5154`) through the `check "<desc>" "<result>"`
   helper (`scripts/validate-contracts.sh:583-597`); that test also greps rule text
   (`tests/workflow-instructions.py:38-54`). The validator check inventory is frozen: the
   inventory oracle requires exactly 36 acceptance expressions and 37 focused modes
   (`tests/fixtures/validator-runtime/oracle.py:250`) and a fixed suffix of additive results
   (`:244-247`); the amendment record `tests/fixtures/validator-runtime/inventory-amendment.json`
   holds only `paths`, `removed_results`, `resources` and `schema`; and the source guard
   pins the digest of every shell and Python file under `tests/`
   (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:73-77`; procedure in
   `tests/fixtures/validator-runtime/README.md`). For that reason the `/spec-draft` check
   runs standalone from `scripts/` (ADR-0019 Decision 3) and spec 19 gates deployment
   through `scripts/sync.sh` instead of the validator. 139 lines of
   `scripts/validate-contracts.sh` reference `rules/` files by path.

**Consequence.** Workflows depend on hand-maintained load lists that nobody checks;
whether a rule is "always on" depends on the harness; rules far exceed the 700-word target
of ADR-0009 Decision 6; nobody can state which instructions a workflow needs, measure them
reproducibly, move rationale out of the mandatory path without risking a lost
prohibition, or verify that a short report still carries its evidence.

## Goal

Make every instruction an agent must follow reachable through an explicit, checked load
declaration, keep the always-on set small by moving rationale, examples and history into
on-demand reference files, measure instruction volume reproducibly as words and bytes, and
give the four atomic-cycle reports a fixed concise form that references full evidence
instead of retelling it — so that the mandatory instruction volume of the atomic test and
implementation steps falls to at most half of a recorded baseline with no obligation lost.

## Scope

1. Load-declaration schema version 1 (`loads:`) in workflow front matter (required) and in
   top-level rule front matter (optional), with a closed condition grammar and feature
   registry.
2. `scripts/measure-context.sh` (Bash launcher) and `scripts/measure-context.py` (Python
   3.11+ standard-library engine): `check`, `measure`, `compare`, `obligations`,
   `evidence make`, `evidence verify`.
3. Two new top-level rules: `rules/contract-loads.md` (`load: always`) and
   `rules/contract-reports.md` (`load: on-demand`).
4. Reference tier: `rules/reference/<name>.md` files holding rationale, optional examples
   and incident history, deployed as `ref-<name>` skills through spec 09's ownership
   mechanism.
5. Size limits owned here: ≤ 700 words per top-level rule, ≤ 6,000 words per harness
   always-on set.
6. Rewriting rules and workflows to meet the limits and the 50% target, with an obligation
   map proving nothing obligatory was lost.
7. Concise report forms for the RED, GREEN, independent check and completion boundaries of
   the atomic cycle, evidence references that can be verified by hash, and the `/spec-run`
   orchestrator's rejection of truncated deltas carried in those four reports.
8. A standalone acceptance suite `scripts/check-context-tiering.py`, a deployment gate in
   `scripts/sync.sh` running `measure-context.sh check`, re-pointing of existing validator
   checks whose rule text moves (path-map entries in 09's schema-2 inventory amendment),
   knowledge-base updates and an ADR.
9. Every proposal and every finding that the 08 audit assigns to owner 11 (08 REQ-02 and
   the owner's decision on AUD-08-065, 2026-11-18), whatever its type: each is either
   implemented (with obligation-map rows where it moves an obligation) or listed as
   declined, with its reason, in the measurement summary.

## Out of Scope

- Token counts, cached input, cost or duration (spec 05); paid golden runs and strategy
  comparison (spec 10). An owner-authorized paid run, if one happens, is recorded under 10
  and is not an acceptance condition here.
- Rule and workflow naming, `load:` field introduction, the bootstrap 300-word and
  always-on 1,200-word limits, adapters, `deploy.env`, the deploy manifest and its
  ownership rules (spec 09). This spec consumes them.
- Generated references, the generated always-on core and `reads`/`writes`/`called_by`
  metadata (spec 19).
- Project-context selection, packets and their freshness, including which `.ai/` files a
  phase bootstrap reads (spec 12).
- The structured checkpoint envelope, receipts and orchestrator deltas schema (spec 13);
  bounded tool output and captured artifacts (spec 14).
- Report forms for Discovery, phase-level Execution/Validation finalizers, `/spec-run`
  orchestrator summaries and any workflow outside the four atomic boundaries.
- Changing workflow semantics, status vocabularies, protected sections, test-first order,
  stops, git rails or the single-writer rule.
- Runtime enforcement of loading by a harness hook (P10 direction; future work).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Maintainer (workflow author) | Edits rules, workflows, references, declarations; runs the meter and validator; never edits deployed copies (P1) |
| Implementing agent | Delivers this spec test-first at the `smoke` level for Markdown and with unit tests for the engine; captures baseline and after records |
| Runtime agent | Executes a workflow; resolves its `loads:` per `contract-loads`; renders the report forms |
| Orchestrator (`/spec-run`) | Consumes worker reports; rejects truncated deltas; owns git and shared files (unchanged) |
| Independent reviewer | Verifies the obligation map semantically (section-level completeness is mechanical) |
| Owner | Decides when the 50% target is not met; authorizes deployment |
| `scripts/measure-context.sh` | Reads source files and optional manifest; writes only to stdout/stderr; never writes files, runs models or uses the network |
| `scripts/sync.sh` (as delivered by 09) | Deploys `ref-<name>` skills and records ownership |
| `scripts/check-context-tiering.py` | Acceptance suite, run manually by maintainers; never run by `scripts/sync.sh` |
| `scripts/validate-contracts.sh` | Unchanged inventory; existing checks re-pointed only (REQ-25) |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Top-level rule | A regular file `rules/<stem>.md` (not in a subdirectory) | This spec; 09 DM-2, DM-10 |
| Reference file | A regular file `rules/reference/<stem>.md`; explanatory only; deployed as `ref-<stem>` | ADR-0009 D6; 09 REQ-26 |
| Instruction source | A top-level rule, a reference file or `principles/<stem>.md` | This spec |
| Load declaration | The `loads:` front-matter mapping (DM-1) | ADR-0009 D2 |
| Harness | A directory as 09 DM-5 defines it (a non-hidden directory under `harness/` holding `deploy.env`, which on a valid tree is the same set as directories holding `capabilities.md`) | 09 DM-5 |
| Always-on set of harness *h* | `harness/<h>/always-on.md` plus, until spec 19's delivery, `harness/<h>/capabilities.md` (from then on the generated `always-on.md` embeds the declaration and is counted alone, 19 REQ-50), every top-level rule with `load: always`, and the mandatory closure of those rules. `always-on.md` names each `load: always` rule in a textual load command, which is how such a rule reaches a session on a harness where rules are skills (REQ-31); those lines count toward 09's 1,200-word body limit (09 REQ-54) and toward the 6,000 words here | This spec; 09 REQ-54, DM-14; 19 REQ-50 |
| Mandatory closure of *w* | Every instruction source reachable from workflow *w* through mandatory edges only | This spec |
| Mandatory set | Always-on set ∪ {*w*} ∪ mandatory closure of *w*; its word count is `mandatory_words` | Previous revision §6 |
| Conditional branch | A conditional edge's target plus that target's mandatory closure | This spec |
| Selected set | Sources reachable through mandatory edges and conditional edges whose condition is true or unknown for the supplied features | This spec |
| Upper bound | Every source reachable through any edge; a bound, not a reachable scenario | Previous revision §5 step 7 |
| Textual load command | A body line containing a load/read verb and a backtick name resolving to an instruction source (Contracts → Textual load command detection) | This spec |
| Obligation | A prohibition, stop condition, mandatory action or canonical vocabulary definition | Previous revision REQ-01 |
| Obligation map | The JSON record of DM-6 | This spec |
| Measurement record | The JSON output of `measure` (DM-4) | This spec |
| Baseline revision | The single commit at which the only instruction changes made by this spec are: a `loads:` declaration describing current loading in every workflow (and any rule that needs one), the `contract-loads` citation line in every workflow, the new `rules/contract-loads.md`, the `harness/<h>/always-on.md` lines naming every `load: always` rule (REQ-31), and REQ-22's registration of `loads` in 09's checker. `rules/contract-loads.md` counts in the before records | This spec |
| Baseline record | A measurement record produced at the baseline revision | This spec |
| Report form | The fixed field list of one boundary in `contract-reports` (DM-8) | This spec |
| Evidence reference | A line of DM-7 naming a file or section and its SHA-256 | This spec |
| Full structured result | On spec 13's helper route, its checkpoint message (13 DM-3); otherwise (before 13, on 13's manual route, REQ-08, or outside `/spec-run`) the canonical state-file writes plus complete `delta` blocks. Under `/spec-run` after 13, `delta` blocks hold 13 DM-4 lines where an operation expresses the change and free text otherwise (13 REQ-36). The concise report form (DM-8) stays the human view either way | This spec; 13 DM-3, DM-4 |
| Word | A maximal non-empty run of non-whitespace characters, counted with Python `str.split()` (counter version 1); files containing U+001C–U+001F are rejected, so on every accepted file the count equals the Unicode White_Space definition of spec 09 | 09 DM-19; spec 19 Terminology (Word) |

Rejected synonyms: "token count" for a word count; "always-loaded" or "global" for the
always-on set; "optional" for a conditional load (a conditional load is mandatory when its
condition holds); "ref skill" for a reference file (the skill is the deployed copy).

## Requirements

Rule and workflow names follow spec 09's target names (09 DM-10, DM-11):
`atomic-execution-tests` (now `pae-tests`), `atomic-execution-implement` (now
`pae-implement`), `atomic-validation-check` (now `pav-check`), `atomic-validation-close`
(now `pav-close`). Where 09's final map differs, its map governs.

- **REQ-01.** WHEN `measure-context.sh check` runs, THE SYSTEM SHALL report finding
  `rule-size-exceeded` for every top-level rule whose whole file exceeds 700 words,
  regardless of its `load:` mode, and finding `always-on-size-exceeded` for every harness
  whose always-on set exceeds 6,000 words. (Spec 09's 300-word bootstrap and 1,200-word
  always-on body limits stay in force and are checked by spec 09 (09 REQ-19, REQ-32 and REQ-54).)
- **REQ-02.** WHEN deployment runs, THE SYSTEM SHALL install each reference file
  `rules/reference/<stem>.md` byte-for-byte as `<skills_dir>/ref-<stem>/SKILL.md` for every
  supported harness and record each as an owned object in the deploy manifest in force
  (09 DM-6; after spec 20, the manifest of its installer, 09 Notes "Relationship to spec 20").
- **REQ-03.** WHEN `check` runs, THE SYSTEM SHALL report `loads-missing` for every workflow
  without a `loads:` declaration and `loads-not-cited` for every workflow whose body does
  not contain the citation `` `contract-loads → ## Runtime resolution` ``.
- **REQ-04.** WHEN `measure --workflow <id>` runs, THE SYSTEM SHALL emit a measurement record
  (DM-4) giving, per harness, always-on, mandatory, selected, conditional and upper-bound
  word and byte counts over the union of loaded regions, each region counted once, with no
  token, cost or cache field.
- **REQ-05.** THE delivered change SHALL bring `mandatory_words` of `atomic-execution-tests`
  and of `atomic-execution-implement` to at most 50% of the respective baseline record for
  each harness, as reported by `compare`, with an obligation map that `obligations` accepts.
- **REQ-06.** WHEN `atomic-execution-tests`, `atomic-execution-implement`,
  `atomic-validation-check` or `atomic-validation-close` reports at the end of its run, THE
  SYSTEM SHALL render its boundary's report form from `contract-reports` (DM-8) with every
  field present, in canonical order, referencing the specification, plan, task state and
  logs by path instead of restating them.
- **REQ-07.** WHEN a report carries a state delta, a branch instruction, an error or
  acceptance evidence, THE SYSTEM SHALL include it verbatim or as an evidence reference
  (DM-7), never shortened, summarized or elided.
- **REQ-08.** WHEN `scripts/sync.sh` runs, THE SYSTEM SHALL run
  `bash "$ROOT/scripts/measure-context.sh" check --root "$ROOT"` after contract validation
  and before hook installation and every copy step, and SHALL exit 1 without deploying
  anything when that command exits non-zero.
- **REQ-09.** WHEN `check` runs, THE SYSTEM SHALL report `reference-stop-marker` for a
  reference file containing `**stop**`, `reference-loads-forbidden` for one with a `loads:`
  key, `reference-load-command` for one with a textual load command, and
  `reference-front-matter-invalid` for one whose front matter is not exactly one
  `description:` key with a non-empty single-line value.
- **REQ-10.** IF a conditional entry's condition evaluates to unknown, THEN THE SYSTEM SHALL
  include its branch in the selected set with reason `conditional-unknown` (meter) and
  require the runtime agent to load it (`contract-loads`).
- **REQ-11.** IF the load graph contains a cycle, THEN THE SYSTEM SHALL report finding
  `cycle` with the complete path, set `complete` to false, set every count to null and exit
  with status 1, without looping.
- **REQ-12.** WHEN `check` runs, THE SYSTEM SHALL report `textual-load-undeclared`, with file
  and line, for every textual load command in a workflow or top-level rule whose target is
  absent from that same file's `loads:` (mandatory or conditional), unless the target
  belongs to the always-on set of each harness.
- **REQ-13.** WHEN `obligations --map <file> --baseline <dir>` runs, THE SYSTEM SHALL report
  every changed baseline section without a map row, every invalid row and every obligation
  row whose destination is missing, inside `rules/reference/`, removed, or unreachable for a
  listed consumer under the row's load condition (DM-6).
- **REQ-14.** THE `contract-loads` rule SHALL instruct the runtime agent to fall back to
  full loading when a declaration is missing or unreadable and to **stop** when a mandatory
  target is unavailable, using the exact lines of `## Contracts & Interfaces → Runtime
  loading contract`.
- **REQ-15.** THE `contract-loads` rule SHALL instruct a standalone invocation or fresh
  worker to load its complete mandatory closure itself, and permit a child in the same
  session to reuse only sources still in context and unchanged, using the exact lines of
  `## Contracts & Interfaces → Runtime loading contract`.
- **REQ-16.** WHEN `evidence make` runs on an existing, unambiguous, `text@1`-valid scope, THE
  SYSTEM SHALL print the DM-7 reference line for it and exit 0, and otherwise print nothing
  on stdout and exit with the DM-7 failure code.
- **REQ-17.** WHILE any subcommand runs, THE SYSTEM SHALL write nothing to the file system,
  invoke no model, open no network connection, and produce byte-identical output for
  byte-identical inputs and arguments.
- **REQ-18.** WHEN a declaration selects sections, THE SYSTEM SHALL resolve each selector as
  an exact heading path (DM-1, Contracts → Section resolution) and report `section-missing`
  when it matches nothing and `section-ambiguous` when it matches more than one location.
- **REQ-19.** WHEN `check` runs, THE SYSTEM SHALL report `reference-name-invalid`,
  `ref-skill-collision`, `reference-orphan` and `rule-unreachable` under the conditions of
  DM-9.
- **REQ-20.** WHEN `check` reads a `loads:` declaration, THE SYSTEM SHALL report every
  violation of DM-1 and DM-2 with the finding code DM-9 assigns to it.
- **REQ-21.** THE delivered change SHALL add vocabulary rows for "Always-on set", "Load
  declaration", "Reference file", "Obligation map", "Evidence reference" and "Report form"
  to `.ai/principles/domain.md`, the meter and suite commands and the rollback procedure to
  `.ai/context/runbook.md`, `rules/reference/` and the meter to
  `.ai/memory/architecture.md`, rows for the three new scripts to `scripts/README.md`, and
  an Accepted ADR covering the load declaration, reference tier and report forms to
  `.ai/adr/index.md`.
- **REQ-22.** WHEN spec 09's checker `scripts/lint-instructions.py` reads a top-level rule or a
  workflow, THE SYSTEM SHALL validate a `loads:` key as 11's registered extension key (09
  DM-2, DM-3) by the DM-1 grammar, so that `loads` on a rule is accepted instead of reported
  as `metadata-unknown-field`.
- **REQ-23.** WHEN `compare --before <a> --after <b>` runs, THE SYSTEM SHALL report per harness
  `target_met: true` only when both records satisfy every DM-5 comparability condition and
  `2 × after.mandatory_words ≤ before.mandatory_words`, `"unknown"` with reasons when any
  condition fails, and `false` otherwise.
- **REQ-24.** THE `contract-reports` rule SHALL instruct the consumer of one of the four
  reports (the `/spec-run` orchestrator, or the user) to reject a `delta` block that is
  unterminated or contains an elision marker, and to treat an evidence reference that fails
  `evidence verify` as unavailable evidence, never as passing, using the DM-7/DM-8 lines.
- **REQ-25.** THE delivered validator SHALL keep every `check` call of the baseline revision
  with its description unchanged and its expression either unchanged or changed only by a
  path-only entry that spec 09's schema-2 inventory amendment (09 DM-9, REQ-51) accepts
  (Contracts → Existing validator checks).
- **REQ-26.** THE delivered change SHALL pass spec 10's offline regression suite, run as the
  standalone command `python3 -I tests/golden-runs.py` (10 A-02; never through
  `scripts/validate-contracts.sh`), with no change to that suite's expected results.
- **REQ-27.** WHEN `check`, `measure` or `obligations` runs, THE SYSTEM SHALL report each DM-9
  code not covered by another requirement under exactly the condition DM-9 states for it.
- **REQ-28.** IF the 50% target of REQ-05 is not met, THEN AC-03 SHALL remain unmet and be
  handed to the owner; no revision other than the baseline revision SHALL serve as the
  baseline, and no obligation SHALL be removed to meet the target.
- **REQ-29.** WHEN `check` runs, THE SYSTEM SHALL report `always-on-load-unreachable` for every
  textual load command in `harness/<h>/always-on.md` whose target is outside that harness's
  always-on set.
- **REQ-30.** WHEN `evidence verify` runs, THE SYSTEM SHALL exit 0 only if the referenced scope
  exists and is unambiguous, satisfies the reference's format, and its SHA-256 equals the
  reference; otherwise it SHALL exit with the DM-7 failure code.
- **REQ-31.** WHEN `check` runs, THE SYSTEM SHALL report `always-on-rule-not-named` for every
  pair of harness *h* and `load: always` rule *r* where `harness/<h>/always-on.md` has no
  textual load command resolving to *r*.
- **REQ-32.** WHEN `check` runs, THE SYSTEM SHALL report `report-form-not-cited` for each of
  the four boundary workflows whose body lacks the citation
  `` `contract-reports → ## <Boundary> report` `` of its own form, and for `spec-run` when its
  body lacks `` `contract-reports → ## Consuming reports` ``.

## Data Model

All entities are **new** unless marked existing. Files are UTF-8 with LF line endings; JSON
outputs use `sort_keys=True`, `ensure_ascii=False`, separators `(",", ":")` and one trailing
LF.

### DM-1 Load declaration, schema version 1

Location: front matter (the lines between a first-line `---` and the next line that is
exactly `---`) of every `workflows/*.md` (required) and of any top-level rule (optional).
Forbidden in reference files and `principles/*.md`. Only the `loads` subtree is defined
here; the other keys belong to spec 09.

```yaml
loads:
  schema_version: 1
  mandatory:
    - path: rules/contract-tdd.md
      sections: ["## Test-level gate", "## RED — what counts"]
    - path: principles/testing-standards.md
  conditional:
    - condition_id: characterize
      condition: "flag.characterize == yes"
      path: rules/reference/tdd-characterization.md
      on_unknown: load
```

The paths above illustrate shape only; a real declaration names existing files.

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Required; only `1` |
| `mandatory` | list | Required; may be `[]` |
| `conditional` | list | Optional; absent equals `[]` |
| entry `path` | plain scalar | Required; `rules/<stem>.md`, `rules/reference/<stem>.md` or `principles/<stem>.md`, `<stem>` = `[a-z0-9]+(-[a-z0-9]+)*`; relative to the source root; no `.`/`..` components, backslash or leading `/` |
| entry `sections` | JSON array of strings on one line | Optional; non-empty when present; each a heading path (Contracts → Section resolution) |
| `condition_id` | plain scalar `[a-z][a-z0-9_]*` | Required on conditional entries; unique within the declaration |
| `condition` | JSON string | Required on conditional entries; DM-2 grammar |
| `on_unknown` | plain scalar | Required on conditional entries; only `load` |

Extent: the block starts at the line `loads:` at column 0 inside the front matter and ends
before the next line at column 0 or at the closing `---`. Only those lines are parsed
here; every other front-matter key and its syntax belong to spec 09 (rule and workflow
fields) and spec 19 (`reads`, `writes`, `called_by`) and are ignored by this engine.

Line grammar inside the block (a subset of what spec 19 `## Data Model → Workflow metadata`
accepts for `loads`; 19 applies the same narrower plain-value rule inside the block, Notes → "Ownership statements for spec 19"): at indent 2 only `schema_version`, `mandatory`, `conditional`; a list
is `[]` on the key's line or items at indent 4 starting `- <key>: <value>` with further
keys of the same item at indent 6; a plain value is `[A-Za-z0-9_./-]+`; a value starting
with `"` is a JSON string parsed with `json.loads` and must be the whole rest of the line;
`sections` is a JSON array of strings parsed with `json.loads`. Tabs, comments, single
quotes, anchors, aliases, tags, flow mappings and multi-line scalars are
`yaml-subset-invalid`; a key outside the table is `unknown-key`; a repeated key in one
mapping is `duplicate-key`; a required key absent is `required-key-missing`. Two entries
with the same path in one declaration are permitted and merged; a mandatory entry absorbs
conditional entries for the same path.

Lifecycle: declarations are edited by maintainers only; no migration of consumer artifacts
is needed because consumer `.ai/` files are not instruction sources.

### DM-2 Condition grammar and feature registry

```text
condition  = comparison { " and " comparison } ;
comparison = feature " " ( "==" | "!=" ) " " value ;
feature    = name ( "." name )+ ;          (* must be a registry feature *)
name       = "a".."z" { "a".."z" | "0".."9" | "-" } ;
value      = 1*( "a".."z" | "0".."9" | "-" ) ;
```

Single spaces exactly; no `or`, parentheses, negation or other operators. Evaluation is
three-valued per comparison (true, false, unknown when the feature has no established
value); the conjunction is false if any comparison is false, otherwise unknown if any is
unknown, otherwise true.

Feature registry version 1, defined on one anchored line (`.ai/principles/coding.md:39`)
in `rules/contract-loads.md → ## Condition features`:

| Feature | Values | Source of the value |
|---|---|---|
| `task.flow` | `full`, `quick` | Task `state.md` top-of-file `flow:`; field absent → `full` (`rules/workflow-globals.md:130-132`) |
| `leaf.type` | `leaf`, `composite` | `T-XX/description.md → ## Context → type:`; absent → `leaf` |
| `leaf.atomic-tests` | the canonical `atomic-tests` vocabulary, plus `absent` | Leaf block in parent `state.md` |
| `leaf.atomic-execution` | the canonical `atomic-execution` vocabulary, plus `absent` | Same block |
| `invocation.mode` | `standalone`, `child` | `child` when a parent workflow in the same session invoked it; otherwise `standalone` (a fresh worker is `standalone`) |
| `run.orchestrator` | `none`, `pipeline`, `spec-run` | The running orchestrator, by 09's names |
| `flag.characterize` | `yes`, `no` | Whether `--characterize` was passed to `atomic-execution-tests` |

Anchored form in the rule, one line per feature, read by the engine at run time from
`rules/contract-loads.md` (finding `feature-registry-invalid` when a line is malformed, a
feature appears twice, or the file is absent):

```text
Condition feature task.flow: `full` | `quick`
Condition feature leaf.type: `leaf` | `composite`
Condition feature leaf.atomic-tests: status values for `atomic-tests` | `absent`
Condition feature leaf.atomic-execution: status values for atomic-execution / atomic-validation | `absent`
Condition feature invocation.mode: `standalone` | `child`
Condition feature run.orchestrator: `none` | `pipeline` | `spec-run`
Condition feature flag.characterize: `yes` | `no`
```

A value item is a backticked token, or `status values for <namespace>`, which the engine
replaces with the values of the canonical anchored vocabulary line of that namespace
(invariant 11, `.ai/principles/domain.md:65`). Vocabulary lines are found with the grammar
spec 19 also uses (`## Data Model → Anchored vocabulary lines`):
`^Status values for (?P<subject>.+?): (?P<values>`[a-z0-9-]+`( \| `[a-z0-9-]+`)*)` followed
by end of line, `.`, or text starting with `.` or ` —`; the namespace is the subject with
backticks removed; only lines inside the `## Canonical Status Formats` section of the
unique top-level rule containing that heading count (today `rules/workflow-globals.md:156`,
lines `:195` and `:197`). No such rule, several such rules, or zero or two lines for a
cited namespace inside that section is `vocabulary-anchor-invalid`. Adding a feature or
value is additive and keeps `schema_version: 1`; renaming or removing one requires schema
version 2.

### DM-3 Reference file

`rules/reference/<stem>.md`, `<stem>` = `[a-z0-9]+(-[a-z0-9]+)*`, unique case-insensitively,
no subdirectories. Front matter is exactly `description: <one non-empty line>`. Content:
rationale, optional worked examples and incident history only; no `**stop**`, no textual
load command, no `loads:`. Each reference file is cited by at least one top-level rule or
workflow (as `ref-<stem>`, by path, or in a `loads:` entry). Deployed name: `ref-<stem>`.

### DM-4 Measurement record (output of `measure`)

| Key | Type | Meaning |
|---|---|---|
| `schema_version` | int | `1` |
| `counter_version` | int | `1` (Contracts → Word and byte counting) |
| `workflow_id` | string | Stem of `workflows/<id>.md` |
| `source_revision` | string\|null | `git rev-parse --verify HEAD` of the root; null when not a git work tree or git is unavailable |
| `source_dirty` | bool\|null | True when `git status --porcelain --untracked-files=all -- rules workflows principles harness` is non-empty; null when revision is null |
| `deployed_manifest_digest` | string\|null | SHA-256 (lowercase hex) of the bytes of the file passed with `--deployed-manifest` (any one harness's deploy manifest of 09 DM-6, or spec 20's ownership manifest after it, from the same isolated deployment; it only binds the revision); null when not passed |
| `deployed_manifest_revision` | string\|null | The manifest's top-level `source_revision` (09 REQ-58, DM-6) or, for spec 20's ownership manifest, its `source.commit` (20 `### Ownership manifest`); null when not passed, not a JSON object, or the field is absent |
| `inputs_digest` | string | SHA-256 of the UTF-8 lines `<path>\t<sha256 of bytes>\n`, sorted by path, for every file this run read |
| `features` | object | Feature assignments supplied with `--feature`, by name |
| `complete` | bool | False when any finding concerns this workflow's graph or the always-on set |
| `findings` | array | DM-9 objects `{code, path, line, detail}` (`path` null only for root-level findings, `line` int or null), sorted by path, then line, then code, with null before any string or integer |
| `cycles` | array | Each a list of paths from the repeated node back to itself, in the order Contracts → Graph resolution step 4 finds them |
| `results` | array | One object per harness, sorted by `harness` |

Per-harness result: `harness` (string); `always_on_words`, `always_on_bytes`,
`mandatory_words`, `mandatory_bytes`, `selected_words`, `selected_bytes`,
`conditional_words`, `conditional_bytes`, `upper_bound_words`, `upper_bound_bytes` (int,
or null when `complete` is false); `files` — array sorted by path of
`{path, sha256, bytes, words, reasons}` for every file in the upper bound, where `bytes`
and `words` are whole-file values and `reasons` is a list of
`{kind, from, condition_id, backing_lines}` with `kind` ∈ `always-on`, `mandatory`,
`conditional-true`, `conditional-false`, `conditional-unknown`; `from` is the declaring
file (null for always-on membership); `backing_lines` lists the line numbers in `from`
holding a textual load command for this target (empty when none).

`conditional_* = upper_bound_* − mandatory_*`. No other keys exist; in particular no key
names tokens, cost, price or cache.

### DM-5 Comparison result (output of `compare`)

Top level: `schema_version` (1), `workflow_id`, `before` and `after` (each
`{source_revision, inputs_digest}`), `target_met` (true \| false \| "unknown": true only if
every harness is true; "unknown" if any harness is unknown; otherwise false), `results`
(per harness in the union of both records' harnesses, sorted: `harness`,
`before_mandatory_words`, `after_mandatory_words` (int, or null when that record lacks
the harness or has a null count), `ratio` (the exact string `"<after>/<before>"` when both
are integers and before > 0, else null), `target_met`, `reasons` (sorted list, empty when
true or false)).

Comparability conditions; each failure adds its reason and makes that harness "unknown":

| Reason | Condition that must hold |
|---|---|
| `schema-mismatch` | Equal `schema_version` |
| `counter-mismatch` | Equal `counter_version` |
| `workflow-mismatch` | Equal `workflow_id` |
| `harness-missing` | The harness appears in both records |
| `incomplete-record` | Both records have `complete: true` |
| `revision-missing` | Both `source_revision` non-null |
| `dirty-source` | Both `source_dirty` false |
| `manifest-missing` | Both `deployed_manifest_digest` non-null |
| `manifest-revision-mismatch` | In each record, `deployed_manifest_revision` equals `source_revision` |
| `baseline-zero` | `before_mandatory_words` > 0 |
| `baseline-edge-unbacked` | Every `mandatory` reason in the before record whose `from` is a workflow or top-level rule has non-empty `backing_lines` |

### DM-6 Obligation map

A JSON file (schema version 1) committed with the change:

```json
{"schema_version": 1, "baseline_revision": "<40 lowercase hex>", "rows": [
  {"id": "OBL-001", "kind": "prohibition", "statement": "<short quote>",
   "source": {"path": "rules/contract-tdd.md", "section": "## GREEN — what implementation may and may not do"},
   "disposition": "moved",
   "destination": {"path": "rules/contract-tdd-green.md", "section": "## Frozen test set"},
   "consumers": ["atomic-execution-implement"], "load_condition": "mandatory",
   "verification": "<validator check description or review>", "reason": null}]}
```

| Field | Rule |
|---|---|
| `id` | Unique, `OBL-` followed by at least three digits |
| `kind` | Obligation kinds `prohibition`, `stop`, `mandatory-action`, `vocabulary`; explanatory kinds `rationale`, `example`, `history` |
| `source` | Baseline path and section; `section` is a `## ` heading or `(preamble)` |
| `disposition` | `rewritten` (same place, new text), `moved`, `deduplicated` (destination is the surviving canonical copy), `removed` |
| `destination` | Required except for `removed`; path + heading path that exist in the delivered tree |
| `consumers` | Workflow ids that must reach the destination; may be empty only for `load_condition` `always` or `on-demand` |
| `load_condition` | `always`, `mandatory`, `on-demand` (explanatory kinds only), or a DM-2 condition string |
| `verification` | Validator check description, or `review` |
| `reason` | Required non-empty string for `removed` and `deduplicated`; otherwise null |

Rules: `removed` is allowed only for explanatory kinds; an obligation kind's destination is
never under `rules/reference/`; `baseline_revision` equals the before records'
`source_revision`. A baseline section is **changed** when the delivered tree has no file at
the same path, or that file has no section with the same heading path, or the section's
bytes differ; sections are each `## ` heading's extent plus `(preamble)`, the body text
before the first `## ` heading, excluding front matter. Baseline files considered:
`workflows/*.md`, top-level `rules/*.md`, `harness/*/always-on.md` and `principles/*.md` of
the `--baseline` directory (always-on files and principles also hold obligations).

**Reachability of an obligation row** (kinds `prohibition`, `stop`, `mandatory-action`,
`vocabulary`), evaluated on the delivered tree for every harness *h*. A destination is
*covered* by a set when that set contains the destination file with a merged region that
includes the whole extent of the destination heading (or the whole file when the
destination has no section).

| `load_condition` | Reachable when, for every harness |
|---|---|
| `always` | The always-on set of *h* covers the destination |
| `mandatory` | For every consumer *c*, the mandatory set of *c* covers it |
| condition string *C* | For every consumer *c*, the mandatory set of *c* covers it, or some conditional edge reachable from the always-on set of *h* or from *c* has a condition string byte-identical to *C* and its branch covers it |

Conditions are never evaluated for this check: an edge whose condition merely could be
true (unrelated feature, `!=`, conjunction with other comparisons) does not count unless its
string is identical. `on-demand` rows are not checked for reachability; their destination
must exist.

### DM-7 Evidence reference

Anchored line in `rules/contract-reports.md`:

```text
Evidence reference: EVIDENCE <path> | <scope> | sha256:<64 lowercase hex> | format:<name>@<version>
```

`<path>` has the form `<base>:<relative path>` with `<base>` either `work` — the task's
`WORK_DIR`, which every atomic workflow resolves and `/spec-run` passes to its workers
(`workflows/spec-run.md:238-239`) — or `task` — the parent task directory that holds
`state.md`, `plan.md` and `T-XX/description.md`, which lies outside `WORK_DIR` when
`working_dir:` is set (`rules/phase-atomic-execution.md:16-22`). The relative path is
POSIX, without `|`, `..` components or a leading `/`. Run-log files are not referenceable;
reports name them by path only. `<scope>` is `file` or a heading path (Contracts →
Section resolution); a heading containing ` | ` cannot be referenced. The hash covers the
scope's exact bytes (the whole file, or the section extent). Registered formats, anchored
line `Evidence formats: text@1`; `text@1` requires strict UTF-8 without NUL bytes. Neither
spec 13 nor spec 14 registers a format: 13's journal files are `text@1` files referenced as
`task:` paths with scope `file`, and 14's `OUTPUT` lines are not DM-7 references (Q-06).

Further anchored lines in `rules/contract-reports.md → ## Consuming reports`:

```text
Unverified evidence: a reference that fails verification is unavailable evidence, never a pass; reload the original or re-run the check.
Verify with: scripts/measure-context.sh evidence verify "<reference line>" --work <WORK_DIR> --task <task directory>
```

`evidence make` and `evidence verify` outcomes (`--work` and `--task` give the two bases; a reference whose base option is absent exits 2):

| Situation | `make` | `verify` |
|---|---|---|
| Scope exists, unambiguous, format valid (and hash equal, for verify) | Prints the line, exit 0 | Exit 0 |
| Hash differs | — | Exit 1 |
| File missing, section missing or ambiguous, invalid UTF-8, NUL byte | Exit 1 | Exit 1 |
| Base not `work` or `task`, or its option absent; path absolute, with `..`, resolving outside its base, or containing `|`; heading containing ` \| `; malformed line; hash not 64 lowercase hex; unregistered format | Exit 2 | Exit 2 |

The failing reason is printed on stderr as `<code>: <detail>`; stdout stays empty.

### DM-8 Report forms

Anchored lines in `rules/contract-reports.md`, one heading per form (`## RED report`,
`## GREEN report`, `## Check report`, `## Completion report`):

```text
Report fields — RED: Boundary | Task | Outcome | Mode | Test level | Acceptance criteria | Tests | Command | Expected | Observed | Test commit | Findings | Blockers | Decisions needed | Evidence | Next
Report fields — GREEN: Boundary | Task | Outcome | Changes | Frozen tests | Acceptance criteria | Checks | Uncovered criteria | Findings | Blockers | Decisions needed | Evidence | Next
Report fields — Check: Boundary | Task | Outcome | Scope | Inputs | Acceptance criteria | Checks | Verified obligations | Unverified obligations | Findings | Verdict | Blockers | Decisions needed | Evidence | Next
Report fields — Completion: Boundary | Task | Outcome | Last verified revision | Completed obligations | Remaining limitations | Branch | Pull request | Findings | Blockers | Decisions needed | Evidence | Next
Report values: none | unknown — <reason> | not applicable — <reason>
Never elide in a report: deltas, branch instructions, errors, acceptance evidence.
Delta block: a fenced code block with info string delta, complete and unabridged; reject one that is unterminated, has a line that is only ... or …, or contains [truncated] or [omitted].
```

| Boundary | Workflow | Field semantics beyond the obvious |
|---|---|---|
| RED | `atomic-execution-tests` | `Mode`: `ordinary`, `characterize` or `n-a`. `Tests`: test file paths and names (may reference the `tdd: red digest` line). `Expected`/`Observed`: failure class and observed failure per group; in `characterize`, Expected `pins pass on unchanged code`, Observed `<N> passing`; in `n-a`, `not applicable — <justification location>`. `Test commit`: a sha, `pending — created by the orchestrator`, or `not applicable — <reason>` |
| GREEN | `atomic-execution-implement` | `Changes`: every changed path with the SHA-256 of its current bytes, plus the revision when the role may read git, else `unknown — this role does not run git`. `Frozen tests`: `intact` or `amended` with each `tdd: test amended` record location |
| Check | `atomic-validation-check` | `Inputs`: description path and diff range or its provider. `Verdict`: `DONE` or `NEEDS WORK`. `Findings`: every critical and important finding, no count limit |
| Completion | `atomic-validation-close` | `Branch`/`Pull request`: the block's `branch:`/`pr:` values or `none` |

Rendering: one `<Field>: <value>` line per field in canonical order; list values as
indented `- ` lines under the field. A field is never omitted; there is no length or
item-count limit. The step-complete line required by `.ai/principles/coding.md` (workflow
shape item 7) precedes the form; `delta` blocks follow it; any run-log report marker stays
last, outside code fences, as `run-log` requires. Existing state writes, digest display and
`--batch` behaviour are unchanged. Each boundary workflow replaces its free-text report
instruction (`workflows/pae-tests.md:234-238`, `workflows/pae-implement.md:197`,
`workflows/pav-check.md:110`, `workflows/pav-close.md:70`) with a citation of its form
heading, `` `contract-reports → ## RED report` `` and so on (REQ-32).

Scope of the delta rule: every shared-file delta inside a report that contains a
`Boundary:` field line (one of the four forms) is a fenced `delta` block — this includes the
plan and composite deltas `atomic-validation-close` returns, also those produced by the
composite validation it triggers (`workflows/pav-close.md:53-62`, `rules/orchestration.md`
"Shared-file discipline"). `atomic-execution-implement` returns no shared-file delta. At
step 4.6 (`workflows/spec-run.md:312-313`) the orchestrator, which cites
`` `contract-reports → ## Consuming reports` `` and declares that section as a mandatory
load, applies the rejection rule to every delta received in a report that contains a
`Boundary:` field line. Deltas returned by `atomic-execution-finalize`,
`atomic-validation-propose` and composite validation are governed by spec 13: under
`/spec-run` the four workflows of 13 REQ-36 return their shared-file changes as fenced
`delta` blocks holding 13 DM-4 lines where an operation expresses the change and free text
otherwise, and the final response orders report forms
before `delta` blocks (13 REQ-50). On the helper route the helper composes them into the
checkpoint message (13 DM-3) and this rejection rule is applied first (a truncated block
yields 13's `delta-truncated`). On the manual route (13 REQ-08) the Orchestrator applies
every received `delta` block by hand, reading structured operations under 13 DM-5, and
applies this rejection rule to each block it receives, from any of those workflows.
Outside `/spec-run` there is no consumer and no rejection step.

### DM-9 Finding codes

| Code | Raised when |
|---|---|
| `loads-missing` | A workflow has no front matter or no `loads` key |
| `loads-not-cited` | A workflow body lacks `` `contract-loads → ## Runtime resolution` `` |
| `loads-not-allowed` | `loads` in a principle file (a reference file raises `reference-loads-forbidden`) |
| `schema-version-unsupported` | `schema_version` absent or not `1` |
| `yaml-subset-invalid` | Any construct outside the DM-1 subset (tabs, quotes, anchors, …) |
| `unknown-key` / `duplicate-key` / `required-key-missing` | Key outside DM-1 / repeated key in one mapping / required DM-1 key absent |
| `invalid-path` | Path text violates the DM-1 path rules, including any path outside `rules/<stem>.md`, `rules/reference/<stem>.md` and `principles/<stem>.md` (for example under `workflows/` or `harness/`) |
| `target-missing` | A path valid as text does not exist as a regular file |
| `symlink-escape` | A path valid as text is a symbolic link whose resolved target lies outside those three forms within the same root |
| `sections-empty` | `sections: []` |
| `section-missing` / `section-ambiguous` | Selector matches nothing / more than one location |
| `condition-invalid` | Condition violates the DM-2 grammar |
| `condition-feature-unknown` / `condition-value-unknown` | Feature or value outside the registry |
| `condition-id-duplicate` | Repeated `condition_id` in one declaration |
| `on-unknown-invalid` | `on_unknown` other than `load` |
| `cycle` | A load cycle, including a file that loads itself |
| `textual-load-undeclared` | REQ-12 |
| `always-on-load-unreachable` | REQ-29 |
| `always-on-rule-not-named` | REQ-31 |
| `report-form-not-cited` | REQ-32 |
| `feature-registry-invalid` | DM-2 registry lines absent, malformed or duplicated |
| `control-character` | A read file contains U+001C–U+001F (Word and byte counting) |
| `reference-stop-marker` / `reference-loads-forbidden` / `reference-load-command` / `reference-front-matter-invalid` | REQ-09 |
| `reference-name-invalid` | Reference stem violates DM-3, or two stems equal case-insensitively, or a file is nested under `rules/reference/` |
| `ref-skill-collision` | A workflow stem starts with `ref-` |
| `reference-orphan` | No top-level rule or workflow cites the reference file |
| `rule-unreachable` | A top-level rule with `load: on-demand` is in no workflow's upper bound and in no always-on set |
| `rule-load-mode-invalid` | A top-level rule lacks `load: always` or `load: on-demand` (the meter needs the mode; 09's checker `scripts/lint-instructions.py` reports the same defect in its own terms) |
| `rule-size-exceeded` / `always-on-size-exceeded` | REQ-01 |
| `harness-always-on-missing` | A harness directory (09 DM-5), or a non-hidden directory under `harness/` holding `capabilities.md`, has no `always-on.md` |
| `report-form-missing` | One of the four workflows lacks a mandatory `loads` entry for `rules/contract-reports.md` covering its form heading |
| `report-form-anchor-invalid` | A DM-8 or DM-7 anchored line is missing or differs from the text above |
| `loads-contract-anchor-invalid` | A line of `## Contracts & Interfaces → Runtime loading contract` is missing from `rules/contract-loads.md → ## Runtime resolution` or differs from it, or that rule is not `load: always` |
| `vocabulary-anchor-invalid` | DM-2: canonical file or a cited namespace line not found exactly once |
| `instruction-source-ambiguous` | A backtick name resolves to both a rule and a principle |
| `invalid-utf8` | A read file is not strict UTF-8 |
| `obligation-section-unmapped` | A changed baseline section has no row with that `source` |
| `obligation-destination-missing` | A row's destination path or heading does not exist in the delivered tree |
| `obligation-in-reference` | An obligation-kind row's destination is under `rules/reference/` |
| `obligation-removed` | An obligation-kind row has disposition `removed` |
| `obligation-unreachable` | DM-6 reachability fails for some consumer or harness |
| `map-invalid` | The map violates the DM-6 field rules (exit 2 when it is not JSON or `schema_version` is not 1; exit 1 for field-rule violations, all listed) |

Scope per subcommand: `check` evaluates every code except the `obligation-*` and
`map-invalid` codes over the whole root. `measure` raises only codes needed to compute its sets:
declaration, path, section, condition, cycle and encoding codes (`invalid-utf8`,
`control-character`) for files in the always-on set of the selected harnesses or the
workflow's upper bound, plus `rule-load-mode-invalid` and `harness-always-on-missing`
(they decide membership of the always-on set) and `feature-registry-invalid` /
`vocabulary-anchor-invalid` when a condition in that upper bound needs them. Every other
code is `check`-only, in particular `loads-not-cited`, `report-form-*`,
`loads-contract-anchor-invalid`, `always-on-rule-not-named`, `always-on-load-unreachable`,
`textual-load-undeclared`, the size codes, `reference-*`, `ref-skill-collision`,
`rule-unreachable` and `instruction-source-ambiguous`. `obligations` raises the DM-6
codes plus any declaration code that prevents computing a consumer's sets.

## Contracts & Interfaces

### Command line

```text
bash scripts/measure-context.sh check    [--root <dir>] [--format text|json]
bash scripts/measure-context.sh measure  --workflow <id> [--harness <name>]... [--feature <name>=<value>]...
                                         [--deployed-manifest <file>] [--root <dir>] [--format text|json]
bash scripts/measure-context.sh compare  --before <record.json> --after <record.json> [--format text|json]
bash scripts/measure-context.sh obligations --map <map.json> --baseline <dir> [--root <dir>] [--format text|json]
bash scripts/measure-context.sh evidence make   --path <base>:<path> [--section "<heading path>"] [--work <dir>] [--task <dir>]
bash scripts/measure-context.sh evidence verify "<reference line>" [--work <dir>] [--task <dir>]
```

- `--root` defaults to the parent of the directory holding the launcher (resolved with
  `pwd -P`); `ORCHESTRAIL_HOME` is not consulted, so a tree is never measured in place of
  another. Every caller in this repository passes `--root` explicitly. The resolved root is
  printed on stderr as `root: <path>` (never in JSON). It must contain `rules/`,
  `workflows/` and `harness/`. `--work` and `--task` have no default.
- `--format` defaults to `text` (human summary, not a contract); `json` is the contract
  (DM-4, DM-5, and `check`/`obligations` objects below).
- `--harness` limits results to named harnesses; default: every harness (Terminology),
  sorted. A repeated `--feature` name, or one outside the registry or with a value outside
  it, exits 2.
- `check` JSON: `{schema_version, counter_version, source_revision, inputs_digest, passed,
  findings, rules: [{path, load, words}], harnesses: [{harness, always_on_words}]}`.
- `obligations` JSON: `{schema_version, passed, rows_checked, changed_sections, findings}`.
- The launcher resolves its own directory (`script_dir="$(cd -- "$(dirname --
  "${BASH_SOURCE[0]}")" && pwd -P)"`, as `scripts/run-log-timing.sh` does), requires
  `python3` ≥ 3.11 and runs `python3 -I "$script_dir/measure-context.py" "$@"`. A missing
  or older Python exits 3 with a one-line message (unlike `run-log-timing.sh`, which exits 0,
  because this is a check, not non-blocking telemetry).

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Passed: no findings; record produced with `complete: true`; `target_met` true; reference made or verified |
| 1 | Findings or failed outcome: any DM-9 finding; `complete: false`; `target_met` false or "unknown"; the DM-7 exit-1 cases |
| 2 | Invalid invocation or input: unknown subcommand or option, missing required option, unknown workflow or harness, invalid `--feature`, root lacking required directories, record or map that is not JSON or has an unsupported `schema_version`, the DM-7 exit-2 cases |
| 3 | I/O error not covered above, or missing/unsupported Python |

A run with exit 1 still prints its complete output; diagnostics go to stderr. Spec 19's
generator exits 2 for declaration defects it meets while generating; the meter reports the
same defects as findings with exit 1 because finding them is its purpose; the difference is intentional (A-13).

### Graph resolution (`measure`, `check`, `obligations`)

1. Read every workflow, top-level rule, reference file, principle file and harness
   always-on/capabilities file once, recording its SHA-256; parse declarations.
2. Validate declarations, paths, sections and conditions (DM-1, DM-2, DM-9).
3. Build a directed graph: nodes are files; edges come from declarations (workflows and
   top-level rules only); each edge carries kind (mandatory/conditional), condition and
   section selection. Loading any part of a rule applies that rule's whole declaration.
4. Detect cycles by depth-first search with three node states (unvisited, on stack, done),
   starting from nodes in path order and following each node's edges in declaration order
   (mandatory entries, then conditional entries, each in listed order). An edge to an
   on-stack node is a cycle, reported as the stack path from that node back to itself;
   reaching a done node is not a cycle. Search continues after a cycle so every cycle
   reachable this way is reported once.
5. For each harness, the origin is the always-on set plus the workflow *w*. Compute the
   always-on set, the mandatory set, the selected set (conditions evaluated per DM-2
   against `--feature` values; features not supplied are unknown) and the upper bound, all
   from that origin; conditional edges of always-on rules therefore count in every
   workflow's selected set and upper bound.
6. Merge regions per file: any whole-file reach absorbs section reaches; otherwise the
   union of section byte ranges. Count words and bytes over merged regions.
7. A missing mandatory or conditional target, a cycle or any other `measure` finding sets
   `complete: false` and nulls every count.

Always-on composition: until spec 19 is delivered, the meter counts `harness/<h>/always-on.md`
(which then holds no embedded declaration) plus `harness/<h>/capabilities.md`; from spec 19's
delivery the generated `always-on.md` embeds the declaration once and the meter counts that
file alone, a change spec 19 makes to the meter (19 REQ-50). Either way the declaration is
counted once. The deploy-time additions of 09 DM-14 — the `<!-- Logging capabilities -->`
separator and the installation record — are machine-written, not instruction sources, and
are not counted.

### Section resolution

Headings are ATX lines (`#` to `######` followed by a space) outside fenced code blocks
(lines opening with three or more backticks or tildes, closed by a matching fence) and
outside front matter. Lines split on LF; a trailing CR is ignored for matching but counted
in bytes. A selector is a heading path in the cross-reference syntax of
`.ai/principles/coding.md:45-51`: one or more heading lines joined by ` → `, each matching a
heading line exactly after trailing whitespace is removed, each later one lying inside the
previous one's extent. A heading's extent runs from its line to the line before the next
heading of the same or a higher level, or to the end of the file.

### Word and byte counting

Counter version 1: decode strictly as UTF-8 and count `len(text.split())` (Python
`str.split()` without arguments) over the whole selected text, including front matter,
headings and code. A file containing any of U+001C–U+001F is rejected (`control-character`):
those four characters are the only ones `str.split()` treats as separators that are not
Unicode White_Space, so on every accepted file this count equals spec 09's definition and
spec 19's. Bytes are the raw byte length. Region boundaries are line boundaries, so counts
of disjoint regions add.

### Textual load command detection

Scan the body (after front matter, outside fenced code blocks) of workflows, top-level
rules, reference files and `harness/<h>/always-on.md`. A line is a textual load command
when its text outside backtick spans matches, case-insensitively,
`\b(load|loads|loaded|loading|read|reads|reading)\b`, and it contains at least one backtick
span resolving to an instruction source. Resolution of a span: drop any text from the
first ` → `; then `rule-<stem>` or a top-level rule stem → `rules/<stem>.md`; `ref-<stem>` →
`rules/reference/<stem>.md`; `principle-<stem>` or a principle stem → `principles/<stem>.md`;
a literal `rules/…md` or `principles/…md` path → itself; anything else (for example `.ai/`
project files) is not an instruction source. A span resolving to both a rule and a
principle raises `instruction-source-ambiguous`. Targets inside the always-on set of every
harness need no declaration (they are loaded already), so a line such as "Load the sources
declared in `loads:` per `contract-loads → ## Runtime resolution`." raises nothing. There is
no suppression marker; a false positive is resolved by declaring the target or rewording
the line.

### Runtime loading contract

`rules/contract-loads.md` (`load: always`, ≤ 700 words) holds `## Schema` (a concise
statement of DM-1), `## Condition features` (the DM-2 anchored lines) and `## Runtime
resolution`, which contains these lines verbatim:

```text
Runtime resolution: load every mandatory entry before the Guard; after the Guard, evaluate each conditional entry and load it when its condition is true or unknown; apply the same to the declaration of every loaded rule.
Unknown condition: load the target.
Name resolution: rules/<stem>.md is rule-<stem>, rules/reference/<stem>.md is ref-<stem>, principles/<stem>.md is principle-<stem>.
Missing or unreadable declaration: load in full every load: always rule, the bootstrap rule of the workflow's phase when one exists, and every rule, reference and principle named anywhere in the workflow body, then report "loads: fallback-full — <reason>".
Unavailable mandatory target: **stop**: "Required instruction <name> is unavailable. Deploy with scripts/sync.sh and re-run."
Standalone or fresh worker: load the complete mandatory closure yourself; a parent's report or receipt is not loaded content.
Child in the same session: reuse an already loaded source only while its content is in context and unchanged.
Load report: after resolution, report "Loaded: <names>; conditions: <condition_id>=true|false|unknown".
```

Every workflow cites `` `contract-loads → ## Runtime resolution` ``. Hand-written lists
of instruction sources to load are replaced by that citation; workflow steps keep citing
the sections they apply (`.ai/principles/coding.md` "Cross-references"), and those cited
names are what fallback-full loads. Utility and entry workflows without a phase bootstrap
rule (for example `spec-draft`, `retro`) load no bootstrap rule in fallback-full.
Project-context bootstrap (which `.ai/` files a phase reads) is unchanged and remains owned
by the bootstrap rules and spec 12. `harness/<h>/always-on.md` names every `load: always`
rule in a textual load command (REQ-31).

### Deployment

Through spec 09's deployment mechanism (`deploy.env` `skills_dir`, deploy manifest, 09 DM-6),
every `rules/reference/<stem>.md` is copied byte-for-byte to `<skills_dir>/ref-<stem>/SKILL.md`
for each supported harness and recorded as owned. Reference files never produce a
`rule-*` skill. Rename and removal rely on 09's ownership rules (09 REQ-10, REQ-42): an
owned, unmodified `ref-*` object whose source disappeared is removed; a modified or
foreign one is preserved and reported. Per-project skill links follow 09's project pass.

Deployment gate (REQ-08): after the contract-validation step (`scripts/sync.sh:40-45`) and
spec 09's runtime guard (09 `scripts/sync.sh` step 3, REQ-56), and before hook installation
(`:51-56`) and every copy step — with spec 19 delivered the order is validator, runtime
guard, `gen-docs.py --check`, then this gate — sync runs
`bash "$ROOT/scripts/measure-context.sh" check --root "$ROOT"`; on a non-zero exit it
prints `ERROR: context tiering check failed (exit <code>); see the diagnostics above` and
exits 1. The gate never runs the acceptance suite.

### Acceptance suite

`python3 -I scripts/check-context-tiering.py` is a standard-library Python 3.11+ `unittest`
program holding every fixture-based acceptance case, including AC-05(b) and AC-07. It
builds each fixture root in a temporary directory with an isolated `HOME` (here and below:
`HOME`, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` set to temporary paths, 09 REQ-47), copies
`scripts/measure-context.sh` and `scripts/measure-context.py` into fixture roots that need
them, runs the launcher as a subprocess with `--root`, never runs
`scripts/validate-contracts.sh` (the sync cases replace it in their private copy with
`#!/bin/bash\nexit 0\n`, as `tests/hook-install.sh:135-138` does) and never touches the real
home. A nested sync in a fixture runs only the meter's `check` gate, so the suite is never
re-entered. Exit 0 when every case passes, 1 otherwise. The suite lives in `scripts/`,
outside the frozen validator inventory and the `tests/` source guard, as the `/spec-draft`
check (ADR-0019 Decision 3) and spec 19's `scripts/check-gen-docs.py` do; it is not
registered in `scripts/validate-contracts.sh`. `.ai/context/runbook.md` lists the command;
`scripts/README.md` lists it.

### Existing validator checks

Splitting rules moves text that existing checks read: 139 lines of
`scripts/validate-contracts.sh` and `tests/workflow-instructions.py:38-54` name `rules/`
files. Each affected check keeps its description and its asserted pattern; only the file
paths it reads change, to the file that now holds the text. No check is deleted, skipped
or weakened.

The inventory oracle pins check expressions, helper bodies and non-standard check lines,
and resource rows for the `tests/` files a check references (Context fact 6). Spec 09 owns
the mechanism that admits changed expressions: the schema-2 inventory amendment (09 DM-9,
REQ-51, REQ-52) with its `path_changes` and `contract_changes` lists, the class-indexed
mask, the oracle application, `APPROVED_PATHS`, `AMENDMENT_SHA256` and the source-guard
refresh. This spec defines no amendment schema of its own. Division of work:

- **11 supplies** the path map of its own re-pointing: one `path_changes` entry per frozen
  expression, helper body or non-standard line whose read path this change moves (a new
  entry, or an updated `after` of 09's `path_changes` entry for the same `(target, key)`;
  text read by a check that 09 recorded under `contract_changes` stays in place unless the
  mask constraint below admits the move), and the
  `resources` changes and `paths`/`APPROVED_PATHS` additions for each `tests/` file it edits
  (at least `tests/workflow-instructions.py`, `:38-54`).
- **09 keeps** the schema, the mask, the validation and application rules and the pins; 11
  re-pins `AMENDMENT_SHA256` and refreshes the source guard by 09's procedure after adding
  its entries.
- **Mask constraint.** 09's mask maps every path of a name-map class (09 DM-1, DM-9) to that
  class's token. Frozen-checked text may move from a mapped rule into a new split target only
  as 09 REQ-68 prescribes: the same delivery appends the target's stem to that rule's `new`
  list in `docs/name-map.json`, updates `docs/USAGE.md → ## Renamed commands and rules`,
  records the re-pointing as `path_changes` entries and refreshes `name_map_sha256`. Any other
  move of frozen-checked text must satisfy 09's mask (another path of the same class, or between
  two unmapped paths); otherwise the text stays in place. Text asserted by checks of two
  different rows cannot move into one new file; where that makes a required split impossible
  within the 700-word limit, the implementer stops (Contracts → Rules and workflows created
  after this spec) and the change returns to spec 09 through `/spec-sync`.

### Rules and workflows created after this spec

- **Naming and placement.** Files created by this spec or a later one (12–18) follow 09
  Notes "Files and sections created after this spec", with no name-map row (except a split
  target of a mapped rule, 09 REQ-68): a rule is
  `rules/<kind>-<subject>.md` with a DM-2 kind and DM-2 front matter, `load` chosen by its
  author (default `on-demand`); a workflow uses the DM-11 pattern (`<phase>-<step-name>`, or
  a name without an old prefix) with DM-3 front matter. The meter needs no special case: such a file is a top-level
  rule or workflow like any other.
- **Checks.** `check` applies to it in full: the 700-word limit (REQ-01), a `loads:`
  declaration for a workflow (REQ-03), textual-load declarations (REQ-12), reachability
  (REQ-19), and, for a `load: always` rule, membership of the always-on set, its 6,000-word
  budget and REQ-31's naming line.
- **Baseline.** The before records are fixed at the baseline revision (REQ-28) and are never
  regenerated to include a later rule. A rule this spec creates after the baseline revision
  (for example `contract-reports` or a split target) counts only in the after records;
  `contract-loads` counts in both (Terminology → Baseline revision). AC-03 is judged once,
  at this spec's delivered revision. Mandatory words that later specs add (for example 14's
  sections of `contract-output` in the atomic workflows) do not reopen AC-03; those specs
  record their own `measure` results.
- **Over a limit.** IF an edit required by any spec would push a top-level rule over 700
  words or a harness's always-on set over 6,000, `check` reports it and the deployment gate
  refuses to deploy (REQ-08). The implementer never drops an obligation, moves it to a
  reference file or paraphrases it away to fit. For a rule this spec owns, splitting it into
  further on-demand `<kind>-<subject>` rules with updated declarations and obligation-map
  rows is the remedy. For a rule whose words another spec fixes (for example 14's
  `contract-output`, 14 REQ-47, REQ-48), the implementer stops and the change returns to the
  owning spec through `/spec-sync`. This is the same rule 14 states and agrees with REQ-28's
  owner hand-off for an unmet target.

### Files created or changed by the implementation

New: `scripts/measure-context.sh`, `scripts/measure-context.py`,
`scripts/check-context-tiering.py`,
`rules/contract-loads.md`, `rules/contract-reports.md`, `rules/reference/*.md`, any further
top-level rules produced by splitting (named per 09's `<kind>-<subject>` scheme), and under
`docs/analysis/`: `YYYY-MM-DD-context-tiering-<workflow>-before.json`, `…-after.json` (two
workflows), `YYYY-MM-DD-context-tiering-obligations.json` (JSON evidence beside the dated
Markdown naming rule of `.ai/principles/coding.md:71-92`, which names `.md` analyses only)
and `YYYY-MM-DD-context-tiering-measurement.md` (summary, word counts only, 08 proposals
and findings with owner 11 implemented or declined), indexed in `docs/README.md`.
Changed: every `workflows/*.md` (declaration and citation), `harness/<h>/always-on.md` (the
line naming `load: always` rules), the rules being split, the four report sections,
`workflows/spec-run.md` (step 4.6 citation), `scripts/sync.sh` (gate), `docs/name-map.json` and
the `docs/USAGE.md → ## Renamed commands and rules` rows when a split target receives moved
checked text (09 REQ-68), `scripts/deploy-skills.py` (`ref-<stem>`, 09 DM-15) and its suite
`scripts/check-deploy-skills.py` where its cases change, existing validator check expressions, `tests/fixtures/validator-runtime/inventory-amendment.json`,
`AMENDMENT_SHA256` in `tests/validator-runtime-oracle.py` (09 DM-9 pin), the source-guard records, `tests/workflow-instructions.py`, 09's checker `scripts/lint-instructions.py` (REQ-22),
`scripts/README.md`, `docs/USAGE.md` (command reference), `.ai/principles/domain.md`,
`.ai/memory/architecture.md`,
`.ai/context/runbook.md`, `.ai/adr/<NNNN>-*.md`, `.ai/adr/index.md`.

## Non-Functional Requirements

| Attribute | Target or standard | Verification |
|---|---|---|
| Determinism | Byte-identical stdout for byte-identical inputs and arguments; no timestamps, absolute paths or random identifiers in JSON | AC-17: two runs compared byte for byte |
| Read-only | No file created, modified or deleted under `--root`, `--base` or elsewhere; git reads run with `GIT_OPTIONAL_LOCKS=0` | AC-17: tree bytes, modes and mtimes and `.git/index` unchanged |
| Offline | No network and no model use; the engine imports only standard-library modules outside `socket`, `ssl`, `http`, `urllib`, `ftplib`, `smtplib`, `subprocess` (except for the two git reads) | AC-17: import scan |
| Input safety | Declarations, maps, records and references are data: no `eval`, `exec`, `yaml.load` or shell interpolation | AC-17 import and call scan (`eval`, `exec`, `yaml` absent); AC-02 malformed inputs |
| Runtime | No numeric target: no measured basis exists, and the full validator already takes 34–52 min (`.ai/context/runbook.md:26`); actual duration of `check` is recorded in the measurement summary | Recorded, not gated |
| Size limits | REQ-01 limits; 09's 300/1,200 limits untouched | AC-01, AC-08; 09's checks |
| Shared gates G1–G8 (`.ai/specs/README.md`) | G1/G2/G8: word and byte counts only, no token, cost or saving claim; G3: test-first order, frozen RED, stops and independent validation preserved (obligation map); G4: workflows without declarations fall back to full loading; G5: meter read-only, no new writer of shared state; G6: failing fixtures before implementation, no paid run; G7: rollback in `## Notes` | AC-03, AC-05, AC-06, AC-15, AC-17 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| Workflow without front matter or `loads` | `loads-missing`; runtime agent uses fallback-full | REQ-03, REQ-14 |
| `mandatory: []` and no `conditional` | Valid; mandatory set is always-on set plus the workflow | REQ-20 |
| `sections: []` | `sections-empty` | REQ-20 |
| Unknown `schema_version`, key, operator or feature | Finding, never treated as a false condition | REQ-20 |
| Feature supplied with a value outside the registry | Exit 2 | REQ-04 |
| Feature not supplied | Conditions using it are unknown; branch selected with `conditional-unknown` | REQ-10 |
| `a == x and b == y` with `a` true, `b` unknown | Unknown → selected | REQ-10 |
| Same file loaded whole and by section | Counted once, whole | REQ-04 |
| Overlapping sections (`## A` and `## A → ### B`) | Union of ranges, counted once | REQ-04 |
| Same file reached from two workflows' rules (diamond) | Not a cycle; counted once | REQ-11 |
| A rule that loads itself | `cycle` with path `[r, r]` | REQ-11 |
| Heading text inside a fenced code block | Not a heading | REQ-18 |
| Duplicate heading in a file, selected | `section-ambiguous`; not selected → no finding | REQ-18 |
| Renamed heading still referenced | `section-missing`; never matched to the nearest heading | REQ-18 |
| CRLF file | Headings match; bytes include CR | REQ-18 |
| Symlink resolving inside the allowed directories | Treated as its resolved file, deduplicated by resolved path | REQ-20 |
| Symlink resolving outside them | `symlink-escape` | REQ-20 |
| Invalid UTF-8 in any read file | `invalid-utf8`; `complete: false` | REQ-27 |
| File containing U+001C–U+001F | `control-character`; `complete: false` | REQ-27 |
| Root is not a git work tree, or git missing | `source_revision` and `source_dirty` null; `compare` reports `revision-missing` | REQ-23 |
| Uncommitted changes in measured directories | `source_dirty: true`; `compare` reports `dirty-source` | REQ-23 |
| Baseline record without deployed manifest digest | `compare` "unknown" (`manifest-missing`) | REQ-23 |
| Manifest from another revision passed to `measure` | `compare` "unknown" (`manifest-revision-mismatch`) | REQ-23 |
| A record lacks a harness or has null counts | That harness appears with null words and null `ratio`, `target_met: "unknown"` | REQ-23 |
| Baseline mandatory edge not backed by a textual command (inflated baseline) | `compare` "unknown" (`baseline-edge-unbacked`) | REQ-23 |
| 50% not reached | `target_met: false`; AC-03 unmet; owner decides; no re-baseline | REQ-28 |
| Baseline records found invalid after later instruction changes | Regenerate them from the same baseline revision (output is deterministic); never choose another revision | REQ-28 |
| Word count down but more loads or cache writes observed by 05 | Both facts reported under 05; no saving claimed here | REQ-04 |
| Obligation section changed but unmapped | `obligation-section-unmapped` | REQ-13 |
| Prohibition moved to a reference file | `obligation-in-reference` | REQ-13 |
| Conditional obligation reachable only under a different condition | `obligation-unreachable` | REQ-13 |
| Mandatory target missing at runtime (skill not deployed) | **stop** with the contract message | REQ-14 |
| Declaration unreadable at runtime | Fallback-full and report the reason | REQ-14 |
| Fallback-full in a utility workflow without a phase bootstrap rule | Loads the always rules and every source the body names; no bootstrap rule | REQ-14 |
| `ORCHESTRAIL_HOME` points to another checkout | Ignored by the meter; callers pass `--root`; stderr names the root used | REQ-08 |
| `load: always` rule not named by a harness's `always-on.md` | `always-on-rule-not-named` | REQ-31 |
| Citation of `contract-loads` or another always-on source on a line with "load" | Not a textual-load finding (target in every always-on set) | REQ-12 |
| Standalone child with a parent receipt but no content | Loads full mandatory closure | REQ-15 |
| Evidence file changed after reference made | `verify` exit 1; evidence treated as unavailable; consumer reloads or re-runs | REQ-16, REQ-24 |
| Evidence scope binary or with NUL bytes | `make` and `verify` exit 1 for `text@1` | REQ-16, REQ-30 |
| Reference path with `..`, absolute, outside `--base`, or with `|`; heading containing ` \| ` | `make` and `verify` exit 2 | REQ-16, REQ-30 |
| Orchestrator verifies a worker's reference | Passes the same `WORK_DIR` and task directory as `--work`/`--task` | REQ-24 |
| Evidence in the task directory while `working_dir:` points elsewhere | Referenced with base `task` | REQ-16 |
| Truncated or elided `delta` block | Consumer rejects it | REQ-24 |
| Very long findings list or delta | Rendered in full; no length limit | REQ-06, REQ-07 |
| `n-a` test level | RED form fields `Expected`/`Observed`/`Test commit` read `not applicable — …`; no invented RED or commit | REQ-06 |
| Characterization (`pinned`) | `Mode: characterize`; Observed shows passing pins, never "failure" | REQ-06 |
| Legacy block without `atomic-tests` | `Mode` and test fields read `not applicable — pre-TDD task`; no retroactive RED | REQ-06 |
| Reference file removed while a user modified its deployed copy | 09's ownership preserves and reports it | REQ-02 |
| Two reference stems differing only in case | `reference-name-invalid` | REQ-19 |
| Concurrent edits during a meter run | Each file is read once; the record is consistent with the hashed bytes; no locking needed because the meter never writes | REQ-17 |
| A required edit would push a rule another spec fixes word for word (14's `contract-output`) over 700 words | Stop; return to the owning spec through `/spec-sync`; nothing is dropped | REQ-01, REQ-28 |
| Text a frozen check asserts would move from a 09 name-map class path to a new file | Allowed only through 09 REQ-68 (split target appended to the row's `new` list); text of two rows into one file: stop | REQ-25 |
| Rule created after the baseline revision | Counted only in after records; `check` applies in full | REQ-01, REQ-28 |
| Spec 09 or 10 not delivered when implementation starts | Implementation stops at its Guard (see `## Notes`, A-28) | REQ-05, REQ-26 |
| A frozen validator check reads text that moved | Its file path is re-pointed; description and pattern unchanged | REQ-25 |

## Acceptance Criteria

Fixture-based criteria (all except AC-03, AC-05(a,c–e), AC-08, AC-15, AC-20, AC-23, which inspect the delivered tree) run inside `scripts/check-context-tiering.py` on disposable source
roots; each criterion's cases are written and observed failing before the engine code they
exercise exists.

**Minimal valid root (MVR).** `harness/claude/deploy.env` (09 DM-5 delivered values), `harness/claude/capabilities.md` (one line);
`harness/claude/always-on.md` containing the line "Load `contract-loads` at session start.";
`rules/contract-loads.md` (`description`, `load: always`; `## Schema`, `## Condition
features` with the seven DM-2 lines, `## Runtime resolution` with the eight contract lines);
`rules/contract-phases.md` (`load: on-demand`; `## Canonical Status Formats` with the two
status vocabulary lines copied from `rules/workflow-globals.md:195,197`);
`rules/contract-reports.md` (`load: on-demand`; the four form headings, `## Consuming
reports`, and every DM-7/DM-8 anchored line); workflows `atomic-execution-tests`,
`atomic-execution-implement`, `atomic-validation-check`, `atomic-validation-close` and
`spec-run`, each with a valid `loads:` holding a mandatory entry for its
`rules/contract-reports.md` section (the tests workflow also loads
`rules/contract-phases.md`), the `contract-loads → ## Runtime resolution` citation and,
for the four, its form citation (`spec-run`: the `## Consuming reports` citation). Each
fixture below is the MVR plus the stated change.

- **AC-01** (REQ-01). Given the MVR plus `load: always` rules (each named in
  `always-on.md`) sized so that the `claude` always-on set totals exactly 6,000 words, and
  two on-demand rules of 700 and 701 words loaded by `spec-run`, when `check --format json`
  runs, then it exits 1 and `findings` is exactly one `rule-size-exceeded` for the 701-word
  file; and with one word added to a `load: always` rule, `findings` additionally holds
  exactly one `always-on-size-exceeded` for `claude`.
- **AC-02** (REQ-03, REQ-20). Given one fixture per defect in one workflow's declaration or
  body — no front matter (`loads-missing`), no `loads` (`loads-missing`), `schema_version: 2`
  (`schema-version-unsupported`), unknown key (`unknown-key`), duplicate key
  (`duplicate-key`), conditional entry without `on_unknown` (`required-key-missing`), tab
  indentation and single-quoted scalar (`yaml-subset-invalid`), absolute path, `..` path and
  a path under `workflows/` (`invalid-path`), missing target (`target-missing`), symlink
  resolving under `workflows/` (`symlink-escape`), `sections: []` (`sections-empty`),
  operator `>` (`condition-invalid`), unknown feature (`condition-feature-unknown`), value
  outside the registry (`condition-value-unknown`), duplicate `condition_id`
  (`condition-id-duplicate`), `on_unknown: skip` (`on-unknown-invalid`), body without the
  citation (`loads-not-cited`) — when `check` runs on each, then each exits 1 with exactly
  the code in parentheses; and the MVR itself, which also carries 09's `description`,
  `phase` and `step` keys around the `loads` block, exits 0 with no finding.
- **AC-03** (REQ-05). Given the committed before records (baseline revision, each with a
  manifest from an isolated deployment of that revision) and after records (delivered
  revision) for `atomic-execution-tests` and `atomic-execution-implement`, and the committed
  obligation map, when `compare` runs for each workflow and `obligations` runs against an
  export of the baseline revision, then both `compare` runs exit 0 with `target_met: true`
  for every harness and `obligations` exits 0.
- **AC-04** (REQ-06, REQ-07, REQ-24). Given the delivered tree, when `check` runs, then
  `rules/contract-reports.md` contains every DM-7 and DM-8 anchored line verbatim
  (including the two `## Consuming reports` lines), and each of the four boundary
  workflows has a mandatory `loads` entry covering its form heading; and given an MVR whose
  "Unverified evidence" line differs by one word, or whose `atomic-validation-check` lacks
  that entry, `check` exits 1 with `report-form-anchor-invalid` or `report-form-missing`
  respectively.
- **AC-05** (REQ-08, REQ-25, REQ-26). Given the delivered tree, then (a)
  `bash scripts/measure-context.sh check --root "$(pwd)"` and
  `python3 -I scripts/check-context-tiering.py` exit 0; (b) in the suite, in a copy of the tree
  where `rules/contract-loads.md` loses one runtime line and `scripts/validate-contracts.sh`
  is replaced by `exit 0`, `HOME=<tmp> XDG_CONFIG_HOME=<tmp>/config XDG_STATE_HOME=<tmp>/state bash scripts/sync.sh --from <copy>` exits 1 before
  creating any file under `<tmp>`; (c) every `check` description of the baseline
  revision's validator is present in the delivered one, and for each, the expression is
  identical or is covered by a `path_changes` entry of 09 DM-9 that this change supplied or
  updated, and the inventory oracle tests (`tests/validator-runtime-oracle.py`) pass with
  those entries and with the resource change for `tests/workflow-instructions.py` in both
  `paths` and `APPROVED_PATHS`; (d) the default `bash scripts/validate-contracts.sh` exits 0;
  (e) `python3 -I tests/golden-runs.py` exits 0 with unchanged expected results.
- **AC-06** (REQ-13). Given a baseline tree and a delivered tree whose differences are five
  changed sections, when `obligations` runs with maps that each break one rule — (a) no row
  for one changed section, (b) a `prohibition` row with its destination under
  `rules/reference/`, (c) a `stop` row whose destination is outside its consumer's
  mandatory set, (d) a `mandatory-action` row with disposition `removed`, (e) a row with
  `load_condition: "leaf.type == composite"` whose destination is reached only through an
  edge with condition `leaf.type != leaf`, (f) a `mandatory` row whose consumer loads only
  a different section of the destination file, (g) a destination heading that does not
  exist — then the codes are `obligation-section-unmapped`, `obligation-in-reference`,
  `obligation-unreachable`, `obligation-removed`, `obligation-unreachable`,
  `obligation-unreachable` and `obligation-destination-missing` respectively, each with
  exit 1; a map that is not JSON exits 2; a complete valid map (including a conditional row
  reached through an edge whose condition string is identical) exits 0.
- **AC-07** (REQ-02). Given, in the suite, a copy of the delivered tree plus
  `rules/reference/alpha.md` cited by one workflow (so `check` passes), with
  `scripts/validate-contracts.sh` replaced as in AC-05(b), and an isolated deployment target
  built with spec 09's isolated deployment fixtures, when deployment
  runs, then `ref-alpha/SKILL.md` exists under both harnesses' skills directories with bytes
  equal to the source, no `rule-reference` or `rule-alpha` skill exists, and the install
  manifest lists both objects as owned; when `alpha.md` is deleted and deployment re-runs,
  then the unmodified copies are removed; and when instead one deployed copy was edited
  first, then that copy is preserved and reported.
- **AC-08** (REQ-01, REQ-03, REQ-12, REQ-19, REQ-29, REQ-31, REQ-32). Given the delivered
  tree, when `check --root "$(pwd)" --format json` runs, then it exits 0 with
  `passed: true`, every top-level rule has at most 700 words and each harness's always-on
  set has at most 6,000 words.
- **AC-09** (REQ-04). Given the MVR plus: a `load: always` rule `x` named in `always-on.md`;
  workflow `w` (30 words) declaring mandatory rule `a` (40 words, whole), mandatory rule
  `b` with selectors `"## X"` (an extent of 15 of `b`'s 50 words) and `"## X → ### Y"`
  (inside it), a second mandatory entry for `a`, and a conditional entry for reference `c`
  (25 words) with condition `leaf.type == composite`; and with A0 the word count of this
  fixture's `claude` always-on set, hard-coded in the test from the fixture text — when
  `measure --workflow w --harness claude --format json` runs, then `always_on_words` is A0,
  `mandatory_words` A0 + 85, `upper_bound_words` A0 + 110 and `conditional_words` 25;
  `selected_words` is A0 + 85 with `--feature leaf.type=leaf`, A0 + 110 with
  `--feature leaf.type=composite`, and A0 + 110 without the feature, with a
  `conditional-unknown` reason on `c`; byte counts equal the byte lengths computed by the
  test from the same regions; the top-level and per-harness key sets equal DM-4 exactly;
  and `--feature leaf.type=leaf --feature leaf.type=leaf` exits 2.
- **AC-10** (REQ-23). Given a valid before record with `mandatory_words` 1000, when
  `compare` runs against after records with 500 and with 501, then the results are
  `target_met: true` with ratio `"500/1000"` (exit 0) and `false` (exit 1); and for each
  DM-5 condition broken in turn (null manifest digest, manifest revision ≠ source revision,
  `source_dirty: true`, before value 0, different `counter_version`, an unbacked mandatory
  edge in the before record, a harness present in only one record, `complete: false`) the
  harness result is `"unknown"` with exactly the matching reason, null `ratio` where DM-5
  says so, and exit 1; a record that is not JSON exits 2.
- **AC-11** (REQ-09). Given MVR fixtures with a reference file (cited by `spec-run`)
  containing, one each, `**stop**`, a `loads:` key, the line "Load the `contract-phases`
  rule.", and front matter with a second key, when `check` runs, then each exits 1 with
  `reference-stop-marker`, `reference-loads-forbidden`, `reference-load-command` and
  `reference-front-matter-invalid` respectively.
- **AC-12** (REQ-10). Given an MVR workflow with a conditional entry
  `task.flow == full and leaf.type == composite`, when `measure` runs with
  `--feature task.flow=full` only, then the branch is selected with reason
  `conditional-unknown`; with `--feature task.flow=quick` it is not selected and has reason
  `conditional-false`; and the MVR's `rules/contract-loads.md` contains the line
  `Unknown condition: load the target.` (AC-15 fails otherwise).
- **AC-13** (REQ-11). Given MVR fixtures where workflow `w` mandatorily loads rule `a`,
  `a` loads `b` and `b` loads `a`; where `w` loads rule `r` and `r` loads itself; and a diamond `w` → `a`,
  `w` → `b`, `a` → `c`, `b` → `c`, when `measure --workflow w` runs, then the first two exit 1
  with `complete: false`, every count null and `cycles` equal to
  `[["rules/a.md","rules/b.md","rules/a.md"]]` and `[["rules/r.md","rules/r.md"]]`, and the
  diamond exits 0 with `c` counted once.
- **AC-14** (REQ-12). Given MVR fixtures where a workflow line reads "Load the
  `contract-phases` rule." without declaring it, and a rule line reads "Read `ref-y` for
  examples." without declaring it, when `check` runs, then it reports
  `textual-load-undeclared` with the correct file and line for both; and declaring the
  targets, a line "Read `T-XX/description.md`", the same load line inside a fenced code
  block, and the citation line "Load the sources in `loads:` per `contract-loads → ##
  Runtime resolution`." produce no finding.
- **AC-15** (REQ-14, REQ-15). Given the delivered tree, when `check` runs, then
  `rules/contract-loads.md` has `load: always` and its `## Runtime resolution` section
  contains every line of `## Contracts & Interfaces → Runtime loading contract` verbatim;
  and given an MVR in which one of those lines differs by one word, `check` exits 1 with
  `loads-contract-anchor-invalid`.
- **AC-16** (REQ-16, REQ-30). Given separate fixture `--work` and `--task` directories (the
  task directory outside the work directory, as with `working_dir:`), each with a file
  holding sections, when `evidence make` runs for a whole file under `work:` and for one
  section under `task:`, then each prints one DM-7 line and exits 0, and `evidence verify`
  of each line exits 0; a `task:` reference verified without `--task` exits 2; after one byte of the
  section changes, verify exits 1; `make` and `verify` exit 1 for a missing file, a missing
  section, a duplicated section and a file containing a NUL byte; and they exit 2 for a path
  containing `..`, an absolute path, a hash of 63 hex digits and the format `bin@1`, with
  empty stdout in every non-zero case.
- **AC-17** (REQ-17). Given an MVR that is a git work tree, when each subcommand runs twice
  with identical arguments, then both stdout byte streams are identical; the fixture's file
  bytes, modes and modification times and `.git/index` are unchanged after every run; and a
  scan of `scripts/measure-context.py` finds no import of `socket`, `ssl`, `http`, `urllib`,
  `ftplib`, `smtplib` or `yaml`, no call of `eval` or `exec`, and `subprocess` used only for
  `git rev-parse` and `git status` with `GIT_OPTIONAL_LOCKS=0`.
- **AC-18** (REQ-18). Given a file with headings `## A`, `### B` (inside `## A`), `## C`, a
  line `## A` inside a fenced code block, two separate `## D` headings, and CRLF line endings,
  when `measure` resolves the selectors `"## A"`, `"## A → ### B"`, `"## D"` and `"## E"`,
  then `## A`'s extent ends before `## C` and ignores the fenced line, `## A → ### B`
  resolves inside it, `## D` yields `section-ambiguous`, and `## E` yields `section-missing`.
- **AC-19** (REQ-19). Given MVR fixtures with `rules/reference/Alpha_1.md`, the pair
  `rules/reference/beta.md` and `rules/reference/Beta.md`, a nested
  `rules/reference/sub/x.md`, a workflow `ref-tool.md`, a reference cited nowhere, and a
  `load: on-demand` rule outside every upper bound, when `check` runs, then it reports
  `reference-name-invalid` for each of the first three, `ref-skill-collision`,
  `reference-orphan` and `rule-unreachable` respectively.
- **AC-20** (REQ-21). Given the delivered tree, then `.ai/principles/domain.md` has a
  vocabulary row for each of "Always-on set", "Load declaration", "Reference file",
  "Obligation map", "Evidence reference" and "Report form"; `.ai/context/runbook.md` names
  `scripts/check-context-tiering.py` and `scripts/measure-context.sh`;
  `.ai/memory/architecture.md` describes `rules/reference/` and the meter;
  `scripts/README.md` has rows for the three new scripts; and `.ai/adr/index.md` lists an
  Accepted ADR for the load declaration, the reference tier and the report forms.
- **AC-21** (REQ-22). Given a top-level rule with `description`, `load` and a valid `loads`,
  when spec 09's checker `scripts/lint-instructions.py` runs, then it accepts the rule without `metadata-unknown-field`, and a copy whose `loads` has `schema_version: 2` makes the checker exit 1 with finding `metadata-invalid-value` (09 REQ-30); and given a principle file
  with `loads`, `check` reports `loads-not-allowed`.
- **AC-22** (REQ-27). Given MVR fixtures with, one each: `harness/codex/capabilities.md`
  without `always-on.md`; a rule without `load:`; a span `` `code-quality` `` where both
  `rules/code-quality.md` and `principles/code-quality.md` exist; a workflow with an
  invalid UTF-8 byte; a workflow containing U+001D; `rules/contract-phases.md` without the
  `atomic-tests` line while a condition uses `leaf.atomic-tests`; and the
  `leaf.type` registry line duplicated — when `check` runs, then it reports
  `harness-always-on-missing`, `rule-load-mode-invalid`, `instruction-source-ambiguous`,
  `invalid-utf8`, `control-character`, `vocabulary-anchor-invalid` and
  `feature-registry-invalid` respectively.
- **AC-23** (REQ-28). Given the delivered measurement summary and the committed records,
  then the before records' `source_revision` equals the map's `baseline_revision`, no other
  revision appears as a before record, and if any AC-03 result is not `true` the summary
  states AC-03 as not met with the measured ratios and the owner hand-off.
- **AC-24** (REQ-29, REQ-31). Given an MVR plus a second `load: always` rule not named in
  `always-on.md`, and an MVR whose `always-on.md` adds "Load `contract-phases`." (an
  on-demand rule), when `check` runs, then it reports `always-on-rule-not-named` for the
  first and `always-on-load-unreachable` for the second.
- **AC-25** (REQ-32). Given an MVR whose `atomic-execution-implement` body lacks
  `` `contract-reports → ## GREEN report` ``, and one whose `spec-run` lacks
  `` `contract-reports → ## Consuming reports` ``, when `check` runs, then each reports
  `report-form-not-cited` for that workflow.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-01, AC-08 |
| REQ-02 | AC-07 |
| REQ-03 | AC-02, AC-08 |
| REQ-04 | AC-09 |
| REQ-05 | AC-03 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04 |
| REQ-08 | AC-05 |
| REQ-09 | AC-11 |
| REQ-10 | AC-12 |
| REQ-11 | AC-13 |
| REQ-12 | AC-08, AC-14 |
| REQ-13 | AC-06 |
| REQ-14 | AC-15 |
| REQ-15 | AC-15 |
| REQ-16 | AC-16 |
| REQ-17 | AC-17 |
| REQ-18 | AC-18 |
| REQ-19 | AC-08, AC-19 |
| REQ-20 | AC-02 |
| REQ-21 | AC-20 |
| REQ-22 | AC-21 |
| REQ-23 | AC-10 |
| REQ-24 | AC-04 |
| REQ-25 | AC-05 |
| REQ-26 | AC-05 |
| REQ-27 | AC-22 |
| REQ-28 | AC-23 |
| REQ-29 | AC-08, AC-24 |
| REQ-30 | AC-16 |
| REQ-31 | AC-08, AC-24 |
| REQ-32 | AC-08, AC-25 |

Every AC names at least one REQ above; AC-01–AC-05 keep their original REQ links, narrowed,
with REQ-26 added to AC-05.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| The 50% target is unreachable without dropping obligations | AC-03 unmet | Medium | REQ-05 owner hand-off; obligation map forbids removal; report the measured ratio |
| Textual-load detection misses loads phrased with other verbs | Undeclared dependency, agent skips a needed rule | Medium | Fallback-full on missing declarations; independent review of the obligation map; verbs list extendable additively |
| Agents ignore declarations (prose enforcement) | Instructions not loaded at runtime | Medium | Always-on `contract-loads`; P10 hook enforcement remains future work |
| 09's DM-9 mask rejects moving checked text to a new split file | A needed split is blocked | Medium | 09 REQ-68 admits split targets of mapped rules; stop only for text of two rows |
| The Claude capability declaration (1,607 words before 09's DM-4 records) consumes the 6,000-word always-on budget (09 A-03 leaves it to 11) | Less room for `load: always` rules | Medium | Measured by `check`; obligations move to on-demand rules, never dropped |
| Spec 19's composition, `loads` grammar and rule fields diverge from 11 | Double-counted capability words; generator rejects valid 11 metadata | Low | Notes → "Ownership statements for spec 19"; composition counts the declaration once |
| Splitting rules breaks frozen validator checks that read moved text | Validator fails or the inventory oracle rejects re-pointed expressions | High | REQ-25 re-pointing with the path-only amendment (A-37); new checks stay standalone in `scripts/` |
| Deployment gate adds time to every sync | Slower deploys | Low | The meter reads small files once; duration recorded in the summary, not gated |
| Baseline inflated by over-declaring mandatory loads | False pass of AC-03 | Low | `baseline-edge-unbacked` comparability condition; review |
| Splitting rules creates many small on-demand rules | More loads per workflow | Medium | `rule-unreachable` and measurement records expose it; owner review |

## Assumptions

- A-01 | Project file language | Resolved: rewrite the spec in English; keep a labelled translation of the previous revision's core statements under `## Source` | Source: `rules/language.md`; `.ai/principles/coding.md` "Language and tone" | Reversible: yes
- A-02 | Which names to use for rules and workflows | Resolved: spec 09's target names, with current names cited for facts | Source: `.ai/specs/README.md` dependency order (11 after 09); 09 DM-10, DM-11 | Reversible: yes
- A-03 | Where `loads:` may appear | Resolved: required in workflow front matter, optional in top-level rule front matter, forbidden elsewhere | Source: ADR-0009 D2 (workflow `loads:`); previous revision §5 algorithm (cycle detection implies rule-level edges); 19 REQ-24 (load cycles) | Reversible: yes
- A-04 | Load targets | Resolved: top-level rules, reference files and principles only; workflows are calls, not loads | Source: 19 REQ-24/REQ-25 (call cycles distinct from load cycles); P6 | Reversible: yes
- A-05 | Condition language | Resolved: `==`/`!=` comparisons joined by ` and `, three-valued evaluation | Source: previous revision §5 ("declarative expression from an approved feature set, not code"); best practice (smallest closed grammar) | Reversible: yes
- A-06 | Feature registry content | Resolved: seven features of DM-2, additive extension | Source: branches present in the atomic workflows (`workflows/pae-tests.md:10,40`, `rules/phase-atomic-execution.md:49-51`, `rules/workflow-globals.md:130`); best practice | Reversible: yes
- A-07 | `on_unknown` semantics | Resolved: required on conditional entries, only `load` | Source: previous revision §5 example and REQ-03; spec 19 `## Data Model → Workflow metadata` (conditional item keys include `on_unknown`) | Reversible: yes
- A-08 | Section selector syntax | Resolved: exact heading paths in cross-reference syntax | Source: `.ai/principles/coding.md:45-51`; `tests/workflow-instructions.py:20-35` | Reversible: yes
- A-09 | Word counter | Resolved: Python `str.split()`, counter version 1; files with U+001C–U+001F rejected so the count equals 09's Unicode White_Space wording | Source: previous revision §6; 09 DM-19; spec 19 Terminology (Word) | Reversible: yes
- A-10 | Scope of the 700-word limit | Resolved: every top-level rule regardless of `load:` mode | Source: previous revision REQ-01; 09 DM-19 and its NFR table; spec 19 A-17 (700 stays with 11) (stricter than and consistent with ADR-0009 D6's per-always-on-rule wording) | Reversible: yes
- A-11 | Composition of the always-on set | Resolved: `always-on.md` + `capabilities.md` until spec 19, then the generated `always-on.md` alone (19 REQ-50); plus `load: always` rules and their mandatory closure; 09 DM-14's separator and installation record not counted | Source: `scripts/sync.sh:58-67,99-101,155-158`; 09 DM-14; 19 REQ-50 (amended 2026-11-14) | Reversible: yes
- A-12 | Granularity of the 50% target | Resolved: per workflow and per harness; all four pairs must pass | Source: previous revision REQ-05 and AC-03 ("each separately; no averaging"); best practice | Reversible: yes
- A-13 | Meter interface and exit codes | Resolved: subcommands and codes of `## Contracts & Interfaces`; declaration defects are findings (exit 1), unlike spec 19's generator (exit 2) | Source: previous revision REQ-04 and §6 (name fixed at implementation); `scripts/run-log-timing.sh` launcher pattern; best practice | Reversible: yes
- A-14 | Baseline binding to the installed version | Resolved: manifest from an isolated deployment of the same revision; its `source_revision` must equal the record's; otherwise the comparison is unknown | Source: previous revision REQ-05 and §6; 09 REQ-58 and DM-6 (`source_revision`); 09 REQ-47 (isolated deployments) | Reversible: yes
- A-15 | Preventing an inflated baseline | Resolved: `backing_lines` and the `baseline-edge-unbacked` condition | Source: previous revision §6 ("compare the same context boundaries"); best practice | Reversible: yes
- A-16 | Where evidence of measurement lives | Resolved: dated files under `docs/analysis/`, indexed in `docs/README.md` | Source: `.ai/principles/coding.md:71-92` | Reversible: yes
- A-17 | Canonical home of the loads contract | Resolved: new `rules/contract-loads.md` with `load: always` | Source: P6; `.ai/principles/domain.md:65` invariant 11 (one definition) | Reversible: yes
- A-18 | Canonical home of report forms | Resolved: new `rules/contract-reports.md`, `load: on-demand`, loaded by the four boundary workflows | Source: P6; previous revision REQ-06/07 | Reversible: yes
- A-19 | Which workflow reports "completion" | Resolved: `atomic-validation-close` | Source: previous revision §7 (last verified revision, branch/PR state, next allowed action); `workflows/pav-close.md:70` | Reversible: yes
- A-20 | "Identity of changes" for workers that may not run git | Resolved: per-path SHA-256 plus revision only when the role may read git | Source: `workflows/spec-run.md:245` | Reversible: yes
- A-21 | Report length | Resolved: no length or item-count limit | Source: previous revision §7 ("the number of important findings is not limited") | Reversible: yes
- A-22 | Evidence reference format | Resolved: DM-7 with `file` or heading-path scope and a `text@1` format registry | Source: previous revision §7 (path, hash, format version, scope); best practice | Reversible: yes
- A-23 | Runtime fallback and stop | Resolved: fallback-full for a missing or unreadable declaration; **stop** for an unavailable mandatory target | Source: previous revision §9; P5 | Reversible: yes
- A-24 | Parent/child context reuse | Resolved: reuse only unchanged sources still in context; standalone and fresh workers load fully | Source: ADR-0014 Decision 1 | Reversible: no (accepted decision)
- A-25 | Reference file schema | Resolved: front matter exactly `description:` | Source: 09 REQ-26 (separate schema and `ref-` namespace); current skills carry only `description:` (`workflows/pav-close.md:1-3`) | Reversible: yes
- A-26 | Test placement and validator inventory | Resolved: standalone suite `scripts/check-context-tiering.py`, not registered in the validator; a deployment gate in `scripts/sync.sh` running only the meter's `check` | Source: ADR-0019 Decision 3 (`.ai/adr/0019-task-unknown-spec-draft-devils-advocate-review.md:69-80`); `tests/fixtures/validator-runtime/oracle.py:244-250`; spec 19 `### Acceptance suite` and REQ-22 (same pattern) | Reversible: yes
- A-27 | Git reads must not write | Resolved: `GIT_OPTIONAL_LOCKS=0` | Source: 13 REQ-03 (read-only helper with `GIT_OPTIONAL_LOCKS=0`); best practice | Reversible: yes
- A-28 | Implementation prerequisites | Resolved: 09 and 10 delivered before start | Source: `.ai/specs/README.md` order row 7; previous revision §11 | Reversible: no
- A-29 | Recording the design | Resolved: one ADR during implementation for the declaration schema, reference tier and report forms | Source: `.ai/specs/README.md` "Record changes to accepted behavioral contracts in an ADR"; `.ai/principles/coding.md` "Changing a contract" step 6 | Reversible: yes

- A-30 | Default root of the meter | Resolved: the launcher's parent directory, `ORCHESTRAIL_HOME` ignored, callers pass `--root` | Source: `.ai/memory/architecture.md` "External Dependencies" (`ORCHESTRAIL_HOME` selects shared checkouts, so it can point elsewhere); best practice | Reversible: yes
- A-31 | How `load: always` rules reach a session | Resolved: `harness/<h>/always-on.md` names each in a textual load command (REQ-31) | Source: `.ai/context/environment.md:19`; P11; ADR-0003 Decision 2 (essentials in the global file) | Reversible: yes
- A-32 | Fallback-full content after hand-written lists are removed | Resolved: always rules, phase bootstrap rule when one exists, and every source named in the body | Source: previous revision §9 ("full previous loading"); `.ai/principles/coding.md` "Cross-references" (steps cite sections) | Reversible: yes
- A-33 | Scope of the delta rule | Resolved: deltas inside the four reports and their consumption by `/spec-run` 4.6; other worker deltas follow 13 REQ-36/DM-4, with this rejection rule applied first on the helper route and by the Orchestrator on the manual route (amended 2026-11-14) | Source: `rules/orchestration.md` "Shared-file discipline"; 13 DM-3, DM-4, REQ-08, REQ-36, REQ-50 | Reversible: yes
- A-34 | Evidence path base | Resolved: two named bases, `work` (`WORK_DIR`) and `task` (parent task directory) | Source: `workflows/spec-run.md:238-239`; `rules/phase-atomic-execution.md:16-22` | Reversible: yes
- A-35 | Baseline revision content | Resolved: declarations, citation line, `contract-loads`, the always-on lines naming every `load: always` rule, and REQ-22 only; `contract-loads` counted | Source: previous revision §8 step 4 ("add the load schema … then split texts"); best practice | Reversible: no once committed (REQ-28)
- A-36 | Handling of 08's 11-owned proposals and findings | Resolved: implement or decline each proposal and each finding of any type with owner 11, recorded in the measurement summary | Source: 08 REQ-02; owner decision on AUD-08-065 (2026-11-18) | Reversible: yes
- A-37 | Changed validator expressions under the frozen inventory | Resolved (amended 2026-11-14): reuse 09's schema-2 amendment (09 DM-9, REQ-51); 11 supplies `path_changes` entries and `resources` changes for its own re-pointing and defines no schema; the earlier fallback definition is withdrawn | Source: 09 DM-9, REQ-51, REQ-52, A-02; 09 Notes "Peer requests" ("09 owns it") | Reversible: yes
- A-38 | Rules created after this spec and after the baseline | Resolved: 09's naming and placement rule; full `check`; counted only in after records; over-limit edits stop, with `/spec-sync` to the owning spec for word-fixed rules | Source: 09 Notes "Files and sections created after this spec"; 14 REQ-47, REQ-48; 13 REQ-49; REQ-28 | Reversible: yes
- A-39 | Delivery order of 09's changes and 11's re-pointing | Resolved: 09's guard (A-28) stays; 11 adds its entries to 09's amendment after 09 has delivered it | Source: `.ai/specs/README.md` dependency order; 09 DM-9 ("reused by spec 11") | Reversible: yes

## Decisions

- D-01 (owner, 2026-11-18) — Scope item 9 takes in every finding with owner 11 that the 08
  audit records, not only its proposals. The audit (AUD-08-065) found nine findings with owner
  11 and another type (reference-defect, duplicate, naming and others: AUD-08-010, AUD-08-018,
  AUD-08-025, AUD-08-026, AUD-08-037, AUD-08-038, AUD-08-058, AUD-08-060, AUD-08-061) that
  the earlier wording gave no intake. Requirement ids and acceptance criteria are unchanged.

Earlier refinements: no owner decision overrides a principle, ADR or shipped invariant.
Owner-standing authorizations used: in-place replacement of this file.

## Clarifications

N/A — no questions were put to the owner in this autonomous refinement on 2026-11-13;
every resolution is recorded under `## Assumptions`.

## Open Questions

- **Q-01 — resolved 2026-11-14.** Spec 09 reserves `loads` as an extension key on rules and
  workflows that this spec registers (09 DM-2, DM-3, A-06); REQ-22 now targets 09's
  checker.
- **Q-02 — resolved 2026-11-14.** Spec 09 applies its 1,200-word limit to the always-on body
  only and leaves the capability declaration to this spec's 6,000-word budget (09 REQ-54,
  A-03); the always-on set definition and the composition rule follow it. 09 keeps its own
  question on restoring the stricter reading (its Q-01).
- **Q-03 — resolved 2026-11-14.** The divergences from spec 19 are settled by the ownership
  statements in Notes → "Ownership statements for spec 19"; the composition change (former
  point 1) is made by spec 19's delivery (19 REQ-50); the exit-code difference stays
  intentional.
- **Q-04 — resolved (A-37).** Settled by reuse of 09 DM-9 (amended 2026-11-14).
- **Q-05 — resolved 2026-11-14.** The manifest field is `source_revision` (09 REQ-58, DM-6).
- **Q-06 — resolved 2026-11-14 (answer to spec 14's Q-03).** Should this spec accept 14's
  `OUTPUT` lines as a second evidence-reference kind? **No.** No requirement of 14 needs it:
  copying the `command:` line, failing test names and error lines verbatim already meets
  REQ-07's "verbatim" branch, and acceptance would only let a report cite captured output by
  reference. `OUTPUT` lines may appear as `Evidence` list items; `evidence verify` does not
  check them (14's own `verify` does).
- **Q-07 (resolved 2026-11-14 by 09 REQ-68, option (a)).** 09's DM-9 mask rejected moving checked text from a name-map class
  path to a file this spec creates (Contracts → Existing validator checks, mask
  constraint). Impact: a rule whose frozen-checked text cannot stay in place within 700
  words cannot be split until 09 decides. Options: (a) 09 lets a later spec append split
  targets to the `new` list of the existing `rule` row (09 DM-1 already models a split that
  way), which puts them in the class — recommended; (b) 09 adds a requirement of its own that
  admits this spec's split re-pointing to the closed requirement set of `contract_changes`,
  with DM-20 rows; (c) keep the text in place (default until
  09 decides). Resolution: 09 adopted option (a) as REQ-68; only text of two rows moving into
  one file still stops.

## Notes

### Prerequisites and Guard for the implementing task

Before any change: confirm spec 09 delivered (`load:` metadata on every rule, target names,
deploy manifest with `source_revision`, isolated deployment fixtures, the schema-2 inventory amendment of 09 DM-9, and the checker `scripts/lint-instructions.py`) and spec 10's
offline regression suite exists.
If any is missing, stop and report; do not invoke future names as existing.

### Implementation order (hint; Discovery decides the decomposition)

1. RED: `scripts/check-context-tiering.py` cases for AC-01, AC-02, AC-04, AC-06, AC-09–AC-19,
   AC-22, AC-24, AC-25; observe them fail.
2. Engine, launcher, `rules/contract-loads.md`, the always-on lines naming every
   `load: always` rule (REQ-31), REQ-22 registration of `loads` in 09's checker.
3. Declarations and citation lines for every workflow describing current loading exactly
   (textual-load check passes; no other text change); commit: this is the baseline
   revision. Isolated deployment of it; capture and commit the before records.
4. `rules/contract-reports.md`, the four report sections and the `/spec-run` 4.6 citation.
5. Split rules: obligations into ≤ 700-word top-level rules, rationale/examples/history
   into `rules/reference/`; re-point affected validator checks (REQ-25); update
   declarations; write the obligation map; handle 08's 11-owned proposals and findings.
6. Reference deployment through 09's mechanism and the sync gate (AC-05, AC-07).
7. After records, `compare`, `obligations`, measurement summary, knowledge-base updates, ADR.

### Rollback

Revert the change set with ordinary commits (no history rewriting). The next deployment
removes owned, unmodified `ref-*` skills through 09's manifest. A workflow whose
declaration is removed or broken is still executable through fallback-full loading, which
loads every source its body names. Task history, state files and evidence records are
untouched by a rollback.

### Follow-ups for other specs and shared files (not edited here)

- 13: none outstanding — Q-07 was settled by 09 REQ-68.
- 10: align with Notes → "Ownership statements for spec 19".
- 11: when its installer replaces 09's engine, it records `ref-*` objects (REQ-02); DM-4
  reads its `source.commit`.
- 15: none; it registers no evidence format and owns the inner `delta` syntax (13 DM-4).
- 17: none; Q-06 answers its Q-03.
- 14: project-context bootstrap stays its domain; packets may cite DM-4 records.

### Ownership statements for spec 19

- **Load-cycle detection** belongs to this spec's meter only, over the load graph of
  top-level rules: edges come from the `loads:` of workflows and rules, workflows are never
  targets (A-04), so every cycle runs through rules (REQ-11, finding `cycle`). Target and
  section existence are also the meter's (REQ-18, REQ-20). The generator checks none of
  them.
- **`sections`** is a one-line JSON array of heading paths with their `#` markers, for
  example `["## Safety rails"]` or `["## A → ### B"]` (DM-1, REQ-18).
- **Plain values inside the `loads` block** match `[A-Za-z0-9_./-]+`; anything else is a
  JSON string (DM-1). Top-level scalars outside the block follow 09 DM-2/DM-3.
- **Capability declaration counted once:** until spec 19 the meter counts `always-on.md` plus
  `capabilities.md`; spec 19's delivery switches it to the generated `always-on.md` alone
  (19 REQ-50), as Contracts → Graph resolution (always-on composition) states. The domain
  row for "Always-on set" is worded by whichever of the two is delivered last.
- **`loads` on rules** is optional and must be accepted wherever spec 19 reads rule front
  matter (REQ-22; 09 DM-2).
- **Exit codes:** the generator exits 2 on declaration defects while the meter reports them
  as findings with exit 1; the difference is intentional (A-13).

### Rejected alternatives

- Flat declarations in workflows only (rejected under A-03; 09 DM-2 registers `loads` on rules).
- A general expression language or Python expressions for conditions (rejected: unsafe and
  unbounded; previous revision §5 forbids executable conditions).
- Keeping obligations in reference files loaded mandatorily (rejected: P6 "reference
  explains").
- Requiring a real user-home deployment for the baseline (rejected: 09 REQ-47 forbids real
  deployments in checks).
- A fixed report length cap (rejected under A-21).

### Change Log

#### 2026-11-06 — implementation/state reconciliation

- Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

#### 2026-11-13 — autonomous refinement

- Translated to English; REQ-01–REQ-08 narrowed to one behaviour each with unchanged
  meaning (REQ-08's validator wording became a deployment gate because the validator
  inventory is frozen); REQ-09–REQ-32 and AC-06–AC-25 added for parts of the old combined
  requirements and for gaps (schema grammar, feature registry, record/map/reference
  schemas, finding codes, runtime contract lines, deployment gate, validator re-pointing). The previous revision's
  withdrawal of the 40–60 thousand token estimate stands.

#### 2026-11-14 — reconciliation with final specs 10, 19, 21, 09, 12, 13, 15, 14, 16, 17

- Reused 09's schema-2 inventory amendment (09 DM-9); the own fallback definition is
  withdrawn (A-37 amended); 11 supplies `path_changes` and `resources` entries; mask
  constraint and Q-07 added.
- Q-01, Q-02, Q-03, Q-05 resolved from 09 DM-2/DM-3, REQ-54, REQ-58 and the spec 19
  ownership statements; always-on set and composition follow 09 REQ-54, DM-14 and 19
  REQ-50; DM-4 reads spec 21's `source.commit`; harness
  definition follows 09 DM-5; REQ-22 targets 09's checker.
- New subsection on rules and workflows created after this spec (A-38); edge cases added.
- Delta scope corrected against 13 DM-3, DM-4, REQ-08, REQ-36, REQ-50; evidence formats:
  neither 13 nor 14 registers one; Q-06 answers 14's Q-03 (no).
- REQ-26 and AC-05(e) name `python3 -I tests/golden-runs.py`.
- Peer rules checked against DM-1/DM-2: the declarations specs 12, 13, 15, 14 and 17 describe
  (mandatory entries for `contract-context`, `contract-checkpoints`,
  `contract-delta-operations`, `contract-verification`, `contract-output`, `contract-repair`)
  use only mandatory entries and parse; spec 16 adds no rule and spec 21's
  `contract-dry-run` declares no `loads`.

#### 2026-11-14 — independent final review

- Q-07 recorded as resolved by 09 REQ-68 (mask constraint, edge case, risk, follow-up, changed files); deployment gate placed after 09's runtime guard and 19's check; isolated `HOME` includes `XDG_CONFIG_HOME`/`XDG_STATE_HOME`; AC-21 names `metadata-invalid-value`; terms unified (deploy manifest, capability declaration, always-on body); stale citations corrected.

#### 2026-11-18 — intake of audit findings with owner 11

- Owner decision on AUD-08-065 of the rules and workflows audit: Scope item 9, A-36, the
  measurement summary and the implementation-order hint now take in every finding with
  owner 11 as well as the proposals (D-01). No requirement or criterion id changed.

## Readiness Checklist

Result of 2026-11-13, updated 2026-11-14:

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph describing the outcome | PASS — `## Goal` is one paragraph |
| 2 | Out of Scope names concrete exclusions | PASS — owners 05, 10, 19, 09, 12, 13, 14 and excluded workflows named |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-32, split where bundled |
| 4 | Every REQ maps to ≥1 AC; every AC names ≥1 REQ | PASS — `## Traceability` |
| 5 | Every AC is binary, observable and can guide a test first | PASS — fixture cases run in `scripts/check-context-tiering.py` from the minimal valid root; delivered-tree cases named |
| 6 | Non-functional targets measurable, standard-referenced or N/A | PASS — runtime N/A justified; others verified by AC-17 |
| 7 | Data model and contracts specified | PASS — DM-1–DM-9, command line, exit codes, algorithms |
| 8 | Error, empty, boundary and concurrency cases covered | PASS — `## Edge Cases & Failure Modes` |
| 9 | Every Step 3 ambiguity recorded as resolved or open | PASS — A-01–A-39, Q-01–Q-07 |
| 10 | No blocker question remains | PASS — Q-01–Q-07 resolved (Q-07 by 09 REQ-68) |
| 11 | Every existing-code claim has a verified path:line citation | PASS — verified by the critic in every round |
| 12 | Terminology matches project domain definitions | PASS — `## Terminology`; new terms added to `domain.md` by REQ-21 |
| 13 | Scope is feature-sized (1–8 subtasks) | PASS — seven implementation steps in `## Notes` |
| 14 | Devil's Advocate review passed | PASS — Review: 5 rounds, score 100/100, critic: sub-agent, open: none |

Reconciliation pass 2026-11-14: targeted edits checked by one independent pass on the changed passages; verdict unchanged.

Verdict: **READY FOR DEVELOPMENT**, subject to the implementation prerequisites in
`## Notes` (specs 09 and 10 delivered). Automated readiness is not owner sign-off.
