---
trigger: always_on
---

# Language Rule (always-on)

Before creating or modifying ANY file or text artifact, apply this rule first.

**All content written to project files must be in English.** This covers every file
type and every kind of text produced during development: source code, comments,
docstrings, commit messages, configuration files, shell scripts, Terraform HCL, YAML,
JSON, Markdown docs, README/ADR/state files, test names and fixtures, and any other
artifact created or edited in the project.

If existing content in a file is not in English, keep new content English and do not
mirror the other language.

This rule applies ONLY to generated code and project files.

# Chat language preference is user-specific.
# Set this in your personal ~/.claude/CLAUDE.md, not here.
