## Goal
Provide versioned source profiles and counter normalization with observable, deterministic behavior.

## Context
- Dependencies: T-01g — producer schema export follows the completed shared schema registry.
- Constraints: Follow the specification sections Counter normalization; AC-01, AC-02; use synthetic offline evidence, preserve unknowns and existing lifecycle behavior.
- Reason: This component has its own independently verifiable output and coherent acceptance cluster.

Off-limits: Paid model calls, automatic model changes, implicit historical discovery, rewriting existing evidence and unrelated components.

## Scope
- **In scope:** versioned source profiles and counter normalization, including all applicable requirements and negative cases in Counter normalization; AC-01, AC-02.
- **Out of scope:** Implementation of other telemetry components and changes to unrelated lifecycle contracts.
- **Target files:** scripts/usage_telemetry_contract.py, tests/usage-source-profiles.py, harness/claude/capabilities.md, harness/codex/capabilities.md.

## Steps
1. Define versioned synthetic profile evidence and counter semantics.
2. Normalize included and separate input categories without adding reasoning twice.
3. Detect cache split, negative remainder and reasoning conflicts while retaining unaffected values.

## Acceptance Criteria
- Split cache-write measurements retain nonoverlapping TTL/token components; their sum matches any reported total, while a mismatch is conflicted and never double-counted.
- A valid split cache-write observation and its containing bundle pass the shared schema, retain evidence per component and canonicalize TTL ordering; duplicate TTLs or conflicting totals cannot yield a complete value.
- Included input 1000 with cache read 200 normalizes to uncached 800; separate categories produce the same totals.
- Unsupported profiles are unavailable; conflicting or unproved cache fields never become an invented zero.

- A cache write split that disagrees with its total or reasoning that exceeds output marks the affected measurement conflicted.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - Normalize short and long cache-write entries with matching and conflicting totals → preserve matching split once and report conflict for a mismatch.
  - Validate a bundle with split cache writes in both TTL orders → identical canonical output; duplicate TTL or inconsistent total → explicit conflict or rejection.
  - Included input 1000 with cache read 200 normalizes to uncached 800; separate categories produce the same totals. → the stated result is observed.
  - Unsupported profiles are unavailable; conflicting or unproved cache fields never become an invented zero. → the stated result is observed.
  - A cache write split that disagrees with its total or reasoning that exceeds output marks the affected measurement conflicted. → the stated result is observed.
- **Edge cases:** empty and unavailable data, boundary values, duplicate operations, invalid input, dependency failures and permissions where applicable.
