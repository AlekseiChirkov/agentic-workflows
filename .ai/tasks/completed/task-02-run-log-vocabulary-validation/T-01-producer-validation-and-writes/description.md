## Goal
Make run-log event writes validate the complete argument set, normalize only specified legacy values, and preserve accepted state when an event is rejected.

## Context
- Dependencies: None.
- Constraints: Keep the shell-only producer and optional-`jq` write fallback; all logging errors remain non-blocking with exit code zero.
- Reason: Producer validation and persistence semantics are the foundation shared by later linting and contract checks.

Off-limits: Do not implement the lint command, retrospective reporting, documentation changes, or the acceptance harness.

## Scope
- **In scope:** Validate run-start, step, and run-end arguments; normalize exact step aliases; protect state and metadata from rejected events; check current workflow names with advisory warnings.
- **Out of scope:** Read-only historical-log linting, `/retro`, documentation, contract-drift checks, and test-harness implementation.
- **Target files:** `scripts/log-step.sh`

## Steps
1. Define the producer's allowed enums, count fields and upper bound, and exact legacy mappings in one runtime contract structure.
2. Parse each event's arguments while detecting unknown options, duplicates, missing operands, and a flag consumed as an operand.
3. Validate required arguments, supplied enum values, integer syntax and bounds, and run identifiers before metadata lookup or mutation.
4. Normalize only the exact step outcome and gate aliases, preserving raw values in the required note order.
5. Default omitted or empty run-start flow to `unknown` and persist it consistently in later events.
6. Validate each step event completely before reading or changing sequence and timestamp metadata.
7. Validate run-end completely and keep the active record until the closing line is persisted.
8. Check step names against the current helper workflow directory and synthetic names; warn while retaining valid unknown names.
9. Gate run-start stdout on a persisted start record and usable metadata; keep successful step and run-end stdout empty.
10. Keep write and filesystem failures as single-line warnings with exit code zero and no success-shaped output.

## Acceptance Criteria
- Every invalid event invocation emits one redacted stderr diagnostic, exits zero, and leaves its event file and applicable active metadata unchanged.
- The exact legacy aliases normalize to their canonical values and append `raw:` provenance after any caller note in the specified order.
- Missing and empty run-start flow is stored as `unknown` across start, step, and end records; invalid identifiers are rejected before metadata path lookup.
- Step-name checks use the current helper workflows directory and synthetic names; an unknown nonempty name warns and is still written.
- A failed start prints no run ID; a valid start prints its ID only after persistence; successful step and end calls print nothing; a rejected end leaves the run active so a later valid end can close it.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - Invalid producer arguments → one redacted warning, exit zero, and unchanged file and metadata checksums.
  - Each specified legacy alias and both aliases together → canonical values and ordered raw provenance are stored; `NEEDS WORKING` remains invalid.
  - Missing and empty flow → `unknown` appears in the start, next step, and end records; malformed run IDs cause no metadata lookup or file creation.
  - Known, synthetic, unknown, and unavailable workflow directories → valid events are written and advisory warnings match the case.
  - Failed and persisted starts, successful step and end, and rejected end followed by valid end → stdout is gated as specified, no premature close occurs, and the run closes once.
- **Edge cases:** duplicate options, missing operands, explicit empty enums, boundary counts, failed filesystem operations, and metadata preservation.
