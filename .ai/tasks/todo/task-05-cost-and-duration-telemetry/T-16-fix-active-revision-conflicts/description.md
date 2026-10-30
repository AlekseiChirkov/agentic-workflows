## Goal
Apply counter conflict restrictions to active selected revisions while retaining valid corrections.

## Context
- Independent PR #54 recheck found the resolver scans superseded historical observations.
- A verified correction must retain the existing corrected input and exact cost.

## Scope
- **In scope:** conflict evaluation after active revision and snapshot selection, and behavioral regressions.
- **Out of scope:** counter schema redesign, weakened authority checks and unrelated pricing changes.
- **Target files:** scripts/usage_telemetry_resolution.py, tests/usage-resolution-revisions.py.

## Steps
1. Reproduce the rejected valid correction through the existing revision fixture and record RED.
2. Restrict conflict propagation to active independently selected evidence without restoring unresolved quantities.
3. Verify corrected and unresolved cases, output, streams and pricing; retain separate test and fix commits.

## Acceptance Criteria
- A verified correction superseding a conflicted snapshot restores its evidenced input and exact pricing.
- Unresolved active conflicts remain unavailable; revision authorization, stream finality and independent output remain intact.

## Test Plan
- **Level:** integration
- **Scenarios:** superseded conflicted final snapshot with verified correction; the same without authorization; active unresolved conflict; ordinary correction and stream paths.
- **Edge cases:** earlier records, evidence ordering, final snapshots, independent output and exact cost.
