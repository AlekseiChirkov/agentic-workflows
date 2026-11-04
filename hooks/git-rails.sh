#!/usr/bin/env bash
# Decide one Claude Code PreToolUse event for the Bash tool against the git safety rails.
# Contract: reads the hook event JSON from stdin, at most 1 MiB plus one byte, and writes
# no file. Without a project registry, or when the raw event holds no git or gh word, it
# exits 0 without starting Python and without output. Otherwise it needs python3 3.11 or
# newer and replaces itself with the isolated decision core (python3 -I git_rails.py),
# which answers in the harness protocol. A missing or older python3 denies with
# runtime-unavailable; the rule line and next step of that diagnostic are read from the
# core so that each is defined once, with a fixed wording when sed is missing. When head or
# tr is missing the prefilter is skipped and the core reads the unchanged stdin itself;
# a registry behind a directory that cannot be searched counts as present.
# Usage: bash hooks/git-rails.sh < event.json
# Exit codes: 0 = no objection (empty stdout) or ask (the ask JSON on stdout, the
#             diagnostic on stderr); 2 = deny (the diagnostic on stderr).
set -uo pipefail

GIT_RAILS_SOURCE="${BASH_SOURCE[0]}"
GIT_RAILS_DIRECTORY="${GIT_RAILS_SOURCE%/*}"
[ "$GIT_RAILS_DIRECTORY" != "$GIT_RAILS_SOURCE" ] || GIT_RAILS_DIRECTORY=.
GIT_RAILS_CORE="$(CDPATH='' cd -P -- "$GIT_RAILS_DIRECTORY" && pwd -P)/git_rails.py"
GIT_RAILS_INPUT_LIMIT=1048576
GIT_RAILS_EVENT=''

# Read the bounded event. NUL becomes \x01, which keeps the byte count and stays invalid
# JSON, because a shell variable cannot hold NUL.
read_event() {
  local LC_ALL=C
  GIT_RAILS_EVENT="$(head -c "$((GIT_RAILS_INPUT_LIMIT + 1))" | tr '\000' '\001'; printf x)"
  GIT_RAILS_EVENT="${GIT_RAILS_EVENT%x}"
}

# The registry exists, or a directory on its path cannot be searched, so only the core
# can tell; either way the core decides.
registry_exists() {
  local base="${XDG_CONFIG_HOME:-}" directory
  if [ -z "$base" ]; then
    [ -n "${HOME:-}" ] || return 1
    base="$HOME/.config"
  fi
  [ -e "$base/orchestrail/projects" ] && return 0
  for directory in "$base" "$base/orchestrail"; do
    if [ -e "$directory" ] && [ ! -x "$directory" ]; then
      return 0
    fi
  done
  return 1
}

read_tools_ready() {
  command -v head >/dev/null 2>&1 && command -v tr >/dev/null 2>&1
}

# A git or gh word in the raw JSON. A JSON escape such as \n or \u0009 before the word
# also counts as a boundary, so an escaped separator cannot hide an invocation.
relevant() {
  local LC_ALL=C
  local before='(^|[^A-Za-z0-9_.-]|\\[bfnrt]|\\u[0-9A-Fa-f]{4})'
  local after='([^A-Za-z0-9_.-]|$)'
  [[ $GIT_RAILS_EVENT =~ ${before}(git|gh)${after} ]]
}

python_ready() {
  command -v python3 >/dev/null 2>&1 || return 1
  [ "$(python3 -I -c 'import sys; print(int(sys.version_info >= (3, 11)))' 2>/dev/null </dev/null)" = 1 ]
}

core_line() {
  sed -n "$1" "$GIT_RAILS_CORE" 2>/dev/null
}

deny_runtime_unavailable() {
  local rule next
  rule="$(core_line "s/^RULE_PATH = '\\(.*\\)'\$/\\1/p")"
  next="$(core_line "s/^    'runtime-unavailable': '\\(.*\\)',\$/\\1/p")"
  [ -n "$rule" ] || rule='the safety rails of the git-flow rule (the core could not be read)'
  [ -n "$next" ] || next='make python3 3.11 or newer available to the hook, then retry'
  printf 'git-rails: deny runtime-unavailable (none)\nrule: %s\noperation: %s\nnext: %s\n' \
    "$rule" 'git-rails hook runtime (python3 3.11 or newer)' "$next" >&2
  exit 2
}

if ! read_tools_ready; then
  registry_exists || exit 0
  python_ready || deny_runtime_unavailable
  exec python3 -I "$GIT_RAILS_CORE"
fi
read_event
registry_exists || exit 0
relevant || exit 0
python_ready || deny_runtime_unavailable
exec python3 -I "$GIT_RAILS_CORE" < <(printf '%s' "$GIT_RAILS_EVENT")
