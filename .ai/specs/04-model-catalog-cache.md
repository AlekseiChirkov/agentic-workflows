# Hand-maintained model catalog with two candidates per subtask

## Goal

`/pd-select-model` rebuilds its model catalog from a live web search on every run and is
4 200 words long; in run b905a8a5 the step took 3 h. Replace the search with a
hand-maintained, cached catalog, reduce selection to a cost-tier table, and record two
candidate models per subtask — one for a Claude-orchestrated run and one for a
Codex-orchestrated run (ADR-0009, Decision 6).

## Acceptance Criteria

- [ ] The catalog lives at `~/.config/orchestrail/model-catalog.md` with a `refreshed:`
      date; the workflow reads it when younger than 14 days, prints a staleness warning
      after 30 days, and performs a web refresh only on `--refresh`
- [ ] The catalog is a table `tier | anthropic model id | openai model id | relative
      cost`, with tiers `light | standard | frontier`; tier equivalence between providers
      is by cost band
- [ ] `plan.md → ## Subtasks` gains two optional columns, `Model (Claude)` and
      `Model (Codex)`, written by `/pd-select-model` in bulk mode; an empty cell means
      the session default; readers (`validate-task.sh`, `/spec-run` Step 2 and 4) tolerate
      absence of either column
- [ ] Selection is by cost tier from the subtask's signals, with an optional trait
      override column value (`creative | heavy-reasoning | mechanical`) that maps to a tier
- [ ] The workflow is ≤ 1 500 words; removed rationale moves to `rules/reference/` or is
      deleted; the prohibition on a persisted catalog is replaced by the TTL rule
- [ ] `/spec-run` Step 2 takes under 60 s wall-clock with a fresh cache (run log)
- [ ] `validate-contracts.sh` checks the column names and the tier vocabulary

## Out of Scope

- Automatic model switching mid-subtask
- A Codex `/spec-run` orchestrator (a later spec; the second column already serves
  single-session runs started from Codex)

## Notes

- Decisions: ADR-0009 Decision 6 (catalog location, TTL, hand-maintained, cost tier +
  trait override, two columns).
- Independent of the 02 → 06 chain; may run any time after spec 13.
