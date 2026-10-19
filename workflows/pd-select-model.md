---
description: Discovery Step 2.5 — Select the optimal LLM per subtask by cost/quality trade-off, after Task Analysis and Decomposition
---

Invocation — two modes, same pattern as `phase-atomic-execution` / `phase-execution`:
- `/pd-select-model <path-to-atomic-description>` — **single-subtask mode**: recommend a model for just this T-XX.
- `/pd-select-model <task-directory>` — **bulk mode**: recommend a model for every subtask in `plan.md`.

Example: `/pd-select-model .ai/tasks/todo/task-01-add-oauth/T-03-slug/description.md`
         `/pd-select-model .ai/tasks/todo/task-01-add-oauth/`

Called by: manually, after `/pd-decompose`. Not auto-invoked by `/phase-discovery`
(wire it in explicitly if you want it to run automatically — see `## Optional Orchestrator Wiring`).

**Output contract — differs by mode.**

- **Single-subtask mode: chat-only, no file writes.** A one-off opinion about one T-XX is
  not project state; it is printed and nothing else.
- **Bulk mode: writes the `Model` column into `plan.md → ## Subtasks`.** Executors need a
  persisted value to act on — `/spec-run` reads this column to choose the model for each
  subtask's Implementer agent. This is the only file this workflow ever writes, and it
  writes exactly that one column.

The model catalog is never written to disk in either mode — it is rebuilt from a live web
search every run (see Step 0) and lives only in the chat for that run.

**Mode detection:** if the argument path is a file named `description.md` →
single-subtask mode. `Atomic task directory` = parent directory of that file
(the T-XX being scored); `Task directory` = one level above that. Otherwise
the argument is a directory → bulk mode; `Task directory` = the argument
itself (trailing slash optional), and all T-XX rows in its `plan.md` are in
scope.

If the path is neither a `description.md` file nor a directory containing
`plan.md` → **stop**: "Not a recognized path. Pass either a T-XX
`description.md` (single-subtask mode) or a task directory containing
`plan.md` (bulk mode)."

---

## Guard

Shared checks (both modes), run against `Task directory`. These are the
only guards. In single-subtask mode nothing is persisted, so re-running is
always safe and simply reprints a fresh recommendation. In bulk mode, if the
`Model` column already holds values **and** any subtask has a `plan.md` Status
beyond `not-started`, ask before overwriting: "Model column already populated
and execution has started. Overwrite? (yes/no)" — re-assigning a model under a
subtask already being executed is a change the user should see. If every
subtask is still `not-started`, overwrite without asking.

1. Read `state.md`. If it does not exist or `## Task Analysis` section is missing → **stop**: "Step 1 (Task Analysis) must be completed first. Run `/pd-analyze <path>`." Do not continue.
2. Verify decomposition is complete: `## Decomposition` section with `decomposition: complete` must be present in `state.md`, and `plan.md` must contain a `## Subtasks` table with at least one T-XX row. If either is missing → **stop**: "Step 2 (Decomposition) must be completed first. Run `/pd-decompose <path>`." Do not continue.

Mode-specific checks:

3a. **Single-subtask mode:** verify the T-XX referenced by the given
`description.md` appears as a row in `plan.md → ## Subtasks`. If not found →
**stop**: "T-XX not listed in plan.md. Re-run /pd-decompose or check the path."
If the T-XX is a composite (`## Context` contains `type: composite`) →
**stop**: "T-XX is a composite container — model selection applies to its
leaf children only. Run /pd-select-model on T-XXa, T-XXb, … instead."

3b. **Bulk mode:** no extra check beyond 1–2 — every scoreable (non-composite)
T-XX row in `plan.md → ## Subtasks` is in scope every time.

4. Otherwise → continue.

---

## Instructions

### Step 0 — Build the model catalog via live web search (every run, no file)

There is no persisted catalog file and this workflow never checks for or
reads one. `.ai/context/model-catalog.md` must **not** be created, read, or
relied upon — model lineups, pricing, and benchmarks move too fast for a
cached file to stay trustworthy, so every invocation rebuilds the catalog
from scratch via web search, in-chat only.

**Every run, unconditionally, before any scoring:** use web search to
determine (a) the current flagship/mid/light model lineup for **every**
provider covered by the tier schema, and (b) recent independent benchmark
results (e.g. coding, reasoning, long-context evals) to derive relative
capability ratings and RCU (relative cost unit) ordering. Models get
renamed, deprecated, or superseded often — never assume prior knowledge or
the `## Model Catalog Template` model ids are still current; always confirm
against fresh search results.

At minimum, explicitly search for and refresh each of the following
providers/model families every run — do not silently skip any of them, and
do not stop at the first one or two that turn up easy results:

- **Anthropic** — Claude family (current flagship/mid/light, e.g. Opus/Sonnet/Haiku tiers, plus Fable)
- **OpenAI** — GPT family (flagship, mid, mini/light tiers) and any current open-weight release (e.g. gpt-oss)
- **Google** — Gemini family
- **xAI** — Grok family
- **Zhipu** — GLM family
- **Moonshot** — Kimi family
- **MiniMax** — MiniMax family
- Any dedicated coding-agent model line (e.g. SWE-family) distinct from the general-purpose vendors above

If a web search turns up a provider/family not on this list (new entrant,
renamed vendor), include it too — this list is a floor, not a ceiling. If
search results are stale, contradictory, or a given provider returns
nothing usable, say so explicitly in the catalog output for that row rather
than silently falling back to the template's placeholder values. Use
`## Model Catalog Template` only as the tier structure/column schema to
fill in, not as a source of model ids or ratings.

Build the resulting catalog as an **in-chat table only**, following the
same schema (tier, model id, provider, RCU, capability ratings, Specialty)
as the template. Show this freshly built catalog to the user before
scoring, prefixed with: "Model catalog rebuilt from live web search as of
<today's date> — not persisted to disk, rebuilt fresh every run. **RCU and
capability ratings are best-effort estimates derived from search results,
not verified pricing/benchmarks — check them against your actual
plan/pricing before trusting the recommendations.**"

If web search is unavailable or returns nothing usable, **stop** — do not
fall back to the static template values or to prior knowledge as if they
were current. Tell the user web search is required to run this workflow and
ask them to retry once it's available.

The catalog defines, per tier: model id, provider, relative cost unit
(RCU — cost of this model per equivalent task relative to the cheapest
tier = 1), capability ratings (1–10) for reasoning depth, long-context
handling, code correctness, and instruction-following under ambiguity, and a
**Specialty** tag (`general`, `long-context`, `coding-heavy`,
`web-knowledge`, or `cost-efficient-bulk`). Several models can share a tier —
exactly one per tier is marked `general (default)`, the fallback when no
specialty applies. All scoring below is relative to this catalog — never
hardcode prices in this workflow.

### Step 1 — Score the subtask(s) in scope

Determine scope from the invocation mode:
- **Single-subtask mode:** scope = the one T-XX resolved in `## Guard`.
- **Bulk mode:** scope = every non-composite T-XX row in
  `plan.md → ## Subtasks`. Skip composite container rows (`type: composite`)
  — score their leaf children individually instead; the composite row is
  annotated `(inherits from children)` when reported in Step 5.

For each T-XX in scope, read `T-XX-*/description.md` (`## Goal`,
`## Context`, `## Scope`, `## Steps`, `## Acceptance Criteria`) and
`state.md → ## Solution Design` for the chosen architecture. Score against
the six input factors, 1–5 each (see `## Scoring Rubric` for anchors):

| Factor | What it measures |
|---|---|
| **Complexity (C)** | Logical/technical difficulty of the steps |
| **Ambiguity (A)** | How under-specified the Goal/Scope/Acceptance Criteria are |
| **Context Volume (V)** | How much surrounding code/domain knowledge must be held at once |
| **Risk (R)** | Likelihood the task produces a subtly wrong result, not just an obviously broken one |
| **Verifiability (Ver)** | How cheaply/automatically a wrong output is caught (tests, types, linters, obvious visual diff) — 5 = caught instantly and free, 1 = only caught in production weeks later |
| **Criticality (Crit)** | Blast radius if this subtask ships wrong: user impact, financial exposure, security surface, architectural lock-in |
| **Rework Cost (RW)** | Cost to redo/debug if this subtask is wrong: hours lost, downstream subtasks blocked, cascading rework |

If any score is genuinely ambiguous between two values — **stop**, describe
the ambiguity, propose the 2 candidate scores with reasoning, and wait for
the user's call. Do not silently pick the higher or lower one.

Also tag the subtask's **Dominant Trait** — the one dimension, if any, where
a specialist model handles the work meaningfully better than a generalist at
the same tier:

| Trait | Trigger |
|---|---|
| creative | Goal/Context is primarily stylistic/tonal — creative writing, marketing/narrative copy, persona-driven dialogue, brainstorming variance — where voice and originality matter more than deterministic correctness |
| long-context | V ≥ 4, or the Context/Scope requires holding a large multi-file/spec surface at once |
| coding-heavy | Steps are predominantly code implementation/refactor and C ≥ 3 |
| web-knowledge | Goal/Context requires reasoning over current/real-time external information |
| general | None of the above apply distinctly |

If two traits both apply, note both — Step 4.5 will check them in the order
listed and use the first that has a matching specialist in the surviving
tier. Exception: `creative` is checked before all others regardless of list
order, since it is resolved off the cost ladder entirely (see Step 4.5) —
if `creative` applies alongside another trait, it still takes priority
unless the hard-floor override in Step 2 fired for a non-stylistic reason
(security/financial/architectural/business-invariant), in which case treat
the subtask as *not* creative for model-selection purposes and fall through
to the next listed trait — correctness trumps voice on high-blast-radius work.

### Step 2 — Derive the minimum quality tier (Qmin)

Compute a raw score:

```
Qmin_raw = round(0.25×C + 0.20×A + 0.20×R + 0.20×Crit + 0.15×V)
Qmin_raw = Qmin_raw + 1   if RW = 5 (very high rework cost)
Qmin_raw = Qmin_raw − 1   if Ver = 5 (instant, free verification)
```

Map to a tier:

| Qmin_raw | Tier |
|---|---|
| ≤ 2 | Light |
| 3 | Standard |
| ≥ 4 | Frontier |

**Hard floor override (quality-priority categories).** Regardless of
`Qmin_raw`, set `Qmin tier = Frontier` if the subtask is any of:
architectural/structural decision-making, security-sensitive logic,
financial/pricing/billing calculations, core business-logic invariants, or
any subtask the task's `## Solution Design → Off-limits` / `Invariants`
mark as high-blast-radius. This is the one place quality overrides the
cost formula outright — everywhere else, the formula in Step 4 decides.

### Step 3 — Filter candidate models

From the catalog built via live web search in Step 0, keep only tiers whose
capability ratings meet `Qmin tier`. Discard everything below the floor — a
model that can't reliably meet the quality bar is not a valid candidate
regardless of price, per the elimination principle: cost only matters among
models that already clear the bar.

### Step 4 — Step up through remaining tiers using expected cost of error

Start from the cheapest surviving tier. For each candidate step-up (cheaper
tier `M_cheap` → next tier `M_expensive`), decide using:

```
ΔCost    = RCU(M_expensive) − RCU(M_cheap)                       [catalog]
ΔQuality = estimated uplift in first-try correctness probability  [banded, see below]
ECE      = expected cost of error if M_cheap is wrong              [banded, see below]

Step up to M_expensive only if:  ΔCost < ECE × ΔQuality
Otherwise: stay on M_cheap.
```

**ΔQuality band** — compare the subtask's C/A/V scores against
`M_cheap`'s capability ratings in the catalog:

| Condition | ΔQuality band | value |
|---|---|---|
| Subtask scores ≤ M_cheap's rated capability on all axes | negligible | 0.05 |
| Subtask exceeds M_cheap's rating on one axis | small | 0.10 |
| Subtask exceeds M_cheap's rating on two axes | moderate | 0.25 |
| Subtask exceeds M_cheap's rating on all axes, or A=5 | large | 0.40 |

**ECE band** — combine Rework Cost, Criticality, Verifiability (in RCU,
same units as `ΔCost`, so the two sides of the inequality are comparable):

| RW | Crit | Ver | ECE band | value (RCU) |
|---|---|---|---|---|
| 1–2 | 1–2 | any | low | 1 |
| 3 | 3 | ≥3 | medium | 4 |
| 4–5 | 3–4 | ≤3 | high | 12 |
| any | 5, or Ver ≤2 with RW≥4 | — | very high | 40+ |

Walk the tiers one step at a time (Light→Standard, then, only if that step
was taken, Standard→Frontier). Stop climbing as soon as a step fails the
inequality — do not skip a failed step to test the next one.

Use each tier's `general (default)` model's catalog ratings for this
stepping math — Step 4.5 below only decides *which* model within the final
tier to recommend, it never reopens the tier decision made here. Same-tier
models are assumed cost-equivalent for this comparison; if one model's real
RCU diverges meaningfully from its tier-mates, treat it as its own tier
instead of grouping it.

**Worked example.** Subtask scores C=3, A=2, V=2, R=2, Ver=4, RW=2, Crit=2 →
`Qmin_raw = round(0.25·3+0.20·2+0.20·2+0.20·2+0.15·2) = round(2.15) = 2` →
tier floor = Light. ECE = low = 1 RCU. Stepping Light→Standard: catalog says
`ΔCost = 3 RCU`, subtask doesn't exceed Light's rated capability on any axis
→ ΔQuality = negligible = 0.05. Check: `3 < 1 × 0.05` → **false** → stay on
Light. The cheaper model wins because the potential quality gain isn't worth
its price at this error cost.

### Step 4.5 — Pick the specific model within the final tier

**Step 0 (creative override, checked first, before Step 4 even matters):**
if the subtask's Dominant Trait is `creative` (and it survived the
non-stylistic hard-floor exception in Step 1's trait table), recommend the
`Fable` tier's model (`claude-fable-5`) directly and **skip Step 4's
tier-ladder math entirely** — Fable is explicitly a non-cost-ladder tier, so
there is no ΔCost/ECE step-up to compute and no `general (default)` to fall
back to. Record the rationale as `(non-cost-ladder: creative trait →
claude-fable-5, tier-ladder bypassed)`. Report its Qmin tier in Step 5 output
as `Fable` rather than Light/Standard/Frontier.

Otherwise, Step 4 already fixed a cost-ladder tier (Light/Standard/Frontier).
Now pick which catalog model in that tier to actually recommend:

1. If the subtask's Dominant Trait (Step 1) is `general`, or no model in
   this tier carries a matching Specialty tag → recommend that tier's
   `general (default)` model. Done.
2. Otherwise, check the tier for a model whose Specialty matches the
   Dominant Trait (in trait-list order, if more than one applies). If found
   → recommend it instead of the default, and record the override in the
   rationale as `(specialty override: <trait> → <model-id>)`.
3. If the only model with a matching Specialty lives in a *higher* tier than
   the one Step 4 landed on, do **not** force the step-up here — that is
   exactly the ΔCost/ECE tradeoff Step 4 already adjudicated. Re-run that
   tier's inequality check once more with the specialist substituted for the
   default model's ratings; only step up if it now passes. If it doesn't,
   stay on the current tier's default model.

Within the cost-ladder path, this step changes *which* model is named, never
the tier itself, and never bypasses Step 4's inequality — the sole exception
is the `creative` override above, which bypasses Step 4 entirely by design
because Fable is not part of the cost ladder.

### Step 5 — Present the recommendation

Per the **Output contract** at the top of this file, what is persisted differs by mode.

**Single-subtask mode — chat only.** Do NOT add a `Model` column to `plan.md`, do NOT create
or update a `## Model Selection` section, do NOT touch `state.md`. A one-off opinion about one
T-XX is not project state. If the user wants to keep the recommendation, they copy it from the
chat themselves.

**Bulk mode — write the `Model` column into `plan.md → ## Subtasks`, and nothing else.** Add
the column after `Name` (format at `## Notes for Consumers` below), leave it blank for
composite rows, and write the same value the chat table shows. `/spec-run` Step 2 reads this
column to choose each subtask's Implementer model, so a bulk run that persists nothing leaves
that reader with no value to act on. Do NOT create a `## Model Selection` section and do NOT
touch `state.md` — the column is the only thing this workflow ever writes.

Format the chat response as follows.

**Single-subtask mode** — plain text, no table needed:

```
Model recommendation for T-XX — <name>:
  Scores: C=<n> A=<n> V=<n> R=<n> Ver=<n> Crit=<n> RW=<n>
  Dominant trait: <general|long-context|coding-heavy|web-knowledge|creative>
  Qmin tier: <Light|Standard|Frontier|Fable>  (<cite hard-floor category, "derived from Qmin_raw=<n>", or "non-cost-ladder: creative trait">)
  Recommended model: <model-id> (<tier>, <provider>)
  Why: <the specific inequality check (pass/fail) at the tier where climbing
        stopped, e.g. "ΔCost(3) ≥ ECE(1)×ΔQuality(0.05) at Light→Standard —
        stayed on Light">, plus <"tier default — no specialty match" or
        "specialty override: <trait> → <model-id>">
```

**Bulk mode** — one markdown table in the chat message (the table itself is not saved; only
the `Model` column it feeds is written to `plan.md`):

```
| ID | C | A | V | R | Ver | Crit | RW | Trait | Qmin Tier | Recommended Model | Rationale |
|----|---|---|---|---|-----|------|----|-------|-----------| -------------------|-----------|
| T-01 | 3 | 2 | 2 | 2 | 4 | 2 | 2 | general | Light | <model-id> | ΔCost(3) ≥ ECE(1)×ΔQuality(0.05); cheapest tier clears floor; tier default |
| T-02 | 5 | 4 | 3 | 4 | 2 | 5 | 4 | general | Frontier | <model-id> | Hard floor: architectural subtask; tier default |
| T-03 | 4 | 2 | 5 | 3 | 3 | 3 | 3 | long-context | Standard | <model-id> | ΔCost/ECE landed on Standard; specialty override: long-context → <model-id> |
| T-04 | 2 | 3 | 1 | 1 | 2 | 1 | 1 | creative | Fable | claude-fable-5 | non-cost-ladder: creative trait → claude-fable-5, tier-ladder bypassed |
```

Every row's Rationale must cite either the hard-floor category that fired,
the specific inequality check (pass/fail) at the tier where climbing
stopped, or the creative bypass, **and** state whether the tier default, a
specialty override, or the non-cost-ladder Fable override was used. "Chose
the strong model to be safe" is not an acceptable rationale — it must
reference the ECE/ΔQuality comparison (or the creative-trait bypass).

Close the bulk-mode message with a one-line summary: "Tier distribution:
Light=<n>, Standard=<n>, Frontier=<n>, Fable=<n>."

If any subtask's decomposition or scope materially changes in `/pd-design`
(Step 3), re-run `/pd-select-model <T-XX/description.md>` in single-subtask
mode for the affected T-XX to get a fresh recommendation. In single-subtask
mode nothing was persisted, so there is no stale value to invalidate; after a
bulk run, update that row's `Model` cell so `plan.md` and the recommendation
do not disagree.

---

## Scoring Rubric

Anchors for the 1–5 scores in Step 1 (use the closest match, do not
interpolate beyond ±1 without stopping to ask, per the Guard-adjacent rule
in Step 1):

| Score | Complexity (C) | Ambiguity (A) | Context Volume (V) | Risk (R) | Verifiability (Ver) | Criticality (Crit) | Rework Cost (RW) |
|---|---|---|---|---|---|---|---|
| 1 | Single obvious operation (rename, format, add getter) | Fully specified, one valid interpretation | Fits in one file, no cross-file reasoning | Wrong output is immediately obvious | Caught instantly by compiler/linter/type-checker | Cosmetic, zero user/business impact | Redo takes minutes, no blocked dependents |
| 2 | Small well-understood change, few branches | Minor gaps, easy to infer intent | 2–3 files, shallow dependencies | Wrong output likely visible on first run | Caught by running existing tests | Internal tooling, low visibility | Redo takes < 1 hour |
| 3 | Multi-step logic, some branching/edge cases | Some requirements need a reasonable judgment call | Module-level, several related files | Wrong output may pass casual review | Needs new tests or manual check to catch | User-facing but non-critical feature | Redo takes a few hours, may touch 1 dependent |
| 4 | Cross-module logic, non-trivial invariants | Requirements conflict or are partially missing | Cross-service/whole-codebase reasoning | Wrong output plausible-looking, hard to spot | Requires deep manual review or staging validation | Revenue/auth/data-integrity adjacent | Redo takes a day+, blocks multiple dependents |
| 5 | Architectural/systemic decision | Requirements essentially undefined, must be designed | Whole-system + external context (specs, ADRs, integrations) | Wrong output silently corrupts data/decisions | Effectively unverifiable short of production incident | Direct financial, security, or core business-logic impact | Redo requires re-architecture or causes incident-level damage |

---

## Model Catalog Template (schema only — never persisted, rebuilt every run in-chat via Step 0)

```markdown
# Model Catalog (in-chat, rebuilt fresh every run — not written to disk)

**Built from live web search:** <YYYY-MM-DD — today, always, see Step 0>

**These RCU and capability numbers are best-effort estimates derived from
this run's web search, not verified pricing or benchmarks — VERIFY against
your actual plan/API pricing and any benchmark you trust before relying on
the recommendations.** Relative Cost Unit (RCU) is per-equivalent-task
cost, cheapest tier = 1. Capability ratings are 1–10. The model ids/ratings
below are illustrative of the schema only — Step 0 must replace them with
whatever the live web search turns up as current, every time.

Exactly one model per tier is marked `general (default)` — the fallback
recommendation when the subtask's Dominant Trait (see Step 1) doesn't match
any specialist in that tier. Other models in the same tier carry a
Specialty tag and are only recommended when Step 4.5 finds a matching trait.

| Tier | Model id | Provider | RCU | Reasoning depth | Long-context | Code correctness | Ambiguous-instruction following | Specialty |
|------|----------|----------|-----|------------------|---------------|-------------------|----------------------------------|-----------|
| Light | claude-haiku-4-5-20251001 | Anthropic | 1 | 5 | 4 | 5 | 4 | general (default) |
| Light | gpt-5.4-mini | OpenAI | 1 | 5 | 4 | 5 | 4 | general |
| Light | glm-5 | Zhipu | 1 | 4 | 4 | 5 | 3 | cost-efficient-bulk |
| Light | minimax-m2 | MiniMax | 1 | 4 | 4 | 5 | 3 | cost-efficient-bulk |
| Light | gpt-oss-120b | OpenAI (open-weight) | 1 | 4 | 4 | 5 | 3 | cost-efficient-bulk |
| Standard | claude-sonnet-5 | Anthropic | 4 | 7 | 7 | 8 | 7 | general (default) |
| Standard | gpt-5.4 | OpenAI | 4 | 7 | 7 | 8 | 7 | general |
| Standard | kimi-k2 | Moonshot | 4 | 6 | 9 | 7 | 6 | long-context |
| Standard | swe-1.5 | (coding-agent) | 4 | 6 | 6 | 9 | 6 | coding-heavy |
| Frontier | claude-opus-4-8 | Anthropic | 15 | 9 | 9 | 9 | 9 | general (default) |
| Frontier | gpt-5.5 | OpenAI | 15 | 9 | 9 | 9 | 9 | general |
| Frontier | gemini-3-pro | Google | 15 | 9 | 10 | 8 | 8 | long-context |
| Frontier | grok-5 | xAI | 15 | 8 | 8 | 8 | 8 | web-knowledge |

Non-cost-ladder tier (style/creative variance, not a cost step — auto-
recommended by Step 4.5 when the subtask's Dominant Trait is `creative`,
bypassing the Light/Standard/Frontier ladder entirely; see Step 4.5):
| Fable | claude-fable-5 | Anthropic | — | — | — | — | — | creative |
```

---

## Optional Orchestrator Wiring

By default `/phase-discovery` does not call this workflow — model selection
is opt-in so tasks that don't need multi-model execution aren't slowed down.
To make it a mandatory Discovery step, insert
`3. Call /pd-select-model <task-directory>` between the existing steps 2
and 3 in `phase-discovery.md → ## Execution`. In bulk mode the recommendation
persists as the `Model` column in `plan.md`, so wiring it in does make the
choice available to executors — but it still does not gate or block
`/pd-design`. This workflow intentionally does not modify
`phase-discovery.md` itself — that is an explicit pipeline-shape decision for
the user to make.

`/spec-run` calls this workflow in bulk mode as its own Step 2, so an
orchestrated run always has the column populated without any wiring.

---

## Notes for Consumers (`/pe-execute`, `/phase-atomic-execution`)

**After bulk mode**, `plan.md → ## Subtasks` carries a `Model` column and
executors can read it directly. `/spec-run` uses it to pick the model for each
subtask's Implementer agent; if the column is missing or a row is blank, it
falls back to the session default and notes that.

**After single-subtask mode**, nothing is persisted — act on the chat output
yourself: switch your session to that model, or pass it explicitly if your
execution environment supports a per-call model argument.

Column format — added after `Name`, left blank for composite rows (they are
containers and run no agent):

```
| ID   | Name   | Model            | Key Steps (summary) | Depends On | Status      |
|------|--------|------------------|---------------------|------------|-------------|
| T-01 | <name> | claude-sonnet-5  | step1 → step2       | —          | not-started |
```
