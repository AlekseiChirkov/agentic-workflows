#!/bin/bash
# scripts/setup-all-repos.sh
# Initializes .ai/ context in all service repositories under an umbrella project.
# Safe to re-run — never overwrites existing files. Existing CLAUDE.md files are
# checked for two-level protocol compliance but never modified.
#
# Usage: bash /path/to/orchestrail/scripts/setup-all-repos.sh [--include-non-git]
#
# Run from the umbrella root (the directory that contains all service repos).
# The umbrella's own .ai/ must already exist (run scripts/setup-umbrella.sh first if not).
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_SRC="${ORCHESTRAIL_HOME:-$SCRIPT_DIR/..}"
WORKFLOWS_SRC="$(cd -- "$WORKFLOWS_SRC" 2>/dev/null && pwd)" || {
  echo "ERROR: source directory not found: ${ORCHESTRAIL_HOME:-$SCRIPT_DIR/..}" >&2
  exit 1
}
export ORCHESTRAIL_HOME="$WORKFLOWS_SRC"
UMBRELLA_DIR="$(pwd)"
INCLUDE_NON_GIT=false

# ── FLAGS ──────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --include-non-git) INCLUDE_NON_GIT=true ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# ── COLORS ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; }

# ── GUARD ──────────────────────────────────────────────────────────────
if [ "$UMBRELLA_DIR" = "$HOME" ]; then
  echo "ERROR: Do not run from home directory. cd into the umbrella root first."
  exit 1
fi

if [ ! -f "$WORKFLOWS_SRC/scripts/setup-new-project.sh" ]; then
  echo "ERROR: $WORKFLOWS_SRC/scripts/setup-new-project.sh not found."
  exit 1
fi

echo "=== setup-all-repos: $UMBRELLA_DIR ==="
echo ""

# ── STEP 1: Umbrella .ai/ check ────────────────────────────────────────
echo "[1/3] Checking umbrella .ai/"
if [ ! -d ".ai" ]; then
  warn "Umbrella .ai/ not found — running scripts/setup-umbrella.sh first"
  bash "$WORKFLOWS_SRC/scripts/setup-umbrella.sh"
elif [ ! -f ".ai/README.md" ]; then
  warn ".ai/ exists but README.md is missing — adding it"
  cp "$WORKFLOWS_SRC/templates/.ai-umbrella/README.md" ".ai/README.md"
  ok ".ai/README.md created (required for service detection)"
else
  ok "Umbrella .ai/ is present with README.md"
fi
echo ""

# ── STEP 2: Discover service directories ──────────────────────────────
echo "[2/3] Discovering service directories"

declare -a GIT_REPOS=()
declare -a NON_GIT_DIRS=()
declare -a SKIPPED=()

for dir in */; do
  dir="${dir%/}"
  [ -d "$dir" ] || continue
  # Skip hidden directories
  [[ "$dir" == .* ]] && continue

  if [ -d "$dir/.git" ]; then
    GIT_REPOS+=("$dir")
    ok "git repo: $dir"
  else
    NON_GIT_DIRS+=("$dir")
    if $INCLUDE_NON_GIT; then
      warn "non-git dir (will include): $dir"
    else
      echo "      non-git dir (skipped): $dir  [use --include-non-git to include]"
      SKIPPED+=("$dir")
    fi
  fi
done

echo ""
echo "  Found ${#GIT_REPOS[@]} git repos, ${#NON_GIT_DIRS[@]} non-git dirs"
echo ""

# ── STEP 3: Run scripts/setup-new-project.sh in each ─────────────────────────
echo "[3/3] Initializing service directories"
echo ""

declare -a REPORT_OK=()
declare -a REPORT_WARN=()
declare -a REPORT_ERR=()

run_setup() {
  local dir="$1"
  echo "──────────────────────────────────────"
  echo "  → $dir"
  echo "──────────────────────────────────────"

  # `set -e` is in force: a bare failing command would abort the whole script before the
  # error branch below could run, so the failure must be captured by the `if` itself.
  if ! (cd "$dir" && bash "$WORKFLOWS_SRC/scripts/setup-new-project.sh"); then
    fail "$dir: scripts/setup-new-project.sh exited non-zero"
    REPORT_ERR+=("$dir")
    return
  fi

  # Post-check: verify CLAUDE.md has two-level protocol
  if [ -f "$dir/CLAUDE.md" ]; then
    if grep -q '\.\.\/\.ai\/' "$dir/CLAUDE.md"; then
      ok "$dir/CLAUDE.md has two-level protocol"
      REPORT_OK+=("$dir")
    else
      warn "$dir/CLAUDE.md EXISTS but does NOT reference ../.ai/ — was it created before the umbrella?"
      warn "   Not modified. Review manually and add the two-level Context Loading Protocol."
      REPORT_WARN+=("$dir (CLAUDE.md missing two-level protocol)")
    fi
  else
    fail "$dir/CLAUDE.md was not created — check setup output above"
    REPORT_ERR+=("$dir")
  fi

  echo ""
}

for dir in "${GIT_REPOS[@]}"; do
  run_setup "$dir"
done

if $INCLUDE_NON_GIT; then
  for dir in "${NON_GIT_DIRS[@]}"; do
    run_setup "$dir"
  done
fi

# ── SUMMARY ───────────────────────────────────────────────────────────
echo "══════════════════════════════════════"
echo "  SUMMARY"
echo "══════════════════════════════════════"
echo ""

if [ ${#REPORT_OK[@]} -gt 0 ]; then
  echo -e "${GREEN}OK (fully initialized):${RESET}"
  for r in "${REPORT_OK[@]}"; do echo "  ✓ $r"; done
  echo ""
fi

if [ ${#REPORT_WARN[@]} -gt 0 ]; then
  echo -e "${YELLOW}WARNINGS (manual review needed):${RESET}"
  for r in "${REPORT_WARN[@]}"; do echo "  ⚠  $r"; done
  echo ""
  echo "  These repos had .ai/ initialized but their CLAUDE.md was already"
  echo "  present and was NOT modified. Add two-level Context Loading Protocol"
  echo "  manually, or replace CLAUDE.md with the template below:"
  echo ""
  cat << 'TMPL'
  ┌─ CLAUDE.md template (two-level protocol) ────────────────────────────
  │ # Project Claude Rules
  │
  │ ## Context Loading Protocol
  │
  │ At the start of every session, read in this order:
  │ 1. `../.ai/memory/architecture.md`  — system topology
  │ 2. `.ai/memory/architecture.md`     — this service's architecture
  │ 3. `.ai/memory/state.md`            — active tasks in this service
  │ 4. `../.ai/principles/`             — shared principles
  │ 5. `.ai/principles/`                — local overrides (if any)
  │ 6. `.ai/adr/index.md`               — decisions for this service
  │
  │ On demand:
  │ - `.ai/context/runbook.md`           — how to run/test/deploy
  │ - `.ai/context/integrations.md`      — this service's integrations
  │ - `../.ai/context/integrations.md`   — shared external systems
  │ - `../.ai/context/environment.md`    — shared environments
  │ - `.ai/memory/progress.md`           — previous sessions
  │
  │ After every task, update:
  │ - `.ai/memory/state.md`
  │ - `.ai/memory/progress.md`
  │
  │ After every architectural decision:
  │ - `.ai/adr/` + `.ai/adr/index.md`
  └───────────────────────────────────────────────────────────────────────
TMPL
  echo ""
fi

if [ ${#REPORT_ERR[@]} -gt 0 ]; then
  echo -e "${RED}ERRORS:${RESET}"
  for r in "${REPORT_ERR[@]}"; do echo "  ✗ $r"; done
  echo ""
fi

if [ ${#SKIPPED[@]} -gt 0 ]; then
  echo "Skipped (non-git, use --include-non-git to include):"
  for r in "${SKIPPED[@]}"; do echo "  - $r"; done
  echo ""
fi

echo "Next steps:"
echo "  1. Fill in ../.ai/memory/architecture.md  — describe all services"
echo "  2. Fill in ../.ai/principles/domain.md    — ubiquitous language"
echo "  3. For each service: fill .ai/context/runbook.md with run/test commands"
echo "  4. For WARN repos above: add two-level Context Loading Protocol to CLAUDE.md"
