## Goal
Behaviour the tool, the task validator and the manual already have, and that the contract states, is pinned by suite cases, so that later changes cannot alter it unnoticed.

## Context
- Origin: owner request of 2026-11-16 to close every deferred improvement proposal and optional review finding of this task. Each item was verified against the code and decided by an independent analyst; the decisions below are the contract of this subtask and are implemented exactly as worded. Item ids name the proposal section and its ordinal (N = Do Now, L = Do Later, O = Optional; I<n> = issue list entry).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`; exit codes 0–8 and the error-code and warning-code tables stay closed (no decision adds a code). No existing test is deleted, renamed, skipped or weakened; new cases are new test methods or new subtests. English only; no planning identifiers or specification labels (requirement, criterion, invariant, decision, assumption, constraint or question labels) in code, tests, comments, messages or documentation.
- Test-first: every decision marked as a behaviour change has failing tests first, observed failing for the stated reason, committed before the implementation. Guard tests (pass before the change) are allowed when named with their mutation evidence. Refactoring is covered by the existing suite, green before and after.
- Pinned fixtures: a change to `tests/state-tool.py`, `scripts/state-tool.py` or another pinned script invalidates pinned digests (see `tests/fixtures/validator-runtime/README.md`); refresh them once after the last source edit. Do not add or remove lines of `docs/USAGE.md` above line 255: the repository's identity ledger pins that line. Never write the ledger's heading line into any file.
- Specification, ADR and knowledge-base sentences named in the decisions are written by the orchestrator at reconciliation, not in this subtask; manual (`docs/USAGE.md`), rule-file and tool-docstring sentences are in scope where the decision names them.

Off-limits: no file under `workflows/`; no deployed copy under the home directory; no change to the oracle mechanism beyond refreshing pinned values; no new exit, error or warning code; no amendment of an existing test.

## Scope
- **In scope:** new suite cases only, in `tests/state-tool.py`; the pattern extension of the wording test; the static-scan helper and its cases.
- **Out of scope:** any change to `scripts/state-tool.py`, to a validator, to the manual or to the specification — the document and specification parts of these items (manual bullets, specification sentences, ADR text) belong to the later subtasks and to reconciliation. The lone-surrogate owner case and the over-long lock file case are not pinned here (their outcomes change in a later subtask).
- **Target files:** `tests/state-tool.py`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

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
Every case in this subtask passes against the unchanged tool. For each new case record the mutation that makes it fail (a one-line change of the tool or validator on a scratch copy, never in the repository).

## Decisions

### T-01 N1

T-01 N1 — APPLY — guard tests: malformed tool VERSION and unreadable state.md
Evidence: `tool_contract_version` returns None for a non-matching `VERSION`; reproduced with a tool copy whose `VERSION` is `1.0` and a task `contract_version: 0.9.0`: `get` exit 0, warning `unsupported-contract-version`. `read_state_file`: `state.md` with mode 000 gives `get` and `validate` exit 7 `io-error`, `source_revision` null. Existing tests cover only an absent `VERSION` (`test_contract_version_without_tool_version_warns`) and never `io-error` on a read.
Decision: add two cases to `tests/state-tool.py`, no tool change. (1) `get` through `isolated_tool("1.0")` on a task with `contract_version: 0.9.0` → exit 0, `contract_version` `"0.9.0"`, `unsupported-contract-version` in `warnings`. (2) `state.md` chmod 000 → `get` exit 7 `io-error` with result `rejected`, `validate` exit 7 `io-error` with result `invalid`, `source_revision` null in both, directory snapshot unchanged; skip under euid 0 like the existing unwritable-directory test; restore the mode in cleanup. Guard tests (pass today): name them in the block notes with mutation evidence (make `tool_contract_version` accept two-part versions; map the open failure to another code). Files: `tests/state-tool.py` plus the pinned fixture refresh.
Why: stated contract (`### Contract version check`, exit-code table) with no pin; zero contract risk.

### T-02 N1

T-02 N1 — APPLY — four guard tests for validate
Evidence: reproduced — empty `  state_receipts:` line → `validate` exit 3 `malformed-receipts` (and `get` warns); receipts line with a continuation line → exit 3 `malformed-receipts`; `state.md` as a directory and as a named pipe → `validate` exit 7 `unsafe-state-file`, `source_revision` null; duplicated `T-02` plus `atomic-execution: done` on `T-01` → errors listed as `["block-duplicate", "invalid-value"]`. Existing tests cover only 21 entries, a bad entry, a repeated id, the symbolic link, and membership (not order) of the two error kinds.
Decision: add the four cases to `tests/state-tool.py` exactly as reproduced; the order case asserts that every structure error code precedes every invariant error code in `errors`. No tool change. Guard tests: name them with mutation evidence (drop `item.continuation` and the lower bound in `receipts_problem`; drop the `S_ISREG` check; swap `structure + invariants`). Files: `tests/state-tool.py`, fixture refresh.
Why: contract stated, unpinned, no risk.

### T-01 L3

T-01 L3 — APPLY — ruling: a line of one or two spaces is not a blank line (no behaviour change)
Evidence: reproduced inside a block: a line of 1 space → exit 3 `malformed-block` ("line indented by one space"); 2 spaces → exit 3 `malformed-block` ("two-space line that is not a field line"); 3 spaces → read as a continuation line whose text is the three spaces; a tab → `malformed-block`. No test pins the whitespace-only forms.
Decision: ruling — a blank line is an empty line everywhere in the tool; a line that holds only spaces is not blank. Behaviour stays exactly as reproduced. Add one guard test (`GetStructureTests` or `BlockGrammarTests`): bodies `"  notes: a\n \n  target_files:\n"` and `"  notes: a\n  \n  target_files:\n"` → `get --block` exit 3 `malformed-block`; body `"  notes: a\n   \n  target_files:\n"` → exit 0 and the `notes` field has `continuation == ["   "]`. Mutation evidence: treating such lines as blank. Documentation: manual bullet M1 and specification sentence S2. Files: `tests/state-tool.py`, `docs/USAGE.md`, `.ai/specs/completed/07-state-tool.md`.
Why: options — (a) keep the literal grammar and state it; (b) count 1–2-space lines as blank; (c) count every spaces-only line as blank. (b) leaves two meanings of "blank" (3+ spaces would still be a continuation line, and block insertion uses the empty-line meaning); (c) changes how existing files read and breaks the read-back of a spaces-only note. (a) is the simplest, fails closed with an existing code, needs no code and changes no bytes; it is trivially reversible later.

### T-02 L4

T-02 L4 — APPLY — confirm the reading and write the in-block fence grammar down
Evidence: reproduced: header, 3-space fence pair, `     cont`, fields → exit 3 `malformed-block` ("continuation line without a field line"). `parse_blocks` treats the fence as belonging to no group, so the continuation line has no field line. No test pins this shape (`test_malformed_lines_make_block_malformed` covers only a continuation line directly under the header).
Decision: confirmed as intended — a fence is not a field line, so a continuation line after a fence that sits directly under the header is a malformed line. No tool change. Add one guard test for the reproduced shape (exit 3 `malformed-block` for `get --block` and `validate`); mutation evidence: letting the fence branch keep or create a group. Add shared text S1 to the specification (it is the single home of the in-block fence rule for T-01 L1, T-01 L2 clause, T-02 L1, L2, L3, L4, T-13 O1) with a change-log entry, and ADR text D6. Files: `tests/state-tool.py`, `.ai/specs/completed/07-state-tool.md`, `.ai/adr/0022-task-07-state-tool-receipts-and-line-preserving-writes.md`.
Why: the behaviour follows from "fenced lines are opaque"; only the statement and a pin were missing.

### T-06 L4

T-06 L4 — APPLY — document that a spaces-only line is the last non-blank line for block insertion
Evidence: `block_insertion` tests `content(line) != ""`. Reproduced: a section ending with a blank line, a line of three spaces, a blank line, `## Next` → `init-block` applied; the new block follows the spaces-only line after one blank line and the earlier blank line stays after the block.
Decision: no tool change (same ruling as T-01 L3: blank means empty). Manual bullet M1 carries the sentence. Add one guard test pinning the reproduced bytes: a section ending `<last leaf line>\n\n   \n\n## Next\n` reads, after an applied `init-block T-05`, `<last leaf line>\n\n   \n\n<lines of the new block>\n\n## Next\n` — one empty line is inserted between the spaces-only line and the new block, and the empty line that followed the spaces-only line stays between the new block and `## Next`. Mutation evidence: using `strip()` in `block_insertion`. Files: `tests/state-tool.py`, `docs/USAGE.md`.
Why: consistent with T-01 L3; documenting is all the proposal asks.

### I5

I5 — APPLY — align the specification: the no-bypass sentence belongs to refused writes
Evidence: `emit` prints the sentence only when the command is a write command and the exit is 4, 5, 6 or 8. Reproduced: `validate` exit 6 `completion-without-tests` prints no sentence. The requirement on optionality and the acceptance criterion speak of refusals; the manual says "Exits 4, 5, 6 and 8 refuse a write"; only the paragraph under `### Exit codes and error codes` is unscoped.
Decision: the tool is right; no tool change. Specification: replace the sentence "The stderr text for exits 4, 5, 6 and 8 contains the sentence `Do not edit state.md by hand to bypass this refusal.`" with "The stderr text of a write command refused with exit 4, 5, 6 or 8 contains the sentence `Do not edit state.md by hand to bypass this refusal.`; `validate` reports violations with exit 6 and refuses nothing, so its stderr does not carry the sentence." Add one guard test: `validate` exiting 6 and exiting 3 → stderr non-empty and without the sentence. Mutation evidence: removing the write-command condition in `emit`. Files: `.ai/specs/completed/07-state-tool.md` (plus change-log line), `tests/state-tool.py`.
Why: options — print the sentence for `validate`; scope the wording. For `validate` the sentence would be false: it refuses nothing, and a block it reports is repaired by the manual procedure because the tool never repairs. No requirement is weakened: the requirement text already says "refuses".

### T-02 O3

T-02 O3 — APPLY — wording test: add the two missing label families, nothing else
Evidence: `SourceWordingTests` uses `\b(?:REQ|AC|I|D|A)-[0-9]+\b` over the tool and the suite. The specification also has constraint (`C-n`) and question (`Q-n`) labels. Neither file has a match for those today (checked: 0 and 0).
Decision: change the pattern to `\b(?:REQ|AC|I|D|A|C|Q)-[0-9]+\b`. Do not widen to other files (manual, rules and workflows legitimately discuss criterion-style identifiers) and do not restrict to comments and docstrings (a label inside a string literal or message is the leak the owner ruling of 2026-11-13 forbids). The test passes before and after (guard; mutation evidence: a scratch copy of the tool with `C-1` in a comment fails). This strengthens a frozen test and weakens nothing. Files: `tests/state-tool.py`, fixture refresh.
Why: options — keep; add families; restrict to comments. The paper-size false positive is hypothetical and would be visible at once; adding two families is free and closes the stated gap; the other two directions add false positives or remove coverage.

### T-03 N1

T-03 N1 — APPLY (reduced) — guard tests for write-path refusals
Evidence: of the four cases, two exist: the receipt shape of `set` is pinned by `expected_receipt` in `test_receipt_digest_covers_notes_and_paths_in_argument_order` and `ReceiptCapTests`; the directory and named-pipe lock path by `test_lock_path_that_is_a_directory_or_a_named_pipe_is_refused`. Not pinned: `set` on CR / BOM / invalid UTF-8 (only `get` is, `test_unsupported_encodings_exit_3`) — reproduced: exit 3 `unsupported-encoding`, file unchanged, no temporary file; and a failing candidate write, file sync or rename (`replace_state`; only the unwritable directory is covered).
Decision: add two guard tests only. (1) `set` on a state file with a CR byte, with a BOM, with an invalid UTF-8 byte → exit 3 `unsupported-encoding`, `state.md` unchanged, no `.state.md.*.tmp`. (2) in-process, with `os.write`, then `os.fsync` on the temporary file descriptor, then `os.replace` patched to raise `OSError` → exit 7 `io-error`, `state.md` unchanged, no temporary file left. File: `tests/state-tool.py`. No behaviour change, no spec text.
Why: the other two cases are already pinned; these two are spec-stated outcomes (REQ-07, write step 4) with no test.

### T-04 N1

T-04 N1 — APPLY (reduced) — guard test for a path with CR or LF
Evidence: reproduced `add-file --path "a\nb.sh"` and `"a\rb.sh"` → exit 6 `invalid-path`, unchanged; no test pins it (`test_invalid_paths_exit_6_invalid_path` has no such case). The other three cases of the proposal are superseded or done: the `target_files` continuation case and the spaces-only path and note cases get new outcomes under T-04 L1, L2, L3 (their failing tests replace the pins); the non-UTF-8 case is pinned by `InvalidUtf8ArgumentTests`.
Decision: add the CR and LF path cases to `test_invalid_paths_exit_6_invalid_path` (guard). File: suite.
Why: only this part still describes delivered, unpinned behaviour.

### T-05 N1

T-05 N1 — APPLY — guard tests for lifecycle refusals
Evidence: all reproduced at the tip: completion with the pre-TDD note from previous `failed` or `skipped` → exit 6 `completion-without-tests`; `tdd: none — ` only in `last_action`, only in another block, or written without its trailing space → `n-a-unjustified`; `atomic-tests=red` on `green` together with `pr=1` → `read-only-field`, together with `rollup=done` → `field-not-applicable`; absent tests segment set to `not-started`, `red`, `pinned`, `failed` on a leaf in progress → applied, segment inserted before `atomic-execution`. None is pinned (only `blocked` is).
Decision: add these as guard cases, plus two that pin the rulings below: completing execution on an unjustified `n-a` → applied with warning `pre-existing-violation`, then `validate` exit 6 `n-a-unjustified` (T-05 L2); naming the current tests value on a block with a standing violation → `unchanged` with empty `warnings` (T-05 L3). File: suite.
Why: spec-stated outcomes without tests; the two extra cases make the L2/L3 rulings visible.

### T-05 L4

T-05 L4 — APPLY — state how a tests status outside the vocabulary is treated
Evidence: `tests_transition_error` uses `ATOMIC_TESTS_RANK.get(previous, 0)`. Reproduced with previous `passing`: → `not-started`, `red`, `pinned`, `failed` applied without warning; → `green` exit 6 `invalid-transition`; → unjustified `n-a` exit 6 `n-a-unjustified`.
Decision: keep the behaviour (replacing an out-of-vocabulary value is a repair, and `green` stays unreachable in one step); document and pin it. Guard test with the six moves above. Spec `### Invariants`, sentence after "an absent `atomic-tests` segment has rank 0": "A previous value outside the vocabulary also has rank 0." Manual, Limits: "A hand-edited `atomic-tests` value outside the vocabulary counts as `not-started`: `set` replaces it with any vocabulary value except `green`." Files: suite, spec, manual. No tool change.
Why: defined and fail-closed already; only the statement was missing.

### T-06 N1

T-06 N1 — APPLY — guard tests for init-block layout and refusals
Evidence: all reproduced: heading directly followed by the next heading → block between them, no blank line; last block directly followed by a heading → one blank line before the new block, none after; creation while another block is malformed, duplicated or carries `[x]` → applied; unclosed `~~~` fence → exit 1 `internal-error`, unchanged; duplicated section, CR byte, `contract_version: 99.0.0` → exit 3 (`section-duplicate`, `unsupported-encoding`, `unsupported-contract-version`), unchanged; mode 0640 kept; a follow-up `set` on the created block applied. None is pinned (existing layout tests use a blank line before the next heading and backtick fences).
Decision: add all of them as guard cases; for the "other block" cases also assert the other block's bytes are unchanged. File: suite.
Why: delivered, spec-stated behaviour with no test.

### T-07 N1

T-07 N1 — APPLY — guard tests around receipts
Evidence: all reproduced: `init-block` on an existing id whose block has a tab line, prefix `[x]` or `atomic-foo:` → exit 3 (`malformed-block`, `unrecognized-prefix`, `unknown-header-field`) at a stale and at the current revision; a write on a receipts line with a bad entry or a repeated id → exit 3 `malformed-receipts`; a hand-made 20-entry line + one write (`set`, `append-note`, `add-file`) → applied, first entry dropped; reused id with `pr=1`, `atomic-execution=done`, `--path /abs` → exit 8 (a new id → exit 6); a would-be `unchanged` call at a stale revision → exit 4; `--children` order swapped under one id → exit 8; another `--lock-wait-seconds` under a recorded id → `already_applied`. Existing tests cover only the 21-entry line, the duplicated id, the dropped operation at a stale revision and invalid UTF-8 under a reused id.
Decision: add all as guard cases, plus "dropped operation repeated at the current revision → applied as new". File: suite.
Why: these outcomes follow from the write order but no test holds them.

### T-12 L1

T-12 L1 — APPLY — guard test that invalid text never shares a digest with valid text
Evidence: `input_digest` encodes with `surrogatepass`. Reproduced: `append-note --note "a?"` applied under id `Q`, then `--note` with bytes `a\xff` under `Q` → exit 8. No test would catch a lossy handler (the existing reuse test starts from unrelated text).
Decision: add one guard test: for each valid text in `a?`, `a` followed by U+FFFD, `a`, the seven ASCII characters `a\udcff`, the five ASCII characters `a\xff` apply `append-note` under one id on a fresh fixture, then repeat the id with the note bytes `a\xff` → exit 8 `operation-conflict`, file unchanged. Record the mutation evidence (digest encoding with `replace`, `ignore` or `backslashreplace` each fails one case). File: suite.
Why: protects the property the non-UTF-8 fix relies on.

### T-08 N1

T-08 N1 — APPLY — pin the existing lock-metadata and kill-fault behaviour, adjusted to RULE-OWNER
Evidence: All listed behaviours reproduced at the tip: 16 levels reported and 17 null, with an empty object or an empty list at level 17 also null; an object of exactly 65536 bytes reported and a 65537-byte object null; duplicate keys → last value; `kill-before-replace` and `kill-after-replace` behave for `set`, `add-file` and `init-block` exactly as for `append-note` (status -9, empty stdout; old file + one temporary file + retry `applied`, or new file + no temporary file + retry `already_applied`). `snapshot` compares mode, mtime and bytes only, so the lock inode is unpinned. The lone-surrogate case currently echoes the escape (exit 5, ASCII output).
Decision: Add guard tests only (no tool change; each passes at the tip), in `tests/state-tool.py`, as NEW test methods — do not edit existing frozen tests:
1. nesting: 16 levels reported unchanged; 17 levels null; a 16-level object whose innermost value is an empty object and one whose innermost value is an empty list → null (the empty container is level 17); the same at 15 levels → reported.
2. size: one object of exactly 65536 bytes → reported; one object of 65537 bytes → null.
3. duplicate keys `{"pid":1,"pid":2}` → `lock_owner == {"pid": 2}` (this is the pin for the L5 ruling).
4. lock inode: during a busy refusal the lock file keeps its `st_dev`/`st_ino` (new method next to the lock-held test).
5. `kill-before-replace` and `kill-after-replace` for `set`, `add-file` and `init-block`, with the same assertions as the two `append-note` tests.
Removed from N1: the lone-surrogate pin as proposed ("echoed") — it moves to L4 with the opposite expected value and a red-first step. The "64 KiB object followed by more bytes" case belongs to L3. Every case asserts exit 5, `lock-busy`, one strict-JSON object on stdout, the no-bypass sentence and an unchanged task snapshot.
Files: `tests/state-tool.py` only (plus the suite's pinned-digest refresh). Guard tests; no failing-first step is possible or required — state that in the commit body.
Why: Cheap regression guards for stated behaviour; written after L2–L4 so they pin the decided rule, not the superseded one.

### T-08 O1

T-08 O1 — APPLY — guard test for the catch-all in `lock_owner_details`; keep the clause
Evidence: `lock_owner_details` (lines 1417–1424) catches `Exception` around `owner_details(read_lock_owner(...))`; `read_lock_owner` already catches `OSError`, `UnicodeDecodeError`, `ValueError`, `RecursionError`, so no file content reaches the outer clause. Reproduced the unreached branch in scratch: with `os.pread` replaced by a function raising `RuntimeError` while the lock is held, the tool still exits 5 `lock-busy` with `lock_owner: null`, age null, stale false.
Decision: Keep the clause as written (do not narrow it). Add one test: lock held by the helper, the tool run with the bounded read raising an unexpected error type (`RuntimeError`) → exit 5, `lock-busy`, the three keys null/null/false, no-bypass sentence, no traceback, snapshot unchanged. Use whichever existing runner can patch `os.pread` (in-process run, or the `launch` helper with a small `-c` wrapper).
Files: `tests/state-tool.py` only. Guard test, passes today; no tool change.
Why: Narrowing would turn an unforeseen failure into exit 1 and lose the busy refusal, which is the less safe direction; the test makes the defensive clause mutation-resistant for a few lines.

### T-09 N1

T-09 N1 — APPLY — Guard fixtures for the scoping and fence skip of the task validator's receipts rule
Evidence: Built the fixtures in scratch and ran `scripts/validate-task.sh` plus two mutants (scoping `!inside` removed; `inside && fenced { next }` removed). Tip: (a) malformed field-shaped line under a later `## ` heading and under a `# ` heading → exit 0; (b) malformed line inside a backtick fence and inside a 3-space tilde fence within the section → exit 0; (c) malformed line after a closed fence and after a fenced heading → exit 1. Scoping mutant fails both (a) fixtures; fence mutant fails both (b) fixtures and passes the fenced-heading (c) fixture. So the six cases kill both mutants.
Decision: Add six cases to `TaskValidatorReceiptsTests` in `tests/state-tool.py` with exactly the expectations above (a: `accepted`, b: `accepted`, c: `rejected`). Guard tests only (they pass at the tip); record the mutation evidence (which mutant each case kills) in the commit body and the task record. Files: `tests/state-tool.py`. Refresh: R-suite.
Why: Two one-token deletions in a contract check currently survive the suite; the cases are cheap and stay valid after T-09 L1.

### T-10 N1

T-10 N1 — APPLY — The consumer-step test requires a sentence that names a rerun of the setup script
Evidence: By reading the test: its paragraph filter is satisfied by the parenthesis "(`scripts/setup-new-project.sh` adds both entries; …)" plus "by hand", so deleting the rerun sentences leaves it green.
Decision: In `test_state_tool_section_tells_a_tracking_consumer_to_rerun_setup_or_edit_by_hand` (`tests/state-tool.py`), after the existing assertion, normalise whitespace of the one matching paragraph, split it with `(?<=\.)\s+`, and assert that at least one sentence matches `(?i)\bre-?run` and contains `scripts/setup-new-project.sh`. Guard test (passes at the tip); evidence to record: on a scratch copy of the manual with the rerun sentence removed the new assertion fails while the old ones pass. Files: `tests/state-tool.py`. Refresh: R-suite.
Why: The test's name promises both routes and enforces one.

### I11

I11 — APPLY — Static scan covers further spawning, import and code-execution forms
Evidence: `test_imports_are_standard_library_only_and_no_dynamic_execution` flags only `subprocess`, `os.system`, `os.exec*`, `eval`, `exec`, `shell=`, relative and non-standard imports. The tool uses none of the forms below (AST check: `os` attributes are file and process-identity calls plus `kill`; `getattr(os, 'O_NOFOLLOW'|'O_CLOEXEC', 0)`; `compile` only as `re.compile`).
Decision: Guard tests only, `tests/state-tool.py`. Move the scan into a module-level function `execution_findings(tree) -> list[str]` that keeps every existing finding and adds exactly: (1) `os.<name>`, `from os import <name>` and `getattr(os, "<name>", …)` where name is `popen`, `fork`, `forkpty`, `startfile` or starts with `spawn` or `posix_spawn` (the existing `system`/`exec*` rule extended to the `getattr` form as well); `getattr(os, <non-literal>)` is a finding; (2) imports whose top-level module is `importlib`, `runpy`, `pty`, `multiprocessing`, `ctypes`, `code` or `codeop`; (3) names `__import__` and `compile`. The existing test asserts `execution_findings(tree of the tool) == []`. A new test feeds one synthetic snippet per forbidden form, old and new, and expects a non-empty result, and controls expected to give `[]`: `os.kill(1, 0)`, `getattr(os, "O_NOFOLLOW", 0)`, `re.compile("x")`, `import socket`. Refresh: R-suite.
Why: The scan guards the "values never reach a shell or interpreter" requirement; the extension is enumerated, passes today, and gains negative evidence the test never had.
