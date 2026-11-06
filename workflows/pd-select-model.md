---
description: Discovery Step 2.5 — Recommend models from an optional local catalog using current capabilities and independent quality evidence
---

Invocation: `/pd-select-model <path-to-atomic-description | task-directory> [--refresh]`
Called by: `/phase-discovery` after `/pd-decompose`, or manually. `/spec-run` verifies the result. Never edit caller wiring during selection.

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

Resolve the configured or already-verified source root: prefer `ORCHESTRAIL_HOME`;
otherwise use an already-known verified absolute `SOURCE_ROOT`. Never infer it from CWD
or an installed skill location. Use the same source root for `scripts/model-catalog.py`
and its siblings `model_selection.py` and `model_plan.py`. Require Python 3.11+ and
readable helper files. Missing Python, source root or helper/siblings → report
"selection unavailable", preserve the current/session model and existing plan/catalog
bytes, and return to the caller. The rubric, policy and schemas below are self-contained;
`$SOURCE_ROOT/docs/MODEL-CATALOG.md` is an optional companion with executable examples,
not a prerequisite for selection. Do not infer missing scores or refresh candidates.
Never bypass explicit-request eligibility; follow `workflow-reference → ### Model columns
and resolution` before any requested model execution. No historical log/store reads are
permitted.

```bash
SOURCE_ROOT="${ORCHESTRAIL_HOME:-${SOURCE_ROOT:-}}"
case "$SOURCE_ROOT" in /*) ;; *) printf '%s\n' 'selection unavailable: configure an absolute source root' >&2; return 2 2>/dev/null || exit 2 ;; esac
python3 -c 'import sys; assert sys.version_info >= (3, 11)' || { printf '%s\n' 'selection unavailable: Python 3.11+ required' >&2; return 2 2>/dev/null || exit 2; }
for relative in scripts/model-catalog.py scripts/model_selection.py scripts/model_plan.py; do
  [ -r "$SOURCE_ROOT/$relative" ] && [ -f "$SOURCE_ROOT/$relative" ] || { printf '%s\n' "selection unavailable: missing $relative" >&2; return 2 2>/dev/null || exit 2; }
done
HELPER="$SOURCE_ROOT/scripts/model-catalog.py"
```

Catalog: `$XDG_CONFIG_HOME/orchestrail/model-catalog.md`, falling back to
`~/.config/orchestrail/model-catalog.md`. Run:

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD
```

Show its notice, dates and errors. Ages 0–13 days are fresh; 14–30 produce a dated
notice; over 30 produce a stale warning but remain usable. Missing, malformed or
future dates make verified selection unavailable; configured fallback remains preliminary. Age never authorizes browsing automatically.

With explicit workflow `--refresh`, a missing or invalid prior catalog remains eligible
for initialization or repair. Refresh research does not require selectable current support.
The workflow performs authorized research using provider documentation for exact
IDs/availability/prices and source-supported capability
evidence. Record source dates; unknown evidence stays null. Build a complete candidate
in a separate temporary file using the schema and rubric below.
Keep quality evidence independent from cost bands and price snapshots. Do not evaluate
models, invent defaults or fetch paid comparisons. The helper never browses; helper
`--refresh CANDIDATE` only validates and atomically installs that complete candidate:

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --refresh CANDIDATE
```

A refresh failure preserves the prior catalog. Report rejection even when the old
catalog remains usable; inspect its notice and continue from it if valid. If research
or installation cannot complete, never replace the prior bytes with a partial result.
Without `--refresh`, an unavailable catalog uses the configured fallback below; retain
catalog errors and never replace catalog bytes. After refresh, use the valid catalog when
available, otherwise use the fallback. Execution eligibility remains a separate check.

### Required fallback configuration

Before bulk selection, read owner-provided `$XDG_CONFIG_HOME/orchestrail/model-fallback.json`
(or `~/.config/orchestrail/model-fallback.json` when XDG is unset). Its JSON object has
`default` and optional `profiles`; `default` is `{ "model": { "provider": "openai",
"id": "OWNER_CHOSEN_EXACT_ID" }, "reasoning_effort": "OWNER_CHOSEN_LEVEL" }`.
The strings are placeholders: the owner must replace them with an allowed actual identity
and an intended effort. `profiles`, when supplied, maps quality-floor strings `1` through
`5` to objects of the same shape. Select the matching profile, otherwise `default`; include
it as `recommendation_fallback` in each helper request. Validate provider, ID, effort and
owner permissions; never invent defaults or silently create this configuration. Missing or
invalid configuration, or a known incompatibility/owner prohibition on the chosen fallback,
leaves selection incomplete with specific setup/recovery instructions. Configure a suitable
allowed fallback for every relevant profile to guarantee a recommendation; no process can
recommend an allowed model when all configured options are known incompatible.

### Selection rules and input contract

Score each leaf using the following rubric. Columns are complexity C, ambiguity A,
context V, subtle-error risk R, verification Ver, criticality Crit and rework RW.
Choose integers, not interpolated or inferred model scores.

| Score | C complexity | A ambiguity | V context | R subtle errors | Ver verification | Crit blast radius | RW rework |
|---|---|---|---|---|---|---|---|
| 1 | Obvious operation | Fully specified | One file | Immediately obvious | Production needed | Cosmetic | Minutes |
| 2 | Familiar small logic | Inferable gap | A few files | First-run visible | Deep review/staging | Local tooling | Under an hour |
| 3 | Branching edge cases | Judgment needed | Module | Casual review misses | New tests/manual check | User-facing | Hours/dependent |
| 4 | Cross-module invariants | Conflicting requirements | System | Plausible wrong result | Existing tests detect | Auth/data adjacent | Day/dependents |
| 5 | System design | Undefined intent | External/system | Silent corruption | Compiler/linter detects | Finance/security/core | Redesign |

Compute `0.25*C + 0.20*A + 0.15*V + 0.20*R + 0.20*Crit`; round half up,
add one when RW=5, subtract one when Ver=5, and clamp to 1–5. Any of `security`,
`financial`, `architecture`, `core-invariant`, `high-blast-radius` forces floor 5.
Independent catalog quality must meet the floor; it is not a probability and cannot be
inferred from model name, price, cost tier or the task score.

Normalize legacy traits: `long-context`, `coding-heavy`, `web-knowledge` →
`heavy-reasoning`; `cost-efficient-bulk` → `mechanical`; `general` and
`general (default)` → empty; `creative` → `creative`. Creative and heavy-reasoning
may coexist; mechanical conflicts with either, and general conflicts with specializations.
Reject unknown or conflicting traits. Context and tools remain independent requirements.

A refresh candidate is Markdown with exactly one `json model-catalog` fenced payload and
a derived table headed `| tier | anthropic model id | openai model id | relative cost |`.
The schema version 1 payload has exactly `schema_version`, `refreshed`, `evidence_date`,
`models`; dates are YYYY-MM-DD and cannot be future. Each model has exactly `provider`,
`id`, `tier` (light, standard, frontier), `availability` (available, unavailable, unknown),
`context_window` (positive integer or null), `tools` (array or null), `traits`,
`capability_evidence` and `price_snapshot`. Represent all three tiers; derive table rows
from the payload. Evidence is null or `{reference,date,quality}` with quality integer 1–5;
price is null or `{reference,date,relative_cost}` with positive finite relative cost.
Evidence dates cannot exceed refresh; unknown evidence is null and cannot qualify a verified model.
Never convert prices, names, or tiers into quality. The helper validates the entire candidate.

The selection JSON contains `scores`, `hard_constraints`, `traits`, `task_class`,
`requirements`, `harness`, `owner`, `default_model`, `cost_comparisons`, plus optional
`recommendation_fallback` as defined above. Scores contain
exactly C, A, V, R, Ver, Crit, RW. Requirements are `{context_tokens, tools}`; context is a
positive integer and tools a unique string array. Identities are `{provider, id}` with
provider `anthropic` or `openai` and an exact ID. `owner` contains `allowed_models`
(null or identity array) and `excluded_models` (identity array); default_model is an
identity or null. `harness` contains `reference`, today's `date`, and `models`: each
entry has provider, id, availability, context_window and tools. Unknown availability,
context or tools is not eligible. Current support must be directly observed, including
permissions and restrictions; a dated catalog or dispatch success is not observation.

For bulk output to the active provider, constrain `allowed_models` to the intersection of
all known owner permissions and observed candidate identities for that provider. Preserve
owner exclusions, and never invent permission when it is unknown. If the active provider
cannot be identified, stop rather than write a cross-provider ID into its column. In single
mode, report the chosen provider explicitly.

Filter by catalog and harness availability, context, tools, owner limits, independently
sourced `capability_evidence.quality` and required traits before considering cost. Keep a
suitable default, otherwise choose highest evidenced quality, breaking ties by provider/ID.
Use no cost comparisons unless the owner supplies qualified comparable-task evaluations.
Each comparison requires `reference`, `date`, `qualification`, `task_class`, `quality_floor`,
`traits`, `requirements`, `currency`, `estimates`; qualification must be
`comparable-task-evaluation`. Each estimate has provider, id, `total_cost_lower` and
`total_cost_upper` as nonnegative decimal strings. Require matching task class and traits,
covering requirements and quality, and a baseline estimate. Only an unambiguous cheaper
nonoverlapping interval across comparable candidates can displace the baseline; missing,
conflicting, overlapping or unqualified evidence retains it. Cost bands and token prices
alone never prove equivalent-task total cost. Report uncertainty; never relax eligibility.

For plan compatibility, a present empty active provider column overrides legacy `Model`
and means session default; absent active column falls back to legacy, and absent both means
default. Adding columns to populated legacy rows requires explicit decisions for every new
provider on every populated row. Empty cells are not evidence of a recommendation. Keep
unrelated data and composite rows unchanged; never transfer IDs between providers.

### Step 1 — Prepare evidence once, then score leaves

Read shared Task Analysis/design once, then each leaf's Goal, Context, Scope, Steps,
Acceptance Criteria and Test Plan. If design is absent, identify that limitation.
Score C, A, V, R, Ver, Crit and RW as integers 1–5 using the rubric above;
Ver=5 means cheap immediate verification. Resolve adjacent scores conservatively:
higher demand/risk or lower Ver. Missing product intent follows the caller's escalation
protocol. Normalize traits as above; context and tools remain separate requirements.

Create an explicit selection JSON input using the contract above; the runnable example is in
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
economics preserves the suitable baseline. When no verified model is eligible, use the
configured fallback if no known contradiction exists. Report `confidence: preliminary`,
all unknowns, and unverified cost/quality optimality; known incompatibilities stop rather
than silently relaxing constraints. A verified result reports `confidence: verified`.

### Reasoning effort recommendation

For each leaf, recommend reasoning effort along with its model. Inspect the actual current
worker tool and chosen model for supported levels, their ordering and whether effort is
configurable; record the observation source and rationale. Use demand and risk scores as
heuristics: 1–2 favor low, 3 medium, 4 high, 5 the highest justified supported level;
hard constraints favor high or higher. Map only to levels whose meaning and support are
observed for that model and invocation, and explain any adjustment. These heuristics do
not establish quality, eligibility or a provider-independent scale. The offline helper does
not recommend reasoning levels; the workflow adds this assessment to its result.

If the tool explicitly has no configurable effort, report `not configurable` and explain
that its default is unknown. If support or level meanings are unknown, report the owner-configured fallback reasoning
level as preliminary and unverified; never claim it is supported. If the selected model
is verified but reasoning support is unknown, use the owner-configured effort for that
same model only; otherwise recommend an effort as a provisional heuristic with uncertainty. Report
recommended, requested and actual reasoning separately; actual remains unknown without
separate matching execution evidence. Never imply a recommendation changed the session.

### Selection checkpoint (bulk mode)

Before bulk preflight, set `## Model Selection` in task `state.md` to `selection: incomplete`.
Record the reason and recovery action on any unavailable, stopped, partial or failed update;
keep an in-progress discovery in progress; never change a previously completed discovery status. Resume selection after recovery. Do not mark complete for
empty cells: an empty assignment is not evidence of a checked recommendation.

On success, record `selection: complete`, the active provider, catalog path and refresh date,
current invocation support evidence reference and date when available (otherwise explicitly
record unknown), and for every leaf its recommendation,
selection confidence (`verified` or `preliminary`), evidence or explicit unknowns, reasoning recommendation (or `not configurable`) with rationale and support observation or unknown, and SHA-256 digests of the raw description bytes and of a UTF-8 JSON array of the parsed plan row ID, Name, Key Steps (summary) and Depends On cells, in that order, with compact separators and non-ASCII characters preserved. Exclude status and model columns. Persist the active provider recommendation in each leaf
row. Composite rows stay blank. Preliminary recommendations count as complete only when
the configured fallback is valid and all known constraints are satisfied; record all missing
evidence. Missing or prohibited fallback keeps the checkpoint incomplete. Never synthesize evidence or treat an empty session
default as a recommendation. Actual execution remains unknown until separately observed.
Recompute digests when resuming and before finalization; changed leaves or decomposition
invalidate the checkpoint and require bulk reselection. Preserve prior plan values on failure.

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
