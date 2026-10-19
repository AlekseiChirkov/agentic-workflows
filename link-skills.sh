#!/bin/bash
# Workaround for Claude Code bug:
# When project has .claude/skills/, global ~/.claude/skills/ are ignored.
# This script symlinks global skills into the project.
# Run once per project that has its own .claude/skills/ directory.
# Usage: bash /path/to/agentic_workflows/link-skills.sh

set -e
PROJECT_SKILLS=".claude/skills"

if [ ! -d "$PROJECT_SKILLS" ]; then
  echo "No .claude/skills/ found in current directory."
  echo "Global skills work automatically — no linking needed."
  exit 0
fi

echo "Linking global skills into project..."
for skill in ~/.claude/skills/*/; do
  name=$(basename "$skill")
  if [ ! -e "$PROJECT_SKILLS/$name" ]; then
    ln -sf "$skill" "$PROJECT_SKILLS/$name"
    echo "  linked: $name"
  else
    echo "  skipped (exists): $name"
  fi
done

# Add to .gitignore
if [ -f ".gitignore" ]; then
  if ! grep -q "^.claude/skills/$" .gitignore; then
    echo ".claude/skills/" >> .gitignore
    echo "!.claude/skills/.gitkeep" >> .gitignore
    echo ".gitignore updated"
  fi
fi

echo "Done."
