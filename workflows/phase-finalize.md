---
description: Finalization — close one validated task after integration with evidence, safe cleanup and lossless archival
---

Invocation: `/phase-finalize <task-directory|spec-path> [--dry-run]`
Example: `/phase-finalize .ai/tasks/todo/task-add-oauth/ --dry-run`

Ordinary invocation authorizes mandatory cleanup of this resolved task's proven resources.
Continue through this one phase without another cleanup approval. This has no public child
workflows. Existing delivery parents stop at Validation and only suggest this command.

## Context Bootstrap

Load the `phase-finalize` rule (`## Context Bootstrap`) in full, including standalone runs.
Resolve `working_dir:` and the physical project root holding the selected `.ai/` before
operations. A recorded umbrella repository set is authoritative; never initialize Git in
an umbrella, infer repositories from directory names, or adopt an unrelated checkout.

Resolve `SOURCE_ROOT` from `ORCHESTRAIL_HOME` or independently verified source provenance,
never from the consumer working directory. Read `$SOURCE_ROOT/scripts/phase-finalize.py`
(the header owns the internal CLI, evidence and journal schemas) and `scripts/README.md`
from that same source. Require Python 3.11+ and all adjacent `finalization_*.py` modules.
Missing mechanics or required evidence → **stop**: report the missing prerequisite.
This is the narrow required-helper exception; optional logging, jq, model guidance and
unrelated build tools remain optional unless the project's verification contract needs them.

## Guard

Read task state and the referenced spec before writing. Use helper `inspect` with the exact
selected target and explicit `--root <physical-project-root>`. A spec must map to one task;
ambiguity → **stop**: display the candidate task paths and require an exact task target.
Resolve old task/spec paths through the stable journal, including interrupted archives.
Do not infer completion from a missing branch, closed PR, done frontmatter or directory.

Require complete independent Validation and its supporting contract/review/fix/TDD evidence.
Canonical `## Final Verification` records require dated independent successful command
receipts bound to the task/state, exact integration tips and changed-surface coverage;
legacy recorded final PASS evidence remains supported. Do not demand a hidden prose marker.
Absent `flow:` means `full`; quick work keeps its inline contract without synthetic leaves.
Missing legacy delivery fields require explicit dated ownership receipts, never guessed
branches or SHAs. Preserve original `branch`, `base_branch`, `base_commit`, `commits`, `pr`,
requirements, decisions, history and TDD records. Repeated invocation reconciles current
facts and continues the existing journal; it never overwrites a completed artifact.
Completed reruns prefer persisted journal evidence. Do not resubmit an optional input file
bound to raw state before the completion marker as newly observed evidence.

`--dry-run` takes precedence over every write below. Call only `inspect ... --dry-run`,
using existing evidence if available; report resolution, blockers, original/current full
SHAs, PR outcomes, independent outcomes, exact candidate commands, recovery packs and
archive eligibility. Create no output/evidence files, locks, directories, telemetry or
Git changes. Unavailable evidence is a blocker, never a successful measurement. Then **stop**.

## Run Logging

Apply `run-log → ## Workflow coverage and routing`; ordinary prompt steps use
`--note approximate`. After the Guard succeeds and only outside dry-run, preserve an
inherited `RUN_ID`. Otherwise open an owned run through the configured logging helper:

```bash
LOG_HELPER="${ORCHESTRAIL_HOME:+$ORCHESTRAIL_HOME/scripts/log-step.sh}"
PHASE_OWNS_RUN=false
if [ -z "${RUN_ID:-}" ] && [ -x "$LOG_HELPER" ]; then
  RUN_ID=$("$LOG_HELPER" run-start --pipeline phase-finalize \
    --project <physical-project-root> --task <resolved-task-directory> --flow <quick|full>) || RUN_ID=""
  [ -z "$RUN_ID" ] || PHASE_OWNS_RUN=true
fi
```

Log `step --run <RUN_ID> --step phase-finalize --outcome ok|blocked|failed --note approximate`
after each internal boundary, following receipt-confirmed suppression in `run-log`.
Only when `PHASE_OWNS_RUN=true`, close with `run-end --outcome completed|stopped|failed`.
An inherited run stays open for its owner. Missing or failing logging never blocks, retries,
or asks for approval; continue and mention the unavailable telemetry once. Read no log store.

## Execution

1. **Inspect delivery.** Reconcile every recorded repository/stack against original full
   SHAs, all original commits, current integration tips and live origin advertisements.
   PR evidence must be repository-bound and authoritative. Canonical numbered or URL PRs
   support GitHub SSH aliases through verified SSH translation; a path alone is no host
   identity. Reject repository/host overrides and mismatched authority responses. Preserve
   actual closed/unmerged PR outcomes even when ancestry proves delivery. Missing objects
   or unavailable reads → **stop**: report the exact missing evidence; any fetch is a
   separately visible, targeted command, followed by fresh inspection.

2. **Prepare durable recovery.** Run internal `prepare <target> --root <root> --authorize
   --expected-revision absent|<actual-journal-sha256>` (plus existing evidence if supplied).
   Invocation supplies `--authorize` only for this task. Reuse the returned stable journal
   path and actual revision on every subsequent write. `recovery-required` is incomplete:
   first validate every existing component of the exact returned recovery parent under the
   stable journal (no symlinks or path escape), then create only that missing directory.
   Execute only returned recovery argv with exact returned stdin and an exclusively created
   stdout pack path; never overwrite an existing pack. This filesystem preparation is not
   a new Git mutation. Preserve any failed attempt before a corrected retry. Rerun `prepare`
   with the new actual revision to verify
   immutable self-contained packs in isolated storage before deletion authorization.
   Show original refs/tips, pack digests, restoration commands, scope, protection/worktrees,
   exact planned argv and operation `operations` checkpoints. Never treat a receipt alone
   as authorization; canonical policy is `git-flow → ## Finalization Git ownership`.
   Before any semantic knowledge edit, supply `knowledge_inventory` with typed existing
   current Markdown record paths discovered in bootstrap. Preparation snapshots their
   exact original bytes. Record all checkout/refresh postconditions before semantic edits
   so the helper captures a clean unchanged-index baseline. Tasks, specs other than the
   scope index, historical ADR bodies, snapshots, recovery, product/config/executable
   files and uninventoried paths cannot become semantic-edit exceptions.

3. **Execute and record attempts.** Run only the helper-returned exact argv as separate
   visible hook-governed commands, in plan order, with proper shell quoting. Do not hide
   Git mutations in a script or replace a refused normal deletion. Before each command,
   recheck its current plan/receipt. After every command, preserve exact argv, exit code,
   stdout, stderr, dated execution provenance and journal-bound `source_tips` in an evidence
   `command_attempt` using the helper header's schema; assign a new immutable attempt id
   to each actual execution.
   Check attempts may bind the physical umbrella/project root or a recorded repository;
   Git action attempts must retain the exact returned repository and argv.
   Use internal `attempt ... --authorize --expected-revision
   <actual-sha256> --evidence <input-json>` to persist it, including nonzero failures.
   Planned Git operations use exact action ids/argv; executed checks use the documented
   check operation ids, including `verification`. Record `applied`, `blocked` or `preserved`;
   caller exit zero never means `verified` or task completion.

   The recorder works on the authorized bound journal even while Git/network reads fail.
   It may preserve an audit/check executed after semantic edits but before independent
   delta acceptance. It retains immutable snapshot/index/scope checks and grants neither
   current-record acceptance nor fresh deletion receipts; normal record/archive/finish
   still block unaccepted current bytes.
   It writes no Git state and does not refresh deletion receipts. When observations recover,
   use internal `record` with the actual revision to recheck refs, checkout and source tips
   and publish fresh receipts before another Git action. A failed recorder → **stop**:
   preserve the raw result and report the recorder failure. A stale revision/lock/conflicting
   attempt → reread the existing journal; never overwrite or reuse an id for changed data.
   A refused deletion, remote drift, dirty/diverged/unowned checkout or unsafe worktree
   leaves cleanup incomplete; retain the resource and report recovery and the same rerun.
   Large outputs use immutable digest-bound exact-byte artifacts; preserve those files and
   all inline failures. A bounded journal refusal preserves the previous revision. More than
   64 receipt files blocks hook matching: report exact paths/identities for owner recovery;
   never discard unrelated task evidence or bypass the bound.

4. **Verify and reconcile knowledge.** On the intended integration checkouts, execute the
   project's applicable runbook test/lint checks, recording every attempt and teardown
   failure. Recheck any advanced source tip. Separate fresh checks from permitted reuse of
   prior validation; reuse requires original state/tips, explicit permission and concrete
   dependency/runtime/coverage limits. Preserve failed attempts when a later retry passes.
   Supply a dated source-bound verification attestation with actual commands/results and
   coverage; the helper validates bindings, not arbitrary command execution.

   Inventory current architecture/state, progress history, ADR index/status, roadmap/scope
   indexes, delivery notes, top-level project guidance, domain, runbook, environment and
   integration knowledge. Skip absent optional records explicitly. Relevant existing layouts
   unsupported by the helper's typed inventory block closure; never silently omit them or
   relabel protected records to fit an allowed kind. Reconcile only records whose current
   claims changed, preserving other tasks and unfinished product work. Keep historical decisions, requirements,
   original Git/TDD fields and snapshot bytes intact. Return shared-file deltas to the
   active owner under `orchestration`; otherwise this invocation owns surgical writes.
   Keep untracked umbrella/consumer state local according to repository policy: no staging,
   commits or metadata publication are authorized here. An independent reviewer checks
   evidence, attempted/recovered errors, current knowledge and archive/link plans; supply
   dated source-bound `knowledge` and `audit` attestations. Use internal `knowledge` to
   accept them. Unresolved semantic/spec changes → **stop**: use `/spec-sync` under its own
   authority before a new finalization snapshot; this phase never edits requirements.
   The knowledge attestation lists exact `file_changes` before/after hashes for only the
   predeclared current records; the helper verifies immutable originals and actual current
   bytes before admitting those precise tracked edits. Every inventoried record retains its
   original or independently accepted binding, including ignored/untracked records; only
   journaled mechanical archive pointers may relocate. New semantic deltas require newer
   independent evidence and retain prior history. Keep the index unchanged during edits.
   If an owner advances integration source, reconcile its descendant generation and clean
   stage-zero index/checkout before new edits/checks. The helper may record that clean
   baseline/history using read-only evidence; staged/unmerged/unowned/rewound changes block.
   If the clean owner commit itself updates an inventoried record, submit its independently
   attested original-before/current-after delta to `knowledge` with the new actual source
   tips. The helper first independently verifies the clean descendant integration generation;
   source/index and semantic bindings persist together only after every proof succeeds.
   Progress is append-only; ADR bodies remain immutable, while index current status pointers may
   reconcile without changing decision titles/links/history. Unresolved ADR semantic change
   blocks this phase and uses the decision workflow under its own authority.

5. **Archive and finish.** With required cleanup, safe checkout, reconciliation and audit
   verified, call internal `archive` with the current revision and evidence. It moves the
   task without overwrite, then only an eligible whole spec; unfinished/future/ambiguous
   phases or deferred scope keep the spec active. Retain manifests, original snapshots,
   recovery packs, current-link plans and stable old-path resolution. Only the current
   `spec_path:` pointer, additive finalization marker and journaled mechanical links may
   relocate; historical links/records remain exact. Collision or interrupted operation →
   **stop**: retain all evidence and rerun the same public command to reconcile the intent.
   Call internal `finish` only after fresh required postconditions and source bindings
   succeed. Deployment remains independently `unverified` unless dated revision/environment
   proof exists; a required deployment contract blocks finish without that proof.
   Discover deployment/migration requirements from the actual task/spec acceptance contract,
   including legacy prose. An absent structured marker cannot downgrade an existing required
   delivery criterion. Unresolved applicability → **stop**: report the contract ambiguity.
   Do not edit requirements or infer authorization to deploy.

   After archival, independently audit actual archive manifests, current task/spec paths,
   relative links/indexes, protected state/history and unfinished scope against snapshots
   and journaled plans. Refresh the dated source-bound audit attestation using the resolved
   archived task/current state, then run `record` before `finish`; a pre-archive plan review
   alone is insufficient. If only metadata moved, report which source checks are reused,
   their original revisions/coverage and why that reuse is permitted. `reuse.validated_tips`
   means original validated task-branch tips. Checks executed during this invocation retain
   actual timestamps/source coverage across metadata-only moves; they need no prior-Validation
   reuse object. Rerun affected state, archive/link and instruction checks; report their actual
   new command receipts. Renew
   broader source checks only when source edits, failures or unresolved concerns require
   them. Never relabel an earlier run as fresh, count recovered teardown as flawless first
   execution, or claim deployment from a metadata-only closure.

Report task/spec original and current paths, prior Validation, current integration/checkout,
cleanup per ref, recovery, knowledge, verification coverage/reuse/errors, archival, audit
and deployment independently. State fresh versus reused evidence and optional tooling/logging
limitations. Announce complete only after helper `finish` returns `complete: true` and the
persisted `finalization: complete` marker verifies. Otherwise name the blocker, preserved
resources, exact recovery commands and `/phase-finalize <same-target>` rerun. Then **stop**.
