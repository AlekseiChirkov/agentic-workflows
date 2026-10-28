---
description: Discovery Step 2.5 — Recommend models from an optional local catalog using current capabilities and independent quality evidence
---

Invocation: `/pd-select-model <path-to-atomic-description | task-directory> [--refresh]`
Called by: manually after `/pd-decompose`, or `/spec-run` Step 2. Optional in
`/phase-discovery`; never edit caller wiring during selection.

| Mode | Input | Output |
|---|---|---|
| Single | Existing leaf description | Chat recommendation; no plan writes |
| Bulk | Task directory containing `plan.md` | Chat recommendations and explicit optional model-column updates |

Resolve task paths first: a leaf description's grandparent is its task directory;
composite children are siblings there. Reject other input shapes. Only `--refresh`
authorizes research and catalog replacement; routine selection is offline.

## Guard

1. Read task `state.md`: require Task Analysis, complete Decomposition and a nonempty
   `plan.md → ## Subtasks` table. Otherwise **stop**: run `/pd-analyze` and
   `/pd-decompose`. Quick flow has no leaves and does not use this command.
2. Single: require the leaf ID in the plan; reject composite containers and select
   their children instead. Bulk: require every non-composite description.
3. Before bulk replacement, inspect legacy and both optional model columns. Existing
   values with any affected Status beyond `not-started` → **stop**: obtain confirmation
   before overwriting. Preserve other columns, sections, row order and statuses.

## Instructions

### Step 0 — Inspect the cache or explicitly refresh

Resolve the configured or already-verified source root and run the read-only guidance
preflight in `workflow-reference → ### Model columns and resolution`. Prefer configured
`ORCHESTRAIL_HOME`; otherwise use an already-known verified absolute `SOURCE_ROOT`.
Use the same source root for the helper `scripts/model-catalog.py`, its siblings
`model_selection.py`/`model_plan.py`, and `$SOURCE_ROOT/docs/MODEL-CATALOG.md`.
Never infer the root from CWD. Relative guide links below serve source readers; installed
skills must read that verified absolute guide. Require Python 3.11+. Missing Python,
missing helper/siblings/guide/schema/rubric → report "selection unavailable", preserve
the current/session model and existing plan/catalog bytes, and return to the caller.
Never invent missing scores, schema or refresh candidates. Check guidance before lookup
or authorized research; missing guidance cannot be repaired by guessing its contents.
Never bypass explicit-request
eligibility; follow `workflow-reference → ### Model columns and resolution` before
any requested model execution. No historical log/store reads are permitted.

Catalog: `$XDG_CONFIG_HOME/orchestrail/model-catalog.md`, falling back to
`~/.config/orchestrail/model-catalog.md`. Run:

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD
```

Show its notice, dates and errors. Ages 0–13 days are fresh; 14–30 produce a dated
notice; over 30 produce a stale warning but remain usable. Missing, malformed or
future dates make selection unavailable. Age never authorizes browsing automatically.

With explicit workflow `--refresh`, a missing or invalid prior catalog remains eligible
for initialization or repair. Refresh research does not require selectable current support.
The workflow performs authorized research using provider documentation for exact
IDs/availability/prices and source-supported capability
evidence. Record source dates; unknown evidence stays null. Build a complete candidate
in a separate temporary file using [the schema and rubric](../docs/MODEL-CATALOG.md).
Keep quality evidence independent from cost bands and price snapshots. Do not evaluate
models, invent defaults or fetch paid comparisons. The helper never browses; helper
`--refresh CANDIDATE` only validates and atomically installs that complete candidate:

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --refresh CANDIDATE
```

A refresh failure preserves the prior catalog. Report rejection even when the old
catalog remains usable; inspect its notice and continue from it if valid. If research
or installation cannot complete, never replace the prior bytes with a partial result.
Without `--refresh`, an unavailable catalog ends ordinary selection visibly. After an
authorized refresh attempt, check catalog usability and current invocation support for
selection. If either remains unavailable, preserve the session and plan and return
"selection unavailable"; never bypass explicit-request eligibility.

### Step 1 — Prepare evidence once, then score leaves

Read shared Task Analysis/design once, then each leaf's Goal, Context, Scope, Steps,
Acceptance Criteria and Test Plan. If design is absent, identify that limitation.
Score C, A, V, R, Ver, Crit and RW as integers 1–5 using the on-demand guide's rubric;
Ver=5 means cheap immediate verification. Resolve adjacent scores conservatively:
higher demand/risk or lower Ver. Missing product intent follows the caller's escalation
protocol. Normalize traits per the guide; context and tools remain separate requirements.

Create an explicit selection JSON input using the helper schema in
[MODEL-CATALOG.md](../docs/MODEL-CATALOG.md). Observe current invocation-specific model
support and permissions from the actual tool; provider labels, catalog TTL and logging
profiles do not establish support. Include requirements, owner constraints, exact
provider/ID default if known, scores, hard categories, traits and task class.
Use `cost_comparisons: []` unless an owner supplies qualified comparable total-cost
exports; never read historical stores directly. Uncalibrated quality is null and
cannot qualify a candidate. No price snapshot establishes capability or equivalent-task cost.

### Step 2 — Recommend through the offline helper

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --select REQUEST.json
```

The helper clamps adjusted weighted demand to ordinal quality 1–5; mandatory security,
financial, architecture, core-invariant and high-blast-radius categories require 5.
Eligibility precedes economics. A suitable session default stays unless qualified
comparable total-cost intervals justify a change; otherwise prefer the strongest eligible
baseline. Cost bands are display labels, never quality floors. Unknown or conflicting
economics preserves the suitable baseline. No eligible model → report stopped and the
unmet constraints; never silently relax them.

### Step 3 — Report and optionally persist

Show each leaf's scores, hard floor, normalized traits, catalog notice, eligible or
excluded identities/reasons, recommendation and uncertainty. Recommendation is advisory;
show requested/resolved/actual separately when resolving a plan, with actual unknown
until separately observed execution evidence. This workflow never spawns or switches models.

Single mode stays chat-only for recommendations. Bulk mode writes only explicit
`Model (Claude)`/`Model (Codex)` decisions through `--update-plan PLAN --updates UPDATES.json`.
Use provider keys `anthropic`/`openai`; leave composite cells blank. Follow the canonical
legacy/empty-column precedence and explicit populated-legacy migration decisions in
`workflow-reference → ### Model columns and resolution`. Never copy one provider's ID
into the other column or erase an unavailable row's prior recommendation. If required
migration decisions are unavailable, report them and preserve the plan.

Changed scope invalidates populated recommendations. Rerun bulk selection to persist
replacement; a single recommendation cannot refresh a stale plan cell. Return visible
results to the caller; `/spec-run`, `/pe-execute` and `/phase-atomic-execution` perform
capability-aware resolution before requesting execution. Missing optional columns retain
visible session-default behavior.
