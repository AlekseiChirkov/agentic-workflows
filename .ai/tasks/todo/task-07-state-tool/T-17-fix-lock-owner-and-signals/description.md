## Goal
The busy refusal reports an owner only when the whole lock file is one reportable JSON object and an age only when it is a real elapsed time, and a signal that ends the process behaves as a silent kill.

## Context
- Origin: owner request of 2026-11-16 to close every deferred improvement proposal and optional review finding of this task. Each item was verified against the code and decided by an independent analyst; the decisions below are the contract of this subtask and are implemented exactly as worded. Item ids name the proposal section and its ordinal (N = Do Now, L = Do Later, O = Optional; I<n> = issue list entry).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`; exit codes 0–8 and the error-code and warning-code tables stay closed (no decision adds a code). No existing test is deleted, renamed, skipped or weakened; new cases are new test methods or new subtests. English only; no planning identifiers or specification labels (requirement, criterion, invariant, decision, assumption, constraint or question labels) in code, tests, comments, messages or documentation.
- Test-first: every decision marked as a behaviour change has failing tests first, observed failing for the stated reason, committed before the implementation. Guard tests (pass before the change) are allowed when named with their mutation evidence. Refactoring is covered by the existing suite, green before and after.
- Pinned fixtures: a change to `tests/state-tool.py`, `scripts/state-tool.py` or another pinned script invalidates pinned digests (see `tests/fixtures/validator-runtime/README.md`); refresh them once after the last source edit. Do not add or remove lines of `docs/USAGE.md` above line 255: the repository's identity ledger pins that line. Never write the ledger's heading line into any file.
- Specification, ADR and knowledge-base sentences named in the decisions are written by the orchestrator at reconciliation, not in this subtask; manual (`docs/USAGE.md`), rule-file and tool-docstring sentences are in scope where the decision names them.

Off-limits: no file under `workflows/`; no deployed copy under the home directory; no change to the oracle mechanism beyond refreshing pinned values; no new exit, error or warning code; no amendment of an existing test.

## Scope
- **In scope:** `read_lock_owner`, `owner_details`, the `__main__` block, the module description, their suite cases and the manual sentences the decisions give.
- **Out of scope:** any signal handler installed at start-up; removal of a temporary file on a signal; a new exit or error code.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`, `docs/USAGE.md`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Read every decision below and the code it names; line numbers quoted in the decisions may be stale, locate by function or test name.
2. Add the suite cases the decisions name; for each behaviour change observe the failure and its reason; for each guard case record its mutation evidence.
3. Implement each decision exactly as worded; keep the frozen tests byte-identical.
4. Apply the document sentences that are in scope.
5. Refresh the pinned fixtures once after the last source edit and run the suite, the focused validator mode, the inventory oracle suite and the source-guard suites.

## Acceptance Criteria
- Each decision below marked APPLY holds exactly as its `Decision:` paragraph states (inputs, exit code, error code, result, bytes written, message), within this subtask's scope.
- Every behaviour change has a test that failed before the implementation for the stated reason; every guard case is named with mutation evidence.
- All tests that existed before this subtask pass unchanged.
- The suite, `bash scripts/validate-contracts.sh --state-tool-only`, the inventory oracle suite and the source-guard suites pass with the refreshed pinned values.
- No line of `docs/USAGE.md` above line 255 moved.

## Test Plan
- **Level:** integration (subprocess runs of the tool and the scripts against disposable fixtures), unit where a decision names an in-process case, smoke for manual and rule sentences.
- **Scenarios:** the cases each decision below names, with the expected exit code, error code, result and bytes.
- **Edge cases:** the boundary inputs each decision names; existing tests unchanged.

## Notes for this subtask
The single owner rule that L2–L5, N1, N2 and O3 all follow (call it RULE-OWNER):
- `lock_owner` is the parsed content of the lock file when the WHOLE file is at most 65536 bytes, is valid UTF-8, parses as exactly one JSON object, is nested at most 16 levels (the top object is level 1; an empty object or list counts as a level), holds only finite numbers the interpreter can convert, and can be written again as strict UTF-8 JSON (no lone surrogate in any key or value). Otherwise `lock_owner` is null. A repeated key is not a reason for null: it is reported with its last value.
- `lock_age_seconds` is the whole number of seconds since `started_at` when the owner is reported, `started_at` is an ISO-8601 string with a UTC offset, and that time is not in the future. Otherwise null. It is therefore never negative.
- `stale_suspected` is true only when `lock_age_seconds` is an integer of 600 or more.
- None of this ever changes the refusal itself: exit 5, `lock-busy`, lock file untouched.

## Decisions

### T-03 L2 + T-08 L1

T-03 L2 + T-08 L1 — APPLY — a signal that ends the process is treated as a kill: no handler, no JSON, no table exit code, silent stderr
Evidence: Reproduced on a scratch task. SIGINT while waiting on a held lock: status -2, empty stdout, a `KeyboardInterrupt` traceback on stderr, `state.md` and lock file untouched, no temporary file. SIGTERM and SIGHUP while waiting: status -15 / -1, empty stdout, empty stderr. SIGINT and SIGTERM during `pause-before-recheck` (between the temporary file and the rename): same statuses, `state.md` unchanged, one `.state.md.<token>.tmp` left; a later command lists it and an identical retry is `applied`. `main` catches `Exception` only (line 1804), and no handler is installed. What the spec already promises: REQ-12 (leftover files listed in `stale_temp_files`, never read as state, never deleted unless created by this process), the edge rows "Killed before or after replace → whole old or whole new file; retry gives `applied` or `already_applied`" and "Leftover temporary files → reported, not deleted", REQ-07 (own temporary file removed on a create/write/sync/rename FAILURE, not on a kill), and the manual ("a write killed before the rename leaves `state.md` unchanged (its temporary file stays ...)"). So a leftover temporary file after an interruption is already a specified, tested outcome.
Decision: Ruling — a signal whose default action ends the process (SIGINT, SIGTERM, SIGHUP, SIGQUIT, and SIGKILL as today) is an interruption in the sense of the existing recovery requirements, at every point of a command, including the lock wait.
- Inputs → outcome: any command + such a signal → the process ends by that signal (subprocess status `-signal`; a shell shows 128+N). No exit code from the table 0–8 is produced, no JSON object is printed, stdout is empty, and stderr is empty (no traceback). No new error code; the exit-code and error-code tables are unchanged.
- SIGTERM is covered as well as SIGINT, by the same rule; the tool installs no signal handler for either.
- Own temporary file: NOT removed on a signal. If the signal arrives between step 10 and the rename, the file stays, is listed in `stale_temp_files` by every later command, is never read as state, and is removed by hand (existing REQ-12 and manual limit). `state.md` is the whole old file (signal before the rename) or the whole new file with its receipt (after). The kernel releases the lock. Recovery is the existing one: repeat the identical command → `applied` or `already_applied`.
- The only behaviour change: SIGINT must end the process as silently as SIGTERM. Required mechanism constraint: do not change the signal disposition at start-up (the suite runs the tool in-process through `runpy` with `run_name="__main__"`, so a start-up change would leak into the test runner); instead, where the script calls `main`, catch `KeyboardInterrupt`, restore the default SIGINT action and re-send SIGINT to the own process. Trialled in scratch `v2`: status -2, empty stdout and stderr in both phases.
- Files: `scripts/state-tool.py` (the `__main__` block; one sentence in the module description), `tests/state-tool.py`, `.ai/specs/07-state-tool.md`, `docs/USAGE.md`. Behaviour change → failing test first.
- Tests (new class or in `InterruptionRecoveryTests`; no existing test changes): (a) RED today — SIGINT sent to a `set` waiting on a held lock (`hold_lock`, `--lock-wait-seconds 20`): status `-SIGINT`, stdout `""`, stderr `""`, task directory snapshot unchanged, no temporary file. (b) RED today — SIGINT sent to a `set` paused by `pause-before-recheck`: status `-SIGINT`, stdout `""`, stderr `""`, `state.md` bytes unchanged, exactly one temporary file, `validate` lists it in `stale_temp_files`, identical retry is `applied` once and the leftover file is byte-identical afterwards. (c) guards, pass today — the same two cases with SIGTERM. Both red cases fail today only on the stderr assertion (the traceback), which is the right reason.
- Spec sentence, new row in `## Edge Cases & Failure Modes`: "| A signal that ends the process (SIGINT, SIGTERM, SIGHUP, SIGQUIT), at any point including the lock wait | Same as a kill: no signal handler, no JSON object, nothing on stderr, no exit code from the table (the process ends by the signal); `state.md` is the whole old or the whole new file; a temporary file already created stays and is listed in `stale_temp_files`; the kernel releases the lock; retry gives `applied` or `already_applied` | REQ-07, REQ-08, REQ-12 |". Under `### Exit codes and error codes` add: "A process ended by a signal prints no JSON object and has no exit code from this table; the caller recovers by repeating the identical command."
- Manual sentence (`docs/USAGE.md`, section 11, after "a write killed after the rename is answered `already_applied`."): "An interrupt (Ctrl-C) or a termination signal counts as a kill: the tool ends by the signal without a JSON object, an exit code from the table or a traceback, also while it waits for the lock."
- Module description sentence: "A signal that ends the process is treated as a kill: no JSON object and no exit code of this table; a temporary file already created stays behind."
Why: Options — (1) signal = kill, silent, no handler [winner]: simplicity 5, reversibility 5, spec fit 5 (reuses REQ-07/08/12 unchanged), testability 4, blast radius 1 line; (2) handlers for SIGINT and SIGTERM that print one JSON object, exit 7 with a NEW code `interrupted` and remove the own temporary file: simplicity 2, spec fit 2 (no existing code fits — it is neither `io-error` nor `lock-busy`, so the closed table would grow), testability 2, and a real honesty risk (a signal after the rename would be reported as `rejected` for an applied write, or would add a second JSON object during output); (3) clean up the temporary file, then die by the signal: simplicity 3, small gain only, because the file exists for milliseconds while the wait (up to 600 s) is where interrupts land and nothing is on disk then. Option 1 fails closed (no output and a non-zero status can never be read as success) and adds no second recovery path.

### T-08 L2

T-08 L2 — APPLY — a start time in the future gives `lock_age_seconds: null`
Evidence: Reproduced: `started_at` one hour ahead → `lock_owner` reported, `lock_age_seconds: -3599`, `stale_suspected: false` (`owner_details`, line 1435). No existing test pins a negative age.
Decision: When the difference between now and `started_at` is negative, `lock_age_seconds` is null and `stale_suspected` is false; `lock_owner` is still reported unchanged. Exit 5, `lock-busy`, JSON keys unchanged. Decide on the unrounded difference (negative `total_seconds()` → null) before converting to an integer. Trialled in scratch `v4`.
Files: `scripts/state-tool.py` (`owner_details`), `tests/state-tool.py`. Behaviour change → failing test first: owner with `started_at` 3600 s in the future, zero wait → `lock_owner == owner`, `lock_age_seconds is None`, `stale_suspected is False`, snapshot unchanged (fails today with -3599). No existing test changes (`test_owner_details_follow_the_recorded_start_time_with_a_zero_wait` uses 5 s in the past). Spec/manual text: covered by the N2 sentences.
Why: Options — as it is (negative): zero cost but an "age" below zero is not an age and the spec types the key as "integer or null" meaning elapsed time; zero: hides a clock disagreement behind a value that looks measured; null [winner]: matches the spec rule "a key that cannot be computed is present with the value null", one line, and the caller still sees `started_at` in the owner.

### T-08 L3

T-08 L3 — APPLY — a lock file longer than 64 KiB is always a null owner
Evidence: Reproduced: a complete 65536-byte object followed by "\ngarbage" (or by one newline) is reported as that object, because `read_lock_owner` (line 1407) reads only the first `LOCK_METADATA_LIMIT` bytes. A small object followed by junk is already null.
Decision: Read at most `LOCK_METADATA_LIMIT + 1` bytes; when more than `LOCK_METADATA_LIMIT` bytes come back, the owner is null (age null, stale false). Do not compare with `fstat` size (a second call and a race for nothing). A file of exactly 65536 bytes is still parsed. Trialled in scratch `v4`.
Files: `scripts/state-tool.py` (`read_lock_owner`), `tests/state-tool.py`. Behaviour change → failing test first: a 65536-byte object plus `b"\n"` and plus `b"\ngarbage"` → `lock_owner is None` (both fail today). Existing tests unaffected (`LockMetadataRobustnessTests` asserts its cases are under 65536 bytes). Spec/manual text: N2 sentences ("the whole file").
Why: Options — keep the prefix reading: reports as "the recorded owner" something the file does not hold; `fstat` size check: same result with an extra call; read one byte beyond the limit [winner]: three lines, bounded memory as before, and it makes the rule statable as "the whole file".

### T-08 L4

T-08 L4 — APPLY — metadata with a lone surrogate is a null owner
Evidence: Reproduced: `{"k":"\ud800"}` and `{"\udc00":1}` are echoed with the same escape; stdout is ASCII and parses, but the parsed value cannot be encoded as UTF-8 by a strict consumer. The existing check `json.dumps(metadata, allow_nan=False)` (line 1411) passes such text.
Decision: The owner is null (age null, stale false) when the parsed object cannot be written as strict UTF-8 JSON. Implement by making the existing re-serialization the one reportability check: serialize without ASCII escaping and with non-finite numbers refused, then encode as UTF-8; a failure is already inside the caught `ValueError` family. Exit 5, `lock-busy`. Trialled in scratch `v4`.
Files: `scripts/state-tool.py` (`read_lock_owner`, one line and its comment), `tests/state-tool.py`. Behaviour change → failing test first: lone surrogate in a value and in a key → exit 5, stdout decodes as UTF-8 and is one strict JSON object, `lock_owner is None`, `lock_age_seconds is None`, `stale_suspected is False` (the owner assertion fails today). This replaces the surrogate pin proposed in N1. No existing test changes.
Why: Options — keep the echo: valid JSON text, but the one place where the tool emits a value a strict consumer rejects, from a file the tool did not write; replace the bad code points: reports text the file does not hold; null [winner]: fits the name and intent of the existing test group ("metadata that cannot be reported as standard JSON reports no owner"), costs one line and fails closed.

### T-08 N2

T-08 N2 — APPLY — state RULE-OWNER in the tool's module description
Evidence: The module description (lines 37–40) says the refusal reports "the recorded owner, its age in seconds and stale_suspected" and never says when the owner or the age is null. The spec and the manual do not state the limits either (no mention of 64 KiB, 16 levels or finite numbers anywhere in `.ai/specs/07-state-tool.md` or `docs/USAGE.md`).
Decision: Documentation only, written after L2–L4 so it describes the final rule.
- `scripts/state-tool.py` module description, after "(age of 600 s or more);" insert: "the owner is null unless the whole lock file is at most 64 KiB of UTF-8 holding one JSON object nested at most 16 levels with finite numbers and no lone surrogate, and the age is null unless the owner records a start time with a UTC offset that is not in the future;". Re-wrap near 95 columns.
- `.ai/specs/07-state-tool.md`, `### Output`, after the table (the sentence the spec lacks): "`lock_owner` is the parsed lock file when the whole file is at most 65536 bytes of UTF-8 that parse as one JSON object nested at most 16 levels (an empty object or list counts as a level), with finite numbers only and no lone surrogate; otherwise it is null. A repeated key is reported with its last value. `lock_age_seconds` is the whole seconds since `started_at` when the owner is reported and `started_at` is an ISO-8601 time with a UTC offset that is not in the future; otherwise null. `stale_suspected` is true only for an integer age of 600 or more."
- `docs/USAGE.md` section 11: replace "(the recorded owner metadata, or null when it cannot be read)" with "(the recorded owner metadata, or null unless the whole lock file is one JSON object of at most 64 KiB that can be reported as standard JSON)" and after "`lock_age_seconds`" add "(null when the start time is missing, unreadable or in the future)".
Files: tool docstring, spec, manual. No behaviour; test-first exemption: documentation text — unit, integration, contract and smoke levels have nothing to execute beyond the L2–L4 tests that pin the rule itself. Check that no manual line above the ledger-pinned clone command (line 255) moves; section 11 starts at line 881, so it does not.
Why: The rule exists only in code and constants today; one sentence in each of the three places closes that.

### T-08 O3

T-08 O3 — APPLY — description line for `owner_details`
Evidence: `owner_details` (line 1427) is the only function of the busy-details group without a docstring; `read_lock_owner` and `lock_owner_details` have one.
Decision: Add the docstring: "Derive the lock age and the stale suspicion from the owner's recorded start time; the age is unknown without an owner, without a start time carrying a UTC offset, or for a start time in the future." Do it in the same edit as L2.
Files: `scripts/state-tool.py`. No behaviour; test-first exemption: a docstring — no unit, integration, contract or smoke level can observe it.
Why: One line, and it records the L2 rule where it is implemented.
