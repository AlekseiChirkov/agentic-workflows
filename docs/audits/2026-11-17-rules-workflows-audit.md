# Rules and workflows audit — 2026-11-17

## Summary

One pinned audit of every rule, workflow and harness adapter file before the naming
migration (spec 09). The inventory was extracted at commit
`8d7e484db530973c82cac8c2a7b82d94b6311c04` on a clean tree: 61 audited files (14 rules,
42 workflow files including `workflows/PIPELINE.md`, 4 harness files and
`templates/codex-global-AGENTS.md`) and 519 reader files (260 active, 33 planning, 217
history, 9 frozen), with 7006 reference edges. 487 of them are defect edges: 42 from audited
files and 445 from readers. Every audited file was read in full; read coverage is complete.

State of this report: the audit is not claimed complete until the independent review line
records `pass`; the report is not accepted (`Accepted: pending`); no defect is claimed fixed.
Nothing was changed in an audited file, and spec 09 itself is unchanged: every change this
audit proposes to it is an amendment below.

### Results for spec 09

- **Migration map.** 61 entries, one per audited path: rename 37 (the 28 workflow renames of
  spec 09 DM-11 and 9 rules), keep 17 (the 13 unchanged workflow names and the 4 harness
  files), split 4 (`rules/phase-discovery.md`, `rules/phase-atomic-execution.md` and
  `rules/workflow-reference.md` by DM-12; `rules/phase-atomic-validation.md` only by its REQ-19
  overflow target) and move 3 (the
  two always-on bodies to `harness/<name>/always-on.md`, `workflows/PIPELINE.md` to
  `docs/PIPELINE.md`). Every spec 09 default was derived by the table of this audit's DM-7; no
  audited path is missing from spec 09's maps, so no entry has a null default, and no entry
  deviates from its default. The atomic-execution and atomic-validation splits carry the
  overflow rule that spec 09 DM-10 permits for their phase, because the text they move has 443
  and 341 words (rules/phase-atomic-execution.md:1-52, rules/phase-atomic-validation.md).
- **Statement coverage (spec 09 REQ-21).** Verdict `not-covered`. Of the 15 statement units of
  `## Codebase Reading Rules` and `## Decision Protocol` in `rules/phase-discovery.md`, only
  three have a counterpart in `## Autonomous Decision Protocol` (rules/workflow-reference.md:426,
  :430). The research order for unclear requirements (rules/phase-discovery.md:49) overlaps only
  in part: the protocol gives the same priority order, but for scoring inputs
  (rules/workflow-reference.md:443-446), without the obligation to record the resolution under
  `### Assumptions`. The reading budget, the back-to-back steps, the Guard stop and the whole
  step-by-step mode (rules/phase-discovery.md:38-41, :56-64) have no counterpart. The merge
  into `protocol-autonomous-decision` is therefore not proven, and the default
  `protocol-discovery-conduct` stands.
- **Amendments.** Seven, all `proposed` and none requiring an ADR, in two independent sets.
  References: AMD-08-01 extends DM-16's pre-existing-defect paragraph to the reference defects
  this audit records with owner 09 outside its grammar (unmarked or paragraph-label section
  references, a reference broken across lines, `.md`-suffixed workflow names in spans, and such
  references in reader files); AMD-08-02 adds the acceptance criterion that checks it; AMD-08-05
  widens DM-20's `## Pre-existing reference defects` table to hold them. Bootstrap size:
  AMD-08-03 makes REQ-19's 300-word limit yield to a recorded exception for a bootstrap whose
  own context section already exceeds it; AMD-08-04 lets the checker of REQ-32 accept such a
  rule at its recorded count; AMD-08-06 adds the `## Bootstrap size exceptions` table to DM-20;
  AMD-08-07 restates AC-11 for the exception. Each set is consistent only when accepted whole.
  Three statements of the limit are not amendment targets (the Non-Functional Requirements,
  Edge Cases and Risks rows of spec 09) and are named in AMD-08-03 for the reconciliation.
- **Blocking findings.** Nine, listed under `## Blockers for spec 09`: each is cited by an
  amendment, so spec 09 cannot settle it before the owner decides that amendment.

### Findings

72 findings: 71 open and 1 `historical-fixed`. By type: mixed-kind 12, other 10,
accepted-observation 10, reference-defect 8, load-repeat 7, conditional-context 6,
ambiguous-name 4, report-repeat 4, review-repeat 4, naming 2, checkpoint-repeat 2,
duplicate 2, legacy-mention 1. By severity: major 15, minor 57; none is `blocker`. By owner:
09 27, 11 19, 12 7, 15 4, 13 2, owner 3, none 10.

### Decisions taken in the synthesis

- **Ownership of pre-existing reference defects.** This audit's A-18 gives them to owner 09,
  and REQ-29 requires an amendment where an edge lies outside spec 09's grammar. AUD-08-001,
  004, 005, 007, 033, 035 and 036 were therefore re-owned from 11 to 09 and cite AMD-08-01, as
  does the new reader finding AUD-08-062.
- **Reader defect edges.** Of the 445 defect edges from reader files, 5 are genuine reference
  defects (three unmarked headings, AUD-08-062; two citations of the mode-override registry,
  which has no heading, added to AUD-08-036), 2 repeat the pack-file misresolution of
  AUD-08-006, and 438 are correct on reading and recorded as seven accepted observations by
  source and pattern (AUD-08-066 to AUD-08-072): mostly `<stem>.md` file names in shell and
  Python code, validator messages, file-role tables and links, plus placeholders such as
  `file → ## Section`.
- **Findings with owner 11 outside the proposal types.** Spec 11 takes in only proposals
  (its Scope item 9), while this audit's data model also allows owner 11 for other types. Nine
  such findings have no intake. This is recorded as AUD-08-065 for the owner's decision rather
  than resolved by re-ownership, since owner 11 is valid for those types.
- **Duplicates.** 18 groups cover the 64 verbatim clusters once each, plus one read-detected
  group: intentional 7 (the always-on essentials mirrored by ADR-0003 Decision 2 and
  one-sentence restatements where they are acted on), condition-specific 9 (per-workflow
  guards, phase bootstraps and run ownership), consolidate 2 with owner 11 (the unchecked copy
  of the atomic status vocabulary, AUD-08-060, and the three paraphrases of the model-resolution
  contract, AUD-08-061). No group is a contradiction.
- **A size target that conflicts with obligatory content.** The atomic-execution bootstrap
  cannot meet spec 09's 300-word limit by overflow alone: its preamble and
  `## Context Bootstrap` already have 316 words (AUD-08-063). Nothing is proposed for deletion;
  AMD-08-03, AMD-08-04, AMD-08-06 and AMD-08-07 state how the rule is delivered, recorded
  and checked.
- **A reference correct in the migration's grammar.** AUD-08-031 is an accepted observation:
  the references to `## Mid-flight escalation (quick → full)` resolve under spec 09's form-2
  pattern, which captures the whole heading; only this audit's grammar splits it.
- **Historical defect.** The ambiguous `phase-execution.md` citation that the naming review of
  2026-09-16 found in `workflows/phase-pipeline.md` is absent at the audited revision
  (AUD-08-064, `historical-fixed`).

### Recorded reasons for the mixed-kind entries the map keeps

Spec 09 owns the mixed-kind findings below; the map keeps each file's default target, for
these reasons:

- AUD-08-008 and AUD-08-009: the DM-12 splits are carried out as mapped; the conduct sections
  stay in `protocol-discovery-conduct` because statement coverage is not proven.
- AUD-08-011 (`rules/tdd.md`): the test-level gate (:54) and the characterization procedure
  (:132) are run from `/pae-tests` and the quick path (rules/quick-flow.md:86) while the
  always-on contract is in force; a separate rule would add a load where the contract is
  already loaded. The rationale section (:219-226) is short.
- AUD-08-012 (`rules/run-log.md`): the logging procedure (:58) and the routing table (:116) are
  the parts every orchestrator acts on; the conditional loading of the other sections is
  AUD-08-013 and AUD-08-039 (owner 11).
- AUD-08-014 (`rules/workflow-globals.md`): the per-harness resolution in the preamble (:19-22)
  is replaced by the `## Rule references` line that spec 09 REQ-14 creates; headings for the
  embedded principles are AUD-08-026 (owner 11).
- AUD-08-017 (`rules/workflow-reference.md`): the procedure and reference sections stay in
  `contract-state-files` under DM-12's catch-all; moving reference material to the reference
  tier is spec 11's work.
- AUD-08-019 (`rules/orchestration.md`): the escalation protocol (:137) routes between the
  roles the same contract defines.
- AUD-08-020 (`rules/git-flow.md`): the preflight (:16) and the owner approval protocol (:251)
  gate the branch and safety-rail obligations of the same contract.
- AUD-08-027 (`rules/quick-flow.md`): the gate and the two procedures are the quick tier's
  operative rules; the worked examples (AUD-08-010, owner 11) go to the reference tier under
  spec 11, not by this map.

## Method

Commands, run from the repository root with `MISE_PYTHON_VERSION=3.12.16` (Python 3.12.16,
git 2.53.0):

- `python3 -I scripts/audit-instructions.py extract --root . --out docs/audits/2026-11-17-rules-workflows-audit.inventory.json`
  at `8d7e484`, with `git status --porcelain` empty before the run; a second extraction was
  byte-identical, and an independent re-extraction in a temporary work tree of `8d7e484`
  matched it byte for byte.
- `python3 -I scripts/audit-instructions.py verify --root . --report docs/audits/2026-11-17-rules-workflows-audit.md`
  after each stage of the assessment, until it printed nothing.
- `python3 -I scripts/audit-instructions.py render --root . --report docs/audits/2026-11-17-rules-workflows-audit.md --write`
  for the generated region below.

The assessment was written by one writer in three sequential parts: rules and adapters,
workflows, then the map, duplicate groups, statement coverage, amendments, reader findings and
blocking values. Each part read its files in full at the audited bytes and recorded every
judgment with current `path:line` evidence; an independent validator re-checked the first two
parts before the next began.

Measured times: `extract` 5.95 s (repeat 5.28 s); `verify` 0.6 to 1.1 s and `render` 0.6 to
0.7 s on the final assessment. The reading and judgment work was not timed.

Deviations from the plan:

- Home paths in copied text: by the owner's decision of 2026-11-17 the extractor writes the
  home-directory prefix of an absolute path as `~/` in every text it copies from audited files.
  The method version stays `08-extract-1`, because no output existed under the earlier rule;
  the data-model text is to be reconciled through `/spec-sync`. The machine-specific lines in
  the two always-on bodies are findings AUD-08-022 and AUD-08-023.
- Stack base: the audited tree includes the multi-repository changes of the branch this
  delivery is stacked on, so the permitted-changes check is computed against that base rather
  than `main`.
- Installed copies were not compared (`installed_access: not-verified`).
- Line citations in the specifications that drifted since they were written (for example the
  section lines of spec 09 DM-12) were re-verified at the audited commit; the requirements they
  support stand.
- A location handed over for the read-detected duplicate group pointed at the rule
  `rules/phase-atomic-execution.md:76-98`, which has 71 lines; the paraphrase is in the
  workflow, `workflows/phase-atomic-execution.md:76-98`, and the group records that.

Copied text kept verbatim in the inventory: only home paths are rewritten. The text of cluster
DUP-021 (`rules/global-claude.md:120`, `templates/codex-global-AGENTS.md:51`) holds an
absolute system path of the setgroups program; four reader edges of the history and planning
classes, none a defect, have a bare temporary-directory path as their raw text; and one
planning-class edge raw from this task's own state file holds a context-size figure of the kind
REQ-03 excludes. None of these is rendered in the region below, and no finding or region row
quotes them.

Detection noise: the token grammar flags every `<stem>.md` name outside instruction files, so
438 of the 445 reader defect edges are correct on reading; they are recorded as accepted
observations so that the defect list stays complete without asking for changes.

<!-- audit:generated:begin -->

### Passport

- source_revision: 8d7e484db530973c82cac8c2a7b82d94b6311c04
- worktree: clean
- inventory_digest: a421bc3a038eee7600bdc7209b296acffa580f66f3dd934c34a19e54dbef8763
- method_version: 08-extract-1
- scope: primary 56 (`rules/`, `workflows/`); adapter 5 (`harness/`, `templates/codex-global-AGENTS.md`); readers 519 (active 260, frozen 9, planning 33, history 217); excluded `docs/audits/*-rules-workflows-audit.md`, `docs/audits/*-rules-workflows-audit.inventory.json`, `docs/audits/*-rules-workflows-audit.assessment.json`, `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`; skipped `.git/`, `logs/`, `output/`, `__pycache__/`, `*.pyc`
- installed_access: not-verified
- read_coverage: complete
- findings: 72 total, 71 open, 9 blocking spec 09
- run_date: 2026-11-17
- environment: Python 3.12.16; git version 2.53.0

### Inventory

| Path | Set | Entry | Tracked | Words | Bytes | Kinds | Coverage | Decision | Findings |
|---|---|---|---|---|---|---|---|---|---|
| harness/claude/capabilities.md | adapter | file | true | 1607 | 10342 | adapter-config | read | keep | AUD-08-024 |
| harness/claude/hooks.json | adapter | file | true | 55 | 718 | adapter-config | read | keep | none |
| harness/claude/permissions.json | adapter | file | true | 23 | 187 | adapter-config | read | keep | none |
| harness/codex/capabilities.md | adapter | file | true | 91 | 672 | adapter-config | read | keep | none |
| rules/git-flow.md | primary | file | true | 3492 | 22671 | contract, protocol | read | rename | AUD-08-001, AUD-08-020 |
| rules/global-claude.md | primary | file | true | 985 | 6996 | always-on | read | move | AUD-08-022, AUD-08-030 |
| rules/language.md | primary | file | true | 122 | 793 | contract | read | rename | AUD-08-021 |
| rules/orchestration.md | primary | file | true | 1659 | 10717 | contract, protocol | read | rename | AUD-08-019 |
| rules/phase-atomic-execution.md | primary | file | true | 733 | 5395 | bootstrap, procedure | read | split | AUD-08-008, AUD-08-063 |
| rules/phase-atomic-validation.md | primary | file | true | 341 | 2511 | bootstrap | read | split | AUD-08-002 |
| rules/phase-discovery.md | primary | file | true | 490 | 3505 | bootstrap, protocol | read | split | AUD-08-003, AUD-08-009 |
| rules/phase-execution.md | primary | file | true | 255 | 1810 | bootstrap | read | rename | none |
| rules/phase-validation.md | primary | file | true | 217 | 1567 | bootstrap | read | rename | none |
| rules/quick-flow.md | primary | file | true | 1681 | 11118 | contract, protocol, procedure, reference | read | rename | AUD-08-004, AUD-08-010, AUD-08-027 |
| rules/run-log.md | primary | file | true | 4547 | 33752 | contract, procedure, protocol | read | rename | AUD-08-012, AUD-08-013 |
| rules/tdd.md | primary | file | true | 1845 | 11816 | contract, protocol, procedure, reference | read | rename | AUD-08-005, AUD-08-011 |
| rules/workflow-globals.md | primary | file | true | 3022 | 21454 | contract, protocol | read | rename | AUD-08-006, AUD-08-007, AUD-08-014, AUD-08-015, AUD-08-016, AUD-08-026 |
| rules/workflow-reference.md | primary | file | true | 5259 | 37108 | contract, protocol, procedure, reference | read | split | AUD-08-017, AUD-08-018, AUD-08-025, AUD-08-028, AUD-08-060 |
| templates/codex-global-AGENTS.md | adapter | file | true | 484 | 3479 | always-on | read | move | AUD-08-023, AUD-08-029 |
| workflows/PIPELINE.md | primary | file | true | 1308 | 10538 | reference | read | move | AUD-08-058 |
| workflows/adr-new.md | primary | file | true | 652 | 4376 | workflow | read | keep | none |
| workflows/bugfix.md | primary | file | true | 1021 | 7188 | workflow | read | keep | AUD-08-055 |
| workflows/compress-state.md | primary | file | true | 384 | 2650 | workflow | read | keep | AUD-08-054 |
| workflows/context-pack.md | primary | file | true | 585 | 4433 | workflow | read | keep | AUD-08-034 |
| workflows/onboard-legacy-project.md | primary | file | true | 1346 | 10174 | workflow | read | keep | none |
| workflows/pae-finalize.md | primary | file | true | 486 | 3652 | workflow | read | rename | none |
| workflows/pae-implement.md | primary | file | true | 1941 | 13453 | workflow | read | rename | AUD-08-040 |
| workflows/pae-tests.md | primary | file | true | 1811 | 12619 | workflow | read | rename | AUD-08-032, AUD-08-042, AUD-08-051, AUD-08-059 |
| workflows/pav-check.md | primary | file | true | 979 | 6856 | workflow | read | rename | AUD-08-057 |
| workflows/pav-close.md | primary | file | true | 537 | 3868 | workflow | read | rename | none |
| workflows/pav-propose.md | primary | file | true | 592 | 4299 | workflow | read | rename | AUD-08-036, AUD-08-046 |
| workflows/pd-analyze.md | primary | file | true | 797 | 6116 | workflow | read | rename | none |
| workflows/pd-archive.md | primary | file | true | 344 | 2628 | workflow | read | rename | none |
| workflows/pd-decompose.md | primary | file | true | 1343 | 10008 | workflow | read | rename | none |
| workflows/pd-design.md | primary | file | true | 499 | 3987 | workflow | read | rename | none |
| workflows/pd-finalize.md | primary | file | true | 984 | 7515 | workflow | read | rename | none |
| workflows/pd-select-model.md | primary | file | true | 2500 | 18723 | workflow | read | rename | AUD-08-041 |
| workflows/pe-execute.md | primary | file | true | 887 | 6797 | workflow | read | rename | AUD-08-045, AUD-08-053, AUD-08-056, AUD-08-061 |
| workflows/pe-finalize.md | primary | file | true | 860 | 6656 | workflow | read | rename | AUD-08-052 |
| workflows/phase-atomic-execution.md | primary | file | true | 1027 | 7564 | workflow | read | rename | none |
| workflows/phase-atomic-validation.md | primary | file | true | 664 | 4814 | workflow | read | rename | none |
| workflows/phase-composite-validation.md | primary | file | true | 1161 | 8601 | workflow | read | rename | none |
| workflows/phase-discovery.md | primary | file | true | 1437 | 10359 | workflow | read | rename | none |
| workflows/phase-execution.md | primary | file | true | 679 | 4906 | workflow | read | rename | AUD-08-031, AUD-08-039, AUD-08-044 |
| workflows/phase-pipeline.md | primary | file | true | 1145 | 8510 | workflow | read | rename | AUD-08-035, AUD-08-043, AUD-08-047, AUD-08-064 |
| workflows/phase-validation.md | primary | file | true | 677 | 5053 | workflow | read | rename | none |
| workflows/pv-classify-fixes.md | primary | file | true | 667 | 4491 | workflow | read | rename | none |
| workflows/pv-contract.md | primary | file | true | 511 | 3517 | workflow | read | rename | AUD-08-033 |
| workflows/pv-create-fixes.md | primary | file | true | 1184 | 8336 | workflow | read | rename | none |
| workflows/pv-execute-fixes.md | primary | file | true | 400 | 2953 | workflow | read | rename | AUD-08-049 |
| workflows/pv-finalize.md | primary | file | true | 1234 | 9612 | workflow, contract | read | rename | AUD-08-038 |
| workflows/pv-issues.md | primary | file | true | 300 | 2092 | workflow | read | rename | none |
| workflows/pv-review.md | primary | file | true | 549 | 4026 | workflow | read | rename | AUD-08-048 |
| workflows/restack.md | primary | file | true | 1506 | 10619 | workflow, contract | read | keep | AUD-08-037 |
| workflows/retro.md | primary | file | true | 3826 | 27890 | workflow | read | keep | none |
| workflows/spec-draft.md | primary | file | true | 2807 | 17894 | workflow | read | keep | AUD-08-050 |
| workflows/spec-run.md | primary | file | true | 4274 | 30383 | workflow | read | keep | none |
| workflows/spec-sync.md | primary | file | true | 784 | 5559 | workflow | read | keep | none |
| workflows/suggest-commit-message.md | primary | file | true | 453 | 2941 | workflow | read | keep | none |
| workflows/suggest-commit-pr.md | primary | file | true | 118 | 803 | workflow | read | keep | none |
| workflows/suggest-pr-description.md | primary | file | true | 331 | 2296 | workflow | read | keep | none |

### Sections

| Path | Section | Line | Words | Bytes | Kind | Proposed home |
|---|---|---|---|---|---|---|
| harness/claude/capabilities.md | (preamble) | 1 | 205 | 1477 | - | - |
| harness/claude/capabilities.md | ## git-rails | 29 | 1402 | 8865 | - | - |
| harness/codex/capabilities.md | (preamble) | 1 | 91 | 672 | - | - |
| rules/git-flow.md | (preamble) | 1 | 63 | 420 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Preflight (mandatory, before any branch is created) | 16 | 206 | 1384 | protocol | rules/contract-git-flow.md |
| rules/git-flow.md | ## Branch model — the stack | 41 | 339 | 2399 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Commits | 86 | 669 | 4495 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Pull requests | 170 | 241 | 1535 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Safety rails | 199 | 1198 | 7281 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Recorded state — required for resume and for restack | 276 | 157 | 1090 | contract | rules/contract-git-flow.md |
| rules/git-flow.md | ## Multi-repository runs | 301 | 619 | 4067 | contract | rules/contract-git-flow.md |
| rules/global-claude.md | (preamble) | 1 | 15 | 102 | - | - |
| rules/global-claude.md | ## Role | 4 | 35 | 228 | - | - |
| rules/global-claude.md | ## On Ambiguity | 9 | 27 | 192 | - | - |
| rules/global-claude.md | ## Language (always-on) | 15 | 61 | 433 | - | - |
| rules/global-claude.md | ## Commit Messages (always-on) | 23 | 234 | 1587 | - | - |
| rules/global-claude.md | ## Test-First Development (always-on) | 50 | 234 | 1483 | - | - |
| rules/global-claude.md | ## Context Loading Protocol | 75 | 128 | 1040 | - | - |
| rules/global-claude.md | ## Context Loading Protocol (Multi-Repo Override) | 96 | 90 | 684 | - | - |
| rules/global-claude.md | ## AST-GREP STRUCTURAL SEARCH POLICY | 109 | 161 | 1247 | - | - |
| rules/language.md | (preamble) | 1 | 122 | 793 | - | - |
| rules/orchestration.md | (preamble) | 1 | 95 | 601 | contract | rules/contract-orchestration.md |
| rules/orchestration.md | ## Roles | 18 | 674 | 4359 | contract | rules/contract-orchestration.md |
| rules/orchestration.md | ## Shared-file discipline | 97 | 419 | 2756 | contract | rules/contract-orchestration.md |
| rules/orchestration.md | ## Escalation protocol | 137 | 471 | 3001 | protocol | rules/contract-orchestration.md |
| rules/phase-atomic-execution.md | (preamble) | 1 | 29 | 256 | bootstrap | rules/bootstrap-atomic-execution.md |
| rules/phase-atomic-execution.md | ## Context Bootstrap | 8 | 287 | 2140 | bootstrap | rules/bootstrap-atomic-execution.md |
| rules/phase-atomic-execution.md | ## Phase Behaviors | 44 | 127 | 857 | bootstrap | rules/bootstrap-atomic-execution.md |
| rules/phase-atomic-execution.md | ## Blocker Reconciliation | 53 | 290 | 2142 | procedure | rules/procedure-blocker-reconciliation.md |
| rules/phase-atomic-validation.md | (preamble) | 1 | 28 | 243 | - | - |
| rules/phase-atomic-validation.md | ## Context Bootstrap | 8 | 252 | 1832 | - | - |
| rules/phase-atomic-validation.md | ## Phase Behaviors | 41 | 61 | 436 | - | - |
| rules/phase-discovery.md | (preamble) | 1 | 26 | 219 | bootstrap | rules/bootstrap-discovery.md |
| rules/phase-discovery.md | ## Context Bootstrap | 8 | 217 | 1530 | bootstrap | rules/bootstrap-discovery.md |
| rules/phase-discovery.md | ## Codebase Reading Rules | 36 | 64 | 439 | protocol | rules/protocol-discovery-conduct.md |
| rules/phase-discovery.md | ## Decision Protocol | 43 | 183 | 1317 | protocol | rules/protocol-discovery-conduct.md |
| rules/phase-execution.md | (preamble) | 1 | 25 | 209 | - | - |
| rules/phase-execution.md | ## Context Bootstrap | 8 | 147 | 1051 | - | - |
| rules/phase-execution.md | ## Phase Behaviors | 26 | 83 | 550 | - | - |
| rules/phase-validation.md | (preamble) | 1 | 25 | 206 | - | - |
| rules/phase-validation.md | ## Context Bootstrap | 8 | 138 | 964 | - | - |
| rules/phase-validation.md | ## Phase Behaviors | 26 | 54 | 397 | - | - |
| rules/quick-flow.md | (preamble) | 1 | 161 | 1068 | contract | rules/contract-quick-flow.md |
| rules/quick-flow.md | ## The escalation gate | 27 | 315 | 1980 | protocol | rules/contract-quick-flow.md |
| rules/quick-flow.md | ## The quick path — what changes | 61 | 512 | 3333 | contract | rules/contract-quick-flow.md |
| rules/quick-flow.md | ## Setting the flow (Discovery) | 118 | 126 | 891 | procedure | rules/contract-quick-flow.md |
| rules/quick-flow.md | ## Mid-flight escalation (quick → full) | 137 | 165 | 996 | procedure | rules/contract-quick-flow.md |
| rules/quick-flow.md | ## Worked example A — rejected by the gate (export pipeline changes) | 156 | 162 | 1175 | reference | rules/reference/quick-flow-examples.md |
| rules/quick-flow.md | ## Worked example B — legitimately quick (log-level fix) | 176 | 240 | 1675 | reference | rules/reference/quick-flow-examples.md |
| rules/run-log.md | (preamble) | 1 | 59 | 434 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## The one rule that outranks the rest | 16 | 89 | 515 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Contract version | 27 | 60 | 443 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Where the log lives | 35 | 137 | 1119 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## How a pipeline logs | 58 | 363 | 2400 | procedure | rules/contract-run-log.md |
| rules/run-log.md | ## Workflow coverage and routing | 116 | 654 | 4762 | protocol | rules/contract-run-log.md |
| rules/run-log.md | ## Field vocabulary | 186 | 731 | 5453 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Validation and writes | 280 | 219 | 1544 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Correlated hook intervals | 304 | 586 | 4448 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Native hook adapter | 375 | 1162 | 9033 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Read-only lint | 523 | 304 | 2520 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## What must never enter the log | 564 | 100 | 589 | contract | rules/contract-run-log.md |
| rules/run-log.md | ## Relationship to the existing state files | 577 | 83 | 492 | contract | rules/contract-run-log.md |
| rules/tdd.md | (preamble) | 1 | 68 | 486 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## Where the step sits | 16 | 72 | 533 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## The three states | 32 | 187 | 1229 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## Test-level gate | 54 | 280 | 1866 | protocol | rules/contract-tdd.md |
| rules/tdd.md | ## RED — what counts | 86 | 155 | 918 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## Characterization mode — behaviour-preserving work | 104 | 623 | 3833 | procedure | rules/contract-tdd.md |
| rules/tdd.md | ## GREEN — what implementation may and may not do | 169 | 203 | 1330 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## Interaction with existing mechanisms | 197 | 186 | 1220 | contract | rules/contract-tdd.md |
| rules/tdd.md | ## Why the order matters | 219 | 71 | 401 | reference | rules/contract-tdd.md |
| rules/workflow-globals.md | (preamble) | 1 | 381 | 3048 | contract | rules/contract-phases.md |
| rules/workflow-globals.md | ## Context Pack | 40 | 1010 | 7220 | contract | rules/contract-phases.md |
| rules/workflow-globals.md | ## Flow tiers (quick \| full) | 128 | 264 | 1735 | contract | rules/contract-phases.md |
| rules/workflow-globals.md | ## Canonical Status Formats | 156 | 1367 | 9451 | contract | rules/contract-phases.md |
| rules/workflow-reference.md | (preamble) | 1 | 49 | 388 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## File Responsibility | 10 | 365 | 2724 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Description Amendment | 66 | 159 | 1155 | procedure | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Parent `plan.md` Table Format | 95 | 958 | 7344 | protocol | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Parent `state.md` — `## Subtask Progress` Format | 205 | 239 | 1578 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Status Lifecycle Notes | 229 | 113 | 813 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Key State-File Markers | 241 | 158 | 1173 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Reference Tables (moved from workflow-globals) | 259 | 6 | 51 | reference | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Status Translation Table | 261 | 127 | 1031 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Protected Sections Contract | 280 | 432 | 3055 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Multi-Phase Spec Rules | 325 | 388 | 2718 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## .ai/memory/state.md Entry Format | 377 | 261 | 1718 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## .ai/project_state.md Update Rules | 408 | 182 | 1179 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Autonomous Decision Protocol | 423 | 474 | 3002 | protocol | rules/protocol-autonomous-decision.md |
| rules/workflow-reference.md | ## Autonomous Subtask Classifier | 487 | 756 | 5015 | protocol | rules/protocol-subtask-classifier.md |
| rules/workflow-reference.md | ## Decomposition Rules | 560 | 225 | 1469 | protocol | rules/protocol-subtask-classifier.md |
| rules/workflow-reference.md | ## Legacy tasks | 584 | 22 | 188 | reference | rules/contract-state-files.md |
| rules/workflow-reference.md | ## Project .ai/ Contract | 590 | 212 | 1478 | contract | rules/contract-state-files.md |
| rules/workflow-reference.md | ## File Location Reference | 619 | 133 | 1029 | reference | rules/contract-state-files.md |
| templates/codex-global-AGENTS.md | (preamble) | 1 | 28 | 212 | - | - |
| templates/codex-global-AGENTS.md | ## Language (always-on) | 5 | 61 | 433 | - | - |
| templates/codex-global-AGENTS.md | ## Commit Messages (always-on) | 13 | 234 | 1587 | - | - |
| templates/codex-global-AGENTS.md | ## AST-GREP STRUCTURAL SEARCH POLICY | 40 | 161 | 1247 | - | - |
| workflows/PIPELINE.md | (preamble) | 1 | 61 | 442 | - | - |
| workflows/PIPELINE.md | ## How to Pass Task Context | 12 | 80 | 585 | - | - |
| workflows/PIPELINE.md | ## Task Structure Types | 25 | 93 | 620 | - | - |
| workflows/PIPELINE.md | ## File Structure | 38 | 131 | 1465 | - | - |
| workflows/PIPELINE.md | ## Phase 1 — Discovery | 65 | 66 | 518 | - | - |
| workflows/PIPELINE.md | ## Phase 2 — Execution | 75 | 53 | 401 | - | - |
| workflows/PIPELINE.md | ## Phase 3 — Validation | 84 | 58 | 429 | - | - |
| workflows/PIPELINE.md | ## Atomic Workflows | 93 | 77 | 648 | - | - |
| workflows/PIPELINE.md | ## Status Glossary | 108 | 141 | 1058 | - | - |
| workflows/PIPELINE.md | ## Child Workflows (Direct Step Access) | 126 | 227 | 1901 | - | - |
| workflows/PIPELINE.md | ## Orchestrated Mode — one spec to review-ready pull requests | 155 | 184 | 1381 | - | - |
| workflows/PIPELINE.md | ## Utility | 177 | 32 | 254 | - | - |
| workflows/PIPELINE.md | ## Full Cycle Example | 183 | 12 | 182 | - | - |
| workflows/PIPELINE.md | ## Quick Start | 191 | 49 | 332 | - | - |
| workflows/PIPELINE.md | ## Known Limitations | 198 | 44 | 322 | - | - |
| workflows/adr-new.md | (preamble) | 1 | 60 | 411 | - | - |
| workflows/adr-new.md | ## Schema — single source | 9 | 44 | 295 | - | - |
| workflows/adr-new.md | ## Guard | 15 | 174 | 1134 | - | - |
| workflows/adr-new.md | ## Step 1 — Gather the decision | 32 | 94 | 663 | - | - |
| workflows/adr-new.md | ## Step 2 — Check for contradiction | 44 | 84 | 552 | - | - |
| workflows/adr-new.md | ## Step 3 — Status | 53 | 76 | 535 | - | - |
| workflows/adr-new.md | ## Step 4 — Write | 63 | 95 | 617 | - | - |
| workflows/adr-new.md | ## Step 5 — Report | 73 | 25 | 169 | - | - |
| workflows/bugfix.md | (preamble) | 1 | 91 | 701 | - | - |
| workflows/bugfix.md | ## Guard | 14 | 132 | 910 | - | - |
| workflows/bugfix.md | ## Run logging | 28 | 29 | 190 | - | - |
| workflows/bugfix.md | ## Step 0 — Resolve the defect | 33 | 60 | 375 | - | - |
| workflows/bugfix.md | ## Step 1 — Reproduce | 50 | 112 | 768 | - | - |
| workflows/bugfix.md | ## Step 2 — Diagnose and write the contract | 70 | 207 | 1466 | - | - |
| workflows/bugfix.md | ## Step 3 — RED: freeze the reproduction as a test | 106 | 100 | 650 | - | - |
| workflows/bugfix.md | ## Step 4 — GREEN: fix | 117 | 89 | 634 | - | - |
| workflows/bugfix.md | ## Step 5 — Verify and record | 127 | 164 | 1241 | - | - |
| workflows/bugfix.md | ## Step 6 — Report | 145 | 37 | 253 | - | - |
| workflows/compress-state.md | (preamble) | 1 | 44 | 345 | - | - |
| workflows/compress-state.md | ## Guard | 9 | 66 | 443 | - | - |
| workflows/compress-state.md | ## Step 1 — Audit Content | 17 | 115 | 712 | - | - |
| workflows/compress-state.md | ## Step 2 — Confirm Changes | 33 | 28 | 202 | - | - |
| workflows/compress-state.md | ## Step 3 — Apply Compression | 38 | 85 | 627 | - | - |
| workflows/compress-state.md | ## Step 4 — Verify Result | 50 | 46 | 321 | - | - |
| workflows/context-pack.md | (preamble) | 1 | 40 | 302 | - | - |
| workflows/context-pack.md | ## Guard | 10 | 71 | 527 | - | - |
| workflows/context-pack.md | ## Sources | 20 | 155 | 1174 | - | - |
| workflows/context-pack.md | ## Step 1 — Check freshness | 43 | 128 | 946 | - | - |
| workflows/context-pack.md | ## Step 2 — Build | 58 | 154 | 1241 | - | - |
| workflows/context-pack.md | ## Step 3 — Report | 96 | 37 | 243 | - | - |
| workflows/onboard-legacy-project.md | (preamble) | 1 | 51 | 426 | - | - |
| workflows/onboard-legacy-project.md | ## Guard | 10 | 119 | 1017 | - | - |
| workflows/onboard-legacy-project.md | ## Phase 0 — Pre-flight | 25 | 107 | 691 | - | - |
| workflows/onboard-legacy-project.md | ## Phase 1 — Codebase Exploration | 51 | 326 | 2481 | - | - |
| workflows/onboard-legacy-project.md | ## Phase 2 — Write Knowledge Base Files | 80 | 588 | 4398 | - | - |
| workflows/onboard-legacy-project.md | ## Phase 3 — Quality Check | 158 | 76 | 581 | - | - |
| workflows/onboard-legacy-project.md | ## Phase 4 — Report | 168 | 79 | 580 | - | - |
| workflows/pae-finalize.md | (preamble) | 1 | 44 | 337 | - | - |
| workflows/pae-finalize.md | ## Guard | 13 | 96 | 705 | - | - |
| workflows/pae-finalize.md | ## Context Bootstrap | 27 | 34 | 281 | - | - |
| workflows/pae-finalize.md | ## Instructions | 33 | 312 | 2329 | - | - |
| workflows/pae-implement.md | (preamble) | 1 | 82 | 558 | - | - |
| workflows/pae-implement.md | ## Guard | 16 | 304 | 2091 | - | - |
| workflows/pae-implement.md | ## Pre-check | 38 | 474 | 3402 | - | - |
| workflows/pae-implement.md | ## Execute Steps | 88 | 139 | 993 | - | - |
| workflows/pae-implement.md | ## Test Set Discipline (GREEN) | 105 | 131 | 796 | - | - |
| workflows/pae-implement.md | ## Tripwire Check (composite promotion) | 123 | 402 | 2712 | - | - |
| workflows/pae-implement.md | ## Final Verification | 156 | 409 | 2901 | - | - |
| workflows/pae-tests.md | (preamble) | 1 | 129 | 1015 | - | - |
| workflows/pae-tests.md | ## Guard | 21 | 213 | 1577 | - | - |
| workflows/pae-tests.md | ## Pre-check | 48 | 186 | 1400 | - | - |
| workflows/pae-tests.md | ## Step 1 — Test-level gate | 74 | 299 | 2092 | - | - |
| workflows/pae-tests.md | ## Step 2 — Derive the test plan | 118 | 174 | 1188 | - | - |
| workflows/pae-tests.md | ## Step 3 — Write the tests | 146 | 159 | 1083 | - | - |
| workflows/pae-tests.md | ## Step 4 — Observe RED | 169 | 545 | 3505 | - | - |
| workflows/pae-tests.md | ## Report | 235 | 106 | 759 | - | - |
| workflows/pav-check.md | (preamble) | 1 | 43 | 331 | - | - |
| workflows/pav-check.md | ## Guard | 13 | 66 | 477 | - | - |
| workflows/pav-check.md | ## Context Bootstrap | 22 | 93 | 699 | - | - |
| workflows/pav-check.md | ## Instructions | 36 | 777 | 5349 | - | - |
| workflows/pav-close.md | (preamble) | 1 | 50 | 361 | - | - |
| workflows/pav-close.md | ## Guard | 13 | 40 | 283 | - | - |
| workflows/pav-close.md | ## Pre-check | 21 | 50 | 392 | - | - |
| workflows/pav-close.md | ## Instructions | 30 | 397 | 2832 | - | - |
| workflows/pav-propose.md | (preamble) | 1 | 132 | 1024 | - | - |
| workflows/pav-propose.md | ## Guard | 22 | 40 | 283 | - | - |
| workflows/pav-propose.md | ## Pre-check | 30 | 40 | 294 | - | - |
| workflows/pav-propose.md | ## Instructions | 38 | 380 | 2698 | - | - |
| workflows/pd-analyze.md | (preamble) | 1 | 51 | 429 | - | - |
| workflows/pd-analyze.md | ## Guard | 11 | 40 | 302 | - | - |
| workflows/pd-analyze.md | ## Instructions | 18 | 706 | 5385 | - | - |
| workflows/pd-archive.md | (preamble) | 1 | 39 | 356 | - | - |
| workflows/pd-archive.md | ## Guard | 11 | 70 | 514 | - | - |
| workflows/pd-archive.md | ## Instructions | 21 | 235 | 1758 | - | - |
| workflows/pd-decompose.md | (preamble) | 1 | 50 | 412 | - | - |
| workflows/pd-decompose.md | ## Guard | 12 | 66 | 494 | - | - |
| workflows/pd-decompose.md | ## Instructions | 21 | 1227 | 9102 | - | - |
| workflows/pd-design.md | (preamble) | 1 | 54 | 460 | - | - |
| workflows/pd-design.md | ## Guard | 12 | 77 | 573 | - | - |
| workflows/pd-design.md | ## Instructions | 22 | 368 | 2954 | - | - |
| workflows/pd-finalize.md | (preamble) | 1 | 50 | 416 | - | - |
| workflows/pd-finalize.md | ## Guard | 12 | 135 | 1017 | - | - |
| workflows/pd-finalize.md | ## Instructions | 23 | 799 | 6082 | - | - |
| workflows/pd-select-model.md | (preamble) | 1 | 113 | 857 | - | - |
| workflows/pd-select-model.md | ## Guard | 17 | 91 | 664 | - | - |
| workflows/pd-select-model.md | ## Instructions | 28 | 2296 | 17202 | - | - |
| workflows/pe-execute.md | (preamble) | 1 | 35 | 268 | - | - |
| workflows/pe-execute.md | ## Guard | 12 | 72 | 512 | - | - |
| workflows/pe-execute.md | ## Context Bootstrap | 21 | 44 | 328 | - | - |
| workflows/pe-execute.md | ## Instructions | 27 | 618 | 4818 | - | - |
| workflows/pe-execute.md | ## Execution Report persistence | 93 | 118 | 871 | - | - |
| workflows/pe-finalize.md | (preamble) | 1 | 32 | 250 | - | - |
| workflows/pe-finalize.md | ## Guard | 12 | 42 | 295 | - | - |
| workflows/pe-finalize.md | ## Context Bootstrap | 20 | 27 | 218 | - | - |
| workflows/pe-finalize.md | ## Instructions | 25 | 759 | 5893 | - | - |
| workflows/phase-atomic-execution.md | (preamble) | 1 | 88 | 707 | - | - |
| workflows/phase-atomic-execution.md | ## Context Bootstrap | 20 | 129 | 962 | - | - |
| workflows/phase-atomic-execution.md | ## Guard | 38 | 370 | 2647 | - | - |
| workflows/phase-atomic-execution.md | ## Execution | 69 | 440 | 3248 | - | - |
| workflows/phase-atomic-validation.md | (preamble) | 1 | 107 | 854 | - | - |
| workflows/phase-atomic-validation.md | ## Context Bootstrap | 19 | 124 | 946 | - | - |
| workflows/phase-atomic-validation.md | ## Guard | 37 | 294 | 1986 | - | - |
| workflows/phase-atomic-validation.md | ## Execution | 71 | 139 | 1028 | - | - |
| workflows/phase-composite-validation.md | (preamble) | 1 | 73 | 616 | - | - |
| workflows/phase-composite-validation.md | ## Context Bootstrap | 16 | 110 | 823 | - | - |
| workflows/phase-composite-validation.md | ## Guard | 29 | 184 | 1370 | - | - |
| workflows/phase-composite-validation.md | ## Step 1 — Integration check | 51 | 158 | 1195 | - | - |
| workflows/phase-composite-validation.md | ## Step 2 — Verdict and close / fix | 72 | 636 | 4597 | - | - |
| workflows/phase-discovery.md | (preamble) | 1 | 52 | 426 | - | - |
| workflows/phase-discovery.md | ## Execution Modes | 11 | 230 | 1590 | - | - |
| workflows/phase-discovery.md | ## Context Bootstrap | 42 | 37 | 280 | - | - |
| workflows/phase-discovery.md | ## Guard | 48 | 79 | 573 | - | - |
| workflows/phase-discovery.md | ## Step 0 — Bootstrap | 58 | 614 | 4466 | - | - |
| workflows/phase-discovery.md | ## Run Logging | 133 | 115 | 883 | - | - |
| workflows/phase-discovery.md | ## Step 0.5 — Resume Check (if state.md existed) | 148 | 132 | 872 | - | - |
| workflows/phase-discovery.md | ## Execution | 163 | 178 | 1269 | - | - |
| workflows/phase-execution.md | (preamble) | 1 | 55 | 434 | - | - |
| workflows/phase-execution.md | ## Run Logging | 16 | 229 | 1653 | - | - |
| workflows/phase-execution.md | ## Context Bootstrap | 51 | 38 | 282 | - | - |
| workflows/phase-execution.md | ## Guard | 59 | 153 | 1062 | - | - |
| workflows/phase-execution.md | ## Execution | 82 | 204 | 1475 | - | - |
| workflows/phase-pipeline.md | (preamble) | 1 | 57 | 457 | - | - |
| workflows/phase-pipeline.md | ## Guard | 11 | 40 | 264 | - | - |
| workflows/phase-pipeline.md | ## Run Logging | 17 | 112 | 901 | - | - |
| workflows/phase-pipeline.md | ## Pipeline Overrides | 38 | 402 | 2821 | - | - |
| workflows/phase-pipeline.md | ## Deep Architectural Analysis Protocol | 78 | 45 | 350 | - | - |
| workflows/phase-pipeline.md | ## Step 0 — Bootstrap | 85 | 172 | 1161 | - | - |
| workflows/phase-pipeline.md | ## Phase 1 — Discovery | 102 | 101 | 741 | - | - |
| workflows/phase-pipeline.md | ## Phase 2 — Execution | 118 | 84 | 778 | - | - |
| workflows/phase-pipeline.md | ## Phase 3 — Validation | 137 | 59 | 494 | - | - |
| workflows/phase-pipeline.md | ## Final Report | 151 | 45 | 339 | - | - |
| workflows/phase-pipeline.md | ## Interruption Recovery | 158 | 28 | 204 | - | - |
| workflows/phase-validation.md | (preamble) | 1 | 66 | 565 | - | - |
| workflows/phase-validation.md | ## Run Logging | 17 | 213 | 1591 | - | - |
| workflows/phase-validation.md | ## Context Bootstrap | 52 | 38 | 283 | - | - |
| workflows/phase-validation.md | ## Guard | 60 | 168 | 1162 | - | - |
| workflows/phase-validation.md | ## Execution | 83 | 192 | 1452 | - | - |
| workflows/pv-classify-fixes.md | (preamble) | 1 | 39 | 322 | - | - |
| workflows/pv-classify-fixes.md | ## Guard | 12 | 78 | 551 | - | - |
| workflows/pv-classify-fixes.md | ## Classification | 24 | 383 | 2535 | - | - |
| workflows/pv-classify-fixes.md | ## Output | 71 | 167 | 1083 | - | - |
| workflows/pv-contract.md | (preamble) | 1 | 32 | 273 | - | - |
| workflows/pv-contract.md | ## Guard | 12 | 53 | 390 | - | - |
| workflows/pv-contract.md | ## Context Bootstrap | 20 | 38 | 283 | - | - |
| workflows/pv-contract.md | ## Instructions | 28 | 388 | 2571 | - | - |
| workflows/pv-create-fixes.md | (preamble) | 1 | 32 | 260 | - | - |
| workflows/pv-create-fixes.md | ## Guard | 12 | 128 | 929 | - | - |
| workflows/pv-create-fixes.md | ## Context Bootstrap | 27 | 28 | 216 | - | - |
| workflows/pv-create-fixes.md | ## Instructions | 32 | 996 | 6931 | - | - |
| workflows/pv-execute-fixes.md | (preamble) | 1 | 33 | 265 | - | - |
| workflows/pv-execute-fixes.md | ## Guard | 12 | 110 | 745 | - | - |
| workflows/pv-execute-fixes.md | ## Context Bootstrap | 24 | 29 | 220 | - | - |
| workflows/pv-execute-fixes.md | ## Instructions | 29 | 228 | 1723 | - | - |
| workflows/pv-finalize.md | (preamble) | 1 | 32 | 257 | workflow | workflows/validation-finalize.md |
| workflows/pv-finalize.md | ## Guard | 12 | 131 | 1016 | workflow | workflows/validation-finalize.md |
| workflows/pv-finalize.md | ## Context Bootstrap | 27 | 37 | 303 | workflow | workflows/validation-finalize.md |
| workflows/pv-finalize.md | ## Instructions | 33 | 1034 | 8036 | contract | workflows/validation-finalize.md |
| workflows/pv-issues.md | (preamble) | 1 | 37 | 277 | - | - |
| workflows/pv-issues.md | ## Guard | 12 | 64 | 441 | - | - |
| workflows/pv-issues.md | ## Instructions | 21 | 199 | 1374 | - | - |
| workflows/pv-review.md | (preamble) | 1 | 33 | 270 | - | - |
| workflows/pv-review.md | ## Guard | 12 | 124 | 880 | - | - |
| workflows/pv-review.md | ## Context Bootstrap | 25 | 38 | 283 | - | - |
| workflows/pv-review.md | ## Instructions | 33 | 354 | 2593 | - | - |
| workflows/restack.md | (preamble) | 1 | 112 | 792 | workflow | workflows/restack.md |
| workflows/restack.md | ## Guard | 13 | 286 | 2034 | workflow | workflows/restack.md |
| workflows/restack.md | ## Recovery journal | 42 | 518 | 3760 | contract | workflows/restack.md |
| workflows/restack.md | ## Step 1 — Classify each branch | 113 | 195 | 1290 | workflow | workflows/restack.md |
| workflows/restack.md | ## Step 2 — Replay | 134 | 262 | 1792 | workflow | workflows/restack.md |
| workflows/restack.md | ## Step 3 — Publish (only with `--allow-pr`) | 163 | 90 | 654 | workflow | workflows/restack.md |
| workflows/restack.md | ## Step 4 — Report | 175 | 43 | 297 | workflow | workflows/restack.md |
| workflows/retro.md | (preamble) | 1 | 101 | 720 | - | - |
| workflows/retro.md | ## Guard | 17 | 110 | 765 | - | - |
| workflows/retro.md | ## Step 1 — Load | 31 | 1125 | 9033 | - | - |
| workflows/retro.md | ## Step 2 — Compute | 183 | 1923 | 13521 | - | - |
| workflows/retro.md | ## Step 3 — Find what to change | 390 | 223 | 1497 | - | - |
| workflows/retro.md | ## Step 4 — Report | 416 | 253 | 1848 | - | - |
| workflows/retro.md | ## Honesty rules | 463 | 91 | 506 | - | - |
| workflows/spec-draft.md | (preamble) | 1 | 70 | 554 | - | - |
| workflows/spec-draft.md | ## Flags | 11 | 74 | 495 | - | - |
| workflows/spec-draft.md | ## Step 0 — Resolve the input | 23 | 131 | 878 | - | - |
| workflows/spec-draft.md | ## Guard | 36 | 139 | 978 | - | - |
| workflows/spec-draft.md | ## Step 1 — Context bootstrap | 51 | 80 | 605 | - | - |
| workflows/spec-draft.md | ## Step 2 — Codebase reconnaissance | 65 | 74 | 536 | - | - |
| workflows/spec-draft.md | ## Step 3 — Ambiguity scan | 75 | 125 | 870 | - | - |
| workflows/spec-draft.md | ## Step 4A — Resolution, --auto-mode | 92 | 103 | 725 | - | - |
| workflows/spec-draft.md | ## Step 4B — Resolution, --brain-storm (default) | 111 | 235 | 1619 | - | - |
| workflows/spec-draft.md | ## Blocker escalation | 138 | 89 | 652 | - | - |
| workflows/spec-draft.md | ## Step 5 — Write the specification | 152 | 458 | 2913 | - | - |
| workflows/spec-draft.md | ## Step 6 — Devil's Advocate review | 200 | 793 | 4434 | - | - |
| workflows/spec-draft.md | ## Step 7 — Readiness gate | 283 | 287 | 1587 | - | - |
| workflows/spec-draft.md | ## Step 8 — Report and stop | 313 | 71 | 554 | - | - |
| workflows/spec-draft.md | ## Re-running on an existing spec | 323 | 78 | 494 | - | - |
| workflows/spec-run.md | (preamble) | 1 | 145 | 1114 | - | - |
| workflows/spec-run.md | ## Repository mode | 19 | 292 | 2081 | - | - |
| workflows/spec-run.md | ## Guard | 52 | 51 | 369 | - | - |
| workflows/spec-run.md | ## Run Logging | 61 | 230 | 1696 | - | - |
| workflows/spec-run.md | ## Step 0 — Preflight and resume | 95 | 360 | 2586 | - | - |
| workflows/spec-run.md | ## Step 1 — Discovery, with the batch gate | 131 | 311 | 2125 | - | - |
| workflows/spec-run.md | ## Step 2 — Model selection | 167 | 397 | 2978 | - | - |
| workflows/spec-run.md | ## Step 3 — Resolve the stack | 209 | 329 | 2559 | - | - |
| workflows/spec-run.md | ## Step 4 — Subtask loop | 259 | 1475 | 10233 | - | - |
| workflows/spec-run.md | ## Step 5 — Task-level validation | 411 | 101 | 794 | - | - |
| workflows/spec-run.md | ## Step 6 — Fix-tasks | 424 | 111 | 794 | - | - |
| workflows/spec-run.md | ## Step 7 — Promote pull requests | 438 | 82 | 511 | - | - |
| workflows/spec-run.md | ## Step 8 — Final report | 450 | 155 | 1085 | - | - |
| workflows/spec-run.md | ## What this workflow never does | 469 | 129 | 764 | - | - |
| workflows/spec-run.md | ## Interruption recovery | 484 | 106 | 694 | - | - |
| workflows/spec-sync.md | (preamble) | 1 | 73 | 601 | - | - |
| workflows/spec-sync.md | ## Guard | 13 | 147 | 1043 | - | - |
| workflows/spec-sync.md | ## Step 1 — Build the delta | 28 | 250 | 1781 | - | - |
| workflows/spec-sync.md | ## Step 2 — Decide what the spec should say | 63 | 85 | 587 | - | - |
| workflows/spec-sync.md | ## Step 3 — Write the spec | 74 | 134 | 873 | - | - |
| workflows/spec-sync.md | ## Step 4 — Record and report | 88 | 95 | 674 | - | - |
| workflows/suggest-commit-message.md | (preamble) | 1 | 62 | 442 | - | - |
| workflows/suggest-commit-message.md | ## Guard | 11 | 31 | 208 | - | - |
| workflows/suggest-commit-message.md | ## Step 0 — Gather Diff Context | 17 | 196 | 1222 | - | - |
| workflows/suggest-commit-message.md | ## Step 2 — Analyse Changes | 39 | 47 | 298 | - | - |
| workflows/suggest-commit-message.md | ## Step 3 — Draft Commit Message | 45 | 76 | 488 | - | - |
| workflows/suggest-commit-message.md | ## Step 4 — Flag Concerns | 59 | 41 | 283 | - | - |
| workflows/suggest-commit-pr.md | (preamble) | 1 | 26 | 181 | - | - |
| workflows/suggest-commit-pr.md | ## Guard | 7 | 92 | 622 | - | - |
| workflows/suggest-pr-description.md | (preamble) | 1 | 40 | 285 | - | - |
| workflows/suggest-pr-description.md | ## Guard | 10 | 31 | 208 | - | - |
| workflows/suggest-pr-description.md | ## Step 0 — Gather Diff Context | 16 | 48 | 360 | - | - |
| workflows/suggest-pr-description.md | ## Step 2 — Analyse Changes | 23 | 41 | 297 | - | - |
| workflows/suggest-pr-description.md | ## Step 3 — Draft PR Description | 29 | 149 | 1015 | - | - |
| workflows/suggest-pr-description.md | ## Step 4 — Flag Concerns | 53 | 22 | 131 | - | - |

### References

| Class | resolved | resolved-prefix | heading-unmarked | missing-heading | missing-target | missing-path | unknown-command | glob-empty | ambiguous-stem |
|---|---|---|---|---|---|---|---|---|---|
| active | 2880 | 2 | 9 | 7 | 7 | 8 | 3 | 0 | 146 |
| frozen | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| planning | 2090 | 2 | 1 | 6 | 167 | 289 | 63 | 12 | 37 |
| history | 1148 | 1 | 1 | 10 | 20 | 13 | 8 | 0 | 15 |

| Source:line:column | Raw | Form | Context | Status | Candidates | Findings |
|---|---|---|---|---|---|---|
| .ai/context/integrations.md:16:65 | global-claude.md | md-name | span | resolved | rules/global-claude.md | AUD-08-071 |
| .ai/context/runbook.md:81:61 | PIPELINE.md | md-name | span | resolved | workflows/PIPELINE.md | AUD-08-071 |
| .ai/context/runbook.md:105:10 | compress-state.md | md-name | span | resolved | workflows/compress-state.md | AUD-08-071 |
| .ai/context/runbook.md:145:5 | workflow-globals → Canonical Status Formats | section-ref | span | heading-unmarked | rules/workflow-globals.md (heading-unmarked) | AUD-08-062 |
| .ai/memory/architecture.md:34:3 | workflow-globals.md | md-name | span | resolved | rules/workflow-globals.md | AUD-08-071 |
| .ai/memory/architecture.md:35:3 | workflow-reference.md | md-name | span | resolved | rules/workflow-reference.md | AUD-08-071 |
| .ai/memory/architecture.md:36:3 | tdd.md | md-name | span | resolved | rules/tdd.md | AUD-08-071 |
| .ai/memory/architecture.md:37:3 | git-flow.md | md-name | span | resolved | rules/git-flow.md | AUD-08-071 |
| .ai/memory/architecture.md:38:3 | orchestration.md | md-name | span | resolved | rules/orchestration.md | AUD-08-071 |
| .ai/memory/architecture.md:39:3 | quick-flow.md | md-name | span | resolved | rules/quick-flow.md | AUD-08-071 |
| .ai/memory/architecture.md:40:3 | run-log.md | md-name | span | resolved | rules/run-log.md | AUD-08-071 |
| .ai/memory/architecture.md:41:3 | language.md | md-name | span | resolved | rules/language.md | AUD-08-071 |
| .ai/memory/architecture.md:43:3 | global-claude.md | md-name | span | resolved | rules/global-claude.md | AUD-08-071 |
| .ai/memory/architecture.md:164:32 | workflow-globals → Workflow-declared mode overrides | section-ref | span | missing-heading | rules/workflow-globals.md (missing-heading) | AUD-08-036 |
| .ai/principles/architecture.md:41:23 | workflow-globals → Workflow-declared mode overrides | section-ref | span | missing-heading | rules/workflow-globals.md (missing-heading) | AUD-08-036 |
| .ai/principles/architecture.md:48:65 | file → ## Section | section-ref | span | missing-target | none | AUD-08-072 |
| .ai/principles/architecture.md:87:19 | global-claude.md | md-name | span | resolved | rules/global-claude.md | AUD-08-071 |
| .ai/principles/coding.md:31:21 | rule-name | rule-name | span | missing-target | none | AUD-08-072 |
| .ai/principles/coding.md:31:55 | file → ## Section | section-ref | span | missing-target | none | AUD-08-072 |
| .ai/principles/coding.md:46:14 | file → ## Section | section-ref | span | missing-target | none | AUD-08-072 |
| .ai/principles/coding.md:46:43 | file → ## Section → ### Subsection | section-ref | span | missing-target | none | AUD-08-072 |
| .ai/principles/coding.md:51:36 | file → ## Section | section-ref | span | missing-target | none | AUD-08-072 |
| .ai/principles/coding.md:57:21 | PIPELINE.md | md-name | span | resolved | workflows/PIPELINE.md | AUD-08-071 |
| .ai/principles/coding.md:95:44 | PIPELINE.md | md-name | span | resolved | workflows/PIPELINE.md | AUD-08-071 |
| .ai/principles/domain.md:49:26 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-006 |
| docs/MODEL-CATALOG.md:10:2 | workflow-reference → Model columns and resolution | section-ref | span | heading-unmarked | rules/workflow-reference.md (heading-unmarked) | AUD-08-062 |
| docs/MODEL-CATALOG.md:10:63 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-071 |
| docs/MODEL-CATALOG.md:48:40 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-071 |
| docs/USAGE.md:18:35 | workflow-globals.md | md-name | span | resolved | rules/workflow-globals.md | AUD-08-070 |
| docs/USAGE.md:18:58 | language.md | md-name | span | resolved | rules/language.md | AUD-08-070 |
| docs/USAGE.md:433:64 | workflow-globals.md | md-name | span | resolved | rules/workflow-globals.md | AUD-08-070 |
| docs/USAGE.md:653:42 | retro.md | md-name | text | resolved | workflows/retro.md | AUD-08-070 |
| docs/USAGE.md:689:67 | /x | command | span | unknown-command | none | AUD-08-072 |
| docs/USAGE.md:748:3 | workflow-globals.md | md-name | span | resolved | rules/workflow-globals.md | AUD-08-070 |
| docs/USAGE.md:748:188 | workflow-reference.md | md-name | span | resolved | rules/workflow-reference.md | AUD-08-070 |
| docs/USAGE.md:749:3 | workflow-reference.md | md-name | span | resolved | rules/workflow-reference.md | AUD-08-070 |
| docs/USAGE.md:750:3 | language.md | md-name | span | resolved | rules/language.md | AUD-08-070 |
| docs/USAGE.md:751:3 | git-flow.md | md-name | span | resolved | rules/git-flow.md | AUD-08-070 |
| docs/USAGE.md:752:3 | orchestration.md | md-name | span | resolved | rules/orchestration.md | AUD-08-070 |
| docs/USAGE.md:753:3 | tdd.md | md-name | span | resolved | rules/tdd.md | AUD-08-070 |
| docs/USAGE.md:754:3 | run-log.md | md-name | span | resolved | rules/run-log.md | AUD-08-070 |
| docs/USAGE.md:755:3 | quick-flow.md | md-name | span | resolved | rules/quick-flow.md | AUD-08-070 |
| docs/USAGE.md:756:3 | phase-discovery.md | md-name | span | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-070 |
| docs/USAGE.md:756:25 | phase-execution.md | md-name | span | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-070 |
| docs/USAGE.md:756:47 | phase-validation.md | md-name | span | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-070 |
| docs/USAGE.md:756:70 | phase-atomic-execution.md | md-name | span | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-070 |
| docs/USAGE.md:756:99 | phase-atomic-validation.md | md-name | span | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-070 |
| docs/USAGE.md:757:3 | global-claude.md | md-name | span | resolved | rules/global-claude.md | AUD-08-070 |
| docs/USAGE.md:772:3 | PIPELINE.md | md-name | span | resolved | workflows/PIPELINE.md | AUD-08-070 |
| docs/USAGE.md:773:3 | phase-pipeline.md | md-name | span | resolved | workflows/phase-pipeline.md | AUD-08-070 |
| docs/USAGE.md:774:3 | phase-discovery.md | md-name | span | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-070 |
| docs/USAGE.md:775:3 | phase-execution.md | md-name | span | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-070 |
| docs/USAGE.md:776:3 | phase-validation.md | md-name | span | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-070 |
| docs/USAGE.md:777:3 | phase-atomic-execution.md | md-name | span | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-070 |
| docs/USAGE.md:778:3 | phase-atomic-validation.md | md-name | span | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-070 |
| docs/USAGE.md:779:3 | pd-analyze.md | md-name | span | resolved | workflows/pd-analyze.md | AUD-08-070 |
| docs/USAGE.md:780:3 | pd-decompose.md | md-name | span | resolved | workflows/pd-decompose.md | AUD-08-070 |
| docs/USAGE.md:781:3 | pd-design.md | md-name | span | resolved | workflows/pd-design.md | AUD-08-070 |
| docs/USAGE.md:782:3 | pd-finalize.md | md-name | span | resolved | workflows/pd-finalize.md | AUD-08-070 |
| docs/USAGE.md:783:3 | pd-archive.md | md-name | span | resolved | workflows/pd-archive.md | AUD-08-070 |
| docs/USAGE.md:784:3 | pd-select-model.md | md-name | span | resolved | workflows/pd-select-model.md | AUD-08-070 |
| docs/USAGE.md:785:3 | pe-execute.md | md-name | span | resolved | workflows/pe-execute.md | AUD-08-070 |
| docs/USAGE.md:786:3 | pe-finalize.md | md-name | span | resolved | workflows/pe-finalize.md | AUD-08-070 |
| docs/USAGE.md:787:3 | pv-contract.md | md-name | span | resolved | workflows/pv-contract.md | AUD-08-070 |
| docs/USAGE.md:788:3 | pv-review.md | md-name | span | resolved | workflows/pv-review.md | AUD-08-070 |
| docs/USAGE.md:789:3 | pv-issues.md | md-name | span | resolved | workflows/pv-issues.md | AUD-08-070 |
| docs/USAGE.md:790:3 | pv-create-fixes.md | md-name | span | resolved | workflows/pv-create-fixes.md | AUD-08-070 |
| docs/USAGE.md:791:3 | pv-execute-fixes.md | md-name | span | resolved | workflows/pv-execute-fixes.md | AUD-08-070 |
| docs/USAGE.md:792:3 | pv-finalize.md | md-name | span | resolved | workflows/pv-finalize.md | AUD-08-070 |
| docs/USAGE.md:793:3 | pae-tests.md | md-name | span | resolved | workflows/pae-tests.md | AUD-08-070 |
| docs/USAGE.md:794:3 | pae-implement.md | md-name | span | resolved | workflows/pae-implement.md | AUD-08-070 |
| docs/USAGE.md:795:3 | pae-finalize.md | md-name | span | resolved | workflows/pae-finalize.md | AUD-08-070 |
| docs/USAGE.md:796:3 | pav-check.md | md-name | span | resolved | workflows/pav-check.md | AUD-08-070 |
| docs/USAGE.md:797:3 | pav-propose.md | md-name | span | resolved | workflows/pav-propose.md | AUD-08-070 |
| docs/USAGE.md:798:3 | pav-close.md | md-name | span | resolved | workflows/pav-close.md | AUD-08-070 |
| docs/USAGE.md:799:3 | spec-draft.md | md-name | span | resolved | workflows/spec-draft.md | AUD-08-070 |
| docs/USAGE.md:800:3 | spec-sync.md | md-name | span | resolved | workflows/spec-sync.md | AUD-08-070 |
| docs/USAGE.md:801:3 | bugfix.md | md-name | span | resolved | workflows/bugfix.md | AUD-08-070 |
| docs/USAGE.md:802:3 | adr-new.md | md-name | span | resolved | workflows/adr-new.md | AUD-08-070 |
| docs/USAGE.md:803:3 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-070 |
| docs/USAGE.md:803:99 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-006 |
| docs/USAGE.md:804:3 | retro.md | md-name | span | resolved | workflows/retro.md | AUD-08-070 |
| docs/USAGE.md:805:3 | spec-run.md | md-name | span | resolved | workflows/spec-run.md | AUD-08-070 |
| docs/USAGE.md:806:3 | restack.md | md-name | span | resolved | workflows/restack.md | AUD-08-070 |
| docs/USAGE.md:807:3 | pv-classify-fixes.md | md-name | span | resolved | workflows/pv-classify-fixes.md | AUD-08-070 |
| docs/USAGE.md:808:3 | phase-composite-validation.md | md-name | span | resolved | workflows/phase-composite-validation.md | AUD-08-070 |
| docs/USAGE.md:809:3 | onboard-legacy-project.md | md-name | span | resolved | workflows/onboard-legacy-project.md | AUD-08-070 |
| docs/USAGE.md:810:3 | suggest-commit-message.md | md-name | span | resolved | workflows/suggest-commit-message.md | AUD-08-070 |
| docs/USAGE.md:811:3 | suggest-pr-description.md | md-name | span | resolved | workflows/suggest-pr-description.md | AUD-08-070 |
| docs/USAGE.md:812:3 | suggest-commit-pr.md | md-name | span | resolved | workflows/suggest-commit-pr.md | AUD-08-070 |
| docs/USAGE.md:813:3 | compress-state.md | md-name | span | resolved | workflows/compress-state.md | AUD-08-070 |
| principles/infra-standards.md:195:21 | /metrics | command | span | unknown-command | none | AUD-08-072 |
| principles/testing-standards.md:63:15 | /pae-implement → Final Verification | section-ref | span | heading-unmarked | workflows/pae-implement.md (heading-unmarked) | AUD-08-062 |
| rules/git-flow.md:279:1 | workflow-globals → Canonical Status Formats | section-ref | span | heading-unmarked | rules/workflow-globals.md (heading-unmarked) | AUD-08-001 |
| rules/git-flow.md:280:1 | workflow-reference → Protected Sections Contract | section-ref | span | heading-unmarked | rules/workflow-reference.md (heading-unmarked) | AUD-08-001 |
| rules/phase-atomic-validation.md:21:27 | phase-atomic-execution → ## Context Bootstrap | section-ref | span | ambiguous-stem | rules/phase-atomic-execution.md (resolved), workflows/phase-atomic-execution.md (resolved) | AUD-08-002 |
| rules/phase-discovery.md:46:20 | /phase-discovery → ## Execution Modes | section-ref | span | ambiguous-stem | rules/phase-discovery.md (missing-heading), workflows/phase-discovery.md (resolved) | AUD-08-003 |
| rules/quick-flow.md:21:27 | workflow-globals → Never auto-advance between phases | section-ref | span | missing-heading | rules/workflow-globals.md (missing-heading) | AUD-08-004 |
| rules/quick-flow.md:22:48 | workflow-globals → Test-first execution | section-ref | span | missing-heading | rules/workflow-globals.md (missing-heading) | AUD-08-004 |
| rules/tdd.md:35:1 | workflow-globals → Canonical Status Formats | section-ref | span | heading-unmarked | rules/workflow-globals.md (heading-unmarked) | AUD-08-005 |
| rules/tdd.md:201:5 | quick-flow → The quick path | section-ref | span | heading-unmarked | rules/quick-flow.md (heading-unmarked) | AUD-08-005 |
| rules/workflow-globals.md:44:46 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-006 |
| scripts/README.md:53:46 | retro.md | md-name | text | resolved | workflows/retro.md | AUD-08-069 |
| scripts/check-repo-set.py:658:31 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-069 |
| scripts/check-spec-draft.sh:9:38 | spec-draft.md | md-name | text | resolved | workflows/spec-draft.md | AUD-08-069 |
| scripts/setup-new-project.sh:89:12 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:32 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:54 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:66 | quick-flow.md | md-name | text | resolved | rules/quick-flow.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:80 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:87 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:98 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-068 |
| scripts/setup-new-project.sh:89:110 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-068 |
| scripts/setup-new-project.sh:90:12 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-068 |
| scripts/setup-new-project.sh:90:31 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-068 |
| scripts/setup-new-project.sh:90:50 | phase-validation.md | md-name | text | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-068 |
| scripts/setup-new-project.sh:91:12 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-068 |
| scripts/setup-new-project.sh:91:38 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-068 |
| scripts/setup-new-project.sh:104:27 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/setup-new-project.sh:105:24 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/setup-new-project.sh:118:35 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:12 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:32 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:54 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:66 | quick-flow.md | md-name | text | resolved | rules/quick-flow.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:80 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:87 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:98 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-068 |
| scripts/setup-new-project.sh:124:110 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-068 |
| scripts/setup-new-project.sh:125:12 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-068 |
| scripts/setup-new-project.sh:125:31 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-068 |
| scripts/setup-new-project.sh:125:50 | phase-validation.md | md-name | text | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-068 |
| scripts/setup-new-project.sh:126:12 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-068 |
| scripts/setup-new-project.sh:126:38 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-068 |
| scripts/sync.sh:61:26 | harness/capabilities.md | path | text | missing-path | none | AUD-08-068 |
| scripts/sync.sh:62:24 | harness/capabilities.md | path | text | missing-path | none | AUD-08-068 |
| scripts/sync.sh:100:11 | global-claude.md | md-name | text | resolved | rules/global-claude.md | AUD-08-068 |
| scripts/sync.sh:208:14 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-068 |
| scripts/sync.sh:208:34 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-068 |
| scripts/sync.sh:208:56 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/sync.sh:208:68 | quick-flow.md | md-name | text | resolved | rules/quick-flow.md | AUD-08-068 |
| scripts/sync.sh:208:82 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-068 |
| scripts/sync.sh:208:89 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-068 |
| scripts/sync.sh:208:100 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-068 |
| scripts/sync.sh:208:112 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-068 |
| scripts/sync.sh:209:14 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-068 |
| scripts/sync.sh:209:33 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-068 |
| scripts/sync.sh:209:52 | phase-validation.md | md-name | text | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-068 |
| scripts/sync.sh:210:14 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-068 |
| scripts/sync.sh:210:40 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-068 |
| scripts/sync.sh:218:16 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-068 |
| scripts/sync.sh:218:36 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-068 |
| scripts/sync.sh:218:58 | language.md | md-name | text | resolved | rules/language.md | AUD-08-068 |
| scripts/sync.sh:218:70 | quick-flow.md | md-name | text | resolved | rules/quick-flow.md | AUD-08-068 |
| scripts/sync.sh:218:84 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-068 |
| scripts/sync.sh:218:91 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-068 |
| scripts/sync.sh:218:102 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-068 |
| scripts/sync.sh:218:114 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-068 |
| scripts/sync.sh:219:16 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-068 |
| scripts/sync.sh:219:35 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-068 |
| scripts/sync.sh:219:54 | phase-validation.md | md-name | text | ambiguous-stem | rules/phase-validation.md, workflows/phase-validation.md | AUD-08-068 |
| scripts/sync.sh:220:16 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-068 |
| scripts/sync.sh:220:42 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-068 |
| scripts/validate-contracts.sh:607:91 | pd-analyze.md | md-name | text | resolved | workflows/pd-analyze.md | AUD-08-066 |
| scripts/validate-contracts.sh:610:100 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:613:92 | pd-design.md | md-name | text | resolved | workflows/pd-design.md | AUD-08-066 |
| scripts/validate-contracts.sh:616:97 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:619:94 | pe-execute.md | md-name | text | resolved | workflows/pe-execute.md | AUD-08-066 |
| scripts/validate-contracts.sh:622:93 | pv-contract.md | md-name | text | resolved | workflows/pv-contract.md | AUD-08-066 |
| scripts/validate-contracts.sh:625:88 | pv-review.md | md-name | text | resolved | workflows/pv-review.md | AUD-08-066 |
| scripts/validate-contracts.sh:628:87 | pv-issues.md | md-name | text | resolved | workflows/pv-issues.md | AUD-08-066 |
| scripts/validate-contracts.sh:631:92 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:634:87 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:643:56 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:647:87 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:655:97 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:662:90 | pd-analyze.md | md-name | text | resolved | workflows/pd-analyze.md | AUD-08-066 |
| scripts/validate-contracts.sh:665:101 | pd-analyze.md | md-name | text | resolved | workflows/pd-analyze.md | AUD-08-066 |
| scripts/validate-contracts.sh:670:88 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:673:46 | workflow-reference.md | md-name | comment | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:674:22 | workflow-reference.md | md-name | comment | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:674:49 | workflow-globals.md | md-name | comment | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:695:7 | pd-archive.md | md-name | check-description | resolved | workflows/pd-archive.md | AUD-08-066 |
| scripts/validate-contracts.sh:701:91 | compress-state.md | md-name | text | resolved | workflows/compress-state.md | AUD-08-066 |
| scripts/validate-contracts.sh:706:89 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:709:83 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:712:99 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:714:7 | phase-composite-validation.md | md-name | check-description | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:718:99 | pav-close.md | md-name | text | resolved | workflows/pav-close.md | AUD-08-066 |
| scripts/validate-contracts.sh:721:83 | pe-execute.md | md-name | text | resolved | workflows/pe-execute.md | AUD-08-066 |
| scripts/validate-contracts.sh:724:84 | pe-finalize.md | md-name | text | resolved | workflows/pe-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:727:82 | pae-finalize.md | md-name | text | resolved | workflows/pae-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:735:108 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:738:170 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:741:95 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:746:95 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:749:152 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:760:94 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:763:93 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:766:107 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:769:84 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:772:92 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:775:97 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:778:122 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:781:108 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:784:86 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:787:101 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:793:133 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:796:119 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:798:12 | PIPELINE.md | md-name | check-description | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:799:108 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:802:138 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:807:98 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:810:86 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:813:85 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:816:87 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:819:89 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:822:87 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:825:89 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:833:144 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:841:142 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:844:144 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:849:151 | compress-state.md | md-name | text | resolved | workflows/compress-state.md | AUD-08-066 |
| scripts/validate-contracts.sh:852:101 | compress-state.md | md-name | text | resolved | workflows/compress-state.md | AUD-08-066 |
| scripts/validate-contracts.sh:856:12 | PIPELINE.md | md-name | check-description | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:857:134 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:871:95 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-066 |
| scripts/validate-contracts.sh:874:206 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-066 |
| scripts/validate-contracts.sh:877:89 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:880:91 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:884:90 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:888:84 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:891:90 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:896:227 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:904:193 | pae-finalize.md | md-name | text | resolved | workflows/pae-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:907:85 | pav-check.md | md-name | text | resolved | workflows/pav-check.md | AUD-08-066 |
| scripts/validate-contracts.sh:921:89 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:924:80 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:927:88 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:930:87 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:933:91 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:939:84 | quick-flow.md | md-name | text | resolved | rules/quick-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:942:87 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:945:91 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:948:96 | compress-state.md | md-name | text | resolved | workflows/compress-state.md | AUD-08-066 |
| scripts/validate-contracts.sh:951:97 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:956:12 | PIPELINE.md | md-name | check-description | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:957:81 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:959:36 | tdd.md | md-name | check-description | resolved | rules/tdd.md | AUD-08-066 |
| scripts/validate-contracts.sh:960:105 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-066 |
| scripts/validate-contracts.sh:962:49 | tdd.md | md-name | check-description | resolved | rules/tdd.md | AUD-08-066 |
| scripts/validate-contracts.sh:963:131 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-066 |
| scripts/validate-contracts.sh:966:91 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:989:165 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:997:111 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1000:89 | compress-state.md | md-name | text | resolved | workflows/compress-state.md | AUD-08-066 |
| scripts/validate-contracts.sh:1003:84 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1009:190 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1013:102 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1016:113 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1019:84 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1022:85 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1025:86 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1028:192 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1032:93 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1035:95 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1043:82 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1047:198 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1050:87 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1053:107 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1056:109 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1059:96 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1063:93 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1066:84 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:1072:136 | orchestration.md | md-name | text | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1075:96 | pd-analyze.md | md-name | text | resolved | workflows/pd-analyze.md | AUD-08-066 |
| scripts/validate-contracts.sh:1078:101 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1084:99 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1087:128 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1090:100 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:1094:106 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1097:90 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1102:129 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1105:85 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1108:80 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1112:115 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1115:131 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1118:110 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1121:104 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1124:72 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1135:113 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1146:82 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1150:92 | pv-classify-fixes.md | md-name | text | resolved | workflows/pv-classify-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1153:96 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1156:94 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:1169:96 | pd-select-model.md | md-name | text | resolved | workflows/pd-select-model.md | AUD-08-066 |
| scripts/validate-contracts.sh:1173:26 | git-flow.md | md-name | check-description | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1173:42 | orchestration.md | md-name | check-description | resolved | rules/orchestration.md | AUD-08-066 |
| scripts/validate-contracts.sh:1231:122 | pae-finalize.md | md-name | text | resolved | workflows/pae-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1234:119 | pav-close.md | md-name | text | resolved | workflows/pav-close.md | AUD-08-066 |
| scripts/validate-contracts.sh:1236:12 | rules/phase-discovery | path | check-description | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:1237:19 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-066 |
| scripts/validate-contracts.sh:1240:121 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1243:94 | phase-atomic-execution.md | md-name | text | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-066 |
| scripts/validate-contracts.sh:1256:103 | pae-implement.md | md-name | text | resolved | workflows/pae-implement.md | AUD-08-066 |
| scripts/validate-contracts.sh:1262:88 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:1265:108 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:1268:88 | pav-check.md | md-name | text | resolved | workflows/pav-check.md | AUD-08-066 |
| scripts/validate-contracts.sh:1274:159 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1277:93 | pd-archive.md | md-name | text | resolved | workflows/pd-archive.md | AUD-08-066 |
| scripts/validate-contracts.sh:1282:168 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:1286:99 | pe-finalize.md | md-name | text | resolved | workflows/pe-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1290:108 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-066 |
| scripts/validate-contracts.sh:1293:93 | phase-execution.md | md-name | text | ambiguous-stem | rules/phase-execution.md, workflows/phase-execution.md | AUD-08-066 |
| scripts/validate-contracts.sh:1306:15 | workflows/rule | path | text | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:1306:64 | workflows/rule | path | text | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:1307:15 | global-claude.md | md-name | text | resolved | rules/global-claude.md | AUD-08-066 |
| scripts/validate-contracts.sh:1353:113 | language.md | md-name | text | resolved | rules/language.md | AUD-08-066 |
| scripts/validate-contracts.sh:1368:79 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:1380:10 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1384:10 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:1395:62 | PIPELINE.md | md-name | comment | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:1398:58 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1398:69 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:1398:331 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1398:342 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:1409:99 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1412:94 | pv-contract.md | md-name | text | resolved | workflows/pv-contract.md | AUD-08-066 |
| scripts/validate-contracts.sh:1415:92 | pv-review.md | md-name | text | resolved | workflows/pv-review.md | AUD-08-066 |
| scripts/validate-contracts.sh:1418:93 | pd-analyze.md | md-name | text | resolved | workflows/pd-analyze.md | AUD-08-066 |
| scripts/validate-contracts.sh:1421:98 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-066 |
| scripts/validate-contracts.sh:1425:143 | pv-classify-fixes.md | md-name | text | resolved | workflows/pv-classify-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1441:126 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1465:97 | pe-execute.md | md-name | text | resolved | workflows/pe-execute.md | AUD-08-066 |
| scripts/validate-contracts.sh:1469:131 | pe-execute.md | md-name | text | resolved | workflows/pe-execute.md | AUD-08-066 |
| scripts/validate-contracts.sh:1472:219 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-066 |
| scripts/validate-contracts.sh:1493:90 | pv-classify-fixes.md | md-name | text | resolved | workflows/pv-classify-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1498:106 | pv-classify-fixes.md | md-name | text | resolved | workflows/pv-classify-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1501:158 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1504:155 | pv-create-fixes.md | md-name | text | resolved | workflows/pv-create-fixes.md | AUD-08-066 |
| scripts/validate-contracts.sh:1514:106 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1517:104 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1520:120 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1523:157 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1558:159 | pae-finalize.md | md-name | text | resolved | workflows/pae-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1561:156 | pav-close.md | md-name | text | resolved | workflows/pav-close.md | AUD-08-066 |
| scripts/validate-contracts.sh:1575:85 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1578:97 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1581:71 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1585:104 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-066 |
| scripts/validate-contracts.sh:1588:100 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-066 |
| scripts/validate-contracts.sh:1598:58 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1609:146 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1614:147 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1617:87 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1620:95 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1635:105 | pav-propose.md | md-name | text | resolved | workflows/pav-propose.md | AUD-08-066 |
| scripts/validate-contracts.sh:1643:104 | pav-propose.md | md-name | text | resolved | workflows/pav-propose.md | AUD-08-066 |
| scripts/validate-contracts.sh:1646:132 | pav-propose.md | md-name | text | resolved | workflows/pav-propose.md | AUD-08-066 |
| scripts/validate-contracts.sh:1649:103 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1652:101 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1655:107 | phase-atomic-validation.md | md-name | text | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1665:89 | pav-close.md | md-name | text | resolved | workflows/pav-close.md | AUD-08-066 |
| scripts/validate-contracts.sh:1687:168 | onboard-legacy-project.md | md-name | text | resolved | workflows/onboard-legacy-project.md | AUD-08-066 |
| scripts/validate-contracts.sh:1725:116 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1728:96 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1731:139 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1734:114 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1740:93 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1755:89 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1758:94 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1761:87 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1764:95 | pd-finalize.md | md-name | text | resolved | workflows/pd-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1768:100 | pe-finalize.md | md-name | text | resolved | workflows/pe-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1771:89 | pe-finalize.md | md-name | text | resolved | workflows/pe-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1786:132 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1789:94 | pe-finalize.md | md-name | text | resolved | workflows/pe-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1801:127 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1804:123 | phase-composite-validation.md | md-name | text | resolved | workflows/phase-composite-validation.md | AUD-08-066 |
| scripts/validate-contracts.sh:1835:104 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1843:131 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:1846:160 | pd-decompose.md | md-name | text | resolved | workflows/pd-decompose.md | AUD-08-066 |
| scripts/validate-contracts.sh:1889:103 | phase-pipeline.md | md-name | text | resolved | workflows/phase-pipeline.md | AUD-08-066 |
| scripts/validate-contracts.sh:1893:122 | spec-run.md | md-name | text | resolved | workflows/spec-run.md | AUD-08-066 |
| scripts/validate-contracts.sh:1918:109 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1921:102 | spec-sync.md | md-name | text | resolved | workflows/spec-sync.md | AUD-08-066 |
| scripts/validate-contracts.sh:1931:82 | adr-new.md | md-name | text | resolved | workflows/adr-new.md | AUD-08-066 |
| scripts/validate-contracts.sh:1934:80 | pd-design.md | md-name | text | resolved | workflows/pd-design.md | AUD-08-066 |
| scripts/validate-contracts.sh:1937:87 | pv-finalize.md | md-name | text | resolved | workflows/pv-finalize.md | AUD-08-066 |
| scripts/validate-contracts.sh:1946:90 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:1949:89 | pae-tests.md | md-name | text | resolved | workflows/pae-tests.md | AUD-08-066 |
| scripts/validate-contracts.sh:1982:84 | context-pack.md | md-name | text | resolved | workflows/context-pack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1985:156 | context-pack.md | md-name | text | resolved | workflows/context-pack.md | AUD-08-066 |
| scripts/validate-contracts.sh:1992:149 | bugfix.md | md-name | text | resolved | workflows/bugfix.md | AUD-08-066 |
| scripts/validate-contracts.sh:1995:123 | bugfix.md | md-name | text | resolved | workflows/bugfix.md | AUD-08-066 |
| scripts/validate-contracts.sh:1998:120 | bugfix.md | md-name | text | resolved | workflows/bugfix.md | AUD-08-066 |
| scripts/validate-contracts.sh:2001:131 | bugfix.md | md-name | text | resolved | workflows/bugfix.md | AUD-08-066 |
| scripts/validate-contracts.sh:2075:391 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-066 |
| scripts/validate-contracts.sh:2078:176 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-066 |
| scripts/validate-contracts.sh:2593:13 | workflows/fixture-known.md | path | text | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:3378:13 | workflows/fixture-known.md | path | text | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:3516:13 | workflows/fixture-known.md | path | text | missing-path | none | AUD-08-067 |
| scripts/validate-contracts.sh:4645:18 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-066 |
| scripts/validate-contracts.sh:4645:46 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-066 |
| scripts/validate-contracts.sh:4697:90 | rule-history | skill-name | text | missing-target | none | AUD-08-067 |
| scripts/validate-contracts.sh:5611:10 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5690:61 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5714:300 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5720:91 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5723:171 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5726:178 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5729:187 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5732:241 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5735:61 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5738:128 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5741:104 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5744:218 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5747:98 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5750:135 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5786:249 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5789:156 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5792:188 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5795:134 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5798:210 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5801:134 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5819:109 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5825:56 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5834:267 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5837:97 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5867:101 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5870:158 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5876:182 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5879:166 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5885:49 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5888:119 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5891:61 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5894:148 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5897:288 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5900:103 | restack.md | md-name | text | resolved | workflows/restack.md | AUD-08-066 |
| scripts/validate-contracts.sh:5903:139 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5906:155 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| scripts/validate-contracts.sh:5912:125 | git-flow.md | md-name | text | resolved | rules/git-flow.md | AUD-08-066 |
| templates/stacks/python-fastapi.md:381:12 | /metrics | command | span | unknown-command | none | AUD-08-072 |
| tests/hook-install.sh:790:77 | global-claude.md | md-name | text | resolved | rules/global-claude.md | AUD-08-069 |
| tests/hook-install.sh:817:34 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-069 |
| tests/hook-install.sh:818:38 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-069 |
| tests/hook-install.sh:824:51 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-069 |
| tests/hook-install.sh:825:54 | tdd.md | md-name | text | resolved | rules/tdd.md | AUD-08-069 |
| tests/hook-install.sh:827:55 | phase-discovery.md | md-name | text | ambiguous-stem | rules/phase-discovery.md, workflows/phase-discovery.md | AUD-08-069 |
| tests/log-step-hook.sh:53:72 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-069 |
| tests/log-step-hook.sh:770:36 | run-log.md | md-name | text | resolved | rules/run-log.md | AUD-08-069 |
| tests/state-tool.py:32:26 | workflow-globals.md | md-name | text | resolved | rules/workflow-globals.md | AUD-08-069 |
| tests/state-tool.py:5076:36 | workflow-reference.md | md-name | text | resolved | rules/workflow-reference.md | AUD-08-069 |
| tests/workflow-instructions.py:11:25 | PIPELINE.md | md-name | text | resolved | workflows/PIPELINE.md | AUD-08-069 |
| workflows/bugfix.md:104:1 | quick-flow → ## Mid-flight escalation (quick → full) | section-ref | span | missing-heading | rules/quick-flow.md (missing-heading) | AUD-08-031 |
| workflows/context-pack.md:46:16 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-034 |
| workflows/context-pack.md:60:72 | context-pack.md | md-name | span | resolved | workflows/context-pack.md | AUD-08-034 |
| workflows/pae-finalize.md:30:46 | phase-atomic-execution → ## Context Bootstrap | section-ref | span | ambiguous-stem | rules/phase-atomic-execution.md (resolved), workflows/phase-atomic-execution.md (resolved) | AUD-08-032 |
| workflows/pae-implement.md:141:98 | workflow-reference → Autonomous Subtask Classifier → Runtime self-correction | section-ref | span | heading-unmarked | rules/workflow-reference.md (heading-unmarked) | AUD-08-033 |
| workflows/pae-implement.md:159:29 | phase-atomic-execution → ## Context Bootstrap | section-ref | span | ambiguous-stem | rules/phase-atomic-execution.md (resolved), workflows/phase-atomic-execution.md (resolved) | AUD-08-032 |
| workflows/pae-tests.md:63:16 | phase-atomic-execution → ## Context Bootstrap | section-ref | span | ambiguous-stem | rules/phase-atomic-execution.md (resolved), workflows/phase-atomic-execution.md (resolved) | AUD-08-032 |
| workflows/pav-check.md:48:53 | phase-atomic-execution → ## Context Bootstrap | section-ref | span | ambiguous-stem | rules/phase-atomic-execution.md (resolved), workflows/phase-atomic-execution.md (resolved) | AUD-08-032 |
| workflows/pav-propose.md:12:31 | workflow-globals → Workflow-declared mode overrides | section-ref | span | missing-heading | rules/workflow-globals.md (missing-heading) | AUD-08-036 |
| workflows/phase-execution.md:97:1 | quick-flow → ## Mid-flight escalation (quick → full) | section-ref | span | missing-heading | rules/quick-flow.md (missing-heading) | AUD-08-031 |
| workflows/phase-pipeline.md:111:19 | pd-analyze.md | md-name | span | resolved | workflows/pd-analyze.md | AUD-08-035 |
| workflows/phase-pipeline.md:112:21 | pd-decompose.md | md-name | span | resolved | workflows/pd-decompose.md | AUD-08-035 |
| workflows/phase-pipeline.md:113:18 | pd-design.md | md-name | span | resolved | workflows/pd-design.md | AUD-08-035 |
| workflows/phase-pipeline.md:114:20 | pd-finalize.md | md-name | span | resolved | workflows/pd-finalize.md | AUD-08-035 |
| workflows/phase-pipeline.md:123:19 | pe-execute.md | md-name | span | resolved | workflows/pe-execute.md | AUD-08-035 |
| workflows/phase-pipeline.md:124:20 | pe-finalize.md | md-name | span | resolved | workflows/pe-finalize.md | AUD-08-035 |
| workflows/phase-pipeline.md:125:31 | phase-atomic-execution.md | md-name | span | ambiguous-stem | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | AUD-08-035 |
| workflows/phase-pipeline.md:126:18 | pae-tests.md | md-name | span | resolved | workflows/pae-tests.md | AUD-08-035 |
| workflows/phase-pipeline.md:127:22 | pae-implement.md | md-name | span | resolved | workflows/pae-implement.md | AUD-08-035 |
| workflows/phase-pipeline.md:128:21 | pae-finalize.md | md-name | span | resolved | workflows/pae-finalize.md | AUD-08-035 |
| workflows/phase-pipeline.md:129:32 | phase-atomic-validation.md | md-name | span | ambiguous-stem | rules/phase-atomic-validation.md, workflows/phase-atomic-validation.md | AUD-08-035 |
| workflows/phase-pipeline.md:130:18 | pav-check.md | md-name | span | resolved | workflows/pav-check.md | AUD-08-035 |
| workflows/phase-pipeline.md:131:20 | pav-propose.md | md-name | span | resolved | workflows/pav-propose.md | AUD-08-035 |
| workflows/phase-pipeline.md:132:18 | pav-close.md | md-name | span | resolved | workflows/pav-close.md | AUD-08-035 |
| workflows/phase-pipeline.md:133:35 | phase-composite-validation.md | md-name | span | resolved | workflows/phase-composite-validation.md | AUD-08-035 |
| workflows/phase-pipeline.md:141:20 | pv-contract.md | md-name | span | resolved | workflows/pv-contract.md | AUD-08-035 |
| workflows/phase-pipeline.md:142:18 | pv-review.md | md-name | span | resolved | workflows/pv-review.md | AUD-08-035 |
| workflows/phase-pipeline.md:143:18 | pv-issues.md | md-name | span | resolved | workflows/pv-issues.md | AUD-08-035 |
| workflows/phase-pipeline.md:144:24 | pv-create-fixes.md | md-name | span | resolved | workflows/pv-create-fixes.md | AUD-08-035 |
| workflows/phase-pipeline.md:145:25 | pv-execute-fixes.md | md-name | span | resolved | workflows/pv-execute-fixes.md | AUD-08-035 |
| workflows/phase-pipeline.md:146:20 | pv-finalize.md | md-name | span | resolved | workflows/pv-finalize.md | AUD-08-035 |
| workflows/phase-pipeline.md:147:23 | compress-state.md | md-name | span | resolved | workflows/compress-state.md | AUD-08-035 |
| workflows/pv-contract.md:33:5 | quick-flow → The quick path | section-ref | span | heading-unmarked | rules/quick-flow.md (heading-unmarked) | AUD-08-033 |

### Loads

| Source:line | Targets | Mode | Condition |
|---|---|---|---|
| rules/phase-atomic-execution.md:55 | workflows/pae-implement.md | conditional | only when a leaf's `atomic-execution: blocked` is met on entry; the span names the workflow that reads the block, and nothing is loaded (AUD-08-025) |
| rules/run-log.md:86 | workflows/retro.md | conditional | only when a pipeline resumes in a later session; the line says how /retro reads two runs of one task, and nothing is loaded (AUD-08-025) |
| rules/run-log.md:582 | workflows/retro.md | conditional | only in /retro after a run; the line names /retro as the only reader of the log, and no pipeline loads it (AUD-08-025) |
| rules/tdd.md:39 | workflows/pae-tests.md | conditional | only when a leaf block lacks the `atomic-tests:` field; the span names the writer of the status, and nothing is loaded (AUD-08-025) |
| rules/workflow-globals.md:32 | templates/codex-global-AGENTS.md | mandatory | - |
| rules/workflow-globals.md:36 | workflows/pav-check.md | conditional | only when a child workflow runs without its parent orchestrator; the span is the example child, and the load is the full bootstrap (AUD-08-025) |
| rules/workflow-globals.md:36 | workflows/phase-atomic-validation.md | conditional | only when a child workflow runs without its parent orchestrator; the span is the example parent, and the load is the full bootstrap (AUD-08-025) |
| rules/workflow-globals.md:44 | workflows/context-pack.md | conditional | only when the pack was confirmed fresh against its own manifest in the same session; the span names the pack file, not the workflow (AUD-08-006) |
| rules/workflow-reference.md:227 | rules/tdd.md | conditional | only when a leaf block lacks the `atomic-tests:` field; the span names the rule that holds the semantics, and nothing is loaded (AUD-08-025) |
| rules/workflow-reference.md:247 | workflows/pav-propose.md | conditional | only at the step that writes `## Improvement Proposals (T-XX)`; the span names its writer, and nothing is loaded (AUD-08-025) |
| rules/workflow-reference.md:247 | workflows/pe-finalize.md | conditional | only at /pe-finalize step 5, which reads `## Improvement Proposals (T-XX)`; the span names that reader, and nothing is loaded (AUD-08-025) |
| rules/workflow-reference.md:282 | workflows/compress-state.md | conditional | only when /compress-state or another workflow edits a protected section; the span names a workflow bound by the contract, and nothing is loaded (AUD-08-025) |
| rules/workflow-reference.md:311 | workflows/pav-propose.md | conditional | only at the step that writes `## Improvement Proposals (T-XX)`; the span names its writer, and nothing is loaded (AUD-08-025) |
| rules/workflow-reference.md:311 | workflows/pe-finalize.md | conditional | only after the execution phase, when /pe-finalize reads `## Improvement Proposals (T-XX)`; the span names that reader, and nothing is loaded (AUD-08-025) |
| workflows/compress-state.md:12 | rules/workflow-reference.md | mandatory | - |
| workflows/context-pack.md:46 | workflows/context-pack.md | conditional | only when a pack already exists; the line reads the manifest of the pack file `AI_DIR/context-pack.md`, not the workflow (AUD-08-034) |
| workflows/context-pack.md:60 | workflows/context-pack.md | conditional | only when the pack is stale, absent or refreshed; the span is the pack file this step writes, not the workflow (AUD-08-034) |
| workflows/pae-finalize.md:30 | rules/phase-atomic-execution.md, workflows/phase-atomic-execution.md | mandatory | - |
| workflows/pae-implement.md:53 | rules/phase-atomic-execution.md | mandatory | - |
| workflows/pae-implement.md:126 | rules/workflow-reference.md | mandatory | - |
| workflows/pae-tests.md:56 | rules/phase-atomic-execution.md | mandatory | - |
| workflows/pae-tests.md:76 | rules/tdd.md | mandatory | - |
| workflows/pav-check.md:24 | rules/phase-atomic-validation.md | mandatory | - |
| workflows/pav-check.md:55 | rules/tdd.md | mandatory | - |
| workflows/pav-close.md:26 | rules/phase-atomic-validation.md | mandatory | - |
| workflows/pav-close.md:32 | rules/workflow-reference.md | mandatory | - |
| workflows/pav-propose.md:18 | rules/phase-atomic-validation.md | mandatory | - |
| workflows/pav-propose.md:91 | workflows/phase-atomic-validation.md | conditional | only when /phase-atomic-validation resumes; the line says that workflow reads the marker this step writes, and nothing of it is loaded (AUD-08-025) |
| workflows/pd-decompose.md:24 | rules/workflow-reference.md | mandatory | - |
| workflows/pd-finalize.md:25 | rules/workflow-reference.md | mandatory | - |
| workflows/pe-execute.md:14 | workflows/phase-discovery.md | conditional | only when the task has no state.md; the span sits in the stop message that names the prerequisite, and nothing of it is loaded (AUD-08-025) |
| workflows/pe-execute.md:23 | rules/phase-execution.md | mandatory | - |
| workflows/pe-execute.md:42 | rules/workflow-reference.md | mandatory | - |
| workflows/pe-finalize.md:22 | rules/phase-execution.md | mandatory | - |
| workflows/pe-finalize.md:27 | rules/workflow-reference.md | mandatory | - |
| workflows/phase-atomic-execution.md:22 | rules/phase-atomic-execution.md | mandatory | - |
| workflows/phase-atomic-execution.md:56 | rules/tdd.md | conditional | only when the value set of `atomic-tests:` must be interpreted; the line reads the progress field, :58-63 list every value acted on, and the span names the rule that defines them; nothing of it is loaded (AUD-08-025) |
| workflows/phase-atomic-validation.md:21 | rules/phase-atomic-validation.md | mandatory | - |
| workflows/phase-atomic-validation.md:80 | workflows/pav-check.md | conditional | after each child call; the line re-reads the progress block, and the span names the child that owns `failed`; nothing of it is loaded (AUD-08-025) |
| workflows/phase-atomic-validation.md:80 | workflows/pav-close.md | conditional | after each child call; the line re-reads the progress block, and the span names the child that owns `complete`; nothing of it is loaded (AUD-08-025) |
| workflows/phase-composite-validation.md:18 | rules/phase-atomic-validation.md | mandatory | - |
| workflows/phase-execution.md:53 | rules/phase-execution.md | mandatory | - |
| workflows/phase-pipeline.md:7 | rules/workflow-globals.md | mandatory | - |
| workflows/phase-pipeline.md:105 | workflows/phase-discovery.md | conditional | only while Discovery is incomplete; the line calls the child phase and the word `Read-only` makes it a load line; nothing of it is loaded (AUD-08-025) |
| workflows/phase-validation.md:54 | rules/phase-validation.md | mandatory | - |
| workflows/pv-classify-fixes.md:14 | workflows/pv-issues.md | conditional | only when `### Approved` is missing; the span sits in the stop message that names the prerequisite, and nothing of it is loaded (AUD-08-025) |
| workflows/pv-classify-fixes.md:19 | rules/phase-validation.md | conditional | only on standalone invocation, before project writes (pv-classify-fixes.md:19-20) |
| workflows/pv-contract.md:14 | workflows/phase-execution.md | conditional | only when state is missing or execution is incomplete; the span sits in the stop message that names the prerequisite, and nothing of it is loaded (AUD-08-025) |
| workflows/pv-contract.md:22 | rules/phase-validation.md | mandatory | - |
| workflows/pv-create-fixes.md:29 | rules/phase-validation.md | mandatory | - |
| workflows/pv-execute-fixes.md:26 | rules/phase-validation.md | mandatory | - |
| workflows/pv-finalize.md:29 | rules/phase-validation.md | mandatory | - |
| workflows/pv-finalize.md:30 | rules/workflow-reference.md | mandatory | - |
| workflows/pv-finalize.md:63 | workflows/adr-new.md | conditional | only when /adr-new reads step 3 for the ADR schema; the span names that reader, and the line forbids running the other steps while loading it |
| workflows/pv-issues.md:23 | rules/phase-validation.md | conditional | only on standalone invocation, before writes (pv-issues.md:23) |
| workflows/pv-review.md:27 | rules/phase-validation.md | mandatory | - |
| workflows/pv-review.md:40 | workflows/pv-contract.md | conditional | on every review; the line re-reads the file set the contract check used (AUD-08-048), and the span names that workflow; nothing of it is loaded (AUD-08-025) |
| workflows/pv-review.md:50 | rules/tdd.md | mandatory | - |
| workflows/restack.md:6 | rules/git-flow.md | mandatory | - |
| workflows/spec-run.md:6 | rules/orchestration.md | mandatory | - |
| workflows/spec-run.md:6 | rules/git-flow.md | mandatory | - |
| workflows/spec-run.md:149 | workflows/pd-finalize.md | conditional | only after Discovery, at the batch gate; the line reads `## Open Questions (batch)`, and the span names the step after which it is read; nothing of it is loaded (AUD-08-025) |
| workflows/spec-run.md:211 | workflows/pe-execute.md | conditional | only in Step 3, when the stack is resolved; the line reads plan.md and copies the ordering rule of /pe-execute (pe-execute.md:29-34), whose workflow is not run |
| workflows/spec-run.md:319 | workflows/pae-finalize.md | conditional | once per leaf Implementer; the span is the last step named in the worker's instruction, and 'loads .ai/ context itself' describes the worker; the Orchestrator loads nothing |
| workflows/spec-run.md:486 | workflows/spec-run.md | conditional | only on interruption recovery; the line re-runs the workflow, whose Step 0 reads state.md |

### Repeated loads

| ID | Caller | Callee | Target | Disposition | Finding |
|---|---|---|---|---|---|
| RL-001 | workflows/pae-implement.md | workflows/pd-decompose.md | rules/workflow-reference.md | not-applicable | - |
| RL-002 | workflows/pav-close.md | workflows/compress-state.md | rules/workflow-reference.md | finding | AUD-08-054 |
| RL-003 | workflows/pav-close.md | workflows/phase-composite-validation.md | rules/phase-atomic-validation.md | finding | AUD-08-053 |
| RL-004 | workflows/pd-finalize.md | workflows/compress-state.md | rules/workflow-reference.md | finding | AUD-08-054 |
| RL-005 | workflows/pe-execute.md | workflows/compress-state.md | rules/workflow-reference.md | finding | AUD-08-054 |
| RL-006 | workflows/pe-finalize.md | workflows/compress-state.md | rules/workflow-reference.md | finding | AUD-08-054 |
| RL-007 | workflows/phase-atomic-execution.md | workflows/pae-implement.md | rules/phase-atomic-execution.md | finding | AUD-08-051 |
| RL-008 | workflows/phase-atomic-execution.md | workflows/pae-tests.md | rules/phase-atomic-execution.md | finding | AUD-08-051 |
| RL-009 | workflows/phase-atomic-execution.md | workflows/pae-tests.md | rules/tdd.md | not-applicable | - |
| RL-010 | workflows/phase-atomic-validation.md | workflows/pav-check.md | rules/phase-atomic-validation.md | finding | AUD-08-053 |
| RL-011 | workflows/phase-atomic-validation.md | workflows/pav-close.md | rules/phase-atomic-validation.md | finding | AUD-08-053 |
| RL-012 | workflows/phase-atomic-validation.md | workflows/pav-propose.md | rules/phase-atomic-validation.md | finding | AUD-08-053 |
| RL-013 | workflows/phase-execution.md | workflows/pe-execute.md | rules/phase-execution.md | finding | AUD-08-053 |
| RL-014 | workflows/phase-execution.md | workflows/pe-finalize.md | rules/phase-execution.md | finding | AUD-08-052 |
| RL-015 | workflows/phase-validation.md | workflows/pv-classify-fixes.md | rules/phase-validation.md | guarded | - |
| RL-016 | workflows/pv-classify-fixes.md | workflows/pv-create-fixes.md | rules/phase-validation.md | not-applicable | - |
| RL-017 | workflows/pv-create-fixes.md | workflows/pv-classify-fixes.md | rules/phase-validation.md | guarded | - |
| RL-018 | workflows/pv-execute-fixes.md | workflows/phase-validation.md | rules/phase-validation.md | not-applicable | - |
| RL-019 | workflows/pv-execute-fixes.md | workflows/pv-contract.md | rules/phase-validation.md | finding | AUD-08-053 |
| RL-020 | workflows/pv-execute-fixes.md | workflows/pv-review.md | rules/phase-validation.md | finding | AUD-08-053 |
| RL-021 | workflows/pv-finalize.md | workflows/compress-state.md | rules/workflow-reference.md | finding | AUD-08-054 |

### Full-output candidates

| ID | Source:line | Text | Disposition | Finding |
|---|---|---|---|---|
| FO-001 | workflows/PIPELINE.md:73 | Outputs: contract and phase markers in state, plus plan and descriptions for full tasks. | not-applicable | - |
| FO-002 | workflows/onboard-legacy-project.md:49 | complete until its outputs exist. | not-applicable | - |
| FO-003 | workflows/onboard-legacy-project.md:165 | Mark Phase 3 complete only when these checks pass. Record completion time, exact output | not-applicable | - |
| FO-004 | workflows/phase-discovery.md:38 | After a nonfinal child completes, output `Step <N> complete — review requested`, | not-applicable | - |
| FO-005 | workflows/phase-execution.md:18 | This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the | finding | AUD-08-039 |
| FO-006 | workflows/phase-validation.md:19 | This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the | finding | AUD-08-039 |
| FO-007 | workflows/retro.md:263 | Invoke the analyzer with the frozen manifest, matching scenario and authority. Its standard output must be a pipe or socket; a trusted consumer must wait for a  | guarded | - |
| FO-008 | workflows/spec-draft.md:305 | <finding ids or none>`; keep the full round log out of the spec. | not-applicable | - |
| FO-009 | workflows/spec-run.md:63 | This pipeline writes a run log. Follow the **`run-log`** rule in full — it defines the | finding | AUD-08-039 |

### Harness-name candidates

| ID | Source:line | Text | Disposition | Finding |
|---|---|---|---|---|
| HN-001 | harness/claude/capabilities.md:1 | # Claude logging capabilities | not-applicable | - |
| HN-002 | harness/claude/capabilities.md:4 | profile: claude-stop-v1 | not-applicable | - |
| HN-003 | harness/claude/capabilities.md:6 | runtime: Claude Code 2.1.309 | not-applicable | - |
| HN-004 | harness/claude/capabilities.md:33 | runtime: Claude Code 2.1.317 | not-applicable | - |
| HN-005 | harness/claude/capabilities.md:35 | evidence: https://code.claude.com/docs/en/hooks | not-applicable | - |
| HN-006 | harness/claude/capabilities.md:36 | evidence: https://code.claude.com/docs/en/permissions | not-applicable | - |
| HN-007 | harness/claude/capabilities.md:37 | evidence: https://code.claude.com/docs/en/permission-modes | not-applicable | - |
| HN-008 | harness/claude/capabilities.md:41 | deny: exit 2 with the diagnostic on stderr; the harness blocks the call before permission rules are evaluated and gives Claude the stderr text as the denial rea | not-applicable | - |
| HN-009 | harness/claude/capabilities.md:47 | failure-mode: onFailure "block" (Claude Code 2.1.295 or later); a handler that cannot start, exits with a code other than 0 or 2, times out or prints invalid JS | not-applicable | - |
| HN-010 | harness/claude/capabilities.md:79 | \| X9 \| Codex and other harnesses have textual rules only. \| | not-applicable | - |
| HN-011 | harness/codex/capabilities.md:1 | # Codex logging capabilities | not-applicable | - |
| HN-012 | harness/codex/capabilities.md:5 | This release installs no native Codex logging adapter. This declaration describes | not-applicable | - |
| HN-013 | harness/codex/capabilities.md:14 | This release installs no command-level git enforcement for Codex. Git safety rails | not-applicable | - |
| HN-014 | rules/git-flow.md:202 | hook does when the harness runs it (Claude Code, in a registered project): `hook: deny` | guarded | - |
| HN-015 | rules/git-flow.md:263 | runs the command outside the agent (in a terminal, or with `! <command>` in Claude Code) or | guarded | - |
| HN-016 | rules/global-claude.md:1 | # Global Claude Code Standards | not-applicable | - |
| HN-017 | rules/global-claude.md:98 | If the project's CLAUDE.md defines its own `## Context Loading Protocol`, that | not-applicable | - |
| HN-018 | rules/language.md:21 | # Set this in your personal ~/.claude/CLAUDE.md, not here. | finding | AUD-08-021 |
| HN-019 | rules/run-log.md:377 | `hooks/log-step-hook.sh` consumes the `claude-stop-v1` profile. It exits zero on | guarded | - |
| HN-020 | rules/workflow-globals.md:11 | \| Phase \| Rules file (Windsurf / Devin) \| Skill name (Claude Code / Codex) \| Loaded by \| | finding | AUD-08-016 |
| HN-021 | rules/workflow-globals.md:21 | Claude Code and Codex there is no rules directory, so `scripts/sync.sh` deploys every `rules/*.md` as a | finding | AUD-08-016 |
| HN-022 | rules/workflow-globals.md:27 | `rule-<name>` on Claude Code and Codex and to the bare basename on Windsurf and Devin. | finding | AUD-08-016 |
| HN-023 | rules/workflow-globals.md:31 | the always-on essentials stay duplicated in `rules/global-claude.md` (→ `~/.claude/CLAUDE.md`) | not-applicable | - |
| HN-024 | rules/workflow-globals.md:32 | and `templates/codex-global-AGENTS.md` (→ `~/.codex/AGENTS.md`), which those agents do read on | not-applicable | - |
| HN-025 | rules/workflow-reference.md:131 | Optional model columns: `Model (Claude)` maps to provider `anthropic`; `Model (Codex)` | guarded | - |
| HN-026 | templates/codex-global-AGENTS.md:1 | # AGENTS.md — Global Codex Instructions | not-applicable | - |
| HN-027 | templates/codex-global-AGENTS.md:2 | # Managed by Orchestrail/scripts/sync.sh — do not edit here; edit templates/codex-global-AGENTS.md. | not-applicable | - |
| HN-028 | templates/codex-global-AGENTS.md:3 | # Codex merges this global file with each project's own AGENTS.md. | not-applicable | - |
| HN-029 | workflows/onboard-legacy-project.md:12 | 1. Require `.ai/{memory,context,principles,adr,specs,tasks}/`, `AGENTS.md` and `CLAUDE.md`. | not-applicable | - |
| HN-030 | workflows/onboard-legacy-project.md:104 | \| 12 \| `CLAUDE.md` \| Append Project Standards only when absent; preserve Context Loading Protocol and existing instructions \| | not-applicable | - |
| HN-031 | workflows/onboard-legacy-project.md:119 | invent a replacement instruction hierarchy. `CLAUDE.md → ## Project Standards` summarizes | not-applicable | - |
| HN-032 | workflows/pd-decompose.md:153 | Preserve optional model columns and their values, including `Model (Claude)`, | guarded | - |
| HN-033 | workflows/pd-decompose.md:154 | `Model (Codex)` and legacy `Model`, under | guarded | - |
| HN-034 | workflows/pd-finalize.md:38 | `Model (Claude)` / `Model (Codex)` and legacy `Model` under | guarded | - |
| HN-035 | workflows/pd-select-model.md:257 | `Model (Claude)`/`Model (Codex)` decisions through `--update-plan PLAN --updates UPDATES.json`. | guarded | - |
| HN-036 | workflows/pe-execute.md:43 | `Model (Claude)` / `Model (Codex)` column, legacy `Model`, or session default by | guarded | - |
| HN-037 | workflows/phase-atomic-execution.md:78 | Read its active optional `Model (Claude)` / `Model (Codex)` column with legacy `Model` | guarded | - |
| HN-038 | workflows/spec-run.md:170 | `Model (Claude)` / `Model (Codex)` columns in `plan.md → ## Subtasks`, preserving | guarded | - |

### Repetition review

| Workflow | Report findings | Checkpoint findings | Review findings |
|---|---|---|---|
| workflows/adr-new.md | none | none | none |
| workflows/bugfix.md | none | none | AUD-08-048 |
| workflows/compress-state.md | none | AUD-08-045 | none |
| workflows/context-pack.md | none | none | none |
| workflows/onboard-legacy-project.md | none | none | none |
| workflows/pae-finalize.md | none | AUD-08-045 | none |
| workflows/pae-implement.md | AUD-08-059 | none | none |
| workflows/pae-tests.md | AUD-08-042, AUD-08-059 | none | none |
| workflows/pav-check.md | none | none | none |
| workflows/pav-close.md | none | AUD-08-045 | none |
| workflows/pav-propose.md | none | AUD-08-046 | none |
| workflows/pd-analyze.md | none | none | none |
| workflows/pd-archive.md | none | none | none |
| workflows/pd-decompose.md | none | none | none |
| workflows/pd-design.md | none | none | none |
| workflows/pd-finalize.md | none | none | none |
| workflows/pd-select-model.md | none | none | none |
| workflows/pe-execute.md | none | AUD-08-045 | none |
| workflows/pe-finalize.md | none | none | none |
| workflows/phase-atomic-execution.md | AUD-08-042 | none | none |
| workflows/phase-atomic-validation.md | AUD-08-044 | none | none |
| workflows/phase-composite-validation.md | none | AUD-08-045 | none |
| workflows/phase-discovery.md | none | none | AUD-08-047 |
| workflows/phase-execution.md | AUD-08-044 | none | none |
| workflows/phase-pipeline.md | AUD-08-043 | none | AUD-08-047 |
| workflows/phase-validation.md | AUD-08-044 | none | AUD-08-048, AUD-08-049 |
| workflows/pv-classify-fixes.md | none | none | none |
| workflows/pv-contract.md | none | none | AUD-08-048 |
| workflows/pv-create-fixes.md | none | none | none |
| workflows/pv-execute-fixes.md | none | AUD-08-045 | AUD-08-049 |
| workflows/pv-finalize.md | none | none | AUD-08-049 |
| workflows/pv-issues.md | none | none | none |
| workflows/pv-review.md | none | none | AUD-08-048 |
| workflows/restack.md | none | none | none |
| workflows/retro.md | none | none | none |
| workflows/spec-draft.md | none | none | AUD-08-050 |
| workflows/spec-run.md | AUD-08-042 | AUD-08-045 | AUD-08-047 |
| workflows/spec-sync.md | none | none | none |
| workflows/suggest-commit-message.md | none | none | none |
| workflows/suggest-commit-pr.md | none | none | none |
| workflows/suggest-pr-description.md | none | none | none |

### Legacy mentions

| Source:line | Term | Role | Note |
|---|---|---|---|
| rules/workflow-globals.md:11 | windsurf | active-behavior | column header of the rule-resolution table for Windsurf and Devin (AUD-08-015) |
| rules/workflow-globals.md:11 | devin | active-behavior | column header of the rule-resolution table for Windsurf and Devin (AUD-08-015) |
| rules/workflow-globals.md:19 | windsurf | active-behavior | instructs how a rule reference resolves on Windsurf and Devin (AUD-08-015) |
| rules/workflow-globals.md:19 | devin | active-behavior | instructs how a rule reference resolves on Windsurf and Devin (AUD-08-015) |
| rules/workflow-globals.md:20 | windsurf | active-behavior | names the Windsurf and Devin rule directories that the resolution reads (AUD-08-015) |
| rules/workflow-globals.md:20 | devin | active-behavior | names the Windsurf and Devin rule directories that the resolution reads (AUD-08-015) |
| rules/workflow-globals.md:27 | windsurf | active-behavior | instructs to resolve a rule to its bare basename on Windsurf and Devin (AUD-08-015) |
| rules/workflow-globals.md:27 | devin | active-behavior | instructs to resolve a rule to its bare basename on Windsurf and Devin (AUD-08-015) |

### Duplicates

| Group | Clusters | Locations | Normative source | Condition differences | Disposition | Owner | Finding |
|---|---|---|---|---|---|---|---|
| DG-001 | DUP-003, DUP-004, DUP-005 | rules/global-claude.md:17-17, rules/language.md:7-7, templates/codex-global-AGENTS.md:7-7, rules/global-claude.md:18-20, templates/codex-global-AGENTS.md:8-10, rules/global-claude.md:21-21, templates/codex-global-AGENTS.md:11-11 | rules/language.md → (preamble) | None: the same always-on language rule in the language contract and in both harness always-on bodies. | intentional | none | - |
| DG-002 | DUP-001, DUP-002, DUP-006, DUP-007, DUP-008, DUP-009, DUP-010, DUP-011, DUP-012, DUP-013 | rules/git-flow.md:115-116, rules/global-claude.md:25-26, templates/codex-global-AGENTS.md:15-16, rules/git-flow.md:134-135, rules/global-claude.md:41-42, templates/codex-global-AGENTS.md:31-32, rules/global-claude.md:25-25, templates/codex-global-AGENTS.md:15-15, rules/global-claude.md:28-32, templates/codex-global-AGENTS.md:18-22, rules/global-claude.md:34-35, templates/codex-global-AGENTS.md:24-25, rules/global-claude.md:37-40, templates/codex-global-AGENTS.md:27-30, rules/global-claude.md:40-41, templates/codex-global-AGENTS.md:30-31, rules/global-claude.md:42-44, templates/codex-global-AGENTS.md:32-34, rules/global-claude.md:46-47, templates/codex-global-AGENTS.md:36-37, rules/global-claude.md:47-48, templates/codex-global-AGENTS.md:37-38 | rules/git-flow.md → ## Commits | None: the commit-message and attribution rule of the git-flow contract, repeated in both always-on bodies. | intentional | none | - |
| DG-003 | DUP-014, DUP-015, DUP-016, DUP-017, DUP-018, DUP-019, DUP-020, DUP-021 | rules/global-claude.md:112-112, templates/codex-global-AGENTS.md:43-43, rules/global-claude.md:113-113, templates/codex-global-AGENTS.md:44-44, rules/global-claude.md:114-114, templates/codex-global-AGENTS.md:45-45, rules/global-claude.md:115-115, templates/codex-global-AGENTS.md:46-46, rules/global-claude.md:117-117, templates/codex-global-AGENTS.md:48-48, rules/global-claude.md:118-118, templates/codex-global-AGENTS.md:49-49, rules/global-claude.md:119-119, templates/codex-global-AGENTS.md:50-50, rules/global-claude.md:120-124, templates/codex-global-AGENTS.md:51-55 | rules/global-claude.md → ## AST-GREP STRUCTURAL SEARCH POLICY | None: the same search policy in the two harness always-on bodies. | intentional | none | - |
| DG-004 | DUP-022, DUP-023, DUP-024, DUP-025, DUP-026 | rules/phase-atomic-execution.md:10-10, rules/phase-atomic-validation.md:10-10, rules/phase-atomic-execution.md:10-12, rules/phase-atomic-validation.md:10-12, rules/phase-atomic-execution.md:12-14, rules/phase-atomic-validation.md:12-14, rules/phase-atomic-execution.md:16-17, rules/phase-atomic-validation.md:16-17, rules/phase-atomic-execution.md:28-28, rules/phase-atomic-validation.md:25-25 | rules/phase-atomic-execution.md → ## Context Bootstrap | rules/phase-atomic-execution.md states the reuse condition, path resolution and load order for atomic execution (loaded by /phase-atomic-execution, /pae-tests and /pae-implement); rules/phase-atomic-validation.md states them for atomic validation (loaded by /phase-atomic-validation and /pav-check). | condition-specific | none | - |
| DG-005 | DUP-027, DUP-029 | rules/phase-atomic-execution.md:30-30, rules/phase-atomic-validation.md:27-27, rules/phase-discovery.md:14-14, rules/phase-execution.md:14-14, rules/phase-validation.md:14-14, rules/phase-discovery.md:11-11, rules/phase-execution.md:11-11, rules/phase-validation.md:11-11 | rules/phase-execution.md → ## Context Bootstrap | Each phase rule lists its own sources under the same table header, and the three orchestrator-phase rules state the same umbrella order for their own phase. | condition-specific | none | - |
| DG-006 | DUP-028 | rules/phase-atomic-execution.md:48-48, workflows/pae-tests.md:64-64 | rules/phase-atomic-execution.md → ## Phase Behaviors | None: the same obligation for the same step; the workflow adds that missing tooling never justifies level `none` (workflows/pae-tests.md:64-65). | intentional | none | - |
| DG-007 | DUP-030 | rules/quick-flow.md:89-89, rules/tdd.md:92-92 | rules/tdd.md → ## RED — what counts | None: the quick path applies the RED criterion of the tdd rule, which it cites (rules/quick-flow.md:86). | intentional | none | - |
| DG-008 | DUP-031 | rules/run-log.md:207-207, rules/run-log.md:256-256 | rules/run-log.md → ## Field vocabulary | None: two different tables in the same section share a column header (rules/run-log.md:205, :254). | intentional | none | - |
| DG-009 | DUP-032 | rules/workflow-globals.md:215-215, rules/workflow-reference.md:226-226 | rules/workflow-globals.md → ## Canonical Status Formats | None: the same vocabulary for the same fields; the `atomic-tests` line that follows differs in wording, not in values (rules/workflow-globals.md:217, rules/workflow-reference.md:227). | consolidate | 11 | AUD-08-060 |
| DG-010 | DUP-033, DUP-034, DUP-040, DUP-047 | workflows/pae-finalize.md:8-8, workflows/pae-implement.md:8-8, workflows/pae-tests.md:13-13, workflows/pav-check.md:8-8, workflows/pav-close.md:8-8, workflows/pav-propose.md:16-16, workflows/phase-atomic-execution.md:9-9, workflows/phase-atomic-validation.md:9-9, workflows/pae-implement.md:18-18, workflows/pae-tests.md:23-24, workflows/pav-check.md:15-15, workflows/pav-close.md:15-15, workflows/pav-propose.md:24-24, workflows/phase-atomic-validation.md:41-41, workflows/pav-check.md:16-16, workflows/pav-close.md:16-16, workflows/pav-propose.md:25-25, workflows/pav-close.md:23-23, workflows/pav-propose.md:32-32 | workflows/pav-check.md → (preamble) | Each atomic workflow resolves its own argument and locates and checks its own progress block before acting; the stop messages name each workflow's phase. | condition-specific | none | - |
| DG-011 | DUP-049, DUP-050, DUP-051, DUP-063 | workflows/pe-execute.md:8-8, workflows/pe-finalize.md:8-8, workflows/phase-execution.md:9-9, workflows/phase-validation.md:9-9, workflows/pv-classify-fixes.md:8-8, workflows/pv-contract.md:8-8, workflows/pv-create-fixes.md:8-8, workflows/pv-execute-fixes.md:8-8, workflows/pv-finalize.md:8-8, workflows/pv-issues.md:8-8, workflows/pv-review.md:8-8, workflows/pe-execute.md:16-16, workflows/pe-finalize.md:15-15, workflows/phase-atomic-execution.md:8-8, workflows/phase-atomic-validation.md:8-8, workflows/phase-composite-validation.md:10-10, workflows/phase-execution.md:8-8, workflows/phase-validation.md:8-8, workflows/pv-contract.md:15-15, workflows/pv-create-fixes.md:15-15, workflows/pv-execute-fixes.md:15-15, workflows/pv-issues.md:15-15, workflows/pv-review.md:15-15 | workflows/phase-execution.md → (preamble) | Each phase workflow takes its task directory and stops on its own phase status; the stop messages name the phase. | condition-specific | none | - |
| DG-012 | DUP-035, DUP-036, DUP-037, DUP-038, DUP-041, DUP-042, DUP-048, DUP-062 | workflows/pae-implement.md:53-54, workflows/pae-tests.md:56-57, workflows/pae-implement.md:54-55, workflows/pae-tests.md:57-58, workflows/pae-implement.md:55-56, workflows/pae-tests.md:58-59, workflows/pae-implement.md:57-57, workflows/pae-tests.md:60-60, workflows/pav-check.md:24-25, workflows/phase-atomic-validation.md:21-22, workflows/pav-check.md:25-26, workflows/phase-atomic-execution.md:23-24, workflows/phase-atomic-validation.md:22-23, workflows/phase-execution.md:54-55, workflows/phase-validation.md:55-56, workflows/pv-contract.md:23-24, workflows/pv-review.md:28-29, workflows/pd-decompose.md:9-10, workflows/pd-design.md:9-10, workflows/pd-finalize.md:9-10, workflows/phase-validation.md:54-55, workflows/pv-contract.md:22-23, workflows/pv-review.md:27-28 | rules/workflow-globals.md → (preamble) | Each workflow loads the bootstrap rule of its own phase (atomic execution, atomic validation, discovery or validation) at its own entry. | condition-specific | none | - |
| DG-013 | DUP-043, DUP-044, DUP-045, DUP-046 | workflows/pav-check.md:28-28, workflows/phase-atomic-execution.md:26-26, workflows/phase-atomic-validation.md:25-25, workflows/pav-check.md:28-30, workflows/phase-atomic-execution.md:26-28, workflows/phase-atomic-validation.md:25-27, workflows/pav-check.md:30-31, workflows/phase-atomic-execution.md:28-29, workflows/phase-atomic-validation.md:27-28, workflows/pav-check.md:32-32, workflows/phase-atomic-execution.md:30-30, workflows/phase-atomic-validation.md:29-29 | rules/phase-atomic-execution.md → ## Context Bootstrap | The workflows resolve the description and parent paths before changing directories and name the base of a relative `working_dir:` (the atomic task directory, workflows/pav-check.md:28-30); the rule's Step 0 states the result for any caller (rules/phase-atomic-execution.md:16-20). | condition-specific | none | - |
| DG-014 | DUP-039 | workflows/pae-implement.md:74-74, workflows/pav-check.md:39-39 | workflows/pae-implement.md → ## Pre-check | /pae-implement reads the design constraints before writing code; /pav-check reads them to check the implementation against them. | condition-specific | none | - |
| DG-015 | DUP-052, DUP-053, DUP-054, DUP-055, DUP-056, DUP-057, DUP-058, DUP-059, DUP-060 | workflows/phase-discovery.md:135-135, workflows/phase-pipeline.md:19-19, workflows/phase-execution.md:18-19, workflows/phase-validation.md:19-20, workflows/spec-run.md:63-64, workflows/phase-execution.md:21-21, workflows/phase-validation.md:22-22, workflows/phase-execution.md:21-22, workflows/phase-validation.md:22-23, workflows/phase-execution.md:24-24, workflows/phase-validation.md:25-25, workflows/phase-execution.md:42-43, workflows/phase-validation.md:43-44, workflows/phase-execution.md:43-43, workflows/phase-validation.md:44-44, workflows/phase-execution.md:45-46, workflows/phase-validation.md:46-47, workflows/phase-execution.md:46-47, workflows/phase-validation.md:47-48 | rules/run-log.md → ## Workflow coverage and routing | Each orchestrator opens or inherits its own run and logs its own boundaries (/phase-execution, /phase-validation, /phase-discovery, /phase-pipeline, /spec-run). | condition-specific | none | - |
| DG-016 | DUP-061 | workflows/phase-pipeline.md:104-105, workflows/spec-run.md:133-134 | rules/workflow-reference.md → ## Multi-Phase Spec Rules | /phase-pipeline passes the phase to its children in the autonomous pipeline; /spec-run passes it to its sub-agents in orchestrated mode. | condition-specific | none | - |
| DG-017 | DUP-064 | workflows/suggest-commit-message.md:13-15, workflows/suggest-pr-description.md:12-14 | workflows/suggest-commit-message.md → ## Step 0 — Gather Diff Context | None: /suggest-pr-description reuses the context step of /suggest-commit-message and states the same stop. | intentional | none | - |
| DG-018 | none | workflows/phase-atomic-execution.md:76-98, workflows/pe-execute.md:41-62, workflows/spec-run.md:181-205, rules/workflow-reference.md:97-188 | rules/workflow-reference.md → ## Parent `plan.md` Table Format | /phase-atomic-execution reuses a caller's resolution only for the same invocation (workflows/phase-atomic-execution.md:97-98); /spec-run stops its setup when guidance is unavailable and never implements inline (workflows/spec-run.md:186, :203), the caller's own conservative path that the contract leaves to it (rules/workflow-reference.md:124-125). | consolidate | 11 | AUD-08-061 |

### Migration map

| Source | Decision | Targets | Spec 09 default | Deviation | Amendment |
|---|---|---|---|---|---|
| harness/claude/capabilities.md | keep | harness/claude/capabilities.md | harness/claude/capabilities.md | no | - |
| harness/claude/hooks.json | keep | harness/claude/hooks.json | harness/claude/hooks.json | no | - |
| harness/claude/permissions.json | keep | harness/claude/permissions.json | harness/claude/permissions.json | no | - |
| harness/codex/capabilities.md | keep | harness/codex/capabilities.md | harness/codex/capabilities.md | no | - |
| rules/git-flow.md | rename | rules/contract-git-flow.md | rules/contract-git-flow.md | no | - |
| rules/global-claude.md | move | harness/claude/always-on.md | harness/claude/always-on.md | no | - |
| rules/language.md | rename | rules/contract-language.md | rules/contract-language.md | no | - |
| rules/orchestration.md | rename | rules/contract-orchestration.md | rules/contract-orchestration.md | no | - |
| rules/phase-atomic-execution.md | split | rules/bootstrap-atomic-execution.md [(preamble), ## Context Bootstrap, ## Phase Behaviors]; rules/procedure-blocker-reconciliation.md [## Blocker Reconciliation]; rules/protocol-atomic-execution-conduct.md | rules/bootstrap-atomic-execution.md [(preamble), ## Context Bootstrap, ## Phase Behaviors]; rules/procedure-blocker-reconciliation.md [## Blocker Reconciliation] | no | - |
| rules/phase-atomic-validation.md | split | rules/bootstrap-atomic-validation.md [(preamble), ## Context Bootstrap, ## Phase Behaviors]; rules/protocol-atomic-validation-conduct.md | rules/bootstrap-atomic-validation.md | no | - |
| rules/phase-discovery.md | split | rules/bootstrap-discovery.md [(preamble), ## Context Bootstrap]; rules/protocol-discovery-conduct.md [## Codebase Reading Rules, ## Decision Protocol] | rules/bootstrap-discovery.md [(preamble), ## Context Bootstrap]; rules/protocol-discovery-conduct.md [## Codebase Reading Rules, ## Decision Protocol] | no | - |
| rules/phase-execution.md | rename | rules/bootstrap-execution.md | rules/bootstrap-execution.md | no | - |
| rules/phase-validation.md | rename | rules/bootstrap-validation.md | rules/bootstrap-validation.md | no | - |
| rules/quick-flow.md | rename | rules/contract-quick-flow.md | rules/contract-quick-flow.md | no | - |
| rules/run-log.md | rename | rules/contract-run-log.md | rules/contract-run-log.md | no | - |
| rules/tdd.md | rename | rules/contract-tdd.md | rules/contract-tdd.md | no | - |
| rules/workflow-globals.md | rename | rules/contract-phases.md | rules/contract-phases.md | no | - |
| rules/workflow-reference.md | split | rules/contract-state-files.md [(preamble), ## File Responsibility, ## Description Amendment, ## Parent `plan.md` Table Format, ## Parent `state.md` — `## Subtask Progress` Format, ## Status Lifecycle Notes, ## Key State-File Markers, ## Reference Tables (moved from workflow-globals), ## Status Translation Table, ## Protected Sections Contract, ## Multi-Phase Spec Rules, ## .ai/memory/state.md Entry Format, ## .ai/project_state.md Update Rules, ## Legacy tasks, ## Project .ai/ Contract, ## File Location Reference]; rules/protocol-autonomous-decision.md [## Autonomous Decision Protocol]; rules/protocol-subtask-classifier.md [## Autonomous Subtask Classifier, ## Decomposition Rules] | rules/contract-state-files.md [(preamble), ## File Responsibility, ## Description Amendment, ## Parent `plan.md` Table Format, ## Parent `state.md` — `## Subtask Progress` Format, ## Status Lifecycle Notes, ## Key State-File Markers, ## Reference Tables (moved from workflow-globals), ## Status Translation Table, ## Protected Sections Contract, ## Multi-Phase Spec Rules, ## .ai/memory/state.md Entry Format, ## .ai/project_state.md Update Rules, ## Legacy tasks, ## Project .ai/ Contract, ## File Location Reference]; rules/protocol-autonomous-decision.md [## Autonomous Decision Protocol]; rules/protocol-subtask-classifier.md [## Autonomous Subtask Classifier, ## Decomposition Rules] | no | - |
| templates/codex-global-AGENTS.md | move | harness/codex/always-on.md | harness/codex/always-on.md | no | - |
| workflows/PIPELINE.md | move | docs/PIPELINE.md | docs/PIPELINE.md | no | - |
| workflows/adr-new.md | keep | workflows/adr-new.md | workflows/adr-new.md | no | - |
| workflows/bugfix.md | keep | workflows/bugfix.md | workflows/bugfix.md | no | - |
| workflows/compress-state.md | keep | workflows/compress-state.md | workflows/compress-state.md | no | - |
| workflows/context-pack.md | keep | workflows/context-pack.md | workflows/context-pack.md | no | - |
| workflows/onboard-legacy-project.md | keep | workflows/onboard-legacy-project.md | workflows/onboard-legacy-project.md | no | - |
| workflows/pae-finalize.md | rename | workflows/atomic-execution-finalize.md | workflows/atomic-execution-finalize.md | no | - |
| workflows/pae-implement.md | rename | workflows/atomic-execution-implement.md | workflows/atomic-execution-implement.md | no | - |
| workflows/pae-tests.md | rename | workflows/atomic-execution-tests.md | workflows/atomic-execution-tests.md | no | - |
| workflows/pav-check.md | rename | workflows/atomic-validation-check.md | workflows/atomic-validation-check.md | no | - |
| workflows/pav-close.md | rename | workflows/atomic-validation-close.md | workflows/atomic-validation-close.md | no | - |
| workflows/pav-propose.md | rename | workflows/atomic-validation-propose.md | workflows/atomic-validation-propose.md | no | - |
| workflows/pd-analyze.md | rename | workflows/discovery-analyze.md | workflows/discovery-analyze.md | no | - |
| workflows/pd-archive.md | rename | workflows/discovery-archive.md | workflows/discovery-archive.md | no | - |
| workflows/pd-decompose.md | rename | workflows/discovery-decompose.md | workflows/discovery-decompose.md | no | - |
| workflows/pd-design.md | rename | workflows/discovery-design.md | workflows/discovery-design.md | no | - |
| workflows/pd-finalize.md | rename | workflows/discovery-finalize.md | workflows/discovery-finalize.md | no | - |
| workflows/pd-select-model.md | rename | workflows/discovery-select-model.md | workflows/discovery-select-model.md | no | - |
| workflows/pe-execute.md | rename | workflows/execution-execute.md | workflows/execution-execute.md | no | - |
| workflows/pe-finalize.md | rename | workflows/execution-finalize.md | workflows/execution-finalize.md | no | - |
| workflows/phase-atomic-execution.md | rename | workflows/atomic-execution.md | workflows/atomic-execution.md | no | - |
| workflows/phase-atomic-validation.md | rename | workflows/atomic-validation.md | workflows/atomic-validation.md | no | - |
| workflows/phase-composite-validation.md | rename | workflows/composite-validation.md | workflows/composite-validation.md | no | - |
| workflows/phase-discovery.md | rename | workflows/discovery.md | workflows/discovery.md | no | - |
| workflows/phase-execution.md | rename | workflows/execution.md | workflows/execution.md | no | - |
| workflows/phase-pipeline.md | rename | workflows/pipeline.md | workflows/pipeline.md | no | - |
| workflows/phase-validation.md | rename | workflows/validation.md | workflows/validation.md | no | - |
| workflows/pv-classify-fixes.md | rename | workflows/validation-classify-fixes.md | workflows/validation-classify-fixes.md | no | - |
| workflows/pv-contract.md | rename | workflows/validation-contract.md | workflows/validation-contract.md | no | - |
| workflows/pv-create-fixes.md | rename | workflows/validation-create-fixes.md | workflows/validation-create-fixes.md | no | - |
| workflows/pv-execute-fixes.md | rename | workflows/validation-execute-fixes.md | workflows/validation-execute-fixes.md | no | - |
| workflows/pv-finalize.md | rename | workflows/validation-finalize.md | workflows/validation-finalize.md | no | - |
| workflows/pv-issues.md | rename | workflows/validation-issues.md | workflows/validation-issues.md | no | - |
| workflows/pv-review.md | rename | workflows/validation-review.md | workflows/validation-review.md | no | - |
| workflows/restack.md | keep | workflows/restack.md | workflows/restack.md | no | - |
| workflows/retro.md | keep | workflows/retro.md | workflows/retro.md | no | - |
| workflows/spec-draft.md | keep | workflows/spec-draft.md | workflows/spec-draft.md | no | - |
| workflows/spec-run.md | keep | workflows/spec-run.md | workflows/spec-run.md | no | - |
| workflows/spec-sync.md | keep | workflows/spec-sync.md | workflows/spec-sync.md | no | - |
| workflows/suggest-commit-message.md | keep | workflows/suggest-commit-message.md | workflows/suggest-commit-message.md | no | - |
| workflows/suggest-commit-pr.md | keep | workflows/suggest-commit-pr.md | workflows/suggest-commit-pr.md | no | - |
| workflows/suggest-pr-description.md | keep | workflows/suggest-pr-description.md | workflows/suggest-pr-description.md | no | - |

### Validator and test impact

| Source | Decision | Validator text | Validator check-description | Validator comment | Other tests | Frozen | Hooks | Other active |
|---|---|---|---|---|---|---|---|---|
| rules/git-flow.md | rename | 81 | 7 | 2 | 3 | 2 | 2 | 60 |
| rules/global-claude.md | move | 9 | 0 | 0 | 1 | 0 | 0 | 18 |
| rules/language.md | rename | 5 | 0 | 0 | 0 | 0 | 0 | 18 |
| rules/orchestration.md | rename | 29 | 1 | 0 | 0 | 0 | 0 | 31 |
| rules/phase-atomic-execution.md | split | 8 | 2 | 1 | 2 | 0 | 0 | 35 |
| rules/phase-atomic-validation.md | split | 8 | 2 | 0 | 0 | 0 | 0 | 26 |
| rules/phase-discovery.md | split | 17 | 4 | 1 | 4 | 1 | 0 | 34 |
| rules/phase-execution.md | rename | 26 | 2 | 0 | 4 | 2 | 0 | 23 |
| rules/phase-validation.md | rename | 5 | 0 | 0 | 1 | 0 | 0 | 29 |
| rules/quick-flow.md | rename | 21 | 4 | 4 | 0 | 0 | 0 | 41 |
| rules/run-log.md | rename | 39 | 5 | 4 | 15 | 14 | 0 | 36 |
| rules/tdd.md | rename | 23 | 4 | 0 | 5 | 0 | 0 | 49 |
| rules/workflow-globals.md | rename | 53 | 20 | 6 | 7 | 9 | 0 | 57 |
| rules/workflow-reference.md | split | 65 | 17 | 6 | 11 | 6 | 0 | 63 |
| templates/codex-global-AGENTS.md | move | 2 | 0 | 0 | 0 | 0 | 0 | 6 |
| workflows/PIPELINE.md | move | 22 | 3 | 1 | 3 | 0 | 0 | 10 |
| workflows/pae-finalize.md | rename | 20 | 4 | 3 | 1 | 0 | 0 | 39 |
| workflows/pae-implement.md | rename | 34 | 11 | 4 | 7 | 0 | 0 | 77 |
| workflows/pae-tests.md | rename | 65 | 10 | 2 | 38 | 5 | 0 | 93 |
| workflows/pav-check.md | rename | 24 | 4 | 2 | 2 | 0 | 0 | 43 |
| workflows/pav-close.md | rename | 20 | 4 | 4 | 1 | 0 | 0 | 35 |
| workflows/pav-propose.md | rename | 23 | 3 | 2 | 1 | 0 | 0 | 36 |
| workflows/pd-analyze.md | rename | 24 | 4 | 1 | 7 | 3 | 0 | 36 |
| workflows/pd-archive.md | rename | 18 | 3 | 3 | 0 | 0 | 0 | 18 |
| workflows/pd-decompose.md | rename | 48 | 18 | 3 | 3 | 0 | 0 | 52 |
| workflows/pd-design.md | rename | 12 | 1 | 0 | 3 | 0 | 0 | 26 |
| workflows/pd-finalize.md | rename | 26 | 8 | 3 | 4 | 1 | 0 | 38 |
| workflows/pd-select-model.md | rename | 12 | 3 | 0 | 14 | 2 | 0 | 21 |
| workflows/pe-execute.md | rename | 21 | 3 | 2 | 3 | 2 | 0 | 28 |
| workflows/pe-finalize.md | rename | 25 | 8 | 4 | 0 | 1 | 0 | 37 |
| workflows/phase-atomic-execution.md | rename | 14 | 2 | 1 | 2 | 2 | 0 | 44 |
| workflows/phase-atomic-validation.md | rename | 16 | 2 | 0 | 0 | 0 | 0 | 36 |
| workflows/phase-composite-validation.md | rename | 27 | 5 | 3 | 0 | 0 | 0 | 25 |
| workflows/phase-discovery.md | rename | 23 | 4 | 1 | 5 | 1 | 0 | 76 |
| workflows/phase-execution.md | rename | 33 | 2 | 0 | 4 | 2 | 0 | 39 |
| workflows/phase-pipeline.md | rename | 33 | 6 | 6 | 2 | 1 | 0 | 43 |
| workflows/phase-validation.md | rename | 10 | 0 | 0 | 1 | 1 | 0 | 47 |
| workflows/pv-classify-fixes.md | rename | 22 | 1 | 2 | 0 | 0 | 0 | 18 |
| workflows/pv-contract.md | rename | 14 | 2 | 0 | 0 | 0 | 0 | 38 |
| workflows/pv-create-fixes.md | rename | 27 | 5 | 1 | 0 | 0 | 0 | 30 |
| workflows/pv-execute-fixes.md | rename | 14 | 1 | 1 | 0 | 0 | 0 | 25 |
| workflows/pv-finalize.md | rename | 30 | 6 | 5 | 0 | 0 | 0 | 36 |
| workflows/pv-issues.md | rename | 10 | 0 | 0 | 0 | 0 | 0 | 27 |
| workflows/pv-review.md | rename | 12 | 1 | 0 | 0 | 0 | 0 | 39 |

### Spec 09 inputs

| Source | Decision | Targets | Amendment |
|---|---|---|---|

req21 verdict: not-covered

| Statement | Text | Covered by |
|---|---|---|
| rules/phase-discovery.md:38 | - Use `.ai/memory/architecture.md` to scope source reads. Read affected source when verifying behavior, freshness, or a concrete pattern; an inventory description alone is not implementation evidence. | - |
| rules/phase-discovery.md:39 | - Budget: max 12 files (8 entry-points + 4 one-level-deeper). Hard limit. | - |
| rules/phase-discovery.md:40 | - Document every file read with reason: "read to verify <specific behavior or gap>." | - |
| rules/phase-discovery.md:41 | - Stop reading when affected parts are understood. | - |
| rules/phase-discovery.md:45 | Discovery runs **autonomously by default**; `--step-by-step` switches it to manual review. See `/phase-discovery → ## Execution Modes` (the workflow, not this rules file). | rules/workflow-reference.md:426 |
| rules/phase-discovery.md:48 | **Autonomous mode (default):** | rules/workflow-reference.md:426 |
| rules/phase-discovery.md:49 | - Task requirements unclear → resolve by research in this order: `.ai/principles/*` → `.ai/adr/` → `.ai/memory/*` → existing codebase patterns → general best practice. Record the resolution in `## Task Analysis → ### Assumptions`. Never infer intent silently — inferring is allowed, hiding it is not. | - |
| rules/phase-discovery.md:53 | - Decomposition boundary or architectural choice ambiguous → generate 2–3 options and resolve them with `workflow-reference → ## Autonomous Decision Protocol`. Record the scoring and rationale. | rules/workflow-reference.md:430 |
| rules/phase-discovery.md:56 | - Steps 1→4 run back-to-back. A step's completion report is not a handoff. | - |
| rules/phase-discovery.md:57 | - Stop only on the Autonomous Decision Protocol's escalation conditions or a Guard confirmation that would overwrite existing artifacts. | - |
| rules/phase-discovery.md:60 | **Step-by-step mode (`--step-by-step`):** | - |
| rules/phase-discovery.md:61 | - Task requirements unclear → ask before proceeding. Never infer intent silently. | - |
| rules/phase-discovery.md:62 | - Decomposition boundary ambiguous → present 2–3 options with trade-offs, wait for decision. | - |
| rules/phase-discovery.md:63 | - Architectural variants → present, wait for the user's choice. | - |
| rules/phase-discovery.md:64 | - After each of Steps 1–4 → stop and wait for review. | - |

### Findings

| ID | Type | Severity | Source | Section | Owner | Blocks 09 | Status | Observation | Closure |
|---|---|---|---|---|---|---|---|---|---|
| AUD-08-001 | reference-defect | minor | rules/git-flow.md | ## Recorded state — required for resume and for restack | 09 | true | open | Two section references omit the `##` marker of their target heading: `workflow-globals → Canonical Status Formats` and `workflow-reference → Protected Sections Contract`. Both targets exist as level-2 headings, so a reader finds them, but the cross-reference syntax requires the marker and the naming migration's executable-reference grammar does not read the unmarked form. | Both spans carry the marker of the target heading (`## Canonical Status Formats`, `## Protected Sections Contract`); the naming migration fixes them under AMD-08-01. |
| AUD-08-002 | ambiguous-name | minor | rules/phase-atomic-validation.md | ## Context Bootstrap | 09 | false | open | `phase-atomic-execution → ## Context Bootstrap` names a stem that is both a rule and a workflow, and both files have a `## Context Bootstrap` heading. The intended target is the rule, whose bootstrap holds the runbook resolution with the umbrella fallback. | The reference names a stem that is unique after the naming migration (the rule's new bootstrap name). |
| AUD-08-003 | ambiguous-name | minor | rules/phase-discovery.md | ## Decision Protocol | 09 | false | open | `/phase-discovery → ## Execution Modes` names a stem shared by the rule and the workflow. Only the workflow has the heading, and the prose adds "the workflow, not this rules file" to disambiguate. | The reference names the workflow by a stem that no rule shares after the naming migration. |
| AUD-08-004 | reference-defect | major | rules/quick-flow.md | (file) | 09 | true | open | Lines 21 and 22 cite `workflow-globals → Never auto-advance between phases` and `workflow-globals → Test-first execution`; neither is a heading of rules/workflow-globals.md, both are bold paragraph labels inside its `## Context Pack` section (:56, :114). Lines 125-126 split `workflow-globals → Canonical Status Formats` across a line break, so no span forms and no tool reads it. | Each reference names an existing heading in the marked form on one line: the cited paragraph's own heading once AUD-08-026 gives it one, otherwise `## Context Pack`, whose extent holds both paragraphs; the naming migration fixes them under AMD-08-01. |
| AUD-08-005 | reference-defect | minor | rules/tdd.md | (file) | 09 | true | open | Two section references omit the `##` marker: `workflow-globals → Canonical Status Formats` (:35) and `quick-flow → The quick path` (:201), the second also a bare prefix of the heading `## The quick path — what changes`. | Both spans carry the marker of the target heading (`## Canonical Status Formats`, `## The quick path — what changes`); the naming migration fixes them under AMD-08-01. |
| AUD-08-006 | accepted-observation | minor | rules/workflow-globals.md | ## Context Pack | none | false | open | The span `.ai/context-pack.md` names the pack file a consumer project generates, not workflows/context-pack.md; the md-name match on its last path component resolves to the workflow and sets the md suffix flag. Read in context the text is correct and needs no change. The same match occurs in docs/USAGE.md:803 and .ai/principles/domain.md:49, where the span `.ai/context-pack.md` also names the generated pack file. | No change; the edge stays recorded as correct on reading. |
| AUD-08-007 | reference-defect | minor | rules/workflow-globals.md | ## Flow tiers (quick \| full) | 09 | true | open | `quick-flow →` and `## Mid-flight escalation` are split across a line break, so no span forms. Joined as written, it names only the start of the heading `## Mid-flight escalation (quick → full)` (rules/quick-flow.md:137). | The reference sits on one line as one span that names `## Mid-flight escalation (quick → full)` with its marker; no heading is renamed; the naming migration fixes it under AMD-08-01. |
| AUD-08-008 | mixed-kind | minor | rules/phase-atomic-execution.md | ## Blocker Reconciliation | 09 | false | open | The file holds a bootstrap (`## Context Bootstrap`, `## Phase Behaviors`, :8-51) and a procedure triggered by `atomic-execution: blocked` on entry (`## Blocker Reconciliation`, :53-71). The reading agrees with the naming migration's section map, which moves the procedure to its own rule. | The section map's split of this file is carried out, or amended with a recorded reason. |
| AUD-08-009 | mixed-kind | minor | rules/phase-discovery.md | ## Decision Protocol | 09 | false | open | The file holds a bootstrap (`## Context Bootstrap`, :8-34) and two conduct sections: `## Codebase Reading Rules` (:36-41: scope, budget, record and stop criteria for reading) and `## Decision Protocol` (:43-64: how ambiguities are resolved in each mode). The reading agrees with the naming migration's section map (bootstrap and discovery conduct protocol). | The section map's split is carried out, or amended with a recorded reason; the statement coverage of the two conduct sections decides whether the autonomous decision protocol can receive them. |
| AUD-08-010 | mixed-kind | minor | rules/quick-flow.md | ## Worked example A — rejected by the gate (export pipeline changes) | 11 | false | open | The always-on contract carries two worked examples (:156-202) and a pointer to an incident that the file does not explain (:39-40, repeated in rules/workflow-globals.md:140-141). Both explain rather than oblige; the gate (:27-57), the quick path (:61-114) and the escalation (:137-152) stay reachable without them. | The worked examples move to a reference file that is not loaded by default, and the incident pointer is either explained or removed from the contract text. |
| AUD-08-011 | mixed-kind | minor | rules/tdd.md | ## Characterization mode — behaviour-preserving work | 09 | false | open | The contract holds a decision protocol (`## Test-level gate`, :54-82), a procedure triggered by behaviour-preserving work (`### The procedure`, :132-151) and a rationale section (`## Why the order matters`, :219-226). The gate and the procedure are invoked from `/pae-tests` and from the quick path, so they stay with the contract; the rationale is short. | The map records the kept sections under the contract with a reason, or splits the gate and procedure through an amendment. |
| AUD-08-012 | mixed-kind | minor | rules/run-log.md | ## Workflow coverage and routing | 09 | false | open | The contract holds the three-call logging procedure every pipeline follows (`## How a pipeline logs`, :58-112) and a decision table for each checkpoint boundary (`## Workflow coverage and routing`, :116-184). | The map keeps the sections in the contract with a recorded reason, or splits them through an amendment. |
| AUD-08-013 | conditional-context | major | rules/run-log.md | ## Native hook adapter | 11 | false | open | The always-on rule carries the internal contracts of the helper and the hook adapter: argument validation and writes (:280-302), correlated interval arithmetic (:304-373), native transcript parsing and private ownership states (:375-521) and lint output (:523-560). They bind scripts/log-step.sh and hooks/log-step-hook.sh; the workflow agent acts on the three calls (:58-112) and the routing table (:116-184), and the adapter part applies only where a capability record declares `hooks: yes`. | The helper and adapter internals are classified as reference or conditional context, loaded only for work on the helper or where hooks are declared, and the agent-facing calls and routing table stay in the always-loaded contract. |
| AUD-08-014 | mixed-kind | minor | rules/workflow-globals.md | (file) | 09 | false | open | The always-on contract embeds a decision protocol among cross-workflow obligations inside `## Context Pack` ("Wait for user decisions", :60, and the trust mechanism, :98-102) and an environment lookup in the preamble (rule resolution per harness, :19-33). | The map records where the embedded protocol and lookup go, with headings that can be cited, or keeps them with a recorded reason. |
| AUD-08-015 | legacy-mention | minor | rules/workflow-globals.md | (preamble) | 09 | false | open | The preamble instructs how a rule reference resolves on Windsurf and Devin (rules directories and bare basenames) next to the skill resolution of the two current harnesses; the mentions are active behaviour, not history. | The Windsurf and Devin resolution is removed or marked historical when the naming migration retires those environments. |
| AUD-08-016 | naming | minor | rules/workflow-globals.md | (preamble) | 09 | false | open | The rule-resolution instruction chooses between a bare basename and the `rule-` skill prefix by harness name ("On Claude Code and Codex", "on Windsurf and Devin") rather than by a declared capability such as rules delivered as skills. | The resolution is stated by capability, with the harness facts in the capability records. |
| AUD-08-017 | mixed-kind | minor | rules/workflow-reference.md | (file) | 09 | false | open | Besides contracts and the two decision protocols that the section map already separates, the file holds a procedure (`## Description Amendment`, :66-91; the composite promotion steps inside the classifier, :530-544) and reference material (`## Legacy tasks`, :584-586, which names one consumer's old directories; `## File Location Reference`, :619-634). | The map records where the procedure and reference sections go, or keeps them with a recorded reason. |
| AUD-08-018 | other | major | rules/workflow-reference.md | (file) | 11 | false | open | Lines 346-373 (composite protected lines, protected `plan.md` items and protected fields) continue the list of `## Protected Sections Contract` (:280-323) but sit under `## Multi-Phase Spec Rules` (:325), after a rule line at :344. `## Reference Tables (moved from workflow-globals)` (:259) is an empty section followed directly by `## Status Translation Table` (:261). | The protected lines sit under the protected-sections heading and the empty heading is removed or given content, before any section-level loading or split of the file. |
| AUD-08-019 | mixed-kind | minor | rules/orchestration.md | ## Escalation protocol | 09 | false | open | The contract of roles and shared files ends with a decision protocol: class A and class B routing and the conditions that always stop the run (:137-191). It is cohesive with the roles it routes between. | The map keeps the protocol in the contract with a recorded reason, or splits it through an amendment. |
| AUD-08-020 | mixed-kind | minor | rules/git-flow.md | ## Preflight (mandatory, before any branch is created) | 09 | false | open | The contract holds a start gate (`## Preflight`, :16-37: refuse unless every check holds) and the owner approval protocol inside `## Safety rails` (:251-268). | The map keeps both in the contract with a recorded reason, or splits them through an amendment. |
| AUD-08-021 | naming | minor | rules/language.md | (preamble) | 09 | false | open | Lines 20-21 are written as comments but are Markdown level-1 headings, and :21 points to one harness's personal instruction file in a rule deployed to every harness. | The lines become prose that names the per-harness personal instruction file by capability or adapter, or move to the harness adapters. |
| AUD-08-022 | other | major | rules/global-claude.md | ## AST-GREP STRUCTURAL SEARCH POLICY | owner | false | open | The always-on body names one host ("On this Linux host") and gives two absolute home-directory paths of one machine for the ast-grep program and its configuration. The file is copied as the global instructions of every installation. | The owner replaces the machine-specific lines with a portable instruction or a per-installation value, or records that the file is personal and not shipped. |
| AUD-08-023 | other | major | templates/codex-global-AGENTS.md | ## AST-GREP STRUCTURAL SEARCH POLICY | owner | false | open | The Codex always-on template names one host ("On this Linux host") and gives two absolute home-directory paths of one machine for the ast-grep program and its configuration. The template is copied as the global instructions of every installation. | The owner replaces the machine-specific lines with a portable instruction or a per-installation value, or records that the template is personal and not shipped. |
| AUD-08-024 | conditional-context | minor | harness/claude/capabilities.md | ## git-rails | 11 | false | open | The git-rails record (:29-90), including twenty residual-risk rows (:69-90), is appended to the always-on file delivered into every session. Workflows act on the Enforcement values of rules/git-flow.md:219-243; the risk table informs the owner and is cited only as the place where unseen commands are listed (rules/git-flow.md:249). | The residual-risk register is delivered as reference context and the always-on part keeps the capability lines a workflow decides on. |
| AUD-08-025 | other | minor | rules/workflow-reference.md | (file) | 11 | false | open | Load-line detection marks spans on lines whose verb describes another reader, not a load: here :227 ("read it as not-started"), :247 and :311 ("read by /pe-finalize") and :282 ("read by orchestrators"); likewise rules/tdd.md:39, rules/run-log.md:86 and :582, rules/phase-atomic-execution.md:55 and rules/workflow-globals.md:36. Of the fourteen load edges in rule and adapter files only rules/workflow-globals.md:32 and :44 describe a load of the target, and :44 resolves to the wrong file (AUD-08-006). | The textual load detection distinguishes a load instruction from a description of another reader, or the load inventory is taken from declared loads. |
| AUD-08-026 | other | major | rules/workflow-globals.md | ## Context Pack | 11 | false | open | `## Context Pack` (:40) follows the last preamble line (:39) without a blank line and opens one section that runs to :127. Besides the optional pack it holds the global phase principles: never auto-advance (:56), continue never restart (:58), wait for user decisions (:60), the registry of workflow-declared mode overrides (:62-85), the `--batch` meaning (:87-94), the trust mechanism (:98-102), orchestrated mode (:106-112) and test-first execution (:114-120). The registry has no heading of its own although workflows/pav-propose.md:12 cites it as `workflow-globals → Workflow-declared mode overrides`. | The principles stand under headings of their own (the mode-override registry among them) before any section-level loading or split of the file, and `## Context Pack` holds only the pack. |
| AUD-08-027 | mixed-kind | minor | rules/quick-flow.md | ## The escalation gate | 09 | false | open | Besides the worked examples (AUD-08-010) the contract holds a decision protocol (`## The escalation gate`, :27-57: four conditions decide quick or full) and two procedures (`## Setting the flow (Discovery)`, :118-133, run by /pd-analyze; `## Mid-flight escalation (quick → full)`, :137-152, triggered by a breach). | The map keeps the gate and the procedures in the contract with a recorded reason, or splits them through an amendment. |
| AUD-08-028 | conditional-context | minor | rules/workflow-reference.md | ## Parent `plan.md` Table Format | 11 | false | open | Most of the section (:97-188) is the model-resolution protocol and the catalog guidance preflight procedure (:99-129); the table format itself is :190-203. Both apply only when a plan uses model columns or a model-specific request is made, but they load with every use of the state-file contract. | The model-resolution protocol and preflight are loaded only when model columns or a model-specific request are present, and the table format stays with the state-file contract. |
| AUD-08-029 | other | minor | templates/codex-global-AGENTS.md | (preamble) | 09 | false | open | Lines 2-3 are written as comments (a managed-file notice and a note on how the harness merges the file) but are Markdown level-1 headings; line 1 is the title. | The notices become prose or a comment form that Markdown does not read as a heading when the file moves to the Codex adapter. |
| AUD-08-030 | other | minor | rules/global-claude.md | (preamble) | 09 | false | open | Line 2 is written as a comment (the scope of the standards) but is a Markdown level-1 heading; line 1 is the title. | The scope note becomes prose when the file moves to the Claude Code adapter. |
| AUD-08-031 | accepted-observation | minor | workflows/phase-execution.md | ## Execution | none | false | open | Two references name `quick-flow → ## Mid-flight escalation (quick → full)`, whose heading exists at rules/quick-flow.md:137. This audit's grammar splits components at every ` → ` and reports a missing heading. The naming migration's form-2 pattern (spec 09 DM-16) captures the whole heading instead, because the text after the inner ` → ` does not start with `#` and the pattern is anchored at the end; the captured heading equals the heading line. Both references are correct on reading and resolve in the migration's grammar. | No change; the edges stay recorded as correct on reading. |
| AUD-08-032 | ambiguous-name | minor | workflows/pae-tests.md | ## Pre-check | 09 | false | open | Four atomic workflows name `phase-atomic-execution → ## Context Bootstrap` for the runbook resolution with its umbrella fallback. The stem is both a rule and a workflow and both files have a `## Context Bootstrap` heading; on reading the rule is meant (rules/phase-atomic-execution.md:21-25). This is the pattern AUD-08-002 records in rules/phase-atomic-validation.md:21. | Every reference names a stem that is unique after the naming migration (the rule's bootstrap name, the workflow `atomic-execution`). |
| AUD-08-033 | reference-defect | minor | workflows/pv-contract.md | ## Instructions | 09 | true | open | Two section references omit the `##` marker of their target heading: `quick-flow → The quick path` (target `## The quick path — what changes`, rules/quick-flow.md:61) and `workflow-reference → Autonomous Subtask Classifier → Runtime self-correction` (targets rules/workflow-reference.md:487 and :530). Both targets exist, so a reader finds them, but the cross-reference syntax requires the marker and the migration's executable-reference grammar does not read the unmarked form. | Both spans carry the markers of their target headings (`## The quick path — what changes`; `## Autonomous Subtask Classifier → ### Runtime self-correction (tripwire)`); the naming migration fixes them under AMD-08-01. |
| AUD-08-034 | accepted-observation | minor | workflows/context-pack.md | (file) | none | false | open | Both edges read `context-pack.md` inside the span `AI_DIR/context-pack.md`, which names the generated pack file in the project's knowledge base, not the workflow file `workflows/context-pack.md`. The token grammar matches the file name and resolves it to the workflow; on reading the references are correct. AUD-08-006 records the same resolution in rules/workflow-globals.md. | No change; the observation stands while the pack keeps this file name. |
| AUD-08-035 | reference-defect | minor | workflows/phase-pipeline.md | (file) | 09 | true | open | Three lists map each child command to its workflow file name (`/pd-analyze` → `pd-analyze.md`). The file names are suffixed references outside the migration's grammar; `phase-atomic-execution.md` and `phase-atomic-validation.md` are also ambiguous between a rule and a workflow. The lists restate children that the phase orchestrators own, and line 109 forbids replaying them separately. | The lists name commands only (`/<name>` without `.md`), or are removed in favour of the phase orchestrators; the naming migration fixes them under AMD-08-01. |
| AUD-08-036 | reference-defect | minor | workflows/pav-propose.md | (preamble) | 09 | true | open | The proposal semantics are cited as `workflow-globals → Workflow-declared mode overrides`, which is no heading: the registry sits inside `## Context Pack` (rules/workflow-globals.md:40, :62). This is the missing registry heading that AUD-08-026 records; this finding records the citing edge so the defect is not reported twice. Two active knowledge files cite the same non-heading: .ai/memory/architecture.md:164 and .ai/principles/architecture.md:41. | The span names an existing heading in the marked form: the registry's own heading once AUD-08-026 gives it one, otherwise `## Context Pack`, whose extent holds the registry; the naming migration fixes this span and the two reader citations under AMD-08-01. |
| AUD-08-037 | mixed-kind | minor | workflows/restack.md | ## Recovery journal | 11 | false | open | The workflow holds a contract: `## Recovery journal` defines the journal schema and the exact command forms that the git-rails hook verifies (restack.md:44-46, :90-93; rules/git-flow.md:205, :237). The rest of the file is the workflow's steps. | The section stays in place, since the validator pins the heading in this file (scripts/validate-contracts.sh:5636) and only this workflow writes the journal; context tiering records it as contract when it classifies the workflow. |
| AUD-08-038 | mixed-kind | minor | workflows/pv-finalize.md | ## Instructions | 11 | false | open | Step 3 of `## Instructions` (lines 62-181) is the canonical ADR trigger, body template, numbering, file name and index schema. It is consumed by /adr-new (adr-new.md:11-13), /pd-design (pd-design.md:77), /spec-sync (spec-sync.md:101-102) and /bugfix (bugfix.md:138), and line 63 warns readers not to execute the other finalization steps while loading it. | The ADR schema is a section of its own (or a contract rule) that the four consumers cite by heading, and the finalization step cites it in turn. |
| AUD-08-039 | conditional-context | major | workflows/phase-execution.md | ## Run Logging | 11 | false | open | Three orchestrators instruct to follow the `run-log` rule in full (phase-execution.md:18, phase-validation.md:19, spec-run.md:63); /bugfix follows the whole rule at :30. The rule has 585 lines, while a prompt-logged boundary needs `## Workflow coverage and routing` (rules/run-log.md:116), which /phase-discovery and /phase-pipeline cite as their only section (phase-discovery.md:135, phase-pipeline.md:19). | /phase-execution, /phase-validation and /bugfix name the sections they use, as /phase-discovery does; /spec-run names its routing and dispatch sections instead of the whole rule; the rest loads only when the condition that needs it holds. |
| AUD-08-040 | conditional-context | major | workflows/pae-implement.md | ## Tripwire Check (composite promotion) | 11 | false | open | The tripwire loads the whole `workflow-reference` rule (634 lines) to use the Autonomous Subtask Classifier (rules/workflow-reference.md:487-548), at the start and again at the midpoint of every leaf. /pav-close (:32), /pe-finalize (:27) and /pv-finalize (:30) likewise load the whole rule for the status translation table, the memory entry format or the project-state update rules. | Each of these workflows loads only the section it uses by its marked heading (`workflow-reference → ## Autonomous Subtask Classifier`, `## Status Translation Table`, `## .ai/memory/state.md Entry Format`, `## .ai/project_state.md Update Rules`). |
| AUD-08-041 | conditional-context | minor | workflows/pd-select-model.md | ## Instructions | 11 | false | open | Routine selection is offline (pd-select-model.md:15), yet every run loads the refresh procedure (:66-85) and the refresh candidate schema (:129-139), which apply only with `--refresh`, and the cost-comparison contract (:162-170), which applies only when the owner supplies qualified comparable-task evaluations. | The refresh procedure, the candidate schema and the cost-comparison contract load only under their conditions (a flag or a supplied evaluation). |
| AUD-08-042 | report-repeat | minor | workflows/pae-tests.md | ## Report | 11 | false | open | The test level is reported before writing (:80-86), the criterion mapping before writing code (:133-139), and both again with the digest in the final report (:237-241). The final digest is suppressed only by `--batch` or /phase-pipeline, but /phase-atomic-execution calls /pae-tests without the flag (:101) and reports the level and RED result once more (:110-111); /spec-run asks the worker to report the RED digest after the step (:318, :325-326); /phase-pipeline asks for `--batch` (:47), but no workflow on its call chain passes it to /pae-tests. | The level, mapping and digest are reported once per leaf at the boundary that needs them, and the callers that want suppression pass it on the actual call. |
| AUD-08-043 | report-repeat | minor | workflows/phase-pipeline.md | ## Phase 1 — Discovery | 11 | false | open | After Discovery completes, the pipeline reports the chosen approach (:116), which /pd-finalize already reported as the single final report that its parent reuses (pd-finalize.md:104-107; phase-discovery.md:178-179); the pipeline's final report restates the phase outcomes again (:153-156). | The pipeline reuses /pd-finalize's report as a progress marker and adds only what it decides itself. |
| AUD-08-044 | report-repeat | minor | workflows/phase-execution.md | ## Execution | 11 | false | open | /phase-execution reports completed and skipped work, verification and paths and displays `Execution complete. Run /phase-validation <task-directory> to start validation.` (:100-101) right after /pe-finalize reported outcomes, verification and paths and displayed the same line (pe-finalize.md:106-107). /phase-validation repeats /pv-finalize's report the same way (phase-validation.md:105; pv-finalize.md:204-205), and /phase-atomic-validation reports the final verdict and status (phase-atomic-validation.md:85) right after /pav-close reported the closure and status (pav-close.md:70). /phase-discovery avoids this by letting /pd-finalize supply the single final report (phase-discovery.md:178). | The three orchestrators reuse their last child's report, as /phase-discovery does, and add only the run-closing facts they own. |
| AUD-08-045 | checkpoint-repeat | major | workflows/pe-execute.md | ## Instructions | 13 | false | open | Each leaf compresses the same parent state three times in one Execution: /pae-finalize after execution (pae-finalize.md:62), /pav-close after validation (pav-close.md:51) and /pe-execute right after the leaf is reviewed (:72). The /pav-close pass follows the writes of /pav-check, /pav-propose and its own status update; the /pe-execute pass follows no write since that pass. A composite check (phase-composite-validation.md:85), each fix cycle (pv-execute-fixes.md:43) and the orchestrated loop (spec-run.md:403) add further passes. | One compression checkpoint per leaf cycle, owned by one workflow, with the others returning to it. |
| AUD-08-046 | checkpoint-repeat | minor | workflows/pav-propose.md | ## Instructions | 13 | false | open | Proposals are recorded in `## Improvement Proposals (T-XX)` (:60-75) and their Do Later and Optional summaries are mirrored into the leaf's `notes:` (:77). | One location holds the proposals, and the leaf block points to it. |
| AUD-08-047 | review-repeat | minor | workflows/phase-pipeline.md | ## Step 0 — Bootstrap | 15 | false | open | For a spec input, the pipeline runs `phase-discovery` Step 0 in full for resolution (:89-92), then runs /phase-discovery (:105), whose Step 0 parses the arguments, reads the spec, checks prefix collisions and locates task directories again (phase-discovery.md:58-93) on inputs nothing has changed in between. /spec-run does the same (spec-run.md:103-105, :134). | The resolution-only result is passed to /phase-discovery, which skips the checks whose inputs are unchanged. |
| AUD-08-048 | review-repeat | minor | workflows/pv-review.md | ## Instructions | 15 | false | open | /pv-review reads the same task-owned file set that /pv-contract read immediately before (pv-contract.md:34-39), including the tests, and resolves the same `working_dir:` values; /phase-validation (:87-88) and /bugfix (:132) run the two steps back to back. | The second step reuses the file set and reading of the first in the same session, or the two reviews are one pass with two verdict sections. |
| AUD-08-049 | review-repeat | minor | workflows/pv-execute-fixes.md | ## Instructions | 15 | false | open | After the fixes, three places order a recheck of contract and review: /pv-execute-fixes re-runs /pv-contract and /pv-review for the changed surface (:47), /phase-validation asks to recheck the affected contract and review findings before finalization (phase-validation.md:101-102), and /pv-finalize reruns both when the evidence does not cover the changed surface (pv-finalize.md:51-52). | One owner of the post-fix recheck; the others confirm its recorded evidence covers the changed surface. |
| AUD-08-050 | review-repeat | minor | workflows/spec-draft.md | ## Step 6 — Devil's Advocate review | 15 | false | open | Without sub-agents each critic round is a fresh pass that re-reads the spec and all Step 1 sources (:216-217), for up to ten rounds (:205). The Step 1 sources do not change between rounds, and the inline review is declared not independent anyway (:217-218). | Inline rounds re-read only the changed spec and keep the Step 1 sources from the first round. |
| AUD-08-051 | load-repeat | minor | workflows/pae-tests.md | ## Pre-check | 12 | false | open | /pae-tests and /pae-implement load the `phase-atomic-execution` rule and "run the full bootstrap even when standalone" (pae-tests.md:56-58, pae-implement.md:53-55); /pae-finalize loads it again (:29-31). Under /phase-atomic-execution, which loaded it at :22, and inside one /spec-run worker that runs all three steps in the context it holds (spec-run.md:342-344), the rule is loaded three or four times per leaf. The rule itself reuses current sources (rules/phase-atomic-execution.md:10-14), so the repeat is the rule text and its bootstrap reports (:26, :28). | The three steps load the rule only when no caller in the session has loaded it, as the rule's reuse clause states, and report the bootstrap once. |
| AUD-08-052 | load-repeat | major | workflows/pe-finalize.md | ## Context Bootstrap | 12 | false | open | /pe-finalize runs the `phase-execution` Context Bootstrap "including standalone runs", that is under /phase-execution as well, which ran it at phase-execution.md:53. /pv-create-fixes (:29) and /pv-finalize (:29) do the same under /phase-validation (:54). Unlike the atomic phase rules, the phase-execution and phase-validation rules have no reuse clause (rules/phase-execution.md:10-12, rules/phase-validation.md:10-12). The global rules answer both ways: the standalone sentence says to run the full bootstrap and never assume pre-loaded context, while the next sentence reuses unchanged context within one parent invocation (rules/workflow-globals.md:35-36). Read literally, the step text reloads the seven bootstrap sources under its parent. | The three steps bootstrap only when invoked standalone, as /pe-execute does (pe-execute.md:23-24), or the two phase rules gain the reuse clause of the atomic rules. |
| AUD-08-053 | load-repeat | minor | workflows/pe-execute.md | ## Context Bootstrap | 12 | false | open | Children load their phase rule unconditionally while limiting the full bootstrap to standalone runs (pe-execute.md:23-24, pav-check.md:24-25, pv-contract.md:22-23, pv-review.md:27-28, pv-execute-fixes.md:26-27), or run the bootstrap in both modes where the rule's reuse clause keeps the sources (pav-close.md:26, pav-propose.md:18, and phase-composite-validation.md:18 when /pav-close calls it). Their callers loaded the same rule (phase-execution.md:53, phase-atomic-validation.md:21, phase-validation.md:54, pav-close.md:26). The atomic-validation reuse clause keeps current sources for the same resolved project (rules/phase-atomic-validation.md:10-14), so a composite in another `working_dir:` loads its own sources legitimately; in every case the repeat is the rule text. | The load sentence of each child is conditional on the rule not being loaded in the session. |
| AUD-08-054 | load-repeat | major | workflows/compress-state.md | ## Guard | 12 | false | open | /compress-state loads `workflow-reference → ## Protected Sections Contract` on every run, with no reuse condition. Its callers have already loaded the rule in the same session: /pd-finalize loads exactly that section (:25) before calling it (:75); /pe-finalize (:27), /pv-finalize (:30) and /pav-close (:32) load the whole rule; /pe-execute loads its model-resolution section (:42). | The Guard loads the contract only when the caller has not loaded it in the session. |
| AUD-08-055 | load-repeat | major | workflows/bugfix.md | ## Step 5 — Verify and record | 12 | false | open | /bugfix loads the principles, architecture and state memory, ADR index and runbook in its Guard (:16-17) and later runs /pv-contract and /pv-review (:132). Neither runs under its parent orchestrator, so each performs the full `phase-validation` bootstrap (pv-contract.md:22-23, pv-review.md:27-28), whose rule has no reuse clause (rules/phase-validation.md:10-12); the standalone rule says never to assume pre-loaded context (rules/workflow-globals.md:35), while the next sentence reuses context within one parent invocation (:35-36). | A caller that has loaded the bootstrap sources counts as the parent for reuse, and the two validation steps reuse them. |
| AUD-08-056 | load-repeat | major | workflows/pe-execute.md | ## Instructions | 12 | false | open | Within one Execution session `workflow-reference` is loaded at several call depths for every leaf: /pe-execute for model resolution (:41-42), /phase-atomic-execution for the same section (:76-77), /pae-implement twice for the classifier (pae-implement.md:125-126), /pae-finalize for the status translation table (:35), /pav-close for the same table (:32) and /compress-state for the protected sections (:12). These repeats lie two or three call levels apart, so no repeated-load candidate covers them. | The rule, or the sections in use, is loaded once per session and reused by every deeper step while unchanged. |
| AUD-08-057 | load-repeat | minor | workflows/pav-check.md | ## Instructions | 12 | false | open | /pav-check loads the `tdd` rule for its audit (:55) after /pae-tests loaded `tdd → ## Test-level gate` (pae-tests.md:76) and /pae-implement enforced its GREEN section (pae-implement.md:107) for the same leaf. Under /pe-execute both subtrees run in one session (pe-execute.md:63-67), two call levels below it; /spec-run avoids the repeat with a separate Validator worker (spec-run.md:365-374). | The validation step reuses the rule loaded by the execution steps of the same session, or loads only the sections it audits. |
| AUD-08-058 | other | minor | workflows/PIPELINE.md | ## Child Workflows (Direct Step Access) | 11 | false | open | The reference says /pv-classify-fixes is "called by fix creation in orchestrated mode", but /pv-create-fixes calls it in every mode before allocating fix-task IDs (pv-create-fixes.md:50-54), as /phase-validation states (:12, :90). | The reference row states that fix creation always calls the classifier. |
| AUD-08-059 | report-repeat | minor | workflows/pae-tests.md | ## Pre-check | 11 | false | open | /pae-tests and /pae-implement each report the resolved WORK_DIR before continuing (pae-tests.md:54, pae-implement.md:51) and then load the `phase-atomic-execution` rule, whose bootstrap reports `WORK_DIR=<path>, AI_DIR=<path>` again (rules/phase-atomic-execution.md:26) and lists the loaded files (:28). AUD-08-051 records the repeated load; this finding records the repeated report. | The working directory is reported once per leaf, either by the step or by the rule bootstrap it loads. |
| AUD-08-060 | duplicate | minor | rules/workflow-reference.md | ## Parent `state.md` — `## Subtask Progress` Format | 11 | false | open | The anchored line `Status values for atomic-execution / atomic-validation:` stands under `## Canonical Status Formats` (rules/workflow-globals.md:215) and again in rules/workflow-reference.md:226; the `atomic-tests` vocabulary follows both (:217 and :227) with the same values. The validator and the state-tool test read the vocabulary only from rules/workflow-globals.md (scripts/validate-contracts.sh:641, :2020; tests/state-tool.py:768), so the copy is read by no check. | rules/workflow-reference.md cites `workflow-globals → ## Canonical Status Formats` instead of restating the anchored lines, after the naming migration, which keeps every parent line starting `Status values for` (spec 09 AC-42). |
| AUD-08-061 | duplicate | minor | workflows/pe-execute.md | ## Instructions | 11 | false | open | Three workflows restate `workflow-reference → ### Model columns and resolution` (rules/workflow-reference.md:97-188) in about twenty lines each: workflows/phase-atomic-execution.md:76-98, workflows/pe-execute.md:41-62 and workflows/spec-run.md:181-205 (guidance preflight, helper call, identity display, fallback or stop, actual identity only from a receipt). The wording differs in each copy; read against the contract, none contradicts it. The caller-specific parts are short: /phase-atomic-execution reuses a caller's resolution only for the same invocation (:97-98), and /spec-run stops its setup when guidance is unavailable and never implements inline (:186, :203), the conservative path the contract leaves to its caller (rules/workflow-reference.md:124-125). | Each workflow cites the contract and keeps only its caller-specific lines. |
| AUD-08-062 | reference-defect | minor | .ai/context/runbook.md | Recovery of a damaged progress block | 09 | true | open | Three active readers cite a section without its heading marker: `workflow-globals → Canonical Status Formats` (.ai/context/runbook.md:145, target rules/workflow-globals.md:156), `workflow-reference → Model columns and resolution` as link text (docs/MODEL-CATALOG.md:10, target the `###` heading at rules/workflow-reference.md:97) and `/pae-implement → Final Verification` (principles/testing-standards.md:63, target workflows/pae-implement.md:156). Each target exists; the references break the cross-reference syntax (.ai/principles/coding.md:46) like AUD-08-001, AUD-08-005 and AUD-08-033 inside instruction files. | Each span names its target heading with the marker (`## Canonical Status Formats`, `### Model columns and resolution`, `## Final Verification`); the naming migration fixes them under AMD-08-01. |
| AUD-08-063 | other | major | rules/phase-atomic-execution.md | ## Context Bootstrap | 09 | true | open | The text that moves into the atomic-execution bootstrap rule has 443 words by the migration's word count: the preamble (front matter and title, :1-7) 29, `## Context Bootstrap` (:8-43) 287 and `## Phase Behaviors` (:44-52) 127. The naming migration lets only `## Phase Behaviors` text overflow (spec 09 REQ-19), yet the preamble and `## Context Bootstrap` alone have 316 words; even with a one-word description, no title and only the citing line under `## Phase Behaviors` the rule would hold 302 words. The migration's own measurement at its parent snapshot (about 393 words, DM-10 → Overflow rules) predates the multi-repository runbook resolution at :21-25. | The migration specification states how a bootstrap whose own context section exceeds the limit is delivered, recorded and checked (AMD-08-03, AMD-08-04, AMD-08-06, AMD-08-07); nothing in the section is deleted. |
| AUD-08-064 | ambiguous-name | minor | workflows/phase-pipeline.md | ## Phase 2 — Execution | 09 | false | historical-fixed | The naming review of 2026-09-16 cited workflows/phase-pipeline.md:185 saying "Read and follow `phase-execution.md` inline", a suffixed name that fits the rule and the workflow equally (docs/analysis/2026-09-16-rules-workflows-naming-review.md:54-56). The current file has 161 lines and no such citation; the Execution phase calls `/phase-execution <task-directory>` (:120). The same suffix pattern remains for two other stems in the child lists (AUD-08-035). | Confirmed absent at the audited revision; no new work. |
| AUD-08-065 | other | major | .ai/specs/11-context-tiering.md | Scope item 9 | owner | false | open | Spec 11 takes in only the proposals that this audit assigns to owner 11 (Scope item 9, citing this audit's REQ-02), while this audit's data model also allows owner 11 for reference-defect, ambiguous-name, mixed-kind, naming, legacy-mention, duplicate, coverage-gap and other findings, and its A-20 gives owner 11 every duplicate consolidation that no map decision performs. Nine findings have owner 11 and a type spec 11 does not take in: AUD-08-010, AUD-08-018, AUD-08-025, AUD-08-026, AUD-08-037, AUD-08-038, AUD-08-058, AUD-08-060 and AUD-08-061. | The owner either extends spec 11's intake to every finding with owner 11 or assigns these findings to a specification that takes them in; this audit does not decide it. |
| AUD-08-066 | accepted-observation | minor | scripts/validate-contracts.sh | check expressions, failure messages, comments and check descriptions | none | false | open | 272 defect edges in scripts/validate-contracts.sh are `<stem>.md` file names matched by the token grammar: 259 in check expressions and failure messages (:607 reads workflows/pd-analyze.md and reports `pd-analyze.md missing …`), 12 of them ambiguous between a rule and a workflow only without the directory written beside them (:871), nine inside `check "…"` descriptions (:695) and four in comment lines (:673-674). Each names the file the check reads; the `.md` belongs to a file name, not to a rule or workflow name in an executable reference, which the migration's grammar defines for instruction files only (spec 09 REQ-22, DM-16). | No change; the edges stay recorded as correct on reading. |
| AUD-08-067 | accepted-observation | minor | scripts/validate-contracts.sh | check descriptions, path templates, fixtures and failure messages | none | false | open | Seven defect edges in scripts/validate-contracts.sh match no file the text means: `rules/phase-discovery` in a check description is the rule's name without suffix (:1236); `workflows/rule` is cut from the path template `workflows/rule-$base.md` built from a variable (:1306, twice); `workflows/fixture-known.md` is a synthetic workflow written into a temporary fixture home (:2593, :3378, :3516); and `rule-history` is part of a failure message about a version-history warning, not a skill (:4697). | No change; the edges stay recorded as correct on reading. |
| AUD-08-068 | accepted-observation | minor | scripts/sync.sh | rule copy loops and the always-on assembly | none | false | open | 58 defect edges in scripts/sync.sh (29) and scripts/setup-new-project.sh (29) are file names in shell code: the `for rule in workflow-globals.md … phase-atomic-validation.md` loops that copy rule files (sync.sh:208-210, :218-220; setup-new-project.sh:89-91, :124-126), where the five `phase-*.md` names are ambiguous only out of context because the loops read rules/; the always-on copy of `global-claude.md` (sync.sh:100); the language rule written into the legacy editor directory (setup-new-project.sh:104-118); and `$harness/capabilities.md`, a path built from the harness variable that the path grammar cuts after the variable name (sync.sh:61-62). | No change; the edges stay recorded as correct on reading. |
| AUD-08-069 | accepted-observation | minor | tests/hook-install.sh | legacy-directory and checkout path fixtures | none | false | open | 14 defect edges name a rule or workflow file in test and helper code: path components joined by the path operator (tests/hook-install.sh:790, tests/log-step-hook.sh:770, tests/state-tool.py:32, :5076), legacy-directory fixtures that the hook installer must leave untouched (tests/hook-install.sh:817-827), a file-name filter (tests/workflow-instructions.py:11), a test message (scripts/check-repo-set.py:658), a default argument path (scripts/check-spec-draft.sh:9), a folder listing (tests/log-step-hook.sh:53) and a relative Markdown link (scripts/README.md:53). Each names the file it means. | No change; the edges stay recorded as correct on reading. |
| AUD-08-070 | accepted-observation | minor | docs/USAGE.md | ## 9. File Roles Quick Reference | none | false | open | 61 defect edges in docs/USAGE.md name rule and workflow files: the file-role tables under `### rules/` (:748-757) and `### workflows/` (:772-813), where the subsection heading fixes the directory, so the ten `phase-*.md` names (:756, :774-778) are not ambiguous on reading; two prose mentions of always-on rule files (:18, :433); and a relative link (:653). The manual documents files; it holds no executable reference (spec 09 REQ-22). | No change; the edges stay recorded as correct on reading. |
| AUD-08-071 | accepted-observation | minor | .ai/memory/architecture.md | Layer 1 rule table | none | false | open | 17 defect edges in knowledge and reference documents name rule and workflow files in prose, tables or link targets: the rule table of .ai/memory/architecture.md (:34-43), .ai/context/integrations.md:16, .ai/context/runbook.md:81 and :105, .ai/principles/architecture.md:87, .ai/principles/coding.md:57 and :95, and the relative link targets `../rules/workflow-reference.md` in docs/MODEL-CATALOG.md:10 and :48. Each names the file it means; none is an executable reference. | No change; the edges stay recorded as correct on reading. |
| AUD-08-072 | accepted-observation | minor | .ai/principles/coding.md | ### Cross-references | none | false | open | Nine defect edges are placeholders or names of other things: the syntax examples `file → ## Section`, `file → ## Section → ### Subsection` and `rule-name` (.ai/principles/coding.md:31, :46, :51; .ai/principles/architecture.md:48), the HTTP endpoint `/metrics` (principles/infra-standards.md:195, templates/stacks/python-fastapi.md:381) and the placeholder command `/x` in a deployment table (docs/USAGE.md:689). | No change; the edges stay recorded as correct on reading. |

### Amendments to spec 09

| ID | Target | Change | Proposed | Reason | Evidence | Affected | Depends on | Requires ADR | Disposition |
|---|---|---|---|---|---|---|---|---|---|
| AMD-08-01 | DM-16 | semantic | A finding this grammar produces on the parent tree is a pre-existing defect: the delivery fixes it and lists it in DM-20 → Pre-existing reference defects. The same holds for every reference defect that 08's accepted report records with owner 09 outside this grammar, in scan set E or R: a section reference without its heading marker gains the marker of the existing heading; a reference to a paragraph label that is no heading names the heading whose extent holds the label; a reference broken across lines is joined into one span; a rule or workflow name with `.md` in a span loses the suffix or becomes a `/<name>` command. These fixes are edits permitted beside DM-1 substitutions; no `## ` heading is renamed or added for them, and each is listed in the same DM-20 table. | The audit gives pre-existing reference defects to the naming migration (spec 08 A-18), but this grammar finds and fixes only marked section references, commands, rule names and paths in scan set E. The recorded defects outside it are unmarked or paragraph-label section references (AUD-08-001, AUD-08-004, AUD-08-005, AUD-08-033, AUD-08-036, AUD-08-062), a reference broken across lines (AUD-08-007) and suffixed workflow file names in span lists (AUD-08-035); REQ-25 renames their stems as stale names but neither repairs nor checks them, so they survive the migration unchecked. | AUD-08-001, AUD-08-004, AUD-08-005, AUD-08-007, AUD-08-033, AUD-08-035, AUD-08-036, AUD-08-062, .ai/specs/09-model-only-harnesses-and-rule-naming.md:958, .ai/specs/08-rules-workflows-audit.md:1044 | AC-16, AC-39 | none | false | proposed |
| AMD-08-02 | new-AC | semantic | AC-NN (DM-16, REQ-31) — Given the 08 report accepted by the owner and the delivered tree, then every reference that a 09-owned reference-defect finding of that report names outside the DM-16 grammar is a row of DM-20 → Pre-existing reference defects whose Fix cell names the applied fix, and the delivered text at that place is one span that names an existing heading with its marker and carries no `.md` after a rule or workflow name. | AMD-08-01 adds an obligation that no acceptance criterion of the migration specification checks; without one the delivery can pass while the recorded defects remain. | AUD-08-001, AUD-08-004, AUD-08-005, AUD-08-007, AUD-08-033, AUD-08-035, AUD-08-036, AUD-08-062 | none | AMD-08-01, AMD-08-05 | false | proposed |
| AMD-08-03 | REQ-19 | semantic | EACH bootstrap rule SHALL contain, after its front matter and one optional H1, exactly the two `## ` sections `## Context Bootstrap` then `## Phase Behaviors` and at most 300 words (DM-19), unless DM-20 → Bootstrap size exceptions lists it; IF the moved text exceeds 300 words, THEN the excess `## Phase Behaviors` text SHALL move to the overflow rule DM-10 names for that phase, cited from `## Phase Behaviors`, and SHALL never be deleted; IF the front matter, the moved `## Context Bootstrap` section and the citing line alone exceed 300 words, THEN THE bootstrap rule SHALL keep that section whole, SHALL move all other `## Phase Behaviors` text to the overflow rule, and SHALL be listed in DM-20 → Bootstrap size exceptions with its word count and that reason. | At the audited revision the atomic-execution bootstrap cannot meet the limit by overflow alone (AUD-08-063): its preamble and `## Context Bootstrap` already have 316 words, and DM-12 moves that section verbatim, so the current REQ-19 can be met only by deleting or rewording load instructions, which it forbids. This amendment states the exception; AMD-08-04 (checker), AMD-08-06 (the DM-20 table it refers to) and AMD-08-07 (AC-11) carry it into the other normative places, and the set is consistent only when all four are accepted. Three further statements of the limit are not amendment targets and are left for the reconciliation of the specification: the Non-Functional Requirements row `Bootstrap rule` (spec 09:1196), the Edge Cases row `Bootstrap over 300 words after the move` (:1244) and the Risks row `Bootstrap rules exceed 300 words after the move` (:1563). DM-10's measurement of about 393 words (:850) is out of date (443 words at the audited revision) but states no rule. Alternatives left to the owner: shorten the section under spec 11's obligation map before this migration, or move the path resolution that the atomic-validation bootstrap repeats (duplicate group DG-004) into a procedure rule; both change text that DM-12 moves verbatim. | AUD-08-063, rules/phase-atomic-execution.md:8, .ai/specs/09-model-only-harnesses-and-rule-naming.md:319, .ai/specs/09-model-only-harnesses-and-rule-naming.md:848, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1196, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1244, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1563 | AC-11 | AMD-08-06 | false | proposed |
| AMD-08-04 | REQ-32 | semantic | THE checker SHALL reject a bootstrap rule over 300 words or with any `## ` section other than the two of REQ-19, counting words by DM-19 (same rule as specs 11 and 19), except that a bootstrap rule listed in DM-20 → Bootstrap size exceptions is not rejected for its word count while its count equals the listed `Words` value. | AMD-08-03 requires a bootstrap rule over 300 words when its own context section already exceeds the limit (AUD-08-063); without the matching exception here the checker rejects that rule. Tying the exception to the listed count keeps any later growth visible. | AUD-08-063, .ai/specs/09-model-only-harnesses-and-rule-naming.md:374 | AC-11 | AMD-08-03, AMD-08-06 | false | proposed |
| AMD-08-05 | DM-20 | semantic | - `## Pre-existing reference defects` — `\| Path:line \| Reference \| Fix \|`: dangling references and missing headings the checker finds on the parent tree, and the reference defects 08's accepted report records with owner 09 outside the DM-16 grammar, fixed by this delivery. | AMD-08-01 lists defects in this table that the checker does not find; without this change the table's description excludes them. | AUD-08-001, AUD-08-004, AUD-08-005, AUD-08-007, AUD-08-033, AUD-08-035, AUD-08-036, AUD-08-062, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1028 | AC-39 | AMD-08-01 | false | proposed |
| AMD-08-06 | DM-20 | semantic | - `## Retained old names` — `\| Path \| Line text \| Reason \|` (DM-17). - `## Bootstrap size exceptions` — `\| Rule \| Words \| Reason \|`: one row per bootstrap rule that REQ-19 lets exceed 300 words, with its word count by DM-19 at the delivery commit and the reason that its front matter, `## Context Bootstrap` section and citing line alone exceed the limit; no other rule is listed. | AMD-08-03, AMD-08-04 and AMD-08-07 refer to a listed size exception and its word count; the record has no table for them (AUD-08-063). | AUD-08-063, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1027 | AC-11, AC-39 | none | false | proposed |
| AMD-08-07 | AC-11 | semantic | **AC-11** (REQ-19, REQ-32) — Given the delivered bootstrap rules, then each has only the two sections and either ≤ 300 words or exactly the word count of its row in DM-20 → Bootstrap size exceptions, and for every listed rule the front matter, `## Context Bootstrap` section and citing line alone exceed 300 words; and fixtures with 301 words, or with a third `## ` section, each yield one finding, while a 316-word fixture listed with 316 words yields none and the same fixture listed with 315 words yields one. | Under AMD-08-03 the atomic-execution bootstrap must exceed 300 words (AUD-08-063), so the current criterion cannot pass on the delivered tree; this restates it for the exception and keeps the 301-word and third-section fixtures. | AUD-08-063, .ai/specs/09-model-only-harnesses-and-rule-naming.md:1311 | AC-11 | AMD-08-03, AMD-08-04, AMD-08-06 | false | proposed |

### Read coverage

| Path | Status | SHA-256 | Reader |
|---|---|---|---|
| harness/claude/capabilities.md | read | 6ba22a6a9030fc23d7effae5c7da5895fc158c6d79bf914539819cd52dcdca0f | Implementer |
| harness/claude/hooks.json | read | d1adf8bf70d513e328fd42719d2aa3b593019b9a7f82701052129bd434432c0a | Implementer |
| harness/claude/permissions.json | read | 57a5c2f1e405d9271bf17dd1dda600b0cf33915cfa69f0fba323e10b269b8361 | Implementer |
| harness/codex/capabilities.md | read | 3c646d8e248e84f846900f785338a58104809201789b47da7279ee2971f16613 | Implementer |
| rules/git-flow.md | read | bee39142bf860cd3f114878433794ad1a7943ab9cba46ab32de73ba3e243ff9f | Implementer |
| rules/global-claude.md | read | 2b7aa608b14136b0d09041a7815bf615d1ee80d8983ab6c6e98d979be3bb3ee2 | Implementer |
| rules/language.md | read | d705b525c040aea368e0361500303f9ab2ca4e2acf117d794dbdfe965b9bf7ca | Implementer |
| rules/orchestration.md | read | dab28e6dcb0109636acd612970c8df1f6fb4e8e48feee3b70510f59bbcfcb3a8 | Implementer |
| rules/phase-atomic-execution.md | read | 0337126eab8b8ca2559559c01af4d85faa7751882e69f4f0522cbf7650e88134 | Implementer |
| rules/phase-atomic-validation.md | read | ed2ebe9186b4d8e24a4a09b920c3d2b1d79eadeb8e11aabc7ef2dfd43925ee76 | Implementer |
| rules/phase-discovery.md | read | 5ab2653bc316e8417cb0f9775104b0c3548b6c6192463c5122a04d54fd2fe5c3 | Implementer |
| rules/phase-execution.md | read | 91a05f24b2387239d4cb0b5891d9f0ceb9d51bcd9bee3f7517131414d33e41e1 | Implementer |
| rules/phase-validation.md | read | 662027dd264d4062ea2980a6b92296a7dd8863228f410b568f304f09f2d340bc | Implementer |
| rules/quick-flow.md | read | 8f6accf9d9fe0fec8fcb4d42a74abd4f35f2ac98568836fa70913fdb995152f4 | Implementer |
| rules/run-log.md | read | cd147aaaf6d802f17d623fc92d470335058a372c57c06c2a7178250dbdefb89c | Implementer |
| rules/tdd.md | read | f5592a9d2d52e98650ca852da98c21732dcc06621a20a82c0dba65f386664225 | Implementer |
| rules/workflow-globals.md | read | 14a1bc2dd813c41b0659cd7d6a546665efce38744d053e569878475344d0fd97 | Implementer |
| rules/workflow-reference.md | read | 08c81786494f39665b4aebf495c705a21b4fd38294a995074a24d165730bd463 | Implementer |
| templates/codex-global-AGENTS.md | read | 0d6649fdc87a0f0ae70b990ba957e5fe85b80148afab197ddb699e02aea39b95 | Implementer |
| workflows/PIPELINE.md | read | 639c2f3b0adc77ec0effcc9a7d84c9ec6ddc813064b4c25f84acb97a6afdf033 | Implementer |
| workflows/adr-new.md | read | ddd8cb4d710d19f65de47ac2d24889fe062d0824d1b1d068f67a524fbaf9d780 | Implementer |
| workflows/bugfix.md | read | aac676509ed85d2a239d94bbbf1e57d3869a27e6eb5dce46c94976b23acfdecf | Implementer |
| workflows/compress-state.md | read | 3b3ba3e8a057df347b35b79ce0b90bad5b64993c7667364c697ac308d311edf5 | Implementer |
| workflows/context-pack.md | read | d757046d92c6d73b27e6bff9b4b9418049682944b4863bb87442e8df79e2fc3c | Implementer |
| workflows/onboard-legacy-project.md | read | 235db2e6ada843817185cc87d2af8a7728ddd25934dd1e619e4cd19a7f4797bf | Implementer |
| workflows/pae-finalize.md | read | 881ff99f99a0650a966b8bc40e364ba5e072b0b78960998ed161c509d870331d | Implementer |
| workflows/pae-implement.md | read | ddbd9ff8e9385172f2132801850e45e97ea4ea41f4bcd27a975b6170a2056865 | Implementer |
| workflows/pae-tests.md | read | 2c5ab47354ecc64b5ac08223fd1f5439d4edb655f08530799a2670fd741a5438 | Implementer |
| workflows/pav-check.md | read | bb006d445c9d6ee291ab3ed16ec698f641c382423d13f0a9c919c3d5638abcef | Implementer |
| workflows/pav-close.md | read | 07b161a998bafcba38cab4754009b1c7f561b78f353273bbb1df081bb1919664 | Implementer |
| workflows/pav-propose.md | read | e3c3ceb7b23138d248def0f04d698e8d48c6fc899887a28f939c5ae1bbdebf8b | Implementer |
| workflows/pd-analyze.md | read | 985770ab0c0b108aff897255c94f48bfa559e8936a2103cf4f7c727b15378384 | Implementer |
| workflows/pd-archive.md | read | fac195f3e99498d5cd3d61914057e52e4628fd55c3d096c6f6640c625988f4f7 | Implementer |
| workflows/pd-decompose.md | read | 06b7515589c31ca6cc4d6a6b88daeea0a28c0bb3ad4be87c2d8d79c608b6ebc7 | Implementer |
| workflows/pd-design.md | read | 8fb082587153671fd950ed787245742533059e74e46f6ba178d170b53ffdbf71 | Implementer |
| workflows/pd-finalize.md | read | 2113a86d7473b977eab045f49f89028961d3ced63b61a4651e24313a72130a58 | Implementer |
| workflows/pd-select-model.md | read | 16a7239c47c97e0fc2c52a54a67017d45be9b12809bb010267555c3a3b6977d2 | Implementer |
| workflows/pe-execute.md | read | 5d4097666f7bd3bc1d343c10dd545db306b845cc74cba2ce21e43acf8d28316e | Implementer |
| workflows/pe-finalize.md | read | 6eba443770005d9d7734cb40e21d09a43caf03ba05bcee4c0d15cd7164efb384 | Implementer |
| workflows/phase-atomic-execution.md | read | 2891c7773cb73a2d25d3ef23e8ec6c3c003f98342cbea69e1288796178ad48f8 | Implementer |
| workflows/phase-atomic-validation.md | read | 5f0c24b23a6126c5e74289aba236ac5432833dcf8d6874ed42124b149f5204d1 | Implementer |
| workflows/phase-composite-validation.md | read | 68cbf2e081ae2574492cfff679a3ebd45b5da2c2c244fcfe9f9aabb45503c2ef | Implementer |
| workflows/phase-discovery.md | read | 4c3a29c76fbd65ddc5a03355a16c369d28d7605abf707ff4951c53f7c7bf6102 | Implementer |
| workflows/phase-execution.md | read | 00642cf36ffb64a08d8e2c2318871fcbd22263b972a7b973e0f0612a7ee6f4c6 | Implementer |
| workflows/phase-pipeline.md | read | 6510fdf8efc7eb9a3fda2193a21af31151372f3aff5f8f23170c72049f074345 | Implementer |
| workflows/phase-validation.md | read | e9da13b70da6ac4f79cf4f7fc3ac1bc7c4a79e01333281e044fb2b9079cf56c5 | Implementer |
| workflows/pv-classify-fixes.md | read | e5ee841a82cfe226bba2699ee2405dc26e61436bc4e5cce8b76bdbc9e1752abe | Implementer |
| workflows/pv-contract.md | read | 0eb78bb230e90cdc9cabf82ef1f65c8853193ed49d5b5f1e8029960ee92edbaa | Implementer |
| workflows/pv-create-fixes.md | read | 7f01772633ca8500701679cdd95720eb40eee4d7e5479627bf9cf25c2227fdc0 | Implementer |
| workflows/pv-execute-fixes.md | read | 9d3e37bf7b399557f6e3653b60495f73c6a30d368157ccaf979f311c3f323e28 | Implementer |
| workflows/pv-finalize.md | read | c4bf378d55d5b3bf2dee3e5abcb386365a6dc756f8b0698ae9c9e914b73a9be7 | Implementer |
| workflows/pv-issues.md | read | 721839727f296885f08c259dc68b58b2119867816210c8f89be6a0db48464009 | Implementer |
| workflows/pv-review.md | read | 9275c0054e2ea95cfa9cdc8ee159e38a41ee842a35f1ff3f6bd91df98e0bf777 | Implementer |
| workflows/restack.md | read | 5a3438f91e66054aa066ac044d8fb56786da14ed7524eaa05ba8c5179d68ce1b | Implementer |
| workflows/retro.md | read | 41d0df3ebc56b27c16f15b1bcffe39ecd8e62b9f51c17be52dcb893d788186b5 | Implementer |
| workflows/spec-draft.md | read | 6a9adbd77065104d229050626695734a95d7784171b18a399a9f06c7be1f1a00 | Implementer |
| workflows/spec-run.md | read | a7a5af2cbadf807d2c316dfe1887bdf9eacb50d9f83c242bd7e0fea939b3106c | Implementer |
| workflows/spec-sync.md | read | 8fe077ca25348fb526ccda1a7c5f6d093dba5dc37e17d819186b357056c51a30 | Implementer |
| workflows/suggest-commit-message.md | read | 38ae16684746bd03cd4a559cce33d5aa2b3fcbc952adb2a12e96e3af9c5f96a4 | Implementer |
| workflows/suggest-commit-pr.md | read | 80fd230cc383e8ee0ff6dae7f382eb53e0d4938a784bccb6afb155bc638c7627 | Implementer |
| workflows/suggest-pr-description.md | read | f3a6a34878df4aed2a1876bc6bf07aa78ea75f6515296da4a03b4f81719f017b | Implementer |

### Installed comparison

Not verified.

<!-- audit:generated:end -->

## Blockers for spec 09

Each finding below is cited by an amendment, so spec 09 settles it only after the owner
accepts or rejects that amendment:

- AUD-08-001 — unmarked section references in `rules/git-flow.md` (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-004 — references in `rules/quick-flow.md` to paragraph labels that are no headings,
  one of them split across lines (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-005 — unmarked section references in `rules/tdd.md` (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-007 — a reference in `rules/workflow-globals.md` split across a line break
  (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-033 — unmarked section references in `workflows/pv-contract.md` and
  `workflows/pae-implement.md` (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-035 — `.md`-suffixed workflow file names in the child lists of
  `workflows/phase-pipeline.md` (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-036 — citations of the mode-override registry, which has no heading
  (`workflows/pav-propose.md` and two knowledge files) (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-062 — unmarked section references in three reader files (AMD-08-01, AMD-08-02, AMD-08-05).
- AUD-08-063 — the atomic-execution bootstrap cannot meet the 300-word limit by overflow
  (AMD-08-03, AMD-08-04, AMD-08-06, AMD-08-07).

## Independent review

Reviewed: pending

## Acceptance

Accepted: pending
