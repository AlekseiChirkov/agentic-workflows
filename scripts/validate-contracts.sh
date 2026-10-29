#!/bin/bash
# scripts/validate-contracts.sh
# Validates consistency of workflow contracts in Orchestrail.
# Run with bash /path/to/orchestrail/scripts/validate-contracts.sh.
# Exit 0 = all pass. Exit 1 = failures found.

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

if [ "${1:-}" = --usage-contract-export-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-contract-export.py" "$@"
fi

if [ "${1:-}" = --usage-current-snapshot-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-current-run-snapshot-schema.py" "$@"
fi

# Check publication receipt schemas with offline fixtures.
if [ "${1:-}" = --usage-projection-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-lifecycle-projection-schema.py" "$@"
fi

if [ "${1:-}" = --usage-receipt-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-usage-receipt-schema.py" "$@"
fi

# Check explicit analysis corpus manifests with offline fixtures.
if [ "${1:-}" = --usage-analysis-corpus-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-analysis-corpus-schema.py" "$@"
fi

# Check warning policy schemas with offline fixtures.
if [ "${1:-}" = --usage-warning-policy-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-warning-policy-schema.py" "$@"
fi

# Check named pricing scenarios with offline fixtures.
if [ "${1:-}" = --usage-pricing-scenario-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-pricing-scenario-schema.py" "$@"
fi

# Check immutable price snapshot schemas with offline fixtures.
if [ "${1:-}" = --usage-price-snapshot-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-price-snapshot-schema.py" "$@"
fi

# Check registered diagnostic measurement schemas with offline fixtures.
if [ "${1:-}" = --usage-diagnostic-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-diagnostic-schema.py" "$@"
fi

# Check collection segment schemas with offline fixtures.
if [ "${1:-}" = --usage-segment-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-collection-segment-schema.py" "$@"
fi

# Check bounded attribution metadata.
if [ "${1:-}" = --usage-attribution-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-attribution-schema.py" "$@"
fi

# Check independent inventory declarations.
if [ "${1:-}" = --usage-inventory-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-inventory-schema.py" "$@"
fi

# Check explicit source selection schemas.
if [ "${1:-}" = --usage-selection-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-source-selection.py" "$@"
fi

# Check synthetic source-profile schemas.
if [ "${1:-}" = --usage-entity-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-entity-schemas.py" "$@"
fi

# Check sanitized observation and bundle schemas.
if [ "${1:-}" = --usage-envelope-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-observation-bundle-schema.py" "$@"
fi

# Check typed usage schema with isolated offline fixtures.
if [ "${1:-}" = --usage-schema-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-typed-schema.py" "$@"
fi

# Check canonical usage encoding with isolated offline fixtures.
if [ "${1:-}" = --usage-canonical-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/usage-canonical-encoding.py" "$@"
fi

# Run every cached-selection contract with fictional isolated inputs and no providers.
if [ "${1:-}" = --model-workflow-only ]; then
  shift
  model_workflow_status=0
  for model_suite in model-catalog.py model-selection.py model-plan.py model-workflow.py; do
    python3 "$REPO_ROOT/tests/$model_suite" "$@" || model_workflow_status=1
  done
  python3 "$REPO_ROOT/tests/workflow-instructions.py" || model_workflow_status=1
  exit "$model_workflow_status"
fi

# Check compatible plan columns and visible resolution with isolated offline fixtures.
if [ "${1:-}" = --model-plan-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/model-plan.py" "$@"
fi

# Exercise conservative selection using fictional capability and cost evidence.
if [ "${1:-}" = --model-selection-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/model-selection.py" "$@"
fi

# Exercise local catalog validation and refresh using only disposable offline fixtures.
if [ "${1:-}" = --model-catalog-only ]; then
  shift
  exec python3 "$REPO_ROOT/tests/model-catalog.py" "$@"
fi

# Inspect focused shell delivery boundaries without reading runtime stores.
if [ "${1:-}" = --hook-shell-quality-only ]; then
  shift
  exec bash "$REPO_ROOT/tests/hook-shell-quality.sh" "$@"
fi

# Run exact timing and complete lifecycle fixtures in disposable roots.
if [ "${1:-}" = --hook-timing-only ]; then
  shift
  exec bash "$REPO_ROOT/tests/hook-timing.sh" "$@"
fi

# Exercise workflow prompt integration without invoking models or real user stores.
if [ "${1:-}" = --hook-workflow-only ]; then
  shift
  exec bash "$REPO_ROOT/tests/hook-workflow-contract.sh" "$@"
fi

# Run user hook lifecycle acceptance without deploying to the current home.
if [ "${1:-}" = --hook-install-only ]; then
  shift
  exec bash "$REPO_ROOT/tests/hook-install.sh" "$@"
fi

# Run native hook acceptance independently of deployment and historical stores.
if [ "${1:-}" = --hook-adapter-only ]; then
  shift
  exec bash "$REPO_ROOT/tests/log-step-hook.sh" "$@"
fi

# Resolve private patterns from an explicit local override or user config. Keep the
# pattern file outside the repository so it does not publish the identifiers it guards.
hygiene_patterns_path() {
  local config_home candidate
  if [ "${ORCHESTRAIL_HYGIENE_DENYLIST+x}" = x ]; then
    [ -n "$ORCHESTRAIL_HYGIENE_DENYLIST" ] || return 1
    printf '%s\n' "$ORCHESTRAIL_HYGIENE_DENYLIST"
    return 0
  fi
  if [ -n "${XDG_CONFIG_HOME:-}" ]; then
    config_home="$XDG_CONFIG_HOME"
  elif [ -n "${HOME:-}" ]; then
    config_home="$HOME/.config"
  else
    return 2
  fi
  candidate="$config_home/orchestrail/hygiene-patterns.txt"
  [ -e "$candidate" ] || return 2
  printf '%s\n' "$candidate"
}

# Scan the working contents of all indexed paths, including newly staged files.
# Only the original source specification is exempt.
run_public_hygiene() (
  local root="$1" denylist="${2:-}" scratch line file status count=0 bad=0
  root="$(cd "$root" && pwd -P)" || { echo 'Hygiene root is unavailable'; return 1; }
  if [ -z "$denylist" ] || [ ! -f "$denylist" ] || [ ! -r "$denylist" ]; then
    echo 'Hygiene pattern file is missing or unreadable'; return 1
  fi
  scratch="$(mktemp -d "${TMPDIR:-/tmp}/tracked-hygiene.XXXXXX")" || return 1
  trap 'rm -rf "$scratch"' EXIT
  : > "$scratch/patterns" || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      *[![:space:]]*) ;;
      *) continue ;;
    esac
    case "${line#"${line%%[![:space:]]*}"}" in \#*) continue ;; esac
    printf '%s\n' "$line" >> "$scratch/patterns" || return 1
  done < "$denylist"
  if [ ! -s "$scratch/patterns" ]; then
    echo 'Hygiene pattern file has no literal patterns'; return 1
  fi
  if [ "$(git -C "$root" rev-parse --show-toplevel)" != "$root" ]; then
    echo 'Hygiene root must be the repository root'; return 1
  fi
  if ! git -C "$root" ls-files --cached -z > "$scratch/files"; then
    echo 'Hygiene tracked-file enumeration failed'; return 1
  fi
  # An empty index is an error: there is no tracked publication scope to verify.
  if [ ! -s "$scratch/files" ]; then
    echo 'Hygiene scan requires tracked files'; return 1
  fi
  while IFS= read -r -d '' file; do
    count=$((count + 1))
    case "$file" in
      .ai/specs/completed/00-sensitive-data-scrub.md) continue ;;
    esac
    if [ -L "$root/$file" ]; then
      # Git stores link text; do not follow a target outside the repository.
      if ! readlink -- "$root/$file" > "$scratch/link"; then
        printf 'Hygiene cannot read symlink: %q\n' "$file"; bad=1; continue
      fi
      line="$scratch/link"
    elif [ -f "$root/$file" ] && [ -r "$root/$file" ]; then
      line="$root/$file"
    else
      printf 'Hygiene tracked file is missing or unreadable: %q\n' "$file"; bad=1; continue
    fi
    status=0
    grep -Fia -f "$scratch/patterns" -- "$line" > /dev/null || status=$?
    case "$status" in
      0) printf 'Hygiene forbidden token in tracked file: %q\n' "$file"; bad=1 ;;
      1) ;;
      *) printf 'Hygiene scan error for tracked file: %q\n' "$file"; bad=1 ;;
    esac
  done < "$scratch/files"
  [ "$count" -gt 0 ] && [ "$bad" -eq 0 ]
)

# Standalone scanner: --root selects a repository; --denylist selects a local pattern file.
if [ "${1:-}" = --hygiene-only ]; then
  shift
  hygiene_root="$REPO_ROOT"
  hygiene_denylist=''
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --root|--denylist)
        [ "$#" -ge 2 ] && [ -n "$2" ] || { echo 'Missing hygiene option value' >&2; exit 1; }
        case "$1" in
          --root) hygiene_root="$2" ;;
          --denylist) hygiene_denylist="$2" ;;
        esac
        shift 2 ;;
      *) echo 'Unknown hygiene option' >&2; exit 1 ;;
    esac
  done
  if [ -z "$hygiene_denylist" ]; then
    status=0
    hygiene_denylist="$(hygiene_patterns_path)" || status=$?
    if [ "$status" -ne 0 ]; then
      echo 'Hygiene patterns are not configured; set ORCHESTRAIL_HYGIENE_DENYLIST or pass --denylist' >&2
      exit 1
    fi
  fi
  run_public_hygiene "$hygiene_root" "$hygiene_denylist"
  exit $?
fi
# Compare canonical Markdown JSON tables with the helper's effective shared export.
validate_run_log_contract() {
  python3 - "$REPO_ROOT" <<'PYRUNLOGCONTRACT'
from pathlib import Path
import json, re, subprocess, sys
root = Path(sys.argv[1])
errors = []
def fail(field, reason):
    errors.append(f'run-log contract {field}: {reason}')
try:
    text = (root/'rules/run-log.md').read_text()
    output = subprocess.check_output(['bash', str(root/'scripts/log-step.sh'), 'contract'], text=True)
    runtime = {}
    for line in output.splitlines():
        key, separator, value = line.partition('=')
        if not separator or key in runtime:
            fail(key, 'malformed or duplicate runtime definition')
        runtime[key] = value
    availability = runtime.pop('usage.availability', None)
    registry = runtime.pop('usage.registry', None)
    if availability not in ('available', 'unavailable'):
        fail('usage.availability', 'missing or invalid usage availability')
    elif (availability == 'available') != (registry is not None):
        fail('usage.registry', 'registry availability does not match the export')
    elif registry is not None:
        try:
            if not isinstance(json.loads(registry), dict):
                raise ValueError('expected object')
        except ValueError:
            fail('usage.registry', 'invalid registry JSON')
    documented = {}
    for heading in ('Runtime vocabulary', 'Legacy normalization'):
        matches = list(re.finditer(r'^### '+re.escape(heading)+r'\s*$', text, re.M))
        if len(matches) != 1:
            fail(heading.lower(), 'missing or duplicate canonical table section')
        elif not re.match(r'\s*\| Runtime key \| Canonical JSON value \|\n\|---\|---\|\n\| `',
                          text[matches[0].end():]):
            fail(heading.lower(), 'missing canonical table header or rows')
    for line in text.splitlines():
        match = re.fullmatch(r'\| `([^`]+)` \| ([^|]+) \|', line)
        if not match:
            continue
        key, encoded = match.groups()
        if key in documented:
            fail(key, 'duplicate documentation row')
        try:
            value = json.loads(encoded)
        except ValueError:
            fail(key, 'invalid canonical JSON value'); continue
        if not isinstance(value, (str, list)) or isinstance(value,list) and (
                not value or not all(isinstance(item,str) and item for item in value)):
            fail(key, 'expected exact string or nonempty string array'); continue
        documented[key] = value
    if not runtime:
        fail('tables', 'empty runtime export')
    for key in sorted(runtime.keys() | documented.keys()):
        if key not in runtime:
            fail(key, 'extra documentation value or missing runtime definition'); continue
        if key not in documented:
            fail(key, 'missing documentation value or extra runtime definition'); continue
        raw, expected = runtime[key], documented[key]
        is_set = key.startswith('step.') or key == 'run-end.outcome' or key in ('count.fields', 'hook.required', 'hook.boundary', 'hook.timing_source', 'hook.span_kind')
        if isinstance(expected,list) != is_set:
            fail(key, 'canonical value has the wrong JSON type'); continue
        if isinstance(expected,list):
            actual = raw.split(' ' if key in ('count.fields', 'hook.required') else '|')
            if len(expected) != len(set(expected)) or len(actual) != len(set(actual)):
                fail(key, 'duplicate enum or count value')
            if set(actual) != set(expected):
                fail(key, 'runtime and documentation values differ')
        elif raw != expected or not raw:
            fail(key, 'runtime and documentation mapping or bound differ')
    prefix_key = 'alias.gate.NEEDS_WORK_PREFIX'
    if prefix_key in runtime:
        # Check the documented boundary meaning independently of regex spelling.
        samples = [('NEEDS WORK',False), ('NEEDS WORKING',False), ('NEEDS WORK_',False),
                   ('needs work: text',False), ('XNEEDS WORK: text',False)]
        samples += [('NEEDS WORK'+boundary+suffix,True)
                    for boundary in (' ', '\t', '\n', '\r', '\v', '\f', ':', '-')
                    for suffix in ('', 'review', 'review\ncontinued')]
        probe = 'pattern=$1; shift; for value in "$@"; do if [[ "$value" =~ $pattern ]]; then echo yes; else echo no; fi; done'
        result = subprocess.check_output(['bash','-c',probe,'contract-boundary',runtime[prefix_key],
                                          *(value for value,_ in samples)],text=True).splitlines()
        if result != ['yes' if accepted else 'no' for _,accepted in samples]:
            fail(prefix_key, 'NEEDS WORK prefix boundary semantics differ')
except (OSError, ValueError, subprocess.SubprocessError) as error:
    fail('tables', f'cannot read canonical contract: {type(error).__name__}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('run-log contract: pass')
PYRUNLOGCONTRACT
}

if [ "${1:-}" = --run-log-contract-only ]; then
  [ "$#" -eq 1 ] || { echo 'Unexpected run-log contract argument' >&2; exit 1; }
  validate_run_log_contract
  exit $?
fi

if [ "$#" -gt 0 ]; then
  echo 'Usage: scripts/validate-contracts.sh [--hygiene-only [--root PATH] [--denylist PATH]]' >&2
  exit 1
fi

cd "$REPO_ROOT"

# Warn about committed rule changes since the last version change. Compare Git
# ancestry rather than timestamps so same-second commits and merges remain valid.
warn_stale_contract_version() {
  local version_commit newer_rules
  [ -f VERSION ] || return 0
  version_commit="$(git log -1 --format=%H -- VERSION 2>/dev/null)" || return 0
  [ -n "$version_commit" ] || return 0
  # Include staged and unstaged contents: a pending version update clears the warning.
  git diff --quiet "$version_commit" -- VERSION 2>/dev/null || return 0
  newer_rules="$(git log --format=%H "$version_commit..HEAD" -- rules/ 2>/dev/null)" || return 0
  if [ -n "$newer_rules" ]; then
    echo '[WARN] Rules changed after VERSION; update the contract version before release.' >&2
  fi
  return 0
}
warn_stale_contract_version

PASS=0
FAIL=0
SKIP=0

check() {
  local desc="$1"
  local result="$2"
  if [ "$result" = "pass" ]; then
    echo "[PASS] $desc"
    PASS=$((PASS + 1))
  elif [[ "$result" == skip:* ]]; then
    echo "[SKIP] $desc: ${result#skip: }"
    SKIP=$((SKIP + 1))
  else
    echo "[FAIL] $desc: $result"
    FAIL=$((FAIL + 1))
  fi
}

# ── Group 1: Protected section writers ───────────────────────────────

check "## Task Analysis has writer" \
  "$(grep -ql '## Task Analysis' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md missing ## Task Analysis')"

check "decomposition: complete has writer" \
  "$(grep -ql 'decomposition: complete' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing decomposition: complete')"

check "## Solution Design has writer" \
  "$(grep -ql '## Solution Design' workflows/pd-design.md 2>/dev/null && echo pass || echo 'pd-design.md missing ## Solution Design')"

check "## Subtask Progress has writer" \
  "$(grep -ql '## Subtask Progress' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md missing ## Subtask Progress')"

check "## Execution Report has writer" \
  "$(grep -ql '## Execution Report' workflows/pe-execute.md 2>/dev/null && echo pass || echo 'pe-execute.md missing ## Execution Report')"

check "## Contract Check has writer" \
  "$(grep -ql '## Contract Check' workflows/pv-contract.md 2>/dev/null && echo pass || echo 'pv-contract.md missing ## Contract Check')"

check "## Code Review has writer" \
  "$(grep -ql '## Code Review' workflows/pv-review.md 2>/dev/null && echo pass || echo 'pv-review.md missing ## Code Review')"

check "## Issue List has writer" \
  "$(grep -ql '## Issue List' workflows/pv-issues.md 2>/dev/null && echo pass || echo 'pv-issues.md missing ## Issue List')"

check "## Fix-Tasks has writer" \
  "$(grep -ql '## Fix-Tasks' workflows/pv-create-fixes.md 2>/dev/null && echo pass || echo 'pv-create-fixes.md missing ## Fix-Tasks')"

check "## Deferred has writer" \
  "$(grep -ql '## Deferred' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md missing ## Deferred')"

# ── Group 2: Atomic status vocabulary ────────────────────────────────

# Anchored to the definition line, not to a bare mention: every one of these words also
# appears elsewhere in the file (## Phases, the plan.md table, the composite fields), so a
# substring check passed even when the vocabulary line itself was deleted.
ATOMIC_STATUS_LINE="$(grep 'Status values for atomic-execution / atomic-validation:' rules/workflow-globals.md 2>/dev/null || true)"
check "Atomic status vocabulary line present in workflow-globals" \
  "$([ -n "$ATOMIC_STATUS_LINE" ] && echo pass || echo 'workflow-globals.md has no atomic-status vocabulary definition line')"

for status in not-started in-progress complete blocked skipped failed; do
  check "Atomic status '$status' defined in workflow-globals vocabulary line" \
    "$(printf '%s' "$ATOMIC_STATUS_LINE" | grep -q "\`$status\`" && echo pass || echo "workflow-globals.md atomic status vocabulary is missing: $status")"
done

# ── Group 3: plan.md status vocabulary ───────────────────────────────

# Anchored to a table row in the "Subtask statuses in plan.md" table, for the same reason.
for status in not-started in-progress done reviewed deferred blocked not-reached; do
  check "plan.md status '$status' has a row in the workflow-globals status table" \
    "$(grep -qE "^\| \`$status\` \|" rules/workflow-globals.md 2>/dev/null && echo pass || echo "workflow-globals.md plan.md status table is missing a row for: $status")"
done

# ── Group 4: pd-analyze reads correct root files ─────────────────────

check "pd-analyze references architecture.md" \
  "$(grep -q 'architecture\.md' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md missing architecture.md reference')"

check "pd-analyze references memory/state.md" \
  "$(grep -q 'memory/state\.md' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md missing memory/state.md reference')"

check "pd-analyze references principles/architecture.md" \
  "$(grep -q 'principles/architecture\.md' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md missing principles/architecture.md reference')"

# ── Group 5: pae-implement reads runbook, not CLAUDE.md for commands ─

check "pae-implement references runbook.md" \
  "$(grep -q 'runbook\.md' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md missing runbook.md reference')"

# ── Group 6: Status Translation Table completeness ───────────────────
# Note: Status Translation Table was moved to workflow-reference.md in Step 1.
# These checks target workflow-reference.md, not workflow-globals.md.

check "Translation table: complete (atomic-execution)" \
  "$(grep -q 'complete.*atomic-execution' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'Status Translation Table missing: complete (atomic-execution)')"

check "Translation table: complete (atomic-validation)" \
  "$(grep -q 'complete.*atomic-validation' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'Status Translation Table missing: complete (atomic-validation)')"

# Each row is asserted as a source→target mapping, not as a bare mention of the word:
# deleting the whole table used to leave these three checks passing.
check "Translation table: blocked → blocked row" \
  "$(grep -qE "^\| \`blocked\` +\| +\`blocked\`" rules/workflow-reference.md 2>/dev/null && echo pass || echo 'Status Translation Table missing the blocked → blocked row')"

check "Translation table: skipped → not-reached row" \
  "$(grep -qE "^\| \`skipped\` +\| +\`not-reached\`" rules/workflow-reference.md 2>/dev/null && echo pass || echo 'Status Translation Table missing the skipped → not-reached row')"

check "Translation table: failed → blocked row" \
  "$(grep -qE "^\| \`failed\` +\| +\`blocked\`" rules/workflow-reference.md 2>/dev/null && echo pass || echo 'Status Translation Table missing the failed → blocked row')"

# ── Group 7: pd-archive exists ───────────────────────────────────────

check "pd-archive.md exists" \
  "$([ -f workflows/pd-archive.md ] && echo pass || echo 'workflows/pd-archive.md not found (created in Step 6)')"

# ── Group 8: state-archive pointer protection in compress-state ───────

check "compress-state protects state-archive pointers" \
  "$(grep -q 'state-archive' workflows/compress-state.md 2>/dev/null && echo pass || echo 'compress-state.md missing state-archive.md pointer protection (added in Step 7)')"

# ── Group 9: Composite block format in workflow-globals ──────────────

check "workflow-globals has [composite] block kind" \
  "$(grep -q '\[composite\]' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing [composite] block kind')"

check "workflow-globals has rollup: field" \
  "$(grep -q 'rollup:' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing rollup: field definition')"

check "workflow-globals has integration-validation: field" \
  "$(grep -q 'integration-validation:' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing integration-validation: field definition')"

check "phase-composite-validation.md exists" \
  "$([ -f workflows/phase-composite-validation.md ] && echo pass || echo 'workflows/phase-composite-validation.md not found')"

check "pav-close triggers composite validation" \
  "$(grep -q 'phase-composite-validation' workflows/pav-close.md 2>/dev/null && echo pass || echo 'pav-close.md missing composite validation trigger')"

check "pe-execute handles composite rows" \
  "$(grep -q 'composite' workflows/pe-execute.md 2>/dev/null && echo pass || echo 'pe-execute.md missing composite row handling')"

check "pe-finalize has composite reconciliation" \
  "$(grep -q 'composite' workflows/pe-finalize.md 2>/dev/null && echo pass || echo 'pe-finalize.md missing composite reconciliation')"

check "pae-finalize has composite rollup step" \
  "$(grep -q 'rollup' workflows/pae-finalize.md 2>/dev/null && echo pass || echo 'pae-finalize.md missing composite rollup step')"

# B-2 regression: workflow-globals declared the [composite] block "written by pd-decompose",
# but pd-decompose only ever wrote the ## Decomposition marker. Every composite task
# dead-ended at its first composite subtask because five readers stop on a missing block.
# Grepping for "[composite]" alone is not enough — the string also occurs in reader files;
# the writer must emit the block header AND carry the upsert rule that makes a re-run safe.
check "COMPOSITE: pd-decompose writes the ## Subtask Progress section" \
  "$(grep -q 'Initialise `## Subtask Progress`' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md does not initialise ## Subtask Progress — the composite and leaf blocks every pe-*/pae-*/pav-* reader depends on have no writer')"

check "COMPOSITE: pd-decompose emits the [composite] block header itself" \
  "$(grep -qE '^ *\[composite\] T-XX \| <name> \| rollup: not-started \| integration-validation: not-started' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md does not emit a [composite] block header with rollup: not-started and integration-validation: not-started')"

check "COMPOSITE: pd-decompose writes children: in the block it creates" \
  "$(grep -qE '^ *children: T-XXa' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md writes no children: line — pe-execute and phase-composite-validation both read that field')"

# The upsert rule is the half that keeps a Guard-confirmed re-run from destroying progress.
PD_UPSERT="$(awk '/\*\*Upsert semantics/,/tripwire/' workflows/pd-decompose.md 2>/dev/null || true)"
check "COMPOSITE: pd-decompose upserts by ID (no duplicate block)" \
  "$(printf '%s' "$PD_UPSERT" | grep -qi 'never write a duplicate block' && echo pass || echo 'pd-decompose.md ## Subtask Progress step has no no-duplicate-block rule — a re-run appends a second block for the same T-XX')"

check "COMPOSITE: pd-decompose re-run never resets a status past not-started" \
  "$(printf '%s' "$PD_UPSERT" | grep -qi 'never reset a block whose' && printf '%s' "$PD_UPSERT" | grep -q 'beyond `not-started`' && echo pass || echo 'pd-decompose.md ## Subtask Progress step does not forbid resetting a status already beyond not-started — a re-run wipes recorded progress')"

# Writer and readers must agree on the field name, not merely both mention composites.
for reader in workflows/pe-execute.md workflows/phase-composite-validation.md; do
  check "COMPOSITE: $(basename $reader) reads children: — the field pd-decompose writes" \
    "$(grep -q 'children:' "$reader" 2>/dev/null && grep -qE '^ *children: T-XXa' workflows/pd-decompose.md 2>/dev/null && echo pass || echo "$reader and workflows/pd-decompose.md disagree on the composite children field name")"
done

# ── Group 10: Classifier and depth-2 cap ─────────────────────────────

check "pd-decompose references autonomous classifier (S1-S5)" \
  "$(grep -q 'S1\|S2\|S3\|S4\|S5' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing S1-S5 signal references')"

check "pd-decompose enforces depth-2 cap" \
  "$(grep -qi 'depth-2\|depth 2' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing depth-2 cap enforcement')"

check "workflow-reference has Autonomous Subtask Classifier" \
  "$(grep -q 'Autonomous Subtask Classifier' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing Autonomous Subtask Classifier section')"

check "workflow-reference has Type 2 nesting rule (S2>=2 AND S5>=2)" \
  "$(grep -q 'S2 ≥ 2' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing Type 2 rule (S2 >= 2 AND S5 >= 2)')"

check "workflow-reference has Type 3 rule (S4 AND S3>=2)" \
  "$(grep -q 'S4.*S3\|Type 3' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing Type 3 rule')"

check "pv-create-fixes has D8 sibling naming" \
  "$(grep -q 'sibling letter\|D8' workflows/pv-create-fixes.md 2>/dev/null && echo pass || echo 'pv-create-fixes.md missing D8 sibling-letter naming')"

check "pv-create-fixes reverts composite on fix creation" \
  "$(grep -q 'Revert\|integration-validation.*not-started' workflows/pv-create-fixes.md 2>/dev/null && echo pass || echo 'pv-create-fixes.md missing parent composite reversion')"

check "pd-finalize exempts composites from Steps-count rule" \
  "$(grep -q 'type: composite\|composite.*Steps' workflows/pd-finalize.md 2>/dev/null && echo pass || echo 'pd-finalize.md missing composite Steps-count exemption')"

check "pae-implement has tripwire check" \
  "$(grep -qi 'tripwire' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md missing tripwire check section')"

check "## Decomposition Decisions in workflow-reference" \
  "$(grep -q 'Decomposition Decisions' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing Decomposition Decisions format')"

# ── Group 11: C-1 regression — no domain terms in Type 3 logic ───────
# Logic must use abstract role names; domain terms (client, server) allowed only in example blocks.

check "C-1: pd-decompose Type 3 instruction uses producer not client" \
  "$(grep -A20 'When Type 3 re-slicing is selected' workflows/pd-decompose.md 2>/dev/null | grep -q 'producer' && echo pass || echo 'pd-decompose.md Type 3 instruction missing producer role — may have regressed to client/server')"

check "C-1: workflow-reference Type 3 rule uses producer not client/server" \
  "$(grep -A5 'When Type 3 applies' rules/workflow-reference.md 2>/dev/null | grep -q 'producer' && echo pass || echo 'workflow-reference.md Type 3 rule missing producer role — may have regressed to client/server')"

check "C-1: PIPELINE.md Type 3 description uses producer not client" \
  "$(grep 'Vertical re-sliced' workflows/PIPELINE.md 2>/dev/null | grep -q 'producer' && echo pass || echo 'PIPELINE.md Type 3 row missing producer role — may have regressed to client/server')"

check "C-1: pd-decompose Execution Strategy template uses producer not client" \
  "$(grep 'Execution Strategy.*states\|states.*ordering' workflows/pd-decompose.md 2>/dev/null | grep -q 'producer' && echo pass || echo 'pd-decompose.md Execution Strategy template uses client/server — regression')"

# ── Group 12: C-2 regression — ID scheme is defined ──────────────────

check "C-2: pd-decompose Type 3 defines base ID assignment rule" \
  "$(grep -q 'base.*min\|min.*AA.*BB' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing Type 3 base ID assignment rule')"

check "C-2: pd-decompose Type 3 has collision-safety rule" \
  "$(grep -qi 'collision' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing collision-safety rule for Type 3 IDs')"

check "C-2: workflow-reference Type 3 rule has collision-safety" \
  "$(grep -qi 'collid' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing collision-safety rule for Type 3 IDs')"

check "C-2: pd-decompose collision rule specifies shift quantum 'upward by 1'" \
  "$(grep -q 'upward by 1' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md collision rule missing required shift quantum (upward by 1)')"

check "C-2: workflow-reference collision rule specifies shift quantum 'upward by 1'" \
  "$(grep -q 'upward by 1' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md collision rule missing required shift quantum (upward by 1)')"

check "C-2: pd-decompose collision rule has loop termination ('until...free')" \
  "$(grep -q 'until.*free' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md collision rule missing loop termination condition (until...free)')"

check "C-2: workflow-reference collision rule has loop termination ('until...free')" \
  "$(grep -q 'until.*free' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md collision rule missing loop termination condition (until...free)')"

check "C-2: neither collision-rule source uses wrong-direction shift ('downward')" \
  "$(grep -l 'downward' workflows/pd-decompose.md rules/workflow-reference.md 2>/dev/null | grep -q '.' && echo 'collision rule contains wrong-direction shift (downward) — behavioral regression' || echo pass)"

# ── Group 13: C-3 regression — tripwire uses structure not ID pattern ─

check "C-3: pae-implement tripwire checks plan.md or state.md structure (not ID pattern)" \
  "$(grep -A20 'Depth-2 cap constraint' workflows/pae-implement.md 2>/dev/null | grep -q 'plan\.md\|state\.md\|children:' && echo pass || echo 'pae-implement.md depth-2 check must use plan.md/state.md structure, not ID regex')"

check "C-3: pae-implement tripwire does not rely on letter-suffix ID pattern" \
  "$(grep -A10 'Depth-2 cap constraint' workflows/pae-implement.md 2>/dev/null | grep -qF 'T-\d+[a-z]' && echo 'depth-2 check still uses raw regex ID pattern — regression' || echo pass)"

# ── Group 14: M-1 regression — cross-cutting work rule present ────────

check "M-1: pd-decompose Type 3 has cross-cutting work rule" \
  "$(grep -qi 'cross-cutting\|shared.*all capabilities\|all capabilities.*shared' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing cross-cutting work rule for Type 3')"

check "M-1: workflow-reference Type 3 rule has cross-cutting work rule" \
  "$(grep -qi 'cross-cutting\|shared.*all capabilities\|all capabilities.*shared' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing cross-cutting work rule for Type 3')"

# ── Group 15: M-2 regression — compress-state points to workflow-reference ──

check "M-2: compress-state references workflow-reference for Protected Sections" \
  "$(grep -q 'workflow-reference.*Protected Sections\|workflow-reference → ## Protected' workflows/compress-state.md 2>/dev/null && echo pass || echo 'compress-state.md does not reference workflow-reference for Protected Sections Contract')"

check "M-2: compress-state does not reference workflow-globals for Protected Sections" \
  "$(grep -q 'workflow-globals.*Protected Sections' workflows/compress-state.md 2>/dev/null && echo 'compress-state.md still references workflow-globals for Protected Sections — regression' || echo pass)"

# ── Group 16: M-3 — Type 3 limitation documented ─────────────────────

check "M-3: PIPELINE.md documents Type 3 no-integration-validation limitation" \
  "$(grep -qi 'Known Limitations\|no.*whole-group\|no automatic.*integration' workflows/PIPELINE.md 2>/dev/null && echo pass || echo 'PIPELINE.md missing Type 3 integration-validation limitation documentation')"

# ── Group 17: TDD step wiring ────────────────────────────────────────

check "TDD: rules/tdd.md exists" \
  "$([ -f rules/tdd.md ] && echo pass || echo 'rules/tdd.md not found')"

check "TDD: rules/tdd.md is always_on" \
  "$(grep -q 'trigger: always_on' rules/tdd.md 2>/dev/null && echo pass || echo 'rules/tdd.md missing trigger: always_on')"

check "TDD: workflows/pae-tests.md exists" \
  "$([ -f workflows/pae-tests.md ] && echo pass || echo 'workflows/pae-tests.md not found')"

check "TDD: phase-atomic-execution calls pae-tests" \
  "$(grep -q 'pae-tests' workflows/phase-atomic-execution.md 2>/dev/null && echo pass || echo 'phase-atomic-execution.md does not invoke /pae-tests')"

check "TDD: pae-tests runs before pae-implement in orchestrator" \
  "$(awk '/Run child workflows in order/,/pae-finalize/' workflows/phase-atomic-execution.md 2>/dev/null | grep -n 'pae-tests\|pae-implement' | head -2 | head -1 | grep -q 'pae-tests' && echo pass || echo 'phase-atomic-execution.md lists pae-implement before pae-tests — TDD order regression')"

check "TDD: atomic-tests field defined in workflow-globals" \
  "$(grep -q 'atomic-tests:' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing atomic-tests: field definition')"

check "TDD: atomic-tests field defined in workflow-reference" \
  "$(grep -q 'atomic-tests:' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing atomic-tests: field in Subtask Progress format')"

for tstatus in red green n-a; do
  check "TDD: atomic-tests status '$tstatus' in workflow-globals" \
    "$(grep -q "\`$tstatus\`" rules/workflow-globals.md 2>/dev/null && echo pass || echo "workflow-globals.md missing atomic-tests status: $tstatus")"
done

check "TDD: backward compatibility for missing atomic-tests documented" \
  "$(grep -qi 'pre-TDD' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing pre-TDD backward-compatibility rule for absent atomic-tests field')"

check "TDD: pae-implement guards on RED before implementing" \
  "$(grep -q 'atomic-tests:' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md missing TDD gate on atomic-tests')"

# The word "weaken" appears in the permitted-amendment prose too, so a bare mention survived
# even when the prohibition itself was inverted. Match the prohibition, not the topic.
check "TDD: pae-implement forbids weakening the RED set" \
  "$(grep -qE 'RED test set may not be weakened|may not be weakened' workflows/pae-implement.md 2>/dev/null && grep -qE 'Do not delete, rename, comment out, or mark' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md no longer states that the RED test set may not be weakened, or lost the concrete list of forbidden edits — the frozen-contract rule is then unenforceable')"

check "TDD: tdd rule and pae-implement agree that weakening needs a recorded amendment" \
  "$(grep -q 'tdd: test amended' rules/tdd.md 2>/dev/null && grep -q 'tdd: test amended' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'the tdd: test amended record is missing from rules/tdd.md or workflows/pae-implement.md — an amendment could then be made with no audit line for /pav-check to find')"

# pae-finalize mentions atomic-tests in its Pre-check as well, so a bare mention passed even
# with the preservation instruction deleted. Match the instruction: preserve, never downgrade.
check "TDD: pae-finalize preserves atomic-tests" \
  "$(grep -qE 'Preserve .atomic-tests:. as set by' workflows/pae-finalize.md 2>/dev/null && grep -qiE 'never remove or downgrade it' workflows/pae-finalize.md 2>/dev/null && echo pass || echo 'pae-finalize.md step 1 no longer instructs preserving atomic-tests without removing or downgrading it — the TDD audit trail can be dropped at finalization')"

check "TDD: pav-check audits the test set" \
  "$(grep -q 'atomic-tests' workflows/pav-check.md 2>/dev/null && echo pass || echo 'pav-check.md missing TDD check')"

check "TDD: test-level gate defined in tdd rule" \
  "$(grep -q 'smoke' rules/tdd.md 2>/dev/null && grep -q 'contract' rules/tdd.md 2>/dev/null && echo pass || echo 'rules/tdd.md missing test-level gate levels (unit/integration/contract/smoke/none)')"

# The word "justification" survives in the rejected-reasons prose, so requiring the record must
# be matched as a mandate plus the literal notes: line /pae-tests writes and /pav-check audits.
check "TDD: 'none' level requires justification" \
  "$(grep -qE 'Justification record \(mandatory when .none.\)' rules/tdd.md 2>/dev/null && grep -qE '^tdd: none —' rules/tdd.md 2>/dev/null && echo pass || echo 'rules/tdd.md no longer mandates the tdd: none — <...> justification record, so an n-a subtask can be closed with no reason for /pav-check to audit')"

check "TDD: the none-justification line has a writer and an auditor" \
  "$(grep -q 'tdd: none —' workflows/pae-tests.md 2>/dev/null && grep -qE 'n-a. → verify the justification|unjustified' workflows/pav-check.md 2>/dev/null && echo pass || echo 'the tdd: none justification line is written by no workflow or audited by none — /pae-tests must write it and /pav-check must check it')"

check "TDD: pae-tests enforces observed RED (not assumed)" \
  "$(grep -qi 'expected reason' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md missing expected-reason RED verification')"

check "TDD: pae-tests requires test: command from runbook" \
  "$(grep -q 'runbook' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md missing runbook test: command requirement')"

check "TDD: ## Test Plan has writer (pd-decompose)" \
  "$(grep -q '## Test Plan' workflows/pd-decompose.md 2>/dev/null && echo pass || echo 'pd-decompose.md missing ## Test Plan section in description.md template')"

check "TDD: ## Test Plan verified by pd-finalize" \
  "$(grep -q '## Test Plan' workflows/pd-finalize.md 2>/dev/null && echo pass || echo 'pd-finalize.md missing ## Test Plan verification')"

check "TDD: pd-finalize checks six sections not five" \
  "$(grep -q 'all six sections' workflows/pd-finalize.md 2>/dev/null && echo pass || echo 'pd-finalize.md still verifies five sections — ## Test Plan not enforced')"

check "TDD: subtask-description template has ## Test Plan" \
  "$(grep -q '## Test Plan' templates/subtask-description.md 2>/dev/null && echo pass || echo 'templates/subtask-description.md missing ## Test Plan section')"

check "TDD: quick-flow mandates inline TDD step" \
  "$(grep -q '## TDD (quick)' rules/quick-flow.md 2>/dev/null && echo pass || echo 'quick-flow.md missing inline TDD step / ## TDD (quick) section')"

check "TDD: phase-pipeline registers pae-tests child" \
  "$(grep -q 'pae-tests' workflows/phase-pipeline.md 2>/dev/null && echo pass || echo 'phase-pipeline.md missing pae-tests in child workflow list')"

check "TDD: phase-pipeline does not allow skipping the TDD step" \
  "$(grep -q 'never skipped' workflows/phase-pipeline.md 2>/dev/null && echo pass || echo 'phase-pipeline.md must state the TDD step is never skipped in autonomous mode')"

check "TDD: compress-state protects the tdd audit trail" \
  "$(grep -q 'atomic-tests\|tdd:' workflows/compress-state.md 2>/dev/null && echo pass || echo 'compress-state.md does not protect atomic-tests / tdd: notes lines')"

check "TDD: workflow-globals has Test-first execution principle" \
  "$(grep -qi 'Test-first execution' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md missing Test-first execution global principle')"

check "TDD: testing-standards links to the executing workflow" \
  "$(grep -q 'pae-tests' principles/testing-standards.md 2>/dev/null && echo pass || echo 'principles/testing-standards.md TDD sequence not linked to /pae-tests executor')"

check "TDD: PIPELINE.md documents the three-step atomic cycle" \
  "$(grep -q 'pae-tests' workflows/PIPELINE.md 2>/dev/null && echo pass || echo 'PIPELINE.md missing pae-tests in atomic cycle / child workflow table')"

check "TDD: scripts/sync.sh deploys tdd.md to projects" \
  "$(grep -q 'tdd\.md' scripts/sync.sh 2>/dev/null && echo pass || echo 'scripts/sync.sh does not deploy tdd.md to per-project rule directories')"

check "TDD: scripts/setup-new-project.sh deploys tdd.md" \
  "$(grep -q 'tdd\.md' scripts/setup-new-project.sh 2>/dev/null && echo pass || echo 'scripts/setup-new-project.sh does not deploy tdd.md to new projects')"

check "TDD: pv-create-fixes requires Test Plan for fix-tasks" \
  "$(grep -q '## Test Plan' workflows/pv-create-fixes.md 2>/dev/null && echo pass || echo 'pv-create-fixes.md missing Test Plan requirement for fix-tasks')"

# ── Group 18: Orchestration + git flow ───────────────────────────────

for f in rules/git-flow.md rules/orchestration.md workflows/spec-run.md \
         workflows/restack.md workflows/pv-classify-fixes.md; do
  check "ORCH: $f exists" \
    "$([ -f "$f" ] && echo pass || echo "$f not found")"
done

for f in rules/git-flow.md rules/orchestration.md; do
  check "ORCH: $f is always_on" \
    "$(grep -q 'trigger: always_on' "$f" 2>/dev/null && echo pass || echo "$f missing trigger: always_on")"
done

# base_commit is the single input that makes restack strategy-agnostic.
# Assert it is in the canonical leaf-block FORMAT, not merely mentioned in prose.
for f in rules/workflow-globals.md rules/workflow-reference.md; do
  check "ORCH: base_commit in canonical leaf block ($(basename $f))" \
    "$(grep -qE '^  base_commit:' "$f" 2>/dev/null && echo pass || echo "$f leaf-block format is missing the base_commit: line — restack cannot survive a squash merge without it")"
done

check "ORCH: git-flow records base_commit and forbids recomputing it" \
  "$(grep -qE '^base_commit:' rules/git-flow.md 2>/dev/null && grep -qi 'never\*\* recomputed\|never recomputed' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must both record base_commit in the state block and state it is never recomputed')"

for f in workflows/spec-run.md workflows/restack.md; do
  check "ORCH: $(basename $f) consumes base_commit" \
    "$(grep -q 'base_commit' "$f" 2>/dev/null && echo pass || echo "$f does not use base_commit")"
done

check "ORCH: restack guard stops when base_commit is missing" \
  "$(grep -A3 'missing .base_commit:' workflows/restack.md 2>/dev/null | grep -qi 'stop' && echo pass || echo 'restack.md must stop when a subtask has no recorded base_commit')"

check "ORCH: compress-state protects the git audit trail" \
  "$(grep -q 'base_commit' workflows/compress-state.md 2>/dev/null && echo pass || echo 'compress-state.md does not protect base_commit / git fields')"

check "ORCH: restack uses rebase --onto (strategy-agnostic primitive)" \
  "$(grep -q 'rebase --onto' workflows/restack.md 2>/dev/null && echo pass || echo 'restack.md missing git rebase --onto primitive')"

# "conflict" appears in the explanation prose too. The contract is that the run STOPS and does
# not resolve the conflict itself — a policy flipped to auto-resolution kept the word.
RESTACK_FLAT="$(tr '\n' ' ' < workflows/restack.md 2>/dev/null | tr -s ' ' || true)"
check "ORCH: restack halts on conflict instead of auto-resolving" \
  "$(printf '%s' "$RESTACK_FLAT" | grep -qE 'On conflict\*\* → \*\*stop immediately\*\*' && printf '%s' "$RESTACK_FLAT" | grep -q 'Do not attempt automatic resolution' && echo pass || echo 'restack.md step 2 no longer stops immediately on a rebase conflict and refuses automatic resolution — a content decision would be made mechanically')"

# Safety rails
check "ORCH: git add -A forbidden in git-flow" \
  "$(grep -iE 'git add -A' rules/git-flow.md 2>/dev/null | grep -qi 'forbidden' && echo pass || echo 'git-flow.md must state git add -A is FORBIDDEN — only intentional, authorized paths may be staged')"

check "ORCH: spec-run repeats the blanket-add prohibition" \
  "$(grep -qi 'never .git add -A.\|never \`git add -A\`' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md must state explicit paths only, never git add -A')"

check "ORCH: force-push restricted to --force-with-lease" \
  "$(grep -q 'force-with-lease' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing --force-with-lease restriction')"

check "ORCH: spec-run never merges pull requests" \
  "$(grep -qi 'never merges' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md must state it never merges a pull request')"

check "ORCH: git-flow forbids pushing to the base branch" \
  "$(grep -qi 'Forbidden, always' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing absolute prohibitions table')"

check "ORCH: preflight accepts repository-owned tracked knowledge" \
  "$(grep -qF 'Tracked knowledge and state are accepted' rules/git-flow.md 2>/dev/null && grep -qF 'Keep untracked consumer state excluded' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must accept tracked knowledge while keeping untracked consumer state local by default')"

# Commit attribution policy
check "ORCH: commits carry no AI authorship attribution" \
  "$(grep -q 'No authorship attribution' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing the no-attribution commit rule')"

check "ORCH: no-attribution rule overrides harness defaults" \
  "$(grep -qi 'overrides any tool default' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must state the no-attribution rule overrides harness defaults that append a trailer')"

for f in rules/global-claude.md templates/codex-global-AGENTS.md templates/AGENTS.md; do
  check "ORCH: no-attribution rule present in $(basename $f)" \
    "$(grep -q 'Co-Authored-By' "$f" 2>/dev/null && grep -qi 'overrides any tool default' "$f" 2>/dev/null && echo pass || echo "$f missing the no-attribution commit rule — harness defaults would append an attribution trailer")"
done

check "ORCH: Co-Authored-By named as forbidden" \
  "$(grep -q 'Co-Authored-By' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must name Co-Authored-By trailers as forbidden')"

# Role separation (A-prime): implementer and validator are distinct agents
check "ORCH: orchestration defines the four roles" \
  "$(grep -q 'Implementer' rules/orchestration.md 2>/dev/null && grep -q 'Validator' rules/orchestration.md 2>/dev/null && grep -q 'Arbiter' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md missing role definitions')"

check "ORCH: validator is a separate agent from the implementer" \
  "$(grep -q 'separate agent' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md must require a separate Validator agent — A-prime collapsed into A')"

check "ORCH: spec-run spawns a separate validator" \
  "$(grep -qi 'Spawn a \*\*separate\*\* sub-agent' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md does not spawn a separate Validator agent')"

check "ORCH: arbiter answers require a citation" \
  "$(grep -qi 'without a citation is not an answer' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md missing the arbiter citation rule')"

check "ORCH: sub-agents do not write shared files" \
  "$(grep -qi 'Shared-file discipline' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md missing shared-file discipline section')"

# Sequential-only guarantee
check "ORCH: execution is declared strictly sequential" \
  "$(grep -qi 'strictly sequential' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md must declare execution strictly sequential — Subtask Progress has no locking')"

check "ORCH: workflow-globals registers orchestrated mode" \
  "$(grep -q 'spec-run' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md does not register /spec-run')"

# Class A/B escalation and the Discovery batch gate
SPECRUN_FLAT_GATE="$(tr '\n' ' ' < workflows/spec-run.md 2>/dev/null | tr -s ' ' || true)"

check "ORCH: class A/B escalation protocol defined" \
  "$(grep -q 'Class A' rules/orchestration.md 2>/dev/null && grep -q 'Class B' rules/orchestration.md 2>/dev/null && echo pass || echo 'orchestration.md missing class A/B escalation protocol')"

check "ORCH: pd-analyze collects class-B into the batch" \
  "$(grep -q 'Open Questions (batch)' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md does not collect class-B ambiguities into ## Open Questions (batch)')"

check "ORCH: batch gate runs before the first branch" \
  "$(grep -qi 'before any branch is created' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md must gate the batch before creating the first branch')"

# Saying WHEN the gate runs is not the gate. The one planned human stop is the run actually
# stopping and waiting — a version that presented the questions and then answered them itself
# kept the timing sentence intact.
check "ORCH: the batch gate actually stops and waits for the human" \
  "$(printf '%s' "$SPECRUN_FLAT_GATE" | grep -q 'Then \*\*stop and wait\*\*' && echo pass || echo 'spec-run.md batch gate no longer stops and waits — class-B questions are reserved for the human by orchestration and no agent, arbiter included, may answer them')"

check "ORCH: spec-run never resolves a class-B ambiguity itself" \
  "$(grep -q 'Never resolves a class-B ambiguity on the human.s behalf' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md dropped the never-resolves-class-B rail from ## What this workflow never does')"

check "ORCH: Open Questions (batch) marker registered" \
  "$(grep -q 'Open Questions (batch)' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference.md missing ## Open Questions (batch) marker')"

# Stack model
check "ORCH: subtask branches stack on the previous subtask" \
  "$(grep -qi 'tip of branch N-1\|tip of subtask N-1' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must define branches as cut from the previous subtask tip')"

check "ORCH: stack merge dependency is stated, not hidden" \
  "$(grep -qi 'cannot be merged into' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must state plainly that a PR cannot be merged without its predecessors')"

# "draft" also appears in the recorded-state example (pr: #142 draft), so the bare word survived
# a policy flipped to "ready on creation". Match the policy line itself.
check "ORCH: PRs are draft during the run" \
  "$(tr '\n' ' ' < rules/git-flow.md 2>/dev/null | tr -s ' ' | grep -qE 'State during the run\*\* = draft' && echo pass || echo 'git-flow.md no longer states that a PR is a draft for the duration of the run — the stack could shift under the run while later subtasks are still being built')"

check "ORCH: PRs are promoted to ready after validation" \
  "$(grep -qi 'ready for review' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing ready-for-review promotion step')"

check "ORCH: RED gets its own commit" \
  "$(grep -qE '^\| .test: ' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing the separate RED commit row — the evidence tests came first')"

# Planning identifiers stay out of product content and git metadata.
check "ORCH: git-flow forbids pipeline identifiers in the repository" \
  "$(grep -q 'Pipeline identifiers stay out of the repository' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md missing the section forbidding T-XX / spec / ADR / .ai references in committed content')"

check "ORCH: product content remains independent of planning records" \
  "$(grep -qi 'dangling reference\|file that does not exist in the repository' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must explain why product content cannot depend on internal planning references')"

check "ORCH: commit scope is a feature name, never a work-item id" \
  "$(grep -qi 'never a subtask, spec, or task identifier' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md must forbid work-item ids as commit scope')"

check "ORCH: branch names are feature-based, not identifier-based" \
  "$(grep -q 'never encodes the subtask identifier' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md branch naming must be feature-based and exclude subtask/spec identifiers')"

check "ORCH: no T-XX-shaped branch template survives in git-flow" \
  "$(grep -qE 'task/<NN>|/T-XX-' rules/git-flow.md 2>/dev/null && echo 'git-flow.md still shows an identifier-based branch template — regression' || echo pass)"

# Matches any concrete or placeholder id used as a commit scope or inside a branch path,
# not just the literal T-XX placeholder — a real leak would read test(T-01), not test(T-XX).
for f in rules/git-flow.md workflows/spec-run.md workflows/pv-create-fixes.md; do
  check "ORCH: no work-item id used as commit scope in $(basename $f)" \
    "$(grep -qE '(test|feat|fix|refactor|perf|docs|chore)\(T-[0-9A-Za-z]+\)' "$f" 2>/dev/null && echo "$f uses a work-item id as commit scope — identifiers must not reach commits" || echo pass)"

  check "ORCH: no identifier-bearing branch path in $(basename $f)" \
    "$(grep -qE '(task/[^ \`]*T-|task/<NN>)' "$f" 2>/dev/null && echo "$f still shows an identifier-based branch path — regression" || echo pass)"
done

check "ORCH: PR stack line names predecessors by branch" \
  "$(grep -qi 'named by branch, never by subtask identifier' rules/git-flow.md 2>/dev/null && echo pass || echo 'git-flow.md PR stack-position line must name predecessors by branch name')"

check "ORCH: code-quality forbids pipeline references in code" \
  "$(grep -qi 'AI-pipeline artifacts in code' principles/code-quality.md 2>/dev/null && echo pass || echo 'code-quality.md must forbid T-XX / ADR / .ai references in code and comments')"

for f in rules/global-claude.md templates/codex-global-AGENTS.md templates/AGENTS.md; do
  check "ORCH: identifier ban present in $(basename $f)" \
    "$(grep -qi 'No internal planning identifiers' "$f" 2>/dev/null && echo pass || echo "$f missing the no-identifier rule for commits and code")"
done

check "ORCH: report warns hashes are pre-merge" \
  "$(grep -qi 'pre-merge' workflows/spec-run.md 2>/dev/null && echo pass || echo 'spec-run.md report must state commit hashes are pre-merge')"

# Fix classification
check "ORCH: fix classification reuses the quick-flow gate" \
  "$(grep -qi 'quick-flow' workflows/pv-classify-fixes.md 2>/dev/null && echo pass || echo 'pv-classify-fixes.md must reuse the quick-flow gate rather than a new rule')"

check "ORCH: pv-create-fixes calls the classifier" \
  "$(grep -q 'pv-classify-fixes' workflows/pv-create-fixes.md 2>/dev/null && echo pass || echo 'pv-create-fixes.md does not call /pv-classify-fixes')"

check "ORCH: Fix Classification subsection permitted in workflow-globals" \
  "$(grep -q 'Fix Classification' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals.md ## Fix-Tasks format does not permit the ### Fix Classification subsection')"

# Optional model columns
# Bulk selection persists explicit provider decisions through the compatible updater;
# single recommendations remain chat-only. Legacy Model reading stays canonical.
PDSM_FLAT="$(tr '\n' ' ' < workflows/pd-select-model.md 2>/dev/null | tr -s ' ' || true)"
check "ORCH: pd-select-model persists explicit optional model columns in bulk mode" \
  "$(printf '%s' "$PDSM_FLAT" | grep -qF 'Bulk mode writes only explicit' && printf '%s' "$PDSM_FLAT" | grep -qF 'Model (Claude)' && printf '%s' "$PDSM_FLAT" | grep -qF 'Model (Codex)' && printf '%s' "$PDSM_FLAT" | grep -qF -- '--update-plan PLAN --updates UPDATES.json' && echo pass || echo 'bulk selection must persist explicit provider-column decisions through the compatible plan updater')"

check "ORCH: pd-select-model keeps single recommendations chat-only" \
  "$(printf '%s' "$PDSM_FLAT" | grep -qF 'Single mode stays chat-only for recommendations.' && echo pass || echo 'single recommendations must not overwrite persisted bulk model decisions')"

check "ORCH: pd-select-model no longer claims it writes no files" \
  "$(grep -q 'writes \*\*no files at all\*\*' workflows/pd-select-model.md 2>/dev/null && echo 'pd-select-model.md still claims it writes no files — contradicts the Model column' || echo pass)"

# Deployment
for f in scripts/sync.sh scripts/setup-new-project.sh; do
  check "ORCH: $f deploys git-flow.md and orchestration.md" \
    "$(grep -q 'git-flow\.md' "$f" 2>/dev/null && grep -q 'orchestration\.md' "$f" 2>/dev/null && echo pass || echo "$f does not deploy the orchestration rules")"
done

check "ORCH: setup-new-project seeds .ai/ into .gitignore" \
  "$(grep -q '"\.ai/"' scripts/setup-new-project.sh 2>/dev/null && echo pass || echo 'scripts/setup-new-project.sh does not add .ai/ to GITIGNORE_ENTRIES — new consumers must keep local state ignored by default')"

# Exercise the real per-project policy block without deploying global skills.
test_sync_preserves_repository_knowledge_policy() (
  local fixture project_dir policy output mode
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/knowledge-policy.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  policy="$(sed -n '/^  # 5\./,/^  PROJECTS_UPDATED=/p' scripts/sync.sh | sed '$d')"
  [ -n "$policy" ] || return 1
  for mode in tracked untracked; do
    project_dir="$fixture/$mode"
    mkdir -p "$project_dir/.ai" || return 1
    git -C "$project_dir" init -q || return 1
    printf '%s\n' 'Knowledge fixture' > "$project_dir/.ai/README.md"
    printf '%s\n' 'local-cache/' > "$project_dir/.gitignore"
    if [ "$mode" = tracked ]; then
      git -C "$project_dir" add -- .ai/README.md || return 1
    fi
    output="$(eval "$policy")" || return 1
    if [ "$mode" = tracked ]; then
      cmp -s "$project_dir/.gitignore" <(printf '%s\n' 'local-cache/') || {
        echo 'Sync changed ignore policy for tracked knowledge'; return 1;
      }
      if grep -q 'rm -r --cached' <<< "$output"; then
        echo 'Sync tells a tracked knowledge repository to remove its files'; return 1
      fi
    else
      grep -qxF '.ai/' "$project_dir/.gitignore" || {
        echo 'Sync no longer supplies the ignore default for untracked state'; return 1;
      }
    fi
    eval "$policy" >/dev/null || return 1
    [ "$(grep -cxF '.ai/' "$project_dir/.gitignore")" -le 1 ] || return 1
  done
)

check "ORCH: sync preserves tracked knowledge and ignores untracked state by default" \
  "$(test_sync_preserves_repository_knowledge_policy && echo pass || echo 'sync must retain repository-owned tracking policy and idempotently ignore untracked consumer state')"

# ── Group 19: Cross-file reference integrity ─────────────────────────
# The reference tables were moved from workflow-globals to workflow-reference; ten workflows
# kept citing the old location, so "load X from workflow-globals" pointed at nothing.
for section in "Status Translation Table" "Decomposition Rules" "Entry Format" "Update Rules" "Protected Sections"; do
  check "REF: '$section' is not cited as living in workflow-globals" \
    "$(grep -rn 'workflow-globals' rules/*.md workflows/*.md principles/*.md docs/USAGE.md 2>/dev/null | grep -q "$section" && echo "a file cites 'workflow-globals' for '$section', which lives in workflow-reference — the reference does not resolve" || echo pass)"
done

for section in "## Status Translation Table" "## Decomposition Rules" "## .ai/memory/state.md Entry Format" "## .ai/project_state.md Update Rules" "## Protected Sections Contract" "## Autonomous Decision Protocol" "## Autonomous Subtask Classifier"; do
  check "REF: workflow-reference actually defines '$section'" \
    "$(grep -qF "$section" rules/workflow-reference.md 2>/dev/null && echo pass || echo "rules/workflow-reference.md no longer defines '$section' — every workflow citing it now dangles")"
done

check "REF: pae-finalize cites workflow-reference for the translation table" \
  "$(grep -q 'Status Translation Table in workflow-reference' workflows/pae-finalize.md 2>/dev/null && echo pass || echo 'pae-finalize.md must cite workflow-reference for the Status Translation Table')"

check "REF: pav-close cites workflow-reference for the translation table" \
  "$(grep -q 'Status Translation Table in workflow-reference' workflows/pav-close.md 2>/dev/null && echo pass || echo 'pav-close.md must cite workflow-reference for the Status Translation Table')"

check "REF: rules/phase-discovery does not point at itself for ## Execution Modes" \
  "$(grep -q 'See .phase-discovery.md → ## Execution Modes' rules/phase-discovery.md 2>/dev/null && echo 'rules/phase-discovery.md points at itself for ## Execution Modes — that section lives in the workflow' || echo pass)"

check "REF: pv-create-fixes does not claim the subtask template is deployed into projects" \
  "$(grep -q 'provided by scripts/setup-new-project.sh in the project' workflows/pv-create-fixes.md 2>/dev/null && echo 'pv-create-fixes.md points at a template that no script copies into a project' || echo pass)"

check "REF: phase-atomic-execution description names description.md, not a T-XX plan.md" \
  "$(sed -n '1,5p' workflows/phase-atomic-execution.md | grep -q 'using its plan.md' && echo 'phase-atomic-execution.md frontmatter still names a T-XX plan.md — that file does not exist in this structure' || echo pass)"

# ── Group 20: description.md six-section contract ────────────────────
# Every producer, verifier and reference must list the same six sections. workflow-reference
# lost "## Scope" while /pae-implement stops without it.
for f in rules/workflow-reference.md workflows/pd-decompose.md templates/subtask-description.md workflows/PIPELINE.md; do
  for sec in "## Goal" "## Context" "## Scope" "## Steps" "## Acceptance Criteria" "## Test Plan"; do
    check "DESC: $(basename $f) lists '$sec'" \
      "$(grep -qF "$sec" "$f" 2>/dev/null && echo pass || echo "$f does not list $sec — the six-section description.md contract disagrees between files")"
  done
done

check "DESC: pae-implement stops when ## Scope is missing" \
  "$(grep -q 'missing .## Scope. section' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement.md must stop when description.md has no ## Scope')"

# ── Group 21: RED digest has a writer ────────────────────────────────
# /pae-implement and /pav-check both read an AC→test-name mapping from notes:. Nothing wrote
# it — the mapping only reached the chat transcript.
check "TDD: pae-tests persists the RED digest to notes:" \
  "$(grep -q 'tdd: red digest' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md does not write the AC→test-name RED digest into notes: — pae-implement and pav-check read a line nothing writes')"

check "TDD: pae-tests writes the digest in every mode, not only batch" \
  "$(grep -q 'RED digest is written in every mode' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md must state the RED digest is recorded regardless of batch mode')"

check "TDD: pav-check reads the digest line by name" \
  "$(grep -q 'tdd: red digest' workflows/pav-check.md 2>/dev/null && echo pass || echo 'pav-check.md must name the tdd: red digest line it audits against')"

# ── Group 22: pd-archive is reachable ────────────────────────────────
# pd-archive's Guard stops unless discovery: complete. pd-finalize used to set that marker
# after invoking it, so the archive step could never run.
check "ARCH: pd-finalize sets discovery: complete BEFORE invoking /pd-archive" \
  "$(awk '/set .discovery: complete./{s=NR} /Run .\/pd-archive/{a=NR} END{exit !(s && a && s < a)}' workflows/pd-finalize.md 2>/dev/null && echo pass || echo 'pd-finalize.md invokes /pd-archive before setting discovery: complete — pd-archive Guard step 2 stops, so archiving is unreachable')"

check "ARCH: pd-archive still guards on discovery: complete" \
  "$(grep -q 'discovery: complete' workflows/pd-archive.md 2>/dev/null && echo pass || echo 'pd-archive.md lost its discovery: complete guard')"

# ── Group 23: Protected sections cover every section with a later reader ─
for sec in "## Contract (quick)" "## TDD (quick)" "## Flow Escalation" "## Improvement Proposals" "## Open Questions (batch)"; do
  check "PROT: '$sec' is in the Protected Sections Contract" \
    "$(awk '/^## Protected Sections Contract/,/^## .ai\/memory\/state.md Entry Format/' rules/workflow-reference.md 2>/dev/null | grep -qF "$sec" && echo pass || echo "workflow-reference.md Protected Sections Contract does not protect $sec — /compress-state may delete it before its reader runs")"
done

check "PROT: pe-finalize still reads the improvement proposals it depends on" \
  "$(grep -q '## Improvement Proposals' workflows/pe-finalize.md 2>/dev/null && echo pass || echo 'pe-finalize.md no longer reads ## Improvement Proposals')"

# ── Group 24: quick tier keeps the test-first rule ───────────────────
check "QUICK: phase-execution quick branch runs the inline TDD step" \
  "$(grep -q 'Run the inline TDD step first' workflows/phase-execution.md 2>/dev/null && echo pass || echo 'phase-execution.md quick branch implements without the inline RED step that quick-flow and tdd mandate')"

check "QUICK: phase-execution quick branch records ## TDD (quick)" \
  "$(grep -q '## TDD (quick)' workflows/phase-execution.md 2>/dev/null && echo pass || echo 'phase-execution.md quick branch does not record the ## TDD (quick) section')"

# ── Group 25: rule deployment completeness ───────────────────────────
# Checking two named rules passed while quick-flow and all five phase-* rules were absent
# from scripts/setup-new-project.sh: a workflow saying "follow phase-atomic-execution rules" had
# nothing to follow in a freshly set-up project.
for rule in rules/*.md; do
  name=$(basename "$rule")
  base="${name%.md}"
  # Claude Code and Codex have no rules directory: every rule is deployed as a skill under the
  # `rule-` prefix. The prefix is a correctness requirement — five basenames exist in both
  # workflows/ and rules/, so an unprefixed rule skill would overwrite a workflow skill.
  check "DEPLOY: the rule skill path rule-$base cannot collide with a workflow skill" \
    "$([ ! -f "workflows/rule-$base.md" ] && echo pass || echo "workflows/rule-$base.md exists, so the rule skill rule-$base and that workflow skill would deploy to the same path")"
  [ "$name" = "global-claude.md" ] && continue   # deployed as ~/.claude/CLAUDE.md, not as a project rule
  check "DEPLOY: scripts/setup-new-project.sh copies $name" \
    "$(grep -q "$name" scripts/setup-new-project.sh 2>/dev/null && echo pass || echo "scripts/setup-new-project.sh does not copy rules/$name into .windsurf/rules/ and .devin/rules/")"
  check "DEPLOY: scripts/sync.sh refreshes $name in existing projects" \
    "$(grep -q "$name" scripts/sync.sh 2>/dev/null && echo pass || echo "scripts/sync.sh per-project loop does not refresh rules/$name")"
done

# Both skill roots must receive *every* rule, not a hand-maintained subset: the deployment loop
# has to iterate "$RULES"/*.md. Before this, "load the `tdd` rule" pointed at a file that existed
# in neither Claude Code nor Codex.
check "DEPLOY: scripts/sync.sh deploys every rule as a Claude Code rule-* skill" \
  "$(awk '/^# ── 3c\./,/^# ── 4\./' scripts/sync.sh 2>/dev/null | grep -q 'for file in "$RULES"/\*\.md' && awk '/^# ── 3c\./,/^# ── 4\./' scripts/sync.sh 2>/dev/null | grep -q 'cp "$file" ~/.claude/skills/$skill_name/SKILL.md' && echo pass || echo 'scripts/sync.sh has no step that copies every rules/*.md to ~/.claude/skills/rule-<name>/SKILL.md — every "load the <rule> rule" instruction is unreachable in Claude Code')"

check "DEPLOY: scripts/sync.sh deploys every rule as a Codex rule-* skill" \
  "$(awk '/^# ── 4d\./,/^# ── 5\./' scripts/sync.sh 2>/dev/null | grep -q 'for file in "$RULES"/\*\.md' && awk '/^# ── 4d\./,/^# ── 5\./' scripts/sync.sh 2>/dev/null | grep -q 'cp "$file" ~/.codex/skills/$skill_name/SKILL.md' && echo pass || echo 'scripts/sync.sh has no step that copies every rules/*.md to ~/.codex/skills/rule-<name>/SKILL.md — every "load the <rule> rule" instruction is unreachable in Codex')"

for root in claude codex; do
  check "DEPLOY: the $root rule deployment uses the rule- prefix" \
    "$(grep -q "skill_name=\"rule-\${name}\"" scripts/sync.sh 2>/dev/null && grep -q "mkdir -p ~/.$root/skills/\$skill_name" scripts/sync.sh 2>/dev/null && echo pass || echo "scripts/sync.sh deploys rules into ~/.$root/skills/ without the rule- prefix, which overwrites the five identically-named workflow skills")"
done

check "DEPLOY: workflow-globals tells the reader how to resolve a rule reference per agent" \
  "$(grep -q 'rule-phase-atomic-execution' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals Context Bootstrap does not name the rule- prefixed skills, so a reader cannot tell the phase rule from the identically-named phase workflow')"

check "DEPLOY: workflow-globals states that a skill is model-invoked, not always-on" \
  "$(tr '\n' ' ' < rules/workflow-globals.md 2>/dev/null | tr -s ' ' | grep -q 'A skill is model-invoked, not always-on' && echo pass || echo 'workflow-globals does not record that deploying an always_on rule as a skill changes its trigger semantics — the reason the always-on essentials stay in global-claude/AGENTS.md')"

check "DEPLOY: USAGE deployment matrix shows the rule skills" \
  "$(grep -q 'skills/rule-<name>/SKILL.md' docs/USAGE.md 2>/dev/null && echo pass || echo 'docs/USAGE.md section 2 deployment matrix still says rules reach Claude Code only as global-claude and Codex not at all')"

check "DEPLOY: setup-all-repos captures a failing setup run (set -e safe)" \
  "$(grep -q 'if ! (cd "$dir" && bash "$WORKFLOWS_SRC/scripts/setup-new-project.sh")' scripts/setup-all-repos.sh 2>/dev/null && echo pass || echo 'scripts/setup-all-repos.sh runs scripts/setup-new-project.sh bare under set -e — the error branch below it can never execute')"

# ── Group 26: no pipeline identifier in a commit-shaped example ───────
# The canonical commits: field showed "type(T-XX): summary", which is exactly the leak
# git-flow forbids. Placeholder and concrete forms both match.
for f in rules/workflow-globals.md rules/workflow-reference.md rules/git-flow.md workflows/spec-run.md workflows/pv-create-fixes.md docs/USAGE.md; do
  check "ORCH: no work-item id as commit scope in $(basename $f)" \
    "$(grep -qE '(<type>|type|test|feat|fix|refactor|perf|docs|chore)\(T-[0-9A-Za-z]+\)' "$f" 2>/dev/null && echo "$f uses a work-item id as a commit scope — identifiers must never reach a commit message" || echo pass)"
done

# ── Group 27: USAGE mirrors the canonical formats it documents ────────
check "USAGE: canonical Subtask Progress block carries atomic-tests" \
  "$(grep -q 'T-XX | <name> | atomic-tests:' docs/USAGE.md 2>/dev/null && echo pass || echo 'docs/USAGE.md documents the pre-TDD Subtask Progress block — it omits atomic-tests:')"

check "USAGE: does not claim the language rule sets a chat language" \
  "$(grep -qi 'chat replies in Russian\|Russian in chat' docs/USAGE.md 2>/dev/null && echo 'docs/USAGE.md claims language.md sets a chat language; the rule explicitly refuses to' || echo pass)"

check "USAGE: compress-state default target matches the workflow" \
  "$(grep -q 'Default target: .\.ai/memory/state\.md' docs/USAGE.md 2>/dev/null && echo pass || echo 'docs/USAGE.md documents the wrong default target for /compress-state')"

# ── Group 28: every workflow is documented somewhere reachable ────────
# A workflow that appears in no reference table is deployed but undiscoverable.
for wf in workflows/*.md; do
  name=$(basename "$wf" .md)
  check "DOC: $name appears in docs/USAGE.md" \
    "$(grep -q "$name" docs/USAGE.md 2>/dev/null && echo pass || echo "workflows/$name.md is deployed as a skill but appears nowhere in docs/USAGE.md")"
done

for name in pd-archive pd-select-model phase-composite-validation pv-classify-fixes; do
  check "DOC: $name appears in the PIPELINE reference" \
    "$(grep -q "$name" workflows/PIPELINE.md 2>/dev/null && echo pass || echo "PIPELINE.md does not list /$name")"
done

# ── Group 29: git safety rails, per operation ────────────────────────
# The prior check only asserted the phrase "Forbidden, always" appeared somewhere. These
# assert each dangerous operation still sits on a row that forbids or confines it — a row
# whose policy silently flipped to "allowed" would have passed before.
rail() {
  local op="$1" desc="$2"
  local line
  line="$(grep -F "$op" rules/git-flow.md 2>/dev/null | grep '^|' | head -1)"
  if [ -z "$line" ]; then
    echo "git-flow.md safety-rail table has no row for $desc"
  elif printf '%s' "$line" | grep -qiE 'forbidden|only inside|only .--force-with-lease'; then
    echo pass
  else
    echo "git-flow.md safety-rail row for $desc no longer forbids or confines it: $line"
  fi
}
check "RAIL: git push --force is forbidden outside /restack"   "$(rail 'git push --force' 'git push --force')"
check "RAIL: gh pr merge is forbidden"                          "$(rail 'gh pr merge' 'gh pr merge')"
check "RAIL: blanket staging is forbidden"                      "$(rail 'git add -A' 'git add -A / . / --all')"
check "RAIL: git rebase outside /restack is forbidden"          "$(rail 'git rebase' 'git rebase outside /restack')"
check "RAIL: git reset --hard / git clean are forbidden"        "$(rail 'git reset --hard' 'git reset --hard / git clean')"
check "RAIL: branch deletion is forbidden"                      "$(rail 'Branch deletion' 'branch deletion')"
check "RAIL: pushing to the base branch is forbidden"           "$(rail 'any protected branch' 'push to base/protected branch')"

# Only /restack may carry the rebase / force-push primitives. PIPELINE.md describes restack,
# so it is allowed to name them; any other workflow naming them is a rail breach.
check "RAIL: rebase / force-push primitives appear only in restack (and the reference doc)" \
  "$(for f in workflows/*.md; do case "$(basename $f)" in restack.md|PIPELINE.md) continue;; esac; grep -qE 'git rebase --onto|--force-with-lease|push --force' "$f" && echo "$f"; done | grep -q . && echo "a workflow other than /restack carries a rebase or force-push command: $(for f in workflows/*.md; do case "$(basename $f)" in restack.md|PIPELINE.md) continue;; esac; grep -qE 'git rebase --onto|--force-with-lease|push --force' "$f" && basename $f; done | tr '\n' ' ')" || echo pass)"

check "RAIL: no workflow merges a pull request" \
  "$(grep -rlE '^[^|]*gh pr merge' workflows/*.md 2>/dev/null | grep -q . && echo 'a workflow contains a gh pr merge command' || echo pass)"

check "RAIL: no workflow stages with git add -A / git add ." \
  "$(grep -rnE 'git add (-A|\.|--all)' workflows/*.md 2>/dev/null | grep -viE 'never|forbidden|not' | grep -q . && echo 'a workflow instructs a blanket git add' || echo pass)"

# ── Group 30: the quick tier reaches the end of the pipeline ─────────
# quick skips pv-create-fixes, so anything that hard-requires ## Fix-Tasks dead-ends it.
check "QUICK: pv-finalize does not require ## Fix-Tasks on the quick tier" \
  "$(grep -q 'Exception — .flow: quick' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md Guard stops when ## Fix-Tasks is missing — on flow: quick that section is never written, so validation can never be finalized')"

check "QUICK: pv-contract reads the contract from ## Contract (quick) on the quick tier" \
  "$(grep -q '## Contract (quick)' workflows/pv-contract.md 2>/dev/null && echo pass || echo 'pv-contract.md reads only ## Solution Design — a quick task has no such section, so the contract check would find nothing')"

check "QUICK: pv-review reads the quick contract too" \
  "$(grep -q '## Contract (quick)' workflows/pv-review.md 2>/dev/null && echo pass || echo 'pv-review.md has no quick-tier source for the contract it reviews against')"

check "QUICK: pd-analyze writes the quick contract" \
  "$(grep -q '## Contract (quick)' workflows/pd-analyze.md 2>/dev/null && echo pass || echo 'pd-analyze.md does not write ## Contract (quick) — the quick tier would have no contract at all')"

check "QUICK: phase-discovery skips decompose+design on the quick tier" \
  "$(grep -qi 'skip Steps 2 and 3' workflows/phase-discovery.md 2>/dev/null && echo pass || echo 'phase-discovery.md does not branch on flow: quick')"

# ── Group 31: pv-classify-fixes ordering ─────────────────────────────
check "FIX: pv-classify-fixes creates ## Fix-Tasks itself when it runs first" \
  "$(tr '\n' ' ' < workflows/pv-classify-fixes.md 2>/dev/null | grep -q 'create .## Fix-Tasks. if it does not exist yet' && echo pass || echo 'pv-classify-fixes.md writes into a section pv-create-fixes has not created yet and does not say to create it')"

# ── Group 32: ADR index — one schema, shared by every writer ──────────
# pv-finalize used to initialise "| ADR | Task | Decision | Status | Date |" and append rows
# in that order, while the seeded template and /onboard-legacy-project both use
# "| Number | Title | Status | Date | Link |". Against a template-seeded index every appended
# value landed one column right of where it belonged. The header alone is not enough to check:
# the append row must use the same column order as the header the same file initialises.
ADR_HEADER='| Number | Title | Status | Date | Link |'

for writer in workflows/pv-finalize.md workflows/onboard-legacy-project.md templates/.ai/adr/index.md templates/.ai-umbrella/adr/index.md; do
  check "ADR: $writer uses the canonical index header" \
    "$(grep -qF "$ADR_HEADER" "$writer" 2>/dev/null && echo pass || echo "$writer does not carry the canonical ADR index header '$ADR_HEADER'")"
done

check "ADR: pv-finalize appends a row in the canonical column order" \
  "$(grep -qE '^ *.?\| NNNN \| .+ \| Accepted \| YYYY-MM-DD \| \[' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md appends an ADR index row whose column order does not match the header it initialises (expected: Number | Title | Status | Date | Link)')"

# The superseded schema may still be quoted in the specs/ documents that describe the defect;
# it must not survive anywhere that is executed or deployed.
ADR_OLD_HITS="$(grep -rlF 'ADR | Task | Decision | Status | Date' workflows/ rules/ templates/ principles/ docs/USAGE.md scripts/sync.sh scripts/setup-new-project.sh scripts/setup-all-repos.sh scripts/setup-umbrella.sh scripts/link-skills.sh 2>/dev/null || true)"
check "ADR: the superseded index schema appears in no deployed file" \
  "$([ -z "$ADR_OLD_HITS" ] && echo pass || echo "the superseded ADR index schema still lives in: $(printf '%s' "$ADR_OLD_HITS" | tr '\n' ' ')— two schemas cannot both be legal")"

# ── Group 33: composite integration-validation has one trigger owner ──
# pav-close step 5 and pe-execute step 1 both used to invoke /phase-composite-validation. The
# second invocation lands on the workflow's Step 0.3 "already complete — confirm? (yes/no)"
# Guard, which is an unplanned stop inside /phase-pipeline and /spec-run. The check counts
# *invocations*, not mentions: a negated line ("do not call") is not an invocation, and a
# user-facing "Run /phase-composite-validation" report string is not one either.
# The backtick before /phase-... is matched as '.' — a backtick inside a single-quoted pattern
# in "$( … )" is not a backtick.
CCV_CALL_LINES="$(grep -n 'call ./phase-composite-validation' workflows/*.md 2>/dev/null | grep -v '^workflows/PIPELINE.md:' | grep -viE 'do \*\*not\*\* call|do not call|never call' || true)"
CCV_CALLERS="$(printf '%s\n' "$CCV_CALL_LINES" | sed -n 's/^\([^:]*\):.*/\1/p' | sort -u | tr '\n' ' ' | sed 's/ *$//')"

check "COMPOSITE: exactly one workflow invokes /phase-composite-validation" \
  "$([ "$CCV_CALLERS" = "workflows/pav-close.md" ] && echo pass || echo "the composite integration-validation trigger must be owned by pav-close alone; invokers found: ${CCV_CALLERS:-none}")"

# The non-owner has to say what it checks instead, or "verify the outcome" is unimplementable.
check "COMPOSITE: pe-execute verifies integration-validation instead of triggering it" \
  "$(grep -q 'integration-validation:' workflows/pe-execute.md 2>/dev/null && echo pass || echo 'pe-execute.md no longer names the integration-validation: field it must read in place of triggering composite validation')"

PE_FLAT="$(tr '\n' ' ' < workflows/pe-execute.md 2>/dev/null | tr -s ' ' || true)"
check "COMPOSITE: pe-execute records composite-stalled when the trigger never fired" \
  "$(printf '%s' "$PE_FLAT" | grep -q 'the trigger never fired. Record the composite as .composite-stalled.' && echo pass || echo 'pe-execute.md does not record composite-stalled in its verify branch — a composite whose trigger never fired leaves no trace in the Execution Report')"

check "COMPOSITE: composite-stalled is a documented Execution Report value" \
  "$(grep -q 'composite-stalled' workflows/PIPELINE.md 2>/dev/null && grep -q 'composite-stalled' workflows/pe-finalize.md 2>/dev/null && echo pass || echo 'composite-stalled is written by pe-execute but not defined in PIPELINE.md or consumed by pe-finalize')"

# ── Group 34: fix-task naming — one vocabulary end to end ─────────────
# The classifier used to name shared groups T-XX-fixes / T-XX-fixes-a, while the creator minted
# T-NN-fix-<slug>, the canonical Created: format used T-XX-fix-<slug>, and pv-execute-fixes
# discovered work by the glob T-XX-fix-* — which matches neither "fixes" form. A shared group
# was created and then never executed. Checking that each file mentions "fix" is useless here;
# the shape of the name is the contract.
FIXNAME_BAD="$(grep -rnE 'T-[0-9A-Za-z]+-fixes' workflows/ rules/ templates/ docs/USAGE.md 2>/dev/null || true)"
check "FIXNAME: no fix-task name uses the unexecutable 'fixes' form" \
  "$([ -z "$FIXNAME_BAD" ] && echo pass || echo "a T-NN-fixes form survives and matches no downstream reader: $(printf '%s' "$FIXNAME_BAD" | head -3 | tr '\n' ' ')")"

check "FIXNAME: pv-execute-fixes uses the authoritative Created list for both fix forms" \
  "$(grep -q 'Created:' workflows/pv-execute-fixes.md && grep -q 'T-XX-fix-<slug>' workflows/pv-execute-fixes.md && grep -q 'T-XXc-fix-<slug>' workflows/pv-execute-fixes.md && echo pass || echo 'fix execution must read Created: and support top-level plus composite fix siblings')"

check "FIXNAME: workflow-globals Created: format uses the same shape" \
  "$(grep -qE '^Created: T-XX-fix-<slug>' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals ## Fix-Tasks Created: format no longer uses the T-XX-fix-<slug> shape that pv-execute-fixes globs for')"

# The classifier must name shared groups in the executable form, and say so for both kinds.
CLASSIFY_FLAT="$(tr '\n' ' ' < workflows/pv-classify-fixes.md 2>/dev/null | tr -s ' ' || true)"
check "FIXNAME: classifier names a shared group T-NN-fix-<group-slug>" \
  "$(printf '%s' "$CLASSIFY_FLAT" | grep -q 'T-NN-fix-<group-slug>' && echo pass || echo 'pv-classify-fixes.md does not name shared groups in the T-NN-fix-<group-slug> form that pv-execute-fixes can discover')"

CLASSIFY_BRANCHES="$(grep -E '^\| #[0-9]+ <title> \|' workflows/pv-classify-fixes.md 2>/dev/null | sed 's/.*| *\(T-[^|]*\) *|.*/\1/' | grep -c . || true)"
CLASSIFY_BAD_BRANCHES="$(grep -E '^\| #[0-9]+ <title> \|' workflows/pv-classify-fixes.md 2>/dev/null | sed 's/.*| *\(T-[^|]*\) *|.*/\1/' | grep -cvE '^T-[0-9A-Za-z]+[a-z]?-fix-' || true)"
check "FIXNAME: classifier's Branch column examples are all executable fix-task IDs" \
  "$([ "${CLASSIFY_BRANCHES:-0}" -ge 2 ] && [ "${CLASSIFY_BAD_BRANCHES:-1}" -eq 0 ] && echo pass || echo "pv-classify-fixes.md ### Fix Classification must show at least two Branch-column examples and every one must match T-<n>-fix-<slug> (found $CLASSIFY_BRANCHES rows, $CLASSIFY_BAD_BRANCHES non-conforming)")"

check "FIXNAME: the D8 child-fix form matches the same glob shape" \
  "$(grep -q 'T-04d-fix-<slug>' workflows/pv-create-fixes.md 2>/dev/null && printf '%s' 'T-04d-fix-x' | grep -qE '^T-[0-9]+[a-z]?-fix-' && echo pass || echo 'pv-create-fixes.md lost the T-04d-fix-<slug> child-fix form, or that form no longer matches the T-XX-fix-* glob')"

check "FIXNAME: creator groups shared issues into one fix-task" \
  "$(tr '\n' ' ' < workflows/pv-create-fixes.md 2>/dev/null | tr -s ' ' | grep -q 'Each .shared. group becomes \*\*one\*\* fix-task' && echo pass || echo 'pv-create-fixes.md still mints one fix-task per approved issue, so the classifier shared/dedicated split has no effect on what is created')"

# ── Group 35: the RED commit is physically reachable in orchestrated mode ─
# git-flow requires a test-only `test:` commit per subtask ("the reviewable evidence that the
# tests came first"), but spec-run spawned one Implementer for /pae-tests → /pae-implement →
# /pae-finalize. A single spawn reports once, after GREEN, by which time implementation files
# are already in the tree and a test-only commit cannot be built. Naming the two commit points
# is not the contract — the contract is that the run stops between them.
SPECRUN_FLAT="$(tr '\n' ' ' < workflows/spec-run.md 2>/dev/null | tr -s ' ' || true)"
check "TDD-GIT: spec-run names a RED checkpoint, not just two commit points" \
  "$(printf '%s' "$SPECRUN_FLAT" | grep -qE 'report RED and wait|stops and reports' && echo pass || echo 'spec-run.md step 4.2 does not stop the Implementer at RED, so the test-only commit git-flow requires cannot be created')"

check "TDD-GIT: spec-run commits test paths before implementation exists" \
  "$(printf '%s' "$SPECRUN_FLAT" | grep -q 'target_files:. holds test files only' && echo pass || echo 'spec-run.md step 4.2 does not state that only test files are staged at the RED commit — without it the test: commit can silently include implementation')"

check "TDD-GIT: spec-run resumes the same agent after the RED commit" \
  "$(printf '%s' "$SPECRUN_FLAT" | grep -q 'sends the \*\*same\*\* agent one message to continue' && echo pass || echo 'spec-run.md step 4.2 does not resume the same agent after the RED commit — a fresh agent loses the RED set the GREEN step must read')"

check "TDD-GIT: the n-a case still yields a single implementation commit" \
  "$(printf '%s' "$SPECRUN_FLAT" | grep -q 'atomic-tests: n-a' && printf '%s' "$SPECRUN_FLAT" | grep -q 'single implementation commit' && echo pass || echo 'spec-run.md step 4.2 does not carry the atomic-tests: n-a exception — git-flow allows a single commit only in that case')"

# Ownership must still be one-sided: the Implementer writes code and tests, never git.
ORCH_IMPL_ROW="$(grep -E '^\| \*\*Implementer\*\* \|' rules/orchestration.md 2>/dev/null || true)"
check "TDD-GIT: orchestration Roles table still keeps git out of the Implementer" \
  "$([ -n "$ORCH_IMPL_ROW" ] && ! printf '%s' "$ORCH_IMPL_ROW" | grep -qi 'git' && printf '%s' "$ORCH_IMPL_ROW" | grep -q 'code, tests' && echo pass || echo 'orchestration ## Roles Implementer row is missing, or now claims the Implementer writes git — spec-run 4.2 gives every commit to the orchestrator')"

ORCH_ORCH_ROW="$(grep -E '^\| \*\*Orchestrator\*\* \|' rules/orchestration.md 2>/dev/null || true)"
check "TDD-GIT: orchestration Roles table gives git operations to the orchestrator" \
  "$(printf '%s' "$ORCH_ORCH_ROW" | grep -q 'git operations' && echo pass || echo 'orchestration ## Roles Orchestrator row no longer owns git operations, contradicting spec-run 4.2')"

check "TDD-GIT: orchestration Implementer section names the RED pause" \
  "$(tr '\n' ' ' < rules/orchestration.md 2>/dev/null | tr -s ' ' | grep -q 'pauses once, at RED' && echo pass || echo 'orchestration ### Implementer does not mention the RED pause spec-run 4.2 depends on — the two files disagree on the sequence')"

# ── Group 36: shared-file discipline covers every file a sub-agent is told to write ─
# orchestration listed plan.md among the files sub-agents must not write, while the mitigation
# clause named only architecture.md and .ai/memory/state.md — yet writing plan.md is the core
# job of /pae-finalize step 2 (Implementer) and /pav-close step 2 (Validator). The check is a
# mapping, not a mention: for every shared path a sub-agent workflow is instructed to update,
# that path must appear in the delta-return clause.
DELTA_CLAUSE="$(awk '/returns the proposed delta in its report/,/^## Escalation protocol/' rules/orchestration.md 2>/dev/null || true)"
check "SHARED: orchestration still has a delta-return clause" \
  "$([ -n "$DELTA_CLAUSE" ] && echo pass || echo 'rules/orchestration.md has no delta-return clause — every shared-file write instruction in a sub-agent workflow is then a flat contradiction')"

for wf in pae-tests pae-implement pae-finalize pav-check pav-propose pav-close phase-composite-validation; do
  for path in "plan.md" "architecture.md" ".ai/memory/state.md" ".ai/project_state.md"; do
    if grep -qE "(Update|update|Set|set|Write|write)[^|]*$path" "workflows/$wf.md" 2>/dev/null; then
      check "SHARED: $path written by $wf is covered by the delta-return clause" \
        "$(printf '%s' "$DELTA_CLAUSE" | grep -qF "$path" && echo pass || echo "workflows/$wf.md instructs a sub-agent to write $path, which orchestration ## Shared-file discipline forbids and its delta-return clause does not name")"
    fi
  done
done

# Both writers must say which mode they are in, or the delta-return route is unimplementable.
check "SHARED: pae-finalize step 2 names its orchestrated-mode behaviour" \
  "$(tr '\n' ' ' < workflows/pae-finalize.md 2>/dev/null | tr -s ' ' | grep -q 'Orchestrated mode (./spec-run.) — do not write the file' && echo pass || echo 'pae-finalize.md step 2 does not say what to do under /spec-run, where writing plan.md is forbidden')"

check "SHARED: pav-close step 2 names its orchestrated-mode behaviour" \
  "$(tr '\n' ' ' < workflows/pav-close.md 2>/dev/null | tr -s ' ' | grep -q 'Orchestrated mode (./spec-run.) — do not write the file' && echo pass || echo 'pav-close.md step 2 does not say what to do under /spec-run, where writing plan.md is forbidden')"

check "SHARED: the progress-block carve-out is not extended to plan.md" \
  "$(tr '\n' ' ' < rules/orchestration.md 2>/dev/null | tr -s ' ' | grep -q 'does \*\*not\*\* extend to .plan.md.' && echo pass || echo 'orchestration ## Shared-file discipline no longer states that the own-progress-block carve-out excludes plan.md')"

# ── Group 37: phase-pipeline does not re-derive the task directory name ─
# phase-pipeline Step 0.2a computed task_dir = .ai/tasks/todo/task- + basename(spec) and then
# said "proceed as phase-discovery Step 0", skipping Step 0.4b (-p<N> multi-phase naming) and
# Step 0.5 (numeric-prefix collision guard). A multi-phase spec was silently discovered as one
# unphased task. Either it delegates, or it carries both dropped rules itself.
PIPE_FLAT="$(tr '\n' ' ' < workflows/phase-pipeline.md 2>/dev/null | tr -s ' ' || true)"
PIPE_DELEGATES="$(printf '%s' "$PIPE_FLAT" | grep -qE 'Run .phase-discovery. Step 0 in full' && echo yes || echo no)"
PIPE_RESTATES="$(printf '%s' "$PIPE_FLAT" | grep -q 'p<N>' && printf '%s' "$PIPE_FLAT" | grep -qi 'prefix collision' && echo yes || echo no)"
check "PIPE: phase-pipeline delegates task-directory naming to phase-discovery Step 0" \
  "$([ "$PIPE_DELEGATES" = yes ] || [ "$PIPE_RESTATES" = yes ] && echo pass || echo 'phase-pipeline.md neither delegates to phase-discovery Step 0 nor carries the -p<N> derivation and the prefix-collision stop — a multi-phase spec gets a non-phased task directory')"

check "PIPE: phase-pipeline no longer computes the task directory itself" \
  "$(printf '%s' "$PIPE_FLAT" | grep -q 'task_dir = .\.ai/tasks/todo/task-. + basename' && echo 'phase-pipeline.md still derives task_dir from the spec basename, which bypasses phase-discovery Step 0.4b multi-phase naming' || echo pass)"

check "PIPE: phase-pipeline names the multi-phase suffix it must not drop" \
  "$(printf '%s' "$PIPE_FLAT" | grep -q '\-p<N>' && echo pass || echo 'phase-pipeline.md Step 0 does not mention the -p<N> multi-phase directory suffix, so nothing tells the reader which naming rule applies')"

# The rule it delegates to must still exist where it delegates to.
check "PIPE: phase-discovery Step 0.4b still derives the -p<N> suffix" \
  "$(grep -q 'task-<spec-basename>-p<N>' workflows/phase-discovery.md 2>/dev/null && echo pass || echo 'phase-discovery.md Step 0.4b no longer derives the -p<N> task directory — phase-pipeline delegates to a rule that is gone')"

check "PIPE: phase-discovery Step 0.5 still guards numeric-prefix collisions" \
  "$(grep -q 'Spec prefix collision' workflows/phase-discovery.md 2>/dev/null && echo pass || echo 'phase-discovery.md lost the numeric-prefix collision stop that phase-pipeline delegates to')"

# ── Group 38: /phase-pipeline accounts for every stop it can reach ────
# The command advertises a fully autonomous run, but pe-finalize step 5 said "Wait for user
# choice" with no override, and the pipeline's own pav-propose override ("auto-apply") flatly
# contradicted the --batch it passes ("do NOT prompt and do NOT apply"). The check is a mapping:
# any child workflow that can stop for a user outside its ## Guard must be named in the
# pipeline's ## Pipeline Overrides region — the curated region, not the child-workflow list.
PIPE_OVERRIDE_REGION="$(awk '/^## Pipeline Overrides/,/^## Deep Architectural Analysis Protocol/' workflows/phase-pipeline.md 2>/dev/null || true)"
check "PIPE: the Pipeline Overrides region exists" \
  "$([ -n "$PIPE_OVERRIDE_REGION" ] && echo pass || echo 'phase-pipeline.md has no ## Pipeline Overrides region — nothing declares which stops the autonomous run suspends')"

# Children of the pipeline, taken from its own child-workflow lists.
PIPE_CHILDREN="$(sed -n 's/^- `\/\([a-z0-9-]*\)` → .*/\1/p' workflows/phase-pipeline.md 2>/dev/null | sort -u || true)"
for child in $PIPE_CHILDREN; do
  [ -f "workflows/$child.md" ] || continue
  # Wait instructions outside the Guard / Pre-check sections: those are Guard confirmations,
  # which no mode override may suspend and which the region covers with one blanket row.
  BODY="$(awk '/^## (Instructions|Steps|Execution|Step 1)/,0' "workflows/$child.md" 2>/dev/null || true)"
  if printf '%s' "$BODY" | grep -qiE 'wait for (user|answers|approval|confirmation|explicit user decision|the user)|\*\*Wait for user' ; then
    check "PIPE: $child can stop for a user and is named in the Pipeline Overrides region" \
      "$(printf '%s' "$PIPE_OVERRIDE_REGION" | grep -q "$child" && echo pass || echo "workflows/$child.md waits for a user outside its Guard, and phase-pipeline.md ## Pipeline Overrides neither overrides that step nor lists it as a declared stop — the autonomy claim is false for this path")"
  fi
done

check "PIPE: pe-finalize step 5 is answered by the pipeline, not waited on" \
  "$(printf '%s' "$PIPE_OVERRIDE_REGION" | grep -q 'pe-finalize' && printf '%s' "$PIPE_OVERRIDE_REGION" | grep -q 'option 2' && echo pass || echo 'phase-pipeline.md does not auto-answer pe-finalize step 5 — the run stops mid-Execution on the batched Do Now prompt')"

check "PIPE: pv-contract's critical-failure gate is still a declared stop" \
  "$(printf '%s' "$PIPE_OVERRIDE_REGION" | grep -q 'pv-contract' && echo pass || echo 'phase-pipeline.md no longer lists the pv-contract critical-failure gate among the stops it does not override')"

check "PIPE: Guard confirmations are still a declared stop" \
  "$(printf '%s' "$PIPE_OVERRIDE_REGION" | grep -qi 'Guard confirmation' && echo pass || echo 'phase-pipeline.md no longer declares that Guard confirmations remain unsuspended')"

# --batch must mean the same thing in every file that passes or receives it.
check "BATCH: workflow-globals fixes the single meaning of --batch" \
  "$(tr '\n' ' ' < rules/workflow-globals.md 2>/dev/null | tr -s ' ' | grep -q 'record every proposal, prompt for nothing, apply nothing' && echo pass || echo 'workflow-globals does not define --batch, so each caller is free to invent its own meaning')"

for f in workflows/pav-propose.md workflows/pe-execute.md workflows/phase-atomic-validation.md workflows/pv-execute-fixes.md workflows/spec-run.md workflows/phase-pipeline.md; do
  check "BATCH: $(basename $f) passes or receives --batch" \
    "$(grep -q -- '--batch' "$f" 2>/dev/null && echo pass || echo "$f is part of the --batch chain but never names the flag")"
done

check "BATCH: no caller reads --batch as apply-without-asking" \
  "$(grep -rniE '\-\-batch[^.]{0,80}(auto-?apply|apply automatically)|(auto-?apply|apply automatically)[^.]{0,80}--batch' workflows/ rules/ 2>/dev/null | grep -qv 'may not reinterpret' && echo 'a workflow still couples --batch with auto-applying Do Now items, contradicting its definition in workflow-globals' || echo pass)"

check "BATCH: pav-propose still refuses to apply under --batch" \
  "$(grep -q 'do NOT prompt and do NOT apply' workflows/pav-propose.md 2>/dev/null && echo pass || echo 'pav-propose.md step 4 no longer states that --batch applies nothing')"

# ── Group 39: every atomic-validation resume point is a recorded value ─
# "atomic-validation: in-progress → continue from last completed step" named no marker, and
# nothing recorded whether step 2 had run: pav-propose wrote its section only when proposals
# were non-empty, and pav-close is the first thing to set `complete`. A resume between steps 2
# and 3 was not derivable from state.
check "RESUME: pav-propose writes a last_action marker" \
  "$(grep -q 'last_action: pav-propose done' workflows/pav-propose.md 2>/dev/null && echo pass || echo 'pav-propose.md writes no last_action: marker, so a run interrupted after step 2 is indistinguishable from one interrupted before it')"

check "RESUME: pav-propose writes it unconditionally, not only when proposals exist" \
  "$(tr '\n' ' ' < workflows/pav-propose.md 2>/dev/null | tr -s ' ' | grep -q 'Write this line in every mode' && echo pass || echo 'pav-propose.md does not require its last_action: marker in every mode and regardless of whether proposals were found — the marker is then as unreliable as the section it replaces')"

check "RESUME: phase-atomic-validation names the marker it resumes on" \
  "$(grep -q 'pav-propose done' workflows/phase-atomic-validation.md 2>/dev/null && echo pass || echo 'phase-atomic-validation.md Step 0 does not name the pav-propose marker, so its in-progress resume point is still underivable')"

check "RESUME: phase-atomic-validation still names the pav-check marker too" \
  "$(grep -q 'pav-check DONE' workflows/phase-atomic-validation.md 2>/dev/null && echo pass || echo 'phase-atomic-validation.md Step 0 does not name the pav-check DONE marker that resumes at step 2')"

check "RESUME: no resume point is described as 'last completed step' with nothing to read" \
  "$(grep -q 'continue from last completed step' workflows/phase-atomic-validation.md 2>/dev/null && echo 'phase-atomic-validation.md still says continue from last completed step without naming a recorded value' || echo pass)"

# Each marker must have exactly one writer and at least one reader.
for marker_writer in "pav-check DONE:workflows/pav-check.md" "pav-propose done:workflows/pav-propose.md"; do
  marker="${marker_writer%%:*}"; writer="${marker_writer##*:}"
  check "RESUME: the marker '$marker' has a writer" \
    "$(grep -q "$marker" "$writer" 2>/dev/null && echo pass || echo "$writer no longer writes the '$marker' marker that phase-atomic-validation Step 0 resumes on")"
done

check "RESUME: pav-close verifies the marker its predecessor writes" \
  "$(grep -q 'pav-propose done' workflows/pav-close.md 2>/dev/null && echo pass || echo 'pav-close.md Pre-check does not verify the pav-propose marker, so it cannot tell that step 2 ran')"

# ── Group 40: seeded .ai/memory/state.md matches the Entry Format ─────
# The seed shipped ## Active Tasks / ## Deferred / ## Blocked. ## Done — which pv-finalize moves
# completed entries into — was missing, and ## Blocked had neither a writer nor a reader. Every
# task section in the seed must have a workflow that writes it, and every section a workflow
# writes must be in the seed. ## Purpose / ## Structure are the file's own scaffolding, not task
# sections, and are excluded by name.
STATE_SEED='templates/.ai/memory/state.md'
while IFS= read -r sec; do
  case "$sec" in "## Purpose"|"## Structure") continue ;; esac
  WRITERS="$(grep -rlF "$sec" workflows/*.md 2>/dev/null | tr '\n' ' ')"
  check "SEED: '$sec' in the seeded state.md has a writer" \
    "$([ -n "$WRITERS" ] && echo pass || echo "$STATE_SEED seeds $sec but no workflow writes it — /compress-state cannot tell an empty section from a stale one")"
done < <(grep '^## ' "$STATE_SEED" 2>/dev/null)

for sec in '## Active Tasks' '## Done' '## Deferred'; do
  check "SEED: the seeded state.md contains '$sec'" \
    "$(grep -qF "$sec" "$STATE_SEED" 2>/dev/null && echo pass || echo "$STATE_SEED is missing $sec, which a workflow writes into it")"
done

check "SEED: onboard-legacy-project seeds the same sections as the template" \
  "$(grep -qF '## Done' workflows/onboard-legacy-project.md 2>/dev/null && grep -qF '## Deferred' workflows/onboard-legacy-project.md 2>/dev/null && echo pass || echo 'onboard-legacy-project.md File 9 writes a different section set than templates/.ai/memory/state.md — an onboarded project and a seeded one disagree')"

check "SEED: no state.md seed carries a writerless ## Blocked section" \
  "$(grep -qF '## Blocked' "$STATE_SEED" 2>/dev/null || grep -qF '## Blocked' workflows/onboard-legacy-project.md 2>/dev/null && echo 'a ## Blocked section is seeded again although no workflow writes or reads it; blocked is a status: value inside ## Active Tasks' || echo pass)"

check "SEED: the Entry Format documents where a blocked task lives" \
  "$(tr '\n' ' ' < rules/workflow-reference.md 2>/dev/null | tr -s ' ' | grep -q 'There is no .## Blocked. section' && echo pass || echo 'workflow-reference Entry Format does not say where a blocked task is recorded, so dropping ## Blocked from the seed is undocumented')"

check "LOG: canonical tables match effective runtime contract" \
  "$(validate_run_log_contract >/dev/null && echo pass || validate_run_log_contract)"

# ── Group 41: the quick-flow gate has no fuzzy condition ──────────────
# quick-flow calls the gate "a checklist, not a judgement call", yet condition 1 read "roughly 3
# files or fewer" in quick-flow and pv-classify-fixes and "≤ ~3 files" in workflow-globals — the
# one condition that decides the tier for most tasks and the shared/dedicated split for most
# fixes. Same bound, same words, in all three places.
QUICK_BOUND='3 or fewer files, counting test files'
for f in rules/quick-flow.md rules/workflow-globals.md workflows/pv-classify-fixes.md workflows/pd-analyze.md; do
  check "GATE: $f states the exact file bound" \
    "$(grep -qF "$QUICK_BOUND" "$f" 2>/dev/null && echo pass || echo "$f does not state gate condition 1 as '$QUICK_BOUND' — the three copies of the gate disagree")"
  check "GATE: $f uses no fuzzy qualifier on the file count" \
    "$(grep -qE 'roughly [0-9]+ files|~ ?[0-9]+ files|≤ ?~' "$f" 2>/dev/null && echo "$f still hedges the file count ('roughly' / '~'), which contradicts quick-flow's claim that the gate is a checklist and not a judgement call" || echo pass)"
done

check "GATE: quick-flow still calls the gate a checklist" \
  "$(grep -q 'checklist, not a judgement call' rules/quick-flow.md 2>/dev/null && echo pass || echo 'quick-flow no longer states that the gate is a checklist — the exact bound in condition 1 loses the rule it serves')"

check "GATE: condition 1 points at the promotion path" \
  "$(tr '\n' ' ' < rules/quick-flow.md 2>/dev/null | tr -s ' ' | grep -qE 'a fourth file fails the condition.*Mid-flight escalation' && echo pass || echo 'quick-flow condition 1 does not cross-reference ## Mid-flight escalation, so the exact bound reads as a trap rather than as the gate working')"

# ── Group 42: composite integration failures have an approval gate ────
# Step 3 said "for each approved fix" while nothing in the workflow produced an approval — no
# prompt, no recorded decision, no approve/defer split. The gate could not be evaluated from any
# available input. Referencing an approval and producing one must travel together.
CCV='workflows/phase-composite-validation.md'
CCV_FLAT="$(tr '\n' ' ' < "$CCV" 2>/dev/null | tr -s ' ' || true)"
if grep -qi 'approved' "$CCV" 2>/dev/null; then
  check "APPROVE: phase-composite-validation produces the approval it references" \
    "$(grep -q '### Approved' "$CCV" 2>/dev/null && grep -q '### Deferred' "$CCV" 2>/dev/null && echo pass || echo 'phase-composite-validation.md refers to approved fixes but writes no ### Approved / ### Deferred split — the gate cannot be evaluated')"

  check "APPROVE: the approval is a decision, not an assumption" \
    "$(printf '%s' "$CCV_FLAT" | grep -qiE 'wait for the user.s decision' && echo pass || echo 'phase-composite-validation.md never asks for the approve/defer decision it then acts on')"

  check "APPROVE: the decision is recorded before any directory is created" \
    "$(printf '%s' "$CCV_FLAT" | grep -q 'Write the decision to the parent .state.md. before creating any directory' && echo pass || echo 'phase-composite-validation.md does not record the approve/defer decision before creating fix siblings, so a re-run cannot tell what was already decided')"

  check "APPROVE: an autonomous caller has a declared rule instead of a stop" \
    "$(printf '%s' "$CCV_FLAT" | grep -q 'Approve every .critical. and .important. failure' && echo pass || echo 'phase-composite-validation.md adds a user prompt with no autonomous branch — /phase-pipeline and /spec-run reach it through /pav-close and would stop undeclared')"

  check "APPROVE: the recorded decision section is compression-protected" \
    "$(awk '/^## Protected Sections Contract/,/^## Multi-Phase Spec Rules/' rules/workflow-reference.md 2>/dev/null | grep -qF '## Integration Issues' && echo pass || echo 'workflow-reference Protected Sections Contract does not protect ## Integration Issues (T-XX) — /compress-state may delete the approve/defer decision before the D8 step reads it')"

  check "APPROVE: the workflow still refuses to auto-advance after creating siblings" \
    "$(grep -q '\*\*Stop. Do not auto-advance.\*\*' "$CCV" 2>/dev/null && echo pass || echo 'phase-composite-validation.md lost its closing Stop — an approval gate that then auto-advances defeats the point')"
fi

# ── Summary ──────────────────────────────────────────────────────────


# ── Group 43: the quick tier can finish Discovery and Execution ───────
# Group 30 proved the quick tier reaches the END of Validation. It could not reach the end of
# the two phases before it: /pd-finalize stopped on a missing ## Solution Design (never written
# on the quick tier) and /pe-finalize stopped on a missing ## Execution Report (/pe-execute
# never runs on the quick tier). Both are the same shape as the pv-finalize dead-end: a Guard
# that hard-requires an artifact its own tier skips. Every phase-final workflow the quick tier
# reaches needs an explicit exception, not an inference.
PDF_FLAT="$(tr '\n' ' ' < workflows/pd-finalize.md 2>/dev/null | tr -s ' ' || true)"
check "QUICK: pd-finalize does not require ## Solution Design on the quick tier" \
  "$(printf '%s' "$PDF_FLAT" | grep -qE 'Exception — .flow: quick' && echo pass || echo 'pd-finalize.md Guard stops when ## Solution Design → ### Decision is missing — the quick tier never writes it, so Discovery can never be marked complete')"

check "QUICK: pd-finalize verifies the quick contract instead" \
  "$(grep -q '## Contract (quick)' workflows/pd-finalize.md 2>/dev/null && echo pass || echo 'pd-finalize.md skips the ## Solution Design check on the quick tier but verifies nothing in its place — a quick task could reach discovery: complete with no contract at all')"

check "QUICK: pd-finalize skips the per-subtask verification that has no subtasks" \
  "$(printf '%s' "$PDF_FLAT" | grep -qE 'skip steps 1, 2 and 4b' && echo pass || echo 'pd-finalize.md still runs its plan.md and per-T-XX verification on the quick tier, which has neither a plan.md nor a T-XX directory')"

check "QUICK: pd-finalize does not archive on the quick tier" \
  "$(printf '%s' "$PDF_FLAT" | grep -qE '.flow: quick. — skip this step' && echo pass || echo 'pd-finalize.md invokes /pd-archive on the quick tier, although quick-flow lists pd-archive among the steps that tier skips and there are no Variants or Rejected sections to archive')"

PEF_FLAT="$(tr '\n' ' ' < workflows/pe-finalize.md 2>/dev/null | tr -s ' ' || true)"
check "QUICK: pe-finalize does not require ## Execution Report on the quick tier" \
  "$(printf '%s' "$PEF_FLAT" | grep -qE 'If .flow: quick., there are no T-XX' && echo pass || echo 'pe-finalize.md stops when ## Execution Report is missing — /pe-execute never runs on the quick tier, so execution can never be marked complete')"

check "QUICK: pe-finalize reads the quick GREEN record in its place" \
  "$(grep -q '## TDD (quick)' workflows/pe-finalize.md 2>/dev/null && echo pass || echo 'pe-finalize.md skips the ## Execution Report read on the quick tier but reads no substitute — nothing then verifies the quick task ever reached GREEN')"

# Every phase-final workflow the quick tier reaches must name the tier at all.
for f in workflows/pd-finalize.md workflows/pe-finalize.md workflows/pv-finalize.md; do
  check "QUICK: $(basename $f) names the quick tier" \
    "$(grep -q 'flow: quick' "$f" 2>/dev/null && echo pass || echo "$f never mentions flow: quick, so a quick task hits a Guard written for artifacts only the full tier produces")"
done

# ── Group 44: pe-finalize's composite stop is declared by the pipeline ─
# pe-finalize step 2b stops the run when a composite's children are all reviewed while its
# integration-validation is failed. That is reachable in an autonomous run (every integration
# failure optional → all auto-deferred → the field stays failed), and it was in neither the
# override table nor the declared-stops table, so /phase-pipeline's autonomy claim did not
# account for it. Group 38 scans for "wait for user" phrasing and this stop uses none.
check "PIPE: pe-finalize's composite-failure stop appears in the Pipeline Overrides region" \
  "$(printf '%s' "$PIPE_OVERRIDE_REGION" | tr '\n' ' ' | tr -s ' ' | grep -q 'integration-validation: failed' && echo pass || echo 'phase-pipeline.md neither overrides nor declares pe-finalize step 2b, which stops the run when a composite is left with integration-validation: failed')"

check "PIPE: the stop pe-finalize declares still exists in pe-finalize" \
  "$(printf '%s' "$PEF_FLAT" | grep -q 'integration-validation: failed' && echo pass || echo 'pe-finalize.md no longer carries the composite integration-validation: failed stop that phase-pipeline declares — the declared-stops table names a step that is gone')"


# ── Group 45: composite validation obeys the shared-file discipline ───
# /pav-close step 5 reaches /phase-composite-validation from inside the Validator sub-agent,
# and that workflow writes plan.md, the [composite] block, ## Integration Issues (T-XX), and a
# whole D8 sibling directory. orchestration forbids all of it and claimed its table covered
# "every such case in the pipeline today" — the claim was false and the workflow had no
# orchestrated-mode route. Group 36's loop now covers it; these assert the pair of statements
# that make the route implementable.
CCV_FLAT="$(tr '\n' ' ' < workflows/phase-composite-validation.md 2>/dev/null | tr -s ' ' || true)"
check "SHARED: phase-composite-validation names its orchestrated-mode behaviour" \
  "$(printf '%s' "$CCV_FLAT" | grep -q 'Orchestrated mode (./spec-run.) — do not write the shared files' && echo pass || echo 'phase-composite-validation.md does not say what to do under /spec-run, where the Validator reaches it and where writing plan.md, the composite block, and a D8 sibling is forbidden')"

check "SHARED: the D8 sibling creation is routed as a delta in orchestrated mode" \
  "$(printf '%s' "$CCV_FLAT" | grep -q 'In orchestrated mode this whole step is returned as a delta' && echo pass || echo 'phase-composite-validation.md step 3 creates a directory and plan.md rows with no orchestrated-mode route — a sub-agent would be instructed to do what shared-file discipline forbids')"

check "SHARED: orchestration names phase-composite-validation in the delta-return table" \
  "$(printf '%s' "$DELTA_CLAUSE" | grep -q 'phase-composite-validation' && echo pass || echo 'rules/orchestration.md ## Shared-file discipline does not list /phase-composite-validation, although the Validator reaches it and it writes four shared artifacts — the table claims to cover every such case')"

check "SHARED: the composite block is excluded from the own-progress-block carve-out" \
  "$(tr '\n' ' ' < rules/orchestration.md 2>/dev/null | tr -s ' ' | grep -q 'composite.s rollup row is not' && echo pass || echo 'orchestration no longer states that a composite rollup row is not any single sub-agent own row — the carve-out would then appear to license the Validator writing it')"

# ── Group 46: the spec file has controlled completion and reconciliation writes ───────────
# workflow-reference calls the spec immutable and says "Do NOT edit the spec file directly",
# while /pv-finalize step 2.5 prepends completion frontmatter to it. Either the write is a
# named carve-out or the two files contradict each other; a reader cannot obey both.
WFR_FLAT="$(tr '\n' ' ' < rules/workflow-reference.md 2>/dev/null | tr -s ' ' || true)"
SPEC_WRITER="$(grep -q 'Mark spec as complete' workflows/pv-finalize.md 2>/dev/null && echo yes || echo no)"
check "SPEC: the completion-marker write is a named carve-out from immutability" \
  "$([ "$SPEC_WRITER" = no ] && echo pass || (printf '%s' "$WFR_FLAT" | grep -q 'completion marker, not a change to the task statement' && echo pass || echo 'pv-finalize step 2.5 writes to the spec file while workflow-reference calls the spec immutable and forbids editing it directly, with no carve-out naming the completion marker'))"

check "SPEC: active-work amendments preserve the source spec outside controlled exceptions" \
  "$(printf '%s' "$WFR_FLAT" | grep -q 'Do NOT edit the spec file directly. (The completion frontmatter written by ./pv-finalize. step 2.5 is not an amendment' && echo pass || echo 'workflow-reference Amendment procedure no longer scopes its prohibition against the one write pv-finalize performs')"

check "SPEC: content changes still go to state.md, not the spec" \
  "$(printf '%s' "$WFR_FLAT" | grep -q 'Add a .### Description Amendments. section to the task-level .state.md' && echo pass || echo 'workflow-reference no longer routes spec content changes into state.md — the carve-out for the completion marker would then read as general permission to edit specs')"

# ── Group 47: the ADR index Status column has one vocabulary ──────────
# Group 32 fixed the column ORDER. The Status VALUE still had two spellings: the onboarding
# seed wrote "accepted", pv-finalize appends "Accepted". One column, one vocabulary.
ADR_STATUS_BAD="$(grep -rnE '^\|[^|]*\|[^|]*\| *accepted *\|' workflows/ templates/ 2>/dev/null || true)"
check "ADR: no index row uses the lowercase Status value" \
  "$([ -z "$ADR_STATUS_BAD" ] && echo pass || echo "an ADR index row writes Status as lowercase 'accepted' while /pv-finalize appends 'Accepted' — one column cannot carry two vocabularies: $(printf '%s' "$ADR_STATUS_BAD" | head -2 | tr '\n' ' ')")"

check "ADR: pv-finalize still writes the canonical Status value" \
  "$(grep -qE '\| NNNN \| .+ \| Accepted \|' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md no longer appends Accepted as the ADR index Status value that the seeded index and onboarding row are aligned to')"

# ── Group 48: Slice grouping is read from plan.md, not description.md ─
# pd-decompose told the Type 3 path to set a `Slice` field inside each leaf's ## Context. The
# six-section description.md template defines no such field, pd-finalize does not verify one,
# and nothing reads it — the grouping is carried by the plan.md Slice column, which IS
# protected. An instruction to write a field no reader reads is a silent no-op.
check "SLICE: pd-decompose does not write a Slice field into description.md" \
  "$(grep -qE 'Set .Slice. field to the capability name in each leaf.s .## Context' workflows/pd-decompose.md 2>/dev/null && echo 'pd-decompose.md writes a Slice field into ## Context, which is not one of the six sections, is not verified by pd-finalize, and is read by nothing — the grouping lives in the plan.md Slice column' || echo pass)"

check "SLICE: pd-decompose records the capability in the plan.md Slice column" \
  "$(tr '\n' ' ' < workflows/pd-decompose.md 2>/dev/null | tr -s ' ' | grep -q 'Record the capability name in the .Slice. \*\*column\*\*' && echo pass || echo 'pd-decompose.md no longer says where the Type 3 capability name is recorded — the Slice column would be left empty while the Protected Sections Contract protects its values')"

check "SLICE: the Slice column is still protected in workflow-reference" \
  "$(grep -qE '^- .Slice. column values' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference Protected Sections Contract no longer protects the Slice column values that pd-decompose writes')"

# ── Group 41: run log — the store, the helper, and the five writers ───
# The log is the only structured evidence about the pipelines themselves. A pipeline that
# claims to log but names no helper call writes nothing, and the gap is invisible until a
# retro comes up empty.

check "LOG: rules/run-log.md exists" \
  "$([ -f rules/run-log.md ] && echo pass || echo 'rules/run-log.md not found')"

check "LOG: rules/run-log.md is always_on" \
  "$(grep -q 'trigger: always_on' rules/run-log.md 2>/dev/null && echo pass || echo 'rules/run-log.md missing trigger: always_on')"

check "LOG: scripts/log-step.sh exists and is executable" \
  "$([ -x scripts/log-step.sh ] && echo pass || echo 'scripts/log-step.sh is missing or not executable — every logging instruction in the pipelines is then unrunnable')"

# The never-blocks rule is the one property that makes logging safe to add everywhere.
check "LOG: scripts/log-step.sh never fails its caller" \
  "$(grep -qE 'die\(\).*exit 0' scripts/log-step.sh 2>/dev/null && echo pass || echo 'scripts/log-step.sh die() no longer exits 0 — a logging failure could then abort a pipeline step')"

check "LOG: run-log states that logging never blocks a run" \
  "$(grep -qi 'never blocks' rules/run-log.md 2>/dev/null && echo pass || echo 'rules/run-log.md no longer carries the never-blocks rule, which is the precondition for logging from inside every pipeline')"

check "LOG: run-log forbids model-written log lines" \
  "$(grep -qi 'never hand-write' rules/run-log.md 2>/dev/null && echo pass || echo 'rules/run-log.md no longer forbids hand-written log lines — durations would become model guesses and the metrics store worthless')"

check "LOG: run-log names the three helper calls" \
  "$(for c in run-start step run-end; do grep -q "scripts/log-step.sh $c" rules/run-log.md || exit 1; done && echo pass || echo 'rules/run-log.md does not document all three of run-start / step / run-end')"

for wf in spec-run phase-pipeline phase-discovery phase-execution phase-validation; do
  check "LOG: $wf declares its run logging" \
    "$(grep -q '## Run Logging' "workflows/$wf.md" 2>/dev/null && echo pass || echo "workflows/$wf.md has no ## Run Logging section, although run-log names it as a producer")"
  check "LOG: $wf opens the run through the helper" \
    "$(grep -q 'scripts/log-step.sh run-start' "workflows/$wf.md" 2>/dev/null && echo pass || echo "workflows/$wf.md never calls scripts/log-step.sh run-start — nothing would be logged")"
  check "LOG: $wf names its pipeline correctly in run-start" \
    "$(grep -q -- "--pipeline $wf" "workflows/$wf.md" 2>/dev/null && echo pass || echo "workflows/$wf.md passes a --pipeline value that is not '$wf'; /retro groups by that field")"
done

# One run per pipeline invocation: phase-pipeline must not open a second run for its children.
check "LOG: phase-pipeline keeps a single run across its child phases" \
  "$(grep -qi 'Do not open a second run' workflows/phase-pipeline.md 2>/dev/null && echo pass || echo 'phase-pipeline.md does not forbid opening a second run when it invokes the phase workflows — one pipeline run would then be split across four files')"

# The Orchestrator owns shared files; a sub-agent calling the helper breaks that discipline.
check "LOG: spec-run keeps log calls with the Orchestrator" \
  "$(tr '\n' ' ' < workflows/spec-run.md 2>/dev/null | tr -s ' ' | grep -qi 'sub-agent never calls' && echo pass || echo 'spec-run.md does not reserve scripts/log-step.sh for the Orchestrator, contradicting the shared-file discipline in orchestration')"

check "LOG: retro is the only declared reader" \
  "$(grep -qi 'sole reader is .\?/retro' rules/run-log.md 2>/dev/null && echo pass || echo 'rules/run-log.md no longer states that /retro is the only reader — a pipeline reading its own telemetry mid-run would make behaviour depend on history')"

check "LOG: retro workflow exists" \
  "$([ -f workflows/retro.md ] && echo pass || echo 'workflows/retro.md not found, although run-log names it as the consumer')"

# ── Group 42: task-artifact validator is reachable from the phases ────
check "TASKVAL: scripts/validate-task.sh exists and is executable" \
  "$([ -x scripts/validate-task.sh ] && echo pass || echo 'scripts/validate-task.sh is missing or not executable')"

for wf in pd-finalize pe-finalize; do
  check "TASKVAL: $wf runs the artifact conformance check" \
    "$(grep -q 'scripts/validate-task.sh' "workflows/$wf.md" 2>/dev/null && echo pass || echo "workflows/$wf.md does not run scripts/validate-task.sh, so nothing checks that the artifacts the phase just wrote conform")"
done

check "TASKVAL: the validator accepts the full atomic-tests vocabulary" \
  "$(for v in not-started red pinned green n-a failed; do grep -q "$v" scripts/validate-task.sh || exit 1; done && echo pass || echo 'scripts/validate-task.sh does not accept every atomic-tests value defined in workflow-globals — a legal status would be reported as a contract failure')"

# ── Group 43: spec reconciliation has a writer and a caller ───────────
check "SPECSYNC: spec-sync workflow exists" \
  "$([ -f workflows/spec-sync.md ] && echo pass || echo 'workflows/spec-sync.md not found')"

check "SPECSYNC: pv-finalize invokes it" \
  "$(grep -qE 'Run ./spec-sync <task-directory>.' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md carries no /spec-sync invocation line, although spec-sync documents itself as being called from there — a doc promise the workflow does not keep. A mention in prose is not a call.')"

check "SPECSYNC: it refuses to weaken a failed acceptance criterion" \
  "$(grep -qi 'failed criterion is a defect' workflows/spec-sync.md 2>/dev/null && echo pass || echo 'spec-sync.md no longer forbids rewriting a failed Acceptance Criterion — the exact abuse spec immutability existed to prevent')"

check "SPECSYNC: spec immutability during a task is still stated" \
  "$(grep -qi 'immutable' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference no longer states that the spec is immutable, which is the rule spec-sync deliberately does not weaken')"

# ── Group 44: ADR — one schema, two writers, no duplicate records ─────
check "ADRNEW: adr-new workflow exists" \
  "$([ -f workflows/adr-new.md ] && echo pass || echo 'workflows/adr-new.md not found')"

check "ADRNEW: it defers to pv-finalize for the schema" \
  "$(grep -q 'pv-finalize' workflows/adr-new.md 2>/dev/null && echo pass || echo 'adr-new.md does not point at pv-finalize for the ADR template and index schema — a second schema would corrupt the index')"

check "ADRNEW: pd-design records the decision when it is made" \
  "$(grep -q 'adr-new' workflows/pd-design.md 2>/dev/null && echo pass || echo 'pd-design.md does not call /adr-new, so an architectural decision is lost whenever the task does not reach pv-finalize')"

check "ADRNEW: pv-finalize promotes a provisional ADR instead of duplicating it" \
  "$(grep -qi 'provisional' workflows/pv-finalize.md 2>/dev/null && echo pass || echo 'pv-finalize.md does not check for a provisional ADR before allocating a new number — a task would end with two ADRs describing one decision')"

# ── Group 45: characterization mode is complete end to end ───────────
# A new atomic-tests value is only safe if every reader knows it. A writer without readers
# leaves a status that later steps treat as unrecognised.
check "CHAR: tdd defines characterization mode" \
  "$(grep -q '## Characterization mode' rules/tdd.md 2>/dev/null && echo pass || echo 'rules/tdd.md has no characterization mode section, although pae-tests offers --characterize')"

check "CHAR: pae-tests accepts --characterize" \
  "$(grep -q -- '--characterize' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md does not accept --characterize')"

check "CHAR: pae-tests verifies the three admission conditions" \
  "$(grep -qi 'admission check' workflows/pae-tests.md 2>/dev/null && echo pass || echo 'pae-tests.md does not gate --characterize on the three conditions in tdd — the mode would become a softer path around RED')"

# Anchored on each reader's actual handling, not on the word: a stray mention elsewhere in
# the file used to satisfy a bare substring check while the handling itself was gone.
check "CHAR: workflow-globals lists pinned in the atomic-tests vocabulary" \
  "$(grep -qE 'Status values for .atomic-tests.:.*[|] .pinned. [|]' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals atomic-tests vocabulary line does not list pinned — the status pae-tests writes would be undefined')"

check "CHAR: workflow-reference lists pinned in the atomic-tests vocabulary" \
  "$(grep -qE 'Status values for .atomic-tests.:.*[|] .pinned. [|]' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'workflow-reference atomic-tests vocabulary line does not list pinned')"

check "CHAR: workflow-reference translates pinned to a plan.md status" \
  "$(grep -qE '^[|] .red. / .pinned. / .n-a.' rules/workflow-reference.md 2>/dev/null && echo pass || echo 'the Status Translation Table has no row covering pinned — pae-finalize could not map it to a plan.md status')"

check "CHAR: pae-implement gates on pinned" \
  "$(grep -qE '^ +- .pinned. . characterization mode' workflows/pae-implement.md 2>/dev/null && echo pass || echo 'pae-implement TDD gate has no pinned branch — a characterized subtask would hit the not-started stop and never be implementable')"

check "CHAR: pae-implement turns the GREEN check into a preservation check" \
  "$(tr '\n' ' ' < workflows/pae-implement.md 2>/dev/null | tr -s ' ' | grep -qi 'preservation check' && echo pass || echo 'pae-implement does not redefine the GREEN check for pinned, so nothing verifies the pinned set still passes after the change')"

check "CHAR: pav-check handles a subtask arriving still pinned" \
  "$(tr '\n' ' ' < workflows/pav-check.md 2>/dev/null | tr -s ' ' | grep -qE '.pinned. reaching validation' && echo pass || echo 'pav-check has no branch for a subtask still marked pinned at validation — an unfinished characterized change would pass unnoticed')"

check "CHAR: a pinned test that turns red blames the change, not the test" \
  "$(grep -qi 'defect in the change' rules/tdd.md 2>/dev/null && echo pass || echo 'rules/tdd.md no longer states that a failing pinned test is a defect in the change — editing the test would become the path of least resistance')"

# ── Group 46: context pack is a cache with a freshness precondition ───
check "CTXPACK: context-pack workflow exists" \
  "$([ -f workflows/context-pack.md ] && echo pass || echo 'workflows/context-pack.md not found')"

check "CTXPACK: workflow-globals permits the substitution only when fresh" \
  "$(grep -qi 'confirmed the pack fresh' rules/workflow-globals.md 2>/dev/null && echo pass || echo 'workflow-globals allows reading the context pack without requiring a freshness check — a stale pack would let an agent work against a superseded principle')"

check "CTXPACK: the pack carries a manifest" \
  "$(grep -q 'manifest' workflows/context-pack.md 2>/dev/null && echo pass || echo 'context-pack.md writes no manifest, so freshness cannot be verified by any reader')"

check "CTXPACK: conditional loads stay out of the pack" \
  "$(grep -q 'integrations.md' workflows/context-pack.md 2>/dev/null && grep -qi 'Never packed' workflows/context-pack.md 2>/dev/null && echo pass || echo 'context-pack.md does not exclude the conditional loads, which would reintroduce the per-step cost the pack exists to remove')"

# ── Group 47: bugfix stays inside the gates it claims to honour ───────
check "BUGFIX: bugfix workflow exists" \
  "$([ -f workflows/bugfix.md ] && echo pass || echo 'workflows/bugfix.md not found')"

check "BUGFIX: it runs the four quick-flow gate conditions" \
  "$(grep -qi 'quick-flow' workflows/bugfix.md 2>/dev/null && grep -qF 'verdict: quick | full' workflows/bugfix.md 2>/dev/null && echo pass || echo 'bugfix.md does not evaluate and record the quick-flow gate, so a shipped-behaviour change could take the light path')"

check "BUGFIX: it hands over to the full path when the gate says full" \
  "$(tr '\n' ' ' < workflows/bugfix.md 2>/dev/null | tr -s ' ' | grep -qi 'stops\*\* and hands over' && echo pass || echo 'bugfix.md does not stop and hand over when the quick gate returns full')"

check "BUGFIX: reproduction precedes the fix" \
  "$(grep -qi 'No fix is written before the defect is reproduced' workflows/bugfix.md 2>/dev/null && echo pass || echo 'bugfix.md no longer requires reproduction before the fix, which is the step that separates it from an ad-hoc change')"

check "BUGFIX: the reproduction becomes the failing test" \
  "$(tr '\n' ' ' < workflows/bugfix.md 2>/dev/null | tr -s ' ' | grep -qi 'reproduction \*is\* the RED test' && echo pass || echo 'bugfix.md does not turn the reproduction into a RED test, so the fix would be unverified and unguarded against regression')"

# ── Script path portability smoke checks ────────────────────────────
test_shell_paths_public_defaults_pass_syntax() {
  local script
  for script in scripts/sync.sh scripts/log-step.sh scripts/setup-new-project.sh scripts/setup-umbrella.sh scripts/setup-all-repos.sh scripts/link-skills.sh scripts/validate-contracts.sh scripts/validate-task.sh; do
    bash -n "$script" || return 1
    if grep -nE '(/|~/|\$HOME/)Documents/projects/' "$script"; then
      echo "$script contains a machine-specific source path"
      return 1
    fi
  done
}

test_shell_paths_relocated_checkout_preserves_overrides() (
  local fixture source_tree alternate script mode target selected output status bad=0
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/script-paths.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  source_tree="$fixture/checkout with spaces"
  alternate="$fixture/alternate source"
  mkdir -p "$fixture/home/.claude/skills/example" "$fixture/work"
  for selected in "$source_tree" "$alternate"; do
    mkdir -p "$selected"/{workflows,rules,principles,scripts,templates/.ai,templates/.ai-umbrella}
    cp scripts/sync.sh scripts/log-step.sh scripts/setup-new-project.sh scripts/setup-umbrella.sh scripts/setup-all-repos.sh scripts/link-skills.sh "$selected/scripts/"
    printf '%s\n' "$selected" > "$selected/templates/.ai/source-marker"
    printf '%s\n' "$selected" > "$selected/templates/.ai-umbrella/source-marker"
    printf '%s\n' 'Umbrella fixture' > "$selected/templates/.ai-umbrella/README.md"
    # Fail at the real preflight boundary so sync cannot deploy anything.
    printf '%s\n' 'printf "source=%s\n" "$(cd "$(dirname "$0")/.." && pwd)"' 'exit 9' > "$selected/scripts/validate-contracts.sh"
  done

  for mode in default empty environment flag equals; do
    selected="$source_tree"
    local -a source_env=(-u WORKFLOWS_SOURCE -u AGENTIC_LOG_ROOT -u ORCHESTRAIL_HOME -u ORCHESTRAIL_LOG_ROOT)
    local -a sync_args=()
    case "$mode" in
      empty) source_env+=(ORCHESTRAIL_HOME=) ;;
      environment) source_env+=(ORCHESTRAIL_HOME="$alternate"); selected="$alternate" ;;
      flag) source_env+=(ORCHESTRAIL_HOME="$fixture/missing"); sync_args=(--from "$alternate"); selected="$alternate" ;;
      equals) source_env+=(ORCHESTRAIL_HOME="$fixture/missing"); sync_args=("--from=$alternate"); selected="$alternate" ;;
    esac
    status=0
    output="$(cd "$fixture/work" && env "${source_env[@]}" HOME="$fixture/home" bash "$source_tree/scripts/sync.sh" "${sync_args[@]}" 2>&1)" || status=$?
    if [ "$status" -ne 1 ] || ! printf '%s\n' "$output" | grep -Fxq "source=$selected"; then
      echo "scripts/sync.sh ($mode): expected selected source to reach failing preflight"
      bad=1
    fi
  done
  if [ -d "$fixture/home/.codeium" ] || [ -d "$fixture/home/.codex" ] || [ -f "$fixture/home/.claude/CLAUDE.md" ]; then
    echo 'scripts/sync.sh crossed the deployment boundary'; bad=1
  fi

  for mode in default empty override; do
    selected="$source_tree/logs"
    local -a log_env=(-u AGENTIC_LOG_ROOT -u ORCHESTRAIL_LOG_ROOT)
    case "$mode" in
      empty) log_env+=(ORCHESTRAIL_LOG_ROOT=) ;;
      override) log_env+=(ORCHESTRAIL_LOG_ROOT="$fixture/custom logs"); selected="$fixture/custom logs" ;;
    esac
    output="$(cd "$fixture/work" && env "${log_env[@]}" HOME="$fixture/home" bash "$source_tree/scripts/log-step.sh" path)"
    if [ "$output" != "$selected" ] || [ -e "$selected" ]; then
      echo "scripts/log-step.sh ($mode): wrong root or read-only path command created a store"; bad=1
    fi
  done

  for script in scripts/setup-new-project.sh scripts/setup-umbrella.sh scripts/setup-all-repos.sh; do
    for mode in default empty override relative; do
      selected="$source_tree"
      local -a setup_env=(-u WORKFLOWS_SOURCE -u ORCHESTRAIL_HOME)
      case "$mode" in
        empty) setup_env+=(ORCHESTRAIL_HOME=) ;;
        override) setup_env+=(ORCHESTRAIL_HOME="$alternate"); selected="$alternate" ;;
        relative) setup_env+=(ORCHESTRAIL_HOME='../../alternate source'); selected="$alternate" ;;
      esac
      target="$fixture/$script $mode"
      mkdir -p "$target"
      if [ "$script" = scripts/setup-all-repos.sh ]; then
        mkdir -p "$target/service with spaces/.git"
      fi
      status=0
      (cd "$target" && env "${setup_env[@]}" HOME="$fixture/home" bash "$source_tree/$script" </dev/null) > "$fixture/setup-output" 2>&1 || status=$?
      if [ "$status" -ne 0 ] || [ "$(cat "$target/.ai/source-marker" 2>/dev/null)" != "$selected" ]; then
        echo "$script ($mode): did not initialize from selected source"; bad=1
      fi
      if [ "$script" = scripts/setup-all-repos.sh ] && [ "$(cat "$target/service with spaces/.ai/source-marker" 2>/dev/null)" != "$selected" ]; then
        echo "$script ($mode): child setup did not use selected source"; bad=1
      fi
      if [ "$script" = scripts/setup-umbrella.sh ]; then
        # Execute the actual suggested command from a child, retaining the caller's overrides.
        local child_command
        child_command="$(sed -n 's/^  cd <service-dir> && //p' "$fixture/setup-output")"
        mkdir -p "$target/service with spaces"
        status=0
        (cd "$target/service with spaces" && env "${setup_env[@]}" HOME="$fixture/home" bash -c "${child_command:-exit 1}" </dev/null) > "$fixture/child-output" 2>&1 || status=$?
        if [ "$status" -ne 0 ] || [ "$(cat "$target/service with spaces/.ai/source-marker" 2>/dev/null)" != "$selected" ]; then
          echo "$script ($mode): suggested child command did not use selected source"; bad=1
        fi
      fi
    done
  done

  # An explicitly selected missing tree must fail instead of seeding from another tree.
  for script in scripts/sync.sh scripts/setup-new-project.sh scripts/setup-umbrella.sh scripts/setup-all-repos.sh; do
    target="$fixture/missing source $script"
    mkdir -p "$target"
    status=0
    (cd "$target" && env -u WORKFLOWS_SOURCE ORCHESTRAIL_HOME="$fixture/missing tree" HOME="$fixture/home" bash "$source_tree/$script" </dev/null) > "$fixture/missing-output" 2>&1 || status=$?
    if [ "$status" -eq 0 ] || [ -e "$target/.ai/source-marker" ]; then
      echo "$script: missing source override did not fail without initialization"; bad=1
    fi
    if [ "$script" = scripts/sync.sh ]; then
      if grep -Fq "source=$source_tree" "$fixture/missing-output"; then
        echo 'scripts/sync.sh: missing source override reached fallback preflight'; bad=1
      fi
      if ! grep -Fq "$fixture/missing tree" "$fixture/missing-output" ||
        ! grep -Eiq 'not found|no such|missing|not a .*tree|cannot|invalid' "$fixture/missing-output"; then
        echo 'scripts/sync.sh: missing source override lacks a source-resolution diagnostic'; bad=1
      fi
    fi
  done

  target="$fixture/skill project"
  mkdir -p "$target/.claude/skills"
  (cd "$target" && env HOME="$fixture/home" bash "$source_tree/scripts/link-skills.sh") > "$fixture/link-output" 2>&1 || bad=1
  if [ ! -L "$target/.claude/skills/example" ] || [ ! -d "$target/.claude/skills/example" ]; then
    echo 'scripts/link-skills.sh: relocated invocation did not link the configured home skills'; bad=1
  fi
  [ "$bad" -eq 0 ]
)

check "test_shell_paths_public_defaults_pass_syntax" \
  "$(test_shell_paths_public_defaults_pass_syntax && echo pass || echo 'shell sources contain private paths or invalid Bash')"
check "test_shell_paths_relocated_checkout_preserves_overrides" \
  "$(test_shell_paths_relocated_checkout_preserves_overrides && echo pass || echo 'relocation or override behavior failed')"

test_runtime_instructions_public_configuration_uses_orchestrail() {
  local file bad=0
  local -a helper_docs=(rules/run-log.md workflows/phase-discovery.md workflows/phase-execution.md
    workflows/phase-pipeline.md workflows/phase-validation.md workflows/spec-run.md
    workflows/pd-finalize.md workflows/pe-finalize.md .ai/principles/coding.md docs/USAGE.md)
  for file in "${helper_docs[@]}" .ai/context/environment.md; do
    if ! grep -Fq 'ORCHESTRAIL_HOME' "$file"; then
      echo "$file: missing public source-root variable"; bad=1
    fi
  done
  for file in rules/run-log.md workflows/retro.md .ai/context/environment.md .ai/principles/coding.md; do
    if ! grep -Fq 'ORCHESTRAIL_LOG_ROOT' "$file"; then
      echo "$file: missing public log-root variable"; bad=1
    fi
  done
  for file in "${helper_docs[@]}" workflows/retro.md .ai/context/environment.md .ai/context/runbook.md; do
    if grep -nE 'WORKFLOWS_SOURCE|AGENTIC_LOG_ROOT|(~|\$HOME)/\.config/agentic[_-]workflows/' "$file"; then
      echo "$file: obsolete runtime configuration remains"; bad=1
    fi
  done
  if ! grep -Fq '~/.config/orchestrail/' .ai/context/environment.md; then
    echo 'Environment instructions omit the public configuration root'; bad=1
  fi
  [ "$bad" -eq 0 ]
}

check "test_runtime_instructions_public_configuration_uses_orchestrail" \
  "$(test_runtime_instructions_public_configuration_uses_orchestrail && echo pass || echo 'public runtime variables and configuration instructions are incomplete')"

# ── Public examples ─────────────────────────────────────────────────

test_public_examples_umbrella_uses_neutral_services() {
  local file required bad=0
  for file in docs/USAGE.md templates/.ai-umbrella/README.md; do
    for required in acme-platform/ service-api service-worker service-frontend infra; do
      if ! grep -Fq -- "$required" "$file"; then
        echo "$file: missing neutral umbrella entry $required"
        bad=1
      fi
    done
  done
  for required in '~/projects/acme-platform' ; do
    if ! grep -Fq -- "$required" docs/USAGE.md; then
      echo 'docs/USAGE.md: missing neutral umbrella setup path'; bad=1
    fi
  done
  if ! grep -Fq -- '/retro --project ~/projects/acme-platform' workflows/retro.md; then
    echo 'workflows/retro.md: missing neutral project filter example'; bad=1
  fi
  [ "$bad" -eq 0 ]
}

test_public_examples_quick_gate_preserves_fictional_outcomes() {
  local rejected accepted required bad=0
  rejected="$(sed -n '/^## Worked example A /,/^## Worked example B /p' rules/quick-flow.md)"
  accepted="$(sed -n '/^## Worked example B /,$p' rules/quick-flow.md)"
  for required in 'fictional' 'export_builder.py' 'export_cache.py' 'export_view.tsx' 'tests/test_export_builder.py' 'Condition 1' '**FAIL**' 'Condition 2' 'Condition 3' 'flow: full'; do
    if ! printf '%s\n' "$rejected" | grep -Fq -- "$required"; then
      echo "Rejected example: missing $required"; bad=1
    fi
  done
  for required in 'fictional' 'queue_diagnostics.py' 'INFO' 'DEBUG' 'one file' 'flow: quick' 'level: none'; do
    if ! printf '%s\n' "$accepted" | grep -Fq -- "$required"; then
      echo "Accepted example: missing $required"; bad=1
    fi
  done
  if printf '%s\n' "$accepted" | grep -Eiq 'invoice|IPN|[1-5][0-9]{2}'; then
    echo 'Accepted example retains private payment-system details'; bad=1
  fi
  [ "$bad" -eq 0 ]
}

test_public_examples_scoped_documents_exclude_private_tokens() {
  local file status bad=0 pattern_file pattern_status=0
  local -a files=(rules/quick-flow.md rules/tdd.md rules/workflow-reference.md workflows/retro.md)
  pattern_file="$(hygiene_patterns_path)" || pattern_status=$?
  [ "$pattern_status" -eq 0 ] || return "$pattern_status"
  while IFS= read -r -d '' file; do
    files+=("$file")
  done < <(find docs templates -type f -name '*.md' -print0)
  if [ ! -r "$pattern_file" ] || ! grep -qEv '^[[:space:]]*(#|$)' "$pattern_file"; then
    echo 'Public example pattern file is missing, unreadable, or empty'; return 1
  fi
  for file in "${files[@]}"; do
    status=0
    grep -Fiq -f <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$pattern_file") -- "$file" || status=$?
    case "$status" in
      0) echo "$file: contains a forbidden public-example token"; bad=1 ;;
      1) ;;
      *) echo "$file: forbidden-token scan failed"; bad=1 ;;
    esac
  done
  for file in docs/analysis/2026-09-16-comparative-analysis.ru.md docs/analysis/2026-09-16-comparative-analysis-tldr.ru.md; do
    if ! grep -Fq 'Redaction legend: Project A, Project B, and Project C are anonymized labels; the mapping is intentionally not recorded.' "$file"; then
      echo "$file: missing English project-redaction legend"; bad=1
    fi
  done
  [ "$bad" -eq 0 ]
}

check "test_public_examples_umbrella_uses_neutral_services" \
  "$(test_public_examples_umbrella_uses_neutral_services && echo pass || echo 'neutral umbrella examples are incomplete')"
check "test_public_examples_quick_gate_preserves_fictional_outcomes" \
  "$(test_public_examples_quick_gate_preserves_fictional_outcomes && echo pass || echo 'fictional quick-gate teaching outcomes are incomplete')"
check "test_public_examples_scoped_documents_exclude_private_tokens" \
  "$(test_public_examples_scoped_documents_exclude_private_tokens && echo pass || { status=$?; if [ "$status" -eq 2 ]; then echo 'skip: no local private hygiene pattern file is configured'; else echo 'scoped public documents require redaction'; fi; })"

# ── Public hygiene smoke checks ─────────────────────────────────────

test_public_hygiene_fixture_scans_fail_closed() (
  local fixture validator repo output status name real_git
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/public-hygiene.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  unset ORCHESTRAIL_HYGIENE_DENYLIST
  validator="$fixture/runner/scripts/validate-contracts.sh"
  mkdir -p "$fixture/runner"
  git archive HEAD | tar -x -C "$fixture/runner" || return 1
  repo="$fixture/repository with spaces"
  real_git="$(command -v git)" || return 1
  # Omit this smoke group in the copied runner to prevent recursive fixture tests.
  sed '/^# ── Public hygiene smoke checks /,/^# ── End public hygiene smoke checks /d' scripts/validate-contracts.sh > "$validator"
  mkdir -p "$repo/.ai/specs/completed" "$repo/logs" "$repo/nested" "$fixture/bin"
  "$real_git" init -q "$repo" || return 1
  printf '%s\n' 'different-marker' > "$repo/scrub-denylist.txt"
  printf '%s\n' 'forbidden-marker' 'literal.[x]' > "$fixture/private-patterns.txt"
  printf '%s\n' 'FORBIDDEN-MARKER' > "$repo/.ai/specs/completed/00-sensitive-data-scrub.md"
  printf '%s\n' 'Ordinary public content; literalax is allowed.' > "$repo/clean file.md"
  "$real_git" -C "$repo" add -- scrub-denylist.txt .ai/specs/completed/00-sensitive-data-scrub.md "clean file.md" || return 1

  fixture_scan() {
    local expected="$1" label="$2"
    shift 2
    status=0
    output="$(ORCHESTRAIL_HYGIENE_DENYLIST="${ORCHESTRAIL_HYGIENE_DENYLIST:-$fixture/private-patterns.txt}" bash "$validator" --hygiene-only --root "$repo" "$@" 2>&1)" || status=$?
    if { [ "$expected" = pass ] && [ "$status" -ne 0 ]; } || { [ "$expected" = fail ] && [ "$status" -eq 0 ]; }; then
      printf '%s: expected %s, exit %s\n' "$label" "$expected" "$status"
      return 1
    fi
  }

  fixture_scan pass 'clean tree and exact source exception' || return 1
  if output="$(env -u ORCHESTRAIL_HYGIENE_DENYLIST XDG_CONFIG_HOME="$fixture/no-config" \
      bash "$validator" --hygiene-only --root "$repo" 2>&1)"; then
    echo 'Standalone hygiene scan passed without a configured pattern file'; return 1
  fi
  if ! grep -Fq 'Hygiene patterns are not configured' <<< "$output"; then
    echo 'Unconfigured scanner did not fail at the configuration guard'; return 1
  fi
  printf '%s\n' 'different-marker' > "$repo/scrub-denylist.txt"
  printf '%s\n' 'forbidden-marker' 'literal.[x]' > "$fixture/private-patterns.txt"
  printf '%s\n' 'prefix-FoRbIdDeN-MaRkEr-suffix' > "$repo/clean file.md"
  ORCHESTRAIL_HYGIENE_DENYLIST="$fixture/private-patterns.txt" fixture_scan fail 'environment pattern list selected' || return 1
  printf '%s\n' 'Public content' > "$repo/clean file.md"
  ORCHESTRAIL_HYGIENE_DENYLIST="$fixture/private-patterns.txt" fixture_scan pass 'environment pattern list with clean content' || return 1
  printf '%s\n' 'different-marker' > "$repo/scrub-denylist.txt"
  for name in 'clean file.md' 'scrub-denylist.txt' $'line\nbreak.md' '.ai/new context.md' 'logs/tracked.log' 'nested/scrub-denylist.txt' 'nested/00-sensitive-data-scrub.md'; do
    printf '%s\n' 'prefix-FoRbIdDeN-MaRkEr-suffix' > "$repo/$name"
    "$real_git" -C "$repo" add -- "$name" || return 1
    fixture_scan fail "case-insensitive substring in $name" || return 1
    printf '%s\n' 'Public content' > "$repo/$name"
    fixture_scan pass "restored $name" || return 1
  done
  printf '%s\n' 'prefixliteral.[x]suffix' > "$repo/clean file.md"
  fixture_scan fail 'literal punctuation substring' || return 1
  printf '%s\n' 'Public content' > "$repo/clean file.md"
  ln -s 'prefix-FoRbIdDeN-MaRkEr-suffix' "$repo/linked file" || return 1
  "$real_git" -C "$repo" add -- "linked file" || return 1
  fixture_scan fail 'symlink target text contamination' || return 1
  rm "$repo/linked file"
  ln -s 'public-target' "$repo/linked file" || return 1
  fixture_scan pass 'clean dangling symlink target text' || return 1
  printf '%s\n' 'Public content' > "$repo/clean file.md"
  fixture_scan fail 'missing configured list' --denylist "$fixture/missing.txt" || return 1
  printf '%s\n' '# Comments only' '' > "$fixture/empty.txt"
  fixture_scan fail 'empty configured list' --denylist "$fixture/empty.txt" || return 1
  printf '%s\n' 'different-marker' > "$fixture/alternate.txt"
  printf '%s\n' 'DIFFERENT-MARKER' > "$repo/clean file.md"
  fixture_scan fail 'configured list selected' --denylist "$fixture/alternate.txt" || return 1
  printf '%s\n' 'Public content' > "$repo/clean file.md"
  fixture_scan pass 'configured list with clean content' --denylist "$fixture/alternate.txt" || return 1
  # Inject a failed readability check only in the scanner subprocess. Mode 000
  # remains readable to root, so filesystem permissions cannot drive these cases.
  cat > "$fixture/unreadable.bash" <<'EOF'
function [ {
  if [[ $# -eq 3 && $1 == -r && $2 == "${HYGIENE_UNREADABLE:-}" ]]; then
    return 1
  fi
  if [[ $# -eq 4 && $1 == '!' && $2 == -r && $3 == "${HYGIENE_UNREADABLE:-}" ]]; then
    return 0
  fi
  builtin [ "$@"
}
EOF
  BASH_ENV="$fixture/unreadable.bash" HYGIENE_UNREADABLE="$fixture/alternate.txt" \
    fixture_scan fail 'unreadable configured list' --denylist "$fixture/alternate.txt" || return 1
  if ! grep -Fq 'Hygiene pattern file is missing or unreadable' <<< "$output"; then
    echo 'Configured-list fixture did not reach the readability guard'; return 1
  fi
  BASH_ENV="$fixture/unreadable.bash" HYGIENE_UNREADABLE="$repo/clean file.md" \
    fixture_scan fail 'unreadable tracked file' || return 1
  if ! grep -Fq 'Hygiene tracked file is missing or unreadable:' <<< "$output"; then
    echo 'Tracked-file fixture did not reach the readability guard'; return 1
  fi
  : > "$repo/clean file.md"
  fixture_scan pass 'empty tracked file' || return 1
  rm "$repo/clean file.md"
  fixture_scan fail 'missing tracked file' || return 1
  printf '%s\n' 'Public content' > "$repo/clean file.md"
  printf '%s\n' '#!/bin/bash' 'exit 2' > "$fixture/bin/git"
  chmod +x "$fixture/bin/git"
  PATH="$fixture/bin:$PATH" fixture_scan fail 'git enumeration failure' || return 1
  rm "$fixture/bin/git"
  printf '%s\n' '#!/bin/bash' 'exit 2' > "$fixture/bin/grep"
  chmod +x "$fixture/bin/grep"
  PATH="$fixture/bin:$PATH" fixture_scan fail 'scanner failure' || return 1
  rm "$fixture/bin/grep"
  mkdir "$fixture/empty repository"
  "$real_git" init -q "$fixture/empty repository" || return 1
  repo="$fixture/empty repository"
  fixture_scan fail 'no tracked files fail closed' --denylist "$fixture/alternate.txt" || return 1
)

test_public_hygiene_repository_preserves_context_and_local_ignores() {
  if git ls-files --error-unmatch -- scrub-denylist.txt >/dev/null 2>&1; then
    echo 'Private hygiene patterns must not be tracked'; return 1
  fi
  if git check-ignore -q -- .ai/public-context.md; then
    echo 'Repository knowledge base must be eligible for tracking'; return 1
  fi
  local file
  for file in logs/runs/local.jsonl .claude/settings.local.json; do
    if ! git check-ignore -q -- "$file"; then
      echo 'Local logs and machine settings must remain ignored'; return 1
    fi
  done
}

check "test_public_hygiene_fixture_scans_fail_closed" \
  "$(test_public_hygiene_fixture_scans_fail_closed && echo pass || echo 'public-hygiene fixture behavior is incomplete')"
check "test_public_hygiene_repository_preserves_context_and_local_ignores" \
  "$(test_public_hygiene_repository_preserves_context_and_local_ignores && echo pass || echo 'repository context, local ignore policy, and private pattern storage are incomplete')"

# ── End public hygiene smoke checks ─────────────────────────────────

# ── Run-log contract smoke checks ───────────────────────────────────
run_log_contract_smoke() {
  python3 - "$REPO_ROOT" "$1" <<'PYCONTRACTTEST'
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile
root, scenario = Path(sys.argv[1]), sys.argv[2]
with tempfile.TemporaryDirectory(prefix='run-log-contract-') as temporary:
    fixture = Path(temporary)
    (fixture/'scripts').mkdir()
    (fixture/'rules').mkdir()
    for name in ('scripts/log-step.sh', 'scripts/validate-contracts.sh', 'rules/run-log.md'):
        shutil.copy2(root/name, fixture/name)
    helper = fixture/'scripts/log-step.sh'
    rule = fixture/'rules/run-log.md'
    original_helper, original_rule = helper.read_text(), rule.read_text()
    def gate(field=None):
        result = subprocess.run(['bash', str(fixture/'scripts/validate-contracts.sh'),
                                 '--run-log-contract-only'], capture_output=True, text=True)
        output = result.stdout + result.stderr
        if field is None:
            assert result.returncode == 0, output
            assert 'run-log contract' in output.lower(), output
        else:
            assert result.returncode != 0, (field, output)
            assert field in output, (field, output)
    gate()
    exported = subprocess.check_output(['bash',str(helper),'contract'], text=True)
    contract = dict(line.split('=',1) for line in exported.splitlines())
    rows = {}
    for line in original_rule.splitlines():
        match = re.fullmatch(r'\| `([^`]+)` \| (.+) \|', line)
        if match:
            try: rows[match[1]] = (line, json.loads(match[2]))
            except json.JSONDecodeError: pass
    assert set(rows) == set(contract), (set(rows),set(contract))
    if scenario == 'tables':
        for heading in ('## Field vocabulary','### Legacy normalization','## Validation and writes',
                        '## Read-only lint'):
            assert heading in original_rule, heading
        for phrase in ('9007199254740991','pinned','unknown','invalid_lines','unavailable',
                       '1.0','1e0','raw:','NEEDS WORKING'):
            assert phrase in original_rule, phrase
    elif scenario == 'mutations':
        for key, (line, value) in rows.items():
            alternatives = ([value[:-1], value+['unexpected'], ['unexpected']+value[1:], value+[value[0]]]
                            if isinstance(value,list) else ['', value+'unexpected'])
            for alternative in alternatives:
                rule.write_text(original_rule.replace(line, f'| `{key}` | {json.dumps(alternative)} |',1))
                gate(key)
            rule.write_text(original_rule.replace(line+'\n','',1)); gate(key)
            rule.write_text(original_rule.replace(line,line+'\n'+line,1)); gate(key)
            rule.write_text(original_rule)
            pattern = re.compile(r'(^  \['+re.escape(key)+r"\]=)'([^']*)'", re.M)
            assert pattern.search(original_helper), key
            raw = contract[key]
            separator = ' ' if key in ('count.fields', 'hook.required') else '|'
            changed = ([separator.join(raw.split(separator)[:-1]), raw+separator+'unexpected',
                        'unexpected'+separator+separator.join(raw.split(separator)[1:]), raw+separator+raw.split(separator)[0]]
                       if isinstance(value,list) else ['', raw+'unexpected'])
            for alternative in changed:
                helper.write_text(pattern.sub(lambda m:m[1]+"'"+alternative+"'", original_helper, count=1))
                gate(key)
            helper.write_text(pattern.sub('',original_helper,count=1)); gate(key)
            helper.write_text(original_helper)
        rule.write_text(original_rule+'\n| `alias.gate.EXTRA` | "fail" |\n'); gate('alias.gate.EXTRA')
        rule.write_text(original_rule)
        helper.write_text(original_helper.replace('declare -Ar RUN_LOG_CONTRACT=(',
                          "declare -Ar RUN_LOG_CONTRACT=(\n  [alias.gate.EXTRA]='fail'",1))
        gate('alias.gate.EXTRA'); helper.write_text(original_helper)
        rule.write_text(original_rule.replace('### Legacy normalization','### Missing normalization',1))
        gate('normalization')
    elif scenario == 'effective':
        # Change the value exported by the actual shared definition; docs follow it.
        key='step.tests'; line,value=rows[key]
        helper.write_text(original_helper.replace("[step.tests]='red|green|n-a|failed|not-run|pinned'",
                            "[step.tests]='red|green|n-a|failed|not-run|pinned|custom-test'",1))
        rule.write_text(original_rule.replace(line,f'| `{key}` | {json.dumps(value+["custom-test"])} |',1))
        gate()
        environment=dict(os.environ, ORCHESTRAIL_LOG_ROOT=str(fixture/'store'), ORCHESTRAIL_HOME=str(root))
        def invoke(*args):
            return subprocess.run(['bash',str(helper),*args],env=environment,capture_output=True,text=True)
        run=invoke('run-start','--pipeline','contract-probe').stdout.strip()
        assert re.fullmatch('[0-9a-f]{8}',run),run
        invoke('step','--run',run,'--step','dry-run','--outcome','ok','--tests','custom-test')
        lint=invoke('lint','--all')
        assert 'invalid-enum' not in lint.stdout,lint.stdout
        assert any(json.loads(line).get('tests')=='custom-test'
                   for file in (fixture/'store/runs').glob('*.jsonl') for line in file.read_text().splitlines())
        helper.write_text(original_helper); rule.write_text(original_rule)
        # Identical but overbroad regexes on both sides still violate the boundary contract.
        key='alias.gate.NEEDS_WORK_PREFIX'; line,value=rows[key]
        broad='^NEEDS WORK.*$'
        helper.write_text(original_helper.replace(value,broad,1))
        rule.write_text(original_rule.replace(line,f'| `{key}` | {json.dumps(broad)} |',1))
        gate(key)
PYCONTRACTTEST
}
test_run_log_contract_documents_effective_runtime_tables() { run_log_contract_smoke tables; }
test_run_log_contract_rejects_bidirectional_vocabulary_drift() { run_log_contract_smoke mutations; }
test_run_log_contract_checks_shared_definitions_and_prefix_boundary() { run_log_contract_smoke effective; }
check "test_run_log_contract_documents_effective_runtime_tables" \
  "$(test_run_log_contract_documents_effective_runtime_tables && echo pass || echo 'run-log contract tables are missing or incomplete')"
check "test_run_log_contract_rejects_bidirectional_vocabulary_drift" \
  "$(test_run_log_contract_rejects_bidirectional_vocabulary_drift && echo pass || echo 'run-log contract drift was not rejected by field')"
check "test_run_log_contract_checks_shared_definitions_and_prefix_boundary" \
  "$(test_run_log_contract_checks_shared_definitions_and_prefix_boundary && echo pass || echo 'effective definitions or prefix boundaries differ')"
# ── End run-log contract smoke checks ───────────────────────────────

# ── Run-log producer smoke checks ───────────────────────────────────
prepare_run_log_fixture() {
  local fixture="$1" helper="$1/helper"
  mkdir -p "$helper/scripts" "$helper/workflows" || return 1
  cp scripts/log-step.sh "$helper/scripts/log-step.sh" || return 1
  cp -R workflows/. "$helper/workflows/" || return 1
}

assert_one_redacted_warning() {
  local warning_file="$1" raw_value="${2:-}"
  [ "$(wc -l < "$warning_file")" -eq 1 ] || return 1
  [ -z "$raw_value" ] || ! grep -Fq -- "$raw_value" "$warning_file"
}

test_run_log_dash_leading_operands_preserve_text_and_reject_known_options() {
  python3 - "$PWD/scripts/log-step.sh" <<'PYOPERANDS'
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='operand boundaries ') as temporary:
    fixture = Path(temporary)
    home = fixture / 'helper home'
    (home / 'scripts').mkdir(parents=True)
    (home / 'workflows').mkdir()
    (home / 'workflows/fixture-known.md').write_text('Fixture workflow\n')
    helper = home / 'scripts/log-step.sh'
    shutil.copyfile(sys.argv[1], helper)
    store = fixture / 'log store'
    env = dict(os.environ, ORCHESTRAIL_HOME=str(home), ORCHESTRAIL_LOG_ROOT=str(store))
    def invoke(*args):
        result = subprocess.run(['bash', str(helper), *args], env=env,
                                capture_output=True, timeout=2)
        assert result.returncode == 0, (args, result)
        return result
    def snapshot():
        return (store.exists(), {str(p.relative_to(store)):
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
                for p in store.rglob('*')})
    def reject(args, warning):
        before = snapshot()
        result = invoke(*args)
        assert result.stdout == b'' and result.stderr == warning.encode(), (args, result)
        assert snapshot() == before, ('rejection changed storage', args)
    known = ('--pipeline', '--project', '--task', '--spec', '--flow', '--flags',
             '--run', '--step', '--outcome', '--stops', '--escalations', '--decisions',
             '--questions', '--gate', '--tests', '--fix-tasks', '--promoted',
             '--amendments', '--files', '--subtask', '--blocker', '--note')
    for option in known:
        reject(('run-start', '--pipeline', 'fixture', '--flags', option),
               'log-step: run-start flags missing-operand\n')
    reject(('run-start', '--pipeline', 'fixture', '--private-option', 'private text'),
           'log-step: run-start argument invalid-option\n')
    for flags in ('--step-by-step', '--allow-pr --dry-run'):
        result = invoke('run-start', '--pipeline', '--custom-pipeline',
                        '--project', '--custom-project', '--task', '--custom-task',
                        '--spec', '--custom-spec', '--flow', '--custom-flow', '--flags', flags)
        run = result.stdout.decode().strip()
        assert re.fullmatch('[0-9a-f]{8}', run) and result.stderr == b'', ('documented flags rejected', flags, result)
        file = next(p for p in (store / 'runs').glob('*.jsonl') if run in p.name)
        file.with_suffix('.md').write_text('Existing digest fixture\n')
        for option in known:
            for event, prefix, field in (
                    ('run-start', ('--pipeline', 'fixture', '--flags'), 'flags'),
                    ('step', ('--run', run, '--step', 'fixture-known', '--outcome', 'ok', '--note'), 'note'),
                    ('run-end', ('--run', run, '--outcome', 'completed', '--note'), 'note')):
                reject((event, *prefix, option), f'log-step: {event} {field} missing-operand\n')
        for event, prefix in (
                ('run-start', ('--pipeline', 'fixture')),
                ('step', ('--run', run, '--step', 'fixture-known', '--outcome', 'ok')),
                ('run-end', ('--run', run, '--outcome', 'completed'))):
            reject((event, *prefix, '--private-option', 'private text'),
                   f'log-step: {event} argument invalid-option\n')
        result = invoke('step', '--run', run, '--step', 'fixture-known', '--outcome', 'ok',
                        '--note', '--custom-note', '--blocker', '--custom-blocker', '--subtask', '--custom-subtask')
        assert result.stdout == b'' and result.stderr == b'', result
        result = invoke('run-end', '--run', run, '--outcome', 'completed', '--note', '--custom-end-note')
        assert result.stdout == b'' and result.stderr == b'', result
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        assert [row['event'] for row in rows] == ['run-start', 'step', 'run-end'], rows
        assert [row['seq'] for row in rows] == [0, 1, 2], rows
        assert all(row['flow'] == '--custom-flow' and row['pipeline'] == '--custom-pipeline' for row in rows)
        assert {key: rows[0][key] for key in ('project', 'task', 'spec', 'flags')} == {
            'project': '--custom-project', 'task': '--custom-task', 'spec': '--custom-spec', 'flags': flags}
        assert {key: rows[1][key] for key in ('note', 'blocker', 'subtask')} == {
            'note': '--custom-note', 'blocker': '--custom-blocker', 'subtask': '--custom-subtask'}
        assert rows[2]['note'] == '--custom-end-note'
        assert not (store / '.active' / run).exists()
PYOPERANDS
}

test_run_log_workflow_directory_permissions_report_verification_availability() {
  python3 - "$PWD/scripts/log-step.sh" <<'PYPERMISSIONS'
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile, traceback
# Use a direct temporary root so a privileged runner can drop all privileges
# without requiring access through the acceptance runner's private ancestors.
with tempfile.TemporaryDirectory(prefix='workflow permissions ', dir='/tmp') as temporary:
    fixture = Path(temporary)
    home = fixture / 'helper home'
    (home / 'scripts').mkdir(parents=True)
    workflows = home / 'workflows'
    workflows.mkdir()
    (workflows / 'fixture-known.md').write_text('Fixture workflow\n')
    helper = home / 'scripts/log-step.sh'
    shutil.copyfile(sys.argv[1], helper)
    if os.geteuid() == 0:
        for path in (fixture, *fixture.rglob('*')):
            os.chown(path, 65534, 65534)
    def exercise():
        store = fixture / 'log store'
        env = dict(os.environ, ORCHESTRAIL_HOME=str(home), ORCHESTRAIL_LOG_ROOT=str(store))
        def invoke(*args):
            result = subprocess.run(['bash', str(helper), *args], env=env,
                                    capture_output=True, timeout=2, cwd=fixture)
            assert result.returncode == 0, (args, result)
            return result
        result = invoke('run-start', '--pipeline', 'fixture', '--flow', 'custom flow')
        run = result.stdout.decode().strip()
        assert re.fullmatch('[0-9a-f]{8}', run) and result.stderr == b'', result
        file = next((store / 'runs').glob('*.jsonl'))
        expected_steps = []
        try:
            for mode, readable, searchable in ((0o700, True, True), (0o400, True, False),
                                                (0o100, False, True), (0o000, False, False)):
                workflows.chmod(mode)
                probe = subprocess.run(['bash', '-c', '[ -r "$1" ]; r=$?; [ -x "$1" ]; x=$?; printf "%s %s" "$r" "$x"',
                                        'permission-probe', str(workflows)], capture_output=True, cwd=fixture)
                assert probe.returncode == 0 and probe.stdout == f'{int(not readable)} {int(not searchable)}'.encode(), (
                    'fixture did not enforce actual read/search permissions', mode, probe)
                for name in ('fixture-known', 'batch-gate', 'subtask', 'dry-run', 'unknown-workflow'):
                    result = invoke('step', '--run', run, '--step', name, '--outcome', 'ok', '--note', 'exact note')
                    warning = (b'log-step: step-name verification unavailable\n' if not (readable and searchable)
                               else b'log-step: step name is not in the current workflow list\n' if name == 'unknown-workflow'
                               else b'')
                    assert result.stdout == b'' and result.stderr == warning, (oct(mode), name, result, warning)
                    expected_steps.append(name)
                    row = json.loads(file.read_text().splitlines()[-1])
                    assert {key: row[key] for key in ('event', 'step', 'outcome', 'note', 'flow', 'seq')} == {
                        'event': 'step', 'step': name, 'outcome': 'ok', 'note': 'exact note',
                        'flow': 'custom flow', 'seq': len(expected_steps)}, row
            workflows.chmod(0o700)
            workflows.rename(home / 'unavailable workflows')
            for name in ('fixture-known', 'dry-run', 'unknown-workflow'):
                result = invoke('step', '--run', run, '--step', name, '--outcome', 'ok', '--note', 'exact note')
                assert result.stdout == b'' and result.stderr == b'log-step: step-name verification unavailable\n', result
                expected_steps.append(name)
            rows = [json.loads(line) for line in file.read_text().splitlines()]
            assert [row['step'] for row in rows[1:]] == expected_steps
            assert [row['seq'] for row in rows] == list(range(len(rows)))
            assert all(row['outcome'] == 'ok' and row['note'] == 'exact note' and row['flow'] == 'custom flow' for row in rows[1:])
        finally:
            if workflows.exists():
                workflows.chmod(0o700)
    if os.geteuid() == 0:
        child = os.fork()
        if child == 0:
            try:
                os.setgroups([])
                os.setgid(65534)
                os.setuid(65534)
                exercise()
            except BaseException:
                traceback.print_exc()
                os._exit(1)
            os._exit(0)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0, 'unprivileged permission scenario failed'
    else:
        exercise()
PYPERMISSIONS
}

check "LOGPRODUCER: dash-leading operands persist and known helper options remain options" \
  "$(test_run_log_dash_leading_operands_preserve_text_and_reject_known_options && echo pass || echo 'operand boundaries rejected documented text or consumed known options')"
check "LOGPRODUCER: workflow directory read and search permissions control verification" \
  "$(test_run_log_workflow_directory_permissions_report_verification_availability && echo pass || echo 'directory permissions misclassified verification or changed the event')"

test_run_log_start_rejects_invalid_argument_sets() (
  set -e
  local fixture helper failures=0 status label
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-start.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  export ORCHESTRAIL_HOME="$helper"
  export ORCHESTRAIL_LOG_ROOT="$fixture/store"
  invoke_log() { bash "$helper/scripts/log-step.sh" "$@"; }
  reject_start() {
    label="$1"; shift
    : > "$fixture/stdout"; : > "$fixture/stderr"
    status=0
    timeout 2 bash "$helper/scripts/log-step.sh" run-start "$@" > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
    if [ "$status" -ne 0 ] || [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" raw-probe-741; then
      printf 'run-start accepted or exposed invalid %s input\n' "$label"
      failures=$((failures + 1))
    fi
    if [ "$(find "$fixture/store/runs" -type f -name '*.jsonl' 2>/dev/null | wc -l)" -ne 0 ] ||
       [ "$(find "$fixture/store/.active" -type f 2>/dev/null | wc -l)" -ne 0 ]; then
      printf 'run-start changed storage for invalid %s input\n' "$label"
      failures=$((failures + 1))
    fi
  }
  reject_start missing-required
  reject_start unknown-option --pipeline phase-discovery --surprise raw-probe-741
  reject_start duplicate-option --pipeline phase-discovery --pipeline phase-execution
  reject_start missing-operand --pipeline
  reject_start flag-as-operand --pipeline --flow full
  [ "$failures" -eq 0 ]
)

test_run_log_step_rejects_invalid_fields_without_mutation() (
  set -e
  local fixture helper run file active failures=0 status label before_log before_active after_log after_active
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-step.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  export ORCHESTRAIL_HOME="$helper"
  export ORCHESTRAIL_LOG_ROOT="$fixture/store"
  invoke_log() { bash "$helper/scripts/log-step.sh" "$@"; }
  run="$(invoke_log run-start --pipeline phase-execution --flow full 2> "$fixture/start.err")" || return 1
  file="$(invoke_log path --run "$run")" || return 1
  active="$fixture/store/.active/$run"
  reject_step() {
    label="$1"; shift
    before_log="$(sha256sum "$file" | awk '{print $1}')"
    before_active="$(sha256sum "$active" | awk '{print $1}')"
    : > "$fixture/stdout"; : > "$fixture/stderr"
    status=0
    timeout 2 bash "$helper/scripts/log-step.sh" step --run "$run" --step pae-tests "$@" > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
    after_log="$(sha256sum "$file" | awk '{print $1}')"
    after_active="$(sha256sum "$active" | awk '{print $1}')"
    if [ "$status" -ne 0 ] || [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" raw-probe-741; then
      printf 'step did not reject or safely report invalid %s input\n' "$label"
      failures=$((failures + 1))
    fi
    if [ "$before_log" != "$after_log" ] || [ "$before_active" != "$after_active" ]; then
      printf 'step changed event or active metadata for invalid %s input\n' "$label"
      failures=$((failures + 1))
    fi
  }
  reject_step outcome --outcome raw-probe-741
  reject_step missing-outcome
  reject_step unknown-option --outcome ok --surprise raw-probe-741
  reject_step gate --outcome ok --gate arbitrary
  reject_step internal-alias-key --outcome ok --gate NEEDS_WORK_EXACT
  reject_step empty-enum --outcome ok --tests ''
  reject_step tests-enum --outcome ok --tests unknown
  reject_step promoted-enum --outcome ok --promoted maybe
  for enum_flag in --outcome --gate --tests --promoted; do
    if [ "$enum_flag" = --outcome ]; then
      reject_step "empty-$enum_flag" "$enum_flag" ''
    else
      reject_step "empty-$enum_flag" --outcome ok "$enum_flag" ''
    fi
  done
  reject_step outcome-case --outcome OK
  reject_step gate-case --outcome ok --gate Pass
  reject_step outcome-whitespace --outcome 'ok '
  reject_step flag-as-operand --outcome --tests green
  for count_flag in --stops --escalations --decisions --questions --fix-tasks --amendments --files; do
    reject_step "malformed-$count_flag" --outcome ok "$count_flag" 01
    reject_step "negative-$count_flag" --outcome ok "$count_flag" -1
    reject_step "fractional-$count_flag" --outcome ok "$count_flag" 1.5
    reject_step "signed-$count_flag" --outcome ok "$count_flag" +1
    reject_step "exponent-$count_flag" --outcome ok "$count_flag" 1e3
    reject_step "oversized-$count_flag" --outcome ok "$count_flag" 9007199254740992
    reject_step "empty-$count_flag" --outcome ok "$count_flag" ''
    reject_step "whitespace-$count_flag" --outcome ok "$count_flag" ' 1'
  done
  reject_step duplicate-option --outcome ok --outcome failed
  reject_step missing-operand --outcome ok --note
  before_log="$(sha256sum "$file" | awk '{print $1}')"
  before_active="$(sha256sum "$active" | awk '{print $1}')"
  : > "$fixture/stdout"; : > "$fixture/stderr"
  status=0
  timeout 2 bash "$helper/scripts/log-step.sh" step --run '../../outside' --step pae-tests --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  after_log="$(sha256sum "$file" | awk '{print $1}')"
  after_active="$(sha256sum "$active" | awk '{print $1}')"
  if [ "$status" -ne 0 ] || [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" '../../outside' ||
     [ "$before_log" != "$after_log" ] || [ "$before_active" != "$after_active" ]; then
    echo 'unsafe run identifier was not rejected before metadata access'
    failures=$((failures + 1))
  fi
  : > "$fixture/stdout"; : > "$fixture/stderr"
  for value in ok blocked failed skipped deferred; do
    invoke_log step --run "$run" --step pae-tests --outcome "$value" > "$fixture/stdout" 2> "$fixture/stderr" || return 1
    [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || failures=$((failures + 1))
  done
  for value in pass fail n-a needs-work ready; do
    invoke_log step --run "$run" --step pae-tests --outcome ok --gate "$value" || return 1
  done
  for value in red green n-a failed not-run pinned; do
    invoke_log step --run "$run" --step pae-tests --outcome ok --tests "$value" || return 1
  done
  for value in yes no; do
    invoke_log step --run "$run" --step pae-tests --outcome ok --promoted "$value" || return 1
  done
  local fakebin="$fixture/fakebin" before_log before_active after_log after_active status
  mkdir -p "$fakebin" || return 1
  printf '#!/bin/sh\nexit 1\n' > "$fakebin/jq"
  chmod +x "$fakebin/jq"
  before_log="$(sha256sum "$file" | awk '{print $1}')"
  before_active="$(sha256sum "$active" | awk '{print $1}')"
  status=0
  PATH="$fakebin:$PATH" invoke_log step --run "$run" --step pae-tests --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  after_log="$(sha256sum "$file" | awk '{print $1}')"
  after_active="$(sha256sum "$active" | awk '{print $1}')"
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" || failures=$((failures + 1))
  [ "$before_log" = "$after_log" ] && [ "$before_active" = "$after_active" ] || failures=$((failures + 1))
  rm -rf "$fakebin"
  invoke_log step --run "$run" --step pae-tests --outcome deferred --stops 0 --escalations 9007199254740991 \
    --decisions 0 --questions 0 --fix-tasks 0 --amendments 0 --files 0 || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
steps = [record for record in records if record.get("event") == "step"]
assert len(steps) == 19, "rejected calls and a failed write must leave only canonical events"
assert [record["seq"] for record in steps] == list(range(1, 20)), "rejections must not advance sequence"
assert [record["outcome"] for record in steps[:5]] == ["ok", "blocked", "failed", "skipped", "deferred"], "step outcomes"
assert [record["gate"] for record in steps[5:10]] == ["pass", "fail", "n-a", "needs-work", "ready"], "gate vocabulary"
assert [record["tests"] for record in steps[10:16]] == ["red", "green", "n-a", "failed", "not-run", "pinned"], "test vocabulary"
assert [record["promoted"] for record in steps[16:18]] == ["yes", "no"], "promotion vocabulary"
assert all(field not in row for row in steps[:5] for field in (
    "gate", "tests", "promoted", "stops", "escalations", "decisions", "questions", "fix_tasks", "amendments", "files"
)), "absent optional fields must stay omitted"
assert steps[18]["stops"] == 0 and type(steps[18]["stops"]) is int, "zero is a JSON integer"
assert steps[18]["escalations"] == 9007199254740991, "maximum safe integer is accepted"
assert all(steps[18][field] == 0 and type(steps[18][field]) is int for field in (
    "decisions", "questions", "fix_tasks", "amendments", "files"
)), "all count fields are numeric"
PYRUNLOG
  status=$?
  [ "$status" -eq 0 ] || failures=$((failures + 1))
  [ "$failures" -eq 0 ]
)

test_run_log_normalizes_only_exact_legacy_values() (
  set -e
  local fixture helper run file raw expected
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-alias.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  export ORCHESTRAIL_HOME="$helper"
  export ORCHESTRAIL_LOG_ROOT="$fixture/store"
  invoke_log() { bash "$helper/scripts/log-step.sh" "$@"; }
  run="$(invoke_log run-start --pipeline phase-execution --flow full)" || return 1
  file="$(invoke_log path --run "$run")" || return 1
  invoke_log step --run "$run" --step pae-tests --outcome completed --gate PASS --note 'caller note' || return 1
  for pair in 'implemented ok' 'restarted failed' 'needs-work failed'; do
    read -r raw expected <<< "$pair"
    invoke_log step --run "$run" --step pae-tests --outcome "$raw" || return 1
  done
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate 'NEEDS WORK' || return 1
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate 'NEEDS WORK: review' || return 1
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate 'NEEDS WORK - review' || return 1
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate 'NEEDS WORK review' || return 1
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate escalated || return 1
  local before_log before_active after_log after_active
  before_log="$(sha256sum "$file" | awk '{print $1}')"
  before_active="$(sha256sum "$fixture/store/.active/$run" | awk '{print $1}')"
  invoke_log step --run "$run" --step pae-tests --outcome ok --gate 'NEEDS WORKING' > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  after_log="$(sha256sum "$file" | awk '{print $1}')"
  after_active="$(sha256sum "$fixture/store/.active/$run" | awk '{print $1}')"
  [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" 'NEEDS WORKING' || return 1
  [ "$before_log" = "$after_log" ] && [ "$before_active" = "$after_active" ] || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
steps = [record for record in records if record.get("event") == "step"]
assert steps[0]["outcome"] == "ok" and steps[0]["gate"] == "pass", "canonical alias values"
assert steps[0]["note"] == "caller note; raw:completed; raw:PASS", "ordered raw provenance"
assert [record["outcome"] for record in steps[1:4]] == ["ok", "failed", "failed"], "outcome aliases"
assert [record["note"] for record in steps[1:4]] == ["raw:implemented", "raw:restarted", "raw:needs-work"], "outcome provenance"
assert [record["gate"] for record in steps[4:9]] == ["needs-work", "needs-work", "needs-work", "needs-work", "fail"], "gate aliases"
assert [record["note"] for record in steps[4:9]] == [
    "raw:NEEDS WORK", "raw:NEEDS WORK: review", "raw:NEEDS WORK - review",
    "raw:NEEDS WORK review", "raw:escalated"
], "gate provenance"
PYRUNLOG
)

test_run_log_flow_defaults_and_step_name_warnings() (
  set -e
  local fixture helper run file status
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-flow.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  mkdir -p "$fixture/caller" || return 1
  export ORCHESTRAIL_LOG_ROOT="$fixture/store"
  run="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" run-start --pipeline phase-execution)" || return 1
  file="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" path --run "$run")" || return 1
  (cd "$fixture/caller" && env -u ORCHESTRAIL_HOME ORCHESTRAIL_LOG_ROOT="$ORCHESTRAIL_LOG_ROOT" bash "$helper/scripts/log-step.sh" step --run "$run" --step pae-tests --outcome ok) > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" step --run "$run" --step batch-gate --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" step --run "$run" --step unknown-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  assert_one_redacted_warning "$fixture/stderr" || return 1
  ORCHESTRAIL_HOME="$fixture/unavailable" bash "$helper/scripts/log-step.sh" step --run "$run" --step dry-run --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  assert_one_redacted_warning "$fixture/stderr" || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [record["flow"] for record in records] == ["unknown"] * 6, "flow fallback propagation"
assert [record["step"] for record in records if record.get("event") == "step"] == [
    "pae-tests", "batch-gate", "unknown-probe", "dry-run"
], "step name preservation"
PYRUNLOG
  run="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" run-start --pipeline phase-execution)" || return 1
  file="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" path --run "$run")" || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" step --run "$run" --step subtask --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
  python3 - "$file" <<'PYRUNLOG' || return 1
import json, sys
from pathlib import Path
assert json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])["step"] == "subtask"
PYRUNLOG
  # Explicitly empty flow uses the same stored fallback across all event kinds.
  run="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" run-start --pipeline phase-execution --flow '')" || return 1
  file="$(ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" path --run "$run")" || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" step --run "$run" --step pae-tests --outcome ok || return 1
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" run-end --run "$run" --outcome completed || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [record["flow"] for record in records] == ["unknown"] * 3, "empty flow fallback propagation"
PYRUNLOG
  ORCHESTRAIL_HOME="$helper" bash "$helper/scripts/log-step.sh" step --run '../../outside' --step pae-tests --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" '../../outside'
)

test_run_log_start_and_end_persist_before_reporting_success() (
  set -e
  local fixture helper fakebin real_jq run file active status before_log before_active after_log after_active
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-persist.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  fakebin="$fixture/fakebin"
  mkdir -p "$fakebin" || return 1
  export ORCHESTRAIL_HOME="$helper"
  invoke_log() { bash "$helper/scripts/log-step.sh" "$@"; }
  printf '#!/bin/sh\nexit 1\n' > "$fakebin/jq"
  chmod +x "$fakebin/jq"
  status=0
  PATH="$fakebin:$PATH" ORCHESTRAIL_LOG_ROOT="$fixture/start-failure" invoke_log run-start --pipeline phase-execution > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" || return 1
  export ORCHESTRAIL_LOG_ROOT="$fixture/store"
  run="$(invoke_log run-start --pipeline phase-execution --flow full 2> "$fixture/start.err")" || return 1
  [[ "$run" =~ ^[0-9a-f]{8}$ ]] || return 1
  file="$(invoke_log path --run "$run")" || return 1
  active="$fixture/store/.active/$run"
  [ -s "$file" ] && [ -f "$active" ] || return 1
  reject_end() {
    local label="$1" raw_value="$2" status=0
    shift 2
    before_log="$(sha256sum "$file" | awk '{print $1}')"
    before_active="$(sha256sum "$active" | awk '{print $1}')"
    : > "$fixture/stdout"; : > "$fixture/stderr"
    timeout 2 bash "$helper/scripts/log-step.sh" run-end "$@" > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
    after_log="$(sha256sum "$file" | awk '{print $1}')"
    after_active="$(sha256sum "$active" | awk '{print $1}')"
    if [ "$status" -ne 0 ] || [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" "$raw_value" ||
       [ "$before_log" != "$after_log" ] || [ "$before_active" != "$after_active" ]; then
      printf 'run-end changed state or exposed values for invalid %s input\n' "$label"
      return 1
    fi
  }
  reject_end missing-outcome '' --run "$run"
  reject_end duplicate-option '' --run "$run" --run "$run" --outcome completed
  reject_end unknown-option raw-probe-741 --run "$run" --outcome completed --surprise raw-probe-741
  reject_end missing-operand '' --run "$run" --outcome
  reject_end unsafe-run-id '../../outside' --run '../../outside' --outcome completed
  reject_end invalid-outcome invalid-close --run "$run" --outcome invalid-close
  [ ! -e "${file%.jsonl}.md" ] || return 1
  printf '#!/bin/sh\nexit 1\n' > "$fakebin/jq"
  chmod +x "$fakebin/jq"
  before_log="$(sha256sum "$file" | awk '{print $1}')"
  before_active="$(sha256sum "$active" | awk '{print $1}')"
  status=0
  PATH="$fakebin:$PATH" invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" || return 1
  [ "$before_log" = "$(sha256sum "$file" | awk '{print $1}')" ] || return 1
  [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] || return 1
  rm -f "$fakebin/jq"
  invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
  [ ! -e "$active" ] || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [record["event"] for record in records] == ["run-start", "run-end"], "invalid close must be inert"
assert records[1]["outcome"] == "completed", "valid close outcome"
PYRUNLOG
  # A digest failure follows a persisted close and emits one warning without reopening the run.
  run="$(invoke_log run-start --pipeline phase-execution --flow full)" || return 1
  file="$(invoke_log path --run "$run")" || return 1
  active="$fixture/store/.active/$run"
  real_jq="$(command -v jq)"
  cat > "$fakebin/jq" <<EOF
#!/usr/bin/env bash
if [ "\${1-}" = -Rn ]; then
  exec "$real_jq" "\$@"
fi
exit 1
EOF
  chmod +x "$fakebin/jq"
  status=0
  PATH="$fakebin:$PATH" invoke_log run-end --run "$run" --outcome stopped > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" || return 1
  [ ! -e "$active" ] || return 1
  python3 - "$file" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
records = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [record["event"] for record in records] == ["run-start", "run-end"], "persisted close survives digest failure"
assert records[1]["outcome"] == "stopped", "persisted close outcome"
PYRUNLOG
  local end_outcome end_file
  for end_outcome in failed abandoned; do
    run="$(invoke_log run-start --pipeline phase-execution --flow full)" || return 1
    end_file="$(invoke_log path --run "$run")" || return 1
    invoke_log run-end --run "$run" --outcome "$end_outcome" || return 1
    python3 - "$end_file" "$end_outcome" <<'PYRUNLOG'
import json
import sys
from pathlib import Path
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert rows[-1]["event"] == "run-end" and rows[-1]["outcome"] == sys.argv[2], "run-end outcome vocabulary"
PYRUNLOG
  done
)

test_run_log_fallback_and_filesystem_errors_remain_nonblocking() (
  set -e
  local fixture helper fakebin utility run file active before_active status note
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-fallback.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  fakebin="$fixture/bin"
  mkdir -p "$fakebin"
  for utility in bash dirname mkdir od tr date cat uname touch grep mv sed head rm wc; do
    ln -s "$(command -v "$utility")" "$fakebin/$utility" || return 1
  done
  export ORCHESTRAIL_HOME="$helper" ORCHESTRAIL_LOG_ROOT="$fixture/store"
  invoke_log() { PATH="$fakebin" bash "$helper/scripts/log-step.sh" "$@"; }
  note=$'quoted "value"; backslash \\; newline\nnext\tline\r\001'
  run="$(invoke_log run-start --pipeline phase-execution 2> "$fixture/stderr")" || return 1
  [[ "$run" =~ ^[0-9a-f]{8}$ ]] && [ ! -s "$fixture/stderr" ] || return 1
  file="$(invoke_log path --run "$run")"
  active="$fixture/store/.active/$run"
  invoke_log step --run "$run" --step pae-tests --outcome completed --note "$note" --stops 0 --files 9007199254740991 > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
  invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || return 1
  [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] && [ ! -e "$active" ] || return 1
  python3 - "$file" "$note" <<'PYRUNLOG' || return 1
import json
import sys
from pathlib import Path
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [row["event"] for row in rows] == ["run-start", "step", "run-end"]
assert all(row["flow"] == "unknown" for row in rows)
assert rows[1]["note"] == sys.argv[2] + "; raw:completed"
assert rows[1]["stops"] == 0 and type(rows[1]["stops"]) is int
assert rows[1]["files"] == 9007199254740991
PYRUNLOG
  printf 'blocked\n' > "$fixture/blocked-store"
  status=0
  ORCHESTRAIL_LOG_ROOT="$fixture/blocked-store" invoke_log run-start --pipeline phase-execution > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" "$fixture" || return 1
  run="$(invoke_log run-start --pipeline phase-execution)" || return 1
  file="$(invoke_log path --run "$run")"
  active="$fixture/store/.active/$run"
  before_active="$(sha256sum "$active" | awk '{print $1}')"
  rm "$file"
  status=0
  invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
  [ "$status" -eq 0 ] && [ ! -s "$fixture/stdout" ] && assert_one_redacted_warning "$fixture/stderr" "$fixture" || return 1
  [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] && [ ! -e "${file%.jsonl}.md" ] || return 1
)

test_run_log_preserves_unrestricted_flow_across_events() (
  local fixture helper fakebin utility mode flow run file status failures=0
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-flow.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  fakebin="$fixture/bin"
  mkdir -p "$fakebin" || return 1
  for utility in bash dirname mkdir od tr date cat uname touch grep mv sed head rm wc; do
    ln -s "$(command -v "$utility")" "$fakebin/$utility" || return 1
  done
  export ORCHESTRAIL_HOME="$helper" ORCHESTRAIL_LOG_ROOT="$fixture/store"
  invoke_log() { PATH="$fakebin" bash "$helper/scripts/log-step.sh" "$@"; }
  for mode in jq no-jq; do
    rm -f "$fakebin/jq"
    [ "$mode" != jq ] || ln -s "$(command -v jq)" "$fakebin/jq" || return 1
    for flow in $'custom\nflow' $'custom\n' $'\n' 'literal\nflow\\' $'custom\nseq=91\npipeline=other\n' $'\n\n' $'literal%0A%25\\n\n'; do
      status=0
      run="$(invoke_log run-start --pipeline phase-execution --flow "$flow" 2> "$fixture/stderr")" || status=$?
      if [ "$status" -ne 0 ] || [[ ! "$run" =~ ^[0-9a-f]{8}$ ]] || [ -s "$fixture/stderr" ]; then
        printf 'nonempty flow did not start successfully (%s)\n' "$mode"
        failures=$((failures + 1))
        continue
      fi
      file="$(invoke_log path --run "$run")" || return 1
      invoke_log step --run "$run" --step pae-tests --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
      invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
      python3 - "$file" "$flow" <<'PYRUNLOG' || failures=$((failures + 1))
import json
import sys
from pathlib import Path
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [row["event"] for row in rows] == ["run-start", "step", "run-end"]
assert [row["seq"] for row in rows] == [0, 1, 2]
assert all(row["pipeline"] == "phase-execution" for row in rows)
assert all(row["flow"] == sys.argv[2] for row in rows), "flow must survive metadata byte for byte"
PYRUNLOG
      [ ! -e "$fixture/store/.active/$run" ] || return 1
    done
  done
  [ "$failures" -eq 0 ]
)

test_run_log_reports_only_one_diagnostic_on_rejection_or_write_failure() (
  local fixture helper fakebin utility mode run file active before_active before_log status failures=0
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-diagnostics.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  fakebin="$fixture/bin"
  mkdir -p "$fakebin" || return 1
  for utility in bash dirname mkdir od tr date cat uname touch grep mv sed head rm wc; do
    ln -s "$(command -v "$utility")" "$fakebin/$utility" || return 1
  done
  export ORCHESTRAIL_HOME="$helper"
  invoke_log() { PATH="$fakebin" bash "$helper/scripts/log-step.sh" "$@"; }
  for mode in jq no-jq; do
    export ORCHESTRAIL_LOG_ROOT="$fixture/store-$mode"
    rm -f "$fakebin/jq"
    [ "$mode" != jq ] || ln -s "$(command -v jq)" "$fakebin/jq" || return 1
    status=0
    invoke_log step --run 00000000 --step unknown-diagnostic-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || status=$?
    if [ "$status" -ne 0 ] || [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" unknown-diagnostic-probe; then
      printf 'unknown run produced multiple or unsafe diagnostics (%s)\n' "$mode"
      failures=$((failures + 1))
    fi
    [ ! -e "$ORCHESTRAIL_LOG_ROOT" ] || return 1
    run="$(invoke_log run-start --pipeline phase-execution)" || return 1
    file="$(invoke_log path --run "$run")"
    active="$ORCHESTRAIL_LOG_ROOT/.active/$run"
    before_active="$(sha256sum "$active" | awk '{print $1}')"
    before_log="$(sha256sum "$file" | awk '{print $1}')"
    if [ "$mode" = jq ]; then
      rm "$fakebin/jq"
      printf '#!/bin/sh\nexit 1\n' > "$fakebin/jq"
      chmod +x "$fakebin/jq"
      invoke_log step --run "$run" --step unknown-diagnostic-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      if [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" unknown-diagnostic-probe; then
        echo 'failed serialization was accompanied by an advisory diagnostic'
        failures=$((failures + 1))
      fi
      [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] &&
        [ "$before_log" = "$(sha256sum "$file" | awk '{print $1}')" ] || return 1
      rm "$fakebin/jq"
      ln -s "$(command -v jq)" "$fakebin/jq" || return 1
    fi
    rm "$fakebin/mv"
    printf '#!/bin/sh\nexit 1\n' > "$fakebin/mv"
    chmod +x "$fakebin/mv"
    invoke_log step --run "$run" --step unknown-diagnostic-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
    if [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" unknown-diagnostic-probe; then
      printf 'failed metadata write was accompanied by an advisory diagnostic (%s)\n' "$mode"
      failures=$((failures + 1))
    fi
    [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] || return 1
    mv "$helper/workflows" "$fixture/workflows-held" || return 1
    invoke_log step --run "$run" --step unknown-diagnostic-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
    if [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" unknown-diagnostic-probe; then
      printf 'failed metadata write was accompanied by an unavailable-workflows advisory (%s)\n' "$mode"
      failures=$((failures + 1))
    fi
    [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] || return 1
    mv "$fixture/workflows-held" "$helper/workflows" || return 1
    rm "$fakebin/mv"
    ln -s "$(command -v mv)" "$fakebin/mv" || return 1
    rm "$file"
    invoke_log step --run "$run" --step unknown-diagnostic-probe --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
    if [ -s "$fixture/stdout" ] || ! assert_one_redacted_warning "$fixture/stderr" unknown-diagnostic-probe; then
      printf 'unavailable event file was accompanied by an advisory diagnostic (%s)\n' "$mode"
      failures=$((failures + 1))
    fi
    [ "$before_active" = "$(sha256sum "$active" | awk '{print $1}')" ] || return 1
  done
  [ "$failures" -eq 0 ]
)

test_run_log_metadata_preserves_text_boundaries_and_legacy_records() (
  local fixture helper fakebin utility mode field payload pipeline project task spec flags flow run file status epoch failures=0
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/run-log-metadata.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  prepare_run_log_fixture "$fixture" || return 1
  helper="$fixture/helper"
  fakebin="$fixture/bin"
  mkdir -p "$fakebin" || return 1
  for utility in bash dirname mkdir od tr date cat uname touch grep mv sed head rm wc; do
    ln -s "$(command -v "$utility")" "$fakebin/$utility" || return 1
  done
  export ORCHESTRAIL_HOME="$helper"
  invoke_log() { PATH="$fakebin" bash "$helper/scripts/log-step.sh" "$@"; }
  for mode in jq no-jq; do
    rm -f "$fakebin/jq"
    [ "$mode" != jq ] || ln -s "$(command -v jq)" "$fakebin/jq" || return 1
    for field in flags-collision pipeline project task spec flags log-root legacy legacy-percent format-marker; do
      pipeline=phase-execution project=fixture-project task=fixture-task spec=fixture-spec flags=fixture-flags flow='literal%0Aflow'
      payload=$'custom%0A\\n\nflow_encoding=percent\nseq=91\npipeline=injected\n'
      export ORCHESTRAIL_LOG_ROOT="$fixture/store-$mode-$field"
      case "$field" in
        flags-collision) flags=$'custom\nflow_encoding=percent' ;;
        format-marker) flags=$'# run-log-metadata percent-v1\nflow_encoding=percent\n' ;;
        pipeline) pipeline="$payload" ;;
        project) project="$payload" ;;
        task) task="$payload" ;;
        spec) spec="$payload" ;;
        flags) flags="$payload" ;;
        log-root) ORCHESTRAIL_LOG_ROOT+=$'\nflow_encoding=percent\n' ;;
        legacy-percent) flow=$'encoded\nflow%0A\\n\n' ;;
      esac
      status=0
      run="$(invoke_log run-start --pipeline "$pipeline" --project "$project" --task "$task" --spec "$spec" --flags "$flags" --flow "$flow" 2> "$fixture/stderr")" || status=$?
      if [ "$status" -ne 0 ] || [[ ! "$run" =~ ^[0-9a-f]{8}$ ]] || [ -s "$fixture/stderr" ]; then
        printf 'metadata text prevented a valid start (%s, %s)\n' "$mode" "$field"
        failures=$((failures + 1))
        continue
      fi
      file="$(invoke_log path --run "$run")" || return 1
      [ -f "$file" ] || return 1
      if [ "$field" = legacy ]; then
        epoch="$(date +%s)"
        printf '%s\n' "file=$file" "pipeline=$pipeline" "project=$project" "task=$task" "spec=$spec" "flags=$flags" "flow=$flow" \
          "started_epoch=$epoch" "last_epoch=$epoch" 'seq=0' > "$ORCHESTRAIL_LOG_ROOT/.active/$run" || return 1
      fi
      if [ "$field" = legacy-percent ]; then
        epoch="$(date +%s)"
        python3 - "$ORCHESTRAIL_LOG_ROOT/.active/$run" "$file" "$flow" "$epoch" <<'PYRUNLOG' || return 1
from pathlib import Path
import sys
metadata, file, flow, epoch = sys.argv[1:]
encoded = flow.replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')
Path(metadata).write_text(f"file={file}\npipeline=phase-execution\nproject=fixture-project\ntask=fixture-task\nspec=fixture-spec\nflags=fixture-flags\nflow={encoded}\nflow_encoding=percent\nstarted_epoch={epoch}\nlast_epoch={epoch}\nseq=0\n")
PYRUNLOG
      fi
      invoke_log active > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      [ ! -s "$fixture/stderr" ] || return 1
      python3 - "$fixture/stdout" "$run" "$pipeline" "$task" <<'PYRUNLOG' || failures=$((failures + 1))
import sys
from pathlib import Path
assert Path(sys.argv[1]).read_text() == f"{sys.argv[2]}  {sys.argv[3]}  {sys.argv[4]}\n", "active listing must decode metadata text"
PYRUNLOG
      invoke_log step --run "$run" --step pae-tests --outcome ok > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
      invoke_log run-end --run "$run" --outcome completed > "$fixture/stdout" 2> "$fixture/stderr" || return 1
      [ ! -s "$fixture/stdout" ] && [ ! -s "$fixture/stderr" ] || return 1
      python3 - "$file" "$pipeline" "$project" "$task" "$spec" "$flags" "$flow" <<'PYRUNLOG' || failures=$((failures + 1))
import json
import sys
from pathlib import Path
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [row["event"] for row in rows] == ["run-start", "step", "run-end"]
assert [row["seq"] for row in rows] == [0, 1, 2], "metadata text must not inject sequence values"
for key, value in zip(("pipeline", "project", "task"), sys.argv[2:5]):
    assert all(row[key] == value for row in rows), f"{key} must survive metadata byte for byte"
assert rows[0]["spec"] == sys.argv[5] and rows[0]["flags"] == sys.argv[6]
assert all(row["flow"] == sys.argv[7] for row in rows), "metadata text must not change flow decoding"
assert all("flow_encoding" not in row for row in rows), "metadata encoding is not an event field"
PYRUNLOG
      [ ! -e "$ORCHESTRAIL_LOG_ROOT/.active/$run" ] || return 1
    done
  done
  [ "$failures" -eq 0 ]
)

test_run_log_unknown_commands_are_redacted_and_preserve_storage() {
  python3 - "$PWD/scripts/log-step.sh" <<'PYDISPATCH'
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='unknown command ') as temporary:
    fixture = Path(temporary)
    home = fixture / 'helper home'
    (home / 'scripts').mkdir(parents=True)
    (home / 'workflows').mkdir()
    (home / 'workflows/fixture-known.md').write_text('Fixture workflow\n')
    helper = home / 'scripts/log-step.sh'
    shutil.copyfile(sys.argv[1], helper)
    store = fixture / 'log store'
    env = dict(os.environ, ORCHESTRAIL_HOME=str(home), ORCHESTRAIL_LOG_ROOT=str(store))
    def snapshot():
        return (store.exists(), {str(p.relative_to(store)):
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
                for p in store.rglob('*')})
    def invoke(*args):
        result = subprocess.run(['bash', str(helper), *args], env=env,
                                capture_output=True, timeout=2)
        assert result.returncode == 0, ('helper must remain nonblocking', args, result)
        return result
    failures = []
    diagnostic = None
    for populated in (False, True):
        if populated:
            result = invoke('run-start', '--pipeline', 'fixture-pipeline')
            run = result.stdout.decode().strip()
            assert re.fullmatch('[0-9a-f]{8}', run) and result.stderr == b'', result
            event_file = next((store / 'runs').glob('*.jsonl'))
            event_file.with_suffix('.md').write_text('Historical digest fixture\n')
        before = snapshot()
        help_output = invoke('--help').stdout
        assert help_output, 'help must describe the helper'
        for args in ((), ('',), ('-h',), ('--help',), ('help',)):
            result = invoke(*args)
            assert result.stdout == help_output and result.stderr == b'', (args, result)
            assert snapshot() == before, ('help changed storage', args)
        commands = ('private-command', '--private-command', '-private-command',
                    'private-command\nsecond-line', 'private-command\rthird-line',
                    'private-command\tfourth-line', '\x1b[31mprivate-command')
        for command in commands:
            for trailing in ((), ('--run', 'private-operand', '--run', '')):
                result = invoke(command, *trailing)
                safe = (result.stdout == b'' and
                        re.fullmatch(rb'log-step: [a-z -]+\n', result.stderr) is not None and
                        b'private' not in result.stderr and
                        b'second-line' not in result.stderr and
                        b'third-line' not in result.stderr and
                        b'fourth-line' not in result.stderr)
                if not safe:
                    failures.append((populated, command, trailing, result))
                if diagnostic is None:
                    diagnostic = result.stderr
                elif result.stderr != diagnostic:
                    failures.append(('unknown-command diagnostic changed with caller text', command))
                assert snapshot() == before, ('unknown command changed storage', command, trailing)
        if populated:
            for args in (('path',), ('path', '--run', run), ('active',), ('contract',)):
                result = invoke(*args)
                assert result.stdout and result.stderr == b'', (args, result)
                assert snapshot() == before, ('read-only command changed storage', args)
            result = invoke('step', '--run', run, '--step', 'fixture-known', '--outcome', 'ok')
            assert result.stdout == b'' and result.stderr == b'', result
            result = invoke('run-end', '--run', run, '--outcome', 'completed')
            assert result.stdout == b'' and result.stderr == b'', result
            assert not (store / '.active' / run).exists()
    assert not failures, ('unknown-command diagnostics exposed caller text or control characters', failures)
PYDISPATCH
}

test_run_log_path_arguments_terminate_safely_and_preserve_storage() {
  python3 - "$PWD/scripts/log-step.sh" <<'PYPATH'
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='path arguments ') as temporary:
    fixture = Path(temporary)
    home, store = fixture / 'helper home', fixture / 'log store'
    (home / 'scripts').mkdir(parents=True)
    helper = home / 'scripts/log-step.sh'
    shutil.copyfile(sys.argv[1], helper)
    env = dict(os.environ, ORCHESTRAIL_HOME=str(home), ORCHESTRAIL_LOG_ROOT=str(store))
    def snapshot():
        return (store.exists(), {str(p.relative_to(store)):
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
                for p in store.rglob('*')})
    def invoke(*args):
        return subprocess.run(['bash', str(helper), *args], env=env,
                              capture_output=True, timeout=1)
    failures = []
    for populated in (False, True):
        run = '01234567'
        if populated:
            result = invoke('run-start', '--pipeline', 'fixture-pipeline')
            run = result.stdout.decode().strip()
            assert result.returncode == 0 and re.fullmatch('[0-9a-f]{8}', run), result
            assert result.stderr == b'', result
            event_file = next((store / 'runs').glob('*.jsonl'))
            event_file.with_suffix('.md').write_text('Historical digest fixture\n')
            # A lookup of an unsafe identifier would disclose this sentinel path.
            (store / '.active/ABCDEF01').write_text('file=private-metadata-sentinel\n')
        before = snapshot()
        cases = [('--run',), ('--run', '--run'), ('--run', '--private-option'),
                 ('--run', '-private-option'), ('--run', run, '--run'),
                 ('--run', run, '--run', run), ('--run', '',),
                 ('--private-option',), ('private-positional',),
                 ('--run', run, '--private-option', 'private-operand'),
                 ('--run', run, 'private-positional'),
                 ('--private-option', '--run', run)]
        for value in ('ABCDEF01', '1234567', '123456789', '../private',
                      'private/operand', 'private\nsecond-line', 'private\rthird-line',
                      'private\tfourth-line', '\x1b[31mprivate'):
            cases.append(('--run', value))
        for args in cases:
            try:
                result = invoke('path', *args)
            except subprocess.TimeoutExpired:
                failures.append((populated, args, 'path arguments did not terminate'))
            else:
                safe = (result.returncode == 0 and result.stdout == b'' and
                        re.fullmatch(rb'log-step: path [a-z-]+ [a-z-]+\n', result.stderr) is not None and
                        b'private' not in result.stderr)
                if not safe:
                    failures.append((populated, args, result))
            assert snapshot() == before, ('malformed path changed storage', args)
        result = invoke('path')
        assert result.returncode == 0 and result.stdout == (str(store) + '\n').encode(), result
        assert result.stderr == b'' and snapshot() == before, result
        if populated:
            result = invoke('path', '--run', run)
            assert result.returncode == 0 and result.stdout == (str(event_file) + '\n').encode(), result
            assert result.stderr == b'' and snapshot() == before, result
        else:
            assert not store.exists(), 'read-only path created the absent store'
    assert not failures, ('malformed path must terminate with one safe warning', failures)
PYPATH
}

test_run_log_required_arguments_and_rejected_timing_preserve_storage() {
  python3 - "$PWD/scripts/log-step.sh" <<'PYREQUIRED'
from pathlib import Path
import hashlib, json, os, re, shlex, shutil, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='required arguments ') as temporary:
    fixture = Path(temporary)
    home, store = fixture / 'helper home', fixture / 'log store'
    (home / 'workflows').mkdir(parents=True)
    (home / 'workflows/fixture-known.md').write_text('Fixture workflow\n')
    env = dict(os.environ, ORCHESTRAIL_HOME=str(home), ORCHESTRAIL_LOG_ROOT=str(store))
    helper = sys.argv[1]
    def snapshot():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in store.rglob('*') if p.is_file()}
    def invoke(*args):
        result = subprocess.run(['bash', helper, *args], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result
        return result
    run = invoke('run-start', '--pipeline', 'fixture-pipeline').stdout.strip()
    assert re.fullmatch('[0-9a-f]{8}', run)
    file = next((store / 'runs').glob('*.jsonl'))
    digest = file.with_suffix('.md')
    digest.write_text('Historical digest fixture\n')
    active = store / '.active' / run
    metadata = active.read_text()
    assert re.search(r'^last_epoch=[0-9]+$', metadata, re.M)
    active.write_text(re.sub(r'^last_epoch=[0-9]+$', 'last_epoch=1000', metadata, flags=re.M))
    fakebin = fixture / 'clock bin'; fakebin.mkdir()
    date = fakebin / 'date'
    date.write_text('#!/bin/sh\nif [ "$*" = "-u +%s" ]; then printf "1005\\n"; else exec '
                    + shlex.quote(shutil.which('date')) + ' "$@"; fi\n')
    date.chmod(0o755)
    env['PATH'] = str(fakebin) + os.pathsep + env['PATH']
    cases = [
        ('step', '--step', 'fixture-known', '--outcome', 'ok'),
        ('step', '--run', run, '--outcome', 'ok'),
        ('step', '--run', run, '--step', '', '--outcome', 'ok'),
        ('step', '--run', '', '--step', 'fixture-known', '--outcome', 'ok'),
        ('step', '--run', 'ABCDEF01', '--step', 'fixture-known', '--outcome', 'ok'),
        ('step', '--run', '1234567', '--step', 'fixture-known', '--outcome', 'ok'),
        ('step', '--run', run, '--step', 'fixture-known', '--outcome', 'ok', '--gate', '--tests', 'green'),
        ('run-end', '--outcome', 'completed'),
        ('run-end', '--run', run, '--outcome', ''),
        ('run-end', '--run', run, '--outcome', 'ok'),
        ('run-end', '--run', run, '--outcome', '--note', 'private-input'),
    ]
    for args in cases:
        before = snapshot()
        result = invoke(*args)
        assert result.stdout == '' and len(result.stderr.splitlines()) == 1, (args, result)
        assert 'private-input' not in result.stderr
        assert snapshot() == before, ('rejected invocation changed storage', args)
    for args in [('path', '--run', run), ('active',), ('contract',)]:
        before = snapshot()
        result = invoke(*args)
        assert result.stdout and not result.stderr
        assert snapshot() == before, ('query changed storage', args)
    result = invoke('step', '--run', run, '--step', 'fixture-known', '--outcome', 'ok',
                    '--note', '', '--subtask', '', '--blocker', '')
    assert not result.stdout and not result.stderr
    rows = [json.loads(line) for line in file.read_text().splitlines()]
    assert rows[-1]['seq'] == 1 and rows[-1]['duration_s'] == 5, rows
    assert all(field not in rows[-1] for field in ('note', 'subtask', 'blocker'))
    assert digest.read_text() == 'Historical digest fixture\n'
    result = invoke('run-end', '--run', run, '--outcome', 'completed')
    assert not result.stdout and not result.stderr and not active.exists()
PYREQUIRED
}

check "LOGPRODUCER: unknown commands emit one redacted warning without storage changes" \
  "$(test_run_log_unknown_commands_are_redacted_and_preserve_storage && echo pass || echo 'unknown-command dispatch leaked caller text or changed storage')"

check "LOGPRODUCER: malformed path arguments terminate safely without storage changes" \
  "$(test_run_log_path_arguments_terminate_safely_and_preserve_storage && echo pass || echo 'path parsing failed termination, redaction, or read-only behavior')"

check "LOGPRODUCER: mandatory arguments and rejected timing preserve storage" \
  "$(test_run_log_required_arguments_and_rejected_timing_preserve_storage && echo pass || echo 'required arguments, read-only queries, or accepted-event timing failed')"

check "LOGPRODUCER: metadata text preserves record boundaries and legacy reads" \
  "$(test_run_log_metadata_preserves_text_boundaries_and_legacy_records && echo pass || echo 'metadata text changed inherited fields or encoding controls')"
check "LOGPRODUCER: arbitrary nonempty flow survives every event" \
  "$(test_run_log_preserves_unrestricted_flow_across_events && echo pass || echo 'nonempty flow changed or was rejected during metadata persistence')"
check "LOGPRODUCER: rejected and failed steps emit one diagnostic" \
  "$(test_run_log_reports_only_one_diagnostic_on_rejection_or_write_failure && echo pass || echo 'step-name advisories duplicated rejection or filesystem diagnostics')"
check "LOGPRODUCER: fallback preserves strings and filesystem failures warn safely" \
  "$(test_run_log_fallback_and_filesystem_errors_remain_nonblocking && echo pass || echo 'fallback encoding or filesystem error behavior is incomplete')"
check "LOGPRODUCER: run-start rejects invalid complete argument sets" \
  "$(test_run_log_start_rejects_invalid_argument_sets && echo pass || echo 'invalid run-start arguments changed state or returned unsafe output')"
check "LOGPRODUCER: step rejects invalid fields before metadata changes" \
  "$(test_run_log_step_rejects_invalid_fields_without_mutation && echo pass || echo 'invalid step fields changed the event file or active metadata')"
check "LOGPRODUCER: exact legacy aliases normalize with ordered provenance" \
  "$(test_run_log_normalizes_only_exact_legacy_values && echo pass || echo 'legacy aliases or raw provenance are not exact')"
check "LOGPRODUCER: flow defaults and workflow names are handled safely" \
  "$(test_run_log_flow_defaults_and_step_name_warnings && echo pass || echo 'flow defaults or advisory step-name checks are incomplete')"
check "LOGPRODUCER: success output follows persistence and rejected closes remain active" \
  "$(test_run_log_start_and_end_persist_before_reporting_success && echo pass || echo 'run persistence, close recovery, or digest warning behavior is incomplete')"

run_lint_smoke() {
  python3 - "$1" "$PWD/scripts/log-step.sh" <<'PYLINT'
import copy
import hashlib
import shlex
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

scenario, helper = sys.argv[1:]
base = dict(event="step", ts="2026-01-01T00:00:00Z", run_id="1234abcd",
            seq=1, pipeline="phase-execution", flow="unknown", step="retired-workflow", outcome="ok")
with tempfile.TemporaryDirectory(prefix="run-log-lint-") as scratch:
    root = Path(scratch) / 'store'
    env = dict(os.environ, ORCHESTRAIL_LOG_ROOT=str(root))
    def snapshot():
        hashes = {}
        for path in root.rglob('*'):
            if path.is_symlink():
                hashes[str(path)] = ('symlink', os.readlink(path))
            elif path.is_file():
                try:
                    hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                except PermissionError:
                    hashes[str(path)] = ('unreadable', path.stat().st_mode, path.stat().st_size)
        return hashes
    def invoke(*args, extra=None):
        before_read = snapshot()
        result = subprocess.run(['/bin/bash', helper, 'lint', *args], env=env | (extra or {}),
                                text=True, capture_output=True, timeout=10)
        assert snapshot() == before_read, "lint changed historical fixture checksums"
        assert result.returncode == 0, result
        try:
            rows = [json.loads(line) for line in result.stdout.splitlines()]
        except ValueError as error:
            raise AssertionError('lint must emit only JSON objects') from error
        assert rows and rows[-1].get('kind') == 'summary', result
        assert sum(r.get('kind') == 'summary' for r in rows) == 1, rows
        assert set(rows[-1]) == {'kind', 'status', 'files', 'lines', 'invalid_lines', 'violations'}, rows
        for row in rows[:-1]:
            assert set(row) == {'kind', 'file', 'line', 'field', 'code'}, row
            assert row['kind'] == 'violation', row
            assert row['code'] in {'invalid-json', 'invalid-object', 'missing-field', 'invalid-type',
                                   'invalid-enum', 'invalid-integer', 'empty-flow'}, row
        return rows, result.stderr
    def summary(rows, files, lines, invalid=0, violations=0, status='ok'):
        assert rows[-1] == dict(kind='summary', status=status, files=files, lines=lines,
                               invalid_lines=invalid, violations=violations), rows
    def write(name, rows, final=True):
        (root / 'runs').mkdir(parents=True, exist_ok=True)
        path = root / 'runs' / name
        path.write_text('\n'.join(json.dumps(r) if not isinstance(r, str) else r for r in rows)
                        + ('\n' if final else ''))
        return path
    if scenario == 'selection':
        rows, _ = invoke(); summary(rows, 0, 0); assert not root.exists()
        a = write('a-1234abcd.jsonl', [base])
        b = write('b-1234abcd.jsonl', [base])
        c = write('c-deadbeef.jsonl', [dict(base, tests='secret-bad-enum')])
        (root / '.active').mkdir(); (root / '.active' / '1234abcd').write_text('opaque metadata')
        (root / 'runs' / 'a-1234abcd.md').write_text('opaque digest')
        before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for args in [(), ('--all',)]:
            rows, err = invoke(*args); summary(rows, 3, 3, 1, 1); assert not err
            assert rows[0]['file'] == str(c)
        rows, _ = invoke('1234abcd'); summary(rows, 2, 2)
        rows, _ = invoke('00000000'); summary(rows, 0, 0)
        for args in [('bad-secret',), ('--all', '1234abcd'), ('1234abcd', 'deadbeef'), ('--other',)]:
            rows, err = invoke(*args); summary(rows, 0, 0, status='unavailable'); assert err
            assert 'bad-secret' not in err
        assert before == {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    elif scenario == 'diagnostics':
        a = write('a-1234abcd.jsonl', ['{secret', [], {}, dict(base, flow='', tests='secret', stops=-1),
                                     '', '{} {}', base], final=False)
        b = write('b-deadbeef.jsonl', [dict(base, outcome='completed')])
        rows, err = invoke('--all'); assert not err
        assert [(r['file'], r['line']) for r in rows[:-1]] == sorted((r['file'], r['line']) for r in rows[:-1])
        assert 'secret' not in json.dumps(rows)
        issues = {(r['line'], r['field'], r['code']) for r in rows[:-1] if r['file'] == str(a)}
        for issue in [(1, 'record', 'invalid-json'), (2, 'record', 'invalid-object'),
                      (4, 'flow', 'empty-flow'), (4, 'tests', 'invalid-enum'),
                      (4, 'stops', 'invalid-integer'), (5, 'record', 'invalid-json'), (6, 'record', 'invalid-json')]:
            assert issue in issues, (issue, rows)
        assert any(r['line'] == 3 and r['field'] == 'event' and r['code'] == 'missing-field' for r in rows[:-1])
        summary(rows, 2, 8, 7, len(rows)-1)
        again, _ = invoke('--all'); assert again == rows
        a.write_bytes(json.dumps(base).encode().replace(b'unknown', b'un\x00known') + b'\n')
        rows, err = invoke('1234abcd'); assert not err
        summary(rows, 1, 1, 1, 1)
        assert rows[0]['code'] == 'invalid-json', rows
        malformed = []
        for literal in ['01', '+1', '.1', '1.', 'NaN', 'Infinity', '-Infinity', '1e', '1e+', '--1']:
            malformed.append(json.dumps(base)[:-1] + ', "optional": {"value": ' + literal + '}}')
        a.write_text('\n'.join(malformed) + '\n')
        rows, err = invoke('1234abcd'); assert not err
        summary(rows, 1, len(malformed), len(malformed), len(malformed))
        assert all(r['field'] == 'record' and r['code'] == 'invalid-json' for r in rows[:-1]), rows
    elif scenario == 'fields':
        records, expected = [], []
        def case(record, field, code):
            records.append(record); expected.append((len(records), field, code))
        for event in ['run-start', 'step', 'run-end']:
            valid = dict(base, event=event, outcome='completed' if event == 'run-end' else 'ok')
            records.append(valid)
            for field in ['event', 'ts', 'run_id', 'seq', 'pipeline', 'flow'] + (['step', 'outcome'] if event == 'step' else ['outcome'] if event == 'run-end' else []):
                r = copy.deepcopy(valid); del r[field]; case(r, field, 'missing-field')
                case(dict(valid, **{field: None}), field, 'invalid-type')
        for field, values in {'outcome':['completed','implemented','restarted','needs-work','OK',''],
                              'gate':['PASS','NEEDS WORK','NEEDS WORK: secret','escalated','NEEDS WORKING',''],
                              'tests':['secret',''], 'promoted':['secret','']}.items():
            for value in values: case(dict(base, **{field:value}), field, 'invalid-enum')
            case(dict(base, **{field:False}), field, 'invalid-type')
        for field in ['seq','duration_s','stops','escalations','decisions','questions','fix_tasks','amendments','files']:
            for value in [-1, 0.5, 9007199254740992]: case(dict(base, **{field:value}), field, 'invalid-integer')
            for value in ['0', None, True]: case(dict(base, **{field:value}), field, 'invalid-type')
            records.extend([dict(base, **{field:0}), dict(base, **{field:9007199254740991})])
        case(dict(base, event='secret'), 'event', 'invalid-enum')
        for literal in ['9007199254740991.1', '9007199254740992', '1e1000000', '1e-1000000', '-1e0']:
            records.append(json.dumps(dict(base, stops=0)).replace('"stops": 0', '"stops": ' + literal))
            expected.append((len(records), 'stops', 'invalid-integer'))
        for literal in ['1.0', '1e0', '1E+0', '-0', '9007199254740991.000', '90071992547409910e-1', '0e1000000', '0e-1000000']:
            records.append(json.dumps(dict(base, stops=0)).replace('"stops": 0', '"stops": ' + literal))
        for value in [False, 3, [], {}]: case(dict(base, event=value), 'event', 'invalid-type')
        for field, values in {'outcome':['ok','blocked','failed','skipped','deferred'], 'gate':['pass','fail','n-a','needs-work','ready'],
                              'tests':['red','green','n-a','failed','not-run','pinned'], 'promoted':['yes','no']}.items():
            records.extend(dict(base, **{field:v}) for v in values)
        records.extend(dict(base, event='run-end', outcome=v) for v in ['completed','stopped','failed','abandoned'])
        write('a-1234abcd.jsonl', records)
        rows, err = invoke(); assert not err
        actual = [(r['line'], r['field'], r['code']) for r in rows[:-1]]
        assert sorted(actual) == sorted(expected), (actual, expected)
        summary(rows, 1, len(records), len({e[0] for e in expected}), len(expected))
    elif scenario == 'availability':
        write('a-1234abcd.jsonl', [base])
        bin_dir = Path(scratch) / 'bin'; bin_dir.mkdir()
        for name in ['dirname', 'sort']:
            os.symlink(shutil.which(name), bin_dir / name)
        rows, err = invoke(extra={'PATH':str(bin_dir)}); summary(rows, 0, 0, status='unavailable'); assert err
        jq = bin_dir / 'jq'; jq.write_text('#!/bin/sh\nexit 7\n'); jq.chmod(0o755)
        rows, err = invoke(extra={'PATH':str(bin_dir)}); summary(rows, 0, 0, status='unavailable'); assert err
        jq.unlink()
        unreadable = write('b-1234abcd.jsonl', [base]); unreadable.chmod(0)
        rows, err = invoke(); summary(rows, 1, 1, status='partial'); assert err
        unreadable.chmod(0o600)
        dangling = root / 'runs' / 'c-1234abcd.jsonl'
        dangling.symlink_to(root / 'missing')
        rows, err = invoke(); summary(rows, 2, 2, status='partial'); assert err
        dangling.unlink()
        (root / 'runs').chmod(0)
        rows, err = invoke(); summary(rows, 0, 0, status='unavailable'); assert err
        (root / 'runs').chmod(0o700)
        jq.write_text('#!/bin/sh\ncase \"$*\" in *-Rsc*) exit 7;; esac\nexec ' + shutil.which('jq') + ' \"$@\"\n')
        jq.chmod(0o755)
        rows, err = invoke(extra={'PATH':str(bin_dir)}); summary(rows, 0, 0, status='unavailable'); assert err
        # Fail only on the second physical line of a single selected file.
        write('a-1234abcd.jsonl', [dict(base, tests='BAD'), base, base])
        jq.write_text('#!/bin/sh\ncase "$*" in *"--argjson line 2"*) exit 7;; esac\nexec '
                      + shlex.quote(shutil.which('jq')) + ' "$@"\n')
        rows, err = invoke('1234abcd', extra={'PATH':str(bin_dir)})
        summary(rows, 2, 2, 1, 1, status='partial'); assert err
        assert [(r['line'], r['field'], r['code']) for r in rows[:-1]] == [(1, 'tests', 'invalid-enum')]
PYLINT
}

test_run_log_lint_selects_files_and_preserves_storage() { run_lint_smoke selection; }
test_run_log_lint_emits_ordered_redacted_diagnostics() { run_lint_smoke diagnostics; }
test_run_log_lint_validates_fields_and_shared_vocabulary() { run_lint_smoke fields; }
test_run_log_lint_reports_unavailable_and_partial_checks() { run_lint_smoke availability; }

check "Run-log lint selects files and preserves storage" \
  "$(test_run_log_lint_selects_files_and_preserves_storage && echo pass || echo 'lint selection or immutable storage contract failed')"
check "Run-log lint emits ordered redacted diagnostics" \
  "$(test_run_log_lint_emits_ordered_redacted_diagnostics && echo pass || echo 'lint diagnostics or distinct-line counts failed')"
check "Run-log lint validates fields and shared vocabulary" \
  "$(test_run_log_lint_validates_fields_and_shared_vocabulary && echo pass || echo 'lint field vocabulary or types failed')"
check "Run-log lint reports unavailable and partial checks" \
  "$(test_run_log_lint_reports_unavailable_and_partial_checks && echo pass || echo 'lint availability status or examined counts failed')"

# Correlated event checks use only disposable stores, including injected I/O failures.
run_correlated_event_smoke() {
  python3 - "$REPO_ROOT" "$1" <<'PYCORRELATED'
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json, os, re, shlex, shutil, subprocess, sys, tempfile, time, uuid
root, scenario = Path(sys.argv[1]), sys.argv[2]
with tempfile.TemporaryDirectory(prefix='correlated events ') as temporary:
    fixture = Path(temporary)
    store = fixture/'private store'
    environment = dict(os.environ, ORCHESTRAIL_LOG_ROOT=str(store), ORCHESTRAIL_HOME=str(root))
    helper = root/'scripts/log-step.sh'
    def invoke(*args: object, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(['bash',str(helper),*map(str,args)], env=env or environment,
                                capture_output=True,text=True)
        assert result.returncode == 0, result
        return result
    def start() -> str:
        result = invoke('run-start','--pipeline','correlation-probe')
        assert re.fullmatch('[0-9a-f]{8}\n',result.stdout), result
        return result.stdout.strip()
    def path(run: str) -> Path:
        return Path(invoke('path','--run',run).stdout.strip())
    def rows(run: str) -> list[dict[str, object]]:
        return [json.loads(line) for line in path(run).read_text().splitlines()]
    def snapshot() -> dict[str, bytes]:
        return {str(p.relative_to(store)):p.read_bytes() for p in store.rglob('*') if p.is_file()}
    session, agent = uuid.uuid4().hex, uuid.uuid4().hex
    now = time.time_ns() // 1_000_000
    def arguments(run: str, checkpoint: str, **changes: object) -> list[str]:
        fields = dict(run=run,step='dry-run',outcome='ok',session_id=session,agent_id=agent,
                      checkpoint_id=checkpoint,span_start_ms=str(now-20000),span_end_ms=str(now-10000),
                      timing_source='hook',boundary='subagent')
        fields.update(changes)
        return ['step',*[part for key,value in fields.items() if value is not None
                         for part in ('--'+key.replace('_','-'),str(value))]]
    def accepted(result: subprocess.CompletedProcess[str], run: str, checkpoint: str, duplicate: bool = False) -> dict[str, object]:
        assert result.stdout.strip(), ('missing accepted receipt',result.stderr)
        receipt = json.loads(result.stdout)
        assert receipt == dict(kind='accepted',run_id=run,session_id=session,agent_id=agent,
                               checkpoint_id=checkpoint,seq=receipt['seq'],duplicate=duplicate), receipt
        assert isinstance(receipt['seq'],int) and receipt['seq'] > 0, receipt
        assert not result.stderr, result.stderr
        return receipt
    def reject(result: subprocess.CompletedProcess[str], before: dict[str, bytes]) -> None:
        assert not result.stdout, result.stdout
        assert len(result.stderr.splitlines()) == 1 and result.stderr.startswith('log-step:'), result.stderr
        assert snapshot() == before, 'rejected delivery changed active state or events'
    run = start()
    checkpoint = uuid.uuid4().hex
    if scenario == 'concurrent':
        other = start()
        deliveries = [(run,uuid.uuid4().hex),(other,uuid.uuid4().hex),(run,uuid.uuid4().hex)]
        # Duplicate each identity concurrently; one new acceptance and one replay per identity.
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda pair: invoke(*arguments(*pair)),deliveries*2))
        for pair in deliveries:
            receipts = [json.loads(r.stdout) for p,r in zip(deliveries*2,results) if p==pair and r.stdout]
            assert len(receipts)==2, ('missing concurrent receipts',results)
            assert sorted(r['duplicate'] for r in receipts)==[False,True],receipts
            assert len({r['seq'] for r in receipts})==1,receipts
        for selected in (run,other):
            records=rows(selected)
            assert [r['seq'] for r in records]==list(range(len(records))),records
            assert {r['checkpoint_id'] for r in records[1:]}=={c for r,c in deliveries if r==selected}
            assert all(r['run_id']==selected for r in records)
    elif scenario == 'duplicates':
        original = accepted(invoke(*arguments(run,checkpoint)),run,checkpoint)
        before=snapshot()
        replay=accepted(invoke(*arguments(run,checkpoint)),run,checkpoint,True)
        assert replay['seq']==original['seq'] and snapshot()==before
        reject(invoke(*arguments(run,checkpoint,outcome='failed')),before)
        earlier=uuid.uuid4().hex
        accepted(invoke(*arguments(run,earlier,span_start_ms=now-40000,span_end_ms=now-30000)),run,earlier)
        assert [r['checkpoint_id'] for r in rows(run)[1:]]==[checkpoint,earlier]
        assert [r['duration_s'] for r in rows(run)[1:]]==[10,10]
    elif scenario == 'invalid':
        accepted(invoke(*arguments(run,checkpoint)),run,checkpoint)
        before=snapshot()
        bad_cases=[dict(session_id=None),dict(agent_id=''),dict(checkpoint_id='../secret'),
                   dict(session_id='private\nsecret'),dict(span_start_ms='-1'),dict(span_start_ms='01'),
                   dict(span_end_ms=str(now-21000)),dict(span_end_ms='9007199254740992'),
                   dict(span_end_ms=None),dict(span_start_ms='1.5'),dict(timing_source='inferred'),
                   dict(boundary='guess'),dict(parent_checkpoint_id=''),dict(step='unknown'),
                   dict(outcome='secret'),dict(stops='-1')]
        for changes in bad_cases:
            reject(invoke(*arguments(run,uuid.uuid4().hex,**changes)),before)
        later=uuid.uuid4().hex
        receipt=accepted(invoke(*arguments(run,later,span_start_ms=now,span_end_ms=now)),run,later)
        assert receipt['seq']==2 and rows(run)[-1]['duration_s']==0
    elif scenario == 'boundaries':
        first=rows(run)[0]
        assert isinstance(first.get('ts_ms'),int), ('missing executable millisecond run boundary',first)
        assert abs(first['ts_ms']-now)<5000,first
        receipt=accepted(invoke(*arguments(run,checkpoint,span_start_ms=now-125,span_end_ms=now)),run,checkpoint)
        record=rows(run)[-1]
        assert record['span_end_ms']-record['span_start_ms']==125,record
        assert record['duration_s']==0,record
        event_file=path(run)
        invoke('run-end','--run',run,'--outcome','completed')
        last=json.loads(event_file.read_text().splitlines()[-1])
        assert isinstance(last.get('ts_ms'),int) and last['ts_ms']>=first['ts_ms'],last
        assert 'span_start_ms' not in first and 'span_start_ms' not in last
    elif scenario == 'clock_format':
        # Exercise executable Unix clock stamps at a fraction with leading zeros.
        # Some coreutils versions format %3N as 650 for 006500000 nanoseconds.
        shim=fixture/'clock commands'; shim.mkdir()
        real_date=shutil.which('date'); assert real_date
        (shim/'date').write_text('#!/bin/bash\nexec '+shlex.quote(real_date)+
                                ' --date @1700000000.006500000 "$@"\n')
        (shim/'date').chmod(0o755)
        environment=dict(environment,PATH=str(shim)+':'+os.environ['PATH'])
        pinned=start()
        event_file=path(pinned)
        invoke('step','--run',pinned,'--step','dry-run','--outcome','ok')
        invoke('run-end','--run',pinned,'--outcome','completed')
        stamps=[json.loads(line)['ts_ms'] for line in event_file.read_text().splitlines()]
        assert stamps==[1700000000006]*3,stamps
    elif scenario == 'waiting':
        accepted(invoke(*arguments(run,checkpoint)),run,checkpoint)
        assert rows(run)[-1]['span_kind']=='work'
        child=uuid.uuid4().hex
        accepted(invoke(*arguments(run,child,span_kind='waiting',parent_checkpoint_id=checkpoint)),run,child)
        assert rows(run)[-1]['span_kind']=='waiting' and rows(run)[-1]['parent_checkpoint_id']==checkpoint
        before=snapshot()
        reject(invoke(*arguments(run,uuid.uuid4().hex,span_kind='guessed')),before)
        reject(invoke(*arguments(run,child,parent_checkpoint_id=child)),before)
        reject(invoke(*arguments(run,checkpoint,agent_id=uuid.uuid4().hex)),before)
        unknown=uuid.uuid4().hex
        result=invoke(*arguments(run,unknown,step='unknown',boundary='session',agent_id=session))
        receipt=json.loads(result.stdout)
        assert receipt['kind']=='accepted' and receipt['agent_id']==session and not result.stderr,result
        diagnostics=[json.loads(line) for line in invoke('lint','--all').stdout.splitlines()]
        assert diagnostics[-1]['invalid_lines']==0,diagnostics
    elif scenario == 'lint':
        accepted(invoke(*arguments(run,checkpoint)),run,checkpoint)
        legacy=invoke('step','--run',run,'--step','dry-run','--outcome','ok')
        assert not legacy.stdout and not legacy.stderr
        historical=rows(run)
        assert 'checkpoint_id' not in historical[-1]
        before=snapshot()
        result=invoke('lint','--all')
        diagnostics=[json.loads(line) for line in result.stdout.splitlines()]
        assert diagnostics[-1]['invalid_lines']==0,diagnostics
        assert snapshot()==before
        # New optional fields must be linted together; old records remain valid.
        malformed=dict(historical[1],span_end_ms=now-21000)
        with path(run).open('a') as stream: stream.write(json.dumps(malformed)+'\n')
        malformed=dict(historical[1]); del malformed['session_id']
        with path(run).open('a') as stream: stream.write(json.dumps(malformed)+'\n')
        before=snapshot()
        diagnostics=[json.loads(line) for line in invoke('lint','--all').stdout.splitlines()]
        assert diagnostics[-1]['invalid_lines']==2,diagnostics
        assert snapshot()==before
        # jq regex end anchors can match before a final newline; require the
        # entire historical identity to match the producer's ASCII contract.
        malformed=dict(historical[1],session_id=session+'\n')
        with path(run).open('a') as stream: stream.write(json.dumps(malformed)+'\n')
        before=snapshot()
        diagnostics=[json.loads(line) for line in invoke('lint','--all').stdout.splitlines()]
        assert diagnostics[-1]['invalid_lines']==3,diagnostics
        assert snapshot()==before
    elif scenario in ('append_retry','metadata_retry'):
        event_file=path(run)
        original=event_file.read_bytes()
        env=environment
        if scenario=='append_retry':
            event_file.unlink(); event_file.mkdir()
        else:
            shim=fixture/'commands'; shim.mkdir()
            real_mv=shutil.which('mv')
            (shim/'mv').write_text('#!/bin/bash\nfor arg in "$@"; do\n'
                '  [ "$arg" != "$CORRELATION_DENY_DEST" ] || exit 1\ndone\n'
                'exec '+str(real_mv)+' "$@"\n')
            (shim/'mv').chmod(0o755)
            env=dict(environment,PATH=str(shim)+':'+os.environ['PATH'],
                     CORRELATION_DENY_DEST=str(store/'.active'/run))
        before=snapshot()
        reject(invoke(*arguments(run,checkpoint),env=env),before)
        if scenario=='append_retry':
            event_file.rmdir(); event_file.write_bytes(original)
        receipt=accepted(invoke(*arguments(run,checkpoint)),run,checkpoint)
        assert receipt['seq']==1
        accepted(invoke(*arguments(run,checkpoint)),run,checkpoint,True)
        assert len(rows(run))==2,rows(run)
        if scenario=='append_retry':
            # Fail inside emit_json after real bytes reached the event inode.
            partial_run=start(); partial_checkpoint=uuid.uuid4().hex
            partial_file=path(partial_run); original_size=partial_file.stat().st_size
            shim=fixture/'partial commands'; shim.mkdir()
            real_jq=shutil.which('jq'); assert real_jq
            (shim/'jq').write_text('#!/bin/bash\nif [ "${1:-}" = -Rn ] && [[ "$*" = *from_entries* ]]; then\n  input="$(cat)"\n  if printf \'%s\\n\' "$input" | grep -q \'^event=step$\'; then\n    printf \'{"partial":\'\n    wc -c < "$CORRELATION_EVENT_FILE" > "$CORRELATION_PARTIAL_SIZE"\n    exit 1\n  fi\n  printf \'%s\\n\' "$input" | '+shlex.quote(real_jq)+' "$@"\n  exit $?\nfi\nexec '+shlex.quote(real_jq)+' "$@"\n')
            (shim/'jq').chmod(0o755)
            size_probe=fixture/'observed partial size'
            env=dict(environment,PATH=str(shim)+':'+os.environ['PATH'],
                     CORRELATION_EVENT_FILE=str(partial_file),CORRELATION_PARTIAL_SIZE=str(size_probe))
            before=snapshot()
            reject(invoke(*arguments(partial_run,partial_checkpoint),env=env),before)
            assert int(size_probe.read_text())>original_size, 'failure occurred before actual append'
            receipt=accepted(invoke(*arguments(partial_run,partial_checkpoint)),partial_run,partial_checkpoint)
            assert receipt['seq']==1
            accepted(invoke(*arguments(partial_run,partial_checkpoint)),partial_run,partial_checkpoint,True)
            assert len(rows(partial_run))==2,rows(partial_run)
    elif scenario=='contract':
        contract=dict(line.split('=',1) for line in invoke('contract').stdout.splitlines())
        for key in ('hook.required','hook.identity_pattern','hook.timing_source','hook.boundary'):
            assert key in contract, ('missing additive runtime contract',key)
        checkout=fixture/'checkout'
        for name in ('scripts/log-step.sh','scripts/validate-contracts.sh','rules/run-log.md'):
            target=checkout/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/name,target)
        def gate() -> subprocess.CompletedProcess[str]:
            return subprocess.run(['bash',str(checkout/'scripts/validate-contracts.sh'),
                                   '--run-log-contract-only'],capture_output=True,text=True)
        assert gate().returncode==0
        rule=checkout/'rules/run-log.md'; original=rule.read_text()
        rule.write_text(re.sub(r'^\| `hook.required` .*\n','',original,flags=re.M))
        result=gate(); assert result.returncode!=0 and 'hook.required' in result.stdout,result
        rule.write_text(original)
        copied=checkout/'scripts/log-step.sh'
        copied.write_text(re.sub(r'^  \[hook.required\].*\n','',copied.read_text(),flags=re.M))
        result=gate(); assert result.returncode!=0 and 'hook.required' in result.stdout,result
PYCORRELATED
}
test_run_log_correlated_concurrent_runs_preserve_identity() { run_correlated_event_smoke concurrent; }
test_run_log_correlated_duplicates_and_out_of_order_are_idempotent() { run_correlated_event_smoke duplicates; }
test_run_log_correlated_invalid_fields_preserve_accepted_state() { run_correlated_event_smoke invalid; }
test_run_log_correlated_lint_accepts_legacy_and_rejects_invalid_spans() { run_correlated_event_smoke lint; }
test_run_log_correlated_append_failure_allows_retry() { run_correlated_event_smoke append_retry; }
test_run_log_correlated_metadata_failure_allows_retry() { run_correlated_event_smoke metadata_retry; }
test_run_log_correlated_waiting_and_parent_identity_are_explicit() { run_correlated_event_smoke waiting; }
test_run_log_correlated_clock_boundaries_preserve_milliseconds() { run_correlated_event_smoke boundaries; }
test_run_log_correlated_clock_fraction_preserves_leading_zeros() { run_correlated_event_smoke clock_format; }
test_run_log_correlated_contract_detects_bidirectional_drift() { run_correlated_event_smoke contract; }
check "test_run_log_correlated_concurrent_runs_preserve_identity" \
  "$(test_run_log_correlated_concurrent_runs_preserve_identity && echo pass || echo 'concurrent correlated attribution failed')"
check "test_run_log_correlated_duplicates_and_out_of_order_are_idempotent" \
  "$(test_run_log_correlated_duplicates_and_out_of_order_are_idempotent && echo pass || echo 'correlated retry or out-of-order delivery failed')"
check "test_run_log_correlated_invalid_fields_preserve_accepted_state" \
  "$(test_run_log_correlated_invalid_fields_preserve_accepted_state && echo pass || echo 'invalid correlation changed accepted state')"
check "test_run_log_correlated_lint_accepts_legacy_and_rejects_invalid_spans" \
  "$(test_run_log_correlated_lint_accepts_legacy_and_rejects_invalid_spans && echo pass || echo 'correlated lint compatibility failed')"
check "test_run_log_correlated_append_failure_allows_retry" \
  "$(test_run_log_correlated_append_failure_allows_retry && echo pass || echo 'append failure lost a checkpoint')"
check "test_run_log_correlated_metadata_failure_allows_retry" \
  "$(test_run_log_correlated_metadata_failure_allows_retry && echo pass || echo 'metadata failure lost or duplicated a checkpoint')"
check "test_run_log_correlated_contract_detects_bidirectional_drift" \
  "$(test_run_log_correlated_contract_detects_bidirectional_drift && echo pass || echo 'correlated schema drift was not detected')"

check "test_run_log_correlated_clock_boundaries_preserve_milliseconds" \
  "$(test_run_log_correlated_clock_boundaries_preserve_milliseconds && echo pass || echo 'millisecond run boundaries missing')"
check "test_run_log_correlated_clock_fraction_preserves_leading_zeros" \
  "$(test_run_log_correlated_clock_fraction_preserves_leading_zeros && echo pass || echo 'clock fraction lost leading zeros')"
check "test_run_log_correlated_waiting_and_parent_identity_are_explicit" \
  "$(test_run_log_correlated_waiting_and_parent_identity_are_explicit && echo pass || echo 'waiting and parent identity contract failed')"
# Private producer regressions use disposable active metadata and public commands only.
run_private_producer_smoke() {
  python3 - "$REPO_ROOT" "$1" <<'PYPRIVATE'
from pathlib import Path
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
root, scenario = Path(sys.argv[1]), sys.argv[2]
with tempfile.TemporaryDirectory(prefix='private producer ') as temporary:
    fixture = Path(temporary)
    store = fixture/'store'
    environment = dict(os.environ, ORCHESTRAIL_HOME=str(root), ORCHESTRAIL_LOG_ROOT=str(store))
    helper = root/'scripts/log-step.sh'
    def invoke(*args: str | int, env: dict[str, str] | None = None,
               mask: int = 0o022) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(['bash',str(helper),*map(str,args)], env=env or environment,
                                capture_output=True,text=True,umask=mask)
        assert result.returncode == 0, result
        return result
    def start(mask: int = 0o022, env: dict[str, str] | None = None) -> str:
        result = invoke('run-start','--pipeline','private-probe',mask=mask,env=env)
        assert re.fullmatch('[0-9a-f]{8}\n',result.stdout) and not result.stderr, result
        return result.stdout.strip()
    def snapshot() -> dict[str, tuple[bytes, int]]:
        return {str(path.relative_to(store)):(path.read_bytes(),stat.S_IMODE(path.stat().st_mode))
                for path in store.rglob('*') if path.is_file()}
    now = time.time_ns()//1_000_000
    def arguments(run: str, checkpoint: str = 'checkpoint', **changes: object) -> list[str]:
        fields = dict(run=run,step='dry-run',outcome='ok',session_id='session',agent_id='agent',
                      checkpoint_id=checkpoint,span_start_ms=now-10,span_end_ms=now,
                      timing_source='hook',boundary='subagent')
        fields.update(changes)
        return ['step',*[part for key,value in fields.items()
                         for part in ('--'+key.replace('_','-'),str(value))]]
    def identity(run: str, checkpoint: str = 'checkpoint', **changes: object) -> dict[str, object]:
        expected = dict(kind='accepted',run_id=run,session_id='session',agent_id='agent',
                        checkpoint_id=checkpoint,duplicate=False)
        expected.update(changes)
        return expected
    def receipt(result: subprocess.CompletedProcess[str], expected: dict[str, object],
                seq: int | None = None) -> dict[str, object]:
        parsed = json.loads(result.stdout)
        assert type(parsed['seq']) is int and 0 < parsed['seq'] <= 9007199254740991, parsed
        expected = dict(expected,seq=parsed['seq'] if seq is None else seq)
        assert parsed == expected, (parsed,expected)
        return parsed
    failures = []
    if scenario == 'cache':
        run = start()
        first = invoke(*arguments(run))
        receipt(first,identity(run),seq=1)
        assert not first.stderr, first
        active = store/'.active'/run
        original = active.read_text()
        key = 'accepted|session|checkpoint='
        line = next(line for line in original.splitlines() if line.startswith(key))
        encoded = line[len(key):]
        cached = json.loads(encoded.replace('%0A','\n').replace('%25','%'))
        def cache_text(seq: str) -> str:
            return '{"arguments":'+json.dumps(cached['arguments'])+',"seq":'+seq+'}'
        cases = [(label,cache_text(token)) for label,token in (
            ('zero','0'),('exponent','1e0'),('negative','-1'),('fraction','1.5'),
            ('rounded-fraction','1.00000000000000000001'),('string','"1"'),
            ('boolean','true'),('null','null'),('array','[1]'),('overflow','9007199254740992'))]
        valid = cache_text('1')
        cases += [('multiple-objects',valid+' '+valid),('object-array','['+valid+']'),
                  ('object-boolean','false'),('object-null','null'),('trailing-junk',valid+' cache-secret'),
                  ('arguments-array','{"arguments":[],"seq":1}'),
                  ('arguments-null','{"arguments":null,"seq":1}'),
                  ('arguments-conflict',json.dumps(dict(cached,arguments=dict(cached['arguments'],outcome='failed')))),
                  ('missing-sequence',json.dumps(dict(arguments=cached['arguments'])))]
        cases += [('nul-after-object',valid+'\x00'),('nul-sequence',cache_text('1\x00')),
                  ('nul-key',valid.replace('"seq"','"se\x00q"')),
                  ('nul-string-value',valid.replace('dry-run','dry-\x00run'))]
        for label,value in cases:
            replacement = key+value.replace('%','%25').replace('\n','%0A')
            active.write_text(original.replace(line,replacement))
            before = snapshot()
            result = invoke(*arguments(run))
            safe_warning = (len(result.stderr.splitlines()) == 1 and
                            re.fullmatch(r'log-step: [A-Za-z0-9 _-]+\n',result.stderr) is not None and
                            not any(secret in result.stderr for secret in ('cache-secret',str(fixture),value)))
            if result.stdout or not safe_warning or snapshot() != before:
                failures.append((label,result.stdout,result.stderr,'unchanged',snapshot()==before))
        for token in ('1','9007199254740991'):
            value = cache_text(token)
            active.write_text(original.replace(line,key+value))
            before = snapshot()
            result = invoke(*arguments(run))
            receipt(result,identity(run,duplicate=True),seq=int(token))
            assert not result.stderr and snapshot() == before, (token,result)
        escaped_key = cache_text('1').replace('"seq"',r'"\u0073eq"')
        active.write_text(original.replace(line,key+escaped_key))
        before = snapshot()
        result = invoke(*arguments(run))
        receipt(result,identity(run,duplicate=True),seq=1)
        assert not result.stderr and snapshot() == before, result
        preserved = arguments(run,'escaped-values',note='literal%00%0A%25 and "\\u0000"\nbackslash\\')
        result = invoke(*preserved)
        receipt(result,identity(run,'escaped-values'),seq=2)
        assert not result.stderr, result
        before = snapshot()
        result = invoke(*preserved)
        receipt(result,identity(run,'escaped-values',duplicate=True),seq=2)
        assert not result.stderr and snapshot() == before, result
        assert not failures, ('invalid private accepted cache established acceptance or mutated storage',failures)
    elif scenario == 'permissions':
        commands = fixture/'commands'
        commands.mkdir()
        mode_log = fixture/'replacement modes'
        real_mv = shutil.which('mv')
        assert real_mv
        (commands/'mv').write_text('#!/bin/bash\n'
            'case "$2" in "$ORCHESTRAIL_LOG_ROOT"/.active/*)\n'
            '  stat -c %a -- "$1" >> "$PRIVATE_MODE_LOG" ;;\nesac\n'
            'exec '+shlex.quote(real_mv)+' "$@"\n')
        (commands/'mv').chmod(0o755)
        env = dict(environment,PATH=str(commands)+':'+os.environ['PATH'],PRIVATE_MODE_LOG=str(mode_log))
        nojq = fixture/'without jq'
        nojq.mkdir()
        for utility in ('bash','dirname','mkdir','od','tr','date','cat','uname','touch','grep',
                        'mv','sed','head','rm','wc','flock','stat'):
            executable = str(commands/'mv') if utility == 'mv' else shutil.which(utility)
            assert executable, utility
            (nojq/utility).symlink_to(executable)
        nojq_env = dict(env,PATH=str(nojq))
        assert not shutil.which('jq',path=nojq_env['PATH'])
        for mask in (0o002,0o000):
            for legacy_env in (env,nojq_env):
                run = start(mask=mask,env=legacy_env)
                active = store/'.active'/run
                event = Path(invoke('path','--run',run).stdout.strip())
                event_mode = stat.S_IMODE(event.stat().st_mode)
                def private(label: str) -> None:
                    mode = stat.S_IMODE(active.stat().st_mode)
                    if mode != 0o600:
                        failures.append((oct(mask),'jq' if legacy_env is env else 'no-jq',label,oct(mode)))
                    assert stat.S_IMODE(event.stat().st_mode) == event_mode, 'event permissions changed'
                private('run-start')
                for index in range(2):
                    result = invoke(*arguments(run,'checkpoint-'+str(index)),env=env,mask=mask)
                    receipt(result,identity(run,'checkpoint-'+str(index)))
                    assert not result.stderr, result
                    private('correlated')
                    accepted_lines = [line for line in active.read_text().splitlines() if line.startswith('accepted|')]
                    result = invoke('step','--run',run,'--step','dry-run','--outcome','ok',env=legacy_env,mask=mask)
                    assert not result.stdout and not result.stderr, result
                    private('ordinary')
                    assert [line for line in active.read_text().splitlines() if line.startswith('accepted|')] == accepted_lines
                records = [json.loads(line) for line in event.read_text().splitlines()]
                assert [row['seq'] for row in records] == [0,1,2,3,4], records
                assert len([row for row in records if 'checkpoint_id' in row]) == 2
                before = snapshot()
                result = invoke(*arguments(run,'checkpoint-0'),env=env,mask=mask)
                receipt(result,identity(run,'checkpoint-0',duplicate=True),seq=1)
                assert not result.stderr and snapshot() == before, result
        replacement_modes = mode_log.read_text().splitlines()
        assert replacement_modes, 'replacement permission probe did not observe writes'
        failures.extend(('temporary replacement',mode) for mode in replacement_modes if mode != '600')
        assert not failures, ('private metadata permissions widened',failures)
    elif scenario == 'advisory':
        run = start()
        for name in ('pae-tests','dry-run','arbitrary-private-skill','unknown'):
            changes = dict(step=name)
            if name == 'unknown':
                changes.update(boundary='session',agent_id='session')
            result = invoke(*arguments(run,name,**changes))
            receipt(result,identity(run,name,agent_id=changes.get('agent_id','agent')))
            expected = 'log-step: step name is not in the current workflow list\n' if name == 'arbitrary-private-skill' else ''
            if result.stderr != expected:
                failures.append((name,result.stderr,expected))
            before = snapshot()
            replay = invoke(*arguments(run,name,**changes))
            receipt(replay,identity(run,name,duplicate=True,agent_id=changes.get('agent_id','agent')))
            assert not replay.stderr and snapshot() == before, replay
            rejected = invoke(*arguments(run,name,**dict(changes,outcome='failed')))
            assert not rejected.stdout and snapshot() == before, rejected
            assert rejected.stderr == 'log-step: step checkpoint_id conflicting-delivery\n', rejected
        event = Path(invoke('path','--run',run).stdout.strip())
        records = [json.loads(line) for line in event.read_text().splitlines()]
        assert [row['step'] for row in records[1:]] == ['pae-tests','dry-run','arbitrary-private-skill','unknown'], records
        missing = dict(environment,ORCHESTRAIL_HOME=str(fixture/'missing workflows'))
        result = invoke(*arguments(run,'unavailable',step='pae-tests'),env=missing)
        receipt(result,identity(run,'unavailable'))
        if result.stderr != 'log-step: step-name verification unavailable\n':
            failures.append(('unavailable workflow definitions',result.stderr))
        before = snapshot()
        replay = invoke(*arguments(run,'unavailable',step='pae-tests'),env=missing)
        receipt(replay,identity(run,'unavailable',duplicate=True))
        assert not replay.stderr and snapshot() == before, replay
        rejected = invoke(*arguments(run,'rejected',step='arbitrary-private-skill',outcome='invalid'))
        assert not rejected.stdout and snapshot() == before, rejected
        assert rejected.stderr == 'log-step: step outcome invalid-enum\n', rejected
        assert not failures, ('new correlated acceptance skipped its step-name advisory',failures)
    else:
        raise AssertionError(scenario)
PYPRIVATE
}
test_run_log_private_cache_requires_canonical_positive_sequence() { run_private_producer_smoke cache; }
test_run_log_private_metadata_stays_private_across_ordinary_writes() { run_private_producer_smoke permissions; }
test_run_log_correlated_new_acceptance_reports_step_name_advisory() { run_private_producer_smoke advisory; }
check "test_run_log_private_cache_requires_canonical_positive_sequence" \
  "$(test_run_log_private_cache_requires_canonical_positive_sequence && echo pass || echo 'invalid accepted cache established duplicate acceptance')"
check "test_run_log_private_metadata_stays_private_across_ordinary_writes" \
  "$(test_run_log_private_metadata_stays_private_across_ordinary_writes && echo pass || echo 'ordinary metadata replacement widened private permissions')"
check "test_run_log_correlated_new_acceptance_reports_step_name_advisory" \
  "$(test_run_log_correlated_new_acceptance_reports_step_name_advisory && echo pass || echo 'new correlated acceptance skipped a required advisory')"

# ── End run-log producer smoke checks ───────────────────────────────

# ── Retrospective executable corpus contract ──────────────────────────
run_retro_smoke() {
  python3 - "$1" "$PWD" <<'PYRETRO'
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

scenario, root = sys.argv[1:]
root = Path(root)
text = (root / "workflows/retro.md").read_text()
blocks = re.findall(r"```bash\n(.*?)\n```", text, re.S)
loader = next((b for b in blocks if "# Retrospective corpus loader." in b), None)
assert loader is not None, "retro must provide an executable lint-aware corpus loader"
with tempfile.TemporaryDirectory(prefix="retro-contract-") as temporary:
    temp = Path(temporary)
    store = temp / "store"
    runs = store / "runs"
    runs.mkdir(parents=True)
    script = temp / "load.sh"
    script.write_text(loader)
    helper = root / "scripts/log-step.sh"
    base = dict(ts="2026-08-10T00:00:00Z", run_id="1234abcd", seq=0,
                pipeline="spec-run", project="/acme", flow="full")

    def write(name, changes=None, events=None):
        start = dict(base, event="run-start", **(changes or {}))
        rows = events if events is not None else [start]
        path = runs / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return path

    def snapshot():
        hashes = {}
        for directory in (runs, store / '.active'):
            for path in directory.rglob('*'):
                if path.is_symlink():
                    hashes[str(path)] = ('symlink', os.readlink(path))
                elif path.is_file():
                    try:
                        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                    except PermissionError:
                        hashes[str(path)] = ('unreadable', path.stat().st_mode, path.stat().st_size)
        return hashes

    def load(expect_mutation=False, **filters):
        before_read = snapshot()
        env = dict(os.environ, STORE=str(store), HELPER=str(helper),
                   SINCE="", PIPELINE="", PROJECT="", LIMIT="")
        env.update(filters)
        result = subprocess.run(["bash", str(script)], env=env,
                                text=True, capture_output=True)
        after_read = snapshot()
        if expect_mutation:
            assert before_read != after_read, "negative fixture must actually change the corpus"
        else:
            assert before_read == after_read, "retro changed historical fixture checksums"
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def metrics(data):
        before_read = snapshot()
        snippet = next(b for b in blocks if "# Retrospective metric inputs." in b)
        artifact = temp / "dataset.json"
        artifact.write_text(json.dumps(data))
        result = subprocess.run(["bash", "-c", snippet], text=True, capture_output=True,
                                env=dict(os.environ, RETRO_DATA=str(artifact)))
        assert result.returncode == 0, result.stderr
        assert snapshot() == before_read, "metrics changed historical fixture checksums"
        return json.loads(result.stdout)

    def step(**fields):
        return dict(base, event="step", seq=1, step="dry-run", outcome="ok", **fields)

    if scenario == "filters":
        write("2026-08-01-11111111.jsonl", {"ts": "2026-08-01T00:00:00Z"})
        write("2026-08-10-22222222.jsonl", {"pipeline": "other"})
        write("2026-08-10-33333333.jsonl", {"project": "/other"})
        selected = write("2026-08-10-44444444.jsonl", events=[dict(base, event="run-start"), step(tests="BAD")])
        newest = write("2026-08-11-55555555.jsonl", events=[dict(base, event="run-start"), step(tests="BAD", gate="BAD")])
        assert load(SINCE="2026-08-02")["total_runs"] == 4
        assert load(PIPELINE="spec-run")["total_runs"] == 4
        assert load(PROJECT="/acme")["total_runs"] == 4
        data = load(SINCE="2026-08-02", PIPELINE="spec-run", PROJECT="/acme", LIMIT="1")
        assert data["files"] == [str(newest)], data
        assert (data["total_runs"], data["examined_lines"], data["invalid_lines"], data["affected_runs"]) == (1, 2, 1, 1)
        assert data["violations"] == [{"field": "gate", "code": "invalid-enum", "count": 1}, {"field": "tests", "code": "invalid-enum", "count": 1}]
        assert data["examples"] == [{"file": str(newest), "line": 2}]
        assert data["status"] == "ok" and data["weak_evidence"] is True
        data = load(SINCE="2026-08-02", PIPELINE="spec-run", PROJECT="/acme", LIMIT="2")
        assert data["files"] == [str(newest), str(selected)]
        assert data["invalid_lines"] == 2 and data["affected_runs"] == 2
    elif scenario == "metrics":
        clean = write("2026-08-10-11111111.jsonl", events=[dict(base, event="run-start"), step(tests="n-a", stops=0), step(tests="green", stops=2), step(), step(tests="BAD", stops=900, duration_s=900), dict(base, event="run-end", seq=5, outcome="completed", duration_s=10)])
        invalid_close = write("2026-08-10-22222222.jsonl", events=[dict(base, event="run-start"), dict(base, event="run-end", outcome="BAD", duration_s=999)])
        missing_close = write("2026-08-10-33333333.jsonl")
        data = load()
        assert data["invalid_lines"] == 2 and data["affected_runs"] == 2
        assert data["abandoned_runs"] == 1 and data["unusable_closes"] == 1
        observations = data["usable_records"]
        steps = [r["record"] for r in observations if r["record"]["event"] == "step"]
        measured = [r for r in steps if "stops" in r]
        assert sum(r["stops"] for r in measured) == 2 and len(measured) == 2
        tests = [r["tests"] for r in steps if "tests" in r]
        assert tests.count("n-a") == 1 and len(tests) == 2
        closes = [r["record"] for r in observations if r["record"]["event"] == "run-end"]
        assert [r["duration_s"] for r in closes] == [10]
        aggregate = metrics(data)
        assert aggregate == {"stops": {"sum": 2, "observations": 2},
                             "tests": {"na": 1, "observations": 2, "na_share": 0.5},
                             "close_durations": [10]}
        assert all(r["line"] != 5 for r in observations if r["file"] == str(clean))
        assert {r["file"] for r in data["incomplete_runs"]} == {str(clean), str(invalid_close)}
    elif scenario == "boundaries":
        data = load()
        assert data["status"] == "ok" and data["total_runs"] == 0
        assert data["examined_lines"] == 0 and data["usable_records"] == []
        broken = runs / "2026-08-10-11111111.jsonl"
        broken.write_text("not-json\n" * 7)
        data = load()
        assert data["invalid_lines"] == 7 and data["examined_lines"] == 7
        assert data["usable_records"] == [] and len(data["examples"]) == 5
        assert metrics(data) == {"stops": {"sum": None, "observations": 0},
                                 "tests": {"na": 0, "observations": 0, "na_share": None},
                                 "close_durations": []}
        assert data["abandoned_runs"] == 1 and data["unusable_closes"] == 0
        assert data["violations"] == [{"field": "record", "code": "invalid-json", "count": 7}]
        assert load(PIPELINE="absent")["total_runs"] == 0
        broken.unlink()
        unusual = write('2026-08-12-newline\n1234abcd.jsonl',
                        events=[dict(base, event='run-start'), step(tests='BAD')])
        data = load()
        assert data['examples'] == [{'file': str(unusual), 'line': 2}]
        encoded_examples = json.dumps(data['examples'])
        assert '\n' not in encoded_examples and r'\n' in encoded_examples
        assert data['invalid_lines'] == 1 and data['affected_runs'] == 1
    elif scenario == "coverage":
        write("2026-08-10-11111111.jsonl", events=[dict(base, event="run-start"), step(stops=1)])
        actual = helper
        helper = temp / "lint.sh"
        for status in ("partial", "unavailable"):
            helper.write_text('''#!/bin/bash
[ "$1" = lint ] && [ "$2" = --all ] || exit 9
printf '%s\\n' '{"kind":"summary","status":"STATUS","files":1,"lines":1,"invalid_lines":0,"violations":0}'
'''.replace("STATUS", status))
            data = load()
            assert data["status"] == status and data["usable_records"] == []
            assert data["examined_lines"] is None and data["affected_runs"] == 1
            assert data["limitations"] and len(data["incomplete_runs"]) == 1
        violation = dict(kind="violation", file=str(runs / "2026-08-10-11111111.jsonl"),
                         line=2, field="outcome", code="invalid-enum")
        summary = dict(kind="summary", status="partial", files=1, lines=2,
                       invalid_lines=1, violations=1)
        payload = json.dumps(violation) + "\n" + json.dumps(summary)
        helper.write_text("#!/bin/bash\nprintf '%s\\n' " + shlex.quote(payload) + "\n")
        data = load()
        assert data["invalid_lines"] == 1 and data["invalid_lines_exact"] is False
        assert data["violations"] == [{"field": "outcome", "code": "invalid-enum", "count": 1}]
        assert data["examples"] == [{"file": violation["file"], "line": 2}]
        assert metrics(data)["stops"] == {"sum": None, "observations": 0}
        helper.write_text('#!/bin/bash\nexit 0\n')
        data = load()
        assert data["status"] == "unavailable" and data["usable_records"] == []
        helper.write_text("#!/bin/bash\nprintf '%s\\n' '{}' >> \"$ORCHESTRAIL_LOG_ROOT/runs/2026-08-10-11111111.jsonl\"\n"
                          + "bash " + shlex.quote(str(actual)) + " lint --all\n")
        data = load(expect_mutation=True)
        assert data["status"] == "partial" and data["usable_records"] == []
        assert data["examined_lines"] is None
        helper = actual
        (runs / "2026-08-11-22222222.jsonl").symlink_to(temp / "missing")
        data = load()
        assert data["status"] == "partial" and data["usable_records"] == []
        assert data["examined_lines"] is None and data["limitations"]
        helper = actual
        (runs / "2026-08-11-22222222.jsonl").unlink()
        runs.chmod(0)
        try:
            data = load()
            assert data['status'] == 'unavailable' and data['usable_records'] == []
            assert data['examined_lines'] is None and data['limitations']
        finally:
            runs.chmod(0o700)
        absent_store = temp / 'absent store'
        saved_store, saved_runs = store, runs
        store, runs = absent_store, absent_store / 'runs'
        data = load()
        assert data['status'] == 'ok' and data['total_runs'] == 0 and not absent_store.exists()
        store, runs = saved_store, saved_runs
        minimal = temp / "minimal-path"
        minimal.mkdir()
        (minimal / "bash").symlink_to(shutil.which("bash"))
        helper = temp / "no-jq-lint.sh"
        helper.write_text('#!/bin/bash\n[ "$1" = lint ] && [ "$2" = --all ] || exit 9\n'
                          'printf checked > "$ORCHESTRAIL_LOG_ROOT/lint-called"\n')
        data = load(PATH=str(minimal))
        assert data["status"] == "unavailable" and data["limitations"]
        assert (store / "lint-called").read_text() == "checked"
        assert "usable_records" not in data or data["usable_records"] == []
    else:
        raise AssertionError("unknown retrospective scenario")
PYRETRO
}

test_retro_filters_intersect_exact_selected_corpus() { run_retro_smoke filters; }
test_retro_invalid_records_never_enter_metric_observations() { run_retro_smoke metrics; }
test_retro_empty_and_invalid_corpora_report_safe_counts() { run_retro_smoke boundaries; }
test_retro_incomplete_lint_never_implies_clean_measurements() { run_retro_smoke coverage; }

check "RETRO: combined filters and limit align lint diagnostics" \
  "$(test_retro_filters_intersect_exact_selected_corpus && echo pass || echo 'retrospective corpus filters or lint intersection failed')"
check "RETRO: invalid observations and unusable closes are excluded" \
  "$(test_retro_invalid_records_never_enter_metric_observations && echo pass || echo 'retrospective usable observations or close classification failed')"
check "RETRO: empty and all-invalid corpora remain measurable honestly" \
  "$(test_retro_empty_and_invalid_corpora_report_safe_counts && echo pass || echo 'retrospective boundary counts or safe examples failed')"
check "RETRO: incomplete lint discloses unverified observations" \
  "$(test_retro_incomplete_lint_never_implies_clean_measurements && echo pass || echo 'retrospective incomplete coverage was treated as clean')"

# ── End retrospective executable corpus contract ─────────────────────

# ── Isolated run-log acceptance harness ──────────────────────────────
test_run_log_acceptance_harness_isolated_and_complete() {
  python3 - "$REPO_ROOT" <<'PYACCEPTANCE'
from pathlib import Path
import hashlib, os, re, shutil, signal, subprocess, sys, tempfile
root = Path(sys.argv[1])
harness = root / 'tests/log-step.sh'
assert harness.is_file() and os.access(harness, os.X_OK), 'missing executable isolated run-log harness'
source = (root / 'scripts/validate-contracts.sh').read_text()
required = set(re.findall(r'^(test_(?:run_log|retro)_[a-z_]+)\(\)', source, re.M))
required.remove('test_run_log_acceptance_harness_isolated_and_complete')
assert len(required) >= 20, required
with tempfile.TemporaryDirectory(prefix='acceptance meta ') as temporary:
    fixture = Path(temporary)
    checkout = fixture / 'checkout with spaces'
    for directory in ('scripts', 'rules', 'workflows', 'tests'):
        (checkout / directory).mkdir(parents=True)
    for name in ('scripts/log-step.sh', 'scripts/validate-contracts.sh', 'rules/run-log.md', 'tests/log-step.sh'):
        shutil.copy2(root / name, checkout / name)
    for workflow in (root / 'workflows').glob('*.md'):
        shutil.copy2(workflow, checkout / 'workflows' / workflow.name)
    hostile = fixture / 'inherited store'
    hostile.mkdir()
    (hostile / 'sentinel').write_bytes(b'private fixture must stay untouched\n')
    scratch = fixture / 'temporary children'
    scratch.mkdir()
    env = dict(os.environ, ORCHESTRAIL_HOME=str(fixture / 'missing inherited home'),
               ORCHESTRAIL_LOG_ROOT=str(hostile), TMPDIR=str(scratch))
    def snapshot():
        return {str(p.relative_to(hostile)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in hostile.rglob('*') if p.is_file()}
    before = snapshot()
    command = ['bash', str(checkout / 'tests/log-step.sh')]
    result = subprocess.run(command, env=env, cwd=fixture, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    passed = set(re.findall(r'^\[PASS\] (test_[a-z_]+)$', result.stdout, re.M))
    assert required <= passed, ('harness did not execute required checks', sorted(required - passed))
    assert snapshot() == before and not (fixture / 'missing inherited home').exists()
    assert list(scratch.iterdir()) == [], 'successful harness leaked fixtures'
    # A focused check must fail the runner even when its caller tests its status.
    validator = checkout / 'scripts/validate-contracts.sh'
    original = validator.read_text()
    needle = 'test_run_log_contract_documents_effective_runtime_tables() { run_log_contract_smoke tables; }'
    assert needle in original
    validator.write_text(original.replace(needle,
        'test_run_log_contract_documents_effective_runtime_tables() { false; echo masked-failure; }', 1))
    result = subprocess.run(command, env=env, cwd=fixture, capture_output=True, text=True, timeout=180)
    assert result.returncode != 0, 'harness masked a failing assertion'
    assert snapshot() == before and list(scratch.iterdir()) == [], 'failed harness leaked or changed storage'
    # Stop during a real focused check; no sleeps or timing assumptions are needed.
    validator.write_text(original.replace(needle,
        'test_run_log_contract_documents_effective_runtime_tables() { kill -TERM "$PPID"; exit 99; }', 1))
    result = subprocess.run(command, env=env, cwd=fixture, capture_output=True, text=True, timeout=180)
    assert result.returncode != 0, 'interrupted harness reported success'
    assert snapshot() == before and list(scratch.iterdir()) == [], 'interrupted harness leaked fixtures'
    # An absent inherited log root must stay absent as well.
    validator.write_text(original.replace(needle,
        'test_run_log_contract_documents_effective_runtime_tables() { exit 29; }', 1))
    absent = fixture / 'absent inherited store'
    result = subprocess.run(command, env=env | {'ORCHESTRAIL_LOG_ROOT': str(absent)},
                            cwd=fixture, capture_output=True, text=True, timeout=180)
    assert result.returncode != 0 and not absent.exists()
    assert list(scratch.iterdir()) == [], 'absent-root run leaked fixtures'
PYACCEPTANCE
}
check "test_run_log_acceptance_harness_isolated_and_complete" \
  "$(test_run_log_acceptance_harness_isolated_and_complete && echo pass || echo 'isolated executable harness, coverage, failure propagation, or cleanup failed')"

# ── End isolated run-log acceptance harness ─────────────────────────

# ── Contract version smoke checks ───────────────────────────────────
test_contract_version_root_has_exact_release_value() {
  [ -f VERSION ] && cmp -s VERSION <(printf '0.9.0\n')
}

test_contract_version_analysis_stamps_state_and_accepts_legacy() {
  # Markdown is the executable interface for analysis; verify its declared output.
  grep -qE '^spec_path: ' workflows/pd-analyze.md &&
    grep -A1 -E '^spec_path: ' workflows/pd-analyze.md | grep -qE '^contract_version: ' &&
    grep -q 'VERSION' workflows/pd-analyze.md &&
    grep -qiE '(absent|missing|without|unavailable).*VERSION|VERSION.*(absent|missing|without|unavailable)' workflows/pd-analyze.md &&
    grep -qiE '(legacy|older|readers).*contract_version|contract_version.*(legacy|older|readers)' workflows/pd-analyze.md
}

test_contract_version_run_start_stamps_current_and_reads_legacy() (
  local fixture run file value
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/contract-log.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  mkdir -p "$fixture/scripts" || return 1
  cp scripts/log-step.sh "$fixture/scripts/log-step.sh" || return 1
  # Test the helper against its own checkout, independently of the caller's cwd.
  for value in 0.9.0 1.2.3 absent empty malformed; do
    rm -f "$fixture/VERSION"
    case "$value" in
      absent) ;;
      empty) : > "$fixture/VERSION" ;;
      malformed) printf 'invalid\nextra\n' > "$fixture/VERSION" ;;
      *) printf '%s\n' "$value" > "$fixture/VERSION" ;;
    esac
    run="$(AGENTIC_LOG_ROOT="$fixture/store-$value" bash "$fixture/scripts/log-step.sh" run-start --pipeline phase-discovery)" || return 1
    file="$(AGENTIC_LOG_ROOT="$fixture/store-$value" bash "$fixture/scripts/log-step.sh" path --run "$run")" || return 1
    python3 - "$file" "$value" <<'PYVERSION'
import json
import sys
from pathlib import Path
record = json.loads(Path(sys.argv[1]).read_text())
expected = sys.argv[2]
assert record['event'] == 'run-start'
if expected in ('0.9.0', '1.2.3'):
    assert record.get('contract_version') == expected, record
else:
    assert 'contract_version' not in record, record
# Historical events omit the optional field and remain ordinary JSON records.
legacy = dict(record)
legacy.pop('contract_version', None)
assert json.loads(json.dumps(legacy))['event'] == 'run-start'
PYVERSION
    [ "$?" -eq 0 ] || return 1
    AGENTIC_LOG_ROOT="$fixture/store-$value" bash "$fixture/scripts/log-step.sh" run-end --run "$run" --outcome completed || return 1
  done
  grep -qE '^.*contract_version.*' rules/run-log.md &&
    grep -qiE '(legacy|older|optional|missing|absent).*contract_version|contract_version.*(legacy|older|optional|missing|absent)' rules/run-log.md
)

test_contract_version_rule_history_warns_until_version_changes() (
  local fixture root output warning
  root="$(pwd -P)"
  warning='[WARN] Rules changed after VERSION; update the contract version before release.'
  fixture="$(mktemp -d "${TMPDIR:-/tmp}/contract-history.XXXXXX")" || return 1
  trap 'rm -rf "$fixture"' EXIT
  # Run the real validator in a disposable repository. Remove this smoke group
  # from its copy to avoid recursively creating more fixture repositories.
  tar --exclude=.git --exclude=logs -cf - . | tar -xf - -C "$fixture" || return 1
  python3 - "$fixture/scripts/validate-contracts.sh" <<'PYVERSION' || return 1
from pathlib import Path
import re
import sys
path = Path(sys.argv[1])
for opening, closing in (
    ('# ── Run-log producer smoke checks', '# ── End run-log producer smoke checks'),
    ('# ── Run-log contract smoke checks', '# ── End run-log contract smoke checks'),
    ('# ── Isolated run-log acceptance harness', '# ── End isolated run-log acceptance harness'),
    ('# ── Contract version smoke checks', '# ── End contract version smoke checks'),
    ('# ── Public package materials smoke checks', '# ── End public package materials smoke checks'),
    ('# ── Public identity smoke checks', '# ── End public identity smoke checks'),
):
    lines = path.read_text().splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(opening))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(closing))
    retained = []
    if opening == '# ── Run-log producer smoke checks':
        block = ''.join(lines[start + 1:end])
        block, removed = re.subn(r'^check [^\n]*\\\n  "\$\([^\n]*\)"\n', '', block, flags=re.M)
        assert removed == 31 and not re.search(r'^check ', block, re.M), 'unexpected producer check shape'
        retained = [block]
    path.write_text(''.join(lines[:start] + retained + lines[end + 1:]))
PYVERSION
  cd "$fixture" || return 1
  git init -q || return 1
  git config user.name 'Contract Fixture' || return 1
  git config user.email 'fixture@example.invalid' || return 1
  printf '0.9.0\n' > VERSION
  git add . || return 1
  GIT_AUTHOR_DATE=2026-01-01T00:00:00Z GIT_COMMITTER_DATE=2026-01-01T00:00:00Z git commit -qm 'Initialize contract fixture' || return 1
  if ! output="$(bash scripts/validate-contracts.sh 2>&1)"; then
    printf '%s\n' "$output"
    echo 'Validator failed at the version commit'; return 1
  fi
  if grep -Fq "$warning" <<< "$output"; then
    echo 'Unexpected version warning at the version commit'; return 1
  fi
  printf '\nFixture rule change.\n' >> rules/run-log.md
  git add rules/run-log.md || return 1
  GIT_AUTHOR_DATE=2026-01-02T00:00:00Z GIT_COMMITTER_DATE=2026-01-02T00:00:00Z git commit -qm 'Change a rule contract' || return 1
  if ! output="$(bash scripts/validate-contracts.sh 2>&1)"; then
    printf '%s\n' "$output"
    echo 'Validator failed while reporting a stale rule version'; return 1
  fi
  if ! grep -Fq "$warning" <<< "$output"; then
    echo 'Missing warning for a rule commit newer than unchanged VERSION'; return 1
  fi
  printf '0.9.1\n' > VERSION
  if ! output="$(bash scripts/validate-contracts.sh 2>&1)"; then
    printf '%s\n' "$output"
    echo 'Validator failed after updating VERSION'; return 1
  fi
  if grep -Fq "$warning" <<< "$output"; then
    echo 'Version update in worktree must clear the warning'; return 1
  fi
)

check "test_contract_version_root_has_exact_release_value" \
  "$(test_contract_version_root_has_exact_release_value && echo pass || echo 'VERSION must contain exactly 0.9.0 followed by newline')"
check "test_contract_version_analysis_stamps_state_and_accepts_legacy" \
  "$(test_contract_version_analysis_stamps_state_and_accepts_legacy && echo pass || echo 'analysis must stamp version after spec_path and preserve legacy states')"
check "test_contract_version_run_start_stamps_current_and_reads_legacy" \
  "$(test_contract_version_run_start_stamps_current_and_reads_legacy && echo pass || echo 'run-start version metadata or legacy compatibility is incomplete')"
check "test_contract_version_rule_history_warns_until_version_changes" \
  "$(test_contract_version_rule_history_warns_until_version_changes && echo pass || echo 'rule-history version warning behavior is incomplete')"
# ── End contract version smoke checks ───────────────────────────────

# ── Public package materials smoke checks ───────────────────────────
test_public_package_overview_and_release_policy() {
  local line_count readme task_state='.ai/tasks/completed/task-01-git-source-of-truth/state.md'
  line_count="$(wc -l < README.md)" || return 1
  [ "$line_count" -le 60 ] || return 1
  readme="$(tr '\n\t' '  ' < README.md | sed -E 's/[[:space:]]+/ /g')" || return 1
  grep -qi 'Orchestrail' <<< "$readme" || return 1
  grep -qiE 'AI|agent' <<< "$readme" || return 1
  grep -qiE 'workflow|process' <<< "$readme" || return 1
  grep -qiE '(versions? (below|under|before) 1\.0\.0|pre.?1\.0(\.0)?).{0,80}unstable' <<< "$readme" || return 1
  grep -qiE 'sync\.sh.*~/?\.claude.*~/?\.codex|sync\.sh.*~/?\.codex.*~/?\.claude' <<< "$readme" || return 1
  grep -Fq '](docs/USAGE.md)' <<< "$readme" || return 1
  grep -Fq '](docs/SPEC-RUN-QUICKSTART.md)' <<< "$readme" || return 1
  grep -Fq '](.ai/specs/README.md)' <<< "$readme" || return 1
  [ -f "$task_state" ] || return 1
  [ ! -e LICENSE ] || return 1
  grep -Fq -- '- Apache-2.0 license | deferred |' "$task_state" || return 1
  grep -qi 'exact copyright-holder wording' "$task_state" || return 1
  grep -Fq -- '- v0.9.0 release tag | deferred |' "$task_state"
}

test_public_ignore_rules_keep_local_data_ignored_and_knowledge_trackable() {
  [ -f logs/.gitignore ] || return 1
  grep -qE '^/?logs/runs/?$' .gitignore || return 1
  grep -qE '^/?logs/\.active/?$' .gitignore || return 1
  grep -qE '^/?\.claude/settings\.local\.json$' .gitignore || return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- logs/runs/package-smoke.log || return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- logs/.active/package-smoke.jsonl || return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- .claude/settings.local.json || return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- .ai/specs/README.md && return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- docs/USAGE.md && return 1
  git -c core.excludesFile=/dev/null check-ignore --no-index -q -- logs/.gitignore && return 1
  ! grep -qE '^[[:space:]]*/?logs/?[[:space:]]*(#.*)?$' .gitignore
}

test_public_setup_guide_uses_orchestrail_release_instructions() {
  local section public_host public_repo public_join public_suffix public_url
  public_host='AlekseiChirkov'
  public_repo='agentic'
  public_join='-'
  public_suffix='workflows.git'
  public_url="https://github.com/${public_host}/${public_repo}${public_join}${public_suffix}"
  section="$(awk '/^## 4\. Initial Setup/{inside=1} /^## / && inside && !/^## 4\. Initial Setup/{exit} inside{print}' docs/USAGE.md)" || return 1
  grep -Fq "git clone ${public_url} ~/projects/orchestrail" <<< "$section" || return 1
  grep -Fq 'v0.9.0' <<< "$section" || return 1
  grep -qiE 'v0\.9\.0.{0,100}(after|once|following).*release|(after|once|following).*release.{0,100}v0\.9\.0' <<< "$(tr '\n' ' ' <<< "$section")"
}

check "test_public_package_overview_and_release_policy" \
  "$(test_public_package_overview_and_release_policy && echo pass || echo 'README must identify Orchestrail, state its purpose and instability policy, describe sync destinations, link the required guides, stay within 60 lines, and preserve the recorded license and tag deferrals')"
check "test_public_ignore_rules_keep_local_data_ignored_and_knowledge_trackable" \
  "$(test_public_ignore_rules_keep_local_data_ignored_and_knowledge_trackable && echo pass || echo 'ignore rules must exclude local run data and machine settings while keeping .ai/, docs/, and logs/.gitignore eligible for tracking')"
check "test_public_setup_guide_uses_orchestrail_release_instructions" \
  "$(test_public_setup_guide_uses_orchestrail_release_instructions && echo pass || echo 'USAGE section 4 must give the live clone URL, Orchestrail checkout path, and v0.9.0 as the post-release tag')"
# ── End public package materials smoke checks ───────────────────────

# ── Public identity smoke checks ────────────────────────────────────
test_public_identity_matches_exact_ledger_and_preserves_knowledge() (
  local root scratch files ledger_file ledger_heading ledger_title ledger_suffix baseline_commit
  local path_field line_field token_field path lines token count line_number file input
  local row candidate_count=0 row_count=0 expected_count=0 identity_prefix identity_join identity_suffix identity_pattern
  local content token_entry matches status
  local -A token_counts=()
  root="$(pwd -P)" || return 1
  scratch="$(mktemp -d "${TMPDIR:-/tmp}/identity-scan.XXXXXX")" || return 1
  trap 'rm -rf "$scratch"' EXIT

  # Assemble the scan term so the validator never stores the complete former name.
  identity_prefix='agentic'
  identity_join='[_-]'
  identity_suffix='workflows'
  identity_pattern="${identity_prefix}${identity_join}${identity_suffix}"

  git ls-files --cached --others --exclude-standard -z > "$scratch/all-files" || return 1
  : > "$scratch/scan-files" || return 1

  # The one state record carrying the ledger is discovered by its unique heading.
  # Split the heading fragments so this source cannot discover itself as the ledger.
  ledger_title='Exact Identity'
  ledger_suffix='Match Ledger'
  ledger_heading="### ${ledger_title} ${ledger_suffix}"
  while IFS= read -r -d '' candidate; do
    if [ -f "$root/$candidate" ] && grep -Fq "$ledger_heading" "$root/$candidate"; then
      ledger_file="$candidate"
      candidate_count=$((candidate_count + 1))
    fi
  done < "$scratch/all-files"
  [ "$candidate_count" -eq 1 ] || {
    echo 'Expected exactly one identity match ledger'; return 1;
  }

  # Scan all repository files. Mask only the markdown table rows beneath the
  # discovered ledger heading; its heading and surrounding prose remain scanned.
  while IFS= read -r -d '' file; do
    printf '%s\0' "$file" >> "$scratch/scan-files" || return 1
  done < "$scratch/all-files"

  awk -F'|' -v start="$ledger_heading" '
    function valid_row() {
      return NF == 5 && substr($0, 1, 1) == "|" && substr($0, length($0), 1) == "|" &&
        $1 ~ /^[[:space:]]*$/ && $5 ~ /^[[:space:]]*$/ &&
        $2 ~ /^[[:space:]]*`[^`]+`[[:space:]]*$/ &&
        $3 ~ /^[[:space:]]*[0-9]+(,[[:space:]]*[0-9]+)*[[:space:]]*$/ &&
        $4 ~ /^[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?([[:space:]]*;[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?)*[[:space:]]*$/
    }
    $0 == start { in_ledger = 1; next }
    in_ledger && /^### / { in_ledger = 0 }
    in_ledger && /^\|/ {
      if ($0 == "| Path | Line | Expected token counts |" || $0 == "|---|---:|---|") next
      if (valid_row()) { print; found = 1; next }
      invalid = 1
    }
    END { if (!found || invalid) exit 1 }
  ' "$ledger_file" > "$scratch/ledger-rows" || {
    echo 'Identity ledger has no exact path rows'; return 1;
  }

  : > "$scratch/expected" || return 1
  while IFS= read -r row; do
    IFS='|' read -r _ path_field line_field token_field _ <<< "$row"
    path="$(sed -E 's/^[[:space:]]*`([^`]*)`.*/\1/' <<< "$path_field")" || return 1
    lines="$(tr -d '[:space:]' <<< "$line_field")" || return 1
    case "$path" in
      ''|/*|../*|*/../*) echo 'Identity ledger contains an invalid path'; return 1 ;;
    esac
    [ -n "$lines" ] && [ -n "$token_field" ] || {
      echo 'Identity ledger contains an incomplete row'; return 1;
    }
    printf '%s\0' "$path" >> "$scratch/scan-files" || return 1
    row_count=$((row_count + 1))

    IFS=',' read -r -a line_entries <<< "$lines"
    IFS=';' read -r -a token_entries <<< "$token_field"
    [ "${#line_entries[@]}" -gt 0 ] && [ "${#token_entries[@]}" -gt 0 ] || return 1
    for line_number in "${line_entries[@]}"; do
      [[ "$line_number" =~ ^[0-9]+$ ]] || {
        echo 'Identity ledger contains an invalid line number'; return 1;
      }
      for token_entry in "${token_entries[@]}"; do
        token="$(sed -nE 's/.*`([^`]*)`.*/\1/p' <<< "$token_entry")" || return 1
        count="$(sed -nE 's/.*×[[:space:]]*([0-9]+).*/\1/p' <<< "$token_entry")" || return 1
        [[ -n "$token" && "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]] || {
          echo 'Identity ledger contains an invalid token count'; return 1;
        }
        printf '%s\t%s\t%s\t%s\n' "$path" "$line_number" "$token" "$count" >> "$scratch/expected" || return 1
        expected_count=$((expected_count + 1))
      done
    done
  done < "$scratch/ledger-rows"
  [ "$row_count" -gt 0 ] && [ "$expected_count" -gt 0 ] || return 1

  sort -zu "$scratch/scan-files" -o "$scratch/scan-files" || return 1
  : > "$scratch/actual" || return 1
  while IFS= read -r -d '' file; do
    if [ -L "$root/$file" ]; then
      readlink -- "$root/$file" > "$scratch/link" || {
        printf 'Cannot read scanned symlink: %s\n' "$file"; return 1;
      }
      input="$scratch/link"
    elif [ -f "$root/$file" ] && [ -r "$root/$file" ]; then
      input="$root/$file"
    else
      printf 'Scanned path is missing or unreadable: %s\n' "$file"; return 1
    fi

    if [ "$file" = "$ledger_file" ]; then
      awk -F'|' -v start="$ledger_heading" '
        function valid_row() {
          return NF == 5 && substr($0, 1, 1) == "|" && substr($0, length($0), 1) == "|" &&
            $1 ~ /^[[:space:]]*$/ && $5 ~ /^[[:space:]]*$/ &&
            $2 ~ /^[[:space:]]*`[^`]+`[[:space:]]*$/ &&
            $3 ~ /^[[:space:]]*[0-9]+(,[[:space:]]*[0-9]+)*[[:space:]]*$/ &&
            $4 ~ /^[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?([[:space:]]*;[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?)*[[:space:]]*$/
        }
        $0 == start { in_ledger = 1; print; next }
        in_ledger && /^### / { in_ledger = 0 }
        in_ledger && valid_row() { print ""; next }
        { print }
      ' "$input" > "$scratch/ledger-source-scan" || return 1
      input="$scratch/ledger-source-scan"
    fi

    line_number=0
    while IFS= read -r content || [ -n "$content" ]; do
      line_number=$((line_number + 1))
      token_counts=()
      status=0
      matches="$(printf '%s\n' "$content" | grep -aEio "$identity_pattern")" || status=$?
      case "$status" in
        0)
          while IFS= read -r token; do
            token_counts["$token"]=$(( ${token_counts["$token"]:-0} + 1 ))
          done <<< "$matches"
          for token in "${!token_counts[@]}"; do
            printf '%s\t%s\t%s\t%s\n' "$file" "$line_number" "$token" "${token_counts[$token]}" >> "$scratch/actual" || return 1
          done
          ;;
        1) ;;
        *) printf 'Identity scan failed on %s:%s\n' "$file" "$line_number"; return 1 ;;
      esac
    done < "$input"
  done < "$scratch/scan-files"

  LC_ALL=C sort "$scratch/expected" -o "$scratch/expected" || return 1
  LC_ALL=C sort "$scratch/actual" -o "$scratch/actual" || return 1
  if ! diff -u "$scratch/expected" "$scratch/actual" > "$scratch/diff"; then
    echo 'Identity scan differs from the exact path, line, token, and count ledger:'
    sed -n '1,80p' "$scratch/diff"
    return 1
  fi

  # The recorded base commit defines the knowledge inventory before this change.
  baseline_commit="$(awk '/^  base_commit:/ { value = $2; found = 1 } END { if (found) print value }' "$ledger_file")"
  [[ "$baseline_commit" =~ ^[[:xdigit:]]{40}$ ]] || {
    echo 'Identity ledger state has no valid baseline commit'; return 1;
  }
  git cat-file -e "${baseline_commit}^{commit}" 2>/dev/null || {
    echo 'Identity ledger baseline commit is unavailable'; return 1;
  }
  git ls-tree -r --name-only "$baseline_commit" -- .ai > "$scratch/baseline" || return 1
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    if [ ! -e "$file" ]; then
      case "$file" in
        .ai/tasks/todo/*) file=".ai/tasks/completed/${file#.ai/tasks/todo/}" ;;
        .ai/specs/*) file=".ai/specs/completed/${file#.ai/specs/}" ;;
      esac
    fi
    [ -e "$file" ] || { printf 'Knowledge file was removed: %s\n' "$file"; return 1; }
    git ls-files --error-unmatch -- "$file" >/dev/null 2>&1 || {
      printf 'Knowledge file is no longer tracked: %s\n' "$file"; return 1;
    }
  done < "$scratch/baseline"
)

check "test_public_identity_matches_exact_ledger_and_preserves_knowledge" \
  "$(test_public_identity_matches_exact_ledger_and_preserves_knowledge && echo pass || echo 'identity occurrences must match the exact ledger and baseline knowledge files must remain')"
# ── End public identity smoke checks ────────────────────────────────

# Run producer contract export fixtures during ordinary validation as well.
test_usage_contract_export_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-contract-export.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_contract_export_acceptance" \
  "$(test_usage_contract_export_acceptance && echo pass || echo 'usage contract export fixtures must pass')"

# Run current run snapshot fixtures during ordinary validation as well.
test_usage_current_snapshot_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-current-run-snapshot-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_current_snapshot_acceptance" \
  "$(test_usage_current_snapshot_acceptance && echo pass || echo 'current snapshot fixtures must pass')"

# Run lifecycle projection fixtures during ordinary validation as well.
test_usage_projection_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-lifecycle-projection-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_projection_acceptance" \
  "$(test_usage_projection_acceptance && echo pass || echo 'lifecycle projection fixtures must pass')"

# Run publication receipt fixtures during ordinary validation as well.
test_usage_receipt_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-usage-receipt-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_receipt_acceptance" \
  "$(test_usage_receipt_acceptance && echo pass || echo 'usage receipt fixtures must pass')"

# Run analysis corpus fixtures during ordinary validation as well.
test_usage_analysis_corpus_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-analysis-corpus-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_analysis_corpus_acceptance" \
  "$(test_usage_analysis_corpus_acceptance && echo pass || echo 'usage analysis corpus fixtures must pass')"

# Run warning policy fixtures during ordinary validation as well.
test_usage_warning_policy_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-warning-policy-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_warning_policy_acceptance" \
  "$(test_usage_warning_policy_acceptance && echo pass || echo 'usage warning policy fixtures must pass')"

# Run pricing scenario fixtures during ordinary validation as well.
test_usage_pricing_scenario_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-pricing-scenario-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_pricing_scenario_acceptance" \
  "$(test_usage_pricing_scenario_acceptance && echo pass || echo 'usage pricing scenario fixtures must pass')"

# Run price snapshot fixtures during ordinary validation as well.
test_usage_price_snapshot_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-price-snapshot-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_price_snapshot_acceptance" \
  "$(test_usage_price_snapshot_acceptance && echo pass || echo 'usage price snapshot fixtures must pass')"

# Run diagnostic measurement fixtures during ordinary validation as well.
test_usage_diagnostic_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-diagnostic-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_diagnostic_acceptance" \
  "$(test_usage_diagnostic_acceptance && echo pass || echo 'usage diagnostic fixtures must pass')"

# Run collection segment fixtures during ordinary validation as well.
test_usage_segment_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-collection-segment-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_segment_acceptance" \
  "$(test_usage_segment_acceptance && echo pass || echo 'usage segment fixtures must pass')"

# Run attribution fixtures during ordinary validation as well.
test_usage_attribution_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-attribution-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_attribution_acceptance" \
  "$(test_usage_attribution_acceptance && echo pass || echo 'usage attribution fixtures must pass')"

# Run independent inventory fixtures during ordinary validation as well.
test_usage_inventory_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-inventory-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_inventory_acceptance" \
  "$(test_usage_inventory_acceptance && echo pass || echo 'usage inventory fixtures must pass')"

# Run explicit source-selection fixtures during ordinary validation as well.
test_usage_selection_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-source-selection.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_selection_acceptance" \
  "$(test_usage_selection_acceptance && echo pass || echo 'usage selection fixtures must pass')"

# Run synthetic source-profile fixtures during ordinary validation as well.
test_usage_entity_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-entity-schemas.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_entity_acceptance" \
  "$(test_usage_entity_acceptance && echo pass || echo 'usage entity fixtures must pass')"

# Run sanitized envelope fixtures during ordinary validation as well.
test_usage_envelope_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-observation-bundle-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_envelope_acceptance" \
  "$(test_usage_envelope_acceptance && echo pass || echo 'usage envelope fixtures must pass')"

# Run typed usage schema fixtures during ordinary validation as well.
test_usage_schema_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-typed-schema.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_schema_acceptance" \
  "$(test_usage_schema_acceptance && echo pass || echo 'typed usage schema fixtures must pass')"

# Run the canonical encoding fixtures during ordinary validation as well.
test_usage_canonical_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/usage-canonical-encoding.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_usage_canonical_acceptance" \
  "$(test_usage_canonical_acceptance && echo pass || echo 'canonical usage encoding fixtures must pass')"

# Workflow entry points and bootstrap contracts are checked without model calls.
test_model_catalog_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/model-catalog.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_model_catalog_acceptance" \
  "$(test_model_catalog_acceptance && echo pass || echo 'offline local catalog schema, freshness and transactional refresh fixtures must pass')"

test_model_selection_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/model-selection.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_model_selection_acceptance" \
  "$(test_model_selection_acceptance && echo pass || echo 'conservative quality, eligibility and qualified economics fixtures must pass')"

test_model_plan_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/model-plan.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_model_plan_acceptance" \
  "$(test_model_plan_acceptance && echo pass || echo 'compatible plan columns, atomic updates and visible supported resolution fixtures must pass')"

check "test_workflow_instruction_contracts" \
  "$(python3 "$REPO_ROOT/tests/workflow-instructions.py" && echo pass || echo 'workflow entry points, bootstrap and mode contracts must be consistent')"

test_model_workflow_acceptance() {
  local output
  output="$(python3 "$REPO_ROOT/tests/model-workflow.py" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 60
    return 1
  }
}
check "test_model_workflow_acceptance" \
  "$(test_model_workflow_acceptance && echo pass || echo 'cached selector callers, guide examples and contract reachability fixtures must pass')"

# ── Native hook adapter acceptance ──────────────────────────────────
test_hook_shell_quality_acceptance() {
  local output
  output="$(bash "$REPO_ROOT/tests/hook-shell-quality.sh" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_hook_shell_quality_acceptance" \
  "$(test_hook_shell_quality_acceptance && echo pass || echo 'focused shell delivery functions must meet size and parameter limits')"

test_native_hook_adapter_acceptance() {
  local output
  output="$(bash "$REPO_ROOT/tests/log-step-hook.sh" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 20
    return 1
  }
}
check "test_native_hook_adapter_acceptance" \
  "$(test_native_hook_adapter_acceptance && echo pass || echo 'native hook dispatch, evidence and ownership fixtures must pass')"

# ── Workflow hook coverage acceptance ──────────────────────────────
test_workflow_hook_coverage_acceptance() {
  local output
  output="$(bash "$REPO_ROOT/tests/hook-workflow-contract.sh" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_workflow_hook_coverage_acceptance" \
  "$(test_workflow_hook_coverage_acceptance && echo pass || echo 'workflow correlation, route ownership and approximate prompt contracts must pass')"

# ── Exact retrospective timing acceptance ────────────────────────────
test_hook_timing_acceptance() {
  local output
  output="$(bash "$REPO_ROOT/tests/hook-timing.sh" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 35
    return 1
  }
}
check "test_hook_timing_acceptance" \
  "$(test_hook_timing_acceptance && echo pass || echo 'exact timing, lint coverage and isolated lifecycle fixtures must pass')"

# ── Tracked public hygiene ──────────────────────────────────────────
test_user_hook_installation_acceptance() {
  local output
  output="$(bash "$REPO_ROOT/tests/hook-install.sh" 2>&1)" || {
    printf '%s\n' "$output" | tail -n 20
    return 1
  }
}
check "test_user_hook_installation_acceptance" \
  "$(test_user_hook_installation_acceptance && echo pass || echo 'owned user hook lifecycle and isolated deployment fixtures must pass')"

hygiene_tracked_tree_result() {
  local pattern_file pattern_status=0
  pattern_file="$(hygiene_patterns_path)" || pattern_status=$?
  if [ "$pattern_status" -eq 2 ]; then
    echo 'skip: no local private hygiene pattern file is configured'
    return 0
  fi
  if [ "$pattern_status" -ne 0 ]; then
    echo 'tracked publication scope has an invalid private pattern configuration'
    return 0
  fi
  run_public_hygiene "$(pwd -P)" "$pattern_file" && echo pass || echo 'tracked publication scope requires redaction'
}
check "test_public_hygiene_tracked_tree_excludes_private_tokens" \
  "$(hygiene_tracked_tree_result)"

echo ""
echo "=== Contract Validation ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Skipped: $SKIP"
echo ""

if [ $FAIL -gt 0 ]; then
  echo "Fix failures before running scripts/sync.sh"
  exit 1
else
  echo "All required contracts valid."
  exit 0
fi
