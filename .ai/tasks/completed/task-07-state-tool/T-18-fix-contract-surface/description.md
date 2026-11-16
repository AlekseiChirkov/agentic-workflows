## Goal
The setup script keeps a tracked knowledge base tracked and never corrupts an ignore file, the vocabulary and receipts checks cannot be defeated by the reproduced forms, the identity check names its candidates, and the manual and rule text match the delivered behaviour.

## Context
- Origin: owner request of 2026-11-16 to close every deferred improvement proposal and optional review finding of this task. Each item was verified against the code and decided by an independent analyst; the decisions below are the contract of this subtask and are implemented exactly as worded. Item ids name the proposal section and its ordinal (N = Do Now, L = Do Later, O = Optional; I<n> = issue list entry).
- Constraints: Python 3.11+, standard library only, single file `scripts/state-tool.py`; exit codes 0–8 and the error-code and warning-code tables stay closed (no decision adds a code). No existing test is deleted, renamed, skipped or weakened; new cases are new test methods or new subtests. English only; no planning identifiers or specification labels (requirement, criterion, invariant, decision, assumption, constraint or question labels) in code, tests, comments, messages or documentation.
- Test-first: every decision marked as a behaviour change has failing tests first, observed failing for the stated reason, committed before the implementation. Guard tests (pass before the change) are allowed when named with their mutation evidence. Refactoring is covered by the existing suite, green before and after.
- Pinned fixtures: a change to `tests/state-tool.py`, `scripts/state-tool.py` or another pinned script invalidates pinned digests (see `tests/fixtures/validator-runtime/README.md`); refresh them once after the last source edit. Do not add or remove lines of `docs/USAGE.md` above line 255: the repository's identity ledger pins that line. Never write the ledger's heading line into any file.
- Specification, ADR and knowledge-base sentences named in the decisions are written by the orchestrator at reconciliation, not in this subtask; manual (`docs/USAGE.md`), rule-file and tool-docstring sentences are in scope where the decision names them.

Off-limits: no file under `workflows/`; no deployed copy under the home directory; no change to the oracle mechanism beyond refreshing pinned values; no new exit, error or warning code; no amendment of an existing test.

## Scope
- **In scope:** `scripts/setup-new-project.sh`, the helper `state_tool_vocabulary_matches_rules` and the identity-check failure branch of `scripts/validate-contracts.sh`, the receipts rule of `scripts/validate-task.sh`, one sentence in `rules/workflow-globals.md`, the manual edits in sections 5, 10 and 11, two reason texts of the source-guard manifest, and their tests.
- **Out of scope:** the knowledge-base documents named in the decisions (`.ai/context/runbook.md`, `.ai/context/environment.md`, `.ai/memory/architecture.md`, the coding principles, the ledger paragraph) — written by the orchestrator; `scripts/setup-umbrella.sh`; `rules/workflow-reference.md`; the older checks of `scripts/validate-task.sh`.
- **Target files:** `scripts/setup-new-project.sh`, `scripts/validate-contracts.sh`, `scripts/validate-task.sh`, `rules/workflow-globals.md`, `docs/USAGE.md`, `tests/state-tool.py`, `tests/validator-runtime-characterization.py`, `tests/fixtures/validator-runtime/inventory-amendment.json`, `tests/validator-runtime-oracle.py`, `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `tests/fixtures/validator-runtime/source_guard.py`

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
Refresh shorthand used below (all refreshes are done once, after the last shell/Python edit of the change set, by the procedure in `tests/fixtures/validator-runtime/README.md`):

- **R-suite** (any edit to `tests/state-tool.py`): the `test_state_tool_acceptance` resource row in `tests/fixtures/validator-runtime/inventory-amendment.json`; `AMENDMENT_SHA256` in `tests/validator-runtime-oracle.py`; `inventory_sha256` on all 137 manifest records that carry one; the manifest digest in `tests/fixtures/validator-runtime/source_guard.py`. Helper context digests (`run_tool`, `launch`, `run_bash`, `run_isolated`) stay valid only if those four helper bodies are not edited.
- **R-validator** (edit to `scripts/validate-contracts.sh` after line 583, the end of the startup prefix): `inventory_sha256` on the 137 records and the manifest digest. `expected_prefix_sha256`, `WARNING_SHA256`, `warning-history-after.txt`, the frozen inventory, the amendment and the oracle constants stay untouched provided that (a) no `check "..."` statement is added, removed, renamed or reworded, and (b) no added or changed line contains the bare word `check` (the oracle pins 94 such lines).
- **R-task-validator** (edit to `scripts/validate-task.sh`): the `scripts/validate-task.sh` dependency digest on 1 record (`run_bash`) and the manifest digest.
- **R-setup** (edit to `scripts/setup-new-project.sh`): its dependency digest on the 3 records that list it and the manifest digest.
- **R-reason** (reason text only): the manifest digest.

Ledger trap, verified: the identity ledger (table in `.ai/tasks/completed/task-01-git-source-of-truth/state.md`) pins `docs/USAGE.md` line 255, `.ai/memory/progress.md` line 4, `.ai/tasks/completed/task-00-sensitive-data-scrub/state.md` 357 and 359, four ADRs (0007:18, 0009:70, 0010:105 and 107, 0012:70), completed specs 01:32, 02:25, 05:698, 06:25, open specs 09:19, 10:19, 11:19, 12:17/19/34, 13:23, 13a:23, and the two Russian analysis documents. Every `docs/USAGE.md` edit decided below lies in sections 5, 10 or 11 (line 295 and later), so line 255 does not move and no ledger row is refreshed; an implementer who nevertheless adds or removes a line above 255 must refresh that row in the same change. No other pinned file is edited (a progress-log entry goes below line 8).

No `check "..."` statement of `scripts/validate-contracts.sh` is added, removed or reworded, and no added line contains the bare word `check`. A complete validator run is the orchestrator's step after this subtask.

## Decisions

### T-09 N2

T-09 N2 — APPLY — Vocabulary check fails when a constant is bound anywhere but its one plain assignment
Evidence: Extracted the helper's Python body and ran it on scratch copies of the tool: appended `ROLLUP_VALUES += ("paused",)`, an annotated rebinding, a rebinding inside `if`/`try`, a `global` rebinding in a function, a tuple target, a `for` target, a walrus, `from os import sep as ROLLUP_VALUES` and `del ROLLUP_VALUES` all exit 0 (check passes); only a second plain module-level assignment exits 1. In the real tool each of the four constants has exactly one non-Load `Name` node.
Decision: Behaviour change, test first. In `state_tool_vocabulary_matches_rules` keep the existing rule and add: for each of the four constant names N, walking the whole tree (`ast.walk`), the check fails when (1) the number of `ast.Name` nodes with `id == N` and a `Store` or `Del` context is not exactly 1 (that one being the sole target of the module-level `ast.Assign` already required); or (2) an `ast.Global`/`ast.Nonlocal` names N; or (3) an import alias binds N (`asname == N`, or no `asname` and the first dotted part of `name` is N); or (4) a function, class, argument, `except ... as`, or match-capture is named N. Failure output: one stderr line per problem, `<N>: bound outside its one module-level assignment (line <lineno>)`, exit 1; a tool with none of these keeps exit 0. Dynamic rebinding (`globals()[...]`, `setattr`) stays outside the static check. RED first in `test_vocabulary_constants_pass_on_source_and_fail_on_any_value_or_order_drift`: for each of the four constants, one subtest per form — augmented assignment, annotated rebinding, rebinding inside `if True:`, `global` rebinding inside a function, tuple target, `for` target, walrus, import alias, `del` — each inserted directly after the constant's line in the disposable copy and expected to `fails(VOCABULARY_CHECK)`; plus one control per constant (`_copy = N` after the line) expected to pass. Files: `tests/state-tool.py`, `scripts/validate-contracts.sh` (helper body only; the three `check` statements unchanged). Refresh: R-suite + R-validator.
Why: The check exists to prove the tool's vocabulary equals the anchored lines; nine cheap rebinding forms defeat it today.

### T-09 L1

T-09 L1 — APPLY (narrowed) — Marker-aware fence tracking for the receipts rule only; an open fence at end of file fails
Evidence: Scratch fixtures at the tip: a `~~~` line inside a backtick fence closes it early and a malformed receipts line after the real closing line passes (exit 0, false negative); a fenced copy of the section heading in an earlier section followed by a malformed line in the real section passes (exit 0, false negative: the mis-toggled fence swallows the real heading); a field-shaped malformed line inside that fenced copy fails (false positive). A prototype of the tool's fence grammar (`fence_openers`: opens at `^ {0,3}(```|~~~)`, closes only on a line starting with the same marker at 0–3 spaces) fixes all three under mawk and busybox awk and keeps the six N1 verdicts. None of the nine task `state.md` files in the repository contains a fence line.
Decision: Behaviour change in the awk program of the `state_receipts:` check in `scripts/validate-task.sh` only; test first. Exact behaviour: (1) fences are tracked from line 1 of `state.md`, not from the section heading; a fence opens on a line matching `^ {0,3}(```|~~~)` when none is open and remembers its marker; it closes only on a later line that starts, after 0–3 spaces, with the same marker; the opening line, the lines inside and the closing line are skipped by every other rule of this awk program (headings included). (2) Outside fences the section rule is unchanged (`^(#|##) ` line sets `inside` to whether it is `## Subtask Progress` with optional trailing whitespace), and the per-line receipts rule is unchanged. (3) New fail-closed rule: when the file ends inside a fence, the check fails; the opener's line number N is reported. Output: malformed lines only → the existing message unchanged; open fence only → `[FAIL] every state_receipts: line has 1 to 20 well-formed entries with unique operation ids: the fence opened at line N is never closed, so the lines after it cannot be read — close the fence`; both → the existing message, then `; ` and the fence sentence. Exit 1 in all three; exit 0 otherwise. The check name is unchanged and no check is added. RED cases (all in `TaskValidatorReceiptsTests`): tilde line inside a backtick fence then malformed line after the closing line → `rejected` (passes today); fenced heading copy in an earlier section then malformed line in the real section → `rejected` (passes today); field-shaped malformed line inside a fenced heading copy in an earlier section, real section well-formed → `accepted` (fails today); well-formed section followed by a never-closed fence → exit 1 with the fence sentence (exit 0 today). The older grep-based checks of the script are NOT made fence-aware (rejected part: it changes verdicts of existing checks and is outside the specification's scope). Files: `tests/state-tool.py`, `scripts/validate-task.sh`; also change the rule's comment to say fences follow the state tool's grammar. Refresh: R-suite + R-task-validator.
Why: Options — (A) reject: zero cost, leaves two reproduced false negatives; (B) receipts rule only: three awk lines, exact parity with the tool's grammar, one pinned digest; (C) whole script: large blast radius, re-scopes old checks (a weakening risk). B wins on fit, testability and blast radius; the end-of-file rule keeps the change from relaxing the case "unclosed fence before the section", which the old code still flagged.

### T-09 L4

T-09 L4 — APPLY — State that the receipts line is not moved when fields are added later
Evidence: Scratch task: after a tool write created the line, git fields appended by hand below it; `validate` → `valid`, a second `set` extended the line in place (it now stands before `branch:`), `scripts/validate-task.sh` → 0 failures. So "the line is the block's last known field" is true only at creation. `test_existing_receipts_line_is_extended_in_place` already pins the tool behaviour. `rules/workflow-globals.md` is not hashed by any manifest record or amendment row.
Decision: In `rules/workflow-globals.md`, receipts paragraph, insert directly after "…and an existing line is replaced in place." this sentence: "That position is fixed when the line is created: fields written to the block afterwards, such as git fields added after the tool's first write, do not move it and may stand on either side of it, so a reader finds the line by its field name, never by its position." Keep the anchored definition line, the `` `notes:` `` and `` `pr:` `` mentions and the reader rule byte-identical. Docs only; test levels considered: unit/integration — the described behaviour is already pinned; contract — pinning rule prose is declined (see O3). No workflow changes. Refresh: none.
Why: Options — (1) prescribe "git fields go before the receipts line": new obligation on writers of git fields, which may not change; (2) prescribe "after it": also a new position rule; (3) state that either side is valid and readers key on the name: true today for the tool and both validators, no new obligation. 3 wins on fit and blast radius.

### T-09 O2

T-09 O2 — APPLY — Reword the `run_bash` reason to its three call sites
Evidence: `run_bash` has call sites at `tests/state-tool.py` 4269 (`-c` fragments), 4380 (validator on a fixture), 4452 (validator on completed task directories); the record says "two fixed callers".
Decision: In `tests/fixtures/validator-runtime/source_guard_exceptions.json`, `run_bash` record, replace "from one of its two fixed callers: the pinned task validator script, which only reads a disposable task fixture or a completed task directory of this project, or -c with" by "from one of its three call sites, of two forms: the pinned task validator script on a disposable task fixture, the same script on a completed task directory of this project (read only), or -c with". Nothing else in the record changes. Done during the single manifest refresh of this change set. Refresh: R-reason.
Why: The manifest is re-serialized anyway; the reason should match the reviewed call sites.

### T-10 N2

T-10 N2 — APPLY — Manual names the lock as `flock` taken through `fcntl`
Evidence: `scripts/state-tool.py` line 1459: `fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)`. Manual, Limits: "an advisory `fcntl` lock".
Decision: `docs/USAGE.md` section 11 Limits: replace "the lock is an advisory `fcntl` lock, which network filesystems may not honour" by "the lock is an advisory `flock` lock (taken through Python's `fcntl` module), which network filesystems may not honour". Docs only (the frozen limits test needs `` `fcntl` `` and "local filesystems", both kept). Line is below 255: no ledger refresh. Refresh: none.
Why: Factual correction.

### T-10 N3

T-10 N3 — APPLY — Manual states the `init-block` option rules per kind
Evidence: Reproduced: `--kind composite` without `--children` → exit 2 `invalid-arguments` ("needs --children"); with children but no `--note` → exit 2 ("needs --note"); with `--target-file` → exit 2; `--kind leaf` with `--children` → exit 2.
Decision: `docs/USAGE.md` section 11, directly after the command table, add the paragraph: "For `init-block`, `--kind composite` requires `--children` and `--note` and refuses `--target-file`; `--kind leaf` refuses `--children` (exit 2, `invalid-arguments`)." Docs only. Below line 255: no ledger refresh. Refresh: none.
Why: The synopsis shows all three as optional.

### T-10 L2

T-10 L2 — APPLY — Setup compares whole lines and ends an unterminated last line before appending
Evidence: Reproduced in disposable projects: `.gitignore` `node_modules` without a line break became `node_modules.ai/` (neither rule left); six older entries with an unterminated last line ended `__pycache__/.state-tool.lock` and the rerun reported `ok: .state-tool.lock already in .gitignore`; a comment containing `.ai/`, a line `.env.local` and a line `!.state-tool.lock` suppressed `.ai/`, `.env` and `.state-tool.lock`.
Decision: Behaviour change, test first. Exact behaviour of the `.gitignore` step: (1) an entry is present iff some line of `.gitignore` equals it exactly (`grep -qxF -e "$entry"`); for `.ai/` a line that is exactly `.ai` also counts (the rule `scripts/sync.sh` uses). Comments, negations, longer or narrower lines never count. (2) Immediately before the first append of a run, and only then, if `.gitignore` is non-empty and its last byte is not a line feed, append one line feed and print `  ok: ended the unterminated last line of .gitignore`. A run that appends nothing leaves the file byte-identical. (3) Messages `  appended to .gitignore: <entry>` and `  ok: <entry> already in .gitignore` unchanged. Expected results (non-tracking project): `node_modules` unterminated → `node_modules` then the eight entries, each on its own line; six older entries with unterminated `__pycache__/` → `__pycache__/`, `.state-tool.lock`, `.state.md.*.tmp` on three lines and a byte-identical file after the second run; `# we do not ignore .ai/ here` / `.env.local` / `!.state-tool.lock` → all eight entries appended in order; a complete file → byte-identical, also when its last line is unterminated. RED tests for these four in `ConsumerSetupIgnoreTests` (same `run_isolated` forms as today). Manual, `docs/USAGE.md` section 5 row 6 (this also settles T-10 L1 and T-10 O3): "| 6    | `.gitignore` entries, each appended on its own line only when no existing line equals it: `.ai/` (default for new consumer projects; skipped with a message when `git ls-files .ai` lists a tracked file, so a repository that tracks its knowledge base keeps it tracked — section 11), `.claude/skills/`, `!.claude/skills/.gitkeep`, `.env`, `*.pyc`, `__pycache__/`, `.state-tool.lock`, `.state.md.*.tmp` (state tool lock and temporary files, section 11) |". Row is below line 255: no ledger refresh. Files: `tests/state-tool.py`, `scripts/setup-new-project.sh`, `docs/USAGE.md`. Refresh: R-suite + R-setup (one refresh with T-10 L1).
Why: The loop corrupts a consumer's ignore file; whole-line comparison plus line termination is the minimal exact rule and matches `scripts/sync.sh`.

### T-10 L1

T-10 L1 — APPLY — Setup skips its `.ai/` entry where the knowledge base is tracked
Evidence: Disposable git project with a tracked `.ai/memory/state.md` and no `.gitignore`: the script appended `.ai/` and `git check-ignore` then matched a new task `state.md`. `scripts/sync.sh` already preserves the policy with `git ls-files .ai`; domain invariant 9 makes the tracking policy authoritative; specification assumption A-28 names the rerun as a valid route.
Decision: Behaviour change, test first, implemented together with T-10 L2 (same loop). Detection (same as `scripts/sync.sh`): the project tracks its knowledge base when `git ls-files .ai 2>/dev/null | head -1`, run in the project root, prints anything (index-based, so a staged file counts; not a repository or no git → not tracked). In the `.gitignore` step, for the entry `.ai/` only: if a line already equals it (T-10 L2 rule) → `  ok: .ai/ already in .gitignore` as today (the script never removes a line); else if tracked → append nothing and print `  skipped: .ai/ — files under .ai/ are tracked in this repository; preserving its tracking policy`; else append as today. All other entries unchanged. `".ai/"` stays in `GITIGNORE_ENTRIES` (a contract check greps it). RED tests in `ConsumerSetupIgnoreTests`, using only the existing `run_isolated` argument forms (`git init -q`, `git add -- <literal path>`, `bash` setup, `git check-ignore -q --`): (1) project with a staged file under `.ai/` and `.gitignore` `node_modules/` → after two runs no `.ai/` line, each tool pattern once, the skip message in stdout of both runs, `git check-ignore` of a new task `state.md` exits 1; (2) same project whose `.gitignore` already holds `.ai/` → that line kept exactly once; (3) directory without `git init` → `.ai/` appended once. The frozen `test_tracking_consumer_step_states_what_rerunning_setup_does_to_the_knowledge_base` derives its expectation from the script, so script and manual change in one commit (it is red between them). Documentation in the same change:
  - `docs/USAGE.md` section 11, replace the whole paragraph under "Ignore rules for the auxiliary files" by: "The lock file and the temporary files sit next to the task `state.md`. This repository and new consumer projects ignore `.state-tool.lock` and `.state.md.*.tmp` through `.gitignore` (`scripts/setup-new-project.sh` adds both entries; `scripts/sync.sh` does not). An existing consumer project that tracks `.ai/` adds the two lines by hand or reruns `scripts/setup-new-project.sh`, which appends both and leaves the knowledge base tracked: when `git ls-files .ai` lists a tracked file, the script skips its `.ai/` entry and says so. No ignore rule may match a task `state.md`. A project that ignores `.ai/` already ignores both files." (No sentence may combine `` `.ai/` ``, "adds"/"appends" and "remov…": the frozen test reads that as the old warning.)
  - `docs/USAGE.md` section 5, table row 6: see T-10 L2 for the full row.
  - `.ai/context/runbook.md`, "Initialize a consumer project" step 6: "A consumer that tracks `.ai/` gets the two state-tool ignore entries by adding `.state-tool.lock` and `.state.md.*.tmp` to its `.gitignore` by hand, or by rerunning `scripts/setup-new-project.sh`, which appends both and skips its `.ai/` entry where files under `.ai/` are tracked."
  - `.ai/context/environment.md`, consumer projects bullet: replace "the script appends `.ai/` even where a project tracks it" by "the script skips the `.ai/` entry where `git ls-files .ai` lists a tracked file".
  - `.ai/memory/architecture.md`, state tool paragraph: replace "(setup also appends the `.ai/` entry there, so the manual recommends adding the two lines by hand)" by "(setup skips its `.ai/` entry there, so a rerun or two lines added by hand both work)".
  Files: `tests/state-tool.py`, `scripts/setup-new-project.sh`, the four documents. All manual edits below line 255: no ledger refresh. Record the behaviour change as a design decision (ADR). Refresh: R-suite + R-setup.
Why: The script contradicted the tracking-policy invariant and the manual compensated with a removal step; one detection rule shared with `scripts/sync.sh` is the smallest fix.

### T-10 L3

T-10 L3 — APPLY — Section 10 lists `pinned` among the tests statuses
Evidence: `docs/USAGE.md` line 853: "`atomic-tests` statuses: `not-started` | `red` | `green` | `n-a` | `failed`."; the anchored line in `rules/workflow-globals.md` and the tool list six values. No contract check mirrors the manual line (only the block header is grepped).
Decision: Replace that line by "`atomic-tests` statuses: `not-started` | `red` | `pinned` | `green` | `n-a` | `failed`." Docs only; no check is added. Same line count, below 255: no ledger refresh. Refresh: none.
Why: The manual contradicts the canonical vocabulary.

### T-10 O1

T-10 O1 — APPLY — Reword the `run_isolated` reason to include the check in the disposable project
Evidence: `run_isolated` call sites: 4532 (check-ignore in this checkout), 4558 (`git init`), 4567 (setup), 4600 (`git add`), 4605 (check-ignore on a literal path in the disposable project, without `--no-index`); the reason names only the checkout for check-ignore.
Decision: In the `run_isolated` record's reason replace "on the state.md paths found by a glob over this checkout's existing task directories;" by "on the state.md paths found by a glob over this checkout's existing task directories, or without --no-index on a literal task path in a disposable project (read only);". Keep "four fixed callers" (four forms). Tests added under T-10 L1/L2 must use only these forms so the reason stays true. Refresh: R-reason (same manifest refresh).
Why: Free on the refresh that is happening anyway.

### T-10 O2

T-10 O2 — APPLY — Result-key sentence lists every key
Evidence: Observed key sets: `get` → `blocks, command, contract_version, errors, result, schema_version, source_revision, stale_temp_files, task, warnings` (a refused `get` has no `blocks`); `validate` → the eight common keys; write → common plus `block_id, block_kind, changed_fields, operation_id, result_revision`.
Decision: `docs/USAGE.md` section 11, replace the first sentence of the paragraph after the command table by: "stdout carries exactly one JSON object (`schema_version` 1) with `command`, `task`, `result` (`read`, `valid`, `invalid`, `applied`, `already_applied`, `unchanged` or `rejected`), `errors`, `warnings`, `source_revision` and `stale_temp_files`; `get` adds `contract_version` and, when it reads, `blocks`; write commands add `operation_id`, `block_id`, `block_kind`, `result_revision` and `changed_fields`." Docs only; below 255: no ledger refresh. Refresh: none.
Why: Callers act on `block_kind` and `blocks`; the list was incomplete.

### T-10 O3

T-10 O3 — APPLY — Row 6 names the negation entry
Evidence: `GITIGNORE_ENTRIES` holds `!.claude/skills/.gitkeep`; row 6 omits it.
Decision: Covered by the row text given under T-10 L2. No separate change.
Why: The row is being rewritten anyway.

### T-11 L1

T-11 L1 — APPLY — The identity check names the candidate files when it does not find exactly one ledger
Evidence: `scripts/validate-contracts.sh` line 4757–4759 prints only `Expected exactly one identity match ledger`. The function is outside the startup prefix and the oracle's pinned identity block; no manifest record has it as container; the differential suite compares only single-ledger scenarios (valid ledger, missing path, unexpected occurrence) and the scan loop, both untouched. Candidates come from `git ls-files --cached --others --exclude-standard`, so untracked, not-ignored files count too.
Decision: Behaviour change, test first. When the number of files carrying the ledger heading is not 1, stdout is: `Expected exactly one identity match ledger; found <N>` followed by one line per candidate, two spaces and the path, in discovery order; return 1. With exactly one candidate nothing changes. Only the discovery loop and that failure branch change; no added line may contain the bare word `check`. RED test in `tests/validator-runtime-characterization.py` (new test method only, existing helpers untouched; build the heading from fragments as that file already does): a fixture with two files carrying the heading → non-zero, stdout contains `found 2` and both path lines; a fixture with none → `found 0`. Files: `tests/validator-runtime-characterization.py`, `scripts/validate-contracts.sh`. Refresh: R-validator (the test file is part of the same inventory fingerprint; its nine records keep their context digests).
Why: The message hid the cause in the last fix; the rule of T-11 L2 becomes diagnosable. Marginal cost is low because the fingerprint is refreshed for T-09 N2 anyway.
