#!/usr/bin/env bash
# Execute the run-log acceptance checks in a disposable checkout and log store.
# Usage: bash tests/log-step.sh. Exit 0 means every check passed; failures exit 1.
# The focused checks come from the contract validator; never run its full suite here.
set -euo pipefail

source_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
acceptance_scratch="$(mktemp -d "${TMPDIR:-/tmp}/run log acceptance.XXXXXX")"
trap 'rm -rf -- "$acceptance_scratch"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Override inherited helper/store choices before any helper can be invoked.
export ORCHESTRAIL_HOME="$acceptance_scratch/checkout"
export ORCHESTRAIL_LOG_ROOT="$acceptance_scratch/isolated store"
export TMPDIR="$acceptance_scratch/temporary fixtures"
mkdir -p "$ORCHESTRAIL_HOME" "$TMPDIR"
python3 - "$source_root" "$ORCHESTRAIL_HOME" <<'PY'
from pathlib import Path
import re
import shutil
import sys

source, checkout = map(Path, sys.argv[1:])
for directory in ('scripts', 'rules', 'workflows'):
    (checkout / directory).mkdir()
for name in ('scripts/log-step.sh', 'scripts/validate-contracts.sh', 'rules/run-log.md'):
    shutil.copy2(source / name, checkout / name)
for workflow in (source / 'workflows').glob('*.md'):
    shutil.copy2(workflow, checkout / 'workflows' / workflow.name)
text = (checkout / 'scripts/validate-contracts.sh').read_text()
groups = (
    ('Run-log contract smoke checks', 'End run-log contract smoke checks'),
    ('Run-log producer smoke checks', 'End run-log producer smoke checks'),
    ('Retrospective executable corpus contract', 'End retrospective executable corpus contract'),
)
definitions = []
for opening, closing in groups:
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith('# ── ' + opening))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith('# ── ' + closing))
    block = ''.join(lines[start + 1:end])
    # Remove only top-level check calls. Run each function directly in a fresh
    # shell so a caller's conditional cannot disable errexit inside assertions.
    block, removed = re.subn(r'^check [^\n]*\\\n[^\n]*\n', '', block, flags=re.M)
    assert removed > 0 and not re.search(r'^check ', block, re.M), opening
    definitions.append(block)
body = '\n'.join(definitions)
names = re.findall(r'^(test_(?:run_log|retro)_[a-z_]+)\(\)', body, re.M)
assert len(names) >= 20 and len(names) == len(set(names)), names
(checkout / 'focused-checks.sh').write_text(body)
(checkout / 'focused-names').write_text('\n'.join(names) + '\n')
PY

cd "$ORCHESTRAIL_HOME"
export REPO_ROOT="$ORCHESTRAIL_HOME"
while IFS= read -r acceptance_check; do
  if bash -euo pipefail -c 'source "$1"; "$2"' acceptance \
      "$ORCHESTRAIL_HOME/focused-checks.sh" "$acceptance_check"; then
    printf '[PASS] %s\n' "$acceptance_check"
  else
    printf '[FAIL] %s\n' "$acceptance_check" >&2
    exit 1
  fi
done < "$ORCHESTRAIL_HOME/focused-names"
