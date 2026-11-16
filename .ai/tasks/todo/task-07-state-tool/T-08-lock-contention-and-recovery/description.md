## Goal
Write commands refuse safely under lock contention, unsafe paths and concurrent file
changes, and after an interruption `state.md` is the whole old or the whole new file with
leftover temporary files reported, never read and never deleted.

## Context
- Dependencies: T-03 (write transaction), T-04 (`append-note` for the retry scenarios),
  T-07 (`already_applied` on retry after the replace).
- Constraints: same runtime limits as the tool. Contract: task spec REQ-06, REQ-07,
  REQ-09, REQ-10, REQ-12, REQ-24, REQ-25, `### Test seam`, `### Auxiliary files`,
  `### Output` (refusal with exit 5), write algorithm steps 3 and 10–12. Lock age never
  proves owner death: a held lock is never deleted, truncated or taken over. English only;
  no planning identifiers in product content.
- Pinned fixtures: a change under `tests/` invalidates the source-guard inventory
  fingerprint and new helper-process call sites need reviewed records; follow
  `tests/fixtures/validator-runtime/README.md`.
- Reason: contention, path safety and interruption are the failure half of the write
  path; they need helper processes and fault injection that the earlier subtasks avoid.

Off-limits: the test seam may only terminate or pause the tool; no stale-lock takeover;
no deletion of a temporary file the process did not create; no network-filesystem or
Windows write support; no file under `workflows/` or `rules/`.

## Scope
- **In scope:** exit 5 `lock-busy` with `lock_owner`, `lock_age_seconds`,
  `stale_suspected`; unreadable metadata → `lock_owner: null`; metadata without a held
  lock never blocks; `unsafe-lock-path`; write-side `path-outside-root` and
  `unsafe-state-file`; `STATE_TOOL_TEST_FAULT` values `kill-before-replace`,
  `kill-after-replace`, `pause-before-recheck` with `STATE_TOOL_TEST_RESUME`; identity and
  revision recheck before the rename; directory-sync failure warning;
  `locking-unavailable` for writes; the no-bypass sentence for exit 5.
- **Out of scope:** changing the lock mechanism or wait defaults; automatic cleanup of
  stale temporary files.
- **Target files:** `scripts/state-tool.py`, `tests/state-tool.py`,
  `tests/fixtures/validator-runtime/source_guard_exceptions.json`,
  `tests/fixtures/validator-runtime/source_guard.py`

## Steps
1. Add failing suite cases for the criteria below, with a helper process that holds
   `flock` on the lock file and writes chosen metadata.
2. Complete the busy path: on wait-bound expiry read the recorded metadata without
   modifying the lock file, report `lock_owner` (or `null`), `lock_age_seconds` and
   `stale_suspected` (age ≥ 600 s), exit 5 with the no-bypass sentence.
3. Refuse a symlinked or non-regular lock path with exit 7 `unsafe-lock-path`, and for
   write commands a task outside root (exit 2) and an unsafe `state.md` (exit 7).
4. Implement the test seam: `kill-before-replace` (SIGKILL self after the temporary file
   is synced), `kill-after-replace` (SIGKILL self after the rename),
   `pause-before-recheck` (wait before the recheck until the file named by
   `STATE_TOOL_TEST_RESUME` exists, at most 10 s); any other value is ignored.
5. Verify the recheck: changed bytes or a different inode with identical bytes → remove
   the own temporary file, exit 4 `state-file-changed`.
6. Return `applied` with warning `directory-sync-failed` and exit 0 when the directory
   `fsync` raises after the rename; refuse writes with exit 7 `locking-unavailable` when
   `fcntl` cannot be imported, while reads still work.
7. Confirm every command lists files matching `.state.md.*.tmp` in `stale_temp_files`,
   never reads them as state and never deletes one it did not create.
8. Refresh the pinned source-guard fingerprint and records, then run the guard suites and
   the suite (`python3 tests/state-tool.py`).

## Acceptance Criteria
- Given a helper holding `flock` on `.state-tool.lock` with `started_at` 660 s in the
  past, `set --lock-wait-seconds 1` exits 5 `lock-busy` with matching `lock_owner`,
  `stale_suspected: true`, and `state.md` and the lock file unchanged; stderr contains
  `Do not edit state.md by hand to bypass this refusal.`
- After the helper is killed with SIGKILL, the same `set` exits 0 `applied`.
- Given lock metadata naming the live PID of an unrelated process and no `flock` held,
  `set` exits 0 `applied`; given unreadable metadata while the lock is held, `set` exits 5
  with `lock_owner: null`.
- Given `STATE_TOOL_TEST_FAULT=kill-before-replace`, `append-note` dies, `state.md` is
  unchanged, one `.state.md.*.tmp` exists, a following `validate` lists it in
  `stale_temp_files` and does not delete it, and a retry with the same `operation_id` and
  the original revision exits 0 `applied` with the note present once.
- Given `kill-after-replace`, `append-note` retried with the same `operation_id` exits 0
  `already_applied` and the note occurs once.
- Given an in-process run where the directory `fsync` raises, the result is `applied`
  with warning `directory-sync-failed` and exit 0.
- `--task` with a `..` escape, or a symlinked directory leaving root, makes `set` exit 2
  `path-outside-root`; `state.md` as a symlink makes `set` exit 7 `unsafe-state-file`; a
  symlinked lock path makes `set` exit 7 `unsafe-lock-path`.
- Given `pause-before-recheck` and `state.md` rewritten during the pause, `set` exits 4
  `state-file-changed`, the test's bytes are retained and the tool's temporary file is
  gone; with `state.md` replaced by a different file with identical bytes, it also exits 4
  `state-file-changed`.
- With the `fcntl` import blocked, `set` exits 7 `locking-unavailable` with the fixture
  unchanged and `get` exits 0.
- With `STATE_TOOL_TEST_FAULT=anything-else`, `set` behaves exactly as with the variable
  unset.

## Test Plan
- **Level:** integration (subprocess runs, helper lock-holder process, fault seam); unit
  for the in-process directory-sync failure.
- **Scenarios:**
  - Held lock with old metadata → exit 5 with owner details and stale flag.
  - Holder killed → next writer applies.
  - Metadata without a held lock; unreadable metadata while held → applied / `null` owner.
  - Kill before replace → old file, one temporary file, retry applies once.
  - Kill after replace → retry `already_applied`, note once.
  - Directory sync failure → `applied` with warning.
  - Path escapes and symlinks → exits 2 and 7.
  - Pause with rewrite or inode swap → exit 4, temporary file removed.
  - Blocked `fcntl` → writes exit 7, reads work.
  - Unknown fault value → normal behaviour.
- **Edge cases:** `--lock-wait-seconds 0`; lock file absent before the first write (created
  with mode 0600); a refused write leaves the lock file in place with rewritten metadata;
  permission-denied task directory → exit 7 with `state.md` unchanged.
