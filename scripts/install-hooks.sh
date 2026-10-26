#!/usr/bin/env bash
# Merge or remove owned user hooks without replacing unrelated settings.
# Usage: bash scripts/install-hooks.sh install [--from <source-tree>] | uninstall
# Recoverable failures emit one unavailable JSON result and exit zero; CLI errors fail.
set -uo pipefail

usage() {
  printf '%s\n' 'Usage: scripts/install-hooks.sh install [--from <source-tree>] | uninstall' \
    '  --from <dir>, --from=<dir>  select the source checkout for installation' \
    '  -h, --help                 show this help'
}

case "${1:-}" in
  -h|--help) [ "$#" -eq 1 ] || { usage >&2; exit 1; }; usage; exit 0 ;;
  install|uninstall) operation="$1"; shift ;;
  *) usage >&2; exit 1 ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source_tree="${ORCHESTRAIL_HOME:-$script_dir/..}"
while [ "$#" -gt 0 ]; do
  [ "$operation" = install ] || { usage >&2; exit 1; }
  case "$1" in
    --from)
      [ "$#" -ge 2 ] && [ -n "$2" ] || { usage >&2; exit 1; }
      source_tree="$2"; shift 2 ;;
    --from=*)
      source_tree="${1#--from=}"
      [ -n "$source_tree" ] || { usage >&2; exit 1; }
      shift ;;
    *) usage >&2; exit 1 ;;
  esac
done

dependencies=(python3)
if [ "$operation" = install ]; then dependencies+=(jq flock); fi
for dependency in "${dependencies[@]}"; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    printf '%s\n' 'orchestrail hooks unavailable: missing-dependency' >&2
    printf '%s\n' '{"reason":"missing-dependency","status":"unavailable"}'
    exit 0
  fi
done

python3 "$script_dir/install-hooks.py" "$operation" "$source_tree"
result=$?
if [ "$result" -ne 0 ]; then
  printf '%s\n' 'orchestrail hooks unavailable: installer-interrupted' >&2
  printf '%s\n' '{"reason":"installer-interrupted","status":"unavailable"}'
fi
exit 0
