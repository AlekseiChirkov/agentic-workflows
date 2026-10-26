# Repository scripts

All executable shell helpers live in this directory. Run project setup helpers from the
target project or umbrella directory. `sync.sh` and setup helpers resolve this repository
root from the parent of `scripts/`, unless `ORCHESTRAIL_HOME` selects another checkout.
`sync.sh --from` takes precedence over `ORCHESTRAIL_HOME`.

| Script | Purpose |
|---|---|
| `sync.sh` | Validate and deploy workflows, rules, and principles to supported coding assistants. |
| `setup-new-project.sh` | Initialize one consumer project. |
| `setup-umbrella.sh` | Initialize shared context for a multi-repository project. |
| `setup-all-repos.sh` | Initialize service repositories under an umbrella. |
| `link-skills.sh` | Link global Claude skills into a project that has local skills. Run from that project. |
| `log-step.sh` | Append pipeline run and step events to the local log store. |
| `install-hooks.sh` | Install or uninstall owned user hook entries with the adjacent standard-library Python engine. |
| `run-log-timing.sh` | Analyze only explicit run files with exact millisecond interval and coverage results. |
| `validate-contracts.sh` | Check repository-wide workflow contracts. |
| `validate-task.sh` | Validate one task directory passed as an argument. |

## Exact run timing

Run `bash scripts/run-log-timing.sh [--] FILE...` from the source checkout, or use
`-h`/`--help`. The small Bash launcher requires Python 3.11 or newer and jq, and
loads the adjacent source-only `run-log-timing.py`. It installs no packages or scripts
into the user's home. Producer writes and hooks keep their existing dependencies.

The helper copies only explicit canonical paths into a private temporary snapshot,
checks unchanged bytes and inventory around this checkout's complete producer lint,
and removes the snapshot afterward. Repeated paths collapse in caller order; distinct
files claiming one run are unavailable. It never discovers a log store or reads active
correlation metadata. Missing dependencies, invalid inputs or unverified checks produce
one versioned unavailable JSON result and exit zero.

Output has `schema_version`, `status`, `coverage`, `runs` and safe `diagnostics`.
Unavailable corpus data uses `runs:null`; an unavailable run uses `metrics:null`.
Coverage counts distinguish exact examined LF lines from inexact known violations.
Run metrics, spans, workers and named steps expose decimal-string milliseconds;
ratios contain exact `numerator_ms` and `denominator_ms` strings. Use Python integers
for arithmetic. Do not convert these totals through jq numeric operations.

Observed coverage unions work and explicit waiting. Gaps are unobserved time;
waiting is never inferred. Exclusive spans subtract every direct child, including
waiting. Invalid dependency components retain raw eligible coverage while disclosing
unavailable exclusive totals; valid disconnected roots remain partial evidence.
Same-actor checkpoint overlap invalidates its additive worker total while preserving
unions and overlap between distinct actors. Span time measures elapsed activity,
never CPU time. Legacy steps remain approximate and receive no synthetic intervals.
See [the retrospective workflow](../workflows/retro.md) for denominators and reporting.
