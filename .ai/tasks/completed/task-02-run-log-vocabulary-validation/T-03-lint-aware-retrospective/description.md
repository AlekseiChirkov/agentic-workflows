## Goal
Make retrospective reports disclose lint coverage and exclude invalid log lines from every downstream metric.

## Context
- Dependencies: T-02, because the workflow consumes the linter's per-file diagnostics and summary.
- Constraints: Keep existing filters, the fewer-than-five-runs warning, honesty rules, and recommendation-only behavior.
- Reason: Metrics must identify unusable telemetry instead of treating invalid values as measurements.

Off-limits: Do not change producer or lint semantics, historical records, or recommendation-only behavior.

## Scope
- **In scope:** Filter-aligned linting, corpus coverage and violations, metric exclusions and denominators, incomplete-run labels, and correct abandonment classification.
- **Out of scope:** Producer validation, linter implementation, vocabulary tables, drift checks, and acceptance-harness implementation.
- **Target files:** `workflows/retro.md`

## Steps
1. Add `lint --all` to the load step and match its per-file diagnostics to the same files selected by existing filters and limit.
2. Define the corpus report fields for total runs, examined event lines, invalid lines, affected runs, violations by field and code, and up to five examples.
3. Require an explicit `partial` or `unavailable` disclosure when lint did not examine the full corpus.
4. Exclude lint-invalid lines from every downstream metric and describe denominators using usable observations only.
5. Label affected runs as having incomplete telemetry and disclose metric effects from exclusions.
6. Count abandoned runs only when the physical run-end event is absent; report a present but invalid end as an unusable close.
7. Preserve the fewer-than-five-runs warning, existing honesty rules, and recommendation-only behavior.
8. Update the report template and reporting instructions to include the lint findings and exclusions.

## Acceptance Criteria
- Lint diagnostics are intersected with exactly the file corpus selected by `--since`, `--pipeline`, `--project`, and `--limit`.
- The corpus report includes all required counts, field/code violation totals, up to five safe examples, and incomplete lint status when applicable.
- Invalid lines are excluded from metric numerators and denominators; affected runs and resulting limitations are disclosed.
- Missing physical end events count as abandoned, while present invalid end events count as unusable closes.

## Test Plan
- **Level:** contract, smoke
- **Scenarios:**
  - Apply each corpus filter with lint diagnostics → only matching file diagnostics appear in the corpus report.
  - Feed clean, invalid, and unreadable files → required counts, affected-run totals, grouped violations, examples, and incomplete status are reported.
  - Include invalid lines alongside valid measurements → metric numerators and denominators use only valid observations and disclose exclusions.
  - Compare absent run-end and invalid run-end records → only the absent physical event increments abandoned runs.
- **Edge cases:** Fewer than five runs, all-invalid corpus, incomplete lint, no invalid rows, and filters selecting no files.
