#!/bin/bash
# setup-umbrella.sh
# Initializes the top-level .ai/ knowledge base for a multi-repo project.
# Run from the umbrella root — the parent directory that contains all service repos.
# Safe to re-run — never overwrites existing content.
# Usage: bash ~/Documents/projects/alterra/agentic_workflows/setup-umbrella.sh
set -e

WORKFLOWS_SRC="$HOME/Documents/projects/alterra/agentic_workflows"
PROJECT_DIR="$(pwd)"
TMPL="$WORKFLOWS_SRC/templates/.ai-umbrella"

echo "=== Umbrella setup: $PROJECT_DIR ==="
echo ""

# ── GUARD ──────────────────────────────────────────────────────────────
if [ "$PROJECT_DIR" = "$HOME" ]; then
  echo "ERROR: Do not run from home directory. cd into your project umbrella root first."
  exit 1
fi

if [ ! -d "$TMPL" ]; then
  echo "ERROR: $TMPL not found. Is agentic_workflows up to date?"
  exit 1
fi

# ── STEP 1: .ai/ knowledge base ────────────────────────────────────────
echo "[1/3] .ai/ umbrella knowledge base"
mkdir -p .ai/memory .ai/principles .ai/context .ai/adr .ai/specs .ai/tasks/todo .ai/tasks/completed

while IFS= read -r -d '' src; do
  rel="${src#$TMPL/}"
  dst=".ai/$rel"
  if [ ! -e "$dst" ]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  created: $dst"
  else
    echo "  ok: $dst already present"
  fi
done < <(find "$TMPL" -type f -print0)

# ── STEP 2: CLAUDE.md ──────────────────────────────────────────────────
echo "[2/3] CLAUDE.md"
if [ ! -f "CLAUDE.md" ]; then
  cat > CLAUDE.md << 'EOF'
# Project Claude Rules — Umbrella

## Role
This is the umbrella root for a multi-repository project.
Open individual service repositories for implementation work.

## Context Loading Protocol

At the start of every session, read in this order:
1. `.ai/memory/architecture.md`  — system topology: all services and their relationships
2. `.ai/memory/state.md`         — cross-service tasks in flight
3. `.ai/principles/`             — shared principles (architecture, coding, domain)
4. `.ai/adr/index.md`            — cross-cutting decisions

On demand (load only when relevant):
- `.ai/context/integrations.md` — external systems shared across services
- `.ai/context/environment.md`  — shared environments (GCP project IDs, staging, prod)
- `.ai/memory/progress.md`      — history of cross-service milestones

After every cross-service task, update:
- `.ai/memory/state.md`         — task status
- `.ai/memory/progress.md`      — append session summary

After every cross-cutting architectural decision, update:
- `.ai/adr/`                    — new ADR file
- `.ai/adr/index.md`            — add one-line entry
- `.ai/memory/architecture.md`  — if system topology changed
EOF
  echo "  created: CLAUDE.md"
else
  echo "  ok: CLAUDE.md already present"
fi

# ── STEP 3: .gitignore ─────────────────────────────────────────────────
echo "[3/3] .gitignore"
if [ ! -f ".gitignore" ]; then
  touch .gitignore
  echo "  created: .gitignore"
fi
GITIGNORE_ENTRIES=(".env")
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
echo "  1. Edit .ai/memory/architecture.md   — describe all services and how they interact"
echo "  2. Edit .ai/principles/coding.md     — shared coding standards (stack defaults)"
echo "  3. Edit .ai/principles/domain.md     — ubiquitous language and domain model"
echo "  4. Edit .ai/context/environment.md   — GCP project IDs, environment URLs, etc."
echo ""
echo "Then for each service repo:"
echo "  cd <service-dir> && bash ~/Documents/projects/alterra/agentic_workflows/setup-new-project.sh"
echo "  (auto-detects ../.ai/ and configures service with two-level context loading)"
