# 07. State tool for safe subtask-progress edits

## Source

- **Request:** `/spec-draft .ai/specs/07-state-tool.md` (interactive refinement, 2026-11-13).
- **Input:** the existing Russian-language specification at commit
  `3ee594a`, file `.ai/specs/07-state-tool.md`. Its full original text stays in git history.
  The English translation below is faithful in substance. Links to the old public repository
  location are replaced with repository-relative paths at the pinned commit
  `8c2fa08c18115ffcf38a1798742c41e53a2c7461` (decision D-08).
- **Governing decision:** the owner scheduled this tool on 2026-11-13
  (`.ai/adr/0021-task-07-schedule-state-tool.md`), superseding the state-tool paragraph of
  ADR-0009 Decision 5 (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:198-202`),
  which had kept it in the backlog.

### Implementation review — 2026-11-06

- **Disposition:** Backlog; not implemented.
- **Verified source scope:** main at `23bded3d96d9c562d16eb7e90285414f4412ac79`; owner-authorized specification/state reconciliation on 2026-11-06.
- **Delivered evidence:** The existing task validator and manual progress-block workflow are foundations only.
- **Outstanding scope and limits:** The get/set/append-note/add-file/init-block/validate writer, expected-revision protocol, and transactional task-state serializer are not delivered. This review does not schedule implementation.
- **Sources:** [`scripts/validate-task.sh`](../../scripts/validate-task.sh), [`rules/workflow-globals.md`](../../rules/workflow-globals.md).
- Existing requirement and acceptance identifiers remain binding (annotation 2026-11-13: except REQ-14 and AC-12, withdrawn by D-01). Source inspection and historical validation records do not constitute a fresh full-suite or deployed-environment certification.

### Original text (translated from Russian)

**1. Status and basis.** The work is not scheduled. The document preserves and refines the
design of a future tool for `## Subtask Progress`. It does not authorize implementation, does
not move the work into the current plan, and is not a prerequisite of other improvements.
Basis: ADR-0009, Decision 5 — agents keep editing state with existing means. Grounds for
separate planning may be confirmed block corruption detected by `scripts/validate-task.sh`
and a decision by the task owner; the existence of a detailed specification is not such a
decision. Verified project snapshot: `8c2fa08c18115ffcf38a1798742c41e53a2c7461`, 2026-10-28.
In the current state contract (`rules/workflow-globals.md` at that commit) progress lives in
the parent `state.md`. The current write discipline (`rules/orchestration.md` at that commit)
separates a worker's own block from shared files whose changes the orchestrator applies; this
is not yet a universal serializer or a locking interface. The existing validator
(`scripts/validate-task.sh` at that commit) checks some structural conditions and exits
non-zero on violations; it does not prove complete parsing, transactional writes or the
legality of every state transition.

**2. Problem and outcome.** Free-form editing can create duplicate blocks, lose required
fields, change unrelated sections and overwrite concurrent changes. A small deterministic
tool is needed that finds a specific block by id, changes agreed fields, checks the
transition and saves the whole result or changes nothing. Outcome, if scheduled: one Python 3
standard-library executable in `ORCHESTRAIL_HOME/bin/`; commands `get`, `set`, `append-note`,
`add-file`, `init-block`, `validate`; exact preservation of foreign text and unknown fields;
an agreed task-directory lock and expected-revision check; atomic file replacement and
recovery after interruption; the tool stays optional at run time with a safe manual
procedure. The exact executable name and minimum Python version are fixed at planning; the
name `state-tool` is provisional.

**3. Ownership boundaries.** The tool owns only `## Subtask Progress` of the parent
`state.md`, including leaf and composite blocks. It does not change `plan.md`,
`.ai/memory/state.md`, task descriptions, code, branches, commits, pull-request status or other
`state.md` sections. Auxiliary lock and temporary files are allowed only in the task
directory and never become a source of canonical status; they are not copied into consumer
projects as mandatory infrastructure. Related specs: 14 builds derived context views and does
not own canonical state changes; 15 checks and forms proposals and gets no arbitrary write
interface from this spec; 12 may run children in parallel without this tool because one
orchestrator applies shared changes; 16 defines verification evidence, and the serializer
cannot declare it successful; 19 defines attempt limits, and a field write does not reset
them. None of the nine optimization streams depends on 07.

**4. Sources of truth and compatibility.** (1) Block format, vocabulary, required and
protected fields come from the canonical state contract at a pinned revision; after the
renames of spec 13 the single new path is used, never a second copy of the grammar.
(2) Transitions and required evidence are defined by the execution and validation processes;
a value being in the vocabulary does not make it reachable from every state. (3) A legacy leaf
block without `atomic-tests:` reads as `not-started` by field name, not position; this does not
prove a passed phase and reading does not add the field. If such a block already has
`atomic-execution: in-progress`, compatibility forbids demanding RED retroactively: the
authorized writer records the exact note `pre-TDD task, TDD step skipped` and continues;
`get`/`validate` only report that the exception applies. A new or unstarted task gets no such
exception. (4) Unknown fields are preserved with values, order and their lines, never removed
by normalization. (5) An unknown block prefix is read per the compatibility rule, but writing
into an ambiguously recognized structure is forbidden. (6) `atomic-tests: pinned` is
characterization mode for behaviour-preserving changes; its only next status is `green`; it
must not be turned into `red`, and once `atomic-tests:` exists it is never removed or
downgraded to obtain the legacy exception. (7) `atomic-tests: n-a` is allowed only with the
existing `none` test-level justification; the tool never chooses that level. (8) Manual-edit
restrictions are not weakened; a validator failure that stops a process stays a stop.

**5. Requirements** REQ-01 narrow scope; REQ-02 structural parsing; REQ-03 canonical
serialization; REQ-04 value and transition checks; REQ-05 expected revision over the whole
file; REQ-06 shared task-directory lock, age alone never proves owner death; REQ-07 atomic
replacement, durability separated from visibility; REQ-08 idempotency by `operation_id`;
REQ-09 safe paths, values never executed; REQ-10 optionality without bypass of live locks,
revision conflicts or forbidden transitions; REQ-11 honest results; REQ-12 recovery after
interruption; REQ-13 one grammar, unknown versions refuse writes; REQ-14 separate planning.
The current text of each requirement is under `## Requirements`.

**6. Interface design.** The six commands above with explicit task directory and block id;
the block kind is checked against the actual structure. Combined changes valid only together
go through one `set`. A machine result with `schema_version`, `operation_id`, `result`
(`applied`, `already_applied`, `unchanged`, `rejected`), `task_id`, `block_id`,
`source_revision`, `result_revision`, `changed_fields`, `errors`. Exit codes: `0` success or
proven safe repeat; `2` invalid invocation; `3` damaged structure, unsupported version or
ambiguous block; `4` revision conflict; `5` live or unclear lock owner, or wait timeout; `6`
invalid field, value, transition or insufficient evidence; `7` file, sync or replace failure;
`8` reused `operation_id` conflict. Machine output is separate from diagnostics.

**7. Locks.** Mutual exclusion covers every process using the tool on one task. Owner
metadata: random ownership token, process id with generation, host/session and creation time.
For local filesystems a mechanism released by the OS on process exit is preferred. The
historical "release the lock after ten minutes" idea is an unresolved policy: ten minutes may
justify reporting a possible hang, never evicting a live or unverifiable owner. The lock
protects only protocol participants; an external editor may ignore it; manual mode requires
stopping concurrent writers.

**8. Safe-write algorithm.** Resolve and check paths and tool version; take the lock; read the
whole file and check it was not swapped; find the single section and single block, stop on
damage; check the durable operation receipt before the expected revision; check the expected
revision for a new operation and build the change in memory; check fields, transitions,
evidence, protected and required lines; serialize the block keeping other bytes and re-parse
the candidate; write a temporary file in the same directory with preserved permissions and
sync; re-check source and ownership; replace atomically and sync the directory; return the
result and release only the own lock. Receipts must be stored atomically with the block in one
additive protected grammar field with bounded growth; until that grammar extension is
accepted, durable idempotent writes are not ready.

**9. Manual mode and recovery.** Tool absent: stop concurrent writing, read the block, change
only the needed fields, review the diff, run the existing validator and record the reason in
`notes:`. Conflict or busy lock: manual mode is never used to bypass the refusal. After
interruption: inspect the canonical file, last receipt, temporary files and owner liveness;
never copy a temporary file over state because it is newer; never repeat tests, commits or
external actions on assumption. On corruption: keep the original bytes, report the exact
place, restore from the last confirmed state without deleting newer evidence or counters.

**10–12. Acceptance, planning order, open decisions.** AC-01–AC-12 (current text under
`## Acceptance Criteria`); planning steps: collect real corruption examples, pin the grammar
and validator call sites, resolve locking/receipts/filesystems, agree on the interface,
write failure tests first, connect workflows gradually. Open at scheduling: executable and
Python version, filesystems, lock mechanism, ten-minute policy, receipt name/schema/retention,
migration of new protected fields. This refinement resolves all of them (see `## Decisions`).

## Context & Problem

- Subtask progress lives in one `## Subtask Progress` section of the task `state.md`: leaf
  blocks (`rules/workflow-globals.md:175-188`) and composite blocks
  (`rules/workflow-globals.md:210-216`), detected by the `[composite]` prefix, with unknown
  prefixes read as leaves (`rules/workflow-globals.md:222`). The same template is repeated in
  `rules/workflow-reference.md:205-227`.
- Vocabularies are anchored lines: `rules/workflow-globals.md:195` (atomic-execution /
  atomic-validation), `:197` (atomic-tests), `:218-219` (rollup, integration-validation).
  `pinned` transitions only to `green` (`:199-201`). A leaf block without `atomic-tests:` is a
  pre-TDD task with a fixed note rule (`:203-208`).
- Field rules: `notes:` and `target_files:` are always written; `atomic-tests:` is never
  removed or downgraded; git fields are rewritten only by `/restack`; `tdd:` note lines are an
  audit trail (`rules/workflow-globals.md:226-238`; `.ai/principles/domain.md:60-61`). The
  `none` justification line is `tdd: none — <…>` (`rules/tdd.md:78`).
- There is no locking: execution is strictly sequential because the section has none
  (`rules/workflow-globals.md:107-110`); sub-agents write only their own block
  (`rules/orchestration.md:98`); one writer per shared file (`.ai/principles/architecture.md:32`).
- `scripts/validate-task.sh` checks the section with line greps (`scripts/validate-task.sh:133-170`)
  and the TDD trail (`:172-185`); it exits 0/1/2 (`:13`). Finalization treats a failure as a
  required repair, not a warning (`workflows/pd-finalize.md:64-73`,
  `workflows/pe-finalize.md:92-95`), which is stricter than ADR-0009's interim "warn-only"
  wording (`.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md:201-202`).
- Real progress blocks are richer than the template: `notes:` continues on lines indented by
  9 spaces (`.ai/tasks/completed/task-00-sensitive-data-scrub/state.md:88-89`), continuation
  runs contain blank lines (`…/task-00-sensitive-data-scrub/state.md:134-136`), note values may
  be quoted (`.ai/tasks/completed/task-01-git-source-of-truth/state.md:38`), and column-0 foreign
  lines sit between blocks (`.ai/tasks/completed/task-03-hook-based-logging/state.md:362`).
- Initial blocks are written by `/pd-decompose` (`workflows/pd-decompose.md:159-171`) and
  `/pv-create-fixes` (`workflows/pv-create-fixes.md:109-111`); fix-task ids have the form
  `T-NN-fix-<slug>` and `T-04d-fix-<slug>` (`workflows/pv-create-fixes.md:59,75`).
- A task may record `contract_version:` from the source `VERSION`
  (`workflows/pd-analyze.md:53-58`); the source `VERSION` is `0.9.0`.
- An existing helper already uses an OS advisory lock with a bounded wait:
  `scripts/install-hooks.py:528-541` (`fcntl.flock`, 5 s deadline). Python helpers require
  Python 3.11+ (`scripts/install-hooks.sh:45`).

Consequence: an agent editing a block by hand can duplicate a block, drop a required line,
lose a `tdd:` line, downgrade `atomic-tests:`, or overwrite a concurrent change, and the
line-grep validator detects only part of this after the fact.

## Goal

Agents editing subtask progress by hand can silently corrupt blocks or lose concurrent
changes, and the validator detects only some of this after the fact. The intended outcome is
an optional, deterministic, standard-library Python tool that reads and validates the progress
section structurally and changes one block's agreed fields under a per-task lock, an
expected-revision check and durable idempotency receipts. It enforces the canonical status
invariants and lifecycle rules cited under `## Contracts & Interfaces` (not a complete
transition table) and replaces the file atomically or not at all. The owner scheduled the
tool on 2026-11-13 (D-09); it stays optional and unwired.

## Scope

- `scripts/state-tool.py`: commands `get`, `validate`, `set`, `append-note`, `add-file`,
  `init-block` over `## Subtask Progress` of one task `state.md`.
- Structural parser for the section grammar defined under `## Data Model`.
- Canonical invariant checks (vocabularies, `atomic-tests` rank order, `pinned → green`,
  justified `n-a`, completion guard, pre-TDD exception, read-only fields).
- Per-task OS advisory lock, expected revision, atomic replace, receipts-based idempotency,
  recovery reporting.
- Additive grammar extension: tool-managed `state_receipts:` field, its anchored definition,
  protection from `/compress-state`, and its checks in `scripts/validate-task.sh` and
  `scripts/validate-contracts.sh`, including a vocabulary drift check between the tool and
  `rules/workflow-globals.md`.
- Usage and manual fallback documentation in `docs/USAGE.md`.
- Ignore rules for the lock and temporary files in this repository's `.gitignore` and in
  the entries `scripts/setup-new-project.sh` writes into consumer projects (D-10).
- Acceptance tests with disposable fixtures.

## Out of Scope

- Wiring the tool into any workflow (`/pae-*`, `/pav-*`, `/pd-decompose`, `/pv-create-fixes`,
  `/spec-run`, `/restack`); workflows keep editing state as today (D-07).
- Writing git fields (`branch`, `base_branch`, `base_commit`, `commits`, `pr`), `children:`
  after creation, or any unknown field.
- Creating or deleting the `## Subtask Progress` section; deleting or renaming blocks.
- Any file other than the task `state.md`, the lock file and the tool's own temporary file;
  in particular `plan.md`, `.ai/memory/state.md`, descriptions, code, branches.
- A full transition state machine beyond the canonical invariants (D-05).
- Network filesystems, Windows writes, multi-host locking.
- Repairing damaged blocks automatically; deduplicating existing duplicate ids.
- Run-log telemetry from the tool.
- Removing the grammar duplication between `rules/workflow-globals.md` and
  `rules/workflow-reference.md` (spec 13a/13 territory).

## Actors & Roles

| Actor | Allowed actions |
|---|---|
| Calling agent (orchestrator, implementer, validator) or human operator | Runs any command; authority over which block it may change comes from `rules/orchestration.md`, not from the tool |
| State tool | Reads the task `state.md`; writes only that file, its lock file and its own temporary file |
| External editor (any process not using the tool) | Not bound by the lock; may race the tool (documented limitation) |
| `scripts/validate-task.sh` | Read-only artifact checks, extended for `state_receipts:` |
| `/compress-state` | Must preserve `state_receipts:` lines like other protected lines |

## Terminology

| Term | Definition | Source |
|---|---|---|
| Task directory | Directory holding the task `state.md` (`.ai/tasks/todo/task-<NN>-<slug>/` in consumers) | `.ai/principles/domain.md` (Task directory) |
| Root | Explicit project root passed as `--root`; the task directory must resolve inside it | this spec |
| Progress section | The `## Subtask Progress` section of the task `state.md` | `rules/workflow-globals.md:173` |
| Block | Header line plus its field and continuation lines | `## Data Model` |
| Leaf block / composite block | Block without / with the `[composite]` prefix | `rules/workflow-globals.md:222` |
| Block id | `T-` id in the header: `T-NN`, `T-NNx`, `T-NN-fix-<slug>`, `T-NNx-fix-<slug>` | `workflows/pv-create-fixes.md:59,75` |
| Header field | `name: value` segment of the header line after the block name | `rules/workflow-globals.md:177,212` |
| Field line | Line starting with exactly two spaces then `name:` | `## Data Model` |
| Continuation line | Line indented by 3 or more spaces following a field line, or a blank line followed by one | `## Data Model` |
| Revision | `sha256:` + lowercase hex SHA-256 of the full `state.md` bytes | REQ-05 |
| Operation | One write command invocation identified by `operation_id` | REQ-08 |
| Receipt | `<operation_id>#<digest>` entry in `state_receipts:` | REQ-19 |
| Input digest | First 16 lowercase hex characters of SHA-256 over the canonical JSON of an operation's inputs | REQ-19 |
| Write command | `set`, `append-note`, `add-file`, `init-block` | REQ-15 |
| Read command | `get`, `validate` | REQ-15 |
| Pre-TDD exception | Leaf block without `atomic-tests:` whose `atomic-execution` is `in-progress` | `rules/workflow-globals.md:203-208` |

"Transaction", "commit" and "status" are not used for tool results: a write result is
`applied`, `already_applied`, `unchanged` or `rejected`, never a task status.

## Requirements

- **REQ-01 Narrow edit.** WHEN a write command applies, THE SYSTEM SHALL change only the
  target block's lines that carry changed or inserted fields and leave every other byte of
  `state.md` identical.
- **REQ-02 Structural parse.** WHEN any command reads `state.md`, THE SYSTEM SHALL locate the
  progress section and blocks by the grammar under `## Data Model`, ignoring lines inside
  fenced code, and IF `state.md` is missing, the section occurs more than once, the target id
  occurs more than once, the target block contains a malformed line, or, for a write
  command, the target block has a malformed `state_receipts:` line, THEN THE SYSTEM SHALL
  refuse with exit 3 and leave every file unchanged; other read outcomes follow
  `## Contracts & Interfaces → ### Read outcomes`.
- **REQ-03 Field serialization (rewritten 2026-11-13).** WHEN a write command changes a
  block, THE SYSTEM SHALL keep the existing order of all lines, insert a missing known field
  at its canonical position, keep empty `notes:` and `target_files:` lines, and preserve
  unknown fields, continuation lines, blank lines and quoted values byte for byte.
- **REQ-04 Invariant checks (rewritten 2026-11-13, D-05).** WHEN a write command would
  change a block, THE SYSTEM SHALL evaluate the write invariants under
  `## Contracts & Interfaces → ### Invariants` against the fields the operation changes and
  IF any fails THEN THE SYSTEM SHALL refuse with exit 6 and leave every file unchanged.
- **REQ-05 Expected revision.** WHEN a write command carries an operation without a matching
  receipt, THE SYSTEM SHALL compare `--expected-revision` with the revision of the current
  file bytes and IF they differ THEN refuse with exit 4 and leave every file unchanged.
- **REQ-06 Lock (rewritten 2026-11-13, D-03).** WHEN a write command runs, THE SYSTEM SHALL
  hold an exclusive OS advisory lock on `<task>/.state-tool.lock` from before reading
  `state.md` until after the replace, and IF the lock is not acquired within the wait bound
  THEN refuse with exit 5, report the recorded owner metadata, and never delete, truncate or
  take over a lock held by another process.
- **REQ-07 Atomic replace.** WHEN a write command applies, THE SYSTEM SHALL write the
  candidate to a new temporary file in the task directory, flush it to disk, and replace
  `state.md` with one rename, and IF creating, writing or syncing the temporary file, or the
  rename itself, fails THEN leave `state.md` unchanged, remove only its own temporary file,
  and exit 7. (Failure clause rewritten 2026-11-13.)
- **REQ-08 Idempotency.** WHEN a write command's `operation_id` has a receipt in the target
  block with the same input digest, THE SYSTEM SHALL return `already_applied` with exit 0
  without writing, regardless of `--expected-revision`, and IF the receipt's digest differs
  THEN refuse with exit 8.
- **REQ-09 Safe paths.** IF the task directory does not resolve inside the resolved root, the
  `state.md` path or lock path is a symbolic link or not a regular file, or the file identity
  or bytes changed between the read and the rename, THEN THE SYSTEM SHALL refuse without
  writing; THE SYSTEM SHALL never pass input values to a shell or interpreter.
- **REQ-10 Optionality (rewritten 2026-11-13).** WHEN THE SYSTEM refuses with exit 4, 5, 6
  or 8, it SHALL print on stderr that the refusal must not be bypassed by a manual edit, and
  the documentation SHALL describe the manual procedure for when the tool is absent.
- **REQ-11 Honest results.** WHEN a read command runs, THE SYSTEM SHALL NOT create, modify or
  delete any file, and WHEN a write command applies, it SHALL change only the fields the
  caller named plus `state_receipts:`.
- **REQ-12 Recovery.** WHEN any command finds files matching `.state.md.*.tmp` in the task
  directory, THE SYSTEM SHALL list them as `stale_temp_files` in its output, never read them
  as state, and never delete a temporary file it did not create.
- **REQ-13 One grammar (rewritten 2026-11-13).** IF the task `state.md` records a
  `contract_version:` greater than the tool's own `VERSION`, or records one while the tool's
  `VERSION` is missing or malformed, or the target block has an
  unrecognized prefix or an unknown header field, THEN THE SYSTEM SHALL refuse writes with
  exit 3 and still serve read commands.
- **REQ-14 Separate planning.** Withdrawn 2026-11-13 — a process rule, not tool behaviour;
  moved to constraint C-1 (D-01).
- **REQ-15 Command-line contract.** THE SYSTEM SHALL accept the command forms, print exactly
  one JSON object on stdout, print diagnostics only on stderr, and use the exit codes defined
  under `## Contracts & Interfaces`.
- **REQ-16 Block initialization (added 2026-11-13).** WHEN `init-block` runs for an id absent from the section,
  THE SYSTEM SHALL insert a block with the canonical initial lines for its kind at the
  position defined under `## Contracts & Interfaces → ### Block insertion layout`, and IF
  the id already exists without a matching receipt
  THEN refuse with exit 6 (`block-exists`) without changing the existing block.
- **REQ-17 Note append.** WHEN `append-note` or `set --note` applies, THE SYSTEM SHALL write
  the first note on the `notes:` line when the block has exactly one `notes:` line, its value
  is empty and it has no continuation lines; when the block has no `notes:` line, as a new
  `  notes: <note>` line inserted by the REQ-03 rule; and otherwise as a new continuation
  line indented by 9 spaces after the last line of the block's last `notes:` group; each
  further note of the same call follows as a continuation line; existing note text is never
  altered. (Added 2026-11-13.)
- **REQ-18 Target-file addition.** WHEN `add-file` runs, THE SYSTEM SHALL append each new
  valid path to `target_files:` with the separator `, ` and return `unchanged` without writing
  when every path is already listed, where the existing value is split on `, ` into entries
  compared by exact string equality and an empty value has no entries; a block without
  `target_files:` gets the line inserted by the REQ-03 rule. (Added 2026-11-13.)
- **REQ-19 Receipts.** WHEN a write command applies, THE SYSTEM SHALL record
  `<operation_id>#<input digest>` as the last entry of the block's `state_receipts:` line and
  keep at most the 20 newest entries, dropping the oldest.
- **REQ-20 Grammar extension.** THE SYSTEM SHALL define `state_receipts:` on one anchored line
  in `rules/workflow-globals.md`, list it as protected in `rules/workflow-reference.md`, and
  have `scripts/validate-task.sh` and `scripts/validate-contracts.sh` check it.
- **REQ-21 Pre-TDD reporting.** WHEN a read command reports a leaf block, THE SYSTEM SHALL
  include `pre_tdd_exception` set to `applicable` exactly when `atomic-tests:` is absent and
  `atomic-execution` is `in-progress`, and `not-applicable` otherwise.
- **REQ-22 Runtime.** THE SYSTEM SHALL import only Python standard-library modules, and IF the
  interpreter is older than 3.11 THEN exit 7 with error code `python-too-old` before any file
  access.
- **REQ-23 Atomic field group.** WHEN `set` names several fields and notes, THE SYSTEM SHALL
  apply all of them in one replace or none of them.
- **REQ-24 Locking availability.** IF the `fcntl` module is unavailable, THEN THE SYSTEM SHALL
  refuse write commands with exit 7 (`locking-unavailable`) and still serve read commands.
- **REQ-25 Test seam.** WHERE the environment variable `STATE_TOOL_TEST_FAULT` is set, THE
  SYSTEM SHALL only terminate itself or pause at the named point, and SHALL behave identically
  to an unset variable for any other value.

- **REQ-26 Ignore rules (added 2026-11-13, D-10).** THE SYSTEM SHALL list the patterns
  `.state-tool.lock` and `.state.md.*.tmp` in this repository's `.gitignore` and in the
  ignore entries `scripts/setup-new-project.sh` appends to a consumer project, and SHALL
  NOT ignore any task `state.md`.

## Data Model

### Section and block grammar (existing format; parsing rules new)

Line endings are LF. A **fence** opens on a line matching `^ {0,3}(```|~~~)` and closes on the
next line starting with the same marker at 0–3 spaces; fenced lines are opaque.

| Element | Rule |
|---|---|
| Section start | Line exactly `## Subtask Progress` outside a fence |
| Section end | Next line matching `^#{1,2} ` outside a fence, or end of file |
| Block header | Column-0 line matching `^(\[[^\]]+\] )?(T-[0-9]{2,}[a-z]?(-fix-[a-z0-9]+(-[a-z0-9]+)*)?) \| ([^|]+?) \|( [a-z][a-z-]*: [^|]*\|)*( [a-z][a-z-]*: [^|]*)$` inside the section and outside a fence |
| Field line | `^  ([a-z][a-z0-9_-]*):( .*)?$` (exactly two spaces) directly inside a block |
| Continuation line | Line indented by 3 or more spaces; or a blank line immediately followed, after any further blank lines, by such a line; it belongs to the preceding field line |
| Block end | Line before the next block header, a column-0 non-blank line, trailing blank lines, or the section end |
| Foreign line | Any section line outside blocks; preserved byte for byte |
| Field group | A field line plus its continuation lines |
| Repeated field | `notes` may occur in several field groups of one block (observed: `.ai/tasks/completed/task-05-cost-and-duration-telemetry/state.md:133-136`); the note text of a block is all `notes` groups in file order. An unknown field may repeat and is preserved. A repeated known field other than `notes` makes the block malformed |
| Malformed line | Inside a block: a line indented by exactly 1 space, a two-space line that is not a field line, a tab-indented line, or a continuation line with no preceding field line |

Known header fields: leaf `atomic-tests`, `atomic-execution`, `atomic-validation`; composite
`rollup`, `integration-validation` (`rules/workflow-globals.md:177,212`). The `atomic-tests`
segment, when present, is the first status segment (`rules/workflow-globals.md:207-208`).

Known field lines and canonical order:

| Kind | Order |
|---|---|
| Leaf | `last_action`, `target_files`, `blocker`, `notes`, `branch`, `base_branch`, `base_commit`, `commits`, `pr`, `state_receipts` |
| Composite | `children`, `blocker`, `notes`, `state_receipts` |

The first nine leaf/three composite names are existing (`rules/workflow-globals.md:178-187,213-215`);
`state_receipts` is **new**.

**Insertion of a missing known field (REQ-03).** The new field line goes directly after the
last line (continuation lines included) of the last field group whose name is a known field
preceding it in canonical order; when no such group exists, directly after the header. Unknown
fields and out-of-order known fields keep their places. Example: in a leaf with
`last_action`, `target_files`, `blocker`, `notes`, `verification` (unknown), a new
`state_receipts:` line goes after the last `notes` group, before `verification:`.
An existing `state_receipts:` line is replaced in place.

### Field writability

| Field | Leaf | Composite | Change through |
|---|---|---|---|
| `atomic-tests`, `atomic-execution`, `atomic-validation` | yes | — | `set` |
| `rollup`, `integration-validation` | — | yes | `set` |
| `last_action`, `blocker` | yes | `blocker` only | `set` |
| `notes` | append only | append only | `append-note`, `set --note`, `init-block --note` |
| `target_files` | add only | — | `add-file`, `init-block --target-file` |
| `children` | — | at creation only | `init-block --children` |
| Git fields, unknown fields | read-only | read-only | — |
| `state_receipts` | tool-managed | tool-managed | every applied write |

### New field `state_receipts:`

- Line: `  state_receipts: <entry>, <entry>, …`, oldest first, at most 20 entries.
- Entry: `<operation_id>#<digest>`; `operation_id` matches `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`;
  `digest` is 16 lowercase hex characters.
- Input digest: SHA-256 over UTF-8 JSON of `{"command", "block_id", "inputs"}` with sorted
  keys and separators `,` and `:`; `inputs` holds the command's arguments other than
  `--root`, `--task`, `--expected-revision`, `--operation-id` and `--lock-wait-seconds`, with
  `--field` pairs sorted by name and notes, paths and children in argument order.
- Lifecycle: created by the first applied write on a block; inserted at its canonical position;
  readers that do not know it treat it as an unknown field (`.ai/principles/architecture.md:24`
  P3). Migration: none; blocks without it are valid.

### Auxiliary files (new)

| File | Content | Lifecycle |
|---|---|---|
| `<task>/.state-tool.lock` | JSON `{"owner_token", "pid", "host", "started_at"}` written by the lock holder after acquiring | Created with mode 0600 on first write command; never deleted by the tool |
| `<task>/.state.md.<owner_token>.tmp` | Candidate bytes | Created exclusively; renamed over `state.md` or removed by its creator |

`owner_token` is 32 lowercase hex characters from a cryptographic random source; `started_at`
is UTC ISO-8601 with seconds.

## Contracts & Interfaces

### Commands

```text
python3 scripts/state-tool.py get         --root R --task T [--block ID] [--field NAME]
python3 scripts/state-tool.py validate    --root R --task T [--block ID]
python3 scripts/state-tool.py set         --root R --task T --block ID --expected-revision REV
                                          --operation-id OP --field NAME=VALUE [--field …]
                                          [--note TEXT …] [--lock-wait-seconds N]
python3 scripts/state-tool.py append-note --root R --task T --block ID --expected-revision REV
                                          --operation-id OP --note TEXT [--note …] [--lock-wait-seconds N]
python3 scripts/state-tool.py add-file    --root R --task T --block ID --expected-revision REV
                                          --operation-id OP --path P [--path …] [--lock-wait-seconds N]
python3 scripts/state-tool.py init-block  --root R --task T --block ID --kind leaf|composite
                                          --name NAME --expected-revision REV --operation-id OP
                                          [--target-file P …] [--children ID,ID…] [--note TEXT …]
                                          [--lock-wait-seconds N]
```

- `--field NAME=VALUE` splits at the first `=`. `--lock-wait-seconds` is an integer 0–600,
  default 5. `--task` is resolved relative to the current directory; `state.md` is
  `<task>/state.md`.
- Text inputs (`VALUE`, `TEXT`, `NAME`, paths) are single-line UTF-8 without CR, LF or NUL.
  `NAME` (block name) is non-empty and contains no `|`. `last_action` and `blocker` values
  are non-empty.
- `add-file` / `--target-file` paths are lexical only (never resolved on disk): non-empty,
  relative, no `..` segment, no leading `./`, no `,`, no trailing `/`.
- Step 1 argument validation (exit 2 `invalid-arguments`) covers: missing required options,
  `--lock-wait-seconds` out of range, `--field` without `=`, `--kind composite` without
  `--children` or without `--note`, `--target-file` with `--kind composite`, `--children`
  with `--kind leaf`. Value and path content rules are exit 6 (`invalid-value`,
  `invalid-path`).
- `init-block` canonical initial lines — leaf:
  `T-ID | NAME | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started`,
  `  last_action:`, `  target_files: <paths joined by ", ">`, `  blocker: none`,
  `  notes: <first note>` plus continuation lines, `  state_receipts: <entry>`. Composite:
  `[composite] T-ID | NAME | rollup: not-started | integration-validation: not-started`,
  `  children: <ids joined by ", ">`, `  blocker: none`, `  notes: …`, `  state_receipts: …`.
  Empty values are written as `  name:` with no trailing space.
- Setting `atomic-tests` on a leaf block without that segment inserts
  `atomic-tests: <value> | ` immediately before `atomic-execution:` in the header.

### Block insertion layout

`init-block` finds the last non-blank line L of the section. When L is the section heading,
the new block lines go directly after it. Otherwise one blank line and then the new block
lines go directly after L. Blank lines that followed L stay after the new block. Example: a
section ending `…  pr: none`, blank, `## Next` becomes `…  pr: none`, blank, new block,
blank, `## Next`.

### Invariants

"Notes text" means every `notes` field group of the resulting block. "Previous" means the value
before the operation; an absent `atomic-tests` segment has rank 0.

| Id | Invariant | Scope | Error code | Source |
|---|---|---|---|---|
| I-1 | Every header status value is in its anchored vocabulary | write (changed fields), validate | `invalid-value` | `rules/workflow-globals.md:195,197,218-219` |
| I-2 | `atomic-tests` rank never decreases: `not-started` (0) < `red`, `pinned`, `n-a`, `failed` (1) < `green` (2); a present `atomic-tests` is never removed | write | `downgrade` | `rules/workflow-globals.md:231-232` (A-16) |
| I-3 | Previous `atomic-tests: pinned` changes only to `green` | write | `pinned-transition` | `rules/workflow-globals.md:199-201` |
| I-4 | Resulting `atomic-tests: n-a` requires notes text containing `tdd: none — ` | write (when `atomic-tests` changes to `n-a`), validate | `n-a-unjustified` | `rules/tdd.md:78` |
| I-5 | Resulting `atomic-execution: complete` requires `atomic-tests` `green` or `n-a`; or `atomic-tests` absent, previous `atomic-execution` `in-progress` (write) and notes text containing `pre-TDD task, TDD step skipped` | write (when `atomic-execution` changes to `complete`), validate (static part) | `completion-without-tests` | `workflows/pae-finalize.md:20-21`; `rules/workflow-globals.md:203-208` |
| I-6 | Leaf blocks carry `notes:` and `target_files:`; composite blocks carry `children:`, `blocker:`, `notes:`; the tool never removes a field line | validate (exit 6); `get` and writes report it as a warning; a write that supplies the missing field inserts it (REQ-17, REQ-18) | `required-field-missing` | `rules/workflow-globals.md:226-230,240-242` |
| I-7 | Only fields writable for the block kind and command change (see Field writability) | write | `read-only-field`, `field-not-applicable` | `rules/workflow-globals.md:233-236` |
| I-8 | Every pre-existing field line and continuation line other than the changed ones is byte-identical | write | `internal-error` (post-serialization re-check) | `rules/workflow-globals.md:237-238` |
| I-9 | On a leaf without `atomic-tests`, changing `atomic-execution` from `not-started` requires `atomic-tests` in the same `set` | write | `pre-tdd-not-applicable` | `workflows/phase-atomic-execution.md:71-73` |
| I-10 | `atomic-tests` changes to `green` only from `red` or `pinned` | write | `invalid-transition` | `rules/workflow-reference.md:231-234`; `rules/workflow-globals.md:201`; `workflows/pae-implement.md:191` |

Write invariants are checked against the fields the operation changes. A pre-existing
violation in a field the operation does not change never blocks the write; it is reported in
`warnings` as `pre-existing-violation` (`required-field-missing` for I-6). I-7 and the
value and path content rules are checked first; then, when no field value changes and no
note or path is added, the result is `unchanged` before the remaining invariants are
evaluated. Accepted gaps (D-05):
`failed → red`, `red → n-a` and other moves inside rank 1 are allowed; atomic-validation and
composite statuses are checked by vocabulary only.

### Write algorithm (normative order)

1. Check the Python version (REQ-22); then validate arguments (exit 2); then check `fcntl`
   (REQ-24).
2. Resolve root and task with `realpath`; check containment and `lstat` of `state.md` (REQ-09);
   a missing `state.md` is exit 3 `state-missing`.
3. Open the lock path with `O_NOFOLLOW`; acquire `flock(LOCK_EX | LOCK_NB)` with 25 ms retries
   until the wait bound (REQ-06); then truncate and write owner metadata.
4. Read the full bytes; record `st_dev`, `st_ino`, revision; reject non-UTF-8, BOM or CR bytes
   (exit 3, `unsupported-encoding`); check `contract_version:` (REQ-13).
5. Parse (REQ-02); locate section and block.
6. Receipt check (REQ-08): match → `already_applied`; digest mismatch → exit 8.
7. Revision check (REQ-05).
8. Check I-7 and value/path content rules; build the candidate in memory; if no field value
   changes and no note or path is added, return `unchanged` without writing; otherwise
   evaluate the remaining write invariants.
9. Insert the receipt (REQ-19); re-parse the candidate and confirm that bytes outside the
   block are identical and I-8 holds.
10. Create the temporary file with `O_CREAT | O_EXCL | O_NOFOLLOW`, the original permission
    bits, write, `fsync`.
11. Re-check `lstat` identity and revision of `state.md` (REQ-09); mismatch → remove own
    temporary file, exit 4 (`state-file-changed`).
12. `os.replace`; `fsync` the task directory; a directory-sync failure after the rename
    returns `applied` with warning `directory-sync-failed`.
13. Print the result; release the lock by closing the descriptor.

### Contract version check (REQ-13)

- Task version: the first line matching `^contract_version: ([0-9]+)\.([0-9]+)\.([0-9]+)$`
  before the first `## ` heading outside a fence (`workflows/pd-analyze.md:55`). A
  `contract_version:` line that does not match is treated as absent.
- Tool version: the file `VERSION` in the parent directory of the tool's own directory
  (`<script dir>/../VERSION`), stripped of surrounding whitespace, matching
  `^[0-9]+\.[0-9]+\.[0-9]+$`.
- Comparison: integer tuples `(major, minor, patch)`.
- Outcomes: task version absent → no check. Task version ≤ tool version → writes allowed.
  Task version > tool version, or task version present and tool `VERSION` missing or
  malformed → writes exit 3 `unsupported-contract-version`; reads proceed and add the warning
  `unsupported-contract-version`.

### Read outcomes

| Situation | `get` | `validate` |
|---|---|---|
| `state.md` missing | exit 3, `rejected`, `state-missing` | exit 3, `invalid`, `state-missing` |
| Section missing or duplicated; encoding refused | exit 3, `rejected` | exit 3, `invalid` |
| `--block X`, X unique and well-formed | exit 0, `read`; problems in other blocks listed in `warnings` | checks X only |
| `--block X`, X absent / duplicated / malformed | exit 3, `rejected`, `block-missing` / `block-duplicate` / `malformed-block` | exit 3, `invalid` |
| No `--block`, every block unique and well-formed | exit 0, `read`, all blocks | checks all blocks |
| No `--block`, any block duplicated or malformed | exit 3, `rejected`, one error per problem, `blocks` omitted | exit 3, `invalid`, every error listed |
| `--field NAME` absent from the block | exit 0; `header_fields` and `fields` empty | — |
| Unrecognized prefix | exit 0; `prefix` reported, read as leaf, warning `unrecognized-prefix` | warning only |
| Unknown header field | exit 0; field in `header_fields`, warning `unknown-header-field` | warning only |
| Required field missing (I-6) | exit 0; warning `required-field-missing` | exit 6, `invalid`, `required-field-missing` |
| Malformed `state_receipts:` line (over 20 entries, bad entry, repeated id) | exit 0; warning `malformed-receipts` | exit 3, `invalid`, `malformed-receipts` |

`get` exits non-zero exactly when `errors` is non-empty; `warnings` never change the exit.
`--field NAME` filters both `header_fields` and `fields` to that name; repeated `notes` groups
appear as separate entries in file order.

### Output (stdout, one JSON object)

Common keys: `schema_version` (1), `command`, `result`, `task` (task path relative to root),
`source_revision`, `errors` (list of `{"code", "message", "line"?}`), `warnings` (list of
codes), `stale_temp_files` (list of names).

| Command | `result` | Extra keys |
|---|---|---|
| `get` | `read` / `rejected` | `contract_version` (string or null), `blocks`: list of `{block_id, block_kind, prefix, name, header_fields, fields: [{name, value, continuation: [..], known}], pre_tdd_exception}`; with `--field`, `fields` holds that field only |
| `validate` | `valid` / `invalid` | — |
| write commands | `applied`, `already_applied`, `unchanged`, `rejected` | `operation_id`, `block_id`, `block_kind`, `result_revision` (current file revision after the command; equals `source_revision` unless applied), `changed_fields` |
| refusal with exit 5 | `rejected` | `lock_owner` (parsed metadata or null), `lock_age_seconds` (integer or null), `stale_suspected` (true when age ≥ 600) |

`result_revision` is never a historical value: storing the revision of a file inside that
file is self-referential (A-03).

### Exit codes and error codes

| Exit | Meaning | Error codes |
|---|---|---|
| 0 | Read, valid, applied, already applied, unchanged | — |
| 1 | Unexpected internal error | `internal-error` |
| 2 | Invalid invocation | `invalid-arguments`, `unknown-command`, `malformed-revision`, `invalid-operation-id`, `path-outside-root` |
| 3 | Structure or version refused | `state-missing`, `malformed-receipts`, `section-missing`, `section-duplicate`, `block-missing`, `block-duplicate`, `malformed-block`, `unrecognized-prefix`, `unknown-header-field`, `unsupported-contract-version`, `unsupported-encoding` |
| 4 | Revision conflict | `revision-conflict`, `state-file-changed` |
| 5 | Lock busy | `lock-busy` |
| 6 | Field, value or invariant refused | `invalid-value`, `downgrade`, `pinned-transition`, `n-a-unjustified`, `completion-without-tests`, `pre-tdd-not-applicable`, `invalid-transition`, `required-field-missing` (validate), `read-only-field`, `field-not-applicable`, `block-exists`, `invalid-path` |
| 7 | File system or runtime | `io-error`, `unsafe-state-file`, `unsafe-lock-path`, `locking-unavailable`, `python-too-old` |
| 8 | Operation conflict | `operation-conflict` |

`validate` exits 0 when valid, 3 when any structure error exists, otherwise 6 when any
invariant error exists. Its static checks are: structure, I-1, I-4, I-5 (static part:
`complete` with `green`, `n-a`, or absent `atomic-tests` plus the pre-TDD note), I-6, and
`state_receipts:` format (1–20 entries, entry pattern, unique ids; violation
`malformed-receipts`, exit 3). I-2, I-3, I-7–I-10 need a
previous value and apply to writes only.
The stderr text for exits 4, 5, 6 and 8 contains the sentence
`Do not edit state.md by hand to bypass this refusal.`

### Test seam (REQ-25)

`STATE_TOOL_TEST_FAULT` values: `kill-before-replace` (SIGKILL self after step 10),
`kill-after-replace` (SIGKILL self after the rename in step 12), `pause-before-recheck`
(before step 11, wait until the file named by `STATE_TOOL_TEST_RESUME` exists, at most 10 s).
Any other value is ignored.

### Contract-file changes

- `rules/workflow-globals.md`: one anchored line
  `Tool-managed field state_receipts: <operation_id>#<16-hex digest>, … — at most 20 entries, oldest first; written only by scripts/state-tool.py; never edited or removed by hand or by /compress-state.`
  plus a reader rule that blocks without it are valid.
- `rules/workflow-reference.md → ## Protected Sections Contract`: `state_receipts:` lines.
- `scripts/validate-task.sh`: a check that every `state_receipts:` line has 1–20 well-formed
  entries and unique operation ids.
- `scripts/validate-contracts.sh`: checks for the anchored line, the protected entry, and
  equality between the tool's vocabulary constants and the anchored vocabulary lines. The
  constants are module-level tuples of string literals, each on one line, in the order of
  the anchored line: `ATOMIC_STATUS_VALUES` (`rules/workflow-globals.md:195`),
  `ATOMIC_TESTS_VALUES` (`:197`), `ROLLUP_VALUES` (`:218`), `INTEGRATION_VALIDATION_VALUES`
  (`:219`); example: `ATOMIC_TESTS_VALUES = ("not-started", "red", "pinned", "green", "n-a", "failed")`.
- `scripts/README.md`: an inventory row for `state-tool.py`.
- `.gitignore`: the lines `.state-tool.lock` and `.state.md.*.tmp` (REQ-26).
- `scripts/setup-new-project.sh`: the same two patterns in `GITIGNORE_ENTRIES`
  (`scripts/setup-new-project.sh:247-254`), and the entry list in `docs/USAGE.md:310`.
- `docs/USAGE.md`: a "State tool" section (commands, exit codes, manual fallback).
- File names follow constraint C-4.

## Non-Functional Requirements

| Attribute | Target | Verification |
|---|---|---|
| Portability | Python 3.11+, standard library only; Linux and macOS local filesystems for writes | Static import scan in the test suite (AC-19) |
| Security | No `subprocess`, `os.system`, `os.exec*`, `eval`, `exec`, `shell=True`; values never interpreted | Static AST scan (AC-19); metacharacter fixture (AC-08) |
| Determinism | Same input bytes and arguments give byte-identical `state.md` and stdout, excluding lock-file metadata | Double-run fixture in AC-02 |
| Atomic visibility | Readers see either the old or the new full file | AC-06 |
| Durability | Best effort: file and directory `fsync`; filesystems that ignore `fsync` are not covered | Documented limitation; AC-06 warning case |
| Performance | N/A — no evidence of cost; one invocation per write on a file of a few hundred lines; revisit with run-log evidence | — |
| Observability | Machine JSON on stdout, human diagnostics on stderr; no run-log writes (logging belongs to `scripts/log-step.sh`, P9) | AC-14 |

## Edge Cases & Failure Modes

| Case | Expected behaviour | REQ |
|---|---|---|
| Empty `state.md` or no progress section | Reads: exit 3 `section-missing`; `init-block`: exit 3 | REQ-02, REQ-16 |
| Section present, no blocks | `get` returns empty `blocks`; `init-block` inserts directly after the heading | REQ-16 |
| Duplicate section / duplicate target id | Exit 3, no write | REQ-02 |
| Duplicate id of a non-target block | `get --block` on another block: warning; `get` without `--block`: exit 3; writes to other blocks proceed | REQ-02 |
| Several `notes:` field groups in one block | Valid; notes text spans all groups; appends follow the last group | REQ-17 |
| Repeated `last_action:` (or another known non-`notes` field) | Block malformed: writes exit 3 | REQ-02 |
| Target block already violates an invariant in a field the operation does not change | Write proceeds; warning `pre-existing-violation` | REQ-04 |
| Leaf missing `notes:` or `target_files:` | Reads and unrelated writes warn `required-field-missing`; `append-note` / `add-file` insert the line | REQ-17, REQ-18 |
| Hand-edited `state_receipts:` line (over 20 entries, bad entry, repeated id) | Writes to that block exit 3 `malformed-receipts`; `validate` exit 3; `get` warns | REQ-02 |
| `set` naming a read-only field with its current value | Exit 6 `read-only-field` (checked before the `unchanged` shortcut) | REQ-04 |
| Leaf without `atomic-tests` at `atomic-execution: not-started` moved to `in-progress` without `atomic-tests` | Exit 6 `pre-tdd-not-applicable` | REQ-04 |
| `atomic-tests` `n-a`, `failed` or `not-started` set to `green` | Exit 6 `invalid-transition` | REQ-04 |
| Existing `target_files:` entries containing spaces or prose | Compared as whole entries split on `, ` | REQ-18 |
| Block-like lines inside a fence | Ignored | REQ-02 |
| Tab-indented or 1-space line inside target block | Exit 3 `malformed-block` | REQ-02 |
| Unrecognized prefix `[x] T-01` | Read as leaf; writes exit 3 | REQ-13 |
| Unknown header field `atomic-foo:` | Reads report it; writes exit 3 | REQ-13 |
| `contract_version` greater than tool `VERSION`; absent or malformed; tool `VERSION` missing | See `### Contract version check`: greater or tool version missing → writes exit 3, reads warn; task line absent or not matching → no check | REQ-13 |
| CR bytes, BOM, invalid UTF-8 | Writes exit 3 `unsupported-encoding`; reads exit 3 | REQ-02 |
| Missing final newline | Preserved; inserted lines keep the file's last-line state | REQ-01 |
| `state.md` missing in the task directory | Exit 3 `state-missing` | REQ-02 |
| `state.md` replaced by another inode with identical bytes during a write | Exit 4 `state-file-changed` | REQ-09 |
| Quoted `notes:` value | Treated as opaque text; appends add a continuation line | REQ-17 |
| Note with shell metacharacters | Stored literally | REQ-09 |
| Note with newline, CR or NUL | Exit 6 `invalid-value` | REQ-17 |
| Path with `..`, absolute, comma, empty | Exit 6 `invalid-path` | REQ-18 |
| Task outside root, symlinked task escaping root | Exit 2 `path-outside-root` | REQ-09 |
| `state.md` or lock path is a symlink | Exit 7 `unsafe-state-file` / `unsafe-lock-path` | REQ-09 |
| Lock held by a live process | Wait up to bound, then exit 5 with owner metadata | REQ-06 |
| Lock held longer than 600 s | Exit 5 with `stale_suspected: true`; no takeover | REQ-06 |
| Holder killed | Kernel releases the lock; next writer proceeds | REQ-06 |
| Lock metadata names a reused PID but no flock is held | Lock acquired; metadata alone never blocks | REQ-06 |
| Unreadable lock metadata while busy | Exit 5 with `lock_owner: null` | REQ-06 |
| Two tool writers with the same revision | Second gets exit 4 | REQ-05 |
| External editor changes the file during a write | Exit 4 `state-file-changed` when detected at step 11; a change after step 11 is an accepted limitation | REQ-09 |
| Killed before or after replace | Whole old or whole new file; retry gives `applied` or `already_applied` | REQ-07, REQ-08, REQ-12 |
| Leftover temporary files | Reported in `stale_temp_files`; not deleted | REQ-12 |
| Disk full or permission denied | Exit 7, `state.md` unchanged | REQ-07 |
| Directory `fsync` fails after rename | `applied` with warning `directory-sync-failed`, exit 0 | REQ-07 |
| Same `operation_id`, different inputs | Exit 8 | REQ-08 |
| Retry after its receipt was dropped (21+ later writes) | Treated as new; usually exit 4 because the revision moved | REQ-19 |
| `set` with one invalid of several fields | Exit 6, nothing changed | REQ-23 |
| `set` with values equal to current | `unchanged`, no write, no receipt | REQ-11 |
| `fcntl` unavailable (Windows) | Writes exit 7, reads work | REQ-24 |
| Python older than 3.11 | Exit 7 `python-too-old` | REQ-22 |
| Concurrency between reads and writes | Reads take no lock and see one complete file because writes rename | REQ-07 |

## Acceptance Criteria

Fixtures are disposable task directories; "unchanged" means byte, mode and mtime identity of
every file in the task directory unless stated otherwise.

- **AC-01** (REQ-02): Given a fixture with leaf `T-01`, composite `[composite] T-02`, and a
  fenced block containing `## Subtask Progress` and `T-01 | Example | atomic-tests: red | atomic-execution: not-started | atomic-validation: not-started`,
  when `get --block T-01` and `get --block T-02` run, then both exit 0 with `block_kind`
  `leaf` and `composite` and the fenced lines are not reported; and given fixtures with two
  progress sections, two `T-01` headers, or a tab-indented line in `T-01`, when `set` targets
  `T-01`, then each exits 3 with `section-duplicate`, `block-duplicate` or `malformed-block`
  and the fixture is unchanged.
- **AC-02** (REQ-01, REQ-03): Given a fixture whose leaf `T-01` has, in order,
  `last_action:`, an empty `target_files:`, `blocker: none`, a quoted `notes:` value with
  9-space continuation lines including an inner blank line, and an unknown field
  `  verification: x`, plus a column-0 foreign line after `T-01` and text in other sections,
  when `set --block T-01 --field last_action=done` applies twice on identical copies, then
  each diff against the original is exactly the changed `last_action` line plus one
  `state_receipts:` line inserted directly after the last `notes` continuation line and
  before `verification: x`, and both results are byte-identical.
- **AC-03** (REQ-04, REQ-13): Given leaf blocks in the states below, when `set` runs, then the
  results are: `pinned → green` applied; `pinned → red` exit 6 `pinned-transition`;
  `green → red` exit 6 `downgrade`; `red → not-started` exit 6 `downgrade`; `→ n-a` without a
  `tdd: none — ` note exit 6 `n-a-unjustified`; `→ n-a` with `--note "tdd: none — smoke considered; no executable surface"`
  applied; `n-a → green`, `failed → green` and `not-started → green` exit 6
  `invalid-transition`; `atomic-execution → done` exit 6 `invalid-value`; a block with
  `atomic-foo: x` in the header exit 3 `unknown-header-field`; a block headed
  `[x] T-03 | …` exit 3 `unrecognized-prefix` while `get --block T-03` exits 0 with
  `prefix` `[x]`; a file with
  `contract_version: 99.0.0` exit 3 `unsupported-contract-version` while `get` exits 0; every
  refused fixture is unchanged.
- **AC-04** (REQ-05): Given revision R0, when writer A applies `set` with R0 and writer B then
  runs another `set` with R0, then B exits 4 `revision-conflict` and the file equals A's
  result; and given a change to another section after R0, when `set` runs with R0, then it
  exits 4 and the other section's new text is retained.
- **AC-05** (REQ-06; rewritten 2026-11-13, D-03): Given a helper process holding `flock` on
  `.state-tool.lock` with metadata `started_at` 660 s in the past, when `set
  --lock-wait-seconds 1` runs, then it exits 5 `lock-busy` with matching `lock_owner`,
  `stale_suspected: true`, and `state.md` and the lock file unchanged; given the helper is
  then killed with SIGKILL, when the same `set` reruns, then it exits 0 `applied`; given lock
  metadata naming the live PID of an unrelated process but no `flock` held, when `set` runs,
  then it exits 0 `applied`.
- **AC-06** (REQ-07, REQ-12, REQ-25): Given `STATE_TOOL_TEST_FAULT=kill-before-replace`, when
  `append-note` runs, then the process dies, `state.md` is unchanged, one
  `.state.md.*.tmp` exists, a following `validate` lists it in `stale_temp_files` and does not
  delete it, and a retry with the same `operation_id` and R0 exits 0 `applied` with the note
  present once; given `kill-after-replace`, when `append-note` runs and is retried with the
  same `operation_id`, then the retry exits 0 `already_applied` and the note occurs once; given
  an in-process test where the directory `fsync` raises, then the result is `applied` with
  warning `directory-sync-failed` and exit 0.
- **AC-07** (REQ-08, REQ-19): Given each write command applied once with `operation_id` X,
  when it is repeated with identical inputs and a stale revision, then it exits 0
  `already_applied` and the file is unchanged; when X is reused with different inputs, then it
  exits 8 `operation-conflict`; given 21 applied operations on one block, then its
  `state_receipts:` holds the 20 newest entries in order.
- **AC-08** (REQ-09, REQ-25): Given `--task` with a `..` escape or a symlinked directory
  leaving root, when `set` runs, then it exits 2 `path-outside-root`; given `state.md` as a
  symlink, then exit 7 `unsafe-state-file`; given `pause-before-recheck` and `state.md`
  rewritten by the test during the pause, then exit 4 `state-file-changed`, the test's bytes
  are retained and the tool's temporary file is gone; given `pause-before-recheck` and
  `state.md` replaced during the pause by a different file with identical bytes (new inode),
  then exit 4 `state-file-changed`; given a note
  `$(touch pwned); rm -rf x`, then the note is stored literally and no `pwned` file exists.
- **AC-09** (REQ-10; rewritten 2026-11-13): Given refusals with exits 4, 5, 6 and 8, then each
  stderr contains `Do not edit state.md by hand to bypass this refusal.`; and
  `docs/USAGE.md` has a "State tool" section listing the manual fallback steps: stop
  concurrent writers, read the whole block, change only the needed fields, review the diff,
  run `scripts/validate-task.sh`, record the reason in `notes:`.
- **AC-10** (REQ-11): Given any fixture, when `get` and `validate` run, then every file in the
  task directory is unchanged and no file (including `.state-tool.lock`) is created; when
  `set --field last_action=x` applies, then `changed_fields` is
  `["last_action", "state_receipts"]` and every header status is unchanged.
- **AC-11** (REQ-03, REQ-04, REQ-21): Given a leaf without `atomic-tests:` and
  `atomic-execution: in-progress`, when `get` runs, then `pre_tdd_exception` is `applicable`
  and the file is unchanged; when `set --field atomic-execution=complete` runs without the
  note, then exit 6 `completion-without-tests`; with `--note "pre-TDD task, TDD step skipped"`,
  then `applied` and the header still has no `atomic-tests` segment; given a leaf with
  `atomic-tests: not-started` or `red`, then completion exits 6 `completion-without-tests`;
  given a leaf with `atomic-tests: not-started` and `atomic-execution: not-started`, then
  `pre_tdd_exception` is `not-applicable`; given a leaf without `atomic-tests:` and
  `atomic-execution: not-started`, when `set --field atomic-execution=in-progress` runs, then
  exit 6 `pre-tdd-not-applicable`, and with `--field atomic-tests=red` added it is `applied`.
- **AC-12** (REQ-14): Withdrawn 2026-11-13 with REQ-14 (D-01).
- **AC-13** (REQ-03, REQ-11): Given a leaf missing `blocker:` and with `atomic-tests:`
  absent, when `set --field blocker=none --field atomic-tests=red` applies, then `blocker:
  none` is inserted directly after `target_files:` and `atomic-tests: red | ` is inserted
  directly before `atomic-execution:`; no other line moves.
- **AC-14** (REQ-15): Given an unknown command, a write without `--operation-id`, a
  `--expected-revision` not matching `^sha256:[0-9a-f]{64}$`, or an invalid `operation_id`,
  then exit 2; for every AC run without `STATE_TOOL_TEST_FAULT`, stdout parses as exactly
  one JSON object with `schema_version` 1, and every refusal writes a non-empty stderr.
- **AC-15** (REQ-16): Given a section whose last block ends with `  pr: none` followed by one
  blank line and `## Next`, when `init-block --block T-05 --kind leaf --name Demo` applies,
  then the file shows `  pr: none`, a blank line, the canonical leaf lines for `T-05`, a blank
  line, `## Next`; given a section holding only its heading, then the block follows the
  heading directly; given an existing `T-05`, then exit 6 `block-exists` and the fixture is
  unchanged; given `--kind composite` without `--note`, or `--target-file` with
  `--kind composite`, then exit 2 `invalid-arguments`; given no section, then exit 3
  `section-missing`.
- **AC-16** (REQ-17, REQ-23): Given empty `notes:`, when `append-note --note a --note b`
  applies, then the block reads `  notes: a` followed by `         b`; given non-empty notes
  with continuation lines, then the new line follows the last continuation line; given a
  block with three `notes:` field groups (task-05 shape), then the new line follows the last
  line of the third group; given a note containing LF, then exit 6 and no note from the same
  call is written.
- **AC-17** (REQ-18): Given `target_files: a.sh`, when `add-file --path b.sh --path a.sh`
  applies, then the line is `target_files: a.sh, b.sh`; when `add-file --path a.sh` runs, then
  `unchanged` and the file is unchanged; given `/abs`, `../x`, `a,b` or an empty path, then
  exit 6 `invalid-path`.
- **AC-18** (REQ-20): Given the source tree, then `scripts/validate-contracts.sh` passes and
  fails on a mutation fixture where a tool vocabulary constant differs from
  `rules/workflow-globals.md`, where the anchored `state_receipts:` line is absent, or where
  the protected-list entry is absent; and `scripts/validate-task.sh` fails a fixture with 21
  entries, a malformed entry or a repeated operation id, and passes a well-formed one.
- **AC-19** (REQ-22, REQ-24): Given the tool source, then a static AST scan finds only
  standard-library imports and none of the forbidden calls under Non-Functional
  Requirements; the Python-version guard precedes all imports other than `sys` and exits 7
  `python-too-old`; given a harness that runs the tool with `fcntl` import blocked, then `get`
  exits 0 and `set` exits 7 `locking-unavailable` with the fixture unchanged.
- **AC-20** (REQ-23, REQ-04): Given a leaf `T-01`, when
  `set --field last_action=x --field atomic-execution=done --note y` runs, then exit 6
  `invalid-value` and the fixture is unchanged; when
  `set --field atomic-tests=n-a --field last_action=x --note "tdd: none — smoke considered; no executable surface"`
  runs on `atomic-tests: not-started`, then `applied` with all three changes in one revision.
- **AC-21** (REQ-04, REQ-17, REQ-18): Given a leaf with `atomic-tests: n-a` whose notes contain `tdd: none - x`
  (hyphen, not em dash), when `set --field last_action=y` runs, then `applied` with warning
  `pre-existing-violation`; when `validate` runs on the result, then exit 6 with
  `n-a-unjustified`; given a leaf without `notes:` and without `target_files:`, when `get`
  runs, then exit 0 with warning `required-field-missing`, `validate` exits 6
  `required-field-missing`, `append-note --note a` inserts `  notes: a` after the
  `blocker:` group, and `add-file --path b.sh` inserts `  target_files: b.sh` after the
  `last_action:` group; given `set --field pr=<its current value>`, then exit 6
  `read-only-field`.
- **AC-22** (REQ-02, REQ-13): Given duplicated `T-02` and well-formed `T-01`, then
  `get --block T-01` exits 0 with a warning, `get` without `--block` exits 3 `rejected` with
  `block-duplicate`, and `validate` exits 3; given no `state.md`, then `get` exits 3
  `state-missing`; given `get --block T-01 --field pr` where `pr` is absent, then exit 0 with
  empty `header_fields` and `fields`; given a task with `contract_version: 0.9.0` and the
  tool's `VERSION` file removed, then `set` exits 3 `unsupported-contract-version` and `get`
  exits 0 with that warning; given a `T-01` whose `state_receipts:` line holds 21 entries,
  then `set` on `T-01` exits 3 `malformed-receipts` with the fixture unchanged, `validate`
  exits 3, and `get --block T-01` exits 0 with warning `malformed-receipts`; given
  a leaf header `T-04` containing `atomic-foo: x`, then `get --block T-04` exits 0 with
  warning `unknown-header-field`.
- **AC-23** (REQ-26): Given this repository, when `git check-ignore -q` runs on
  `.ai/tasks/todo/task-x/.state-tool.lock` and on
  `.ai/tasks/todo/task-x/.state.md.0123456789abcdef0123456789abcdef.tmp`, then both exit 0,
  and on `.ai/tasks/todo/task-x/state.md` it exits 1; given a disposable git project where
  `scripts/setup-new-project.sh` ran twice, then its `.gitignore` contains the lines
  `.state-tool.lock` and `.state.md.*.tmp` exactly once each; and the entry list in
  `docs/USAGE.md` names both patterns.

## Traceability

| REQ | AC |
|---|---|
| REQ-01 | AC-02 |
| REQ-02 | AC-01, AC-22 |
| REQ-03 | AC-02, AC-11, AC-13 |
| REQ-04 | AC-03, AC-11, AC-20, AC-21 |
| REQ-05 | AC-04 |
| REQ-06 | AC-05 |
| REQ-07 | AC-06 |
| REQ-08 | AC-07 |
| REQ-09 | AC-08 |
| REQ-10 | AC-09 |
| REQ-11 | AC-10, AC-13 |
| REQ-12 | AC-06 |
| REQ-13 | AC-03, AC-22 |
| REQ-14 | Withdrawn (AC-12 withdrawn) |
| REQ-15 | AC-14 |
| REQ-16 | AC-15 |
| REQ-17 | AC-16, AC-21 |
| REQ-18 | AC-17, AC-21 |
| REQ-19 | AC-07 |
| REQ-20 | AC-18 |
| REQ-21 | AC-11 |
| REQ-22 | AC-19 |
| REQ-23 | AC-16, AC-20 |
| REQ-24 | AC-19 |
| REQ-25 | AC-06, AC-08 |
| REQ-26 | AC-23 |

## Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Lock and temporary files appear as untracked files where `.ai/` is tracked (this repository tracks it in full) | Noise in `git status`; accidental commit | High here, low in consumers | Ignore rules (REQ-26, D-10) |
| External editors ignore the lock | Lost update outside the recheck window | Medium while workflows edit by hand | Step 11 recheck; documented limitation; manual procedure requires stopping concurrent writers |
| Grammar duplicated in `rules/workflow-globals.md` and `rules/workflow-reference.md` drifts | Tool follows one copy, workflows the other | Medium | Drift check (AC-18) pins the tool to `workflow-globals` |
| Tool stays unused because it is optional and unwired | Effort without effect | Medium | Accepted by the owner at scheduling (D-09); wiring is a follow-up spec |
| Network filesystems give weak `flock` semantics | Mutual exclusion fails | Low | Out of scope; documented |
| Receipt line grows block size | Larger `state.md` | Low | 20-entry cap |
| Real blocks contain shapes the grammar marks malformed | Writes refused on legacy tasks | Low: the header pattern and line grammar matched all 98 block headers and found no malformed line across the eight completed tasks' `state.md` on 2026-11-13 | Writes refuse rather than guess; reads still work; collect consumer examples at scheduling (C-2) |

## Assumptions

- A-01 | Receipt field name | Resolved: `state_receipts` with an underscore, matching field-line names | Source: `rules/workflow-globals.md:178-187` naming pattern | Reversible: yes
- A-02 | Receipt entry and digest format | Resolved: `<operation_id>#<16-hex>` with the stated id pattern and canonical JSON digest | Source: best practice (smallest unambiguous form) | Reversible: yes
- A-03 | Historical result revision in `already_applied` (original §8 step 5) | Resolved: not stored; `result_revision` is the current revision, because a file cannot contain its own hash | Source: best practice | Reversible: yes
- A-04 | Lock file name, wait default and bound | Resolved: `.state-tool.lock`, 5 s default, 0–600 s, 25 ms polling | Source: `scripts/install-hooks.py:528-541` | Reversible: yes
- A-05 | Hang threshold | Resolved: 600 s sets `stale_suspected`, never takeover | Source: ADR-0009 Decision 5 ten minutes, reinterpreted by D-03 | Reversible: yes
- A-06 | Git fields, `children:` and unknown fields | Resolved: read-only in this version | Source: `rules/workflow-globals.md:233-236`; smallest reversible choice | Reversible: yes
- A-07 | Notes and target files mutation | Resolved: append-only / add-only | Source: `rules/workflow-globals.md:226-238`; `.ai/principles/domain.md:60-61` | Reversible: yes
- A-08 | Note continuation indentation | Resolved: 9 spaces | Source: `.ai/tasks/completed/task-00-sensitive-data-scrub/state.md:88-89` | Reversible: yes
- A-09 | Encoding and line endings | Resolved: UTF-8 without BOM, LF only; otherwise exit 3 | Source: best practice | Reversible: yes
- A-10 | Section creation and insertion point | Resolved: `init-block` needs an existing section and inserts after its last non-blank line | Source: `workflows/pd-decompose.md:159` owns section initialization | Reversible: yes
- A-11 | Locking for reads | Resolved: reads take no lock | Source: best practice (atomic rename gives readers a complete file) | Reversible: yes
- A-12 | Version source | Resolved: compare task `contract_version:` with the `VERSION` file of the tool's own checkout | Source: `workflows/pd-analyze.md:53-58` | Reversible: yes
- A-13 | Windows | Resolved: reads only | Source: best practice (`fcntl` absent) | Reversible: yes
- A-14 | `validate` exit split | Resolved: 3 for structure, 6 for invariants | Source: original exit-code table | Reversible: yes
- A-15 | `n-a` justification match | Resolved: substring `tdd: none — ` | Source: `rules/tdd.md:78` | Reversible: yes
- A-16 | Meaning of "downgrade" | Resolved: rank order in I-2 | Source: `rules/workflow-globals.md:199-201,231-232`; best practice for the ordering inside rank 1 | Reversible: yes
- A-17 | Required values | Resolved: `last_action` and `blocker` values non-empty when set; `last_action:` empty at creation | Source: `rules/workflow-globals.md:178-180`; `workflows/pd-decompose.md:160-162` | Reversible: yes
- A-18 | Directory sync failure after rename | Resolved: `applied` with a warning | Source: best practice (the change is already visible) | Reversible: yes
- A-19 | Header `NAME` and block id grammar | Resolved: patterns under `## Data Model` | Source: `workflows/pv-create-fixes.md:59,75`; observed ids | Reversible: yes
- A-20 | Repeated field lines | Resolved: `notes` repeatable; other repeated known fields malformed; unknown repeats preserved | Source: `.ai/tasks/completed/task-05-cost-and-duration-telemetry/state.md:133-136` (only `notes` repeats across the eight completed tasks) | Reversible: yes
- A-21 | Invariant scope on legacy blocks | Resolved: write invariants apply to changed fields; other violations become warnings | Source: best practice (refuse no unrelated write on legacy data) | Reversible: yes
- A-22 | `init-block` layout | Resolved: one blank separator except directly after the heading | Source: `.ai/tasks/completed/task-03-hook-based-logging/state.md:361-363`; `.ai/tasks/completed/task-01-git-source-of-truth/state.md:33-34` | Reversible: yes
- A-23 | Missing tool `VERSION` with a versioned task | Resolved: writes refused, reads warn | Source: best practice (fail closed for writes) | Reversible: yes

## Decisions

- D-01 | Keep the tool in the backlog with an implementation-ready design; withdraw REQ-14 and AC-12 into constraint C-1 | Overrides: none (consistent with ADR-0009 Decision 5) | Rationale: a scheduling rule cannot be tested in the tool | Follow-up: backlog status ended by D-09
- D-02 | Rewrite the specification in English in the spec-draft structure, preserving ids, the implementation review and the change log | Overrides: none | Rationale: English-only rule (`.ai/principles/coding.md:11`) | Follow-up: none
- D-03 | OS advisory lock (`fcntl.flock`) released by the kernel; no stale takeover; ten minutes only reports a possible hang | Overrides: ADR-0009 Decision 5 "per-task lock with 10-minute stale override" | Rationale: age never proves owner death; kernel release covers dead owners | Follow-up: recorded in `.ai/adr/0021-task-07-schedule-state-tool.md`
- D-04 | Durable receipts in an additive in-block field, capped at 20 per block | Overrides: none (additive under P3) | Rationale: atomic with the block change | Follow-up: contract-file changes listed under `## Contracts & Interfaces`
- D-05 | Invariant-only checks from canonical sources (vocabularies, no-downgrade, `pinned → green`, `green` only from `red`/`pinned`, completion preconditions, pre-TDD guard); no transition table; evidence references dropped from `set`; moves inside rank 1 and atomic-validation/composite transitions are accepted gaps | Overrides: original §6 interface "evidence references" | Rationale: one source of truth; the tool never certifies test results | Follow-up: none
- D-06 | `scripts/state-tool.py`, Python 3.11+, single file | Overrides: ADR-0009 Decision 5 path `ORCHESTRAIL_HOME/bin/` | Rationale: matches existing helpers and deployment | Follow-up: recorded in `.ai/adr/0021-task-07-schedule-state-tool.md`
- D-07 | Tool only; no workflow wiring | Overrides: none | Rationale: the tool stays optional; wiring is a later spec | Follow-up: wiring spec after adoption evidence
- D-08 | Replace old-repository URLs with repository-relative paths at the pinned commit; delete the two identity-ledger rows for this file | Overrides: none | Rationale: rewrite moves the pinned lines; fewer old-identity occurrences | Follow-up: ledger rows removed in the same change
- D-09 | Schedule the tool for implementation; waive the corruption-evidence precondition (C-2) | Overrides: D-01 backlog status; ADR-0009 Decision 5 "not built now" | Rationale: owner decision of 2026-11-13; design complete, tool optional and unwired; `scripts/validate-task.sh` exits 0 on all eight completed tasks, so no corruption evidence exists to collect | Follow-up: `.ai/adr/0021-task-07-schedule-state-tool.md`
- D-10 | Add ignore rules for the lock and temporary files in this repository and in consumer setup (resolves Q-01) | Overrides: none | Rationale: this repository tracks `.ai/`; untracked auxiliary files invite accidental commits | Follow-up: REQ-26, AC-23

Rejected alternatives: full transition table (contract change every workflow must follow,
could reject legitimate recovery paths); vocabulary-only checks (lets `pinned → red` and
unjustified `n-a` through); lock directory with owner protocol (more recovery code for the
same guarantee); revision-only optimistic writes (race between check and rename); sidecar
receipt journal (two files, crash reconciliation); no receipts (identical intended notes
collapse); `bin/` location (new top-level directory for sync and layout rules).

## Clarifications

### Session 2026-11-13

- Q: May the whole file be replaced with an English spec in the spec-draft structure, keeping ids, the implementation review and the change log? → A: Full rewrite.
- Q: Keep the tool as backlog or make it schedulable? → A: Backlog with a ready design; REQ-14 moves to a constraint.
- Q: Which locking model? → A: OS advisory lock; the ten-minute rule only reports a hang; amends the ADR-0009 wording.
- Q: Where are durable operation receipts stored? → A: An in-block field.
- Q: How strictly are transitions checked? → A: Canonical invariants only.
- Q: Where does the executable live and which Python? → A: `scripts/`, Python 3.11+.
- Q: Does the spec include workflow wiring? → A: Tool only.
- Q: How many receipts per block? → A: The last 20.
- Q: How are the old-repository URLs on the ledger-pinned lines handled? → A: Drop the URLs and delete the two ledger rows.

### Session 2026-11-13 — scheduling

- Q: Is the tool scheduled now, given that no corruption evidence exists? → A: Scheduled; the evidence precondition is waived.
- Q: Are ignore rules added for the lock and temporary files (Q-01)? → A: Yes, in this repository and in consumer setup, as part of this spec.

## Open Questions

None. Q-01 (ignore rules for the lock and temporary files) was resolved by D-10 on
2026-11-13.

## Notes

### Constraints

- C-1 (former REQ-14): implementation starts only after an explicit owner decision to
  schedule 07. Satisfied 2026-11-13 by D-09.
- C-2: at scheduling, collect real corruption examples from `scripts/validate-task.sh`
  failures and confirm the value of the tool first. Waived 2026-11-13 by D-09: the
  validator exits 0 on all eight completed tasks, so none exist in this repository.
- C-3: the manual procedure and every existing mandatory stop stay in force; a validator
  failure that stops finalization stays a stop.
- C-4: rule file names in this spec are the current ones. If spec 13 has landed at
  scheduling, the targets are its renamed canonical files
  (`.ai/specs/13-model-only-harnesses-and-rule-naming.md:141-143`):
  `rules/workflow-globals.md` → `rules/contract-phases.md`, `rules/workflow-reference.md` →
  `rules/contract-state-files.md`, `rules/tdd.md` → `rules/contract-tdd.md`; the anchored line,
  protected entry, drift check and citations follow the file that then holds each definition.
- Boundaries with other specs are unchanged: 12, 14, 15, 16, 19 neither depend on nor gain a
  write interface from 07.

### Implementation hints (nonbinding)

- Hint: separate parse, invariants, write path and receipts into functions testable without
  the CLI.
- Hint: register the acceptance suite as `tests/state-tool.sh` with a focused validator mode,
  after checking the inventory constraints of ADR-0018 and ADR-0020.
- Hint: the existing validator message at `scripts/validate-task.sh:141` omits `pinned` from
  the expected list; fix it in the same change that adds the receipts check.

### Change Log

#### 2026-11-06 — implementation/state reconciliation

- Owner-authorized source review at `23bded3d96d9c562d16eb7e90285414f4412ac79`: record delivered scope, remaining obligations, and verification limits in the Implementation review above. Preserve requirement/acceptance identifiers and historical decisions; repair current local references where needed.

#### 2026-11-13 — interactive refinement

- Rewritten in English in the spec-draft structure; original text translated under
  `## Source`. REQ-02, REQ-03, REQ-04, REQ-06, REQ-07 (failure clause), REQ-10, REQ-13
  rewritten; REQ-14 and AC-12 withdrawn; REQ-15–REQ-25 and AC-13–AC-22 added; invariants
  I-1–I-10, read outcomes, contract-version check and block insertion layout defined;
  assumptions A-01–A-23, decisions D-01–D-08 and constraints C-1–C-4 recorded; two
  identity-ledger rows for this file removed (D-08).

#### 2026-11-13 — scheduling

- Owner scheduled the tool (D-09) and resolved Q-01 (D-10): backlog wording removed from
  the title, Source, Goal and Out of Scope; REQ-26 and AC-23 added; C-1 marked satisfied
  and C-2 waived; superseding decision record cited. This amendment was owner-directed and
  was not put through another Devil's Advocate round.

## Readiness Checklist

Result of 2026-11-13:

| # | Check | Result |
|---|---|---|
| 1 | Goal is one domain-language paragraph | PASS — one paragraph: problem, outcome, scheduled status |
| 2 | Out of Scope names concrete exclusions | PASS — eleven named exclusions |
| 3 | Each REQ has a stable id and one EARS behaviour | PASS — REQ-01–REQ-26, REQ-14 withdrawn with reason |
| 4 | Every REQ maps to ≥1 AC and every AC to ≥1 REQ | PASS — Traceability table; AC-12 withdrawn with REQ-14 |
| 5 | Every AC is binary and observable | PASS — exit codes, error codes and exact layouts named |
| 6 | Non-functional targets measurable or N/A | PASS — performance N/A with reason; others verified by AC-02, AC-06, AC-08, AC-14, AC-19 |
| 7 | Data model and contracts specified | PASS — grammar, writability, receipts, files, commands, outputs, exit codes |
| 8 | Error, empty, boundary, concurrency cases covered | PASS — Edge Cases & Failure Modes table |
| 9 | Every Step 3 ambiguity recorded | PASS — D-01–D-10, A-01–A-23 |
| 10 | No blocker question remains | PASS — no open question |
| 11 | Existing-code claims cited and verified | PASS — every `path:line` verified by author and critic |
| 12 | Terminology matches project definitions | PASS — Terminology table aligned with `.ai/principles/domain.md` |
| 13 | Feature-sized scope | PASS — plausibly 6–8 subtasks: parser and reads, invariants, write path, receipts, mutating commands, grammar extension and checks, documentation |
| 14 | Devil's Advocate review passed | PASS — Review: 4 rounds, score 100/100, critic: sub-agent, open: none (before the scheduling amendment, which was not re-reviewed) |

Verdict: **READY FOR DEVELOPMENT**. The owner scheduled the work on 2026-11-13 (D-09);
automated readiness is not sign-off.
