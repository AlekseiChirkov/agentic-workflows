#!/usr/bin/env bash
# log-step.sh — append-only run log for the pipeline workflows.
#
# The workflow system has no runtime, so an agent cannot measure a step's duration
# on its own. This helper stamps the time itself and derives every duration from
# its own previous write. Agents call it; they never hand-write a log line.
#
# Contract: rules/run-log.md
#
# Usage:
#   log-step.sh run-start --pipeline <name> [--project <path>] [--task <path>]
#                         [--spec <path>] [--flow quick|full] [--flags "<str>"]
#       → prints the run id on stdout, nothing else
#
#   log-step.sh step --run <id> --step <name> --outcome <ok|blocked|failed|skipped|deferred>
#                    [--stops N] [--escalations N] [--decisions N] [--questions N]
#                    [--gate <pass|fail|n-a|...>] [--tests <red|green|n-a|failed|not-run>]
#                    [--fix-tasks N] [--promoted <yes|no>] [--amendments N]
#                    [--files N] [--subtask <T-XX>] [--blocker "<text>"] [--note "<text>"]
#
#   log-step.sh run-end --run <id> --outcome <completed|stopped|failed|abandoned> [--note "<text>"]
#       → appends the closing line and writes the human-readable digest
#
#   log-step.sh path [--run <id>]     → print the log root, or one run's jsonl path
#   log-step.sh active                → list runs that have not been closed
#
# Never fails a pipeline: every error is a warning on stderr and exit 0.

set -uo pipefail

LOG_ROOT="${AGENTIC_LOG_ROOT:-$HOME/Documents/projects/alterra/agentic_workflows/logs}"
RUNS_DIR="$LOG_ROOT/runs"
ACTIVE_DIR="$LOG_ROOT/.active"

warn() { printf 'log-step: %s\n' "$*" >&2; }
die()  { warn "$*"; exit 0; }   # deliberate: logging never blocks the pipeline

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
now_epoch() { date -u +%s; }

ensure_store() {
  mkdir -p "$RUNS_DIR" "$ACTIVE_DIR" 2>/dev/null || return 1
  # The log store is local telemetry, never a committed artifact.
  [ -f "$LOG_ROOT/.gitignore" ] || printf '*\n' > "$LOG_ROOT/.gitignore" 2>/dev/null
  return 0
}

new_run_id() {
  if [ -r /dev/urandom ]; then
    od -An -N4 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n'
  else
    printf '%04x%04x' "$RANDOM" "$RANDOM"
  fi
}

# json_kv <key> <value> — emit a JSON member, escaping the value as a string.
# Numeric-looking values are emitted unquoted so the log stays arithmetically usable.
json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' \
    | awk 'BEGIN{ORS=""} {print sep $0; sep="\\n"}'
}

emit_json() {
  # Reads KEY=VALUE pairs on stdin (one per line, value may contain '='), emits one JSON object.
  if command -v jq >/dev/null 2>&1; then
    jq -Rn -c '
      [inputs
       | select(length > 0)
       | (index("=")) as $i
       | {key: .[0:$i], value: .[$i+1:]}]
      | from_entries
      | with_entries(
          if (.value | test("^-?[0-9]+$")) and (.key | IN("seq","duration_s","stops","escalations","decisions","questions","fix_tasks","amendments","files"))
          then .value |= tonumber else . end)
    '
  else
    local first=1 line key val
    printf '{'
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      key="${line%%=*}"; val="${line#*=}"
      [ $first -eq 1 ] || printf ','
      first=0
      case "$key" in
        seq|duration_s|stops|escalations|decisions|questions|fix_tasks|amendments|files)
          if printf '%s' "$val" | grep -qE '^-?[0-9]+$'; then
            printf '"%s":%s' "$key" "$val"; continue
          fi ;;
      esac
      printf '"%s":"%s"' "$key" "$(json_escape "$val")"
    done
    printf '}\n'
  fi
}

meta_get() { # meta_get <run_id> <key>
  local f="$ACTIVE_DIR/$1"
  [ -f "$f" ] || return 1
  sed -n "s/^$2=//p" "$f" | head -1
}

meta_set() { # meta_set <run_id> <key> <value>
  local f="$ACTIVE_DIR/$1"
  touch "$f" 2>/dev/null || return 1
  local tmp="$f.tmp.$$"
  grep -v "^$2=" "$f" 2>/dev/null > "$tmp"
  printf '%s=%s\n' "$2" "$3" >> "$tmp"
  mv "$tmp" "$f" 2>/dev/null
}

# ── run-start ─────────────────────────────────────────────────────────
cmd_run_start() {
  local pipeline="" project="" task="" spec="" flow="" flags=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --pipeline) pipeline="${2-}"; shift 2 ;;
      --project)  project="${2-}";  shift 2 ;;
      --task)     task="${2-}";     shift 2 ;;
      --spec)     spec="${2-}";     shift 2 ;;
      --flow)     flow="${2-}";     shift 2 ;;
      --flags)    flags="${2-}";    shift 2 ;;
      *) warn "unknown argument to run-start: $1"; shift ;;
    esac
  done
  [ -n "$pipeline" ] || die "run-start requires --pipeline"
  ensure_store || die "cannot create log store at $LOG_ROOT"

  [ -n "$project" ] || project="$(pwd)"
  local run_id ts file base
  run_id="$(new_run_id)"
  ts="$(now_iso)"
  base="$(printf '%s' "$ts" | tr ':' '-')-$pipeline-$run_id"
  file="$RUNS_DIR/$base.jsonl"

  meta_set "$run_id" file "$file"
  meta_set "$run_id" pipeline "$pipeline"
  meta_set "$run_id" project "$project"
  meta_set "$run_id" task "$task"
  meta_set "$run_id" spec "$spec"
  meta_set "$run_id" flow "$flow"
  meta_set "$run_id" flags "$flags"
  meta_set "$run_id" started_epoch "$(now_epoch)"
  meta_set "$run_id" last_epoch "$(now_epoch)"
  meta_set "$run_id" seq 0

  {
    printf 'ts=%s\n' "$ts"
    printf 'run_id=%s\n' "$run_id"
    printf 'event=run-start\n'
    printf 'seq=0\n'
    printf 'pipeline=%s\n' "$pipeline"
    printf 'project=%s\n' "$project"
    printf 'task=%s\n' "$task"
    printf 'spec=%s\n' "$spec"
    printf 'flow=%s\n' "$flow"
    printf 'flags=%s\n' "$flags"
    printf 'host=%s\n' "$(uname -n 2>/dev/null || echo unknown)"
  } | emit_json >> "$file" 2>/dev/null || warn "could not write to $file"

  printf '%s\n' "$run_id"
}

# ── step ──────────────────────────────────────────────────────────────
cmd_step() {
  local run="" step="" outcome="" stops="" esc="" dec="" q="" gate="" tests=""
  local fixt="" promoted="" amend="" files="" subtask="" blocker="" note=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --run)         run="${2-}";      shift 2 ;;
      --step)        step="${2-}";     shift 2 ;;
      --outcome)     outcome="${2-}";  shift 2 ;;
      --stops)       stops="${2-}";    shift 2 ;;
      --escalations) esc="${2-}";      shift 2 ;;
      --decisions)   dec="${2-}";      shift 2 ;;
      --questions)   q="${2-}";        shift 2 ;;
      --gate)        gate="${2-}";     shift 2 ;;
      --tests)       tests="${2-}";    shift 2 ;;
      --fix-tasks)   fixt="${2-}";     shift 2 ;;
      --promoted)    promoted="${2-}"; shift 2 ;;
      --amendments)  amend="${2-}";    shift 2 ;;
      --files)       files="${2-}";    shift 2 ;;
      --subtask)     subtask="${2-}";  shift 2 ;;
      --blocker)     blocker="${2-}";  shift 2 ;;
      --note)        note="${2-}";     shift 2 ;;
      *) warn "unknown argument to step: $1"; shift ;;
    esac
  done
  [ -n "$run" ]     || die "step requires --run"
  [ -n "$step" ]    || die "step requires --step"
  [ -n "$outcome" ] || die "step requires --outcome"

  local file; file="$(meta_get "$run" file)" || die "unknown run id: $run"
  [ -n "$file" ] || die "unknown run id: $run"

  local last seq dur
  last="$(meta_get "$run" last_epoch)"; : "${last:=$(now_epoch)}"
  seq="$(meta_get "$run" seq)";         : "${seq:=0}"
  seq=$((seq + 1))
  dur=$(( $(now_epoch) - last ))
  meta_set "$run" last_epoch "$(now_epoch)"
  meta_set "$run" seq "$seq"

  {
    printf 'ts=%s\n' "$(now_iso)"
    printf 'run_id=%s\n' "$run"
    printf 'event=step\n'
    printf 'seq=%s\n' "$seq"
    printf 'pipeline=%s\n' "$(meta_get "$run" pipeline)"
    printf 'step=%s\n' "$step"
    printf 'outcome=%s\n' "$outcome"
    printf 'duration_s=%s\n' "$dur"
    printf 'project=%s\n' "$(meta_get "$run" project)"
    printf 'task=%s\n' "$(meta_get "$run" task)"
    printf 'flow=%s\n' "$(meta_get "$run" flow)"
    [ -n "$subtask" ]  && printf 'subtask=%s\n' "$subtask"
    [ -n "$stops" ]    && printf 'stops=%s\n' "$stops"
    [ -n "$esc" ]      && printf 'escalations=%s\n' "$esc"
    [ -n "$dec" ]      && printf 'decisions=%s\n' "$dec"
    [ -n "$q" ]        && printf 'questions=%s\n' "$q"
    [ -n "$gate" ]     && printf 'gate=%s\n' "$gate"
    [ -n "$tests" ]    && printf 'tests=%s\n' "$tests"
    [ -n "$fixt" ]     && printf 'fix_tasks=%s\n' "$fixt"
    [ -n "$promoted" ] && printf 'promoted=%s\n' "$promoted"
    [ -n "$amend" ]    && printf 'amendments=%s\n' "$amend"
    [ -n "$files" ]    && printf 'files=%s\n' "$files"
    [ -n "$blocker" ]  && printf 'blocker=%s\n' "$blocker"
    [ -n "$note" ]     && printf 'note=%s\n' "$note"
    true
  } | emit_json >> "$file" 2>/dev/null || warn "could not append step to $file"
}

# ── run-end ───────────────────────────────────────────────────────────
cmd_run_end() {
  local run="" outcome="" note=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --run)     run="${2-}";     shift 2 ;;
      --outcome) outcome="${2-}"; shift 2 ;;
      --note)    note="${2-}";    shift 2 ;;
      *) warn "unknown argument to run-end: $1"; shift ;;
    esac
  done
  [ -n "$run" ]     || die "run-end requires --run"
  [ -n "$outcome" ] || die "run-end requires --outcome"

  local file; file="$(meta_get "$run" file)" || die "unknown run id: $run"
  [ -n "$file" ] || die "unknown run id: $run"

  local started total seq
  started="$(meta_get "$run" started_epoch)"; : "${started:=$(now_epoch)}"
  total=$(( $(now_epoch) - started ))
  seq="$(meta_get "$run" seq)"; : "${seq:=0}"
  seq=$((seq + 1))

  {
    printf 'ts=%s\n' "$(now_iso)"
    printf 'run_id=%s\n' "$run"
    printf 'event=run-end\n'
    printf 'seq=%s\n' "$seq"
    printf 'pipeline=%s\n' "$(meta_get "$run" pipeline)"
    printf 'outcome=%s\n' "$outcome"
    printf 'duration_s=%s\n' "$total"
    printf 'project=%s\n' "$(meta_get "$run" project)"
    printf 'task=%s\n' "$(meta_get "$run" task)"
    printf 'flow=%s\n' "$(meta_get "$run" flow)"
    [ -n "$note" ] && printf 'note=%s\n' "$note"
    true
  } | emit_json >> "$file" 2>/dev/null || warn "could not append run-end to $file"

  write_digest "$run" "$file"
  rm -f "$ACTIVE_DIR/$run" 2>/dev/null
}

write_digest() { # write_digest <run_id> <jsonl_path>
  local run="$1" file="$2" md="${2%.jsonl}.md"
  if ! command -v jq >/dev/null 2>&1; then
    { echo "# Run $run"; echo; echo "jq is not installed — no digest table."; \
      echo "Raw log: $file"; } > "$md" 2>/dev/null
    return 0
  fi
  {
    jq -r --arg run "$run" '
      select(.event == "run-start")
      | "# Run \($run) — \(.pipeline)",
        "",
        "| field | value |",
        "|---|---|",
        "| started | \(.ts) |",
        "| project | \(.project // "-") |",
        "| task | \(.task // "-") |",
        "| spec | \(.spec // "-") |",
        "| flow | \(.flow // "-") |",
        "| flags | \(if (.flags // "") == "" then "-" else .flags end) |",
        ""
    ' "$file"

    jq -r '
      select(.event == "run-end")
      | "**Outcome:** \(.outcome) — total \(.duration_s)s\(if (.note // "") != "" then " — \(.note)" else "" end)",
        ""
    ' "$file"

    echo "## Steps"
    echo
    echo "| # | step | outcome | dur s | stops | esc | dec | gate | tests | files | note |"
    echo "|---|---|---|---|---|---|---|---|---|---|---|"
    jq -r '
      select(.event == "step")
      | "| \(.seq) | \(.step)\(if (.subtask // "") != "" then " (\(.subtask))" else "" end) | \(.outcome) | \(.duration_s) | \(.stops // "-") | \(.escalations // "-") | \(.decisions // "-") | \(.gate // "-") | \(.tests // "-") | \(.files // "-") | \((.note // "-") | gsub("\\|"; "/")) |"
    ' "$file"
    echo

    echo "## Totals"
    echo
    jq -s -r '
      (map(select(.event == "step"))) as $s
      | "- steps: \($s | length)",
        "- human stops: \($s | map(.stops // 0) | add // 0)",
        "- escalations: \($s | map(.escalations // 0) | add // 0)",
        "- autonomous decisions: \($s | map(.decisions // 0) | add // 0)",
        "- fix-tasks created: \($s | map(.fix_tasks // 0) | add // 0)",
        "- description amendments: \($s | map(.amendments // 0) | add // 0)",
        "- steps not ok: \($s | map(select(.outcome != "ok")) | length)",
        "- slowest step: \(($s | max_by(.duration_s // 0) | "\(.step) (\(.duration_s)s)") // "-")"
    ' "$file"
  } > "$md" 2>/dev/null || warn "could not write digest $md"
}

# ── path / active ─────────────────────────────────────────────────────
cmd_path() {
  local run=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) run="${2-}"; shift 2 ;;
      *) shift ;;
    esac
  done
  if [ -n "$run" ]; then
    meta_get "$run" file || die "unknown run id: $run"
  else
    printf '%s\n' "$LOG_ROOT"
  fi
}

cmd_active() {
  [ -d "$ACTIVE_DIR" ] || { echo "no active runs"; return 0; }
  local any=0 f
  for f in "$ACTIVE_DIR"/*; do
    [ -f "$f" ] || continue
    any=1
    printf '%s  %s  %s\n' "$(basename "$f")" "$(sed -n 's/^pipeline=//p' "$f" | head -1)" \
                          "$(sed -n 's/^task=//p' "$f" | head -1)"
  done
  [ $any -eq 1 ] || echo "no active runs"
}

# ── dispatch ──────────────────────────────────────────────────────────
case "${1-}" in
  run-start) shift; cmd_run_start "$@" ;;
  step)      shift; cmd_step "$@" ;;
  run-end)   shift; cmd_run_end "$@" ;;
  path)      shift; cmd_path "$@" ;;
  active)    shift; cmd_active "$@" ;;
  ""|-h|--help|help)
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command: ${1-}" ;;
esac
