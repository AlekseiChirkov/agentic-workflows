---
description: Analyse the run log across projects and report what to change in the workflows themselves — the only reader of the log store
---

Invocation: `/retro [--since <YYYY-MM-DD>] [--pipeline <name>] [--project <path>] [--limit <N>]`
Examples:
- `/retro` — everything in the store
- `/retro --since 2026-08-01 --pipeline spec-run` — one pipeline, one month
- `/retro --project ~/projects/acme-platform` — one repository

---

## Why this exists

`progress.md` is a narrative and `state.md` is resumable state; neither can answer "is the
pipeline getting better, and where does it hurt?" across projects. The run log can, because
it is structured, uniform, and cross-project. This workflow is its **only** reader — nothing
in a live run may consult it.

The output is a judgement about **the workflows**, not about the work. "Task 04 was slow" is
not a finding. "Four of the last nine runs stopped at the same gate, all for the same missing
input" is.

---

## Guard

1. Resolve the store: `$ORCHESTRAIL_LOG_ROOT`, else the script-relative store reported by `bash <workflow-source>/scripts/log-step.sh path`. If absent →
   **stop**: "No run log at `<path>`. Pipelines write it via `scripts/log-step.sh`; nothing has been
   recorded yet."
2. Count run files after filters. Fewer than **5** → report the count and warn: "Below 5 runs
   the numbers below are anecdotes, not signal." Continue, but every finding must be marked
   `weak evidence`.

---

## Step 1 — Load

Resolve `HELPER` to `<workflow-source>/scripts/log-step.sh` and `STORE` to the store
from the guard. Set `SINCE`, `PIPELINE`, `PROJECT`, and `LIMIT` from the invocation,
using empty strings for absent filters. Expand `~` in the requested project path;
compare the resulting project and pipeline strings exactly. `--since` includes the
start date. Apply all filters before taking the newest `N` filenames for `--limit`;
without a limit select all matches. Require a positive integer limit and a valid
`YYYY-MM-DD` date when supplied.

Use the following loader with Bash and `jq`. It invokes `lint --all` once, intersects
violations by exact file path, and retains physical line numbers. Its stdout is a JSON
working dataset: save it to a temporary file, then aggregate with `jq`; never paste
raw records into the report or the conversation. Temporary snapshots are removed on
exit. This reads the store without repairing logs or creating active metadata.

```bash
# Retrospective corpus loader.
set -euo pipefail
: "${STORE:?Set STORE to the resolved log store}"
: "${HELPER:?Set HELPER to scripts/log-step.sh}"
SINCE=${SINCE:-} PIPELINE=${PIPELINE:-} PROJECT=${PROJECT:-} LIMIT=${LIMIT:-}
if ! command -v jq >/dev/null 2>&1; then
  ORCHESTRAIL_LOG_ROOT="$STORE" bash "$HELPER" lint --all >/dev/null 2>&1 || true
  printf '%s\n' '{"status":"unavailable","limitations":["jq unavailable; corpus and metrics not measurable"]}'
  exit 0
fi
if [[ -n $LIMIT && ! $LIMIT =~ ^[1-9][0-9]*$ ]]; then
  printf '%s\n' 'Invalid --limit: use a positive integer' >&2; exit 1
fi
if [[ -n $SINCE ]] && { [[ ! $SINCE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] ||
  ! jq -en --arg since "$SINCE" '($since|strptime("%Y-%m-%d")|mktime|strftime("%Y-%m-%d")) == $since' >/dev/null 2>&1; }; then
  printf '%s\n' 'Invalid --since: use a valid YYYY-MM-DD' >&2; exit 1
fi
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
snapshot() {
  local file
  shopt -s nullglob
  for file in "$STORE"/runs/*.jsonl; do
    if jq -Rs --arg file "$file" '
      {file:$file, readable:true, raw:., rows:
        (split("\n") | if last == "" then .[:-1] else . end
         | to_entries | map({line:(.key+1), record:(try (.value|fromjson) catch null)}))}
    ' "$file" > "$scratch/one" 2>/dev/null; then
      cat "$scratch/one"
    else
      jq -n --arg file "$file" '{file:$file,readable:false,rows:[]}'
    fi
  done | jq -s 'sort_by(.file)'
}
snapshot > "$scratch/before"
lint_exit=0
ORCHESTRAIL_LOG_ROOT="$STORE" bash "$HELPER" lint --all > "$scratch/lint" 2> "$scratch/warnings" || lint_exit=$?
snapshot > "$scratch/after"
# A missing/broken response is unavailable, never a clean result.
if ! jq -s 'if (map(select(.kind == "summary"))|length) == 1
                 and last.kind == "summary" then . else error("missing summary") end' \
  "$scratch/lint" > "$scratch/diagnostics" 2>/dev/null; then
  printf '%s\n' '[{"kind":"summary","status":"unavailable","files":0,"lines":0,"invalid_lines":0,"violations":0}]' > "$scratch/diagnostics"
fi
jq -n --slurpfile before "$scratch/before" --slurpfile after "$scratch/after" \
  --slurpfile lint "$scratch/diagnostics" --arg since "$SINCE" --arg pipeline "$PIPELINE" \
  --arg project "$PROJECT" --arg limit "$LIMIT" --argjson lint_exit "$lint_exit" '
  $before[0] as $all | $lint[0] as $diagnostics | $diagnostics[-1] as $summary
  | ($diagnostics | map(select(.kind == "violation"))) as $global_bad
  | ($all | map(. as $run
      | ([.rows[].record | objects | select(.event == "run-start")][0] // {}) as $start
      | select(($since == "" or (($start.ts|type) == "string" and $start.ts[0:10] >= $since))
           and ($pipeline == "" or $start.pipeline == $pipeline)
           and ($project == "" or $start.project == $project)))
      | sort_by(.file) | reverse
      | if $limit == "" then . else .[:($limit|tonumber)] end) as $selected
  | ($selected | map(.file)) as $files
  | ($global_bad | map(select(.file as $file | $files | index($file)))) as $bad
  | ($bad | unique_by([.file,.line])) as $invalid
  | ($lint_exit == 0 and $summary.status == "ok" and $before == $after
       and all($all[]; .readable)
       and $summary.files == ($all|length)
       and $summary.lines == ([$all[].rows|length]|add // 0)
       and $summary.violations == ($global_bad|length)
       and $summary.invalid_lines == ($global_bad|unique_by([.file,.line])|length)) as $verified
  | (if $verified then "ok"
     elif $summary.status == "unavailable" or $lint_exit != 0 then "unavailable"
     else "partial" end) as $status
  | (if $verified then
       [$selected[] | .file as $file | .rows[]
        | select(.line as $line | all($invalid[]; .file != $file or .line != $line))
        | select(.record|type == "object") | {file:$file,line,record}]
     else [] end) as $usable
  | [$selected[] | .file as $file
      | ([$invalid[] | select(.file == $file)]|length) as $excluded
      | select($excluded > 0 or ($verified|not))
      | {file:$file,invalid_lines:$excluded,reason:
          (if $verified then "incomplete telemetry: invalid lines excluded"
           else "incomplete telemetry: lint coverage unverified" end)}] as $incomplete
  | {status:$status, files:$files, total_runs:($files|length),
     weak_evidence:(($files|length) < 5),
     examined_lines:(if $verified then ([$selected[].rows|length]|add // 0) else null end),
     invalid_lines:($invalid|length), invalid_lines_exact:$verified,
     affected_runs:($incomplete|length), incomplete_runs:$incomplete,
     violations:($bad | group_by([.field,.code]) | map({field:.[0].field,code:.[0].code,count:length})),
     examples:($invalid | sort_by(.file,.line) | .[:5] | map({file,line})),
     usable_records:$usable,
     abandoned_runs:([$selected[] | select(.readable)
       | select(any(.rows[].record | objects; .event == "run-end")|not)]|length),
     unusable_closes:([$selected[] | .file as $file
       | select(any(.rows[].record | objects; .event == "run-end"))
       | select(any($usable[]; .file == $file and .record.event == "run-end")|not)]|length),
     unknown_close_runs:([$selected[]|select(.readable|not)]|length),
     selection_unverified_files:([$all[]
       | ([.rows[].record | objects | select(.event == "run-start")][0] // {}) as $start
       | select(($since != "" and ($start.ts|type) != "string")
           or ($pipeline != "" and ($start.pipeline|type) != "string")
           or ($project != "" and ($start.project|type) != "string"))]|length),
     limitations:(if $verified then [] else
       ["Lint coverage is incomplete or the store changed: examined selected lines are not measurable; known invalid counts are lower bounds; no unverified records enter metrics"] end)}
'
```

Do not treat a missing violation as proof that a line was checked. The linter reports
aggregate examined counts, with no per-file clean-line coverage for `partial` results.
Consequently this loader excludes **all** selected records from metrics unless an `ok`
summary covers the unchanged complete snapshot. Preserve known selected violations even
when coverage is partial. Report `examined_lines: null` as **not measurable**, never zero;
label invalid-line and violation counts as **known lower bounds** in that case. A failure
outside the selected files may conservatively prevent metrics for the selected corpus;
state that limitation and rerun against a stable accessible store when possible.

If `jq` is missing, report lint **unavailable** and the corpus/metrics **not measurable**;
do not continue with guessed counts. If filters cannot be evaluated for files without a
readable start record, report `selection_unverified_files` and disclose that selection
is incomplete; selected-run counts and diagnostic totals are lower bounds for that
request. If the runs directory cannot be listed, its corpus count is **not measurable**,
even when the glob returned no paths. An unreadable selected file has unknown close status; it is not proof of
abandonment. A parseable physical `event: run-end` counts as present even when its fields
are invalid: report an **unusable close**, never abandonment. With incomplete coverage a
present close is also unverified and unusable. Keep physical close counts separate from
metrics over usable records; disclose the readable-run denominator and unknown closes.

Report the corpus before analysing it: total selected runs, date range, pipelines and
projects from usable starts (or **not measurable**), lint status, examined event lines,
known invalid lines, affected runs labeled **incomplete telemetry**, violation totals by
field/code, and up to five JSON-escaped `file:line` examples without raw field values.
Include abandoned runs, unusable closes, unknown close status, selection limitations,
and the below-five-runs warning. Do not copy `raw`, record bodies, notes, or blockers
into diagnostic examples. Escape paths when rendering them; control characters must not
create new report lines. Retain all run counts as corpus facts, never as implicit metric
denominators.

---

## Step 2 — Compute

Compute every metric below. A metric that cannot be computed because the field is absent is
reported as **not measurable**, with the reason — never estimated, and never quietly dropped.

Use **only** `usable_records` for every metric numerator, denominator, grouping key,
duration, counter, and comparison window. Never rescan the physical JSONL files to fill
missing metric values or normalize an excluded alias. Physical close presence in Corpus
is the explicit exception: it describes file completeness, not a validated measurement.
When `status` is not `ok`, keep every Step 2 row and label it **not measurable — lint
coverage unverified**. A zero denominator is **not measurable**, not a zero rate.

For each value show `n` (usable observations), the eligible run/step count, excluded
invalid/unverified lines, and missing-field observations. Split by pipeline/project
using usable record metadata only. Apply these denominator rules to all tables below:

- Durations and percentiles use usable records with an explicit numeric `duration_s`,
  separately for closes and steps. State the percentile convention; do not infer a missing
  close duration by summing steps. A valid close in an affected run still supplies its own
  duration, with the incomplete-telemetry label.
- Step counts use usable steps. Per-run means divide by runs with usable starts and
  observed steps; label affected counts as observed subtotals. A clean readable run with
  a usable start and no physical steps may supply an observed zero; an invalid step is
  never evidence of zero. Do not present incomplete subtotals as exact full-run totals.
- Each optional counter (`stops`, `escalations`, `decisions`, `questions`, `fix_tasks`,
  `amendments`) has its own measured-step set: usable steps where that field is present.
  Sum those values, including explicit zeros. For a per-run mean/rate, divide by distinct
  runs contributing that counter, using usable start metadata for grouping. Missing
  counters do not contribute a zero or a denominator run. State how many measured steps
  supplied each observed subtotal; claim a full-run total only if all its physical steps
  are usable and all carry that counter. Stop-producing-step rankings use this same
  measured set, including its zero observations in comparisons.
- First-pass rate uses runs with usable starts and closes, no excluded/unverified lines,
  and explicit `fix_tasks` on every physical step. Its numerator requires a completed
  close, no failed step, and zero summed fix tasks; its denominator is the number of runs
  meeting the observability requirements, including observed stopped/failed closes.
  Missing fix-task counts or unusable closes cannot imply success or failure.
- Gate failure rate groups usable steps with a present applicable `gate` (exclude `n-a`)
  by step; numerator is `fail` or `needs-work`, denominator is these applicable gate
  observations. Report the observed status distribution so `ready` is visible.
- Test distribution and `n-a` share use usable steps with `tests` present. Promotion rate
  uses usable quick-flow steps with `promoted` present; numerator is `yes`. Missing
  optional fields enter neither side of these ratios. Compare time windows only with
  the same eligibility rules and disclose each window’s exclusions and denominator.
- Blocked/failure concentration uses usable steps with their required outcome; give the
  usable-step denominator per group. Describe causes only where a usable record carries
  `blocker`, and disclose missing causes. Repeated-task counts use usable starts with an
  explicit nonempty task; absent task identifiers are not a shared task group.
- Abandonment uses the physical close classification from Corpus. Its denominator is
  readable selected run files, with unknown/unreadable closes reported separately.
  Present invalid or unverified closes remain unusable closes even when no usable close
  reaches metric inputs. Never divide this count by the number of usable close records.

For example, after saving the loader stdout to `$RETRO_DATA` in a temporary directory
outside the store, run this aggregation to check the observation denominators. Print
aggregates like these and the corpus object with `usable_records` removed; keep the
working dataset out of model context. These examples return null when no measurement
exists, rather than inventing a zero.

```bash
# Retrospective metric inputs.
jq '
  [.usable_records[].record | select(.event == "step")] as $steps
  | [$steps[] | select(has("stops"))] as $stops
  | [$steps[] | select(has("tests"))] as $tests
  | {stops:{sum:(if ($stops|length)>0 then ([$stops[].stops]|add) else null end),
            observations:($stops|length)},
     tests:{na:([$tests[]|select(.tests == "n-a")]|length), observations:($tests|length),
            na_share:(if ($tests|length)>0 then
              ([$tests[]|select(.tests == "n-a")]|length)/($tests|length) else null end)},
     close_durations:[.usable_records[].record
       | select(.event == "run-end" and has("duration_s")) | .duration_s]}
' "$RETRO_DATA"
```

**Throughput and cost**

| Metric | From |
|---|---|
| Median and p90 wall-clock per run, per pipeline | `run-end.duration_s` |
| Median duration per step name | `step.duration_s` grouped by `step` |
| The five slowest steps by median | same |
| Steps per run, per pipeline | count of `event: step` |

**Autonomy** — the pipelines claim to run unattended; this is where the claim is tested.

| Metric | From |
|---|---|
| Human stops per run, per pipeline | sum of `stops` |
| Which steps produce the stops | `stops > 0` grouped by `step` |
| Escalation rate | measured `escalations` / contributing usable runs |
| Autonomous decisions per run | sum of `decisions` |
| Questions asked per run | sum of `questions` |

**Quality**

| Metric | From |
|---|---|
| First-pass rate — runs completing with no `failed` step and no fix-tasks | `outcome`, `fix_tasks` |
| Fix-tasks per run and per project | sum of `fix_tasks` |
| Gate failure rate per gate | `gate` grouped by `step` |
| Test-level distribution | `tests` values across steps |
| `n-a` share — how often the TDD gate returned `none` | usable `tests == "n-a"` / usable steps with `tests` |
| quick→full promotion rate | `promoted == "yes"` |
| Amendments per run | sum of `amendments` |

**Reliability**

| Metric | From |
|---|---|
| Abandoned runs — no `run-end` | runs missing the closing line |
| Blocked steps, and what blocked them | `outcome == "blocked"`, `blocker` |
| Repeated runs of the same task | runs grouped by `task` with count > 1 |
| Failure concentration | `outcome != "ok"` grouped by `step` |

---

## Step 3 — Find what to change

Turn numbers into candidate changes. A finding qualifies only when it names a **specific
file** in this repository and the change to make. Three or more occurrences, or a clear
majority of a small corpus, or it is `weak evidence`.

Work through these questions explicitly — for each, state what you checked, not only what you
found:

1. **Which step consumes the most time relative to its value?** A step that is consistently
   slow and never produces a finding, a decision, or a gate result is ceremony. Name it.
2. **Where does autonomy actually break?** Group `stops` by step. A step that stops in most
   runs is either mis-specified or genuinely needs a human — and if the latter, the workflow
   should *declare* it as a stop rather than surprising the operator each time.
3. **Which gate fails most, and is the gate wrong or is the work wrong?** A gate failing
   nearly always is a gate mis-calibrated; a gate never failing is a gate not doing anything.
4. **Is the TDD gate being honoured?** A rising `n-a` share is the leading indicator of the
   test-first rule decaying into test-after. Compare against the previous window.
5. **Is the quick tier calibrated?** A high promotion rate means the gate admits work it
   should not; a promotion rate of zero across many quick runs means the gate is so strict
   the tier is unused.
6. **What blocks runs, repeatedly?** Recurring `blocker` text across projects is usually a
   missing prerequisite the workflows should check in preflight instead of discovering late.
7. **Which tasks needed more than one run?** Repeated runs of one task mean the resume path
   or the state format is failing, and that is a contract defect.
8. **What is not measurable that should be?** A question you could not answer because no
   field carries it is a finding against `run-log → ## Field vocabulary`. This is the loop
   that keeps the log useful.

---

## Step 4 — Report

Write `retro-<YYYY-MM-DD>.md` in the log store root (never in a project):

```markdown
# Retro — <date range>

## Corpus
<selected runs, usable date range/pipelines/projects, lint status (ok/partial/unavailable),
examined event lines or not measurable, known invalid lines (exact/lower bound),
affected runs labeled incomplete telemetry, violations by field/code,
up to five escaped file:line examples without raw values,
physical abandoned/unusable/unknown closes and their readable-run denominator,
selection/coverage limitations; the warning if below 5 runs>

## Metrics
<the tables from Step 2, values filled with usable observation/run denominators,
invalid/unverified exclusions, missing-field counts, and incomplete-run effects;
not-measurable rows kept with their reason>

## Findings
Ranked by expected improvement, worst first.

### R<N> — <one-line title>  [strong | weak evidence]
**Evidence:** <the numbers, with the run count they rest on>
**Diagnosis:** <what in the workflow produces this>
**Change:** <the specific file and the specific edit>
**Cost of not doing it:** <what continues to happen>

## What is working
<Metrics that improved or are healthy. Named explicitly so the next retro does not
"fix" them.>

## Not measurable
<Questions the log cannot answer, and the field that would answer each.>
```

Then report to the user: the corpus including lint coverage and exclusions, the top three
findings (or fewer when supported), and the report path.

**Never** apply a finding automatically. This workflow analyses and recommends; changing a
workflow is a deliberate act, and a change made on three data points that turns out wrong is
harder to detect than the problem it replaced.

Then **stop**.

---

## Honesty rules

- **A number with a small denominator is labelled.** "50% of runs" over four runs is two
  runs; say so.
- **Correlation is not diagnosis.** If a step is slow, say it is slow; claim a cause only
  when the log carries it (`blocker`, `outcome`, `gate`).
- **Do not manufacture findings to fill the section.** A window with nothing worth changing
  is a legitimate and useful result — say so in one line.
- **The log records the process, not the work.** Never infer code quality from it.
