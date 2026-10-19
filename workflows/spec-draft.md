---
description: Standalone SDD authoring — turn a raw task (link, text, or file) into a development-ready specification; interactive by default, fully autonomous with --auto-mode
---

Invocation: `/spec-draft <task-input> [--auto-mode | --brain-storm] [--output <path>]`

Examples:
- `/spec-draft "Add OAuth login for B2B tenants"` — interactive authoring (default)
- `/spec-draft https://jira.example.com/browse/PROJ-412 --auto-mode` — autonomous, from a ticket link
- `/spec-draft ./notes/oauth-brief.md --auto-mode --output .ai/specs/07-oauth.md`

**Isolation.** This workflow is standalone. It is not a step of `/phase-discovery`,
`/phase-pipeline`, or `/spec-run`, it is never invoked by them, and it never invokes them.
It creates **no** task directory, **no** `state.md`, **no** `plan.md`, and **no** T-XX
subtasks. Its single output is one specification file. When it finishes it prints the
follow-up command as plain text and stops — it never auto-advances into a pipeline.

**Output contract.** The produced file is a superset of `templates/spec.md`: it keeps
`## Goal`, `## Acceptance Criteria`, `## Out of Scope`, and `## Notes` with their existing
meaning, so the file remains a valid `spec_path:` input for `/phase-discovery` and
`/spec-run` should the user later choose to run them. The extra sections are additive.

---

## Flags

| Flag | Meaning |
|---|---|
| *(none)* | `--brain-storm` — the default. Interactive authoring: the AI asks, proposes options, and the human decides. |
| `--brain-storm` | Explicit form of the default. |
| `--auto-mode` | Fully autonomous. No questions except a true blocker (see `## Blocker escalation`). Every ambiguity is resolved by the resolution ladder and recorded. |
| `--output <path>` | Write the spec here instead of the derived default path. |

`--auto-mode` and `--brain-storm` are mutually exclusive. If both are passed → **stop**:
"`--auto-mode` and `--brain-storm` are mutually exclusive. Pass one or neither."

**Mode declaration.** `--auto-mode` is a declared autonomous mode for the duration of this
workflow: it overrides `workflow-globals → Wait for user decisions`. It does **not** override
the Guard below, and it does **not** license silent decisions — every autonomous resolution
is written into `## Assumptions` with its source.

---

## Step 0 — Resolve the input

1. Classify `<task-input>`:
   - **URL** (starts with `http://` or `https://`) → fetch it and extract the task
     description: title, body, acceptance criteria, comments that change scope, linked
     specs. If the fetch fails or requires authentication → **stop** and ask the user to
     paste the description instead. Never guess the contents of a URL you could not read.
   - **Existing file path** → read the file in full.
   - **Anything else** → treat the literal text as the human-written task statement.
2. If the resolved statement is empty or under one sentence of actual content → **stop**:
   "Task input is too thin to specify. Provide a description, a file, or a ticket link."
3. Record the raw statement verbatim. It goes into `## Source` in the output document.
   Never paraphrase it away — the spec must remain auditable against what was asked.

---

## Guard

Derive the output path (unless `--output` was passed):

- Directory: `.ai/specs/` if it exists, else the repository root.
- Filename: `NN-<slug>.md`, where `NN` is the next free two-digit number in that directory
  (`01` if empty) and `<slug>` is a kebab-case slug derived from the task title, at most
  five words.

If the target file already exists → **stop**: "`<path>` already exists. Overwriting will
discard the current specification. Confirm to proceed? (yes/no)". Wait for explicit
confirmation. This Guard holds in `--auto-mode` too.

---

## Step 1 — Context bootstrap

Read, in this order, skipping what is missing without error. In a multi-repo project check
`../.ai/` first and load umbrella before local — local overrides umbrella.

1. `.ai/principles/architecture.md`, `.ai/principles/coding.md`, `.ai/principles/domain.md`
   — binding constraints and the ubiquitous language the spec must be written in.
2. `.ai/memory/architecture.md` — components, boundaries, existing constraints.
3. `.ai/memory/state.md` — in-flight work that could collide with this task.
4. `.ai/adr/index.md` — past decisions. Read a full ADR only when the index line touches
   this task's subject.
5. `.ai/context/integrations.md` — **only if** the statement mentions external services,
   third-party APIs, or cross-service contracts.
6. `.ai/context/environment.md` — **only if** the statement mentions environments, secrets,
   or infrastructure topology.
7. `.ai/specs/` — skim existing spec titles for overlap with this task.

Report one line: "Context loaded: [files read] | not found: [files skipped]".

If **no** `.ai/` directory exists at all, say so explicitly and continue — the spec is then
written from the codebase and the task statement alone, and that limitation is recorded in
`## Assumptions`.

---

## Step 2 — Codebase reconnaissance

Establish what already exists before specifying what should exist. Bounded: this is a
reconnaissance pass, not a review.

1. Locate the modules, entrypoints, models, and tests the task would touch.
2. Identify how comparable problems are already solved in this repository — the existing
   pattern outranks a theoretically better alternative.
3. Note anything the task would break: shipped behaviour, public contracts, DB schema,
   cached shapes, invariants.

**Evidence rule.** Every statement the output document makes about existing code MUST cite
`path/to/file.py:123`. A claim about the codebase without a citation is a hallucination —
delete it or verify it. If you could not verify something, it belongs in `## Open Questions`,
not in the body of the spec.

---

## Step 3 — Ambiguity scan

Scan the task statement against these nine categories and mark each **Clear** / **Partial** /
**Missing**. This scan drives both modes: it is the question queue in `--brain-storm` and the
resolution queue in `--auto-mode`.

| # | Category | What to look for |
|---|---|---|
| 1 | Functional scope & behaviour | User goals, success criteria, explicit scope boundaries, affected roles |
| 2 | Domain & data model | Entities, attributes, relationships, identity, lifecycle states, migrations |
| 3 | Interaction & flow | Journeys, API call sequences, error and loading states, idempotency |
| 4 | Non-functional attributes | Latency, throughput, scale, availability, observability, security, compliance |
| 5 | Integration & dependencies | External APIs, payload formats, versioning, failure semantics of dependencies |
| 6 | Edge cases & failure handling | Empty, boundary, malformed, concurrent, partial-failure, retry, rate-limit |
| 7 | Constraints & trade-offs | Technical constraints, explicitly rejected alternatives, budget/deadline limits |
| 8 | Terminology | Canonical terms from `domain.md`; synonyms that must be collapsed |
| 9 | Completion signals | Testable acceptance criteria, Definition of Done, rollout/rollback |

Rank every gap by **impact**: a gap that would change the shape of the implementation ranks
above a gap that would change a default value.

Print the scan as a table before proceeding. This table is working material, not part of the
output document.

---

## Step 4A — Resolution, `--auto-mode`

Do **not** ask. Resolve every gap by the ladder below, stopping at the first level that
answers it:

1. `.ai/principles/*` — an explicit rule settles the question outright.
2. `.ai/adr/` — a past decision on the same subject is binding unless the task statement
   explicitly supersedes it.
3. `.ai/memory/architecture.md` + `.ai/memory/state.md` — current system shape and
   in-flight constraints.
4. Existing codebase patterns — how comparable cases are already solved here.
5. General best practice — only when levels 1–4 are silent. Prefer the smallest, most
   reversible option.

Every resolution produces exactly one line in `## Assumptions`:

```
- A-01 | <the ambiguity, one clause> | Resolved: <the decision> | Source: principles/coding.md → "Naming" | Reversible: yes
```

`Source:` is mandatory and names the level that settled it (`best practice` is a valid
source and must be labelled as such — it is the weakest and the most likely to be wrong).
No silent resolutions. A gap resolved without a recorded line is a defect in this workflow's
output.

A gap that level 5 cannot honestly resolve does **not** get an invented answer. It goes into
`## Open Questions` with a severity of `blocker` or `non-blocker`.

---

## Step 4B — Resolution, `--brain-storm` (default)

Interactive authoring. The human decides; the AI does the thinking, proposes, and records.

**Question protocol.**

1. Ask in rounds, ordered by impact — highest-impact gap first. At most **4 questions per
   round** and at most **3 rounds** (12 questions total). If gaps remain after round 3,
   record the rest in `## Open Questions` rather than continuing to interrogate.
2. Use the `AskUserQuestion` tool where available; otherwise print the same content as a
   Markdown table and wait.
3. Every question must be:
   - a full interrogative sentence ending in `?` — never a bare topic label or a
     requirement id;
   - accompanied by one line of **Why it matters** — what changes downstream depending on
     the answer;
   - answerable by picking one of **2–4 mutually exclusive options**, each with its
     trade-off stated in one line. Free-form answers are always allowed.
4. Order the options with your **recommendation first**, marked `(Recommended)`, and state
   in one clause why you recommend it. A recommendation is not a decision: wait for the
   human.
5. **The human's answer wins.** If it contradicts your recommendation, adopt it without
   argument.

**Conflict rule.** If the human's answer contradicts a binding source — a rule in
`.ai/principles/*`, an accepted ADR, or a shipped invariant — do not silently comply and do
not silently refuse. State the conflict in two sentences (what the answer is, what it
contradicts, and the concrete consequence), then ask for one of: *override*, *revise the
answer*, or *supersede the ADR*. Record the outcome:

```
- D-01 | <decision> | Overrides: adr/0007-token-storage.md | Rationale: <human's stated reason> | Follow-up: supersede ADR-0007
```

in `## Decisions`, and, when an ADR is overridden, add a follow-up line to `## Notes`. The
ADR itself is **not** written by this workflow.

**Recording.** After each round, append every exchange to `## Clarifications` in the output
document as `- Q: <question> → A: <answer>` under a `### Session YYYY-MM-DD` heading, and
immediately fold the answer into the affected section — requirement, data model, edge case,
or acceptance criterion. Never leave an answer sitting only in the clarification log: the
log is the audit trail, the body is the spec.

**Proposal duty.** Brain-storm mode is not only interrogation. Where the task admits more
than one shape — data model, integration boundary, sync vs async, new module vs extension of
an existing one — present **2–3 concrete variants** with trade-offs and a recommendation,
and let the human choose. Record the choice in `## Decisions` and the rejected variants in
one line each under `## Notes → Rejected alternatives`. Rejected alternatives are kept
because the next reader will otherwise re-propose them.

---

## Blocker escalation

Applies in **both** modes, `--auto-mode` included. Stop and ask the human when, and only
when, proceeding under any assumption would make the specification useless or unsafe:

- the task's core goal is genuinely unreadable from the input;
- two binding sources (a principle and an ADR, or two ADRs) contradict each other on a
  point this task depends on;
- the task requires deleting or changing shipped behaviour, and it is not stated whether
  that is intended;
- the task touches credentials, personal data, payments, or an irreversible migration, and
  the required handling is unspecified.

Anything short of that is not a blocker — resolve it and record it.

---

## Step 5 — Write the specification

Write the document at the Guard's path, using exactly this structure. Sections that
genuinely do not apply are kept with the single line `N/A — <one-clause reason>`. Never
delete a section, and never leave one blank: a blank section is indistinguishable from an
overlooked one.

```markdown
# <Task Title>

<!-- SDD spec. Authored by /spec-draft in <mode> mode on <YYYY-MM-DD>. -->

## Source

<Verbatim task statement, or the URL plus the extracted description. Unedited.>

## Context & Problem

<What is true today and why it is a problem. Cite existing code as path:line.
Business consequence of doing nothing. One or two paragraphs.>

## Goal

<What problem this solves and why. One paragraph, domain language, no implementation.>

## Scope

<What this spec covers, as a short bulleted list of capabilities.>

## Out of Scope

<Explicit exclusions — name actual features, files, or behaviours, not abstractions.
This section bounds the implementing agent's exploration; an empty one is a defect.>

## Actors & Roles

| Actor | Description | What they can do in this feature |
|---|---|---|

## Terminology

| Term | Definition | Source |
|---|---|---|

<Canonical terms only, taken from principles/domain.md where it defines them. List any
synonym that must NOT be used alongside the canonical term.>

## Requirements

Functional requirements in EARS notation. One requirement per line, one behaviour per
requirement, each with a stable `REQ-NN` id.

| Pattern | Shape |
|---|---|
| Ubiquitous | THE SYSTEM SHALL `<response>` |
| Event-driven | WHEN `<trigger>`, THE SYSTEM SHALL `<response>` |
| State-driven | WHILE `<state>`, THE SYSTEM SHALL `<response>` |
| Unwanted behaviour | IF `<condition>`, THEN THE SYSTEM SHALL `<response>` |
| Optional feature | WHERE `<feature is included>`, THE SYSTEM SHALL `<response>` |
| Complex | WHILE `<state>`, WHEN `<trigger>`, THE SYSTEM SHALL `<response>` |

- **REQ-01** | WHEN <trigger>, THE SYSTEM SHALL <observable response>.
- **REQ-02** | IF <error condition>, THEN THE SYSTEM SHALL <recovery response>.

## Data Model

<Entities, fields with types, relationships, identity, lifecycle states, and whether a
migration is required. Mark each entity `new` or `existing (path:line)`. N/A only when the
task provably touches no persisted or transferred state.>

## Contracts & Interfaces

<Public surfaces this task adds or changes: HTTP endpoints with method/path/request/
response/status codes, events with payload shape, CLI arguments, module-level function
signatures other components will call. Include failure responses, not only the happy path.>

## Non-Functional Requirements

| Attribute | Target | How it is verified |
|---|---|---|

<Numeric targets only — "fast", "scalable", "secure" are not targets. Where an
organization-wide standard already covers an attribute, reference it instead of restating
it. Attributes that genuinely do not apply are listed as N/A with a reason.>

## Edge Cases & Failure Modes

| # | Case | Expected behaviour | Requirement |
|---|---|---|---|

<At minimum consider: empty input, boundary values, malformed input, unauthorized actor,
duplicate/replayed request, concurrent modification, dependency unavailable, partial
failure mid-operation, timeout and retry.>

## Acceptance Criteria

Binary and measurable. Each criterion carries an `AC-NN` id and names the requirements it
proves.

- [ ] **AC-01** (REQ-01) — Given <precondition>, when <action>, then <observable outcome>.
- [ ] **AC-02** (REQ-02) — Given <precondition>, when <action>, then <observable outcome>.

## Traceability

| REQ | Acceptance Criteria | Notes |
|---|---|---|

<Every REQ appears exactly once. Every AC appears against at least one REQ. An orphan on
either side is a defect, not a table entry.>

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|

## Assumptions

<One line per resolved ambiguity, in the Step 4A format, including assumptions resolved
from a human's answer in brain-storm mode.>

## Decisions

<Brain-storm mode: one line per human decision, in the Step 4B format. Auto mode: N/A.>

## Clarifications

### Session YYYY-MM-DD

<Brain-storm mode: `- Q: … → A: …` per exchange. Auto mode: N/A — no questions asked.>

## Open Questions

| # | Question | Severity | Impact if answered differently |
|---|---|---|---|

<`blocker` or `non-blocker`. An empty table is written as `None.`>

## Notes

<Constraints, links to related specs and ADRs, rejected alternatives with a one-line
reason each, and any follow-up the implementation must not forget.>

## Readiness Checklist

<The gate result from Step 7, copied verbatim.>
```

**Writing rules.**

- Write in domain language. Requirements state *what*, not *how*. Implementation hints, if
  genuinely load-bearing, go in `## Notes` and are labelled as hints, not requirements.
- One behaviour per requirement. A requirement containing "and" that joins two observable
  behaviours is two requirements.
- No unbounded adjectives anywhere: *fast*, *robust*, *user-friendly*, *scalable*,
  *properly*, *as needed*. Replace each with a number or a named condition.
- Ids are stable. Never renumber `REQ-NN` or `AC-NN` on a later edit — append instead, and
  mark a withdrawn requirement `(withdrawn)` rather than deleting it.
- Every unresolved point is a `## Open Questions` row, never a `TODO` buried in prose.
- Match the size to the risk: a low-criticality change does not need a nine-section essay,
  but it does need every section to be *decided* — `N/A — <reason>` is a decision.

---

## Step 6 — Adversarial self-review

Before the gate, review the draft as a hostile reader whose job is to find the hole. Run at
least two passes and fix what you find:

1. **Implementability** — for each REQ: could a developer with no access to this
   conversation implement it without asking a question? If no, the requirement is
   underspecified.
2. **Testability** — for each AC: can it be turned into a failing test *today*, before any
   implementation exists? If it cannot be observed, it is not a criterion.
3. **Contradiction** — do any two requirements conflict? Does any requirement contradict a
   principle, an ADR, or a shipped invariant?
4. **Coverage** — does every capability listed in `## Scope` have at least one requirement?
   Does every requirement trace to something in `## Scope`? A requirement outside scope is
   either scope creep or a missing scope line.
5. **Hallucination** — does every claim about existing code carry a `path:line` citation
   that you actually read?

Report the pass as a short list: what was found, what was changed. If two consecutive
passes find only cosmetic nits, the draft has converged — that is the signal to stop
refining.

---

## Step 7 — Readiness gate

The spec is **development-ready** only if every check passes. Print the checklist with
`PASS` / `FAIL` per line and copy it into the document's `## Readiness Checklist`.

| # | Check | Fails when |
|---|---|---|
| 1 | Goal is one paragraph in domain language | It describes a solution instead of a problem |
| 2 | `## Out of Scope` names concrete exclusions | Empty, or only abstractions |
| 3 | Every requirement has a `REQ-NN` id and matches one EARS pattern | A free-form sentence sits among them |
| 4 | Every REQ has ≥1 AC; every AC names ≥1 REQ | An orphan exists on either side |
| 5 | Every AC is binary and observable | It contains an unbounded adjective, or cannot be tested before implementation |
| 6 | Non-functional targets are numeric or explicitly N/A with a reason | "Should be fast" |
| 7 | Data model and contracts are present or explicitly N/A with a reason | Section left blank |
| 8 | Edge cases cover at least error, empty, boundary, and concurrency | The table only lists happy-path variants |
| 9 | Every ambiguity from the Step 3 scan is either resolved in `## Assumptions` or listed in `## Open Questions` | A gap disappeared without a trace |
| 10 | No `blocker`-severity open question remains | One remains |
| 11 | Every codebase claim carries a `path:line` citation | An uncited claim exists |
| 12 | Terminology matches `principles/domain.md` where it defines a term | A synonym is used for a canonical term |
| 13 | The spec is feature-sized — plausibly 1–8 implementation subtasks | It spans several features; recommend splitting |

**Verdict.**

- All pass → `READY FOR DEVELOPMENT`.
- Only non-blocker failures → `READY WITH RESERVATIONS`, listing each failure and what it
  costs downstream.
- Any of checks 4, 5, 9, 10, or 11 fails → `NOT READY`. Name the exact failures and the
  shortest path to fixing them. Do not soften the verdict: a spec that reads as finished but
  is not is worse than an obviously unfinished one.

Check 13 failing is not a `NOT READY` on its own — it is a recommendation to split, stated
with the proposed split boundary.

---

## Step 8 — Report and stop

Print:

1. The output path.
2. The mode used, and the counts: requirements, acceptance criteria, assumptions,
   decisions, open questions.
3. The gate verdict from Step 7.
4. Every `blocker` open question, verbatim.
5. The follow-up commands, **as plain text only**:

```
Next (run manually):
  /phase-discovery <path>      — decompose into subtasks and plan
  /spec-run <path>             — orchestrated run to review-ready PRs
  /spec-draft <path> --brain-storm  — another authoring round on this spec
```

Then **stop**. Do not invoke any of them. Do not create a task directory. Do not write
`state.md`. Do not start implementing.

**Human sign-off.** An AI-authored spec that no human has read is a draft, whatever the
gate says. State this in the report in one line: "Gate is an automated check, not sign-off —
review before implementation."

---

## Re-running on an existing spec

`/spec-draft <path-to-existing-spec> [--brain-storm | --auto-mode]` refines rather than
replaces. The Guard's confirmation still applies, and additionally:

- Existing `REQ-NN` and `AC-NN` ids are preserved. New material is appended with new ids.
- `## Clarifications` gains a new `### Session YYYY-MM-DD` block; earlier sessions are kept.
- `## Assumptions` and `## Decisions` are appended to, never rewritten — a superseded line
  is marked `(superseded by D-NN)` and left in place.
- `## Source` is never edited.
- The gate is re-run in full and the `## Readiness Checklist` replaced with the new result.
