#!/usr/bin/env bash
# Analyze explicitly selected run files through the source-only Python engine.
# Usage: bash scripts/run-log-timing.sh [--] FILE...; -h/--help shows usage.
# Dependency or analysis failures emit unavailable JSON and exit zero.
set -uo pipefail

unavailable() {
  printf '{"schema_version":1,"status":"unavailable","coverage":{"lint_status":"unavailable","selected_files":null,"examined_lines":null,"invalid_lines":0,"violations":0,"invalid_lines_exact":false},"runs":null,"diagnostics":[{"code":"%s"}]}\n' "$1"
}

for dependency in python3 jq; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    unavailable missing-dependency
    exit 0
  fi
done
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
  unavailable unsupported-python
  exit 0
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
python3 "$script_dir/run-log-timing.py" "$@"
result=$?
if [ "$result" -ne 0 ]; then unavailable engine-unavailable; fi
exit 0
