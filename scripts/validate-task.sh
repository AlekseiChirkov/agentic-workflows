#!/bin/bash
# scripts/validate-task.sh
# Validates the artifacts of ONE task directory against the canonical contracts.
#
# scripts/validate-contracts.sh checks that the workflow definitions agree with each other.
# This script checks that a task the workflows produced actually conforms — the same
# contracts, applied to the output rather than to the instructions.
#
# Usage: scripts/validate-task.sh <task-directory> [--phase discovery|execution|validation]
#        --phase narrows the checks to those meaningful at that point; without it,
#        every check runs and phase-inappropriate ones report as [SKIP].
#
# Exit 0 = no failures. Exit 1 = failures found. Exit 2 = bad invocation.

set -uo pipefail

TASK="${1:-}"
PHASE=""
shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --phase) PHASE="${2-}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$TASK" ]; then
  echo "Usage: scripts/validate-task.sh <task-directory> [--phase discovery|execution|validation]" >&2
  exit 2
fi
TASK="${TASK%/}"
[ -d "$TASK" ] || { echo "Not a directory: $TASK" >&2; exit 2; }

STATE="$TASK/state.md"
PLAN="$TASK/plan.md"

PASS=0; FAIL=0; SKIP=0

check() { # check <desc> <result>   result "pass" or a failure message
  if [ "$2" = "pass" ]; then echo "[PASS] $1"; PASS=$((PASS+1))
  else echo "[FAIL] $1: $2"; FAIL=$((FAIL+1)); fi
}
skip() { echo "[SKIP] $1 — $2"; SKIP=$((SKIP+1)); }

phase_at_least() { # phase_at_least <phase>
  case "$PHASE" in
    "") return 0 ;;
    discovery) [ "$1" = "discovery" ] ;;
    execution) [ "$1" = "discovery" ] || [ "$1" = "execution" ] ;;
    validation) return 0 ;;
    *) return 0 ;;
  esac
}

echo "=== Task contract validation: $TASK ==="
echo ""

# ── Group 1: state.md exists and carries the top-of-file fields ──────
if [ ! -f "$STATE" ]; then
  check "state.md exists" "no state.md in $TASK — every workflow reads it first"
  echo ""; echo "  Passed: $PASS  Failed: $FAIL  Skipped: $SKIP"; exit 1
fi
check "state.md exists" pass

check "state.md carries spec_path:" \
  "$(grep -qE '^spec_path: *[^ ]' "$STATE" && echo pass \
     || { [ -f "$TASK/description.md" ] && echo pass \
          || echo 'no spec_path: and no legacy description.md — the task statement cannot be resolved'; })"

check "state.md carries a flow: tier" \
  "$(grep -qE '^flow: *(quick|full)$' "$STATE" && echo pass \
     || echo 'flow: is missing or is not exactly quick|full — pd-analyze sets it and quick-flow depends on it')"

check "state.md has the ## Phases block with all three phases" \
  "$(awk '/^## Phases/{f=1} f&&/^- discovery:/{d=1} f&&/^- execution:/{e=1} f&&/^- validation:/{v=1} END{exit !(d&&e&&v)}' "$STATE" && echo pass \
     || echo 'the ## Phases block must list discovery, execution and validation')"

BAD_PHASE="$(awk '/^## Phases/{f=1;next} f&&/^- (discovery|execution|validation):/{ if ($0 !~ /: *(not-started|in-progress|complete)$/) print $0 } f&&/^## /&&!/^## Phases/{f=0}' "$STATE")"
check "phase statuses use the canonical vocabulary" \
  "$([ -z "$BAD_PHASE" ] && echo pass || echo "not-started|in-progress|complete expected, found: $(echo "$BAD_PHASE" | tr '\n' ';')")"

FLOW="$(sed -n 's/^flow: *//p' "$STATE" | head -1)"

# ── Group 2: quick tier keeps its inline contract ────────────────────
if [ "$FLOW" = "quick" ]; then
  check "quick tier has ## Contract (quick)" \
    "$(grep -q '^## Contract (quick)' "$STATE" && echo pass \
       || echo 'flow: quick requires an inline ## Contract (quick) in state.md — quick-flow removes decomposition, never the contract')"
  for sec in '### Off-limits' '### Invariants' '### Acceptance Criteria'; do
    check "quick contract has $sec" \
      "$(grep -qF "$sec" "$STATE" && echo pass || echo "missing $sec from ## Contract (quick)")"
  done
  check "quick tier did not create T-XX subtasks" \
    "$(ls -d "$TASK"/T-* >/dev/null 2>&1 && echo 'T-XX directories exist under a flow: quick task — either the tier is wrong or the task was promoted without updating flow:' || echo pass)"
fi

if [ "$FLOW" != "quick" ] && [ "$FLOW" != "full" ]; then
  skip "tier-specific artifact checks" "flow: is not a recognised tier, so neither the quick contract nor the full decomposition can be checked"
fi

# ── Group 3: full tier decomposition artifacts ───────────────────────
if [ "$FLOW" = "full" ] && phase_at_least execution; then
  if grep -qE '^- discovery: *complete' "$STATE"; then
    check "plan.md exists after discovery" \
      "$([ -f "$PLAN" ] && echo pass || echo 'discovery is complete but there is no plan.md')"
    check "at least one T-XX directory exists" \
      "$(ls -d "$TASK"/T-* >/dev/null 2>&1 && echo pass || echo 'discovery is complete but no T-XX subtask directory exists')"
    check "no state.md or plan.md inside a T-XX directory" \
      "$(find "$TASK" -mindepth 2 -maxdepth 2 \( -name state.md -o -name plan.md \) 2>/dev/null | grep -q . \
         && echo "atomic-level state/plan files found: $(find "$TASK" -mindepth 2 -maxdepth 2 \( -name state.md -o -name plan.md \) | tr '\n' ' ')— all atomic progress lives in the parent state.md" \
         || echo pass)"
  else
    skip "full-tier decomposition artifacts" "discovery not complete"
  fi
fi

# ── Group 4: the six-section description.md contract ─────────────────
if ls -d "$TASK"/T-* >/dev/null 2>&1; then
  MISSING=""
  for d in "$TASK"/T-*/; do
    f="$d/description.md"
    if [ ! -f "$f" ]; then MISSING="$MISSING $(basename "$d"):no-file"; continue; fi
    for sec in '## Goal' '## Context' '## Scope' '## Steps' '## Acceptance Criteria' '## Test Plan'; do
      grep -qF "$sec" "$f" || MISSING="$MISSING $(basename "$d"):${sec// /_}"
    done
  done
  check "every T-XX description.md has all six sections" \
    "$([ -z "$MISSING" ] && echo pass || echo "missing:$MISSING")"
else
  skip "description.md six-section contract" "no T-XX directories"
fi

# ── Group 5: ## Subtask Progress block format ────────────────────────
if grep -q '^## Subtask Progress' "$STATE"; then
  BLOCKS="$(grep -cE '^\[composite\] T-|^T-' "$STATE" || true)"
  check "## Subtask Progress contains at least one block" \
    "$([ "${BLOCKS:-0}" -gt 0 ] && echo pass || echo 'the section exists but holds no T-XX block')"

  BAD_TESTS="$(grep -oE 'atomic-tests: *[a-z-]+' "$STATE" | grep -vE 'atomic-tests: *(not-started|red|pinned|green|n-a|failed)$' || true)"
  check "atomic-tests: uses the canonical vocabulary" \
    "$([ -z "$BAD_TESTS" ] && echo pass || echo "not-started|red|green|n-a|failed expected, found: $(echo "$BAD_TESTS" | tr '\n' ';')")"

  BAD_STAT="$(grep -oE 'atomic-(execution|validation): *[a-z-]+' "$STATE" | grep -vE ': *(not-started|in-progress|complete|blocked|skipped|failed)$' || true)"
  check "atomic-execution/validation use the canonical vocabulary" \
    "$([ -z "$BAD_STAT" ] && echo pass || echo "found: $(echo "$BAD_STAT" | tr '\n' ';')")"

  # Required-even-when-empty fields, per workflow-globals.
  LEAVES="$(grep -cE '^T-[0-9]' "$STATE" || true)"
  for field in target_files notes; do
    COUNT="$(grep -cE "^ +$field:" "$STATE" || true)"
    check "every leaf block carries $field: (written even when empty)" \
      "$([ "${COUNT:-0}" -ge "${LEAVES:-0}" ] && echo pass \
         || echo "$COUNT ${field}: lines for $LEAVES leaf blocks — the field is mandatory even when empty")"
  done

  # Composite blocks must declare children and blocker.
  COMPOSITES="$(grep -cE '^\[composite\] T-' "$STATE" || true)"
  if [ "${COMPOSITES:-0}" -gt 0 ]; then
    CH="$(grep -cE '^ +children:' "$STATE" || true)"
    check "every composite block carries children:" \
      "$([ "${CH:-0}" -ge "${COMPOSITES:-0}" ] && echo pass || echo "$CH children: lines for $COMPOSITES composite blocks")"
  fi
else
  if grep -qE '^- execution: *(in-progress|complete)' "$STATE"; then
    check "## Subtask Progress exists once execution started" \
      "execution is under way but state.md has no ## Subtask Progress section"
  else
    skip "## Subtask Progress format" "execution not started"
  fi
fi

# ── Group 6: TDD audit trail ─────────────────────────────────────────
if grep -q 'atomic-execution: *complete' "$STATE"; then
  NA_COUNT="$(grep -c 'atomic-tests: *n-a' "$STATE" || true)"
  TDD_NOTES="$(grep -c 'tdd: none' "$STATE" || true)"
  check "every n-a test level carries its tdd: none justification" \
    "$([ "${TDD_NOTES:-0}" -ge "${NA_COUNT:-0}" ] && echo pass \
       || echo "$NA_COUNT subtasks recorded atomic-tests: n-a but only $TDD_NOTES carry a 'tdd: none — ...' note; an unjustified n-a is a validation finding")"

  NOT_STARTED="$(awk '/^T-[0-9]/{name=$0} /atomic-execution: *complete/{if (name ~ /atomic-tests: *not-started/) print name}' "$STATE" || true)"
  check "no subtask reached atomic-execution: complete with atomic-tests: not-started" \
    "$([ -z "$NOT_STARTED" ] && echo pass || echo "implementation completed without the RED step: $NOT_STARTED")"
else
  skip "TDD audit trail" "no completed atomic execution yet"
fi

# ── Group 7: fix-task bookkeeping ────────────────────────────────────
if grep -q '^## Fix-Tasks' "$STATE"; then
  check "## Fix-Tasks carries fixes-count:" \
    "$(grep -qE '^fixes-count: *[0-9]+' "$STATE" && echo pass || echo 'fixes-count: is missing or not numeric')"
  check "## Fix-Tasks carries a Created: list" \
    "$(grep -qE '^Created: *' "$STATE" && echo pass || echo 'Created: is missing — write "none" when there are no fix-tasks')"
  check "no progress block lives under ## Fix-Tasks" \
    "$(awk '/^## Fix-Tasks/{f=1;next} /^## /{f=0} f&&/^ +(last_action|target_files|atomic-tests):/{print;exit}' "$STATE" | grep -q . \
       && echo 'a subtask progress block was written under ## Fix-Tasks; fix-task progress belongs in ## Subtask Progress' || echo pass)"
else
  skip "fix-task bookkeeping" "no ## Fix-Tasks section"
fi

# ── Group 8: spec reconciliation ─────────────────────────────────────
if grep -qE '^- validation: *complete' "$STATE"; then
  check "the spec was reconciled after validation" \
    "$(grep -q '^## Spec Sync' "$STATE" && echo pass \
       || echo 'validation is complete but no ## Spec Sync record exists — run /spec-sync so the spec stops describing a system that changed')"
else
  skip "spec reconciliation" "validation not complete"
fi

# ── Group 9: language ────────────────────────────────────────────────
CYRILLIC="$(grep -rlP '[\x{0400}-\x{04FF}]' "$TASK" 2>/dev/null || true)"
check "task artifacts are written in English" \
  "$([ -z "$CYRILLIC" ] && echo pass \
     || echo "non-English text found in: $(printf '%s' "$CYRILLIC" | tr '\n' ' ')— project files are English-only regardless of chat language")"

echo ""
echo "=== Task Validation ==="
echo "  Passed:  $PASS"
echo "  Failed:  $FAIL"
echo "  Skipped: $SKIP"
echo ""
if [ $FAIL -gt 0 ]; then
  echo "The task's artifacts do not conform. Fix before advancing the phase."
  exit 1
fi
echo "Task artifacts conform to the canonical contracts."
exit 0
