#!/bin/bash
# setup-new-project.sh
# Sets up workflow infrastructure for a new or existing project.
# Safe to run multiple times — never overwrites existing content.
# Usage: bash /path/to/agentic_workflows/setup-new-project.sh
# Run from the project root directory.
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_SRC="${WORKFLOWS_SOURCE:-$SCRIPT_DIR}"
PROJECT_DIR="$(pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"

echo "=== Project: $PROJECT_DIR ==="
echo ""

# ── GUARD ──────────────────────────────────────────────────────────────
if [ "$PROJECT_DIR" = "$HOME" ]; then
  echo "ERROR: Do not run from home directory. cd into your project first."
  exit 1
fi

# ── UMBRELLA DETECTION ─────────────────────────────────────────────────
PARENT_AI=""
if [ -d "../.ai" ] && [ -f "../.ai/README.md" ]; then
  PARENT_AI="$(cd .. && pwd)/.ai"
  PARENT_REL="../.ai"
  echo "  Detected umbrella .ai/ at: $PARENT_AI"
  echo "  This service will use two-level context loading."
  echo ""
fi

# ── STEP 1: CLAUDE.md ──────────────────────────────────────────────────
echo "[1/7] CLAUDE.md"
if [ ! -f "CLAUDE.md" ]; then
  if [ -n "$PARENT_AI" ]; then
    # Two-level loading: umbrella first, then local overrides
    cat > CLAUDE.md << 'EOF'
# Project Claude Rules

## Context Loading Protocol

At the start of every session, read in this order:
1. `../.ai/memory/architecture.md`  — system topology (all services, how they interact)
2. `.ai/memory/architecture.md`     — this service's internal architecture
3. `.ai/memory/state.md`            — active tasks in this service
4. `../.ai/principles/`             — shared principles (architecture, coding, domain)
5. `.ai/principles/`                — local overrides for this service (if any)
6. `.ai/adr/index.md`               — decisions specific to this service

On demand (load only when relevant to current task):
- `.ai/context/runbook.md`           — how to run, test, and deploy this service
- `.ai/context/integrations.md`      — this service's specific integration details
- `../.ai/context/integrations.md`   — external systems shared across services
- `../.ai/context/environment.md`    — shared environments (GCP project IDs, etc.)
- `.ai/memory/progress.md`           — history of previous sessions

After every completed task, update:
- `.ai/memory/state.md`              — task status
- `.ai/memory/progress.md`           — append session summary (date, what was done, key decisions)

After every architectural decision, update:
- `.ai/adr/`                         — new ADR file
- `.ai/adr/index.md`                 — add one-line entry
EOF
    echo "  created: CLAUDE.md (two-level protocol — umbrella + local)"
  else
    # Standalone project: local .ai/ only
    cat > CLAUDE.md << 'EOF'
# Project Claude Rules
# Project-specific commands and standards live in .ai/
# See .ai/context/runbook.md → ## Commands
# See .ai/principles/coding.md → ## Standards
EOF
    echo "  created: CLAUDE.md (pointer only — commands and standards are in .ai/)"
  fi
else
  echo "  ok: CLAUDE.md already present"
fi

# ── STEP 2: .windsurf/rules/ ───────────────────────────────────────────
echo "[2/7] .windsurf/rules/"
mkdir -p .windsurf/rules

for rule in workflow-globals.md workflow-reference.md language.md quick-flow.md tdd.md run-log.md git-flow.md orchestration.md \
            phase-discovery.md phase-execution.md phase-validation.md \
            phase-atomic-execution.md phase-atomic-validation.md; do
  if [ ! -f ".windsurf/rules/$rule" ]; then
    if [ -f "$WORKFLOWS_SRC/rules/$rule" ]; then
      cp "$WORKFLOWS_SRC/rules/$rule" ".windsurf/rules/$rule"
      echo "  copied: .windsurf/rules/$rule"
    else
      echo "  WARNING: $WORKFLOWS_SRC/rules/$rule not found — skipped"
    fi
  else
    echo "  ok: .windsurf/rules/$rule already present"
  fi
done

if [ ! -f ".windsurf/rules/language.md" ]; then
  cat > .windsurf/rules/language.md << 'EOF'
---
trigger: always_on
---
# Language Rule (always-on)
Before creating or modifying ANY file or text artifact, apply this rule first.
All content written to project files must be in English — source code, comments,
docstrings, commit messages, config, shell scripts, Terraform/YAML/JSON, Markdown
docs, README/ADR/state files, test names, and any other generated artifact.
This rule applies ONLY to generated code and project files.
# Chat language preference is user-specific.
# Set this in your personal ~/.claude/CLAUDE.md, not here.
EOF
  echo "  created: .windsurf/rules/language.md"
fi

# Devin Desktop: create .devin/rules/ as the preferred location
echo "  [Devin Desktop] creating .devin/rules/"
mkdir -p .devin/rules
for rule in workflow-globals.md workflow-reference.md language.md quick-flow.md tdd.md run-log.md git-flow.md orchestration.md \
            phase-discovery.md phase-execution.md phase-validation.md \
            phase-atomic-execution.md phase-atomic-validation.md; do
  if [ ! -f ".devin/rules/$rule" ]; then
    if [ -f "$WORKFLOWS_SRC/rules/$rule" ]; then
      cp "$WORKFLOWS_SRC/rules/$rule" ".devin/rules/$rule"
      echo "  copied: .devin/rules/$rule"
    fi
  else
    echo "  ok: .devin/rules/$rule already present"
  fi
done

# ── STEP 3: .windsurf/workflows/ ──────────────────────────────────────
echo "[3/7] .windsurf/workflows/ — not created"
echo "  Workflows are global: ~/.codeium/windsurf/global_workflows/"
echo "  Do NOT create local .windsurf/workflows/ or .devin/workflows/ —"
echo "  local copies shadow the global ones and go stale between syncs."

# ── STEP 4: .claude/skills/ symlinks ──────────────────────────────────
echo "[4/7] .claude/skills/ (Claude Code global skills workaround)"
mkdir -p .claude/skills

# Remove broken symlinks first
while IFS= read -r -d '' link; do
  [ -e "$link" ] || { rm "$link"; echo "  removed stale: $(basename "$link")"; }
done < <(find ".claude/skills" -maxdepth 1 -type l -print0)

LINKED=0
SKIPPED=0
for skill in "$CLAUDE_SKILLS"/*/; do
  name=$(basename "$skill")
  target=".claude/skills/$name"
  if [ ! -e "$target" ]; then
    ln -sf "$skill" "$target"
    LINKED=$((LINKED + 1))
  else
    SKIPPED=$((SKIPPED + 1))
  fi
done
echo "  linked: $LINKED skills, skipped (exist): $SKIPPED"

# ── STEP 5a: .ai/ knowledge base ─────────────────────────────────────
echo "[5/7] .ai/ knowledge base"
if [ -d "$WORKFLOWS_SRC/templates/.ai" ]; then
  mkdir -p .ai
  # Copy template files only when missing — never overwrite project content.
  while IFS= read -r -d '' src; do
    rel="${src#$WORKFLOWS_SRC/templates/.ai/}"
    dst=".ai/$rel"
    if [ ! -e "$dst" ]; then
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
      echo "  created: $dst"
    fi
  done < <(find "$WORKFLOWS_SRC/templates/.ai" -type f -print0)
  mkdir -p .ai/tasks/todo .ai/tasks/completed
  mkdir -p .ai/specs
  echo "  ok: .ai/specs/ ready"
  echo "  ok: .ai/ ready (memory/, tasks/, specs/, adr/, principles/, context/)"
else
  echo "  WARNING: $WORKFLOWS_SRC/templates/.ai not found — skipped"
fi

# ── STEP 5: AGENTS.md (Codex) ─────────────────────────────────────────
echo "[6/7] AGENTS.md (Codex)"
if [ ! -f "AGENTS.md" ]; then
  if [ -f "$WORKFLOWS_SRC/templates/AGENTS.md" ]; then
    cp "$WORKFLOWS_SRC/templates/AGENTS.md" AGENTS.md
    echo "  created: AGENTS.md from template"

    # Stack overlay selection
    echo ""
    echo "  Select stack overlay (or press Enter to skip):"
    echo "    1) python-fastapi"
    echo "    2) none (fill ## Standards manually)"
    printf "  Choice [1/2, default=2]: "
    read -r stack_choice

    case "$stack_choice" in
      1)
        STACK_FILE="$WORKFLOWS_SRC/templates/stacks/python-fastapi.md"
        if [ -f "$STACK_FILE" ]; then
          # Replace the ## Standards injection comment block with stack content
          python3 - "$STACK_FILE" << 'PYEOF'
import sys, re, pathlib

stack_content = pathlib.Path(sys.argv[1]).read_text()

agents = pathlib.Path("AGENTS.md").read_text()
injection_block = (
    "<!-- Stack standards are injected here by setup-new-project.sh -->\n"
    "<!-- Run setup-new-project.sh to select a stack and populate this section -->\n"
    "<!-- If no stack was selected, define project-specific standards here -->"
)
agents = agents.replace(injection_block, stack_content.strip())
pathlib.Path("AGENTS.md").write_text(agents)
PYEOF
          echo "  Stack overlay applied: python-fastapi"
        else
          echo "  WARNING: $STACK_FILE not found — ## Standards left as injection comment"
        fi
        ;;
      *)
        echo "  No stack overlay applied. Fill ## Standards in AGENTS.md manually."
        ;;
    esac

    echo "  ACTION REQUIRED: fill in ## Project Context section in AGENTS.md"
  else
    echo "  WARNING: templates/AGENTS.md not found — skipped"
  fi
else
  echo "  ok: AGENTS.md already present"
fi

# ── STEP 6: .gitignore ────────────────────────────────────────────────
echo "[7/7] .gitignore"
if [ ! -f ".gitignore" ]; then
  touch .gitignore
  echo "  created: .gitignore"
fi

GITIGNORE_ENTRIES=(
  ".ai/"
  ".claude/skills/"
  "!.claude/skills/.gitkeep"
  ".env"
  "*.pyc"
  "__pycache__/"
)
for entry in "${GITIGNORE_ENTRIES[@]}"; do
  if ! grep -qF "$entry" .gitignore; then
    echo "$entry" >> .gitignore
    echo "  appended to .gitignore: $entry"
  else
    echo "  ok: $entry already in .gitignore"
  fi
done

# ── SUMMARY ───────────────────────────────────────────────────────────
echo ""
echo "=== Done ==="
echo ""
echo "Next steps:"
echo "  1. Edit .ai/context/runbook.md → ## Commands with your project's test/lint commands"
echo "  2. Edit .ai/principles/coding.md → ## Standards with project-specific overrides (optional)"
echo "  3. Edit AGENTS.md → ## Project Context with project description and stack"
echo "  4. Edit AGENTS.md → ## Commands with actual test/lint commands"
echo "  5. In Windsurf: verify global workflows load with /phase-discovery"
echo "  6. In Claude Code: verify skills load with /phase-discovery"
echo "  7. In Codex: AGENTS.md will be read automatically"
