# ADR-0003: Decisions for Task unknown — Rules deploy to Claude Code and Codex as `rule-<name>` skills; always-on essentials are duplicated

## Status

Accepted

## Date

2026-07-21

## Related Task

- Task: logic-audit-fixes (finding B-3, CHANGE 1)
- Related files: `sync.sh` steps 3c/4c, `rules/workflow-globals.md → Context Bootstrap`, `rules/global-claude.md`, `templates/codex-global-AGENTS.md`

## Summary

Claude Code and Codex have no rules directory. Each `rules/*.md` is deployed as a skill
under a mandatory `rule-` prefix, and the always-on essentials are duplicated into
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`.

## Context

The 2026-07 audit found that the five `phase-*` rule files were never reachable from
Claude Code or Codex, so the Context Bootstrap could not run there. Five rule basenames
collide with workflow basenames, so an unprefixed deployment would overwrite workflows.

## Decisions

### Decision 1: `rule-` prefix, always

**What was decided:**
`sync.sh` deploys `rules/<name>.md` → `~/.claude/skills/rule-<name>/SKILL.md` and the
same under `~/.codex/skills/`. Workflows say "load the `<name>` rule" and the reader
resolves it per harness (`workflow-globals → How to resolve a rules reference`).

**Why:**
Correctness (collision avoidance), not style.

**Alternatives:**
- Rename the colliding rule files — rejected: the Windsurf rule names are referenced by
  bare basename in every workflow.
- Merge all rules into `CLAUDE.md` — rejected: ~17 600 words always-on.

**Consequences:**
A skill is model-invoked, not always-on. The trigger semantics differ per harness, which
is stated openly (`principles/architecture.md → P11`).

**Related files:**
- `sync.sh`, `validate-contracts.sh` (rule-skill checks)

### Decision 2: Duplicate the essentials

**What was decided:**
`rules/global-claude.md` and `templates/codex-global-AGENTS.md` carry the always-on
summary (language, commit rule, test-first, context loading) and are deployed verbatim.

**Why:**
Those are the rules that must hold even when the model does not invoke a skill.

**Alternatives:**
- Rely on skills alone — rejected: a session that never loads `rule-tdd` would not know
  test-first exists.

**Consequences:**
Two summaries to keep in sync with the full rules (`specs/10-generated-reference-docs.md`
proposes generating them).

**Related files:**
- `rules/global-claude.md`, `templates/codex-global-AGENTS.md`

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

See Alternatives.

## Implications for Future Work

Any new always-on rule must be added to both summaries and to `setup-new-project.sh`'s
rule-copy list.

## Verification

`validate-contracts.sh` checks that every `rules/*.md` has a `rule-` deployment line in
`sync.sh` and that the Context Bootstrap table names both forms.
