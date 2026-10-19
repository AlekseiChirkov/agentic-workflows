# Token, cost, and duration telemetry with anomaly warnings

## Goal

Spec runs take 21–26 h; one subtask took 15.4 h; an Implementer was terminated by a
spend limit. The run log cannot say what a run cost, and nothing flags an abnormal
subtask while it is happening. Record tokens, cost, and duration per step and per run,
warn on anomalous duration, and give `/retro` cost metrics. Nothing in this spec stops a
run (ADR-0009, Decision 5 — budgets were rejected).

## Acceptance Criteria

- [ ] `log-step.sh step` accepts `--tokens-in N --tokens-out N --cost-usd X`; `run-end`
      sums them into `tokens_in`, `tokens_out`, `cost_usd`; `rules/run-log.md` documents
      the fields and that an omitted field means "not measured"
- [ ] On a harness with `hooks: yes`, the hook from spec 03 fills the token and cost
      fields from the harness payload; on `hooks: no` (Codex) the fields are omitted, never
      estimated
- [ ] Anomalous-duration warning: while fewer than 5 samples exist for a step name in the
      log store, a step longer than 2 h is flagged; from 5 samples on, a step longer than
      3× that step's median **and** longer than 2 h is flagged
- [ ] The flag is written as `telemetry: anomalous duration — <step> <duration> vs
      <threshold>` to the subtask's `notes:` (by the orchestrator, not a sub-agent) and
      listed in the pipeline's final report; the run continues
- [ ] `/retro` computes median and p90 `cost_usd` and `duration_s` per run, per pipeline,
      and per step; lists the five most expensive subtasks by tokens; reports how many
      runs lack cost data and why
- [ ] `docs/SPEC-RUN-QUICKSTART.md` documents the telemetry fields and the warning

## Out of Scope

- Any budget, cap, timeout, or automatic stop (rejected by the owner)
- Optimising a workflow's token use (spec 08)

## Notes

- Decisions: ADR-0009 Decision 5 (telemetry-only; threshold rule; Codex cost omitted).
- Clarifications 2026-09-17: the original budget requirements were withdrawn in full;
  the spec was renamed from `subtask-budgets-and-cost-telemetry`.
- Depends on spec 02 (vocabulary) and spec 03 (hook payloads for real token counts).
