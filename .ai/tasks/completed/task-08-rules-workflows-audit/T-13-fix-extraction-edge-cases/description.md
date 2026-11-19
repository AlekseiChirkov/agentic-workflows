## Goal
`extract` and the extraction helpers that `verify` shares handle the remaining edge cases the subtask reviews proposed: an unreadable adapter directory, unreadable unclassifiable directories, deep reader directory chains, the adapter path token boundary, bare home directories, separator rows with trailing whitespace, and the stop marker's case and spans.

## Context
- Dependencies: T-12 (the tool and suite as merged into main at 09fba91).
- Source: improvement proposals of T-01 (P1, P5), T-02 (P1, P4), T-03 (P1, P3, P4) and T-04 (P9), all ordered applied by the owner on 2026-11-18 ("apply all proposals now"). A read-only planning pass verified each claim against the code:
  - T-01 P1: `audited_paths` checks the Codex adapter file with `os.path.lexists(...) and not is_real_directory(...)` (scripts/audit-instructions.py:426); `lexists` returns False on EACCES, so with `templates/` at mode 000 `verify` prints `inventory-stale templates/codex-global-AGENTS.md:0 removed from the root` instead of exiting 2 with `root-unreadable`. Decision: look the file up with `os.lstat`; FileNotFoundError/NotADirectoryError → absent; any other OSError → `root-unreadable` (exit 2, one `ERROR:` line), in both `extract` and `verify`.
  - T-01 P5 + T-04 P9: `reader_paths` walks with `os.walk` and `onerror` raise (:464). An unreadable directory that cannot hold a classifiable reader path refuses the root; and `os.walk` is recursive on Python 3.11, so a reader directory chain deeper than the recursion limit raises there. Decision: replace it with the tool's own explicit-stack walk (as `tree_below` does) that descends only into directories that can hold a classifiable reader path; an unreadable directory that can hold one still refuses the root (the existing test stays).
  - T-02 P1: `TOKEN_PATH_RE` (:886-887) matches `templates/codex-global-AGENTS.md` inside `templates/codex-global-AGENTS.md.bak`, while `rules/a.md.bak` is taken whole. Decision: give the literal the same right boundary as the other path tokens.
  - T-02 P4: the edge fixture uses the real repository heading `## Codebase Reading Rules` in r-one (scripts/check-audit-instructions.py around :897, :1063, :1069, :1389-1399). Rename it to a synthetic heading through a recorded test amendment (reason: the suite contract requires synthetic names). The verify fixtures near :2006 and :3399 keep the real heading because the verifier needs it.
  - T-03 P1: `HOME_PREFIX_RE` (:1214) needs a trailing slash. Decision: also rewrite a bare `/home/<name>` or `/Users/<name>` to `~` when followed by end of text, whitespace, a backtick or punctuation (`.,;:)` and similar); `/home/ alone` (no name) stays unchanged (existing test near suite :1980).
  - T-03 P3: separator rows are matched without removing trailing whitespace (:1314). Decision: match after `rstrip()`; a separator row is never content.
  - T-03 P4: decision: match the stop marker case-insensitively and only outside code spans (use the existing span-removal helper).
- Neutrality: every change must leave the delivered inventory byte-identical when extracted at 8d7e484. The planning pass checked each against the audited bytes (only `/home/<n>/…` forms exist; no separator row with trailing whitespace; the only case variant `**Stop**` at `workflows/pae-tests.md:185` has no call after it; no marker inside a span).
- Constraints: Python 3.11+ standard library only; type annotations on every function; `verify` writes nothing; no new git command; `METHOD_VERSION` unchanged (the schema pins it); diagnostics keep `<code> <location> <message>`; comments, docstrings and test names state rules in words, with no planning identifiers (no subtask, requirement, criterion or specification labels, no `.ai/` paths). Frozen tests: amend only when the test is wrong, and record each amendment with its reason in `notes:`.
- Off-limits: `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, other scripts, every specification, and the three audit outputs under `docs/audits/`. Never read or change installed copies under `~/.claude`, `~/.codex`, `~/.codeium`.

## Scope
- **In scope:** the items above in `scripts/audit-instructions.py`; their tests and the one recorded fixture amendment in `scripts/check-audit-instructions.py`.
- **Out of scope:** git isolation, verifier form rules, output escaping and render (later subtasks); spec 08 text (synced afterwards).
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing tests (one per item): `verify` and `extract` with an unsearchable `templates/` exit 2 `root-unreadable`; `extract` with an unreadable root-level unclassifiable directory exits 0; a reader directory chain of about 1200 levels extracts without a traceback (red is observable with `~/.local/bin/python3.11`; record the interpreter used); `templates/codex-global-AGENTS.md.bak` yields no adapter edge; bare `/home/someone` and `/Users/x` before end of text, a space, a backtick or punctuation become `~` and `/home/ alone` stays; a separator row with trailing whitespace is not a unit; `**Stop**` before a call suppresses it and a `**stop**` inside a code span does not.
2. Apply the fixture heading amendment and record it.
3. Implement each item.
4. Run the full suite and the delivery gate.

## Acceptance Criteria
- Each behaviour in Steps 1 holds and has a test that failed before its implementation.
- The only changed earlier test is the recorded fixture heading rename.
- `MISE_PYTHON_VERSION=3.12.16 python3 -I scripts/check-audit-instructions.py` exits 0.
- `bash <scratchpad>/orch/delivery-gate.sh <WORK_DIR>` prints `GATE PASS` (at 8d7e484 with the new tool both `verify` and `verify --strict` are silent; on the current tree plain `verify` prints exactly the recorded 14 `inventory-stale` lines).

## Test Plan
- **Level:** integration (synthetic fixture roots; subprocess runs of the tool).
- **Scenarios:** as Steps 1.
- **Edge cases:** an absent `templates/` stays silent; a symbolic link named like the adapter file keeps its current classification; `/home/` followed by a slash-less name at the end of a line; a separator row of only dashes and pipes with a tab after it.
