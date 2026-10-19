# Enforce the run-log field vocabulary in `log-step.sh`

## Goal

`rules/run-log.md` defines an enum for `outcome`, `tests`, `promoted`, and a required
`flow`, but `log-step.sh` writes whatever it is given. Four of the ten runs in
`logs/runs/` carry values outside the vocabulary (`completed`, `implemented`,
`restarted`, `needs-work`; free text in `gate`; empty `flow`). `/retro` metrics over
this corpus are noise. The helper must normalise known drift and reject the rest so the
store stays countable (ADR-0009, Decision 5).

## Acceptance Criteria

- [ ] `log-step.sh step` normalises, with the original value copied into `note` as
      `raw:<value>`: `outcome` `completed`→`ok`, `implemented`→`ok`,
      `restarted`→`failed`, `needs-work`→`failed`; `gate` `PASS`→`pass`,
      `NEEDS WORK …`→`needs-work`, `escalated`→`fail`
- [ ] Any other value outside `outcome ∈ ok|blocked|failed|skipped|deferred`,
      `tests ∈ red|green|n-a|failed|not-run|pinned`, `promoted ∈ yes|no`,
      `run-end --outcome ∈ completed|stopped|failed|abandoned`, or a non-integer count
      writes nothing, prints one warning line to stderr, and exits 0
- [ ] `run-start` without `--flow` writes `flow: "unknown"`, never an empty string
- [ ] `--step` values not matching a basename in `workflows/*.md` (resolved via
      `ORCHESTRAIL_HOME`) or a documented synthetic step (`batch-gate`, `subtask`,
      `dry-run`) are written with a warning, not rejected
- [ ] `pinned` is added to the `tests` enum and the normalisation map is documented in
      `rules/run-log.md → ## Field vocabulary`
- [ ] `log-step.sh lint [<run-id>|--all]` reports vocabulary violations in existing files
      without modifying them; the ten historical runs are left as-is
- [ ] `/retro` Step 1 reports lines rejected by `lint` as part of the corpus description
- [ ] `validate-contracts.sh` checks that the enum lists and the map in `log-step.sh` and
      `rules/run-log.md` are identical
- [ ] `tests/log-step.sh` exercises every branch above against a temporary
      `ORCHESTRAIL_LOG_ROOT` and is the first executable test in `tests/`

## Out of Scope

- Rewriting historical log files
- Token/cost fields (spec 05); hook-driven calls (spec 03)

## Notes

- Decisions: ADR-0009 Decision 5 (normalisation map, warn on unknown step, leave history).
- Clarifications 2026-09-17: normalise known drift rather than drop; unknown values
  rejected; step list derived at call time.
- The never-block rule stands: exit 0 on every path.
- Test level: `smoke` — the bash test script is the validating tool.
- Order: first of the 02 → 03 → 05 → 06 chain (ADR-0009 Decision 7).
