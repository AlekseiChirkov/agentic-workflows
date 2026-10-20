---
trigger: always_on
---

# Workflow Global Principles

These rules govern ALL phase workflows (`/phase-discovery`, `/phase-execution`, `/phase-validation` and their atomic counterparts) without exception.

**Context Bootstrap (mandatory for every phase invocation).** Before reading any codebase file or modifying any project file, load `.ai/` context from the phase-specific rules file:

| Phase | Rules file (Windsurf / Devin) | Skill name (Claude Code / Codex) | Loaded by |
|-------|-------------------------------|----------------------------------|-----------|
| Discovery | `phase-discovery` | `rule-phase-discovery` | `/phase-discovery`, `/pd-analyze` |
| Execution | `phase-execution` | `rule-phase-execution` | `/phase-execution`, `/pe-execute` |
| Validation | `phase-validation` | `rule-phase-validation` | `/phase-validation`, `/pv-contract`, `/pv-review` |
| Atomic Execution | `phase-atomic-execution` | `rule-phase-atomic-execution` | `/phase-atomic-execution`, `/pae-tests`, `/pae-implement` |
| Atomic Validation | `phase-atomic-validation` | `rule-phase-atomic-validation` | `/phase-atomic-validation`, `/pav-check` |

**How to resolve a rules reference in each environment.** On Windsurf and Devin a rule is a file
under `global_rules/` / `.windsurf/rules/` / `.devin/rules/`, addressed by its bare basename. On
Claude Code and Codex there is no rules directory, so `scripts/sync.sh` deploys every `rules/*.md` as a
skill under the `rule-` prefix — `workflow-globals` → `rule-workflow-globals`, `tdd` →
`rule-tdd`. The prefix is mandatory: five basenames (`phase-discovery`, `phase-execution`,
`phase-validation`, `phase-atomic-execution`, `phase-atomic-validation`) exist in both
`workflows/` and `rules/`, and an unprefixed rule skill would overwrite the identically-named
*workflow* skill. When a workflow says "load the `<name>` rule", resolve it to
`rule-<name>` on Claude Code and Codex and to the bare basename on Windsurf and Devin.

A skill is model-invoked, not always-on. Deploying an `always_on` rule as a skill therefore
changes its trigger semantics: the file is reachable, but it is not loaded unbidden. That is why
the always-on essentials stay duplicated in `rules/global-claude.md` (→ `~/.claude/CLAUDE.md`)
and `templates/codex-global-AGENTS.md` (→ `~/.codex/AGENTS.md`), which those agents do read on
every session. The `rule-*` skills carry the full contracts those summaries point at.

Rules define the exact load order, what to extract, and phase-specific behaviors.
**Standalone invocation rule:** when a child workflow runs without its parent orchestrator (e.g., `/pav-check` without `/phase-atomic-validation`), it must run the full bootstrap as if no parent loaded context. Never assume context was pre-loaded.
**Context Pack (optional optimisation).** `/context-pack` assembles bootstrap sources 1–7 —
the three `principles/`, `memory/architecture.md`, `memory/state.md`, `adr/index.md`, and
`context/runbook.md` — into one verified `.ai/context-pack.md`. A step may read the pack
**instead of** those seven files, on one precondition: it confirmed the pack fresh against
its own manifest (path, size, mtime of every source) in the same session. Stale, absent, or
unverified → read the sources directly. The substitution never covers a conditional load
(`integrations.md`, `environment.md`), a full ADR body, or `progress.md`; those are read from
source, packed or not. The pack is a cache with a freshness check, never a source of truth,
and no workflow may write to it.

**Umbrella-first rule:** in multi-repo projects, check if `../.ai/` exists. If yes, load umbrella before local `.ai/` — local overrides umbrella.

---

**Never auto-advance between phases.** After completing a phase (`/phase-discovery`, `/phase-execution`, `/phase-validation`), STOP completely. Do NOT invoke the next phase command. Display the next command as plain text for the user to run manually. Phase transitions are always initiated by the user, never by Claude.

**Continue, never restart.** Before any workflow, read state files. If progress exists — continue from stopping point. Never restart from scratch.

**Wait for user decisions.** Architectural / technical / ambiguous choice → present 2–3 options with trade-offs, wait for user decision. Never decide independently in ambiguous situations.

**Workflow-declared mode overrides.** A workflow may declare an autonomous mode that overrides "Wait for user decisions" and the Trust-mechanism stop rule below, for the duration of that workflow only. When it does, the workflow decides independently via `workflow-reference → ## Autonomous Decision Protocol` and records the rationale in `state.md`. Currently declared by:

| Workflow | Autonomous when | Interactive when |
|---|---|---|
| `/phase-pipeline` | always | never |
| `/phase-discovery` (+ `/pd-analyze`, `/pd-decompose`, `/pd-design`, `/pd-finalize`) | default | `--step-by-step` passed |
| `/pav-propose` | `--batch` passed | default |
| `/spec-run` (+ `/restack`) | always, except the Discovery batch gate | never — the batch gate is its only planned stop |

`/phase-pipeline` additionally overrides these named steps, and only these — the full table with
rationale is `phase-pipeline → ## Pipeline Overrides`, and its `### Declared stops` subsection
lists every step it deliberately does **not** override:

| Step | Pipeline behaviour |
|---|---|
| `/pv-issues` step 4 — approve/defer prompt | approve `critical` + `important`, defer `optional` |
| `/pe-finalize` step 5 — batched `Do Now` prompt | choose option 2 (apply now, before validation) and record that the choice was automatic |
| `/pe-execute`, `/pv-execute-fixes` — "wait for user's choice" on an ambiguity | resolve via the Autonomous Decision Protocol; a *blocker* still stops |
| `/phase-composite-validation` step 2 — approve/defer prompt on integration failures | approve `critical` + `important`, defer `optional`, and record that the split was automatic |

**`--batch` — one meaning, everywhere.** `--batch` is `/pav-propose`'s flag, passed down
unchanged by `/phase-atomic-validation`, `/pe-execute`, `/pv-execute-fixes`, `/spec-run`, and
`/phase-pipeline`. It means: **record every proposal, prompt for nothing, apply nothing.** No
caller may redefine it — in particular, no autonomous mode may read it as
apply-without-asking. A workflow that wants the `Do Now` items applied applies them at a step of
its own and declares that step as an override (`/phase-pipeline` → `/pe-finalize` step 5).

No mode override ever suspends: **Never auto-advance between phases**, Guard confirmations that would overwrite existing artifacts, or the escalation conditions in the Autonomous Decision Protocol. A mode override does not license silent decisions — it licenses *unblocked* decisions, and every one must be written down.

**Trust mechanism in execution.**
- Trivial task (clear plan, no dependencies, no ambiguity) → execute autonomously without stopping.
- Non-trivial task (ambiguity, architectural choice, Off-limits risk, blocker) → stop immediately, describe the problem, propose 2–3 options with trade-offs, wait for user decision.
- AI evaluates triviality based on the plan from atomic-discovery. Any doubt → treat as non-trivial.
- Number of stops is unlimited: an extra stop is always better than a silent wrong decision.

**Strict adherence to artifacts.** Execution at any level follows the plan and architecture from the corresponding Discovery exactly. No deviations.

**Orchestrated mode.** `/spec-run` carries one spec from Discovery to review-ready pull
requests using context-bounded sub-agents, one stacked branch per subtask. It is strictly
sequential — no workflow may introduce concurrent subtask execution, because the single
`## Subtask Progress` section has no locking. Roles, context boundaries, and the class A/B
escalation protocol are defined in **`orchestration`**; branching, commits, and git safety
rails in **`git-flow`**. Orchestrated mode does not suspend the escalation conditions, the
Guard confirmations, or the test-first rule below.

**Test-first execution.** Implementation is never the first step of an atomic cycle. Every
leaf subtask passes through `/pae-tests` (RED) before `/pae-implement` (GREEN) — the failing
tests are written from `## Acceptance Criteria` and become a frozen contract the
implementation must satisfy rather than edit. The step is additive: it precedes the existing
cycle and replaces nothing. Work that is genuinely not testable passes an explicit,
recorded gate rather than skipping silently. Full contract → the **`tdd`** rule; test style →
`testing-standards`. No autonomous mode — including `/phase-pipeline` — suspends it.

**File updates after each phase.** After completing any phase, update relevant state/plan files and run `/compress-state --auto`. Only update files relevant to the completed phase. Current phase status must always be present in `state.md`.

**Direct child-workflow invocation for partial reruns.** To re-run a specific step, call its child workflow directly (for example `/pd-analyze`, `/pae-implement`). There is no `--step=N` flag. Each child workflow has a `## Guard` section that detects already-completed work and asks for explicit confirmation before overwriting.

---

## Flow tiers (quick | full)

Every task runs in one of two tiers, recorded in the top-of-file `flow:` field. **`full`
is the default and is the complete, unchanged pipeline.** `quick` is a lighter but
still-governed path for small changes; the full specification, gate, and mid-flight
escalation live in the **`quick-flow`** rule. Summary:

- A task qualifies for `flow: quick` **only if ALL four gate conditions hold** (else it is
  `full`, no exceptions): (1) 3 or fewer files, counting test files; (2) no new invariant;
  (3) no behaviour change to an already-shipped pipeline; (4) no DB schema change / no
  migration. Condition 1 is a count, not an estimate — the fourth file sends the task to
  `full`, and a quick task that discovers it mid-flight is promoted (see `quick-flow →
  ## Mid-flight escalation`). Condition 3 is the one that would have caught the 2026-07-22
  out-of-pipeline macro fix.
- The quick path SKIPS `/pd-decompose`, `/pd-design`, `/pd-archive`, T-XX subtasks, and the
  separate `/pv-create-fixes` + `/pv-execute-fixes` cycle. It still MANDATES an inline
  contract in `state.md` (`## Contract (quick)` with `### Off-limits` / `### Invariants` /
  `### Acceptance Criteria`, written before any code), **the TDD step inline** (RED against
  the quick contract's Acceptance Criteria before implementation — see `quick-flow`),
  `/pv-contract` + `/pv-review`, an ADR on the same trigger as the full path, and a
  `progress.md` entry.
- A quick task that breaches any gate condition mid-flight MUST be promoted to `full` and
  the promotion recorded in `state.md` — never silently finished. See `quick-flow`.

This tier does not weaken **Never auto-advance between phases** or the ADR trigger.

---

## Canonical Status Formats

These formats are the contract between all workflows. Do not rename, reformat, or extend them without updating every workflow that reads them.

**Top-level task `state.md`:**
```
spec_path: <path-to-spec>
flow: quick | full

## Phases
- discovery: not-started | in-progress | complete
- execution: not-started | in-progress | complete
- validation: not-started | in-progress | complete
```

`flow:` is a top-of-file field (alongside `spec_path:`), set during Discovery by `/pd-analyze` and defaulting to `full`. It selects the tier — see `## Flow tiers` below and the `quick-flow` rule. `## Phases` is unchanged in both tiers. Multi-phase fields (`active_phase:`, `spec_phase_count:`) keep their existing position after `spec_path:`.

**Parent `state.md` → `## Subtask Progress` (one block per T-XX):**

*Leaf block* (any subtask without children — this is the default):
```
T-XX | <name> | atomic-tests: <status> | atomic-execution: <status> | atomic-validation: <status>
  last_action: <one line — what was done last>
  target_files: <comma-separated list of files modified, test files included — required, write even if empty>
  blocker: <none | description of blocker>
  notes: <key decisions or deviations — required, write even if empty>
  branch: <branch name — orchestrated mode only>
  base_branch: <branch this one was cut from — orchestrated mode only>
  base_commit: <sha of the branch point — orchestrated mode only>
  commits: <sha <type>: <summary>, ... — orchestrated mode only; the commit scope is a feature or module name, never a subtask identifier (see `git-flow`)>
  pr: <#N draft | #N ready | none — orchestrated mode only>
```

The five git fields are written only when the task runs under `/spec-run` (see the
`orchestration` and `git-flow` rules). They are absent in ordinary manual runs, and readers
must not require them. `base_commit` is written once, at branch creation, and never
recomputed — it is the only input that lets `/restack` replay a branch after its parent was
squash-merged.

Status values for atomic-execution / atomic-validation: `not-started` | `in-progress` | `complete` | `blocked` | `skipped` | `failed`.

Status values for `atomic-tests`: `not-started` | `red` | `pinned` | `green` | `n-a` | `failed`.
Written by `/pae-tests` (`red` / `pinned` / `n-a` / `failed`) and `/pae-implement` (`green`);
preserved by `/pae-finalize`, `/pav-close`, and `/compress-state`. `pinned` is characterization
mode — tests that pin existing behaviour and pass before the change, used for
behaviour-preserving work; it transitions only to `green`. Semantics → the `tdd` rule.

**Backward compatibility (required of every reader):** a leaf block **without** an
`atomic-tests:` field is a pre-TDD task. Treat the missing field as `not-started`, do not
error, and do not retroactively demand RED for a subtask already `atomic-execution:
in-progress` — record `pre-TDD task, TDD step skipped` in `notes:` and continue. The field's
position (first status field, before `atomic-execution:`) is fixed; parsers must key on the
field name, never on ordinal position.

*Composite block* (a subtask that owns leaf children — written by `pd-decompose` when a subtask is classified as Type 2 or is the product of Type 3 re-slicing):
```
[composite] T-XX | <name> | rollup: <status> | integration-validation: <status>
  children: T-XXa, T-XXb, T-XXc
  blocker: <none | description of blocker>
  notes: <classifier rationale — which signals fired, why nested>
```

Status values for `rollup`: `not-started` | `in-progress` | `done` | `blocked`.
Status values for `integration-validation`: `not-started` | `in-progress` | `complete` | `failed`.
A composite's `plan.md` Status reaches `reviewed` **only** after `integration-validation: complete`.

Detection rule: a block starting with `[composite]` is a composite block; all others are leaf blocks. Readers that encounter an unrecognized prefix must treat the block as a leaf (backward compatibility).

T-XX subdirectories no longer contain their own `state.md` or `plan.md`. All atomic-level progress lives in the parent task's `state.md → ## Subtask Progress`.

**`notes:` field rules:**
- `notes:` is ALWAYS written, even when empty. Example: `notes:`
- `/compress-state` must NOT remove an empty `notes:` line.
- `target_files:` is ALWAYS written, even when empty. Example: `target_files:`
- `/compress-state` must NOT remove an empty `target_files:` line.
- `atomic-tests:` is ALWAYS written in leaf blocks once `/pae-tests` has run, and is never
  removed or downgraded by a later workflow.
- `branch:`, `base_branch:`, `base_commit:`, `commits:`, `pr:` — once written by `/spec-run`,
  never removed, rewritten, or summarized by any workflow other than `/restack`. Losing
  `base_commit` makes the branch stack unrepairable; losing `commits` makes the run's history
  unreportable.
- `notes:` lines beginning with `tdd:` (test level, `none` justification, test amendments)
  are part of the TDD audit trail — `/compress-state` must NOT remove or summarize them.

**Composite field rules:**
- `children:` is ALWAYS written in composite blocks, even if only one child exists.
- `blocker:` is ALWAYS written in composite blocks, even when `none`.
- `notes:` in a composite block MUST include the classifier rationale (which signals fired).
- `/compress-state` must NOT remove or summarize composite block headers or field lines.

---

**Fix-task progress blocks:**
Fix-task progress blocks follow the same format as regular T-XX blocks and live under `## Subtask Progress` in the parent `state.md`. `## Fix-Tasks` contains ONLY the `fixes-created` marker, `fixes-count` field, and the `Created` list — never progress blocks.

**`## Fix-Tasks` format:**
```
## Fix-Tasks
fixes-created: complete
fixes-count: <N>
Created: T-XX-fix-<slug>, ...

### Fix Classification
<table written by /pv-classify-fixes — shared vs dedicated branch per issue, with all
four quick-flow gate results recorded so the decision can be audited>
```
When no fix-tasks were created: `fixes-count: 0` and `Created: none`, and no
`### Fix Classification` subsection.

`### Fix Classification` is the ONLY permitted subsection. Progress blocks never go here —
fix-task progress lives in `## Subtask Progress` like any other leaf.

**Subtask statuses in `plan.md`:**

| Status | Meaning |
|---|---|
| `not-started` | Not started |
| `in-progress` | In progress |
| `done` | Execution complete, validation not started |
| `reviewed` | Validation passed, task closed |
| `deferred` | Postponed by decision after phase-validation |
| `blocked` | External blocker not dependent on code |
| `not-reached` | Execution finished without reaching this subtask |

Extended examples, file-role rationale → `workflow-reference`.
