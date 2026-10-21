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
      (never from model text), the outcome from the agent's report marker, and uses an explicit
      run/session/agent correlation supplied at dispatch. It never guesses the run from
      the newest active timestamp or reads the shared store to attribute an event
- [ ] The hook is installed at **user level** (`~/.claude/settings.json`) by `sync.sh`,
      idempotently and without clobbering existing hooks, and exits immediately unless the
      current directory is in `~/.config/orchestrail/projects`
- [ ] Single-session `/phase-*` runs: steps are detected from the skill name in the
      transcript on a best-effort basis; a step name the hook cannot identify may use
      `step: unknown` only when its run is unambiguously correlated; otherwise the event
      is omitted with a coverage warning, never attached to another run
- [ ] `run-start` / `run-end` stay prompt-driven in the orchestrator workflows; per-step
      logging prompts are removed only for step boundaries reliably observed by the
      hook adapter. `hooks: yes` alone does not prove workflow-step coverage; unobserved
      boundaries retain prompt-driven logging and approximate labels
- [ ] For a harness with `hooks: no` the prompt-driven path remains and
      every step line it writes carries `note: approximate`; `/retro` labels such runs
- [ ] A fully covered sequential fixture reports explicit nonoverlapping intervals whose
      sum is within 5 % of run wall time, with uncovered gaps labeled. Nested/parallel
      fixtures report inclusive/exclusive/worker durations separately; their span sum
      is never equated to run wall time
- [ ] `rules/run-log.md` documents both paths and the capability that selects them

## Out of Scope

- Cost/token fields (spec 05); git rails (spec 06)
- Project-level hook installation (rejected: would be committed with consumer repos)

## Notes

- Decisions: ADR-0009 Decision 2 (capabilities, registry) and 5 (user-level hooks,
  `SubagentStop` + `Stop`, run-start/run-end prompt-driven, Codex approximate).
- Depends on spec 02 (vocabulary) and spec 13 (`harness/` layout, capabilities).
- The hook must be fast and must never fail the tool call it observes.

## Review integration — 2026-10-21

### Requirements

- **REQ-01** THE SYSTEM SHALL correlate run/session/agent/checkpoint identities explicitly,
  deduplicate Stop/SubagentStop delivery and preserve completed spec 02's validation,
  non-blocking diagnostics and no-mutation-on-invalid-input behavior.
- **REQ-02** IF hook payloads lack a reliable run, step, outcome or start time, THEN
  THE SYSTEM SHALL report attribution/coverage unavailable or approximate; it SHALL
  NOT parse narrative prose as a definitive outcome or assign another active run.
- **REQ-03** THE SYSTEM SHALL keep active correlation metadata separate from the shared
  historical log store, available through the dispatch envelope. Only retro reads
  that store. Spec 05 owns usage normalization and cost, not the hook adapter.
- **REQ-04** THE SYSTEM SHALL merge only manifest-owned user hook entries, preserve
  user settings, activate only in registered projects and expose capability-based
  fallback. A generic Stop event SHALL not be assumed to occur at every workflow step.
- **REQ-05** THE SYSTEM SHALL test two concurrent runs in one project, duplicate/
  out-of-order events, missing payloads, single-session boundaries and unavailable
  hooks without invoking a model. Duration claims SHALL distinguish gaps, overlaps,
  waiting and actual exclusive work.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02, REQ-03) Interleaved two-run fixtures attribute correctly;
  duplicate deliveries cannot create duplicate accepted events and an ambiguous event
  cannot mutate either run.
- [ ] **AC-02** (REQ-04, REQ-05) Hook install/uninstall fixtures preserve user settings;
  absent capability/payload follows the documented prompt-driven approximate path;
  unobserved step boundaries remain explicitly uncovered.
- [ ] **AC-03** (REQ-05) Sequential/nested/parallel timing fixtures expose the specified
  denominators and never present overlapping worker time as run wall time.

These additions refine correlation and timing, not paid-run authorization. Update the
canonical log rule/adapter contract together. Depends on 02 and 13; 05 consumes the
measurements. Remove step prompts only for boundaries demonstrably observed by hooks.
