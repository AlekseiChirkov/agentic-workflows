---
trigger: always_on
---

# Quick-Flow tier

Every task runs in one of two tiers, recorded in the top-of-file `flow:` field of the
task `state.md`:

- `flow: full` — the default. The complete Discovery → Execution → Validation pipeline,
  unchanged. When in doubt, this is the tier.
- `flow: quick` — a lighter but still-governed path for small changes that clear the
  escalation gate below. It removes ceremony, never the contract.

The purpose of the quick tier is to give small changes a **real, auditable path** so they
are no longer forced through full decomposition (the `task1_subscription_fix/` case, 23
`fix-NN` directories for often single-file changes) **nor** done outside the pipeline
entirely (the 2026-07-22 "Macro (forex) report defects, ad-hoc fix" case — four behaviour
changes to a shipped pipeline with no contract, no `pv-contract`, no ADR). A quick task is
lighter than the first and governed unlike the second.

This rule does not weaken `workflow-globals → Never auto-advance between phases`, it does not
weaken the ADR trigger, and it does not weaken `workflow-globals → Test-first execution`. It
only removes decomposition and the separate fix-cycle.

---

## The escalation gate

A task may be set to `flow: quick` **only if ALL four conditions hold**. This is a
checklist, not a judgement call — if any one condition fails, the task runs `flow: full`.
No exceptions.

1. **Small surface** — it touches **3 or fewer files, counting test files**. This is a count,
   not an estimate: a fourth file fails the condition and the task runs `full`. The strictness
   costs nothing, because a quick task that turns out to need a fourth file is *promoted* rather
   than failed — see `## Mid-flight escalation (quick → full)` below.
2. **No new invariant** — it introduces no new invariant (nothing that would become a new
   line under `### Invariants` / `domain.md` / `principles/*`).
3. **No behaviour change to an already-shipped pipeline** — see the definition below. *This
   is the condition that would have caught the 2026-07-22 macro fix.*
4. **No schema change** — it requires no DB schema change and no Alembic migration.
   (A migration cannot be undone by a single revert, so migrations are never quick.)

**What "behaviour change to an already-shipped pipeline" means (condition 3).**
A behaviour change is any change to a shipped pipeline's:
- inputs it accepts or rejects (validation, routing, symbol resolution),
- outputs it produces (verdicts, scores, response shape/fields, rendered values),
- data it persists or caches (cache blob contents, cache keys, DB writes),
- control flow (when/whether it calls a provider, ordering of effects), or
- any invariant it upholds.

Explicitly **not** a behaviour change (these stay quick-eligible): log-level or log-message
changes, comments/docstrings, added tests for existing behaviour, dependency-pin bumps with
no code change, and pure UI copy that does not alter what is submitted to the backend.

If the change is to code that has never shipped (still inside the task that created it),
condition 3 does not apply — it is about *already-shipped* pipelines.

---

## The quick path — what changes

**SKIPPED on the quick path:**
- `pd-decompose` — no T-XX split.
- `pd-design` — no 2–3 variant exploration.
- `pd-archive` — nothing verbose to archive.
- Subtask directories and `T-XX/description.md` — there are no subtasks.
- `pv-create-fixes` / `pv-execute-fixes` as separate atomic cycles — review findings are
  fixed inline (see Validation below).

**MANDATORY on the quick path (non-negotiable):**
- **An inline contract in `state.md`, written before any code is touched.** Under a
  `## Contract (quick)` heading, with the same three sub-sections the full path uses, same
  terminology: `### Off-limits`, `### Invariants`, `### Acceptance Criteria`. "No new
  invariant" (gate condition 2) means `### Invariants` lists only the *existing* invariants
  the change must not break — it never adds one.
- **`pv-contract` and `pv-review` still run** — against the inline contract. The verdict is
  recorded in `state.md` exactly as on the full path (`## Contract Check`, `## Code Review`).
- **An ADR is still required whenever a decision is made that a future reader would need to
  understand** — same trigger as the full path, not weakened. A quick task that reaches an
  ADR-worthy decision writes the ADR and links it from `adr/index.md`.
- **The TDD step, run inline.** The quick tier has no T-XX subtasks, so there is no
  `/pae-tests` invocation — but the RED-before-GREEN sequence is identical and mandatory.
  Against `## Contract (quick) → ### Acceptance Criteria`, before touching implementation
  code:
  1. Classify the test level with the gate from the `tdd` rule
     (`unit` → `integration` → `contract` → `smoke` → `none`, first match wins).
  2. Write the failing tests, run the `test:` command, and **observe them fail for the
     expected reason**. A test assumed to fail is not RED.
  3. Record the result in `state.md` under a `## TDD (quick)` heading:
     ```
     ## TDD (quick)
     level: <unit | integration | contract | smoke | none>
     tests: <test names>
     red-observed: <yes — command output summary | n-a — justification>
     green-observed: <yes — after implementation>
     ```
  4. Implement until green. The RED set is frozen exactly as on the full path — no deleting,
     skipping, or weakening without a recorded amendment.

  `level: none` needs the same justification as the full path and the same rejections apply
  ("hard to test", "small change", "will add later", "existing tests cover it"). Note that
  the gate condition 3 exclusions — log-level changes, comments, dependency pins, pure UI
  copy — are exactly the cases that legitimately land on `none`, so on the quick tier `none`
  will be common. That is the gate working, not the rule being bypassed: a change with no
  behaviour change has no behaviour to test.
- **A `progress.md` entry on completion** — same format as a full task.

Because there is no decomposition, the quick contract is the audit trail. The point of the
tier is a *lighter contract, not the absence of one*.

---

## Setting the flow (Discovery)

`flow:` is set during Discovery, by `/pd-analyze`, after Task Analysis has established the
file surface and codebase impact — the facts the gate needs. `/pd-analyze`:

1. Evaluates the four gate conditions against the analysis and records the result in
   `### Assumptions` as one line: `flow: quick|full — gate: 1<pass/fail> 2<..> 3<..> 4<..>`.
2. Writes the top-of-file `flow:` field (see the canonical format in `workflow-globals →
   Canonical Status Formats`).
3. If `flow: quick` — writes the `## Contract (quick)` section instead of proceeding to
   decomposition/design; `/phase-discovery` then skips `/pd-decompose` and `/pd-design`
   and runs `/pd-finalize` directly.
4. If `flow: full` — unchanged behaviour.

Default is `full`. `quick` must be justified by the recorded gate line; an unjustified
`quick` is a validation finding.

---

## Mid-flight escalation (quick → full)

A quick task that, once underway, is found to breach **any** gate condition — a fourth file
proves necessary, an invariant surfaces, a shipped-pipeline behaviour must change, or a
migration is required — **must be promoted to `full`**. It is never silently finished after
a breach. Mechanical steps:

1. Stop implementing at the point of breach.
2. In `state.md`, change `flow: quick` → `flow: full` and add a
   `## Flow Escalation` line: `quick → full | reason: <which condition broke and how> | at: <what was in progress>`.
3. Ensure a full task directory exists (create it if the quick task did not have one) and
   run `/pd-decompose` on the **remaining** work (the inline `## Contract (quick)` becomes
   the seed for the Solution Design / contract; already-done work is recorded as complete).
4. Continue on the full path from Execution.

The promotion is a normal, expected outcome, not a failure — it is the gate doing its job.

---

## Worked example A — rejected by the gate (2026-07-22 macro fix)

The `.ai/memory/progress.md` "Macro (forex) report defects, ad-hoc fix" made four changes
to the **already-shipped** macro pipeline: (1) stopped `macro_metrics` echoing
`price_history`/`technicals`/`news` (response-shape + cache-blob change), (2) moved the news
fetch into `_build_macro_data` and cached it so `/data` returns headlines (control-flow +
caching change), (3) nulled `beta`/`sharpe_ratio_1y` and dropped zero `volume_avg` (output
change), (4) added magnitude-scaled MACD precision (rendered-value change).

Gate evaluation:
- Condition 1 (≤3 files): **FAIL** — `report_builder.py`, `MacroTechnical.tsx`, and more.
- Condition 2 (no new invariant): **FAIL** — "the response carries each field once" and
  "one provider call per report" are new invariants.
- Condition 3 (no shipped-pipeline behaviour change): **FAIL, decisively** — all four
  changes alter outputs, control flow, and cached data of a shipped pipeline.
- Condition 4 (no migration): pass.

Any one failure sends it to `full`; three fail. **Verdict: `flow: full`.** The full path
would have required: a task directory, an inline-or-decomposed contract naming those
invariants under `### Invariants`, decomposition into T-NN, `/pv-contract` + `/pv-review`,
an **ADR** (these were material, revisit-worthy decisions), and a `progress.md` entry —
precisely the governance the out-of-pipeline fix skipped.

## Worked example B — legitimately quick (log-level fix)

Audit item L-05: lower the invoice-body log line in `nowpayments_service.py` from `INFO` to
`DEBUG` (it logged full payloads at INFO).

Gate evaluation:
- Condition 1 (≤3 files): **pass** — one file.
- Condition 2 (no new invariant): **pass**.
- Condition 3 (no shipped-pipeline behaviour change): **pass** — a log-level change is
  explicitly outside the behaviour-change definition; the payment pipeline's inputs,
  outputs, persisted data, and control flow are untouched.
- Condition 4 (no migration): **pass**.

**Verdict: `flow: quick`.** Path: write `## Contract (quick)` — Off-limits: "do not change
IPN control flow or status codes"; Invariants (existing, not new): "V2 IPN signature failure
still returns 403"; Acceptance Criteria: "invoice body no longer logged at INFO; DEBUG line
present; existing payment tests still green" — then the inline TDD step, then implement, run
`/pv-contract` + `/pv-review`, and add the `progress.md` entry. No ADR (no reader-relevant
decision). Done in one light cycle instead of a `fix-NN` directory.

TDD step for this example: the gate returns `none` — a log-level change alters no input,
output, persisted data, or control flow, so there is no behaviour to assert. `## TDD (quick)`
records `level: none`, `red-observed: n-a — log-level change only; unit/integration/contract
have no behaviour to assert, smoke has no validating tool for log levels`. The Acceptance
Criterion "existing payment tests still green" is then covered by the regression run, not by
a new test.
