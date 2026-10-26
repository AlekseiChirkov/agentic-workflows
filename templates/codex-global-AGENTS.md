# AGENTS.md — Global Codex Instructions
# Managed by Orchestrail/scripts/sync.sh — do not edit here; edit templates/codex-global-AGENTS.md.
# Codex merges this global file with each project's own AGENTS.md.

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
