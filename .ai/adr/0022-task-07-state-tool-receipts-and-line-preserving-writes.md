# ADR-0022: Decisions for Task 07 — State tool receipts, invariant checks and line-preserving writes

## Status

Accepted

## Date

2026-11-13

## Related Task

- Task: `.ai/tasks/todo/task-07-state-tool/` (spec `.ai/specs/07-state-tool.md`)
- Related pull request: #80–#92 and the follow-up series (stacked; ten changes and three
  fixes, then five follow-up changes)
- Related files: `scripts/state-tool.py`, `tests/state-tool.py`,
  `rules/workflow-globals.md`, `rules/workflow-reference.md`, `scripts/validate-task.sh`,
  `scripts/validate-contracts.sh`, `scripts/setup-new-project.sh`, `docs/USAGE.md`

## Summary

ADR-0021 scheduled the state tool and fixed its lock, location and ignore rules. This
record covers the remaining design decisions that shape the canonical state format and
the tool's internals: operation receipts stored in an additive in-block field,
invariant-only lifecycle checks, a line-preserving write model, and the placement and
registration of the acceptance suite under the pinned test inventory.

## Context

The tool edits one block of `## Subtask Progress` in a task `state.md`. Real blocks carry
quoted note values, blank lines inside continuation runs, unknown fields and foreign
lines, all of which must survive a write byte for byte. Idempotent retries need durable
evidence that an operation was applied. Status transitions are defined by the execution
and validation workflows, not by one table. Every file under `tests/` and the contract
validator are bound by a pinned source-guard inventory fingerprint
(`tests/fixtures/validator-runtime/README.md`).

## Decisions

### Decision 1: Operation receipts live in an additive in-block field

**What was decided:** Each applied write records `<operation_id>#<16-hex input digest>` as
the last entry of a tool-managed `state_receipts:` field line of the target block, capped
at the 20 newest entries. The field is defined on one anchored line of
`rules/workflow-globals.md`, listed as protected, and checked by both validators. Blocks
without the field stay valid; readers that do not know it treat it as an unknown field.

**Why:** The receipt is written in the same atomic replace as the block change, so a
retry after an interruption can tell applied from not applied without a second file.

**Alternatives:** A sidecar receipt journal — rejected: two files need crash
reconciliation. No receipts — rejected: identical intended notes would collapse or
duplicate on retry. Storing the resulting revision — rejected: a file cannot contain its
own hash.

**Consequences:** The canonical block grammar gains one protected field (additive under
P3). A retry after 20 later writes on the same block is treated as a new operation.

**Related files:**
- `rules/workflow-globals.md`, `rules/workflow-reference.md`
- `scripts/validate-task.sh`, `scripts/validate-contracts.sh`

### Decision 2: Lifecycle checks are canonical invariants, not a transition table

**What was decided:** Writes enforce only invariants taken from canonical sources:
vocabulary membership, no downgrade of `atomic-tests` by rank, `pinned` only to `green`,
`green` only from `red` or `pinned`, justified `n-a`, completion preconditions and the
pre-TDD guard. Moves inside one rank, atomic-validation and composite statuses are
checked by vocabulary only. Invariants apply to the fields an operation changes;
pre-existing violations elsewhere become warnings.

**Why:** One source of truth: the workflows define transitions, and the tool must never
certify test results or refuse an unrelated write on legacy data.

**Alternatives:** A full transition table — rejected: a contract change every workflow
must follow, and it could reject legitimate recovery paths. Vocabulary-only checks —
rejected: `pinned → red` and an unjustified `n-a` would pass.

**Consequences:** Some illegitimate moves remain possible (accepted gaps). The tool's
vocabulary constants are pinned to the anchored lines by a drift check. Decision 8 narrows
the accepted gap for moves inside one rank on a completed leaf.

**Related files:**
- `scripts/state-tool.py`

### Decision 3: Writes use a line-preserving document model

**What was decided:** The tool keeps `state.md` as its original list of lines, classifies
each line, and applies a write as whole-line replacements and insertions by index. The
candidate is re-parsed before the replace to confirm that bytes outside the changed lines
are identical.

**Why:** Byte preservation of untouched text holds by construction instead of depending
on a faithful re-serializer for quoting, blank continuation lines and unknown fields.

**Alternatives:** Parsing the block into an object and re-serializing it — rejected: risk
of silent normalization in legacy blocks.

**Consequences:** Edit operations work on line indexes; a missing known field is inserted
at its canonical position without moving existing lines.

**Related files:**
- `scripts/state-tool.py`

### Decision 4: The acceptance suite lives under `tests/` and is registered in the validator once

**What was decided (amended 2026-11-13 by owner decision, before implementation):** The
suite is `tests/state-tool.py` (`unittest`). It is registered in
`scripts/validate-contracts.sh` — a focused `--state-tool-only` mode and a check in the
default run — once, in the change that adds the grammar-extension contract checks. That
change extends the frozen validator inventory exactly and by name: the added results, one
focused flag, the suite's resource row and the two counts. Changes before it run the suite
directly; every change under `tests/` still refreshes the pinned source-guard fixtures.
Changes after it that edit the suite refresh its pinned digest.

**Why:** The frozen validator inventory accepts no new check, focused mode or resource
row without a change to its oracle, and a registered suite pins its own digest. The
contract checks the specification requires force one oracle extension in any case;
registering the suite in the same change keeps that to one extension instead of one
rewrite of the oracle's pinned values per change.

**Alternatives:** Registration from the first change with a re-amendment in every later
change (the original form of this decision) — rejected by the owner: about ten rewrites of
a protective oracle. A permanently standalone suite — rejected: the suite would never be
part of the repository test command. A shell suite — rejected: it cannot run the
in-process directory-sync case or the static scan without embedded Python. A general
"allow additions" path in the oracle — rejected: it conflicts with the frozen inventory's
rejection of broad exemptions.

**Consequences:** Until the registration change the suite is outside the default validator
run and each stack branch verifies it directly. The oracle gains an exact, enumerated
extension, and its amendment digest changes whenever the suite changes afterwards.

**Related files:**
- `tests/state-tool.py`, `scripts/validate-contracts.sh`
- `tests/fixtures/validator-runtime/`, `tests/validator-runtime-oracle.py`

### Decision 5: `set` never deletes continuation lines

**What was decided (owner ruling, 2026-11-14):** `set` on `last_action` or `blocker` whose
existing value has continuation lines is refused with exit 6 and changes nothing, also
when the current first-line value is named.

**Why:** The line-preserving model replaces the field line only; the specification did not
say what happens to the continuation lines, and leaving them under a new value silently
changes the meaning of the block.

**Alternatives:** Replacing the whole field group — rejected by the owner: it deletes text
the caller did not name. Keeping the earlier behaviour as a documented limitation —
rejected: the write was reported as applied while the block read wrongly.

**Consequences:** Such a block is edited by the manual procedure or by appending a note.
The rule is a requirement of the reconciled specification.

**Related files:**
- `scripts/state-tool.py`, `docs/USAGE.md`

### Decision 6: Fences inside a block, blank lines and NUL bytes

**What was decided (2026-11-16; the owner delegated this ruling to independent analysts on
that day):** A fence opened at column 0 ends the current block. A fence opened at 1–3
spaces while a block is open is opaque block content together with the blank lines
directly before it: these lines belong to no field group, are never reported, changed or
used as an insertion point, and do not end the block; such a fence that is never closed
makes its block malformed (`malformed-block` at the opening line). A blank line is an empty
line: a line holding only spaces is not blank, so inside a block one or two spaces make a
malformed line and three or more a continuation line. A `state.md` that holds a NUL byte is
refused as `unsupported-encoding`, like a carriage return or a byte order mark.

**Why:** One rule for fenced text — it belongs to no field group — instead of two readings
that depended on a blank line before the fence and silently dropped the fields after it.
Damage fails closed with codes that already exist, so exit codes 0–8 and the error-code
table stay closed.

**Alternatives:** A new `unclosed-fence` code — rejected: it opens the closed table and
would replace the pinned exit 1 of `init-block`. Refusing `set` over fenced text under the
named field — rejected: it contradicts a pinned result, and the fenced lines are never
deleted or changed anyway. Counting short spaces-only lines as blank — rejected: two
meanings of blank.

**Consequences:** A column-0 fence that is never closed remains a documented limit: it runs
to the end of the file, the blocks after it are not read, and `init-block` exits 1 with
nothing written. Bytes written change only for blocks with blank lines before an in-block
fence. A run of blank lines is scanned once, which removes a quadratic read time.

**Related files:**
- `scripts/state-tool.py`, `docs/USAGE.md`, `.ai/specs/07-state-tool.md`

### Decision 7: Refusals for continued target files and whitespace-only text, and the read-only state file

**What was decided (2026-11-16; the owner delegated these rulings to independent analysts
on that day):** `add-file` on a block whose `target_files` value has continuation lines is
refused with exit 6 (`invalid-value`), also when every named path is already listed: it
reads and writes the field line only. A text input that must be non-empty must hold a
non-whitespace character: a whitespace-only note or block name is `invalid-value`, a
whitespace-only path is `invalid-path`, and a path with leading or trailing whitespace is
`invalid-path` as well; an existing whitespace-only `target_files:` value has no entries.
A `state.md` the caller cannot open for writing is not replaced: exit 7 (`io-error`)
before any temporary file exists. A field line named like a header status is an ordinary
unknown field: `set` on that status changes the header segment only.

**Why:** The same rule as Decision 5 — refuse rather than guess or delete: reading
continuation lines as further entries would invent a list grammar the contract does not
define, and ignoring them wrote a duplicated entry. The tool already treated a
whitespace-only `last_action` or `blocker` as empty, so one rule now covers every text
input; a path is a list entry compared by exact equality, so surrounding whitespace would
create near-duplicate entries. A read-only permission is an explicit instruction not to
modify the file, and the rename needs only directory permission, so it was not honoured.
An internal error for input the grammar allows is a tool fault; the reader already reports
such a field line as an unknown field.

**Alternatives:** Reading the continuation lines of `target_files` as entries — rejected:
guesses a grammar. Refusing leading or trailing whitespace on notes and names too —
rejected: they are opaque text stored literally, and it would be a second rule. Refusing a
write on any ownership difference of `state.md` — rejected: it needs a policy for shared
files. Making a block with a status-named field line malformed — rejected: it turns blocks
that `validate` accepts into structure errors for every command.

**Consequences:** A block with a continued `target_files` value is edited by the manual
procedure. Existing note text, including a whitespace-only `notes:` value, is still never
altered. Results decided before the replace (`already_applied`, `unchanged`, earlier
refusals) are unchanged on a read-only file. The writability probe opens the file without
truncation, without following links and without blocking, like every open of the state
file. An applied write still replaces the file by rename, so the new file belongs to the
user who ran the tool. No exit code or error code is added.

**Related files:**
- `scripts/state-tool.py`, `docs/USAGE.md`, `.ai/specs/07-state-tool.md`

### Decision 8: A tests-status change may not break a completed leaf

**What was decided (2026-11-16; the owner delegated this ruling to independent analysts on
that day):** A `set` that changes `atomic-tests` to a value other than `green` or `n-a` on
a leaf whose `atomic-execution` is `complete`, without changing `atomic-execution` in the
same call, is refused with exit 6 (`completion-without-tests`). The tests-transition rules
are judged first, so `downgrade`, `pinned-transition`, `invalid-transition` and
`n-a-unjustified` keep precedence. This narrows the accepted gap of Decision 2: moves
inside one rank stay allowed except where they would break a completion the write keeps.

**Why:** The tool reported as applied a write that created a violation its own `validate`
then reported, under a warning named `pre-existing-violation` although the write had
created it. The completion rule and its code already exist; one condition closes the gap.

**Alternatives:** Keeping the write and adding a distinct warning — rejected: a new warning
code, and the tool would still write a block its own check rejects. Keeping and documenting
— rejected: the warning name stays false. Requiring the `n-a` justification at completion
— rejected: that write does not create the violation, so the warning is accurate and the
rule that a pre-existing violation never blocks a write holds.

**Consequences:** The same change together with another `atomic-execution` value in one
`set`, a repair to `green`, and naming the current value are unaffected. A previous
`atomic-tests` value outside the vocabulary counts as rank 0, so it can be replaced by any
vocabulary value except `green`. The invariant-only design of Decision 2 is otherwise
unchanged.

**Related files:**
- `scripts/state-tool.py`, `docs/USAGE.md`, `.ai/specs/07-state-tool.md`

### Decision 9: Lock owner report rule; a signal is treated as a kill

**What was decided (2026-11-16; the owner delegated these rulings to independent analysts
on that day):** On a busy refusal `lock_owner` is the parsed lock file only when the whole
file is at most 65536 bytes of UTF-8 that parse as one JSON object nested at most 16
levels, with finite numbers and no lone surrogate; otherwise it is null. A repeated key is
reported with its last value. `lock_age_seconds` is null unless the reported owner records
a start time with a UTC offset that is not in the future, so it is never negative. None of
this changes the refusal: exit 5, `lock-busy`, lock file untouched. A signal whose default
action ends the process (SIGINT, SIGTERM, SIGHUP, SIGQUIT) is an interruption like a kill
at every point of a command, the lock wait included: the tool installs no signal handler,
prints no JSON object and nothing on stderr, and ends by the signal without an exit code
from the table.

**Why:** The owner report must be something the file holds as a whole and a strict JSON
consumer can read; a null value is the contract's answer for a key that cannot be
computed, and an age below zero is not an age. For signals the existing recovery
requirements already cover an interruption: `state.md` is the whole old or the whole new
file, a leftover temporary file is listed and never read as state, the kernel releases
the lock, and the identical command is repeated. No output and a non-zero status can never
be read as success.

**Alternatives:** Reporting the first 64 KiB of a longer file, or echoing a lone surrogate
— rejected: the report would not be what the file holds, or not strict JSON. Null for
repeated keys — rejected: extra parsing for a shape only a hand edit produces, while no
decision depends on the owner. Signal handlers that print one JSON object with a new
`interrupted` code and remove the temporary file — rejected: no existing code fits, the
closed table would grow, and a signal after the rename would be reported as rejected for
an applied write. Removing the temporary file and then ending by the signal — rejected:
small gain, since interrupts land in the lock wait, where nothing is on disk.

**Consequences:** An interrupt is handled only where the entry point is called (the default
action is restored and the signal re-sent), so no signal disposition changes at start-up.
A temporary file created before a signal stays behind until it is removed by hand. The
catch-all around the owner details stays, so an unforeseen failure never replaces the busy
refusal.

**Related files:**
- `scripts/state-tool.py`, `docs/USAGE.md`, `.ai/specs/07-state-tool.md`

### Decision 10: Project setup preserves a tracked knowledge base and compares whole ignore lines

**What was decided (2026-11-16; the owner delegated these rulings to independent analysts
on that day):** In its `.gitignore` step `scripts/setup-new-project.sh` treats an entry as
present only when a whole line equals it (for `.ai/` a line that is exactly `.ai` counts
too); comments, negations and longer or narrower lines never count. Before the first
append of a run it ends an unterminated last line. It skips its `.ai/` entry, with a
message, where `git ls-files .ai` lists a tracked file; it never removes a line.

**Why:** The substring comparison and the missing line break corrupted a consumer's ignore
file (joined lines, suppressed entries), and appending `.ai/` in a repository that tracks
its knowledge base contradicted the rule that the repository's tracking policy is
authoritative, which the manual had to compensate for with a removal step. The detection
is the one `scripts/sync.sh` already uses, so both scripts follow one rule.

**Alternatives:** Keeping the script and the manual's removal step — rejected: the script
keeps contradicting the tracking-policy rule. Warning about an existing `.ai/` line in a
tracking repository — not done: the script never removes or judges existing lines.

**Consequences:** A consumer that tracks `.ai/` gets the two state-tool ignore entries by
rerunning the setup script or by hand; both routes leave the knowledge base tracked. A run
that appends nothing leaves the ignore file byte-identical. The index decides tracking, so
a staged file counts and a directory outside a git repository tracks nothing.
`scripts/setup-umbrella.sh` keeps its own substring append loop and is not covered by this
decision.

**Related files:**
- `scripts/setup-new-project.sh`, `docs/USAGE.md`
- `.ai/context/runbook.md`, `.ai/context/environment.md`, `.ai/memory/architecture.md`

## Verification

Verified 2026-11-16 on the stack tip `fc63efb`: the acceptance suite `tests/state-tool.py`
(232 tests) passes; `bash scripts/validate-contracts.sh --state-tool-only` passes; the
complete contract validator reports 721 passed, 0 failed, 2 skipped (hygiene checks that
need a local pattern file). Every change and fix on the stack was validated by an
independent reviewer; the task-level contract check and code review are recorded in the
task state. Limitation: the tool is not wired into any workflow, so no workflow run has
exercised it.

Follow-up changes (Decisions 6–10), 2026-11-16: verified by the acceptance suite
`tests/state-tool.py` (347 tests), which passes through
`bash scripts/validate-contracts.sh --state-tool-only`.

Complete validator result for the follow-up changes (2026-11-16, stack tip `1ad3653`): 721 passed, 0 failed, 2 skipped (hygiene checks that need a local pattern file).
