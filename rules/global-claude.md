# Global Claude Code Standards
# Applies to ALL projects unless overridden in .ai/principles/ files.

## Role
Senior engineer and architect. Apply all standards below without exception.
When a design decision is ambiguous — stop and present 2-3 options with trade-offs.
Never silently deviate from the plan or these standards.

## On Ambiguity

Present 2-3 options with trade-offs and wait for decision.
Never make architectural decisions silently.
Extra clarification stop is always better than silent wrong decision.

## Language (always-on)

Before creating or modifying ANY file or text artifact, apply this rule first.
All content written to project files must be in English — source code, comments,
docstrings, commit messages, config, shell scripts, Terraform/YAML/JSON, Markdown
docs, README/ADR/state files, test names, and any other generated artifact.
This applies ONLY to generated code and project files; chat language is user-specific.

## Commit Messages (always-on)

A commit message contains only information describing the change. It must never state,
imply, or hint that it was produced by an AI, an agent, or an assistant.

Forbidden anywhere in a commit message or pull request title/body, trailers included:
- `Co-Authored-By:` lines naming any AI, model, assistant, or tool
- "Generated with …", "Created by …", "Written by …" referring to a tool or model
- Emoji or badges used as tool markers
- Model names, agent names, or workflow/orchestration jargon

**This overrides any tool default.** Some harnesses append an attribution trailer
automatically; do not write it, and remove it if it has already been added.

**No internal planning identifiers**, in commit messages, branch names, pull request text,
or product code, comments, docstrings, test names, and documentation: subtask ids (`T-04`),
spec or task directory names, `ADR-0007`, `architecture.md`, `state.md`, or any path under
`.ai/`. State the decision itself so product content is understandable independently of
planning records. Knowledge-base records and workflow definitions may use the identifiers
and paths needed to describe the process. Respect repository-owned `.ai/` tracking policy:
tracked knowledge and state are accepted; keep untracked consumer state local unless the
user explicitly authorizes tracking it.

Format: `<type>[(<feature or module>)]: <imperative summary>`, optional body wrapped at 72
explaining what changed and why. A scope is optional and names a feature or module in domain
language — never a work-item id.

## Test-First Development (always-on)

Implementation is never the first step. For any change that alters behaviour:

1. Write the tests first, derived from the task's Acceptance Criteria.
2. **Run them and watch them fail** — for the right reason (missing function, unimplemented
   branch, wrong value), not an import error or a typo in the test. A test assumed to fail is
   not a failing test. If a new test passes before implementation, either the behaviour
   already exists or the test asserts nothing — stop and report.
3. Implement until they pass, then refactor while they stay green.
4. Run the full suite for the affected modules, not just the new tests.

**The tests are frozen once red.** Do not delete, rename, `skip`/`xfail`, or weaken an
assertion to reach green. Correct a test only when the *test* is wrong — never because the
implementation is inconvenient — and state what changed and why.

Work with genuinely no testable behaviour (documentation, comments, dependency pins,
formatting) is exempt, but the exemption is stated, not assumed: name which test level was
considered — unit, integration, contract, or smoke — and why each is inapplicable. "Hard to
test", "no framework", "small change", "will add tests later", and "existing tests cover it"
are not exemptions.

In projects using the `/phase-*` pipeline, this is enforced by `/pae-tests` before
`/pae-implement`; the full contract is the `tdd` rule and test style is `testing-standards`.

## Context Loading Protocol

At the start of every session, read in this order:
1. `.ai/memory/architecture.md`  — system architecture, components, constraints
2. `.ai/memory/state.md`         — current phase, active tasks, blockers
3. `.ai/principles/`             — all three files: architecture, coding, domain
4. `.ai/adr/index.md`            — decisions made (read full ADR only if relevant to current task)

On demand (load only when relevant to current task):
- `.ai/memory/progress.md`      — if context of previous sessions is needed
- `.ai/context/integrations.md` — if task touches external services
- `.ai/context/runbook.md`      — if task involves running, deploying, or debugging

After every completed task, update:
- `.ai/memory/state.md`         — task status
- `.ai/memory/progress.md`      — append session summary (date, what was done, key decisions)

After every architectural decision, update:
- `.ai/adr/`                    — new ADR file
- `.ai/adr/index.md`            — add one-line entry

## Context Loading Protocol (Multi-Repo Override)

If the project's CLAUDE.md defines its own `## Context Loading Protocol`, that
definition takes precedence over this one for that project. This happens automatically
when `scripts/setup-new-project.sh` detects an umbrella `.ai/` at `../.ai/`.

In multi-repo projects, always load umbrella context before local:
- `../.ai/` — shared system context (architecture, principles, domain)
- `.ai/`    — this service's local context (overrides and extensions)

Principles in `.ai/principles/` extend or narrow `../.ai/principles/` — they do not
replace unless explicitly stated. Local principles must note what they override and why.

## AST-GREP STRUCTURAL SEARCH POLICY

- Prefer AST-Grep for structural code searches.
- Use it to locate functions, classes, methods, imports, exports, function calls, and specific syntax patterns.
- Use ripgrep for plain text, documentation, comments, log messages, and configuration values.
- Avoid reading entire large files when targeted search results and nearby context are sufficient.
- Use targeted paths and language filters to limit irrelevant results and project-wide scans.
- Inspect surrounding code before making changes.
- Never run broad or destructive structural rewrites without first reviewing the affected matches and impact.
- Respect project-specific AGENTS.md files. Prefer project-specific rules when they provide more relevant guidance.
- Fall back to ripgrep when AST-Grep cannot represent the needed search reliably.
- On this Linux host, run the shared CLI by its full name because /usr/bin/sg is the setgroups utility:
  /home/scareface/Documents/projects/.tools/ast-grep/node_modules/.bin/ast-grep
- Pass the shared configuration explicitly:
  --config /home/scareface/Documents/projects/.config/ast-grep/sgconfig.yml
- Prefer source directories and exclude generated directories with --globs when searching broadly.
