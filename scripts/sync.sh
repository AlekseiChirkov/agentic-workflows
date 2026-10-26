#!/bin/bash
set -e

# Source tree to deploy from. Defaults to the repository root (the parent of scripts/).
# ORCHESTRAIL_HOME overrides the default; --from <dir> takes precedence over the environment.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ORCHESTRAIL_HOME:-$SCRIPT_DIR/..}"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --from)
      ROOT="${2:-}"
      [ -n "$ROOT" ] || { echo "ERROR: --from needs a directory"; exit 1; }
      shift 2 ;;
    --from=*)
      ROOT="${1#--from=}"; shift ;;
    -h|--help)
      echo "Usage: scripts/sync.sh [--from <source-tree>]"
      echo "  --from <dir>  deploy from <dir> instead of the repository root (or ORCHESTRAIL_HOME)"
      exit 0 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

SELECTED_ROOT="$ROOT"
ROOT="$(cd -- "$SELECTED_ROOT" 2>/dev/null && pwd)" || {
  echo "ERROR: source directory not found: $SELECTED_ROOT" >&2
  exit 1
}

for d in workflows rules principles templates scripts; do
  [ -d "$ROOT/$d" ] || { echo "ERROR: $ROOT is not an Orchestrail checkout (missing $d/)"; exit 1; }
done

SRC="$ROOT/workflows"
RULES="$ROOT/rules"
PRINCIPLES="$ROOT/principles"

# ── 0. Pre-flight contract validation ────────────────────────────────
echo "[0/5] Contract validation"
bash "$ROOT/scripts/validate-contracts.sh" || {
  echo "ERROR: Contract validation failed. Fix errors before syncing."
  exit 1
}
echo ""

echo "=== Syncing Orchestrail ==="
echo ""

# Hook installation is independent of the remaining deployment targets.
HOOK_INSTALL_RESULT='{"reason":"installer-unavailable","status":"unavailable"}'
if [ -f "$ROOT/scripts/install-hooks.sh" ]; then
  HOOK_INSTALL_RESULT="$(bash "$ROOT/scripts/install-hooks.sh" install --from "$ROOT")" || \
    HOOK_INSTALL_RESULT='{"reason":"installer-failed","status":"unavailable"}'
fi

append_logging_capabilities() {
  local target="$1" harness="$2" result="$3"
  printf '\n<!-- Logging capabilities -->\n' >> "$target"
  if [ -f "$ROOT/harness/$harness/capabilities.md" ]; then
    cat "$ROOT/harness/$harness/capabilities.md" >> "$target"
  else
    printf '%s\n' 'hooks: unknown' 'Unknown capability is unavailable; use note: approximate.' >> "$target"
  fi
  printf '\n## Current hook installation\n\ninstallation-result: %s\n' "$result" >> "$target"
}

# ── 1. Devin Desktop / Windsurf: global workflows (path unchanged) ──
echo "[1/5] Devin Desktop / Windsurf global workflows"
mkdir -p ~/.codeium/windsurf/global_workflows
cp "$SRC"/*.md ~/.codeium/windsurf/global_workflows/
echo "  $(ls "$SRC"/*.md | wc -l) workflows → ~/.codeium/windsurf/global_workflows/"

# ── 2. Devin Desktop / Windsurf: global rules (path unchanged) ──
echo "[2/5] Devin Desktop / Windsurf global rules"
mkdir -p ~/.codeium/windsurf/global_rules
for rule in "$RULES"/*.md; do
  name=$(basename "$rule")
  cp "$rule" ~/.codeium/windsurf/global_rules/"$name"
  echo "  copied: $name"
done
for principle in "$PRINCIPLES"/*.md; do
  name=$(basename "$principle")
  cp "$principle" ~/.codeium/windsurf/global_rules/"$name"
  echo "  copied (principle): $name"
done

# ── 3. Claude Code: global skills ─────────────────────────────────────
echo "[3/5] Claude Code global skills"
for file in "$SRC"/*.md; do
  name=$(basename "$file" .md)
  mkdir -p ~/.claude/skills/$name
  cp "$file" ~/.claude/skills/$name/SKILL.md
done
echo "  $(ls ~/.claude/skills/ | wc -l) skills → ~/.claude/skills/"

# Global CLAUDE.md — principles + standards for Claude Code
GLOBAL_CLAUDE="$HOME/.claude/CLAUDE.md"
cp "$RULES/global-claude.md" "$GLOBAL_CLAUDE"
append_logging_capabilities "$GLOBAL_CLAUDE" claude "$HOOK_INSTALL_RESULT"
echo "  updated: ~/.claude/CLAUDE.md"

# ── 3b. Claude Code: principles as skills ─────────────────────────────
echo "[3b/5] Claude Code: principles as skills"
for file in "$PRINCIPLES"/*.md; do
  name=$(basename "$file" .md)
  skill_name="principle-${name}"
  mkdir -p ~/.claude/skills/$skill_name
  cp "$file" ~/.claude/skills/$skill_name/SKILL.md
  echo "  deployed: $skill_name"
done
echo "  $(ls "$PRINCIPLES"/*.md | wc -l | tr -d ' ') principles → ~/.claude/skills/principle-*/"

# ── 3c. Claude Code: rules as skills ──────────────────────────────────
# Rules are contracts every workflow cites ("load the `tdd` rule", "follow
# `phase-atomic-execution` rules"). Claude Code has no rules directory, so each rule is
# deployed as a skill. The `rule-` prefix is a correctness requirement, not a style choice:
# five basenames (phase-discovery, phase-execution, phase-validation,
# phase-atomic-execution, phase-atomic-validation) exist in BOTH workflows/ and rules/, and
# deploying rules under their bare names would overwrite those workflow skills.
echo "[3c/5] Claude Code: rules as skills"
for file in "$RULES"/*.md; do
  name=$(basename "$file" .md)
  skill_name="rule-${name}"
  mkdir -p ~/.claude/skills/$skill_name
  cp "$file" ~/.claude/skills/$skill_name/SKILL.md
  echo "  deployed: $skill_name"
done
echo "  $(ls "$RULES"/*.md | wc -l | tr -d ' ') rules → ~/.claude/skills/rule-*/"

# ── 4. Codex: global skills ───────────────────────────────────────────
echo "[4/5] Codex global skills"
mkdir -p ~/.codex/skills
for file in "$SRC"/*.md; do
  name=$(basename "$file" .md)
  mkdir -p ~/.codex/skills/$name
  cp "$file" ~/.codex/skills/$name/SKILL.md
done
echo "  $(ls ~/.codex/skills/ | grep -v '^\.' | wc -l) skills → ~/.codex/skills/"

# ── 4b. Codex: principles as skills ───────────────────────────────────
echo "[4b/5] Codex: principles as skills"
for file in "$PRINCIPLES"/*.md; do
  name=$(basename "$file" .md)
  skill_name="principle-${name}"
  mkdir -p ~/.codex/skills/$skill_name
  cp "$file" ~/.codex/skills/$skill_name/SKILL.md
  echo "  deployed: $skill_name"
done
echo "  $(ls "$PRINCIPLES"/*.md | wc -l | tr -d ' ') principles → ~/.codex/skills/principle-*/"

# ── 4c. Codex: global AGENTS.md (always-on rules, incl. language) ─────
echo "[4c/5] Codex global AGENTS.md"
if [ -f "$ROOT/templates/codex-global-AGENTS.md" ]; then
  mkdir -p ~/.codex
  cp "$ROOT/templates/codex-global-AGENTS.md" ~/.codex/AGENTS.md
  append_logging_capabilities "$HOME/.codex/AGENTS.md" codex '{"reason":"no-native-adapter","status":"unavailable"}'
  echo "  updated: ~/.codex/AGENTS.md"
else
  echo "  WARNING: templates/codex-global-AGENTS.md not found — global AGENTS.md not deployed"
fi

# ── 4d. Codex: rules as skills ────────────────────────────────────────
# Same reasoning as step 3c, including the mandatory `rule-` prefix.
echo "[4d/5] Codex: rules as skills"
for file in "$RULES"/*.md; do
  name=$(basename "$file" .md)
  skill_name="rule-${name}"
  mkdir -p ~/.codex/skills/$skill_name
  cp "$file" ~/.codex/skills/$skill_name/SKILL.md
  echo "  deployed: $skill_name"
done
echo "  $(ls "$RULES"/*.md | wc -l | tr -d ' ') rules → ~/.codex/skills/rule-*/"

# ── 5. Codex: principles summary in Orchestrail ──────────────────────
# Codex reads AGENTS.md per project — scripts/setup-new-project.sh handles that.
# Here we just confirm the template is current.
echo "[5/5] Codex"
if [ -f "$ROOT/templates/AGENTS.md" ]; then
  echo "  AGENTS.md template present → scripts/setup-new-project.sh will deploy per project"
else
  echo "  WARNING: templates/AGENTS.md not found — Codex template missing"
fi

# ── .ai/ knowledge-base template ─────────────────────────────────────
if [ -d "$ROOT/templates/.ai" ]; then
  echo "  .ai/ template present → scripts/setup-new-project.sh will deploy per project"
else
  echo "  WARNING: templates/.ai not found — knowledge-base template missing"
fi

# ── 5b. Per-project sync ─────────────────────────────────────────────
echo "[5b/5] Per-project sync (rules, skills symlinks, workflow cleanup)"
PROJECTS_UPDATED=0

while IFS= read -r -d '' devin_dir; do

  project_dir="$(dirname "$devin_dir")"
  # Never treat the script directory or selected source tree as a target project.
  [ "$project_dir" = "$ROOT" ] && continue
  [ "$project_dir" = "$SCRIPT_DIR" ] && continue

  echo "  project: $project_dir"

  # 1. Update .devin/rules/
  mkdir -p "$devin_dir/rules"
  for rule in workflow-globals.md workflow-reference.md language.md quick-flow.md tdd.md run-log.md git-flow.md orchestration.md \
              phase-discovery.md phase-execution.md phase-validation.md \
              phase-atomic-execution.md phase-atomic-validation.md; do
    src="$ROOT/rules/$rule"
    [ -f "$src" ] && cp "$src" "$devin_dir/rules/$rule"
  done

  # 2. Update .windsurf/rules/ if it exists
  windsurf_rules="$project_dir/.windsurf/rules"
  if [ -d "$windsurf_rules" ]; then
    for rule in workflow-globals.md workflow-reference.md language.md quick-flow.md tdd.md run-log.md git-flow.md orchestration.md \
                phase-discovery.md phase-execution.md phase-validation.md \
                phase-atomic-execution.md phase-atomic-validation.md; do
      src="$ROOT/rules/$rule"
      [ -f "$src" ] && cp "$src" "$windsurf_rules/$rule"
    done
  fi

  # 3. Refresh .claude/skills/ symlinks if directory exists
  claude_skills="$project_dir/.claude/skills"
  if [ -d "$claude_skills" ]; then
    # Remove broken symlinks
    while IFS= read -r -d '' link; do
      [ -e "$link" ] || { rm "$link"; echo "    removed stale symlink: $(basename "$link")"; }
    done < <(find "$claude_skills" -maxdepth 1 -type l -print0)
    # Add symlinks for any new skills
    for skill in "$HOME/.claude/skills"/*/; do
      name=$(basename "$skill")
      target="$claude_skills/$name"
      [ ! -e "$target" ] && ln -sf "$skill" "$target"
    done
  fi

  # 4. Remove local workflow files that duplicate global ones.
  #    Project-specific workflows (names not in orchestrail/) are preserved.
  for wf_dir in "$devin_dir/workflows" "$project_dir/.windsurf/workflows"; do
    if [ -d "$wf_dir" ]; then
      removed=0
      kept=0
      for local_wf in "$wf_dir"/*.md; do
        [ -f "$local_wf" ] || continue
        name=$(basename "$local_wf")
        if [ -f "$ROOT/workflows/$name" ]; then
          rm "$local_wf"
          removed=$((removed + 1))
        else
          kept=$((kept + 1))
        fi
      done
      # Remove directory only if now empty
      if [ "$(ls -A "$wf_dir" 2>/dev/null)" = "" ]; then
        rmdir "$wf_dir"
        echo "    removed (empty): $wf_dir"
      else
        echo "    workflows: removed $removed global copies, kept $kept project-specific"
      fi
    fi
  done

  # 5. Preserve tracked knowledge; ignore untracked consumer state by default.
  if [ -d "$project_dir/.git" ]; then
    gi="$project_dir/.gitignore"
    if [ -n "$(git -C "$project_dir" ls-files .ai 2>/dev/null | head -1)" ]; then
      echo "    .ai/: preserving repository-owned tracking policy"
    elif ! grep -qE '^\.ai/?$' "$gi" 2>/dev/null; then
      echo ".ai/" >> "$gi"
      echo "    .gitignore: added .ai/"
    fi
  fi

  PROJECTS_UPDATED=$((PROJECTS_UPDATED + 1))
done < <(find "$HOME" -maxdepth 6 -type d -name ".devin" \
    -not -path "*/Trash/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" -print0 2>/dev/null)

echo "  $PROJECTS_UPDATED projects updated"

# ── Summary ───────────────────────────────────────────────────────────
echo ""
echo "=== Sync complete ==="
echo ""
echo "Deployed to:"
echo "  Windsurf workflows: ~/.codeium/windsurf/global_workflows/"
echo "  Windsurf rules:     ~/.codeium/windsurf/global_rules/"
echo "  Claude Code skills: ~/.claude/skills/"
echo "  Claude Code global: ~/.claude/CLAUDE.md"
echo "  Codex skills:       ~/.codex/skills/"
echo "  Codex global:       ~/.codex/AGENTS.md (always-on rules, incl. language)"
echo "  Codex template:     $ROOT/templates/AGENTS.md (deployed per project)"
echo "  Claude principles: ~/.claude/skills/principle-*/"
echo "  Codex principles:  ~/.codex/skills/principle-*/"
echo "  Claude rules:      ~/.claude/skills/rule-*/"
echo "  Codex rules:       ~/.codex/skills/rule-*/"
echo "  Per-project:    rules (.devin/rules/ + .windsurf/rules/), skills symlinks refresh, local workflow cleanup"
