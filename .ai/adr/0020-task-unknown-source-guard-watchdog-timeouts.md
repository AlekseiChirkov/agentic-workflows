# ADR-0020: Decisions for Task unknown — Source guard timeouts are watchdogs, not budgets

## Status

Accepted

## Date

2026-11-13

## Related Task

- Task: owner-requested repair of the contract suite before deployment.
- Related files: `tests/validator-runtime-guard-regressions.py`,
  `tests/validator-runtime-integrated.py`, `tests/validator-runtime-oracle.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`.

## Summary

Subprocess timeouts around the nested source guard scan protect against hangs; they do
not assert performance. They are raised to 30, 90 and 180 seconds along the chain
oracle → integrated wrapper → guard scan, and the guard exceptions are re-pinned under
the fixture maintenance procedure.

## Context

The full guard scan takes about 7.6 s on Python 3.14 and 9.3 s on Python 3.12 on the
owner's machine, single-threaded and independent of load, while the regression test
allowed 5 s. The wrapper that runs the scan and the guard suites takes about 23 s
against a 15 s limit, and the oracle wraps that wrapper in another 15 s limit. The suite
therefore failed on a correct tree. The bounded validator runtime decision keeps
performance budgets out of ordinary-suite wall assertions and lists changed suite
timeouts among options rejected as a means of meeting its speed goals.

## Decisions

### Decision 1: Raise the watchdogs, keep every assertion

**What was decided:** Raise the guard CLI scan timeout from 5 to 30 s, the integrated
wrapper from 15 to 90 s and the oracle's integrated run from 15 to 180 s. No assertion,
coverage or classification is changed.

**Why:** A wall-clock limit tighter than the measured duration fails correct code; the
runtime decision already places budgets in measurement records, not suite assertions.
This does not claim any runtime improvement, so it does not use the rejected option to
meet a speed goal.

**Alternatives:** Speed up the guard scan to fit 5 s — rejected for now: unknown effort
and risk to scan logic, and the re-pinning cost is the same. Leave the suite failing —
rejected: it blocks every deployment.

**Consequences:** A genuine hang still fails, after up to 30–180 s. Scan speed remains
measured separately.

### Decision 2: Re-pin only the reviewed records

**What was decided:** Recompute the inventory fingerprint after the three edits, update the
133 `inventory_sha256` fields and the three `context_sha256` records whose functions
changed, then update the manifest digest in the guard.

**Why:** The fixture procedure requires reviewed, exact updates; the diff contains only the
three timeout literals, with no new call site and no dependency on the changed files.

**Consequences:** The guard, its regression, executable and external-source suites, the
integrated registrations and the inventory oracle pass.

## Verification

Before: the guard regression test timed out at 5 s on a clean checkout. After: guard
7.4 s, regression suite 8 s, integrated 23 s, oracle 68 s, all passing.
