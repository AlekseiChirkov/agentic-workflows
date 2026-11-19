## Goal
Every line the tool prints passes one documented escaping boundary that also covers space separators, format characters and quoted values, an output failure has a defined exit, and `render` keeps escaped pipes inside cells, sorts its tables explicitly, refuses a write-protected report, and the economics check no longer scans text copied verbatim into the generated region.

## Context
- Dependencies: T-15.
- Source: improvement proposals of T-04 (P1, P2, P11, P12, P13), T-05 P8 (= T-12 Do Later 3), T-06 (P1, P4, P6, P7, P8), ordered applied by the owner on 2026-11-18. Verified by a read-only planning pass:
  - T-04 P1: no test covers a backslash printed as `\x5c`, U+2028 and U+0085 in a copied string, a `root-unreadable` `ERROR:` line for a file name holding a line break, or a direct `write_lines` call on an `ascii` stream escaping a non-encodable character. Add them (they pin existing behaviour and must pass against the current boundary; record them as characterization tests, not red).
  - T-04 P2: state the escape convention in the module docstring: control, surrogate, line-separator, format and non-encodable characters and the backslash as `\xNN`, `\uNNNN` or `\UNNNNNNNN`; every space separator inside a code or location as its escape.
  - T-04 P11, decision: a failing standard output (EPIPE, ENOSPC) exits 2 with one `ERROR: output-unwritable: …` line on standard error, instead of the interpreter's 120. Test with `/dev/full` (skip when absent) and a closed pipe.
  - T-04 P12: escape every Unicode space separator (category Zs) inside a location, not only U+0020 (scripts/audit-instructions.py:3910).
  - T-05 P8 / T-12 Do Later 3: escape format characters (category Cf: bidirectional controls such as U+202E, zero-width joiner, byte order mark, soft hyphen) at the output boundary.
  - T-04 P13, decision: one `quoted(value)` helper for the quoted message values: delimit with `"` and double an inner `"`. Do not use a `\x22` escape (the backslash rule would re-escape it).
  - T-06 P1: `cell` escapes only `|` (:3109-3111), so source `a\|b` renders as `a\\|b` and the pipe splits the cell in GitHub-flavoured Markdown. Double each backslash run directly before a `|`, then escape the `|`; mirror the fix in the suite's cell model (around suite :4141; recorded amendment: the test-side model encodes the defect).
  - T-06 P6: sort Inventory, Sections, Loads, Defect edges and Legacy rows explicitly by path, line and column instead of relying on extraction order.
  - T-06 P7, decision: `render --write` refuses a report without owner write permission as `report-unwritable` (exit 2) and leaves it unchanged; a writable report keeps its mode. Today it replaces a 0444 report and keeps 0444 (:1621-1642).
  - T-06 P8: cut suite time by refreshing the fixture report only when the assessment bytes changed (around suite :4110-4123); behaviour-neutral; measure the suite time before and after.
  - T-06 P4, decision taken under the owner's order to apply all proposals (recommended option of the planning pass): the economics check of the report skips the lines of the generated region; assessment strings are still scanned at their source and inventory text is a verbatim copy. Today `report_economics_rules` scans every report line (:3667-3674), so an amount copied verbatim from an audited file would make `verify` unpassable.
- Re-render check: after the change, `render` of the delivered outputs must produce a byte-identical report (no backslash in decoded strings; lists already sorted). The delivery gate covers `verify`; also run `render` to a temporary copy and compare.
- Constraints: as T-13. Off-limits: as T-13.

## Scope
- **In scope:** the items above.
- **Out of scope:** audit output content; spec 08 text.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Characterization tests for T-04 P1 (must pass).
2. Failing tests: U+00A0 and U+2003 in a location are escaped; U+202E in a message is escaped; a quoted value holding `"` is doubled; `verify` with standard output on `/dev/full` exits 2 with one `ERROR: output-unwritable` line; source `a\|b` stays one cell; a shuffled inventory renders sorted; `render --write` on a 0444 report is `report-unwritable` and the file is unchanged, a 0640 report keeps 0640; an amount inside the generated region is silent and outside it is still `economics-claim`; docstring phrases.
3. Implement; apply recorded amendments (grep existing expectations that hold a quoted value with `"`; the suite cell model).
4. Suite (record time before and after), delivery gate, byte-identical re-render.

## Acceptance Criteria
- Each behaviour in Step 2 holds and has a test that failed before its implementation; the Step 1 tests pass.
- Only recorded amendments change earlier tests.
- Suite exits 0; the delivery gate prints `GATE PASS`; re-rendering the delivered outputs is byte-identical.

## Test Plan
- **Level:** integration.
- **Scenarios:** as Steps 1–2.
- **Edge cases:** a soft hyphen in a heading text of a location; an empty quoted value; three backslashes before a pipe; a report that is writable by group only.
