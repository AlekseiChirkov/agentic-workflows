#!/usr/bin/env bash
# Run the acceptance suite of scripts/audit-instructions.py against each git release
# whose behaviour its module docstring names, one container per release.
#
# Contract: for each version, build the image of Dockerfile (git from its source tarball,
# which needs network access) unless it is cached, then run
# `python3 -I scripts/check-audit-instructions.py` in a container without network, with
# this repository mounted read-only and bytecode writing disabled. Cases that need a newer
# git skip themselves; cases that confirm a residual run only below their boundary.
# Containers are removed after each run; images stay cached. One summary line per
# version: `<version> pass|fail|build-failed <log file>`.
#
# Usage: bash scripts/audit-git-matrix/run.sh [--logs DIR] [VERSION...]
#   Without versions, every release of DEFAULT_VERSIONS is run. Logs go to DIR (default:
#   a new temporary directory, printed first).
# Exit codes: 0 every version passed; 1 a version failed or could not be built;
#   2 usage error or docker unavailable.
set -uo pipefail

DEFAULT_VERSIONS=(2.30.6 2.30.7 2.31.0 2.31.8 2.40.1 2.41.0 2.44.2 2.45.0 2.53.0)

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
logs=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --logs)
      [ "$#" -ge 2 ] || { echo "ERROR: --logs needs a directory" >&2; exit 2; }
      logs="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --) shift; break ;;
    -*) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    *) break ;;
  esac
done

versions=("$@")
[ "${#versions[@]}" -gt 0 ] || versions=("${DEFAULT_VERSIONS[@]}")
for version in "${versions[@]}"; do
  [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
    echo "ERROR: not a git release number: $version" >&2; exit 2; }
done

command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 || {
  echo "ERROR: docker is not available" >&2; exit 2; }

if [ -z "$logs" ]; then
  logs="$(mktemp -d "${TMPDIR:-/tmp}/audit-git-matrix.XXXXXX")" || exit 2
fi
mkdir -p "$logs" || { echo "ERROR: cannot create $logs" >&2; exit 2; }
echo "logs: $logs"

status=0
for version in "${versions[@]}"; do
  image="audit-git-matrix:$version"
  log="$logs/$version.log"
  if ! docker build -q --build-arg "GIT_VERSION=$version" -t "$image" "$here" \
      > "$logs/$version.build.log" 2>&1; then
    echo "$version build-failed $logs/$version.build.log"
    status=1
    continue
  fi
  if docker run --rm --network none -v "$repo:/src:ro" "$image" \
      sh -c 'git --version && python3 --version && python3 -I /src/scripts/check-audit-instructions.py' \
      > "$log" 2>&1; then
    echo "$version pass $log"
  else
    echo "$version fail $log"
    status=1
  fi
done
exit "$status"
