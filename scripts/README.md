# Repository scripts

All executable shell helpers live in this directory. Run project setup helpers from the
target project or umbrella directory. `sync.sh` and setup helpers resolve this repository
root from the parent of `scripts/`, unless `ORCHESTRAIL_HOME` selects another checkout.
`sync.sh --from` takes precedence over `ORCHESTRAIL_HOME`.

| Script | Purpose |
|---|---|
| `sync.sh` | Validate and deploy workflows, rules, and principles to supported coding assistants. |
| `setup-new-project.sh` | Initialize one consumer project. |
| `setup-umbrella.sh` | Initialize shared context for a multi-repository project. |
| `setup-all-repos.sh` | Initialize service repositories under an umbrella. |
| `link-skills.sh` | Link global Claude skills into a project that has local skills. Run from that project. |
| `log-step.sh` | Append pipeline run and step events to the local log store. |
| `install-hooks.sh` | Install or uninstall owned user hook entries with the adjacent standard-library Python engine. |
| `run-log-timing.sh` | Analyze only explicit run files with exact millisecond interval and coverage results. |
| `validate-contracts.sh` | Check repository-wide workflow contracts. |
| `validate-task.sh` | Validate one task directory passed as an argument. |
| `state-tool.py` | Read and edit one task's subtask-progress section through a structural parser, with a per-task lock, an expected revision and one JSON result per call; optional, Python 3.11+ standard library only. See [the operating manual](../docs/USAGE.md#11-state-tool). |
| `check-spec-draft.sh` | Check the specification-authoring review contract in milliseconds; standalone, outside the validator inventory. |
| `repo-set.py` | Read-only repository-set facts for a multi-repository `/spec-run`: `mode`, per-repository `preflight`, plan `route` (shared order, one stack per repository, cross-repository dependencies) and checkpoint `reconcile`; one JSON result per call; Python 3.9+ standard library only. |
| `check-repo-set.py` | Acceptance suite for `repo-set.py` and the multi-repository instruction contract, against disposable git repositories; standalone, outside the validator inventory. |
| `audit-instructions.py` | Read-only audit tool for rules, workflows and harness adapters: `extract` writes a deterministic inventory of the audited and reader files, their reference edges and candidate findings; `verify` checks the inventory, its hand-written assessment and the audit report and prints one line per violation; `render --write` regenerates the report's generated region. Python 3.11+ standard library only; standalone, outside the validator inventory. |
| `check-audit-instructions.py` | Acceptance suite for `audit-instructions.py`, against disposable fixture roots and git repositories; standalone, outside the validator inventory. |
| `audit-git-matrix/` | `run.sh` runs the `check-audit-instructions.py` suite in one container per git release that the audit tool's git isolation names (git built from its kernel.org source tarball by the `Dockerfile`; the build needs network access and Docker); standalone, outside the validator inventory. |

## Exact run timing

Run `bash scripts/run-log-timing.sh [--] FILE...` from the source checkout, or use
`-h`/`--help`. The small Bash launcher requires Python 3.11 or newer and jq, and
loads the adjacent source-only `run-log-timing.py`. It installs no packages or scripts
into the user's home. Producer writes and hooks keep their existing dependencies.

The helper copies only explicit canonical paths into a private temporary snapshot,
checks unchanged bytes and inventory around this checkout's complete producer lint,
and removes the snapshot afterward. Repeated paths collapse in caller order; distinct
files claiming one run are unavailable. It never discovers a log store or reads active
correlation metadata. Missing dependencies, invalid inputs or unverified checks produce
one versioned unavailable JSON result and exit zero.

Output has `schema_version`, `status`, `coverage`, `runs` and safe `diagnostics`.
Unavailable corpus data uses `runs:null`; an unavailable run uses `metrics:null`.
Coverage counts distinguish exact examined LF lines from inexact known violations.
Run metrics, spans, workers and named steps expose decimal-string milliseconds;
ratios contain exact `numerator_ms` and `denominator_ms` strings. Use Python integers
for arithmetic. Do not convert these totals through jq numeric operations.

Observed coverage unions work and explicit waiting. Gaps are unobserved time;
waiting is never inferred. Exclusive spans subtract every direct child, including
waiting. Invalid dependency components retain raw eligible coverage while disclosing
unavailable exclusive totals; valid disconnected roots remain partial evidence.
Same-actor checkpoint overlap invalidates its additive worker total while preserving
unions and overlap between distinct actors. Span time measures elapsed activity,
never CPU time. Legacy steps remain approximate and receive no synthetic intervals.
See [the retrospective workflow](../workflows/retro.md) for denominators and reporting.

## Post-merge finalization

Public workflow: `/phase-finalize <task-directory|spec-path> [--dry-run]`. Invoke separately
after owner integration; ordinary invocation authorizes mandatory cleanup of proven task
resources. Markdown owns orchestration. Python 3.11+ standard-library helpers are required
for mutation safety; Git mutations remain returned argv for explicit hook-governed commands.
The `phase-finalize.py` header is authoritative for CLI, journal and evidence schemas.

| Helper | Responsibility |
|---|---|
| `phase-finalize.py` | `inspect`, `prepare`, `attempt`, `record`, `knowledge`, `archive`, `finish`; versioned JSON, locked revision-checked journals, independent outcomes |
| `finalization_evidence.py` | Original full SHAs, independent validation, live origin/integration and repository-bound PR reads; configured/effective transport identity |
| `finalization_attempts.py`, `finalization_outputs.py` | Immutable execution observations/checkpoints, failed-pass invalidation and digest-bound exact outputs; no Git/network reads |
| `finalization_knowledge.py` | Predeclared current-record snapshots, independent exact before/after changes and unchanged-index enforcement |
| `finalization_recovery.py` | Self-contained original-object recovery packs, isolated closure verification and immutable digests |
| `finalization_archive.py`, `finalization_support.py` | Stable old-path resolution, snapshots/manifests, no-overwrite archival, mechanical link/pointer relocation, atomic writes |
| `check-phase-finalize.py` | Isolated evidence, safety, recovery and archive behavior |
| `check-finalization-safety.py` | Hook receipts/rails and isolated staged provider parity |
| `check-finalization-workflow.py` | Standalone workflow contracts, failed/recovered commands and checks, SSH aliases, interruption checkpoints and task validation |

Resolve helpers from `ORCHESTRAIL_HOME` or independently verified source provenance,
never a guessed consumer-relative path. No helper merges PRs, initializes project Git,
fetches, checks out, deletes branches, publishes metadata or writes telemetry. Recovery
verification creates disposable isolated object storage only. Optional logging/tools remain
nonblocking unless the project's required verification depends on them.

### Internal command sequence

```text
python3 SOURCE/scripts/phase-finalize.py inspect TARGET --root ROOT [--evidence EXISTING_JSON] [--dry-run]
python3 SOURCE/scripts/phase-finalize.py prepare TARGET --root ROOT --authorize --expected-revision absent
python3 SOURCE/scripts/phase-finalize.py prepare TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256
python3 SOURCE/scripts/phase-finalize.py attempt TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256 --evidence ATTEMPT_JSON
python3 SOURCE/scripts/phase-finalize.py record TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256 --evidence EVIDENCE_JSON
python3 SOURCE/scripts/phase-finalize.py knowledge TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256 --evidence EVIDENCE_JSON
python3 SOURCE/scripts/phase-finalize.py archive TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256 --evidence EVIDENCE_JSON
python3 SOURCE/scripts/phase-finalize.py finish TARGET --root ROOT --authorize --expected-revision ACTUAL_SHA256 --evidence EVIDENCE_JSON
```

Use real paths/argv, not literal placeholders. `recovery-required` from first preparation
means execute the returned exact pack command/stdin/stdout path, then prepare again at the
actual new revision. No deletion receipt exists until immutable pack/closure verification
passes. Preserve existing corrupt/incomplete packs and block; never regenerate over them.
After recording attempts, fresh `record` rechecks facts and refreshes hook receipts before
another mutation. All integration checkout/refresh operations precede cleanup; delete proven
remote refs before local branches, retaining normal local deletion refusal as incomplete.
Follow `rules/git-flow.md → Finalization Git ownership` for the narrowly authorized forms.

### Attempt input and recovery

Evidence JSON adds one `command_attempt` object with exactly `attempt_id`, `operation_id`,
`checkpoint`, `repository`, `argv`, `exit_code`, `stdout`, `stderr`, `observed_at`,
`provenance` and `source_tips`. `operation_id` is a planned action id with exact argv/repository,
or one of the documented check ids (for example `verification`); source tips match the
journal's integration binding. Each actual execution gets a new id. Replaying identical
content is a no-op; conflicting content blocks.
Check working directories may be the physical project root (including an umbrella outside
Git) or an exactly recorded repository; planned Git actions keep their exact bound repository.
`applied` requires exit zero; `blocked` and
`preserved` retain errors/resources. Only fresh postconditions verify Git actions. Caller
exit zero never proves cleanup, coverage or completion.

The supported recorder checks the authorized journal, original snapshots, plan digest,
lock and expected revision without invoking Git/network. It atomically writes only the
journal, so old hook receipts become stale until fresh reconciliation. This permits recording
network failures and failed verification/teardown while observations are unavailable.
Audit/check attempts after current semantic edits may be recorded before independent delta
acceptance, retaining original snapshots/index/scope bindings. This records execution only;
record/archive/finish still enforce current accepted digests, and no new receipts are emitted.
Keep both failed and recovered attempts. A later pass attestation states actual coverage and any
prior-evidence reuse/runtime/dependency limits; it never erases the earlier error.

The journal is `.ai/context/finalization/<stable-id>/journal.json`; it stays in place during
archival. Resume with the same public invocation, including original task/spec paths. Read
an actual journal revision when a write was interrupted; never replay a stale expected hash.
Completed reruns use persisted journal evidence; an old optional evidence file bound to raw
state before the completion marker is stale, and must not be presented as fresh evidence.
Journals bind `remote_identity` to configured fetch/push URLs and expanded effective fetch/push
URLs. Changed bindings or legacy incompatible journals fail closed; no rebinding/migration
command exists. The single exception is a verified rename of the GitHub repository: the origin
changes only in its owner/repository path, and `gh api --hostname github.com repos/<old>` and
the same read of `repos/<new>` return the same repository id with the new name. That proof is
appended to the journal's `remote_rebindings` and revalidated offline on every reconciliation;
the original binding stays unchanged, and hook receipts authorize no deletion under the renamed
origin. SSH alias PR resolution follows GitHub CLI's `ssh -G` translation, then an explicit
canonical `gh repo view` identity check and repo-bound PR read. Reject unsafe host spellings,
`GH_REPO`/`GH_HOST`, other default remotes and mismatched authority identities.
Primary references: [CLI remote resolution](https://github.com/cli/cli/blob/trunk/pkg/cmd/factory/remote_resolver.go),
[SSH translation](https://github.com/cli/go-gh/blob/trunk/pkg/ssh/ssh.go),
[repo view](https://cli.github.com/manual/gh_repo_view).

Only current pointers and journaled mechanical links relocate; snapshots, original Git/TDD
fields, requirements/history and unfinished scope remain intact. Audit actual archived paths,
manifests, state and references after movement and refresh source-bound audit evidence before
finish. Deployment remains unverified without dated revision/environment proof; required
proof blocks closure. Respect repository tracking policy; untracked umbrella state stays local.

### Focused checks and staged synchronization

Run the three standalone acceptance suites sequentially with the supported system Python.
The frozen broad validator remains unchanged. `sync.sh` requires all three suites after its
complete preflight. For an isolated provider export use:

```bash
bash scripts/sync.sh --from /absolute/source --stage /absolute/new-empty-destination
```

Staging writes only provider artifacts under the destination: no live HOME configuration,
project refresh, hook installation or consumer deployment. Missing/failing required checks
block staging. Validate generated parity in fixtures; do not infer live installation from it.

### Current-record bindings and bounded evidence

Before semantic edits, pass `knowledge_inventory:[{path,kind}]` to preparation. Existing
current Markdown records only are eligible, at root or recorded-repository scope: current
architecture/state/domain/runbook/environment/integrations and the spec scope index;
`progress`, `adr-index` and top-level `guidance` use their documented kinds. `roadmap`
supports `.ai/roadmap.md` or `.ai/memory/roadmap.md`; `delivery-notes` supports existing
`.ai/context/<scope>-delivery.md` records with one safe filename component. Unsupported
relevant layouts block closure explicitly. Original bytes are immutable snapshots.
Finish all integration checkout/refresh operations and record
postconditions to establish the clean index baseline before editing. The independent
knowledge attestation supplies exact `file_changes:[{path,before_sha256,after_sha256}]`.
Only those exact inventoried after bytes enter the dirty-file predicate. Every inventoried
current file, including unchanged ignored/untracked files, retains its bound digest; only
exact journaled archive-pointer changes are allowed. A later independent change needs strictly
newer dated evidence and retains all prior deltas. The clean index binds raw bytes, canonical
entries and integration HEAD. Normal fresh reconciliation may retain metadata-only refreshes
or descendant integration advances only with exact verified checkout and stage-zero entries
equal to HEAD; original baselines/history remain preserved. Offline attempts require the old
exact baseline until that reconciliation. Staged/unmerged/unowned/rewound index generations,
unrelated/product/config/executable edits, task/spec bodies, historical ADR bodies and
unlisted paths block. Progress is append-only. ADR index status pointers may reconcile;
unresolved semantic decision changes need their own authority and block this phase.
For a clean owner commit changing both integration source and inventoried knowledge, internal
`knowledge` independently observes the clean descendant generation before validating the
exact original-before/current-after attestation against its actual tips. Index/source and
semantic bindings persist atomically only after every proof succeeds.
Verification `reuse.validated_tips` contains original validated task-branch tips. Checks from
this same invocation retained after metadata-only archival preserve their actual timestamps,
commands and source coverage; they need no prior-Validation reuse object.

Outputs above 64 KiB become typed `{path,sha256,bytes,encoding:'utf-8'}` references to exact
immutable files under journal-dir/outputs; smaller strings stay inline. Replay normalizes
identically, including prior errors. Verify artifacts at every reconciliation/audit; never
truncate. Interrupted unreferenced artifacts remain preserved. Every authoritative journal
write refuses more than 1 MiB before replacing the previous revision. A newly recorded
verification/knowledge/audit/deployment check invalidates that kind's older pass until a
strictly newer valid source-bound attestation recovers it.

Canonical `## Final Verification` narrative needs matching dated independent successful
command evidence, task/raw-state hash, current integration tips and coverage; it needs no
hidden prose marker or existing journal. Legacy final PASS records remain supported.
The workflow discovers deployment/migration obligations from actual acceptance criteria,
including legacy prose; an absent structured marker cannot downgrade required delivery.
No requirement edit or deployment permission is inferred.

The hook's receipt scan is bounded to 64 files. Report excess files as a recoverable blocker
with exact identities/paths; the owner can archive obsolete receipt files while retaining
stable journals and recovery evidence. Never discard unrelated evidence or bypass the bound.
