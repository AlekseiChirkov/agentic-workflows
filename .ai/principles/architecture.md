# architecture.md — architectural principles of the workflow system

## Purpose
The design principles that shape Orchestrail as a product. A change to a rule,
workflow, or script that violates one of these is a design change and needs an ADR — not
a quiet edit. Global engineering principles (`principles/*.md` at the repository root)
still apply to the shell scripts.

## Principles

### P1 — The repository is the only source of truth
Edits happen here and nowhere else. Deployed copies (`~/.claude/skills`, `~/.codex/skills`,
`~/.codeium/windsurf/global_*`, project `.windsurf/rules/`) are disposable and overwritten
by `scripts/sync.sh`. A fix applied to a deployed copy is lost; a fix applied here reaches every
harness and every project.
*Rationale:* three harnesses, N projects, one author — divergence is the default failure.

### P2 — State lives on disk, not in the conversation
Every phase reads `state.md` before acting and writes it before finishing. A workflow must
be resumable by re-running the same command with no flags. Nothing an agent "remembers"
counts; only what is written counts.
*Rationale:* context windows end, sessions crash, agents are swapped mid-task.

### P3 — Canonical formats are contracts, and contracts are additive
Status vocabularies, block layouts, section names, and cross-reference syntax are defined
once (`workflow-globals`, `workflow-reference`) and consumed everywhere. A change is made
by extension with a backward-compatibility rule for readers (e.g. a missing
`atomic-tests:` reads as `not-started`), never by renaming. Parsers key on field names,
never on position.
*Rationale:* tasks in flight in other repositories were written under the old format.

### P4 — One writer per shared file
`state.md`, `plan.md`, `architecture.md`, `adr/index.md` each have exactly one writer at
any moment. Sub-agents return deltas; the orchestrator applies them. This is why execution
is strictly sequential today, and why parallelism requires a state-format change first.
*Rationale:* markdown has no locking; a truncated block from a concurrent writer corrupts
the resume point for every later step.

### P5 — Every stop is declared
A workflow stops only at a named `**stop**` with a reported reason, at a `## Guard`, or at
a condition listed in `workflow-globals → Workflow-declared mode overrides`. An autonomous
mode licenses *unblocked* decisions, never *unrecorded* ones. There is no silent decision
and no undeclared stop.
*Rationale:* an operator must be able to predict where a run will wait.

### P6 — Rules govern, workflows execute, reference explains
A `rules/` file states a contract in the fewest words that make it unambiguous. A
`workflows/` file is an executable sequence that cites rules by `file → ## Section`. Rationale,
worked examples, and incident history belong in `workflow-reference` or in the rule's own
"why" paragraph — never spread across workflows. A statement that exists in two places is
a defect (see the 2026-07 audit: ten dangling references).
*Rationale:* the always-on context budget is finite; duplication drifts.

### P7 — Test-first is not suspended by any mode
`/pae-tests` precedes `/pae-implement` on every leaf; the quick tier runs the same cycle
inline; `/phase-pipeline` and `/spec-run` do not override it; `none` needs a written
justification. This repository applies it to itself at the `smoke` level via
`scripts/validate-contracts.sh`.
*Rationale:* tests written after the code describe the code, not the requirement.

### P8 — The pipeline is invisible to the repository it works on
No subtask identifier, spec name, task directory, ADR number, `.ai/` path, workflow name,
or tool attribution reaches product content, a branch name, commit message, or PR.
Knowledge records and workflow definitions may describe the process. Repository-owned
tracking policy determines whether knowledge and state are shared; untracked consumer
state remains local unless explicitly authorized.
*Rationale:* a reader of the repository who never saw the pipeline must not meet dangling
pointers.

### P9 — Logging never blocks, and numbers are never guessed
`scripts/log-step.sh` stamps its own timestamps, derives durations from its own previous write,
and exits 0 on every error. An agent never hand-writes a log line. An omitted field means
"not measured"; a `0` means "measured and none".
*Rationale:* a metrics store with invented numbers is worse than none.

### P10 — Enforcement should move toward the harness, not toward more prose
When a harness can enforce a rule (hooks, permission deny-lists, a validating script),
that is preferred over a paragraph asking the model to comply. Prose remains as the
explanation. This principle is aspirational today — most rails are still text — and the
roadmap (`specs/`) is ordered by it.
*Rationale:* the run log shows text rules being violated (retroactive logging,
non-vocabulary statuses); the interpreter of these rules is probabilistic.

### P11 — Environment parity is stated, not assumed
Where a harness cannot execute a mechanism (sub-agents on Windsurf, always-on rules on
Claude Code), the documentation says so and the rule provides the closest substitute
(`rule-*` skills, `global-claude.md` essentials). A capability that only works in one
harness is labelled with that harness.
*Rationale:* an undocumented gap is a workflow that silently does something else.

### P12 — The system measures itself
Every orchestrator writes the run log; `/retro` is its only reader; findings must name a
file and an edit. Changes to workflows are expected to be justified by evidence from the
log where evidence exists.
*Rationale:* "the pipeline feels slow" is not actionable; "four of nine runs stopped at
the same gate" is.
