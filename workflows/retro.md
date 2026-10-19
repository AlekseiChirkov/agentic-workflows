---
description: Analyse the run log across projects and report what to change in the workflows themselves — the only reader of the log store
---

Invocation: `/retro [--since <YYYY-MM-DD>] [--pipeline <name>] [--project <path>] [--limit <N>]`
Examples:
- `/retro` — everything in the store
- `/retro --since 2026-08-01 --pipeline spec-run` — one pipeline, one month
- `/retro --project ~/Documents/projects/alterra/invest_ai` — one repository

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

1. Resolve the store: `$AGENTIC_LOG_ROOT`, else `~/Documents/projects/alterra/agentic_workflows/logs`. If absent →
   **stop**: "No run log at `<path>`. Pipelines write it via `log-step.sh`; nothing has been
   recorded yet."
2. Count run files after filters. Fewer than **5** → report the count and warn: "Below 5 runs
   the numbers below are anecdotes, not signal." Continue, but every finding must be marked
   `weak evidence`.

---

## Step 1 — Load

Read `<store>/runs/*.jsonl`, applying the filters. Each line is one JSON object; the
vocabulary is `run-log → ## Field vocabulary`. Use `jq` for aggregation rather than reading
files into context — the store grows without bound and the point of the format is that it
does not need an LLM to be counted.

```bash
cat <store>/runs/*.jsonl | jq -s '...'
```

Report the corpus before analysing it: run count, date range, pipelines present, projects
present, and how many runs have no `run-end` line (abandoned).

---

## Step 2 — Compute

Compute every metric below. A metric that cannot be computed because the field is absent is
reported as **not measurable**, with the reason — never estimated, and never quietly dropped.

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
| Escalation rate | sum of `escalations` / runs |
| Autonomous decisions per run | sum of `decisions` |
| Questions asked per run | sum of `questions` |

**Quality**

| Metric | From |
|---|---|
| First-pass rate — runs completing with no `failed` step and no fix-tasks | `outcome`, `fix_tasks` |
| Fix-tasks per run and per project | sum of `fix_tasks` |
| Gate failure rate per gate | `gate` grouped by `step` |
| Test-level distribution | `tests` values across steps |
| `n-a` share — how often the TDD gate returned `none` | `tests == "n-a"` / total |
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
<runs, pipelines, projects, abandoned count; the warning if below 5 runs>

## Metrics
<the tables from Step 2, values filled, not-measurable rows kept with their reason>

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

Then report to the user: the corpus, the top three findings, and the report path.

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
