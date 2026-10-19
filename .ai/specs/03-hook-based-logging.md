# Drive run-log `step` calls from harness hooks

## Goal

Run 4305eda1 logged all twelve steps at run-end with `duration_s: 0`: the model wrote
the log retroactively because nothing forces a call when a step finishes. Claude Code
hooks execute deterministically; wiring `log-step.sh step` into them makes timestamps
real and removes the per-step logging instructions from the workflows' context
(ADR-0009, Decision 5).

## Acceptance Criteria

- [ ] `harness/claude/hooks.json` declares `SubagentStop` and `Stop` hooks that call
      `hooks/log-step-hook.sh`; the script derives the step name from the invoked skill
      (never from model text), the outcome from the agent's report marker, and the
      `RUN_ID` from the newest open run for the current project (`log-step.sh active`)
- [ ] The hook is installed at **user level** (`~/.claude/settings.json`) by `sync.sh`,
      idempotently and without clobbering existing hooks, and exits immediately unless the
      current directory is in `~/.config/orchestrail/projects`
- [ ] Single-session `/phase-*` runs: steps are detected from the skill name in the
      transcript on a best-effort basis; a step the hook cannot attribute is logged as
      `step: unknown` with a warning
- [ ] `run-start` / `run-end` stay prompt-driven in the orchestrator workflows; the
      per-step `log-step.sh step` instructions are removed from `spec-run`, `phase-*`, and
      `bugfix` for harnesses whose `capabilities.md` declares `hooks: yes`
- [ ] For a harness with `hooks: no` (Codex today) the prompt-driven path remains and
      every step line it writes carries `note: approximate`; `/retro` labels such runs
- [ ] A run executed under the hooks produces step lines whose `duration_s` values sum to
      within 5 % of `run-end.duration_s`
- [ ] `rules/run-log.md` documents both paths and the capability that selects them

## Out of Scope

- Cost/token fields (spec 05); git rails (spec 06)
- Project-level hook installation (rejected: would be committed with consumer repos)

## Notes

- Decisions: ADR-0009 Decision 2 (capabilities, registry) and 5 (user-level hooks,
  `SubagentStop` + `Stop`, run-start/run-end prompt-driven, Codex approximate).
- Depends on spec 02 (vocabulary) and spec 13 (`harness/` layout, capabilities).
- The hook must be fast and must never fail the tool call it observes.
