#!/usr/bin/env bash
# Verify the /spec-draft review contract: an independent Devil's Advocate critic,
# a bounded critique loop and a 100-point rubric with a 95-point pass threshold.
# Usage: bash scripts/check-spec-draft.sh [workflow-file]. Exit 0 = pass, 1 = failure.
# Reads one file with shell builtins only, so it runs in milliseconds.
set -uo pipefail

source_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
workflow="${1:-$source_root/workflows/spec-draft.md}"
failures=0

fail() {
  printf '[FAIL] %s\n' "$1"
  failures=$((failures + 1))
}

if [ ! -f "$workflow" ]; then
  printf '[FAIL] workflow file not found: %s\n' "$workflow"
  exit 1
fi
text="$(<"$workflow")"

# Each row: description, then an extended regular expression the workflow must match.
required=(
  "Step 6 is the Devil's Advocate review"
  $'(^|\n)## Step 6 — Devil\'s Advocate review\n'
  "loop bounds name 10 rounds and the 95/100 threshold on one line"
  $'(^|\n)Review loop bounds: at most 10 rounds; pass at score ≥ 95/100 with no open critical or major finding\\.'
  "one critic serves every round and is addressed by message"
  'Spawn one Devil.s Advocate sub-agent for the whole loop and address later rounds to it by message'
  "the critic does not see the conversation"
  'Do not give it the conversation'
  "the critic never edits the specification"
  'It never edits the spec'
  "severity caps make 95 unreachable with open critical or major findings"
  'An open critical finding caps the score at 80; an open major finding caps it at 94\.'
  "minor findings cannot buy a perfect score or a new round"
  'Minor findings together deduct at most 5 points; never start a round for minor findings alone\.'
  "stagnation ends the loop early"
  'stagnation: two consecutive rounds raised no new critical or major finding and the score did not increase'
  "a rejected finding needs a citation and a maintained one is a dispute"
  'reject it with a citation'
  "harnesses without sub-agents use a labelled inline critic"
  'critic: inline'
  "the readiness gate includes the review result"
  $'\n\\| 14 \\| Devil.s Advocate review passed: score ≥ 95/100 with no open critical or major finding \\|'
  "the report states rounds, per-round scores and unresolved findings"
  'review rounds, the score of each round, critic mode and unresolved findings'
)
for ((i = 0; i < ${#required[@]}; i += 2)); do
  [[ "$text" =~ ${required[i + 1]} ]] || fail "${required[i]}"
done

# The self-review it replaces must be gone, or the author would still grade its own work.
[[ "$text" =~ 'Run two passes over the draft' ]] && fail "the former author self-review is removed"

# The rubric has exactly ten numbered criteria whose weights add up to 100.
in_rubric=0
rows=0
total=0
expected=1
while IFS= read -r line; do
  if [[ "$line" == '### Rubric' ]]; then in_rubric=1; continue; fi
  ((in_rubric)) || continue
  [[ "$line" == '#'* ]] && break
  if [[ "$line" =~ ^\|\ ([0-9]+)\ \|[^|]+\|\ ([0-9]+)\ \| ]]; then
    [ "${BASH_REMATCH[1]}" -eq "$expected" ] || fail "rubric row ${BASH_REMATCH[1]} is out of order"
    expected=$((expected + 1))
    rows=$((rows + 1))
    total=$((total + BASH_REMATCH[2]))
  fi
done <<<"$text"
[ "$rows" -eq 10 ] || fail "the rubric has 10 criteria (found $rows)"
[ "$total" -eq 100 ] || fail "the rubric weights add up to 100 (found $total)"

if [ "$failures" -gt 0 ]; then
  printf '%d spec-draft contract failure(s)\n' "$failures"
  exit 1
fi
printf '[PASS] spec-draft review contract\n'
