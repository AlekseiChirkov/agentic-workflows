---
description: Discovery Step 2.5 — Select the optimal LLM per subtask by cost/quality trade-off, after Task Analysis and Decomposition
---

Invocation: `/pd-select-model <path-to-atomic-description | task-directory>`
Called by: manually after `/pd-decompose`, or `/spec-run` Step 2. Optional in
`/phase-discovery`; do not modify orchestrator wiring while running this command.

| Mode | Input | Output |
|---|---|---|
| Single | Existing leaf `T-XX-*/description.md` | Chat recommendation only; no file writes |
| Bulk | Task directory containing `plan.md` | Chat recommendations and only the `Model` column in `plan.md → ## Subtasks` |

For single mode, task directory is the description's grandparent; composite children
are sibling directories at that level. Reject other input shapes. The live catalog stays in chat; never read or write a catalog cache.

## Guard

1. Require task `state.md → ## Task Analysis`, complete Decomposition, and a nonempty
   `plan.md → ## Subtasks` table. Otherwise **stop**: run `/pd-analyze` and
   `/pd-decompose` first. Quick flow has no leaves and does not use this workflow.
2. Single mode: require the ID in the plan and reject `type: composite` containers;
   recommend models for their leaf children instead.
3. Bulk mode: score every non-composite row. Require its description; missing input
   → **stop** and report it. If Model already has values and any row Status is beyond
   `not-started`, **stop** for confirmation before overwriting. Otherwise replacement
   is permitted. Preserve all other columns, sections, row order and statuses.

## Instructions

### Step 0 — Build the model catalog via live web search (every run, no file)

Use live sources on every invocation to verify current model IDs, pricing basis,
capabilities and availability. Cover Anthropic/Claude, OpenAI/GPT and open-weight
releases, Google/Gemini, xAI/Grok, Zhipu/GLM, Moonshot/Kimi, MiniMax, and dedicated
coding-agent families. Include relevant new providers found. Batch independent
queries; reuse each result within this run. Do not assume model names exist.

Prefer provider documentation for IDs, availability and prices, and published
benchmark methodology/results for capability evidence. Cite sources and their dates.
Mark missing, stale or conflicting evidence per provider; do not invent a catalog row.
If web search is unavailable or no usable candidates remain, **stop** and report why.

Assign verified models to Light, Standard or Frontier quality bands. Every populated
band has exactly one `general (default)` model. A missing band is unavailable, not
permission to invent a default. Recommend only IDs the executing environment can use;
mark other verified models advisory. If availability is unknown, state that dependency
rather than claiming the recommendation is immediately executable.

Use RCU (relative cost per equivalent task, cheapest comparable candidate = 1) and
1–10 capability estimates. State the workload/pricing assumptions used to normalize
RCU; input-token price alone does not establish equivalent-task cost. Ratings and
correctness probabilities are selection heuristics, not measured guarantees.
Show the compact catalog once, dated today, before scoring; schema below.

### Step 1 — Score the subtask(s) in scope

Read shared Task Analysis/design once, then each leaf's Goal, Context, Scope, Steps,
Acceptance Criteria and Test Plan. Design may not exist yet when called directly after
Decomposition; use analysis/descriptions and identify that limitation. Reuse shared context across leaves.

Score all **seven** factors C, A, V, R, Ver, Crit and RW from 1–5 using
`## Scoring Rubric`. If evidence supports adjacent scores, use the higher demand/risk
score (or lower Ver) and explain briefly; do not interrupt for numerical rounding.
Missing product intent follows the caller's escalation protocol rather than being
resolved through model selection.

Tag applicable traits in priority order: creative (style/voice dominates), long-context
(V≥4), coding-heavy (implementation/refactor and C≥3), web-knowledge (current external
facts), otherwise general. A non-stylistic hard floor disables creative bypass.

### Step 2 — Derive the minimum quality tier (Qmin)

```
Qmin_raw = floor(0.25*C + 0.20*A + 0.20*R + 0.20*Crit + 0.15*V + 0.5)
Qmin_raw += 1 if RW = 5
Qmin_raw -= 1 if Ver = 5
```

Map ≤2 → Light, 3 → Standard, ≥4 → Frontier. The explicit rounding rule applies
before adjustments. Regardless of score, Frontier is required for architectural
or structural decisions, security-sensitive logic, financial/pricing/billing
calculations, core business invariants, or work explicitly marked high blast radius
by task Off-limits/Invariants. Ordinary implementation near those areas is not by
itself a structural decision; cite the actual category that applies.

### Step 3 — Filter candidate models

Keep available models at or above Qmin in the ordered Light → Standard → Frontier
bands. No eligible candidate → **stop** and report the unmet quality/availability
constraint. Cost never admits a model below the floor.

An optional live-confirmed creative specialist may be reported under the display
label `Fable`, outside the cost ladder, only if it also meets Qmin and no non-stylistic
hard floor applies. `Fable` is a selection label, never a hardcoded model ID or a
claim that such a release exists. Without an eligible specialist, use the normal ladder.

### Step 4 — Step up through remaining tiers using expected cost of error

For the normal path, start with the lowest eligible quality band's default. Compare each
next available higher band using its default; if verified RCU is non-monotonic,
report the inconsistency and prefer the higher-quality candidate at equal/lower cost.

```
DeltaCost = RCU(higher) - RCU(current)
Step up only if DeltaCost < ECE * DeltaQuality.
```

Stop at the first failed inequality; do not skip that failure to test a later tier.
All ECE and uplift values below are heuristic bands, not observations.

Compare demands on a common scale: `2*C` to code correctness for coding-heavy work
(otherwise reasoning depth), `2*A` to ambiguous-instruction following, and `2*V` to
long-context capability of the current default. Count exceeded axes:

| Condition (first match) | DeltaQuality |
|---|---|
| A=5 or all three axes exceed capability | 0.40 |
| Two axes exceed | 0.25 |
| One axis exceeds | 0.10 |
| No axis exceeds | 0.05 |

Select ECE with exhaustive first-match rules:

| Condition | ECE (RCU) |
|---|---|
| Crit=5, or Ver≤2 and RW≥4 | 40 |
| RW≥4 or Crit≥4 | 12 |
| RW≤2 and Crit≤2 | 1 |
| Otherwise | 4 |

Example: C=3,A=2,V=2,R=2,Ver=4,Crit=2,RW=2 gives raw=2 and Light floor.
If DeltaCost=3, ECE=1 and no axis exceeds capability, `3 < 1*0.05` fails: stay.

### Step 4.5 — Pick the specific model within the final tier

For an eligible creative selection from Step 3, report its verified ID and the
cost-ladder bypass. Otherwise, within the chosen band, select the first matching
specialty in trait order; ties use lower RCU, then stronger relevant capability.
No match → use the band's default. A specialist never bypasses Qmin or forces a
higher band. If it costs more than the default, apply the same inequality to that
substitution; if it fails, keep the default. Do not reopen a failed inter-band step.

### Step 5 — Present the recommendation

Single mode prints ID/name, seven scores, traits, Qmin and reason, selected verified
model/provider, final band, and rationale. No table is necessary; write no files.

Bulk mode prints one compact table:

```
| ID | C | A | V | R | Ver | Crit | RW | Trait | Qmin Tier | Recommended Model | Rationale |
|----|---|---|---|---|-----|------|----|-------|-----------|-------------------|-----------|
| T-XX | <scores> | ... | ... | ... | ... | ... | ... | <trait> | <floor> | <verified ID> | <evidence> |
```

For each rationale, cite the hard floor, the actual terminal inequality, or the
eligible creative bypass, plus default/specialty selection. At the highest available
band with no next comparison, say so instead of inventing an inequality. Show composite
containers as `(inherits from children)` without scoring them. Close with the band
counts (Light, Standard, Frontier, optional Fable).

Bulk mode — write the `Model` column into `plan.md` after `Name`; leave composite cells
blank, and writes the same verified ID as the chat recommendation. Do not create a
Model Selection section or touch state/descriptions/catalog files. A changed scope
invalidates a prior bulk recommendation: rerun **bulk** mode to persist a refresh.
A later single-mode recommendation remains chat-only and never updates a stale cell.

## Scoring Rubric

Use the closest evidence-supported anchor. Ver runs in the opposite direction from
risk factors: **5 is easiest/cheapest verification; 1 is hardest**.

| Score | C: complexity | A: ambiguity | V: context | R: subtle-error risk | Ver: verification | Crit: blast radius | RW: rework |
|---|---|---|---|---|---|---|---|
| 1 | Obvious operation | Fully specified | One file | Error obvious | Production incident needed | Cosmetic | Minutes |
| 2 | Small familiar logic | Minor inferable gap | 2–3 files | Visible on first run | Deep review/staging | Low-visibility tooling | Under one hour |
| 3 | Branching/edge cases | Judgment needed | Related module files | Casual review may miss | New tests/manual check | User-facing, noncritical | Hours; one dependent |
| 4 | Cross-module invariants | Conflicting/missing requirements | Cross-service/system | Plausible wrong result | Existing tests detect | Revenue/auth/data integrity adjacent | Day; multiple dependents |
| 5 | System design | Undefined intent | System and external context | Silent corruption | Compiler/linter detects instantly | Direct finance/security/core invariant | Redesign/incident |

## Model Catalog Template (schema only — never persisted, rebuilt every run in-chat via Step 0)

Use verified rows only; the placeholders are column definitions, not candidates.

```
Model catalog rebuilt from live web search as of <YYYY-MM-DD>.
RCU/rating estimates use <workload and pricing assumptions>; availability: <source>.

| Tier | Model id | Provider | RCU | Reasoning depth | Long-context | Code correctness | Ambiguous-instruction following | Specialty |
|------|----------|----------|-----|-----------------|--------------|------------------|---------------------------------|-----------|
| <band> | <verified ID> | <provider> | <estimate> | <1–10> | <1–10> | <1–10> | <1–10> | <general (default), general, creative, long-context, coding-heavy, web-knowledge or cost-efficient-bulk> |
```

## Optional Orchestrator Wiring

`/phase-discovery` does not call this command by default. A separately authorized
pipeline edit may insert bulk selection after Decomposition; `/pd-design` can then
invalidate affected recommendations. This workflow never edits its caller.
`/spec-run` invokes bulk selection after Discovery and reads the persisted column.

## Notes for Consumers (`/pe-execute`, `/phase-atomic-execution`)

`/spec-run` reads Model per leaf; absent/blank cells use the session default with a
note. Other executors use it only if they support model selection. Single mode
leaves model switching to the caller. Do not claim a model switch the harness cannot make.
