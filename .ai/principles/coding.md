# coding.md — standards for writing workflow, rule, principle, and script files

## Purpose
How files in this repository are written so that an LLM can execute them, a human can
audit them, and `validate-contracts.sh` can check them. These are the "coding standards"
of a codebase whose language is instructional markdown plus bash.

## Standards

### Language and tone
- English only, in every file (`rules/language.md`).
- Imperative, second person to the agent ("Read `state.md`", "**stop**: …"). No hedging
  ("try to", "ideally") in a contract — a rule either holds or does not.
- Explain *why* once, next to the rule, in one paragraph. Do not repeat the rationale in
  each workflow that cites the rule.
- No planning identifiers in anything that could be copied into a consumer repository:
  examples in rules use domain names (`feat/oauth-token-schema`), never `T-01`.

### Workflow file shape (`workflows/*.md`)
1. Front matter: `description:` — one line, starts with the step name
   ("Discovery Step 2 — …", "Atomic Validation Step 1 — …", "Utility — …").
2. `Invocation:` line with the exact argument form; `Called by:` line for children.
3. Working-directory resolution when the workflow touches files (`working_dir:` handling,
   `WORK_DIR` / `AI_DIR`).
4. `## Guard` — detect prerequisites and already-completed work; ask before overwriting;
   never silently redo.
5. Numbered steps. Each step names what it reads, what it writes, and where.
6. Every stop is written `**stop**: "<message>"` followed by what the user should do.
7. A final report line ("Step N (Name) complete. …") and, for children of an autonomous
   parent, an explicit "progress marker, not a handoff" note.
8. Cite rules as `` `rule-name` `` and sections as `` `file → ## Section` ``. Never paste a
   rule's body into a workflow.

### Rule file shape (`rules/*.md`)
- Front matter `trigger: always_on` (Windsurf semantics; on Claude Code/Codex the file
  becomes a `rule-<name>` skill).
- Contract first, rationale second, worked examples last. Target: a rule readable in one
  screen before its first example.
- Any vocabulary (status values, field names, enum) is defined on **one anchored line**
  that `validate-contracts.sh` can grep for, e.g.
  `Status values for atomic-execution / atomic-validation: …`.
- When a rule changes a canonical format, it also states the backward-compatibility rule
  for readers.

### Cross-references
- Syntax: `` `file → ## Section` `` or `` `file → ## Section → ### Subsection` ``. The
  section must exist with that exact heading text.
- Adding a reference means adding a check in `validate-contracts.sh` if the target is a
  section other workflows do not already depend on.
- A concept has exactly one canonical definition. If two files must mention it, one of
  them says "canonical definition: `file → ## Section`".

### Changing a contract
1. Write the failing check in `validate-contracts.sh` first (RED at `smoke` level).
2. Update the canonical definition.
3. Update every reader and writer — grep for the old value across `workflows/`, `rules/`,
   `docs/USAGE.md`, `PIPELINE.md`, `templates/`.
4. Add the backward-compatibility rule if artifacts in the old shape may exist.
5. Run `validate-contracts.sh`, then `sync.sh`.
6. Record the change in `.ai/adr/` if it alters a format, a stop, or a mode override.

### Shell scripts
- `#!/bin/bash` (or `#!/usr/bin/env bash`), `set -uo pipefail`; `set -e` only where a
  failure must abort (`sync.sh`, `setup-*.sh`). Logging helpers exit 0 on every path.
- A header comment: what the script does, its contract, usage, exit codes.
- No hard-coded home paths in new code; read `ORCHESTRAIL_HOME` / `ORCHESTRAIL_LOG_ROOT`
  with the current default as fallback.
- Every check in `validate-contracts.sh` uses the `check "<desc>" "$(… && echo pass || echo '<reason>')"` form and is anchored to a definition line, not a bare substring.
- `bash -n` before committing; `shellcheck` when available.

### Document placement (mandatory)
Every document that is *about* the project rather than *part of* the pipeline goes under
`docs/`, never in the repository root and never in `.ai/` or `workflows/`:

| Kind | Location | Naming |
|---|---|---|
| Analysis, comparison, research, review of the system | `docs/analysis/` | `YYYY-MM-DD-<slug>.md` (`.ru.md` suffix for a Russian original) |
| Audit prompts, audit reports, audit fix specs | `docs/audits/` | prompts by name (`AUDIT-PROMPT.md`); reports and fix specs `YYYY-MM-DD-<slug>.md` |
| Retro reports produced by `/retro` | `logs/` (untracked, per `run-log`) — copy a report to `docs/retros/YYYY-MM-DD-retro.md` only when it drives a spec |
| Operating manuals, quickstarts, harness matrices, guides | `docs/` root | descriptive upper-case names (`USAGE.md`, `SPEC-RUN-QUICKSTART.md`) |
| Worked examples of finished tasks | `docs/examples/<slug>/` | — |

The repository root holds only `CLAUDE.md` (the harness reads it there), `README.md`
(once spec 11 creates it), `LICENSE`, the scripts, and the source directories
(`workflows/`, `rules/`, `principles/`, `templates/`, `.ai/`, `docs/`, `logs/`).

An agent asked to "analyse", "audit", "compare", "review", "summarise", or "write up"
anything about this repository creates the file under `docs/` in the matching
subdirectory, dated, and links it from `docs/README.md`. It never creates such a file in
the root, in `.ai/`, or next to the workflows. Improvement *specs* are the exception: an
actionable change goes to `.ai/specs/<NN>-<slug>.md` so the pipeline can pick it up, and
the analysis that motivated it stays in `docs/`.

### Documentation
- `docs/USAGE.md` is the operating manual; `PIPELINE.md` the reference; a workflow's own header
  is the authority on its invocation. When they disagree, fix the two derived ones to
  match the workflow (until `specs/10-generated-reference-docs.md` makes them generated).
- Numbers quoted in docs (check counts, file counts) are updated in the same change that
  changes them.

### Commits (once the repository is under git)
- `<type>[(<scope>)]: <imperative summary>`; scope names a layer or workflow in plain words
  (`rules`, `spec-run`, `sync`), never a task or spec identifier.
- No authorship attribution trailers of any kind (`rules/git-flow.md → ## Commits`).
- One contract change per commit where possible: rule + its readers + its check together.
