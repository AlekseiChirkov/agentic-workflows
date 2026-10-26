# ADR-0012: Decisions for Task unknown — Respect repository knowledge tracking policy

## Status

Accepted

## Date

2026-10-22

## Related Task

- Task: owner-requested correction before hook-based logging.
- Related files: `rules/git-flow.md:24`, `scripts/sync.sh:250`, `workflows/spec-run.md:321`.

## Summary

Accept repositories that track their knowledge base and preserve their tracking policy during synchronization. Keep explicit path staging and ignored local state as the default for new consumers.

## Context

The source checkout intentionally tracks its complete knowledge base, but the preflight and sync contracts reject that same state or advise deleting it from the index. The owner explicitly requested removal of this erroneous prohibition.

## Supersedes

Supersedes ADR-0007's statement that the repository cannot use the orchestrated entry point. Its decision to track the full knowledge base remains in force and is retained here. ADR-0002's default of local consumer state remains applicable where the repository has not elected tracking.

## Decisions

### Decision 1: Follow repository-owned tracking policy

**What was decided:**
Allow tracked knowledge and state during preflight and intentional explicit staging; synchronization never asks the owner to remove tracked knowledge. Preserve the full knowledge base in this repository.

**Why:**
Knowledge tracking is a repository decision and cannot be inferred to be an error from a generic consumer default.

**Alternatives:**
A one-run bypass leaves the same false failure in future runs. Removing knowledge from Git contradicts the owner's selected documentation policy. Blanket staging would mix unrelated state into commits.

**Consequences:**
Preflight remains strict about unrelated tracked changes and branch state. Explicit staging and independent review continue. New consumers retain their ignored-state default.

**Related files:**
- `rules/git-flow.md`
- `scripts/sync.sh`
- `workflows/spec-run.md`

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| May tracked knowledge remain and the current run continue? | The owner approved it and requested removal of the prohibition. | Correct canonical rules and their live readers, then continue the selected specification. |

## Rejected Options

Untracking existing knowledge, a temporary hidden bypass, and blanket staging.

## Implications for Future Work

Repository tracking policy remains authoritative. Do not reintroduce refusal or destructive migration advice in deployment helpers.

## Verification

The real synchronization fixture failed before the change and passes afterward. Independent review passed. Shell syntax and whitespace checks pass. The full suite passed 575 checks and exposed one stale archived-spec ledger path, now corrected; its focused recheck passed.

## References

- Task: owner-requested knowledge tracking correction.
- Pull request: [#22](https://github.com/AlekseiChirkov/agentic-workflows/pull/22).
- Related documents: Git flow contract and knowledge tracking decision.
