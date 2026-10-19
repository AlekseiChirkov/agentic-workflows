# AGENTS.md — Global Codex Instructions
# Managed by Orchestrail/sync.sh — do not edit here; edit templates/codex-global-AGENTS.md.
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

**No internal planning identifiers**, in commits *or* in committed code, comments,
docstrings, test names, and documentation: subtask ids (`T-04`), spec or task directory
names, `ADR-0007`, `architecture.md`, `state.md`, or any path under `.ai/`. Where an `.ai/`
directory exists it is not committed, so such a reference points at a file the reader does
not have. State the decision itself rather than citing where it was recorded.

Format: `<type>[(<feature or module>)]: <imperative summary>`, optional body wrapped at 72
explaining what changed and why. A scope is optional and names a feature or module in domain
language — never a work-item id.
