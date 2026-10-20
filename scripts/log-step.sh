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
#   scripts/log-step.sh lint [<run-id>|--all] → validate historical files without writing
#   scripts/log-step.sh contract              → print the runtime vocabulary as key=value lines
#
# Never fails a pipeline: every error is a warning on stderr and exit 0.

set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
LOG_ROOT="${ORCHESTRAIL_LOG_ROOT:-$REPO_ROOT/logs}"
RUNS_DIR="$LOG_ROOT/runs"
ACTIVE_DIR="$LOG_ROOT/.active"
METADATA_FORMAT='# run-log-metadata percent-v1'

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

meta_read() { # meta_read <run_id> <key> <output-variable>
  valid_run_id "$1" || return 1
  local metadata_file="$ACTIVE_DIR/$1" metadata_header='' metadata_line metadata_value='' metadata_found=0 metadata_legacy_flow=0
  [ -f "$metadata_file" ] || return 1
  {
    IFS= read -r metadata_header < "$metadata_file" || return 1
    while IFS= read -r metadata_line || [ -n "$metadata_line" ]; do
      if [[ "$metadata_line" == "$2="* ]] && [ "$metadata_found" -eq 0 ]; then
        metadata_value="${metadata_line#*=}"
        metadata_found=1
      fi
      if [ "$metadata_line" = flow_encoding=percent ]; then metadata_legacy_flow=1; fi
    done < "$metadata_file"
  } 2>/dev/null || return 1
  [ "$metadata_found" -eq 1 ] || return 1
  if [ "$metadata_header" = "$METADATA_FORMAT" ] ||
     { [ "$2" = flow ] && [ "$metadata_legacy_flow" -eq 1 ]; }; then
    metadata_value="${metadata_value//%0A/$'\n'}"
    metadata_value="${metadata_value//%25/%}"
  fi
  # Assign directly so trailing newlines survive decoding.
  printf -v "$3" '%s' "$metadata_value"
}

meta_get() { # meta_get <run_id> <key>
  local meta_value
  meta_read "$1" "$2" meta_value || return 1
  printf '%s\n' "$meta_value"
}

meta_encode() { # meta_encode <value>
  local encoded_value="$1"
  encoded_value="${encoded_value//%/%25}"
  encoded_value="${encoded_value//$'\n'/%0A}"
  printf '%s' "$encoded_value"
}

meta_set() { # meta_set <run_id> <key> <value>
  valid_run_id "$1" || return 1
  local f="$ACTIVE_DIR/$1"
  touch "$f" 2>/dev/null || return 1
  local tmp="$f.tmp.$$" header='' line key value
  { IFS= read -r header < "$f"; } 2>/dev/null || [ ! -s "$f" ] || return 1
  if ! { (
    printf '%s\n' "$METADATA_FORMAT" || exit 1
    while IFS= read -r line || [ -n "$line" ]; do
      [[ "$line" == *=* ]] || continue
      key="${line%%=*}"
      [ "$key" != "$2" ] || continue
      value="${line#*=}"
      if [ "$header" != "$METADATA_FORMAT" ]; then
        meta_read "$1" "$key" value || exit 1
        value="$(meta_encode "$value")" || exit 1
      fi
      printf '%s=%s\n' "$key" "$value" || exit 1
    done < "$f"
    value="$(meta_encode "$3")" || exit 1
    printf '%s=%s\n' "$2" "$value" || exit 1
  ) > "$tmp"; } 2>/dev/null; then
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
  meta_read "$run_id" file recorded_file 2>/dev/null || recorded_file=''
  recorded_seq="$(meta_get "$run_id" seq 2>/dev/null)"
  meta_read "$run_id" flow recorded_flow 2>/dev/null || recorded_flow=''
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
  meta_read "$run" pipeline pipeline || pipeline=''
  meta_read "$run" project project || project=''
  meta_read "$run" task task || task=''
  meta_read "$run" flow flow || flow=''
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
  check_step_name "$step"
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
  meta_read "$run" pipeline pipeline || pipeline=''
  meta_read "$run" project project || project=''
  meta_read "$run" task task || task=''
  meta_read "$run" flow flow || flow=''
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
  local any=0 f run active_pipeline active_task
  for f in "$ACTIVE_DIR"/*; do
    [ -f "$f" ] || continue
    any=1
    run="${f##*/}"
    meta_read "$run" pipeline active_pipeline || active_pipeline=''
    meta_read "$run" task active_task || active_task=''
    printf '%s  %s  %s\n' "$run" "$active_pipeline" "$active_task"
  done
  [ $any -eq 1 ] || echo "no active runs"
}


# Lint is a read-only consumer: no initialization or metadata lookup is needed.
cmd_lint() {
  local selector='' status=ok files=0 lines=0 invalid_lines=0 violations=0
  local key contract='{' separator='' file record diagnostics issue encoded_lines line_number checked failed=0
  local -a selected=()
  local LC_ALL=C
  lint_summary() {
    printf '{"kind":"summary","status":"%s","files":%d,"lines":%d,"invalid_lines":%d,"violations":%d}\n' \
      "$status" "$files" "$lines" "$invalid_lines" "$violations"
  }
  if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != --all ] && ! valid_run_id "$1"; }; then
    warn 'lint argument invalid-selection'
    status=unavailable; lint_summary; return 0
  fi
  [ "$#" -eq 0 ] || [ "$1" = --all ] || selector="$1"
  if ! command -v jq >/dev/null 2>&1 || ! jq -n -e 'true' >/dev/null 2>&1; then
    warn 'lint tooling unavailable'
    status=unavailable; lint_summary; return 0
  fi
  if [ ! -e "$RUNS_DIR" ] && [ ! -L "$RUNS_DIR" ]; then
    # A missing store is an empty corpus, unless a present ancestor cannot be searched.
    local ancestor="$RUNS_DIR"
    while [ ! -e "$ancestor" ] && [ "$ancestor" != / ]; do ancestor="${ancestor%/*}"; [ -n "$ancestor" ] || ancestor=/; done
    if [ ! -d "$ancestor" ] || [ ! -x "$ancestor" ]; then
      warn 'lint corpus unavailable'; status=unavailable
    fi
    lint_summary; return 0
  fi
  if [ ! -d "$RUNS_DIR" ] || [ ! -r "$RUNS_DIR" ] || [ ! -x "$RUNS_DIR" ]; then
    warn 'lint corpus unavailable'; status=unavailable; lint_summary; return 0
  fi
  # Bash glob expansion follows LC_ALL=C and preserves arbitrary filename bytes.
  if [ -n "$selector" ]; then
    for file in "$RUNS_DIR"/*-"$selector".jsonl; do
      [ -e "$file" ] || [ -L "$file" ] || continue
      selected+=("$file")
    done
  else
    for file in "$RUNS_DIR"/*.jsonl; do
      [ -e "$file" ] || [ -L "$file" ] || continue
      selected+=("$file")
    done
  fi
  for key in "${!RUN_LOG_CONTRACT[@]}"; do
    contract+="$separator\"$(json_escape "$key")\":\"$(json_escape "${RUN_LOG_CONTRACT[$key]}")\""
    separator=,
  done
  contract+='}'
  for file in "${selected[@]}"; do
    if [ ! -f "$file" ] || [ ! -r "$file" ]; then
      warn 'lint file unreadable'; failed=1; continue
    fi
    # Encode raw physical lines before Bash sees them: shell variables cannot retain NUL.
    # A failed file read is never counted as an examined empty file.
    if ! encoded_lines="$(jq -Rc '.' "$file" 2>/dev/null)"; then
      warn 'lint file-check unavailable'; failed=1; continue
    fi
    files=$((files + 1)); line_number=0; checked=0
    [ -n "$encoded_lines" ] || continue
    while IFS= read -r record; do
      line_number=$((line_number + 1))
      if ! diagnostics="$(printf '%s' "$record" | jq -Rsc --arg file "$file" --argjson line "$line_number" --argjson contract "$contract" '
        def issue($field; $code): {kind:"violation",file:$file,line:$line,field:$field,code:$code};
        def field($row; $name; $expected_type; $required):
          if ($row|has($name)|not) then
            if $required then issue($name; "missing-field") else empty end
          elif ($row[$name]|type) != $expected_type then issue($name; "invalid-type")
          elif $name == "flow" and $row[$name] == "" then issue($name; "empty-flow")
          else empty end;
        # jq accepts some numeric extensions; require complete JSON token coverage.
        def json_tokens:
          [scan("\"(?:[^\"\\\\\u0000-\u001f]|\\\\(?:[\"\\\\/bfnrt]|u[0-9a-fA-F]{4}))*\"|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?(?![0-9.eE+-])|true|false|null|[{}\\[\\]:,]|[ \\t\\r\\n]+")];
        # Preserve number tokens: jq can round or canonicalize exponent notation.
        def numeric_lexemes:
          reduce (json_tokens[] | select(test("^[ \\t\\r\\n]+$")|not)) as $token
            ({depth:0, key:null, previous:null, values:{}};
             (if $token == "{" or $token == "[" then .depth += 1
              elif $token == "}" or $token == "]" then .depth -= 1
              elif .depth == 1 and $token == ":" then .key = (.previous|fromjson)
              elif .depth == 1 and .key != null and ($token|test("^-?[0-9]")) then
                .values[.key] = $token | .key = null
              elif .depth == 1 and $token == "," then .key = null
              else . end) | .previous = $token)
          | .values;
        def bounded_exponent($text; $limit):
          ($text // "0" | capture("^(?<sign>[+-]?)(?<digits>[0-9]+)$")) as $parts
          | ($parts.digits | sub("^0+"; "") | if . == "" then "0" else . end) as $digits
          | ($limit|tostring) as $bound
          | (if ($digits|length) > ($bound|length) or (($digits|length) == ($bound|length) and $digits > $bound)
             then $limit + 1 else ($digits|tonumber) end)
            * (if $parts.sign == "-" then -1 else 1 end);
        def valid_integer_value($literal):
          ($literal | capture("^(?<sign>-?)(?<whole>[0-9]+)(?:\\.(?<fraction>[0-9]+))?(?:[eE](?<exponent>[+-]?[0-9]+))?$")) as $parts
          | ($parts.whole + ($parts.fraction // "")) as $digits
          | ($digits|sub("0+$"; "")) as $trimmed
          | ($trimmed|sub("^0+"; "")) as $significant
          | $contract["count.maximum"] as $maximum
          | if $significant == "" then true
            else (bounded_exponent($parts.exponent; (($digits|length) + ($maximum|length)))
                  - ($parts.fraction // ""|length) + ($digits|length) - ($trimmed|length)) as $scale
            | if $parts.sign == "-" or $scale < 0 or (($significant|length) + $scale) > ($maximum|length) then false
              else ($significant + ("0" * $scale)) as $integer
              | ($integer|length) < ($maximum|length) or $integer <= $maximum
              end
            end;
        def integer($row; $literals; $name; $required):
          field($row; $name; "number"; $required),
          (if ($row|has($name)) and ($row[$name]|type) == "number" then
             if (valid_integer_value($literals[$name])|not)
             then issue($name; "invalid-integer") else empty end
           else empty end);
        (fromjson) as $raw
        | (try (if ($raw | json_tokens | join("")) != $raw then {malformed:true}
                else {value:($raw|fromjson), literals:($raw|numeric_lexemes)} end) catch {malformed:true}) as $parsed
        | if $parsed.malformed then issue("record"; "invalid-json")
          elif ($parsed.value|type) != "object" then issue("record"; "invalid-object")
          else $parsed.value as $row
          | field($row; "event"; "string"; true),
            (if ($row.event|type) == "string" and (["run-start","step","run-end"]|index($row.event)|not)
             then issue("event"; "invalid-enum") else empty end),
            ("ts", "run_id", "pipeline", "flow" | field($row; .; "string"; true)),
            integer($row; $parsed.literals; "seq"; true), integer($row; $parsed.literals; "duration_s"; false),
            (if $row.event == "step" then field($row; "step"; "string"; true) else empty end),
            (if $row.event == "step" or $row.event == "run-end" then field($row; "outcome"; "string"; true) else empty end),
            ($contract | to_entries[] | select(.key|startswith(($row.event | if type == "string" then . else "" end) + "."))
             | select(.key != "step.synthetic")
             | (.key|split(".")[1]) as $name | .value as $allowed
             | if ($row|has($name)) then
                 if ($row[$name]|type) != "string" then
                   if $name == "outcome" then empty else issue($name; "invalid-type") end
                 elif ($allowed|split("|")|index($row[$name])|not) then issue($name; "invalid-enum")
                 else empty end
               else empty end),
            ($contract["count.fields"]|split(" ")[] | integer($row; $parsed.literals; .; false))
          end
      ' 2>/dev/null)"; then
        warn 'lint tooling unavailable'; failed=1
        [ "$checked" -gt 0 ] || files=$((files - 1))
        break
      fi
      checked=$((checked + 1)); lines=$((lines + 1))
      if [ -n "$diagnostics" ]; then
        invalid_lines=$((invalid_lines + 1))
        while IFS= read -r issue; do
          printf '%s\n' "$issue"
          violations=$((violations + 1))
        done <<< "$diagnostics"
      fi
    done <<< "$encoded_lines"
  done
  if [ "$failed" -eq 1 ]; then
    if [ "$files" -gt 0 ]; then status=partial; else status=unavailable; fi
  fi
  lint_summary
  return 0
}

# ── dispatch ──────────────────────────────────────────────────────────
case "${1-}" in
  run-start) shift; cmd_run_start "$@" ;;
  step)      shift; cmd_step "$@" ;;
  run-end)   shift; cmd_run_end "$@" ;;
  path)      shift; cmd_path "$@" ;;
  active)    shift; cmd_active "$@" ;;
  contract)  shift; cmd_contract "$@" ;;
  lint)      shift; cmd_lint "$@" ;;
  ""|-h|--help|help)
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die 'command invalid-command' ;;
esac
