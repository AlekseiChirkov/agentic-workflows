# Golden-run tests: behavioural regression tests for the workflows

## Goal

`validate-contracts.sh` checks that files agree with each other; nothing checks that a
workflow, when executed, produces the artifacts the contracts describe. Add a
fixture-based harness that runs selected workflows headlessly against a small project
and diffs the produced `.ai/` artifacts against a normalised expectation (ADR-0009,
Decision 6).

## Acceptance Criteria

- [ ] `tests/fixtures/<case>/` contains a ~5-file pure-Python + pytest project with a
      filled `.ai/` (no FastAPI, no network needs) and a spec; cases: `flat` (3 leaves),
      `composite` (one Type 2 with two children), `quick`, `bugfix`
- [ ] `tests/run-golden.sh <case> <workflow>` copies the fixture to a temp dir, runs the
      workflow through `claude -p` with the model pinned to Sonnet 5, tools allow-listed,
      **no network**, and writes the resulting `.ai/tasks/…` to `tests/out/<case>/`
- [ ] A normaliser strips dates, hashes, free-text `notes:` / `last_action:` values, and
      model-specific prose, leaving structure, statuses, section names, and field presence
- [ ] `tests/expected/<case>/` holds the normalised expectation; the runner diffs and
      exits non-zero on mismatch; `--update` rewrites expectations after a reviewed change
- [ ] Independent assertions: `validate-task.sh` passes on the output; for `flat`, the
      fixture's git history shows test files committed before implementation files
- [ ] Golden runs are executed only before a release (`release.sh` or a documented manual
      step); plain `sync.sh` never runs them
- [ ] A CI workflow runs `validate-contracts.sh` and the shell tests on every push, and
      the golden runs on **manual dispatch only**, with the API key as a repository secret
- [ ] `docs/examples/` (spec 11) is generated from the `flat` fixture run

## Out of Scope

- End-to-end `/spec-run` with real PRs
- Codex execution of golden runs

## Notes

- Decisions: ADR-0009 Decision 6 (release-only, Sonnet 5 pinned, pure-Python fixture,
  offline, manual-dispatch secret, examples from fixture).
- The normaliser is where most of the work is; structure is deterministic under the
  contracts, and that is what is tested.
