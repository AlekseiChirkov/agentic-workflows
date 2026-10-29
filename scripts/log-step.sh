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
  [hook.required]='session_id agent_id checkpoint_id span_start_ms span_end_ms timing_source boundary'
  [hook.identity_pattern]='^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'
  [hook.timing_source]='hook'
  [hook.boundary]='session|subagent'
  [hook.span_kind]='work|waiting'
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

event_option_allowed() { # event_option_allowed <event> <option>
  case "$1:$2" in
      run-start:--pipeline|run-start:--project|run-start:--task|run-start:--spec|run-start:--flow|run-start:--flags|\
      step:--run|step:--step|step:--outcome|step:--stops|step:--escalations|step:--decisions|step:--questions|step:--gate|step:--tests|step:--fix-tasks|step:--promoted|step:--amendments|step:--files|step:--subtask|step:--blocker|step:--note|step:--session-id|step:--agent-id|step:--checkpoint-id|step:--parent-checkpoint-id|step:--span-start-ms|step:--span-end-ms|step:--timing-source|step:--boundary|step:--span-kind|\
      run-end:--run|run-end:--outcome|run-end:--note) return 0 ;;
    *) return 1 ;;
  esac
}

parse_arguments() { # parse_arguments <event> <option> <value> ...
  local event="$1" option key
  shift
  PARSED_ARGS=()
  PARSE_ERROR_FIELD='argument'
  PARSE_ERROR_CODE='invalid-option'
  while [ "$#" -gt 0 ]; do
    option="$1"
    if ! event_option_allowed "$event" "$option"; then
      PARSE_ERROR_FIELD='argument'
      PARSE_ERROR_CODE='invalid-option'
      return 1
    fi
    key="${option#--}"
    key="${key//-/_}"
    PARSE_ERROR_FIELD="$key"
    PARSE_ERROR_CODE='duplicate-option'
    [[ ${PARSED_ARGS[$key]+present} ]] && return 1
    if [ "$#" -lt 2 ] || event_option_allowed run-start "$2" ||
       event_option_allowed step "$2" || event_option_allowed run-end "$2"; then
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
  validate_hook_args
}

# The tuple is explicit; accepted deliveries live only in active metadata.
is_correlated_step() {
  local field
  for field in ${RUN_LOG_CONTRACT[hook.required]} parent_checkpoint_id span_kind; do
    has_parsed_arg "$field" && return 0
  done
  return 1
}

valid_hook_identity() {
  local pattern="${RUN_LOG_CONTRACT[hook.identity_pattern]}"
  [[ "$1" =~ $pattern ]]
}

validate_hook_identity_fields() {
  local field
  for field in ${RUN_LOG_CONTRACT[hook.required]}; do
    if ! has_parsed_arg "$field"; then
      reject_invocation step "$field" missing-required; return 1
    fi
  done
  for field in session_id agent_id checkpoint_id parent_checkpoint_id; do
    if has_parsed_arg "$field" && ! valid_hook_identity "${PARSED_ARGS[$field]}"; then
      reject_invocation step "$field" invalid-id; return 1
    fi
  done
}

validate_hook_span_fields() {
  local field
  for field in span_start_ms span_end_ms; do
    if ! valid_count "${PARSED_ARGS[$field]}"; then
      reject_invocation step "$field" invalid-integer; return 1
    fi
  done
  if [ "${PARSED_ARGS[span_end_ms]}" -lt "${PARSED_ARGS[span_start_ms]}" ]; then
    reject_invocation step span_end_ms invalid-interval; return 1
  fi
  validate_enum_arg step timing_source hook.timing_source yes || return 1
  validate_enum_arg step boundary hook.boundary yes || return 1
  validate_enum_arg step span_kind hook.span_kind no || return 1
  if [ "${PARSED_ARGS[step]}" = unknown ] &&
     { [ "${PARSED_ARGS[boundary]}" != session ] ||
       [ "${PARSED_ARGS[agent_id]}" != "${PARSED_ARGS[session_id]}" ]; }; then
    reject_invocation step step ambiguous-unknown; return 1
  fi
  if has_parsed_arg parent_checkpoint_id &&
     [ "${PARSED_ARGS[parent_checkpoint_id]}" = "${PARSED_ARGS[checkpoint_id]}" ]; then
    reject_invocation step parent_checkpoint_id self-parent; return 1
  fi
}

validate_hook_args() {
  is_correlated_step || return 0
  validate_hook_identity_fields || return 1
  validate_hook_span_fields || return 1
  if ! command -v jq >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1 ||
     ! command -v truncate >/dev/null 2>&1; then
    reject_invocation step correlation dependencies-unavailable; return 1
  fi
}

# Use the existing append-only event inode as a stable per-run lock. Replacing
# metadata does not replace this inode. Never inspect event contents for identity.
lock_run() { # lock_run <event> <run> <event-path>
  if command -v flock >/dev/null 2>&1; then
    if ! { exec {RUN_LOCK_FD}>> "$3"; } 2>/dev/null ||
       ! flock -x -w 5 "$RUN_LOCK_FD" 2>/dev/null; then
      reject_invocation "$1" run lock-unavailable; return 1
    fi
  fi
  [ -f "$ACTIVE_DIR/$2" ] || { reject_invocation "$1" run not-found; return 1; }
}

hook_receipt() { # hook_receipt <run> <sequence> <duplicate>
  jq -cn --arg run "${1}" --arg session "${PARSED_ARGS[session_id]}" \
    --arg agent "${PARSED_ARGS[agent_id]}" --arg checkpoint "${PARSED_ARGS[checkpoint_id]}" \
    --argjson seq "$2" --argjson duplicate "$3" \
    '{kind:"accepted",run_id:$run,session_id:$session,agent_id:$agent,
      checkpoint_id:$checkpoint,seq:$seq,duplicate:$duplicate}'
}

stage_hook_metadata() { # stage_hook_metadata <run> <path> <context-json>
  local header line key value last_epoch seq delivery_key delivery
  last_epoch="$(jq -r .last_epoch <<< "$3")" || return 1
  seq="$(jq -r .seq <<< "$3")" || return 1
  delivery_key="$(jq -r .delivery_key <<< "$3")" || return 1
  delivery="$(jq -r .delivery <<< "$3")" || return 1
  IFS= read -r header < "$ACTIVE_DIR/$1" || return 1
  (
    printf '%s\n' "$METADATA_FORMAT" || exit 1
    while IFS= read -r line || [ -n "$line" ]; do
      [[ "$line" == *=* ]] || continue
      key="${line%%=*}"
      case "$key" in seq|last_epoch) continue ;; esac
      [ "$key" != "$delivery_key" ] || continue
      value="${line#*=}"
      if [ "$header" != "$METADATA_FORMAT" ]; then
        meta_read "$1" "$key" value || exit 1
        value="$(meta_encode "$value")" || exit 1
      fi
      printf '%s=%s\n' "$key" "$value" || exit 1
    done < "$ACTIVE_DIR/$1"
    printf 'last_epoch=%s\nseq=%s\n' "$last_epoch" "$seq" || exit 1
    printf '%s=%s\n' "$delivery_key" "$(meta_encode "$delivery")" || exit 1
  ) > "$2"
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
  if [ ! -d "$workflows_dir" ] || [ ! -r "$workflows_dir" ] || [ ! -x "$workflows_dir" ]; then
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
now_millis() {
  # Keep the full fractional field before dropping micro/nanoseconds: some date
  # implementations lose leading zeros when formatting a reduced-width %3N.
  local clock_stamp
  clock_stamp="$(date -u +%s%N)" || return 1
  printf '%s\n' "${clock_stamp%??????}"
}

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

emit_json_jq() {
  jq -Rn -c '
      [inputs
       | select(length > 0)
       | (index("=")) as $i
       | {key: .[0:$i], value: (("\"" + .[$i+1:] + "\"") | fromjson)}]
      | from_entries
      | with_entries(
          if (.key | IN("ts_ms","span_start_ms","span_end_ms","seq","duration_s","stops","escalations","decisions","questions","fix_tasks","amendments","files"))
             and (.value | type == "string" and test("^(0|[1-9][0-9]*)$"))
          then .value |= tonumber else . end)
  '
}

emit_json_legacy() {
  local first=1 line key val
  printf '{'
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    key="${line%%=*}"
    val="${line#*=}"
    [ $first -eq 1 ] || printf ','
    first=0
    case "$key" in
      ts_ms|span_start_ms|span_end_ms|seq|duration_s|stops|escalations|decisions|questions|fix_tasks|amendments|files)
        if [[ "$val" =~ ^(0|[1-9][0-9]*)$ ]]; then
          printf '"%s":%s' "$key" "$val"
          continue
        fi ;;
    esac
    printf '"%s":"%s"' "$key" "$val"
  done
  printf '}\n'
}

emit_json() {
  # Reads KEY=JSON-ESCAPED-VALUE pairs on stdin and emits one JSON object.
  if command -v jq >/dev/null 2>&1; then
    emit_json_jq
  else
    emit_json_legacy
  fi
}

# Bash line reads discard NUL bytes; reject them before interpreting metadata.
metadata_has_no_nul() {
  local metadata_probe metadata_status metadata_fd
  { exec {metadata_fd}< "$1"; } 2>/dev/null || return 1
  IFS= read -r -d '' metadata_probe <&"$metadata_fd" 2>/dev/null
  metadata_status=$?
  { exec {metadata_fd}<&-; } 2>/dev/null || return 1
  [ "$metadata_status" -eq 1 ]
}

meta_read() { # meta_read <run_id> <key> <output-variable>
  valid_run_id "$1" || return 1
  local metadata_file="$ACTIVE_DIR/$1" metadata_header='' metadata_line metadata_value='' metadata_found=0 metadata_legacy_flow=0
  [ -f "$metadata_file" ] || return 1
  metadata_has_no_nul "$metadata_file" || return 1
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

meta_set() ( # meta_set <run_id> <key> <value>
  umask 077
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
)

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
  local run_id ts file base file_pipeline contract_version="" start_epoch active recorded_file recorded_seq recorded_flow usage_key_fingerprint=''
  # Registration is optional and must never prevent existing lifecycle logging.
  if [ -n "${USAGE_TELEMETRY_CONFIG:-}" ] && command -v python3 >/dev/null 2>&1; then
    usage_key_fingerprint="$(python3 "$SCRIPT_DIR/usage_telemetry_ingest.py" register 2>/dev/null)" || usage_key_fingerprint=''
    [[ "$usage_key_fingerprint" =~ ^[0-9a-f]{64}$ ]] || usage_key_fingerprint=''
  fi
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
  if [ -n "$usage_key_fingerprint" ] && [ -n "${USAGE_TELEMETRY_AUTHORITY_KEY:-}" ]; then
    local usage_authority_fingerprint=''
    usage_authority_fingerprint="$(python3 "$SCRIPT_DIR/usage_telemetry_ingest.py" register-authority 2>/dev/null)" || usage_authority_fingerprint=''
    if [[ "$usage_authority_fingerprint" =~ ^[0-9a-f]{64}$ ]]; then
      meta_set "$run_id" usage_authority_key_sha256 "$usage_authority_fingerprint" || {
        rm -f "$active" 2>/dev/null
        warn 'run-start metadata persistence failed'
        return 0
      }
    fi
  fi
  if [ -n "$usage_key_fingerprint" ]; then
    meta_set "$run_id" usage_key_fingerprint "$usage_key_fingerprint" || {
      rm -f "$active" 2>/dev/null
      warn 'run-start metadata persistence failed'
      return 0
    }
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
      json_kv ts_ms "$(now_millis)"
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
# Private step phases read and update cmd_step's invocation-local step_context.
# Call mutating phases directly: subshells and pipelines cannot update their owner.
# Storage, replay, clock, inherited labels and staged receipt fields use fixed keys;
# PARSED_ARGS remains the validated public options, including normalized aliases.
normalize_step_arguments() {
  normalize_step_aliases "${PARSED_ARGS[outcome]-}" "${PARSED_ARGS[gate]-}" "${PARSED_ARGS[note]-}"
  if has_parsed_arg outcome; then PARSED_ARGS[outcome]="$NORMALIZED_OUTCOME"; fi
  if has_parsed_arg gate; then PARSED_ARGS[gate]="$NORMALIZED_GATE"; fi
  if has_parsed_arg note || [ -n "$NORMALIZED_NOTE" ]; then PARSED_ARGS[note]="$NORMALIZED_NOTE"; fi
}

prepare_step_storage() {
  local run="${step_context[run]}" file
  file="$(meta_get "$run" file)" || { reject_invocation step run not-found; return 1; }
  [ -n "$file" ] && [ -f "$file" ] || { reject_invocation step run not-found; return 1; }
  lock_run step "$run" "$file" || return 1
  step_context[file]="$file"
}

# Check the original number tokens before JSON parsing can normalize them.
read_step_delivery_sequence() {
  printf '%s' "$1" | jq -Rser '
    def json_tokens:
      [scan("\"(?:[^\"\\\\\u0000-\u001f]|\\\\(?:[\"\\\\/bfnrt]|u[0-9a-fA-F]{4}))*\"|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?(?![0-9.eE+-])|true|false|null|[{}\\[\\]:,]|[ \\t\\r\\n]+")];
    . as $original | json_tokens as $tokens |
    select(($tokens | join("")) == $original) |
    select(all($tokens[] | select(test("^-?[0-9]"));
      test("^(0|[1-9][0-9]*)\\z") and
      (length < 16 or (length == 16 and . <= "9007199254740991")))) |
    ($tokens | map(select(test("^[ \\t\\r\\n]+$") | not))) as $compact |
    [$compact | range(0; length - 1) as $index |
      select(.[$index + 1] == ":") | .[$index] | fromjson] as $keys |
    select(($keys | length) == ($keys | unique | length)) |
    fromjson |
    select(type == "object" and keys == ["arguments", "seq"] and
      (.arguments | type == "object") and
      (.seq | type == "number" and . > 0 and . <= 9007199254740991)) |
    .seq
  ' 2>/dev/null
}

replay_step_delivery() {
  local previous="$1" run="${step_context[run]}" payload="${step_context[payload]}" seq
  seq="$(read_step_delivery_sequence "$previous")" || {
    warn 'step accepted metadata unavailable'; return 1;
  }
  if ! printf '%s' "$previous" | jq -e --argjson payload "$payload" '.arguments == $payload' >/dev/null 2>&1; then
    reject_invocation step checkpoint_id conflicting-delivery; return 1
  fi
  hook_receipt "$run" "$seq" true 2>/dev/null || warn 'step receipt unavailable'
}

prepare_step_delivery() {
  local run="${step_context[run]}" delivery_key payload previous field
  step_context[correlated]=0
  if ! is_correlated_step; then return 0; fi
  step_context[correlated]=1
  delivery_key="accepted|${PARSED_ARGS[session_id]}|${PARSED_ARGS[checkpoint_id]}"
  PARSED_ARGS[span_kind]="${PARSED_ARGS[span_kind]-work}"
  payload="$(for field in "${!PARSED_ARGS[@]}"; do json_kv "$field" "${PARSED_ARGS[$field]}"; done | emit_json | jq -Sc .)" || {
    warn 'step correlation tooling unavailable'; return 1;
  }
  step_context[delivery_key]="$delivery_key"
  step_context[payload]="$payload"
  if meta_read "$run" "$delivery_key" previous; then
    replay_step_delivery "$previous"
    return 1
  fi
}

read_step_clock() {
  local run="${step_context[run]}" file="${step_context[file]}" last seq dur event_epoch ts before_size
  before_size="$( (wc -c < "$file") 2>/dev/null)" || { warn 'step event storage unavailable'; return 1; }
  last="$(meta_get "$run" last_epoch)"
  seq="$(meta_get "$run" seq)"
  valid_count "$last" || last="$(now_epoch)"
  valid_count "$seq" || seq=0
  seq=$((seq + 1))
  event_epoch="$(now_epoch)"
  dur=$((event_epoch - last))
  if [ "${step_context[correlated]}" -eq 1 ]; then
    dur=$(( (PARSED_ARGS[span_end_ms] - PARSED_ARGS[span_start_ms]) / 1000 ))
  fi
  [ "$dur" -ge 0 ] || dur=0
  ts="$(now_iso)"
  step_context[before_size]="$before_size"
  step_context[seq]="$seq"
  step_context[event_epoch]="$event_epoch"
  step_context[duration_s]="$dur"
  step_context[ts]="$ts"
}

read_step_metadata() {
  local run="${step_context[run]}" pipeline project task flow
  meta_read "$run" pipeline pipeline || pipeline=''
  meta_read "$run" project project || project=''
  meta_read "$run" task task || task=''
  meta_read "$run" flow flow || flow=''
  [ -n "$flow" ] || flow='unknown'
  step_context[pipeline]="$pipeline"
  step_context[project]="$project"
  step_context[task]="$task"
  step_context[flow]="$flow"
}

stage_step_delivery() {
  [ "${step_context[correlated]}" -eq 1 ] || return 0
  local run="${step_context[run]}" pending delivery receipt context_json
  pending="$ACTIVE_DIR/$run.pending.$$"
  step_context[pending]="$pending"
  (umask 077; : > "$pending") 2>/dev/null || { warn 'step metadata persistence failed'; return 1; }
  delivery="$(jq -cn --argjson arguments "${step_context[payload]}" --argjson seq "${step_context[seq]}" '{arguments:$arguments,seq:$seq}')" &&
  receipt="$(hook_receipt "$run" "${step_context[seq]}" false)" &&
  context_json="$(jq -cn --arg last_epoch "${step_context[event_epoch]}" --arg seq "${step_context[seq]}" \
    --arg delivery_key "${step_context[delivery_key]}" --arg delivery "$delivery" \
    '{last_epoch:$last_epoch,seq:$seq,delivery_key:$delivery_key,delivery:$delivery}')" &&
  stage_hook_metadata "$run" "$pending" "$context_json" 2>/dev/null || {
    rm -f "$pending" 2>/dev/null
    warn 'step metadata persistence failed'; return 1;
  }
  step_context[receipt]="$receipt"
}

emit_step_core_fields() {
  local field
  json_kv ts "${step_context[ts]}"
  json_kv ts_ms "$(now_millis)"
  json_kv run_id "${step_context[run]}"
  json_kv event step
  json_kv seq "${step_context[seq]}"
  json_kv pipeline "${step_context[pipeline]}"
  json_kv step "${PARSED_ARGS[step]-}"
  json_kv outcome "${PARSED_ARGS[outcome]-}"
  json_kv duration_s "${step_context[duration_s]}"
  if [ "${step_context[correlated]}" -eq 1 ]; then
    for field in ${RUN_LOG_CONTRACT[hook.required]} parent_checkpoint_id span_kind; do
      has_parsed_arg "$field" && json_kv "$field" "${PARSED_ARGS[$field]}"
    done
  fi
}

emit_step_optional_fields() {
  local field
  json_kv project "${step_context[project]}"
  [ -z "${step_context[task]}" ] || json_kv task "${step_context[task]}"
  json_kv flow "${step_context[flow]}"
  for field in subtask stops escalations decisions questions gate tests fix_tasks promoted amendments files blocker note; do
    [ -z "${PARSED_ARGS[$field]-}" ] || json_kv "$field" "${PARSED_ARGS[$field]}"
  done
  true
}

rollback_step_append() {
  if [ "${step_context[correlated]}" -eq 1 ]; then
    truncate -s "${step_context[before_size]}" "${step_context[file]}" 2>/dev/null
    rm -f "${step_context[pending]}" 2>/dev/null
  fi
}

append_step_event() {
  local file="${step_context[file]}" before_size="${step_context[before_size]}" after_size
  if ! (
    {
      emit_step_core_fields
      emit_step_optional_fields
    } | emit_json >> "$file"
  ) 2>/dev/null; then
    rollback_step_append
    warn 'step event persistence failed'
    return 1
  fi
  after_size="$( (wc -c < "$file") 2>/dev/null)" || after_size=0
  if [ "$after_size" -le "$before_size" ]; then
    rollback_step_append
    warn 'step event persistence failed'
    return 1
  fi
}

commit_step_metadata() {
  local run="${step_context[run]}" pending="${step_context[pending]-}"
  if [ "${step_context[correlated]}" -eq 1 ]; then
    if ! mv "$pending" "$ACTIVE_DIR/$run" 2>/dev/null; then
      truncate -s "${step_context[before_size]}" "${step_context[file]}" 2>/dev/null
      rm -f "$pending" 2>/dev/null
      warn 'step metadata persistence failed'; return 1
    fi
    printf '%s\n' "${step_context[receipt]}"
    [ "${PARSED_ARGS[step]-}" = unknown ] || check_step_name "${PARSED_ARGS[step]-}"
    return 0
  fi
  if ! meta_set "$run" last_epoch "${step_context[event_epoch]}" ||
     ! meta_set "$run" seq "${step_context[seq]}" ||
     ! meta_set "$run" flow "${step_context[flow]}"; then
    warn 'step metadata persistence failed'
    return 1
  fi
  check_step_name "${PARSED_ARGS[step]-}"
}

cmd_step() {
  local -A step_context=()
  if ! parse_arguments step "$@"; then
    reject_invocation step "$PARSE_ERROR_FIELD" "$PARSE_ERROR_CODE"
    return 0
  fi
  normalize_step_arguments
  step_context[run]="${PARSED_ARGS[run]-}"
  if ! validate_step_args; then return 0; fi
  prepare_step_storage || return 0
  prepare_step_delivery || return 0
  read_step_clock || return 0
  read_step_metadata
  stage_step_delivery || return 0
  append_step_event || return 0
  commit_step_metadata || return 0
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
  [ -n "$file" ] && [ -f "$file" ] || { reject_invocation run-end run not-found; return 0; }
  lock_run run-end "$run" "$file" || return 0

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
      json_kv ts_ms "$(now_millis)"
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
  if [ "$#" -eq 0 ]; then
    printf '%s\n' "$LOG_ROOT"
    return 0
  fi
  if [ "$#" -ne 2 ] || [ "$1" != '--run' ]; then
    reject_invocation path argument invalid-option
    return 0
  fi
  local run="$2"
  if ! valid_run_id "$run"; then
    reject_invocation path run invalid-id
    return 0
  fi
  meta_get "$run" file || { reject_invocation path run not-found; return 0; }
}

cmd_contract() {
  local key registry=''
  [ "$#" -eq 0 ] || { reject_invocation contract argument unexpected; return 0; }
  if command -v python3 >/dev/null 2>&1; then
    registry="$(python3 -c '
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location("usage_telemetry_contract", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw = module.export_schema_registry()
registry = json.loads(raw)
expected = {
    "source_profile": ("validate_source_profile_json", module.PROFILE_LIMIT),
    "source_selection": ("validate_source_selection_json", module.SELECTION_LIMIT),
    "observation": ("validate_observation_json", module.OBSERVATION_LIMIT),
    "usage_bundle": ("validate_usage_bundle_json", module.BUNDLE_LIMIT),
    "inventory": ("validate_inventory_json", module.INVENTORY_LIMIT),
    "collection_segment": ("validate_collection_segment_json", module.SEGMENT_LIMIT),
    "diagnostic_measurement": ("validate_diagnostic_measurement_json", module.DIAGNOSTIC_LIMIT),
    "price_snapshot": ("validate_price_snapshot_json", module.PRICE_SNAPSHOT_LIMIT),
    "pricing_scenario": ("validate_pricing_scenario_json", module.PRICING_SCENARIO_LIMIT),
    "warning_policy": ("validate_warning_policy_json", module.WARNING_POLICY_LIMIT),
    "analysis_corpus": ("validate_analysis_corpus_json", module.ANALYSIS_CORPUS_LIMIT),
    "usage_accepted": ("validate_usage_receipt_json", module.RECEIPT_LIMIT),
    "lifecycle_projection": ("validate_lifecycle_projection_json", module.LIFECYCLE_PROJECTION_LIMIT),
    "current_run_snapshot": ("validate_current_run_snapshot_json", module.CURRENT_RUN_SNAPSHOT_LIMIT),
}
source = Path(sys.argv[1]).read_bytes()
if (not isinstance(registry, dict) or registry != module.schema_registry() or
        type(registry.get("schema_version")) is not int or registry["schema_version"] != 1 or
        set(registry) != {"schema_version", "measurement_states", "measurement_reasons", "kinds", "validator_source", "validator_source_sha256"} or
        registry["measurement_states"] != sorted(module.MEASUREMENT_STATES) or
        registry["measurement_reasons"] != sorted(module.MEASUREMENT_REASONS) or
        registry["validator_source"].encode("utf-8") != source or
        registry["validator_source_sha256"] != hashlib.sha256(source).hexdigest() or
        registry["kinds"] != {kind: {"validator": name, "max_bytes": limit}
                               for kind, (name, limit) in expected.items()} or
        any(not callable(getattr(module, name, None)) or type(limit) is not int or limit <= 0
            for name, limit in expected.values())):
    raise ValueError("invalid registry")
print(json.dumps(registry, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
' "$SCRIPT_DIR/usage_telemetry_contract.py" 2>/dev/null)" || registry=''
  fi
  {
    for key in "${!RUN_LOG_CONTRACT[@]}"; do
      printf '%s=%s\n' "$key" "${RUN_LOG_CONTRACT[$key]}"
    done
    if [ -n "$registry" ]; then
      printf 'usage.availability=available\nusage.registry=%s\n' "$registry"
    else
      printf 'usage.availability=unavailable\n'
    fi
  } | LC_ALL=C sort
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
            integer($row; $parsed.literals; "ts_ms"; false),
            (if ([$contract["hook.required"]|split(" ")[]] + ["parent_checkpoint_id", "span_kind"]
                 | any(. as $name | $row|has($name))) then
               (if $row.event != "step" then issue("event"; "invalid-correlation") else empty end),
               ($contract["hook.required"]|split(" ")[] | . as $name
                | if ($name == "span_start_ms" or $name == "span_end_ms")
                  then integer($row; $parsed.literals; $name; true)
                  else field($row; $name; "string"; true) end),
               ("session_id", "agent_id", "checkpoint_id", "parent_checkpoint_id" | . as $name
                | if ($row|has($name)) then
                    if ($row[$name]|type) != "string" then
                      if $name == "parent_checkpoint_id" then issue($name; "invalid-type") else empty end
                    elif ($row[$name] | . as $identity
                          | [match($contract["hook.identity_pattern"]).string] != [$identity])
                    then issue($name; "invalid-id") else empty end
                  else empty end),
               ("timing_source", "boundary", "span_kind" | . as $name
                | if ($row|has($name)) then
                    if ($row[$name]|type) != "string" then
                      if $name == "span_kind" then issue($name; "invalid-type") else empty end
                    elif ($contract["hook."+$name]|split("|")|index($row[$name])|not)
                    then issue($name; "invalid-enum") else empty end
                  else empty end),
               (if ($row.span_start_ms|type) == "number" and ($row.span_end_ms|type) == "number"
                   and $row.span_end_ms < $row.span_start_ms
                then issue("span_end_ms"; "invalid-interval") else empty end),
               (if $row.parent_checkpoint_id != null and $row.parent_checkpoint_id == $row.checkpoint_id
                then issue("parent_checkpoint_id"; "self-parent") else empty end),
               (if $row.step == "unknown" and ($row.boundary != "session" or $row.agent_id != $row.session_id)
                then issue("step"; "ambiguous-unknown") else empty end)
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

cmd_usage_ingest() {
  local mode="${ORCHESTRAIL_USAGE_MODE:-off}" receipt
  if [ "$mode" != on ]; then
    warn 'usage collection_disabled'
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    warn 'usage dependency_unavailable'
    return 0
  fi
  if { [ "$#" -ne 2 ] && [ "$#" -ne 4 ]; } || [ "$1" != --manifest ] || [ -z "$2" ]; then
    warn 'usage invalid_schema'
    return 0
  fi
  local -a ingest_args=(ingest "$2" "$LOG_ROOT")
  if [ "$#" -eq 4 ]; then
    if [ "$3" != --late-certificate ] || [ -z "$4" ]; then
      warn 'usage invalid_schema'
      return 0
    fi
    ingest_args+=("$4")
  fi
  receipt="$(python3 "$SCRIPT_DIR/usage_telemetry_ingest.py" "${ingest_args[@]}" 2>/dev/null)" || {
    warn 'usage ingestion_unavailable'
    return 0
  }
  [ -n "$receipt" ] || { warn 'usage ingestion_unavailable'; return 0; }
  printf '%s\n' "$receipt"
}

# ── dispatch ──────────────────────────────────────────────────────────
case "${1-}" in
  run-start) shift; cmd_run_start "$@" ;;
  usage-ingest) shift; cmd_usage_ingest "$@" ;;
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
