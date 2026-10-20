#!/usr/bin/env bash
# scripts/log-step.sh — append-only run log for the pipeline workflows.
#
# The workflow system has no runtime, so an agent cannot measure a step's duration
# on its own. This helper stamps the time itself and derives every duration from
# its own previous write. Agents call it; they never hand-write a log line.
#
# Contract: rules/run-log.md
#
# Usage:
#   scripts/log-step.sh run-start --pipeline <name> [--project <path>] [--task <path>]
#                         [--spec <path>] [--flow <label>] [--flags "<str>"]
#       → prints the run id on stdout, nothing else
#
#   scripts/log-step.sh step --run <id> --step <name> --outcome <ok|blocked|failed|skipped|deferred>
#                    [--stops N] [--escalations N] [--decisions N] [--questions N]
#                    [--gate <pass|fail|n-a|needs-work|ready>] [--tests <red|green|n-a|failed|not-run|pinned>]
#                    [--fix-tasks N] [--promoted <yes|no>] [--amendments N]
#                    [--files N] [--subtask <T-XX>] [--blocker "<text>"] [--note "<text>"]
#
#   scripts/log-step.sh run-end --run <id> --outcome <completed|stopped|failed|abandoned> [--note "<text>"]
#       → appends the closing line and writes the human-readable digest
#
#   scripts/log-step.sh path [--run <id>]     → print the log root, or one run's jsonl path
#   scripts/log-step.sh active                → list runs that have not been closed
#   scripts/log-step.sh contract              → print the runtime vocabulary as key=value lines
#
# Never fails a pipeline: every error is a warning on stderr and exit 0.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
LOG_ROOT="${ORCHESTRAIL_LOG_ROOT:-$REPO_ROOT/logs}"
RUNS_DIR="$LOG_ROOT/runs"
ACTIVE_DIR="$LOG_ROOT/.active"

# Canonical producer vocabulary. Values are pipe-delimited enums, a space-delimited
# count field list, or exact alias mappings; consumers can inspect this structure
# through the contract command without maintaining a second vocabulary.
declare -Ar RUN_LOG_CONTRACT=(
  [step.outcome]='ok|blocked|failed|skipped|deferred'
  [step.gate]='pass|fail|n-a|needs-work|ready'
  [step.tests]='red|green|n-a|failed|not-run|pinned'
  [step.promoted]='yes|no'
  [run-end.outcome]='completed|stopped|failed|abandoned'
  [count.fields]='stops escalations decisions questions fix_tasks amendments files'
  [count.maximum]='9007199254740991'
  [alias.outcome.completed]='ok'
  [alias.outcome.implemented]='ok'
  [alias.outcome.restarted]='failed'
  [alias.outcome.needs-work]='failed'
  [alias.gate.PASS]='pass'
  [alias.gate.NEEDS_WORK_EXACT]='needs-work'
  [alias.gate.NEEDS_WORK_PREFIX]='^NEEDS WORK([[:space:]:-].*)$'
  [alias.gate.escalated]='fail'
  [step.synthetic]='batch-gate|subtask|dry-run'
)

warn() { printf 'log-step: %s\n' "$*" >&2; }
die()  { warn "$*"; exit 0; }   # deliberate: logging never blocks the pipeline

contract_enum_has() { # contract_enum_has <enum-key> <value>
  local key="$1" candidate value="$2"
  local -a allowed=()
  key="${RUN_LOG_CONTRACT[$key]-}"
  [ -n "$key" ] || return 1
  IFS='|' read -r -a allowed <<< "$key"
  for candidate in "${allowed[@]}"; do
    [ "$candidate" = "$value" ] && return 0
  done
  return 1
}

valid_run_id() { [[ "${1-}" =~ ^[0-9a-f]{8}$ ]]; }

reject_invocation() { # reject_invocation <event> <field> <reason-code>
  warn "$1 $2 $3"
}

declare -A PARSED_ARGS=()
PARSE_ERROR_FIELD=''
PARSE_ERROR_CODE=''

parse_arguments() { # parse_arguments <event> <option> <value> ...
  local event="$1" option key
  shift
  PARSED_ARGS=()
  PARSE_ERROR_FIELD='argument'
  PARSE_ERROR_CODE='invalid-option'
  while [ "$#" -gt 0 ]; do
    option="$1"
    case "$event:$option" in
      run-start:--pipeline|run-start:--project|run-start:--task|run-start:--spec|run-start:--flow|run-start:--flags|\
      step:--run|step:--step|step:--outcome|step:--stops|step:--escalations|step:--decisions|step:--questions|step:--gate|step:--tests|step:--fix-tasks|step:--promoted|step:--amendments|step:--files|step:--subtask|step:--blocker|step:--note|\
      run-end:--run|run-end:--outcome|run-end:--note) ;;
      *) PARSE_ERROR_FIELD='argument'; PARSE_ERROR_CODE='invalid-option'; return 1 ;;
    esac
    key="${option#--}"
    key="${key//-/_}"
    PARSE_ERROR_FIELD="$key"
    PARSE_ERROR_CODE='duplicate-option'
    [[ ${PARSED_ARGS[$key]+present} ]] && return 1
    if [ "$#" -lt 2 ] || [[ "$2" == --* ]]; then
      PARSE_ERROR_CODE='missing-operand'
      return 1
    fi
    PARSED_ARGS[$key]="$2"
    shift 2
  done
  PARSE_ERROR_FIELD=''
  PARSE_ERROR_CODE=''
  return 0
}

valid_count() { # valid_count <decimal-value>
  local value="$1" maximum="${RUN_LOG_CONTRACT[count.maximum]}"
  [[ "$value" =~ ^(0|[1-9][0-9]*)$ ]] || return 1
  [ "${#value}" -lt "${#maximum}" ] && return 0
  [ "${#value}" -eq "${#maximum}" ] && [[ ! "$value" > "$maximum" ]]
}

has_parsed_arg() { [[ ${PARSED_ARGS[$1]+present} ]]; }

validate_enum_arg() { # validate_enum_arg <event> <field> <contract-key> <required>
  local event="$1" field="$2" enum_key="$3" required="$4" value="${PARSED_ARGS[$2]-}"
  if ! has_parsed_arg "$field"; then
    if [ "$required" = yes ]; then
      reject_invocation "$event" "$field" missing-required
      return 1
    fi
    return 0
  fi
  if [ -z "$value" ]; then
    reject_invocation "$event" "$field" empty-value
    return 1
  fi
  if ! contract_enum_has "$enum_key" "$value"; then
    reject_invocation "$event" "$field" invalid-enum
    return 1
  fi
  return 0
}

validate_start_args() {
  if ! has_parsed_arg pipeline; then
    reject_invocation run-start pipeline missing-required
    return 1
  fi
  if [ -z "${PARSED_ARGS[pipeline]}" ]; then
    reject_invocation run-start pipeline empty-value
    return 1
  fi
  return 0
}

validate_step_args() {
  if ! has_parsed_arg run; then
    reject_invocation step run missing-required
    return 1
  fi
  if ! valid_run_id "${PARSED_ARGS[run]}"; then
    reject_invocation step run invalid-id
    return 1
  fi
  if ! has_parsed_arg step; then
    reject_invocation step step missing-required
    return 1
  fi
  if [ -z "${PARSED_ARGS[step]}" ]; then
    reject_invocation step step empty-value
    return 1
  fi
  validate_enum_arg step outcome step.outcome yes || return 1
  validate_enum_arg step gate step.gate no || return 1
  validate_enum_arg step tests step.tests no || return 1
  validate_enum_arg step promoted step.promoted no || return 1
  local field
  for field in ${RUN_LOG_CONTRACT[count.fields]}; do
    if has_parsed_arg "$field" && ! valid_count "${PARSED_ARGS[$field]}"; then
      reject_invocation step "$field" invalid-integer
      return 1
    fi
  done
  return 0
}

validate_end_args() {
  if ! has_parsed_arg run; then
    reject_invocation run-end run missing-required
    return 1
  fi
  if ! valid_run_id "${PARSED_ARGS[run]}"; then
    reject_invocation run-end run invalid-id
    return 1
  fi
  validate_enum_arg run-end outcome run-end.outcome yes
}

append_raw_note() { # append_raw_note <current-note> <raw-value>
  if [ -n "$1" ]; then
    APPENDED_NOTE="$1; raw:$2"
  else
    APPENDED_NOTE="raw:$2"
  fi
}

normalize_step_aliases() { # normalize_step_aliases <outcome> <gate> <note>
  local outcome="$1" gate="$2" note="$3" raw alias_key prefix_pattern mapped
  raw="$outcome"
  alias_key="alias.outcome.$raw"
  mapped="${RUN_LOG_CONTRACT[$alias_key]-}"
  if [ -n "$mapped" ]; then
    outcome="$mapped"
    append_raw_note "$note" "$raw"
    note="$APPENDED_NOTE"
  fi

  raw="$gate"
  if [ "$raw" = 'NEEDS WORK' ]; then
    mapped="${RUN_LOG_CONTRACT[alias.gate.NEEDS_WORK_EXACT]}"
  elif [ "$raw" = PASS ] || [ "$raw" = escalated ]; then
    alias_key="alias.gate.$raw"
    mapped="${RUN_LOG_CONTRACT[$alias_key]-}"
  else
    mapped=''
  fi
  if [ -n "$mapped" ]; then
    gate="$mapped"
    append_raw_note "$note" "$raw"
    note="$APPENDED_NOTE"
  else
    prefix_pattern="${RUN_LOG_CONTRACT[alias.gate.NEEDS_WORK_PREFIX]}"
    if [[ "$raw" =~ $prefix_pattern ]]; then
      gate="${RUN_LOG_CONTRACT[alias.gate.NEEDS_WORK_EXACT]}"
      append_raw_note "$note" "$raw"
      note="$APPENDED_NOTE"
    fi
  fi

  NORMALIZED_OUTCOME="$outcome"
  NORMALIZED_GATE="$gate"
  NORMALIZED_NOTE="$note"
}

check_step_name() { # check_step_name <step-name>
  local name="$1" source_root="${ORCHESTRAIL_HOME:-$REPO_ROOT}" workflows_dir file base
  workflows_dir="$source_root/workflows"
  if [ ! -d "$workflows_dir" ] || [ ! -r "$workflows_dir" ]; then
    warn 'step-name verification unavailable'
    return 0
  fi
  if contract_enum_has step.synthetic "$name"; then return 0; fi
  for file in "$workflows_dir"/*.md; do
    [ -f "$file" ] || continue
    base="${file##*/}"
    base="${base%.md}"
    [ "$base" = "$name" ] && return 0
  done
  warn 'step name is not in the current workflow list'
}

NORMALIZED_OUTCOME=''
NORMALIZED_GATE=''
NORMALIZED_NOTE=''

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
now_epoch() { date -u +%s; }

ensure_store() {
  mkdir -p "$RUNS_DIR" "$ACTIVE_DIR" 2>/dev/null || return 1
  # The log store is local telemetry, never a committed artifact.
  [ -f "$LOG_ROOT/.gitignore" ] || (printf '*\n' > "$LOG_ROOT/.gitignore") 2>/dev/null
  return 0
}

new_run_id() {
  if [ -r /dev/urandom ]; then
    od -An -N4 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n'
  else
    printf '%04x%04x' "$RANDOM" "$RANDOM"
  fi
}

# json_escape <value> — emit the JSON string contents without surrounding quotes.
json_escape() {
  local value="$1" output='' char code escaped index
  local LC_ALL=C
  for ((index = 0; index < ${#value}; index++)); do
    char="${value:index:1}"
    case "$char" in
      '"') output+='\"' ;;
      \\) output+='\\' ;;
      $'\b') output+='\b' ;;
      $'\f') output+='\f' ;;
      $'\n') output+='\n' ;;
      $'\r') output+='\r' ;;
      $'\t') output+='\t' ;;
      *)
        printf -v code '%d' "'$char"
        if [ "$code" -lt 32 ]; then
          printf -v escaped '\\u%04x' "$code"
          output+="$escaped"
        else
          output+="$char"
        fi
        ;;
    esac
  done
  printf '%s' "$output"
}

json_kv() { # json_kv <key> <value>
  local escaped
  escaped="$(json_escape "$2")"
  printf '%s=%s\n' "$1" "$escaped"
}

emit_json() {
  # Reads KEY=JSON-ESCAPED-VALUE pairs on stdin and emits one JSON object.
  if command -v jq >/dev/null 2>&1; then
    jq -Rn -c '
      [inputs
       | select(length > 0)
       | (index("=")) as $i
       | {key: .[0:$i], value: (("\"" + .[$i+1:] + "\"") | fromjson)}]
      | from_entries
      | with_entries(
          if (.key | IN("seq","duration_s","stops","escalations","decisions","questions","fix_tasks","amendments","files"))
             and (.value | type == "string" and test("^(0|[1-9][0-9]*)$"))
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
          if [[ "$val" =~ ^(0|[1-9][0-9]*)$ ]]; then
            printf '"%s":%s' "$key" "$val"; continue
          fi ;;
      esac
      printf '"%s":"%s"' "$key" "$val"
    done
    printf '}\n'
  fi
}

meta_get() { # meta_get <run_id> <key>
  valid_run_id "$1" || return 1
  local f="$ACTIVE_DIR/$1"
  [ -f "$f" ] || return 1
  sed -n "s/^$2=//p" "$f" | head -1
}

meta_set() { # meta_set <run_id> <key> <value>
  valid_run_id "$1" || return 1
  local f="$ACTIVE_DIR/$1"
  touch "$f" 2>/dev/null || return 1
  local tmp="$f.tmp.$$" grep_status
  grep -v "^$2=" "$f" 2>/dev/null > "$tmp"
  grep_status=$?
  if [ "$grep_status" -gt 1 ]; then rm -f "$tmp" 2>/dev/null; return 1; fi
  if ! ( printf '%s=%s\n' "$2" "$3" >> "$tmp" ) 2>/dev/null; then
    rm -f "$tmp" 2>/dev/null
    return 1
  fi
  if ! mv "$tmp" "$f" 2>/dev/null; then rm -f "$tmp" 2>/dev/null; return 1; fi
}

# ── run-start ─────────────────────────────────────────────────────────
cmd_run_start() {
  local pipeline="" project="" task="" spec="" flow="" flags=""
  if ! parse_arguments run-start "$@"; then
    reject_invocation run-start "$PARSE_ERROR_FIELD" "$PARSE_ERROR_CODE"
    return 0
  fi
  pipeline="${PARSED_ARGS[pipeline]-}"
  project="${PARSED_ARGS[project]-}"
  task="${PARSED_ARGS[task]-}"
  spec="${PARSED_ARGS[spec]-}"
  flow="${PARSED_ARGS[flow]-}"
  flags="${PARSED_ARGS[flags]-}"
  if ! validate_start_args; then return 0; fi
  [ -n "$flow" ] || flow='unknown'
  ensure_store || { warn 'run-start storage unavailable'; return 0; }

  [ -n "$project" ] || project="$(pwd)"
  local run_id ts file base file_pipeline contract_version="" start_epoch active recorded_file recorded_seq recorded_flow
  # The version belongs to this helper's checkout, independently of the caller.
  if [ -r "$REPO_ROOT/VERSION" ]; then
    contract_version="$(cat "$REPO_ROOT/VERSION" 2>/dev/null)" || contract_version=""
    [[ "$contract_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || contract_version=""
  fi
  run_id="$(new_run_id)"
  if ! valid_run_id "$run_id"; then
    warn 'run-start could not allocate a run identifier'
    return 0
  fi
  ts="$(now_iso)"
  file_pipeline="${pipeline//[^A-Za-z0-9._-]/_}"
  base="$(printf '%s' "$ts" | tr ':' '-')-$file_pipeline-$run_id"
  file="$RUNS_DIR/$base.jsonl"
  start_epoch="$(now_epoch)"
  active="$ACTIVE_DIR/$run_id"
  if [ -e "$active" ] || [ -e "$file" ]; then
    warn 'run-start identifier collision'
    return 0
  fi

  if ! meta_set "$run_id" file "$file" ||
     ! meta_set "$run_id" pipeline "$pipeline" ||
     ! meta_set "$run_id" project "$project" ||
     ! meta_set "$run_id" task "$task" ||
     ! meta_set "$run_id" spec "$spec" ||
     ! meta_set "$run_id" flow "$flow" ||
     ! meta_set "$run_id" flags "$flags" ||
     ! meta_set "$run_id" started_epoch "$start_epoch" ||
     ! meta_set "$run_id" last_epoch "$start_epoch" ||
     ! meta_set "$run_id" seq 0; then
    rm -f "$active" 2>/dev/null
    warn 'run-start metadata persistence failed'
    return 0
  fi
  recorded_file="$(meta_get "$run_id" file 2>/dev/null)"
  recorded_seq="$(meta_get "$run_id" seq 2>/dev/null)"
  recorded_flow="$(meta_get "$run_id" flow 2>/dev/null)"
  if [ ! -f "$active" ] || [ "$recorded_file" != "$file" ] ||
     [ "$recorded_seq" != 0 ] || [ "$recorded_flow" != "$flow" ]; then
    rm -f "$active" 2>/dev/null
    warn 'run-start metadata is unusable'
    return 0
  fi

  if ! (
    {
      json_kv ts "$ts"
      json_kv run_id "$run_id"
      json_kv event run-start
      [ -z "$contract_version" ] || json_kv contract_version "$contract_version"
      json_kv seq 0
      json_kv pipeline "$pipeline"
      json_kv project "$project"
      [ -z "$task" ] || json_kv task "$task"
      [ -z "$spec" ] || json_kv spec "$spec"
      json_kv flow "$flow"
      [ -z "$flags" ] || json_kv flags "$flags"
      json_kv host "$(uname -n 2>/dev/null || echo unknown)"
    } | emit_json >> "$file"
  ) 2>/dev/null; then
    rm -f "$active" "$file" 2>/dev/null
    warn 'run-start event persistence failed'
    return 0
  fi
  if [ ! -s "$file" ]; then
    rm -f "$active" "$file" 2>/dev/null
    warn 'run-start event persistence failed'
    return 0
  fi

  printf '%s\n' "$run_id"
}

# ── step ──────────────────────────────────────────────────────────────
cmd_step() {
  local run="" step="" outcome="" stops="" esc="" dec="" q="" gate="" tests=""
  local fixt="" promoted="" amend="" files="" subtask="" blocker="" note=""
  if ! parse_arguments step "$@"; then
    reject_invocation step "$PARSE_ERROR_FIELD" "$PARSE_ERROR_CODE"
    return 0
  fi
  normalize_step_aliases "${PARSED_ARGS[outcome]-}" "${PARSED_ARGS[gate]-}" "${PARSED_ARGS[note]-}"
  if has_parsed_arg outcome; then PARSED_ARGS[outcome]="$NORMALIZED_OUTCOME"; fi
  if has_parsed_arg gate; then PARSED_ARGS[gate]="$NORMALIZED_GATE"; fi
  if has_parsed_arg note || [ -n "$NORMALIZED_NOTE" ]; then PARSED_ARGS[note]="$NORMALIZED_NOTE"; fi
  run="${PARSED_ARGS[run]-}"
  step="${PARSED_ARGS[step]-}"
  outcome="${PARSED_ARGS[outcome]-}"
  stops="${PARSED_ARGS[stops]-}"
  esc="${PARSED_ARGS[escalations]-}"
  dec="${PARSED_ARGS[decisions]-}"
  q="${PARSED_ARGS[questions]-}"
  gate="${PARSED_ARGS[gate]-}"
  tests="${PARSED_ARGS[tests]-}"
  fixt="${PARSED_ARGS[fix_tasks]-}"
  promoted="${PARSED_ARGS[promoted]-}"
  amend="${PARSED_ARGS[amendments]-}"
  files="${PARSED_ARGS[files]-}"
  subtask="${PARSED_ARGS[subtask]-}"
  blocker="${PARSED_ARGS[blocker]-}"
  note="${PARSED_ARGS[note]-}"
  if ! validate_step_args; then return 0; fi
  check_step_name "$step"

  local file last seq dur event_epoch ts pipeline project task flow before_size after_size
  file="$(meta_get "$run" file)" || { reject_invocation step run not-found; return 0; }
  [ -n "$file" ] && [ -f "$file" ] || { reject_invocation step run not-found; return 0; }
  before_size="$( (wc -c < "$file") 2>/dev/null)" || { warn 'step event storage unavailable'; return 0; }
  last="$(meta_get "$run" last_epoch)"
  seq="$(meta_get "$run" seq)"
  valid_count "$last" || last="$(now_epoch)"
  valid_count "$seq" || seq=0
  seq=$((seq + 1))
  event_epoch="$(now_epoch)"
  dur=$((event_epoch - last))
  [ "$dur" -ge 0 ] || dur=0
  ts="$(now_iso)"
  pipeline="$(meta_get "$run" pipeline)"
  project="$(meta_get "$run" project)"
  task="$(meta_get "$run" task)"
  flow="$(meta_get "$run" flow)"
  [ -n "$flow" ] || flow='unknown'

  if ! (
    {
      json_kv ts "$ts"
      json_kv run_id "$run"
      json_kv event step
      json_kv seq "$seq"
      json_kv pipeline "$pipeline"
      json_kv step "$step"
      json_kv outcome "$outcome"
      json_kv duration_s "$dur"
      json_kv project "$project"
      [ -z "$task" ] || json_kv task "$task"
      json_kv flow "$flow"
      [ -z "$subtask" ] || json_kv subtask "$subtask"
      [ -z "$stops" ] || json_kv stops "$stops"
      [ -z "$esc" ] || json_kv escalations "$esc"
      [ -z "$dec" ] || json_kv decisions "$dec"
      [ -z "$q" ] || json_kv questions "$q"
      [ -z "$gate" ] || json_kv gate "$gate"
      [ -z "$tests" ] || json_kv tests "$tests"
      [ -z "$fixt" ] || json_kv fix_tasks "$fixt"
      [ -z "$promoted" ] || json_kv promoted "$promoted"
      [ -z "$amend" ] || json_kv amendments "$amend"
      [ -z "$files" ] || json_kv files "$files"
      [ -z "$blocker" ] || json_kv blocker "$blocker"
      [ -z "$note" ] || json_kv note "$note"
      true
    } | emit_json >> "$file"
  ) 2>/dev/null; then
    warn 'step event persistence failed'
    return 0
  fi
  after_size="$( (wc -c < "$file") 2>/dev/null)" || { warn 'step event persistence failed'; return 0; }
  if [ "$after_size" -le "$before_size" ]; then
    warn 'step event persistence failed'
    return 0
  fi
  if ! meta_set "$run" last_epoch "$event_epoch" ||
     ! meta_set "$run" seq "$seq" ||
     ! meta_set "$run" flow "$flow"; then
    warn 'step metadata persistence failed'
    return 0
  fi
}

# ── run-end ───────────────────────────────────────────────────────────
cmd_run_end() {
  local run="" outcome="" note=""
  if ! parse_arguments run-end "$@"; then
    reject_invocation run-end "$PARSE_ERROR_FIELD" "$PARSE_ERROR_CODE"
    return 0
  fi
  run="${PARSED_ARGS[run]-}"
  outcome="${PARSED_ARGS[outcome]-}"
  note="${PARSED_ARGS[note]-}"
  if ! validate_end_args; then return 0; fi

  local file; file="$(meta_get "$run" file)" || {
    reject_invocation run-end run not-found
    return 0
  }
  [ -n "$file" ] || { reject_invocation run-end run not-found; return 0; }

  local started total seq pipeline project task flow before_size after_size
  started="$(meta_get "$run" started_epoch)"
  valid_count "$started" || started="$(now_epoch)"
  seq="$(meta_get "$run" seq)"
  valid_count "$seq" || seq=0
  seq=$((seq + 1))
  total=$(( $(now_epoch) - started ))
  [ "$total" -ge 0 ] || total=0
  pipeline="$(meta_get "$run" pipeline)"
  project="$(meta_get "$run" project)"
  task="$(meta_get "$run" task)"
  flow="$(meta_get "$run" flow)"
  [ -n "$flow" ] || flow='unknown'
  before_size="$( (wc -c < "$file") 2>/dev/null)" || { warn 'run-end event storage unavailable'; return 0; }

  if ! (
    {
      json_kv ts "$(now_iso)"
      json_kv run_id "$run"
      json_kv event run-end
      json_kv seq "$seq"
      json_kv pipeline "$pipeline"
      json_kv outcome "$outcome"
      json_kv duration_s "$total"
      json_kv project "$project"
      [ -z "$task" ] || json_kv task "$task"
      json_kv flow "$flow"
      [ -z "$note" ] || json_kv note "$note"
      true
    } | emit_json >> "$file"
  ) 2>/dev/null; then
    warn 'run-end persistence failed'
    return 0
  fi
  after_size="$( (wc -c < "$file") 2>/dev/null)" || { warn 'run-end persistence failed'; return 0; }
  if [ "$after_size" -le "$before_size" ]; then
    warn 'run-end persistence failed'
    return 0
  fi

  local close_warning=0
  rm -f "$ACTIVE_DIR/$run" 2>/dev/null || close_warning=1
  write_digest "$run" "$file" || close_warning=1
  [ "$close_warning" -eq 0 ] || warn 'run-end persisted with a filesystem warning'
}

write_digest() { # write_digest <run_id> <jsonl_path>
  local run="$1" file="$2" md="${2%.jsonl}.md" tmp="${2%.jsonl}.md.tmp.$$"
  if ! command -v jq >/dev/null 2>&1; then
    if ! { echo "# Run $run"; echo; echo "jq is not installed — no digest table."; \
      echo "Raw log: $file"; } 2>/dev/null > "$tmp"; then
      rm -f "$tmp" 2>/dev/null
      return 1
    fi
    mv "$tmp" "$md" 2>/dev/null || { rm -f "$tmp" 2>/dev/null; return 1; }
    return 0
  fi
  if ! (
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
    ' "$file" || exit 1

    jq -r '
      select(.event == "run-end")
      | "**Outcome:** \(.outcome) — total \(.duration_s)s\(if (.note // "") != "" then " — \(.note)" else "" end)",
        ""
    ' "$file" || exit 1

    echo "## Steps"
    echo
    echo "| # | step | outcome | dur s | stops | esc | dec | gate | tests | files | note |"
    echo "|---|---|---|---|---|---|---|---|---|---|---|"
    jq -r '
      select(.event == "step")
      | "| \(.seq) | \(.step)\(if (.subtask // "") != "" then " (\(.subtask))" else "" end) | \(.outcome) | \(.duration_s) | \(.stops // "-") | \(.escalations // "-") | \(.decisions // "-") | \(.gate // "-") | \(.tests // "-") | \(.files // "-") | \((.note // "-") | gsub("\\|"; "/")) |"
    ' "$file" || exit 1
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
    ' "$file" || exit 1
  ) 2>/dev/null > "$tmp"; then
    rm -f "$tmp" 2>/dev/null
    return 1
  fi
  mv "$tmp" "$md" 2>/dev/null || { rm -f "$tmp" 2>/dev/null; return 1; }
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
    if ! valid_run_id "$run"; then
      reject_invocation path run invalid-id
      return 0
    fi
    meta_get "$run" file || { reject_invocation path run not-found; return 0; }
  else
    printf '%s\n' "$LOG_ROOT"
  fi
}

cmd_contract() {
  local key
  [ "$#" -eq 0 ] || { reject_invocation contract argument unexpected; return 0; }
  for key in "${!RUN_LOG_CONTRACT[@]}"; do
    printf '%s=%s\n' "$key" "${RUN_LOG_CONTRACT[$key]}"
  done | LC_ALL=C sort
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
  contract)  shift; cmd_contract "$@" ;;
  ""|-h|--help|help)
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command: ${1-}" ;;
esac
