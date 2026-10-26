#!/usr/bin/env bash
# Correlate explicit dispatches to bounded native Claude Stop/SubagentStop input.
# Usage: dispatch --run ID --agent-id ID --boundary session|subagent
#          [--expected-skill NAME] [--parent-checkpoint-id ID] [--span-kind work|waiting]
#        status --checkpoint ID
#        fallback --checkpoint ID --step NAME --outcome VALUE [--tests VALUE] [--gate VALUE]
# No argument consumes claude-stop-v1 JSON on stdin. Every path exits zero;
# stdout contains only a dispatch marker or private status, never a blocking decision.
set -uo pipefail
export LC_ALL=C
umask 077
exec 3>&2

HOOK_SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
HOOK_HOME="${ORCHESTRAIL_HOME:-$HOOK_SOURCE}"
HOOK_STATE="${XDG_STATE_HOME:-${HOME:-}/.local/state}/orchestrail/hooks"
HOOK_CONFIG="${XDG_CONFIG_HOME:-${HOME:-}/.config}/orchestrail/projects"
HOOK_HELPER="$HOOK_HOME/scripts/log-step.sh"
HOOK_TEMP=''
HOOK_WARNED=no

warn() {
  if [ "$HOOK_WARNED" = no ]; then
    printf 'orchestrail hook: coverage unavailable [%s]\n' "$1" >&3
    HOOK_WARNED=yes
  fi
}
cleanup() { [ -z "$HOOK_TEMP" ] || rm -f -- "$HOOK_TEMP" 2>/dev/null; }
trap cleanup EXIT

identity_ok() { [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$ ]]; }
run_ok() { [[ "$1" =~ ^[a-f0-9]{8}$ ]]; }
clock_ms() {
  local stamp
  stamp="$(date +%s%N 2>/dev/null)" || return 1
  [[ "$stamp" =~ ^[0-9]{16,25}$ ]] || return 1
  stamp="${stamp:0:${#stamp}-6}"
  [[ "$stamp" =~ ^(0|[1-9][0-9]*)$ ]] && [ "${#stamp}" -le 16 ] || return 1
  [ "$stamp" -le 9007199254740991 ] || return 1
  printf '%s' "$stamp"
}

# Select the most-specific canonical registered ancestor before opening private
# correlation, transcripts, or producer state. Registry order is irrelevant.
project_for() {
  local location="$1" canonical registered best=''
  [ -d "$location" ] && [ -f "$HOOK_CONFIG" ] && [ -r "$HOOK_CONFIG" ] || return 1
  canonical="$(cd -- "$location" 2>/dev/null && pwd -P)" || return 1
  while IFS= read -r registered || [ -n "$registered" ]; do
    [[ "$registered" = /* ]] && [ -d "$registered" ] || continue
    [ "$(cd -- "$registered" 2>/dev/null && pwd -P)" = "$registered" ] || continue
    if [ "$registered" = / ] || [ "$canonical" = "$registered" ] || [[ "$canonical" = "$registered/"* ]]; then
      if [ "${#registered}" -gt "${#best}" ]; then best="$registered"; fi
    fi
  done < "$HOOK_CONFIG"
  [ -n "$best" ] || return 1
  printf '%s' "$best"
}

# Options are deliberately closed. Reject duplicates and empty values before any
# ownership transition, including fallback's ordinary producer call.
declare -A OPT=()
options() {
  local mode="$1" key
  shift
  while [ "$#" -gt 0 ]; do
    key="$1"
    [ "$#" -ge 2 ] && [ -n "$2" ] || return 1
    case "$mode:$key" in
      dispatch:--run|dispatch:--agent-id|dispatch:--boundary|dispatch:--expected-skill|dispatch:--parent-checkpoint-id|dispatch:--span-kind|status:--checkpoint|fallback:--checkpoint|fallback:--step|fallback:--outcome|fallback:--tests|fallback:--gate) ;;
      *) return 1 ;;
    esac
    [ "${OPT[$key]+present}" != present ] || return 1
    OPT["$key"]="$2"
    shift 2
  done
}

enums_ok() {
  case "$1" in ok|blocked|failed|skipped|deferred) ;; *) return 1 ;; esac
  if [ "${OPT[--tests]+present}" = present ]; then
    case "${OPT[--tests]}" in red|green|n-a|failed|not-run|pinned) ;; *) return 1 ;; esac
  fi
  if [ "${OPT[--gate]+present}" = present ]; then
    case "${OPT[--gate]}" in pass|fail|n-a|needs-work|ready) ;; *) return 1 ;; esac
  fi
}

save_record() {
  HOOK_TEMP="$(mktemp "$HOOK_STATE/.record.XXXXXX" 2>/dev/null)" || return 1
  printf '%s\n' "$RECORD" > "$HOOK_TEMP" && chmod 600 "$HOOK_TEMP" &&
    mv -f -- "$HOOK_TEMP" "$RECORD_PATH" || return 1
  HOOK_TEMP=''
}

# Inspect original JSON tokens before jq can round a fractional/exponent number.
# Fresh protocol numbers are bounded unsigned decimal integer tokens; quoted
# strings remain whole tokens and cannot masquerade as numeric fields.
canonical_integer_tokens() {
  printf '%s' "$1" | jq -Rse '
    def json_tokens:
      [scan("\"(?:[^\"\\\\\u0000-\u001f]|\\\\(?:[\"\\\\/bfnrt]|u[0-9a-fA-F]{4}))*\"|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?(?![0-9.eE+-])|true|false|null|[{}\\[\\]:,]|[ \\t\\r\\n]+")];
    . as $original | json_tokens as $tokens |
    ($tokens | join("")) == $original and
    all($tokens[] | select(test("^-?[0-9]"));
      test("^(0|[1-9][0-9]*)\\z") and
      (length < 16 or (length == 16 and . <= "9007199254740991")))
  ' >/dev/null 2>&1
}

record_valid() {
  canonical_integer_tokens "$RECORD" || return 1
  jq -se '
    def id: type == "string" and test("^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\z");
    def count: type == "number" and floor == . and . >= 0 and . <= 9007199254740991;
    length == 1 and (.[0] | type == "object" and .schema_version == 1 and
    (.run_id | type == "string" and test("^[a-f0-9]{8}\\z")) and
    ([.session_id,.agent_id,.checkpoint_id] | all(.[]; id)) and
    (.project | type == "string" and startswith("/")) and
    (.span_start_ms | count) and
    (.boundary == "session" or .boundary == "subagent") and
    (if .boundary == "session" then .agent_id == .session_id else true end) and
    (.state | IN("pending","delivering","accepted","fallback","fallback-attempted")) and
    (if has("expected_skill") then (.expected_skill | id) else true end) and
    (if has("parent_checkpoint_id") then (.parent_checkpoint_id | id) and .parent_checkpoint_id != .checkpoint_id else true end) and
    (.span_kind == "work" or .span_kind == "waiting") and
    (if .state == "delivering" or .state == "accepted" then . as $record |
      (.native_agent_id | type == "string" and length > 0 and (test("[\u0000\r\n]") | not)) and
      (if .boundary == "session" then .native_agent_id == .session_id else true end) and
      (.payload | type == "object" and
        .run_id == $record.run_id and .session_id == $record.session_id and
        .agent_id == $record.agent_id and .checkpoint_id == $record.checkpoint_id and
        .span_start_ms == $record.span_start_ms and .boundary == $record.boundary and
        .span_kind == $record.span_kind and .parent_checkpoint_id == $record.parent_checkpoint_id and
        (has("parent_checkpoint_id") == ($record | has("parent_checkpoint_id"))) and
        .timing_source == "hook" and (.span_end_ms | count) and .span_end_ms >= .span_start_ms and
        (.step | id) and (.outcome | IN("ok","blocked","failed","skipped","deferred")) and
        (if has("tests") then (.tests | IN("red","green","n-a","failed","not-run","pinned")) else true end) and
        (if has("gate") then (.gate | IN("pass","fail","n-a","needs-work","ready")) else true end) and
        (if .step == "unknown" then .boundary == "session" and .agent_id == .session_id
         elif ($record | has("expected_skill")) then .step == $record.expected_skill else true end)) and
      (if .state == "accepted" then .receipt |
        type == "object" and .kind == "accepted" and
        .run_id == $record.run_id and .session_id == $record.session_id and
        .agent_id == $record.agent_id and .checkpoint_id == $record.checkpoint_id and
        (.seq | count and . > 0) and (.duplicate | type == "boolean")
       else true end)
    else true end))
  ' <<< "$RECORD" >/dev/null 2>&1
}

load_record() {
  local checkpoint="$1"
  identity_ok "$checkpoint" || { warn invalid-checkpoint; return 1; }
  RECORD_PATH="$HOOK_STATE/$checkpoint.json"
  [ -f "$RECORD_PATH" ] && [ ! -L "$RECORD_PATH" ] &&
    [ -f "$HOOK_STATE/$checkpoint.lock" ] && [ ! -L "$HOOK_STATE/$checkpoint.lock" ] || {
      warn missing-checkpoint; return 1;
    }
  exec 9<> "$HOOK_STATE/$checkpoint.lock" || { warn state-unavailable; return 1; }
  flock -x -w 2 9 || { warn checkpoint-busy; return 1; }
  RECORD="$(cat -- "$RECORD_PATH" 2>/dev/null)" || { warn state-unavailable; return 1; }
  record_valid && [ "$(jq -r .checkpoint_id <<< "$RECORD")" = "$checkpoint" ] || {
    warn invalid-correlation; return 1;
  }
  [ "$(jq -r .project <<< "$RECORD")" = "$PROJECT" ] || { warn project-mismatch; return 1; }
}

dispatch() {
  local run="${OPT[--run]-}" actor="${OPT[--agent-id]-}" boundary="${OPT[--boundary]-}"
  local session="${CLAUDE_CODE_SESSION_ID:-}" checkpoint started marker
  PROJECT="$(project_for "$PWD")" || return 0
  run_ok "$run" && identity_ok "$actor" && identity_ok "$session" || { warn missing-dispatch-identity; return; }
  case "$boundary" in session) [ "$actor" = "$session" ] || { warn session-actor-mismatch; return; } ;; subagent) ;; *) warn invalid-boundary; return ;; esac
  if [ "${OPT[--expected-skill]+present}" = present ]; then
    identity_ok "${OPT[--expected-skill]}" || { warn invalid-expected-skill; return; }
  fi
  if [ "${OPT[--parent-checkpoint-id]+present}" = present ]; then
    identity_ok "${OPT[--parent-checkpoint-id]}" || { warn invalid-parent; return; }
  fi
  case "${OPT[--span-kind]-work}" in work|waiting) ;; *) warn invalid-span-kind; return ;; esac
  started="$(clock_ms)" || { warn clock-unavailable; return; }
  [ ! -L "$HOOK_STATE" ] && mkdir -p -- "$HOOK_STATE" && chmod 700 "$HOOK_STATE" || { warn state-unavailable; return; }
  # mktemp creates a unique private lock before publishing the corresponding record.
  checkpoint="$(mktemp "$HOOK_STATE/checkpoint-XXXXXXXXXXXX.lock" 2>/dev/null)" || { warn state-unavailable; return; }
  checkpoint="${checkpoint##*/}"
  checkpoint="${checkpoint%.lock}"
  RECORD_PATH="$HOOK_STATE/$checkpoint.json"
  marker="$(jq -cnS --arg run "$run" --arg session "$session" --arg actor "$actor" --arg checkpoint "$checkpoint" \
    '{schema_version:1,run_id:$run,session_id:$session,agent_id:$actor,checkpoint_id:$checkpoint}')" || { warn state-unavailable; return; }
  RECORD="$(jq -cS --arg project "$PROJECT" --arg boundary "$boundary" --argjson start "$started" \
    --arg expected "${OPT[--expected-skill]-}" --arg parent "${OPT[--parent-checkpoint-id]-}" \
    --arg kind "${OPT[--span-kind]-work}" \
    '. + {project:$project,boundary:$boundary,span_start_ms:$start,span_kind:$kind,state:"pending"}
     + (if $expected != "" then {expected_skill:$expected} else {} end)
     + (if $parent != "" then {parent_checkpoint_id:$parent} else {} end)' <<< "$marker")" || { warn state-unavailable; return; }
  save_record || { warn state-unavailable; return; }
  printf 'ORCHESTRAIL_DISPATCH_V1 %s\n' "$marker"
}

status() {
  PROJECT="$(project_for "$PWD")" || return 0
  load_record "${OPT[--checkpoint]-}" || return
  jq -cS '{schema_version,run_id,session_id,agent_id,checkpoint_id,state} +
    (if .state == "accepted" then {receipt} else {} end)' <<< "$RECORD"
}

fallback() {
  local step="${OPT[--step]-}" outcome="${OPT[--outcome]-}"
  local -a args
  PROJECT="$(project_for "$PWD")" || return 0
  identity_ok "$step" && enums_ok "$outcome" || { warn invalid-fallback; return; }
  load_record "${OPT[--checkpoint]-}" || return
  case "$(jq -r .state <<< "$RECORD")" in
    pending) ;;
    delivering) warn acceptance-uncertain; return ;;
    *) return ;;
  esac
  args=(step --run "$(jq -r .run_id <<< "$RECORD")" --step "$step" --outcome "$outcome" --note approximate)
  if [ "${OPT[--tests]+present}" = present ]; then args+=(--tests "${OPT[--tests]}"); fi
  if [ "${OPT[--gate]+present}" = present ]; then args+=(--gate "${OPT[--gate]}"); fi
  RECORD="$(jq -cS '.state="fallback"' <<< "$RECORD")" || { warn state-unavailable; return; }
  save_record || { warn state-unavailable; return; }
  # The legacy interface has no receipt. A claim is never retried as another route.
  bash "$HOOK_HELPER" "${args[@]}" >/dev/null 2>&1 || true
  RECORD="$(jq -cS '.state="fallback-attempted"' <<< "$RECORD")" || { warn state-unavailable; return; }
  save_record || { warn state-unavailable; return; }
}

# Find exactly one unindented report outside Markdown fences. Canonical raw JSON
# equality rejects duplicate keys as well as whitespace, unknown keys and aliases.
parse_report() {
  local message="$1" line fence='' fence_length=0 run suffix
  local fence_pattern='^ {0,3}(`{3,}|~{3,})(.*)$'
  local prefix='ORCHESTRAIL_REPORT_V1 ' found=0 raw canonical
  # CommonMark line separators do not belong to the canonical marker bytes.
  message="${message//$'\r\n'/$'\n'}"
  message="${message//$'\r'/$'\n'}"
  while IFS= read -r line || [ -n "$line" ]; do
    if [[ "$line" =~ $fence_pattern ]]; then
      run="${BASH_REMATCH[1]}"
      suffix="${BASH_REMATCH[2]}"
      if [ -z "$fence" ]; then
        # Backtick opener info cannot contain another backtick. Tilde info
        # accepts either delimiter as ordinary text after the opening run.
        if [ "${run:0:1}" != '`' ] || [[ "$suffix" != *'`'* ]]; then
          fence="${run:0:1}"
          fence_length="${#run}"
        fi
      elif [ "${run:0:1}" = "$fence" ] && [ "${#run}" -ge "$fence_length" ] &&
           [[ "$suffix" =~ ^[[:blank:]]*$ ]]; then
        fence=''
        fence_length=0
      fi
      continue
    fi
    if [ -z "$fence" ] && [[ "$line" = "$prefix"* ]]; then
      found=$((found + 1))
      [ "${#line}" -le 4096 ] || return 1
      raw="${line#"$prefix"}"
    fi
  done <<< "$message"
  [ "$found" -eq 1 ] || return 1
  canonical_integer_tokens "$raw" || return 1
  canonical="$(jq -cS -e '
    def id: type == "string" and test("^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\z");
    select(type == "object") |
    select((keys - ["schema_version","run_id","session_id","agent_id","checkpoint_id","outcome","tests","gate"]) == []) |
    select(.schema_version == 1) |
    select(.run_id | type == "string" and test("^[a-f0-9]{8}\\z")) |
    select([.session_id,.agent_id,.checkpoint_id] | all(.[]; id)) |
    select(.outcome | IN("ok","blocked","failed","skipped","deferred")) |
    select(if has("tests") then (.tests | IN("red","green","n-a","failed","not-run","pinned")) else true end) |
    select(if has("gate") then (.gate | IN("pass","fail","n-a","needs-work","ready")) else true end)
  ' <<< "$raw" 2>/dev/null)" || return 1
  [ "$raw" = "$canonical" ] || return 1
  REPORT="$canonical"
}

# Parse a bounded tail as native JSONL records. Only direct user input text can
# bind the dispatch; only subsequent assistant tool_use objects establish skills.
transcript_skill() {
  local path="$1" dispatch="$2" size evidence
  [ -f "$path" ] && [ -r "$path" ] || return 1
  size="$(stat -c %s -- "$path" 2>/dev/null)" || return 1
  [[ "$size" =~ ^[0-9]+$ ]] || return 1
  evidence="$(tail -c 16777216 -- "$path" | {
    if [ "$size" -gt 16777216 ]; then IFS= read -r _ || true; fi
    cat
  } | jq -Rsc -e --arg dispatch "$dispatch" '
    def input_text:
      select(.type == "user" and (.message | type == "object") and (.message.role // "user") == "user") |
      .message.content | if type == "string" then . elif type == "array" then .[] | select(.type == "text") | .text | select(type == "string") else empty end;
    split("\n") | map(select(length > 0) | fromjson) as $rows |
    [$rows | to_entries[] | select([.value | input_text | split("\n")[] | select(. == $dispatch)] | length > 0) | .key] as $indices |
    if ($indices | length) != 1 then error("dispatch-input") else
      [$rows[($indices[0]+1):][] |
       select(.type == "assistant" and (.message.role // "assistant") == "assistant") |
       .message.content | select(type == "array") | .[] |
       select(.type == "tool_use" and .name == "Skill")] as $calls |
      if any($calls[]; (.id | type != "string") or (.id | length == 0) or
             (.input.skill | type != "string") or
             (.input.skill | test("^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\z") | not)) then error("invalid-invocation") else
        ($calls | sort_by(.id) | group_by(.id)) as $groups |
        if any($groups[]; (map(.input) | unique | length) != 1) then error("conflicting-invocation") else
          [$groups[] | .[0].input.skill] |
          if length > 1 then error("ambiguous-invocation") elif length == 1 then {step:.[0]} else {step:"unknown"} end
        end
      end
    end
  ' 2>/dev/null)" || return 1
  SKILL="$(jq -r .step <<< "$evidence")" || return 1
  identity_ok "$SKILL"
}

receipt_valid() {
  canonical_integer_tokens "$1" || return 1
  jq -s -e --argjson record "$RECORD" '
    length == 1 and (.[0] |
      type == "object" and .kind == "accepted" and
      .run_id == $record.run_id and .session_id == $record.session_id and
      .agent_id == $record.agent_id and .checkpoint_id == $record.checkpoint_id and
      (.seq | type == "number" and floor == . and . > 0 and . <= 9007199254740991) and
      (.duplicate | type == "boolean"))
  ' <<< "$1" >/dev/null 2>&1
}

forward_payload() {
  local payload receipt key value
  local -a args=(step)
  payload="$(jq -cS .payload <<< "$RECORD")" || { warn invalid-correlation; return; }
  for key in run_id step outcome session_id agent_id checkpoint_id span_start_ms span_end_ms timing_source boundary span_kind parent_checkpoint_id tests gate; do
    if jq -e --arg key "$key" 'has($key)' <<< "$payload" >/dev/null; then
      value="$(jq -r --arg key "$key" '.[$key]' <<< "$payload")" || { warn invalid-correlation; return; }
      case "$key" in run_id) args+=(--run "$value") ;; *) args+=("--${key//_/-}" "$value") ;; esac
    fi
  done
  receipt="$(bash "$HOOK_HELPER" "${args[@]}" 2>/dev/null)" || true
  receipt_valid "$receipt" || { warn acceptance-uncertain; return; }
  RECORD="$(jq -cS --argjson receipt "$receipt" '.state="accepted" | .receipt=$receipt' <<< "$RECORD")" || { warn state-unavailable; return; }
  save_record || { warn acceptance-uncertain; return; }
}

completion() {
  local raw kind session path message dispatch state ended payload native_agent
  raw=''
  # read preserves trailing newlines. A NUL terminates early and is rejected;
  # command substitution would silently discard both kinds of bytes.
  if IFS= read -r -d '' -n 1048577 raw; then
    if [ "${#raw}" -ge 1048577 ]; then warn input-too-large; else warn malformed-input; fi
    return
  fi
  [ "${#raw}" -le 1048576 ] || { warn input-too-large; return; }
  jq -s -e 'length == 1 and (.[0] | type == "object")' <<< "$raw" >/dev/null 2>&1 || { warn malformed-input; return; }
  # Only cwd is inspected before the registry gate. Unregistered native events
  # exit without opening any correlation file, transcript or producer state.
  path="$(jq -er '.cwd | select(type == "string" and length > 0 and (test("[\u0000\r\n]") | not))' <<< "$raw" 2>/dev/null)" || { warn invalid-native-input; return; }
  PROJECT="$(project_for "$path")" || return 0
  jq -e '
    def text: type == "string" and length > 0;
    ([.hook_event_name,.session_id,.cwd,.transcript_path,.last_assistant_message] | all(.[]; text)) and
    (.session_id | test("^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\z")) and
    (.transcript_path | test("[\u0000\r\n]") | not) and
    (.last_assistant_message | contains("\u0000") | not)
  ' <<< "$raw" >/dev/null 2>&1 || { warn invalid-native-input; return; }
  kind="$(jq -r .hook_event_name <<< "$raw")"
  session="$(jq -r .session_id <<< "$raw")"
  case "$kind" in
    Stop) kind=session; native_agent="$session"; path="$(jq -r .transcript_path <<< "$raw")" ;;
    SubagentStop)
      jq -e '[.agent_id,.agent_transcript_path] | all(.[]; type == "string" and length > 0 and (test("[\u0000\r\n]") | not))' <<< "$raw" >/dev/null || { warn invalid-native-input; return; }
      kind=subagent; native_agent="$(jq -r .agent_id <<< "$raw")"; path="$(jq -r .agent_transcript_path <<< "$raw")" ;;
    *) warn invalid-native-event; return ;;
  esac
  message="$(jq -r .last_assistant_message <<< "$raw")"
  parse_report "$message" || { warn invalid-report-marker; return; }
  [ "$(jq -r .session_id <<< "$REPORT")" = "$session" ] || { warn session-mismatch; return; }
  load_record "$(jq -r .checkpoint_id <<< "$REPORT")" || return
  jq -e --argjson report "$REPORT" --arg boundary "$kind" '
    .boundary == $boundary and
    .run_id == $report.run_id and .session_id == $report.session_id and
    .agent_id == $report.agent_id and .checkpoint_id == $report.checkpoint_id
  ' <<< "$RECORD" >/dev/null || { warn correlation-mismatch; return; }
  state="$(jq -r .state <<< "$RECORD")"
  case "$state" in
    fallback|fallback-attempted) return ;;
    delivering|accepted)
      # First validated evidence is durable. A rotated transcript cannot prevent
      # retry, while a contradictory report or different native actor cannot
      # change or forward the already frozen completion.
      jq -e --arg native "$native_agent" --argjson report "$REPORT" '
        def result_fields: {outcome} + (if has("tests") then {tests} else {} end) +
          (if has("gate") then {gate} else {} end);
        .native_agent_id == $native and (.payload | result_fields) == ($report | result_fields)
      ' <<< "$RECORD" >/dev/null || { warn conflicting-delivery; return; }
      if [ "$state" = delivering ]; then forward_payload; fi
      return ;;
  esac
  dispatch="ORCHESTRAIL_DISPATCH_V1 $(jq -cS '{agent_id,checkpoint_id,run_id,schema_version,session_id}' <<< "$RECORD")"
  transcript_skill "$path" "$dispatch" || { warn transcript-evidence; return; }
  if [ "$SKILL" = unknown ]; then
    [ "$kind" = session ] && [ "$(jq -r .agent_id <<< "$RECORD")" = "$session" ] || { warn missing-skill; return; }
  elif jq -e 'has("expected_skill")' <<< "$RECORD" >/dev/null; then
    [ "$(jq -r .expected_skill <<< "$RECORD")" = "$SKILL" ] || { warn skill-mismatch; return; }
  fi
  if [ "$state" = pending ]; then
    ended="$(clock_ms)" || { warn clock-unavailable; return; }
    [ "$ended" -ge "$(jq -r .span_start_ms <<< "$RECORD")" ] || { warn clock-reversed; return; }
    payload="$(jq -cS --argjson report "$REPORT" --arg step "$SKILL" --argjson ended "$ended" '
      {run_id,session_id,agent_id,checkpoint_id,span_start_ms,boundary,span_kind} +
      {step:$step,outcome:$report.outcome,span_end_ms:$ended,timing_source:"hook"} +
      (if has("parent_checkpoint_id") then {parent_checkpoint_id} else {} end) +
      ($report | {tests,gate} | with_entries(select(.value != null)))
    ' <<< "$RECORD")" || { warn invalid-correlation; return; }
    RECORD="$(jq -cS --argjson payload "$payload" --arg native "$native_agent" \
      '.state="delivering" | .payload=$payload | .native_agent_id=$native' <<< "$RECORD")" || { warn state-unavailable; return; }
    save_record || { warn state-unavailable; return; }
  fi
  forward_payload
}

main() {
  local dependency mode="${1:-}"
  for dependency in jq flock; do
    command -v "$dependency" >/dev/null 2>&1 || { warn dependency-unavailable; return; }
  done
  case "$mode" in
    '') completion ;;
    dispatch|status|fallback)
      shift
      options "$mode" "$@" || { warn invalid-options; return; }
      "$mode" ;;
    *) warn invalid-command ;;
  esac
}
main "$@" 2>/dev/null || true
exit 0
