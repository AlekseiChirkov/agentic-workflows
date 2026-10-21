## Goal
Add a read-only lint command that validates selected historical run-log files and emits stable JSON diagnostics and a summary.

## Context
- Dependencies: T-01, because lint must reuse the producer's runtime vocabulary and mappings.
- Constraints: Require `jq` only for lint; never create the log store or rewrite logs, digests, or active metadata; always exit zero.
- Reason: The retrospective needs reliable validation of historical records without migrating them.

Off-limits: Do not edit historical files, change producer behavior outside the shared runtime contract, or update `/retro`.

## Scope
- **In scope:** `lint`, `lint --all`, and run-ID selection; deterministic file and line ordering; record validation; JSON diagnostics and accurate status summaries.
- **Out of scope:** Retrospective filtering and metrics, documentation and drift validation, and acceptance-harness implementation.
- **Target files:** `scripts/log-step.sh`

## Steps
1. Add lint argument handling for no arguments, `--all`, and one safe eight-character run ID; reject unsupported combinations without failing the caller.
2. Select matching JSONL files in lexicographic filename order without consulting active metadata.
3. Avoid creating the store and handle absent corpus, missing `jq`, and unreadable files as specified.
4. Read each selected file in ascending line order and parse each line as a JSON object.
5. Validate common fields, event-specific required fields, field types, enums, exact legacy-alias rejection, and integer bounds using the shared runtime contract.
6. Emit one newline-delimited JSON violation object per issue without including invalid values.
7. Track examined files and lines, distinct invalid lines, total violations, and `ok`, `partial`, or `unavailable` status.
8. Emit exactly one summary object for every invocation, including empty and no-match corpora.
9. Ensure lint does not alter JSONL, digest, or active metadata contents.

## Acceptance Criteria
- No argument and `--all` lint every run file; a valid run ID selects all matching files; no-match and empty-store cases return an `ok` zero-count summary.
- Each invalid JSONL record produces stable JSON diagnostics in filename and line order, with valid codes and no raw field values.
- The final summary counts examined files and lines, distinct invalid lines, and violations accurately and reports incomplete checks as `partial` or `unavailable`.
- Lint always exits zero and leaves all selected and unselected logs, digests, and active metadata unchanged.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - No-argument and `--all` invocation → every file is visited in sorted order and exactly one summary ends output.
  - Valid run-ID and no-match run-ID → all matching files are visited, or a zero-count `ok` summary is returned.
  - Malformed JSON, invalid objects, missing fields, wrong types, aliases, invalid enums, and invalid integers → stable violation objects and accurate distinct-line and issue counts.
  - Missing `jq` and unreadable files → warning plus `unavailable` or `partial`, never a clean result for unchecked records.
  - Lint over active and closed runs → checks records while preserving checksums of JSONL, digest, and active metadata.
- **Edge cases:** Empty corpus, malformed identifier, active runs without active metadata, one line with multiple violations, and final line without a newline.
